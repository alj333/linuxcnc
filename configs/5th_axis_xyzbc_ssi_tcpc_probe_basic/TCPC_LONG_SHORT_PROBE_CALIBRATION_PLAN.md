# TCPC Long/Short Probe Calibration Plan

> Superseded operator order: the current next stage is campaign `2026082403`
> in `TCPC_RELOCATED_SPHERE_CAMPAIGN_2026082403.md`. Retain this file as prior
> campaign design and provenance; do not start its runners or mix its CSV data
> into the relocated-sphere campaign.

Status: historical campaign `2026082201` is paused after its completed ring,
S1/T3 Stage A, and S1/T3 Stage B work. Stage C-low attempt 1 remains an excluded
canonical `13/20` partial. Prepared attempt 2 was superseded before measurement,
its ID is retired, and any future mode-17 restart must use attempt 3. The active
legacy runner is disarmed. T3 `0.117658 mm` and T4 `0.154742 mm` remain frozen.

The current owner-directed work is separate campaign `2026082202`, documented
in `TCPC_POSITIVE_B_C45_BASELINE_PLAN.md`: T3 short then T4 long at B
`0/+5/+15/+30 deg` and safe C45 sectors. Do not use this historical S1-L-S2
plan as the current start order and do not mix the two campaign CSV files.

Latest runtime checkpoint:
`TCPC_CALIBRATION_RESUME_STATE.md`.

Applies only to:

- config: `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic`
- machine: real XYZBC SSI head-head machine
- comparison: T3 short wireless probe, T4 long wireless probe, then T3 short
  wireless probe again
- measurement artifacts: certified fixed 50 mm qualification ring and
  certified fixed 30 mm sphere
- TCPC state: current persistent production correction enabled

This is a measurement and decision plan. It does not authorize an immediate
geometry, correction-coefficient, home-zero, backlash, or tool-table change.

## Current Campaign Decision - 2026-08-22 +07

The certified ring remained fixed. The completed ring results establish
separate scalar lateral trigger offsets for the two physical probe assemblies:

```text
T3 short #3032 = 0.117658 mm
T4 long  #3032 = 0.154742 mm
```

T3 has two accepted verification rows under an explicit operator waiver of the
normal three-row minimum. T4 has three complete verification rows. T4's exact
executed program stopped under its original `0.005 mm` per-row gate, but its
complete logged set passes the later owner-approved `0.010 mm` machine-
capability contract. The original abort, selectors, and executed hash remain
historical facts; the capability review does not recast them as a clean run.

The machine is a steel-frame production CNC with known spindle wear and
position-dependent Z-axis error. Probe insertion/clocking, rail position,
directional trigger response, imperfect alignment, and B-axis zero may all
contribute. Under `0.010 mm` is a very good ring result. The purpose of the next
stage is to classify repeatable correctable terms versus mechanical uncertainty,
not to force all observed error into TCP coefficients.

At the supersession checkpoint, T3/H3 remained installed with TCPC active.
LinuxCNC was enabled, homed, idle, and at B0/C0 over the sphere. Mode-17
attempt 2 caused no axis/probe motion and logged no CSV row; it is not the
current selected measurement job. See the current resume checkpoint and
campaign `2026082202` procedure before any Cycle Start.

## Historical Operator Handoff State - 2026-08-21 +07

At this historical pre-campaign checkpoint there was no touch probe installed
in the CNC. It is retained as startup provenance and is superseded by campaign
`2026082201` above.

The owner/operator confirms that the CNC was fully operational before this
software-preparation check. The machine-off and unhomed state recorded below
was deliberate for the permitted load-only test and does not indicate a known
machine fault.

The real TCPC Probe Basic configuration was launched today only for load-only
verification. The final check used the exact prepared tree and loaded these
three files, one at a time, through LinuxCNC's `program_open` interface:

- `nc_files/calibration/50mm_ring_probe_qualify.ngc`
- `nc_files/calibration/50mm_ring_probe_verify.ngc`
- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`

All three loaded without an error-channel or UI parse error. The observed idle
state before, during, and after those loads was:

- machine power off and motion disabled
- `iocontrol.0.tool-number = 0`
- live motion, HALUI, and kinematics tool-length offsets all zero
- TCPC false and all TWP states false
- B and C SSI-invalid signals false

No joint was homed or jogged. No MDI command was issued, no G-code program was
started, and no machine or probe motion was requested. The interpreter stayed
idle and actual position remained unchanged while each file was loaded.
LinuxCNC was then shut down and the hardware/real-time stack unloaded. Probe
Basic did not terminate after Ctrl-C or SIGTERM during this scripted check and
had to be killed before the LinuxCNC wrapper could complete its otherwise clean
shutdown. This load-only check proves startup and file acceptance only; it is
not evidence that homing, tool state, probing, TCPC motion, clearances,
measurement quality, or calibration is accepted.

An earlier preparation launch displayed the intermittent startup real-time
delay warning already known to the owner/operator; the machine has remained
fully operational and the warning has not affected operation. The final
exact-tree shutdown reported zero latency excursions. Record the message as
known startup context, not as a calibration blocker. If a latency event is
ever accompanied by a control or motion fault, stop and investigate that event
before continuing. The configured program directory was not present, so
LinuxCNC used its fallback program location:

`/home/cnc5/mnt/cnc/5th axis`

This does not block explicit selection of the reviewed files, but record the
actual source path and hash in the manifest before any run.

At that historical checkpoint, the software artifacts were prepared for final
review and an operator-led machine session; they did not authorize motion.
Current ring and machine status is controlled by the current campaign decision
above and `TCPC_CAMPAIGN_2026082201.md`.

## Review Summary

The reviewed work spans the March through June 2026 head-head development and
the current August tool-table state:

1. March simulation established `headheadkins`, continuous TCP motion, TCPC
   entry/exit, and the initial TWP contract.
2. April real-machine SSI work qualified the 30 mm sphere workflow and produced
   the first B/C geometry. The original B-to-tool value represented the fixed
   T3 probe tip.
3. Late April rigid corrections improved the sphere map but could not explain
   the full C-dependent and high-B surface. Direct output SSI became the rotary
   position authority and B/C software backlash was returned to zero.
4. May short-probe harmonic and B/C-cross work produced a balanced diagnostic
   result of about `0.055446 mm RMS` and `0.113585 mm maximum` on accepted live
   rows. It met the core `<0.20 mm` target, not a guaranteed global `<0.10 mm`
   target. Richer fits showed held-out errors as large as roughly
   `0.22-0.45 mm`, so low training RMS was not treated as release evidence.
5. On May 7, the fixed T3-tip geometry was split into spindle-nose geometry plus
   live G43 tool length. That architecture is correct for more than one H
   length; the remaining empirical surface was still identified with T3 only.
6. May commissioning hardened TCPC entry/exit, servo response, probe gating,
   and toolsetter behavior. Real-machine TWP was disabled after a G68.2
   following-error/lost-home event. A corrected B-90/C90 investigation still
   reached roughly `0.98 mm`, with SSI following error near zero, reinforcing
   the decision to keep high-B frame/alignment work separate.
7. In June a loose B conical clamp was found and retorqued, the sphere moved,
   and fresh low-angle data established `b_ssi_zero.in1 = -176.1160`. Older
   sphere rows are not a comparable baseline. Remaining B-90 error was assigned
   to geometry/alignment/flex investigation, not another zero change.
8. The current T4/H4 row adds `100.800271 mm` beyond T3/H3. This is the first
   useful lever-arm separation for identifying length-proportional error.

The current startup uses the earlier persistent refined B/C-cross candidate.
The later balanced-final short-probe candidate was better on its recorded
short-only validation but remained diagnostic and was never promoted. There is
no documented decision supporting a baseline swap now, so the actual startup
state is frozen for the paired experiment.

Documentation authority for this stage is:

1. this plan and the current top plus June tail of this config's `README.md`
2. the May 7 current-state sections and final handoff in
   `../5th_axis_xyzbc_ssi_probe_basic/TCPC_FIT_NEXT_SCOPE.md`
3. `../5th_axis_xyzbc_ssi_probe_basic/TCPC_SHORT_PROBE_BALANCED_FINAL_REPORT.md`
   for the short-only result and explicit long/short next experiment
4. `../5th_axis_xyzbc_ssi_probe_basic/CALIBRATION_WORKSHEET.md` and
   `SESSION_NOTES.md` as raw chronology, not current operating instructions

Older simulation bring-up, 20 mm sphere, fixed-tip, correction-off, backlash,
and TWP sequences remain useful history only. The `Superseded Guidance`
section below defines the conflicts explicitly.

## Non-Negotiable Controls

1. Do not change any kinematic coefficient, fitted correction coefficient,
   B/C SSI zero, joint scale, backlash value, WCS, sphere position, or ring
   position before or during the complete short-long-short baseline.
2. Keep `headheadkins.sim-bharm-enable = 1` for every paired sphere run. This
   historical pin name is the enable for the current persistent production
   correction.
3. Do not use TWP. Do not issue `G68.2`. TWP must be off and undefined for the
   entire session.
4. Keep B and C LinuxCNC backlash at `0.0`. Direct SSI feedback is at the
   rotary output. The old nonzero software backlash values created TCP error.
5. Apply `G43 Hn` before `G43.4`. Never change or clear tool length while TCPC
   is active. Return to the saved B0/C0 entry orientation, issue `G49.1`, and
   only then issue `G49`.
6. Treat every result collected before the June 2026 B-shaft-clamp repair and
   sphere move as historical context only. It is not comparable paired-length
   data. No historical row, including a later good short-probe row, replaces a
   fresh short run in the current mechanical and thermal state.
7. Keep B90 and other high-B investigation out of this baseline. High-B
   geometry, stiffness, and alignment are a separate project after the
   production-envelope comparison is accepted.
8. Use no cutting motion. Keep the spindle stopped. A trained operator must
   stay at the controls with feed hold and emergency stop available.
9. Do not weaken a check or substitute a fallback value to keep a run going.
   An invalid or incomplete run remains logged as invalid and is restarted
   from a fresh B0/C0 reference after the cause is corrected.

## Frozen Starting State

Record the actual Git commit, working-tree diff, file hashes, and live values at
the start of the session. The expected starting state is:

| Item | Expected value |
| --- | ---: |
| B SSI zero input | `b_ssi_zero.in1 = -176.1160` |
| C SSI zero input | `c_ssi_zero.in1 = -180.8703` |
| nominal C-to-B X | `0.010934` mm |
| nominal C-to-B Y | `0.0` mm |
| nominal C-to-B Z | `-270.0` mm |
| nominal B-to-spindle-nose X | `-0.668710` mm |
| nominal B-to-spindle-nose Y | `-26.721365` mm |
| nominal B-to-spindle-nose Z | `-180.373272` mm |
| calibrated C-to-B X | `0.035886006` mm |
| calibrated C-to-B Y | `0.009526306` mm |
| calibrated C-to-B Z | `0.0` mm |
| calibrated B-to-tool Z | `0.815000` mm |
| kinematic B zero offset | `0.0` deg |
| kinematic C zero offset | `-0.024500` deg |
| fitted correction enable | `headheadkins.sim-bharm-enable = 1` |
| B joint backlash | `0.0` deg |
| C joint backlash | `0.0` deg |
| TWP | off and undefined |
| TCPC before tool setup | off |

The full harmonic and B/C cross-term baseline is the exact content of
`5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` at the recorded commit and hash. Do
not transcribe or edit individual fitted terms during the session.

The loose conical B-shaft clamp was retorqued before the current B SSI zero was
established. Verify its witness marks, fastener condition, and agreed torque
control before warming the machine. If there is any evidence of movement, stop
and resolve the mechanics before collecting data.

## Current Model Boundary

The active rigid model is already tool-length aware. It combines the
B-to-spindle-nose geometry with live `motion.tooloffset.*`, then rotates that
local vector through B and C. T3/H3 therefore reconstructs the old short-probe
tip without storing that tip length in fixed geometry, and T4/H4 receives its
own longer lever arm.

The fitted B/C correction is different: it is an additive XYZ surface in
millimetres and does not scale with active H length. It was learned entirely
from the short probe. A true machine-fixed residual can remain additive, but a
spindle/tool-axis or rotary-axis angular error absorbed by that surface will be
wrong away from the T3 lever arm.

`headheadkins` has C-axis and B-axis tilt inputs, currently all zero, but the
single-length history could not identify them independently. The local tool
axis itself is still fixed at `(0, 0, -1)`; there is no independent common
spindle/tool-axis tilt input that creates an X/Y slope proportional to live Z
tool length. Per-tool X/Y table offsets can represent measured lateral tip
offsets, but the current Probe Basic table exposes only T/Z/D/R and both probe
rows contain only Z/D. Do not add tilt pins or synthetic X/Y offsets before the
paired vectors show which physical term is identifiable.

The dual-length observation is not automatically a pure lever-arm observation.
At one fixed artifact height, T3 and T4 place the Z carriage approximately
`100.800271 mm` apart. Their difference therefore couples active tool length to
Z-rail straightness/pitch/Abbe error. A changed physical probe assembly also
couples length to spindle/holder seating and directional trigger behavior. The
current ring-center difference of X `-0.092066 mm`, Y `-0.066641 mm` cannot be
assigned uniquely to any one of those terms.

Use these identification boundaries throughout the campaign:

- A per-probe scalar ring offset is correctable when its averaged diameter and
  repeatability meet the ring contract.
- A constant center shift or X/Y diameter split is diagnostic; scalar `#3032`
  cannot correct it.
- A deterministic holder-clock effect is eligible for a per-tool lateral
  correction only if the insertion is mechanically keyed and independently
  repeatable. Random seating is an uncertainty/mechanical issue.
- `L - 0.5*(S1 + S2)` at the sphere is an effective length/setup differential.
  It still contains the single T4 seating and the coupled Z-rail position.
- A B-zero or rigid tilt is eligible for later fitting only if one common
  low-dimensional term predicts both lengths, both B signs and C rotation, and
  improves held-out poses. Physical spindle/B-zero attribution may still need
  independent metrology.
- Z-rail error requires the same probe assembly at two stable artifact heights,
  or independent rail/spindle metrology. Do not absorb a one-height long/short
  difference into rotary TCP coefficients.

## Probe Identity and Length Separation

The shared tool table currently identifies the two probes as follows:

| Role | Tool/H | Pocket | Table Z | Diameter | Table remark |
| --- | --- | ---: | ---: | ---: | --- |
| short | T3/H3 | P1 | `128.606729` mm | `6.000000` mm | `Wireless PROBE` |
| long | T4/H4 | P0 | `229.407000` mm | `6.000000` mm | `Wireless PROBE_150` |

The table-length separation is:

```text
229.407000 - 128.606729 = 100.800271 mm
```

This exact `100.800271 mm` separation is the denominator for the first
length-sensitivity comparison. Do not substitute nominal stylus length.

Before accepting these identities:

- Mark or photograph the physical probe body, stylus, extension, ball, holder,
  and seating arrangement assigned to T3 and T4.
- Record the serial numbers or durable physical labels.
- Record how each table Z value was established, the date, repeated
  measurements, range, and measurement reference.
- Confirm that both balls really are 6 mm. Record the measured ball diameter if
  available.
- Resolve the tool-table pocket difference deliberately. Do not assume P0 or P1
  identifies the physical probe.
- Treat T4/H4 `229.407000` as provisional until its measurement provenance and
  live application are verified.

The historical T3 probe calibration offset `0.134533` is superseded for this
campaign. The frozen values are T3 `0.117658 mm` and T4 `0.154742 mm`; their
`+0.037084 mm` difference is expected assembly-specific lateral pre-travel and
is not an axial tool-length error.

## Guarded Runner

The paired-length runner is:

```text
nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc
```

Its paired modes are separate from historical mode 8 and the high-B candidate
modes. Before loading each stage, set and review only this selector block:

```ngc
#711 = 15.0   (stage mode: 15=A, 16=B, 17=C-low, 18=C)
#715 = 0.0    (campaign ID: set to YYYYMMDDNN, NN=session number)
#716 = 0.0    (leg: 1=S1 short, 2=L long, 3=S2 short)
#717 = -1.0   (this probe's accepted ring-qualified #3032 value)
#727 = 0.0    (attempt: 1, then increment for a retained/restarted stage)
```

The sentinel defaults abort without motion. Paired modes enforce live T3/T4
identity, exact H3/H4 Z length, all three live Z-TLO views, zero non-Z motion
tool offsets, 6 mm diameter,
explicit ring offset, correction-on state, TCPC-on state, TWP-clear state,
valid B/C SSI feedback, and B0/C0 start. They do not use the historical T3,
diameter, or calibration-offset fallbacks.

After the selector and live-state guards, every paired program invocation
enforces an `M0` immediately before its selected stage can move. At that stop,
the operator must read back all five selectors, verify the physical probe and
live H state, and repeat the sphere/start/body-clearance check before Cycle
Start. Actual XYZ is frozen across every hold, and the initial stop also
requires physical B/C to remain at B0/C0. The live guard runs again after this
initial stop before the first pose, and it runs before later index/probe motion
so a state change while paused is not silently accepted.

The runner also enforces one inspection `M0` inside every selected stage and
every S1/L/S2 leg:

- mode 15: after the complete opening B0 C-quadrant group
- mode 16: after the B+5 C0/+20/-20/C0 group, before B-5
- modes 17 and 18: after the opening B0 C-quadrant group, before tilted B

At each hold, inspect the accepted rows, closure/diameter/probe behavior, and
remaining body/post clearances before resuming. The general legacy selector
`#704 = 0` means there is still no pause before every individual pose; the
explicit stage-group holds above are the enforced review boundaries.

Each live guard begins with `M66 E0 L0` to drain queued retract or index motion
before reading HAL, WCS, and joint state. The accepted-pose capture has another
synchronized live guard after the final side retract, so endpoint and joint
fields cannot be sampled while that retract is still queued. Direct C SSI is
opposite joint-C polarity and is checked with the wrapped equivalent of
`C_ssi + C_cmd`; B SSI is same-polarity and remains checked as
`B_ssi - B_cmd`.

| Mode | Released paired stage |
| ---: | --- |
| `15` | Stage A, B0 C-quadrant reference |
| `16` | Stage B, B+/-5 and C+/-20 trim envelope |
| `17` | Stage C-low, B+/-10 C quadrants |
| `18` | Stage C, B+/-30 C quadrants |

Every accepted paired pose writes to the isolated schema in
`tcpc-long-short-pair-results.csv`, including campaign, leg, stage, monotonic
sample sequence, live tool, TLO, probe offset, correction/TCPC/TWP/SSI state,
center/diameter QA, rotary command/feedback, accepted-pass absolute XYZ, and
X/Y/Z joint motor command/feedback/following error. Paired rows are kept out of
the historical single-length detail CSV files. The linear fields locate every
measurement on the rails and support correlation; they do not alone identify a
rail-error model. The runner returns B and C to zero and deliberately leaves
TCPC/tool length active for the controlled exit sequence.

Do not use `tcpc_symmetric_pose_vector_sphere_auto.ngc`,
`tcpc_expanded_pose_vector_sphere_auto.ngc`, the untracked C0-only copy, or
historical resume programs for this paired campaign. No calibration motion is
released until the exact selector values, runner diff/hash, clearance dry run,
and machine preflight have been reviewed.

## Session Prerequisites

Complete every safety, state, identity, geometry, and clearance item before
motion. Complete the entire list before accepting the final dataset or changing
the machine model. Certificate metadata may remain pending during diagnostic
collection only under the explicit campaign disposition below; it remains a
hard final-acceptance gate.

- [ ] The machine is mechanically complete and no production work will alter
      the head, probe, ring, sphere, or table during the session.
- [ ] The B shaft clamp and other rotary-head fasteners show no movement.
- [ ] The 50 mm ring and 30 mm sphere are clean, rigid, undamaged, and cannot
      move between S1, L, and S2.
- [ ] The certificate ID, calibrated dimension, uncertainty, and reference
      temperature are copied into the run manifest for both certified
      artifacts. The ring is stamped `50.001 mm`, and the prepared ring
      routines use that value. The sphere routines use `30.000 mm`; if its full
      certificate value is materially different, the affected sphere rows
      cannot support a model or calibration decision until constants,
      acceptance limits, and the need to rerun them have been reviewed.
- [ ] Sphere/post collision clearance has been checked for both probe bodies,
      holders, and all approved poses, not only for the probe tip.
- [ ] The wireless probe has a good battery, clean seating contacts, stable
      receiver indication, and no multi-flash/faint-flicker fault.
- [ ] Laser cutters, welders, and other observed EMI sources are inactive for
      the entire probe program. Any suspected false trigger during an active
      `G38` move rejects that attempt; do not resume it as accepted data.
- [ ] Raw `t_probe-in` and `probe-mux` are idle with the probe clear, and each
      changes cleanly on a supervised hand trip.
- [ ] All five joints home normally and B/C SSI channels report valid data.
- [ ] B and C command/feedback agree at zero within the established no-motion
      verification tolerance.
- [ ] LinuxCNC has been restarted after any compiled, remap, HAL, or INI
      build/change. Reviewed NGC/logger-only revisions may be loaded directly.
- [ ] The exact config, tool table, HAL, INI, runner, variables file, Git commit,
      working-tree diff, and hashes are captured in the run manifest.
- [ ] The active calibration WCS and its offsets are recorded. Its B/C offsets
      and XY rotation are zero; G52 and G92 are disabled with all offsets zero.
      G55 remains untouched.
- [ ] Room, frame, head, and spindle temperatures are recorded at the start.
- [ ] The machine is warmed by the established repeatable procedure. Record the
      procedure and elapsed time; do not invent a new warm-up during the run.
- [ ] Feed override begins low for the first dry movement and first probe cycle.
- [ ] Output files and row boundaries have been isolated as described below.

Campaign `2026082201` disposition: the owner/operator identified both artifacts
as certified, supplied the ring's stamped `50.001 mm` value, identified the
sphere as certified 30 mm, and authorized diagnostic sphere collection using
the nominal `30.000 mm` constant. Full certificate IDs, calibrated values,
uncertainties, and reference temperatures remain pending. This is an explicit
metadata waiver for diagnostic collection only; it does not permit a fit,
coefficient change, calibration acceptance, or production release.

## Independent Ring Qualification

Qualify T3 and T4 independently before the sphere sequence. Perform ring work
with TCPC off, TWP off, B0/C0, the spindle stopped, and the correct active tool
length. Use the recorded WCS with its B/C offsets and XY rotation zero, and keep
G52/G92 disabled with all offsets zero. Use:

- `nc_files/calibration/50mm_ring_probe_qualify.ngc`
- `nc_files/calibration/50mm_ring_probe_verify.ngc`

Both wrappers use reviewed selectors and abort before motion when their
selectors are left at sentinel values. The qualification wrapper now includes
the required verification set. For qualification set:

```ngc
#715 = 2026082101.0  (campaign ID YYYYMMDDNN; example only)
#727 = 1.0           (base ID reserved for qualification plus three verifications)
```

Qualification intentionally calculates and replaces live `#3032`. It does not
take `#717` as input. It logs `cycle_kind=1` with attempt `#727`, lifts an
additional `5 mm`, and uses protected no-contact positioning to establish a
calculated left-wall start from the measured center and the certified ring
diameter. A second mandatory `M0` then requires review of the newly calculated
`#3032`. Resuming from that hold freezes the candidate into `#717` and attempts
three verification rounds automatically, logged as `cycle_kind=2` with attempt
IDs `#727+1`, `#727+2`, and `#727+3`. The first failed diameter or accumulated
center-range gate is logged and aborts at the measured center and top clearance
before any automatic wall repositioning. A passing set has exactly three
passing verification rows; a failed set may contain only a completed prefix
and is rejected.

The base therefore reserves four consecutive IDs. If any part of an integrated
set is interrupted, retain its rows as diagnostic evidence and advance the
next qualification base by four; do not reuse or overlap retained IDs.

Use the standalone verification wrapper for later probe installations,
additional evidence, or a post-interruption check. For every such set:

```ngc
#715 = 2026082101.0  (same campaign ID; example only)
#717 = -1.0          (replace with this physical probe's frozen offset)
#727 = 1.0           (positive integral verification attempt; increment repeats)
```

The standalone verification wrapper first requires live `#3032` to match
`#717` within `0.0005 mm`; `#717` is not a fallback for an unknown live value.
It has one mandatory `M0`. The integrated qualifier has an initial pre-motion
`M0` and a second candidate-review `M0` before the automatic verification set.
Cycle Start after either stop authorizes its following probe phase, so verify
probe identity, G43 state, ring/start position, and all body/holder clearances
again at the stop. After a hold, the wrappers reject changes to selectors,
frozen offset where applicable, live `#3032`, actual XYZ, active WCS, or any
active WCS entry. They then rewrite and validate the fixed
feed/clearance/measurement-only contract before motion.

For the 6 mm probe ball, start with the ball center `3-4 mm` onto the solid
left wall from the bore edge, approximately on the ring Y centerline, and no
more than `15 mm` above the top. The pinned wrappers then move `+X 10 mm`,
placing the ball center `6-7 mm` inside the bore before the Z descent. The
earlier `+X 3 mm` setup was rejected during campaign `2026082201` attempt 1
because it did not clear the ball into the bore.

The wrappers call only the pinned `tcpc_ring_*` stack in this config's local
subroutine directory. This avoids mixing incompatible global-reading and
positional-argument Probe Basic variants found elsewhere in the configured
search path. Its no-contact `G38.3` positioning helper checks `#5070` after
every move; unexpected contact returns along that single known axis to the
captured pre-move coordinate, synchronizes motion, clears legacy outputs, and
aborts.

Every completed ring cycle appends to the dedicated file:

```text
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-long-short-ring-results.csv
```

`cycle_kind=1` identifies qualification and `cycle_kind=2` verification. The
row records campaign/attempt, live tool and TLO values, offset before/after,
X/Y/average diameter, measured X/Y center, WCS before/after, and the three live
Z-offset views.
Preserve and hash the row interval in the external run manifest.

For each physical assembly:

1. Load the probe through the normal manual tool-change workflow.
2. Set Probe Basic probe tool number to the actual tool, update the probe
   parameters, and verify live tool identity before motion.
3. Apply the matching `G43 Hn` and verify all live TLO sources.
4. Run the integrated qualification cycle and record its proposed calibration
   offset at the second mandatory `M0`.
5. Resume only after reviewing the candidate and the protected calculated wall
   start. The wrapper then freezes that candidate and runs three verification
   cycles without reseating or manual repositioning.
6. Record every measured diameter, center, offset, feed, raw probe state, room
   temperature, and head temperature.
7. Accept only when every verification average is within `0.010 mm` of the
   stamped `50.001 mm`, the three-row averaged-diameter range is no more than
   `0.010 mm`, each X/Y center range is no more than `0.010 mm`, and there is no
   false trip or frozen-state violation. Record X/Y diameter split and
   directional trend as diagnostic evidence; they are not an automatic scalar-
   offset rejection unless they are nonrepeatable or indicate a probe fault.
8. Record the final offset separately as `T3_CAL_OFFSET` or `T4_CAL_OFFSET`.

After both probes have been qualified, freeze both calibration offsets. Do not
recalculate or edit either offset during the sphere sequence. On every later
probe installation, perform a ring verification. If it does not reproduce the
frozen qualification, reject the current short-long-short sequence and start a
new one after correcting seating, stylus, or probe behavior.

For campaign `2026082201`, T3's two verification rows are accepted by explicit
operator waiver of the usual three-row minimum. T4 attempts 6-8 pass the
reviewed contract with maximum average error `0.005417 mm`, averaged-diameter
range `0.008750 mm`, X-center range `0.004850 mm`, and Y-center range
`0.004101 mm`. No base-9 requalification is required solely because the
executed file used the earlier `0.005 mm` gate.

### Installation and Clocking Evidence

The sphere campaign is the primary tool for resolving the center-offset vector
versus B/C pose. Before each S1, L, or S2 leg, use one standalone frozen-offset
ring verification to confirm the current installation and record its measured
center, attempt ID, holder/spindle clock mark, temperature, and installation ID
in the manifest. Do not recalculate `#3032` during these checks.

S2 closing back toward S1 bounds short-probe session drift/reseating. The sphere
C quadrants show whether the long-minus-short center component rotates with the
head; balanced `+B/-B` poses distinguish symmetric center terms from B-sign
terms. This makes the sphere map more informative than the B0 ring center alone.

If the installation checks or S1/L/S2 closures show material ambiguity, run a
separate clocking diagnostic without changing the frozen offsets:
`0 deg -> 90 deg -> 180 deg -> repeat 0 deg`, with two ring verifies per seating
where controlled clocking is practical. Repeat-0 bounds random reseating; the
0/180 half-difference estimates rotating eccentricity and the half-sum estimates
the machine-fixed center at that rail height. A second long insertion or a
second complete S-L-S campaign is needed before treating a long-only shift as a
stable tool correction.

The final S2 T3 installation must use the same frozen T3 offset as S1. A changed
offset would confound length error with probe reseating/calibration error.

Only the qualification cycle may replace `#3032`, and only before starting the
paired baseline. For verification and sphere work, load the matching frozen
offset deliberately into live `#3032`, enter the same value in selector
`#717`, and verify both values against the manifest. T3/S1 and T3/S2 must use
one identical T3 value; T4/L must use its separately qualified T4 value. Never
copy the historical T3 value or either probe's value into the other probe by
default.

The dedicated campaign-2026082202 positive-B T3/T4 runners implement that
deliberate reload internally: only after the exact live-tool and TLO guards
pass, each writes its already-qualified selector `#717` into `#3032`, reads it
back, and later aborts on any change. They do not calculate or replace the
accepted value. This exception avoids a separate remote MDI parameter entry;
it does not apply to generic or historical paired runners.

## Live Tool and TCPC Preflight

Probe Basic display state is not authoritative. A prior run showed T3 in the UI
while live `motion.tooloffset.z` still contained the T97 length. Interpreter
variables `#5400`, `#5410`, and `#<_current_tool>` can also be zero or stale.

For every S1, L, and S2 stage, record a live snapshot immediately before
`G43.4` and immediately after TCPC entry.

| Live item | T3 expected | T4 expected |
| --- | ---: | ---: |
| `iocontrol.0.tool-number` | `3` | `4` |
| `halui.tool.diameter` | `6.000000` | `6.000000` |
| `motion.tooloffset.x` | `0.0` | `0.0` |
| `motion.tooloffset.y` | `0.0` | `0.0` |
| `motion.tooloffset.z` | `128.606729` | `229.407000` |
| `motion.tooloffset.a/b/c/u/v/w` | all `0.0` | all `0.0` |
| `halui.tool.length_offset.z` | `128.606729` | `229.407000` |
| `headheadkins.active-tool-offset.z` | `128.606729` | `229.407000` |
| loaded probe calibration offset | `0.117658` | `0.154742` |
| `headheadkins.sim-bharm-enable` | `1` | `1` |

The three Z TLO values must agree with the expected table value within
`0.002 mm`, and every non-Z motion tool offset must be within `0.002` of zero.
A UI row, tool graphic, or interpreter parameter is not a substitute for this
check.

Before `G43.4`, also require:

- `headheadtwp.tcpc_enabled = 0`
- `headheadtwp.active = 0`
- `headheadtwp.motion_enabled = 0`
- `headheadtwp.valid = 0`
- B command and feedback angular-equivalent to `0.0000` within `0.005 deg`
- C command and feedback angular-equivalent to `0.0000` within `0.005 deg`
- `b-ssi-invalid = 0` and `c-ssi-invalid = 0`
- `t_probe-in = 0`, `probe-mux = 0`, and `motion.probe-input = 0` with the probe
  clear
- `motion.digital-out-00 = 0` and `motion.digital-out-01 = 0` outside a probe
  move
- all joints homed and machine enabled
- G52/G92 disabled with all offsets zero, the recorded WCS active, and that
  WCS's B/C offsets and XY rotation zero

Use the following state order from a verified collision-clear position:

```ngc
Tn M6
G43 Hn
G0 B0 C0
(record and approve live preflight)
G43.4
(record and approve post-entry snapshot)
```

After entry require `headheadtwp.tcpc_enabled = 1`, with TWP `active`,
`motion_enabled`, and `valid` still all zero. Stop if TCPC entry causes an
unexpected position or joint discontinuity.

## Short-Long-Short Order

The required order is:

1. `S1`: T3/H3 short probe, current correction on.
2. `L`: T4/H4 long probe, current correction on.
3. `S2`: T3/H3 short probe repeated, current correction on.

Do not change the sphere, WCS, offsets, feeds, pose order, approach directions,
probe algorithms, software, HAL, INI, correction state, or rotary zeros between
these runs. Change only the documented physical probe assembly, T/H state, and
the matching frozen probe calibration offset.

The guarded runner snapshots the active WCS and all ten of its coordinate/XY
rotation entries before the first `M0`. Its live guard rejects a WCS change,
any offset change, nonzero active-WCS B/C offset or XY rotation, or any G52/G92
state before a rotary index or probing move.

For a tool change:

1. Finish the current stage at the saved B0/C0 entry orientation.
2. Move to a verified linear clearance while TCPC remains active.
3. Issue `G49.1` at B0/C0 and verify TCPC is off.
4. Issue `G49` and verify all active TLO components are zero.
5. Use the normal manual tool-change process.
6. Perform the required ring verification for the newly installed assembly.
7. Apply the matching H and frozen calibration offset.
8. Repeat the full live preflight before TCPC entry.

Run each tool through the authorized stage prefix without interleaving tools.
The first center-map pass is exactly:

| Order | Leg/tool | `#716` | `#717` | Modes (`#711`) |
| ---: | --- | ---: | ---: | --- |
| 1 | S1 T3/H3 | `1` | `0.117658` | `15`, then `16`, then `17` |
| 2 | L T4/H4 | `2` | `0.154742` | `15`, then `16`, then `17` |
| 3 | S2 T3/H3 | `3` | `0.117658` | `15`, then `16`, then `17` |

Use campaign `#715 = 2026082201` and first-attempt `#727 = 1` for each distinct
leg/stage; increment only when retaining and restarting that same leg/stage.
Mode 18 is not part of this first pass and requires review of the mode-17
center map. S1 may advance after its own preceding stage passes. L may advance
only after the same S1 stage is accepted and its own preceding stage passes.
S2 repeats exactly the stages completed by L. If L is stopped early, run S2
only through the same completed stage. Do not expose either tool to a wider
stage merely to complete a table.

## Staged Pose Grid

Every pose uses two-pass vector sphere measurement in the tool-local U/V/W
frame. Start each run at B0/C0 with the tip 4 to 5 mm clear of the sphere. The
top search is bounded to `7 mm`, leaving only `2-3 mm` miss overtravel; do not
start higher and rely on extra probe travel. Use the same slow probe feed and
controlled rotary feed for every tool.

For every B group:

- start and finish at C0
- move B only from C0 and a verified linear/tool-body clearance
- do not use a combined diagonal B/C transition
- obtain a fresh B0 closure group before moving to the next stage
- use the enforced first-group `M0` in every S1, T4/L, and S2 stage to inspect
  the accepted rows and clearances before resuming

### Stage A: B0 and C-Axis Reference

Required order:

```text
B0 C0 opening
B0 C90
B0 C180
B0 C270
B0 C0 closing
```

This stage establishes C-only behavior, closure, probe health, and collision
clearance before any B tilt. Compare the absolute L center with the bracketed
S1/S2 center at each C quadrant. A component that rotates with C is different
evidence from a component that stays fixed in machine XYZ.

### Stage B: Proven Production Trim Envelope

Required order:

```text
B0 C0 opening
B+5 C0 guard
B+5 C+20
B+5 C-20
B+5 C0 guard
B-5 C0 guard
B-5 C+20
B-5 C-20
B-5 C0 guard
B0 C0 closing
```

This is the previously verified small-angle production envelope. It is the
minimum required T3/T4 production-state comparison. Its balanced B+5/B-5
groups expose the sign/parity needed to test an effective B-zero or rotary-
center hypothesis instead of inferring one from a B0 ring center.

### Stage C: Moderate Calibration Grid

For S1, run this stage only after its Stages A and B pass. For L, run it only
after S1 Stage C is accepted and L Stages A and B pass. S2 repeats it only when
L completed it. This is a calibration diagnostic, not an expansion of the
released production envelope.

Mode 17 groups:

```text
B0:   C0, C90, C180, C270, C0
B+10: C0, C90, C180, C270, C0
B-10: C0, C90, C180, C270, C0
B0:   C0, C90, C180, C270, C0 closure
```

Mode 17 adds enough B lever arm and C rotation to map the effective center
offset while remaining below the first B+/-30 diagnostic. Analyze its absolute
long-minus-bracketed-short center vectors and its per-leg B0-referenced
residuals as separate quantities.

Review mode 17 before mode 18. Mode 18 groups:

```text
B0:   C0, C90, C180, C270, C0
B+30: C0, C90, C180, C270, C0
B-30: C0, C90, C180, C270, C0
B0:   C0, C90, C180, C270, C0 final closure
```

Do not extend this sequence to B+/-50, B+/-60, or B+/-90 during the paired
baseline. Do not add C45/C225 paths during the first long-probe study. Negative
B with C45 has a known sphere-post risk in older expanded testing.

## Per-Pose and Per-Stage Gates

Stop the current stage immediately on any of the following:

- wrong live tool, length, diameter, or calibration offset
- fitted correction enable not equal to 1
- any TWP state present
- SSI invalid, following-error event, servo fault, or lost home
- wireless probe fault, double indication, false trip, or failure to release
- pass-1 U or V center correction greater than `2.0 mm`
- pass-1 corrected U or V diameter outside `29.9 to 30.5 mm`
- pass-2 U or V centering residual greater than `0.10 mm`
- pass-2 corrected U or V diameter outside `29.9 to 30.5 mm`
- unexpected holder, probe body, stylus, post, ring, or sphere clearance
- opening-to-closing B0 center-vector drift greater than `0.05 mm`

The `0.05 mm` closure gate is a data-quality limit, not the machine TCPC
accuracy claim. Prior warm-session drift was of similar size; a larger closure
means length effects cannot be separated reliably without repeating or
explicitly modeling the changed state.

At every gate, record the reason, pose, current machine state, output row range,
and whether the data is invalid or diagnostic-only. Never delete an aborted
run.

## Run Metadata and Log Isolation

Create one run directory before machine motion, using a unique local timestamp
and session ID, for example:

```text
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/
  20260821_HHMM_T3_T4_T3/
```

Do not truncate or overwrite historical CSV files. The guarded runner writes
only paired accepted rows to:

```text
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-long-short-pair-results.csv
```

`campaign_id`, `leg_id`, `stage_mode`, `attempt_id`, and `sample_seq` identify
every row and allow missing, duplicate, or reordered stages to be rejected.
Increment `attempt_id` before restarting an aborted leg/stage; never reuse an
attempt number or delete its partial rows. The runner does not supply
timestamps, file hashes, temperatures, physical probe identity, or operator
notes, so the external manifest remains mandatory.

Each paired row also records accepted-pass absolute XYZ; joint 0/1/2 motor
command and feedback; and logged `feedback - command` following error. The
analyzer rejects a following-error field that does not agree with the logged
command/feedback after CSV rounding. These measurements expose the carriage
position and live tracking state for correlation. They are not an independent
measurement of rail straightness.

The ring wrappers append their separate qualification/verification evidence
to `tcpc-long-short-ring-results.csv`. Preserve and hash its before/after row
intervals in the same run directory; do not mix ring rows into the paired
sphere CSV.

For every stage:

1. Record the line count and hash of every append-only source before a stage.
2. Record the line count and hash immediately after the stage.
3. Extract exactly that new row interval into a uniquely named stage file if a
   standalone evidence file is needed.
4. Verify the extracted first/last poses and row count against the stage plan.
5. Mark partial or aborted intervals clearly and exclude them from accepted
   analysis.

Use unambiguous names such as:

```text
S1_T3_stage_A_results.csv
S1_T3_stage_B_results.csv
S1_T3_stage_C_results.csv
S1_T3_stage_C_low_results.csv
L_T4_stage_A_results.csv
L_T4_stage_B_results.csv
L_T4_stage_C_results.csv
L_T4_stage_C_low_results.csv
S2_T3_stage_A_results.csv
S2_T3_stage_B_results.csv
S2_T3_stage_C_results.csv
S2_T3_stage_C_low_results.csv
```

The manifest must contain, for every stage:

| Field | Required record |
| --- | --- |
| session/stage | unique run ID, S1/L/S2, A/B/C |
| timing | local start/end time and elapsed time |
| operator | name and observer, if present |
| software | Git commit, dirty diff summary, LinuxCNC build |
| files | hashes of INI, HAL, tool table, variables, runner |
| mechanics | B-clamp witness check, sphere/ring IDs and condition |
| environment | room, frame/head, and spindle temperature |
| warm-up | exact procedure and elapsed time |
| coordinates | active WCS and numeric offsets, G52/G92 state |
| probe | physical ID, body, extension, stylus, ball, seating/install ID, clock mark |
| tool state | expected and live T/H, table Z, diameter, pocket |
| calibration | frozen probe offset and ring verification results |
| TCPC | entry/exit state and `sim-bharm-enable` value |
| TWP | valid/active/motion state, all required zero |
| rotary | B/C command, feedback, SSI state, zero values |
| probing | feeds, clearances, raw input idle/trip check |
| logs | source and isolated files, start/end row numbers |
| outcome | accepted, diagnostic-only, aborted, and reason |

## Analysis Method

Create one isolated campaign CSV with the exact header and retained source-row
order from the append-only paired log, including clearly identified partial
attempts. Do not sort it by pose or stage. From the repository root, run the
analyzer with an already-created run directory:

```bash
RUN_DIR="configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260821_HHMM_T3_T4_T3"
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_long_short_pair.py \
  "$RUN_DIR/tcpc-long-short-pair-campaign.csv" \
  --output "$RUN_DIR/tcpc-long-short-pair-derived.csv"
```

Its internal synthetic checks can be run separately with:

```bash
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_long_short_pair.py \
  --self-test
```

The analyzer validates the CSV schema, live-state fields captured in each row,
linear joint command/feedback/following-error consistency, canonical
S1-then-L-then-S2/stage/sample order, retained attempt selection, pose
alignment, per-row probe QA, and the paired vector calculations it reports.
Exit `0` means those logged-data acceptance gates passed; exit `1`
means a live-state or acceptance gate failed; exit `2` means the input, schema,
sequence, or I/O was invalid. Exit `0` does not validate the external manifest,
ring qualification, physical probe identity/seating, file hashes, mechanical
inspection, temperature/warm-up history, artifact movement, collision
clearance, or what occurred between logged rows. Those remain manual dataset
acceptance gates. Analyzer output is descriptive evidence, not a coefficient
recommendation or production release.

Use accepted pass-2 sphere centers only. Preserve X, Y, and Z vector components;
do not reduce the study to scalar RMS before diagnosing direction and sign.

For each aligned pose, report both:

```text
effective_center_offset = center_L - 0.5 * (center_S1 + center_S2)
pose_residual_difference = residual_L - 0.5 * (residual_S1 + residual_S2)
```

The first is the absolute center-offset map requested from the dual-length
experiment. The second removes each leg's B0 reference and isolates how that
offset changes with B/C pose. A repeatable rigid transform may be correctable;
the absolute map alone does not establish its mechanical cause.

Classify the observed pattern before fitting anything:

| Observed repeatable pattern | First interpretation | Possible later action |
| --- | --- | --- |
| nearly constant in machine XYZ across B/C | installation or rail-position reference shift | retain as reference/uncertainty; do not put it in rotary TCP |
| rotates with C as a tool-local lateral vector | probe/holder/spindle eccentricity | keyed, reseat-stable per-tool X/Y candidate |
| changes with B sign and rotates consistently through C | effective B-zero, B-center, or tool-axis angular term | compare nested rigid models on held-out poses |
| common to T3 and T4 after their own B0 references | machine-fixed rotary/additive residual | review base geometry or existing correction surface |
| scales with the `100.800271 mm` length difference | candidate angular/lever-arm term | validate against reseating and Z-rail alternatives first |
| changes with joint-2 position but not rotary parity | Z-rail/Abbe nuisance candidate | crossed-height or independent rail metrology |

Only the repeatable model that predicts both lengths and held-out poses is a
calibration candidate. Nonrepeatable insertion, hysteresis, flex, or rail
behavior remains a mechanical uncertainty envelope.

Do not feed this dataset into `tcpc_expanded_geometry_fit.py` or
`tcpc_short_probe_current_fit.py` unchanged. Those historical fit paths are
single-length: they discard tool/TLO/session fields, select old fixed row
ranges, and retain the obsolete fixed T3-tip geometry. The paired analyzer may
validate and difference this campaign, but a later fitter must model the
spindle nose plus each row's actual TLO and separate S1/L/S2 reference offsets.

For each pose and time block:

1. In Stage A, use the mean of opening and closing B0/C0 as the reference for
   its C-quadrant residuals. In modes 17 and 18, use the surrounding same-C B0
   opening/closing references.
2. In Stage B, use the mean of its opening and closing B0/C0 centers as the
   established production-grid reference. Treat the combined B/C pose error as
   the production result; do not invent an unmeasured B0/C+/-20 reference.
3. Compute each tilted-pose residual relative to its defined same-run reference.
4. Compute opening/closing B0 drift separately. Do not hide drift inside a
   fitted geometry term.
5. Compare S1 and S2 at every common pose to measure session drift and probe
   reseating repeatability.
6. Estimate the short residual at the time of L as:

```text
r_short_mid = 0.5 * (r_S1 + r_S2)
```

7. Compute the effective long-minus-bracketed-short residual vector as:

```text
delta_r_length = r_L - r_short_mid
k_length = delta_r_length / 100.800271
```

`k_length` is dimensionless. For a small rotational error its magnitude is an
approximate angle in radians, but retain the signed vector components. This
quantity also contains T4's one physical insertion and the coupled Z-carriage
position; it is not automatically a pure angular or B-zero measurement.

Report at least:

- per-pose X/Y/Z residuals for S1, L, and S2
- S2 minus S1 drift vectors
- L minus bracketed-short vectors
- per-length vector components using `100.800271 mm`
- RMS and maximum vector magnitude by stage, B sign, C quadrant, and tool
- balanced `+B/-B` averages and antisymmetric differences
- opening/closing B0 drift and ring-verification drift
- any correlation with time, temperature, B sign, C angle, approach, SSI error,
  accepted-pass joint XYZ position/following error, or probe fault

Interpretation rules:

- A residual common to S1 and L is evidence for a machine-fixed, reference,
  correction-surface, or thermal component; it is not proof of one cause.
- A repeatable residual proportional to the added `100.800271 mm` is a candidate
  angular/alignment/rotary-center signature only after insertion/clocking and
  Z-rail-position alternatives have been bounded.
- A difference that is not reproduced by S2 or is accompanied by ring drift is
  probe seating, probe calibration, artifact, or thermal evidence first.
- Balanced low/moderate `+B/-B` evidence across C quadrants and both lengths is
  more suitable for a B-zero question than a one-sided or B90 residual. Ring
  measurements at B0 with TCPC off cannot identify B-zero.
- Do not infer a global B/C zero or force a rich harmonic fit from high-B
  outliers.
- Hold back poses or an entire stage from any later fit. A candidate that only
  reduces its training rows is not accepted.

No coefficient or zero adjustment is allowed while this analysis is in
progress. Complete and review the baseline report first.

## Acceptance and Decisions

### Dataset Acceptance

The paired dataset is acceptable for model decisions only when:

- all required metadata and file hashes are present
- S1, L, and S2 used the same frozen machine state and approved pose order
- every live tool/TLO/calibration/correction check passed
- every accepted pose passed the U/V and diameter gates
- every stage B0 closure is `0.05 mm` or less
- S1-to-S2 common-pose drift is `0.05 mm RMS` or less and `0.10 mm maximum` or
  less, or a separately reviewed thermal model explains the difference
- no sphere/ring movement, rotary clamp movement, SSI fault, following error,
  or unexplained probe event occurred

If these conditions are not met, the data can document a fault but cannot be
used to change the live TCPC model.

### Production-Envelope Acceptance

For each tool separately in Stage B:

- core requirement: maximum B0-referenced center-vector error below `0.20 mm`
- preferred local result: maximum below `0.10 mm`
- B0 closure: `0.05 mm` or less
- no probe, servo, SSI, TCPC entry/exit, clearance, or tool-state fault

T4 is not released for production TCPC merely because T3 passes. T4 must meet
the core Stage B requirement in its own live H4 state. Stage C results are
reported separately and do not silently expand the production envelope.

If T3 passes and T4 fails, preserve the result. That is useful evidence of a
length-dependent problem, not permission to tune the live machine during the
session.

### Post-Baseline Decision Order

1. Reject or repeat first if probe qualification, S1/S2 repeat, closure,
   mechanics, electrical behavior, thermal state, or metadata is weak.
2. If a repeatable length-proportional vector exists, test the smallest
   physically meaningful rigid geometry/alignment hypothesis offline.
3. If a residual is common to both lengths, investigate reference frame,
   machine-fixed harmonic behavior, linear-axis lost motion, and thermal state.
4. Validate any proposed model on held-out short and long poses before creating
   a live candidate.
5. Treat high-B work as a new, separately authorized experiment.
6. Apply only one reviewed parameter family at a time in a later session with
   an explicit before/after and rollback record.

The steel frame and intended vacuum-formed-part trimming use do not justify
forcing a global sub-0.1 mm fit. Prefer a stable, balanced, explainable result
inside the required production envelope.

## Abort Recovery

On a probe miss, false trip, abnormal indication, clearance concern, following
error, or any unexpected motion:

1. Use feed hold or stop immediately. Use emergency stop whenever personnel or
   equipment safety requires it.
2. Do not change WCS, touch off, clear tool length, disable TCPC, or rotate the
   head while the probe may still be in contact.
3. Clear the legacy motion digital outputs with `M65 P0` and `M65 P1` when MDI
   is available and it is safe to do so. They do not authorize or inhibit the
   current physical probe path; the real-time gate follows actual G38 motion and
   closes when that probing transaction is removed from the motion queue.
4. Verify the raw and gated probe inputs. Retract from contact along the last
   known safe probe vector or to a previously verified linear clearance while
   preserving the current TCPC/tool state.
5. Only after the tip, probe body, holder, sphere, and post are clear, return C
   and B to the saved B0/C0 TCPC entry orientation using a supervised safe path.
6. At B0/C0 issue `G49.1` and verify `headheadtwp.tcpc_enabled = 0`.
7. Issue `G49` only after TCPC is confirmed off. Verify active TLO is zero.
8. Preserve and label all partial logs. Record the exact failure state and do
   not use accepted-looking rows from the interrupted stage for paired fitting.
9. Correct the physical, electrical, software, or state problem. Repeat ring
   verification and live preflight, increment selector `#727`, then restart
   that S1/L/S2 stage from a new B0 reference.

Campaign `2026082201` exception: the owner/operator waived repeat T3 ring
attempt `10` after the mode-17 attempt-1 software release-timing abort. T3
remained clamped and undisturbed, there was no collision or loss of home, and
ring attempt `9` remains the S1 installation reference. Attempt `10` was never
started and its ID is retired. This scoped waiver does not waive the live
preflight, new attempt ID, fresh reviewed B0/C0 sphere start, or complete
20-pose restart, and it does not change the normal L/T4 or S2 installation
checks.

Prepared mode-17 attempt `2` was later superseded before measurement. At the
supersession snapshot LinuxCNC was idle at line 0 with zero velocity, unchanged
XYZBC, and no added CSV row. Whether Cycle Start ever briefly reached the
initial pre-motion M0 cannot be established independently, so the record makes
no stronger claim. The exact prepared runner is retained, attempt ID 2 is
retired, and a future complete mode-17 restart must use attempt 3.

Campaign `2026082202` has a separate owner disposition waiving repeat ring
verification for its provisional T3-to-T4 baseline while both frozen offsets
remain unchanged. That disposition does not retroactively alter this plan's
S1-L-S2 installation-check contract and ends on a collision, abnormal or false
trigger, visible damage, lost home, or tool/offset mismatch.

Do not use a historical resume file unless it has been separately reviewed for
the current tool, current calibration offset, correction-on state, safe pose,
and isolated output files.

## Rollback

This baseline intentionally makes no model or zero change, so the normal
rollback is to stop, leave the frozen configuration untouched, and retain the
evidence.

If a coefficient, zero, backlash, tool length, or other frozen value is changed
accidentally:

1. Abort the paired sequence and mark every subsequent row invalid.
2. Restore the exact recorded pre-session values without discarding unrelated
   working-tree changes.
3. Restart LinuxCNC so rebuilt or reloaded state is unambiguous.
4. Recheck file hashes, live pins, B/C zero, backlash, tool table, ring
   qualification, and sphere position.
5. Start a completely new S1-L-S2 run ID. Do not splice data across the change.

Any later correction candidate requires its own signed-off change record with
the exact old/new values, offline result, held-out validation, live smoke test,
short/long verification, acceptance result, and manual restore procedure. That
candidate phase is outside this baseline plan.

## Superseded Guidance

For this calibration stage, this plan supersedes older instructions that call
for any of the following:

- a 20 mm sphere instead of the current 30 mm sphere
- TWP or real-machine `G68.2` verification
- `G43.4` without first applying and live-verifying `G43 Hn`
- a fixed short-probe-tip B-to-tool Z of `-308.980001` combined with active H3
- correction-off mode 8 as the production-state paired baseline
- nonzero B or C LinuxCNC backlash
- automatic reuse of T3 calibration offset `0.134533` for another probe
- trust in Probe Basic's displayed tool row or stale interpreter tool variables
- comparison of new T4 results with pre-clamp or pre-sphere-move data
- B+/-50, B+/-60, or B+/-90 as part of the first paired-length run

The detailed historical reports remain useful for provenance and diagnosis,
but they do not override this run control.

## Session Close-Out

Before leaving the machine:

- [ ] B and C are at zero.
- [ ] TCPC is off.
- [ ] TWP remains off and undefined.
- [ ] Active tool length is either deliberately preserved for the next approved
      operation or cleared only after TCPC exit; the final state is recorded.
- [ ] Probe gates are closed and raw probe input is healthy.
- [ ] Every output interval is isolated, hashed, and labelled.
- [ ] Aborted and diagnostic-only data is retained but excluded explicitly.
- [ ] No coefficient, zero, backlash, or WCS change was made.
- [ ] A short factual session note records what passed, what failed, and the
      next authorized action.
