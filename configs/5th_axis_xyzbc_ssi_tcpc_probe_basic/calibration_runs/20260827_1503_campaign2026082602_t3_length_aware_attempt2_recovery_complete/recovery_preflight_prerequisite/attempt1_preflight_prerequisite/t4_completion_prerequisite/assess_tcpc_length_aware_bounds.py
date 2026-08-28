#!/usr/bin/env python3
"""Audit the exploratory TCPC length model without accessing LinuxCNC or HAL."""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
import re
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TOOL_TABLE = HERE.parent / "5th_axis_xyzbc_ssi_probe_basic" / "tool.tbl"
BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_MODEL_PLAN.md"
DEFAULT_CANDIDATE_HAL = HERE / "tcpc_length_aware_candidate_2026082601.hal"
AUTHORIZED_VALIDATION_INI = (
    HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini"
)
AUTHORIZED_VALIDATION_KINS = (
    "headheadkins coordinates=XYZBC kinstype=B "
    "lengthmodel=1 lengthmodelid=2026082601"
)
AUTHORIZED_VALIDATION_TASK = (
    HERE / "diagnostics" / "milltask_exit_capture.sh"
).resolve()
AUTHORIZED_VALIDATION_OPEN_FILE = Path(
    "/home/cnc5/dev/probe_basic/example_gcode/blank.ngc"
).resolve()
AUTHORIZED_VALIDATION_OPEN_FILE_TEXT = "(New Program)\n\n\nM30"
AUTHORIZED_VALIDATION_HALFILES = (
    (HERE.parent / "5th_axis_xyzbc_ssi_probe_basic" / "5th_axis_xyzbc_ssi_probe_basic.hal").resolve(),
    (HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal").resolve(),
    (HERE / "tcpc_probe_attempt3_edge_counters.hal").resolve(),
    (HERE.parent / "5th_axis_xyzbc_ssi_probe_basic" / "xhc.hal").resolve(),
    DEFAULT_CANDIDATE_HAL.resolve(),
)
KINS_SOURCE = REPO_ROOT / "src" / "emc" / "kinematics" / "headheadkins.c"
REAL_TCPC_INIS = tuple(sorted(HERE.glob("*.ini")))

EXPECTED_TOOL_TABLE_SHA256 = (
    "e7d459a2c875f56f2fcdeeefd3c8fa889809a5545cd3eab1309176c8c623092d"
)
EXPECTED_BASE_HAL_SHA256 = (
    "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778"
)

T3_LENGTH_MM = 128.606729
T4_LENGTH_MM = 229.407000
CURRENT_TABLE_MIN_LENGTH_MM = 114.677000
CURRENT_TABLE_MAX_LENGTH_MM = 411.810000
RECENT_HISTORICAL_MAX_LENGTH_MM = 425.022000
MODEL_MIN_LENGTH_MM = 100.000000
MODEL_MAX_LENGTH_MM = 430.000000
MODEL_LENGTH_TOLERANCE_MM = 0.002
MODEL_ID = 2026082601
B_MIN_DEG = -100.0
B_MAX_DEG = 100.0
B_ZERO_DEG = 0.0
C_ZERO_DEG = -0.024500
DENSE_STEP_DEG = 0.25

INCREMENTAL_CAP_MM = 0.700
LENGTH_BANK_CAP_MM = 0.400
TOTAL_SURFACE_CAP_MM = 1.350

AUDIT_LENGTHS_MM = (
    MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM,
    MODEL_MIN_LENGTH_MM,
    CURRENT_TABLE_MIN_LENGTH_MM,
    T3_LENGTH_MM,
    T4_LENGTH_MM,
    CURRENT_TABLE_MAX_LENGTH_MM,
    RECENT_HISTORICAL_MAX_LENGTH_MM,
    MODEL_MAX_LENGTH_MM,
    MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM,
)

AXES = ("x", "y", "z")

# H0 is the currently accepted empirical surface in the base HAL.
H0 = {
    "b_sin": (+0.015577123, +0.060508594, +0.312123080),
    "b_omc": (+0.141330042, +0.111703959, -0.338104991),
    "b_sin2": (-0.013271805, +0.050707231, -0.156014210),
    "bc_sinb_sinc": (-0.006371196, +0.325723886, +0.130042953),
    "bc_omcb_sinc": (-0.074687973, +0.012622224, -0.001729459),
    "bc_omcb_sin2c": (-0.017723675, -0.255875638, -0.055414262),
    "bc_sinb_cosc": (-0.048238059, -0.063070849, -0.018239994),
    "bc_omcb_cosc": (-0.030283175, +0.071683484, +0.000165632),
}

# S is the incremental common surface fitted to T4. It is not a replacement
# for H0. Every basis is referenced so the correction is zero at B0/C0.
COMMON_INCREMENT = {
    "c_cos": (-0.020464473, +0.052740586, +0.011847695),
    "b_sin": (+0.015022942, -0.003100056, +0.057461362),
    "b_sin2": (+0.009817048, -0.022720137, +0.004872879),
    "bc_sinb_sinc": (-0.051798995, +0.118281130, -0.011204319),
    "bc_omcb_sin2c": (-0.015049287, +0.350473397, -0.065656585),
    "bc_sinb_cos2c": (-0.020544144, +0.051627926, -0.002830134),
    "bmid_base": (+0.036249664, +0.057389135, -0.009113528),
    "bmid_cosc": (-0.069934796, +0.035520813, +0.007391483),
    "bmid_sinc": (-0.024676972, -0.094829113, +0.005885591),
    "bmid_cos2c": (-0.006803814, -0.040256211, -0.000493361),
}

# D is one T3-endpoint differential. Runtime scaling is synchronous from the
# active G43 Z length: q=(T4-L)/(T4-T3). It must never clamp at T3 or T4.
LENGTH_DIFFERENTIAL = {
    "c_cos": (+0.014666078, -0.034936825, -0.000531832),
    "c_sin": (+0.037331865, +0.007479807, +0.000596261),
    "b_sin": (-0.009333530, -0.018596090, -0.055267212),
    "bc_sinb_sinc": (+0.022658483, +0.036745231, -0.024883253),
    "bc_sinb_cosc": (+0.126705142, +0.001218059, +0.017700599),
}

PIN_STEMS = {
    "b_sin": "headheadkins.bharm-m.sin",
    "b_omc": "headheadkins.bharm-m.omc",
    "b_sin2": "headheadkins.bharm-m.sin2",
    "bc_sinb_sinc": "headheadkins.bcross.sinb-sinc",
    "bc_omcb_sinc": "headheadkins.bcross.omcb-sinc",
    "bc_omcb_sin2c": "headheadkins.bcross.omcb-sin2c",
    "bc_sinb_cosc": "headheadkins.bcross.sinb-cosc",
    "bc_omcb_cosc": "headheadkins.bcross.omcb-cosc",
}

MODEL_PIN_STEMS = {
    "c_cos": "headheadkins.charm.cos",
    "c_sin": "headheadkins.charm.sin",
    "b_sin": "headheadkins.bharm-m.sin",
    "b_omc": "headheadkins.bharm-m.omc",
    "b_sin2": "headheadkins.bharm-m.sin2",
    "bc_sinb_sinc": "headheadkins.bcross.sinb-sinc",
    "bc_omcb_sinc": "headheadkins.bcross.omcb-sinc",
    "bc_omcb_sin2c": "headheadkins.bcross.omcb-sin2c",
    "bc_sinb_cosc": "headheadkins.bcross.sinb-cosc",
    "bc_omcb_cosc": "headheadkins.bcross.omcb-cosc",
    "bc_sinb_cos2c": "headheadkins.bcross.sinb-cos2c",
    "bmid_base": "headheadkins.bmid.base",
    "bmid_cosc": "headheadkins.bmid.cosc",
    "bmid_sinc": "headheadkins.bmid.sinc",
    "bmid_cos2c": "headheadkins.bmid.cos2c",
}

LENGTH_PIN_STEMS = {
    "c_cos": "headheadkins.ldiff.c-cos",
    "c_sin": "headheadkins.ldiff.c-sin",
    "b_sin": "headheadkins.ldiff.b-sin",
    "bc_sinb_sinc": "headheadkins.ldiff.sinb-sinc",
    "bc_sinb_cosc": "headheadkins.ldiff.sinb-cosc",
}

ALL_COMMON_PIN_STEMS = (
    "headheadkins.bharm-m.sin",
    "headheadkins.bharm-m.omc",
    "headheadkins.bharm-m.sin2",
    "headheadkins.bharm-c.sin",
    "headheadkins.bharm-c.omc",
    "headheadkins.bharm-c.sin2",
    "headheadkins.charm.cos",
    "headheadkins.charm.sin",
    "headheadkins.charm.cos2",
    "headheadkins.charm.sin2",
    "headheadkins.bmid.base",
    "headheadkins.bmid.cosc",
    "headheadkins.bmid.sinc",
    "headheadkins.bmid.cos2c",
    "headheadkins.bmid.sin2c",
    "headheadkins.bcross.sinb-sinc",
    "headheadkins.bcross.omcb-sinc",
    "headheadkins.bcross.omcb-sin2c",
    "headheadkins.bcross.sinb-cosc",
    "headheadkins.bcross.omcb-cosc",
    "headheadkins.bcross.sinb-sin2c",
    "headheadkins.bcross.sinb-cos2c",
)

ALL_LENGTH_PIN_STEMS = tuple(sorted(LENGTH_PIN_STEMS.values()))

# Global absolute derivative bounds with respect to B and C in radians.
BASIS_DERIVATIVE_BOUNDS = {
    "c_cos": (0.0, 1.0),
    "c_sin": (0.0, 1.0),
    "b_sin": (1.0, 0.0),
    "b_omc": (1.0, 0.0),
    "b_sin2": (2.0, 0.0),
    "bc_sinb_sinc": (1.0, 1.0),
    "bc_omcb_sinc": (1.0, 2.0),
    "bc_omcb_sin2c": (1.0, 2.0),
    "bc_sinb_cosc": (1.0, 1.0),
    "bc_omcb_cosc": (1.0, 2.0),
    "bc_sinb_cos2c": (1.0, 2.0),
    "bmid_base": (2.0, 0.0),
    "bmid_cosc": (2.0, 1.0),
    "bmid_sinc": (2.0, 1.0),
    "bmid_cos2c": (2.0, 2.0),
}


class AuditError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def tool_lengths(path: Path) -> dict[int, float]:
    tools: dict[int, float] = {}
    field_pattern = re.compile(
        r"(?:^|\s)([A-Za-z])([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)"
        r"(?=\s|$)"
    )
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        body = line.split(";", 1)[0].strip()
        if not body:
            continue
        matches = list(field_pattern.finditer(body))
        if not matches or matches[0].group(1).upper() != "T":
            raise AuditError(f"unrecognized tool-table row at line {line_number}: {body}")
        fields: dict[str, float] = {}
        for match in matches:
            field = match.group(1).upper()
            if field in fields:
                raise AuditError(f"duplicate {field} field at tool-table line {line_number}")
            fields[field] = float(match.group(2))
        if "Z" not in fields:
            raise AuditError(f"tool-table row has no Z length at line {line_number}")
        if not all(math.isfinite(value) for value in fields.values()):
            raise AuditError(f"tool-table row is nonfinite at line {line_number}")
        tool_value = fields["T"]
        if tool_value < 0.0 or not tool_value.is_integer():
            raise AuditError(f"invalid tool number at line {line_number}: {tool_value}")
        tool = int(tool_value)
        if tool in tools:
            raise AuditError(f"duplicate T{tool} in tool table at line {line_number}")
        length = fields["Z"]
        if length <= 0.0:
            raise AuditError(f"T{tool} has nonpositive Z length {length}")
        unsupported = {
            field: fields[field]
            for field in ("X", "Y", "A", "B", "C", "U", "V", "W")
            if abs(fields.get(field, 0.0)) > 1e-9
        }
        if unsupported:
            raise AuditError(f"T{tool} has unsupported non-Z offsets: {unsupported}")
        tools[tool] = length
    if not tools:
        raise AuditError("tool table contains no Z lengths")
    return tools


def ini_section_values(text: str, section: str) -> dict[str, str]:
    match = re.search(
        r"^\[" + re.escape(section) + r"\]\s*$([\s\S]*?)(?=^\[[^\]]+\]\s*$|\Z)",
        text,
        re.MULTILINE,
    )
    if not match:
        raise AuditError(f"missing [{section}] INI section")
    values: dict[str, str] = {}
    for key, value in re.findall(
        r"^\s*([A-Za-z0-9_]+)\s*=\s*([^#;\r\n]+)",
        match.group(1),
        re.MULTILINE,
    ):
        values[key.upper()] = value.strip()
    return values


def verify_real_ini_tool_tables() -> tuple[Path, ...]:
    canonical = TOOL_TABLE.resolve()
    promoted: list[Path] = []
    if not REAL_TCPC_INIS:
        raise AuditError("no top-level real TCPC INI files found")
    for path in REAL_TCPC_INIS:
        text = path.read_text(encoding="ascii")
        if re.search(r"^\s*TOOL_DATABASE\s*=", text, re.MULTILINE):
            raise AuditError(f"{path.name} defines TOOL_DATABASE instead of the audited table")
        matches = re.findall(r"^\s*TOOL_TABLE\s*=\s*([^#;\r\n]+)", text, re.MULTILINE)
        if len(matches) != 1:
            raise AuditError(f"{path.name} must define exactly one TOOL_TABLE")
        resolved = (path.parent / matches[0].strip()).resolve()
        if resolved != canonical:
            raise AuditError(
                f"{path.name} uses {resolved}, not audited table {canonical}"
            )
        kins = re.findall(r"^\s*KINEMATICS\s*=\s*([^#;\r\n]+)", text, re.MULTILINE)
        if len(kins) != 1 or "headheadkins" not in kins[0].split():
            raise AuditError(f"{path.name} does not select headheadkins exactly once")
        halfiles = re.findall(r"^\s*HALFILE\s*=\s*([^#;\r\n]+)", text, re.MULTILINE)
        resolved_halfiles = tuple((path.parent / item.strip()).resolve() for item in halfiles)
        candidate_referenced = DEFAULT_CANDIDATE_HAL.resolve() in resolved_halfiles
        for section in ("AXIS_B", "JOINT_3"):
            values = ini_section_values(text, section)
            try:
                minimum = float(values["MIN_LIMIT"])
                maximum = float(values["MAX_LIMIT"])
            except (KeyError, ValueError) as exc:
                raise AuditError(f"{path.name} has invalid [{section}] B limits") from exc
            if (
                not math.isfinite(minimum)
                or not math.isfinite(maximum)
                or minimum < B_MIN_DEG
                or maximum > B_MAX_DEG
                or maximum < minimum
            ):
                raise AuditError(
                    f"{path.name} [{section}] limits {minimum}..{maximum} "
                    f"exceed audited B={B_MIN_DEG}..{B_MAX_DEG}"
                )
        length_match = re.search(r"(?:^|\s)lengthmodel=([^\s]+)(?:\s|$)", kins[0])
        if length_match and length_match.group(1) not in ("0", "1"):
            raise AuditError(f"{path.name} has invalid lengthmodel value")
        length_model_enabled = bool(length_match and length_match.group(1) == "1")
        required_lines = re.findall(
            r"^\s*LENGTH_MODEL_REQUIRED\s*=\s*([^#;\r\n]+)",
            text,
            re.MULTILINE,
        )
        if length_model_enabled:
            promoted.append(path.resolve())
            id_match = re.search(r"(?:^|\s)lengthmodelid=(\d+)(?:\s|$)", kins[0])
            if not id_match or int(id_match.group(1)) != MODEL_ID:
                raise AuditError(
                    f"{path.name} enables lengthmodel without lengthmodelid={MODEL_ID}"
                )
            tcpc_values = ini_section_values(text, "TCPC")
            required_value = tcpc_values.get("LENGTH_MODEL_REQUIRED", "").lower()
            if len(required_lines) != 1 or required_value not in (
                "1",
                "true",
                "yes",
                "on",
            ):
                raise AuditError(
                    f"{path.name} enables lengthmodel without fail-closed LENGTH_MODEL_REQUIRED"
                )
            if not candidate_referenced or resolved_halfiles[-1] != DEFAULT_CANDIDATE_HAL.resolve():
                raise AuditError(
                    f"{path.name} must load the canonical length overlay as its final HALFILE"
                )
            if path.resolve() == AUTHORIZED_VALIDATION_INI.resolve():
                if kins[0].strip() != AUTHORIZED_VALIDATION_KINS:
                    raise AuditError(
                        f"{path.name} does not use the sealed validation KINEMATICS line"
                    )
                if resolved_halfiles != AUTHORIZED_VALIDATION_HALFILES:
                    raise AuditError(
                        f"{path.name} HALFILE order differs from the sealed validation order"
                    )
                task_values = ini_section_values(text, "TASK")
                task_path = Path(task_values.get("TASK", ""))
                if not task_path.is_absolute():
                    task_path = path.parent / task_path
                if task_path.resolve() != AUTHORIZED_VALIDATION_TASK:
                    raise AuditError(
                        f"{path.name} does not use the diagnostic task-capture wrapper"
                    )
                display_values = ini_section_values(text, "DISPLAY")
                open_file = Path(display_values.get("OPEN_FILE", ""))
                if not open_file.is_absolute():
                    open_file = path.parent / open_file
                if open_file.resolve() != AUTHORIZED_VALIDATION_OPEN_FILE:
                    raise AuditError(
                        f"{path.name} does not select the sealed blank startup program"
                    )
                if (
                    AUTHORIZED_VALIDATION_OPEN_FILE.read_text(encoding="ascii")
                    != AUTHORIZED_VALIDATION_OPEN_FILE_TEXT
                ):
                    raise AuditError("sealed validation startup program is not blank")
        else:
            if candidate_referenced:
                raise AuditError(
                    f"{path.name} references the length overlay without enabling lengthmodel"
                )
            if required_lines or re.search(r"(?:^|\s)lengthmodelid=", kins[0]):
                raise AuditError(
                    f"{path.name} contains a length-model promotion marker while disabled"
                )
    expected = {AUTHORIZED_VALIDATION_INI.resolve()}
    if set(promoted) != expected:
        names = sorted(path.name for path in promoted)
        raise AuditError(
            "length-model promotion must be limited to the authorized validation INI; "
            f"found {names}"
        )
    return tuple(promoted)


def verify_static_model() -> None:
    banks = (H0, COMMON_INCREMENT, LENGTH_DIFFERENTIAL)
    for bank in banks:
        for term, vector in bank.items():
            if term not in BASIS_DERIVATIVE_BOUNDS:
                raise AuditError(f"no derivative bound for model term {term}")
            if len(vector) != 3 or not all(math.isfinite(value) for value in vector):
                raise AuditError(f"model term {term} is not a finite XYZ vector")
    common_terms = set(H0) | set(COMMON_INCREMENT)
    missing = common_terms - set(MODEL_PIN_STEMS)
    if missing:
        raise AuditError(f"common terms have no runtime pin mapping: {sorted(missing)}")
    if set(LENGTH_DIFFERENTIAL) != set(LENGTH_PIN_STEMS):
        raise AuditError("length differential/runtime pin mapping differs")
    constants = (
        T3_LENGTH_MM,
        T4_LENGTH_MM,
        MODEL_MIN_LENGTH_MM,
        MODEL_MAX_LENGTH_MM,
        MODEL_LENGTH_TOLERANCE_MM,
        INCREMENTAL_CAP_MM,
        LENGTH_BANK_CAP_MM,
        TOTAL_SURFACE_CAP_MM,
    )
    if not all(math.isfinite(value) for value in constants):
        raise AuditError("model configuration contains a nonfinite constant")


def verify_baseline_hal(path: Path) -> None:
    values: dict[str, float] = {}
    pattern = re.compile(r"^setp\s+(headheadkins\.[^\s]+)\s+([^\s#]+)")
    for line in path.read_text(encoding="ascii").splitlines():
        match = pattern.match(line.strip())
        if match:
            try:
                values[match.group(1)] = float(match.group(2))
            except ValueError:
                pass
    for term, vector in H0.items():
        for axis, expected in zip(AXES, vector):
            pin = f"{PIN_STEMS[term]}.{axis}"
            if pin not in values:
                raise AuditError(f"baseline HAL no longer defines {pin}")
            if not math.isclose(values[pin], expected, abs_tol=5e-10):
                raise AuditError(
                    f"baseline HAL changed {pin}: {values[pin]:+.9f} != {expected:+.9f}"
                )
    if values.get("headheadkins.c-zero-offset") != C_ZERO_DEG:
        raise AuditError("baseline HAL C-zero differs from the model basis")
    if values.get("headheadkins.b-zero-offset") != B_ZERO_DEG:
        raise AuditError("baseline HAL B-zero differs from the model basis")


def q_for_length(length_mm: float) -> float:
    return (T4_LENGTH_MM - length_mm) / (T4_LENGTH_MM - T3_LENGTH_MM)


def combine_coefficients(
    *weighted: tuple[float, dict[str, tuple[float, float, float]]],
) -> dict[str, tuple[float, float, float]]:
    result: dict[str, tuple[float, float, float]] = {}
    for weight, bank in weighted:
        for term, vector in bank.items():
            previous = result.get(term, (0.0, 0.0, 0.0))
            result[term] = tuple(
                previous[axis] + weight * vector[axis] for axis in range(3)
            )
    return result


def surface_coefficients(
    length_mm: float,
) -> dict[str, dict[str, tuple[float, float, float]]]:
    q_value = q_for_length(length_mm)
    return {
        "incremental": combine_coefficients(
            (1.0, COMMON_INCREMENT), (q_value, LENGTH_DIFFERENTIAL)
        ),
        "length_bank": combine_coefficients((q_value, LENGTH_DIFFERENTIAL)),
        "total": combine_coefficients(
            (1.0, H0),
            (1.0, COMMON_INCREMENT),
            (q_value, LENGTH_DIFFERENTIAL),
        ),
    }


def continuous_upper_bound(
    grid_maximum: float,
    coefficients: dict[str, tuple[float, float, float]],
) -> float:
    derivative_b = 0.0
    derivative_c = 0.0
    for term, vector in coefficients.items():
        vector_norm = math.sqrt(sum(value * value for value in vector))
        bound_b, bound_c = BASIS_DERIVATIVE_BOUNDS[term]
        derivative_b += vector_norm * bound_b
        derivative_c += vector_norm * bound_c
    half_cell_rad = math.radians(DENSE_STEP_DEG / 2.0)
    result = grid_maximum + half_cell_rad * (derivative_b + derivative_c)
    if not math.isfinite(result):
        raise AuditError("continuous angular bound is nonfinite")
    return result


def basis_values(b_deg: float, c_deg: np.ndarray) -> dict[str, np.ndarray]:
    b_rad = np.deg2rad(b_deg)
    c_rad = np.deg2rad(c_deg + C_ZERO_DEG)
    c_ref = math.radians(C_ZERO_DEG)
    sin_b = math.sin(b_rad)
    omc_b = 1.0 - math.cos(b_rad)
    mid_b = math.sin(2.0 * b_rad) ** 2
    return {
        "c_cos": np.cos(c_rad) - math.cos(c_ref),
        "c_sin": np.sin(c_rad) - math.sin(c_ref),
        "b_sin": np.full_like(c_deg, sin_b),
        "b_omc": np.full_like(c_deg, omc_b),
        "b_sin2": np.full_like(c_deg, math.sin(2.0 * b_rad)),
        "bc_sinb_sinc": sin_b * np.sin(c_rad),
        "bc_omcb_sinc": omc_b * np.sin(c_rad),
        "bc_omcb_sin2c": omc_b * np.sin(c_rad) ** 2,
        "bc_sinb_cosc": sin_b * np.cos(c_rad),
        "bc_omcb_cosc": omc_b * np.cos(c_rad),
        "bc_sinb_cos2c": sin_b * np.cos(2.0 * c_rad),
        "bmid_base": np.full_like(c_deg, mid_b),
        "bmid_cosc": mid_b * np.cos(c_rad),
        "bmid_sinc": mid_b * np.sin(c_rad),
        "bmid_cos2c": mid_b * np.cos(2.0 * c_rad),
    }


def evaluate_surface(
    basis: dict[str, np.ndarray], coefficients: dict[str, tuple[float, float, float]]
) -> np.ndarray:
    result = np.zeros((len(next(iter(basis.values()))), 3), dtype=float)
    for term, vector in coefficients.items():
        result += basis[term][:, None] * np.asarray(vector, dtype=float)[None, :]
    return result


def dense_audit(length_mm: float) -> dict[str, tuple[float, float, float]]:
    q_value = q_for_length(length_mm)
    c_values = np.arange(0.0, 360.0 + (DENSE_STEP_DEG / 2.0), DENSE_STEP_DEG)
    maxima = {
        "incremental": (-1.0, 0.0, 0.0),
        "length_bank": (-1.0, 0.0, 0.0),
        "total": (-1.0, 0.0, 0.0),
    }
    b_values = np.arange(B_MIN_DEG, B_MAX_DEG + (DENSE_STEP_DEG / 2.0), DENSE_STEP_DEG)
    for b_deg in b_values:
        basis = basis_values(float(b_deg), c_values)
        h0 = evaluate_surface(basis, H0)
        common = evaluate_surface(basis, COMMON_INCREMENT)
        length_bank = q_value * evaluate_surface(basis, LENGTH_DIFFERENTIAL)
        surfaces = {
            "incremental": common + length_bank,
            "length_bank": length_bank,
            "total": h0 + common + length_bank,
        }
        for name, surface in surfaces.items():
            norms = np.linalg.norm(surface, axis=1)
            if not np.all(np.isfinite(norms)):
                raise AuditError(
                    f"{name} surface is nonfinite at B={float(b_deg):.6f}, "
                    f"L={length_mm:.6f}"
                )
            index = int(np.argmax(norms))
            value = float(norms[index])
            if value > maxima[name][0]:
                maxima[name] = (value, float(b_deg), float(c_values[index]))
    return maxima


def zero_reference_error(length_mm: float) -> float:
    basis = basis_values(0.0, np.asarray([0.0]))
    value = (
        evaluate_surface(basis, H0)
        + evaluate_surface(basis, COMMON_INCREMENT)
        + q_for_length(length_mm) * evaluate_surface(basis, LENGTH_DIFFERENTIAL)
    )
    result = float(np.linalg.norm(value[0]))
    if not math.isfinite(result):
        raise AuditError(f"B0/C0 reference is nonfinite at L={length_mm:.6f}")
    return result


def render_candidate_hal() -> str:
    common_total = combine_coefficients((1.0, H0), (1.0, COMMON_INCREMENT))
    lines = [
        "# REAL-MACHINE VALIDATION CANDIDATE: TCPC length-aware revision 2026082601.",
        "# Not released for production machining or general TCPC use.",
        "# Generated by assess_tcpc_length_aware_bounds.py; do not edit by hand.",
        "# STARTUP ONLY: never source or reload this file in a running LinuxCNC session.",
        "# Every coefficient change requires a new model ID and a clean restart.",
        "",
        "# Invalidate first so a failed or partial startup load cannot publish a commit.",
        "setp headheadkins.length-model.id 0",
        "",
        f"setp headheadkins.length-model.reference {T4_LENGTH_MM:.9f}",
        f"setp headheadkins.length-model.span {T4_LENGTH_MM - T3_LENGTH_MM:.9f}",
        f"setp headheadkins.length-model.minimum {MODEL_MIN_LENGTH_MM:.9f}",
        f"setp headheadkins.length-model.maximum {MODEL_MAX_LENGTH_MM:.9f}",
        f"setp headheadkins.length-model.tolerance {MODEL_LENGTH_TOLERANCE_MM:.9f}",
        f"setp headheadkins.length-model.max-diff-norm {LENGTH_BANK_CAP_MM:.9f}",
        f"setp headheadkins.length-model.max-total-norm {TOTAL_SURFACE_CAP_MM:.9f}",
        f"setp headheadkins.b-zero-offset {B_ZERO_DEG:+.9f}",
        f"setp headheadkins.c-zero-offset {C_ZERO_DEG:+.9f}",
        "setp headheadkins.sim-bharm-enable 1",
        "",
        "# Clear every evaluated bank before writing the absolute model.",
    ]
    for stem in ALL_COMMON_PIN_STEMS:
        for axis in AXES:
            lines.append(f"setp {stem}.{axis} +0.000000000")
    for stem in ALL_LENGTH_PIN_STEMS:
        for axis in AXES:
            lines.append(f"setp {stem}.{axis} +0.000000000")
    lines.extend(["", "# Absolute H0 + S common surface."])
    for term in sorted(common_total, key=lambda name: MODEL_PIN_STEMS[name]):
        for axis, value in zip(AXES, common_total[term]):
            lines.append(f"setp {MODEL_PIN_STEMS[term]}.{axis} {value:+.9f}")
    lines.extend(["", "# T3 endpoint differential D; runtime applies q(L) synchronously."])
    for term in sorted(LENGTH_DIFFERENTIAL, key=lambda name: LENGTH_PIN_STEMS[name]):
        for axis, value in zip(AXES, LENGTH_DIFFERENTIAL[term]):
            lines.append(f"setp {LENGTH_PIN_STEMS[term]}.{axis} {value:+.9f}")
    lines.extend(
        [
            "",
            "# Commit marker is deliberately last; partial overlays remain invalid.",
            f"setp headheadkins.length-model.id {MODEL_ID}",
            "",
        ]
    )
    return "\n".join(lines)


def run_audit() -> tuple[
    dict[int, float],
    dict[float, dict[str, tuple[float, float, float]]],
    tuple[Path, ...],
]:
    verify_static_model()
    if sha256(TOOL_TABLE) != EXPECTED_TOOL_TABLE_SHA256:
        raise AuditError("tool table hash changed; re-audit its full length domain")
    if sha256(BASE_HAL) != EXPECTED_BASE_HAL_SHA256:
        raise AuditError("base HAL hash changed; re-audit H0 before using this model")
    verify_baseline_hal(BASE_HAL)
    promoted = verify_real_ini_tool_tables()

    tools = tool_lengths(TOOL_TABLE)
    minimum = min(tools.values())
    maximum = max(tools.values())
    if len(tools) != 54:
        raise AuditError(f"expected 54 configured tools, found {len(tools)}")
    if minimum != CURRENT_TABLE_MIN_LENGTH_MM or maximum != CURRENT_TABLE_MAX_LENGTH_MM:
        raise AuditError(
            f"current tool range changed: {minimum:.6f}..{maximum:.6f} mm; re-audit it"
        )
    outside = {
        tool: length
        for tool, length in tools.items()
        if not MODEL_MIN_LENGTH_MM <= length <= MODEL_MAX_LENGTH_MM
    }
    if outside:
        raise AuditError(f"tool lengths outside the hard model domain: {outside}")
    if tools.get(3) != T3_LENGTH_MM or tools.get(4) != T4_LENGTH_MM:
        raise AuditError("T3 or T4 calibration length changed")
    if not math.isclose(q_for_length(T4_LENGTH_MM), 0.0, abs_tol=1e-15):
        raise AuditError("T4 normalization is not zero")
    if not math.isclose(q_for_length(T3_LENGTH_MM), 1.0, abs_tol=1e-15):
        raise AuditError("T3 normalization is not one")

    audits = {length: dense_audit(length) for length in AUDIT_LENGTHS_MM}
    caps = {
        "incremental": INCREMENTAL_CAP_MM,
        "length_bank": LENGTH_BANK_CAP_MM,
        "total": TOTAL_SURFACE_CAP_MM,
    }
    for length, audit in audits.items():
        coefficient_sets = surface_coefficients(length)
        for name, cap in caps.items():
            upper_bound = continuous_upper_bound(
                audit[name][0], coefficient_sets[name]
            )
            if not math.isfinite(upper_bound) or upper_bound > cap:
                raise AuditError(
                    f"continuous {name} cap exceeded at L={length:.6f}: "
                    f"{upper_bound:.6f} > {cap:.6f}"
                )
        if zero_reference_error(length) > 1e-12:
            raise AuditError(f"B0/C0 reference is not exact zero at L={length:.6f}")
    return tools, audits, promoted


def render_report(
    tools: dict[int, float],
    audits: dict[float, dict[str, tuple[float, float, float]]],
    promoted: tuple[Path, ...],
) -> str:
    min_tool = min(tools, key=tools.get)
    max_tool = max(tools, key=tools.get)
    candidate_hal = render_candidate_hal()
    outer_continuous: dict[float, dict[str, float]] = {}
    for length in (
        MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM,
        MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM,
    ):
        coefficient_sets = surface_coefficients(length)
        outer_continuous[length] = {
            name: continuous_upper_bound(audits[length][name][0], coefficients)
            for name, coefficients in coefficient_sets.items()
        }
    rows = []
    for length in AUDIT_LENGTHS_MM:
        audit = audits[length]
        rows.append(
            "| "
            f"{length:.6f} | {q_for_length(length):+.6f} | "
            f"{audit['incremental'][0]:.6f} | {audit['length_bank'][0]:.6f} | "
            f"{audit['total'][0]:.6f} |"
        )
    return "\n".join(
        [
            "# TCPC Length-Aware Model Plan",
            "",
            "## Status",
            "",
            "`REAL-MACHINE VALIDATION CANDIDATE - NOT PRODUCTION RELEASED`",
            "",
            "The reviewed rigid head-head transform remains suitable. The current empirical",
            "B/C surface is tool-length independent, so it cannot explain the repeatable T3/T4",
            "difference. The next candidate therefore uses:",
            "",
            "```text",
            "H(B,C,L) = H0(B,C) + S(B,C) + q(L) D(B,C)",
            f"q(L) = ({T4_LENGTH_MM:.6f} - L) / {T4_LENGTH_MM - T3_LENGTH_MM:.6f}",
            "```",
            "",
            "`H0` is the accepted baseline surface, `S` is a ten-term common increment, and",
            "`D` is a five-term T3 endpoint differential. `q=0` at T4 and `q=1` at T3.",
            "Runtime evaluation must use the active G43 Z length synchronously inside the",
            "kinematics calculation. It must not asynchronously rewrite coefficient pins and",
            "must not clamp at either calibration probe length. Each forward/inverse call must",
            "use one snapshot of the active offset, bracket coefficient evaluation with the",
            "expected model ID, and fail on a nonfinite complete transform.",
            "The generated overlay is startup-only: never source or reload it in a running",
            "LinuxCNC session. Every coefficient revision requires a new model ID and a clean",
            "restart; the ID is not a supported live-reload mechanism.",
            "",
            "## Full Tool Domain",
            "",
            f"The active table contains `{len(tools)}` tools from T{min_tool} `{tools[min_tool]:.6f} mm`",
            f"through T{max_tool} `{tools[max_tool]:.6f} mm`, a `{tools[max_tool] - tools[min_tool]:.6f} mm` span.",
            f"The tracked predecessor used T69 at `{RECENT_HISTORICAL_MAX_LENGTH_MM:.6f} mm`. To cover both",
            "the current table and that recently used tool, the declared hard runtime domain is",
            f"`{MODEL_MIN_LENGTH_MM:.6f}..{MODEL_MAX_LENGTH_MM:.6f} mm`, with only",
            f"`{MODEL_LENGTH_TOLERANCE_MM:.3f} mm` boundary-comparison tolerance. The nominal hard domain is",
            f"`{MODEL_MIN_LENGTH_MM:.3f}..{MODEL_MAX_LENGTH_MM:.3f} mm`; the exact guard acceptance interval is",
            f"`{MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM:.3f}..{MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM:.3f} mm`.",
            "Zero/nonfinite Z, nonfinite offset fields, nonzero X/Y/A/B/C/U/V/W offsets, or a",
            "length outside that interval must make G43.4 fail closed. The guard uses the live",
            "active offset because normal tool touch-off legitimately updates table lengths.",
            "Every table edit refreshes sealed traceability; an inside-domain edit does not expand",
            "the coefficient domain, while an outside-domain edit requires explicit domain/cap",
            "requalification and remains blocked. The domain must never expand implicitly.",
            "",
            "| length mm | q | dense incremental max mm | dense length-bank max mm | dense total max mm |",
            "| ---: | ---: | ---: | ---: | ---: |",
            *rows,
            "",
            f"The dense audit covers `B={B_MIN_DEG:+.0f}..{B_MAX_DEG:+.0f}` and a complete C cycle at",
            f"`{DENSE_STEP_DEG:.2f} deg` spacing. It enforces incremental `<={INCREMENTAL_CAP_MM:.3f} mm`,",
            f"length-bank `<={LENGTH_BANK_CAP_MM:.3f} mm`, total empirical `<={TOTAL_SURFACE_CAP_MM:.3f} mm`, and",
            "exact zero correction at B0/C0. The two permitted comparison-tolerance endpoints",
            f"`{MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM:.6f}` and",
            f"`{MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM:.6f} mm` are included. A global derivative bound",
            "adds the worst possible half-grid-cell change in both B and C. The resulting continuous",
            "low/high endpoint upper bounds are respectively",
            f"`{outer_continuous[MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM]['incremental']:.6f} / "
            f"{outer_continuous[MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM]['length_bank']:.6f} / "
            f"{outer_continuous[MODEL_MIN_LENGTH_MM - MODEL_LENGTH_TOLERANCE_MM]['total']:.6f} mm` and",
            f"`{outer_continuous[MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM]['incremental']:.6f} / "
            f"{outer_continuous[MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM]['length_bank']:.6f} / "
            f"{outer_continuous[MODEL_MAX_LENGTH_MM + MODEL_LENGTH_TOLERANCE_MM]['total']:.6f} mm`.",
            "Because correction is affine in length and vector norm is convex, the two outer",
            "length endpoints plus these angular bounds cover every intermediate B/C/L point.",
            "",
            "## Evidence Boundary",
            "",
            "The numerical envelope covers the hard software domain, but present accuracy evidence does",
            "not. T3 and T4 identify one straight slope only. The current table maximum is 181% of the",
            "T3-to-T4 span beyond T4, where nonlinear rail, spindle, or probe-length behavior is",
            "not identifiable from the existing data; the 430 mm endpoint is 199% beyond T4.",
            "Therefore only the T3-to-T4 bracket may",
            "be accepted until an independent physical endpoint test is complete.",
            "",
            "Consumed-data development scores are T4 `0.107256/0.247250 mm` RMS/max and T3",
            "`0.099481/0.206612 mm`; all 20 unique T3 poses improve. These are model-development",
            "results, not release validation.",
            "",
            "## Release Sequence",
            "",
            "1. Implement synchronous length evaluation, fail-closed guards, diagnostics, and",
            "   forward/inverse simulation tests while leaving the production configuration unchanged.",
            f"2. The dedicated validation INI now uses `lengthmodel=1 lengthmodelid={MODEL_ID}`",
            "   with `[TCPC] LENGTH_MODEL_REQUIRED=1` and loads the exact coefficient overlay",
            "   only during startup, never by sourcing it into a running session.",
            "3. Freeze code, coefficients, model ID, domain, caps, analyzer, and hashes.",
            "4. Run a fresh uninterrupted T4 101-row/28-closure validation, followed by a fresh",
            "   uninterrupted T3 31-row/14-closure validation without retuning.",
            "5. T4 is the longest available touch probe. Validate the `425-430 mm` endpoint later",
            "   with the planned dial-gauge method on an equivalent pose grid. A second endpoint",
            "   near `100-115 mm` is preferable.",
            "6. If the long endpoint fails, fit continuous short-side and long-side slopes anchored",
            "   at T4, freeze again, and require a new untouched endpoint validation.",
            "",
            "## Traceability",
            "",
            f"All `{len(REAL_TCPC_INIS)}` top-level real TCPC INIs resolve to the audited canonical",
            "tool table and define no TOOL_DATABASE override. Length-model promotion is limited to",
            f"the validation-only `{promoted[0].name}`; every production and legacy capture INI",
            "remains unpromoted.",
            f"Kinematics source SHA-256: `{sha256(KINS_SOURCE)}`.",
            f"Base HAL SHA-256: `{sha256(BASE_HAL)}`.",
            f"Canonical tool table SHA-256: `{sha256(TOOL_TABLE)}`.",
            f"Generated real-machine validation candidate HAL SHA-256: `{sha256_text(candidate_hal)}`.",
            "The compiled headless integration test independently checks runtime coefficients,",
            "range/tolerance faults, caps, model ID, and forward/inverse continuity.",
            "",
            "This auditor imports neither LinuxCNC nor HAL and cannot issue machine commands.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--candidate-hal", type=Path, default=DEFAULT_CANDIDATE_HAL)
    parser.add_argument("--check", action="store_true", help="audit only; do not write the report")
    args = parser.parse_args()
    try:
        tools, audits, promoted = run_audit()
        report = render_report(tools, audits, promoted)
        candidate_hal = render_candidate_hal()
        if args.check:
            if not args.report.exists():
                raise AuditError(f"report does not exist: {args.report}")
            if args.report.read_text(encoding="ascii") != report:
                raise AuditError("checked report differs from deterministic output")
            if not args.candidate_hal.exists():
                raise AuditError(f"candidate HAL does not exist: {args.candidate_hal}")
            if args.candidate_hal.read_text(encoding="ascii") != candidate_hal:
                raise AuditError("checked candidate HAL differs from deterministic output")
        else:
            args.report.write_text(report, encoding="ascii")
            args.candidate_hal.write_text(candidate_hal, encoding="ascii")
    except (AuditError, OSError, ValueError) as exc:
        print(f"LENGTH MODEL AUDIT FAIL: {exc}", file=sys.stderr)
        return 1
    print("LENGTH MODEL AUDIT PASS")
    for length, audit in audits.items():
        print(
            f"L={length:.6f} q={q_for_length(length):+.6f} "
            f"incremental={audit['incremental'][0]:.6f} "
            f"length_bank={audit['length_bank'][0]:.6f} "
            f"total={audit['total'][0]:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
