# T4 New-Location Attempt-4 Partial Bridge-Closure Report

Status: `PARTIAL EVIDENCE SEALED - ATTEMPT 4 RETIRED`

Recorded: `2026-08-27 +07`

## Stop Classification

Attempt 4 stopped under its own closure guard at `2026-08-27T22:17:07+07:00`
after accepting current-run sequence rows `1..9`. The six stopped outputs contain:

- `9/9/9` result, state, and model-state rows
- `2` closure rows
- `72/72` contact and gap trace rows

The stop was not a failed current-run same-pose loop. Closure block `100`, which
compares current Attempt-4 sequence 1 with current Attempt-4 sequence 9 at
B0/C0, passed:

```text
delta = [+0.003457, +0.003016, -0.000169] mm
norm  = 0.004591 mm
limit = 0.050000 mm
pass  = 1
```

The following historical bridge closure, block `3709`, failed. It compares the
immutable Attempt-1 sequence-9 center at the previous sphere location with the
current Attempt-4 sequence-9 center at the relocated sphere position:

```text
Attempt-1 seq 9 = [2501.004768, 696.551145, -302.567719] mm
Attempt-4 seq 9 = [2500.940456, 696.558194, -302.576056] mm
delta           = [  -0.064312,  +0.007049,   -0.008337] mm
norm            = 0.065232 mm
limit           = 0.050000 mm
pass            = 0
```

The bridge failure is therefore mainly X (`-0.064312 mm`). The on-screen text
`T4 primary same-pose closure exceeds 0.050 mm` is the guard's generic abort
message; it does not identify which closure invocation failed. The output ledger
does: current block `100` passed and historical bridge block `3709` failed.

## Probe Evidence

All 72 accepted contacts have travel from `2.999396` through `5.008500 mm`.
There are no burst, counter-consistency, release, or terminal-failure flags.

The contact ledger records 11 matched raw/mux repeat edges across eight
contacts, with zero repeat gated edges. The gap ledger records seven additional
matched raw/mux edges across four gaps, again with zero gated edges. Thus all 18
observed extra edges were kept out of `motion.probe-input`; the 10-second
post-retract settling treatment contained the repeat pulses for these rows.
The stop is a geometric bridge-threshold decision, not a double-pulse or
short-travel rejection.

## Disposition

Attempt 4 must not be resumed, appended, or restarted under the same identity.
It did not reach canonical recovery sequence 21 and contributes no completed
canonical replacement segment. Its rows remain useful partial evidence that:

- the relocated-sphere B0/C sweep was internally repeatable within `0.004591 mm`
- the previous-location to new-location B0 reference moved by `0.065232 mm`
- that transfer difference is predominantly along X

A future attempt should preserve the current-run closure guards while treating
cross-location historical bridges as diagnostic transfer measurements rather
than applying the same `0.050 mm` within-run closure abort threshold.

## Frozen Evidence

Archive:
`calibration_runs/20260827_2222_campaign2026082701_t4_new_location_attempt4_partial_historical_bridge_closure_3709`

The archive contains the exact runner, final validator, plan/preflight and
reachability artifacts, six stopped acquisition outputs, frozen configuration
and HAL provenance, prerequisite archive roots, and execution-scoped logs:

- edge slice: `2026-08-27T21:32:45.843+07:00` through
  `2026-08-27T22:17:15.570+07:00`
- QtPyVCP slice: Attempt-4 load through the `22:17:07` closure error

Runner SHA-256:
`66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b`

Final validator SHA-256:
`c529881ec4cb2d3ff50c776170cbb9af16e9c6a238b2286a67544907456bc638`

No controller, HAL, program-control, MDI, homing, motion, or `rs274` command was
issued while classifying or sealing this evidence. The working acquisition
outputs were not modified.
