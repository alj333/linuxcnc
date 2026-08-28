# T4 R2 Attempt-5 Recovery Report

Status: `COMPLETE SOURCE-LOCAL RECOVERY`

- campaign / mode / attempt: `2026082404 / 29 / 5`
- accepted result / state rows: `19 / 19`
- exact sequences: `1-9,72,93-101`
- validated closures: `14 / 14`
- worst closure: `0.019998 mm` (block 913, sequence `3 -> 95`)
- validated contact / gap traces: `152 / 152`
- successful G38 contacts: `152 / 152`
- raw / mux / gated final counts: `160 / 160 / 152`
- isolated suppressed post-contact repeats: `8`
- burst / consistency / release / terminal faults: `0 / 0 / 0 / 0`
- correction-norm range: `0.000759-0.021022 mm`
- pass-center-delta range: `0.000863-0.022766 mm`
- corrected-diameter range: `30.130500-30.336342 mm`
- standalone centered RMS / max: `0.078560 / 0.119618 mm`

Three independent structured read-only audits found no schema, ordering,
state, endpoint, closure, trace, or counter discrepancy. The eight excess
raw/mux edges occurred as isolated post-contact repeats at contact 4; every one
was blocked from the G38-facing gated input and correctly carried into the next
gap ledger.

Across the seven closures shared with Attempt 4, closure RMS improved from
`0.022358 mm` to `0.010489 mm`. Block 913 remains a repeatability signal: its
closure vector changed by `0.040884 mm` and its Y component reversed sign,
although both attempts pass the `0.050000 mm` closure limit. Treat the
four-source composite as diagnostic rather than an uninterrupted acceptance
run.

The immutable raw acquisition is
`calibration_runs/20260826_0244_campaign04_t4_candidate_r2_attempt5_complete_raw`.
Its `SHA256SUMS` SHA-256 is
`2fbbc4021d51ef7afd5fbdddcf21a1171762f2b0baec915f7c63843ff775a90d`.

No calibration parameter, kinematic geometry, B/C zero, tool-table entry, or
production/base configuration changed during this acquisition. The hardened
Attempt-5 analyzer was run only after LinuxCNC and HAL were fully closed.

## Offline Composite

The copied-workspace analyzer exited `0` with `RECOVERY CONTRACT PASS`. Its
sealed analysis archive is
`calibration_runs/20260826_0902_campaign04_t4_candidate_r2_attempt5_complete_analysis`;
the archive `SHA256SUMS` SHA-256 is
`3b155b67b718509d3228c1c2517ccfd7a4ca4a4d12ba98b9105d311c27de966c`.

- composite equal-76 centered RMS / max: `0.089045 / 0.190827 mm`
- frozen equal-76 prediction: `0.085763 / 0.204948 mm`
- composite raw-101 centered RMS / max: `0.090001 / 0.194441 mm`
- frozen raw-101 prediction: `0.087176 / 0.207789 mm`
- actual-versus-predicted pattern RMS / max: `0.030038 / 0.068496 mm`
- canonical source-local closures: `28` (`5 / 4 / 5 / 14`)

This composite aligns Attempts 2, 3, and 4 into Attempt 5's opening-B0 frame.
It removes one translation per acquisition and cannot establish uninterrupted
drift or cross-acquisition closure evidence.

## Disposition

The analyzer's recovery-contract pass validates acquisition structure, source
ownership, contacts, gaps, states, and closures. It does not enforce the six
frozen R2 statistical gates. A separate reconstruction passes 11 of 12
diagnostic gate calculations. The failure is maximum unique-pose worsening at
`B+90 C180`: `0.090202 mm` against the `0.075000 mm` limit. Baseline and
composite centered norms are `0.076479 / 0.166681 mm`.

R2 is not accepted or released. Do not refit it from this validation
composite. This result does not authorize the formal predeclared T3 transfer
verification. A separately declared exploratory T3 holdout may still supply
independent tool-length evidence, but it must run under the baseline
task-capture configuration with the R2 overlay absent and a scoring method
frozen before motion. It cannot cure the failed T4 gate or convert this
composite into a formal T4 pass.
