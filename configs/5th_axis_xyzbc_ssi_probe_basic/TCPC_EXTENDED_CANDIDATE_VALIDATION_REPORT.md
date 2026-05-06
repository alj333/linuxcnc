# TCPC Extended Candidate Validation Report

Generated from the full safe-grid validation run completed after the extended
candidate kinematics update.

## Machine State

- candidate was enabled only for the validation run
- `headheadkins.sim-bharm-enable` was disabled after completion
- machine was reported idle at `B0 C0` above the sphere
- UI/current tool displayed tool `0`, but the program fallback logged
  `program_probe_tool_number=3`, probe calibration offset `0.134533`, and
  zero motion tool offsets
- current TCPC kinematics still do not use tool length compensation, so the
  tool-0 display does not invalidate this run

## Data Selection

- source CSV: `tcpc-b-angle-scaling-diagnostic-2pass-results.csv`
- candidate-on accepted pass-2 rows:
  - first segment: `409-471`
  - resume segment: `473-529`
- first segment stopped after clean `B-90 C45` pass 2 at the next `B-90 C90`
  first-pass `-U side touch did not record point data`
- resume mode `#711=14` started with a fresh `B0 C0` reference and completed
  the remaining safe grid
- accepted pass-2 rows after the baseline: `61`
- nonzero-B validation rows: `42`
- no expected safe-grid pass-2 points are missing
- max pass-2 centering residuals: U `0.007500 mm`, V `0.015833 mm`
- accepted corrected diameter range: `30.126621` to `30.265788 mm`

## Validation Metrics

Vectors below compare each nonzero-B pose to the B0 reference at the same C
within the same run segment.

| segment | nonzero-B rows | RMS mm | max mm | B0 C0 drift mm |
| --- | ---: | ---: | ---: | ---: |
| first segment | 23 | 0.092310 | 0.179604 | 0.013651 |
| resume segment | 19 | 0.091345 | 0.189695 | 0.004489 |
| combined per-segment refs | 42 | 0.091875 | 0.189695 | n/a |

## Worst Error Vectors

| line | segment | pose | dX mm | dY mm | dZ mm | magnitude mm |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 491 | resume | `B-60 C180` | -0.173795 | -0.073580 | +0.019114 | 0.189695 |
| 445 | first | `B+60 C90` | -0.091015 | +0.154723 | -0.005878 | 0.179604 |
| 489 | resume | `B-60 C90` | -0.111678 | +0.127532 | +0.030139 | 0.172176 |
| 431 | first | `B+30 C90` | -0.052853 | +0.155606 | +0.015937 | 0.165108 |
| 487 | resume | `B-60 C45` | -0.145588 | +0.053298 | +0.004836 | 0.155113 |
| 449 | first | `B+60 C225` | -0.128960 | -0.056641 | -0.017858 | 0.141978 |
| 443 | first | `B+60 C45` | -0.089541 | +0.103898 | -0.003619 | 0.137206 |
| 447 | first | `B+60 C180` | -0.127492 | -0.003907 | -0.035348 | 0.132359 |
| 451 | first | `B+60 C270` | -0.119850 | -0.037083 | -0.003295 | 0.125499 |
| 493 | resume | `B-60 C225` | -0.102141 | +0.015120 | +0.069081 | 0.124232 |
| 435 | first | `B+30 C225` | -0.108889 | -0.029879 | -0.022589 | 0.115151 |
| 495 | resume | `B-60 C270` | -0.105806 | -0.011808 | +0.042244 | 0.114538 |
| 429 | first | `B+30 C45` | -0.007323 | +0.103075 | +0.021819 | 0.105613 |

## Interpretation

- The extended candidate validated under the core `0.2 mm` requirement on this
  full safe-grid run.
- It is not yet a full `0.1 mm` solution. The remaining problem area is mainly
  B around `+60` and `-60`, with strong C dependence.
- The earlier `B-90 C90` miss was a probing reach/margin issue, not an
  accepted bad data point. Resume mode completed `B-90 C90` with residual
  vector `(+0.017923, +0.072192, +0.024901)`, magnitude `0.078441 mm`.
- The tool-0 display should be fixed before future tool-length validation, but
  it did not affect this run because the program used the known probe fallback
  values and TCPC tool-length compensation is not wired in yet.

## Next Work

1. Keep the extended candidate non-persistent until the validation data is
   folded into the offline fit.
2. Refit using the candidate-on validation rows as measured residuals and look
   specifically at the `B+60` and `B-60` C-dependent pattern.
3. Decide whether to make a small second correction candidate or keep this
   candidate as the current practical core-task solution.
4. Before long-probe comparison, restore Probe Basic/LinuxCNC tool state so
   the loaded probe is not displayed as tool `0`.
