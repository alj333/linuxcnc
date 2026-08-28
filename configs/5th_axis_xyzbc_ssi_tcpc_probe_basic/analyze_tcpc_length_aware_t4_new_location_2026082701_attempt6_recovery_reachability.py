#!/usr/bin/env python3
"""Replay the exact T4 location-2 Attempt-6 grid against frozen q=0 kinematics.

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
RUNNER = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery.ngc"
REPLAY_MODULE = HERE / "analyze_tcpc_relocated_sphere_reachability.py"
ANCHOR_MODULE = HERE / "analyze_tcpc_relocated_sphere_anchor.py"
FIT_MODULE = HERE / "fit_tcpc_dual_probe.py"

DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT6_RECOVERY_REACHABILITY_REPORT.md"
DEFAULT_DETAILS = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery-reachability.csv"

CAMPAIGN = 2026082701
MODE = 40
ATTEMPT = 6
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
OBSERVED_A4_TERMINAL_CLEAR = np.array([
    2500.9727270632798,
    696.5502785572226,
    -279.73079775900703,
])
CENTER_ALLOWANCE_MM = 2.0
PATH_MODEL_ALLOWANCE_MM = 3.0
HANDOFF_ENVELOPE_MM = 0.050
REQUIRED_REMAINING_MARGIN_MM = 10.0
A4_ROW9_CENTER = np.array([2500.940456, 696.558194, -302.576056])

EXPECTED_SHA256 = {
    BASE_HAL: "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778",
    MODEL_HAL: "8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14",
    VALIDATION_INI: "24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a",
    RUNNER: "2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310",
    REPLAY_MODULE: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    ANCHOR_MODULE: "30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d",
    FIT_MODULE: "7f005200a42bda0c2ccd39352fa1da71e6ba33d5d7f566bd5255c3548315bb97",
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
        "#707 = 92.0", "#711 = 40.0", "#727 = 6.0", "#726 = 9.0",
        "#778 = 0.050", "ABS[#978 - 27.0]",
        "ABS[#973 - 736.0]", "o<tcpc_external_continuity_guard> sub",
        "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]",
        "o<tcpc_primary_low_tilt_block> call [-5.0] [-5.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
        "#831 = 2501.941254485", "#832 = 696.899347451",
        "#833 = -280.866128272", "#843 = 2501.941254485",
        "#844 = 696.899347451", "#845 = -510.273128272",
        "#701 = 2500.940456", "#702 = 696.558194",
        "#703 = -302.576056", "o<tcpc_resume_start_guard> call",
    )
    for snippet in required:
        expected_count = 2 if snippet == "o<tcpc_resume_start_guard> call" else 1
        if text.count(snippet) != expected_count:
            raise ReachabilityError(f"Attempt-6 runner contract changed: {snippet}")
    if text.count("#700 = 1.0") != 2:
        raise ReachabilityError("Attempt-6 resume seed or accepted-center state changed")
    if "o<tcpc_primary_b0_sweep> call [100.0]" in text:
        raise ReachabilityError("Attempt-6 must not reacquire sequences 1..9")
    if len(re.findall(r"^\s*G4 P10\.0$", text, re.MULTILINE)) != 4:
        raise ReachabilityError("Attempt-6 lost a post-contact 10 second dwell")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ReachabilityError("Attempt-6 four-contact probe topology changed")


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
    return A4_ROW9_CENTER.copy()


def recovery_grid() -> list[reach.Pose]:
    """Use exact Attempt-6 continuation order: canonical sequences 10..101."""
    return [pose for pose in reach.grid() if 10 <= pose.slot <= 101]


def center_derived_clear(center: np.ndarray) -> np.ndarray:
    """Match the runner's B0/C0 current_clear calculation from #701..#703."""
    return center + np.array([0.0, 0.0, reach.TOP_CLEAR_RADIUS])


def start_corners() -> list[tuple[tuple[int, int, int], np.ndarray]]:
    """Return the eight corners of the runner's absolute-start guard cube."""
    return [
        (signs, START_XYZ + HANDOFF_ENVELOPE_MM * np.array(signs, dtype=float))
        for signs in itertools.product((-1, 1), repeat=3)
    ]


def handoff_samples(
    start_xyz: np.ndarray,
    target: np.ndarray,
    center: np.ndarray,
    pins: dict[str, float],
    limits: reach.Limits,
    label: str,
) -> tuple[list[reach.Sample], float, float]:
    samples: list[reach.Sample] = []
    seed_pose = reach.Pose(9, 0.0, 0.0, "attempt4_row9_resume_seed")
    minimum_clearance = math.inf
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
        minimum_z_above_center = min(
            minimum_z_above_center, float(point[2] - center[2])
        )
    return samples, minimum_clearance, minimum_z_above_center


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
    if len(poses) != 92:
        raise ReachabilityError("T4 Attempt-6 continuation grid is not 92 rows")
    center = estimated_center(START_XYZ)
    target = center_derived_clear(center)
    seed_pose = reach.Pose(9, 0.0, 0.0, "attempt4_row9_resume_seed")
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
    # common exact sequence-9-to-10 high-Z transition in the retained samples.
    common_tail = [sample for sample in seeded if sample.slot != seed_pose.slot]
    if not common_tail:
        raise ReachabilityError("reachability replay produced no continuation samples")

    # The absolute guard is the final physical-position constraint. Replaying
    # its complete cube is conservative over all consistent work/G54/TLO states.
    samples: list[reach.Sample] = []
    corner_metrics: list[dict[str, object]] = []
    for signs, corner in start_corners():
        label = "corner_" + "_".join("p" if value > 0 else "m" for value in signs)
        corner_samples, clearance, z_above = handoff_samples(
            corner, target, center, pins, limits, label
        )
        samples.extend(corner_samples)
        corner_metrics.append(
            {
                "signs": signs,
                "start": corner,
                "distance": float(np.linalg.norm(target - corner)),
                "sphere_clearance": clearance,
                "z_above_center": z_above,
            }
        )
    nominal_samples, nominal_clearance, nominal_z_above = handoff_samples(
        START_XYZ, target, center, pins, limits, "nominal"
    )
    samples.extend(nominal_samples)
    samples.extend(common_tail)
    corner_metrics.append(
        {
            "signs": (0, 0, 0),
            "start": START_XYZ.copy(),
            "distance": float(np.linalg.norm(target - START_XYZ)),
            "sphere_clearance": nominal_clearance,
            "z_above_center": nominal_z_above,
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
    nominal = next(item for item in corner_metrics if item["signs"] == (0, 0, 0))
    minimum_z_above_center = min(
        float(item["z_above_center"]) for item in corner_metrics
    )
    passed = (
        minimum_nominal - reserve >= REQUIRED_REMAINING_MARGIN_MM
        and b_margin >= 5.0
        and c_margin >= 5.0
        and float(worst_clearance["sphere_clearance"]) > 0.0
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
    archived_difference = float(np.linalg.norm(OBSERVED_A4_TERMINAL_CLEAR - target))
    worst_signs = "".join("+" if value > 0 else "-" for value in worst["signs"])
    lines = [
        "# T4 New-Location Attempt-6 Continuation Reachability",
        "",
        f"Status: `{'PASS' if summary['passed'] else 'FAIL'}`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- frozen model / T4 length: `{MODEL_ID} / {TOOL_LENGTH_MM:.6f} mm`",
        f"- active WCS / work start: `G54 / X{WORK_START[0]:.3f} Y{WORK_START[1]:.3f} Z{WORK_START[2]:.3f}`",
        f"- frozen G54 offsets: `X{G54_OFFSETS[0]:.9f} Y{G54_OFFSETS[1]:.9f} Z{G54_OFFSETS[2]:.9f}` mm",
        f"- nominal B0/C0 absolute start: `X{START_XYZ[0]:.9f} Y{START_XYZ[1]:.9f} Z{START_XYZ[2]:.9f}` mm",
        f"- frozen Attempt-4 row-9 center seed: `X{center[0]:.9f} Y{center[1]:.9f} Z{center[2]:.9f}` mm",
        f"- center-derived B0/C0 top-clear: `X{target[0]:.9f} Y{target[1]:.9f} Z{target[2]:.9f}` mm",
        f"- nominal first handoff distance: `{float(nominal['distance']):.9f} mm`",
        f"- nominal / worst-corner physical sphere clearance: `{float(nominal['sphere_clearance']):.9f} / {float(worst['sphere_clearance']):.9f} mm`",
        f"- worst absolute-envelope corner: `{worst_signs}` at `X{worst['start'][0]:.9f} Y{worst['start'][1]:.9f} Z{worst['start'][2]:.9f}` mm",
        f"- sampled unique grid/path points: `{len(samples)}` over `8` envelope-corner handoffs, nominal handoff, and `92` recovery poses",
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
            "The exact replay starts at guarded active-G54 work X0/Y0/Z0 and moves directly to the B0/C0 top-clear derived from the immutable accepted Attempt-4 row-9 center. There is no motion through the archived Attempt-4 terminal-clear point. The full eight-corner 0.050 mm absolute-start cube is replayed; it conservatively contains every physical start admitted by the simultaneous work-coordinate, G54-offset, tool-length, and absolute-position guards. After the common top-clear endpoint, the exact sequence-10-to-101 trajectory is independent of the selected start corner.",
            "",
            f"The observed Attempt-4 terminal clear was `X{OBSERVED_A4_TERMINAL_CLEAR[0]:.9f} Y{OBSERVED_A4_TERMINAL_CLEAR[1]:.9f} Z{OBSERVED_A4_TERMINAL_CLEAR[2]:.9f}` mm, `{archived_difference:.9f} mm` from the center-derived clear. That 0.033228 mm difference is archived provenance from the row-9 measured correction before Attempt 4 aborted at its closure; it is not an Attempt-6 waypoint or center seed.",
            "",
            f"Every handoff sample remains at least `{float(summary['minimum_z_above_center']):.9f} mm` above the sphere center, greater than the `{reach.T4_EFFECTIVE_RADIUS:.9f} mm` effective contact radius. The post extends below the sphere toward X-, Y+, Z-, so this above-sphere handoff cannot intersect the reviewed post segment.",
            "",
            "The full 0.050 mm handoff envelope is also additive to the 2 mm center and 3 mm path/model reserves for configured-limit reporting. The separate post-M0 hold guard permits only 0.001 mm physical movement before motion.",
            "",
            "This is a configured-limit and kinematic-path proof. The operator remains responsible for confirming the unchanged post direction (base to sphere X+, Y-, Z+), nearby fixture clearance, secured sphere, and laser-off condition.",
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
                [2500.940456, 696.558194, -302.576056],
                atol=1e-9,
            )
            assert np.allclose(
                target,
                [2500.940456, 696.558194, -279.730798],
                atol=1e-9,
            )
            assert np.allclose(
                G54_OFFSETS + WORK_START + [0.0, 0.0, TOOL_LENGTH_MM],
                START_XYZ,
                atol=1e-9,
            )
            assert abs(float(summary["nominal_handoff"]["distance"]) - 1.5514374333223189) < 1e-9
            assert abs(float(summary["nominal_handoff"]["sphere_clearance"]) - 3.890402681423918) < 1e-9
            assert abs(float(summary["worst_clearance"]["sphere_clearance"]) - 3.837483000426399) < 1e-9
            assert abs(float(np.linalg.norm(OBSERVED_A4_TERMINAL_CLEAR - target)) - 0.03322763548071013) < 1e-9
            assert len(corner_metrics) == 9
            assert summary["passed"]
            assert [pose.slot for pose in recovery_grid()] == list(range(10, 102))
            print("T4 new-location Attempt-6 continuation reachability self-test: PASS")
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
