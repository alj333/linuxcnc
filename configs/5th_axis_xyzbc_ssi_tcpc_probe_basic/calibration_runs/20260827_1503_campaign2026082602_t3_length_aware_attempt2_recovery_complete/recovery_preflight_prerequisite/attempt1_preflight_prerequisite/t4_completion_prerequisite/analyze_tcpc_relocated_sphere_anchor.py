#!/usr/bin/env python3
"""Validate the one-row T4 anchor for the relocated calibration sphere."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sys
from pathlib import Path
from typing import Sequence


HERE = Path(__file__).resolve().parent
ANCHOR_PROGRAM = HERE.parents[1] / "nc_files/calibration/tcpc_relocated_sphere_t4_anchor.ngc"
EXPECTED_ANCHOR_PROGRAM_SHA256 = "4d1db5b89ae9a3b833381a64c8667aa475e0adc17b00fb2c49e318f9ace0fcaf"
DEFAULT_RESULTS = HERE / "tcpc-relocated-sphere-t4-anchor-results.csv"
DEFAULT_STATE = HERE / "tcpc-relocated-sphere-t4-anchor-state.csv"

CAMPAIGN = 2026082403
MODE = 22
TOOL = 4
TOOL_LENGTH = 229.407000
CAL_OFFSET = 0.154742
BALL_DIAMETER = 6.0
EFFECTIVE_RADIUS = 15.0 + BALL_DIAMETER / 2.0 - CAL_OFFSET
POSE_ANGLE_TOLERANCE_DEG = 0.01

RESULT_FIELDS = (
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

STATE_FIELDS = (
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


class ValidationError(ValueError):
    pass


def validate_program_hash() -> None:
    digest = hashlib.sha256(ANCHOR_PROGRAM.read_bytes()).hexdigest()
    if digest != EXPECTED_ANCHOR_PROGRAM_SHA256:
        raise ValidationError(
            f"anchor program SHA-256 {digest} does not match frozen {EXPECTED_ANCHOR_PROGRAM_SHA256}"
        )


def number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"invalid {field!r}") from exc
    if not math.isfinite(value):
        raise ValidationError(f"non-finite {field!r}")
    return value


def near(row: dict[str, str], field: str, expected: float, tolerance: float) -> None:
    value = number(row, field)
    if abs(value - expected) > tolerance:
        raise ValidationError(f"{field}={value:.9f}, expected {expected:.9f} +/- {tolerance:.9f}")


def angular_error(value: float, target: float) -> float:
    return abs((value - target + 180.0) % 360.0 - 180.0)


def near_angle(
    row: dict[str, str], field: str, expected: float, tolerance: float
) -> None:
    value = number(row, field)
    error = angular_error(value, expected)
    if error > tolerance:
        raise ValidationError(
            f"{field}={value:.9f}, expected wrapped angle {expected:.9f} "
            f"+/- {tolerance:.9f}"
        )


def bounded(row: dict[str, str], field: str, minimum: float, maximum: float) -> float:
    value = number(row, field)
    if not minimum <= value <= maximum:
        raise ValidationError(f"{field}={value:.9f}, expected range {minimum:.9f}..{maximum:.9f}")
    return value


def read_rows(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(fields):
            raise ValidationError(f"{path}: exact schema mismatch")
        rows = list(reader)
    for line_number, row in enumerate(rows, 2):
        if None in row or any(row.get(field) is None for field in fields):
            raise ValidationError(f"{path}:{line_number}: surplus or missing CSV fields")
    return rows


def validate(results: list[dict[str, str]], states: list[dict[str, str]]) -> tuple[int, tuple[float, float, float]]:
    attempts: set[int] = set()
    for row in results + states:
        if int(number(row, "campaign_id")) != CAMPAIGN or int(number(row, "stage_mode")) != MODE:
            continue
        attempt_value = number(row, "attempt_id")
        if attempt_value < 1.0 or abs(attempt_value - round(attempt_value)) > 1e-9:
            raise ValidationError("anchor attempt ID must be a positive exact integer")
        attempts.add(int(round(attempt_value)))
    if not attempts:
        raise ValidationError("no relocated-sphere anchor row has been recorded")
    attempt = max(attempts)
    selected_results = [
        row
        for row in results
        if int(number(row, "campaign_id")) == CAMPAIGN
        and int(number(row, "stage_mode")) == MODE
        and int(number(row, "attempt_id")) == attempt
    ]
    selected_states = [
        row
        for row in states
        if int(number(row, "campaign_id")) == CAMPAIGN
        and int(number(row, "stage_mode")) == MODE
        and int(number(row, "attempt_id")) == attempt
    ]
    if len(selected_results) != 1 or len(selected_states) != 1:
        raise ValidationError(
            f"latest attempt {attempt} requires exactly one result/state row, got "
            f"{len(selected_results)}/{len(selected_states)}"
        )
    result = selected_results[0]
    state = selected_states[0]
    for row in (result, state):
        near(row, "schema_version", 1.0, 1e-9)
        near(row, "campaign_id", CAMPAIGN, 1e-6)
        near(row, "stage_mode", MODE, 1e-9)
        near(row, "attempt_id", attempt, 1e-9)
        near(row, "sample_seq", 1.0, 1e-9)
        near_angle(row, "abs_b_deg", 0.0, POSE_ANGLE_TOLERANCE_DEG)
        near_angle(row, "abs_c_deg", 0.0, POSE_ANGLE_TOLERANCE_DEG)
    if any(result[field] != state[field] for field in ("campaign_id", "stage_mode", "attempt_id", "sample_seq")):
        raise ValidationError("result/state sequence identity mismatch")

    near(result, "block_id", 0.0, 1e-9)
    near(result, "anchor_seq", 1.0, 1e-9)
    near(result, "is_closure", 0.0, 1e-9)
    near(result, "contact_count", 4.0, 1e-9)
    near(result, "u_method_code", 1.0, 1e-9)
    near(result, "live_tool_number", TOOL, 1e-9)
    near(result, "expected_tool_length_mm", TOOL_LENGTH, 0.002)
    near(result, "probe_calibration_offset_mm", CAL_OFFSET, 0.0005)
    near(result, "probe_diameter_mm", BALL_DIAMETER, 0.01)
    near(result, "effective_contact_radius_mm", EFFECTIVE_RADIUS, 0.001)
    derived_radius = 15.0 + number(result, "probe_diameter_mm") / 2.0 - number(
        result, "probe_calibration_offset_mm"
    )
    if abs(number(result, "effective_contact_radius_mm") - derived_radius) > 1e-6:
        raise ValidationError("effective contact radius is inconsistent with ball diameter and probe offset")

    u_correction = bounded(result, "u_center_correction_mm", -0.050, 0.050)
    v_correction = bounded(result, "v_center_correction_mm", -0.050, 0.050)
    correction_norm = bounded(result, "center_correction_norm_mm", 0.0, 0.050)
    if abs(correction_norm - math.hypot(u_correction, v_correction)) > 0.0001:
        raise ValidationError("anchor correction components do not reproduce the logged norm")
    bounded(result, "v_corrected_diameter_mm", 29.9, 30.5)
    bounded(result, "pass_center_delta_mm", 0.0, 0.100)
    for field in (
        "w_contact_radial_residual_mm",
        "u_contact_radial_residual_mm",
        "v_minus_contact_radial_residual_mm",
        "v_plus_contact_radial_residual_mm",
    ):
        bounded(result, field, 0.0, 0.250)
    bounded(result, "w_travel_mm", 1.0, 7.01)
    for field in ("u_travel_mm", "v_minus_travel_mm", "v_plus_travel_mm"):
        bounded(result, field, 1.0, 6.01)

    for field, expected in (
        ("persistent_correction_enabled", 1.0),
        ("tcpc_enabled", 1.0),
        ("twp_active", 0.0),
        ("twp_motion_enabled", 0.0),
        ("twp_valid", 0.0),
        ("b_ssi_invalid", 0.0),
        ("c_ssi_invalid", 0.0),
    ):
        near(state, field, expected, 1e-9)
    for field in (
        "motion_tooloffset_z_mm",
        "halui_tool_length_offset_z_mm",
        "kins_active_tool_offset_z_mm",
    ):
        near(state, field, TOOL_LENGTH, 0.002)
    for field in ("joint_b_cmd_deg", "joint_b_fb_deg", "joint_c_cmd_deg", "joint_c_fb_deg"):
        near_angle(state, field, 0.0, POSE_ANGLE_TOLERANCE_DEG)
    for field in ("b_ssi_zeroed_deg", "c_ssi_zeroed_deg"):
        near_angle(state, field, 0.0, POSE_ANGLE_TOLERANCE_DEG)
    for joint in range(3):
        command = number(state, f"joint_{joint}_motor_pos_cmd_mm")
        feedback = number(state, f"joint_{joint}_motor_pos_fb_mm")
        logged = number(state, f"joint_{joint}_motor_following_error_fb_minus_cmd_mm")
        if abs((feedback - command) - logged) > 2e-6 or abs(logged) > 0.002:
            raise ValidationError(f"joint {joint} logged linear state is inconsistent")

    center = tuple(number(result, field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm"))
    endpoint = tuple(
        number(state, field)
        for field in ("accepted_endpoint_abs_x_mm", "accepted_endpoint_abs_y_mm", "accepted_endpoint_abs_z_mm")
    )
    expected_endpoint = (
        center[0] - u_correction,
        center[1] - v_correction,
        center[2] + EFFECTIVE_RADIUS + 5.0,
    )
    if math.dist(endpoint, expected_endpoint) > 0.020:
        raise ValidationError("accepted endpoint is not the expected B0/C0 top-clear point")
    return attempt, center


def self_test() -> None:
    validate_program_hash()
    result = {field: "0" for field in RESULT_FIELDS}
    state = {field: "0" for field in STATE_FIELDS}
    for row in (result, state):
        row.update(
            schema_version="1",
            campaign_id=str(CAMPAIGN),
            stage_mode=str(MODE),
            attempt_id="1",
            sample_seq="1",
            abs_b_deg="0",
            abs_c_deg="0",
        )
    result.update(
        block_id="0",
        anchor_seq="1",
        is_closure="0",
        contact_count="4",
        u_method_code="1",
        live_tool_number=str(TOOL),
        expected_tool_length_mm=str(TOOL_LENGTH),
        probe_calibration_offset_mm=str(CAL_OFFSET),
        probe_diameter_mm=str(BALL_DIAMETER),
        effective_contact_radius_mm=str(EFFECTIVE_RADIUS),
        center_abs_x_mm="1000",
        center_abs_y_mm="500",
        center_abs_z_mm="-300",
        u_center_correction_mm="0.003",
        v_center_correction_mm="0.004",
        center_correction_norm_mm="0.005",
        v_corrected_diameter_mm="30.1",
        pass_center_delta_mm="0.005",
        w_travel_mm="5",
        u_travel_mm="4",
        v_minus_travel_mm="4",
        v_plus_travel_mm="4",
    )
    state.update(
        persistent_correction_enabled="1",
        tcpc_enabled="1",
        motion_tooloffset_z_mm=str(TOOL_LENGTH),
        halui_tool_length_offset_z_mm=str(TOOL_LENGTH),
        kins_active_tool_offset_z_mm=str(TOOL_LENGTH),
        accepted_endpoint_abs_x_mm="999.997",
        accepted_endpoint_abs_y_mm="499.996",
        accepted_endpoint_abs_z_mm=str(-300.0 + EFFECTIVE_RADIUS + 5.0),
        b_ssi_zeroed_deg="-360.00001",
        c_ssi_zeroed_deg="-0.00032",
    )
    attempt, center = validate([result], [state])
    assert attempt == 1 and center == (1000.0, 500.0, -300.0)
    bad_result_values = (
        ("center_correction_norm_mm", "0.051"),
        ("u_center_correction_mm", "999"),
        ("pass_center_delta_mm", "-0.001"),
        ("w_contact_radial_residual_mm", "-0.001"),
        ("u_travel_mm", "999"),
        ("live_tool_number", "4.09"),
        ("effective_contact_radius_mm", str(EFFECTIVE_RADIUS + 0.0005)),
        ("abs_c_deg", "0.011"),
    )
    for field, value in bad_result_values:
        bad = dict(result)
        bad[field] = value
        try:
            validate([bad], [state])
        except ValidationError:
            pass
        else:
            raise AssertionError(f"bad result field {field} was accepted")
    for field, value in (("b_ssi_zeroed_deg", "0.1"), ("accepted_endpoint_abs_x_mm", "not-a-number")):
        bad_state = dict(state)
        bad_state[field] = value
        try:
            validate([result], [bad_state])
        except ValidationError:
            pass
        else:
            raise AssertionError(f"bad state field {field} was accepted")
    for invalid_attempt in ("0", "-1", "1.5"):
        bad_result = dict(result)
        bad_state = dict(state)
        bad_result["attempt_id"] = invalid_attempt
        bad_state["attempt_id"] = invalid_attempt
        try:
            validate([bad_result], [bad_state])
        except ValidationError:
            pass
        else:
            raise AssertionError(f"bad attempt ID {invalid_attempt} was accepted")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="?", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("state", nargs="?", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("self-test: PASS")
        return 0
    try:
        validate_program_hash()
        result_rows = read_rows(args.results, RESULT_FIELDS)
        state_rows = read_rows(args.state, STATE_FIELDS)
        attempt, center = validate(result_rows, state_rows)
    except (OSError, ValidationError) as exc:
        print(f"anchor validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print("relocated-sphere T4 anchor validation: PASS")
    print(f"attempt: {attempt}")
    print(f"center_abs_mm: X={center[0]:.6f} Y={center[1]:.6f} Z={center[2]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
