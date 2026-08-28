# T4 New-Location Attempt-2 Recovery Partial Report

Status: `ATTEMPT RETIRED - QUALITY ABORT AT CANONICAL SEQUENCE 21`

## Identity And Stop

- campaign / mode / attempt: `2026082701 / 36 / 2`
- runner SHA-256: `c027a0bab19f403e5e625f01fb50d6d050b51188fa0a0885dbaa795035b5c758`
- model / tool: `2026082601 / T4 H4 229.407000 mm / q=0`
- stop time: `2026-08-27 18:48:46 +07`
- stopped pose: `X2502.405372075 Y698.018973813 Z-279.792014243 B-5 C225`
- stop state: enabled, homed, idle, queue zero, in position, velocity zero,
  live probe clear, T4 active

The runner stopped itself on `Sphere pose quality failed`; the operator and
automation issued no Resume after the stop. Attempt 2 must not be resumed,
appended, restarted, or reused.

## Accepted Boundary

Recovery summary/state/model rows are exactly canonical sequence IDs
`1..9,17..20` (`13` rows). The first `104` contact/gap transactions are exact,
complete, and valid for those accepted rows. The three written closures pass:

- B0 source-local sweep closure: `0.021536 mm`
- hard Attempt-1 row-9 bridge: `0.006576 mm`
- hard Attempt-1 row-17 bridge: `0.026743 mm`

All are below the `0.050 mm` hard limit. The safe composite boundary is:

- Attempt 1: canonical rows `1..17`
- Attempt 2: canonical rows `18..20`
- combined accepted coverage: canonical rows `1..20`

Attempt-2 bridge-only repeats `1..9,17` remain continuity evidence but do not
replace the canonical Attempt-1 rows. No coordinate translation or refit is
applied.

## Rejected Sequence 21

Canonical sequence 21 is B-5/C225. Only pass 1 exists and no result, state, or
model-state row was written. Its four reported contact travels were:

- contact 1 W: `5.005950 mm`
- contact 2 U: `1.903202 mm`
- contact 3 -V: `0.609798 mm`
- contact 4 +V: `3.820871 mm`

Contact 3 violated the `1.000000 mm` minimum-travel guard. Immediately before
it, two matched raw/mux pulses occurred while the real-time probe gate was
closed (`2/2/0` raw/mux/gated). Its G38 then saw one gated edge but triggered
after only `0.609798 mm`, followed by one matched raw/mux release repeat with
no gated repeat (`1/1/0`). The pose-quality gate correctly rejected the entire
pose and stopped before pass 2 or any accepted summary row.

This is a probe pulse episode, not evidence of a TCPC, SSI, length-model, or
counter-consistency failure. No release, burst, terminal, SSI, or model fault
was set. The full run recorded five matched raw/mux diagnostic extra edges
that did not reach motion; the invalid gated touch itself is rejected rather
than filtered because its position is unsafe to treat as sphere data.

## Frozen Output Hashes

- results: `9dcec878f993c81eb053016f6112816cf95686b400b1ae789ec0ff3a77d2a7a0`
- state: `b6649bd662e9be9c1ffd1b3ad79f6d555b4eabc761c849021e8ba7af6ac85583`
- model-state: `771dedb2cf29a2716917291ae15f851786783e4a76ffbbbc6a7cddb9ffa0523c`
- closures: `b6c59a4e7f6f509d36e25b45ad6946d1d37c39c58ec0d2e1e7d06b8060d59a8c`
- contact trace: `f132da6b56acba1aaf29add895e09ddda736813be67e40c97376f139d59c98af`
- gap trace: `27bbaf30b85fdd5d52129ca49d36cc992804dcc81f3b60abc8eb68258053c2a7`

Line counts including headers are `14/14/14/4/109/109`.

## Next Recovery Gate

A new attempt identity and fresh isolated outputs are required. Before any new
run, reset or reseat the probe and repeat the manual deflection/release and
quiet checks. The next recovery must bridge immutable accepted data, reacquire
canonical sequence 21 in full, and preserve the B-5 block closure ownership.
No row-21 trace from this attempt may enter the composite.

## Sealed Archive

The stopped evidence is sealed at
`calibration_runs/20260827_1851_campaign2026082701_t4_new_location_attempt2_recovery_partial_quality_abort_seq21`.
Its 22-entry inventory verifies, contains no symlinks or special files, and
the root `SHA256SUMS` SHA-256 is
`466c730dd4732e930f0d97da5ecbae6715374b7855535e62c7d3cf30c8437481`.
