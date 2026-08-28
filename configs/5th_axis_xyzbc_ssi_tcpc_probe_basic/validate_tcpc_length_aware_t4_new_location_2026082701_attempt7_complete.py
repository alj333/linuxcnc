#!/usr/bin/env python3
"""Offline completion validation for campaign-2026082701 T4 Attempt 7.

This validator imports neither LinuxCNC nor HAL. It validates the immutable
runner and prior-run ownership, the completed Attempt-7 outputs, adaptive
quiet telemetry, and the final A4+A6+A7 composite.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import hashlib
import math
from pathlib import Path
import stat
import sys
from typing import Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import assess_tcpc_length_aware_bounds as bounds
import validate_tcpc_length_aware_t4_attempt2 as canonical
import validate_tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery as frozen


HERE = Path(__file__).resolve().parent
CAMPAIGN = frozen.CAMPAIGN
MODE = frozen.MODE
ATTEMPT = frozen.ATTEMPT
MODEL_ID = frozen.MODEL_ID
TOOL = 4
TOOL_LENGTH_MM = 229.407000
PROBE_OFFSET_MM = 0.154742
EFFECTIVE_RADIUS_MM = 17.845258
DIFF_CAP_MM = 0.400000
TOTAL_CAP_MM = 1.350000
REFERENCE_RMS_MM = 0.120
REFERENCE_MAX_MM = 0.280

EXPECTED_SEQUENCES = tuple(range(24, 102))
EXPECTED_ROWS = frozen.EXPECTED_ROWS
EXPECTED_TRACES = frozen.EXPECTED_TRACES
EXPECTED_CLOSURES = frozen.EXPECTED_CLOSURES
EXPECTED_COMPOSITE_ROWS = frozen.EXPECTED_COMPOSITE_ROWS
EXPECTED_COMPOSITE_TRACES = frozen.EXPECTED_COMPOSITE_TRACES
EXPECTED_COMPOSITE_CLOSURES = frozen.EXPECTED_COMPOSITE_CLOSURES
EXPECTED_TAIL = tuple(canonical.EXPECTED_BY_SEQ[seq] for seq in EXPECTED_SEQUENCES)
EXPECTED_BY_SEQ = {row.seq: row for row in EXPECTED_TAIL}

DEFAULT_REPORT = (
    HERE
    / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT7_COMPLETION_REPORT.md"
)

RESULT_FIELDS = tuple(anchor.RESULT_FIELDS)
STATE_FIELDS = tuple(anchor.STATE_FIELDS)
MODEL_FIELDS = tuple(canonical.MODEL_STATE_FIELDS)
CLOSURE_FIELDS = tuple(campaign.CLOSURE_FIELDS)
CONTACT_FIELDS = frozen.TRACE_SCHEMA_V2["contact-trace"]
GAP_FIELDS = frozen.TRACE_SCHEMA_V2["gap-trace"]

SPEC = campaign.RunSpec(
    "T4 new-location Attempt 7",
    TOOL,
    MODE,
    TOOL_LENGTH_MM,
    PROBE_OFFSET_MM,
    EFFECTIVE_RADIUS_MM,
    frozen.A7_PATHS["results"],
    frozen.A7_PATHS["state"],
    frozen.A7_PATHS["closures"],
    EXPECTED_TAIL,
    (),
)

# Exact on-disk closure order. The source column selects the center owner for
# the opening row; all closing rows are owned by Attempt 7.
EXPECTED_CLOSURE_ROWS = (
    (10, 24, 30, 0.050),
    (-10, 31, 37, 0.050),
    (15, 38, 44, 0.050),
    (-15, 45, 51, 0.050),
    (30, 52, 56, 0.050),
    (-30, 57, 61, 0.050),
    (45, 62, 66, 0.050),
    (-45, 67, 71, 0.050),
    (905, 9, 72, 0.100),
    (60, 73, 77, 0.050),
    (-60, 78, 82, 0.050),
    (90, 83, 87, 0.050),
    (-90, 88, 92, 0.050),
    (911, 1, 93, 0.100),
    (906, 72, 93, 0.050),
    (912, 2, 94, 0.100),
    (913, 3, 95, 0.100),
    (914, 4, 96, 0.100),
    (915, 5, 97, 0.100),
    (916, 6, 98, 0.100),
    (917, 7, 99, 0.100),
    (918, 8, 100, 0.100),
    (919, 9, 101, 0.100),
    (200, 93, 101, 0.050),
    (900, 1, 101, 0.100),
)


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_int(row: dict[str, str], field: str) -> int:
    return frozen.exact_int(row, field)


def finite(row: dict[str, str], field: str) -> float:
    return frozen.finite(row, field)


def read_rows(kind: str, fields: Sequence[str]) -> list[dict[str, str]]:
    header, rows = frozen.csv_rows(frozen.A7_PATHS[kind])
    require(tuple(header) == tuple(fields), f"Attempt-7 {kind} header changed")
    return rows


def validate_output_files() -> None:
    prior_inodes = {
        (path.lstat().st_dev, path.lstat().st_ino)
        for path in (*frozen.A4_PATHS.values(), *frozen.A5_PATHS.values(), *frozen.A6_PATHS.values())
    }
    seen: set[tuple[int, int]] = set()
    for kind, path in frozen.A7_PATHS.items():
        require(path.exists(), f"missing Attempt-7 output: {path}")
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), f"Attempt-7 {kind} is not regular")
        require(not path.is_symlink(), f"Attempt-7 {kind} is a symlink")
        inode = (info.st_dev, info.st_ino)
        require(inode not in seen, f"Attempt-7 outputs alias each other: {kind}")
        require(inode not in prior_inodes, f"Attempt-7 {kind} aliases prior evidence")
        seen.add(inode)


def validate_frozen_sources() -> None:
    runner_text = frozen.read_ascii(frozen.RUNNER)
    frozen.validate_a4_sources()
    frozen.validate_a5_zero_row_sources()
    frozen.validate_a6_sources()
    frozen.validate_quiet_reference_model()
    frozen.validate_runner_text(runner_text, enforce_hash=True)


@contextmanager
def campaign_identity():
    previous = campaign.CAMPAIGN
    campaign.CAMPAIGN = CAMPAIGN
    try:
        yield
    finally:
        campaign.CAMPAIGN = previous


def require_identity(
    row: dict[str, str], sequence_field: str, *, schema: int = 1
) -> int:
    for field, value in (
        ("schema_version", schema),
        ("campaign_id", CAMPAIGN),
        ("stage_mode", MODE),
        ("attempt_id", ATTEMPT),
    ):
        require(exact_int(row, field) == value, f"{sequence_field}: {field} mismatch")
    sequence = exact_int(row, sequence_field)
    require(sequence in EXPECTED_BY_SEQ, f"{sequence_field}={sequence} outside 24..101")
    return sequence


def validate_summary_rows() -> tuple[
    list[dict[str, str]], list[dict[str, str]], dict[int, np.ndarray]
]:
    results = read_rows("results", RESULT_FIELDS)
    states = read_rows("state", STATE_FIELDS)
    require(len(results) == len(states) == EXPECTED_ROWS, "A7 result/state row count mismatch")
    require(
        [exact_int(row, "sample_seq") for row in results] == list(EXPECTED_SEQUENCES),
        "A7 results are not exact ordered sequences 24..101",
    )
    require(
        [exact_int(row, "sample_seq") for row in states] == list(EXPECTED_SEQUENCES),
        "A7 states are not exact ordered sequences 24..101",
    )

    centers: dict[int, np.ndarray] = {}
    with campaign_identity():
        for result, state, expected in zip(results, states, EXPECTED_TAIL, strict=True):
            centers[expected.seq] = campaign.validate_result(SPEC, result, expected, ATTEMPT)
            campaign.validate_state(SPEC, state, result, expected, ATTEMPT)
    return results, states, centers


def expected_empirical_vector(b_deg: float, c_deg: float) -> np.ndarray:
    basis = bounds.basis_values(b_deg, np.asarray([c_deg], dtype=float))
    coefficients = bounds.surface_coefficients(TOOL_LENGTH_MM)["total"]
    return bounds.evaluate_surface(basis, coefficients)[0]


def validate_model_row(row: dict[str, str], expected: campaign.ExpectedRow) -> None:
    sequence = require_identity(row, "sample_seq")
    require(sequence == expected.seq, f"model-state seq {sequence} out of order")
    for field, value in (
        ("model_id", MODEL_ID),
        ("expected_model_id", MODEL_ID),
        ("configured", 1),
        ("valid", 1),
        ("fault_code", 0),
    ):
        require(exact_int(row, field) == value, f"model-state seq {sequence}: {field} mismatch")
    require(abs(finite(row, "q")) <= 1e-6, f"model-state seq {sequence}: q is not zero")
    require(
        campaign.angular_error(finite(row, "evaluated_b_deg"), expected.pose.b_deg) <= 0.01,
        f"model-state seq {sequence}: evaluated B mismatch",
    )
    require(
        campaign.angular_error(finite(row, "evaluated_c_deg"), expected.pose.c_deg) <= 0.01,
        f"model-state seq {sequence}: evaluated C mismatch",
    )
    require(
        abs(finite(row, "evaluated_length_mm") - TOOL_LENGTH_MM) <= 0.002,
        f"model-state seq {sequence}: evaluated length mismatch",
    )

    diff = np.asarray([finite(row, f"diff_offset_{axis}_mm") for axis in "xyz"])
    diff_norm = finite(row, "diff_offset_norm_mm")
    require(np.max(np.abs(diff)) <= 1e-6 and abs(diff_norm) <= 1e-6, f"model-state seq {sequence}: q=0 differential is nonzero")
    require(abs(diff_norm - float(np.linalg.norm(diff))) <= 3e-6, f"model-state seq {sequence}: differential norm mismatch")
    require(diff_norm <= DIFF_CAP_MM, f"model-state seq {sequence}: differential cap exceeded")

    empirical = np.asarray([finite(row, f"empirical_offset_{axis}_mm") for axis in "xyz"])
    empirical_norm = finite(row, "empirical_offset_norm_mm")
    require(0.0 <= empirical_norm <= TOTAL_CAP_MM, f"model-state seq {sequence}: empirical cap exceeded")
    require(abs(empirical_norm - float(np.linalg.norm(empirical))) <= 5e-6, f"model-state seq {sequence}: empirical norm mismatch")
    expected_vector = expected_empirical_vector(expected.pose.b_deg, expected.pose.c_deg)
    require(float(np.linalg.norm(empirical - expected_vector)) <= 2e-5, f"model-state seq {sequence}: empirical vector changed")


def validate_model_rows() -> list[dict[str, str]]:
    rows = read_rows("model-state", MODEL_FIELDS)
    require(len(rows) == EXPECTED_ROWS, "A7 model-state row count mismatch")
    for row, expected in zip(rows, EXPECTED_TAIL, strict=True):
        validate_model_row(row, expected)
    return rows


def counter_tuple(row: dict[str, str], prefix: str) -> tuple[int, int, int]:
    return tuple(exact_int(row, f"{prefix}_{name}_count") for name in ("raw", "mux", "gated"))


def expected_trace_keys() -> list[tuple[int, int, int, int]]:
    return [
        (sequence, 1, pass_id, contact_id)
        for sequence in EXPECTED_SEQUENCES
        for pass_id in (1, 2)
        for contact_id in (1, 2, 3, 4)
    ]


def trace_key(row: dict[str, str], sequence_field: str) -> tuple[int, int, int, int]:
    return (
        require_identity(row, sequence_field, schema=2),
        exact_int(row, "acquisition_try"),
        exact_int(row, "pass_id"),
        exact_int(row, "contact_id"),
    )


def validate_trace_pose(row: dict[str, str], sequence: int) -> None:
    expected = EXPECTED_BY_SEQ[sequence]
    require(
        campaign.angular_error(finite(row, "abs_b_deg"), expected.pose.b_deg) <= 0.01,
        f"trace seq {sequence}: B pose mismatch",
    )
    require(
        campaign.angular_error(finite(row, "abs_c_deg"), expected.pose.c_deg) <= 0.01,
        f"trace seq {sequence}: C pose mismatch",
    )


def validate_quiet_telemetry(
    row: dict[str, str], *, activity_requires_quiet: bool, label: str
) -> None:
    chatter = exact_int(row, "chatter_observed")
    episodes = exact_int(row, "quiet_episode_count")
    resets = exact_int(row, "quiet_reset_count")
    elapsed = finite(row, "quiet_elapsed_s")
    require(chatter in (0, 1), f"{label}: chatter flag is not binary")
    require(episodes >= 0 and resets >= 0 and elapsed >= 0.0, f"{label}: negative quiet telemetry")
    require(elapsed <= frozen.QUIET_TIMEOUT_S + frozen.QUIET_SAMPLE_S, f"{label}: quiet timeout exceeded")
    require(abs(elapsed / frozen.QUIET_SAMPLE_S - round(elapsed / frozen.QUIET_SAMPLE_S)) <= 1e-6, f"{label}: quiet time is not sampled in 0.25 s steps")
    if chatter:
        require(episodes == 1, f"{label}: chatter does not own exactly one quiet episode")
        require(elapsed + 1e-9 >= frozen.QUIET_DURATION_S, f"{label}: quiet episode shorter than 15 s")
        require(resets <= round(elapsed / frozen.QUIET_SAMPLE_S) + 1, f"{label}: impossible quiet reset count")
    else:
        require(episodes == 0 and resets == 0 and abs(elapsed) <= 1e-9, f"{label}: quiet telemetry exists without chatter")
    require(not activity_requires_quiet or chatter == 1, f"{label}: counter activity was accepted without quiet")


def validate_contact_row(row: dict[str, str], key: tuple[int, int, int, int]) -> None:
    sequence, acquisition_try, pass_id, contact_id = key
    require(acquisition_try == 1 and pass_id in (1, 2) and contact_id in (1, 2, 3, 4), f"contact seq {sequence}: transaction key invalid")
    validate_trace_pose(row, sequence)
    pre = counter_tuple(row, "pre")
    post = counter_tuple(row, "post")
    ready = counter_tuple(row, "ready")
    require(all(value >= 0 for value in pre + post + ready), f"contact seq {sequence}: negative counter")
    require(all(pre[i] <= post[i] <= ready[i] for i in range(3)), f"contact seq {sequence}: non-monotonic counter")

    direct = tuple(post[i] - pre[i] for i in range(3))
    repeats = tuple(ready[i] - post[i] for i in range(3))
    total = tuple(ready[i] - pre[i] for i in range(3))
    for field, value in zip(("raw_delta", "mux_delta", "gated_delta"), direct, strict=True):
        require(exact_int(row, field) == value, f"contact seq {sequence}: {field} mismatch")
    for field, value in zip(("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"), repeats, strict=True):
        require(exact_int(row, field) == value, f"contact seq {sequence}: {field} mismatch")
    require(direct[0] == direct[1] and direct[0] >= 1 and direct[2] == 1, f"contact seq {sequence}: G38 edge invariant failed")
    require(repeats[0] == repeats[1] and repeats[2] == 0, f"contact seq {sequence}: repeat edge invariant failed")
    require(total[0] == total[1], f"contact seq {sequence}: cumulative raw/mux mismatch")

    extra = total[0] - total[2]
    require(extra >= 0, f"contact seq {sequence}: negative extra count")
    require(exact_int(row, "extra_raw_minus_gated_delta") == extra, f"contact seq {sequence}: extra count mismatch")
    require(exact_int(row, "probe_result") == 1, f"contact seq {sequence}: probe did not succeed")
    for field in ("consistency_fault", "release_fault", "terminal_failure"):
        require(exact_int(row, field) == 0, f"contact seq {sequence}: {field} set")
    travel = finite(row, "travel_mm")
    upper = 7.01 if contact_id == 1 else 6.01
    require(1.0 <= travel <= upper, f"contact seq {sequence}: travel outside bounds")
    validate_quiet_telemetry(
        row,
        activity_requires_quiet=extra > 0,
        label=f"contact seq {sequence} pass {pass_id} id {contact_id}",
    )


def validate_contact_rows() -> list[dict[str, str]]:
    rows = read_rows("contact-trace", CONTACT_FIELDS)
    require(len(rows) == EXPECTED_TRACES, f"expected {EXPECTED_TRACES} contact rows, got {len(rows)}")
    keys = [trace_key(row, "global_seq") for row in rows]
    require(keys == expected_trace_keys(), "A7 contact trace order changed")
    for row, key in zip(rows, keys, strict=True):
        validate_contact_row(row, key)
    return rows


def validate_gap_row(
    gap: dict[str, str],
    contact: dict[str, str],
    previous_contact: dict[str, str] | None,
    index: int,
    key: tuple[int, int, int, int],
) -> None:
    sequence, acquisition_try, pass_id, contact_id = key
    require(acquisition_try == 1 and pass_id in (1, 2) and contact_id in (1, 2, 3, 4), f"gap seq {sequence}: transaction key invalid")
    require(trace_key(contact, "global_seq") == key, f"gap seq {sequence}: contact key mismatch")
    validate_trace_pose(gap, sequence)
    prior = counter_tuple(gap, "prior_ready")
    current = counter_tuple(gap, "current_pre")
    require(all(value >= 0 for value in prior + current), f"gap seq {sequence}: negative counter")
    delta = tuple(current[i] - prior[i] for i in range(3))
    require(all(value >= 0 for value in delta), f"gap seq {sequence}: non-monotonic counter")
    for field, value in zip(("gap_raw_delta", "gap_mux_delta", "gap_gated_delta"), delta, strict=True):
        require(exact_int(gap, field) == value, f"gap seq {sequence}: {field} mismatch")
    require(delta[0] == delta[1] and delta[2] == 0, f"gap seq {sequence}: outside-G38 edge invariant failed")

    initial = exact_int(gap, "initial_baseline")
    require(initial == int(index == 0), "only the first A7 gap may mark the initial baseline")
    prior_extra = exact_int(gap, "prior_contact_extra_delta")
    if previous_contact is None:
        require(prior_extra == 0 and not any(delta), "initial baseline contains prior or gap activity")
    else:
        require(prior == counter_tuple(previous_contact, "ready"), f"gap seq {sequence}: prior-ready boundary mismatch")
        require(prior_extra == exact_int(previous_contact, "extra_raw_minus_gated_delta"), f"gap seq {sequence}: prior extra mismatch")
    require(current == counter_tuple(contact, "pre"), f"gap seq {sequence}: current-pre/contact-pre mismatch")
    combined = prior_extra + delta[0] - delta[2]
    require(exact_int(gap, "combined_extra_delta") == combined, f"gap seq {sequence}: combined extra mismatch")
    require(combined >= 0, f"gap seq {sequence}: negative combined extra")
    require(exact_int(gap, "consistency_fault") == 0, f"gap seq {sequence}: consistency fault set")
    validate_quiet_telemetry(
        gap,
        activity_requires_quiet=delta[0] > 0,
        label=f"gap seq {sequence} pass {pass_id} id {contact_id}",
    )


def validate_gap_rows(contacts: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    rows = read_rows("gap-trace", GAP_FIELDS)
    require(len(rows) == EXPECTED_TRACES, f"expected {EXPECTED_TRACES} gap rows, got {len(rows)}")
    keys = [trace_key(row, "next_global_seq") for row in rows]
    require(keys == expected_trace_keys(), "A7 gap trace order changed")
    previous: dict[str, str] | None = None
    for index, (gap, contact, key) in enumerate(zip(rows, contacts, keys, strict=True)):
        validate_gap_row(gap, contact, previous, index, key)
        previous = contact
    return rows


def composite_center_rows(
    a7_results: Sequence[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[int, np.ndarray]]:
    _, a4 = frozen.csv_rows(frozen.A4_PATHS["results"])
    _, a6_all = frozen.csv_rows(frozen.A6_PATHS["results"])
    a6 = [row for row in a6_all if 10 <= exact_int(row, "sample_seq") <= 23]
    rows = [*a4, *a6, *a7_results]
    require(len(rows) == EXPECTED_COMPOSITE_ROWS, "composite result count is not 101")
    require([exact_int(row, "sample_seq") for row in rows] == list(range(1, 102)), "composite result sequence is not 1..101")
    centers = {
        exact_int(row, "sample_seq"): np.asarray(
            [finite(row, f"center_abs_{axis}_mm") for axis in "xyz"], dtype=float
        )
        for row in rows
    }
    return rows, centers


def validate_closure_rows(center_by_seq: dict[int, np.ndarray]) -> tuple[list[dict[str, str]], np.ndarray]:
    rows = read_rows("closures", CLOSURE_FIELDS)
    require(len(rows) == len(EXPECTED_CLOSURE_ROWS) == EXPECTED_CLOSURES, "A7 closure count mismatch")
    norms: list[float] = []
    for row, expected in zip(rows, EXPECTED_CLOSURE_ROWS, strict=True):
        block, open_sequence, close_sequence, limit = expected
        for field, value in (
            ("schema_version", 1),
            ("campaign_id", CAMPAIGN),
            ("stage_mode", MODE),
            ("attempt_id", ATTEMPT),
            ("block_id", block),
            ("open_sample_seq", open_sequence),
            ("close_sample_seq", close_sequence),
            ("pass", 1),
        ):
            require(exact_int(row, field) == value, f"closure block {block}: {field} mismatch")
        require(abs(finite(row, "limit_mm") - limit) <= 1e-9, f"closure block {block}: limit mismatch")
        expected_close = canonical.EXPECTED_BY_SEQ[close_sequence]
        require(campaign.angular_error(finite(row, "abs_b_deg"), expected_close.pose.b_deg) <= 0.01, f"closure block {block}: B mismatch")
        require(campaign.angular_error(finite(row, "abs_c_deg"), expected_close.pose.c_deg) <= 0.01, f"closure block {block}: C mismatch")
        delta = center_by_seq[close_sequence] - center_by_seq[open_sequence]
        logged = np.asarray([finite(row, f"closure_d{axis}_mm") for axis in "xyz"])
        require(float(np.linalg.norm(delta - logged)) <= 3e-6, f"closure block {block}: vector mismatch")
        norm = finite(row, "closure_norm_mm")
        require(abs(norm - float(np.linalg.norm(delta))) <= 3e-6, f"closure block {block}: norm mismatch")
        require(0.0 <= norm <= limit + 1e-9, f"closure block {block}: limit exceeded")
        norms.append(norm)
    return rows, np.asarray(norms)


def validate_composite_ownership(
    a7_closures: Sequence[dict[str, str]],
    a7_contacts: Sequence[dict[str, str]],
    a7_gaps: Sequence[dict[str, str]],
) -> None:
    _, a4_closures = frozen.csv_rows(frozen.A4_PATHS["closures"])
    _, a6_closures = frozen.csv_rows(frozen.A6_PATHS["closures"])
    retained_closures = [row for row in a4_closures if exact_int(row, "block_id") == 100]
    retained_closures.extend(a6_closures)
    retained_closures.extend(a7_closures)
    require(len(retained_closures) == EXPECTED_COMPOSITE_CLOSURES, "composite closure ownership is not 28")
    require(all(exact_int(row, "pass") == 1 for row in retained_closures), "composite contains a failed closure")

    composite_by_kind: dict[str, list[dict[str, str]]] = {}
    for kind, sequence_field, a7_rows in (
        ("contact-trace", "global_seq", a7_contacts),
        ("gap-trace", "next_global_seq", a7_gaps),
    ):
        _, a4_rows = frozen.csv_rows(frozen.A4_PATHS[kind])
        _, a6_all = frozen.csv_rows(frozen.A6_PATHS[kind])
        a6_rows = [row for row in a6_all if 10 <= exact_int(row, sequence_field) <= 23]
        mapped = [frozen.normalize_trace_row(kind, row) for row in (*a4_rows, *a6_rows)]
        composite = [*mapped, *a7_rows]
        require(len(composite) == EXPECTED_COMPOSITE_TRACES, f"composite {kind} count is not 808")
        keys = [
            (
                exact_int(row, sequence_field),
                exact_int(row, "acquisition_try"),
                exact_int(row, "pass_id"),
                exact_int(row, "contact_id"),
            )
            for row in composite
        ]
        expected = [
            (sequence, 1, pass_id, contact_id)
            for sequence in range(1, 102)
            for pass_id in (1, 2)
            for contact_id in (1, 2, 3, 4)
        ]
        require(keys == expected, f"composite {kind} topology changed")
        composite_by_kind[kind] = composite


def centered_metrics(
    rows: Sequence[dict[str, str]],
) -> dict[str, float]:
    centers = np.vstack(
        [
            [finite(row, f"center_abs_{axis}_mm") for axis in "xyz"]
            for row in rows
        ]
    )
    residuals = centers - np.mean(centers, axis=0)
    norms = np.linalg.norm(residuals, axis=1)
    groups: dict[tuple[float, float], list[np.ndarray]] = {}
    for row, center in zip(rows, centers, strict=True):
        key = (round(finite(row, "abs_b_deg"), 6), round(finite(row, "abs_c_deg") % 360.0, 6))
        groups.setdefault(key, []).append(center)
    unique = np.vstack([np.mean(np.vstack(values), axis=0) for values in groups.values()])
    unique_residuals = unique - np.mean(unique, axis=0)
    unique_norms = np.linalg.norm(unique_residuals, axis=1)
    return {
        "rows": float(len(rows)),
        "unique": float(len(unique)),
        "raw_rms": float(math.sqrt(np.mean(norms * norms))),
        "raw_max": float(np.max(norms)),
        "equal_unique_rms": float(math.sqrt(np.mean(unique_norms * unique_norms))),
        "equal_unique_max": float(np.max(unique_norms)),
    }


def trace_diagnostics(
    contacts: Sequence[dict[str, str]], gaps: Sequence[dict[str, str]]
) -> dict[str, float]:
    start = counter_tuple(gaps[0], "prior_ready")
    finish = counter_tuple(contacts[-1], "ready")
    contact_extras = [exact_int(row, "extra_raw_minus_gated_delta") for row in contacts]
    gap_extras = [exact_int(row, "gap_raw_delta") for row in gaps]
    contact_extra_total = sum(contact_extras)
    gap_extra_total = sum(gap_extras)
    admitted = finish[2] - start[2]
    raw_delta = finish[0] - start[0]
    require(finish[0] == finish[1], "final raw/mux counters differ")
    require(admitted == EXPECTED_TRACES, "final gated counter delta is not 624")
    require(raw_delta == admitted + contact_extra_total + gap_extra_total, "counter-chain extra total mismatch")
    return {
        "baseline_raw": float(start[0]),
        "baseline_mux": float(start[1]),
        "baseline_gated": float(start[2]),
        "final_raw": float(finish[0]),
        "final_mux": float(finish[1]),
        "final_gated": float(finish[2]),
        "gated_edges": float(admitted),
        "contact_extra_transactions": float(sum(value > 0 for value in contact_extras)),
        "contact_extra_edges": float(contact_extra_total),
        "gap_extra_transactions": float(sum(value > 0 for value in gap_extras)),
        "gap_extra_edges": float(gap_extra_total),
        "filtered_extra_edges": float(contact_extra_total + gap_extra_total),
        "direct_duplicate_transactions": float(sum(exact_int(row, "raw_delta") > 1 for row in contacts)),
        "repeat_extra_transactions": float(sum(exact_int(row, "repeat_raw_delta") > 0 for row in contacts)),
        "contact_quiet_episodes": float(sum(exact_int(row, "quiet_episode_count") for row in contacts)),
        "gap_quiet_episodes": float(sum(exact_int(row, "quiet_episode_count") for row in gaps)),
        "contact_quiet_elapsed_s": float(sum(finite(row, "quiet_elapsed_s") for row in contacts)),
        "gap_quiet_elapsed_s": float(sum(finite(row, "quiet_elapsed_s") for row in gaps)),
        "quiet_resets": float(sum(exact_int(row, "quiet_reset_count") for row in (*contacts, *gaps))),
        "max_contact_extra": float(max(contact_extras, default=0)),
        "max_gap_extra": float(max(gap_extras, default=0)),
        "max_combined_extra": float(max(exact_int(row, "combined_extra_delta") for row in gaps)),
    }


def validate_completed_run() -> dict[str, object]:
    validate_frozen_sources()
    validate_output_files()
    results, states, a7_centers = validate_summary_rows()
    models = validate_model_rows()
    contacts = validate_contact_rows()
    gaps = validate_gap_rows(contacts)
    composite_rows, composite_centers = composite_center_rows(results)
    closures, closure_norms = validate_closure_rows(composite_centers)
    validate_composite_ownership(closures, contacts, gaps)
    return {
        "results": results,
        "states": states,
        "models": models,
        "contacts": contacts,
        "gaps": gaps,
        "closures": closures,
        "a7_centers": a7_centers,
        "a7_metrics": centered_metrics(results),
        "composite_metrics": centered_metrics(composite_rows),
        "closure_norms": closure_norms,
        "diagnostics": trace_diagnostics(contacts, gaps),
    }


def write_report(path: Path, data: dict[str, object]) -> None:
    a7 = data["a7_metrics"]
    composite = data["composite_metrics"]
    diagnostics = data["diagnostics"]
    closure_norms = data["closure_norms"]
    assert isinstance(a7, dict) and isinstance(composite, dict)
    assert isinstance(diagnostics, dict) and isinstance(closure_norms, np.ndarray)
    reference_pass = (
        composite["equal_unique_rms"] <= REFERENCE_RMS_MM
        and composite["equal_unique_max"] <= REFERENCE_MAX_MM
    )
    internal_norms = [
        finite(row, "closure_norm_mm")
        for row in data["closures"]
        if abs(finite(row, "limit_mm") - 0.050) <= 1e-9
    ]
    external_norms = [
        finite(row, "closure_norm_mm")
        for row in data["closures"]
        if abs(finite(row, "limit_mm") - 0.100) <= 1e-9
    ]
    lines = [
        "# T4 New-Location Attempt-7 Completion Report",
        "",
        "Status: `PASS - DATA INTEGRITY; ACCURACY FIT/REVIEW REQUIRED`",
        "",
        f"- campaign / mode / attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- runner SHA-256: `{sha256(frozen.RUNNER)}`",
        f"- exact A7 rows / closures / traces: `{EXPECTED_ROWS} / {EXPECTED_CLOSURES} / {EXPECTED_TRACES}/{EXPECTED_TRACES}`",
        f"- exact composite rows / closures / traces: `{EXPECTED_COMPOSITE_ROWS} / {EXPECTED_COMPOSITE_CLOSURES} / {EXPECTED_COMPOSITE_TRACES}/{EXPECTED_COMPOSITE_TRACES}`",
        f"- A7 raw centered RMS / max: `{a7['raw_rms']:.6f} / {a7['raw_max']:.6f} mm`",
        f"- composite raw centered RMS / max: `{composite['raw_rms']:.6f} / {composite['raw_max']:.6f} mm`",
        f"- composite equal-{int(composite['unique'])}-pose RMS / max: `{composite['equal_unique_rms']:.6f} / {composite['equal_unique_max']:.6f} mm`",
        f"- prior reference-location guide `{REFERENCE_RMS_MM:.3f}/{REFERENCE_MAX_MM:.3f} mm`: `{'PASS' if reference_pass else 'EXCEEDED - diagnostic, not a data rejection'}`",
        f"- worst same-run / cross-attempt closure: `{max(internal_norms):.6f} / {max(external_norms):.6f} mm`",
        f"- admitted G38 edges: `{int(diagnostics['gated_edges'])}`",
        f"- filtered matched raw/mux extras: `{int(diagnostics['filtered_extra_edges'])}` (`{int(diagnostics['contact_extra_edges'])}` contact, `{int(diagnostics['gap_extra_edges'])}` gap)",
        f"- adaptive quiet episodes: `{int(diagnostics['contact_quiet_episodes'])}` contact + `{int(diagnostics['gap_quiet_episodes'])}` gap",
        f"- adaptive quiet elapsed: `{diagnostics['contact_quiet_elapsed_s'] + diagnostics['gap_quiet_elapsed_s']:.2f} s`; resets `{int(diagnostics['quiet_resets'])}`",
        f"- largest contact / gap / combined extra burst: `{int(diagnostics['max_contact_extra'])} / {int(diagnostics['max_gap_extra'])} / {int(diagnostics['max_combined_extra'])}` edges",
        f"- counter chain: `{int(diagnostics['baseline_raw'])}/{int(diagnostics['baseline_mux'])}/{int(diagnostics['baseline_gated'])}` -> `{int(diagnostics['final_raw'])}/{int(diagnostics['final_mux'])}/{int(diagnostics['final_gated'])}`",
        "",
        "All identities, sequence ownership, poses, result geometry, state snapshots, T4/TLO values, q=0 model vectors, closure vectors and limits, counter chains, exactly-one gated G38 edges, zero outside-G38 gated edges, quiet timing, and terminal fault flags passed.",
        "",
        "The adaptive policy handled matched gate-closed receiver chatter without accepting a false gated probe edge. The accuracy guide is intentionally not used as a data-integrity rejection at this second table location; the observed location-dependent residuals are evidence for the next offline fit and machine-volume separation step.",
        "",
        "## Output Hashes",
        "",
    ]
    for kind, output in frozen.A7_PATHS.items():
        lines.append(f"- `{output.name}`: `{sha256(output)}`")
    lines.extend(
        [
            "",
            "This validator imports neither LinuxCNC nor HAL and issued no controller command.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="ascii")


def expect_failure(label: str, operation) -> None:
    try:
        operation()
    except (ValidationError, anchor.ValidationError, KeyError, ValueError):
        return
    raise AssertionError(f"self-test mutation accepted: {label}")


def self_test() -> int:
    data = validate_completed_run()
    contacts = data["contacts"]
    gaps = data["gaps"]
    models = data["models"]
    closures = data["closures"]
    composite_rows, composite_centers = composite_center_rows(data["results"])
    del composite_rows
    rejected = 0

    bad = copy.deepcopy(contacts[0])
    bad["gated_delta"] = "0"
    expect_failure("contact gated delta", lambda: validate_contact_row(bad, expected_trace_keys()[0]))
    rejected += 1

    chatter_index = next(index for index, row in enumerate(contacts) if exact_int(row, "chatter_observed") == 1)
    bad = copy.deepcopy(contacts[chatter_index])
    bad["quiet_elapsed_s"] = "14.75"
    expect_failure("short contact quiet", lambda: validate_contact_row(bad, expected_trace_keys()[chatter_index]))
    rejected += 1

    gap_index = next(index for index, row in enumerate(gaps) if exact_int(row, "chatter_observed") == 1)
    bad = copy.deepcopy(gaps[gap_index])
    bad["quiet_episode_count"] = "0"
    previous = contacts[gap_index - 1] if gap_index else None
    expect_failure(
        "gap chatter without quiet",
        lambda: validate_gap_row(bad, contacts[gap_index], previous, gap_index, expected_trace_keys()[gap_index]),
    )
    rejected += 1

    bad = copy.deepcopy(models[0])
    bad["q"] = "1"
    expect_failure("T4 nonzero q", lambda: validate_model_row(bad, EXPECTED_TAIL[0]))
    rejected += 1

    bad_closures = copy.deepcopy(closures)
    bad_closures[0]["pass"] = "0"
    expect_failure("failed retained closure", lambda: validate_closure_rows_from_memory(bad_closures, composite_centers))
    rejected += 1
    return rejected


def validate_closure_rows_from_memory(
    rows: Sequence[dict[str, str]], center_by_seq: dict[int, np.ndarray]
) -> None:
    require(len(rows) == len(EXPECTED_CLOSURE_ROWS), "mutated closure row count")
    for row, expected in zip(rows, EXPECTED_CLOSURE_ROWS, strict=True):
        block, open_sequence, close_sequence, limit = expected
        require(exact_int(row, "block_id") == block, "mutated closure block")
        require(exact_int(row, "pass") == 1, "mutated closure pass")
        require(abs(finite(row, "limit_mm") - limit) <= 1e-9, "mutated closure limit")
        delta = center_by_seq[close_sequence] - center_by_seq[open_sequence]
        require(abs(finite(row, "closure_norm_mm") - float(np.linalg.norm(delta))) <= 3e-6, "mutated closure norm")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            rejected = self_test()
            print(f"Attempt-7 completion validator self-test: PASS ({rejected}/5 mutations rejected)")
            return 0
        data = validate_completed_run()
        write_report(args.report, data)
    except (
        AssertionError,
        OSError,
        ValidationError,
        anchor.ValidationError,
        bounds.AuditError,
        ValueError,
    ) as exc:
        print(f"Attempt-7 completion validation: FAIL: {exc}", file=sys.stderr)
        return 1
    metrics = data["composite_metrics"]
    diagnostics = data["diagnostics"]
    assert isinstance(metrics, dict) and isinstance(diagnostics, dict)
    print("Attempt-7 completion validation: PASS - DATA INTEGRITY")
    print(f"A7 contract: {EXPECTED_ROWS} rows, {EXPECTED_CLOSURES} closures, {EXPECTED_TRACES}/{EXPECTED_TRACES} traces")
    print(f"composite contract: {EXPECTED_COMPOSITE_ROWS} rows, {EXPECTED_COMPOSITE_CLOSURES} closures, {EXPECTED_COMPOSITE_TRACES}/{EXPECTED_COMPOSITE_TRACES} traces")
    print(f"composite equal-pose RMS/max: {metrics['equal_unique_rms']:.6f}/{metrics['equal_unique_max']:.6f} mm")
    print(f"filtered extras: {int(diagnostics['filtered_extra_edges'])}; admitted gated edges: {int(diagnostics['gated_edges'])}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
