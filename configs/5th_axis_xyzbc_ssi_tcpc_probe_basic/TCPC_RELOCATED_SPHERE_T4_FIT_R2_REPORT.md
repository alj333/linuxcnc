# Relocated-Sphere T4-Only Fit Revision R2

## Operational Status

`OFFLINE CANDIDATE - NOT AUTHORIZED FOR MACHINE USE`

Revision r2 supersedes the archived lambda-30 r1 candidate for operational
planning. The r1 fitter, report, residuals, overlay, INI, analyzer, and runner
remain immutable provenance; this fitter neither reads nor writes an overlay,
INI, analyzer, runner, HAL configuration, or machine-control interface.
A separate reviewed release package and a fresh T4 verification are required.

## Frozen T4 Inputs

- campaign/mode/attempt: `2026082404 / 23 / 1`
- accepted result/state rows: `101 / 101`
- strict closures: `28`; RMS/max `0.014798 / 0.027115` mm
- equal-weight unique poses used by every fit and validation: `76`
- result, state, ordered-pose, correction-enabled, and closure contracts: `PASS`

| frozen input | SHA-256 |
| --- | --- |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-primary-results.csv` | `70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-primary-state.csv` | `dd09051f37bfc8c91e13d3617e77bc9e2aea40393237cc935e1350364a73693d` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-primary-closures.csv` | `f0fd62d8c99259c7ea76d167b1d9ce7ee68825a7cef1234f3ce3906a4a9c3021` |
| `nc_files/calibration/tcpc_relocated_sphere_t4_primary.ngc` | `bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` | `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` |

## Predeclared Selection Protocol

1. Average repeated identical `(B,C)` measurements first. Every one of the
   76 resulting poses has weight one in fitting, selection, and validation.
2. Search only the 17 existing headheadkins bases listed below. Exclude
   `bc_sinb_sin2c` and `bmid_sin2c`: nonzero-B C135/C315 observations were
   deliberately omitted for collision clearance, so their opposite sin(2C)
   phase is not physically observed.
3. Use standardized ridge fits with lambda in `{1,3,10,30,100}`. The
   intercept is unpenalized; feature mean and population standard deviation
   are learned from each training fold only.
4. Starting empty, greedily add one term at a time. At each size evaluate
   every remaining term at every lambda, then repeatedly evaluate every
   same-size one-for-one term swap with lambda retuned until the tie key no
   longer improves. Continue to 10 terms and select the best refined model
   anywhere on the 1-to-10-term path. This deterministic search is not
   exhaustive enumeration of all subsets.
5. Inner objective `J = RMS_signed-B + RMS_paired-abs(B) + 0.5*RMS_C-sector`.
   All three components are grouped leave-one-block-out predictions.
6. Reject a candidate if its modeled correction exceeds `0.750 mm`
   anywhere on the complete measured 76-pose grid in the full fit or any
   inner grouped refit.
7. Deterministic tie key after rounding metrics to `12` decimals:
   lower J, lower worst validation maximum, fewer terms, lower maximum
   correction, stronger regularization, then fixed pool-index order.
8. For every outer holdout, repeat the entire term/lambda search using only
   its training poses. No outer response participates in selection or fit.

Fixed admissible pool:

```text
c_cos, c_sin, c_cos2, c_sin2, b_sin, b_omc, b_sin2, bc_sinb_sinc, bc_omcb_sinc, bc_omcb_sin2c, bc_sinb_cosc, bc_omcb_cosc, bc_sinb_cos2c, bmid_base, bmid_cosc, bmid_sinc, bmid_cos2c
```

## Primary Candidate

One primary model is frozen: `10` terms, lambda `10`.

```text
c_cos, b_sin, b_sin2, bc_sinb_sinc, bc_omcb_sin2c, bc_sinb_cos2c, bmid_base, bmid_cosc, bmid_sinc, bmid_cos2c
```

- selection objective J: `0.286445518`
- inner signed-B RMS/max: `0.110795 / 0.292920` mm
- inner paired-abs(B) RMS/max: `0.105447 / 0.261705` mm
- inner C-sector RMS/max: `0.140406 / 0.436565` mm
- primary modeled correction maximum: `0.670166 mm`
- primary plus inner-refit correction maximum: `0.722851 mm`
- design rank: `10/10`; raw/scaled condition: `3.336e+00 / 2.745`

### Forward-Only Reconciliation

The forward-only result is retained as a method audit, but only the
swap-refined result above is the r2 primary.

| method | terms | lambda | J | correction max |
| --- | ---: | ---: | ---: | ---: |
| forward only | `8` | `10` | `0.295360638` | `0.743763` |
| swap refined, primary | `10` | `10` | `0.286445518` | `0.722851` |

Forward-only terms:

```text
c_cos, b_sin, bc_sinb_sinc, bc_omcb_sin2c, bc_sinb_cos2c, bmid_base, bmid_sinc, bmid_cos2c
```

| weighting | current | r2 offline prediction |
| --- | ---: | ---: |
| 76 equal unique poses | `0.219602 / 0.709875` | `0.085763 / 0.204948` |
| all 101 diagnostic rows | `0.201016 / 0.711434` | `0.087176 / 0.207789` |

### Forward Path

The selected row is the global winner on the predeclared path, not
necessarily the final 10-term step.

| terms | refined set | swap passes | lambda | J | signed B | paired abs(B) | C sector | correction max | selected |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `bc_omcb_sin2c` | 0 | 10 | `0.449187760` | `0.176332 / 0.511938` | `0.179195 / 0.510432` | `0.187322 / 0.548992` | `0.688665` |  |
| 2 | `c_cos,bc_omcb_sin2c` | 0 | 10 | `0.406003512` | `0.160791 / 0.511971` | `0.163640 / 0.510464` | `0.163145 / 0.549046` | `0.627988` |  |
| 3 | `c_cos,bc_sinb_sinc,bc_omcb_sin2c` | 0 | 30 | `0.385119132` | `0.150493 / 0.451614` | `0.148426 / 0.437457` | `0.172400 / 0.550985` | `0.632858` |  |
| 4 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c` | 0 | 30 | `0.368041071` | `0.142734 / 0.434651` | `0.140995 / 0.412497` | `0.168623 / 0.572102` | `0.675125` |  |
| 5 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c` | 0 | 30 | `0.351916880` | `0.136505 / 0.392172` | `0.134499 / 0.366990` | `0.161826 / 0.549020` | `0.728460` |  |
| 6 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_sinc` | 0 | 30 | `0.335271196` | `0.126390 / 0.313055` | `0.125294 / 0.298777` | `0.167175 / 0.554356` | `0.726849` |  |
| 7 | `c_cos,c_cos2,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_sinc` | 1 | 10 | `0.319549877` | `0.118660 / 0.259743` | `0.119075 / 0.257403` | `0.163630 / 0.502237` | `0.743740` |  |
| 8 | `c_cos,c_cos2,c_sin2,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_sinc` | 0 | 10 | `0.320820806` | `0.119059 / 0.260953` | `0.119532 / 0.259284` | `0.164461 / 0.500603` | `0.743214` |  |
| 9 | `c_cos,c_sin,b_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | 2 | 10 | `0.312173061` | `0.119847 / 0.308771` | `0.113001 / 0.257821` | `0.158650 / 0.476372` | `0.749275` |  |
| 10 | `c_cos,b_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | 3 | 10 | `0.286445518` | `0.110795 / 0.292920` | `0.105447 / 0.261705` | `0.140406 / 0.436565` | `0.722851` | `YES` |

## Selection-Adjusted Outer Validation

Every row below repeats the complete forward term and lambda selection inside
each outer training fold. Metrics are absolute-center prediction errors on
the untouched outer poses; they are not fixed-family refits.

The antipodal test groups C sectors modulo 180 degrees, holding C0/C180,
C45/C225, C90/C270, or C135/C315 out together. It tests transfer when both
opposite phases are absent from the outer training set.

| outer scheme | RMS / max mm | worst group / max | selected terms | lambda counts `lambda:folds` | protocol correction max |
| --- | ---: | ---: | ---: | --- | ---: |
| signed-B | `0.122241 / 0.319849` | B-90 / `0.319849` | `8-10` | `1:0, 3:0, 10:14, 30:1, 100:0` | `0.749541` |
| paired-abs-B | `0.110892 / 0.267291` | abs(B)90 / `0.267291` | `8-10` | `1:0, 3:0, 10:7, 30:1, 100:0` | `0.749996` |
| C-sector | `0.201632 / 0.655231` | C270 / `0.655231` | `6-10` | `1:0, 3:0, 10:8, 30:0, 100:0` | `0.749336` |
| antipodal-C-pair | `0.253374 / 0.837828` | C90/C270 / `0.837828` | `6-10` | `1:0, 3:0, 10:4, 30:0, 100:0` | `0.744650` |

No primary, inner, or outer-selection model exceeds the `0.750 mm`
bound; the largest protocol value is `0.749996 mm`.
C-sector and antipodal results remain the controlling extrapolation checks.
C135/C315 exists only at B0, so no conclusion is made about those sectors at
nonzero B.

### Outer Fold Detail

| scheme | held group | poses | lambda | terms | held RMS / max | protocol correction max |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| signed-B | B-90 | 4 | 10 | `c_cos,c_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.260234 / 0.319849` | `0.704313` |
| signed-B | B-60 | 4 | 10 | `c_cos,c_sin,c_cos2,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.172875 / 0.229512` | `0.706213` |
| signed-B | B-45 | 4 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.145433 / 0.180657` | `0.725946` |
| signed-B | B-30 | 4 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.088146 / 0.108554` | `0.749541` |
| signed-B | B-15 | 6 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.089990 / 0.105682` | `0.747451` |
| signed-B | B-10 | 6 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.093033 / 0.121645` | `0.746916` |
| signed-B | B-5 | 6 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.089838 / 0.114291` | `0.747253` |
| signed-B | B+0 | 8 | 10 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.094467 / 0.140426` | `0.736263` |
| signed-B | B+5 | 6 | 10 | `c_cos,c_sin,c_cos2,b_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.082483 / 0.101905` | `0.735768` |
| signed-B | B+10 | 6 | 10 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.070644 / 0.096032` | `0.738751` |
| signed-B | B+15 | 6 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.077632 / 0.102744` | `0.742973` |
| signed-B | B+30 | 4 | 10 | `c_cos,c_sin,c_cos2,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.091477 / 0.141562` | `0.736525` |
| signed-B | B+45 | 4 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.113519 / 0.176239` | `0.713598` |
| signed-B | B+60 | 4 | 30 | `c_cos,c_sin,c_cos2,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc` | `0.150076 / 0.199209` | `0.725664` |
| signed-B | B+90 | 4 | 10 | `c_cos,c_sin,b_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.178308 / 0.242052` | `0.743591` |
| paired-abs-B | abs(B)0 | 8 | 10 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.094467 / 0.140426` | `0.736263` |
| paired-abs-B | abs(B)5 | 12 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.082311 / 0.116420` | `0.749996` |
| paired-abs-B | abs(B)10 | 12 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.083105 / 0.125056` | `0.726106` |
| paired-abs-B | abs(B)15 | 12 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.082418 / 0.100346` | `0.737026` |
| paired-abs-B | abs(B)30 | 8 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.090647 / 0.128293` | `0.728199` |
| paired-abs-B | abs(B)45 | 8 | 10 | `c_cos,c_sin,c_cos2,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc` | `0.109839 / 0.168215` | `0.745442` |
| paired-abs-B | abs(B)60 | 8 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.153067 / 0.205687` | `0.711819` |
| paired-abs-B | abs(B)90 | 8 | 30 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cosc,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc` | `0.182963 / 0.267291` | `0.734180` |
| C-sector | C0 | 15 | 10 | `c_cos,c_sin,b_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_sinc,bmid_cos2c` | `0.140969 / 0.307491` | `0.700095` |
| C-sector | C45 | 7 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.091307 / 0.121471` | `0.749336` |
| C-sector | C90 | 15 | 10 | `c_cos,c_sin,c_cos2,b_sin,b_omc,b_sin2,bc_sinb_sinc,bmid_cosc,bmid_sinc` | `0.236368 / 0.510852` | `0.695031` |
| C-sector | C135 | 1 | 10 | `c_cos,b_sin,b_sin2,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.034667 / 0.034667` | `0.720344` |
| C-sector | C180 | 15 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_sinc,bmid_cos2c` | `0.151132 / 0.285222` | `0.724563` |
| C-sector | C225 | 7 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.095776 / 0.112885` | `0.743461` |
| C-sector | C270 | 15 | 10 | `c_cos,c_cos2,b_sin,b_omc,bc_sinb_cosc,bmid_cosc` | `0.313222 / 0.655231` | `0.343256` |
| C-sector | C315 | 1 | 10 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.125155 / 0.125155` | `0.747290` |
| antipodal-C-pair | C0/C180 | 30 | 10 | `c_cos,b_sin,b_omc,bc_sinb_sinc,bc_sinb_cos2c,bmid_sinc,bmid_cos2c` | `0.198609 / 0.583167` | `0.718367` |
| antipodal-C-pair | C45/C225 | 14 | 10 | `c_cos,c_sin,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.094149 / 0.120987` | `0.733349` |
| antipodal-C-pair | C90/C270 | 30 | 10 | `c_cos,c_sin,b_omc,bc_sinb_sinc,bc_sinb_cos2c,bmid_cosc` | `0.344229 / 0.837828` | `0.694631` |
| antipodal-C-pair | C135/C315 | 2 | 10 | `c_cos,b_sin,bc_sinb_sinc,bc_omcb_sin2c,bc_sinb_cos2c,bmid_base,bmid_cosc,bmid_sinc,bmid_cos2c` | `0.091672 / 0.125074` | `0.744650` |

## Paired-B Stability

Stability uses the eight selection-adjusted paired-abs(B) outer fits. Missing
terms are aligned as zero coefficient deltas. Prediction differences compare
each fold-selected correction surface with the primary surface over all 76
measured poses.

- fold-to-primary prediction difference RMS/max: `0.044909 / 0.140937` mm
- pointwise fold prediction SD RMS/max: `0.028110 / 0.060568` mm

## Exact Offline Pin Totals

`delta` is added to the frozen baseline pin. Nonselected terms have zero
delta. These values are predictions only; this report is not a HAL overlay.
Coefficient SD and max difference include selection changes across the eight
paired-B outer folds.

| selected | basis / pin stem | current XYZ | delta XYZ | predicted total XYZ | abs-B frequency | coefficient SD | max difference | direction |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| YES | `c_cos` / `headheadkins.charm.cos.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.020461249, +0.076365546, +0.017039535` | `-0.020461249, +0.076365546, +0.017039535` | `8/8` | `0.010254` | `0.021126` | `8/8` |
| no | `c_sin` / `headheadkins.charm.sin.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `+0.000000000, +0.000000000, +0.000000000` | `+0.000000000, +0.000000000, +0.000000000` | `7/8` | `0.010340` | `0.032039` | `n/a` |
| no | `c_cos2` / `headheadkins.charm.cos2.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `+0.000000000, +0.000000000, +0.000000000` | `+0.000000000, +0.000000000, +0.000000000` | `1/8` | `0.005369` | `0.016236` | `n/a` |
| no | `c_sin2` / `headheadkins.charm.sin2.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `+0.000000000, +0.000000000, +0.000000000` | `+0.000000000, +0.000000000, +0.000000000` | `0/8` | `0.000000` | `0.000000` | `n/a` |
| YES | `b_sin` / `headheadkins.bharm-m.sin.[xyz]` | `+0.015577123, +0.060508594, +0.312123080` | `+0.020075820, +0.005582796, +0.092144803` | `+0.035652943, +0.066091390, +0.404267883` | `8/8` | `0.011516` | `0.056805` | `8/8` |
| no | `b_omc` / `headheadkins.bharm-m.omc.[xyz]` | `+0.141330042, +0.111703959, -0.338104991` | `+0.000000000, +0.000000000, +0.000000000` | `+0.141330042, +0.111703959, -0.338104991` | `0/8` | `0.000000` | `0.000000` | `n/a` |
| YES | `b_sin2` / `headheadkins.bharm-m.sin2.[xyz]` | `-0.013271805, +0.050707231, -0.156014210` | `+0.010074165, -0.036089433, -0.015170060` | `-0.003197640, +0.014617798, -0.171184270` | `0/8` | `0.000000` | `0.040424` | `0/8` |
| YES | `bc_sinb_sinc` / `headheadkins.bcross.sinb-sinc.[xyz]` | `-0.006371196, +0.325723886, +0.130042953` | `-0.069868412, +0.159541990, -0.015112802` | `-0.076239608, +0.485265876, +0.114930151` | `8/8` | `0.007492` | `0.018280` | `8/8` |
| no | `bc_omcb_sinc` / `headheadkins.bcross.omcb-sinc.[xyz]` | `-0.074687973, +0.012622224, -0.001729459` | `+0.000000000, +0.000000000, +0.000000000` | `-0.074687973, +0.012622224, -0.001729459` | `0/8` | `0.000000` | `0.000000` | `n/a` |
| YES | `bc_omcb_sin2c` / `headheadkins.bcross.omcb-sin2c.[xyz]` | `-0.017723675, -0.255875638, -0.055414262` | `-0.023870227, +0.474515250, -0.090829591` | `-0.041593902, +0.218639612, -0.146243853` | `8/8` | `0.031734` | `0.087612` | `8/8` |
| no | `bc_sinb_cosc` / `headheadkins.bcross.sinb-cosc.[xyz]` | `-0.048238059, -0.063070849, -0.018239994` | `+0.000000000, +0.000000000, +0.000000000` | `-0.048238059, -0.063070849, -0.018239994` | `1/8` | `0.014505` | `0.043860` | `n/a` |
| no | `bc_omcb_cosc` / `headheadkins.bcross.omcb-cosc.[xyz]` | `-0.030283175, +0.071683484, +0.000165632` | `+0.000000000, +0.000000000, +0.000000000` | `-0.030283175, +0.071683484, +0.000165632` | `0/8` | `0.000000` | `0.000000` | `n/a` |
| YES | `bc_sinb_cos2c` / `headheadkins.bcross.sinb-cos2c.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.027710790, +0.069637932, -0.003817325` | `-0.027710790, +0.069637932, -0.003817325` | `3/8` | `0.033769` | `0.075046` | `3/8` |
| YES | `bmid_base` / `headheadkins.bmid.base.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `+0.049306652, +0.071617641, -0.011117499` | `+0.049306652, +0.071617641, -0.011117499` | `8/8` | `0.019384` | `0.033624` | `8/8` |
| YES | `bmid_cosc` / `headheadkins.bmid.cosc.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.094209330, +0.019592845, +0.003604714` | `-0.094209330, +0.019592845, +0.003604714` | `8/8` | `0.014241` | `0.028312` | `8/8` |
| YES | `bmid_sinc` / `headheadkins.bmid.sinc.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.032916421, -0.129517107, +0.007589668` | `-0.032916421, -0.129517107, +0.007589668` | `8/8` | `0.016566` | `0.049432` | `8/8` |
| YES | `bmid_cos2c` / `headheadkins.bmid.cos2c.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.010555597, -0.034914537, -0.004599347` | `-0.010555597, -0.034914537, -0.004599347` | `3/8` | `0.018662` | `0.036764` | `3/8` |

Machine-readable pin audit: `tcpc-relocated-sphere-t4-fit-r2-pins.csv`.
Per-observation predictions: `tcpc-relocated-sphere-t4-fit-r2-residuals.csv`.

## Generated Artifact Hashes

| artifact | SHA-256 |
| --- | --- |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/fit_tcpc_relocated_sphere_t4_r2.py` | `faae48919e01f5f7cf5a9e8f29da40fc77bdf359d21bec1848bdcdfb979c71bb` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-fit-r2-residuals.csv` | `8de7e98a4767eba6545ee3e6f3a0688bf56e43427153bea79c08c4787f59ade1` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-fit-r2-pins.csv` | `d3481e51cd98b6fc4c8ac8484a781b6fe88321ab371b53bc5081248f72c1e2b6` |

## Decision

Freeze this one r2 model as the campaign-04 T4-only offline candidate.
It supersedes r1/lambda30 for future operational planning because r1 was
over-regularized after sparse-family selection and its fixed-family CV did
not account for term selection. R2 remains unvalidated on a fresh run.

Do not load these totals directly. A separate revision-specific overlay,
configured-limit replay, analyzer, immutable archive, operator review, and
fresh T4 verification must be completed before any machine release.
