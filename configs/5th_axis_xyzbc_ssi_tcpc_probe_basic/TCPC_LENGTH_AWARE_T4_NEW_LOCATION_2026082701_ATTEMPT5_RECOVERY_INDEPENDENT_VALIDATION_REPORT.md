# T4 New-Location Attempt-5 Independent Validation

Status: `PASS - READY FOR CONTROLLED LOAD`

This was an offline-only review. It did not load, start, resume, or otherwise
operate LinuxCNC, and it did not invoke standalone `rs274` while LinuxCNC was
active.

## Frozen Candidate

- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.ngc`
- runner SHA-256: `372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1`
- independent validator SHA-256: `7434e6f7e0075bf3b3148cb2ccedd39888d457eaf8c68cad3e63c84c3e278026`
- immutable A4 results SHA-256: `835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`
- frozen A4 runner SHA-256: `66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b`

## Independent Results

- Exact campaign/mode/attempt identity is `2026082701 / 39 / 5`.
- The sole main-path hold is one `M0`; no axis, spindle, or tool motion occurs
  on the main path before it.
- The absolute A4 row-9 handoff is guarded to `0.050 mm` per axis before the
  hold. The separate hold guard rejects more than `0.001 mm` movement after
  load and before motion.
- A4 row-9 center is seeded before the first requested pose. Therefore the
  inherited guarded transit returns to computed B0/C0 top-clear, lifts 25 mm,
  and indexes to B+5. It does not require B+5 at the B0 start and does not
  remeasure sequence 9.
- The tail topology is exactly sequences `10..101`: `92` result/state/model
  rows and `736 / 736` contact/gap trace rows.
- Attempt-5 produces exactly `27` closures: `16` true same-run closures at the
  unchanged hard `0.050 mm` limit and `11` A4-to-A5 continuity closures at the
  separately logged `0.100 mm` limit.
- Composite ownership is A4 rows `1..9` plus A5 rows `10..101`, yielding
  `101` summaries, `28` retained closures, and `808 / 808` traces. The failed
  A4 historical bridge block 3709 is excluded; A4 same-run block 100 remains.
- All 27 hardcoded A4 outer-reference coordinates, the A4 row-1/row-9 aliases,
  and the seeded row-9 center match the immutable A4 results at logged
  precision.
- The six A5 outputs are distinct ordinary header-only files. Every
  `LOGAPPEND` targets only the A5 prefix; no A4 or older output can be mutated.
- Four G38.3 sites retain four immediate final guards, including the live
  ignore-window assertion. Exactly four fixed `G4 P10.0` sites immediately
  follow successful retracts and execute twice per pose.
- Fifteen motion/probe subroutines are byte-identical to frozen A4 after only
  normalizing the fresh output prefix. Resume ownership and external closure
  logic are checked separately.
- The semantic adversarial suite rejected `23 / 23` mutations.

## Reachability

The independent replay includes all eight corners of the `+/-0.050 mm`
per-axis handoff envelope, each path back to seeded row-9 clear, and the full
sequence-10..101 trajectory.

- poses: `92`
- sampled points: `28,391`
- maximum handoff-corner-to-seeded-clear move: `0.112351 mm`
- minimum nominal configured linear/joint margin: `187.776884 mm`
- remaining margin after the full `5.050 mm` reserve: `182.726884 mm`

The bounded handoff move occurs at the established 5 mm top clearance and then
moves upward by 25 mm. It does not create a geometric hazard within the
configured-limit model. Physical fixture/post clearance remains an operator
check, as documented by the campaign.

## Reproduction

```bash
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/validate_tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.py --static --reachability --self-test
```

Result: `PASS`, runner hash matched, contracts `92 / 27 / 736 / 736`, composite
contracts `101 / 28 / 808 / 808`, and all 23 adversarial mutations were
rejected.

`READY FOR CONTROLLED LOAD` means the frozen file may be loaded under operator
clearance for LinuxCNC parse/runtime-state validation. It does not authorize
Cycle Start or Resume.
