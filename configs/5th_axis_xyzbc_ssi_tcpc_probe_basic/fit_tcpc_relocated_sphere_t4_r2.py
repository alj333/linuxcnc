#!/usr/bin/env python3
"""Select and fit the campaign-04 T4-only TCPC surface revision r2.

This is an offline analysis program. It reads only the frozen campaign-04 T4
inputs and the baseline HAL/program snapshots listed in EXPECTED_SHA256. It has
no T3 input path, imports no LinuxCNC or HAL control API, and cannot edit or load
machine configuration.

Revision r2 supersedes the earlier lambda-30 candidate for operational planning
without modifying any r1 artifact. Model selection uses one equal-weight row per
unique (B, C) pose, a physically admissible 17-term pool, nested grouped
validation, and a hard 0.75 mm modeled-correction bound.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Callable, Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

RESULTS_PATH = HERE / "tcpc-relocated-sphere-t4-primary-results.csv"
STATE_PATH = HERE / "tcpc-relocated-sphere-t4-primary-state.csv"
CLOSURES_PATH = HERE / "tcpc-relocated-sphere-t4-primary-closures.csv"
PROGRAM_PATH = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_primary.ngc"
HAL_PATH = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"

DEFAULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_FIT_R2_REPORT.md"
DEFAULT_RESIDUALS = HERE / "tcpc-relocated-sphere-t4-fit-r2-residuals.csv"
DEFAULT_PINS = HERE / "tcpc-relocated-sphere-t4-fit-r2-pins.csv"
DEFAULT_CHECKPOINT = Path("/tmp/tcpc-relocated-sphere-t4-fit-r2-checkpoint.json")

EXPECTED_SHA256 = {
    RESULTS_PATH: "70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468",
    STATE_PATH: "dd09051f37bfc8c91e13d3617e77bc9e2aea40393237cc935e1350364a73693d",
    CLOSURES_PATH: "f0fd62d8c99259c7ea76d167b1d9ce7ee68825a7cef1234f3ce3906a4a9c3021",
    PROGRAM_PATH: "bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2",
    HAL_PATH: "b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778",
}

CAMPAIGN = 2026082404
MODE = 23
ATTEMPT = 1
REVISION = "r2"
ROW_COUNT = 101
CLOSURE_COUNT = 28
UNIQUE_POSE_COUNT = 76
B_ZERO_DEG = 0.0
C_ZERO_DEG = -0.024500

LAMBDA_GRID = (1.0, 3.0, 10.0, 30.0, 100.0)
MAX_SELECTED_TERMS = 10
MAX_CORRECTION_MM = 0.750
OBJECTIVE_C_WEIGHT = 0.5
TIE_DIGITS = 12
AXES = ("x", "y", "z")

# Pool order is part of the deterministic final tie-break. The two bases that
# need nonzero-B C135/C315 observations are intentionally absent.
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

PIN_STEMS = {
    "c_cos": "headheadkins.charm.cos",
    "c_sin": "headheadkins.charm.sin",
    "c_cos2": "headheadkins.charm.cos2",
    "c_sin2": "headheadkins.charm.sin2",
    "b_sin": "headheadkins.bharm-m.sin",
    "b_omc": "headheadkins.bharm-m.omc",
    "b_sin2": "headheadkins.bharm-m.sin2",
    "bc_sinb_sinc": "headheadkins.bcross.sinb-sinc",
    "bc_omcb_sinc": "headheadkins.bcross.omcb-sinc",
    "bc_omcb_sin2c": "headheadkins.bcross.omcb-sin2c",
    "bc_sinb_cosc": "headheadkins.bcross.sinb-cosc",
    "bc_omcb_cosc": "headheadkins.bcross.omcb-cosc",
    "bc_sinb_cos2c": "headheadkins.bcross.sinb-cos2c",
    "bmid_base": "headheadkins.bmid.base",
    "bmid_cosc": "headheadkins.bmid.cosc",
    "bmid_sinc": "headheadkins.bmid.sinc",
    "bmid_cos2c": "headheadkins.bmid.cos2c",
}

RESULT_CENTER_FIELDS = ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")
RESIDUAL_FIELDS = (
    "campaign_id",
    "attempt_id",
    "fit_revision",
    "sample_seq",
    "abs_b_deg",
    "abs_c_deg",
    "pose_multiplicity",
    "fit_weight",
    "primary_lambda",
    "primary_term_count",
    "center_abs_x_mm",
    "center_abs_y_mm",
    "center_abs_z_mm",
    "current_residual_x_mm",
    "current_residual_y_mm",
    "current_residual_z_mm",
    "current_residual_norm_mm",
    "candidate_delta_x_mm",
    "candidate_delta_y_mm",
    "candidate_delta_z_mm",
    "candidate_delta_norm_mm",
    "candidate_center_x_mm",
    "candidate_center_y_mm",
    "candidate_center_z_mm",
    "candidate_residual_x_mm",
    "candidate_residual_y_mm",
    "candidate_residual_z_mm",
    "candidate_residual_norm_mm",
)

PIN_FIELDS = (
    "campaign_id",
    "fit_revision",
    "operational_status",
    "selected",
    "basis_term",
    "pin",
    "axis",
    "current_mm",
    "delta_mm",
    "predicted_total_mm",
)


class FitError(ValueError):
    pass


@dataclass(frozen=True)
class Observation:
    seq: int
    b_deg: float
    c_deg: float
    center: np.ndarray


@dataclass(frozen=True)
class UniquePose:
    b_deg: float
    c_deg: float
    center: np.ndarray
    sequences: tuple[int, ...]

    @property
    def multiplicity(self) -> int:
        return len(self.sequences)


@dataclass(frozen=True)
class Dataset:
    observations: tuple[Observation, ...]
    poses: tuple[UniquePose, ...]
    b_deg: np.ndarray
    c_deg: np.ndarray
    centers: np.ndarray
    features: np.ndarray


@dataclass(frozen=True)
class Metric:
    rms: float
    maximum: float


@dataclass(frozen=True)
class RidgeFit:
    term_indices: tuple[int, ...]
    ridge_lambda: float
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    standardized_coefficients: np.ndarray
    center_mean: np.ndarray

    @property
    def raw_center_coefficients(self) -> np.ndarray:
        return self.standardized_coefficients / self.feature_scale[:, None]

    @property
    def correction_deltas(self) -> np.ndarray:
        return -self.raw_center_coefficients


@dataclass(frozen=True)
class GroupCv:
    metric: Metric
    maximum_correction: float


@dataclass(frozen=True)
class CandidateEvaluation:
    term_indices: tuple[int, ...]
    ridge_lambda: float
    objective: float
    worst_validation_maximum: float
    maximum_correction: float
    signed_cv: GroupCv
    abs_b_cv: GroupCv
    c_cv: GroupCv
    fit: RidgeFit


@dataclass(frozen=True)
class SelectionResult:
    winner: CandidateEvaluation
    path: tuple[CandidateEvaluation, ...]
    swap_counts: tuple[int, ...]


@dataclass(frozen=True)
class OuterFold:
    group: float
    held_count: int
    selection: CandidateEvaluation
    metric: Metric


@dataclass(frozen=True)
class OuterValidation:
    name: str
    metric: Metric
    worst_group: float
    worst_group_maximum: float
    folds: tuple[OuterFold, ...]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_hashes() -> None:
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256(path)
        if actual != expected:
            raise FitError(
                f"input SHA-256 changed for {path}: {actual}, expected {expected}"
            )


def number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, ValueError) as exc:
        raise FitError(f"invalid numeric field {field!r}") from exc
    if not math.isfinite(value):
        raise FitError(f"non-finite field {field!r}")
    return value


def exact_integer(row: dict[str, str], field: str) -> int:
    value = number(row, field)
    rounded = round(value)
    if abs(value - rounded) > 1e-9:
        raise FitError(f"{field}={value}, expected an exact integer")
    return int(rounded)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise FitError(f"no data rows in {path}")
    return rows


def expected_poses() -> tuple[tuple[float, float], ...]:
    poses: list[tuple[float, float]] = []
    poses.extend((0.0, float(c)) for c in (0, 45, 90, 135, 180, 225, 270, 315, 0))
    for b in (5, -5, 10, -10, 15, -15):
        poses.extend((float(b), float(c)) for c in (0, 45, 90, 180, 225, 270, 0))
    for b in (30, -30, 45, -45):
        poses.extend((float(b), float(c)) for c in (0, 90, 180, 270, 0))
    poses.append((0.0, 0.0))
    for b in (60, -60, 90, -90):
        poses.extend((float(b), float(c)) for c in (0, 90, 180, 270, 0))
    poses.extend((0.0, float(c)) for c in (0, 45, 90, 135, 180, 225, 270, 315, 0))
    if len(poses) != ROW_COUNT:
        raise AssertionError("internal pose count mismatch")
    return tuple(poses)


def validate_and_load() -> tuple[list[Observation], list[dict[str, str]]]:
    results = read_csv(RESULTS_PATH)
    states = read_csv(STATE_PATH)
    closures = read_csv(CLOSURES_PATH)
    if len(results) != ROW_COUNT or len(states) != ROW_COUNT:
        raise FitError(f"expected {ROW_COUNT} result/state rows, got {len(results)}/{len(states)}")
    if len(closures) != CLOSURE_COUNT:
        raise FitError(f"expected {CLOSURE_COUNT} closures, got {len(closures)}")

    expected = expected_poses()
    states_by_seq = {exact_integer(row, "sample_seq"): row for row in states}
    if sorted(states_by_seq) != list(range(1, ROW_COUNT + 1)):
        raise FitError("state sequence is duplicated, missing, or out of range")

    observations: list[Observation] = []
    seen: set[int] = set()
    for result in results:
        seq = exact_integer(result, "sample_seq")
        if seq in seen or not 1 <= seq <= ROW_COUNT:
            raise FitError("result sequence is duplicated or out of range")
        seen.add(seq)
        for field, required in (
            ("campaign_id", CAMPAIGN),
            ("stage_mode", MODE),
            ("attempt_id", ATTEMPT),
            ("live_tool_number", 4),
            ("contact_count", 4),
        ):
            if exact_integer(result, field) != required:
                raise FitError(f"result seq {seq}: {field} contract changed")
        b_deg = number(result, "abs_b_deg")
        c_deg = number(result, "abs_c_deg")
        target_b, target_c = expected[seq - 1]
        if abs(b_deg - target_b) > 0.01 or abs(c_deg - target_c) > 0.01:
            raise FitError(f"result seq {seq}: pose differs from the frozen grid")
        center = np.array([number(result, field) for field in RESULT_CENTER_FIELDS])

        state = states_by_seq[seq]
        for field, required in (
            ("campaign_id", CAMPAIGN),
            ("stage_mode", MODE),
            ("attempt_id", ATTEMPT),
            ("persistent_correction_enabled", 1),
            ("tcpc_enabled", 1),
            ("twp_active", 0),
            ("twp_motion_enabled", 0),
            ("twp_valid", 0),
            ("b_ssi_invalid", 0),
            ("c_ssi_invalid", 0),
        ):
            if exact_integer(state, field) != required:
                raise FitError(f"state seq {seq}: {field} contract changed")
        if abs(number(state, "abs_b_deg") - b_deg) > 0.01:
            raise FitError(f"state seq {seq}: B pose differs from result")
        if abs(number(state, "abs_c_deg") - c_deg) > 0.01:
            raise FitError(f"state seq {seq}: C pose differs from result")
        observations.append(Observation(seq, b_deg, c_deg, center))

    if seen != set(range(1, ROW_COUNT + 1)):
        raise FitError("result sequence is incomplete")
    observations.sort(key=lambda item: item.seq)

    for closure in closures:
        for field, required in (
            ("campaign_id", CAMPAIGN),
            ("stage_mode", MODE),
            ("attempt_id", ATTEMPT),
            ("pass", 1),
        ):
            if exact_integer(closure, field) != required:
                raise FitError(f"closure {field} contract changed")
        norm = number(closure, "closure_norm_mm")
        limit = number(closure, "limit_mm")
        if limit != 0.050 or norm > limit + 1e-9:
            raise FitError("closure limit or pass result changed")
    return observations, closures


def unique_poses(observations: Sequence[Observation]) -> list[UniquePose]:
    grouped: dict[tuple[float, float], list[Observation]] = {}
    for observation in observations:
        grouped.setdefault((observation.b_deg, observation.c_deg), []).append(observation)
    poses = [
        UniquePose(
            b_deg=key[0],
            c_deg=key[1],
            center=np.mean([item.center for item in values], axis=0),
            sequences=tuple(item.seq for item in values),
        )
        for key, values in grouped.items()
    ]
    poses.sort(key=lambda pose: min(pose.sequences))
    if len(poses) != UNIQUE_POSE_COUNT:
        raise FitError(f"expected {UNIQUE_POSE_COUNT} unique poses, got {len(poses)}")
    return poses


def basis_values(b_deg: np.ndarray, c_deg: np.ndarray) -> dict[str, np.ndarray]:
    b_rad = np.radians(b_deg + B_ZERO_DEG)
    c_rad = np.radians(c_deg + C_ZERO_DEG)
    c_ref = math.radians(C_ZERO_DEG)
    sin_b = np.sin(b_rad)
    omc_b = 1.0 - np.cos(b_rad)
    sin_c = np.sin(c_rad)
    cos_c = np.cos(c_rad)
    mid_b = np.sin(2.0 * b_rad) ** 2
    return {
        "c_cos": cos_c - math.cos(c_ref),
        "c_sin": sin_c - math.sin(c_ref),
        "c_cos2": np.cos(2.0 * c_rad) - math.cos(2.0 * c_ref),
        "c_sin2": np.sin(2.0 * c_rad) - math.sin(2.0 * c_ref),
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


def feature_matrix(b_deg: np.ndarray, c_deg: np.ndarray) -> np.ndarray:
    values = basis_values(b_deg, c_deg)
    return np.column_stack([values[term] for term in ADMISSIBLE_TERMS])


def build_dataset(observations: Sequence[Observation]) -> Dataset:
    poses = unique_poses(observations)
    b_deg = np.array([pose.b_deg for pose in poses])
    c_deg = np.array([pose.c_deg for pose in poses])
    centers = np.vstack([pose.center for pose in poses])
    return Dataset(
        tuple(observations),
        tuple(poses),
        b_deg,
        c_deg,
        centers,
        feature_matrix(b_deg, c_deg),
    )


def fit_ridge(
    data: Dataset,
    row_indices: np.ndarray,
    term_indices: tuple[int, ...],
    ridge_lambda: float,
) -> RidgeFit:
    if len(row_indices) == 0 or len(term_indices) == 0:
        raise FitError("ridge fit needs nonempty rows and terms")
    features = data.features[np.ix_(row_indices, term_indices)]
    feature_mean = np.mean(features, axis=0)
    feature_scale = np.std(features, axis=0)
    if np.any(feature_scale <= 1e-12):
        bad = [
            ADMISSIBLE_TERMS[index]
            for index, scale in zip(term_indices, feature_scale)
            if scale <= 1e-12
        ]
        raise FitError(f"training fold cannot identify terms: {bad}")
    standardized = (features - feature_mean) / feature_scale
    centers = data.centers[row_indices]
    center_mean = np.mean(centers, axis=0)
    centered = centers - center_mean
    gram = standardized.T @ standardized
    right = standardized.T @ centered
    if ridge_lambda == 0.0:
        coefficients = np.linalg.lstsq(standardized, centered, rcond=None)[0]
    else:
        coefficients = np.linalg.solve(
            gram + ridge_lambda * np.eye(len(term_indices)), right
        )
    return RidgeFit(
        term_indices,
        ridge_lambda,
        feature_mean,
        feature_scale,
        coefficients,
        center_mean,
    )


def predict_raw_centers(data: Dataset, fit: RidgeFit, row_indices: np.ndarray) -> np.ndarray:
    features = data.features[np.ix_(row_indices, fit.term_indices)]
    standardized = (features - fit.feature_mean) / fit.feature_scale
    return fit.center_mean + standardized @ fit.standardized_coefficients


def correction_offsets_for_features(features: np.ndarray, fit: RidgeFit) -> np.ndarray:
    return features[:, fit.term_indices] @ fit.correction_deltas


def correction_offsets(data: Dataset, fit: RidgeFit) -> np.ndarray:
    return correction_offsets_for_features(data.features, fit)


def metric(residuals: np.ndarray) -> Metric:
    norms = np.linalg.norm(residuals, axis=1)
    return Metric(float(math.sqrt(np.mean(norms**2))), float(np.max(norms)))


def centered_metric(centers: np.ndarray) -> Metric:
    return metric(centers - np.mean(centers, axis=0))


def corrected_metric(data: Dataset, fit: RidgeFit) -> Metric:
    return centered_metric(data.centers + correction_offsets(data, fit))


def signed_b_group(data: Dataset) -> np.ndarray:
    return data.b_deg


def abs_b_group(data: Dataset) -> np.ndarray:
    return np.abs(data.b_deg)


def c_group(data: Dataset) -> np.ndarray:
    return data.c_deg


def antipodal_group(data: Dataset) -> np.ndarray:
    return np.mod(data.c_deg, 180.0)


GROUPERS: dict[str, Callable[[Dataset], np.ndarray]] = {
    "signed-B": signed_b_group,
    "paired-abs-B": abs_b_group,
    "C-sector": c_group,
    "antipodal-C-pair": antipodal_group,
}


def max_correction(data: Dataset, fit: RidgeFit) -> float:
    return float(np.max(np.linalg.norm(correction_offsets(data, fit), axis=1)))


def grouped_cv(
    data: Dataset,
    selection_rows: np.ndarray,
    term_indices: tuple[int, ...],
    ridge_lambda: float,
    grouping: str,
) -> GroupCv | None:
    group_values = GROUPERS[grouping](data)
    residual_blocks: list[np.ndarray] = []
    correction_maximum = 0.0
    groups = sorted(set(group_values[selection_rows]))
    if len(groups) < 2:
        return None
    for held_group in groups:
        held = selection_rows[group_values[selection_rows] == held_group]
        training = selection_rows[group_values[selection_rows] != held_group]
        try:
            fit = fit_ridge(data, training, term_indices, ridge_lambda)
        except FitError:
            return None
        fold_correction = max_correction(data, fit)
        if fold_correction > MAX_CORRECTION_MM + 1e-12:
            return None
        correction_maximum = max(correction_maximum, fold_correction)
        residual_blocks.append(
            data.centers[held] - predict_raw_centers(data, fit, held)
        )
    return GroupCv(metric(np.vstack(residual_blocks)), correction_maximum)


def evaluate_candidate(
    data: Dataset,
    selection_rows: np.ndarray,
    term_indices: tuple[int, ...],
    ridge_lambda: float,
) -> CandidateEvaluation | None:
    try:
        fit = fit_ridge(data, selection_rows, term_indices, ridge_lambda)
    except FitError:
        return None
    correction_maximum = max_correction(data, fit)
    if correction_maximum > MAX_CORRECTION_MM + 1e-12:
        return None

    signed_cv = grouped_cv(
        data, selection_rows, term_indices, ridge_lambda, "signed-B"
    )
    abs_b_cv = grouped_cv(
        data, selection_rows, term_indices, ridge_lambda, "paired-abs-B"
    )
    c_cv = grouped_cv(data, selection_rows, term_indices, ridge_lambda, "C-sector")
    if signed_cv is None or abs_b_cv is None or c_cv is None:
        return None
    correction_maximum = max(
        correction_maximum,
        signed_cv.maximum_correction,
        abs_b_cv.maximum_correction,
        c_cv.maximum_correction,
    )
    objective = (
        signed_cv.metric.rms
        + abs_b_cv.metric.rms
        + OBJECTIVE_C_WEIGHT * c_cv.metric.rms
    )
    worst_validation_maximum = max(
        signed_cv.metric.maximum,
        abs_b_cv.metric.maximum,
        c_cv.metric.maximum,
    )
    return CandidateEvaluation(
        term_indices,
        ridge_lambda,
        objective,
        worst_validation_maximum,
        correction_maximum,
        signed_cv,
        abs_b_cv,
        c_cv,
        fit,
    )


def candidate_key(evaluation: CandidateEvaluation) -> tuple[object, ...]:
    return (
        round(evaluation.objective, TIE_DIGITS),
        round(evaluation.worst_validation_maximum, TIE_DIGITS),
        len(evaluation.term_indices),
        round(evaluation.maximum_correction, TIE_DIGITS),
        -evaluation.ridge_lambda,
        evaluation.term_indices,
    )


def evaluation_record(evaluation: CandidateEvaluation) -> dict[str, object]:
    return {
        "term_indices": list(evaluation.term_indices),
        "ridge_lambda": evaluation.ridge_lambda,
        "objective": evaluation.objective,
        "worst_validation_maximum": evaluation.worst_validation_maximum,
        "maximum_correction": evaluation.maximum_correction,
    }


def restore_evaluation(
    data: Dataset,
    selection_rows: np.ndarray,
    record: dict[str, object],
) -> CandidateEvaluation:
    try:
        term_indices = tuple(int(value) for value in record["term_indices"])
        ridge_lambda = float(record["ridge_lambda"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FitError("invalid model-selection checkpoint entry") from exc
    if term_indices != tuple(sorted(set(term_indices))):
        raise FitError("checkpoint term indices are not canonical")
    if any(not 0 <= index < len(ADMISSIBLE_TERMS) for index in term_indices):
        raise FitError("checkpoint term index is out of range")
    if ridge_lambda not in LAMBDA_GRID:
        raise FitError("checkpoint lambda is outside the frozen grid")
    evaluation = evaluate_candidate(data, selection_rows, term_indices, ridge_lambda)
    if evaluation is None:
        raise FitError("checkpoint model no longer passes the frozen selection contract")
    for field in ("objective", "worst_validation_maximum", "maximum_correction"):
        try:
            stored = float(record[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise FitError(f"checkpoint is missing {field}") from exc
        if round(getattr(evaluation, field), TIE_DIGITS) != round(stored, TIE_DIGITS):
            raise FitError(f"checkpoint {field} does not reproduce")
    return evaluation


def selection_record(selection: SelectionResult) -> dict[str, object]:
    winner_index = next(
        index for index, evaluation in enumerate(selection.path) if evaluation is selection.winner
    )
    return {
        "winner_index": winner_index,
        "path": [evaluation_record(evaluation) for evaluation in selection.path],
        "swap_counts": list(selection.swap_counts),
    }


def restore_selection(
    data: Dataset,
    selection_rows: np.ndarray,
    record: dict[str, object],
) -> SelectionResult:
    try:
        path_records = record["path"]
        swap_counts = tuple(int(value) for value in record["swap_counts"])
        winner_index = int(record["winner_index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FitError("invalid selection checkpoint") from exc
    if not isinstance(path_records, list):
        raise FitError("checkpoint selection path is not a list")
    path = tuple(
        restore_evaluation(data, selection_rows, item) for item in path_records
    )
    if len(path) != len(swap_counts) or not 0 <= winner_index < len(path):
        raise FitError("checkpoint selection path dimensions changed")
    winner = path[winner_index]
    if candidate_key(winner) != min(candidate_key(item) for item in path):
        raise FitError("checkpoint winner is not the best stored path model")
    return SelectionResult(winner, path, swap_counts)


def select_model(
    data: Dataset,
    selection_rows: np.ndarray,
    *,
    swap_refine: bool = True,
) -> SelectionResult:
    selected: list[int] = []
    path: list[CandidateEvaluation] = []
    swap_counts: list[int] = []
    cache: dict[tuple[tuple[int, ...], float], CandidateEvaluation | None] = {}

    def cached_evaluation(
        term_indices: Sequence[int], ridge_lambda: float
    ) -> CandidateEvaluation | None:
        canonical = tuple(sorted(term_indices))
        key = (canonical, ridge_lambda)
        if key not in cache:
            cache[key] = evaluate_candidate(
                data, selection_rows, canonical, ridge_lambda
            )
        return cache[key]

    for _ in range(MAX_SELECTED_TERMS):
        candidates: list[CandidateEvaluation] = []
        for term_index in range(len(ADMISSIBLE_TERMS)):
            if term_index in selected:
                continue
            for ridge_lambda in LAMBDA_GRID:
                evaluation = cached_evaluation(selected + [term_index], ridge_lambda)
                if evaluation is not None:
                    candidates.append(evaluation)
        if not candidates:
            break
        best_step = min(candidates, key=candidate_key)
        swaps = 0
        if swap_refine:
            while True:
                swap_candidates = [best_step]
                selected_set = set(best_step.term_indices)
                for removed in best_step.term_indices:
                    retained = selected_set - {removed}
                    for added in range(len(ADMISSIBLE_TERMS)):
                        if added in selected_set:
                            continue
                        swapped = tuple(sorted(retained | {added}))
                        for ridge_lambda in LAMBDA_GRID:
                            evaluation = cached_evaluation(swapped, ridge_lambda)
                            if evaluation is not None:
                                swap_candidates.append(evaluation)
                refined = min(swap_candidates, key=candidate_key)
                if candidate_key(refined) >= candidate_key(best_step):
                    break
                best_step = refined
                swaps += 1
        selected = list(best_step.term_indices)
        path.append(best_step)
        swap_counts.append(swaps)
    if not path:
        raise FitError("no admissible model survived the selection contract")
    return SelectionResult(
        min(path, key=candidate_key), tuple(path), tuple(swap_counts)
    )


def outer_validation(
    data: Dataset,
    grouping: str,
    checkpoint: dict[str, object],
    save_checkpoint: Callable[[], None],
) -> OuterValidation:
    group_values = GROUPERS[grouping](data)
    all_rows = np.arange(len(data.poses))
    residual_blocks: list[np.ndarray] = []
    folds: list[OuterFold] = []
    worst_group = float("nan")
    worst_maximum = -1.0
    outer_root = checkpoint.setdefault("outer", {})
    if not isinstance(outer_root, dict):
        raise FitError("checkpoint outer section is invalid")
    section = outer_root.setdefault(grouping, {})
    if not isinstance(section, dict):
        raise FitError(f"checkpoint outer section {grouping} is invalid")
    groups = sorted(set(group_values))
    for fold_index, held_group in enumerate(groups, start=1):
        held = all_rows[group_values == held_group]
        training = all_rows[group_values != held_group]
        checkpoint_key = f"{float(held_group):+.9f}"
        source = "resumed"
        if checkpoint_key in section:
            entry = section[checkpoint_key]
            if not isinstance(entry, dict):
                raise FitError(f"checkpoint fold {grouping}/{checkpoint_key} is invalid")
            selection = restore_evaluation(data, training, entry)
        else:
            source = "computed"
            selection = select_model(data, training).winner
            section[checkpoint_key] = evaluation_record(selection)
            save_checkpoint()
        residuals = data.centers[held] - predict_raw_centers(data, selection.fit, held)
        held_metric = metric(residuals)
        residual_blocks.append(residuals)
        folds.append(
            OuterFold(
                float(held_group), len(held), selection, held_metric
            )
        )
        if held_metric.maximum > worst_maximum:
            worst_group = float(held_group)
            worst_maximum = held_metric.maximum
        print(
            f"r2: {grouping} fold {fold_index}/{len(groups)} "
            f"{float(held_group):+g} {source}",
            flush=True,
        )
    return OuterValidation(
        grouping,
        metric(np.vstack(residual_blocks)),
        worst_group,
        worst_maximum,
        tuple(folds),
    )


def parse_hal_values() -> dict[str, float]:
    values: dict[str, float] = {}
    pattern = re.compile(r"^\s*setp\s+(headheadkins\.[^\s]+)\s+([-+0-9.eE]+)")
    for line in HAL_PATH.read_text(encoding="ascii").splitlines():
        match = pattern.match(line)
        if match:
            values[match.group(1)] = float(match.group(2))
    if abs(values.get("headheadkins.b-zero-offset", float("nan")) - B_ZERO_DEG) > 1e-12:
        raise FitError("HAL B-zero input differs from the frozen fit basis")
    if abs(values.get("headheadkins.c-zero-offset", float("nan")) - C_ZERO_DEG) > 1e-12:
        raise FitError("HAL C-zero input differs from the frozen fit basis")
    for stem in PIN_STEMS.values():
        for axis in AXES:
            if f"{stem}.{axis}" not in values:
                raise FitError(f"HAL is missing fit target pin {stem}.{axis}")
    return values


def full_delta_matrix(fit: RidgeFit) -> np.ndarray:
    output = np.zeros((len(ADMISSIBLE_TERMS), len(AXES)))
    for local_index, term_index in enumerate(fit.term_indices):
        output[term_index] = fit.correction_deltas[local_index]
    return output


def format_metric(value: Metric) -> str:
    return f"`{value.rms:.6f} / {value.maximum:.6f}`"


def term_names(term_indices: Sequence[int]) -> tuple[str, ...]:
    return tuple(ADMISSIBLE_TERMS[index] for index in term_indices)


def write_csv_atomically(path: Path, fields: Sequence[str], rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        encoding="ascii",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_residuals(path: Path, data: Dataset, primary: CandidateEvaluation) -> None:
    pose_multiplicity = {
        (pose.b_deg, pose.c_deg): pose.multiplicity for pose in data.poses
    }
    observation_b = np.array([item.b_deg for item in data.observations])
    observation_c = np.array([item.c_deg for item in data.observations])
    observation_centers = np.vstack([item.center for item in data.observations])
    observation_features = feature_matrix(observation_b, observation_c)
    offsets = correction_offsets_for_features(observation_features, primary.fit)
    candidate_centers = observation_centers + offsets

    current_reference = np.mean(data.centers, axis=0)
    candidate_reference = np.mean(data.centers + correction_offsets(data, primary.fit), axis=0)
    rows: list[dict[str, object]] = []
    for observation, offset, candidate in zip(data.observations, offsets, candidate_centers):
        multiplicity = pose_multiplicity[(observation.b_deg, observation.c_deg)]
        current_residual = observation.center - current_reference
        candidate_residual = candidate - candidate_reference
        row: dict[str, object] = {
            "campaign_id": CAMPAIGN,
            "attempt_id": ATTEMPT,
            "fit_revision": REVISION,
            "sample_seq": observation.seq,
            "abs_b_deg": f"{observation.b_deg:.6f}",
            "abs_c_deg": f"{observation.c_deg:.6f}",
            "pose_multiplicity": multiplicity,
            "fit_weight": f"{1.0 / multiplicity:.9f}",
            "primary_lambda": f"{primary.ridge_lambda:.1f}",
            "primary_term_count": len(primary.term_indices),
        }
        for field, value in zip(RESULT_CENTER_FIELDS, observation.center):
            row[field] = f"{value:.9f}"
        for prefix, vector in (
            ("current_residual", current_residual),
            ("candidate_delta", offset),
            ("candidate_center", candidate),
            ("candidate_residual", candidate_residual),
        ):
            for axis, value in zip(AXES, vector):
                row[f"{prefix}_{axis}_mm"] = f"{value:.9f}"
            if prefix != "candidate_center":
                row[f"{prefix}_norm_mm"] = f"{np.linalg.norm(vector):.9f}"
        rows.append(row)
    write_csv_atomically(path, RESIDUAL_FIELDS, rows)


def write_pins(
    path: Path,
    primary: CandidateEvaluation,
    hal_values: dict[str, float],
) -> None:
    deltas = full_delta_matrix(primary.fit)
    rows: list[dict[str, object]] = []
    selected = set(primary.term_indices)
    for term_index, term in enumerate(ADMISSIBLE_TERMS):
        stem = PIN_STEMS[term]
        for axis_index, axis in enumerate(AXES):
            pin = f"{stem}.{axis}"
            current = hal_values[pin]
            delta = deltas[term_index, axis_index]
            rows.append(
                {
                    "campaign_id": CAMPAIGN,
                    "fit_revision": REVISION,
                    "operational_status": "offline_not_authorized",
                    "selected": int(term_index in selected),
                    "basis_term": term,
                    "pin": pin,
                    "axis": axis,
                    "current_mm": f"{current:+.9f}",
                    "delta_mm": f"{delta:+.9f}",
                    "predicted_total_mm": f"{current + delta:+.9f}",
                }
            )
    write_csv_atomically(path, PIN_FIELDS, rows)


@dataclass(frozen=True)
class Stability:
    selection_frequency: np.ndarray
    coefficient_sd_norm: np.ndarray
    coefficient_max_difference: np.ndarray
    direction_agreement: np.ndarray
    prediction_difference: Metric
    pointwise_prediction_sd: Metric


def paired_b_stability(
    data: Dataset,
    primary: CandidateEvaluation,
    abs_b_validation: OuterValidation,
) -> Stability:
    primary_deltas = full_delta_matrix(primary.fit)
    fold_deltas = np.stack(
        [full_delta_matrix(fold.selection.fit) for fold in abs_b_validation.folds]
    )
    selected_sets = [set(fold.selection.term_indices) for fold in abs_b_validation.folds]
    selection_frequency = np.array(
        [sum(index in selected for selected in selected_sets) for index in range(len(ADMISSIBLE_TERMS))]
    )
    coefficient_sd_norm = np.linalg.norm(np.std(fold_deltas, axis=0), axis=1)
    coefficient_max_difference = np.max(
        np.linalg.norm(fold_deltas - primary_deltas[None, :, :], axis=2), axis=0
    )
    direction_agreement = np.array(
        [
            sum(np.dot(primary_deltas[index], fold[index]) > 0.0 for fold in fold_deltas)
            if np.linalg.norm(primary_deltas[index]) > 1e-15
            else 0
            for index in range(len(ADMISSIBLE_TERMS))
        ]
    )

    primary_surface = correction_offsets(data, primary.fit)
    fold_surfaces = np.stack(
        [correction_offsets(data, fold.selection.fit) for fold in abs_b_validation.folds]
    )
    prediction_difference = metric(
        (fold_surfaces - primary_surface[None, :, :]).reshape(-1, len(AXES))
    )
    pointwise_sd_norms = np.linalg.norm(np.std(fold_surfaces, axis=0), axis=1)
    pointwise_prediction_sd = Metric(
        float(math.sqrt(np.mean(pointwise_sd_norms**2))),
        float(np.max(pointwise_sd_norms)),
    )
    return Stability(
        selection_frequency,
        coefficient_sd_norm,
        coefficient_max_difference,
        direction_agreement,
        prediction_difference,
        pointwise_prediction_sd,
    )


def design_condition(data: Dataset, term_indices: tuple[int, ...]) -> tuple[int, float, float]:
    features = data.features[:, term_indices]
    centered = features - np.mean(features, axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    raw_condition = float(singular[0] / singular[-1])
    scaled = centered / np.linalg.norm(centered, axis=0)
    scaled_singular = np.linalg.svd(scaled, compute_uv=False)
    scaled_condition = float(scaled_singular[0] / scaled_singular[-1])
    return int(np.linalg.matrix_rank(centered)), raw_condition, scaled_condition


def raw_diagnostic_metrics(data: Dataset, primary: CandidateEvaluation) -> tuple[Metric, Metric]:
    centers = np.vstack([item.center for item in data.observations])
    b_deg = np.array([item.b_deg for item in data.observations])
    c_deg = np.array([item.c_deg for item in data.observations])
    features = feature_matrix(b_deg, c_deg)
    corrected = centers + correction_offsets_for_features(features, primary.fit)
    return centered_metric(centers), centered_metric(corrected)


def group_label(validation: OuterValidation, group: float) -> str:
    if validation.name == "signed-B":
        return f"B{group:+g}"
    if validation.name == "paired-abs-B":
        return f"abs(B){group:g}"
    if validation.name == "C-sector":
        return f"C{group:g}"
    return f"C{group:g}/C{group + 180.0:g}"


def lambda_counts(folds: Sequence[OuterFold]) -> str:
    counts = {
        ridge_lambda: sum(fold.selection.ridge_lambda == ridge_lambda for fold in folds)
        for ridge_lambda in LAMBDA_GRID
    }
    return ", ".join(f"{value:g}:{counts[value]}" for value in LAMBDA_GRID)


def validation_summary_row(validation: OuterValidation) -> str:
    sizes = [len(fold.selection.term_indices) for fold in validation.folds]
    correction_maximum = max(fold.selection.maximum_correction for fold in validation.folds)
    return (
        f"| {validation.name} | {format_metric(validation.metric)} | "
        f"{group_label(validation, validation.worst_group)} / `{validation.worst_group_maximum:.6f}` | "
        f"`{min(sizes)}-{max(sizes)}` | `{lambda_counts(validation.folds)}` | "
        f"`{correction_maximum:.6f}` |"
    )


def report_text(
    data: Dataset,
    closures: Sequence[dict[str, str]],
    forward_selection: SelectionResult,
    selection: SelectionResult,
    validations: Sequence[OuterValidation],
    hal_values: dict[str, float],
    residual_path: Path,
    pins_path: Path,
) -> str:
    primary = selection.winner
    forward_primary = forward_selection.winner
    validation_by_name = {validation.name: validation for validation in validations}
    abs_b_validation = validation_by_name["paired-abs-B"]
    stability = paired_b_stability(data, primary, abs_b_validation)
    primary_deltas = full_delta_matrix(primary.fit)
    selected = set(primary.term_indices)

    closure_values = np.array([number(row, "closure_norm_mm") for row in closures])
    closure_metric = Metric(
        float(math.sqrt(np.mean(closure_values**2))), float(np.max(closure_values))
    )
    current_pose_metric = centered_metric(data.centers)
    candidate_pose_metric = corrected_metric(data, primary.fit)
    current_row_metric, candidate_row_metric = raw_diagnostic_metrics(data, primary)
    rank, raw_condition, scaled_condition = design_condition(data, primary.term_indices)
    primary_correction = max_correction(data, primary.fit)
    worst_nested_correction = max(
        fold.selection.maximum_correction
        for validation in validations
        for fold in validation.folds
    )

    output_hashes = {
        Path(__file__).resolve(): sha256(Path(__file__).resolve()),
        residual_path.resolve(): sha256(residual_path),
        pins_path.resolve(): sha256(pins_path),
    }

    lines = [
        "# Relocated-Sphere T4-Only Fit Revision R2",
        "",
        "## Operational Status",
        "",
        "`OFFLINE CANDIDATE - NOT AUTHORIZED FOR MACHINE USE`",
        "",
        "Revision r2 supersedes the archived lambda-30 r1 candidate for operational",
        "planning. The r1 fitter, report, residuals, overlay, INI, analyzer, and runner",
        "remain immutable provenance; this fitter neither reads nor writes an overlay,",
        "INI, analyzer, runner, HAL configuration, or machine-control interface.",
        "A separate reviewed release package and a fresh T4 verification are required.",
        "",
        "## Frozen T4 Inputs",
        "",
        f"- campaign/mode/attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- accepted result/state rows: `{len(data.observations)} / {len(data.observations)}`",
        f"- strict closures: `{len(closures)}`; RMS/max {format_metric(closure_metric)} mm",
        f"- equal-weight unique poses used by every fit and validation: `{len(data.poses)}`",
        "- result, state, ordered-pose, correction-enabled, and closure contracts: `PASS`",
        "",
        "| frozen input | SHA-256 |",
        "| --- | --- |",
    ]
    for path, digest in EXPECTED_SHA256.items():
        lines.append(f"| `{path.relative_to(REPO_ROOT)}` | `{digest}` |")

    lines.extend(
        [
            "",
            "## Predeclared Selection Protocol",
            "",
            "1. Average repeated identical `(B,C)` measurements first. Every one of the",
            "   76 resulting poses has weight one in fitting, selection, and validation.",
            "2. Search only the 17 existing headheadkins bases listed below. Exclude",
            "   `bc_sinb_sin2c` and `bmid_sin2c`: nonzero-B C135/C315 observations were",
            "   deliberately omitted for collision clearance, so their opposite sin(2C)",
            "   phase is not physically observed.",
            "3. Use standardized ridge fits with lambda in `{1,3,10,30,100}`. The",
            "   intercept is unpenalized; feature mean and population standard deviation",
            "   are learned from each training fold only.",
            "4. Starting empty, greedily add one term at a time. At each size evaluate",
            "   every remaining term at every lambda, then repeatedly evaluate every",
            "   same-size one-for-one term swap with lambda retuned until the tie key no",
            "   longer improves. Continue to 10 terms and select the best refined model",
            "   anywhere on the 1-to-10-term path. This deterministic search is not",
            "   exhaustive enumeration of all subsets.",
            "5. Inner objective `J = RMS_signed-B + RMS_paired-abs(B) + 0.5*RMS_C-sector`.",
            "   All three components are grouped leave-one-block-out predictions.",
            f"6. Reject a candidate if its modeled correction exceeds `{MAX_CORRECTION_MM:.3f} mm`",
            "   anywhere on the complete measured 76-pose grid in the full fit or any",
            "   inner grouped refit.",
            f"7. Deterministic tie key after rounding metrics to `{TIE_DIGITS}` decimals:",
            "   lower J, lower worst validation maximum, fewer terms, lower maximum",
            "   correction, stronger regularization, then fixed pool-index order.",
            "8. For every outer holdout, repeat the entire term/lambda search using only",
            "   its training poses. No outer response participates in selection or fit.",
            "",
            "Fixed admissible pool:",
            "",
            "```text",
            ", ".join(ADMISSIBLE_TERMS),
            "```",
            "",
            "## Primary Candidate",
            "",
            f"One primary model is frozen: `{len(primary.term_indices)}` terms, lambda "
            f"`{primary.ridge_lambda:g}`.",
            "",
            "```text",
            ", ".join(term_names(primary.term_indices)),
            "```",
            "",
            f"- selection objective J: `{primary.objective:.9f}`",
            f"- inner signed-B RMS/max: {format_metric(primary.signed_cv.metric)} mm",
            f"- inner paired-abs(B) RMS/max: {format_metric(primary.abs_b_cv.metric)} mm",
            f"- inner C-sector RMS/max: {format_metric(primary.c_cv.metric)} mm",
            f"- primary modeled correction maximum: `{primary_correction:.6f} mm`",
            f"- primary plus inner-refit correction maximum: `{primary.maximum_correction:.6f} mm`",
            f"- design rank: `{rank}/{len(primary.term_indices)}`; raw/scaled condition: "
            f"`{raw_condition:.3e} / {scaled_condition:.3f}`",
            "",
            "### Forward-Only Reconciliation",
            "",
            "The forward-only result is retained as a method audit, but only the",
            "swap-refined result above is the r2 primary.",
            "",
            "| method | terms | lambda | J | correction max |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| forward only | `{len(forward_primary.term_indices)}` | "
            f"`{forward_primary.ridge_lambda:g}` | `{forward_primary.objective:.9f}` | "
            f"`{forward_primary.maximum_correction:.6f}` |",
            f"| swap refined, primary | `{len(primary.term_indices)}` | "
            f"`{primary.ridge_lambda:g}` | `{primary.objective:.9f}` | "
            f"`{primary.maximum_correction:.6f}` |",
            "",
            "Forward-only terms:",
            "",
            "```text",
            ", ".join(term_names(forward_primary.term_indices)),
            "```",
            "",
            "| weighting | current | r2 offline prediction |",
            "| --- | ---: | ---: |",
            f"| 76 equal unique poses | {format_metric(current_pose_metric)} | {format_metric(candidate_pose_metric)} |",
            f"| all 101 diagnostic rows | {format_metric(current_row_metric)} | {format_metric(candidate_row_metric)} |",
            "",
            "### Forward Path",
            "",
            "The selected row is the global winner on the predeclared path, not",
            "necessarily the final 10-term step.",
            "",
            "| terms | refined set | swap passes | lambda | J | signed B | paired abs(B) | C sector | correction max | selected |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for step, (evaluation, swaps) in enumerate(
        zip(selection.path, selection.swap_counts), start=1
    ):
        lines.append(
            f"| {step} | `{','.join(term_names(evaluation.term_indices))}` | {swaps} | "
            f"{evaluation.ridge_lambda:g} | "
            f"`{evaluation.objective:.9f}` | {format_metric(evaluation.signed_cv.metric)} | "
            f"{format_metric(evaluation.abs_b_cv.metric)} | {format_metric(evaluation.c_cv.metric)} | "
            f"`{evaluation.maximum_correction:.6f}` | "
            f"{'`YES`' if evaluation is primary else ''} |"
        )

    lines.extend(
        [
            "",
            "## Selection-Adjusted Outer Validation",
            "",
            "Every row below repeats the complete forward term and lambda selection inside",
            "each outer training fold. Metrics are absolute-center prediction errors on",
            "the untouched outer poses; they are not fixed-family refits.",
            "",
            "The antipodal test groups C sectors modulo 180 degrees, holding C0/C180,",
            "C45/C225, C90/C270, or C135/C315 out together. It tests transfer when both",
            "opposite phases are absent from the outer training set.",
            "",
            "| outer scheme | RMS / max mm | worst group / max | selected terms | lambda counts `lambda:folds` | protocol correction max |",
            "| --- | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for validation in validations:
        lines.append(validation_summary_row(validation))
    lines.extend(
        [
            "",
            f"No primary, inner, or outer-selection model exceeds the `{MAX_CORRECTION_MM:.3f} mm`",
            f"bound; the largest protocol value is `{worst_nested_correction:.6f} mm`.",
            "C-sector and antipodal results remain the controlling extrapolation checks.",
            "C135/C315 exists only at B0, so no conclusion is made about those sectors at",
            "nonzero B.",
            "",
            "### Outer Fold Detail",
            "",
            "| scheme | held group | poses | lambda | terms | held RMS / max | protocol correction max |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for validation in validations:
        for fold in validation.folds:
            lines.append(
                f"| {validation.name} | {group_label(validation, fold.group)} | "
                f"{fold.held_count} | {fold.selection.ridge_lambda:g} | "
                f"`{','.join(term_names(fold.selection.term_indices))}` | "
                f"{format_metric(fold.metric)} | `{fold.selection.maximum_correction:.6f}` |"
            )

    lines.extend(
        [
            "",
            "## Paired-B Stability",
            "",
            "Stability uses the eight selection-adjusted paired-abs(B) outer fits. Missing",
            "terms are aligned as zero coefficient deltas. Prediction differences compare",
            "each fold-selected correction surface with the primary surface over all 76",
            "measured poses.",
            "",
            f"- fold-to-primary prediction difference RMS/max: {format_metric(stability.prediction_difference)} mm",
            f"- pointwise fold prediction SD RMS/max: {format_metric(stability.pointwise_prediction_sd)} mm",
            "",
            "## Exact Offline Pin Totals",
            "",
            "`delta` is added to the frozen baseline pin. Nonselected terms have zero",
            "delta. These values are predictions only; this report is not a HAL overlay.",
            "Coefficient SD and max difference include selection changes across the eight",
            "paired-B outer folds.",
            "",
            "| selected | basis / pin stem | current XYZ | delta XYZ | predicted total XYZ | abs-B frequency | coefficient SD | max difference | direction |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for term_index, term in enumerate(ADMISSIBLE_TERMS):
        stem = PIN_STEMS[term]
        current = np.array([hal_values[f"{stem}.{axis}"] for axis in AXES])
        delta = primary_deltas[term_index]
        total = current + delta
        direction = (
            f"{stability.direction_agreement[term_index]}/8"
            if term_index in selected
            else "n/a"
        )
        lines.append(
            f"| {'YES' if term_index in selected else 'no'} | `{term}` / `{stem}.[xyz]` | "
            f"`{current[0]:+.9f}, {current[1]:+.9f}, {current[2]:+.9f}` | "
            f"`{delta[0]:+.9f}, {delta[1]:+.9f}, {delta[2]:+.9f}` | "
            f"`{total[0]:+.9f}, {total[1]:+.9f}, {total[2]:+.9f}` | "
            f"`{stability.selection_frequency[term_index]}/8` | "
            f"`{stability.coefficient_sd_norm[term_index]:.6f}` | "
            f"`{stability.coefficient_max_difference[term_index]:.6f}` | "
            f"`{direction}` |"
        )

    lines.extend(
        [
            "",
            "Machine-readable pin audit: `tcpc-relocated-sphere-t4-fit-r2-pins.csv`.",
            "Per-observation predictions: `tcpc-relocated-sphere-t4-fit-r2-residuals.csv`.",
            "",
            "## Generated Artifact Hashes",
            "",
            "| artifact | SHA-256 |",
            "| --- | --- |",
        ]
    )
    for path, digest in output_hashes.items():
        try:
            shown = path.relative_to(REPO_ROOT)
        except ValueError:
            shown = path
        lines.append(f"| `{shown}` | `{digest}` |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Freeze this one r2 model as the campaign-04 T4-only offline candidate.",
            "It supersedes r1/lambda30 for future operational planning because r1 was",
            "over-regularized after sparse-family selection and its fixed-family CV did",
            "not account for term selection. R2 remains unvalidated on a fresh run.",
            "",
            "Do not load these totals directly. A separate revision-specific overlay,",
            "configured-limit replay, analyzer, immutable archive, operator review, and",
            "fresh T4 verification must be completed before any machine release.",
            "",
        ]
    )
    return "\n".join(lines)


def write_text_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="ascii",
        newline="\n",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def new_checkpoint() -> dict[str, object]:
    return {
        "schema": 1,
        "script_sha256": sha256(Path(__file__).resolve()),
        "input_sha256": {
            str(path.relative_to(REPO_ROOT)): digest
            for path, digest in EXPECTED_SHA256.items()
        },
        "primary": {},
        "outer": {},
    }


def load_checkpoint(path: Path) -> dict[str, object]:
    expected = new_checkpoint()
    if not path.exists():
        return expected
    try:
        checkpoint = json.loads(path.read_text(encoding="ascii"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise FitError(f"invalid checkpoint JSON: {path}") from exc
    if not isinstance(checkpoint, dict):
        raise FitError("checkpoint root is not an object")
    for field in ("schema", "script_sha256", "input_sha256"):
        if checkpoint.get(field) != expected[field]:
            raise FitError(
                f"checkpoint {field} differs from this exact script/input revision; "
                f"use a new --checkpoint path"
            )
    if not isinstance(checkpoint.get("primary"), dict):
        raise FitError("checkpoint primary section is invalid")
    if not isinstance(checkpoint.get("outer"), dict):
        raise FitError("checkpoint outer section is invalid")
    return checkpoint


def write_checkpoint(path: Path, checkpoint: dict[str, object]) -> None:
    text = json.dumps(checkpoint, indent=2, sort_keys=True, allow_nan=False) + "\n"
    write_text_atomically(path, text)


def synthetic_dataset() -> Dataset:
    unique: list[tuple[float, float]] = []
    for pose in expected_poses():
        if pose not in unique:
            unique.append(pose)
    b_deg = np.array([pose[0] for pose in unique])
    c_deg = np.array([pose[1] for pose in unique])
    features = feature_matrix(b_deg, c_deg)
    coefficients = np.arange(15, dtype=float).reshape(5, 3) * 0.001
    centers = np.array([1.0, 2.0, 3.0]) + features[:, :5] @ coefficients
    poses = tuple(
        UniquePose(b, c, center, (index + 1,))
        for index, ((b, c), center) in enumerate(zip(unique, centers))
    )
    observations = tuple(
        Observation(index + 1, pose.b_deg, pose.c_deg, pose.center)
        for index, pose in enumerate(poses)
    )
    return Dataset(observations, poses, b_deg, c_deg, centers, features)


def self_test() -> None:
    assert len(ADMISSIBLE_TERMS) == 17
    assert len(set(ADMISSIBLE_TERMS)) == len(ADMISSIBLE_TERMS)
    assert set(ADMISSIBLE_TERMS) == set(PIN_STEMS)
    assert "bc_sinb_sin2c" not in ADMISSIBLE_TERMS
    assert "bmid_sin2c" not in ADMISSIBLE_TERMS
    assert LAMBDA_GRID == (1.0, 3.0, 10.0, 30.0, 100.0)
    assert MAX_SELECTED_TERMS == 10
    assert MAX_CORRECTION_MM == 0.750

    zero = feature_matrix(np.array([0.0]), np.array([0.0]))
    assert np.max(np.abs(zero)) < 1e-12
    data = synthetic_dataset()
    assert len(data.poses) == UNIQUE_POSE_COUNT
    assert set(antipodal_group(data)) == {0.0, 45.0, 90.0, 135.0}
    all_rows = np.arange(len(data.poses))
    fit = fit_ridge(data, all_rows, tuple(range(5)), 0.0)
    expected_coefficients = np.arange(15, dtype=float).reshape(5, 3) * 0.001
    assert np.max(np.abs(fit.raw_center_coefficients - expected_coefficients)) < 1e-10
    assert metric(data.centers - predict_raw_centers(data, fit, all_rows)).maximum < 1e-10

    # A zero-response grid exercises deterministic ties: stronger lambda and
    # fixed pool order must win, and the selected path must respect the cap.
    zero_data = Dataset(
        data.observations,
        data.poses,
        data.b_deg,
        data.c_deg,
        np.zeros_like(data.centers),
        data.features,
    )
    selection = select_model(zero_data, all_rows)
    assert len(selection.path) == MAX_SELECTED_TERMS
    assert selection.winner.term_indices == (0,)
    assert selection.winner.ridge_lambda == max(LAMBDA_GRID)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--residuals", type=Path, default=DEFAULT_RESIDUALS)
    parser.add_argument("--pins", type=Path, default=DEFAULT_PINS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("self-test: PASS")
        return 0
    try:
        validate_hashes()
        observations, closures = validate_and_load()
        data = build_dataset(observations)
        all_rows = np.arange(len(data.poses))
        checkpoint = load_checkpoint(args.checkpoint)
        primary_checkpoint = checkpoint["primary"]
        if not isinstance(primary_checkpoint, dict):
            raise FitError("checkpoint primary section is invalid")

        if "forward" in primary_checkpoint:
            print("r2: restoring forward-only audit model", flush=True)
            forward_record = primary_checkpoint["forward"]
            if not isinstance(forward_record, dict):
                raise FitError("checkpoint forward selection is invalid")
            forward_selection = restore_selection(data, all_rows, forward_record)
        else:
            print("r2: selecting forward-only audit model", flush=True)
            forward_selection = select_model(data, all_rows, swap_refine=False)
            primary_checkpoint["forward"] = selection_record(forward_selection)
            write_checkpoint(args.checkpoint, checkpoint)

        if "refined" in primary_checkpoint:
            print("r2: restoring swap-refined primary", flush=True)
            refined_record = primary_checkpoint["refined"]
            if not isinstance(refined_record, dict):
                raise FitError("checkpoint refined selection is invalid")
            selection = restore_selection(data, all_rows, refined_record)
        else:
            print("r2: selecting swap-refined primary on 76 equal-weight T4 poses", flush=True)
            selection = select_model(data, all_rows)
            primary_checkpoint["refined"] = selection_record(selection)
            write_checkpoint(args.checkpoint, checkpoint)
        print(
            "r2: primary "
            f"lambda={selection.winner.ridge_lambda:g} "
            f"terms={','.join(term_names(selection.winner.term_indices))}",
            flush=True,
        )
        validations = []
        for grouping in ("signed-B", "paired-abs-B", "C-sector", "antipodal-C-pair"):
            print(f"r2: nested outer validation {grouping}", flush=True)
            validations.append(
                outer_validation(
                    data,
                    grouping,
                    checkpoint,
                    lambda: write_checkpoint(args.checkpoint, checkpoint),
                )
            )
        hal_values = parse_hal_values()
        write_residuals(args.residuals, data, selection.winner)
        write_pins(args.pins, selection.winner, hal_values)
        write_text_atomically(
            args.report,
            report_text(
                data,
                closures,
                forward_selection,
                selection,
                validations,
                hal_values,
                args.residuals,
                args.pins,
            ),
        )
    except (OSError, KeyError, ValueError, np.linalg.LinAlgError) as exc:
        print(f"T4-only r2 fit refused: {exc}", file=sys.stderr)
        return 1
    print("relocated-sphere T4-only fit r2: PASS")
    print(f"report: {args.report}")
    print(f"residuals: {args.residuals}")
    print(f"pins: {args.pins}")
    print(f"checkpoint: {args.checkpoint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
