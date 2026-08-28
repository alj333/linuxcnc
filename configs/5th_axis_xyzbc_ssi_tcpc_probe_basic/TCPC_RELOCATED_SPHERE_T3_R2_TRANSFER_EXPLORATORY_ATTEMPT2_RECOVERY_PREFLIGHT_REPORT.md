# T3 R2-Transfer Attempt-2 Recovery Preflight

- status: `PASS`
- disposition: `R2 NOT ACCEPTED`
- campaign/mode/attempt: `2026082601/31/2`
- recovery runner SHA-256: `1fd88b02972d4a09d2aedd5615e6b5471721b69b6c6a6b901a2c20d8a7b96f66`
- A1 archive `SHA256SUMS` SHA-256: `85306077f177700c49fc122fc79d2e24edbc7ab5d11b25209a8e7eb35439d700`
- sealed A1 results/state/local closures: `14 / 14 / 2`
- sealed A1 contact/gap rows: `119 / 119`
- sealed A1 terminal: `seq15 try1/pass2/contact3 no touch; 6.000000 mm`
- fresh A2 outputs: `five exact header-only files`
- A2 accepted-row contract: `global seq15-31; 17 results and 17 states`
- A2 source-local closure order: `90, -90, 906, 200`
- composite closure contract: `6 source-local + 8 offline cross-source`
- formal same-acquisition 31/31/14: `cannot be satisfied by this split recovery`
- motion boundary: `one M0; no axis, rotary, or probe motion before M0`
- parser boundary: `static Python checks only; rs274/LinuxCNC/HAL not invoked`
- analyzer SHA-256 at execution: `a2797be9e6849db317a8df7d45d1fa96294f294f0604f4497c830a639a7e0b4b`

The runner starts from the operator-established B-45/C0 top-clear point
left by Attempt 1. Loading this file authorizes no motion. The operator
owns Cycle Start, Resume, Hold, Abort, jog, MDI, and machine observation.
