# T4 New-Location Attempt-4 Recovery

Status: `OFFLINE BUILD FROZEN - HOLD FOR VALIDATION, REACHABILITY, FILTER, AND LIVE GATES`

## Scope

Attempt 4 is a fresh isolated repeat of the reviewed Attempt-3 recovery
topology. The runner does not read, append, rename, or replace any Attempt-3
artifact, and no Attempt-3 output is admitted to the composite. No
probe-filter change is part of this build.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 38 / 4`
- model / tool: `2026082601 / T4 H4 229.407000 mm / q=0`
- probe calibration: `#3032=0.154742`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt4_recovery.ngc`
- runner SHA-256: `66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b`
- output prefix: `tcpc-length-aware-t4-new-location-2026082701-attempt4-recovery`

The source is the frozen Attempt-3 preflight archive runner with SHA-256
`bf76ab273c76a32046e6f2066f6b865ea8e0a448266cff0399186e262c5a061a`.
Reviewed changes are the mode/attempt identity, debug labels, six isolated
output paths, operator-contract text, the four fixed retract dwells below, and
the A4-only non-delaying final ignore-window guard.

## Exact Topology

Summary, state, and model-state rows are acquired in this exact order:

`1..9, 17, 20..101`

Rows `1..9` rebuild Attempt-4-local outer references, row `17` rebuilds
the local B-5 opening reference, row `20` repeats the accepted boundary,
and rows `21..101` are reacquired. The hard `0.050 mm` bridges remain:

- `3709`: immutable Attempt-1 row 9 to Attempt-4 row 9
- `3717`: immutable Attempt-1 row 17 to Attempt-4 row 17
- `3720`: immutable Attempt-2 row 20 to Attempt-4 row 20

All three bridges must pass before row 21. Clean counts remain `92/92/92`
summary/state/model rows, `30` closures, and `736/736` contact/gap rows.

## Detection-Retract Pause

Each successful W, U, -V, and +V contact retract is followed immediately by
`G4 P10.0` inside `tcpc_vector_sphere_pass4`, before the next reposition or
ready guard. The subroutine runs twice per pose, so this is eight pauses per
pose and `736` pauses in a clean 92-pose run: `7,360 s` (`2:02:40`) of fixed
dwell. No dwell was added to a no-touch abort branch or transit move.

## Final Ignore-Window Guard

Immediately before every `G38.3`, `tcpc_pair_probe_final_guard` runs its live
guard and `M66 E0 L0`, then aborts if
`#<_hal[tcpc_probe_gate_ignore.out]>` remains active. This check precedes the
existing final gate-request, input, abnormal-level, fault-latch, and counter
checks. It adds no dwell and prevents a new contact from starting inside the
post-contact ignore window.

## Execution Hold

Do not load, preview through LinuxCNC, or execute this runner yet. Release
requires all of the following:

1. The dedicated Attempt-4 validator passes static, mutation, and fresh-output checks.
2. Exact Attempt-4 trajectory reachability passes from the reviewed B0/C0 start.
3. The probe-filter review is closed without invalidating this frozen runner.
4. All six outputs are rechecked as one-line regular files with the frozen hashes.
5. Live tool, TLO, model, TCPC/TWP, SSI, probe release/quiet, sphere security, start pose, and physical clearance gates pass.

Attempt 4 may execute once only after explicit release. Any append, stop,
abort, setup change, filter change, or controller fault retires this identity.
