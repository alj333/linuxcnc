# T3 Length-Aware Attempt-2 Recovery Plan

Status: `READY - INDEPENDENT REVIEW AND RS274 PREFLIGHT PASS`

## Purpose

Attempt 1 accepted and preserved canonical rows 1-22. Its row-23 transaction
traces show a false electrical pass-2 W touch (`2.543169 mm` travel), after which
the 0.10 mm two-pass center-quality gate stopped the acquisition before writing
row 23 to the result, state, or model-state files.

This is a new, isolated recovery acquisition. It never appends to Attempt 1.
It verifies continuity across the probe reseat, then measures canonical rows
23-31. A successful composite is engineering evidence only; it is not a formal
same-acquisition T3 release.

## Frozen Identity

- Campaign / mode / attempt: `2026082602 / 34 / 2`
- Model: `2026082601`, T3/H3, `q=1`
- Tool length: `128.606729 mm`
- Probe offset: `#3032=0.117658 mm`
- Runner: `nc_files/calibration/tcpc_length_aware_t3_validation_2026082601_attempt2_recovery.ngc`
- Runner SHA-256: `1924e4af8be964a29442f23903e3566daceb4e65dde0e334bd595ba2dcb31294`
- Validator: `validate_tcpc_length_aware_t3_attempt2_recovery.py`
- Validator SHA-256: `cb8960567f39d08bf0ef303110e49910fe50f1d9bb828b200803ba4a6ebe47a1`
- Read-only pre-run archive:
  `calibration_runs/20260827_1416_campaign2026082602_t3_length_aware_attempt2_recovery_preflight`

## Recovery Schedule

| Recovery row | B | C | Role | Composite row |
|---:|---:|---:|---|---:|
| 1 | 0 | 0 | post-reseat bridge to Attempt-1 row 16 | bridge only |
| 2 | -90 | 0 | post-reseat bridge to Attempt-1 row 22 | bridge only |
| 3 | -90 | 90 | missing canonical measurement | 23 |
| 4 | -90 | 180 | missing canonical measurement | 24 |
| 5 | -90 | 270 | missing canonical measurement | 25 |
| 6 | -90 | 0 | B-90 block closure | 26 |
| 7 | 0 | 0 | closing B0 sweep opening | 27 |
| 8 | 0 | 90 | closing B0 sweep | 28 |
| 9 | 0 | 180 | closing B0 sweep | 29 |
| 10 | 0 | 270 | closing B0 sweep | 30 |
| 11 | 0 | 0 | closing B0 sweep closure | 31 |

The runner writes exactly 11 result/state/model-state rows, 6 closure rows,
88 contact traces, and 88 gap traces. It has one initial `M0`, no `M1`, no
whole-pose retry, and no later planned hold.

## Built-In Continuity Gates

The first two rows are checked before missing canonical data is collected:

- Closure `3416`: recovery row 1 versus sealed Attempt-1 row 16 center
  `[1024.840507, 843.991200, -403.293929] mm`.
- Closure `3422`: recovery row 2 versus sealed Attempt-1 row 22 center
  `[1025.069611, 844.044347, -403.151636] mm`.

Each hard gate is `0.050 mm`. Failure stops the recovery immediately. The four
additional recovery closures are `-90` (2->6), `3401` (1->7), `200` (7->11),
and `3402` (1->11), also at `0.050 mm`.

## Operator Setup

1. Reseat T3 in its keyed orientation and verify receiver response by hand.
2. Return to the reviewed sphere-top start: B0/C0, probe ball 3-5 mm above the
   sphere, with the same secured sphere and stand position.
3. Confirm all axes homed, spindle stopped, laser off, T3 active, and apply
   `G43 H3` before `G43.4`.
4. Confirm the length model is configured and valid at model `2026082601`,
   `q=1`, fault `0`, with TWP inactive and both SSI channels valid.
5. Observe 30 seconds of continuously quiet probe state.
6. Load only the frozen recovery runner. Press Cycle Start once to reach its
   sole `M0`; reconfirm setup and another 30-second quiet interval, then Resume.
7. If any unexpected stop occurs, preserve the partial recovery outputs. Do not
   resume or reuse attempt 2; diagnose and issue a new attempt identity.

## Acceptance Boundary

The offline validator requires exact identity, schedule, row/state/model
semantics, `q=1` D and H0+S+D vectors, bounded duplicate-pulse traces, all six
recovery closures, all 14 reconstructed canonical closures, and the frozen
raw/equal, reconstructed-H0, sign, B0, and per-pose metric gates.

The composite preserves Attempt-1 rows 1-22 and uses only recovery rows 3-11
for canonical rows 23-31. Recovery rows 1-2 are continuity evidence only.

A pass is reported as `COMPOSITE ENGINEERING PASS; NOT FORMAL T3 RELEASE`.
A fresh uninterrupted 31-row mode-33 acquisition remains necessary if a formal
same-acquisition T3 release is later required.
