#!/usr/bin/env python3
"""Deterministic offline preflight and result validation for T3 Attempt 1."""

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
MODE = 33
ATTEMPT = 1
MODEL_ID = 2026082601
TOOL = 3
TOOL_LENGTH_MM = 128.606729
PROBE_OFFSET_MM = 0.117658
DIFF_CAP_MM = 0.400000
TOTAL_CAP_MM = 1.350000
RMS_LIMIT_MM = 0.120
MAX_LIMIT_MM = 0.280
RMS_IMPROVEMENT_FRACTION = 0.90
RMS_IMPROVEMENT_MIN_MM = 0.010
MAX_IMPROVEMENT_FRACTION = 0.90
MAX_IMPROVEMENT_MIN_MM = 0.020
B0_RMS_WORSENING_LIMIT_MM = 0.010
POSE_WORSENING_LIMIT_MM = 0.050
EXPECTED_ROWS = 31
EXPECTED_CLOSURES = 14
EXPECTED_TRANSACTIONS = 248
EXPECTED_UNIQUE_POSES = 20
MAX_FILTERED_EXTRA_EDGES = 2

PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t3_validation_2026082601_attempt1.ngc"
CANONICAL_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc"
SAFETY_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_validation_2026082601_attempt2.ngc"
VALIDATION_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini"
CANDIDATE_HAL = HERE / "tcpc_length_aware_candidate_2026082601.hal"
ASSESSOR = HERE / "assess_tcpc_length_aware_bounds.py"
MODEL_PLAN = HERE / "TCPC_LENGTH_AWARE_MODEL_PLAN.md"
ANCHOR_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_anchor.py"
CAMPAIGN_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_campaign.py"
REACHABILITY_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_reachability.py"
R3_FEASIBILITY_ANALYZER = HERE / "assess_tcpc_r3_feasibility.py"
KINS_SOURCE = REPO_ROOT / "src/emc/kinematics/headheadkins.c"
KINS_MODULE = REPO_ROOT / "rtlib/headheadkins.so"
PROBE_COUNTER_HAL = HERE / "tcpc_probe_attempt3_edge_counters.hal"
T4_COMPLETION_ARCHIVE = (
    HERE
    / "calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete"
)
T4_COMPLETION_MANIFEST = T4_COMPLETION_ARCHIVE / "SHA256SUMS"
T4_COMPLETION_REPORT = (
    T4_COMPLETION_ARCHIVE / "TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md"
)

OUTPUT_BASE = HERE / "tcpc-length-aware-t3-validation-2026082601-attempt1"
RESULTS = Path(f"{OUTPUT_BASE}-results.csv")
STATE = Path(f"{OUTPUT_BASE}-state.csv")
MODEL_STATE = Path(f"{OUTPUT_BASE}-model-state.csv")
CLOSURES = Path(f"{OUTPUT_BASE}-closures.csv")
CONTACT_TRACE = Path(f"{OUTPUT_BASE}-contact-trace.csv")
GAP_TRACE = Path(f"{OUTPUT_BASE}-gap-trace.csv")

DEFAULT_PREFLIGHT_REPORT = HERE / "TCPC_LENGTH_AWARE_T3_ATTEMPT1_PREFLIGHT_REPORT.md"
DEFAULT_RESULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T3_ATTEMPT1_VALIDATION_REPORT.md"
LINUXCNC_LOCK = Path("/tmp/linuxcnc.lock")

SEALED_SHA256 = {
    VALIDATION_INI: "24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a",
    CANDIDATE_HAL: "8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14",
    PROGRAM: "d6158b9ff91f5fa73a11071d314c64a442d6747f6758587415ece7c867e53bd6",
    CANONICAL_PROGRAM: "90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5",
    SAFETY_PROGRAM: "d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d",
    ASSESSOR: "b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2",
    MODEL_PLAN: "b8306e4612dff6ad52914ea0cd146bff39a093643f96a766836d82337ddc826e",
    ANCHOR_ANALYZER: "30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d",
    CAMPAIGN_ANALYZER: "d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a",
    REACHABILITY_ANALYZER: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    R3_FEASIBILITY_ANALYZER: "4520081bb7e7b4088a555e498ad7e6430dd3f5fc2d3d93a8a1e4c9867eaa6dd1",
    KINS_SOURCE: "cd3b4ba9c9dc82ab6cec266280d48f7fd6c5b0ad4064f16c3b87cfc7caff4fa0",
    KINS_MODULE: "1cc5b7023bed01bd2eb56bb52139e74f964cf17754b440aff42a987f4b22ac4c",
    PROBE_COUNTER_HAL: "6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34",
    T4_COMPLETION_MANIFEST: "546377e7ed7c98f4e24e6fc239b05810ea664ea101e6bd5d79e3c36558f9a880",
    T4_COMPLETION_REPORT: "0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae",
}

T4_REQUIRED_MEMBER_SHA256 = {
    "TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md":
        "0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae",
    "tcpc_length_aware_t4_validation_2026082601_attempt2.ngc":
        "d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d",
    "validate_tcpc_length_aware_t4_attempt2.py":
        "8d5f8c0fb34659d57377e9d3702cd4ac8614f008925e8cbcd33697316bc32f81",
    "tcpc-length-aware-t4-validation-2026082601-attempt2-results.csv":
        "ff1d93d954bd1e5a5370db26adaf6d77c1eb4c2823ef5bd5c6fbe1ec6e36e47c",
    "headheadkins.c":
        "cd3b4ba9c9dc82ab6cec266280d48f7fd6c5b0ad4064f16c3b87cfc7caff4fa0",
    "headheadkins.so":
        "1cc5b7023bed01bd2eb56bb52139e74f964cf17754b440aff42a987f4b22ac4c",
    "tcpc_probe_attempt3_edge_counters.hal":
        "6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34",
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

GRID = tuple(reach.verification_grid())
EXPECTED = campaign.expected_rows(GRID, campaign.T3_RANGES)
EXPECTED_BY_SEQ = {row.seq: row for row in EXPECTED}
SPEC = campaign.RunSpec(
    "T3 length-aware q=1 validation",
    TOOL,
    MODE,
    TOOL_LENGTH_MM,
    PROBE_OFFSET_MM,
    reach.T3_EFFECTIVE_RADIUS,
    RESULTS,
    STATE,
    CLOSURES,
    EXPECTED,
    campaign.T3_CLOSURES,
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
        raise ValidationError(
            f"{sequence_field}={seq} is outside 1..{EXPECTED_ROWS}"
        )
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
        r"^o<run_relocated_t3_(?:primary|exploratory)> if\b[\s\S]*?"
        r"^o<run_relocated_t3_(?:primary|exploratory)> endif\s*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        raise ValidationError("program is missing the canonical T3 run body")
    selected = []
    for line in match.group(0).splitlines():
        stripped = line.strip()
        if (
            re.fullmatch(r"#(?:728|729|738) = [-+0-9.]+", stripped)
            or re.match(
                r"^o<tcpc_(?:primary_b0_sweep|primary_tilt_block|measure_pose)> call\b",
                stripped,
            )
            or re.match(r"^o<tcpc_primary_closure_guard> call\b", stripped)
        ):
            selected.append(stripped)
    if len(selected) != 12:
        raise ValidationError(
            f"canonical T3 grid signature has {len(selected)} lines, expected 12"
        )
    return "\n".join(selected)


def strip_subroutine_definitions(text: str) -> str:
    return re.sub(
        r"^o<([^>]+)> sub\s*$[\s\S]*?^o<\1> endsub\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )


def validate_preview_and_prem0_boundary(text: str) -> None:
    preview = re.search(
        r"^o<preview_guard> if \[#<_task> EQ 0\]\s*$"
        r"[\s\S]*?^o<preview_guard> endif\s*$",
        text,
        re.MULTILINE,
    )
    if preview is None or len(re.findall(r"^o<preview_guard> if\b", text, re.MULTILINE)) != 1:
        raise ValidationError("runner must contain one exact preview guard")
    preview_active = [
        line.strip()
        for line in preview.group(0).splitlines()
        if line.strip() and not line.lstrip().startswith("(")
    ]
    if preview_active != [
        "o<preview_guard> if [#<_task> EQ 0]",
        "M2",
        "o<preview_guard> endif",
    ]:
        raise ValidationError("preview guard no longer exits through M2 before execution")
    first_runtime_access = min(
        position
        for token in ("#<_hal[", "(LOGAPPEND,", "G38.")
        if (position := text.find(token)) >= 0
    )
    if preview.end() > first_runtime_access:
        raise ValidationError("preview exit is not before HAL access/logging/probing")

    top_level = strip_subroutine_definitions(text)
    m0_matches = list(re.finditer(r"^\s*M0\s*$", top_level, re.MULTILINE))
    if len(m0_matches) != 1:
        raise ValidationError("top-level runner must contain exactly one M0")
    prefix = top_level[:m0_matches[0].start()]
    active = [
        line.strip()
        for line in prefix.splitlines()
        if line.strip() and not line.lstrip().startswith("(")
    ]
    motion_code = re.compile(
        r"(?:^|\s)(?:G0?0|G0?1|G0?2|G0?3|G33|G38)(?:\D|$)",
        re.IGNORECASE,
    )
    axis_word = re.compile(
        r"(?:^|\s)[XYZABCUVW](?:[-+#\[0-9.])", re.IGNORECASE
    )
    for original_line in active:
        line = re.sub(r"\([^)]*\)", "", original_line).strip()
        if motion_code.search(line) or axis_word.search(line) or re.match(
            r"^M66\b", line, re.IGNORECASE
        ):
            raise ValidationError(
                f"pre-M0 top level contains motion/probe activity: {original_line}"
            )
        if re.match(r"^M\d+\b", line, re.IGNORECASE) and not re.fullmatch(
            r"M(?:2|65\s+P[01](?:\.0*)?)", line, re.IGNORECASE
        ):
            raise ValidationError(f"pre-M0 top level contains unreviewed M code: {line}")
        if re.match(r"^o<[^>]+> call", line) and not re.match(
            r"^o<tcpc_(?:pair_coordinate_guard|length_model_guard)> call$", line
        ):
            raise ValidationError(f"pre-M0 top level contains unreviewed call: {line}")


def validate_accepted_row_boundary(text: str) -> None:
    measure = subroutine_text(text, "tcpc_measure_pose")
    summary = re.search(
        r"^  o<pair_summary_logging> if \[#714 GT 0\.5\]\s*$"
        r"[\s\S]*?^  o<pair_summary_logging> endif\s*$",
        measure,
        re.MULTILINE,
    )
    if summary is None:
        raise ValidationError("accepted-row summary boundary is missing")
    core = [
        line.strip()
        for line in summary.group(0).splitlines()[1:-1]
        if line.strip()
        and (
            not line.lstrip().startswith("(")
            or line.lstrip().startswith("(LOG")
        )
    ]
    snapshot = (
        "o<tcpc_pair_selector_guard> call",
        "o<tcpc_pair_live_guard> call [1.0] [#520] [#521]",
        "o<tcpc_length_model_guard> call",
        "#980 = #<_hal[headheadkins.length-model.id]>",
        "#981 = #<_hal[headheadkins.length-model.expected-id]>",
        "#982 = #<_hal[headheadkins.length-model.configured]>",
        "#983 = #<_hal[headheadkins.length-model.valid]>",
        "#984 = #<_hal[headheadkins.length-model.fault-code]>",
        "#985 = #<_hal[headheadkins.length-model.q]>",
        "#986 = #<_hal[headheadkins.tool-offset-eval.b]>",
        "#987 = #<_hal[headheadkins.tool-offset-eval.c]>",
        "#988 = #<_hal[headheadkins.tool-offset-eval.length]>",
        "#989 = #<_hal[headheadkins.length-model.diff-offset.x]>",
        "#990 = #<_hal[headheadkins.length-model.diff-offset.y]>",
        "#991 = #<_hal[headheadkins.length-model.diff-offset.z]>",
        "#992 = #<_hal[headheadkins.length-model.diff-offset-norm]>",
        "#993 = #<_hal[headheadkins.empirical-offset.x]>",
        "#994 = #<_hal[headheadkins.empirical-offset.y]>",
        "#995 = #<_hal[headheadkins.empirical-offset.z]>",
        "#996 = #<_hal[headheadkins.empirical-offset-norm]>",
    )
    if tuple(core[:len(snapshot)]) != snapshot:
        raise ValidationError(
            "accepted-row selector/live/model guard or model snapshot ordering changed"
        )
    log_paths = [
        line.removeprefix("(LOGAPPEND,").removesuffix(")")
        for line in core
        if line.startswith("(LOGAPPEND,")
    ]
    if log_paths != [str(RESULTS), str(STATE), str(MODEL_STATE)]:
        raise ValidationError("accepted-row result/state/model log ordering changed")
    first_log = next(index for index, line in enumerate(core) if line.startswith("(LOGAPPEND,"))
    if core[first_log - 2:first_log] != [
        "#726 = [#726 + 1.0]",
        "#788 = [#788 + 1.0]",
    ]:
        raise ValidationError("accepted-row counters are not immediately before first log")
    model_log = core.index(f"(LOGAPPEND,{MODEL_STATE})")
    if core[model_log - 1] != "#977 = [#977 + 1.0]":
        raise ValidationError("model-state counter is not immediately before model log")


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


def validate_program_text(text: str, canonical: str, safety: str) -> None:
    lines = text.splitlines()
    if max((len(line) for line in lines), default=0) > 256:
        longest = max(range(len(lines)), key=lambda index: len(lines[index])) + 1
        raise ValidationError(
            f"runner line {longest} is {len(lines[longest - 1])} chars; limit is 256"
        )
    required_identity = (
        "#711 = 33.0",
        "#715 = 2026082602.0",
        "#716 = 1.0",
        "#727 = 1.0",
        "#516 = 128.606729",
        "#717 = 0.117658",
        "#3032 = #717",
        "#707 = 31.0",
        "#739 = 1.0",
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
    validate_preview_and_prem0_boundary(text)
    validate_accepted_row_boundary(text)

    expected_paths = {str(path) for path in OUTPUT_FIELDS}
    logged_paths = re.findall(r"\(LOGAPPEND,([^\r\n)]+)\)", text)
    if len(logged_paths) != 6 or set(logged_paths) != expected_paths:
        raise ValidationError("runner LOGAPPEND paths differ from the six dedicated outputs")
    if any(logged_paths.count(path) != 1 for path in expected_paths):
        raise ValidationError("a dedicated runner output path is not logged exactly once")

    forbidden_residue = (
        "#711 = 32.0",
        "#716 = 2.0",
        "#727 = 2.0",
        "#707 = 101.0",
        "#973 - 808.0",
        "tcpc-length-aware-t4-validation-2026082601-attempt2",
    )
    for snippet in forbidden_residue:
        if snippet in text:
            raise ValidationError(f"runner retains T4/101/808 residue {snippet!r}")

    for name in (
        "tcpc_primary_outer_reference",
        "tcpc_primary_b0_sweep",
        "tcpc_primary_tilt_block",
        "tcpc_baseline_return_top_clear",
    ):
        if subroutine_text(text, name) != subroutine_text(canonical, name):
            raise ValidationError(f"runner changed canonical motion/grid subroutine {name}")
    for name in (
        "tcpc_pair_coordinate_guard",
        "tcpc_pair_hold_position_guard",
        "tcpc_pair_selector_guard",
        "tcpc_pair_live_guard",
        "tcpc_pair_release_guard",
        "tcpc_probe_counter_guard",
        "tcpc_contact_trace_begin",
        "tcpc_contact_trace_post",
        "tcpc_pair_probe_final_guard",
        "tcpc_pair_probe_ready_guard",
        "tcpc_vector_sphere_pass4",
        "tcpc_primary_tilt_block",
        "tcpc_baseline_return_top_clear",
    ):
        if subroutine_text(text, name) != subroutine_text(safety, name):
            raise ValidationError(f"runner changed sealed Attempt-2 safety subroutine {name}")
    if grid_body_fragment(text) != grid_body_fragment(canonical):
        raise ValidationError("runner changed the canonical 31-pose/14-closure body")
    if len(EXPECTED) != EXPECTED_ROWS or len(campaign.T3_CLOSURES) != EXPECTED_CLOSURES:
        raise ValidationError("imported canonical grid/topology is not 31 rows/14 closures")
    exact_closures = (
        (100, 1, 5), (45, 6, 10), (-45, 11, 15), (905, 5, 16),
        (90, 17, 21), (-90, 22, 26), (911, 1, 27), (906, 16, 27),
        (912, 2, 28), (913, 3, 29), (914, 4, 30), (915, 5, 31),
        (200, 27, 31), (900, 1, 31),
    )
    if campaign.T3_CLOSURES != exact_closures:
        raise ValidationError("imported T3 closure mapping changed")

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
        "o<trace_exact_count> if",
    )
    for snippet in required_guards:
        if snippet not in text:
            raise ValidationError(f"runner is missing guard/log contract {snippet!r}")
    exact_count_guards = (
        "o<primary_sequence_complete> if [[ABS[#726 - #707] GT 0.000001] OR [ABS[#788 - #707] GT 0.000001]]",
        "o<model_state_sequence_complete> if [ABS[#977 - #707] GT 0.000001]",
        "o<closure_sequence_complete> if [ABS[#978 - 14.0] GT 0.000001]",
        "o<trace_pair_count> if [ABS[#973 - #974] GT 0.000001]",
        "o<trace_exact_count> if [ABS[#973 - 248.0] GT 0.000001]",
    )
    for exact_guard in exact_count_guards:
        if text.count(exact_guard) != 1:
            raise ValidationError(f"runner runtime count guard changed for {exact_guard!r}")
    exact_trace_count = "o<trace_exact_count> if [ABS[#973 - 248.0] GT 0.000001]"
    if text.count(exact_trace_count) != 1:
        raise ValidationError("runner no longer enforces exactly 248 transactions")
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

    trace_finish = subroutine_text(text, "tcpc_contact_trace_finish")
    required_trace_contract = (
        "o<trace_retrigger_burst> if [[#969 LT 0.0] OR [#969 GT 2.0]]",
        "o<trace_success_counter_consistency> if [#929 GT 0.5]",
        "o<trace_success_direct_raw_mux> if [ABS[#963 - #964] GT 0.000001]",
        "o<trace_success_raw_edge_present> if [#963 LT 1.0]",
        "o<trace_success_repeat_raw_mux> if [ABS[#966 - #967] GT 0.000001]",
        "o<trace_success_total_raw_mux> if [ABS[#<trace_total_raw> - #<trace_total_mux>] GT 0.000001]",
        "o<trace_success_extra_bound> if [[#969 LT 0.0] OR [#969 GT 2.0]]",
        "o<trace_success_one_gated_edge> if [ABS[#965 - 1.0] GT 0.000001]",
        "o<trace_success_no_gated_repeat> if [ABS[#968] GT 0.000001]",
        "o<trace_release_fault_abort> if [#971 GT 0.5]",
        "o<trace_success_consistency_abort> if [[[#962 GT 0.5] OR [#936 GT 0.5]] AND [#970 LT 0.5]]",
    )
    for snippet in required_trace_contract:
        if trace_finish.count(snippet) != 1:
            raise ValidationError(f"bounded duplicate-pulse contract changed for {snippet!r}")
    if "trace_success_one_raw_edge" in trace_finish or "trace_success_one_mux_edge" in trace_finish:
        raise ValidationError("runner restored the obsolete exact-one raw/mux rule")

    trace_begin = subroutine_text(text, "tcpc_contact_trace_begin")
    required_gap_contract = (
        "o<trace_gap_retrigger_burst> if [[#959 LT 0.0] OR [#959 GT 2.0]]",
        "o<trace_gap_counter_consistency> if [[ABS[#956 - #957] GT 0.000001] OR [ABS[#958] GT 0.000001]]",
        "o<trace_initial_baseline_quiet> if [[#955 GT 0.5] AND [[ABS[#956] GT 0.000001] OR [ABS[#957] GT 0.000001] OR [ABS[#958] GT 0.000001]]]",
        "o<trace_gap_pre_g38_fault> if [[#960 GT 0.5] OR [#961 GT 0.5]]",
    )
    for snippet in required_gap_contract:
        if trace_begin.count(snippet) != 1:
            raise ValidationError(f"bounded inter-contact pulse contract changed for {snippet!r}")


def validate_program() -> None:
    require_hash(PROGRAM, SEALED_SHA256[PROGRAM])
    text = PROGRAM.read_text(encoding="ascii")
    canonical = CANONICAL_PROGRAM.read_text(encoding="ascii")
    safety = SAFETY_PROGRAM.read_text(encoding="ascii")
    validate_program_text(text, canonical, safety)
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
    validate_t4_completion_evidence()


def read_t4_completion_entries() -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(
        T4_COMPLETION_MANIFEST.read_text(encoding="ascii").splitlines(), 1
    ):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/]+)", line)
        if match is None:
            raise ValidationError(
                f"T4 completion manifest line {line_number} is malformed"
            )
        name = match.group(2)
        if (
            name in entries
            or name in {".", "..", T4_COMPLETION_MANIFEST.name}
            or Path(name).is_absolute()
            or Path(name).name != name
        ):
            raise ValidationError(
                f"T4 completion manifest line {line_number} has an unsafe or "
                f"duplicate member name"
            )
        entries[name] = match.group(1)
    return entries


def require_t4_completion_entries(entries: dict[str, str]) -> None:
    for name, digest in T4_REQUIRED_MEMBER_SHA256.items():
        if entries.get(name) != digest:
            raise ValidationError(f"T4 completion manifest does not own sealed {name}")


def validate_t4_archive_inventory(entries: dict[str, str]) -> None:
    actual: set[str] = set()
    for member in T4_COMPLETION_ARCHIVE.iterdir():
        if member.is_symlink():
            raise ValidationError(f"T4 completion archive contains symlink {member.name}")
        if not member.is_file():
            raise ValidationError(
                f"T4 completion archive contains non-file member {member.name}"
            )
        actual.add(member.name)
    expected = set(entries) | {T4_COMPLETION_MANIFEST.name}
    missing = sorted(expected - actual)
    surplus = sorted(actual - expected)
    if missing or surplus:
        raise ValidationError(
            f"T4 completion archive inventory mismatch; missing={missing}, "
            f"surplus={surplus}"
        )
    for name, digest in entries.items():
        member = T4_COMPLETION_ARCHIVE / name
        if sha256(member) != digest:
            raise ValidationError(f"T4 completion member changed: {name}")


def validate_t4_completion_evidence() -> None:
    entries = read_t4_completion_entries()
    require_t4_completion_entries(entries)
    validate_t4_archive_inventory(entries)
    shared_current = {
        "headheadkins.c": KINS_SOURCE,
        "headheadkins.so": KINS_MODULE,
        "tcpc_probe_attempt3_edge_counters.hal": PROBE_COUNTER_HAL,
    }
    for name, current in shared_current.items():
        if sha256(current) != entries[name]:
            raise ValidationError(
                f"current {current.relative_to(REPO_ROOT)} differs from T4 evidence"
            )
    report = T4_COMPLETION_REPORT.read_text(encoding="ascii")
    required_report_lines = (
        "Status: `PASS`",
        "- campaign / mode / attempt: `2026082602 / 32 / 2`",
        "- exact rows: `101` results, `101` state, `101` model-state",
        "- transaction traces: `808` contact / `808` gap",
        "- equal-unique-76 centered RMS / max: `0.107589 / 0.241710 mm`",
    )
    for line in required_report_lines:
        if report.count(line) != 1:
            raise ValidationError(f"T4 completion PASS evidence changed for {line!r}")


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


def active_controller_processes() -> list[str]:
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
            continue
        try:
            raw_cmdline = (entry / "cmdline").read_bytes()
            arguments = [
                value.decode("utf-8", errors="replace")
                for value in raw_cmdline.split(b"\0")
                if value
            ]
        except OSError:
            continue
        argument_names = {
            Path(argument).name.lower() for argument in arguments if argument
        }
        exact_arguments = {argument.lower() for argument in arguments}
        matched = sorted(
            live_names & (argument_names | exact_arguments)
        )
        if matched:
            active.append(f"{entry.name}:cmdline:{','.join(matched)}")
    return sorted(active)


def require_controller_off(stage: str) -> None:
    if os.path.lexists(LINUXCNC_LOCK):
        raise ValidationError(
            f"refusing standalone rs274 while LinuxCNC lock exists at {stage}: "
            f"{LINUXCNC_LOCK}"
        )
    active = active_controller_processes()
    if active:
        raise ValidationError(
            f"refusing standalone rs274 while controller processes are active "
            f"at {stage}: " + ", ".join(active)
        )


def run_rs274_preview() -> None:
    require_controller_off("initial check")
    with tempfile.TemporaryDirectory(prefix="tcpc-length-aware-rs274-") as isolated_home:
        env = os.environ.copy()
        env["HOME"] = isolated_home
        require_controller_off("immediate pre-launch check")
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
    require_controller_off("post-preview check")
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
            f"expected {EXPECTED_ROWS} result/state rows, got "
            f"{len(results)}/{len(states)}"
        )
    result_seq = [exact_int(row, "sample_seq", positive=True) for row in results]
    state_seq = [exact_int(row, "sample_seq", positive=True) for row in states]
    exact_sequence = list(range(1, EXPECTED_ROWS + 1))
    if result_seq != exact_sequence or state_seq != exact_sequence:
        raise ValidationError(
            f"result/state rows are not the exact ordered 1..{EXPECTED_ROWS} sequence"
        )

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
        raise ValidationError(
            f"closure validator did not return exactly {EXPECTED_CLOSURES} closures"
        )
    return centers, closure_norms


def expected_surface_vector(
    b_deg: float, c_deg: float, surface: str
) -> np.ndarray:
    basis = bounds.basis_values(b_deg, np.asarray([c_deg], dtype=float))
    coefficients = bounds.surface_coefficients(TOOL_LENGTH_MM)[surface]
    return bounds.evaluate_surface(basis, coefficients)[0]


def expected_diff_vector(b_deg: float, c_deg: float) -> np.ndarray:
    return expected_surface_vector(b_deg, c_deg, "length_bank")


def expected_incremental_vector(b_deg: float, c_deg: float) -> np.ndarray:
    return expected_surface_vector(b_deg, c_deg, "incremental")


def expected_empirical_vector(b_deg: float, c_deg: float) -> np.ndarray:
    return expected_surface_vector(b_deg, c_deg, "total")


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
    anchor.near(row, "q", 1.0, 1e-6)
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
    if diff_norm < 0.0:
        raise ValidationError(f"model-state seq {seq}: negative differential norm")
    if abs(diff_norm - float(np.linalg.norm(diff))) > 3e-6 or diff_norm > DIFF_CAP_MM:
        raise ValidationError(f"model-state seq {seq}: differential norm/cap mismatch")
    offline_diff = expected_diff_vector(expected.pose.b_deg, expected.pose.c_deg)
    if float(np.linalg.norm(diff - offline_diff)) > 2e-5:
        raise ValidationError(
            f"model-state seq {seq}: differential vector differs from sealed q=1 D bank"
        )

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
            f"model-state seq {seq}: empirical vector differs from sealed H0+S+D model"
        )


def validate_model_states() -> None:
    rows = read_rows(MODEL_STATE, MODEL_STATE_FIELDS)
    if len(rows) != EXPECTED_ROWS:
        raise ValidationError(
            f"expected {EXPECTED_ROWS} model-state rows, got {len(rows)}"
        )
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


def validate_contact_trace_row(
    row: dict[str, str], key: tuple[int, int, int, int]
) -> None:
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
    total = tuple(ready[i] - pre[i] for i in range(3))
    for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
        if exact_int(row, field) != value:
            raise ValidationError(f"contact trace seq {seq}: {field} mismatch")
    for field, value in zip(
        ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats
    ):
        if exact_int(row, field) != value:
            raise ValidationError(f"contact trace seq {seq}: {field} mismatch")

    if direct[0] != direct[1] or direct[0] < 1 or direct[2] != 1:
        raise ValidationError(f"contact trace seq {seq}: G38 raw/mux/gated edge failure")
    if repeats[0] != repeats[1] or repeats[2] != 0:
        raise ValidationError(f"contact trace seq {seq}: repeat-edge consistency failure")
    if total[0] != total[1]:
        raise ValidationError(f"contact trace seq {seq}: total raw/mux edge mismatch")

    extra = total[0] - total[2]
    if exact_int(row, "extra_raw_minus_gated_delta") != extra:
        raise ValidationError(f"contact trace seq {seq}: extra-edge delta mismatch")
    if extra < 0 or extra > MAX_FILTERED_EXTRA_EDGES:
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


def validate_contact_traces() -> list[dict[str, str]]:
    rows = read_rows(CONTACT_TRACE, CONTACT_TRACE_FIELDS)
    if len(rows) != EXPECTED_TRANSACTIONS:
        raise ValidationError(
            f"expected exactly {EXPECTED_TRANSACTIONS} contact traces, got {len(rows)}"
        )
    keys = [trace_key(row, "global_seq") for row in rows]
    if keys != expected_transaction_keys():
        raise ValidationError("contact traces are not exact try1/pass1-2/contact1-4 order")
    for row, key in zip(rows, keys):
        validate_contact_trace_row(row, key)
    return rows


def validate_gap_trace_row(
    gap: dict[str, str],
    contact: dict[str, str],
    previous_contact: dict[str, str] | None,
    index: int,
    key: tuple[int, int, int, int],
) -> None:
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
    if combined < 0 or combined > MAX_FILTERED_EXTRA_EDGES or consistency:
        raise ValidationError(f"gap trace seq {seq}: electrical gate failure")
    for field in ("burst_flag", "consistency_fault"):
        if exact_int(gap, field) != 0:
            raise ValidationError(f"gap trace seq {seq}: {field} is nonzero")


def validate_gap_traces(
    contacts: Sequence[dict[str, str]]
) -> list[dict[str, str]]:
    rows = read_rows(GAP_TRACE, GAP_TRACE_FIELDS)
    if len(rows) != EXPECTED_TRANSACTIONS:
        raise ValidationError(
            f"expected exactly {EXPECTED_TRANSACTIONS} gap traces, got {len(rows)}"
        )
    keys = [trace_key(row, "next_global_seq") for row in rows]
    if keys != expected_transaction_keys():
        raise ValidationError("gap traces are not exact try1/pass1-2/contact1-4 order")
    previous_contact: dict[str, str] | None = None
    for index, (gap, contact, key) in enumerate(zip(rows, contacts, keys)):
        validate_gap_trace_row(gap, contact, previous_contact, index, key)
        previous_contact = contact
    return rows


def centered_residual_norms(values: np.ndarray) -> np.ndarray:
    if values.ndim != 2 or values.shape[1] != 3 or len(values) < 1:
        raise ValidationError("center metric requires a nonempty N-by-3 array")
    residuals = values - np.mean(values, axis=0)
    return np.linalg.norm(residuals, axis=1)


def centered_metric(values: np.ndarray) -> tuple[float, float]:
    norms = centered_residual_norms(values)
    return float(math.sqrt(np.mean(norms * norms))), float(np.max(norms))


def pose_key(expected: campaign.ExpectedRow) -> tuple[float, float]:
    return (
        round(expected.pose.b_deg, 9),
        round(expected.pose.c_deg % 360.0, 9),
    )


def unique_center_array(
    centers: dict[int, np.ndarray],
) -> tuple[tuple[tuple[float, float], ...], np.ndarray]:
    groups: dict[tuple[float, float], list[np.ndarray]] = {}
    for expected in EXPECTED:
        groups.setdefault(pose_key(expected), []).append(centers[expected.seq])
    if len(groups) != EXPECTED_UNIQUE_POSES:
        raise ValidationError(
            f"expected exactly {EXPECTED_UNIQUE_POSES} unique poses, got {len(groups)}"
        )
    keys = tuple(groups)
    values = np.vstack(
        [np.mean(np.vstack(group), axis=0) for group in groups.values()]
    )
    return keys, values


def require_metric_improvement(
    label: str,
    actual_rms: float,
    actual_max: float,
    h0_rms: float,
    h0_max: float,
) -> None:
    rms_gate = min(
        RMS_IMPROVEMENT_FRACTION * h0_rms,
        h0_rms - RMS_IMPROVEMENT_MIN_MM,
    )
    max_gate = min(
        MAX_IMPROVEMENT_FRACTION * h0_max,
        h0_max - MAX_IMPROVEMENT_MIN_MM,
    )
    if actual_rms > rms_gate + 1e-12:
        raise ValidationError(
            f"{label} RMS {actual_rms:.6f} mm does not improve same-acquisition "
            f"H0 {h0_rms:.6f} mm through gate {rms_gate:.6f} mm"
        )
    if actual_max > max_gate + 1e-12:
        raise ValidationError(
            f"{label} max {actual_max:.6f} mm does not improve same-acquisition "
            f"H0 {h0_max:.6f} mm through gate {max_gate:.6f} mm"
        )


def require_absolute_metric(label: str, rms: float, maximum: float) -> None:
    if rms > RMS_LIMIT_MM + 1e-12 or maximum > MAX_LIMIT_MM + 1e-12:
        raise ValidationError(
            f"{label} centered RMS/max {rms:.6f}/{maximum:.6f} mm exceeds "
            f"{RMS_LIMIT_MM:.3f}/{MAX_LIMIT_MM:.3f} mm"
        )


def require_sign_rms_improvement(label: str, current_rms: float, h0_rms: float) -> None:
    if current_rms > RMS_IMPROVEMENT_FRACTION * h0_rms + 1e-12:
        raise ValidationError(
            f"{label} unique RMS {current_rms:.6f} mm does not improve "
            f"same-acquisition H0 {h0_rms:.6f} mm by at least 10%"
        )


def require_b0_rms_worsening(current_rms: float, h0_rms: float) -> None:
    if current_rms > h0_rms + B0_RMS_WORSENING_LIMIT_MM + 1e-12:
        raise ValidationError(
            f"B0 unique RMS worsens by {current_rms - h0_rms:.6f} mm; "
            f"limit is {B0_RMS_WORSENING_LIMIT_MM:.3f} mm"
        )


def require_pose_worsening(
    keys: Sequence[tuple[float, float]],
    current_norms: np.ndarray,
    h0_norms: np.ndarray,
) -> float:
    pose_worsenings = current_norms - h0_norms
    maximum_pose_worsening = float(np.max(pose_worsenings))
    if maximum_pose_worsening > POSE_WORSENING_LIMIT_MM + 1e-12:
        worst_index = int(np.argmax(pose_worsenings))
        raise ValidationError(
            f"unique pose {keys[worst_index]} centered norm worsens by "
            f"{maximum_pose_worsening:.6f} mm; limit is "
            f"{POSE_WORSENING_LIMIT_MM:.3f} mm"
        )
    return maximum_pose_worsening


def sign_subgroup_rms(
    keys: Sequence[tuple[float, float]], residuals: np.ndarray, sign: int
) -> float:
    indices = [
        index
        for index, (b_deg, _) in enumerate(keys)
        if (b_deg > 0.0 and sign > 0) or (b_deg < 0.0 and sign < 0)
    ]
    if len(indices) != 8:
        raise ValidationError(
            f"T3 sign subgroup {sign:+d} has {len(indices)} poses, expected 8"
        )
    norms = np.linalg.norm(residuals[indices], axis=1)
    return float(math.sqrt(np.mean(norms * norms)))


def center_metrics(centers: dict[int, np.ndarray]) -> dict[str, float]:
    raw = np.vstack([centers[seq] for seq in range(1, EXPECTED_ROWS + 1)])
    h0_centers: dict[int, np.ndarray] = {}
    for expected in EXPECTED:
        h0_centers[expected.seq] = centers[expected.seq] - expected_incremental_vector(
            expected.pose.b_deg, expected.pose.c_deg
        )
    raw_h0 = np.vstack(
        [h0_centers[seq] for seq in range(1, EXPECTED_ROWS + 1)]
    )
    keys, unique = unique_center_array(centers)
    h0_keys, unique_h0 = unique_center_array(h0_centers)
    if keys != h0_keys:
        raise ValidationError("current and reconstructed-H0 unique pose order differs")

    raw_rms, raw_max = centered_metric(raw)
    unique_rms, unique_max = centered_metric(unique)
    raw_h0_rms, raw_h0_max = centered_metric(raw_h0)
    unique_h0_rms, unique_h0_max = centered_metric(unique_h0)
    unique_residuals = unique - np.mean(unique, axis=0)
    unique_h0_residuals = unique_h0 - np.mean(unique_h0, axis=0)
    for label, rms, maximum in (
        ("raw", raw_rms, raw_max),
        ("equal-unique", unique_rms, unique_max),
    ):
        require_absolute_metric(label, rms, maximum)

    require_metric_improvement(
        "raw", raw_rms, raw_max, raw_h0_rms, raw_h0_max
    )
    require_metric_improvement(
        "equal-unique", unique_rms, unique_max, unique_h0_rms, unique_h0_max
    )

    subgroup_metrics: dict[str, float] = {}
    for name, sign in (("positive_b", 1), ("negative_b", -1)):
        current_rms = sign_subgroup_rms(keys, unique_residuals, sign)
        h0_rms = sign_subgroup_rms(keys, unique_h0_residuals, sign)
        require_sign_rms_improvement(name, current_rms, h0_rms)
        subgroup_metrics[f"{name}_rms"] = current_rms
        subgroup_metrics[f"{name}_h0_rms"] = h0_rms

    b0_indices = [index for index, key in enumerate(keys) if key[0] == 0.0]
    if len(b0_indices) != 4:
        raise ValidationError(f"T3 B0 unique subgroup has {len(b0_indices)} poses, expected 4")
    b0_norms = np.linalg.norm(unique_residuals[b0_indices], axis=1)
    b0_h0_norms = np.linalg.norm(unique_h0_residuals[b0_indices], axis=1)
    b0_rms = float(math.sqrt(np.mean(b0_norms * b0_norms)))
    b0_h0_rms = float(math.sqrt(np.mean(b0_h0_norms * b0_h0_norms)))
    require_b0_rms_worsening(b0_rms, b0_h0_rms)

    maximum_pose_worsening = require_pose_worsening(
        keys,
        np.linalg.norm(unique_residuals, axis=1),
        np.linalg.norm(unique_h0_residuals, axis=1),
    )

    return {
        "raw_count": float(len(raw)),
        "unique_count": float(len(unique)),
        "raw_rms": raw_rms,
        "raw_max": raw_max,
        "unique_rms": unique_rms,
        "unique_max": unique_max,
        "raw_h0_rms": raw_h0_rms,
        "raw_h0_max": raw_h0_max,
        "unique_h0_rms": unique_h0_rms,
        "unique_h0_max": unique_h0_max,
        "b0_rms": b0_rms,
        "b0_h0_rms": b0_h0_rms,
        "maximum_pose_worsening": maximum_pose_worsening,
        **subgroup_metrics,
    }


def trace_diagnostics(
    contacts: Sequence[dict[str, str]], gaps: Sequence[dict[str, str]]
) -> dict[str, int]:
    contact_extras = [
        exact_int(row, "extra_raw_minus_gated_delta") for row in contacts
    ]
    gap_extras = [exact_int(row, "gap_raw_delta") for row in gaps]
    combined_extras = [exact_int(row, "combined_extra_delta") for row in gaps]
    return {
        "direct_duplicate_transactions": sum(
            exact_int(row, "raw_delta") > 1 for row in contacts
        ),
        "repeat_extra_transactions": sum(
            exact_int(row, "repeat_raw_delta") > 0 for row in contacts
        ),
        "contact_extra_transactions": sum(value > 0 for value in contact_extras),
        "contact_extra_edges": sum(contact_extras),
        "gap_extra_transactions": sum(value > 0 for value in gap_extras),
        "gap_extra_edges": sum(gap_extras),
        "maximum_contact_extra": max(contact_extras, default=0),
        "maximum_combined_extra": max(contact_extras + combined_extras, default=0),
    }


def validate_completed_run() -> tuple[dict[str, float], np.ndarray, dict[str, int]]:
    offline_contract(header_only=False)
    centers, closure_norms = validate_results_state_closures()
    validate_model_states()
    contacts = validate_contact_traces()
    gaps = validate_gap_traces(contacts)
    return center_metrics(centers), closure_norms, trace_diagnostics(contacts, gaps)


def write_preflight_report(path: Path) -> None:
    lines = [
        "# TCPC Length-Aware T3 Validation Preflight",
        "",
        "Status: `PASS`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- model ID: `{MODEL_ID}`",
        f"- probe: `T3 / H3 / {TOOL_LENGTH_MM:.6f} mm / #3032={PROBE_OFFSET_MM:.6f}`",
        f"- canonical acquisition: `{EXPECTED_ROWS}` result/state/model-state rows, "
        f"`{EXPECTED_CLOSURES}` closures, `{EXPECTED_TRANSACTIONS}` contact and gap traces",
        "- parser: standalone in-tree `bin/rs274 -g` passed under an isolated temporary HOME",
        "- controller-process gate: no LinuxCNC, linuxcncsvr, milltask, rtapi_app, Probe Basic, or QtPyVCP process was active, and /tmp/linuxcnc.lock was absent",
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
            "The frozen runner has one initial M0, no M1, no long dwell, no whole-pose retry, no direct HAL or coefficient mutation, and only its reviewed deassert-only M65 P0/P1 safety clears. The canonical 31-pose/14-closure T3 grid, sealed T3 motion subroutines, sealed Attempt-2 safety subroutines, every G38 transaction layer, model/live/final guards, exact 31/14/248 runtime guards, and six isolated LOGAPPEND destinations passed static and mutation checks.",
            "",
            "The bounded duplicate-pulse rule accepts at most two matched raw/mux extras only when G38 succeeds, exactly one gated edge reaches motion, no gated repeat occurs, and the probe passes the two-sample release guard. All extras remain visible in the trace outputs.",
            "",
            "The deterministic full-length-domain model audit passed. Every model row is required to match `q=1`, the offline differential D vector, and the total H0+S+D vector. The independent historical synthetic check reproduces the documented H0 and candidate metrics and proves the same-acquisition reconstruction sign without using consumed data for runtime acceptance.",
            "",
            "The immutable T4 completion manifest and archived formal PASS report were verified. Every manifest entry matches its archive member; no member is missing, surplus, nested, or symlinked. Semantic checks additionally require ownership and hashes of the runner, validator, completed results, kinematics source, compiled kinematics module, and probe-counter HAL. The current source/module/probe-counter artifacts exactly match those archived T4 members. T3 is therefore gated on the accepted physical q=0 endpoint and the same implementation/safety dependencies, rather than code provenance alone.",
            "",
            "Runtime acceptance requires raw-31 and equal-20 RMS/max at or below 0.120/0.280 mm, the prescribed relative and absolute improvements against reconstructed same-acquisition H0, at least 10% RMS improvement for both B signs on globally centered equal-20 residuals, B0 RMS worsening no greater than 0.010 mm on those same residuals, and no unique-pose centered-norm worsening above 0.050 mm.",
            "Targeted rejection fixtures exercise raw and equal absolute RMS/max ceilings, both branches of every relative/fixed-minimum improvement gate, positive-B, negative-B, B0, and single-pose worsening boundaries. Result/state/closure schema and geometry validation remains delegated to the sealed imported campaign analyzers.",
            "",
            "A passing acquisition validates the physical T3 endpoint and the T3-to-T4 evidence bracket. It does not validate extrapolation to tools outside that bracket.",
            "",
            "This validator imports neither LinuxCNC nor HAL and issues no machine-control command.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")


def write_result_report(
    path: Path,
    metrics: dict[str, float],
    closure_norms: np.ndarray,
    diagnostics: dict[str, int],
) -> None:
    lines = [
        "# TCPC Length-Aware T3 Validation Result",
        "",
        "Status: `PASS`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- exact rows: `{EXPECTED_ROWS}` results, `{EXPECTED_ROWS}` state, `{EXPECTED_ROWS}` model-state",
        f"- closures: `{len(closure_norms)}`; worst `{float(np.max(closure_norms)):.6f} mm`",
        f"- transaction traces: `{EXPECTED_TRANSACTIONS}` contact / `{EXPECTED_TRANSACTIONS}` gap",
        f"- direct duplicate transactions: `{diagnostics['direct_duplicate_transactions']}`",
        f"- delayed/repeat extra transactions: `{diagnostics['repeat_extra_transactions']}`",
        f"- contact-window filtered extras: `{diagnostics['contact_extra_transactions']}` transactions / `{diagnostics['contact_extra_edges']}` edges",
        f"- inter-contact filtered extras: `{diagnostics['gap_extra_transactions']}` transactions / `{diagnostics['gap_extra_edges']}` edges",
        f"- maximum contact-window filtered extras: `{diagnostics['maximum_contact_extra']} / {MAX_FILTERED_EXTRA_EDGES}`",
        f"- maximum combined filtered extras: `{diagnostics['maximum_combined_extra']} / {MAX_FILTERED_EXTRA_EDGES}`",
        f"- raw-{int(metrics['raw_count'])} centered RMS / max: `{metrics['raw_rms']:.6f} / {metrics['raw_max']:.6f} mm`",
        f"- equal-unique-{int(metrics['unique_count'])} centered RMS / max: `{metrics['unique_rms']:.6f} / {metrics['unique_max']:.6f} mm`",
        f"- reconstructed H0 raw centered RMS / max: `{metrics['raw_h0_rms']:.6f} / {metrics['raw_h0_max']:.6f} mm`",
        f"- reconstructed H0 equal-unique centered RMS / max: `{metrics['unique_h0_rms']:.6f} / {metrics['unique_h0_max']:.6f} mm`",
        f"- positive-B unique RMS current / H0: `{metrics['positive_b_rms']:.6f} / {metrics['positive_b_h0_rms']:.6f} mm`",
        f"- negative-B unique RMS current / H0: `{metrics['negative_b_rms']:.6f} / {metrics['negative_b_h0_rms']:.6f} mm`",
        f"- B0 unique RMS current / H0: `{metrics['b0_rms']:.6f} / {metrics['b0_h0_rms']:.6f} mm`",
        f"- maximum single unique-pose centered-norm worsening: `{metrics['maximum_pose_worsening']:.6f} mm`",
        f"- acceptance limits: RMS `<={RMS_LIMIT_MM:.3f} mm`, max `<={MAX_LIMIT_MM:.3f} mm`",
        "",
        "All identities, poses, T3 tool/TLO values, q=1 model snapshots, differential and total model vectors/norms/caps, transaction counters/flags, closure mappings, absolute score limits, and same-acquisition H0 improvement gates passed.",
        "",
        "This T3 acquisition validates the short-probe differential endpoint. Together with the completed T4 q=0 acquisition it supports only the tested T3-to-T4 tool-length bracket, not extrapolated tool lengths.",
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
    diff = expected_diff_vector(expected.pose.b_deg, expected.pose.c_deg)
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
        q="1",
        evaluated_b_deg=f"{expected.pose.b_deg:.9f}",
        evaluated_c_deg=f"{expected.pose.c_deg:.9f}",
        evaluated_length_mm=f"{TOOL_LENGTH_MM:.9f}",
        diff_offset_x_mm=f"{diff[0]:.9f}",
        diff_offset_y_mm=f"{diff[1]:.9f}",
        diff_offset_z_mm=f"{diff[2]:.9f}",
        diff_offset_norm_mm=f"{np.linalg.norm(diff):.9f}",
        empirical_offset_x_mm=f"{empirical[0]:.9f}",
        empirical_offset_y_mm=f"{empirical[1]:.9f}",
        empirical_offset_z_mm=f"{empirical[2]:.9f}",
        empirical_offset_norm_mm=f"{np.linalg.norm(empirical):.9f}",
    )
    return row


def synthetic_contact_row(
    *,
    direct: tuple[int, int, int] = (1, 1, 1),
    repeats: tuple[int, int, int] = (0, 0, 0),
    pre: tuple[int, int, int] = (100, 100, 100),
    probe_result: int = 1,
    burst_flag: int = 0,
    consistency_fault: int = 0,
    release_fault: int = 0,
    terminal_failure: int = 0,
) -> dict[str, str]:
    expected = EXPECTED_BY_SEQ[1]
    post = tuple(pre[index] + direct[index] for index in range(3))
    ready = tuple(post[index] + repeats[index] for index in range(3))
    extra = (ready[0] - pre[0]) - (ready[2] - pre[2])
    row = {field: "0" for field in CONTACT_TRACE_FIELDS}
    row.update(
        schema_version="1",
        campaign_id=str(CAMPAIGN),
        stage_mode=str(MODE),
        attempt_id=str(ATTEMPT),
        global_seq="1",
        abs_b_deg=f"{expected.pose.b_deg:.9f}",
        abs_c_deg=f"{expected.pose.c_deg:.9f}",
        acquisition_try="1",
        pass_id="1",
        contact_id="1",
        probe_result=str(probe_result),
        travel_mm="5.0",
        burst_flag=str(burst_flag),
        consistency_fault=str(consistency_fault),
        release_fault=str(release_fault),
        terminal_failure=str(terminal_failure),
        extra_raw_minus_gated_delta=str(extra),
    )
    for prefix, values in (("pre", pre), ("post", post), ("ready", ready)):
        for name, value in zip(("raw", "mux", "gated"), values):
            row[f"{prefix}_{name}_count"] = str(value)
    for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
        row[field] = str(value)
    for field, value in zip(
        ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats
    ):
        row[field] = str(value)
    return row


def synthetic_gap_row(
    contact: dict[str, str],
    *,
    previous_contact: dict[str, str] | None = None,
    gap_delta: tuple[int, int, int] = (0, 0, 0),
    burst_flag: int = 0,
    consistency_fault: int = 0,
) -> dict[str, str]:
    current = counter_tuple(contact, "pre")
    if previous_contact is None:
        prior = tuple(current[index] - gap_delta[index] for index in range(3))
        prior_extra = 0
        initial = 1
    else:
        prior = counter_tuple(previous_contact, "ready")
        prior_extra = exact_int(previous_contact, "extra_raw_minus_gated_delta")
        initial = 0
    combined = prior_extra + gap_delta[0] - gap_delta[2]
    row = {field: "0" for field in GAP_TRACE_FIELDS}
    row.update(
        schema_version="1",
        campaign_id=str(CAMPAIGN),
        stage_mode=str(MODE),
        attempt_id=str(ATTEMPT),
        next_global_seq=contact["global_seq"],
        abs_b_deg=contact["abs_b_deg"],
        abs_c_deg=contact["abs_c_deg"],
        acquisition_try=contact["acquisition_try"],
        pass_id=contact["pass_id"],
        contact_id=contact["contact_id"],
        prior_contact_extra_delta=str(prior_extra),
        combined_extra_delta=str(combined),
        burst_flag=str(burst_flag),
        consistency_fault=str(consistency_fault),
        initial_baseline=str(initial),
    )
    for prefix, values in (("prior_ready", prior), ("current_pre", current)):
        for name, value in zip(("raw", "mux", "gated"), values):
            row[f"{prefix}_{name}_count"] = str(value)
    for field, value in zip(
        ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"), gap_delta
    ):
        row[field] = str(value)
    return row


def historical_metric_formula_self_test() -> dict[int, np.ndarray]:
    # Historical consumed data is used only to prove the reconstruction sign and
    # metric implementation. Runtime acceptance reads only the fresh Attempt-1 files.
    import assess_tcpc_r3_feasibility as r3

    r3.self_test()
    historical_t3 = r3.calculate()[1]
    expected_keys = tuple(
        (int(round(expected.pose.b_deg)), int(round(expected.pose.c_deg % 360.0)))
        for expected in EXPECTED
    )
    if historical_t3.raw_keys != expected_keys:
        raise AssertionError("historical T3 raw pose order differs from frozen schedule")

    h0_raw = np.asarray(historical_t3.raw_centers, dtype=float)
    candidate_raw = np.vstack(
        [
            h0_raw[index]
            + expected_incremental_vector(
                expected.pose.b_deg, expected.pose.c_deg
            )
            for index, expected in enumerate(EXPECTED)
        ]
    )
    centers = {
        expected.seq: candidate_raw[index]
        for index, expected in enumerate(EXPECTED)
    }
    metrics = center_metrics(centers)
    expected_metrics = {
        "raw_h0_rms": 0.221010740,
        "raw_h0_max": 0.650679707,
        "raw_rms": 0.104775561,
        "raw_max": 0.226344480,
        "unique_h0_rms": 0.251154900,
        "unique_h0_max": 0.617559442,
        "unique_rms": 0.099481386,
        "unique_max": 0.206611915,
        "positive_b_h0_rms": 0.207278246,
        "positive_b_rms": 0.087507566,
        "negative_b_h0_rms": 0.321714766,
        "negative_b_rms": 0.107266951,
        "b0_h0_rms": 0.149881940,
        "b0_rms": 0.105618113,
        "maximum_pose_worsening": -0.001846927,
    }
    for field, expected_value in expected_metrics.items():
        if not math.isclose(metrics[field], expected_value, abs_tol=5e-9):
            raise AssertionError(
                f"historical formula check {field}={metrics[field]:.9f}, "
                f"expected {expected_value:.9f}"
            )

    wrong_sign = {
        expected.seq: h0_raw[index]
        - expected_incremental_vector(expected.pose.b_deg, expected.pose.c_deg)
        for index, expected in enumerate(EXPECTED)
    }
    expect_failure("same-acquisition reconstruction sign", lambda: center_metrics(wrong_sign))
    return centers


def metric_gate_self_test() -> None:
    for label in ("raw", "equal-unique"):
        require_absolute_metric(label, RMS_LIMIT_MM, MAX_LIMIT_MM)
        expect_failure(
            f"{label} absolute RMS ceiling",
            lambda name=label: require_absolute_metric(
                name, RMS_LIMIT_MM + 1e-8, 0.0
            ),
        )
        expect_failure(
            f"{label} absolute max ceiling",
            lambda name=label: require_absolute_metric(
                name, 0.0, MAX_LIMIT_MM + 1e-8
            ),
        )

        # Use H0 values on opposite sides of each crossover so both the
        # fractional and fixed-minimum branches of min() are exercised.
        require_metric_improvement(label, 0.18, 0.36, 0.20, 0.40)
        expect_failure(
            f"{label} relative RMS improvement",
            lambda name=label: require_metric_improvement(
                name, 0.18 + 1e-8, 0.0, 0.20, 0.40
            ),
        )
        expect_failure(
            f"{label} absolute RMS improvement",
            lambda name=label: require_metric_improvement(
                name, 0.04 + 1e-8, 0.0, 0.05, 0.40
            ),
        )
        expect_failure(
            f"{label} relative max improvement",
            lambda name=label: require_metric_improvement(
                name, 0.0, 0.36 + 1e-8, 0.20, 0.40
            ),
        )
        expect_failure(
            f"{label} absolute max improvement",
            lambda name=label: require_metric_improvement(
                name, 0.0, 0.08 + 1e-8, 0.20, 0.10
            ),
        )

    for label in ("positive_b", "negative_b"):
        require_sign_rms_improvement(label, 0.09, 0.10)
        expect_failure(
            f"{label} 10 percent RMS improvement",
            lambda name=label: require_sign_rms_improvement(
                name, 0.09 + 1e-8, 0.10
            ),
        )

    require_b0_rms_worsening(0.11, 0.10)
    expect_failure(
        "B0 0.010 mm worsening",
        lambda: require_b0_rms_worsening(0.11 + 1e-8, 0.10),
    )
    keys = ((90.0, 180.0),)
    require_pose_worsening(keys, np.asarray([0.15]), np.asarray([0.10]))
    expect_failure(
        "unique-pose 0.050 mm worsening",
        lambda: require_pose_worsening(
            keys, np.asarray([0.15 + 1e-8]), np.asarray([0.10])
        ),
    )


def self_test() -> None:
    offline_contract(header_only=True)
    manifest_entries = read_t4_completion_entries()
    for member in (
        "headheadkins.c",
        "headheadkins.so",
        "tcpc_probe_attempt3_edge_counters.hal",
    ):
        mutated_entries = dict(manifest_entries)
        mutated_entries[member] = "0" * 64
        expect_failure(
            f"T4 completion ownership {member}",
            lambda entries=mutated_entries: require_t4_completion_entries(entries),
        )
    missing_inventory_entry = dict(manifest_entries)
    missing_inventory_entry.pop("CONFIG_README.md")
    expect_failure(
        "T4 completion surplus archive member",
        lambda: validate_t4_archive_inventory(missing_inventory_entry),
    )
    surplus_inventory_entry = dict(manifest_entries)
    surplus_inventory_entry["not-present-in-archive"] = "0" * 64
    expect_failure(
        "T4 completion missing archive member",
        lambda: validate_t4_archive_inventory(surplus_inventory_entry),
    )
    assert len(EXPECTED) == EXPECTED_ROWS
    assert len(campaign.T3_CLOSURES) == EXPECTED_CLOSURES
    assert len(expected_transaction_keys()) == EXPECTED_TRANSACTIONS
    assert len({
        (round(expected.pose.b_deg, 9), round(expected.pose.c_deg % 360.0, 9))
        for expected in EXPECTED
    }) == EXPECTED_UNIQUE_POSES

    text = PROGRAM.read_text(encoding="ascii")
    canonical = CANONICAL_PROGRAM.read_text(encoding="ascii")
    safety = SAFETY_PROGRAM.read_text(encoding="ascii")
    mutations = {
        "campaign": text.replace("#715 = 2026082602.0", "#715 = 2026082603.0", 1),
        "whole-pose retry": text.replace("#739 = 1.0", "#739 = 2.0", 1),
        "M0": text.replace("\nM0\n", "\n", 1),
        "preview exit": text.replace("  M2\n", "  (DEBUG, preview failed to exit)\n", 1),
        "pre-M0 motion": text.replace("\nM0\n", "\nG1 X0\nM0\n", 1),
        "pre-M0 combined modal motion": text.replace(
            "\nM0\n", "\nG90 G1 X0\nM0\n", 1
        ),
        "long dwell": text.replace("G4 P0.05", "G4 P20", 1),
        "output path": text.replace(
            f"(LOGAPPEND,{RESULTS})",
            f"(LOGAPPEND,{str(RESULTS).replace('attempt1', 'attempt999')})",
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
        "accepted guard order": text.replace(
            "o<tcpc_pair_selector_guard> call\n    o<tcpc_pair_live_guard> call [1.0] [#520] [#521]\n    o<tcpc_length_model_guard> call",
            "o<tcpc_pair_live_guard> call [1.0] [#520] [#521]\n    o<tcpc_pair_selector_guard> call\n    o<tcpc_length_model_guard> call",
            1,
        ),
        "accepted model snapshot": text.replace(
            "#989 = #<_hal[headheadkins.length-model.diff-offset.x]>",
            "#989 = #<_hal[headheadkins.length-model.diff-offset.y]>",
            1,
        ),
        "direct raw mux equality": text.replace(
            "o<trace_success_direct_raw_mux> if [ABS[#963 - #964] GT 0.000001]",
            "o<trace_success_direct_raw_mux> if [0.0]",
            1,
        ),
        "successful G38 branch": text.replace(
            "o<trace_success_counter_consistency> if [#929 GT 0.5]",
            "o<trace_success_counter_consistency> if [#929 GT 1.5]",
            1,
        ),
        "raw edge presence": text.replace(
            "o<trace_success_raw_edge_present> if [#963 LT 1.0]",
            "o<trace_success_raw_edge_present> if [#963 LT 0.0]",
            1,
        ),
        "repeat raw mux equality": text.replace(
            "o<trace_success_repeat_raw_mux> if [ABS[#966 - #967] GT 0.000001]",
            "o<trace_success_repeat_raw_mux> if [0.0]",
            1,
        ),
        "total raw mux equality": text.replace(
            "o<trace_success_total_raw_mux> if [ABS[#<trace_total_raw> - #<trace_total_mux>] GT 0.000001]",
            "o<trace_success_total_raw_mux> if [0.0]",
            1,
        ),
        "filtered extra bound": text.replace(
            "o<trace_success_extra_bound> if [[#969 LT 0.0] OR [#969 GT 2.0]]",
            "o<trace_success_extra_bound> if [[#969 LT 0.0] OR [#969 GT 3.0]]",
            1,
        ),
        "contact burst bound": text.replace(
            "o<trace_retrigger_burst> if [[#969 LT 0.0] OR [#969 GT 2.0]]",
            "o<trace_retrigger_burst> if [[#969 LT 0.0] OR [#969 GT 3.0]]",
            1,
        ),
        "single gated edge": text.replace(
            "o<trace_success_one_gated_edge> if [ABS[#965 - 1.0] GT 0.000001]",
            "o<trace_success_one_gated_edge> if [ABS[#965 - 2.0] GT 0.000001]",
            1,
        ),
        "no gated repeat": text.replace(
            "o<trace_success_no_gated_repeat> if [ABS[#968] GT 0.000001]",
            "o<trace_success_no_gated_repeat> if [ABS[#968] GT 1.000001]",
            1,
        ),
        "release abort": text.replace(
            "o<trace_release_fault_abort> if [#971 GT 0.5]",
            "o<trace_release_fault_abort> if [#971 GT 1.5]",
            1,
        ),
        "gap burst gate": text.replace(
            "o<trace_gap_pre_g38_fault> if [[#960 GT 0.5] OR [#961 GT 0.5]]",
            "o<trace_gap_pre_g38_fault> if [#961 GT 0.5]",
            1,
        ),
        "gap burst bound": text.replace(
            "o<trace_gap_retrigger_burst> if [[#959 LT 0.0] OR [#959 GT 2.0]]",
            "o<trace_gap_retrigger_burst> if [[#959 LT 0.0] OR [#959 GT 3.0]]",
            1,
        ),
        "gap counter consistency": text.replace(
            "o<trace_gap_counter_consistency> if [[ABS[#956 - #957] GT 0.000001] OR [ABS[#958] GT 0.000001]]",
            "o<trace_gap_counter_consistency> if [ABS[#958] GT 0.000001]",
            1,
        ),
        "initial baseline quiet": text.replace(
            "o<trace_initial_baseline_quiet> if [[#955 GT 0.5] AND [[ABS[#956] GT 0.000001] OR [ABS[#957] GT 0.000001] OR [ABS[#958] GT 0.000001]]]",
            "o<trace_initial_baseline_quiet> if [0.0]",
            1,
        ),
        "exact trace count": text.replace(
            "o<trace_exact_count> if [ABS[#973 - 248.0] GT 0.000001]",
            "o<trace_exact_count> if [#973 LT 248.0]",
            1,
        ),
        "accepted row count": text.replace("#707 = 31.0", "#707 = 32.0", 1),
        "closure count guard": text.replace(
            "o<closure_sequence_complete> if [ABS[#978 - 14.0] GT 0.000001]",
            "o<closure_sequence_complete> if [ABS[#978 - 15.0] GT 0.000001]",
            1,
        ),
        "T3 pose body": text.replace(
            "o<tcpc_primary_tilt_block> call [45.0] [45.0]",
            "o<tcpc_primary_tilt_block> call [30.0] [45.0]",
            1,
        ),
        "line length": text + "\n(" + ("x" * 257) + ")\n",
    }
    for label, mutated in mutations.items():
        expect_failure(
            label,
            lambda value=mutated: validate_program_text(value, canonical, safety),
        )

    valid_header = [list(MODEL_STATE_FIELDS)]
    validate_header_rows(valid_header, MODEL_STATE_FIELDS)
    bad_header = [list(MODEL_STATE_FIELDS)]
    bad_header[0][5] = "wrong_model_id"
    expect_failure(
        "model-state header",
        lambda: validate_header_rows(bad_header, MODEL_STATE_FIELDS),
    )

    expected = EXPECTED_BY_SEQ[18]
    valid_model = synthetic_model_row(expected)
    validate_model_row(valid_model, expected)
    for field, value in (
        ("model_id", str(MODEL_ID + 1)),
        ("q", "0.99"),
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

    key = (1, 1, 1, 1)
    accepted_contacts = (
        synthetic_contact_row(),
        synthetic_contact_row(direct=(2, 2, 1)),
        synthetic_contact_row(repeats=(1, 1, 0)),
        synthetic_contact_row(direct=(3, 3, 1)),
        synthetic_contact_row(direct=(2, 2, 1), repeats=(1, 1, 0)),
    )
    for row in accepted_contacts:
        validate_contact_trace_row(row, key)

    rejected_contacts = {
        "direct raw mux mismatch": synthetic_contact_row(direct=(2, 1, 1)),
        "missing raw edge": synthetic_contact_row(direct=(0, 0, 1)),
        "missing gated edge": synthetic_contact_row(direct=(1, 1, 0)),
        "second gated edge": synthetic_contact_row(direct=(2, 2, 2)),
        "repeat raw mux mismatch": synthetic_contact_row(repeats=(1, 0, 0)),
        "gated repeat": synthetic_contact_row(repeats=(1, 1, 1)),
        "three filtered extras": synthetic_contact_row(direct=(4, 4, 1)),
        "failed G38": synthetic_contact_row(probe_result=0),
        "release fault": synthetic_contact_row(release_fault=1),
        "terminal failure": synthetic_contact_row(terminal_failure=1),
        "burst flag": synthetic_contact_row(burst_flag=1),
        "consistency flag": synthetic_contact_row(consistency_fault=1),
    }
    corrupt_delta = synthetic_contact_row(direct=(2, 2, 1))
    corrupt_delta["raw_delta"] = "1"
    rejected_contacts["logged direct delta"] = corrupt_delta
    corrupt_repeat = synthetic_contact_row(repeats=(1, 1, 0))
    corrupt_repeat["repeat_mux_delta"] = "0"
    rejected_contacts["logged repeat delta"] = corrupt_repeat
    corrupt_extra = synthetic_contact_row(direct=(2, 2, 1))
    corrupt_extra["extra_raw_minus_gated_delta"] = "0"
    rejected_contacts["logged extra delta"] = corrupt_extra
    for label, row in rejected_contacts.items():
        expect_failure(
            f"contact {label}",
            lambda value=row: validate_contact_trace_row(value, key),
        )

    first_contact = synthetic_contact_row(pre=(100, 100, 100))
    first_gap = synthetic_gap_row(first_contact)
    validate_gap_trace_row(first_gap, first_contact, None, 0, key)
    initial_pulse_gap = synthetic_gap_row(first_contact, gap_delta=(1, 1, 0))
    expect_failure(
        "gap initial baseline pulse",
        lambda: validate_gap_trace_row(
            initial_pulse_gap, first_contact, None, 0, key
        ),
    )

    prior_contact = synthetic_contact_row(
        direct=(2, 2, 1), pre=(100, 100, 100)
    )
    prior_ready = counter_tuple(prior_contact, "ready")
    next_pre = (prior_ready[0] + 1, prior_ready[1] + 1, prior_ready[2])
    next_contact = synthetic_contact_row(pre=next_pre)
    boundary_gap = synthetic_gap_row(
        next_contact, previous_contact=prior_contact, gap_delta=(1, 1, 0)
    )
    validate_gap_trace_row(boundary_gap, next_contact, prior_contact, 1, key)

    gap_field_mutations = {
        "logged delta": ("gap_raw_delta", "0"),
        "prior extra": ("prior_contact_extra_delta", "0"),
        "combined extra": ("combined_extra_delta", "1"),
        "burst flag": ("burst_flag", "1"),
        "consistency flag": ("consistency_fault", "1"),
    }
    for label, (field, value) in gap_field_mutations.items():
        mutated = dict(boundary_gap)
        mutated[field] = value
        expect_failure(
            f"gap {label}",
            lambda gap=mutated: validate_gap_trace_row(
                gap, next_contact, prior_contact, 1, key
            ),
        )

    rejected_gaps = {
        "raw mux mismatch": (1, 0, 0),
        "gated edge": (0, 0, 1),
    }
    for label, delta in rejected_gaps.items():
        bad_pre = tuple(prior_ready[index] + delta[index] for index in range(3))
        bad_contact = synthetic_contact_row(pre=bad_pre)
        bad_gap = synthetic_gap_row(
            bad_contact, previous_contact=prior_contact, gap_delta=delta
        )
        expect_failure(
            f"gap {label}",
            lambda gap=bad_gap, contact=bad_contact: validate_gap_trace_row(
                gap, contact, prior_contact, 1, key
            ),
        )

    max_prior = synthetic_contact_row(direct=(3, 3, 1))
    max_ready = counter_tuple(max_prior, "ready")
    excessive_pre = (max_ready[0] + 1, max_ready[1] + 1, max_ready[2])
    excessive_contact = synthetic_contact_row(pre=excessive_pre)
    excessive_gap = synthetic_gap_row(
        excessive_contact, previous_contact=max_prior, gap_delta=(1, 1, 0)
    )
    expect_failure(
        "gap combined extra bound",
        lambda: validate_gap_trace_row(
            excessive_gap, excessive_contact, max_prior, 1, key
        ),
    )

    expected_diagnostics = {
        "direct_duplicate_transactions": 3,
        "repeat_extra_transactions": 2,
        "contact_extra_transactions": 4,
        "contact_extra_edges": 6,
        "gap_extra_transactions": 1,
        "gap_extra_edges": 1,
        "maximum_contact_extra": 2,
        "maximum_combined_extra": 2,
    }
    assert trace_diagnostics(accepted_contacts, (first_gap, boundary_gap)) == expected_diagnostics
    historical_metric_formula_self_test()
    metric_gate_self_test()


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
            print("TCPC length-aware T3 validator self-test: PASS")
            return 0
        if args.preflight:
            self_test()
            report = args.report or DEFAULT_PREFLIGHT_REPORT
            write_preflight_report(report)
            print("TCPC length-aware T3 preflight: PASS")
        else:
            metrics, closure_norms, diagnostics = validate_completed_run()
            report = args.report or DEFAULT_RESULT_REPORT
            write_result_report(report, metrics, closure_norms, diagnostics)
            print("TCPC length-aware T3 result validation: PASS")
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
        print(f"TCPC length-aware T3 validation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
