#!/usr/bin/env python3
"""Replay the exact T4 location-2 Attempt-5 grid against frozen q=0 kinematics.

This module is offline-only. It reads configuration and G-code files, writes
CSV/Markdown evidence, and has no LinuxCNC or HAL runtime interface.
"""

from __future__ import annotations

import argparse
import hashlib
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
RUNNER = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.ngc"
REPLAY_MODULE = HERE / "analyze_tcpc_relocated_sphere_reachability.py"
ANCHOR_MODULE = HERE / "analyze_tcpc_relocated_sphere_anchor.py"
FIT_MODULE = HERE / "fit_tcpc_dual_probe.py"

DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT5_RECOVERY_REACHABILITY_REPORT.md"
DEFAULT_DETAILS = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt5-recovery-reachability.csv"

CAMPAIGN = 2026082701
MODE = 39
ATTEMPT = 5
MODEL_ID = 2026082601
TOOL_LENGTH_MM = 229.407000
START_XYZ = np.array([
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
    RUNNER: "372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1",
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
        "#707 = 92.0", "#711 = 39.0", "#727 = 5.0", "#726 = 9.0",
        "#778 = 0.050", "ABS[#978 - 27.0]",
        "ABS[#973 - 736.0]", "o<tcpc_external_continuity_guard> sub",
        "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]",
        "o<tcpc_primary_low_tilt_block> call [-5.0] [-5.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
    )
    for snippet in required:
        if text.count(snippet) != 1:
            raise ReachabilityError(f"Attempt-5 runner contract changed: {snippet}")
    if text.count("#700 = 1.0") != 2:
        raise ReachabilityError("Attempt-5 resume seed or accepted-center state changed")
    if "o<tcpc_primary_b0_sweep> call [100.0]" in text:
        raise ReachabilityError("Attempt-5 must not reacquire sequences 1..9")
    if len(re.findall(r"^\s*G4 P10\.0$", text, re.MULTILINE)) != 4:
        raise ReachabilityError("Attempt-5 lost a post-contact 10 second dwell")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ReachabilityError("Attempt-5 four-contact probe topology changed")


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
    """Use exact Attempt-5 continuation order: canonical sequences 10..101."""
    return [pose for pose in reach.grid() if 10 <= pose.slot <= 101]


def replay(start_xyz: np.ndarray) -> tuple[np.ndarray, list[reach.Sample], reach.Limits]:
    if start_xyz.shape != (3,) or not np.all(np.isfinite(start_xyz)):
        raise ReachabilityError("start XYZ must contain three finite values")
    if np.any(np.abs(start_xyz - START_XYZ) > HANDOFF_ENVELOPE_MM):
        raise ReachabilityError("start XYZ exceeds the frozen 0.050 mm handoff envelope")
    validate_hashes()
    validate_runner_contract()
    pins = merged_model_pins()
    limits = reach.parse_limits(VALIDATION_INI)
    poses = recovery_grid()
    if len(poses) != 92:
        raise ReachabilityError("T4 Attempt-5 continuation grid is not 92 rows")
    center = estimated_center(start_xyz)
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
    # Discard the synthetic seed's probe paths but retain the transition it
    # creates into sequence 10. Add the runner's initial current-to-seed move.
    seed_top = center + np.array([0.0, 0.0, reach.TOP_CLEAR_RADIUS])
    samples: list[reach.Sample] = []
    for point in reach.linear_points(start_xyz, seed_top):
        reach.append_sample(
            samples, 4, TOOL_LENGTH_MM, seed_pose, "resume_handoff_path",
            point, pins, limits,
        )
    samples.extend(sample for sample in seeded if sample.slot != seed_pose.slot)
    if not samples:
        raise ReachabilityError("reachability replay produced no samples")
    return center, samples, limits


def summarize(samples: list[reach.Sample], limits: reach.Limits) -> dict[str, object]:
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
    passed = (
        minimum_nominal - reserve >= REQUIRED_REMAINING_MARGIN_MM
        and b_margin >= 5.0
        and c_margin >= 5.0
    )
    return {
        "per_joint": per_joint,
        "per_axis": per_axis,
        "minimum_nominal": minimum_nominal,
        "remaining": minimum_nominal - reserve,
        "b_margin": b_margin,
        "c_margin": c_margin,
        "passed": passed,
    }


def write_report(
    path: Path,
    details: Path,
    start_xyz: np.ndarray,
    center: np.ndarray,
    samples: list[reach.Sample],
    summary: dict[str, object],
) -> None:
    reserve = CENTER_ALLOWANCE_MM + PATH_MODEL_ALLOWANCE_MM + HANDOFF_ENVELOPE_MM
    lines = [
        "# T4 New-Location Attempt-5 Continuation Reachability",
        "",
        f"Status: `{'PASS' if summary['passed'] else 'FAIL'}`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- frozen model / T4 length: `{MODEL_ID} / {TOOL_LENGTH_MM:.6f} mm`",
        f"- B0/C0 operator start: `X{start_xyz[0]:.9f} Y{start_xyz[1]:.9f} Z{start_xyz[2]:.9f}` mm",
        f"- frozen Attempt-4 row-9 center seed: `X{center[0]:.9f} Y{center[1]:.9f} Z{center[2]:.9f}` mm",
        f"- seeded top-clear radius: `{reach.TOP_CLEAR_RADIUS:.6f} mm`",
        f"- sampled grid/path points: `{len(samples)}` over `92` recovery poses",
        f"- center / path-model / handoff reserves: `{CENTER_ALLOWANCE_MM:.3f} / {PATH_MODEL_ALLOWANCE_MM:.3f} / {HANDOFF_ENVELOPE_MM:.3f} mm`",
        f"- required margin after `{reserve:.3f} mm` reserve: `{REQUIRED_REMAINING_MARGIN_MM:.3f} mm`",
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
            "The exact replay starts from the verified Attempt-4 row-9 B0/C0 top-clear command. The full 0.050 mm absolute handoff envelope is additive to the 2 mm center and 3 mm path/model reserves. The separate post-load hold guard permits only 0.001 mm change before motion.",
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
    parser.add_argument("--start-x", type=float, default=float(START_XYZ[0]))
    parser.add_argument("--start-y", type=float, default=float(START_XYZ[1]))
    parser.add_argument("--start-z", type=float, default=float(START_XYZ[2]))
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--details", type=Path, default=DEFAULT_DETAILS)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        start_xyz = np.array([args.start_x, args.start_y, args.start_z])
        center, samples, limits = replay(start_xyz)
        summary = summarize(samples, limits)
        if args.self_test:
            assert np.allclose(
                center,
                [2500.940456, 696.558194, -302.576056],
                atol=1e-9,
            )
            assert summary["passed"]
            assert [pose.slot for pose in recovery_grid()] == list(range(10, 102))
            print("T4 new-location Attempt-5 continuation reachability self-test: PASS")
            return 0
        reach.write_details(args.details, samples)
        write_report(args.report, args.details, start_xyz, center, samples, summary)
    except (AssertionError, OSError, ValueError, ReachabilityError) as exc:
        print(f"T4 new-location reachability: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"T4 new-location reachability: {'PASS' if summary['passed'] else 'FAIL'}")
    print(f"report: {args.report}")
    print(f"details: {args.details}")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
