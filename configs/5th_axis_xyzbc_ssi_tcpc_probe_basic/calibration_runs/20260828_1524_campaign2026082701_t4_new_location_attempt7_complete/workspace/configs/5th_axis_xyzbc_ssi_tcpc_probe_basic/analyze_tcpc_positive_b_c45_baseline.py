#!/usr/bin/env python3
"""Validate the positive-B C45 TCPC baseline as one leg or a matched pair.

The input retains the established 46-column accepted-pose schema. A companion
grid file defines canonical slot IDs, including intentionally unsafe slots that
must not appear in the measurement CSV. The analysis is descriptive only: a
T3 -> T4 sequence cannot separate tool-length behavior from elapsed drift or
probe reseating without a closing T3 leg.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import sys
import tempfile
from collections import defaultdict
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "tcpc-positive-b-c45-baseline-results.csv"
DEFAULT_GRID = SCRIPT_DIR / "tcpc-positive-b-c45-baseline-grid.csv"

CAMPAIGN_ID = 2026082202
STAGE_MODE = 19
SHORT_TOOL = 3
LONG_TOOL = 4
SHORT_LENGTH_MM = 128.606729
LONG_LENGTH_MM = 229.407000
LENGTH_SEPARATION_MM = LONG_LENGTH_MM - SHORT_LENGTH_MM
SHORT_CAL_OFFSET_MM = 0.117658
LONG_CAL_OFFSET_MM = 0.154742

TLO_TOL_MM = 0.002
CAL_OFFSET_TOL_MM = 0.0005
DIAMETER_TOL_MM = 0.01
ROTARY_TOL_DEG = 0.01
POSE_TOL_DEG = 1e-6
FOLLOWING_ERROR_CONSISTENCY_TOL_MM = 2e-6
ACQUISITION_CENTER_TOL_MM_BY_LEG = {
    1: 0.10,  # Historical T3 acquisition contract remains strict.
    2: 2.00,  # T4 acquisition was released with the operator-approved limit.
}
QA_DIAMETER_MIN_MM = 29.9
QA_DIAMETER_MAX_MM = 30.5
CLOSURE_LIMIT_MM = 0.05
EXCELLENT_CLOSURE_MM = 0.01

EXIT_ACCEPTED = 0
EXIT_DATA_QUALITY = 1
EXIT_INPUT_ERROR = 2

LEG_NAMES = {1: "S1/T3 short", 2: "L/T4 long"}
LEG_EXPECTATIONS = {
    1: (SHORT_TOOL, SHORT_LENGTH_MM, SHORT_CAL_OFFSET_MM),
    2: (LONG_TOOL, LONG_LENGTH_MM, LONG_CAL_OFFSET_MM),
}
GROUP_ENDPOINTS = {
    0.0: (1, 9),
    5.0: (10, 18),
    15.0: (19, 27),
    30.0: (28, 36),
}
OUTER_CLOSURE = (1, 37)
UNSAFE_SLOT_IDS = frozenset((13, 17, 22, 26, 31, 35))
REQUIRED_SLOT_IDS = tuple(slot for slot in range(1, 38) if slot not in UNSAFE_SLOT_IDS)

Vec3 = tuple[float, float, float]
Pose = tuple[float, float]

GRID_COLUMNS = (
    "slot_id",
    "abs_b_deg",
    "abs_c_deg",
    "role",
    "status",
    "reason",
)

REQUIRED_COLUMNS = (
    "campaign_id",
    "leg_id",
    "stage_mode",
    "attempt_id",
    "sample_seq",
    "abs_b_deg",
    "abs_c_deg",
    "live_tool_number",
    "expected_tool_length_mm",
    "probe_calibration_offset_mm",
    "probe_diameter_mm",
    "persistent_correction_enabled",
    "tcpc_enabled",
    "twp_active",
    "twp_motion_enabled",
    "twp_valid",
    "b_ssi_invalid",
    "c_ssi_invalid",
    "center_abs_x_mm",
    "center_abs_y_mm",
    "center_abs_z_mm",
    "u_center_error_mm",
    "v_center_error_mm",
    "u_corrected_diameter_mm",
    "v_corrected_diameter_mm",
    "motion_tooloffset_z_mm",
    "halui_tool_length_offset_z_mm",
    "kins_active_tool_offset_z_mm",
    "joint_b_cmd_deg",
    "joint_b_fb_deg",
    "joint_c_cmd_deg",
    "joint_c_fb_deg",
    "b_ssi_zeroed_deg",
    "c_ssi_zeroed_deg",
    "accepted_endpoint_abs_x_mm",
    "accepted_endpoint_abs_y_mm",
    "accepted_endpoint_abs_z_mm",
    "joint_0_motor_pos_cmd_mm",
    "joint_0_motor_pos_fb_mm",
    "joint_0_motor_following_error_fb_minus_cmd_mm",
    "joint_1_motor_pos_cmd_mm",
    "joint_1_motor_pos_fb_mm",
    "joint_1_motor_following_error_fb_minus_cmd_mm",
    "joint_2_motor_pos_cmd_mm",
    "joint_2_motor_pos_fb_mm",
    "joint_2_motor_following_error_fb_minus_cmd_mm",
)

DERIVED_COLUMNS = (
    "campaign_id",
    "stage_mode",
    "short_attempt_id",
    "long_attempt_id",
    "slot_id",
    "semantic_role",
    "grid_status",
    "grid_reason",
    "abs_b_deg",
    "abs_c_deg",
    "short_absolute_center_x_mm",
    "short_absolute_center_y_mm",
    "short_absolute_center_z_mm",
    "long_absolute_center_x_mm",
    "long_absolute_center_y_mm",
    "long_absolute_center_z_mm",
    "raw_long_minus_short_x_mm",
    "raw_long_minus_short_y_mm",
    "raw_long_minus_short_z_mm",
    "raw_long_minus_short_norm_mm",
    "short_group_c0_relative_x_mm",
    "short_group_c0_relative_y_mm",
    "short_group_c0_relative_z_mm",
    "long_group_c0_relative_x_mm",
    "long_group_c0_relative_y_mm",
    "long_group_c0_relative_z_mm",
    "c_shape_long_minus_short_x_mm",
    "c_shape_long_minus_short_y_mm",
    "c_shape_long_minus_short_z_mm",
    "c_shape_long_minus_short_norm_mm",
    "short_b0_same_c_relative_x_mm",
    "short_b0_same_c_relative_y_mm",
    "short_b0_same_c_relative_z_mm",
    "long_b0_same_c_relative_x_mm",
    "long_b0_same_c_relative_y_mm",
    "long_b0_same_c_relative_z_mm",
    "b0_referenced_long_minus_short_x_mm",
    "b0_referenced_long_minus_short_y_mm",
    "b0_referenced_long_minus_short_z_mm",
    "b0_referenced_long_minus_short_norm_mm",
    "length_slope_x",
    "length_slope_y",
    "length_slope_z",
    "length_slope_norm_rad_approx",
    "length_slope_norm_deg_approx",
    "short_u_center_error_mm",
    "short_v_center_error_mm",
    "short_u_corrected_diameter_mm",
    "short_v_corrected_diameter_mm",
    "long_u_center_error_mm",
    "long_v_center_error_mm",
    "long_u_corrected_diameter_mm",
    "long_v_corrected_diameter_mm",
)


class AnalysisError(ValueError):
    """The input schema, grid, sequence, or invocation is invalid."""


class DataQualityError(ValueError):
    """The logged state or selected data fails a quality gate."""


@dataclass(frozen=True)
class GridSlot:
    slot_id: int
    pose: Pose
    role: str
    status: str
    reason: str


@dataclass(frozen=True)
class GridSpec:
    slots: tuple[GridSlot, ...]
    by_id: dict[int, GridSlot]
    required: tuple[GridSlot, ...]
    unsafe: tuple[GridSlot, ...]


@dataclass(frozen=True)
class Row:
    source_order: int
    line: int
    campaign_id: int
    leg_id: int
    attempt_id: int
    slot_id: int
    pose: Pose
    calibration_offset: float
    center: Vec3
    u_error: float
    v_error: float
    u_diameter: float
    v_diameter: float
    accepted_endpoint: Vec3
    linear_motor_cmd: Vec3
    linear_motor_fb: Vec3
    linear_following_error: Vec3


@dataclass(frozen=True)
class MatchedSample:
    slot: GridSlot
    rows: dict[int, Row]
    raw_long_minus_short: Vec3
    group_relative: dict[int, Vec3]
    c_shape_long_minus_short: Vec3
    b0_same_c_relative: dict[int, Vec3] | None
    b0_referenced_long_minus_short: Vec3 | None
    length_slope: Vec3 | None


@dataclass(frozen=True)
class ClosureResult:
    leg_id: int
    label: str
    first_slot: int
    last_slot: int
    vector: Vec3


@dataclass(frozen=True)
class LegResult:
    leg_id: int
    selected_attempt_id: int
    selected_rows: tuple[Row, ...]
    ignored_attempts: tuple[str, ...]
    group_references: dict[float, Vec3]
    closures: tuple[ClosureResult, ...]


@dataclass(frozen=True)
class BaselineResult:
    selected_attempts: dict[int, int]
    selected_rows: dict[int, tuple[Row, ...]]
    ignored_attempts: tuple[str, ...]
    group_references: dict[int, dict[float, Vec3]]
    b0_same_c_references: dict[int, dict[float, Vec3]]
    closures: tuple[ClosureResult, ...]
    samples: tuple[MatchedSample, ...]


@dataclass(frozen=True)
class QualityAssessment:
    passed: bool
    failures: tuple[str, ...]
    advisories: tuple[str, ...]


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec3, factor: float) -> Vec3:
    return (a[0] * factor, a[1] * factor, a[2] * factor)


def norm(a: Vec3) -> float:
    return math.sqrt(sum(value * value for value in a))


def mean_vec(values: Sequence[Vec3]) -> Vec3:
    if not values:
        raise AnalysisError("cannot average an empty vector set")
    return (
        sum(value[0] for value in values) / len(values),
        sum(value[1] for value in values) / len(values),
        sum(value[2] for value in values) / len(values),
    )


def rms_max(vectors: Iterable[Vec3]) -> tuple[float, float]:
    magnitudes = [norm(vector) for vector in vectors]
    if not magnitudes:
        return (0.0, 0.0)
    return (
        math.sqrt(sum(value * value for value in magnitudes) / len(magnitudes)),
        max(magnitudes),
    )


def angular_difference_deg(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def parse_float(raw: dict[str, str], name: str, line: int) -> float:
    value_text = raw.get(name)
    if value_text is None or not value_text.strip():
        raise AnalysisError(f"line {line}: missing value for {name}")
    try:
        value = float(value_text)
    except ValueError as exc:
        raise AnalysisError(f"line {line}: invalid {name}={value_text!r}") from exc
    if not math.isfinite(value):
        raise AnalysisError(f"line {line}: non-finite {name}={value_text!r}")
    return value


def parse_int(raw: dict[str, str], name: str, line: int) -> int:
    value = parse_float(raw, name, line)
    rounded = round(value)
    if abs(value - rounded) > 1e-6:
        raise AnalysisError(f"line {line}: {name} must be integral, got {value}")
    return int(rounded)


def require_near(
    line: int,
    name: str,
    actual: float,
    expected: float,
    tolerance: float,
) -> None:
    if abs(actual - expected) > tolerance:
        raise DataQualityError(
            f"line {line}: {name}={actual:.9f}, expected {expected:.9f} "
            f"+/- {tolerance:.6f}"
        )


def require_flag(line: int, name: str, actual: float, expected: int) -> None:
    require_near(line, name, actual, float(expected), 1e-6)


def expected_grid_layout() -> tuple[GridSlot, ...]:
    slots: list[GridSlot] = []
    slot_id = 1
    c_sequence = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 0.0)
    for b_deg in (0.0, 5.0, 15.0, 30.0):
        prefix = f"B{int(b_deg)}"
        for index, c_deg in enumerate(c_sequence):
            if index == 0:
                role = f"{prefix}_group_open"
            elif index == len(c_sequence) - 1:
                role = f"{prefix}_group_close"
            elif slot_id in UNSAFE_SLOT_IDS:
                role = f"{prefix}_unsafe_skip"
            else:
                role = f"{prefix}_measure"
            status = "unsafe_skip" if slot_id in UNSAFE_SLOT_IDS else "required"
            slots.append(GridSlot(slot_id, (b_deg, c_deg), role, status, ""))
            slot_id += 1
    slots.append(GridSlot(37, (0.0, 0.0), "outer_B0_close", "required", ""))
    return tuple(slots)


def load_grid(path: Path) -> GridSpec:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != GRID_COLUMNS:
                raise AnalysisError(
                    f"grid header must exactly match {GRID_COLUMNS}; got {reader.fieldnames}"
                )
            slots: list[GridSlot] = []
            for raw in reader:
                line = reader.line_num
                if None in raw:
                    raise AnalysisError(
                        f"grid line {line}: row has more than {len(GRID_COLUMNS)} fields"
                    )
                slot_id = parse_int(raw, "slot_id", line)
                b_deg = parse_float(raw, "abs_b_deg", line)
                c_deg = parse_float(raw, "abs_c_deg", line)
                role = (raw.get("role") or "").strip()
                status = (raw.get("status") or "").strip()
                reason = (raw.get("reason") or "").strip()
                if not role:
                    raise AnalysisError(f"grid line {line}: role is empty")
                if status not in ("required", "unsafe_skip"):
                    raise AnalysisError(
                        f"grid line {line}: status must be required or unsafe_skip"
                    )
                if status == "unsafe_skip" and not reason:
                    raise AnalysisError(
                        f"grid line {line}: unsafe_skip slot requires a reason"
                    )
                slots.append(GridSlot(slot_id, (b_deg, c_deg), role, status, reason))
    except AnalysisError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AnalysisError(f"cannot read grid {path}: {exc}") from exc

    expected = expected_grid_layout()
    if len(slots) != len(expected):
        raise AnalysisError(
            f"grid must contain exactly {len(expected)} canonical slots, got {len(slots)}"
        )
    canonical_slots: list[GridSlot] = []
    for actual, wanted in zip(slots, expected):
        if actual.slot_id != wanted.slot_id:
            raise AnalysisError(
                f"grid slot order mismatch: got {actual.slot_id}, expected {wanted.slot_id}"
            )
        if actual.role != wanted.role or actual.status != wanted.status:
            raise AnalysisError(
                f"grid slot {actual.slot_id}: role/status {(actual.role, actual.status)} "
                f"does not match {(wanted.role, wanted.status)}"
            )
        if (
            abs(actual.pose[0] - wanted.pose[0]) > POSE_TOL_DEG
            or angular_difference_deg(actual.pose[1], wanted.pose[1]) > POSE_TOL_DEG
        ):
            raise AnalysisError(
                f"grid slot {actual.slot_id}: pose {actual.pose} does not match {wanted.pose}"
            )
        canonical_slots.append(
            GridSlot(
                actual.slot_id,
                wanted.pose,
                actual.role,
                actual.status,
                actual.reason,
            )
        )

    slots = canonical_slots

    by_id = {slot.slot_id: slot for slot in slots}
    if len(by_id) != len(slots):
        raise AnalysisError("grid contains duplicate slot IDs")
    required = tuple(slot for slot in slots if slot.status == "required")
    unsafe = tuple(slot for slot in slots if slot.status == "unsafe_skip")
    if tuple(slot.slot_id for slot in required) != REQUIRED_SLOT_IDS:
        raise AnalysisError("grid required-slot set does not match the reviewed baseline")
    if frozenset(slot.slot_id for slot in unsafe) != UNSAFE_SLOT_IDS:
        raise AnalysisError("grid unsafe-slot set does not match the reviewed baseline")
    return GridSpec(tuple(slots), by_id, required, unsafe)


def validate_rotary(line: int, raw: dict[str, str], b_deg: float, c_deg: float) -> None:
    b_cmd = parse_float(raw, "joint_b_cmd_deg", line)
    b_fb = parse_float(raw, "joint_b_fb_deg", line)
    c_cmd = parse_float(raw, "joint_c_cmd_deg", line)
    c_fb = parse_float(raw, "joint_c_fb_deg", line)
    b_ssi = parse_float(raw, "b_ssi_zeroed_deg", line)
    c_ssi = parse_float(raw, "c_ssi_zeroed_deg", line)
    comparisons = (
        ("joint_b_cmd_deg", b_cmd, b_deg, False),
        ("joint_b_fb_deg", b_fb, b_cmd, False),
        ("b_ssi_zeroed_deg", b_ssi, b_cmd, True),
        ("joint_c_cmd_deg", c_cmd, c_deg, True),
        ("joint_c_fb_deg", c_fb, c_cmd, True),
        ("c_ssi_zeroed_deg", c_ssi, -c_cmd, True),
    )
    for name, actual, expected, wraps in comparisons:
        difference = (
            angular_difference_deg(actual, expected)
            if wraps
            else abs(actual - expected)
        )
        if difference > ROTARY_TOL_DEG:
            raise DataQualityError(
                f"line {line}: {name} differs from its reference by "
                f"{difference:.6f} deg (limit {ROTARY_TOL_DEG:.6f})"
            )


def parse_linear_axis_state(
    raw: dict[str, str],
    line: int,
) -> tuple[Vec3, Vec3, Vec3, Vec3]:
    endpoint = tuple(
        parse_float(raw, f"accepted_endpoint_abs_{axis}_mm", line)
        for axis in "xyz"
    )
    motor_cmd = tuple(
        parse_float(raw, f"joint_{joint}_motor_pos_cmd_mm", line)
        for joint in range(3)
    )
    motor_fb = tuple(
        parse_float(raw, f"joint_{joint}_motor_pos_fb_mm", line)
        for joint in range(3)
    )
    following_error = tuple(
        parse_float(
            raw,
            f"joint_{joint}_motor_following_error_fb_minus_cmd_mm",
            line,
        )
        for joint in range(3)
    )
    for joint, (command, feedback, logged_error) in enumerate(
        zip(motor_cmd, motor_fb, following_error)
    ):
        calculated_error = feedback - command
        if abs(logged_error - calculated_error) > FOLLOWING_ERROR_CONSISTENCY_TOL_MM:
            raise DataQualityError(
                f"line {line}: joint {joint} logged following error "
                f"{logged_error:.9f} mm does not equal feedback minus command "
                f"{calculated_error:.9f} mm within "
                f"{FOLLOWING_ERROR_CONSISTENCY_TOL_MM:.9f} mm"
            )
    return endpoint, motor_cmd, motor_fb, following_error  # type: ignore[return-value]


def parse_row(raw: dict[str, str], source_order: int, line: int) -> Row:
    campaign_id = parse_int(raw, "campaign_id", line)
    if campaign_id != CAMPAIGN_ID:
        raise AnalysisError(
            f"line {line}: campaign_id must be {CAMPAIGN_ID}, got {campaign_id}"
        )
    stage_mode = parse_int(raw, "stage_mode", line)
    if stage_mode != STAGE_MODE:
        raise AnalysisError(f"line {line}: stage_mode must be {STAGE_MODE}, got {stage_mode}")
    leg_id = parse_int(raw, "leg_id", line)
    if leg_id not in LEG_EXPECTATIONS:
        raise AnalysisError(f"line {line}: leg_id must be 1 or 2, got {leg_id}")
    attempt_id = parse_int(raw, "attempt_id", line)
    if attempt_id <= 0:
        raise AnalysisError(f"line {line}: attempt_id must be positive")
    slot_id = parse_int(raw, "sample_seq", line)
    b_deg = parse_float(raw, "abs_b_deg", line)
    c_deg = parse_float(raw, "abs_c_deg", line)

    expected_tool, expected_length, expected_calibration = LEG_EXPECTATIONS[leg_id]
    live_tool = parse_int(raw, "live_tool_number", line)
    if live_tool != expected_tool:
        raise DataQualityError(
            f"line {line}: leg {leg_id} requires T{expected_tool}, got T{live_tool}"
        )
    tlo_values = (
        parse_float(raw, "expected_tool_length_mm", line),
        parse_float(raw, "motion_tooloffset_z_mm", line),
        parse_float(raw, "halui_tool_length_offset_z_mm", line),
        parse_float(raw, "kins_active_tool_offset_z_mm", line),
    )
    tlo_names = (
        "expected_tool_length_mm",
        "motion_tooloffset_z_mm",
        "halui_tool_length_offset_z_mm",
        "kins_active_tool_offset_z_mm",
    )
    for name, value in zip(tlo_names, tlo_values):
        require_near(line, name, value, expected_length, TLO_TOL_MM)
    if max(tlo_values) - min(tlo_values) > TLO_TOL_MM:
        raise DataQualityError(
            f"line {line}: expected/live Z tool offsets span "
            f"{max(tlo_values) - min(tlo_values):.6f} mm "
            f"(limit {TLO_TOL_MM:.6f})"
        )

    require_near(
        line,
        "probe_diameter_mm",
        parse_float(raw, "probe_diameter_mm", line),
        6.0,
        DIAMETER_TOL_MM,
    )
    calibration_offset = parse_float(raw, "probe_calibration_offset_mm", line)
    require_near(
        line,
        "probe_calibration_offset_mm",
        calibration_offset,
        expected_calibration,
        CAL_OFFSET_TOL_MM,
    )

    for name, expected in (
        ("persistent_correction_enabled", 1),
        ("tcpc_enabled", 1),
        ("twp_active", 0),
        ("twp_motion_enabled", 0),
        ("twp_valid", 0),
        ("b_ssi_invalid", 0),
        ("c_ssi_invalid", 0),
    ):
        require_flag(line, name, parse_float(raw, name, line), expected)

    u_error = parse_float(raw, "u_center_error_mm", line)
    v_error = parse_float(raw, "v_center_error_mm", line)
    acquisition_center_limit = ACQUISITION_CENTER_TOL_MM_BY_LEG[leg_id]
    center_error_norm = math.hypot(u_error, v_error)
    if center_error_norm > acquisition_center_limit:
        raise DataQualityError(
            f"line {line}: U/V centering residual ({u_error:.6f}, {v_error:.6f}) "
            f"has norm {center_error_norm:.6f} mm, exceeding leg-{leg_id} "
            f"acquisition limit {acquisition_center_limit:.3f} mm"
        )
    u_diameter = parse_float(raw, "u_corrected_diameter_mm", line)
    v_diameter = parse_float(raw, "v_corrected_diameter_mm", line)
    for name, diameter in (
        ("u_corrected_diameter_mm", u_diameter),
        ("v_corrected_diameter_mm", v_diameter),
    ):
        if not QA_DIAMETER_MIN_MM <= diameter <= QA_DIAMETER_MAX_MM:
            raise DataQualityError(
                f"line {line}: {name}={diameter:.6f} outside "
                f"[{QA_DIAMETER_MIN_MM:.1f}, {QA_DIAMETER_MAX_MM:.1f}] mm"
            )

    validate_rotary(line, raw, b_deg, c_deg)
    center = tuple(
        parse_float(raw, f"center_abs_{axis}_mm", line) for axis in "xyz"
    )
    endpoint, motor_cmd, motor_fb, following_error = parse_linear_axis_state(raw, line)
    return Row(
        source_order=source_order,
        line=line,
        campaign_id=campaign_id,
        leg_id=leg_id,
        attempt_id=attempt_id,
        slot_id=slot_id,
        pose=(b_deg, c_deg),
        calibration_offset=calibration_offset,
        center=center,  # type: ignore[arg-type]
        u_error=u_error,
        v_error=v_error,
        u_diameter=u_diameter,
        v_diameter=v_diameter,
        accepted_endpoint=endpoint,
        linear_motor_cmd=motor_cmd,
        linear_motor_fb=motor_fb,
        linear_following_error=following_error,
    )


def validate_calibration_offsets(rows: Sequence[Row]) -> None:
    for leg_id in LEG_EXPECTATIONS:
        values = [row.calibration_offset for row in rows if row.leg_id == leg_id]
        if not values:
            continue
        spread = max(values) - min(values)
        if spread > CAL_OFFSET_TOL_MM:
            raise DataQualityError(
                f"{LEG_NAMES[leg_id]} calibration offset range is {spread:.6f} mm "
                f"(limit {CAL_OFFSET_TOL_MM:.6f})"
            )


def read_rows(path: Path) -> list[Row]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
                raise AnalysisError(
                    f"CSV header must exactly match the {len(REQUIRED_COLUMNS)}-column "
                    f"baseline schema; got {reader.fieldnames}"
                )
            rows: list[Row] = []
            for source_order, raw in enumerate(reader, start=1):
                line = reader.line_num
                if None in raw:
                    raise AnalysisError(
                        f"line {line}: row has more than {len(REQUIRED_COLUMNS)} fields"
                    )
                rows.append(parse_row(raw, source_order, line))
    except AnalysisError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AnalysisError(f"cannot read {path}: {exc}") from exc
    if not rows:
        raise AnalysisError(f"{path} contains a header but no data rows")
    validate_calibration_offsets(rows)
    return rows


def pose_matches(actual: Pose, expected: Pose) -> bool:
    return (
        abs(actual[0] - expected[0]) <= POSE_TOL_DEG
        and angular_difference_deg(actual[1], expected[1]) <= POSE_TOL_DEG
    )


def validate_source_order(rows: Sequence[Row]) -> None:
    run_blocks: list[tuple[int, int]] = []
    for row in rows:
        key = (row.leg_id, row.attempt_id)
        if not run_blocks or run_blocks[-1] != key:
            run_blocks.append(key)
    if len(run_blocks) != len(set(run_blocks)):
        raise AnalysisError(f"a leg/attempt block was interleaved or reused: {run_blocks}")
    leg_order = [leg for leg, _attempt in run_blocks]
    if leg_order != sorted(leg_order):
        raise AnalysisError(
            f"source order must be T3 short then T4 long; observed leg blocks {leg_order}"
        )
    for leg_id in LEG_EXPECTATIONS:
        attempts = [attempt for leg, attempt in run_blocks if leg == leg_id]
        if attempts != sorted(set(attempts)):
            raise AnalysisError(
                f"{LEG_NAMES[leg_id]} attempt IDs are reused or out of order: {attempts}"
            )


def validate_attempt_prefix(
    leg_id: int,
    attempt_id: int,
    rows: Sequence[Row],
    grid: GridSpec,
) -> None:
    if len(rows) > len(grid.required):
        raise AnalysisError(
            f"{LEG_NAMES[leg_id]} attempt {attempt_id}: got {len(rows)} rows, "
            f"more than {len(grid.required)} required slots"
        )
    for index, row in enumerate(rows):
        expected = grid.required[index]
        if row.slot_id != expected.slot_id:
            raise AnalysisError(
                f"{LEG_NAMES[leg_id]} attempt {attempt_id} row {row.line}: "
                f"slot {row.slot_id}, expected canonical slot {expected.slot_id}"
            )
        if not pose_matches(row.pose, expected.pose):
            raise AnalysisError(
                f"{LEG_NAMES[leg_id]} attempt {attempt_id} slot {row.slot_id}: "
                f"pose {row.pose} does not match grid pose {expected.pose}"
            )


def select_attempt(
    leg_id: int,
    rows: Sequence[Row],
    grid: GridSpec,
) -> tuple[int, tuple[Row, ...], list[str]]:
    attempts: dict[int, list[Row]] = defaultdict(list)
    for row in rows:
        attempts[row.attempt_id].append(row)
    complete: list[int] = []
    notes: list[str] = []
    for attempt_id in sorted(attempts):
        attempt_rows = attempts[attempt_id]
        validate_attempt_prefix(leg_id, attempt_id, attempt_rows, grid)
        if len(attempt_rows) == len(grid.required):
            complete.append(attempt_id)
        else:
            next_slot = grid.required[len(attempt_rows)].slot_id
            notes.append(
                f"{LEG_NAMES[leg_id]} attempt {attempt_id}: ignored canonical partial "
                f"{len(attempt_rows)}/{len(grid.required)}; next required slot {next_slot}"
            )
    if not complete:
        raise DataQualityError(
            f"{LEG_NAMES[leg_id]} has no complete valid attempt; "
            f"available attempts={sorted(attempts)}"
        )
    selected = max(complete)
    for attempt_id in complete:
        if attempt_id != selected:
            notes.append(
                f"{LEG_NAMES[leg_id]} attempt {attempt_id}: ignored complete superseded "
                f"by deterministic highest complete attempt {selected}"
            )
    return selected, tuple(attempts[selected]), notes


def analyze_leg(rows: Sequence[Row], grid: GridSpec, leg_id: int) -> LegResult:
    if leg_id not in LEG_EXPECTATIONS:
        raise AnalysisError(f"leg-only selection must be 1 or 2, got {leg_id}")
    leg_rows = [row for row in rows if row.leg_id == leg_id]
    if not leg_rows:
        raise DataQualityError(f"missing required {LEG_NAMES[leg_id]} leg")
    validate_source_order(leg_rows)

    attempt_id, selected, notes = select_attempt(leg_id, leg_rows, grid)
    by_slot = {row.slot_id: row for row in selected}
    group_references: dict[float, Vec3] = {}
    closures: list[ClosureResult] = []
    for b_deg, (opening, closing) in GROUP_ENDPOINTS.items():
        group_references[b_deg] = mean_vec(
            (by_slot[opening].center, by_slot[closing].center)
        )
        closures.append(
            ClosureResult(
                leg_id,
                f"B{b_deg:g} C0 within-group",
                opening,
                closing,
                sub(by_slot[closing].center, by_slot[opening].center),
            )
        )
    outer_open, outer_close = OUTER_CLOSURE
    closures.append(
        ClosureResult(
            leg_id,
            "outer B0 C0 first-to-last",
            outer_open,
            outer_close,
            sub(by_slot[outer_close].center, by_slot[outer_open].center),
        )
    )
    return LegResult(
        leg_id=leg_id,
        selected_attempt_id=attempt_id,
        selected_rows=selected,
        ignored_attempts=tuple(notes),
        group_references=group_references,
        closures=tuple(closures),
    )


def analyze_rows(rows: Sequence[Row], grid: GridSpec) -> BaselineResult:
    validate_source_order(rows)
    legs = {leg_id: analyze_leg(rows, grid, leg_id) for leg_id in LEG_EXPECTATIONS}

    selected_attempts = {
        leg_id: result.selected_attempt_id for leg_id, result in legs.items()
    }
    selected_rows = {leg_id: result.selected_rows for leg_id, result in legs.items()}
    ignored_attempts = tuple(
        note for leg_id in LEG_EXPECTATIONS for note in legs[leg_id].ignored_attempts
    )
    by_slot = {
        leg_id: {row.slot_id: row for row in selected_rows[leg_id]}
        for leg_id in LEG_EXPECTATIONS
    }
    group_references = {
        leg_id: result.group_references for leg_id, result in legs.items()
    }

    b0_same_c_references: dict[int, dict[float, Vec3]] = {1: {}, 2: {}}
    for leg_id in LEG_EXPECTATIONS:
        b0_same_c_references[leg_id][0.0] = group_references[leg_id][0.0]
        for slot_id in range(2, 9):
            row = by_slot[leg_id][slot_id]
            canonical_c = grid.by_id[slot_id].pose[1]
            b0_same_c_references[leg_id][canonical_c] = row.center

    closures = tuple(
        closure
        for leg_id in LEG_EXPECTATIONS
        for closure in legs[leg_id].closures
    )

    samples: list[MatchedSample] = []
    for slot in grid.required:
        short = by_slot[1][slot.slot_id]
        long = by_slot[2][slot.slot_id]
        raw_delta = sub(long.center, short.center)
        short_group_rel = sub(short.center, group_references[1][slot.pose[0]])
        long_group_rel = sub(long.center, group_references[2][slot.pose[0]])
        c_shape = sub(long_group_rel, short_group_rel)

        b0_relative: dict[int, Vec3] | None = None
        b0_delta: Vec3 | None = None
        length_slope: Vec3 | None = None
        if slot.pose[0] > POSE_TOL_DEG:
            reference_c = (
                0.0
                if angular_difference_deg(slot.pose[1], 0.0) <= POSE_TOL_DEG
                else slot.pose[1]
            )
            b0_relative = {
                1: sub(short.center, b0_same_c_references[1][reference_c]),
                2: sub(long.center, b0_same_c_references[2][reference_c]),
            }
            b0_delta = sub(b0_relative[2], b0_relative[1])
            length_slope = scale(b0_delta, 1.0 / LENGTH_SEPARATION_MM)

        samples.append(
            MatchedSample(
                slot=slot,
                rows={1: short, 2: long},
                raw_long_minus_short=raw_delta,
                group_relative={1: short_group_rel, 2: long_group_rel},
                c_shape_long_minus_short=c_shape,
                b0_same_c_relative=b0_relative,
                b0_referenced_long_minus_short=b0_delta,
                length_slope=length_slope,
            )
        )

    return BaselineResult(
        selected_attempts=selected_attempts,
        selected_rows=selected_rows,
        ignored_attempts=ignored_attempts,
        group_references=group_references,
        b0_same_c_references=b0_same_c_references,
        closures=closures,
        samples=tuple(samples),
    )


def evaluate_closures(closures: Sequence[ClosureResult]) -> QualityAssessment:
    failures: list[str] = []
    advisories: list[str] = []
    for closure in closures:
        magnitude = norm(closure.vector)
        prefix = f"{LEG_NAMES[closure.leg_id]} {closure.label} closure"
        if magnitude > CLOSURE_LIMIT_MM:
            failures.append(
                f"{prefix} {magnitude:.6f} mm exceeds {CLOSURE_LIMIT_MM:.6f} mm"
            )
        elif magnitude > EXCELLENT_CLOSURE_MM:
            advisories.append(
                f"{prefix} {magnitude:.6f} mm passes the data-quality limit but "
                f"exceeds the {EXCELLENT_CLOSURE_MM:.6f} mm excellent-result scale"
            )
    return QualityAssessment(not failures, tuple(failures), tuple(advisories))


def evaluate_leg_quality(result: LegResult) -> QualityAssessment:
    return evaluate_closures(result.closures)


def evaluate_quality(result: BaselineResult) -> QualityAssessment:
    return evaluate_closures(result.closures)


def vec_text(vector: Vec3) -> str:
    return f"({vector[0]:+.6f}, {vector[1]:+.6f}, {vector[2]:+.6f})"


def optional_vec_text(vector: Vec3 | None) -> str:
    return "n/a" if vector is None else vec_text(vector)


def metric_text(vectors: Iterable[Vec3]) -> str:
    rms, maximum = rms_max(vectors)
    return f"{rms:.6f}/{maximum:.6f}"


def format_group_summaries(result: BaselineResult) -> list[str]:
    lines = [
        "B-group RMS/max mm (raw L-S1 | group-C0-referenced C-shape | "
        "B0-same-C-referenced L-S1):"
    ]
    for b_deg in GROUP_ENDPOINTS:
        group = [
            sample
            for sample in result.samples
            if sample.slot.slot_id <= 36
            and abs(sample.slot.pose[0] - b_deg) <= POSE_TOL_DEG
        ]
        raw_metric = metric_text(sample.raw_long_minus_short for sample in group)
        c_shape_metric = metric_text(
            sample.c_shape_long_minus_short for sample in group
        )
        b0_vectors = [
            sample.b0_referenced_long_minus_short
            for sample in group
            if sample.b0_referenced_long_minus_short is not None
        ]
        b0_metric = "n/a" if not b0_vectors else metric_text(b0_vectors)
        lines.append(
            f"  B{b_deg:+g}: n={len(group)}  {raw_metric} | "
            f"{c_shape_metric} | {b0_metric}"
        )

    lines.append(
        "C-angle RMS/max mm across matched slots "
        "(raw L-S1 | group-C0-referenced C-shape):"
    )
    by_c: dict[float, list[MatchedSample]] = defaultdict(list)
    for sample in result.samples:
        if sample.slot.slot_id <= 36:
            by_c[sample.slot.pose[1]].append(sample)
    for c_deg in sorted(by_c):
        group = by_c[c_deg]
        lines.append(
            f"  C{c_deg:g}: n={len(group)}  "
            f"{metric_text(sample.raw_long_minus_short for sample in group)} | "
            f"{metric_text(sample.c_shape_long_minus_short for sample in group)}"
        )
    return lines


def format_leg_state_range(leg_id: int, rows: Sequence[Row]) -> str:
    u_diameters = [row.u_diameter for row in rows]
    v_diameters = [row.v_diameter for row in rows]
    max_u_error = max(abs(row.u_error) for row in rows)
    max_v_error = max(abs(row.v_error) for row in rows)
    max_center_error_norm = max(math.hypot(row.u_error, row.v_error) for row in rows)
    max_ferror = max(
        abs(value) for row in rows for value in row.linear_following_error
    )
    return (
        f"  {LEG_NAMES[leg_id]}: U diameter "
        f"{min(u_diameters):.6f}..{max(u_diameters):.6f} mm; "
        f"V diameter {min(v_diameters):.6f}..{max(v_diameters):.6f} mm; "
        f"max |U/V center| {max_u_error:.6f}/{max_v_error:.6f} mm; "
        f"max center norm {max_center_error_norm:.6f} mm; acquisition norm limit "
        f"{ACQUISITION_CENTER_TOL_MM_BY_LEG[leg_id]:.3f} mm; "
        f"max |logged linear ferror| {max_ferror:.9f} mm"
    )


def format_state_ranges(result: BaselineResult) -> list[str]:
    return [
        "selected-row probe/axis QA ranges:",
        *(
            format_leg_state_range(leg_id, result.selected_rows[leg_id])
            for leg_id in LEG_EXPECTATIONS
        ),
    ]


def format_leg_report(
    input_path: Path,
    grid_path: Path,
    input_row_count: int,
    grid: GridSpec,
    result: LegResult,
    assessment: QualityAssessment | None = None,
) -> str:
    if assessment is None:
        assessment = evaluate_leg_quality(result)
    status = "PASS" if assessment.passed else "FAIL"
    target_input_count = sum(
        1 for row in result.selected_rows if row.leg_id == result.leg_id
    )
    lines = [
        "TCPC positive-B C45 single-leg validation",
        "validation mode: one complete leg; cross-leg calculations: not performed",
        f"CSV data-quality status: {status}",
        f"source: {input_path}",
        f"grid: {grid_path}",
        f"campaign/stage: {CAMPAIGN_ID}/{STAGE_MODE}",
        f"selected leg: {result.leg_id} ({LEG_NAMES[result.leg_id]}); "
        f"attempt={result.selected_attempt_id}",
        f"rows: {input_row_count} input / {target_input_count} selected for this leg; "
        f"required slots: {len(grid.required)}",
        "sequence: every required canonical slot is present in exact order; "
        "unsafe gaps are explicit and C0 open/close occurrences are retained",
        "missing required slots in selected leg: none",
        "exit codes: 0=CSV quality pass, 1=data-quality/acceptance fail, "
        "2=input/schema/grid/sequence error",
    ]
    for failure in assessment.failures:
        lines.append(f"FAIL: {failure}")
    for advisory in assessment.advisories:
        lines.append(f"ADVISORY: {advisory}")
    for note in result.ignored_attempts:
        lines.append(f"WARNING: {note}")

    lines.append("unsafe grid slots omitted from selected leg:")
    for slot in grid.unsafe:
        lines.append(
            f"  slot {slot.slot_id}: B{slot.pose[0]:g} C{slot.pose[1]:g} "
            f"{slot.role}; reason={slot.reason}"
        )
    annotated_required = [slot for slot in grid.required if slot.reason]
    lines.append("required grid slots with clearance annotations:")
    for slot in annotated_required:
        lines.append(
            f"  slot {slot.slot_id}: B{slot.pose[0]:g} C{slot.pose[1]:g} "
            f"{slot.role}; reason={slot.reason}"
        )

    lines.append("closure evidence [quality gate <=0.050000 mm]:")
    for closure in result.closures:
        closure_norm = norm(closure.vector)
        closure_status = "PASS" if closure_norm <= CLOSURE_LIMIT_MM else "FAIL"
        lines.append(
            f"  {LEG_NAMES[closure.leg_id]} {closure.label} "
            f"slots {closure.first_slot}->{closure.last_slot}: "
            f"{vec_text(closure.vector)} mm; norm {closure_norm:.6f} "
            f"[{closure_status}]"
        )
    lines.extend(
        (
            "selected-row probe/axis QA ranges:",
            format_leg_state_range(result.leg_id, result.selected_rows),
            "group C0 reference means:",
            "  " + LEG_NAMES[result.leg_id] + ": " + ", ".join(
                f"B{b_deg:g}={vec_text(reference)}"
                for b_deg, reference in result.group_references.items()
            ) + " mm",
        )
    )
    return "\n".join(lines)


def format_report(
    input_path: Path,
    grid_path: Path,
    input_row_count: int,
    grid: GridSpec,
    result: BaselineResult,
    assessment: QualityAssessment | None = None,
) -> str:
    if assessment is None:
        assessment = evaluate_quality(result)
    status = "PASS" if assessment.passed else "FAIL"
    selected_count = sum(len(rows) for rows in result.selected_rows.values())
    lines = [
        "TCPC positive-B C45 two-leg baseline analysis",
        f"CSV data-quality status: {status}",
        f"source: {input_path}",
        f"grid: {grid_path}",
        f"campaign/stage: {CAMPAIGN_ID}/{STAGE_MODE}",
        f"rows: {input_row_count} input / {selected_count} selected; "
        f"matched required slots: {len(result.samples)}",
        f"selected attempts: short={result.selected_attempts[1]}, "
        f"long={result.selected_attempts[2]}",
        f"tool-length separation: {LENGTH_SEPARATION_MM:.6f} mm",
        "sequence: canonical slot IDs retained; unsafe gaps are explicit and "
        "C0 open/close occurrences are not collapsed",
        "exit codes: 0=CSV quality pass, 1=data-quality/acceptance fail, "
        "2=input/schema/grid/sequence error",
        "CAVEAT - NO S2: raw L-S1 includes elapsed drift, probe reseating, and "
        "tool-specific offsets; it is not a bracketed effective center offset.",
        "CAVEAT - POSITIVE B ONLY: odd/even B behavior, B-zero error, pivot error, "
        "and length scale are not uniquely separable.",
        "CAVEAT - UNSAFE SLOTS: intentionally omitted poses are not measured, "
        "imputed, fitted, or included in aggregate metrics.",
    ]
    for failure in assessment.failures:
        lines.append(f"FAIL: {failure}")
    for advisory in assessment.advisories:
        lines.append(f"ADVISORY: {advisory}")
    for note in result.ignored_attempts:
        lines.append(f"WARNING: {note}")

    lines.append("unsafe grid slots omitted from both selected legs:")
    for slot in grid.unsafe:
        lines.append(
            f"  slot {slot.slot_id}: B{slot.pose[0]:g} C{slot.pose[1]:g} "
            f"{slot.role}; reason={slot.reason}"
        )
    annotated_required = [slot for slot in grid.required if slot.reason]
    lines.append("required grid slots with clearance annotations:")
    for slot in annotated_required:
        lines.append(
            f"  slot {slot.slot_id}: B{slot.pose[0]:g} C{slot.pose[1]:g} "
            f"{slot.role}; reason={slot.reason}"
        )
    lines.append("missing required slots in selected legs: none")

    lines.append("closure evidence [quality gate <=0.050000 mm]:")
    closures_by_key: dict[tuple[str, int, int], dict[int, ClosureResult]] = defaultdict(dict)
    for closure in result.closures:
        closure_norm = norm(closure.vector)
        closure_status = "PASS" if closure_norm <= CLOSURE_LIMIT_MM else "FAIL"
        lines.append(
            f"  {LEG_NAMES[closure.leg_id]} {closure.label} "
            f"slots {closure.first_slot}->{closure.last_slot}: "
            f"{vec_text(closure.vector)} mm; norm {closure_norm:.6f} [{closure_status}]"
        )
        key = (closure.label, closure.first_slot, closure.last_slot)
        closures_by_key[key][closure.leg_id] = closure
    lines.append("differential closure diagnostics [long closure - short closure]:")
    for (label, first_slot, last_slot), closures in closures_by_key.items():
        differential = sub(closures[2].vector, closures[1].vector)
        lines.append(
            f"  {label} slots {first_slot}->{last_slot}: "
            f"{vec_text(differential)} mm; norm {norm(differential):.6f}"
        )

    lines.extend(format_state_ranges(result))
    lines.append("group C0 reference means:")
    for leg_id in LEG_EXPECTATIONS:
        references = ", ".join(
            f"B{b_deg:g}={vec_text(reference)}"
            for b_deg, reference in result.group_references[leg_id].items()
        )
        lines.append(f"  {LEG_NAMES[leg_id]}: {references} mm")
    lines.extend(format_group_summaries(result))

    lines.append("matched accepted slots:")
    lines.append(
        "  slot role              B      C      raw L-S1 XYZ mm               "
        "C-shape XYZ mm                B0-ref L-S1 XYZ mm             "
        "|B0-ref| slope(rad)"
    )
    for sample in result.samples:
        b0_delta = sample.b0_referenced_long_minus_short
        slope = sample.length_slope
        b0_norm = "      n/a" if b0_delta is None else f"{norm(b0_delta):9.6f}"
        slope_norm = "        n/a" if slope is None else f"{norm(slope):11.8f}"
        lines.append(
            f"  {sample.slot.slot_id:3d} {sample.slot.role:<17} "
            f"{sample.slot.pose[0]:+6.1f} {sample.slot.pose[1]:6.1f}  "
            f"{vec_text(sample.raw_long_minus_short):<31} "
            f"{vec_text(sample.c_shape_long_minus_short):<31} "
            f"{optional_vec_text(b0_delta):<31} {b0_norm} {slope_norm}"
        )
    return "\n".join(lines)


def put_vector(row: dict[str, str | int], prefix: str, vector: Vec3) -> None:
    for axis, value in zip("xyz", vector):
        row[f"{prefix}_{axis}_mm"] = f"{value:.9f}"


def put_optional_vector(
    row: dict[str, str | int],
    prefix: str,
    vector: Vec3 | None,
) -> None:
    if vector is None:
        for axis in "xyz":
            row[f"{prefix}_{axis}_mm"] = ""
    else:
        put_vector(row, prefix, vector)


def derived_row(result: BaselineResult, sample: MatchedSample) -> dict[str, str | int]:
    row: dict[str, str | int] = {
        "campaign_id": CAMPAIGN_ID,
        "stage_mode": STAGE_MODE,
        "short_attempt_id": result.selected_attempts[1],
        "long_attempt_id": result.selected_attempts[2],
        "slot_id": sample.slot.slot_id,
        "semantic_role": sample.slot.role,
        "grid_status": sample.slot.status,
        "grid_reason": sample.slot.reason,
        "abs_b_deg": f"{sample.slot.pose[0]:.6f}",
        "abs_c_deg": f"{sample.slot.pose[1]:.6f}",
    }
    put_vector(row, "short_absolute_center", sample.rows[1].center)
    put_vector(row, "long_absolute_center", sample.rows[2].center)
    put_vector(row, "raw_long_minus_short", sample.raw_long_minus_short)
    row["raw_long_minus_short_norm_mm"] = f"{norm(sample.raw_long_minus_short):.9f}"
    put_vector(row, "short_group_c0_relative", sample.group_relative[1])
    put_vector(row, "long_group_c0_relative", sample.group_relative[2])
    put_vector(row, "c_shape_long_minus_short", sample.c_shape_long_minus_short)
    row["c_shape_long_minus_short_norm_mm"] = (
        f"{norm(sample.c_shape_long_minus_short):.9f}"
    )

    b0_relative = sample.b0_same_c_relative
    put_optional_vector(
        row,
        "short_b0_same_c_relative",
        None if b0_relative is None else b0_relative[1],
    )
    put_optional_vector(
        row,
        "long_b0_same_c_relative",
        None if b0_relative is None else b0_relative[2],
    )
    put_optional_vector(
        row,
        "b0_referenced_long_minus_short",
        sample.b0_referenced_long_minus_short,
    )
    row["b0_referenced_long_minus_short_norm_mm"] = (
        ""
        if sample.b0_referenced_long_minus_short is None
        else f"{norm(sample.b0_referenced_long_minus_short):.9f}"
    )
    if sample.length_slope is None:
        for name in (
            "length_slope_x",
            "length_slope_y",
            "length_slope_z",
            "length_slope_norm_rad_approx",
            "length_slope_norm_deg_approx",
        ):
            row[name] = ""
    else:
        for axis, value in zip("xyz", sample.length_slope):
            row[f"length_slope_{axis}"] = f"{value:.12f}"
        slope_norm = norm(sample.length_slope)
        row["length_slope_norm_rad_approx"] = f"{slope_norm:.12f}"
        row["length_slope_norm_deg_approx"] = f"{math.degrees(slope_norm):.9f}"

    for label, leg_id in (("short", 1), ("long", 2)):
        source = sample.rows[leg_id]
        row[f"{label}_u_center_error_mm"] = f"{source.u_error:.9f}"
        row[f"{label}_v_center_error_mm"] = f"{source.v_error:.9f}"
        row[f"{label}_u_corrected_diameter_mm"] = f"{source.u_diameter:.9f}"
        row[f"{label}_v_corrected_diameter_mm"] = f"{source.v_diameter:.9f}"
    return row


def write_derived_csv(path: Path, result: BaselineResult) -> None:
    try:
        with path.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(handle, fieldnames=DERIVED_COLUMNS)
            writer.writeheader()
            for sample in result.samples:
                writer.writerow(derived_row(result, sample))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AnalysisError(f"cannot write {path}: {exc}") from exc


def synthetic_raw_row(
    leg_id: int,
    attempt_id: int,
    slot: GridSlot,
    center: Vec3,
) -> dict[str, str]:
    tool, length, calibration = LEG_EXPECTATIONS[leg_id]
    b_deg, c_deg = slot.pose
    motor_cmd = (center[0] + 100.0, center[1] + 200.0, center[2] + 300.0)
    following_error = (0.000001, -0.000001, 0.0)
    motor_fb = add(motor_cmd, following_error)
    values: dict[str, float | int] = {
        "campaign_id": CAMPAIGN_ID,
        "leg_id": leg_id,
        "stage_mode": STAGE_MODE,
        "attempt_id": attempt_id,
        "sample_seq": slot.slot_id,
        "abs_b_deg": b_deg,
        "abs_c_deg": c_deg,
        "live_tool_number": tool,
        "expected_tool_length_mm": length,
        "probe_calibration_offset_mm": calibration,
        "probe_diameter_mm": 6.0,
        "persistent_correction_enabled": 1,
        "tcpc_enabled": 1,
        "twp_active": 0,
        "twp_motion_enabled": 0,
        "twp_valid": 0,
        "b_ssi_invalid": 0,
        "c_ssi_invalid": 0,
        "center_abs_x_mm": center[0],
        "center_abs_y_mm": center[1],
        "center_abs_z_mm": center[2],
        "u_center_error_mm": 0.002,
        "v_center_error_mm": -0.003,
        "u_corrected_diameter_mm": 30.01,
        "v_corrected_diameter_mm": 30.02,
        "motion_tooloffset_z_mm": length,
        "halui_tool_length_offset_z_mm": length,
        "kins_active_tool_offset_z_mm": length,
        "joint_b_cmd_deg": b_deg,
        "joint_b_fb_deg": b_deg + 0.0001,
        "joint_c_cmd_deg": c_deg,
        "joint_c_fb_deg": c_deg - 0.0001,
        "b_ssi_zeroed_deg": b_deg - 360.0,
        "c_ssi_zeroed_deg": -c_deg - 360.0,
        "accepted_endpoint_abs_x_mm": center[0],
        "accepted_endpoint_abs_y_mm": center[1],
        "accepted_endpoint_abs_z_mm": center[2],
        "joint_0_motor_pos_cmd_mm": motor_cmd[0],
        "joint_0_motor_pos_fb_mm": motor_fb[0],
        "joint_0_motor_following_error_fb_minus_cmd_mm": following_error[0],
        "joint_1_motor_pos_cmd_mm": motor_cmd[1],
        "joint_1_motor_pos_fb_mm": motor_fb[1],
        "joint_1_motor_following_error_fb_minus_cmd_mm": following_error[1],
        "joint_2_motor_pos_cmd_mm": motor_cmd[2],
        "joint_2_motor_pos_fb_mm": motor_fb[2],
        "joint_2_motor_following_error_fb_minus_cmd_mm": following_error[2],
    }
    return {name: str(values[name]) for name in REQUIRED_COLUMNS}


def synthetic_common_center(slot: GridSlot) -> Vec3:
    b_rad = math.radians(slot.pose[0])
    c_rad = math.radians(slot.pose[1])
    return (
        1000.0 + (0.020 * math.sin(b_rad)) + (0.004 * math.cos(c_rad)),
        400.0 + (0.015 * math.sin(c_rad)) - (0.005 * math.sin(b_rad)),
        -400.0 + (0.010 * (1.0 - math.cos(b_rad))) + (0.003 * math.cos(c_rad)),
    )


def synthetic_length_effect(slot: GridSlot) -> Vec3:
    b_factor = slot.pose[0] / 30.0
    c_rad = math.radians(slot.pose[1])
    slope = (
        0.001 * b_factor * math.cos(c_rad),
        -0.0005 * b_factor * math.sin(c_rad),
        0.00025 * b_factor,
    )
    return scale(slope, LENGTH_SEPARATION_MM)


def synthetic_center(leg_id: int, slot: GridSlot) -> Vec3:
    common = synthetic_common_center(slot)
    if leg_id == 1:
        return common
    return add(add(common, (0.125, -0.050, 0.200)), synthetic_length_effect(slot))


def write_raw_csv(path: Path, raw_rows: Sequence[dict[str, str]]) -> None:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=REQUIRED_COLUMNS)
    writer.writeheader()
    writer.writerows(raw_rows)
    path.write_text(stream.getvalue(), encoding="ascii")


def write_grid_csv(path: Path, slots: Sequence[GridSlot]) -> None:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=GRID_COLUMNS)
    writer.writeheader()
    for slot in slots:
        writer.writerow(
            {
                "slot_id": slot.slot_id,
                "abs_b_deg": slot.pose[0],
                "abs_c_deg": slot.pose[1],
                "role": slot.role,
                "status": slot.status,
                "reason": slot.reason,
            }
        )
    path.write_text(stream.getvalue(), encoding="ascii")


def run_self_test(grid_path: Path) -> None:
    grid = load_grid(grid_path)
    if len(grid.required) != 31 or len(grid.unsafe) != 6:
        raise AssertionError("reviewed grid did not retain 31 required and 6 unsafe slots")

    raw_rows: list[dict[str, str]] = []
    # T3 has an early partial then a complete second attempt.
    for slot in grid.required[:4]:
        raw_rows.append(synthetic_raw_row(1, 1, slot, synthetic_center(1, slot)))
    for slot in grid.required:
        raw_rows.append(synthetic_raw_row(1, 2, slot, synthetic_center(1, slot)))
    # T4 has a complete first attempt and a later partial. Highest complete is 1.
    for slot in grid.required:
        raw_rows.append(synthetic_raw_row(2, 1, slot, synthetic_center(2, slot)))
    for slot in grid.required[:3]:
        raw_rows.append(synthetic_raw_row(2, 2, slot, synthetic_center(2, slot)))

    with tempfile.TemporaryDirectory() as temp_dir_text:
        temp_dir = Path(temp_dir_text)
        raw_path = temp_dir / "synthetic.csv"
        derived_path = temp_dir / "derived.csv"
        write_raw_csv(raw_path, raw_rows)

        parsed = read_rows(raw_path)
        result = analyze_rows(parsed, grid)
        if result.selected_attempts != {1: 2, 2: 1}:
            raise AssertionError(f"wrong attempts selected: {result.selected_attempts}")
        if len(result.samples) != 31:
            raise AssertionError("unsafe gaps or matched required slots were collapsed")
        if len(result.ignored_attempts) != 2:
            raise AssertionError(f"wrong partial-attempt notes: {result.ignored_attempts}")
        assessment = evaluate_quality(result)
        if not assessment.passed:
            raise AssertionError(f"valid synthetic baseline failed: {assessment.failures}")

        by_slot = {sample.slot.slot_id: sample for sample in result.samples}
        offset = (0.125, -0.050, 0.200)
        if norm(sub(by_slot[1].raw_long_minus_short, offset)) > 1e-10:
            raise AssertionError("nonzero raw absolute L-S1 offset was not retained")
        slot_30 = by_slot[30]
        expected_b0_delta = synthetic_length_effect(slot_30.slot)
        if slot_30.b0_referenced_long_minus_short is None:
            raise AssertionError("positive-B B0-referenced delta was omitted")
        if norm(sub(slot_30.b0_referenced_long_minus_short, expected_b0_delta)) > 1e-10:
            raise AssertionError("B0 same-C referenced differential is incorrect")
        expected_slope = scale(expected_b0_delta, 1.0 / LENGTH_SEPARATION_MM)
        if slot_30.length_slope is None or norm(sub(slot_30.length_slope, expected_slope)) > 1e-10:
            raise AssertionError("length-normalized slope is incorrect")
        expected_c_shape = sub(
            synthetic_length_effect(slot_30.slot),
            synthetic_length_effect(grid.by_id[28]),
        )
        if norm(sub(slot_30.c_shape_long_minus_short, expected_c_shape)) > 1e-10:
            raise AssertionError("group-C0-referenced C-shape is incorrect")

        report = format_report(raw_path, grid_path, len(parsed), grid, result, assessment)
        for required_text in (
            "CAVEAT - NO S2",
            "CAVEAT - POSITIVE B ONLY",
            "slot 13: B5 C135",
            "missing required slots in selected legs: none",
            "ignored canonical partial",
            "differential closure diagnostics",
            "B-group RMS/max",
        ):
            if required_text not in report:
                raise AssertionError(f"report omitted {required_text!r}")

        write_derived_csv(derived_path, result)
        with derived_path.open(newline="", encoding="ascii") as handle:
            derived = list(csv.DictReader(handle))
        if len(derived) != 31:
            raise AssertionError(f"derived row count was {len(derived)}, expected 31")
        derived_slot_1 = next(row for row in derived if row["slot_id"] == "1")
        if abs(float(derived_slot_1["raw_long_minus_short_x_mm"]) - offset[0]) > 1e-9:
            raise AssertionError("derived CSV lost the raw absolute L-S1 offset")
        if derived_slot_1["length_slope_x"] != "":
            raise AssertionError("B0 length slope should be blank")

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            accepted_exit = main(
                [str(raw_path), "--grid", str(grid_path), "--output", str(derived_path)]
            )
        if accepted_exit != EXIT_ACCEPTED:
            raise AssertionError(f"valid baseline returned exit {accepted_exit}")

        t3_rows = [dict(row) for row in raw_rows if row["leg_id"] == "1"]
        t3_path = temp_dir / "t3-only.csv"
        write_raw_csv(t3_path, t3_rows)
        leg_report_stream = io.StringIO()
        with redirect_stdout(leg_report_stream), redirect_stderr(io.StringIO()):
            leg_accepted_exit = main(
                [str(t3_path), "--grid", str(grid_path), "--leg-only", "1"]
            )
        if leg_accepted_exit != EXIT_ACCEPTED:
            raise AssertionError(
                f"valid T3-only leg returned exit {leg_accepted_exit}"
            )
        leg_report = leg_report_stream.getvalue()
        for required_text in (
            "single-leg validation",
            "cross-leg calculations: not performed",
            "attempt=2",
            "missing required slots in selected leg: none",
            "outer B0 C0 first-to-last",
        ):
            if required_text not in leg_report:
                raise AssertionError(f"single-leg report omitted {required_text!r}")

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            missing_leg_exit = main(
                [str(t3_path), "--grid", str(grid_path), "--leg-only", "2"]
            )
        if missing_leg_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"missing selected leg returned exit {missing_leg_exit}, expected 1"
            )

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            leg_output_exit = main(
                [
                    str(t3_path),
                    "--grid",
                    str(grid_path),
                    "--leg-only",
                    "1",
                    "--output",
                    str(derived_path),
                ]
            )
        if leg_output_exit != EXIT_INPUT_ERROR:
            raise AssertionError(
                f"leg-only derived output returned exit {leg_output_exit}, expected 2"
            )

        near_c_rows = [dict(row) for row in raw_rows]
        for row in near_c_rows:
            if (
                (row["leg_id"], row["attempt_id"], row["sample_seq"])
                in (("1", "2", "3"), ("2", "1", "3"))
            ):
                near_c = float(row["abs_c_deg"]) + 0.0000005
                row["abs_c_deg"] = str(near_c)
                row["joint_c_cmd_deg"] = str(near_c)
                row["joint_c_fb_deg"] = str(near_c - 0.0001)
                row["c_ssi_zeroed_deg"] = str(-near_c - 360.0)
        near_c_path = temp_dir / "near-tolerance-c.csv"
        write_raw_csv(near_c_path, near_c_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            near_c_exit = main([str(near_c_path), "--grid", str(grid_path)])
        if near_c_exit != EXIT_ACCEPTED:
            raise AssertionError(
                f"near-tolerance canonical C references returned exit {near_c_exit}"
            )

        bad_state_rows = [dict(raw_rows[0])]
        bad_state_rows[0]["tcpc_enabled"] = "0"
        bad_state_path = temp_dir / "bad-state.csv"
        write_raw_csv(bad_state_path, bad_state_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            bad_state_exit = main([str(bad_state_path), "--grid", str(grid_path)])
        if bad_state_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"bad live state returned exit {bad_state_exit}, expected {EXIT_DATA_QUALITY}"
            )

        closure_rows = [dict(row) for row in raw_rows]
        for row in closure_rows:
            if row["leg_id"] == "1" and row["attempt_id"] == "2" and row["sample_seq"] == "18":
                row["center_abs_x_mm"] = str(float(row["center_abs_x_mm"]) + 0.050001)
        closure_path = temp_dir / "bad-closure.csv"
        write_raw_csv(closure_path, closure_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            closure_exit = main([str(closure_path), "--grid", str(grid_path)])
        if closure_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"closure failure returned exit {closure_exit}, expected {EXIT_DATA_QUALITY}"
            )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            leg_closure_exit = main(
                [str(closure_path), "--grid", str(grid_path), "--leg-only", "1"]
            )
        if leg_closure_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"single-leg closure failure returned exit {leg_closure_exit}, expected 1"
            )

        partial_rows = [
            row
            for row in raw_rows
            if not (
                row["leg_id"] == "1"
                and row["attempt_id"] == "2"
                and row["sample_seq"] == "37"
            )
        ]
        partial_path = temp_dir / "no-complete-attempt.csv"
        write_raw_csv(partial_path, partial_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            partial_exit = main([str(partial_path), "--grid", str(grid_path)])
        if partial_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"no-complete-attempt returned exit {partial_exit}, expected 1"
            )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            leg_partial_exit = main(
                [str(partial_path), "--grid", str(grid_path), "--leg-only", "1"]
            )
        if leg_partial_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"single-leg incomplete attempt returned exit {leg_partial_exit}, expected 1"
            )

        gap_rows = [
            row
            for row in raw_rows
            if not (
                row["leg_id"] == "1"
                and row["attempt_id"] == "2"
                and row["sample_seq"] == "14"
            )
        ]
        gap_path = temp_dir / "undeclared-gap.csv"
        write_raw_csv(gap_path, gap_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            gap_exit = main([str(gap_path), "--grid", str(grid_path)])
        if gap_exit != EXIT_INPUT_ERROR:
            raise AssertionError(f"undeclared gap returned exit {gap_exit}, expected 2")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            leg_gap_exit = main(
                [str(gap_path), "--grid", str(grid_path), "--leg-only", "1"]
            )
        if leg_gap_exit != EXIT_INPUT_ERROR:
            raise AssertionError(
                f"single-leg undeclared gap returned exit {leg_gap_exit}, expected 2"
            )

        wrapped_b_pose_rows = [dict(row) for row in raw_rows]
        for row in wrapped_b_pose_rows:
            if (
                row["leg_id"] == "1"
                and row["attempt_id"] == "2"
                and row["sample_seq"] == "10"
            ):
                row["abs_b_deg"] = "-355"
                row["joint_b_cmd_deg"] = "-355"
                row["joint_b_fb_deg"] = "-354.9999"
                row["b_ssi_zeroed_deg"] = "5"
        wrapped_b_pose_path = temp_dir / "wrapped-b-pose.csv"
        write_raw_csv(wrapped_b_pose_path, wrapped_b_pose_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            wrapped_b_pose_exit = main(
                [str(wrapped_b_pose_path), "--grid", str(grid_path)]
            )
        if wrapped_b_pose_exit != EXIT_INPUT_ERROR:
            raise AssertionError(
                f"wrapped logged B pose returned exit {wrapped_b_pose_exit}, expected 2"
            )

        unsafe_rows = [dict(row) for row in raw_rows]
        insert_after = next(
            index
            for index, row in enumerate(unsafe_rows)
            if row["leg_id"] == "1"
            and row["attempt_id"] == "2"
            and row["sample_seq"] == "12"
        )
        unsafe_slot = grid.by_id[13]
        unsafe_rows.insert(
            insert_after + 1,
            synthetic_raw_row(1, 2, unsafe_slot, synthetic_center(1, unsafe_slot)),
        )
        unsafe_path = temp_dir / "unsafe-slot-logged.csv"
        write_raw_csv(unsafe_path, unsafe_rows)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            unsafe_exit = main([str(unsafe_path), "--grid", str(grid_path)])
        if unsafe_exit != EXIT_INPUT_ERROR:
            raise AssertionError(f"logged unsafe slot returned exit {unsafe_exit}, expected 2")

        bad_header_path = temp_dir / "bad-header.csv"
        bad_header_path.write_text(",".join(REQUIRED_COLUMNS[:-1]) + "\n", encoding="ascii")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            bad_header_exit = main([str(bad_header_path), "--grid", str(grid_path)])
        if bad_header_exit != EXIT_INPUT_ERROR:
            raise AssertionError(f"bad header returned exit {bad_header_exit}, expected 2")

        header_only_path = temp_dir / "header-only.csv"
        header_only_path.write_text(",".join(REQUIRED_COLUMNS) + "\n", encoding="ascii")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            header_only_exit = main([str(header_only_path), "--grid", str(grid_path)])
        if header_only_exit != EXIT_INPUT_ERROR:
            raise AssertionError(
                f"header-only input returned exit {header_only_exit}, expected 2"
            )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            header_only_leg_exit = main(
                [
                    str(header_only_path),
                    "--grid",
                    str(grid_path),
                    "--leg-only",
                    "1",
                ]
            )
        if header_only_leg_exit != EXIT_INPUT_ERROR:
            raise AssertionError(
                "header-only single-leg input returned exit "
                f"{header_only_leg_exit}, expected 2"
            )

        near_c_grid_slots = list(grid.slots)
        canonical_slot_3 = near_c_grid_slots[2]
        near_c_grid_slots[2] = GridSlot(
            canonical_slot_3.slot_id,
            (canonical_slot_3.pose[0], canonical_slot_3.pose[1] + 0.0000005),
            canonical_slot_3.role,
            canonical_slot_3.status,
            canonical_slot_3.reason,
        )
        near_c_grid_path = temp_dir / "near-tolerance-c-grid.csv"
        write_grid_csv(near_c_grid_path, near_c_grid_slots)
        normalized_grid = load_grid(near_c_grid_path)
        if normalized_grid.by_id[3].pose != grid.by_id[3].pose:
            raise AssertionError("accepted near-tolerance grid pose was not canonicalized")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            near_c_grid_exit = main(
                [str(raw_path), "--grid", str(near_c_grid_path)]
            )
        if near_c_grid_exit != EXIT_ACCEPTED:
            raise AssertionError(
                f"near-tolerance canonical grid returned exit {near_c_grid_exit}"
            )

        bad_grid_slots = list(grid.slots)
        bad_grid_slots[12] = GridSlot(
            13,
            bad_grid_slots[12].pose,
            "B5_measure",
            "required",
            "",
        )
        bad_grid_path = temp_dir / "bad-grid.csv"
        write_grid_csv(bad_grid_path, bad_grid_slots)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            bad_grid_exit = main([str(raw_path), "--grid", str(bad_grid_path)])
        if bad_grid_exit != EXIT_INPUT_ERROR:
            raise AssertionError(f"bad grid returned exit {bad_grid_exit}, expected 2")

        wrapped_b_grid_slots = list(grid.slots)
        canonical_slot_10 = wrapped_b_grid_slots[9]
        wrapped_b_grid_slots[9] = GridSlot(
            canonical_slot_10.slot_id,
            (-355.0, canonical_slot_10.pose[1]),
            canonical_slot_10.role,
            canonical_slot_10.status,
            canonical_slot_10.reason,
        )
        wrapped_b_grid_path = temp_dir / "wrapped-b-grid.csv"
        write_grid_csv(wrapped_b_grid_path, wrapped_b_grid_slots)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            wrapped_b_grid_exit = main(
                [str(raw_path), "--grid", str(wrapped_b_grid_path)]
            )
        if wrapped_b_grid_exit != EXIT_INPUT_ERROR:
            raise AssertionError(
                f"wrapped grid B pose returned exit {wrapped_b_grid_exit}, expected 2"
            )

    # Direct row-level checks also cover circular C reporting and SSI polarity.
    wrapped_slot = grid.by_id[24]
    wrapped = synthetic_raw_row(1, 1, wrapped_slot, synthetic_center(1, wrapped_slot))
    wrapped["joint_c_cmd_deg"] = str(wrapped_slot.pose[1] - 360.0)
    wrapped["joint_c_fb_deg"] = str(wrapped_slot.pose[1] - 359.9999)
    wrapped["c_ssi_zeroed_deg"] = str(-wrapped_slot.pose[1] + 360.0001)
    parse_row(wrapped, 1, 2)

    b_slot = grid.by_id[10]
    wrapped_b_ssi = synthetic_raw_row(1, 1, b_slot, synthetic_center(1, b_slot))
    wrapped_b_ssi["b_ssi_zeroed_deg"] = str(b_slot.pose[0] - 360.0)
    parse_row(wrapped_b_ssi, 1, 2)

    wrapped_b_command = synthetic_raw_row(1, 1, b_slot, synthetic_center(1, b_slot))
    wrapped_b_command["joint_b_cmd_deg"] = str(b_slot.pose[0] - 360.0)
    wrapped_b_command["joint_b_fb_deg"] = str(b_slot.pose[0] - 360.0)
    try:
        parse_row(wrapped_b_command, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("B command wrapped by -360 degrees was accepted")

    wrapped_b_feedback = synthetic_raw_row(1, 1, b_slot, synthetic_center(1, b_slot))
    wrapped_b_feedback["joint_b_fb_deg"] = str(b_slot.pose[0] - 360.0)
    try:
        parse_row(wrapped_b_feedback, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("B feedback wrapped by -360 degrees was accepted")

    same_polarity = synthetic_raw_row(1, 1, grid.by_id[12], synthetic_center(1, grid.by_id[12]))
    same_polarity["c_ssi_zeroed_deg"] = same_polarity["joint_c_cmd_deg"]
    try:
        parse_row(same_polarity, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("same-polarity C SSI state was accepted")

    bad_ferror = synthetic_raw_row(1, 1, grid.by_id[1], synthetic_center(1, grid.by_id[1]))
    bad_ferror["joint_1_motor_following_error_fb_minus_cmd_mm"] = "0.000010"
    try:
        parse_row(bad_ferror, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("inconsistent linear following error was accepted")

    # T4's relaxed acquisition ceiling must not relabel historical T3 rows.
    t4_relaxed_center = synthetic_raw_row(
        2, 1, grid.by_id[1], synthetic_center(2, grid.by_id[1])
    )
    t4_relaxed_center["u_center_error_mm"] = "2.000000"
    t4_relaxed_center["v_center_error_mm"] = "0.000000"
    parse_row(t4_relaxed_center, 1, 2)

    t4_over_center = dict(t4_relaxed_center)
    t4_over_center["u_center_error_mm"] = "2.000001"
    try:
        parse_row(t4_over_center, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("T4 center residual above 2 mm was accepted")

    t4_diagonal_center = dict(t4_relaxed_center)
    t4_diagonal_center["u_center_error_mm"] = "1.500000"
    t4_diagonal_center["v_center_error_mm"] = "1.500000"
    try:
        parse_row(t4_diagonal_center, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("T4 diagonal center residual above 2 mm was accepted")

    t3_relaxed_center = synthetic_raw_row(
        1, 1, grid.by_id[1], synthetic_center(1, grid.by_id[1])
    )
    t3_relaxed_center["u_center_error_mm"] = "0.100001"
    try:
        parse_row(t3_relaxed_center, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("historical T3 center residual above 0.10 mm was accepted")

    print(
        "self-test passed: exact grid/unsafe gaps, 46-column schema, live-state QA, "
        "direct B and wrapped SSI/C rotary QA, following-error consistency, "
        "per-leg T3/T4 acquisition center-norm limits, "
        "attempt selection, single-leg validation exits 0/1/2, "
        "partial retention, undeclared-gap/unsafe-slot rejection, closure gates, "
        "raw L-S1 offset, C-shape, B0-referenced differential, slopes, report, "
        "canonical near-tolerance row/grid C references, derived CSV, header-only "
        "rejection, and exit codes"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Exit status: 0 when CSV quality and closure gates pass; 1 when logged "
            "machine state or selected data fails a gate; 2 for input, schema, "
            "grid, sequence, or I/O errors."
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"isolated stage-19 baseline CSV (default: {DEFAULT_INPUT.name})",
    )
    parser.add_argument(
        "--grid",
        type=Path,
        default=DEFAULT_GRID,
        help=f"canonical required/unsafe grid CSV (default: {DEFAULT_GRID.name})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write matched per-slot derived values to CSV",
    )
    parser.add_argument(
        "--leg-only",
        type=int,
        choices=(1, 2),
        help=(
            "validate only one complete leg and its closures; no T3/T4 matched "
            "calculations are performed"
        ),
    )
    parser.add_argument("--self-test", action="store_true", help="run synthetic checks and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test(args.grid)
        return EXIT_ACCEPTED
    try:
        grid = load_grid(args.grid)
        rows = read_rows(args.input)
        if args.leg_only is not None:
            if args.output is not None:
                raise AnalysisError(
                    "--output is unavailable with --leg-only because derived output "
                    "requires matched T3 and T4 legs"
                )
            leg_result = analyze_leg(rows, grid, args.leg_only)
            assessment = evaluate_leg_quality(leg_result)
            print(
                format_leg_report(
                    args.input,
                    args.grid,
                    len(rows),
                    grid,
                    leg_result,
                    assessment,
                )
            )
        else:
            result = analyze_rows(rows, grid)
            assessment = evaluate_quality(result)
            print(format_report(args.input, args.grid, len(rows), grid, result, assessment))
        if args.output is not None and args.leg_only is None:
            output = args.output.resolve()
            if output == args.input.resolve():
                raise AnalysisError("--output must not overwrite the source measurement CSV")
            if output == args.grid.resolve():
                raise AnalysisError("--output must not overwrite the companion grid CSV")
            write_derived_csv(args.output, result)
            print(f"derived CSV: {args.output}")
    except DataQualityError as exc:
        print(f"data-quality failure: {exc}", file=sys.stderr)
        return EXIT_DATA_QUALITY
    except AnalysisError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    return EXIT_ACCEPTED if assessment.passed else EXIT_DATA_QUALITY


if __name__ == "__main__":
    sys.exit(main())
