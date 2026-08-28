# T4 New-Location Attempt-7 Adaptive-Quiet Pre-Load Archive

- sealed at: `2026-08-28T10:24:48+07:00`
- campaign / mode / attempt: `2026082701 / 41 / 7`
- status: `PASS - READY FOR EXPLICIT CONTROLLED LOAD`
- model / tool: `2026082601 / T4 H4 229.407000 mm / q=0`
- probe calibration: `#3032=0.154742`, ball diameter `6.000 mm`
- runner SHA-256: `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d`
- validator SHA-256: `b7a61c4f0ff81de1a7b330739b6ccfee3685c5aeb8bdbc53915c7d4a9c890b4b`
- reachability analyzer SHA-256: `7400d875008b393cbebe166d99b6394df75fa62c6768008f4f2817ba8fd40463`
- independent report SHA-256: `8ca61de71c856f31fad4c9a10dd0c4282c92309b80f43aa9bed60c68c789a998`
- final quiet evidence SHA-256: `2c4c9609affc5687d4547b5aacf2103f934a8c932235f906dd0020fb2a08f612`
- final state evidence SHA-256: `66a4c9828cbb1f861220cdcfc8ceb149aff8a3d15aba8f813c35dfdde57b6ab1`

## Purpose

Attempt 7 continues the T4 new-location sphere campaign after Attempt 6 was
retired. Attempt 4 owns sequences `1..9`; Attempt 6 owns accepted sequences
`10..23`; Attempt 7 reacquires all eight contacts for sequence 24 and owns
exact sequences `24..101`.

The A7 contract is `78` result/state/model rows, `25` closures, and exact
`624/624` contact/gap traces. The completed A4+A6+A7 composite contract is
`101` rows, `28` closures, and `808/808` contact/gap traces. Attempt 6's
partial sequence-24 contact and gap records remain diagnostic-only.

## Adaptive Quiet Policy

The retired fixed post-contact settling delay is replaced by a stationary
adaptive quiet handler. A clean contact uses only physical release and the
existing 10 second HAL ignore window. Matched raw/mux repeat pulses, transient
raw/mux skew, abnormal level, fault latch, or ignore activity start a 15 second
continuous quiet timer. Each new event resets that timer without repeating a
pose or probe move. Contact and gap contexts each retain a non-resetting
900 second cumulative budget.

The quiet handler contains no axis or rotary motion, G38 command, gate write,
M0, tool change, spindle command, or feed hold. It continuously checks pose,
machine state, model identity, T4/H4/TLO, SSI state, counters, and live probe
levels. Any outside-G38 gated edge remains immediately fatal. Exactly one
gated edge is still required for each successful G38 transaction, and final
raw/mux totals must match.

## Validation

The exact frozen runner passed static/source/fresh-output validation, all `23`
quiet-policy reference cases, and `81/81` adversarial mutations. Independent
reachability replay covered `78` poses and `33,837` samples, including `1,728`
coordinate-envelope vertices, `64` physical starts, and `65` handoff paths.
The minimum sphere clearance was `3.833512880 mm`; minimum noncontact entry
post clearance was `14.797951493 mm`; remaining configured linear margin was
`182.722856655 mm`. Analyzer self-test and Python compile both passed.

All six Attempt-7 output files were distinct regular files containing exactly
one schema header and zero data rows at seal time. The runner has one initial
M0, no pre-M0 axis motion, and no other hold.

## Live Readiness Evidence

At `2026-08-28T10:22:06+07:00`, LinuxCNC was active, homed, enabled, idle,
in-position, interpreter idle, and queue zero. T4/H4, G43.4, model
`2026082601 q=0`, and TLO `229.407000 mm` were active. The commanded start was
active G54 work `X0 Y0 Z0 B0 C0`, absolute
`X2501.941254485 Y696.899347451 Z-280.866128272`. Attempt 6 remained loaded;
Attempt 7 had not been loaded.

The probe receiver was visibly intermittent during preparation. Stationary,
gate-closed activity raised matched raw/mux counts while the gated count stayed
fixed at `618`. The final automated observation proved `35.190` continuous
seconds clear from `10:21:12.829` through `10:21:48.019`, with counts stable
at `1617/1617/618` and raw, mux, gate request, ignore, abnormal, fault, gated,
and motion probe-input levels all clear. The final read-only snapshot preserved
the same counts and clear levels.

The point-in-time quiet result does not claim that the intermittent receiver
cannot pulse again. Repeat the live state and quiet check immediately before
load and before Cycle Start. If pulses recur during execution, Attempt 7 is
designed to remain stationary until it obtains 15 continuous quiet seconds or
the cumulative 900 second context budget expires.

## Archive Contents

`workspace/` preserves repository-relative paths. It contains the exact A7
runner, validator, analyzer, plan, offline preflight, independent and
reachability reports, reachability CSV, and six fresh output headers. It also
contains the validation INI, base/model/probe-counter HAL files, T4 tool table,
replay dependencies, immutable Attempt-4 source data, and the accepted
Attempt-6 partial data and runner.

`evidence/` contains the final quiet excerpt and controller/HAL snapshot, the
earlier quiet and state snapshots that were followed by renewed activity, and
the bounded Attempt-6 gate-burst excerpt. `prerequisite_roots/` binds these
sealed inventories:

- Attempt-4 partial archive root:
  `d2d78d095d254cd6d59123d3d0596ac2ea8473e5e66cb7070790066447e79181`
- Attempt-6 pre-load archive root:
  `639bb502ea5029911e9d1cd745fb11a41839c2c54c39a35c74c91c7ef2b2fddc`
- Attempt-6 partial archive root:
  `d2e84c1534d63d34974a438788ea3d03522d2b597e0d116e032ef587f91adde6`

Every archive entry is a regular file or directory; there are no symlinks.
Every copied A7 artifact was verified byte-identical to its source.
`SHA256SUMS` binds every regular file below this archive except itself.

No LinuxCNC, controller, HAL write, program-load, Cycle Start, Resume, MDI,
homing, motion, or standalone `rs274` command was issued while constructing,
verifying, or sealing this archive. `READY FOR EXPLICIT CONTROLLED LOAD`
permits only a separately authorized LinuxCNC load and read-only parse/state
check. It does not authorize Cycle Start, Resume, or any machine motion.
