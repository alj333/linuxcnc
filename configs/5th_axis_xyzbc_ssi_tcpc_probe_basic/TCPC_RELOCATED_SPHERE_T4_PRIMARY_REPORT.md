# Relocated-Sphere Campaign T4 Primary Report

Campaign `2026082404`, mode `23`, attempt `1` completed. All schemas, pose
identities, tool states, contact quality checks, endpoints, and closures pass.
T4 is the training set. T3 remains an untouched holdout and is not eligible
for candidate selection.

| run | rows | current centered RMS / max | worst closure |
| --- | ---: | ---: | ---: |
| T4 primary | 101 | 0.201016 / 0.711434 mm | 0.027115 mm |

## Acquisition Quality

- Exact counts are 101 results, 101 state rows, and 28 closures. Sequences
  `1..101` are complete and unique, with 41 positive-B, 41 matching
  negative-B, and 19 B0 rows.
- All 28 closures pass. Closure mean/RMS/max are
  `0.013020 / 0.014798 / 0.027115 mm`; whole-run closure is `0.023988 mm`.
- Maximum pass-to-pass center delta is `0.024466 mm` at sequence 58
  (`B-30 C90`), below the `0.100 mm` gate.
- Maximum four-contact center correction is `0.023730 mm`, also sequence 58,
  below the `0.250 mm` gate.
- Corrected V diameters span `30.074955..30.328879 mm`; all remain within
  `29.9..30.5 mm`. Minimum accepted probe travel is `3.833466 mm`.
- Maximum B/C pose errors are `0.000333 / 0.004097 deg`; logged XYZ following
  errors are zero at CSV precision.

No row meets a rejection criterion. Sequences 37, 58, 89, and 91 receive
sensitivity checks because they contain the strongest closure or two-pass
quality extrema, but they remain in the primary fit.

## Repeatable Structure

The maximum current-calibration residual is `0.711434 mm` at sequence 91,
`B-90 C270`. Similar large residuals occur at `B-60 C270` (`0.694426 mm`)
and `B-45 C270` (`0.559953 mm`), while their local block closures are only
approximately `0.003-0.006 mm`. This is repeatable pose dependence, not an
isolated missed touch.

The B0 C sweep also repeats within `0.0227 mm` and is dominated by a stable
first-C harmonic. However, low-B signed offsets do not scale cleanly with
`sin(B)` or `1-cos(B)`, and measured diameter depends strongly on probe
direction. Those features, plus correlation with the linear-axis positions,
are consistent with rail mapping, compliance, backlash, or probe/spindle
seating as well as TCPC geometry. A single fixed sphere cannot separate those
causes completely.

## Decision Boundary

These are diagnostics under the current calibration, not a live candidate
release. Fit selection uses equal-weight unique T4 poses and grouped holdouts;
closure duplicates remain quality evidence rather than extra fit weight. The
candidate family, regularization, coefficients, input hashes, and pass gates
must be frozen before T3 is run.

T3 will run under the unchanged current calibration. The frozen additive
candidate can then be evaluated exactly offline as:

```text
candidate_center = measured_current_center + frozen_delta_offset(B, C)
```

No TCPC coefficient is eligible for live loading until that untouched T3
test passes, followed by a loaded-candidate physical verification.
