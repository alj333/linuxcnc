#!/usr/bin/env python3
"""Fit the frozen campaign-04 T4 sphere data without reading the T3 holdout.

The primary candidate is deliberately fixed: nine existing headheadkins surface
terms, standardized ridge lambda 30, and equal total weight per unique (B, C)
pose.  This program only reads the exact T4 inputs and the frozen program/HAL
snapshots listed below.  It never imports LinuxCNC or HAL control APIs and never
loads or edits machine configuration.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Callable, Iterable, Sequence

import numpy as np


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

RESULTS_PATH = HERE / "tcpc-relocated-sphere-t4-primary-results.csv"
STATE_PATH = HERE / "tcpc-relocated-sphere-t4-primary-state.csv"
CLOSURES_PATH = HERE / "tcpc-relocated-sphere-t4-primary-closures.csv"
PROGRAM_PATH = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_primary.ngc"
HAL_PATH = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"

DEFAULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_T4_FIT_REPORT.md"
DEFAULT_RESIDUALS = HERE / "tcpc-relocated-sphere-t4-fit-residuals.csv"

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
ROW_COUNT = 101
CLOSURE_COUNT = 28
UNIQUE_POSE_COUNT = 76
RIDGE_LAMBDA = 30.0
LAMBDA_SENSITIVITY = (0.0, 1.0, 3.0, 10.0, 30.0, 100.0)
NESTED_LAMBDAS = (1.0, 3.0, 10.0, 30.0, 100.0)
AXES = ("x", "y", "z")

# These angle offsets are inputs to the exact headheadkins basis functions.
B_ZERO_DEG = 0.0
C_ZERO_DEG = -0.024500

# The model-selection boundary is frozen before the T3 holdout is read.
PRIMARY_TERMS = (
    "bc_omcb_sin2c",
    "c_cos",
    "bc_sinb_sinc",
    "bmid_sinc",
    "b_sin",
    "bc_sinb_cos2c",
    "bmid_cosc",
    "bmid_base",
    "c_sin",
)

PIN_STEMS = {
    "bc_omcb_sin2c": "headheadkins.bcross.omcb-sin2c",
    "c_cos": "headheadkins.charm.cos",
    "bc_sinb_sinc": "headheadkins.bcross.sinb-sinc",
    "bmid_sinc": "headheadkins.bmid.sinc",
    "b_sin": "headheadkins.bharm-m.sin",
    "bc_sinb_cos2c": "headheadkins.bcross.sinb-cos2c",
    "bmid_cosc": "headheadkins.bmid.cosc",
    "bmid_base": "headheadkins.bmid.base",
    "c_sin": "headheadkins.charm.sin",
}

RESULT_CENTER_FIELDS = ("center_abs_x_mm", "center_abs_y_mm", "center_abs_z_mm")
RESIDUAL_FIELDS = (
    "campaign_id",
    "attempt_id",
    "sample_seq",
    "abs_b_deg",
    "abs_c_deg",
    "pose_multiplicity",
    "fit_weight",
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
class RidgeFit:
    terms: tuple[str, ...]
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
class Metric:
    rms: float
    maximum: float


@dataclass(frozen=True)
class CvResult:
    metric: Metric
    worst_group: float
    worst_group_maximum: float


@dataclass(frozen=True)
class NestedFold:
    held_abs_b: float
    selected_lambda: float
    metric: Metric


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
            raise FitError(f"input SHA-256 changed for {path}: {actual}, expected {expected}")


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


def basis(b_deg: np.ndarray, c_deg: np.ndarray) -> dict[str, np.ndarray]:
    b_rad = np.radians(b_deg + B_ZERO_DEG)
    c_rad = np.radians(c_deg + C_ZERO_DEG)
    c_ref = math.radians(C_ZERO_DEG)
    sin_b = np.sin(b_rad)
    omc_b = 1.0 - np.cos(b_rad)
    sin_c = np.sin(c_rad)
    cos_c = np.cos(c_rad)
    mid_b = np.sin(2.0 * b_rad) ** 2
    return {
        "bc_omcb_sin2c": omc_b * sin_c * sin_c,
        "c_cos": cos_c - math.cos(c_ref),
        "bc_sinb_sinc": sin_b * sin_c,
        "bmid_sinc": mid_b * sin_c,
        "b_sin": sin_b,
        "bc_sinb_cos2c": sin_b * np.cos(2.0 * c_rad),
        "bmid_cosc": mid_b * cos_c,
        "bmid_base": mid_b,
        "c_sin": sin_c - math.sin(c_ref),
    }


def feature_matrix(
    b_deg: np.ndarray,
    c_deg: np.ndarray,
    terms: Sequence[str] = PRIMARY_TERMS,
) -> np.ndarray:
    values = basis(b_deg, c_deg)
    try:
        return np.column_stack([values[term] for term in terms])
    except KeyError as exc:
        raise FitError(f"unsupported model term {exc.args[0]!r}") from exc


def arrays(items: Sequence[UniquePose | Observation]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.array([item.b_deg for item in items]),
        np.array([item.c_deg for item in items]),
        np.vstack([item.center for item in items]),
    )


def fit_ridge(
    items: Sequence[UniquePose | Observation],
    ridge_lambda: float = RIDGE_LAMBDA,
    terms: Sequence[str] = PRIMARY_TERMS,
) -> RidgeFit:
    if not items:
        raise FitError("cannot fit an empty dataset")
    if ridge_lambda < 0.0:
        raise FitError("ridge lambda must be nonnegative")
    b_deg, c_deg, centers = arrays(items)
    features = feature_matrix(b_deg, c_deg, terms)
    feature_mean = np.mean(features, axis=0)
    feature_scale = np.std(features, axis=0)
    if np.any(feature_scale <= 1e-12):
        bad = [term for term, scale in zip(terms, feature_scale) if scale <= 1e-12]
        raise FitError(f"training fold cannot identify terms: {bad}")
    standardized = (features - feature_mean) / feature_scale
    center_mean = np.mean(centers, axis=0)
    centered = centers - center_mean
    gram = standardized.T @ standardized
    right = standardized.T @ centered
    if ridge_lambda == 0.0:
        coefficients = np.linalg.lstsq(standardized, centered, rcond=None)[0]
    else:
        coefficients = np.linalg.solve(
            gram + ridge_lambda * np.eye(len(terms)),
            right,
        )
    return RidgeFit(
        tuple(terms),
        ridge_lambda,
        feature_mean,
        feature_scale,
        coefficients,
        center_mean,
    )


def predict_raw_centers(
    fit: RidgeFit,
    items: Sequence[UniquePose | Observation],
) -> np.ndarray:
    b_deg, c_deg, _ = arrays(items)
    features = feature_matrix(b_deg, c_deg, fit.terms)
    standardized = (features - fit.feature_mean) / fit.feature_scale
    return fit.center_mean + standardized @ fit.standardized_coefficients


def correction_offsets(
    fit: RidgeFit,
    items: Sequence[UniquePose | Observation],
) -> np.ndarray:
    b_deg, c_deg, _ = arrays(items)
    return feature_matrix(b_deg, c_deg, fit.terms) @ fit.correction_deltas


def corrected_centers(
    fit: RidgeFit,
    items: Sequence[UniquePose | Observation],
) -> np.ndarray:
    _, _, centers = arrays(items)
    return centers + correction_offsets(fit, items)


def residuals_about_mean(values: np.ndarray) -> np.ndarray:
    return values - np.mean(values, axis=0)


def metric(residuals: np.ndarray) -> Metric:
    norms = np.linalg.norm(residuals, axis=1)
    return Metric(float(math.sqrt(np.mean(norms**2))), float(np.max(norms)))


def fit_metric(fit: RidgeFit, items: Sequence[UniquePose | Observation]) -> Metric:
    return metric(residuals_about_mean(corrected_centers(fit, items)))


def grouped_cv(
    poses: Sequence[UniquePose],
    group: Callable[[UniquePose], float],
    ridge_lambda: float = RIDGE_LAMBDA,
) -> CvResult:
    groups = sorted({group(pose) for pose in poses})
    all_residuals: list[np.ndarray] = []
    worst_group = float("nan")
    worst_maximum = -1.0
    for held_group in groups:
        training = [pose for pose in poses if group(pose) != held_group]
        held = [pose for pose in poses if group(pose) == held_group]
        fit = fit_ridge(training, ridge_lambda)
        residuals = np.vstack([pose.center for pose in held]) - predict_raw_centers(fit, held)
        all_residuals.append(residuals)
        held_maximum = metric(residuals).maximum
        if held_maximum > worst_maximum:
            worst_group = held_group
            worst_maximum = held_maximum
    return CvResult(metric(np.vstack(all_residuals)), worst_group, worst_maximum)


def inner_abs_b_score(poses: Sequence[UniquePose], ridge_lambda: float) -> tuple[float, float]:
    result = grouped_cv(poses, lambda pose: abs(pose.b_deg), ridge_lambda)
    return result.metric.rms, result.metric.maximum


def nested_abs_b_cv(poses: Sequence[UniquePose]) -> tuple[Metric, tuple[NestedFold, ...]]:
    residual_blocks: list[np.ndarray] = []
    folds: list[NestedFold] = []
    for held_abs_b in sorted({abs(pose.b_deg) for pose in poses}):
        training = [pose for pose in poses if abs(pose.b_deg) != held_abs_b]
        held = [pose for pose in poses if abs(pose.b_deg) == held_abs_b]
        candidates: list[tuple[float, float, float]] = []
        for ridge_lambda in NESTED_LAMBDAS:
            rms, maximum = inner_abs_b_score(training, ridge_lambda)
            candidates.append((rms, maximum, -ridge_lambda))
        _, _, negative_lambda = min(candidates)
        selected_lambda = -negative_lambda
        fit = fit_ridge(training, selected_lambda)
        residuals = np.vstack([pose.center for pose in held]) - predict_raw_centers(fit, held)
        residual_blocks.append(residuals)
        folds.append(NestedFold(held_abs_b, selected_lambda, metric(residuals)))
    return metric(np.vstack(residual_blocks)), tuple(folds)


def pose_design_condition(poses: Sequence[UniquePose]) -> tuple[int, float, float]:
    b_deg, c_deg, _ = arrays(poses)
    features = feature_matrix(b_deg, c_deg)
    centered = features - np.mean(features, axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    raw_condition = float(singular[0] / singular[-1])
    scaled = centered / np.linalg.norm(centered, axis=0)
    scaled_singular = np.linalg.svd(scaled, compute_uv=False)
    scaled_condition = float(scaled_singular[0] / scaled_singular[-1])
    return int(np.linalg.matrix_rank(centered)), raw_condition, scaled_condition


def signed_pair_metrics(
    poses: Sequence[UniquePose],
    adjusted: np.ndarray,
) -> list[tuple[float, Metric, Metric]]:
    lookup = {
        (pose.b_deg, pose.c_deg): center
        for pose, center in zip(poses, adjusted)
    }
    b0 = {c: center for (b, c), center in lookup.items() if b == 0.0}
    output: list[tuple[float, Metric, Metric]] = []
    for abs_b in (5.0, 10.0, 15.0, 30.0, 45.0, 60.0, 90.0):
        c_values = sorted(
            {c for b, c in lookup if b == abs_b}
            & {c for b, c in lookup if b == -abs_b}
        )
        odd = np.vstack(
            [(lookup[(abs_b, c)] - lookup[(-abs_b, c)]) / 2.0 for c in c_values]
        )
        even = np.vstack(
            [
                (lookup[(abs_b, c)] + lookup[(-abs_b, c)]) / 2.0 - b0[c]
                for c in c_values
            ]
        )
        output.append((abs_b, metric(odd), metric(even)))
    return output


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


def format_metric(value: Metric) -> str:
    return f"`{value.rms:.6f} / {value.maximum:.6f}`"


def coefficient_stability(
    poses: Sequence[UniquePose],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    full = fit_ridge(poses).correction_deltas
    folded = []
    for held_abs_b in sorted({abs(pose.b_deg) for pose in poses}):
        training = [pose for pose in poses if abs(pose.b_deg) != held_abs_b]
        folded.append(fit_ridge(training).correction_deltas)
    fold_array = np.stack(folded)
    standard_deviation = np.std(fold_array, axis=0)
    direction_agreement = np.array(
        [
            sum(np.dot(full[index], fold[index]) > 0.0 for fold in fold_array)
            for index in range(len(PRIMARY_TERMS))
        ]
    )
    return full, standard_deviation, direction_agreement


def write_residuals(
    path: Path,
    observations: Sequence[Observation],
    poses: Sequence[UniquePose],
    fit: RidgeFit,
) -> None:
    pose_multiplicity = {
        (pose.b_deg, pose.c_deg): pose.multiplicity for pose in poses
    }
    current_centers = np.vstack([observation.center for observation in observations])
    offsets = correction_offsets(fit, observations)
    candidate_centers = current_centers + offsets

    # References use equal-pose means, matching the primary fit's weighting.
    pose_current_reference = np.mean(np.vstack([pose.center for pose in poses]), axis=0)
    pose_candidate_reference = np.mean(corrected_centers(fit, poses), axis=0)

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
        writer = csv.DictWriter(stream, fieldnames=RESIDUAL_FIELDS)
        writer.writeheader()
        for observation, offset, candidate in zip(observations, offsets, candidate_centers):
            multiplicity = pose_multiplicity[(observation.b_deg, observation.c_deg)]
            current_residual = observation.center - pose_current_reference
            candidate_residual = candidate - pose_candidate_reference
            row: dict[str, str | int] = {
                "campaign_id": CAMPAIGN,
                "attempt_id": ATTEMPT,
                "sample_seq": observation.seq,
                "abs_b_deg": f"{observation.b_deg:.6f}",
                "abs_c_deg": f"{observation.c_deg:.6f}",
                "pose_multiplicity": multiplicity,
                "fit_weight": f"{1.0 / multiplicity:.9f}",
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
            writer.writerow(row)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def report_text(
    observations: Sequence[Observation],
    closures: Sequence[dict[str, str]],
    poses: Sequence[UniquePose],
    fit: RidgeFit,
) -> str:
    _, _, raw_row_centers = arrays(observations)
    _, _, raw_pose_centers = arrays(poses)
    current_row_metric = metric(residuals_about_mean(raw_row_centers))
    current_pose_metric = metric(residuals_about_mean(raw_pose_centers))
    candidate_row_metric = fit_metric(fit, observations)
    candidate_pose_metric = fit_metric(fit, poses)
    closures_array = np.array([number(row, "closure_norm_mm") for row in closures])
    closure_metric = Metric(
        float(math.sqrt(np.mean(closures_array**2))),
        float(np.max(closures_array)),
    )

    signed_cv = grouped_cv(poses, lambda pose: pose.b_deg)
    abs_b_cv = grouped_cv(poses, lambda pose: abs(pose.b_deg))
    c_cv = grouped_cv(poses, lambda pose: pose.c_deg)
    nested_metric, nested_folds = nested_abs_b_cv(poses)
    rank, raw_condition, scaled_condition = pose_design_condition(poses)

    raw_pairs = signed_pair_metrics(poses, raw_pose_centers)
    candidate_pairs = signed_pair_metrics(poses, corrected_centers(fit, poses))
    candidate_pairs_by_b = {item[0]: item for item in candidate_pairs}

    hal_values = parse_hal_values()
    deltas, fold_std, direction_agreement = coefficient_stability(poses)

    row_fit = fit_ridge(observations)
    coefficient_weight_sensitivity = np.linalg.norm(
        fit.correction_deltas - row_fit.correction_deltas,
        axis=1,
    )
    pose_adjustment_difference = correction_offsets(fit, poses) - correction_offsets(row_fit, poses)
    weighting_adjustment_maximum = float(
        np.max(np.linalg.norm(pose_adjustment_difference, axis=1))
    )

    lines = [
        "# Relocated-Sphere T4-Only Fit Report",
        "",
        "This report freezes the candidate before the T3 holdout is read. The fitter",
        "has no T3 input path and performs no LinuxCNC, HAL, or machine-control action.",
        "The values below are offline predictions, not authorized machine settings.",
        "",
        "## Frozen Inputs",
        "",
        f"- campaign/mode/attempt: `{CAMPAIGN} / {MODE} / {ATTEMPT}`",
        f"- accepted result/state rows: `{len(observations)} / {len(observations)}`",
        f"- strict closures: `{len(closures)}`; RMS/max {format_metric(closure_metric)} mm",
        f"- equal-weight unique poses: `{len(poses)}`",
        "- all result, state, pose, correction-enabled, and closure contracts: `PASS`",
        "",
        "| frozen raw input | SHA-256 |",
        "| --- | --- |",
    ]
    for path, digest in EXPECTED_SHA256.items():
        lines.append(f"| `{path.relative_to(REPO_ROOT)}` | `{digest}` |")

    lines.extend(
        [
            "",
            "## Current Error",
            "",
            "Metrics are three-dimensional centered RMS / maximum in millimetres.",
            f"The official 101-row current metric is {format_metric(current_row_metric)}.",
            f"After averaging repeated identical poses, the current metric is {format_metric(current_pose_metric)}.",
            "The largest raw row is B-90/C270. Same-pose closures are an order of",
            "magnitude smaller, so the dominant error is pose-dependent rather than",
            "probe repeatability or run drift.",
            "",
            "Signed-pair decomposition uses `(B+ - B-)/2` for the odd component and",
            "`(B+ + B-)/2 - B0(C)` for the even component.",
            "",
            "| abs(B) | current odd | candidate odd | current even | candidate even |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for abs_b, raw_odd, raw_even in raw_pairs:
        _, candidate_odd, candidate_even = candidate_pairs_by_b[abs_b]
        lines.append(
            f"| {abs_b:.0f} | {format_metric(raw_odd)} | {format_metric(candidate_odd)} | "
            f"{format_metric(raw_even)} | {format_metric(candidate_even)} |"
        )

    lines.extend(
        [
            "",
            "The even component grows most strongly with B and is dominant at high B,",
            "especially C270. A smaller odd-B component is also repeatable. This supports",
            "surface terms with both B-sign parity classes; it does not support replacing",
            "the error with a single B/C zero or rigid translation.",
            "",
            "## Frozen Candidate",
            "",
            f"Primary estimator: standardized ridge regression with lambda `{RIDGE_LAMBDA:.1f}`.",
            "Each distinct `(B,C)` pose has total weight one. Repeated C0 closure rows",
            "are averaged within their pose and do not receive extra model weight.",
            f"The centered scalar design has rank `{rank}/{len(PRIMARY_TERMS)}`, raw condition",
            f"`{raw_condition:.3e}`, and standardized condition `{scaled_condition:.3f}`.",
            "",
            "The fixed nine-term family is:",
            "",
            "```text",
            ", ".join(PRIMARY_TERMS),
            "```",
            "",
            "`bc_omcb_sin2c` follows the existing implementation name; its actual basis",
            "is `(1-cos(B))*sin(C)^2`. Terms proportional to `sin(B)*sin(2C)` and",
            "`sin(B)^2`-midband `sin(2C)` remain frozen at zero because C135/C315",
            "are collision omissions at nonzero B. Their opposite `sin(2C)` phase is",
            "therefore not physically observed.",
            "",
            "| weighting | current | candidate prediction |",
            "| --- | ---: | ---: |",
            f"| 76 equal unique poses | {format_metric(current_pose_metric)} | {format_metric(candidate_pose_metric)} |",
            f"| all 101 diagnostic rows | {format_metric(current_row_metric)} | {format_metric(candidate_row_metric)} |",
            "",
            "## T4 Validation",
            "",
            "All fits below use T4 only. Fixed-family group holdouts refit the coefficients",
            "without the named group and predict its absolute center from the remaining",
            "groups.",
            "",
            "| validation | RMS / max mm | worst group / max mm |",
            "| --- | ---: | ---: |",
            f"| leave one signed B block out | {format_metric(signed_cv.metric)} | B{signed_cv.worst_group:+g} / `{signed_cv.worst_group_maximum:.6f}` |",
            f"| leave one paired abs(B) group out | {format_metric(abs_b_cv.metric)} | abs(B){abs_b_cv.worst_group:g} / `{abs_b_cv.worst_group_maximum:.6f}` |",
            f"| leave one C sector out | {format_metric(c_cv.metric)} | C{c_cv.worst_group:g} / `{c_cv.worst_group_maximum:.6f}` |",
            "",
            "Nested leave-abs(B) validation chooses lambda only inside each outer training",
            "fold from `{1,3,10,30,100}`. Its outer metric is",
            f"{format_metric(nested_metric)}. This is a sensitivity check; it does not",
            f"change the frozen primary lambda `{RIDGE_LAMBDA:.1f}`.",
            "",
            "| outer held abs(B) | inner-selected lambda | outer RMS / max mm |",
            "| ---: | ---: | ---: |",
        ]
    )
    for fold in nested_folds:
        lines.append(
            f"| {fold.held_abs_b:.0f} | {fold.selected_lambda:.0f} | {format_metric(fold.metric)} |"
        )

    lines.extend(
        [
            "",
            "C270 is essential training evidence. Leaving it out is the worst C-sector",
            "test, so this surface must not be extrapolated to unmeasured C sectors.",
            "The planned T3 poses are all within the measured C quadrants; T3 tests",
            "probe-length transfer, not an unmeasured-C extrapolation.",
            "",
            "## Lambda And Weighting Sensitivity",
            "",
            "| lambda | equal-pose train | leave signed B | leave abs(B) | leave C |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for ridge_lambda in LAMBDA_SENSITIVITY:
        sensitivity_fit = fit_ridge(poses, ridge_lambda)
        train_metric = fit_metric(sensitivity_fit, poses)
        sensitivity_signed = grouped_cv(poses, lambda pose: pose.b_deg, ridge_lambda)
        sensitivity_abs = grouped_cv(poses, lambda pose: abs(pose.b_deg), ridge_lambda)
        sensitivity_c = grouped_cv(poses, lambda pose: pose.c_deg, ridge_lambda)
        lines.append(
            f"| {ridge_lambda:g} | {format_metric(train_metric)} | "
            f"{format_metric(sensitivity_signed.metric)} | {format_metric(sensitivity_abs.metric)} | "
            f"{format_metric(sensitivity_c.metric)} |"
        )

    lines.extend(
        [
            "",
            "A row-weighted refit changes the predicted adjustment over the 76 unique",
            f"poses by at most `{weighting_adjustment_maximum:.6f} mm`. The primary remains",
            "the equal-pose fit because repeated C0 closure samples are repeatability",
            "evidence, not a reason to weight C0 more heavily in calibration.",
            "",
            "## Offline Pin Mapping",
            "",
            "These are analysis values only. `delta` is the fitted addition to the current",
            "pin; `predicted total` is shown for audit and is not an executable HAL block.",
            "Fold SD is the vector norm of coefficient variation across leave-abs(B) fits.",
            "",
            "| basis term | existing pin stem | current XYZ | delta XYZ | predicted total XYZ | fold SD | direction | weighting delta |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, term in enumerate(PRIMARY_TERMS):
        stem = PIN_STEMS[term]
        current = np.array([hal_values[f"{stem}.{axis}"] for axis in AXES])
        delta = deltas[index]
        predicted = current + delta
        lines.append(
            f"| `{term}` | `{stem}.[xyz]` | "
            f"`{current[0]:+.9f}, {current[1]:+.9f}, {current[2]:+.9f}` | "
            f"`{delta[0]:+.9f}, {delta[1]:+.9f}, {delta[2]:+.9f}` | "
            f"`{predicted[0]:+.9f}, {predicted[1]:+.9f}, {predicted[2]:+.9f}` | "
            f"`{np.linalg.norm(fold_std[index]):.6f}` | "
            f"`{direction_agreement[index]}/8` | "
            f"`{coefficient_weight_sensitivity[index]:.6f}` |"
        )

    lines.extend(
        [
            "",
            "The candidate may require up to the maximum adjustment listed in the residual",
            "CSV. It must not be loaded before holdout evaluation, a fresh configured-limit",
            "replay, and an explicit operator release.",
            "",
            "## Frozen T3 Acceptance Gates",
            "",
            "The following gates were fixed without reading T3 values:",
            "",
            "1. The completed T3 schema, state, pose, contact-quality, and all 14 closure",
            "   contracts must pass. A partial or reseated-probe splice is rejected.",
            "2. Apply this exact nine-term coefficient delta offline with no T3 refit, no",
            "   lambda change, no term selection, and a separately centered constant sphere",
            "   center for the T3 leg.",
            "3. Candidate T3 centered RMS must improve current RMS by both at least 10% and",
            "   at least 0.010 mm.",
            "4. Candidate T3 maximum must improve current maximum by both at least 10% and",
            "   at least 0.020 mm.",
            "5. Candidate RMS must improve separately for the paired abs(B)=45 and abs(B)=90",
            "   groups. B0 RMS may not worsen by more than 0.010 mm.",
            "6. No individual T3 pose residual norm may worsen by more than 0.050 mm.",
            "7. Passing these offline gates freezes a proposed parameter revision only. It",
            "   does not authorize a HAL edit or machine motion. Live release still requires",
            "   reviewed parameter bounds, configured-limit replay, a new immutable archive,",
            "   and operator authorization.",
            "",
            "If any gate fails, reject this family. Do not inspect T3 to choose another",
            "family; a different family requires a new untouched verification campaign.",
            "",
            "## Decision",
            "",
            "Freeze this nine-term lambda-30 candidate as the sole campaign-04 offline",
            "prediction. Keep all rigid geometry, B/C zeros, and live correction pins",
            "unchanged until the T3 holdout is completed and evaluated against the gates",
            "above.",
            "",
            "Detailed per-row predictions: `tcpc-relocated-sphere-t4-fit-residuals.csv`",
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


def self_test() -> None:
    assert len(PRIMARY_TERMS) == 9
    assert set(PRIMARY_TERMS) == set(PIN_STEMS)
    assert "bc_sinb_sin2c" not in PRIMARY_TERMS
    assert "bmid_sin2c" not in PRIMARY_TERMS
    zero = feature_matrix(np.array([0.0]), np.array([0.0]))
    assert np.max(np.abs(zero)) < 1e-12
    synthetic: list[UniquePose] = []
    coefficient = np.arange(27, dtype=float).reshape(9, 3) * 0.001
    for slot, (b_deg, c_deg) in enumerate(expected_poses(), start=1):
        if any(pose.b_deg == b_deg and pose.c_deg == c_deg for pose in synthetic):
            continue
        features = feature_matrix(np.array([b_deg]), np.array([c_deg]))[0]
        center = np.array([1.0, 2.0, 3.0]) + features @ coefficient
        synthetic.append(UniquePose(b_deg, c_deg, center, (slot,)))
    assert len(synthetic) == UNIQUE_POSE_COUNT
    fit = fit_ridge(synthetic, 0.0)
    assert np.max(np.abs(fit.raw_center_coefficients - coefficient)) < 1e-10
    assert fit_metric(fit, synthetic).maximum < 1e-10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--residuals", type=Path, default=DEFAULT_RESIDUALS)
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
        poses = unique_poses(observations)
        fit = fit_ridge(poses)
        write_residuals(args.residuals, observations, poses, fit)
        write_text_atomically(args.report, report_text(observations, closures, poses, fit))
    except (OSError, KeyError, ValueError, np.linalg.LinAlgError) as exc:
        print(f"T4-only fit refused: {exc}", file=sys.stderr)
        return 1
    print("relocated-sphere T4-only fit: PASS")
    print(f"report: {args.report}")
    print(f"residuals: {args.residuals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
