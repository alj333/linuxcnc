# T3 Post-Load Probe Observation

Between `2026-08-26T10:05:02+07:00` and `10:06:07+07:00`, after the clean
load-only checkpoint, the observation counters advanced from `0/0/0` to
`11/11/0` raw/mux/gated edges. LinuxCNC remained disabled and unhomed, the
program remained idle at line 0, and no output row was written. The G38-only
gate correctly rejected every edge from `motion.probe-input`.

At the final sample the raw, muxed, gated, and abnormal-level signals were all
false and the counts remained unchanged through `10:07:21+07:00`. The source
of the pulses has not been classified as deliberate hand
deflection or spontaneous T3 activity. The operator must classify it before
Cycle Start. Persistent glow, spontaneous pulsing, a stuck level, or unmatched
raw/mux counts bars the run.

The runner does not require counters to start at zero. It freezes the current
sticky counts only after the sole M0 and requires no intervening activity
before the first G38. Therefore this post-load activity does not alter or
contaminate an acquisition that has not started, but any new edge across the
post-M0 boundary fails closed.
