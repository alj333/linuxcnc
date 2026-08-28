#!/usr/bin/env python3
"""Replay the exact T4 location-2 Attempt-7 recovery against frozen q=0 kinematics.

This module is offline-only. It reads configuration and G-code files, writes
CSV/Markdown evidence, and has no LinuxCNC or HAL runtime interface.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import math
from pathlib import Path
import re
import sys

import numpy as np

import analyze_tcpc_relocated_sphere_reachability as reach


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
MODEL_HAL = HERE / "tcpc_length_aware_candidate_2026082601.hal"
VALIDATION_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini"
RUNNER = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.ngc"
REPLAY_MODULE = HERE / "analyze_tcpc_relocated_sphere_reachability.py"
ANCHOR_MODULE = HERE / "analyze_tcpc_relocated_sphere_anchor.py"
FIT_MODULE = HERE / "fit_tcpc_dual_probe.py"

DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT7_RECOVERY_REACHABILITY_REPORT.md"
DEFAULT_DETAILS = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-reachability.csv"

CAMPAIGN = 2026082701
MODE = 41
ATTEMPT = 7
MODEL_ID = 2026082601
TOOL_LENGTH_MM = 229.407000
START_XYZ = np.array([
    2501.9412544845527,
    696.8993474512587,
    -280.8661282715618,
])
G54_OFFSETS = np.array([
    2501.9412544845527,
    696.8993474512587,
    -510.27312827156186,
])
WORK_START = np.zeros(3)
CENTER_ALLOWANCE_MM = 2.0
PATH_MODEL_ALLOWANCE_MM = 3.0
HANDOFF_ENVELOPE_MM = 0.050
REQUIRED_REMAINING_MARGIN_MM = 10.0
A6_SEQ23_CENTER = np.array([2501.156895, 696.528585, -302.580083])
A6_PARTIAL_ARCHIVE_ROOT = "d2e84c1534d63d34974a438788ea3d03522d2b597e0d116e032ef587f91adde6"
A6_RESULTS = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery-results.csv"
A6_PARTIAL_SHA256SUMS = (
    HERE / "calibration_runs/"
    "20260828_0806_campaign2026082701_t4_new_location_attempt6_partial_gate_burst_abort_seq24/"
    "SHA256SUMS"
)
POST_TO_BASE = np.array([-1.0, 1.0, -1.0]) / math.sqrt(3.0)
POST_EFFECTIVE_RADIUS_MM = 18.0

EXPECTED_SHA256 = {
    BASE_HAL: "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778",
    MODEL_HAL: "8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14",
    VALIDATION_INI: "24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a",
    RUNNER: "fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d",
    REPLAY_MODULE: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    ANCHOR_MODULE: "30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d",
    FIT_MODULE: "7f005200a42bda0c2ccd39352fa1da71e6ba33d5d7f566bd5255c3548315bb97",
    A6_RESULTS: "06752f2d73dc1ecbf1f605922e2270c55aba0a81e60640bc9e5217730bb785e6",
    A6_PARTIAL_SHA256SUMS: A6_PARTIAL_ARCHIVE_ROOT,
}

SET_RE = re.compile(r"^\s*setp\s+(headheadkins\.[^\s]+)\s+([^\s#]+)")


class ReachabilityError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_hashes() -> None:
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256(path)
        if actual != expected:
            raise ReachabilityError(
                f"SHA-256 changed for {path.relative_to(REPO_ROOT)}: "
                f"{actual}, expected {expected}"
            )


def validate_runner_contract() -> None:
    text = RUNNER.read_text(encoding="ascii")
    required = (
        "#707 = 78.0", "#711 = 41.0", "#727 = 7.0", "#726 = 23.0",
        "#778 = 0.050", "#777 = 15.0", "#779 = 900.0",
        "#793 = 0.25", "#789 = #779", "#794 = #777", "#795 = #793",
        "#<gap_quiet_budget> = [#779 - #948]",
        "#<contact_quiet_budget> = [#779 - #976]",
        "#<quiet_consistency_raw> = #8", "#<quiet_consistency_mux> = #9",
        "TCPC_QUIET_FAIL code=#946 context=#<quiet_context>",
        "ABS[#978 - 25.0]",
        "ABS[#973 - 624.0]", "o<tcpc_external_continuity_guard> sub",
        "o<tcpc_primary_low_tilt_block> call [10.0] [10.0]",
        "o<tcpc_primary_low_tilt_block> call [-10.0] [-10.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
        "#831 = 2501.941254485", "#832 = 696.899347451",
        "#833 = -280.866128272", "#843 = 2501.941254485",
        "#844 = 696.899347451", "#845 = -510.273128272",
        "#837 = 2501.156895000", "#838 = 696.528585000",
        "#839 = -302.580083000", "#701 = #837", "#702 = #838",
        "#703 = #839", "o<tcpc_resume_start_guard> call",
    )
    for snippet in required:
        expected_count = {
            "o<tcpc_resume_start_guard> call": 2,
            "TCPC_QUIET_FAIL code=#946 context=#<quiet_context>": 3,
        }.get(snippet, 1)
        if text.count(snippet) != expected_count:
            raise ReachabilityError(f"Attempt-7 runner contract changed: {snippet}")
    if text.count("#700 = 1.0") != 2:
        raise ReachabilityError("Attempt-7 resume seed or accepted-center state changed")
    if "o<tcpc_primary_b0_sweep> call [100.0]" in text:
        raise ReachabilityError("Attempt-7 must not reacquire sequences 1..9")
    if "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]" in text:
        raise ReachabilityError("Attempt-7 must not reacquire Attempt-6 B+5 rows")
    if "o<tcpc_primary_low_tilt_block> call [-5.0] [-5.0]" in text:
        raise ReachabilityError("Attempt-7 must not reacquire Attempt-6 B-5 rows")
    dwell_lines = re.findall(r"^\s*G4\s+([^\r\n()]+)", text, re.MULTILINE)
    if dwell_lines != ["P#793", "P#793", "P#793"]:
        raise ReachabilityError(f"Attempt-7 automatic sampled dwell sites changed: {dwell_lines}")
    if re.search(r"^\s*G4 P(?:10|15)(?:\.0)?$", text, re.MULTILINE):
        raise ReachabilityError("Attempt-7 retains a fixed successful-contact dwell")
    quiet = re.search(
        r"^o<tcpc_stationary_quiet_guard> sub$.*?^o<tcpc_stationary_quiet_guard> endsub$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if quiet is None:
        raise ReachabilityError("Attempt-7 stationary quiet subroutine is missing")
    quiet_exec = "\n".join(
        line for line in quiet.group(0).splitlines()
        if not line.lstrip().startswith("(")
    )
    if re.search(r"^\s*(?:G0|G1|G2|G3|G38|M0|M1|M60|M62|M63|M64|M65)(?:\s|\.)", quiet_exec, re.MULTILINE):
        raise ReachabilityError("Attempt-7 stationary quiet contains motion, hold, or gate write")
    if max(map(len, text.splitlines())) > 225:
        raise ReachabilityError("Attempt-7 runner exceeds the 225-character parser-safe line bound")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ReachabilityError("Attempt-7 four-contact probe topology changed")


def merged_model_pins() -> dict[str, float]:
    pins = reach.parse_hal(BASE_HAL)
    overlay = MODEL_HAL.read_text(encoding="ascii")
    active_id = None
    for line in overlay.splitlines():
        match = SET_RE.match(line)
        if match is None:
            continue
        try:
            value = float(match.group(2))
        except ValueError as exc:
            raise ReachabilityError(f"non-numeric model assignment: {line}") from exc
        if not math.isfinite(value):
            raise ReachabilityError(f"non-finite model assignment: {line}")
        pins[match.group(1)] = value
        if match.group(1) == "headheadkins.length-model.id":
            active_id = value
    if active_id != MODEL_ID:
        raise ReachabilityError(
            f"model overlay did not finish with ID {MODEL_ID}: {active_id}"
        )
    if pins.get("headheadkins.length-model.reference") != TOOL_LENGTH_MM:
        raise ReachabilityError("T4 is not the q=0 reference length")
    return pins


def estimated_center(start_xyz: np.ndarray) -> np.ndarray:
    del start_xyz
    return A6_SEQ23_CENTER.copy()


def recovery_grid() -> list[reach.Pose]:
    """Use exact Attempt-7 continuation order: canonical sequences 24..101."""
    return [pose for pose in reach.grid() if 24 <= pose.slot <= 101]


def center_derived_clear(center: np.ndarray) -> np.ndarray:
    """Match the runner's B0/C0 current_clear calculation from #701..#703."""
    return center + np.array([0.0, 0.0, reach.TOP_CLEAR_RADIUS])


def effective_post_clearance(point: np.ndarray, center: np.ndarray) -> float:
    """Clearance to a sphere-width post ray beginning at the sphere surface."""
    post_start = center + POST_TO_BASE * 15.0
    offset = point - post_start
    along = max(0.0, float(np.dot(offset, POST_TO_BASE)))
    radial = offset - along * POST_TO_BASE
    return float(np.linalg.norm(radial) - POST_EFFECTIVE_RADIUS_MM)


def axis_guard_vertices() -> list[tuple[float, float, float, float]]:
    """Enumerate one-axis work/G54/TLO/absolute guard-polytope vertices."""
    planes: list[tuple[np.ndarray, float]] = []
    for normal, bound in (
        (np.array([1.0, 0.0, 0.0]), 0.050),
        (np.array([0.0, 1.0, 0.0]), 0.050),
        (np.array([0.0, 0.0, 1.0]), 0.002),
        (np.array([1.0, 1.0, 1.0]), 0.050),
    ):
        planes.extend((normal, sign * bound) for sign in (-1.0, 1.0))
    vertices: set[tuple[float, float, float, float]] = set()
    for selected in itertools.combinations(planes, 3):
        matrix = np.array([plane[0] for plane in selected])
        if abs(float(np.linalg.det(matrix))) < 1e-12:
            continue
        work, g54, tlo = np.linalg.solve(
            matrix, np.array([plane[1] for plane in selected])
        )
        absolute = work + g54 + tlo
        if (
            abs(work) <= 0.0500000001
            and abs(g54) <= 0.0500000001
            and abs(tlo) <= 0.0020000001
            and abs(absolute) <= 0.0500000001
        ):
            vertices.add(
                tuple(round(float(value), 12) for value in (work, g54, tlo, absolute))
            )
    result = sorted(vertices)
    if len(result) != 12:
        raise ReachabilityError(
            f"one-axis coordinate guard polytope has {len(result)} vertices, expected 12"
        )
    return result


def coordinate_guard_projection() -> tuple[int, list[tuple[tuple[float, float, float], np.ndarray]]]:
    """Enumerate 1,728 layer vertices and their 64 mapped physical starts."""
    axis_vertices = axis_guard_vertices()
    states = list(itertools.product(axis_vertices, repeat=3))
    physical: dict[tuple[float, float, float], np.ndarray] = {}
    for state in states:
        absolute_delta = tuple(axis[3] for axis in state)
        physical[absolute_delta] = START_XYZ + np.array(absolute_delta)
    if len(states) != 1728 or len(physical) != 64:
        raise ReachabilityError(
            f"coordinate guard projection is {len(states)} states/{len(physical)} starts"
        )
    return len(states), sorted(physical.items())


def handoff_samples(
    start_xyz: np.ndarray,
    target: np.ndarray,
    center: np.ndarray,
    pins: dict[str, float],
    limits: reach.Limits,
    label: str,
) -> tuple[list[reach.Sample], float, float, float]:
    samples: list[reach.Sample] = []
    seed_pose = reach.Pose(23, 0.0, 0.0, "attempt6_seq23_b0_resume_seed")
    minimum_clearance = math.inf
    minimum_post_clearance = math.inf
    minimum_z_above_center = math.inf
    for point in reach.linear_points(start_xyz, target, maximum_step=0.010):
        reach.append_sample(
            samples, 4, TOOL_LENGTH_MM, seed_pose,
            f"resume_handoff_{label}", point, pins, limits,
        )
        minimum_clearance = min(
            minimum_clearance,
            float(np.linalg.norm(point - center) - reach.T4_EFFECTIVE_RADIUS),
        )
        minimum_post_clearance = min(
            minimum_post_clearance,
            effective_post_clearance(point, center),
        )
        minimum_z_above_center = min(
            minimum_z_above_center, float(point[2] - center[2])
        )
    return samples, minimum_clearance, minimum_post_clearance, minimum_z_above_center


def replay() -> tuple[
    np.ndarray,
    np.ndarray,
    list[reach.Sample],
    reach.Limits,
    list[dict[str, object]],
]:
    validate_hashes()
    validate_runner_contract()
    pins = merged_model_pins()
    limits = reach.parse_limits(VALIDATION_INI)
    poses = recovery_grid()
    if len(poses) != 78:
        raise ReachabilityError("T4 Attempt-7 continuation grid is not 78 rows")
    center = estimated_center(START_XYZ)
    target = center_derived_clear(center)
    seed_pose = reach.Pose(23, 0.0, 0.0, "attempt6_seq23_b0_resume_seed")
    seeded = reach.replay(
        center,
        pins,
        limits,
        tool=4,
        length=TOOL_LENGTH_MM,
        effective_radius=reach.T4_EFFECTIVE_RADIUS,
        poses=[seed_pose, *poses],
    )
    # The synthetic seed contributes no probe cycle. Its state creates the
    # common exact sequence-23-to-24 high-Z transition in the retained samples.
    common_tail = [sample for sample in seeded if sample.slot != seed_pose.slot]
    if not common_tail:
        raise ReachabilityError("reachability replay produced no continuation samples")

    # The absolute guard is the final physical-position constraint. Replaying
    # its complete cube is conservative over all consistent work/G54/TLO states.
    samples: list[reach.Sample] = []
    corner_metrics: list[dict[str, object]] = []
    coordinate_state_count, physical_starts = coordinate_guard_projection()
    for deviations, corner in physical_starts:
        label = "vertex_" + "_".join(f"{value:+.3f}" for value in deviations)
        corner_samples, clearance, post_clearance, z_above = handoff_samples(
            corner, target, center, pins, limits, label
        )
        samples.extend(corner_samples)
        corner_metrics.append(
            {
                "deviations": deviations,
                "start": corner,
                "distance": float(np.linalg.norm(target - corner)),
                "sphere_clearance": clearance,
                "post_clearance": post_clearance,
                "z_above_center": z_above,
            }
        )
    nominal_samples, nominal_clearance, nominal_post_clearance, nominal_z_above = handoff_samples(
        START_XYZ, target, center, pins, limits, "nominal"
    )
    samples.extend(nominal_samples)
    samples.extend(common_tail)
    corner_metrics.append(
        {
            "deviations": (0.0, 0.0, 0.0),
            "start": START_XYZ.copy(),
            "distance": float(np.linalg.norm(target - START_XYZ)),
            "sphere_clearance": nominal_clearance,
            "post_clearance": nominal_post_clearance,
            "z_above_center": nominal_z_above,
            "coordinate_state_count": coordinate_state_count,
        }
    )
    if not samples:
        raise ReachabilityError("reachability replay produced no samples")
    return center, target, samples, limits, corner_metrics


def summarize(
    samples: list[reach.Sample],
    limits: reach.Limits,
    corner_metrics: list[dict[str, object]],
) -> dict[str, object]:
    per_joint = [
        min(samples, key=lambda sample, index=index: sample.joint_margins[index])
        for index in range(3)
    ]
    per_axis = [
        min(samples, key=lambda sample, index=index: sample.axis_margins[index])
        for index in range(3)
    ]
    reserve = CENTER_ALLOWANCE_MM + PATH_MODEL_ALLOWANCE_MM + HANDOFF_ENVELOPE_MM
    minimum_nominal = min(
        *(float(sample.joint_margins[index]) for index, sample in enumerate(per_joint)),
        *(float(sample.axis_margins[index]) for index, sample in enumerate(per_axis)),
    )
    b_margin = min(
        min(pose.b_deg - limits.b_limits[0], limits.b_limits[1] - pose.b_deg)
        for pose in recovery_grid()
    )
    c_margin = min(
        min(pose.c_deg - limits.c_limits[0], limits.c_limits[1] - pose.c_deg)
        for pose in recovery_grid()
    )
    worst_clearance = min(
        corner_metrics, key=lambda item: float(item["sphere_clearance"])
    )
    worst_post_handoff = min(
        corner_metrics, key=lambda item: float(item["post_clearance"])
    )
    entry_kinds = {
        "transit_lift", "transit_rotary", "transit_xy", "transit_descend", "top_clear"
    }
    entry_samples = [
        sample for sample in samples
        if sample.kind.startswith("resume_handoff")
        or (sample.slot == 24 and sample.kind in entry_kinds)
    ]
    if not entry_samples:
        raise ReachabilityError("Attempt-7 replay produced no first-entry samples")
    entry_post_clearance = min(
        effective_post_clearance(sample.tcp, A6_SEQ23_CENTER)
        for sample in entry_samples
    )
    entry_sphere_clearance = min(
        float(np.linalg.norm(sample.tcp - A6_SEQ23_CENTER) - reach.T4_EFFECTIVE_RADIUS)
        for sample in entry_samples
    )
    nominal = next(
        item for item in corner_metrics
        if item["deviations"] == (0.0, 0.0, 0.0)
    )
    minimum_z_above_center = min(
        float(item["z_above_center"]) for item in corner_metrics
    )
    passed = (
        minimum_nominal - reserve >= REQUIRED_REMAINING_MARGIN_MM
        and b_margin >= 5.0
        and c_margin >= 5.0
        and float(worst_clearance["sphere_clearance"]) > 0.0
        and float(worst_post_handoff["post_clearance"]) > 0.0
        and entry_post_clearance > 0.0
        and entry_sphere_clearance > 0.0
        and minimum_z_above_center > reach.T4_EFFECTIVE_RADIUS
    )
    return {
        "per_joint": per_joint,
        "per_axis": per_axis,
        "minimum_nominal": minimum_nominal,
        "remaining": minimum_nominal - reserve,
        "b_margin": b_margin,
        "c_margin": c_margin,
        "worst_clearance": worst_clearance,
        "worst_post_handoff": worst_post_handoff,
        "entry_post_clearance": entry_post_clearance,
        "entry_sphere_clearance": entry_sphere_clearance,
        "nominal_handoff": nominal,
        "minimum_z_above_center": minimum_z_above_center,
        "passed": passed,
    }


def write_report(
    path: Path,
    details: Path,
    center: np.ndarray,
    target: np.ndarray,
    samples: list[reach.Sample],
    summary: dict[str, object],
) -> None:
    reserve = CENTER_ALLOWANCE_MM + PATH_MODEL_ALLOWANCE_MM + HANDOFF_ENVELOPE_MM
    nominal = summary["nominal_handoff"]
    worst = summary["worst_clearance"]
    worst_post = summary["worst_post_handoff"]
    worst_delta = ", ".join(f"{value:+.3f}" for value in worst["deviations"])
    lines = [
        "# T4 New-Location Attempt-7 Continuation Reachability",
        "",
        f"Status: `{'PASS' if summary['passed'] else 'FAIL'}`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- frozen model / T4 length: `{MODEL_ID} / {TOOL_LENGTH_MM:.6f} mm`",
        f"- active WCS / work start: `G54 / X{WORK_START[0]:.3f} Y{WORK_START[1]:.3f} Z{WORK_START[2]:.3f}`",
        f"- frozen G54 offsets: `X{G54_OFFSETS[0]:.9f} Y{G54_OFFSETS[1]:.9f} Z{G54_OFFSETS[2]:.9f}` mm",
        f"- nominal B0/C0 absolute start: `X{START_XYZ[0]:.9f} Y{START_XYZ[1]:.9f} Z{START_XYZ[2]:.9f}` mm",
        f"- frozen Attempt-6 sequence-23 center seed: `X{center[0]:.9f} Y{center[1]:.9f} Z{center[2]:.9f}` mm",
        f"- center-derived B0/C0 top-clear: `X{target[0]:.9f} Y{target[1]:.9f} Z{target[2]:.9f}` mm",
        f"- nominal first handoff distance: `{float(nominal['distance']):.9f} mm`",
        f"- nominal / worst-vertex physical sphere clearance: `{float(nominal['sphere_clearance']):.9f} / {float(worst['sphere_clearance']):.9f} mm`",
        f"- nominal / worst-vertex effective post clearance: `{float(nominal['post_clearance']):.9f} / {float(worst_post['post_clearance']):.9f} mm`",
        f"- minimum sphere / effective-post clearance over first entry: `{float(summary['entry_sphere_clearance']):.9f} / {float(summary['entry_post_clearance']):.9f} mm`",
        f"- worst physical-start deviation XYZ: `{worst_delta}` mm at `X{worst['start'][0]:.9f} Y{worst['start'][1]:.9f} Z{worst['start'][2]:.9f}` mm",
        f"- coordinate guard enumeration: `{int(nominal['coordinate_state_count'])}` simultaneous layer vertices -> `64` distinct mapped physical starts",
        f"- sampled grid/path points: `{len(samples)}` over `64` physical-start handoffs, nominal handoff, and `78` recovery poses",
        f"- automatic chatter quiet: `{15.0:.1f} s` continuous, `{900.0:.1f} s` cumulative context cap, `{0.25:.2f} s` samples",
        f"- center / path-model / handoff reserves: `{CENTER_ALLOWANCE_MM:.3f} / {PATH_MODEL_ALLOWANCE_MM:.3f} / {HANDOFF_ENVELOPE_MM:.3f} mm`",
        f"- required margin after `{reserve:.3f} mm` reserve: `{REQUIRED_REMAINING_MARGIN_MM:.3f} mm`",
        f"- frozen runner SHA-256: `{EXPECTED_SHA256[RUNNER]}`",
        "",
        "| constraint | nominal margin | after reserve | limiting pose/sample | position |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for index, sample in enumerate(summary["per_joint"]):
        margin = float(sample.joint_margins[index])
        lines.append(
            f"| J{index} | {margin:.6f} mm | {margin - reserve:.6f} mm | "
            f"B{sample.b_deg:+g} C{sample.c_deg:g} `{sample.kind}` | "
            f"{sample.joints[index]:.6f} mm |"
        )
    for index, name in enumerate("XYZ"):
        sample = summary["per_axis"][index]
        margin = float(sample.axis_margins[index])
        lines.append(
            f"| {name} axis | {margin:.6f} mm | {margin - reserve:.6f} mm | "
            f"B{sample.b_deg:+g} C{sample.c_deg:g} `{sample.kind}` | "
            f"{sample.tcp[index]:.6f} mm |"
        )
    lines.extend(
        [
            "",
            f"Rotary configured-limit margins: B `{summary['b_margin']:.3f} deg`, C `{summary['c_margin']:.3f} deg`.",
            "",
            "The exact replay starts at guarded active-G54 work X0/Y0/Z0 and first moves to the B0/C0 top-clear derived from the immutable accepted Attempt-6 sequence-23 center. It then applies the runner's 25 mm Z lift, B10/C0 index, XY positioning, Z descent, full sequence-24 reacquisition, and exact sequence-24-to-101 tail.",
            "",
            "The simultaneous start guards were not collapsed by assertion. For each axis the analyzer solves the bounded work, G54, TLO, and absolute-position identity polytope: 12 vertices per axis, 1,728 XYZ layer-state vertices, and 64 distinct mapped physical starts. Every mapped start is replayed to the one fixed center-derived top-clear; the nominal start is replayed separately. The absolute guard makes this enumeration the exact physical projection, while the separate post-M0 hold guard restricts movement to 0.001 mm.",
            "",
            f"Every first-segment sample remains at least `{float(summary['minimum_z_above_center']):.9f} mm` above the sphere center, greater than the `{reach.T4_EFFECTIVE_RADIUS:.9f} mm` effective contact radius. The first handoff, 25 mm lift, B10 index, XY move, and descent retain positive modeled sphere and post clearance. The post ray begins at the sphere surface and extends toward X-, Y+, Z- (base-to-sphere X+, Y-, Z+), so it does not consume the sphere itself. Its 18 mm effective radius conservatively bounds a post no wider than the 30 mm sphere plus the 3 mm probe-ball radius.",
            "",
            "The full 0.050 mm start envelope is additive to the 2 mm center and 3 mm path/model reserves for configured-limit reporting.",
            "",
            "The complete sequence-24-to-101 trajectory is replayed against configured joint/axis limits. The effective-post calculation applies to the noncontact first-entry path only; it deliberately excludes intended sphere contact/overtravel samples and does not claim a body/holder/fixture proof. The operator's prior pose-clearance confirmation remains the authority for those physical clearances, along with the secured sphere and laser-off checks.",
            "",
            "All automatic quiet loops are stationary: they contain sampled dwell/synchronization plus live, model, pose, counter, level, and fault guards, with no axis/rotary motion, gate write, or operator hold. Therefore the quiet policy adds no geometric path samples. Normal no-chatter contacts wait only for physical release and the existing 10.0 second HAL ignore window; matched gate-closed activity resets a 15.0 second continuous quiet timer within a cumulative 900.0 second contact or gap budget.",
            "",
            "The policy is based on the stationary observation in which raw/mux counters rose together from 1259 to 1283 while gated remained 618 over roughly 50 seconds, then became quiet after 08:40:28. Matched raw/mux extras are diagnostic; any outside-G38 gated change, final cumulative mismatch, uncleared fault/levels, or cumulative timeout remains fatal.",
            "",
            "Because X, Y, and Z all changed from the reference location, this is a machine-volume transfer test, not an isolated X-axis straightness measurement.",
            "",
            f"Detailed samples: `{details.name}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--details", type=Path, default=DEFAULT_DETAILS)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        center, target, samples, limits, corner_metrics = replay()
        summary = summarize(samples, limits, corner_metrics)
        if args.self_test:
            assert np.allclose(
                center,
                [2501.156895, 696.528585, -302.580083],
                atol=1e-9,
            )
            assert np.allclose(
                target,
                [2501.156895, 696.528585, -279.734825],
                atol=1e-9,
            )
            assert np.allclose(
                G54_OFFSETS + WORK_START + [0.0, 0.0, TOOL_LENGTH_MM],
                START_XYZ,
                atol=1e-9,
            )
            assert abs(float(summary["nominal_handoff"]["distance"]) - 1.4256688565432931) < 1e-9
            assert abs(float(summary["nominal_handoff"]["sphere_clearance"]) - 3.886021634318219) < 1e-9
            assert len(axis_guard_vertices()) == 12
            assert int(summary["nominal_handoff"]["coordinate_state_count"]) == 1728
            assert len(corner_metrics) == 65
            assert float(summary["worst_clearance"]["sphere_clearance"]) > 0.0
            assert float(summary["worst_post_handoff"]["post_clearance"]) > 0.0
            assert float(summary["entry_post_clearance"]) > 0.0
            assert float(summary["entry_sphere_clearance"]) > 0.0
            assert summary["passed"]
            assert [pose.slot for pose in recovery_grid()] == list(range(24, 102))
            print("T4 new-location Attempt-7 continuation reachability self-test: PASS")
            return 0
        reach.write_details(args.details, samples)
        write_report(args.report, args.details, center, target, samples, summary)
    except (AssertionError, OSError, ValueError, ReachabilityError) as exc:
        print(f"T4 new-location reachability: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"T4 new-location reachability: {'PASS' if summary['passed'] else 'FAIL'}")
    print(f"report: {args.report}")
    print(f"details: {args.details}")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
