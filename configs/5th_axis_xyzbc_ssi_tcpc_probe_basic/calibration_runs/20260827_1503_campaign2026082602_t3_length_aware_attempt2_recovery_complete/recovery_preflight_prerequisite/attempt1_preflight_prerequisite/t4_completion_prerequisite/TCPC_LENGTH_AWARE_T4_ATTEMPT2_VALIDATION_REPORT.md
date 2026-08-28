# TCPC Length-Aware T4 Validation Result

Status: `PASS`

- campaign / mode / attempt: `2026082602 / 32 / 2`
- exact rows: `101` results, `101` state, `101` model-state
- closures: `28`; worst `0.040366 mm`
- transaction traces: `808` contact / `808` gap
- direct duplicate transactions: `0`
- delayed/repeat extra transactions: `14`
- contact-window filtered extras: `14` transactions / `14` edges
- inter-contact filtered extras: `1` transactions / `1` edges
- maximum contact-window filtered extras: `1 / 2`
- maximum combined filtered extras: `1 / 2`
- raw-101 centered RMS / max: `0.105164 / 0.245253 mm`
- equal-unique-76 centered RMS / max: `0.107589 / 0.241710 mm`
- acceptance limits: RMS `<=0.120 mm`, max `<=0.280 mm`

All identities, poses, T4 tool/TLO values, model snapshots, q=0 differential bank, empirical vectors/norms/caps, transaction counters/flags, and closure mappings passed.

This T4 acquisition validates the common model surface at `q=0` only. It does not validate the length differential or longer-tool extrapolation.
