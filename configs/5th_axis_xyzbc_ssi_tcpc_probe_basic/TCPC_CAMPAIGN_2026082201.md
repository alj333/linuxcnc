# TCPC Campaign 2026082201

Status: paused and superseded for current operations by separate baseline
campaign `2026082202`. The ring phase and S1/T3 Stages A and B are complete.
S1 Stage C-low attempt 1 is a retained excluded `13/20` partial. Prepared
attempt 2 produced no measurement row or axis/probe motion before supersession;
its ID is retired and any future mode-17 restart must use attempt 3. The active
legacy runner is disarmed. No machine-model correction has been authorized.

Started: `2026-08-22 +07`

Authoritative procedure: `TCPC_LONG_SHORT_PROBE_CALIBRATION_PLAN.md`

## Supersession Record

The owner redirected work to a two-leg positive-B/C45 baseline using T3 short
then T4 long. That work has campaign ID `2026082202`, its own runner pair, grid,
CSV, analyzer, manifest, and procedure
`TCPC_POSITIVE_B_C45_BASELINE_PLAN.md`. Its rows must never be appended to or
interpreted as this campaign's modes 15-18 data.

The exact mode-17 attempt-2 runner remains preserved with SHA-256
`9e370c91f49f0ca78d7cef1a5e3ccb3a472df1dd1afd2a899c452249c3580f49`.
At supersession LinuxCNC was idle at line 0, in position, at zero velocity, and
at unchanged XYZBC; the paired CSV remained unchanged. This proves no
axis/probe motion or row occurred. It does not independently distinguish a
never-started file from one that may have briefly reached its initial
pre-motion M0, so no stronger claim is made. Attempt ID 2 is retired.

## Artifact State

- Certified ring stamped value: `50.001 mm`
- Ring routine reference value: `50.001 mm`
- Certified sphere nominal value: `30 mm`
- Owner/operator confirms the ring is stable and has not moved. Observed
  short/long differences are therefore classified as machine/probe-system
  evidence, subject to the certificate and temperature records below.
- This steel-frame machine is not treated as a metrology machine. A result
  within `0.010 mm` is very good for this calibration stage; the purpose of the
  dual-length work is to separate repeatable correctable terms from spindle
  seating, Z-rail, alignment, flex, and other mechanical uncertainty.
- Ring certificate ID, uncertainty, and reference temperature: pending entry
- Sphere certificate ID, calibrated value, uncertainty, and reference
  temperature: pending entry before final dataset/model acceptance. Stage A
  used the owner-certified nominal `30.000 mm` value under an explicit operator
  diagnostic-collection waiver. The waiver does not authorize a fit,
  calibration change, or production release.

## T3 Opening Qualification Preflight

- Physical short probe installed; operator identifies it as T3.
- Live IOC tool: T3
- Live tool diameter: `6.000000 mm`
- Motion, HALUI, and kinematics Z TLO: `128.606729 mm`
- All non-Z tool offsets: zero
- All five joints: homed and in position
- B/C command and feedback: angular-equivalent to zero
- B/C SSI-invalid: false
- TCPC/TWP: off
- Spindle/coolant: off
- G54 active; G54 B/C offsets and XY rotation: zero
- G92 offsets: all zero
- Raw probe, probe mux, motion probe input: clear
- Supervised hand trip: raw and mux asserted and released; motion probe input
  remained gated off outside G38 motion
- Operator-reported start: probe `3-4 mm` onto the left wall from the bore,
  approximately on the Y centerline and `5 mm` above the wall
- T3 qualification program selector used: campaign `2026082201`, attempt `4`
- Executed T3 qualification file SHA-256:
  `3242c9bad2de374bbd5ff99808331e7969852e11cb01710d5054ba21a86219dd`
- Executed T3 verification-attempt-2 file SHA-256:
  `3149212200e28333d4689538f16d995b3088ddf9fe8e6750a4f7d34a1a85742f`
- Feed and rapid overrides were zero during preparation

Before the first Cycle Start, the operator must confirm the probe is over the
top face of the left ring wall, approximately on the Y centerline, within
`15 mm` above the surface, and that the routine's `+X 10 mm` step places the
6 mm ball center clearly inside the bore. The first Cycle Start may only
advance through guards to the
mandatory M0. A separate operator confirmation is required before resuming
from M0 into probe motion.

## Attempt History

- Attempt 1: the operator stopped after the top contact because the fixed
  `+X 3 mm` move did not place the 6 mm ball safely inside the bore. No result
  row was logged and the routine had not reached its `#3032` assignment. The
  machine remained homed, idle, probe-released, and error-free.
- Corrective change: both ring wrappers and their live guard now require a
  `+X 10 mm` step from the reviewed `3-4 mm` left-wall start.
- Attempt 2: the corrected 10 mm entry cleared the bore and probing progressed
  normally through multiple contacts. The external Codex monitor incorrectly
  treated the designed post-contact probe-release window as unsafe and issued
  Abort during a valid Y-minus contact. The probe released, the machine
  remained homed and error-free, no result row was logged, and the routine had
  not reached its `#3032` assignment. This was a monitoring error, not a probe
  or machine failure. Future monitoring is passive and leaves contact/release
  handling to the reviewed HAL and G-code guards.
- Attempt 3: the full probe-motion sequence completed, returned to clearance,
  and calculated `#3032 = 0.118700 mm`. The final 271-character `(LOG,...)`
  command exceeded LinuxCNC's command buffer, so the interpreter stopped before
  writing a CSV row. The machine remained homed, in position, and probe-clear.
  This result is not accepted or frozen because its required record is absent.
- Corrective change: qualification and verification now stage the same 22 CSV
  fields through unused numeric scratch parameters `#1100` through `#1112`.
  Each `(LOG,...)` command is 131 characters; field order and CSV schema are
  unchanged. The corrected qualification file passed an idle load/preview
  check with zero joint movement and no LinuxCNC messages.
- Attempt 4: completed normally and wrote the first canonical ring row for
  campaign `2026082201`. T3/H3 was `128.606729 mm`; X diameter was
  `50.334233 mm`, Y diameter `50.138400 mm`, and their average
  `50.236316 mm`. The resulting T3 candidate is `#3032 = 0.117658 mm`.
  G54 XYZ, all three live Z TLO views, and machine state closed unchanged.
  The machine ended homed, idle, in position, and probe-clear with TCPC/TWP
  and the spindle off.

## Results

- Qualification attempt 4 is recorded in
  `tcpc-long-short-ring-results.csv` as `cycle_kind=1`.
- T3 candidate frozen for verification: `0.117658 mm`.
- Verification attempt 1 is recorded as `cycle_kind=2`: X `50.097250 mm`,
  Y `49.903084 mm`, average `50.000167 mm`, X center `592.283568 mm`,
  and Y center `-1026.688883 mm`. Average error from the certified ring is
  `-0.000833 mm`, numerically within `0.005 mm`. Frozen offset, WCS, and all TLO
  views closed unchanged.
- Verification attempt 2 is recorded: X `50.097251 mm`, Y `49.905584 mm`,
  average `50.001417 mm`, X center `592.282669 mm`, and Y center
  `-1026.689233 mm`. Average error is `+0.000417 mm`. Across attempts 1-2,
  X-center range is `0.000899 mm` and Y-center range is `0.000350 mm`.
  Frozen offset, WCS, and all TLO views again closed unchanged.
- The operator directed the campaign to move on after two verification rows.
  This is retained as a deliberate waiver of the normal three-row minimum.
  Both rows pass the `0.010 mm` average-error contract and the available center
  ranges are below `0.001 mm`. For this diagnostic campaign, T3 offset
  `0.117658 mm` is accepted and frozen for both S1 and S2. Later installation
  checks add evidence but must not recalculate this value.

## T4 Integrated Qualification Preparation

- Preparation checkpoint: `2026-08-22T11:39:53+07:00`.
- Physical long probe installed through the normal tool workflow; live IOC tool
  is T4 with diameter `6.000000 mm`.
- `G43 H4` is active. Motion, HALUI, and kinematics Z TLO are all
  `229.407000 mm`; all non-Z tool offsets are zero.
- All five joints are homed and in position. The machine is enabled, the
  interpreter is idle, and commanded velocity is zero.
- B/C are angular-equivalent to zero with valid SSI. TCPC, TWP, spindle, and
  coolant are off. G54 is active with G92 clear.
- Raw probe, probe mux, motion probe input, and both probe gates are clear.
  A supervised hand trip asserted and released the raw and mux signals twice;
  `motion.probe-input` remained gated off outside G38 motion.
- Operator-reported start: T4 is over the left ring wall, approximately on the
  Y centerline and at the reviewed top clearance.
- Integrated selector base is campaign `2026082201`, attempt `5`. The base
  reserves IDs `5-8`: qualification uses `5`, and the program attempts three
  automatic verification rows using `6`, `7`, and `8`. A passing set requires
  all three rows to pass. A failed set may contain only a completed prefix and
  is rejected. Any partial retry advances the base to `9`; retained rows are
  never overwritten or treated as accepted evidence.
- Exact prepared and subsequently executed integrated qualification SHA-256:
  `cedc4f3f37c0f99f3b314b808e53a18fb302186a1138293a949afc3ff37dc872`.
  Its longest source line is 237 characters and both log records have the
  required 22 fields. Independent exact-tree safety review found no remaining
  high-severity or blocking issue.
- Load-only checkpoint: `2026-08-22T11:54:21+07:00`. LinuxCNC retained a stale
  paused flag from the prior session while `blank.ngc` was selected. Stop/Abort
  cleared it to interpreter idle with zero velocity and no XYZ/B movement. The
  exact reviewed qualifier was then loaded successfully in Manual mode. It
  remained idle, emitted no LinuxCNC message, and caused no XYZ/B movement;
  normal C SSI zero quantization continued. The ring CSV remained at its header
  plus the three existing T3 rows.
- At this preparation checkpoint, the standalone verification wrapper was
  disarmed at sentinel selectors. Its then-current SHA-256 was
  `d0f47423d6907d2c9c2e390c88887ae47ebd45616f81b78fe7370bbf8854c631`.
- The integrated program's first Cycle Start advances through guards to the
  initial mandatory `M0`; resuming that hold is separate authorization for the
  qualification probe sequence. After the candidate is logged and a protected
  wall start is established, the program stops at a second `M0`. Resuming that
  hold authorizes the three-round automatic verification attempt. The first
  failed numeric gate is logged and stops at measured-center clearance before
  any automatic wall repositioning.
- Under the then-active program contract, a row failing a numeric gate remained
  diagnostic-only and required manual review. That is the execution rule that
  produced the attempt-8 abort; the later capability disposition is recorded
  separately below.

## T4 Integrated Set 5-8 Execution History

- Completed terminal checkpoint: `2026-08-22T12:14:11+07:00`.
- Qualification attempt `5` logged X `50.398400 mm`, Y `50.222567 mm`,
  average `50.310483 mm`, X center `592.193852 mm`, and Y center
  `-1026.756250 mm`. It changed the provisional T4 candidate from the prior
  live `0.117658 mm` to `#3032 = 0.154742 mm`.
- The operator confirms that the long probe requires more lateral displacement
  to trigger because of its length. Its separate radial pre-travel calibration
  is therefore expected to differ from T3: the provisional T4 candidate is
  `0.037084 mm` larger than the provisional T3 candidate. This difference is
  not itself a failure. `G43 H4 = 229.407000 mm` represents axial tool length;
  `#3032 = 0.154742 mm` represents the long assembly's lateral trigger offset.
  Neither value substitutes for the other.
- Verification attempt `6` logged X `50.096416 mm`, Y `49.912250 mm`, average
  `50.004333 mm`, X center `592.188702 mm`, and Y center `-1026.754099 mm`.
  Average error was `+0.003333 mm`, inside the `0.005 mm` gate.
- Verification attempt `7` logged X `50.083083 mm`, Y `49.911417 mm`, average
  `49.997250 mm`, X center `592.193552 mm`, and Y center `-1026.758200 mm`.
  Average error was `-0.003750 mm`, inside the gate.
- Verification attempt `8` logged X `50.081416 mm`, Y `49.909750 mm`, average
  `49.995583 mm`, X center `592.190903 mm`, and Y center `-1026.754799 mm`.
  Average error was `-0.005417 mm`, outside the gate by `0.000417 mm`.
- Across the three verification rows, maximum absolute average-diameter error
  was `0.005417 mm`, averaged-diameter range was `0.008750 mm`, X-center range
  was `0.004850 mm`, and Y-center range was `0.004101 mm`. X diameter range was
  `0.015000 mm`; Y diameter range was `0.002500 mm`.
- The program logged attempt `8`, raised its designed diameter-gate abort, and
  stopped without wall repositioning. Terminal G53 XYZ was approximately
  `1315.189186, 444.713517, -583.351065`; the probe was at measured-center top
  clearance. LinuxCNC was interpreter-idle, homed, in position, and at zero
  velocity. Raw/mux/motion probe inputs and both gates were clear. G54, G92,
  all three live TLO views, and TCPC/TWP state closed unchanged.
- The exact executed program and hash above factually stopped under its
  then-active `0.005 mm` per-row gate. IDs `5-8` remain consumed. This history is
  not rewritten as a clean program completion.

## Capability Review and Ring Disposition

Decision checkpoint: `2026-08-22 +07`, after the owner/operator clarified that
`0.010 mm` is a very good result for this machine.

- The reviewed ring contract is now: each verification average within
  `0.010 mm` of `50.001 mm`; three-row averaged-diameter range no more than
  `0.010 mm`; X-center and Y-center ranges each no more than `0.010 mm`; and no
  false probe trip or frozen-state violation. Per-axis X/Y split and trends are
  retained as diagnostics rather than silently absorbed by scalar `#3032`.
- T4 attempts `6-8` pass all four numeric gates: maximum absolute average error
  `0.005417 mm`, average range `0.008750 mm`, X-center range `0.004850 mm`, and
  Y-center range `0.004101 mm`. The complete logged set therefore passes the
  revised capability review without another qualification cycle.
- T4 `#3032 = 0.154742 mm` is accepted and frozen for this physical long-probe
  assembly and the planned L leg. T3 `#3032 = 0.117658 mm` remains separately
  frozen for S1 and S2. Their `0.037084 mm` difference is the measured
  assembly-specific lateral trigger pre-travel difference.
- The prepared qualifier and standalone verifier now enforce the reviewed
  `0.010 mm` contract. They are disarmed at selector sentinels. Their current
  reviewed hashes are recorded in `TCPC_CALIBRATION_RESUME_STATE.md`; the
  executed T4 hash above remains the authority for what actually ran.

## Error Classification From the Ring

- Mean T3 verification center: X `592.2831185 mm`, Y `-1026.6890580 mm`.
- Mean T4 verification center: X `592.1910523 mm`, Y `-1026.7556993 mm`.
- T4 minus T3 center: X `-0.092066 mm`, Y `-0.066641 mm`; vector magnitude
  `0.113654 mm` across a `100.800271 mm` tool-length separation.
- That vector is real combined evidence, but it is not an identified B-zero or
  tool-axis correction. At one fixed ring height it combines probe/holder
  insertion eccentricity, spindle wear, the different Z-carriage rail
  positions, directional trigger behavior, tool/spindle alignment, and any
  rotary-zero contribution. Ring work at B0/C0 with TCPC off cannot identify
  rotary TCP geometry.
- T3 X-minus-Y diameter splits are about `0.192 mm`; T4 splits are about
  `0.172-0.184 mm`. A scalar `#3032` corrects the certified averaged diameter
  but cannot correct this directional response or move the measured center.
- No X/Y tool-table offset, B-zero change, rail compensation, spindle tilt, or
  TCPC coefficient is authorized from these ring rows.

## Historical Resume Path

This is not the current operator order. Campaign `2026082202` must be closed or
explicitly abandoned before this campaign is reconsidered.

1. Keep both frozen offsets. Do not requalify `#3032` for each insertion.
2. Before each S1/L/S2 sphere leg, perform one frozen-offset ring installation
   check and record its center, holder/spindle clock mark, temperature,
   installation ID, and attempt ID. S2 returning toward S1 bounds short-probe
   reseating/session drift without delaying the primary pose experiment. S1
   already has attempt `9`; the owner/operator explicitly waived an additional
   post-abort attempt `10` because this machine's capability does not justify
   its incremental evidence.
3. The paired sphere CSV and analyzer must include accepted-pass absolute XYZ
   plus X/Y/Z joint motor command, feedback, and following error before sphere
   motion. These fields permit rail-position correlation but do not deconfound
   rail geometry by themselves.
4. S1-T3 modes 15 and 16 are accepted. Mode-17 attempt 1 is a retained excluded
   `13/20` partial and prepared attempt 2 is retired. After a fresh reviewed
   B0/C0 sphere start and full live preflight, a future restart must use attempt
   3 and review its
   B0/B+10/B-10/closing-B0 map. After the accepted S1 prefix, run the same modes
   for L-T4 and then S2-T3. Analyze all three legs before authorizing mode 18 at
   B+/-30.
5. At each aligned sphere pose, calculate the absolute effective center offset
   `center_L - 0.5*(center_S1 + center_S2)`. Separately compare B0-referenced
   residuals to show how that offset changes with B/C. C quadrants and balanced
   B signs are the primary evidence for a repeatable rigid correction.
6. Treat the effective map as a combined length/setup result until validation.
   If S1/S2 closure or the pose map is ambiguous, then run the controlled
   `0 -> 90 -> 180 -> repeat 0 deg` clocking study and/or a second long insertion.
7. Separating Z-rail error from tool-length error requires the same assembly at
   two stable artifact heights spanning the relevant rail distance, or
   independent rail/spindle metrology. Two different probe lengths at one
   artifact height are not sufficient.

## Superseded Machine Handoff

- Checkpoint: `2026-08-22T16:48:58+07:00` after the S1 Stage C-low attempt-1
  abort, evidence capture, guard correction, operator waiver, and load-only
  checks.
- T3/H3 `128.606729 mm` remains installed with frozen `#3032 = 0.117658 mm`.
  TCPC and the persistent correction are active; every TWP state is clear.
- LinuxCNC is enabled, interpreter-idle, in position, and all five joints are
  homed. B/C commands are `0/0 deg` with valid SSI; spindle speed and current
  velocity are zero. Raw, muxed, and motion probe inputs, both digital requests,
  and the abnormal-pause output are clear.
- The operator later established T3 at B0/C0 with `5.000 mm` relative tip
  clearance above the sphere. This pose was unchanged at supersession, but it
  is not stored motion authority and must be revalidated before any future run.
- For this software-only abort recovery, retaining the unchanged T3 installation
  and continuously active TCPC state at B0/C0 is explicitly reviewed instead of
  an exit/re-entry cycle. This exception ends on any tool, TLO, WCS, correction,
  home, TCPC, or saved-entry-orientation change.
- The owner/operator waived ring attempt `10` before Cycle Start; it produced no
  ring motion or CSV row, and attempt `9` remains the S1 installation reference.
  The ring verifier is disarmed. The revised mode-17 attempt-2 runner was
  load-checked, then preserved and superseded without measurement. Attempt 2 is
  retired; the disarmed active legacy runner is not authorized to start.

## Sphere Software Readiness

- Historical full-set no-motion load checkpoint: `2026-08-22T12:53:42+07:00`.
- The paired CSV schema has 46 fields. Each accepted pose now includes absolute
  endpoint XYZ and joint 0/1/2 motor command, feedback, and following error.
- The analyzer self-test passes exact schema/state/sequence QA, following-error
  consistency, the existing B0-referenced residual calculation, and a regression
  proving that a constant absolute long-minus-bracketed-short center offset is
  preserved rather than normalized away.
- Safety review reduced the top probe vector from `16 mm` to `7 mm` and requires
  a `4-5 mm` initial tip clearance. A missed top contact is therefore limited to
  `2-3 mm` travel beyond nominal contact; the side searches retain `2 mm` miss
  overtravel.
- The revised qualifier, verifier, and paired runner were each selected through
  LinuxCNC `program_open` without a message or any XYZ/B/C change. The
  interpreter stayed idle, velocity stayed zero, T4 and all five homed flags
  remained unchanged, and `blank.ngc` was restored afterward.
- Load preview exits through each file's preview guard, so this check confirms
  safe selection/UI acceptance but does not execute the guarded body. Static
  checks separately confirm a 239-character maximum line, exact 46-field
  logger/header mapping, balanced O-words, and clean whitespace.

## S1 T3 Installation Ring Check

- Installation verification attempt: `9`; cycle kind `2`; completed
  `2026-08-22 +07` without a probe, state, or numeric-gate fault.
- Exact armed verifier SHA-256:
  `b2a4a7cb24417b36ee65d52a44898fd541af12ad63c68d3c7925c8ddb50c8584`.
- T3/H3 and frozen `#3032` were `128.606729 mm` and `0.117658 mm`.
- X diameter `50.096417 mm`; Y diameter `49.902250 mm`; average
  `49.999334 mm`; certified-average error `-0.001666 mm`. The radial
  installation check passes the `0.010 mm` contract.
- Measured center: X `592.249169 mm`, Y `-1026.711400 mm`. Relative to the mean
  of the two opening T3 verification centers, this installation moved X
  `-0.0339495 mm`, Y `-0.0223420 mm`, vector magnitude `0.0406415 mm`.
- The X-minus-Y diameter split is `0.194167 mm`, essentially the same directional
  characteristic as the opening T3 rows. The changed center with preserved
  radial average/split is recorded as spindle/holder reseating evidence, not a
  reason to recalculate `#3032` or alter TCP geometry.
- This measured center is the ring reference for the physical S1 installation.
  The S2 installation check will quantify whether T3 returns toward it; sphere
  analysis will retain the absolute center offset rather than normalize it away.
- Terminal state was interpreter-idle, zero velocity, in position, all five
  joints homed, T3 active, and every probe input/gate clear. The verifier source
  was returned to its sentinels after completion.
- Ring CSV after attempt 9: SHA-256
  `e187bc446e755c2f97d6ee0dad3cb559202ce3ea4cee6e440cb7fd48d0a0e2a4`.

## S1 Stage A Sphere Execution

- Mode `15`, leg `1`, used T3/H3 `128.606729 mm`, frozen
  `#3032 = 0.117658 mm`, TCPC active, TWP clear, and the persistent correction
  enabled. The sphere and machine calibration state were not changed between
  attempts.
- Attempt `1` made a valid top contact, but the following live guard sampled the
  raw probe state before the queued retract had physically executed. It aborted
  with the probe held at contact and wrote no row. The operator manually lifted
  clear and stopped the aborted program.
- Correction after attempt 1: every paired live guard begins with
  `M66 E0 L0`, and a final synchronized guard runs after the last side retract
  before accepted endpoint and joint state are captured.
- Attempt `2` completed and retained one valid B0/C0 row. It then reached C90
  and aborted before probing because the software compared direct C SSI with
  the wrong sign. Direct C SSI is opposite joint-C polarity; this was a software
  pose-check error, not an SSI-invalid or rotary-position fault.
- Correction after attempt 2: the C guard and analyzer now compare the wrapped
  equivalent of `C_ssi + C_cmd`. The same-polarity B check remains unchanged.
  The incomplete attempt-2 prefix remains in the source CSV as provenance and
  is ignored when a later complete attempt is selected.
- Attempt `3` completed the canonical B0/C `0/90/180/270/0` sequence with five
  accepted rows and no probe, live-state, SSI, or QA abort. Executed runner
  SHA-256:
  `cfbef787ab07770003e3a0fa13f2651e6f1d370543a329d3d4e2076c823070dd`.
- Opening-to-closing C0 center change was X `-0.004912 mm`, Y
  `-0.004718 mm`, Z `+0.003665 mm`; vector norm `0.007734 mm`, passing the
  `0.050 mm` closure gate.
- The opening/closing C0 mean was X `1024.044433 mm`, Y `443.395959 mm`, Z
  `-403.3081335 mm`. Relative center magnitudes were `0.050691 mm` at C90,
  `0.069135 mm` at C180, and `0.028643 mm` at C270. These pose-dependent shifts
  exceed the `0.0077-0.0089 mm` same-pose closure/repeat evidence and are
  systematic evidence, but cannot be assigned to a coefficient or mechanical
  cause until L and S2 bracket them.
- Accepted U/V corrected diameters ranged from `30.126330` to `30.279693 mm`.
  Every programmed broad QA gate passed, but this directional bias is not a
  10 um sphere-diameter result. Midpoint centers can repeat more closely because
  common pretravel cancels; retain the diameter behavior as probe/contact-system
  diagnostic evidence.
- Pair CSV now has one incomplete attempt-2 row and five complete attempt-3
  rows. SHA-256:
  `aa1e83c509bfb171c9b8c2de2b13fc64cacbea68f56768f1176805a2c9e164d5`.
  Analyzer SHA-256:
  `eb40fdf16565de8edba2c9610cf3cca3927537a52bb7bd0332fb3d6df734b0a7`;
  its self-test passes. Full paired analysis intentionally remains incomplete
  until L and S2 exist.
- Attempt 3 ended cleanly at the programmed inspection stop and then `M2`, with
  T3 clear above the sphere at B0/C0. The runner was then armed for S1 Stage B
  attempt `1` with SHA-256
  `712ff7ea3584f7e8aa122b006e5caf69628033602d0cf0dfe7ded465dde590af`.
  Its load-only check was motionless and message-free before Stage B started.

## S1 Stage B Sphere Execution

- Mode `16`, leg `1`, attempt `1` completed all ten canonical rows:
  opening B0/C0; B+5 C0/+20/-20/C0; B-5 C0/+20/-20/C0; closing B0/C0.
  T3/H3, frozen `#3032`, TCPC/TWP, persistent correction, WCS, sphere, and
  machine calibration state remained unchanged.
- The mandatory internal pause after row 5 occurred at B+5/C0. Its within-group
  closure was X `+0.001445 mm`, Y `-0.000308 mm`, Z `+0.002008 mm`, norm
  `0.002493 mm`; live state and all probe inputs were clear before resume.
- During row 9 first pass at B-5/C0, a laser-cutter false trigger caused an
  external pause while the CNC was stationary at the +U start on source line
  `520`, before the live guard and `G38.3` on lines `526/528`. At inspection the
  queue was empty, the machine was in position, raw/mux/motion probe inputs were
  clear, and LinuxCNC had no error. On resume the live guard revalidated state
  and clear inputs before probing. Rows 9 and 10 then passed and logged normally.
  The operator confirms the CNC and measurement were not interfered with; all
  rows are accepted for this baseline. Retain the event as provenance and keep
  laser cutters and other observed EMI sources inactive during remaining probe
  programs. Any suspected false trigger during active `G38` rejects that
  attempt.
- Closing-minus-opening B0 center was X `+0.005258 mm`, Y `-0.014941 mm`, Z
  `+0.002445 mm`, norm `0.016027 mm`, passing the `0.050 mm` gate. B+5 and B-5
  within-group closure norms were `0.002493 mm` and `0.014061 mm`.
- Using the opening/closing B0 mean as reference, rows 2-9 had RMS
  `0.031153 mm` and maximum `0.045463 mm`; the maximum was B+5/C-20, dominated
  by X `+0.044085 mm`. This passes the preferred `<0.100 mm` production-grid
  maximum and the core `<0.200 mm` gate without an advisory.
- The balanced odd-in-B half-difference was `0.008439 mm` at C+20 and
  `0.036167 mm` at C-20, mainly X. That C dependence does not identify a simple
  B-zero correction by itself; freeze it as S1 evidence for comparison with L
  and S2.
- Pass-2 U/V centering residual magnitudes were at most
  `0.004054/0.002526 mm`. Corrected directional diameters spanned
  `30.116026-30.280823 mm`; B+ mean U exceeded B- mean U by `0.116960 mm`.
  The broad program gates pass, but this remains strong orientation-dependent
  trigger/contact evidence rather than sphere-diameter accuracy.
- Rotary feedback/SSI errors were at most `0.000201 deg` for B and
  `0.004364 deg` for C. Logged linear following error was at most `0.001 mm`;
  all tool, TLO, correction, TCPC/TWP, SSI-valid, and schema checks pass.
- Stage B ended cleanly at B0/C0, interpreter-idle and clear above the sphere.
  Exact executed runner SHA-256:
  `712ff7ea3584f7e8aa122b006e5caf69628033602d0cf0dfe7ded465dde590af`.
  Pair CSV now contains 16 retained data rows and has SHA-256:
  `d67ad5bbac68f64e49ebccdfb73ab87ee0988ff59e9e4a04221a3ae4280fe5a5`.
- After Stage B, the runner was armed for S1 Stage C-low mode `17`, attempt `1`,
  with SHA-256
  `6e269b9d7f4a2814b066dac78be039156390bd1cc6ac1f468fce57e96915686b`.
  It passed static checks and a load-only selection with zero commanded-axis
  change and no LinuxCNC message before Stage C-low started.

## S1 Stage C-Low Sphere Attempt 1

- Mode `17`, leg `1`, attempt `1` started with the exact runner SHA-256
  `6e269b9d7f4a2814b066dac78be039156390bd1cc6ac1f468fce57e96915686b`.
  Before row 1, laser-cutter EMI caused an external hold during ordinary
  positioning. The operator turned the laser off; the subsequent live guard
  found every probe input clear before G38 motion.
- Rows 1-5 logged the canonical opening B0 C0/90/180/270/0 group. Sequence 5
  minus sequence 1 was X `-0.006073 mm`, Y `+0.006477 mm`, Z `+0.003670 mm`,
  norm `0.009607 mm`, passing the programmed `0.050 mm` review gate. Maximum
  accepted-pass U/V centering residual magnitude was `0.007088 mm`.
- Rows 6-10 completed the B+10 group. Sequence 10 minus sequence 6 was X
  `-0.007975 mm`, Y `+0.000654 mm`, Z `+0.000478 mm`, norm `0.008016 mm`.
  Rows 11-13 then logged B-10/C0, C90, and C180 normally.
- Intended sequence 14 at B-10/C270 completed pass 1 and made a valid pass-2 top
  contact. After the 5 mm top retract, the synchronized live guard sampled the
  raw wireless probe before its designed HAL release interval had elapsed and
  aborted at `2026-08-22T16:06:03+07:00` with `Paired sphere probe input is
  active before a probe move`. No sequence-14 row was logged. Raw, muxed, and
  motion inputs were clear immediately afterward; the machine was idle, in
  position, homed, and clear at the calculated top-clear point.
- Attempt 1 is retained as a canonical `13/20` partial and excluded from accepted
  paired fitting. The source CSV has 29 data rows plus its header, SHA-256
  `70ba9ef3748bc1f50188160831928cc0f49185690b5951d53563368fd8ab1972`.
  The exact partial evidence and executed runner are preserved in
  `calibration_runs/20260822_1529_S1_T3_mode17_attempt1_partial/`.
- The root cause is a software timing mismatch: queue synchronization completed
  the retract but did not wait for wireless release, while HAL intentionally
  ignores valid post-G38 release for `1.0 s`. The revised runner checks probe
  gates immediately after each contact retract, then requires two consecutive
  raw/mux clear samples `0.05 s` apart within a `1.0 s` post-retract timeout.
  Every pre-G38 live guard remains strict. Full attempt `2` was prepared and
  load-checked; no suffix was appended to attempt 1.
- Revised attempt-2 runner SHA-256:
  `9e370c91f49f0ca78d7cef1a5e3ccb3a472df1dd1afd2a899c452249c3580f49`.
  Unexecuted armed T3 ring verifier attempt `10` SHA-256:
  `a3f462f3f4d878de20687cfcf1e5ece09389788c2b815e8e38dac01a02d82cb7`.
  Current disarmed verifier SHA-256:
  `15ded0868408874749a74e0690989372482394ad94002367643010de848cdff5`.
  Attempt `10` was waived before Cycle Start, so it caused no ring motion and
  logged no row. Prepared mode-17 attempt 2 was subsequently superseded before
  measurement and is retired. Any future full restart requires attempt 3, a
  fresh reviewed B0/C0 sphere start, and full live preflight.
