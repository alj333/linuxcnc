# T3 R2-Transfer Attempt-4 Recovery Preflight

- status: `PASS`
- disposition: `R2 NOT ACCEPTED`
- campaign/mode/attempt: `2026082601/31/4`
- recovery runner SHA-256: `b0f33c47d76df4401353838cd93be2af5ca4c38b2f835e55d355b11220a0a15a`
- A1 archive `SHA256SUMS` SHA-256: `85306077f177700c49fc122fc79d2e24edbc7ab5d11b25209a8e7eb35439d700`
- sealed A1 results/state/local closures: `14 / 14 / 2`
- sealed A1 contact/gap rows: `119 / 119`
- sealed A1 terminal: `seq15 try1/pass2/contact3 no touch; 6.000000 mm`
- A2 archive `SHA256SUMS` SHA-256: `053344b2cf1676f6ae06ec3ae53a65ec3b7decd9e726839ed7fb94ed595a3df2`
- sealed A2 results/state/local closures: `8 / 8 / 1`
- sealed A2 contact/gap rows: `64 / 65`
- sealed A2 terminal: `seq23 try1/pass1/contact1 pre-G38 gap burst; raw/mux/gated delta 4/4/0`
- A3 forensic archive `SHA256SUMS` SHA-256: `841640923c31a7b4275bb2edc7e4273f1e64a4dd70624b1ed0f815902cedd5f7`
- sealed A3 accepted centers/contact/gap rows: `0 / 2 / 3`
- sealed A3 terminal: `zero accepted; seq23 try1/pass1/contact3 pre-G38 gap burst 5/5/0`
- fresh A4 outputs: `five exact header-only files`
- A4 accepted-row contract: `global seq23-31; 9 results and 9 states`
- A4 source-local closure order: `200`
- A4 electrical policy: `direct 1/1/1 required; matched raw/mux-only repeats and gaps retained as diagnostics`
- composite closure contract: `4 validated source-local + 10 offline cross-source`
- formal same-acquisition 31/31/14: `cannot be satisfied by this three-source recovery`
- motion boundary: `one M0; no axis, rotary, or probe motion before M0`
- parser boundary: `static Python checks only; rs274/LinuxCNC/HAL not invoked`
- analyzer SHA-256 at execution: `cce6702da6f48966f2088a19be5e58445a2dc1e777ef0b232cf1459c7ca74d1c`

The runner starts from the operator-established B-90/C90 top-clear point
for the sequence-23 restart. Loading this file authorizes no motion. The operator
owns Cycle Start, Resume, Hold, Abort, jog, MDI, and machine observation.
