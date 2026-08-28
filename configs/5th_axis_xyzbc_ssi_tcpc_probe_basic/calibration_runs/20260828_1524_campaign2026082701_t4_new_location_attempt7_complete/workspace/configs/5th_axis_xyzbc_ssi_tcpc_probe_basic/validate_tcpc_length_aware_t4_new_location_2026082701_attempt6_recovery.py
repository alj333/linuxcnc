#!/usr/bin/env python3
"""Offline validation for the campaign-2026082701 T4 Attempt-6 continuation.

This script has no LinuxCNC/HAL control interface.  It validates the frozen
runner, the immutable Attempt-4 handoff evidence, fresh output isolation, the
exact sequence-10..101 topology, closure ownership, and an offline trajectory
replay that includes the bounded resume-start handoff.
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
    "tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery.ngc"
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

CAMPAIGN = 2026082701
MODE = 40
ATTEMPT = 6
MODEL_ID = 2026082601
EXPECTED_ROWS = 92
EXPECTED_TRACES = 736
EXPECTED_CLOSURES = 27
EXPECTED_COMPOSITE_ROWS = 101
EXPECTED_COMPOSITE_TRACES = 808
EXPECTED_COMPOSITE_CLOSURES = 28

RUNNER_SHA256 = "2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310"
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
SAVED_A4_PASS_CLEAR = (
    2500.9727270632798,
    696.5502785572226,
    -279.73079775900703,
)
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


def validate_fresh_outputs() -> None:
    prior_inode_keys = {
        (path.lstat().st_dev, path.lstat().st_ino)
        for path in (*A4_PATHS.values(), *A5_PATHS.values())
    }
    inode_keys: set[tuple[int, int]] = set()
    for kind, path in A6_PATHS.items():
        require(path.exists(), f"missing Attempt-6 output: {path}")
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), f"Attempt-6 output is not a regular file: {path}")
        require(not path.is_symlink(), f"Attempt-6 output is a symlink: {path}")
        inode_key = (info.st_dev, info.st_ino)
        require(inode_key not in inode_keys, f"Attempt-6 outputs share an inode: {path}")
        require(inode_key not in prior_inode_keys, f"Attempt-6 output aliases immutable prior evidence: {path}")
        inode_keys.add(inode_key)
        a4_header, _ = csv_rows(A4_PATHS[kind])
        a6_header, a6_rows = csv_rows(path)
        require(a6_header == a4_header, f"Attempt-6 {kind} header differs from established schema")
        require(not a6_rows, f"Attempt-6 {kind} is not header-only before execution")


def validate_probe_geometry(text: str) -> None:
    lines = executable_lines(text)
    dwell = "G4 P10.0"
    dwell_indices = [index for index, line in enumerate(lines) if line == dwell]
    require(len(dwell_indices) == 4, f"post-contact G4 P10.0 site count is {len(dwell_indices)}, expected 4")
    predecessors = [lines[index - 1] for index in dwell_indices]
    require(predecessors.count("G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>") == 1, "top-contact dwell is not immediately after its retract")
    require(predecessors.count("G1 X#125 Y#126 Z#127") == 3, "side-contact dwells are not immediately after all three retracts")

    g38_indices = [index for index, line in enumerate(lines) if line.startswith("G38.")]
    require(len(g38_indices) == 4, f"G38 site count is {len(g38_indices)}, expected 4")
    expected_final_call = "o<tcpc_pair_probe_final_guard> call [#520] [#521]"
    require(all(lines[index - 1] == expected_final_call for index in g38_indices), "a G38 is missing its immediate final guard call")
    require(all(lines[index].startswith("G38.3 ") for index in g38_indices), "probe moves must all use G38.3")

    final_guard = extract_oword(text, "tcpc_pair_probe_final_guard", "sub", "endsub")
    require_count(final_guard, "#<_hal[tcpc_probe_gate_ignore.out]>", 1, "final ignore-active pin assertion")
    require("o<pair_final_ignore_active> if [#<_hal[tcpc_probe_gate_ignore.out]> GT 0.5]" in final_guard, "final pre-G38 ignore-active predicate missing")
    require("(abort, Paired probe post-contact ignore is still active immediately before G38)" in final_guard, "final pre-G38 ignore-active abort missing")
    require("M66 E0 L0" in final_guard, "final pre-G38 guard does not synchronize before sampling")


def validate_motion_subroutines(text: str) -> None:
    require(sha256(ATTEMPT5_RUNNER) == ATTEMPT5_RUNNER_SHA256, "Attempt-5 motion source hash changed")
    attempt5 = read_ascii(ATTEMPT5_RUNNER)
    names = (
        "tcpc_pair_release_guard",
        "tcpc_probe_counter_guard",
        "tcpc_contact_gap_log",
        "tcpc_contact_trace_begin",
        "tcpc_contact_trace_post",
        "tcpc_contact_trace_finish",
        "tcpc_pair_probe_final_guard",
        "tcpc_pair_probe_ready_guard",
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
        source = source.replace(A5_PREFIX, A6_PREFIX)
        candidate = extract_oword(text, name, "sub", "endsub")
        require(candidate == source, f"motion/probe subroutine o<{name}> differs from frozen Attempt 5")


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
    sequence = 10
    for b_deg in (5, -5, 10, -10, 15, -15):
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
    require(sequence == 102 and len(rows) == EXPECTED_ROWS, "internal expected tail is not seq10..101")
    return rows


def validate_topology(text: str) -> None:
    body = extract_oword(text, "run_relocated_t4_recovery", "if", "endif")
    low_calls = re.findall(r"^\s*o<tcpc_primary_low_tilt_block>\s+call\s+\[(-?\d+\.0)\]\s+\[(-?\d+\.0)\]", body, re.MULTILINE)
    tilt_calls = re.findall(r"^\s*o<tcpc_primary_tilt_block>\s+call\s+\[(-?\d+\.0)\]\s+\[(-?\d+\.0)\]", body, re.MULTILINE)
    require(low_calls == [("5.0", "5.0"), ("-5.0", "-5.0"), ("10.0", "10.0"), ("-10.0", "-10.0"), ("15.0", "15.0"), ("-15.0", "-15.0")], f"low-B continuation calls changed: {low_calls}")
    require(tilt_calls == [("30.0", "30.0"), ("-30.0", "-30.0"), ("45.0", "45.0"), ("-45.0", "-45.0"), ("60.0", "60.0"), ("-60.0", "-60.0"), ("90.0", "90.0"), ("-90.0", "-90.0")], f"quadrant continuation calls changed: {tilt_calls}")
    require_count(body, "o<tcpc_primary_b0_sweep> call [200.0]", 1, "closing B0 sweep")
    require("o<tcpc_primary_b0_sweep> call [100.0]" not in body, "Attempt-6 remeasures the opening B0 sweep")
    require_count(body, "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]", 1, "midpoint B0/C0 pose")
    require_assignment(body, 726, "9.0")
    require_assignment(body, 700, "1.0")
    for parameter, value in zip((701, 702, 703), A4_CENTERS[8], strict=True):
        require_assignment(body, parameter, f"{value:.6f}")

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
    require([sequence for sequence, _, _ in rows] == list(range(10, 102)), "tail IDs are not exactly 10..101")
    require(len(rows) * 2 * 4 == EXPECTED_TRACES, "tail trace derivation is not 736")

    # Six low closures, eight quadrant closures, midpoint-to-closing and closing
    # sweep closures are same-run.  Eleven references cross A4/A6 ownership.
    internal_closures = 6 + 8 + 2
    external_closures = 1 + 9 + 1
    require(internal_closures + external_closures == EXPECTED_CLOSURES, "closure derivation is not 27")
    outer = extract_oword(text, "tcpc_primary_outer_reference", "sub", "endsub")
    require("#<outer_base> = [800 + [3 * [#<outer_slot> - 1]]]" in outer, "outer A4 reference mapping changed")
    require_count(outer, "o<tcpc_external_continuity_guard> call", 1, "dynamic A4 outer continuity call")
    require_count(outer, "o<tcpc_primary_closure_guard> call [#790] [#791] [#792] [906.0] [72.0] [#726]", 1, "same-A6 midpoint-to-close closure")
    require_count(body, "o<tcpc_external_continuity_guard> call [#783] [#784] [#785] [905.0] [9.0] [#726]", 1, "A4 row9 to A6 midpoint continuity")
    require_count(body, "o<tcpc_external_continuity_guard> call [#780] [#781] [#782] [900.0] [1.0] [#726]", 1, "A4 row1 to A6 final continuity")
    require_count(body, "o<tcpc_external_continuity_guard> call", 2, "main-body external continuity calls")
    require_count(body, "[ABS[#978 - 27.0] GT 0.000001]", 1, "exact closure completion guard")
    require_count(body, "[ABS[#973 - 736.0] GT 0.000001]", 1, "exact trace completion guard")
    require_count(body, "[ABS[#726 - 101.0] GT 0.000001]", 1, "exact terminal sequence guard")
    require_count(body, "[ABS[#788 - #707] GT 0.000001]", 1, "exact result row guard")
    require_count(body, "[ABS[#977 - #707] GT 0.000001]", 1, "exact model row guard")

    require(9 + EXPECTED_ROWS == EXPECTED_COMPOSITE_ROWS, "composite summary derivation is not 101")
    require(72 + EXPECTED_TRACES == EXPECTED_COMPOSITE_TRACES, "composite trace derivation is not 808")
    require(1 + EXPECTED_CLOSURES == EXPECTED_COMPOSITE_CLOSURES, "composite closure derivation is not 28")


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
    for parameter, value in zip((837, 838, 839), SAVED_A4_PASS_CLEAR, strict=True):
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
    for parameter in (837, 838, 839, 840, 841, 842):
        require(f"#{parameter}" not in body, f"saved pass-clear parameter #{parameter} is used as motion/center state")
    require("center-derived row-9" in text, "operator header does not identify the center-derived first clear")
    require("no separate saved-clear waypoint" in text, "operator header does not exclude a saved pass-clear waypoint")

    executable = executable_lines(text)
    for parameter in (837, 838, 839):
        references = sum(
            bool(re.search(rf"#{parameter}(?!\d)", line))
            for line in executable
        )
        require(references == 3, f"saved pass-clear #{parameter} has {references} executable references, expected provenance/freeze/guard only")
    for parameter in (840, 841, 842):
        references = sum(
            bool(re.search(rf"#{parameter}(?!\d)", line))
            for line in executable
        )
        require(references == 2, f"frozen saved pass-clear #{parameter} has {references} executable references, expected freeze/guard only")

    body_lines = executable_lines(body)
    seed_matches = [index for index, line in enumerate(body_lines) if line == "#703 = -302.576056"]
    require(len(seed_matches) == 1, "exact A4 row-9 Z center seed is missing or duplicated")
    seed_end = seed_matches[0]
    calls_after_seed = [
        line for line in body_lines[seed_end + 1 :] if re.match(r"^o<[^>]+> call\b", line)
    ]
    require(bool(calls_after_seed), "continuation has no call after the A4 center seed")
    first_call_after_seed = calls_after_seed[0]
    require(
        first_call_after_seed == "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]",
        f"first continuation call is not sequence-10 B+5: {first_call_after_seed}",
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
        ],
        f"unexpected pre-M0 subroutine call path: {pre_hold_calls}",
    )


def validate_output_paths(text: str) -> None:
    log_paths = re.findall(r"^\s*\(LOGAPPEND,([^\r\n)]+)\)\s*$", text, re.MULTILINE)
    expected = {str(path) for path in A6_PATHS.values()}
    require(set(log_paths) == expected, f"LOGAPPEND path set is not the six Attempt-6 outputs: {set(log_paths)}")
    require(len(log_paths) == 7, f"LOGAPPEND site count is {len(log_paths)}, expected 7 (two closure guards)")
    require(all(A6_PREFIX in path for path in log_paths), "a LOGAPPEND can mutate an older attempt")
    require(not any(A4_PREFIX in path for path in log_paths), "runner contains an Attempt-4 mutation path")
    require(not any(A5_PREFIX in path for path in log_paths), "runner contains an Attempt-5 mutation path")


def validate_runner_text(text: str, *, enforce_hash: bool) -> None:
    require("\x00" not in text, "runner contains NUL")
    validate_oword_balance(text)
    if enforce_hash:
        require(RUNNER_SHA256 != "FROZEN_HASH_PENDING", "validator has not been frozen to a runner hash")
        require(text_sha256(text) == RUNNER_SHA256, "Attempt-6 runner hash changed")

    require_assignment(text, 711, "40.0")
    require_assignment(text, 715, "2026082701.0")
    require_assignment(text, 727, "6.0")
    require_assignment(text, 707, "92.0")
    require_assignment(text, 717, "0.154742")
    require_count(text, "#3032 = #717", 1, "frozen #3032 install")
    require_count(text, "[ABS[#711 - 40.0] GT 0.000001]", 1, "mode-40 hard guard")
    require_count(text, "[ABS[#711 - 40.0] LT 0.1]", 1, "single mode-40 body predicate")
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
    require_count(text, "#779 = 8.0", 1, "bounded raw/mux extras contract")
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

    center = np.asarray(A4_CENTERS[8], dtype=float)
    nominal_start = np.asarray(RESUME_ABSOLUTE, dtype=float)
    saved_pass_clear = np.asarray(SAVED_A4_PASS_CLEAR, dtype=float)
    pins = a3.merged_model_pins()
    limits = reach.parse_limits(VALIDATION_INI)
    poses = reach.grid()
    require(len(poses) == 101, "reachability source grid is not 101 poses")
    require([pose.slot for pose in poses[9:]] == list(range(10, 102)), "reachability tail is not seq10..101")

    # Slot 9 supplies only the exact accepted A4 center state. Discard its
    # synthetic contacts while retaining the actual high-Z transition to 10.
    replayed = reach.replay(
        center,
        pins,
        limits,
        tool=4,
        length=229.407000,
        effective_radius=reach.T4_EFFECTIVE_RADIUS,
        poses=poses[8:],
    )
    first = next(
        index
        for index, sample in enumerate(replayed)
        if sample.slot == 10 and sample.kind == "transit_lift"
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
            reach.append_sample(samples, 4, 229.407000, poses[8], "resume_handoff", point, pins, limits, 0.0, 0.0)

    saved_clear_delta = float(np.linalg.norm(saved_pass_clear - computed_clear))
    require(abs(nominal_handoff - 1.5514374333223189) <= 1e-9, f"nominal center-derived handoff changed: {nominal_handoff:.12f} mm")
    require(abs(nominal_sphere_clearance - 3.890402681423918) <= 1e-9, f"nominal sphere clearance changed: {nominal_sphere_clearance:.12f} mm")
    require(abs(minimum_sphere_clearance - 3.837483000426399) <= 1e-9, f"worst coordinate-corner sphere clearance changed: {minimum_sphere_clearance:.12f} mm")
    require(minimum_sphere_clearance > 3.8, "coordinate tolerance corners consume initial sphere clearance")
    require(abs(saved_clear_delta - 0.03322763548071013) <= 1e-12, f"saved-pass versus center-derived clear delta changed: {saved_clear_delta:.12f} mm")
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
        "saved_clear_delta_mm": saved_clear_delta,
        "minimum_nominal_margin_mm": minimum_nominal,
        "remaining_margin_mm": remaining,
    }


def replace_once(text: str, old: str, new: str) -> str:
    require(text.count(old) == 1, f"self-test target is not unique: {old}")
    return text.replace(old, new, 1)


def self_test(base: str) -> int:
    mutations = {
        "mode assignment": ("#711 = 40.0", "#711 = 39.0"),
        "campaign assignment": ("#715 = 2026082701.0", "#715 = 2026082702.0"),
        "attempt assignment": ("#727 = 6.0", "#727 = 5.0"),
        "row contract": ("#707 = 92.0", "#707 = 91.0"),
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
        "saved clear promoted to center": ("#701 = 2500.940456", "#701 = #837"),
        "seed Z": ("#703 = -302.576056", "#703 = -302.476056"),
        "saved clear X provenance": ("#837 = 2500.972727063", "#837 = 2501.972727063"),
        "center-derived clear formula": (
            "#<current_clear_x> = [#701 - #540 - [#<current_w_x> * #513]]",
            "#<current_clear_x> = [#837 - #540 - [#<current_w_x> * #513]]",
        ),
        "high-Z lift": (
            "#<safe_z> = [#<_z> + #515]",
            "#<safe_z> = [#<_z> + #505]",
        ),
        "pre-M0 motion": (
            "#773 = #<_abs_z>\nM0",
            "#773 = #<_abs_z>\nG1 X0\nM0",
        ),
        "pre-M0 motion subroutine": (
            "o<tcpc_resume_start_guard> call\n(MSG, Confirm laser OFF",
            "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]\n(MSG, Confirm laser OFF",
        ),
        "hold tolerance": (
            "o<pair_hold_xyz_unchanged> if [[ABS[#<_abs_x> - #771] GT 0.001] OR [ABS[#<_abs_y> - #772] GT 0.001] OR [ABS[#<_abs_z> - #773] GT 0.001]]",
            "o<pair_hold_xyz_unchanged> if [[ABS[#<_abs_x> - #771] GT 0.010] OR [ABS[#<_abs_y> - #772] GT 0.010] OR [ABS[#<_abs_z> - #773] GT 0.010]]",
        ),
        "post-M0 coordinate recheck": (
            "o<tcpc_pair_selector_guard> call\no<tcpc_resume_start_guard> call\no<tcpc_pair_live_guard> call [1.0] [0.0] [0.0]",
            "o<tcpc_pair_selector_guard> call\n(MSG, coordinate recheck removed)\no<tcpc_pair_live_guard> call [1.0] [0.0] [0.0]",
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
        "dwell removed": (
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n  G4 P10.0",
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n  G4 P9.0",
        ),
        "ignore guard removed": (
            "o<pair_final_ignore_active> if [#<_hal[tcpc_probe_gate_ignore.out]> GT 0.5]",
            "o<pair_final_ignore_active> if [#<_hal[tcpc_probe_gate_ignore.width]> GT 0.5]",
        ),
        "first low block": (
            "o<tcpc_primary_low_tilt_block> call [5.0] [5.0]",
            "o<tcpc_primary_low_tilt_block> call [10.0] [5.0]",
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
        "closure count guard": ("[ABS[#978 - 27.0] GT 0.000001]", "[ABS[#978 - 28.0] GT 0.000001]"),
        "trace count guard": ("[ABS[#973 - 736.0] GT 0.000001]", "[ABS[#973 - 735.0] GT 0.000001]"),
        "terminal sequence": ("[ABS[#726 - 101.0] GT 0.000001]", "[ABS[#726 - 100.0] GT 0.000001]"),
        "prior output mutation": (
            f"(LOGAPPEND,{A6_PATHS['results']})",
            f"(LOGAPPEND,{A5_PATHS['results']})",
        ),
        "midpoint guard class": ("o<tcpc_external_continuity_guard> call [#783]", "o<tcpc_primary_closure_guard> call [#783]"),
        "outer mapping": ("[800 + [3 * [#<outer_slot> - 1]]]", "[803 + [3 * [#<outer_slot> - 1]]]"),
        "saved-clear waypoint claim": (
            "no separate saved-clear waypoint",
            "use a separate saved-clear waypoint",
        ),
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
    print(f"Attempt-6 independent validator self-test: PASS ({rejected}/{len(mutations)} mutations rejected)")
    return rejected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true", help="validate frozen sources, runner, and fresh outputs")
    parser.add_argument("--reachability", action="store_true", help="also replay the bounded resume and seq10..101 geometry")
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
        validate_runner_text(runner_text, enforce_hash=True)
        validate_fresh_outputs()
        reachability = validate_reachability() if args.reachability else None
        rejected = self_test(runner_text) if args.self_test else None
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Attempt-6 independent validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print("Attempt-6 independent validation: PASS")
    print(f"runner SHA-256: {sha256(RUNNER)}")
    print(f"A4 immutable results SHA-256: {sha256(A4_PATHS['results'])}")
    print(f"A6 contract: rows={EXPECTED_ROWS}, closures={EXPECTED_CLOSURES}, contact/gap={EXPECTED_TRACES}/{EXPECTED_TRACES}")
    print(f"composite contract: rows={EXPECTED_COMPOSITE_ROWS}, closures={EXPECTED_COMPOSITE_CLOSURES}, contact/gap={EXPECTED_COMPOSITE_TRACES}/{EXPECTED_COMPOSITE_TRACES}")
    if reachability is not None:
        print("reachability: " + ", ".join(f"{key}={value}" for key, value in reachability.items()))
    if rejected is not None:
        print(f"adversarial mutations rejected: {rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
