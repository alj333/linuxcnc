#!/usr/bin/env python3
"""Read-only validator for T4 new-location Attempt-4 recovery.

The validator reads ordinary files only. It does not import LinuxCNC, HAL, or
subprocess, does not launch rs274, and never writes a file. Attempt 3 is a
retired identity and is never a composite source: Attempt 1 owns rows 1..17,
Attempt 2 owns rows 18..20, and Attempt 4 owns rows 21..101. The A4-only final
guard must reject an active post-contact ignore window immediately after M66.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
import stat
import sys
from typing import Callable, Mapping, Sequence

import numpy as np

import validate_tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery as a3


common = a3.prior
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CAMPAIGN = 2026082701
MODE = 38
ATTEMPT = 4
TOOL = 4
TOOL_LENGTH_MM = common.TOOL_LENGTH_MM
CLOSURE_LIMIT_MM = common.CLOSURE_LIMIT_MM
MAX_EXTRA_EDGES = 8

PROGRAM = (
    REPO_ROOT / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt4_recovery.ngc"
)
BASE = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery"
FILES = {suffix: Path(f"{BASE}-{suffix}.csv") for suffix in common.SUFFIXES}

PROGRAM_SHA256 = "66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b"
PRIOR_VALIDATOR_SHA256 = "7bb80f4aa04af2b0bbfaabc49a274a0c8fbe6d52a294a28e00f1172aac422413"
HEADER_HASHES = {
    "results": "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    "state": "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    "model-state": "340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd",
    "closures": "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    "contact-trace": "df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8",
    "gap-trace": "e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2",
}

ATTEMPT4_SEQS = tuple(range(1, 10)) + (17,) + tuple(range(20, 102))
CANONICAL_SEQS = tuple(range(1, 102))
ATTEMPT4_EXPECTED = tuple(common.EXPECTED_BY_SEQ[seq] for seq in ATTEMPT4_SEQS)

ATTEMPT4_SPEC = common.campaign.RunSpec(
    "T4 new-location Attempt 4 recovery", TOOL, MODE, TOOL_LENGTH_MM,
    common.PROBE_OFFSET_MM, common.EFFECTIVE_RADIUS_MM,
    FILES["results"], FILES["state"], FILES["closures"],
    ATTEMPT4_EXPECTED, (),
)

# block, source-local open, close, external source, external open sequence.
ATTEMPT4_CLOSURE_TOPOLOGY = (
    (100, 1, 9, None, None),
    (3709, 9, 9, "a1", 9),
    (3717, 17, 17, "a1", 17),
    (3720, 20, 20, "a2", 20),
    (-5, 17, 23, None, None),
    (10, 24, 30, None, None), (-10, 31, 37, None, None),
    (15, 38, 44, None, None), (-15, 45, 51, None, None),
    (30, 52, 56, None, None), (-30, 57, 61, None, None),
    (45, 62, 66, None, None), (-45, 67, 71, None, None),
    (905, 9, 72, None, None),
    (60, 73, 77, None, None), (-60, 78, 82, None, None),
    (90, 83, 87, None, None), (-90, 88, 92, None, None),
    (911, 1, 93, None, None), (906, 72, 93, None, None),
    (912, 2, 94, None, None), (913, 3, 95, None, None),
    (914, 4, 96, None, None), (915, 5, 97, None, None),
    (916, 6, 98, None, None), (917, 7, 99, None, None),
    (918, 8, 100, None, None), (919, 9, 101, None, None),
    (200, 93, 101, None, None), (900, 1, 101, None, None),
)

CRITICAL_SUBROUTINES = (
    "tcpc_pair_coordinate_guard", "tcpc_pair_hold_position_guard",
    "tcpc_pair_selector_guard", "tcpc_length_model_guard",
    "tcpc_pair_live_guard", "tcpc_pair_release_guard",
    "tcpc_probe_counter_guard", "tcpc_contact_gap_log",
    "tcpc_contact_trace_begin", "tcpc_contact_trace_post",
    "tcpc_contact_trace_finish", "tcpc_pair_probe_final_guard",
    "tcpc_pair_probe_ready_guard", "tcpc_vector_sphere_pass4",
    "tcpc_measure_pose", "tcpc_primary_closure_guard",
    "tcpc_primary_outer_reference", "tcpc_primary_b0_sweep",
    "tcpc_primary_low_tilt_block", "tcpc_primary_tilt_block",
    "tcpc_baseline_return_top_clear",
)

FINAL_IGNORE_GUARD = (
    "  o<pair_final_ignore_active> if [#<_hal[tcpc_probe_gate_ignore.out]> GT 0.5]\n"
    "    (abort, Paired probe post-contact ignore is still active immediately before G38)\n"
    "  o<pair_final_ignore_active> endif"
)

BODY_OPENER = "o<run_relocated_t4_recovery> if [ABS[#711 - 38.0] LT 0.1]"
BRIDGE_CALLS = (
    "o<tcpc_primary_closure_guard> call "
    "[2501.004768] [696.551145] [-302.567719] [3709.0] [9.0] [#726]",
    "o<tcpc_primary_closure_guard> call "
    "[2501.211649] [696.532630] [-302.571603] [3717.0] [17.0] [#726]",
    "o<tcpc_primary_closure_guard> call "
    "[2500.997060] [696.609459] [-302.544243] [3720.0] [20.0] [#726]",
)
COMPLETION_GUARD_BLOCKS = (
    (
        "o<primary_sequence_complete> if [[ABS[#726 - 101.0] GT 0.000001] "
        "OR [ABS[#788 - #707] GT 0.000001]]",
        "(abort, Length-aware T4 recovery did not log exact canonical IDs and 92 rows)",
        "o<primary_sequence_complete> endif",
    ),
    (
        "o<model_state_sequence_complete> if [ABS[#977 - #707] GT 0.000001]",
        "(abort, Length-aware T4 recovery did not log exactly 92 model-state rows)",
        "o<model_state_sequence_complete> endif",
    ),
    (
        "o<closure_sequence_complete> if [ABS[#978 - 30.0] GT 0.000001]",
        "(abort, Length-aware T4 recovery did not log exactly 30 closures)",
        "o<closure_sequence_complete> endif",
    ),
    (
        "o<trace_pair_count> if [ABS[#973 - #974] GT 0.000001]",
        "(abort, Length-aware T4 recovery contact and gap trace row counts differ)",
        "o<trace_pair_count> endif",
    ),
    (
        "o<trace_exact_count> if [ABS[#973 - 736.0] GT 0.000001]",
        "(abort, Length-aware T4 recovery trace count is not the exact 736 contract)",
        "o<trace_exact_count> endif",
    ),
)
COMPLETION_GUARDS = tuple(block[0] for block in COMPLETION_GUARD_BLOCKS)

FROZEN_ASSIGNMENTS = (
    ("#707", "92.0"), ("#711", "38.0"), ("#715", "2026082701.0"),
    ("#716", "2.0"), ("#727", "4.0"), ("#739", "1.0"),
    ("#779", "8.0"), ("#789", "#779"), ("#516", "229.407000"),
    ("#717", "0.154742"), ("#3032", "#717"),
)
EXECUTABLE_REQUIREMENTS = (
    *(f"{name} = {value}" for name, value in FROZEN_ASSIGNMENTS),
    "o<high_b_mode_required> if [ABS[#711 - 38.0] GT 0.000001]",
    BODY_OPENER,
    *COMPLETION_GUARDS,
)

ValidationError = common.ValidationError


@dataclass(frozen=True)
class Metrics:
    raw_rms: float
    raw_max: float
    unique_rms: float
    unique_max: float
    transfer_pass: bool
    worst_attempt4_closure: float
    worst_canonical_closure: float
    bridge_row9: float
    bridge_row17: float
    bridge_row20: float
    attempt4_filtered_extras: int


def replacement(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise AssertionError(f"self-test replacement is not unique: {old!r}")
    return text.replace(old, new, 1)


def executable_code_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("(") or stripped.startswith(";"):
            continue
        code = re.sub(r"\([^)]*\)", "", stripped).split(";", 1)[0].strip()
        if code:
            lines.append(code)
    return lines


def sequence_count(lines: Sequence[str], sequence: Sequence[str]) -> int:
    width = len(sequence)
    return sum(
        tuple(lines[index:index + width]) == tuple(sequence)
        for index in range(len(lines) - width + 1)
    )


def output_identity(path: Path) -> tuple[int, int, int]:
    if path.is_symlink():
        raise ValidationError(f"output must not be a symlink: {path}")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValidationError(f"output is not an ordinary regular file: {path}")
    return info.st_dev, info.st_ino, info.st_nlink


def validate_identity_snapshot(
    current: Mapping[str, tuple[int, int, int]],
    retired: Mapping[str, tuple[int, int, int]],
) -> None:
    current_ids: set[tuple[int, int]] = set()
    retired_ids = {(value[0], value[1]) for value in retired.values()}
    for label, (device, inode, links) in current.items():
        identity = (device, inode)
        if links != 1:
            raise ValidationError(f"Attempt-4 {label} has link count {links}, expected 1")
        if identity in current_ids:
            raise ValidationError("Attempt-4 outputs alias the same inode")
        if identity in retired_ids:
            raise ValidationError(f"Attempt-4 {label} reuses an Attempt-1/2/3 inode")
        current_ids.add(identity)


def validate_output_isolation(*, fresh: bool) -> None:
    retired_paths = {
        **{f"a1-{key}": value for key, value in common.ATTEMPT1_FILES.items()},
        **{f"a2-{key}": value for key, value in a3.ATTEMPT2_FILES.items()},
        **{f"a3-{key}": value for key, value in a3.FILES.items()},
    }
    retired = {label: output_identity(path) for label, path in retired_paths.items()}
    current = {label: output_identity(path) for label, path in FILES.items()}
    validate_identity_snapshot(current, retired)
    if fresh:
        validate_fresh_outputs()


def validate_fresh_payload(suffix: str, payload: bytes) -> None:
    actual = hashlib.sha256(payload).hexdigest()
    if actual != HEADER_HASHES[suffix]:
        raise ValidationError(
            f"Attempt-4 {suffix} is nonfresh or has a changed header: {actual}"
        )
    try:
        text = payload.decode("ascii")
    except UnicodeError as exc:
        raise ValidationError(f"Attempt-4 {suffix} header is not ASCII") from exc
    if len(text.splitlines()) != 1:
        raise ValidationError(f"Attempt-4 {suffix} is not an exact one-line header")


def validate_fresh_outputs() -> None:
    for suffix, path in FILES.items():
        validate_fresh_payload(suffix, path.read_bytes())
        if common.read_rows(path, common.FIELDS[suffix]):
            raise ValidationError(f"Attempt-4 {suffix} is not header-only")
        prior_header = a3.FILES[suffix].read_text(encoding="ascii").splitlines()[0]
        current_header = path.read_text(encoding="ascii").splitlines()[0]
        if current_header != prior_header:
            raise ValidationError(f"Attempt-4 {suffix} schema differs from Attempt 3")


def normalize_attempt4_subroutine(text: str) -> str:
    text = text.replace(str(BASE), str(a3.BASE))
    text = text.replace("\n  G4 P10.0", "")
    return text.replace("\n" + FINAL_IGNORE_GUARD, "")


def validate_final_ignore_guard(text: str) -> None:
    final_guard = common.extract_subroutine(text, "tcpc_pair_probe_final_guard")
    placement = (
        "  M66 E0 L0\n" + FINAL_IGNORE_GUARD + "\n"
        "  o<pair_final_gate_requests> if "
    )
    if final_guard.count(placement) != 1:
        raise ValidationError(
            "post-contact ignore guard is not immediately after final M66"
        )
    if text.count(FINAL_IGNORE_GUARD) != 1:
        raise ValidationError("post-contact ignore guard must exist exactly once")
    without_final = text.replace(final_guard, "", 1)
    if "o<pair_final_ignore_active>" in without_final:
        raise ValidationError("post-contact ignore guard exists outside final guard")
    start = final_guard.index("  M66 E0 L0")
    end = final_guard.index("  o<pair_final_gate_requests>")
    if any(
        re.match(r"^\s*G4\b", line)
        for line in final_guard[start:end].splitlines()
    ):
        raise ValidationError("post-contact ignore guard must be non-delaying")


def validate_post_contact_dwells(text: str) -> None:
    dwell_lines = [
        line for line in text.splitlines() if re.match(r"^\s*G4\b", line)
    ]
    if dwell_lines != [
        "    G4 P0.05", "    G4 P0.05",
        "  G4 P10.0", "  G4 P10.0", "  G4 P10.0", "  G4 P10.0",
    ]:
        raise ValidationError("Attempt-4 dwell sites/counts changed")
    vector = common.extract_subroutine(text, "tcpc_vector_sphere_pass4")
    if vector.count("\n  G4 P10.0") != 4:
        raise ValidationError("four post-contact dwell sites are required per pass")
    w_retract = (
        "  G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n"
        "  G4 P10.0\n\n"
        "  (Contact 2: start on the sign-aware upper U side and probe inward.)"
    )
    side_retract = (
        "  G1 X#125 Y#126 Z#127\n"
        "  G4 P10.0\n"
        "  G90"
    )
    if vector.count(w_retract) != 1 or vector.count(side_retract) != 3:
        raise ValidationError(
            "each 10-second dwell must immediately follow its successful retract"
        )
    measure = common.extract_subroutine(text, "tcpc_measure_pose")
    passes_per_pose = sum(
        line.startswith("o<tcpc_vector_sphere_pass4> call ")
        for line in executable_code_lines(measure)
    )
    if passes_per_pose != 2 or 4 * passes_per_pose * len(ATTEMPT4_SEQS) != 736:
        raise ValidationError("post-contact dwell runtime count is not exact 736")
    without_vector = text.replace(vector, "", 1)
    if any(
        re.match(r"^\s*G4\s+P10\.0\s*$", line)
        for line in without_vector.splitlines()
    ):
        raise ValidationError("10-second dwell exists outside the contact subroutine")


def validate_program_text(text: str, attempt3_text: str) -> None:
    if max((len(line) for line in text.splitlines()), default=0) > 225:
        raise ValidationError("Attempt-4 runner exceeds the 225-character line limit")
    required_once = (
        "#707 = 92.0", "#711 = 38.0", "#715 = 2026082701.0",
        "#716 = 2.0", "#727 = 4.0", "#739 = 1.0", "#779 = 8.0",
        "#789 = #779", "#516 = 229.407000", "#717 = 0.154742",
        "#3032 = #717",
        "o<high_b_mode_required> if [ABS[#711 - 38.0] GT 0.000001]",
        "(abort, This dedicated recovery runner requires mode #711 equal to 38)",
        "o<pair_final_ignore_active> if [#<_hal[tcpc_probe_gate_ignore.out]> GT 0.5]",
        BODY_OPENER,
        *COMPLETION_GUARDS,
        "Attempt-3 outputs are excluded from this fresh acquisition and composite.",
        "(18. Every successful-contact immediate retract is followed by G4 P10.0:)",
        "(DEBUG, TCPC_LENGTH_AWARE_T4_NEW_LOCATION_ATTEMPT4_RECOVERY_2026082701 complete)",
        "Sphere-to-post direction remains X+ Y- Z+.",
    )
    for snippet in required_once:
        if text.count(snippet) != 1:
            raise ValidationError(f"Attempt-4 runner contract changed for {snippet!r}")
    code_lines = executable_code_lines(text)
    for requirement in EXECUTABLE_REQUIREMENTS:
        if code_lines.count(requirement) != 1:
            raise ValidationError(
                f"Attempt-4 executable contract changed for {requirement!r}"
            )
    for name, value in FROZEN_ASSIGNMENTS:
        assignments = [
            line for line in code_lines
            if re.match(rf"^{re.escape(name)}\s*=", line)
        ]
        if assignments != [f"{name} = {value}"]:
            raise ValidationError(
                f"Attempt-4 assignment contract changed for {name}: {assignments}"
            )

    mode_assignments = re.findall(r"(?m)^\s*#711\s*=\s*([^\s(]+)", text)
    attempt_assignments = re.findall(r"(?m)^\s*#727\s*=\s*([^\s(]+)", text)
    if mode_assignments != ["38.0"] or attempt_assignments != ["4.0"]:
        raise ValidationError("Attempt-4 has reused or ambiguous mode/attempt assignments")
    if re.search(
        r"(?i)(?:attempt3-recovery|#711\s*=\s*37|#727\s*=\s*3|"
        r"#711\s*-\s*37|#711\s+equal\s+to\s+37)",
        text,
    ):
        raise ValidationError("Attempt-4 runner reuses executable Attempt-3 identity")

    top = common.top_level_lines(text)
    if top.count("M0") != 1 or any(line == "M1" for line in top):
        raise ValidationError("Attempt-4 runner must contain one top-level M0 and no M1")
    m0_index = top.index("M0")
    motion = re.compile(
        r"\b(?:G0|G1|G2|G3|G38\.[2345])\b.*\b[XYZBC](?=[-+#\d\[])", re.I
    )
    if any(motion.search(line) for line in top[:m0_index]):
        raise ValidationError("Attempt-4 top-level axis motion exists before M0")
    validate_post_contact_dwells(text)
    validate_final_ignore_guard(text)
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ValidationError("four-contact acquisition must contain four G38.3 sites")
    if len(re.findall(
        r"o<tcpc_pair_probe_final_guard> call \[#520\] \[#521\]\s*\n\s*G38\.3\b",
        text,
    )) != 4:
        raise ValidationError("every G38.3 lacks its immediate final guard")
    common.validate_no_direct_hal_writes(text)

    expected_paths = {str(path) for path in FILES.values()}
    logged_paths = [
        match.group(1)
        for line in text.splitlines()
        if (match := re.fullmatch(r"\(LOGAPPEND,([^\r\n)]+)\)", line.strip()))
    ]
    if len(logged_paths) != 6 or set(logged_paths) != expected_paths:
        raise ValidationError("LOGAPPEND destinations are not the six Attempt-4 files")
    if any(logged_paths.count(path) != 1 or text.count(path) != 2 for path in expected_paths):
        raise ValidationError("an Attempt-4 output path is not isolated to one logging leg")
    retired_paths = (
        set(map(str, common.ATTEMPT1_FILES.values()))
        | set(map(str, a3.ATTEMPT2_FILES.values()))
        | set(map(str, a3.FILES.values()))
    )
    if retired_paths & set(logged_paths):
        raise ValidationError("Attempt-4 runner can append to a retired attempt")

    for name in CRITICAL_SUBROUTINES:
        current = normalize_attempt4_subroutine(common.extract_subroutine(text, name))
        previous = common.extract_subroutine(attempt3_text, name)
        if current != previous:
            raise ValidationError(f"sealed motion/safety subroutine changed: {name}")

    definitions = set(re.findall(r"(?m)^o<([^>]+)> sub\s*$", text))
    calls = set(re.findall(r"(?m)^\s*o<([^>]+)> call(?:\s|$)", text))
    if calls - definitions:
        raise ValidationError(f"unresolved subroutine call(s): {sorted(calls - definitions)}")

    match = re.search(
        rf"(?ms)^{re.escape(BODY_OPENER)}[ \t]*$.*?"
        r"^o<run_relocated_t4_recovery> endif[ \t]*$",
        text,
    )
    if not match:
        raise ValidationError("Attempt-4 recovery body is missing")
    body = match.group(0)
    body_code = executable_code_lines(body)
    body_stripped = [line.strip() for line in body.splitlines() if line.strip()]
    acquisitions = [
        line for line in body_code
        if re.match(
            r"^o<(?:tcpc_primary_b0_sweep|tcpc_measure_pose|"
            r"tcpc_primary_low_tilt_block|tcpc_primary_tilt_block)> call(?:\s|$)",
            line,
        )
    ]
    expected = [
        "o<tcpc_primary_b0_sweep> call [100.0]",
        "o<tcpc_measure_pose> call [-5.0] [0.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [180.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [225.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [270.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-5.0] [0.0] [0.0] [0.0]",
        "o<tcpc_primary_low_tilt_block> call [10.0] [10.0]",
        "o<tcpc_primary_low_tilt_block> call [-10.0] [-10.0]",
        "o<tcpc_primary_low_tilt_block> call [15.0] [15.0]",
        "o<tcpc_primary_low_tilt_block> call [-15.0] [-15.0]",
        "o<tcpc_primary_tilt_block> call [30.0] [30.0]",
        "o<tcpc_primary_tilt_block> call [-30.0] [-30.0]",
        "o<tcpc_primary_tilt_block> call [45.0] [45.0]",
        "o<tcpc_primary_tilt_block> call [-45.0] [-45.0]",
        "o<tcpc_measure_pose> call [0.0] [0.0] [0.0] [0.0]",
        "o<tcpc_primary_tilt_block> call [60.0] [60.0]",
        "o<tcpc_primary_tilt_block> call [-60.0] [-60.0]",
        "o<tcpc_primary_tilt_block> call [90.0] [90.0]",
        "o<tcpc_primary_tilt_block> call [-90.0] [-90.0]",
        "o<tcpc_primary_b0_sweep> call [200.0]",
    ]
    if acquisitions != expected:
        raise ValidationError("Attempt-4 acquisition topology/order changed")
    if body_code.count("#726 = 16.0") != 1 or body_code.count("#726 = 19.0") != 1:
        raise ValidationError("Attempt-4 accepted-boundary sequence jumps changed")
    if any(body_code.count(bridge) != 1 for bridge in BRIDGE_CALLS):
        raise ValidationError("one or more sealed cross-attempt bridges changed")
    ordered_milestones = (
        expected[0], BRIDGE_CALLS[0], expected[1], BRIDGE_CALLS[1],
        expected[2], BRIDGE_CALLS[2], expected[3],
    )
    cursor = -1
    for milestone in ordered_milestones:
        try:
            cursor = body_code.index(milestone, cursor + 1)
        except ValueError:
            raise ValidationError("all three bridges must pass before sequence 21")
    if any(
        sequence_count(body_stripped, block) != 1
        for block in COMPLETION_GUARD_BLOCKS
    ):
        raise ValidationError("Attempt-4 runtime completion guard block changed")
    if body_code.count("#726 = [#726 + 1.0]") != 0:
        raise ValidationError("sequence mutation must remain inside measurement subroutine")


def validate_internal_topology(
    sequences: Sequence[int] = ATTEMPT4_SEQS,
    closures: Sequence[tuple[int, int, int, str | None, int | None]] = ATTEMPT4_CLOSURE_TOPOLOGY,
) -> None:
    expected_sequences = tuple(range(1, 10)) + (17,) + tuple(range(20, 102))
    if tuple(sequences) != expected_sequences or len(sequences) != 92:
        raise ValidationError("internal Attempt-4 sequence topology changed")
    if tuple(closures) != ATTEMPT4_CLOSURE_TOPOLOGY or len(closures) != 30:
        raise ValidationError("internal Attempt-4 closure topology changed")
    if ATTEMPT4_CLOSURE_TOPOLOGY != a3.ATTEMPT3_CLOSURE_TOPOLOGY:
        raise ValidationError("Attempt-4 closure topology differs from the reviewed full recovery")
    if len(common.expected_transaction_keys(sequences)) != 736:
        raise ValidationError("internal Attempt-4 trace topology changed")
    if len(common.CANONICAL_EXPECTED) != 101 or len(common.campaign.T4_CLOSURES) != 28:
        raise ValidationError("imported canonical topology changed")


def validate_static_source() -> None:
    common.require_hash(PROGRAM, PROGRAM_SHA256)
    common.require_hash(Path(a3.__file__), PRIOR_VALIDATOR_SHA256)
    a3.validate_static_source()
    try:
        text = PROGRAM.read_text(encoding="ascii")
        attempt3_text = a3.PROGRAM.read_text(encoding="ascii")
        source = Path(__file__).read_text(encoding="ascii")
    except UnicodeError as exc:
        raise ValidationError("Attempt-4 source, prior runner, or validator is not ASCII") from exc
    validate_program_text(text, attempt3_text)
    common.validate_python_safety(source)
    validate_internal_topology()


def validate_preflight() -> None:
    validate_static_source()
    common.validate_attempt1_partial()
    a3.validate_attempt2_partial()
    validate_output_isolation(fresh=True)


def validate_attempt4_summaries() -> dict[str, list[dict[str, str]]]:
    rows = {
        suffix: common.read_rows(FILES[suffix], common.FIELDS[suffix])
        for suffix in ("results", "state", "model-state")
    }
    if tuple(len(rows[suffix]) for suffix in rows) != (92, 92, 92):
        raise ValidationError("Attempt-4 summary files are not exact 92/92/92 rows")
    for source, field in (
        (rows["results"], "sample_seq"),
        (rows["state"], "sample_seq"),
        (rows["model-state"], "sample_seq"),
    ):
        actual = tuple(
            common.require_identity(row, field, mode=MODE, attempt=ATTEMPT)
            for row in source
        )
        if actual != ATTEMPT4_SEQS:
            raise ValidationError("Attempt-4 summaries are not 1..9,17,20..101")
    with common.campaign_identity():
        for result, state_row, model, expected in zip(
            rows["results"], rows["state"], rows["model-state"], ATTEMPT4_EXPECTED
        ):
            common.campaign.validate_result(ATTEMPT4_SPEC, result, expected, ATTEMPT)
            common.campaign.validate_state(
                ATTEMPT4_SPEC, state_row, result, expected, ATTEMPT
            )
            common.validate_model_row(model, expected, mode=MODE, attempt=ATTEMPT)
    return rows


def validate_attempt4_closures(
    a1_centers: Mapping[int, np.ndarray],
    a2_centers: Mapping[int, np.ndarray],
    a4_centers: Mapping[int, np.ndarray],
) -> tuple[float, dict[int, float]]:
    rows = common.read_rows(FILES["closures"], common.campaign.CLOSURE_FIELDS)
    if len(rows) != 30:
        raise ValidationError(f"Attempt-4 closure count is {len(rows)}, expected 30")
    norms: list[float] = []
    bridges: dict[int, float] = {}
    for row, (block, open_seq, close_seq, source, external_seq) in zip(
        rows, ATTEMPT4_CLOSURE_TOPOLOGY
    ):
        common.require_identity(row, "close_sample_seq", mode=MODE, attempt=ATTEMPT)
        for field, value in (
            ("block_id", block), ("open_sample_seq", open_seq),
            ("close_sample_seq", close_seq), ("pass", 1),
        ):
            if common.exact_int(row, field) != value:
                raise ValidationError(f"Attempt-4 closure {block}: {field} mismatch")
        if source == "a1":
            open_center = a1_centers[int(external_seq)]
        elif source == "a2":
            open_center = a2_centers[int(external_seq)]
        else:
            open_center = a4_centers[open_seq]
        delta = a4_centers[close_seq] - open_center
        logged = np.asarray([common.number(row, f"closure_d{axis}_mm") for axis in "xyz"])
        norm = float(np.linalg.norm(delta))
        if float(np.linalg.norm(delta - logged)) > 3e-6:
            raise ValidationError(f"Attempt-4 closure {block}: vector mismatch")
        if abs(common.number(row, "closure_norm_mm") - norm) > 3e-6:
            raise ValidationError(f"Attempt-4 closure {block}: norm mismatch")
        if abs(common.number(row, "limit_mm") - CLOSURE_LIMIT_MM) > 1e-9:
            raise ValidationError(f"Attempt-4 closure {block}: limit changed")
        if norm > CLOSURE_LIMIT_MM or common.exact_int(row, "pass") != 1:
            raise ValidationError(f"Attempt-4 closure {block}: exceeds 0.050 mm")
        pose = common.EXPECTED_BY_SEQ[close_seq].pose
        if common.angular_error(common.number(row, "abs_b_deg"), pose.b_deg) > 0.01:
            raise ValidationError(f"Attempt-4 closure {block}: B pose mismatch")
        if common.angular_error(common.number(row, "abs_c_deg"), pose.c_deg) > 0.01:
            raise ValidationError(f"Attempt-4 closure {block}: C pose mismatch")
        norms.append(norm)
        if block in (3709, 3717, 3720):
            bridges[block] = norm
    if set(bridges) != {3709, 3717, 3720}:
        raise ValidationError("Attempt-4 three-bridge topology is incomplete")
    return max(norms), bridges


def source_map(
    rows: Sequence[dict[str, str]], expected: Sequence[int], label: str
) -> dict[int, dict[str, str]]:
    mapped = {common.exact_int(row, "sample_seq", positive=True): row for row in rows}
    if tuple(sorted(mapped)) != tuple(expected) or len(mapped) != len(rows):
        raise ValidationError(f"{label} source mapping/uniqueness changed")
    return mapped


def compose_rows(
    a1_rows: Sequence[dict[str, str]],
    a2_rows: Sequence[dict[str, str]],
    a4_rows: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    first = source_map(a1_rows, range(1, 18), "Attempt-1")
    second = source_map(a2_rows, a3.ATTEMPT2_SEQS, "Attempt-2")
    fourth = source_map(a4_rows, ATTEMPT4_SEQS, "Attempt-4")
    composite: list[dict[str, str]] = []
    for seq in CANONICAL_SEQS:
        source = first if seq <= 17 else second if seq <= 20 else fourth
        row = common.normalize_identity(source[seq])
        row["stage_mode"] = str(MODE)
        row["attempt_id"] = str(ATTEMPT)
        composite.append(row)
    if tuple(common.exact_int(row, "sample_seq") for row in composite) != CANONICAL_SEQS:
        raise ValidationError("A1+A2+A4 composite is not exact canonical rows 1..101")
    return composite


def validate_canonical_trace_splice(
    a1_contacts: Sequence[dict[str, str]],
    a1_gaps: Sequence[dict[str, str]],
    a2_contacts: Sequence[dict[str, str]],
    a2_gaps: Sequence[dict[str, str]],
    a4_contacts: Sequence[dict[str, str]],
    a4_gaps: Sequence[dict[str, str]],
) -> None:
    pieces = (
        (a1_contacts[:136], a1_gaps[:136], tuple(range(1, 18)), 35, 1),
        (a2_contacts[80:104], a2_gaps[80:104], (18, 19, 20), 36, 2),
        (a4_contacts[88:], a4_gaps[88:], tuple(range(21, 102)), MODE, ATTEMPT),
    )
    contact_keys: list[tuple[int, int, int, int]] = []
    gap_keys: list[tuple[int, int, int, int]] = []
    for contacts, gaps, sequences, mode, attempt in pieces:
        expected = common.expected_transaction_keys(sequences)
        current_contacts = [
            common.trace_key(row, "global_seq", mode=mode, attempt=attempt)
            for row in contacts
        ]
        current_gaps = [
            common.trace_key(row, "next_global_seq", mode=mode, attempt=attempt)
            for row in gaps
        ]
        if current_contacts != expected or current_gaps != expected:
            raise ValidationError("canonical trace splice source boundary/order changed")
        contact_keys.extend(current_contacts)
        gap_keys.extend(current_gaps)
    canonical = common.expected_transaction_keys(CANONICAL_SEQS)
    if contact_keys != canonical or gap_keys != canonical or len(canonical) != 808:
        raise ValidationError("canonical trace splice does not cover exact 808 transactions")


def canonical_closure_max(centers: Mapping[int, np.ndarray]) -> float:
    norms: list[float] = []
    if len(common.campaign.T4_CLOSURES) != 28:
        raise ValidationError("canonical closure topology is not 28 rows")
    for block, open_seq, close_seq in common.campaign.T4_CLOSURES:
        norm = float(np.linalg.norm(centers[close_seq] - centers[open_seq]))
        if norm > CLOSURE_LIMIT_MM:
            raise ValidationError(
                f"composite closure {block} {open_seq}->{close_seq} "
                f"is {norm:.6f} mm, above 0.050 mm"
            )
        norms.append(norm)
    return max(norms)


def validate_complete() -> Metrics:
    validate_static_source()
    validate_output_isolation(fresh=False)
    a1_results, a1_states, a1_models = common.validate_attempt1_partial()
    a2_rows = a3.validate_attempt2_partial()
    a4_rows = validate_attempt4_summaries()

    a4_contacts = common.read_rows(FILES["contact-trace"], common.CONTACT_TRACE_FIELDS)
    a4_gaps = common.read_rows(FILES["gap-trace"], common.GAP_TRACE_FIELDS)
    extras = common.validate_transaction_chain(
        a4_contacts, a4_gaps, ATTEMPT4_SEQS,
        mode=MODE, attempt=ATTEMPT, max_extra=MAX_EXTRA_EDGES,
    )
    a1_centers = common.centers_from_results(a1_results)
    a2_centers = common.centers_from_results(a2_rows["results"])
    a4_centers = common.centers_from_results(a4_rows["results"])
    worst_a4, bridges = validate_attempt4_closures(a1_centers, a2_centers, a4_centers)

    validate_canonical_trace_splice(
        common.read_rows(common.ATTEMPT1_FILES["contact-trace"], common.CONTACT_TRACE_FIELDS),
        common.read_rows(common.ATTEMPT1_FILES["gap-trace"], common.GAP_TRACE_FIELDS),
        a2_rows["contact-trace"], a2_rows["gap-trace"], a4_contacts, a4_gaps,
    )
    composite_results = compose_rows(a1_results, a2_rows["results"], a4_rows["results"])
    composite_states = compose_rows(a1_states, a2_rows["state"], a4_rows["state"])
    composite_models = compose_rows(a1_models, a2_rows["model-state"], a4_rows["model-state"])

    raw_centers, keys = common.full.result_centers(
        composite_results, CAMPAIGN, MODE, ATTEMPT
    )
    common.full.validate_states(
        composite_states, composite_results, CAMPAIGN, MODE, ATTEMPT
    )
    common.full.validate_model_rows(composite_models, CAMPAIGN, MODE, ATTEMPT)
    for row, expected in zip(composite_models, common.CANONICAL_EXPECTED):
        common.validate_model_row(row, expected, mode=MODE, attempt=ATTEMPT)
    centers = {seq: raw_centers[seq - 1] for seq in CANONICAL_SEQS}
    worst_canonical = canonical_closure_max(centers)
    _, groups = common.full.canonical_groups(keys)
    unique_centers = common.full.collapse(raw_centers, groups)
    raw_metric = common.full.center_metric(raw_centers)
    unique_metric = common.full.center_metric(unique_centers)
    common.full.repeated_pose_scatter(raw_centers, keys)
    common.full.b0_drift(raw_centers, keys)
    return Metrics(
        raw_metric.rms, raw_metric.maximum, unique_metric.rms, unique_metric.maximum,
        unique_metric.rms <= common.RMS_LIMIT_MM
        and unique_metric.maximum <= common.MAX_LIMIT_MM,
        worst_a4, worst_canonical,
        bridges[3709], bridges[3717], bridges[3720], extras,
    )


def expect_failure(label: str, operation: Callable[[], object]) -> None:
    try:
        operation()
    except (
        ValidationError, common.anchor.ValidationError,
        common.full.AnalysisError, ValueError,
    ):
        return
    raise AssertionError(f"self-test mutation was accepted: {label}")


def synthetic_contact(extra: int) -> dict[str, str]:
    row = common.synthetic_contact(extra)
    row.update(stage_mode=str(MODE), attempt_id=str(ATTEMPT))
    return row


def self_test() -> None:
    validate_preflight()
    text = PROGRAM.read_text(encoding="ascii")
    attempt3_text = a3.PROGRAM.read_text(encoding="ascii")
    row20_bridge = "  " + BRIDGE_CALLS[2]
    row21_call = "  o<tcpc_measure_pose> call [-5.0] [225.0] [0.0] [0.0]"
    row20_bridge_late = replacement(text, "\n" + row20_bridge, "")
    row20_bridge_late = replacement(
        row20_bridge_late, row21_call, row21_call + "\n" + row20_bridge
    )
    all_bridges_late = text
    for bridge in BRIDGE_CALLS:
        all_bridges_late = replacement(all_bridges_late, "\n  " + bridge, "")
    final_sweep = "  o<tcpc_primary_b0_sweep> call [200.0]"
    all_bridges_late = replacement(
        all_bridges_late,
        final_sweep,
        final_sweep + "\n" + "\n".join("  " + bridge for bridge in BRIDGE_CALLS),
    )
    mutations = {
        "M0 removal": replacement(text, "\nM0\n", "\n"),
        "pre-M0 motion": replacement(text, "\nM0\n", "\nG1 Z0\nM0\n"),
        "mode identity": replacement(text, "#711 = 38.0", "#711 = 37.0"),
        "attempt identity": replacement(text, "#727 = 4.0", "#727 = 3.0"),
        "body mode predicate": replacement(
            text, BODY_OPENER, BODY_OPENER.replace("38.0", "39.0")
        ),
        "stale mode diagnostic": replacement(text, "equal to 38", "equal to 37"),
        "edge allowance": replacement(text, "#779 = 8.0", "#779 = 9.0"),
        "trace count": replacement(text, "#973 - 736.0", "#973 - 735.0"),
        "closure count": replacement(text, "#978 - 30.0", "#978 - 29.0"),
        "row-20 bridge": replacement(text, "[2500.997060]", "[2500.997061]"),
        "row-20 bridge after row21": row20_bridge_late,
        "all bridges after acquisition": all_bridges_late,
        "primary completion disabled": replacement(
            text, COMPLETION_GUARDS[0], "o<primary_sequence_complete> if [0]"
        ),
        "model completion disabled": replacement(
            text, COMPLETION_GUARDS[1], "o<model_state_sequence_complete> if [0]"
        ),
        "trace pairing disabled": replacement(
            text, COMPLETION_GUARDS[3], "o<trace_pair_count> if [0]"
        ),
        "Attempt-3 path reuse": replacement(
            text,
            f"(LOGAPPEND,{FILES['results']})",
            f"(LOGAPPEND,{a3.FILES['results']})",
        ),
        "commented LOGAPPEND": replacement(
            text,
            f"(LOGAPPEND,{FILES['results']})",
            f"((LOGAPPEND,{FILES['results']}))",
        ),
        "final G38 guard": replacement(
            text,
            "o<tcpc_pair_probe_ready_guard> call [#520] [#521]\n"
            "  o<tcpc_contact_trace_begin> call [1.0]\n"
            "  o<tcpc_pair_probe_final_guard> call [#520] [#521]\n"
            "  G38.3 X#122 Y#123 Z#124",
            "o<tcpc_pair_probe_ready_guard> call [#520] [#521]\n"
            "  o<tcpc_contact_trace_begin> call [1.0]\n"
            "  o<tcpc_pair_live_guard> call [1.0] [#520] [#521]\n"
            "  G38.3 X#122 Y#123 Z#124",
        ),
        "final ignore guard removal": replacement(
            text, "\n" + FINAL_IGNORE_GUARD, ""
        ),
        "final ignore signal substitution": replacement(
            text,
            "#<_hal[tcpc_probe_gate_ignore.out]>",
            "#<_hal[tcpc_probe_fault_pause.out]>",
        ),
        "final ignore guard before M66": replacement(
            text,
            "  M66 E0 L0\n" + FINAL_IGNORE_GUARD,
            FINAL_IGNORE_GUARD + "\n  M66 E0 L0",
        ),
        "direct HAL write": text + "\nsetp headheadkins.length-model.id 7\n",
        "gate dwell changed": replacement(
            text,
            "  o<pair_release_wait> while [[[#<release_elapsed> LT #756] AND "
            "[#<release_clear_count> LT 1.5]] AND [#971 LT 0.5]]\n"
            "    G4 P0.05",
            "  o<pair_release_wait> while [[[#<release_elapsed> LT #756] AND "
            "[#<release_clear_count> LT 1.5]] AND [#971 LT 0.5]]\n"
            "    G4 P20",
        ),
        "post-contact dwell removal": replacement(
            text,
            "  G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n"
            "  G4 P10.0\n\n"
            "  (Contact 2: start on the sign-aware upper U side and probe inward.)",
            "  G1 X#<top_clear_x> Y#<top_clear_y> Z#<top_clear_z>\n\n"
            "  (Contact 2: start on the sign-aware upper U side and probe inward.)",
        ),
        "pre-retract dwell": replacement(
            text,
            "  #127 = [#539 * #535 * #512]\n"
            "  G91\n  F#507\n  G1 X#125 Y#126 Z#127\n  G4 P10.0",
            "  #127 = [#539 * #535 * #512]\n"
            "  G91\n  F#507\n  G4 P10.0\n  G1 X#125 Y#126 Z#127",
        ),
        "transit dwell": replacement(
            text,
            "  G4 P10.0\n  G90\n"
            "  G1 X#<um_clear_x> Y#<um_clear_y> Z#<um_clear_z>\n",
            "  G4 P10.0\n  G90\n"
            "  G1 X#<um_clear_x> Y#<um_clear_y> Z#<um_clear_z>\n"
            "  G4 P10.0\n",
        ),
        "second pass removal": replacement(
            text,
            "      o<tcpc_vector_sphere_pass4> call [2.0] [#626] [#627] "
            "[#628] [1.0] [#<pose_acquisition_try>]\n",
            "",
        ),
        "topology": replacement(
            text,
            "o<tcpc_primary_tilt_block> call [60.0] [60.0]",
            "o<tcpc_primary_tilt_block> call [61.0] [60.0]",
        ),
        "commented acquisition": replacement(
            text, row21_call, "  (" + row21_call.strip() + ")"
        ),
        "commented sequence jump": replacement(
            text, "  #726 = 19.0", "  (#726 = 19.0)"
        ),
    }
    for index, requirement in enumerate(EXECUTABLE_REQUIREMENTS, start=1):
        mutations[f"commented executable requirement {index}"] = replacement(
            text, requirement, f"({requirement})"
        )
    for name, value in FROZEN_ASSIGNMENTS:
        assignment = f"{name} = {value}"
        mutations[f"second assignment for {name}"] = replacement(
            text, assignment, assignment + f"\n{name} = 0.0"
        )
    for block, bridge in enumerate(BRIDGE_CALLS, start=1):
        mutations[f"commented bridge {block}"] = replacement(
            text, "  " + bridge, "  (" + bridge + ")"
        )
    for index, block in enumerate(COMPLETION_GUARD_BLOCKS, start=1):
        mutations[f"neutralized completion abort {index}"] = replacement(
            text, block[1], block[1].replace("(abort,", "(DEBUG,", 1)
        )
    for label, mutated in mutations.items():
        expect_failure(
            label,
            lambda value=mutated: validate_program_text(value, attempt3_text),
        )

    for suffix, path in FILES.items():
        payload = path.read_bytes()
        validate_fresh_payload(suffix, payload)
        expect_failure(
            f"nonfresh {suffix}",
            lambda kind=suffix, value=payload + b"0\n": validate_fresh_payload(kind, value),
        )

    current = {"results": (1, 101, 1), "state": (1, 102, 1)}
    retired = {"a3-results": (1, 99, 1)}
    validate_identity_snapshot(current, retired)
    expect_failure(
        "duplicate Attempt-4 inode",
        lambda: validate_identity_snapshot(
            {"results": (1, 101, 1), "state": (1, 101, 1)}, retired
        ),
    )
    expect_failure(
        "Attempt-3 inode reuse",
        lambda: validate_identity_snapshot({"results": (1, 99, 1)}, retired),
    )
    expect_failure(
        "hard-linked output",
        lambda: validate_identity_snapshot({"results": (1, 101, 2)}, retired),
    )

    common.validate_contact_row(synthetic_contact(8), (1, 1, 1, 1), max_extra=8)
    expect_failure(
        "nine matched contact extras",
        lambda: common.validate_contact_row(
            synthetic_contact(9), (1, 1, 1, 1), max_extra=8
        ),
    )
    mismatched = synthetic_contact(1)
    mismatched["post_mux_count"] = "101"
    expect_failure(
        "raw/mux mismatch",
        lambda: common.validate_contact_row(mismatched, (1, 1, 1, 1), max_extra=8),
    )

    identity = {
        "schema_version": "1", "campaign_id": str(CAMPAIGN),
        "stage_mode": str(MODE), "attempt_id": str(ATTEMPT), "sample_seq": "1",
    }
    common.require_identity(identity, "sample_seq", mode=MODE, attempt=ATTEMPT)
    stale = dict(identity)
    stale.update(stage_mode="37", attempt_id="3")
    expect_failure(
        "Attempt-3 row identity",
        lambda: common.require_identity(stale, "sample_seq", mode=MODE, attempt=ATTEMPT),
    )

    a1_rows = [{"sample_seq": str(seq), "owner": "a1"} for seq in range(1, 18)]
    a2_rows = [{"sample_seq": str(seq), "owner": "a2"} for seq in a3.ATTEMPT2_SEQS]
    a4_rows = [{"sample_seq": str(seq), "owner": "a4"} for seq in ATTEMPT4_SEQS]
    composed = compose_rows(a1_rows, a2_rows, a4_rows)
    boundary = (
        composed[16]["owner"], composed[17]["owner"],
        composed[19]["owner"], composed[20]["owner"],
    )
    if boundary != ("a1", "a2", "a2", "a4"):
        raise AssertionError("A1+A2+A4 ownership boundary changed")
    expect_failure("missing Attempt-4 row101", lambda: compose_rows(a1_rows, a2_rows, a4_rows[:-1]))
    expect_failure(
        "missing Attempt-4 bridge row20",
        lambda: compose_rows(
            a1_rows, a2_rows,
            [row for row in a4_rows if row["sample_seq"] != "20"],
        ),
    )
    expect_failure(
        "short closure topology",
        lambda: validate_internal_topology(ATTEMPT4_SEQS, ATTEMPT4_CLOSURE_TOPOLOGY[:-1]),
    )
    if (
        len(common.expected_transaction_keys(tuple(range(1, 18)))) != 136
        or len(common.expected_transaction_keys((18, 19, 20))) != 24
        or len(common.expected_transaction_keys(tuple(range(21, 102)))) != 648
    ):
        raise AssertionError("canonical transaction splice counts changed")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static", action="store_true", help="source and sealed-evidence audit")
    modes.add_argument("--preflight", action="store_true", help="static audit plus fresh outputs")
    modes.add_argument("--validate", action="store_true", help="validate Attempt 4 and composite")
    modes.add_argument("--self-test", action="store_true", help="preflight plus mutation tests")
    args = parser.parse_args(argv)
    try:
        metrics: Metrics | None = None
        if args.static:
            validate_static_source()
            common.validate_attempt1_partial()
            a3.validate_attempt2_partial()
            label = "STATIC PASS"
        elif args.preflight:
            validate_preflight()
            label = "PREFLIGHT PASS"
        elif args.validate:
            metrics = validate_complete()
            label = "A1+A2+A4 COMPOSITE ACQUISITION VALID"
        else:
            self_test()
            label = "SELF-TEST PASS"
    except (
        AssertionError, OSError, UnicodeError, ValidationError,
        common.anchor.ValidationError, common.bounds.AuditError,
        common.full.AnalysisError, ValueError,
    ) as exc:
        print(f"T4 new-location Attempt-4 validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"T4 new-location Attempt-4 recovery {label}")
    print(f"runner_sha256={PROGRAM_SHA256}")
    print("identity=campaign2026082701/mode38/attempt4")
    print("recovery=rows92 sequences1..9,17,20..101 closures30 traces736")
    print("canonical=A1:1..17+A2:18..20+A4:21..101 closures28 traces808")
    if metrics is not None:
        print(f"transfer={'PASS' if metrics.transfer_pass else 'FAIL'}")
        for field in Metrics.__dataclass_fields__:
            if field == "transfer_pass":
                continue
            value = getattr(metrics, field)
            print(f"{field}={value:.6f}" if isinstance(value, float) else f"{field}={value}")
        for suffix, path in FILES.items():
            print(f"{suffix}_sha256={common.sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
