# TCPC Calibration Resume Checkpoint

## Current Handoff - T4 Attempt 2 Double-Pulse Handling, 2026-08-27

- T4 length-aware Attempt 2 completed all 101 poses at
  `2026-08-27T03:56:52+07:00` and formal post-shutdown validation passed. Exact
  counts are `101/101/101` result/state/model-state rows, `28` closures, and
  `808/808` contact/gap traces. LinuxCNC is now closed.
- Centered raw-101 RMS/max are `0.105164/0.245253 mm`; equal-unique-76 RMS/max
  are `0.107589/0.241710 mm`; closure RMS/max are
  `0.022237/0.040366 mm`. These pass the frozen `0.120/0.280 mm` centered-error
  and `0.050 mm` closure limits.
- The revised pulse policy was exercised successfully. Terminal raw/mux/gated
  counters were `823/823/808`: 14 delayed post-contact extras and one
  inter-contact extra were logged and filtered, with no raw/mux mismatch,
  second gated edge, burst, release fault, or terminal failure.
- Formal report `TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md` SHA-256 is
  `0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae`.
  The completion archive is
  `calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete`.
- This validates the T4 `q=0` common correction bank only. No production
  promotion is authorized yet; the next physical gate is a deliberately
  smaller T3 run that verifies the length-differential bank without retuning.

- T4 length-model Attempt 1 is retired after 36 complete poses. At sequence 37
  it recorded a successful G38 transaction with direct raw/mux/gated deltas
  `2/2/1`; the second raw/mux edge arrived about 50 ms after the real-time G38
  gate closed and could not change the captured touch point. Do not resume,
  append, truncate, or reuse the Attempt 1 runner or outputs. See
  `TCPC_LENGTH_AWARE_T4_ATTEMPT1_PARTIAL_REPORT.md`.
- A fresh full Attempt 2 is prepared as campaign/mode/attempt
  `2026082602/32/2`. Its runner is
  `tcpc_length_aware_t4_validation_2026082601_attempt2.ngc`, SHA-256
  `d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d`.
  All six Attempt 2 outputs are separate exact header-only files.
- Attempt 2 permits zero, one, or two matching raw/mux extra pulses only after
  proving a successful G38 touch, exactly one gated motion edge, no gated
  repeat, bounded counter consistency, and a clean two-sample release. Every
  extra pulse is logged. A mismatch, missing or second gated edge, more than
  two extras, no-touch, unstable pre-G38 state, or release failure still
  aborts. The realtime HAL gate and all probing motion are unchanged.
- The formal run has no automatic whole-pose retry and must produce exactly
  `101/101/101` result/state/model-state rows, `28` closures, and `808/808`
  contact/gap traces. Any hard stop retires that attempt.
- The operator safely lifted from the stopped `B-10 C0` side position, returned
  to `B0 C0` above the sphere, and cleanly closed LinuxCNC. The final Attempt 1
  edge-log heartbeat confirms `B0 C0`. Attempt 1 is now preserved under
  `calibration_runs/tcpc-length-aware-t4-validation-2026082601-attempt1-retired`;
  its `SHA256SUMS` hash is
  `dfad4987a8cc7dbb99d21f39c60246d7d4872be4b669f9613b3f8062f62d8bc9`.
- With all controller processes stopped and `/tmp/linuxcnc.lock` absent, the
  full Attempt 2 integration self-test and isolated RS274 preflight passed.
  `TCPC_LENGTH_AWARE_T4_ATTEMPT2_PREFLIGHT_REPORT.md` SHA-256 is
  `8f35c96f29de6d6c0b334e42edaeb6aaacc9d7d6fdae706b82549393bdc5a544`.
- LinuxCNC has been clean-launched with the dedicated validation INI and the
  exact Attempt 2 runner is selected. At the load checkpoint the controller is
  off, unhomed, idle, queue zero, and unpaused, with tool 0, zero tool offset,
  zero velocity, and all spindles stopped. No Cycle Start or motion command was
  issued and every Attempt 2 output remains header-only.
- The machine setup is now complete and all live guards pass: all five axes
  are homed, T4/H4 is active at `229.407000 mm`, TCPC is active with TWP clear,
  B/C are within the start tolerance, both SSI invalid signals are clear, the
  length model is valid with fault `0`, the spindle is stopped, and the exact
  Attempt 2 file remains selected and idle with zero output rows. The
  authoritative order is `TCPC_LENGTH_AWARE_T4_ATTEMPT2_PLAN.md`.
- The owner is remote and explicitly retained the prior T4 functional-touch
  test because the probe has not been removed or reseated and Attempt 1 already
  supplied 290 successful contacts with clean releases. This launch therefore
  waives only a new post-restart manual deflection. A passive 30-second check
  at `00:37:22..00:37:52 +07` observed all probe levels clear and raw/mux/gated
  counters unchanged at `0/0/0`. A reseat, restart, unexpected pulse, or setup
  change invalidates this waiver.

## Current Handoff - Full Tool-Length Domain Fixed, 2026-08-26

- The active tool table spans `114.677000..411.810000 mm` across 54 tools, but
  its tracked predecessor used T69 at `425.022000 mm`. The length-aware hard
  software domain therefore covers `100.000000..430.000000 mm`, not only the
  current table or the T3/T4 bracket.
  Runtime scaling must be evaluated synchronously from active G43 Z length and
  must not clamp at either probe length. Zero length or a value outside the
  declared domain (allowing only `0.002 mm` comparison tolerance) must make
  G43.4 fail closed when the real-machine length model is enabled. A future
  tool-table extension outside this hard domain requires a new audit. The live
  active offset is authoritative because routine tool touch-off legitimately
  changes tool-table lengths; table hashes are traceability, not a permanent
  runtime interlock.
- The exploratory model is
  `H(B,C,L) = H0(B,C) + S(B,C) + q(L)D(B,C)`, where
  `q(L)=(229.407000-L)/100.800271`, `q(T4)=0`, and `q(T3)=1`. `H0` is the
  accepted baseline surface; `S` and `D` are incremental common and
  length-differential surfaces. No coefficient is released to production; the
  bank is frozen only in the dedicated validation configuration.
- The deterministic offline dense audit passes over B `-100..+100`, a complete
  C cycle, and the hard `100..430 mm` interval. At those endpoints,
  incremental maxima are `0.667969 / 0.500650 mm`, length-bank maxima are
  `0.245711 / 0.380875 mm`, and total empirical maxima are
  `1.112224 / 1.298708 mm`. The recently used `425.022 mm` length is also
  explicitly checked at `0.492394 / 0.371423 / 1.294172 mm`. These pass the
  separate `0.700 / 0.400 / 1.350 mm` limits, with exact zero at B0/C0.
- Numerical boundedness is not full-range accuracy evidence. T3 and T4 identify
  only one linear slope. Release across the full table requires an untouched
  physical endpoint validation near `425-430 mm`. T4 is the longest available
  touch probe, so the longer endpoint is deferred to a dial-gauge test; a second
  endpoint near `100-115 mm` is preferable. Until then, only the T3-to-T4
  bracket is eligible for accuracy acceptance.
- The opt-in kinematics implementation now enforces one active-offset snapshot
  per forward/inverse call, exact reference/span and maximum cap ceilings, the
  hard domain/tolerance ceiling, a matching coefficient-set ID, finite complete
  transforms, and live correction norms. Interpreter and remap guards reject
  tool/offset changes while TCPC is active and retain their kinematics fallback
  if the userspace state component disappears. A promoted INI must specify
  `lengthmodel=1 lengthmodelid=2026082601` and
  `[TCPC] LENGTH_MODEL_REQUIRED=1`. Its matching overlay is startup-only and
  must never be sourced or reloaded into a running LinuxCNC session. Each
  coefficient revision requires a new model ID and a clean restart.
- Production and legacy capture INIs do not enable this model. Promotion is
  limited to the dedicated validation-only
  `5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`,
  which loads `tcpc_length_aware_candidate_2026082601.hal` last. All seven
  top-level TCPC INIs resolve to the audited canonical table and define no
  `TOOL_DATABASE` override. This is a physical-validation candidate, not a
  production coefficient release or full-range accuracy acceptance.
- The first physical gate is frozen as campaign/mode/attempt
  `2026082602 / 32 / 1`. The dedicated T4 runner is
  `tcpc_length_aware_t4_validation_2026082601.ngc`, SHA-256
  `0c25bad2be98eae5e927c765fea83d1b877e652635f446ff637dbf8160e308be`.
  It has one initial M0, no intermediate holds, no 20-second dwell, the proven
  101-pose/28-closure T4 path, and the latest bounded false-pulse transaction
  layer. A clean run requires exactly `101/101/101` result/state/model-state
  rows, `28` closures, and `808/808` contact/gap traces. Attempt 1 outputs are
  currently exact header-only files.
- The offline T4 validator and preflight pass. Validator
  `validate_tcpc_length_aware_t4.py` SHA-256 is
  `6ebbd6ba910f9700e481b47c4bef89ad31039b286cbca5f659134ea7d616c7fb`;
  generated `TCPC_LENGTH_AWARE_T4_VALIDATION_PREFLIGHT_REPORT.md` SHA-256 is
  `aca382142a2fac0539e0fd69be144ed87040479183f186086bddb929da1bd0a3`.
  Its self-test, full-domain audit, header contract, runner static checks, and
  isolated standalone rs274 preview all pass. The exact operator order is
  `TCPC_LENGTH_AWARE_T4_VALIDATION_PLAN.md`, SHA-256
  `c1212e77b3864a752555d37b73fcc322350b9a8e29992f135f07bba5fe8d6b20`.
- At this checkpoint every exact LinuxCNC, LinuxCNC server, milltask, RTAPI,
  and Probe Basic process is stopped and `/tmp/linuxcnc.lock` is absent. Do not
  infer machine position from any historical section below. The operator must
  clean-launch the dedicated validation INI, home, establish T4/H4/G43/G43.4,
  and place T4 3-5 mm above the current secured sphere at B0 C0.
- At `18:03:06 +07`, the diagnostic wrapper recorded live `milltask` PID 524892
  ending with status 137 / signal 9 (`probable_sigkill`), with no core. QtPyVCP
  then reported `unrecognized error -1` and `Error buffer invalid` at
  `18:03:33`; the same notification-timer traceback recurred during UI shutdown
  at `21:05:52`. The error-channel traceback was secondary to task loss, not a
  probe or calibration fault. The SIGKILL source is not proven, but its timing
  is consistent with the earlier concurrent headless-test collision. The live
  controller state after task loss was not trustworthy.
- After every real LinuxCNC/Probe Basic process was confirmed stopped, the
  current compiled headless suite passed `1/1` at about `21:08 +07`. It now
  includes nonzero-B/C forward/inverse TCPC round trips at `99.998`, `411.810`,
  `425.022`, and `430.002 mm`, as well as runtime equivalence, entry guards, and
  fault-cap checks. `test.sh` now fails closed on an existing LinuxCNC lock, a
  live LinuxCNC/server/milltask/RTAPI/Probe Basic process, or a process-
  inspection failure, then rechecks the lock immediately before launch. Never
  bypass that guard; production/headless exclusion is still an operator-
  controlled protocol rather than a shared atomic launcher lock.
- Exact plan and audit are `TCPC_LENGTH_AWARE_MODEL_PLAN.md` and
  `assess_tcpc_length_aware_bounds.py`. Their current SHA-256 values are
  `b8306e4612dff6ad52914ea0cd146bff39a093643f96a766836d82337ddc826e` and
  `b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2`.
  The auditor and T4 validator import neither LinuxCNC nor HAL. No machine or
  live configuration action was taken for this handoff.

## Current Handoff - T3 Transfer Complete, 2026-08-26 16:33 +07

- LinuxCNC remains running in the baseline T3 task-capture configuration. A
  passive status read found it enabled, Auto idle, unpaused, in position,
  queue zero, all XYZBC joints homed, spindle off, and probe clear. T3/H3 is
  active with Z tool offset `128.606729 mm`. Commanded position is
  approximately `X1024.928164 Y844.033499 Z-380.402535 B0 C0`; actual B/C are
  within `0.000024 deg` of zero. The completed Attempt-5 recovery file remains
  selected at its end. This is a state record, not authority for motion.
- The requested T3 transfer grid is complete. Direct source ownership is A1
  sequences 1-14, A2 15-22, A4 sequence 23, and A5 sequences 24-31. A5 itself
  completed `8/8/1` result/state/closure rows and `64/64` contact/gap traces.
  Every commanded touch was exact raw/mux/gated `1/1/1`, with no repeat or gap
  activity and no rejected pose. Its B0 closure is `0.008580 mm`.
- The complete A5 archive is
  `calibration_runs/20260826_1612_campaign2026082601_t3_exploratory_attempt5_complete`.
  `MANIFEST.md` SHA-256 is
  `d93982d4c47798d9f841c8ac4840635fb4ea73d5d231a50e593eeecda552aaa6`;
  `SHA256SUMS` SHA-256 is
  `ef9e1c3957a9c2c30011d2f8c127737df53ab5a10b3f70bc1bab82b28c2ff03b`.
- The frozen four-source analyzer passes its acquisition contract. Its report
  is
  `TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_ATTEMPT5_FOUR_SOURCE_REPORT.md`,
  SHA-256
  `0a7176f6fcb3edc00c4dc461fe3b39c3d750c499f8f907400d3a2b0ce3095a07`.
- R2 is not accepted. It improves T3 equal-20 RMS/max from
  `0.251155 / 0.617559` to `0.148716 / 0.328314 mm`, but fails the
  `0.120 / 0.280 mm` ceiling; raw-31 is `0.149044 / 0.352450 mm`. The maximum
  pose worsening is `+0.119219 mm` at B+90/C0 against the `0.075 mm` limit.
  B+90/C180 controls the remaining maximum-error ceilings. These points are
  internally clean and must not be removed.
- No live coefficient, B/C zero, geometry, tool table, probe scalar, INI, or
  production HAL change is authorized. The next stage is offline R3
  feasibility under
  `TCPC_T3_R2_TRANSFER_CLOSEOUT_AND_R3_PLAN.md`. No operator action is required
  until a candidate and exact verification package are frozen.
- The deterministic offline feasibility assessment is complete and reports
  `NO R3 COEFFICIENTS RELEASED`. Generator
  `assess_tcpc_r3_feasibility.py` SHA-256 is
  `4520081bb7e7b4088a555e498ad7e6430dd3f5fc2d3d93a8a1e4c9867eaa6dd1`;
  generated `TCPC_R3_FEASIBILITY_REPORT.md` SHA-256 is
  `5b5b747e7c3f5ef0df9a0c5e41a5518e0a6f281a79917df5388c1d015d29bee2`.
  Its self-test and byte-for-byte report reproduction pass. Stable7 fails the
  T3 ceilings, and the fixed ten-term compromise remains outside raw-31 limits
  with a threshold-sensitive equal-20 result. No candidate INI, overlay, or
  runner is authorized or prepared from that illustration.

The older campaign-04 handoff below remains immutable provenance. Where it
describes R2 verification or T3 as a future action, this handoff supersedes its
operator order.

Current continuation: measurement campaign `2026082404` is authoritative. See
`TCPC_RELOCATED_SPHERE_CAMPAIGN_2026082404.md`. It inherits the accepted
campaign-03 anchor without relabeling or rerunning it. Historical live states
and campaign orders below are provenance only and do not authorize motion.

## Current Handoff - Campaign 2026082404

### Immediate State - 2026-08-26

- LinuxCNC was cleanly closed by the operator after the completed Attempt-5
  capture. Recovery-A3 milltask PID `499194` and all LinuxCNC/HAL processes
  are gone. Its final passive state was enabled, Auto idle, unpaused, in
  position, and all five joints homed at approximately
  `X1025.066409 Y844.123930 Z-279.663852 B0 C0`, clear above the sphere, with
  T4/H4 `229.407000 mm`, TCPC, and R2 active, TWP clear, spindle off, and probe
  inputs clear. This is historical end-state evidence, not a restart target.
- Attempt 5 completed normally at `2026-08-26T02:41:32+07:00`. It accepted
  exact sequences `1-9,72,93-101`: `19 / 19` result/state rows, 14 passing
  source-local closures, and `152 / 152` contact/gap traces. All 152 G38 moves
  touched successfully. Every burst, consistency, release, and terminal-fault
  flag is zero. Final raw/mux/gated counters are `160 / 160 / 152`: the eight
  excess raw/mux edges are eight individually recorded post-contact repeats,
  each blocked from the gated probe input.
- The worst Attempt-5 closure is block 913 (`sequence 3 -> 95`) at
  `0.019998 mm` against the frozen `0.050000 mm` limit. Correction norm is
  `0.000759-0.021022 mm`, pass-center delta is
  `0.000863-0.022766 mm`, and corrected diameter is
  `30.130500-30.336342 mm`. Three independent structured read-only audits find
  no schema, order, state, geometry, closure, or counter discrepancy.
- The immutable raw acquisition is sealed at
  `calibration_runs/20260826_0244_campaign04_t4_candidate_r2_attempt5_complete_raw`.
  Its `SHA256SUMS` SHA-256 is
  `2fbbc4021d51ef7afd5fbdddcf21a1171762f2b0baec915f7c63843ff775a90d`;
  all 20 covered members verify. The five result hashes are recorded in its
  manifest and remain identical to the live files.
- The sealed copied-workspace analyzer exited `0` with
  `RECOVERY CONTRACT PASS` and generated the explicitly diagnostic four-source
  composite. Its immutable archive is
  `calibration_runs/20260826_0902_campaign04_t4_candidate_r2_attempt5_complete_analysis`;
  the `SHA256SUMS` SHA-256 is
  `3b155b67b718509d3228c1c2517ccfd7a4ca4a4d12ba98b9105d311c27de966c`,
  with all 139 covered members verified. Composite equal-76 centered RMS/max
  are `0.089045 / 0.190827 mm`; raw-101 centered RMS/max are
  `0.090001 / 0.194441 mm`; actual-versus-frozen-prediction pattern RMS/max are
  `0.030038 / 0.068496 mm`. The generated active composite report SHA-256 is
  `f5fb2aa38360e1d6be484290b17e2b7c6692c345c297df3f9c5c12ce9f2ee1ef`;
  the independent gate-audit SHA-256 is
  `823918d9fb6751ed99fb31b37b146694a5eef64ffa8e8f916549b8742b636d05`.
- The analyzer's recovery pass is not R2 acceptance. Reconstructed diagnostic
  values pass 11 of the 12 frozen statistical gates, but the maximum
  unique-pose worsening is `0.090202 mm` against the `0.075000 mm` limit at
  `B+90 C180` (sequence 85 from Attempt 4). Its baseline/composite centered
  norms are `0.076479 / 0.166681 mm`. Attempt 4's local B+90 closure
  (`0.009112 mm`) and sequence-85 pass repeat (`0.001930 mm`) are clean, so do
  not discard this as a bad touch. The multi-source translations also prevent
  any whole-grid gate from being called a formal uninterrupted-run result.
- Attempt 4 is an immutable valid partial. It accepted exact sequences
  `1-9,67-96` (`39 / 44` result/state rows), 12 passing closures, 318 contact
  traces, and 318 gap traces. At sequence 97 (`B0/C180`), pass 2 contact 2
  traversed the full probe vector with no gated touch after six successful
  contacts. No sequence-97 result or state row exists. The partial is sealed
  at
  `calibration_runs/20260826_0100_campaign04_t4_candidate_r2_attempt4_partial_no_touch_seq97`;
  its `SHA256SUMS` SHA-256 is
  `7bcc0bd32c995f9f9805eb77594dbe18421bc979e8d90964be2b66ca9b576ee6`.
- Attempt 4 must not be resumed, appended, truncated, or repaired in place.
  Attempt 5 now supplies the complete independently acquired B0 ownership
  required by the four-source diagnostic composite; it does not convert that
  composite into a formal same-acquisition 101-row pass.
- Current attempt-5 identities are runner
  `779f18f20d70ada82bea0f06caf91f5111dfa746ea4ae2a5bab3da55abf0e6b6`,
  analyzer
  `e41ceaf962d2639ecc00872223de0e42d91e294c960c1d4b5552a4146e44a6c0`,
  and preflight report
  `2f346bf4271d19aff3f9c4aae5a74f68ac427026934921e13fe288336a4496b2`.
  The replacement package is sealed at
  `calibration_runs/20260826_0133_c04_r2_a5_restart_safe_preflight`; its
  `SHA256SUMS` SHA-256 is
  `fa72869d8f85ca6ee7affdb1e299238d618fe79c59dc394838f807ca31ea4563`.
  All 130 archive checksums and both active/archive self-tests and preflights
  pass. The earlier `20260826_0119` package is immutable but superseded before
  motion and must not be loaded.
- The three prior milltask SIGBUS exits are causally linked to standalone
  repository `bin/rs274` previews running under the controller's `HOME`.
  Standalone RS274 unconditionally opens `$HOME/.tool.mmap` with `O_TRUNC`
  before parsing `-g` or `-T`; live milltask then faults in
  `tool_mmap_mutex_get()` at mapping offset zero. See
  `diagnostics/SIGBUS_RS274_TOOL_MMAP_CAUSE_20260826.md`. The current attempt-5
  analyzer supplies a private temporary `HOME` to every RS274 subprocess.
- R2 remains diagnostic and is not accepted or released. Do not refit it from
  this validation composite and do not edit production/base geometry, zeros,
  tool data, INI, or HAL. This result does not authorize the formal predeclared
  T3 verification stage. If the operator elects to continue the tool-length
  diagnosis, prepare a separately declared exploratory T3 holdout acquisition
  under a clean restart of the baseline task-capture INI after verifying base
  HAL SHA-256
  `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`
  and confirming that the R2 overlay is absent. Freeze the T3 scoring method
  before motion; T3 cannot cure the failed T4 gate or relabel the composite as
  a formal pass.

- T4 primary mode 23 attempt 1 completed all 101 result rows, 101 state rows,
  and 28 closures. Strict validation and an independent reconstructed-contract
  audit pass. The immutable result/state/closure hashes are respectively
  `70e346c0...d9468`, `dd09051f...a73693d`, and `f0fd62d8...c3021`.
- Current-calibration centered RMS/max are `0.201016 / 0.711434 mm`. Worst is
  sequence 91 at `B-90 C270`; the repeated high-B/C270 pattern has local
  closures of only approximately `0.003-0.006 mm`, so it is calibration or
  mechanical pose signal rather than a bad touch.
- All 28 closures pass; worst is `0.027115 mm` and whole-run closure is
  `0.023988 mm`. Every accepted contact, travel, diameter, pose, tool/TLO,
  TCPC, SSI, and state gate passes. No T4 row is rejected.
- The exact completed run and passive final state are archived under
  `calibration_runs/20260825_0756_campaign04_t4_primary_attempt1_complete`.
  At that capture LinuxCNC was idle/in-position at approximately
  `X1025.007919 Y844.055749 Z-279.656567 B0 C0`, T4/H4 `229.407000 mm`, with
  the original baseline correction active and all probe inputs clear.
- A first nine-term lambda-30 fit was frozen and archived, then rejected during
  final statistical review before any load or motion. Its fixed-family
  validation understated term-selection uncertainty, and lambda 10/3
  outperformed lambda 30 after the family was fixed. Exact R1 preparation is
  preserved under
  `calibration_runs/20260825_0833_campaign04_t4_candidate_r1_rejected_pre_motion`.
- Active R1 artifacts are disarmed: its overlay contains no executable `setp`
  command, its runner aborts before any setup output or motion, and its
  preflight hash guard refuses the altered files. Do not load or run R1.
- R2 is frozen as one ten-term, lambda-10 candidate selected from 76
  equal-weight unique T4 poses without reading T3. Predicted centered RMS/max
  are `0.085763 / 0.204948 mm` on equal-76 and `0.087176 / 0.207789 mm` on
  raw-101. The fit and audit checkpoint is archived under
  `calibration_runs/20260825_0909_campaign04_t4_fit_r2_frozen`.
- R2 mode-26 attempt 1 ran under the isolated candidate configuration and
  accepted synchronized sequences `1-93`. Closure 911 then compared sequence
  1 with closing `B0/C0` sequence 93 and measured
  `+0.035156 / +0.033230 / +0.014069 mm`, norm `0.050380 mm`. This exceeded
  the frozen `0.050000 mm` closure limit by `0.000380 mm`; the guard correctly
  aborted before sequences `94-101`. Attempt 1 is formally incomplete and
  must not be resumed, appended, truncated, relabelled, or called a pass.
- The immutable attempt-1 counts are `93 / 93 / 17` result/state/closure rows.
  All result/state rows pass their exact contracts; the first 16 closures pass
  and closure 911 correctly records failure. The raw acquisition is sealed at
  `calibration_runs/20260825_1412_campaign04_t4_candidate_r2_attempt1_partial_closure_stop`;
  its `SHA256SUMS` SHA-256 is
  `2026776b2b3a1b7b98fc74af2881fe99b2498ddbb7aa0899f8033977ef8156a0`.
- Attempt 1 contains all 76 unique T4 poses and strongly supports the R2 sign
  and scale without satisfying final acceptance. Provisional equal-76 RMS/max
  are `0.086446 / 0.221643 mm`; positive/negative high-B RMS are
  `0.087004 / 0.103197 mm`; raw-93 prediction-pattern RMS/max are
  `0.024691 / 0.055345 mm`. Contact sensitivity around sequences 85 and 82
  does not change that conclusion. Exact disposition is in
  `TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2_ATTEMPT1_PARTIAL_REPORT.md`.
- A fresh full attempt-2 package retains the exact overlay, 101-pose motion,
  guards, `0.050 mm` closure limit, and statistical gates. Its runner differs
  from attempt 1 only in `#727=2` and the fresh output paths. Active and sealed
  analyzer self-tests, `rs274` parse, reachability, correction, negative tests,
  and full preflights pass. The sealed package is
  `calibration_runs/20260825_1425_campaign04_t4_candidate_r2_attempt2_final_preflight`;
  its `SHA256SUMS` SHA-256 is
  `dc2c0415d128a3710bb5b0f5ec0b37880908ec35a154450cd6c901941a4f6e27`.
- R2 mode-26 attempt 2 subsequently accepted synchronized sequences `1-48`
  and six passing closures. During the next intended pose, sequence 49 at
  `B-15/C225`, contact 2's U-side `G38.3` move returned `#5070=0`. The runner
  retracted, returned to top clear, disabled its probe outputs, and aborted
  with `Four-contact safe U touch did not record point data`. No sequence-49
  result or state row was written. Attempt 2 is formally incomplete and must
  not be resumed, appended, relabelled, or reused.
- The immutable attempt-2 counts are `48 / 48 / 6` result/state/closure rows.
  All six logged closures pass; their norms span `0.002647-0.015379 mm`
  against the frozen `0.050000 mm` limit. The partial acquisition and exact
  passive end state are sealed at
  `calibration_runs/20260825_1654_campaign04_t4_candidate_r2_attempt2_partial_no_touch_seq49`;
  its `SHA256SUMS` SHA-256 is
  `5a8e2562c3ad85601cd701207aba87e061c2eb9ce4e767f6519b314748a07895`.
- The owner/operator subsequently reviewed CCTV and confirmed that T4 showed
  an error state with continual visible pulsing around `16:14`, during the
  sequence-49 failure interval. The active HAL masked raw post-G38 activity for
  `10.0 s`, retained any later abnormal event for only `0.50 s`, and had no
  persistent edge counter or raw-pin trace. The program therefore surfaced
  only the downstream U no-touch error. Attempt 2 is classified as
  probe-fault contaminated, not as evidence of a TCPC reach failure.
- The volatile controller, QtPyVCP, and health logs are sealed separately at
  `calibration_runs/20260825_1716_campaign04_attempt2_probe_fault_trace`;
  its `SHA256SUMS` SHA-256 is
  `cf141d46a543dc3558d051633501d6b061b49083641517235eec2179ff81eed8`.
  They prove command serial `94` remained unchanged from the initial M0 Resume
  through the automatic abort; no later operator controller command is logged.
- Critical identities are: base task-capture INI
  `afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519`,
  base HAL
  `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`,
  candidate INI
  `1ab3b84611b93fbf10083e21f87b90d19eea5c3c8a8fe66373570a7cace3d77e`,
  R2 overlay
  `0bfefdb068bb353282fc41067d5cd7464f76ea6a4f520204f0ab5c914ee1673a`,
  attempt-2 runner
  `6421c2f8cb8c12a7e4d8ace98f956e4270974482058815609cce9b5f22dbea86`,
  and attempt-2 analyzer
  `0774fc7d75e49fee26ad990c74b11cc6cd0267ecfc15019ae4cc7e117736afe2`.
  The attempt-2 output hashes are results
  `8c3ee95280b068be4322f526ced03836c7e371a0b12db444a5ee31eb8ae123c4`,
  state
  `66d7d5e1d8568e2b4f50ce2218d435a537f79f6ae8c951cd49dad1635df11b8d`,
  and closures
  `47e4b96fa7fb5f7b69aa1d0d7c03796d0835bd67a31052cdacb55ba3a6909e08`.
- The exact runner is bounded to `B+/-90`: dense candidate correction peaks at
  `0.671900 mm` and passes the `0.750 mm` diagnostic cap. The configured
  `B+/-100` scan reaches `0.764644 mm` near `B-100/C272.6561`; this is an
  explicit production-release blocker. While the candidate overlay is active,
  allow only operator startup/homing/state establishment, the operator's sole
  setup move to the exact B0/C0 sphere-top start, and the exact runner. No
  other manual, MDI, or jog motion is permitted.
- T3 remains untouched and must never run under the candidate INI. Immediately
  after the T4 diagnostic, clean-close the candidate, restart the baseline
  task-capture INI, verify the base HAL hash above and absence of the overlay,
  then perform any T3 transfer check.
- At `2026-08-25T16:56:14+07:00`, the isolated R2 candidate INI remained live
  with task PID `426717` and start ticks `34306115` unchanged. The exact
  attempt-2 runner was idle after its controlled no-touch abort at line `657`.
  Interpreter idle, execution done, not paused, in position, velocity zero,
  all five axes homed, machine enabled, and T4/H4 `229.407000 mm`. Commanded
  position was approximately
  `X1029.270816 Y848.271154 Z-280.401003 B-15 C225`; probe input was clear and
  the spindle was off. The operator later returned the machine to the standard
  B0/C0 sphere-top start. At `2026-08-25T17:13+07:00`, passive inspection found
  it idle/in-position at approximately
  `X1024.747449 Y844.756916 Z-281.365857 B0 C0`, T4/H4 unchanged and about
  `3.25 mm` above the latest reconstructed sphere top. The retired attempt-2
  file remained selected. These are recorded states, not motion or restart
  authority.
- At `2026-08-25T17:34:18+07:00`, after the operator had returned the machine
  to that standard B0/C0 start, the prior R2 session's `milltask` terminated
  with `SIGBUS`. Its milltask log, health trace, and core were captured under
  `diagnostics/task_exit_captures`. This records the failure symptom and does
  not establish a root cause. That controller session is retired.
- Attempt 2 remains immutable and retired. It must not be interpreter-resumed,
  rerun, appended, truncated, relabelled, or used as a machine-run namespace.
- Attempt 3 is frozen as a fresh mode-27 recovery acquisition, not an
  interpreter continuation and not a formal uninterrupted 101-row pass. It
  acquires original sequences `1-9` and `45-101` only: `66` accepted rows and
  `23` closures. The opening B0 block supplies within-acquisition references;
  the sequence namespace is then seeded to 44, the complete B-15 block is
  rerun, and the exact remaining B+/-30, B+/-45, midpoint B0, B+/-60,
  B+/-90, and closing B0 blocks follow. Sequences `10-44` are deliberately
  omitted. An analyzer-only composite may read those immutable attempt-2 rows
  with a separate nuisance translation, but it is diagnostic only and can
  never be reported as a formal same-run pass.
- Attempt-3 motion, feeds, probe vectors, release sampling, and protected
  guards remain matched to attempt 2. It has one initial pre-motion `M0`, no
  intermediate holds, and no 10 or 20 second settle dwell. Observation-only
  raw-receiver, mux, and gated-input edge counters plus per-G38 contact and
  inter-contact-gap traces retain the probe evidence. The bounded logic accepts
  at most two true post-contact repeat edges; excess repeats, any gated edge in
  a gap, raw/mux inconsistency, an invalid successful-contact gated count, or
  initial post-M0 activity logs and aborts through the protected retract path.
- Frozen attempt-3 identities are runner
  `1e1dee457a6b9792585f2afe4abb2f99b09951e20bdfe2f174b863896b77579d`,
  analyzer
  `0508f819ddb26000194c4c336b6a162212d8ffbdf3439a95b34933baa0cfa15f`,
  recovery INI
  `66d2b123e2df19eab2a0c1f53875e699c666b32e3a19800ac9427d8eafbabd3b`,
  counter HAL
  `6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34`,
  edge monitor
  `83531e3dcbb26b516a60fe9a89f32aaf0cf85180e5fd33b88ec7b3664b629aea`,
  and monitor wrapper
  `0793ddfed545562ffeffe50dbe91b4a0a74ec45e6d0e16153f344288994db49c`.
  The final post-review package is sealed at
  `calibration_runs/20260825_1743_c04_r2_a3_recovery_preflight`; its
  `SHA256SUMS` SHA-256 is
  `698f4768e0422cfa8b2b72a6eaa6496f0c8a9410737d3083816e59b6a647ef24`.
- The clean recovery-A3 INI was launched at
  `2026-08-25T17:58:54+07:00`. The exact frozen runner was loaded at line 0
  with zero motion, after which the operator completed setup and started the
  recovery. Attempt 3 is now an immutable valid partial: `34 / 66` accepted
  rows at exact sequences `1-9,45-69`, five passing closures, `273` contact
  traces, and `274` gap traces. Worst closure was `0.020390 mm`; standalone
  centered RMS / maximum residual was `0.076430 / 0.141219 mm`.
- At sequence 70 (`B-45/C270`), contact 1 completed and retracted. At the clear
  contact-2 U-side start, before its G38, two further raw/mux edges combined
  with the prior permitted repeat to produce a terminal extra-edge count of
  three. The runner logged the gap and auto-aborted with
  `Electrical retrigger burst exceeded two repeats across inter-contact gap`.
  It was stationary and in position at approximately
  `X1025.285920 Y828.615696 Z-286.989540 B-45 C270`, with inputs clear. No
  sequence-70 result/state row exists.
- Attempt 3 must not be interpreter-resumed, rerun, appended, truncated,
  imputed, or relabelled, and it is not a formal same-acquisition candidate
  pass. Its sealed partial archive is
  `calibration_runs/20260825_2249_campaign04_t4_candidate_r2_attempt3_partial_gap_burst_seq70`;
  the archive `SHA256SUMS` SHA-256 is
  `d77d728bccc11c36cd97ccbd7ae28fb6832aa5b2695cd3244e527e0b9bde3072`.
- After the operator returned the machine to the exact standard B0/C0
  sphere-top start, recovery-A3 `milltask` PID `459090` terminated with
  `SIGBUS` at `2026-08-25T23:04:57+07:00`. Passive evidence shows the retired
  attempt-3 runner was still selected; attempt 4 had not been opened in that
  controller session. The temporal proximity to preparation of a new runner
  is not a root-cause determination. The captured core SHA-256 is
  `bab1380c1e5fb8c86705ce25562be17b9a1671f3126aa31302ab1b5526d99f61`.
- A clean recovery-A3 controller launched at
  `2026-08-25T23:09:13+07:00`; new `milltask` PID `471211` started one second
  later. It opened only Probe Basic's `blank.ngc`, with fresh raw/mux/gated
  counters `0/0/0`. The operator owns the new Home All, T4/H4 plus TCPC state
  restoration, probe reset/qualification, and return to the B0/C0 top start.
- Attempt 4 is frozen as a fresh mode-28 acquisition, not an
  interpreter resume. Its exact source ownership is sequences `1-9,67-101`
  (`44` rows): a fresh B0 reference, the complete B-45 block, midpoint B0,
  B+/-60, B+/-90, and closing B0. It contains `19` source-local closures, one
  initial pre-motion `M0`, no intermediate holds, and the unchanged attempt-3
  contact/gap counter guards. The runner SHA-256 is
  `f4dd59e60219e3c0a5d83f3f76fbcb451871a9996d186adae6d2fdd6fd480364`;
  analyzer SHA-256 is
  `61c6ed90e6773fbd348ac07a1310ca0b6c729c8678f7e057f89b4634b6e5bb7d`;
  and preflight-report SHA-256 is
  `29d74db8a52efab260f63808e199dab3a2b076e5edd79267db2f46cc8b264b26`.
  The immutable package is
  `calibration_runs/20260825_2312_c04_r2_a4_recovery_preflight`; its
  `SHA256SUMS` SHA-256 is
  `0459c30465ee93d23d7d1d28fc2dfb722c8de0bd73e82c068a02489bcaa9c3f7`.
  Active and archived self-tests, preflights, prior-partial validation, exact
  28-closure ownership, and all 96 archive checksums pass. The runner is ready
  for load-only verification after the operator completes live setup and probe
  qualification.
- At `2026-08-25T23:34:01+07:00`, the remote operator reported that a manual
  probe deflection was not physically available. The two-deflection positive
  receiver qualification is waived for this attempt only. Raw/mux/gated
  counters remained `0/0/0` throughout homing, T4/H4 and TCPC restoration,
  repositioning, and the subsequent stationary interval; all input levels were
  clear. This proves absence of spontaneous edges but does not prove that the
  receiver can generate a contact edge. The runner's initial post-M0 edge
  baseline and first-G38 no-touch handling remain mandatory and fail closed.
- At `2026-08-25T23:35:10+07:00`, the exact frozen attempt-4 runner was opened
  load-only. `wait_complete` returned success; task PID `471211` and its start
  time were unchanged; current/motion lines remained zero; commanded and
  actual XYZBC deltas were exactly zero; no controller error was returned; and
  all five outputs remained exact header-only files. T4/H4, TCPC, clear probe
  state, and `0/0/0` counters remained unchanged. The program is selected but
  has not been started. Cycle Start may advance only to its single initial M0;
  Cycle Start and Resume remain operator actions.
- At `2026-08-25T23:36:38+07:00`, operator Cycle Start reached the single
  initial M0 without motion or error. Passive verification found AUTO paused,
  zero velocity, the unchanged standard start, all five axes homed, T4/H4
  `229.407000 mm`, TCPC enabled, TWP inactive, the R2 correction enabled,
  spindle and all probe signals clear, counters `0/0/0`, task PID `471211`
  unchanged, and all five outputs still header-only. The operator is clear to
  Resume; the first post-M0 transaction establishes the sticky counter
  baseline before any probe move.
- No TCPC coefficient, B/C zero, rigid geometry, production/base INI or HAL,
  tool table, or kinematic setting has changed.

## Historical Handoff - Campaign 2026082403

- The relocated certified 30 mm sphere T4 anchor completed and is accepted.
  Center is `X1024.957789 Y844.074417 Z-302.468115`; center correction was
  `0.008821 mm` and pass-to-pass center delta was `0.019449 mm`. Do not rerun
  the anchor.
- Combined configured-limit replay passed all 29,349 T4/T3 samples with
  `182.860993 mm` worst remaining linear margin after allowances. Frozen T4
  59-pose and T3 31-pose probing runners remain unchanged.
- Generated T4/T3 no-contact runner hashes are respectively
  `f4ec525156b6692c6b6f5c1ffd13c58104cb21371e588ee3b65ca654302ce22d`
  and `0fe18a880bea26fd7f977ea44e59bd1e7f71fa4604acbda7e6a5410df04ddb08`.
  Every positive-B pose has a corresponding negative-B pose at the same C
  angle and multiplicity. Each envelope retains one initial pre-motion `M0`;
  all intermediate B-block holds were removed for the shared clearance profile.
- A load-only request for the T4 envelope returned `-1`/timed out with the
  selected anchor file and XYZBC position unchanged; no motion occurred.
  `milltask` PID `353251` was then found absent while the remaining controller
  processes exposed stale idle status. Do not load, start, or resume in that
  session.
- Accepted final top-clear endpoint was approximately
  `X1024.957785 Y844.074417 Z-279.622857 B-0.000010 C+0.000320`, with T4/H4
  `229.407000 mm`; these are archived observations, not motion authority.
- The next physical stage remains the operator-observed T4 no-contact
  envelope after a clean, instrumented LinuxCNC restart, homing, T4/H4/TCPC
  revalidation, and return to the accepted start envelope. The exact
  termination point remains unknown. In the best-bounded incident, direct
  inspection found PID `314951` alive at `18:13:46` and absent at `18:27:57`,
  before the failed file-open request at `18:32:18`; `kill 344915` at `18:26`
  targeted a separate hung offline analyzer. The later open detected that
  existing loss. Deferred close/reset remains a controlled hypothesis only.
- Valid anchor provenance is in
  `calibration_runs/20260824_1900_relocated_sphere_anchor_attempt1_complete`;
  the subsequent controller incident is in
  `calibration_runs/20260824_1917_post_anchor_task_lost`.
- The disabled close/open diagnostic passed on attempt 2. File A opened at
  `20:06:49`, the same task survived a greater-than-20-minute idle soak with
  continuous polling, and file B opened at `20:27:30`. Both returned
  `RCS_DONE`; commanded/actual XYZBC deltas were zero and neither file ran.
- A separate attempt-1 Probe Basic `SIGBUS` caused normal launcher cleanup to
  kill a healthy task; it was not a reproduced milltask failure and does not
  explain the earlier milltask-only incidents.
- At the `2026-08-24T20:50:46+07:00` load-only handoff, the diagnostic INI was
  running, all five axes were homed, machine was enabled, and T4/H4
  `229.407000 mm` with TCPC active and TWP clear. The revised T4 no-contact
  envelope was selected at line 0 and had not been started. Commanded position
  was approximately `X1024.747449 Y844.756916 Z-281.365857 B0 C0`, only
  `1.883639 mm` from the accepted top-clear endpoint. The same task PID/start
  time survived the reload and XYZBC did not change. This observation is not
  motion authority; the operator owns Cycle Start and Resume. No TCPC
  coefficient, production INI, production HAL, tool table, or kinematic setting
  changed during diagnostics or envelope revision.

Initial capture: `2026-08-21T21:53:08+07:00`

Historical final handoff: `2026-08-21T22:03:43+07:00`

Current recorded live checkpoint: `2026-08-23T00:01:05+07:00`

This file preserves the 2026-08-21 pre-campaign state and records the current
campaign handoff below. The authoritative current procedure is
`TCPC_POSITIVE_B_C45_BASELINE_PLAN.md`. Runtime observations must be
revalidated after any machine enable, LinuxCNC restart, power cycle, tool
change, or physical movement.

## Current Handoff - Campaign 2026082202

- The owner redirected work to a separate T3-short then T4-long baseline on the
  fixed certified 30 mm sphere at B `0/+5/+15/+30 deg` and safe C45 sectors.
- The 45-degree post runs base-to-sphere in `X+,Y-,Z+`. At nonzero B the new
  runners never descend to or probe C135/C315. Canonical slots
  `13,17,22,26,31,35` remain explicit unsafe gaps; no row is imputed.
- Campaign `2026082201` mode-17 attempt 1 remains an excluded `13/20` partial.
  Prepared attempt 2 was superseded with unchanged XYZBC and CSV, no axis/probe
  motion, and no measurement row. Its exact file is preserved, attempt ID 2 is
  retired, and any future mode-17 restart must use attempt 3. The active legacy
  runner is disarmed.
- After attempt 5, `milltask` and `halui` were found absent while the GUI and
  realtime processes remained. LinuxCNC was fully shut down and cleanly
  relaunched; the complete server/IO/HALUI/realtime/milltask/Probe Basic
  process set is now present. The operator completed Home All.
- Attempt 6 was executed twice under the same selector while T3 showed its
  known bad electrical state, including severe repeated trips and faint LED
  glow. Operator-controlled pauses/resumes were used, but the resulting partial
  acquisition is not trustworthy.
- The second execution completed only B0/C0 pass 1. Its center was displaced
  `0.709062 mm` from the mean of four prior accepted B0/C0 centers. Pass 2 did
  not complete, no summary row was written, and Attempt 6 is excluded zero-row.
- The operator stopped, returned X/Y/B/C to zero, and retracted Z exactly
  100 mm clear. Four samples were interpreter-idle, queue zero, in position,
  and zero velocity at commanded machine XYZ
  `1024.747449/444.756916/-282.166128 mm`, B/C `0/0 deg`.
- `blank.ngc` is loaded. T3/H3 `128.606729 mm` remains the software selection;
  TCPC and the persistent correction remain active, and TWP is clear. LinuxCNC
  still reported enabled at the last sample. Apply E-stop/disable before
  physically removing T3, and do not enable or move while it is absent.
- Spindle and probe inputs were clear at the last preflight. Feed and rapid
  overrides were `100%` and `4%`; these are recorded state, not motion authority.
- The live tool number and all three Z TLO sources are correct for T3, but
  `halui.tool.diameter` currently reports stale `0.201` metadata. The exact
  campaign runners therefore freeze the physically known and tool-specific
  `6.000 mm` ball diameter as an immutable constant; they do not reload or rely
  on that stale controller field.
- T3 attempts 1-2 are retired zero-row starts. Attempt 3 accepted canonical
  sequences 1-10, attempt 4 accepted sequences 1-3, and attempt 5 accepted
  sequences 1-2. Those partials and zero-row Attempt 6 are excluded and cannot
  be resumed or spliced.
- Attempt 4 proved that a delayed pulse could straddle a later G38 and become
  an approximately `0.000060 mm` zero-travel false contact. Attempt 5's two
  pauses instead followed valid contacts during retract/return outside G38;
  those accepted rows remain usable provenance but not a complete attempt.
- The revised exact T3 and T4 runners restore their own accepted frozen
  `#3032` after exact live-tool and TLO validation and before calculating probe
  geometry. T3 writes `0.117658`; T4 writes `0.154742`. Preview exits before
  the write, and later guards abort if the value changes.
- At the owner's request, both runners widen only the pass-1 acquisition
  diameter range to `29.5-31.0 mm`. Accepted pass 2 remains
  `29.9-30.5 mm` with a `0.10 mm` centering-residual gate.
- Attempt 6 exposed a conflict between the late-pulse oneshot wired to
  `halui.program.pause` and the runner's own 20-second clear-settle loop. The
  prepared Attempt-7 configuration restores pendant-only pause wiring and uses
  a monitor-only, retriggerable `0.5 s` event latch. The realtime G38-only
  probe gate, 10-second quarantine, 20-second continuous-clear proof, and
  60-second timeout remain. These saved changes are not live until a controlled
  HAL update or restart.
- Attempt 7 is barred until the operator resets/reseats T3 and
  `qualify_tcpc_probe_reset.py` passes the disabled untouched/three-deflection/
  final-soak sequence plus the enabled 120-second motionless soak. Any LED
  glow, spontaneous/repeated edge, latch reset, or raw/mux mismatch fails.
- Under the owner/operator's current campaign disposition, repeat ring
  verification was skipped for both legs while frozen offsets remained
  unchanged. The Attempt-6 electrical fault rejects that attempt. Whether the
  prior ring waiver remains acceptable after physical reseating must be
  explicitly confirmed before Attempt 7; no offset is recalculated implicitly.

## Superseded Handoff - Campaign 2026082201

- Campaign ID: `2026082201`.
- Ring phase and S1/T3 Stages A and B are complete. S1 Stage C-low attempt 1 is
  retained as an excluded canonical `13/20` partial; prepared attempt 2 was
  superseded without measurement and is retired.
- Frozen T3/S1/S2 probe offset: `0.117658 mm` (two verification rows accepted
  by explicit operator waiver of the normal three-row minimum).
- Frozen T4/L probe offset: `0.154742 mm` (three verification rows; maximum
  average error `0.005417 mm`, average range `0.008750 mm`, X/Y center ranges
  `0.004850/0.004101 mm`).
- The exact T4 program stopped after logging attempt 8 under its then-active
  `0.005 mm` gate. Its run hash and abort remain execution history; the complete
  rows were accepted later under the declared capability rule.
- S1 Stage A attempt 1 stopped on a corrected queued-motion synchronization
  guard. Attempt 2 retained one valid B0/C0 row, then stopped on a corrected
  C-SSI polarity comparison at C90. Attempt 3 completed all five canonical
  B0/C `0/90/180/270/0` rows.
- Attempt-3 opening-to-closing C0 drift was X `-0.004912 mm`, Y
  `-0.004718 mm`, Z `+0.003665 mm`, norm `0.007734 mm`. All programmed
  center/diameter/state gates passed. Directional diameters of
  `30.126330-30.279693 mm` remain diagnostic and are not a 10 um accuracy claim.
- S1 Stage B mode-16 attempt 1 completed all ten canonical rows. Outer B0
  closure was `0.016027 mm`; production-grid RMS/maximum were
  `0.031153/0.045463 mm`, passing the preferred `0.100 mm` maximum. B+5 and
  B-5 within-group closures were `0.002493/0.014061 mm`.
- During row 9 first pass, a laser-cutter false trigger caused an external pause
  while the CNC was stationary at the +U start before the next `G38.3`. Raw,
  mux, and motion probe inputs were clear before resume; the mandatory live
  guard ran before probing, rows 9-10 passed, and the operator confirms the CNC
  and measurement were not interfered with. Retain the event as provenance, not
  a rejected row. Keep the laser cutter and other EMI sources inactive during
  all remaining probe motion.
- S1 Stage C-low attempt 1 logged sequence 1-13, through B-10/C180. Intended
  sequence 14 at B-10/C270 completed its first pass and made a valid pass-2 top
  contact, then the immediate post-top-retract guard sampled the raw wireless
  probe during the designed HAL release interval. It aborted at
  `2026-08-22T16:06:03+07:00` with no sequence-14 row. Raw, muxed, and motion
  inputs were clear immediately afterward. The partial and exact executed file
  are preserved under
  `calibration_runs/20260822_1529_S1_T3_mode17_attempt1_partial/`.
- This historical, now-disarmed mode-17 runner used a bounded release-stability
  guard after each of the five
  contact retracts: gates must clear immediately, then raw and mux inputs must
  be clear on two consecutive `0.05 s` samples within a `1.0 s` post-retract
  timeout. Immediately-before-G38 guards remain strict. Attempt was advanced to
  `2`; no partial suffix is permitted.
- At the current checkpoint T3/H3 `128.606729 mm` is installed with frozen
  `#3032 = 0.117658 mm`. TCPC and the persistent correction are active; TWP,
  spindle, raw/mux/motion probe inputs, both digital requests, and the abnormal
  probe-pause output are off/clear.
- LinuxCNC is enabled, all five joints are homed, the interpreter is idle and in
  position, and velocity is zero. Commanded B/C are `0/0 deg`; the operator has
  placed T3 over the sphere. The current tip clearance is not yet accepted as
  the required `4-5 mm` attempt-2 start.
- The observed feed and rapid overrides are `100%` and `4%`. This is checkpoint
  state, not permission to change or start motion.
- Ring attempt `10` was selected and load-checked but explicitly waived by the
  owner/operator before Cycle Start because its incremental evidence is not
  justified by this machine's capability. It produced no ring motion or CSV
  row; attempt `9` remains the S1 installation reference and ID `10` is retired.
  The verifier is now restored to aborting sentinel selectors.
- The revised mode-17 attempt-2 runner was load-checked without a LinuxCNC
  message or XYZBC change, then preserved and superseded. The active legacy
  runner is disarmed; attempt 2 must not be started or reused.
- No geometry, correction-surface, B/C-zero, backlash, or tool-table change was
  made from the Stage A or B evidence.

## Historical Stored State - 2026-08-21 +07

- LinuxCNC config:
  `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.ini`
- Git HEAD: `86dd4068016ab748cf0e0e454075f2e2b6b6a7d2`
- The working tree contains the prepared calibration changes, the owner's
  uncommitted tool-table work, and unrelated pre-existing files. Do not clean,
  reset, or substitute a committed-only tree before capturing the campaign
  manifest.
- At the initial capture, LinuxCNC was enabled, in Manual mode, interpreter
  idle, and all five joints were homed and in position. At final handoff,
  LinuxCNC remained running but the machine was disabled; all five homed flags
  remained set and the interpreter remained idle.
- Current velocity, configured velocity, maximum velocity, feed override,
  rapid override, and spindle speed all read zero at final handoff.
- X/Y/Z were at machine zero. B was `-0.000010 deg`; C was within normal SSI
  zero quantization at approximately `-0.000367 deg`.
- All limit inputs were clear. B/C SSI-invalid signals were false and the
  LinuxCNC error channel was empty.
- The spindle was physically empty. Live software state was deliberately
  corrected from Probe Basic's restored T30 state to tool 0 with all nine tool
  offsets zero. No joint motion occurred during that correction.
- TCPC and TWP were off. Spindle, coolant, raw probe, probe mux, and probe gate
  were off/clear.
- Only Probe Basic's `blank.ngc` was selected. No calibration program was
  started and no calibration or probe motion occurred.
- There was no probe installed.

Probe Basic attempted its persisted probe-parameter MDI synchronization before
all joints were homed, so LinuxCNC rejected that startup attempt. It later
restored persisted `T30 G43 Z164.548` after homing; this was incorrect for the
physically empty spindle and was cleared with `G49` then `M61 Q0`. On every
restart, trust live IOC/motion/HALUI/kinematics state rather than the UI row and
verify tool 0 plus zero TLO before installing T3.

## Historical Campaign 2026082201 Data State

- The certified ring is stamped `50.001 mm`; the guarded ring routines were
  updated to use that value. The certified 30 mm sphere has also been
  identified by the owner/operator. Certificate IDs, full certificate values,
  uncertainties, and reference temperatures still need to be copied into the
  run manifest.
- Campaign `2026082201` is assigned. S1 Stage C-low attempt 1 is partial and
  excluded. Prepared mode-17 attempt 2 is preserved but retired; the active
  legacy runner is disarmed. Ring attempt `10` was waived unexecuted.
- T3 `0.117658 mm` and T4 `0.154742 mm` are accepted/frozen for the diagnostic
  campaign under the capability disposition above.
- `tcpc-long-short-ring-results.csv` contains its header plus eight retained
  rows: T3 qualification and two verifies, T4 qualification and three verifies,
  then S1 installation verification attempt `9`. Waived attempt `10` added no
  row.
- `tcpc-long-short-pair-results.csv` contains its header plus 29 retained rows:
  one incomplete mode-15 attempt-2 row, five complete mode-15 attempt-3 rows,
  ten complete mode-16 attempt-1 rows, and the 13-row incomplete mode-17
  attempt-1 prefix.
- No geometry coefficient, empirical correction coefficient, B/C zero,
  backlash, or tool-table value was changed during this checkpoint.

## Reviewed File Hashes

```text
b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.hal (prepared Attempt 7; not live yet)
26f2833cfb0c35b3d5653a507503dc7f5925e5eb7b12a15de3807f1e2557c727  configs/5th_axis_xyzbc_ssi_probe_basic/xhc.hal (prepared Attempt 7; not live yet)
e7d459a2c875f56f2fcdeeefd3c8fa889809a5545cd3eab1309176c8c623092d  configs/5th_axis_xyzbc_ssi_probe_basic/tool.tbl
1946ee06257aced2b8622dd53d2a88790943ef586da7891b374abf1a1853284a  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/subroutines/tcpc_ring_live_guard.ngc
7f806f335683908d1b69f59551af24ac3c22e1d64ab4a2d10bc26884576c276c  nc_files/calibration/50mm_ring_probe_qualify.ngc
15ded0868408874749a74e0690989372482394ad94002367643010de848cdff5  nc_files/calibration/50mm_ring_probe_verify.ngc (current disarmed sentinel)
02c8811a25a04263f0e14b0ec180cf592d9d5882714973e7ef8bd6fdb793874b  nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc (current disarmed sentinel)
70ba9ef3748bc1f50188160831928cc0f49185690b5951d53563368fd8ab1972  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-long-short-pair-results.csv
eb40fdf16565de8edba2c9610cf3cca3927537a52bb7bd0332fb3d6df734b0a7  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_long_short_pair.py
14e3f59d8a46fc9b82bc7c1b683c2d3406827363730d9102c72ccfe00628a13c  nc_files/calibration/tcpc_positive_b_c45_baseline_t3.ngc (prepared Attempt 7)
e816cc4c9e27a636726db6640c0c3ceab092b0dd3672d1fb36ea145650c18967  nc_files/calibration/tcpc_positive_b_c45_baseline_t4.ngc
bbbdc8aa28ea80c318a0dda3044ebcd0d9fa614557a1afe18721fbd7467cf934  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/qualify_tcpc_probe_reset.py
4e4918cce60d8ea2130a1605fb46f0d555b5722179274f6036c42a040c765e1a  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_positive_b_c45_baseline.py
e9d50c8cddde601b17274c64733a2324ffd3ed0a47da3671bcc351c3d66ccbd8  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-grid.csv
53bd0e3ca122d9001419634ba8b095a0140fd71a418472cbb5dec2855da406bd  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-results.csv (15 excluded attempt-3-to-5 rows; Attempt 6 zero-row)
```

Executed/pre-revision provenance:

```text
cedc4f3f37c0f99f3b314b808e53a18fb302186a1138293a949afc3ff37dc872  exact T4 attempts 5-8 qualifier; active 0.005 mm gate
d0f47423d6907d2c9c2e390c88887ae47ebd45616f81b78fe7370bbf8854c631  pre-revision standalone verifier
cfbef787ab07770003e3a0fa13f2651e6f1d370543a329d3d4e2076c823070dd  exact completed S1 Stage A attempt-3 runner
712ff7ea3584f7e8aa122b006e5caf69628033602d0cf0dfe7ded465dde590af  exact completed S1 Stage B attempt-1 runner
6e269b9d7f4a2814b066dac78be039156390bd1cc6ac1f468fce57e96915686b  exact partial S1 Stage C-low attempt-1 runner
57c38342434e0473da9b06fa9b85f10d03cc10dc31226c01b4da5ce4312ed4  historical pre-attempt-10 verifier
a3f462f3f4d878de20687cfcf1e5ece09389788c2b815e8e38dac01a02d82cb7  armed attempt-10 verifier; waived and unexecuted
9e370c91f49f0ca78d7cef1a5e3ccb3a472df1dd1afd2a899c452249c3580f49  exact prepared mode-17 attempt-2 runner; superseded and retired
f3e60ba17f9218538c2f17883f31077b2f7a8eda0fdf2331f5b387bce868569f  exact Attempt-6 zero-row electrical-fault T3 runner
077e27e3bce7ac318749f25792d10bb80846d9d674c4774e3d98abc689c3f15b  exact Attempt-6 HAL with 20-second auto-pause hold
75fe4dd23de4d586d5e0e1957169f50a928930e717c7f66ce58c277cbe864c5b  exact Attempt-6 xhc pause-OR wiring
```

Recompute and compare these hashes before the next operator load or run. Any
difference requires review before Cycle Start.

Current campaign and live machine state are recorded in
`TCPC_BASELINE_CAMPAIGN_2026082202.md`; campaign `2026082201` remains historical
provenance.

## Current Operator Order

1. Keep the laser cutter and other observed EMI sources inactive. At the
   current 100 mm clear pose, apply LinuxCNC E-stop/disable before removing T3.
   Wait for every probe/receiver LED to extinguish, then reinstall with the
   same controlled clocking and retention practice. Do not enable or move the
   CNC while T3 is absent.
2. Run the read-only reset qualification: 60 seconds disabled/untouched, three
   approximately one-second hand deflections with 30 seconds untouched after
   each, another 60 seconds disabled/untouched, then a 120-second enabled but
   motionless soak. LED glow, spontaneous/repeated edges, latch resets, stuck
   state, or raw/mux disagreement bars Attempt 7.
3. Apply the reviewed Attempt-7 HAL live while disabled or restart LinuxCNC;
   verify pendant Pause still works, the event latch is `0.5 s`, and the fault
   signal is no longer connected to `halui.program.pause`. Revalidate all homes,
   B0/C0, TCPC/TWP/correction, T3/H3 TLO, inputs, WCS, limits, and clearance.
4. Establish the operator-confirmed 4-5 mm sphere start. Confirm selected
   `tcpc_positive_b_c45_baseline_t3.ngc` matches the reviewed Attempt-7 hash,
   remains at line 0 with unchanged position, its campaign/mode/leg/attempt
   selectors are `2026082202/19/1/7`, and the output CSV still ends at excluded
   attempt-5 sequence 2 with no Attempt-6 row.
5. The first Cycle Start may advance only to the mandatory pre-motion M0. It
   executes guards and restores frozen T3 `#3032 = 0.117658`, but commands no
   axis motion before the hold. Recheck the post direction, T3 body/holder
   clearance, selectors, and live state. Resume only under explicit operator
   authority.
6. The program measures 31 rows: all C45 slots at B0; C0/C45/C90/C180/C225/
   C270/C0 at B+5, B+15, and B+30; then final B0/C0 closure. It never descends
   or probes the six tilted C135/C315 gaps. Obey every built-in inspection hold.
7. After T3 completes, freeze the exact runner and appended interval and require
   this command to exit `0` before changing tools:

   ```bash
   python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_positive_b_c45_baseline.py \
     configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-results.csv \
     --grid configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-grid.csv \
     --leg-only 1
   ```
8. Perform the controlled B0/C0 TCPC exit and manual T4 change from verified
   linear clearance. Apply T4/H4 `229.407000 mm` and the reviewed TCPC entry;
   establish a fresh operator-confirmed 4-5 mm start and preflight the exact
   T4 runner. That runner restores frozen `#3032 = 0.154742 mm` itself after
   exact live-tool and TLO validation.
9. Run the same guarded grid for T4 as campaign leg 2. Confirm the long body and
   holder have post clearance at every hold. Analyze both legs before planning
   any negative-B, S2, model, zero, tool-table, rail, or correction change.

## Superseded Campaign 2026082201 Operator Order

Do not execute this historical order while campaign `2026082202` is current.

1. Revalidate the current idle B0/C0 state and physical sphere clearance. Never
   use stored XYZ as an unattended motion target. Keep the laser cutter and
   other observed EMI sources inactive.
2. Under the documented software-abort recovery exception, keep the unchanged
   T3 installation and TCPC active. Under operator supervision, establish the
   T3 tip `4-5 mm` clear above the sphere at B0/C0, then revalidate every live
   state and clearance item. If any exception condition no longer holds, stop
   and use the normal reviewed TCPC entry procedure.
3. If this campaign is explicitly resumed later, prepare a newly reviewed exact
   mode-17 runner for campaign `2026082201`, mode `17`, leg `1`, offset
   `0.117658`, attempt `3`. The first Cycle Start may advance
   only to the mandatory pre-motion `M0`; re-read selectors and clearance there.
4. Resume from that initial hold only after explicit operator authorization.
   Mode 17 first measures the five-row B0/C `0/90/180/270/0` group, then pauses
   at B0/C0 for row and clearance inspection before any B+10 motion.
5. After that second resume there is no final inspection `M0`: mode 17 runs five
   rows at B+10, five at B-10, a five-row closing B0 group, and `M2`. Inspect all
   20 rows, four group closures, diameter behavior, balanced B signs, state
   fields, and clearances after completion.
6. After S1 mode 17 is accepted, S1's released prefix is complete. Use the
   controlled B0/C0 TCPC exit and tool-change procedure, perform the frozen T4
   ring installation verification, then prepare L/T4 mode 15 as leg `2`,
   attempt `1`. Do not requalify `#3032`.
7. Analyze the absolute effective center offset
   `center_L - 0.5*(center_S1 + center_S2)` and the separate B0-referenced
   pose-dependent difference before authorizing B+/-30.
8. Do not change B-zero, TCP geometry, persistent corrections, tool X/Y, or rail
   compensation during baseline collection.

## T3 Exploratory Package - 2026-08-26

The operator elected to continue with a separately declared short-probe
tool-length transfer diagnostic. The formal mode-24 T3 runner and its three
header-only files remain untouched. The new acquisition is campaign
`2026082601`, mode `30`, attempt `1`, and is always labeled `R2 NOT ACCEPTED`.

Prepared identities:

```text
90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5  nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc
347a0bfb9f616875fa7c68a24d9134269a0e4dce967deca11b21d278a2b49a47  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t3_exploratory_a1.ini
ba863ff3747ed1efe7540616423369b424452cc331c42568a211583f6350f00c  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_t3_r2_transfer_exploratory.py
a678fd580b7fdf013287ea4296b84ebe0567105e6192b05045038e0141a6b6e2  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_PLAN.md
e1b8a99ebfeba81a26511d0c7b816772786a966a8a15f682c0f4466bb3e05d61  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_PREFLIGHT_REPORT.md
```

The INI is derived from baseline task-capture SHA
`afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519`.
Its sole functional addition is observation counter HAL SHA
`6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34`;
the base TCPC HAL remains
`b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`.
The R2 overlay is absent and all 30 R2-target pins are runtime-guarded at their
exact baseline values.

The runner uses the completed Attempt-5 four-contact/two-pass transaction,
G38-only gate, sticky counter/contact/gap ledgers, bounded whole-pose retry,
release checks, and protected transits. It has one initial M0, no clearance
sweep, no later holds, no 20-second settle delay, and exactly 31 accepted poses
over B0, B+/-45, and B+/-90 C quadrants with 14 source-local closures. Five
new output files are exact header-only files.

Offline preflight exited `0`: isolated-HOME RS274 parsing passed, exact
configuration/program/header checks passed, and configured-limit replay of the
same 31-pose T3 topology passed. This replay does not establish physical T3
body, holder, cable, post, sphere, or fixture clearance; the operator owns that
decision at the sole initial M0.

At this checkpoint LinuxCNC and HAL were closed and no machine command or
motion was issued. The operator subsequently authorized launch and load only.
Launch the exact T3 diagnostic INI above, then load only the exact runner at
line 0. Do not Home, jog, MDI, Cycle Start, or Resume on the assistant's
authority. After operator setup, the first Cycle Start may advance only to the
single initial M0. Any abort, missed touch, closure fault, or T3 reseat retires
attempt 1 and requires preserved partial files plus a new attempt namespace.

Load-only completed at `2026-08-26T10:04:30+07:00`. LinuxCNC is running from
the exact diagnostic INI and the exact mode-30 runner is selected at line 0.
The load produced zero commanded and actual XYZBC change. The machine remains
disabled and unhomed with T0, zero TLO, clear raw/mux/gated probe levels,
`0/0/0` counters, five exact header-only outputs, and no controller error.
No program was started. The next step belongs to the operator: enable/reset,
Home All, install and establish T3/H3 plus G43.4, position 3-5 mm above the
sphere at B0/C0, and confirm physical clearance before Cycle Start to the sole
M0. See `TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_LOAD_REPORT.md`.

Sealed checkpoints:

```text
calibration_runs/20260826_0959_campaign2026082601_t3_r2_transfer_exploratory_attempt1_pre_run
SHA256SUMS 0dafc8bd1f020ab3afc060d84afaf990c6f1c1b70609c54a816f4ac257d3a3ff
calibration_runs/20260826_1004_campaign2026082601_t3_exploratory_attempt1_load_only
SHA256SUMS 51e545091ff755fc73f6ba9fbf6f7294949e1d588ee0f433c7cf7794e31c0543
```

After the sealed zero-count load checkpoint, 11 matched raw/mux edges and zero
gated edges were observed from `10:05:02` through `10:06:07` while the machine
remained disabled/unhomed and the program remained at line 0. All probe and
abnormal levels were clear afterward, and outputs remained header-only. The
source is not yet classified as deliberate hand testing or spontaneous T3
activity. See `TCPC_RELOCATED_SPHERE_T3_POST_LOAD_PROBE_OBSERVATION.md` and
require operator classification plus a stable clear probe before Cycle Start.
