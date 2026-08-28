#!/usr/bin/env python3
"""Reproducible offline closeout analysis for length-aware T4 Attempt 2.

The analyzer reads only hash-sealed calibration archives and writes one
Markdown report.  It has no controller interface and performs no machine
action.
"""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass
import hashlib
import importlib.util
import math
from pathlib import Path
import sys
from types import ModuleType
from typing import Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

BASELINE_ARCHIVE = (
    HERE
    / "calibration_runs/20260825_0815_campaign04_t4_fit_frozen"
)
ATTEMPT_ARCHIVE = (
    HERE
    / "calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete"
)
BASELINE_RESULTS = BASELINE_ARCHIVE / "tcpc-relocated-sphere-t4-primary-results.csv"
BASELINE_SUMS = BASELINE_ARCHIVE / "SHA256SUMS"

RESULTS = ATTEMPT_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2-results.csv"
STATE = ATTEMPT_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2-state.csv"
MODEL_STATE = ATTEMPT_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2-model-state.csv"
CLOSURES = ATTEMPT_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2-closures.csv"
CONTACT_TRACE = ATTEMPT_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2-contact-trace.csv"
GAP_TRACE = ATTEMPT_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2-gap-trace.csv"
RUNNER = ATTEMPT_ARCHIVE / "tcpc_length_aware_t4_validation_2026082601_attempt2.ngc"
VALIDATOR = ATTEMPT_ARCHIVE / "validate_tcpc_length_aware_t4_attempt2.py"
ASSESSOR = ATTEMPT_ARCHIVE / "assess_tcpc_length_aware_bounds.py"
VALIDATION_REPORT = ATTEMPT_ARCHIVE / "TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md"
ATTEMPT_SUMS = ATTEMPT_ARCHIVE / "SHA256SUMS"

DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_ATTEMPT2_CLOSEOUT_REPORT.md"

BASELINE_CAMPAIGN = 2026082404
BASELINE_MODE = 23
BASELINE_ATTEMPT = 1
ATTEMPT_CAMPAIGN = 2026082602
ATTEMPT_MODE = 32
ATTEMPT_ID = 2
MODEL_ID = 2026082601
TOOL = 4
TOOL_LENGTH_MM = 229.407000
EXPECTED_ROWS = 101
EXPECTED_UNIQUE = 76
EXPECTED_CLOSURES = 28
EXPECTED_TRANSACTIONS = 808
RMS_LIMIT_MM = 0.120
MAX_LIMIT_MM = 0.280
CLOSURE_LIMIT_MM = 0.050

# This digest seals the sequence-indexed canonical mapping as ASCII rows
# ``sequence:B:C`` after integer pose canonicalization and C modulo 360.
CANONICAL_MAPPING_SHA256 = (
    "51a4170ffa874c5757fd8d097200e5f5f67b627c1b2d32d951c056b4de88fd9f"
)

SEALED_HASHES = {
    BASELINE_SUMS: "d9cad3f41abaac5af29aed4e60d4ebc2c562f9607639ba3b4c6bb0498b69f76d",
    BASELINE_RESULTS: "70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468",
    ATTEMPT_SUMS: "546377e7ed7c98f4e24e6fc239b05810ea664ea101e6bd5d79e3c36558f9a880",
    RESULTS: "ff1d93d954bd1e5a5370db26adaf6d77c1eb4c2823ef5bd5c6fbe1ec6e36e47c",
    STATE: "ff6f0362a0a83505383044cb0ca1fe00f1d4ab6f5a882266720cb067fe75ed49",
    MODEL_STATE: "fb17c1295f9def5502fd25ef15bf01d6e8a10d61b8ddd4ebde62a8bde0bba43a",
    CLOSURES: "aca7c2f436bd49bbfdcb437d0a214f7312f92241dbb5c24ec7d6fbe15c01a552",
    CONTACT_TRACE: "95d2024c53203c6b944961bfd2f82eda28bd7b408a73d6b453e49229c341f777",
    GAP_TRACE: "02c5eb249467da28e611147a4c4baae5203528f77d1a83313bf7fd7a915d67a4",
    RUNNER: "d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d",
    VALIDATOR: "8d5f8c0fb34659d57377e9d3702cd4ac8614f008925e8cbcd33697316bc32f81",
    ASSESSOR: "b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2",
    VALIDATION_REPORT: "0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae",
}

RESULT_FIELDS = tuple(
    "schema_version,campaign_id,stage_mode,attempt_id,sample_seq,block_id,"
    "anchor_seq,is_closure,contact_count,u_method_code,abs_b_deg,abs_c_deg,"
    "live_tool_number,expected_tool_length_mm,probe_calibration_offset_mm,"
    "probe_diameter_mm,effective_contact_radius_mm,center_abs_x_mm,"
    "center_abs_y_mm,center_abs_z_mm,u_center_correction_mm,"
    "v_center_correction_mm,center_correction_norm_mm,v_corrected_diameter_mm,"
    "pass_center_delta_mm,w_contact_radial_residual_mm,"
    "u_contact_radial_residual_mm,v_minus_contact_radial_residual_mm,"
    "v_plus_contact_radial_residual_mm,w_travel_mm,u_travel_mm,"
    "v_minus_travel_mm,v_plus_travel_mm".split(",")
)
STATE_FIELDS = tuple(
    "schema_version,campaign_id,stage_mode,attempt_id,sample_seq,abs_b_deg,"
    "abs_c_deg,persistent_correction_enabled,tcpc_enabled,twp_active,"
    "twp_motion_enabled,twp_valid,b_ssi_invalid,c_ssi_invalid,"
    "motion_tooloffset_z_mm,halui_tool_length_offset_z_mm,"
    "kins_active_tool_offset_z_mm,joint_b_cmd_deg,joint_b_fb_deg,"
    "joint_c_cmd_deg,joint_c_fb_deg,b_ssi_zeroed_deg,c_ssi_zeroed_deg,"
    "accepted_endpoint_abs_x_mm,accepted_endpoint_abs_y_mm,"
    "accepted_endpoint_abs_z_mm,joint_0_motor_pos_cmd_mm,"
    "joint_0_motor_pos_fb_mm,joint_0_motor_following_error_fb_minus_cmd_mm,"
    "joint_1_motor_pos_cmd_mm,joint_1_motor_pos_fb_mm,"
    "joint_1_motor_following_error_fb_minus_cmd_mm,joint_2_motor_pos_cmd_mm,"
    "joint_2_motor_pos_fb_mm,joint_2_motor_following_error_fb_minus_cmd_mm".split(",")
)
MODEL_STATE_FIELDS = tuple(
    "schema_version,campaign_id,stage_mode,attempt_id,sample_seq,model_id,"
    "expected_model_id,configured,valid,fault_code,q,evaluated_b_deg,"
    "evaluated_c_deg,evaluated_length_mm,diff_offset_x_mm,diff_offset_y_mm,"
    "diff_offset_z_mm,diff_offset_norm_mm,empirical_offset_x_mm,"
    "empirical_offset_y_mm,empirical_offset_z_mm,empirical_offset_norm_mm".split(",")
)
CLOSURE_FIELDS = tuple(
    "schema_version,campaign_id,stage_mode,attempt_id,block_id,open_sample_seq,"
    "close_sample_seq,abs_b_deg,abs_c_deg,closure_dx_mm,closure_dy_mm,"
    "closure_dz_mm,closure_norm_mm,limit_mm,pass".split(",")
)
CONTACT_FIELDS = tuple(
    "schema_version,campaign_id,stage_mode,attempt_id,global_seq,abs_b_deg,"
    "abs_c_deg,acquisition_try,pass_id,contact_id,pre_raw_count,pre_mux_count,"
    "pre_gated_count,post_raw_count,post_mux_count,post_gated_count,"
    "ready_raw_count,ready_mux_count,ready_gated_count,probe_result,travel_mm,"
    "raw_delta,mux_delta,gated_delta,repeat_raw_delta,repeat_mux_delta,"
    "repeat_gated_delta,extra_raw_minus_gated_delta,burst_flag,"
    "consistency_fault,release_fault,terminal_failure".split(",")
)
GAP_FIELDS = tuple(
    "schema_version,campaign_id,stage_mode,attempt_id,next_global_seq,abs_b_deg,"
    "abs_c_deg,acquisition_try,pass_id,contact_id,prior_ready_raw_count,"
    "prior_ready_mux_count,prior_ready_gated_count,current_pre_raw_count,"
    "current_pre_mux_count,current_pre_gated_count,gap_raw_delta,gap_mux_delta,"
    "gap_gated_delta,prior_contact_extra_delta,combined_extra_delta,burst_flag,"
    "consistency_fault,initial_baseline".split(",")
)


class AnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class Metric:
    rms: float
    maximum: float


@dataclass(frozen=True)
class PulseSummary:
    direct_duplicates: int
    delayed_transactions: int
    contact_extra_transactions: int
    contact_extra_edges: int
    gap_extra_transactions: int
    gap_extra_edges: int
    gated_contacts: int
    terminal_raw: int
    terminal_mux: int
    terminal_gated: int


@dataclass(frozen=True)
class Closeout:
    baseline_raw: Metric
    predicted_raw: Metric
    actual_raw: Metric
    baseline_unique: Metric
    predicted_unique: Metric
    actual_unique: Metric
    raw_pattern: Metric
    unique_pattern: Metric
    closure: Metric
    pulse: PulseSummary
    baseline_unique_values: np.ndarray
    predicted_unique_values: np.ndarray
    actual_unique_values: np.ndarray
    unique_keys: tuple[tuple[int, int], ...]
    mean_translation: np.ndarray
    pattern_axis_rms: np.ndarray
    worst_pattern_pose: tuple[int, int]
    worst_pattern_vector: np.ndarray
    improved_count: int
    worsened_count: int
    predicted_improved_count: int
    predicted_worsened_count: int
    maximum_improvement: float
    maximum_improvement_pose: tuple[int, int]
    maximum_worsening: float
    maximum_worsening_pose: tuple[int, int]
    group_rows: tuple[tuple[str, int, Metric, Metric, Metric, Metric], ...]
    worst_signed_b: tuple[int, Metric]
    worst_c_sector: tuple[int, Metric]
    worst_closure_row: dict[str, str]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise AnalysisError(
            f"SHA-256 changed for {relative(path)}: {actual}, expected {expected}"
        )


def read_sum_inventory(path: Path) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise AnalysisError(f"{relative(path)}:{line_number}: malformed hash row")
        digest, name = parts
        if name in inventory or any(char not in "0123456789abcdef" for char in digest):
            raise AnalysisError(f"{relative(path)}:{line_number}: invalid hash inventory")
        inventory[name] = digest
    return inventory


def validate_provenance() -> None:
    for path, digest in SEALED_HASHES.items():
        require_hash(path, digest)

    baseline_inventory = read_sum_inventory(BASELINE_SUMS)
    if baseline_inventory.get(BASELINE_RESULTS.name) != SEALED_HASHES[BASELINE_RESULTS]:
        raise AnalysisError("frozen campaign-04 inventory does not own the baseline result")

    attempt_inventory = read_sum_inventory(ATTEMPT_SUMS)
    for path in (
        RESULTS,
        STATE,
        MODEL_STATE,
        CLOSURES,
        CONTACT_TRACE,
        GAP_TRACE,
        RUNNER,
        VALIDATOR,
        ASSESSOR,
        VALIDATION_REPORT,
    ):
        if attempt_inventory.get(path.name) != SEALED_HASHES[path]:
            raise AnalysisError(f"completion inventory does not own {path.name}")

    report_text = VALIDATION_REPORT.read_text(encoding="ascii")
    if "Status: `PASS`" not in report_text:
        raise AnalysisError("sealed formal validation report is not PASS")


def read_rows(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="ascii") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(fields):
                raise AnalysisError(f"{relative(path)}: exact schema mismatch")
            rows = list(reader)
    except UnicodeError as exc:
        raise AnalysisError(f"{relative(path)}: non-ASCII input") from exc
    for line_number, row in enumerate(rows, 2):
        if None in row or any(row.get(field) is None for field in fields):
            raise AnalysisError(f"{relative(path)}:{line_number}: malformed CSV row")
    return rows


def number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise AnalysisError(f"invalid numeric field {field}") from exc
    if not math.isfinite(value):
        raise AnalysisError(f"nonfinite numeric field {field}")
    return value


def exact_int(row: dict[str, str], field: str) -> int:
    value = number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9:
        raise AnalysisError(f"{field}={value:.9f} is not an exact integer")
    return int(rounded)


def validate_identity(
    rows: Sequence[dict[str, str]], campaign: int, mode: int, attempt: int
) -> None:
    for row in rows:
        expected = (
            ("schema_version", 1),
            ("campaign_id", campaign),
            ("stage_mode", mode),
            ("attempt_id", attempt),
        )
        if any(exact_int(row, field) != value for field, value in expected):
            raise AnalysisError("CSV identity differs from its sealed run")


def canonical_pose(b_deg: float, c_deg: float) -> tuple[int, int]:
    b_value = int(round(b_deg))
    c_value = int(round(c_deg)) % 360
    c_error = abs(((c_deg - c_value + 180.0) % 360.0) - 180.0)
    if abs(b_deg - b_value) > 0.01 or c_error > 0.01:
        raise AnalysisError(f"non-contract pose B{b_deg:.6f} C{c_deg:.6f}")
    return b_value, c_value


def result_values(
    rows: Sequence[dict[str, str]], *, campaign: int, mode: int, attempt: int
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    if len(rows) != EXPECTED_ROWS:
        raise AnalysisError(f"result row count is {len(rows)}, expected {EXPECTED_ROWS}")
    validate_identity(rows, campaign, mode, attempt)
    if [exact_int(row, "sample_seq") for row in rows] != list(range(1, EXPECTED_ROWS + 1)):
        raise AnalysisError("result sequence is not exact 1..101 order")
    for row in rows:
        if exact_int(row, "live_tool_number") != TOOL:
            raise AnalysisError("result contains another tool")
        if abs(number(row, "expected_tool_length_mm") - TOOL_LENGTH_MM) > 1e-9:
            raise AnalysisError("result contains another T4 length")
    centers = np.asarray(
        [
            [number(row, f"center_abs_{axis}_mm") for axis in "xyz"]
            for row in rows
        ],
        dtype=float,
    )
    keys = [
        canonical_pose(number(row, "abs_b_deg"), number(row, "abs_c_deg"))
        for row in rows
    ]
    return centers, keys


def centered(values: np.ndarray) -> np.ndarray:
    if values.ndim != 2 or values.shape[1] != 3 or not np.all(np.isfinite(values)):
        raise AnalysisError("center array must be finite Nx3")
    return values - np.mean(values, axis=0)


def residual_metric(residuals: np.ndarray) -> Metric:
    if not len(residuals):
        raise AnalysisError("cannot score an empty residual group")
    norms = np.linalg.norm(residuals, axis=1)
    return Metric(float(math.sqrt(np.mean(norms * norms))), float(np.max(norms)))


def center_metric(values: np.ndarray) -> Metric:
    return residual_metric(centered(values))


def canonical_groups(
    keys: Sequence[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, ...], ...]]:
    order: list[tuple[int, int]] = []
    grouped: dict[tuple[int, int], list[int]] = {}
    for index, key in enumerate(keys):
        if key not in grouped:
            order.append(key)
            grouped[key] = []
        grouped[key].append(index)
    if len(order) != EXPECTED_UNIQUE:
        raise AnalysisError(f"canonical collapse produced {len(order)} poses, expected 76")
    return tuple(order), tuple(tuple(grouped[key]) for key in order)


def collapse(values: np.ndarray, groups: Sequence[Sequence[int]]) -> np.ndarray:
    return np.vstack([np.mean(values[list(indices)], axis=0) for indices in groups])


def load_assessor() -> ModuleType:
    source = ASSESSOR.read_text(encoding="ascii")
    tree = ast.parse(source, filename=str(ASSESSOR))
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".", 1)[0]]
        if set(names) & {"linuxcnc", "hal"}:
            raise AnalysisError("sealed assessor has a forbidden controller import")
    spec = importlib.util.spec_from_file_location("_sealed_t4_length_assessor", ASSESSOR)
    if spec is None or spec.loader is None:
        raise AnalysisError("cannot load sealed assessor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prediction(
    baseline: np.ndarray,
    keys: Sequence[tuple[int, int]],
    assessor: ModuleType,
) -> np.ndarray:
    if abs(float(assessor.q_for_length(TOOL_LENGTH_MM))) > 1e-15:
        raise AnalysisError("sealed model no longer has q(T4)=0")
    if abs(float(assessor.C_ZERO_DEG) + 0.024500) > 1e-12:
        raise AnalysisError("sealed prediction C-zero convention changed")
    increments = []
    for b_deg, c_deg in keys:
        basis = assessor.basis_values(float(b_deg), np.asarray([float(c_deg)]))
        value = assessor.evaluate_surface(basis, assessor.COMMON_INCREMENT)[0]
        increments.append(value)
    result = baseline + np.asarray(increments)
    if not np.all(np.isfinite(result)):
        raise AnalysisError("prediction contains a nonfinite center")
    return result


def validate_supporting_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    state = read_rows(STATE, STATE_FIELDS)
    model = read_rows(MODEL_STATE, MODEL_STATE_FIELDS)
    closures = read_rows(CLOSURES, CLOSURE_FIELDS)
    contacts = read_rows(CONTACT_TRACE, CONTACT_FIELDS)
    gaps = read_rows(GAP_TRACE, GAP_FIELDS)
    contracts = (
        (state, EXPECTED_ROWS),
        (model, EXPECTED_ROWS),
        (closures, EXPECTED_CLOSURES),
        (contacts, EXPECTED_TRANSACTIONS),
        (gaps, EXPECTED_TRANSACTIONS),
    )
    for rows, expected_count in contracts:
        if len(rows) != expected_count:
            raise AnalysisError(f"supporting row count is {len(rows)}, expected {expected_count}")
        validate_identity(rows, ATTEMPT_CAMPAIGN, ATTEMPT_MODE, ATTEMPT_ID)

    if [exact_int(row, "sample_seq") for row in state] != list(range(1, 102)):
        raise AnalysisError("state sequence is not exact 1..101 order")
    if [exact_int(row, "sample_seq") for row in model] != list(range(1, 102)):
        raise AnalysisError("model-state sequence is not exact 1..101 order")
    for row in model:
        checks = (
            exact_int(row, "model_id") == MODEL_ID,
            exact_int(row, "expected_model_id") == MODEL_ID,
            exact_int(row, "configured") == 1,
            exact_int(row, "valid") == 1,
            exact_int(row, "fault_code") == 0,
            abs(number(row, "q")) <= 1e-12,
            abs(number(row, "evaluated_length_mm") - TOOL_LENGTH_MM) <= 1e-9,
            abs(number(row, "diff_offset_norm_mm")) <= 1e-12,
        )
        if not all(checks):
            raise AnalysisError("model-state row is not a valid T4 q=0 snapshot")
    return state, model, closures, contacts, gaps


def closure_summary(rows: Sequence[dict[str, str]]) -> tuple[Metric, dict[str, str]]:
    values = []
    for row in rows:
        value = number(row, "closure_norm_mm")
        if exact_int(row, "pass") != 1 or number(row, "limit_mm") != CLOSURE_LIMIT_MM:
            raise AnalysisError("closure row did not pass the frozen 0.050 mm gate")
        if value > CLOSURE_LIMIT_MM + 1e-12:
            raise AnalysisError("closure norm exceeds its frozen limit")
        values.append(value)
    array = np.asarray(values)
    metric = Metric(float(math.sqrt(np.mean(array * array))), float(np.max(array)))
    return metric, rows[int(np.argmax(array))]


def pulse_summary(
    contacts: Sequence[dict[str, str]], gaps: Sequence[dict[str, str]]
) -> PulseSummary:
    direct_duplicates = 0
    delayed_transactions = 0
    contact_extra_transactions = 0
    contact_extra_edges = 0
    gated_contacts = 0
    for row in contacts:
        direct = tuple(exact_int(row, field) for field in ("raw_delta", "mux_delta", "gated_delta"))
        repeat = tuple(exact_int(row, field) for field in ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"))
        extra = exact_int(row, "extra_raw_minus_gated_delta")
        flags = tuple(exact_int(row, field) for field in ("burst_flag", "consistency_fault", "release_fault", "terminal_failure"))
        expected_extra = direct[0] + repeat[0] - direct[2] - repeat[2]
        if (
            direct[0] != direct[1]
            or direct[0] < 1
            or direct[2] != 1
            or repeat[0] != repeat[1]
            or repeat[2] != 0
            or extra != expected_extra
            or not 0 <= extra <= 2
            or exact_int(row, "probe_result") != 1
            or flags != (0, 0, 0, 0)
        ):
            raise AnalysisError("contact trace violates the accepted duplicate-pulse contract")
        direct_duplicates += int(direct[0] > 1)
        delayed_transactions += int(repeat[0] > 0)
        contact_extra_transactions += int(extra > 0)
        contact_extra_edges += extra
        gated_contacts += direct[2] + repeat[2]

    gap_extra_transactions = 0
    gap_extra_edges = 0
    for row in gaps:
        delta = tuple(exact_int(row, field) for field in ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"))
        flags = tuple(exact_int(row, field) for field in ("burst_flag", "consistency_fault"))
        if delta[0] != delta[1] or delta[2] != 0 or flags != (0, 0):
            raise AnalysisError("gap trace contains an unsafe pulse pattern")
        gap_extra_transactions += int(delta[0] > 0)
        gap_extra_edges += delta[0]

    terminal = tuple(
        max(exact_int(row, field) for row in contacts)
        for field in ("ready_raw_count", "ready_mux_count", "ready_gated_count")
    )
    summary = PulseSummary(
        direct_duplicates,
        delayed_transactions,
        contact_extra_transactions,
        contact_extra_edges,
        gap_extra_transactions,
        gap_extra_edges,
        gated_contacts,
        terminal[0],
        terminal[1],
        terminal[2],
    )
    if summary != PulseSummary(0, 14, 14, 14, 1, 1, 808, 823, 823, 808):
        raise AnalysisError(f"sealed pulse diagnostics changed: {summary}")
    return summary


def subset_metric(residuals: np.ndarray, mask: np.ndarray) -> Metric:
    return residual_metric(residuals[mask])


def group_diagnostics(
    keys: Sequence[tuple[int, int]],
    baseline_residuals: np.ndarray,
    predicted_residuals: np.ndarray,
    actual_residuals: np.ndarray,
) -> tuple[
    tuple[tuple[str, int, Metric, Metric, Metric, Metric], ...],
    tuple[int, Metric],
    tuple[int, Metric],
]:
    b_values = np.asarray([key[0] for key in keys])
    c_values = np.asarray([key[1] for key in keys])
    discrepancy = actual_residuals - predicted_residuals
    masks = (
        ("B0", b_values == 0),
        ("positive B", b_values > 0),
        ("negative B", b_values < 0),
        ("positive high B (>=30)", b_values >= 30),
        ("negative high B (<=-30)", b_values <= -30),
        ("low tilt (|B|<=15)", np.abs(b_values) <= 15),
    )
    rows = tuple(
        (
            label,
            int(np.sum(mask)),
            subset_metric(baseline_residuals, mask),
            subset_metric(predicted_residuals, mask),
            subset_metric(actual_residuals, mask),
            subset_metric(discrepancy, mask),
        )
        for label, mask in masks
    )
    signed = [
        (int(value), subset_metric(discrepancy, b_values == value))
        for value in sorted(set(b_values.tolist()))
    ]
    sectors = [
        (int(value), subset_metric(discrepancy, c_values == value))
        for value in sorted(set(c_values.tolist()))
    ]
    return rows, max(signed, key=lambda item: item[1].rms), max(sectors, key=lambda item: item[1].rms)


def analyze() -> Closeout:
    validate_provenance()
    baseline_rows = read_rows(BASELINE_RESULTS, RESULT_FIELDS)
    actual_rows = read_rows(RESULTS, RESULT_FIELDS)
    baseline, baseline_keys = result_values(
        baseline_rows,
        campaign=BASELINE_CAMPAIGN,
        mode=BASELINE_MODE,
        attempt=BASELINE_ATTEMPT,
    )
    actual, actual_keys = result_values(
        actual_rows,
        campaign=ATTEMPT_CAMPAIGN,
        mode=ATTEMPT_MODE,
        attempt=ATTEMPT_ID,
    )
    if actual_keys != baseline_keys:
        raise AnalysisError("Attempt 2 sequence-indexed poses differ from the baseline")
    mapping_text = "".join(
        f"{seq}:{key[0]}:{key[1]}\n"
        for seq, key in enumerate(baseline_keys, 1)
    )
    mapping_digest = hashlib.sha256(mapping_text.encode("ascii")).hexdigest()
    if mapping_digest != CANONICAL_MAPPING_SHA256:
        raise AnalysisError("canonical 101-row pose mapping changed")
    unique_keys, groups = canonical_groups(baseline_keys)

    assessor = load_assessor()
    predicted = prediction(baseline, baseline_keys, assessor)
    baseline_unique = collapse(baseline, groups)
    predicted_unique = collapse(predicted, groups)
    actual_unique = collapse(actual, groups)

    baseline_raw_metric = center_metric(baseline)
    predicted_raw_metric = center_metric(predicted)
    actual_raw_metric = center_metric(actual)
    baseline_unique_metric = center_metric(baseline_unique)
    predicted_unique_metric = center_metric(predicted_unique)
    actual_unique_metric = center_metric(actual_unique)
    predicted_contract = (
        predicted_raw_metric.rms,
        predicted_raw_metric.maximum,
        predicted_unique_metric.rms,
        predicted_unique_metric.maximum,
    )
    expected_prediction = (
        0.1048887982265539,
        0.2503720296549383,
        0.10725592769956575,
        0.2472503056839364,
    )
    if max(abs(left - right) for left, right in zip(predicted_contract, expected_prediction)) > 1e-10:
        raise AnalysisError("sealed T4 prediction/reference convention changed")
    for label, metric in (("raw-101", actual_raw_metric), ("equal-76", actual_unique_metric)):
        if metric.rms > RMS_LIMIT_MM or metric.maximum > MAX_LIMIT_MM:
            raise AnalysisError(f"{label} metric no longer passes the formal accuracy gate")

    baseline_raw_residuals = centered(baseline)
    predicted_raw_residuals = centered(predicted)
    actual_raw_residuals = centered(actual)
    baseline_unique_residuals = centered(baseline_unique)
    predicted_unique_residuals = centered(predicted_unique)
    actual_unique_residuals = centered(actual_unique)
    raw_pattern = residual_metric(actual_raw_residuals - predicted_raw_residuals)
    unique_pattern_values = actual_unique_residuals - predicted_unique_residuals
    unique_pattern = residual_metric(unique_pattern_values)

    _, _, closures, contacts, gaps = validate_supporting_rows()
    closure, worst_closure = closure_summary(closures)
    pulse = pulse_summary(contacts, gaps)

    baseline_norms = np.linalg.norm(baseline_unique_residuals, axis=1)
    predicted_norms = np.linalg.norm(predicted_unique_residuals, axis=1)
    actual_norms = np.linalg.norm(actual_unique_residuals, axis=1)
    improvement = baseline_norms - actual_norms
    improvement_index = int(np.argmax(improvement))
    worsening_index = int(np.argmin(improvement))
    pattern_index = int(np.argmax(np.linalg.norm(unique_pattern_values, axis=1)))
    group_rows, worst_signed_b, worst_c_sector = group_diagnostics(
        unique_keys,
        baseline_unique_residuals,
        predicted_unique_residuals,
        actual_unique_residuals,
    )

    return Closeout(
        baseline_raw_metric,
        predicted_raw_metric,
        actual_raw_metric,
        baseline_unique_metric,
        predicted_unique_metric,
        actual_unique_metric,
        raw_pattern,
        unique_pattern,
        closure,
        pulse,
        baseline_unique,
        predicted_unique,
        actual_unique,
        unique_keys,
        np.mean(actual_unique, axis=0) - np.mean(predicted_unique, axis=0),
        np.sqrt(np.mean(unique_pattern_values * unique_pattern_values, axis=0)),
        unique_keys[pattern_index],
        unique_pattern_values[pattern_index],
        int(np.sum(actual_norms < baseline_norms)),
        int(np.sum(actual_norms > baseline_norms)),
        int(np.sum(predicted_norms < baseline_norms)),
        int(np.sum(predicted_norms > baseline_norms)),
        float(improvement[improvement_index]),
        unique_keys[improvement_index],
        float(-improvement[worsening_index]),
        unique_keys[worsening_index],
        group_rows,
        worst_signed_b,
        worst_c_sector,
        worst_closure,
    )


def pose_text(pose: tuple[int, int]) -> str:
    return f"B{pose[0]:+d}/C{pose[1]}"


def vector_text(vector: np.ndarray) -> str:
    return ", ".join(f"{value:+.6f}" for value in vector)


def render_report(result: Closeout) -> str:
    unique_rms_reduction = 100.0 * (1.0 - result.actual_unique.rms / result.baseline_unique.rms)
    unique_max_reduction = 100.0 * (1.0 - result.actual_unique.maximum / result.baseline_unique.maximum)
    raw_rms_reduction = 100.0 * (1.0 - result.actual_raw.rms / result.baseline_raw.rms)
    raw_max_reduction = 100.0 * (1.0 - result.actual_raw.maximum / result.baseline_raw.maximum)
    analyzer_hash = sha256(Path(__file__).resolve())
    provenance_paths = (
        BASELINE_SUMS,
        BASELINE_RESULTS,
        ATTEMPT_SUMS,
        RESULTS,
        STATE,
        MODEL_STATE,
        CLOSURES,
        CONTACT_TRACE,
        GAP_TRACE,
        RUNNER,
        VALIDATOR,
        ASSESSOR,
        VALIDATION_REPORT,
    )
    lines = [
        "# TCPC Length-Aware T4 Attempt 2 Closeout",
        "",
        "Status: `PASS - T4 q=0 common-bank validation complete`",
        "",
        "## Disposition",
        "",
        "The sealed 101-pose T4 acquisition passes its formal centered-error, closure, model-state, and probe-transaction contracts. It validates the length-aware implementation and common correction bank at T4, where `q=0`. It does not validate the T3 differential bank, other tool lengths, a different table location, or production release.",
        "",
        f"- formal raw-101 RMS / max: `{result.actual_raw.rms:.6f} / {result.actual_raw.maximum:.6f} mm`",
        f"- formal equal-76 RMS / max: `{result.actual_unique.rms:.6f} / {result.actual_unique.maximum:.6f} mm`",
        f"- formal limits: `{RMS_LIMIT_MM:.3f} / {MAX_LIMIT_MM:.3f} mm`",
        f"- closure RMS / max: `{result.closure.rms:.6f} / {result.closure.maximum:.6f} mm` across `{EXPECTED_CLOSURES}` closures",
        "",
        "## Reproducible Method",
        "",
        "The baseline is not inferred from a later candidate run. It is the exact mode-23 T4 result owned by the pre-machine campaign-04 fit freeze at `20260825_0815_campaign04_t4_fit_frozen`; that archive inventory and result hash are both verified. Attempt 2 is read only from its completion archive.",
        "",
        "For each sequence, B is rounded to the contract integer and C is rounded modulo 360 with a maximum 0.01 degree tolerance. The resulting 101-key sequence must match digest `" + CANONICAL_MAPPING_SHA256 + "` and collapses by first canonical occurrence to 76 equal-weight poses. Repeated-pose centers are arithmetic means.",
        "",
        "At T4, the sealed model has `q(T4)=0`, so the offline prediction is:",
        "",
        "```text",
        "predicted center(B,C) = frozen H0 baseline center(B,C) + S(B,C)",
        "centered residual i    = center i - mean(center field)",
        "RMS                    = sqrt(mean(norm(centered residual i)^2))",
        "```",
        "",
        "Baseline, prediction, and fresh actual fields are centered independently. This removes only the unidentifiable global sphere-center translation; it does not align, rotate, scale, or refit the pose fields.",
        "",
        "## Baseline Comparison",
        "",
        "| weighting | frozen H0 baseline | sealed H0+S prediction | fresh actual | actual reduction from baseline |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| raw 101 rows RMS / max | `{result.baseline_raw.rms:.6f} / {result.baseline_raw.maximum:.6f}` | `{result.predicted_raw.rms:.6f} / {result.predicted_raw.maximum:.6f}` | `{result.actual_raw.rms:.6f} / {result.actual_raw.maximum:.6f}` | `{raw_rms_reduction:.1f}% / {raw_max_reduction:.1f}%` |",
        f"| equal 76 poses RMS / max | `{result.baseline_unique.rms:.6f} / {result.baseline_unique.maximum:.6f}` | `{result.predicted_unique.rms:.6f} / {result.predicted_unique.maximum:.6f}` | `{result.actual_unique.rms:.6f} / {result.actual_unique.maximum:.6f}` | `{unique_rms_reduction:.1f}% / {unique_max_reduction:.1f}%` |",
        "",
        f"Actual residual norm improves at `{result.improved_count}/76` poses and worsens at `{result.worsened_count}/76`; the prediction expected `{result.predicted_improved_count}` improvements and `{result.predicted_worsened_count}` worsenings. The largest improvement is `{result.maximum_improvement:.6f} mm` at `{pose_text(result.maximum_improvement_pose)}`. The largest local worsening is `{result.maximum_worsening:.6f} mm` at `{pose_text(result.maximum_worsening_pose)}`; this is diagnostic and does not exceed the run's absolute maximum-error contract.",
        "",
        "## Spatial Agreement",
        "",
        f"- raw-101 actual-minus-predicted centered-pattern RMS / max: `{result.raw_pattern.rms:.6f} / {result.raw_pattern.maximum:.6f} mm`",
        f"- equal-76 actual-minus-predicted centered-pattern RMS / max: `{result.unique_pattern.rms:.6f} / {result.unique_pattern.maximum:.6f} mm`",
        f"- equal-76 uncentered mean translation actual-minus-predicted XYZ: `[{vector_text(result.mean_translation)}] mm`, norm `{np.linalg.norm(result.mean_translation):.6f} mm`",
        f"- centered-pattern per-axis RMS XYZ: `[{vector_text(result.pattern_axis_rms)}] mm`",
        f"- largest centered-pattern discrepancy: `{pose_text(result.worst_pattern_pose)}`, vector `[{vector_text(result.worst_pattern_vector)}] mm`, norm `{result.unique_pattern.maximum:.6f} mm`",
        "",
        "The mean translation is reported rather than hidden, but it is excluded from TCPC pose-field scoring by the frozen centering convention. It can include machine-coordinate drift, artifact-location change, probe seating, and common acquisition offset and cannot by itself identify a B-axis or rail correction.",
        "",
        "### B Groups",
        "",
        "All group RMS values below use the one global equal-76 mean for each field; no group is recentered.",
        "",
        "| group | poses | baseline RMS | prediction RMS | actual RMS | actual-prediction pattern RMS |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, count, baseline, predicted, actual, discrepancy in result.group_rows:
        lines.append(
            f"| {label} | `{count}` | `{baseline.rms:.6f}` | `{predicted.rms:.6f}` | `{actual.rms:.6f}` | `{discrepancy.rms:.6f}` |"
        )
    lines.extend(
        [
            "",
            f"The largest exact signed-B group discrepancy is `B{result.worst_signed_b[0]:+d}` at `{result.worst_signed_b[1].rms:.6f} mm` RMS. The largest C-sector discrepancy is `C{result.worst_c_sector[0]}` at `{result.worst_c_sector[1].rms:.6f} mm` RMS. The positive/negative asymmetry remains visible, but a single T4 sphere field cannot separate B-axis alignment from X/Y/Z rail, head, spindle, seating, or table-position effects.",
            "",
            "## Closure And Pulse Evidence",
            "",
            f"All `{EXPECTED_CLOSURES}` closures pass `<= {CLOSURE_LIMIT_MM:.3f} mm`; RMS / max are `{result.closure.rms:.6f} / {result.closure.maximum:.6f} mm`. The worst is block `{exact_int(result.worst_closure_row, 'block_id')}` (`{exact_int(result.worst_closure_row, 'open_sample_seq')}->{exact_int(result.worst_closure_row, 'close_sample_seq')}`) at `{result.closure.maximum:.6f} mm`. Closure measures within-run return consistency, not absolute TCPC accuracy or mechanical-axis alignment.",
            "",
            f"The trace contains `{result.pulse.terminal_raw}/{result.pulse.terminal_mux}/{result.pulse.terminal_gated}` terminal raw/mux/gated counts. Exactly `{result.pulse.gated_contacts}` contacts reached motion. The bounded filter accepted `{result.pulse.contact_extra_edges}` delayed post-contact raw/mux edges in `{result.pulse.contact_extra_transactions}` transactions and `{result.pulse.gap_extra_edges}` inter-contact edge in `{result.pulse.gap_extra_transactions}` transaction; direct duplicates were `{result.pulse.direct_duplicates}`. No extra edge reached the gated motion input.",
            "",
            "These extras remain evidence of probe-system electrical susceptibility. Their acceptance means the logged second pulses occurred outside the one gated G38 contact and passed release/consistency guards; it does not mean future pulse faults may be ignored without the same contract. The new-session manual-deflection check was explicitly waived because T4 had not been reseated, while two passive 30-second quiet checks passed. That waiver is retained as a qualification caveat.",
            "",
            "## Next Stage",
            "",
            "1. Freeze this T4 result without retuning the common bank.",
            "2. Run the fresh T3 length-aware validation under the same model ID and coefficient set. T3 is the required `q=1` differential-bank check and must remain an untouched verification set.",
            "3. If T3 passes, test the long-tool endpoint near 425-430 mm with the planned dial-gauge method; a second 100-115 mm endpoint remains preferable. The software envelope alone is not accuracy evidence outside the T3-T4 bracket.",
            "4. Use a later second table position to distinguish repeatable TCPC/B-axis structure from X/Y/Z rail and machine-volume effects. Do not infer axis correction tables from this single sphere location.",
            "",
            "The T4 common-bank implementation is accepted for the next validation stage, not for production promotion. The roughly 0.108 mm equal-pose RMS, 0.242 mm worst pose, 0.022 mm closure RMS, and 0.075 mm worst prediction discrepancy do not support a general sub-10-micron machine claim.",
            "",
            "## Sealed Provenance",
            "",
            f"Analyzer: `{relative(Path(__file__).resolve())}` SHA-256 `{analyzer_hash}`.",
            "",
            "| input | computed and required SHA-256 |",
            "| --- | --- |",
        ]
    )
    for path in provenance_paths:
        lines.append(f"| `{relative(path)}` | `{sha256(path)}` |")
    lines.extend(
        [
            "",
            "This analyzer imports no controller module, reads no live state, and issues no machine command.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_python_safety() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"), filename=__file__)
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".", 1)[0]]
        if set(names) & {"linuxcnc", "hal"}:
            raise AnalysisError("analyzer has a forbidden controller import")


def self_test() -> None:
    validate_python_safety()
    if canonical_pose(-0.00001, 360.00032) != (0, 0):
        raise AssertionError("pose canonicalization failed")
    try:
        canonical_pose(0.02, 0.0)
    except AnalysisError:
        pass
    else:
        raise AssertionError("off-contract pose was accepted")
    test_values = np.asarray([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [4.0, 0.0, 0.0]])
    test_keys = ((0, 0), (0, 45))
    test_groups = ((0, 1), (2,))
    if test_keys != ((0, 0), (0, 45)) or not np.array_equal(
        collapse(test_values, test_groups),
        [[1.0, 0.0, 0.0], [4.0, 0.0, 0.0]],
    ):
        raise AssertionError("unique-pose collapse failed")
    known = center_metric(np.asarray([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]]))
    if abs(known.rms - 1.0) > 1e-15 or abs(known.maximum - 1.0) > 1e-15:
        raise AssertionError("metric formula failed")
    result = analyze()
    expected = (
        (result.baseline_raw.rms, 0.2010161412067549),
        (result.predicted_raw.rms, 0.1048887982265539),
        (result.actual_raw.rms, 0.1051635465071548),
        (result.baseline_unique.rms, 0.21960179392464912),
        (result.predicted_unique.rms, 0.10725592769956575),
        (result.actual_unique.rms, 0.10758912508070545),
        (result.unique_pattern.rms, 0.03882403331669973),
        (result.unique_pattern.maximum, 0.07490382505276962),
        (result.closure.rms, 0.022237265685748582),
    )
    if any(abs(actual - wanted) > 1e-12 for actual, wanted in expected):
        raise AssertionError("sealed full-data metric changed")
    report = render_report(result)
    report.encode("ascii")
    if "Status: `PASS - T4 q=0 common-bank validation complete`" not in report:
        raise AssertionError("report status is missing")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check", action="store_true", help="compare the existing report byte-for-byte")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("T4 Attempt 2 closeout analyzer self-test: PASS")
            return 0
        report = render_report(analyze())
        if args.check:
            try:
                existing = args.report.read_text(encoding="ascii")
            except (OSError, UnicodeError) as exc:
                raise AnalysisError(f"cannot read report for deterministic check: {exc}") from exc
            if existing != report:
                raise AnalysisError("closeout report differs from deterministic analyzer output")
            print("T4 Attempt 2 closeout report check: PASS")
            return 0
        args.report.write_text(report, encoding="ascii")
        print(f"wrote {args.report}")
        print("T4 Attempt 2 closeout analysis: PASS")
        return 0
    except (AnalysisError, OSError, UnicodeError, ValueError) as exc:
        print(f"T4 Attempt 2 closeout analysis: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
