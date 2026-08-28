#!/usr/bin/env python3
"""Offline validation for the campaign-2026082701 T4 Attempt-7 continuation.

This script has no LinuxCNC/HAL control interface.  It validates the frozen
runner, immutable Attempt-4/Attempt-6 evidence, fresh output isolation, exact
sequence-24..101 topology, closure ownership, and the bounded B0 entry replay.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import itertools
import math
from pathlib import Path
import re
import stat
import sys


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
RUNNER = (
    REPO_ROOT
    / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.ngc"
)
ATTEMPT1_RUNNER = (
    REPO_ROOT
    / "nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt1.ngc"
)
ATTEMPT4_RUNNER = (
    REPO_ROOT
    / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt4_recovery.ngc"
)
ATTEMPT5_RUNNER = (
    REPO_ROOT
    / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.ngc"
)
A6_PARTIAL_ARCHIVE_SHA256SUMS = (
    HERE / "calibration_runs/"
    "20260828_0806_campaign2026082701_t4_new_location_attempt6_partial_gate_burst_abort_seq24/"
    "SHA256SUMS"
)
A6_PARTIAL_ARCHIVE_ROOT = "d2e84c1534d63d34974a438788ea3d03522d2b597e0d116e032ef587f91adde6"

CAMPAIGN = 2026082701
MODE = 41
ATTEMPT = 7
MODEL_ID = 2026082601
EXPECTED_ROWS = 78
EXPECTED_TRACES = 624
EXPECTED_CLOSURES = 25
EXPECTED_COMPOSITE_ROWS = 101
EXPECTED_COMPOSITE_TRACES = 808
EXPECTED_COMPOSITE_CLOSURES = 28
MAX_GCODE_LINE_LENGTH = 225
QUIET_DURATION_S = 15.0
QUIET_TIMEOUT_S = 900.0
QUIET_SAMPLE_S = 0.25

RUNNER_SHA256 = "fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d"
ATTEMPT1_RUNNER_SHA256 = (
    "54bd1e3b5cfc95f44ddbf344693652b68dec920f74649e466d939860fe4a9174"
)
ATTEMPT4_RUNNER_SHA256 = (
    "66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b"
)
ATTEMPT5_RUNNER_SHA256 = (
    "372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1"
)

A4_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery"
A5_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt5-recovery"
A6_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery"
A7_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery"
KINDS = (
    "results",
    "state",
    "model-state",
    "closures",
    "contact-trace",
    "gap-trace",
)
A4_PATHS = {kind: HERE / f"{A4_PREFIX}-{kind}.csv" for kind in KINDS}
A5_PATHS = {kind: HERE / f"{A5_PREFIX}-{kind}.csv" for kind in KINDS}
A6_PATHS = {kind: HERE / f"{A6_PREFIX}-{kind}.csv" for kind in KINDS}
A7_PATHS = {kind: HERE / f"{A7_PREFIX}-{kind}.csv" for kind in KINDS}
TRACE_SCHEMA_V2 = {
    "contact-trace": (
        "schema_version", "campaign_id", "stage_mode", "attempt_id",
        "global_seq", "abs_b_deg", "abs_c_deg", "acquisition_try",
        "pass_id", "contact_id", "pre_raw_count", "pre_mux_count",
        "pre_gated_count", "post_raw_count", "post_mux_count",
        "post_gated_count", "ready_raw_count", "ready_mux_count",
        "ready_gated_count", "probe_result", "travel_mm", "raw_delta",
        "mux_delta", "gated_delta", "repeat_raw_delta", "repeat_mux_delta",
        "repeat_gated_delta", "extra_raw_minus_gated_delta",
        "chatter_observed", "quiet_episode_count", "quiet_elapsed_s",
        "quiet_reset_count", "consistency_fault", "release_fault",
        "terminal_failure",
    ),
    "gap-trace": (
        "schema_version", "campaign_id", "stage_mode", "attempt_id",
        "next_global_seq", "abs_b_deg", "abs_c_deg", "acquisition_try",
        "pass_id", "contact_id", "prior_ready_raw_count",
        "prior_ready_mux_count", "prior_ready_gated_count",
        "current_pre_raw_count", "current_pre_mux_count",
        "current_pre_gated_count", "gap_raw_delta", "gap_mux_delta",
        "gap_gated_delta", "prior_contact_extra_delta",
        "combined_extra_delta", "chatter_observed", "quiet_episode_count",
        "quiet_elapsed_s", "quiet_reset_count", "consistency_fault",
        "initial_baseline",
    ),
}
A4_SHA256 = {
    "results": "835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1",
    "state": "99f96ba6e418a514cb07ecba4bd81fec6c18d3f0fbef39c46fcf01d5d8d84235",
    "model-state": "e28f0f7aab6aca30484381590a6f53284f7f8daa43622e35694d415cd68b7cbc",
    "closures": "26919899661bdf78deddbef9983906814f307d25682370eb5d03c47504090bb4",
    "contact-trace": "cc097ab53887f6356531681d7ab2bd70021185e0f44e38b8afd46f53b6abe21b",
    "gap-trace": "3f3e72c8738d2fc57efad3bba0617ed5791b88c2e586d07cd0ff092d496671e7",
}
A5_SHA256 = {
    "results": "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    "state": "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    "model-state": "340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd",
    "closures": "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    "contact-trace": "df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8",
    "gap-trace": "e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2",
}
A6_SHA256 = {
    "results": "06752f2d73dc1ecbf1f605922e2270c55aba0a81e60640bc9e5217730bb785e6",
    "state": "9497b7f047b3b674f496e9dd8f1c27594ed35ddd8e54bda1aa59308ac312a449",
    "model-state": "7ff4da12561c90af7306c7a2925d482d746a7647b33b17f1558d5ab920029f03",
    "closures": "ff4d020689ee7f8d6e1d13584829a6a51e955a406613743572ea5f17cfa9ae32",
    "contact-trace": "37ce836c1914fe27328d14613e402dec895afa61b7e7e4a56aaaf127f480cf28",
    "gap-trace": "8fb60a0f3baf2fc57cabffcb1144c6c2cbf870e6480d3c593a35642fe777a14d",
}

BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
MODEL_HAL = HERE / "tcpc_length_aware_candidate_2026082601.hal"
VALIDATION_INI = (
    HERE
    / "5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini"
)
REACH_MODULE = HERE / "analyze_tcpc_relocated_sphere_reachability.py"
A3_REACH_MODULE = (
    HERE
    / "analyze_tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery_reachability.py"
)
REACH_PREREQUISITE_SHA256 = {
    BASE_HAL: "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778",
    MODEL_HAL: "8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14",
    VALIDATION_INI: "24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a",
    REACH_MODULE: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
    A3_REACH_MODULE: "4af0e489ca919d66799468ae3b34ce02face41cc21d1555a58c7c728e62bbff9",
}

A4_RESULTS_SHA_COMMENT = A4_SHA256["results"]
A4_CENTERS = (
    (2500.936999, 696.555178, -302.575887),
    (2501.053018, 696.557477, -302.573720),
    (2501.106783, 696.527547, -302.564887),
    (2501.122339, 696.570911, -302.560221),
    (2501.085125, 696.601748, -302.555554),
    (2501.040197, 696.636425, -302.559221),
    (2501.011103, 696.640736, -302.561222),
    (2500.963878, 696.611948, -302.571556),
    (2500.940456, 696.558194, -302.576056),
)
RESUME_WORK = (0.0, 0.0, 0.0)
RESUME_ABSOLUTE = (
    2501.9412544845527,
    696.8993474512587,
    -280.8661282715618,
)
G54_OFFSETS = (
    2501.9412544845527,
    696.8993474512587,
    -510.27312827156186,
)
ACTIVE_TLO = (0.0, 0.0, 229.407000)
A6_SEQ23_CENTER = (2501.156895, 696.528585, -302.580083)
RESUME_TOLERANCE = 0.050
TOOL_OFFSET_TOLERANCE = 0.002
TOP_CLEAR_RADIUS = 22.845258
EFFECTIVE_CONTACT_RADIUS = 17.845258


class ValidationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def read_ascii(path: Path) -> str:
    data = path.read_bytes()
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"non-ASCII file: {path}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_count(text: str, needle: str, expected: int, label: str) -> None:
    actual = text.count(needle)
    require(actual == expected, f"{label}: found {actual}, expected {expected}")


def strip_parenthesized_comments(line: str) -> str:
    depth = 0
    result: list[str] = []
    for character in line:
        if character == "(":
            depth += 1
        elif character == ")":
            require(depth > 0, f"unbalanced ')' in line: {line}")
            depth -= 1
        elif depth == 0:
            result.append(character)
    require(depth == 0, f"unbalanced '(' in line: {line}")
    return "".join(result)


def executable_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = " ".join(strip_parenthesized_comments(raw).split())
        if line:
            lines.append(line)
    return lines


def extract_oword(text: str, name: str, opening: str, closing: str) -> str:
    start_re = re.compile(rf"^\s*o<{re.escape(name)}>\s+{opening}\b", re.MULTILINE)
    end_re = re.compile(rf"^\s*o<{re.escape(name)}>\s+{closing}\b", re.MULTILINE)
    starts = list(start_re.finditer(text))
    ends = list(end_re.finditer(text))
    require(len(starts) == 1, f"o<{name}> {opening} count is {len(starts)}, expected 1")
    require(len(ends) == 1, f"o<{name}> {closing} count is {len(ends)}, expected 1")
    require(starts[0].start() < ends[0].end(), f"o<{name}> block is reversed")
    return text[starts[0].start() : ends[0].end()]


def assignment_literals(text: str, parameter: int) -> list[str]:
    pattern = re.compile(rf"^\s*#{parameter}\s*=\s*([^\s(]+)", re.MULTILINE)
    return pattern.findall(text)


def require_assignment(text: str, parameter: int, literal: str, count: int = 1) -> None:
    values = assignment_literals(text, parameter)
    actual = values.count(literal)
    require(
        actual == count,
        f"#{parameter}={literal}: found {actual}, expected {count}; assignments={values}",
    )


def validate_oword_balance(text: str) -> None:
    token_re = re.compile(
        r"^\s*o<([^>]+)>\s+(sub|endsub|if|elseif|else|endif|while|endwhile|repeat|endrepeat)\b",
        re.IGNORECASE,
    )
    stack: list[tuple[str, str, int]] = []
    opener_for = {"endsub": "sub", "endif": "if", "endwhile": "while", "endrepeat": "repeat"}
    for line_number, line in enumerate(text.splitlines(), 1):
        match = token_re.match(line)
        if match is None:
            continue
        name, token = match.group(1), match.group(2).lower()
        if token in {"sub", "if", "while", "repeat"}:
            stack.append((name, token, line_number))
        elif token in {"elseif", "else"}:
            require(stack and stack[-1][0] == name and stack[-1][1] == "if", f"orphan {token} at line {line_number}")
        else:
            require(bool(stack), f"orphan {token} at line {line_number}")
            open_name, open_token, open_line = stack.pop()
            require(open_name == name and open_token == opener_for[token], f"o-word mismatch: line {open_line} {open_name}/{open_token}, line {line_number} {name}/{token}")
    require(not stack, f"unclosed o-word blocks: {stack[-5:]}")


def csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="ascii") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None, f"missing CSV header: {path}")
        return list(reader.fieldnames), list(reader)


def normalize_trace_row(kind: str, row: dict[str, str]) -> dict[str, str]:
    """Map immutable schema-1 traces into the schema-2 composite view.

    Attempt 4 and Attempt 6 remain byte-for-byte schema 1 on disk. Their
    ``burst_flag`` becomes ``chatter_observed`` and the new quiet telemetry is
    zero because those runners did not implement the stationary quiet policy.
    Attempt 7 rows already use schema 2 and pass through unchanged.
    """
    require(kind in TRACE_SCHEMA_V2, f"not a trace kind: {kind}")
    version = exact_int(row, "schema_version")
    if version == 2:
        require(tuple(row) == TRACE_SCHEMA_V2[kind], f"{kind} schema-2 fields changed")
        return dict(row)
    require(version == 1, f"unsupported {kind} schema version {version}")
    mapped = dict(row)
    mapped["schema_version"] = "2.0"
    mapped["chatter_observed"] = mapped.pop("burst_flag")
    mapped["quiet_episode_count"] = "0.0"
    mapped["quiet_elapsed_s"] = "0.0"
    mapped["quiet_reset_count"] = "0.0"
    require(set(mapped) == set(TRACE_SCHEMA_V2[kind]), f"{kind} schema-1 mapping is incomplete")
    return {field: mapped[field] for field in TRACE_SCHEMA_V2[kind]}


def finite(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise ValidationError(f"invalid {field} in CSV row") from exc
    require(math.isfinite(value), f"non-finite {field} in CSV row")
    return value


def exact_int(row: dict[str, str], field: str) -> int:
    value = finite(row, field)
    require(abs(value - round(value)) <= 1e-9, f"non-integral {field}={value}")
    return int(round(value))


def validate_a4_sources() -> list[dict[str, str]]:
    require(sha256(ATTEMPT1_RUNNER) == ATTEMPT1_RUNNER_SHA256, "Attempt-1 topology source hash changed")
    require(sha256(ATTEMPT4_RUNNER) == ATTEMPT4_RUNNER_SHA256, "Attempt-4 handoff runner hash changed")
    for kind, path in A4_PATHS.items():
        require(path.exists(), f"missing immutable Attempt-4 source: {path}")
        require(sha256(path) == A4_SHA256[kind], f"Attempt-4 {kind} source hash changed")

    _, results = csv_rows(A4_PATHS["results"])
    require(len(results) == 9, "Attempt-4 handoff must contain exactly rows 1..9")
    for sequence, (row, center) in enumerate(zip(results, A4_CENTERS, strict=True), 1):
        require(exact_int(row, "campaign_id") == CAMPAIGN, "Attempt-4 campaign mismatch")
        require(exact_int(row, "stage_mode") == 38, "Attempt-4 mode mismatch")
        require(exact_int(row, "attempt_id") == 4, "Attempt-4 attempt mismatch")
        require(exact_int(row, "sample_seq") == sequence, "Attempt-4 sequence is not 1..9")
        require(exact_int(row, "block_id") == 100, "Attempt-4 opening block mismatch")
        require(exact_int(row, "anchor_seq") == sequence, "Attempt-4 opening anchor mismatch")
        require(exact_int(row, "is_closure") == int(sequence == 9), "Attempt-4 closure marker mismatch")
        actual = tuple(finite(row, field) for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm"))
        require(actual == center, f"Attempt-4 center {sequence} changed: {actual} != {center}")

    _, state_rows = csv_rows(A4_PATHS["state"])
    _, model_rows = csv_rows(A4_PATHS["model-state"])
    _, contact_rows = csv_rows(A4_PATHS["contact-trace"])
    _, gap_rows = csv_rows(A4_PATHS["gap-trace"])
    require(len(state_rows) == 9 and len(model_rows) == 9, "Attempt-4 state/model handoff is not 9 rows")
    require(len(contact_rows) == 72 and len(gap_rows) == 72, "Attempt-4 handoff trace count is not 72/72")
    for rows, label, sequence_field in (
        (contact_rows, "contact", "global_seq"),
        (gap_rows, "gap", "next_global_seq"),
    ):
        counts = Counter(exact_int(row, sequence_field) for row in rows)
        require(counts == Counter({sequence: 8 for sequence in range(1, 10)}), f"Attempt-4 {label} trace ownership mismatch")
    for kind, rows in (("contact-trace", contact_rows), ("gap-trace", gap_rows)):
        normalized = [normalize_trace_row(kind, row) for row in rows]
        require(all(exact_int(row, "schema_version") == 2 for row in normalized), f"Attempt-4 {kind} schema mapping failed")

    _, closures = csv_rows(A4_PATHS["closures"])
    require(len(closures) == 2, "Attempt-4 closure evidence must contain pass plus failed historical bridge")
    by_block = {exact_int(row, "block_id"): row for row in closures}
    require(set(by_block) == {100, 3709}, "Attempt-4 closure block set changed")
    require(exact_int(by_block[100], "pass") == 1, "Attempt-4 same-run closure did not pass")
    require(abs(finite(by_block[100], "limit_mm") - 0.050) <= 1e-12, "Attempt-4 same-run closure limit changed")
    require(exact_int(by_block[3709], "pass") == 0, "Attempt-4 historical bridge is no longer marked failed")
    require(finite(by_block[3709], "closure_norm_mm") > 0.050, "Attempt-4 failed bridge no longer exceeds 0.050 mm")
    return results


def validate_a5_zero_row_sources() -> None:
    require(sha256(ATTEMPT5_RUNNER) == ATTEMPT5_RUNNER_SHA256, "Attempt-5 zero-row runner hash changed")
    for kind, path in A5_PATHS.items():
        require(path.exists(), f"missing Attempt-5 zero-row source: {path}")
        require(sha256(path) == A5_SHA256[kind], f"Attempt-5 {kind} zero-row source changed")
        _, rows = csv_rows(path)
        require(not rows, f"Attempt-5 {kind} is no longer zero-row evidence")


def validate_a6_sources() -> None:
    require(
        sha256(A6_PARTIAL_ARCHIVE_SHA256SUMS) == A6_PARTIAL_ARCHIVE_ROOT,
        "Attempt-6 partial archive root changed",
    )
    for kind, path in A6_PATHS.items():
        require(path.exists(), f"missing immutable Attempt-6 source: {path}")
        require(sha256(path) == A6_SHA256[kind], f"Attempt-6 {kind} source hash changed")

    _, results = csv_rows(A6_PATHS["results"])
    _, state_rows = csv_rows(A6_PATHS["state"])
    _, model_rows = csv_rows(A6_PATHS["model-state"])
    require(len(results) == len(state_rows) == len(model_rows) == 14, "Attempt-6 accepted row count is not 14")
    for rows, label in ((results, "results"), (state_rows, "state"), (model_rows, "model")):
        sequences = [exact_int(row, "sample_seq") for row in rows]
        require(sequences == list(range(10, 24)), f"Attempt-6 {label} ownership is not seq10..23")
        for row in rows:
            require(exact_int(row, "campaign_id") == CAMPAIGN, f"Attempt-6 {label} campaign mismatch")
            require(exact_int(row, "stage_mode") == 40, f"Attempt-6 {label} mode mismatch")
            require(exact_int(row, "attempt_id") == 6, f"Attempt-6 {label} attempt mismatch")
    last_center = tuple(
        finite(results[-1], field)
        for field in ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")
    )
    require(last_center == A6_SEQ23_CENTER, f"Attempt-6 sequence-23 center changed: {last_center}")

    _, closures = csv_rows(A6_PATHS["closures"])
    require(len(closures) == 2, "Attempt-6 retained closure count is not 2")
    require(
        [(exact_int(row, "open_sample_seq"), exact_int(row, "close_sample_seq")) for row in closures]
        == [(10, 16), (17, 23)],
        "Attempt-6 closure ownership changed",
    )
    for row in closures:
        require(exact_int(row, "pass") == 1, "Attempt-6 retained closure did not pass")
        require(abs(finite(row, "limit_mm") - 0.050) <= 1e-12, "Attempt-6 closure limit changed")

    _, contacts = csv_rows(A6_PATHS["contact-trace"])
    _, gaps = csv_rows(A6_PATHS["gap-trace"])
    require(len(contacts) == 113 and len(gaps) == 114, "Attempt-6 partial trace dimensions changed")
    accepted_contacts = [row for row in contacts if 10 <= exact_int(row, "global_seq") <= 23]
    accepted_gaps = [row for row in gaps if 10 <= exact_int(row, "next_global_seq") <= 23]
    require(len(accepted_contacts) == len(accepted_gaps) == 112, "Attempt-6 accepted trace count is not 112/112")
    require(
        Counter(exact_int(row, "global_seq") for row in accepted_contacts)
        == Counter({sequence: 8 for sequence in range(10, 24)}),
        "Attempt-6 accepted contact topology changed",
    )
    require(
        Counter(exact_int(row, "next_global_seq") for row in accepted_gaps)
        == Counter({sequence: 8 for sequence in range(10, 24)}),
        "Attempt-6 accepted gap topology changed",
    )
    for row in accepted_contacts:
        require(exact_int(row, "probe_result") == 1, "Attempt-6 accepted contact is not a touch")
        require(exact_int(row, "gated_delta") == 1, "Attempt-6 accepted contact lost exactly-one gated edge")
        require(exact_int(row, "repeat_gated_delta") == 0, "Attempt-6 accepted contact has a gated repeat")
        for field in ("consistency_fault", "release_fault", "terminal_failure"):
            require(exact_int(row, field) == 0, f"Attempt-6 accepted contact has {field}")
    for row in accepted_gaps:
        require(exact_int(row, "gap_gated_delta") == 0, "Attempt-6 accepted gap has a gated edge")
        require(exact_int(row, "consistency_fault") == 0, "Attempt-6 accepted gap has a consistency fault")
    partial_contacts = [row for row in contacts if exact_int(row, "global_seq") == 24]
    partial_gaps = [row for row in gaps if exact_int(row, "next_global_seq") == 24]
    require(len(partial_contacts) == 1 and len(partial_gaps) == 2, "Attempt-6 partial seq24 evidence changed")
    for kind, rows in (("contact-trace", contacts), ("gap-trace", gaps)):
        normalized = [normalize_trace_row(kind, row) for row in rows]
        require(all(exact_int(row, "schema_version") == 2 for row in normalized), f"Attempt-6 {kind} schema mapping failed")


def validate_fresh_outputs() -> None:
    prior_inode_keys = {
        (path.lstat().st_dev, path.lstat().st_ino)
        for path in (*A4_PATHS.values(), *A5_PATHS.values(), *A6_PATHS.values())
    }
    inode_keys: set[tuple[int, int]] = set()
    for kind, path in A7_PATHS.items():
        require(path.exists(), f"missing Attempt-7 output: {path}")
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), f"Attempt-7 output is not a regular file: {path}")
        require(not path.is_symlink(), f"Attempt-7 output is a symlink: {path}")
        inode_key = (info.st_dev, info.st_ino)
        require(inode_key not in inode_keys, f"Attempt-7 outputs share an inode: {path}")
        require(inode_key not in prior_inode_keys, f"Attempt-7 output aliases immutable prior evidence: {path}")
        inode_keys.add(inode_key)
        a4_header, _ = csv_rows(A4_PATHS[kind])
        a7_header, a7_rows = csv_rows(path)
        if kind in TRACE_SCHEMA_V2:
            require(tuple(a7_header) == TRACE_SCHEMA_V2[kind], f"Attempt-7 {kind} schema-2 header changed")
        else:
            require(a7_header == a4_header, f"Attempt-7 {kind} established header changed")
        require(not a7_rows, f"Attempt-7 {kind} is not header-only before execution")


def validate_probe_geometry(text: str) -> None:
    lines = executable_lines(text)
    long_lines = [(index, len(line)) for index, line in enumerate(text.splitlines(), 1) if len(line) > MAX_GCODE_LINE_LENGTH]
    require(not long_lines, f"runner exceeds {MAX_GCODE_LINE_LENGTH}-character parser-safe line bound: {long_lines[:3]}")
    dwell_lines = [line for line in lines if line.startswith("G4 ")]
    require(dwell_lines == ["G4 P#793"] * 3, f"unexpected dwell sites: {dwell_lines}")
    require("G4 P10.0" not in lines and "G4 P15.0" not in lines, "fixed successful-contact dwell remains")

    g38_indices = [index for index, line in enumerate(lines) if line.startswith("G38.")]
    require(len(g38_indices) == 4, f"G38 site count is {len(g38_indices)}, expected 4")
    expected_final_call = "o<tcpc_pair_probe_final_guard> call [#520] [#521]"
    require(all(lines[index - 1] == expected_final_call for index in g38_indices), "a G38 is missing its immediate final guard call")
    require(all(lines[index].startswith("G38.3 ") for index in g38_indices), "probe moves must all use G38.3")

    selector = extract_oword(text, "tcpc_pair_selector_guard", "sub", "endsub")
    for snippet, label in (
        ("[[ABS[#777 - #794] GT 0.000001] OR [ABS[#777 - 15.0] GT 0.000001]]", "15-second quiet duration"),
        ("[[ABS[#779 - #789] GT 0.000001] OR [ABS[#779 - 900.0] GT 0.000001]]", "900-second quiet timeout"),
        ("[[ABS[#793 - #795] GT 0.000001] OR [ABS[#793 - 0.25] GT 0.000001]]", "0.25-second quiet sample"),
    ):
        require(snippet in selector, f"{label} selector guard changed")

    quiet = extract_oword(text, "tcpc_stationary_quiet_guard", "sub", "endsub")
    quiet_lines = executable_lines(quiet)
    forbidden_quiet = re.compile(r"^(?:G(?:0|00|1|01|2|02|3|03|38(?:\.|\s))|M(?:0|1|60|62|63|64|65))(?:\s|$)")
    require(not [line for line in quiet_lines if forbidden_quiet.match(line)], "stationary quiet contains motion, hold, or gate-write command")
    require_count(quiet, "G4 P#793", 1, "stationary quiet sampled dwell")
    require_count(quiet, "o<tcpc_pair_live_guard> call [1.0] [#<quiet_target_b>] [#<quiet_target_c>] [1.0]", 2, "stationary quiet live/model guard")
    for snippet, label in (
        ("#<quiet_budget> = #7", "remaining quiet budget argument"),
        ("#<quiet_consistency_raw> = #8", "raw consistency origin"),
        ("#<quiet_consistency_mux> = #9", "mux consistency origin"),
        ("while [[#944 LT #<quiet_budget>] AND [#<quiet_complete> LT 0.5]]", "non-resetting remaining-budget loop"),
        ("#<quiet_stable> = 0.0", "quiet timer reset"),
        ("#<quiet_stable> = [#<quiet_stable> + #793]", "quiet timer accumulation"),
        ("o<quiet_episode_timeout> if [#<quiet_complete> LT 0.5]", "quiet timeout predicate"),
        ("[ABS[#<_abs_x> - #<quiet_x>] GT 0.001]", "stationary X check"),
        ("Automatic stationary probe quiet did not complete within 900 cumulative seconds", "finite timeout abort"),
    ):
        require(snippet in quiet, f"{label} missing")
    require_count(quiet, "[ABS[#<quiet_gated> - #<quiet_anchor_gated>] GT 0.000001]", 3, "outside-G38 gated hard checks")
    require_count(quiet, "[ABS[[#<quiet_raw> - #<quiet_consistency_raw>] - [#<quiet_mux> - #<quiet_consistency_mux>]] GT 0.000001]", 2, "entry/final cumulative raw-mux checks")
    require("o<quiet_level_activity_entry> if [[[[#<_hal[t_probe-in]> + #<_hal[probe-mux]> + #<_hal[tcpc-probe-abnormal-level]> + #<_hal[tcpc_probe_fault_pause.out]>] GT 0.5] OR [#<_hal[tcpc_probe_gate_ignore.out]> GT 0.5]]]" in quiet, "quiet entry does not treat transient fault/ignore as recoverable activity")
    require("o<quiet_fault_level> if [#<_hal[tcpc_probe_fault_pause.out]> GT 0.5]" in quiet, "quiet sample does not reset for transient fault")
    require("o<quiet_stable_sample> else\n        #<quiet_stable> = 0.0" in quiet, "quiet timer is not reset after activity, skew, or uncleared levels")
    require("o<quiet_complete_sample> if [[#<quiet_stable> GE #777] AND [#<_hal[tcpc_probe_gate_ignore.out]> LT 0.5]]" in quiet, "quiet may complete while ignore remains active")
    require("o<quiet_final_levels> if [[[[#<_hal[t_probe-in]> + #<_hal[probe-mux]> + #<_hal[motion.probe-input]> + #<_hal[tcpc-probe-abnormal-level]> + #<_hal[tcpc_probe_fault_pause.out]> + #<_hal[tcpc_probe_gate_ignore.out]>] GT 0.5]]]" in quiet, "quiet final level/fault/ignore guard changed")
    require("#<quiet_context> = #10" in quiet, "quiet diagnostic context argument missing")
    require_count(quiet, "TCPC_QUIET_FAIL code=#946 context=#<quiet_context> seq=#933 pass=#931 contact=#932", 3, "durable quiet failure context")
    require_count(quiet, "TCPC_QUIET_COUNTERS raw=#<quiet_raw> mux=#<quiet_mux> gated=#<quiet_gated>", 3, "durable quiet counter diagnostics")
    require_count(quiet, "TCPC_QUIET_LATCH fault=#<_hal[tcpc_probe_fault_pause.out]> ignore=#<_hal[tcpc_probe_gate_ignore.out]>", 3, "durable quiet latch diagnostics")
    require("M0" not in quiet and "M1" not in quiet, "operator hold appears in automatic quiet")

    gap_wrapper = extract_oword(text, "tcpc_gap_quiet_guard", "sub", "endsub")
    contact_wrapper = extract_oword(text, "tcpc_contact_quiet_guard", "sub", "endsub")
    require("#<gap_quiet_budget> = [#779 - #948]" in gap_wrapper, "gap retries restart the 900-second budget")
    require("[#<gap_quiet_budget>] [#950] [#951]" in gap_wrapper, "gap quiet does not use full-gap consistency origins")
    require("[#948 GT #779]" in gap_wrapper, "gap cumulative quiet timeout guard missing")
    require("#<contact_quiet_budget> = [#779 - #976]" in contact_wrapper, "contact retries restart the 900-second budget")
    require("[#<contact_quiet_budget>] [#920] [#921]" in contact_wrapper, "contact quiet does not use pre-G38 consistency origins")
    require("[#976 GT #779]" in contact_wrapper, "contact cumulative quiet timeout guard missing")

    motion_ready = extract_oword(text, "tcpc_gap_motion_ready_guard", "sub", "endsub")
    motion_ready_lines = executable_lines(motion_ready)
    require(
        not [line for line in motion_ready_lines if forbidden_quiet.match(line)],
        "motion-ready quiet helper contains motion, hold, or gate-write command",
    )
    require("o<tcpc_gap_motion_ready_guard> call" not in motion_ready, "motion-ready quiet helper recurses")
    require_count(
        motion_ready,
        "o<tcpc_gap_quiet_guard> call [#<motion_ready_target_b>] [#<motion_ready_target_c>] [0.0]",
        1,
        "motion-ready conditional gap quiet",
    )
    require_count(
        motion_ready,
        "o<tcpc_gap_quiet_guard> call [#<motion_ready_target_b>] [#<motion_ready_target_c>] [1.0]",
        1,
        "motion-ready forced gap quiet",
    )
    require_count(
        motion_ready,
        "o<tcpc_pair_live_guard> call [1.0] [#<motion_ready_target_b>] [#<motion_ready_target_c>] [1.0]",
        1,
        "motion-ready tolerant live guard",
    )
    require("ABS[#<motion_ready_gated> - #942] GT 0.000001" in motion_ready, "motion-ready gated change is not fatal")
    require("#<motion_ready_raw> LT #940" in motion_ready and "#<motion_ready_mux> LT #941" in motion_ready, "motion-ready counter rollback checks changed")

    live_calls = [line for line in lines if line.startswith("o<tcpc_pair_live_guard> call")]
    require(live_calls, "runner has no live-guard calls")
    require(
        all(line.endswith(" [1.0]") for line in live_calls),
        f"a stationary live-guard boundary still rejects recoverable gate-closed noise: {live_calls}",
    )

    release = extract_oword(text, "tcpc_pair_release_guard", "sub", "endsub")
    require("#<release_extra_seen> = #998" in release, "immediate post-G38 chatter does not force release quiet")
    require("o<tcpc_contact_quiet_guard> call [#<release_target_b>] [#<release_target_c>] [1.0]" in release, "release chatter does not invoke forced stationary quiet")
    require("G4 P10.0" not in release and "G4 P15.0" not in release, "release uses a fixed settle dwell")

    post = extract_oword(text, "tcpc_contact_trace_post", "sub", "endsub")
    require("#940 = #923" in post and "#941 = #924" in post and "#942 = #925" in post, "post-G38 last-sample anchor changed")
    require("o<trace_post_partition_skew> if [ABS[#<trace_post_raw_delta> - #<trace_post_mux_delta>] GT 0.000001]" in post, "immediate direct skew does not force quiet")
    require_count(post, "#998 = 1.0", 2, "immediate matched-extra/skew force flags")

    final_guard = extract_oword(text, "tcpc_pair_probe_final_guard", "sub", "endsub")
    require("M66 E0 L0" in final_guard, "final pre-G38 guard does not synchronize before sampling")
    require("o<tcpc_contact_trace_begin> call [#932] [0.0]" in final_guard, "final guard does not recapture a quiet baseline")
    require("o<tcpc_gap_quiet_guard> call [#<final_target_b>] [#<final_target_c>] [1.0]" in final_guard, "final race does not restart quiet")
    require("[ABS[#<final_gated> - #922] GT 0.000001]" in final_guard, "final interval gated hard check missing")

    gap = extract_oword(text, "tcpc_contact_trace_begin", "sub", "endsub")
    require("#<reset_gap_quiet> = #2" in gap, "trace-begin reserved argument is missing")
    require("o<trace_gap_quiet_reset_forbidden> if [ABS[#<reset_gap_quiet>] GT 0.000001]" in gap, "trace-begin reserved argument is not hard-required zero")
    require(not any(f"#{parameter} = 0.0" in gap for parameter in (947, 948, 949)), "trace-begin can reset the gap quiet context")
    require_count(gap, "o<tcpc_gap_quiet_guard> call [#934] [#935] [0.0]", 1, "pre-G38 gap quiet entry")
    require_count(gap, "o<tcpc_gap_quiet_guard> call [#934] [#935] [1.0]", 1, "pre-G38 gap race quiet")
    require("#959 = [#953 + [#956 - #958]]" in gap, "combined gap-extra formula changed")
    require(
        "[[ABS[#956 - #957] GT 0.000001] OR [ABS[#958] GT 0.000001]]" in gap,
        "gap raw/mux equality or zero-gated hard guard changed",
    )
    require("o<trace_gap_pre_g38_fault> if [#961 GT 0.5]" in gap, "gap hard fault no longer isolates mismatch/gated state")
    require("#959 GT #779" not in gap and "#960 GT" not in gap, "matched gap chatter is still count-fatal")
    finish = extract_oword(text, "tcpc_contact_trace_finish", "sub", "endsub")
    for snippet, label in (
        ("ABS[#<trace_total_raw> - #<trace_total_mux>]", "final cumulative raw/mux equality"),
        ("ABS[#965 - 1.0]", "exactly-one G38 gated edge"),
        ("ABS[#968]", "zero gated repeat"),
    ):
        require(snippet in finish, f"{label} hard probe invariant changed")
    require("ABS[#963 - #964]" not in finish and "ABS[#966 - #967]" not in finish, "transient direct/repeat partition skew is still fatal")
    require("o<trace_success_consistency_abort> if [[#962 GT 0.5] AND [#970 LT 0.5]]" in finish, "final success consistency abort changed")
    require("#936 GT" not in finish and "#969 GT #779" not in finish, "matched contact chatter is still count-fatal")

    vector = extract_oword(text, "tcpc_vector_sphere_pass4", "sub", "endsub")
    vector_lines = executable_lines(vector)
    ready_indices = [index for index, line in enumerate(vector_lines) if line == "o<tcpc_pair_probe_ready_guard> call [#520] [#521]"]
    final_indices = [index for index, line in enumerate(vector_lines) if line == "o<tcpc_pair_probe_final_guard> call [#520] [#521]"]
    require(len(ready_indices) == len(final_indices) == 4, "vector ready/final guard site count changed")
    for contact in range(1, 5):
        begin_call = f"o<tcpc_contact_trace_begin> call [{contact}.0] [0.0]"
        begin_indices = [index for index, line in enumerate(vector_lines) if line == begin_call]
        require(len(begin_indices) == 2, f"contact {contact} does not use exactly two reserved-zero trace baselines")
        require(
            begin_indices[0] < ready_indices[contact - 1] < begin_indices[1] < final_indices[contact - 1],
            f"contact {contact} trace/ready/final order changed",
        )
    trace_begin_calls = [line for line in lines if line.startswith("o<tcpc_contact_trace_begin> call")]
    require(len(trace_begin_calls) == 9, f"trace-begin call-site count is {len(trace_begin_calls)}, expected 9")
    require(all(line.endswith(" [0.0]") for line in trace_begin_calls), "a trace-begin caller can reset the gap context")
    require_count(vector, "o<tcpc_pair_release_guard> call [#520] [#521] [1.0]", 4, "successful-contact release guard")
    require_count(vector, "o<tcpc_gap_motion_ready_guard> call [#520] [#521]", 8, "vector stationary motion-boundary guard")
    measure = extract_oword(text, "tcpc_measure_pose", "sub", "endsub")
    require_count(measure, "o<tcpc_gap_motion_ready_guard> call", 12, "pose-transit stationary motion-boundary guard")
    for snippet, label in (
        ("G1 X#<current_clear_x> Y#<current_clear_y> Z#<current_clear_z>\n    o<tcpc_gap_motion_ready_guard> call [#<current_b>] [#<current_c>]", "center-derived clear boundary"),
        ("G1 Z#<safe_z>\n    o<tcpc_gap_motion_ready_guard> call [#<current_b>] [#<current_c>]", "high-Z lift boundary"),
        ("G1 B0 C0\n      o<tcpc_gap_motion_ready_guard> call [0.0] [0.0]", "sign-change B0 boundary"),
        ("G1 B#<target_b> C#<target_c>\n    (Verify target rotary command/feedback/SSI while still at high Z.)\n    o<tcpc_gap_motion_ready_guard> call [#<target_b>] [#<target_c>]", "target index boundary"),
        ("G1 X#<next_start_x> Y#<next_start_y>\n    o<tcpc_gap_motion_ready_guard> call [#<target_b>] [#<target_c>]", "target XY boundary"),
        ("G1 Z#<next_start_z>\n    o<tcpc_gap_motion_ready_guard> call [#<target_b>] [#<target_c>]", "target Z boundary"),
    ):
        require(snippet in measure, f"{label} lost adaptive quiet")
    closure = extract_oword(text, "tcpc_primary_closure_guard", "sub", "endsub")
    baseline = extract_oword(text, "tcpc_baseline_return_top_clear", "sub", "endsub")
    require_count(closure, "o<tcpc_gap_motion_ready_guard> call [#520] [#521]", 1, "closure stationary boundary")
    require_count(baseline, "o<tcpc_gap_motion_ready_guard> call [0.0] [0.0]", 2, "baseline-return stationary boundaries")
    ready = extract_oword(text, "tcpc_pair_probe_ready_guard", "sub", "endsub")
    require_count(ready, "o<tcpc_gap_quiet_guard> call [#<ready_target_b>] [#<ready_target_c>] [0.0]", 1, "ready-stage gap quiet")

    contact_log = re.search(r"^\s*\(LOG,2\.0,#715,#711,#727,#933.*?#970\)\s*$", text, re.MULTILINE)
    gap_log = re.search(r"^\s*\(LOG,2\.0,#715,#711,#727,#933.*?#955\)\s*$", text, re.MULTILINE)
    require(contact_log is not None and len(contact_log.group(0).strip()[5:-1].split(",")) == len(TRACE_SCHEMA_V2["contact-trace"]), "contact schema-2 LOG field count changed")
    require(gap_log is not None and len(gap_log.group(0).strip()[5:-1].split(",")) == len(TRACE_SCHEMA_V2["gap-trace"]), "gap schema-2 LOG field count changed")


def validate_gap_context_ownership(text: str) -> None:
    """Prove that an in-flight gap budget cannot be silently restarted."""
    for parameter in (947, 948, 949):
        require_count(text, f"#{parameter} = 0.0", 3, f"gap-context #{parameter} initialization/reset ownership")

    trace_begin = extract_oword(text, "tcpc_contact_trace_begin", "sub", "endsub")
    require(not any(f"#{parameter} = 0.0" in trace_begin for parameter in (947, 948, 949)), "trace-begin resets an in-flight gap context")

    finish = extract_oword(text, "tcpc_contact_trace_finish", "sub", "endsub")
    for parameter in (947, 948, 949):
        require_count(finish, f"#{parameter} = 0.0", 1, f"accepted-contact #{parameter} reset")
    finish_abort = finish.index("o<trace_success_consistency_abort> if")
    finish_reset = finish.index("#947 = 0.0")
    finish_ready = finish.index("o<tcpc_gap_motion_ready_guard> call")
    require(finish_abort < finish_reset < finish_ready, "accepted-contact gap reset occurs before trace acceptance or after the next boundary check")
    require("o<trace_post_log_live_guard> if [#970 LT 0.5]" in finish, "terminal contact can reset the next gap context")

    subroutine_blocks = re.findall(r"^o<([^>]+)> sub\n(.*?)^o<\1> endsub", text, re.MULTILINE | re.DOTALL)
    reset_owners = {
        name
        for name, block in subroutine_blocks
        if any(f"#{parameter} = 0.0" in block for parameter in (947, 948, 949))
    }
    require(reset_owners == {"tcpc_contact_trace_finish"}, f"unexpected subroutine gap-reset owners: {sorted(reset_owners)}")

    hold = text.index("\nM0\n")
    body = text.index("\no<run_relocated_t4_recovery> if")
    startup = text[hold:body]
    for parameter in (947, 948, 949):
        require_count(startup, f"#{parameter} = 0.0", 1, f"accepted-startup #{parameter} reset")
    require("#950 = #940\n#951 = #941\n#952 = #942" in startup, "startup accepted baseline does not recapture all three quiet counters")
    recapture = startup.index("#950 = #940")
    startup_reset = startup.index("#947 = 0.0")
    require(recapture < startup_reset, "startup gap context resets before the accepted quiet baseline is recaptured")
    require(startup.index("o<tcpc_gap_motion_ready_guard> call [0.0] [0.0]") < recapture, "startup baseline is accepted before conditional quiet")


def canonical_geometry_subroutine(subroutine: str) -> str:
    """Remove only reviewed instrumentation deltas from an A5/A7 body."""
    subroutine = subroutine.replace(A5_PREFIX, A7_PREFIX)
    canonical: list[str] = []
    for line in subroutine.splitlines():
        stripped = line.strip()
        if stripped == "G4 P10.0":
            continue
        if stripped.startswith("o<tcpc_pair_live_guard> call"):
            continue
        if stripped.startswith("o<tcpc_gap_motion_ready_guard> call"):
            continue
        if stripped.startswith("o<tcpc_contact_trace_begin> call"):
            line = re.sub(
                r"(o<tcpc_contact_trace_begin> call \[[^]]+\])(?: \[[^]]+\])?$",
                r"\1",
                line,
            )
        canonical.append(line)
    return "\n".join(canonical)


def validate_motion_subroutines(text: str) -> None:
    require(sha256(ATTEMPT5_RUNNER) == ATTEMPT5_RUNNER_SHA256, "Attempt-5 motion source hash changed")
    attempt5 = read_ascii(ATTEMPT5_RUNNER)
    names = (
        "tcpc_probe_counter_guard",
        "tcpc_vector_sphere_pass4",
        "tcpc_measure_pose",
        "tcpc_primary_closure_guard",
        "tcpc_primary_low_tilt_block",
        "tcpc_primary_tilt_block",
        "tcpc_primary_b0_sweep",
        "tcpc_baseline_return_top_clear",
    )
    for name in names:
        source = extract_oword(attempt5, name, "sub", "endsub")
        candidate = extract_oword(text, name, "sub", "endsub")
        require(
            canonical_geometry_subroutine(candidate) == canonical_geometry_subroutine(source),
            f"canonical motion/geometry body o<{name}> differs from frozen Attempt 5",
        )


def validate_closure_guards(text: str) -> None:
    internal = extract_oword(text, "tcpc_primary_closure_guard", "sub", "endsub")
    external = extract_oword(text, "tcpc_external_continuity_guard", "sub", "endsub")
    require_count(internal, "GT 0.050", 1, "same-run closure predicate")
    require_count(internal, ",0.050,#<closure_pass>", 1, "same-run logged limit")
    require_count(internal, "exceeds 0.050 mm", 1, "same-run closure abort")
    require("0.100" not in internal, "same-run closure guard contains external tolerance")
    require_count(external, "GT 0.100", 1, "external continuity predicate")
    require_count(external, ",0.100,#<external_pass>", 1, "external logged limit")
    require_count(external, "cross-attempt continuity exceeds 0.100 mm", 1, "external continuity abort")
    require("GT 0.050" not in external and ",0.050," not in external, "external guard silently uses same-run tolerance")
    require_count(internal, "#978 = [#978 + 1.0]", 1, "same-run closure counter")
    require_count(external, "#978 = [#978 + 1.0]", 1, "external closure counter")


def expected_pose_tail() -> list[tuple[int, int, int]]:
    rows: list[tuple[int, int, int]] = []
    sequence = 24
    for b_deg in (10, -10, 15, -15):
        for c_deg in (0, 45, 90, 180, 225, 270, 0):
            rows.append((sequence, b_deg, c_deg))
            sequence += 1
    for b_deg in (30, -30, 45, -45):
        for c_deg in (0, 90, 180, 270, 0):
            rows.append((sequence, b_deg, c_deg))
            sequence += 1
    rows.append((sequence, 0, 0))
    sequence += 1
    for b_deg in (60, -60, 90, -90):
        for c_deg in (0, 90, 180, 270, 0):
            rows.append((sequence, b_deg, c_deg))
            sequence += 1
    for c_deg in (0, 45, 90, 135, 180, 225, 270, 315, 0):
        rows.append((sequence, 0, c_deg))
        sequence += 1
    require(sequence == 102 and len(rows) == EXPECTED_ROWS, "internal expected tail is not seq24..101")
    return rows


def validate_topology(text: str) -> None:
    body = extract_oword(text, "run_relocated_t4_recovery", "if", "endif")
    low_calls = re.findall(r"^\s*o<tcpc_primary_low_tilt_block>\s+call\s+\[(-?\d+\.0)\]\s+\[(-?\d+\.0)\]", body, re.MULTILINE)
    tilt_calls = re.findall(r"^\s*o<tcpc_primary_tilt_block>\s+call\s+\[(-?\d+\.0)\]\s+\[(-?\d+\.0)\]", body, re.MULTILINE)
    require(low_calls == [("10.0", "10.0"), ("-10.0", "-10.0"), ("15.0", "15.0"), ("-15.0", "-15.0")], f"low-B continuation calls changed: {low_calls}")
    require(tilt_calls == [("30.0", "30.0"), ("-30.0", "-30.0"), ("45.0", "45.0"), ("-45.0", "-45.0"), ("60.0", "60.0"), ("-60.0", "-60.0"), ("90.0", "90.0"), ("-90.0", "-90.0")], f"quadrant continuation calls changed: {tilt_calls}")
    require_count(body, "o<tcpc_primary_b0_sweep> call [200.0]", 1, "closing B0 sweep")
    require("o<tcpc_primary_b0_sweep> call [100.0]" not in body, "Attempt-7 remeasures the opening B0 sweep")
    require_count(body, "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]", 1, "midpoint B0/C0 pose")
    require_assignment(body, 726, "23.0")
    require_assignment(body, 700, "1.0")
    for parameter, source in zip((701, 702, 703), (837, 838, 839), strict=True):
        require_assignment(body, parameter, f"#{source}")

    low = extract_oword(text, "tcpc_primary_low_tilt_block", "sub", "endsub")
    tilt = extract_oword(text, "tcpc_primary_tilt_block", "sub", "endsub")
    sweep = extract_oword(text, "tcpc_primary_b0_sweep", "sub", "endsub")
    low_c = [float(value) for value in re.findall(r"o<tcpc_measure_pose> call \[#<block_b>\] \[(-?\d+\.0)\]", low)]
    tilt_c = [float(value) for value in re.findall(r"o<tcpc_measure_pose> call \[#<block_b>\] \[(-?\d+\.0)\]", tilt)]
    sweep_c = [float(value) for value in re.findall(r"o<tcpc_measure_pose> call \[0\.0\] \[(-?\d+\.0)\]", sweep)]
    require(low_c == [0, 45, 90, 180, 225, 270, 0], f"low-B C topology changed: {low_c}")
    require(tilt_c == [0, 90, 180, 270, 0], f"quadrant C topology changed: {tilt_c}")
    require(sweep_c == [0, 45, 90, 135, 180, 225, 270, 315, 0], f"B0 sweep topology changed: {sweep_c}")

    rows = expected_pose_tail()
    require([sequence for sequence, _, _ in rows] == list(range(24, 102)), "tail IDs are not exactly 24..101")
    require(len(rows) * 2 * 4 == EXPECTED_TRACES, "tail trace derivation is not 624")

    # Four low closures, eight quadrant closures, midpoint-to-closing and closing
    # sweep closures are same-run. Eleven references cross Attempt-4 ownership.
    internal_closures = 4 + 8 + 2
    external_closures = 1 + 9 + 1
    require(internal_closures + external_closures == EXPECTED_CLOSURES, "closure derivation is not 25")
    outer = extract_oword(text, "tcpc_primary_outer_reference", "sub", "endsub")
    require("#<outer_base> = [800 + [3 * [#<outer_slot> - 1]]]" in outer, "outer A4 reference mapping changed")
    require_count(outer, "o<tcpc_external_continuity_guard> call", 1, "dynamic A4 outer continuity call")
    require_count(outer, "o<tcpc_primary_closure_guard> call [#790] [#791] [#792] [906.0] [72.0] [#726]", 1, "same-A7 midpoint-to-close closure")
    require_count(body, "o<tcpc_external_continuity_guard> call [#783] [#784] [#785] [905.0] [9.0] [#726]", 1, "A4 row9 to A7 midpoint continuity")
    require_count(body, "o<tcpc_external_continuity_guard> call [#780] [#781] [#782] [900.0] [1.0] [#726]", 1, "A4 row1 to A7 final continuity")
    require_count(body, "o<tcpc_external_continuity_guard> call", 2, "main-body external continuity calls")
    require_count(body, "[ABS[#978 - 25.0] GT 0.000001]", 1, "exact closure completion guard")
    require_count(body, "[ABS[#973 - 624.0] GT 0.000001]", 1, "exact trace completion guard")
    require_count(body, "[ABS[#726 - 101.0] GT 0.000001]", 1, "exact terminal sequence guard")
    require_count(body, "[ABS[#788 - #707] GT 0.000001]", 1, "exact result row guard")
    require_count(body, "[ABS[#977 - #707] GT 0.000001]", 1, "exact model row guard")

    require(9 + 14 + EXPECTED_ROWS == EXPECTED_COMPOSITE_ROWS, "composite summary derivation is not 101")
    require(72 + 112 + EXPECTED_TRACES == EXPECTED_COMPOSITE_TRACES, "composite trace derivation is not 808")
    require(1 + 2 + EXPECTED_CLOSURES == EXPECTED_COMPOSITE_CLOSURES, "composite closure derivation is not 28")


def validate_hardcoded_a4_centers(text: str) -> None:
    body = extract_oword(text, "run_relocated_t4_recovery", "if", "endif")
    require_count(body, A4_RESULTS_SHA_COMMENT, 1, "Attempt-4 source hash provenance")
    for parameter, value in zip((780, 781, 782), A4_CENTERS[0], strict=True):
        require_assignment(body, parameter, f"{value:.6f}")
    for parameter, value in zip((783, 784, 785), A4_CENTERS[8], strict=True):
        require_assignment(body, parameter, f"{value:.6f}")
    for slot, center in enumerate(A4_CENTERS):
        base = 800 + slot * 3
        for parameter, value in zip(range(base, base + 3), center, strict=True):
            require_assignment(body, parameter, f"{value:.6f}")


def validate_tool_offset_layers(text: str) -> None:
    require_assignment(text, 516, "229.407000")
    require_count(text, "#753 = #516", 1, "frozen T4 length copy")
    selector = extract_oword(text, "tcpc_pair_selector_guard", "sub", "endsub")
    require("ABS[#516 - #753]" in selector, "T4 length is not protected by the selector guard")

    initial_guards = {
        517: "o<motion_tlo_required> if [ABS[#517 - #516] GT 0.002]",
        518: "o<halui_tlo_required> if [ABS[#518 - #516] GT 0.002]",
        519: "o<kins_tlo_required> if [ABS[#519 - #516] GT 0.002]",
    }
    live_guards = {
        517: "o<pair_motion_tlo_live> if [ABS[#517 - #516] GT 0.002]",
        518: "o<pair_halui_tlo_live> if [ABS[#518 - #516] GT 0.002]",
        519: "o<pair_kins_tlo_live> if [ABS[#519 - #516] GT 0.002]",
    }
    for parameter, guard in initial_guards.items():
        require_count(text, guard, 1, f"initial TLO layer #{parameter} guard")
    live = extract_oword(text, "tcpc_pair_live_guard", "sub", "endsub")
    for parameter, guard in live_guards.items():
        require_count(live, guard, 1, f"live TLO layer #{parameter} guard")

    for axis in "xy":
        require_count(
            text,
            f"o<motion_tlo_{axis}_zero> if [ABS[#<_hal[motion.tooloffset.{axis}]>] GT 0.002]",
            1,
            f"initial zero {axis.upper()} tool-offset guard",
        )
        require_count(
            live,
            f"o<pair_tlo_{axis}_live> if [ABS[#<_hal[motion.tooloffset.{axis}]>] GT 0.002]",
            1,
            f"live zero {axis.upper()} tool-offset guard",
        )

    model = extract_oword(text, "tcpc_length_model_guard", "sub", "endsub")
    require_count(
        model,
        "[ABS[#<_hal[headheadkins.tool-offset-eval.length]> - #516] GT 0.002]",
        1,
        "length-model evaluated TLO guard",
    )
    require_count(
        model,
        "[ABS[#<_hal[headheadkins.length-model.q]>] GT 0.000001]",
        1,
        "T4 q-zero guard",
    )
    for axis in "xyz":
        require_count(
            model,
            f"[ABS[#<_hal[headheadkins.length-model.diff-offset.{axis}]>] GT 0.000001]",
            1,
            f"T4 differential {axis.upper()} zero guard",
        )


def validate_seeded_transition(text: str) -> None:
    require_assignment(text, 515, "25.0")
    require_count(text, "#504 = [[#501 / 2.0] - #502]", 1, "effective probe radius formula")
    require_count(text, "#505 = [#503 + #504]", 1, "effective contact radius formula")
    require_count(text, "#513 = [#505 + #509]", 1, "top-clear radius formula")

    measure = extract_oword(text, "tcpc_measure_pose", "sub", "endsub")
    require_count(measure, "o<use_high_z_transit> if [#700 GT 0.5]", 1, "seed-valid transit branch")
    for parameter, absolute, work in (
        (540, "#<_abs_x>", "#<_x>"),
        (541, "#<_abs_y>", "#<_y>"),
        (542, "#<_abs_z>", "#<_z>"),
    ):
        require_count(
            measure,
            f"#{parameter} = [{absolute} - {work}]",
            3,
            f"current coordinate-layer transform #{parameter}",
        )
    for axis, center_parameter, offset_parameter in (
        ("x", 701, 540),
        ("y", 702, 541),
        ("z", 703, 542),
    ):
        require_count(
            measure,
            f"#<current_clear_{axis}> = [#{center_parameter} - #{offset_parameter} - [#<current_w_{axis}> * #513]]",
            1,
            f"center-derived current-clear {axis.upper()} formula",
        )
    require_count(
        measure,
        "G1 X#<current_clear_x> Y#<current_clear_y> Z#<current_clear_z>",
        1,
        "center-derived first retract command",
    )
    require_count(measure, "#<safe_z> = [#<_z> + #515]", 1, "25 mm high-Z lift target")
    require_count(measure, "G1 Z#<safe_z>", 1, "high-Z lift command")
    require_count(measure, "G1 B#<target_b> C#<target_c>", 1, "target rotary index command")


def validate_resume_start(text: str) -> None:
    for parameter in (774, 775, 776):
        require_assignment(text, parameter, "0.000000000")
    require_assignment(text, 778, f"{RESUME_TOLERANCE:.3f}")
    for parameter, value in zip((831, 832, 833), RESUME_ABSOLUTE, strict=True):
        require_assignment(text, parameter, f"{value:.9f}")
    for parameter, value in zip((837, 838, 839), A6_SEQ23_CENTER, strict=True):
        require_assignment(text, parameter, f"{value:.9f}")
    for parameter, value in zip((843, 844, 845), G54_OFFSETS, strict=True):
        require_assignment(text, parameter, f"{value:.9f}")

    runner_work = tuple(float(assignment_literals(text, parameter)[0]) for parameter in (774, 775, 776))
    runner_absolute = tuple(float(assignment_literals(text, parameter)[0]) for parameter in (831, 832, 833))
    runner_g54 = tuple(float(assignment_literals(text, parameter)[0]) for parameter in (843, 844, 845))
    for axis, (work, absolute, g54, tlo) in enumerate(
        zip(runner_work, runner_absolute, runner_g54, ACTIVE_TLO, strict=True)
    ):
        require(
            abs(absolute - work - g54 - tlo) <= 1e-9,
            f"runner {chr(88 + axis)} coordinate layers do not satisfy absolute=work+G54+TLO",
        )

    frozen_pairs = (
        (774, 827), (775, 828), (776, 829), (778, 830),
        (831, 834), (832, 835), (833, 836),
        (837, 840), (838, 841), (839, 842),
        (843, 846), (844, 847), (845, 848),
    )
    for source, frozen in frozen_pairs:
        require_count(text, f"#{frozen} = #{source}", 1, f"resume constant #{source} frozen copy")

    selector = extract_oword(text, "tcpc_pair_selector_guard", "sub", "endsub")
    for source, frozen in frozen_pairs:
        require(f"ABS[#{source} - #{frozen}]" in selector, f"resume constant #{source} is not covered by selector guard")

    start_guard = extract_oword(text, "tcpc_resume_start_guard", "sub", "endsub")
    require_count(start_guard, "[ABS[#5220 - 1.0] GT 0.000001]", 1, "active G54 guard")
    for axis, parameter in zip("xyz", (843, 844, 845), strict=True):
        index = {"x": 5201, "y": 5202, "z": 5203}[axis]
        require_count(
            start_guard,
            f"[ABS[#[{index} + [20 * #5220]] - #{parameter}] GT #778]",
            1,
            f"frozen G54 {axis.upper()} offset guard",
        )
    for axis, parameter in zip("xyz", (774, 775, 776), strict=True):
        require_count(
            start_guard,
            f"o<resume_work_{axis}_required> if [ABS[#<_{axis}> - #{parameter}] GT #778]",
            1,
            f"G54 work {axis.upper()} guard",
        )
    for axis, parameter in zip("xyz", (831, 832, 833), strict=True):
        require_count(
            start_guard,
            f"o<resume_abs_{axis}_required> if [ABS[#<_abs_{axis}> - #{parameter}] GT #778]",
            1,
            f"absolute {axis.upper()} guard",
        )
    require("#833" not in re.search(r"o<g54_expected_z>.*?o<g54_expected_z> endif", start_guard, re.DOTALL).group(0), "G54 Z guard incorrectly uses absolute-Z #833")
    require("#845" in start_guard, "G54 Z guard does not use frozen G54-Z #845")
    require_count(text, "o<tcpc_resume_start_guard> call", 2, "pre/post-M0 coordinate start guard")

    # The coordinate layers are separate: absolute = work + G54 + active TLO.
    for axis_index in (0, 1):
        residual = RESUME_ABSOLUTE[axis_index] - RESUME_WORK[axis_index] - G54_OFFSETS[axis_index] - ACTIVE_TLO[axis_index]
        require(abs(residual) <= 1e-9, f"nominal {chr(88 + axis_index)} coordinate layers are inconsistent")
    z_residual = RESUME_ABSOLUTE[2] - RESUME_WORK[2] - G54_OFFSETS[2] - ACTIVE_TLO[2]
    require(abs(z_residual) <= 1e-9, "nominal Z = work + G54 + TLO relationship is inconsistent")

    body = extract_oword(text, "run_relocated_t4_recovery", "if", "endif")
    require("center-derived" in text and "Attempt-6 sequence-23" in text, "operator header does not identify the A6-center-derived first clear")
    require_count(body, A6_PARTIAL_ARCHIVE_ROOT, 1, "Attempt-6 partial archive provenance")
    for parameter, source in zip((701, 702, 703), (837, 838, 839), strict=True):
        require_assignment(body, parameter, f"#{source}")
    for parameter in (840, 841, 842):
        require(f"#{parameter}" not in body, f"frozen-copy parameter #{parameter} is used as motion state")

    body_lines = executable_lines(body)
    seed_matches = [index for index, line in enumerate(body_lines) if line == "#703 = #839"]
    require(len(seed_matches) == 1, "exact Attempt-6 sequence-23 center seed is missing or duplicated")
    seed_end = seed_matches[0]
    calls_after_seed = [
        line for line in body_lines[seed_end + 1 :] if re.match(r"^o<[^>]+> call\b", line)
    ]
    require(bool(calls_after_seed), "continuation has no call after the Attempt-6 center seed")
    first_call_after_seed = calls_after_seed[0]
    require(
        first_call_after_seed == "o<tcpc_primary_low_tilt_block> call [10.0] [10.0]",
        f"first continuation call is not full sequence-24 B+10 block: {first_call_after_seed}",
    )

    lines = executable_lines(text)
    hold_indices = [index for index, line in enumerate(lines) if line == "M0"]
    require(len(hold_indices) == 1, "runner must have exactly one M0")
    hold_index = hold_indices[0]
    pre_calls = [index for index, line in enumerate(lines) if line == "o<tcpc_resume_start_guard> call" and index < hold_index]
    post_calls = [index for index, line in enumerate(lines) if line == "o<tcpc_resume_start_guard> call" and index > hold_index]
    require(len(pre_calls) == 1 and len(post_calls) == 1, "resume start guard is not called once on each side of M0")
    require(lines[hold_index + 1] == "o<tcpc_pair_hold_position_guard> call", "0.001 hold-position guard is not first after M0")
    hold_guard = extract_oword(text, "tcpc_pair_hold_position_guard", "sub", "endsub")
    require_count(hold_guard, "GT 0.001", 3, "post-M0 absolute XYZ hold tolerance")
    body_start = next(index for index, line in enumerate(lines) if line.startswith("o<run_relocated_t4_recovery> if"))
    require(body_start > hold_index, "continuation body appears before the sole hold")


def validate_main_pre_hold_path(text: str) -> None:
    main: list[str] = []
    sub_depth = 0
    for raw_line in text.splitlines():
        line = " ".join(strip_parenthesized_comments(raw_line).split())
        if re.match(r"^o<[^>]+> sub\b", line):
            sub_depth += 1
            continue
        if re.match(r"^o<[^>]+> endsub\b", line):
            sub_depth -= 1
            require(sub_depth >= 0, "negative subroutine depth")
            continue
        if sub_depth == 0 and line:
            main.append(line)
    require(sub_depth == 0, "unclosed subroutine while deriving main path")
    hold = main.index("M0")
    pre_hold = main[:hold]
    motion_re = re.compile(r"(?:^|\s)G(?:0|00|1|01|2|02|3|03|38\.)\b")
    require(not [line for line in pre_hold if motion_re.search(line)], "main path contains axis motion before M0")
    unsafe_m_re = re.compile(r"^M(?:0?3|0?4|0?6|1?9|6[234])\b")
    require(not [line for line in pre_hold if unsafe_m_re.match(line)], "main path contains spindle/tool motion before M0")
    pre_hold_calls = [line for line in pre_hold if re.match(r"^o<[^>]+> call\b", line)]
    require(
        pre_hold_calls
        == [
            "o<tcpc_pair_coordinate_guard> call",
            "o<tcpc_length_model_guard> call",
            "o<tcpc_resume_start_guard> call",
            "o<tcpc_probe_counter_guard> call",
        ],
        f"unexpected pre-M0 subroutine call path: {pre_hold_calls}",
    )
    require(
        main[hold - 5 : hold]
        == [
            "M66 E0 L0",
            "o<tcpc_probe_counter_guard> call",
            "#850 = #<_hal[counter.0.counts]>",
            "#851 = #<_hal[counter.1.counts]>",
            "#852 = #<_hal[counter.2.counts]>",
        ],
        "pre-M0 raw/mux/gated origin capture changed",
    )
    expected_post_hold = [
        "o<tcpc_pair_hold_position_guard> call",
        "o<tcpc_pair_selector_guard> call",
        "o<tcpc_resume_start_guard> call",
        "o<tcpc_pair_live_guard> call [1.0] [0.0] [0.0] [1.0]",
        "o<tcpc_length_model_guard> call",
        "#940 = #850",
        "#941 = #851",
        "#942 = #852",
        "#950 = #850",
        "#951 = #851",
        "#952 = #852",
        "#953 = 0.0",
        "#954 = 1.0",
        "#955 = 1.0",
        "o<tcpc_gap_motion_ready_guard> call [0.0] [0.0]",
    ]
    require(main[hold + 1 : hold + 1 + len(expected_post_hold)] == expected_post_hold, "post-M0 chatter is not closed from the pre-hold origin")


def validate_output_paths(text: str) -> None:
    log_paths = re.findall(r"^\s*\(LOGAPPEND,([^\r\n)]+)\)\s*$", text, re.MULTILINE)
    expected = {str(path) for path in A7_PATHS.values()}
    require(set(log_paths) == expected, f"LOGAPPEND path set is not the six Attempt-7 outputs: {set(log_paths)}")
    require(len(log_paths) == 7, f"LOGAPPEND site count is {len(log_paths)}, expected 7 (two closure guards)")
    require(all(A7_PREFIX in path for path in log_paths), "a LOGAPPEND can mutate an older attempt")
    require(not any(A4_PREFIX in path for path in log_paths), "runner contains an Attempt-4 mutation path")
    require(not any(A5_PREFIX in path for path in log_paths), "runner contains an Attempt-5 mutation path")


def validate_runner_text(text: str, *, enforce_hash: bool) -> None:
    require("\x00" not in text, "runner contains NUL")
    validate_oword_balance(text)
    if enforce_hash:
        require(RUNNER_SHA256 != "FROZEN_HASH_PENDING", "validator has not been frozen to a runner hash")
        require(text_sha256(text) == RUNNER_SHA256, "Attempt-7 runner hash changed")

    require_assignment(text, 711, "41.0")
    require_assignment(text, 715, "2026082701.0")
    require_assignment(text, 727, "7.0")
    require_assignment(text, 707, "78.0")
    require_assignment(text, 717, "0.154742")
    require_count(text, "#3032 = #717", 1, "frozen #3032 install")
    require_count(text, "[ABS[#711 - 41.0] GT 0.000001]", 1, "mode-41 hard guard")
    require_count(text, "[ABS[#711 - 41.0] LT 0.1]", 1, "single mode-41 body predicate")
    require_count(text, "#730 = #711", 1, "frozen mode selector")
    require_count(text, "#734 = #727", 1, "frozen attempt selector")
    require_count(
        text,
        "[ABS[[[#<_hal[headheadtwp.current_joint_b]> + 540.0] MOD 360.0] - 180.0] GT 0.05]",
        1,
        "B0 resume guard",
    )
    require_count(
        text,
        "[ABS[[[#<_hal[headheadtwp.current_joint_c]> + 540.0] MOD 360.0] - 180.0] GT 0.05]",
        1,
        "C0 resume guard",
    )
    require_count(text, "#756 = 10.00", 1, "10-second ignore/release contract")
    require_count(text, "#777 = 15.0", 1, "continuous quiet-duration contract")
    require_count(text, "#779 = 900.0", 1, "cumulative quiet-timeout contract")
    require_count(text, "#793 = 0.25", 1, "quiet sample-period contract")
    require_count(text, "#789 = #779", 1, "frozen quiet-timeout selector")
    require_count(text, "#794 = #777", 1, "frozen quiet-duration selector")
    require_count(text, "#795 = #793", 1, "frozen quiet-sample selector")
    require_count(text, "#759 = 1.0", 1, "minimum contact travel contract")
    require_count(text, "#739 = 1.0", 1, "no-retry pose contract")
    require_count(text, "#501 = 6.0", 1, "T4 probe diameter")
    require_count(text, "#516 = 229.407000", 1, "T4 H4 length")
    executable = executable_lines(text)
    forbidden_motion = ("G43", "G49", "G52", "G92", "M3", "M4")
    for line in executable:
        require(not any(re.match(rf"^{code}(?:\s|$)", line) for code in forbidden_motion), f"forbidden modal/spindle command: {line}")

    validate_tool_offset_layers(text)
    validate_resume_start(text)
    validate_seeded_transition(text)
    validate_main_pre_hold_path(text)
    validate_output_paths(text)
    validate_probe_geometry(text)
    validate_gap_context_ownership(text)
    validate_motion_subroutines(text)
    validate_closure_guards(text)
    validate_topology(text)
    validate_hardcoded_a4_centers(text)


def validate_reachability() -> dict[str, float | int]:
    for path, expected in REACH_PREREQUISITE_SHA256.items():
        require(sha256(path) == expected, f"reachability prerequisite changed: {path.name}")

    sys.path.insert(0, str(HERE))
    try:
        import numpy as np
        import analyze_tcpc_relocated_sphere_reachability as reach
        import analyze_tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery_reachability as a3
    except ImportError as exc:
        raise ValidationError(f"reachability import failed: {exc}") from exc

    center = np.asarray(A6_SEQ23_CENTER, dtype=float)
    nominal_start = np.asarray(RESUME_ABSOLUTE, dtype=float)
    pins = a3.merged_model_pins()
    limits = reach.parse_limits(VALIDATION_INI)
    poses = reach.grid()
    require(len(poses) == 101, "reachability source grid is not 101 poses")
    require([pose.slot for pose in poses[23:]] == list(range(24, 102)), "reachability tail is not seq24..101")

    # The accepted sequence-23 center supplies state, while the operator has
    # established the physical B0/C0 start. The synthetic seed therefore uses
    # B0/C0 and contributes no probe contacts.
    seed_pose = reach.Pose(23, 0.0, 0.0, "attempt6_seq23_b0_resume_seed")
    replayed = reach.replay(
        center,
        pins,
        limits,
        tool=4,
        length=229.407000,
        effective_radius=reach.T4_EFFECTIVE_RADIUS,
        poses=[seed_pose, *poses[23:]],
    )
    first = next(
        index
        for index, sample in enumerate(replayed)
        if sample.slot == 24 and sample.kind == "transit_lift"
    )
    samples = list(replayed[first:])
    computed_clear = center - np.asarray((0.0, 0.0, -1.0)) * TOP_CLEAR_RADIUS

    def coordinate_axis_vertices() -> tuple[tuple[float, float, float, float], ...]:
        # Independent variables are work, G54, and active TLO deviations. The
        # fourth value is their sum and is constrained by the absolute guard.
        bounds = (RESUME_TOLERANCE, RESUME_TOLERANCE, TOOL_OFFSET_TOLERANCE)
        rows: list[np.ndarray] = []
        rhs: list[float] = []
        for index, bound in enumerate(bounds):
            unit = np.zeros(3)
            unit[index] = 1.0
            rows.extend((unit, -unit))
            rhs.extend((bound, bound))
        rows.extend((np.ones(3), -np.ones(3)))
        rhs.extend((RESUME_TOLERANCE, RESUME_TOLERANCE))
        matrix = np.asarray(rows)
        vector = np.asarray(rhs)
        vertices: set[tuple[float, float, float, float]] = set()
        for active in itertools.combinations(range(len(vector)), 3):
            equalities = matrix[list(active)]
            if abs(float(np.linalg.det(equalities))) < 1e-12:
                continue
            candidate = np.linalg.solve(equalities, vector[list(active)])
            if np.all(matrix @ candidate <= vector + 1e-10):
                absolute = float(np.sum(candidate))
                vertices.add(tuple(round(float(value), 12) for value in (*candidate, absolute)))
        ordered = tuple(sorted(vertices))
        require(len(ordered) == 12, f"coordinate-axis feasible polytope has {len(ordered)} vertices, expected 12")
        for work, g54, tlo, absolute in ordered:
            require(abs(work) <= RESUME_TOLERANCE + 1e-12, "work vertex exceeds guard")
            require(abs(g54) <= RESUME_TOLERANCE + 1e-12, "G54 vertex exceeds guard")
            require(abs(tlo) <= TOOL_OFFSET_TOLERANCE + 1e-12, "TLO vertex exceeds guard")
            require(abs(absolute) <= RESUME_TOLERANCE + 1e-12, "absolute vertex exceeds guard")
            require(abs(absolute - work - g54 - tlo) <= 1e-12, "coordinate vertex violates absolute relationship")
        return ordered

    axis_vertices = coordinate_axis_vertices()
    coordinate_states = tuple(itertools.product(axis_vertices, repeat=3))
    require(len(coordinate_states) == 1728, "combined XYZ coordinate-state vertex count is not 1728")
    absolute_deviations = {
        tuple(axis_state[3] for axis_state in state)
        for state in coordinate_states
    }
    require(len(absolute_deviations) == 64, "combined coordinate vertices do not reduce to 64 distinct physical starts")

    def segment_clearance(start: np.ndarray, end: np.ndarray) -> float:
        delta = end - start
        fraction = float(np.clip(np.dot(center - start, delta) / np.dot(delta, delta), 0.0, 1.0))
        closest = start + fraction * delta
        return float(np.linalg.norm(closest - center) - EFFECTIVE_CONTACT_RADIUS)

    nominal_handoff = float(np.linalg.norm(nominal_start - computed_clear))
    nominal_sphere_clearance = float(np.linalg.norm(nominal_start - center) - EFFECTIVE_CONTACT_RADIUS)
    worst_handoff = 0.0
    minimum_sphere_clearance = math.inf
    handoff_deviations = absolute_deviations | {(0.0, 0.0, 0.0)}
    require(len(handoff_deviations) == 65, "exact current start plus coordinate corners are not 65 physical handoffs")
    for deviation in sorted(handoff_deviations):
        start = nominal_start + np.asarray(deviation)
        worst_handoff = max(worst_handoff, float(np.linalg.norm(start - computed_clear)))
        minimum_sphere_clearance = min(minimum_sphere_clearance, segment_clearance(start, computed_clear))
        for point in reach.linear_points(start, computed_clear, maximum_step=0.01):
            reach.append_sample(samples, 4, 229.407000, seed_pose, "resume_handoff", point, pins, limits, 0.0, 0.0)

    require(abs(nominal_handoff - 1.4256688565432931) <= 1e-9, f"nominal center-derived handoff changed: {nominal_handoff:.12f} mm")
    require(abs(nominal_sphere_clearance - 3.886021634318219) <= 1e-9, f"nominal sphere clearance changed: {nominal_sphere_clearance:.12f} mm")
    require(abs(minimum_sphere_clearance - 3.8335128802530605) <= 1e-9, f"worst coordinate-vertex sphere clearance changed: {minimum_sphere_clearance:.12f} mm")
    require(minimum_sphere_clearance > 3.8, "coordinate tolerance corners consume initial sphere clearance")
    post_direction = np.asarray((-1.0, 1.0, -1.0), dtype=float) / math.sqrt(3.0)
    post_start = center + post_direction * 15.0

    def post_clearance(point: np.ndarray) -> float:
        offset = point - post_start
        along = max(0.0, float(np.dot(offset, post_direction)))
        return float(np.linalg.norm(offset - along * post_direction) - 18.0)

    entry_kinds = {"transit_lift", "transit_rotary", "transit_xy", "transit_descend", "top_clear"}
    entry_samples = [
        sample for sample in samples
        if sample.kind == "resume_handoff"
        or (sample.slot == 24 and sample.kind in entry_kinds)
    ]
    require(entry_samples, "independent replay produced no first-entry samples")
    minimum_entry_post = min(post_clearance(sample.tcp) for sample in entry_samples)
    minimum_entry_sphere = min(
        float(np.linalg.norm(sample.tcp - center) - EFFECTIVE_CONTACT_RADIUS)
        for sample in entry_samples
    )
    require(minimum_entry_post > 0.0, "first entry intersects effective post envelope")
    require(minimum_entry_sphere > 0.0, "first entry intersects effective sphere envelope")
    margins = [
        *(float(sample.joint_margins[index]) for index in range(3) for sample in samples),
        *(float(sample.axis_margins[index]) for index in range(3) for sample in samples),
    ]
    minimum_nominal = min(margins)
    # Existing 2 mm center plus 3 mm path/model reserve, with the 0.050 mm
    # absolute handoff envelope charged again as an explicit conservative term.
    remaining = minimum_nominal - 5.050
    require(remaining >= 10.0, f"reachability has only {remaining:.6f} mm after reserve")
    return {
        "poses": EXPECTED_ROWS,
        "samples": len(samples),
        "coordinate_vertices": len(coordinate_states),
        "physical_starts": len(absolute_deviations),
        "handoff_paths": len(handoff_deviations),
        "nominal_handoff_mm": nominal_handoff,
        "worst_handoff_mm": worst_handoff,
        "nominal_sphere_clearance_mm": nominal_sphere_clearance,
        "minimum_sphere_clearance_mm": minimum_sphere_clearance,
        "minimum_entry_post_clearance_mm": minimum_entry_post,
        "minimum_entry_sphere_clearance_mm": minimum_entry_sphere,
        "minimum_nominal_margin_mm": minimum_nominal,
        "remaining_margin_mm": remaining,
    }


def simulate_quiet_window(
    samples: list[tuple[float, float, float, int, int, int, int, int, int]],
    *,
    force: bool = True,
    entry: tuple[float, float, float, int, int, int, int, int, int] | None = None,
    origin_raw: float = 0,
    origin_mux: float = 0,
    anchor_raw: float = 0,
    anchor_mux: float = 0,
    anchor_gated: float = 0,
    budget_s: float = QUIET_TIMEOUT_S,
) -> float:
    """Reference the runner's counter/level quiet semantics at 0.25 s samples."""
    def valid_counter(value: float, label: str) -> None:
        require(math.isfinite(value) and value >= 0 and abs(value - math.floor(value)) <= 1e-9, f"reference quiet {label} counter invalid")

    if entry is None:
        entry = (anchor_raw, anchor_mux, anchor_gated, 0, 0, 0, 0, 0, 0)
    raw, mux, gated, raw_level, mux_level, gated_level, abnormal, fault, ignore = entry
    for value, label in ((raw, "raw"), (mux, "mux"), (gated, "gated")):
        valid_counter(value, label)
    require(raw >= anchor_raw and mux >= anchor_mux, "reference quiet counter rollback")
    require(gated == anchor_gated and not gated_level, "reference quiet outside-G38 gated change")
    require(0.0 <= budget_s <= QUIET_TIMEOUT_S, "reference quiet remaining budget invalid")

    stable = 0.0
    elapsed = 0.0
    last_raw = raw
    last_mux = mux
    required = (
        force
        or raw != anchor_raw
        or mux != anchor_mux
        or (raw - origin_raw) != (mux - origin_mux)
        or bool(raw_level or mux_level or abnormal or fault or ignore)
    )
    if not required:
        return 0.0
    for raw, mux, gated, raw_level, mux_level, gated_level, abnormal, fault, ignore in samples:
        elapsed += QUIET_SAMPLE_S
        if elapsed > budget_s + 1e-12:
            break
        for value, label in ((raw, "raw"), (mux, "mux"), (gated, "gated")):
            valid_counter(value, label)
        require(raw >= last_raw and mux >= last_mux, "reference quiet counter rollback")
        require(gated == anchor_gated and not gated_level, "reference quiet outside-G38 gated change")
        changed = raw != last_raw or mux != last_mux
        levels_clear = not (raw_level or mux_level or abnormal or fault)
        totals_match = (raw - origin_raw) == (mux - origin_mux)
        if not changed and levels_clear and totals_match:
            stable += QUIET_SAMPLE_S
        else:
            stable = 0.0
        if stable >= QUIET_DURATION_S and not ignore:
            return elapsed
        last_raw, last_mux = raw, mux
    raise ValidationError("reference quiet timeout or persistent final mismatch")


def validate_quiet_reference_model() -> int:
    clear = (0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0)
    cases = 0

    def expect_elapsed(label: str, expected: float, *args: object, **kwargs: object) -> None:
        nonlocal cases
        elapsed = simulate_quiet_window(*args, **kwargs)
        require(abs(elapsed - expected) <= 1e-12, f"reference case {label} elapsed {elapsed}, expected {expected}")
        cases += 1

    def expect_failure(label: str, *args: object, **kwargs: object) -> None:
        nonlocal cases
        try:
            simulate_quiet_window(*args, **kwargs)
        except ValidationError:
            cases += 1
        else:
            raise ValidationError(f"reference quiet accepted {label}")

    expect_elapsed("clean bypass", 0.0, [], force=False)
    expect_elapsed("forced clean", 15.0, [clear] * 60)
    for burst in (1.0, 24.0, 1000.0):
        level = (burst, burst, 0.0, 0, 0, 0, 0, 0, 0)
        expect_elapsed(
            f"matched burst {int(burst)}",
            15.0,
            [level] * 60,
            force=False,
            entry=level,
        )

    matched_one = (1.0, 1.0, 0.0, 0, 0, 0, 0, 0, 0)
    late_reset = [clear] * 58 + [matched_one] + [matched_one] * 60
    expect_elapsed("edge at 14.75 seconds resets full window", 29.75, late_reset)
    storm = [(float(index), float(index), 0.0, 0, 0, 0, 0, 0, 0) for index in range(1, 3601)]
    expect_failure("sustained matched storm", storm)

    raw_skew = (1.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0)
    skew_caught = (1.0, 1.0, 0.0, 0, 0, 0, 0, 0, 0)
    expect_elapsed("transient skew catch-up", 15.25, [skew_caught] + [skew_caught] * 60, entry=raw_skew)
    expect_failure("persistent raw-mux mismatch", [raw_skew] * 3600, entry=raw_skew)
    expect_failure("gated counter change", [], entry=(0.0, 0.0, 1.0, 0, 0, 0, 0, 0, 0))
    expect_failure("gated input level", [], entry=(0.0, 0.0, 0.0, 0, 0, 1, 0, 0, 0))
    expect_failure("raw rollback", [], entry=(-1.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0))
    expect_failure("mux rollback", [], entry=(0.0, -1.0, 0.0, 0, 0, 0, 0, 0, 0))
    expect_failure("raw non-integral", [], entry=(0.5, 0.0, 0.0, 0, 0, 0, 0, 0, 0))
    expect_failure("mux non-integral", [], entry=(0.0, 0.5, 0.0, 0, 0, 0, 0, 0, 0))
    expect_failure("gated non-integral", [], entry=(0.0, 0.0, 0.5, 0, 0, 0, 0, 0, 0))

    faulted = (0.0, 0.0, 0.0, 0, 0, 0, 1, 1, 0)
    expect_elapsed("transient abnormal and fault", 15.0, [clear] * 60, entry=faulted)
    expect_failure("persistent fault", [faulted] * 3600, entry=faulted)
    ignored = (0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 1)
    expect_elapsed("ignore clears after stable interval", 20.25, [ignored] * 80 + [clear], entry=ignored)
    expect_failure("persistent ignore", [ignored] * 3600, entry=ignored)

    first = simulate_quiet_window([clear] * 60)
    second = simulate_quiet_window([clear] * 60, budget_s=QUIET_TIMEOUT_S - first)
    require(abs(first + second - 30.0) <= 1e-12, "reference cumulative wrapper retries did not retain elapsed time")
    cases += 1
    cumulative = 0.0
    for _ in range(60):
        cumulative += simulate_quiet_window([clear] * 60, budget_s=QUIET_TIMEOUT_S - cumulative)
    require(abs(cumulative - QUIET_TIMEOUT_S) <= 1e-12, "reference cumulative budget did not reach exactly 900 seconds")
    cases += 1
    expect_failure("next wrapper invocation after cumulative timeout", [clear] * 60, budget_s=QUIET_TIMEOUT_S - cumulative)
    return cases


def replace_once(text: str, old: str, new: str) -> str:
    require(text.count(old) == 1, f"self-test target is not unique: {old}")
    return text.replace(old, new, 1)


def self_test(base: str) -> int:
    validate_quiet_reference_model()
    mutations = {
        "mode assignment": ("#711 = 41.0", "#711 = 40.0"),
        "campaign assignment": ("#715 = 2026082701.0", "#715 = 2026082702.0"),
        "attempt assignment": ("#727 = 7.0", "#727 = 6.0"),
        "row contract": ("#707 = 78.0", "#707 = 77.0"),
        "T4 length": ("#516 = 229.407000", "#516 = 129.407000"),
        "initial TLO layer": (
            "o<motion_tlo_required> if [ABS[#517 - #516] GT 0.002]",
            "o<motion_tlo_required> if [ABS[#517 - #516] GT 0.020]",
        ),
        "live TLO layer": (
            "o<pair_kins_tlo_live> if [ABS[#519 - #516] GT 0.002]",
            "o<pair_kins_tlo_live> if [ABS[#519 - #516] GT 0.020]",
        ),
        "zero X tool offset": (
            "o<motion_tlo_x_zero> if [ABS[#<_hal[motion.tooloffset.x]>] GT 0.002]",
            "o<motion_tlo_x_zero> if [ABS[#<_hal[motion.tooloffset.x]>] GT 0.020]",
        ),
        "resume tolerance": ("#778 = 0.050", "#778 = 0.500"),
        "resume work X": ("#774 = 0.000000000", "#774 = 1.000000000"),
        "resume absolute Z": ("#833 = -280.866128272", "#833 = -510.273128272"),
        "G54 Z offset": ("#845 = -510.273128272", "#845 = -280.866128272"),
        "G54 Z frozen copy": ("#848 = #845", "#848 = #833"),
        "G54 Z predicate cross-wire": (
            "o<g54_expected_z> if [ABS[#[5203 + [20 * #5220]] - #845] GT #778]",
            "o<g54_expected_z> if [ABS[#[5203 + [20 * #5220]] - #833] GT #778]",
        ),
        "work Z predicate cross-wire": (
            "o<resume_work_z_required> if [ABS[#<_z> - #776] GT #778]",
            "o<resume_work_z_required> if [ABS[#<_z> - #833] GT #778]",
        ),
        "absolute Z predicate cross-wire": (
            "o<resume_abs_z_required> if [ABS[#<_abs_z> - #833] GT #778]",
            "o<resume_abs_z_required> if [ABS[#<_abs_z> - #845] GT #778]",
        ),
        "center seed source": ("#701 = #837", "#701 = #840"),
        "seed Z source": ("#703 = #839", "#703 = -302.480083"),
        "A6 center X": ("#837 = 2501.156895000", "#837 = 2502.156895000"),
        "center-derived clear formula": (
            "#<current_clear_x> = [#701 - #540 - [#<current_w_x> * #513]]",
            "#<current_clear_x> = [#840 - #540 - [#<current_w_x> * #513]]",
        ),
        "high-Z lift": (
            "#<safe_z> = [#<_z> + #515]",
            "#<safe_z> = [#<_z> + #505]",
        ),
        "pre-M0 motion": (
            "#852 = #<_hal[counter.2.counts]>\nM0",
            "#852 = #<_hal[counter.2.counts]>\nG1 X0\nM0",
        ),
        "pre-M0 motion subroutine": (
            "o<tcpc_resume_start_guard> call\n(MSG, Confirm laser OFF",
            "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]\n(MSG, Confirm laser OFF",
        ),
        "pre-M0 counter origin removed": (
            "#850 = #<_hal[counter.0.counts]>",
            "#850 = #940",
        ),
        "hold tolerance": (
            "o<pair_hold_xyz_unchanged> if [[ABS[#<_abs_x> - #771] GT 0.001] OR [ABS[#<_abs_y> - #772] GT 0.001] OR [ABS[#<_abs_z> - #773] GT 0.001]]",
            "o<pair_hold_xyz_unchanged> if [[ABS[#<_abs_x> - #771] GT 0.010] OR [ABS[#<_abs_y> - #772] GT 0.010] OR [ABS[#<_abs_z> - #773] GT 0.010]]",
        ),
        "post-M0 coordinate recheck": (
            "o<tcpc_pair_selector_guard> call\no<tcpc_resume_start_guard> call\no<tcpc_pair_live_guard> call [1.0] [0.0] [0.0] [1.0]",
            "o<tcpc_pair_selector_guard> call\n(MSG, coordinate recheck removed)\no<tcpc_pair_live_guard> call [1.0] [0.0] [0.0] [1.0]",
        ),
        "post-M0 raw noise made immediately fatal": (
            "o<tcpc_resume_start_guard> call\no<tcpc_pair_live_guard> call [1.0] [0.0] [0.0] [1.0]",
            "o<tcpc_resume_start_guard> call\no<tcpc_pair_live_guard> call [1.0] [0.0] [0.0] [0.0]",
        ),
        "post-M0 pre-hold origin absorbed": (
            "#940 = #850\n#941 = #851\n#942 = #852",
            "#940 = #<_hal[counter.0.counts]>\n#941 = #<_hal[counter.1.counts]>\n#942 = #<_hal[counter.2.counts]>",
        ),
        "startup adaptive quiet removed": (
            "#955 = 1.0\no<tcpc_gap_motion_ready_guard> call [0.0] [0.0]",
            "#955 = 1.0\n(DEBUG, startup quiet removed)",
        ),
        "startup accepted baseline stale": (
            "#950 = #940\n#951 = #941\n#952 = #942\n#947 = 0.0",
            "#950 = #850\n#951 = #851\n#952 = #852\n#947 = 0.0",
        ),
        "B0 start guard": (
            "o<start_b_zero_required> if [ABS[[[#<_hal[headheadtwp.current_joint_b]> + 540.0] MOD 360.0] - 180.0] GT 0.05]",
            "o<start_b_zero_required> if [ABS[[[#<_hal[headheadtwp.current_joint_b]> + 540.0] MOD 360.0] - 180.0] GT 5.0]",
        ),
        "C0 start guard": (
            "o<start_c_zero_required> if [ABS[[[#<_hal[headheadtwp.current_joint_c]> + 540.0] MOD 360.0] - 180.0] GT 0.05]",
            "o<start_c_zero_required> if [ABS[[[#<_hal[headheadtwp.current_joint_c]> + 540.0] MOD 360.0] - 180.0] GT 5.0]",
        ),
        "outer row 4 X": ("#809 = 2501.122339", "#809 = 2502.122339"),
        "same-run tolerance": ("GT 0.050", "GT 0.100"),
        "external tolerance": ("GT 0.100", "GT 0.200"),
        "same-run abort": ("T4 primary same-pose closure exceeds 0.050 mm", "T4 primary closure warning only"),
        "external abort": ("T4 cross-attempt continuity exceeds 0.100 mm", "T4 external warning only"),
        "quiet duration below 15": ("#777 = 15.0", "#777 = 14.75"),
        "quiet timeout above 900": ("#779 = 900.0", "#779 = 901.0"),
        "quiet sample changed": ("#793 = 0.25", "#793 = 0.50"),
        "quiet duration selector disabled": (
            "[ABS[#777 - 15.0] GT 0.000001]",
            "[ABS[#777 - 150.0] GT 0.000001]",
        ),
        "quiet timeout restart": (
            "o<quiet_episode> while [[#944 LT #<quiet_budget>] AND [#<quiet_complete> LT 0.5]]",
            "o<quiet_episode> while [[#944 LT #779] AND [#<quiet_complete> LT 0.5]]",
        ),
        "quiet timeout predicate removed": (
            "o<quiet_episode_timeout> if [#<quiet_complete> LT 0.5]",
            "o<quiet_episode_timeout> if [#<quiet_complete> LT -0.5]",
        ),
        "quiet reset disabled": (
            "o<quiet_stable_sample> else\n        #<quiet_stable> = 0.0",
            "o<quiet_stable_sample> else\n        #<quiet_stable> = #<quiet_stable>",
        ),
        "motion inside quiet": (
            "(This routine is stationary by construction: only synchronization and dwell.)\n  M66 E0 L0",
            "(This routine is stationary by construction: only synchronization and dwell.)\n  G1 X0\n  M66 E0 L0",
        ),
        "operator hold inside quiet": (
            "(This routine is stationary by construction: only synchronization and dwell.)\n  M66 E0 L0",
            "(This routine is stationary by construction: only synchronization and dwell.)\n  M0\n  M66 E0 L0",
        ),
        "motion-ready helper motion": (
            "o<tcpc_gap_motion_ready_guard> sub\n  #<motion_ready_target_b> = #1",
            "o<tcpc_gap_motion_ready_guard> sub\n  G1 X0\n  #<motion_ready_target_b> = #1",
        ),
        "motion-ready helper recursion": (
            "o<tcpc_gap_motion_ready_guard> sub\n  #<motion_ready_target_b> = #1",
            "o<tcpc_gap_motion_ready_guard> sub\n  o<tcpc_gap_motion_ready_guard> call [#1] [#2]\n  #<motion_ready_target_b> = #1",
        ),
        "motion-ready raw noise made fatal": (
            "o<tcpc_pair_live_guard> call [1.0] [#<motion_ready_target_b>] [#<motion_ready_target_c>] [1.0]",
            "o<tcpc_pair_live_guard> call [1.0] [#<motion_ready_target_b>] [#<motion_ready_target_c>] [0.0]",
        ),
        "motion-ready conditional quiet removed": (
            "o<tcpc_gap_quiet_guard> call [#<motion_ready_target_b>] [#<motion_ready_target_c>] [0.0]",
            "(DEBUG, motion-ready quiet removed)",
        ),
        "sample live guard removed": (
            "M66 E0 L0\n      o<tcpc_pair_live_guard> call [1.0] [#<quiet_target_b>] [#<quiet_target_c>] [1.0]",
            "M66 E0 L0\n      (DEBUG, live guard removed)",
        ),
        "gated change ignored": (
            "o<quiet_gated_exact> if [ABS[#<quiet_gated> - #<quiet_anchor_gated>] GT 0.000001]",
            "o<quiet_gated_exact> if [ABS[#<quiet_raw> - #<quiet_anchor_raw>] GT 0.000001]",
        ),
        "final mismatch accepted": (
            "o<quiet_final_raw_mux_match> if [ABS[[#<quiet_raw> - #<quiet_consistency_raw>] - [#<quiet_mux> - #<quiet_consistency_mux>]] GT 0.000001]",
            "o<quiet_final_raw_mux_match> if [ABS[[#<quiet_raw> - #<quiet_consistency_raw>] - [#<quiet_mux> - #<quiet_consistency_mux>]] GT 999.0]",
        ),
        "fault final clear removed": (
            "o<quiet_final_levels> if [[[[#<_hal[t_probe-in]> + #<_hal[probe-mux]> + #<_hal[motion.probe-input]> + #<_hal[tcpc-probe-abnormal-level]> + #<_hal[tcpc_probe_fault_pause.out]> + #<_hal[tcpc_probe_gate_ignore.out]>] GT 0.5]]]",
            "o<quiet_final_levels> if [[[[#<_hal[t_probe-in]> + #<_hal[probe-mux]> + #<_hal[motion.probe-input]> + #<_hal[tcpc-probe-abnormal-level]> + #<_hal[tcpc_probe_fault_pause.width]> + #<_hal[tcpc_probe_gate_ignore.out]>] GT 0.5]]]",
        ),
        "ignore completion clear removed": (
            "o<quiet_complete_sample> if [[#<quiet_stable> GE #777] AND [#<_hal[tcpc_probe_gate_ignore.out]> LT 0.5]]",
            "o<quiet_complete_sample> if [[#<quiet_stable> GE #777] AND [#<_hal[tcpc_probe_gate_ignore.width]> GT 0.5]]",
        ),
        "fixed successful-contact dwell": (
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n\n  (Contact 2: start on the sign-aware upper U side and probe inward.)",
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n  G4 P15.0\n\n  (Contact 2: start on the sign-aware upper U side and probe inward.)",
        ),
        "post-contact quiet omitted": (
            "o<tcpc_contact_quiet_guard> call [#<release_target_b>] [#<release_target_c>] [1.0]",
            "(DEBUG, post-contact quiet removed)",
        ),
        "final gap quiet omitted": (
            "o<tcpc_gap_quiet_guard> call [#<final_target_b>] [#<final_target_c>] [1.0]",
            "(DEBUG, final gap quiet removed)",
        ),
        "matched chatter made fatal": (
            "o<trace_success_consistency_abort> if [[#962 GT 0.5] AND [#970 LT 0.5]]",
            "o<trace_success_consistency_abort> if [[[#962 GT 0.5] OR [#936 GT 0.5]] AND [#970 LT 0.5]]",
        ),
        "gap chatter made count-fatal": (
            "o<trace_gap_pre_g38_fault> if [#961 GT 0.5]",
            "o<trace_gap_pre_g38_fault> if [[#961 GT 0.5] OR [#959 GT #779]]",
        ),
        "gap quiet removed": (
            "o<trace_stationary_baseline> while [#<trace_baseline_ready> LT 0.5]\n    o<tcpc_gap_quiet_guard> call [#934] [#935] [0.0]",
            "o<trace_stationary_baseline> while [#<trace_baseline_ready> LT 0.5]\n    (DEBUG, pre-G38 gap quiet removed)",
        ),
        "second trace baseline stale": (
            "o<tcpc_pair_probe_ready_guard> call [#520] [#521]\n  o<tcpc_contact_trace_begin> call [1.0] [0.0]\n  o<tcpc_pair_probe_final_guard> call [#520] [#521]",
            "o<tcpc_pair_probe_ready_guard> call [#520] [#521]\n  o<tcpc_contact_trace_begin> call [1.0] [1.0]\n  o<tcpc_pair_probe_final_guard> call [#520] [#521]",
        ),
        "trace-begin resets gap budget": (
            "o<trace_gap_quiet_reset_forbidden> endif\n  #937 = #938",
            "o<trace_gap_quiet_reset_forbidden> endif\n  #947 = 0.0\n  #937 = #938",
        ),
        "accepted-contact gap reset removed": (
            "o<trace_post_log_live_guard> if [#970 LT 0.5]\n    #947 = 0.0",
            "o<trace_post_log_live_guard> if [#970 LT 0.5]\n    #947 = #947",
        ),
        "vector post-position quiet omitted": (
            "G1 X#<start_x> Y#<start_y> Z#<start_z>\n  o<tcpc_gap_motion_ready_guard> call [#520] [#521]",
            "G1 X#<start_x> Y#<start_y> Z#<start_z>\n  (DEBUG, post-position quiet removed)",
        ),
        "gap aggregate timeout reset": (
            "#<gap_quiet_budget> = [#779 - #948]",
            "#<gap_quiet_budget> = #779",
        ),
        "contact aggregate timeout reset": (
            "#<contact_quiet_budget> = [#779 - #976]",
            "#<contact_quiet_budget> = #779",
        ),
        "contact consistency origin stale": (
            "[#<contact_quiet_budget>] [#920] [#921]",
            "[#<contact_quiet_budget>] [#940] [#941]",
        ),
        "immediate skew force removed": (
            "o<trace_post_partition_skew> if [ABS[#<trace_post_raw_delta> - #<trace_post_mux_delta>] GT 0.000001]",
            "o<trace_post_partition_skew> if [ABS[#<trace_post_raw_delta> - #<trace_post_mux_delta>] GT 999.0]",
        ),
        "parser line too long": (
            "(TCPC length-aware T4 new-location continuation after Attempt-6 sequence 23.)",
            "(" + ("X" * 226) + ")",
        ),
        "first low block": (
            "o<tcpc_primary_low_tilt_block> call [10.0] [10.0]",
            "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]",
        ),
        "negative low block": (
            "o<tcpc_primary_low_tilt_block> call [-15.0] [-15.0]",
            "o<tcpc_primary_low_tilt_block> call [15.0] [-15.0]",
        ),
        "high block": (
            "o<tcpc_primary_tilt_block> call [-90.0] [-90.0]",
            "o<tcpc_primary_tilt_block> call [-60.0] [-90.0]",
        ),
        "opening remeasure": ("o<tcpc_primary_b0_sweep> call [200.0]", "o<tcpc_primary_b0_sweep> call [100.0]"),
        "closure count guard": ("[ABS[#978 - 25.0] GT 0.000001]", "[ABS[#978 - 26.0] GT 0.000001]"),
        "trace count guard": ("[ABS[#973 - 624.0] GT 0.000001]", "[ABS[#973 - 623.0] GT 0.000001]"),
        "terminal sequence": ("[ABS[#726 - 101.0] GT 0.000001]", "[ABS[#726 - 100.0] GT 0.000001]"),
        "prior output mutation": (
            f"(LOGAPPEND,{A7_PATHS['results']})",
            f"(LOGAPPEND,{A5_PATHS['results']})",
        ),
        "midpoint guard class": ("o<tcpc_external_continuity_guard> call [#783]", "o<tcpc_primary_closure_guard> call [#783]"),
        "outer mapping": ("[800 + [3 * [#<outer_slot> - 1]]]", "[803 + [3 * [#<outer_slot> - 1]]]"),
        "frozen timeout selector": ("#789 = #779", "#789 = 0.0"),
    }
    rejected = 0
    for name, (old, new) in mutations.items():
        candidate = replace_once(base, old, new)
        try:
            validate_runner_text(candidate, enforce_hash=False)
        except ValidationError:
            rejected += 1
        else:
            raise ValidationError(f"self-test mutation was accepted: {name}")
    print(f"Attempt-7 independent validator self-test: PASS ({rejected}/{len(mutations)} mutations rejected)")
    return rejected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true", help="validate frozen sources, runner, and fresh outputs")
    parser.add_argument("--reachability", action="store_true", help="also replay the bounded B0 entry and seq24..101 geometry")
    parser.add_argument("--self-test", action="store_true", help="run semantic adversarial mutations")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (args.static or args.reachability or args.self_test):
        args.static = True
        args.reachability = True
    try:
        runner_text = read_ascii(RUNNER)
        validate_a4_sources()
        validate_a5_zero_row_sources()
        validate_a6_sources()
        validate_quiet_reference_model()
        validate_runner_text(runner_text, enforce_hash=True)
        validate_fresh_outputs()
        reachability = validate_reachability() if args.reachability else None
        rejected = self_test(runner_text) if args.self_test else None
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Attempt-7 independent validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print("Attempt-7 independent validation: PASS")
    print(f"runner SHA-256: {sha256(RUNNER)}")
    print(f"A4 immutable results SHA-256: {sha256(A4_PATHS['results'])}")
    print(f"A7 contract: rows={EXPECTED_ROWS}, closures={EXPECTED_CLOSURES}, contact/gap={EXPECTED_TRACES}/{EXPECTED_TRACES}")
    print(f"composite contract: rows={EXPECTED_COMPOSITE_ROWS}, closures={EXPECTED_COMPOSITE_CLOSURES}, contact/gap={EXPECTED_COMPOSITE_TRACES}/{EXPECTED_COMPOSITE_TRACES}")
    if reachability is not None:
        print("reachability: " + ", ".join(f"{key}={value}" for key, value in reachability.items()))
    if rejected is not None:
        print(f"adversarial mutations rejected: {rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
