#!/usr/bin/env python3
"""Offline TCPC geometry fit for the XYZBC head-head calibration data.

This intentionally does not write HAL values.  It compares model families and
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

# Live validated candidate during the 2026-05-04 B90 C-quadrant run.
CURRENT_NOMINAL_C_TO_B = np.array([0.010934, 0.0, -270.000000])
CURRENT_CAL_C_TO_B = np.array([-0.065000, 0.014000, 0.0])
CURRENT_NOMINAL_B_TO_TOOL = np.array([-0.668710, -26.721365, -308.980001])
CURRENT_CAL_B_TO_TOOL = np.array([0.0, 0.0, 0.815000])
CURRENT_C_TO_B = CURRENT_NOMINAL_C_TO_B + CURRENT_CAL_C_TO_B
CURRENT_B_TO_TOOL = CURRENT_NOMINAL_B_TO_TOOL + CURRENT_CAL_B_TO_TOOL
CURRENT_B_ZERO_DEG = 0.0
CURRENT_C_ZERO_DEG = -0.024500


@dataclass(frozen=True)
class Observation:
    source: str
    group: str
    line: int
    b_deg: float
    c_deg: float
    center: np.ndarray

    @property
    def label(self) -> str:
        return f"{self.source}:L{self.line}:B{self.b_deg:+.0f}C{self.c_deg:.0f}"


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


MODEL_FAMILIES = {
    "current": [],
    "c_center_xy": ["dcx", "dcy"],
    "current_pins": ["dcx", "dcy", "dcz", "dbx", "dby", "dbz", "b_zero", "c_zero"],
    "axis_vectors": [
        "dcx",
        "dcy",
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
    "axis_vectors_linear_diag": [
        "dcx",
        "dcy",
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
    "axis_vectors_linear_full": [
        "dcx",
        "dcy",
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


def read_results(
    path: Path,
    source: str,
    group: str,
    min_line: int | None = None,
    max_line: int | None = None,
    exclude_lines: Iterable[int] = (),
) -> list[Observation]:
    observations: list[Observation] = []
    excluded = set(exclude_lines)
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for line, row in enumerate(reader, start=2):
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


def as_params(names: list[str], values: np.ndarray) -> dict[str, float]:
    params = {name: 0.0 for name in PARAM_BOUNDS}
    for name, value in zip(names, values):
        params[name] = float(value)
    return params


def current_offset(b_deg: float, c_deg: float) -> np.ndarray:
    b_eff = b_deg + CURRENT_B_ZERO_DEG
    c_eff = c_deg + CURRENT_C_ZERO_DEG
    return rot_z(c_eff) @ (CURRENT_C_TO_B + (rot_y(b_eff) @ CURRENT_B_TO_TOOL))


def expanded_offset(b_deg: float, c_deg: float, params: dict[str, float]) -> np.ndarray:
    c_to_b = CURRENT_C_TO_B + np.array([params["dcx"], params["dcy"], params["dcz"]])
    b_to_tool = CURRENT_B_TO_TOOL + np.array([params["dbx"], params["dby"], params["dbz"]])
    c_frame = rot_y(params["c_tilt_y"]) @ rot_x(params["c_tilt_x"])
    b_axis = np.array(
        [
            math.tan(math.radians(params["b_axis_x"])),
            1.0,
            math.tan(math.radians(params["b_axis_z"])),
        ]
    )
    b_eff = b_deg + CURRENT_B_ZERO_DEG + params["b_zero"]
    c_eff = c_deg + CURRENT_C_ZERO_DEG + params["c_zero"]
    local = c_to_b + (rot_axis(b_axis, b_eff) @ b_to_tool)
    return c_frame @ (rot_z(c_eff) @ local)


def linear_matrix(params: dict[str, float]) -> np.ndarray:
    return np.eye(3) + np.array(
        [
            [params["lin_xx"], params["lin_xy"], params["lin_xz"]],
            [params["lin_yx"], params["lin_yy"], params["lin_yz"]],
            [params["lin_zx"], params["lin_zy"], params["lin_zz"]],
        ]
    )


def physical_estimate(obs: Observation, params: dict[str, float]) -> np.ndarray:
    linear = obs.center - current_offset(obs.b_deg, obs.c_deg)
    return (linear_matrix(params) @ linear) + expanded_offset(obs.b_deg, obs.c_deg, params)


def residual_matrix(observations: list[Observation], params: dict[str, float]) -> np.ndarray:
    estimates = np.array([physical_estimate(obs, params) for obs in observations])
    residuals = np.zeros_like(estimates)
    groups = sorted({obs.group for obs in observations})
    for group in groups:
        indexes = [i for i, obs in enumerate(observations) if obs.group == group]
        mean = np.mean(estimates[indexes], axis=0)
        residuals[indexes] = estimates[indexes] - mean
    return residuals


def residual_vector(names: list[str], values: np.ndarray, observations: list[Observation]) -> np.ndarray:
    return residual_matrix(observations, as_params(names, values)).ravel()


def fit_model(name: str, observations: list[Observation]):
    names = MODEL_FAMILIES[name]
    if not names:
        params = as_params([], np.array([]))
        return params, None
    lower = np.array([PARAM_BOUNDS[param][0] for param in names])
    upper = np.array([PARAM_BOUNDS[param][1] for param in names])
    result = least_squares(
        lambda values: residual_vector(names, values, observations),
        np.zeros(len(names)),
        bounds=(lower, upper),
        loss="linear",
        x_scale="jac",
        max_nfev=20000,
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
    )
    return as_params(names, result.x), result


def metrics(observations: list[Observation], params: dict[str, float]) -> dict[str, float]:
    if not observations:
        return {"points": 0, "rms3": float("nan"), "max3": float("nan")}
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


def jacobian_condition(result) -> tuple[int, float]:
    if result is None or result.jac.size == 0:
        return (0, float("nan"))
    singular_values = np.linalg.svd(result.jac, compute_uv=False)
    if singular_values.size == 0:
        return (0, float("nan"))
    tol = singular_values[0] * max(result.jac.shape) * np.finfo(float).eps
    rank = int(np.sum(singular_values > tol))
    condition = float(singular_values[0] / singular_values[-1]) if singular_values[-1] > 0.0 else float("inf")
    return rank, condition


def format_metric_row(name: str, train: dict[str, float], holdout: dict[str, float], rank: int, cond: float) -> str:
    cond_text = "n/a" if math.isnan(cond) else f"{cond:.2e}"
    return (
        f"| `{name}` | {train['points']:.0f} | {train['rms3']:.6f} | {train['max3']:.6f} | "
        f"{holdout['points']:.0f} | {holdout['rms3']:.6f} | {holdout['max3']:.6f} | {rank} | {cond_text} |"
    )


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


def group_summary(observations: list[Observation], params: dict[str, float]) -> list[str]:
    lines = []
    residuals = residual_matrix(observations, params)
    for obs, res in zip(observations, residuals):
        lines.append(
            f"| `{obs.source}` | {obs.line} | `{obs.b_deg:+.0f}` | `{obs.c_deg:.0f}` | "
            f"{res[0]:+.6f} | {res[1]:+.6f} | {res[2]:+.6f} | {np.linalg.norm(res):.6f} |"
        )
    return lines


def c_orbit_summary(observations: list[Observation]) -> list[str]:
    b0 = [obs for obs in observations if abs(obs.b_deg) < 1e-6]
    lines = []
    if not b0:
        return lines
    means = {}
    for c_deg in sorted({round(obs.c_deg) for obs in b0}):
        pts = np.array([obs.center for obs in b0 if round(obs.c_deg) == c_deg])
        means[c_deg] = np.mean(pts, axis=0)
    base = means.get(0)
    for c_deg, mean in means.items():
        delta = mean - base if base is not None else np.zeros(3)
        lines.append(
            f"| `{c_deg:.0f}` | {mean[0]:.6f} | {mean[1]:.6f} | {mean[2]:.6f} | "
            f"{delta[0]:+.6f} | {delta[1]:+.6f} | {delta[2]:+.6f} |"
        )
    return lines


def write_report(
    path: Path,
    train: list[Observation],
    holdout: list[Observation],
    fit_results: dict[str, tuple],
    b0_fit: tuple,
):
    current_params = as_params([], np.array([]))
    b0_params, _ = b0_fit
    b0_opposite = as_params(["dcx", "dcy"], np.array([-b0_params["dcx"], -b0_params["dcy"]]))
    current_pin_params, _ = fit_results["current_pins"]
    axis_params, _ = fit_results["axis_vectors"]
    affine_params, _ = fit_results["axis_vectors_linear_diag"]
    b0_train = [obs for obs in train if abs(obs.b_deg) < 1e-6]
    lines = [
        "# TCPC Expanded Geometry Fit Report",
        "",
        "Generated by `tcpc_expanded_geometry_fit.py`.",
        "",
        "## Data Sets",
        "",
        f"- training: `{len(train)}` valid pass-2 points from the 2026-05-04 B90 C-quadrant run",
        f"- holdout: `{len(holdout)}` valid pass-2 points from the clean B90 C0/C180 rerun",
        "- the earlier bad accepted `B0 C90` false-top row is filtered by the `29.9 mm` diameter floor",
        "",
        "## B0 C-Orbit In Training Data",
        "",
        "| C deg | mean X | mean Y | mean Z | dX from C0 | dY from C0 | dZ from C0 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *c_orbit_summary(train),
        "",
        "### B0-Only C-Center Fit",
        "",
        "This fit uses only B0 rows from the C-quadrant run, so it is not contaminated by B90 residuals.",
        "",
        f"- current B0 C-orbit RMS/max: `{metrics(b0_train, current_params)['rms3']:.6f}` / `{metrics(b0_train, current_params)['max3']:.6f}` mm",
        f"- fitted B0 C-orbit RMS/max: `{metrics(b0_train, b0_params)['rms3']:.6f}` / `{metrics(b0_train, b0_params)['max3']:.6f}` mm",
        f"- opposite-sign RMS/max: `{metrics(b0_train, b0_opposite)['rms3']:.6f}` / `{metrics(b0_train, b0_opposite)['max3']:.6f}` mm",
        f"- `dcx = {b0_params['dcx']:.9f} mm`",
        f"- `dcy = {b0_params['dcy']:.9f} mm`",
        f"- equivalent test-only `cal-c-to-b.x = {CURRENT_CAL_C_TO_B[0] + b0_params['dcx']:.9f}`",
        f"- equivalent test-only `cal-c-to-b.y = {CURRENT_CAL_C_TO_B[1] + b0_params['dcy']:.9f}`",
        "",
        "## Initial Conclusions",
        "",
        "- The B0 C-orbit is the cleanest identified term. It supports a C-center correction of about `+0.1009 mm` in the current `c-to-b.x` convention and about `-0.0045 mm` in `c-to-b.y`.",
        "- Existing `headheadkins` pins reduce residuals but are rank-deficient on this data. Do not load the current-pin fit as a live candidate.",
        "- Adding C/B axis-vector terms gives only a modest improvement over current pins, so the remaining high-B error is not just simple rotary-axis skew.",
        "- Adding machine-fixed linear scale terms improves both training and holdout residuals, but the X scale term hits its diagnostic bound and the Jacobian is ill-conditioned. Treat this as evidence to test linear-axis geometry, not as a compensation answer.",
        "- The next model pass should keep the C-center term separate, then fit rotary-axis angular terms and linear-axis terms with dedicated validation data.",
        "",
        "## Model Comparison",
        "",
        "| model | train n | train RMS 3D | train max 3D | holdout n | holdout RMS 3D | holdout max 3D | rank | Jacobian cond |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, (params, result) in fit_results.items():
        rank, cond = jacobian_condition(result)
        lines.append(format_metric_row(name, metrics(train, params), metrics(holdout, params), rank, cond))
    lines.extend(
        [
            "",
            "## Current-Pin Fit Parameters",
            "",
            "This is the best training-set fit using only variables that the current `headheadkins` already exposes. The Jacobian is rank-deficient, so do not load this as a candidate.",
            "",
            *format_params(current_pin_params, MODEL_FAMILIES["current_pins"]),
            "",
            "## Axis-Vector Fit Parameters",
            "",
            "These are deltas relative to the current live/reverted candidate. They are an offline model result, not values to load directly.",
            "",
            *format_params(axis_params, MODEL_FAMILIES["axis_vectors"]),
            "",
            "## Axis-Vector Plus Linear-Diagonal Fit Parameters",
            "",
            "The linear diagonal terms are diagnostic only. They are dimensionless scale terms, so `0.001` is about `1 mm/m`.",
            "",
            *format_params(affine_params, MODEL_FAMILIES["axis_vectors_linear_diag"]),
            "",
            "## Training Residuals Before Fit",
            "",
            "| source | line | B | C | residual X | residual Y | residual Z | norm |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            *group_summary(train, current_params),
            "",
            "## Training Residuals After Axis-Vector Fit",
            "",
            "| source | line | B | C | residual X | residual Y | residual Z | norm |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            *group_summary(train, axis_params),
            "",
            "## Notes",
            "",
            "- `current_pins` is the best model that can be represented with the existing `headheadkins` HAL pins.",
            "- `axis_vectors` adds C-axis tilt and B-axis skew terms but requires kinematics code changes before live testing.",
            "- `axis_vectors_linear_diag` shows whether residuals can be reduced by machine-fixed axis scale terms; do not treat those as confirmed until a dedicated linear-axis test is run.",
            "- Any candidate sign must still be verified in simulation before applying live.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        type=Path,
        default=CONFIG_DIR / "TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md",
        help="Markdown report path",
    )
    args = parser.parse_args()

    train = read_results(
        CONFIG_DIR / "tcpc-b90-c-quadrant-diagnostic-2pass-results.csv",
        source="b90_c_quadrant",
        group="2026-05-04-b90-c-quadrant",
    )
    holdout = read_results(
        CONFIG_DIR / "tcpc-b90-b-axis-diagnostic-2pass-results.csv",
        source="b90_b_axis",
        group="2026-05-03-clean-b90",
        min_line=18,
        max_line=37,
    )

    fit_results = {}
    for name in MODEL_FAMILIES:
        fit_results[name] = fit_model(name, train)

    b0_train = [obs for obs in train if abs(obs.b_deg) < 1e-6]
    b0_fit = fit_model("c_center_xy", b0_train)

    write_report(args.report, train, holdout, fit_results, b0_fit)

    print(f"training points: {len(train)}")
    print(f"holdout points: {len(holdout)}")
    print(f"report: {args.report}")
    print()
    b0_params, _ = b0_fit
    print(
        "b0_only_c_center, "
        f"dcx={b0_params['dcx']:.9f}, dcy={b0_params['dcy']:.9f}, "
        f"rms3={metrics(b0_train, b0_params)['rms3']:.6f}, "
        f"max3={metrics(b0_train, b0_params)['max3']:.6f}"
    )
    print()
    print("model, train_rms3, train_max3, holdout_rms3, holdout_max3")
    for name, (params, _) in fit_results.items():
        train_metrics = metrics(train, params)
        holdout_metrics = metrics(holdout, params)
        print(
            f"{name}, {train_metrics['rms3']:.6f}, {train_metrics['max3']:.6f}, "
            f"{holdout_metrics['rms3']:.6f}, {holdout_metrics['max3']:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
