# Campaign-04 T4 Candidate Verification Plan

Status: `REJECTED PRE-MOTION`. Do not use this R1 plan, INI, overlay, or
runner. The exact preflighted R1 artifacts are preserved under
`calibration_runs/20260825_0833_campaign04_t4_candidate_r1_rejected_pre_motion`.
A separately versioned R2 fit and verification contract supersedes this work.

## Scope

This is a same-grid implementation and sign test of the frozen T4-only
nine-term lambda-30 candidate. It is not a general/live release and must not be
used to extrapolate into unmeasured C sectors.

- campaign / stage / attempt: `2026082404 / 25 / 1`
- probe: T4 long probe only, `T4`, `G43 H4`, length `229.407000 mm`
- probe calibration parameter: `#3032=0.154742`
- grid: the exact 101-pose mode-23 T4 grid, with 28 closure checks
- holds: one initial `M0`; no intermediate clearance or block holds

The base HAL, rigid geometry, B/C zeros, production INI, and baseline
task-capture INI remain unedited. The candidate is supplied only by:

- `tcpc_relocated_sphere_t4_candidate_lambda30.hal`
- `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate.ini`

The overlay contains only 27 absolute tuning-pin totals. The runner reads and
guards those values; it contains no coefficient writes.

## Preflight

Run the offline preflight before launching the candidate configuration:

```bash
python3 analyze_tcpc_relocated_sphere_t4_candidate.py --preflight
```

The frozen preflight is currently `PASS`. It covers the candidate fit identity,
base and candidate hashes, final-overlay INI ordering, `rs274 -g` parsing, exact
pose order, one-hold contract, pristine output files, and candidate-geometry
configured-limit replay.

## Candidate Run

Only the operator may close/restart LinuxCNC, home, select/apply T4/H4 and TCPC,
position above the sphere, load the runner, or start/resume motion.

Launch only the separate candidate INI, then use only:

`/home/cnc5/linuxcnc-dev/nc_files/calibration/tcpc_relocated_sphere_t4_candidate_verification.ngc`

The runner writes exclusively to these header-only mode-25 files:

- `tcpc-relocated-sphere-t4-candidate-verification-results.csv`
- `tcpc-relocated-sphere-t4-candidate-verification-state.csv`
- `tcpc-relocated-sphere-t4-candidate-verification-closures.csv`

The mode-23 attempt-1 inputs are immutable. Do not truncate or reuse the
mode-25 files after any accepted row; an interrupted run requires a separately
prepared attempt and new immutable outputs.

## Acceptance Gates

After a complete run, execute the validator without `--preflight`. It requires
all 101 result/state rows, all 28 closures, exact pose/tool/state/contact and
endpoint contracts, plus these frozen gates:

1. Full centered RMS and maximum each improve by both 10% and 0.010/0.020 mm.
2. Positive- and negative-B high-tilt RMS each improve by at least 10%.
3. B0 RMS does not worsen by more than 0.010 mm.
4. No row's centered residual norm worsens by more than 0.075 mm.
5. Raw-row centered RMS / maximum are at most 0.130 / 0.300 mm; the frozen
   offline prediction is 0.099990 / 0.237606 mm.
6. The RMS / maximum difference between actual and frozen-predicted centered
   residual vectors are at most 0.050 / 0.120 mm.

A pass confirms only that the overlay implements the frozen correction with
the expected signs on this measured T4 grid.

## Mandatory Rollback

T3 must not run under the candidate INI or overlay. Immediately after the T4
candidate test:

1. Close LinuxCNC cleanly.
2. Clean-restart `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini`.
3. Verify `5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` SHA-256 is
   `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`.
4. Confirm the candidate overlay is not present in the selected INI before any
   current-calibration T3 holdout run.

The T3 holdout remains a baseline-current-calibration run followed by offline
application of the already frozen T4 candidate. It must never be refit from T3.
