# Relocated-Sphere T4-Only Fit Report

This report freezes the candidate before the T3 holdout is read. The fitter
has no T3 input path and performs no LinuxCNC, HAL, or machine-control action.
The values below are offline predictions, not authorized machine settings.

## Frozen Inputs

- campaign/mode/attempt: `2026082404 / 23 / 1`
- accepted result/state rows: `101 / 101`
- strict closures: `28`; RMS/max `0.014798 / 0.027115` mm
- equal-weight unique poses: `76`
- all result, state, pose, correction-enabled, and closure contracts: `PASS`

| frozen raw input | SHA-256 |
| --- | --- |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-primary-results.csv` | `70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-primary-state.csv` | `dd09051f37bfc8c91e13d3617e77bc9e2aea40393237cc935e1350364a73693d` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-relocated-sphere-t4-primary-closures.csv` | `f0fd62d8c99259c7ea76d167b1d9ce7ee68825a7cef1234f3ce3906a4a9c3021` |
| `nc_files/calibration/tcpc_relocated_sphere_t4_primary.ngc` | `bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` | `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` |

## Current Error

Metrics are three-dimensional centered RMS / maximum in millimetres.
The official 101-row current metric is `0.201016 / 0.711434`.
After averaging repeated identical poses, the current metric is `0.219602 / 0.709875`.
The largest raw row is B-90/C270. Same-pose closures are an order of
magnitude smaller, so the dominant error is pose-dependent rather than
probe repeatability or run drift.

Signed-pair decomposition uses `(B+ - B-)/2` for the odd component and
`(B+ + B-)/2 - B0(C)` for the even component.

| abs(B) | current odd | candidate odd | current even | candidate even |
| ---: | ---: | ---: | ---: | ---: |
| 5 | `0.075324 / 0.090960` | `0.068743 / 0.077572` | `0.092427 / 0.113840` | `0.089732 / 0.110245` |
| 10 | `0.079314 / 0.124646` | `0.063775 / 0.086999` | `0.117842 / 0.183540` | `0.110229 / 0.179069` |
| 15 | `0.089472 / 0.143140` | `0.068767 / 0.092154` | `0.131266 / 0.159514` | `0.111603 / 0.159332` |
| 30 | `0.108901 / 0.208919` | `0.050818 / 0.092614` | `0.174433 / 0.261878` | `0.103916 / 0.175732` |
| 45 | `0.152817 / 0.263490` | `0.080606 / 0.098735` | `0.271580 / 0.452704` | `0.127673 / 0.180453` |
| 60 | `0.171351 / 0.300069` | `0.064577 / 0.095575` | `0.348213 / 0.574761` | `0.174737 / 0.255161` |
| 90 | `0.183268 / 0.254299` | `0.072119 / 0.099658` | `0.412122 / 0.611614` | `0.173845 / 0.210575` |

The even component grows most strongly with B and is dominant at high B,
especially C270. A smaller odd-B component is also repeatable. This supports
surface terms with both B-sign parity classes; it does not support replacing
the error with a single B/C zero or rigid translation.

## Frozen Candidate

Primary estimator: standardized ridge regression with lambda `30.0`.
Each distinct `(B,C)` pose has total weight one. Repeated C0 closure rows
are averaged within their pose and do not receive extra model weight.
The centered scalar design has rank `9/9`, raw condition
`3.475e+00`, and standardized condition `2.536`.

The fixed nine-term family is:

```text
bc_omcb_sin2c, c_cos, bc_sinb_sinc, bmid_sinc, b_sin, bc_sinb_cos2c, bmid_cosc, bmid_base, c_sin
```

`bc_omcb_sin2c` follows the existing implementation name; its actual basis
is `(1-cos(B))*sin(C)^2`. Terms proportional to `sin(B)*sin(2C)` and
`sin(B)^2`-midband `sin(2C)` remain frozen at zero because C135/C315
are collision omissions at nonzero B. Their opposite `sin(2C)` phase is
therefore not physically observed.

| weighting | current | candidate prediction |
| --- | ---: | ---: |
| 76 equal unique poses | `0.219602 / 0.709875` | `0.101210 / 0.235391` |
| all 101 diagnostic rows | `0.201016 / 0.711434` | `0.099990 / 0.237606` |

## T4 Validation

All fits below use T4 only. Fixed-family group holdouts refit the coefficients
without the named group and predict its absolute center from the remaining
groups.

| validation | RMS / max mm | worst group / max mm |
| --- | ---: | ---: |
| leave one signed B block out | `0.119709 / 0.285163` | B-60 / `0.285163` |
| leave one paired abs(B) group out | `0.115245 / 0.274805` | abs(B)60 / `0.274805` |
| leave one C sector out | `0.162075 / 0.550587` | C270 / `0.550587` |

Nested leave-abs(B) validation chooses lambda only inside each outer training
fold from `{1,3,10,30,100}`. Its outer metric is
`0.109287 / 0.253190`. This is a sensitivity check; it does not
change the frozen primary lambda `30.0`.

| outer held abs(B) | inner-selected lambda | outer RMS / max mm |
| ---: | ---: | ---: |
| 0 | 10 | `0.098475 / 0.136052` |
| 5 | 10 | `0.082073 / 0.113481` |
| 10 | 10 | `0.082578 / 0.125264` |
| 15 | 10 | `0.080181 / 0.100348` |
| 30 | 10 | `0.080039 / 0.122515` |
| 45 | 10 | `0.095087 / 0.158991` |
| 60 | 10 | `0.133884 / 0.178410` |
| 90 | 3 | `0.201046 / 0.253190` |

C270 is essential training evidence. Leaving it out is the worst C-sector
test, so this surface must not be extrapolated to unmeasured C sectors.
The planned T3 poses are all within the measured C quadrants; T3 tests
probe-length transfer, not an unmeasured-C extrapolation.

## Lambda And Weighting Sensitivity

| lambda | equal-pose train | leave signed B | leave abs(B) | leave C |
| ---: | ---: | ---: | ---: | ---: |
| 0 | `0.083933 / 0.195405` | `0.108271 / 0.253088` | `0.109315 / 0.294595` | `0.247108 / 0.753438` |
| 1 | `0.083979 / 0.197032` | `0.107596 / 0.254095` | `0.108364 / 0.280034` | `0.165205 / 0.483513` |
| 3 | `0.084318 / 0.200245` | `0.106743 / 0.256086` | `0.106971 / 0.253190` | `0.135322 / 0.341956` |
| 10 | `0.087289 / 0.210861` | `0.107314 / 0.262691` | `0.105822 / 0.248697` | `0.139333 / 0.407611` |
| 30 | `0.101210 / 0.235391` | `0.119709 / 0.285163` | `0.115245 / 0.274805` | `0.162075 / 0.550587` |
| 100 | `0.140076 / 0.411972` | `0.156675 / 0.463352` | `0.151676 / 0.453603` | `0.194883 / 0.665278` |

A row-weighted refit changes the predicted adjustment over the 76 unique
poses by at most `0.040668 mm`. The primary remains
the equal-pose fit because repeated C0 closure samples are repeatability
evidence, not a reason to weight C0 more heavily in calibration.

## Offline Pin Mapping

These are analysis values only. `delta` is the fitted addition to the current
pin; `predicted total` is shown for audit and is not an executable HAL block.
Fold SD is the vector norm of coefficient variation across leave-abs(B) fits.

| basis term | existing pin stem | current XYZ | delta XYZ | predicted total XYZ | fold SD | direction | weighting delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `bc_omcb_sin2c` | `headheadkins.bcross.omcb-sin2c.[xyz]` | `-0.017723675, -0.255875638, -0.055414262` | `-0.013420920, +0.402913343, -0.071557787` | `-0.031144595, +0.147037705, -0.126972049` | `0.037693` | `8/8` | `0.027625` |
| `c_cos` | `headheadkins.charm.cos.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.018417307, +0.059820553, +0.012777450` | `-0.018417307, +0.059820553, +0.012777450` | `0.004546` | `8/8` | `0.009933` |
| `bc_sinb_sinc` | `headheadkins.bcross.sinb-sinc.[xyz]` | `-0.006371196, +0.325723886, +0.130042953` | `-0.056685693, +0.129439728, -0.012261330` | `-0.063056889, +0.455163614, +0.117781623` | `0.009914` | `8/8` | `0.010680` |
| `bmid_sinc` | `headheadkins.bmid.sinc.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.004859883, -0.091165546, +0.003700491` | `-0.004859883, -0.091165546, +0.003700491` | `0.006140` | `8/8` | `0.014942` |
| `b_sin` | `headheadkins.bharm-m.sin.[xyz]` | `+0.015577123, +0.060508594, +0.312123080` | `+0.022257459, -0.016855720, +0.065769744` | `+0.037834582, +0.043652874, +0.377892824` | `0.008047` | `8/8` | `0.006047` |
| `bc_sinb_cos2c` | `headheadkins.bcross.sinb-cos2c.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.022482124, +0.056498110, -0.003097114` | `-0.022482124, +0.056498110, -0.003097114` | `0.001109` | `8/8` | `0.007198` |
| `bmid_cosc` | `headheadkins.bmid.cosc.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.077381904, +0.032648437, +0.007022422` | `-0.077381904, +0.032648437, +0.007022422` | `0.006877` | `8/8` | `0.016847` |
| `bmid_base` | `headheadkins.bmid.base.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `+0.039607854, +0.060817434, -0.009749765` | `+0.039607854, +0.060817434, -0.009749765` | `0.016480` | `8/8` | `0.010375` |
| `c_sin` | `headheadkins.charm.sin.[xyz]` | `+0.000000000, +0.000000000, +0.000000000` | `-0.022394938, -0.013148382, +0.002711441` | `-0.022394938, -0.013148382, +0.002711441` | `0.003550` | `8/8` | `0.007559` |

The candidate may require up to the maximum adjustment listed in the residual
CSV. It must not be loaded before holdout evaluation, a fresh configured-limit
replay, and an explicit operator release.

## Frozen T3 Acceptance Gates

The following gates were fixed without reading T3 values:

1. The completed T3 schema, state, pose, contact-quality, and all 14 closure
   contracts must pass. A partial or reseated-probe splice is rejected.
2. Apply this exact nine-term coefficient delta offline with no T3 refit, no
   lambda change, no term selection, and a separately centered constant sphere
   center for the T3 leg.
3. Candidate T3 centered RMS must improve current RMS by both at least 10% and
   at least 0.010 mm.
4. Candidate T3 maximum must improve current maximum by both at least 10% and
   at least 0.020 mm.
5. Candidate RMS must improve separately for the paired abs(B)=45 and abs(B)=90
   groups. B0 RMS may not worsen by more than 0.010 mm.
6. No individual T3 pose residual norm may worsen by more than 0.050 mm.
7. Passing these offline gates freezes a proposed parameter revision only. It
   does not authorize a HAL edit or machine motion. Live release still requires
   reviewed parameter bounds, configured-limit replay, a new immutable archive,
   and operator authorization.

If any gate fails, reject this family. Do not inspect T3 to choose another
family; a different family requires a new untouched verification campaign.

## Decision

Freeze this nine-term lambda-30 candidate as the sole campaign-04 offline
prediction. Keep all rigid geometry, B/C zeros, and live correction pins
unchanged until the T3 holdout is completed and evaluated against the gates
above.

Detailed per-row predictions: `tcpc-relocated-sphere-t4-fit-residuals.csv`
