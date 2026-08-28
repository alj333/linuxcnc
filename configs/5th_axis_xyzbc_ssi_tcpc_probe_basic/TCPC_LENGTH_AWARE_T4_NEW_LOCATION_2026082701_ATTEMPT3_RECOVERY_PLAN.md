# T4 New-Location Attempt-3 Recovery

Status: `OFFLINE PREFLIGHT PASS - HOLD FOR OPERATOR RESET, START RESTORE, AND LOAD GATE`

## Purpose

Preserve immutable Attempt-1 canonical rows 1..17 and Attempt-2 canonical
rows 18..20, exclude every Attempt-2 sequence-21 trace, and reacquire
canonical rows 21..101 under a fresh isolated identity. The final composite
is an engineering recovery acquisition, not one uninterrupted run.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 37 / 3`
- model / tool: `2026082601 / T4 H4 229.407000 mm / q=0`
- probe calibration: `#3032=0.154742`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery.ngc`
- runner SHA-256: `bf76ab273c76a32046e6f2066f6b865ea8e0a448266cff0399186e262c5a061a`
- output prefix: `tcpc-length-aware-t4-new-location-2026082701-attempt3-recovery`

Attempt 3 may run once only. Any execution stop, quality abort, controller
fault, setup change, or output append retires this identity. Never Resume or
reuse Attempt 2, and never append Attempt-3 data to an Attempt-1/2 file.

## Immutable Salvage

Attempt 1 owns canonical rows `1..17`. Attempt 2 wrote summaries at
`1..9,17..20`; only canonical rows `18..20` are salvage data. Its three
closures remain continuity evidence. Its contact and gap files each contain
`108` data rows: the first `104` belong to accepted summaries, while the last
four are rejected sequence-21 pass-1 contacts `1..4`. All four sequence-21
contact rows and all four matching gap rows are excluded.

Attempt 2 stopped on the sequence-21 B-5/C225 `-V` touch at `0.609798 mm`,
below the `1.000000 mm` minimum, after a matched gate-closed `2/2/0`
raw/mux/gated gap. Attempt 3 reacquires sequence 21 from its first contact.

Composite ownership is exact:

- Attempt 1: canonical `1..17`
- Attempt 2: canonical `18..20`
- Attempt 3: canonical `21..101`

Bridge-only repeats never replace the owning attempt's canonical row.

## Acquisition Topology

Attempt 3 writes summary/state/model rows in this exact order:

`1..9, 17, 20..101`

- `1..9`: repeated opening B0 full-C sweep; repopulates all outer references
- `10..16`: absent; immutable Attempt-1 data
- `17`: repeated B-5/C0; owns the source-local B-5 opening reference
- `18..19`: absent; immutable Attempt-2 data
- `20`: repeated B-5/C180 and latest-boundary bridge evidence
- `21..23`: fresh B-5/C225, C270, C0; row 23 closes to Attempt-3 row 17
- `24..92`: unchanged remaining low-, medium-, midpoint-, and high-B poses
- `93..101`: closing B0 sweep using Attempt-3 source-local outer references

Exact clean output counts are `92/92/92` result/state/model rows, `30`
closures, and `736/736` contact/gap transactions. Including headers, final
line counts are `93/93/93/31/737/737`.

The 30 closure rows are ordered exactly:

`100 1->9; 3709 A1:9->A3:9; 3717 A1:17->A3:17;`
`3720 A2:20->A3:20; -5 17->23; 10 24->30; -10 31->37;`
`15 38->44; -15 45->51; 30 52->56; -30 57->61; 45 62->66;`
`-45 67->71; 905 9->72; 60 73->77; -60 78->82; 90 83->87;`
`-90 88->92; 911 1->93; 906 72->93; 912 2->94; 913 3->95;`
`914 4->96; 915 5->97; 916 6->98; 917 7->99; 918 8->100;`
`919 9->101; 200 93->101; 900 1->101`.

## Hard Bridges

All three bridges have a `0.050 mm` hard limit and must pass before the first
new canonical measurement at sequence 21:

- block `3709`: Attempt-3 row 9 versus immutable Attempt-1 row 9 at
  `[2501.004768, 696.551145, -302.567719] mm`
- block `3717`: Attempt-3 row 17 versus immutable Attempt-1 row 17 at
  `[2501.211649, 696.532630, -302.571603] mm`
- block `3720`: Attempt-3 row 20 versus immutable Attempt-2 row 20 at
  `[2500.997060, 696.609459, -302.544243] mm`

Rows 9 and 17 are intentionally sourced from Attempt 1, never from Attempt-2
bridge repeats. Row 20 is sourced from the accepted Attempt-2 canonical row.

## Motion And Pulse Contract

The 21 motion/safety/logging subroutines are byte-equivalent to Attempt 2
after normalizing only the isolated output prefix. The runner retains one M0,
no M1, no top-level motion before M0, no later hold, no whole-pose retry,
minimum valid contact travel `1.0 mm`, and max matched gate-closed extras `8`.
Every successful G38 still requires raw/mux agreement, exactly one gated
motion edge, zero gated repeats, clear synchronized ready/final levels, and
passing release/model/state guards.

## Reachability Pass

Reviewed start XYZBC remains:

`X2501.941254485 Y696.899347451 Z-280.866128272 B0 C0`

The dedicated Attempt-3 replay samples `28,345` path points from this start,
including the direct B-5/C0 to B-5/C180 machine-Z-plus-25-mm transit. It
passes with `181.641553 mm` worst remaining configured linear margin after
the conservative reserve; rotary margins are B `10 deg` and C `44 deg`.
Evidence is in
`TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT3_RECOVERY_REACHABILITY_REPORT.md`.

## Operator Boundary

1. Do not Resume, restart, or reuse the loaded retired Attempt-2 runner.
2. Reset or reseat the probe; repeat manual deflection/release and quiet tests.
3. Re-establish the reviewed T4/H4 B0/C0 start without reusing stopped B-5/C225.
4. Confirm the frozen Attempt-3 file, hash, and live setup preflight.
5. Verify all six Attempt-3 outputs are the frozen one-line header files.
6. Load only the frozen Attempt-3 runner after explicit clearance; load is not Cycle Start authorization.
7. Press Cycle Start once to reach the sole M0; there must be no motion.
8. At M0, do not jog or use MDI; reconfirm setup and observe 30 seconds quiet.
9. Resume only after the separate physical and electronic release decision.
10. Preserve every output and retire Attempt 3 after any stop or fault.

File-only construction evidence is in
`TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT3_RECOVERY_PREFLIGHT.md`.
