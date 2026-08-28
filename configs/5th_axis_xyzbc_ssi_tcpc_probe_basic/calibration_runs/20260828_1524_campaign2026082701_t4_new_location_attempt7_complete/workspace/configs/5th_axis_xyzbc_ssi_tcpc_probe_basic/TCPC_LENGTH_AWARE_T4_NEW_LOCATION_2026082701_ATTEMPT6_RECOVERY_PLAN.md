# T4 New-Location Attempt-6 Continuation Plan

## Objective

Complete campaign `2026082701` after Attempt 5 was retired with zero data
rows. Attempt 4 owns canonical sequences `1..9`; Attempt 6 acquires exact
sequences `10..101`. Use the composite for the offline TCPC fit only after
both source legs pass their transaction and closure audits.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 40 / 6`
- model: `2026082601`, configured at startup, T4 reference `q=0`
- tool: `T4 / H4 / 229.407000 mm`
- probe offset / ball: `#3032=0.154742 / 6.000 mm`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery.ngc`
- runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`

Attempt 6 is single-use. Any hard abort, missing row, operator stop, controller
restart, or output reuse retires it and requires a new identity and six fresh
files. Do not restart or Resume a stopped Attempt 6.

## Source Ownership

- Attempt 4 owns summary/state/model sequences `1..9`, its first closure row
  `block 100, 1->9`, and all `72/72` corresponding contact/gap traces.
- Attempt 4's failed historical bridge `block 3709` is excluded. Attempts
  1/2/3 and the zero-row Attempt 5 are excluded from the composite.
- Attempt 6 owns exact sequences `10..101`, all `27` closures it writes, and
  exact `736/736` contact/gap traces.
- Composite contract: `101` summary/state/model rows, `28` closures, and exact
  `808/808` contact/gap traces.

The nine accepted Attempt-4 B0 centers are embedded as constants. Their source
results SHA-256 is
`835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`.

## Work-Zero Handoff

Attempt 6 requires active G54 at work `X0 Y0 Z0`, B0/C0, with T4/H4 and
G43.4 active. The frozen absolute start is:

`X2501.941254485 Y696.899347451 Z-280.866128272 B0 C0`

The frozen G54 offsets are:

`X2501.941254485 Y696.899347451 Z-510.273128272`

Before the sole `M0`, and again after it, the runner rejects any work XYZ,
G54 offset, or absolute XYZ outside its separate `0.050 mm` per-axis
contracts. It freezes the actual loaded position before M0; the hold guard
rejects physical movement above `0.001 mm` before motion. Tool length and
TCPC/model guards remain active independently.

The state machine is seeded only with the accepted Attempt-4 row-9 center:

`X2500.940456 Y696.558194 Z-302.576056`

The first move goes directly from the guarded work-zero start to the
center-derived B0/C0 top-clear
`X2500.940456 Y696.558194 Z-279.730798`, a nominal `1.551437433 mm` path.
It then lifts 25 mm in machine Z and indexes to sequence 10 at B+5/C0.

The observed Attempt-4 terminal clear is `0.033227635 mm` from that derived
clear because Attempt 4 aborted after applying the row-9 measured correction
and before its baseline return. It is provenance only, not an Attempt-6
waypoint or state seed.

## Closure Policy

- All `16` true Attempt-6 same-run closures retain the `0.050 mm` hard limit.
- The `11` Attempt-4-to-Attempt-6 continuity comparisons use a distinct
  `0.100 mm` hard limit and write `limit_mm=0.100`.
- External checks are row9-to-sequence72, Attempt-4 rows1..9 to closing
  sequences93..101, and row1-to-sequence101.
- Error text distinguishes `same-pose closure` from `cross-attempt continuity`.

## Probe Timing

Every successful-contact immediate retract is followed by `G4 P10.0`. The
shared four-contact subroutine has four such sites and is called twice per
pose, giving eight 10-second settling intervals per pose. Every G38 keeps the
bounded two-sample clear gate, immediate live/model checks, and final
`tcpc_probe_gate_ignore.out` inactive guard. There is no dwell on a no-touch
abort or ordinary transit motion.

## Operator Boundary

The runner has one initial `M0`, no pre-M0 axis motion, no other hold, and no
retry. The operator owns Cycle Start and Resume. Before continuing from M0,
confirm the laser is off, sphere secured, active G54 work XYZ remains zero,
T4/H4 and G43.4 are active, B0/C0 is unchanged, probe inputs are clear, and a
continuous 30-second quiet observation has passed. Preserve all six files
after any stop.

The program returns to B0/C0 at the final measured top-clear position before
M2.
