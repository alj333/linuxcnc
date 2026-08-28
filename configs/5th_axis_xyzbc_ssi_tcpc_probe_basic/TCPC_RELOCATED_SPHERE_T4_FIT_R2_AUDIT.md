# Relocated-Sphere T4 Fit R2 Audit

Audit completed `2026-08-25` before any R2 overlay, LinuxCNC load, or machine
motion. No T3 measurement data was read.

## Result

R2 is acceptable only for a guarded, same-grid T4 implementation test. It is
not accepted as a production correction or as evidence of transfer to T3,
other tool lengths, unmeasured C sectors, or the full configured rotary range.

- primary: 10 terms, lambda 10
- 76-pose current/predicted RMS: `0.219602 / 0.085763 mm`
- 76-pose current/predicted maximum: `0.709875 / 0.204948 mm`
- primary measured-grid correction maximum: `0.670166 mm`
- primary plus inner-refit protocol maximum: `0.722851 mm`
- selection-adjusted signed-B outer RMS/max: `0.122241 / 0.319849 mm`
- selection-adjusted paired-abs(B) outer RMS/max: `0.110892 / 0.267291 mm`
- selection-adjusted C-sector outer RMS/max: `0.201632 / 0.655231 mm`
- selection-adjusted antipodal-C outer RMS/max: `0.253374 / 0.837828 mm`

## Method Checks

- `PASS`: repeated rows are collapsed to 76 equal-weight poses before fitting.
- `PASS`: every outer fold repeats term and lambda selection without reading
  the held response. Fold-local scaling and intercepts are used.
- `PASS`: deterministic forward selection, swap refinement, lambda grid,
  10-term limit, tie order, and measured-grid `0.750 mm` cap are encoded.
- `PASS`: all selected basis definitions and pin mappings match
  `headheadkins.c`; fitted correction signs are correct.
- `PASS`: every selected addition is zero at `B0/C0`, so the proposed overlay
  introduces no correction discontinuity at the established start pose.
- `PASS`: raw inputs, fitter, outputs, and exact selection checkpoint are
  hash-frozen in
  `calibration_runs/20260825_0909_campaign04_t4_fit_r2_frozen`.

## Limitations

- The protocol was frozen before T3 and before a loaded-candidate run, but
  after the baseline T4 data had been inspected. “Predeclared” in the fit
  report has that limited meaning.
- The 17-term pool deliberately excludes the two collision-unidentified
  sin(2C) bases. The C-frame `bharm-c` family is also outside this fit's scope;
  it was not tested or selected.
- Three primary terms are selection-unstable across paired-abs(B) outer folds:
  `b_sin2` appears in `0/8`, while `bc_sinb_cos2c` and `bmid_cos2c` each appear
  in `3/8`. The other seven primary terms appear in `8/8`.
- Paired-B fold-to-primary surface difference is `0.044909 / 0.140937 mm`
  RMS/max; pointwise fold prediction SD is `0.028110 / 0.060568 mm`.
- The largest outer protocol correction is `0.749996 mm`, effectively on the
  declared `0.750 mm` boundary. That is a selection-stability warning, not the
  primary candidate magnitude.
- The fit-time correction cap covers the measured 76-pose grid. The loaded
  primary's dense angular audit peaks at `0.671900 mm` near `B-90/C272.8566`;
  its worst inner refit peaks at approximately `0.724369 mm`. Both remain
  below `0.750 mm`. The outer abs(B)=5 audit model reaches `0.751498 mm` on
  the dense grid despite its `0.749996 mm` measured-grid value. That outer
  model is not the overlay, but it proves the fit report's cap is not a
  continuous-envelope claim. Exact candidate-path reachability is still
  required.
- Checkpoint restoration recomputes each stored model and its metrics but does
  not independently prove that a stored outer model won its original search.
  The checkpoint is execution provenance, not an adversarial proof.
- Residual-CSV row norms use the equal-76-pose reference center. The report's
  `all 101 diagnostic rows` metric instead recenters the raw 101 rows, giving
  current/candidate `0.201016/0.711434` and `0.087176/0.207789 mm`. Recomputing
  raw-row norms about the equal-pose reference gives `0.201204/0.709875` and
  `0.087290/0.204948 mm`. Both calculations are valid, but verification must
  label and compare like with like.

## Required Next Evidence

The mode-26 T4 run may test only overlay identity, correction sign, repeatable
same-grid behavior, and implementation agreement with the frozen prediction.
Primary acceptance must use 76 equal-weight poses; raw 101-row and closure
checks remain diagnostic quality gates. T3 must remain untouched until the R2
family, coefficients, runner, hashes, and acceptance gates are archived.
