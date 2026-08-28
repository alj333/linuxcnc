# T4 New-Location Transfer Campaign 2026082701

## Purpose

Acquire one full T4 field at the relocated certified 30 mm sphere and compare
it pose-for-pose with the sealed T4 Attempt 2 reference. This tests spatial
transfer of frozen model `2026082601` at T4 `q=0`; it does not refit the model
and does not test the length-differential bank.

The observed relocation changes X, Y, and Z. Results are therefore classified
as a second machine-volume location, not as an isolated X-axis straightness
test and not as evidence sufficient to build an axis correction table.

## Frozen Identity

- campaign / mode / attempt: `2026082701 / 35 / 1`
- model ID: `2026082601`
- tool: `T4 / H4 / 229.407000 mm`
- probe calibration: `#3032=0.154742`
- sphere / ball: certified `30 mm` sphere / `6 mm` probe ball
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt1.ngc`
- runner SHA-256: `54bd1e3b5cfc95f44ddbf344693652b68dec920f74649e466d939860fe4a9174`

Attempt 1 may be run once only. Any hard abort or missing accepted row retires
the attempt and requires a new attempt ID and fresh output files. Do not append,
restart mid-file, or construct an intermediate-pose resume.

## Acquisition Contract

- exact prior T4 grid: `101` ordered rows and `76` equally weighted unique poses
- paired B signs through `+/-90 deg`; low-B C45 sectors retained
- `28` closure records
- two passes of W, upper-U, -V, +V at every row
- exact `808` contact and `808` gap traces
- one initial `M0`; no other holds, clearance-test moves, or automatic long dwell
- unchanged feeds, retracts, high-Z transits, guards, and bounded duplicate-pulse logic
- C135/C315 remain excluded whenever B is nonzero

The runner is current-position-relative. At initialization it freezes the live
absolute XYZ and active WCS; the post-M0 guard rejects a position or coordinate
change greater than `0.001 mm` before motion.

## New-Location Release

Recorded B0/C0 start:

`X2501.941254485 Y696.899347451 Z-280.866128272`

The exact frozen-q0 replay sampled `30,653` path points and passed. The worst
remaining configured-limit margin after the `2 mm` center and `3 mm` path/model
reserves is `181.641553 mm` at J2. This supersedes the initial pre-load start:
the operator raised Z by an observed `2.100000 mm` before program execution
because the initial clearance was too small. Moving more than `2 mm` from the
recorded XYZ invalidates that proof until it is rerun.

The replay proves configured kinematic and soft-limit reachability. Before
Cycle Start, the operator must confirm the sphere is secured, nearby fixtures
are clear, and the post still runs base-to-sphere `X+, Y-, Z+`.

## Operator Boundary

1. Keep T4/H4 active with G43.4, B0/C0, TWP clear, spindle off, and the probe
   3-5 mm above the sphere top.
2. Keep the laser off. The earlier two-touch qualification is retired because
   23 later gate-closed raw/mux pulses were observed while stationary. Confirm
   whether those pulses were intentional; otherwise treat them as receiver or
   EMI instability. Require continued clear state before Cycle Start and a
   fresh 30-second quiet observation at the initial M0.
3. Load the dedicated runner only after explicit operator clearance.
4. At its sole M0, do not jog, use MDI, alter WCS/TLO/tool state, or touch the
   probe. Confirm the same setup and quiet state, then the operator owns Cycle
   Start.
5. On any fault or hard abort, stop and preserve every output. Do not resume
   Attempt 1.

The program returns to B0/C0 at the measured top-clear position before M2.

## Outcome Classification

1. `ACQUISITION VALID/INVALID`: exact schemas, identities, pose mapping,
   geometry, closures, state/model snapshots, and pulse transaction gates.
2. `FROZEN-MODEL T4 TRANSFER PASS/FAIL`: equal-76 centered RMS/max limits
   `0.120 / 0.280 mm`. A transfer failure remains usable location evidence.
3. `LOCATION-ASSOCIATED DIFFERENCE`: independently center the reference and
   new 76-pose fields by one global XYZ mean, then compare posewise. No rotation,
   scale, shear, group offsets, probe/TLO change, or coefficient fit is removed.

The comparison flags location-associated change above `0.050 / 0.100 mm`
RMS/max as material and above `0.100 / 0.200 mm` as strong. It also reports the
raw mean displacement, XYZ components, signed-B even/odd structure, B/C groups,
closures, repeat scatter, diameter changes, and apparent micrometres-per-metre
gradient without converting two locations into a correction table.

The offline-only comparison analyzer is
`analyze_tcpc_length_aware_t4_new_location_2026082701.py`, SHA-256
`e9c91215f7a83d747136f9cf08271f424f31e6b26723887718f8528af3cf5134`.

The immutable pre-run package is
`calibration_runs/20260827_1602_campaign2026082701_t4_new_location_attempt1_preflight`;
its 91-entry `SHA256SUMS` hashes to
`55ea88c783ebc8be88dac3ee64997066245537b91ed22041c2949e8aec3a3a36`.

The post-load start amendment is sealed under
`calibration_runs/20260827_1613_campaign2026082701_t4_new_location_attempt1_start_amendment`;
its 18-entry `SHA256SUMS` hashes to
`70fe8b2dde48e0fbef8b82f90a09d896ab3c394f79d7e846c4a22eed8097d106`.
It binds the observed `Z +2.100000 mm` operator adjustment, exact replay, idle
unexecuted controller state, and still-empty acquisition outputs.
