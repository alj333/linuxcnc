# T4 New-Location Attempt-7 Independent Validation

Status: `PASS - OFFLINE ARTIFACTS VALIDATED; LIVE QUIET-STATE PENDING`

This was an independent, read-only controller review. It did not access or
operate LinuxCNC, HAL, motion, program control, or standalone `rs274`. The
only edited artifact is this report.

## Frozen Candidate

- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.ngc`
- campaign / mode / attempt: `2026082701 / 41 / 7`
- runner SHA-256: `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d`
- runner size: `2,284` lines / `108,039` bytes / maximum line `225` bytes
- validator SHA-256: `b7a61c4f0ff81de1a7b330739b6ccfee3685c5aeb8bdbc53915c7d4a9c890b4b`
- analyzer SHA-256: `7400d875008b393cbebe166d99b6394df75fa62c6768008f4f2817ba8fd40463`
- reachability report SHA-256: `e89a703d1f1c0975fb20a810394b7a17af8b4f0132a4cfdf7ad738c6f1da7a7b`
- reachability CSV SHA-256: `4fa0a2bbcbce34af25d33b70d6876f8e1cf0f19a44a6bc85fdd82329599b3062`
- immutable Attempt-6 partial archive root:
  `d2e84c1534d63d34974a438788ea3d03522d2b597e0d116e032ef587f91adde6`

## Start And Entry

- The frozen start is active G54 work `X0 Y0 Z0 B0 C0`, G54 offsets
  `X2501.941254485 Y696.899347451 Z-510.273128272`, TLO
  `X0 Y0 Z229.407000`, and absolute
  `X2501.941254485 Y696.899347451 Z-280.866128272`.
- Work, G54, and absolute coordinates retain independent `0.050 mm` per-axis
  guards. The post-M0 physical position guard remains `0.001 mm`.
- There is exactly one `M0`, no axis motion before it, and no other hold.
- Raw/mux/gated counters are captured immediately before M0. Conditional
  startup quiet closes hold/resume activity against that origin, then the
  accepted baseline is recaptured. Hold-time pulses cannot be absorbed by a
  post-M0 baseline reset.
- The immutable accepted Attempt-6 sequence-23 center
  `X2501.156895 Y696.528585 Z-302.580083` is the only prior-center seed.
  Attempt-6's partial sequence-24 touch remains diagnostic-only.
- The first target is the center-derived B0/C0 top-clear
  `X2501.156895 Y696.528585 Z-279.734825`. The nominal start-to-target delta
  is `[-0.784359485, -0.370762451, +1.131303272]`, length
  `1.425668857 mm`.
- The first two axis motions remain start-to-top-clear and the 25 mm Z lift.
  The validated path then indexes B10/C0 at high Z, positions XY, descends in
  Z, and reacquires the whole sequence-24 pose. No stale B10 recovery path or
  direct start-to-G54-zero move remains.

## Ownership And Topology

- Attempt 7 owns exact sequences `24..101`: `78` result/state/model rows,
  `25` closures, and `624/624` contact/gap trace rows.
- Composite ownership is A4 `1..9`, A6 `10..23`, and A7 `24..101`, yielding
  `101` summaries, `28` closures, and `808/808` traces.
- The `14` true A7 same-run closures retain the `0.050 mm` hard limit. The
  `11` A4-to-A7 continuity closures retain the separate `0.100 mm` limit.
- Sequence 24 is reacquired as two complete four-contact passes. No incomplete
  Attempt-6 sequence-24 contact or gap row is accepted into the composite.
- The established W, sign-aware upper-U, -V, +V contact geometry, probe
  vectors, retracts, feeds, travel checks, diameter checks, center checks, and
  pose ordering remain unchanged apart from stationary adaptive guards.

## Adaptive Quiet Policy

- Matched raw/mux activity with zero gated delta is diagnostic and has no
  count ceiling. `#779=900.0` is elapsed-time budget, not an edge allowance.
- A clean contact waits only for physical release and the existing `10.0 s`
  HAL ignore window. There is no fixed successful-contact `G4 P10.0` or
  `G4 P15.0`.
- Chatter starts a `15.0 s` continuous quiet timer sampled every `0.25 s`.
  Each counter edge, transient raw/mux skew, active raw/mux level, abnormal
  level, or fault-pause latch resets the 15 second timer.
- Transient raw/mux partition skew may catch up. Acceptance requires final
  cumulative raw and mux deltas to match and all raw/mux/abnormal/fault/ignore
  levels to be clear.
- All quiet episodes and race retries in one between-contact gap share one
  non-resetting `900.0 s` cumulative budget. Release/finish retries share a
  separate non-resetting `900.0 s` contact budget.
- Gap ownership resets only after accepted startup recapture and after an
  accepted contact trace. `trace_begin` cannot reset an active gap budget.
  This covers startup, post-motion boundaries, complete transit/reposition,
  ready/final races, and the interval immediately adjacent to each G38.
- The motion-boundary, stationary quiet, release, trace-finish, and final
  guards contain no axis/rotary motion, G38, gate write, or operator hold.
  Live machine/model/tool/TLO/SSI/pose, counter, level, motion-type, and gate
  state are checked while stationary.
- Any outside-G38 gated count/input change remains immediately fatal. Every
  successful G38 still requires exactly one gated edge, zero gated repeats or
  gaps, valid release, and the unchanged live/model/travel/geometry/closure
  invariants.
- Persistent mismatch, uncleared levels/latches, release failure, or exhausted
  cumulative budget aborts. Durable DEBUG output records context, sequence,
  pass/contact, B/C, elapsed time, counters/deltas, and probe/fault/ignore
  levels for unattended diagnosis.

The policy is grounded in the stationary observation where raw/mux rose
together from `1259` to `1283` over roughly 50 seconds while gated remained
`618`, then stayed quiet after `08:40:28`. It permits only matched gate-closed
activity to settle; it does not relax the gated probe contract.

## Trace And Output Contract

- Attempt-7 contact/gap trace schema 2 adds `chatter_observed`, quiet episode,
  elapsed, and reset telemetry. Immutable A4/A6 schema-1 traces are mapped at
  ingest without rewriting their files.
- All seven LOGAPPEND sites target only six fresh Attempt-7 outputs.
- The six files are distinct regular single-link files, each with exactly one
  expected schema header and zero data rows.
- Header-only SHA-256 values:
  - results: `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93`
  - state: `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7`
  - model-state: `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd`
  - closures: `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f`
  - contact trace: `518ea7cfd7943594fe9d39af8b76b79bfa965804adae22cc8b32699fb573dffb`
  - gap trace: `e7ab4fb0012ae50a208a9db94e855bbe95a18cc2bea56fa2b5e84bd3c123ea74`

## Independent Test Results

The exact frozen-hash command passed static source checks, immutable source
hashes, fresh-output checks, the `23` quiet reference cases, reachability, and
the semantic mutation suite. All `81/81` adversarial mutations were rejected.
Mutations cover duration/budget/sample constants and frozen selectors,
counter/gated/fault behavior, reset ownership, startup origin/recapture,
motion-boundary handling, stationary-loop motion insertion, post/release/gap/
final handler removal, G38 adjacency, topology, row/trace counts, and closure
classes.

The analyzer self-test also passed independently and left its report and CSV
hashes unchanged.

## Reachability

The review solved the simultaneous work/G54/TLO/absolute coordinate
constraints rather than asserting an absolute cube. It replayed `12` vertices
per axis, `1,728` XYZ coordinate-layer states, `64` distinct mapped physical
starts, and the nominal start through the fixed entry and full tail.

- recovery poses: `78`
- sampled points: `33,837`
- physical handoff paths including nominal: `65`
- nominal / worst handoff: `1.425668857 / 1.506211874 mm`
- nominal / minimum sphere clearance: `3.886021634 / 3.833512880 mm`
- minimum modeled entry-post clearance: `14.797951493 mm`
- minimum configured linear/joint margin: `187.772856655 mm`
- remaining margin after the full `5.050 mm` reserve: `182.722856655 mm`
- configured B / C margins: `10 / 44 deg`

The modeled post ray begins at the sphere surface and extends toward X-, Y+,
Z-. Post checking is limited to the noncontact B0 handoff and sequence-24
entry. Intended contacts, overtravel, probe body, holder, fixture, and stand
clearance remain under the operator's prior physical clearance confirmation.
Stationary waits add no geometric trajectory.

## Reproduction

```bash
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/validate_tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.py --static --reachability --self-test
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery_reachability.py --self-test
```

Result: `PASS`; frozen hashes match, contracts are `78 / 25 / 624 / 624`,
composite contracts are `101 / 28 / 808 / 808`, reachability is
`78 poses / 33,837 samples`, and all `81` adversarial mutations are rejected.

## Operational Hold

This offline PASS does not load, start, or clear the machine. Program load and
Cycle Start remain operator-controlled. The pre-load archive and runtime-ready
declaration remain withheld until the root-owned live quiet-state preflight
passes after the operator's probe reset or reseat.
