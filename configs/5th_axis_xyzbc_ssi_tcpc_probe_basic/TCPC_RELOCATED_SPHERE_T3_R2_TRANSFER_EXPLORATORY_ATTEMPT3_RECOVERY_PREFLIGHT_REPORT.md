# T3 R2-Transfer Attempt-3 Recovery Preflight

- status: `PASS`
- disposition: `R2 NOT ACCEPTED`
- campaign/mode/attempt: `2026082601/31/3`
- recovery runner SHA-256: `9db6d03a12085928fb3fe9eacea203e240ee5d52274f5cb04e23d2e981fb18ed`
- A1 archive `SHA256SUMS` SHA-256: `85306077f177700c49fc122fc79d2e24edbc7ab5d11b25209a8e7eb35439d700`
- sealed A1 results/state/local closures: `14 / 14 / 2`
- sealed A1 contact/gap rows: `119 / 119`
- sealed A1 terminal: `seq15 try1/pass2/contact3 no touch; 6.000000 mm`
- A2 archive `SHA256SUMS` SHA-256: `053344b2cf1676f6ae06ec3ae53a65ec3b7decd9e726839ed7fb94ed595a3df2`
- sealed A2 results/state/local closures: `8 / 8 / 1`
- sealed A2 contact/gap rows: `64 / 65`
- sealed A2 terminal: `seq23 try1/pass1/contact1 pre-G38 gap burst; raw/mux/gated delta 4/4/0`
- fresh A3 outputs: `five exact header-only files`
- A3 accepted-row contract: `global seq23-31; 9 results and 9 states`
- A3 source-local closure order: `200`
- composite closure contract: `4 validated source-local + 10 offline cross-source`
- formal same-acquisition 31/31/14: `cannot be satisfied by this three-source recovery`
- motion boundary: `one M0; no axis, rotary, or probe motion before M0`
- parser boundary: `static Python checks only; rs274/LinuxCNC/HAL not invoked`
- analyzer SHA-256 at execution: `0e62885fcbe6d0d13ca19bcf69cc2c7232da33edd383cb9325dc94fb444c6a23`

The runner starts from the operator-established B-90/C90 top-clear point
left after Attempt 2. Loading this file authorizes no motion. The operator
owns Cycle Start, Resume, Hold, Abort, jog, MDI, and machine observation.
