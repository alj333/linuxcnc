#!/usr/bin/env python3
"""Read-only validator for T4 new-location Attempt-3 recovery.

The validator reads ordinary files only.  It does not import LinuxCNC, HAL, or
subprocess, does not launch rs274, and never writes a file.  Static, preflight,
validation, and mutation-test modes are therefore safe while LinuxCNC runs.

Canonical ownership is deliberately asymmetric after the two sealed aborts:
Attempt 1 owns rows 1..17, Attempt 2 owns rows 18..20, and Attempt 3 owns rows
21..101.  Duplicate recovery rows are continuity evidence, never replacements.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import re
import sys
from typing import Callable, Sequence

import numpy as np

import validate_tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery as prior


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CAMPAIGN = 2026082701
MODE = 37
ATTEMPT = 3
TOOL = 4
TOOL_LENGTH_MM = prior.TOOL_LENGTH_MM
CLOSURE_LIMIT_MM = prior.CLOSURE_LIMIT_MM
MAX_EXTRA_EDGES = 8

PROGRAM = (
    REPO_ROOT / "nc_files/calibration/"
    "tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery.ngc"
)
ATTEMPT2_PROGRAM = prior.PROGRAM
BASE = HERE / "tcpc-length-aware-t4-new-location-2026082701-attempt3-recovery"
FILES = {suffix: Path(f"{BASE}-{suffix}.csv") for suffix in prior.SUFFIXES}

PROGRAM_SHA256 = "bf76ab273c76a32046e6f2066f6b865ea8e0a448266cff0399186e262c5a061a"
PRIOR_VALIDATOR_SHA256 = "8eb205238aa3507484ce1f17201fdb4f0f2cbe29507157c833af94c70b7c39c5"

ATTEMPT2_PARTIAL_HASHES = {
    "results": "9dcec878f993c81eb053016f6112816cf95686b400b1ae789ec0ff3a77d2a7a0",
    "state": "b6649bd662e9be9c1ffd1b3ad79f6d555b4eabc761c849021e8ba7af6ac85583",
    "model-state": "771dedb2cf29a2716917291ae15f851786783e4a76ffbbbc6a7cddb9ffa0523c",
    "closures": "b6c59a4e7f6f509d36e25b45ad6946d1d37c39c58ec0d2e1e7d06b8060d59a8c",
    "contact-trace": "f132da6b56acba1aaf29add895e09ddda736813be67e40c97376f139d59c98af",
    "gap-trace": "27bbaf30b85fdd5d52129ca49d36cc992804dcc81f3b60abc8eb68258053c2a7",
}

HEADER_HASHES = {
    "results": "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    "state": "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    "model-state": "340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd",
    "closures": "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    "contact-trace": "df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8",
    "gap-trace": "e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2",
}

ARCHIVE_ROOT = HERE / "calibration_runs"
ATTEMPT1_ARCHIVE = (
    ARCHIVE_ROOT
    / "20260827_1754_campaign2026082701_t4_new_location_attempt1_partial_gap_abort_seq18"
)
ATTEMPT2_ARCHIVE = (
    ARCHIVE_ROOT
    / "20260827_1851_campaign2026082701_t4_new_location_attempt2_recovery_partial_quality_abort_seq21"
)
ARCHIVE_HASHES = {
    ATTEMPT1_ARCHIVE: (
        "66d0b18fd9715722d228b31463194f34419bdbc69ae0a4bac79f8ba1581ea168",
        "2cef1968a26d61cf3f14c6a8807541ce3462f92a8927e6a44e643901234ac6f2",
    ),
    ATTEMPT2_ARCHIVE: (
        "671b22d672bac2adc8dfad7efa6e85e7e604075126d6cae08682b212c669d124",
        "466c730dd4732e930f0d97da5ecbae6715374b7855535e62c7d3cf30c8437481",
    ),
}

ATTEMPT2_BASE = prior.RECOVERY_BASE
ATTEMPT2_FILES = prior.RECOVERY_FILES
ATTEMPT2_SEQS = tuple(range(1, 10)) + (17, 18, 19, 20)
ATTEMPT3_SEQS = tuple(range(1, 10)) + (17,) + tuple(range(20, 102))
CANONICAL_SEQS = tuple(range(1, 102))
ATTEMPT3_EXPECTED = tuple(prior.EXPECTED_BY_SEQ[seq] for seq in ATTEMPT3_SEQS)

ATTEMPT3_SPEC = prior.campaign.RunSpec(
    "T4 new-location Attempt 3 recovery", TOOL, MODE, TOOL_LENGTH_MM,
    prior.PROBE_OFFSET_MM, prior.EFFECTIVE_RADIUS_MM,
    FILES["results"], FILES["state"], FILES["closures"],
    ATTEMPT3_EXPECTED, (),
)

# block, source-local open, close, external source and external open sequence.
ATTEMPT3_CLOSURE_TOPOLOGY = (
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

ValidationError = prior.ValidationError


@dataclass(frozen=True)
class Metrics:
    raw_rms: float
    raw_max: float
    unique_rms: float
    unique_max: float
    transfer_pass: bool
    worst_attempt3_closure: float
    worst_canonical_closure: float
    bridge_row9: float
    bridge_row17: float
    bridge_row20: float
    attempt3_filtered_extras: int


def inventory(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or match.group(2) in entries:
            raise ValidationError(f"malformed or duplicate archive inventory line: {line!r}")
        entries[match.group(2)] = match.group(1)
    if not entries:
        raise ValidationError(f"empty archive inventory: {path}")
    return entries


def require_inventory_suffix(entries: dict[str, str], suffix: str, digest: str) -> None:
    matched = [(name, value) for name, value in entries.items() if name.endswith(suffix)]
    if len(matched) != 1 or matched[0][1] != digest:
        raise ValidationError(f"archive does not bind exactly one {suffix} to {digest}")


def validate_archives() -> None:
    for directory, (manifest_hash, sums_hash) in ARCHIVE_HASHES.items():
        prior.require_hash(directory / "MANIFEST.md", manifest_hash)
        prior.require_hash(directory / "SHA256SUMS", sums_hash)
    a1 = inventory(ATTEMPT1_ARCHIVE / "SHA256SUMS")
    a2 = inventory(ATTEMPT2_ARCHIVE / "SHA256SUMS")
    for suffix, digest in prior.ATTEMPT1_PARTIAL_HASHES.items():
        require_inventory_suffix(a1, f"attempt1-{suffix}.csv", digest)
    for suffix, digest in ATTEMPT2_PARTIAL_HASHES.items():
        require_inventory_suffix(a2, f"attempt2-recovery-{suffix}.csv", digest)
    require_inventory_suffix(a1, "attempt1.ngc", prior.ATTEMPT1_PROGRAM_SHA256)
    require_inventory_suffix(a2, "attempt2_recovery.ngc", prior.PROGRAM_SHA256)
    require_inventory_suffix(
        a2,
        "validate_tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.py",
        PRIOR_VALIDATOR_SHA256,
    )


def validate_program_text(text: str) -> None:
    if max((len(line) for line in text.splitlines()), default=0) > 225:
        raise ValidationError("Attempt-3 runner exceeds the 225-character line limit")
    required_once = (
        "#707 = 92.0", "#711 = 37.0", "#715 = 2026082701.0",
        "#716 = 2.0", "#727 = 3.0", "#739 = 1.0", "#779 = 8.0",
        "#789 = #779", "#516 = 229.407000", "#717 = 0.154742",
        "#3032 = #717",
        "o<closure_sequence_complete> if [ABS[#978 - 30.0] GT 0.000001]",
        "o<trace_exact_count> if [ABS[#973 - 736.0] GT 0.000001]",
        "(DEBUG, TCPC_LENGTH_AWARE_T4_NEW_LOCATION_ATTEMPT3_RECOVERY_2026082701 complete)",
        "Sphere-to-post direction remains X+ Y- Z+.",
    )
    for snippet in required_once:
        if text.count(snippet) != 1:
            raise ValidationError(f"Attempt-3 runner contract changed for {snippet!r}")

    top = prior.top_level_lines(text)
    if top.count("M0") != 1 or any(line == "M1" for line in top):
        raise ValidationError("Attempt-3 runner must contain one top-level M0 and no M1")
    m0_index = top.index("M0")
    motion = re.compile(
        r"\b(?:G0|G1|G2|G3|G38\.[2345])\b.*\b[XYZBC](?=[-+#\d\[])", re.I
    )
    if any(motion.search(line) for line in top[:m0_index]):
        raise ValidationError("Attempt-3 top-level axis motion exists before M0")
    if [line for line in text.splitlines() if re.match(r"^\s*G4\b", line)] != [
        "    G4 P0.05", "    G4 P0.05"
    ]:
        raise ValidationError("only the two reviewed 0.05-second gate dwells are allowed")
    if len(re.findall(r"^\s*G38\.3\b", text, re.MULTILINE)) != 4:
        raise ValidationError("four-contact acquisition must contain four G38.3 sites")
    if len(re.findall(
        r"o<tcpc_pair_probe_final_guard> call \[#520\] \[#521\]\s*\n\s*G38\.3\b",
        text,
    )) != 4:
        raise ValidationError("every G38.3 lacks its immediate final guard")
    prior.validate_no_direct_hal_writes(text)

    expected_paths = {str(path) for path in FILES.values()}
    logged_paths = re.findall(r"\(LOGAPPEND,([^\r\n)]+)\)", text)
    if len(logged_paths) != 6 or set(logged_paths) != expected_paths:
        raise ValidationError("LOGAPPEND destinations are not the six Attempt-3 files")
    if any(logged_paths.count(path) != 1 or text.count(path) != 2 for path in expected_paths):
        raise ValidationError("an Attempt-3 output path is not isolated to one logging leg")
    sealed_paths = set(map(str, prior.ATTEMPT1_FILES.values())) | set(map(str, ATTEMPT2_FILES.values()))
    if sealed_paths & set(logged_paths):
        raise ValidationError("Attempt-3 runner can append to a sealed earlier attempt")

    definitions = set(re.findall(r"(?m)^o<([^>]+)> sub\s*$", text))
    calls = set(re.findall(r"(?m)^\s*o<([^>]+)> call(?:\s|$)", text))
    if calls - definitions:
        raise ValidationError(f"unresolved subroutine call(s): {sorted(calls - definitions)}")

    match = re.search(
        r"(?ms)^o<run_relocated_t4_recovery> if .*?^o<run_relocated_t4_recovery> endif$",
        text,
    )
    if not match:
        raise ValidationError("Attempt-3 recovery body is missing")
    body = match.group(0)
    acquisitions = [
        line.strip() for line in body.splitlines()
        if re.search(
            r"o<(?:tcpc_primary_b0_sweep|tcpc_measure_pose|"
            r"tcpc_primary_low_tilt_block|tcpc_primary_tilt_block)> call",
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
        raise ValidationError("Attempt-3 acquisition topology/order changed")
    if body.count("#726 = 16.0") != 1 or body.count("#726 = 19.0") != 1:
        raise ValidationError("Attempt-3 accepted-boundary sequence jumps changed")
    bridges = (
        "o<tcpc_primary_closure_guard> call [2501.004768] [696.551145] [-302.567719] [3709.0] [9.0] [#726]",
        "o<tcpc_primary_closure_guard> call [2501.211649] [696.532630] [-302.571603] [3717.0] [17.0] [#726]",
        "o<tcpc_primary_closure_guard> call [2500.997060] [696.609459] [-302.544243] [3720.0] [20.0] [#726]",
    )
    if any(body.count(bridge) != 1 for bridge in bridges):
        raise ValidationError("one or more sealed cross-attempt bridges changed")
    if body.count("#726 = [#726 + 1.0]") != 0:
        raise ValidationError("sequence mutation must remain inside the measurement subroutine")


def validate_static_source() -> None:
    prior.require_hash(PROGRAM, PROGRAM_SHA256)
    prior.require_hash(Path(prior.__file__), PRIOR_VALIDATOR_SHA256)
    prior.validate_static_source()
    validate_archives()
    try:
        text = PROGRAM.read_text(encoding="ascii")
        source = Path(__file__).read_text(encoding="ascii")
    except UnicodeError as exc:
        raise ValidationError("Attempt-3 runner or validator is not ASCII") from exc
    validate_program_text(text)
    prior.validate_python_safety(source)
    if ATTEMPT3_SEQS != tuple(range(1, 10)) + (17,) + tuple(range(20, 102)):
        raise ValidationError("internal Attempt-3 sequence mapping changed")
    if len(ATTEMPT3_SEQS) != 92 or len(ATTEMPT3_CLOSURE_TOPOLOGY) != 30:
        raise ValidationError("internal Attempt-3 row/closure topology changed")
    if len(prior.expected_transaction_keys(ATTEMPT3_SEQS)) != 736:
        raise ValidationError("internal Attempt-3 transaction topology changed")
    if len(prior.CANONICAL_EXPECTED) != 101 or len(prior.campaign.T4_CLOSURES) != 28:
        raise ValidationError("imported canonical T4 topology changed")


def validate_attempt2_rejected_suffix(
    contacts: Sequence[dict[str, str]], gaps: Sequence[dict[str, str]]
) -> None:
    suffix_contacts = list(contacts[104:])
    suffix_gaps = list(gaps[104:])
    keys = [(21, 1, 1, contact_id) for contact_id in (1, 2, 3, 4)]
    if [prior.trace_key(row, "global_seq", mode=36, attempt=2) for row in suffix_contacts] != keys:
        raise ValidationError("Attempt-2 rejected contact suffix is not seq21/pass1/contact1..4")
    if [prior.trace_key(row, "next_global_seq", mode=36, attempt=2) for row in suffix_gaps] != keys:
        raise ValidationError("Attempt-2 rejected gap suffix is not seq21/pass1/contact1..4")
    expected_travel = (5.005950, 1.903202, 0.609798, 3.820871)
    previous = contacts[103]
    for offset, (contact, gap, key, travel) in enumerate(
        zip(suffix_contacts, suffix_gaps, keys, expected_travel), start=104
    ):
        if abs(prior.number(contact, "travel_mm") - travel) > 5e-7:
            raise ValidationError("Attempt-2 rejected suffix travel chronology changed")
        checked = dict(contact)
        if key[-1] == 3:
            checked["travel_mm"] = "1.0"
        prior.validate_contact_row(checked, key, max_extra=8)
        prior.validate_gap_row(gap, contact, previous, offset, key, max_extra=8)
        previous = contact
    third_contact, third_gap = suffix_contacts[2], suffix_gaps[2]
    if (
        prior.counter_tuple(third_contact, "pre") != (823, 823, 331)
        or prior.counter_tuple(third_contact, "post") != (824, 824, 332)
        or prior.counter_tuple(third_contact, "ready") != (825, 825, 332)
        or prior.exact_int(third_contact, "extra_raw_minus_gated_delta") != 1
        or tuple(prior.exact_int(third_gap, field) for field in
                 ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta", "combined_extra_delta"))
        != (2, 2, 0, 2)
    ):
        raise ValidationError("Attempt-2 short-contact electrical chronology changed")
    for row in suffix_contacts:
        for field in ("burst_flag", "consistency_fault", "release_fault", "terminal_failure"):
            if prior.exact_int(row, field) != 0:
                raise ValidationError("Attempt-2 rejected suffix fault flags changed")


def validate_attempt2_partial() -> dict[str, list[dict[str, str]]]:
    for suffix, digest in ATTEMPT2_PARTIAL_HASHES.items():
        prior.require_hash(ATTEMPT2_FILES[suffix], digest)
    rows = {
        suffix: prior.read_rows(ATTEMPT2_FILES[suffix], prior.FIELDS[suffix])
        for suffix in prior.SUFFIXES
    }
    counts = tuple(len(rows[suffix]) for suffix in prior.SUFFIXES)
    if counts != (13, 13, 13, 3, 108, 108):
        raise ValidationError(f"Attempt-2 sealed partial counts changed: {counts}")
    results, states, models = rows["results"], rows["state"], rows["model-state"]
    expected_rows = tuple(prior.EXPECTED_BY_SEQ[seq] for seq in ATTEMPT2_SEQS)
    with prior.campaign_identity():
        for result, state, model, expected in zip(results, states, models, expected_rows):
            prior.campaign.validate_result(prior.RECOVERY_SPEC, result, expected, 2)
            prior.campaign.validate_state(prior.RECOVERY_SPEC, state, result, expected, 2)
            prior.validate_model_row(model, expected, mode=36, attempt=2)
    for source, field in ((results, "sample_seq"), (states, "sample_seq"), (models, "sample_seq")):
        actual = tuple(prior.require_identity(row, field, mode=36, attempt=2) for row in source)
        if actual != ATTEMPT2_SEQS:
            raise ValidationError("Attempt-2 accepted summaries changed from 1..9,17..20")

    prior.validate_transaction_chain(
        rows["contact-trace"][:104], rows["gap-trace"][:104], ATTEMPT2_SEQS,
        mode=36, attempt=2, max_extra=8,
    )
    validate_attempt2_rejected_suffix(rows["contact-trace"], rows["gap-trace"])
    if any(prior.exact_int(row, "sample_seq") == 21 for row in results):
        raise ValidationError("Attempt-2 rejected seq21 leaked into summary ownership")
    return rows


def validate_headers() -> None:
    for suffix, path in FILES.items():
        prior.require_hash(path, HEADER_HASHES[suffix])
        if prior.read_rows(path, prior.FIELDS[suffix]):
            raise ValidationError(f"Attempt-3 {suffix} is not fresh/header-only")
        a2_header = ATTEMPT2_FILES[suffix].read_text(encoding="ascii").splitlines()[0]
        if path.read_text(encoding="ascii").splitlines()[0] != a2_header:
            raise ValidationError(f"Attempt-3 {suffix} header differs from sealed schema")


def validate_preflight() -> None:
    validate_static_source()
    prior.validate_attempt1_partial()
    validate_attempt2_partial()
    validate_headers()


def validate_attempt3_summaries() -> dict[str, list[dict[str, str]]]:
    rows = {
        suffix: prior.read_rows(FILES[suffix], prior.FIELDS[suffix])
        for suffix in ("results", "state", "model-state")
    }
    if tuple(len(rows[suffix]) for suffix in ("results", "state", "model-state")) != (92, 92, 92):
        raise ValidationError("Attempt-3 summary files are not exact 92/92/92 rows")
    for source, field in (
        (rows["results"], "sample_seq"),
        (rows["state"], "sample_seq"),
        (rows["model-state"], "sample_seq"),
    ):
        actual = tuple(prior.require_identity(row, field, mode=MODE, attempt=ATTEMPT) for row in source)
        if actual != ATTEMPT3_SEQS:
            raise ValidationError("Attempt-3 summaries are not exact sequences 1..9,17,20..101")
    with prior.campaign_identity():
        for result, state, model, expected in zip(
            rows["results"], rows["state"], rows["model-state"], ATTEMPT3_EXPECTED
        ):
            prior.campaign.validate_result(ATTEMPT3_SPEC, result, expected, ATTEMPT)
            prior.campaign.validate_state(ATTEMPT3_SPEC, state, result, expected, ATTEMPT)
            prior.validate_model_row(model, expected, mode=MODE, attempt=ATTEMPT)
    return rows


def validate_attempt3_closures(
    a1_centers: dict[int, np.ndarray], a2_centers: dict[int, np.ndarray],
    a3_centers: dict[int, np.ndarray],
) -> tuple[float, dict[int, float]]:
    rows = prior.read_rows(FILES["closures"], prior.campaign.CLOSURE_FIELDS)
    if len(rows) != 30:
        raise ValidationError(f"Attempt-3 closure count is {len(rows)}, expected 30")
    norms: list[float] = []
    bridges: dict[int, float] = {}
    for row, (block, open_seq, close_seq, source, external_seq) in zip(
        rows, ATTEMPT3_CLOSURE_TOPOLOGY
    ):
        prior.require_identity(row, "close_sample_seq", mode=MODE, attempt=ATTEMPT)
        for field, value in (
            ("block_id", block), ("open_sample_seq", open_seq),
            ("close_sample_seq", close_seq), ("pass", 1),
        ):
            if prior.exact_int(row, field) != value:
                raise ValidationError(f"Attempt-3 closure {block}: {field} mismatch")
        if source == "a1":
            open_center = a1_centers[int(external_seq)]
        elif source == "a2":
            open_center = a2_centers[int(external_seq)]
        else:
            open_center = a3_centers[open_seq]
        delta = a3_centers[close_seq] - open_center
        logged = np.asarray([prior.number(row, f"closure_d{axis}_mm") for axis in "xyz"])
        norm = float(np.linalg.norm(delta))
        if float(np.linalg.norm(delta - logged)) > 3e-6:
            raise ValidationError(f"Attempt-3 closure {block}: vector mismatch")
        if abs(prior.number(row, "closure_norm_mm") - norm) > 3e-6:
            raise ValidationError(f"Attempt-3 closure {block}: norm mismatch")
        if abs(prior.number(row, "limit_mm") - CLOSURE_LIMIT_MM) > 1e-9:
            raise ValidationError(f"Attempt-3 closure {block}: limit changed")
        if norm > CLOSURE_LIMIT_MM or prior.exact_int(row, "pass") != 1:
            raise ValidationError(f"Attempt-3 closure {block}: exceeds 0.050 mm")
        pose = prior.EXPECTED_BY_SEQ[close_seq].pose
        if prior.angular_error(prior.number(row, "abs_b_deg"), pose.b_deg) > 0.01:
            raise ValidationError(f"Attempt-3 closure {block}: B pose mismatch")
        if prior.angular_error(prior.number(row, "abs_c_deg"), pose.c_deg) > 0.01:
            raise ValidationError(f"Attempt-3 closure {block}: C pose mismatch")
        norms.append(norm)
        if block in (3709, 3717, 3720):
            bridges[block] = norm
    if set(bridges) != {3709, 3717, 3720}:
        raise ValidationError("Attempt-3 three-bridge topology is incomplete")
    return max(norms), bridges


def source_map(rows: Sequence[dict[str, str]], expected: Sequence[int], label: str) -> dict[int, dict[str, str]]:
    mapped = {prior.exact_int(row, "sample_seq", positive=True): row for row in rows}
    if tuple(sorted(mapped)) != tuple(expected) or len(mapped) != len(rows):
        raise ValidationError(f"{label} source mapping/uniqueness changed")
    return mapped


def compose_rows(
    a1: Sequence[dict[str, str]], a2: Sequence[dict[str, str]],
    a3: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    first = source_map(a1, range(1, 18), "Attempt-1")
    second = source_map(a2, ATTEMPT2_SEQS, "Attempt-2")
    third = source_map(a3, ATTEMPT3_SEQS, "Attempt-3")
    composite: list[dict[str, str]] = []
    for seq in CANONICAL_SEQS:
        source = first if seq <= 17 else second if seq <= 20 else third
        row = prior.normalize_identity(source[seq])
        row["stage_mode"] = str(MODE)
        row["attempt_id"] = str(ATTEMPT)
        composite.append(row)
    if tuple(prior.exact_int(row, "sample_seq") for row in composite) != CANONICAL_SEQS:
        raise ValidationError("three-source composite is not exact canonical rows 1..101")
    return composite


def validate_canonical_trace_splice(
    a1_contacts: Sequence[dict[str, str]], a1_gaps: Sequence[dict[str, str]],
    a2_contacts: Sequence[dict[str, str]], a2_gaps: Sequence[dict[str, str]],
    a3_contacts: Sequence[dict[str, str]], a3_gaps: Sequence[dict[str, str]],
) -> None:
    pieces = (
        (a1_contacts[:136], a1_gaps[:136], tuple(range(1, 18)), 35, 1),
        (a2_contacts[80:104], a2_gaps[80:104], (18, 19, 20), 36, 2),
        (a3_contacts[88:], a3_gaps[88:], tuple(range(21, 102)), 37, 3),
    )
    contact_keys: list[tuple[int, int, int, int]] = []
    gap_keys: list[tuple[int, int, int, int]] = []
    for contacts, gaps, seqs, mode, attempt in pieces:
        expected = prior.expected_transaction_keys(seqs)
        current_contacts = [prior.trace_key(row, "global_seq", mode=mode, attempt=attempt) for row in contacts]
        current_gaps = [prior.trace_key(row, "next_global_seq", mode=mode, attempt=attempt) for row in gaps]
        if current_contacts != expected or current_gaps != expected:
            raise ValidationError("canonical trace splice source boundary/order changed")
        contact_keys.extend(current_contacts)
        gap_keys.extend(current_gaps)
    canonical = prior.expected_transaction_keys(CANONICAL_SEQS)
    if contact_keys != canonical or gap_keys != canonical or len(canonical) != 808:
        raise ValidationError("canonical trace splice does not cover exact 808 transactions")


def canonical_closure_max(centers: dict[int, np.ndarray]) -> float:
    norms: list[float] = []
    if len(prior.campaign.T4_CLOSURES) != 28:
        raise ValidationError("canonical closure topology is not 28 rows")
    for block, open_seq, close_seq in prior.campaign.T4_CLOSURES:
        norm = float(np.linalg.norm(centers[close_seq] - centers[open_seq]))
        if norm > CLOSURE_LIMIT_MM:
            raise ValidationError(
                f"composite canonical closure {block} {open_seq}->{close_seq} "
                f"is {norm:.6f} mm, above 0.050 mm"
            )
        norms.append(norm)
    return max(norms)


def validate_complete() -> Metrics:
    validate_static_source()
    a1_results, a1_states, a1_models = prior.validate_attempt1_partial()
    a2 = validate_attempt2_partial()
    a3 = validate_attempt3_summaries()

    a3_contacts = prior.read_rows(FILES["contact-trace"], prior.CONTACT_TRACE_FIELDS)
    a3_gaps = prior.read_rows(FILES["gap-trace"], prior.GAP_TRACE_FIELDS)
    extras = prior.validate_transaction_chain(
        a3_contacts, a3_gaps, ATTEMPT3_SEQS,
        mode=MODE, attempt=ATTEMPT, max_extra=MAX_EXTRA_EDGES,
    )
    a1_centers = prior.centers_from_results(a1_results)
    a2_centers = prior.centers_from_results(a2["results"])
    a3_centers = prior.centers_from_results(a3["results"])
    worst_a3, bridges = validate_attempt3_closures(a1_centers, a2_centers, a3_centers)

    validate_canonical_trace_splice(
        prior.read_rows(prior.ATTEMPT1_FILES["contact-trace"], prior.CONTACT_TRACE_FIELDS),
        prior.read_rows(prior.ATTEMPT1_FILES["gap-trace"], prior.GAP_TRACE_FIELDS),
        a2["contact-trace"], a2["gap-trace"], a3_contacts, a3_gaps,
    )
    composite_results = compose_rows(a1_results, a2["results"], a3["results"])
    composite_states = compose_rows(a1_states, a2["state"], a3["state"])
    composite_models = compose_rows(a1_models, a2["model-state"], a3["model-state"])

    raw_centers, keys = prior.full.result_centers(composite_results, CAMPAIGN, MODE, ATTEMPT)
    prior.full.validate_states(composite_states, composite_results, CAMPAIGN, MODE, ATTEMPT)
    prior.full.validate_model_rows(composite_models, CAMPAIGN, MODE, ATTEMPT)
    for row, expected in zip(composite_models, prior.CANONICAL_EXPECTED):
        prior.validate_model_row(row, expected, mode=MODE, attempt=ATTEMPT)
    centers = {seq: raw_centers[seq - 1] for seq in CANONICAL_SEQS}
    worst_canonical = canonical_closure_max(centers)
    _, groups = prior.full.canonical_groups(keys)
    unique_centers = prior.full.collapse(raw_centers, groups)
    raw_metric = prior.full.center_metric(raw_centers)
    unique_metric = prior.full.center_metric(unique_centers)
    prior.full.repeated_pose_scatter(raw_centers, keys)
    prior.full.b0_drift(raw_centers, keys)
    return Metrics(
        raw_metric.rms, raw_metric.maximum, unique_metric.rms, unique_metric.maximum,
        unique_metric.rms <= prior.RMS_LIMIT_MM and unique_metric.maximum <= prior.MAX_LIMIT_MM,
        worst_a3, worst_canonical, bridges[3709], bridges[3717], bridges[3720], extras,
    )


def expect_failure(label: str, operation: Callable[[], object]) -> None:
    try:
        operation()
    except (ValidationError, prior.anchor.ValidationError, prior.full.AnalysisError, ValueError):
        return
    raise AssertionError(f"self-test mutation was accepted: {label}")


def synthetic_contact(extra: int) -> dict[str, str]:
    row = prior.synthetic_contact(extra)
    row.update(stage_mode=str(MODE), attempt_id=str(ATTEMPT))
    return row


def self_test() -> None:
    validate_preflight()
    text = PROGRAM.read_text(encoding="ascii")
    mutations = {
        "M0 removal": text.replace("\nM0\n", "\n", 1),
        "pre-M0 motion": text.replace("\nM0\n", "\nG1 Z0\nM0\n", 1),
        "attempt identity": text.replace("#727 = 3.0", "#727 = 4.0", 1),
        "edge allowance": text.replace("#779 = 8.0", "#779 = 9.0", 1),
        "trace count": text.replace("#973 - 736.0", "#973 - 735.0", 1),
        "closure count": text.replace("#978 - 30.0", "#978 - 29.0", 1),
        "row-20 bridge": text.replace("[2500.997060]", "[2500.997061]", 1),
        "output isolation": text.replace("attempt3-recovery-results.csv", "attempt2-recovery-results.csv", 1),
        "final G38 guard": text.replace(
            "o<tcpc_pair_probe_final_guard> call [#520] [#521]\n  G38.3",
            "o<tcpc_pair_live_guard> call [1.0] [#520] [#521]\n  G38.3", 1,
        ),
        "direct HAL write": text + "\nsetp headheadkins.length-model.id 7\n",
        "long dwell": text.replace("G4 P0.05", "G4 P20", 1),
        "topology": text.replace(
            "o<tcpc_primary_tilt_block> call [60.0] [60.0]",
            "o<tcpc_primary_tilt_block> call [61.0] [60.0]", 1,
        ),
    }
    for label, mutated in mutations.items():
        expect_failure(label, lambda value=mutated: validate_program_text(value))

    prior.validate_contact_row(synthetic_contact(8), (1, 1, 1, 1), max_extra=8)
    expect_failure(
        "nine matched contact extras",
        lambda: prior.validate_contact_row(synthetic_contact(9), (1, 1, 1, 1), max_extra=8),
    )
    mismatched = synthetic_contact(1)
    mismatched["post_mux_count"] = "101"
    expect_failure(
        "raw/mux contact mismatch",
        lambda: prior.validate_contact_row(mismatched, (1, 1, 1, 1), max_extra=8),
    )

    a1 = [{"sample_seq": str(seq), "owner": "a1"} for seq in range(1, 18)]
    a2 = [{"sample_seq": str(seq), "owner": "a2"} for seq in ATTEMPT2_SEQS]
    a3 = [{"sample_seq": str(seq), "owner": "a3"} for seq in ATTEMPT3_SEQS]
    composed = compose_rows(a1, a2, a3)
    if (composed[16]["owner"], composed[17]["owner"], composed[19]["owner"], composed[20]["owner"]) != (
        "a1", "a2", "a2", "a3"
    ):
        raise AssertionError("three-source ownership boundary changed")
    expect_failure("missing Attempt-3 row101", lambda: compose_rows(a1, a2, a3[:-1]))
    expect_failure(
        "missing Attempt-3 bridge row20",
        lambda: compose_rows(a1, a2, [row for row in a3 if row["sample_seq"] != "20"]),
    )
    assert len(prior.expected_transaction_keys(tuple(range(1, 18)))) == 136
    assert len(prior.expected_transaction_keys((18, 19, 20))) == 24
    assert len(prior.expected_transaction_keys(tuple(range(21, 102)))) == 648
    assert 136 + 24 + 648 == 808

    validate_attempt2_partial()
    model = dict(prior.read_rows(prior.ATTEMPT1_FILES["model-state"], prior.MODEL_STATE_FIELDS)[0])
    model["q"] = "0.001"
    expect_failure(
        "nonzero T4 q",
        lambda: prior.validate_model_row(model, prior.CANONICAL_EXPECTED[0], mode=35, attempt=1),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static", action="store_true", help="source, archive, and partial audit")
    modes.add_argument("--preflight", action="store_true", help="static audit plus exact fresh headers")
    modes.add_argument("--validate", action="store_true", help="validate Attempt 3 and the composite")
    modes.add_argument("--self-test", action="store_true", help="run static and mutation tests")
    args = parser.parse_args(argv)
    try:
        metrics: Metrics | None = None
        if args.static:
            validate_static_source()
            prior.validate_attempt1_partial()
            validate_attempt2_partial()
            label = "STATIC PASS"
        elif args.preflight:
            validate_preflight()
            label = "PREFLIGHT PASS"
        elif args.validate:
            metrics = validate_complete()
            label = "THREE-SOURCE COMPOSITE ACQUISITION VALID"
        else:
            self_test()
            label = "SELF-TEST PASS"
    except (
        AssertionError, OSError, UnicodeError, ValidationError,
        prior.anchor.ValidationError, prior.bounds.AuditError,
        prior.full.AnalysisError, ValueError,
    ) as exc:
        print(f"T4 new-location Attempt-3 validation: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"T4 new-location Attempt-3 recovery {label}")
    print(f"runner_sha256={PROGRAM_SHA256}")
    print("identity=campaign2026082701/mode37/attempt3")
    print("recovery=rows92 sequences1..9,17,20..101 closures30 traces736")
    print("canonical=A1:1..17+A2:18..20+A3:21..101 closures28 traces808")
    if metrics is not None:
        print(f"transfer={'PASS' if metrics.transfer_pass else 'FAIL'}")
        for field in Metrics.__dataclass_fields__:
            if field == "transfer_pass":
                continue
            value = getattr(metrics, field)
            print(f"{field}={value:.6f}" if isinstance(value, float) else f"{field}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
