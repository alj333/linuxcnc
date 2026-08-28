# T3 Length-Aware Attempt-2 Recovery Pre-Run Archive

Created controller-off on `2026-08-27` after the Attempt-1 quality abort and
machine-power loss. LinuxCNC/HAL processes and `/tmp/linuxcnc.lock` were absent.

## Frozen Recovery

- campaign / mode / attempt: `2026082602 / 34 / 2`
- model / tool / interpolation: `2026082601 / T3-H3 / q=1`
- runner SHA-256:
  `1924e4af8be964a29442f23903e3566daceb4e65dde0e334bd595ba2dcb31294`
- validator SHA-256:
  `cb8960567f39d08bf0ef303110e49910fe50f1d9bb828b200803ba4a6ebe47a1`
- exact recovery contract: `11` result/state/model rows, `6` closures, and
  `88/88` contact/gap traces
- holds: one initial pre-motion `M0`; no later planned hold

The first B0/C0 and B-90/C0 measurements hard-check continuity against sealed
Attempt-1 rows 16 and 22 at `0.050 mm`. Recovery rows 3-11 supply canonical
rows 23-31. The six recovery outputs are frozen at exact one-line headers.

## Verification

- Python compilation: pass
- static and fresh-output preflight: pass
- mapping, provenance, metric, and mutation self-test: pass
- isolated controller-off `bin/rs274 -g` parse: pass
- independent engineering review: no blocker

`attempt1_preflight_prerequisite/` contains the complete sealed Attempt-1
pre-run package and its complete T4 prerequisite. `attempt1_partial_prerequisite/`
contains the exact retired Attempt-1 partial, failure diagnostics, and report.
Both nested checksum manifests passed before this parent archive was sealed.

The root `SHA256SUMS` seals every other regular file recursively, including
both nested manifests. Verify from this directory with
`sha256sum -c SHA256SUMS`.

## Scope

A successful recovery supports a composite engineering verification only. It
does not convert the split/reseated data into a formal uninterrupted T3 release.
Any new stop, power loss, or probe reseat retires this recovery attempt.
