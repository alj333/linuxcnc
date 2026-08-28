#!/usr/bin/env python3
"""Deterministic offline preflight and result validation for T4 model revision 2026082601."""

from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import csv
import hashlib
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Callable, Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import analyze_tcpc_relocated_sphere_reachability as reach
import assess_tcpc_length_aware_bounds as bounds


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CAMPAIGN = 2026082602
MODE = 32
ATTEMPT = 1
MODEL_ID = 2026082601
TOOL = 4
TOOL_LENGTH_MM = 229.407000
PROBE_OFFSET_MM = 0.154742
DIFF_CAP_MM = 0.400000
TOTAL_CAP_MM = 1.350000
RMS_LIMIT_MM = 0.120
MAX_LIMIT_MM = 0.280
EXPECTED_ROWS = 101
EXPECTED_CLOSURES = 28
EXPECTED_TRANSACTIONS = 808
EXPECTED_UNIQUE_POSES = 76

PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_validation_2026082601.ngc"
CANONICAL_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_primary.ngc"
VALIDATION_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini"
CANDIDATE_HAL = HERE / "tcpc_length_aware_candidate_2026082601.hal"
ASSESSOR = HERE / "assess_tcpc_length_aware_bounds.py"
MODEL_PLAN = HERE / "TCPC_LENGTH_AWARE_MODEL_PLAN.md"
ANCHOR_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_anchor.py"
CAMPAIGN_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_campaign.py"
REACHABILITY_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_reachability.py"

OUTPUT_BASE = HERE / "tcpc-length-aware-t4-validation-2026082601-attempt1"
RESULTS = Path(f"{OUTPUT_BASE}-results.csv")
STATE = Path(f"{OUTPUT_BASE}-state.csv")
MODEL_STATE = Path(f"{OUTPUT_BASE}-model-state.csv")
CLOSURES = Path(f"{OUTPUT_BASE}-closures.csv")
CONTACT_TRACE = Path(f"{OUTPUT_BASE}-contact-trace.csv")
GAP_TRACE = Path(f"{OUTPUT_BASE}-gap-trace.csv")

DEFAULT_PREFLIGHT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_VALIDATION_PREFLIGHT_REPORT.md"
DEFAULT_RESULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_VALIDATION_REPORT.md"

SEALED_SHA256 = {
    VALIDATION_INI: "24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a",
    CANDIDATE_HAL: "8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14",
    PROGRAM: "0c25bad2be98eae5e927c765fea83d1b877e652635f446ff637dbf8160e308be",
    ASSESSOR: "b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2",
    MODEL_PLAN: "b8306e4612dff6ad52914ea0cd146bff39a093643f96a766836d82337ddc826e",
    ANCHOR_ANALYZER: "30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d",
    CAMPAIGN_ANALYZER: "d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a",
    REACHABILITY_ANALYZER: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
}

MODEL_STATE_FIELDS = (
    "schema_version", "campaign_id", "stage_mode", "attempt_id",
    "sample_seq", "model_id", "expected_model_id", "configured", "valid",
    "fault_code", "q", "evaluated_b_deg", "evaluated_c_deg",
    "evaluated_length_mm", "diff_offset_x_mm", "diff_offset_y_mm",
    "diff_offset_z_mm", "diff_offset_norm_mm", "empirical_offset_x_mm",
    "empirical_offset_y_mm", "empirical_offset_z_mm",
    "empirical_offset_norm_mm",
)

CONTACT_TRACE_FIELDS = (
    "schema_version", "campaign_id", "stage_mode", "attempt_id",
    "global_seq", "abs_b_deg", "abs_c_deg", "acquisition_try", "pass_id",
    "contact_id", "pre_raw_count", "pre_mux_count", "pre_gated_count",
    "post_raw_count", "post_mux_count", "post_gated_count", "ready_raw_count",
    "ready_mux_count", "ready_gated_count", "probe_result", "travel_mm",
    "raw_delta", "mux_delta", "gated_delta", "repeat_raw_delta",
    "repeat_mux_delta", "repeat_gated_delta", "extra_raw_minus_gated_delta",
    "burst_flag", "consistency_fault", "release_fault", "terminal_failure",
)

GAP_TRACE_FIELDS = (
    "schema_version", "campaign_id", "stage_mode", "attempt_id",
    "next_global_seq", "abs_b_deg", "abs_c_deg", "acquisition_try",
    "pass_id", "contact_id", "prior_ready_raw_count", "prior_ready_mux_count",
    "prior_ready_gated_count", "current_pre_raw_count", "current_pre_mux_count",
    "current_pre_gated_count", "gap_raw_delta", "gap_mux_delta",
    "gap_gated_delta", "prior_contact_extra_delta", "combined_extra_delta",
    "burst_flag", "consistency_fault", "initial_baseline",
)

OUTPUT_FIELDS = {
    RESULTS: anchor.RESULT_FIELDS,
    STATE: anchor.STATE_FIELDS,
    MODEL_STATE: MODEL_STATE_FIELDS,
    CLOSURES: campaign.CLOSURE_FIELDS,
    CONTACT_TRACE: CONTACT_TRACE_FIELDS,
    GAP_TRACE: GAP_TRACE_FIELDS,
}

GRID = tuple(reach.grid())
EXPECTED = campaign.expected_rows(GRID, campaign.T4_RANGES)
EXPECTED_BY_SEQ = {row.seq: row for row in EXPECTED}
SPEC = campaign.RunSpec(
    "T4 length-aware q=0 validation",
    TOOL,
    MODE,
    TOOL_LENGTH_MM,
    PROBE_OFFSET_MM,
    anchor.EFFECTIVE_RADIUS,
    RESULTS,
    STATE,
    CLOSURES,
    EXPECTED,
    campaign.T4_CLOSURES,
)


class ValidationError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValidationError(
            f"SHA-256 changed for {path}: {actual}, expected {expected}"
        )


def exact_int(row: dict[str, str], field: str, *, positive: bool = False) -> int:
    value = anchor.number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9 or (positive and rounded < 1):
        qualifier = "positive exact integer" if positive else "exact integer"
        raise ValidationError(f"{field}={value:.9f}, expected {qualifier}")
    return int(rounded)


def require_identity(row: dict[str, str], *, sequence_field: str) -> int:
    expected = (
        ("schema_version", 1),
        ("campaign_id", CAMPAIGN),
        ("stage_mode", MODE),
        ("attempt_id", ATTEMPT),
    )
    for field, value in expected:
        if exact_int(row, field, positive=field != "stage_mode") != value:
            raise ValidationError(f"{field} does not match the validation identity")
    seq = exact_int(row, sequence_field, positive=True)
    if seq not in EXPECTED_BY_SEQ:
        raise ValidationError(f"{sequence_field}={seq} is outside 1..101")
    return seq


def read_rows(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="ascii") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(fields):
                raise ValidationError(f"{path}: exact schema mismatch")
            rows = list(reader)
    except UnicodeError as exc:
        raise ValidationError(f"{path}: output is not ASCII") from exc
    for line_number, row in enumerate(rows, 2):
        if None in row or any(row.get(field) is None for field in fields):
            raise ValidationError(f"{path}:{line_number}: surplus or missing fields")
    return rows


def validate_header_rows(rows: Sequence[Sequence[str]], fields: Sequence[str]) -> None:
    if list(map(list, rows)) != [list(fields)]:
        raise ValidationError("output is not the exact header-only schema")


def validate_header_only_files() -> None:
    for path, fields in OUTPUT_FIELDS.items():
        try:
            with path.open(newline="", encoding="ascii") as stream:
                rows = list(csv.reader(stream))
        except UnicodeError as exc:
            raise ValidationError(f"{path}: header is not ASCII") from exc
        try:
            validate_header_rows(rows, fields)
        except ValidationError as exc:
            raise ValidationError(f"{path}: {exc}") from exc


def subroutine_text(text: str, name: str) -> str:
    match = re.search(
        rf"^o<{re.escape(name)}> sub\s*$[\s\S]*?^o<{re.escape(name)}> endsub\s*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        raise ValidationError(f"program is missing protected subroutine {name}")
    return match.group(0)


def grid_body_fragment(text: str) -> str:
    match = re.search(
        r"^  \(Seq 1-9: opening B0 full-C reference and closure\.\)\s*$"
        r"[\s\S]*?"
        r"^  o<tcpc_primary_closure_guard> call \[#780\] \[#781\] \[#782\] "
        r"\[900\.0\] \[1\.0\] \[#726\]\s*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        raise ValidationError("program is missing the canonical 101-pose body")
    return match.group(0)


def validate_no_direct_hal_writes(text: str) -> None:
    active = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("(")
    ]
    forbidden_words = re.compile(
        r"\b(?:halcmd|setp|sets|net|loadrt|loadusr|source)\b", re.IGNORECASE
    )
    for line in active:
        if forbidden_words.search(line):
            raise ValidationError(f"runner contains direct HAL mutation: {line}")
        if re.match(r"^M(?:62|63|64)\b", line, re.IGNORECASE):
            raise ValidationError(f"runner contains a forbidden digital-output command: {line}")
        if re.match(r"^M65\b", line, re.IGNORECASE) and not re.fullmatch(
            r"M65\s+P[01](?:\.0*)?", line, re.IGNORECASE
        ):
            raise ValidationError(f"runner contains non-safety M65 output: {line}")
    top_level_m65 = [
        line.strip().upper() for line in text.splitlines() if line.startswith("M65")
    ]
    if top_level_m65.count("M65 P0") != 2 or top_level_m65.count("M65 P1") != 2:
        raise ValidationError("frozen top-level M65 P0/P1 safety-clear count changed")


def validate_python_safety(text: str) -> None:
    tree = ast.parse(text)
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".", 1)[0]]
        if set(names) & {"linuxcnc", "hal"}:
            raise ValidationError("validator must not import linuxcnc or hal")


def validate_program_text(text: str, canonical: str) -> None:
    lines = text.splitlines()
    if max((len(line) for line in lines), default=0) > 256:
        longest = max(range(len(lines)), key=lambda index: len(lines[index])) + 1
        raise ValidationError(
            f"runner line {longest} is {len(lines[longest - 1])} chars; limit is 256"
        )
    required_identity = (
        "#711 = 32.0",
        "#715 = 2026082602.0",
        "#716 = 2.0",
        "#727 = 1.0",
        "#516 = 229.407000",
        "#717 = 0.154742",
        "#3032 = #717",
        "#707 = 101.0",
    )
    for snippet in required_identity:
        if text.count(snippet) != 1:
            raise ValidationError(f"runner identity contract changed for {snippet!r}")
    if len(re.findall(r"^\s*M0\s*$", text, re.MULTILINE)) != 1:
        raise ValidationError("runner must contain exactly one M0")
    if re.search(r"^\s*M1\s*$", text, re.MULTILINE):
        raise ValidationError("runner must not contain M1")
    dwell_lines = re.findall(r"^\s*G4\b.*$", text, re.MULTILINE)
    if dwell_lines != ["    G4 P0.05", "    G4 P0.05"]:
        raise ValidationError("runner dwell contract changed; only two 0.05 s gates are allowed")
    validate_no_direct_hal_writes(text)

    expected_paths = {str(path) for path in OUTPUT_FIELDS}
    logged_paths = re.findall(r"\(LOGAPPEND,([^\r\n)]+)\)", text)
    if len(logged_paths) != 6 or set(logged_paths) != expected_paths:
        raise ValidationError("runner LOGAPPEND paths differ from the six dedicated outputs")
    if any(logged_paths.count(path) != 1 for path in expected_paths):
        raise ValidationError("a dedicated runner output path is not logged exactly once")

    for name in (
        "tcpc_primary_outer_reference",
        "tcpc_primary_b0_sweep",
        "tcpc_primary_low_tilt_block",
        "tcpc_primary_tilt_block",
    ):
        if subroutine_text(text, name) != subroutine_text(canonical, name):
            raise ValidationError(f"runner changed canonical motion/grid subroutine {name}")
    if grid_body_fragment(text) != grid_body_fragment(canonical):
        raise ValidationError("runner changed the canonical 101-pose/28-closure body")
    if len(EXPECTED) != EXPECTED_ROWS or len(campaign.T4_CLOSURES) != EXPECTED_CLOSURES:
        raise ValidationError("imported canonical grid/topology is not 101 rows/28 closures")

    required_guards = (
        "o<tcpc_length_model_guard> sub",
        "o<tcpc_pair_live_guard> sub",
        "o<tcpc_pair_probe_final_guard> sub",
        "headheadkins.length-model.configured",
        "headheadkins.length-model.valid",
        "headheadkins.length-model.fault-code",
        "headheadkins.length-model.expected-id",
        "headheadkins.length-model.q",
        "headheadkins.tool-offset-eval.length",
        "headheadkins.length-model.diff-offset-norm",
        "headheadkins.empirical-offset-norm",
        "o<model_state_sequence_complete> if",
        "o<trace_pair_count> if",
        "o<trace_minimum_count> if",
    )
    for snippet in required_guards:
        if snippet not in text:
            raise ValidationError(f"runner is missing guard/log contract {snippet!r}")
    live_guard = subroutine_text(text, "tcpc_pair_live_guard")
    final_guard = subroutine_text(text, "tcpc_pair_probe_final_guard")
    if "o<tcpc_length_model_guard> call" not in live_guard:
        raise ValidationError("live guard no longer validates the length model")
    if "o<tcpc_pair_live_guard> call" not in final_guard:
        raise ValidationError("final pre-G38 guard no longer performs the live/model guard")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ValidationError("four-contact subroutine must have four G38.3 sites")
    guarded_g38 = re.findall(
        r"o<tcpc_pair_probe_final_guard> call \[#520\] \[#521\]\s*\n\s*G38\.3\b",
        text,
    )
    if len(guarded_g38) != 4:
        raise ValidationError("every G38.3 must have the immediate final guard")
    for call, count in (
        ("o<tcpc_contact_trace_begin> call", 8),
        ("o<tcpc_contact_trace_post> call", 4),
        ("o<tcpc_contact_trace_finish> call [0.0]", 4),
        ("o<tcpc_contact_trace_finish> call [1.0]", 4),
    ):
        if text.count(call) != count:
            raise ValidationError(f"transaction call count changed for {call}")


def validate_program() -> None:
    require_hash(PROGRAM, SEALED_SHA256[PROGRAM])
    text = PROGRAM.read_text(encoding="ascii")
    canonical = CANONICAL_PROGRAM.read_text(encoding="ascii")
    validate_program_text(text, canonical)
    validate_python_safety(Path(__file__).read_text(encoding="ascii"))


def validate_configuration() -> None:
    for path, digest in SEALED_SHA256.items():
        require_hash(path, digest)
    ini = VALIDATION_INI.read_text(encoding="ascii")
    required_ini = (
        "KINEMATICS = headheadkins coordinates=XYZBC kinstype=B lengthmodel=1 lengthmodelid=2026082601",
        "LENGTH_MODEL_REQUIRED = 1",
        "HALFILE = tcpc_probe_attempt3_edge_counters.hal",
        "HALFILE = tcpc_length_aware_candidate_2026082601.hal",
    )
    for line in required_ini:
        if ini.count(line) != 1:
            raise ValidationError(f"validation INI contract changed for {line!r}")
    halfiles = [
        line.strip() for line in ini.splitlines()
        if line.strip().startswith("HALFILE =")
    ]
    if not halfiles or halfiles[-1] != required_ini[-1]:
        raise ValidationError("length-aware overlay is not the final validation HALFILE")
    overlay = CANDIDATE_HAL.read_text(encoding="ascii")
    if overlay.count("setp headheadkins.length-model.id 0") != 1:
        raise ValidationError("candidate overlay no longer begins with model-ID invalidation")
    if overlay.count(f"setp headheadkins.length-model.id {MODEL_ID}") != 1:
        raise ValidationError("candidate overlay no longer commits the frozen model ID")
    if overlay.rstrip().splitlines()[-1] != f"setp headheadkins.length-model.id {MODEL_ID}":
        raise ValidationError("candidate overlay model-ID commit is not the final command")


def run_length_model_audit() -> str:
    completed = subprocess.run(
        [sys.executable, str(ASSESSOR), "--check"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0 or "LENGTH MODEL AUDIT PASS" not in completed.stdout:
        tail = "\n".join(completed.stdout.splitlines()[-12:])
        raise ValidationError(f"length-model audit failed ({completed.returncode}):\n{tail}")
    return completed.stdout


def run_rs274_preview() -> None:
    live_names = {
        "linuxcnc", "linuxcncsvr", "milltask", "milltask.bin", "rtapi_app",
        "probe_basic", "qtpyvcp",
    }
    active: list[str] = []
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            name = (entry / "comm").read_text(encoding="ascii").strip()
        except (OSError, UnicodeError):
            continue
        if name in live_names:
            active.append(f"{entry.name}:{name}")
    if active:
        raise ValidationError(
            "refusing standalone rs274 while controller processes are active: "
            + ", ".join(sorted(active))
        )
    with tempfile.TemporaryDirectory(prefix="tcpc-length-aware-rs274-") as isolated_home:
        env = os.environ.copy()
        env["HOME"] = isolated_home
        completed = subprocess.run(
            [str(REPO_ROOT / "bin/rs274"), "-g", str(PROGRAM)],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-12:])
        raise ValidationError(f"standalone bin/rs274 -g failed ({completed.returncode}):\n{tail}")


def offline_contract(*, header_only: bool) -> None:
    validate_configuration()
    validate_program()
    run_length_model_audit()
    run_rs274_preview()
    if header_only:
        validate_header_only_files()


@contextmanager
def validation_campaign_context():
    """Reuse the proven campaign validators under this frozen campaign identity."""
    previous = campaign.CAMPAIGN
    campaign.CAMPAIGN = CAMPAIGN
    try:
        yield
    finally:
        campaign.CAMPAIGN = previous


def validate_results_state_closures() -> tuple[dict[int, np.ndarray], np.ndarray]:
    results = read_rows(RESULTS, anchor.RESULT_FIELDS)
    states = read_rows(STATE, anchor.STATE_FIELDS)
    closures = read_rows(CLOSURES, campaign.CLOSURE_FIELDS)
    if len(results) != EXPECTED_ROWS or len(states) != EXPECTED_ROWS:
        raise ValidationError(
            f"expected 101 result/state rows, got {len(results)}/{len(states)}"
        )
    result_seq = [exact_int(row, "sample_seq", positive=True) for row in results]
    state_seq = [exact_int(row, "sample_seq", positive=True) for row in states]
    exact_sequence = list(range(1, EXPECTED_ROWS + 1))
    if result_seq != exact_sequence or state_seq != exact_sequence:
        raise ValidationError("result/state rows are not the exact ordered 1..101 sequence")

    centers: dict[int, np.ndarray] = {}
    with validation_campaign_context():
        for result, state, expected in zip(results, states, EXPECTED):
            centers[expected.seq] = campaign.validate_result(
                SPEC, result, expected, ATTEMPT
            )
            campaign.validate_state(SPEC, state, result, expected, ATTEMPT)
        results_by_seq = {expected.seq: row for expected, row in zip(EXPECTED, results)}
        closure_norms = campaign.validate_closures(
            SPEC, closures, results_by_seq, ATTEMPT
        )
    if len(closure_norms) != EXPECTED_CLOSURES:
        raise ValidationError("closure validator did not return exactly 28 closures")
    return centers, closure_norms


def expected_empirical_vector(b_deg: float, c_deg: float) -> np.ndarray:
    basis = bounds.basis_values(b_deg, np.asarray([c_deg], dtype=float))
    coefficients = bounds.surface_coefficients(TOOL_LENGTH_MM)["total"]
    return bounds.evaluate_surface(basis, coefficients)[0]


def validate_model_row(row: dict[str, str], expected: campaign.ExpectedRow) -> None:
    seq = require_identity(row, sequence_field="sample_seq")
    if seq != expected.seq:
        raise ValidationError(f"model-state sequence {seq} is out of order")
    for field, value in (
        ("model_id", MODEL_ID),
        ("expected_model_id", MODEL_ID),
        ("configured", 1),
        ("valid", 1),
        ("fault_code", 0),
    ):
        if exact_int(row, field) != value:
            raise ValidationError(f"model-state seq {seq}: {field} mismatch")
    anchor.near(row, "q", 0.0, 1e-6)
    if campaign.angular_error(
        anchor.number(row, "evaluated_b_deg"), expected.pose.b_deg
    ) > 0.01:
        raise ValidationError(f"model-state seq {seq}: evaluated B mismatch")
    if campaign.angular_error(
        anchor.number(row, "evaluated_c_deg"), expected.pose.c_deg
    ) > 0.01:
        raise ValidationError(f"model-state seq {seq}: evaluated C mismatch")
    anchor.near(row, "evaluated_length_mm", TOOL_LENGTH_MM, 0.002)

    diff = np.asarray(
        [anchor.number(row, f"diff_offset_{axis}_mm") for axis in "xyz"],
        dtype=float,
    )
    diff_norm = anchor.number(row, "diff_offset_norm_mm")
    if np.max(np.abs(diff)) > 1e-6 or abs(diff_norm) > 1e-6:
        raise ValidationError(f"model-state seq {seq}: T4 q=0 differential bank is nonzero")
    if abs(diff_norm - float(np.linalg.norm(diff))) > 3e-6 or diff_norm > DIFF_CAP_MM:
        raise ValidationError(f"model-state seq {seq}: differential norm/cap mismatch")

    empirical = np.asarray(
        [anchor.number(row, f"empirical_offset_{axis}_mm") for axis in "xyz"],
        dtype=float,
    )
    empirical_norm = anchor.number(row, "empirical_offset_norm_mm")
    if empirical_norm < 0.0 or empirical_norm > TOTAL_CAP_MM:
        raise ValidationError(f"model-state seq {seq}: empirical norm exceeds cap")
    if abs(empirical_norm - float(np.linalg.norm(empirical))) > 5e-6:
        raise ValidationError(f"model-state seq {seq}: empirical vector/norm mismatch")
    offline = expected_empirical_vector(expected.pose.b_deg, expected.pose.c_deg)
    if float(np.linalg.norm(empirical - offline)) > 2e-5:
        raise ValidationError(
            f"model-state seq {seq}: empirical vector differs from sealed q=0 model"
        )


def validate_model_states() -> None:
    rows = read_rows(MODEL_STATE, MODEL_STATE_FIELDS)
    if len(rows) != EXPECTED_ROWS:
        raise ValidationError(f"expected 101 model-state rows, got {len(rows)}")
    for row, expected in zip(rows, EXPECTED):
        validate_model_row(row, expected)


def counter_tuple(row: dict[str, str], prefix: str) -> tuple[int, int, int]:
    return tuple(exact_int(row, f"{prefix}_{name}_count") for name in ("raw", "mux", "gated"))


def expected_transaction_keys() -> list[tuple[int, int, int, int]]:
    return [
        (seq, 1, pass_id, contact_id)
        for seq in range(1, EXPECTED_ROWS + 1)
        for pass_id in (1, 2)
        for contact_id in (1, 2, 3, 4)
    ]


def trace_key(row: dict[str, str], sequence_field: str) -> tuple[int, int, int, int]:
    return (
        require_identity(row, sequence_field=sequence_field),
        exact_int(row, "acquisition_try", positive=True),
        exact_int(row, "pass_id", positive=True),
        exact_int(row, "contact_id", positive=True),
    )


def validate_trace_pose(row: dict[str, str], seq: int) -> None:
    expected = EXPECTED_BY_SEQ[seq]
    if campaign.angular_error(anchor.number(row, "abs_b_deg"), expected.pose.b_deg) > 0.01:
        raise ValidationError(f"trace seq {seq}: B pose mismatch")
    if campaign.angular_error(anchor.number(row, "abs_c_deg"), expected.pose.c_deg) > 0.01:
        raise ValidationError(f"trace seq {seq}: C pose mismatch")


def validate_contact_traces() -> list[dict[str, str]]:
    rows = read_rows(CONTACT_TRACE, CONTACT_TRACE_FIELDS)
    if len(rows) != EXPECTED_TRANSACTIONS:
        raise ValidationError(f"expected exactly 808 contact traces, got {len(rows)}")
    keys = [trace_key(row, "global_seq") for row in rows]
    if keys != expected_transaction_keys():
        raise ValidationError("contact traces are not exact try1/pass1-2/contact1-4 order")
    for row, key in zip(rows, keys):
        seq, _, _, contact_id = key
        validate_trace_pose(row, seq)
        pre = counter_tuple(row, "pre")
        post = counter_tuple(row, "post")
        ready = counter_tuple(row, "ready")
        if any(value < 0 for value in pre + post + ready):
            raise ValidationError(f"contact trace seq {seq}: negative counter")
        if any(not (pre[i] <= post[i] <= ready[i]) for i in range(3)):
            raise ValidationError(f"contact trace seq {seq}: non-monotonic counter")
        direct = tuple(post[i] - pre[i] for i in range(3))
        repeats = tuple(ready[i] - post[i] for i in range(3))
        for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
            if exact_int(row, field) != value:
                raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
        for field, value in zip(
            ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats
        ):
            if exact_int(row, field) != value:
                raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
        if direct != (1, 1, 1):
            raise ValidationError(f"contact trace seq {seq}: G38 edge delta is not 1/1/1")
        if repeats[0] != repeats[1] or repeats[2] != 0:
            raise ValidationError(f"contact trace seq {seq}: repeat-edge consistency failure")
        extra = (ready[0] - pre[0]) - (ready[2] - pre[2])
        if exact_int(row, "extra_raw_minus_gated_delta") != extra:
            raise ValidationError(f"contact trace seq {seq}: extra-edge delta mismatch")
        if extra < 0 or extra > 2:
            raise ValidationError(f"contact trace seq {seq}: retrigger burst exceeds gate")
        for field in (
            "burst_flag", "consistency_fault", "release_fault", "terminal_failure"
        ):
            if exact_int(row, field) != 0:
                raise ValidationError(f"contact trace seq {seq}: {field} is nonzero")
        if exact_int(row, "probe_result") != 1:
            raise ValidationError(f"contact trace seq {seq}: probe result is not success")
        travel = anchor.number(row, "travel_mm")
        upper = 7.01 if contact_id == 1 else 6.01
        if not 1.0 <= travel <= upper:
            raise ValidationError(f"contact trace seq {seq}: travel is outside bounds")
    return rows


def validate_gap_traces(contacts: Sequence[dict[str, str]]) -> None:
    rows = read_rows(GAP_TRACE, GAP_TRACE_FIELDS)
    if len(rows) != EXPECTED_TRANSACTIONS:
        raise ValidationError(f"expected exactly 808 gap traces, got {len(rows)}")
    keys = [trace_key(row, "next_global_seq") for row in rows]
    if keys != expected_transaction_keys():
        raise ValidationError("gap traces are not exact try1/pass1-2/contact1-4 order")
    previous_contact: dict[str, str] | None = None
    for index, (gap, contact, key) in enumerate(zip(rows, contacts, keys)):
        seq = key[0]
        if trace_key(contact, "global_seq") != key:
            raise ValidationError(f"gap trace seq {seq}: contact transaction key mismatch")
        validate_trace_pose(gap, seq)
        prior = counter_tuple(gap, "prior_ready")
        current = counter_tuple(gap, "current_pre")
        if any(value < 0 for value in prior + current):
            raise ValidationError(f"gap trace seq {seq}: negative counter")
        delta = tuple(current[i] - prior[i] for i in range(3))
        if any(value < 0 for value in delta):
            raise ValidationError(f"gap trace seq {seq}: non-monotonic counter")
        for field, value in zip(("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"), delta):
            if exact_int(gap, field) != value:
                raise ValidationError(f"gap trace seq {seq}: {field} mismatch")
        initial = exact_int(gap, "initial_baseline")
        if initial != int(index == 0):
            raise ValidationError("only the first gap row may mark the post-M0 baseline")
        prior_extra = exact_int(gap, "prior_contact_extra_delta")
        if previous_contact is None:
            if prior_extra != 0:
                raise ValidationError("initial gap has nonzero prior-contact extra delta")
        else:
            if prior != counter_tuple(previous_contact, "ready"):
                raise ValidationError(f"gap trace seq {seq}: prior-ready boundary changed")
            if prior_extra != exact_int(previous_contact, "extra_raw_minus_gated_delta"):
                raise ValidationError(f"gap trace seq {seq}: prior-contact extra changed")
        if current != counter_tuple(contact, "pre"):
            raise ValidationError(f"gap trace seq {seq}: current-pre/contact-pre mismatch")
        combined = prior_extra + delta[0] - delta[2]
        if exact_int(gap, "combined_extra_delta") != combined:
            raise ValidationError(f"gap trace seq {seq}: combined extra delta mismatch")
        consistency = delta[0] != delta[1] or delta[2] != 0 or (
            initial == 1 and any(delta)
        )
        if combined > 2 or consistency:
            raise ValidationError(f"gap trace seq {seq}: electrical gate failure")
        for field in ("burst_flag", "consistency_fault"):
            if exact_int(gap, field) != 0:
                raise ValidationError(f"gap trace seq {seq}: {field} is nonzero")
        previous_contact = contact


def centered_metric(values: np.ndarray) -> tuple[float, float]:
    residuals = values - np.mean(values, axis=0)
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms * norms))), float(np.max(norms))


def center_metrics(centers: dict[int, np.ndarray]) -> dict[str, float]:
    raw = np.vstack([centers[seq] for seq in range(1, EXPECTED_ROWS + 1)])
    groups: dict[tuple[float, float], list[np.ndarray]] = {}
    for expected in EXPECTED:
        key = (round(expected.pose.b_deg, 9), round(expected.pose.c_deg % 360.0, 9))
        groups.setdefault(key, []).append(centers[expected.seq])
    if len(groups) != EXPECTED_UNIQUE_POSES:
        raise ValidationError(
            f"expected exactly {EXPECTED_UNIQUE_POSES} unique poses, got {len(groups)}"
        )
    unique = np.vstack([np.mean(np.vstack(values), axis=0) for values in groups.values()])
    raw_rms, raw_max = centered_metric(raw)
    unique_rms, unique_max = centered_metric(unique)
    for label, rms, maximum in (
        ("raw", raw_rms, raw_max),
        ("equal-unique", unique_rms, unique_max),
    ):
        if rms > RMS_LIMIT_MM or maximum > MAX_LIMIT_MM:
            raise ValidationError(
                f"{label} centered RMS/max {rms:.6f}/{maximum:.6f} mm exceeds "
                f"{RMS_LIMIT_MM:.3f}/{MAX_LIMIT_MM:.3f} mm"
            )
    return {
        "raw_count": float(len(raw)),
        "unique_count": float(len(unique)),
        "raw_rms": raw_rms,
        "raw_max": raw_max,
        "unique_rms": unique_rms,
        "unique_max": unique_max,
    }


def validate_completed_run() -> tuple[dict[str, float], np.ndarray]:
    offline_contract(header_only=False)
    centers, closure_norms = validate_results_state_closures()
    validate_model_states()
    contacts = validate_contact_traces()
    validate_gap_traces(contacts)
    return center_metrics(centers), closure_norms


def write_preflight_report(path: Path) -> None:
    lines = [
        "# TCPC Length-Aware T4 Validation Preflight",
        "",
        "Status: `PASS`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- model ID: `{MODEL_ID}`",
        f"- probe: `T4 / H4 / {TOOL_LENGTH_MM:.6f} mm / #3032={PROBE_OFFSET_MM:.6f}`",
        f"- canonical acquisition: `{EXPECTED_ROWS}` result/state/model-state rows, "
        f"`{EXPECTED_CLOSURES}` closures, `{EXPECTED_TRANSACTIONS}` contact and gap traces",
        "- parser: standalone in-tree `bin/rs274 -g` passed under an isolated temporary HOME",
        "- controller-process gate: no LinuxCNC, linuxcncsvr, milltask, rtapi_app, Probe Basic, or QtPyVCP process was active",
        "",
        "## Sealed Inputs",
        "",
    ]
    for item in SEALED_SHA256:
        lines.append(f"- `{item.relative_to(REPO_ROOT)}`: `{sha256(item)}`")
    lines.extend(
        [
            f"- validator: `{sha256(Path(__file__).resolve())}`",
            "",
            "## Fresh Outputs",
            "",
            "All six attempt-1 files are exact header-only ASCII files:",
            "",
            "| output | columns | header SHA-256 |",
            "| --- | ---: | --- |",
        ]
    )
    for output, fields in OUTPUT_FIELDS.items():
        lines.append(
            f"| `{output.name}` | {len(fields)} | `{sha256(output)}` |"
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "The frozen runner has one initial M0, no M1, no long dwell, no direct HAL or coefficient mutation, and only its reviewed deassert-only M65 P0/P1 safety clears. The canonical 101-pose/28-closure T4 grid, every G38 transaction layer, model/live/final guards, and six isolated LOGAPPEND destinations passed static checks.",
            "",
            "The deterministic full-length-domain model audit passed. This physical acquisition validates T4 at `q=0` only; it does not validate the differential length bank or extrapolated longer tools. Those remain assigned to later T3 and dial-gauge validation.",
            "",
            "This validator imports neither LinuxCNC nor HAL and issues no machine-control command.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")


def write_result_report(
    path: Path, metrics: dict[str, float], closure_norms: np.ndarray
) -> None:
    lines = [
        "# TCPC Length-Aware T4 Validation Result",
        "",
        "Status: `PASS`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- exact rows: `{EXPECTED_ROWS}` results, `{EXPECTED_ROWS}` state, `{EXPECTED_ROWS}` model-state",
        f"- closures: `{len(closure_norms)}`; worst `{float(np.max(closure_norms)):.6f} mm`",
        f"- transaction traces: `{EXPECTED_TRANSACTIONS}` contact / `{EXPECTED_TRANSACTIONS}` gap",
        f"- raw-{int(metrics['raw_count'])} centered RMS / max: `{metrics['raw_rms']:.6f} / {metrics['raw_max']:.6f} mm`",
        f"- equal-unique-{int(metrics['unique_count'])} centered RMS / max: `{metrics['unique_rms']:.6f} / {metrics['unique_max']:.6f} mm`",
        f"- acceptance limits: RMS `<={RMS_LIMIT_MM:.3f} mm`, max `<={MAX_LIMIT_MM:.3f} mm`",
        "",
        "All identities, poses, T4 tool/TLO values, model snapshots, q=0 differential bank, empirical vectors/norms/caps, transaction counters/flags, and closure mappings passed.",
        "",
        "This T4 acquisition validates the common model surface at `q=0` only. It does not validate the length differential or longer-tool extrapolation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="ascii")


def expect_failure(label: str, operation: Callable[[], None]) -> None:
    try:
        operation()
    except (ValidationError, anchor.ValidationError, ValueError, SyntaxError):
        return
    raise AssertionError(f"self-test mutation was accepted: {label}")


def synthetic_model_row(expected: campaign.ExpectedRow) -> dict[str, str]:
    empirical = expected_empirical_vector(expected.pose.b_deg, expected.pose.c_deg)
    row = {field: "0" for field in MODEL_STATE_FIELDS}
    row.update(
        schema_version="1",
        campaign_id=str(CAMPAIGN),
        stage_mode=str(MODE),
        attempt_id=str(ATTEMPT),
        sample_seq=str(expected.seq),
        model_id=str(MODEL_ID),
        expected_model_id=str(MODEL_ID),
        configured="1",
        valid="1",
        fault_code="0",
        q="0",
        evaluated_b_deg=f"{expected.pose.b_deg:.9f}",
        evaluated_c_deg=f"{expected.pose.c_deg:.9f}",
        evaluated_length_mm=f"{TOOL_LENGTH_MM:.9f}",
        diff_offset_x_mm="0",
        diff_offset_y_mm="0",
        diff_offset_z_mm="0",
        diff_offset_norm_mm="0",
        empirical_offset_x_mm=f"{empirical[0]:.9f}",
        empirical_offset_y_mm=f"{empirical[1]:.9f}",
        empirical_offset_z_mm=f"{empirical[2]:.9f}",
        empirical_offset_norm_mm=f"{np.linalg.norm(empirical):.9f}",
    )
    return row


def self_test() -> None:
    offline_contract(header_only=True)
    assert len(EXPECTED) == EXPECTED_ROWS
    assert len(campaign.T4_CLOSURES) == EXPECTED_CLOSURES
    assert len(expected_transaction_keys()) == EXPECTED_TRANSACTIONS
    assert len({
        (round(expected.pose.b_deg, 9), round(expected.pose.c_deg % 360.0, 9))
        for expected in EXPECTED
    }) == EXPECTED_UNIQUE_POSES

    text = PROGRAM.read_text(encoding="ascii")
    canonical = CANONICAL_PROGRAM.read_text(encoding="ascii")
    mutations = {
        "campaign": text.replace("#715 = 2026082602.0", "#715 = 2026082603.0", 1),
        "M0": text.replace("\nM0\n", "\n", 1),
        "long dwell": text.replace("G4 P0.05", "G4 P20", 1),
        "output path": text.replace(
            f"(LOGAPPEND,{RESULTS})",
            f"(LOGAPPEND,{str(RESULTS).replace('attempt1', 'attempt2')})",
            1,
        ),
        "direct HAL write": text + "\nsetp headheadkins.length-model.id 7\n",
        "non-safety M65": text.replace("M65 P0", "M65 P2", 1),
        "final G38 guard": text.replace(
            "o<tcpc_pair_probe_final_guard> call [#520] [#521]\n  G38.3",
            "o<tcpc_pair_live_guard> call [1.0] [#520] [#521]\n  G38.3",
            1,
        ),
        "model pin": text.replace(
            "headheadkins.length-model.expected-id",
            "headheadkins.length-model.unchecked-id",
        ),
        "line length": text + "\n(" + ("x" * 257) + ")\n",
    }
    for label, mutated in mutations.items():
        expect_failure(label, lambda value=mutated: validate_program_text(value, canonical))

    valid_header = [list(MODEL_STATE_FIELDS)]
    validate_header_rows(valid_header, MODEL_STATE_FIELDS)
    bad_header = [list(MODEL_STATE_FIELDS)]
    bad_header[0][5] = "wrong_model_id"
    expect_failure(
        "model-state header",
        lambda: validate_header_rows(bad_header, MODEL_STATE_FIELDS),
    )

    expected = EXPECTED_BY_SEQ[62]
    valid_model = synthetic_model_row(expected)
    validate_model_row(valid_model, expected)
    for field, value in (
        ("model_id", str(MODEL_ID + 1)),
        ("q", "0.01"),
        ("evaluated_b_deg", str(expected.pose.b_deg + 1.0)),
        ("diff_offset_x_mm", "0.001"),
        ("empirical_offset_norm_mm", "1.35"),
    ):
        mutated = dict(valid_model)
        mutated[field] = value
        expect_failure(
            f"model-state {field}",
            lambda row=mutated: validate_model_row(row, expected),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preflight", action="store_true", help="validate frozen inputs and exact header-only outputs")
    group.add_argument("--self-test", action="store_true", help="run integration and in-memory mutation tests")
    parser.add_argument("--report", type=Path, help="override the mode-specific report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("TCPC length-aware T4 validator self-test: PASS")
            return 0
        if args.preflight:
            offline_contract(header_only=True)
            report = args.report or DEFAULT_PREFLIGHT_REPORT
            write_preflight_report(report)
            print("TCPC length-aware T4 preflight: PASS")
        else:
            metrics, closure_norms = validate_completed_run()
            report = args.report or DEFAULT_RESULT_REPORT
            write_result_report(report, metrics, closure_norms)
            print("TCPC length-aware T4 result validation: PASS")
        print(f"report: {report}")
        return 0
    except (
        AssertionError,
        OSError,
        subprocess.SubprocessError,
        ValidationError,
        anchor.ValidationError,
        bounds.AuditError,
        ValueError,
    ) as exc:
        print(f"TCPC length-aware T4 validation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
