# T4 Length-Aware Attempt 2 Completion Archive

Status: `COMPLETE - FORMAL VALIDATION PASS`

## Identity

- campaign / mode / attempt: `2026082602 / 32 / 2`
- model ID: `2026082601`
- tool: `T4 / H4 / 229.407000 mm`
- probe offset: `#3032=0.154742 mm`
- program completed: `2026-08-27T03:56:52+07:00`
- controller closed: `2026-08-27T10:25:07+07:00`
- formal validation passed: `2026-08-27T10:26:07+07:00`

## Accepted Result

- results / state / model-state rows: `101 / 101 / 101`
- closure rows: `28`
- contact / gap traces: `808 / 808`
- centered raw-101 RMS / max: `0.105164 / 0.245253 mm`
- centered equal-unique-76 RMS / max: `0.107589 / 0.241710 mm`
- closure RMS / max: `0.022237 / 0.040366 mm`
- frozen centered-error limits: `0.120 mm RMS / 0.280 mm max`
- frozen closure limit: `0.050 mm`

Terminal raw/mux/gated counters were `823/823/808`. The bounded policy logged
and accepted 14 delayed post-contact extra edges plus one inter-contact extra.
Every raw and mux count matched, exactly 808 edges reached the G38 motion gate,
and no second gated edge, burst, release fault, consistency fault, or terminal
failure was accepted.

The owner was remote after setup. A new-session manual deflection was
explicitly waived because T4 had not been removed or reseated and Attempt 1
had already supplied 290 successful contacts with clean releases. Before
Cycle Start, a passive 30-second check observed all probe levels clear and
counters unchanged at `0/0/0`; the sole-M0 30-second check repeated that result.

## Validation

- runner SHA-256:
  `d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d`
- validator SHA-256:
  `8d5f8c0fb34659d57377e9d3702cd4ac8614f008925e8cbcd33697316bc32f81`
- preflight report SHA-256:
  `8f35c96f29de6d6c0b334e42edaeb6aaacc9d7d6fdae706b82549393bdc5a544`
- result report SHA-256:
  `0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae`
- source-tree commit: `86dd4068016ab748cf0e0e454075f2e2b6b6a7d2`
- source-tree description: `v2.9.8-168-g86dd406801-dirty`
- LinuxCNC version: `2.9.8`
- runtime `milltask` SHA-256:
  `23f640db275c1fb5f8e2d938448ce1a0cd726ea002e3550e52439a9396ef1625`
- runtime `headheadkins.so` SHA-256:
  `1cc5b7023bed01bd2eb56bb52139e74f964cf17754b440aff42a987f4b22ac4c`
- preflight `rs274` SHA-256:
  `1ac7ac4e0e2f3ae07a42ca02a34730d370651063e7dcfcc093643d76063cb4c9`

The formal validator ran only after all controller processes stopped and
`/tmp/linuxcnc.lock` was absent. It rechecked sealed inputs, the deterministic
full-length-domain audit, isolated standalone RS274 parsing, all output schemas
and identities, model snapshots, pose topology, contact/gap transaction
semantics, closure mappings, and accuracy limits.

The milltask wrapper records status 137 because the LinuxCNC launcher killed
the task during the operator-requested clean GUI shutdown, more than six hours
after the program had completed and returned idle. The G-code completion,
output files, final edge-log heartbeats, and formal validator all precede or
independently survive that shutdown cleanup; it is not classified as a run
failure.

## Contents

This archive contains:

- the exact runner and all six completed output CSV files;
- preflight, result, operator-plan, configuration README, and resume reports;
- the validator, model auditor, model plan, imported analysis modules, and
  dual-probe fitter dependency;
- the canonical T4 motion/grid source used by the validator;
- all seven top-level TCPC INIs inspected by the model auditor, their hash
  inventory, the coefficient overlay, probe counter HAL, machine HAL,
  shared base/post-GUI/shutdown HALs, XHC HAL, canonical tool table, parameter
  snapshot, remap sources, and TWP state helpers;
- the relevant kinematics/interpreter sources and supporting runtime binaries;
- the validation command, environment, stdout/stderr transcript, and exit code;
- the 1 kHz probe-edge log, milltask lifecycle log, and diagnostic helpers.

The copied `milltask`, `rs274`, and `headheadkins.so` files are supporting
binary evidence only, not a complete or bootable LinuxCNC runtime snapshot.
Their recorded hashes, the source-tree identity, and the captured source/config
inputs are the authoritative provenance.

`SHA256SUMS` authenticates every archived file except itself. This archive
validates only the T4 `q=0` common correction bank. It does not validate the T3
length-differential bank, longer-tool extrapolation, or production promotion.
After the final checksum generation, write permission is removed from every
archive member and from this directory while existing executable bits are
preserved.
