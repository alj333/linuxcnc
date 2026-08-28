# TCPC Length-Aware T4 Attempt 2 Closeout

Status: `PASS - T4 q=0 common-bank validation complete`

## Disposition

The sealed 101-pose T4 acquisition passes its formal centered-error, closure, model-state, and probe-transaction contracts. It validates the length-aware implementation and common correction bank at T4, where `q=0`. It does not validate the T3 differential bank, other tool lengths, a different table location, or production release.

- formal raw-101 RMS / max: `0.105164 / 0.245253 mm`
- formal equal-76 RMS / max: `0.107589 / 0.241710 mm`
- formal limits: `0.120 / 0.280 mm`
- closure RMS / max: `0.022237 / 0.040366 mm` across `28` closures

## Reproducible Method

The baseline is not inferred from a later candidate run. It is the exact mode-23 T4 result owned by the pre-machine campaign-04 fit freeze at `20260825_0815_campaign04_t4_fit_frozen`; that archive inventory and result hash are both verified. Attempt 2 is read only from its completion archive.

For each sequence, B is rounded to the contract integer and C is rounded modulo 360 with a maximum 0.01 degree tolerance. The resulting 101-key sequence must match digest `51a4170ffa874c5757fd8d097200e5f5f67b627c1b2d32d951c056b4de88fd9f` and collapses by first canonical occurrence to 76 equal-weight poses. Repeated-pose centers are arithmetic means.

At T4, the sealed model has `q(T4)=0`, so the offline prediction is:

```text
predicted center(B,C) = frozen H0 baseline center(B,C) + S(B,C)
centered residual i    = center i - mean(center field)
RMS                    = sqrt(mean(norm(centered residual i)^2))
```

Baseline, prediction, and fresh actual fields are centered independently. This removes only the unidentifiable global sphere-center translation; it does not align, rotate, scale, or refit the pose fields.

## Baseline Comparison

| weighting | frozen H0 baseline | sealed H0+S prediction | fresh actual | actual reduction from baseline |
| --- | ---: | ---: | ---: | ---: |
| raw 101 rows RMS / max | `0.201016 / 0.711434` | `0.104889 / 0.250372` | `0.105164 / 0.245253` | `47.7% / 65.5%` |
| equal 76 poses RMS / max | `0.219602 / 0.709875` | `0.107256 / 0.247250` | `0.107589 / 0.241710` | `51.0% / 66.0%` |

Actual residual norm improves at `66/76` poses and worsens at `10/76`; the prediction expected `67` improvements and `9` worsenings. The largest improvement is `0.496478 mm` at `B-90/C270`. The largest local worsening is `0.086446 mm` at `B+90/C180`; this is diagnostic and does not exceed the run's absolute maximum-error contract.

## Spatial Agreement

- raw-101 actual-minus-predicted centered-pattern RMS / max: `0.038513 / 0.076969 mm`
- equal-76 actual-minus-predicted centered-pattern RMS / max: `0.038824 / 0.074904 mm`
- equal-76 uncentered mean translation actual-minus-predicted XYZ: `[+0.060756, +0.040999, -0.011676] mm`, norm `0.074219 mm`
- centered-pattern per-axis RMS XYZ: `[+0.029262, +0.024221, +0.008026] mm`
- largest centered-pattern discrepancy: `B+30/C270`, vector `[+0.064843, +0.035160, +0.013026] mm`, norm `0.074904 mm`

The mean translation is reported rather than hidden, but it is excluded from TCPC pose-field scoring by the frozen centering convention. It can include machine-coordinate drift, artifact-location change, probe seating, and common acquisition offset and cannot by itself identify a B-axis or rail correction.

### B Groups

All group RMS values below use the one global equal-76 mean for each field; no group is recentered.

| group | poses | baseline RMS | prediction RMS | actual RMS | actual-prediction pattern RMS |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 | `8` | `0.133686` | `0.091999` | `0.095381` | `0.028297` |
| positive B | `34` | `0.191100` | `0.096791` | `0.101892` | `0.049888` |
| negative B | `34` | `0.258984` | `0.119810` | `0.115551` | `0.026306` |
| positive high B (>=30) | `16` | `0.232068` | `0.109829` | `0.113146` | `0.053998` |
| negative high B (<=-30) | `16` | `0.346272` | `0.140630` | `0.140874` | `0.029503` |
| low tilt (|B|<=15) | `44` | `0.141818` | `0.091062` | `0.090123` | `0.035025` |

The largest exact signed-B group discrepancy is `B+90` at `0.066246 mm` RMS. The largest C-sector discrepancy is `C270` at `0.042327 mm` RMS. The positive/negative asymmetry remains visible, but a single T4 sphere field cannot separate B-axis alignment from X/Y/Z rail, head, spindle, seating, or table-position effects.

## Closure And Pulse Evidence

All `28` closures pass `<= 0.050 mm`; RMS / max are `0.022237 / 0.040366 mm`. The worst is block `905` (`9->72`) at `0.040366 mm`. Closure measures within-run return consistency, not absolute TCPC accuracy or mechanical-axis alignment.

The trace contains `823/823/808` terminal raw/mux/gated counts. Exactly `808` contacts reached motion. The bounded filter accepted `14` delayed post-contact raw/mux edges in `14` transactions and `1` inter-contact edge in `1` transaction; direct duplicates were `0`. No extra edge reached the gated motion input.

These extras remain evidence of probe-system electrical susceptibility. Their acceptance means the logged second pulses occurred outside the one gated G38 contact and passed release/consistency guards; it does not mean future pulse faults may be ignored without the same contract. The new-session manual-deflection check was explicitly waived because T4 had not been reseated, while two passive 30-second quiet checks passed. That waiver is retained as a qualification caveat.

## Next Stage

1. Freeze this T4 result without retuning the common bank.
2. Run the fresh T3 length-aware validation under the same model ID and coefficient set. T3 is the required `q=1` differential-bank check and must remain an untouched verification set.
3. If T3 passes, test the long-tool endpoint near 425-430 mm with the planned dial-gauge method; a second 100-115 mm endpoint remains preferable. The software envelope alone is not accuracy evidence outside the T3-T4 bracket.
4. Use a later second table position to distinguish repeatable TCPC/B-axis structure from X/Y/Z rail and machine-volume effects. Do not infer axis correction tables from this single sphere location.

The T4 common-bank implementation is accepted for the next validation stage, not for production promotion. The roughly 0.108 mm equal-pose RMS, 0.242 mm worst pose, 0.022 mm closure RMS, and 0.075 mm worst prediction discrepancy do not support a general sub-10-micron machine claim.

## Sealed Provenance

Analyzer: `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_length_aware_t4_attempt2.py` SHA-256 `7371444295d66b6fcd7e75a77689726a46bd1a494c51a272fa246bcc95554b08`.

| input | computed and required SHA-256 |
| --- | --- |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260825_0815_campaign04_t4_fit_frozen/SHA256SUMS` | `d9cad3f41abaac5af29aed4e60d4ebc2c562f9607639ba3b4c6bb0498b69f76d` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260825_0815_campaign04_t4_fit_frozen/tcpc-relocated-sphere-t4-primary-results.csv` | `70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/SHA256SUMS` | `546377e7ed7c98f4e24e6fc239b05810ea664ea101e6bd5d79e3c36558f9a880` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-results.csv` | `ff1d93d954bd1e5a5370db26adaf6d77c1eb4c2823ef5bd5c6fbe1ec6e36e47c` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-state.csv` | `ff6f0362a0a83505383044cb0ca1fe00f1d4ab6f5a882266720cb067fe75ed49` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-model-state.csv` | `fb17c1295f9def5502fd25ef15bf01d6e8a10d61b8ddd4ebde62a8bde0bba43a` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-closures.csv` | `aca7c2f436bd49bbfdcb437d0a214f7312f92241dbb5c24ec7d6fbe15c01a552` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-contact-trace.csv` | `95d2024c53203c6b944961bfd2f82eda28bd7b408a73d6b453e49229c341f777` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-gap-trace.csv` | `02c5eb249467da28e611147a4c4baae5203528f77d1a83313bf7fd7a915d67a4` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc_length_aware_t4_validation_2026082601_attempt2.ngc` | `d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/validate_tcpc_length_aware_t4_attempt2.py` | `8d5f8c0fb34659d57377e9d3702cd4ac8614f008925e8cbcd33697316bc32f81` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/assess_tcpc_length_aware_bounds.py` | `b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md` | `0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae` |

This analyzer imports no controller module, reads no live state, and issues no machine command.
