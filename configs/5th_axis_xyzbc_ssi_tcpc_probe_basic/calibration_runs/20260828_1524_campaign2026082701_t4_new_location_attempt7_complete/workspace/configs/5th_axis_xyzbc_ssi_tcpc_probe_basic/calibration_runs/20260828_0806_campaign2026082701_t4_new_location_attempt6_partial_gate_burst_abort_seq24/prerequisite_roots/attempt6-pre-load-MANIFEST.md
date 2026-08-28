# T4 New-Location Attempt-6 Pre-Load Archive

- sealed at: `2026-08-27T23:47:30+07:00`
- campaign / mode / attempt: `2026082701 / 40 / 6`
- status: `PASS - READY FOR CONTROLLED LOAD`
- model / tool: `2026082601 / T4 H4 229.407000 mm / q=0`
- probe calibration: `#3032=0.154742`
- runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`
- independent validator SHA-256: `fbc010eb260f32b72307733366a1c6b5258ec3e4421d5e5641b597ebeb6bc53a`
- reachability analyzer SHA-256: `bf54287a1f5a461d9a355c3cedab8c29a51fd71a0c7e9208f4a84463ce017e5d`
- frozen start: active G54 work `X0 Y0 Z0`, absolute
  `X2501.941254485 Y696.899347451 Z-280.866128272 B0 C0`
- frozen G54 offsets: `X2501.941254485 Y696.899347451 Z-510.273128272`
- work/G54/absolute start envelope / post-M0 hold guard:
  `0.050 / 0.050 / 0.050 / 0.001 mm per axis`
- validator static / reachability / mutation self-test:
  `PASS / PASS / 45 of 45 rejected`
- reachability analyzer self-test: `PASS`

Attempt 6 is a fresh continuation after Attempt 5 was retired with zero data
rows. Attempt 4 owns canonical sequences `1..9`, its valid block-100 closure,
and `72/72` contact/gap trace rows. Attempt 6 acquires exact sequences
`10..101`; Attempts 1/2/3, Attempt 4's failed historical bridge block `3709`,
and zero-row Attempt 5 supply no additional composite rows.

The Attempt-6 output contract is `92/92/92` result/state/model rows, `27`
closures, and exact `736/736` contact/gap traces. The completed A4+A6
composite contract is `101/101/101` rows, `28` closures, and exact `808/808`
contact/gap traces. All `16` true A6 same-run closures retain the `0.050 mm`
hard limit. The `11` A4-to-A6 continuity checks use the separately logged
`0.100 mm` hard limit.

The state machine is seeded only with the immutable accepted Attempt-4 row-9
center `X2500.940456 Y696.558194 Z-302.576056`. The first motion goes directly
from the guarded work-zero start to the center-derived B0/C0 top-clear
`X2500.940456 Y696.558194 Z-279.730798`, a nominal `1.551437433 mm` path. The
archived Attempt-4 terminal clear differs by `0.033227635 mm` because A4
aborted before baseline return; it is provenance only, not an A6 waypoint or
center seed.

Independent replay enumerated `1,728` simultaneous work/G54/TLO/absolute
coordinate vertices, `64` distinct physical tolerance starts, and the exact
current start. Across `65` handoff paths and the complete sequence-10..101
tail, it sampled `38,496` points. Nominal/minimum physical sphere clearance
was `3.890402681 / 3.837483000 mm`. After the full `5.050 mm` center,
path/model, and handoff reserve, the worst remaining configured linear margin
was `182.726884 mm`. Configured rotary margins are B `10.000 deg` and C
`44.000 deg`.

All six fresh Attempt-6 output files were regular, distinct, one-link ASCII
files containing exactly one schema header and zero data rows at seal time.
The runner has one initial `M0`, no pre-M0 axis motion, and no other hold.
Four successful-contact retract sites each carry `G4 P10.0`; two passes give
eight settling dwells per accepted pose. Every G38 retains the final inactive
post-contact-ignore guard and the bounded live probe gates.

`workspace/` preserves repository-relative paths and contains the exact A6
runner, frozen validator and analyzer, plan, READY preflight, independent and
reachability reports, reachability CSV, six fresh output headers, validation
INI, base/model/probe-counter HAL files, tool table, and replay dependencies.
The validator is copied unchanged and retains the production runner's
absolute LOGAPPEND path contract; reproduce it from the original repository
root rather than the relocated archive workspace.

The archive also contains the exact immutable A4 runner and six handoff data
files, the Attempt-1 topology source used by the validator, the A4 bridge
closeout report, the retired A5 runner and six zero-row headers, and the A5
zero-row retirement report. `prerequisite_roots/` binds the complete sealed
archive inventories:

- Attempt-4 partial archive `SHA256SUMS` root:
  `d2d78d095d254cd6d59123d3d0596ac2ea8473e5e66cb7070790066447e79181`
- Attempt-5 zero-row retirement archive `SHA256SUMS` root:
  `efa461c3c6d0bb8c28c7fdc11f245f5765e5131864aebb58e26f7825236e86fb`

Every archive entry is a regular file or directory; there are no symlinks.
Every `workspace/` copy was verified byte-identical to its frozen source.
`SHA256SUMS` binds every regular file below this archive except itself.

No LinuxCNC, controller, HAL, program-load, Cycle Start, Resume, MDI, homing,
motion, or standalone `rs274` command was issued while verifying or sealing
this pre-load archive. `READY FOR CONTROLLED LOAD` permits only an explicitly
operator-controlled LinuxCNC load and parse/runtime-state check. It does not
authorize Cycle Start or Resume; physical clearance, probe state, and the sole
M0 decision remain operator responsibilities.
