# T4 New-Location Attempt-5 Continuation Plan

## Objective

Complete campaign `2026082701` without repeating the accepted Attempt-4 B0
sweep. Attempt 4 owns canonical sequences `1..9`; Attempt 5 acquires exact
sequences `10..101`. The composite is used for the offline TCPC fit only after
both source legs pass their transaction and closure audits.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 39 / 5`
- model: `2026082601`, configured at startup, T4 reference `q=0`
- tool: `T4 / H4 / 229.407000 mm`
- probe offset / ball: `#3032=0.154742 / 6.000 mm`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.ngc`
- runner SHA-256: `372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1`

Attempt 5 is single-use. Any hard abort, missing row, operator stop, controller
restart, or output reuse retires it and requires a new identity and six fresh
files. Do not restart or Resume a stopped Attempt 5.

## Source Ownership

- Attempt 4 owns summary/state/model sequences `1..9`, its first closure row
  `block 100, 1->9`, and all `72/72` corresponding contact/gap traces.
- Attempt 4's failed historical bridge `block 3709` is excluded. Older Attempt
  1/2/3 rows and traces are excluded from this composite.
- Attempt 5 owns exact sequences `10..101`, all `27` closures it writes, and
  exact `736/736` contact/gap traces.
- Composite contract: `101` summary/state/model rows, `28` closures, and exact
  `808/808` contact/gap traces.

The nine accepted Attempt-4 B0 centers are embedded as constants. Their source
results SHA-256 is
`835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`.

## Resume Handoff

Attempt 5 must load at the unchanged Attempt-4 row-9 B0/C0 top-clear command:

`X2500.972727063 Y696.550278557 Z-279.730797759 B0 C0`

Before the sole `M0`, the runner rejects an absolute XYZ deviation above
`0.050 mm`. It then freezes the actual loaded position; the existing post-M0
hold guard rejects any subsequent change above `0.001 mm`. The accepted
Attempt-4 row-9 center seeds the standard high-Z transit, so sequence 10 safely
indexes from B0/C0 to B+5/C0 without a duplicate probe measurement.

## Closure Policy

- Every true Attempt-5 same-run closure retains the `0.050 mm` hard limit.
- The `11` comparisons that cross the Attempt-4/Attempt-5 boundary use a
  distinct `0.100 mm` hard continuity limit and write `limit_mm=0.100`.
- External checks are row9-to-sequence72, Attempt-4 rows1..9 to closing
  sequences93..101, and row1-to-sequence101.
- Error text explicitly distinguishes `same-pose closure` from
  `cross-attempt continuity`.

## Probe Timing

Every successful-contact immediate retract is followed by `G4 P10.0`. The
shared four-contact subroutine has four such sites and is called twice per
pose, giving eight 10-second settling intervals per pose. Every G38 also keeps
the bounded clear gate, immediate live/model checks, and final
`tcpc_probe_gate_ignore.out` inactive guard. There is no dwell on no-touch
abort or ordinary transit motion.

## Operator Boundary

The runner has one initial `M0`, no pre-M0 axis motion, no other hold, and no
retry. The operator owns Cycle Start and Resume. Before continuing from M0,
confirm laser off, sphere secured, T4/H4 and G43.4 active, B0/C0 unchanged,
probe inputs clear, and a continuously quiet 30-second observation. Preserve
all six files after any stop.

The program returns to B0/C0 at the final measured top-clear position before
M2.
