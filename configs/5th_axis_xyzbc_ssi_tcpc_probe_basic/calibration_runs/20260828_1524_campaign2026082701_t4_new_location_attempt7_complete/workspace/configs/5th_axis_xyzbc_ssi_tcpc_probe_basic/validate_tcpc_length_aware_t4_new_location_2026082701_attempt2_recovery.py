#!/usr/bin/env python3
"""Read-only preflight and offline validation for the T4 location recovery.

This module reads ordinary files only.  It does not import LinuxCNC or HAL,
does not launch rs274, and does not create a subprocess, so every mode is safe
while the controller is running.
"""

from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import csv
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
import sys
from typing import Callable, Sequence

import numpy as np

import analyze_tcpc_length_aware_t4_new_location_2026082701 as full
import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import analyze_tcpc_relocated_sphere_reachability as reach
import assess_tcpc_length_aware_bounds as bounds


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CAMPAIGN = 2026082701
MODE = 36
ATTEMPT = 2
ATTEMPT1_MODE = 35
ATTEMPT1_ATTEMPT = 1
MODEL_ID = 2026082601
TOOL = 4
TOOL_LENGTH_MM = 229.407000
PROBE_OFFSET_MM = 0.154742
EFFECTIVE_RADIUS_MM = 17.845258
DIFF_CAP_MM = 0.400000
TOTAL_CAP_MM = 1.350000
CLOSURE_LIMIT_MM = 0.050
RMS_LIMIT_MM = 0.120
MAX_LIMIT_MM = 0.280
MAX_RECOVERY_EXTRA_EDGES = 8
MAX_ATTEMPT1_EXTRA_EDGES = 2

EXPECTED_CANONICAL_ROWS = 101
EXPECTED_UNIQUE_POSES = 76
EXPECTED_RECOVERY_ROWS = 94
EXPECTED_RECOVERY_CLOSURES = 29
EXPECTED_RECOVERY_TRANSACTIONS = 752
ATTEMPT1_ACCEPTED_ROWS = 17
ATTEMPT1_ACCEPTED_TRANSACTIONS = 136

PROGRAM = (
    REPO_ROOT
    / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.ngc"
)
ATTEMPT1_PROGRAM = (
    REPO_ROOT
    / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt1.ngc"
)
RECOVERY_BASE = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt2-recovery"
ATTEMPT1_BASE = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt1"

SUFFIXES = (
    "results", "state", "model-state", "closures", "contact-trace", "gap-trace"
)
RECOVERY_FILES = {
    suffix: Path(f"{RECOVERY_BASE}-{suffix}.csv") for suffix in SUFFIXES
}
ATTEMPT1_FILES = {
    suffix: Path(f"{ATTEMPT1_BASE}-{suffix}.csv") for suffix in SUFFIXES
}

MODEL_STATE_FIELDS = (
    "schema_version", "campaign_id", "stage_mode", "attempt_id",
    "sample_seq", "model_id", "expected_model_id", "configured", "valid",
    "fault_code", "q", "evaluated_b_deg", "evaluated_c_deg",
    "evaluated_length_mm", "diff_offset_x_mm", "diff_offset_y_mm",
    "diff_offset_z_mm", "diff_offset_norm_mm", "empirical_offset_x_mm",
    "empirical_offset_y_mm", "empirical_offset_z_mm", "empirical_offset_norm_mm",
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
FIELDS = {
    "results": anchor.RESULT_FIELDS,
    "state": anchor.STATE_FIELDS,
    "model-state": MODEL_STATE_FIELDS,
    "closures": campaign.CLOSURE_FIELDS,
    "contact-trace": CONTACT_TRACE_FIELDS,
    "gap-trace": GAP_TRACE_FIELDS,
}

PROGRAM_SHA256 = "c027a0bab19f403e5e625f01fb50d6d050b51188fa0a0885dbaa795035b5c758"
ATTEMPT1_PROGRAM_SHA256 = "54bd1e3b5cfc95f44ddbf344693652b68dec920f74649e466d939860fe4a9174"
ATTEMPT1_PARTIAL_HASHES = {
    "results": "94c19d4552c75112ada77a30930580a7f8503ca23941f5b62d5e8e4daebe9c92",
    "state": "f1f35bb6f9368170fa1c6797a30757c71b61072626f3204973fbe8c9d0823e32",
    "model-state": "e933c2323463dfb214007a61094feb09769da9ad73e0db821db33d3fc031dae3",
    "closures": "6f72fd83b0689883b53f7810d19735e6c487d41f6d7c75a46e402408f6dfdf96",
    "contact-trace": "22e8239b8914b64ec0735a66c04b44942b1acdfadf33ea9a6f0eaeadac72839e",
    "gap-trace": "6ff1cd9053e4db1cba8172d93a2c2a749868608c12c867e4c037421b8353d09a",
}
SEALED_READERS = {
    HERE / "analyze_tcpc_relocated_sphere_anchor.py":
        "30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d",
    HERE / "analyze_tcpc_relocated_sphere_campaign.py":
        "d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a",
    HERE / "analyze_tcpc_relocated_sphere_reachability.py":
        "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    HERE / "assess_tcpc_length_aware_bounds.py":
        "b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2",
    HERE / "analyze_tcpc_length_aware_t4_new_location_2026082701.py":
        "e9c91215f7a83d747136f9cf08271f424f31e6b26723887718f8528af3cf5134",
}

CANONICAL_EXPECTED = campaign.expected_rows(tuple(reach.grid()), campaign.T4_RANGES)
EXPECTED_BY_SEQ = {row.seq: row for row in CANONICAL_EXPECTED}
RECOVERY_SEQS = tuple(range(1, 10)) + tuple(range(17, 102))
ATTEMPT1_SEQS = tuple(range(1, 18))
RECOVERY_EXPECTED = tuple(EXPECTED_BY_SEQ[seq] for seq in RECOVERY_SEQS)

ATTEMPT1_SPEC = campaign.RunSpec(
    "sealed T4 new-location Attempt 1 prefix", TOOL, ATTEMPT1_MODE,
    TOOL_LENGTH_MM, PROBE_OFFSET_MM, EFFECTIVE_RADIUS_MM,
    ATTEMPT1_FILES["results"], ATTEMPT1_FILES["state"],
    ATTEMPT1_FILES["closures"], CANONICAL_EXPECTED[:17],
    campaign.T4_CLOSURES[:2],
)
RECOVERY_SPEC = campaign.RunSpec(
    "T4 new-location Attempt 2 recovery", TOOL, MODE, TOOL_LENGTH_MM,
    PROBE_OFFSET_MM, EFFECTIVE_RADIUS_MM, RECOVERY_FILES["results"],
    RECOVERY_FILES["state"], RECOVERY_FILES["closures"], RECOVERY_EXPECTED, (),
)


class ValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Metrics:
    raw_rms: float
    raw_max: float
    unique_rms: float
    unique_max: float
    transfer_pass: bool
    worst_recovery_closure: float
    worst_canonical_closure: float
    bridge_row9: float
    bridge_row17: float
    filtered_extra_edges: int


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


def read_rows(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="ascii") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(fields):
                raise ValidationError(f"{path}: exact schema mismatch")
            rows = list(reader)
    except UnicodeError as exc:
        raise ValidationError(f"{path}: non-ASCII CSV") from exc
    if any(None in row or any(row.get(field) is None for field in fields) for row in rows):
        raise ValidationError(f"{path}: malformed, missing, or surplus CSV field")
    return rows


def number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise ValidationError(f"invalid numeric field {field}") from exc
    if not math.isfinite(value):
        raise ValidationError(f"nonfinite numeric field {field}")
    return value


def exact_int(row: dict[str, str], field: str, *, positive: bool = False) -> int:
    value = number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9 or (positive and rounded < 1):
        raise ValidationError(f"{field}={value:.9f} is not an exact integer")
    return int(rounded)


def angular_error(actual: float, expected: float) -> float:
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def require_identity(
    row: dict[str, str], sequence_field: str, *, mode: int, attempt: int
) -> int:
    for field, expected in (
        ("schema_version", 1), ("campaign_id", CAMPAIGN),
        ("stage_mode", mode), ("attempt_id", attempt),
    ):
        if exact_int(row, field, positive=field != "stage_mode") != expected:
            raise ValidationError(f"{field} does not match {CAMPAIGN}/{mode}/{attempt}")
    return exact_int(row, sequence_field, positive=True)


@contextmanager
def campaign_identity():
    previous = campaign.CAMPAIGN
    campaign.CAMPAIGN = CAMPAIGN
    try:
        yield
    finally:
        campaign.CAMPAIGN = previous


def extract_subroutine(text: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^o<{re.escape(name)}> sub\s*$.*?^o<{re.escape(name)}> endsub\s*$",
        text,
    )
    if not match:
        raise ValidationError(f"missing subroutine o<{name}>")
    return match.group(0)


def normalized_recovery_subroutine(text: str, name: str) -> str:
    text = text.replace(
        "tcpc-length-aware-t4-new-location-2026082701-attempt2-recovery",
        "tcpc-length-aware-t4-new-location-2026082701-attempt1",
    )
    if name == "tcpc_pair_selector_guard":
        text = re.sub(
            r"\n  o<pair_probe_edge_bound> if .*?\n"
            r"    \(abort, Recovery matched gate-closed edge allowance changed during the run\)\n"
            r"  o<pair_probe_edge_bound> endif",
            "", text, flags=re.DOTALL,
        )
    if name in ("tcpc_contact_trace_begin", "tcpc_contact_trace_finish"):
        text = text.replace("#779", "2.0")
    if name == "tcpc_primary_closure_guard":
        text = text.replace("\n  #978 = [#978 + 1.0]", "")
    return text


def top_level_lines(text: str) -> list[str]:
    output: list[str] = []
    in_subroutine = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"o<[^>]+> sub", stripped):
            in_subroutine = True
            continue
        if re.fullmatch(r"o<[^>]+> endsub", stripped):
            in_subroutine = False
            continue
        if not in_subroutine and stripped and not stripped.startswith("("):
            output.append(stripped)
    return output


def validate_python_safety(source: str) -> None:
    tree = ast.parse(source)
    forbidden = {"linuxcnc", "hal", "subprocess"}
    for node in ast.walk(tree):
        names: set[str] = set()
        if isinstance(node, ast.Import):
            names = {alias.name.split(".", 1)[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = {node.module.split(".", 1)[0]}
        if names & forbidden:
            raise ValidationError(f"validator imports forbidden module(s): {names & forbidden}")


def validate_no_direct_hal_writes(text: str) -> None:
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("("):
            continue
        if re.search(r"\b(?:halcmd|setp|sets|net|loadrt|loadusr|source)\b", line, re.I):
            raise ValidationError(f"runner contains direct HAL mutation: {line}")
        if re.match(r"^M(?:62|63|64)\b", line, re.I):
            raise ValidationError(f"runner contains forbidden output command: {line}")
        if re.match(r"^M65\b", line, re.I) and not re.fullmatch(
            r"M65\s+P[01](?:\.0*)?", line, re.I
        ):
            raise ValidationError(f"runner contains non-safety M65: {line}")


def validate_program_text(text: str, attempt1_text: str) -> None:
    if max((len(line) for line in text.splitlines()), default=0) > 225:
        raise ValidationError("runner exceeds the reviewed 225-character line limit")
    required_once = (
        "#707 = 94.0", "#711 = 36.0", "#715 = 2026082701.0",
        "#716 = 2.0", "#727 = 2.0", "#739 = 1.0", "#779 = 8.0",
        "#789 = #779", "#516 = 229.407000", "#717 = 0.154742",
        "#3032 = #717",
        "o<closure_sequence_complete> if [ABS[#978 - 29.0] GT 0.000001]",
        "o<trace_exact_count> if [ABS[#973 - 752.0] GT 0.000001]",
        "(DEBUG, TCPC_LENGTH_AWARE_T4_NEW_LOCATION_RECOVERY_2026082701 complete)",
        "Sphere-to-post direction remains X+ Y- Z+.",
    )
    for snippet in required_once:
        if text.count(snippet) != 1:
            raise ValidationError(f"runner contract changed for {snippet!r}")

    top = top_level_lines(text)
    if top.count("M0") != 1 or any(line == "M1" for line in top):
        raise ValidationError("runner must contain one top-level M0 and no M1")
    m0_index = top.index("M0")
    motion = re.compile(
        r"\b(?:G0|G1|G2|G3|G38\.[2345])\b.*\b[XYZBC](?=[-+#\d\[])", re.I
    )
    if any(motion.search(line) for line in top[:m0_index]):
        raise ValidationError("top-level axis motion exists before the initial M0")
    if [line for line in text.splitlines() if re.match(r"^\s*G4\b", line)] != [
        "    G4 P0.05", "    G4 P0.05"
    ]:
        raise ValidationError("only the two reviewed 0.05-second gate dwells are allowed")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ValidationError("four-contact acquisition must contain four G38.3 sites")
    guarded = re.findall(
        r"o<tcpc_pair_probe_final_guard> call \[#520\] \[#521\]\s*\n\s*G38\.3\b",
        text,
    )
    if len(guarded) != 4:
        raise ValidationError("every G38.3 lacks its immediate final live/model guard")
    validate_no_direct_hal_writes(text)

    expected_paths = {str(path) for path in RECOVERY_FILES.values()}
    logged_paths = re.findall(r"\(LOGAPPEND,([^\r\n)]+)\)", text)
    if len(logged_paths) != 6 or set(logged_paths) != expected_paths:
        raise ValidationError("LOGAPPEND destinations are not the six isolated recovery files")
    if any(logged_paths.count(path) != 1 or text.count(path) != 2 for path in expected_paths):
        raise ValidationError("a recovery output path is not referenced exactly twice/leg once")
    if any(str(path) in logged_paths for path in ATTEMPT1_FILES.values()):
        raise ValidationError("recovery runner can append to a sealed Attempt-1 output")

    critical = (
        "tcpc_pair_coordinate_guard", "tcpc_pair_hold_position_guard",
        "tcpc_pair_selector_guard", "tcpc_length_model_guard",
        "tcpc_pair_live_guard", "tcpc_pair_release_guard",
        "tcpc_probe_counter_guard", "tcpc_contact_gap_log",
        "tcpc_contact_trace_begin", "tcpc_contact_trace_post",
        "tcpc_contact_trace_finish", "tcpc_pair_probe_final_guard",
        "tcpc_pair_probe_ready_guard", "tcpc_vector_sphere_pass4",
        "tcpc_measure_pose", "tcpc_primary_closure_guard",
        "tcpc_primary_outer_reference", "tcpc_primary_b0_sweep",
        "tcpc_primary_low_tilt_block", "tcpc_primary_tilt_block",
        "tcpc_baseline_return_top_clear",
    )
    for name in critical:
        recovery = normalized_recovery_subroutine(extract_subroutine(text, name), name)
        original = extract_subroutine(attempt1_text, name)
        if recovery != original:
            raise ValidationError(f"sealed motion/safety subroutine changed: {name}")

    definitions = set(re.findall(r"(?m)^o<([^>]+)> sub\s*$", text))
    calls = set(re.findall(r"(?m)^\s*o<([^>]+)> call(?:\s|$)", text))
    if calls - definitions:
        raise ValidationError(f"unresolved subroutine call(s): {sorted(calls - definitions)}")

    body_match = re.search(
        r"(?ms)^o<run_relocated_t4_recovery> if .*?^o<run_relocated_t4_recovery> endif$",
        text,
    )
    if not body_match:
        raise ValidationError("recovery body is missing")
    body = body_match.group(0)
    acquisition_calls = [
        line.strip() for line in body.splitlines()
        if re.search(
            r"o<(?:tcpc_primary_b0_sweep|tcpc_measure_pose|"
            r"tcpc_primary_low_tilt_block|tcpc_primary_tilt_block)> call",
            line,
        )
    ]
    expected_calls = [
        "o<tcpc_primary_b0_sweep> call [100.0]",
        "o<tcpc_measure_pose> call [-5.0] [0.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [45.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [90.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [180.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [225.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [270.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [0.0] [0.0] [0.0]",
        "o<tcpc_primary_low_tilt_block> call [10.0] [10.0]",
        "o<tcpc_primary_low_tilt_block> call [-10.0] [-10.0]",
        "o<tcpc_primary_low_tilt_block> call [15.0] [15.0]",
        "o<tcpc_primary_low_tilt_block> call [-15.0] [-15.0]",
        "o<tcpc_primary_tilt_block> call [30.0] [30.0]",
        "o<tcpc_primary_tilt_block> call [-30.0] [-30.0]",
        "o<tcpc_primary_tilt_block> call [45.0] [45.0]",
        "o<tcpc_primary_tilt_block> call [-45.0] [-45.0]",
        "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]",
        "o<tcpc_primary_tilt_block> call [60.0] [60.0]",
        "o<tcpc_primary_tilt_block> call [-60.0] [-60.0]",
        "o<tcpc_primary_tilt_block> call [90.0] [90.0]",
        "o<tcpc_primary_tilt_block> call [-90.0] [-90.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
    ]
    if acquisition_calls != expected_calls:
        raise ValidationError("recovery acquisition topology/order changed")
    if body.count("#726 = 16.0") != 1:
        raise ValidationError("recovery no longer skips canonical summary IDs 10..16")

    sealed_results = read_rows(ATTEMPT1_FILES["results"], anchor.RESULT_FIELDS)
    bridge_calls = []
    for seq, block in ((9, 3609), (17, 3617)):
        row = sealed_results[seq - 1]
        xyz = [number(row, f"center_abs_{axis}_mm") for axis in "xyz"]
        bridge_calls.append(
            "o<tcpc_primary_closure_guard> call "
            f"[{xyz[0]:.6f}] [{xyz[1]:.6f}] [{xyz[2]:.6f}] "
            f"[{block}.0] [{seq}.0] [#726]"
        )
    for call in bridge_calls:
        if body.count(call) != 1:
            raise ValidationError(f"sealed cross-attempt bridge changed: {call}")


def validate_static_source() -> None:
    require_hash(PROGRAM, PROGRAM_SHA256)
    require_hash(ATTEMPT1_PROGRAM, ATTEMPT1_PROGRAM_SHA256)
    for path, digest in SEALED_READERS.items():
        require_hash(path, digest)
    try:
        text = PROGRAM.read_text(encoding="ascii")
        attempt1 = ATTEMPT1_PROGRAM.read_text(encoding="ascii")
    except UnicodeError as exc:
        raise ValidationError("runner is not ASCII") from exc
    validate_program_text(text, attempt1)
    validate_python_safety(Path(__file__).read_text(encoding="ascii"))
    if RECOVERY_SEQS != tuple(range(1, 10)) + tuple(range(17, 102)):
        raise ValidationError("internal recovery sequence mapping changed")
    if len(CANONICAL_EXPECTED) != 101 or len(campaign.T4_CLOSURES) != 28:
        raise ValidationError("imported canonical T4 topology changed")


def expected_empirical_vector(b_deg: float, c_deg: float) -> np.ndarray:
    basis = bounds.basis_values(b_deg, np.asarray([c_deg], dtype=float))
    coefficients = bounds.surface_coefficients(TOOL_LENGTH_MM)["total"]
    return bounds.evaluate_surface(basis, coefficients)[0]


def validate_model_row(
    row: dict[str, str], expected: campaign.ExpectedRow, *, mode: int, attempt: int
) -> None:
    seq = require_identity(row, "sample_seq", mode=mode, attempt=attempt)
    if seq != expected.seq:
        raise ValidationError(f"model-state sequence {seq} is out of order")
    for field, value in (
        ("model_id", MODEL_ID), ("expected_model_id", MODEL_ID),
        ("configured", 1), ("valid", 1), ("fault_code", 0),
    ):
        if exact_int(row, field) != value:
            raise ValidationError(f"model-state seq {seq}: {field} mismatch")
    if abs(number(row, "q")) > 1e-6:
        raise ValidationError(f"model-state seq {seq}: T4 must evaluate q=0")
    if angular_error(number(row, "evaluated_b_deg"), expected.pose.b_deg) > 0.01:
        raise ValidationError(f"model-state seq {seq}: evaluated B mismatch")
    if angular_error(number(row, "evaluated_c_deg"), expected.pose.c_deg) > 0.01:
        raise ValidationError(f"model-state seq {seq}: evaluated C mismatch")
    if abs(number(row, "evaluated_length_mm") - TOOL_LENGTH_MM) > 0.002:
        raise ValidationError(f"model-state seq {seq}: evaluated length mismatch")
    diff = np.asarray([number(row, f"diff_offset_{axis}_mm") for axis in "xyz"])
    diff_norm = number(row, "diff_offset_norm_mm")
    if np.max(np.abs(diff)) > 1e-6 or abs(diff_norm) > 1e-6:
        raise ValidationError(f"model-state seq {seq}: q=0 differential bank is nonzero")
    if abs(diff_norm - float(np.linalg.norm(diff))) > 3e-6 or diff_norm > DIFF_CAP_MM:
        raise ValidationError(f"model-state seq {seq}: differential norm/cap mismatch")
    empirical = np.asarray(
        [number(row, f"empirical_offset_{axis}_mm") for axis in "xyz"]
    )
    empirical_norm = number(row, "empirical_offset_norm_mm")
    expected_vector = expected_empirical_vector(expected.pose.b_deg, expected.pose.c_deg)
    if not 0.0 <= empirical_norm <= TOTAL_CAP_MM:
        raise ValidationError(f"model-state seq {seq}: empirical norm exceeds cap")
    if abs(empirical_norm - float(np.linalg.norm(empirical))) > 5e-6:
        raise ValidationError(f"model-state seq {seq}: empirical vector/norm mismatch")
    if float(np.linalg.norm(empirical - expected_vector)) > 2e-5:
        raise ValidationError(f"model-state seq {seq}: empirical vector differs from sealed model")


def counter_tuple(row: dict[str, str], prefix: str) -> tuple[int, int, int]:
    return tuple(
        exact_int(row, f"{prefix}_{name}_count") for name in ("raw", "mux", "gated")
    )  # type: ignore[return-value]


def trace_key(
    row: dict[str, str], sequence_field: str, *, mode: int, attempt: int
) -> tuple[int, int, int, int]:
    return (
        require_identity(row, sequence_field, mode=mode, attempt=attempt),
        exact_int(row, "acquisition_try", positive=True),
        exact_int(row, "pass_id", positive=True),
        exact_int(row, "contact_id", positive=True),
    )


def validate_trace_pose(row: dict[str, str], seq: int) -> None:
    if seq not in EXPECTED_BY_SEQ:
        raise ValidationError(f"trace sequence {seq} is outside 1..101")
    expected = EXPECTED_BY_SEQ[seq].pose
    if angular_error(number(row, "abs_b_deg"), expected.b_deg) > 0.01:
        raise ValidationError(f"trace seq {seq}: B pose mismatch")
    if angular_error(number(row, "abs_c_deg"), expected.c_deg) > 0.01:
        raise ValidationError(f"trace seq {seq}: C pose mismatch")


def validate_contact_row(
    row: dict[str, str], key: tuple[int, int, int, int], *, max_extra: int
) -> int:
    seq, _, _, contact_id = key
    validate_trace_pose(row, seq)
    pre, post, ready = (
        counter_tuple(row, prefix) for prefix in ("pre", "post", "ready")
    )
    if any(value < 0 for value in pre + post + ready):
        raise ValidationError(f"contact trace seq {seq}: negative counter")
    if any(not pre[index] <= post[index] <= ready[index] for index in range(3)):
        raise ValidationError(f"contact trace seq {seq}: non-monotonic counter")
    direct = tuple(post[index] - pre[index] for index in range(3))
    repeats = tuple(ready[index] - post[index] for index in range(3))
    total = tuple(ready[index] - pre[index] for index in range(3))
    for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
        if exact_int(row, field) != value:
            raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
    for field, value in zip(
        ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats
    ):
        if exact_int(row, field) != value:
            raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
    if direct[0] != direct[1] or direct[0] < 1 or direct[2] != 1:
        raise ValidationError(f"contact trace seq {seq}: G38 edge mismatch")
    if repeats[0] != repeats[1] or repeats[2] != 0 or total[0] != total[1]:
        raise ValidationError(f"contact trace seq {seq}: repeat/total edge mismatch")
    extra = total[0] - total[2]
    if exact_int(row, "extra_raw_minus_gated_delta") != extra:
        raise ValidationError(f"contact trace seq {seq}: extra-edge field mismatch")
    if not 0 <= extra <= max_extra:
        raise ValidationError(f"contact trace seq {seq}: filtered extras exceed {max_extra}")
    for field in ("burst_flag", "consistency_fault", "release_fault", "terminal_failure"):
        if exact_int(row, field) != 0:
            raise ValidationError(f"contact trace seq {seq}: {field} is nonzero")
    if exact_int(row, "probe_result") != 1:
        raise ValidationError(f"contact trace seq {seq}: probe result is not success")
    upper = 7.01 if contact_id == 1 else 6.01
    if not 1.0 <= number(row, "travel_mm") <= upper:
        raise ValidationError(f"contact trace seq {seq}: travel outside contract")
    return extra


def validate_gap_row(
    gap: dict[str, str], contact: dict[str, str], previous: dict[str, str] | None,
    index: int, key: tuple[int, int, int, int], *, max_extra: int,
) -> int:
    seq = key[0]
    validate_trace_pose(gap, seq)
    prior = counter_tuple(gap, "prior_ready")
    current = counter_tuple(gap, "current_pre")
    delta = tuple(current[item] - prior[item] for item in range(3))
    if any(value < 0 for value in prior + current + delta):
        raise ValidationError(f"gap trace seq {seq}: invalid counter progression")
    for field, value in zip(("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"), delta):
        if exact_int(gap, field) != value:
            raise ValidationError(f"gap trace seq {seq}: {field} mismatch")
    initial = exact_int(gap, "initial_baseline")
    if initial != int(index == 0):
        raise ValidationError("only the first source gap may mark the initial baseline")
    prior_extra = exact_int(gap, "prior_contact_extra_delta")
    if previous is None:
        if prior_extra != 0:
            raise ValidationError("initial gap has nonzero prior-contact extras")
    else:
        if prior != counter_tuple(previous, "ready"):
            raise ValidationError(f"gap trace seq {seq}: prior-ready boundary changed")
        if prior_extra != exact_int(previous, "extra_raw_minus_gated_delta"):
            raise ValidationError(f"gap trace seq {seq}: prior-contact extras changed")
    if current != counter_tuple(contact, "pre"):
        raise ValidationError(f"gap trace seq {seq}: current-pre boundary changed")
    combined = prior_extra + delta[0] - delta[2]
    if exact_int(gap, "combined_extra_delta") != combined:
        raise ValidationError(f"gap trace seq {seq}: combined-extra mismatch")
    if (
        delta[0] != delta[1] or delta[2] != 0 or (initial == 1 and any(delta))
        or not 0 <= combined <= max_extra
    ):
        raise ValidationError(f"gap trace seq {seq}: electrical gate failure")
    for field in ("burst_flag", "consistency_fault"):
        if exact_int(gap, field) != 0:
            raise ValidationError(f"gap trace seq {seq}: {field} is nonzero")
    return delta[0]


def expected_transaction_keys(sequences: Sequence[int]) -> list[tuple[int, int, int, int]]:
    return [
        (seq, 1, pass_id, contact_id)
        for seq in sequences for pass_id in (1, 2) for contact_id in (1, 2, 3, 4)
    ]


def validate_transaction_chain(
    contacts: Sequence[dict[str, str]], gaps: Sequence[dict[str, str]],
    sequences: Sequence[int], *, mode: int, attempt: int, max_extra: int,
) -> int:
    keys = expected_transaction_keys(sequences)
    if len(contacts) != len(keys) or len(gaps) != len(keys):
        raise ValidationError(f"trace count is {len(contacts)}/{len(gaps)}, expected {len(keys)}")
    if [trace_key(row, "global_seq", mode=mode, attempt=attempt) for row in contacts] != keys:
        raise ValidationError("contact transaction keys/order changed")
    if [trace_key(row, "next_global_seq", mode=mode, attempt=attempt) for row in gaps] != keys:
        raise ValidationError("gap transaction keys/order changed")
    previous: dict[str, str] | None = None
    extras = 0
    for index, (contact, gap, key) in enumerate(zip(contacts, gaps, keys)):
        extras += validate_contact_row(contact, key, max_extra=max_extra)
        extras += validate_gap_row(
            gap, contact, previous, index, key, max_extra=max_extra
        )
        previous = contact
    return extras


def validate_attempt1_partial() -> tuple[
    list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]
]:
    for suffix, digest in ATTEMPT1_PARTIAL_HASHES.items():
        require_hash(ATTEMPT1_FILES[suffix], digest)
    rows = {suffix: read_rows(ATTEMPT1_FILES[suffix], FIELDS[suffix]) for suffix in SUFFIXES}
    counts = tuple(len(rows[suffix]) for suffix in SUFFIXES)
    if counts != (17, 17, 17, 2, 137, 138):
        raise ValidationError(f"Attempt-1 sealed partial counts changed: {counts}")
    results, states, models = rows["results"], rows["state"], rows["model-state"]
    with campaign_identity():
        for result, state, model, expected in zip(
            results, states, models, CANONICAL_EXPECTED[:17]
        ):
            campaign.validate_result(ATTEMPT1_SPEC, result, expected, ATTEMPT1_ATTEMPT)
            campaign.validate_state(ATTEMPT1_SPEC, state, result, expected, ATTEMPT1_ATTEMPT)
            validate_model_row(
                model, expected, mode=ATTEMPT1_MODE, attempt=ATTEMPT1_ATTEMPT
            )
        campaign.validate_closures(
            ATTEMPT1_SPEC, rows["closures"],
            {expected.seq: result for expected, result in zip(CANONICAL_EXPECTED, results)},
            ATTEMPT1_ATTEMPT,
        )
    contacts, gaps = rows["contact-trace"], rows["gap-trace"]
    validate_transaction_chain(
        contacts[:ATTEMPT1_ACCEPTED_TRANSACTIONS],
        gaps[:ATTEMPT1_ACCEPTED_TRANSACTIONS], ATTEMPT1_SEQS,
        mode=ATTEMPT1_MODE, attempt=ATTEMPT1_ATTEMPT,
        max_extra=MAX_ATTEMPT1_EXTRA_EDGES,
    )
    incomplete_key = (18, 1, 1, 1)
    if trace_key(
        contacts[136], "global_seq", mode=ATTEMPT1_MODE, attempt=ATTEMPT1_ATTEMPT
    ) != incomplete_key:
        raise ValidationError("Attempt-1 rejected prefix is not seq18/pass1/contact1")
    validate_contact_row(contacts[136], incomplete_key, max_extra=2)
    validate_gap_row(
        gaps[136], contacts[136], contacts[135], 136, incomplete_key, max_extra=2
    )
    failed_gap = gaps[137]
    failed_key = trace_key(
        failed_gap, "next_global_seq", mode=ATTEMPT1_MODE, attempt=ATTEMPT1_ATTEMPT
    )
    if failed_key != (18, 1, 1, 2):
        raise ValidationError("Attempt-1 terminal gap is not seq18/pass1/contact2")
    prior = counter_tuple(failed_gap, "prior_ready")
    current = counter_tuple(failed_gap, "current_pre")
    delta = tuple(current[index] - prior[index] for index in range(3))
    if prior != counter_tuple(contacts[136], "ready") or delta != (4, 4, 0):
        raise ValidationError("Attempt-1 terminal gap no longer records matched 4/4/0 edges")
    if any(
        exact_int(failed_gap, field) != value
        for field, value in (
            ("gap_raw_delta", 4), ("gap_mux_delta", 4), ("gap_gated_delta", 0),
            ("prior_contact_extra_delta", 0), ("combined_extra_delta", 4),
            ("burst_flag", 1), ("consistency_fault", 0), ("initial_baseline", 0),
        )
    ):
        raise ValidationError("Attempt-1 terminal gap abort semantics changed")
    return results, states, models


def validate_fresh_outputs() -> None:
    for suffix, path in RECOVERY_FILES.items():
        rows = read_rows(path, FIELDS[suffix])
        if rows:
            raise ValidationError(f"recovery {suffix} output is not fresh/header-only")
        attempt1_header = ATTEMPT1_FILES[suffix].read_text(encoding="ascii").splitlines()[0]
        recovery_header = path.read_text(encoding="ascii").splitlines()[0]
        if recovery_header != attempt1_header:
            raise ValidationError(f"recovery {suffix} header differs from Attempt 1")


def validate_preflight() -> None:
    validate_static_source()
    validate_attempt1_partial()
    validate_fresh_outputs()


def validate_recovery_summaries() -> tuple[
    list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[int, np.ndarray]
]:
    results = read_rows(RECOVERY_FILES["results"], anchor.RESULT_FIELDS)
    states = read_rows(RECOVERY_FILES["state"], anchor.STATE_FIELDS)
    models = read_rows(RECOVERY_FILES["model-state"], MODEL_STATE_FIELDS)
    if (len(results), len(states), len(models)) != (94, 94, 94):
        raise ValidationError("recovery summary files are not exact 94/94/94 rows")
    for rows, field in ((results, "sample_seq"), (states, "sample_seq"), (models, "sample_seq")):
        seqs = [require_identity(row, field, mode=MODE, attempt=ATTEMPT) for row in rows]
        if tuple(seqs) != RECOVERY_SEQS:
            raise ValidationError("recovery summary sequence is not exact 1..9,17..101")
    centers: dict[int, np.ndarray] = {}
    with campaign_identity():
        for result, state, model, expected in zip(results, states, models, RECOVERY_EXPECTED):
            centers[expected.seq] = campaign.validate_result(
                RECOVERY_SPEC, result, expected, ATTEMPT
            )
            campaign.validate_state(RECOVERY_SPEC, state, result, expected, ATTEMPT)
            validate_model_row(model, expected, mode=MODE, attempt=ATTEMPT)
    return results, states, models, centers


# block, open sequence, close sequence, sealed Attempt-1 open sequence or None.
RECOVERY_CLOSURE_TOPOLOGY = (
    (100, 1, 9, None), (3609, 9, 9, 9), (3617, 17, 17, 17),
    (-5, 17, 23, None), (10, 24, 30, None), (-10, 31, 37, None),
    (15, 38, 44, None), (-15, 45, 51, None), (30, 52, 56, None),
    (-30, 57, 61, None), (45, 62, 66, None), (-45, 67, 71, None),
    (905, 9, 72, None), (60, 73, 77, None), (-60, 78, 82, None),
    (90, 83, 87, None), (-90, 88, 92, None), (911, 1, 93, None),
    (906, 72, 93, None), (912, 2, 94, None), (913, 3, 95, None),
    (914, 4, 96, None), (915, 5, 97, None), (916, 6, 98, None),
    (917, 7, 99, None), (918, 8, 100, None), (919, 9, 101, None),
    (200, 93, 101, None), (900, 1, 101, None),
)


def centers_from_results(rows: Sequence[dict[str, str]]) -> dict[int, np.ndarray]:
    return {
        exact_int(row, "sample_seq", positive=True): np.asarray(
            [number(row, f"center_abs_{axis}_mm") for axis in "xyz"]
        )
        for row in rows
    }


def validate_recovery_closures(
    recovery_centers: dict[int, np.ndarray], attempt1_centers: dict[int, np.ndarray]
) -> tuple[float, float, float]:
    rows = read_rows(RECOVERY_FILES["closures"], campaign.CLOSURE_FIELDS)
    if len(rows) != EXPECTED_RECOVERY_CLOSURES:
        raise ValidationError(f"recovery closure count is {len(rows)}, expected 29")
    norms: list[float] = []
    bridges: dict[int, float] = {}
    for row, (block, open_seq, close_seq, sealed_open_seq) in zip(
        rows, RECOVERY_CLOSURE_TOPOLOGY
    ):
        require_identity(row, "close_sample_seq", mode=MODE, attempt=ATTEMPT)
        for field, value in (
            ("block_id", block), ("open_sample_seq", open_seq),
            ("close_sample_seq", close_seq), ("pass", 1),
        ):
            if exact_int(row, field) != value:
                raise ValidationError(f"recovery closure {block}: {field} mismatch")
        open_center = (
            attempt1_centers[sealed_open_seq]
            if sealed_open_seq is not None else recovery_centers[open_seq]
        )
        delta = recovery_centers[close_seq] - open_center
        logged = np.asarray([number(row, f"closure_d{axis}_mm") for axis in "xyz"])
        norm = float(np.linalg.norm(delta))
        if float(np.linalg.norm(delta - logged)) > 3e-6:
            raise ValidationError(f"recovery closure {block}: vector mismatch")
        if abs(number(row, "closure_norm_mm") - norm) > 3e-6:
            raise ValidationError(f"recovery closure {block}: norm mismatch")
        if abs(number(row, "limit_mm") - CLOSURE_LIMIT_MM) > 1e-9:
            raise ValidationError(f"recovery closure {block}: limit changed")
        if norm > CLOSURE_LIMIT_MM:
            raise ValidationError(f"recovery closure {block}: exceeds 0.050 mm")
        expected_pose = EXPECTED_BY_SEQ[close_seq].pose
        if angular_error(number(row, "abs_b_deg"), expected_pose.b_deg) > 0.01:
            raise ValidationError(f"recovery closure {block}: B pose mismatch")
        if angular_error(number(row, "abs_c_deg"), expected_pose.c_deg) > 0.01:
            raise ValidationError(f"recovery closure {block}: C pose mismatch")
        if block in (3609, 3617):
            bridges[block] = norm
        norms.append(norm)
    return max(norms), bridges[3609], bridges[3617]


def normalize_identity(row: dict[str, str]) -> dict[str, str]:
    normalized = dict(row)
    normalized.update(
        schema_version="1", campaign_id=str(CAMPAIGN), stage_mode=str(MODE),
        attempt_id=str(ATTEMPT),
    )
    return normalized


def compose_rows(
    attempt1: Sequence[dict[str, str]], recovery: Sequence[dict[str, str]]
) -> list[dict[str, str]]:
    first = {exact_int(row, "sample_seq", positive=True): row for row in attempt1}
    second = {exact_int(row, "sample_seq", positive=True): row for row in recovery}
    if sorted(first) != list(range(1, 18)):
        raise ValidationError("Attempt-1 composite source is not exact rows 1..17")
    if sorted(second) != list(RECOVERY_SEQS):
        raise ValidationError("recovery composite source is not exact rows 1..9,17..101")
    composite = [
        normalize_identity(first[seq] if seq <= 17 else second[seq])
        for seq in range(1, 102)
    ]
    if [exact_int(row, "sample_seq") for row in composite] != list(range(1, 102)):
        raise ValidationError("composite does not cover exact canonical rows 1..101")
    return composite


def canonical_closure_max(centers: dict[int, np.ndarray]) -> float:
    norms = []
    for block, open_seq, close_seq in campaign.T4_CLOSURES:
        norm = float(np.linalg.norm(centers[close_seq] - centers[open_seq]))
        if norm > CLOSURE_LIMIT_MM:
            raise ValidationError(
                f"composite canonical closure {block} {open_seq}->{close_seq} "
                f"is {norm:.6f} mm, above 0.050 mm"
            )
        norms.append(norm)
    return max(norms)


def validate_complete() -> Metrics:
    validate_static_source()
    attempt1_results, attempt1_states, attempt1_models = validate_attempt1_partial()
    recovery_results, recovery_states, recovery_models, recovery_centers = (
        validate_recovery_summaries()
    )
    contacts = read_rows(RECOVERY_FILES["contact-trace"], CONTACT_TRACE_FIELDS)
    gaps = read_rows(RECOVERY_FILES["gap-trace"], GAP_TRACE_FIELDS)
    extras = validate_transaction_chain(
        contacts, gaps, RECOVERY_SEQS, mode=MODE, attempt=ATTEMPT,
        max_extra=MAX_RECOVERY_EXTRA_EDGES,
    )
    attempt1_centers = centers_from_results(attempt1_results)
    worst_recovery, bridge9, bridge17 = validate_recovery_closures(
        recovery_centers, attempt1_centers
    )
    composite_results = compose_rows(attempt1_results, recovery_results)
    composite_states = compose_rows(attempt1_states, recovery_states)
    composite_models = compose_rows(attempt1_models, recovery_models)

    # Reuse the established full-run geometry/state/model and mapping checks on
    # the in-memory canonical composition.  Source identities were validated
    # before normalization, so this cannot conceal a cross-attempt mismatch.
    raw_centers, keys = full.result_centers(composite_results, CAMPAIGN, MODE, ATTEMPT)
    full.validate_states(composite_states, composite_results, CAMPAIGN, MODE, ATTEMPT)
    full.validate_model_rows(composite_models, CAMPAIGN, MODE, ATTEMPT)
    for row, expected in zip(composite_models, CANONICAL_EXPECTED):
        validate_model_row(row, expected, mode=MODE, attempt=ATTEMPT)
    centers = {seq: raw_centers[seq - 1] for seq in range(1, 102)}
    worst_canonical = canonical_closure_max(centers)
    _, groups = full.canonical_groups(keys)
    unique_centers = full.collapse(raw_centers, groups)
    raw_metric = full.center_metric(raw_centers)
    unique_metric = full.center_metric(unique_centers)
    full.repeated_pose_scatter(raw_centers, keys)
    full.b0_drift(raw_centers, keys)
    return Metrics(
        raw_metric.rms, raw_metric.maximum,
        unique_metric.rms, unique_metric.maximum,
        unique_metric.rms <= RMS_LIMIT_MM and unique_metric.maximum <= MAX_LIMIT_MM,
        worst_recovery, worst_canonical, bridge9, bridge17, extras,
    )


def expect_failure(label: str, operation: Callable[[], object]) -> None:
    try:
        operation()
    except (ValidationError, anchor.ValidationError, full.AnalysisError, ValueError):
        return
    raise AssertionError(f"self-test mutation was accepted: {label}")


def synthetic_contact(extra: int) -> dict[str, str]:
    row = {field: "0" for field in CONTACT_TRACE_FIELDS}
    row.update(
        schema_version="1", campaign_id=str(CAMPAIGN), stage_mode=str(MODE),
        attempt_id=str(ATTEMPT), global_seq="1", abs_b_deg="0", abs_c_deg="0",
        acquisition_try="1", pass_id="1", contact_id="1", probe_result="1",
        travel_mm="5", pre_raw_count="100", pre_mux_count="100",
        pre_gated_count="100", post_raw_count=str(101 + extra),
        post_mux_count=str(101 + extra), post_gated_count="101",
        ready_raw_count=str(101 + extra), ready_mux_count=str(101 + extra),
        ready_gated_count="101", raw_delta=str(1 + extra),
        mux_delta=str(1 + extra), gated_delta="1", repeat_raw_delta="0",
        repeat_mux_delta="0", repeat_gated_delta="0",
        extra_raw_minus_gated_delta=str(extra), burst_flag="0",
        consistency_fault="0", release_fault="0", terminal_failure="0",
    )
    return row


def self_test() -> None:
    validate_static_source()
    validate_attempt1_partial()
    assert RECOVERY_SEQS == tuple(range(1, 10)) + tuple(range(17, 102))
    assert len(RECOVERY_SEQS) == 94
    assert len(RECOVERY_CLOSURE_TOPOLOGY) == 29
    assert len(expected_transaction_keys(RECOVERY_SEQS)) == 752

    text = PROGRAM.read_text(encoding="ascii")
    original = ATTEMPT1_PROGRAM.read_text(encoding="ascii")
    mutations = {
        "M0 removal": text.replace("\nM0\n", "\n", 1),
        "pre-M0 motion": text.replace("\nM0\n", "\nG1 Z0\nM0\n", 1),
        "attempt identity": text.replace("#727 = 2.0", "#727 = 3.0", 1),
        "edge allowance": text.replace("#779 = 8.0", "#779 = 9.0", 1),
        "trace count": text.replace("#973 - 752.0", "#973 - 751.0", 1),
        "closure count": text.replace("#978 - 29.0", "#978 - 28.0", 1),
        "bridge constant": text.replace("[2501.004768]", "[2501.004769]", 1),
        "output isolation": text.replace("attempt2-recovery-results.csv", "attempt1-results.csv", 1),
        "final G38 guard": text.replace(
            "o<tcpc_pair_probe_final_guard> call [#520] [#521]\n  G38.3",
            "o<tcpc_pair_live_guard> call [1.0] [#520] [#521]\n  G38.3", 1,
        ),
        "direct HAL write": text + "\nsetp headheadkins.length-model.id 7\n",
        "long dwell": text.replace("G4 P0.05", "G4 P20", 1),
        "recovery topology": text.replace(
            "o<tcpc_primary_tilt_block> call [60.0] [60.0]",
            "o<tcpc_primary_tilt_block> call [61.0] [60.0]", 1,
        ),
    }
    for label, mutated in mutations.items():
        expect_failure(label, lambda value=mutated: validate_program_text(value, original))

    accepted = synthetic_contact(8)
    validate_contact_row(accepted, (1, 1, 1, 1), max_extra=8)
    expect_failure(
        "nine matched contact extras",
        lambda: validate_contact_row(synthetic_contact(9), (1, 1, 1, 1), max_extra=8),
    )
    mismatched = synthetic_contact(1)
    mismatched["post_mux_count"] = "101"
    expect_failure(
        "raw/mux contact mismatch",
        lambda: validate_contact_row(mismatched, (1, 1, 1, 1), max_extra=8),
    )

    attempt1 = [{"sample_seq": str(seq), "value": f"a{seq}"} for seq in range(1, 18)]
    recovery = [
        {"sample_seq": str(seq), "value": f"r{seq}"} for seq in RECOVERY_SEQS
    ]
    composite = compose_rows(attempt1, recovery)
    if composite[16]["value"] != "a17" or composite[17]["value"] != "r18":
        raise AssertionError("canonical composition did not preserve row17/reacquire row18")
    missing = recovery[:-1]
    expect_failure("missing recovery row101", lambda: compose_rows(attempt1, missing))

    model = dict(read_rows(ATTEMPT1_FILES["model-state"], MODEL_STATE_FIELDS)[0])
    model["q"] = "0.001"
    expect_failure(
        "nonzero T4 q",
        lambda: validate_model_row(
            model, CANONICAL_EXPECTED[0], mode=ATTEMPT1_MODE, attempt=1
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static", action="store_true", help="read-only source/provenance audit")
    modes.add_argument("--preflight", action="store_true", help="static audit plus fresh outputs")
    modes.add_argument("--validate", action="store_true", help="validate recovery and composite")
    modes.add_argument("--self-test", action="store_true", help="run static and mutation tests")
    args = parser.parse_args(argv)
    try:
        metrics: Metrics | None = None
        if args.static:
            validate_static_source()
            validate_attempt1_partial()
            label = "STATIC PASS"
        elif args.preflight:
            validate_preflight()
            label = "PREFLIGHT PASS"
        elif args.validate:
            metrics = validate_complete()
            label = "COMPOSITE ACQUISITION VALID"
        else:
            self_test()
            label = "SELF-TEST PASS"
    except (
        AssertionError, OSError, UnicodeError, ValidationError,
        anchor.ValidationError, bounds.AuditError, full.AnalysisError, ValueError,
    ) as exc:
        print(f"T4 new-location recovery validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"T4 new-location attempt-2 recovery {label}")
    print(f"runner_sha256={PROGRAM_SHA256}")
    print("identity=campaign2026082701/mode36/attempt2")
    print("recovery=rows94 sequences1..9,17..101 closures29 traces752")
    if metrics is not None:
        print(f"transfer={'PASS' if metrics.transfer_pass else 'FAIL'}")
        for field in Metrics.__dataclass_fields__:
            if field == "transfer_pass":
                continue
            value = getattr(metrics, field)
            print(f"{field}={value:.6f}" if isinstance(value, float) else f"{field}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
