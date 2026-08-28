#!/usr/bin/env python3
"""Compare the T4 new-location sphere field with the sealed T4 reference.

This is a diagnostic-only offline analyzer.  It reads CSV files, validates the
acquisition and model contracts, and writes a Markdown report.  It has no
controller interface and performs no machine action.
"""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import sys
from typing import Iterable, Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

NEW_CAMPAIGN = 2026082701
NEW_MODE = 35
NEW_ATTEMPT = 1
NEW_BASE = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt1"

REFERENCE_ARCHIVE = (
    HERE
    / "calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete"
)
REFERENCE_BASE = REFERENCE_ARCHIVE / "tcpc-length-aware-t4-validation-2026082601-attempt2"
REFERENCE_CAMPAIGN = 2026082602
REFERENCE_MODE = 32
REFERENCE_ATTEMPT = 2
REFERENCE_SUMS = REFERENCE_ARCHIVE / "SHA256SUMS"
REFERENCE_REPORT = REFERENCE_ARCHIVE / "TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md"

DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_COMPARISON_REPORT.md"

MODEL_ID = 2026082601
TOOL = 4
TOOL_LENGTH_MM = 229.407000
PROBE_OFFSET_MM = 0.154742
PROBE_DIAMETER_MM = 6.0
EFFECTIVE_RADIUS_MM = 15.0 + PROBE_DIAMETER_MM / 2.0 - PROBE_OFFSET_MM
EXPECTED_ROWS = 101
EXPECTED_UNIQUE = 76
EXPECTED_CLOSURES = 28
EXPECTED_TRANSACTIONS = 808
MAX_FILTERED_EXTRA_EDGES = 2
CLOSURE_LIMIT_MM = 0.050
TRANSFER_RMS_LIMIT_MM = 0.120
TRANSFER_MAX_LIMIT_MM = 0.280
LOCATION_MATERIAL_RMS_MM = 0.050
LOCATION_MATERIAL_MAX_MM = 0.100
LOCATION_STRONG_RMS_MM = 0.100
LOCATION_STRONG_MAX_MM = 0.200

# SHA-256 of ASCII rows ``sequence:B:C`` after pose canonicalization.
CANONICAL_MAPPING_SHA256 = (
    "51a4170ffa874c5757fd8d097200e5f5f67b627c1b2d32d951c056b4de88fd9f"
)

REFERENCE_HASHES = {
    REFERENCE_SUMS: "546377e7ed7c98f4e24e6fc239b05810ea664ea101e6bd5d79e3c36558f9a880",
    Path(f"{REFERENCE_BASE}-results.csv"): "ff1d93d954bd1e5a5370db26adaf6d77c1eb4c2823ef5bd5c6fbe1ec6e36e47c",
    Path(f"{REFERENCE_BASE}-state.csv"): "ff6f0362a0a83505383044cb0ca1fe00f1d4ab6f5a882266720cb067fe75ed49",
    Path(f"{REFERENCE_BASE}-model-state.csv"): "fb17c1295f9def5502fd25ef15bf01d6e8a10d61b8ddd4ebde62a8bde0bba43a",
    Path(f"{REFERENCE_BASE}-closures.csv"): "aca7c2f436bd49bbfdcb437d0a214f7312f92241dbb5c24ec7d6fbe15c01a552",
    Path(f"{REFERENCE_BASE}-contact-trace.csv"): "95d2024c53203c6b944961bfd2f82eda28bd7b408a73d6b453e49229c341f777",
    Path(f"{REFERENCE_BASE}-gap-trace.csv"): "02c5eb249467da28e611147a4c4baae5203528f77d1a83313bf7fd7a915d67a4",
    REFERENCE_REPORT: "0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae",
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
class ExpectedRow:
    seq: int
    block: int
    anchor_seq: int
    is_closure: int
    pose: tuple[int, int]


@dataclass(frozen=True)
class Metric:
    rms: float
    maximum: float


@dataclass(frozen=True)
class PulseSummary:
    direct_duplicate_transactions: int
    delayed_transactions: int
    contact_extra_transactions: int
    contact_extra_edges: int
    gap_extra_transactions: int
    gap_extra_edges: int
    maximum_contact_extra: int
    maximum_combined_extra: int
    gated_contacts: int
    initial_raw: int
    initial_mux: int
    initial_gated: int
    terminal_raw: int
    terminal_mux: int
    terminal_gated: int


@dataclass(frozen=True)
class ClosureSummary:
    metric: Metric
    axis_rms: np.ndarray
    worst_block: int
    worst_open_seq: int
    worst_close_seq: int


@dataclass(frozen=True)
class ScalarStats:
    mean: float
    standard_deviation: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class RepeatedScatter:
    group_count: int
    observation_count: int
    metric: Metric
    axis_rms: np.ndarray
    b0c0_count: int
    b0c0_metric: Metric


@dataclass(frozen=True)
class B0Drift:
    opening: np.ndarray
    midpoint: np.ndarray
    closing: np.ndarray
    midpoint_from_opening: np.ndarray
    closing_from_opening: np.ndarray


@dataclass(frozen=True)
class RunData:
    label: str
    base: Path
    raw_centers: np.ndarray
    raw_keys: tuple[tuple[int, int], ...]
    unique_centers: np.ndarray
    unique_keys: tuple[tuple[int, int], ...]
    raw_metric: Metric
    unique_metric: Metric
    raw_mean: np.ndarray
    unique_mean: np.ndarray
    closure: ClosureSummary
    pulse: PulseSummary
    raw_diameters: np.ndarray
    unique_diameters: np.ndarray
    raw_joint_commands: np.ndarray
    unique_joint_commands: np.ndarray
    repeated_scatter: RepeatedScatter
    b0_drift: B0Drift
    model_rows: tuple[dict[str, str], ...]
    files: tuple[Path, ...]


@dataclass(frozen=True)
class GroupDiagnostic:
    label: str
    count: int
    new_metric: Metric
    delta_metric: Metric
    delta_axis_rms: np.ndarray


@dataclass(frozen=True)
class PairDiagnostic:
    abs_b: int
    c_sector: int
    even_vector: np.ndarray
    odd_vector: np.ndarray


@dataclass(frozen=True)
class PairBandDiagnostic:
    abs_b: int
    pair_count: int
    even_metric: Metric
    odd_metric: Metric
    even_axis_rms: np.ndarray
    odd_axis_rms: np.ndarray


@dataclass(frozen=True)
class DiameterComparison:
    reference: ScalarStats
    new: ScalarStats
    delta_mean: float
    delta_rms: float
    delta_maximum_absolute: float


@dataclass(frozen=True)
class JointRelocation:
    mean: np.ndarray
    axis_standard_deviation: np.ndarray
    centered_metric: Metric


@dataclass(frozen=True)
class Comparison:
    reference: RunData
    new: RunData
    transfer_pass: bool
    location_classification: str
    raw_delta_metric: Metric
    raw_delta_axis_rms: np.ndarray
    delta_metric: Metric
    delta_axis_rms: np.ndarray
    raw_mean_displacement: np.ndarray
    unique_mean_displacement: np.ndarray
    worst_pose: tuple[int, int]
    worst_pose_vector: np.ndarray
    signed_b: tuple[GroupDiagnostic, ...]
    abs_b: tuple[GroupDiagnostic, ...]
    c_sectors: tuple[GroupDiagnostic, ...]
    pair_rows: tuple[PairDiagnostic, ...]
    pair_bands: tuple[PairBandDiagnostic, ...]
    b0_midpoint_drift_delta: np.ndarray
    b0_closing_drift_delta: np.ndarray
    diameter: DiameterComparison
    joint_relocation: JointRelocation
    location_purity_ratio: float | None


T4_RANGES = (
    (100, 1, 9),
    (5, 10, 16),
    (-5, 17, 23),
    (10, 24, 30),
    (-10, 31, 37),
    (15, 38, 44),
    (-15, 45, 51),
    (30, 52, 56),
    (-30, 57, 61),
    (45, 62, 66),
    (-45, 67, 71),
    (500, 72, 72),
    (60, 73, 77),
    (-60, 78, 82),
    (90, 83, 87),
    (-90, 88, 92),
    (200, 93, 101),
)
T4_CLOSURES = (
    (100, 1, 9),
    (5, 10, 16),
    (-5, 17, 23),
    (10, 24, 30),
    (-10, 31, 37),
    (15, 38, 44),
    (-15, 45, 51),
    (30, 52, 56),
    (-30, 57, 61),
    (45, 62, 66),
    (-45, 67, 71),
    (905, 9, 72),
    (60, 73, 77),
    (-60, 78, 82),
    (90, 83, 87),
    (-90, 88, 92),
    (911, 1, 93),
    (906, 72, 93),
    (912, 2, 94),
    (913, 3, 95),
    (914, 4, 96),
    (915, 5, 97),
    (916, 6, 98),
    (917, 7, 99),
    (918, 8, 100),
    (919, 9, 101),
    (200, 93, 101),
    (900, 1, 101),
)


def paths_for_base(base: Path) -> tuple[Path, Path, Path, Path, Path, Path]:
    return tuple(
        Path(f"{base}-{suffix}.csv")
        for suffix in (
            "results",
            "state",
            "model-state",
            "closures",
            "contact-trace",
            "gap-trace",
        )
    )  # type: ignore[return-value]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def read_sum_inventory(path: Path) -> dict[str, str]:
    inventory: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise AnalysisError(f"{relative(path)}:{line_number}: malformed hash row")
        digest, name = parts
        if any(char not in "0123456789abcdef" for char in digest) or name in inventory:
            raise AnalysisError(f"{relative(path)}:{line_number}: invalid hash inventory")
        inventory[name] = digest
    return inventory


def validate_reference_provenance() -> None:
    for path, expected in REFERENCE_HASHES.items():
        actual = sha256(path)
        if actual != expected:
            raise AnalysisError(
                f"sealed reference hash changed for {relative(path)}: {actual}, expected {expected}"
            )
    inventory = read_sum_inventory(REFERENCE_SUMS)
    for path, expected in REFERENCE_HASHES.items():
        if path == REFERENCE_SUMS:
            continue
        if inventory.get(path.name) != expected:
            raise AnalysisError(f"sealed inventory does not own {path.name}")
    report = REFERENCE_REPORT.read_text(encoding="ascii")
    if "Status: `PASS`" not in report:
        raise AnalysisError("sealed reference validation report is not PASS")


def read_rows(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="ascii") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(fields):
                raise AnalysisError(f"{relative(path)}: exact schema mismatch")
            rows = list(reader)
    except UnicodeError as exc:
        raise AnalysisError(f"{relative(path)}: input is not ASCII") from exc
    for line_number, row in enumerate(rows, 2):
        if None in row or any(row.get(field) is None for field in fields):
            raise AnalysisError(f"{relative(path)}:{line_number}: surplus or missing fields")
    return rows


def number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisError(f"invalid numeric field {field}") from exc
    if not math.isfinite(value):
        raise AnalysisError(f"nonfinite numeric field {field}")
    return value


def exact_int(row: dict[str, str], field: str, *, positive: bool = False) -> int:
    value = number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9 or (positive and rounded < 1):
        qualifier = "positive exact integer" if positive else "exact integer"
        raise AnalysisError(f"{field}={value:.9f}, expected {qualifier}")
    return int(rounded)


def near(row: dict[str, str], field: str, expected: float, tolerance: float) -> None:
    value = number(row, field)
    if abs(value - expected) > tolerance:
        raise AnalysisError(
            f"{field}={value:.9f}, expected {expected:.9f} +/- {tolerance:.9f}"
        )


def bounded(row: dict[str, str], field: str, minimum: float, maximum: float) -> float:
    value = number(row, field)
    if not minimum <= value <= maximum:
        raise AnalysisError(f"{field}={value:.9f}, expected {minimum:.9f}..{maximum:.9f}")
    return value


def angular_error(value: float, target: float) -> float:
    return abs((value - target + 180.0) % 360.0 - 180.0)


def require_angle(row: dict[str, str], field: str, target: float) -> None:
    value = number(row, field)
    if angular_error(value, target) > 0.01:
        raise AnalysisError(f"{field}={value:.9f}, expected wrapped angle {target:.9f}")


def validate_identity(
    row: dict[str, str], campaign: int, mode: int, attempt: int
) -> None:
    for field, expected in (
        ("schema_version", 1),
        ("campaign_id", campaign),
        ("stage_mode", mode),
        ("attempt_id", attempt),
    ):
        if exact_int(row, field, positive=field != "stage_mode") != expected:
            raise AnalysisError(f"{field} does not match {campaign}/{mode}/{attempt}")


def pose_grid() -> tuple[tuple[int, int], ...]:
    poses: list[tuple[int, int]] = []
    poses.extend((0, c) for c in (0, 45, 90, 135, 180, 225, 270, 315, 0))
    for b_deg in (5, -5, 10, -10, 15, -15):
        poses.extend((b_deg, c) for c in (0, 45, 90, 180, 225, 270, 0))
    for b_deg in (30, -30, 45, -45):
        poses.extend((b_deg, c) for c in (0, 90, 180, 270, 0))
    poses.append((0, 0))
    for b_deg in (60, -60, 90, -90):
        poses.extend((b_deg, c) for c in (0, 90, 180, 270, 0))
    poses.extend((0, c) for c in (0, 45, 90, 135, 180, 225, 270, 315, 0))
    if len(poses) != EXPECTED_ROWS:
        raise AssertionError("internal T4 pose grid is not 101 rows")
    return tuple(poses)


def expected_rows() -> tuple[ExpectedRow, ...]:
    poses = pose_grid()
    rows: dict[int, ExpectedRow] = {}
    for block, first, last in T4_RANGES:
        for seq in range(first, last + 1):
            rows[seq] = ExpectedRow(
                seq,
                block,
                seq - first + 1,
                int(last > first and seq == last),
                poses[seq - 1],
            )
    if sorted(rows) != list(range(1, EXPECTED_ROWS + 1)):
        raise AssertionError("internal row ranges do not cover 1..101")
    return tuple(rows[seq] for seq in range(1, EXPECTED_ROWS + 1))


EXPECTED = expected_rows()
EXPECTED_BY_SEQ = {row.seq: row for row in EXPECTED}


def mapping_digest(keys: Sequence[tuple[int, int]]) -> str:
    text = "".join(
        f"{seq}:{b_deg}:{c_deg % 360}\n"
        for seq, (b_deg, c_deg) in enumerate(keys, 1)
    )
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def frame(b_deg: float, c_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    b = math.radians(b_deg)
    c = math.radians(c_deg)
    w = np.asarray(
        [-math.sin(b) * math.cos(c), -math.sin(b) * math.sin(c), -math.cos(b)]
    )
    u = np.asarray(
        [math.cos(b) * math.cos(c), math.cos(b) * math.sin(c), -math.sin(b)]
    )
    v = np.asarray([-math.sin(c), math.cos(c), 0.0])
    return w, u, v


def result_centers(
    rows: Sequence[dict[str, str]], campaign: int, mode: int, attempt: int
) -> tuple[np.ndarray, tuple[tuple[int, int], ...]]:
    if len(rows) != EXPECTED_ROWS:
        raise AnalysisError(f"result row count is {len(rows)}, expected {EXPECTED_ROWS}")
    centers: list[np.ndarray] = []
    keys: list[tuple[int, int]] = []
    for row, expected in zip(rows, EXPECTED):
        validate_identity(row, campaign, mode, attempt)
        for field, value in (
            ("sample_seq", expected.seq),
            ("block_id", expected.block),
            ("anchor_seq", expected.anchor_seq),
            ("is_closure", expected.is_closure),
            ("contact_count", 4),
            ("live_tool_number", TOOL),
        ):
            if exact_int(row, field) != value:
                raise AnalysisError(f"result seq {expected.seq}: {field} mismatch")
        require_angle(row, "abs_b_deg", expected.pose[0])
        require_angle(row, "abs_c_deg", expected.pose[1])
        expected_method = 2 if expected.pose[0] < 0 else 1
        if exact_int(row, "u_method_code") != expected_method:
            raise AnalysisError(f"result seq {expected.seq}: U-method mismatch")
        near(row, "expected_tool_length_mm", TOOL_LENGTH_MM, 0.002)
        near(row, "probe_calibration_offset_mm", PROBE_OFFSET_MM, 0.0005)
        near(row, "probe_diameter_mm", PROBE_DIAMETER_MM, 0.01)
        near(row, "effective_contact_radius_mm", EFFECTIVE_RADIUS_MM, 0.001)
        derived_radius = 15.0 + number(row, "probe_diameter_mm") / 2.0 - number(
            row, "probe_calibration_offset_mm"
        )
        if abs(number(row, "effective_contact_radius_mm") - derived_radius) > 1e-6:
            raise AnalysisError(f"result seq {expected.seq}: contact radius mismatch")

        u_correction = bounded(row, "u_center_correction_mm", -0.250, 0.250)
        v_correction = bounded(row, "v_center_correction_mm", -0.250, 0.250)
        correction_norm = bounded(row, "center_correction_norm_mm", 0.0, 0.250)
        if abs(correction_norm - math.hypot(u_correction, v_correction)) > 0.001:
            raise AnalysisError(f"result seq {expected.seq}: correction norm mismatch")
        bounded(row, "v_corrected_diameter_mm", 29.9, 30.5)
        bounded(row, "pass_center_delta_mm", 0.0, 0.100)
        for field_name in (
            "w_contact_radial_residual_mm",
            "u_contact_radial_residual_mm",
            "v_minus_contact_radial_residual_mm",
            "v_plus_contact_radial_residual_mm",
        ):
            bounded(row, field_name, 0.0, 0.250)
        bounded(row, "w_travel_mm", 1.0, 7.01)
        for field_name in ("u_travel_mm", "v_minus_travel_mm", "v_plus_travel_mm"):
            bounded(row, field_name, 1.0, 6.01)

        centers.append(
            np.asarray([number(row, f"center_abs_{axis}_mm") for axis in "xyz"])
        )
        keys.append(expected.pose)
    if mapping_digest(keys) != CANONICAL_MAPPING_SHA256:
        raise AnalysisError("sequence-indexed T4 pose mapping changed")
    return np.vstack(centers), tuple(keys)


def validate_states(
    rows: Sequence[dict[str, str]],
    results: Sequence[dict[str, str]],
    campaign: int,
    mode: int,
    attempt: int,
) -> None:
    if len(rows) != EXPECTED_ROWS:
        raise AnalysisError(f"state row count is {len(rows)}, expected {EXPECTED_ROWS}")
    for row, result, expected in zip(rows, results, EXPECTED):
        validate_identity(row, campaign, mode, attempt)
        if exact_int(row, "sample_seq") != expected.seq:
            raise AnalysisError(f"state seq {expected.seq}: sample sequence mismatch")
        for field, value in (
            ("persistent_correction_enabled", 1),
            ("tcpc_enabled", 1),
            ("twp_active", 0),
            ("twp_motion_enabled", 0),
            ("twp_valid", 0),
            ("b_ssi_invalid", 0),
            ("c_ssi_invalid", 0),
        ):
            if exact_int(row, field) != value:
                raise AnalysisError(f"state seq {expected.seq}: {field} mismatch")
        for field in (
            "motion_tooloffset_z_mm",
            "halui_tool_length_offset_z_mm",
            "kins_active_tool_offset_z_mm",
        ):
            near(row, field, TOOL_LENGTH_MM, 0.002)
        for field, target in (
            ("abs_b_deg", expected.pose[0]),
            ("joint_b_cmd_deg", expected.pose[0]),
            ("joint_b_fb_deg", expected.pose[0]),
            ("b_ssi_zeroed_deg", expected.pose[0]),
            ("abs_c_deg", expected.pose[1]),
            ("joint_c_cmd_deg", expected.pose[1]),
            ("joint_c_fb_deg", expected.pose[1]),
            ("c_ssi_zeroed_deg", -expected.pose[1]),
        ):
            require_angle(row, field, target)
        for joint in range(3):
            command = number(row, f"joint_{joint}_motor_pos_cmd_mm")
            feedback = number(row, f"joint_{joint}_motor_pos_fb_mm")
            logged = number(row, f"joint_{joint}_motor_following_error_fb_minus_cmd_mm")
            if abs((feedback - command) - logged) > 2e-6 or abs(logged) > 0.002:
                raise AnalysisError(f"state seq {expected.seq}: J{joint} state mismatch")

        center = np.asarray([number(result, f"center_abs_{axis}_mm") for axis in "xyz"])
        u_correction = number(result, "u_center_correction_mm")
        v_correction = number(result, "v_center_correction_mm")
        w, u, v = frame(*expected.pose)
        expected_endpoint = (
            center
            - u_correction * u
            - v_correction * v
            - w * (EFFECTIVE_RADIUS_MM + 5.0)
        )
        endpoint = np.asarray(
            [number(row, f"accepted_endpoint_abs_{axis}_mm") for axis in "xyz"]
        )
        if float(np.linalg.norm(endpoint - expected_endpoint)) > 0.030:
            raise AnalysisError(f"state seq {expected.seq}: accepted endpoint mismatch")


def validate_model_rows(
    rows: Sequence[dict[str, str]], campaign: int, mode: int, attempt: int
) -> tuple[dict[str, str], ...]:
    if len(rows) != EXPECTED_ROWS:
        raise AnalysisError(f"model-state row count is {len(rows)}, expected {EXPECTED_ROWS}")
    for row, expected in zip(rows, EXPECTED):
        validate_identity(row, campaign, mode, attempt)
        if exact_int(row, "sample_seq") != expected.seq:
            raise AnalysisError(f"model-state seq {expected.seq}: sequence mismatch")
        for field, value in (
            ("model_id", MODEL_ID),
            ("expected_model_id", MODEL_ID),
            ("configured", 1),
            ("valid", 1),
            ("fault_code", 0),
        ):
            if exact_int(row, field) != value:
                raise AnalysisError(f"model-state seq {expected.seq}: {field} mismatch")
        near(row, "q", 0.0, 1e-6)
        require_angle(row, "evaluated_b_deg", expected.pose[0])
        require_angle(row, "evaluated_c_deg", expected.pose[1])
        near(row, "evaluated_length_mm", TOOL_LENGTH_MM, 0.002)
        diff = np.asarray([number(row, f"diff_offset_{axis}_mm") for axis in "xyz"])
        diff_norm = number(row, "diff_offset_norm_mm")
        if np.max(np.abs(diff)) > 1e-6 or abs(diff_norm) > 1e-6:
            raise AnalysisError(f"model-state seq {expected.seq}: T4 q=0 differential is nonzero")
        if abs(diff_norm - float(np.linalg.norm(diff))) > 3e-6:
            raise AnalysisError(f"model-state seq {expected.seq}: differential norm mismatch")
        empirical = np.asarray(
            [number(row, f"empirical_offset_{axis}_mm") for axis in "xyz"]
        )
        empirical_norm = number(row, "empirical_offset_norm_mm")
        if not 0.0 <= empirical_norm <= 1.350:
            raise AnalysisError(f"model-state seq {expected.seq}: empirical norm exceeds cap")
        if abs(empirical_norm - float(np.linalg.norm(empirical))) > 5e-6:
            raise AnalysisError(f"model-state seq {expected.seq}: empirical norm mismatch")
    return tuple(rows)


def compare_model_rows(
    reference: Sequence[dict[str, str]], new: Sequence[dict[str, str]]
) -> None:
    for ref_row, new_row, expected in zip(reference, new, EXPECTED):
        ref_vector = np.asarray(
            [number(ref_row, f"empirical_offset_{axis}_mm") for axis in "xyz"]
        )
        new_vector = np.asarray(
            [number(new_row, f"empirical_offset_{axis}_mm") for axis in "xyz"]
        )
        if float(np.linalg.norm(new_vector - ref_vector)) > 2e-5:
            raise AnalysisError(
                f"model-state seq {expected.seq}: empirical q=0 vector differs from sealed reference"
            )


def validate_closures(
    rows: Sequence[dict[str, str]],
    results: Sequence[dict[str, str]],
    campaign: int,
    mode: int,
    attempt: int,
) -> ClosureSummary:
    if len(rows) != EXPECTED_CLOSURES:
        raise AnalysisError(f"closure row count is {len(rows)}, expected {EXPECTED_CLOSURES}")
    vectors: list[np.ndarray] = []
    norms: list[float] = []
    results_by_seq = {exact_int(row, "sample_seq"): row for row in results}
    for row, (block, first, last) in zip(rows, T4_CLOSURES):
        validate_identity(row, campaign, mode, attempt)
        for field, value in (
            ("block_id", block),
            ("open_sample_seq", first),
            ("close_sample_seq", last),
            ("pass", 1),
        ):
            if exact_int(row, field) != value:
                raise AnalysisError(f"closure block {block}: {field} mismatch")
        near(row, "limit_mm", CLOSURE_LIMIT_MM, 1e-9)
        open_center = np.asarray(
            [number(results_by_seq[first], f"center_abs_{axis}_mm") for axis in "xyz"]
        )
        close_center = np.asarray(
            [number(results_by_seq[last], f"center_abs_{axis}_mm") for axis in "xyz"]
        )
        vector = close_center - open_center
        logged = np.asarray([number(row, f"closure_d{axis}_mm") for axis in "xyz"])
        if float(np.linalg.norm(vector - logged)) > 3e-6:
            raise AnalysisError(f"closure block {block}: vector mismatch")
        norm = bounded(row, "closure_norm_mm", 0.0, CLOSURE_LIMIT_MM)
        if abs(norm - float(np.linalg.norm(vector))) > 3e-6:
            raise AnalysisError(f"closure block {block}: norm mismatch")
        require_angle(row, "abs_b_deg", EXPECTED_BY_SEQ[last].pose[0])
        require_angle(row, "abs_c_deg", EXPECTED_BY_SEQ[last].pose[1])
        vectors.append(vector)
        norms.append(norm)
    vector_array = np.vstack(vectors)
    norm_array = np.asarray(norms)
    worst = int(np.argmax(norm_array))
    return ClosureSummary(
        Metric(float(math.sqrt(np.mean(norm_array * norm_array))), float(norm_array[worst])),
        np.sqrt(np.mean(vector_array * vector_array, axis=0)),
        T4_CLOSURES[worst][0],
        T4_CLOSURES[worst][1],
        T4_CLOSURES[worst][2],
    )


def counter_tuple(row: dict[str, str], prefix: str) -> tuple[int, int, int]:
    return tuple(
        exact_int(row, f"{prefix}_{name}_count") for name in ("raw", "mux", "gated")
    )  # type: ignore[return-value]


def expected_transaction_keys() -> tuple[tuple[int, int, int, int], ...]:
    return tuple(
        (seq, 1, pass_id, contact_id)
        for seq in range(1, EXPECTED_ROWS + 1)
        for pass_id in (1, 2)
        for contact_id in (1, 2, 3, 4)
    )


def trace_key(
    row: dict[str, str], sequence_field: str, campaign: int, mode: int, attempt: int
) -> tuple[int, int, int, int]:
    validate_identity(row, campaign, mode, attempt)
    return (
        exact_int(row, sequence_field, positive=True),
        exact_int(row, "acquisition_try", positive=True),
        exact_int(row, "pass_id", positive=True),
        exact_int(row, "contact_id", positive=True),
    )


def validate_trace_pose(row: dict[str, str], seq: int) -> None:
    if seq not in EXPECTED_BY_SEQ:
        raise AnalysisError(f"trace sequence {seq} is outside 1..101")
    require_angle(row, "abs_b_deg", EXPECTED_BY_SEQ[seq].pose[0])
    require_angle(row, "abs_c_deg", EXPECTED_BY_SEQ[seq].pose[1])


def validate_pulses(
    contacts: Sequence[dict[str, str]],
    gaps: Sequence[dict[str, str]],
    campaign: int,
    mode: int,
    attempt: int,
) -> PulseSummary:
    if len(contacts) != EXPECTED_TRANSACTIONS or len(gaps) != EXPECTED_TRANSACTIONS:
        raise AnalysisError(
            f"contact/gap trace rows are {len(contacts)}/{len(gaps)}, expected 808/808"
        )
    expected_keys = expected_transaction_keys()
    contact_keys = tuple(
        trace_key(row, "global_seq", campaign, mode, attempt) for row in contacts
    )
    gap_keys = tuple(
        trace_key(row, "next_global_seq", campaign, mode, attempt) for row in gaps
    )
    if contact_keys != expected_keys or gap_keys != expected_keys:
        raise AnalysisError("contact/gap transaction order is not exact try1/pass1-2/contact1-4")

    direct_duplicates = 0
    delayed = 0
    contact_extra_transactions = 0
    contact_extra_edges = 0
    maximum_contact_extra = 0
    gated_contacts = 0
    previous_contact: dict[str, str] | None = None
    gap_extra_transactions = 0
    gap_extra_edges = 0
    maximum_combined_extra = 0

    for index, (contact, gap, key) in enumerate(zip(contacts, gaps, expected_keys)):
        seq, _, _, contact_id = key
        validate_trace_pose(contact, seq)
        pre = counter_tuple(contact, "pre")
        post = counter_tuple(contact, "post")
        ready = counter_tuple(contact, "ready")
        if any(value < 0 for value in pre + post + ready):
            raise AnalysisError(f"contact trace seq {seq}: negative counter")
        if any(not pre[i] <= post[i] <= ready[i] for i in range(3)):
            raise AnalysisError(f"contact trace seq {seq}: non-monotonic counter")
        direct = tuple(post[i] - pre[i] for i in range(3))
        repeats = tuple(ready[i] - post[i] for i in range(3))
        for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
            if exact_int(contact, field) != value:
                raise AnalysisError(f"contact trace seq {seq}: {field} mismatch")
        for field, value in zip(
            ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats
        ):
            if exact_int(contact, field) != value:
                raise AnalysisError(f"contact trace seq {seq}: {field} mismatch")
        if direct[0] != direct[1] or direct[0] < 1 or direct[2] != 1:
            raise AnalysisError(f"contact trace seq {seq}: G38 edge failure")
        if repeats[0] != repeats[1] or repeats[2] != 0:
            raise AnalysisError(f"contact trace seq {seq}: repeat-edge failure")
        extra = ready[0] - pre[0] - (ready[2] - pre[2])
        if exact_int(contact, "extra_raw_minus_gated_delta") != extra:
            raise AnalysisError(f"contact trace seq {seq}: extra-edge mismatch")
        if not 0 <= extra <= MAX_FILTERED_EXTRA_EDGES:
            raise AnalysisError(f"contact trace seq {seq}: filtered burst exceeds contract")
        for field in ("burst_flag", "consistency_fault", "release_fault", "terminal_failure"):
            if exact_int(contact, field) != 0:
                raise AnalysisError(f"contact trace seq {seq}: {field} is nonzero")
        if exact_int(contact, "probe_result") != 1:
            raise AnalysisError(f"contact trace seq {seq}: probe result is not success")
        travel = number(contact, "travel_mm")
        upper = 7.01 if contact_id == 1 else 6.01
        if not 1.0 <= travel <= upper:
            raise AnalysisError(f"contact trace seq {seq}: travel is outside bounds")

        validate_trace_pose(gap, seq)
        prior = counter_tuple(gap, "prior_ready")
        current = counter_tuple(gap, "current_pre")
        delta = tuple(current[i] - prior[i] for i in range(3))
        if any(value < 0 for value in prior + current + delta):
            raise AnalysisError(f"gap trace seq {seq}: invalid counter progression")
        for field, value in zip(("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"), delta):
            if exact_int(gap, field) != value:
                raise AnalysisError(f"gap trace seq {seq}: {field} mismatch")
        initial = exact_int(gap, "initial_baseline")
        if initial != int(index == 0):
            raise AnalysisError("only the first gap row may mark the initial baseline")
        prior_extra = exact_int(gap, "prior_contact_extra_delta")
        if previous_contact is None:
            if prior_extra != 0:
                raise AnalysisError("initial gap has a prior-contact extra")
        else:
            if prior != counter_tuple(previous_contact, "ready"):
                raise AnalysisError(f"gap trace seq {seq}: prior-ready boundary changed")
            if prior_extra != exact_int(previous_contact, "extra_raw_minus_gated_delta"):
                raise AnalysisError(f"gap trace seq {seq}: prior-contact extra changed")
        if current != pre:
            raise AnalysisError(f"gap trace seq {seq}: current-pre boundary changed")
        combined = prior_extra + delta[0] - delta[2]
        if exact_int(gap, "combined_extra_delta") != combined:
            raise AnalysisError(f"gap trace seq {seq}: combined-extra mismatch")
        if (
            delta[0] != delta[1]
            or delta[2] != 0
            or (initial == 1 and any(delta))
            or not 0 <= combined <= MAX_FILTERED_EXTRA_EDGES
        ):
            raise AnalysisError(f"gap trace seq {seq}: electrical gate failure")
        for field in ("burst_flag", "consistency_fault"):
            if exact_int(gap, field) != 0:
                raise AnalysisError(f"gap trace seq {seq}: {field} is nonzero")

        direct_duplicates += int(direct[0] > 1)
        delayed += int(repeats[0] > 0)
        contact_extra_transactions += int(extra > 0)
        contact_extra_edges += extra
        maximum_contact_extra = max(maximum_contact_extra, extra)
        gated_contacts += direct[2] + repeats[2]
        gap_extra_transactions += int(delta[0] > 0)
        gap_extra_edges += delta[0]
        maximum_combined_extra = max(maximum_combined_extra, combined)
        previous_contact = contact

    initial_counters = counter_tuple(contacts[0], "pre")
    terminal_counters = counter_tuple(contacts[-1], "ready")
    if gated_contacts != EXPECTED_TRANSACTIONS:
        raise AnalysisError(f"gated contacts are {gated_contacts}, expected 808")
    return PulseSummary(
        direct_duplicates,
        delayed,
        contact_extra_transactions,
        contact_extra_edges,
        gap_extra_transactions,
        gap_extra_edges,
        maximum_contact_extra,
        maximum_combined_extra,
        gated_contacts,
        *initial_counters,
        *terminal_counters,
    )


def centered(values: np.ndarray) -> np.ndarray:
    if values.ndim != 2 or values.shape[1] != 3 or not np.all(np.isfinite(values)):
        raise AnalysisError("center field must be finite Nx3")
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
        canonical = (key[0], key[1] % 360)
        if canonical not in grouped:
            order.append(canonical)
            grouped[canonical] = []
        grouped[canonical].append(index)
    if len(order) != EXPECTED_UNIQUE:
        raise AnalysisError(f"canonical collapse produced {len(order)} poses, expected 76")
    return tuple(order), tuple(tuple(grouped[key]) for key in order)


def collapse(values: np.ndarray, groups: Sequence[Sequence[int]]) -> np.ndarray:
    return np.vstack([np.mean(values[list(indices)], axis=0) for indices in groups])


def collapse_scalar(values: np.ndarray, groups: Sequence[Sequence[int]]) -> np.ndarray:
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise AnalysisError("scalar pose field must be finite and one-dimensional")
    return np.asarray([float(np.mean(values[list(indices)])) for indices in groups])


def scalar_stats(values: np.ndarray) -> ScalarStats:
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)):
        raise AnalysisError("scalar statistics require a finite nonempty vector")
    return ScalarStats(
        float(np.mean(values)),
        float(np.std(values)),
        float(np.min(values)),
        float(np.max(values)),
    )


def repeated_pose_scatter(
    values: np.ndarray, keys: Sequence[tuple[int, int]]
) -> RepeatedScatter:
    grouped: dict[tuple[int, int], list[int]] = {}
    for index, key in enumerate(keys):
        canonical = (key[0], key[1] % 360)
        grouped.setdefault(canonical, []).append(index)
    repeated = [indices for indices in grouped.values() if len(indices) > 1]
    if not repeated:
        raise AnalysisError("pose field has no repeated observations")
    residuals = np.vstack(
        [values[index] - np.mean(values[indices], axis=0) for indices in repeated for index in indices]
    )
    b0c0_indices = grouped.get((0, 0), [])
    if len(b0c0_indices) != 5:
        raise AnalysisError(f"B0/C0 repeat count is {len(b0c0_indices)}, expected 5")
    b0c0_values = values[b0c0_indices]
    return RepeatedScatter(
        len(repeated),
        len(residuals),
        residual_metric(residuals),
        np.sqrt(np.mean(residuals * residuals, axis=0)),
        len(b0c0_indices),
        center_metric(b0c0_values),
    )


def b0_drift(values: np.ndarray, keys: Sequence[tuple[int, int]]) -> B0Drift:
    # Seq 1/9 bracket the opening sweep, 72 is the midpoint, and 93/101
    # bracket the closing sweep.  All five observations are the same B0/C0 pose.
    groups = ((1, 9), (72,), (93, 101))
    for sequence in (1, 9, 72, 93, 101):
        if (keys[sequence - 1][0], keys[sequence - 1][1] % 360) != (0, 0):
            raise AnalysisError(f"sequence {sequence} is no longer B0/C0")
    opening = np.mean(values[[sequence - 1 for sequence in groups[0]]], axis=0)
    midpoint = values[groups[1][0] - 1].copy()
    closing = np.mean(values[[sequence - 1 for sequence in groups[2]]], axis=0)
    return B0Drift(
        opening,
        midpoint,
        closing,
        midpoint - opening,
        closing - opening,
    )


def load_run(
    label: str,
    base: Path,
    campaign: int,
    mode: int,
    attempt: int,
) -> RunData:
    result_path, state_path, model_path, closure_path, contact_path, gap_path = paths_for_base(base)
    results = read_rows(result_path, RESULT_FIELDS)
    states = read_rows(state_path, STATE_FIELDS)
    models = read_rows(model_path, MODEL_STATE_FIELDS)
    closures = read_rows(closure_path, CLOSURE_FIELDS)
    contacts = read_rows(contact_path, CONTACT_FIELDS)
    gaps = read_rows(gap_path, GAP_FIELDS)

    raw_centers, raw_keys = result_centers(results, campaign, mode, attempt)
    validate_states(states, results, campaign, mode, attempt)
    model_rows = validate_model_rows(models, campaign, mode, attempt)
    closure = validate_closures(closures, results, campaign, mode, attempt)
    pulse = validate_pulses(contacts, gaps, campaign, mode, attempt)
    unique_keys, groups = canonical_groups(raw_keys)
    unique_centers = collapse(raw_centers, groups)
    raw_diameters = np.asarray(
        [number(row, "v_corrected_diameter_mm") for row in results], dtype=float
    )
    raw_joint_commands = np.asarray(
        [
            [number(row, f"joint_{joint}_motor_pos_cmd_mm") for joint in range(3)]
            for row in states
        ],
        dtype=float,
    )
    return RunData(
        label,
        base,
        raw_centers,
        raw_keys,
        unique_centers,
        unique_keys,
        center_metric(raw_centers),
        center_metric(unique_centers),
        np.mean(raw_centers, axis=0),
        np.mean(unique_centers, axis=0),
        closure,
        pulse,
        raw_diameters,
        collapse_scalar(raw_diameters, groups),
        raw_joint_commands,
        collapse(raw_joint_commands, groups),
        repeated_pose_scatter(raw_centers, raw_keys),
        b0_drift(raw_centers, raw_keys),
        model_rows,
        paths_for_base(base),
    )


def subset_diagnostic(
    label: str,
    mask: np.ndarray,
    new_residuals: np.ndarray,
    delta: np.ndarray,
) -> GroupDiagnostic:
    if not np.any(mask):
        raise AnalysisError(f"diagnostic group {label} is empty")
    return GroupDiagnostic(
        label,
        int(np.sum(mask)),
        residual_metric(new_residuals[mask]),
        residual_metric(delta[mask]),
        np.sqrt(np.mean(delta[mask] * delta[mask], axis=0)),
    )


def group_diagnostics(
    keys: Sequence[tuple[int, int]],
    new_residuals: np.ndarray,
    delta: np.ndarray,
) -> tuple[
    tuple[GroupDiagnostic, ...],
    tuple[GroupDiagnostic, ...],
    tuple[GroupDiagnostic, ...],
]:
    b_values = np.asarray([key[0] for key in keys], dtype=int)
    c_values = np.asarray([key[1] % 360 for key in keys], dtype=int)
    signed = tuple(
        subset_diagnostic(f"B{value:+d}", b_values == value, new_residuals, delta)
        for value in sorted(set(b_values.tolist()))
    )
    absolute = tuple(
        subset_diagnostic(f"abs(B)={value}", np.abs(b_values) == value, new_residuals, delta)
        for value in sorted(set(np.abs(b_values).tolist()))
    )
    sectors = tuple(
        subset_diagnostic(f"C{value}", c_values == value, new_residuals, delta)
        for value in sorted(set(c_values.tolist()))
    )
    return signed, absolute, sectors


def paired_even_odd_diagnostics(
    keys: Sequence[tuple[int, int]], delta: np.ndarray
) -> tuple[tuple[PairDiagnostic, ...], tuple[PairBandDiagnostic, ...]]:
    by_pose = {(b_deg, c_deg % 360): delta[index] for index, (b_deg, c_deg) in enumerate(keys)}
    rows: list[PairDiagnostic] = []
    bands: list[PairBandDiagnostic] = []
    magnitudes = sorted({abs(b_deg) for b_deg, _ in by_pose if b_deg != 0})
    for magnitude in magnitudes:
        sectors = sorted(
            {c_deg for b_deg, c_deg in by_pose if b_deg == magnitude}
            & {c_deg for b_deg, c_deg in by_pose if b_deg == -magnitude}
        )
        if not sectors:
            continue
        even_values: list[np.ndarray] = []
        odd_values: list[np.ndarray] = []
        for c_sector in sectors:
            positive = by_pose[(magnitude, c_sector)]
            negative = by_pose[(-magnitude, c_sector)]
            even = (positive + negative) / 2.0
            odd = (positive - negative) / 2.0
            rows.append(PairDiagnostic(magnitude, c_sector, even, odd))
            even_values.append(even)
            odd_values.append(odd)
        even_array = np.vstack(even_values)
        odd_array = np.vstack(odd_values)
        bands.append(
            PairBandDiagnostic(
                magnitude,
                len(sectors),
                residual_metric(even_array),
                residual_metric(odd_array),
                np.sqrt(np.mean(even_array * even_array, axis=0)),
                np.sqrt(np.mean(odd_array * odd_array, axis=0)),
            )
        )
    if len(rows) != 34:
        raise AnalysisError(f"paired signed-B topology produced {len(rows)} pairs, expected 34")
    return tuple(rows), tuple(bands)


def location_classification(metric: Metric) -> str:
    if metric.rms > LOCATION_STRONG_RMS_MM or metric.maximum > LOCATION_STRONG_MAX_MM:
        return "STRONG"
    if metric.rms > LOCATION_MATERIAL_RMS_MM or metric.maximum > LOCATION_MATERIAL_MAX_MM:
        return "MATERIAL"
    return "NOMINAL"


def diameter_comparison(reference: RunData, new: RunData) -> DiameterComparison:
    delta = new.unique_diameters - reference.unique_diameters
    return DiameterComparison(
        scalar_stats(reference.unique_diameters),
        scalar_stats(new.unique_diameters),
        float(np.mean(delta)),
        float(math.sqrt(np.mean(delta * delta))),
        float(np.max(np.abs(delta))),
    )


def joint_relocation(reference: RunData, new: RunData) -> JointRelocation:
    delta = new.unique_joint_commands - reference.unique_joint_commands
    mean = np.mean(delta, axis=0)
    centered_delta = delta - mean
    return JointRelocation(
        mean,
        np.std(delta, axis=0),
        residual_metric(centered_delta),
    )


def analyze(new_base: Path = NEW_BASE) -> Comparison:
    validate_reference_provenance()
    reference = load_run(
        "sealed reference", REFERENCE_BASE, REFERENCE_CAMPAIGN, REFERENCE_MODE, REFERENCE_ATTEMPT
    )
    new = load_run("new location", new_base, NEW_CAMPAIGN, NEW_MODE, NEW_ATTEMPT)
    if reference.raw_keys != new.raw_keys or reference.unique_keys != new.unique_keys:
        raise AnalysisError("new-location pose mapping differs from the sealed reference")
    compare_model_rows(reference.model_rows, new.model_rows)

    # Each field is centered by its own single XYZ mean before posewise comparison.
    reference_raw_residuals = centered(reference.raw_centers)
    new_raw_residuals = centered(new.raw_centers)
    raw_delta = new_raw_residuals - reference_raw_residuals
    reference_residuals = centered(reference.unique_centers)
    new_residuals = centered(new.unique_centers)
    delta = new_residuals - reference_residuals
    raw_delta_metric = residual_metric(raw_delta)
    delta_metric = residual_metric(delta)
    raw_delta_axis_rms = np.sqrt(np.mean(raw_delta * raw_delta, axis=0))
    delta_axis_rms = np.sqrt(np.mean(delta * delta, axis=0))
    worst = int(np.argmax(np.linalg.norm(delta, axis=1)))
    signed, absolute, sectors = group_diagnostics(
        new.unique_keys, new_residuals, delta
    )
    pair_rows, pair_bands = paired_even_odd_diagnostics(new.unique_keys, delta)
    raw_displacement = new.raw_mean - reference.raw_mean
    unique_displacement = new.unique_mean - reference.unique_mean
    displacement_norm = float(np.linalg.norm(unique_displacement))
    purity = (
        abs(float(unique_displacement[0])) / displacement_norm
        if displacement_norm > 1e-12
        else None
    )
    return Comparison(
        reference,
        new,
        new.unique_metric.rms <= TRANSFER_RMS_LIMIT_MM
        and new.unique_metric.maximum <= TRANSFER_MAX_LIMIT_MM,
        location_classification(delta_metric),
        raw_delta_metric,
        raw_delta_axis_rms,
        delta_metric,
        delta_axis_rms,
        raw_displacement,
        unique_displacement,
        new.unique_keys[worst],
        delta[worst],
        signed,
        absolute,
        sectors,
        pair_rows,
        pair_bands,
        new.b0_drift.midpoint_from_opening - reference.b0_drift.midpoint_from_opening,
        new.b0_drift.closing_from_opening - reference.b0_drift.closing_from_opening,
        diameter_comparison(reference, new),
        joint_relocation(reference, new),
        purity,
    )


def vector_text(vector: np.ndarray) -> str:
    return ", ".join(f"{value:+.6f}" for value in vector)


def metric_text(metric: Metric) -> str:
    return f"{metric.rms:.6f} / {metric.maximum:.6f}"


def group_table(lines: list[str], title: str, groups: Iterable[GroupDiagnostic]) -> None:
    lines.extend(
        [
            f"### {title}",
            "",
            "All group metrics use the globally centered 76-pose fields; no group is recentered.",
            "",
            "| group | poses | new RMS / max (mm) | centered delta RMS / max (mm) | delta X/Y/Z component RMS (mm) |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for group in groups:
        lines.append(
            f"| {group.label} | {group.count} | `{metric_text(group.new_metric)}` | "
            f"`{metric_text(group.delta_metric)}` | `[{vector_text(group.delta_axis_rms)}]` |"
        )
    lines.append("")


def pair_tables(
    lines: list[str],
    bands: Sequence[PairBandDiagnostic],
    rows: Sequence[PairDiagnostic],
) -> None:
    lines.extend(
        [
            "### Paired Signed-B Even/Odd Components",
            "",
            "For every available +/-B pair at the same C sector, `r+` and `r-` are the centered new-minus-reference pose vectors. `E=(r+ + r-)/2` is the sign-even component and `O=(r+ - r-)/2` is the sign-odd component. Neither component is recentered.",
            "",
            "| abs(B) | pairs | E RMS / max (mm) | O RMS / max (mm) | E X/Y/Z RMS (mm) | O X/Y/Z RMS (mm) |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for band in bands:
        lines.append(
            f"| {band.abs_b} | {band.pair_count} | `{metric_text(band.even_metric)}` | "
            f"`{metric_text(band.odd_metric)}` | `[{vector_text(band.even_axis_rms)}]` | "
            f"`[{vector_text(band.odd_axis_rms)}]` |"
        )
    lines.extend(
        [
            "",
            "| abs(B) | C | E vector (mm) / norm | O vector (mm) / norm |",
            "| ---: | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.abs_b} | {row.c_sector} | `[{vector_text(row.even_vector)}] / "
            f"{float(np.linalg.norm(row.even_vector)):.6f}` | "
            f"`[{vector_text(row.odd_vector)}] / "
            f"{float(np.linalg.norm(row.odd_vector)):.6f}` |"
        )
    lines.append("")


def scalar_stats_text(stats: ScalarStats) -> str:
    return (
        f"mean {stats.mean:.6f}, SD {stats.standard_deviation:.6f}, "
        f"range {stats.minimum:.6f}..{stats.maximum:.6f}"
    )


def normalized_metric(metric: Metric, dx_mm: float) -> str:
    if abs(dx_mm) <= 1e-9:
        return "N/A (measured dX is zero)"
    scale = 1_000_000.0 / abs(dx_mm)
    return f"{metric.rms * scale:.3f} / {metric.maximum * scale:.3f} um/m"


def normalized_vector(vector: np.ndarray, dx_mm: float) -> str:
    if abs(dx_mm) <= 1e-9:
        return "N/A (measured dX is zero)"
    return f"[{vector_text(vector * (1_000_000.0 / abs(dx_mm)))}] um/m"


def pulse_row(label: str, pulse: PulseSummary) -> str:
    return (
        f"| {label} | {pulse.gated_contacts} | {pulse.direct_duplicate_transactions} | "
        f"{pulse.delayed_transactions} | {pulse.contact_extra_transactions} / "
        f"{pulse.contact_extra_edges} | {pulse.gap_extra_transactions} / "
        f"{pulse.gap_extra_edges} | {pulse.maximum_contact_extra} / "
        f"{pulse.maximum_combined_extra} | "
        f"{pulse.initial_raw}/{pulse.initial_mux}/{pulse.initial_gated} -> "
        f"{pulse.terminal_raw}/{pulse.terminal_mux}/{pulse.terminal_gated} |"
    )


def render_report(result: Comparison) -> str:
    new_hashes = {path: sha256(path) for path in result.new.files}
    worst_norm = float(np.linalg.norm(result.worst_pose_vector))
    transfer_label = "PASS" if result.transfer_pass else "FAIL"
    dx_mm = float(result.unique_mean_displacement[0])
    purity_text = (
        f"{result.location_purity_ratio:.6f} ({100.0 * result.location_purity_ratio:.3f}%)"
        if result.location_purity_ratio is not None
        else "N/A (zero mean displacement)"
    )
    lines = [
        "# TCPC Length-Aware T4 New-Location Comparison",
        "",
        f"Status: `ACQUISITION VALID` | `FROZEN-MODEL TRANSFER {transfer_label}` | `LOCATION-ASSOCIATED {result.location_classification}`",
        "",
        "## Scope",
        "",
        f"This compares campaign `{NEW_CAMPAIGN}/{NEW_MODE}/{NEW_ATTEMPT}` with the hash-sealed T4 Attempt 2 reference. Both acquisitions use T4/H4 `{TOOL_LENGTH_MM:.6f} mm`, model `{MODEL_ID}`, and the same 101-row/76-unique-pose mapping.",
        "",
        "`ACQUISITION VALID` means every recorded schema, identity, pose, state, model, closure, and probe-transaction contract passed. Frozen-model transfer is judged only on the new equal-76 absolute field at RMS/max limits `<= 0.120/0.280 mm`. It is independent of the location-change classification.",
        "",
        "## Headline Metrics",
        "",
        "| metric | sealed reference | new location |",
        "| --- | ---: | ---: |",
        f"| centered raw 101 RMS / max (mm) | `{metric_text(result.reference.raw_metric)}` | `{metric_text(result.new.raw_metric)}` |",
        f"| centered equal-unique 76 RMS / max (mm) | `{metric_text(result.reference.unique_metric)}` | `{metric_text(result.new.unique_metric)}` |",
        "",
        f"Frozen-model transfer is `{transfer_label}` because the new equal-76 result is `{metric_text(result.new.unique_metric)} mm` against `{TRANSFER_RMS_LIMIT_MM:.3f}/{TRANSFER_MAX_LIMIT_MM:.3f} mm`.",
        "",
        "Each raw-101 field and each equal-76 field is independently translated by one XYZ mean before its posewise comparison:",
        "",
        "| centered new-minus-reference delta | RMS / max (mm) | X/Y/Z component RMS (mm) |",
        "| --- | ---: | ---: |",
        f"| raw 101 rows | `{metric_text(result.raw_delta_metric)}` | `[{vector_text(result.raw_delta_axis_rms)}]` |",
        f"| equal-unique 76 poses | `{metric_text(result.delta_metric)}` | `[{vector_text(result.delta_axis_rms)}]` |",
        "",
        f"The equal-76 change is classified `LOCATION-ASSOCIATED {result.location_classification}`. `MATERIAL` begins when RMS is `> {LOCATION_MATERIAL_RMS_MM:.3f} mm` or max is `> {LOCATION_MATERIAL_MAX_MM:.3f} mm`; `STRONG` begins when RMS is `> {LOCATION_STRONG_RMS_MM:.3f} mm` or max is `> {LOCATION_STRONG_MAX_MM:.3f} mm`; otherwise it is `NOMINAL`.",
        "",
        f"The largest equal-76 centered change is `B{result.worst_pose[0]:+d}/C{result.worst_pose[1]}` with vector `[{vector_text(result.worst_pose_vector)}] mm` and norm `{worst_norm:.6f} mm`.",
        "",
        "## Mean Displacement",
        "",
        f"Raw-101 new-minus-reference mean center displacement is `[{vector_text(result.raw_mean_displacement)}] mm`, norm `{float(np.linalg.norm(result.raw_mean_displacement)):.6f} mm`.",
        "",
        f"Equal-76 new-minus-reference mean center displacement is `[{vector_text(result.unique_mean_displacement)}] mm`, norm `{float(np.linalg.norm(result.unique_mean_displacement)):.6f} mm`.",
        "",
        "These are the physical sphere-location translations plus any location-dependent mean bias. They are removed before the pose-pattern comparison and are not TCPC calibration errors by themselves.",
        "",
        f"The location-purity ratio is defined as `|dX| / ||dXYZ||` from the equal-76 mean displacement and is `{purity_text}`. It reports how closely this relocation follows X; it is not a data-quality or axis-alignment score.",
        "",
        f"Using measured `|dX|={abs(dx_mm):.6f} mm`, raw-101 centered delta RMS/max normalizes to `{normalized_metric(result.raw_delta_metric, dx_mm)}` and its X/Y/Z component RMS to `{normalized_vector(result.raw_delta_axis_rms, dx_mm)}`.",
        "",
        f"Equal-76 centered delta RMS/max normalizes to `{normalized_metric(result.delta_metric, dx_mm)}` and its X/Y/Z component RMS to `{normalized_vector(result.delta_axis_rms, dx_mm)}`.",
        "",
        "The um/m values are descriptive normalization by this run's measured dX, not an axis compensation slope. Two sphere locations are insufficient to build or justify a correction table.",
        "",
        "## Pose Diagnostics",
        "",
    ]
    group_table(lines, "Signed B", result.signed_b)
    group_table(lines, "Absolute-B Bands", result.abs_b)
    group_table(lines, "C Sectors", result.c_sectors)
    pair_tables(lines, result.pair_bands, result.pair_rows)
    lines.extend(
        [
            "The even/odd split helps describe whether the location-associated change is common to both B signs or reverses with B sign. It does not by itself isolate B-axis alignment from X/Y/Z rail, head, spindle, probe seating, or sphere seating effects.",
            "",
            "## B0/C0 Drift And Repeat Scatter",
            "",
            "Opening is the mean of sequences 1 and 9, midpoint is sequence 72, and closing is the mean of sequences 93 and 101. All are B0/C0.",
            "",
            "| acquisition | opening center XYZ (mm) | midpoint center XYZ (mm) | closing center XYZ (mm) | midpoint-opening (mm) / norm | closing-opening (mm) / norm |",
            "| --- | --- | --- | --- | --- | --- |",
            f"| sealed reference | `[{vector_text(result.reference.b0_drift.opening)}]` | `[{vector_text(result.reference.b0_drift.midpoint)}]` | `[{vector_text(result.reference.b0_drift.closing)}]` | `[{vector_text(result.reference.b0_drift.midpoint_from_opening)}] / {float(np.linalg.norm(result.reference.b0_drift.midpoint_from_opening)):.6f}` | `[{vector_text(result.reference.b0_drift.closing_from_opening)}] / {float(np.linalg.norm(result.reference.b0_drift.closing_from_opening)):.6f}` |",
            f"| new location | `[{vector_text(result.new.b0_drift.opening)}]` | `[{vector_text(result.new.b0_drift.midpoint)}]` | `[{vector_text(result.new.b0_drift.closing)}]` | `[{vector_text(result.new.b0_drift.midpoint_from_opening)}] / {float(np.linalg.norm(result.new.b0_drift.midpoint_from_opening)):.6f}` | `[{vector_text(result.new.b0_drift.closing_from_opening)}] / {float(np.linalg.norm(result.new.b0_drift.closing_from_opening)):.6f}` |",
            "",
            f"New-minus-reference change in midpoint-opening drift is `[{vector_text(result.b0_midpoint_drift_delta)}] mm`, norm `{float(np.linalg.norm(result.b0_midpoint_drift_delta)):.6f} mm`; the change in closing-opening drift is `[{vector_text(result.b0_closing_drift_delta)}] mm`, norm `{float(np.linalg.norm(result.b0_closing_drift_delta)):.6f} mm`.",
            "",
            "Repeated-pose scatter pools each observation's XYZ deviation from its own canonical-pose mean. It includes only canonical poses recorded more than once.",
            "",
            "| acquisition | repeated groups / observations | pooled RMS / max (mm) | X/Y/Z RMS (mm) | B0/C0 observations, RMS / max (mm) |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| sealed reference | `{result.reference.repeated_scatter.group_count} / {result.reference.repeated_scatter.observation_count}` | `{metric_text(result.reference.repeated_scatter.metric)}` | `[{vector_text(result.reference.repeated_scatter.axis_rms)}]` | `{result.reference.repeated_scatter.b0c0_count}, {metric_text(result.reference.repeated_scatter.b0c0_metric)}` |",
            f"| new location | `{result.new.repeated_scatter.group_count} / {result.new.repeated_scatter.observation_count}` | `{metric_text(result.new.repeated_scatter.metric)}` | `[{vector_text(result.new.repeated_scatter.axis_rms)}]` | `{result.new.repeated_scatter.b0c0_count}, {metric_text(result.new.repeated_scatter.b0c0_metric)}` |",
            "",
            "Repeated-pose scatter and B0/C0 drift include time-order effects such as thermal drift and seating repeatability; they are not pure spatial calibration terms.",
            "",
            "## Diameter And Joint Relocation",
            "",
            "Equal-76 v-corrected diameter statistics:",
            "",
            "| field | statistics (mm) |",
            "| --- | --- |",
            f"| sealed reference | `{scalar_stats_text(result.diameter.reference)}` |",
            f"| new location | `{scalar_stats_text(result.diameter.new)}` |",
            f"| paired new-reference delta | `mean {result.diameter.delta_mean:+.6f}, RMS {result.diameter.delta_rms:.6f}, max absolute {result.diameter.delta_maximum_absolute:.6f}` |",
            "",
            "The equal-76 paired relocation of accepted J0/J1/J2 motor-position commands is:",
            "",
            f"- mean: `[{vector_text(result.joint_relocation.mean)}] mm`",
            f"- component standard deviation: `[{vector_text(result.joint_relocation.axis_standard_deviation)}] mm`",
            f"- centered vector spread RMS / max: `{metric_text(result.joint_relocation.centered_metric)} mm`",
            "",
            "Joint-command relocation is reported as execution geometry evidence. It is not substituted for the independently centered TCP sphere-field comparison.",
            "",
            "## Closures",
            "",
            "| acquisition | closure RMS / max (mm) | vector X/Y/Z RMS (mm) | worst block (open->close) |",
            "| --- | ---: | ---: | --- |",
            f"| sealed reference | `{metric_text(result.reference.closure.metric)}` | `[{vector_text(result.reference.closure.axis_rms)}]` | `{result.reference.closure.worst_block}` (`{result.reference.closure.worst_open_seq}->{result.reference.closure.worst_close_seq}`) |",
            f"| new location | `{metric_text(result.new.closure.metric)}` | `[{vector_text(result.new.closure.axis_rms)}]` | `{result.new.closure.worst_block}` (`{result.new.closure.worst_open_seq}->{result.new.closure.worst_close_seq}`) |",
            "",
            f"All `{EXPECTED_CLOSURES}` closures in each acquisition passed the runner's `{CLOSURE_LIMIT_MM:.3f} mm` gate. Closure is repeatability evidence within a run, not an absolute accuracy measurement.",
            "",
            "## Probe-Pulse Diagnostics",
            "",
            "| acquisition | gated contacts | direct duplicate tx | delayed tx | contact extras tx / edges | gap extras tx / edges | max contact / combined extras | initial -> terminal raw/mux/gated |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            pulse_row("sealed reference", result.reference.pulse),
            pulse_row("new location", result.new.pulse),
            "",
            f"Both traces contain exactly `{EXPECTED_TRANSACTIONS}` successful gated G38 contacts. Raw/mux counters match, no repeat reached the gated input, and every accepted transaction stayed within the bounded `{MAX_FILTERED_EXTRA_EDGES}`-extra-edge contract.",
            "",
            "## Integrity And Provenance",
            "",
            "The analyzer validated exact schemas and identities for all six files, ordered result/state/model rows, tool and TLO values, the canonical pose topology, T4 q=0 model snapshots, empirical model vectors against the sealed reference, closure mappings/vectors, and every contact/gap counter boundary. No absolute-accuracy threshold is used to decide acquisition validity; the frozen-model transfer decision is reported separately.",
            "",
            f"Analyzer: `{relative(Path(__file__).resolve())}` SHA-256 `{sha256(Path(__file__).resolve())}`.",
            "",
            "### Sealed reference inputs",
            "",
            "| input | required SHA-256 |",
            "| --- | --- |",
        ]
    )
    for path, digest in REFERENCE_HASHES.items():
        lines.append(f"| `{relative(path)}` | `{digest}` |")
    lines.extend(
        [
            "",
            "### New-location inputs at analysis time",
            "",
            "| input | computed SHA-256 |",
            "| --- | --- |",
        ]
    )
    for path, digest in new_hashes.items():
        lines.append(f"| `{relative(path)}` | `{digest}` |")
    lines.extend(
        [
            "",
            "This analyzer imports no controller module, reads no live state, issues no machine command, fits no coefficient, and generates no correction table.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_python_safety() -> None:
    source = Path(__file__).read_text(encoding="ascii")
    tree = ast.parse(source, filename=__file__)
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
    if mapping_digest(pose_grid()) != CANONICAL_MAPPING_SHA256:
        raise AssertionError("canonical mapping digest changed")
    values = np.asarray([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    metric = center_metric(values)
    if abs(metric.rms - 1.0) > 1e-15 or abs(metric.maximum - 1.0) > 1e-15:
        raise AssertionError("centered metric formula failed")
    translated = values + np.asarray([100.0, -20.0, 7.0])
    if float(np.max(np.abs(centered(translated) - centered(values)))) > 1e-15:
        raise AssertionError("independent translation removal failed")

    validate_reference_provenance()
    reference = load_run(
        "sealed reference", REFERENCE_BASE, REFERENCE_CAMPAIGN, REFERENCE_MODE, REFERENCE_ATTEMPT
    )
    expected_metrics = (
        (reference.raw_metric.rms, 0.1051635465071548),
        (reference.raw_metric.maximum, 0.24525298589163422),
        (reference.unique_metric.rms, 0.10758912508070545),
        (reference.unique_metric.maximum, 0.24171008318074322),
        (reference.closure.metric.rms, 0.022237265685748582),
        (reference.closure.metric.maximum, 0.040366),
    )
    if any(abs(actual - expected) > 1e-12 for actual, expected in expected_metrics):
        raise AssertionError("sealed reference metric changed")
    if reference.pulse != PulseSummary(
        0, 14, 14, 14, 1, 1, 1, 1, 808, 0, 0, 0, 823, 823, 808
    ):
        raise AssertionError(f"sealed reference pulse summary changed: {reference.pulse}")
    expected_repeat = (
        reference.repeated_scatter.group_count,
        reference.repeated_scatter.observation_count,
        reference.repeated_scatter.metric.rms,
        reference.repeated_scatter.metric.maximum,
        reference.repeated_scatter.b0c0_count,
    )
    wanted_repeat = (22, 47, 0.011118787244722591, 0.02596107135367291, 5)
    if any(
        abs(float(actual) - float(expected)) > 1e-12
        for actual, expected in zip(expected_repeat, wanted_repeat)
    ):
        raise AssertionError("sealed repeated-pose diagnostic changed")

    if location_classification(Metric(0.050, 0.100)) != "NOMINAL":
        raise AssertionError("nominal location threshold changed")
    if location_classification(Metric(0.100, 0.200)) != "MATERIAL":
        raise AssertionError("material location threshold changed")
    if location_classification(Metric(0.100001, 0.200)) != "STRONG":
        raise AssertionError("strong location threshold changed")

    test_delta = np.zeros_like(reference.unique_centers)
    pose_index = {key: index for index, key in enumerate(reference.unique_keys)}
    test_delta[pose_index[(5, 0)]] = [2.0, 4.0, 6.0]
    test_delta[pose_index[(-5, 0)]] = [0.0, 2.0, 4.0]
    pair_rows, pair_bands = paired_even_odd_diagnostics(reference.unique_keys, test_delta)
    pair = next(row for row in pair_rows if row.abs_b == 5 and row.c_sector == 0)
    if (
        len(pair_rows) != 34
        or [band.pair_count for band in pair_bands] != [6, 6, 6, 4, 4, 4, 4]
        or not np.array_equal(pair.even_vector, [1.0, 3.0, 5.0])
        or not np.array_equal(pair.odd_vector, [1.0, 1.0, 1.0])
    ):
        raise AssertionError("paired even/odd diagnostic failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--new-base",
        type=Path,
        default=NEW_BASE,
        help="path prefix before -results.csv and the other five suffixes",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--check", action="store_true", help="compare the existing report byte-for-byte"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("T4 new-location comparison analyzer self-test: PASS")
            return 0
        report = render_report(analyze(args.new_base))
        report.encode("ascii")
        if args.check:
            existing = args.report.read_text(encoding="ascii")
            if existing != report:
                raise AnalysisError("comparison report differs from deterministic analyzer output")
            print("T4 new-location comparison report check: PASS")
            return 0
        args.report.write_text(report, encoding="ascii")
        print(f"wrote {args.report}")
        print("T4 new-location diagnostic comparison: COMPLETE")
        return 0
    except (AnalysisError, OSError, UnicodeError, ValueError) as exc:
        print(f"T4 new-location diagnostic comparison: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
