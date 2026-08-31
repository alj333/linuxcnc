# Head-head TWP switchkins continuity

This headless fixture opts into the production `G68.2`/`G53.1`/`G69` remap with a
test-only `[TWP] ENABLE = 1`. It imports the production remap and directly
sources the commissioned `2026082601` length-model overlay instead of copying
either implementation into the test.

For each tool, `G68.2` first defines a frame while world kinematics and public
TCPC remain off. `G53.1` then performs the stationary switchkins entry, and
`G69` exits and clears the frame. The test covers:

* T3 (`L=128.606729`, `q=1`) at reached `B30 C90`, defined with Fusion-style
  rotating-`ZXZ` `X/Y/Z/I/J/K` words and nonzero normal rotation `R17`.
* T4 (`L=229.407000`, `q=0`) at reached `B-30 C-350`, requested as the
  equivalent `B-30 C10` to verify continuous C-branch latching.

A nonzero G54 offset exercises the production coordinate-layer transfer. Each
active TWP interval includes a reversible one-millimetre local-X move, checked
against an independently calculated world-space plane vector. A 21-channel
HAL sampler records every servo cycle around both entry/exit pairs and rejects
joint or physical-TCP transients, model faults, invalid switch topology, and
any B/C movement while TWP is active.

Each active plane also runs `G38.3` along local X in two modes. A no-contact
move must reach its programmed endpoint with `#5070=0`. A second move drives
the simulated `motion.probe-input` after 1.25 mm, must stop before its 4 mm
endpoint with `#5070=1`, and must report consistent local XYZ and fixed B/C in
`#5061` through `#5066` with zero unused `#5067` through `#5069`. Both moves
are checked against the independent world-space plane vector and retract to
their starting physical TCP before the test continues. The interpreter values
are read back through a `DEBUG` block, so this covers the real task/interpreter
probe-result path rather than only the Python status mirror.

While each plane is active, real MDI blocks additionally verify that rotary
words, G53, work-offset selection, coordinate parameter writes, arcs,
`G38.2`, `G38.4`, `G38.5`, tool selection, tool-length changes, and M2 fail
closed without changing the TWP transaction, tool state, model, joints, or
physical TCP. The rejected probe variants additionally preserve the motion
probe latch and every `#5061..#5069/#5070` result parameter. A two-line
percent-delimited AUTO program separately verifies that its closing `%` cannot
end a program while TWP remains active and cannot bypass the same continuity
checks. The test then returns to MDI and exits normally through G69.
