# Campaign-04 T4 R2 Candidate Verification Plan

Status: `OFFLINE PREFLIGHT PASS`. This is a guarded same-grid diagnostic, not
a released calibration. The candidate configuration has not been loaded and
no machine action was taken during preparation.

## Scope And Isolation

- campaign / mode / attempt: `2026082404 / 26 / 1`
- probe: T4 long probe only, `T4`, `G43 H4`, length `229.407000 mm`
- probe calibration parameter: `#3032=0.154742`
- grid: the exact 101-row mode-23 T4 grid, collapsed to 76 equal-weight poses
  for the primary statistics, with all 28 closure checks retained
- holds: one initial `M0`; no intermediate clearance or block holds

The base HAL, rigid geometry, B/C zeros, production INI, and baseline
task-capture INI remain unedited. The R2 totals are isolated in:

- `tcpc_relocated_sphere_t4_candidate_r2.hal`
- `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate_r2.ini`

The overlay contains exactly 30 absolute `setp` totals for the frozen ten-term
lambda-10 R2 family. It contains no load, net, unlink, source, or shell
commands. The candidate INI is the hash-locked baseline task-capture INI with
three diagnostic comments and one final overlay `HALFILE` line.

## Runner Derivation And Guards

The machine runner is:

`/home/cnc5/linuxcnc-dev/nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_verification.ngc`

It is derived from the archived runnable R1 runner, not from the disarmed R1
working file. Whole-file normalization permits only these changes:

- identity text from R1 to R2 and lambda 30 to the ten-term lambda-10 fit
- mode `25` to isolated mode `26`
- three output names to R2 attempt-1 names
- overlay identity from the 27-pin R1 file to the 30-pin R2 file
- replacement of the read-only pin guard with the exact 30 R2 totals

All motion, probing, pose order, closure logic, and error handling otherwise
remain byte-equivalent to the archived runnable R1 program. The 30-pin guard
runs before the initial hold, inside every live guard, before every pose's
positioning motion, and immediately before accepted-row logging. The runner
contains no coefficient writes.

## Output Contract

The runner writes only these initially header-only files:

- `tcpc-relocated-sphere-t4-candidate-r2-attempt1-results.csv`: 101 rows using
  the 33-column result schema from `schema_version` through
  `v_plus_travel_mm`
- `tcpc-relocated-sphere-t4-candidate-r2-attempt1-state.csv`: 101 rows using
  the 35-column state schema from `schema_version` through
  `joint_2_motor_following_error_fb_minus_cmd_mm`
- `tcpc-relocated-sphere-t4-candidate-r2-attempt1-closures.csv`: 28 rows using
  the 15-column closure schema from `schema_version` through `pass`

Every row must identify campaign `2026082404`, mode `26`, and attempt `1`.
The analyzer rejects extra rows, mixed attempts, missing sequence numbers,
schema changes, incorrect poses, tool/TLO or TCPC state changes, contact-quality
failures, endpoint errors, or a closure above `0.050 mm`.

Do not truncate or reuse attempt-1 outputs after any accepted row. An
interrupted or incomplete run must be archived and a separately versioned
attempt prepared and preflighted.

## Offline Preflight

From the repository root, run:

```bash
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_t4_candidate_r2.py --self-test
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_t4_candidate_r2.py --preflight
```

Both currently pass. The preflight independently restores the frozen R2
checkpoint, recomputes all 30 totals, checks the fit/pin-audit hashes, proves
the INI and R1-runner derivations, parses the runner with in-tree `rs274 -g`,
checks pristine outputs, replays configured limits, checks correction along
the full verification trajectory, and scans both the authorized B +/-90
diagnostic domain and the configured B +/-100 range over a complete C cycle at
0.25-degree spacing with local quadratic interpolation.

The authorized-domain interpolated primary peak is `0.671900 mm` near
`B-90/C272.8566`, below the `0.750 mm` diagnostic cap. The correction reaches
`0.764644 mm` near `B-100/C272.6561` in the configured but unauthorized
extrapolation region; this is reported, not passed against the measured-grid
protocol cap. Exact candidate-path reachability retains `182.861514 mm` after
the declared center and path allowances.

## Operator Run Boundary

Only the operator may close or launch LinuxCNC, home, install or reseat T4,
establish the required `G43 H4` and `G43.4` state, position at the reviewed
B0/C0 sphere-top start, load the runner, release the initial `M0`, or
start/resume motion.

For this test, the operator must launch only the separate R2 candidate INI,
confirm T4 is 3-5 mm above the sphere at B0/C0 with the known post clearance,
and keep direct observation and feed-hold/stop control for the run. Apart from
the required startup, homing, and state establishment, the candidate is for
this exact runner only: no manual, MDI, or jog motion is permitted while the
candidate overlay is active. A pin, tool, state, probe-quality, closure, or
endpoint abort is evidence to preserve; do not bypass its guard.

## Frozen Acceptance Gates

After an exact complete run, run the analyzer without `--preflight`. It must
pass the structural contracts above and all of these statistical gates:

1. Equal-76 globally centered RMS and maximum each improve over immutable
   mode-23 attempt 1 by both 10% and `0.010/0.020 mm`.
2. Equal-76 positive- and negative-B high-tilt RMS each improve by 10%.
3. Equal-76 B0 RMS worsens by at most `0.010 mm`, and no pose's centered norm
   worsens by more than `0.075 mm`.
4. Equal-76 centered RMS / maximum are at most `0.120 / 0.280 mm`; the frozen
   prediction is `0.085763 / 0.204948 mm`.
5. Raw-101 centered RMS / maximum are at most `0.120 / 0.280 mm`; the frozen
   prediction, using the raw-101 mean, is `0.087176 / 0.207789 mm`.
6. Raw-101 actual-versus-predicted centered-pattern RMS / maximum are at most
   `0.050 / 0.120 mm`; both patterns use their own raw-101 global mean.

The residual CSV's published row norms use the equal-76 reference center. The
analyzer does not mix those norms with raw-101 metrics; it recomputes each
metric from centers under the explicitly labelled reference convention.

## Statistical Limits

- paired-B selection frequency is weak for `b_sin2` (`0/8`) and for
  `bc_sinb_cos2c` and `bmid_cos2c` (`3/8` each)
- selection-adjusted antipodal-C outer RMS / maximum is
  `0.253374 / 0.837828 mm`
- the measured-grid cap has an outer fit at `0.749996 mm`; it is not a
  continuous-envelope guarantee
- the primary reaches `0.764644 mm` near `B-100/C272.6561` within configured
  B travel but outside the authorized diagnostic domain
- `bharm-c` was excluded by declared scope, not selected against the pool
- the forward-plus-swap protocol was frozen before fresh T4/T3 candidate data,
  but only after baseline T4 inspection

Therefore a pass establishes implementation/sign agreement only on this
measured T4 grid. It does not authorize general use, omitted C sectors,
different tool lengths, or a production HAL/INI change.

## Mandatory Rollback

T3 must never run under the candidate INI or overlay. Immediately after the
T4 diagnostic:

1. Close LinuxCNC cleanly.
2. Clean-restart `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini`.
3. Verify the base HAL SHA-256 is
   `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`.
4. Confirm the R2 overlay is absent from the selected INI before the untouched
   current-calibration T3 transfer check.
