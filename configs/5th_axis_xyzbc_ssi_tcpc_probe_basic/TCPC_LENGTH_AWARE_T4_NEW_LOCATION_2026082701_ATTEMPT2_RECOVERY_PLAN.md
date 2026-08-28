# T4 New-Location Attempt-2 Recovery

Status: `RETIRED - QUALITY ABORT AT CANONICAL SEQUENCE 21`

## Purpose

Preserve Attempt-1 canonical rows 1..17, exclude its incomplete row-18 prefix,
and reacquire canonical rows 18..101 under a fresh isolated identity. The
result is a composite engineering acquisition, not an uninterrupted formal
release.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 36 / 2`
- model / tool: `2026082601 / T4 H4 229.407000 mm / q=0`
- probe calibration: `#3032=0.154742`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.ngc`
- runner SHA-256: `c027a0bab19f403e5e625f01fb50d6d050b51188fa0a0885dbaa795035b5c758`
- recovery output prefix: `tcpc-length-aware-t4-new-location-2026082701-attempt2-recovery`

Attempt 2 may be run once only. Any hard abort retires this identity and its
outputs. Never append, restart mid-file, or reuse Attempt 1.

## Recovery Mapping

- recovery sequence `1..9`: repeated B0 full-C sweep, bridge evidence only
- sequence `10..16`: deliberately absent; preserve Attempt-1 canonical rows
- recovery sequence `17`: repeated B-5/C0 block opening, bridge evidence only
- recovery sequence `18..101`: missing canonical measurements
- composite: Attempt-1 rows `1..17` plus recovery rows `18..101`

The recovery writes exactly `94` result/state/model rows, `29` closures, and
`752/752` contact/gap traces. It has one initial M0, no M1, no later hold, no
whole-pose retry, and no motion before M0.

The in-program continuity gates are:

- block `3609`: recovery row 9 versus sealed Attempt-1 row 9 at
  `[2501.004768, 696.551145, -302.567719] mm`
- block `3617`: recovery row 17 versus sealed Attempt-1 row 17 at
  `[2501.211649, 696.532630, -302.571603] mm`

Both retain the `0.050 mm` hard limit. The repeated B0 sweep also repopulates
all source-local outer references used by the midpoint and closing closures.

## Pulse Boundary

Exactly one gated edge remains mandatory for every successful G38 contact;
gated repeats remain forbidden, raw and mux counts must match, all synchronized
ready/final levels must be clear, and release/model/state guards are unchanged.

Only the matched gate-closed diagnostic-extra ceiling changes from `2` to `8`.
This covers the observed four raw/mux edges that never reached motion. The
value is frozen by the selector guard. The initial post-M0 baseline still
requires zero edges.

## Exact Start And Reachability

Start XYZBC:

`X2501.941254485 Y696.899347451 Z-280.866128272 B0 C0`

The q0 recovery replay passes `28,734` sampled points. Worst remaining margin
after the 2 mm center and 3 mm path/model reserves is `181.641553 mm` at J2.
Moving more than `2 mm` from the recorded XYZ invalidates this release until
replayed.

## Operator Boundary

1. Keep the machine at the recorded B0/C0 sphere-top start with T4/H4 and
   G43.4 active, TWP clear, spindle stopped, and the laser off.
2. Confirm the sphere and nearby fixtures are secure and clear and the post
   remains base-to-sphere `X+, Y-, Z+`.
3. Load only the frozen recovery runner after explicit clearance. Loading does
   not authorize Cycle Start.
4. Press Cycle Start once to reach the sole M0. Do not jog, use MDI, alter the
   WCS/TLO/tool, or touch the probe at M0.
5. Observe a fresh continuously quiet 30-second interval at M0. Resume only
   after electronic and physical release are both confirmed.
6. On any stop or fault, preserve all outputs and do not resume Attempt 2.

## Evidence

Attempt 1 is sealed at
`calibration_runs/20260827_1754_campaign2026082701_t4_new_location_attempt1_partial_gap_abort_seq18`.
Its 21-entry root `SHA256SUMS` hashes to
`2cef1968a26d61cf3f14c6a8807541ce3462f92a8927e6a44e643901234ac6f2`.

Recovery reachability is recorded in
`TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_RECOVERY_REACHABILITY_REPORT.md`.

Final file-only preflight is recorded in
`TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT2_RECOVERY_PREFLIGHT.md`.
The primary validator SHA-256 is
`8eb205238aa3507484ce1f17201fdb4f0f2cbe29507157c833af94c70b7c39c5`;
its compile, static, preflight, and mutation self-tests pass. The independent
171-check audit SHA-256 is
`51aac8c72dd42ab651154b017cc44c6d220f721e254312606615ed4004c438b3`.
Neither validator invokes LinuxCNC, HAL, rs274, or a subprocess.

The complete pre-run package is sealed at
`calibration_runs/20260827_1817_campaign2026082701_t4_new_location_attempt2_recovery_preflight`.
Its 65-entry inventory verifies and its root `SHA256SUMS` SHA-256 is
`bf8230e538399364cbe36d1234b82e7bec656e7a7ff1c24b4f71dcd8e71d8f82`.

At `2026-08-27 18:19 +07`, the exact runner was loaded through LinuxCNC's
program-open interface. Post-load status remained idle, queue-zero, unpaused,
in position and stationary at the frozen XYZBC. `current/read/motion` lines
were `0/0/0`; all six outputs remained exact header-only files and counters
remained `713/713/225`. No Cycle Start, Resume, MDI, homing, or motion command
was issued.

The operator then pressed Cycle Start once and the runner reached its sole M0
without motion. From `18:21:36` through `18:22:50 +07`, the 100 Hz monitor
recorded a continuous `74.400 s` quiet window: only heartbeat records,
raw/mux/gated counters fixed at `713/713/225`, every probe/gate/fault/motion
level clear, and unchanged XYZBC. The workshop is closed and the operator
confirmed there will be no further laser work. Resume remains held pending the
fresh physical sphere, fixture-clearance, and post-direction confirmation.

The operator confirmed the physical gate and resumed. Attempt 2 later stopped
itself at `2026-08-27 18:48:46 +07` on rejected canonical row 21 B-5/C225.
The -V contact triggered after `0.609798 mm`, below the `1.000000 mm` minimum,
following a matched `2/2/0` gate-closed pulse episode. Accepted recovery rows
are `1..9,17..20`; all row-21 traces are excluded. See
`TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT2_RECOVERY_PARTIAL_REPORT.md`.
Do not Resume or reuse this attempt.
