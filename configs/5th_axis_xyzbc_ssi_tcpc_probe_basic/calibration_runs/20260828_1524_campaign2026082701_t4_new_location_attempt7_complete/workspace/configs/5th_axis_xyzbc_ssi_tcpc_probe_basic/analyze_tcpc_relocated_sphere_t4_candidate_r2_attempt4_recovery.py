#!/usr/bin/env python3
"""Validate campaign-04 T4 R2 attempt-4 recovery and optional composite data.

The recovery acquisition is intentionally sparse: sequences 1-9 and 67-101.
It can validate that acquisition on its own.  With --composite it uses sealed
attempt-3 sequences 45-66 and immutable attempt-2 sequences 10-44.  The three
acquisitions are independently validated before any diagnostic composition.
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
import analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt2 as attempt2
import analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt3_recovery as attempt3


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CAMPAIGN = 2026082404
MODE = 28
ATTEMPT = 4
ATTEMPT2_MODE = 26
ATTEMPT2_ATTEMPT = 2
ATTEMPT3_MODE = 27
ATTEMPT3_ATTEMPT = 3

PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_attempt4_recovery_verification.ngc"
ATTEMPT3_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_attempt3_recovery_verification.ngc"
ATTEMPT2_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_attempt2_verification.ngc"
ATTEMPT2_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt2.py"
ATTEMPT3_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt3_recovery.py"
RECOVERY_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate_r2_recovery_a3.ini"
COUNTER_HAL = HERE / "tcpc_probe_attempt3_edge_counters.hal"
EDGE_MONITOR = HERE / "diagnostics/monitor_tcpc_probe_edges.py"
EDGE_MONITOR_LAUNCHER = HERE / "diagnostics/start_tcpc_probe_edge_monitor.sh"

RESULTS = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-results.csv"
STATE = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-state.csv"
CLOSURES = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-closures.csv"
TRACE = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-contact-trace.csv"
GAP_TRACE = HERE / "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-gap-trace.csv"

ATTEMPT2_ARCHIVE = HERE / "calibration_runs/20260825_1654_campaign04_t4_candidate_r2_attempt2_partial_no_touch_seq49"
ATTEMPT2_SUMS = ATTEMPT2_ARCHIVE / "SHA256SUMS"
ATTEMPT2_RESULTS = ATTEMPT2_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt2-results.csv"
ATTEMPT2_STATE = ATTEMPT2_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt2-state.csv"
ATTEMPT2_CLOSURES = ATTEMPT2_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt2-closures.csv"

ATTEMPT3_ARCHIVE = HERE / "calibration_runs/20260825_2249_campaign04_t4_candidate_r2_attempt3_partial_gap_burst_seq70"
ATTEMPT3_SUMS = ATTEMPT3_ARCHIVE / "SHA256SUMS"
ATTEMPT3_RESULTS = ATTEMPT3_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt3-recovery-results.csv"
ATTEMPT3_STATE = ATTEMPT3_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt3-recovery-state.csv"
ATTEMPT3_CLOSURES = ATTEMPT3_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt3-recovery-closures.csv"
ATTEMPT3_TRACE = ATTEMPT3_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt3-recovery-contact-trace.csv"
ATTEMPT3_GAP_TRACE = ATTEMPT3_ARCHIVE / "tcpc-relocated-sphere-t4-candidate-r2-attempt3-recovery-gap-trace.csv"

DEFAULT_PREFLIGHT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2_ATTEMPT4_RECOVERY_PREFLIGHT_REPORT.md"
DEFAULT_RESULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2_ATTEMPT4_RECOVERY_REPORT.md"

EXPECTED_PROGRAM_SHA256 = "f4dd59e60219e3c0a5d83f3f76fbcb451871a9996d186adae6d2fdd6fd480364"
EXPECTED_ATTEMPT3_PROGRAM_SHA256 = "1e1dee457a6b9792585f2afe4abb2f99b09951e20bdfe2f174b863896b77579d"
EXPECTED_ATTEMPT3_ANALYZER_SHA256 = "0508f819ddb26000194c4c336b6a162212d8ffbdf3439a95b34933baa0cfa15f"
EXPECTED_ATTEMPT2_PROGRAM_SHA256 = "6421c2f8cb8c12a7e4d8ace98f956e4270974482058815609cce9b5f22dbea86"
EXPECTED_ATTEMPT2_ANALYZER_SHA256 = "0774fc7d75e49fee26ad990c74b11cc6cd0267ecfc15019ae4cc7e117736afe2"
EXPECTED_RECOVERY_INI_SHA256 = "66d2b123e2df19eab2a0c1f53875e699c666b32e3a19800ac9427d8eafbabd3b"
EXPECTED_COUNTER_HAL_SHA256 = "6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34"
EXPECTED_EDGE_MONITOR_SHA256 = "83531e3dcbb26b516a60fe9a89f32aaf0cf85180e5fd33b88ec7b3664b629aea"
EXPECTED_EDGE_MONITOR_LAUNCHER_SHA256 = "0793ddfed545562ffeffe50dbe91b4a0a74ec45e6d0e16153f344288994db49c"
EXPECTED_ATTEMPT2_SUMS_SHA256 = "5a8e2562c3ad85601cd701207aba87e061c2eb9ce4e767f6519b314748a07895"
EXPECTED_ATTEMPT2_RESULTS_SHA256 = "8c3ee95280b068be4322f526ced03836c7e371a0b12db444a5ee31eb8ae123c4"
EXPECTED_ATTEMPT2_STATE_SHA256 = "66d7d5e1d8568e2b4f50ce2218d435a537f79f6ae8c951cd49dad1635df11b8d"
EXPECTED_ATTEMPT2_CLOSURES_SHA256 = "47e4b96fa7fb5f7b69aa1d0d7c03796d0835bd67a31052cdacb55ba3a6909e08"
EXPECTED_ATTEMPT3_SUMS_SHA256 = "d77d728bccc11c36cd97ccbd7ae28fb6832aa5b2695cd3244e527e0b9bde3072"
EXPECTED_ATTEMPT3_RESULTS_SHA256 = "f2e7e1dcf9c38f2bceba356be2e0720f08cd5d3c2c35c2d1486afc07adf3771c"
EXPECTED_ATTEMPT3_STATE_SHA256 = "427e9d4721dcc11f014b80895ee10e997058effd66bf917128c612fb1087b966"
EXPECTED_ATTEMPT3_CLOSURES_SHA256 = "ef1f2053fda13a993132e2e168eeadc9fd2929746244aeb7c7e91b900238cc6c"
EXPECTED_ATTEMPT3_TRACE_SHA256 = "b16628171590537be4a7429d5d552532ff5da55315f568332f65e0f09d193cd4"
EXPECTED_ATTEMPT3_GAP_TRACE_SHA256 = "fbcce79d3e0a9572680f1b2ad3f92f60a583a5785bd58d9aff657c5b52127612"

EXPECTED_HEADER_SHA256 = {
    RESULTS: "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    STATE: "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    CLOSURES: "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    TRACE: "df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8",
    GAP_TRACE: "e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2",
}

TRACE_FIELDS = (
    "schema_version", "campaign_id", "stage_mode", "attempt_id",
    "global_seq", "abs_b_deg", "abs_c_deg", "acquisition_try",
    "pass_id", "contact_id", "pre_raw_count", "pre_mux_count",
    "pre_gated_count", "post_raw_count", "post_mux_count",
    "post_gated_count", "ready_raw_count", "ready_mux_count",
    "ready_gated_count", "probe_result", "travel_mm", "raw_delta",
    "mux_delta", "gated_delta", "repeat_raw_delta", "repeat_mux_delta",
    "repeat_gated_delta", "extra_raw_minus_gated_delta", "burst_flag",
    "consistency_fault", "release_fault", "terminal_failure",
)

GAP_TRACE_FIELDS = (
    "schema_version", "campaign_id", "stage_mode", "attempt_id",
    "next_global_seq", "abs_b_deg", "abs_c_deg", "acquisition_try",
    "pass_id", "contact_id", "prior_ready_raw_count",
    "prior_ready_mux_count", "prior_ready_gated_count",
    "current_pre_raw_count", "current_pre_mux_count",
    "current_pre_gated_count", "gap_raw_delta", "gap_mux_delta",
    "gap_gated_delta", "prior_contact_extra_delta",
    "combined_extra_delta", "burst_flag", "consistency_fault",
    "initial_baseline",
)

FULL_EXPECTED = campaign.expected_rows(reach.grid(), campaign.T4_RANGES)
FULL_BY_SEQ = {row.seq: row for row in FULL_EXPECTED}
RECOVERY_SEQUENCES = tuple(range(1, 10)) + tuple(range(67, 102))
RECOVERY_EXPECTED = tuple(FULL_BY_SEQ[seq] for seq in RECOVERY_SEQUENCES)
RECOVERY_SEQUENCE_SET = set(RECOVERY_SEQUENCES)
RECOVERY_CLOSURES = tuple(
    item for item in campaign.T4_CLOSURES
    if item[1] in RECOVERY_SEQUENCE_SET and item[2] in RECOVERY_SEQUENCE_SET
)
ATTEMPT2_SEQUENCES = tuple(range(1, 49))
ATTEMPT2_CLOSURE_RANGES = tuple(item for item in campaign.T4_CLOSURES if item[2] <= 48)
ATTEMPT3_ACCEPTED_SEQUENCES = tuple(range(1, 10)) + tuple(range(45, 70))
ATTEMPT2_COMPOSITE_SEQUENCES = tuple(range(10, 45))
ATTEMPT3_COMPOSITE_SEQUENCES = tuple(range(45, 67))
ATTEMPT2_COMPOSITE_CLOSURES = tuple(
    item for item in campaign.T4_CLOSURES
    if item[1] in ATTEMPT2_COMPOSITE_SEQUENCES
    and item[2] in ATTEMPT2_COMPOSITE_SEQUENCES
)
ATTEMPT3_COMPOSITE_CLOSURES = tuple(
    item for item in campaign.T4_CLOSURES
    if item[1] in ATTEMPT3_COMPOSITE_SEQUENCES
    and item[2] in ATTEMPT3_COMPOSITE_SEQUENCES
)
COMPOSITE_CLOSURES = (
    ATTEMPT2_COMPOSITE_CLOSURES
    + ATTEMPT3_COMPOSITE_CLOSURES
    + RECOVERY_CLOSURES
)
COMPOSITE_CLOSURE_COUNT = len(COMPOSITE_CLOSURES)


class RecoveryError(ValueError):
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
        raise RecoveryError(f"SHA-256 changed for {path}: {actual}, expected {expected}")


def exact_int(row: dict[str, str], field: str, *, positive: bool = False) -> int:
    return campaign.exact_integer(row, field, positive=positive)


def validate_recovery_configuration() -> None:
    if (
        len(set(COMPOSITE_CLOSURES)) != len(COMPOSITE_CLOSURES)
        or set(COMPOSITE_CLOSURES) != set(campaign.T4_CLOSURES)
    ):
        raise RecoveryError(
            "attempt-2/3/4 closure ownership does not exactly partition the canonical closures"
        )

    for path, digest in (
        (RECOVERY_INI, EXPECTED_RECOVERY_INI_SHA256),
        (COUNTER_HAL, EXPECTED_COUNTER_HAL_SHA256),
        (EDGE_MONITOR, EXPECTED_EDGE_MONITOR_SHA256),
        (EDGE_MONITOR_LAUNCHER, EXPECTED_EDGE_MONITOR_LAUNCHER_SHA256),
    ):
        require_hash(path, digest)

    ini = RECOVERY_INI.read_text(encoding="ascii")
    counter_line = "HALFILE = tcpc_probe_attempt3_edge_counters.hal"
    xhc_line = "HALFILE = ../5th_axis_xyzbc_ssi_probe_basic/xhc.hal"
    overlay_line = "HALFILE = tcpc_relocated_sphere_t4_candidate_r2.hal"
    for line in (counter_line, xhc_line, overlay_line):
        if ini.count(line) != 1:
            raise RecoveryError(f"recovery INI must contain exactly one {line!r}")
    if not (ini.index(counter_line) < ini.index(xhc_line) < ini.index(overlay_line)):
        raise RecoveryError("recovery INI HAL order changed")
    hal_lines = [
        line.strip() for line in ini.splitlines()
        if line.strip().startswith("HALFILE =")
    ]
    if not hal_lines or hal_lines[-1] != overlay_line:
        raise RecoveryError("R2 overlay must remain the final recovery HALFILE")

    hal = COUNTER_HAL.read_text(encoding="ascii")
    required = (
        "loadrt counter num_chan=3",
        "net t_probe-in => counter.0.phase-A",
        "net probe-mux => counter.1.phase-A",
        "net tcpc-probe-gated => counter.2.phase-A",
        "addf counter.update-counters servo-thread",
        "addf counter.capture-position servo-thread",
        "loadusr -Wn tcpc_probe_edge_monitor /home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/diagnostics/start_tcpc_probe_edge_monitor.sh",
    )
    for line in required:
        if hal.count(line) != 1:
            raise RecoveryError(f"counter HAL contract changed: {line}")
    active = [line.strip() for line in hal.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if any("motion.probe-input" in line or "motion.digital-out" in line for line in active):
        raise RecoveryError("counter HAL must not drive probe or digital motion pins")


def motion_lines(text: str) -> list[str]:
    pattern = re.compile(r"^\s*(?:G(?:1|38\.3|90|91)\b.*|F(?:#|[-+0-9]).*)$", re.MULTILINE)
    return [match.group(0).strip() for match in pattern.finditer(text)]


def normalize_output_namespace(text: str) -> str:
    return re.sub(r"attempt[34]-recovery", "attemptX-recovery", text)


def validate_program() -> None:
    require_hash(ATTEMPT3_PROGRAM, EXPECTED_ATTEMPT3_PROGRAM_SHA256)
    require_hash(ATTEMPT3_ANALYZER, EXPECTED_ATTEMPT3_ANALYZER_SHA256)
    require_hash(ATTEMPT2_PROGRAM, EXPECTED_ATTEMPT2_PROGRAM_SHA256)
    require_hash(ATTEMPT2_ANALYZER, EXPECTED_ATTEMPT2_ANALYZER_SHA256)
    require_hash(PROGRAM, EXPECTED_PROGRAM_SHA256)
    original = ATTEMPT3_PROGRAM.read_text(encoding="ascii")
    text = PROGRAM.read_text(encoding="ascii")

    source_lines = text.splitlines()
    longest = max((len(line) for line in source_lines), default=0)
    if longest > 225:
        line_number = max(range(len(source_lines)), key=lambda index: len(source_lines[index])) + 1
        raise RecoveryError(
            f"recovery source line {line_number} is {longest} chars; frozen limit is 225"
        )

    if motion_lines(text) != motion_lines(original):
        raise RecoveryError("recovery changed a probing, positioning, or feed line")
    if re.findall(r"^\s*G4\b.*$", text, re.MULTILINE) != re.findall(r"^\s*G4\b.*$", original, re.MULTILINE):
        raise RecoveryError("recovery changed the dwell/release-sampling contract")
    if "G4 P20" in text or "G4 P10" in text:
        raise RecoveryError("recovery reintroduced a 10/20 second settle delay")

    pins = attempt2.validate_overlay()
    attempt2.validate_pin_guard(text, pins)
    for name in (
        "tcpc_pair_coordinate_guard", "tcpc_pair_hold_position_guard",
        "tcpc_pair_selector_guard", "tcpc_candidate_pin_guard",
        "tcpc_pair_live_guard", "tcpc_pair_release_guard",
        "tcpc_probe_counter_guard", "tcpc_contact_gap_log",
        "tcpc_contact_trace_begin", "tcpc_contact_trace_post",
        "tcpc_contact_trace_finish", "tcpc_pair_probe_ready_guard",
        "tcpc_vector_sphere_pass4", "tcpc_measure_pose",
        "tcpc_primary_closure_guard",
        "tcpc_primary_outer_reference", "tcpc_primary_b0_sweep",
        "tcpc_primary_low_tilt_block", "tcpc_primary_tilt_block",
        "tcpc_baseline_return_top_clear",
    ):
        current_sub = normalize_output_namespace(attempt2.subroutine_text(text, name))
        frozen_sub = normalize_output_namespace(attempt2.subroutine_text(original, name))
        if current_sub != frozen_sub:
            raise RecoveryError(f"recovery changed protected subroutine {name}")

    required = (
        "#707 = 44.0", "#711 = 28.0", "#727 = 4.0", "#726 = 66.0",
        "#788 = [#788 + 1.0]", "counter.0.counts", "counter.1.counts",
        "counter.2.counts", "#969 GT 2.0",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-results.csv",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-state.csv",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-closures.csv",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-contact-trace.csv",
        "tcpc-relocated-sphere-t4-candidate-r2-attempt4-recovery-gap-trace.csv",
        "#959 = [#953 + [#956 - #958]]", "#959 GT 2.0",
        "[ABS[#958] GT 0.000001]",
        "ABS[#966 - #967] GT 0.000001",
        "ABS[#965 - 1.0] GT 0.000001",
        "[#972 GT 0.5] AND [[ABS[#956] GT 0.000001]",
        "#972 = #955",
        "Probe edge activity occurred after M0 before the first G38",
        "#<release_status_mode> = #3", "#971 = 1.0",
        "Probe did not reach a valid two-sample released state after contact",
        "Electrical retrigger burst exceeded two repeats across inter-contact gap",
        "(Establish the sticky edge baseline only after the operator M0 boundary.)",
    )
    for snippet in required:
        if snippet not in text:
            raise RecoveryError(f"recovery program is missing {snippet!r}")
    for forbidden in (
        "attempt2-results.csv", "attempt2-state.csv", "attempt2-closures.csv",
        "attempt3-recovery-results.csv", "attempt3-recovery-state.csv",
        "attempt3-recovery-closures.csv", "attempt3-recovery-contact-trace.csv",
        "attempt3-recovery-gap-trace.csv",
        "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]",
        "o<tcpc_primary_low_tilt_block> call [-5.0] [-5.0]",
        "o<tcpc_primary_low_tilt_block> call [10.0] [10.0]",
        "o<tcpc_primary_low_tilt_block> call [-10.0] [-10.0]",
        "o<tcpc_primary_low_tilt_block> call [15.0] [15.0]",
        "o<tcpc_primary_low_tilt_block> call [-15.0] [-15.0]",
        "o<tcpc_primary_tilt_block> call [30.0] [30.0]",
        "o<tcpc_primary_tilt_block> call [-30.0] [-30.0]",
        "o<tcpc_primary_tilt_block> call [45.0] [45.0]",
    ):
        if forbidden in text:
            raise RecoveryError(f"recovery program contains forbidden {forbidden!r}")

    if len(re.findall(r"^M0\s*$", text, re.MULTILINE)) != 1 or re.search(r"^M1\s*$", text, re.MULTILINE):
        raise RecoveryError("recovery must have exactly one initial M0 and no M1")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise RecoveryError("four-contact subroutine no longer has exactly four G38 moves")
    for call, count in (
        ("o<tcpc_contact_trace_begin> call", 8),
        ("o<tcpc_contact_trace_post> call", 4),
        ("o<tcpc_contact_trace_finish> call [0.0]", 4),
        ("o<tcpc_contact_trace_finish> call [1.0]", 4),
    ):
        if text.count(call) != count:
            raise RecoveryError(f"trace call contract changed for {call}")

    trace_finish = attempt2.subroutine_text(text, "tcpc_contact_trace_finish")
    log_at = trace_finish.find("(LOG,1.0")
    burst_abort_at = trace_finish.find("o<trace_success_burst_abort> if")
    if log_at < 0 or burst_abort_at < log_at:
        raise RecoveryError("successful burst abort must occur after trace persistence")
    if "[#936 GT 0.5] AND [#970 LT 0.5]" not in trace_finish:
        raise RecoveryError("burst abort does not preserve contextual terminal no-touch logging")
    gap_begin = attempt2.subroutine_text(text, "tcpc_contact_trace_begin")
    gap_log = attempt2.subroutine_text(text, "tcpc_contact_gap_log")
    if gap_begin.find("o<tcpc_contact_gap_log> call") > gap_begin.find("(abort, Electrical retrigger burst"):
        raise RecoveryError("inter-contact burst must persist its gap row before abort")
    if "#959 = [#953 + [#956 - #958]]" not in gap_begin or "#959 GT 2.0" not in gap_begin:
        raise RecoveryError("inter-contact gap does not combine prior and sticky extra edges")
    if "#955 = 0.0" not in gap_log:
        raise RecoveryError("initial-baseline marker is not consumed by the first gap log")
    m0_at = text.find("\nM0\n")
    baseline_at = text.find("(Establish the sticky edge baseline only after the operator M0 boundary.)")
    body_at = text.find("(Dedicated mode 28 T4 loaded-candidate recovery body.)")
    if not (0 <= m0_at < baseline_at < body_at):
        raise RecoveryError("sticky counter baseline is not between M0 and recovery motion")
    release = attempt2.subroutine_text(text, "tcpc_pair_release_guard")
    if "#<release_status_mode> = #3" not in release or release.count("#971 = 1.0") < 4:
        raise RecoveryError("release guard does not return every bounded release fault")
    if "G4 P0.05" not in release or "#<release_clear_count> LT 1.5" not in release:
        raise RecoveryError("release guard changed the two-sample 0.05 s clear contract")
    if text.count("o<tcpc_pair_release_guard> call [#520] [#521] [1.0]") != 4:
        raise RecoveryError("each successful contact must use status-return release handling")
    if text.count("o<tcpc_pair_release_guard> call [#520] [#521] [0.0]") != 1:
        raise RecoveryError("non-contact retry release must retain hard-abort handling")
    if trace_finish.find("(LOG,1.0") > trace_finish.find("o<trace_release_fault_abort> if"):
        raise RecoveryError("release-fault contact trace must persist before abort")

    body_match = re.search(
        r"^o<run_relocated_t4_primary> if \[ABS\[#711 - 28\.0\] LT 0\.1\]\s*$([\s\S]*?)^o<run_relocated_t4_primary> endif\s*$",
        text, re.MULTILINE,
    )
    if body_match is None:
        raise RecoveryError("mode-28 recovery body is missing")
    body = body_match.group(1)
    ordered = (
        "o<tcpc_primary_b0_sweep> call [100.0]",
        "#726 = 66.0",
        "o<tcpc_primary_tilt_block> call [-45.0] [-45.0]",
        "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]",
        "o<tcpc_primary_tilt_block> call [60.0] [60.0]",
        "o<tcpc_primary_tilt_block> call [-60.0] [-60.0]",
        "o<tcpc_primary_tilt_block> call [90.0] [90.0]",
        "o<tcpc_primary_tilt_block> call [-90.0] [-90.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
    )
    positions = [body.find(item) for item in ordered]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise RecoveryError("recovery pose-block order changed")
    expected_body_calls = {
        "o<tcpc_primary_b0_sweep> call": 2,
        "o<tcpc_primary_tilt_block> call": 5,
        "o<tcpc_primary_low_tilt_block> call": 0,
        "o<tcpc_measure_pose> call": 1,
    }
    for call, count in expected_body_calls.items():
        if body.count(call) != count:
            raise RecoveryError(f"mode-28 body call count changed for {call}")


def run_rs274_preview() -> None:
    completed = subprocess.run(
        [str(REPO_ROOT / "bin/rs274"), "-g", str(PROGRAM)],
        cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=30, check=False,
    )
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-12:])
        raise RecoveryError(f"in-tree rs274 -g failed ({completed.returncode}):\n{tail}")


def validate_header_only_files() -> None:
    fields = {
        RESULTS: anchor.RESULT_FIELDS,
        STATE: anchor.STATE_FIELDS,
        CLOSURES: campaign.CLOSURE_FIELDS,
        TRACE: TRACE_FIELDS,
        GAP_TRACE: GAP_TRACE_FIELDS,
    }
    for path, expected_fields in fields.items():
        require_hash(path, EXPECTED_HEADER_SHA256[path])
        with path.open(newline="", encoding="ascii") as stream:
            rows = list(csv.reader(stream))
        if rows != [list(expected_fields)]:
            raise RecoveryError(f"output is not exact header-only: {path}")


def run_spec(mode: int, results: Path, state: Path, closures: Path, sequences: Sequence[int], name: str) -> campaign.RunSpec:
    return campaign.RunSpec(
        name, 4, mode, reach.T4_TOOL_LENGTH, anchor.CAL_OFFSET,
        anchor.EFFECTIVE_RADIUS, results, state, closures,
        tuple(FULL_BY_SEQ[seq] for seq in sequences), tuple(),
    )


def read_identity_rows(path: Path, fields: Sequence[str], mode: int, attempt: int) -> list[dict[str, str]]:
    rows = anchor.read_rows(path, fields)
    for row in rows:
        if exact_int(row, "campaign_id") != CAMPAIGN:
            raise RecoveryError(f"{path.name} contains another campaign")
        if exact_int(row, "stage_mode") != mode:
            raise RecoveryError(f"{path.name} contains another stage mode")
        if exact_int(row, "attempt_id", positive=True) != attempt:
            raise RecoveryError(f"{path.name} contains another attempt")
    return rows


def validate_closure_rows(
    spec: campaign.RunSpec,
    rows: Sequence[dict[str, str]],
    expected_ranges: Sequence[tuple[int, int, int]],
    results_by_seq: dict[int, dict[str, str]],
    attempt: int,
) -> np.ndarray:
    if len(rows) != len(expected_ranges):
        raise RecoveryError(f"{spec.name}: closures {len(rows)}, expected {len(expected_ranges)}")
    norms: list[float] = []
    for row, (block, first, last) in zip(rows, expected_ranges):
        for field, value, positive in (
            ("schema_version", 1, True), ("campaign_id", CAMPAIGN, True),
            ("stage_mode", spec.mode, True), ("attempt_id", attempt, True),
            ("block_id", block, False), ("open_sample_seq", first, True),
            ("close_sample_seq", last, True), ("pass", 1, False),
        ):
            if exact_int(row, field, positive=positive) != value:
                raise RecoveryError(f"{spec.name}: closure {field} mismatch")
        anchor.near(row, "limit_mm", 0.050, 1e-9)
        opening = np.array([anchor.number(results_by_seq[first], field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")])
        closing = np.array([anchor.number(results_by_seq[last], field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")])
        delta = closing - opening
        logged = np.array([anchor.number(row, field) for field in ("closure_dx_mm", "closure_dy_mm", "closure_dz_mm")])
        if np.linalg.norm(delta - logged) > 3e-6:
            raise RecoveryError(f"{spec.name}: closure {block} vector mismatch")
        norm = anchor.bounded(row, "closure_norm_mm", 0.0, 0.050)
        if abs(norm - np.linalg.norm(delta)) > 3e-6:
            raise RecoveryError(f"{spec.name}: closure {block} norm mismatch")
        expected = FULL_BY_SEQ[last]
        anchor.near(row, "abs_b_deg", expected.pose.b_deg, 0.01)
        anchor.near(row, "abs_c_deg", expected.pose.c_deg, 0.01)
        norms.append(norm)
    return np.array(norms, dtype=float)


def validate_acquisition(
    spec: campaign.RunSpec,
    sequences: Sequence[int],
    closure_ranges: Sequence[tuple[int, int, int]],
    *,
    allow_prefix: bool = False,
) -> tuple[dict[int, np.ndarray], np.ndarray, list[int]]:
    results = read_identity_rows(spec.results_path, anchor.RESULT_FIELDS, spec.mode, ATTEMPT if spec.mode == MODE else ATTEMPT2_ATTEMPT)
    states = read_identity_rows(spec.state_path, anchor.STATE_FIELDS, spec.mode, ATTEMPT if spec.mode == MODE else ATTEMPT2_ATTEMPT)
    closures = read_identity_rows(spec.closures_path, campaign.CLOSURE_FIELDS, spec.mode, ATTEMPT if spec.mode == MODE else ATTEMPT2_ATTEMPT)
    result_seq = [exact_int(row, "sample_seq", positive=True) for row in results]
    state_seq = [exact_int(row, "sample_seq", positive=True) for row in states]
    target = list(sequences)
    if allow_prefix:
        if result_seq != target[: len(result_seq)] or state_seq != result_seq:
            raise RecoveryError(f"{spec.name}: result/state rows are not the exact recovery prefix")
    elif result_seq != target or state_seq != target:
        raise RecoveryError(f"{spec.name}: result/state sequence differs from exact contract")
    if len(set(result_seq)) != len(result_seq):
        raise RecoveryError(f"{spec.name}: duplicated sequence")

    attempt = ATTEMPT if spec.mode == MODE else ATTEMPT2_ATTEMPT
    centers: dict[int, np.ndarray] = {}
    for result, state, seq in zip(results, states, result_seq):
        expected = FULL_BY_SEQ[seq]
        centers[seq] = campaign.validate_result(spec, result, expected, attempt)
        campaign.validate_state(spec, state, result, expected, attempt)
    results_by_seq = {seq: row for seq, row in zip(result_seq, results)}
    expected_closures = tuple(item for item in closure_ranges if item[2] in results_by_seq)
    closure_norms = validate_closure_rows(spec, closures, expected_closures, results_by_seq, attempt)
    return centers, closure_norms, result_seq


def counter_value(row: dict[str, str], field: str) -> int:
    return exact_int(row, field)


def contact_counter_inconsistent(
    probe_result: int, direct: tuple[int, int, int], repeats: tuple[int, int, int]
) -> bool:
    if probe_result == 1:
        return (
            direct[0] != direct[1]
            or repeats[0] != repeats[1]
            or direct[0] + repeats[0] != direct[1] + repeats[1]
            or direct[2] != 1
            or direct[1] < 1
            or repeats[2] != 0
        )
    return direct[2] != 0


def gap_evaluation(
    delta: tuple[int, int, int], prior_extra: int, *, initial: bool = False
) -> tuple[int, bool, bool]:
    combined = prior_extra + delta[0] - delta[2]
    burst = combined > 2
    consistency = (
        delta[0] != delta[1]
        or delta[2] != 0
        or (initial and any(value != 0 for value in delta))
    )
    return combined, burst, consistency


def validate_trace_row(row: dict[str, str]) -> tuple[int, tuple[int, int, int], bool, bool, bool, bool]:
    for field, value in (
        ("schema_version", 1), ("campaign_id", CAMPAIGN),
        ("stage_mode", MODE), ("attempt_id", ATTEMPT),
    ):
        if exact_int(row, field, positive=field in {"schema_version", "campaign_id", "attempt_id"}) != value:
            raise RecoveryError(f"trace {field} mismatch")
    seq = exact_int(row, "global_seq", positive=True)
    if seq not in RECOVERY_SEQUENCE_SET:
        raise RecoveryError(f"trace sequence {seq} is outside recovery contract")
    expected = FULL_BY_SEQ[seq]
    if campaign.angular_error(anchor.number(row, "abs_b_deg"), expected.pose.b_deg) > 0.01:
        raise RecoveryError(f"trace sequence {seq}: B pose mismatch")
    if campaign.angular_error(anchor.number(row, "abs_c_deg"), expected.pose.c_deg) > 0.01:
        raise RecoveryError(f"trace sequence {seq}: C pose mismatch")
    acquisition = exact_int(row, "acquisition_try", positive=True)
    pass_id = exact_int(row, "pass_id", positive=True)
    contact = exact_int(row, "contact_id", positive=True)
    if acquisition not in (1, 2) or pass_id not in (1, 2) or contact not in (1, 2, 3, 4):
        raise RecoveryError(f"trace sequence {seq}: invalid acquisition/pass/contact")

    pre = tuple(counter_value(row, f"pre_{name}_count") for name in ("raw", "mux", "gated"))
    post = tuple(counter_value(row, f"post_{name}_count") for name in ("raw", "mux", "gated"))
    ready = tuple(counter_value(row, f"ready_{name}_count") for name in ("raw", "mux", "gated"))
    if any(value < 0 for value in pre + post + ready):
        raise RecoveryError(f"trace sequence {seq}: negative counter")
    if any(not (pre[i] <= post[i] <= ready[i]) for i in range(3)):
        raise RecoveryError(f"trace sequence {seq}: counter is not monotonic")
    direct = tuple(post[i] - pre[i] for i in range(3))
    repeats = tuple(ready[i] - post[i] for i in range(3))
    for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct):
        if counter_value(row, field) != value:
            raise RecoveryError(f"trace sequence {seq}: {field} mismatch")
    for field, value in zip(("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats):
        if counter_value(row, field) != value:
            raise RecoveryError(f"trace sequence {seq}: {field} mismatch")
    total = tuple(ready[i] - pre[i] for i in range(3))
    if total[0] != total[1]:
        raise RecoveryError(f"trace sequence {seq}: raw and probe-mux edge totals differ")
    if total[2] > total[1]:
        raise RecoveryError(f"trace sequence {seq}: gated edges exceed mux edges")
    extra = total[0] - total[2]
    if counter_value(row, "extra_raw_minus_gated_delta") != extra or extra < 0:
        raise RecoveryError(f"trace sequence {seq}: extra-edge delta mismatch")
    burst = exact_int(row, "burst_flag") == 1
    if exact_int(row, "burst_flag") not in (0, 1) or burst != (extra > 2):
        raise RecoveryError(f"trace sequence {seq}: burst flag mismatch")
    terminal = exact_int(row, "terminal_failure") == 1
    if exact_int(row, "terminal_failure") not in (0, 1):
        raise RecoveryError(f"trace sequence {seq}: invalid terminal flag")
    release_fault = exact_int(row, "release_fault") == 1
    if exact_int(row, "release_fault") not in (0, 1):
        raise RecoveryError(f"trace sequence {seq}: invalid release-fault flag")
    probe_result = exact_int(row, "probe_result")
    if probe_result not in (0, 1) or terminal != (probe_result == 0):
        raise RecoveryError(f"trace sequence {seq}: #5070/terminal contract mismatch")
    travel = anchor.number(row, "travel_mm")
    consistency = contact_counter_inconsistent(probe_result, direct, repeats)
    if exact_int(row, "consistency_fault") not in (0, 1):
        raise RecoveryError(f"trace sequence {seq}: invalid consistency flag")
    if (exact_int(row, "consistency_fault") == 1) != consistency:
        raise RecoveryError(f"trace sequence {seq}: contact consistency flag mismatch")
    maximum = 7.01 if contact == 1 else 6.01
    if probe_result == 1:
        if not 1.0 <= travel <= maximum:
            raise RecoveryError(f"trace sequence {seq}: successful contact travel out of range")
    else:
        commanded = 7.0 if contact == 1 else 6.0
        if abs(travel - commanded) > 0.01:
            raise RecoveryError(f"trace sequence {seq}: terminal no-touch trace mismatch")
    return seq, (acquisition, pass_id, contact), burst, terminal, consistency, release_fault


def validate_success_trace_group(seq: int, keyed: Sequence[tuple[int, int, int]]) -> None:
    tries = sorted({key[0] for key in keyed})
    if tries not in ([1], [1, 2]):
        raise RecoveryError(f"trace sequence {seq}: acquisition tries are not 1 or 1,2")
    expected_order: list[tuple[int, int, int]] = []
    for acquisition in tries:
        rows = [key for key in keyed if key[0] == acquisition]
        pass1 = [(acquisition, 1, contact) for contact in range(1, 5)]
        pass2 = [(acquisition, 2, contact) for contact in range(1, 5)]
        allowed = (pass1, pass1 + pass2)
        if rows not in allowed:
            raise RecoveryError(f"trace sequence {seq}: incomplete pass in acquisition {acquisition}")
        if acquisition == tries[-1] and rows != pass1 + pass2:
            raise RecoveryError(f"trace sequence {seq}: accepted acquisition lacks complete pass 2")
        expected_order.extend(rows)
    if list(keyed) != expected_order:
        raise RecoveryError(f"trace sequence {seq}: pass/contact order mismatch")


def validate_terminal_trace_group(seq: int, keyed: Sequence[tuple[int, int, int]]) -> None:
    if not keyed:
        raise RecoveryError("empty terminal trace group")
    tries = sorted({key[0] for key in keyed})
    if tries not in ([1], [1, 2]):
        raise RecoveryError(f"terminal trace sequence {seq}: invalid acquisition tries")
    previous: tuple[int, int, int] | None = None
    for key in keyed:
        acquisition, pass_id, contact = key
        if previous is not None:
            pa, pp, pc = previous
            allowed_next = []
            if pc < 4:
                allowed_next.append((pa, pp, pc + 1))
            elif pp == 1:
                allowed_next.extend(((pa, 2, 1), (pa + 1, 1, 1)))
            elif pa == 1:
                allowed_next.append((2, 1, 1))
            if key not in allowed_next:
                raise RecoveryError(f"terminal trace sequence {seq}: invalid pass/contact prefix")
        elif key != (1, 1, 1):
            raise RecoveryError(f"terminal trace sequence {seq}: does not start at try1/pass1/contact1")
        previous = key


def validate_gap_terminated_trace_prefix(
    seq: int,
    keyed: Sequence[tuple[int, int, int]],
    terminal_gap_key: tuple[int, int, int, int],
) -> None:
    if terminal_gap_key[0] != seq:
        raise RecoveryError("terminal gap belongs to another recovery sequence")
    validate_terminal_trace_group(seq, list(keyed) + [terminal_gap_key[1:]])


def validate_contact_trace(
    accepted_sequences: Sequence[int],
    *,
    complete: bool,
    terminal_gap_key: tuple[int, int, int, int] | None = None,
    rows_override: Sequence[dict[str, str]] | None = None,
) -> tuple[int, int, str | None]:
    rows = (
        list(rows_override)
        if rows_override is not None
        else read_identity_rows(TRACE, TRACE_FIELDS, MODE, ATTEMPT)
    )
    parsed = [validate_trace_row(row) for row in rows]
    order_index = {seq: index for index, seq in enumerate(RECOVERY_SEQUENCES)}
    if any(order_index[parsed[i][0]] > order_index[parsed[i + 1][0]] for i in range(len(parsed) - 1)):
        raise RecoveryError("trace sequence order moved backwards")
    bursts = sum(int(item[2]) for item in parsed)
    terminals = [
        index for index, item in enumerate(parsed)
        if item[3] or item[2] or item[4] or item[5]
    ]
    if complete and terminals:
        raise RecoveryError("complete recovery contains terminal or retrigger-burst trace")
    if not complete and (len(terminals) > 1 or (terminals and terminals[0] != len(parsed) - 1)):
        raise RecoveryError("partial recovery permits only one final electrical/contact failure")

    by_seq: dict[int, list[tuple[int, int, int]]] = {}
    for seq, key, _, _, _, _ in parsed:
        by_seq.setdefault(seq, []).append(key)
    accepted = list(accepted_sequences)
    for seq in accepted:
        if seq not in by_seq:
            raise RecoveryError(f"accepted sequence {seq} has no contact trace")
        validate_success_trace_group(seq, by_seq.pop(seq))
    terminal_description: str | None = None
    if by_seq:
        if complete or len(by_seq) != 1:
            raise RecoveryError("trace has rows not backed by accepted recovery rows")
        expected_next = RECOVERY_SEQUENCES[len(accepted)] if len(accepted) < len(RECOVERY_SEQUENCES) else None
        seq, keys = next(iter(by_seq.items()))
        if seq != expected_next:
            raise RecoveryError("orphan trace is not the single next terminal recovery sequence")
        if terminals:
            validate_terminal_trace_group(seq, keys)
            final = parsed[-1]
            if final[5]:
                terminal_description = "post-contact release fault"
            elif final[2]:
                terminal_description = "retrigger burst"
            elif final[4]:
                terminal_description = "contact counter inconsistency"
            else:
                terminal_description = "no touch"
        elif terminal_gap_key is not None:
            validate_gap_terminated_trace_prefix(seq, keys, terminal_gap_key)
        else:
            raise RecoveryError("orphan successful contact prefix has no terminal gap fault")
    elif terminals:
        raise RecoveryError("terminal trace cannot belong to an accepted row")
    elif terminal_gap_key is not None:
        if len(accepted) >= len(RECOVERY_SEQUENCES):
            raise RecoveryError("terminal gap exists after a complete recovery")
        expected_next = RECOVERY_SEQUENCES[len(accepted)]
        validate_gap_terminated_trace_prefix(expected_next, [], terminal_gap_key)
    return len(rows), bursts, terminal_description


def trace_key(row: dict[str, str], sequence_field: str) -> tuple[int, int, int, int]:
    return (
        exact_int(row, sequence_field, positive=True),
        exact_int(row, "acquisition_try", positive=True),
        exact_int(row, "pass_id", positive=True),
        exact_int(row, "contact_id", positive=True),
    )


def validate_gap_trace(
    *,
    complete: bool,
    contacts_override: Sequence[dict[str, str]] | None = None,
    gaps_override: Sequence[dict[str, str]] | None = None,
) -> tuple[int, str | None, tuple[int, int, int, int] | None]:
    contacts = (
        list(contacts_override)
        if contacts_override is not None
        else read_identity_rows(TRACE, TRACE_FIELDS, MODE, ATTEMPT)
    )
    gaps = (
        list(gaps_override)
        if gaps_override is not None
        else read_identity_rows(GAP_TRACE, GAP_TRACE_FIELDS, MODE, ATTEMPT)
    )
    contact_by_key = {trace_key(row, "global_seq"): row for row in contacts}
    if len(contact_by_key) != len(contacts):
        raise RecoveryError("contact trace contains a duplicate transaction key")
    gap_keys = [trace_key(row, "next_global_seq") for row in gaps]
    if len(set(gap_keys)) != len(gap_keys):
        raise RecoveryError("gap trace contains a duplicate transaction key")
    contact_keys = [trace_key(row, "global_seq") for row in contacts]
    if gap_keys[: len(contact_keys)] != contact_keys:
        raise RecoveryError("gap/contact traces do not have exact transaction order")
    unmatched = gaps[len(contact_keys) :]
    if complete and unmatched:
        raise RecoveryError("complete recovery contains a gap without a G38 transaction")
    if len(unmatched) > 1:
        raise RecoveryError("partial recovery permits only one final pre-G38 gap fault")

    prior_contact: dict[str, str] | None = None
    terminal: str | None = None
    for index, gap in enumerate(gaps):
        key = gap_keys[index]
        seq = key[0]
        if seq not in RECOVERY_SEQUENCE_SET:
            raise RecoveryError(f"gap trace sequence {seq} is outside recovery contract")
        expected = FULL_BY_SEQ[seq]
        if campaign.angular_error(anchor.number(gap, "abs_b_deg"), expected.pose.b_deg) > 0.01:
            raise RecoveryError(f"gap sequence {seq}: B pose mismatch")
        if campaign.angular_error(anchor.number(gap, "abs_c_deg"), expected.pose.c_deg) > 0.01:
            raise RecoveryError(f"gap sequence {seq}: C pose mismatch")
        prior = tuple(counter_value(gap, f"prior_ready_{name}_count") for name in ("raw", "mux", "gated"))
        current = tuple(counter_value(gap, f"current_pre_{name}_count") for name in ("raw", "mux", "gated"))
        delta = tuple(current[i] - prior[i] for i in range(3))
        if any(value < 0 for value in prior + current) or any(value < 0 for value in delta):
            raise RecoveryError(f"gap sequence {seq}: non-monotonic counter baseline")
        for field, value in zip(("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"), delta):
            if counter_value(gap, field) != value:
                raise RecoveryError(f"gap sequence {seq}: {field} mismatch")
        initial = exact_int(gap, "initial_baseline")
        if initial not in (0, 1) or initial != int(index == 0):
            raise RecoveryError("only the first gap row may use the post-M0 initial baseline")
        prior_extra = counter_value(gap, "prior_contact_extra_delta")
        combined, burst, consistency = gap_evaluation(
            delta, prior_extra, initial=bool(initial)
        )
        if exact_int(gap, "consistency_fault") not in (0, 1):
            raise RecoveryError(f"gap sequence {seq}: invalid consistency flag")
        if (exact_int(gap, "consistency_fault") == 1) != consistency:
            raise RecoveryError(f"gap sequence {seq}: consistency flag mismatch")
        if counter_value(gap, "combined_extra_delta") != combined:
            raise RecoveryError(f"gap sequence {seq}: combined extra delta mismatch")
        if exact_int(gap, "burst_flag") not in (0, 1) or (exact_int(gap, "burst_flag") == 1) != burst:
            raise RecoveryError(f"gap sequence {seq}: burst flag mismatch")
        if prior_contact is None:
            if prior_extra != 0:
                raise RecoveryError("initial post-M0 gap must start with zero prior-contact extra")
        else:
            expected_prior = tuple(counter_value(prior_contact, f"ready_{name}_count") for name in ("raw", "mux", "gated"))
            if prior != expected_prior:
                raise RecoveryError(f"gap sequence {seq}: unaccounted counter change at prior-ready boundary")
            if prior_extra != counter_value(prior_contact, "extra_raw_minus_gated_delta"):
                raise RecoveryError(f"gap sequence {seq}: prior-contact extra delta changed")

        contact = contact_by_key.get(key)
        if contact is not None:
            contact_pre = tuple(counter_value(contact, f"pre_{name}_count") for name in ("raw", "mux", "gated"))
            if current != contact_pre:
                raise RecoveryError(f"gap sequence {seq}: current-pre snapshot differs from contact trace")
            if burst or consistency:
                raise RecoveryError(f"gap sequence {seq}: pre-G38 fault nevertheless has a contact row")
            prior_contact = contact
        else:
            if index != len(gaps) - 1 or not (burst or consistency) or complete:
                raise RecoveryError("unmatched gap is not one final pre-G38 electrical fault")
            if initial and consistency:
                terminal = "initial post-M0 probe activity"
            else:
                terminal = "inter-contact retrigger burst" if burst else "inter-contact counter inconsistency"
    if not gaps and contacts:
        raise RecoveryError("contact trace exists without gap accounting")
    terminal_key = gap_keys[-1] if unmatched else None
    return len(gaps), terminal, terminal_key


def validate_sealed_archive(archive: Path, sums: Path, expected_sums: str, label: str) -> None:
    require_hash(sums, expected_sums)
    listed: dict[str, str] = {}
    for line_number, line in enumerate(sums.read_text(encoding="ascii").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise RecoveryError(f"{label} checksum line {line_number} malformed")
        digest, relative_text = match.groups()
        relative = Path(relative_text)
        normalized = relative.as_posix()
        if relative.is_absolute() or ".." in relative.parts or normalized in listed:
            raise RecoveryError(f"{label} checksum member is unsafe or duplicated")
        listed[normalized] = digest
    actual: set[str] = set()
    for member in archive.rglob("*"):
        if member.is_symlink():
            raise RecoveryError(f"{label} archive contains a symlink: {member}")
        if member.is_file() and member != sums:
            actual.add(member.relative_to(archive).as_posix())
    if actual != set(listed):
        raise RecoveryError(f"{label} archive members differ from sealed checksum set")
    for relative, digest in listed.items():
        require_hash(archive / relative, digest)


def validate_attempt3_archive() -> tuple[dict[int, np.ndarray], np.ndarray]:
    validate_sealed_archive(
        ATTEMPT3_ARCHIVE, ATTEMPT3_SUMS, EXPECTED_ATTEMPT3_SUMS_SHA256,
        "attempt-3",
    )
    for path, digest in (
        (ATTEMPT3_RESULTS, EXPECTED_ATTEMPT3_RESULTS_SHA256),
        (ATTEMPT3_STATE, EXPECTED_ATTEMPT3_STATE_SHA256),
        (ATTEMPT3_CLOSURES, EXPECTED_ATTEMPT3_CLOSURES_SHA256),
        (ATTEMPT3_TRACE, EXPECTED_ATTEMPT3_TRACE_SHA256),
        (ATTEMPT3_GAP_TRACE, EXPECTED_ATTEMPT3_GAP_TRACE_SHA256),
    ):
        require_hash(path, digest)

    original_paths = (
        attempt3.RESULTS, attempt3.STATE, attempt3.CLOSURES,
        attempt3.TRACE, attempt3.GAP_TRACE,
    )
    try:
        attempt3.RESULTS = ATTEMPT3_RESULTS
        attempt3.STATE = ATTEMPT3_STATE
        attempt3.CLOSURES = ATTEMPT3_CLOSURES
        attempt3.TRACE = ATTEMPT3_TRACE
        attempt3.GAP_TRACE = ATTEMPT3_GAP_TRACE
        spec = attempt3.run_spec(
            ATTEMPT3_MODE, ATTEMPT3_RESULTS, ATTEMPT3_STATE,
            ATTEMPT3_CLOSURES, attempt3.RECOVERY_SEQUENCES,
            "sealed attempt-3 partial",
        )
        centers, closures, accepted = attempt3.validate_acquisition(
            spec, attempt3.RECOVERY_SEQUENCES, attempt3.RECOVERY_CLOSURES,
            allow_prefix=True,
        )
        if accepted != list(ATTEMPT3_ACCEPTED_SEQUENCES):
            raise RecoveryError("sealed attempt-3 archive is not the exact 34-row prefix")
        gap_count, gap_terminal, terminal_gap_key = attempt3.validate_gap_trace(
            complete=False
        )
        trace_count, bursts, contact_terminal = attempt3.validate_contact_trace(
            accepted, complete=False, terminal_gap_key=terminal_gap_key,
        )
        if (
            gap_count != 274 or trace_count != 273 or bursts != 0
            or gap_terminal != "inter-contact retrigger burst"
            or contact_terminal is not None
        ):
            raise RecoveryError("sealed attempt-3 terminal-fault contract changed")
    finally:
        (
            attempt3.RESULTS, attempt3.STATE, attempt3.CLOSURES,
            attempt3.TRACE, attempt3.GAP_TRACE,
        ) = original_paths
    return centers, closures


def validate_attempt2_archive() -> tuple[dict[int, np.ndarray], np.ndarray]:
    require_hash(ATTEMPT2_SUMS, EXPECTED_ATTEMPT2_SUMS_SHA256)
    listed: dict[str, str] = {}
    for line_number, line in enumerate(ATTEMPT2_SUMS.read_text(encoding="ascii").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise RecoveryError(f"attempt-2 checksum line {line_number} malformed")
        digest, relative_text = match.groups()
        relative = Path(relative_text)
        if relative.is_absolute() or ".." in relative.parts or relative_text in listed:
            raise RecoveryError("attempt-2 checksum member is unsafe or duplicated")
        listed[relative_text] = digest
    actual: set[str] = set()
    for member in ATTEMPT2_ARCHIVE.rglob("*"):
        if member.is_symlink():
            raise RecoveryError(f"attempt-2 archive contains a symlink: {member}")
        if member.is_file() and member != ATTEMPT2_SUMS:
            actual.add(member.relative_to(ATTEMPT2_ARCHIVE).as_posix())
    if actual != set(listed):
        raise RecoveryError("attempt-2 archive members differ from sealed checksum set")
    for relative, digest in listed.items():
        require_hash(ATTEMPT2_ARCHIVE / relative, digest)
    for path, digest in (
        (ATTEMPT2_RESULTS, EXPECTED_ATTEMPT2_RESULTS_SHA256),
        (ATTEMPT2_STATE, EXPECTED_ATTEMPT2_STATE_SHA256),
        (ATTEMPT2_CLOSURES, EXPECTED_ATTEMPT2_CLOSURES_SHA256),
    ):
        require_hash(path, digest)
    spec = run_spec(ATTEMPT2_MODE, ATTEMPT2_RESULTS, ATTEMPT2_STATE, ATTEMPT2_CLOSURES, ATTEMPT2_SEQUENCES, "immutable attempt-2 partial")
    centers, closures, seq = validate_acquisition(spec, ATTEMPT2_SEQUENCES, ATTEMPT2_CLOSURE_RANGES)
    if seq != list(ATTEMPT2_SEQUENCES):
        raise RecoveryError("attempt-2 archive no longer contains exact sequences 1-48")
    return centers, closures


def centered_metric(values: np.ndarray) -> tuple[float, float]:
    residuals = values - np.mean(values, axis=0)
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms**2))), float(np.max(norms))


def unique_metric(centers: dict[int, np.ndarray]) -> tuple[int, float, float]:
    grouped: dict[tuple[float, float], list[np.ndarray]] = {}
    for seq in range(1, 102):
        pose = FULL_BY_SEQ[seq].pose
        grouped.setdefault((pose.b_deg, pose.c_deg), []).append(centers[seq])
    collapsed = np.vstack([np.mean(values, axis=0) for values in grouped.values()])
    rms, maximum = centered_metric(collapsed)
    return len(grouped), rms, maximum


def composite_diagnostic(
    recovery: dict[int, np.ndarray], attempt3_centers: dict[int, np.ndarray],
    attempt2_centers: dict[int, np.ndarray],
) -> dict[str, float]:
    recovery_open = np.vstack([recovery[seq] for seq in range(1, 10)])
    attempt3_open = np.vstack([attempt3_centers[seq] for seq in range(1, 10)])
    attempt2_open = np.vstack([attempt2_centers[seq] for seq in range(1, 10)])
    translation3 = np.mean(recovery_open, axis=0) - np.mean(attempt3_open, axis=0)
    translation2 = np.mean(recovery_open, axis=0) - np.mean(attempt2_open, axis=0)
    composite: dict[int, np.ndarray] = {}
    for seq in range(1, 102):
        if 10 <= seq <= 44:
            composite[seq] = attempt2_centers[seq] + translation2
        elif 45 <= seq <= 66:
            composite[seq] = attempt3_centers[seq] + translation3
        else:
            composite[seq] = recovery[seq]
    raw = np.vstack([composite[seq] for seq in range(1, 102)])
    raw_rms, raw_maximum = centered_metric(raw)
    unique_count, unique_rms, unique_maximum = unique_metric(composite)
    return {
        "translation2_x": float(translation2[0]),
        "translation2_y": float(translation2[1]),
        "translation2_z": float(translation2[2]),
        "translation2_norm": float(np.linalg.norm(translation2)),
        "translation3_x": float(translation3[0]),
        "translation3_y": float(translation3[1]),
        "translation3_z": float(translation3[2]),
        "translation3_norm": float(np.linalg.norm(translation3)),
        "raw_rms": raw_rms, "raw_max": raw_maximum,
        "unique_count": float(unique_count),
        "unique_rms": unique_rms, "unique_max": unique_maximum,
    }


def write_preflight(path: Path) -> None:
    lines = [
        "# T4 R2 Attempt-4 Recovery Preflight",
        "", "Status: `PASS`", "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- recovery sequences: `1-9 + 67-101` (`{len(RECOVERY_SEQUENCES)}` rows)",
        f"- expected recovery closures: `{len(RECOVERY_CLOSURES)}`",
        f"- program SHA-256: `{sha256(PROGRAM)}`",
        f"- analyzer SHA-256: `{sha256(Path(__file__).resolve())}`",
        f"- sealed attempt-3 checksum-set SHA-256: `{sha256(ATTEMPT3_SUMS)}`",
        f"- recovery INI SHA-256: `{sha256(RECOVERY_INI)}`",
        f"- observation-only counter HAL SHA-256: `{sha256(COUNTER_HAL)}`",
        "", "The sealed attempt-3 34-row prefix and terminal gap-burst evidence validate exactly.",
        "All five attempt-4 outputs are exact header-only files. The in-tree RS274 preview parser passed.",
        "No LinuxCNC, HAL, MDI, or machine-control command is issued by this analyzer.", "",
    ]
    path.write_text("\n".join(lines), encoding="ascii")


def write_result_report(
    path: Path,
    centers: dict[int, np.ndarray],
    closures: np.ndarray,
    trace_count: int,
    gap_count: int,
    bursts: int,
    terminal: str | None,
    composite: dict[str, float] | None,
    *,
    complete: bool,
) -> None:
    ordered = np.vstack([centers[seq] for seq in centers]) if centers else np.empty((0, 3))
    rms, maximum = centered_metric(ordered) if len(ordered) else (math.nan, math.nan)
    status = "RECOVERY CONTRACT PASS" if complete else "VALID PARTIAL RECOVERY"
    lines = [
        "# T4 R2 Attempt-4 Recovery Report", "", f"Status: `{status}`", "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- accepted recovery rows: `{len(centers)} / {len(RECOVERY_SEQUENCES)}`",
        f"- validated closures: `{len(closures)}`",
        f"- worst recovery closure: `{np.max(closures):.6f} mm`" if len(closures) else "- worst recovery closure: `n/a`",
        f"- validated per-G38 contact traces: `{trace_count}`",
        f"- validated inter-contact gap traces: `{gap_count}`",
        f"- retrigger bursts: `{bursts}`",
        f"- terminal trace: `{terminal or 'none'}`",
        f"- standalone centered RMS / max: `{rms:.6f} / {maximum:.6f} mm`",
        "",
        "This is a 44-row recovery acquisition, not a formal same-acquisition 101-row candidate pass.",
    ]
    if composite is not None:
        lines.extend([
            "", "## Composite Diagnostic Only", "",
            "This diagnostic uses attempt-4 sequences 1-9 and 67-101, sealed attempt-3 sequences 45-66, and immutable attempt-2 sequences 10-44.",
            "Attempt-2 and attempt-3 rows are independently translated into the attempt-4 opening-B0 frame.",
            f"- attempt-2 nuisance translation XYZ / norm: `{composite['translation2_x']:.6f}, {composite['translation2_y']:.6f}, {composite['translation2_z']:.6f} / {composite['translation2_norm']:.6f} mm`",
            f"- attempt-3 nuisance translation XYZ / norm: `{composite['translation3_x']:.6f}, {composite['translation3_y']:.6f}, {composite['translation3_z']:.6f} / {composite['translation3_norm']:.6f} mm`",
            f"- composite raw-101 centered RMS / max: `{composite['raw_rms']:.6f} / {composite['raw_max']:.6f} mm`",
            f"- composite equal-{int(composite['unique_count'])} centered RMS / max: `{composite['unique_rms']:.6f} / {composite['unique_max']:.6f} mm`",
            f"- canonical within-acquisition closures: `{COMPOSITE_CLOSURE_COUNT}` (attempt 2 / 3 / 4: `{len(ATTEMPT2_COMPOSITE_CLOSURES)} / {len(ATTEMPT3_COMPOSITE_CLOSURES)} / {len(RECOVERY_CLOSURES)}`)",
            "",
            "The alignment removes one translation per acquisition. It cannot remove probe reseat, spindle, axis-position, or time-dependent changes.",
            "Closures remain valid only inside their source acquisition; the composite creates no cross-acquisition closure evidence.",
            "These metrics are diagnostic and must not be labeled a formal 101-row pass.",
        ])
    lines.append("")
    path.write_text("\n".join(lines), encoding="ascii")


def offline_preflight() -> None:
    validate_recovery_configuration()
    validate_program()
    validate_attempt3_archive()
    run_rs274_preview()
    validate_header_only_files()


def self_test() -> None:
    validate_recovery_configuration()
    validate_program()
    attempt3_centers, _ = validate_attempt3_archive()
    run_rs274_preview()
    assert RECOVERY_SEQUENCES == tuple(range(1, 10)) + tuple(range(67, 102))
    assert len(RECOVERY_SEQUENCES) == 44
    assert len(RECOVERY_CLOSURES) == 19
    assert RECOVERY_CLOSURES[0] == (100, 1, 9)
    assert RECOVERY_CLOSURES[1] == (-45, 67, 71)
    assert RECOVERY_CLOSURES[-1] == (900, 1, 101)
    assert len(ATTEMPT2_COMPOSITE_CLOSURES) == 5
    assert len(ATTEMPT3_COMPOSITE_CLOSURES) == 4
    assert COMPOSITE_CLOSURE_COUNT == 28
    assert len(set(COMPOSITE_CLOSURES)) == COMPOSITE_CLOSURE_COUNT
    assert set(COMPOSITE_CLOSURES) == set(campaign.T4_CLOSURES)
    assert tuple(seq for seq in ATTEMPT3_COMPOSITE_SEQUENCES if seq not in attempt3_centers) == ()
    source_sets = (
        set(range(1, 10)) | set(range(67, 102)),
        set(range(45, 67)),
        set(range(10, 45)),
    )
    assert not any(source_sets[i] & source_sets[j] for i in range(3) for j in range(i + 1, 3))
    assert set.union(*source_sets) == set(range(1, 102))
    synthetic4 = {
        seq: np.array([4000.0 + seq, 2.0 * seq, -seq])
        for seq in RECOVERY_SEQUENCES
    }
    synthetic3 = {
        seq: np.array([3000.0 + seq, 2.0 * seq, -seq])
        for seq in tuple(range(1, 10)) + ATTEMPT3_COMPOSITE_SEQUENCES
    }
    synthetic2 = {
        seq: np.array([2000.0 + seq, 2.0 * seq, -seq])
        for seq in range(1, 45)
    }
    synthetic_composite = composite_diagnostic(synthetic4, synthetic3, synthetic2)
    assert abs(synthetic_composite["translation2_x"] - 2000.0) < 1e-9
    assert abs(synthetic_composite["translation3_x"] - 1000.0) < 1e-9
    assert abs(synthetic_composite["translation2_norm"] - 2000.0) < 1e-9
    assert abs(synthetic_composite["translation3_norm"] - 1000.0) < 1e-9
    text = PROGRAM.read_text(encoding="ascii")
    assert max(len(line) for line in text.splitlines()) <= 225
    finish = attempt2.subroutine_text(text, "tcpc_contact_trace_finish")
    assert finish.find("(LOG,1.0") < finish.find("o<trace_success_burst_abort> if")
    assert "#969 GT 2.0" in finish
    assert "#970 LT 0.5" in finish
    assert "Electrical dropout after retrigger burst" in text
    assert text.count("o<tcpc_probe_counter_guard> call") >= 4
    begin = attempt2.subroutine_text(text, "tcpc_contact_trace_begin")
    assert "#959 = [#953 + [#956 - #958]]" in begin
    assert "#959 GT 2.0" in begin
    assert begin.find("o<tcpc_contact_gap_log> call") < begin.find("(abort, Electrical retrigger burst")
    assert text.find("\nM0\n") < text.find("(Establish the sticky edge baseline only after the operator M0 boundary.)")
    assert gap_evaluation((1, 1, 1), 0) == (0, False, True)
    assert gap_evaluation((1, 1, 0), 2) == (3, True, False)
    assert gap_evaluation((1, 1, 0), 0) == (1, False, False)
    assert gap_evaluation((1, 1, 0), 0, initial=True) == (1, False, True)
    assert not contact_counter_inconsistent(1, (1, 1, 1), (2, 2, 0))
    assert contact_counter_inconsistent(1, (1, 1, 0), (0, 0, 0))
    assert contact_counter_inconsistent(1, (1, 1, 1), (1, 0, 0))
    validate_gap_terminated_trace_prefix(67, [(1, 1, 1)], (67, 1, 1, 2))
    try:
        validate_gap_terminated_trace_prefix(67, [(1, 1, 1)], (67, 1, 1, 3))
    except RecoveryError:
        pass
    else:
        raise AssertionError("non-immediate terminal gap key was accepted")

    initial_gap = {field: "0" for field in GAP_TRACE_FIELDS}
    initial_gap.update(
        schema_version="1", campaign_id=str(CAMPAIGN), stage_mode=str(MODE),
        attempt_id=str(ATTEMPT), next_global_seq="1", abs_b_deg="0",
        abs_c_deg="0", acquisition_try="1", pass_id="1", contact_id="1",
        current_pre_raw_count="1", current_pre_mux_count="1",
        gap_raw_delta="1", gap_mux_delta="1", combined_extra_delta="1",
        consistency_fault="1", initial_baseline="1",
    )
    _, initial_terminal, initial_key = validate_gap_trace(
        complete=False, contacts_override=[], gaps_override=[initial_gap]
    )
    assert initial_terminal == "initial post-M0 probe activity"
    validate_contact_trace(
        [], complete=False, terminal_gap_key=initial_key, rows_override=[]
    )
    broken_initial = dict(initial_gap, consistency_fault="0")
    try:
        validate_gap_trace(
            complete=False, contacts_override=[], gaps_override=[broken_initial]
        )
    except RecoveryError:
        pass
    else:
        raise AssertionError("initial post-M0 edge activity was accepted as clear")

    release_row = {field: "0" for field in TRACE_FIELDS}
    release_row.update(
        schema_version="1", campaign_id=str(CAMPAIGN), stage_mode=str(MODE),
        attempt_id=str(ATTEMPT), global_seq="1", abs_b_deg="0",
        abs_c_deg="0", acquisition_try="1", pass_id="1", contact_id="1",
        post_raw_count="1", post_mux_count="1", post_gated_count="1",
        ready_raw_count="1", ready_mux_count="1", ready_gated_count="1",
        probe_result="1", travel_mm="5", raw_delta="1", mux_delta="1",
        gated_delta="1", release_fault="1",
    )
    _, _, release_terminal = validate_contact_trace(
        [], complete=False, rows_override=[release_row]
    )
    assert release_terminal == "post-contact release fault"
    try:
        validate_contact_trace([], complete=True, rows_override=[release_row])
    except RecoveryError:
        pass
    else:
        raise AssertionError("release-fault trace was accepted as a complete recovery")

    broken = text.replace("#969 GT 2.0", "#969 GT 3.0", 1)
    if broken == text:
        raise AssertionError("failed to construct burst-threshold mutation")
    try:
        if "#969 GT 2.0" not in broken:
            raise RecoveryError("burst threshold changed")
    except RecoveryError:
        pass
    else:
        raise AssertionError("burst threshold mutation was accepted")

    broken_gap = text.replace("#959 GT 2.0", "#959 GT 3.0", 1)
    if broken_gap == text:
        raise AssertionError("failed to construct inter-contact threshold mutation")
    try:
        if "#959 GT 2.0" not in broken_gap:
            raise RecoveryError("inter-contact burst threshold changed")
    except RecoveryError:
        pass
    else:
        raise AssertionError("inter-contact burst threshold mutation was accepted")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="require pristine header-only recovery outputs")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--partial", action="store_true", help="validate an exact recovery prefix and at most one terminal trace")
    parser.add_argument("--composite", action="store_true", help="add explicitly diagnostic attempt2/attempt3/attempt4 composite metrics")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("attempt-4 recovery self-test: PASS")
            return 0
        if args.preflight:
            offline_preflight()
            report = args.report or DEFAULT_PREFLIGHT_REPORT
            write_preflight(report)
            print("attempt-4 recovery preflight: PASS")
            print(f"report: {report}")
            return 0

        validate_recovery_configuration()
        validate_program()
        attempt3_centers, _ = validate_attempt3_archive()
        spec = run_spec(MODE, RESULTS, STATE, CLOSURES, RECOVERY_SEQUENCES, "attempt-4 recovery")
        centers, closures, accepted = validate_acquisition(
            spec, RECOVERY_SEQUENCES, RECOVERY_CLOSURES, allow_prefix=args.partial,
        )
        complete = accepted == list(RECOVERY_SEQUENCES)
        if not args.partial and not complete:
            raise RecoveryError("recovery is incomplete; use --partial only for preserved failure evidence")
        gap_count, gap_terminal, terminal_gap_key = validate_gap_trace(complete=complete)
        trace_count, bursts, terminal = validate_contact_trace(
            accepted, complete=complete, terminal_gap_key=terminal_gap_key,
        )
        if gap_terminal is not None:
            if terminal is not None:
                raise RecoveryError("partial recovery contains both contact and gap terminal faults")
            terminal = gap_terminal
        if args.partial and not complete and terminal is None:
            raise RecoveryError("partial recovery requires one structured terminal fault")
        if complete and (bursts or terminal):
            raise RecoveryError("complete recovery has electrical/contact trace failures")
        composite = None
        if args.composite:
            if not complete:
                raise RecoveryError("composite diagnostic requires the complete 44-row recovery")
            attempt2_centers, _ = validate_attempt2_archive()
            composite = composite_diagnostic(centers, attempt3_centers, attempt2_centers)
        report = args.report or DEFAULT_RESULT_REPORT
        write_result_report(report, centers, closures, trace_count, gap_count, bursts, terminal, composite, complete=complete)
        print(f"attempt-4 recovery validation: {'PASS' if complete else 'VALID PARTIAL'}")
        if composite is not None:
            print("composite diagnostic: GENERATED (not a formal 101-row pass)")
        print(f"report: {report}")
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, anchor.ValidationError) as exc:
        print(f"attempt-4 recovery validation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
