#!/usr/bin/env python3
"""Validate and score the A1/A2/A4 T3 R2-transfer exploratory composite.

Attempt 1 is an immutable partial acquisition containing accepted global
sequences 1-14 and a terminal no-touch transaction at sequence 15. Attempt 2
is an immutable partial acquisition containing accepted sequences 15-22 and a
terminal pre-probe gap burst at sequence 23. Attempt 3 is an immutable,
zero-accepted forensic failure at sequence 23. Attempt 4 owns sequences 23-31
in fresh files. The accepted sources and the forensic source are independently
validated before accepted centers are composed. No inter-source alignment is
applied to the frozen R2 transfer score.

This module is deliberately offline-only. Its preflight performs static file,
schema, hash, and G-code checks; it never starts an interpreter or controller.
"""

from __future__ import annotations

import argparse
import csv
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
import sys
from typing import Iterator, Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_campaign as campaign
import analyze_tcpc_relocated_sphere_t3_r2_transfer_exploratory as frozen_t3
import analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt5_recovery as a5


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

CAMPAIGN = 2026082601
A1_MODE = 30
A1_ATTEMPT = 1
A2_MODE = 31
A2_ATTEMPT = 2
A3_MODE = 31
A3_ATTEMPT = 3
A4_MODE = 31
A4_ATTEMPT = 4
TOOL = 3
TOOL_LENGTH = 128.606729
CALIBRATION_OFFSET = 0.117658
EFFECTIVE_RADIUS = 17.882342

A1_SEQUENCES = tuple(range(1, 15))
A2_PLANNED_SEQUENCES = tuple(range(15, 32))
A2_SEQUENCES = tuple(range(15, 23))
A3_PLANNED_SEQUENCES = tuple(range(23, 32))
A4_SEQUENCES = tuple(range(23, 32))
ALL_SEQUENCES = tuple(range(1, 32))

A1_LOCAL_CLOSURES = (
    (100, 1, 5),
    (45, 6, 10),
)
A2_LOCAL_CLOSURES = (
    (90, 17, 21),
)
A3_PLANNED_LOCAL_CLOSURES = (
    (200, 27, 31),
)
A4_LOCAL_CLOSURES = (
    (200, 27, 31),
)
CROSS_SOURCE_CLOSURES = (
    (-45, 11, 15),
    (905, 5, 16),
    (-90, 22, 26),
    (911, 1, 27),
    (906, 16, 27),
    (912, 2, 28),
    (913, 3, 29),
    (914, 4, 30),
    (915, 5, 31),
    (900, 1, 31),
)

CONTRAST_C_ANGLES = (90, 180, 270)
TILT_BLOCK_SEQUENCES = {
    45: (6, {90: 7, 180: 8, 270: 9}, 10),
    -45: (11, {90: 12, 180: 13, 270: 14}, 15),
    90: (17, {90: 18, 180: 19, 270: 20}, 21),
    -90: (22, {90: 23, 180: 24, 270: 25}, 26),
}

A1_ARCHIVE = (
    HERE
    / "calibration_runs/20260826_1131_campaign2026082601_t3_exploratory_attempt1_partial_no_touch_seq15"
)
A1_SUMS = A1_ARCHIVE / "SHA256SUMS"
A1_PREFIX = "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1"
A1_RESULTS = A1_ARCHIVE / f"{A1_PREFIX}-results.csv"
A1_STATE = A1_ARCHIVE / f"{A1_PREFIX}-state.csv"
A1_CLOSURES = A1_ARCHIVE / f"{A1_PREFIX}-closures.csv"
A1_TRACE = A1_ARCHIVE / f"{A1_PREFIX}-contact-trace.csv"
A1_GAP_TRACE = A1_ARCHIVE / f"{A1_PREFIX}-gap-trace.csv"

A2_PROGRAM = (
    REPO_ROOT
    / "nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt2_recovery.ngc"
)
A2_PREFIX = "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt2-recovery"
A2_PARTIAL_ARCHIVE = (
    HERE
    / "calibration_runs/20260826_1238_campaign2026082601_t3_exploratory_attempt2_partial_gap_burst_seq23"
)
A2_PARTIAL_SUMS = A2_PARTIAL_ARCHIVE / "SHA256SUMS"
A2_PARTIAL_RESULTS = A2_PARTIAL_ARCHIVE / f"{A2_PREFIX}-results.csv"
A2_PARTIAL_STATE = A2_PARTIAL_ARCHIVE / f"{A2_PREFIX}-state.csv"
A2_PARTIAL_CLOSURES = A2_PARTIAL_ARCHIVE / f"{A2_PREFIX}-closures.csv"
A2_PARTIAL_TRACE = A2_PARTIAL_ARCHIVE / f"{A2_PREFIX}-contact-trace.csv"
A2_PARTIAL_GAP_TRACE = A2_PARTIAL_ARCHIVE / f"{A2_PREFIX}-gap-trace.csv"
A2_RESULTS = HERE / f"{A2_PREFIX}-results.csv"
A2_STATE = HERE / f"{A2_PREFIX}-state.csv"
A2_CLOSURES = HERE / f"{A2_PREFIX}-closures.csv"
A2_TRACE = HERE / f"{A2_PREFIX}-contact-trace.csv"
A2_GAP_TRACE = HERE / f"{A2_PREFIX}-gap-trace.csv"

A3_PROGRAM = (
    REPO_ROOT
    / "nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt3_recovery.ngc"
)
A3_PREFIX = "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt3-recovery"
A3_RESULTS = HERE / f"{A3_PREFIX}-results.csv"
A3_STATE = HERE / f"{A3_PREFIX}-state.csv"
A3_CLOSURES = HERE / f"{A3_PREFIX}-closures.csv"
A3_TRACE = HERE / f"{A3_PREFIX}-contact-trace.csv"
A3_GAP_TRACE = HERE / f"{A3_PREFIX}-gap-trace.csv"

A3_PARTIAL_ARCHIVE = (
    HERE
    / "calibration_runs/20260826_1304_campaign2026082601_t3_exploratory_attempt3_zero_accepted_gap_burst_seq23"
)
A3_PARTIAL_SUMS = A3_PARTIAL_ARCHIVE / "SHA256SUMS"
A3_PARTIAL_PROGRAM = A3_PARTIAL_ARCHIVE / A3_PROGRAM.name
A3_PARTIAL_ANALYZER = (
    A3_PARTIAL_ARCHIVE
    / "analyze_tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt3_recovery.py"
)
A3_PARTIAL_PREFLIGHT = (
    A3_PARTIAL_ARCHIVE
    / "TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_ATTEMPT3_RECOVERY_PREFLIGHT_REPORT.md"
)
A3_PARTIAL_RESULTS = A3_PARTIAL_ARCHIVE / f"{A3_PREFIX}-results.csv"
A3_PARTIAL_STATE = A3_PARTIAL_ARCHIVE / f"{A3_PREFIX}-state.csv"
A3_PARTIAL_CLOSURES = A3_PARTIAL_ARCHIVE / f"{A3_PREFIX}-closures.csv"
A3_PARTIAL_TRACE = A3_PARTIAL_ARCHIVE / f"{A3_PREFIX}-contact-trace.csv"
A3_PARTIAL_GAP_TRACE = A3_PARTIAL_ARCHIVE / f"{A3_PREFIX}-gap-trace.csv"

A4_PROGRAM = (
    REPO_ROOT
    / "nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt4_recovery.ngc"
)
A4_PREFIX = "tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt4-recovery"
A4_RESULTS = HERE / f"{A4_PREFIX}-results.csv"
A4_STATE = HERE / f"{A4_PREFIX}-state.csv"
A4_CLOSURES = HERE / f"{A4_PREFIX}-closures.csv"
A4_TRACE = HERE / f"{A4_PREFIX}-contact-trace.csv"
A4_GAP_TRACE = HERE / f"{A4_PREFIX}-gap-trace.csv"

FROZEN_T3_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_t3_r2_transfer_exploratory.py"
A5_ANALYZER = HERE / "analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt5_recovery.py"

DEFAULT_PREFLIGHT_REPORT = (
    HERE / "TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_ATTEMPT4_RECOVERY_PREFLIGHT_REPORT.md"
)
DEFAULT_RESULT_REPORT = (
    HERE / "TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_ATTEMPT4_THREE_SOURCE_REPORT.md"
)

EXPECTED_HASHES = {
    A1_SUMS: "85306077f177700c49fc122fc79d2e24edbc7ab5d11b25209a8e7eb35439d700",
    A1_RESULTS: "bd529dc0ebbdabcddca92ce0a46bf5e6da5f4718ba659e3d44ff8a4f57279e81",
    A1_STATE: "108a5859acc6e360913ef74a17130004b0a2b75112f560cf00cb653c7d35aee0",
    A1_CLOSURES: "ac58157f6fb29ca61098373059089a2d7e8ab86f0bc58dc68f05b0da5e5aa111",
    A1_TRACE: "04aedbcffbeb5bb57e6d4c79e5a9b94c58d7830c2ed1ec21476be04aa9cce6f6",
    A1_GAP_TRACE: "68fea41cdf67aa694f02e00aaedeb5a64197836901c11a0d1b0deafda3b0fc59",
    A2_PARTIAL_SUMS: "053344b2cf1676f6ae06ec3ae53a65ec3b7decd9e726839ed7fb94ed595a3df2",
    A2_PARTIAL_RESULTS: "ce881c922ad6df18ef92e076d7ab9ef953371c9e92a536e6e726f66046019ee4",
    A2_PARTIAL_STATE: "9ed40579a009b97c0a3d724f3d855b2928a0e5c2480c624bbef705a8eb9d7b10",
    A2_PARTIAL_CLOSURES: "0d05a529b3537c563e500e111a48ad33c2f87c8a73f9d9fc31b6d3795ff230cb",
    A2_PARTIAL_TRACE: "bc0eb7b098de93eeea2eef533ad89758b1a98ec0db635d539d9f38358eb1eff6",
    A2_PARTIAL_GAP_TRACE: "6734adbdfcb29cadcae7a1047db9b00a6479b426c44a25be576ad6615d0d5c62",
    A2_PROGRAM: "1fd88b02972d4a09d2aedd5615e6b5471721b69b6c6a6b901a2c20d8a7b96f66",
    A4_PROGRAM: "b0f33c47d76df4401353838cd93be2af5ca4c38b2f835e55d355b11220a0a15a",
    A3_PARTIAL_SUMS: "841640923c31a7b4275bb2edc7e4273f1e64a4dd70624b1ed0f815902cedd5f7",
    A3_PARTIAL_PROGRAM: "9db6d03a12085928fb3fe9eacea203e240ee5d52274f5cb04e23d2e981fb18ed",
    A3_PARTIAL_ANALYZER: "0e62885fcbe6d0d13ca19bcf69cc2c7232da33edd383cb9325dc94fb444c6a23",
    A3_PARTIAL_PREFLIGHT: "1f044a9421f792ce7fa8af319769ce4296dbacceb0f25d798f3a66fa8b8079c1",
    A3_PARTIAL_RESULTS: "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    A3_PARTIAL_STATE: "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    A3_PARTIAL_CLOSURES: "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    A3_PARTIAL_TRACE: "dfbd0a4ec9774723a9c112dfa817e32b1e3c140fc6781521902460e187f52644",
    A3_PARTIAL_GAP_TRACE: "0215954344f95bc2b354f7233c67075e2589debbcae707aaff0d0b7e800ba7a1",
    FROZEN_T3_ANALYZER: "ba863ff3747ed1efe7540616423369b424452cc331c42568a211583f6350f00c",
    A5_ANALYZER: "e41ceaf962d2639ecc00872223de0e42d91e294c960c1d4b5552a4146e44a6c0",
}

HEADER_HASHES = {
    A4_RESULTS: "9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93",
    A4_STATE: "ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7",
    A4_CLOSURES: "1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f",
    A4_TRACE: "df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8",
    A4_GAP_TRACE: "e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2",
}

EXPECTED_ROWS = frozen_t3.EXPECTED_ROWS
EXPECTED_BY_SEQ = {row.seq: row for row in EXPECTED_ROWS}


class CompositeError(ValueError):
    pass


@dataclass(frozen=True)
class ElectricalEvent:
    scope: str
    sequence: int
    acquisition_try: int
    pass_id: int
    contact_id: int
    raw_delta: int
    mux_delta: int
    gated_delta: int
    combined_extra: int
    burst: bool


@dataclass(frozen=True)
class ElectricalDiagnostics:
    contact_repeat_events: tuple[ElectricalEvent, ...] = ()
    gap_events: tuple[ElectricalEvent, ...] = ()


@dataclass(frozen=True)
class SegmentValidation:
    centers: dict[int, np.ndarray]
    pass_center_deltas: dict[int, float]
    closure_norms: np.ndarray
    contact_rows: int
    gap_rows: int
    rejected_try1_poses: int
    electrical: ElectricalDiagnostics = ElectricalDiagnostics()


@dataclass(frozen=True)
class Score:
    classification: str
    raw_base: tuple[float, float]
    raw_r2: tuple[float, float]
    equal_base: tuple[float, float]
    equal_r2: tuple[float, float]
    mismatch: tuple[float, float]
    gates: dict[str, bool]
    maximum_worsening: float
    maximum_worsening_pose: tuple[int, int]


@dataclass(frozen=True)
class OverlapSensitivity:
    translation: np.ndarray
    raw_rms: float
    raw_max: float
    aligned_rms: float
    aligned_max: float


@dataclass(frozen=True)
class MatchedT4:
    centers: dict[int, np.ndarray]
    pass_center_deltas: dict[int, float]
    source_sequences: dict[int, int]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise CompositeError(
            f"SHA-256 changed for {path}: {actual}, expected {expected}"
        )


def exact_int(row: dict[str, str], field: str, *, positive: bool = False) -> int:
    return campaign.exact_integer(row, field, positive=positive)


def validate_archive_members(archive: Path, sums: Path, label: str) -> None:
    """Verify a complete sealed directory against its hash manifest."""
    listed: dict[str, str] = {}
    for line_number, line in enumerate(
        sums.read_text(encoding="ascii").splitlines(), 1
    ):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise CompositeError(f"{label} checksum line {line_number} is malformed")
        digest, relative_text = match.groups()
        relative = Path(relative_text)
        normalized = relative.as_posix()
        if relative.is_absolute() or ".." in relative.parts or normalized in listed:
            raise CompositeError(f"{label} checksum member is unsafe or duplicated")
        listed[normalized] = digest

    actual: set[str] = set()
    for member in archive.rglob("*"):
        if member.is_symlink():
            raise CompositeError(f"{label} archive contains a symlink: {member}")
        if member.is_file() and member != sums:
            actual.add(member.relative_to(archive).as_posix())
    if actual != set(listed):
        missing = sorted(set(listed) - actual)
        extra = sorted(actual - set(listed))
        raise CompositeError(
            f"{label} archive members differ from seal; missing={missing}, extra={extra}"
        )
    for relative, digest in listed.items():
        require_hash(archive / relative, digest)


def validate_archive_seal() -> None:
    """Verify frozen dependencies and the complete sealed A1 directory."""
    for path, digest in EXPECTED_HASHES.items():
        require_hash(path, digest)
    validate_archive_members(A1_ARCHIVE, A1_SUMS, "A1")


@contextmanager
def validator_context(
    mode: int,
    attempt: int,
    sequences: Sequence[int],
    trace: Path,
    gap_trace: Path,
) -> Iterator[None]:
    """Temporarily point the proven Attempt-5 transaction validator at a source."""
    saved_campaign = campaign.CAMPAIGN
    saved = {
        name: getattr(a5, name)
        for name in (
            "CAMPAIGN",
            "MODE",
            "ATTEMPT",
            "ATTEMPT2_ATTEMPT",
            "FULL_BY_SEQ",
            "RECOVERY_SEQUENCES",
            "RECOVERY_SEQUENCE_SET",
            "TRACE",
            "GAP_TRACE",
        )
    }
    try:
        campaign.CAMPAIGN = CAMPAIGN
        a5.CAMPAIGN = CAMPAIGN
        a5.MODE = mode
        a5.ATTEMPT = attempt
        a5.ATTEMPT2_ATTEMPT = attempt
        a5.FULL_BY_SEQ = EXPECTED_BY_SEQ
        a5.RECOVERY_SEQUENCES = tuple(sequences)
        a5.RECOVERY_SEQUENCE_SET = set(sequences)
        a5.TRACE = trace
        a5.GAP_TRACE = gap_trace
        yield
    finally:
        campaign.CAMPAIGN = saved_campaign
        for name, value in saved.items():
            setattr(a5, name, value)


def run_spec(
    name: str,
    mode: int,
    results: Path,
    state: Path,
    closures: Path,
    sequences: Sequence[int],
) -> campaign.RunSpec:
    return campaign.RunSpec(
        name,
        TOOL,
        mode,
        TOOL_LENGTH,
        CALIBRATION_OFFSET,
        EFFECTIVE_RADIUS,
        results,
        state,
        closures,
        tuple(EXPECTED_BY_SEQ[seq] for seq in sequences),
        tuple(),
    )


def tuple_sum(rows: Sequence[dict[str, str]], fields: Sequence[str]) -> tuple[int, ...]:
    return tuple(sum(exact_int(row, field) for row in rows) for field in fields)


def retry_trace_summary(rows: Sequence[dict[str, str]]) -> tuple[int, int]:
    """Return retried-pose count and the rejected try-1 transaction count."""
    by_sequence: dict[int, dict[int, int]] = {}
    for row in rows:
        sequence = exact_int(row, "global_seq", positive=True)
        acquisition = exact_int(row, "acquisition_try", positive=True)
        counts = by_sequence.setdefault(sequence, {})
        counts[acquisition] = counts.get(acquisition, 0) + 1

    rejected_transactions = 0
    retried_poses = 0
    for sequence, counts in by_sequence.items():
        if 2 not in counts:
            continue
        retried_poses += 1
        if counts.get(1) not in (4, 8) or counts[2] != 8:
            raise CompositeError(
                f"sequence {sequence}: retry trace shape changed: {counts}"
            )
        rejected_transactions += counts[1]
    return retried_poses, rejected_transactions


def pass_center_deltas(
    rows: Sequence[dict[str, str]], sequences: Sequence[int]
) -> dict[int, float]:
    row_sequences = [
        exact_int(row, "sample_seq", positive=True) for row in rows
    ]
    if row_sequences != list(sequences):
        raise CompositeError("pass-center rows do not match their accepted sequence order")
    values = {
        sequence: anchor.bounded(row, "pass_center_delta_mm", 0.0, 0.100)
        for sequence, row in zip(row_sequences, rows)
    }
    if len(values) != len(sequences):
        raise CompositeError("pass-center context contains a duplicate sequence")
    return values


def validate_a1_forensics() -> SegmentValidation:
    """Validate A1's accepted prefix and exact terminal no-touch evidence."""
    validate_archive_seal()
    with validator_context(A1_MODE, A1_ATTEMPT, ALL_SEQUENCES, A1_TRACE, A1_GAP_TRACE):
        spec = run_spec(
            "sealed T3 exploratory attempt 1 partial",
            A1_MODE,
            A1_RESULTS,
            A1_STATE,
            A1_CLOSURES,
            ALL_SEQUENCES,
        )
        centers, closure_norms, accepted = a5.validate_acquisition(
            spec,
            ALL_SEQUENCES,
            A1_LOCAL_CLOSURES,
            allow_prefix=True,
        )
        if accepted != list(A1_SEQUENCES):
            raise CompositeError("sealed A1 accepted rows are not exactly seq1-14")

        gap_count, gap_terminal, terminal_gap_key = a5.validate_gap_trace(
            complete=False
        )
        contact_count, bursts, contact_terminal = a5.validate_contact_trace(
            accepted,
            complete=False,
            terminal_gap_key=terminal_gap_key,
        )
        if (
            contact_count != 119
            or gap_count != 119
            or bursts != 0
            or gap_terminal is not None
            or terminal_gap_key is not None
            or contact_terminal != "no touch"
        ):
            raise CompositeError("sealed A1 terminal trace classification changed")

        contacts = a5.read_identity_rows(
            A1_TRACE, a5.TRACE_FIELDS, A1_MODE, A1_ATTEMPT
        )
        gaps = a5.read_identity_rows(
            A1_GAP_TRACE, a5.GAP_TRACE_FIELDS, A1_MODE, A1_ATTEMPT
        )
        result_rows = a5.read_identity_rows(
            A1_RESULTS, anchor.RESULT_FIELDS, A1_MODE, A1_ATTEMPT
        )
        center_deltas = pass_center_deltas(result_rows, A1_SEQUENCES)

        first_pre = tuple(
            exact_int(contacts[0], f"pre_{name}_count")
            for name in ("raw", "mux", "gated")
        )
        final_ready = tuple(
            exact_int(contacts[-1], f"ready_{name}_count")
            for name in ("raw", "mux", "gated")
        )
        if first_pre != (343, 343, 0) or final_ready != (466, 466, 118):
            raise CompositeError("sealed A1 first/final edge-counter baseline changed")

        direct = tuple_sum(
            contacts, ("raw_delta", "mux_delta", "gated_delta")
        )
        repeats = tuple_sum(
            contacts,
            ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"),
        )
        gap_edges = tuple_sum(
            gaps, ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta")
        )
        if direct != (118, 118, 118):
            raise CompositeError("sealed A1 direct-contact edge totals changed")
        if repeats != (4, 4, 0) or gap_edges != (1, 1, 0):
            raise CompositeError("sealed A1 contained repeat/gap edge totals changed")
        if final_ready[0] - first_pre[0] - (final_ready[2] - first_pre[2]) != 5:
            raise CompositeError("sealed A1 five-extra-edge invariant changed")

        repeat_keys = [
            (
                exact_int(row, "global_seq", positive=True),
                exact_int(row, "acquisition_try", positive=True),
                exact_int(row, "pass_id", positive=True),
                exact_int(row, "contact_id", positive=True),
            )
            for row in contacts
            if exact_int(row, "repeat_raw_delta") != 0
            or exact_int(row, "repeat_mux_delta") != 0
            or exact_int(row, "repeat_gated_delta") != 0
        ]
        if repeat_keys != [
            (4, 1, 1, 1),
            (7, 1, 2, 1),
            (15, 1, 2, 2),
            (15, 1, 2, 3),
        ]:
            raise CompositeError("sealed A1 post-contact repeat locations changed")

        nonzero_gap_keys = [
            (
                exact_int(row, "next_global_seq", positive=True),
                exact_int(row, "acquisition_try", positive=True),
                exact_int(row, "pass_id", positive=True),
                exact_int(row, "contact_id", positive=True),
            )
            for row in gaps
            if exact_int(row, "gap_raw_delta") != 0
            or exact_int(row, "gap_mux_delta") != 0
            or exact_int(row, "gap_gated_delta") != 0
        ]
        if nonzero_gap_keys != [(15, 1, 2, 3)]:
            raise CompositeError("sealed A1 inter-contact repeat location changed")

        terminal = contacts[-1]
        terminal_identity = {
            "global_seq": 15,
            "acquisition_try": 1,
            "pass_id": 2,
            "contact_id": 3,
            "probe_result": 0,
            "raw_delta": 0,
            "mux_delta": 0,
            "gated_delta": 0,
            "repeat_raw_delta": 1,
            "repeat_mux_delta": 1,
            "repeat_gated_delta": 0,
            "burst_flag": 0,
            "consistency_fault": 0,
            "release_fault": 0,
            "terminal_failure": 1,
        }
        if any(exact_int(terminal, field) != value for field, value in terminal_identity.items()):
            raise CompositeError("sealed A1 terminal seq15 transaction changed")
        if abs(anchor.number(terminal, "travel_mm") - 6.0) > 1e-9:
            raise CompositeError("sealed A1 terminal no-touch travel changed")

    return SegmentValidation(
        centers, center_deltas, closure_norms, contact_count, gap_count, 0
    )


def validate_a2_partial_forensics() -> SegmentValidation:
    """Validate sealed A2 seq15-22 and its terminal pre-G38 gap burst."""
    for path in (
        A2_PARTIAL_SUMS,
        A2_PARTIAL_RESULTS,
        A2_PARTIAL_STATE,
        A2_PARTIAL_CLOSURES,
        A2_PARTIAL_TRACE,
        A2_PARTIAL_GAP_TRACE,
    ):
        require_hash(path, EXPECTED_HASHES[path])
    validate_archive_members(A2_PARTIAL_ARCHIVE, A2_PARTIAL_SUMS, "A2")

    with validator_context(
        A2_MODE,
        A2_ATTEMPT,
        A2_PLANNED_SEQUENCES,
        A2_PARTIAL_TRACE,
        A2_PARTIAL_GAP_TRACE,
    ):
        spec = run_spec(
            "sealed T3 exploratory attempt 2 partial",
            A2_MODE,
            A2_PARTIAL_RESULTS,
            A2_PARTIAL_STATE,
            A2_PARTIAL_CLOSURES,
            A2_PLANNED_SEQUENCES,
        )
        centers, closure_norms, accepted = a5.validate_acquisition(
            spec,
            A2_PLANNED_SEQUENCES,
            A2_LOCAL_CLOSURES,
            allow_prefix=True,
        )
        if accepted != list(A2_SEQUENCES):
            raise CompositeError("sealed A2 accepted rows are not exactly seq15-22")

        gap_count, gap_terminal, terminal_gap_key = a5.validate_gap_trace(
            complete=False
        )
        contact_count, bursts, contact_terminal = a5.validate_contact_trace(
            accepted,
            complete=False,
            terminal_gap_key=terminal_gap_key,
        )
        if (
            gap_count != 65
            or contact_count != 64
            or bursts != 0
            or gap_terminal != "inter-contact retrigger burst"
            or terminal_gap_key != (23, 1, 1, 1)
            or contact_terminal is not None
        ):
            raise CompositeError("sealed A2 terminal gap-burst classification changed")

        contacts = a5.read_identity_rows(
            A2_PARTIAL_TRACE, a5.TRACE_FIELDS, A2_MODE, A2_ATTEMPT
        )
        gaps = a5.read_identity_rows(
            A2_PARTIAL_GAP_TRACE, a5.GAP_TRACE_FIELDS, A2_MODE, A2_ATTEMPT
        )
        result_rows = a5.read_identity_rows(
            A2_PARTIAL_RESULTS, anchor.RESULT_FIELDS, A2_MODE, A2_ATTEMPT
        )
        center_deltas = pass_center_deltas(result_rows, A2_SEQUENCES)
        if retry_trace_summary(contacts) != (0, 0):
            raise CompositeError("sealed A2 unexpectedly contains a whole-pose retry")

        direct = tuple_sum(
            contacts, ("raw_delta", "mux_delta", "gated_delta")
        )
        repeats = tuple_sum(
            contacts,
            ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"),
        )
        gap_edges = tuple_sum(
            gaps, ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta")
        )
        if direct != (64, 64, 64) or repeats != (5, 5, 0) or gap_edges != (5, 5, 0):
            raise CompositeError("sealed A2 contact/repeat/gap edge totals changed")

        repeat_keys = [
            (
                exact_int(row, "global_seq", positive=True),
                exact_int(row, "acquisition_try", positive=True),
                exact_int(row, "pass_id", positive=True),
                exact_int(row, "contact_id", positive=True),
            )
            for row in contacts
            if any(
                exact_int(row, field)
                for field in (
                    "repeat_raw_delta",
                    "repeat_mux_delta",
                    "repeat_gated_delta",
                )
            )
        ]
        if repeat_keys != [
            (16, 1, 2, 4),
            (20, 1, 1, 1),
            (22, 1, 1, 2),
            (22, 1, 2, 1),
            (22, 1, 2, 2),
        ]:
            raise CompositeError("sealed A2 contained-repeat locations changed")

        nonzero_gaps = [
            row
            for row in gaps
            if any(
                exact_int(row, field)
                for field in ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta")
            )
        ]
        nonzero_gap_keys = [
            (
                exact_int(row, "next_global_seq", positive=True),
                exact_int(row, "acquisition_try", positive=True),
                exact_int(row, "pass_id", positive=True),
                exact_int(row, "contact_id", positive=True),
            )
            for row in nonzero_gaps
        ]
        if nonzero_gap_keys != [(22, 1, 2, 3), (23, 1, 1, 1)]:
            raise CompositeError("sealed A2 nonzero-gap locations changed")
        contained, terminal = nonzero_gaps
        if (
            tuple(exact_int(contained, field) for field in (
                "gap_raw_delta", "gap_mux_delta", "gap_gated_delta"
            )) != (1, 1, 0)
            or exact_int(contained, "combined_extra_delta") != 2
            or exact_int(contained, "burst_flag") != 0
        ):
            raise CompositeError("sealed A2 contained gap-edge contract changed")

        terminal_expected = {
            "prior_ready_raw_count": 692,
            "prior_ready_mux_count": 692,
            "prior_ready_gated_count": 182,
            "current_pre_raw_count": 696,
            "current_pre_mux_count": 696,
            "current_pre_gated_count": 182,
            "gap_raw_delta": 4,
            "gap_mux_delta": 4,
            "gap_gated_delta": 0,
            "prior_contact_extra_delta": 0,
            "combined_extra_delta": 4,
            "burst_flag": 1,
            "consistency_fault": 0,
            "initial_baseline": 0,
        }
        if any(
            exact_int(terminal, field) != value
            for field, value in terminal_expected.items()
        ):
            raise CompositeError("sealed A2 terminal gap counters changed")

    return SegmentValidation(
        centers,
        center_deltas,
        closure_norms,
        contact_count,
        gap_count,
        0,
    )


def validate_a3_partial_forensics() -> SegmentValidation:
    """Validate sealed A3 as a zero-accepted terminal forensic source."""
    for path in (
        A3_PARTIAL_SUMS,
        A3_PARTIAL_PROGRAM,
        A3_PARTIAL_ANALYZER,
        A3_PARTIAL_PREFLIGHT,
        A3_PARTIAL_RESULTS,
        A3_PARTIAL_STATE,
        A3_PARTIAL_CLOSURES,
        A3_PARTIAL_TRACE,
        A3_PARTIAL_GAP_TRACE,
    ):
        require_hash(path, EXPECTED_HASHES[path])
    validate_archive_members(A3_PARTIAL_ARCHIVE, A3_PARTIAL_SUMS, "A3")

    with validator_context(
        A3_MODE,
        A3_ATTEMPT,
        A3_PLANNED_SEQUENCES,
        A3_PARTIAL_TRACE,
        A3_PARTIAL_GAP_TRACE,
    ):
        spec = run_spec(
            "sealed T3 exploratory attempt 3 zero-accepted partial",
            A3_MODE,
            A3_PARTIAL_RESULTS,
            A3_PARTIAL_STATE,
            A3_PARTIAL_CLOSURES,
            A3_PLANNED_SEQUENCES,
        )
        centers, closure_norms, accepted = a5.validate_acquisition(
            spec,
            A3_PLANNED_SEQUENCES,
            A3_PLANNED_LOCAL_CLOSURES,
            allow_prefix=True,
        )
        if accepted or centers or len(closure_norms) != 0:
            raise CompositeError("sealed A3 unexpectedly owns an accepted pose")

        gap_count, gap_terminal, terminal_gap_key = a5.validate_gap_trace(
            complete=False
        )
        contact_count, bursts, contact_terminal = a5.validate_contact_trace(
            accepted,
            complete=False,
            terminal_gap_key=terminal_gap_key,
        )
        if (
            contact_count != 2
            or gap_count != 3
            or bursts != 0
            or gap_terminal != "inter-contact retrigger burst"
            or terminal_gap_key != (23, 1, 1, 3)
            or contact_terminal is not None
        ):
            raise CompositeError("sealed A3 terminal gap-burst classification changed")

        contacts = a5.read_identity_rows(
            A3_PARTIAL_TRACE, a5.TRACE_FIELDS, A3_MODE, A3_ATTEMPT
        )
        gaps = a5.read_identity_rows(
            A3_PARTIAL_GAP_TRACE, a5.GAP_TRACE_FIELDS, A3_MODE, A3_ATTEMPT
        )
        if retry_trace_summary(contacts) != (0, 0):
            raise CompositeError("sealed A3 unexpectedly contains a whole-pose retry")

        contact_keys = [
            (
                exact_int(row, "global_seq", positive=True),
                exact_int(row, "acquisition_try", positive=True),
                exact_int(row, "pass_id", positive=True),
                exact_int(row, "contact_id", positive=True),
            )
            for row in contacts
        ]
        if contact_keys != [(23, 1, 1, 1), (23, 1, 1, 2)]:
            raise CompositeError("sealed A3 successful-contact prefix changed")

        expected_contact_counters = (
            ((700, 700, 182), (701, 701, 183), (701, 701, 183)),
            ((701, 701, 183), (702, 702, 184), (702, 702, 184)),
        )
        expected_travel = (4.707656, 4.060944)
        for index, row in enumerate(contacts):
            observed = tuple(
                tuple(exact_int(row, f"{phase}_{name}_count") for name in ("raw", "mux", "gated"))
                for phase in ("pre", "post", "ready")
            )
            if observed != expected_contact_counters[index]:
                raise CompositeError("sealed A3 contact counters changed")
            if tuple_sum([row], ("raw_delta", "mux_delta", "gated_delta")) != (1, 1, 1):
                raise CompositeError("sealed A3 direct-contact delta changed")
            if tuple_sum(
                [row],
                ("repeat_raw_delta", "repeat_mux_delta", "repeat_gated_delta"),
            ) != (0, 0, 0):
                raise CompositeError("sealed A3 contact gained a repeat edge")
            for field, value in (
                ("probe_result", 1),
                ("burst_flag", 0),
                ("consistency_fault", 0),
                ("release_fault", 0),
                ("terminal_failure", 0),
            ):
                if exact_int(row, field) != value:
                    raise CompositeError(f"sealed A3 contact {field} changed")
            if abs(anchor.number(row, "travel_mm") - expected_travel[index]) > 1e-6:
                raise CompositeError("sealed A3 successful-contact travel changed")

        gap_keys = [
            (
                exact_int(row, "next_global_seq", positive=True),
                exact_int(row, "acquisition_try", positive=True),
                exact_int(row, "pass_id", positive=True),
                exact_int(row, "contact_id", positive=True),
            )
            for row in gaps
        ]
        if gap_keys != [
            (23, 1, 1, 1),
            (23, 1, 1, 2),
            (23, 1, 1, 3),
        ]:
            raise CompositeError("sealed A3 gap transaction order changed")
        if tuple_sum(gaps, ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta")) != (5, 5, 0):
            raise CompositeError("sealed A3 gap-edge total changed")

        terminal = gaps[-1]
        terminal_expected = {
            "prior_ready_raw_count": 702,
            "prior_ready_mux_count": 702,
            "prior_ready_gated_count": 184,
            "current_pre_raw_count": 707,
            "current_pre_mux_count": 707,
            "current_pre_gated_count": 184,
            "gap_raw_delta": 5,
            "gap_mux_delta": 5,
            "gap_gated_delta": 0,
            "prior_contact_extra_delta": 0,
            "combined_extra_delta": 5,
            "burst_flag": 1,
            "consistency_fault": 0,
            "initial_baseline": 0,
        }
        if any(
            exact_int(terminal, field) != value
            for field, value in terminal_expected.items()
        ):
            raise CompositeError("sealed A3 terminal gap counters changed")

    return SegmentValidation({}, {}, closure_norms, contact_count, gap_count, 0)


def strip_subroutines(text: str) -> str:
    return re.sub(
        r"(?ms)^o<([^>]+)> sub\s*$.*?^o<\1> endsub\s*$",
        "",
        text,
    )


def validate_a4_program() -> None:
    require_hash(A4_PROGRAM, EXPECTED_HASHES[A4_PROGRAM])
    text = A4_PROGRAM.read_text(encoding="ascii")
    lines = text.splitlines()
    if len(lines) != 1476 or max(map(len, lines)) > 225:
        raise CompositeError("A4 runner line-count/maximum-line contract changed")
    if text.count("\nM0\n") != 1:
        raise CompositeError("A4 runner must contain exactly one standalone M0")

    before_hold = strip_subroutines(text.split("\nM0\n", 1)[0])
    executable = "\n".join(line.split("(", 1)[0] for line in before_hold.splitlines())
    motion = re.compile(
        r"(?:^|\s)G(?:0?0|0?1|0?2|0?3|38(?:\.\d+)?)\b", re.IGNORECASE
    )
    if motion.search(executable):
        raise CompositeError("A4 runner has axis/rotary/probe motion before M0")

    required_once = (
        "#516 = 128.606729",
        "#717 = 0.117658",
        "#707 = 9.0",
        "#711 = 31.0",
        "#715 = 2026082601.0",
        "#716 = 1.0",
        "#727 = 4.0",
        "#726 = 22.0",
        "o<run_relocated_t3_recovery> if [ABS[#711 - 31.0] LT 0.1]",
        "o<primary_sequence_complete> if [[ABS[#726 - 31.0] GT 0.000001] OR [ABS[#788 - #707] GT 0.000001]]",
        "o<trace_success_one_raw_edge> if [ABS[#963 - 1.0] GT 0.000001]",
        "o<trace_success_one_mux_edge> if [ABS[#964 - 1.0] GT 0.000001]",
        "o<trace_success_one_gated_edge> if [ABS[#965 - 1.0] GT 0.000001]",
        "o<trace_success_no_gated_repeat> if [ABS[#968] GT 0.000001]",
        "o<trace_gap_counter_consistency> if [[ABS[#956 - #957] GT 0.000001] OR [ABS[#958] GT 0.000001]]",
        "(Matched raw/mux extra edges with zero gated delta remain diagnostic.)",
        "(A matched raw/mux burst with zero gated repeats remains a logged diagnostic.)",
    )
    for token in required_once:
        if text.count(token) != 1:
            raise CompositeError(f"A4 runner identity token changed: {token}")
    if re.search(r"\b(?:setp|halcmd)\b", text, re.IGNORECASE):
        raise CompositeError("A4 runner contains a HAL/coefficient write command")
    for forbidden_abort in (
        "Electrical retrigger burst exceeded two repeats across inter-contact gap",
        "Probe electrical retrigger burst exceeds two repeats",
    ):
        if forbidden_abort in text:
            raise CompositeError("A4 runner still aborts on a matched diagnostic burst")
    for forbidden in (
        "tcpc_relocated_sphere_t4_candidate_r2.hal",
        f"{A1_PREFIX}-results.csv",
        f"{A1_PREFIX}-state.csv",
        f"{A1_PREFIX}-closures.csv",
        f"{A1_PREFIX}-contact-trace.csv",
        f"{A1_PREFIX}-gap-trace.csv",
        f"{A2_PREFIX}-results.csv",
        f"{A2_PREFIX}-state.csv",
        f"{A2_PREFIX}-closures.csv",
        f"{A2_PREFIX}-contact-trace.csv",
        f"{A2_PREFIX}-gap-trace.csv",
        f"{A3_PREFIX}-results.csv",
        f"{A3_PREFIX}-state.csv",
        f"{A3_PREFIX}-closures.csv",
        f"{A3_PREFIX}-contact-trace.csv",
        f"{A3_PREFIX}-gap-trace.csv",
    ):
        if forbidden in text:
            raise CompositeError(f"A4 runner contains forbidden source/write target: {forbidden}")

    log_paths = re.findall(r"^\s*\(LOGAPPEND,([^\n)]+)\)\s*$", text, re.MULTILINE)
    expected_logs = {
        str(A4_RESULTS),
        str(A4_STATE),
        str(A4_CLOSURES),
        str(A4_TRACE),
        str(A4_GAP_TRACE),
    }
    if len(log_paths) != 5 or set(log_paths) != expected_logs:
        raise CompositeError("A4 runner does not write exactly its five fresh outputs")

    match = re.search(
        r"^o<run_relocated_t3_recovery> if \[ABS\[#711 - 31\.0\] LT 0\.1\]\s*$"
        r"([\s\S]*?)^o<run_relocated_t3_recovery> endif\s*$",
        text,
        re.MULTILINE,
    )
    if match is None:
        raise CompositeError("A4 mode-31 body is missing")
    body = match.group(1)
    ordered = (
        "#726 = 22.0",
        "o<tcpc_measure_pose> call [-90.0] [90.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-90.0] [180.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-90.0] [270.0] [0.0] [0.0]",
        "o<tcpc_measure_pose> call [-90.0] [0.0] [0.0] [0.0]",
        "o<tcpc_recovery_closing_b0_sweep> call",
    )
    positions = [body.find(token) for token in ordered]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise CompositeError("A4 sequence 23-31 pose-block order changed")
    if body.count("o<tcpc_measure_pose> call") != 4:
        raise CompositeError("A4 body direct pose-call count changed")
    if body.count("o<tcpc_primary_tilt_block> call") != 0:
        raise CompositeError("A4 body unexpectedly invokes a full tilt block")
    if body.count("o<tcpc_recovery_closing_b0_sweep> call") != 1:
        raise CompositeError("A4 body closing-sweep call count changed")

    closure_token = "[#728] [#<sweep_open_seq>] [#726]"
    if text.count(closure_token) != 1:
        raise CompositeError("A4 source-local closure implementation changed")
    for forbidden_closure in (
        "[906.0] [16.0] [#726]",
        "[#728] [#<block_open_seq>] [#726]",
    ):
        if forbidden_closure in text:
            raise CompositeError("A4 contains a non-local closure implementation")

    balances = (
        (r"^\s*o<[^>]+>\s+sub\s*$", r"^\s*o<[^>]+>\s+endsub\s*$", "sub"),
        (r"^\s*o<[^>]+>\s+if\b", r"^\s*o<[^>]+>\s+endif\s*$", "if"),
        (r"^\s*o<[^>]+>\s+while\b", r"^\s*o<[^>]+>\s+endwhile\s*$", "while"),
    )
    for opening, closing, label in balances:
        if len(re.findall(opening, text, re.MULTILINE)) != len(
            re.findall(closing, text, re.MULTILINE)
        ):
            raise CompositeError(f"A4 runner has unbalanced O-word {label} blocks")


def validate_a4_headers() -> None:
    contracts = {
        A4_RESULTS: anchor.RESULT_FIELDS,
        A4_STATE: anchor.STATE_FIELDS,
        A4_CLOSURES: campaign.CLOSURE_FIELDS,
        A4_TRACE: a5.TRACE_FIELDS,
        A4_GAP_TRACE: a5.GAP_TRACE_FIELDS,
    }
    for path, fields in contracts.items():
        require_hash(path, HEADER_HASHES[path])
        with path.open(newline="", encoding="ascii") as stream:
            rows = list(csv.reader(stream))
        if rows != [list(fields)]:
            raise CompositeError(f"A4 output is not the exact fresh header: {path}")


def trace_transaction_key(
    row: dict[str, str], sequence_field: str
) -> tuple[int, int, int, int]:
    return (
        exact_int(row, sequence_field, positive=True),
        exact_int(row, "acquisition_try", positive=True),
        exact_int(row, "pass_id", positive=True),
        exact_int(row, "contact_id", positive=True),
    )


def raw_only_delta_valid(delta: tuple[int, int, int]) -> bool:
    return delta[0] >= 0 and delta[0] == delta[1] and delta[2] == 0


def direct_g38_delta_valid(delta: tuple[int, int, int]) -> bool:
    return delta == (1, 1, 1)


def phase_counters(
    row: dict[str, str], phase: str
) -> tuple[int, int, int]:
    return tuple(
        exact_int(row, f"{phase}_{name}_count")
        for name in ("raw", "mux", "gated")
    )


def validate_burst_tolerant_complete_traces(
    accepted: Sequence[int],
    contacts: Sequence[dict[str, str]],
    gaps: Sequence[dict[str, str]],
) -> ElectricalDiagnostics:
    """Validate A4 traces while retaining matched raw-only burst diagnostics."""
    parsed = [a5.validate_trace_row(row) for row in contacts]
    order_index = {seq: index for index, seq in enumerate(A4_SEQUENCES)}
    if any(
        order_index[parsed[index][0]] > order_index[parsed[index + 1][0]]
        for index in range(len(parsed) - 1)
    ):
        raise CompositeError("A4 contact trace sequence order moved backwards")

    by_sequence: dict[int, list[tuple[int, int, int]]] = {}
    contact_events: list[ElectricalEvent] = []
    for row, (sequence, key, burst, terminal, consistency, release_fault) in zip(
        contacts, parsed
    ):
        direct = tuple(
            exact_int(row, field)
            for field in ("raw_delta", "mux_delta", "gated_delta")
        )
        repeats = tuple(
            exact_int(row, field)
            for field in (
                "repeat_raw_delta",
                "repeat_mux_delta",
                "repeat_gated_delta",
            )
        )
        if not direct_g38_delta_valid(direct):
            raise CompositeError(
                f"A4 sequence {sequence}: successful G38 delta is not exactly 1/1/1"
            )
        if not raw_only_delta_valid(repeats):
            raise CompositeError(
                f"A4 sequence {sequence}: post-contact repeat is not matched raw/mux-only"
            )
        if (
            terminal
            or consistency
            or release_fault
            or exact_int(row, "probe_result") != 1
            or exact_int(row, "terminal_failure") != 0
        ):
            raise CompositeError(f"A4 sequence {sequence}: forbidden contact fault")
        if burst != (repeats[0] > 2):
            raise CompositeError(f"A4 sequence {sequence}: contact burst flag changed")
        by_sequence.setdefault(sequence, []).append(key)
        if repeats[0] != 0 or burst:
            contact_events.append(
                ElectricalEvent(
                    "post-contact",
                    sequence,
                    key[0],
                    key[1],
                    key[2],
                    repeats[0],
                    repeats[1],
                    repeats[2],
                    repeats[0],
                    burst,
                )
            )

    if set(by_sequence) != set(accepted):
        raise CompositeError("A4 contact traces do not cover exactly accepted rows")
    for sequence in accepted:
        a5.validate_success_trace_group(sequence, by_sequence[sequence])

    contact_keys = [
        trace_transaction_key(row, "global_seq") for row in contacts
    ]
    gap_keys = [trace_transaction_key(row, "next_global_seq") for row in gaps]
    if len(set(contact_keys)) != len(contact_keys):
        raise CompositeError("A4 contact trace contains a duplicate transaction")
    if len(set(gap_keys)) != len(gap_keys):
        raise CompositeError("A4 gap trace contains a duplicate transaction")
    if gap_keys != contact_keys:
        raise CompositeError("A4 gap/contact transaction order differs")

    gap_events: list[ElectricalEvent] = []
    prior_contact: dict[str, str] | None = None
    for index, (gap, contact, key) in enumerate(zip(gaps, contacts, gap_keys)):
        sequence, acquisition_try, pass_id, contact_id = key
        expected = EXPECTED_BY_SEQ[sequence]
        if exact_int(gap, "schema_version", positive=True) != 1:
            raise CompositeError("A4 gap schema version changed")
        if campaign.angular_error(
            anchor.number(gap, "abs_b_deg"), expected.pose.b_deg
        ) > 0.01 or campaign.angular_error(
            anchor.number(gap, "abs_c_deg"), expected.pose.c_deg
        ) > 0.01:
            raise CompositeError(f"A4 gap sequence {sequence}: pose changed")

        prior = phase_counters(gap, "prior_ready")
        current = phase_counters(gap, "current_pre")
        if any(value < 0 for value in prior + current) or any(
            current[axis] < prior[axis] for axis in range(3)
        ):
            raise CompositeError(
                f"A4 gap sequence {sequence}: counter reversal or negative value"
            )
        delta = tuple(current[axis] - prior[axis] for axis in range(3))
        logged_delta = tuple(
            exact_int(gap, field)
            for field in ("gap_raw_delta", "gap_mux_delta", "gap_gated_delta")
        )
        if logged_delta != delta or not raw_only_delta_valid(delta):
            raise CompositeError(
                f"A4 gap sequence {sequence}: gap is not matched raw/mux-only"
            )

        initial = exact_int(gap, "initial_baseline")
        if initial not in (0, 1) or initial != int(index == 0):
            raise CompositeError("A4 initial-baseline gap identity changed")
        prior_extra = exact_int(gap, "prior_contact_extra_delta")
        if prior_contact is None:
            if prior_extra != 0:
                raise CompositeError("A4 initial gap has nonzero prior-contact extra")
        else:
            if prior != phase_counters(prior_contact, "ready"):
                raise CompositeError("A4 gap prior-ready boundary changed")
            if prior_extra != exact_int(
                prior_contact, "extra_raw_minus_gated_delta"
            ):
                raise CompositeError("A4 prior-contact extra does not carry forward")
        if current != phase_counters(contact, "pre"):
            raise CompositeError("A4 gap current-pre differs from contact trace")

        combined = prior_extra + delta[0]
        if exact_int(gap, "combined_extra_delta") != combined:
            raise CompositeError("A4 combined extra-edge delta changed")
        burst_value = exact_int(gap, "burst_flag")
        if burst_value not in (0, 1) or bool(burst_value) != (combined > 2):
            raise CompositeError("A4 gap burst flag changed")
        if exact_int(gap, "consistency_fault") != 0:
            raise CompositeError("A4 gap contains a forbidden consistency fault")
        if delta[0] != 0 or burst_value:
            gap_events.append(
                ElectricalEvent(
                    "initial-baseline" if initial else "inter-contact",
                    sequence,
                    acquisition_try,
                    pass_id,
                    contact_id,
                    delta[0],
                    delta[1],
                    delta[2],
                    combined,
                    bool(burst_value),
                )
            )
        prior_contact = contact

    return ElectricalDiagnostics(tuple(contact_events), tuple(gap_events))


def validate_a4_complete() -> SegmentValidation:
    with validator_context(A4_MODE, A4_ATTEMPT, A4_SEQUENCES, A4_TRACE, A4_GAP_TRACE):
        spec = run_spec(
            "T3 exploratory attempt 4 recovery",
            A4_MODE,
            A4_RESULTS,
            A4_STATE,
            A4_CLOSURES,
            A4_SEQUENCES,
        )
        centers, closure_norms, accepted = a5.validate_acquisition(
            spec,
            A4_SEQUENCES,
            A4_LOCAL_CLOSURES,
        )
        if accepted != list(A4_SEQUENCES):
            raise CompositeError("A4 accepted rows are not exactly seq23-31")
        trace_rows = a5.read_identity_rows(
            A4_TRACE, a5.TRACE_FIELDS, A4_MODE, A4_ATTEMPT
        )
        gap_rows = a5.read_identity_rows(
            A4_GAP_TRACE, a5.GAP_TRACE_FIELDS, A4_MODE, A4_ATTEMPT
        )
        result_rows = a5.read_identity_rows(
            A4_RESULTS, anchor.RESULT_FIELDS, A4_MODE, A4_ATTEMPT
        )
        center_deltas = pass_center_deltas(result_rows, A4_SEQUENCES)
        rejected, rejected_transactions = retry_trace_summary(trace_rows)
        contact_count = len(trace_rows)
        gap_count = len(gap_rows)
        if contact_count != 72 + rejected_transactions or gap_count != contact_count:
            raise CompositeError("A4 trace count does not match its validated retry shapes")
        electrical = validate_burst_tolerant_complete_traces(
            accepted, trace_rows, gap_rows
        )
    return SegmentValidation(
        centers,
        center_deltas,
        closure_norms,
        contact_count,
        gap_count,
        rejected,
        electrical,
    )


def compose_centers(
    a1_centers: dict[int, np.ndarray],
    a2_centers: dict[int, np.ndarray],
    a4_centers: dict[int, np.ndarray],
) -> dict[int, np.ndarray]:
    if set(a1_centers) != set(A1_SEQUENCES):
        raise CompositeError("A1 composite ownership changed")
    if set(a2_centers) != set(A2_SEQUENCES):
        raise CompositeError("A2 composite ownership changed")
    if set(a4_centers) != set(A4_SEQUENCES):
        raise CompositeError("A4 composite ownership changed")
    source_sets = (set(a1_centers), set(a2_centers), set(a4_centers))
    if any(
        source_sets[left] & source_sets[right]
        for left, right in ((0, 1), (0, 2), (1, 2))
    ):
        raise CompositeError("composite sequence sources overlap")
    combined = {**a1_centers, **a2_centers, **a4_centers}
    if set(combined) != set(ALL_SEQUENCES):
        raise CompositeError("composite does not cover exactly seq1-31")
    return combined


def closure_delta(
    centers: dict[int, np.ndarray], first: int, last: int
) -> tuple[np.ndarray, float]:
    delta = centers[last] - centers[first]
    return delta, float(np.linalg.norm(delta))


def source_identity(seq: int) -> str:
    if seq in A1_SEQUENCES:
        return "mode30/attempt1"
    if seq in A2_SEQUENCES:
        return "mode31/attempt2"
    if seq in A4_SEQUENCES:
        return "mode31/attempt4"
    raise CompositeError(f"sequence {seq} has no acquisition source")


def validate_closure_partition() -> None:
    local = A1_LOCAL_CLOSURES + A2_LOCAL_CLOSURES + A4_LOCAL_CLOSURES
    combined = local + CROSS_SOURCE_CLOSURES
    if len(set(combined)) != 14 or set(combined) != set(frozen_t3.CLOSURE_CONTRACT):
        raise CompositeError("four-local/ten-cross closure partition changed")
    if any(source_identity(first) != source_identity(last) for _, first, last in local):
        raise CompositeError("source-local closure crosses acquisition sources")
    if any(source_identity(first) == source_identity(last) for _, first, last in CROSS_SOURCE_CLOSURES):
        raise CompositeError("cross-source diagnostic no longer crosses acquisition sources")


def local_contrasts(
    centers: dict[int, np.ndarray],
) -> dict[tuple[int, int], np.ndarray]:
    """Return D(B,C) against the mean of each block's two C0 centers."""
    contrasts: dict[tuple[int, int], np.ndarray] = {}
    for b_deg, (opening, middle, closing) in TILT_BLOCK_SEQUENCES.items():
        required = {opening, closing, *middle.values()}
        if not required.issubset(centers):
            raise CompositeError(f"local contrast B{b_deg} lacks required centers")
        c0_mean = (centers[opening] + centers[closing]) / 2.0
        for c_deg in CONTRAST_C_ANGLES:
            contrasts[(b_deg, c_deg)] = centers[middle[c_deg]] - c0_mean
    if len(contrasts) != 12:
        raise CompositeError("local contrast contract is not exactly 12 vectors")
    return contrasts


def paired_sign_components(
    contrasts: dict[tuple[int, int], np.ndarray],
) -> dict[tuple[int, int], tuple[np.ndarray, np.ndarray]]:
    """Return even and odd paired-sign components for abs(B)=45/90."""
    paired: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}
    for abs_b in (45, 90):
        for c_deg in CONTRAST_C_ANGLES:
            positive = contrasts[(abs_b, c_deg)]
            negative = contrasts[(-abs_b, c_deg)]
            paired[(abs_b, c_deg)] = (
                (positive + negative) / 2.0,
                (positive - negative) / 2.0,
            )
    return paired


def norm_ratio(numerator: np.ndarray, denominator: np.ndarray) -> float | None:
    denominator_norm = float(np.linalg.norm(denominator))
    if denominator_norm <= 1e-12:
        return None
    return float(np.linalg.norm(numerator)) / denominator_norm


def matching_t4_context(keys: Sequence[tuple[int, int]]) -> MatchedT4:
    """Select immutable mode-23 T4 rows on the frozen 31-occurrence grid."""
    rows = anchor.read_rows(frozen_t3.T4_RESULTS, anchor.RESULT_FIELDS)
    queues: dict[tuple[int, int], list[tuple[int, np.ndarray, float]]] = {}
    for row in rows:
        for field, expected in (
            ("campaign_id", 2026082404),
            ("stage_mode", 23),
            ("attempt_id", 1),
            ("live_tool_number", 4),
        ):
            if exact_int(row, field, positive=True) != expected:
                raise CompositeError(f"immutable T4 baseline {field} changed")
        source_seq = exact_int(row, "sample_seq", positive=True)
        key = frozen_t3.canonical_pose(
            anchor.number(row, "abs_b_deg"), anchor.number(row, "abs_c_deg")
        )
        center = np.array(
            [
                anchor.number(row, field)
                for field in (
                    "center_abs_x_mm",
                    "center_abs_y_mm",
                    "center_abs_z_mm",
                )
            ]
        )
        delta = anchor.bounded(row, "pass_center_delta_mm", 0.0, 0.100)
        queues.setdefault(key, []).append((source_seq, center, delta))

    centers: dict[int, np.ndarray] = {}
    deltas: dict[int, float] = {}
    source_sequences: dict[int, int] = {}
    used: dict[tuple[int, int], int] = {}
    for target_seq, key in zip(ALL_SEQUENCES, keys):
        index = used.get(key, 0)
        if key not in queues or index >= len(queues[key]):
            raise CompositeError(f"immutable T4 baseline lacks occurrence {index + 1} for {key}")
        source_seq, center, delta = queues[key][index]
        centers[target_seq] = center
        deltas[target_seq] = delta
        source_sequences[target_seq] = source_seq
        used[key] = index + 1

    frozen_centers = frozen_t3.matching_t4_raw(keys)
    selected = np.array([centers[seq] for seq in ALL_SEQUENCES])
    if np.max(np.linalg.norm(selected - frozen_centers, axis=1)) > 1e-12:
        raise CompositeError("T4 diagnostic occurrence selection differs from frozen scorer")
    return MatchedT4(centers, deltas, source_sequences)


def rms_max(vectors: np.ndarray) -> tuple[float, float]:
    norms = np.linalg.norm(vectors, axis=1)
    return float(math.sqrt(np.mean(norms * norms))), float(np.max(norms))


def overlap_sensitivity(centers: dict[int, np.ndarray]) -> OverlapSensitivity:
    pairs = (
        (centers[11], centers[15]),
        (
            np.mean([centers[1], centers[5]], axis=0),
            np.mean([centers[16], centers[27], centers[31]], axis=0),
        ),
        (centers[2], centers[28]),
        (centers[3], centers[29]),
        (centers[4], centers[30]),
    )
    a1_values = np.array([pair[0] for pair in pairs])
    a2_values = np.array([pair[1] for pair in pairs])
    translation = np.mean(a1_values - a2_values, axis=0)
    raw_rms, raw_max = rms_max(a2_values - a1_values)
    aligned_rms, aligned_max = rms_max(a2_values + translation - a1_values)
    return OverlapSensitivity(
        translation, raw_rms, raw_max, aligned_rms, aligned_max
    )


def score_direct_composite(centers: dict[int, np.ndarray]) -> Score:
    """Apply the original frozen no-fit R2 counterfactual without source alignment."""
    raw = np.array([centers[seq] for seq in ALL_SEQUENCES])
    raw_keys = frozen_t3.expected_pose_keys()
    unique_keys, unique = frozen_t3.unique_means(raw, raw_keys)
    if len(unique_keys) != 20:
        raise CompositeError("31-row composite did not reduce to 20 unique poses")
    deltas = frozen_t3.read_r2_delta_map(unique_keys)
    raw_r2_values = np.array(
        [value + deltas[key] for value, key in zip(raw, raw_keys)]
    )
    unique_r2_values = np.array(
        [value + deltas[key] for value, key in zip(unique, unique_keys)]
    )

    raw_base = frozen_t3.metric(raw)
    raw_r2 = frozen_t3.metric(raw_r2_values)
    equal_base = frozen_t3.metric(unique)
    equal_r2 = frozen_t3.metric(unique_r2_values)

    t4_raw = frozen_t3.matching_t4_raw(raw_keys)
    t4_keys, t4_unique = frozen_t3.unique_means(t4_raw, raw_keys)
    if t4_keys != unique_keys:
        raise CompositeError("T3/T4 matching-grid unique pose order differs")
    for actual, expected, label in (
        (frozen_t3.metric(t4_raw), frozen_t3.T4_RAW_BASE, "raw31 baseline"),
        (frozen_t3.metric(t4_unique), frozen_t3.T4_EQ_BASE, "equal20 baseline"),
    ):
        if max(abs(actual[index] - expected[index]) for index in range(2)) > 1e-9:
            raise CompositeError(f"sealed T4 {label} comparator changed: {actual}")

    mismatch_vectors = frozen_t3.centered(unique) - frozen_t3.centered(t4_unique)
    mismatch = rms_max(mismatch_vectors)

    base_residual = frozen_t3.centered(unique)
    r2_residual = frozen_t3.centered(unique_r2_values)
    base_norm = np.linalg.norm(base_residual, axis=1)
    r2_norm = np.linalg.norm(r2_residual, axis=1)
    worsening = r2_norm - base_norm
    plus = [index for index, key in enumerate(unique_keys) if key[0] > 0]
    minus = [index for index, key in enumerate(unique_keys) if key[0] < 0]
    bzero = [index for index, key in enumerate(unique_keys) if key[0] == 0]
    plus_improvement = 1.0 - (
        frozen_t3.subgroup_rms(unique_r2_values, plus)
        / frozen_t3.subgroup_rms(unique, plus)
    )
    minus_improvement = 1.0 - (
        frozen_t3.subgroup_rms(unique_r2_values, minus)
        / frozen_t3.subgroup_rms(unique, minus)
    )
    bzero_worsening = (
        frozen_t3.subgroup_rms(unique_r2_values, bzero)
        - frozen_t3.subgroup_rms(unique, bzero)
    )
    rms_improvement = equal_base[0] - equal_r2[0]
    max_improvement = equal_base[1] - equal_r2[1]
    gates = {
        "equal20 RMS improvement": (
            rms_improvement >= 0.010
            and rms_improvement / equal_base[0] >= 0.10
        ),
        "equal20 max improvement": (
            max_improvement >= 0.020
            and max_improvement / equal_base[1] >= 0.10
        ),
        "positive-B RMS improvement": plus_improvement >= 0.10,
        "negative-B RMS improvement": minus_improvement >= 0.10,
        "B0 RMS non-worsening": bzero_worsening <= 0.010,
        "maximum pose worsening": float(np.max(worsening)) <= 0.075,
        "equal20 ceiling": equal_r2[0] <= 0.120 and equal_r2[1] <= 0.280,
        "raw31 ceiling": raw_r2[0] <= 0.120 and raw_r2[1] <= 0.280,
    }
    if all(gates.values()):
        classification = "SUPPORTIVE"
    elif equal_r2[0] < equal_base[0]:
        classification = "MIXED"
    else:
        classification = "ADVERSE"
    worst_index = int(np.argmax(worsening))
    return Score(
        classification,
        raw_base,
        raw_r2,
        equal_base,
        equal_r2,
        mismatch,
        gates,
        float(worsening[worst_index]),
        unique_keys[worst_index],
    )


def validate_frozen_dependencies() -> None:
    require_hash(FROZEN_T3_ANALYZER, EXPECTED_HASHES[FROZEN_T3_ANALYZER])
    require_hash(A5_ANALYZER, EXPECTED_HASHES[A5_ANALYZER])
    frozen_t3.validate_config()


def write_preflight_report(
    path: Path,
    a1: SegmentValidation,
    a2: SegmentValidation,
    a3_forensic: SegmentValidation,
) -> None:
    lines = [
        "# T3 R2-Transfer Attempt-4 Recovery Preflight",
        "",
        "- status: `PASS`",
        "- disposition: `R2 NOT ACCEPTED`",
        f"- campaign/mode/attempt: `{CAMPAIGN}/{A4_MODE}/{A4_ATTEMPT}`",
        f"- recovery runner SHA-256: `{sha256(A4_PROGRAM)}`",
        f"- A1 archive `SHA256SUMS` SHA-256: `{sha256(A1_SUMS)}`",
        f"- sealed A1 results/state/local closures: `{len(a1.centers)} / {len(a1.centers)} / {len(a1.closure_norms)}`",
        f"- sealed A1 contact/gap rows: `{a1.contact_rows} / {a1.gap_rows}`",
        "- sealed A1 terminal: `seq15 try1/pass2/contact3 no touch; 6.000000 mm`",
        f"- A2 archive `SHA256SUMS` SHA-256: `{sha256(A2_PARTIAL_SUMS)}`",
        f"- sealed A2 results/state/local closures: `{len(a2.centers)} / {len(a2.centers)} / {len(a2.closure_norms)}`",
        f"- sealed A2 contact/gap rows: `{a2.contact_rows} / {a2.gap_rows}`",
        "- sealed A2 terminal: `seq23 try1/pass1/contact1 pre-G38 gap burst; raw/mux/gated delta 4/4/0`",
        f"- A3 forensic archive `SHA256SUMS` SHA-256: `{sha256(A3_PARTIAL_SUMS)}`",
        f"- sealed A3 accepted centers/contact/gap rows: `{len(a3_forensic.centers)} / {a3_forensic.contact_rows} / {a3_forensic.gap_rows}`",
        "- sealed A3 terminal: `zero accepted; seq23 try1/pass1/contact3 pre-G38 gap burst 5/5/0`",
        "- fresh A4 outputs: `five exact header-only files`",
        "- A4 accepted-row contract: `global seq23-31; 9 results and 9 states`",
        "- A4 source-local closure order: `200`",
        "- A4 electrical policy: `direct 1/1/1 required; matched raw/mux-only repeats and gaps retained as diagnostics`",
        "- composite closure contract: `4 validated source-local + 10 offline cross-source`",
        "- formal same-acquisition 31/31/14: `cannot be satisfied by this three-source recovery`",
        "- motion boundary: `one M0; no axis, rotary, or probe motion before M0`",
        "- parser boundary: `static Python checks only; rs274/LinuxCNC/HAL not invoked`",
        f"- analyzer SHA-256 at execution: `{sha256(Path(__file__))}`",
        "",
        "The runner starts from the operator-established B-90/C90 top-clear point",
        "for the sequence-23 restart. Loading this file authorizes no motion. The operator",
        "owns Cycle Start, Resume, Hold, Abort, jog, MDI, and machine observation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="ascii")


def format_closure_row(
    scope: str,
    centers: dict[int, np.ndarray],
    closure: tuple[int, int, int],
    formal_pass: str,
) -> str:
    block, first, last = closure
    delta, norm = closure_delta(centers, first, last)
    opening = f"{source_identity(first)}/seq{first}"
    closing = f"{source_identity(last)}/seq{last}"
    return (
        f"| {scope} | {block} | {opening} | {closing} | "
        f"{delta[0]:.6f} | {delta[1]:.6f} | {delta[2]:.6f} | "
        f"{norm:.6f} | {formal_pass} |"
    )


def vector_cells(vector: np.ndarray) -> str:
    return (
        f"{vector[0]:.6f} | {vector[1]:.6f} | {vector[2]:.6f} | "
        f"{float(np.linalg.norm(vector)):.6f}"
    )


def ratio_text(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.6f}"


def write_result_report(
    path: Path,
    a1: SegmentValidation,
    a2: SegmentValidation,
    a3_forensic: SegmentValidation,
    a4: SegmentValidation,
    centers: dict[int, np.ndarray],
    score: Score,
    sensitivity: OverlapSensitivity,
    t4: MatchedT4,
) -> None:
    local_norms = np.concatenate(
        (a1.closure_norms, a2.closure_norms, a4.closure_norms)
    )
    t3_pass_deltas = {
        **a1.pass_center_deltas,
        **a2.pass_center_deltas,
        **a4.pass_center_deltas,
    }
    if set(t3_pass_deltas) != set(ALL_SEQUENCES):
        raise CompositeError("composite pass-center context does not cover seq1-31")
    t3_contrasts = local_contrasts(centers)
    t4_contrasts = local_contrasts(t4.centers)
    t3_paired = paired_sign_components(t3_contrasts)
    t4_paired = paired_sign_components(t4_contrasts)

    a1_delta_values = np.array(list(a1.pass_center_deltas.values()))
    a2_delta_values = np.array(list(a2.pass_center_deltas.values()))
    a4_delta_values = np.array(list(a4.pass_center_deltas.values()))
    t3_delta_values = np.array([t3_pass_deltas[seq] for seq in ALL_SEQUENCES])
    t4_delta_values = np.array([t4.pass_center_deltas[seq] for seq in ALL_SEQUENCES])
    lines = [
        "# T3 R2-Transfer Attempt-4 Three-Source Composite Report",
        "",
        "## R2 NOT ACCEPTED",
        "",
        f"- exploratory classification: `{score.classification}`",
        "- direct composite: `A1 seq1-14 + A2 seq15-22 + A4 seq23-31; no source alignment`",
        "- composite result/state rows: `31 / 31`",
        "- formal same-acquisition `31 / 31 / 14`: `NOT SATISFIED`",
        "- reason: accepted rows span mode30/attempt1, mode31/attempt2, and mode31/attempt4; only four closures are validated within one source",
        "- validated source-local/cross-source diagnostics: `4 / 10`",
        f"- A1 contact/gap rows: `{a1.contact_rows} / {a1.gap_rows}`",
        f"- A2 contact/gap rows: `{a2.contact_rows} / {a2.gap_rows}`",
        f"- A3 forensic accepted/contact/gap rows: `{len(a3_forensic.centers)} / {a3_forensic.contact_rows} / {a3_forensic.gap_rows}`",
        f"- A4 contact/gap rows: `{a4.contact_rows} / {a4.gap_rows}`",
        f"- A4 complete rejected try-1 poses: `{a4.rejected_try1_poses}`",
        f"- maximum validated source-local closure: `{float(np.max(local_norms)):.6f} mm`",
        f"- equal-20 baseline RMS/max: `{score.equal_base[0]:.9f} / {score.equal_base[1]:.9f} mm`",
        f"- equal-20 R2 counterfactual RMS/max: `{score.equal_r2[0]:.9f} / {score.equal_r2[1]:.9f} mm`",
        f"- raw-31 baseline RMS/max: `{score.raw_base[0]:.9f} / {score.raw_base[1]:.9f} mm`",
        f"- raw-31 R2 counterfactual RMS/max: `{score.raw_r2[0]:.9f} / {score.raw_r2[1]:.9f} mm`",
        f"- centered T3-minus-T4 equal-20 mismatch RMS/max: `{score.mismatch[0]:.9f} / {score.mismatch[1]:.9f} mm`",
        f"- maximum unique-pose worsening: `{score.maximum_worsening:.9f} mm` at `{score.maximum_worsening_pose}`",
        "",
        "## Closure Diagnostics",
        "",
        "| scope | block | opening provenance | closing provenance | dx mm | dy mm | dz mm | norm mm | formal_pass |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for closure in A1_LOCAL_CLOSURES + A2_LOCAL_CLOSURES + A4_LOCAL_CLOSURES:
        lines.append(
            format_closure_row("validated source-local", centers, closure, "PASS")
        )
    for closure in CROSS_SOURCE_CLOSURES:
        lines.append(format_closure_row("cross-source", centers, closure, "N/A"))

    lines += [
        "",
        "The four validated source-local PASS values apply only to their original",
        "source acquisition. They do not convert this split composite into formal",
        "same-acquisition evidence. Cross-source `formal_pass=N/A` is retained.",
        "",
        "Cross-source rows are offline diagnostics with explicit provenance.",
        "They are not controller closure rows, and the 0.050 mm same-acquisition",
        "closure limit is not applied to them.",
        "",
        "## Pass-Center Context",
        "",
        f"- T3 A1 seq1-14 min/max: `{float(np.min(a1_delta_values)):.6f} / {float(np.max(a1_delta_values)):.6f} mm`",
        f"- T3 A2 seq15-22 min/max: `{float(np.min(a2_delta_values)):.6f} / {float(np.max(a2_delta_values)):.6f} mm`",
        f"- T3 A4 seq23-31 min/max: `{float(np.min(a4_delta_values)):.6f} / {float(np.max(a4_delta_values)):.6f} mm`",
        f"- T3 composite min/max: `{float(np.min(t3_delta_values)):.6f} / {float(np.max(t3_delta_values)):.6f} mm`",
        f"- immutable T4 matching-grid min/max: `{float(np.min(t4_delta_values)):.6f} / {float(np.max(t4_delta_values)):.6f} mm`",
        "",
        "| T3 seq | pose | readout | T3 provenance | T3 pass-center delta mm | T4 mode23 source seq | T4 pass-center delta mm |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for seq, key in zip(ALL_SEQUENCES, frozen_t3.expected_pose_keys()):
        marker = "PRIMARY" if seq in (19, 24) else ""
        lines.append(
            f"| {seq} | B{key[0]:+d}/C{key[1]} | {marker} | "
            f"{source_identity(seq)} | {t3_pass_deltas[seq]:.6f} | "
            f"{t4.source_sequences[seq]} | {t4.pass_center_deltas[seq]:.6f} |"
        )

    lines += [
        "",
        "Pass-center deltas are preserved repeatability context, not exclusion",
        "weights. Seq19 B+90/C180 and seq24 B-90/C180 remain mandatory readouts.",
        "",
        "## Local Contrasts",
        "",
        "`D(B,C) = center(B,C) - mean(center(B,C0-open), center(B,C0-close))`.",
        "The immutable T4 reference uses the same 31 occurrence keys selected by",
        "the frozen scorer from the sealed mode23/attempt1 acquisition.",
        "",
        "| pose | readout | T3 dx mm | T3 dy mm | T3 dz mm | T3 norm mm | T4 dx mm | T4 dy mm | T4 dz mm | T4 norm mm | T3-T4 dx mm | T3-T4 dy mm | T3-T4 dz mm | T3-T4 norm mm |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for b_deg in (45, -45, 90, -90):
        for c_deg in CONTRAST_C_ANGLES:
            key = (b_deg, c_deg)
            if b_deg in (-45, -90):
                if key == (-90, 180):
                    marker = "PRIMARY CROSS-SOURCE-SENSITIVE"
                else:
                    marker = "CROSS-SOURCE-SENSITIVE"
            elif key == (90, 180):
                marker = "PRIMARY SOURCE-LOCAL"
            else:
                marker = "SOURCE-LOCAL"
            difference = t3_contrasts[key] - t4_contrasts[key]
            lines.append(
                f"| B{b_deg:+d}/C{c_deg} | {marker} | "
                f"{vector_cells(t3_contrasts[key])} | "
                f"{vector_cells(t4_contrasts[key])} | "
                f"{vector_cells(difference)} |"
            )

    lines += [
        "",
        "Every contrast cancels one common global translation. T3 D(-45,C) is",
        "nevertheless CROSS-SOURCE-SENSITIVE because its C0 opening seq11 is A1",
        "and its C0 closing seq15 is A2. T3 D(-90,C) is also",
        "CROSS-SOURCE-SENSITIVE: its C0 opening seq22 is A2, while its tilted",
        "centers and C0 closing seq26 are A4. D(+45,C) and D(+90,C) are",
        "source-local and invariant to a constant translation of their own source. The T4",
        "contrasts are all source-local. No contrast, quadrant, or T3-minus-T4",
        "value adds an acceptance gate or receives a source-alignment correction.",
        "",
        "## Paired-Sign Components",
        "",
        "`even=(D(+B,C)+D(-B,C))/2`; `odd=(D(+B,C)-D(-B,C))/2`.",
        "",
        "| abs(B) | C | readout | T3 even x mm | T3 even y mm | T3 even z mm | T3 even norm mm | T3 odd x mm | T3 odd y mm | T3 odd z mm | T3 odd norm mm |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for abs_b in (45, 90):
        for c_deg in CONTRAST_C_ANGLES:
            even, odd = t3_paired[(abs_b, c_deg)]
            marker = (
                "PRIMARY CROSS-SOURCE-SENSITIVE"
                if abs_b == 90 and c_deg == 180
                else "CROSS-SOURCE-SENSITIVE"
            )
            lines.append(
                f"| {abs_b} | {c_deg} | {marker} | "
                f"{vector_cells(even)} | {vector_cells(odd)} |"
            )

    lines += [
        "",
        "| abs(B) | C | readout | T4 even x mm | T4 even y mm | T4 even z mm | T4 even norm mm | T4 odd x mm | T4 odd y mm | T4 odd z mm | T4 odd norm mm | T3-T4 even norm mm | T3-T4 odd norm mm |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for abs_b in (45, 90):
        for c_deg in CONTRAST_C_ANGLES:
            t3_even, t3_odd = t3_paired[(abs_b, c_deg)]
            t4_even, t4_odd = t4_paired[(abs_b, c_deg)]
            marker = (
                "T3 PRIMARY CROSS-SOURCE-SENSITIVE"
                if abs_b == 90 and c_deg == 180
                else "T3 CROSS-SOURCE-SENSITIVE"
            )
            lines.append(
                f"| {abs_b} | {c_deg} | {marker} | "
                f"{vector_cells(t4_even)} | {vector_cells(t4_odd)} | "
                f"{float(np.linalg.norm(t3_even - t4_even)):.6f} | "
                f"{float(np.linalg.norm(t3_odd - t4_odd)):.6f} |"
            )

    lines += [
        "",
        "B+90/C180 and B-90/C180 contribute explicitly to the abs(B)=90/C180",
        "even/odd row; neither pose is searched for or excluded after acquisition.",
        "Every T3 even/odd row inherits a negative-sign acquisition boundary:",
        "D(-45,C) spans A1/A2 and D(-90,C) spans A2/A4. No source translation",
        "is applied.",
        "",
        "## B45-vs-B90 Angle Scale",
        "",
        "Diagnostic only. `delta D = D(sign*90,C) - D(sign*45,C)` and the",
        "reported ratio is `||D(sign*90,C)|| / ||D(sign*45,C)||`. No value in",
        "this table is an acceptance gate, fitted scale, or coefficient update.",
        "",
        "| data | B sign | C | sensitivity | delta-D x mm | delta-D y mm | delta-D z mm | delta-D norm mm | norm ratio B90/B45 |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, contrasts in (("T3 composite", t3_contrasts), ("T4 mode23", t4_contrasts)):
        for sign in (1, -1):
            for c_deg in CONTRAST_C_ANGLES:
                low = contrasts[(sign * 45, c_deg)]
                high = contrasts[(sign * 90, c_deg)]
                difference = high - low
                if label == "T3 composite" and sign < 0:
                    sensitivity_label = "CROSS-SOURCE-SENSITIVE"
                else:
                    sensitivity_label = "SOURCE-LOCAL"
                lines.append(
                    f"| {label} | {'+' if sign > 0 else '-'} | {c_deg} | "
                    f"{sensitivity_label} | "
                    f"{vector_cells(difference)} | {ratio_text(norm_ratio(high, low))} |"
                )

    lines += [
        "",
        "All negative-sign T3 B45-vs-B90 rows combine split-source D(-45,C)",
        "and D(-90,C) references. Their vector differences and norm ratios remain unaligned",
        "diagnostics and do not enter the frozen gates.",
    ]

    contact_events = a4.electrical.contact_repeat_events
    gap_events = a4.electrical.gap_events
    lines += [
        "",
        "## Electrical Burst Diagnostics",
        "",
        "A4 requires every successful direct G38 edge delta to be exactly",
        "raw/mux/gated 1/1/1. Matched raw/mux post-contact repeats and",
        "inter-contact gaps with gated delta 0 remain diagnostic even when their",
        "logged burst flag is 1. Raw/mux mismatch, gated repeat/gap activity,",
        "counter reversal, consistency, release, terminal, or no-touch evidence",
        "is invalid.",
        "",
        f"- post-contact repeat events / burst rows / raw edges: `{len(contact_events)} / {sum(int(event.burst) for event in contact_events)} / {sum(event.raw_delta for event in contact_events)}`",
        f"- gap events / burst rows / raw edges: `{len(gap_events)} / {sum(int(event.burst) for event in gap_events)} / {sum(event.raw_delta for event in gap_events)}`",
        "",
        "| scope | seq | try | pass | contact | raw delta | mux delta | gated delta | combined extra | burst |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    electrical_events = contact_events + gap_events
    if electrical_events:
        for event in electrical_events:
            lines.append(
                f"| {event.scope} | {event.sequence} | {event.acquisition_try} | "
                f"{event.pass_id} | {event.contact_id} | {event.raw_delta} | "
                f"{event.mux_delta} | {event.gated_delta} | "
                f"{event.combined_extra} | {int(event.burst)} |"
            )
    else:
        lines.append("| none | N/A | N/A | N/A | N/A | 0 | 0 | 0 | 0 | 0 |")
    lines += [
        "",
        "These rows are preserved acquisition diagnostics only. They do not",
        "alter source alignment, closure treatment, the frozen score, or gates.",
    ]

    lines += [
        "",
        "## Frozen Gates",
        "",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'}: {name}"
        for name, passed in score.gates.items()
    )
    lines += [
        "",
        "## Overlap Sensitivity",
        "",
        "This optional five-pose, equal-weight recovery-to-A1 translation is reported",
        "only as acquisition-boundary sensitivity. The recovery side is explicitly",
        "mixed-source: A2 supplies B-45/C0 and B0/C0 seq16; A4 supplies the closing",
        "B0 sweep, while the B0/C0 recovery value averages A2 and A4 occurrences.",
        "It was not used for closures,",
        "gates, classification, centering, or the frozen R2 score.",
        "",
        f"- estimated mixed-recovery-to-A1 translation XYZ: `{sensitivity.translation[0]:.9f}, {sensitivity.translation[1]:.9f}, {sensitivity.translation[2]:.9f} mm`",
        f"- overlap unaligned RMS/max: `{sensitivity.raw_rms:.9f} / {sensitivity.raw_max:.9f} mm`",
        f"- overlap translation-aligned RMS/max: `{sensitivity.aligned_rms:.9f} / {sensitivity.aligned_max:.9f} mm`",
        "",
        "The counterfactual adds the immutable, pose-keyed T4 R2 deltas to the",
        "direct composite T3 centers using the original single global centering.",
        "No T3 coefficient, rotation, scale, row deletion, or per-source",
        "translation was fitted. This report cannot accept R2 or authorize a",
        "machine calibration parameter change.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="ascii")


def preflight(report: Path) -> None:
    self_test()
    validate_frozen_dependencies()
    a1 = validate_a1_forensics()
    a2 = validate_a2_partial_forensics()
    a3_forensic = validate_a3_partial_forensics()
    validate_a4_program()
    validate_a4_headers()
    write_preflight_report(report, a1, a2, a3_forensic)


def analyze(report: Path) -> None:
    self_test()
    validate_frozen_dependencies()
    a1 = validate_a1_forensics()
    a2 = validate_a2_partial_forensics()
    a3_forensic = validate_a3_partial_forensics()
    validate_a4_program()
    a4 = validate_a4_complete()
    centers = compose_centers(a1.centers, a2.centers, a4.centers)
    score = score_direct_composite(centers)
    sensitivity = overlap_sensitivity(centers)
    t4 = matching_t4_context(frozen_t3.expected_pose_keys())
    write_result_report(
        report, a1, a2, a3_forensic, a4, centers, score, sensitivity, t4
    )


def self_test() -> None:
    if len(EXPECTED_ROWS) != 31 or tuple(row.seq for row in EXPECTED_ROWS) != ALL_SEQUENCES:
        raise CompositeError("31-row T3 pose contract changed")
    if A1_SEQUENCES + A2_SEQUENCES + A4_SEQUENCES != ALL_SEQUENCES:
        raise CompositeError("A1/A2/A4 sequence ownership is not an exact partition")
    validate_closure_partition()
    keys = frozen_t3.expected_pose_keys()
    if len(dict.fromkeys(keys)) != 20:
        raise CompositeError("T3 20-unique-pose contract changed")

    synthetic = {
        seq: np.array([float(seq), float(seq % 4), -float(seq % 7)])
        for seq in ALL_SEQUENCES
    }
    composed = compose_centers(
        {seq: synthetic[seq] for seq in A1_SEQUENCES},
        {seq: synthetic[seq] for seq in A2_SEQUENCES},
        {seq: synthetic[seq] for seq in A4_SEQUENCES},
    )
    if any(np.linalg.norm(composed[seq] - synthetic[seq]) > 1e-12 for seq in ALL_SEQUENCES):
        raise CompositeError("direct composite changed a source center")

    translation = np.array([0.25, -0.5, 1.0])
    overlap_fixture = {seq: np.zeros(3) for seq in ALL_SEQUENCES}
    for seq in A2_SEQUENCES + A4_SEQUENCES:
        overlap_fixture[seq] = -translation
    sensitivity = overlap_sensitivity(overlap_fixture)
    if np.linalg.norm(sensitivity.translation - translation) > 1e-12:
        raise CompositeError("overlap translation direction/weighting changed")
    if sensitivity.aligned_max > 1e-12:
        raise CompositeError("overlap translation sensitivity failed synthetic closure")

    base_contrasts = local_contrasts(synthetic)
    shifted_contrasts = local_contrasts(
        {seq: center + translation for seq, center in synthetic.items()}
    )
    if any(
        np.linalg.norm(base_contrasts[key] - shifted_contrasts[key]) > 1e-12
        for key in base_contrasts
    ):
        raise CompositeError("local contrasts are not globally translation invariant")

    a2_translation = np.array([0.20, -0.40, 0.80])
    a4_translation = np.array([-0.30, 0.60, -1.20])
    boundary_shifted = {}
    for seq, center in synthetic.items():
        if seq in A2_SEQUENCES:
            boundary_shifted[seq] = center + a2_translation
        elif seq in A4_SEQUENCES:
            boundary_shifted[seq] = center + a4_translation
        else:
            boundary_shifted[seq] = center
    boundary_contrasts = local_contrasts(boundary_shifted)
    for key in base_contrasts:
        if key[0] == -45:
            expected_change = -a2_translation / 2.0
        elif key[0] == -90:
            expected_change = (a4_translation - a2_translation) / 2.0
        else:
            expected_change = np.zeros(3)
        actual_change = boundary_contrasts[key] - base_contrasts[key]
        if np.linalg.norm(actual_change - expected_change) > 1e-12:
            raise CompositeError(
                "local contrast split-source translation sensitivity changed"
            )
    base_paired = paired_sign_components(base_contrasts)
    boundary_paired = paired_sign_components(boundary_contrasts)
    for key in base_paired:
        if key[0] == 45:
            expected_even_change = -a2_translation / 4.0
            expected_odd_change = a2_translation / 4.0
        else:
            expected_even_change = (a4_translation - a2_translation) / 4.0
            expected_odd_change = -(a4_translation - a2_translation) / 4.0
        if (
            np.linalg.norm(
                boundary_paired[key][0] - base_paired[key][0] - expected_even_change
            )
            > 1e-12
            or np.linalg.norm(
                boundary_paired[key][1] - base_paired[key][1] - expected_odd_change
            )
            > 1e-12
        ):
            raise CompositeError("paired-sign split-source sensitivity changed")
    for sign in (1, -1):
        for c_deg in CONTRAST_C_ANGLES:
            base_difference = (
                base_contrasts[(sign * 90, c_deg)]
                - base_contrasts[(sign * 45, c_deg)]
            )
            boundary_difference = (
                boundary_contrasts[(sign * 90, c_deg)]
                - boundary_contrasts[(sign * 45, c_deg)]
            )
            expected_change = a4_translation / 2.0 if sign < 0 else np.zeros(3)
            if (
                np.linalg.norm(
                    boundary_difference - base_difference - expected_change
                )
                > 1e-12
            ):
                raise CompositeError("B45/B90 split-source sensitivity changed")

    even_odd_fixture: dict[tuple[int, int], np.ndarray] = {}
    expected_components: dict[
        tuple[int, int], tuple[np.ndarray, np.ndarray]
    ] = {}
    for abs_b in (45, 90):
        for c_deg in CONTRAST_C_ANGLES:
            even = np.array([abs_b / 10.0, c_deg / 100.0, 0.25])
            odd = np.array([-c_deg / 200.0, abs_b / 20.0, -0.5])
            even_odd_fixture[(abs_b, c_deg)] = even + odd
            even_odd_fixture[(-abs_b, c_deg)] = even - odd
            expected_components[(abs_b, c_deg)] = (even, odd)
    recovered = paired_sign_components(even_odd_fixture)
    if any(
        np.linalg.norm(recovered[key][index] - expected_components[key][index])
        > 1e-12
        for key in expected_components
        for index in (0, 1)
    ):
        raise CompositeError("paired-sign even/odd decomposition changed")
    if norm_ratio(np.ones(3), np.zeros(3)) is not None:
        raise CompositeError("zero-denominator angle-scale ratio is not N/A")

    matched_t4 = matching_t4_context(keys)
    if (
        set(matched_t4.centers) != set(ALL_SEQUENCES)
        or set(matched_t4.pass_center_deltas) != set(ALL_SEQUENCES)
        or set(matched_t4.source_sequences) != set(ALL_SEQUENCES)
        or len(local_contrasts(matched_t4.centers)) != 12
    ):
        raise CompositeError("immutable T4 matching-grid context changed")

    retry_fixture = (
        [{"global_seq": "15", "acquisition_try": "1"}] * 4
        + [{"global_seq": "15", "acquisition_try": "2"}] * 8
        + [{"global_seq": "16", "acquisition_try": "1"}] * 8
        + [{"global_seq": "16", "acquisition_try": "2"}] * 8
        + [{"global_seq": "17", "acquisition_try": "1"}] * 8
    )
    if retry_trace_summary(retry_fixture) != (2, 12):
        raise CompositeError("four/eight-contact retry accounting changed")

    if not direct_g38_delta_valid((1, 1, 1)) or any(
        direct_g38_delta_valid(delta)
        for delta in ((0, 0, 0), (2, 2, 1), (1, 1, 0), (1, 2, 1))
    ):
        raise CompositeError("A4 exact direct-G38 edge policy changed")
    if any(
        not raw_only_delta_valid(delta)
        for delta in ((0, 0, 0), (1, 1, 0), (5, 5, 0))
    ) or any(
        raw_only_delta_valid(delta)
        for delta in ((1, 0, 0), (0, 1, 0), (1, 1, 1), (-1, -1, 0))
    ):
        raise CompositeError("A4 matched raw/mux-only diagnostic policy changed")

    if a5.gap_evaluation((2, 2, 0), 0)[1]:
        raise CompositeError("contained two-edge gap boundary changed")
    if not a5.gap_evaluation((3, 3, 0), 0)[1]:
        raise CompositeError("greater-than-two burst boundary changed")


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
            print("T3 attempt-4 three-source analyzer self-test: PASS")
            return 0
        if args.preflight:
            preflight(args.preflight_report)
            print("T3 attempt-4 recovery static preflight: PASS")
            print("R2 NOT ACCEPTED")
            print(f"report: {args.preflight_report}")
            return 0
        analyze(args.report)
        print("T3 three-source composite acquisition contract: PASS")
        print("R2 NOT ACCEPTED")
        print(f"report: {args.report}")
        return 0
    except (
        CompositeError,
        frozen_t3.T3Error,
        a5.RecoveryError,
        anchor.ValidationError,
        OSError,
        ValueError,
    ) as exc:
        print(f"T3 attempt-4 composite validation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
