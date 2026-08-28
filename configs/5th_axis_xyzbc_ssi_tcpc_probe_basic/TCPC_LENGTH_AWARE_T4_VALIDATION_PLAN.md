# TCPC Length-Aware T4 Validation Plan

Status: `ATTEMPT 1 RETIRED - HISTORICAL PROCEDURE`

Attempt 1 stopped after 36 complete poses on a harmless filtered duplicate raw
probe pulse and must not be resumed or appended. Its evidence is preserved in
`TCPC_LENGTH_AWARE_T4_ATTEMPT1_PARTIAL_REPORT.md`. The current operator
procedure is `TCPC_LENGTH_AWARE_T4_ATTEMPT2_PLAN.md`.

This is the first physical validation of length-model revision `2026082601`.
It is not a production release. T4 is the reference length, so this run tests
the common correction bank at `q=0`; it does not test the T3 differential bank
or prove accuracy for tools longer than T4.

## Frozen Run

- physical campaign / mode / attempt: `2026082602 / 32 / 1`
- tool: keyed-orientation T4/H4, `229.407000 mm`
- probe scalar: `#3032=0.154742 mm`
- sphere: certified 30 mm sphere, fixed for the complete attempt
- poses: `101`, including balanced positive/negative B and the previously
  cleared C sectors
- closures: `28`, each limited to `0.050 mm`
- clean transactions: `808` contact rows and `808` gap rows
- holds: one initial `M0`; no intermediate holds or clearance-test moves
- post-contact behavior: bounded two-clear-sample release/ready checks; no
  automatic 20-second dwell

Use only:

- configuration: `5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`
- program: `nc_files/calibration/tcpc_length_aware_t4_validation_2026082601.ngc`

The configuration loads `tcpc_length_aware_candidate_2026082601.hal` as its
final startup HAL file. Never source, reload, or edit that overlay while
LinuxCNC is running. The runner validates the committed model ID and evaluated
banks; it does not re-authenticate every coefficient pin. The offline overlay
hash check and startup-only rule are therefore mandatory parts of the run
contract.

## Before Launch

1. Confirm every previous LinuxCNC, Probe Basic, milltask, and RTAPI process is
   stopped. Run only one controller instance.
2. Run `python3 validate_tcpc_length_aware_t4.py --preflight` from this config
   directory. It must report `PASS` while every Attempt 1 CSV is header-only.
3. Confirm the laser cutter is off and will remain off for the attempt.
4. Manually deflect T4 twice and confirm two normal releases. Then observe at
   least 30 seconds of continuously quiet probe state.
5. If the probe glows, pulses, fails to release, or needs reseating, correct it
   before launching. A reseat after Attempt 1 starts retires Attempt 1.

## Machine Setup

The operator performs all controller and machine actions.

1. Launch the dedicated validation INI and home all five axes.
2. Enable the machine with the spindle inverter still isolated and spindle
   stopped.
3. Install T4 in its keyed orientation. Make T4 active and apply `G43 H4`.
4. At `B0 C0`, enter TCPC with `G43.4`.
5. Secure the sphere at the current qualified table location. The
   sphere-to-post direction is `X- Y+ Z-`.
6. Position the probe at `B0 C0`, 3-5 mm above the sphere top. Do not use an
   archived XYZ position; the program captures the operator-established point.
7. Confirm every active X/Y/A/B/C/U/V/W tool offset is zero. Only the positive
   `229.407000 mm` Z offset is supported.

The complete pose path was already physically qualified with T4. C135 and C315
remain excluded whenever B is nonzero because they are the known post sectors.

## Run

1. Select the exact frozen program. Loading or previewing it must not move the
   machine.
2. At the only `M0`, reconfirm: laser off, sphere secured, T4/H4 active, TCPC
   active, B0/C0, probe 3-5 mm above the top, and probe clear.
3. Observe another 30 seconds of continuously quiet probe state. This is an
   operator observation; the program contains no long dwell.
4. Start once. Remain at the machine and monitor the initial poses.
5. Do not jog, use MDI, change WCS/tool/offsets, reseat the probe, reload the
   coefficient file, or restart from an intermediate pose.

The runner checks model/configuration ID, TLO, q, differential and total banks,
pose synchronization, homing, SSI validity, spindle state, probe levels, and
edge counters before motion/probing and before accepted-row logging.

## Abort Rule

Any abort, task loss, unexpected stop, manual reseat, missed contact, false G38
contact, operator interference, or output-count mismatch retires Attempt 1.
Stop clear of the sphere, preserve all six files unchanged, close LinuxCNC, and
prepare a newly identified attempt. Do not truncate, append a restart, or make
a resume program from the failed pose.

`linuxcnc.error: Error buffer invalid` means the UI has lost its error channel.
In the recorded 2026-08-26 event it followed a SIGKILL of milltask and was not a
probe/calibration result. Treat it as a clean-restart condition; do not trust or
resume that controller session.

## Attempt 1 Outputs

All files begin with
`tcpc-length-aware-t4-validation-2026082601-attempt1-`:

- `results.csv`: exactly 101 data rows
- `state.csv`: exactly 101 data rows
- `model-state.csv`: exactly 101 data rows
- `closures.csv`: exactly 28 data rows
- `contact-trace.csv`: exactly 808 data rows
- `gap-trace.csv`: exactly 808 data rows

The preflight requires all six to contain only their frozen header. The
post-run validator rejects mixed attempts, retries, missing rows, model-state
drift, transaction faults, and closure failures.

After a completed run, close LinuxCNC and run
`python3 validate_tcpc_length_aware_t4.py` from this config directory. Do not
prepare T3 unless that result validation reports `PASS`.

## Acceptance And Next Stage

T4 passes only if the full acquisition contract passes and the centered sphere
errors are at most `0.120 mm RMS / 0.280 mm maximum` on both the raw 101 rows
and the 76 equal-weight unique poses. Passing T4 validates only the `q=0`
common bank.

After T4 analysis passes, prepare a fresh T3/H3 `31`-row, `14`-closure run with
the same model revision and no retuning. T3 tests `q=1` and the differential
bank. T4 is the longest touch probe available; the `425-430 mm` endpoint is a
later dial-gauge validation and remains outside present physical accuracy
acceptance.

## Frozen Hashes

| artifact | SHA-256 |
| --- | --- |
| validation INI | `24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a` |
| coefficient overlay | `8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14` |
| T4 runner | `0c25bad2be98eae5e927c765fea83d1b877e652635f446ff637dbf8160e308be` |
| model auditor | `b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2` |
| generated model plan | `b8306e4612dff6ad52914ea0cd146bff39a093643f96a766836d82337ddc826e` |
| anchor analyzer | `30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d` |
| campaign analyzer | `d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a` |
| reachability analyzer | `e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607` |
| T4 validator | `6ebbd6ba910f9700e481b47c4bef89ad31039b286cbca5f659134ea7d616c7fb` |
| T4 preflight report | `aca382142a2fac0539e0fd69be144ed87040479183f186086bddb929da1bd0a3` |
