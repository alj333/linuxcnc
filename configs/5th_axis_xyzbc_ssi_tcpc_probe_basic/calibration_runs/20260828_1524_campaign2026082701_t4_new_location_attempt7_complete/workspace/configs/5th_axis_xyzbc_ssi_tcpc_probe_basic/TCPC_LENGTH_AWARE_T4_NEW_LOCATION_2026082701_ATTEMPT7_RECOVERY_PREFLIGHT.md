# T4 New-Location Attempt-7 Recovery Preflight

Status: `PASS - OFFLINE CONTRACT; LIVE QUIET-STATE PENDING`

## Frozen Inputs

- runner SHA-256: `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d`
- A4 results SHA-256: `835974bf0f352e722720f0a5046fc8d7a038b10273f642c795be57713ffeaaa1`
- A6 results/state/model SHA-256: `06752f2d73dc1ecbf1f605922e2270c55aba0a81e60640bc9e5217730bb785e6 / 9497b7f047b3b674f496e9dd8f1c27594ed35ddd8e54bda1aa59308ac312a449 / 7ff4da12561c90af7306c7a2925d482d746a7647b33b17f1558d5ab920029f03`
- A6 closures/contact/gap SHA-256: `ff4d020689ee7f8d6e1d13584829a6a51e955a406613743572ea5f17cfa9ae32 / 37ce836c1914fe27328d14613e402dec895afa61b7e7e4a56aaaf127f480cf28 / 8fb60a0f3baf2fc57cabffcb1144c6c2cbf870e6480d3c593a35642fe777a14d`
- A6 partial archive root: `d2e84c1534d63d34974a438788ea3d03522d2b597e0d116e032ef587f91adde6`
- base HAL / model HAL / validation INI SHA-256: `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778 / 8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14 / 24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a`
- validator / analyzer SHA-256: `b7a61c4f0ff81de1a7b330739b6ccfee3685c5aeb8bdbc53915c7d4a9c890b4b / 7400d875008b393cbebe166d99b6394df75fa62c6768008f4f2817ba8fd40463`
- reachability report / CSV SHA-256: `e89a703d1f1c0975fb20a810394b7a17af8b4f0132a4cfdf7ad738c6f1da7a7b / 4fa0a2bbcbce34af25d33b70d6876f8e1cf0f19a44a6bc85fdd82329599b3062`

## Start Contract

Active G54 work is exactly `X0 Y0 Z0`, absolute
`X2501.941254485 Y696.899347451 Z-280.866128272`, B0/C0, T4/H4, G43.4.
G54 offsets are `X2501.941254485 Y696.899347451 Z-510.273128272` and TLO Z
is `229.407000 mm`. Separate work/G54/absolute guards use `0.050 mm`; the
post-load physical hold guard uses `0.001 mm`.

The A6 sequence-23 center-derived first target is
`X2501.156895000 Y696.528585000 Z-279.734825000`, a nominal
`1.425668857 mm` first segment. This is followed by the validated 25 mm Z
lift, B10/C0 index, XY move, and Z descent before full sequence-24 probing.

## Static Contract

- exact identity / seed: `mode41 / attempt7 / sequence23`
- exact A7 topology: sequences `24..101`, `78` accepted rows
- A7 closures: `14` same-run plus `11` external = `25`
- traces: `624/624`; composite A4+A6+A7: `101 / 28 / 808/808`
- single M0, no pre-M0 axis motion, no other hold, no pose retry
- six distinct regular header-only Attempt-7 outputs; no stale LOGAPPEND path
- four G38.3 sites and four immediately adjacent final guards
- no fixed `G4 P10.0` or `G4 P15.0`; three `G4 P#793` sites are sampled
  release/ignore/quiet loops with `#793=0.25`
- matched gate-closed raw/mux extras are diagnostic; chatter requires 15.0
  continuous quiet within non-resetting 900 second contact or gap budgets
- pre-M0 counters anchor hold-time chatter; the accepted startup baseline is
  recaptured only after conditional quiet
- gap budget reset ownership is limited to accepted startup recapture and an
  accepted contact; trace-begin cannot reset it
- transient raw/mux partition skew may catch up; final cumulative raw=mux,
  exactly one successful G38 gated edge, and zero gated repeats/gaps stay hard
- stationary quiet has no motion, gate write, or hold and runs full live/model/
  tool/TLO/SSI/pose plus counter/level guards at each sample
- Attempt-7 trace schema 2 has explicit schema-1 mapping for immutable A4/A6
- immutable A4 reference centers and A6 sequence-23 seed match source hashes

Frozen validator results: static/source/fresh-output checks PASS, `23`
reference quiet cases PASS, and `81/81` adversarial mutations are rejected.
The canonical A5/A7 subroutine comparison strips only approved adaptive-guard
calls, A5's retired fixed dwell, trace-call arity, and output-path identity;
the remaining motion-driving assignments, geometry, quality math, logging,
feeds, and G90/G91/motion commands are byte-equivalent.

## Reachability

The offline replay explicitly solved the simultaneous work/G54/TLO/absolute
guard polytope: `12` vertices per axis, `1,728` XYZ layer states, `64` unique
physical starts, and `65` handoff paths including nominal.

- replayed points: `33,837`
- nominal / worst first-segment length: `1.425668857 / 1.506211874 mm`
- nominal / worst first-segment sphere clearance: `3.886021634 / 3.833512880 mm`
- minimum effective-post clearance over the noncontact first entry:
  `14.797951493 mm`
- remaining configured linear margin after `5.050 mm` reserve:
  `182.722857 mm`
- rotary configured margins: B `10 deg`, C `44 deg`

The post ray begins at the sphere surface toward X-/Y+/Z-. The post model is
used only for the noncontact first entry; intentional sphere probe/overtravel
samples are excluded from that physical-post claim. Prior operator clearance
confirmation remains authoritative for probe body, holder, stand, and fixture.

Evidence:

- `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT7_RECOVERY_REACHABILITY_REPORT.md`
- `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-reachability.csv`
- `analyze_tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery_reachability.py`
- `validate_tcpc_length_aware_t4_new_location_2026082701_attempt7_recovery.py`

A stationary observation saw matched raw/mux counters rise `1259 -> 1283` in
bursts over roughly 50 seconds, with gated fixed at `618`, then quiet after
`08:40:28`. The automatic policy waits for 15.0 continuous quiet after the
last activity and hard-aborts when a contact or gap context consumes its
cumulative 900 second budget. This does not relax any gated-input invariant.
The pre-load archive and runtime-ready declaration remain withheld until a
fresh read-only quiet-state snapshot passes after the operator resets or
reseats the probe. No LinuxCNC, HAL control, motion, or standalone rs274
command was used in this construction and verification.
