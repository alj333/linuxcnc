# TCPC Length-Aware T4 Attempt 2 Plan

Status: `COMPLETE - FORMAL VALIDATION PASS`

## Purpose

Attempt 1 stopped after 36 complete poses because one successful G38 contact
produced direct raw/mux/gated edge deltas `2 / 2 / 1`. The second raw/mux edge
occurred after the real-time G38 gate closed and did not reach motion. Attempt
1 is retired and preserved in
`TCPC_LENGTH_AWARE_T4_ATTEMPT1_PARTIAL_REPORT.md`.

Attempt 2 is a fresh, uninterrupted 101-pose validation. It does not append,
truncate, resume, or merge Attempt 1.

## Completion

- physical run completed: `2026-08-27T03:56:52+07:00`
- clean controller shutdown: `2026-08-27T10:25:07+07:00`
- formal offline validation: `PASS`
- exact data: `101/101/101` result/state/model-state rows, `28` closures,
  and `808/808` contact/gap traces
- centered raw-101 RMS / max: `0.105164 / 0.245253 mm`
- centered equal-unique-76 RMS / max: `0.107589 / 0.241710 mm`
- closure RMS / max: `0.022237 / 0.040366 mm`
- filtered extras: `14` delayed contact edges and `1` inter-contact edge;
  raw/mux/gated terminal counters were `823/823/808`
- validation report SHA-256:
  `0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae`
- completion archive:
  `calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete`

This passes the T4 `q=0` common-bank gate. It does not validate the T3
differential bank or longer-tool extrapolation and is not, by itself, a
production release.

## Frozen Identity

- campaign / mode / attempt: `2026082602 / 32 / 2`
- model ID: `2026082601`
- tool: `T4 / H4 / 229.407000 mm`
- probe offset: `#3032=0.154742`
- configuration: `5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`
- runner: `tcpc_length_aware_t4_validation_2026082601_attempt2.ngc`
- runner SHA-256: `d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d`
- validator: `validate_tcpc_length_aware_t4_attempt2.py`
- validator SHA-256: `8d5f8c0fb34659d57377e9d3702cd4ac8614f008925e8cbcd33697316bc32f81`

## Execution Setup Record

At `2026-08-27T00:29:23+07:00`:

- the full integration self-test and isolated standalone RS274 preflight pass;
- preflight report SHA-256 is
  `8f35c96f29de6d6c0b334e42edaeb6aaacc9d7d6fdae706b82549393bdc5a544`;
- Attempt 1 is preserved under
  `calibration_runs/tcpc-length-aware-t4-validation-2026082601-attempt1-retired`;
- the archived `SHA256SUMS` file hashes to
  `dfad4987a8cc7dbb99d21f39c60246d7d4872be4b669f9613b3f8062f62d8bc9`;
- LinuxCNC is running the dedicated validation INI with the exact Attempt 2
  runner selected;
- the controller is off, unhomed, idle, queue zero, and unpaused, with tool 0,
  zero tool offset, zero current velocity, and all spindles stopped;
- all six Attempt 2 outputs remain exact header-only files.

At that checkpoint no Cycle Start had occurred. The setup and quiet checks
below were subsequently completed before the successful run.

The operator is remote for this launch and cannot perform new manual
deflections. The owner confirmed that the prior T4 touch test remains valid:
T4 has not been removed or reseated, and Attempt 1 supplied 290 successful
contact transactions with clean releases. A new passive quiet check from
`2026-08-27T00:37:22+07:00` through `00:37:52+07:00` observed every raw, mux,
gated, abnormal, and pause level clear with sticky counters unchanged at
`0/0/0`. This is an explicit waiver of only the new-session manual-deflection
step. Any probe reseat, controller restart, unexpected pulse, or changed setup
invalidates the waiver and retires a started attempt under the normal rules.

## Duplicate-Pulse Contract

A successful contact may continue with zero, one, or two filtered extra edges
only when every condition below is true:

- direct raw and mux deltas match and contain at least one edge;
- exactly one direct gated edge reached LinuxCNC motion;
- repeat raw and mux deltas match;
- no gated repeat occurred;
- total raw and mux deltas match;
- total raw-minus-gated extras remain in the inclusive range `0..2`;
- G38 succeeded with valid travel;
- the probe passed the two-consecutive-clear-sample release guard.

The runner logs every extra edge. It still stops on a raw/mux mismatch, a
missing or repeated gated edge, more than two combined extras, a failed touch,
an unreleased probe, unstable pre-G38 state, model fault, or machine-state
change. The HAL motion gate and probe directions are unchanged.

## Before Relaunch

1. Leave the aborted Attempt 1 file stopped; do not press Cycle Start.
2. From the current stopped `B-10 C0` side-retract position, the operator first
   lifts/retracts to the known rotary-clear height without changing B or C.
   Only after that clearance is established may the operator index to `B0 C0`
   and return the probe to 3-5 mm above the secured sphere top.
3. Close LinuxCNC cleanly. Do not run the standalone parser while any
   LinuxCNC, linuxcncsvr, milltask, RTAPI, Probe Basic, or QtPyVCP process
   remains or while `/tmp/linuxcnc.lock` exists.
4. Run `python3 validate_tcpc_length_aware_t4_attempt2.py --self-test` and
   `python3 validate_tcpc_length_aware_t4_attempt2.py --preflight` from the
   TCPC configuration directory. Both must pass.
5. Confirm all six Attempt 2 CSV files are exact header-only files.

## Machine Setup

1. Clean-launch the dedicated length-model validation INI and home all five
   axes.
2. Keep the spindle inverter isolated and the spindle stopped.
3. Install T4 in its keyed orientation, make T4 active, and apply `G43 H4`.
4. At `B0 C0`, enter TCPC with `G43.4`.
5. Confirm all active non-Z tool offsets are zero and the Z tool offset is
   `229.407000 mm`.
6. Secure the sphere at the qualified location. Sphere-to-post remains
   `X- Y+ Z-`.
7. Position T4 at `B0 C0`, 3-5 mm above the sphere top.

## Run

1. Confirm the laser is off and will remain off.
2. Deflect T4 twice, confirm both releases, and observe 30 seconds of quiet
   probe state.
3. Load the exact Attempt 2 runner. Loading and previewing must not move the
   machine.
4. Press Cycle Start once to reach the sole initial `M0`.
5. At `M0`, reconfirm the physical setup and observe another 30 seconds of
   quiet probe state.
6. Press Cycle Start once and monitor the continuous run. There are no other
   holds or clearance-test moves.

Do not jog, use MDI, change the tool/WCS/offsets, reseat the probe, reload the
coefficient overlay, or restart from an intermediate pose after Attempt 2
begins. Any hard stop retires Attempt 2 and preserves its outputs.

The formal acquisition has one whole-pose try. It does not automatically retry
a failed pose: a retry would write more than the exact `808/808` transaction
rows and could not pass the validator.

## Acceptance

A complete run must contain exactly:

- `101` result rows;
- `101` machine-state rows;
- `101` model-state rows;
- `28` closure rows;
- `808` contact traces;
- `808` gap traces.

After completion, close LinuxCNC and run
`python3 validate_tcpc_length_aware_t4_attempt2.py`. The result validator
reports every accepted duplicate/repeat edge count in addition to the model,
pose, closure, and centered-error acceptance metrics.
