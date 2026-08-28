#!/usr/bin/env python3
"""Validate and summarize isolated T3/T4/T3 TCPC calibration results.

The analyzer preserves the runner's semantic sample sequence, reports the
absolute long-versus-bracketed-short center offset, then separately removes
the defined B0 reference from each leg to report pose-dependent length
sensitivity. It is descriptive only: it does not fit or recommend kinematic
coefficients.
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
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "tcpc-long-short-pair-results.csv"

SHORT_TOOL = 3
LONG_TOOL = 4
SHORT_LENGTH_MM = 128.606729
LONG_LENGTH_MM = 229.407000
LENGTH_SEPARATION_MM = LONG_LENGTH_MM - SHORT_LENGTH_MM

TLO_TOL_MM = 0.002
CAL_OFFSET_TOL_MM = 0.0005
DIAMETER_TOL_MM = 0.01
ROTARY_TOL_DEG = 0.01
POSE_TOL_DEG = 1e-6
# LinuxCNC's parameter-comment expansion logs floats with six decimal places.
# Three independently rounded values can differ by at most 1.5e-6 mm.
FOLLOWING_ERROR_CONSISTENCY_TOL_MM = 2e-6
QA_CENTER_TOL_MM = 0.10
QA_DIAMETER_MIN_MM = 29.9
QA_DIAMETER_MAX_MM = 30.5
CLOSURE_LIMIT_MM = 0.05
SHORT_DRIFT_RMS_LIMIT_MM = 0.05
SHORT_DRIFT_MAX_LIMIT_MM = 0.10
PRODUCTION_MAX_LIMIT_MM = 0.20
PRODUCTION_PREFERRED_MAX_MM = 0.10

EXIT_ACCEPTED = 0
EXIT_DATA_QUALITY = 1
EXIT_INPUT_ERROR = 2

LEG_NAMES = {1: "S1", 2: "L", 3: "S2"}
LEG_EXPECTATIONS = {
    1: (SHORT_TOOL, SHORT_LENGTH_MM),
    2: (LONG_TOOL, LONG_LENGTH_MM),
    3: (SHORT_TOOL, SHORT_LENGTH_MM),
}

Vec3 = tuple[float, float, float]
Pose = tuple[float, float]


def quadrant_group(b_deg: float) -> tuple[Pose, ...]:
    return (
        (b_deg, 0.0),
        (b_deg, 90.0),
        (b_deg, 180.0),
        (b_deg, 270.0),
        (b_deg, 0.0),
    )


MODE_POSES: dict[int, tuple[Pose, ...]] = {
    15: quadrant_group(0.0),
    16: (
        (0.0, 0.0),
        (5.0, 0.0),
        (5.0, 20.0),
        (5.0, -20.0),
        (5.0, 0.0),
        (-5.0, 0.0),
        (-5.0, 20.0),
        (-5.0, -20.0),
        (-5.0, 0.0),
        (0.0, 0.0),
    ),
    17: quadrant_group(0.0) + quadrant_group(10.0) + quadrant_group(-10.0) + quadrant_group(0.0),
    18: quadrant_group(0.0) + quadrant_group(30.0) + quadrant_group(-30.0) + quadrant_group(0.0),
}

MEASUREMENT_SEQUENCES = {
    15: frozenset(range(2, 5)),
    16: frozenset(range(2, 10)),
    17: frozenset(range(6, 16)),
    18: frozenset(range(6, 16)),
}

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
    "s1_attempt_id",
    "long_attempt_id",
    "s2_attempt_id",
    "sample_seq",
    "semantic_role",
    "abs_b_deg",
    "abs_c_deg",
    "s1_absolute_center_x_mm",
    "s1_absolute_center_y_mm",
    "s1_absolute_center_z_mm",
    "s1_absolute_center_norm_mm",
    "long_absolute_center_x_mm",
    "long_absolute_center_y_mm",
    "long_absolute_center_z_mm",
    "long_absolute_center_norm_mm",
    "s2_absolute_center_x_mm",
    "s2_absolute_center_y_mm",
    "s2_absolute_center_z_mm",
    "s2_absolute_center_norm_mm",
    "absolute_bracketed_short_center_x_mm",
    "absolute_bracketed_short_center_y_mm",
    "absolute_bracketed_short_center_z_mm",
    "absolute_bracketed_short_center_norm_mm",
    "effective_center_offset_x_mm",
    "effective_center_offset_y_mm",
    "effective_center_offset_z_mm",
    "effective_center_offset_norm_mm",
    "s1_rel_x_mm",
    "s1_rel_y_mm",
    "s1_rel_z_mm",
    "s1_rel_norm_mm",
    "long_rel_x_mm",
    "long_rel_y_mm",
    "long_rel_z_mm",
    "long_rel_norm_mm",
    "s2_rel_x_mm",
    "s2_rel_y_mm",
    "s2_rel_z_mm",
    "s2_rel_norm_mm",
    "s2_minus_s1_x_mm",
    "s2_minus_s1_y_mm",
    "s2_minus_s1_z_mm",
    "s2_minus_s1_norm_mm",
    "bracketed_short_x_mm",
    "bracketed_short_y_mm",
    "bracketed_short_z_mm",
    "bracketed_short_norm_mm",
    "long_minus_short_x_mm",
    "long_minus_short_y_mm",
    "long_minus_short_z_mm",
    "long_minus_short_norm_mm",
    "length_slope_x",
    "length_slope_y",
    "length_slope_z",
    "length_slope_norm_rad_approx",
    "length_slope_norm_deg_approx",
)


class AnalysisError(ValueError):
    """The input schema, sequence, or invocation is structurally invalid."""


class DataQualityError(ValueError):
    """The logged machine state or measurements fail a data-quality gate."""


@dataclass(frozen=True)
class Row:
    source_order: int
    line: int
    campaign_id: str
    leg_id: int
    stage_mode: int
    attempt_id: int
    sample_seq: int
    pose: Pose
    calibration_offset: float
    center: Vec3
    accepted_endpoint: Vec3
    linear_motor_cmd: Vec3
    linear_motor_fb: Vec3
    linear_following_error: Vec3


@dataclass(frozen=True)
class SampleResult:
    sample_seq: int
    pose: Pose
    role: str
    absolute_centers: dict[int, Vec3]
    absolute_bracketed_short_center: Vec3
    effective_center_offset: Vec3
    relative: dict[int, Vec3]
    s2_minus_s1: Vec3
    bracketed_short: Vec3
    long_minus_short: Vec3
    length_slope: Vec3


@dataclass(frozen=True)
class ClosureResult:
    label: str
    quality_gate: bool
    vectors: dict[int, Vec3]


@dataclass(frozen=True)
class StageResult:
    campaign_id: str
    stage_mode: int
    row_count: int
    selected_row_count: int
    selected_attempts: dict[int, int]
    ignored_attempts: tuple[str, ...]
    references: dict[int, dict[float, Vec3]]
    opening_b0c0: dict[int, Vec3]
    closing_b0c0: dict[int, Vec3]
    opening_effective_center_offset: Vec3
    closing_effective_center_offset: Vec3
    closures: dict[int, Vec3]
    closure_results: tuple[ClosureResult, ...]
    samples: tuple[SampleResult, ...]
    leg_metrics: dict[int, tuple[float, float]]
    drift_metric: tuple[float, float]
    length_delta_metric: tuple[float, float]


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
    return (math.sqrt(sum(value * value for value in magnitudes) / len(magnitudes)), max(magnitudes))


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


def require_near(line: int, name: str, actual: float, expected: float, tolerance: float) -> None:
    if abs(actual - expected) > tolerance:
        raise DataQualityError(
            f"line {line}: {name}={actual:.9f}, expected {expected:.9f} +/- {tolerance:.6f}"
        )


def require_flag(line: int, name: str, actual: float, expected: int) -> None:
    require_near(line, name, actual, float(expected), 1e-6)


def validate_rotary(line: int, raw: dict[str, str], b_deg: float, c_deg: float) -> None:
    b_cmd = parse_float(raw, "joint_b_cmd_deg", line)
    b_fb = parse_float(raw, "joint_b_fb_deg", line)
    c_cmd = parse_float(raw, "joint_c_cmd_deg", line)
    c_fb = parse_float(raw, "joint_c_fb_deg", line)
    b_ssi = parse_float(raw, "b_ssi_zeroed_deg", line)
    c_ssi = parse_float(raw, "c_ssi_zeroed_deg", line)
    comparisons = (
        ("joint_b_cmd_deg", b_cmd, b_deg),
        ("joint_b_fb_deg", b_fb, b_cmd),
        ("b_ssi_zeroed_deg", b_ssi, b_cmd),
        ("joint_c_cmd_deg", c_cmd, c_deg),
        ("joint_c_fb_deg", c_fb, c_cmd),
        # The physical C SSI zeroed signal has the opposite polarity to joint C.
        ("c_ssi_zeroed_deg", c_ssi, -c_cmd),
    )
    for name, actual, expected in comparisons:
        difference = angular_difference_deg(actual, expected)
        if difference > ROTARY_TOL_DEG:
            raise DataQualityError(
                f"line {line}: {name} differs from its reference by "
                f"{difference:.6f} deg (limit {ROTARY_TOL_DEG:.6f})"
            )


def parse_linear_axis_state(raw: dict[str, str], line: int) -> tuple[Vec3, Vec3, Vec3, Vec3]:
    endpoint = (
        parse_float(raw, "accepted_endpoint_abs_x_mm", line),
        parse_float(raw, "accepted_endpoint_abs_y_mm", line),
        parse_float(raw, "accepted_endpoint_abs_z_mm", line),
    )
    motor_cmd = (
        parse_float(raw, "joint_0_motor_pos_cmd_mm", line),
        parse_float(raw, "joint_1_motor_pos_cmd_mm", line),
        parse_float(raw, "joint_2_motor_pos_cmd_mm", line),
    )
    motor_fb = (
        parse_float(raw, "joint_0_motor_pos_fb_mm", line),
        parse_float(raw, "joint_1_motor_pos_fb_mm", line),
        parse_float(raw, "joint_2_motor_pos_fb_mm", line),
    )
    following_error = (
        parse_float(
            raw,
            "joint_0_motor_following_error_fb_minus_cmd_mm",
            line,
        ),
        parse_float(
            raw,
            "joint_1_motor_following_error_fb_minus_cmd_mm",
            line,
        ),
        parse_float(
            raw,
            "joint_2_motor_following_error_fb_minus_cmd_mm",
            line,
        ),
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
    return endpoint, motor_cmd, motor_fb, following_error


def parse_row(raw: dict[str, str], source_order: int, line: int) -> Row:
    campaign_id = (raw.get("campaign_id") or "").strip()
    if not campaign_id:
        raise AnalysisError(f"line {line}: campaign_id is empty")
    leg_id = parse_int(raw, "leg_id", line)
    if leg_id not in LEG_EXPECTATIONS:
        raise AnalysisError(f"line {line}: leg_id must be 1, 2, or 3, got {leg_id}")
    stage_mode = parse_int(raw, "stage_mode", line)
    if stage_mode not in MODE_POSES:
        raise AnalysisError(f"line {line}: stage_mode must be 15, 16, 17, or 18, got {stage_mode}")
    attempt_id = parse_int(raw, "attempt_id", line)
    if attempt_id <= 0:
        raise AnalysisError(f"line {line}: attempt_id must be positive, got {attempt_id}")
    sample_seq = parse_int(raw, "sample_seq", line)
    b_deg = parse_float(raw, "abs_b_deg", line)
    c_deg = parse_float(raw, "abs_c_deg", line)

    expected_tool, expected_length = LEG_EXPECTATIONS[leg_id]
    live_tool = parse_int(raw, "live_tool_number", line)
    if live_tool != expected_tool:
        raise DataQualityError(
            f"line {line}: leg {leg_id} requires T{expected_tool}, got T{live_tool}"
        )
    expected_tlo = parse_float(raw, "expected_tool_length_mm", line)
    tlo_values = [
        expected_tlo,
        parse_float(raw, "motion_tooloffset_z_mm", line),
        parse_float(raw, "halui_tool_length_offset_z_mm", line),
        parse_float(raw, "kins_active_tool_offset_z_mm", line),
    ]
    for name, value in zip(
        (
            "expected_tool_length_mm",
            "motion_tooloffset_z_mm",
            "halui_tool_length_offset_z_mm",
            "kins_active_tool_offset_z_mm",
        ),
        tlo_values,
    ):
        require_near(line, name, value, expected_length, TLO_TOL_MM)
    if max(tlo_values) - min(tlo_values) > TLO_TOL_MM:
        raise DataQualityError(
            f"line {line}: expected/live Z tool offsets span "
            f"{max(tlo_values) - min(tlo_values):.6f} mm (limit {TLO_TOL_MM:.6f})"
        )

    require_near(
        line,
        "probe_diameter_mm",
        parse_float(raw, "probe_diameter_mm", line),
        6.0,
        DIAMETER_TOL_MM,
    )
    calibration_offset = parse_float(raw, "probe_calibration_offset_mm", line)
    if not 0.0 < calibration_offset <= 1.0:
        raise DataQualityError(
            f"line {line}: probe_calibration_offset_mm must be in (0, 1], got {calibration_offset}"
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
    if abs(u_error) > QA_CENTER_TOL_MM or abs(v_error) > QA_CENTER_TOL_MM:
        raise DataQualityError(
            f"line {line}: U/V centering residual ({u_error:.6f}, {v_error:.6f}) "
            f"exceeds +/-{QA_CENTER_TOL_MM:.3f} mm"
        )
    for name in ("u_corrected_diameter_mm", "v_corrected_diameter_mm"):
        diameter = parse_float(raw, name, line)
        if not QA_DIAMETER_MIN_MM <= diameter <= QA_DIAMETER_MAX_MM:
            raise DataQualityError(
                f"line {line}: {name}={diameter:.6f} outside "
                f"[{QA_DIAMETER_MIN_MM:.1f}, {QA_DIAMETER_MAX_MM:.1f}] mm"
            )

    validate_rotary(line, raw, b_deg, c_deg)
    center = (
        parse_float(raw, "center_abs_x_mm", line),
        parse_float(raw, "center_abs_y_mm", line),
        parse_float(raw, "center_abs_z_mm", line),
    )
    endpoint, motor_cmd, motor_fb, following_error = parse_linear_axis_state(raw, line)
    return Row(
        source_order=source_order,
        line=line,
        campaign_id=campaign_id,
        leg_id=leg_id,
        stage_mode=stage_mode,
        attempt_id=attempt_id,
        sample_seq=sample_seq,
        pose=(b_deg, c_deg),
        calibration_offset=calibration_offset,
        center=center,
        accepted_endpoint=endpoint,
        linear_motor_cmd=motor_cmd,
        linear_motor_fb=motor_fb,
        linear_following_error=following_error,
    )


def read_rows(path: Path) -> list[Row]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle, strict=True)
            fieldnames = reader.fieldnames or []
            if tuple(fieldnames) != REQUIRED_COLUMNS:
                raise AnalysisError(
                    f"CSV header must exactly match the {len(REQUIRED_COLUMNS)}-column "
                    "paired-run schema; "
                    f"got {fieldnames}"
                )
            rows = []
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


def validate_calibration_offsets(rows: Sequence[Row]) -> None:
    offsets: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in rows:
        offsets[(row.campaign_id, row.leg_id)].append(row.calibration_offset)
    means = {}
    for key, values in offsets.items():
        spread = max(values) - min(values)
        if spread > CAL_OFFSET_TOL_MM:
            campaign, leg = key
            raise DataQualityError(
                f"campaign {campaign} leg {leg}: calibration offset range is "
                f"{spread:.6f} mm (limit {CAL_OFFSET_TOL_MM:.6f})"
            )
        means[key] = sum(values) / len(values)
    for campaign in sorted({row.campaign_id for row in rows}):
        s1 = means.get((campaign, 1))
        s2 = means.get((campaign, 3))
        if s1 is not None and s2 is not None and abs(s2 - s1) > CAL_OFFSET_TOL_MM:
            raise DataQualityError(
                f"campaign {campaign}: S1/S2 T3 calibration offsets differ by "
                f"{abs(s2 - s1):.6f} mm (limit {CAL_OFFSET_TOL_MM:.6f})"
            )


def pose_matches(actual: Pose, expected: Pose) -> bool:
    return (
        angular_difference_deg(actual[0], expected[0]) <= POSE_TOL_DEG
        and angular_difference_deg(actual[1], expected[1]) <= POSE_TOL_DEG
    )


def validate_attempt_prefix(
    campaign_id: str,
    stage_mode: int,
    leg: int,
    attempt_id: int,
    rows: Sequence[Row],
) -> None:
    expected = MODE_POSES[stage_mode]
    if len(rows) > len(expected):
        raise AnalysisError(
            f"campaign {campaign_id} stage {stage_mode} {LEG_NAMES[leg]} attempt {attempt_id}: "
            f"got {len(rows)} samples, more than the expected {len(expected)}"
        )
    for index, row in enumerate(rows, start=1):
        expected_pose = expected[index - 1]
        if row.sample_seq != index:
            raise AnalysisError(
                f"campaign {campaign_id} stage {stage_mode} {LEG_NAMES[leg]} "
                f"attempt {attempt_id}: "
                f"row {row.line} has sample_seq {row.sample_seq}, expected {index}"
            )
        if not pose_matches(row.pose, expected_pose):
            raise AnalysisError(
                f"campaign {campaign_id} stage {stage_mode} {LEG_NAMES[leg]} "
                f"attempt {attempt_id} sample {index}: pose {row.pose} does not match {expected_pose}"
            )


def select_attempt(
    campaign_id: str,
    stage_mode: int,
    leg: int,
    rows: Sequence[Row],
) -> tuple[int, list[Row], list[str]]:
    attempt_order = []
    for row in rows:
        if not attempt_order or attempt_order[-1] != row.attempt_id:
            attempt_order.append(row.attempt_id)
    if attempt_order != sorted(set(attempt_order)):
        raise AnalysisError(
            f"campaign {campaign_id} stage {stage_mode} {LEG_NAMES[leg]}: "
            f"attempt IDs are reused or out of order: {attempt_order}"
        )

    attempts: dict[int, list[Row]] = defaultdict(list)
    for row in rows:
        attempts[row.attempt_id].append(row)
    complete = []
    notes = []
    expected_count = len(MODE_POSES[stage_mode])
    for attempt_id in sorted(attempts):
        attempt_rows = attempts[attempt_id]
        validate_attempt_prefix(campaign_id, stage_mode, leg, attempt_id, attempt_rows)
        if len(attempt_rows) == expected_count:
            complete.append(attempt_id)
        else:
            notes.append(
                f"{LEG_NAMES[leg]} attempt {attempt_id}: ignored canonical partial "
                f"{len(attempt_rows)}/{expected_count}"
            )
    if not complete:
        raise DataQualityError(
            f"campaign {campaign_id} stage {stage_mode} {LEG_NAMES[leg]}: "
            f"no complete valid attempt; available attempts={sorted(attempts)}"
        )
    selected = max(complete)
    for attempt_id in complete:
        if attempt_id != selected:
            notes.append(
                f"{LEG_NAMES[leg]} attempt {attempt_id}: ignored complete superseded "
                f"by deterministic highest complete attempt {selected}"
            )
    return selected, attempts[selected], notes


def reference_map(stage_mode: int, rows: Sequence[Row]) -> dict[float, Vec3]:
    if stage_mode in (15, 16):
        return {0.0: mean_vec((rows[0].center, rows[-1].center))}
    return {
        0.0: mean_vec((rows[0].center, rows[4].center, rows[15].center, rows[19].center)),
        90.0: mean_vec((rows[1].center, rows[16].center)),
        180.0: mean_vec((rows[2].center, rows[17].center)),
        270.0: mean_vec((rows[3].center, rows[18].center)),
    }


def reference_for_sample(stage_mode: int, references: dict[float, Vec3], pose: Pose) -> Vec3:
    if stage_mode in (15, 16):
        return references[0.0]
    for c_deg, reference in references.items():
        if angular_difference_deg(pose[1], c_deg) <= POSE_TOL_DEG:
            return reference
    raise AnalysisError(f"stage {stage_mode}: no same-C B0 reference for pose {pose}")


def semantic_role(stage_mode: int, sample_seq: int) -> str:
    if sample_seq in MEASUREMENT_SEQUENCES[stage_mode]:
        return "measurement"
    midpoint = len(MODE_POSES[stage_mode]) // 2
    return "reference_open" if sample_seq <= midpoint else "reference_close"


def build_closure_results(
    stage_mode: int,
    legs: dict[int, list[Row]],
) -> tuple[ClosureResult, ...]:
    results: list[ClosureResult] = []

    def add_pair(label: str, first_seq: int, last_seq: int, quality_gate: bool) -> None:
        results.append(
            ClosureResult(
                label=label,
                quality_gate=quality_gate,
                vectors={
                    leg: sub(
                        legs[leg][last_seq - 1].center,
                        legs[leg][first_seq - 1].center,
                    )
                    for leg in LEG_NAMES
                },
            )
        )

    def add_mean_pair(
        label: str,
        opening_seqs: Sequence[int],
        closing_seqs: Sequence[int],
        quality_gate: bool,
    ) -> None:
        results.append(
            ClosureResult(
                label=label,
                quality_gate=quality_gate,
                vectors={
                    leg: sub(
                        mean_vec(tuple(legs[leg][seq - 1].center for seq in closing_seqs)),
                        mean_vec(tuple(legs[leg][seq - 1].center for seq in opening_seqs)),
                    )
                    for leg in LEG_NAMES
                },
            )
        )

    if stage_mode == 15:
        add_pair("B0 C0 first-to-last", 1, 5, True)
    elif stage_mode == 16:
        add_pair("B0 C0 outer first-to-last", 1, 10, True)
        add_pair("B+5 C0 within-group", 2, 5, False)
        add_pair("B-5 C0 within-group", 6, 9, False)
    else:
        b_magnitude = 10 if stage_mode == 17 else 30
        add_pair("B0 C0 first-to-last", 1, 20, True)
        add_pair("opening B0 C0 within-sweep", 1, 5, True)
        add_pair(f"B+{b_magnitude} C0 within-group", 6, 10, False)
        add_pair(f"B-{b_magnitude} C0 within-group", 11, 15, False)
        add_pair("closing B0 C0 within-sweep", 16, 20, True)
        add_mean_pair("same-C B0 C0 opening-to-closing", (1, 5), (16, 20), True)
        add_pair("same-C B0 C90 opening-to-closing", 2, 17, True)
        add_pair("same-C B0 C180 opening-to-closing", 3, 18, True)
        add_pair("same-C B0 C270 opening-to-closing", 4, 19, True)
    return tuple(results)


def validate_source_order(rows: Sequence[Row]) -> None:
    """Enforce the physical S1 -> L -> S2, stage, and campaign chronology."""
    campaign_blocks: list[str] = []
    for row in rows:
        if not campaign_blocks or campaign_blocks[-1] != row.campaign_id:
            campaign_blocks.append(row.campaign_id)
    if len(campaign_blocks) != len(set(campaign_blocks)):
        raise AnalysisError(
            "campaign rows are interleaved or a completed campaign ID was reused: "
            f"{campaign_blocks}"
        )

    expected_modes = tuple(sorted(MODE_POSES))
    for campaign_id in campaign_blocks:
        campaign_rows = [row for row in rows if row.campaign_id == campaign_id]
        run_blocks: list[tuple[int, int, int]] = []
        for row in campaign_rows:
            key = (row.leg_id, row.stage_mode, row.attempt_id)
            if not run_blocks or run_blocks[-1] != key:
                run_blocks.append(key)
        if len(run_blocks) != len(set(run_blocks)):
            raise AnalysisError(
                f"campaign {campaign_id}: a leg/stage/attempt block was interleaved "
                f"or reused: {run_blocks}"
            )

        leg_order = [leg for leg, _stage, _attempt in run_blocks]
        if leg_order != sorted(leg_order):
            raise AnalysisError(
                f"campaign {campaign_id}: source order must be S1 then L then S2; "
                f"observed leg blocks {leg_order}"
            )

        modes_by_leg: dict[int, tuple[int, ...]] = {}
        for leg in LEG_NAMES:
            stage_blocks = [
                stage for block_leg, stage, _attempt in run_blocks if block_leg == leg
            ]
            collapsed: list[int] = []
            for stage in stage_blocks:
                if not collapsed or collapsed[-1] != stage:
                    collapsed.append(stage)
            if len(collapsed) != len(set(collapsed)):
                raise AnalysisError(
                    f"campaign {campaign_id} {LEG_NAMES[leg]}: a completed stage "
                    f"was revisited out of order: {collapsed}"
                )
            expected_prefix = expected_modes[: len(collapsed)]
            if tuple(collapsed) != expected_prefix:
                raise AnalysisError(
                    f"campaign {campaign_id} {LEG_NAMES[leg]}: stages must run in "
                    f"15,16,17,18 order without gaps; observed {collapsed}"
                )
            modes_by_leg[leg] = tuple(collapsed)

        if modes_by_leg[2] and modes_by_leg[2] != modes_by_leg[1][: len(modes_by_leg[2])]:
            raise AnalysisError(
                f"campaign {campaign_id}: L stages {modes_by_leg[2]} are not an "
                f"accepted prefix of S1 stages {modes_by_leg[1]}"
            )
        if modes_by_leg[3] and modes_by_leg[3] != modes_by_leg[2][: len(modes_by_leg[3])]:
            raise AnalysisError(
                f"campaign {campaign_id}: S2 stages {modes_by_leg[3]} are not an "
                f"accepted prefix of L stages {modes_by_leg[2]}"
            )


def analyze_rows(rows: Sequence[Row]) -> list[StageResult]:
    validate_source_order(rows)
    stages: dict[tuple[str, int], dict[int, list[Row]]] = defaultdict(
        lambda: {leg: [] for leg in LEG_NAMES}
    )
    for row in rows:
        stages[(row.campaign_id, row.stage_mode)][row.leg_id].append(row)

    results = []
    for (campaign_id, stage_mode), all_attempt_rows in sorted(stages.items()):
        legs: dict[int, list[Row]] = {}
        selected_attempts = {}
        ignored_attempts = []
        for leg in LEG_NAMES:
            if not all_attempt_rows[leg]:
                raise DataQualityError(
                    f"campaign {campaign_id} stage {stage_mode}: missing {LEG_NAMES[leg]} leg"
                )
            attempt_id, selected_rows, notes = select_attempt(
                campaign_id, stage_mode, leg, all_attempt_rows[leg]
            )
            selected_attempts[leg] = attempt_id
            legs[leg] = selected_rows
            ignored_attempts.extend(notes)

        references = {leg: reference_map(stage_mode, legs[leg]) for leg in LEG_NAMES}
        opening = {leg: legs[leg][0].center for leg in LEG_NAMES}
        closing = {leg: legs[leg][-1].center for leg in LEG_NAMES}
        closures = {leg: sub(closing[leg], opening[leg]) for leg in LEG_NAMES}
        closure_results = build_closure_results(stage_mode, legs)

        sample_results = []
        for index, expected_pose in enumerate(MODE_POSES[stage_mode], start=1):
            absolute_centers = {
                leg: legs[leg][index - 1].center for leg in LEG_NAMES
            }
            absolute_bracketed_short_center = scale(
                add(absolute_centers[1], absolute_centers[3]), 0.5
            )
            effective_center_offset = sub(
                absolute_centers[2], absolute_bracketed_short_center
            )
            relative = {
                leg: sub(
                    absolute_centers[leg],
                    reference_for_sample(stage_mode, references[leg], expected_pose),
                )
                for leg in LEG_NAMES
            }
            drift = sub(relative[3], relative[1])
            bracketed_short = scale(add(relative[1], relative[3]), 0.5)
            length_delta = sub(relative[2], bracketed_short)
            sample_results.append(
                SampleResult(
                    sample_seq=index,
                    pose=expected_pose,
                    role=semantic_role(stage_mode, index),
                    absolute_centers=absolute_centers,
                    absolute_bracketed_short_center=absolute_bracketed_short_center,
                    effective_center_offset=effective_center_offset,
                    relative=relative,
                    s2_minus_s1=drift,
                    bracketed_short=bracketed_short,
                    long_minus_short=length_delta,
                    length_slope=scale(length_delta, 1.0 / LENGTH_SEPARATION_MM),
                )
            )

        measurements = [sample for sample in sample_results if sample.role == "measurement"]
        results.append(
            StageResult(
                campaign_id=campaign_id,
                stage_mode=stage_mode,
                row_count=sum(len(all_attempt_rows[leg]) for leg in LEG_NAMES),
                selected_row_count=sum(len(legs[leg]) for leg in LEG_NAMES),
                selected_attempts=selected_attempts,
                ignored_attempts=tuple(ignored_attempts),
                references=references,
                opening_b0c0=opening,
                closing_b0c0=closing,
                opening_effective_center_offset=sub(
                    opening[2], scale(add(opening[1], opening[3]), 0.5)
                ),
                closing_effective_center_offset=sub(
                    closing[2], scale(add(closing[1], closing[3]), 0.5)
                ),
                closures=closures,
                closure_results=closure_results,
                samples=tuple(sample_results),
                leg_metrics={
                    leg: rms_max(sample.relative[leg] for sample in measurements)
                    for leg in LEG_NAMES
                },
                drift_metric=rms_max(sample.s2_minus_s1 for sample in measurements),
                length_delta_metric=rms_max(
                    sample.long_minus_short for sample in measurements
                ),
            )
        )
    return results


def measurement_samples(stage: StageResult) -> list[SampleResult]:
    return [sample for sample in stage.samples if sample.role == "measurement"]


def evaluate_quality(results: Sequence[StageResult]) -> QualityAssessment:
    failures = []
    advisories = [
        "CSV checks do not verify the run manifest, ring qualification, mechanics, "
        "temperature, or physical clearance."
    ]
    for stage in results:
        prefix = f"campaign {stage.campaign_id} stage {stage.stage_mode}"
        for closure in stage.closure_results:
            for leg in (1, 2, 3):
                magnitude = norm(closure.vectors[leg])
                message = (
                    f"{prefix} {LEG_NAMES[leg]} {closure.label} closure "
                    f"{magnitude:.6f} mm exceeds {CLOSURE_LIMIT_MM:.6f} mm"
                )
                if closure.quality_gate and magnitude > CLOSURE_LIMIT_MM:
                    failures.append(message)
                elif not closure.quality_gate and magnitude > CLOSURE_LIMIT_MM:
                    advisories.append(message + " (diagnostic repeat, not an acceptance gate)")

        drift_rms, drift_max = stage.drift_metric
        if drift_rms > SHORT_DRIFT_RMS_LIMIT_MM:
            failures.append(
                f"{prefix} normalized S2-S1 RMS {drift_rms:.6f} mm exceeds "
                f"{SHORT_DRIFT_RMS_LIMIT_MM:.6f} mm"
            )
        if drift_max > SHORT_DRIFT_MAX_LIMIT_MM:
            failures.append(
                f"{prefix} normalized S2-S1 max {drift_max:.6f} mm exceeds "
                f"{SHORT_DRIFT_MAX_LIMIT_MM:.6f} mm"
            )

        if stage.stage_mode == 16:
            for leg in (1, 2, 3):
                maximum = stage.leg_metrics[leg][1]
                if maximum >= PRODUCTION_MAX_LIMIT_MM:
                    failures.append(
                        f"{prefix} {LEG_NAMES[leg]} production-envelope max "
                        f"{maximum:.6f} mm is not below {PRODUCTION_MAX_LIMIT_MM:.6f} mm"
                    )
                elif maximum >= PRODUCTION_PREFERRED_MAX_MM:
                    advisories.append(
                        f"{prefix} {LEG_NAMES[leg]} max {maximum:.6f} mm passes the "
                        f"core limit but not the preferred <{PRODUCTION_PREFERRED_MAX_MM:.6f} mm"
                    )

    modes_by_campaign: dict[str, set[int]] = defaultdict(set)
    for stage in results:
        modes_by_campaign[stage.campaign_id].add(stage.stage_mode)
    for campaign_id, modes in sorted(modes_by_campaign.items()):
        if 16 not in modes:
            advisories.append(
                f"campaign {campaign_id} has no stage 16; production-envelope acceptance "
                "was not evaluated"
            )
        if modes != set(MODE_POSES):
            advisories.append(
                f"campaign {campaign_id} is a valid staged prefix, not the full 15-18 grid: "
                f"stages {sorted(modes)}"
            )
    return QualityAssessment(not failures, tuple(failures), tuple(advisories))


def metric_text(vectors: Iterable[Vec3]) -> str:
    rms, maximum = rms_max(vectors)
    return f"{rms:.6f}/{maximum:.6f}"


def b_sign(b_deg: float) -> str:
    if b_deg > POSE_TOL_DEG:
        return "B+"
    if b_deg < -POSE_TOL_DEG:
        return "B-"
    return "B0"


def c_label(c_deg: float) -> str:
    return f"C{c_deg:+g}" if c_deg < 0.0 else f"C{c_deg:g}"


def format_group_summaries(stage: StageResult) -> list[str]:
    samples = measurement_samples(stage)
    lines = ["B-sign summary, RMS/max mm (S1 | L | S2 | L-short):"]
    sign_order = {"B+": 0, "B-": 1, "B0": 2}
    by_sign: dict[str, list[SampleResult]] = defaultdict(list)
    for sample in samples:
        by_sign[b_sign(sample.pose[0])].append(sample)
    for label in sorted(by_sign, key=lambda value: sign_order[value]):
        group = by_sign[label]
        metrics = [metric_text(sample.relative[leg] for sample in group) for leg in (1, 2, 3)]
        metrics.append(metric_text(sample.long_minus_short for sample in group))
        lines.append(f"  {label}: n={len(group)}  " + " | ".join(metrics))

    lines.append("C-angle/quadrant summary, RMS/max mm (S1 | L | S2 | L-short):")
    by_c: dict[float, list[SampleResult]] = defaultdict(list)
    for sample in samples:
        by_c[sample.pose[1]].append(sample)
    for c_deg in sorted(by_c, key=lambda value: value % 360.0):
        group = by_c[c_deg]
        metrics = [metric_text(sample.relative[leg] for sample in group) for leg in (1, 2, 3)]
        metrics.append(metric_text(sample.long_minus_short for sample in group))
        lines.append(f"  {c_label(c_deg)}: n={len(group)}  " + " | ".join(metrics))
    return lines


def balanced_sequence_pairs(stage_mode: int) -> tuple[tuple[int, int], ...]:
    if stage_mode == 16:
        return tuple(zip(range(2, 6), range(6, 10)))
    if stage_mode in (17, 18):
        return tuple(zip(range(6, 11), range(11, 16)))
    return ()


def format_balanced_summary(stage: StageResult) -> list[str]:
    pairs = balanced_sequence_pairs(stage.stage_mode)
    if not pairs:
        return []
    by_seq = {sample.sample_seq: sample for sample in stage.samples}
    occurrences: dict[float, int] = defaultdict(int)
    lines = [
        "Balanced +B/-B summary: average=(+B+-B)/2, "
        "antisymmetric half-difference=(+B--B)/2"
    ]
    for positive_seq, negative_seq in pairs:
        positive = by_seq[positive_seq]
        negative = by_seq[negative_seq]
        occurrences[positive.pose[1]] += 1
        occurrence = occurrences[positive.pose[1]]
        label = (
            f"|B|={abs(positive.pose[0]):g} {c_label(positive.pose[1])} "
            f"occurrence {occurrence} (seq {positive_seq}/{negative_seq})"
        )
        lines.append(f"  {label}:")
        vectors = [(LEG_NAMES[leg], positive.relative[leg], negative.relative[leg]) for leg in (1, 2, 3)]
        vectors.append(("L-short", positive.long_minus_short, negative.long_minus_short))
        for name, positive_vector, negative_vector in vectors:
            balanced = scale(add(positive_vector, negative_vector), 0.5)
            antisymmetric = scale(sub(positive_vector, negative_vector), 0.5)
            lines.append(
                f"    {name}: avg {vec_text(balanced)} mm; "
                f"anti {vec_text(antisymmetric)} mm"
            )
    return lines


def vec_text(vector: Vec3) -> str:
    return f"({vector[0]:+.6f}, {vector[1]:+.6f}, {vector[2]:+.6f})"


def format_report(
    path: Path,
    row_count: int,
    results: Sequence[StageResult],
    assessment: QualityAssessment | None = None,
) -> str:
    if assessment is None:
        assessment = evaluate_quality(results)
    status = "PASS" if assessment.passed else "FAIL"
    lines = [
        "TCPC long/short paired analysis",
        f"CSV data-quality status: {status}",
        f"source: {path}",
        f"validated rows: {row_count}",
        f"tool-length separation: {LENGTH_SEPARATION_MM:.6f} mm",
        "sequence: exact semantic slots retained; no coordinate-only duplicate collapse",
        "exit codes: 0=CSV quality pass, 1=data-quality/acceptance fail, 2=input/schema/sequence error",
    ]
    for failure in assessment.failures:
        lines.append(f"FAIL: {failure}")
    for advisory in assessment.advisories:
        lines.append(f"ADVISORY: {advisory}")
    for stage in results:
        lines.extend(
            [
                "",
                f"campaign {stage.campaign_id}, stage {stage.stage_mode}",
                f"rows: {stage.row_count} input / {stage.selected_row_count} selected; "
                f"aligned samples: {len(stage.samples)}",
                "selected attempts: "
                + ", ".join(
                    f"{LEG_NAMES[leg]}={stage.selected_attempts[leg]}" for leg in (1, 2, 3)
                ),
                "closure evidence:",
            ]
        )
        for note in stage.ignored_attempts:
            lines.append(f"WARNING: {note}")
        for closure in stage.closure_results:
            gate_label = "quality gate" if closure.quality_gate else "diagnostic"
            lines.append(f"  {closure.label} [{gate_label}]:")
            for leg in (1, 2, 3):
                closure_norm = norm(closure.vectors[leg])
                closure_status = (
                    "PASS" if closure_norm <= CLOSURE_LIMIT_MM else "EXCEEDS 0.05 MM"
                )
                lines.append(
                    f"    {LEG_NAMES[leg]}: {vec_text(closure.vectors[leg])} mm; "
                    f"norm {closure_norm:.6f} [{closure_status}]"
                )
        lines.append("reference means:")
        for leg in (1, 2, 3):
            references = ", ".join(
                f"C{c_deg:g}={vec_text(center)}" for c_deg, center in sorted(stage.references[leg].items())
            )
            lines.append(f"  {LEG_NAMES[leg]}: {references} mm")
        reference_drift = sub(stage.references[3][0.0], stage.references[1][0.0])
        lines.append(
            f"  S2-S1 C0 reference drift: {vec_text(reference_drift)} mm; "
            f"norm {norm(reference_drift):.6f}"
        )
        lines.append(
            "absolute long-vs-bracketed-short center offsets "
            "(raw aligned centers; not B0-referenced):"
        )
        lines.append(
            "  opening B0 C0 effective center offset: "
            f"{vec_text(stage.opening_effective_center_offset)} mm; "
            f"norm {norm(stage.opening_effective_center_offset):.6f}"
        )
        lines.append(
            "  closing B0 C0 effective center offset: "
            f"{vec_text(stage.closing_effective_center_offset)} mm; "
            f"norm {norm(stage.closing_effective_center_offset):.6f}"
        )
        lines.append("measurement-slot relative vector metrics:")
        for leg in (1, 2, 3):
            rms, maximum = stage.leg_metrics[leg]
            lines.append(f"  {LEG_NAMES[leg]} RMS/max: {rms:.6f} / {maximum:.6f} mm")
        lines.append(
            f"  normalized S2-S1 drift RMS/max: {stage.drift_metric[0]:.6f} / "
            f"{stage.drift_metric[1]:.6f} mm"
        )
        lines.append(
            f"  L-bracketed-short RMS/max: {stage.length_delta_metric[0]:.6f} / "
            f"{stage.length_delta_metric[1]:.6f} mm"
        )
        lines.extend(format_group_summaries(stage))
        lines.extend(format_balanced_summary(stage))
        lines.append("aligned semantic samples:")
        lines.append(
            "  seq role             B       C       S2-S1 XYZ mm                    "
            "short-mid XYZ mm                L-short XYZ mm                  "
            "|L-short|  slope(rad)  deg"
        )
        for sample in stage.samples:
            delta_norm = norm(sample.long_minus_short)
            slope_norm = norm(sample.length_slope)
            lines.append(
                f"  {sample.sample_seq:3d} {sample.role:<16} "
                f"{sample.pose[0]:+7.3f} {sample.pose[1]:+7.3f}  "
                f"{vec_text(sample.s2_minus_s1):<31} "
                f"{vec_text(sample.bracketed_short):<31} "
                f"{vec_text(sample.long_minus_short):<31} "
                f"{delta_norm:9.6f}  {slope_norm:10.8f}  "
                f"{math.degrees(slope_norm):.6f}"
            )
    return "\n".join(lines)


def derived_row(stage: StageResult, sample: SampleResult) -> dict[str, str | int]:
    row: dict[str, str | int] = {
        "campaign_id": stage.campaign_id,
        "stage_mode": stage.stage_mode,
        "s1_attempt_id": stage.selected_attempts[1],
        "long_attempt_id": stage.selected_attempts[2],
        "s2_attempt_id": stage.selected_attempts[3],
        "sample_seq": sample.sample_seq,
        "semantic_role": sample.role,
        "abs_b_deg": f"{sample.pose[0]:.6f}",
        "abs_c_deg": f"{sample.pose[1]:.6f}",
    }

    def put_vector(prefix: str, vector: Vec3, units: str = "mm") -> None:
        suffix = f"_{units}" if units else ""
        for axis, value in zip("xyz", vector):
            row[f"{prefix}_{axis}{suffix}"] = f"{value:.9f}"
        row[f"{prefix}_norm{suffix}"] = f"{norm(vector):.9f}"

    put_vector("s1_absolute_center", sample.absolute_centers[1])
    put_vector("long_absolute_center", sample.absolute_centers[2])
    put_vector("s2_absolute_center", sample.absolute_centers[3])
    put_vector(
        "absolute_bracketed_short_center",
        sample.absolute_bracketed_short_center,
    )
    put_vector("effective_center_offset", sample.effective_center_offset)
    put_vector("s1_rel", sample.relative[1])
    put_vector("long_rel", sample.relative[2])
    put_vector("s2_rel", sample.relative[3])
    put_vector("s2_minus_s1", sample.s2_minus_s1)
    put_vector("bracketed_short", sample.bracketed_short)
    put_vector("long_minus_short", sample.long_minus_short)
    for axis, value in zip("xyz", sample.length_slope):
        row[f"length_slope_{axis}"] = f"{value:.12f}"
    slope_norm = norm(sample.length_slope)
    row["length_slope_norm_rad_approx"] = f"{slope_norm:.12f}"
    row["length_slope_norm_deg_approx"] = f"{math.degrees(slope_norm):.9f}"
    return row


def write_derived_csv(path: Path, results: Sequence[StageResult]) -> None:
    try:
        with path.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(handle, fieldnames=DERIVED_COLUMNS)
            writer.writeheader()
            for stage in results:
                for sample in stage.samples:
                    writer.writerow(derived_row(stage, sample))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AnalysisError(f"cannot write {path}: {exc}") from exc


def synthetic_raw_row(
    campaign: str,
    leg: int,
    stage: int,
    attempt: int,
    sample_seq: int,
    pose: Pose,
    center: Vec3,
) -> dict[str, str]:
    tool, length = LEG_EXPECTATIONS[leg]
    calibration = 0.134533 if leg in (1, 3) else 0.151000
    b_deg, c_deg = pose
    motor_cmd = (center[0] + 100.0, center[1] + 200.0, center[2] + 300.0)
    following_error = (0.000001, -0.000001, 0.0)
    motor_fb = add(motor_cmd, following_error)
    values: dict[str, float | int | str] = {
        "campaign_id": campaign,
        "leg_id": leg,
        "stage_mode": stage,
        "attempt_id": attempt,
        "sample_seq": sample_seq,
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


def run_self_test() -> None:
    raw_rows: list[dict[str, str]] = []
    expected_absolute_offset = (0.125, -0.050, 0.200)
    translations = {
        1: (10.0, 20.0, 30.0),
        2: (11.125, 18.950, 31.200),
        3: (12.0, 18.0, 32.0),
    }
    c_reference = {
        0.0: (0.0, 0.0, 0.0),
        90.0: (0.15, -0.03, 0.02),
        180.0: (-0.04, 0.08, -0.01),
        270.0: (0.02, 0.01, 0.06),
    }

    # Canonical mode 15 with independent translations, retained abort prefixes,
    # and deterministic selection of the highest complete attempt.
    for leg in (1, 2, 3):
        if leg == 1:
            for sample_seq, pose in enumerate(MODE_POSES[15][:2], start=1):
                center = add(translations[leg], c_reference[pose[1]])
                raw_rows.append(
                    synthetic_raw_row("zero", leg, 15, 1, sample_seq, pose, center)
                )
            selected_attempt = 2
        elif leg == 2:
            for sample_seq, pose in enumerate(MODE_POSES[15], start=1):
                center = add(translations[leg], c_reference[pose[1]])
                raw_rows.append(
                    synthetic_raw_row("zero", leg, 15, 1, sample_seq, pose, center)
                )
            selected_attempt = 2
        else:
            selected_attempt = 1
        for sample_seq, pose in enumerate(MODE_POSES[15], start=1):
            center = add(translations[leg], c_reference[pose[1]])
            raw_rows.append(
                synthetic_raw_row(
                    "zero", leg, 15, selected_attempt, sample_seq, pose, center
                )
            )

    # Canonical tool-major 15/16/17 chronology. Mode 17 has four distinct
    # B0/C0 samples and a known length slope.
    expected_slope = (0.001, -0.002, 0.0005)
    short_drift = (0.007, -0.004, 0.002)
    for leg in (1, 2, 3):
        for stage in (15, 16):
            for sample_seq, pose in enumerate(MODE_POSES[stage], start=1):
                raw_rows.append(
                    synthetic_raw_row(
                        "known-slope",
                        leg,
                        stage,
                        1,
                        sample_seq,
                        pose,
                        translations[leg],
                    )
                )
        for sample_seq, pose in enumerate(MODE_POSES[17], start=1):
            b_deg, c_deg = pose
            residual = (0.0, 0.0, 0.0)
            if sample_seq in MEASUREMENT_SEQUENCES[17]:
                residual = (
                    (0.002 * b_deg) + (0.001 * sample_seq),
                    (-0.001 * b_deg) + (0.0005 * sample_seq),
                    0.0003 * sample_seq,
                )
                if leg == 1:
                    residual = sub(residual, short_drift)
                elif leg == 3:
                    residual = add(residual, short_drift)
                else:
                    residual = add(residual, scale(expected_slope, LENGTH_SEPARATION_MM))
            center = add(add(translations[leg], c_reference[c_deg]), residual)
            raw_rows.append(
                synthetic_raw_row("known-slope", leg, 17, 1, sample_seq, pose, center)
            )

    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=REQUIRED_COLUMNS)
    writer.writeheader()
    writer.writerows(raw_rows)
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "synthetic.csv"
        path.write_text(stream.getvalue(), encoding="ascii")
        rows = read_rows(path)
        if rows[0].accepted_endpoint != translations[1]:
            raise AssertionError("accepted endpoint state was not retained in Row")
        if rows[0].linear_following_error != (0.000001, -0.000001, 0.0):
            raise AssertionError("linear following-error state was not retained in Row")
        if rows[0].linear_motor_cmd != (110.0, 220.0, 330.0):
            raise AssertionError("linear motor-command state was not retained in Row")
        if rows[0].linear_motor_fb != (110.000001, 219.999999, 330.0):
            raise AssertionError("linear motor-feedback state was not retained in Row")
        analyzed = analyze_rows(rows)
        results = {(item.campaign_id, item.stage_mode): item for item in analyzed}
        assessment = evaluate_quality(analyzed)
        if not assessment.passed:
            raise AssertionError(f"valid synthetic campaign failed quality gates: {assessment.failures}")
        report = format_report(path, len(rows), analyzed, assessment)
        if "selected attempts: S1=2, L=2, S2=1" not in report:
            raise AssertionError("report omitted deterministic selected-attempt IDs")
        if "ignored canonical partial" not in report or "ignored complete superseded" not in report:
            raise AssertionError("report omitted ignored-attempt warnings")
        for required_text in (
            "same-C B0 C90 opening-to-closing",
            "opening B0 C0 effective center offset: (+0.125000, -0.050000, +0.200000) mm",
            "closing B0 C0 effective center offset: (+0.125000, -0.050000, +0.200000) mm",
            "B-sign summary",
            "C-angle/quadrant summary",
            "Balanced +B/-B summary",
        ):
            if required_text not in report:
                raise AssertionError(f"report omitted {required_text!r}")
        derived_path = Path(temp_dir) / "derived.csv"
        write_derived_csv(derived_path, analyzed)
        with derived_path.open(newline="", encoding="ascii") as handle:
            derived_rows = list(csv.DictReader(handle))
        if len(derived_rows) != 40:
            raise AssertionError(f"derived CSV row count was {len(derived_rows)}, expected 40")
        zero_derived = next(
            row
            for row in derived_rows
            if row["campaign_id"] == "zero" and row["sample_seq"] == "1"
        )
        derived_offset = tuple(
            float(zero_derived[f"effective_center_offset_{axis}_mm"])
            for axis in "xyz"
        )
        if norm(sub(derived_offset, expected_absolute_offset)) > 1e-10:
            raise AssertionError(
                "derived CSV did not preserve the synthetic absolute center offset"
            )

        captured_out = io.StringIO()
        captured_err = io.StringIO()
        with redirect_stdout(captured_out), redirect_stderr(captured_err):
            accepted_exit = main([str(path)])
        if accepted_exit != EXIT_ACCEPTED:
            raise AssertionError(f"valid campaign returned exit {accepted_exit}")

        bad_state_path = Path(temp_dir) / "bad-state.csv"
        bad_state = dict(raw_rows[0])
        bad_state["tcpc_enabled"] = "0"
        bad_stream = io.StringIO()
        bad_writer = csv.DictWriter(bad_stream, fieldnames=REQUIRED_COLUMNS)
        bad_writer.writeheader()
        bad_writer.writerow(bad_state)
        bad_state_path.write_text(bad_stream.getvalue(), encoding="ascii")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            quality_exit = main([str(bad_state_path)])
        if quality_exit != EXIT_DATA_QUALITY:
            raise AssertionError(f"bad live state returned exit {quality_exit}, expected 1")

        failed_acceptance_rows = [dict(row) for row in raw_rows]
        for row in failed_acceptance_rows:
            if (
                row["campaign_id"] == "zero"
                and row["leg_id"] == "1"
                and row["attempt_id"] == "2"
                and row["sample_seq"] == "5"
            ):
                row["center_abs_x_mm"] = str(float(row["center_abs_x_mm"]) + 0.050001)
        failed_acceptance_path = Path(temp_dir) / "failed-acceptance.csv"
        failed_stream = io.StringIO()
        failed_writer = csv.DictWriter(failed_stream, fieldnames=REQUIRED_COLUMNS)
        failed_writer.writeheader()
        failed_writer.writerows(failed_acceptance_rows)
        failed_acceptance_path.write_text(failed_stream.getvalue(), encoding="ascii")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            acceptance_exit = main([str(failed_acceptance_path)])
        if acceptance_exit != EXIT_DATA_QUALITY:
            raise AssertionError(
                f"closure acceptance failure returned exit {acceptance_exit}, expected 1"
            )

        header_only_path = Path(temp_dir) / "header-only.csv"
        header_only_path.write_text(",".join(REQUIRED_COLUMNS) + "\n", encoding="ascii")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            input_exit = main([str(header_only_path)])
        if input_exit != EXIT_INPUT_ERROR:
            raise AssertionError(f"header-only input returned exit {input_exit}, expected 2")

    zero = results[("zero", 15)]
    if len(zero.samples) != 5:
        raise AssertionError("mode 15 semantic sample count was not preserved")
    if zero.selected_attempts != {1: 2, 2: 2, 3: 1}:
        raise AssertionError(f"wrong attempts selected: {zero.selected_attempts}")
    if len(zero.ignored_attempts) != 2:
        raise AssertionError(f"wrong ignored-attempt notes: {zero.ignored_attempts}")
    if any(norm(sample.long_minus_short) > 1e-10 for sample in zero.samples):
        raise AssertionError("zero-case length delta was not zero")
    for sample in zero.samples:
        if norm(sub(sample.effective_center_offset, expected_absolute_offset)) > 1e-10:
            raise AssertionError(
                "constant absolute center offset was lost during per-leg normalization"
            )
        expected_long_center = add(translations[2], c_reference[sample.pose[1]])
        if norm(sub(sample.absolute_centers[2], expected_long_center)) > 1e-10:
            raise AssertionError("absolute long-probe center was not retained")
        expected_short_center = add((11.0, 19.0, 31.0), c_reference[sample.pose[1]])
        if norm(sub(sample.absolute_bracketed_short_center, expected_short_center)) > 1e-10:
            raise AssertionError("absolute bracketed-short center was calculated incorrectly")
    if norm(sub(zero.opening_effective_center_offset, expected_absolute_offset)) > 1e-10:
        raise AssertionError("opening B0 C0 absolute center offset was not retained")
    if norm(sub(zero.closing_effective_center_offset, expected_absolute_offset)) > 1e-10:
        raise AssertionError("closing B0 C0 absolute center offset was not retained")

    known = results[("known-slope", 17)]
    if len(known.samples) != 20:
        raise AssertionError("mode 17 duplicate coordinate occurrences were collapsed")
    for sample in known.samples:
        if sample.role != "measurement":
            continue
        if norm(sub(sample.length_slope, expected_slope)) > 1e-10:
            raise AssertionError(
                f"known-slope mismatch at sample {sample.sample_seq}: "
                f"{sample.length_slope} != {expected_slope}"
            )

    # Acceptance boundaries are separate from structural validity.
    zero_closure = ClosureResult(
        "synthetic closure", True, {1: (0.05, 0.0, 0.0), 2: (0.0, 0.0, 0.0), 3: (0.0, 0.0, 0.0)}
    )
    boundary_stage = replace(
        zero,
        closure_results=(zero_closure,),
        drift_metric=(SHORT_DRIFT_RMS_LIMIT_MM, SHORT_DRIFT_MAX_LIMIT_MM),
    )
    if not evaluate_quality((boundary_stage,)).passed:
        raise AssertionError("inclusive closure/drift quality boundary did not pass")
    failed_closure = replace(
        zero_closure,
        vectors={1: (0.050001, 0.0, 0.0), 2: (0.0, 0.0, 0.0), 3: (0.0, 0.0, 0.0)},
    )
    if evaluate_quality((replace(boundary_stage, closure_results=(failed_closure,)),)).passed:
        raise AssertionError("closure above 0.05 mm was accepted")
    if evaluate_quality(
        (replace(boundary_stage, drift_metric=(0.050001, SHORT_DRIFT_MAX_LIMIT_MM)),)
    ).passed:
        raise AssertionError("S1-S2 RMS above 0.05 mm was accepted")

    stage16 = results[("known-slope", 16)]
    production_at_limit = replace(
        stage16,
        leg_metrics={
            1: (0.0, PRODUCTION_MAX_LIMIT_MM),
            2: stage16.leg_metrics[2],
            3: stage16.leg_metrics[3],
        },
    )
    if evaluate_quality((production_at_limit,)).passed:
        raise AssertionError("production max equal to 0.20 mm was accepted")

    # Missing, duplicated, or reordered samples must fail before analysis.
    malformed = [row for row in rows if not (
        row.campaign_id == "known-slope" and row.leg_id == 3 and row.sample_seq == 20
    )]
    try:
        analyze_rows(malformed)
    except DataQualityError:
        pass
    else:
        raise AssertionError("partial semantic sequence was accepted")

    reordered = list(rows)
    indexes = [
        index for index, row in enumerate(reordered)
        if row.campaign_id == "known-slope" and row.leg_id == 2 and row.stage_mode == 17
    ]
    reordered[indexes[5]], reordered[indexes[6]] = reordered[indexes[6]], reordered[indexes[5]]
    try:
        analyze_rows(reordered)
    except AnalysisError:
        pass
    else:
        raise AssertionError("reordered semantic sequence was accepted")

    duplicated = list(rows)
    duplicate_index = next(
        index
        for index, row in enumerate(duplicated)
        if row.campaign_id == "known-slope"
        and row.leg_id == 2
        and row.stage_mode == 17
        and row.sample_seq == 6
    )
    duplicated.insert(duplicate_index + 1, duplicated[duplicate_index])
    try:
        analyze_rows(duplicated)
    except AnalysisError:
        pass
    else:
        raise AssertionError("duplicate semantic sample was accepted")

    zero_rows = [row for row in rows if row.campaign_id == "zero"]
    known_rows = [row for row in rows if row.campaign_id == "known-slope"]
    reversed_legs = (
        [row for row in zero_rows if row.leg_id == 2]
        + [row for row in zero_rows if row.leg_id == 1]
        + [row for row in zero_rows if row.leg_id == 3]
        + known_rows
    )
    try:
        analyze_rows(reversed_legs)
    except AnalysisError:
        pass
    else:
        raise AssertionError("L-before-S1 source order was accepted")

    skipped_stage = [
        row
        for row in rows
        if not (row.campaign_id == "known-slope" and row.stage_mode == 16)
    ]
    try:
        analyze_rows(skipped_stage)
    except AnalysisError:
        pass
    else:
        raise AssertionError("stage 17 without preceding stage 16 was accepted")

    bad = dict(raw_rows[0])
    bad["tcpc_enabled"] = "0"
    try:
        parse_row(bad, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("invalid TCPC state was accepted")

    bad_tlo = dict(raw_rows[0])
    bad_tlo["motion_tooloffset_z_mm"] = str(SHORT_LENGTH_MM + TLO_TOL_MM + 0.000001)
    try:
        parse_row(bad_tlo, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("out-of-tolerance live TLO was accepted")

    inconsistent_ferror = dict(raw_rows[0])
    inconsistent_ferror["joint_1_motor_following_error_fb_minus_cmd_mm"] = "0.000010"
    try:
        parse_row(inconsistent_ferror, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("inconsistent linear following error was accepted")

    nonfinite_endpoint = dict(raw_rows[0])
    nonfinite_endpoint["accepted_endpoint_abs_z_mm"] = "nan"
    try:
        parse_row(nonfinite_endpoint, 1, 2)
    except AnalysisError:
        pass
    else:
        raise AssertionError("non-finite accepted endpoint was accepted")

    with tempfile.TemporaryDirectory() as temp_dir:
        bad_header_path = Path(temp_dir) / "bad-header.csv"
        bad_header_path.write_text(
            ",".join(REQUIRED_COLUMNS[:-1]) + "\n",
            encoding="ascii",
        )
        try:
            read_rows(bad_header_path)
        except AnalysisError:
            pass
        else:
            raise AssertionError("non-exact CSV header was accepted")

    # Circular comparison must accept joint C=-20 reported as 340 deg while the
    # opposite-polarity C SSI reports the angularly equivalent +20 deg.
    wrapped = synthetic_raw_row("wrap", 1, 16, 1, 4, (5.0, -20.0), (1.0, 2.0, 3.0))
    wrapped["joint_c_cmd_deg"] = "340.0"
    wrapped["joint_c_fb_deg"] = "340.0001"
    wrapped["c_ssi_zeroed_deg"] = "20.0001"
    parse_row(wrapped, 1, 2)

    same_polarity = synthetic_raw_row(
        "bad-c-ssi-polarity", 1, 16, 1, 3, (5.0, 20.0), (1.0, 2.0, 3.0)
    )
    same_polarity["c_ssi_zeroed_deg"] = "20.0"
    try:
        parse_row(same_polarity, 1, 2)
    except DataQualityError:
        pass
    else:
        raise AssertionError("same-polarity C SSI state was accepted")

    print(
        "self-test passed: canonical sequences, retained occurrences, zero delta, "
        "preserved absolute center offset, known length slope, attempt selection, "
        "sample/run/stage order rejection, "
        "quality boundaries, live-state rejection, exact schema, linear-axis "
        "state validation, and C SSI polarity/wrapping"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Exit status: 0 when CSV quality/acceptance gates pass; 1 when logged "
            "machine state or analyzed data fails a gate; 2 for input, schema, "
            "sequence, or I/O errors."
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"isolated paired CSV (default: {DEFAULT_INPUT.name})",
    )
    parser.add_argument("--output", type=Path, help="write per-sample derived values to CSV")
    parser.add_argument("--self-test", action="store_true", help="run synthetic checks and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    try:
        rows = read_rows(args.input)
        results = analyze_rows(rows)
        assessment = evaluate_quality(results)
        print(format_report(args.input, len(rows), results, assessment))
        if args.output is not None:
            if args.output.resolve() == args.input.resolve():
                raise AnalysisError("--output must not overwrite the source calibration CSV")
            write_derived_csv(args.output, results)
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
