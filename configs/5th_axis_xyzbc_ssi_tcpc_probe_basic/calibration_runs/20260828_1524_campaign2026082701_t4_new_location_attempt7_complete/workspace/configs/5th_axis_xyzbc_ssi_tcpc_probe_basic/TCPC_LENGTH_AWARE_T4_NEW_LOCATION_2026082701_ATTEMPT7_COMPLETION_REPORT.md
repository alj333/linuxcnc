# T4 New-Location Attempt-7 Completion Report

Status: `PASS - DATA INTEGRITY; ACCURACY FIT/REVIEW REQUIRED`

- campaign / mode / attempt: `2026082701 / 41 / 7`
- runner SHA-256: `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d`
- exact A7 rows / closures / traces: `78 / 25 / 624/624`
- exact composite rows / closures / traces: `101 / 28 / 808/808`
- A7 raw centered RMS / max: `0.147646 / 0.349931 mm`
- composite raw centered RMS / max: `0.141802 / 0.351243 mm`
- composite equal-76-pose RMS / max: `0.146265 / 0.337105 mm`
- prior reference-location guide `0.120/0.280 mm`: `EXCEEDED - diagnostic, not a data rejection`
- worst same-run / cross-attempt closure: `0.029799 / 0.060516 mm`
- admitted G38 edges: `624`
- filtered matched raw/mux extras: `53` (`30` contact, `23` gap)
- adaptive quiet episodes: `20` contact + `2` gap
- adaptive quiet elapsed: `368.50 s`; resets `13`
- largest contact / gap / combined extra burst: `7 / 22 / 29` edges
- counter chain: `1630/1630/618` -> `2307/2307/1242`

All identities, sequence ownership, poses, result geometry, state snapshots, T4/TLO values, q=0 model vectors, closure vectors and limits, counter chains, exactly-one gated G38 edges, zero outside-G38 gated edges, quiet timing, and terminal fault flags passed.

The adaptive policy handled matched gate-closed receiver chatter without accepting a false gated probe edge. The accuracy guide is intentionally not used as a data-integrity rejection at this second table location; the observed location-dependent residuals are evidence for the next offline fit and machine-volume separation step.

## Output Hashes

- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-results.csv`: `3bf1ae345503cc338e953d3f1174637f54aff078ba359d91147a83326e467730`
- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-state.csv`: `755290df7f6b4aa39d41839d19a96c3bf16250a2d5ca956cc2e28d6f52328602`
- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-model-state.csv`: `7282676b53c41db3c42337fa8a111674fad6b236ee97f8e49d2dd7663af37379`
- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-closures.csv`: `7269b0b24b5d3a49f0d4adae40a4794ac30fb79d2d0d2f36c74662d3d703d9fe`
- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-contact-trace.csv`: `6801ee3e8b8bdbbfbfbca859497a2acbdbd8e6d9672e99688f9350d7a2140afe`
- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-gap-trace.csv`: `ef3ff481a1c6c3a80cbcdfd4f002ae7535b0d255e6d07d3049bcf335975ee348`

This validator imports neither LinuxCNC nor HAL and issued no controller command.
