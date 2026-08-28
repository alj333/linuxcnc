# T3 Length-Aware Attempt 1 Pre-Run Archive

Created offline on `2026-08-27` with LinuxCNC closed and
`/tmp/linuxcnc.lock` absent.

## Frozen Run Identity

- campaign / mode / attempt: `2026082602 / 33 / 1`
- model ID: `2026082601`
- tool: `T3 / H3 / 128.606729 mm`
- length interpolation: `q=1`
- runner: `tcpc_length_aware_t3_validation_2026082601_attempt1.ngc`
- runner SHA-256:
  `d6158b9ff91f5fa73a11071d314c64a442d6747f6758587415ece7c867e53bd6`
- expected accepted rows / unique poses: `31 / 20`
- expected closures: `14`
- expected contact / gap traces: `248 / 248`
- planned holds: one initial pre-motion `M0`

## Verification State

- `validate_tcpc_length_aware_t3_attempt1.py --self-test`: pass
- `validate_tcpc_length_aware_t3_attempt1.py --preflight`: pass
- isolated in-tree RS274 parse: pass
- independent static, mutation, provenance, and deterministic-report audit:
  pass with no open blocker or medium finding
- validator SHA-256:
  `88ddd9a4ead0d5a461cb7de7caa919cb878e0dcaf9dcf7633902abd86a8fbdae`
- preflight report SHA-256:
  `dc09e6df1b77426fcdb1530fda1c146cec831758a37480450a154e7e208523d0`

The six attempt output files are frozen at their one-line header state. They
must remain unchanged until this exact run is started. Any aborted or partial
acquisition retires Attempt 1 and requires new filenames and a new preflight.

## Evidence Included

The archive root contains the exact T3 runner, its canonical motion source,
the accepted T4 safety-layer source, the dedicated validation INI and HAL,
all six fresh outputs, the validator and its dependencies, the plan and
preflight report, current kinematics source and binary, edge-counter HAL, and
the reproducible T4 closeout analyzer/report.

`t4_completion_prerequisite/` is a byte-for-byte copy of the complete sealed
T4 Attempt 2 archive. Its internal `SHA256SUMS` verifies all 60 manifest
members and has SHA-256
`546377e7ed7c98f4e24e6fc239b05810ea664ea101e6bd5d79e3c36558f9a880`.
T4's formal validation report is a pass and has SHA-256
`0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae`.

`SHA256SUMS` at this archive root seals every other regular file recursively,
including the complete T4 prerequisite. Verification must be run from this
directory with `sha256sum -c SHA256SUMS`.

## Scope

This package authorizes only the operator-controlled T3 verification run.
It does not release the length-aware model for production, alter the frozen
coefficient bank, or validate extrapolation outside the measured T3-to-T4
tool-length bracket.
