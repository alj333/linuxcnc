#!/usr/bin/env python3
"""Preflight and validate the campaign-04 T4 R2 loaded-candidate test.

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
import fit_tcpc_relocated_sphere_t4_r2 as fitter


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CAMPAIGN = 2026082404
MODE = 26
ATTEMPT = 1
UNIQUE_RMS_LIMIT_MM = 0.120
UNIQUE_MAX_LIMIT_MM = 0.280
RAW_RMS_LIMIT_MM = 0.120
RAW_MAX_LIMIT_MM = 0.280
PATTERN_RMS_LIMIT_MM = 0.050
PATTERN_MAX_LIMIT_MM = 0.120
MAX_ROW_WORSENING_MM = 0.075
MAX_MODELED_CORRECTION_MM = 0.750
DENSE_STEP_DEG = 0.25
DIAGNOSTIC_B_LIMITS = (-90.0, 90.0)

FROZEN_TERMS = (
    "c_cos",
    "b_sin",
    "b_sin2",
    "bc_sinb_sinc",
    "bc_omcb_sin2c",
    "bc_sinb_cos2c",
    "bmid_base",
    "bmid_cosc",
    "bmid_sinc",
    "bmid_cos2c",
)
FROZEN_LAMBDA = 10.0

BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
BASE_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini"
CANDIDATE_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate_r2.ini"
OVERLAY = HERE / "tcpc_relocated_sphere_t4_candidate_r2.hal"
PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_verification.ngc"
RESULTS = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt1-results.csv"
STATE = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt1-state.csv"
CLOSURES = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt1-closures.csv"
FIT_SCRIPT = HERE / "fit_tcpc_relocated_sphere_t4_r2.py"
FIT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_FIT_R2_REPORT.md"
FIT_RESIDUALS = HERE / "tcpc-relocated-sphere-t4-fit-r2-residuals.csv"
FIT_PINS = HERE / "tcpc-relocated-sphere-t4-fit-r2-pins.csv"
FIT_CHECKPOINT = HERE / "tcpc-relocated-sphere-t4-fit-r2-checkpoint.json"
R1_TEMPLATE = (
    HERE
    / "calibration_runs/20260825_0833_campaign04_t4_candidate_r1_rejected_pre_motion"
    / "tcpc_relocated_sphere_t4_candidate_verification.ngc"
)

DEFAULT_PREFLIGHT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2_PREFLIGHT_REPORT.md"
DEFAULT_RESULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2_REPORT.md"
DEFAULT_REACH_DETAILS = HERE / "tcpc-relocated-sphere-t4-candidate-r2-reachability.csv"

EXPECTED_BASE_HAL_SHA256 = "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778"
EXPECTED_BASE_INI_SHA256 = "afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519"
EXPECTED_OVERLAY_SHA256 = "0bfefdb068bb353282fc41067d5cd7464f76ea6a4f520204f0ab5c914ee1673a"
EXPECTED_CANDIDATE_INI_SHA256 = "1ab3b84611b93fbf10083e21f87b90d19eea5c3c8a8fe66373570a7cace3d77e"
EXPECTED_PROGRAM_SHA256 = "a1358c407399ad3606a5a2a449cc973cd39c6ea705233c1f87fdfc0dcb45b7f4"
EXPECTED_R1_TEMPLATE_SHA256 = "5803746d4973cd3ea6322d9f128be016a706b2b136224806eac1b1e5566df522"
EXPECTED_FIT_SCRIPT_SHA256 = "faae48919e01f5f7cf5a9e8f29da40fc77bdf359d21bec1848bdcdfb979c71bb"
EXPECTED_FIT_REPORT_SHA256 = "c4c625eb44254e60d0f95ce8544713d406743c45810f0d4fb6d5bce6306095b9"
EXPECTED_FIT_RESIDUALS_SHA256 = "8de7e98a4767eba6545ee3e6f3a0688bf56e43427153bea79c08c4787f59ade1"
EXPECTED_FIT_PINS_SHA256 = "d3481e51cd98b6fc4c8ac8484a781b6fe88321ab371b53bc5081248f72c1e2b6"
EXPECTED_FIT_CHECKPOINT_SHA256 = "d3a76e7149e251a1a422bcb54cf3bd0f1629f53178f9c64a3929bd99e7134d33"

EXPECTED_HEADER_SHA256 = {
    RESULTS: "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    STATE: "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    CLOSURES: "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
}

INI_PREFIX = (
    "# DIAGNOSTIC ONLY: campaign-04 T4 R2 loaded-candidate verification.\n"
    "# Derived from the hash-locked task-capture INI. The final HALFILE applies only\n"
    "# the 30 frozen surface-tuning totals; production/base files remain unchanged.\n"
)
BASE_XHC_LINE = "HALFILE = ../5th_axis_xyzbc_ssi_probe_basic/xhc.hal\n"
OVERLAY_INI_LINE = "HALFILE = tcpc_relocated_sphere_t4_candidate_r2.hal\n"

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


def frozen_fit() -> tuple[list[fitter.Observation], fitter.Dataset, fitter.CandidateEvaluation]:
    for path, digest in (
        (FIT_SCRIPT, EXPECTED_FIT_SCRIPT_SHA256),
        (FIT_REPORT, EXPECTED_FIT_REPORT_SHA256),
        (FIT_RESIDUALS, EXPECTED_FIT_RESIDUALS_SHA256),
        (FIT_PINS, EXPECTED_FIT_PINS_SHA256),
        (FIT_CHECKPOINT, EXPECTED_FIT_CHECKPOINT_SHA256),
    ):
        require_hash(path, digest)
    fitter.validate_hashes()
    observations, _ = fitter.validate_and_load()
    data = fitter.build_dataset(observations)
    checkpoint = fitter.load_checkpoint(FIT_CHECKPOINT)
    primary = checkpoint["primary"]
    if not isinstance(primary, dict) or not isinstance(primary.get("refined"), dict):
        raise CandidateError("R2 checkpoint has no frozen refined primary")
    selection = fitter.restore_selection(
        data, np.arange(len(data.poses)), primary["refined"]
    )
    model = selection.winner
    if fitter.term_names(model.term_indices) != FROZEN_TERMS:
        raise CandidateError("frozen candidate family or lambda changed")
    if model.ridge_lambda != FROZEN_LAMBDA:
        raise CandidateError("frozen candidate lambda changed")
    if fitter.max_correction(data, model.fit) > MAX_MODELED_CORRECTION_MM + 1e-12:
        raise CandidateError("R2 measured-grid correction exceeds its frozen bound")
    return observations, data, model


def recomputed_candidate_totals() -> dict[str, float]:
    _, _, model = frozen_fit()
    base = fitter.parse_hal_values()
    deltas = fitter.full_delta_matrix(model.fit)
    totals: dict[str, float] = {}
    for term_index in model.term_indices:
        term = fitter.ADMISSIBLE_TERMS[term_index]
        delta = deltas[term_index]
        stem = fitter.PIN_STEMS[term]
        for axis_name, adjustment in zip(fitter.AXES, delta):
            pin = f"{stem}.{axis_name}"
            totals[pin] = base[pin] + float(adjustment)
    if len(totals) != 30:
        raise CandidateError(f"candidate recomputation produced {len(totals)} pins, expected 30")
    return totals


def validate_fit_pin_audit(expected_totals: dict[str, float]) -> None:
    with FIT_PINS.open(newline="", encoding="ascii") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != fitter.PIN_FIELDS:
            raise CandidateError("R2 pin-audit schema changed")
        rows = list(reader)
    if len(rows) != len(fitter.ADMISSIBLE_TERMS) * len(fitter.AXES):
        raise CandidateError("R2 pin-audit row count changed")
    selected_terms: set[str] = set()
    selected_pins: set[str] = set()
    for row in rows:
        if row["campaign_id"] != str(CAMPAIGN) or row["fit_revision"] != "r2":
            raise CandidateError("R2 pin-audit provenance changed")
        if row["operational_status"] != "offline_not_authorized":
            raise CandidateError("R2 fit pin audit has unexpected operational status")
        selected = row["selected"] == "1"
        if row["selected"] not in ("0", "1"):
            raise CandidateError("R2 pin-audit selected flag is invalid")
        if selected:
            selected_terms.add(row["basis_term"])
            selected_pins.add(row["pin"])
            if row["pin"] not in expected_totals:
                raise CandidateError(f"unexpected selected R2 pin {row['pin']}")
            if abs(float(row["predicted_total_mm"]) - expected_totals[row["pin"]]) > 1e-9:
                raise CandidateError(f"R2 pin-audit total differs for {row['pin']}")
        elif abs(float(row["delta_mm"])) > 5e-10:
            raise CandidateError(f"nonselected R2 pin has a nonzero delta: {row['pin']}")
    if tuple(term for term in fitter.ADMISSIBLE_TERMS if term in selected_terms) != FROZEN_TERMS:
        raise CandidateError("R2 pin-audit selected term family changed")
    if selected_pins != set(expected_totals):
        raise CandidateError("R2 pin-audit and overlay pin sets differ")


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
    validate_fit_pin_audit(expected)
    if command_count != 30 or set(parsed) != set(expected):
        raise CandidateError("overlay must contain exactly the 30 selected candidate pins")
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
        r"^o<run_relocated_t4_primary> if \[ABS\[#711 - 26\.0\] LT 0\.1\]\s*$"
        r"([\s\S]*?)^o<run_relocated_t4_primary> endif\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not body:
        raise CandidateError("candidate mode-26 body is missing")
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
    block_pattern = re.compile(
        r"^\s*o<cand([0-9]{2})> if \[ABS\[#<_hal\[([^\]]+)\]> ([+-]) ([0-9.]+)\] GT 0\.000000001\]\s*$\n"
        r"^\s*\(abort, R2 candidate pin mismatch ([0-9]{2}) ([^)]+)\)\s*$\n"
        r"^\s*o<cand([0-9]{2})> endif\s*$",
        re.MULTILINE,
    )
    matches = list(block_pattern.finditer(guard))
    if block_pattern.sub("", guard).strip():
        raise CandidateError("candidate pin guard contains a malformed or extra statement")
    if len(matches) != 30:
        raise CandidateError(f"candidate pin guard has {len(matches)} complete abort blocks, expected 30")

    guarded: dict[str, float] = {}
    expected_items = list(expected.items())
    for index, match in enumerate(matches, 1):
        block_id, pin, operator, magnitude_text, abort_id, abort_label, end_id = match.groups()
        required_id = f"{index:02d}"
        if block_id != required_id or abort_id != required_id or end_id != required_id:
            raise CandidateError(f"candidate guard block {index} identity is inconsistent")
        expected_pin, _ = expected_items[index - 1]
        expected_label = expected_pin.removeprefix("headheadkins.").replace(".", " ")
        if pin != expected_pin or abort_label != expected_label:
            raise CandidateError(f"candidate guard block {required_id} pin/abort identity differs")
        magnitude = float(magnitude_text)
        target = -magnitude if operator == "+" else magnitude
        if pin in guarded:
            raise CandidateError(f"duplicate G-code candidate guard for {pin}")
        guarded[pin] = target
    if len(guarded) != 30 or set(guarded) != set(expected):
        raise CandidateError("G-code does not guard exactly the 30 candidate pins")
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


def replace_subroutine(text: str, name: str, replacement_text: str) -> str:
    pattern = re.compile(
        rf"^o<{re.escape(name)}> sub\s*$[\s\S]*?^o<{re.escape(name)}> endsub\s*$",
        re.MULTILINE,
    )
    replacement = pattern.search(replacement_text)
    if replacement is None or pattern.search(text) is None:
        raise CandidateError(f"cannot compare template subroutine {name}")
    return pattern.sub(replacement.group(0), text, count=1)


def validate_r1_template_derivation(text: str) -> None:
    require_hash(R1_TEMPLATE, EXPECTED_R1_TEMPLATE_SHA256)
    template = R1_TEMPLATE.read_text(encoding="ascii")
    normalized = text
    replacements = (
        ("frozen R2 ten-term lambda-10 candidate", "frozen lambda-30 candidate"),
        ("TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2", "TCPC_RELOCATED_SPHERE_T4_CANDIDATE"),
        ("tcpc-relocated-sphere-t4-candidate-r2-attempt1-results.csv", "tcpc-relocated-sphere-t4-candidate-verification-results.csv"),
        ("tcpc-relocated-sphere-t4-candidate-r2-attempt1-state.csv", "tcpc-relocated-sphere-t4-candidate-verification-state.csv"),
        ("tcpc-relocated-sphere-t4-candidate-r2-attempt1-closures.csv", "tcpc-relocated-sphere-t4-candidate-verification-closures.csv"),
        ("tcpc_relocated_sphere_t4_candidate_r2.hal", "tcpc_relocated_sphere_t4_candidate_lambda30.hal"),
        ("30 absolute tuning-pin totals", "27 absolute tuning-pin totals"),
        ("mode-26", "mode-25"),
        ("mode 26", "mode 25"),
        ("#711 = 26.0", "#711 = 25.0"),
        ("#711 - 26.0", "#711 - 25.0"),
        ("equal to 26", "equal to 25"),
    )
    for current, original in replacements:
        normalized = normalized.replace(current, original)
    normalized = replace_subroutine(normalized, "tcpc_candidate_pin_guard", template)
    if normalized != template:
        raise CandidateError(
            "R2 runner differs from the archived runnable R1 template outside approved identity substitutions"
        )


def validate_program(expected_pins: dict[str, float]) -> tuple[list[reach.Pose], str]:
    require_hash(PROGRAM, EXPECTED_PROGRAM_SHA256)
    text = PROGRAM.read_text(encoding="ascii")
    required = (
        "#707 = 101.0",
        "#711 = 26.0",
        "#715 = 2026082404.0",
        "#716 = 2.0",
        "#727 = 1.0",
        "#717 = 0.154742",
        "#3032 = #717",
        "o<exact_t4_tool_required> if [ABS[#500 - 4.0] GT 0.1]",
        "#516 = 229.407000",
        "#502 = #3032",
        "o<pair_calibration_live> if [ABS[#502 - #717] GT 0.0005]",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt1-results.csv",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt1-state.csv",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt1-closures.csv",
        "#539 = -1.0",
        "o<negative_b_upper_u> if [#520 LT -0.001]",
        "#122 = [-#539 * #533 * #511]",
        "G1 Z#<safe_z>",
    )
    for snippet in required:
        if snippet not in text:
            raise CandidateError(f"candidate program is missing {snippet!r}")
    forbidden = (
        "tcpc-relocated-sphere-t4-candidate-verification-results.csv",
        "tcpc-relocated-sphere-t4-candidate-verification-state.csv",
        "tcpc-relocated-sphere-t4-candidate-verification-closures.csv",
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
    validate_r1_template_derivation(text)
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


def correction_norm(
    model: fitter.CandidateEvaluation, b_value: float, c_value: float
) -> float:
    features = fitter.feature_matrix(
        np.array([b_value], dtype=float), np.array([c_value], dtype=float)
    )
    correction = fitter.correction_offsets_for_features(features, model.fit)[0]
    return float(np.linalg.norm(correction))


def quadratic_peak_offset(y_minus: float, y_center: float, y_plus: float) -> float:
    denominator = y_minus - 2.0 * y_center + y_plus
    if denominator >= 0.0 or abs(denominator) < 1e-15:
        return 0.0
    offset = 0.5 * (y_minus - y_plus) / denominator * DENSE_STEP_DEG
    if abs(offset) > DENSE_STEP_DEG:
        return 0.0
    return float(offset)


def dense_correction_check(
    b_minimum: float, b_maximum: float, *, enforce_protocol_cap: bool
) -> tuple[float, float, float]:
    if b_minimum >= b_maximum:
        raise CandidateError("dense correction check has invalid B limits")
    _, _, model = frozen_fit()
    c_values = np.arange(0.0, 360.0, DENSE_STEP_DEG)
    b_grid = np.arange(b_minimum, b_maximum + DENSE_STEP_DEG / 2.0, DENSE_STEP_DEG)
    maximum = -1.0
    maximum_b = float("nan")
    maximum_c = float("nan")
    for b_value in b_grid:
        b_values = np.full_like(c_values, b_value)
        features = fitter.feature_matrix(b_values, c_values)
        corrections = fitter.correction_offsets_for_features(features, model.fit)
        norms = np.linalg.norm(corrections, axis=1)
        index = int(np.argmax(norms))
        if float(norms[index]) > maximum:
            maximum = float(norms[index])
            maximum_b = float(b_value)
            maximum_c = float(c_values[index])

    for _ in range(2):
        c_offset = quadratic_peak_offset(
            correction_norm(model, maximum_b, (maximum_c - DENSE_STEP_DEG) % 360.0),
            correction_norm(model, maximum_b, maximum_c),
            correction_norm(model, maximum_b, (maximum_c + DENSE_STEP_DEG) % 360.0),
        )
        maximum_c = (maximum_c + c_offset) % 360.0
        if (
            b_minimum + DENSE_STEP_DEG
            <= maximum_b
            <= b_maximum - DENSE_STEP_DEG
        ):
            b_offset = quadratic_peak_offset(
                correction_norm(model, maximum_b - DENSE_STEP_DEG, maximum_c),
                correction_norm(model, maximum_b, maximum_c),
                correction_norm(model, maximum_b + DENSE_STEP_DEG, maximum_c),
            )
            maximum_b += b_offset
    maximum = correction_norm(model, maximum_b, maximum_c)
    if enforce_protocol_cap and maximum > MAX_MODELED_CORRECTION_MM + 1e-12:
        raise CandidateError(
            f"dense diagnostic-domain R2 correction {maximum:.6f} mm exceeds "
            f"{MAX_MODELED_CORRECTION_MM:.3f} mm"
        )
    return maximum, maximum_b, maximum_c


def reachability(
    overlay_pins: dict[str, float], details_path: Path
) -> tuple[
    np.ndarray, int, int, float, float, float,
    float, float, float, float, float, float,
]:
    anchor.validate_program_hash()
    result_rows = anchor.read_rows(anchor.DEFAULT_RESULTS, anchor.RESULT_FIELDS)
    state_rows = anchor.read_rows(anchor.DEFAULT_STATE, anchor.STATE_FIELDS)
    anchor_attempt, center_tuple = anchor.validate(result_rows, state_rows)
    center = np.array(center_tuple)
    baseline_pins = reach.parse_hal(BASE_HAL)
    pins = dict(baseline_pins)
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
    trajectory_correction = max(
        float(
            np.linalg.norm(
                reach.harmonic_offset(sample.b_deg, sample.c_deg, pins)
                - reach.harmonic_offset(sample.b_deg, sample.c_deg, baseline_pins)
            )
        )
        for sample in samples
    )
    if trajectory_correction > MAX_MODELED_CORRECTION_MM + 1e-12:
        raise CandidateError("R2 verification-trajectory correction exceeds 0.750 mm")
    dense_maximum, dense_b, dense_c = dense_correction_check(
        *DIAGNOSTIC_B_LIMITS, enforce_protocol_cap=True
    )
    configured_maximum, configured_b, configured_c = dense_correction_check(
        *limits.b_limits, enforce_protocol_cap=False
    )
    return (
        center,
        anchor_attempt,
        len(samples),
        worst_linear,
        remaining,
        trajectory_correction,
        dense_maximum,
        dense_b,
        dense_c,
        configured_maximum,
        configured_b,
        configured_c,
    )


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
    trajectory_correction: float,
    dense_maximum: float,
    dense_b: float,
    dense_c: float,
    configured_maximum: float,
    configured_b: float,
    configured_c: float,
) -> None:
    lines = [
        "# T4 R2 Loaded-Candidate Verification Preflight",
        "",
        "Status: `PASS` (offline preparation only; nothing was loaded and no machine action was taken).",
        "",
        "## Frozen Stage",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        "- tool state required by the runner: `T4`, `G43 H4`, `229.407000 mm`, `#3032=0.154742`",
        "- accepted rows / closures: `101 / 28`",
        "- holds: one initial `M0`; no intermediate holds",
        "- overlay: exactly 30 absolute totals for the frozen ten-term lambda-10 R2 fit",
        "- candidate pins are read-guarded before the initial hold, through every live guard, before per-pose motion, and immediately before accepted logging",
        "- G-code coefficient writes: none",
        "",
        "## Offline Checks",
        "",
        "- base HAL unchanged and hash-locked: `PASS`",
        "- candidate INI is the exact task-capture INI plus one final HALFILE: `PASS`",
        "- overlay matches an independent recomputation from immutable T4 attempt 1: `PASS`",
        "- runner is the archived runnable R1 program with only audited R2 identity substitutions: `PASS`",
        "- in-tree `bin/rs274 -g` preview parse: `PASS`",
        "- exact 101-pose order and positive/negative-B pairing: `PASS`",
        f"- anchor attempt / center: `{anchor_attempt}` / `X{center[0]:.6f} Y{center[1]:.6f} Z{center[2]:.6f}`",
        f"- candidate-geometry reachability samples: `{sample_count}`",
        f"- worst configured linear margin: `{worst_linear:.6f} mm`",
        f"- remaining margin after 2 mm center and 3 mm path allowances: `{remaining:.6f} mm` (`PASS`)",
        f"- maximum correction on the replayed verification trajectory: `{trajectory_correction:.6f} mm`",
        f"- maximum correction on the authorized diagnostic domain B[-90,+90] over a complete C cycle, using a 0.25-degree grid plus local quadratic interpolation: `{dense_maximum:.6f} mm` at `B{dense_b:+.4f} C{dense_c:.4f}` (`PASS` against 0.750 mm)",
        f"- configured-range extrapolation over B[-100,+100] and a complete C cycle: `{configured_maximum:.6f} mm` at `B{configured_b:+.4f} C{configured_c:.4f}` (reported limitation; not a protocol gate)",
        "",
        "## Frozen Files",
        "",
        "| file | SHA-256 |",
        "| --- | --- |",
    ]
    for item in (
        BASE_HAL,
        BASE_INI,
        FIT_SCRIPT,
        FIT_REPORT,
        FIT_RESIDUALS,
        FIT_PINS,
        FIT_CHECKPOINT,
        R1_TEMPLATE,
        OVERLAY,
        CANDIDATE_INI,
        PROGRAM,
        RESULTS,
        STATE,
        CLOSURES,
    ):
        lines.append(markdown_hash_row(item))
    lines.extend(
        [
            "",
            "## T4 Gates",
            "",
            "A completed mode-26 run is accepted only if its exact schema, pose, tool/TLO, contact-quality, state, endpoint, and all 28 closure contracts pass, and:",
            "",
            "1. On 76 equal-weight unique poses, centered RMS and maximum each improve over immutable mode-23 attempt 1 by both 10% and 0.010/0.020 mm.",
            "2. On those globally centered unique-pose residuals, positive- and negative-B high-tilt RMS each improve by at least 10%.",
            "3. Unique-pose B0 RMS does not worsen by more than 0.010 mm, and no unique pose worsens by more than 0.075 mm.",
            "4. Unique-pose centered RMS / max are at most 0.120 / 0.280 mm (offline prediction: 0.085763 / 0.204948 mm).",
            "5. Raw-101 centered RMS / max are at most 0.120 / 0.280 mm (offline prediction: 0.087176 / 0.207789 mm).",
            "6. Raw-101 actual-versus-predicted centered pattern RMS / max are at most 0.050 / 0.120 mm; both use their own raw-101 global mean.",
            "",
            "These gates test implementation and sign on the same measured grid. They do not authorize extrapolation to omitted C sectors, a general live correction, or a production HAL/INI change.",
            "",
            "## Explicit Limitations",
            "",
            "- weak paired-B selection stability: `b_sin2` 0/8; `bc_sinb_cos2c` and `bmid_cos2c` 3/8",
            "- selection-adjusted antipodal-C outer RMS / max: `0.253374 / 0.837828 mm`",
            "- the 0.750 mm protocol cap was imposed on measured poses; the largest outer-fit value was `0.749996 mm`; this preflight separately checks the primary densely and along the run path",
            "- the primary reaches `0.764644 mm` near `B-100/C272.6561` inside the configured B range but outside the authorized B +/-90 diagnostic domain; no manual, MDI, or jog motion is permitted under the candidate configuration",
            "- `bharm-c` vectors were excluded by the declared model scope, not selected against the 17-term pool",
            "- the forward-plus-swap protocol was frozen before fresh T4/T3 candidate data, but after inspection of the baseline T4 data",
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


def residual_metric(residuals: np.ndarray) -> tuple[float, float]:
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms**2))), float(np.max(norms))


def centered_residuals(values: np.ndarray) -> np.ndarray:
    return values - np.mean(values, axis=0)


def centered_metric(values: np.ndarray) -> tuple[float, float]:
    return residual_metric(centered_residuals(values))


def collapse_unique(
    observations: Sequence[fitter.Observation], centers: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    grouped: dict[tuple[float, float], list[np.ndarray]] = {}
    order: list[tuple[float, float]] = []
    for observation, center in zip(observations, centers):
        key = (observation.b_deg, observation.c_deg)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(center)
    if len(order) != fitter.UNIQUE_POSE_COUNT:
        raise CandidateError(f"candidate collapsed to {len(order)} unique poses, expected 76")
    return (
        np.vstack([np.mean(grouped[key], axis=0) for key in order]),
        np.array([key[0] for key in order]),
        np.array([key[1] for key in order]),
    )


def validate_exact_result_files() -> None:
    contracts = (
        (RESULTS, anchor.RESULT_FIELDS, 101),
        (STATE, anchor.STATE_FIELDS, 101),
        (CLOSURES, campaign.CLOSURE_FIELDS, 28),
    )
    for path, fields, expected_count in contracts:
        rows = anchor.read_rows(path, fields)
        if len(rows) != expected_count:
            raise CandidateError(
                f"{path.name} has {len(rows)} data rows, expected exactly {expected_count}"
            )
        for row in rows:
            if campaign.exact_integer(row, "campaign_id") != CAMPAIGN:
                raise CandidateError(f"{path.name} contains another campaign")
            if campaign.exact_integer(row, "stage_mode") != MODE:
                raise CandidateError(f"{path.name} contains another stage mode")
            if campaign.exact_integer(row, "attempt_id", positive=True) != ATTEMPT:
                raise CandidateError(f"{path.name} contains another attempt")


def evaluate_result_gates(
    run: campaign.ValidatedRun,
) -> tuple[list[tuple[str, bool, str]], dict[str, float]]:
    observations, data, model = frozen_fit()
    baseline_raw = np.vstack([item.center for item in observations])
    candidate_raw = run.centers
    if baseline_raw.shape != candidate_raw.shape:
        raise CandidateError("candidate and immutable baseline row shapes differ")

    baseline_unique, b_values, _ = collapse_unique(observations, baseline_raw)
    candidate_unique, candidate_b, _ = collapse_unique(observations, candidate_raw)
    if not np.array_equal(b_values, candidate_b) or np.max(np.abs(baseline_unique - data.centers)) > 5e-10:
        raise CandidateError("unique-pose collapse differs from the frozen R2 fit order")

    observation_b = np.array([item.b_deg for item in observations])
    observation_c = np.array([item.c_deg for item in observations])
    predicted_raw = baseline_raw + fitter.correction_offsets_for_features(
        fitter.feature_matrix(observation_b, observation_c), model.fit
    )
    predicted_unique = baseline_unique + fitter.correction_offsets(data, model.fit)

    baseline_unique_residuals = centered_residuals(baseline_unique)
    candidate_unique_residuals = centered_residuals(candidate_unique)
    predicted_unique_residuals = centered_residuals(predicted_unique)
    baseline_raw_residuals = centered_residuals(baseline_raw)
    candidate_raw_residuals = centered_residuals(candidate_raw)
    predicted_raw_residuals = centered_residuals(predicted_raw)

    base_unique_rms, base_unique_max = residual_metric(baseline_unique_residuals)
    candidate_unique_rms, candidate_unique_max = residual_metric(candidate_unique_residuals)
    predicted_unique_rms, predicted_unique_max = residual_metric(predicted_unique_residuals)
    base_raw_rms, base_raw_max = residual_metric(baseline_raw_residuals)
    candidate_raw_rms, candidate_raw_max = residual_metric(candidate_raw_residuals)
    predicted_raw_rms, predicted_raw_max = residual_metric(predicted_raw_residuals)
    if (
        abs(predicted_unique_rms - 0.085763134706) > 5e-10
        or abs(predicted_unique_max - 0.204948235546) > 5e-10
        or abs(predicted_raw_rms - 0.087176491560) > 5e-10
        or abs(predicted_raw_max - 0.207789379480) > 5e-10
    ):
        raise CandidateError("R2 prediction/reference convention changed")

    pattern_rms, pattern_max = residual_metric(
        candidate_raw_residuals - predicted_raw_residuals
    )
    masks = {
        "positive high-B RMS": b_values >= 30.0,
        "negative high-B RMS": b_values <= -30.0,
        "B0 RMS": np.abs(b_values) < 0.001,
    }
    group_metrics = {
        name: (
            residual_metric(baseline_unique_residuals[mask]),
            residual_metric(candidate_unique_residuals[mask]),
        )
        for name, mask in masks.items()
    }
    base_residual_norm = np.linalg.norm(baseline_unique_residuals, axis=1)
    candidate_residual_norm = np.linalg.norm(candidate_unique_residuals, axis=1)
    maximum_worsening = float(np.max(candidate_residual_norm - base_residual_norm))

    rms_limit = min(base_unique_rms * 0.90, base_unique_rms - 0.010)
    max_limit = min(base_unique_max * 0.90, base_unique_max - 0.020)
    positive_base = group_metrics["positive high-B RMS"][0][0]
    positive_candidate = group_metrics["positive high-B RMS"][1][0]
    negative_base = group_metrics["negative high-B RMS"][0][0]
    negative_candidate = group_metrics["negative high-B RMS"][1][0]
    b0_base = group_metrics["B0 RMS"][0][0]
    b0_candidate = group_metrics["B0 RMS"][1][0]
    gates = [
        ("unique-pose centered RMS improvement", candidate_unique_rms <= rms_limit, f"{candidate_unique_rms:.6f} <= {rms_limit:.6f} mm"),
        ("unique-pose centered maximum improvement", candidate_unique_max <= max_limit, f"{candidate_unique_max:.6f} <= {max_limit:.6f} mm"),
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
        ("maximum unique-pose worsening", maximum_worsening <= MAX_ROW_WORSENING_MM, f"{maximum_worsening:.6f} <= {MAX_ROW_WORSENING_MM:.6f} mm"),
        (
            "unique-pose RMS ceiling",
            candidate_unique_rms <= UNIQUE_RMS_LIMIT_MM,
            f"{candidate_unique_rms:.6f} <= {UNIQUE_RMS_LIMIT_MM:.6f} mm",
        ),
        (
            "unique-pose maximum ceiling",
            candidate_unique_max <= UNIQUE_MAX_LIMIT_MM,
            f"{candidate_unique_max:.6f} <= {UNIQUE_MAX_LIMIT_MM:.6f} mm",
        ),
        (
            "raw-101 RMS ceiling",
            candidate_raw_rms <= RAW_RMS_LIMIT_MM,
            f"{candidate_raw_rms:.6f} <= {RAW_RMS_LIMIT_MM:.6f} mm",
        ),
        (
            "raw-101 maximum ceiling",
            candidate_raw_max <= RAW_MAX_LIMIT_MM,
            f"{candidate_raw_max:.6f} <= {RAW_MAX_LIMIT_MM:.6f} mm",
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
    metrics = {
        "base_unique_rms": base_unique_rms,
        "base_unique_max": base_unique_max,
        "candidate_unique_rms": candidate_unique_rms,
        "candidate_unique_max": candidate_unique_max,
        "base_raw_rms": base_raw_rms,
        "base_raw_max": base_raw_max,
        "candidate_raw_rms": candidate_raw_rms,
        "candidate_raw_max": candidate_raw_max,
        "pattern_rms": pattern_rms,
        "pattern_max": pattern_max,
    }
    return gates, metrics


def write_result_report(
    path: Path,
    run: campaign.ValidatedRun,
    gates: Sequence[tuple[str, bool, str]],
    metrics: dict[str, float],
) -> bool:
    passed = all(gate[1] for gate in gates)
    lines = [
        "# T4 R2 Loaded-Candidate Verification Report",
        "",
        f"Status: `{'PASS' if passed else 'FAIL'}`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {run.attempt}`",
        f"- validated rows / closures: `{len(run.centers)} / {len(run.closure_norms)}`",
        f"- worst closure: `{np.max(run.closure_norms):.6f} mm`",
        f"- immutable mode-23 equal-76 centered RMS / max: `{metrics['base_unique_rms']:.6f} / {metrics['base_unique_max']:.6f} mm`",
        f"- mode-26 equal-76 centered RMS / max: `{metrics['candidate_unique_rms']:.6f} / {metrics['candidate_unique_max']:.6f} mm`",
        f"- immutable mode-23 raw-101 centered RMS / max: `{metrics['base_raw_rms']:.6f} / {metrics['base_raw_max']:.6f} mm`",
        f"- mode-26 raw-101 centered RMS / max: `{metrics['candidate_raw_rms']:.6f} / {metrics['candidate_raw_max']:.6f} mm`",
        f"- raw-101 actual-versus-predicted pattern RMS / max: `{metrics['pattern_rms']:.6f} / {metrics['pattern_max']:.6f} mm`",
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
            "Weak term stability and the 0.253374 / 0.837828 mm antipodal outer result remain release blockers; T3 is still required as an untouched transfer check.",
            "",
            "T3 must not run with the candidate overlay. Clean-restart the baseline task-capture INI and verify the frozen base-HAL hash before the current-calibration T3 holdout.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")
    return passed


def offline_contract(
    details: Path,
) -> tuple[
    np.ndarray, int, int, float, float, float,
    float, float, float, float, float, float,
]:
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
    assert len(pins) == 30
    assert len(poses) == 101
    assert len(digest) == 64
    spec = candidate_run_spec()
    assert spec.mode == MODE and len(spec.expected_rows) == 101
    assert len(spec.closure_ranges) == 28
    assert {row.pose.b_deg for row in spec.expected_rows} == {
        -90.0, -60.0, -45.0, -30.0, -15.0, -10.0, -5.0,
        0.0, 5.0, 10.0, 15.0, 30.0, 45.0, 60.0, 90.0,
    }
    dense_maximum, dense_b, dense_c = dense_correction_check(
        *DIAGNOSTIC_B_LIMITS, enforce_protocol_cap=True
    )
    assert abs(dense_maximum - 0.671900103005) < 5e-10
    assert abs(dense_b + 90.0) < 1e-12
    assert abs(dense_c - 272.8566) < 0.001
    configured_maximum, configured_b, configured_c = dense_correction_check(
        -100.0, 100.0, enforce_protocol_cap=False
    )
    assert abs(configured_maximum - 0.764644095) < 5e-9
    assert abs(configured_b + 100.0) < 1e-12
    assert abs(configured_c - 272.6561) < 0.001

    broken_guard = PROGRAM.read_text(encoding="ascii").replace(
        "    (abort, R2 candidate pin mismatch 01 charm cos x)\n", "", 1
    )
    try:
        validate_pin_guard(broken_guard, pins)
    except CandidateError:
        pass
    else:
        raise AssertionError("candidate guard without an abort body was accepted")


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
        (
            center,
            anchor_attempt,
            sample_count,
            worst_linear,
            remaining,
            trajectory_correction,
            dense_maximum,
            dense_b,
            dense_c,
            configured_maximum,
            configured_b,
            configured_c,
        ) = offline_contract(args.reach_details)
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
                trajectory_correction,
                dense_maximum,
                dense_b,
                dense_c,
                configured_maximum,
                configured_b,
                configured_c,
            )
            print("T4 candidate preflight: PASS")
        else:
            report = args.report or DEFAULT_RESULT_REPORT
            validate_exact_result_files()
            run = campaign.validate_run(candidate_run_spec())
            if run.attempt != ATTEMPT:
                raise CandidateError(f"candidate attempt is {run.attempt}, expected frozen {ATTEMPT}")
            gates, metrics = evaluate_result_gates(run)
            passed = write_result_report(report, run, gates, metrics)
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
