#!/usr/bin/env python3
"""Fit current dual-length sphere data without changing the live machine.

The fitter mirrors the rigid portion of ``headheadkins`` and the exact active
T3/T4 tool lengths.  T4 is the training probe.  T3 is reported only as a
holdout so a short-probe-tuned correction cannot silently re-enter the fit.

This script is deliberately diagnostic.  It writes a report and residual CSV;
it never edits HAL, INI, tool-table, parameter, or G-code files.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent
BASELINE = HERE / "tcpc-positive-b-c45-baseline-results.csv"
HIGH_B_T3 = HERE / "tcpc-high-b-t3-supplemental-results.csv"
HIGH_B_T4 = HERE / "tcpc-high-b-t4-supplemental-results.csv"
DEFAULT_REPORT = HERE / "TCPC_DUAL_PROBE_OFFLINE_FIT_REPORT.md"
DEFAULT_RESIDUALS = HERE / "tcpc-dual-probe-offline-fit-residuals.csv"

T3 = 3
T4 = 4
T3_LENGTH = 128.606729
T4_LENGTH = 229.407000
LENGTH_SEPARATION = T4_LENGTH - T3_LENGTH

# Exact active rigid geometry from the 2026-08-24 calibration HAL snapshot.
CURRENT_C_TO_B = np.array([0.010934 + 0.035886006, 0.0 + 0.009526306, -270.0])
CURRENT_B_TO_NOSE = np.array([-0.668710, -26.721365, -180.373272 + 0.815000])
CURRENT_B_ZERO = 0.0
CURRENT_C_ZERO = -0.024500


@dataclass(frozen=True)
class Observation:
    source: str
    group: str
    tool: int
    length: float
    seq: int
    b_deg: float
    c_deg: float
    center: np.ndarray
    trusted_holdout: bool

    @property
    def label(self) -> str:
        return f"{self.source}:T{self.tool}:S{self.seq}:B{self.b_deg:g}:C{self.c_deg:g}"


@dataclass(frozen=True)
class ModelSpec:
    name: str
    parameters: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class FitResult:
    spec: ModelSpec
    values: np.ndarray
    residuals: np.ndarray
    rank: int
    condition: float
    at_bounds: tuple[str, ...]

    @property
    def params(self) -> dict[str, float]:
        return dict(zip(self.spec.parameters, self.values))


@dataclass(frozen=True)
class CrossValidation:
    residuals: np.ndarray
    worst_b_deg: float
    worst_max_mm: float


PARAM_BOUNDS = {
    "dcx_mm": (-2.0, 2.0),
    "dcy_mm": (-2.0, 2.0),
    "dbx_mm": (-3.0, 3.0),
    "dby_mm": (-3.0, 3.0),
    "dbz_mm": (-3.0, 3.0),
    "db_zero_deg": (-0.5, 0.5),
    "dc_zero_deg": (-0.5, 0.5),
    "c_tilt_x_deg": (-0.5, 0.5),
    "c_tilt_y_deg": (-0.5, 0.5),
    "b_axis_x_deg": (-0.5, 0.5),
    "b_axis_z_deg": (-0.5, 0.5),
    "tool_tilt_x_deg": (-0.25, 0.25),
    "tool_tilt_y_deg": (-0.25, 0.25),
}

LOW_ADDITIVE_TERMS = (
    "c_cos",
    "c_sin",
    "c_cos2",
    "c_sin2",
    "b_sin",
    "b_omc",
    "b_sin2",
)
CURRENT_SURFACE_TERMS = LOW_ADDITIVE_TERMS + (
    "bc_sinb_sinc",
    "bc_omcb_sinc",
    "bc_omcb_sin2c",
    "bc_sinb_cosc",
    "bc_omcb_cosc",
    "bc_sinb_sin2c",
    "bc_sinb_cos2c",
)
AXES = ("x", "y", "z")


def additive_parameter_names(terms: Sequence[str]) -> tuple[str, ...]:
    return tuple(f"h_{term}_{axis}_mm" for term in terms for axis in AXES)


for name in additive_parameter_names(CURRENT_SURFACE_TERMS):
    PARAM_BOUNDS[name] = (-1.5, 1.5)

MODELS = (
    ModelSpec("current", (), "unchanged active kinematics"),
    ModelSpec(
        "tool_vector_only",
        ("tool_tilt_x_deg", "tool_tilt_y_deg"),
        "common active-length vector tilt; requires a future kinematics extension",
    ),
    ModelSpec(
        "rigid_translation",
        ("dcx_mm", "dcy_mm", "dbx_mm", "dby_mm", "dbz_mm"),
        "existing rigid C-to-B and B-to-nose translation pins",
    ),
    ModelSpec(
        "minimal_existing_angles",
        ("db_zero_deg", "c_tilt_x_deg", "c_tilt_y_deg", "b_axis_z_deg"),
        "existing angular pins with C zero and B-axis X fixed as the gauge",
    ),
    ModelSpec(
        "existing_rigid",
        (
            "dcx_mm",
            "dcy_mm",
            "dbx_mm",
            "dby_mm",
            "dbz_mm",
            "db_zero_deg",
            "dc_zero_deg",
            "c_tilt_x_deg",
            "c_tilt_y_deg",
            "b_axis_x_deg",
            "b_axis_z_deg",
        ),
        "all currently exposed low-dimensional rigid pins",
    ),
    ModelSpec(
        "rigid_plus_tool_vector",
        (
            "dcx_mm",
            "dcy_mm",
            "dbx_mm",
            "dby_mm",
            "dbz_mm",
            "db_zero_deg",
            "dc_zero_deg",
            "c_tilt_x_deg",
            "c_tilt_y_deg",
            "b_axis_x_deg",
            "b_axis_z_deg",
            "tool_tilt_x_deg",
            "tool_tilt_y_deg",
        ),
        "existing rigid pins plus a diagnostic active-length vector tilt",
    ),
    ModelSpec(
        "additive_low_order",
        additive_parameter_names(LOW_ADDITIVE_TERMS),
        "length-independent first/second C and low-order B surface deltas",
    ),
    ModelSpec(
        "additive_current_surface",
        additive_parameter_names(CURRENT_SURFACE_TERMS),
        "length-independent deltas spanning every currently active C/B/cross surface family",
    ),
)


def rotation_x(deg: float) -> np.ndarray:
    angle = math.radians(deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rotation_y(deg: float) -> np.ndarray:
    angle = math.radians(deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rotation_z(deg: float) -> np.ndarray:
    angle = math.radians(deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rotation_axis(axis: np.ndarray, deg: float) -> np.ndarray:
    unit = axis / np.linalg.norm(axis)
    x, y, z = unit
    angle = math.radians(deg)
    c = math.cos(angle)
    s = math.sin(angle)
    cross = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    return c * np.eye(3) + s * cross + (1.0 - c) * np.outer(unit, unit)


def parameter(params: dict[str, float], name: str) -> float:
    return params.get(name, 0.0)


def rigid_offset(b_deg: float, c_deg: float, length: float, params: dict[str, float]) -> np.ndarray:
    c_to_b = CURRENT_C_TO_B + np.array(
        [parameter(params, "dcx_mm"), parameter(params, "dcy_mm"), 0.0]
    )
    b_to_nose = CURRENT_B_TO_NOSE + np.array(
        [
            parameter(params, "dbx_mm"),
            parameter(params, "dby_mm"),
            parameter(params, "dbz_mm"),
        ]
    )

    tx = math.tan(math.radians(parameter(params, "tool_tilt_x_deg")))
    ty = math.tan(math.radians(parameter(params, "tool_tilt_y_deg")))
    tool_direction = np.array([tx, ty, -1.0])
    tool_direction /= np.linalg.norm(tool_direction)
    b_to_tool = b_to_nose + length * tool_direction

    b_axis = np.array(
        [
            math.tan(math.radians(parameter(params, "b_axis_x_deg"))),
            1.0,
            math.tan(math.radians(parameter(params, "b_axis_z_deg"))),
        ]
    )
    b_axis /= np.linalg.norm(b_axis)

    b_eff = b_deg + CURRENT_B_ZERO + parameter(params, "db_zero_deg")
    c_eff = c_deg + CURRENT_C_ZERO + parameter(params, "dc_zero_deg")
    local = c_to_b + rotation_axis(b_axis, b_eff) @ b_to_tool
    c_rotated = rotation_z(c_eff) @ local
    c_frame = rotation_y(parameter(params, "c_tilt_y_deg")) @ rotation_x(
        parameter(params, "c_tilt_x_deg")
    )
    return c_frame @ c_rotated


def additive_basis(b_deg: float, c_deg: float) -> dict[str, float]:
    b_rad = math.radians(b_deg + CURRENT_B_ZERO)
    c_rad = math.radians(c_deg + CURRENT_C_ZERO)
    c_ref = math.radians(CURRENT_C_ZERO)
    sin_b = math.sin(b_rad)
    omc_b = 1.0 - math.cos(b_rad)
    sin_c = math.sin(c_rad)
    cos_c = math.cos(c_rad)
    return {
        "c_cos": cos_c - math.cos(c_ref),
        "c_sin": sin_c - math.sin(c_ref),
        "c_cos2": math.cos(2.0 * c_rad) - math.cos(2.0 * c_ref),
        "c_sin2": math.sin(2.0 * c_rad) - math.sin(2.0 * c_ref),
        "b_sin": sin_b,
        "b_omc": omc_b,
        "b_sin2": math.sin(2.0 * b_rad),
        "bc_sinb_sinc": sin_b * sin_c,
        "bc_omcb_sinc": omc_b * sin_c,
        "bc_omcb_sin2c": omc_b * sin_c * sin_c,
        "bc_sinb_cosc": sin_b * cos_c,
        "bc_omcb_cosc": omc_b * cos_c,
        "bc_sinb_sin2c": sin_b * math.sin(2.0 * c_rad),
        "bc_sinb_cos2c": sin_b * math.cos(2.0 * c_rad),
    }


def additive_offset(b_deg: float, c_deg: float, params: dict[str, float]) -> np.ndarray:
    basis = additive_basis(b_deg, c_deg)
    result = np.zeros(3)
    for term, value in basis.items():
        for axis_index, axis in enumerate(AXES):
            result[axis_index] += value * parameter(params, f"h_{term}_{axis}_mm")
    return result


def offset_change(obs: Observation, params: dict[str, float]) -> np.ndarray:
    return (
        rigid_offset(obs.b_deg, obs.c_deg, obs.length, params)
        - rigid_offset(obs.b_deg, obs.c_deg, obs.length, {})
        + additive_offset(obs.b_deg, obs.c_deg, params)
    )


def corrected_centers(observations: Sequence[Observation], params: dict[str, float]) -> np.ndarray:
    return np.array([obs.center + offset_change(obs, params) for obs in observations])


def centered_residuals(observations: Sequence[Observation], params: dict[str, float]) -> np.ndarray:
    if not observations:
        return np.empty((0, 3))
    estimates = corrected_centers(observations, params)
    residuals = np.zeros_like(estimates)
    for group in sorted({obs.group for obs in observations}):
        indexes = [index for index, obs in enumerate(observations) if obs.group == group]
        residuals[indexes] = estimates[indexes] - np.mean(estimates[indexes], axis=0)
    return residuals


def metric(residuals: np.ndarray) -> tuple[float, float]:
    if not len(residuals):
        return float("nan"), float("nan")
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms**2))), float(np.max(norms))


def metric_text(residuals: np.ndarray) -> str:
    rms, maximum = metric(residuals)
    return f"{rms:.6f} / {maximum:.6f}"


def _center_columns(row: dict[str, str]) -> np.ndarray:
    return np.array(
        [
            float(row["center_abs_x_mm"]),
            float(row["center_abs_y_mm"]),
            float(row["center_abs_z_mm"]),
        ]
    )


def read_baseline(path: Path) -> list[Observation]:
    observations: list[Observation] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            leg = int(float(row["leg_id"]))
            attempt = int(float(row["attempt_id"]))
            if (leg, attempt) not in {(1, 7), (2, 1)}:
                continue
            tool = T3 if leg == 1 else T4
            seq = int(float(row["sample_seq"]))
            observations.append(
                Observation(
                    source="positive_b_baseline",
                    group=f"positive_b_baseline_t{tool}",
                    tool=tool,
                    length=T3_LENGTH if tool == T3 else T4_LENGTH,
                    seq=seq,
                    b_deg=float(row["abs_b_deg"]),
                    c_deg=float(row["abs_c_deg"]),
                    center=_center_columns(row),
                    # The T3 B30 and outer closures failed their strict gates.
                    trusted_holdout=tool == T4 or seq <= 27,
                )
            )
    return observations


def read_high_b(path: Path, tool: int) -> list[Observation]:
    observations: list[Observation] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            observations.append(
                Observation(
                    source=f"high_b_t{tool}",
                    group=f"high_b_t{tool}",
                    tool=tool,
                    length=T3_LENGTH if tool == T3 else T4_LENGTH,
                    seq=int(float(row["sample_seq"])),
                    b_deg=float(row["abs_b_deg"]),
                    c_deg=float(row["abs_c_deg"]),
                    center=_center_columns(row),
                    trusted_holdout=True,
                )
            )
    return observations


def load_observations() -> list[Observation]:
    observations = read_baseline(BASELINE)
    observations.extend(read_high_b(HIGH_B_T3, T3))
    observations.extend(read_high_b(HIGH_B_T4, T4))
    return observations


def fit_model(spec: ModelSpec, training: Sequence[Observation]) -> FitResult:
    if not spec.parameters:
        residuals = centered_residuals(training, {})
        return FitResult(spec, np.empty(0), residuals, 0, float("nan"), ())

    lower = np.array([PARAM_BOUNDS[name][0] for name in spec.parameters])
    upper = np.array([PARAM_BOUNDS[name][1] for name in spec.parameters])

    def objective(values: np.ndarray) -> np.ndarray:
        params = dict(zip(spec.parameters, values))
        return centered_residuals(training, params).ravel()

    result = least_squares(
        objective,
        np.zeros(len(spec.parameters)),
        bounds=(lower, upper),
        loss="linear",
        x_scale="jac",
        max_nfev=100000,
        ftol=1e-13,
        xtol=1e-13,
        gtol=1e-13,
    )
    singular = np.linalg.svd(result.jac, compute_uv=False)
    if singular.size:
        tolerance = singular[0] * max(result.jac.shape) * np.finfo(float).eps
        rank = int(np.sum(singular > tolerance))
        condition = float(singular[0] / singular[-1]) if singular[-1] > 0.0 else float("inf")
    else:
        rank = 0
        condition = float("nan")
    at_bounds = tuple(
        name
        for name, value, low, high in zip(spec.parameters, result.x, lower, upper)
        if abs(value - low) < 1e-7 or abs(value - high) < 1e-7
    )
    return FitResult(spec, result.x, centered_residuals(training, dict(zip(spec.parameters, result.x))), rank, condition, at_bounds)


def subset(observations: Iterable[Observation], *, tool: int | None = None, trusted: bool | None = None) -> list[Observation]:
    return [
        obs
        for obs in observations
        if (tool is None or obs.tool == tool)
        and (trusted is None or obs.trusted_holdout == trusted)
    ]


def evaluate(observations: Sequence[Observation], fit: FitResult) -> np.ndarray:
    return centered_residuals(observations, fit.params)


def group_centers(observations: Sequence[Observation], params: dict[str, float]) -> dict[str, np.ndarray]:
    estimates = corrected_centers(observations, params)
    return {
        group: np.mean(
            [estimate for obs, estimate in zip(observations, estimates) if obs.group == group], axis=0
        )
        for group in sorted({obs.group for obs in observations})
    }


def leave_b_out(spec: ModelSpec, observations: Sequence[Observation]) -> CrossValidation:
    residual_blocks = []
    worst_b = float("nan")
    worst_max = -1.0
    for b_deg in sorted({obs.b_deg for obs in observations}):
        training = [obs for obs in observations if obs.b_deg != b_deg]
        held_out = [obs for obs in observations if obs.b_deg == b_deg]
        fit = fit_model(spec, training)
        centers = group_centers(training, fit.params)
        residuals = np.array(
            [obs.center + offset_change(obs, fit.params) - centers[obs.group] for obs in held_out]
        )
        residual_blocks.append(residuals)
        _, maximum = metric(residuals)
        if maximum > worst_max:
            worst_b = b_deg
            worst_max = maximum
    return CrossValidation(np.vstack(residual_blocks), worst_b, worst_max)


def direct_b0_length_vector(observations: Sequence[Observation]) -> tuple[np.ndarray, np.ndarray, float, float]:
    rows = {
        (obs.tool, obs.seq): obs
        for obs in observations
        if obs.source == "positive_b_baseline" and obs.seq <= 9
    }
    reference = np.mean(
        [rows[(T4, seq)].center - rows[(T3, seq)].center for seq in (1, 9)], axis=0
    )
    matrix = []
    values = []
    c_ref = CURRENT_C_ZERO
    for seq in range(1, 10):
        short = rows[(T3, seq)]
        long = rows[(T4, seq)]
        observed = long.center - short.center - reference
        pose_rotation = rotation_z(short.c_deg + CURRENT_C_ZERO)
        reference_rotation = rotation_z(c_ref)
        matrix.append(pose_rotation - reference_rotation)
        values.append(observed)
    design = np.vstack(matrix)
    target = np.hstack(values)
    error_vector = np.linalg.lstsq(design, target, rcond=None)[0]
    residuals = (target - design @ error_vector).reshape(-1, 3)
    rms, maximum = metric(residuals)
    candidate_tilt_deg = -np.degrees(error_vector[:2] / LENGTH_SEPARATION)
    return error_vector, candidate_tilt_deg, rms, maximum


def write_residuals(path: Path, observations: Sequence[Observation], fits: Sequence[FitResult]) -> None:
    columns = [
        "model",
        "source",
        "group",
        "tool",
        "sample_seq",
        "abs_b_deg",
        "abs_c_deg",
        "trusted_holdout",
        "residual_x_mm",
        "residual_y_mm",
        "residual_z_mm",
        "residual_norm_mm",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for fit in fits:
            residuals = evaluate(observations, fit)
            for obs, residual in zip(observations, residuals):
                writer.writerow(
                    {
                        "model": fit.spec.name,
                        "source": obs.source,
                        "group": obs.group,
                        "tool": obs.tool,
                        "sample_seq": obs.seq,
                        "abs_b_deg": f"{obs.b_deg:.6f}",
                        "abs_c_deg": f"{obs.c_deg:.6f}",
                        "trusted_holdout": int(obs.trusted_holdout),
                        "residual_x_mm": f"{residual[0]:.9f}",
                        "residual_y_mm": f"{residual[1]:.9f}",
                        "residual_z_mm": f"{residual[2]:.9f}",
                        "residual_norm_mm": f"{np.linalg.norm(residual):.9f}",
                    }
                )


def format_params(fit: FitResult) -> list[str]:
    if not fit.spec.parameters:
        return ["- no fitted parameters"]
    return [f"- `{name}` = `{value:+.9f}`" for name, value in zip(fit.spec.parameters, fit.values)]


def write_report(
    path: Path,
    observations: Sequence[Observation],
    fits: Sequence[FitResult],
    cross_validation: dict[str, CrossValidation],
    residual_path: Path,
) -> None:
    t4 = subset(observations, tool=T4)
    t3 = subset(observations, tool=T3)
    t3_trusted = [obs for obs in t3 if obs.trusted_holdout]
    error_vector, tilt_deg, direct_rms, direct_max = direct_b0_length_vector(observations)

    lines = [
        "# TCPC Dual-Probe Offline Fit Report",
        "",
        "Generated by `fit_tcpc_dual_probe.py`. This is an analysis artifact, not a live calibration release.",
        "",
        "## Dataset Boundary",
        "",
        f"- T4 primary training rows: `{len(t4)}` (31 stable low-angle rows plus 9 accepted high-B prefix rows)",
        f"- T3 holdout rows: `{len(t3)}`; trusted verification subset: `{len(t3_trusted)}`",
        "- T3 low-angle B30 and final B0 rows remain visible but are excluded from the trusted holdout because their strict closures failed.",
        "- Each acquisition method/tool leg has its own fitted constant center. Absolute centers are not mixed across tool length or probing method.",
        "- The T4 high-B run is diagnostic-only and incomplete after B90/C180; no missing B90/C270 value is imputed.",
        "",
        "## Model Comparison",
        "",
        "Metrics are 3D center residual RMS / maximum in millimetres. All parameters are fitted on T4 only.",
        "",
        "| model | T4 train | T4 leave-B-out | worst held B/max | T3 trusted holdout | T3 all diagnostic | rank/parameters | condition |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for fit in fits:
        condition = "n/a" if math.isnan(fit.condition) else f"{fit.condition:.3e}"
        cv = cross_validation[fit.spec.name]
        lines.append(
            f"| `{fit.spec.name}` | `{metric_text(evaluate(t4, fit))}` | `{metric_text(cv.residuals)}` | "
            f"`B{cv.worst_b_deg:+g} / {cv.worst_max_mm:.6f}` | "
            f"`{metric_text(evaluate(t3_trusted, fit))}` | `{metric_text(evaluate(t3, fit))}` | "
            f"{fit.rank}/{len(fit.spec.parameters)} | {condition} |"
        )

    lines.extend(
        [
            "",
            "## Fit Finding",
            "",
            "No current-data parameter family is eligible for live loading. The full additive surface reaches `0.081212 mm` maximum on its T4 training rows but expands to approximately `0.961 mm` when an entire B group is withheld. The exposed rigid family is strongly ill-conditioned, predicts more than `0.53 mm` on the held-out B group, and worsens the untouched T3 result.",
            "",
            "The two-parameter tool-vector hypothesis is the only stable low-dimensional improvement on unseen T4 B groups, but it does not improve T3 and is physically confounded with the two probe assemblies. It is retained as a hypothesis for the balanced-B campaign, not as a HAL candidate.",
            "",
            "## Direct Length Diagnostic",
            "",
            "The matched B0 C sweep contains a clean rotating long-minus-short lateral vector. "
            "Solving only that differential gives:",
            "",
            f"- observed local length-difference vector: `({error_vector[0]:+.9f}, {error_vector[1]:+.9f}, {error_vector[2]:+.9f}) mm`",
            f"- candidate cancelling active-vector tilt: X `{tilt_deg[0]:+.6f} deg`, Y `{tilt_deg[1]:+.6f} deg`",
            f"- B0 differential reconstruction residual RMS/max: `{direct_rms:.6f} / {direct_max:.6f} mm`",
            "",
            "This is strong evidence for a rotating probe/spindle-vector component, but two different physical probe assemblies cannot by themselves distinguish common spindle-axis tilt from keyed probe/stylus eccentricity. The live kinematics has no common active-length vector tilt input, so this result is not directly loadable.",
            "",
            "## Fitted Parameters",
        ]
    )
    for fit in fits:
        lines.extend(["", f"### {fit.spec.name}", "", fit.spec.description + "."])
        lines.extend(format_params(fit))
        if fit.at_bounds:
            lines.append(f"- parameters at bounds: `{', '.join(fit.at_bounds)}`")

    lines.extend(
        [
            "",
            "## Decision Boundary",
            "",
            "A parameter family is not eligible for live use merely because it lowers the T4 training residual. It must also improve the untouched T3 rows, remain full-rank and stable under the relocated-sphere expanded grid, and survive pose holdouts. Positive-B-only data cannot uniquely release B zero, B-sign parity, pivot translation, and angular alignment together.",
            "",
            "The recommended next campaign therefore uses T4 for the expanded balanced-B fit and T3 for a shorter untouched verification grid. The sphere relocation starts a new campaign; none of its absolute centers may be appended to these groups.",
            "",
            f"Detailed residuals: `{residual_path.name}`",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def self_test() -> None:
    zero = rigid_offset(0.0, 0.0, T4_LENGTH, {})
    assert np.allclose(offset_change(Observation("x", "g", T4, T4_LENGTH, 1, 0.0, 0.0, zero, True), {}), 0.0)
    params = {"tool_tilt_y_deg": 0.02}
    delta_zero = rigid_offset(0.0, 0.0, T4_LENGTH, params) - rigid_offset(
        0.0, 0.0, T4_LENGTH, {}
    )
    delta_180 = rigid_offset(0.0, 180.0, T4_LENGTH, params) - rigid_offset(
        0.0, 180.0, T4_LENGTH, {}
    )
    assert np.linalg.norm(delta_zero[:2]) > 0.05
    assert np.dot(delta_zero[:2], delta_180[:2]) < 0.0


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

    observations = load_observations()
    t4 = subset(observations, tool=T4)
    fits = [fit_model(spec, t4) for spec in MODELS]
    cross_validation = {spec.name: leave_b_out(spec, t4) for spec in MODELS}
    write_residuals(args.residuals, observations, fits)
    write_report(args.report, observations, fits, cross_validation, args.residuals)
    print(f"wrote {args.report}")
    print(f"wrote {args.residuals}")
    for fit in fits:
        print(f"{fit.spec.name}: T4 {metric_text(evaluate(t4, fit))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
