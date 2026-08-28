#!/usr/bin/env python3
"""Offline spatial comparison for the completed T4 new-location campaign.

The analyzer validates the populated A4+A6+A7 composite and the sealed T4
reference before comparing their equal-weight canonical pose fields. It has no
LinuxCNC or HAL interface and cannot issue a machine command.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import sys
from typing import Callable, Sequence

import numpy as np

import analyze_tcpc_length_aware_t4_attempt2 as reference
import validate_tcpc_length_aware_t4_new_location_2026082701_attempt7_complete as completion


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_REPORT = (
    HERE
    / "TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_SPATIAL_COMPARISON_REPORT.md"
)


class AnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class Metric:
    rms: float
    maximum: float


@dataclass(frozen=True)
class RepeatMetric:
    groups: int
    observations: int
    vector: Metric
    axis_rms: np.ndarray


@dataclass(frozen=True)
class DiameterRepeatMetric:
    groups: int
    observations: int
    rms: float
    maximum: float


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def exact_int(row: dict[str, str], field: str) -> int:
    value = float(row[field])
    rounded = round(value)
    if not math.isfinite(value) or abs(value - rounded) > 1e-9:
        raise AnalysisError(f"{field}={row[field]!r} is not an exact integer")
    return int(rounded)


def number(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not math.isfinite(value):
        raise AnalysisError(f"{field} is not finite")
    return value


def pose(row: dict[str, str]) -> tuple[int, int]:
    return reference.canonical_pose(
        number(row, "abs_b_deg"), number(row, "abs_c_deg")
    )


def center(row: dict[str, str]) -> np.ndarray:
    return np.asarray(
        [number(row, f"center_abs_{axis}_mm") for axis in "xyz"], dtype=float
    )


def metric(vectors: np.ndarray) -> Metric:
    norms = np.linalg.norm(vectors, axis=1)
    return Metric(float(np.sqrt(np.mean(norms * norms))), float(np.max(norms)))


def center_metric(values: np.ndarray) -> Metric:
    return metric(values - np.mean(values, axis=0))


def vector_text(vector: Sequence[float]) -> str:
    return ", ".join(f"{value:+.6f}" for value in vector)


def metric_text(value: Metric) -> str:
    return f"{value.rms:.6f} / {value.maximum:.6f}"


def group_rows(
    rows: Sequence[dict[str, str]],
) -> dict[tuple[int, int], list[dict[str, str]]]:
    grouped: dict[tuple[int, int], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(pose(row), []).append(row)
    return grouped


def collapse_vector(
    rows: Sequence[dict[str, str]], getter: Callable[[dict[str, str]], np.ndarray]
) -> dict[tuple[int, int], np.ndarray]:
    return {
        key: np.mean(np.vstack([getter(row) for row in values]), axis=0)
        for key, values in group_rows(rows).items()
    }


def collapse_scalar(
    rows: Sequence[dict[str, str]], getter: Callable[[dict[str, str]], float]
) -> dict[tuple[int, int], float]:
    return {
        key: float(np.mean([getter(row) for row in values]))
        for key, values in group_rows(rows).items()
    }


def repeated_center_scatter(rows: Sequence[dict[str, str]]) -> RepeatMetric:
    grouped = [values for values in group_rows(rows).values() if len(values) > 1]
    residuals = np.vstack(
        [
            center(row) - np.mean(np.vstack([center(item) for item in values]), axis=0)
            for values in grouped
            for row in values
        ]
    )
    return RepeatMetric(
        len(grouped),
        len(residuals),
        metric(residuals),
        np.sqrt(np.mean(residuals * residuals, axis=0)),
    )


def repeated_diameter_scatter(
    rows: Sequence[dict[str, str]],
) -> DiameterRepeatMetric:
    grouped = [values for values in group_rows(rows).values() if len(values) > 1]
    residuals = np.asarray(
        [
            number(row, "v_corrected_diameter_mm")
            - np.mean([number(item, "v_corrected_diameter_mm") for item in values])
            for values in grouped
            for row in values
        ],
        dtype=float,
    )
    return DiameterRepeatMetric(
        len(grouped),
        len(residuals),
        float(np.sqrt(np.mean(residuals * residuals))),
        float(np.max(np.abs(residuals))),
    )


def paired_repeated_diameter_scatter(
    reference_rows: Sequence[dict[str, str]],
    new_rows: Sequence[dict[str, str]],
) -> DiameterRepeatMetric:
    reference_by_sequence = {
        exact_int(row, "sample_seq"): row for row in reference_rows
    }
    new_by_sequence = {exact_int(row, "sample_seq"): row for row in new_rows}
    if set(reference_by_sequence) != set(new_by_sequence):
        raise AnalysisError("reference/new result sequence sets differ")
    grouped: dict[tuple[int, int], list[float]] = {}
    for sequence in sorted(reference_by_sequence):
        reference_row = reference_by_sequence[sequence]
        new_row = new_by_sequence[sequence]
        if pose(reference_row) != pose(new_row):
            raise AnalysisError(f"reference/new pose differs at sequence {sequence}")
        difference = number(new_row, "v_corrected_diameter_mm") - number(
            reference_row, "v_corrected_diameter_mm"
        )
        grouped.setdefault(pose(reference_row), []).append(difference)
    repeated = [values for values in grouped.values() if len(values) > 1]
    residuals = np.asarray(
        [value - np.mean(values) for values in repeated for value in values],
        dtype=float,
    )
    return DiameterRepeatMetric(
        len(repeated),
        len(residuals),
        float(np.sqrt(np.mean(residuals * residuals))),
        float(np.max(np.abs(residuals))),
    )


def load_new_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validated = completion.validate_completed_run()
    a7_results = validated["results"]
    a7_states = validated["states"]
    if not isinstance(a7_results, list) or not isinstance(a7_states, list):
        raise AnalysisError("completion validator returned unexpected row types")

    composite_results, _ = completion.composite_center_rows(a7_results)
    _, a4_states = completion.frozen.csv_rows(completion.frozen.A4_PATHS["state"])
    _, a6_all_states = completion.frozen.csv_rows(completion.frozen.A6_PATHS["state"])
    a6_states = [
        row
        for row in a6_all_states
        if 10 <= exact_int(row, "sample_seq") <= 23
    ]
    composite_states = [*a4_states, *a6_states, *a7_states]
    if [exact_int(row, "sample_seq") for row in composite_states] != list(
        range(1, 102)
    ):
        raise AnalysisError("new composite state sequence is not exactly 1..101")
    return composite_results, composite_states


def load_reference_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    # This validates the archive inventory, six acquisition files, canonical
    # topology, model snapshots, closures, and pulse transactions.
    reference.analyze()
    results = reference.read_rows(reference.RESULTS, reference.RESULT_FIELDS)
    states = reference.read_rows(reference.STATE, reference.STATE_FIELDS)
    return results, states


def fixed_head_vector_fit(
    keys: Sequence[tuple[int, int]], delta: np.ndarray
) -> tuple[Metric, float]:
    design: list[np.ndarray] = []
    observed: list[float] = []
    for (b_deg, c_deg), vector in zip(keys, delta, strict=True):
        b_rad = math.radians(b_deg)
        c_rad = math.radians(c_deg)
        u = np.asarray(
            [
                math.cos(b_rad) * math.cos(c_rad),
                math.cos(b_rad) * math.sin(c_rad),
                -math.sin(b_rad),
            ]
        )
        v = np.asarray([-math.sin(c_rad), math.cos(c_rad), 0.0])
        w = np.asarray(
            [
                -math.sin(b_rad) * math.cos(c_rad),
                -math.sin(b_rad) * math.sin(c_rad),
                -math.cos(b_rad),
            ]
        )
        transform = np.column_stack((u, v, w))
        for axis in range(3):
            row = np.zeros(6)
            row[axis] = 1.0
            row[3:] = transform[axis]
            design.append(row)
            observed.append(float(vector[axis]))
    matrix = np.vstack(design)
    values = np.asarray(observed)
    coefficients = np.linalg.lstsq(matrix, values, rcond=None)[0]
    fitted = (matrix @ coefficients).reshape((-1, 3))
    remainder = delta - fitted
    explained = 1.0 - float(np.sum(remainder * remainder) / np.sum(delta * delta))
    return metric(remainder), explained


def paired_parity(
    keys: Sequence[tuple[int, int]], delta: np.ndarray
) -> tuple[Metric, np.ndarray, Metric, np.ndarray]:
    by_pose = dict(zip(keys, delta, strict=True))
    even: list[np.ndarray] = []
    odd: list[np.ndarray] = []
    for b_deg in (5, 10, 15, 30, 45, 60, 90):
        for c_deg in range(0, 360, 45):
            positive = (b_deg, c_deg)
            negative = (-b_deg, c_deg)
            if positive in by_pose and negative in by_pose:
                even.append((by_pose[positive] + by_pose[negative]) / 2.0)
                odd.append((by_pose[positive] - by_pose[negative]) / 2.0)
    even_values = np.vstack(even)
    odd_values = np.vstack(odd)
    return (
        metric(even_values),
        np.sqrt(np.mean(even_values * even_values, axis=0)),
        metric(odd_values),
        np.sqrt(np.mean(odd_values * odd_values, axis=0)),
    )


def encoder_delta(
    reference_states: Sequence[dict[str, str]],
    new_states: Sequence[dict[str, str]],
) -> tuple[np.ndarray, np.ndarray]:
    def error(row: dict[str, str]) -> np.ndarray:
        return np.asarray(
            [
                number(row, "joint_b_fb_deg") - number(row, "joint_b_cmd_deg"),
                number(row, "joint_c_fb_deg") - number(row, "joint_c_cmd_deg"),
            ]
        )

    reference_errors = collapse_vector(reference_states, error)
    new_errors = collapse_vector(new_states, error)
    keys = sorted(reference_errors)
    if set(keys) != set(new_errors):
        raise AnalysisError("encoder pose sets differ")
    delta = np.vstack([new_errors[key] - reference_errors[key] for key in keys])
    return np.sqrt(np.mean(delta * delta, axis=0)), np.max(np.abs(delta), axis=0)


def analyze() -> dict[str, object]:
    if completion.self_test() != 5:
        raise AnalysisError("completion validator mutation self-test changed")
    reference.self_test()
    reference_rows, reference_states = load_reference_rows()
    new_rows, new_states = load_new_rows()
    reference_centers = collapse_vector(reference_rows, center)
    new_centers = collapse_vector(new_rows, center)
    keys = sorted(reference_centers)
    if len(keys) != 76 or set(keys) != set(new_centers):
        raise AnalysisError("reference/new canonical pose sets are not the same 76 poses")

    ref = np.vstack([reference_centers[key] for key in keys])
    new = np.vstack([new_centers[key] for key in keys])
    ref_residual = ref - np.mean(ref, axis=0)
    new_residual = new - np.mean(new, axis=0)
    delta = new_residual - ref_residual
    delta_metric = metric(delta)
    delta_axis_rms = np.sqrt(np.mean(delta * delta, axis=0))
    worst_index = int(np.argmax(np.linalg.norm(delta, axis=1)))
    energy_fraction = delta_axis_rms * delta_axis_rms / (delta_metric.rms**2)

    even_metric, even_axes, odd_metric, odd_axes = paired_parity(keys, delta)
    seating_remainder, seating_explained = fixed_head_vector_fit(keys, delta)

    reference_diameter = collapse_scalar(
        reference_rows, lambda row: number(row, "v_corrected_diameter_mm")
    )
    new_diameter = collapse_scalar(
        new_rows, lambda row: number(row, "v_corrected_diameter_mm")
    )
    diameter_delta = {
        key: new_diameter[key] - reference_diameter[key] for key in keys
    }

    def diameter_values(
        source: dict[tuple[int, int], float], sectors: tuple[int, int]
    ) -> np.ndarray:
        return np.asarray([source[key] for key in keys if key[1] in sectors])

    x_sectors = (90, 270)  # V=(-sin C,+cos C,0), therefore V is machine X.
    y_sectors = (0, 180)
    ref_x = diameter_values(reference_diameter, x_sectors)
    ref_y = diameter_values(reference_diameter, y_sectors)
    new_x = diameter_values(new_diameter, x_sectors)
    new_y = diameter_values(new_diameter, y_sectors)
    delta_x = diameter_values(diameter_delta, x_sectors)
    delta_y = diameter_values(diameter_delta, y_sectors)
    diameter_contrast = float(np.mean(delta_x) - np.mean(delta_y))
    diameter_sectors = {
        c_deg: (
            float(np.mean(diameter_values(reference_diameter, (c_deg, c_deg)))),
            float(np.mean(diameter_values(new_diameter, (c_deg, c_deg)))),
            float(np.mean(diameter_values(diameter_delta, (c_deg, c_deg)))),
        )
        for c_deg in (0, 90, 180, 270)
    }

    signed_b_contrasts = []
    for b_deg in sorted({key[0] for key in keys}):
        x_values = np.asarray(
            [diameter_delta[key] for key in keys if key[0] == b_deg and key[1] in x_sectors]
        )
        y_values = np.asarray(
            [diameter_delta[key] for key in keys if key[0] == b_deg and key[1] in y_sectors]
        )
        if len(x_values) and len(y_values):
            signed_b_contrasts.append(float(np.mean(x_values) - np.mean(y_values)))

    c_groups: dict[int, Metric] = {}
    c_y_means: dict[int, float] = {}
    for c_deg in (0, 45, 90, 135, 180, 225, 270, 315):
        indices = [index for index, key in enumerate(keys) if key[1] == c_deg]
        c_groups[c_deg] = metric(delta[indices])
        c_y_means[c_deg] = float(np.mean(delta[indices, 1]))

    low_indices = [index for index, key in enumerate(keys) if abs(key[0]) <= 15]
    high_indices = [index for index, key in enumerate(keys) if abs(key[0]) >= 30]
    encoder_rms, encoder_max = encoder_delta(reference_states, new_states)

    return {
        "reference_rows": reference_rows,
        "new_rows": new_rows,
        "keys": keys,
        "reference_metric": center_metric(ref),
        "new_metric": center_metric(new),
        "mean_displacement": np.mean(new, axis=0) - np.mean(ref, axis=0),
        "delta": delta,
        "delta_metric": delta_metric,
        "delta_axis_rms": delta_axis_rms,
        "delta_energy_fraction": energy_fraction,
        "worst_pose": keys[worst_index],
        "worst_vector": delta[worst_index],
        "low_metric": metric(delta[low_indices]),
        "high_metric": metric(delta[high_indices]),
        "even_metric": even_metric,
        "even_axes": even_axes,
        "odd_metric": odd_metric,
        "odd_axes": odd_axes,
        "c_groups": c_groups,
        "c_y_means": c_y_means,
        "seating_remainder": seating_remainder,
        "seating_explained": seating_explained,
        "reference_repeat": repeated_center_scatter(reference_rows),
        "new_repeat": repeated_center_scatter(new_rows),
        "reference_diameter_repeat": repeated_diameter_scatter(reference_rows),
        "new_diameter_repeat": repeated_diameter_scatter(new_rows),
        "paired_diameter_repeat": paired_repeated_diameter_scatter(
            reference_rows, new_rows
        ),
        "ref_x": ref_x,
        "ref_y": ref_y,
        "new_x": new_x,
        "new_y": new_y,
        "delta_x": delta_x,
        "delta_y": delta_y,
        "diameter_contrast": diameter_contrast,
        "diameter_sectors": diameter_sectors,
        "signed_b_contrast_min": min(signed_b_contrasts),
        "signed_b_contrast_max": max(signed_b_contrasts),
        "encoder_rms": encoder_rms,
        "encoder_max": encoder_max,
    }


def render_report(data: dict[str, object]) -> str:
    displacement = data["mean_displacement"]
    delta_metric = data["delta_metric"]
    delta_axis_rms = data["delta_axis_rms"]
    fractions = data["delta_energy_fraction"]
    worst_pose = data["worst_pose"]
    worst_vector = data["worst_vector"]
    reference_repeat = data["reference_repeat"]
    new_repeat = data["new_repeat"]
    assert isinstance(displacement, np.ndarray)
    assert isinstance(delta_metric, Metric)
    assert isinstance(delta_axis_rms, np.ndarray)
    assert isinstance(fractions, np.ndarray)
    assert isinstance(worst_pose, tuple)
    assert isinstance(worst_vector, np.ndarray)
    assert isinstance(reference_repeat, RepeatMetric)
    assert isinstance(new_repeat, RepeatMetric)

    ref_x = data["ref_x"]
    ref_y = data["ref_y"]
    new_x = data["new_x"]
    new_y = data["new_y"]
    delta_x = data["delta_x"]
    delta_y = data["delta_y"]
    encoder_rms = data["encoder_rms"]
    encoder_max = data["encoder_max"]
    assert all(
        isinstance(value, np.ndarray)
        for value in (ref_x, ref_y, new_x, new_y, delta_x, delta_y, encoder_rms, encoder_max)
    )

    c_groups = data["c_groups"]
    c_y_means = data["c_y_means"]
    assert isinstance(c_groups, dict) and isinstance(c_y_means, dict)
    displacement_norm = float(np.linalg.norm(displacement))
    location_x_fraction = abs(float(displacement[0])) / displacement_norm
    irreducible = Metric(delta_metric.rms / 2.0, delta_metric.maximum / 2.0)

    input_paths = [
        reference.RESULTS,
        reference.STATE,
        completion.frozen.A4_PATHS["results"],
        completion.frozen.A4_PATHS["state"],
        completion.frozen.A6_PATHS["results"],
        completion.frozen.A6_PATHS["state"],
        *completion.frozen.A7_PATHS.values(),
        completion.frozen.RUNNER,
        Path(reference.__file__).resolve(),
        Path(completion.frozen.__file__).resolve(),
        Path(completion.__file__).resolve(),
    ]
    lines = [
        "# T4 New-Location Spatial Comparison",
        "",
        "Status: `DIAGNOSTIC ONLY - STRONG LOCATION/SESSION-ASSOCIATED DIFFERENCE; X-ORIENTED INDICATED-SPAN CHANGE`",
        "",
        "## Decision",
        "",
        "Disposition: `NO TCPC CALIBRATION CHANGE`. This second location is retained only as axis-rail and machine-volume diagnostic evidence; it is not a fit source for the current TCPC model.",
        "",
        "The completed data is consistent with a location-dependent linear-axis or machine-volume term, but it cannot establish a rail cause by itself. The campaigns differ in X, Y, time, homing session, and T4 seating. This evidence therefore does not justify changing either global B-axis/TCPC parameters or an axis compensation table.",
        "",
        "The strongest direct evidence is the certified-sphere opposing-contact span. In the runner, `V=(-sin(C),+cos(C),0)`, so C90/C270 measure a pure machine-X line and C0/C180 measure a pure machine-Y line. The X-line span changes by about 96 um between locations while the Y-line span changes by only about 9 um. Rigid sphere position, TCPC center translation, and any correction constant at a fixed B/C pose cancel from this diameter measurement.",
        "",
        "This directly identifies an X-oriented indicated-span change and makes X-axis-local metrology or X-associated cross-axis geometry a leading hypothesis. It does not prove an X-rail fault or show that the new X region is the bad region: the reference X span was anomalously high, while the new-location X/Y spans are nearly isotropic. The broader center field is instead Y-dominated at high B and remains coupled to its single-side W/U reconstruction. A same-seating axis-isolation run is required before assigning either result to a rail.",
        "",
        "## Center Field",
        "",
        f"- reference equal-76 centered RMS / max: `{metric_text(data['reference_metric'])} mm`",
        f"- new equal-76 centered RMS / max: `{metric_text(data['new_metric'])} mm`",
        f"- new-minus-reference after independent XYZ centering: `{metric_text(delta_metric)} mm`",
        f"- delta component RMS X/Y/Z: `[{vector_text(delta_axis_rms)}] mm`",
        f"- delta energy X/Y/Z: `[{', '.join(f'{100.0 * value:.1f}%' for value in fractions)}]`",
        f"- worst delta: `B{worst_pose[0]:+d}/C{worst_pose[1]}` = `[{vector_text(worst_vector)}] mm`, norm `{float(np.linalg.norm(worst_vector)):.6f} mm`",
        "",
        f"The equal-pose mean sphere displacement is `[{vector_text(displacement)}] mm`, norm `{displacement_norm:.6f} mm`; `{100.0 * location_x_fraction:.3f}%` of that norm is X. Z changed only `{abs(float(displacement[2])):.6f} mm`, so this comparison does not primarily sample a different Z-rail height.",
        "",
        f"Low tilt `|B|<=15` delta RMS/max is `{metric_text(data['low_metric'])} mm`; high tilt `|B|>=30` rises to `{metric_text(data['high_metric'])} mm`. The paired B-sign even component is `{metric_text(data['even_metric'])} mm`, versus `{metric_text(data['odd_metric'])} mm` odd. Parity is descriptive only: a B-zero change can itself create even signed-B XY terms, so this split does not exclude B zero.",
        "",
        "| C sector | pose-delta RMS / max (mm) | mean Y delta (mm) |",
        "| ---: | ---: | ---: |",
    ]
    for c_deg in (0, 45, 90, 135, 180, 225, 270, 315):
        lines.append(
            f"| {c_deg} | `{metric_text(c_groups[c_deg])}` | `{c_y_means[c_deg]:+.6f}` |"
        )
    lines.extend(
        [
            "",
            "C90/C270 dominate and have the same Y sign; C0/C180 are smaller and have the opposite Y sign. This second-C-harmonic-like structure is inconsistent with explaining the complete field as one simple rigid radial probe shift. It does not independently exclude a B-zero change coupled to other machine geometry.",
            "",
            f"A best-fit constant rigid vector in the runner's rotating U/V/W head frame explains only `{100.0 * float(data['seating_explained']):.1f}%` of the location-delta energy; its unexplained remainder is `{metric_text(data['seating_remainder'])} mm`. A simple rigid probe seating shift therefore cannot account for the field.",
            "",
            "## Direct X/Y Span",
            "",
            "Equal weighting is used after collapsing all 101 rows to the same 76 canonical poses.",
            "",
            "| V measurement line | poses | reference mean (mm) | new mean (mm) | new-reference mean / RMS (mm) |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| machine X, C90/C270 | `{len(delta_x)}` | `{float(np.mean(ref_x)):.9f}` | `{float(np.mean(new_x)):.9f}` | `{float(np.mean(delta_x)):+.9f} / {float(np.sqrt(np.mean(delta_x * delta_x))):.9f}` |",
            f"| machine Y, C0/C180 | `{len(delta_y)}` | `{float(np.mean(ref_y)):.9f}` | `{float(np.mean(new_y)):.9f}` | `{float(np.mean(delta_y)):+.9f} / {float(np.sqrt(np.mean(delta_y * delta_y))):.9f}` |",
            "",
            f"The X-minus-Y change of changes is `{float(data['diameter_contrast']):+.9f} mm`. Its sign is consistent in every signed-B band; band contrasts range `{float(data['signed_b_contrast_min']):+.6f}..{float(data['signed_b_contrast_max']):+.6f} mm`.",
            "",
            "The reference X/Y means differ by "
            f"`{float(np.mean(ref_x) - np.mean(ref_y)):+.6f} mm`; the new-location means differ by `{float(np.mean(new_x) - np.mean(new_y)):+.6f} mm`. This is why the evidence identifies a change in X behavior between locations rather than declaring the new X region intrinsically worse.",
            "",
            "Opposite C orientations are retained separately because their disparity is material:",
            "",
            "| C | machine line | reference / new / delta mean (mm) |",
            "| ---: | --- | ---: |",
        ]
    )
    diameter_sectors = data["diameter_sectors"]
    assert isinstance(diameter_sectors, dict)
    for c_deg, line in ((0, "Y"), (90, "X"), (180, "Y"), (270, "X")):
        ref_value, new_value, delta_value = diameter_sectors[c_deg]
        lines.append(
            f"| {c_deg} | {line} | `{ref_value:.6f} / {new_value:.6f} / {delta_value:+.6f}` |"
        )
    paired_diameter_repeat = data["paired_diameter_repeat"]
    reference_diameter_repeat = data["reference_diameter_repeat"]
    new_diameter_repeat = data["new_diameter_repeat"]
    assert isinstance(paired_diameter_repeat, DiameterRepeatMetric)
    assert isinstance(reference_diameter_repeat, DiameterRepeatMetric)
    assert isinstance(new_diameter_repeat, DiameterRepeatMetric)
    lines.extend(
        [
            "",
            "Both X orientations change negative, so the pooled X association remains. However, the C90/C270 disparity is `0.151500 mm` at the reference and `0.104521 mm` at the new location. The pooled X value is therefore an indicated-span diagnostic, not a pure local scale estimate.",
            "",
            "## Repeatability And Encoders",
            "",
            f"- reference repeated-center scatter: `{reference_repeat.groups}` groups / `{reference_repeat.observations}` observations, `{metric_text(reference_repeat.vector)} mm`, axis RMS `[{vector_text(reference_repeat.axis_rms)}] mm`",
            f"- new repeated-center scatter: `{new_repeat.groups}` groups / `{new_repeat.observations}` observations, `{metric_text(new_repeat.vector)} mm`, axis RMS `[{vector_text(new_repeat.axis_rms)}] mm`",
            f"- reference repeated-diameter scatter RMS / max: `{reference_diameter_repeat.rms:.6f} / {reference_diameter_repeat.maximum:.6f} mm`",
            f"- new repeated-diameter scatter RMS / max: `{new_diameter_repeat.rms:.6f} / {new_diameter_repeat.maximum:.6f} mm`",
            f"- paired new-reference repeated-diameter scatter RMS / max: `{paired_diameter_repeat.rms:.6f} / {paired_diameter_repeat.maximum:.6f} mm`",
            "",
            f"The systematic location delta is `{delta_metric.rms / new_repeat.vector.rms:.2f}x` the new repeated-center RMS and `{delta_metric.maximum / new_repeat.vector.maximum:.2f}x` its maximum. The result is not explained by accepted probe chatter or ordinary within-run scatter.",
            "",
            f"The pooled X-minus-Y diameter contrast is `{abs(float(data['diameter_contrast'])) / paired_diameter_repeat.rms:.2f}x` the paired repeated-diameter RMS. This supports a repeatable session/location association, while the cross-session reseat remains a systematic confound rather than random scatter.",
            "",
            f"Posewise new-minus-reference B/C feedback-minus-command RMS is `[{vector_text(encoder_rms)}] deg`; maximum is `[{vector_text(encoder_max)}] deg`. Even using the full `{completion.TOOL_LENGTH_MM:.3f} mm` T4 length as a conservative lever, the RMS bounds are about `{math.radians(float(encoder_rms[0])) * completion.TOOL_LENGTH_MM:.6f} / {math.radians(float(encoder_rms[1])) * completion.TOOL_LENGTH_MM:.6f} mm` for B/C, far below the `{delta_metric.rms:.6f} mm` field change. This does not test absolute rotary-axis alignment, but it rules out servo following error as the main cause.",
            "",
            "## Software Consequence",
            "",
            f"Even an unrestricted location-independent pose table fitted equally to both locations has an irreducible half-difference of `{metric_text(irreducible)} mm` at each location before measurement noise. A global B/C TCPC retune can compromise between the two fields, but cannot make both locations agree. Absorbing the full new-location field into the global TCPC coefficients would over-correct the reference location.",
            "",
            "The next isolation test should keep T4 seated and the sphere at the same Z: acquire a compact B0/B+45/B-45/B+90/B-90 grid at two points differing only in X, then at two points differing only in Y. Every positive B is paired with its corresponding negative B. The same V-pair diameter rows provide a direct X/Y span check. A dial-gauge or laser measurement can then decide whether the location term belongs in screw/axis compensation, a volumetric map, or head/load correction.",
            "",
            "## Provenance",
            "",
            "The analyzer executes the populated Attempt-7 validator mutation self-test and the sealed reference analyzer self-test before loading the comparison. No coordinate rotation, scale, shear, group offset, or fit is removed from the center fields; only one global XYZ translation per sphere location is removed.",
            "",
            f"Analyzer: `{relative(Path(__file__).resolve())}` SHA-256 `{sha256(Path(__file__).resolve())}`.",
            "",
            "| input | SHA-256 at analysis time |",
            "| --- | --- |",
        ]
    )
    for path in input_paths:
        lines.append(f"| `{relative(path)}` | `{sha256(path)}` |")
    lines.extend(
        [
            "",
            "This analyzer imports neither LinuxCNC nor HAL and issued no controller command.",
            "",
        ]
    )
    return "\n".join(lines)


def self_test() -> None:
    sample = np.asarray([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    value = metric(sample)
    if abs(value.rms - 1.0) > 1e-12 or abs(value.maximum - 1.0) > 1e-12:
        raise AnalysisError("metric self-test failed")
    if reference.canonical_pose(0.0, 360.0) != (0, 0):
        raise AnalysisError("pose canonicalization self-test failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        self_test()
        if args.self_test:
            print("T4 new-location spatial analyzer self-test: PASS")
            return 0
        data = analyze()
        args.report.write_text(render_report(data), encoding="ascii")
    except (
        AnalysisError,
        AssertionError,
        OSError,
        ValueError,
        reference.AnalysisError,
        completion.ValidationError,
        completion.anchor.ValidationError,
        completion.bounds.AuditError,
    ) as exc:
        print(f"T4 new-location spatial analysis: FAIL: {exc}", file=sys.stderr)
        return 1
    delta = data["delta_metric"]
    assert isinstance(delta, Metric)
    print("T4 new-location spatial analysis: PASS")
    print(f"location delta RMS/max: {metric_text(delta)} mm")
    print(f"X-vs-Y diameter change: {float(data['diameter_contrast']):+.9f} mm")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
