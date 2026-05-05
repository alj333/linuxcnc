#!/usr/bin/env python3
"""Review whether the refined TCPC candidate should be frozen or retuned."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

import tcpc_expanded_geometry_fit as fit


REPORT_PATH = Path(__file__).with_name("TCPC_REFINED_PERSISTENCE_REVIEW.md")


@dataclass(frozen=True)
class ReviewSet:
    label: str
    data_sets: list[list[fit.Observation]]


def rms_max(norms: list[float] | np.ndarray) -> tuple[float, float]:
    values = np.array(norms, dtype=float)
    return (float(math.sqrt(np.mean(values**2))), float(np.max(values)))


def metric_text(data_sets: list[list[fit.Observation]], params: dict[str, float]) -> str:
    norms = []
    for observations in data_sets:
        _, rows = fit.b_angle_delta_rows(observations, params)
        norms.extend(float(np.linalg.norm(delta)) for _, delta in rows)
    rms, max_value = rms_max(norms)
    return f"`{rms:.6f} / {max_value:.6f} mm`"


def rows_for(
    data_sets: list[list[fit.Observation]],
    params: dict[str, float],
) -> list[tuple[fit.Observation, np.ndarray]]:
    rows: list[tuple[fit.Observation, np.ndarray]] = []
    for observations in data_sets:
        _, data_rows = fit.b_angle_delta_rows(observations, params)
        rows.extend(data_rows)
    return rows


def term_values(b_deg: float, c_deg: float, family: str) -> list[float]:
    b_rad = math.radians(b_deg)
    c_rad = math.radians(c_deg + fit.BASE_C_ZERO_DEG)
    omc = 1.0 - math.cos(b_rad)
    sin2b = math.sin(2.0 * b_rad)
    sinb2 = math.sin(b_rad) * math.sin(b_rad)
    sin_c = math.sin(c_rad)
    cos_c = math.cos(c_rad)

    if family == "sin2_cross":
        return [sin2b * cos_c, sin2b * sin_c]
    if family == "sin2_even_cross":
        return [
            sin2b * cos_c,
            sin2b * sin_c,
            sinb2 * cos_c,
            sinb2 * sin_c,
            sinb2 * sin_c * sin_c,
        ]
    if family == "omcb2_cross":
        omc2 = omc * omc
        return [omc2, omc2 * cos_c, omc2 * sin_c, omc2 * sin_c * sin_c]
    if family == "sin2_plus_omcb2_cross":
        omc2 = omc * omc
        return [
            sin2b * cos_c,
            sin2b * sin_c,
            omc2,
            omc2 * cos_c,
            omc2 * sin_c,
            omc2 * sin_c * sin_c,
        ]
    raise ValueError(f"unknown family {family}")


def fit_extension(
    train_sets: list[list[fit.Observation]],
    family: str,
    base_params: dict[str, float],
) -> np.ndarray:
    rows = rows_for(train_sets, base_params)
    term_count = len(term_values(rows[0][0].b_deg, rows[0][0].c_deg, family))

    def residual(values: np.ndarray) -> np.ndarray:
        out = []
        for obs, delta in rows:
            correction = np.zeros(3)
            for term_index, value in enumerate(term_values(obs.b_deg, obs.c_deg, family)):
                start = term_index * 3
                correction += value * values[start : start + 3]
            out.extend(delta + correction)
        return np.array(out)

    result = least_squares(
        residual,
        np.zeros(term_count * 3),
        bounds=(-0.5, 0.5),
        x_scale="jac",
        max_nfev=20000,
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
    )
    return result.x


def extension_metric(
    data_sets: list[list[fit.Observation]],
    family: str,
    values: np.ndarray,
    base_params: dict[str, float],
) -> str:
    norms = []
    for obs, delta in rows_for(data_sets, base_params):
        correction = np.zeros(3)
        for term_index, value in enumerate(term_values(obs.b_deg, obs.c_deg, family)):
            start = term_index * 3
            correction += value * values[start : start + 3]
        norms.append(float(np.linalg.norm(delta + correction)))
    rms, max_value = rms_max(norms)
    return f"`{rms:.6f} / {max_value:.6f} mm`"


def load_review_sets() -> list[ReviewSet]:
    data = fit.load_data()
    return [
        ReviewSet("old B-harmonic-only live rows", [*data[5:8]]),
        ReviewSet("B/C cross live rows", [*data[8:11]]),
        ReviewSet("refined live rows", [*data[11:14]]),
    ]


def write_report(path: Path) -> None:
    review_sets = load_review_sets()
    all_live_sets = [data_set for review_set in review_sets for data_set in review_set.data_sets]
    current_params = fit.as_params(
        [],
        np.array([]),
        {
            **fit.FIXED_C_CENTER,
            **fit.REFINED_BCROSS_CANDIDATE,
        },
    )
    post_refined = fit.fit_direct_model(
        "b_harmonic_machine_bcross_no_cxy",
        all_live_sets,
        fit.FIXED_C_CENTER,
    )

    param_names = fit.B_HARMONIC_MACHINE_PARAMS + fit.B_CROSS_MACHINE_PARAMS
    current_vector = np.array([current_params[name] for name in param_names])

    leave_one_rows = []
    for holdout in review_sets:
        train_sets = [
            data_set
            for review_set in review_sets
            if review_set is not holdout
            for data_set in review_set.data_sets
        ]
        result = fit.fit_direct_model(
            "b_harmonic_machine_bcross_no_cxy",
            train_sets,
            fit.FIXED_C_CENTER,
        )
        result_vector = np.array([result.params[name] for name in param_names])
        leave_one_rows.append(
            "| "
            f"{holdout.label} | "
            f"{metric_text(holdout.data_sets, result.params)} | "
            f"{metric_text(all_live_sets, result.params)} | "
            f"`{np.max(np.abs(result_vector - current_vector)):.6f}` |"
        )

    pose_rows = []
    by_pose: dict[tuple[int, int], list[tuple[str, np.ndarray]]] = {}
    for review_set in review_sets:
        for obs, delta in rows_for(review_set.data_sets, current_params):
            key = (round(obs.b_deg), round(obs.c_deg))
            by_pose.setdefault(key, []).append((review_set.label, delta))
    for key, values in by_pose.items():
        vectors = np.array([delta for _, delta in values])
        norms = np.linalg.norm(vectors, axis=1)
        pose_rows.append(
            (
                float(np.max(norms)),
                "| "
                f"`B{key[0]:+} C{key[1]}` | "
                f"{len(values)} | "
                f"`{np.mean(norms):.6f}` | "
                f"`{np.max(norms):.6f}` | "
                f"`{np.std(vectors[:, 0]):.6f}` | "
                f"`{np.std(vectors[:, 1]):.6f}` | "
                f"`{np.std(vectors[:, 2]):.6f}` |"
            )
        )
    pose_rows.sort(reverse=True)

    extension_rows = []
    for family, label in [
        ("sin2_cross", "`sin(2B)` C-cross"),
        ("sin2_even_cross", "`sin(2B)` plus `sin(B)^2` C-cross"),
        ("omcb2_cross", "`(1-cos(B))^2` C-cross"),
        ("sin2_plus_omcb2_cross", "`sin(2B)` plus `(1-cos(B))^2` C-cross"),
    ]:
        values = fit_extension(all_live_sets, family, current_params)
        extension_rows.append(
            "| "
            f"{label} | "
            f"{extension_metric(all_live_sets, family, values, current_params)} | "
            f"`{np.max(np.abs(values)):.6f}` |"
        )

    lines = [
        "# TCPC Refined Candidate Persistence Review",
        "",
        "Generated by `tcpc_refined_persistence_review.py`.",
        "",
        "## Candidate State",
        "",
        "The live-tested refined B/C cross candidate remains the current candidate.",
        "It is still non-persistent and should stay behind the manual diagnostic",
        "enable until the operator accepts the persistence decision.",
        "",
        "| evaluation | non-B0 RMS/max |",
        "| --- | ---: |",
        f"| current refined candidate on old live rows | {metric_text(review_sets[0].data_sets, current_params)} |",
        f"| current refined candidate on B/C-cross live rows | {metric_text(review_sets[1].data_sets, current_params)} |",
        f"| current refined candidate on refined live rows | {metric_text(review_sets[2].data_sets, current_params)} |",
        f"| current refined candidate on all live rows | {metric_text(all_live_sets, current_params)} |",
        f"| post-refined all-live retune on all live rows | {metric_text(all_live_sets, post_refined.params)} |",
        "",
        "The all-live retune lowers combined RMS by less than `0.001 mm` and raises",
        "maximum error from `0.133632 mm` to `0.136366 mm`. That is not enough",
        "improvement to replace the live-tested refined candidate.",
        "",
        "## Leave-One-Live-State-Out Check",
        "",
        "| held-out set | held-out RMS/max | all-live RMS/max | max coefficient change |",
        "| --- | ---: | ---: | ---: |",
        *leave_one_rows,
        "",
        "The fitted coefficients stay close when any one live state is held out,",
        "and no held-out result beats the current refined candidate by enough to",
        "justify another full validation run.",
        "",
        "## Remaining Pose Pattern",
        "",
        "The table evaluates all live rows as if the current refined candidate were",
        "active. The largest remaining errors are concentrated at C180 high-B poses.",
        "",
        "| pose | samples | mean norm | max norm | std X | std Y | std Z |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[row for _, row in pose_rows[:8]],
        "",
        "The C180 high-B residual repeats across independent live states. Treat it as",
        "a real remaining model error, not a probe-quality fault.",
        "",
        "## Experimental Extra Terms",
        "",
        "These terms were checked offline only. They are not implemented in",
        "`headheadkins` and should not be added unless a larger improvement appears",
        "after a targeted repeat.",
        "",
        "| extra family | all-live RMS/max after extra fit | max coefficient |",
        "| --- | ---: | ---: |",
        *extension_rows,
        "",
        "The best experimental family improves RMS by about `0.003 mm` and does not",
        "materially reduce maximum error. Adding another kinematics correction family",
        "is not justified from this data alone.",
        "",
        "## Decision",
        "",
        "- Keep the refined candidate unchanged.",
        "- Do not promote it to persistent startup HAL yet.",
        "- Do not run another full `#711 = 4.0` validation.",
        "- If another machine run is needed, use the targeted repeat mode",
        "  `#711 = 5.0` in `tcpc_b_angle_scaling_diagnostic.ngc`.",
        "- Targeted mode repeats C180 high-B and C270 B+90 only, with B0 open/close",
        "  references for each C group.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    write_report(args.report)
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
