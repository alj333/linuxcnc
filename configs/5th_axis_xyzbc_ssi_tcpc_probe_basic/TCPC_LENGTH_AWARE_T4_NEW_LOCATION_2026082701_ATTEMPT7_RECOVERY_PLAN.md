# T4 New-Location Attempt-7 Recovery Plan

## Objective

Complete campaign `2026082701` after Attempt 6 accepted sequences `10..23`
and aborted before sequence-24 contact 2. Attempt 7 reacquires all eight
contacts of sequence 24 and owns exact sequences `24..101`.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 41 / 7`
- model / tool: `2026082601 / T4 H4 / 229.407000 mm / q=0`
- probe offset / ball: `#3032=0.154742 / 6.000 mm`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.ngc`
- runner SHA-256: `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d`

Attempt 7 is single-use. Any abort, operator stop, missing row, controller
restart, or output reuse retires it and requires a new identity and outputs.

## Ownership

- Attempt 4 owns sequences `1..9`, one retained closure, and `72/72` traces.
- Attempt 6 owns accepted sequences `10..23`, two retained closures, and
  `112/112` complete traces. Its one contact and two gap rows for sequence 24
  are diagnostic-only and excluded.
- Attempt 7 owns sequences `24..101`, `25` closures, and `624/624` traces.
- Final composite: `101` summary/state/model rows, `28` closures, and
  `808/808` contact/gap traces.

Attempt-6 partial archive root:
`d2e84c1534d63d34974a438788ea3d03522d2b597e0d116e032ef587f91adde6`.

## Start And Entry

The sole start is active G54 work `X0 Y0 Z0`, absolute
`X2501.941254485 Y696.899347451 Z-280.866128272`, B0/C0, T4/H4, G43.4.
Frozen G54 is `X2501.941254485 Y696.899347451 Z-510.273128272`.

The immutable accepted Attempt-6 sequence-23 center seeds state:
`X2501.156895 Y696.528585 Z-302.580083`.
The first target is its B0/C0 top-clear:
`X2501.156895 Y696.528585 Z-279.734825`.
Nominal first-segment delta is
`[-0.784359485, -0.370762451, +1.131303272] mm`, length `1.425668857 mm`.
The standard validated path then lifts 25 mm in Z, indexes B10/C0 at high Z,
positions XY, lowers to top-clear, and reacquires the full B+10 block.

Work, G54, and absolute XYZ each have separate `0.050 mm` start guards. TLO
has its existing `0.002 mm` guards. The post-M0 hold guard is `0.001 mm`.
There is one M0, no pre-M0 axis motion, and no other hold.
Raw/mux/gated counters are captured immediately before M0. After resume,
matched gate-closed activity is closed against that pre-hold origin before the
accepted baseline is recaptured, so hold-time pulses cannot be absorbed.

## Probe Contract

Matched raw/mux activity with zero gated delta is diagnostic rather than
count-fatal. The normal no-chatter path waits only for physical release and
the existing 10.0 second HAL ignore window. Any immediate post-G38 extras,
transient raw/mux skew, or later gate-closed activity enters an automatic
stationary quiet handler. It requires 15.0 continuous seconds with counters
unchanged and raw/mux/abnormal/fault levels clear; every new edge or transient
level resets only that 15 second timer. Gap/final quiet retries share one
non-resetting 900 second cumulative budget, and release/finish retries share a
separate non-resetting 900 second contact budget. Samples are 0.25 seconds.
The gap context resets only after the accepted startup recapture and after an
accepted contact trace; trace-begin callers pass a reserved literal zero and
cannot restart an in-flight budget.

The stationary handler contains no axis/rotary motion, gate write, M0, or
feed hold. It checks live machine/model/tool/TLO/SSI/pose state on every
sample. Transient raw/mux partition skew may catch up, but final cumulative
raw/mux totals must match. Any outside-G38 gated count/input change is
immediately fatal; final active levels, mismatch, release failure, or timeout
also abort. Failure DEBUG records sequence/pass/contact, pose, cumulative
elapsed time, counters/deltas, and raw/mux/gated/abnormal/fault/ignore levels.

There is no fixed post-retract `G4 P10.0` or `G4 P15.0`. The observation that
motivated the policy saw matched raw/mux counters rise from `1259` to `1283`
in bursts over roughly 50 seconds while gated remained `618`, then remain
quiet after `08:40:28`.

Attempt-7 contact/gap trace schema 2 adds `chatter_observed`, quiet episode,
elapsed, and reset telemetry. Immutable Attempt-4/Attempt-6 schema-1 files are
not rewritten: composite ingest maps `burst_flag` to `chatter_observed` and
sets the unavailable quiet telemetry to zero.

## Closures

Attempt 7 writes `14` same-run closures at the unchanged `0.050 mm` hard
limit and `11` Attempt-4 external continuity rows at the distinct `0.100 mm`
limit. Error text and logged limits keep those classes separate.

## Operator Boundary

Before Cycle Start at M0, confirm the exact start remains unchanged, laser is
off, sphere is secured, T4/H4 and G43.4 remain active, and the probe has been
continuously quiet for 30 seconds. Program load and Cycle Start remain
operator-controlled. The pre-load archive remains withheld until a fresh
root-owned read-only quiet-state snapshot passes after the operator's reset or
reseat.
