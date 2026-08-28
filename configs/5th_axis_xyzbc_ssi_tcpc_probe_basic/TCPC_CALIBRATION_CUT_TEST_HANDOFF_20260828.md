# TCPC Calibration Cut-Test Handoff 20260828

Status: `CALIBRATION FROZEN - DEFAULT FOR CONTROLLED CUT TESTS`

## Default Selection

The default TCPC launcher selects
`5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`.
Both `5th Axis.desktop` and `TCPC Trim Work.desktop` call that shared launcher.
LinuxCNC `LAST_CONFIG` in `/home/cnc5/.linuxcncrc` selects the same INI.

The selected commissioning configuration enables
`headheadkins ... lengthmodel=1 lengthmodelid=2026082601`, requires
`[TCPC] LENGTH_MODEL_REQUIRED = 1`, and loads the matching revisioned HAL bank
last. It opens a blank program and does not issue Cycle Start or motion.

This is a controlled cut-test promotion, not an unattended or general
production release. Coefficients remain startup-only. A coefficient change
requires a new model ID, complete validation, and a clean restart.

## Reference-Location Accuracy

All errors below are independently centered sphere-center fields across B/C
poses. They measure pose-dependent TCPC variation, not absolute cutting
accuracy, artifact diameter, or machine-volume accuracy.

| probe/data set | original model RMS/max | revision 2026082601 RMS/max | reduction |
| --- | ---: | ---: | ---: |
| T4 equal 76 poses | `0.219602/0.709875 mm` | `0.107589/0.241710 mm` | `51.0%/66.0%` |
| T4 raw 101 rows | `0.201016/0.711434 mm` | `0.105164/0.245253 mm` | `47.7%/65.5%` |
| T3 equal 20 poses | `0.251775/0.592990 mm` | `0.103060/0.218333 mm` | `59.1%/63.2%` |

T4 is a formal uninterrupted q0 validation. T3 is a composite q1 engineering
pass using canonical Attempt-1 rows `1..22` and recovery rows `23..31` after
two continuity bridges passed. The accepted physical length bracket is
T3/H3 `128.606729 mm` through T4/H4 `229.407000 mm`. The audited software
domain `100.000..430.000 mm` is fail-closed runtime coverage, not physical
accuracy evidence outside the T3/T4 bracket.

## Second-Location Diagnostic

The T4 new-location campaign completed as the validated A4/A6/A7 composite:
`101` rows, `28` closures, and `808/808` guarded contacts. It is excluded from
calibration fitting and default coefficients.

- independently centered new-minus-reference field RMS/max:
  `0.155952/0.491649 mm`
- X-oriented indicated-span change: `-0.095544 mm`
- Y-oriented indicated-span change: `+0.009149 mm`
- X-minus-Y indicated-span contrast: `-0.104693 mm`
- encoder feedback-minus-command was far too small to explain the field

This is strong evidence of a location/session-associated machine-geometry
effect. It does not isolate an X rail because X and Y location, homing session,
and T4 seating all changed. The broader center field is Y-dominated at high B.
Do not retune global TCPC from this campaign. A later same-seating X-only and
Y-only paired-position test is required before designing rail correction
tables.

## Evidence

- T4 closeout: `TCPC_LENGTH_AWARE_T4_ATTEMPT2_CLOSEOUT_REPORT.md`
- T3 closeout: `TCPC_LENGTH_AWARE_T3_ATTEMPT2_RECOVERY_CLOSEOUT_REPORT.md`
- second-location comparison:
  `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_SPATIAL_COMPARISON_REPORT.md`
- T3 final evidence root `SHA256SUMS`:
  `91296bbd468f5b5f67c0722c1142ce0a0edbf3bedd4bd4579aa6f53f68215bca`
- T4 new-location final evidence root `SHA256SUMS`:
  `04e85dffc27db62831eaa783efc599d7b6ed7adda58b1d2706c0aac3e15ba730`

Intermediate preflight/recovery archives and raw diagnostic task captures are
retained locally but are not part of the source commit. The final T3 and T4
new-location evidence packages, canonical result CSVs, analyzers, validators,
plans, and reports form the committed closeout record.

## Verification And Shutdown

Offline and isolated checks passed on `2026-08-28`:

- full length-model numerical audit across `99.998..430.002 mm`
- TCPC entry/exit and tooling-guard simulation
- runtime length endpoint, unsupported-offset, ID, range, and cap faults
- canonical offline/runtime coefficient equivalence
- short/long active-tool TCPC/TWP continuity simulation
- populated T3/T4 data validation plus T3, T4, and second-location analyzer
  and mutation self-tests

At `2026-08-28T18:11+07:00`, after the operator closed LinuxCNC, no LinuxCNC,
Probe Basic, milltask, or RTAPI process and no `/tmp/linuxcnc.lock` remained.
The software shutdown does not record CNC hardware power state.

At the next start, assume the machine is not homed and no tool, TLO, coordinate,
G43.4, or probe state is retained. The operator must establish and verify those
states before starting a cut-test program. No program is authorized merely by
loading the default configuration.
