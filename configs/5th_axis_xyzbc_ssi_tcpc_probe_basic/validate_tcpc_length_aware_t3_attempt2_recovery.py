#!/usr/bin/env python3
"""Static preflight and offline result validation for the T3 recovery.

This module only reads ordinary files. It deliberately does not import LinuxCNC
or HAL and never starts rs274 or another subprocess, so --static/--preflight are
safe to run while the controller is active.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
import sys
from typing import Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import analyze_tcpc_relocated_sphere_reachability as reach
import validate_tcpc_length_aware_t3_attempt1 as frozen


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t3_validation_2026082601_attempt2_recovery.ngc"
ATTEMPT1_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t3_validation_2026082601_attempt1.ngc"
RECOVERY_BASE = HERE / "tcpc-length-aware-t3-validation-2026082601-attempt2-recovery"
ATTEMPT1_BASE = HERE / "tcpc-length-aware-t3-validation-2026082601-attempt1"

PROGRAM_SHA256 = "1924e4af8be964a29442f23903e3566daceb4e65dde0e334bd595ba2dcb31294"
ATTEMPT1_PROGRAM_SHA256 = "d6158b9ff91f5fa73a11071d314c64a442d6747f6758587415ece7c867e53bd6"
CAMPAIGN = 2026082602
MODE = 34
ATTEMPT = 2
MODEL_ID = 2026082601
TOOL = 3
TOOL_LENGTH_MM = 128.606729
PROBE_OFFSET_MM = 0.117658
EFFECTIVE_RADIUS_MM = 17.882342
EXPECTED_ROWS = 11
EXPECTED_CLOSURES = 6
EXPECTED_TRANSACTIONS = 88
MAX_FILTERED_EXTRA_EDGES = 2
BRIDGE_LIMIT_MM = 0.050
RMS_LIMIT_MM = 0.120
MAX_LIMIT_MM = 0.280

SUFFIXES = (
    "results",
    "state",
    "model-state",
    "closures",
    "contact-trace",
    "gap-trace",
)
FILES = {suffix: Path(f"{RECOVERY_BASE}-{suffix}.csv") for suffix in SUFFIXES}
ATTEMPT1_FILES = {
    suffix: Path(f"{ATTEMPT1_BASE}-{suffix}.csv") for suffix in SUFFIXES
}
ATTEMPT1_PARTIAL_HASHES = {
    "results": "6685fcf140f44a11f4f9c51baa990d813da42b6a47b83fd61be9873bdb1923a5",
    "state": "386a785d24113b9619cb5b388db9a8f5fdc825b4ffab4c6d03a4bc0bdefb2208",
    "model-state": "4a65e1995e8c4d942cf38cfe0255c716bd3bc7d2301febe3dbdeaa8766fc3785",
    "closures": "aad7d8356c14d1063ce63a9e16fb5564e7b2e8f2bd0f132bd62a951e2f883efb",
    "contact-trace": "d9ab34e836e6ee260aebe397ac0faa74465d8f0d85732f2d279f54c95ef23925",
    "gap-trace": "da6b21e3def9740c86257c8c55aebd499252ee1ac62d79734a1b91e2408d9fd9",
}
IMPORTED_VALIDATION_HASHES = {
    HERE / "validate_tcpc_length_aware_t3_attempt1.py": "88ddd9a4ead0d5a461cb7de7caa919cb878e0dcaf9dcf7633902abd86a8fbdae",
    HERE / "analyze_tcpc_relocated_sphere_anchor.py": "30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d",
    HERE / "analyze_tcpc_relocated_sphere_campaign.py": "d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a",
    HERE / "analyze_tcpc_relocated_sphere_reachability.py": "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    HERE / "assess_tcpc_length_aware_bounds.py": "b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2",
    HERE / "fit_tcpc_dual_probe.py": "7f005200a42bda0c2ccd39352fa1da71e6ba33d5d7f566bd5255c3548315bb97",
    HERE / "assess_tcpc_r3_feasibility.py": "4520081bb7e7b4088a555e498ad7e6430dd3f5fc2d3d93a8a1e4c9867eaa6dd1",
}


class ValidationError(RuntimeError):
    pass


class Pose(tuple):
    __slots__ = ()

    def __new__(cls, b_deg: float, c_deg: float):
        return tuple.__new__(cls, (float(b_deg), float(c_deg)))

    @property
    def b_deg(self) -> float:
        return self[0]

    @property
    def c_deg(self) -> float:
        return self[1]


# seq, block, anchor, is_closure, pose, canonical Attempt-1 sequence (or None)
RECOVERY_ROWS = (
    (1, 901, 1, 0, Pose(0, 0), None),
    (2, -90, 1, 0, Pose(-90, 0), None),
    (3, -90, 2, 0, Pose(-90, 90), 23),
    (4, -90, 3, 0, Pose(-90, 180), 24),
    (5, -90, 4, 0, Pose(-90, 270), 25),
    (6, -90, 5, 1, Pose(-90, 0), 26),
    (7, 200, 1, 0, Pose(0, 0), 27),
    (8, 200, 2, 0, Pose(0, 90), 28),
    (9, 200, 3, 0, Pose(0, 180), 29),
    (10, 200, 4, 0, Pose(0, 270), 30),
    (11, 200, 5, 1, Pose(0, 0), 31),
)
RECOVERY_EXPECTED = tuple(
    campaign.ExpectedRow(
        seq,
        block,
        anchor_seq,
        is_closure,
        reach.Pose(seq, pose.b_deg, pose.c_deg, "t3_attempt2_recovery"),
    )
    for seq, block, anchor_seq, is_closure, pose, _ in RECOVERY_ROWS
)
RECOVERY_SPEC = campaign.RunSpec(
    "T3 length-aware Attempt-2 recovery",
    TOOL,
    MODE,
    TOOL_LENGTH_MM,
    PROBE_OFFSET_MM,
    EFFECTIVE_RADIUS_MM,
    FILES["results"],
    FILES["state"],
    FILES["closures"],
    RECOVERY_EXPECTED,
    (),
)
POSE_BY_SEQ = {row[0]: row[4] for row in RECOVERY_ROWS}
RECOVERY_CLOSURES = (
    (3416, 16, 1, (1024.840507, 843.991200, -403.293929)),
    (3422, 22, 2, (1025.069611, 844.044347, -403.151636)),
    (-90, 2, 6, None),
    (3401, 1, 7, None),
    (200, 7, 11, None),
    (3402, 1, 11, None),
)
CANONICAL_CLOSURES = (
    (100, 1, 5),
    (45, 6, 10),
    (-45, 11, 15),
    (905, 5, 16),
    (90, 17, 21),
    (-90, 22, 26),
    (911, 1, 27),
    (906, 16, 27),
    (912, 2, 28),
    (913, 3, 29),
    (914, 4, 30),
    (915, 5, 31),
    (200, 27, 31),
    (900, 1, 31),
)

CRITICAL_SUBROUTINES = (
    "tcpc_pair_coordinate_guard",
    "tcpc_pair_hold_position_guard",
    "tcpc_pair_selector_guard",
    "tcpc_length_model_guard",
    "tcpc_pair_live_guard",
    "tcpc_pair_release_guard",
    "tcpc_probe_counter_guard",
    "tcpc_contact_gap_log",
    "tcpc_contact_trace_begin",
    "tcpc_contact_trace_post",
    "tcpc_contact_trace_finish",
    "tcpc_pair_probe_final_guard",
    "tcpc_pair_probe_ready_guard",
    "tcpc_vector_sphere_pass4",
    "tcpc_measure_pose",
    "tcpc_primary_closure_guard",
    "tcpc_primary_outer_reference",
    "tcpc_primary_b0_sweep",
    "tcpc_primary_tilt_block",
    "tcpc_baseline_return_top_clear",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValidationError(f"hash mismatch for {path}: {actual} != {expected}")


def extract_subroutine(text: str, name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^o<{re.escape(name)}> sub\s*$.*?^o<{re.escape(name)}> endsub\s*$"
    )
    match = pattern.search(text)
    if not match:
        raise ValidationError(f"missing subroutine o<{name}>")
    return match.group(0)


def normalize_output_base(text: str) -> str:
    return text.replace(
        "tcpc-length-aware-t3-validation-2026082601-attempt2-recovery",
        "tcpc-length-aware-t3-validation-2026082601-attempt1",
    )


def top_level_lines(text: str) -> list[str]:
    lines: list[str] = []
    in_subroutine = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"o<[^>]+> sub", stripped):
            in_subroutine = True
            continue
        if re.fullmatch(r"o<[^>]+> endsub", stripped):
            in_subroutine = False
            continue
        if not in_subroutine:
            lines.append(stripped)
    return lines


def validate_static_source() -> None:
    require_hash(PROGRAM, PROGRAM_SHA256)
    require_hash(ATTEMPT1_PROGRAM, ATTEMPT1_PROGRAM_SHA256)
    for path, expected_hash in IMPORTED_VALIDATION_HASHES.items():
        require_hash(path, expected_hash)
    raw = PROGRAM.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError("recovery runner is not ASCII") from exc
    original = ATTEMPT1_PROGRAM.read_text(encoding="ascii")
    longest = max((len(line) for line in text.splitlines()), default=0)
    if longest > 225:
        raise ValidationError(f"runner line length {longest} exceeds sealed limit 225")

    for name in CRITICAL_SUBROUTINES:
        recovery_sub = normalize_output_base(extract_subroutine(text, name))
        original_sub = extract_subroutine(original, name)
        if recovery_sub != original_sub:
            raise ValidationError(f"sealed motion/safety subroutine changed: {name}")

    definitions = set(re.findall(r"(?m)^o<([^>]+)> sub\s*$", text))
    calls = set(re.findall(r"(?m)^\s*o<([^>]+)> call(?:\s|$)", text))
    missing = sorted(calls - definitions)
    if missing:
        raise ValidationError(f"unresolved subroutine calls: {missing}")
    if len(definitions) != len(re.findall(r"(?m)^o<([^>]+)> endsub\s*$", text)):
        raise ValidationError("subroutine definition/end count differs")

    top = top_level_lines(text)
    if sum(line == "M0" for line in top) != 1 or any(line == "M1" for line in top):
        raise ValidationError("runner must have exactly one top-level M0 and no M1")
    m0_index = top.index("M0")
    if any(re.search(r"\b(?:G0|G1|G2|G3|G38\.)\b.*\b[XYZBC]", line) for line in top[:m0_index]):
        raise ValidationError("top-level axis motion exists before initial M0")
    if text.count("G38.3") != 4:
        raise ValidationError("four-contact acquisition must contain four G38.3 sites")
    if "attempt1-" in text:
        raise ValidationError("recovery runner references an Attempt-1 output")

    required = (
        "#707 = 11.0",
        "#711 = 34.0",
        "#715 = 2026082602.0",
        "#716 = 1.0",
        "#727 = 2.0",
        "#739 = 1.0",
        "#3032 = #717",
        "o<closure_sequence_complete> if [ABS[#978 - 6.0] GT 0.000001]",
        "o<trace_exact_count> if [ABS[#973 - 88.0] GT 0.000001]",
        "o<tcpc_probe_counter_guard> call",
        "#950 = #<_hal[counter.0.counts]>",
        "(DEBUG, TCPC_LENGTH_AWARE_T3_RECOVERY_2026082601 complete)",
    )
    for snippet in required:
        if snippet not in text:
            raise ValidationError(f"required recovery contract missing: {snippet}")

    body_match = re.search(
        r"(?ms)^o<run_relocated_t3_recovery> if .*?^o<run_relocated_t3_recovery> endif$",
        text,
    )
    if not body_match:
        raise ValidationError("recovery body is missing")
    calls_found = [
        (float(b), float(c))
        for b, c in re.findall(
            r"o<tcpc_measure_pose> call \[([-+0-9.]+)\] \[([-+0-9.]+)\] \[0\.0\] \[0\.0\]",
            body_match.group(0),
        )
    ]
    expected_calls = [(row[4].b_deg, row[4].c_deg) for row in RECOVERY_ROWS]
    if calls_found != expected_calls:
        raise ValidationError(f"recovery pose order changed: {calls_found}")
    closure_snippets = (
        "[3416.0] [16.0] [#726]",
        "[3422.0] [22.0] [#726]",
        "[-90.0] [2.0] [#726]",
        "[3401.0] [1.0] [#726]",
        "[200.0] [7.0] [#726]",
        "[3402.0] [1.0] [#726]",
    )
    closure_calls = [
        line for line in body_match.group(0).splitlines()
        if "o<tcpc_primary_closure_guard> call" in line
    ]
    if len(closure_calls) != EXPECTED_CLOSURES:
        raise ValidationError("recovery body does not contain exactly six closures")
    for line, suffix in zip(closure_calls, closure_snippets):
        if suffix not in line:
            raise ValidationError(f"recovery closure topology changed: {line.strip()}")

    for suffix in SUFFIXES:
        expected_path = str(FILES[suffix])
        if text.count(expected_path) != 2:
            raise ValidationError(f"runner must reference dedicated {suffix} path twice")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValidationError(f"missing CSV header: {path}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValidationError(f"malformed CSV row: {path}")
    return rows


def validate_headers() -> None:
    for suffix in SUFFIXES:
        recovery_header = FILES[suffix].read_text(encoding="ascii").splitlines()[0]
        attempt1_header = ATTEMPT1_FILES[suffix].read_text(encoding="ascii").splitlines()[0]
        if recovery_header != attempt1_header:
            raise ValidationError(f"{suffix} header differs from frozen Attempt 1 schema")


def exact_number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise ValidationError(f"invalid number in {field}") from exc
    if not math.isfinite(value):
        raise ValidationError(f"nonfinite number in {field}")
    return value


def exact_int(row: dict[str, str], field: str) -> int:
    value = exact_number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-6:
        raise ValidationError(f"{field}={value} is not integral")
    return int(rounded)


def angular_error(actual: float, expected: float) -> float:
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def require_identity(
    row: dict[str, str], sequence_field: str, *, mode: int = MODE, attempt: int = ATTEMPT
) -> int:
    for field, expected in (
        ("schema_version", 1),
        ("campaign_id", CAMPAIGN),
        ("stage_mode", mode),
        ("attempt_id", attempt),
    ):
        if exact_int(row, field) != expected:
            raise ValidationError(f"{field} identity mismatch")
    return exact_int(row, sequence_field)


def validate_attempt1_partial() -> None:
    for suffix, expected_hash in ATTEMPT1_PARTIAL_HASHES.items():
        require_hash(ATTEMPT1_FILES[suffix], expected_hash)
    results = read_rows(ATTEMPT1_FILES["results"])
    states = read_rows(ATTEMPT1_FILES["state"])
    models = read_rows(ATTEMPT1_FILES["model-state"])
    closures = read_rows(ATTEMPT1_FILES["closures"])
    contacts = read_rows(ATTEMPT1_FILES["contact-trace"])
    gaps = read_rows(ATTEMPT1_FILES["gap-trace"])
    if (len(results), len(states), len(models), len(closures), len(contacts), len(gaps)) != (
        22, 22, 22, 5, 184, 184
    ):
        raise ValidationError("Attempt 1 no longer matches sealed 22-row/row-23-trace partial state")
    for rows, field in ((results, "sample_seq"), (states, "sample_seq"), (models, "sample_seq")):
        seqs = [require_identity(row, field, mode=33, attempt=1) for row in rows]
        if seqs != list(range(1, 23)):
            raise ValidationError("Attempt 1 accepted summary sequence is not exactly 1..22")
    expected_keys = [
        (seq, pass_id, contact_id)
        for seq in range(1, 24)
        for pass_id in (1, 2)
        for contact_id in (1, 2, 3, 4)
    ]
    contact_keys = [
        (
            require_identity(row, "global_seq", mode=33, attempt=1),
            exact_int(row, "pass_id"),
            exact_int(row, "contact_id"),
        )
        for row in contacts
    ]
    gap_keys = [
        (
            require_identity(row, "next_global_seq", mode=33, attempt=1),
            exact_int(row, "pass_id"),
            exact_int(row, "contact_id"),
        )
        for row in gaps
    ]
    if contact_keys != expected_keys or gap_keys != expected_keys:
        raise ValidationError("Attempt 1 trace boundary is not exact seq1..23/pass1..2/contact1..4")
    if angular_error(exact_number(results[-1], "abs_b_deg"), -90.0) > 0.01:
        raise ValidationError("Attempt 1 accepted row22 is not the B-90/C0 bridge")
    if angular_error(exact_number(results[-1], "abs_c_deg"), 0.0) > 0.01:
        raise ValidationError("Attempt 1 accepted row22 is not the B-90/C0 bridge")
    partial_spec = campaign.RunSpec(
        "T3 length-aware Attempt-1 accepted partial",
        frozen.TOOL,
        frozen.MODE,
        frozen.TOOL_LENGTH_MM,
        frozen.PROBE_OFFSET_MM,
        frozen.SPEC.effective_radius,
        ATTEMPT1_FILES["results"],
        ATTEMPT1_FILES["state"],
        ATTEMPT1_FILES["closures"],
        frozen.EXPECTED[:22],
        campaign.T3_CLOSURES[:5],
    )
    try:
        with frozen.validation_campaign_context():
            for result, state, model, expected in zip(
                results, states, models, frozen.EXPECTED[:22]
            ):
                campaign.validate_result(partial_spec, result, expected, 1)
                campaign.validate_state(partial_spec, state, result, expected, 1)
                frozen.validate_model_row(model, expected)
            campaign.validate_closures(
                partial_spec,
                closures,
                {seq: row for seq, row in enumerate(results, 1)},
                1,
            )
        previous: dict[str, str] | None = None
        for index, (contact, gap) in enumerate(zip(contacts[:176], gaps[:176])):
            key = frozen.trace_key(contact, "global_seq")
            frozen.validate_contact_trace_row(contact, key)
            frozen.validate_gap_trace_row(gap, contact, previous, index, key)
            previous = contact
    except (anchor.ValidationError, frozen.ValidationError) as exc:
        raise ValidationError(f"Attempt 1 sealed partial semantic check failed: {exc}") from exc


def validate_fresh_outputs() -> None:
    validate_headers()
    for suffix, path in FILES.items():
        if len(path.read_text(encoding="ascii").splitlines()) != 1:
            raise ValidationError(f"recovery {suffix} output is not fresh/header-only")


def validate_preflight() -> None:
    validate_static_source()
    validate_attempt1_partial()
    validate_fresh_outputs()


def validate_result_rows() -> tuple[list[dict[str, str]], dict[int, np.ndarray]]:
    results = read_rows(FILES["results"])
    states = read_rows(FILES["state"])
    models = read_rows(FILES["model-state"])
    if len(results) != EXPECTED_ROWS or len(states) != EXPECTED_ROWS or len(models) != EXPECTED_ROWS:
        raise ValidationError("recovery summary files are not exact 11/11/11 rows")
    try:
        with frozen.validation_campaign_context():
            for result, state, expected in zip(results, states, RECOVERY_EXPECTED):
                campaign.validate_result(RECOVERY_SPEC, result, expected, ATTEMPT)
                campaign.validate_state(RECOVERY_SPEC, state, result, expected, ATTEMPT)
    except anchor.ValidationError as exc:
        raise ValidationError(f"recovery strict result/state validation failed: {exc}") from exc
    centers: dict[int, np.ndarray] = {}
    for expected, result, state, model in zip(RECOVERY_ROWS, results, states, models):
        seq, block, anchor, is_closure, pose, _ = expected
        for row in (result, state, model):
            if require_identity(row, "sample_seq") != seq:
                raise ValidationError(f"recovery summary row {seq} is out of order")
        for field, value in (
            ("block_id", block),
            ("anchor_seq", anchor),
            ("is_closure", is_closure),
            ("contact_count", 4),
            ("live_tool_number", TOOL),
        ):
            if exact_int(result, field) != value:
                raise ValidationError(f"result seq {seq}: {field} mismatch")
        for row in (result, state):
            if angular_error(exact_number(row, "abs_b_deg"), pose.b_deg) > 0.01:
                raise ValidationError(f"summary seq {seq}: B pose mismatch")
            if angular_error(exact_number(row, "abs_c_deg"), pose.c_deg) > 0.01:
                raise ValidationError(f"summary seq {seq}: C pose mismatch")
        for field, expected_value, tolerance in (
            ("expected_tool_length_mm", TOOL_LENGTH_MM, 0.002),
            ("probe_calibration_offset_mm", PROBE_OFFSET_MM, 0.0005),
            ("effective_contact_radius_mm", EFFECTIVE_RADIUS_MM, 0.0005),
        ):
            if abs(exact_number(result, field) - expected_value) > tolerance:
                raise ValidationError(f"result seq {seq}: {field} mismatch")
        if exact_int(result, "u_method_code") not in (1, 2):
            raise ValidationError(f"result seq {seq}: invalid U method")
        if not 29.9 <= exact_number(result, "v_corrected_diameter_mm") <= 30.5:
            raise ValidationError(f"result seq {seq}: V diameter outside accepted range")
        if exact_number(result, "pass_center_delta_mm") > 0.10:
            raise ValidationError(f"result seq {seq}: pass-center disagreement")
        for field in (
            "center_correction_norm_mm",
            "w_contact_radial_residual_mm",
            "u_contact_radial_residual_mm",
            "v_minus_contact_radial_residual_mm",
            "v_plus_contact_radial_residual_mm",
        ):
            if exact_number(result, field) > 0.25:
                raise ValidationError(f"result seq {seq}: {field} exceeds 0.25 mm")
        for field, upper in (
            ("w_travel_mm", 7.01),
            ("u_travel_mm", 6.01),
            ("v_minus_travel_mm", 6.01),
            ("v_plus_travel_mm", 6.01),
        ):
            if not 1.0 <= exact_number(result, field) <= upper:
                raise ValidationError(f"result seq {seq}: {field} outside motion contract")

        for field, expected_value in (
            ("persistent_correction_enabled", 1),
            ("tcpc_enabled", 1),
            ("twp_active", 0),
            ("twp_motion_enabled", 0),
            ("twp_valid", 0),
            ("b_ssi_invalid", 0),
            ("c_ssi_invalid", 0),
        ):
            if exact_int(state, field) != expected_value:
                raise ValidationError(f"state seq {seq}: {field} mismatch")
        for field in (
            "motion_tooloffset_z_mm",
            "halui_tool_length_offset_z_mm",
            "kins_active_tool_offset_z_mm",
        ):
            if abs(exact_number(state, field) - TOOL_LENGTH_MM) > 0.002:
                raise ValidationError(f"state seq {seq}: {field} mismatch")
        for field, expected_value in (
            ("model_id", MODEL_ID),
            ("expected_model_id", MODEL_ID),
            ("configured", 1),
            ("valid", 1),
            ("fault_code", 0),
            ("q", 1),
        ):
            if exact_int(model, field) != expected_value:
                raise ValidationError(f"model seq {seq}: {field} mismatch")
        if angular_error(exact_number(model, "evaluated_b_deg"), pose.b_deg) > 0.01:
            raise ValidationError(f"model seq {seq}: evaluated B mismatch")
        if angular_error(exact_number(model, "evaluated_c_deg"), pose.c_deg) > 0.01:
            raise ValidationError(f"model seq {seq}: evaluated C mismatch")
        if abs(exact_number(model, "evaluated_length_mm") - TOOL_LENGTH_MM) > 0.002:
            raise ValidationError(f"model seq {seq}: evaluated length mismatch")
        diff = np.asarray(
            [exact_number(model, f"diff_offset_{axis}_mm") for axis in "xyz"],
            dtype=float,
        )
        diff_norm = exact_number(model, "diff_offset_norm_mm")
        expected_diff = frozen.expected_diff_vector(pose.b_deg, pose.c_deg)
        if (
            diff_norm < 0.0
            or diff_norm > frozen.DIFF_CAP_MM
            or abs(diff_norm - float(np.linalg.norm(diff))) > 3e-6
            or float(np.linalg.norm(diff - expected_diff)) > 2e-5
        ):
            raise ValidationError(f"model seq {seq}: sealed q=1 differential vector mismatch")
        empirical = np.asarray(
            [exact_number(model, f"empirical_offset_{axis}_mm") for axis in "xyz"],
            dtype=float,
        )
        empirical_norm = exact_number(model, "empirical_offset_norm_mm")
        expected_empirical = frozen.expected_empirical_vector(pose.b_deg, pose.c_deg)
        if (
            empirical_norm < 0.0
            or empirical_norm > frozen.TOTAL_CAP_MM
            or abs(empirical_norm - float(np.linalg.norm(empirical))) > 5e-6
            or float(np.linalg.norm(empirical - expected_empirical)) > 2e-5
        ):
            raise ValidationError(f"model seq {seq}: sealed q=1 empirical vector mismatch")
        centers[seq] = np.asarray(
            [exact_number(result, f"center_abs_{axis}_mm") for axis in "xyz"],
            dtype=float,
        )
    return results, centers


def counter_tuple(row: dict[str, str], prefix: str) -> tuple[int, int, int]:
    return tuple(exact_int(row, f"{prefix}_{kind}_count") for kind in ("raw", "mux", "gated"))


def expected_transaction_keys() -> list[tuple[int, int, int, int]]:
    return [
        (seq, 1, pass_id, contact_id)
        for seq in range(1, EXPECTED_ROWS + 1)
        for pass_id in (1, 2)
        for contact_id in (1, 2, 3, 4)
    ]


def trace_key(row: dict[str, str], sequence_field: str) -> tuple[int, int, int, int]:
    return (
        require_identity(row, sequence_field),
        exact_int(row, "acquisition_try"),
        exact_int(row, "pass_id"),
        exact_int(row, "contact_id"),
    )


def validate_trace_pose(row: dict[str, str], seq: int) -> None:
    pose = POSE_BY_SEQ[seq]
    if angular_error(exact_number(row, "abs_b_deg"), pose.b_deg) > 0.01:
        raise ValidationError(f"trace seq {seq}: B pose mismatch")
    if angular_error(exact_number(row, "abs_c_deg"), pose.c_deg) > 0.01:
        raise ValidationError(f"trace seq {seq}: C pose mismatch")


def validate_traces() -> dict[str, int]:
    contacts = read_rows(FILES["contact-trace"])
    gaps = read_rows(FILES["gap-trace"])
    keys = expected_transaction_keys()
    if len(contacts) != EXPECTED_TRANSACTIONS or len(gaps) != EXPECTED_TRANSACTIONS:
        raise ValidationError("recovery trace files are not exact 88/88 rows")
    if [trace_key(row, "global_seq") for row in contacts] != keys:
        raise ValidationError("contact traces are not exact try1/pass1-2/contact1-4 order")
    if [trace_key(row, "next_global_seq") for row in gaps] != keys:
        raise ValidationError("gap traces are not exact try1/pass1-2/contact1-4 order")
    previous_contact: dict[str, str] | None = None
    filtered_extras = 0
    for index, (contact, gap, key) in enumerate(zip(contacts, gaps, keys)):
        seq, _, _, contact_id = key
        validate_trace_pose(contact, seq)
        validate_trace_pose(gap, seq)
        pre = counter_tuple(contact, "pre")
        post = counter_tuple(contact, "post")
        ready = counter_tuple(contact, "ready")
        direct = tuple(post[i] - pre[i] for i in range(3))
        repeats = tuple(ready[i] - post[i] for i in range(3))
        total = tuple(ready[i] - pre[i] for i in range(3))
        if any(value < 0 for value in pre + post + ready):
            raise ValidationError(f"contact trace seq {seq}: negative counter")
        if any(not (pre[i] <= post[i] <= ready[i]) for i in range(3)):
            raise ValidationError(f"contact trace seq {seq}: non-monotonic counter")
        if direct[0] != direct[1] or direct[0] < 1 or direct[2] != 1:
            raise ValidationError(f"contact trace seq {seq}: gated contact mismatch")
        if repeats[0] != repeats[1] or repeats[2] != 0 or total[0] != total[1]:
            raise ValidationError(f"contact trace seq {seq}: repeat-edge mismatch")
        for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
            if exact_int(contact, field) != value:
                raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
        for field, value in zip(
            ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats
        ):
            if exact_int(contact, field) != value:
                raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
        extra = total[0] - total[2]
        if exact_int(contact, "extra_raw_minus_gated_delta") != extra or not 0 <= extra <= MAX_FILTERED_EXTRA_EDGES:
            raise ValidationError(f"contact trace seq {seq}: filtered extras outside contract")
        filtered_extras += extra
        for field in ("burst_flag", "consistency_fault", "release_fault", "terminal_failure"):
            if exact_int(contact, field) != 0:
                raise ValidationError(f"contact trace seq {seq}: {field} is nonzero")
        if exact_int(contact, "probe_result") != 1:
            raise ValidationError(f"contact trace seq {seq}: probe result is not success")
        upper = 7.01 if contact_id == 1 else 6.01
        if not 1.0 <= exact_number(contact, "travel_mm") <= upper:
            raise ValidationError(f"contact trace seq {seq}: travel outside contract")

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
            raise ValidationError("only first recovery gap may be initial baseline")
        if initial == 1 and any(delta):
            raise ValidationError("initial recovery gap baseline contains electrical activity")
        prior_extra = exact_int(gap, "prior_contact_extra_delta")
        if previous_contact is None:
            if prior_extra != 0:
                raise ValidationError("initial gap has prior-contact extras")
        else:
            if prior != counter_tuple(previous_contact, "ready"):
                raise ValidationError(f"gap trace seq {seq}: prior boundary changed")
            if prior_extra != exact_int(previous_contact, "extra_raw_minus_gated_delta"):
                raise ValidationError(f"gap trace seq {seq}: prior extras changed")
        if current != pre:
            raise ValidationError(f"gap trace seq {seq}: contact boundary changed")
        combined = prior_extra + delta[0] - delta[2]
        if exact_int(gap, "combined_extra_delta") != combined:
            raise ValidationError(f"gap trace seq {seq}: combined extras mismatch")
        if delta[0] != delta[1] or delta[2] != 0 or not 0 <= combined <= MAX_FILTERED_EXTRA_EDGES:
            raise ValidationError(f"gap trace seq {seq}: electrical gate failure")
        for field in ("burst_flag", "consistency_fault"):
            if exact_int(gap, field) != 0:
                raise ValidationError(f"gap trace seq {seq}: {field} is nonzero")
        previous_contact = contact
    return {"filtered_extra_edges": filtered_extras}


def validate_recovery_closures(centers: dict[int, np.ndarray]) -> None:
    rows = read_rows(FILES["closures"])
    if len(rows) != EXPECTED_CLOSURES:
        raise ValidationError("recovery closure file does not contain exactly six rows")
    for row, expected in zip(rows, RECOVERY_CLOSURES):
        block, open_seq, close_seq, sealed_open = expected
        require_identity(row, "close_sample_seq")
        if (
            exact_int(row, "block_id"),
            exact_int(row, "open_sample_seq"),
            exact_int(row, "close_sample_seq"),
        ) != expected[:3]:
            raise ValidationError(f"recovery closure topology mismatch: expected {expected[:3]}")
        open_center = (
            np.asarray(sealed_open, dtype=float)
            if sealed_open is not None
            else centers[open_seq]
        )
        delta = centers[close_seq] - open_center
        logged = np.asarray([exact_number(row, f"closure_d{axis}_mm") for axis in "xyz"])
        norm = float(np.linalg.norm(delta))
        if float(np.linalg.norm(delta - logged)) > 3e-6:
            raise ValidationError(f"recovery closure {block}: vector mismatch")
        if abs(exact_number(row, "closure_norm_mm") - norm) > 3e-6:
            raise ValidationError(f"recovery closure {block}: norm mismatch")
        if abs(exact_number(row, "limit_mm") - BRIDGE_LIMIT_MM) > 1e-9:
            raise ValidationError(f"recovery closure {block}: logged limit changed")
        if norm > BRIDGE_LIMIT_MM or exact_int(row, "pass") != 1:
            raise ValidationError(f"recovery closure {block}: exceeds 0.050 mm")


def canonical_poses() -> tuple[Pose, ...]:
    poses: list[Pose] = []
    for c_deg in (0, 90, 180, 270, 0):
        poses.append(Pose(0, c_deg))
    for b_deg in (45, -45):
        for c_deg in (0, 90, 180, 270, 0):
            poses.append(Pose(b_deg, c_deg))
    poses.append(Pose(0, 0))
    for b_deg in (90, -90):
        for c_deg in (0, 90, 180, 270, 0):
            poses.append(Pose(b_deg, c_deg))
    for c_deg in (0, 90, 180, 270, 0):
        poses.append(Pose(0, c_deg))
    if len(poses) != 31:
        raise AssertionError("canonical T3 pose construction failed")
    return tuple(poses)


def centered_metric(values: np.ndarray) -> tuple[float, float]:
    residuals = values - np.mean(values, axis=0)
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms * norms))), float(np.max(norms))


def require_bridges(b0_bridge: float, bm90_bridge: float) -> None:
    if b0_bridge > BRIDGE_LIMIT_MM or bm90_bridge > BRIDGE_LIMIT_MM:
        raise ValidationError(
            f"cross-attempt bridge exceeds 0.050 mm: B0={b0_bridge:.6f}, "
            f"B-90={bm90_bridge:.6f}"
        )


def compose_centers(
    attempt1_centers: dict[int, np.ndarray],
    recovery_centers: dict[int, np.ndarray],
) -> dict[int, np.ndarray]:
    if not all(seq in attempt1_centers for seq in range(1, 23)):
        raise ValidationError("Attempt 1 centers do not cover exact accepted rows 1..22")
    if not all(seq in recovery_centers for seq in range(1, 12)):
        raise ValidationError("recovery centers do not cover exact rows 1..11")
    composite = {seq: attempt1_centers[seq] for seq in range(1, 23)}
    for recovery_seq in range(3, 12):
        canonical_seq = RECOVERY_ROWS[recovery_seq - 1][5]
        if canonical_seq is None:
            raise ValidationError(f"recovery row {recovery_seq} lacks canonical mapping")
        composite[canonical_seq] = recovery_centers[recovery_seq]
    if sorted(composite) != list(range(1, 32)):
        raise ValidationError("composite does not cover exact canonical rows 1..31")
    return composite


def validate_composite(recovery_centers: dict[int, np.ndarray]) -> dict[str, float]:
    attempt1 = read_rows(ATTEMPT1_FILES["results"])
    attempt1_centers = {
        exact_int(row, "sample_seq"): np.asarray(
            [exact_number(row, f"center_abs_{axis}_mm") for axis in "xyz"], dtype=float
        )
        for row in attempt1
    }
    b0_reference = attempt1_centers[16]
    b0_bridge = float(np.linalg.norm(recovery_centers[1] - b0_reference))
    bm90_bridge = float(np.linalg.norm(recovery_centers[2] - attempt1_centers[22]))
    require_bridges(b0_bridge, bm90_bridge)

    composite = compose_centers(attempt1_centers, recovery_centers)

    canonical = canonical_poses()
    for seq, pose in enumerate(canonical, 1):
        if seq <= 22:
            source = attempt1[seq - 1]
        else:
            recovery_seq = seq - 20
            source = read_rows(FILES["results"])[recovery_seq - 1]
        if angular_error(exact_number(source, "abs_b_deg"), pose.b_deg) > 0.01:
            raise ValidationError(f"composite seq {seq}: B pose mismatch")
        if angular_error(exact_number(source, "abs_c_deg"), pose.c_deg) > 0.01:
            raise ValidationError(f"composite seq {seq}: C pose mismatch")

    canonical_closure_max = 0.0
    for block, open_seq, close_seq in CANONICAL_CLOSURES:
        norm = float(np.linalg.norm(composite[close_seq] - composite[open_seq]))
        canonical_closure_max = max(canonical_closure_max, norm)
        if norm > BRIDGE_LIMIT_MM:
            raise ValidationError(
                f"composite canonical closure {block} {open_seq}->{close_seq} "
                f"is {norm:.6f} mm, above 0.050 mm"
            )

    try:
        frozen_metrics = frozen.center_metrics(composite)
    except frozen.ValidationError as exc:
        raise ValidationError(f"composite frozen q=1 metric gate failed: {exc}") from exc
    return {
        "b0_bridge_mm": b0_bridge,
        "bm90_bridge_mm": bm90_bridge,
        "canonical_closure_max_mm": canonical_closure_max,
        "raw_rms_mm": frozen_metrics["raw_rms"],
        "raw_max_mm": frozen_metrics["raw_max"],
        "unique_rms_mm": frozen_metrics["unique_rms"],
        "unique_max_mm": frozen_metrics["unique_max"],
        "raw_h0_rms_mm": frozen_metrics["raw_h0_rms"],
        "raw_h0_max_mm": frozen_metrics["raw_h0_max"],
        "unique_h0_rms_mm": frozen_metrics["unique_h0_rms"],
        "unique_h0_max_mm": frozen_metrics["unique_h0_max"],
        "positive_b_rms_mm": frozen_metrics["positive_b_rms"],
        "positive_b_h0_rms_mm": frozen_metrics["positive_b_h0_rms"],
        "negative_b_rms_mm": frozen_metrics["negative_b_rms"],
        "negative_b_h0_rms_mm": frozen_metrics["negative_b_h0_rms"],
        "b0_rms_mm": frozen_metrics["b0_rms"],
        "b0_h0_rms_mm": frozen_metrics["b0_h0_rms"],
        "maximum_pose_worsening_mm": frozen_metrics["maximum_pose_worsening"],
    }


def validate_complete() -> dict[str, float | int]:
    validate_static_source()
    validate_headers()
    validate_attempt1_partial()
    _, centers = validate_result_rows()
    diagnostics = validate_traces()
    validate_recovery_closures(centers)
    return {**validate_composite(centers), **diagnostics}


def expect_validation_failure(label: str, function) -> None:
    try:
        function()
    except ValidationError:
        return
    raise AssertionError(f"self-test mutation was accepted: {label}")


def self_test() -> None:
    validate_static_source()
    validate_attempt1_partial()
    require_bridges(BRIDGE_LIMIT_MM, BRIDGE_LIMIT_MM)
    expect_validation_failure(
        "B0 bridge ceiling",
        lambda: require_bridges(BRIDGE_LIMIT_MM + 1e-8, 0.0),
    )
    expect_validation_failure(
        "B-90 bridge ceiling",
        lambda: require_bridges(0.0, BRIDGE_LIMIT_MM + 1e-8),
    )

    attempt1_centers = {
        seq: np.asarray([float(seq), 0.0, 0.0]) for seq in range(1, 23)
    }
    recovery_centers = {
        seq: np.asarray([100.0 + seq, 0.0, 0.0]) for seq in range(1, 12)
    }
    composite = compose_centers(attempt1_centers, recovery_centers)
    if not np.array_equal(composite[22], attempt1_centers[22]):
        raise AssertionError("composite replaced accepted Attempt-1 row22")
    if not np.array_equal(composite[23], recovery_centers[3]):
        raise AssertionError("composite did not map recovery row3 to canonical row23")
    if not np.array_equal(composite[31], recovery_centers[11]):
        raise AssertionError("composite did not map recovery row11 to canonical row31")
    missing_attempt1 = dict(attempt1_centers)
    del missing_attempt1[22]
    expect_validation_failure(
        "missing Attempt-1 row22",
        lambda: compose_centers(missing_attempt1, recovery_centers),
    )
    missing_recovery = dict(recovery_centers)
    del missing_recovery[3]
    expect_validation_failure(
        "missing recovery row3",
        lambda: compose_centers(attempt1_centers, missing_recovery),
    )

    # Reuse the frozen validator's exhaustive metric branch mutations and its
    # independent historical H0 reconstruction-sign fixture.
    frozen.metric_gate_self_test()
    frozen.historical_metric_formula_self_test()

    mutated = dict(read_rows(ATTEMPT1_FILES["results"])[0])
    mutated["contact_count"] = "3"
    try:
        with frozen.validation_campaign_context():
            campaign.validate_result(frozen.SPEC, mutated, frozen.EXPECTED[0], 1)
    except anchor.ValidationError:
        pass
    else:
        raise AssertionError("Attempt-1 semantic mutation was accepted")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--static", action="store_true", help="read-only source audit")
    mode.add_argument("--preflight", action="store_true", help="static audit plus fresh-file gates")
    mode.add_argument("--validate", action="store_true", help="validate completed recovery and composite")
    mode.add_argument("--self-test", action="store_true", help="run static and mutation tests")
    args = parser.parse_args(argv)
    try:
        if args.static:
            validate_static_source()
            label = "STATIC PASS"
            metrics: dict[str, float | int] = {}
        elif args.preflight:
            validate_preflight()
            label = "PREFLIGHT PASS"
            metrics = {}
        elif args.validate:
            metrics = validate_complete()
            label = "COMPOSITE ENGINEERING PASS; NOT FORMAL T3 RELEASE"
        else:
            self_test()
            metrics = {}
            label = "SELF-TEST PASS"
    except (OSError, ValidationError, AssertionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"T3 attempt-2 recovery {label}")
    print(f"runner_sha256={PROGRAM_SHA256}")
    print("identity=campaign2026082602/mode34/attempt2 rows=11 closures=6 traces=88")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"{key}={value:.6f}")
        else:
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
