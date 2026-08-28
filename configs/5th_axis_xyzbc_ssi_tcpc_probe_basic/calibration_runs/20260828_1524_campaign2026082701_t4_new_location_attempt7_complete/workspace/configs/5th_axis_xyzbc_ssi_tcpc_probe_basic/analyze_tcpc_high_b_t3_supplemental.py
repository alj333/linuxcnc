#!/usr/bin/env python3
"""Validate and summarize the isolated T3 high-B sphere supplemental.

This analyzer is deliberately offline.  It reads the dedicated mode-20
geometry, state, and closure CSVs, enforces their frozen run identity and
reviewed sequence, then reports C-dependent center motion.  The four-contact
method has only one opposing-contact pair, so a V diameter is required and a U
diameter is not.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS = SCRIPT_DIR / "tcpc-high-b-t3-supplemental-results.csv"
DEFAULT_STATE = SCRIPT_DIR / "tcpc-high-b-t3-supplemental-state.csv"
DEFAULT_CLOSURES = SCRIPT_DIR / "tcpc-high-b-t3-supplemental-closures.csv"

SCHEMA_VERSION = 1
CAMPAIGN_ID = 2026082401
STAGE_MODE = 20
ATTEMPT_ID = 1
TOOL_NUMBER = 3
TOOL_LENGTH_MM = 128.606729
CALIBRATION_OFFSET_MM = 0.117658
PROBE_DIAMETER_MM = 6.0
SPHERE_RADIUS_MM = 15.0
EFFECTIVE_CONTACT_RADIUS_MM = (
    SPHERE_RADIUS_MM + PROBE_DIAMETER_MM / 2.0 - CALIBRATION_OFFSET_MM
)

POSE_TOL_DEG = 0.01
TLO_TOL_MM = 0.002
CALIBRATION_TOL_MM = 0.0005
DIAMETER_TOL_MM = 0.01
RADIUS_TOL_MM = 0.001
CONSISTENCY_TOL_MM = 0.000005
FOLLOWING_ERROR_CONSISTENCY_TOL_MM = 0.000002
MIN_TRAVEL_MM = 1.0
MAX_W_TRAVEL_MM = 7.001
MAX_SIDE_TRAVEL_MM = 6.001
MAX_CENTER_CORRECTION_MM = 0.250
MAX_RADIAL_RESIDUAL_MM = 0.250
MIN_V_DIAMETER_MM = 29.9
MAX_V_DIAMETER_MM = 30.5
MAX_PASS_CENTER_DELTA_MM = 0.100
CLOSURE_LIMIT_MM = 0.250

EXIT_ACCEPTED = 0
EXIT_DATA_QUALITY = 1
EXIT_INPUT_ERROR = 2

Vec3 = tuple[float, float, float]

RESULT_COLUMNS = (
    "schema_version",
    "campaign_id",
    "stage_mode",
    "attempt_id",
    "sample_seq",
    "block_id",
    "anchor_seq",
    "is_closure",
    "contact_count",
    "u_method_code",
    "abs_b_deg",
    "abs_c_deg",
    "live_tool_number",
    "expected_tool_length_mm",
    "probe_calibration_offset_mm",
    "probe_diameter_mm",
    "effective_contact_radius_mm",
    "center_abs_x_mm",
    "center_abs_y_mm",
    "center_abs_z_mm",
    "u_center_correction_mm",
    "v_center_correction_mm",
    "center_correction_norm_mm",
    "v_corrected_diameter_mm",
    "pass_center_delta_mm",
    "w_contact_radial_residual_mm",
    "u_contact_radial_residual_mm",
    "v_minus_contact_radial_residual_mm",
    "v_plus_contact_radial_residual_mm",
    "w_travel_mm",
    "u_travel_mm",
    "v_minus_travel_mm",
    "v_plus_travel_mm",
)

STATE_COLUMNS = (
    "schema_version",
    "campaign_id",
    "stage_mode",
    "attempt_id",
    "sample_seq",
    "abs_b_deg",
    "abs_c_deg",
    "persistent_correction_enabled",
    "tcpc_enabled",
    "twp_active",
    "twp_motion_enabled",
    "twp_valid",
    "b_ssi_invalid",
    "c_ssi_invalid",
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

CLOSURE_COLUMNS = (
    "schema_version",
    "campaign_id",
    "stage_mode",
    "attempt_id",
    "closure_id",
    "open_seq",
    "close_seq",
    "open_b_deg",
    "open_c_deg",
    "close_b_deg",
    "close_c_deg",
    "dx_mm",
    "dy_mm",
    "dz_mm",
    "norm_mm",
    "limit_mm",
    "passed",
)


class AnalysisError(ValueError):
    """The file, schema, or frozen run identity is invalid."""


class DataQualityError(ValueError):
    """The measurements do not form a complete accepted supplemental."""


@dataclass(frozen=True)
class ExpectedSample:
    seq: int
    b_deg: float
    c_deg: float
    block_id: int
    anchor_seq: int
    is_closure: int
    role: str


EXPECTED_SAMPLES = (
    ExpectedSample(1, 0.0, 0.0, 0, 1, 0, "B0 opening"),
    ExpectedSample(2, 45.0, 0.0, 45, 2, 0, "B45 C0 opening"),
    ExpectedSample(3, 45.0, 90.0, 45, 2, 0, "B45 C90"),
    ExpectedSample(4, 45.0, 180.0, 45, 2, 0, "B45 C180"),
    ExpectedSample(5, 45.0, 270.0, 45, 2, 0, "B45 C270"),
    ExpectedSample(6, 45.0, 0.0, 45, 2, 1, "B45 C0 closure"),
    ExpectedSample(7, 90.0, 0.0, 90, 7, 0, "B90 C0 opening"),
    ExpectedSample(8, 90.0, 90.0, 90, 7, 0, "B90 C90"),
    ExpectedSample(9, 90.0, 180.0, 90, 7, 0, "B90 C180"),
    ExpectedSample(10, 90.0, 270.0, 90, 7, 0, "B90 C270"),
    ExpectedSample(11, 90.0, 0.0, 90, 7, 1, "B90 C0 closure"),
    ExpectedSample(12, 0.0, 0.0, 190, 1, 1, "outer B0 C0 closure"),
)


@dataclass(frozen=True)
class ExpectedClosure:
    closure_id: int
    open_seq: int
    close_seq: int
    b_deg: float
    c_deg: float
    label: str


EXPECTED_CLOSURES = (
    ExpectedClosure(45, 2, 6, 45.0, 0.0, "B45 C0 within-group"),
    ExpectedClosure(90, 7, 11, 90.0, 0.0, "B90 C0 within-group"),
    ExpectedClosure(190, 1, 12, 0.0, 0.0, "outer B0 C0"),
)


@dataclass(frozen=True)
class Sample:
    line: int
    state_line: int
    expected: ExpectedSample
    center: Vec3
    center_correction: tuple[float, float]
    center_correction_norm: float
    v_diameter: float
    pass_center_delta: float
    radial_residuals: tuple[float, float, float, float]
    travels: tuple[float, float, float, float]
    following_errors: Vec3


@dataclass(frozen=True)
class Closure:
    line: int
    expected: ExpectedClosure
    delta: Vec3
    norm: float


@dataclass(frozen=True)
class SupplementalResult:
    samples: tuple[Sample, ...]
    closures: tuple[Closure, ...]


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(vector: Vec3, factor: float) -> Vec3:
    return (vector[0] * factor, vector[1] * factor, vector[2] * factor)


def norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def vec_text(vector: Vec3) -> str:
    return f"({vector[0]:+.6f}, {vector[1]:+.6f}, {vector[2]:+.6f})"


def angular_difference_deg(actual: float, expected: float) -> float:
    return abs((actual - expected + 180.0) % 360.0 - 180.0)


def parse_float(raw: dict[str, str], name: str, line: int) -> float:
    text = raw.get(name)
    if text is None or not text.strip():
        raise AnalysisError(f"line {line}: missing value for {name}")
    try:
        value = float(text)
    except ValueError as exc:
        raise AnalysisError(f"line {line}: invalid {name}={text!r}") from exc
    if not math.isfinite(value):
        raise AnalysisError(f"line {line}: non-finite {name}={text!r}")
    return value


def parse_int(raw: dict[str, str], name: str, line: int) -> int:
    value = parse_float(raw, name, line)
    rounded = round(value)
    if abs(value - rounded) > 0.000001:
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


def require_flag(line: int, raw: dict[str, str], name: str, expected: int) -> None:
    require_near(line, name, parse_float(raw, name, line), float(expected), 0.000001)


def require_range(
    line: int,
    name: str,
    value: float,
    lower: float,
    upper: float,
) -> None:
    if not lower <= value <= upper:
        raise DataQualityError(
            f"line {line}: {name}={value:.6f} outside "
            f"[{lower:.6f}, {upper:.6f}]"
        )


def validate_identity(raw: dict[str, str], line: int) -> None:
    expected = (
        ("schema_version", SCHEMA_VERSION),
        ("campaign_id", CAMPAIGN_ID),
        ("stage_mode", STAGE_MODE),
        ("attempt_id", ATTEMPT_ID),
    )
    for name, wanted in expected:
        actual = parse_int(raw, name, line)
        if actual != wanted:
            raise AnalysisError(
                f"line {line}: {name} must be {wanted}, got {actual}"
            )


def validate_rotary(
    raw: dict[str, str], line: int, expected_b: float, expected_c: float
) -> None:
    abs_b = parse_float(raw, "abs_b_deg", line)
    abs_c = parse_float(raw, "abs_c_deg", line)
    b_cmd = parse_float(raw, "joint_b_cmd_deg", line)
    b_fb = parse_float(raw, "joint_b_fb_deg", line)
    c_cmd = parse_float(raw, "joint_c_cmd_deg", line)
    c_fb = parse_float(raw, "joint_c_fb_deg", line)
    b_ssi = parse_float(raw, "b_ssi_zeroed_deg", line)
    c_ssi = parse_float(raw, "c_ssi_zeroed_deg", line)

    direct = (
        ("abs_b_deg", abs_b, expected_b),
        ("joint_b_cmd_deg", b_cmd, expected_b),
        ("joint_b_fb_deg", b_fb, b_cmd),
    )
    wrapped = (
        ("abs_c_deg", abs_c, expected_c),
        ("joint_c_cmd_deg", c_cmd, expected_c),
        ("joint_c_fb_deg", c_fb, c_cmd),
        ("b_ssi_zeroed_deg", b_ssi, b_cmd),
        ("c_ssi_zeroed_deg", c_ssi, -c_cmd),
    )
    for name, actual, wanted in direct:
        difference = abs(actual - wanted)
        if difference > POSE_TOL_DEG:
            raise DataQualityError(
                f"line {line}: {name} differs by {difference:.6f} deg "
                f"(limit {POSE_TOL_DEG:.6f})"
            )
    for name, actual, wanted in wrapped:
        difference = angular_difference_deg(actual, wanted)
        if difference > POSE_TOL_DEG:
            raise DataQualityError(
                f"line {line}: {name} differs by {difference:.6f} deg "
                f"(limit {POSE_TOL_DEG:.6f})"
            )


def validate_linear_axis_state(raw: dict[str, str], line: int) -> Vec3:
    for axis in "xyz":
        parse_float(raw, f"accepted_endpoint_abs_{axis}_mm", line)

    errors: list[float] = []
    for joint in range(3):
        command = parse_float(raw, f"joint_{joint}_motor_pos_cmd_mm", line)
        feedback = parse_float(raw, f"joint_{joint}_motor_pos_fb_mm", line)
        logged = parse_float(
            raw,
            f"joint_{joint}_motor_following_error_fb_minus_cmd_mm",
            line,
        )
        calculated = feedback - command
        if abs(logged - calculated) > FOLLOWING_ERROR_CONSISTENCY_TOL_MM:
            raise DataQualityError(
                f"line {line}: joint {joint} following error {logged:.9f} mm "
                f"does not equal feedback-command {calculated:.9f} mm"
            )
        errors.append(logged)
    return (errors[0], errors[1], errors[2])


def parse_sample(
    raw: dict[str, str],
    state_raw: dict[str, str],
    line: int,
    state_line: int,
    expected: ExpectedSample,
) -> Sample:
    validate_identity(raw, line)
    validate_identity(state_raw, state_line)
    seq = parse_int(raw, "sample_seq", line)
    if seq != expected.seq:
        raise DataQualityError(
            f"line {line}: sample_seq {seq}, expected {expected.seq} "
            f"({expected.role})"
        )
    state_seq = parse_int(state_raw, "sample_seq", state_line)
    if state_seq != seq:
        raise DataQualityError(
            f"state line {state_line}: sample_seq {state_seq} does not join "
            f"results sequence {seq}"
        )
    for name, wanted in (
        ("block_id", expected.block_id),
        ("anchor_seq", expected.anchor_seq),
        ("is_closure", expected.is_closure),
        ("contact_count", 4),
        ("u_method_code", 1),
    ):
        actual = parse_int(raw, name, line)
        if actual != wanted:
            raise DataQualityError(
                f"line {line}: {name}={actual}, expected {wanted} "
                f"for sequence {expected.seq}"
            )

    if parse_int(raw, "live_tool_number", line) != TOOL_NUMBER:
        raise DataQualityError(f"line {line}: supplemental requires live T3")
    tlo_names = (
        "expected_tool_length_mm",
        "motion_tooloffset_z_mm",
        "halui_tool_length_offset_z_mm",
        "kins_active_tool_offset_z_mm",
    )
    tlo_values = (
        parse_float(raw, "expected_tool_length_mm", line),
        parse_float(state_raw, "motion_tooloffset_z_mm", state_line),
        parse_float(state_raw, "halui_tool_length_offset_z_mm", state_line),
        parse_float(state_raw, "kins_active_tool_offset_z_mm", state_line),
    )
    for name, value in zip(tlo_names, tlo_values):
        require_near(line, name, value, TOOL_LENGTH_MM, TLO_TOL_MM)
    if max(tlo_values) - min(tlo_values) > TLO_TOL_MM:
        raise DataQualityError(
            f"line {line}: expected/live Z tool offsets span "
            f"{max(tlo_values) - min(tlo_values):.6f} mm"
        )

    calibration = parse_float(raw, "probe_calibration_offset_mm", line)
    diameter = parse_float(raw, "probe_diameter_mm", line)
    radius = parse_float(raw, "effective_contact_radius_mm", line)
    require_near(
        line,
        "probe_calibration_offset_mm",
        calibration,
        CALIBRATION_OFFSET_MM,
        CALIBRATION_TOL_MM,
    )
    require_near(
        line,
        "probe_diameter_mm",
        diameter,
        PROBE_DIAMETER_MM,
        DIAMETER_TOL_MM,
    )
    derived_radius = SPHERE_RADIUS_MM + diameter / 2.0 - calibration
    require_near(
        line,
        "effective_contact_radius_mm",
        radius,
        EFFECTIVE_CONTACT_RADIUS_MM,
        RADIUS_TOL_MM,
    )
    require_near(
        line,
        "effective_contact_radius_mm derived consistency",
        radius,
        derived_radius,
        RADIUS_TOL_MM,
    )

    for name, wanted in (
        ("persistent_correction_enabled", 1),
        ("tcpc_enabled", 1),
        ("twp_active", 0),
        ("twp_motion_enabled", 0),
        ("twp_valid", 0),
        ("b_ssi_invalid", 0),
        ("c_ssi_invalid", 0),
    ):
        require_flag(state_line, state_raw, name, wanted)

    result_b = parse_float(raw, "abs_b_deg", line)
    result_c = parse_float(raw, "abs_c_deg", line)
    if abs(result_b - expected.b_deg) > POSE_TOL_DEG:
        raise DataQualityError(
            f"line {line}: abs_b_deg differs from sequence {expected.seq} "
            f"by {abs(result_b - expected.b_deg):.6f} deg"
        )
    if angular_difference_deg(result_c, expected.c_deg) > POSE_TOL_DEG:
        raise DataQualityError(
            f"line {line}: abs_c_deg differs from sequence {expected.seq} "
            f"by {angular_difference_deg(result_c, expected.c_deg):.6f} deg"
        )
    validate_rotary(state_raw, state_line, expected.b_deg, expected.c_deg)
    state_b = parse_float(state_raw, "abs_b_deg", state_line)
    state_c = parse_float(state_raw, "abs_c_deg", state_line)
    if abs(result_b - state_b) > POSE_TOL_DEG:
        raise DataQualityError(
            f"sequence {seq}: results/state B disagree by "
            f"{abs(result_b - state_b):.6f} deg"
        )
    if angular_difference_deg(result_c, state_c) > POSE_TOL_DEG:
        raise DataQualityError(
            f"sequence {seq}: results/state C disagree by "
            f"{angular_difference_deg(result_c, state_c):.6f} deg"
        )
    center = tuple(
        parse_float(raw, f"center_abs_{axis}_mm", line) for axis in "xyz"
    )
    u_correction = parse_float(raw, "u_center_correction_mm", line)
    v_correction = parse_float(raw, "v_center_correction_mm", line)
    correction_norm = parse_float(raw, "center_correction_norm_mm", line)
    require_range(
        line,
        "center_correction_norm_mm",
        correction_norm,
        0.0,
        MAX_CENTER_CORRECTION_MM,
    )
    projected_norm = math.hypot(u_correction, v_correction)
    if abs(correction_norm - projected_norm) > CONSISTENCY_TOL_MM:
        raise DataQualityError(
            f"line {line}: center correction norm {correction_norm:.6f} mm "
            f"does not match U/V norm {projected_norm:.6f} mm"
        )

    v_diameter = parse_float(raw, "v_corrected_diameter_mm", line)
    require_range(
        line,
        "v_corrected_diameter_mm",
        v_diameter,
        MIN_V_DIAMETER_MM,
        MAX_V_DIAMETER_MM,
    )
    pass_delta = parse_float(raw, "pass_center_delta_mm", line)
    require_range(
        line,
        "pass_center_delta_mm",
        pass_delta,
        0.0,
        MAX_PASS_CENTER_DELTA_MM,
    )

    residual_names = (
        "w_contact_radial_residual_mm",
        "u_contact_radial_residual_mm",
        "v_minus_contact_radial_residual_mm",
        "v_plus_contact_radial_residual_mm",
    )
    residuals = tuple(parse_float(raw, name, line) for name in residual_names)
    for name, value in zip(residual_names, residuals):
        require_range(line, name, value, 0.0, MAX_RADIAL_RESIDUAL_MM)

    travel_names = (
        "w_travel_mm",
        "u_travel_mm",
        "v_minus_travel_mm",
        "v_plus_travel_mm",
    )
    travels = tuple(parse_float(raw, name, line) for name in travel_names)
    travel_maxima = (
        MAX_W_TRAVEL_MM,
        MAX_SIDE_TRAVEL_MM,
        MAX_SIDE_TRAVEL_MM,
        MAX_SIDE_TRAVEL_MM,
    )
    for name, value, upper in zip(travel_names, travels, travel_maxima):
        require_range(line, name, value, MIN_TRAVEL_MM, upper)

    following_errors = validate_linear_axis_state(state_raw, state_line)
    return Sample(
        line=line,
        state_line=state_line,
        expected=expected,
        center=center,  # type: ignore[arg-type]
        center_correction=(u_correction, v_correction),
        center_correction_norm=correction_norm,
        v_diameter=v_diameter,
        pass_center_delta=pass_delta,
        radial_residuals=residuals,  # type: ignore[arg-type]
        travels=travels,  # type: ignore[arg-type]
        following_errors=following_errors,
    )


def read_exact_csv(
    path: Path,
    columns: Sequence[str],
    label: str,
    expected_rows: int,
) -> list[tuple[int, dict[str, str]]]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != tuple(columns):
                raise AnalysisError(
                    f"{label} header must exactly match the reviewed "
                    f"{len(columns)}-column schema; got {reader.fieldnames}"
                )
            rows: list[tuple[int, dict[str, str]]] = []
            for raw in reader:
                if None in raw:
                    raise AnalysisError(
                        f"{label} line {reader.line_num}: too many fields"
                    )
                rows.append((reader.line_num, raw))
    except AnalysisError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AnalysisError(f"cannot read {label} {path}: {exc}") from exc

    if len(rows) != expected_rows:
        raise DataQualityError(
            f"{label} require exactly {expected_rows} rows, got {len(rows)}"
        )
    return rows


def row_join_key(raw: dict[str, str], line: int) -> tuple[int, int, int, int]:
    return (
        parse_int(raw, "campaign_id", line),
        parse_int(raw, "stage_mode", line),
        parse_int(raw, "attempt_id", line),
        parse_int(raw, "sample_seq", line),
    )


def read_results(results_path: Path, state_path: Path) -> tuple[Sample, ...]:
    result_rows = read_exact_csv(
        results_path, RESULT_COLUMNS, "results", len(EXPECTED_SAMPLES)
    )
    state_rows = read_exact_csv(
        state_path, STATE_COLUMNS, "state rows", len(EXPECTED_SAMPLES)
    )

    state_by_key: dict[tuple[int, int, int, int], tuple[int, dict[str, str]]] = {}
    for line, raw in state_rows:
        key = row_join_key(raw, line)
        if key in state_by_key:
            raise DataQualityError(f"state rows contain duplicate join key {key}")
        state_by_key[key] = (line, raw)

    samples: list[Sample] = []
    result_keys: set[tuple[int, int, int, int]] = set()
    for (line, raw), expected in zip(result_rows, EXPECTED_SAMPLES):
        key = row_join_key(raw, line)
        if key in result_keys:
            raise DataQualityError(f"results contain duplicate join key {key}")
        result_keys.add(key)
        state_match = state_by_key.get(key)
        if state_match is None:
            raise DataQualityError(f"results join key {key} has no matching state row")
        state_line, state_raw = state_match
        samples.append(parse_sample(raw, state_raw, line, state_line, expected))
    extra_state_keys = set(state_by_key) - result_keys
    if extra_state_keys:
        raise DataQualityError(
            f"state rows contain unmatched join keys {sorted(extra_state_keys)}"
        )
    return tuple(samples)


def parse_closure(
    raw: dict[str, str], line: int, expected: ExpectedClosure
) -> Closure:
    validate_identity(raw, line)
    identity = (
        ("closure_id", expected.closure_id),
        ("open_seq", expected.open_seq),
        ("close_seq", expected.close_seq),
    )
    for name, wanted in identity:
        actual = parse_int(raw, name, line)
        if actual != wanted:
            raise DataQualityError(
                f"closure line {line}: {name}={actual}, expected {wanted}"
            )
    angles = (
        ("open_b_deg", expected.b_deg, False),
        ("open_c_deg", expected.c_deg, True),
        ("close_b_deg", expected.b_deg, False),
        ("close_c_deg", expected.c_deg, True),
    )
    for name, wanted, wraps in angles:
        actual = parse_float(raw, name, line)
        difference = (
            angular_difference_deg(actual, wanted)
            if wraps
            else abs(actual - wanted)
        )
        if difference > POSE_TOL_DEG:
            raise DataQualityError(
                f"closure line {line}: {name} differs by {difference:.6f} deg"
            )

    delta = tuple(parse_float(raw, f"d{axis}_mm", line) for axis in "xyz")
    logged_norm = parse_float(raw, "norm_mm", line)
    calculated_norm = norm(delta)
    if abs(logged_norm - calculated_norm) > CONSISTENCY_TOL_MM:
        raise DataQualityError(
            f"closure line {line}: norm {logged_norm:.6f} mm does not match "
            f"vector norm {calculated_norm:.6f} mm"
        )
    require_near(
        line,
        "limit_mm",
        parse_float(raw, "limit_mm", line),
        CLOSURE_LIMIT_MM,
        0.000001,
    )
    require_flag(line, raw, "passed", 1)
    require_range(
        line, "norm_mm", logged_norm, 0.0, CLOSURE_LIMIT_MM
    )
    return Closure(
        line=line,
        expected=expected,
        delta=delta,  # type: ignore[arg-type]
        norm=logged_norm,
    )


def read_closures(path: Path) -> tuple[Closure, ...]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != CLOSURE_COLUMNS:
                raise AnalysisError(
                    f"closures header must exactly match the reviewed "
                    f"{len(CLOSURE_COLUMNS)}-column schema; got {reader.fieldnames}"
                )
            raw_rows = list(reader)
    except AnalysisError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AnalysisError(f"cannot read closures {path}: {exc}") from exc

    if len(raw_rows) != len(EXPECTED_CLOSURES):
        raise DataQualityError(
            f"closures require exactly {len(EXPECTED_CLOSURES)} rows, got "
            f"{len(raw_rows)}"
        )
    closures: list[Closure] = []
    for index, (raw, expected) in enumerate(zip(raw_rows, EXPECTED_CLOSURES), start=2):
        if None in raw:
            raise AnalysisError(f"closures line {index}: too many fields")
        closures.append(parse_closure(raw, index, expected))
    return tuple(closures)


def analyze(
    results_path: Path, state_path: Path, closures_path: Path
) -> SupplementalResult:
    samples = read_results(results_path, state_path)
    closures = read_closures(closures_path)
    by_seq = {sample.expected.seq: sample for sample in samples}
    for closure in closures:
        open_center = by_seq[closure.expected.open_seq].center
        close_center = by_seq[closure.expected.close_seq].center
        calculated = sub(close_center, open_center)
        difference = sub(closure.delta, calculated)
        if norm(difference) > CONSISTENCY_TOL_MM:
            raise DataQualityError(
                f"closure {closure.expected.closure_id}: logged vector "
                f"{vec_text(closure.delta)} does not match accepted-center "
                f"difference {vec_text(calculated)} mm"
            )
    return SupplementalResult(samples, closures)


def min_max(values: Sequence[float]) -> str:
    return f"{min(values):.6f}..{max(values):.6f}"


def group_reference(by_seq: dict[int, Sample], opening: int, closing: int) -> Vec3:
    return scale(add(by_seq[opening].center, by_seq[closing].center), 0.5)


def format_report(
    results_path: Path,
    state_path: Path,
    closures_path: Path,
    result: SupplementalResult,
) -> str:
    by_seq = {sample.expected.seq: sample for sample in result.samples}
    references = {
        45: group_reference(by_seq, 2, 6),
        90: group_reference(by_seq, 7, 11),
    }
    selected = {
        45: {0: references[45], 90: by_seq[3].center, 180: by_seq[4].center, 270: by_seq[5].center},
        90: {0: references[90], 90: by_seq[8].center, 180: by_seq[9].center, 270: by_seq[10].center},
    }

    all_travels = [value for sample in result.samples for value in sample.travels]
    all_residuals = [
        value for sample in result.samples for value in sample.radial_residuals
    ]
    v_diameters = [sample.v_diameter for sample in result.samples]
    pass_deltas = [sample.pass_center_delta for sample in result.samples]
    correction_norms = [sample.center_correction_norm for sample in result.samples]
    following_errors = [
        abs(value) for sample in result.samples for value in sample.following_errors
    ]

    lines = [
        "TCPC high-B T3 supplemental validation",
        "CSV data-quality status: PASS",
        f"results: {results_path}",
        f"state: {state_path}",
        f"closures: {closures_path}",
        f"identity: schema={SCHEMA_VERSION} campaign={CAMPAIGN_ID} "
        f"mode={STAGE_MODE} attempt={ATTEMPT_ID} T{TOOL_NUMBER}",
        f"sequence: {len(result.samples)}/12 exact accepted rows; "
        "B0 open, B45 C quadrants/close, B90 C quadrants/close, B0 close",
        "join: 12/12 unique geometry-state keys matched on "
        "campaign/mode/attempt/sample_seq",
        "method: four contacts, contact_count=4, u_method_code=1 "
        "(certified-radius single-side U)",
        "U diameter: not measured and intentionally absent from this schema; "
        "V opposing-contact diameter is validated",
        "accepted-row QA ranges:",
        f"  all W/U/V-/V+ travel: {min_max(all_travels)} mm",
        f"  radial residual: {min_max(all_residuals)} mm",
        f"  V corrected diameter: {min_max(v_diameters)} mm",
        f"  pass-center delta: {min_max(pass_deltas)} mm",
        f"  pass-2 center-correction norm: {min_max(correction_norms)} mm",
        f"  max |logged linear following error|: {max(following_errors):.9f} mm",
        "closure evidence [limit <=0.250000 mm]:",
    ]
    for closure in result.closures:
        lines.append(
            f"  {closure.expected.label} seq "
            f"{closure.expected.open_seq}->{closure.expected.close_seq}: "
            f"{vec_text(closure.delta)} mm; norm {closure.norm:.6f} [PASS]"
        )

    lines.append("C-dependent reconstructed centers and group-C0-relative vectors:")
    for b_deg in (45, 90):
        lines.append(f"  B{b_deg} C0 reference mean: {vec_text(references[b_deg])} mm")
        for c_deg in (0, 90, 180, 270):
            center = selected[b_deg][c_deg]
            relative = sub(center, references[b_deg])
            lines.append(
                f"    C{c_deg}: center {vec_text(center)} mm; "
                f"relative {vec_text(relative)} mm; norm {norm(relative):.6f}"
            )

    lines.append("B90 minus B45 same-C shifts:")
    for c_deg in (0, 90, 180, 270):
        raw_shift = sub(selected[90][c_deg], selected[45][c_deg])
        shape_shift = sub(
            sub(selected[90][c_deg], references[90]),
            sub(selected[45][c_deg], references[45]),
        )
        lines.append(
            f"  C{c_deg}: raw {vec_text(raw_shift)} mm; norm {norm(raw_shift):.6f}; "
            f"C0-referenced shape {vec_text(shape_shift)} mm; "
            f"norm {norm(shape_shift):.6f}"
        )
    return "\n".join(lines)


def synthetic_data() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    centers: dict[int, Vec3] = {
        1: (100.000, 200.000, -300.000),
        2: (100.050, 200.000, -300.000),
        3: (100.040, 200.100, -300.010),
        4: (99.950, 200.020, -300.030),
        5: (100.020, 199.950, -300.020),
        6: (100.052, 200.001, -299.999),
        7: (100.100, 200.000, -300.050),
        8: (100.070, 200.180, -300.040),
        9: (99.900, 200.030, -300.080),
        10: (100.060, 199.900, -300.070),
        11: (100.103, 200.002, -300.049),
        12: (100.005, 200.002, -299.999),
    }
    result_rows: list[dict[str, str]] = []
    state_rows: list[dict[str, str]] = []
    for expected in EXPECTED_SAMPLES:
        center = centers[expected.seq]
        raw = {
            name: "0.000000"
            for name in dict.fromkeys(RESULT_COLUMNS + STATE_COLUMNS)
        }
        values: dict[str, float | int] = {
            "schema_version": SCHEMA_VERSION,
            "campaign_id": CAMPAIGN_ID,
            "stage_mode": STAGE_MODE,
            "attempt_id": ATTEMPT_ID,
            "sample_seq": expected.seq,
            "block_id": expected.block_id,
            "anchor_seq": expected.anchor_seq,
            "is_closure": expected.is_closure,
            "contact_count": 4,
            "u_method_code": 1,
            "abs_b_deg": expected.b_deg,
            "abs_c_deg": expected.c_deg,
            "live_tool_number": TOOL_NUMBER,
            "expected_tool_length_mm": TOOL_LENGTH_MM,
            "probe_calibration_offset_mm": CALIBRATION_OFFSET_MM,
            "probe_diameter_mm": PROBE_DIAMETER_MM,
            "effective_contact_radius_mm": EFFECTIVE_CONTACT_RADIUS_MM,
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
            "u_center_correction_mm": 0.002,
            "v_center_correction_mm": -0.001,
            "center_correction_norm_mm": math.hypot(0.002, -0.001),
            "v_corrected_diameter_mm": 30.180,
            "pass_center_delta_mm": 0.005,
            "w_contact_radial_residual_mm": 0.001,
            "u_contact_radial_residual_mm": 0.002,
            "v_minus_contact_radial_residual_mm": 0.003,
            "v_plus_contact_radial_residual_mm": 0.004,
            "w_travel_mm": 4.0,
            "u_travel_mm": 4.0,
            "v_minus_travel_mm": 4.0,
            "v_plus_travel_mm": 4.0,
            "motion_tooloffset_z_mm": TOOL_LENGTH_MM,
            "halui_tool_length_offset_z_mm": TOOL_LENGTH_MM,
            "kins_active_tool_offset_z_mm": TOOL_LENGTH_MM,
            "joint_b_cmd_deg": expected.b_deg,
            "joint_b_fb_deg": expected.b_deg,
            "joint_c_cmd_deg": expected.c_deg,
            "joint_c_fb_deg": expected.c_deg,
            "b_ssi_zeroed_deg": expected.b_deg - 360.0,
            "c_ssi_zeroed_deg": -expected.c_deg - 360.0,
            "accepted_endpoint_abs_x_mm": center[0],
            "accepted_endpoint_abs_y_mm": center[1],
            "accepted_endpoint_abs_z_mm": center[2] + 20.0,
            "joint_0_motor_pos_cmd_mm": 10.0,
            "joint_0_motor_pos_fb_mm": 10.0,
            "joint_0_motor_following_error_fb_minus_cmd_mm": 0.0,
            "joint_1_motor_pos_cmd_mm": 20.0,
            "joint_1_motor_pos_fb_mm": 20.0,
            "joint_1_motor_following_error_fb_minus_cmd_mm": 0.0,
            "joint_2_motor_pos_cmd_mm": 30.0,
            "joint_2_motor_pos_fb_mm": 30.0,
            "joint_2_motor_following_error_fb_minus_cmd_mm": 0.0,
        }
        raw.update({name: f"{value:.9f}" for name, value in values.items()})
        result_rows.append({name: raw[name] for name in RESULT_COLUMNS})
        state_rows.append({name: raw[name] for name in STATE_COLUMNS})
    return result_rows, state_rows


def synthetic_closures(
    result_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    by_seq = {int(float(row["sample_seq"])): row for row in result_rows}
    rows: list[dict[str, str]] = []
    for expected in EXPECTED_CLOSURES:
        opening = tuple(
            float(by_seq[expected.open_seq][f"center_abs_{axis}_mm"])
            for axis in "xyz"
        )
        closing = tuple(
            float(by_seq[expected.close_seq][f"center_abs_{axis}_mm"])
            for axis in "xyz"
        )
        delta = sub(closing, opening)  # type: ignore[arg-type]
        values: dict[str, float | int] = {
            "schema_version": SCHEMA_VERSION,
            "campaign_id": CAMPAIGN_ID,
            "stage_mode": STAGE_MODE,
            "attempt_id": ATTEMPT_ID,
            "closure_id": expected.closure_id,
            "open_seq": expected.open_seq,
            "close_seq": expected.close_seq,
            "open_b_deg": expected.b_deg,
            "open_c_deg": expected.c_deg,
            "close_b_deg": expected.b_deg,
            "close_c_deg": expected.c_deg,
            "dx_mm": delta[0],
            "dy_mm": delta[1],
            "dz_mm": delta[2],
            "norm_mm": norm(delta),
            "limit_mm": CLOSURE_LIMIT_MM,
            "passed": 1,
        }
        rows.append({name: f"{values[name]:.9f}" for name in CLOSURE_COLUMNS})
    return rows


def write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def expect_failure(function, expected_exception: type[Exception], label: str) -> None:
    try:
        function()
    except expected_exception:
        return
    raise AssertionError(f"self-test {label}: expected {expected_exception.__name__}")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="tcpc-high-b-analyzer-") as directory:
        root = Path(directory)
        results_path = root / "results.csv"
        state_path = root / "state.csv"
        closures_path = root / "closures.csv"
        rows, state_rows = synthetic_data()
        closure_rows = synthetic_closures(rows)
        write_csv(results_path, RESULT_COLUMNS, rows)
        write_csv(state_path, STATE_COLUMNS, state_rows)
        write_csv(closures_path, CLOSURE_COLUMNS, closure_rows)
        analyze(results_path, state_path, closures_path)

        write_csv(results_path, RESULT_COLUMNS, rows[:-1])
        expect_failure(
            lambda: analyze(results_path, state_path, closures_path),
            DataQualityError,
            "partial sequence rejection",
        )

        bad_contact = [dict(row) for row in rows]
        bad_contact[4]["contact_count"] = "5"
        write_csv(results_path, RESULT_COLUMNS, bad_contact)
        expect_failure(
            lambda: analyze(results_path, state_path, closures_path),
            DataQualityError,
            "contact method rejection",
        )

        bad_v_diameter = [dict(row) for row in rows]
        bad_v_diameter[7]["v_corrected_diameter_mm"] = "30.600"
        write_csv(results_path, RESULT_COLUMNS, bad_v_diameter)
        expect_failure(
            lambda: analyze(results_path, state_path, closures_path),
            DataQualityError,
            "V diameter rejection",
        )

        write_csv(results_path, RESULT_COLUMNS, rows)
        duplicate_state = [dict(row) for row in state_rows]
        duplicate_state[5]["sample_seq"] = duplicate_state[4]["sample_seq"]
        write_csv(state_path, STATE_COLUMNS, duplicate_state)
        expect_failure(
            lambda: analyze(results_path, state_path, closures_path),
            DataQualityError,
            "duplicate state join-key rejection",
        )

        write_csv(state_path, STATE_COLUMNS, state_rows)
        bad_closure = [dict(row) for row in closure_rows]
        bad_closure[0]["norm_mm"] = "0.300000"
        bad_closure[0]["passed"] = "0"
        write_csv(closures_path, CLOSURE_COLUMNS, bad_closure)
        expect_failure(
            lambda: analyze(results_path, state_path, closures_path),
            DataQualityError,
            "closure rejection",
        )

        extra_columns = RESULT_COLUMNS + ("u_corrected_diameter_mm",)
        write_csv(results_path, extra_columns, rows)
        write_csv(closures_path, CLOSURE_COLUMNS, closure_rows)
        expect_failure(
            lambda: analyze(results_path, state_path, closures_path),
            AnalysisError,
            "unexpected U diameter schema rejection",
        )
    print(
        "self-test: PASS (valid four-contact dataset, exact sequence, partial, "
        "method, state join, V-diameter, closure, and schema/U-diameter cases)"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Exit status: 0 for a complete accepted supplemental, 1 for a "
            "measurement/data-quality failure, and 2 for schema/input errors."
        ),
    )
    parser.add_argument(
        "results",
        nargs="?",
        type=Path,
        default=DEFAULT_RESULTS,
        help=f"pose results CSV (default: {DEFAULT_RESULTS.name})",
    )
    parser.add_argument(
        "state",
        nargs="?",
        type=Path,
        default=DEFAULT_STATE,
        help=f"matching pose-state CSV (default: {DEFAULT_STATE.name})",
    )
    parser.add_argument(
        "closures",
        nargs="?",
        type=Path,
        default=DEFAULT_CLOSURES,
        help=f"closure CSV (default: {DEFAULT_CLOSURES.name})",
    )
    parser.add_argument("--self-test", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        return EXIT_ACCEPTED
    try:
        result = analyze(args.results, args.state, args.closures)
        print(format_report(args.results, args.state, args.closures, result))
    except DataQualityError as exc:
        print(f"data-quality failure: {exc}", file=sys.stderr)
        return EXIT_DATA_QUALITY
    except AnalysisError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    return EXIT_ACCEPTED


if __name__ == "__main__":
    sys.exit(main())
