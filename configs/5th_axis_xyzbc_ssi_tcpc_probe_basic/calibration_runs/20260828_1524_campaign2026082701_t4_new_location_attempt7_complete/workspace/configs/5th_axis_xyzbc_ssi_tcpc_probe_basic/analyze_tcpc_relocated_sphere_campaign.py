#!/usr/bin/env python3
"""Validate the relocated-sphere T4 training and untouched T3 verification runs."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_reachability as reach


HERE = Path(__file__).resolve().parent
CAMPAIGN = 2026082404
DEFAULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_CAMPAIGN_REPORT.md"

CLOSURE_FIELDS = (
    "schema_version",
    "campaign_id",
    "stage_mode",
    "attempt_id",
    "block_id",
    "open_sample_seq",
    "close_sample_seq",
    "abs_b_deg",
    "abs_c_deg",
    "closure_dx_mm",
    "closure_dy_mm",
    "closure_dz_mm",
    "closure_norm_mm",
    "limit_mm",
    "pass",
)


@dataclass(frozen=True)
class ExpectedRow:
    seq: int
    block: int
    anchor_seq: int
    is_closure: int
    pose: reach.Pose


@dataclass(frozen=True)
class RunSpec:
    name: str
    tool: int
    mode: int
    length: float
    calibration_offset: float
    effective_radius: float
    results_path: Path
    state_path: Path
    closures_path: Path
    expected_rows: tuple[ExpectedRow, ...]
    closure_ranges: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class ValidatedRun:
    spec: RunSpec
    attempt: int
    centers: np.ndarray
    closure_norms: np.ndarray


def expected_rows(
    poses: Sequence[reach.Pose], ranges: Sequence[tuple[int, int, int]]
) -> tuple[ExpectedRow, ...]:
    by_seq: dict[int, ExpectedRow] = {}
    for block, first, last in ranges:
        for seq in range(first, last + 1):
            by_seq[seq] = ExpectedRow(
                seq,
                block,
                seq - first + 1,
                int(last > first and seq == last),
                poses[seq - 1],
            )
    if sorted(by_seq) != list(range(1, len(poses) + 1)):
        raise ValueError("expected row ranges do not cover the pose grid exactly")
    return tuple(by_seq[seq] for seq in sorted(by_seq))


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
T3_RANGES = (
    (100, 1, 5),
    (45, 6, 10),
    (-45, 11, 15),
    (500, 16, 16),
    (90, 17, 21),
    (-90, 22, 26),
    (200, 27, 31),
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
T3_CLOSURES = (
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

T4_SPEC = RunSpec(
    "T4 primary training",
    4,
    23,
    reach.T4_TOOL_LENGTH,
    anchor.CAL_OFFSET,
    anchor.EFFECTIVE_RADIUS,
    HERE / "tcpc-relocated-sphere-t4-primary-results.csv",
    HERE / "tcpc-relocated-sphere-t4-primary-state.csv",
    HERE / "tcpc-relocated-sphere-t4-primary-closures.csv",
    expected_rows(reach.grid(), T4_RANGES),
    T4_CLOSURES,
)
T3_SPEC = RunSpec(
    "T3 untouched verification",
    3,
    24,
    reach.T3_TOOL_LENGTH,
    0.117658,
    reach.T3_EFFECTIVE_RADIUS,
    HERE / "tcpc-relocated-sphere-t3-verification-results.csv",
    HERE / "tcpc-relocated-sphere-t3-verification-state.csv",
    HERE / "tcpc-relocated-sphere-t3-verification-closures.csv",
    expected_rows(reach.verification_grid(), T3_RANGES),
    T3_CLOSURES,
)


def angular_error(value: float, target: float) -> float:
    return abs((value - target + 180.0) % 360.0 - 180.0)


def read_closures(path: Path) -> list[dict[str, str]]:
    return anchor.read_rows(path, CLOSURE_FIELDS)


def exact_integer(row: dict[str, str], field: str, *, positive: bool = False) -> int:
    value = anchor.number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9 or (positive and rounded < 1):
        qualifier = "positive exact integer" if positive else "exact integer"
        raise anchor.ValidationError(f"{field}={value:.9f}, expected {qualifier}")
    return int(rounded)


def selected_attempt(
    spec: RunSpec,
    results: Sequence[dict[str, str]],
    states: Sequence[dict[str, str]],
    closures: Sequence[dict[str, str]],
) -> tuple[int, list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    all_rows = list(results) + list(states) + list(closures)
    attempts: set[int] = set()
    for row in all_rows:
        campaign = exact_integer(row, "campaign_id")
        mode = exact_integer(row, "stage_mode")
        attempt = exact_integer(row, "attempt_id", positive=True)
        if campaign == CAMPAIGN and mode == spec.mode:
            attempts.add(attempt)
    if not attempts:
        raise anchor.ValidationError(f"{spec.name}: no campaign rows")
    attempt = max(attempts)

    def choose(rows: Sequence[dict[str, str]]) -> list[dict[str, str]]:
        return [
            row
            for row in rows
            if exact_integer(row, "campaign_id") == CAMPAIGN
            and exact_integer(row, "stage_mode") == spec.mode
            and exact_integer(row, "attempt_id", positive=True) == attempt
        ]

    return attempt, choose(results), choose(states), choose(closures)


def expected_endpoint(result: dict[str, str], expected: ExpectedRow, radius: float) -> np.ndarray:
    center = np.array(
        [anchor.number(result, field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")]
    )
    u_correction = anchor.number(result, "u_center_correction_mm")
    v_correction = anchor.number(result, "v_center_correction_mm")
    w, u, v = reach.frame(expected.pose.b_deg, expected.pose.c_deg)
    return center - u_correction * u - v_correction * v - w * (radius + 5.0)


def validate_contact_geometry(spec: RunSpec, row: dict[str, str]) -> None:
    diameter = anchor.number(row, "probe_diameter_mm")
    calibration_offset = anchor.number(row, "probe_calibration_offset_mm")
    effective_radius = anchor.number(row, "effective_contact_radius_mm")
    derived_radius = 15.0 + diameter / 2.0 - calibration_offset
    if abs(effective_radius - derived_radius) > 1e-6:
        raise anchor.ValidationError(
            f"{spec.name}: effective contact radius is inconsistent with ball diameter and probe offset"
        )


def validate_result(spec: RunSpec, row: dict[str, str], expected: ExpectedRow, attempt: int) -> np.ndarray:
    for field, value, tolerance in (
        ("schema_version", 1.0, 1e-9),
        ("campaign_id", CAMPAIGN, 1e-6),
        ("stage_mode", spec.mode, 1e-9),
        ("attempt_id", attempt, 1e-9),
        ("sample_seq", expected.seq, 1e-9),
        ("block_id", expected.block, 1e-9),
        ("anchor_seq", expected.anchor_seq, 1e-9),
        ("is_closure", expected.is_closure, 1e-9),
        ("contact_count", 4.0, 1e-9),
        ("abs_b_deg", expected.pose.b_deg, 0.01),
        ("abs_c_deg", expected.pose.c_deg, 0.01),
        ("live_tool_number", spec.tool, 1e-9),
        ("expected_tool_length_mm", spec.length, 0.002),
        ("probe_calibration_offset_mm", spec.calibration_offset, 0.0005),
        ("probe_diameter_mm", 6.0, 0.01),
        ("effective_contact_radius_mm", spec.effective_radius, 0.001),
    ):
        anchor.near(row, field, value, tolerance)
    validate_contact_geometry(spec, row)
    expected_method = 2.0 if expected.pose.b_deg < -0.001 else 1.0
    anchor.near(row, "u_method_code", expected_method, 1e-9)

    u_correction = anchor.bounded(row, "u_center_correction_mm", -0.250, 0.250)
    v_correction = anchor.bounded(row, "v_center_correction_mm", -0.250, 0.250)
    norm = anchor.bounded(row, "center_correction_norm_mm", 0.0, 0.250)
    if abs(norm - math.hypot(u_correction, v_correction)) > 0.001:
        raise anchor.ValidationError(f"{spec.name} seq {expected.seq}: correction norm mismatch")
    anchor.bounded(row, "v_corrected_diameter_mm", 29.9, 30.5)
    anchor.bounded(row, "pass_center_delta_mm", 0.0, 0.100)
    for field in (
        "w_contact_radial_residual_mm",
        "u_contact_radial_residual_mm",
        "v_minus_contact_radial_residual_mm",
        "v_plus_contact_radial_residual_mm",
    ):
        anchor.bounded(row, field, 0.0, 0.250)
    anchor.bounded(row, "w_travel_mm", 1.0, 7.01)
    for field in ("u_travel_mm", "v_minus_travel_mm", "v_plus_travel_mm"):
        anchor.bounded(row, field, 1.0, 6.01)
    return np.array(
        [anchor.number(row, field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")]
    )


def validate_state(
    spec: RunSpec,
    row: dict[str, str],
    result: dict[str, str],
    expected: ExpectedRow,
    attempt: int,
) -> None:
    for field, value in (
        ("schema_version", 1.0),
        ("campaign_id", CAMPAIGN),
        ("stage_mode", spec.mode),
        ("attempt_id", attempt),
        ("sample_seq", expected.seq),
        ("persistent_correction_enabled", 1.0),
        ("tcpc_enabled", 1.0),
        ("twp_active", 0.0),
        ("twp_motion_enabled", 0.0),
        ("twp_valid", 0.0),
        ("b_ssi_invalid", 0.0),
        ("c_ssi_invalid", 0.0),
    ):
        anchor.near(row, field, value, 1e-6)
    for field in ("motion_tooloffset_z_mm", "halui_tool_length_offset_z_mm", "kins_active_tool_offset_z_mm"):
        anchor.near(row, field, spec.length, 0.002)
    for field, target in (
        ("abs_b_deg", expected.pose.b_deg),
        ("joint_b_cmd_deg", expected.pose.b_deg),
        ("joint_b_fb_deg", expected.pose.b_deg),
        ("b_ssi_zeroed_deg", expected.pose.b_deg),
        ("abs_c_deg", expected.pose.c_deg),
        ("joint_c_cmd_deg", expected.pose.c_deg),
        ("joint_c_fb_deg", expected.pose.c_deg),
        ("c_ssi_zeroed_deg", -expected.pose.c_deg),
    ):
        if angular_error(anchor.number(row, field), target) > 0.01:
            raise anchor.ValidationError(f"{spec.name} seq {expected.seq}: {field} pose mismatch")
    for joint in range(3):
        command = anchor.number(row, f"joint_{joint}_motor_pos_cmd_mm")
        feedback = anchor.number(row, f"joint_{joint}_motor_pos_fb_mm")
        logged = anchor.number(row, f"joint_{joint}_motor_following_error_fb_minus_cmd_mm")
        if abs((feedback - command) - logged) > 2e-6 or abs(logged) > 0.002:
            raise anchor.ValidationError(f"{spec.name} seq {expected.seq}: J{joint} state mismatch")
    endpoint = np.array(
        [
            anchor.number(row, field)
            for field in ("accepted_endpoint_abs_x_mm", "accepted_endpoint_abs_y_mm", "accepted_endpoint_abs_z_mm")
        ]
    )
    if np.linalg.norm(endpoint - expected_endpoint(result, expected, spec.effective_radius)) > 0.030:
        raise anchor.ValidationError(f"{spec.name} seq {expected.seq}: accepted endpoint mismatch")


def validate_closures(
    spec: RunSpec,
    rows: Sequence[dict[str, str]],
    results_by_seq: dict[int, dict[str, str]],
    attempt: int,
) -> np.ndarray:
    if len(rows) != len(spec.closure_ranges):
        raise anchor.ValidationError(
            f"{spec.name}: expected {len(spec.closure_ranges)} closures, got {len(rows)}"
        )
    norms: list[float] = []
    for row, (block, first, last) in zip(rows, spec.closure_ranges):
        for field, value, positive in (
            ("schema_version", 1, True),
            ("campaign_id", CAMPAIGN, True),
            ("stage_mode", spec.mode, True),
            ("attempt_id", attempt, True),
            ("block_id", block, False),
            ("open_sample_seq", first, True),
            ("close_sample_seq", last, True),
            ("pass", 1, False),
        ):
            actual = exact_integer(row, field, positive=positive)
            if actual != value:
                raise anchor.ValidationError(
                    f"{spec.name}: closure {field}={actual}, expected {value}"
                )
        anchor.near(row, "limit_mm", 0.050, 1e-9)
        open_center = np.array(
            [anchor.number(results_by_seq[first], field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")]
        )
        close_center = np.array(
            [anchor.number(results_by_seq[last], field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")]
        )
        delta = close_center - open_center
        logged_delta = np.array(
            [anchor.number(row, field) for field in ("closure_dx_mm", "closure_dy_mm", "closure_dz_mm")]
        )
        if np.linalg.norm(delta - logged_delta) > 3e-6:
            raise anchor.ValidationError(f"{spec.name}: closure block {block} vector mismatch")
        norm = anchor.bounded(row, "closure_norm_mm", 0.0, 0.050)
        if abs(norm - np.linalg.norm(delta)) > 3e-6:
            raise anchor.ValidationError(f"{spec.name}: closure block {block} norm mismatch")
        close_expected = spec.expected_rows[last - 1]
        anchor.near(row, "abs_b_deg", close_expected.pose.b_deg, 0.01)
        anchor.near(row, "abs_c_deg", close_expected.pose.c_deg, 0.01)
        norms.append(norm)
    return np.array(norms)


def validate_run(spec: RunSpec) -> ValidatedRun:
    results = anchor.read_rows(spec.results_path, anchor.RESULT_FIELDS)
    states = anchor.read_rows(spec.state_path, anchor.STATE_FIELDS)
    closures = read_closures(spec.closures_path)
    attempt, selected_results, selected_states, selected_closures = selected_attempt(
        spec, results, states, closures
    )
    count = len(spec.expected_rows)
    if len(selected_results) != count or len(selected_states) != count:
        raise anchor.ValidationError(
            f"{spec.name} attempt {attempt}: expected {count} result/state rows, got "
            f"{len(selected_results)}/{len(selected_states)}"
        )
    results_by_seq = {
        exact_integer(row, "sample_seq", positive=True): row for row in selected_results
    }
    states_by_seq = {
        exact_integer(row, "sample_seq", positive=True): row for row in selected_states
    }
    if sorted(results_by_seq) != list(range(1, count + 1)) or sorted(states_by_seq) != list(range(1, count + 1)):
        raise anchor.ValidationError(f"{spec.name}: sequence is duplicated, missing, or out of range")
    centers = []
    for expected in spec.expected_rows:
        result = results_by_seq[expected.seq]
        state = states_by_seq[expected.seq]
        centers.append(validate_result(spec, result, expected, attempt))
        validate_state(spec, state, result, expected, attempt)
    closure_norms = validate_closures(spec, selected_closures, results_by_seq, attempt)
    return ValidatedRun(spec, attempt, np.vstack(centers), closure_norms)


def metric(centers: np.ndarray) -> tuple[float, float]:
    residuals = centers - np.mean(centers, axis=0)
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms**2))), float(np.max(norms))


def write_report(path: Path, runs: Sequence[ValidatedRun]) -> None:
    includes_t3 = any(run.spec.tool == 3 for run in runs)
    lines = [
        "# Relocated-Sphere Campaign Data Report",
        "",
        "All schemas, pose identities, tool states, contact quality, endpoints, and closures passed.",
        (
            "T4 is the training set. T3 passed as an untouched holdout and was not eligible for candidate selection."
            if includes_t3
            else "T4 is the training set. T3 remains an unread, untouched holdout and is not eligible for candidate selection."
        ),
        "",
        "| run | attempt | rows | current centered RMS / max | worst closure |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for run in runs:
        rms, maximum = metric(run.centers)
        lines.append(
            f"| {run.spec.name} | {run.attempt} | {len(run.centers)} | "
            f"{rms:.6f} / {maximum:.6f} mm | {np.max(run.closure_norms):.6f} mm |"
        )
    lines.extend(
        [
            "",
            (
                "These are current-calibration diagnostics, not a candidate release. T3 has now been checked only against the previously frozen T4-selected candidate."
                if includes_t3
                else "These are current-calibration diagnostics, not a candidate release. Fit selection may now use T4 only; freeze the candidate before reading or running T3."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines))


def self_test() -> None:
    reach.validate_model_constants()
    assert len(T4_SPEC.expected_rows) == 101
    assert len(T3_SPEC.expected_rows) == 31
    assert len(T4_SPEC.closure_ranges) == 28
    assert len(T3_SPEC.closure_ranges) == 14
    assert [row.seq for row in T4_SPEC.expected_rows] == list(range(1, 102))
    assert [row.seq for row in T3_SPEC.expected_rows] == list(range(1, 32))
    reach.validate_program_contract(reach.PRIMARY_PROGRAM)
    reach.validate_verification_program_contract(reach.VERIFICATION_PROGRAM)
    assert exact_integer({"attempt_id": "2.0"}, "attempt_id", positive=True) == 2
    for invalid in ("0", "-1", "1.5", "nan"):
        try:
            exact_integer({"attempt_id": invalid}, "attempt_id", positive=True)
        except anchor.ValidationError:
            pass
        else:
            raise AssertionError(f"invalid attempt ID {invalid} was accepted")
    geometry = {
        "probe_diameter_mm": "6.0",
        "probe_calibration_offset_mm": str(T4_SPEC.calibration_offset),
        "effective_contact_radius_mm": str(T4_SPEC.effective_radius),
    }
    validate_contact_geometry(T4_SPEC, geometry)
    bad_geometry = dict(geometry)
    bad_geometry["effective_contact_radius_mm"] = str(T4_SPEC.effective_radius + 0.005)
    try:
        validate_contact_geometry(T4_SPEC, bad_geometry)
    except anchor.ValidationError:
        pass
    else:
        raise AssertionError("inconsistent effective contact radius was accepted")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--t4-only",
        action="store_true",
        help="validate and report the completed T4 training set without reading T3",
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("self-test: PASS")
        return 0
    try:
        reach.validate_model_constants()
        reach.validate_program_contract(reach.PRIMARY_PROGRAM)
        reach.validate_verification_program_contract(reach.VERIFICATION_PROGRAM)
        runs = (validate_run(T4_SPEC),)
        if not args.t4_only:
            runs += (validate_run(T3_SPEC),)
        write_report(args.report, runs)
    except (OSError, ValueError, KeyError, anchor.ValidationError) as exc:
        print(f"campaign analysis: FAIL: {exc}", file=sys.stderr)
        return 1
    print("relocated-sphere campaign validation: PASS")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
