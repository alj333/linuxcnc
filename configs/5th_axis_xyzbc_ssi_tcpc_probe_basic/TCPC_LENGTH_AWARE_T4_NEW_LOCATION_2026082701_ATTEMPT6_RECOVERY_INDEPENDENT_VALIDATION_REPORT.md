# T4 New-Location Attempt-6 Independent Validation

Status: `PASS - READY FOR CONTROLLED LOAD`

This was an offline-only review. It did not load, start, resume, or otherwise
operate LinuxCNC, and it did not invoke standalone `rs274`.

## Frozen Candidate

- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery.ngc`
- runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`
- independent validator SHA-256: `fbc010eb260f32b72307733366a1c6b5258ec3e4421d5e5641b597ebeb6bc53a`
- immutable A4 runner SHA-256: `66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b`
- immutable A4 results SHA-256: `835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`
- zero-row A5 runner SHA-256: `372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1`

## Independent Results

- Exact campaign/mode/attempt identity is `2026082701 / 40 / 6`.
- The sole main-path hold is one `M0`. No direct axis, spindle, or tool motion
  occurs before it, and the only pre-M0 subroutine calls are the read-only
  coordinate, length-model, and resume-start guards.
- The frozen start layers are active G54 work `X0 Y0 Z0`, G54 offsets
  `X2501.941254485 Y696.899347451 Z-510.273128272`, TLO
  `X0 Y0 Z229.407000`, and absolute
  `X2501.941254485 Y696.899347451 Z-280.866128272`. They satisfy
  `absolute = work + G54 + TLO` on all three axes.
- Work coordinates, G54 offsets, and absolute coordinates each retain their
  separate `0.050 mm` per-axis guards before and after M0. The physical
  post-M0 hold guard remains a distinct `0.001 mm` per-axis check.
- The motion, HALUI, and kinematics TLO values are checked against the frozen
  T4/H4 length before M0 and during the run. X/Y tool offsets remain guarded
  at zero, and the T4 q=0 differential model bank remains guarded at zero.
- The exact accepted A4 row-9 center
  `2500.940456, 696.558194, -302.576056` seeds `#701..#703`. The archived
  physical pass-clear constants occur only as provenance/freeze/selector
  values and cannot seed center state or a waypoint.
- The first continuation call is B+5 sequence 10. The unchanged standard
  transit first moves directly from guarded work zero to the center-derived
  B0/C0 clear, then lifts 25 mm and indexes. There is no initial remeasure.
- The tail topology is exactly sequences `10..101`: `92`
  result/state/model rows and `736 / 736` contact/gap trace rows.
- A6 produces exactly `27` closures: `16` same-run closures at the unchanged
  hard `0.050 mm` limit and `11` A4-to-A6 continuity closures at the distinct
  logged `0.100 mm` limit.
- Composite ownership is A4 rows `1..9` plus A6 rows `10..101`, yielding
  `101` summaries, `28` retained closures, and `808 / 808` traces.
- All 27 hardcoded A4 outer-reference coordinates, row-1/row-9 aliases, and
  the row-9 seed match immutable A4 results at logged precision.
- The six A5 outputs remain immutable zero-row evidence. The six A6 outputs
  are distinct ordinary header-only files, share no inode with A4/A5 evidence,
  and all seven LOGAPPEND sites target only the fresh A6 prefix.
- Four G38.3 sites retain four immediate final ignore guards. Exactly four
  fixed `G4 P10.0` sites immediately follow the four successful retract sites.
- Fifteen acquisition, motion, probe, and closure subroutines are byte-equal
  to frozen A5 after normalizing only the fresh output prefix.
- The semantic adversarial suite rejected `45 / 45` mutations, including the
  prior G54-Z/absolute-Z cross-wire, saved-clear center seeding, missing start
  recheck, hidden pre-M0 motion call, closure-limit, topology, and stale-output
  cases.

## Reachability

The independent replay enumerated the simultaneous work/G54/TLO/absolute
coordinate constraints as `1,728` combined XYZ polytope vertices. These reduce
to `64` distinct physical tolerance-corner starts. It replayed all 64 plus the
exact current start to the common center-derived clear, followed by the full
sequence-10..101 trajectory.

- recovery poses: `92`
- sampled points: `38,496`
- physical handoff paths: `65`
- nominal / worst handoff distance: `1.551437433 / 1.631620768 mm`
- nominal / minimum path sphere clearance: `3.890402681 / 3.837483000 mm`
- archived pass-clear versus center-derived clear: `0.033227635 mm`
- minimum configured linear/joint margin: `187.776884 mm`
- remaining margin after the full `5.050 mm` reserve: `182.726884 mm`

The first handoff remains above the sphere and converges to one common clear;
the exact tail after that endpoint is independent of the admitted start corner.
The post is below the sphere in the previously reviewed X-/Y+/Z- direction,
but the operator remains responsible for confirming the fixture is unchanged,
secured, and clear before any controlled load or run.

## Reproduction

```bash
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/validate_tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery.py --static --reachability --self-test
```

Result: `PASS`, frozen runner hash matched, contracts
`92 / 27 / 736 / 736`, composite contracts `101 / 28 / 808 / 808`, and all
45 adversarial mutations were rejected.

`READY FOR CONTROLLED LOAD` permits only an operator-controlled LinuxCNC load
and parse/runtime-state check. It does not authorize Cycle Start or Resume.
