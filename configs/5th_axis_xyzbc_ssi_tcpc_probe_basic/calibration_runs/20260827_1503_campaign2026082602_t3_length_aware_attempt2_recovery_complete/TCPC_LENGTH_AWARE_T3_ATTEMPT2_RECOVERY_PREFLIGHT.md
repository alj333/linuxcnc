# T3 Attempt-2 Recovery Preflight

Date: 2026-08-27

Result: PASS

- Frozen runner SHA-256: `1924e4af8be964a29442f23903e3566daceb4e65dde0e334bd595ba2dcb31294`
- Identity: campaign `2026082602`, mode `34`, attempt `2`
- Contract: 11 rows, 6 closures, 88 contact traces, 88 gap traces
- Attempt-1 partial: six files hash-sealed; 22 accepted summaries, five
  closures, and complete transaction traces through unaccepted row 23
- Recovery outputs: six dedicated files, each exact schema header only
- Motion/safety layer: all 20 subroutines byte-identical to frozen Attempt 1
  after output-prefix normalization
- Source checks: ASCII, maximum line length 225, one top-level `M0`, no `M1`,
  no top-level pre-M0 axis motion, four guarded `G38.3` sites
- Runtime gates: two in-program cross-attempt bridges, four local closures,
  exact row/model/closure/trace counters, no whole-pose retry
- Offline validator: Python compile, static/preflight, strict partial semantics,
  and in-memory mapping/bridge/full-metric mutation tests pass

The preflight is file-only. It did not import LinuxCNC or HAL, invoke `rs274`,
start a subprocess, issue MDI, alter a pin, or command machine motion.

After LinuxCNC and HAL had exited and `/tmp/linuxcnc.lock` was absent, an
independent isolated `bin/rs274 -g` parse of the exact frozen runner also
passed. A second independent source/validator audit reported no blocker.
