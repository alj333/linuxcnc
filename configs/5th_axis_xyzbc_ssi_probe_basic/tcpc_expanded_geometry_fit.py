#!/usr/bin/env python3
"""Run-state-aware offline TCPC geometry fit for XYZBC calibration data.

This intentionally does not write HAL values. It compares model families and
generates a report so candidate kinematics changes can be reviewed before any
live machine test.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.optimize import least_squares


CONFIG_DIR = Path(__file__).resolve().parent

# Baseline geometry that was loaded before the 2026-05-04 C-center correction.
NOMINAL_C_TO_B = np.array([0.010934, 0.0, -270.000000])
BASE_CAL_C_TO_B = np.array([-0.065000, 0.014000, 0.0])
NOMINAL_B_TO_TOOL = np.array([-0.668710, -26.721365, -308.980001])
BASE_CAL_B_TO_TOOL = np.array([0.0, 0.0, 0.815000])
BASE_B_ZERO_DEG = 0.0
BASE_C_ZERO_DEG = -0.024500

# Live-validated C-center correction from the B0 C-quadrant run.
VALIDATED_CAL_C_TO_B = np.array([0.035886006, 0.009526306, 0.0])
FIXED_C_CENTER = {
    "dcx": float(VALIDATED_CAL_C_TO_B[0] - BASE_CAL_C_TO_B[0]),
    "dcy": float(VALIDATED_CAL_C_TO_B[1] - BASE_CAL_C_TO_B[1]),
}

# Machine-fixed B-harmonic candidate tested live on 2026-05-04.
MACHINE_BHARMONIC_CANDIDATE = {
    "mb_sin_b_x": 0.003457595,
    "mb_sin_b_y": 0.071987315,
    "mb_sin_b_z": 0.318267363,
    "mb_omc_b_x": 0.108123741,
    "mb_omc_b_y": 0.034446993,
    "mb_omc_b_z": -0.364472105,
    "mb_sin_2b_x": -0.032225192,
    "mb_sin_2b_y": 0.005230194,
    "mb_sin_2b_z": -0.190772593,
}

# Live-tested B/C cross candidate. This is the same machine-fixed B-harmonic
# candidate plus the incremental B/C cross layer.
BCROSS_CANDIDATE = {
    **MACHINE_BHARMONIC_CANDIDATE,
    "bc_sinb_sinc_x": 0.002528625,
    "bc_sinb_sinc_y": 0.322704792,
    "bc_sinb_sinc_z": 0.129756713,
    "bc_omcb_sinc_x": -0.075154781,
    "bc_omcb_sinc_y": 0.002088037,
    "bc_omcb_sinc_z": -0.001416604,
    "bc_omcb_sin2c_x": 0.015430253,
    "bc_omcb_sin2c_y": -0.178186533,
    "bc_omcb_sin2c_z": -0.027922013,
    "bc_sinb_cosc_x": -0.047944843,
    "bc_sinb_cosc_y": -0.063115561,
    "bc_sinb_cosc_z": -0.018569166,
    "bc_omcb_cosc_x": -0.033954526,
    "bc_omcb_cosc_y": 0.071241728,
    "bc_omcb_cosc_z": -0.000964915,
}


@dataclass(frozen=True)
class Observation:
    source: str
    group: str
    line: int
    b_deg: float
    c_deg: float
    center: np.ndarray
    active_name: str
    active_cal_c_to_b: np.ndarray
    active_bharmonic_params: dict[str, float] | None

    @property
    def label(self) -> str:
        return f"{self.source}:L{self.line}:B{self.b_deg:+.0f}C{self.c_deg:.0f}"


@dataclass(frozen=True)
class FitResult:
    model: str
    params: dict[str, float]
    result: object | None


PARAM_BOUNDS = {
    "dcx": (-3.0, 3.0),
    "dcy": (-3.0, 3.0),
    "dcz": (-3.0, 3.0),
    "dbx": (-5.0, 5.0),
    "dby": (-5.0, 5.0),
    "dbz": (-5.0, 5.0),
    "b_zero": (-0.50, 0.50),
    "c_zero": (-0.50, 0.50),
    "c_tilt_x": (-0.50, 0.50),
    "c_tilt_y": (-0.50, 0.50),
    "b_axis_x": (-0.50, 0.50),
    "b_axis_z": (-0.50, 0.50),
    "lin_xx": (-0.0020, 0.0020),
    "lin_xy": (-0.0020, 0.0020),
    "lin_xz": (-0.0020, 0.0020),
    "lin_yx": (-0.0020, 0.0020),
    "lin_yy": (-0.0020, 0.0020),
    "lin_yz": (-0.0020, 0.0020),
    "lin_zx": (-0.0020, 0.0020),
    "lin_zy": (-0.0020, 0.0020),
    "lin_zz": (-0.0020, 0.0020),
}

B_HARMONIC_TERMS = ["sin_b", "omc_b", "sin_2b"]
B_HARMONIC_AXES = ["x", "y", "z"]
B_CROSS_TERMS = ["sinb_sinc", "omcb_sinc", "omcb_sin2c", "sinb_cosc", "omcb_cosc"]
B_CROSS_TERM_PINS = [
    ("sinb_sinc", "sinb-sinc"),
    ("omcb_sinc", "omcb-sinc"),
    ("omcb_sin2c", "omcb-sin2c"),
    ("sinb_cosc", "sinb-cosc"),
    ("omcb_cosc", "omcb-cosc"),
]


def harmonic_param_names(prefix: str) -> list[str]:
    return [
        f"{prefix}_{term}_{axis}"
        for term in B_HARMONIC_TERMS
        for axis in B_HARMONIC_AXES
    ]


B_HARMONIC_MACHINE_PARAMS = harmonic_param_names("mb")
B_HARMONIC_CFRAME_PARAMS = harmonic_param_names("cf")
B_CROSS_MACHINE_PARAMS = [
    f"bc_{term}_{axis}"
    for term in B_CROSS_TERMS
    for axis in B_HARMONIC_AXES
]

for harmonic_param in B_HARMONIC_MACHINE_PARAMS + B_HARMONIC_CFRAME_PARAMS + B_CROSS_MACHINE_PARAMS:
    PARAM_BOUNDS[harmonic_param] = (-1.5, 1.5)


MODEL_FAMILIES = {
    "base_current": [],
    "c_center_xy": ["dcx", "dcy"],
    "c_center_fixed_only": [],
    "b_zero_only": ["b_zero"],
    "b_zero_btool_z": ["b_zero", "dbz"],
    "current_pins_no_cxy": ["dcz", "dbx", "dby", "dbz", "b_zero", "c_zero"],
    "b_harmonic_machine_no_cxy": B_HARMONIC_MACHINE_PARAMS,
    "b_harmonic_cframe_no_cxy": B_HARMONIC_CFRAME_PARAMS,
    "b_harmonic_machine_cframe_no_cxy": B_HARMONIC_MACHINE_PARAMS + B_HARMONIC_CFRAME_PARAMS,
    "b_cross_machine_no_cxy": B_CROSS_MACHINE_PARAMS,
    "b_harmonic_machine_bcross_no_cxy": B_HARMONIC_MACHINE_PARAMS + B_CROSS_MACHINE_PARAMS,
    "c_tilt_b_harmonic_cframe_no_cxy": [
        "c_tilt_x",
        "c_tilt_y",
        *B_HARMONIC_CFRAME_PARAMS,
    ],
    "c_tilt_b_harmonic_machine_cframe_no_cxy": [
        "c_tilt_x",
        "c_tilt_y",
        *B_HARMONIC_MACHINE_PARAMS,
        *B_HARMONIC_CFRAME_PARAMS,
    ],
    "axis_vectors_no_cxy": [
        "dcz",
        "dbx",
        "dby",
        "dbz",
        "b_zero",
        "c_zero",
        "c_tilt_x",
        "c_tilt_y",
        "b_axis_x",
        "b_axis_z",
    ],
    "axis_vectors_linear_diag_no_cxy": [
        "dcz",
        "dbx",
        "dby",
        "dbz",
        "b_zero",
        "c_zero",
        "c_tilt_x",
        "c_tilt_y",
        "b_axis_x",
        "b_axis_z",
        "lin_xx",
        "lin_yy",
        "lin_zz",
    ],
    "axis_vectors_linear_full_no_cxy": [
        "dcz",
        "dbx",
        "dby",
        "dbz",
        "b_zero",
        "c_zero",
        "c_tilt_x",
        "c_tilt_y",
        "b_axis_x",
        "b_axis_z",
        "lin_xx",
        "lin_xy",
        "lin_xz",
        "lin_yx",
        "lin_yy",
        "lin_yz",
        "lin_zx",
        "lin_zy",
        "lin_zz",
    ],
}

HIGH_B_MODELS = [
    "c_center_fixed_only",
    "b_zero_only",
    "b_zero_btool_z",
    "current_pins_no_cxy",
    "b_harmonic_machine_no_cxy",
    "b_harmonic_cframe_no_cxy",
    "b_harmonic_machine_cframe_no_cxy",
    "b_cross_machine_no_cxy",
    "b_harmonic_machine_bcross_no_cxy",
    "c_tilt_b_harmonic_cframe_no_cxy",
    "c_tilt_b_harmonic_machine_cframe_no_cxy",
    "axis_vectors_no_cxy",
    "axis_vectors_linear_diag_no_cxy",
    "axis_vectors_linear_full_no_cxy",
]


def read_results(
    path: Path,
    source: str,
    group: str,
    active_name: str,
    active_cal_c_to_b: np.ndarray,
    active_bharmonic_params: dict[str, float] | None = None,
    min_line: int | None = None,
    max_line: int | None = None,
    exclude_lines: Iterable[int] = (),
    include_lines: Iterable[int] | None = None,
) -> list[Observation]:
    observations: list[Observation] = []
    excluded = set(exclude_lines)
    included = set(include_lines) if include_lines is not None else None
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for line, row in enumerate(reader, start=2):
            if included is not None and line not in included:
                continue
            if min_line is not None and line < min_line:
                continue
            if max_line is not None and line > max_line:
                continue
            if line in excluded:
                continue
            if float(row["pass_num"]) != 2.0 or float(row["accepted"]) != 1.0:
                continue
            if float(row["u_corr_diam_mm"]) < 29.9 or float(row["v_corr_diam_mm"]) < 29.9:
                continue
            center = np.array(
                [
                    float(row["center_abs_x_mm"]),
                    float(row["center_abs_y_mm"]),
                    float(row["center_abs_z_mm"]),
                ]
            )
            observations.append(
                Observation(
                    source=source,
                    group=group,
                    line=line,
                    b_deg=float(row["abs_b_deg"]),
                    c_deg=float(row["abs_c_deg"]),
                    center=center,
                    active_name=active_name,
                    active_cal_c_to_b=active_cal_c_to_b.copy(),
                    active_bharmonic_params=(
                        active_bharmonic_params.copy()
                        if active_bharmonic_params is not None
                        else None
                    ),
                )
            )
    return observations


def rot_x(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rot_y(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rot_z(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c = math.cos(a)
    s = math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rot_axis(axis: np.ndarray, deg: float) -> np.ndarray:
    axis = axis / np.linalg.norm(axis)
    a = math.radians(deg)
    c = math.cos(a)
    s = math.sin(a)
    x, y, z = axis
    k = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    return (c * np.eye(3)) + (s * k) + ((1.0 - c) * np.outer(axis, axis))


def as_params(
    names: list[str],
    values: np.ndarray,
    fixed_params: dict[str, float] | None = None,
) -> dict[str, float]:
    params = {name: 0.0 for name in PARAM_BOUNDS}
    if fixed_params:
        params.update(fixed_params)
    for name, value in zip(names, values):
        params[name] = float(value)
    return params


def offset_for_c_cal(b_deg: float, c_deg: float, cal_c_to_b: np.ndarray) -> np.ndarray:
    b_eff = b_deg + BASE_B_ZERO_DEG
    c_eff = c_deg + BASE_C_ZERO_DEG
    c_to_b = NOMINAL_C_TO_B + cal_c_to_b
    b_to_tool = NOMINAL_B_TO_TOOL + BASE_CAL_B_TO_TOOL
    return rot_z(c_eff) @ (c_to_b + (rot_y(b_eff) @ b_to_tool))


def active_offset(obs: Observation) -> np.ndarray:
    offset = offset_for_c_cal(obs.b_deg, obs.c_deg, obs.active_cal_c_to_b)
    if obs.active_bharmonic_params is not None:
        active_params = as_params([], np.array([]), obs.active_bharmonic_params)
        offset = offset + b_harmonic_offset(obs.b_deg, obs.c_deg, active_params)
        offset = offset + b_cross_offset(obs.b_deg, obs.c_deg, active_params)
    return offset


def expanded_offset(b_deg: float, c_deg: float, params: dict[str, float]) -> np.ndarray:
    c_to_b = NOMINAL_C_TO_B + BASE_CAL_C_TO_B + np.array([params["dcx"], params["dcy"], params["dcz"]])
    b_to_tool = NOMINAL_B_TO_TOOL + BASE_CAL_B_TO_TOOL + np.array(
        [params["dbx"], params["dby"], params["dbz"]]
    )
    c_frame = rot_y(params["c_tilt_y"]) @ rot_x(params["c_tilt_x"])
    b_axis = np.array(
        [
            math.tan(math.radians(params["b_axis_x"])),
            1.0,
            math.tan(math.radians(params["b_axis_z"])),
        ]
    )
    b_eff = b_deg + BASE_B_ZERO_DEG + params["b_zero"]
    c_eff = c_deg + BASE_C_ZERO_DEG + params["c_zero"]
    local = c_to_b + (rot_axis(b_axis, b_eff) @ b_to_tool)
    return c_frame @ (rot_z(c_eff) @ local)


def b_harmonic_vector(prefix: str, b_deg: float, params: dict[str, float]) -> np.ndarray:
    b_eff = b_deg + BASE_B_ZERO_DEG + params["b_zero"]
    b_rad = math.radians(b_eff)
    values = {
        "sin_b": math.sin(b_rad),
        "omc_b": 1.0 - math.cos(b_rad),
        "sin_2b": math.sin(2.0 * b_rad),
    }
    correction = np.zeros(3)
    for term, value in values.items():
        correction += value * np.array(
            [
                params[f"{prefix}_{term}_x"],
                params[f"{prefix}_{term}_y"],
                params[f"{prefix}_{term}_z"],
            ]
        )
    return correction


def b_harmonic_offset(b_deg: float, c_deg: float, params: dict[str, float]) -> np.ndarray:
    c_eff = c_deg + BASE_C_ZERO_DEG + params["c_zero"]
    c_frame = rot_y(params["c_tilt_y"]) @ rot_x(params["c_tilt_x"])
    machine_fixed = b_harmonic_vector("mb", b_deg, params)
    cframe_rotating = c_frame @ (rot_z(c_eff) @ b_harmonic_vector("cf", b_deg, params))
    return machine_fixed + cframe_rotating


def b_cross_offset(b_deg: float, c_deg: float, params: dict[str, float]) -> np.ndarray:
    b_eff = b_deg + BASE_B_ZERO_DEG + params["b_zero"]
    c_eff = c_deg + BASE_C_ZERO_DEG + params["c_zero"]
    b_rad = math.radians(b_eff)
    c_rad = math.radians(c_eff)
    terms = {
        "sinb_sinc": math.sin(b_rad) * math.sin(c_rad),
        "omcb_sinc": (1.0 - math.cos(b_rad)) * math.sin(c_rad),
        "omcb_sin2c": (1.0 - math.cos(b_rad)) * math.sin(c_rad) * math.sin(c_rad),
        "sinb_cosc": math.sin(b_rad) * math.cos(c_rad),
        "omcb_cosc": (1.0 - math.cos(b_rad)) * math.cos(c_rad),
    }
    correction = np.zeros(3)
    for term, value in terms.items():
        correction += value * np.array(
            [
                params[f"bc_{term}_x"],
                params[f"bc_{term}_y"],
                params[f"bc_{term}_z"],
            ]
        )
    return correction


def linear_matrix(params: dict[str, float]) -> np.ndarray:
    return np.eye(3) + np.array(
        [
            [params["lin_xx"], params["lin_xy"], params["lin_xz"]],
            [params["lin_yx"], params["lin_yy"], params["lin_yz"]],
            [params["lin_zx"], params["lin_zy"], params["lin_zz"]],
        ]
    )


def physical_estimate(obs: Observation, params: dict[str, float]) -> np.ndarray:
    linear_position = obs.center - active_offset(obs)
    return (
        (linear_matrix(params) @ linear_position)
        + expanded_offset(obs.b_deg, obs.c_deg, params)
        + b_harmonic_offset(obs.b_deg, obs.c_deg, params)
        + b_cross_offset(obs.b_deg, obs.c_deg, params)
    )


def residual_matrix(observations: list[Observation], params: dict[str, float]) -> np.ndarray:
    if not observations:
        return np.empty((0, 3))
    estimates = np.array([physical_estimate(obs, params) for obs in observations])
    residuals = np.zeros_like(estimates)
    groups = sorted({obs.group for obs in observations})
    for group in groups:
        indexes = [i for i, obs in enumerate(observations) if obs.group == group]
        mean = np.mean(estimates[indexes], axis=0)
        residuals[indexes] = estimates[indexes] - mean
    return residuals


def residual_vector(
    names: list[str],
    values: np.ndarray,
    observations: list[Observation],
    fixed_params: dict[str, float] | None,
) -> np.ndarray:
    return residual_matrix(observations, as_params(names, values, fixed_params)).ravel()


def fit_model(
    name: str,
    observations: list[Observation],
    fixed_params: dict[str, float] | None = None,
) -> FitResult:
    names = MODEL_FAMILIES[name]
    if not names:
        params = as_params([], np.array([]), fixed_params)
        return FitResult(model=name, params=params, result=None)
    lower = np.array([PARAM_BOUNDS[param][0] for param in names])
    upper = np.array([PARAM_BOUNDS[param][1] for param in names])
    result = least_squares(
        lambda values: residual_vector(names, values, observations, fixed_params),
        np.zeros(len(names)),
        bounds=(lower, upper),
        loss="linear",
        x_scale="jac",
        max_nfev=20000,
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
    )
    return FitResult(model=name, params=as_params(names, result.x, fixed_params), result=result)


def fit_suite(
    model_names: list[str],
    observations: list[Observation],
    fixed_params: dict[str, float] | None = None,
) -> dict[str, FitResult]:
    return {name: fit_model(name, observations, fixed_params) for name in model_names}


def direct_residual_vector(
    names: list[str],
    values: np.ndarray,
    data_sets: list[list[Observation]],
    fixed_params: dict[str, float] | None,
) -> np.ndarray:
    params = as_params(names, values, fixed_params)
    residuals = []
    for observations in data_sets:
        _, rows = b_angle_delta_rows(observations, params)
        for _, delta in rows:
            residuals.extend(delta)
    return np.array(residuals)


def fit_direct_model(
    name: str,
    data_sets: list[list[Observation]],
    fixed_params: dict[str, float] | None = None,
) -> FitResult:
    names = MODEL_FAMILIES[name]
    if not names:
        params = as_params([], np.array([]), fixed_params)
        return FitResult(model=name, params=params, result=None)
    lower = np.array([PARAM_BOUNDS[param][0] for param in names])
    upper = np.array([PARAM_BOUNDS[param][1] for param in names])
    result = least_squares(
        lambda values: direct_residual_vector(names, values, data_sets, fixed_params),
        np.zeros(len(names)),
        bounds=(lower, upper),
        loss="linear",
        x_scale="jac",
        max_nfev=50000,
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
    )
    return FitResult(model=name, params=as_params(names, result.x, fixed_params), result=result)


def metrics(observations: list[Observation], params: dict[str, float]) -> dict[str, float]:
    if not observations:
        return {
            "points": 0,
            "rms3": float("nan"),
            "max3": float("nan"),
            "rms_x": float("nan"),
            "rms_y": float("nan"),
            "rms_z": float("nan"),
        }
    residuals = residual_matrix(observations, params)
    norms = np.linalg.norm(residuals, axis=1)
    return {
        "points": len(observations),
        "rms3": float(math.sqrt(np.mean(norms**2))),
        "max3": float(np.max(norms)),
        "rms_x": float(math.sqrt(np.mean(residuals[:, 0] ** 2))),
        "rms_y": float(math.sqrt(np.mean(residuals[:, 1] ** 2))),
        "rms_z": float(math.sqrt(np.mean(residuals[:, 2] ** 2))),
    }


def jacobian_condition(result: object | None) -> tuple[int, float]:
    if result is None or result.jac.size == 0:
        return (0, float("nan"))
    singular_values = np.linalg.svd(result.jac, compute_uv=False)
    if singular_values.size == 0:
        return (0, float("nan"))
    tol = singular_values[0] * max(result.jac.shape) * np.finfo(float).eps
    rank = int(np.sum(singular_values > tol))
    condition = float(singular_values[0] / singular_values[-1]) if singular_values[-1] > 0.0 else float("inf")
    return rank, condition


def metric_text(observations: list[Observation], params: dict[str, float]) -> str:
    m = metrics(observations, params)
    return f"{m['rms3']:.4f} / {m['max3']:.4f}"


def format_comparison_row(
    fit: FitResult,
    eval_sets: list[tuple[str, list[Observation]]],
) -> str:
    rank, cond = jacobian_condition(fit.result)
    cond_text = "n/a" if math.isnan(cond) else f"{cond:.2e}"
    metric_cols = [f"`{metric_text(observations, fit.params)}`" for _, observations in eval_sets]
    return f"| `{fit.model}` | {' | '.join(metric_cols)} | {rank} | {cond_text} |"


def format_comparison_table(
    fit_results: dict[str, FitResult],
    eval_sets: list[tuple[str, list[Observation]]],
) -> list[str]:
    headers = " | ".join([f"{name} RMS/max" for name, _ in eval_sets])
    align = " | ".join(["---:" for _ in eval_sets])
    lines = [
        f"| model | {headers} | rank | Jacobian cond |",
        f"| --- | {align} | ---: | ---: |",
    ]
    for fit in fit_results.values():
        lines.append(format_comparison_row(fit, eval_sets))
    return lines


def format_candidate_validation_table(
    fit_results: list[tuple[str, FitResult]],
    eval_sets: list[tuple[str, list[Observation]]],
) -> list[str]:
    data_sets = [observations for _, observations in eval_sets]
    all_observations = [obs for observations in data_sets for obs in observations]
    headers = " | ".join([f"{name} direct RMS/max" for name, _ in eval_sets])
    align = " | ".join(["---:" for _ in eval_sets])
    lines = [
        f"| model | all direct RMS/max | {headers} | residual RMS/max | rank | Jacobian cond |",
        f"| --- | ---: | {align} | ---: | ---: | ---: |",
    ]
    for label, fit in fit_results:
        rank, cond = jacobian_condition(fit.result)
        cond_text = "n/a" if math.isnan(cond) else f"{cond:.2e}"
        direct_cols = [
            b_angle_combined_delta_metric_text([observations], fit.params)
            for _, observations in eval_sets
        ]
        lines.append(
            f"| {label} | {b_angle_combined_delta_metric_text(data_sets, fit.params)} | "
            f"{' | '.join(direct_cols)} | `{metric_text(all_observations, fit.params)}` | "
            f"{rank} | {cond_text} |"
        )
    return lines


def format_direct_refit_table(
    fit_results: list[tuple[str, str, FitResult]],
    eval_sets: list[tuple[str, list[Observation]]],
) -> list[str]:
    headers = " | ".join([f"{name} direct RMS/max" for name, _ in eval_sets])
    align = " | ".join(["---:" for _ in eval_sets])
    lines = [
        f"| model | train set | {headers} | rank | Jacobian cond |",
        f"| --- | --- | {align} | ---: | ---: |",
    ]
    for label, train_set, fit in fit_results:
        rank, cond = jacobian_condition(fit.result)
        cond_text = "n/a" if math.isnan(cond) else f"{cond:.2e}"
        direct_cols = [
            b_angle_combined_delta_metric_text([observations], fit.params)
            for _, observations in eval_sets
        ]
        lines.append(
            f"| {label} | {train_set} | {' | '.join(direct_cols)} | "
            f"{rank} | {cond_text} |"
        )
    return lines


def format_params(params: dict[str, float], names: list[str]) -> list[str]:
    lines = []
    for name in names:
        value = params[name]
        lo, hi = PARAM_BOUNDS[name]
        marker = ""
        if abs(value - lo) < 1e-7 or abs(value - hi) < 1e-7:
            marker = "  # at bound"
        lines.append(f"- `{name}` = `{value:.9f}`{marker}")
    return lines


def b_harmonic_sim_hal_block(params: dict[str, float]) -> list[str]:
    term_pins = [
        ("sin_b", "sin"),
        ("omc_b", "omc"),
        ("sin_2b", "sin2"),
    ]
    families = [
        ("m", "mb"),
        ("c", "cf"),
    ]
    lines = ["```hal", "setp headheadkins.sim-bharm-enable 0"]
    for family_pin, param_prefix in families:
        for term_key, term_pin in term_pins:
            for axis in B_HARMONIC_AXES:
                name = f"{param_prefix}_{term_key}_{axis}"
                lines.append(
                    f"setp headheadkins.bharm-{family_pin}.{term_pin}.{axis} "
                    f"{params[name]:.9f}"
                )
    for term_key, term_pin in B_CROSS_TERM_PINS:
        for axis in B_HARMONIC_AXES:
            name = f"bc_{term_key}_{axis}"
            lines.append(
                f"setp headheadkins.bcross.{term_pin}.{axis} "
                f"{params[name]:.9f}"
            )
    lines.append("setp headheadkins.sim-bharm-enable 1")
    lines.append("```")
    return lines


def c_orbit_summary(observations: list[Observation], params: dict[str, float]) -> list[str]:
    b0 = [obs for obs in observations if abs(obs.b_deg) < 1e-6]
    lines = []
    if not b0:
        return lines
    estimates = [(obs, physical_estimate(obs, params)) for obs in b0]
    means = {}
    for c_deg in sorted({round(obs.c_deg) for obs in b0}):
        pts = np.array([estimate for obs, estimate in estimates if round(obs.c_deg) == c_deg])
        means[c_deg] = np.mean(pts, axis=0)
    base = means.get(0)
    for c_deg, mean in means.items():
        delta = mean - base if base is not None else np.zeros(3)
        lines.append(
            f"| `{c_deg:.0f}` | {mean[0]:.6f} | {mean[1]:.6f} | {mean[2]:.6f} | "
            f"{delta[0]:+.6f} | {delta[1]:+.6f} | {delta[2]:+.6f} |"
        )
    return lines


def residual_summary(observations: list[Observation], params: dict[str, float]) -> list[str]:
    lines = []
    residuals = residual_matrix(observations, params)
    for obs, res in zip(observations, residuals):
        lines.append(
            f"| `{obs.source}` | {obs.line} | `{obs.b_deg:+.0f}` | `{obs.c_deg:.0f}` | "
            f"{res[0]:+.6f} | {res[1]:+.6f} | {res[2]:+.6f} | {np.linalg.norm(res):.6f} |"
        )
    return lines


def b_angle_delta_rows(
    observations: list[Observation],
    params: dict[str, float] | None = None,
) -> tuple[np.ndarray, list[tuple[Observation, np.ndarray]]]:
    def point(obs: Observation) -> np.ndarray:
        if params is None:
            return obs.center
        return physical_estimate(obs, params)

    bases = []
    rows = []
    keys = sorted({(obs.group, round(obs.c_deg, 6)) for obs in observations})
    for group, c_deg in keys:
        group_rows = [
            obs
            for obs in observations
            if obs.group == group and round(obs.c_deg, 6) == c_deg
        ]
        b0 = [obs for obs in group_rows if abs(obs.b_deg) < 1e-6]
        if len(b0) < 2:
            continue
        base = (point(b0[0]) + point(b0[-1])) / 2.0
        bases.append(base)
        for obs in group_rows:
            if abs(obs.b_deg) < 1e-6:
                continue
            rows.append((obs, point(obs) - base))
    if not bases:
        return np.zeros(3), []
    return np.mean(np.array(bases), axis=0), rows


def b_angle_delta_summary(observations: list[Observation]) -> list[str]:
    _, rows = b_angle_delta_rows(observations)
    lines = []
    for obs, delta in rows:
        lines.append(
            f"| `{obs.label}` | {delta[0]:+.6f} | {delta[1]:+.6f} | "
            f"{delta[2]:+.6f} | {np.linalg.norm(delta):.6f} |"
        )
    return lines


def b_angle_delta_metric_text(observations: list[Observation]) -> str:
    _, rows = b_angle_delta_rows(observations)
    if not rows:
        return "`n/a`"
    norms = np.array([np.linalg.norm(delta) for _, delta in rows])
    return f"`{math.sqrt(np.mean(norms**2)):.6f} / {np.max(norms):.6f} mm`"


def b_angle_combined_delta_metric_text(
    data_sets: list[list[Observation]],
    params: dict[str, float] | None = None,
) -> str:
    norms = []
    for observations in data_sets:
        _, rows = b_angle_delta_rows(observations, params)
        norms.extend(float(np.linalg.norm(delta)) for _, delta in rows)
    if not norms:
        return "`n/a`"
    norm_array = np.array(norms)
    return f"`{math.sqrt(np.mean(norm_array**2)):.6f} / {np.max(norm_array):.6f} mm`"


def b_angle_closure_text(observations: list[Observation]) -> str:
    b0 = [obs for obs in observations if abs(obs.b_deg) < 1e-6]
    if len(b0) < 2:
        return "n/a"
    closure = b0[-1].center - b0[0].center
    return (
        f"`{closure[0]:+.6f} X`, `{closure[1]:+.6f} Y`, "
        f"`{closure[2]:+.6f} Z`, `{np.linalg.norm(closure):.6f} mm` 3D"
    )


def b_angle_basis_fit(observations: list[Observation], include_sin2: bool) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    _, rows = b_angle_delta_rows(observations)
    names = ["sin(B)", "1-cos(B)"]
    if include_sin2:
        names.append("sin(2B)")
    matrix = []
    deltas = []
    for obs, delta in rows:
        b_rad = math.radians(obs.b_deg)
        terms = [math.sin(b_rad), 1.0 - math.cos(b_rad)]
        if include_sin2:
            terms.append(math.sin(2.0 * b_rad))
        matrix.append(terms)
        deltas.append(delta)
    a = np.array(matrix)
    y = np.array(deltas)
    coeff = np.linalg.lstsq(a, y, rcond=None)[0]
    residuals = y - (a @ coeff)
    return names, coeff, residuals, np.array([obs.b_deg for obs, _ in rows])


def b_angle_basis_metric_text(observations: list[Observation], include_sin2: bool) -> str:
    _, _, residuals, _ = b_angle_basis_fit(observations, include_sin2)
    norms = np.linalg.norm(residuals, axis=1)
    return f"`{math.sqrt(np.mean(norms**2)):.6f} / {np.max(norms):.6f} mm`"


def b_angle_basis_coeff_lines(observations: list[Observation], include_sin2: bool) -> list[str]:
    names, coeff, _, _ = b_angle_basis_fit(observations, include_sin2)
    lines = ["| term | X coeff | Y coeff | Z coeff |", "| --- | ---: | ---: | ---: |"]
    for name, values in zip(names, coeff):
        lines.append(f"| `{name}` | {values[0]:+.9f} | {values[1]:+.9f} | {values[2]:+.9f} |")
    return lines


def write_report(
    path: Path,
    pre_cquad: list[Observation],
    validation_b0: list[Observation],
    post_cquad: list[Observation],
    baxis_holdout: list[Observation],
    c0_scaling: list[Observation],
    candidate_on_c0: list[Observation],
    candidate_on_c180: list[Observation],
    candidate_on_side: list[Observation],
    bcross_candidate_c0: list[Observation],
    bcross_candidate_c180: list[Observation],
    bcross_candidate_side: list[Observation],
    b0_fit: FitResult,
    post_fit: dict[str, FitResult],
    post_baxis_fit: dict[str, FitResult],
    all_fit: dict[str, FitResult],
    scaling_fit: dict[str, FitResult],
    post_baxis_scaling_fit: dict[str, FitResult],
    all_scaling_fit: dict[str, FitResult],
    candidate_validation_fit: list[tuple[str, FitResult]],
    bcross_refit_fit: list[tuple[str, str, FitResult]],
) -> None:
    base_params = as_params([], np.array([]))
    fixed_c_params = as_params([], np.array([]), FIXED_C_CENTER)
    pre_b0 = [obs for obs in pre_cquad if abs(obs.b_deg) < 1e-6]
    combined_post_baxis = post_cquad + baxis_holdout
    combined_all = pre_cquad + post_cquad + baxis_holdout
    combined_post_baxis_scaling = post_cquad + baxis_holdout + c0_scaling
    combined_all_scaling = pre_cquad + post_cquad + baxis_holdout + c0_scaling
    selected_post = post_fit["axis_vectors_linear_diag_no_cxy"]
    selected_post_baxis = post_baxis_fit["axis_vectors_linear_diag_no_cxy"]
    selected_all = all_fit["axis_vectors_linear_diag_no_cxy"]
    selected_post_baxis_scaling = post_baxis_scaling_fit["axis_vectors_linear_diag_no_cxy"]
    selected_all_scaling = all_scaling_fit["axis_vectors_linear_diag_no_cxy"]
    selected_harmonic_machine = post_baxis_scaling_fit["b_harmonic_machine_no_cxy"]
    selected_harmonic_cframe = post_baxis_scaling_fit["b_harmonic_cframe_no_cxy"]
    selected_harmonic_combo = post_baxis_scaling_fit["b_harmonic_machine_cframe_no_cxy"]
    candidate_validation = candidate_on_c0 + candidate_on_c180 + candidate_on_side
    candidate_validation_by_label = {
        label: fit
        for label, fit in candidate_validation_fit
    }
    selected_candidate_incremental_cframe = candidate_validation_by_label[
        "incremental C-frame on live candidate"
    ]
    selected_candidate_bcross = candidate_validation_by_label[
        "direct B/C cross on live candidate"
    ]
    selected_candidate_combo = candidate_validation_by_label[
        "replacement machine plus C-frame"
    ]
    selected_candidate_tilted_combo = candidate_validation_by_label[
        "C-tilted replacement machine plus C-frame"
    ]
    bcross_refit_by_label = {
        label: fit
        for label, _, fit in bcross_refit_fit
    }
    selected_bcross_refined = bcross_refit_by_label[
        "refined replacement machine plus B/C cross"
    ]
    old_candidate_validation = candidate_validation
    bcross_candidate_validation = (
        bcross_candidate_c0 + bcross_candidate_c180 + bcross_candidate_side
    )
    combined_live_validation = old_candidate_validation + bcross_candidate_validation
    live_candidate_params = as_params(
        [],
        np.array([]),
        {
            **FIXED_C_CENTER,
            **MACHINE_BHARMONIC_CANDIDATE,
        },
    )
    predicted_side_high_b = [
        obs
        for obs in post_cquad
        if abs(obs.b_deg) > 1e-6 and round(obs.c_deg) in (90, 270)
    ]
    harmonic_machine_rank, harmonic_machine_cond = jacobian_condition(selected_harmonic_machine.result)
    harmonic_cframe_rank, harmonic_cframe_cond = jacobian_condition(selected_harmonic_cframe.result)
    harmonic_combo_rank, harmonic_combo_cond = jacobian_condition(selected_harmonic_combo.result)
    harmonic_combo_cond_text = "n/a" if math.isnan(harmonic_combo_cond) else f"{harmonic_combo_cond:.2e}"
    harmonic_machine_cond_text = (
        "n/a" if math.isnan(harmonic_machine_cond) else f"{harmonic_machine_cond:.2e}"
    )
    harmonic_cframe_cond_text = "n/a" if math.isnan(harmonic_cframe_cond) else f"{harmonic_cframe_cond:.2e}"

    lines = [
        "# TCPC Expanded Geometry Fit Report",
        "",
        "Generated by `tcpc_expanded_geometry_fit.py`.",
        "",
        "## Data Sets",
        "",
        "| data set | rows | active kinematics | notes |",
        "| --- | ---: | --- | --- |",
        f"| pre-correction B90 C-quadrant | {len(pre_cquad)} | old C-center | CSV lines `2-43`, bad line `13` excluded |",
        f"| B0 C-center validation | {len(validation_b0)} | validated C-center | CSV lines `44-53` |",
        f"| corrected B90 C-quadrant | {len(post_cquad)} | validated C-center | CSV lines `54-93` |",
        f"| clean B90 C0/C180 holdout | {len(baxis_holdout)} | old C-center | B-axis diagnostic CSV lines `18-37` |",
        f"| C0 B-angle scaling | {len(c0_scaling)} | validated C-center | CSV lines `9,11,13,15,17,19,22,24` |",
        f"| candidate-on C0 B-angle scaling | {len(candidate_on_c0)} | validated C-center plus machine B-harmonic | CSV lines `29,31,33,35,37,39,41,43` |",
        f"| candidate-on C180 B-angle scaling | {len(candidate_on_c180)} | validated C-center plus machine B-harmonic | CSV lines `45,47,49,51,53,55,57,59` |",
        f"| candidate-on C90/C270 side check | {len(candidate_on_side)} | validated C-center plus machine B-harmonic | CSV lines `61,63,65,67,69,71,73,75` |",
        f"| B/C cross candidate C0 validation | {len(bcross_candidate_c0)} | validated C-center plus machine B-harmonic plus B/C cross | CSV lines `77,79,81,83,85,87,89,91` |",
        f"| B/C cross candidate C180 validation | {len(bcross_candidate_c180)} | validated C-center plus machine B-harmonic plus B/C cross | CSV lines `93,95,97,99,101,103,105,107` |",
        f"| B/C cross candidate C90/C270 side validation | {len(bcross_candidate_side)} | validated C-center plus machine B-harmonic plus B/C cross | CSV lines `109,111,113,115,117,119,121,123` |",
        "",
        "Each observation now subtracts the kinematic offset active during that run",
        "before applying a candidate model. This avoids treating pre-correction and",
        "post-correction rows as though they were measured with the same TCPC",
        "geometry.",
        "",
        "## C-Center Term",
        "",
        "The clean C-center term is still identified from the pre-correction B0",
        "C-quadrant rows only.",
        "",
        "| C deg | corrected mean X | corrected mean Y | corrected mean Z | dX from C0 | dY from C0 | dZ from C0 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *c_orbit_summary(pre_cquad, b0_fit.params),
        "",
        f"- old/base B0 C-orbit RMS/max: `{metric_text(pre_b0, base_params)}` mm",
        f"- fitted B0 C-orbit RMS/max: `{metric_text(pre_b0, b0_fit.params)}` mm",
        f"- fixed validated C-center RMS/max on validation rows: `{metric_text(validation_b0, fixed_c_params)}` mm",
        f"- `dcx = {b0_fit.params['dcx']:.9f} mm`",
        f"- `dcy = {b0_fit.params['dcy']:.9f} mm`",
        f"- equivalent validated `cal-c-to-b.x = {BASE_CAL_C_TO_B[0] + b0_fit.params['dcx']:.9f}`",
        f"- equivalent validated `cal-c-to-b.y = {BASE_CAL_C_TO_B[1] + b0_fit.params['dcy']:.9f}`",
        "",
        "The live validation confirms this correction. Keep this C-center fixed for",
        "high-B fitting; do not refit it against the B90 residuals.",
        "",
        "## Corrected B90 Run, C-Center Fixed",
        "",
        "Fit target: corrected B90 C-quadrant rows only. Evaluation is shown against",
        "the corrected run, the older clean B90 C0/C180 data, and the B0 validation",
        "rows.",
        "",
        *format_comparison_table(
            post_fit,
            [
                ("post B90", post_cquad),
                ("B-axis holdout", baxis_holdout),
                ("B0 validation", validation_b0),
            ],
        ),
        "",
        "## Corrected B90 Plus C0/C180 Holdout",
        "",
        f"Fit target: corrected B90 C-quadrant plus clean B90 C0/C180 rows",
        f"(`{len(combined_post_baxis)}` total points, two run groups).",
        "",
        *format_comparison_table(
            post_baxis_fit,
            [
                ("post B90", post_cquad),
                ("B-axis holdout", baxis_holdout),
                ("pre B90", pre_cquad),
                ("B0 validation", validation_b0),
            ],
        ),
        "",
        "## Pre Plus Corrected Plus Holdout",
        "",
        f"Fit target: all valid B90 C-quadrant and clean B90 rows",
        f"(`{len(combined_all)}` total points, three run groups).",
        "",
        *format_comparison_table(
            all_fit,
            [
                ("post B90", post_cquad),
                ("B-axis holdout", baxis_holdout),
                ("pre B90", pre_cquad),
                ("B0 validation", validation_b0),
            ],
        ),
        "",
        "## C0 B-Angle Scaling Diagnostic",
        "",
        "This short run used only opening and closing B0 references, then measured",
        "`B+30`, `B-30`, `B+60`, `B-60`, `B+90`, and `B-90` at `C0` with the",
        "validated C-center correction active.",
        "",
        f"- B0 opening/closing closure: {b_angle_closure_text(c0_scaling)}",
        f"- basis fit residual, `sin(B) + 1-cos(B)`: {b_angle_basis_metric_text(c0_scaling, include_sin2=False)}",
        f"- basis fit residual, `sin(B) + 1-cos(B) + sin(2B)`: {b_angle_basis_metric_text(c0_scaling, include_sin2=True)}",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(c0_scaling),
        "",
        "Simple B-basis coefficients from the C0 scaling data:",
        "",
        "### `sin(B) + 1-cos(B)`",
        "",
        *b_angle_basis_coeff_lines(c0_scaling, include_sin2=False),
        "",
        "### `sin(B) + 1-cos(B) + sin(2B)`",
        "",
        *b_angle_basis_coeff_lines(c0_scaling, include_sin2=True),
        "",
        "The `sin(2B)` term is diagnostic only. It shows the C0 error shape is not",
        "well represented by only a static B pivot translation plus a cosine-radius",
        "term.",
        "",
        "## C0 Scaling Fit, C-Center Fixed",
        "",
        f"Fit target: C0 B-angle scaling data only (`{len(c0_scaling)}` points).",
        "",
        *format_comparison_table(
            scaling_fit,
            [
                ("C0 scaling", c0_scaling),
                ("post B90", post_cquad),
                ("B-axis holdout", baxis_holdout),
                ("B0 validation", validation_b0),
            ],
        ),
        "",
        "## Corrected B90 Plus Holdout Plus C0 Scaling",
        "",
        f"Fit target: corrected B90, clean B90 C0/C180 holdout, and C0 B-angle",
        f"scaling (`{len(combined_post_baxis_scaling)}` total points, three run groups).",
        "",
        *format_comparison_table(
            post_baxis_scaling_fit,
            [
                ("C0 scaling", c0_scaling),
                ("post B90", post_cquad),
                ("B-axis holdout", baxis_holdout),
                ("pre B90", pre_cquad),
                ("B0 validation", validation_b0),
            ],
        ),
        "",
        "## All Data Plus C0 Scaling",
        "",
        f"Fit target: all curated B90 rows plus C0 B-angle scaling",
        f"(`{len(combined_all_scaling)}` total points, four run groups).",
        "",
        *format_comparison_table(
            all_scaling_fit,
            [
                ("C0 scaling", c0_scaling),
                ("post B90", post_cquad),
                ("B-axis holdout", baxis_holdout),
                ("pre B90", pre_cquad),
                ("B0 validation", validation_b0),
            ],
        ),
        "",
        "## B-Harmonic Diagnostic Result",
        "",
        "The bounded B-harmonic families add empirical correction vectors using",
        "`sin(B)`, `1-cos(B)`, and `sin(2B)`. These terms are offline diagnostic",
        "only until the same math is implemented and verified in simulation.",
        "",
        "On the corrected B90 plus holdout plus C0 scaling target:",
        "",
        f"- machine-fixed B harmonic: C0 scaling `{metric_text(c0_scaling, selected_harmonic_machine.params)}`, "
        f"corrected B90 `{metric_text(post_cquad, selected_harmonic_machine.params)}`, "
        f"clean holdout `{metric_text(baxis_holdout, selected_harmonic_machine.params)}`, "
        f"rank `{harmonic_machine_rank}`, condition `{harmonic_machine_cond_text}`",
        f"- C-frame B harmonic: C0 scaling `{metric_text(c0_scaling, selected_harmonic_cframe.params)}`, "
        f"corrected B90 `{metric_text(post_cquad, selected_harmonic_cframe.params)}`, "
        f"clean holdout `{metric_text(baxis_holdout, selected_harmonic_cframe.params)}`, "
        f"rank `{harmonic_cframe_rank}`, condition `{harmonic_cframe_cond_text}`",
        f"- combined machine/C-frame B harmonic: C0 scaling `{metric_text(c0_scaling, selected_harmonic_combo.params)}`, "
        f"corrected B90 `{metric_text(post_cquad, selected_harmonic_combo.params)}`, "
        f"clean holdout `{metric_text(baxis_holdout, selected_harmonic_combo.params)}`, "
        f"rank `{harmonic_combo_rank}`, condition `{harmonic_combo_cond_text}`",
        "",
        "The machine-fixed B harmonic is the cleanest bounded diagnostic so far for",
        "C0 scaling plus the clean B90 C0/C180 holdout. The C-frame harmonic is",
        "slightly better on the corrected B90 quadrant but weaker on the holdout.",
        "The combined machine/C-frame model is not identifiable from the current",
        "data because its condition number is extremely high.",
        "",
        "## Live Candidate-On Validation",
        "",
        "The machine-fixed B-harmonic candidate above was loaded manually and",
        "enabled only for live validation passes at C0, C180, C90, and C270.",
        "These rows are modeled with that B-harmonic correction as the active",
        "kinematic state.",
        "",
        "| validation set | B0 closure | non-B0 RMS/max |",
        "| --- | ---: | ---: |",
        f"| candidate-on C0 | {b_angle_closure_text(candidate_on_c0)} | {b_angle_delta_metric_text(candidate_on_c0)} |",
        f"| candidate-on C180 | {b_angle_closure_text(candidate_on_c180)} | {b_angle_delta_metric_text(candidate_on_c180)} |",
        f"| candidate-on C90/C270 side check | n/a | {b_angle_combined_delta_metric_text([candidate_on_side])} |",
        f"| candidate-on C0+C180 combined | n/a | {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180])} |",
        f"| candidate-on all validation | n/a | {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side])} |",
        "",
        "Candidate-on C0 deltas:",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(candidate_on_c0),
        "",
        "Candidate-on C180 deltas:",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(candidate_on_c180),
        "",
        "Candidate-on side-quadrant deltas:",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(candidate_on_side),
        "",
        "The same candidate evaluated against the older corrected B90 C-quadrant",
        "data predicts that the side quadrants are still the highest-risk area.",
        "These are model predictions from existing C90/C270 data, not new live",
        "candidate-on measurements:",
        "",
        f"- predicted corrected B90 all-quadrant RMS/max: `{metric_text(post_cquad, live_candidate_params)}`",
        f"- predicted side-quadrant high-B RMS/max: `{metric_text(predicted_side_high_b, live_candidate_params)}`",
        "",
        "| source | line | B | C | residual X | residual Y | residual Z | norm |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *residual_summary(predicted_side_high_b, live_candidate_params),
        "",
        "## Candidate-On Refit With Side Rows",
        "",
        "This refit uses only the rows measured with the live machine-fixed",
        "B-harmonic candidate active. The direct columns use the same non-B0",
        "metric as the live validation table, but recomputed after applying each",
        "offline model to the measured rows.",
        "",
        *format_candidate_validation_table(
            candidate_validation_fit,
            [
                ("C0", candidate_on_c0),
                ("C180", candidate_on_c180),
                ("C90/C270", candidate_on_side),
            ],
        ),
        "",
        "The direct B/C cross fit is the first side-aware candidate that improves",
        "C0, C180, and C90/C270 together without an ill-conditioned Jacobian. It",
        "is fitted as an incremental layer on top of the already tested",
        "machine-fixed B-harmonic candidate.",
        "",
        "### Candidate-On Direct B/C Cross Parameters",
        "",
        *format_params(
            selected_candidate_bcross.params,
            B_CROSS_MACHINE_PARAMS,
        ),
        "",
        "Simulation-only HAL load block used for this diagnostic candidate:",
        "",
        *b_harmonic_sim_hal_block(selected_candidate_bcross.params),
        "",
        "## Live B/C Cross Candidate Validation",
        "",
        "The B/C cross candidate was then loaded on top of the machine-fixed",
        "B-harmonic candidate and enabled only for the live C0/C180/C90/C270",
        "validation pass. The candidate was disabled again after the run.",
        "",
        "| validation set | B0 closure | non-B0 RMS/max |",
        "| --- | ---: | ---: |",
        f"| B/C cross C0 | {b_angle_closure_text(bcross_candidate_c0)} | {b_angle_delta_metric_text(bcross_candidate_c0)} |",
        f"| B/C cross C180 | {b_angle_closure_text(bcross_candidate_c180)} | {b_angle_delta_metric_text(bcross_candidate_c180)} |",
        f"| B/C cross C90/C270 side | n/a | {b_angle_combined_delta_metric_text([bcross_candidate_side])} |",
        f"| B/C cross C0+C180 combined | n/a | {b_angle_combined_delta_metric_text([bcross_candidate_c0, bcross_candidate_c180])} |",
        f"| B/C cross all validation | n/a | {b_angle_combined_delta_metric_text([bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side])} |",
        "",
        "Live candidate comparison:",
        "",
        "| set | machine B-harmonic only | machine B-harmonic plus B/C cross |",
        "| --- | ---: | ---: |",
        f"| C0 | {b_angle_delta_metric_text(candidate_on_c0)} | {b_angle_delta_metric_text(bcross_candidate_c0)} |",
        f"| C180 | {b_angle_delta_metric_text(candidate_on_c180)} | {b_angle_delta_metric_text(bcross_candidate_c180)} |",
        f"| C90/C270 side | {b_angle_combined_delta_metric_text([candidate_on_side])} | {b_angle_combined_delta_metric_text([bcross_candidate_side])} |",
        f"| all validation | {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side])} | {b_angle_combined_delta_metric_text([bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side])} |",
        "",
        "B/C cross C0 deltas:",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(bcross_candidate_c0),
        "",
        "B/C cross C180 deltas:",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(bcross_candidate_c180),
        "",
        "B/C cross side-quadrant deltas:",
        "",
        "| pose | dX from B0 mean | dY from B0 mean | dZ from B0 mean | 3D drift |",
        "| --- | ---: | ---: | ---: | ---: |",
        *b_angle_delta_summary(bcross_candidate_side),
        "",
        "## Post B/C Cross Refit",
        "",
        "The live B/C cross validation rows are an independent check on the",
        "previous B/C cross fit. This refit keeps the validated C-center fixed",
        "and compares candidate families against both live states: the older",
        "B-harmonic-only rows and the new rows measured with B/C cross active.",
        "",
        *format_direct_refit_table(
            bcross_refit_fit,
            [
                ("old B-harmonic-only live rows", old_candidate_validation),
                ("new B/C cross live rows", bcross_candidate_validation),
                ("combined live rows", combined_live_validation),
                ("corrected B90 holdout", post_cquad),
                ("clean B-axis holdout", baxis_holdout),
                ("original C0 scaling", c0_scaling),
            ],
        ),
        "",
        "The best next diagnostic is the refined replacement machine plus B/C",
        "cross fit. It is not a new kinematics family; it only retunes the",
        "already simulation-gated machine harmonic and B/C cross pins using the",
        "additional live validation rows.",
        "",
        "### Refined Replacement Machine Plus B/C Cross Parameters",
        "",
        *format_params(
            selected_bcross_refined.params,
            B_HARMONIC_MACHINE_PARAMS + B_CROSS_MACHINE_PARAMS,
        ),
        "",
        "Simulation-only HAL load block for the refined diagnostic candidate:",
        "",
        *b_harmonic_sim_hal_block(selected_bcross_refined.params),
        "",
        "Dedicated HAL file for the refined candidate:",
        "",
        "- `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`",
        "",
        "### Candidate-On Incremental C-Frame Parameters",
        "",
        *format_params(
            selected_candidate_incremental_cframe.params,
            B_HARMONIC_CFRAME_PARAMS,
        ),
        "",
        "### Candidate-On Replacement Machine Plus C-Frame Parameters",
        "",
        *format_params(
            selected_candidate_combo.params,
            B_HARMONIC_MACHINE_PARAMS + B_HARMONIC_CFRAME_PARAMS,
        ),
        "",
        "### Candidate-On C-Tilted Replacement Machine Plus C-Frame Parameters",
        "",
        *format_params(
            selected_candidate_tilted_combo.params,
            MODEL_FAMILIES["c_tilt_b_harmonic_machine_cframe_no_cxy"],
        ),
        "",
        "## Selected Diagnostic Parameters",
        "",
        "All parameter values below keep C-center fixed. They are diagnostic, not",
        "live HAL candidates. Some fits hit bounds or remain ill-conditioned; the",
        "B-harmonic terms also require kinematics implementation and simulation",
        "verification before any live test.",
        "",
        "### Post-Only Axis Vector Plus Linear Diagonal",
        "",
        *format_params(selected_post.params, MODEL_FAMILIES["axis_vectors_linear_diag_no_cxy"]),
        "",
        "### Post Plus Holdout Axis Vector Plus Linear Diagonal",
        "",
        *format_params(selected_post_baxis.params, MODEL_FAMILIES["axis_vectors_linear_diag_no_cxy"]),
        "",
        "### All-Data Axis Vector Plus Linear Diagonal",
        "",
        *format_params(selected_all.params, MODEL_FAMILIES["axis_vectors_linear_diag_no_cxy"]),
        "",
        "### Post Plus Holdout Plus C0 Scaling Axis Vector Plus Linear Diagonal",
        "",
        *format_params(
            selected_post_baxis_scaling.params,
            MODEL_FAMILIES["axis_vectors_linear_diag_no_cxy"],
        ),
        "",
        "### All-Data Plus C0 Scaling Axis Vector Plus Linear Diagonal",
        "",
        *format_params(selected_all_scaling.params, MODEL_FAMILIES["axis_vectors_linear_diag_no_cxy"]),
        "",
        "### Post Plus Holdout Plus C0 Scaling Machine-Fixed B Harmonic",
        "",
        *format_params(selected_harmonic_machine.params, B_HARMONIC_MACHINE_PARAMS),
        "",
        "Simulation-only HAL load block for this diagnostic candidate:",
        "",
        *b_harmonic_sim_hal_block(selected_harmonic_machine.params),
        "",
        "### Post Plus Holdout Plus C0 Scaling C-Frame B Harmonic",
        "",
        *format_params(selected_harmonic_cframe.params, B_HARMONIC_CFRAME_PARAMS),
        "",
        "## Corrected-Run Residuals With Post Plus Holdout Fit",
        "",
        "| source | line | B | C | residual X | residual Y | residual Z | norm |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *residual_summary(post_cquad, selected_post_baxis.params),
        "",
        "## Current Decision",
        "",
        "- Keep the live C-center correction:",
        "  - `headheadkins.cal-c-to-b.x = +0.035886006`",
        "  - `headheadkins.cal-c-to-b.y = +0.009526306`",
        "- The manually tested machine-fixed B-harmonic candidate materially",
        "  improves C0 and C180, but it should not be made persistent yet.",
        "- Candidate-on C0+C180 combined non-B0 RMS/max is",
        f"  {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180])}.",
        "- Candidate-on all-validation non-B0 RMS/max is",
        f"  {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side])}.",
        "- B/C cross candidate all-validation non-B0 RMS/max is",
        f"  {b_angle_combined_delta_metric_text([bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side])}.",
        "- B/C cross candidate side-quadrant non-B0 RMS/max is",
        f"  {b_angle_combined_delta_metric_text([bcross_candidate_side])}.",
        "- The refined replacement machine plus B/C cross fit reduces combined",
        "  live-state direct RMS/max to",
        f"  {b_angle_combined_delta_metric_text([combined_live_validation], selected_bcross_refined.params)}.",
        "- With the B-harmonic-only candidate, C180 still had a `0.228885 mm`",
        "  maximum at `B+60 C180`.",
        f"- With the B/C cross candidate active, the current maximum is `{max(np.linalg.norm(delta) for _, delta in b_angle_delta_rows(bcross_candidate_validation)[1]):.6f} mm`.",
        "- Under the B-harmonic-only candidate, live side-quadrant testing",
        "  confirmed the highest remaining risk at `C90/C270`, especially",
        "  `B+90 C270`.",
        "- The tested machine-fixed correction is not a general solution by itself;",
        "  the side-quadrant validation is much worse than C0/C180.",
        "- The B/C cross layer is a validated improvement over the machine-fixed",
        "  B-harmonic-only candidate, but it should still remain simulation-gated",
        "  until the new run is used in the next correction-selection pass.",
        "- On the prior B-harmonic-only rows, the direct B/C cross candidate",
        "  reduces all-validation direct RMS/max to",
        f"  {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side], selected_candidate_bcross.params)}.",
        "- The same direct B/C cross candidate evaluates at",
        f"  `{metric_text(post_cquad, selected_candidate_bcross.params)}` on the older corrected B90 run",
        f"  and `{metric_text(baxis_holdout, selected_candidate_bcross.params)}` on the clean B-axis holdout.",
        "- Axis-vector terms help only modestly and still point at an incomplete",
        "  model.",
        "- Linear/affine terms improve the numerical fit but repeatedly hit bounds,",
        "  so they are diagnostic evidence, not a compensation solution.",
        "",
        "## Next TCPC Math Work",
        "",
        "1. Keep the run-state-aware fitter as the source of truth for mixed data.",
        "2. Use the refined replacement machine plus B/C cross candidate as",
        "   the next simulation-gated live diagnostic.",
        "3. Keep the B-harmonic and B/C cross terms simulation-gated with zero",
        "   defaults.",
        "4. Do not promote any B-harmonic or B/C cross correction to persistent",
        "   startup HAL until the validation rows have been reviewed and a",
        "   persistent-candidate decision is made.",
        "",
        "## Next Live Data",
        "",
        "The next live probe pass should use the refined candidate HAL file above",
        "with `headheadkins.sim-bharm-enable` still normally `FALSE`.",
        "",
        "Use `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` with",
        "`#711 = 4.0` for the next validation so the refined candidate is checked",
        "against C0, C180, and the C90/C270 side poses.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def load_data() -> tuple[
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
    list[Observation],
]:
    cquad_path = CONFIG_DIR / "tcpc-b90-c-quadrant-diagnostic-2pass-results.csv"
    baxis_path = CONFIG_DIR / "tcpc-b90-b-axis-diagnostic-2pass-results.csv"
    scaling_path = CONFIG_DIR / "tcpc-b-angle-scaling-diagnostic-2pass-results.csv"
    pre_cquad = read_results(
        cquad_path,
        source="pre_b90_c_quadrant",
        group="2026-05-04-pre-c-center",
        active_name="old_c_center",
        active_cal_c_to_b=BASE_CAL_C_TO_B,
        min_line=2,
        max_line=43,
        exclude_lines=[13],
    )
    validation_b0 = read_results(
        cquad_path,
        source="b0_validation",
        group="2026-05-04-c-center-validation",
        active_name="validated_c_center",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        min_line=44,
        max_line=53,
    )
    post_cquad = read_results(
        cquad_path,
        source="corrected_b90_c_quadrant",
        group="2026-05-04-post-c-center",
        active_name="validated_c_center",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        min_line=54,
        max_line=93,
    )
    baxis_holdout = read_results(
        baxis_path,
        source="clean_b90_b_axis",
        group="2026-05-03-clean-b90",
        active_name="old_c_center",
        active_cal_c_to_b=BASE_CAL_C_TO_B,
        min_line=18,
        max_line=37,
    )
    c0_scaling = read_results(
        scaling_path,
        source="c0_b_angle_scaling",
        group="2026-05-04-c0-b-angle-scaling",
        active_name="validated_c_center",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        include_lines=[9, 11, 13, 15, 17, 19, 22, 24],
    )
    candidate_on_c0 = read_results(
        scaling_path,
        source="candidate_on_c0_scaling",
        group="2026-05-04-candidate-on-c0",
        active_name="validated_c_center_plus_machine_bharmonic",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        active_bharmonic_params=MACHINE_BHARMONIC_CANDIDATE,
        include_lines=[29, 31, 33, 35, 37, 39, 41, 43],
    )
    candidate_on_c180 = read_results(
        scaling_path,
        source="candidate_on_c180_scaling",
        group="2026-05-04-candidate-on-c180",
        active_name="validated_c_center_plus_machine_bharmonic",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        active_bharmonic_params=MACHINE_BHARMONIC_CANDIDATE,
        include_lines=[45, 47, 49, 51, 53, 55, 57, 59],
    )
    candidate_on_side = read_results(
        scaling_path,
        source="candidate_on_side_scaling",
        group="2026-05-04-candidate-on-side",
        active_name="validated_c_center_plus_machine_bharmonic",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        active_bharmonic_params=MACHINE_BHARMONIC_CANDIDATE,
        include_lines=[61, 63, 65, 67, 69, 71, 73, 75],
    )
    bcross_candidate_c0 = read_results(
        scaling_path,
        source="bcross_candidate_c0_scaling",
        group="2026-05-04-bcross-candidate-c0",
        active_name="validated_c_center_plus_machine_bharmonic_bcross",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        active_bharmonic_params=BCROSS_CANDIDATE,
        include_lines=[77, 79, 81, 83, 85, 87, 89, 91],
    )
    bcross_candidate_c180 = read_results(
        scaling_path,
        source="bcross_candidate_c180_scaling",
        group="2026-05-04-bcross-candidate-c180",
        active_name="validated_c_center_plus_machine_bharmonic_bcross",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        active_bharmonic_params=BCROSS_CANDIDATE,
        include_lines=[93, 95, 97, 99, 101, 103, 105, 107],
    )
    bcross_candidate_side = read_results(
        scaling_path,
        source="bcross_candidate_side_scaling",
        group="2026-05-04-bcross-candidate-side",
        active_name="validated_c_center_plus_machine_bharmonic_bcross",
        active_cal_c_to_b=VALIDATED_CAL_C_TO_B,
        active_bharmonic_params=BCROSS_CANDIDATE,
        include_lines=[109, 111, 113, 115, 117, 119, 121, 123],
    )
    return (
        pre_cquad,
        validation_b0,
        post_cquad,
        baxis_holdout,
        c0_scaling,
        candidate_on_c0,
        candidate_on_c180,
        candidate_on_side,
        bcross_candidate_c0,
        bcross_candidate_c180,
        bcross_candidate_side,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        type=Path,
        default=CONFIG_DIR / "TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md",
        help="Markdown report path",
    )
    args = parser.parse_args()

    (
        pre_cquad,
        validation_b0,
        post_cquad,
        baxis_holdout,
        c0_scaling,
        candidate_on_c0,
        candidate_on_c180,
        candidate_on_side,
        bcross_candidate_c0,
        bcross_candidate_c180,
        bcross_candidate_side,
    ) = load_data()
    pre_b0 = [obs for obs in pre_cquad if abs(obs.b_deg) < 1e-6]
    b0_fit = fit_model("c_center_xy", pre_b0)
    post_fit = fit_suite(HIGH_B_MODELS, post_cquad, FIXED_C_CENTER)
    post_baxis_fit = fit_suite(HIGH_B_MODELS, post_cquad + baxis_holdout, FIXED_C_CENTER)
    all_fit = fit_suite(HIGH_B_MODELS, pre_cquad + post_cquad + baxis_holdout, FIXED_C_CENTER)
    scaling_fit = fit_suite(HIGH_B_MODELS, c0_scaling, FIXED_C_CENTER)
    post_baxis_scaling_fit = fit_suite(
        HIGH_B_MODELS,
        post_cquad + baxis_holdout + c0_scaling,
        FIXED_C_CENTER,
    )
    all_scaling_fit = fit_suite(
        HIGH_B_MODELS,
        pre_cquad + post_cquad + baxis_holdout + c0_scaling,
        FIXED_C_CENTER,
    )
    live_candidate_fixed_params = {
        **FIXED_C_CENTER,
        **MACHINE_BHARMONIC_CANDIDATE,
    }
    live_bcross_fixed_params = {
        **FIXED_C_CENTER,
        **BCROSS_CANDIDATE,
    }
    candidate_validation = candidate_on_c0 + candidate_on_c180 + candidate_on_side
    bcross_validation = bcross_candidate_c0 + bcross_candidate_c180 + bcross_candidate_side
    combined_live_validation_sets = [
        candidate_on_c0,
        candidate_on_c180,
        candidate_on_side,
        bcross_candidate_c0,
        bcross_candidate_c180,
        bcross_candidate_side,
    ]
    candidate_validation_fit = [
        (
            "current live candidate",
            FitResult(
                model="current_live_candidate",
                params=as_params([], np.array([]), live_candidate_fixed_params),
                result=None,
            ),
        ),
        (
            "direct B/C cross on live candidate",
            fit_direct_model(
                "b_cross_machine_no_cxy",
                [candidate_on_c0, candidate_on_c180, candidate_on_side],
                live_candidate_fixed_params,
            ),
        ),
        (
            "incremental C-frame on live candidate",
            fit_model(
                "b_harmonic_cframe_no_cxy",
                candidate_validation,
                live_candidate_fixed_params,
            ),
        ),
        (
            "C-tilted C-frame on live candidate",
            fit_model(
                "c_tilt_b_harmonic_cframe_no_cxy",
                candidate_validation,
                live_candidate_fixed_params,
            ),
        ),
        (
            "replacement machine only",
            fit_model("b_harmonic_machine_no_cxy", candidate_validation, FIXED_C_CENTER),
        ),
        (
            "replacement C-frame only",
            fit_model("b_harmonic_cframe_no_cxy", candidate_validation, FIXED_C_CENTER),
        ),
        (
            "replacement machine plus C-frame",
            fit_model(
                "b_harmonic_machine_cframe_no_cxy",
                candidate_validation,
                FIXED_C_CENTER,
            ),
        ),
        (
            "C-tilted replacement machine plus C-frame",
            fit_model(
                "c_tilt_b_harmonic_machine_cframe_no_cxy",
                candidate_validation,
                FIXED_C_CENTER,
            ),
        ),
        (
            "axis vector plus linear diagonal",
            fit_model("axis_vectors_linear_diag_no_cxy", candidate_validation, FIXED_C_CENTER),
        ),
    ]
    bcross_refit_fit = [
        (
            "current B/C cross candidate",
            "live-tested candidate",
            FitResult(
                model="current_bcross_candidate",
                params=as_params([], np.array([]), live_bcross_fixed_params),
                result=None,
            ),
        ),
        (
            "refit B/C cross only",
            "old+new live rows",
            fit_direct_model(
                "b_cross_machine_no_cxy",
                combined_live_validation_sets,
                live_candidate_fixed_params,
            ),
        ),
        (
            "refined replacement machine plus B/C cross",
            "old+new live rows",
            fit_direct_model(
                "b_harmonic_machine_bcross_no_cxy",
                combined_live_validation_sets,
                FIXED_C_CENTER,
            ),
        ),
        (
            "replacement machine plus B/C cross from new rows only",
            "new B/C cross rows",
            fit_direct_model(
                "b_harmonic_machine_bcross_no_cxy",
                [bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side],
                FIXED_C_CENTER,
            ),
        ),
        (
            "incremental C-frame on current B/C cross",
            "new B/C cross rows",
            fit_direct_model(
                "b_harmonic_cframe_no_cxy",
                [bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side],
                live_bcross_fixed_params,
            ),
        ),
    ]

    write_report(
        args.report,
        pre_cquad,
        validation_b0,
        post_cquad,
        baxis_holdout,
        c0_scaling,
        candidate_on_c0,
        candidate_on_c180,
        candidate_on_side,
        bcross_candidate_c0,
        bcross_candidate_c180,
        bcross_candidate_side,
        b0_fit,
        post_fit,
        post_baxis_fit,
        all_fit,
        scaling_fit,
        post_baxis_scaling_fit,
        all_scaling_fit,
        candidate_validation_fit,
        bcross_refit_fit,
    )

    fixed_c_params = as_params([], np.array([]), FIXED_C_CENTER)
    print(f"pre-correction B90 C-quadrant points: {len(pre_cquad)}")
    print(f"B0 C-center validation points: {len(validation_b0)}")
    print(f"corrected B90 C-quadrant points: {len(post_cquad)}")
    print(f"clean B90 C0/C180 holdout points: {len(baxis_holdout)}")
    print(f"C0 B-angle scaling points: {len(c0_scaling)}")
    print(f"candidate-on C0 scaling points: {len(candidate_on_c0)}")
    print(f"candidate-on C180 scaling points: {len(candidate_on_c180)}")
    print(f"candidate-on side scaling points: {len(candidate_on_side)}")
    print(f"B/C cross candidate C0 scaling points: {len(bcross_candidate_c0)}")
    print(f"B/C cross candidate C180 scaling points: {len(bcross_candidate_c180)}")
    print(f"B/C cross candidate side scaling points: {len(bcross_candidate_side)}")
    print(f"report: {args.report}")
    print()
    print(
        "b0_only_c_center, "
        f"dcx={b0_fit.params['dcx']:.9f}, dcy={b0_fit.params['dcy']:.9f}, "
        f"cal_x={BASE_CAL_C_TO_B[0] + b0_fit.params['dcx']:.9f}, "
        f"cal_y={BASE_CAL_C_TO_B[1] + b0_fit.params['dcy']:.9f}, "
        f"rms/max={metric_text(pre_b0, b0_fit.params)}"
    )
    print()
    print("post-corrected run, C-center fixed, model, post_rms/max, baxis_rms/max")
    for name, fit in post_fit.items():
        print(
            f"{name}, {metric_text(post_cquad, fit.params)}, "
            f"{metric_text(baxis_holdout, fit.params)}"
        )
    print()
    print("post+B-axis train, C-center fixed, model, post_rms/max, baxis_rms/max")
    for name, fit in post_baxis_fit.items():
        print(
            f"{name}, {metric_text(post_cquad, fit.params)}, "
            f"{metric_text(baxis_holdout, fit.params)}"
        )
    print()
    print("C0 scaling train, C-center fixed, model, scaling_rms/max, post_rms/max, baxis_rms/max")
    for name, fit in scaling_fit.items():
        print(
            f"{name}, {metric_text(c0_scaling, fit.params)}, "
            f"{metric_text(post_cquad, fit.params)}, "
            f"{metric_text(baxis_holdout, fit.params)}"
        )
    print()
    print("post+B-axis+C0 scaling train, C-center fixed, model, scaling_rms/max, post_rms/max, baxis_rms/max")
    for name, fit in post_baxis_scaling_fit.items():
        print(
            f"{name}, {metric_text(c0_scaling, fit.params)}, "
            f"{metric_text(post_cquad, fit.params)}, "
            f"{metric_text(baxis_holdout, fit.params)}"
        )
    print()
    print("candidate-on live validation, set, non-B0 RMS/max")
    print(f"C0, {b_angle_delta_metric_text(candidate_on_c0)}")
    print(f"C180, {b_angle_delta_metric_text(candidate_on_c180)}")
    print(f"C90/C270, {b_angle_combined_delta_metric_text([candidate_on_side])}")
    print(f"C0+C180, {b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180])}")
    print(
        "all, "
        f"{b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side])}"
    )
    print("B/C cross live validation, set, non-B0 RMS/max")
    print(f"C0, {b_angle_delta_metric_text(bcross_candidate_c0)}")
    print(f"C180, {b_angle_delta_metric_text(bcross_candidate_c180)}")
    print(f"C90/C270, {b_angle_combined_delta_metric_text([bcross_candidate_side])}")
    print(
        "all, "
        f"{b_angle_combined_delta_metric_text([bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side])}"
    )
    print()
    print("candidate-on refit, model, all direct non-B0 RMS/max, residual RMS/max")
    for label, fit in candidate_validation_fit:
        print(
            f"{label}, "
            f"{b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side], fit.params)}, "
            f"{metric_text(candidate_validation, fit.params)}"
        )
    print()
    print("B/C cross refit, model, train set, old direct RMS/max, new direct RMS/max, combined direct RMS/max")
    for label, train_set, fit in bcross_refit_fit:
        print(
            f"{label}, {train_set}, "
            f"{b_angle_combined_delta_metric_text([candidate_on_c0, candidate_on_c180, candidate_on_side], fit.params)}, "
            f"{b_angle_combined_delta_metric_text([bcross_candidate_c0, bcross_candidate_c180, bcross_candidate_side], fit.params)}, "
            f"{b_angle_combined_delta_metric_text(combined_live_validation_sets, fit.params)}"
        )
    print()
    print(f"fixed C-center validation rms/max: {metric_text(validation_b0, fixed_c_params)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
