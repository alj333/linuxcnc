#!/usr/bin/env python3
"""Preflight and validate the baseline-only T3 R2-transfer exploration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Iterable, Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import analyze_tcpc_relocated_sphere_reachability as reach
import analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt5_recovery as a5


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CAMPAIGN = 2026082601
MODE = 30
ATTEMPT = 1
TOOL = 3
TOOL_LENGTH = 128.606729
CALIBRATION_OFFSET = 0.117658
EFFECTIVE_RADIUS = 17.882342

PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc"
FORMAL_T3_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t3_verification.ngc"
A5_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_attempt5_recovery_verification.ngc"
BASE_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini"
RUN_INI = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t3_exploratory_a1.ini"
BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
COUNTER_HAL = HERE / "tcpc_probe_attempt3_edge_counters.hal"
TOOL_TABLE = HERE.parent / "5th_axis_xyzbc_ssi_probe_basic/tool.tbl"
R2_OVERLAY = HERE / "tcpc_relocated_sphere_t4_candidate_r2.hal"
REACH_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_reachability.py"

PREFIX = "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1"
RESULTS = HERE / f"{PREFIX}-results.csv"
STATE = HERE / f"{PREFIX}-state.csv"
CLOSURES = HERE / f"{PREFIX}-closures.csv"
TRACE = HERE / f"{PREFIX}-contact-trace.csv"
GAP_TRACE = HERE / f"{PREFIX}-gap-trace.csv"

T4_ARCHIVE = HERE / "calibration_runs/20260825_0756_campaign04_t4_primary_attempt1_complete"
T4_RESULTS = T4_ARCHIVE / "tcpc-relocated-sphere-t4-primary-results.csv"
R2_ARCHIVE = HERE / "calibration_runs/20260825_0909_campaign04_t4_fit_r2_frozen"
R2_RESIDUALS = R2_ARCHIVE / "tcpc-relocated-sphere-t4-fit-r2-residuals.csv"
A5_ANALYSIS = HERE / "calibration_runs/20260826_0902_campaign04_t4_candidate_r2_attempt5_complete_analysis"

DEFAULT_PREFLIGHT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_PREFLIGHT_REPORT.md"
DEFAULT_RESULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_REPORT.md"

EXPECTED_HASHES = {
    PROGRAM: "90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5",
    FORMAL_T3_PROGRAM: "ceaf8895626a2b3030fb1d36f5575f7ff5c3850630178303795279e9be483c18",
    A5_PROGRAM: "779f18f20d70ada82bea0f06caf91f5111dfa746ea4ae2a5bab3da55abf0e6b6",
    BASE_INI: "afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519",
    RUN_INI: "347a0bfb9f616875fa7c68a24d9134269a0e4dce967deca11b21d278a2b49a47",
    BASE_HAL: "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778",
    COUNTER_HAL: "6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34",
    TOOL_TABLE: "e7d459a2c875f56f2fcdeeefd3c8fa889809a5545cd3eab1309176c8c623092d",
    R2_OVERLAY: "0bfefdb068bb353282fc41067d5cd7464f76ea6a4f520204f0ab5c914ee1673a",
    REACH_ANALYZER: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    T4_RESULTS: "70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468",
    T4_ARCHIVE / "SHA256SUMS": "6a7989720963f09277dd623fff57f06a0b0ceedb0252fcaf9258544783d4e7af",
    R2_ARCHIVE / "SHA256SUMS": "602cf8bf0bef86fcb4e80f1b1b7323a8a7608fc2c7baad35e3d2ed909d759835",
    R2_RESIDUALS: "8de7e98a4767eba6545ee3e6f3a0688bf56e43427153bea79c08c4787f59ade1",
    A5_ANALYSIS / "SHA256SUMS": "3b155b67b718509d3228c1c2517ccfd7a4ca4a4d12ba98b9105d311c27de966c",
}

HEADER_HASHES = {
    RESULTS: "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    STATE: "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    CLOSURES: "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    TRACE: "df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8",
    GAP_TRACE: "e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2",
}

EXPECTED_ROWS = campaign.expected_rows(reach.verification_grid(), campaign.T3_RANGES)
EXPECTED_BY_SEQ = {row.seq: row for row in EXPECTED_ROWS}
SEQUENCES = tuple(range(1, 32))
CLOSURE_CONTRACT = campaign.T3_CLOSURES

T4_EQ_BASE = (0.278753177, 0.601154593)
T4_EQ_R2 = (0.090608971, 0.177367821)
T4_RAW_BASE = (0.245103389, 0.641222515)
T4_RAW_R2 = (0.098503727, 0.190599148)


class T3Error(ValueError):
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
        raise T3Error(f"SHA-256 changed for {path}: {actual}, expected {expected}")


def canonical_pose(b_deg: float, c_deg: float) -> tuple[int, int]:
    b = int(round(b_deg))
    c = int(round(c_deg)) % 360
    if abs(b_deg - b) > 0.01 or campaign.angular_error(c_deg, c) > 0.01:
        raise T3Error(f"non-contract pose B{b_deg} C{c_deg}")
    return b, c


def expected_pose_keys() -> list[tuple[int, int]]:
    return [canonical_pose(row.pose.b_deg, row.pose.c_deg) for row in EXPECTED_ROWS]


def extract_sub(text: str, name: str) -> str:
    start_token = f"o<{name}> sub"
    end_token = f"o<{name}> endsub"
    start = text.find(start_token)
    end = text.find(end_token)
    if start < 0 or end < start:
        raise T3Error(f"missing subroutine {name}")
    end = text.find("\n", end)
    return text[start:] if end < 0 else text[start : end + 1]


def normalized_a5_block(text: str) -> str:
    return (
        text.replace("tcpc_candidate_pin_guard", "tcpc_baseline_pin_guard")
        .replace(
            "tcpc-relocated-sphere-t4-candidate-r2-attempt5-recovery",
            PREFIX,
        )
    )


def validate_config() -> None:
    for path, expected in EXPECTED_HASHES.items():
        require_hash(path, expected)

    base = BASE_INI.read_text(encoding="ascii")
    derived = RUN_INI.read_text(encoding="ascii")
    normalized = derived.splitlines()
    expected_prefix = [
        "# DIAGNOSTIC ONLY: baseline-correction T3 R2-transfer exploratory attempt 1.",
        "# Derived from the hash-locked task-capture INI. The sole functional addition",
        "# is the observation-only raw/muxed/gated probe edge counter layer. No R2",
        "# candidate overlay is loaded and production/base files remain unchanged.",
    ]
    if normalized[:4] != expected_prefix:
        raise T3Error("derived INI diagnostic declaration changed")
    normalized = normalized[4:]
    try:
        title_index = normalized.index("TITLE = 5th Axis XYZBC SSI TCPC T3 Exploratory A1")
        counter_index = normalized.index("HALFILE = tcpc_probe_attempt3_edge_counters.hal")
    except ValueError as exc:
        raise T3Error("derived INI title or counter HAL is missing") from exc
    normalized[title_index] = "TITLE = 5th Axis XYZBC SSI TCPC Probe Basic"
    normalized.pop(counter_index)
    if "\n".join(normalized) + "\n" != base:
        raise T3Error("derived INI differs from baseline beyond declaration/title/counter HAL")
    halfiles = [line.strip() for line in derived.splitlines() if line.strip().startswith("HALFILE")]
    if halfiles.count("HALFILE = tcpc_probe_attempt3_edge_counters.hal") != 1:
        raise T3Error("counter HAL must be loaded exactly once")
    if any("candidate_r2" in line or line.endswith("candidate_r2.hal") for line in halfiles):
        raise T3Error("R2 candidate overlay is present in the T3 INI")

    tool_line = next((line for line in TOOL_TABLE.read_text(encoding="ascii").splitlines() if line.startswith("T3 ")), "")
    if "Z+128.606729" not in tool_line or "D+6.000000" not in tool_line:
        raise T3Error("tool-table T3/H3 identity changed")


def validate_program() -> None:
    text = PROGRAM.read_text(encoding="ascii")
    formal = FORMAL_T3_PROGRAM.read_text(encoding="ascii")
    source = A5_PROGRAM.read_text(encoding="ascii")

    if text.count("\nM0\n") != 1:
        raise T3Error("runner must contain exactly one standalone M0")
    before_hold = text.split("\nM0\n", 1)[0]
    before_hold = re.sub(
        r"(?ms)^o<[^>]+> sub\s*$.*?^o<[^>]+> endsub\s*$",
        "",
        before_hold,
    )
    motion = re.compile(r"(?:^|\s)G(?:0?0|0?1|0?2|0?3|38(?:\.\d+)?)\b", re.IGNORECASE)
    executable_before_hold = "\n".join(
        line.split("(", 1)[0] for line in before_hold.splitlines()
    )
    if motion.search(executable_before_hold):
        raise T3Error("axis/rotary/probe motion exists before the sole M0")

    required = (
        "#717 = 0.117658",
        "#516 = 128.606729",
        "#707 = 31.0",
        "#711 = 30.0",
        "#715 = 2026082601.0",
        "#716 = 1.0",
        "#727 = 1.0",
        "o<run_relocated_t3_exploratory> if [ABS[#711 - 30.0] LT 0.1]",
        "o<primary_sequence_complete> if [[ABS[#726 - 31.0] GT 0.000001] OR [ABS[#788 - #707] GT 0.000001]]",
    )
    for token in required:
        if text.count(token) != 1:
            raise T3Error(f"runner identity token changed: {token}")
    for stale in (
        "tcpc-relocated-sphere-t4-candidate-r2-attempt5-recovery-results.csv",
        "tcpc-relocated-sphere-t3-verification-results.csv",
        "tcpc_relocated_sphere_t4_candidate_r2.hal",
    ):
        if stale in text:
            raise T3Error(f"runner contains stale path/name: {stale}")
    if re.search(r"\b(?:setp|halcmd)\b", text, re.IGNORECASE):
        raise T3Error("runner contains a HAL/coefficient write command")

    body = text.split("o<run_relocated_t3_exploratory> if", 1)[1].split(
        "o<run_relocated_t3_exploratory> endif", 1
    )[0]
    calls = re.findall(
        r"o<(tcpc_primary_b0_sweep|tcpc_primary_tilt_block|tcpc_measure_pose)> call[^\n]*",
        body,
    )
    if calls != [
        "tcpc_primary_b0_sweep",
        "tcpc_primary_tilt_block",
        "tcpc_primary_tilt_block",
        "tcpc_measure_pose",
        "tcpc_primary_tilt_block",
        "tcpc_primary_tilt_block",
        "tcpc_primary_b0_sweep",
    ]:
        raise T3Error("mode-30 body call order changed")
    ordered_calls = (
        "o<tcpc_primary_b0_sweep> call [100.0]",
        "o<tcpc_primary_tilt_block> call [45.0] [45.0]",
        "o<tcpc_primary_tilt_block> call [-45.0] [-45.0]",
        "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]",
        "o<tcpc_primary_tilt_block> call [90.0] [90.0]",
        "o<tcpc_primary_tilt_block> call [-90.0] [-90.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
    )
    positions = [body.find(item) for item in ordered_calls]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise T3Error("mode-30 pose blocks changed")

    for name in (
        "tcpc_pair_coordinate_guard",
        "tcpc_pair_hold_position_guard",
        "tcpc_pair_selector_guard",
        "tcpc_pair_live_guard",
        "tcpc_pair_release_guard",
        "tcpc_probe_counter_guard",
        "tcpc_contact_gap_log",
        "tcpc_contact_trace_begin",
        "tcpc_contact_trace_post",
        "tcpc_contact_trace_finish",
        "tcpc_pair_probe_ready_guard",
        "tcpc_vector_sphere_pass4",
        "tcpc_measure_pose",
        "tcpc_baseline_return_top_clear",
    ):
        if extract_sub(text, name) != normalized_a5_block(extract_sub(source, name)):
            raise T3Error(f"Attempt-5 implementation block changed: {name}")
    for name in (
        "tcpc_primary_outer_reference",
        "tcpc_primary_b0_sweep",
        "tcpc_primary_tilt_block",
        "tcpc_baseline_return_top_clear",
    ):
        if extract_sub(text, name) != extract_sub(formal, name):
            raise T3Error(f"formal T3 pose/closure block changed: {name}")

    baseline_guard = extract_sub(text, "tcpc_baseline_pin_guard")
    expected_values = (
        "charm.cos.x]>]",
        "charm.cos.y]>]",
        "charm.cos.z]>]",
        "bharm-m.sin.x]> - 0.015577123",
        "bharm-m.sin.y]> - 0.060508594",
        "bharm-m.sin.z]> - 0.312123080",
        "bharm-m.sin2.x]> + 0.013271805",
        "bharm-m.sin2.y]> - 0.050707231",
        "bharm-m.sin2.z]> + 0.156014210",
        "bcross.sinb-sinc.x]> + 0.006371196",
        "bcross.sinb-sinc.y]> - 0.325723886",
        "bcross.sinb-sinc.z]> - 0.130042953",
        "bcross.omcb-sin2c.x]> + 0.017723675",
        "bcross.omcb-sin2c.y]> + 0.255875638",
        "bcross.omcb-sin2c.z]> + 0.055414262",
        "bcross.sinb-cos2c.x]>]",
        "bcross.sinb-cos2c.y]>]",
        "bcross.sinb-cos2c.z]>]",
        "bmid.base.x]>]", "bmid.base.y]>]", "bmid.base.z]>]",
        "bmid.cosc.x]>]", "bmid.cosc.y]>]", "bmid.cosc.z]>]",
        "bmid.sinc.x]>]", "bmid.sinc.y]>]", "bmid.sinc.z]>]",
        "bmid.cos2c.x]>]", "bmid.cos2c.y]>]", "bmid.cos2c.z]>]",
    )
    if any(token not in baseline_guard for token in expected_values):
        raise T3Error("one or more baseline pin totals/signs changed")
    if baseline_guard.count("o<cand") != 60:
        raise T3Error("baseline guard is not exactly 30 balanced pin checks")

    if len(text.splitlines()) != 1555 or max(map(len, text.splitlines())) > 225:
        raise T3Error("runner line-count or maximum-line contract changed")
    balances = (
        (r"^\s*o<[^>]+>\s+sub\s*$", r"^\s*o<[^>]+>\s+endsub\s*$", "sub/endsub"),
        (r"^\s*o<[^>]+>\s+if\b", r"^\s*o<[^>]+>\s+endif\s*$", "if/endif"),
        (r"^\s*o<[^>]+>\s+while\b", r"^\s*o<[^>]+>\s+endwhile\s*$", "while/endwhile"),
    )
    for opening, closing, label in balances:
        if len(re.findall(opening, text, re.MULTILINE)) != len(re.findall(closing, text, re.MULTILINE)):
            raise T3Error(f"unbalanced O-word {label}")


def validate_header_only() -> None:
    contracts = {
        RESULTS: anchor.RESULT_FIELDS,
        STATE: anchor.STATE_FIELDS,
        CLOSURES: campaign.CLOSURE_FIELDS,
        TRACE: a5.TRACE_FIELDS,
        GAP_TRACE: a5.GAP_TRACE_FIELDS,
    }
    for path, fields in contracts.items():
        require_hash(path, HEADER_HASHES[path])
        with path.open(newline="", encoding="ascii") as stream:
            rows = list(csv.reader(stream))
        if rows != [list(fields)]:
            raise T3Error(f"{path.name} is not the exact fresh header")


def controller_running() -> bool:
    names = {"linuxcnc", "linuxcncsvr", "milltask", "milltask.bin", "rtapi_app"}
    for comm in Path("/proc").glob("[0-9]*/comm"):
        try:
            if comm.read_text(encoding="ascii").strip() in names:
                return True
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            continue
    return False


def run_offline_parsers() -> str:
    if controller_running():
        raise T3Error("refusing standalone RS274/reachability preflight while LinuxCNC is running")
    with tempfile.TemporaryDirectory(prefix="tcpc-t3-preflight-") as directory:
        root = Path(directory)
        env = os.environ.copy()
        env["HOME"] = str(root / "home")
        Path(env["HOME"]).mkdir()
        parsed = subprocess.run(
            [str(REPO_ROOT / "bin/rs274"), "-g", str(PROGRAM)],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        if parsed.returncode != 0:
            raise T3Error(f"isolated-HOME RS274 failed:\n{parsed.stdout[-2000:]}")
        reached = subprocess.run(
            [
                sys.executable,
                str(REACH_ANALYZER),
                "--report", str(root / "reach.md"),
                "--details", str(root / "reach.csv"),
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
            check=False,
        )
        if reached.returncode != 0 or "reachability analysis: PASS" not in reached.stdout:
            raise T3Error(f"configured-limit reachability failed:\n{reached.stdout[-2000:]}")
    return "isolated-HOME RS274 PASS; configured-limit replay PASS"


def offline_preflight(report: Path) -> None:
    validate_config()
    validate_program()
    validate_header_only()
    parser_status = run_offline_parsers()
    lines = [
        "# T3 R2-Transfer Exploratory Preflight",
        "",
        "- status: `PASS`",
        "- disposition: `R2 NOT ACCEPTED`",
        f"- campaign/mode/attempt: `{CAMPAIGN}/{MODE}/{ATTEMPT}`",
        f"- runner SHA-256: `{sha256(PROGRAM)}`",
        f"- diagnostic INI SHA-256: `{sha256(RUN_INI)}`",
        f"- analyzer SHA-256 at execution: `{sha256(Path(__file__))}`",
        f"- outputs: five exact header-only files",
        f"- pose/closure contract: `{len(EXPECTED_ROWS)} / {len(CLOSURE_CONTRACT)}`",
        f"- parser/replay: `{parser_status}`",
        "- motion boundary: one pre-motion M0; no intermediate holds",
        "- implementation: Attempt-5 probe transaction/filter/retry/transit blocks match",
        "- configuration: baseline plus observation counters only; R2 overlay absent",
        "",
        "Configured-limit replay does not release physical T3 body, holder, cable,",
        "sphere-post, sphere, or fixture clearance. The operator must confirm those",
        "at the sole initial M0. Loading the file authorizes no motion.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")


def patched_validation() -> tuple[dict[int, np.ndarray], np.ndarray, int, int, int]:
    saved_campaign = campaign.CAMPAIGN
    saved = {
        "CAMPAIGN": a5.CAMPAIGN,
        "MODE": a5.MODE,
        "ATTEMPT": a5.ATTEMPT,
        "FULL_BY_SEQ": a5.FULL_BY_SEQ,
        "RECOVERY_SEQUENCES": a5.RECOVERY_SEQUENCES,
        "RECOVERY_SEQUENCE_SET": a5.RECOVERY_SEQUENCE_SET,
        "TRACE": a5.TRACE,
        "GAP_TRACE": a5.GAP_TRACE,
    }
    try:
        campaign.CAMPAIGN = CAMPAIGN
        a5.CAMPAIGN = CAMPAIGN
        a5.MODE = MODE
        a5.ATTEMPT = ATTEMPT
        a5.FULL_BY_SEQ = EXPECTED_BY_SEQ
        a5.RECOVERY_SEQUENCES = SEQUENCES
        a5.RECOVERY_SEQUENCE_SET = set(SEQUENCES)
        a5.TRACE = TRACE
        a5.GAP_TRACE = GAP_TRACE
        spec = campaign.RunSpec(
            "T3 R2-transfer exploratory",
            TOOL,
            MODE,
            TOOL_LENGTH,
            CALIBRATION_OFFSET,
            EFFECTIVE_RADIUS,
            RESULTS,
            STATE,
            CLOSURES,
            EXPECTED_ROWS,
            CLOSURE_CONTRACT,
        )
        centers, closure_norms, accepted = a5.validate_acquisition(
            spec, SEQUENCES, CLOSURE_CONTRACT
        )
        if accepted != list(SEQUENCES):
            raise T3Error("accepted sequence contract changed")
        gap_count, terminal_gap, terminal_key = a5.validate_gap_trace(complete=True)
        contact_count, bursts, terminal_contact = a5.validate_contact_trace(
            SEQUENCES, complete=True, terminal_gap_key=terminal_key
        )
        if terminal_gap or terminal_contact or bursts:
            raise T3Error("complete T3 acquisition contains a terminal electrical fault")
        return centers, closure_norms, contact_count, gap_count, bursts
    finally:
        campaign.CAMPAIGN = saved_campaign
        for name, value in saved.items():
            setattr(a5, name, value)


def centered(values: np.ndarray) -> np.ndarray:
    return values - values.mean(axis=0)


def metric(values: np.ndarray) -> tuple[float, float]:
    norms = np.linalg.norm(centered(values), axis=1)
    return float(math.sqrt(np.mean(norms * norms))), float(np.max(norms))


def unique_means(values: np.ndarray, keys: Sequence[tuple[int, int]]) -> tuple[list[tuple[int, int]], np.ndarray]:
    order: list[tuple[int, int]] = []
    grouped: dict[tuple[int, int], list[np.ndarray]] = {}
    for key, value in zip(keys, values):
        if key not in grouped:
            order.append(key)
            grouped[key] = []
        grouped[key].append(value)
    return order, np.array([np.mean(grouped[key], axis=0) for key in order])


def read_r2_delta_map(keys: Iterable[tuple[int, int]]) -> dict[tuple[int, int], np.ndarray]:
    wanted = set(keys)
    found: dict[tuple[int, int], np.ndarray] = {}
    with R2_RESIDUALS.open(newline="", encoding="ascii") as stream:
        for row in csv.DictReader(stream):
            key = canonical_pose(float(row["abs_b_deg"]), float(row["abs_c_deg"]))
            if key not in wanted:
                continue
            delta = np.array([
                float(row["candidate_delta_x_mm"]),
                float(row["candidate_delta_y_mm"]),
                float(row["candidate_delta_z_mm"]),
            ])
            if key in found and np.linalg.norm(found[key] - delta) > 1e-9:
                raise T3Error(f"frozen R2 delta differs across duplicate pose {key}")
            found[key] = delta
    if set(found) != wanted:
        raise T3Error("frozen R2 residual table does not cover every T3 pose")
    return found


def matching_t4_raw(keys: Sequence[tuple[int, int]]) -> np.ndarray:
    queues: dict[tuple[int, int], list[np.ndarray]] = {}
    with T4_RESULTS.open(newline="", encoding="ascii") as stream:
        for row in csv.DictReader(stream):
            key = canonical_pose(float(row["abs_b_deg"]), float(row["abs_c_deg"]))
            queues.setdefault(key, []).append(np.array([
                float(row["center_abs_x_mm"]),
                float(row["center_abs_y_mm"]),
                float(row["center_abs_z_mm"]),
            ]))
    selected: list[np.ndarray] = []
    used: dict[tuple[int, int], int] = {}
    for key in keys:
        index = used.get(key, 0)
        if key not in queues or index >= len(queues[key]):
            raise T3Error(f"sealed T4 primary lacks matching occurrence for {key}")
        selected.append(queues[key][index])
        used[key] = index + 1
    return np.array(selected)


def subgroup_rms(values: np.ndarray, indices: Sequence[int]) -> float:
    residuals = centered(values)
    norms = np.linalg.norm(residuals[list(indices)], axis=1)
    return float(math.sqrt(np.mean(norms * norms)))


def analyze_results(report: Path) -> None:
    validate_config()
    validate_program()
    centers, closure_norms, contacts, gaps, bursts = patched_validation()
    raw = np.array([centers[seq] for seq in SEQUENCES])
    raw_keys = expected_pose_keys()
    unique_keys, unique = unique_means(raw, raw_keys)
    if len(unique_keys) != 20:
        raise T3Error("31-row contract did not reduce to exactly 20 unique poses")
    deltas = read_r2_delta_map(unique_keys)
    raw_cf = np.array([value + deltas[key] for value, key in zip(raw, raw_keys)])
    unique_cf = np.array([value + deltas[key] for value, key in zip(unique, unique_keys)])

    raw_base_metric = metric(raw)
    raw_cf_metric = metric(raw_cf)
    eq_base_metric = metric(unique)
    eq_cf_metric = metric(unique_cf)

    t4_raw = matching_t4_raw(raw_keys)
    t4_keys, t4_unique = unique_means(t4_raw, raw_keys)
    if t4_keys != unique_keys:
        raise T3Error("T3/T4 matching-grid unique pose order differs")
    for actual, frozen, label in (
        (metric(t4_raw), T4_RAW_BASE, "raw31 baseline"),
        (metric(t4_unique), T4_EQ_BASE, "equal20 baseline"),
    ):
        if max(abs(actual[i] - frozen[i]) for i in range(2)) > 1e-9:
            raise T3Error(f"sealed T4 {label} comparator changed: {actual}")
    mismatch = centered(unique) - centered(t4_unique)
    mismatch_norms = np.linalg.norm(mismatch, axis=1)
    mismatch_metric = (
        float(math.sqrt(np.mean(mismatch_norms * mismatch_norms))),
        float(np.max(mismatch_norms)),
    )

    base_residual = centered(unique)
    cf_residual = centered(unique_cf)
    base_norm = np.linalg.norm(base_residual, axis=1)
    cf_norm = np.linalg.norm(cf_residual, axis=1)
    worsening = cf_norm - base_norm
    plus = [i for i, key in enumerate(unique_keys) if key[0] > 0]
    minus = [i for i, key in enumerate(unique_keys) if key[0] < 0]
    bzero = [i for i, key in enumerate(unique_keys) if key[0] == 0]
    plus_improvement = 1.0 - subgroup_rms(unique_cf, plus) / subgroup_rms(unique, plus)
    minus_improvement = 1.0 - subgroup_rms(unique_cf, minus) / subgroup_rms(unique, minus)
    bzero_worsening = subgroup_rms(unique_cf, bzero) - subgroup_rms(unique, bzero)
    rms_improvement = eq_base_metric[0] - eq_cf_metric[0]
    max_improvement = eq_base_metric[1] - eq_cf_metric[1]
    gates = {
        "equal20 RMS improvement": rms_improvement >= 0.010 and rms_improvement / eq_base_metric[0] >= 0.10,
        "equal20 max improvement": max_improvement >= 0.020 and max_improvement / eq_base_metric[1] >= 0.10,
        "positive-B RMS improvement": plus_improvement >= 0.10,
        "negative-B RMS improvement": minus_improvement >= 0.10,
        "B0 RMS non-worsening": bzero_worsening <= 0.010,
        "maximum pose worsening": float(np.max(worsening)) <= 0.075,
        "equal20 ceiling": eq_cf_metric[0] <= 0.120 and eq_cf_metric[1] <= 0.280,
        "raw31 ceiling": raw_cf_metric[0] <= 0.120 and raw_cf_metric[1] <= 0.280,
    }
    if all(gates.values()):
        classification = "SUPPORTIVE"
    elif eq_cf_metric[0] < eq_base_metric[0]:
        classification = "MIXED"
    else:
        classification = "ADVERSE"

    lines = [
        "# T3 R2-Transfer Exploratory Report",
        "",
        "## R2 NOT ACCEPTED",
        "",
        f"- exploratory classification: `{classification}`",
        f"- acquisition contract: `31 / 31 / 14` results/state/closures",
        f"- contact/gap trace rows: `{contacts} / {gaps}`; burst faults: `{bursts}`",
        f"- maximum closure: `{float(np.max(closure_norms)):.6f} mm`",
        f"- equal-20 baseline RMS/max: `{eq_base_metric[0]:.9f} / {eq_base_metric[1]:.9f} mm`",
        f"- equal-20 R2 counterfactual RMS/max: `{eq_cf_metric[0]:.9f} / {eq_cf_metric[1]:.9f} mm`",
        f"- raw-31 baseline RMS/max: `{raw_base_metric[0]:.9f} / {raw_base_metric[1]:.9f} mm`",
        f"- raw-31 R2 counterfactual RMS/max: `{raw_cf_metric[0]:.9f} / {raw_cf_metric[1]:.9f} mm`",
        f"- centered T3-minus-T4 equal-20 mismatch RMS/max: `{mismatch_metric[0]:.9f} / {mismatch_metric[1]:.9f} mm`",
        f"- maximum unique-pose worsening: `{float(np.max(worsening)):.9f} mm` at `{unique_keys[int(np.argmax(worsening))]}`",
        "",
        "## Frozen Gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'}: {name}" for name, passed in gates.items())
    lines += [
        "",
        "The candidate values above are an offline counterfactual formed by adding",
        "the sealed T4 R2 pose deltas to baseline T3 measurements. R2 was not loaded",
        "for this acquisition. No T3 coefficient, rotation, scale, row deletion, or",
        "alignment beyond one global translation was fitted.",
        "",
        "This exploratory classification cannot cure the failed T4 B+90/C180 gate,",
        "accept R2, release production, or authorize a calibration parameter change.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="ascii")


def self_test() -> None:
    if len(EXPECTED_ROWS) != 31 or len(CLOSURE_CONTRACT) != 14:
        raise T3Error("pose/closure constants changed")
    keys = expected_pose_keys()
    if len(dict.fromkeys(keys)) != 20:
        raise T3Error("unique-pose contract changed")
    synthetic = np.array([[float(i), float(i % 3), -float(i % 5)] for i in range(31)])
    shifted = synthetic + np.array([1000.0, -300.0, 25.0])
    if max(abs(metric(synthetic)[i] - metric(shifted)[i]) for i in range(2)) > 1e-10:
        raise T3Error("single-translation metric is not translation invariant")
    order, means = unique_means(synthetic, keys)
    if order != list(dict.fromkeys(keys)) or len(means) != 20:
        raise T3Error("unique-pose grouping changed")
    if a5.gap_evaluation((3, 3, 0), 0)[1] is not True:
        raise T3Error("sticky >2 edge-burst boundary changed")
    if a5.gap_evaluation((2, 2, 0), 0)[1] is not False:
        raise T3Error("isolated <=2 edge acceptance boundary changed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--preflight-report", type=Path, default=DEFAULT_PREFLIGHT_REPORT)
    parser.add_argument("--report", type=Path, default=DEFAULT_RESULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("T3 exploratory self-test: PASS")
            return 0
        if args.preflight:
            self_test()
            offline_preflight(args.preflight_report)
            print("T3 exploratory preflight: PASS")
            print(f"report: {args.preflight_report}")
            return 0
        analyze_results(args.report)
        print("T3 exploratory acquisition contract: PASS")
        print("R2 NOT ACCEPTED")
        print(f"report: {args.report}")
        return 0
    except (T3Error, anchor.ValidationError, a5.RecoveryError, OSError, ValueError) as exc:
        print(f"T3 exploratory validation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
