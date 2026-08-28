# T4 New-Location Attempt-5 Continuation Preflight

Status: `READY FOR CONTROLLED LOAD - OPERATOR START REQUIRED`

## Frozen Inputs

- runner SHA-256: `372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1`
- A4 canonical results SHA-256: `835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`
- A4 state/model/closures SHA-256: `99f96ba6e418a514cb07ecba4bd81fec6c18d3f0fbef39c46fcf01d5d8d84235 / e28f0f7aab6aca30484381590a6f53284f7f8daa43622e35694d415cd68b7cbc / 26919899661bdf78deddbef9983906814f307d25682370eb5d03c47504090bb4`
- A4 contact/gap SHA-256: `cc097ab53887f6356531681d7ab2bd70021185e0f44e38b8afd46f53b6abe21b / 3f3e72c8738d2fc57efad3bba0617ed5791b88c2e586d07cd0ff092d496671e7`
- model/HAL/validation INI hashes remain the frozen Attempt-4 values.

## Live Handoff

Read-only status before construction showed task on and idle, axes 1-5 homed,
T4 length `229.407`, TCPC active, model `2026082601` valid, probe/fault/ignore
clear, zero velocity and distance-to-go, and exact commanded pose:

`X2500.972727063280 Y696.550278557223 Z-279.730797759007 B0 C0`

The runner's absolute handoff envelope is `0.050 mm`. This tolerates the
practical live-coordinate readback while preventing a materially different
start. After load, the separate hold-position guard permits only `0.001 mm`
change before motion.

## Static Contract

Builder checks passed:

- ASCII and maximum line length at or below `225` characters
- one top-level `M0`, no `M1`, no pre-M0 axis motion by design
- exact mode/attempt/sequence seed `39 / 5 / 9`
- exact expanded topology `10..101`: `92` accepted rows
- exact Attempt-5 closure topology: `27` rows
- exact trace contract: `736` contact plus `736` gap rows
- composite topology: A4 `1..9` plus A5 `10..101`, yielding `101 / 28 / 808 / 808`
- six isolated fresh output paths; all ordinary one-link files and exact
  one-line schema headers
- no earlier-attempt LOGAPPEND destination
- four G38 sites, four post-retract `G4 P10.0` sites, and four immediate final
  guards; two acquisition passes yield eight settling dwells per pose
- all subroutine calls resolve
- embedded `#800..#826` centers match A4 results rows `1..9` exactly at logged
  precision

## Reachability

Offline exact replay passed from the frozen handoff for canonical sequences
`10..101`:

- sampled path points: `28,309`, including the explicit current-to-seeded-clear
  handoff and seeded B0-to-B+5 high-Z transition
- center / path-model / handoff reserves: `2.000 / 3.000 / 0.050 mm`
- worst remaining linear margin after the full `5.050 mm` reserve:
  `182.726884 mm` at J2, B+90/C180 transit descend
- rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`

Evidence:

- `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT5_RECOVERY_REACHABILITY_REPORT.md`
- `tcpc-length-aware-t4-new-location-2026082701-attempt5-recovery-reachability.csv`
- `analyze_tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery_reachability.py`

## Independent Validation

Independent offline validation passed against the frozen runner hash:

- exact A4 `1..9` plus A5 `10..101` ownership and `92 / 27 / 736 / 736`
  Attempt-5 contracts
- distinct `0.050 mm` same-run and `0.100 mm` cross-attempt closure guards
- frozen handoff envelope, seeded row-9 transit, and no main-path motion before
  the sole M0
- all eight handoff-envelope corners plus the full tail trajectory, with
  `182.726884 mm` remaining configured margin
- `23 / 23` adversarial semantic mutations rejected

Evidence:

- `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT5_RECOVERY_INDEPENDENT_VALIDATION_REPORT.md`
- `validate_tcpc_length_aware_t4_new_location_2026082701_attempt5_recovery.py`

No LinuxCNC command, standalone rs274 invocation, or machine motion was used
during construction or offline replay. The frozen program is ready for a
controlled LinuxCNC load under explicit operator clearance. Loading does not
authorize Cycle Start or Resume.
