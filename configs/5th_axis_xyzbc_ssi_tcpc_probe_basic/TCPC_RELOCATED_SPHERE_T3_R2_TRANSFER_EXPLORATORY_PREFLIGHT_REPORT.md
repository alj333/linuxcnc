# T3 R2-Transfer Exploratory Preflight

- status: `PASS`
- disposition: `R2 NOT ACCEPTED`
- campaign/mode/attempt: `2026082601/30/1`
- runner SHA-256: `90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5`
- diagnostic INI SHA-256: `347a0bfb9f616875fa7c68a24d9134269a0e4dce967deca11b21d278a2b49a47`
- analyzer SHA-256 at execution: `ba863ff3747ed1efe7540616423369b424452cc331c42568a211583f6350f00c`
- outputs: five exact header-only files
- pose/closure contract: `31 / 14`
- parser/replay: `isolated-HOME RS274 PASS; configured-limit replay PASS`
- motion boundary: one pre-motion M0; no intermediate holds
- implementation: Attempt-5 probe transaction/filter/retry/transit blocks match
- configuration: baseline plus observation counters only; R2 overlay absent

Configured-limit replay does not release physical T3 body, holder, cable,
sphere-post, sphere, or fixture clearance. The operator must confirm those
at the sole initial M0. Loading the file authorizes no motion.
