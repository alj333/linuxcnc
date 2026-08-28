# T3 Length-Aware Attempt 1 Partial Report

Status: `RETIRED PARTIAL - QUALITY GUARD ABORT AT SEQ 23`

## Identity And Counts

- campaign / mode / attempt: `2026082602 / 33 / 1`
- runner SHA-256:
  `d6158b9ff91f5fa73a11071d314c64a442d6747f6758587415ece7c867e53bd6`
- accepted result / state / model-state rows: `22 / 22 / 22`
- accepted closures: `5`
- contact / gap traces: `184 / 184`
- accepted canonical sequence: `1..22`
- failed unaccepted acquisition: sequence `23`, `B-90 C90`

The final eight contact/gap records are retained forensic evidence for the
complete but rejected sequence-23 acquisition. There is no sequence-23
result, state, or model-state row. Attempt 1 must not be resumed, appended,
truncated, or reused.

## Abort Cause

The hard pose-quality guard rejected pass 2 before it could write an accepted
row. The second-pass W/top touch occurred at `2.543169 mm`; all 22 earlier
accepted second-pass W touches were `4.974503..5.008489 mm`. The reconstructed
pass-center disagreement was `2.463369 mm` against the `0.100 mm` limit, and
the pass-2 diameter was `29.759013 mm` against the `29.900..30.500 mm` gate.

The other pass-2 contacts were coherent. All eight transactions had matching
raw/mux counts, exactly one gated edge, clean release, and no consistency or
terminal fault. The bad W event was therefore electrically indistinguishable
from a real G38 contact, but geometry proves that it occurred about `2.457 mm`
before the sphere. The operator observed the probe flashing in its known bad
receiver state. Additional raw/mux-only pulses followed outside G38.

The quality guard behaved correctly and prevented the corrupt center from
entering the accepted result set. This is a probe/receiver acquisition fault,
not evidence of a `2.46 mm` TCPC error.

## Shutdown

After the abort, machine power was lost. LinuxCNC shut down after the Mesa
read error `hm2/hm2_7i95.0: error finishing read! iter=8316115`. All LinuxCNC
processes exited and `/tmp/linuxcnc.lock` was absent before this archive was
sealed. No position from the terminated session is trusted for restart.

## Recovery Boundary

A separately identified recovery acquisition may preserve the valid first 22
rows for engineering/composite analysis if it repeats bridge poses after the
probe reseat and passes explicit cross-source closure checks. It cannot turn
this interrupted/reseated acquisition into the uninterrupted formal Attempt 1
PASS defined by the frozen plan. Formal T3 endpoint release still requires a
fresh complete 31-row attempt.
