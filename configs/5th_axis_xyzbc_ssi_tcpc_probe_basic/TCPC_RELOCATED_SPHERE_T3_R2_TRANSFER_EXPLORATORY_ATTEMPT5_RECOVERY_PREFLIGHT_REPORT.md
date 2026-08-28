# T3 R2-Transfer Attempt-5 Recovery Preflight

- status: `PASS`
- disposition: `R2 NOT ACCEPTED`
- campaign/mode/attempt: `2026082601/31/5`
- recovery runner SHA-256: `1bef6382eda66d81abe2d371a2bb62668ab2386e54b9cfcac820dd4de8779f2c`
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
- A4 partial archive `SHA256SUMS` SHA-256: `5f0fa30df3b7cf3e326e44671c30cd231e4c6d74b82059d9fd359fc14923ebfa`
- sealed A4 accepted/contact/gap/local-closure rows: `1 / 8 / 8 / 0`
- sealed A4 accepted source: `seq23 B-90/C90; correction 0.001012 mm; pass delta 0.001387 mm`
- sealed A4 terminal: `seq24 B-90/C180 before G38; pending matched 13/13/0 gap; fault latch active`
- sealed A4 passive snapshot: `41/41/0 total post-seq23 edges; final 829/829/192`
- fresh A5 outputs: `five exact header-only files`
- A5 accepted-row contract: `global seq24-31; 8 results and 8 states`
- A5 source-local closure order: `200`
- A5 electrical policy: `direct 1/1/1 required; matched raw/mux-only repeats and gaps retained as diagnostics`
- A5 bounded settle: `two consecutive clear 0.05 s samples within 10.00 s before every G38, followed by final guards`
- composite closure contract: `4 validated source-local + 10 offline cross-source`
- formal same-acquisition 31/31/14: `cannot be satisfied by this four-source recovery`
- motion boundary: `one M0; no axis, rotary, or probe motion before M0`
- parser boundary: `static Python checks only; rs274/LinuxCNC/HAL not invoked`
- analyzer SHA-256 at execution: `77c25e543190b336e17049410526d9d41b58cc8e3ae39ef6892e3460c9b9a5b4`

The sealed A4 pulse snapshot found no defensible debounce discriminator:
accepted/gated n=167 high-time min/median/max was 39.935/50.005/50.940 ms;
ungated faults n=608 was 39.872/49.998/100.098 ms. A later live, unsealed
observation reached n=762 with the same summary; that count is context only.
Pulse width is diagnostic only and is not an acceptance gate.

The operator must reseat/reset T3 and complete a fresh quiet qualification
before this run. The runner starts from the operator-established B-90/C180
top-clear point for sequence 24. Loading this file authorizes no motion. The operator
owns Cycle Start, Resume, Hold, Abort, jog, MDI, and machine observation.
