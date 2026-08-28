# T4 New-Location Spatial Comparison

Status: `DIAGNOSTIC ONLY - STRONG LOCATION/SESSION-ASSOCIATED DIFFERENCE; X-ORIENTED INDICATED-SPAN CHANGE`

## Decision

Disposition: `NO TCPC CALIBRATION CHANGE`. This second location is retained only as axis-rail and machine-volume diagnostic evidence; it is not a fit source for the current TCPC model.

The completed data is consistent with a location-dependent linear-axis or machine-volume term, but it cannot establish a rail cause by itself. The campaigns differ in X, Y, time, homing session, and T4 seating. This evidence therefore does not justify changing either global B-axis/TCPC parameters or an axis compensation table.

The strongest direct evidence is the certified-sphere opposing-contact span. In the runner, `V=(-sin(C),+cos(C),0)`, so C90/C270 measure a pure machine-X line and C0/C180 measure a pure machine-Y line. The X-line span changes by about 96 um between locations while the Y-line span changes by only about 9 um. Rigid sphere position, TCPC center translation, and any correction constant at a fixed B/C pose cancel from this diameter measurement.

This directly identifies an X-oriented indicated-span change and makes X-axis-local metrology or X-associated cross-axis geometry a leading hypothesis. It does not prove an X-rail fault or show that the new X region is the bad region: the reference X span was anomalously high, while the new-location X/Y spans are nearly isotropic. The broader center field is instead Y-dominated at high B and remains coupled to its single-side W/U reconstruction. A same-seating axis-isolation run is required before assigning either result to a rail.

## Center Field

- reference equal-76 centered RMS / max: `0.107589 / 0.241710 mm`
- new equal-76 centered RMS / max: `0.146265 / 0.337105 mm`
- new-minus-reference after independent XYZ centering: `0.155952 / 0.491649 mm`
- delta component RMS X/Y/Z: `[+0.069887, +0.137923, +0.020344] mm`
- delta energy X/Y/Z: `[20.1%, 78.2%, 1.7%]`
- worst delta: `B-90/C270` = `[-0.094893, +0.481708, -0.025907] mm`, norm `0.491649 mm`

The equal-pose mean sphere displacement is `[+1475.889832, -147.498845, -0.042642] mm`, norm `1483.241958 mm`; `99.504%` of that norm is X. Z changed only `0.042642 mm`, so this comparison does not primarily sample a different Z-rail height.

Low tilt `|B|<=15` delta RMS/max is `0.088829 / 0.160609 mm`; high tilt `|B|>=30` rises to `0.216593 / 0.491649 mm`. The paired B-sign even component is `0.150305 / 0.407634 mm`, versus `0.062568 / 0.136665 mm` odd. Parity is descriptive only: a B-zero change can itself create even signed-B XY terms, so this split does not exclude B zero.

| C sector | pose-delta RMS / max (mm) | mean Y delta (mm) |
| ---: | ---: | ---: |
| 0 | `0.111176 / 0.170467` | `-0.069831` |
| 45 | `0.068547 / 0.111862` | `-0.042045` |
| 90 | `0.205625 / 0.488652` | `+0.091357` |
| 135 | `0.046467 / 0.046467` | `-0.041726` |
| 180 | `0.110801 / 0.176067` | `-0.069573` |
| 225 | `0.098983 / 0.140753` | `-0.060310` |
| 270 | `0.221339 / 0.491649` | `+0.103490` |
| 315 | `0.078189 / 0.078189` | `-0.073443` |

C90/C270 dominate and have the same Y sign; C0/C180 are smaller and have the opposite Y sign. This second-C-harmonic-like structure is inconsistent with explaining the complete field as one simple rigid radial probe shift. It does not independently exclude a B-zero change coupled to other machine geometry.

A best-fit constant rigid vector in the runner's rotating U/V/W head frame explains only `7.0%` of the location-delta energy; its unexplained remainder is `0.150388 / 0.430378 mm`. A simple rigid probe seating shift therefore cannot account for the field.

## Direct X/Y Span

Equal weighting is used after collapsing all 101 rows to the same 76 canonical poses.

| V measurement line | poses | reference mean (mm) | new mean (mm) | new-reference mean / RMS (mm) |
| --- | ---: | ---: | ---: | ---: |
| machine X, C90/C270 | `30` | `30.225010750` | `30.129466767` | `-0.095543983 / 0.099844925` |
| machine Y, C0/C180 | `30` | `30.131827793` | `30.140976420` | `+0.009148627 / 0.018940662` |

The X-minus-Y change of changes is `-0.104692610 mm`. Its sign is consistent in every signed-B band; band contrasts range `-0.138678..-0.076527 mm`.

The reference X/Y means differ by `+0.093183 mm`; the new-location means differ by `-0.011510 mm`. This is why the evidence identifies a change in X behavior between locations rather than declaring the new X region intrinsically worse.

Opposite C orientations are retained separately because their disparity is material:

| C | machine line | reference / new / delta mean (mm) |
| ---: | --- | ---: |
| 0 | Y | `30.125072 / 30.146119 / +0.021047` |
| 90 | X | `30.149261 / 30.077206 / -0.072055` |
| 180 | Y | `30.138583 / 30.135833 / -0.002750` |
| 270 | X | `30.300761 / 30.181727 / -0.119033` |

Both X orientations change negative, so the pooled X association remains. However, the C90/C270 disparity is `0.151500 mm` at the reference and `0.104521 mm` at the new location. The pooled X value is therefore an indicated-span diagnostic, not a pure local scale estimate.

## Repeatability And Encoders

- reference repeated-center scatter: `22` groups / `47` observations, `0.011119 / 0.025961 mm`, axis RMS `[+0.008603, +0.006546, +0.002599] mm`
- new repeated-center scatter: `22` groups / `47` observations, `0.013703 / 0.031859 mm`, axis RMS `[+0.008141, +0.004865, +0.009890] mm`
- reference repeated-diameter scatter RMS / max: `0.007334 / 0.021666 mm`
- new repeated-diameter scatter RMS / max: `0.009850 / 0.030503 mm`
- paired new-reference repeated-diameter scatter RMS / max: `0.011108 / 0.029169 mm`

The systematic location delta is `11.38x` the new repeated-center RMS and `15.43x` its maximum. The result is not explained by accepted probe chatter or ordinary within-run scatter.

The pooled X-minus-Y diameter contrast is `9.43x` the paired repeated-diameter RMS. This supports a repeatable session/location association, while the cross-session reseat remains a systematic confound rather than random scatter.

Posewise new-minus-reference B/C feedback-minus-command RMS is `[+0.000164, +0.001483] deg`; maximum is `[+0.000344, +0.006866] deg`. Even using the full `229.407 mm` T4 length as a conservative lever, the RMS bounds are about `0.000658 / 0.005939 mm` for B/C, far below the `0.155952 mm` field change. This does not test absolute rotary-axis alignment, but it rules out servo following error as the main cause.

## Software Consequence

Even an unrestricted location-independent pose table fitted equally to both locations has an irreducible half-difference of `0.077976 / 0.245824 mm` at each location before measurement noise. A global B/C TCPC retune can compromise between the two fields, but cannot make both locations agree. Absorbing the full new-location field into the global TCPC coefficients would over-correct the reference location.

The next isolation test should keep T4 seated and the sphere at the same Z: acquire a compact B0/B+45/B-45/B+90/B-90 grid at two points differing only in X, then at two points differing only in Y. Every positive B is paired with its corresponding negative B. The same V-pair diameter rows provide a direct X/Y span check. A dial-gauge or laser measurement can then decide whether the location term belongs in screw/axis compensation, a volumetric map, or head/load correction.

## Provenance

The analyzer executes the populated Attempt-7 validator mutation self-test and the sealed reference analyzer self-test before loading the comparison. No coordinate rotation, scale, shear, group offset, or fit is removed from the center fields; only one global XYZ translation per sphere location is removed.

Analyzer: `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_length_aware_t4_new_location_2026082701_complete.py` SHA-256 `0400b92c8d0556eda88cb32cfa039bf7d0d6436b794bcf05ff21b040bafa0868`.

| input | SHA-256 at analysis time |
| --- | --- |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-results.csv` | `ff1d93d954bd1e5a5370db26adaf6d77c1eb4c2823ef5bd5c6fbe1ec6e36e47c` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/tcpc-length-aware-t4-validation-2026082601-attempt2-state.csv` | `ff6f0362a0a83505383044cb0ca1fe00f1d4ab6f5a882266720cb067fe75ed49` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery-results.csv` | `835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery-state.csv` | `99f96ba6e418a514cb07ecba4bd81fec6c18d3f0fbef39c46fcf01d5d8d84235` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery-results.csv` | `06752f2d73dc1ecbf1f605922e2270c55aba0a81e60640bc9e5217730bb785e6` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery-state.csv` | `9497b7f047b3b674f496e9dd8f1c27594ed35ddd8e54bda1aa59308ac312a449` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-results.csv` | `3bf1ae345503cc338e953d3f1174637f54aff078ba359d91147a83326e467730` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-state.csv` | `755290df7f6b4aa39d41839d19a96c3bf16250a2d5ca956cc2e28d6f52328602` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-model-state.csv` | `7282676b53c41db3c42337fa8a111674fad6b236ee97f8e49d2dd7663af37379` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-closures.csv` | `7269b0b24b5d3a49f0d4adae40a4794ac30fb79d2d0d2f36c74662d3d703d9fe` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-contact-trace.csv` | `6801ee3e8b8bdbbfbfbca859497a2acbdbd8e6d9672e99688f9350d7a2140afe` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-gap-trace.csv` | `ef3ff481a1c6c3a80cbcdfd4f002ae7535b0d255e6d07d3049bcf335975ee348` |
| `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.ngc` | `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_length_aware_t4_attempt2.py` | `7371444295d66b6fcd7e75a77689726a46bd1a494c51a272fa246bcc95554b08` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/validate_tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.py` | `b7a61c4f0ff81de1a7b330739b6ccfee3685c5aeb8bdbc53915c7d4a9c890b4b` |
| `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/validate_tcpc_length_aware_t4_new_location_2026082701_attempt7_complete.py` | `3b75b6347a74607e0da7a114d2e93b7aa714a3c55210215a7909712b653c306c` |

This analyzer imports neither LinuxCNC nor HAL and issued no controller command.
