#!/usr/bin/env python3
"""Offline validation for the campaign-2026082701 T4 Attempt-5 continuation.

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
    "tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.ngc"
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

CAMPAIGN = 2026082701
MODE = 39
ATTEMPT = 5
MODEL_ID = 2026082601
EXPECTED_ROWS = 92
EXPECTED_TRACES = 736
EXPECTED_CLOSURES = 27
EXPECTED_COMPOSITE_ROWS = 101
EXPECTED_COMPOSITE_TRACES = 808
EXPECTED_COMPOSITE_CLOSURES = 28

RUNNER_SHA256 = "372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1"
ATTEMPT1_RUNNER_SHA256 = (
    "54bd1e3b5cfc95f44ddbf344693652b68dec920f74649e466d939860fe4a9174"
)
ATTEMPT4_RUNNER_SHA256 = (
    "66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b"
)

A4_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery"
A5_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt5-recovery"
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
A4_SHA256 = {
    "results": "835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1",
    "state": "99f96ba6e418a514cb07ecba4bd81fec6c18d3f0fbef39c46fcf01d5d8d84235",
    "model-state": "e28f0f7aab6aca30484381590a6f53284f7f8daa43622e35694d415cd68b7cbc",
    "closures": "26919899661bdf78deddbef9983906814f307d25682370eb5d03c47504090bb4",
    "contact-trace": "cc097ab53887f6356531681d7ab2bd70021185e0f44e38b8afd46f53b6abe21b",
    "gap-trace": "3f3e72c8738d2fc57efad3bba0617ed5791b88c2e586d07cd0ff092d496671e7",
}

BASE_HAL = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
MODEL_HAL = HERE / "tcpc_length_aware_candidate_2026082601.hal"
VALIDATION_INI = (
    HERE
    / "5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini"
)
REACH_MODULE = HERE / "analyze_tcpc_relocated_sphere_reachability.py"
REACH_PREREQUISITE_SHA256 = {
    BASE_HAL: "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778",
    MODEL_HAL: "8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14",
    VALIDATION_INI: "24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a",
    REACH_MODULE: "e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607",
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
RESUME_START = (2500.972727063, 696.550278557, -279.730797759)
RESUME_TOLERANCE = 0.050
TOP_CLEAR_RADIUS = 22.845258


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


def validate_fresh_outputs() -> None:
    inode_keys: set[tuple[int, int]] = set()
    for kind, path in A5_PATHS.items():
        require(path.exists(), f"missing Attempt-5 output: {path}")
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), f"Attempt-5 output is not a regular file: {path}")
        require(not path.is_symlink(), f"Attempt-5 output is a symlink: {path}")
        inode_key = (info.st_dev, info.st_ino)
        require(inode_key not in inode_keys, f"Attempt-5 outputs share an inode: {path}")
        inode_keys.add(inode_key)
        a4_header, _ = csv_rows(A4_PATHS[kind])
        a5_header, a5_rows = csv_rows(path)
        require(a5_header == a4_header, f"Attempt-5 {kind} header differs from established schema")
        require(not a5_rows, f"Attempt-5 {kind} is not header-only before execution")


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
    require(sha256(ATTEMPT4_RUNNER) == ATTEMPT4_RUNNER_SHA256, "Attempt-4 motion source hash changed")
    attempt4 = read_ascii(ATTEMPT4_RUNNER)
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
        source = extract_oword(attempt4, name, "sub", "endsub")
        source = source.replace(A4_PREFIX, A5_PREFIX)
        candidate = extract_oword(text, name, "sub", "endsub")
        require(candidate == source, f"motion/probe subroutine o<{name}> differs from frozen Attempt 4")


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
    require("o<tcpc_primary_b0_sweep> call [100.0]" not in body, "Attempt-5 remeasures the opening B0 sweep")
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
    # sweep closures are same-run.  Eleven references cross A4/A5 ownership.
    internal_closures = 6 + 8 + 2
    external_closures = 1 + 9 + 1
    require(internal_closures + external_closures == EXPECTED_CLOSURES, "closure derivation is not 27")
    outer = extract_oword(text, "tcpc_primary_outer_reference", "sub", "endsub")
    require("#<outer_base> = [800 + [3 * [#<outer_slot> - 1]]]" in outer, "outer A4 reference mapping changed")
    require_count(outer, "o<tcpc_external_continuity_guard> call", 1, "dynamic A4 outer continuity call")
    require_count(outer, "o<tcpc_primary_closure_guard> call [#790] [#791] [#792] [906.0] [72.0] [#726]", 1, "same-A5 midpoint-to-close closure")
    require_count(body, "o<tcpc_external_continuity_guard> call [#783] [#784] [#785] [905.0] [9.0] [#726]", 1, "A4 row9 to A5 midpoint continuity")
    require_count(body, "o<tcpc_external_continuity_guard> call [#780] [#781] [#782] [900.0] [1.0] [#726]", 1, "A4 row1 to A5 final continuity")
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


def validate_resume_start(text: str) -> None:
    for parameter, value in zip((774, 775, 776), RESUME_START, strict=True):
        require_assignment(text, parameter, f"{value:.9f}")
    require_assignment(text, 778, f"{RESUME_TOLERANCE:.3f}")
    for source, frozen in ((774, 827), (775, 828), (776, 829), (778, 830)):
        require_count(text, f"#{frozen} = #{source}", 1, f"resume constant #{source} frozen copy")
    selector = extract_oword(text, "tcpc_pair_selector_guard", "sub", "endsub")
    require("ABS[#774 - #827]" in selector and "ABS[#778 - #830]" in selector, "resume constants are not covered by selector guard")
    for axis, parameter in zip("xyz", (774, 775, 776), strict=True):
        require_count(text, f"o<resume_start_{axis}_required> if [ABS[#<_abs_{axis}> - #{parameter}] GT #778]", 1, f"frozen resume {axis.upper()} guard")
    lines = executable_lines(text)
    hold_indices = [index for index, line in enumerate(lines) if line == "M0"]
    require(len(hold_indices) == 1, "runner must have exactly one M0")
    hold_index = hold_indices[0]
    for axis in "xyz":
        guard = f"o<resume_start_{axis}_required> if"
        require(any(line.startswith(guard) for line in lines[:hold_index]), f"resume {axis.upper()} guard is not before M0")
    require(lines[hold_index + 1] == "o<tcpc_pair_hold_position_guard> call", "0.001 hold-position guard is not first after M0")
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


def validate_output_paths(text: str) -> None:
    log_paths = re.findall(r"^\s*\(LOGAPPEND,([^\r\n)]+)\)\s*$", text, re.MULTILINE)
    expected = {str(path) for path in A5_PATHS.values()}
    require(set(log_paths) == expected, f"LOGAPPEND path set is not the six Attempt-5 outputs: {set(log_paths)}")
    require(len(log_paths) == 7, f"LOGAPPEND site count is {len(log_paths)}, expected 7 (two closure guards)")
    require(all(A5_PREFIX in path for path in log_paths), "a LOGAPPEND can mutate an older attempt")
    require(not any(A4_PREFIX in path for path in log_paths), "runner contains an Attempt-4 mutation path")


def validate_runner_text(text: str, *, enforce_hash: bool) -> None:
    require("\x00" not in text, "runner contains NUL")
    validate_oword_balance(text)
    if enforce_hash:
        require(RUNNER_SHA256 != "FROZEN_HASH_PENDING", "validator has not been frozen to a runner hash")
        require(text_sha256(text) == RUNNER_SHA256, "Attempt-5 runner hash changed")

    require_assignment(text, 711, "39.0")
    require_assignment(text, 715, "2026082701.0")
    require_assignment(text, 727, "5.0")
    require_assignment(text, 707, "92.0")
    require_assignment(text, 717, "0.154742")
    require_count(text, "#3032 = #717", 1, "frozen #3032 install")
    require_count(text, "[ABS[#711 - 39.0] GT 0.000001]", 1, "mode-39 hard guard")
    require_count(text, "[ABS[#711 - 39.0] LT 0.1]", 1, "single mode-39 body predicate")
    require_count(text, "#730 = #711", 1, "frozen mode selector")
    require_count(text, "#734 = #727", 1, "frozen attempt selector")
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

    validate_resume_start(text)
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
    frozen_start = np.asarray(RESUME_START, dtype=float)
    pins = a3.merged_model_pins()
    limits = reach.parse_limits(VALIDATION_INI)
    poses = reach.grid()
    require(len(poses) == 101, "reachability source grid is not 101 poses")
    require([pose.slot for pose in poses[9:]] == list(range(10, 102)), "reachability tail is not seq10..101")

    # Slot 9 supplies only the physical prior top-clear state.  Discard its
    # synthetic contact path and retain the actual initial lift into slot 10.
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

    worst_handoff = 0.0
    for signs in itertools.product((-1.0, 1.0), repeat=3):
        corner = frozen_start + RESUME_TOLERANCE * np.asarray(signs)
        worst_handoff = max(worst_handoff, float(np.linalg.norm(corner - computed_clear)))
        for point in reach.linear_points(corner, computed_clear, maximum_step=0.01):
            reach.append_sample(samples, 4, 229.407000, poses[8], "resume_handoff", point, pins, limits, 0.0, 0.0)

    require(worst_handoff < 0.200, f"bounded resume reposition is unexpectedly large: {worst_handoff:.6f} mm")
    require(5.0 - worst_handoff > 4.8, "bounded resume reposition consumes the reviewed top clearance")
    margins = [
        *(float(sample.joint_margins[index]) for index in range(3) for sample in samples),
        *(float(sample.axis_margins[index]) for index in range(3) for sample in samples),
    ]
    minimum_nominal = min(margins)
    # Existing 2 mm center plus 3 mm path/model reserve, with the 0.050 mm
    # absolute handoff envelope charged again as an explicit conservative term.
    remaining = minimum_nominal - 5.050
    require(remaining >= 10.0, f"reachability has only {remaining:.6f} mm after reserve")
    require(len(samples) == 28391, f"reachability sample topology changed: {len(samples)} != 28391")
    return {
        "poses": EXPECTED_ROWS,
        "samples": len(samples),
        "worst_handoff_mm": worst_handoff,
        "minimum_nominal_margin_mm": minimum_nominal,
        "remaining_margin_mm": remaining,
    }


def replace_once(text: str, old: str, new: str) -> str:
    require(text.count(old) == 1, f"self-test target is not unique: {old}")
    return text.replace(old, new, 1)


def self_test(base: str) -> int:
    mutations = {
        "mode assignment": ("#711 = 39.0", "#711 = 38.0"),
        "attempt assignment": ("#727 = 5.0", "#727 = 6.0"),
        "row contract": ("#707 = 92.0", "#707 = 91.0"),
        "resume tolerance": ("#778 = 0.050", "#778 = 0.500"),
        "resume X": ("#774 = 2500.972727063", "#774 = 2501.972727063"),
        "seed X": ("#701 = 2500.940456", "#701 = 2501.940456"),
        "outer row 4 X": ("#809 = 2501.122339", "#809 = 2502.122339"),
        "same-run tolerance": ("GT 0.050", "GT 0.100"),
        "external tolerance": ("GT 0.100", "GT 0.200"),
        "same-run abort": ("T4 primary same-pose closure exceeds 0.050 mm", "T4 primary closure warning only"),
        "external abort": ("T4 cross-attempt continuity exceeds 0.100 mm", "T4 external warning only"),
        "dwell removed": (
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n  G4 P10.0",
            "G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n  G4 P9.0",
        ),
        "ignore guard removed": ("#<_hal[tcpc_probe_gate_ignore.out]>", "#<_hal[tcpc_probe_gate_ignore.width]>"),
        "first low block": ("call [5.0] [5.0]", "call [10.0] [5.0]"),
        "negative low block": ("call [-15.0] [-15.0]", "call [15.0] [-15.0]"),
        "high block": ("call [-90.0] [-90.0]", "call [-60.0] [-90.0]"),
        "opening remeasure": ("o<tcpc_primary_b0_sweep> call [200.0]", "o<tcpc_primary_b0_sweep> call [100.0]"),
        "closure count guard": ("[ABS[#978 - 27.0] GT 0.000001]", "[ABS[#978 - 28.0] GT 0.000001]"),
        "trace count guard": ("[ABS[#973 - 736.0] GT 0.000001]", "[ABS[#973 - 735.0] GT 0.000001]"),
        "terminal sequence": ("[ABS[#726 - 101.0] GT 0.000001]", "[ABS[#726 - 100.0] GT 0.000001]"),
        "A4 output mutation": (
            f"(LOGAPPEND,{A5_PATHS['results']})",
            f"(LOGAPPEND,{A4_PATHS['results']})",
        ),
        "midpoint guard class": ("o<tcpc_external_continuity_guard> call [#783]", "o<tcpc_primary_closure_guard> call [#783]"),
        "outer mapping": ("[800 + [3 * [#<outer_slot> - 1]]]", "[803 + [3 * [#<outer_slot> - 1]]]"),
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
    print(f"Attempt-5 independent validator self-test: PASS ({rejected}/{len(mutations)} mutations rejected)")
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
        validate_runner_text(runner_text, enforce_hash=True)
        validate_fresh_outputs()
        reachability = validate_reachability() if args.reachability else None
        rejected = self_test(runner_text) if args.self_test else None
    except (OSError, ValueError, ValidationError) as exc:
        print(f"Attempt-5 independent validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print("Attempt-5 independent validation: PASS")
    print(f"runner SHA-256: {sha256(RUNNER)}")
    print(f"A4 immutable results SHA-256: {sha256(A4_PATHS['results'])}")
    print(f"A5 contract: rows={EXPECTED_ROWS}, closures={EXPECTED_CLOSURES}, contact/gap={EXPECTED_TRACES}/{EXPECTED_TRACES}")
    print(f"composite contract: rows={EXPECTED_COMPOSITE_ROWS}, closures={EXPECTED_COMPOSITE_CLOSURES}, contact/gap={EXPECTED_COMPOSITE_TRACES}/{EXPECTED_COMPOSITE_TRACES}")
    if reachability is not None:
        print("reachability: " + ", ".join(f"{key}={value}" for key, value in reachability.items()))
    if rejected is not None:
        print(f"adversarial mutations rejected: {rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
