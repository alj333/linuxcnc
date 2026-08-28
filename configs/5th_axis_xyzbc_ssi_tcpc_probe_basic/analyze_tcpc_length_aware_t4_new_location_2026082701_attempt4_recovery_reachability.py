#!/usr/bin/env python3
"""Replay the exact T4 location-2 Attempt-4 grid against frozen q=0 kinematics.

This module is offline-only. It reads configuration and G-code files, writes
CSV/Markdown evidence, and has no LinuxCNC or HAL runtime interface.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
from pathlib import Path
import re
import sys

import numpy as np

import analyze_tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery_reachability as attempt3
import analyze_tcpc_relocated_sphere_reachability as reach


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
REFERENCE_RUNNER = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery.ngc"
RUNNER = REPO_ROOT / "nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt4_recovery.ngc"

DEFAULT_REPORT = HERE / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT4_RECOVERY_REACHABILITY_REPORT.md"
DEFAULT_DETAILS = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery-reachability.csv"

CAMPAIGN = 2026082701
MODE = 38
ATTEMPT = 4
MODEL_ID = attempt3.MODEL_ID
TOOL_LENGTH_MM = attempt3.TOOL_LENGTH_MM
START_XYZ = attempt3.START_XYZ.copy()
CENTER_ALLOWANCE_MM = attempt3.CENTER_ALLOWANCE_MM
PATH_MODEL_ALLOWANCE_MM = attempt3.PATH_MODEL_ALLOWANCE_MM
REQUIRED_REMAINING_MARGIN_MM = attempt3.REQUIRED_REMAINING_MARGIN_MM

REFERENCE_RUNNER_SHA256 = "bf76ab273c76a32046e6f2066f6b865ea8e0a448266cff0399186e262c5a061a"
RUNNER_SHA256 = "66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b"
EXPECTED_SHA256 = dict(attempt3.EXPECTED_SHA256)
EXPECTED_SHA256[REFERENCE_RUNNER] = REFERENCE_RUNNER_SHA256
EXPECTED_SHA256[RUNNER] = RUNNER_SHA256

PAREN_COMMENT_RE = re.compile(r"\([^()]*\)")
MODE_ASSIGN_RE = re.compile(r"^#711\s*=\s*(?:37|38)\.0$")
ATTEMPT_ASSIGN_RE = re.compile(r"^#727\s*=\s*(?:3|4)\.0$")
MODE_LITERAL_RE = re.compile(r"(?<=#711 - )(?:37|38)\.0")
OUTPUT_PATH_RE = re.compile(
    r"^\(LOGAPPEND,.*/tcpc-length-aware-t4-new-location-2026082701-"
    r"attempt(?P<attempt>[34])-recovery-(?P<kind>"
    r"gap-trace|contact-trace|results|state|model-state|closures)\.csv\)$"
)
DWELL_LINE = "G4 P10.0"
IGNORE_ASSERT_START = (
    "o<pair_final_ignore_active> if "
    "[#<_hal[tcpc_probe_gate_ignore.out]> GT 0.5]"
)
IGNORE_ASSERT_END = "o<pair_final_ignore_active> endif"


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


def executable_lines(path: Path) -> list[str]:
    """Return canonical executable blocks with all G-code comments removed."""
    lines: list[str] = []
    for raw_line in path.read_text(encoding="ascii").splitlines():
        line = PAREN_COMMENT_RE.sub("", raw_line)
        line = " ".join(line.split())
        if line:
            lines.append(line)
    return lines


def normalize_identity(line: str) -> str:
    if MODE_ASSIGN_RE.fullmatch(line):
        return "#711 = <MODE>"
    if ATTEMPT_ASSIGN_RE.fullmatch(line):
        return "#727 = <ATTEMPT>"
    return MODE_LITERAL_RE.sub("<MODE>", line)


def output_path_kinds(path: Path, attempt: int) -> list[str]:
    kinds: list[str] = []
    for raw_line in path.read_text(encoding="ascii").splitlines():
        match = OUTPUT_PATH_RE.fullmatch(raw_line.strip())
        if match is None:
            continue
        if int(match.group("attempt")) != attempt:
            raise ReachabilityError(
                f"wrong output attempt identity in {path.name}: {raw_line.strip()}"
            )
        kinds.append(match.group("kind"))
    return kinds


def normalized_motion_geometry(path: Path, *, remove_attempt4_guards: bool) -> tuple[list[str], dict[str, object]]:
    lines = executable_lines(path)
    dwell_indices = [index for index, line in enumerate(lines) if line == DWELL_LINE]
    dwell_predecessors = [lines[index - 1] for index in dwell_indices]
    ignore_start_indices = [
        index for index, line in enumerate(lines) if line == IGNORE_ASSERT_START
    ]
    ignore_end_indices = [
        index for index, line in enumerate(lines) if line == IGNORE_ASSERT_END
    ]

    if remove_attempt4_guards:
        if dwell_predecessors.count(
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>"
        ) != 1 or dwell_predecessors.count("G1 X#125 Y#126 Z#127") != 3:
            raise ReachabilityError(
                "Attempt-4 does not have exactly four proven post-retract G4 P10.0 dwells"
            )
        if len(ignore_start_indices) != 1 or len(ignore_end_indices) != 1:
            raise ReachabilityError(
                "Attempt-4 does not have exactly one ignore-active assertion"
            )
        if ignore_end_indices[0] != ignore_start_indices[0] + 1:
            raise ReachabilityError(
                "Attempt-4 ignore-active assertion is not one canonical executable block"
            )
    elif dwell_indices or ignore_start_indices or ignore_end_indices:
        raise ReachabilityError(
            "Attempt-3 unexpectedly contains an Attempt-4 dwell or ignore assertion"
        )

    normalized = []
    for line in lines:
        if remove_attempt4_guards and line in {
            DWELL_LINE,
            IGNORE_ASSERT_START,
            IGNORE_ASSERT_END,
        }:
            continue
        normalized.append(normalize_identity(line))
    metadata = {
        "executable_lines": len(lines),
        "dwell_count": len(dwell_indices),
        "dwell_predecessors": dwell_predecessors,
        "ignore_assertion_count": len(ignore_start_indices),
    }
    return normalized, metadata


def geometry_equivalence_proof() -> dict[str, object]:
    expected_kinds = sorted(
        ["gap-trace", "contact-trace", "results", "state", "model-state", "closures"]
    )
    if sorted(output_path_kinds(REFERENCE_RUNNER, 3)) != expected_kinds:
        raise ReachabilityError("Attempt-3 does not contain the exact six reference outputs")
    if sorted(output_path_kinds(RUNNER, 4)) != expected_kinds:
        raise ReachabilityError("Attempt-4 does not contain the exact six fresh outputs")

    reference, reference_meta = normalized_motion_geometry(
        REFERENCE_RUNNER, remove_attempt4_guards=False
    )
    candidate, candidate_meta = normalized_motion_geometry(
        RUNNER, remove_attempt4_guards=True
    )
    if reference != candidate:
        delta = "\n".join(
            difflib.unified_diff(
                reference,
                candidate,
                fromfile=REFERENCE_RUNNER.name,
                tofile=RUNNER.name,
                lineterm="",
            )
        )
        raise ReachabilityError(
            "normalized Attempt-4 motion geometry differs from Attempt-3:\n"
            + "\n".join(delta.splitlines()[:80])
        )
    normalized_sha = hashlib.sha256(
        ("\n".join(reference) + "\n").encode("ascii")
    ).hexdigest()
    return {
        "reference_runner_sha256": sha256(REFERENCE_RUNNER),
        "runner_sha256": sha256(RUNNER),
        "normalized_sha256": normalized_sha,
        "normalized_lines": len(reference),
        "reference_executable_lines": reference_meta["executable_lines"],
        "candidate_executable_lines": candidate_meta["executable_lines"],
        "dwell_count": candidate_meta["dwell_count"],
        "ignore_assertion_count": candidate_meta["ignore_assertion_count"],
        "output_path_count": 6,
    }


def recovery_grid() -> list[reach.Pose]:
    return attempt3.recovery_grid()


def replay(start_xyz: np.ndarray) -> tuple[np.ndarray, list[reach.Sample], reach.Limits]:
    if start_xyz.shape != (3,) or not np.all(np.isfinite(start_xyz)):
        raise ReachabilityError("start XYZ must contain three finite values")
    validate_hashes()
    geometry_equivalence_proof()
    pins = attempt3.merged_model_pins()
    limits = reach.parse_limits(attempt3.VALIDATION_INI)
    poses = recovery_grid()
    if len(poses) != 92:
        raise ReachabilityError("T4 Attempt-4 recovery grid is not 92 rows")
    center = attempt3.estimated_center(start_xyz)
    samples = reach.replay(
        center,
        pins,
        limits,
        tool=4,
        length=TOOL_LENGTH_MM,
        effective_radius=reach.T4_EFFECTIVE_RADIUS,
        poses=poses,
    )
    if not samples:
        raise ReachabilityError("reachability replay produced no samples")
    return center, samples, limits


def summarize(samples: list[reach.Sample], limits: reach.Limits) -> dict[str, object]:
    return attempt3.summarize(samples, limits)


def write_report(
    path: Path,
    details: Path,
    start_xyz: np.ndarray,
    center: np.ndarray,
    samples: list[reach.Sample],
    summary: dict[str, object],
    proof: dict[str, object],
) -> None:
    prior_identity = (attempt3.CAMPAIGN, attempt3.MODE, attempt3.ATTEMPT)
    try:
        attempt3.CAMPAIGN = CAMPAIGN
        attempt3.MODE = MODE
        attempt3.ATTEMPT = ATTEMPT
        attempt3.write_report(path, details, start_xyz, center, samples, summary)
    finally:
        attempt3.CAMPAIGN, attempt3.MODE, attempt3.ATTEMPT = prior_identity

    geometry_lines = [
        "## Frozen geometry equivalence",
        "",
        "Status: `PASS`",
        "",
        f"- Attempt-4 runner SHA-256: `{proof['runner_sha256']}`",
        f"- Attempt-3 reference SHA-256: `{proof['reference_runner_sha256']}`",
        f"- normalized executable geometry SHA-256: `{proof['normalized_sha256']}`",
        f"- normalized executable lines compared: `{proof['normalized_lines']}`",
        f"- fresh output paths checked: `{proof['output_path_count']}`",
        f"- post-retract `G4 P10.0` lines excluded from geometry: `{proof['dwell_count']}`",
        f"- pre-G38 ignore-active assertions excluded from geometry: `{proof['ignore_assertion_count']}`",
        "",
        "All G-code comments are removed symmetrically because they are non-executable. The six output paths are checked separately. After normalizing only the mode/attempt identity and excluding the four proven post-retract dwells plus the single ignore-active assertion, Attempt 4 is byte-identical to the frozen Attempt-3 executable geometry.",
        "",
    ]
    with path.open("a", encoding="ascii") as stream:
        stream.write("\n" + "\n".join(geometry_lines))


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
        proof = geometry_equivalence_proof()
        if args.self_test:
            assert np.allclose(
                center,
                [2501.9412544845527, 696.8993474512587, -303.7113862715618],
                atol=1e-9,
            )
            assert summary["passed"]
            assert [pose.slot for pose in recovery_grid()] == [
                *range(1, 10), 17, *range(20, 102)
            ]
            assert proof["dwell_count"] == 4
            assert proof["ignore_assertion_count"] == 1
            print("T4 new-location Attempt-4 recovery reachability self-test: PASS")
            print(f"normalized geometry SHA-256: {proof['normalized_sha256']}")
            return 0
        reach.write_details(args.details, samples)
        write_report(args.report, args.details, start_xyz, center, samples, summary, proof)
    except (AssertionError, OSError, ValueError, ReachabilityError) as exc:
        print(f"T4 new-location Attempt-4 reachability: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"T4 new-location Attempt-4 reachability: "
        f"{'PASS' if summary['passed'] else 'FAIL'}"
    )
    print(f"samples: {len(samples)}")
    print(f"minimum nominal margin: {summary['minimum_nominal']:.6f} mm")
    print(f"minimum remaining margin: {summary['remaining']:.6f} mm")
    print(f"runner SHA-256: {proof['runner_sha256']}")
    print(f"normalized geometry SHA-256: {proof['normalized_sha256']}")
    print(f"report: {args.report}")
    print(f"details: {args.details}")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
