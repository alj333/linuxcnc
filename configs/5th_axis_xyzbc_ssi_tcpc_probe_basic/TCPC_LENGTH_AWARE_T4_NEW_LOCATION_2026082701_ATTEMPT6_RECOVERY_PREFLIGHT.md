# T4 New-Location Attempt-6 Continuation Preflight

Status: `PASS - READY FOR CONTROLLED LOAD`

## Frozen Inputs

- runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`
- A4 canonical results SHA-256: `835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`
- A4 state/model/closures SHA-256: `99f96ba6e418a514cb07ecba4bd81fec6c18d3f0fbef39c46fcf01d5d8d84235 / e28f0f7aab6aca30484381590a6f53284f7f8daa43622e35694d415cd68b7cbc / 26919899661bdf78deddbef9983906814f307d25682370eb5d03c47504090bb4`
- A4 contact/gap SHA-256: `cc097ab53887f6356531681d7ab2bd70021185e0f44e38b8afd46f53b6abe21b / 3f3e72c8738d2fc57efad3bba0617ed5791b88c2e586d07cd0ff092d496671e7`
- base HAL / length model / validation INI SHA-256: `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778 / 8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14 / 24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a`

Attempt 5 remains frozen at runner SHA-256
`372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1`.
Its six outputs remain one-line headers after both pre-M0 aborts. Attempt 6
uses six new `attempt6-recovery` paths and does not mutate or reference an
Attempt-5 LOGAPPEND destination.

## Start Contract

The operator-established state supplied for this recovery is active G54 work
`X0 Y0 Z0`, absolute
`X2501.941254484553 Y696.899347451259 Z-280.866128271562`, B0/C0, T4/H4,
G43.4, and T4 length `229.407000 mm`. Frozen G54 offsets are
`X2501.941254484553 Y696.899347451259 Z-510.273128271562`.

The runner checks active G54, each G54 offset, each work coordinate, and each
absolute coordinate before M0 and after M0. Work, offset, and absolute checks
each use a practical `0.050 mm` per-axis envelope. The independent frozen
hold guard permits only `0.001 mm` physical movement between load and Cycle
Start. Tool, TLO, TCPC, model, feedback, and probe-state guards remain active.

The immutable accepted A4 row-9 center, not the observed terminal clear, seeds
`#701..#703`. The nominal first path is:

`X2501.941254485 Y696.899347451 Z-280.866128272`

to center-derived clear:

`X2500.940456000 Y696.558194000 Z-279.730798000`

Delta is `[-1.000798485, -0.341153451, +1.135330272] mm`; length is
`1.551437433 mm`. The archived Attempt-4 terminal clear differs from that
target by `0.033227635 mm` because A4 aborted before baseline return. It is
provenance only and is not commanded by A6.

## Fresh Outputs

All six Attempt-6 files are one-line schema headers:

- results: `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93`
- state: `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7`
- model-state: `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd`
- closures: `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f`
- contact trace: `df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8`
- gap trace: `e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2`

## Static Contract

Builder checks passed:

- ASCII and maximum line length at or below `225` characters
- one top-level `M0`, no `M1`, and no pre-M0 axis motion
- exact mode/attempt/sequence seed `40 / 6 / 9`
- exact expanded topology `10..101`: `92` accepted rows
- exact Attempt-6 closure topology: `16` same-run plus `11` external rows
- exact trace contract: `736` contact plus `736` gap rows
- composite A4 `1..9` plus A6 `10..101`: `101 / 28 / 808 / 808`
- six isolated fresh output paths and exact one-line schema headers
- no earlier-attempt LOGAPPEND destination
- four G38 sites, four post-retract `G4 P10.0` sites, and four immediate
  pre-G38 final guards; two passes give eight settling dwells per pose
- all subroutine calls resolve
- A6 acquisition/motion/probe subroutines match frozen A5 after output-path
  identity normalization
- embedded `#800..#826` centers match A4 rows `1..9` at logged precision

## Reachability

Offline replay passed from all eight corners of the absolute `+/-0.050 mm`
start cube, the nominal handoff, and the common exact sequence-10-to-101 tail:

- unique sampled points: `29,719`
- nominal first-path physical sphere clearance: `3.890402681 mm`
- worst corner/path sphere clearance: `3.837483000 mm`
- minimum handoff height above sphere center: `21.659927728 mm`, above the
  `17.845258000 mm` effective contact radius and the below-sphere post
- center / path-model / handoff reserves: `2.000 / 3.000 / 0.050 mm`
- worst remaining linear margin after the full `5.050 mm` reserve:
  `182.726884 mm` at J2, B+90/C180 transit descend
- rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`

Evidence:

- `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT6_RECOVERY_REACHABILITY_REPORT.md`
- `tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery-reachability.csv`
- `analyze_tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery_reachability.py`

## Independent Validation

Independent validation passed against the frozen runner hash.

- validator: `validate_tcpc_length_aware_t4_new_location_2026082701_attempt6_recovery.py`
- validator SHA-256: `fbc010eb260f32b72307733366a1c6b5258ec3e4421d5e5641b597ebeb6bc53a`
- exact A6 contract: `92 / 27 / 736 / 736`
- exact A4+A6 composite contract: `101 / 28 / 808 / 808`
- simultaneous coordinate-layer vertices: `1,728`
- exact start plus distinct physical tolerance-corner handoffs: `65`
- independent sampled points: `38,496`
- minimum handoff sphere clearance: `3.837483000 mm`
- remaining configured margin after reserve: `182.726884 mm`
- semantic adversarial mutations rejected: `45 / 45`

Evidence:

- `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT6_RECOVERY_INDEPENDENT_VALIDATION_REPORT.md`

`READY FOR CONTROLLED LOAD` permits an operator-controlled LinuxCNC load and
parse/runtime-state check only. It does not authorize Cycle Start or Resume.

No LinuxCNC command, standalone rs274 invocation, or machine motion was used
during A6 construction or offline replay. Loading and Cycle Start remain
operator-controlled actions after final independent approval.
