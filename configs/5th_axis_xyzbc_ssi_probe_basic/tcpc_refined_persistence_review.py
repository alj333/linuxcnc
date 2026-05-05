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
RESULTS_PATH = Path(__file__).with_name("tcpc-b-angle-scaling-diagnostic-2pass-results.csv")
TARGETED_REPEATS = [
    (
        "targeted repeat 1",
        "2026-05-05-refined-targeted-repeat-1",
        [173, 175, 177, 179, 181, 183, 185, 187, 189],
    ),
    (
        "targeted repeat 2",
        "2026-05-05-refined-targeted-repeat-2",
        [191, 193, 195, 197, 199, 201, 203, 205, 207],
    ),
]


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


def load_targeted_repeats() -> list[ReviewSet]:
    if not RESULTS_PATH.exists():
        return []
    repeats = []
    for label, group, lines in TARGETED_REPEATS:
        observations = fit.read_results(
            RESULTS_PATH,
            source=group,
            group=group,
            active_name="validated_c_center_plus_refined_machine_bharmonic_bcross",
            active_cal_c_to_b=fit.VALIDATED_CAL_C_TO_B,
            active_bharmonic_params=fit.REFINED_BCROSS_CANDIDATE,
            include_lines=lines,
        )
        if observations:
            repeats.append(ReviewSet(label, [observations]))
    return repeats


def mean_point(observations: list[fit.Observation], b_deg: float, c_deg: float) -> np.ndarray:
    points = [
        obs.center
        for obs in observations
        if abs(obs.b_deg - b_deg) < 1e-6 and abs(obs.c_deg - c_deg) < 1e-6
    ]
    if not points:
        return np.full(3, float("nan"))
    return np.mean(np.array(points), axis=0)


def vector_text(vec: np.ndarray) -> str:
    return f"`{vec[0]:+.6f}`, `{vec[1]:+.6f}`, `{vec[2]:+.6f}`"


def norm_rows(
    data_sets: list[list[fit.Observation]],
    params: dict[str, float],
) -> list[tuple[float, fit.Observation, np.ndarray]]:
    rows = []
    for observations in data_sets:
        _, data_rows = fit.b_angle_delta_rows(observations, params)
        for obs, delta in data_rows:
            rows.append((float(np.linalg.norm(delta)), obs, delta))
    return rows


def acceptance_row(
    label: str,
    data_sets: list[list[fit.Observation]],
    params: dict[str, float],
) -> str:
    rows = norm_rows(data_sets, params)
    if not rows:
        return f"| {label} | `0` | `n/a` | `n/a` | `0/0` | `0/0` |"
    norms = np.array([norm for norm, _, _ in rows])
    rms, max_value = rms_max(norms)
    under_core = int(np.sum(norms <= 0.2 + 1e-12))
    under_refine = int(np.sum(norms <= 0.1 + 1e-12))
    return (
        f"| {label} | `{len(rows)}` | `{rms:.6f}` | `{max_value:.6f}` | "
        f"`{under_core}/{len(rows)}` | `{under_refine}/{len(rows)}` |"
    )


def worst_row_lines(
    data_sets: list[list[fit.Observation]],
    params: dict[str, float],
    limit: int = 8,
) -> list[str]:
    rows = sorted(norm_rows(data_sets, params), key=lambda row: row[0], reverse=True)
    lines = []
    for norm, obs, delta in rows[:limit]:
        lines.append(
            "| "
            f"`{obs.source}` | {obs.line} | `B{obs.b_deg:+.0f} C{obs.c_deg:.0f}` | "
            f"{vector_text(delta)} | `{norm:.6f}` |"
        )
    return lines


def write_report(path: Path) -> None:
    review_sets = load_review_sets()
    targeted_repeats = load_targeted_repeats()
    all_live_sets = [data_set for review_set in review_sets for data_set in review_set.data_sets]
    all_targeted_sets = [
        data_set
        for targeted_repeat in targeted_repeats
        for data_set in targeted_repeat.data_sets
    ]
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
    all_live_targeted_sets = [*all_live_sets]
    all_live_targeted_sets.extend(all_targeted_sets)
    post_targeted = fit.fit_direct_model(
        "b_harmonic_machine_bcross_no_cxy",
        all_live_targeted_sets,
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

    targeted_lines: list[str] = []
    if targeted_repeats:
        refined_data = [data_set for data_set in review_sets[2].data_sets]
        refined_observations = [obs for data_set in refined_data for obs in data_set]
        targeted_metric_rows = [
            f"| {targeted_repeat.label} | "
            f"{metric_text(targeted_repeat.data_sets, current_params)} |"
            for targeted_repeat in targeted_repeats
        ]
        repeat_shift_rows = []
        previous_targeted_observations: list[fit.Observation] | None = None
        for targeted_repeat in targeted_repeats:
            targeted_observations = [
                obs
                for data_set in targeted_repeat.data_sets
                for obs in data_set
            ]
            c180_shift = mean_point(targeted_observations, 0.0, 180.0) - mean_point(
                refined_observations,
                0.0,
                180.0,
            )
            c270_shift = mean_point(targeted_observations, 0.0, 270.0) - mean_point(
                refined_observations,
                0.0,
                270.0,
            )
            repeat_shift_rows.extend(
                [
                    f"| {targeted_repeat.label} vs refined | C180 | "
                    f"{vector_text(c180_shift)} | `{np.linalg.norm(c180_shift):.6f} mm` |",
                    f"| {targeted_repeat.label} vs refined | C270 | "
                    f"{vector_text(c270_shift)} | `{np.linalg.norm(c270_shift):.6f} mm` |",
                ]
            )
            if previous_targeted_observations is not None:
                c180_repeat_shift = mean_point(targeted_observations, 0.0, 180.0) - mean_point(
                    previous_targeted_observations,
                    0.0,
                    180.0,
                )
                c270_repeat_shift = mean_point(targeted_observations, 0.0, 270.0) - mean_point(
                    previous_targeted_observations,
                    0.0,
                    270.0,
                )
                repeat_shift_rows.extend(
                    [
                        f"| {targeted_repeat.label} vs prior targeted | C180 | "
                        f"{vector_text(c180_repeat_shift)} | `{np.linalg.norm(c180_repeat_shift):.6f} mm` |",
                        f"| {targeted_repeat.label} vs prior targeted | C270 | "
                        f"{vector_text(c270_repeat_shift)} | `{np.linalg.norm(c270_repeat_shift):.6f} mm` |",
                    ]
                )
            previous_targeted_observations = targeted_observations
        targeted_lines = [
            "",
            "## Targeted Repeat Results",
            "",
            "Two targeted `#711 = 5.0` repeats completed with accepted pass-2 rows",
            "`173..189` and `191..207` respectively, and no pass-2 rejects.",
            "",
            "| evaluation | non-B0 RMS/max |",
            "| --- | ---: |",
            *targeted_metric_rows,
            f"| targeted repeats combined | {metric_text(all_targeted_sets, current_params)} |",
            f"| current refined candidate on all live rows plus targeted repeats | {metric_text(all_live_targeted_sets, current_params)} |",
            f"| all-live-plus-targeted retune on all rows | {metric_text(all_live_targeted_sets, post_targeted.params)} |",
            "",
            "The targeted repeats are clean enough to use as evidence, but they are",
            "not a standalone retune target. The B0 reference moved substantially",
            "from the previous refined validation and repeated in the shifted state:",
            "",
            "| comparison | C group | B0 mean shift X/Y/Z | 3D shift |",
            "| --- | --- | ---: | ---: |",
            *repeat_shift_rows,
            "",
            "Including the targeted repeats in a retune improves today's shifted",
            "targeted rows but raises earlier validation maxima. Treat this as",
            "machine/session repeatability evidence before changing the candidate.",
        ]

    acceptance_lines = [
        "",
        "## Acceptance Band Review",
        "",
        "Use `0.2 mm` as the current production/core-task acceptance band and",
        "`0.1 mm` as the secondary refinement target. These counts use non-B0",
        "rows compared to the adjacent B0 references in each C group.",
        "",
        "| evaluation | non-B0 rows | RMS | max | <=0.2 mm | <=0.1 mm |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        acceptance_row("current refined candidate on live validation rows", all_live_sets, current_params),
        acceptance_row("current refined candidate on targeted repeats", all_targeted_sets, current_params),
        acceptance_row("current refined candidate on live plus targeted rows", all_live_targeted_sets, current_params),
        acceptance_row("all-live-plus-targeted retune on live plus targeted rows", all_live_targeted_sets, post_targeted.params),
        "",
        "The current refined candidate stays inside the `0.2 mm` core-task band",
        "for every accepted live and targeted non-B0 row. It does not satisfy the",
        "`0.1 mm` refinement target as a hard maximum; the over-`0.1 mm` rows are",
        "concentrated in high-B C180 and the shifted targeted-repeat session.",
        "",
        "The all-live-plus-targeted retune improves the shifted targeted repeats",
        "but still does not meet the `0.1 mm` hard target and is not live-tested.",
        "Do not replace the refined candidate with that retune unless a stable",
        "B0 reference check proves the shifted session is the new machine state.",
        "",
        "Worst current-candidate rows across live plus targeted data:",
        "",
        "| source | line | pose | delta X/Y/Z | norm |",
        "| --- | ---: | --- | ---: | ---: |",
        *worst_row_lines(all_live_targeted_sets, current_params),
    ]

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
        *targeted_lines,
        *acceptance_lines,
        "",
        "## Decision",
        "",
        "- Keep the refined candidate unchanged.",
        "- Do not promote it to persistent startup HAL yet.",
        "- Do not run another full `#711 = 4.0` validation.",
        "- Treat the refined candidate as acceptable for the core task only after",
        "  the shifted B0 reference state is checked; current data is inside",
        "  `0.2 mm` but not a hard `0.1 mm` fit.",
        "- The `#711 = 5.0` targeted repeats show a repeatable shifted B0",
        "  reference state; do not retune from those repeats alone.",
        "- The next machine run should be a short candidate-off B0 C-quadrant",
        "  reference check, not another high-B validation grid.",
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
