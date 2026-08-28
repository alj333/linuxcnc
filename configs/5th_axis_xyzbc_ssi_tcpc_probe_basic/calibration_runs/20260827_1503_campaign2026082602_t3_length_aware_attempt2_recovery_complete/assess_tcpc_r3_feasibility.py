#!/usr/bin/env python3
"""Deterministic offline feasibility assessment for a future TCPC R3 model.

The program reads only hash-frozen calibration archives.  It has no LinuxCNC
or HAL imports, no machine-control path, and never writes a pin, overlay, INI,
tool-table, or live configuration file. Its sole optional write is the fixed
``TCPC_R3_FEASIBILITY_REPORT.md`` beside this script.

The four-source T3 composite is development evidence only.  The joint fit in
this assessment is deliberately an illustration of mathematical feasibility,
not a candidate and not a coefficient release.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
import tempfile
from typing import Iterable, Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
RUNS = HERE / "calibration_runs"

T4_ARCHIVE = RUNS / "20260825_0909_campaign04_t4_fit_r2_frozen"
T4_RESULTS = T4_ARCHIVE / "tcpc-relocated-sphere-t4-primary-results.csv"
T4_STATE = T4_ARCHIVE / "tcpc-relocated-sphere-t4-primary-state.csv"
T4_CLOSURES = T4_ARCHIVE / "tcpc-relocated-sphere-t4-primary-closures.csv"
R2_PINS = T4_ARCHIVE / "tcpc-relocated-sphere-t4-fit-r2-pins.csv"
R2_RESIDUALS = T4_ARCHIVE / "tcpc-relocated-sphere-t4-fit-r2-residuals.csv"
R2_FITTER = T4_ARCHIVE / "fit_tcpc_relocated_sphere_t4_r2.py"

T3_A1_ARCHIVE = RUNS / (
    "20260826_1131_campaign2026082601_t3_exploratory_attempt1_"
    "partial_no_touch_seq15"
)
T3_A2_ARCHIVE = RUNS / (
    "20260826_1238_campaign2026082601_t3_exploratory_attempt2_"
    "partial_gap_burst_seq23"
)
T3_A4_ARCHIVE = RUNS / (
    "20260826_1359_campaign2026082601_t3_exploratory_attempt4_"
    "partial_fault_latch_before_seq24"
)
T3_A5_ARCHIVE = RUNS / (
    "20260826_1612_campaign2026082601_t3_exploratory_attempt5_complete"
)

DEFAULT_REPORT = HERE / "TCPC_R3_FEASIBILITY_REPORT.md"

T4_CAMPAIGN = 2026082404
T4_MODE = 23
T4_ATTEMPT = 1
T3_CAMPAIGN = 2026082601
T3_TOOL = 3
T3_TOOL_LENGTH = 128.606729
B_ZERO_DEG = 0.0
C_ZERO_DEG = -0.024500
RIDGE_LAMBDA = 30.0
AVERAGED_LOSS_SENSITIVITY_LAMBDA = 60.0
CLOSURE_LIMIT_MM = 0.050

AXES = ("x", "y", "z")
ADMISSIBLE_TERMS = (
    "c_cos",
    "c_sin",
    "c_cos2",
    "c_sin2",
    "b_sin",
    "b_omc",
    "b_sin2",
    "bc_sinb_sinc",
    "bc_omcb_sinc",
    "bc_omcb_sin2c",
    "bc_sinb_cosc",
    "bc_omcb_cosc",
    "bc_sinb_cos2c",
    "bmid_base",
    "bmid_cosc",
    "bmid_sinc",
    "bmid_cos2c",
)
R2_TERMS = (
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
STABLE7_TERMS = (
    "c_cos",
    "b_sin",
    "bc_sinb_sinc",
    "bc_omcb_sin2c",
    "bmid_base",
    "bmid_cosc",
    "bmid_sinc",
)


class AssessmentError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    label: str
    archive: Path
    prefix: str
    mode: int
    attempt: int
    sequences: tuple[int, ...]
    result_rows: int
    closure_rows: int
    contact_rows: int
    gap_rows: int

    def path(self, suffix: str) -> Path:
        return self.archive / f"{self.prefix}-{suffix}.csv"


T3_SOURCES = (
    Source(
        "A1",
        T3_A1_ARCHIVE,
        "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1",
        30,
        1,
        tuple(range(1, 15)),
        14,
        2,
        119,
        119,
    ),
    Source(
        "A2",
        T3_A2_ARCHIVE,
        "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery",
        31,
        2,
        tuple(range(15, 23)),
        8,
        1,
        64,
        65,
    ),
    Source(
        "A4",
        T3_A4_ARCHIVE,
        "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery",
        31,
        4,
        (23,),
        1,
        0,
        8,
        8,
    ),
    Source(
        "A5",
        T3_A5_ARCHIVE,
        "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt5-recovery",
        31,
        5,
        tuple(range(24, 32)),
        8,
        1,
        64,
        64,
    ),
)


EXPECTED_SHA256: dict[Path, str] = {
    T4_ARCHIVE / "SHA256SUMS":
        "602cf8bf0bef86fcb4e80f1b1b7323a8a7608fc2c7baad35e3d2ed909d759835",
    T4_RESULTS:
        "70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468",
    T4_STATE:
        "dd09051f37bfc8c91e13d3617e77bc9e2aea40393237cc935e1350364a73693d",
    T4_CLOSURES:
        "f0fd62d8c99259c7ea76d167b1d9ce7ee68825a7cef1234f3ce3906a4a9c3021",
    R2_PINS:
        "d3481e51cd98b6fc4c8ac8484a781b6fe88321ab371b53bc5081248f72c1e2b6",
    R2_RESIDUALS:
        "8de7e98a4767eba6545ee3e6f3a0688bf56e43427153bea79c08c4787f59ade1",
    R2_FITTER:
        "faae48919e01f5f7cf5a9e8f29da40fc77bdf359d21bec1848bdcdfb979c71bb",
    T3_A1_ARCHIVE / "SHA256SUMS":
        "85306077f177700c49fc122fc79d2e24edbc7ab5d11b25209a8e7eb35439d700",
    T3_A1_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-results.csv":
        "bd529dc0ebbdabcddca92ce0a46bf5e6da5f4718ba659e3d44ff8a4f57279e81",
    T3_A1_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-state.csv":
        "108a5859acc6e360913ef74a17130004b0a2b75112f560cf00cb653c7d35aee0",
    T3_A1_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-closures.csv":
        "ac58157f6fb29ca61098373059089a2d7e8ab86f0bc58dc68f05b0da5e5aa111",
    T3_A1_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-contact-trace.csv":
        "04aedbcffbeb5bb57e6d4c79e5a9b94c58d7830c2ed1ec21476be04aa9cce6f6",
    T3_A1_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-gap-trace.csv":
        "68fea41cdf67aa694f02e00aaedeb5a64197836901c11a0d1b0deafda3b0fc59",
    T3_A2_ARCHIVE / "SHA256SUMS":
        "053344b2cf1676f6ae06ec3ae53a65ec3b7decd9e726839ed7fb94ed595a3df2",
    T3_A2_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery-results.csv":
        "ce881c922ad6df18ef92e076d7ab9ef953371c9e92a536e6e726f66046019ee4",
    T3_A2_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery-state.csv":
        "9ed40579a009b97c0a3d724f3d855b2928a0e5c2480c624bbef705a8eb9d7b10",
    T3_A2_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery-closures.csv":
        "0d05a529b3537c563e500e111a48ad33c2f87c8a73f9d9fc31b6d3795ff230cb",
    T3_A2_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery-contact-trace.csv":
        "bc0eb7b098de93eeea2eef533ad89758b1a98ec0db635d539d9f38358eb1eff6",
    T3_A2_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery-gap-trace.csv":
        "6734adbdfcb29cadcae7a1047db9b00a6479b426c44a25be576ad6615d0d5c62",
    T3_A4_ARCHIVE / "SHA256SUMS":
        "5f0fa30df3b7cf3e326e44671c30cd231e4c6d74b82059d9fd359fc14923ebfa",
    T3_A4_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery-results.csv":
        "b1d90a472cdb8686e25d1ac52d0523fcae6c97222e2c10ab87d85fb3c6455503",
    T3_A4_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery-state.csv":
        "ffaebb70c8d890a239a3d9941cb9265876906e4cb4364788a3f97e983258c1de",
    T3_A4_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery-closures.csv":
        "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    T3_A4_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery-contact-trace.csv":
        "c87c125f72cb0735aada6523bbf21f49ee3614672e1f128ae5292389a3356d97",
    T3_A4_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery-gap-trace.csv":
        "72c0b7f1eb8d2c670b536114ec6c5491da942f17ba5e85e732c012a120c7467d",
    T3_A5_ARCHIVE / "SHA256SUMS":
        "ef9e1c3957a9c2c30011d2f8c127737df53ab5a10b3f70bc1bab82b28c2ff03b",
    T3_A5_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt5-recovery-results.csv":
        "6deba25edc6d0f7cf32d95a2599853368d23dadda603ecb82fa323cb2f64a4f3",
    T3_A5_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt5-recovery-state.csv":
        "0de540fc4b23ad28704bd232860cf9a441d5fe5892da6ef71f37ddb739b5a11f",
    T3_A5_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt5-recovery-closures.csv":
        "bb78bc08ca146bb9efa31087a1f9e0e8e28affa20d04318c39205bb9ca0c08be",
    T3_A5_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt5-recovery-contact-trace.csv":
        "4c0c7f8c69a359045a337cf0dd98f41e53928bd7a2840911fa8bc30befa355d1",
    T3_A5_ARCHIVE / "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt5-recovery-gap-trace.csv":
        "c03f211bf5a7310d6f307a4a3867740849afb82d480a5c18db382e7a831f7b66",
}


@dataclass(frozen=True)
class Metric:
    rms: float
    maximum: float


@dataclass(frozen=True)
class Dataset:
    keys: tuple[tuple[int, int], ...]
    centers: np.ndarray
    raw_keys: tuple[tuple[int, int], ...]
    raw_centers: np.ndarray


@dataclass(frozen=True)
class R2Assessment:
    equal_base: Metric
    equal_candidate: Metric
    raw_base: Metric
    raw_candidate: Metric
    plus_base: float
    plus_candidate: float
    minus_base: float
    minus_candidate: float
    b0_base: float
    b0_candidate: float
    maximum_worsening: float
    maximum_worsening_pose: tuple[int, int]
    worsenings: dict[tuple[int, int], float]
    base_residuals: dict[tuple[int, int], np.ndarray]
    candidate_residuals: dict[tuple[int, int], np.ndarray]
    raw_offsets: dict[tuple[int, int], np.ndarray]
    centered_offsets: dict[tuple[int, int], np.ndarray]


@dataclass(frozen=True)
class FitAssessment:
    t4: Metric
    t3_equal: Metric
    t3_raw: Metric
    maximum_worsening: float
    maximum_worsening_pose: tuple[int, int]
    dense_maximum: float | None = None
    dense_pose: tuple[float, float] | None = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as stream:
        rows = list(csv.DictReader(stream))
    if not rows and "closures" not in path.name:
        raise AssessmentError(f"no data rows in {path}")
    return rows


def finite_number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise AssessmentError(f"invalid numeric field {field!r}") from exc
    if not math.isfinite(value):
        raise AssessmentError(f"non-finite numeric field {field!r}")
    return value


def exact_integer(row: dict[str, str], field: str) -> int:
    value = finite_number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9:
        raise AssessmentError(f"{field}={value}, expected an integer")
    return int(rounded)


def require_integer(
    row: dict[str, str], field: str, expected: int, context: str
) -> None:
    actual = exact_integer(row, field)
    if actual != expected:
        raise AssessmentError(
            f"{context}: {field}={actual}, expected {expected}"
        )


def require_number(
    row: dict[str, str],
    field: str,
    expected: float,
    context: str,
    *,
    tolerance: float = 1e-9,
) -> None:
    actual = finite_number(row, field)
    if abs(actual - expected) > tolerance:
        raise AssessmentError(
            f"{context}: {field}={actual}, expected {expected}"
        )


def canonical_pose(b_deg: float, c_deg: float) -> tuple[int, int]:
    b_value = int(round(b_deg))
    c_value = int(round(c_deg)) % 360
    c_error = abs((c_deg - c_value + 180.0) % 360.0 - 180.0)
    if abs(b_deg - b_value) > 0.01 or c_error > 0.01:
        raise AssessmentError(f"noncanonical pose B{b_deg} C{c_deg}")
    return b_value, c_value


def row_pose(row: dict[str, str]) -> tuple[int, int]:
    return canonical_pose(
        finite_number(row, "abs_b_deg"), finite_number(row, "abs_c_deg")
    )


def row_center(row: dict[str, str]) -> np.ndarray:
    return np.array(
        [finite_number(row, f"center_abs_{axis}_mm") for axis in AXES],
        dtype=float,
    )


def parse_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="ascii").splitlines(), start=1
    ):
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise AssessmentError(f"malformed seal line {path}:{line_number}")
        digest, name = parts
        if any(character not in "0123456789abcdef" for character in digest):
            raise AssessmentError(f"invalid seal digest {path}:{line_number}")
        if name in entries:
            raise AssessmentError(f"duplicate seal member {name!r} in {path}")
        entries[name] = digest
    return entries


def validate_hashes() -> None:
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256(path)
        if actual != expected:
            raise AssessmentError(
                f"SHA-256 changed for {path}: {actual}, expected {expected}"
            )

    archives = {path.parent for path in EXPECTED_SHA256 if path.name == "SHA256SUMS"}
    for archive in archives:
        entries = parse_manifest(archive / "SHA256SUMS")
        for path, expected in EXPECTED_SHA256.items():
            if path.parent != archive or path.name == "SHA256SUMS":
                continue
            if entries.get(path.name) != expected:
                raise AssessmentError(
                    f"{path.name} is not tied to the expected seal in {archive}"
                )


def expected_t3_poses() -> tuple[tuple[int, int], ...]:
    poses: list[tuple[int, int]] = []
    poses.extend((0, c_value) for c_value in (0, 90, 180, 270, 0))
    poses.extend((45, c_value) for c_value in (0, 90, 180, 270, 0))
    poses.extend((-45, c_value) for c_value in (0, 90, 180, 270, 0))
    poses.append((0, 0))
    poses.extend((90, c_value) for c_value in (0, 90, 180, 270, 0))
    poses.extend((-90, c_value) for c_value in (0, 90, 180, 270, 0))
    poses.extend((0, c_value) for c_value in (0, 90, 180, 270, 0))
    if len(poses) != 31:
        raise AssertionError("internal T3 pose count differs from 31")
    return tuple(poses)


def validate_t4() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    results = read_csv(T4_RESULTS)
    states = read_csv(T4_STATE)
    closures = read_csv(T4_CLOSURES)
    if (len(results), len(states), len(closures)) != (101, 101, 28):
        raise AssessmentError("T4 frozen row counts changed")
    sequences = [exact_integer(row, "sample_seq") for row in results]
    if sequences != list(range(1, 102)):
        raise AssessmentError("T4 result sequence changed")
    state_by_sequence = {
        exact_integer(row, "sample_seq"): row for row in states
    }
    if sorted(state_by_sequence) != list(range(1, 102)):
        raise AssessmentError("T4 state sequence changed")
    for row in results:
        sequence = exact_integer(row, "sample_seq")
        for field, expected in (
            ("campaign_id", T4_CAMPAIGN),
            ("stage_mode", T4_MODE),
            ("attempt_id", T4_ATTEMPT),
            ("live_tool_number", 4),
            ("contact_count", 4),
        ):
            if exact_integer(row, field) != expected:
                raise AssessmentError(f"T4 sequence {sequence}: {field} changed")
        state = state_by_sequence[sequence]
        if row_pose(row) != row_pose(state):
            raise AssessmentError(f"T4 sequence {sequence}: state pose changed")
    for row in closures:
        if exact_integer(row, "pass") != 1:
            raise AssessmentError("T4 closure pass changed")
        if finite_number(row, "closure_norm_mm") > 0.050000001:
            raise AssessmentError("T4 closure norm changed")
    return results, states


TRACE_IDENTITIES = tuple(
    (pass_id, contact_id)
    for pass_id in (1, 2)
    for contact_id in (1, 2, 3, 4)
)


def validate_t3_trace_common(
    row: dict[str, str], source: Source, sequence_field: str, context: str
) -> int:
    for field, expected in (
        ("campaign_id", T3_CAMPAIGN),
        ("stage_mode", source.mode),
        ("attempt_id", source.attempt),
    ):
        require_integer(row, field, expected, context)
    sequence = exact_integer(row, sequence_field)
    if sequence < 1 or sequence > len(expected_t3_poses()):
        raise AssessmentError(f"{context}: sequence {sequence} is outside 1-31")
    if row_pose(row) != expected_t3_poses()[sequence - 1]:
        raise AssessmentError(f"{context}: trace pose changed")
    return sequence


def trace_identity(row: dict[str, str]) -> tuple[int, int]:
    return exact_integer(row, "pass_id"), exact_integer(row, "contact_id")


def validate_accepted_trace_groups(
    source: Source,
    rows: Sequence[dict[str, str]],
    sequence_field: str,
    label: str,
) -> None:
    for sequence in source.sequences:
        identities = sorted(
            trace_identity(row)
            for row in rows
            if exact_integer(row, sequence_field) == sequence
        )
        if identities != sorted(TRACE_IDENTITIES):
            raise AssessmentError(
                f"T3 {source.label} sequence {sequence}: accepted {label} "
                "identity set changed"
            )


def validate_t3_contacts(
    source: Source, contacts: Sequence[dict[str, str]]
) -> None:
    accepted_sequences = set(source.sequences)
    seen_sequences: set[int] = set()
    terminal_rows: list[tuple[int, tuple[int, int]]] = []
    for row_number, row in enumerate(contacts, start=1):
        context = f"T3 {source.label} contact row {row_number}"
        sequence = validate_t3_trace_common(
            row, source, "global_seq", context
        )
        seen_sequences.add(sequence)
        identity = trace_identity(row)
        if identity not in TRACE_IDENTITIES:
            raise AssessmentError(f"{context}: contact identity changed")

        raw_delta = exact_integer(row, "raw_delta")
        mux_delta = exact_integer(row, "mux_delta")
        gated_delta = exact_integer(row, "gated_delta")
        repeat_raw = exact_integer(row, "repeat_raw_delta")
        repeat_mux = exact_integer(row, "repeat_mux_delta")
        repeat_gated = exact_integer(row, "repeat_gated_delta")
        extra_delta = exact_integer(row, "extra_raw_minus_gated_delta")
        terminal = exact_integer(row, "terminal_failure")

        if raw_delta != mux_delta or repeat_raw != repeat_mux:
            raise AssessmentError(f"{context}: raw/mux delta mismatch")
        if repeat_gated != 0:
            raise AssessmentError(f"{context}: gated repeat was not zero")
        if extra_delta != raw_delta + repeat_raw - gated_delta:
            raise AssessmentError(f"{context}: extra-pulse arithmetic changed")
        for field in ("burst_flag", "consistency_fault", "release_fault"):
            require_integer(row, field, 0, context)

        pre_raw = exact_integer(row, "pre_raw_count")
        pre_mux = exact_integer(row, "pre_mux_count")
        pre_gated = exact_integer(row, "pre_gated_count")
        post_raw = exact_integer(row, "post_raw_count")
        post_mux = exact_integer(row, "post_mux_count")
        post_gated = exact_integer(row, "post_gated_count")
        ready_raw = exact_integer(row, "ready_raw_count")
        ready_mux = exact_integer(row, "ready_mux_count")
        ready_gated = exact_integer(row, "ready_gated_count")
        if pre_raw != pre_mux or post_raw != post_mux or ready_raw != ready_mux:
            raise AssessmentError(f"{context}: raw/mux counters diverged")
        if (
            post_raw - pre_raw != raw_delta
            or post_mux - pre_mux != mux_delta
            or post_gated - pre_gated != gated_delta
            or ready_raw - post_raw != repeat_raw
            or ready_mux - post_mux != repeat_mux
            or ready_gated - post_gated != repeat_gated
        ):
            raise AssessmentError(f"{context}: contact counter arithmetic changed")

        if terminal == 0:
            for field in ("probe_result", "raw_delta", "mux_delta", "gated_delta"):
                require_integer(row, field, 1, context)
        elif terminal == 1:
            terminal_rows.append((sequence, identity))
            if source.label != "A1" or sequence != 15 or identity != (2, 3):
                raise AssessmentError(f"{context}: unexpected terminal contact")
            for field in ("probe_result", "raw_delta", "mux_delta", "gated_delta"):
                require_integer(row, field, 0, context)
            require_integer(row, "repeat_raw_delta", 1, context)
            require_integer(row, "repeat_mux_delta", 1, context)
        else:
            raise AssessmentError(f"{context}: terminal_failure is not binary")

    expected_sequences = accepted_sequences | ({15} if source.label == "A1" else set())
    if seen_sequences != expected_sequences:
        raise AssessmentError(f"T3 {source.label}: contact sequence set changed")
    expected_terminal = [(15, (2, 3))] if source.label == "A1" else []
    if terminal_rows != expected_terminal:
        raise AssessmentError(f"T3 {source.label}: terminal contact contract changed")
    validate_accepted_trace_groups(source, contacts, "global_seq", "contact")


def validate_t3_gaps(source: Source, gaps: Sequence[dict[str, str]]) -> None:
    accepted_sequences = set(source.sequences)
    seen_sequences: set[int] = set()
    initial_rows: list[tuple[int, tuple[int, int]]] = []
    burst_rows: list[tuple[int, tuple[int, int]]] = []
    for row_number, row in enumerate(gaps, start=1):
        context = f"T3 {source.label} gap row {row_number}"
        sequence = validate_t3_trace_common(
            row, source, "next_global_seq", context
        )
        seen_sequences.add(sequence)
        identity = trace_identity(row)
        if identity not in TRACE_IDENTITIES:
            raise AssessmentError(f"{context}: gap identity changed")

        gap_raw = exact_integer(row, "gap_raw_delta")
        gap_mux = exact_integer(row, "gap_mux_delta")
        gap_gated = exact_integer(row, "gap_gated_delta")
        prior_extra = exact_integer(row, "prior_contact_extra_delta")
        combined_extra = exact_integer(row, "combined_extra_delta")
        burst = exact_integer(row, "burst_flag")
        initial = exact_integer(row, "initial_baseline")
        require_integer(row, "consistency_fault", 0, context)
        if gap_raw != gap_mux or gap_gated != 0:
            raise AssessmentError(f"{context}: gap mux/gated contract changed")
        if combined_extra != gap_raw + prior_extra:
            raise AssessmentError(f"{context}: combined gap arithmetic changed")

        prior_raw = exact_integer(row, "prior_ready_raw_count")
        prior_mux = exact_integer(row, "prior_ready_mux_count")
        prior_gated = exact_integer(row, "prior_ready_gated_count")
        current_raw = exact_integer(row, "current_pre_raw_count")
        current_mux = exact_integer(row, "current_pre_mux_count")
        current_gated = exact_integer(row, "current_pre_gated_count")
        if prior_raw != prior_mux or current_raw != current_mux:
            raise AssessmentError(f"{context}: raw/mux gap counters diverged")
        if (
            current_raw - prior_raw != gap_raw
            or current_mux - prior_mux != gap_mux
            or current_gated - prior_gated != gap_gated
        ):
            raise AssessmentError(f"{context}: gap counter arithmetic changed")

        if initial == 1:
            initial_rows.append((sequence, identity))
            if gap_raw != 0 or prior_extra != 0 or combined_extra != 0:
                raise AssessmentError(f"{context}: initial baseline was not quiet")
        elif initial != 0:
            raise AssessmentError(f"{context}: initial_baseline is not binary")

        if burst == 1:
            burst_rows.append((sequence, identity))
            if (
                source.label != "A2"
                or sequence != 23
                or identity != (1, 1)
                or gap_raw != 4
                or prior_extra != 0
            ):
                raise AssessmentError(f"{context}: unexpected burst terminal row")
        elif burst != 0:
            raise AssessmentError(f"{context}: burst_flag is not binary")

    extra_sequences = (
        {15}
        if source.label == "A1"
        else ({23} if source.label == "A2" else set())
    )
    if seen_sequences != accepted_sequences | extra_sequences:
        raise AssessmentError(f"T3 {source.label}: gap sequence set changed")
    expected_initial = [(source.sequences[0], (1, 1))]
    if initial_rows != expected_initial:
        raise AssessmentError(f"T3 {source.label}: initial gap baseline changed")
    expected_burst = [(23, (1, 1))] if source.label == "A2" else []
    if burst_rows != expected_burst:
        raise AssessmentError(f"T3 {source.label}: burst terminal contract changed")
    validate_accepted_trace_groups(source, gaps, "next_global_seq", "gap")


def validate_t3_source(source: Source) -> list[dict[str, str]]:
    results = read_csv(source.path("results"))
    states = read_csv(source.path("state"))
    closures = read_csv(source.path("closures"))
    contacts = read_csv(source.path("contact-trace"))
    gaps = read_csv(source.path("gap-trace"))
    counts = (len(results), len(states), len(closures), len(contacts), len(gaps))
    expected_counts = (
        source.result_rows,
        source.result_rows,
        source.closure_rows,
        source.contact_rows,
        source.gap_rows,
    )
    if counts != expected_counts:
        raise AssessmentError(
            f"T3 {source.label} row counts changed: {counts}, expected {expected_counts}"
        )
    sequences = tuple(exact_integer(row, "sample_seq") for row in results)
    if sequences != source.sequences:
        raise AssessmentError(f"T3 {source.label} result sequence changed")
    state_by_sequence = {
        exact_integer(row, "sample_seq"): row for row in states
    }
    if tuple(sorted(state_by_sequence)) != source.sequences:
        raise AssessmentError(f"T3 {source.label} state sequence changed")
    expected_poses = expected_t3_poses()
    for row in results:
        sequence = exact_integer(row, "sample_seq")
        for field, expected in (
            ("campaign_id", T3_CAMPAIGN),
            ("stage_mode", source.mode),
            ("attempt_id", source.attempt),
            ("live_tool_number", T3_TOOL),
            ("contact_count", 4),
        ):
            if exact_integer(row, field) != expected:
                raise AssessmentError(
                    f"T3 {source.label} sequence {sequence}: {field} changed"
                )
        if abs(finite_number(row, "expected_tool_length_mm") - T3_TOOL_LENGTH) > 1e-9:
            raise AssessmentError(
                f"T3 {source.label} sequence {sequence}: tool length changed"
            )
        if row_pose(row) != expected_poses[sequence - 1]:
            raise AssessmentError(
                f"T3 {source.label} sequence {sequence}: pose changed"
            )
        state = state_by_sequence[sequence]
        context = f"T3 {source.label} sequence {sequence} accepted state"
        if row_pose(state) != row_pose(row):
            raise AssessmentError(
                f"T3 {source.label} sequence {sequence}: state pose changed"
            )
        for field, expected in (
            ("campaign_id", T3_CAMPAIGN),
            ("stage_mode", source.mode),
            ("attempt_id", source.attempt),
            ("sample_seq", sequence),
            ("persistent_correction_enabled", 1),
            ("tcpc_enabled", 1),
            ("twp_active", 0),
            ("twp_motion_enabled", 0),
            ("twp_valid", 0),
            ("b_ssi_invalid", 0),
            ("c_ssi_invalid", 0),
        ):
            require_integer(state, field, expected, context)
        for field in (
            "motion_tooloffset_z_mm",
            "halui_tool_length_offset_z_mm",
            "kins_active_tool_offset_z_mm",
        ):
            require_number(state, field, T3_TOOL_LENGTH, context)
        for joint in range(3):
            require_number(
                state,
                f"joint_{joint}_motor_following_error_fb_minus_cmd_mm",
                0.0,
                context,
            )
        for axis in ("b", "c"):
            command = finite_number(state, f"joint_{axis}_cmd_deg")
            feedback = finite_number(state, f"joint_{axis}_fb_deg")
            if abs(command - feedback) > 0.005:
                raise AssessmentError(f"{context}: {axis.upper()} feedback changed")

    sequence_set = set(source.sequences)
    for row_number, row in enumerate(closures, start=1):
        context = f"T3 {source.label} closure row {row_number}"
        for field, expected in (
            ("campaign_id", T3_CAMPAIGN),
            ("stage_mode", source.mode),
            ("attempt_id", source.attempt),
            ("pass", 1),
        ):
            require_integer(row, field, expected, context)
        open_sequence = exact_integer(row, "open_sample_seq")
        close_sequence = exact_integer(row, "close_sample_seq")
        if open_sequence not in sequence_set or close_sequence not in sequence_set:
            raise AssessmentError(f"{context}: closure sequence left source")
        if (
            expected_poses[open_sequence - 1] != expected_poses[close_sequence - 1]
            or row_pose(row) != expected_poses[open_sequence - 1]
        ):
            raise AssessmentError(f"{context}: closure pose changed")
        require_number(row, "limit_mm", CLOSURE_LIMIT_MM, context)
        norm = finite_number(row, "closure_norm_mm")
        components = np.array(
            [finite_number(row, f"closure_d{axis}_mm") for axis in AXES]
        )
        if norm > CLOSURE_LIMIT_MM + 1e-9:
            raise AssessmentError(f"{context}: closure exceeded 0.050 mm")
        if abs(np.linalg.norm(components) - norm) > 1.5e-6:
            raise AssessmentError(f"{context}: closure norm arithmetic changed")

    validate_t3_contacts(source, contacts)
    validate_t3_gaps(source, gaps)
    return results


def unique_means(
    raw_keys: Sequence[tuple[int, int]], raw_centers: np.ndarray
) -> tuple[tuple[tuple[int, int], ...], np.ndarray]:
    order: list[tuple[int, int]] = []
    grouped: dict[tuple[int, int], list[np.ndarray]] = {}
    for key, center in zip(raw_keys, raw_centers):
        if key not in grouped:
            order.append(key)
            grouped[key] = []
        grouped[key].append(center)
    means = np.array([np.mean(grouped[key], axis=0) for key in order])
    return tuple(order), means


def build_t4_dataset(rows: Sequence[dict[str, str]]) -> Dataset:
    raw_keys = tuple(row_pose(row) for row in rows)
    raw_centers = np.array([row_center(row) for row in rows])
    keys, centers = unique_means(raw_keys, raw_centers)
    if len(keys) != 76:
        raise AssessmentError(f"T4 unique-pose count is {len(keys)}, expected 76")
    return Dataset(keys, centers, raw_keys, raw_centers)


def build_t3_dataset(source_rows: Iterable[Sequence[dict[str, str]]]) -> Dataset:
    rows = [row for source in source_rows for row in source]
    rows.sort(key=lambda row: exact_integer(row, "sample_seq"))
    if [exact_integer(row, "sample_seq") for row in rows] != list(range(1, 32)):
        raise AssessmentError("T3 composite sequence differs from 1-31")
    raw_keys = tuple(row_pose(row) for row in rows)
    raw_centers = np.array([row_center(row) for row in rows])
    keys, centers = unique_means(raw_keys, raw_centers)
    if len(keys) != 20:
        raise AssessmentError(f"T3 unique-pose count is {len(keys)}, expected 20")
    return Dataset(keys, centers, raw_keys, raw_centers)


def centered(values: np.ndarray) -> np.ndarray:
    return values - np.mean(values, axis=0)


def metric(values: np.ndarray) -> Metric:
    norms = np.linalg.norm(centered(values), axis=1)
    return Metric(float(math.sqrt(np.mean(norms * norms))), float(np.max(norms)))


def residual_metric(residuals: np.ndarray) -> Metric:
    norms = np.linalg.norm(residuals, axis=1)
    return Metric(float(math.sqrt(np.mean(norms * norms))), float(np.max(norms)))


def subgroup_rms(residuals: np.ndarray, indices: Sequence[int]) -> float:
    norms = np.linalg.norm(residuals[list(indices)], axis=1)
    return float(math.sqrt(np.mean(norms * norms)))


def basis_values(b_deg: np.ndarray, c_deg: np.ndarray) -> dict[str, np.ndarray]:
    b_rad = np.radians(b_deg + B_ZERO_DEG)
    c_rad = np.radians(c_deg + C_ZERO_DEG)
    c_reference = math.radians(C_ZERO_DEG)
    sin_b = np.sin(b_rad)
    omc_b = 1.0 - np.cos(b_rad)
    sin_c = np.sin(c_rad)
    cos_c = np.cos(c_rad)
    mid_b = np.sin(2.0 * b_rad) ** 2
    return {
        "c_cos": cos_c - math.cos(c_reference),
        "c_sin": sin_c - math.sin(c_reference),
        "c_cos2": np.cos(2.0 * c_rad) - math.cos(2.0 * c_reference),
        "c_sin2": np.sin(2.0 * c_rad) - math.sin(2.0 * c_reference),
        "b_sin": sin_b,
        "b_omc": omc_b,
        "b_sin2": np.sin(2.0 * b_rad),
        "bc_sinb_sinc": sin_b * sin_c,
        "bc_omcb_sinc": omc_b * sin_c,
        "bc_omcb_sin2c": omc_b * sin_c * sin_c,
        "bc_sinb_cosc": sin_b * cos_c,
        "bc_omcb_cosc": omc_b * cos_c,
        "bc_sinb_cos2c": sin_b * np.cos(2.0 * c_rad),
        "bmid_base": mid_b,
        "bmid_cosc": mid_b * cos_c,
        "bmid_sinc": mid_b * sin_c,
        "bmid_cos2c": mid_b * np.cos(2.0 * c_rad),
    }


def feature_matrix(keys: Sequence[tuple[int, int]]) -> np.ndarray:
    b_values = np.array([key[0] for key in keys], dtype=float)
    c_values = np.array([key[1] for key in keys], dtype=float)
    values = basis_values(b_values, c_values)
    return np.column_stack([values[term] for term in ADMISSIBLE_TERMS])


def term_indices(terms: Sequence[str]) -> tuple[int, ...]:
    indices = tuple(ADMISSIBLE_TERMS.index(term) for term in terms)
    if len(set(indices)) != len(indices):
        raise AssessmentError("duplicate model term")
    return indices


def load_r2_deltas() -> dict[str, np.ndarray]:
    rows = read_csv(R2_PINS)
    if len(rows) != len(ADMISSIBLE_TERMS) * len(AXES):
        raise AssessmentError("R2 pin row count changed")
    output = {term: np.zeros(3) for term in ADMISSIBLE_TERMS}
    seen: set[tuple[str, str]] = set()
    selected: set[str] = set()
    for row in rows:
        term = row.get("basis_term", "")
        axis = row.get("axis", "")
        if term not in output or axis not in AXES or (term, axis) in seen:
            raise AssessmentError("R2 pin identity changed")
        seen.add((term, axis))
        delta = finite_number(row, "delta_mm")
        current = finite_number(row, "current_mm")
        total = finite_number(row, "predicted_total_mm")
        if abs(current + delta - total) > 1.1e-9:
            raise AssessmentError(f"R2 pin arithmetic changed for {term}.{axis}")
        output[term][AXES.index(axis)] = delta
        if exact_integer(row, "selected") == 1:
            selected.add(term)
    if selected != set(R2_TERMS):
        raise AssessmentError("R2 selected-term identity changed")
    if any(np.linalg.norm(output[term]) > 1e-12 for term in set(ADMISSIBLE_TERMS) - selected):
        raise AssessmentError("R2 nonselected coefficient became nonzero")
    return output


def coefficient_matrix(
    coefficients: dict[str, np.ndarray], terms: Sequence[str]
) -> np.ndarray:
    return np.array([coefficients[term] for term in terms])


def offsets_for_keys(
    keys: Sequence[tuple[int, int]],
    terms: Sequence[str],
    coefficients: np.ndarray,
) -> np.ndarray:
    indices = term_indices(terms)
    return feature_matrix(keys)[:, indices] @ coefficients


def assess_r2(
    t3: Dataset,
    residual_offsets: dict[tuple[int, int], np.ndarray],
) -> R2Assessment:
    # Score with the archived residual-map values. The separately rounded pin
    # coefficients remain the source for term attribution below.
    equal_offsets = np.array([residual_offsets[key] for key in t3.keys])
    raw_offsets = np.array([residual_offsets[key] for key in t3.raw_keys])
    equal_candidate_values = t3.centers + equal_offsets
    raw_candidate_values = t3.raw_centers + raw_offsets
    base_residual = centered(t3.centers)
    candidate_residual = centered(equal_candidate_values)
    base_norm = np.linalg.norm(base_residual, axis=1)
    candidate_norm = np.linalg.norm(candidate_residual, axis=1)
    worsening = candidate_norm - base_norm
    plus = [index for index, key in enumerate(t3.keys) if key[0] > 0]
    minus = [index for index, key in enumerate(t3.keys) if key[0] < 0]
    b_zero = [index for index, key in enumerate(t3.keys) if key[0] == 0]
    worst_index = int(np.argmax(worsening))
    return R2Assessment(
        metric(t3.centers),
        metric(equal_candidate_values),
        metric(t3.raw_centers),
        metric(raw_candidate_values),
        subgroup_rms(base_residual, plus),
        subgroup_rms(candidate_residual, plus),
        subgroup_rms(base_residual, minus),
        subgroup_rms(candidate_residual, minus),
        subgroup_rms(base_residual, b_zero),
        subgroup_rms(candidate_residual, b_zero),
        float(worsening[worst_index]),
        t3.keys[worst_index],
        {key: float(value) for key, value in zip(t3.keys, worsening)},
        {key: value for key, value in zip(t3.keys, base_residual)},
        {key: value for key, value in zip(t3.keys, candidate_residual)},
        {key: value for key, value in zip(t3.keys, equal_offsets)},
        {
            key: value
            for key, value in zip(t3.keys, equal_offsets - np.mean(equal_offsets, axis=0))
        },
    )


def fit_t4_ridge(
    t4: Dataset, terms: Sequence[str], ridge_lambda: float
) -> np.ndarray:
    indices = term_indices(terms)
    features = feature_matrix(t4.keys)[:, indices]
    feature_mean = np.mean(features, axis=0)
    feature_scale = np.std(features, axis=0)
    if np.any(feature_scale <= 1e-12):
        raise AssessmentError("unidentifiable T4 ridge feature")
    standardized = (features - feature_mean) / feature_scale
    response = centered(t4.centers)
    gram = standardized.T @ standardized
    right = standardized.T @ response
    fitted_center = np.linalg.solve(
        gram + ridge_lambda * np.eye(len(terms)), right
    )
    return -fitted_center / feature_scale[:, None]


def assess_coefficients(
    t4: Dataset,
    t3: Dataset,
    terms: Sequence[str],
    coefficients: np.ndarray,
    *,
    dense: bool = False,
) -> FitAssessment:
    t4_candidate = t4.centers + offsets_for_keys(t4.keys, terms, coefficients)
    t3_candidate = t3.centers + offsets_for_keys(t3.keys, terms, coefficients)
    t3_raw_candidate = t3.raw_centers + offsets_for_keys(
        t3.raw_keys, terms, coefficients
    )
    base_norms = np.linalg.norm(centered(t3.centers), axis=1)
    candidate_norms = np.linalg.norm(centered(t3_candidate), axis=1)
    worsening = candidate_norms - base_norms
    worst_index = int(np.argmax(worsening))
    dense_maximum: float | None = None
    dense_pose: tuple[float, float] | None = None
    if dense:
        dense_maximum, dense_pose = dense_correction_maximum(terms, coefficients)
    return FitAssessment(
        metric(t4_candidate),
        metric(t3_candidate),
        metric(t3_raw_candidate),
        float(worsening[worst_index]),
        t3.keys[worst_index],
        dense_maximum,
        dense_pose,
    )


def fit_equal_tool_joint_development(
    t4: Dataset, t3: Dataset, terms: Sequence[str], ridge_lambda: float
) -> np.ndarray:
    """Fit an equal-total-weight, separately centered two-tool illustration."""
    indices = term_indices(terms)
    t4_features = feature_matrix(t4.keys)[:, indices]
    t3_features = feature_matrix(t3.keys)[:, indices]
    t4_mean = np.mean(t4_features, axis=0)
    scale = np.std(t4_features, axis=0)
    if np.any(scale <= 1e-12):
        raise AssessmentError("unidentifiable joint-development feature")
    t4_standardized = (t4_features - t4_mean) / scale
    t3_standardized = (t3_features - np.mean(t3_features, axis=0)) / scale
    # Each tool has equal total weight despite 76 versus 20 unique poses.
    t3_row_scale = math.sqrt(len(t4.keys) / len(t3.keys))
    design = np.vstack([t4_standardized, t3_row_scale * t3_standardized])
    response = np.vstack(
        [centered(t4.centers), t3_row_scale * centered(t3.centers)]
    )
    fitted_center = np.linalg.solve(
        design.T @ design + ridge_lambda * np.eye(len(terms)),
        design.T @ response,
    )
    return -fitted_center / scale[:, None]


def dense_correction_maximum(
    terms: Sequence[str], coefficients: np.ndarray
) -> tuple[float, tuple[float, float]]:
    """Audit B[-100,+100], complete C, on a deterministic 0.25-degree grid."""
    maximum = -1.0
    maximum_pose = (float("nan"), float("nan"))
    c_values = np.arange(0.0, 360.0 + 0.125, 0.25)
    indices = term_indices(terms)
    for b_value in np.arange(-100.0, 100.0 + 0.125, 0.25):
        b_values = np.full_like(c_values, b_value)
        values = basis_values(b_values, c_values)
        design = np.column_stack([values[term] for term in ADMISSIBLE_TERMS])
        offsets = design[:, indices] @ coefficients
        norms = np.linalg.norm(offsets, axis=1)
        index = int(np.argmax(norms))
        if norms[index] > maximum:
            maximum = float(norms[index])
            maximum_pose = (float(b_value), float(c_values[index] % 360.0))
    return maximum, maximum_pose


def matching_t4_dataset(t4: Dataset, t3: Dataset) -> Dataset:
    queues: dict[tuple[int, int], list[np.ndarray]] = {}
    for key, center in zip(t4.raw_keys, t4.raw_centers):
        queues.setdefault(key, []).append(center)
    used: dict[tuple[int, int], int] = {}
    selected: list[np.ndarray] = []
    for key in t3.raw_keys:
        index = used.get(key, 0)
        if key not in queues or index >= len(queues[key]):
            raise AssessmentError(f"T4 lacks matching occurrence for {key}")
        selected.append(queues[key][index])
        used[key] = index + 1
    raw_centers = np.array(selected)
    keys, centers = unique_means(t3.raw_keys, raw_centers)
    if keys != t3.keys:
        raise AssessmentError("T3/T4 common-grid order changed")
    return Dataset(keys, centers, t3.raw_keys, raw_centers)


def mismatch_metrics(t3: Dataset, matching_t4: Dataset) -> tuple[Metric, Metric]:
    mismatch = centered(t3.centers) - centered(matching_t4.centers)
    mismatch_metric = residual_metric(mismatch)
    lower_bound = Metric(mismatch_metric.rms / 2.0, mismatch_metric.maximum / 2.0)
    return mismatch_metric, lower_bound


def validate_residual_map(
    keys: Sequence[tuple[int, int]], r2_deltas: dict[str, np.ndarray]
) -> dict[tuple[int, int], np.ndarray]:
    wanted = set(keys)
    found: dict[tuple[int, int], np.ndarray] = {}
    for row in read_csv(R2_RESIDUALS):
        key = row_pose(row)
        if key not in wanted:
            continue
        value = np.array(
            [finite_number(row, f"candidate_delta_{axis}_mm") for axis in AXES]
        )
        if key in found and np.linalg.norm(found[key] - value) > 1e-9:
            raise AssessmentError(f"R2 residual delta differs at duplicate {key}")
        found[key] = value
    calculated = offsets_for_keys(
        keys, R2_TERMS, coefficient_matrix(r2_deltas, R2_TERMS)
    )
    for key, value in zip(keys, calculated):
        # Both archived CSVs intentionally publish nine decimal places.  The
        # vector reconstructed from individually rounded pin coefficients can
        # differ from the independently rounded residual vector by a few nm.
        if key not in found or np.linalg.norm(found[key] - value) > 3e-9:
            raise AssessmentError(f"R2 pin/residual mapping changed at {key}")
    return found


def assert_close(actual: float, expected: float, tolerance: float, label: str) -> None:
    if abs(actual - expected) > tolerance:
        raise AssessmentError(
            f"{label} changed: {actual:.12f}, expected {expected:.12f}"
        )


def calculate() -> tuple[
    Dataset,
    Dataset,
    Dataset,
    dict[str, np.ndarray],
    R2Assessment,
    FitAssessment,
    FitAssessment,
    FitAssessment,
    Metric,
    Metric,
]:
    validate_hashes()
    t4_rows, _ = validate_t4()
    t3_rows = [validate_t3_source(source) for source in T3_SOURCES]
    t4 = build_t4_dataset(t4_rows)
    t3 = build_t3_dataset(t3_rows)
    matching_t4 = matching_t4_dataset(t4, t3)
    r2_deltas = load_r2_deltas()
    residual_offsets = validate_residual_map(t3.keys, r2_deltas)
    r2 = assess_r2(t3, residual_offsets)

    stable7_coefficients = fit_t4_ridge(t4, STABLE7_TERMS, RIDGE_LAMBDA)
    stable7 = assess_coefficients(
        t4, t3, STABLE7_TERMS, stable7_coefficients
    )
    joint_coefficients = fit_equal_tool_joint_development(
        t4, t3, R2_TERMS, RIDGE_LAMBDA
    )
    joint = assess_coefficients(
        t4, t3, R2_TERMS, joint_coefficients, dense=True
    )
    averaged_loss_coefficients = fit_equal_tool_joint_development(
        t4, t3, R2_TERMS, AVERAGED_LOSS_SENSITIVITY_LAMBDA
    )
    averaged_loss_joint = assess_coefficients(
        t4, t3, R2_TERMS, averaged_loss_coefficients, dense=True
    )
    mismatch, lower_bound = mismatch_metrics(t3, matching_t4)

    # A common correction must cancel identically from the centered mismatch.
    common_offsets = offsets_for_keys(
        t3.keys, R2_TERMS, coefficient_matrix(r2_deltas, R2_TERMS)
    )
    corrected_mismatch = centered(t3.centers + common_offsets) - centered(
        matching_t4.centers + common_offsets
    )
    if np.max(
        np.abs(
            corrected_mismatch
            - (centered(t3.centers) - centered(matching_t4.centers))
        )
    ) > 1e-12:
        raise AssessmentError("common-correction mismatch invariance failed")

    return (
        t4,
        t3,
        matching_t4,
        r2_deltas,
        r2,
        stable7,
        joint,
        averaged_loss_joint,
        mismatch,
        lower_bound,
    )


def self_test() -> None:
    (
        t4,
        t3,
        _matching_t4,
        _r2_deltas,
        r2,
        stable7,
        joint,
        averaged_loss_joint,
        mismatch,
        lower_bound,
    ) = calculate()
    if (len(t4.keys), len(t4.raw_keys), len(t3.keys), len(t3.raw_keys)) != (
        76,
        101,
        20,
        31,
    ):
        raise AssessmentError("dataset dimensions changed")

    checks = (
        (r2.equal_base.rms, 0.251154900, "R2 T3 equal baseline RMS"),
        (r2.equal_base.maximum, 0.617559442, "R2 T3 equal baseline max"),
        (r2.equal_candidate.rms, 0.148716274, "R2 T3 equal candidate RMS"),
        (r2.equal_candidate.maximum, 0.328314143, "R2 T3 equal candidate max"),
        (r2.raw_candidate.rms, 0.149044164, "R2 T3 raw candidate RMS"),
        (r2.raw_candidate.maximum, 0.352449968, "R2 T3 raw candidate max"),
        (r2.maximum_worsening, 0.119218671, "R2 maximum worsening"),
        (r2.worsenings[(90, 270)], 0.078338770, "R2 B+90/C270 worsening"),
        (stable7.t4.rms, 0.111474, "stable7 T4 RMS"),
        (stable7.t4.maximum, 0.288058, "stable7 T4 max"),
        (stable7.t3_equal.rms, 0.151898, "stable7 T3 RMS"),
        (stable7.t3_equal.maximum, 0.352274, "stable7 T3 max"),
        (stable7.maximum_worsening, 0.069992, "stable7 maximum worsening"),
        (joint.t4.rms, 0.106656305, "joint T4 RMS"),
        (joint.t4.maximum, 0.247541359, "joint T4 max"),
        (joint.t3_equal.rms, 0.117685732, "joint T3 equal RMS"),
        (joint.t3_equal.maximum, 0.268980083, "joint T3 equal max"),
        (joint.t3_raw.rms, 0.124315035, "joint T3 raw RMS"),
        (joint.t3_raw.maximum, 0.291520953, "joint T3 raw max"),
        (joint.maximum_worsening, 0.042816641, "joint maximum worsening"),
        (joint.dense_maximum or float("nan"), 0.695646358, "joint dense maximum"),
        (averaged_loss_joint.t4.rms, 0.114060555, "averaged-loss T4 RMS"),
        (averaged_loss_joint.t4.maximum, 0.261638021, "averaged-loss T4 max"),
        (averaged_loss_joint.t3_equal.rms, 0.121013881, "averaged-loss T3 equal RMS"),
        (averaged_loss_joint.t3_equal.maximum, 0.275411863, "averaged-loss T3 equal max"),
        (averaged_loss_joint.t3_raw.rms, 0.126287231, "averaged-loss T3 raw RMS"),
        (averaged_loss_joint.t3_raw.maximum, 0.297832544, "averaged-loss T3 raw max"),
        (averaged_loss_joint.maximum_worsening, 0.037260763, "averaged-loss maximum worsening"),
        (
            averaged_loss_joint.dense_maximum or float("nan"),
            0.632943586,
            "averaged-loss dense maximum",
        ),
        (mismatch.rms, 0.164423503, "T3/T4 mismatch RMS"),
        (mismatch.maximum, 0.264629483, "T3/T4 mismatch max"),
        (lower_bound.rms, 0.082211752, "common-surface RMS lower bound"),
        (lower_bound.maximum, 0.132314742, "common-surface max lower bound"),
    )
    for actual, expected, label in checks:
        assert_close(actual, expected, 1.5e-6, label)
    if r2.maximum_worsening_pose != (90, 0):
        raise AssessmentError("R2 worst-worsening pose changed")
    if stable7.maximum_worsening_pose != (90, 0):
        raise AssessmentError("stable7 worst-worsening pose changed")
    if joint.maximum_worsening_pose != (90, 0):
        raise AssessmentError("joint worst-worsening pose changed")
    if averaged_loss_joint.maximum_worsening_pose != (90, 0):
        raise AssessmentError("averaged-loss worst-worsening pose changed")
    if joint.dense_pose != (-100.0, 272.0):
        raise AssessmentError(f"joint dense-maximum pose changed: {joint.dense_pose}")
    if averaged_loss_joint.dense_pose != (-100.0, 272.0):
        raise AssessmentError(
            f"averaged-loss dense-maximum pose changed: {averaged_loss_joint.dense_pose}"
        )
    if AVERAGED_LOSS_SENSITIVITY_LAMBDA != 2.0 * RIDGE_LAMBDA:
        raise AssessmentError("averaged-loss lambda scaling changed")


def vector_text(vector: np.ndarray) -> str:
    return ", ".join(f"{value:+.6f}" for value in vector)


def pose_text(pose: tuple[int, int]) -> str:
    return f"B{pose[0]:+d}/C{pose[1]:d}"


def direct_contribution_rows(
    pose: tuple[int, int], r2_deltas: dict[str, np.ndarray]
) -> list[str]:
    values = basis_values(
        np.array([float(pose[0])]), np.array([float(pose[1])])
    )
    rows: list[str] = []
    for term in R2_TERMS:
        basis = float(values[term][0])
        contribution = basis * r2_deltas[term]
        if np.linalg.norm(contribution) < 1e-6:
            continue
        rows.append(
            f"| `{term}` | `{basis:+.9f}` | `{vector_text(contribution)}` | "
            f"`{np.linalg.norm(contribution):.6f}` |"
        )
    return rows


def report_text() -> str:
    (
        _t4,
        _t3,
        _matching_t4,
        r2_deltas,
        r2,
        stable7,
        joint,
        averaged_loss_joint,
        mismatch,
        lower_bound,
    ) = calculate()
    script_hash = sha256(Path(__file__).resolve())
    b90_c0 = (90, 0)
    b90_c270 = (90, 270)
    plus_improvement = 1.0 - r2.plus_candidate / r2.plus_base
    minus_improvement = 1.0 - r2.minus_candidate / r2.minus_base
    b0_change = r2.b0_candidate - r2.b0_base

    lines = [
        "# TCPC R3 Offline Feasibility Assessment",
        "",
        "## Decision",
        "",
        "`NO R3 COEFFICIENTS RELEASED`",
        "",
        "The existing evidence diagnoses a real T3/T4 transfer conflict and shows",
        "that a mathematical compromise exists. It does not support a calibration",
        "release. The four-source T3 composite is development-only evidence, not an",
        "independent or same-acquisition holdout. A future R3 must be frozen before",
        "fresh uninterrupted T4 and T3 validation runs.",
        "",
        "The preferred exploratory path can proceed without another machine run:",
        "keep T4 as the primary fit evidence and use the current T3 composite only",
        "as noisy development compatibility evidence. Because that consumes the T3",
        "responses, only a fresh T3 run may accept the frozen result. A clean T3",
        "baseline is required before fitting only if a formal equal-tool joint",
        "objective is chosen.",
        "",
        "This report is offline-only. The generator imports neither LinuxCNC nor HAL",
        "and cannot write a pin, overlay, INI, tool table, or live configuration.",
        "",
        "## Frozen Evidence",
        "",
        "- T4 training: campaign `2026082404`, mode `23`, attempt `1`; `101` raw",
        "  rows collapsed to `76` equal-weight poses; `28` strict closures.",
        "- T3 development composite: A1 sequences `1-14`, A2 `15-22`, A4 `23`,",
        "  and A5 `24-31`; `31` raw rows collapsed to `20` equal-weight poses.",
        "- T3 source-local closures: `4`; this does not satisfy the formal",
        "  same-acquisition `31 / 31 / 14` contract.",
        "- Every logged T3 closure passes `0.050 mm`. Every accepted source row",
        "  satisfies the logged TCPC, SSI-valid, T3/tool-length, three-way TLO,",
        "  exact gated-contact, zero gated-repeat, and zero gated-gap contracts.",
        "  The A1 no-touch and A2 gap-burst terminal forensic rows are checked",
        "  separately and are never promoted into accepted result rows.",
        "- Every calculation input is tied to its archive seal and independently",
        "  checked against the SHA-256 values embedded in the generator.",
        "",
        "| evidence | SHA-256 |",
        "| --- | --- |",
        f"| T4/R2 archive seal | `{EXPECTED_SHA256[T4_ARCHIVE / 'SHA256SUMS']}` |",
        f"| T4 primary results | `{EXPECTED_SHA256[T4_RESULTS]}` |",
        f"| R2 pin audit | `{EXPECTED_SHA256[R2_PINS]}` |",
        f"| R2 residual map | `{EXPECTED_SHA256[R2_RESIDUALS]}` |",
        f"| T3 A1 archive seal | `{EXPECTED_SHA256[T3_A1_ARCHIVE / 'SHA256SUMS']}` |",
        f"| T3 A2 archive seal | `{EXPECTED_SHA256[T3_A2_ARCHIVE / 'SHA256SUMS']}` |",
        f"| T3 A4 archive seal | `{EXPECTED_SHA256[T3_A4_ARCHIVE / 'SHA256SUMS']}` |",
        f"| T3 A5 archive seal | `{EXPECTED_SHA256[T3_A5_ARCHIVE / 'SHA256SUMS']}` |",
        f"| assessment generator | `{script_hash}` |",
        "",
        "## R2 T3 Failure",
        "",
        "| frozen calculation | result | limit | status |",
        "| --- | ---: | ---: | --- |",
        f"| equal-20 RMS | `{r2.equal_candidate.rms:.9f}` | `0.120000000` | `FAIL` |",
        f"| equal-20 maximum | `{r2.equal_candidate.maximum:.9f}` | `0.280000000` | `FAIL` |",
        f"| raw-31 RMS | `{r2.raw_candidate.rms:.9f}` | `0.120000000` | `FAIL` |",
        f"| raw-31 maximum | `{r2.raw_candidate.maximum:.9f}` | `0.280000000` | `FAIL` |",
        f"| maximum pose worsening | `{r2.maximum_worsening:.9f}` | `0.075000000` | `FAIL` |",
        "",
        f"Equal-20 improves from `{r2.equal_base.rms:.9f} / {r2.equal_base.maximum:.9f}`",
        f"to `{r2.equal_candidate.rms:.9f} / {r2.equal_candidate.maximum:.9f} mm`, but",
        "the remaining positive-high-B field controls all three failed gates. Raw",
        f"sequence 19 at B+90/C180 is the `{r2.raw_candidate.maximum:.9f} mm` maximum.",
        "",
        f"- positive-B RMS: `{r2.plus_base:.9f} -> {r2.plus_candidate:.9f} mm`",
        f"  (`{plus_improvement * 100.0:.3f}%` improvement)",
        f"- negative-B RMS: `{r2.minus_base:.9f} -> {r2.minus_candidate:.9f} mm`",
        f"  (`{minus_improvement * 100.0:.3f}%` improvement)",
        f"- B0 RMS: `{r2.b0_base:.9f} -> {r2.b0_candidate:.9f} mm`",
        f"  (change `{b0_change:+.9f} mm`)",
        f"- B+90/C0: `{np.linalg.norm(r2.base_residuals[b90_c0]):.9f} -> "
        f"{np.linalg.norm(r2.candidate_residuals[b90_c0]):.9f} mm`, worsening",
        f"  `{r2.worsenings[b90_c0]:+.9f} mm`",
        f"- B+90/C270: `{np.linalg.norm(r2.base_residuals[b90_c270]):.9f} -> "
        f"{np.linalg.norm(r2.candidate_residuals[b90_c270]):.9f} mm`, worsening",
        f"  `{r2.worsenings[b90_c270]:+.9f} mm`",
        "",
        "## B+90 Attribution",
        "",
        f"At B+90/C0 the direct R2 correction is `[{vector_text(r2.raw_offsets[b90_c0])}]`",
        f"mm. Global centering changes the scored correction to",
        f"`[{vector_text(r2.centered_offsets[b90_c0])}]` mm, which aligns with the",
        f"baseline residual `[{vector_text(r2.base_residuals[b90_c0])}]` and increases",
        "its norm. The direct terms are:",
        "",
        "| term | basis value | direct XYZ mm | norm mm |",
        "| --- | ---: | ---: | ---: |",
        *direct_contribution_rows(b90_c0, r2_deltas),
        "",
        "`b_sin.z` is the dominant direct C0 component. The unstable",
        "`bc_sinb_cos2c` X/Y vector reinforces it. `c_cos` is exactly zero at C0;",
        "any apparent C0 effect from that term in a centered attribution is only a",
        "change of the global reference center.",
        "",
        f"At B+90/C270 the direct R2 correction is",
        f"`[{vector_text(r2.raw_offsets[b90_c270])}]` mm; the scored centered correction",
        f"is `[{vector_text(r2.centered_offsets[b90_c270])}]` mm:",
        "",
        "| term | basis value | direct XYZ mm | norm mm |",
        "| --- | ---: | ---: | ---: |",
        *direct_contribution_rows(b90_c270, r2_deltas),
        "",
        "The positive X correction is mainly `bc_sinb_sinc`,",
        "`bc_sinb_cos2c`, and `b_sin`. The Y result is a large cancellation between",
        "the positive `bc_omcb_sin2c.y` contribution and negative",
        "`bc_sinb_sinc.y`, `c_cos.y`, and `bc_sinb_cos2c.y` contributions.",
        "`b_sin2` and every `bmid_*` basis are zero at B90 and cannot directly cure",
        "either endpoint.",
        "",
        "## Common-Surface Limit",
        "",
        f"The centered T3-minus-T4 common-grid mismatch is `{mismatch.rms:.9f} /",
        f"{mismatch.maximum:.9f} mm` RMS/maximum. Adding any identical pose correction",
        "to both tools cancels exactly from this mismatch. A completely unrestricted",
        "shared pose surface could at best split the difference between the tools,",
        f"giving the theoretical equal-tool lower bound `{lower_bound.rms:.9f} /",
        f"{lower_bound.maximum:.9f} mm`. A common R3 can compromise; it cannot remove",
        "the tool/mechanical differential.",
        "",
        "## T4-Only Stable7 Check",
        "",
        "The seven R2 terms selected in all eight paired-|B| folds were refitted to",
        "the frozen T4 76-pose data at lambda 30:",
        "",
        "```text",
        ", ".join(STABLE7_TERMS),
        "```",
        "",
        "| evaluation | RMS / maximum mm |",
        "| --- | ---: |",
        f"| T4 training | `{stable7.t4.rms:.6f} / {stable7.t4.maximum:.6f}` |",
        f"| T3 development counterfactual | `{stable7.t3_equal.rms:.6f} / "
        f"{stable7.t3_equal.maximum:.6f}` |",
        f"| T3 maximum pose worsening | `{stable7.maximum_worsening:.6f}` at "
        f"`{pose_text(stable7.maximum_worsening_pose)}` |",
        "",
        "Stable7 does not meet the T3 ceilings. The transfer failure is therefore",
        "not resolved by simply deleting the three selection-unstable R2 terms.",
        "",
        "## Joint-Development Illustration",
        "",
        "For feasibility only, the fixed ten-term R2 family was refitted with one",
        "center per tool and equal total T4/T3 tool weight. No term was added or",
        "selected. T4 features set the scale; T3 features are separately centered and",
        "its 20 rows are weighted by `sqrt(76/20)`.",
        "",
        "For standardized correction coefficients A, the implemented sum objective is",
        "`D4 + D3 + lambda_sum*||A||^2`, where `D4=||Y4+Z4*A||^2` and",
        "`D3=(76/20)*||Y3+Z3*A||^2`. Thus each tool supplies data weight 76.",
        "The first column uses `lambda_sum=30`. An equal-tool averaged objective",
        "`0.5*(D4+D3) + 30*||A||^2` is algebraically the same normal equation as",
        "the sum implementation at `lambda_sum=60`; that is reported as the required",
        "normalization sensitivity.",
        "",
        "| evaluation | sum lambda 30 | averaged-loss lambda 30 (sum lambda 60) |",
        "| --- | ---: | ---: |",
        f"| T4 equal-76 RMS / max mm | `{joint.t4.rms:.9f} / {joint.t4.maximum:.9f}` | "
        f"`{averaged_loss_joint.t4.rms:.9f} / {averaged_loss_joint.t4.maximum:.9f}` |",
        f"| T3 equal-20 RMS / max mm | `{joint.t3_equal.rms:.9f} / {joint.t3_equal.maximum:.9f}` | "
        f"`{averaged_loss_joint.t3_equal.rms:.9f} / {averaged_loss_joint.t3_equal.maximum:.9f}` |",
        f"| T3 raw-31 RMS / max mm | `{joint.t3_raw.rms:.9f} / {joint.t3_raw.maximum:.9f}` | "
        f"`{averaged_loss_joint.t3_raw.rms:.9f} / {averaged_loss_joint.t3_raw.maximum:.9f}` |",
        f"| T3 maximum pose worsening mm | `{joint.maximum_worsening:.9f}` at "
        f"`{pose_text(joint.maximum_worsening_pose)}` | "
        f"`{averaged_loss_joint.maximum_worsening:.9f}` at "
        f"`{pose_text(averaged_loss_joint.maximum_worsening_pose)}` |",
        f"| dense configured correction mm | `{joint.dense_maximum:.9f}` at "
        f"`B{joint.dense_pose[0]:+.2f}/C{joint.dense_pose[1]:.2f}` | "
        f"`{averaged_loss_joint.dense_maximum:.9f}` at "
        f"`B{averaged_loss_joint.dense_pose[0]:+.2f}/C{averaged_loss_joint.dense_pose[1]:.2f}` |",
        "",
        "The sum-lambda-30 equal-20 result only just crosses the `0.120 / 0.280 mm`",
        "ceiling and its raw-31 result remains outside at `0.124315 / 0.291521 mm`.",
        "Under the averaged-loss normalization, equal-20 RMS moves outside to",
        "`0.121014 mm` and raw-31 remains outside at `0.126287 / 0.297833 mm`.",
        "The threshold crossing is not robust to objective normalization. Both cases",
        "are consumed development illustrations; their coefficients are intentionally",
        "not reported or written, and neither supplies a release candidate.",
        "",
        "## R3 Protocol Boundary",
        "",
        "A defensible R3 stage requires:",
        "",
        "1. Treat this four-source T3 dataset as development evidence only.",
        "2. For the preferred immediate path, use the equal-pose T4 grouped objective",
        "   `J=RMS_signed-B + RMS_paired-|B| + 0.5*RMS_C-sector` and the frozen",
        "   lambda grid `{1,3,10,30,100}`. Use current T3 only as a compatibility",
        "   constraint or rejection screen. It may influence development, never",
        "   acceptance.",
        "3. Obtain a clean uninterrupted baseline T3 development acquisition first",
        "   only if a formal equal-tool joint objective is selected.",
        "4. Freeze the family, exact sum-versus-average objective normalization,",
        "   regularization and penalty grid, dense correction bound, coefficients,",
        "   scorer, and hashes before candidate motion.",
        "5. In a formal joint fit, use equal total tool weight and one nuisance center",
        "   per complete tool acquisition. Do not fit per-pose or incomplete-source",
        "   translations.",
        "6. Keep T4 paired-|B| blocks and antipodal-C pairs outside each nested",
        "   training fold. No held response may affect scaling or selection.",
        "7. Keep the R2 ten-term family fixed, retain the collision-unidentified",
        "   sin(2C) exclusions, and strongly regularize the three unstable terms with",
        "   predeclared penalty multipliers rather than response-driven term deletion.",
        "8. Require each tool to meet equal-pose and raw `0.120 / 0.280 mm` ceilings,",
        "   at least 10% plus `0.010 / 0.020 mm` RMS/maximum improvement, positive-",
        "   and negative-B improvement, B0 worsening no more than `0.010 mm`, and",
        "   unique-pose worsening no more than `0.050 mm`.",
        "9. Bound the primary and every nested refit to `0.700 mm` on a dense complete",
        "   configured B[-100,+100]/C-cycle audit, with exact zero correction at B0/C0.",
        "10. After freezing R3, acquire an untouched uninterrupted T4 `101/28`",
        "    validation and a fresh predeclared shorter T3 verification covering every",
        "    acceptance gate, both B signs, and the B+90/C0 and C270 endpoints. Freeze",
        "    its exact poses and closure contract before motion. Neither run may trigger",
        "    coefficient tuning.",
        "",
        "Only a repeatable pose field common to both tools is eligible for the shared",
        "TCPC surface. Acquisition translations, probe reseat/insertion behavior,",
        "spindle or stylus eccentricity, rail-position straightness, electrical pulse",
        "faults, and unexplained T3/T4 differences remain in the mechanical and",
        "measurement error budget. A length-dependent vector term requires separate",
        "reseat and clocking evidence before it is physically identifiable.",
        "",
    ]
    return "\n".join(lines)


def write_atomically(path: Path, text: str) -> None:
    if path != DEFAULT_REPORT:
        raise AssessmentError(f"report path is not fixed: {path}")
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="ascii",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-report", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            self_test()
            print("TCPC R3 offline feasibility self-test: PASS")
            return 0
        generated = report_text()
        if args.check_report:
            existing = DEFAULT_REPORT.read_text(encoding="ascii")
            if existing != generated:
                raise AssessmentError(
                    f"report is not reproducible: {DEFAULT_REPORT}"
                )
            print("TCPC R3 offline feasibility report check: PASS")
            return 0
        write_atomically(DEFAULT_REPORT, generated)
        print("TCPC R3 offline feasibility assessment: COMPLETE")
        print("NO R3 COEFFICIENTS RELEASED")
        print(f"report: {DEFAULT_REPORT}")
        return 0
    except (AssessmentError, OSError, ValueError, np.linalg.LinAlgError) as exc:
        print(f"TCPC R3 offline feasibility assessment: FAIL: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
