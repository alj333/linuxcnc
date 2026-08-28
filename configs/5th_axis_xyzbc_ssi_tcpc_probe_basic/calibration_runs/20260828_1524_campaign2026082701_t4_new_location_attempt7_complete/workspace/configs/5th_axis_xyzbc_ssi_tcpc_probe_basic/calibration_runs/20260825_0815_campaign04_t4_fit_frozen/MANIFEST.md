# Campaign 2026082404 T4-Only Fit Freeze

Frozen `2026-08-25T08:15:26+07:00` before any T3 measurement row existed.
The fitter has no T3 input path. No LinuxCNC, HAL, configuration, tool-table,
or machine-control operation was performed by the fit.

## Input Identity

```text
T4 runner   bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2
results     70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468
state       dd09051f37bfc8c91e13d3617e77bc9e2aea40393237cc935e1350364a73693d
closures    f0fd62d8c99259c7ea76d167b1d9ce7ee68825a7cef1234f3ce3906a4a9c3021
base HAL    b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778
```

The validated acquisition contains 101 result rows, 101 state rows, 28
passing closures, and 76 equal-weight unique `(B,C)` poses.

## Frozen Candidate

- Nine existing `headheadkins` additive correction terms.
- Standardized ridge regression, lambda `30.0`.
- Repeated identical poses are averaged before fitting.
- Rigid geometry, B/C zeros, active tool length, and unselected correction
  pins remain unchanged.
- Predicted all-row centered RMS/max improves from
  `0.201016 / 0.711434 mm` to `0.099990 / 0.237606 mm`.
- Nested paired-absolute-B validation is `0.109287 / 0.253190 mm`.
- C270 remains the principal transfer limitation; the candidate is not valid
  for extrapolation into unmeasured C sectors.

The exact term family, fitted deltas, predicted absolute pin totals,
cross-validation, sensitivity results, and predeclared holdout gates are in
`TCPC_RELOCATED_SPHERE_T4_FIT_REPORT.md`.

## Frozen Output Identity

```text
fitter      9a7adf0ad9552d9543fdfc38cc46c502ab58abe9b09d7eeb0cb08475df51a5cc
fit report  f1e587244565a07750b00bc2e36f250f5e5c91c60eb75c5c6748e36feb82a229
residuals   fbf85a922c8de6cfc7993d060f3e14b3adde2abaa272b77d52dbaf486df6b31d
```

The candidate is an offline prediction, not a production release. Following
the operator's direction, a separate T4 loaded-candidate verification stage
will be prepared before the T3 holdout. It must use separate output files and
must not overwrite or append to this acquisition.

`SHA256SUMS` covers every other regular file in this archive.
