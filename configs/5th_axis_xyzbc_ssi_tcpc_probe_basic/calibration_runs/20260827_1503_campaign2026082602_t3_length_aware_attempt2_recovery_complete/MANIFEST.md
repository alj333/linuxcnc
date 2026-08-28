# T3 Length-Aware Attempt-2 Recovery Completion Archive

Status: `COMPLETE - COMPOSITE ENGINEERING PASS; NOT FORMAL T3 RELEASE`

## Identity

- model ID: `2026082601`
- recovery campaign / mode / attempt: `2026082602 / 34 / 2`
- tool: `T3 / H3 / 128.606729 mm`
- probe offset: `#3032=0.117658 mm`
- first recovery G38 contact: `2026-08-27T14:37:41.231+07:00`
- program returned idle at M2: `2026-08-27T14:59:32.911+07:00`
- offline validation passed: `2026-08-27T15:02:50+07:00`
- live probe-edge snapshot through: `2026-08-27T15:10:35.741+07:00`

## Accepted Result

- recovery results / state / model-state rows: `11 / 11 / 11`
- recovery closure rows: `6`
- recovery contact / gap traces: `88 / 88`
- composite canonical rows: `31` from Attempt 1 rows 1-22 and recovery rows 3-11
- centered raw-31 RMS / max: `0.107172 / 0.238596 mm`
- centered equal-unique-20 RMS / max: `0.103060 / 0.218333 mm`
- reconstructed H0 equal-unique RMS / max: `0.251775 / 0.592990 mm`
- B0 / B-90 cross-attempt bridges: `0.005719 / 0.013314 mm`
- worst canonical closure: `0.016482 mm`

All frozen result, state, model, pose, closure, and transaction gates pass.
Four delayed post-contact raw/mux edges were filtered across three contacts;
none reached the gated motion input. There is no accepted bad probe point.

## Evidence Classification

Attempt 1 accepted canonical rows 1-22, then rejected a false electrical
pass-2 W touch before accepting row 23. The probe was reseated and machine
power was later lost. Recovery Attempt 2 independently bridged to Attempt 1 at
B0 and B-90 before acquiring the missing rows. The rejected transaction is
retained in the Attempt-1 partial prerequisite and is never composed into this
result.

The composite is sufficient engineering evidence for the current T3
differential-bank verification stage. It is not a formal uninterrupted T3
release. A fresh 31-row acquisition is required only if that stronger evidence
classification is later needed.

## Validation

- recovery runner SHA-256:
  `1924e4af8be964a29442f23903e3566daceb4e65dde0e334bd595ba2dcb31294`
- recovery validator SHA-256:
  `cb8960567f39d08bf0ef303110e49910fe50f1d9bb828b200803ba4a6ebe47a1`
- source-tree commit: `86dd4068016ab748cf0e0e454075f2e2b6b6a7d2`
- source-tree description: `v2.9.8-168-g86dd406801-dirty`
- runtime `milltask` SHA-256:
  `23f640db275c1fb5f8e2d938448ce1a0cd726ea002e3550e52439a9396ef1625`
- runtime `headheadkins.so` SHA-256:
  `1cc5b7023bed01bd2eb56bb52139e74f964cf17754b440aff42a987f4b22ac4c`
- standalone `rs274` SHA-256:
  `1ac7ac4e0e2f3ae07a42ca02a34730d370651063e7dcfcc093643d76063cb4c9`

The validator is file-only. It imports no LinuxCNC or HAL module and starts no
subprocess. A separate read-only live audit confirmed the completed controller
state; that audit issued no command, load, mode change, MDI, or motion.

## Contents

This archive contains:

- the exact recovery and Attempt-1 runners and all twelve acquisition CSVs;
- the recovery validator, frozen Attempt-1 validator, imported analysis
  dependencies, operator plans, preflight reports, closeout report, model plan,
  configuration README, and resume checkpoint;
- the complete read-only recovery preflight prerequisite archive, including
  the sealed Attempt-1 partial and T4 prerequisites;
- the dedicated validation INI, coefficient overlay, probe counter HAL,
  machine/shared HAL, tool table and parameter snapshots, remap/TWP sources,
  and relevant kinematics/interpreter sources and runtime binaries;
- the file-only validation command, environment, stdout/stderr transcript,
  exit status, independent-review summary, and final live-state audit;
- a point-in-time copy of the 100 Hz probe-edge log after M2, the milltask
  lifecycle log, and their diagnostic helpers.

LinuxCNC was intentionally still running and idle when the point-in-time logs
and final state were captured. The archived milltask log therefore records
launch state but no process-exit record. Program completion and acquisition
validity are established independently by the terminal M2 state, completed
CSV contracts, edge log, file-only validator, and live-state audit.

The copied runtime binaries are supporting evidence, not a bootable LinuxCNC
snapshot. `SHA256SUMS` authenticates every archived file except itself.
After checksum generation, write permission is removed from every archive
member and directory while existing executable bits are preserved.

Physical accuracy evidence covers only T3 through T4
(`128.606729..229.407000 mm`). Longer-tool accuracy remains extrapolation
until the planned dial-gauge endpoint test.
