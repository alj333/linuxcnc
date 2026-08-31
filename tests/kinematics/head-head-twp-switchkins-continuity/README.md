# Head-head TWP switchkins continuity

This headless fixture opts into the production `G68.2`/`G69` remap with a
test-only `[TWP] ENABLE = 1`. It imports the production remap and directly
sources the commissioned `2026082601` length-model overlay instead of copying
either implementation into the test.

The test performs stationary switchkins entry and exit for:

* T3 (`L=128.606729`, `q=1`) at reached and requested `B30 C90`, with
  nonzero normal rotation `R17`.
* T4 (`L=229.407000`, `q=0`) at reached `B-30 C-350`, requested as the
  equivalent `B-30 C10` to verify continuous C-branch latching.

A nonzero G54 offset exercises the production coordinate-layer transfer. Each
active TWP interval includes a reversible one-millimetre local-X move, checked
against an independently calculated world-space plane vector. A 21-channel
HAL sampler records every servo cycle around both entry/exit pairs and rejects
joint or physical-TCP transients, model faults, invalid switch topology, and
any B/C movement while TWP is active. While each plane is active, real MDI
blocks also verify that rotary words, G53, work-offset selection, coordinate
parameter writes, arcs, tool selection, tool-length changes, and M2 fail
closed without changing the TWP transaction, tool state, model, joints, or
physical TCP. A two-line percent-delimited AUTO program separately verifies
that its closing `%` cannot end a program while TWP remains active and cannot
bypass the same continuity checks. The test then returns to MDI and exits
normally through G69.
