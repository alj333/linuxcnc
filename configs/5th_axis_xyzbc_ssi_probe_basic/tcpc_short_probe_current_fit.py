#!/usr/bin/env python3
"""Analyze the current short-probe TCPC coverage run.

This report is deliberately session-local. It uses only the accepted rows from
the current short-probe baseline/resume/supplement sequence and excludes the
known failed B-60 C0 pass-1 probe row.
"""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

import tcpc_expanded_geometry_fit as fit


CONFIG_DIR = Path(__file__).resolve().parent
RESULTS_PATH = CONFIG_DIR / "tcpc-b-angle-scaling-diagnostic-2pass-results.csv"
REPORT_PATH = CONFIG_DIR / "TCPC_SHORT_PROBE_CURRENT_FIT_REPORT.md"

DATA_BLOCKS = [
    ("mode9", "short-probe mode 9", 273, 348),
    ("supplement", "short-probe C90/C270 supplement", 349, 394),
    ("continuation", "short-probe B-30 continuation", 396, 407),
]
EXCLUDED_LINES = [395]
AXIS_NAMES = ["x", "y", "z"]

MODEL_NAMES = [
    "c_center_fixed_only",
    "current_pins_no_cxy",
    "axis_vectors_no_cxy",
    "axis_vectors_linear_diag_no_cxy",
    "b_harmonic_machine_no_cxy",
    "b_harmonic_machine_bcross_no_cxy",
]

BASE_EXTENDED_TERMS = [
    "sinb",
    "omcb",
    "sin2b",
    "sinb_cosc",
    "sinb_sinc",
    "omcb_sin2c",
    "omcb_cosc",
    "omcb_sinc",
]

C_HARMONIC_TERMS = ["c_cos", "c_sin", "c_cos2", "c_sin2"]
NEW_B_CROSS_TERMS = ["sinb_sin2c", "sinb_cos2c"]
SELECTED_EXTENDED_TERMS = C_HARMONIC_TERMS + BASE_EXTENDED_TERMS + NEW_B_CROSS_TERMS


@dataclass(frozen=True)
class DataRow:
    line: int
    block: str
    b_deg: float
    c_deg: float
    center: np.ndarray
    err_u: float
    err_v: float
    diam_u: float
    diam_v: float

    @property
    def pose(self) -> str:
        return f"B{self.b_deg:+.0f} C{self.c_deg:.0f}"


def vec_text(vec: np.ndarray) -> str:
    return f"{vec[0]:+.6f}, {vec[1]:+.6f}, {vec[2]:+.6f}"


def metric(norms: list[float] | np.ndarray) -> tuple[float, float]:
    values = np.array(norms, dtype=float)
    return float(math.sqrt(np.mean(values**2))), float(np.max(values))


def metric_text_from_residuals(residuals: np.ndarray) -> str:
    norms = np.linalg.norm(residuals, axis=1)
    rms, max_value = metric(norms)
    return f"{rms:.6f} / {max_value:.6f}"


def read_rows() -> list[DataRow]:
    block_by_line = {}
    for block, _label, start, end in DATA_BLOCKS:
        for line in range(start, end + 1):
            block_by_line[line] = block

    rows: list[DataRow] = []
    with RESULTS_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for line, row in enumerate(reader, start=2):
            if line not in block_by_line:
                continue
            if line in EXCLUDED_LINES:
                continue
            if float(row["pass_num"]) != 2.0 or float(row["accepted"]) != 1.0:
                continue
            rows.append(
                DataRow(
                    line=line,
                    block=block_by_line[line],
                    b_deg=float(row["abs_b_deg"]),
                    c_deg=float(row["abs_c_deg"]),
                    center=np.array(
                        [
                            float(row["center_abs_x_mm"]),
                            float(row["center_abs_y_mm"]),
                            float(row["center_abs_z_mm"]),
                        ]
                    ),
                    err_u=float(row["u_center_error_mm"]),
                    err_v=float(row["v_center_error_mm"]),
                    diam_u=float(row["u_corr_diam_mm"]),
                    diam_v=float(row["v_corr_diam_mm"]),
                )
            )
    return rows


def read_observations() -> list[fit.Observation]:
    observations: list[fit.Observation] = []
    for block, label, start, end in DATA_BLOCKS:
        observations.extend(
            fit.read_results(
                RESULTS_PATH,
                source=block,
                group=label,
                active_name="validated_c_center",
                active_cal_c_to_b=fit.VALIDATED_CAL_C_TO_B,
                min_line=start,
                max_line=end,
                exclude_lines=EXCLUDED_LINES,
            )
        )
    return observations


def same_c_reference_errors(rows: list[DataRow]) -> list[tuple[float, np.ndarray, DataRow]]:
    refs: dict[tuple[str, int], np.ndarray] = {}
    for block in {row.block for row in rows}:
        for c_deg in {round(row.c_deg) for row in rows if row.block == block}:
            points = [
                row.center
                for row in rows
                if row.block == block and abs(row.b_deg) < 1e-6 and round(row.c_deg) == c_deg
            ]
            if points:
                refs[(block, c_deg)] = np.mean(np.array(points), axis=0)

    supplement_c0 = refs.get(("supplement", 0))
    continuation_c0 = refs.get(("continuation", 0))
    continuation_shift = (
        continuation_c0 - supplement_c0
        if supplement_c0 is not None and continuation_c0 is not None
        else np.zeros(3)
    )

    errors: list[tuple[float, np.ndarray, DataRow]] = []
    for row in rows:
        if abs(row.b_deg) < 1e-6:
            continue
        c_key = round(row.c_deg)
        ref = refs.get((row.block, c_key))
        if ref is None and row.block == "continuation":
            ref = refs.get(("supplement", c_key))
            if ref is not None:
                ref = ref + continuation_shift
        if ref is None:
            continue
        delta = row.center - ref
        errors.append((float(np.linalg.norm(delta)), delta, row))
    return sorted(errors, key=lambda item: item[0], reverse=True)


def group_residual_rows(
    observations: list[fit.Observation],
    params: dict[str, float],
) -> list[tuple[float, np.ndarray, fit.Observation]]:
    residuals = fit.residual_matrix(observations, params)
    rows = [
        (float(np.linalg.norm(residual)), residual, obs)
        for residual, obs in zip(residuals, observations)
    ]
    return sorted(rows, key=lambda item: item[0], reverse=True)


def data_residual_rows(
    rows: list[DataRow],
    residuals: np.ndarray,
) -> list[tuple[float, np.ndarray, DataRow]]:
    output = [
        (float(np.linalg.norm(residual)), residual, row)
        for residual, row in zip(residuals, rows)
    ]
    return sorted(output, key=lambda item: item[0], reverse=True)


def full_basis_terms(b_deg: float, c_deg: float) -> tuple[list[str], np.ndarray]:
    b_rad = math.radians(b_deg + fit.BASE_B_ZERO_DEG)
    c_rad = math.radians(c_deg + fit.BASE_C_ZERO_DEG)
    c_ref_rad = math.radians(fit.BASE_C_ZERO_DEG)
    sin_b = math.sin(b_rad)
    omc_b = 1.0 - math.cos(b_rad)
    sin_c = math.sin(c_rad)
    cos_c = math.cos(c_rad)
    terms = [
        ("c_cos", cos_c - math.cos(c_ref_rad)),
        ("c_sin", sin_c - math.sin(c_ref_rad)),
        ("c_cos2", math.cos(2.0 * c_rad) - math.cos(2.0 * c_ref_rad)),
        ("c_sin2", math.sin(2.0 * c_rad) - math.sin(2.0 * c_ref_rad)),
        ("sinb", sin_b),
        ("omcb", omc_b),
        ("sin2b", math.sin(2.0 * b_rad)),
        ("sinb_cosc", sin_b * cos_c),
        ("sinb_sinc", sin_b * sin_c),
        ("omcb_sin2c", omc_b * sin_c * sin_c),
        ("sinb_sin2c", sin_b * math.sin(2.0 * c_rad)),
        ("sinb_cos2c", sin_b * math.cos(2.0 * c_rad)),
        ("omcb_cosc", omc_b * cos_c),
        ("omcb_sinc", omc_b * sin_c),
    ]
    return [name for name, _value in terms], np.array([value for _name, value in terms])


def named_basis(term_names: list[str]) -> Callable[[float, float], tuple[list[str], np.ndarray]]:
    def basis(b_deg: float, c_deg: float) -> tuple[list[str], np.ndarray]:
        names, terms = full_basis_terms(b_deg, c_deg)
        indexes = [names.index(name) for name in term_names]
        return [names[index] for index in indexes], terms[indexes]

    return basis


def extended_basis(b_deg: float, c_deg: float) -> tuple[list[str], np.ndarray]:
    return named_basis(SELECTED_EXTENDED_TERMS)(b_deg, c_deg)


def linear_basis_fit(
    rows: list[DataRow],
    basis_fn: Callable[[float, float], tuple[list[str], np.ndarray]] = extended_basis,
) -> tuple[list[str], np.ndarray, np.ndarray, float]:
    names, _ = basis_fn(rows[0].b_deg, rows[0].c_deg)
    groups = sorted({row.block for row in rows})
    group_indexes = {group: index for index, group in enumerate(groups)}
    coeff_count = len(names) * 3
    group_count = len(groups) * 3
    matrix = []
    values = []

    for data_row in rows:
        _names, terms = basis_fn(data_row.b_deg, data_row.c_deg)
        for axis in range(3):
            row = np.zeros(coeff_count + group_count)
            for term_index, term_value in enumerate(terms):
                row[(term_index * 3) + axis] = term_value
            row[coeff_count + (group_indexes[data_row.block] * 3) + axis] = 1.0
            matrix.append(row)
            values.append(data_row.center[axis])

    a = np.array(matrix)
    y = np.array(values)
    solution = np.linalg.lstsq(a, y, rcond=None)[0]
    coeffs = solution[:coeff_count].reshape((len(names), 3))
    group_offsets = solution[coeff_count:].reshape((len(groups), 3))

    residuals = []
    for data_row in rows:
        _names, terms = basis_fn(data_row.b_deg, data_row.c_deg)
        modeled = np.sum(coeffs * terms[:, None], axis=0)
        modeled += group_offsets[group_indexes[data_row.block]]
        residuals.append(data_row.center - modeled)

    singular_values = np.linalg.svd(a[:, :coeff_count], compute_uv=False)
    condition = (
        float(singular_values[0] / singular_values[-1])
        if singular_values[-1] > 1e-12
        else float("inf")
    )
    return names, -coeffs, np.array(residuals), condition


def model_comparison(observations: list[fit.Observation]) -> list[tuple[str, str, int, str, fit.FitResult]]:
    output = []
    for name in MODEL_NAMES:
        result = fit.fit_model(name, observations, fit.FIXED_C_CENTER)
        residuals = fit.residual_matrix(observations, result.params)
        rank, condition = fit.jacobian_condition(result.result)
        condition_text = "n/a" if math.isnan(condition) else f"{condition:.2e}"
        output.append((name, metric_text_from_residuals(residuals), rank, condition_text, result))
    return output


def extended_pin_name(term: str, axis: str) -> str:
    c_terms = {
        "c_cos": "charm.cos",
        "c_sin": "charm.sin",
        "c_cos2": "charm.cos2",
        "c_sin2": "charm.sin2",
    }
    b_terms = {
        "sinb": "bharm-m.sin",
        "omcb": "bharm-m.omc",
        "sin2b": "bharm-m.sin2",
    }
    bcross_terms = {
        "sinb_cosc": "bcross.sinb-cosc",
        "sinb_sinc": "bcross.sinb-sinc",
        "omcb_sin2c": "bcross.omcb-sin2c",
        "sinb_sin2c": "bcross.sinb-sin2c",
        "sinb_cos2c": "bcross.sinb-cos2c",
        "omcb_cosc": "bcross.omcb-cosc",
        "omcb_sinc": "bcross.omcb-sinc",
    }
    if term in c_terms:
        return f"{c_terms[term]}.{axis}"
    if term in b_terms:
        return f"{b_terms[term]}.{axis}"
    return f"{bcross_terms[term]}.{axis}"


def extended_variant_summary(rows: list[DataRow]) -> list[str]:
    variants = [
        (
            "existing B/B-C surface recreated",
            BASE_EXTENDED_TERMS,
        ),
        (
            "existing plus `c_sin` only",
            BASE_EXTENDED_TERMS + ["c_sin"],
        ),
        (
            "existing plus C first harmonic",
            BASE_EXTENDED_TERMS + ["c_cos", "c_sin"],
        ),
        (
            "selected C harmonics plus true sinB/C2",
            SELECTED_EXTENDED_TERMS,
        ),
        (
            "selected without `c_sin2`",
            [name for name in SELECTED_EXTENDED_TERMS if name != "c_sin2"],
        ),
    ]
    lines = [
        "| variant | terms | residual RMS/max mm | condition |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, term_names in variants:
        names, _coeffs, residuals, condition = linear_basis_fit(rows, named_basis(term_names))
        condition_text = "inf" if math.isinf(condition) else f"{condition:.2e}"
        lines.append(
            f"| {label} | {len(names)} | `{metric_text_from_residuals(residuals)}` | {condition_text} |"
        )
    return lines


def holdout_summary(rows: list[DataRow]) -> list[str]:
    lines = [
        "| holdout | train rows | test rows | extended implementable train RMS/max | extended implementable test RMS/max |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    holdouts = [
        ("mode9 block", lambda row: row.block == "mode9"),
        ("supplement block", lambda row: row.block == "supplement"),
        ("C90/C270", lambda row: round(row.c_deg) in (90, 270)),
        ("B-90", lambda row: round(row.b_deg) == -90),
    ]
    for label, predicate in holdouts:
        train = [row for row in rows if not predicate(row)]
        test = [row for row in rows if predicate(row)]
        if not train or not test:
            continue
        names, coeffs, train_residuals, _condition = linear_basis_fit(train)
        test_residuals = evaluate_linear_basis(rows=test, names=names, coeffs=coeffs)
        lines.append(
            f"| {label} | {len(train)} | {len(test)} | "
            f"{metric_text_from_residuals(train_residuals)} | "
            f"{metric_text_from_residuals(test_residuals)} |"
        )
    return lines


def evaluate_linear_basis(rows: list[DataRow], names: list[str], coeffs: np.ndarray) -> np.ndarray:
    # Fit only a constant center per held-out block, with the harmonic candidate fixed.
    model_coeffs = -coeffs
    residuals = []
    for block in sorted({row.block for row in rows}):
        block_rows = [row for row in rows if row.block == block]
        harmonic_points = []
        for row in block_rows:
            _basis_names, terms = extended_basis(row.b_deg, row.c_deg)
            harmonic_points.append(np.sum(model_coeffs * terms[:, None], axis=0))
        offset = np.mean(
            np.array([row.center for row in block_rows]) - np.array(harmonic_points),
            axis=0,
        )
        for row, harmonic in zip(block_rows, harmonic_points):
            residuals.append(row.center - (harmonic + offset))
    return np.array(residuals)


def write_report() -> None:
    rows = read_rows()
    observations = read_observations()
    current_params = fit.as_params([], np.array([]), fit.FIXED_C_CENTER)
    current_group_rows = group_residual_rows(observations, current_params)
    same_c_rows = same_c_reference_errors(rows)
    comparison = model_comparison(observations)
    comparison_by_name = {name: result for name, _metric, _rank, _cond, result in comparison}
    extended_names, extended_coeffs, extended_residuals, extended_condition = linear_basis_fit(rows)
    extended_rows = data_residual_rows(rows, extended_residuals)

    best_existing = comparison_by_name["b_harmonic_machine_bcross_no_cxy"]
    best_existing_rows = group_residual_rows(observations, best_existing.params)

    max_err_u = max(abs(row.err_u) for row in rows)
    max_err_v = max(abs(row.err_v) for row in rows)
    min_diam = min(min(row.diam_u, row.diam_v) for row in rows)
    max_diam = max(max(row.diam_u, row.diam_v) for row in rows)

    lines = [
        "# TCPC Short-Probe Current Fit Report",
        "",
        "Generated by `tcpc_short_probe_current_fit.py`.",
        "",
        "## Data Selection",
        "",
        f"- source CSV: `{RESULTS_PATH.name}`",
        "- selected accepted pass-2 rows: `273-394` and `396-407`",
        "- excluded failed probe row: `395` (`B-60 C0 pass 1`, bad U diameter)",
        f"- accepted pass-2 points used: `{len(rows)}`",
        f"- max accepted pass-2 centering residuals: U `{max_err_u:.6f} mm`, V `{max_err_v:.6f} mm`",
        f"- accepted corrected diameter range: `{min_diam:.6f}` to `{max_diam:.6f} mm`",
        "- temperature note for this run: `32 C` room/machine reference",
        "",
        "## Raw Error Vectors From Same-C B0 References",
        "",
        "The vectors below compare each nonzero-B pose to a B0 reference at the",
        "same C angle where one exists. For the B-30 continuation C90/C270 rows,",
        "the supplement B0 C90/C270 references are translated by the continuation",
        "B0 C0 opening/closing shift.",
        "",
        "| line | block | pose | dX mm | dY mm | dZ mm | magnitude mm |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for norm, delta, row in same_c_rows[:20]:
        lines.append(
            f"| {row.line} | {row.block} | `{row.pose}` | "
            f"{delta[0]:+.6f} | {delta[1]:+.6f} | {delta[2]:+.6f} | {norm:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Current-Kinematics Problem Areas",
            "",
            "This view removes only a constant sphere center per program block. It is",
            "the current-error field before fitting candidate corrections.",
            "",
            f"- current residual RMS/max: `{fit.metrics(observations, current_params)['rms3']:.6f} / "
            f"{fit.metrics(observations, current_params)['max3']:.6f} mm`",
            "",
            "| line | block | pose | dX mm | dY mm | dZ mm | magnitude mm |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for norm, residual, obs in current_group_rows[:20]:
        lines.append(
            f"| {obs.line} | {obs.group} | `B{obs.b_deg:+.0f} C{obs.c_deg:.0f}` | "
            f"{residual[0]:+.6f} | {residual[1]:+.6f} | {residual[2]:+.6f} | {norm:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Candidate Model Comparison",
            "",
            "Metrics are residual RMS/max after removing a constant sphere center per",
            "program block. Current C-center is fixed unless the model name states",
            "otherwise.",
            "",
            "| model | residual RMS/max mm | rank | condition |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for name, metric_text, rank, condition_text, _result in comparison:
        lines.append(f"| `{name}` | `{metric_text}` | {rank} | {condition_text} |")
    lines.append(
        f"| `extended_implementable_surface` | `{metric_text_from_residuals(extended_residuals)}` | "
        f"{len(extended_names) * 3} | {extended_condition:.2e} |"
    )

    lines.extend(
        [
            "",
            "## Extended Surface Variants",
            "",
            "The selected surface avoids the redundant `omcb_cos2c` term. It adds C-only",
            "harmonics that are relative to commanded C0, plus two true `sinB` cross",
            "terms on top of the currently implemented B/B-C surface.",
            "",
            *extended_variant_summary(rows),
        ]
    )

    lines.extend(
        [
            "",
            "## Existing-Pin Best Fit Residuals",
            "",
            "The best currently implemented pin family is the simulation-gated",
            "`b_harmonic_machine_bcross_no_cxy` fit. It helps, but leaves several",
            "points over the preferred `0.2 mm` target.",
            "",
            "| line | block | pose | dX mm | dY mm | dZ mm | magnitude mm |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for norm, residual, obs in best_existing_rows[:15]:
        lines.append(
            f"| {obs.line} | {obs.group} | `B{obs.b_deg:+.0f} C{obs.c_deg:.0f}` | "
            f"{residual[0]:+.6f} | {residual[1]:+.6f} | {residual[2]:+.6f} | {norm:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Selected Extended Residuals",
            "",
            "These are the remaining fitted error vectors for the selected implementable",
            "surface, after removing the per-block sphere center.",
            "",
            "| line | block | pose | dX mm | dY mm | dZ mm | magnitude mm |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for norm, residual, row in extended_rows[:15]:
        lines.append(
            f"| {row.line} | {row.block} | `{row.pose}` | "
            f"{residual[0]:+.6f} | {residual[1]:+.6f} | {residual[2]:+.6f} | {norm:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Extended Surface Holdouts",
            "",
            "The extended surface fits the measured grid well, but holdout tests show",
            "it should be validated on the machine before trusting it outside this",
            "exact B/C coverage. The mode9 holdout is intentionally weak because",
            "the remaining train rows do not contain enough C45/C180/C225 support;",
            "treat that row as an extrapolation warning, not as a useful prediction.",
            "",
            *holdout_summary(rows),
            "",
            "## Existing-Pin Candidate Parameters",
            "",
            "These values map to pins that already exist in `headheadkins`, gated by",
            "`headheadkins.sim-bharm-enable`. They are not recommended as a final",
            "candidate because the max residual remains about `0.246 mm`.",
            "",
            "```hal",
            "setp headheadkins.sim-bharm-enable 0",
        ]
    )
    for name in fit.B_HARMONIC_MACHINE_PARAMS + fit.B_CROSS_MACHINE_PARAMS:
        value = best_existing.params[name]
        if name.startswith("mb_"):
            _, term_a, term_b, axis = name.split("_")
            term_key = f"{term_a}_{term_b}"
            term_pin = {"sin_b": "sin", "omc_b": "omc", "sin_2b": "sin2"}[term_key]
            pin = f"bharm-m.{term_pin}.{axis}"
        else:
            term_axis = name.removeprefix("bc_")
            term_key, axis = term_axis.rsplit("_", 1)
            term_pin = term_key.replace("_", "-")
            pin = f"bcross.{term_pin}.{axis}"
        lines.append(f"setp headheadkins.{pin} {value:.9f}")
    lines.extend(["# setp headheadkins.sim-bharm-enable 1", "```"])

    lines.extend(
        [
            "",
            "## Extended Surface Correction Coefficients",
            "",
            "The signs below are correction signs: they are the values that would be",
            "added to the kinematic offset surface. The C-only terms are evaluated as",
            "deltas from commanded C0 so B0/C0 is unchanged. The existing",
            "`bcross.omcb-sin2c.*` pin is `(1-cosB)*sin(C)^2`; true `sin(2C)`",
            "support would be a separate new term.",
            "",
            "| term | X coeff | Y coeff | Z coeff | current pin support |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    supported = {
        "c_cos": "new `charm.cos.*`",
        "c_sin": "new `charm.sin.*`",
        "c_cos2": "new `charm.cos2.*`",
        "c_sin2": "new `charm.sin2.*`",
        "sinb": "existing `bharm-m.sin.*`",
        "omcb": "existing `bharm-m.omc.*`",
        "sin2b": "existing `bharm-m.sin2.*`",
        "sinb_sinc": "existing `bcross.sinb-sinc.*`",
        "omcb_sinc": "existing `bcross.omcb-sinc.*`",
        "omcb_sin2c": "existing `bcross.omcb-sin2c.*` (`sin(C)^2`)",
        "sinb_cosc": "existing `bcross.sinb-cosc.*`",
        "omcb_cosc": "existing `bcross.omcb-cosc.*`",
        "sinb_sin2c": "new `bcross.sinb-sin2c.*`",
        "sinb_cos2c": "new `bcross.sinb-cos2c.*`",
    }
    for name, coeff in zip(extended_names, extended_coeffs):
        lines.append(
            f"| `{name}` | {coeff[0]:+.9f} | {coeff[1]:+.9f} | {coeff[2]:+.9f} | "
            f"{supported.get(name, 'new term needed')} |"
        )

    lines.extend(
        [
            "",
            "## Selected Extended Candidate Parameters",
            "",
            "This block uses the selected nonredundant surface. It requires the new",
            "`charm.*`, `bcross.sinb-sin2c.*`, and `bcross.sinb-cos2c.*` pins before",
            "it can be loaded.",
            "",
            "```hal",
            "setp headheadkins.sim-bharm-enable 0",
        ]
    )
    for name, coeff in zip(extended_names, extended_coeffs):
        for axis, value in zip(AXIS_NAMES, coeff):
            lines.append(f"setp headheadkins.{extended_pin_name(name, axis)} {value:.9f}")
    lines.extend(["# setp headheadkins.sim-bharm-enable 1", "```"])

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The largest current errors are strongly B/C dependent, not random probe",
            "  noise in the accepted rows.",
            "- The most severe raw vectors are at negative high B, especially",
            "  `B-90 C90`, `B-90 C45`, `B-90 C0`, and `B-90 C180`.",
            "- Existing rigid geometry pins cannot explain the full surface; the best",
            "  rigid/axis-vector fit remains above `0.34 mm` max and is poorly",
            "  conditioned.",
            "- Existing B-harmonic plus B/C cross pins are directionally useful but not",
            "  enough for the whole short-probe grid.",
            "- A richer harmonic surface can get the measured grid under the preferred",
            "  `0.2 mm` target offline, but it needs code support and live validation.",
            "- The current short-probe-only data cannot separate true tool-length",
            "  dependency from B-axis center/tilt terms. A long-probe repeat remains",
            "  necessary before promoting any correction to production use.",
            "",
            "## Next Work",
            "",
            "1. Add the missing extended surface pins with zero defaults and keep them",
            "   gated off by `sim-bharm-enable`.",
            "2. Verify unchanged behavior when the gate is off.",
            "3. Verify the extended surface math in simulation.",
            "4. Prepare one short live validation of the extended candidate on the same",
            "   B/C coverage, then compare against this report.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    write_report()
    print(f"wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
