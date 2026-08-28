# T4 New-Location Attempt-6 Partial Gate-Burst Report

- campaign / mode / attempt: `2026082701 / 40 / 6`
- stop time: `2026-08-28 01:12:15.194 +07:00`
- stop pose: `B+10 C0`, before sequence-24 pass-1 contact 2 `G38.3`
- disposition: `PARTIAL - RETIRED; DO NOT RESUME OR APPEND`
- runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`
- Attempt-6 pre-load archive root: `639bb502ea5029911e9d1cd745fb11a41839c2c54c39a35c74c91c7ef2b2fddc`

## Exact Stop Mechanism

Sequence 24 pass 1 contact 1 was a valid W touch. Its counter transaction was
raw/mux/gated `1172/1172/617` before G38, `1173/1173/618` immediately after,
and `1181/1181/618` at the released-state snapshot. The single gated contact
was therefore valid, while eight matched raw/mux repeat edges occurred with
the gate closed and the gated count unchanged.

One further matched raw/mux edge occurred during the gate-closed reposition
toward contact 2. The next pre-G38 transaction was consequently
`1182/1182/618`: gap extra `1`, prior-contact extra `8`, combined extra `9`.
Attempt 6 bounded this diagnostic value at `#779=8`, so it logged the terminal
gap row and aborted with:

`Raw mux gated probe counters or bounded extras are inconsistent before G38`

No sequence-24 contact-2 G38 move occurred. This was not a no-touch, travel,
pose-quality, TCPC, closure, following-error, or geometric abort. The edge
monitor shows the gated counter held at `618` for every repeat pulse.

## Accepted Ownership

Attempt 6 owns accepted sequences `10..23`: exactly `14` result rows, `14`
state rows, `14` model-state rows, and `112/112` complete contact/gap trace
transactions. Each accepted pose has two passes and four contacts. All
accepted contacts have `probe_result=1`, matched raw/mux deltas, exactly one
gated G38 edge, zero gated repeats, and no consistency, release, or terminal
flag.

The two Attempt-6 closures are usable:

- block `+5`, sequence `10 -> 16`: `0.014476 mm`, pass at `0.050 mm`
- block `-5`, sequence `17 -> 23`: `0.010175 mm`, pass at `0.050 mm`

The last accepted center, sequence 23, is
`X2501.156895 Y696.528585 Z-302.580083`.

Sequence 24 contributes one diagnostic contact row (pass 1 contact 1) and two
diagnostic gap rows (contacts 1 and 2). These partial rows are excluded from
fit and composite ownership. Attempt 5 remains a zero-row retirement. The
valid composite through this stop is:

- Attempt 4: sequences `1..9`, its valid block-100 closure, `72/72` traces
- Attempt 6: sequences `10..23`, its two valid closures, `112/112` traces
- total: `23` accepted rows, `3` retained closures, `184/184` traces

A fresh continuation from sequence 24 must acquire `78` rows, `25` closures,
and `624/624` traces. The completed A4+A6+continuation contract remains `101`
rows, `28` retained closures, and `808/808` traces.

## Accepted Quality

For Attempt-6 sequences `10..23`, maximum center correction is `0.024398 mm`,
maximum pass-center delta is `0.023082 mm`, corrected diameter spans
`30.047167..30.186877 mm`, maximum contact radial residual is `0.093439 mm`,
and every accepted travel is above `3.90 mm`. These values satisfy the frozen
runner limits.

## Frozen Stop Geometry

The read-only commanded absolute stop is:

`X2479.642700100176 Y696.528615621598 Z-298.779137642143 B10 C0`

With frozen G54 offsets
`X2501.941254484553 Y696.899347451259 Z-510.273128271562` and T4/H4
`229.407 mm`, the corresponding G54 work position is:

`X-22.298554384377 Y-0.370731829661 Z-17.913009370581 B10 C0`

At B+10/C0, `W=(-0.173648177667,0,-0.984807753012)` and
`U=(0.984807753012,0,-0.173648177667)`. The stopped point is the exact
upper-U start reconstructed from the valid W contact:

- W-derived center: `X2501.156079545128 Y696.528615621598 Z-302.572526884507`
- U start: `center - U * 21.845258 mm` (the current point)
- contact-2 vector: `+6U = (+5.908846518073,0,-1.041889066002) mm`
- successful retract vector: `-3U = (-2.954423259037,0,+0.520944533001) mm`

The safe initial escape is from the current point along `-W` to:

`X2483.609737520207 Y696.528615621598 Z-276.280950444179`

This path starts with `4.000 mm` modeled physical clearance and increases it.
From there, a traverse at W clearance to the reconstructed top-clear point

`X2505.123116965159 Y696.528615621598 Z-280.074339686543`

retains `5.000 mm` modeled physical clearance. A straight current-to-top-clear
move intersects the effective sphere envelope by `2.057 mm`. A straight move
from the current point to G54 `X0 Y0 Z0` intersects it by `1.414 mm`. Neither
straight move is an acceptable recovery path.

## Diagnostic Allowance

Across all 17 nonempty top-level paired trace datasets, `2,900` contact rows
and `2,905` gap rows were reviewed. The maximum contact extra was `8`; the
maximum combined gap extra was this stop's `9`. A bound of `12` is the minimum
data-derived operating recommendation: three edges, or 33 percent, above the
observed maximum while detecting a new escalation at 13.

A bound of `16` is also defensible for completion margin. It does not change a
hard probing or geometry safety property because the allowance applies only
to matched raw/mux extras when the gated delta is zero. Raw/mux equality, zero
gap-gated edges, synchronized clear levels, inactive ignore/fault state,
release checks, the final pre-G38 guard, and exactly one gated edge for every
successful G38 remain mandatory. The tradeoff is diagnostic sensitivity: 16
tolerates a longer gate-closed electrical burst and provides seven-edge
headroom over the observed maximum, while remaining finite.

## Frozen Data Hashes

- results: `06752f2d73dc1ecbf1f605922e2270c55aba0a81e60640bc9e5217730bb785e6`
- state: `9497b7f047b3b674f496e9dd8f1c27594ed35ddd8e54bda1aa59308ac312a449`
- model state: `7ff4da12561c90af7306c7a2925d482d746a7647b33b17f1558d5ab920029f03`
- closures: `ff4d020689ee7f8d6e1d13584829a6a51e955a406613743572ea5f17cfa9ae32`
- contact trace: `37ce836c1914fe27328d14613e402dec895afa61b7e7e4a56aaaf127f480cf28`
- gap trace: `8fb60a0f3baf2fc57cabffcb1144c6c2cbf870e6480d3c593a35642fe777a14d`

The audit and archive operation used only filesystem reads, read-only status
and HAL snapshots, and file copies. It issued no program-control, load, Cycle
Start, Resume, MDI, homing, motion, or standalone `rs274` command.
