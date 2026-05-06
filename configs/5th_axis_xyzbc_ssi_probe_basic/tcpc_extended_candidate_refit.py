#!/usr/bin/env python3
"""Refit the validated short-probe extended TCPC candidate residuals.

This script is intentionally diagnostic. It starts from the candidate-on
validation rows and asks whether a second, small correction can reduce the
remaining same-C B0-relative error field toward 0.1 mm.
"""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


CONFIG_DIR = Path(__file__).resolve().parent
RESULTS_PATH = CONFIG_DIR / "tcpc-b-angle-scaling-diagnostic-2pass-results.csv"
REPORT_PATH = CONFIG_DIR / "TCPC_EXTENDED_CANDIDATE_REFIT_REPORT.md"

BASE_B_ZERO_DEG = 0.0
BASE_C_ZERO_DEG = -0.024500
AXES = ["x", "y", "z"]

SEGMENTS = [
    ("first", 409, 471),
    ("resume", 473, 529),
]

CURRENT_CANDIDATE = {
    "c_cos": np.array([-0.131593800, -0.007562306, 0.016558764]),
    "c_sin": np.array([-0.004929903, -0.124613220, 0.006528345]),
    "c_cos2": np.array([-0.011171047, 0.018637150, 0.010762855]),
    "c_sin2": np.array([0.016179345, -0.013748585, -0.001209434]),
    "sinb": np.array([0.017924948, 0.058126845, 0.392280490]),
    "omcb": np.array([0.097308591, 0.081476614, -0.344419137]),
    "sin2b": np.array([0.004105061, 0.005536233, -0.150507227]),
    "sinb_cosc": np.array([-0.052968194, -0.071049371, -0.015714834]),
    "sinb_sinc": np.array([-0.009597862, 0.260181317, 0.118497105]),
    "omcb_sin2c": np.array([0.005037623, -0.221178842, -0.041979701]),
    "omcb_cosc": np.array([0.099996873, 0.082895840, 0.000822785]),
    "omcb_sinc": np.array([-0.050693113, 0.097446530, -0.003005566]),
    "sinb_sin2c": np.array([-0.049640417, -0.035604022, -0.012113361]),
    "sinb_cos2c": np.array([-0.021909475, 0.064078633, -0.002501793]),
}

CURRENT_TERMS = [
    "sinb",
    "omcb",
    "sin2b",
    "sinb_cosc",
    "sinb_sinc",
    "omcb_sin2c",
    "omcb_cosc",
    "omcb_sinc",
    "sinb_sin2c",
    "sinb_cos2c",
]

MIDB_TERMS = [
    "midb",
    "midb_cosc",
    "midb_sinc",
    "midb_cos2c",
    "midb_sin2c",
]

PIN_BY_TERM = {
    "c_cos": "charm.cos",
    "c_sin": "charm.sin",
    "c_cos2": "charm.cos2",
    "c_sin2": "charm.sin2",
    "sinb": "bharm-m.sin",
    "omcb": "bharm-m.omc",
    "sin2b": "bharm-m.sin2",
    "sinb_cosc": "bcross.sinb-cosc",
    "sinb_sinc": "bcross.sinb-sinc",
    "omcb_sin2c": "bcross.omcb-sin2c",
    "omcb_cosc": "bcross.omcb-cosc",
    "omcb_sinc": "bcross.omcb-sinc",
    "sinb_sin2c": "bcross.sinb-sin2c",
    "sinb_cos2c": "bcross.sinb-cos2c",
    "midb": "bmid.base",
    "midb_cosc": "bmid.cosc",
    "midb_sinc": "bmid.sinc",
    "midb_cos2c": "bmid.cos2c",
    "midb_sin2c": "bmid.sin2c",
}


@dataclass(frozen=True)
class DataRow:
    line: int
    segment: str
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


@dataclass(frozen=True)
class ResidualRow:
    row: DataRow
    residual: np.ndarray

    @property
    def magnitude(self) -> float:
        return float(np.linalg.norm(self.residual))


@dataclass(frozen=True)
class Fit:
    label: str
    terms: list[str]
    coeffs: np.ndarray
    residuals: np.ndarray
    rank: int
    condition: float
    ridge: float


def metric(residuals: np.ndarray) -> tuple[float, float]:
    norms = np.linalg.norm(residuals, axis=1)
    return float(math.sqrt(np.mean(norms**2))), float(np.max(norms))


def metric_text(residuals: np.ndarray) -> str:
    rms, max_value = metric(residuals)
    return f"{rms:.6f} / {max_value:.6f}"


def vec_text(vec: np.ndarray) -> str:
    return f"{vec[0]:+.6f}, {vec[1]:+.6f}, {vec[2]:+.6f}"


def read_rows() -> list[DataRow]:
    segment_by_line = {}
    for segment, start, end in SEGMENTS:
        for line in range(start, end + 1):
            segment_by_line[line] = segment

    rows: list[DataRow] = []
    with RESULTS_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for line, row in enumerate(reader, start=2):
            segment = segment_by_line.get(line)
            if segment is None:
                continue
            if float(row["pass_num"]) != 2.0 or float(row["accepted"]) != 1.0:
                continue
            rows.append(
                DataRow(
                    line=line,
                    segment=segment,
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


def reference_map(rows: list[DataRow]) -> dict[tuple[str, int], np.ndarray]:
    refs: dict[tuple[str, int], np.ndarray] = {}
    for segment in sorted({row.segment for row in rows}):
        for c_deg in sorted({round(row.c_deg) for row in rows if row.segment == segment}):
            points = [
                row.center
                for row in rows
                if row.segment == segment
                and abs(row.b_deg) < 1e-9
                and round(row.c_deg) == c_deg
            ]
            if points:
                refs[(segment, c_deg)] = np.mean(np.array(points), axis=0)
    return refs


def residual_rows(rows: list[DataRow]) -> list[ResidualRow]:
    refs = reference_map(rows)
    residuals: list[ResidualRow] = []
    for row in rows:
        if abs(row.b_deg) < 1e-9:
            continue
        ref = refs.get((row.segment, round(row.c_deg)))
        if ref is None:
            continue
        residuals.append(ResidualRow(row=row, residual=row.center - ref))
    return residuals


def basis_values(b_deg: float, c_deg: float) -> dict[str, float]:
    b_rad = math.radians(b_deg + BASE_B_ZERO_DEG)
    c_rad = math.radians(c_deg + BASE_C_ZERO_DEG)
    sinb = math.sin(b_rad)
    omcb = 1.0 - math.cos(b_rad)
    sin2b = math.sin(2.0 * b_rad)
    sin_c = math.sin(c_rad)
    cos_c = math.cos(c_rad)
    midb = sin2b * sin2b
    return {
        "sinb": sinb,
        "omcb": omcb,
        "sin2b": sin2b,
        "sinb_cosc": sinb * cos_c,
        "sinb_sinc": sinb * sin_c,
        "omcb_sin2c": omcb * sin_c * sin_c,
        "omcb_cosc": omcb * cos_c,
        "omcb_sinc": omcb * sin_c,
        "sinb_sin2c": sinb * math.sin(2.0 * c_rad),
        "sinb_cos2c": sinb * math.cos(2.0 * c_rad),
        "midb": midb,
        "midb_cosc": midb * cos_c,
        "midb_sinc": midb * sin_c,
        "midb_cos2c": midb * math.cos(2.0 * c_rad),
        "midb_sin2c": midb * math.sin(2.0 * c_rad),
    }


def design_matrix(rows: list[ResidualRow], terms: list[str]) -> np.ndarray:
    return np.array(
        [
            [basis_values(residual_row.row.b_deg, residual_row.row.c_deg)[term] for term in terms]
            for residual_row in rows
        ],
        dtype=float,
    )


def fit_delta(label: str, rows: list[ResidualRow], terms: list[str], ridge: float = 0.0) -> Fit:
    x = design_matrix(rows, terms)
    y = np.array([row.residual for row in rows], dtype=float)
    if ridge > 0.0:
        regularizer = math.sqrt(ridge) * np.eye(len(terms))
        x_solve = np.vstack([x, regularizer])
        y_solve = np.vstack([y * -1.0, np.zeros((len(terms), 3))])
        coeffs = np.linalg.lstsq(x_solve, y_solve, rcond=None)[0]
    else:
        coeffs = np.linalg.lstsq(x, -y, rcond=None)[0]
    residuals = y + (x @ coeffs)
    singular_values = np.linalg.svd(x, compute_uv=False)
    rank = int(np.linalg.matrix_rank(x))
    condition = (
        float(singular_values[0] / singular_values[-1])
        if singular_values.size and singular_values[-1] > 1e-12
        else float("inf")
    )
    return Fit(
        label=label,
        terms=terms,
        coeffs=coeffs,
        residuals=residuals,
        rank=rank,
        condition=condition,
        ridge=ridge,
    )


def evaluate(rows: list[ResidualRow], terms: list[str], coeffs: np.ndarray) -> np.ndarray:
    x = design_matrix(rows, terms)
    y = np.array([row.residual for row in rows], dtype=float)
    return y + (x @ coeffs)


def holdouts(rows: list[ResidualRow], terms: list[str]) -> list[tuple[str, int, int, str, str]]:
    checks: list[tuple[str, Callable[[ResidualRow], bool]]] = [
        ("first segment", lambda item: item.row.segment == "first"),
        ("resume segment", lambda item: item.row.segment == "resume"),
        ("B+60", lambda item: round(item.row.b_deg) == 60),
        ("B-60", lambda item: round(item.row.b_deg) == -60),
        ("B+90", lambda item: round(item.row.b_deg) == 90),
        ("B-90", lambda item: round(item.row.b_deg) == -90),
        ("C0", lambda item: round(item.row.c_deg) == 0),
        ("C45", lambda item: round(item.row.c_deg) == 45),
        ("C90", lambda item: round(item.row.c_deg) == 90),
        ("C180", lambda item: round(item.row.c_deg) == 180),
        ("C225", lambda item: round(item.row.c_deg) == 225),
        ("C270", lambda item: round(item.row.c_deg) == 270),
    ]
    output = []
    for label, predicate in checks:
        train = [row for row in rows if not predicate(row)]
        test = [row for row in rows if predicate(row)]
        if len(train) < len(terms) or not test:
            continue
        fit = fit_delta(label, train, terms)
        output.append(
            (
                label,
                len(train),
                len(test),
                metric_text(fit.residuals),
                metric_text(evaluate(test, terms, fit.coeffs)),
            )
        )
    return output


def grouped_metrics(rows: list[ResidualRow], residuals: np.ndarray) -> list[tuple[str, int, str]]:
    output = []
    groups: list[tuple[str, Callable[[ResidualRow], bool]]] = []
    for b_deg in sorted({round(row.row.b_deg) for row in rows}):
        groups.append((f"B{b_deg:+.0f}", lambda item, b=b_deg: round(item.row.b_deg) == b))
    for c_deg in sorted({round(row.row.c_deg) for row in rows}):
        groups.append((f"C{c_deg:.0f}", lambda item, c=c_deg: round(item.row.c_deg) == c))

    for label, predicate in groups:
        indexes = [index for index, row in enumerate(rows) if predicate(row)]
        output.append((label, len(indexes), metric_text(residuals[indexes])))
    return output


def rows_by_magnitude(rows: list[ResidualRow], residuals: np.ndarray) -> list[tuple[float, np.ndarray, DataRow]]:
    output = [
        (float(np.linalg.norm(residual)), residual, residual_row.row)
        for residual_row, residual in zip(rows, residuals)
    ]
    return sorted(output, key=lambda item: item[0], reverse=True)


def refined_coefficients(fit: Fit) -> dict[str, np.ndarray]:
    coeffs: dict[str, np.ndarray] = {term: value.copy() for term, value in CURRENT_CANDIDATE.items()}
    for term, delta in zip(fit.terms, fit.coeffs):
        if term in coeffs:
            coeffs[term] = coeffs[term] + delta
        else:
            coeffs[term] = delta.copy()
    for term in MIDB_TERMS:
        coeffs.setdefault(term, np.zeros(3))
    return coeffs


def hal_block(coeffs: dict[str, np.ndarray]) -> list[str]:
    lines = ["```hal", "setp headheadkins.sim-bharm-enable 0"]
    ordered_terms = [
        "c_cos",
        "c_sin",
        "c_cos2",
        "c_sin2",
        "sinb",
        "omcb",
        "sin2b",
        "sinb_cosc",
        "sinb_sinc",
        "omcb_sin2c",
        "omcb_cosc",
        "omcb_sinc",
        "sinb_sin2c",
        "sinb_cos2c",
        "midb",
        "midb_cosc",
        "midb_sinc",
        "midb_cos2c",
        "midb_sin2c",
    ]
    for term in ordered_terms:
        for axis, value in zip(AXES, coeffs[term]):
            lines.append(f"setp headheadkins.{PIN_BY_TERM[term]}.{axis} {value:.9f}")
    lines.extend(["# setp headheadkins.sim-bharm-enable 1", "```"])
    return lines


def write_report() -> None:
    data_rows = read_rows()
    residual_data = residual_rows(data_rows)
    baseline = np.array([row.residual for row in residual_data])

    variants = [
        fit_delta("selected current B/B-C delta only", residual_data, CURRENT_TERMS),
        fit_delta("mid-B envelope only", residual_data, MIDB_TERMS),
        fit_delta("current B/B-C delta plus mid-B envelope", residual_data, CURRENT_TERMS + MIDB_TERMS),
        fit_delta("mid-B base/cos/sin only", residual_data, ["midb", "midb_cosc", "midb_sinc"]),
        fit_delta(
            "current B/B-C plus mid-B, light ridge",
            residual_data,
            CURRENT_TERMS + MIDB_TERMS,
            ridge=0.01,
        ),
    ]
    selected = variants[2]
    selected_coeffs = refined_coefficients(selected)
    selected_rows = rows_by_magnitude(residual_data, selected.residuals)

    max_err_u = max(abs(row.err_u) for row in data_rows)
    max_err_v = max(abs(row.err_v) for row in data_rows)
    min_diam = min(min(row.diam_u, row.diam_v) for row in data_rows)
    max_diam = max(max(row.diam_u, row.diam_v) for row in data_rows)

    lines = [
        "# TCPC Extended Candidate Refit Report",
        "",
        "Generated by `tcpc_extended_candidate_refit.py` from the latest candidate-on",
        "validation rows.",
        "",
        "## Data Selection",
        "",
        f"- source CSV: `{RESULTS_PATH.name}`",
        "- accepted pass-2 rows: first segment `409-471`, resume segment `473-529`",
        f"- total accepted rows in selection: `{len(data_rows)}`",
        f"- nonzero-B rows compared to same-segment same-C B0 refs: `{len(residual_data)}`",
        f"- max accepted pass-2 centering residuals: U `{max_err_u:.6f} mm`, V `{max_err_v:.6f} mm`",
        f"- accepted corrected diameter range: `{min_diam:.6f}` to `{max_diam:.6f} mm`",
        "",
        "## Current Validated Residuals",
        "",
        "These are the remaining error vectors after the current extended candidate,",
        "computed against the B0 reference at the same C angle within the same run",
        "segment.",
        "",
        f"- current candidate residual RMS/max: `{metric_text(baseline)} mm`",
        "",
        "| line | segment | pose | dX mm | dY mm | dZ mm | magnitude mm |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for magnitude, residual, row in rows_by_magnitude(residual_data, baseline)[:15]:
        lines.append(
            f"| {row.line} | {row.segment} | `{row.pose}` | "
            f"{residual[0]:+.6f} | {residual[1]:+.6f} | {residual[2]:+.6f} | {magnitude:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Second-Correction Fits",
            "",
            "The fitted coefficients are correction-sign values added to the kinematic",
            "offset surface. The `mid-B` envelope is `sin(2B)^2`, so it is exactly zero",
            "at `B0` and `B+-90` and has its largest effect around `B+-45` to `B+-60`.",
            "",
            "| variant | terms | rank | condition | residual RMS/max mm |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    lines.append(f"| current candidate, no second correction | 0 | 0 | n/a | `{metric_text(baseline)}` |")
    for variant in variants:
        condition = "inf" if math.isinf(variant.condition) else f"{variant.condition:.2e}"
        ridge = "" if variant.ridge == 0.0 else f" ridge={variant.ridge:g}"
        lines.append(
            f"| {variant.label}{ridge} | {len(variant.terms)} | {variant.rank} | "
            f"{condition} | `{metric_text(variant.residuals)}` |"
        )

    lines.extend(
        [
            "",
            "## Selected Diagnostic Candidate Residuals",
            "",
            f"Selected offline fit: `{selected.label}`. It gets the completed validation",
            "grid just below the preferred 0.1 mm max target, but the holdouts below",
            "show that it is not yet proven outside this exact short-probe grid.",
            "",
            "| line | segment | pose | dX mm | dY mm | dZ mm | magnitude mm |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for magnitude, residual, row in selected_rows[:15]:
        lines.append(
            f"| {row.line} | {row.segment} | `{row.pose}` | "
            f"{residual[0]:+.6f} | {residual[1]:+.6f} | {residual[2]:+.6f} | {magnitude:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Group Metrics After Selected Diagnostic Candidate",
            "",
            "| group | rows | residual RMS/max mm |",
            "| --- | ---: | ---: |",
        ]
    )
    for label, count, text in grouped_metrics(residual_data, selected.residuals):
        lines.append(f"| {label} | {count} | `{text}` |")

    lines.extend(
        [
            "",
            "## Holdout Checks",
            "",
            "Each row fits the selected candidate family with one group removed, then",
            "tests on the removed group. These are the main reason not to treat the",
            "sub-0.1 mm result as confirmed yet.",
            "",
            "| holdout | train rows | test rows | train RMS/max mm | test RMS/max mm |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for label, train_count, test_count, train_text, test_text in holdouts(residual_data, selected.terms):
        lines.append(
            f"| {label} | {train_count} | {test_count} | `{train_text}` | `{test_text}` |"
        )

    lines.extend(
        [
            "",
            "## Selected Diagnostic Coefficients",
            "",
            "The table shows the total coefficient value to load, not just the delta.",
            "`charm.*` values are unchanged from the currently validated candidate",
            "because the same-C B0-relative residuals cannot identify C-only terms.",
            "",
            "| term | X coeff | Y coeff | Z coeff | pin |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for term in [
        "c_cos",
        "c_sin",
        "c_cos2",
        "c_sin2",
        *CURRENT_TERMS,
        *MIDB_TERMS,
    ]:
        value = selected_coeffs[term]
        lines.append(
            f"| `{term}` | {value[0]:+.9f} | {value[1]:+.9f} | {value[2]:+.9f} | "
            f"`headheadkins.{PIN_BY_TERM[term]}.*` |"
        )

    lines.extend(
        [
            "",
            "## HAL Block For Simulation/Diagnostic Loading",
            "",
            *hal_block(selected_coeffs),
            "",
            "## Interpretation",
            "",
            "- The current extended candidate is a credible first target solution:",
            "  combined RMS/max is under 0.1/0.2 mm on the full safe grid.",
            "- A sub-0.1 mm max is viable on the measured validation grid if we add the",
            "  mid-B envelope family. This targets the remaining B+-60 pattern without",
            "  moving B0 or B+-90.",
            "- The sub-0.1 result is not robust enough to promote. Segment and C-angle",
            "  holdouts still predict errors above 0.1 mm, which means the fit is using",
            "  details of this one short-probe run.",
            "- The next machine pass should therefore be a confirmation pass for this",
            "  diagnostic candidate, not a production calibration. If it repeats under",
            "  0.1 mm on a fresh run, the correction becomes much more credible.",
            "- A long stylus remains necessary before finalizing production TCPC values;",
            "  with one tool length we still cannot separate some tool-length-dependent",
            "  B-axis center/tilt effects from machine-fixed harmonic correction.",
            "",
            "## Next Confirmation Pass",
            "",
            "Run the same safe validation grid with the mid-B diagnostic candidate",
            "loaded and `sim-bharm-enable` turned on only for the program. Keep the",
            "opening and closing B0 C sweeps so each session can reference its own",
            "sphere center and thermal state. Before the run, set the loaded probe tool",
            "state back to tool 3 so the later short/long probe comparison is clean.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    write_report()
    print(f"wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
