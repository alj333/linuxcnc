#!/usr/bin/env python3
"""Preflight and validate the campaign-04 T4 loaded-candidate test.

This tool has no T3 data input. It performs offline file, fit-identity, G-code,
pose-grid, configured-limit, and result-contract checks only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import analyze_tcpc_relocated_sphere_reachability as reach
import fit_tcpc_relocated_sphere_t4 as fitter


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CAMPAIGN = 2026082404
MODE = 25
ATTEMPT = 1
PREDICTED_RMS_LIMIT_MM = 0.130
PREDICTED_MAX_LIMIT_MM = 0.300
PATTERN_RMS_LIMIT_MM = 0.050
PATTERN_MAX_LIMIT_MM = 0.120

BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
BASE_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini"
CANDIDATE_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate.ini"
OVERLAY = HERE / "tcpc_relocated_sphere_t4_candidate_lambda30.hal"
PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_candidate_verification.ngc"
RESULTS = HERE / "tcpc-relocated-sphere-t4-candidate-verification-results.csv"
STATE = HERE / "tcpc-relocated-sphere-t4-candidate-verification-state.csv"
CLOSURES = HERE / "tcpc-relocated-sphere-t4-candidate-verification-closures.csv"

DEFAULT_PREFLIGHT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_CANDIDATE_PREFLIGHT_REPORT.md"
DEFAULT_RESULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_CANDIDATE_REPORT.md"
DEFAULT_REACH_DETAILS = HERE / "tcpc-relocated-sphere-t4-candidate-reachability.csv"

EXPECTED_BASE_HAL_SHA256 = "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778"
EXPECTED_BASE_INI_SHA256 = "afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519"
EXPECTED_OVERLAY_SHA256 = "7df9c650d5571172f62132a586256ce6a499773827de540a3bd88bdbdc2a8df1"
EXPECTED_CANDIDATE_INI_SHA256 = "4340fab84d965e632e34a1c349b94317b9d8842e5c3e94831b85317262184491"
EXPECTED_PROGRAM_SHA256 = "5803746d4973cd3ea6322d9f128be016a706b2b136224806eac1b1e5566df522"

EXPECTED_HEADER_SHA256 = {
    RESULTS: "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    STATE: "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    CLOSURES: "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
}

INI_PREFIX = (
    "# DIAGNOSTIC ONLY: campaign-04 T4 lambda-30 candidate verification.\n"
    "# Derived from the task-capture INI. The final HALFILE applies only the 27\n"
    "# frozen surface-tuning totals; it does not alter the production/base files.\n"
)
BASE_XHC_LINE = "HALFILE = ../5th_axis_xyzbc_ssi_probe_basic/xhc.hal\n"
OVERLAY_INI_LINE = "HALFILE = tcpc_relocated_sphere_t4_candidate_lambda30.hal\n"

SET_RE = re.compile(r"^setp\s+(headheadkins\.[^\s]+)\s+([-+0-9.eE]+)$")


class CandidateError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise CandidateError(f"SHA-256 changed for {path}: {actual}, expected {expected}")


def recomputed_candidate_totals() -> dict[str, float]:
    # The fitter hashes and reads only the immutable T4 attempt-1 inputs.
    fitter.validate_hashes()
    observations, _ = fitter.validate_and_load()
    model = fitter.fit_ridge(fitter.unique_poses(observations))
    if model.terms != fitter.PRIMARY_TERMS or model.ridge_lambda != 30.0:
        raise CandidateError("frozen candidate family or lambda changed")
    base = fitter.parse_hal_values()
    totals: dict[str, float] = {}
    for term, delta in zip(fitter.PRIMARY_TERMS, model.correction_deltas):
        stem = fitter.PIN_STEMS[term]
        for axis_name, adjustment in zip(fitter.AXES, delta):
            pin = f"{stem}.{axis_name}"
            totals[pin] = base[pin] + float(adjustment)
    if len(totals) != 27:
        raise CandidateError(f"candidate recomputation produced {len(totals)} pins, expected 27")
    return totals


def validate_overlay() -> dict[str, float]:
    require_hash(BASE_HAL, EXPECTED_BASE_HAL_SHA256)
    require_hash(OVERLAY, EXPECTED_OVERLAY_SHA256)
    parsed: dict[str, float] = {}
    command_count = 0
    for line_number, raw_line in enumerate(OVERLAY.read_text(encoding="ascii").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = SET_RE.fullmatch(line)
        if not match:
            raise CandidateError(f"overlay line {line_number} is not one numeric setp command")
        pin, text_value = match.groups()
        value = float(text_value)
        if not math.isfinite(value) or pin in parsed:
            raise CandidateError(f"invalid or duplicate overlay pin {pin}")
        parsed[pin] = value
        command_count += 1
    expected = recomputed_candidate_totals()
    if command_count != 27 or set(parsed) != set(expected):
        raise CandidateError("overlay must contain exactly the 27 selected candidate pins")
    for pin, value in expected.items():
        if abs(parsed[pin] - value) > 5e-13:
            raise CandidateError(
                f"overlay {pin}={parsed[pin]:+.15f}, recomputed {value:+.15f}"
            )
    return parsed


def validate_candidate_ini() -> None:
    require_hash(BASE_INI, EXPECTED_BASE_INI_SHA256)
    require_hash(CANDIDATE_INI, EXPECTED_CANDIDATE_INI_SHA256)
    base = BASE_INI.read_text(encoding="ascii")
    if base.count(BASE_XHC_LINE) != 1:
        raise CandidateError("baseline INI XHC HALFILE identity changed")
    derived = INI_PREFIX + base.replace(
        BASE_XHC_LINE, BASE_XHC_LINE + OVERLAY_INI_LINE, 1
    )
    actual = CANDIDATE_INI.read_text(encoding="ascii")
    if actual != derived:
        raise CandidateError("candidate INI is not the exact baseline-plus-overlay derivation")

    in_hal = False
    halfiles: list[str] = []
    for raw_line in actual.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_hal = line == "[HAL]"
        elif in_hal and line.startswith("HALFILE"):
            halfiles.append(line)
    if not halfiles or halfiles[-1] != OVERLAY_INI_LINE.strip():
        raise CandidateError("candidate overlay is not the final HALFILE")
    if halfiles.count(OVERLAY_INI_LINE.strip()) != 1:
        raise CandidateError("candidate overlay HALFILE must occur exactly once")


def subroutine_text(text: str, name: str) -> str:
    match = re.search(
        rf"^o<{re.escape(name)}> sub\s*$([\s\S]*?)^o<{re.escape(name)}> endsub\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        raise CandidateError(f"candidate program is missing subroutine {name}")
    return match.group(1)


def parsed_program_grid(text: str) -> list[reach.Pose]:
    b0_sub = subroutine_text(text, "tcpc_primary_b0_sweep")
    b0_c = [
        float(value)
        for value in re.findall(
            r"^\s*o<tcpc_measure_pose> call \[0\.0\] \[([-+0-9.]+)\]",
            b0_sub,
            re.MULTILINE,
        )
    ]
    low_sub = subroutine_text(text, "tcpc_primary_low_tilt_block")
    low_c = [
        float(value)
        for value in re.findall(
            r"^\s*o<tcpc_measure_pose> call \[#<block_b>\] \[([-+0-9.]+)\]",
            low_sub,
            re.MULTILINE,
        )
    ]
    tilt_sub = subroutine_text(text, "tcpc_primary_tilt_block")
    tilt_c = [
        float(value)
        for value in re.findall(
            r"^\s*o<tcpc_measure_pose> call \[#<block_b>\] \[([-+0-9.]+)\]",
            tilt_sub,
            re.MULTILINE,
        )
    ]
    if b0_c != [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 0.0]:
        raise CandidateError(f"candidate B0 sweep changed: {b0_c}")
    if low_c != [float(value) for value in reach.LOW_TILT_C]:
        raise CandidateError(f"candidate low-B sweep changed: {low_c}")
    if tilt_c != [float(value) for value in reach.QUADRANT_C]:
        raise CandidateError(f"candidate high-B sweep changed: {tilt_c}")

    body = re.search(
        r"^o<run_relocated_t4_primary> if \[ABS\[#711 - 25\.0\] LT 0\.1\]\s*$"
        r"([\s\S]*?)^o<run_relocated_t4_primary> endif\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not body:
        raise CandidateError("candidate mode-25 body is missing")
    tokens = re.findall(
        r"^\s*o<tcpc_primary_b0_sweep> call \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_primary_low_tilt_block> call \[([-+0-9.]+)\] \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_primary_tilt_block> call \[([-+0-9.]+)\] \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_measure_pose> call \[0\.0\] \[0\.0\]",
        body.group(1),
        flags=re.MULTILINE,
    )
    poses: list[reach.Pose] = []
    slot = 0
    for b0_block, low_b, low_block, tilt_b, tilt_block in tokens:
        if b0_block:
            values = [(0.0, c) for c in b0_c]
        elif low_b:
            if abs(float(low_b) - float(low_block)) > 1e-12:
                raise CandidateError("candidate low-B block ID differs from B")
            values = [(float(low_b), c) for c in low_c]
        elif tilt_b:
            if abs(float(tilt_b) - float(tilt_block)) > 1e-12:
                raise CandidateError("candidate high-B block ID differs from B")
            values = [(float(tilt_b), c) for c in tilt_c]
        else:
            values = [(0.0, 0.0)]
        for b_deg, c_deg in values:
            slot += 1
            poses.append(reach.Pose(slot, b_deg, c_deg, "candidate"))
    expected = reach.grid()
    if [(p.b_deg, p.c_deg) for p in poses] != [(p.b_deg, p.c_deg) for p in expected]:
        raise CandidateError("candidate program pose order differs from the frozen 101-pose grid")
    return poses


def validate_pin_guard(text: str, expected: dict[str, float]) -> None:
    guard = subroutine_text(text, "tcpc_candidate_pin_guard")
    matches = re.findall(
        r"if \[ABS\[#<_hal\[([^\]]+)\]> ([+-]) ([0-9.]+)\] GT 0\.000000001\]",
        guard,
    )
    guarded: dict[str, float] = {}
    for pin, operator, magnitude_text in matches:
        magnitude = float(magnitude_text)
        target = -magnitude if operator == "+" else magnitude
        if pin in guarded:
            raise CandidateError(f"duplicate G-code candidate guard for {pin}")
        guarded[pin] = target
    if len(guarded) != 27 or set(guarded) != set(expected):
        raise CandidateError("G-code does not guard exactly the 27 candidate pins")
    for pin, value in expected.items():
        if abs(guarded[pin] - value) > 5e-13:
            raise CandidateError(f"G-code candidate guard value differs for {pin}")

    calls = list(
        re.finditer(r"^\s*o<tcpc_candidate_pin_guard> call\s*$", text, re.MULTILINE)
    )
    if len(calls) != 5:
        raise CandidateError(f"expected five static candidate-guard call sites, got {len(calls)}")
    first_m0 = re.search(r"^M0\s*$", text, re.MULTILINE)
    if not first_m0 or not any(call.start() < first_m0.start() for call in calls):
        raise CandidateError("candidate pin guard is not called before the initial M0")
    live = subroutine_text(text, "tcpc_pair_live_guard")
    if "o<tcpc_candidate_pin_guard> call" not in live:
        raise CandidateError("every live guard must include the candidate pin guard")
    measure = subroutine_text(text, "tcpc_measure_pose")
    first_motion = re.search(r"^\s*G1\b", measure, re.MULTILINE)
    direct_guard = measure.find("o<tcpc_candidate_pin_guard> call")
    if direct_guard < 0 or (first_motion and direct_guard > first_motion.start()):
        raise CandidateError("per-pose candidate guard is not before positioning motion")
    logging = measure.find("(LOG,1.0")
    accepted_guard = measure.rfind("o<tcpc_candidate_pin_guard> call", 0, logging)
    if logging < 0 or accepted_guard < 0:
        raise CandidateError("accepted-pose logging is not preceded by a candidate guard")


def validate_program(expected_pins: dict[str, float]) -> tuple[list[reach.Pose], str]:
    require_hash(PROGRAM, EXPECTED_PROGRAM_SHA256)
    text = PROGRAM.read_text(encoding="ascii")
    required = (
        "#707 = 101.0",
        "#711 = 25.0",
        "#715 = 2026082404.0",
        "#716 = 2.0",
        "#727 = 1.0",
        "#717 = 0.154742",
        "#3032 = #717",
        "o<exact_t4_tool_required> if [ABS[#500 - 4.0] GT 0.1]",
        "#516 = 229.407000",
        "#502 = #3032",
        "o<pair_calibration_live> if [ABS[#502 - #717] GT 0.0005]",
        "tcpc-relocated-sphere-t4-candidate-verification-results.csv",
        "tcpc-relocated-sphere-t4-candidate-verification-state.csv",
        "tcpc-relocated-sphere-t4-candidate-verification-closures.csv",
        "#539 = -1.0",
        "o<negative_b_upper_u> if [#520 LT -0.001]",
        "#122 = [-#539 * #533 * #511]",
        "G1 Z#<safe_z>",
    )
    for snippet in required:
        if snippet not in text:
            raise CandidateError(f"candidate program is missing {snippet!r}")
    forbidden = (
        "tcpc-relocated-sphere-t4-primary-results.csv",
        "tcpc-relocated-sphere-t4-primary-state.csv",
        "tcpc-relocated-sphere-t4-primary-closures.csv",
        "tcpc-relocated-sphere-t3-verification-results.csv",
        "G4 P20",
    )
    for snippet in forbidden:
        if snippet in text:
            raise CandidateError(f"candidate program contains forbidden {snippet!r}")
    if re.search(r"^\s*(?:setp|sets|halcmd)\b", text, re.MULTILINE | re.IGNORECASE):
        raise CandidateError("candidate G-code contains a HAL/coefficient write command")
    if len(re.findall(r"^M0\s*$", text, re.MULTILINE)) != 1:
        raise CandidateError("candidate program must contain exactly one initial M0")
    if re.search(r"^M1\s*$", text, re.MULTILINE):
        raise CandidateError("candidate program contains an intermediate optional hold")
    validate_pin_guard(text, expected_pins)
    return parsed_program_grid(text), sha256(PROGRAM)


def run_rs274_preview() -> None:
    command = [str(REPO_ROOT / "bin/rs274"), "-g", str(PROGRAM)]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-12:])
        raise CandidateError(f"in-tree rs274 -g failed ({completed.returncode}):\n{tail}")


def validate_header_only_files() -> None:
    expected_fields = {
        RESULTS: anchor.RESULT_FIELDS,
        STATE: anchor.STATE_FIELDS,
        CLOSURES: campaign.CLOSURE_FIELDS,
    }
    for path, fields in expected_fields.items():
        require_hash(path, EXPECTED_HEADER_SHA256[path])
        with path.open(newline="", encoding="ascii") as stream:
            rows = list(csv.reader(stream))
        if rows != [list(fields)]:
            raise CandidateError(f"candidate output is not an exact header-only file: {path}")


def candidate_run_spec() -> campaign.RunSpec:
    return campaign.RunSpec(
        "T4 loaded-candidate verification",
        4,
        MODE,
        reach.T4_TOOL_LENGTH,
        anchor.CAL_OFFSET,
        anchor.EFFECTIVE_RADIUS,
        RESULTS,
        STATE,
        CLOSURES,
        campaign.expected_rows(reach.grid(), campaign.T4_RANGES),
        campaign.T4_CLOSURES,
    )


def reachability(
    overlay_pins: dict[str, float], details_path: Path
) -> tuple[np.ndarray, int, float, float, float]:
    anchor.validate_program_hash()
    result_rows = anchor.read_rows(anchor.DEFAULT_RESULTS, anchor.RESULT_FIELDS)
    state_rows = anchor.read_rows(anchor.DEFAULT_STATE, anchor.STATE_FIELDS)
    anchor_attempt, center_tuple = anchor.validate(result_rows, state_rows)
    center = np.array(center_tuple)
    pins = reach.parse_hal(BASE_HAL)
    pins.update(overlay_pins)
    limits = reach.parse_limits(CANDIDATE_INI)
    samples = reach.replay(
        center,
        pins,
        limits,
        tool=4,
        length=reach.T4_TOOL_LENGTH,
        effective_radius=reach.T4_EFFECTIVE_RADIUS,
        poses=reach.grid(),
    )
    reach.write_details(details_path, samples)
    worst_linear = min(
        min(float(np.min(sample.joint_margins)), float(np.min(sample.axis_margins)))
        for sample in samples
    )
    remaining = worst_linear - reach.CENTER_ERROR_ALLOWANCE - reach.PATH_MODEL_ALLOWANCE
    b_margin = min(
        min(pose.b_deg - limits.b_limits[0], limits.b_limits[1] - pose.b_deg)
        for pose in reach.grid()
    )
    c_margin = min(
        min(pose.c_deg - limits.c_limits[0], limits.c_limits[1] - pose.c_deg)
        for pose in reach.grid()
    )
    if remaining < reach.REQUIRED_REMAINING_LINEAR_MARGIN or b_margin < 5.0 or c_margin < 5.0:
        raise CandidateError(
            f"candidate reachability failed: remaining={remaining:.6f}, B={b_margin:.3f}, C={c_margin:.3f}"
        )
    return center, anchor_attempt, len(samples), worst_linear, remaining


def markdown_hash_row(path: Path) -> str:
    return f"| `{path.name}` | `{sha256(path)}` |"


def write_preflight_report(
    path: Path,
    details: Path,
    center: np.ndarray,
    anchor_attempt: int,
    sample_count: int,
    worst_linear: float,
    remaining: float,
) -> None:
    lines = [
        "# T4 Loaded-Candidate Verification Preflight",
        "",
        "Status: `PASS` (offline preparation only; nothing was loaded and no machine action was taken).",
        "",
        "## Frozen Stage",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        "- tool state required by the runner: `T4`, `G43 H4`, `229.407000 mm`, `#3032=0.154742`",
        "- accepted rows / closures: `101 / 28`",
        "- holds: one initial `M0`; no intermediate holds",
        "- overlay: exactly 27 absolute totals for the frozen nine-term lambda-30 fit",
        "- candidate pins are read-guarded before the initial hold, through every live guard, before per-pose motion, and immediately before accepted logging",
        "- G-code coefficient writes: none",
        "",
        "## Offline Checks",
        "",
        "- base HAL unchanged and hash-locked: `PASS`",
        "- candidate INI is the exact task-capture INI plus one final HALFILE: `PASS`",
        "- overlay matches an independent recomputation from immutable T4 attempt 1: `PASS`",
        "- in-tree `bin/rs274 -g` preview parse: `PASS`",
        "- exact 101-pose order and positive/negative-B pairing: `PASS`",
        f"- anchor attempt / center: `{anchor_attempt}` / `X{center[0]:.6f} Y{center[1]:.6f} Z{center[2]:.6f}`",
        f"- candidate-geometry reachability samples: `{sample_count}`",
        f"- worst configured linear margin: `{worst_linear:.6f} mm`",
        f"- remaining margin after 2 mm center and 3 mm path allowances: `{remaining:.6f} mm` (`PASS`)",
        "",
        "## Frozen Files",
        "",
        "| file | SHA-256 |",
        "| --- | --- |",
    ]
    for item in (BASE_HAL, BASE_INI, OVERLAY, CANDIDATE_INI, PROGRAM, RESULTS, STATE, CLOSURES):
        lines.append(markdown_hash_row(item))
    lines.extend(
        [
            "",
            "## T4 Gates",
            "",
            "A completed mode-25 run is accepted only if its exact schema, pose, tool/TLO, contact-quality, state, endpoint, and all 28 closure contracts pass, and:",
            "",
            "1. Centered RMS and maximum each improve over immutable mode-23 attempt 1 by both 10% and 0.010/0.020 mm respectively.",
            "2. Centered RMS improves by at least 10% separately for the positive- and negative-B high-tilt groups (`|B|>=30`).",
            "3. B0 centered RMS does not worsen by more than 0.010 mm.",
            "4. No row's centered residual norm worsens by more than 0.075 mm.",
            "5. Actual raw-row centered RMS / max are at most 0.130 / 0.300 mm (offline prediction: 0.099990 / 0.237606 mm).",
            "6. Against the frozen offline predicted centered residual vectors, pattern-difference RMS / max are at most 0.050 / 0.120 mm.",
            "",
            "These gates test implementation and sign on the same measured grid. They do not authorize extrapolation to omitted C sectors, a general live correction, or a production HAL/INI change.",
            "",
            "## Mandatory Rollback",
            "",
            "T3 must not run under this candidate configuration. After the T4 test, close LinuxCNC and clean-restart the baseline `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini`; verify the base HAL SHA-256 is `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` before any current-calibration T3 holdout run.",
            "",
            f"Detailed configured-limit replay: `{details.name}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")


def centered_metric(values: np.ndarray) -> tuple[float, float]:
    residuals = values - np.mean(values, axis=0)
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms**2))), float(np.max(norms))


def evaluate_result_gates(
    run: campaign.ValidatedRun,
) -> tuple[list[tuple[str, bool, str]], np.ndarray, np.ndarray]:
    observations, _ = fitter.validate_and_load()
    baseline = np.vstack([item.center for item in observations])
    candidate_centers = run.centers
    b_values = np.array([item.b_deg for item in observations])
    if baseline.shape != candidate_centers.shape:
        raise CandidateError("candidate and immutable baseline row shapes differ")

    base_rms, base_max = centered_metric(baseline)
    cand_rms, cand_max = centered_metric(candidate_centers)
    model = fitter.fit_ridge(fitter.unique_poses(observations))
    predicted_centers = fitter.corrected_centers(model, observations)
    predicted_residuals = predicted_centers - np.mean(predicted_centers, axis=0)
    candidate_residuals = candidate_centers - np.mean(candidate_centers, axis=0)
    pattern_delta = candidate_residuals - predicted_residuals
    pattern_norms = np.linalg.norm(pattern_delta, axis=1)
    pattern_rms = float(math.sqrt(np.mean(pattern_norms**2)))
    pattern_max = float(np.max(pattern_norms))
    masks = {
        "positive high-B RMS": b_values >= 30.0,
        "negative high-B RMS": b_values <= -30.0,
        "B0 RMS": np.abs(b_values) < 0.001,
    }
    group_metrics = {
        name: (centered_metric(baseline[mask]), centered_metric(candidate_centers[mask]))
        for name, mask in masks.items()
    }
    base_residual_norm = np.linalg.norm(baseline - np.mean(baseline, axis=0), axis=1)
    candidate_residual_norm = np.linalg.norm(
        candidate_centers - np.mean(candidate_centers, axis=0), axis=1
    )
    maximum_worsening = float(np.max(candidate_residual_norm - base_residual_norm))

    rms_limit = min(base_rms * 0.90, base_rms - 0.010)
    max_limit = min(base_max * 0.90, base_max - 0.020)
    positive_base = group_metrics["positive high-B RMS"][0][0]
    positive_candidate = group_metrics["positive high-B RMS"][1][0]
    negative_base = group_metrics["negative high-B RMS"][0][0]
    negative_candidate = group_metrics["negative high-B RMS"][1][0]
    b0_base = group_metrics["B0 RMS"][0][0]
    b0_candidate = group_metrics["B0 RMS"][1][0]
    gates = [
        ("full centered RMS", cand_rms <= rms_limit, f"{cand_rms:.6f} <= {rms_limit:.6f} mm"),
        ("full centered maximum", cand_max <= max_limit, f"{cand_max:.6f} <= {max_limit:.6f} mm"),
        (
            "positive high-B RMS",
            positive_candidate <= positive_base * 0.90,
            f"{positive_candidate:.6f} <= {positive_base * 0.90:.6f} mm",
        ),
        (
            "negative high-B RMS",
            negative_candidate <= negative_base * 0.90,
            f"{negative_candidate:.6f} <= {negative_base * 0.90:.6f} mm",
        ),
        ("B0 RMS", b0_candidate <= b0_base + 0.010, f"{b0_candidate:.6f} <= {b0_base + 0.010:.6f} mm"),
        ("maximum row worsening", maximum_worsening <= 0.075, f"{maximum_worsening:.6f} <= 0.075000 mm"),
        (
            "prediction RMS ceiling",
            cand_rms <= PREDICTED_RMS_LIMIT_MM,
            f"{cand_rms:.6f} <= {PREDICTED_RMS_LIMIT_MM:.6f} mm",
        ),
        (
            "prediction maximum ceiling",
            cand_max <= PREDICTED_MAX_LIMIT_MM,
            f"{cand_max:.6f} <= {PREDICTED_MAX_LIMIT_MM:.6f} mm",
        ),
        (
            "predicted-pattern RMS",
            pattern_rms <= PATTERN_RMS_LIMIT_MM,
            f"{pattern_rms:.6f} <= {PATTERN_RMS_LIMIT_MM:.6f} mm",
        ),
        (
            "predicted-pattern maximum",
            pattern_max <= PATTERN_MAX_LIMIT_MM,
            f"{pattern_max:.6f} <= {PATTERN_MAX_LIMIT_MM:.6f} mm",
        ),
    ]
    return gates, baseline, candidate_centers


def write_result_report(
    path: Path,
    run: campaign.ValidatedRun,
    gates: Sequence[tuple[str, bool, str]],
    baseline: np.ndarray,
    candidate_centers: np.ndarray,
) -> bool:
    base_rms, base_max = centered_metric(baseline)
    candidate_rms, candidate_max = centered_metric(candidate_centers)
    passed = all(gate[1] for gate in gates)
    lines = [
        "# T4 Loaded-Candidate Verification Report",
        "",
        f"Status: `{'PASS' if passed else 'FAIL'}`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {run.attempt}`",
        f"- validated rows / closures: `{len(run.centers)} / {len(run.closure_norms)}`",
        f"- worst closure: `{np.max(run.closure_norms):.6f} mm`",
        f"- immutable mode-23 centered RMS / max: `{base_rms:.6f} / {base_max:.6f} mm`",
        f"- mode-25 candidate centered RMS / max: `{candidate_rms:.6f} / {candidate_max:.6f} mm`",
        "",
        "| frozen gate | result | measured contract |",
        "| --- | --- | ---: |",
    ]
    for name, gate_passed, detail in gates:
        lines.append(f"| {name} | `{'PASS' if gate_passed else 'FAIL'}` | `{detail}` |")
    lines.extend(
        [
            "",
            "This is a same-grid implementation/sign test only. It does not authorize unmeasured-C extrapolation, general live use, or any production/base HAL or INI edit.",
            "",
            "T3 must not run with the candidate overlay. Clean-restart the baseline task-capture INI and verify the frozen base-HAL hash before the current-calibration T3 holdout.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")
    return passed


def offline_contract(details: Path) -> tuple[np.ndarray, int, int, float, float]:
    reach.validate_model_constants()
    overlay_pins = validate_overlay()
    validate_candidate_ini()
    poses, _ = validate_program(overlay_pins)
    if len(poses) != 101:
        raise CandidateError("candidate pose parser did not produce exactly 101 poses")
    run_rs274_preview()
    return reachability(overlay_pins, details)


def self_test() -> None:
    pins = validate_overlay()
    validate_candidate_ini()
    poses, digest = validate_program(pins)
    assert len(pins) == 27
    assert len(poses) == 101
    assert len(digest) == 64
    spec = candidate_run_spec()
    assert spec.mode == MODE and len(spec.expected_rows) == 101
    assert len(spec.closure_ranges) == 28
    assert {row.pose.b_deg for row in spec.expected_rows} == {
        -90.0, -60.0, -45.0, -30.0, -15.0, -10.0, -5.0,
        0.0, 5.0, 10.0, 15.0, 30.0, 45.0, 60.0, 90.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="require pristine header-only outputs")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--reach-details", type=Path, default=DEFAULT_REACH_DETAILS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("candidate self-test: PASS")
            return 0
        center, anchor_attempt, sample_count, worst_linear, remaining = offline_contract(
            args.reach_details
        )
        if args.preflight:
            validate_header_only_files()
            report = args.report or DEFAULT_PREFLIGHT_REPORT
            write_preflight_report(
                report,
                args.reach_details,
                center,
                anchor_attempt,
                sample_count,
                worst_linear,
                remaining,
            )
            print("T4 candidate preflight: PASS")
        else:
            report = args.report or DEFAULT_RESULT_REPORT
            run = campaign.validate_run(candidate_run_spec())
            if run.attempt != ATTEMPT:
                raise CandidateError(f"candidate attempt is {run.attempt}, expected frozen {ATTEMPT}")
            gates, baseline, candidate_centers = evaluate_result_gates(run)
            passed = write_result_report(report, run, gates, baseline, candidate_centers)
            print(f"T4 candidate validation: {'PASS' if passed else 'FAIL'}")
            if not passed:
                return 1
        print(f"report: {report}")
        print(f"reachability details: {args.reach_details}")
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, anchor.ValidationError) as exc:
        print(f"T4 candidate validation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
