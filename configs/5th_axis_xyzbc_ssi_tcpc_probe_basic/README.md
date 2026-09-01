# 5th Axis XYZBC SSI TCPC Probe Basic Config

Current calibration stage: length-aware model revision `2026082601` has passed
both available physical probe endpoints at the reference sphere location. T4
Attempt 2 is the formal uninterrupted `q=0` common-bank result. T3 is a
composite engineering `q=1` pass: Attempt 1 supplies canonical rows `1..22`,
and the separately identified Attempt-2 recovery supplies rows `23..31` after
two continuity bridges passed at `0.005719` and `0.013314 mm`.

The T3 equal-20-pose RMS/max is `0.103060/0.218333 mm`, compared with
`0.251775/0.592990 mm` reconstructed without the length-aware correction.
Positive B, negative B, and B0 all improve; the maximum individual-pose
worsening is `0.008584 mm`. Recovery acquired exactly `11/11/11`
result/state/model rows, six passing closures, and `88/88` successful guarded
contact/gap transactions. Four delayed post-contact edges were logged and
filtered; none reached the motion input. Full disposition and hashes are in
`TCPC_LENGTH_AWARE_T3_ATTEMPT2_RECOVERY_CLOSEOUT_REPORT.md`.

Attempt 1's rejected false W touch remains excluded. The T3 result spans a
probe reseat and power cycle, so it is not a formal uninterrupted release; a
fresh 31-row acquisition is required only if that stronger evidence class is
later needed. The current physical accuracy evidence covers the probe bracket
`128.606729..229.407000 mm`. Longer-tool accuracy remains extrapolation until
the planned dial-gauge test near `425..430 mm`.

A second-location T4 campaign is also complete. It identified a strong
location/session-associated X-oriented indicated-span change and a broader
Y-dominated high-B center field. That campaign is an axis-geometry diagnostic,
not a calibration source: it did not change the model coefficients, B/C zeros,
kinematics, HAL calibration, or tool table. An X-only/Y-only paired-position
test is still required before attributing the effect to a specific rail or
building an axis correction table.

LinuxCNC was closed normally on `2026-08-28` after the completed campaigns.
No LinuxCNC, Probe Basic, milltask, or RTAPI process and no
`/tmp/linuxcnc.lock` remained at the closeout check. Do not assume homing,
tool, TLO, G43.4, coordinate, or probe state at the next start.

The complete read-only T3 composite evidence package is
`calibration_runs/20260827_1503_campaign2026082602_t3_length_aware_attempt2_recovery_complete`.
Its 186-entry `SHA256SUMS` hashes to
`91296bbd468f5b5f67c0722c1142ce0a0edbf3bedd4bd4579aa6f53f68215bca`.

This is the separate real-machine TCPC/TWP Probe Basic config. It is not the
maintenance or setup config, and it remains a commissioning work config until
the full TCPC/TWP task list is complete.

## Default Cut-Test Launch - 2026-08-28 +07

The shared TCPC launcher and LinuxCNC `LAST_CONFIG` now select the physically
validated length-aware revision `2026082601` INI. Both desktop shortcuts use
the shared launcher, so `5th Axis.desktop` and `TCPC Trim Work.desktop` select
the same configuration without duplicating the INI path in the desktop files.

This promotion is for controlled program cut testing. It does not release the
commissioning config for unattended or general production use. The separate
T4 new-location campaign remains an axis-geometry diagnostic only: none of its
location-associated results changed the model coefficients, B/C zeros,
kinematics, HAL calibration, or tool table.

## Separate TWP Shared Workpath - 2026-08-31 +07

The authoritative current controller and Fusion postprocessor contract is
`TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md`. Older simulation contracts
that required public `G43.4` under TWP are superseded and must not be used for
posted code.

`G43.4` TCPC and `G68.2` TWP are separate public modes. The commissioned
length-aware geometry revision remains shared internally; there is no second
TWP coefficient set or reduced tool model. The guarded TWP sequence is:

1. Apply the ordinary positive `G43 H` tool length with `G43.4` off.
2. Preposition B/C to the required orientation while TWP is clear.
3. `G68.2` defines the frame and leaves world switchkins type 0 selected.
4. `G53.1` performs a stationary handoff to tilted switchkins type 1.
5. Fixed-B/C local XYZ motion runs with public TCPC still off.
6. `G69` returns to world type 0 and then clears the stored frame.

Fusion/Fanuc `G68.2 X Y Z I J K` input is accepted using the post's rotating
`ZXZ` Euler convention. `X/Y/Z` define the pivot in the active work frame.
The commissioning `B/C/R` form remains available as a reached-pose assertion.
Neither form commands rotary motion in this first implementation. The exact
live C branch is retained, so an equivalent assertion such as `C10` at reached
`C-350` cannot introduce a 360-degree move.

Type 1 calls the same active-tool snapshot and
`evaluate_tool_offset_world()` implementation as TCPC. It captures that
calibrated tool reference internally without setting
`headheadtwp.tcpc_enabled`. A dedicated
`headheadkins.synchronized-twp-enable` input and the TCPC-off condition
authorize the type-1 switch; finite stale frame parameters alone are not
sufficient.

`G69` uses separate exit and clear transactions. Interpreter guards restrict
the first scope to fixed-B/C `G0/G1/G38.3` XYZ motion plus `G4` dwell.
Unsupported probing, arcs, coordinate changes, cutter compensation, rotary
words, tool or offset changes, and program end before `G69` are rejected.

The default cut-test INI still omits `[TWP] ENABLE=1`, so TWP remains locked
there. Only the dedicated supervised INI
`5th_axis_xyzbc_ssi_tcpc_probe_basic_twp_probe_validation_2026083101.ini` opts
in; its launcher is `launch_xyzbc_ssi_twp_probe_validation.sh`.

The physical stage-1 routine is `twp_sphere_probe_stage1_t4.ngc`. It runs a
WORLD/TWP/WORLD comparison, explicitly issues `G68.2` then `G53.1`, and
reconstructs the tilted result through the captured pivot/coordinate layer.
Its B0-first operator and recovery sequence is in
`TWP_SPHERE_STAGE1_T4_PLAN_2026083101.md`.

Revalidation completed after a clean controller shutdown on 2026-08-31:

- Python compilation, static G-code structure, independent coordinate math,
  and the rebuilt interpreter/kinematics pass.
- The switchkins runtime completed 18,931 servo samples across four stationary
  edges. It covered T3 with Fusion `ZXZ` I/J/K input at `B30 C90 R17`, T4 at
  reached `C-350` asserted as `C10`, defined-only motion rejection, 11 active
  fail-closed guards per tool, and `G38.3` contact/no-contact paths. Public
  TCPC remained off and no joint/TCP continuity fault was detected.
- The component-loss runtime held the active type-1 pose stationary after the
  state owner was killed; a wholly fresh start restored world type 0 with all
  synchronized frame state clear.
- The exact physical sphere program completed in AUTO with 24 contacts and six
  pass rows. Simulated WORLD closure was `0.000726 mm`, transformed TWP error
  was `0.000776 mm`, the reversible 1 mm preflight closed to zero, `G69`
  restored world state, and both CSV files were restored byte-for-byte.
- All 15 existing head-head TCPC/TWP behavior scenarios also completed with
  successful process status, preserving the older diagnostics interface and
  its fail-closed tooling, reset, limit, and recovery behavior.

At this historical stage these were offline/headless results only. That status
is superseded by the accepted B0, signed-B, and 24-pose physical runs recorded
later in this section. The dedicated INI remains a supervised path.

The existing calibration revision `2026082601` is frozen. This TWP work changes
no fitted coefficient, B/C zero, tool-table entry, or default cut-test
configuration.

### First Physical Attempt And Coordinate-Layer Fix - 2026-09-01 +07

The first B0/C0 physical attempt completed eight opening WORLD contacts before
the program's coordinate-layer guard stopped it after stationary `G68.2` and
`G53.1`, but before the 1 mm local TWP preflight. `G69` returned the controller
cleanly to world type 0. Therefore this attempt contains valid opening WORLD
diagnostics but no physical local-TWP motion and no accepted result row.

The two retained pass rows have centers `(0.001139,0.015416,-21.492091)` and
`(-0.004695,0.014585,-21.489758) mm`, V diameters `30.185500` and
`30.182167 mm`, and radial residuals `0.092750` and `0.091084 mm`. They are
partial-attempt evidence only.

Read-only post-abort diagnostics isolated the failure to coordinate sources.
The real homing state separated machine joint XYZ from `motor-pos-cmd` by
`(878.642799829,645.600399981,-280.865200000) mm`. The TWP remap and state
component had incorrectly treated the motor layer, which includes this homing
offset, as machine coordinates. Both now source `joint.N.pos-cmd`. The
program's independent coordinate guard remains unchanged and continues to
fail closed.

The simulator now preserves those measured homing layers instead of allowing
machine and motor coordinates to be numerically identical. An exact replay at
the captured B/C, G54, and work start completed the production program with 24
contacts, `0.000965 mm` WORLD closure, and `0.000510 mm` TWP error. The normal
B+5/C0 case also passed with `0.000630/0.000236 mm` closure/error. Switchkins
continuity, component-loss/restart, and all 15 established TCPC/TWP scenarios
passed. The production CSV backup/restore checks remained byte exact.

This correction changes no calibration coefficient, rotary zero, tool-table
entry, probe offset, or length-model ID. Revision `2026082601` remains the
single shared calibration for TCPC and TWP. The next physical attempt must be
a full restart of the WORLD/TWP/WORLD program under direct supervision.

### Accepted B0/C0 Physical TWP Run - 2026-09-01 +07

The restarted T4/H4 program completed all six passes and appended its first
accepted physical result row. Measured rotary position was
`B-0.000354 C-0.000367`. The result was:

- 24/24 gated contacts
- WORLD opening-to-closing closure `0.008815 mm`
- transformed TWP center error `0.001965 mm`
- opening WORLD / TWP / closing WORLD two-pass deltas
  `0.005467 / 0.005058 / 0.010796 mm`
- V diameters `30.173000 / 30.177167 / 30.184667 mm`
- maximum radial residuals `0.086970 / 0.090712 / 0.097388 mm`

Each pass intentionally uses four contacts: top W, one stand-safe U side
(X-minus at B0), and both V sides (Y-minus/Y-plus at B0). The opposite U side
is omitted for stand clearance; the certified sphere radius supplies that
single-sided center constraint, while the paired V contacts provide the
diameter check.

The operator paused once for a transient wireless-probe error that self-cleared.
The raw/mux counters finished at 25 edges and the motion-gated counter at the
required 24, proving the extra receiver pulse did not reach a G38 contact. No
point was missed, all program gates passed, and no persistent fault remained.
The result is accepted supervised evidence with one documented intervention,
not an unattended-clean run.

`G69` restored world type 0 and cleared all TWP frame state. This neutral run
validates the physical coordinate-layer correction and the B0 TWP path. It
does not replace nonzero-angle validation. The earlier plan for an
operator-prepositioned B+5 run is superseded by the guarded full-cycle test
below.

### Prepared B0/B+5/B0 Full-Cycle Test - 2026-09-01 +07

The next production test program is
`twp_sphere_full_cycle_bplus5_t4.ngc`. It starts only from the standard B0/C0
sphere-top point. After two opening WORLD references, it moves the physical
probe through an 80 mm world-clearance point, indexes to B+5/C0 with TWP clear,
approaches the B+5 start, and executes the literal Fusion/Fanuc sequence
`G68.2 X0 Y0 Z0 I90 J5 K-90` followed by `G53.1`. It probes in TWP, cancels
with `G69`, returns through the guarded clearance path to B0/C0, and measures
closing WORLD references. This validates positioning plus transition into and
out of TWP as one cycle rather than relying on operator prepositioning.

The program has one initial `M0`, 24 gated contacts, no clearance-test holds,
and separate pass/result CSVs. Its full operator and recovery contract is in
`TWP_SPHERE_FULL_CYCLE_BPLUS5_T4_PLAN_2026090101.md`. Static G-code,
lifecycle-order, coordinate-source, and CSV-schema checks pass. With the
physical controller closed, the dedicated actual-program simulator completed
the B0/B+5/B0 path with 24/24 contacts, `79.734424 mm` minimum rotary-transition
clearance, exact 1 mm local-Z preflight and zero closure, `0.000410 mm` WORLD
return closure, and `0.000606 mm` transformed TWP error. It observed exactly
one TWP entry and exit, no rotary motion in TWP, final B0/C0 world state, and
byte-identical evidence-CSV restoration. The program is ready for its first
supervised physical run but has not been loaded or started on the CNC.

### Accepted B0/B+5/B0 Physical TWP Cycle - 2026-09-01 +07

The first physical full-cycle run passed. Starting from the standard B0/C0
sphere-top point with T4/H4 and public TCPC off, it completed the guarded world
lift, B+5 index, literal Fusion/Fanuc `G68.2 X0 Y0 Z0 I90 J5 K-90` / `G53.1`
entry, local TWP probing, `G69`, B0 return, and closing WORLD reference.

Accepted metrics were:

- 24/24 gated contacts and six complete pass rows
- WORLD return closure `0.006120 mm`
- transformed B+5 TWP center error `0.039035 mm`
- opening WORLD / TWP / closing WORLD pair deltas
  `0.006026 / 0.007905 / 0.009274 mm`
- V diameters `30.174250 / 30.181332 / 30.186333 mm`
- maximum radial residuals `0.088598 / 0.091539 / 0.095250 mm`

Rapid override was initially 0%, so the program waited safely at the common
world-clearance point before B motion. Raising it to 10% continued the queued
move; there was no Stop, Abort, jog, MDI, or restart-from-line. Raw/mux/gated
counters ended `31/31/24`: six additional pulses were delayed post-contact
events inside the ignore window, and one transient pulse occurred during the
safe B index. The latter asserted the abnormal/fault event briefly but never
reached `motion.probe-input`, self-cleared, and passed the subsequent quiet and
state guards before TWP entry.

Final state was idle at commanded B0/C0 in world type 0, all TWP/TCPC state and
probe levels clear, SSI valid, T4/H4 retained, and the 25 mm safe lift complete.
The full disposition is in
`TWP_SPHERE_FULL_CYCLE_BPLUS5_T4_CLOSEOUT_2026090101.md`. This accepted B+5
result changes no shared calibration value.

### Accepted B0/B-5/B0 Physical TWP Cycle - 2026-09-01 +07

The signed counterpart also completed the full program-controlled lifecycle.
Starting from the same B0/C0 sphere-top point, it indexed in world mode to
B-5/C0, used the exact Fusion/Fanuc alternate rotating-ZXZ branch
`G68.2 X0 Y0 Z0 I-90 J5 K90` / `G53.1`, probed locally, cancelled with
`G69`, and returned to B0/C0.

Accepted metrics were:

- 24/24 gated contacts and six complete pass rows
- WORLD return closure `0.008735 mm`
- transformed B-5 TWP center error `0.187620 mm`
- opening WORLD / TWP / closing WORLD pair deltas
  `0.001675 / 0.004967 / 0.008813 mm`
- V diameters `30.174667 / 30.154666 / 30.171333 mm`
- maximum radial residuals `0.088991 / 0.079189 / 0.087335 mm`

The accepted restart was clean: raw/mux/gated counter deltas were exactly
`24/24/24`. An earlier start was externally aborted after four opening WORLD
contacts, before TWP entry and before any row was logged; a later idle receiver
pulse storm remained outside the motion gate. The operator restored the
standard start and an eight-second quiet qualification passed before the clean
restart.

The B-5 TWP center delta is dominated by X:
`(+0.187194, -0.012535, -0.001567) mm`. The independent commissioned TCPC data
at B-5/C0 gives `(+0.180134, +0.000898, -0.006274) mm`, norm `0.180245 mm`.
The matching magnitude and +X direction show that this asymmetry is shared
rotary-model or machine-geometry behavior, not a TWP transition-specific
error. It passes the `0.250 mm` commissioning gate but exceeds the secondary
`0.100 mm` accuracy target.

Final state was idle at commanded B0/C0 in world type 0, all TWP/TCPC state and
probe levels clear, SSI and model state valid, T4/H4 retained, spindle off,
and the 25 mm safe lift complete. Full disposition is in
`TWP_SPHERE_FULL_CYCLE_BMINUS5_T4_CLOSEOUT_2026090102.md`. No shared
calibration value changed. The next staged lifecycle evidence is the signed
B+5/B-5 pair at C90.

### Accepted Low-Angle B/C TWP Grid - 2026-09-01 +07

The supervised T4 campaign `2026090103` completed the full 24-pose matrix:
B `+/-5, +/-15, +/-30` at C `0, 90, 180, 270`. Each pose completed a world
index, literal rotating-`ZXZ` `G68.2`, stationary `G53.1`, local-Z preflight,
four-contact sphere pass, `G69`, and world-mode retract. Every positive B pose
was immediately followed by its negative counterpart.

Accepted acquisition:

- 24/24 pose rows and 24/24 TWP entries/exits
- 24/24 reversible local-Z preflights
- 112/112 motion-gated contacts and 28 complete pass rows
- no B/C motion while TWP was active
- no Stop, Abort, recovery segment, restart, or offset change
- final commanded B0/C0 in ready world type 0 with TWP/TCPC clear

Physical metrics:

- WORLD return closure `0.052759 mm`
- opening/closing pair repeatability `0.006406/0.010418 mm`
- center-error mean/RMS `0.141458/0.150468 mm`
- center-error range `0.031116..0.205463 mm`
- worst center pose B-30/C180
- maximum radial residual `0.141089 mm` at B+30/C270

All program gates passed. The center-error gate was a tolerant `2.000 mm`
diagnostic stop, not an accuracy target. The matching signed-B TCPC/TWP
evidence continues to identify the remaining error as shared machine/rotary
geometry rather than a TWP transition defect. No calibration coefficient,
B/C zero, WCS, tool-table value, or probe offset changed.

The implementation is accepted for supervised CAM cut testing inside the
physically tested `|B| <= 30 deg` envelope. This is not an unattended
production release and does not validate arcs, canned cycles, changing B/C in
TWP, or the remaining machine angular range. Full disposition and evidence
hashes are in `TWP_SPHERE_GRID_LOW_ANGLE_T4_CLOSEOUT_2026090103.md`.

## Length-Aware Runtime Boundary - 2026-08-26

The kinematics now has an opt-in, synchronous length-aware correction path.
Its reviewed software domain is `100.000..430.000 mm`, with at most `0.002 mm`
comparison tolerance at either endpoint. This includes every current tool
(`114.677..411.810 mm`) and the recent historical `425.022 mm` tool. It uses
the live effective Z tool offset, does not clamp at T3/T4, and rejects
zero/nonfinite Z, unsupported non-Z tool offsets, an expanded domain or
tolerance, a coefficient-set ID mismatch, nonfinite transforms, and correction
norms beyond their audited caps.

This path remains disabled in the production and legacy capture INIs. It is
enabled only in the dedicated validation config
`5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`,
which loads `tcpc_length_aware_candidate_2026082601.hal` as its final HALFILE.
Neither file is released for production machining or general TCPC use. Any
promoted configuration must specify both
`lengthmodel=1 lengthmodelid=2026082601` on its `KINEMATICS` line and
`LENGTH_MODEL_REQUIRED = 1` in `[TCPC]`, then load the exact matching overlay.
That overlay is startup-only and must never be sourced or reloaded in a running
LinuxCNC session. Every coefficient change requires a new model ID and a clean
restart; the ID commit marker is not a live-tuning interface.
The required flag makes a missing kinematics option fail closed at `G43.4`;
the model ID makes a missing or wrong coefficient overlay invalid. Fault codes
are: `0` OK, `1` configuration, `2` model ID, `3` nonfinite active offset,
`4` unsupported active X/Y, `5` length range, `6` common surface disabled,
`7` nonfinite correction, `8` differential norm, `9` total norm, and `10`
nonfinite complete transform. Full numerical and physical-validation limits
are in `TCPC_LENGTH_AWARE_MODEL_PLAN.md`.

The frozen T3 recovery campaign `2026082602`, mode `34`, attempt `2` is
complete. Its exact operator order remains in
`TCPC_LENGTH_AWARE_T3_ATTEMPT2_RECOVERY_PLAN.md`. It carried forward the
T4-proven rule that accepts at most two matching raw/mux extra edges around a
successful contact only when exactly one gated edge reaches motion and the
probe releases cleanly; all extras remain logged. T4 has passed the common bank
at `q=0`, and the composite T3 result has passed the differential endpoint at
`q=1`. The longer-tool dial-gauge endpoint remains a separate later gate.

Current status:

- uses `headheadkins coordinates=XYZBC kinstype=B`
- reuses the proven Mesa/SSI motion HAL from
  `configs/5th_axis_xyzbc_ssi_probe_basic`
- reuses the existing Probe Basic UI, subroutines, XHC HAL, shutdown HAL, and
  tool table from the trivkins Probe Basic config
- uses its own LinuxCNC parameter file so TCPC/TWP WCS changes do not write
  back to the normal Probe Basic parameter file
- starts fail-safe with TCPC disabled; production G-code must move to explicit
  `B0 C0` and then enter TCPC with `G43.4` after the machine is enabled and all
  XYZBC joints are homed
- `G43.4` sets a live TCPC entry origin in `headheadkins` so entry does not
  cause a kinematics position jump
- `G49.1` exits TCPC only when TWP is fully cancelled with `G69` and B/C are
  back at the `B0 C0` TCPC entry orientation; otherwise it aborts with an
  operator error
- `M6` and `M61` are rejected while guarded TCPC or TWP is active and while any
  spindle is active through `TOOL_CHANGE_REJECT_SPINDLE_ON = 1`; tool/current-
  tool changes require `G49.1` TCPC exit and an explicit `M5` first
- `headheadtwp.tcpc_enabled` gates `headheadkins.tcpc-enable`, and
  `headheadtwp.tcpc_origin_*` feeds `headheadkins.tcpc-origin.*`
- the refined B-harmonic/B-cross fitted correction is now persistent in this
  TCPC work config and starts enabled with `headheadkins.sim-bharm-enable = 1`
- `headheadtwp` uses the live `headheadkins.tool-offset.*` pins for TCPC/TWP
  state calculations, so the helper state sees the same fitted tool offset as
  the kinematics layer
- unwraps the single-turn C SSI feedback to the nearest commanded C angle with
  `rotaryunwrap` before feeding joint 4
- requires homing before motion with `NO_FORCE_HOMING = 0`
- B/C homing uses `HOME_ABSOLUTE_ENCODER = 2`, so homing no longer redefines
  B0/C0 at the current rotary position; B/C machine position remains the
  SSI-derived angle from the calibrated HAL zero constants
- adds TCPC/TWP indicators to Probe Basic:
  - compact single-LED `TCPC OFF` / `TCPC ON` / `TCPC TWP` status in the
    user-button area
  - detailed `TCPC STATUS` user tab showing state, angles, tool vector, tool
    offset, TCPC origin, TCPC entry B/C pins, direct B/C SSI absolute and
    zeroed positions, raw SSI counts, invalid flags, and joint command/feedback

## Long/Short Probe Calibration Handoff - 2026-08-22 +07

Current work is the separate owner-directed campaign `2026082202`: T3 short,
then T4 long, on the fixed 30 mm sphere at B `0/+5/+15/+30 deg` and safe C45
sectors. Its authoritative procedure is
`TCPC_POSITIVE_B_C45_BASELINE_PLAN.md`; its data must not be appended to or
analyzed as campaign `2026082201` modes 15-18. The 45-degree post runs
base-to-sphere in `X+,Y-,Z+`. At nonzero B the new runners never descend to or
probe C135/C315; those six canonical slots remain explicit unsafe gaps.

T3 attempts 3, 4, and 5 are excluded partials ending at canonical sequences
10, 3, and 2. Attempt 6 is an excluded zero-row electrical/probe-state fault:
its one completed first pass was displaced `0.709 mm` from prior B0/C0 centers,
pass 2 did not complete, and the campaign CSV did not change. Attempt 7 is the
next required full restart, but it is barred until T3 is reseated and passes
the no-motion electrical qualification.

The prepared Attempt-7 HAL keeps the realtime G38-only motion probe path and
the `10.0 s` post-contact quarantine. Later outside-G38 pulses create a
monitor-only `0.5 s` event latch; they no longer request `halui.program.pause`.
The runner samples that latch and raw signals, resets its separate `20.0 s`
continuous-clear timer on every event, and hard-aborts if it cannot prove a
clear interval within `60.0 s`. False pulses during G38 remain a hardware risk
and are not hidden or debounced.

Campaign `2026082201` completed the ring phase and S1/T3 Stages A and B. S1
Stage C-low attempt 1 is retained as an excluded `13/20` partial after a
post-contact probe-release guard abort. Prepared attempt 2 was superseded
before any axis/probe motion or CSV row; its exact file is preserved, attempt
ID 2 is retired, and any future mode-17 restart must use attempt 3. The active
legacy runner is disarmed. T3 `#3032 = 0.117658 mm` and T4
`#3032 = 0.154742 mm` remain frozen. No geometry, B/C zero, correction surface,
backlash, or tool-table change has been made from the sphere results.
The dedicated campaign-2026082202 T3 and T4 runners now restore their matching
frozen value internally, after exact live-tool and TLO validation and before
any probing. This is a reload of accepted calibration state, not a new
qualification or offset calculation.

The owner/operator confirms that the CNC is fully operational, that the 50 mm
ring and 30 mm sphere are certified calibration tools, and that the ring has not
moved. The steel frame, spindle wear, insertion position, Z-rail error,
alignment, and possible B-zero error define the identification problem. A
ring result under `0.010 mm` is very good here; it is not a global 10 um TCPC
accuracy claim.

At the 2026-08-22 handoff, the long probe was represented by the then-uncommitted
T4/H4 tool-table row. That row is included in the 2026-08-28 calibration
closeout commit.
The historical S1-L-S2 procedure is:

```text
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_LONG_SHORT_PROBE_CALIBRATION_PLAN.md
```

The current runtime checkpoint and operator order are in:

```text
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_CALIBRATION_RESUME_STATE.md
```

Current tool identities are T3/H3 `128.606729 mm` and T4/H4 `229.407000 mm`,
giving `100.800271 mm` of differential length. The base kinematics already
rotates live `G43` tool length from a spindle-nose model; it is not a fixed T3
tip model. The unresolved issue is that the persistent additive B/C correction
was fitted and validated only with T3. Any angular or alignment error absorbed
by that surface will not scale correctly for T4.

At one fixed artifact height, the length difference also changes the Z-carriage
position and physical probe insertion. The ring-center difference cannot by
itself distinguish rail error, seating eccentricity, trigger anisotropy,
tool/spindle tilt, or B-zero. The sphere B/C poses are the primary next evidence:
they map the absolute effective center offset across C quadrants and balanced B
signs, while joint XYZ logging records where each observation occurred.

The current startup HAL deliberately remains frozen for the baseline. It uses
the earlier persistent refined B/C-cross candidate, not the later diagnostic
balanced-final short-probe candidate. Do not promote either candidate, change
B/C zeros, or add a tool-axis tilt before collecting fresh paired evidence.

At the historical 2026-08-21 pre-campaign checkpoint, the real configuration
was launched only for load-only checks.
The exact prepared versions of both ring wrappers and the paired runner were
loaded one at a time through LinuxCNC `program_open`; all three loaded without
an error-channel or UI parse error. LinuxCNC remained machine-off and
motion-disabled with tool 0, all three live TLO views at zero, TCPC false,
every TWP state false, both SSI-invalid signals false, an idle interpreter, and
unchanged actual positions. No homing, jog, MDI, program start, or motion was
performed. LinuxCNC was shut down afterward and the hardware/real-time stack
unloaded. Probe Basic required forced termination during this scripted
shutdown after it did not respond to Ctrl-C or SIGTERM. This is a
configuration/file-load check, not a machine-motion or calibration result.

An earlier preparation launch displayed the intermittent startup real-time
delay warning already known to the owner/operator. It has not affected machine
operation, and the final exact-tree shutdown reported zero latency excursions;
record it as known startup context rather than a calibration blocker. Stop and
investigate only if a latency event is accompanied by a control or motion
fault. The configured `PROGRAM_PREFIX=/home/cnc5/mnt/cnc/5th axis` path was
absent, so the UI used a fallback program location. Explicit selection of the
reviewed files is acceptable; record their actual paths and hashes in the run
manifest.

The normal procedure qualifies T3 and T4 separately with
`nc_files/calibration/50mm_ring_probe_qualify.ngc`. The wrapper derives and
logs `#3032`, establishes a calculated wall start with protected moves, stops
for candidate review, then freezes the candidate and attempts three automatic
verification rounds. The first failed numeric gate is logged and stops at the
measured center and top clearance without automatic repositioning. A passing
set has exactly three passing rows; a failed set may contain only a completed
prefix and is rejected. Selector `#727` reserves four IDs: qualification uses
the base and verification uses base+1 through base+3; a partial retry advances
the base by four. `50mm_ring_probe_verify.ngc` remains the standalone check for
later installations or extra evidence and requires `#717` plus matching live
`#3032`. Results append to `tcpc-long-short-ring-results.csv`. Freeze one offset
for T3 and reuse it unchanged for S1 and S2; qualify and freeze a different
value for T4/L. Do not reuse the historical T3 offset for T4.

The ring contract is: each averaged diameter within `0.010 mm` of the stamped
`50.001 mm`; three-row averaged-diameter range no more than `0.010 mm`; X and Y
center ranges each no more than `0.010 mm`; and no false trip or frozen-state
violation. Directional X/Y diameter behavior remains diagnostic and is not
hidden by scalar `#3032`. The executed T4 program factually stopped on its old
`0.005 mm` gate after logging all rows; post-run review accepted the complete
set under the declared machine-capability rule without rewriting that history.

The certified ring is stamped `50.001 mm`, and both guarded ring routines use
that value. The sphere routines currently use `30.000 mm`. The operator has
authorized diagnostic collection with the certified nominal 30 mm sphere, but
each certificate ID, calibrated dimension, uncertainty, and reference
temperature remains mandatory before final dataset/model acceptance. If the
full sphere certificate value is materially different, the affected rows cannot
support a calibration decision until the constants, limits, and need to rerun
have been reviewed.

The pinned ring stack treats non-contact `G38.3` positioning as protected
motion. Any unexpected trip reverses that single-axis move to its captured
start coordinate, synchronizes motion, and aborts instead of accepting a
shortened move.

The guarded runner is
`nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`, paired modes
`15` through `18`. Invalid or sentinel campaign, leg, stage, attempt, and
independently ring-qualified probe-offset fields abort before motion; the file
is armed only for the reviewed next stage. It checks
live tool/TLO/diameter/correction/TCPC/TWP/SSI state, requires G52/G92 clear and
active-WCS B/C offsets plus XY rotation zero, freezes the active WCS/offsets,
and writes accepted rows to
`tcpc-long-short-pair-results.csv` without mixing them into the historical
single-length logs. Each accepted row includes absolute endpoint XYZ and joint
0/1/2 motor command, feedback, and following error in addition to the sphere
center and rotary state. Run T3 short-open, T4 long, then T3 short-close on the
same sphere and warm state. Start at B0, then the proven trim envelope and
B+/-10. Analyze the absolute effective center map and B0-referenced pose change
before authorizing B+/-30. Start the tip only `4-5 mm` clear above the sphere;
the guarded top search is `7 mm`. B+/-60 and B+/-90 are outside this first
baseline.

The ring wrappers and paired runner enforce an `M0` after their state guards
and immediately before probing or paired-stage motion. Across every hold they
reject selector changes; the ring wrappers also reject WCS/offset changes,
reject actual-XYZ changes, rewrite the fixed measurement contract, and then
revalidate live state before motion. The paired runner also snapshots and
revalidates all motion constants.
Every hold freezes actual XYZ, and the initial hold additionally requires the
machine to remain physically at B0/C0 before the low-clearance first pose. It
has a mandatory inspection `M0` in every leg: after Stage A's B0 quadrant group,
after Stage B's B+5 group, and after the opening B0 quadrant group in modes 17
and 18. Live state is checked again before subsequent motion. `#704 = 0` only
means there is no extra stop before every individual pose. Restart LinuxCNC
after compiled/remap/HAL/INI changes; the reviewed NGC-only revision does not
require a restart and was load-checked in the live idle session.

Every paired live guard begins with `M66 E0 L0` so queued retract or rotary
motion finishes before HAL and coordinate state are sampled. A final
synchronized guard after the last side retract verifies probe release before
accepted endpoint and joint state are captured. Direct C SSI is physically
opposite joint-C polarity, so its wrapped pose check compares `C_ssi + C_cmd`;
B SSI remains same-polarity and compares `B_ssi - B_cmd`.

Historical mode-17 attempt 1 showed that queue synchronization alone did not
implement the HAL wireless-probe release contract. That disarmed runner uses a dedicated guard
at all five post-contact locations: probe gates must be clear immediately, then
raw and mux inputs must produce two consecutive clear samples `0.05 s` apart
within a `1.0 s` post-retract timeout matching the configured HAL release-ignore
duration used at that time. The prepared Attempt-7 baseline contract is the
10-second quarantine, monitor-only event latch, and separate 20-second clear
interval documented above.

On `2026-08-22T12:53:42+07:00`, the exact revised qualifier, verifier, and paired
runner were selected in the live idle LinuxCNC session without a message or any
position/state change; `blank.ngc` was restored. This load-only preview exits at
the preview guard and is not guarded-body execution. Static review separately
confirmed the runner's 239-character maximum line, balanced O-words, and exact
46-field logger/header mapping; the analyzer self-test passed.

The first S1 Stage A invocation exposed a queued-motion synchronization error
after a valid top contact; the second retained one valid B0/C0 row before a
software-only C-SSI polarity rejection at C90. Both defects were corrected and
attempt 3 completed all five accepted rows. Its center displacement relative to
the opening/closing C0 mean reached `0.050691 mm` at C90, `0.069135 mm` at C180,
and `0.028643 mm` at C270. Directional sphere diameters ranged from
`30.126330` to `30.279693 mm`; that bias remains diagnostic and is not a claim
of 10 um sphere-diameter accuracy. S1 Stage B then passed its prepared closure
and production-envelope gates. A laser-cutter false trigger caused an external
pause during row 9 while the machine was stationary before the next `G38.3`;
the resumed live guard verified all probe inputs clear, and the operator
confirmed there was no CNC or measurement interference. Keep the event as
provenance and keep EMI sources inactive during remaining probing. S1 Stage
C-low attempt 1 later logged canonical rows 1-13 and aborted before logging row
14 when the immediate post-top-retract guard sampled the wireless probe during
the HAL's designed release window. The raw, muxed, and motion inputs were clear
immediately afterward. The partial is preserved and excluded from accepted
analysis. The owner/operator explicitly waived the unexecuted post-abort T3
ring attempt 10 because its incremental evidence is not justified by this
machine's capability; there was no ring motion or new row, and attempt 9 remains
the S1 installation reference. This waiver does not accept or splice the
partial. Prepared mode-17 attempt 2 was load-checked, then superseded without
axis/probe motion or a CSV row. It is preserved and retired; any future restart
must use attempt 3 after separate review.

Analyze an isolated, source-order campaign copy from an existing run directory
with:

```bash
RUN_DIR="configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260821_HHMM_T3_T4_T3"
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_long_short_pair.py \
  "$RUN_DIR/tcpc-long-short-pair-campaign.csv" \
  --output "$RUN_DIR/tcpc-long-short-pair-derived.csv"
```

Analyzer exit `0` means its logged-data acceptance gates passed, exit `1` means
a live-state or acceptance gate failed, and exit `2` means the input, schema,
sequence, or I/O was invalid. Even exit `0` validates only logged CSV structure, state,
sequence, QA fields, linear-axis consistency, and paired calculations. The
derived data reports absolute `L - bracketed-short` center offset separately
from the B0-referenced pose-dependent difference. It cannot validate the mandatory
manifest, ring/probe identity, file hashes, mechanics, temperature, artifact
movement, or clearances, and it does not accept a calibration or release a
tool for production. Ring and S1 Stage A sphere motion occurred in the recorded
campaign; no machine-model fit or live calibration change has occurred.

## B/C SSI Homing and Zero Verification - 2026-05-07 +07

The B and C axes use direct single-turn SSI encoder feedback at the rotary
output. The calibrated zero constants live in the shared SSI HAL:

- `b_ssi_zero.in1`
- `c_ssi_zero.in1`

The TCPC overlay flips the B convention to match TCPC sign convention, so it
also overrides the B SSI scale and `b_ssi_zero.in1`.

Both Probe Basic SSI configs now use:

```ini
HOME_ABSOLUTE_ENCODER = 2
```

for `[JOINT_3]` and `[JOINT_4]`. This prevents immediate homing from masking a
wrong rotary position by declaring the current B/C position to be zero. After
homing, B/C displayed machine position should therefore match the SSI-derived
zeroed angle. If the rotary is not truly at B0/C0, the DRO should show the
residual instead of silently creating a new home offset.

A no-motion check program is available:

```ngc
nc_files/calibration/rotary_ssi_zero_verify.ngc
```

Run it after homing when B/C are expected to be at machine zero. It aborts if
either SSI channel is invalid or if `joint.3.motor-pos-fb` /
`joint.4.motor-pos-fb` is more than `0.020 deg` from zero.

## Persistent Refined TCPC Candidate - 2026-05-07 +07

The refined B-harmonic/B-cross correction has been moved from manually gated
diagnostic use into the persistent TCPC work config. This does not mark the
machine as released for production; it means all remaining TCPC/TWP
commissioning runs now exercise the full fitted correction by default.

Startup behavior in `5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`:

- base fixed-tip correction remains active:
  - `cal-c-to-b.x = 0.035886006`
  - `cal-c-to-b.y = 0.009526306`
  - `cal-b-to-tool.z = 0.815000`
  - `c-zero-offset = -0.024500`
- refined fitted coefficients from
  `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal` are
  copied into this real-machine TCPC work HAL
- `headheadkins.sim-bharm-enable = 1` at startup
- `headheadtwp.use_external_tool_offset = 1`, with
  `headheadkins.tool-offset.*` netted into `headheadtwp.external_tool_offset_*`
- `motion.tooloffset.x/y/z` is netted into
  `headheadkins.active-tool-offset.x/y/z`
- `headheadkins.nominal-b-to-tool.z` is now the B-axis centerline to spindle
  nose, not the short-probe tip; the previous short-probe baseline
  `-308.980001` had T3 H3 `128.606729 mm` removed, giving `-180.373272`

The enable pin still has the historical `sim-bharm-enable` name, but it is now
the persistent fitted-correction enable for this TCPC work config.

## Production TCPC Entry/Exit - 2026-05-07 +07

This section is the dated TCPC commissioning record. Its TCPC entry/exit rules
remain relevant, but its TWP lockout and combined TCPC/TWP program examples are
superseded by `TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md`.

Production entry/exit behavior is now implemented in the real-machine remap:

- `G43.4` checks that the machine is enabled, all five joints are homed, TWP is
  not active/defined, no nonzero `G52/G92` offset is active, and B/C are at
  `B0.0000 C0.0000` within `0.005 deg`.
- `G43.4` is idempotent while TCPC is already enabled only if B/C are still at
  `B0 C0`; repeated `G43.4` away from the zero entry pose is rejected.
- on first `G43.4`, `headheadtwp` stores the zero B/C TCPC entry orientation
  and stores the current tool-offset vector as `tcpc_origin`.
- `headheadkins` subtracts `tcpc-origin` while TCPC/TWP are active, so the
  current program position and physical joints remain continuous when TCPC is
  entered live.
- `G49.1` is idempotent while TCPC is already disabled.
- `G49.1` is rejected while TWP is active or still defined; run `G69` first.
- `G49.1` is rejected unless B/C have returned to the saved TCPC entry
  orientation within `0.01 deg`; this prevents the old exit discontinuity.
- ordinary tool-length changes (`G43`, `G43.1`, `G43.2`, and `G49`) are
  rejected while TCPC is active; apply `G43 Hn` before `G43.4`, and clear tool
  length with `G49` only after `G49.1`
- `M6` and `M61` are rejected while the guarded TCPC state is active, before
  physical/current tool state can change; exit with `G49.1` first
- active `G43 Hn` length is included in the head-head kinematics as local tool
  length, so the same B-to-spindle-nose geometry can handle different tools
- at this 2026-05-07 stage, `G68.2` TWP entry was temporarily disabled pending
  continuity work; that historical lockout was later replaced by the separate
  synchronized TWP implementation and dedicated supervised INI
- the TCPC tool-length guard is enabled by
  `headheadtwp.tcpc_tool_length_guard`; the real fail-safe state wrapper sets
  this pin true so the interpreter blocks tool-length changes only for guarded
  TCPC configs
- the TCPC config intentionally leaves `ON_ABORT_COMMAND` unset; abort recovery
  is manual so automatic cleanup cannot hide or disturb active TCPC/tool-length
  state. Return B/C to `B0 C0`, run `G49.1`, and only then clear tool length
  with `G49` if required.

TCPC-only program envelope:

```ngc
G17 G21 G40 G49 G54 G64 P0.001 G80 G90 G92.1 G94
(machine enabled and homed before this program starts)
Tn M6
G43 Hn
G0 B0 C0
G43.4
(normal TCPC work only)
G0 B0 C0
G49.1
G49
M30
```

Do not extend this TCPC envelope with `G68.2`. Indexed TWP uses ordinary
`G43 H`, public `G43.4` off, world B/C preposition, `G68.2`, `G53.1`, local
motion, and `G69` as defined by the current TWP contract.

Historical production-release items that were open at this stage:

- restart LinuxCNC before testing; currently running processes do not pick up
  rebuilt kinematics/interpreter code
- validate the spindle-nose split with tool 3 active: `G43 H3` before `G43.4`
  should reproduce the previous short-probe TCPC fit
- run the no-cut smoke program and one active-`G43 H3` sphere validation pass
- current production guidance remains that tool changes/current-tool changes
  happen outside TCPC; guarded TCPC, TWP, and spindle-active lockouts now
  enforce that state order
- execute the reviewed T3/T4/T3 plan above after independent probe
  qualification and collision-clearance dry runs

Legacy prototype-era headless regression added:

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-tcpc-entry-exit
rm -f sim.var
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

This test verifies fail-safe startup, `G43.4` entry continuity, idempotent
`G43.4`, `M6`/`M61` and ordinary `G49`/`G43.1` rejection while TCPC is active,
rotary TCPC compensation, unsafe `G49.1` rejection away from entry B/C,
continuous `G49.1` exit after returning to entry B/C, `G68.2` rejection while
TCPC is off, and `G49.1` rejection while TWP is active.

Machine no-cut smoke program:

- `nc_files/calibration/tcpc_production_entry_exit_smoke.ngc`
- start homed, machine enabled, at safe clearance near `B0 C0`, with TCPC off
- a real tool must be loaded and selected; the smoke program applies
  `G43 H#<_current_tool>` before `G43.4`
- the program checks HAL state and displayed XYZ continuity around `G43.4` and
  `G49.1`
- `#5403` is the selected/current tool table Z length, not proof that active
  G43 compensation is still applied; active compensation is verified after the
  program through `motion.tooloffset.z`
- the TCPC status tab displays `Active TLO X/Y/Z` from the live
  `motion.tooloffset.*` HAL pins because the UI's modal `G49/G43` state can
  disagree with active motion compensation after an abort or queued cleanup
- the program moves to explicit `B0 C0` before `G43.4` and returns to explicit
  `B0 C0` before `G49.1`; this avoids inheriting small SSI homing reference
  offsets as the TCPC entry orientation
- `nc_files/calibration/tcpc_production_entry_exit_preserve_tool_smoke.ngc`
  is the companion check that exits TCPC with `G49.1` but intentionally does
  not run final `G49`; after it completes, `motion.tooloffset.z` must still
  show the active tool length

Real-machine result, 2026-05-07 08:24 +07:

- TCPC Probe Basic started fail-safe with `TCPC OFF`
- machine homed normally
- live HAL confirmed TCPC off, TWP off, all joints homed, machine enabled
- `B` command state reported as wrapped `360.02 deg`, equivalent to B0 for the
  smoke start; the smoke program now normalizes B/C before the start check
- `nc_files/calibration/tcpc_production_entry_exit_smoke.ngc` ran and completed
  successfully on the real machine
- this validates the basic production path:
  `G0 B0 C0 -> G43.4 -> small B/C TCPC move -> return B0 C0 -> G49.1`

Real-machine G49.1 guard result, 2026-05-07 08:26 +07:

- `nc_files/calibration/tcpc_production_g49_guard_smoke.ngc` intentionally
  attempted `G49.1` at `B5 C5`
- the remap correctly rejected the exit with:
  `G49.1 requires B/C back at the TCPC entry orientation`
- live state after the intentional error was TCPC still enabled, TWP off, and
  B/C still away from the entry orientation; recover with MDI `G0 B0 C0`,
  then `G49.1`
- the test also exposed that automatic abort subroutine lookup was unreliable
  in this TCPC config. `ON_ABORT_COMMAND` is now intentionally unset; TCPC abort
  recovery is manual and state must be checked through TCPC status plus
  `motion.tooloffset.*`.

Follow-up recovery/status check, 2026-05-07 21:02 +07:

- after the intentional `G49.1` guard error, operator recovery with
  `G0 B0 C0`, `G49.1`, then `G49` worked as expected
- HAL confirmed `headheadtwp.tcpc_enabled = FALSE`,
  `motion.tooloffset.z = 0`, and B/C current joints at `0/0`

## Servo Motion Checks - 2026-05-08 +07

Servo tuning work is being done only in this TCPC work config. The shared
SSI/3-axis Probe Basic config remains unchanged for normal 3-axis work.

Important measurement limit: X/Y/Z are open-loop at the LinuxCNC level in this
configuration. The logger records LinuxCNC command versus Mesa stepgen
position feedback for X/Y/Z, not true motor encoder position. Those logs are
valid for checking trajectory generation, stepgen limits, following-error
math, and commanded step rate/acceleration headroom, but the servo amplifiers
still need operator observation or separate fault/status logging. B/C feedback
is the direct SSI rotary output feedback.

Future servo upgrade direction: replace stepgen-level X/Y/Z drive control and
diagnostics with direct communication to the servo amplifiers. The useful
production signals are actual drive position/velocity, drive following error,
torque/current/load, temperature, warning/fault bits, and fault history. That is
the correct path for final servo health monitoring; the current Mesa stepgen
logs are only a commissioning aid.

Added no-probe/no-TCPC logging helpers:

- `scripts/tcpc_servo_logger.py`
- `scripts/analyze_tcpc_servo_log.py`
- `nc_files/calibration/tcpc_servo_tune_linear_small_motion.ngc`
- `nc_files/calibration/tcpc_servo_tune_linear_ramp_motion.ngc`
- `nc_files/calibration/tcpc_servo_tune_linear_limit_motion.ngc`
- `nc_files/calibration/tcpc_servo_tune_rotary_small_motion.ngc`

Baseline linear relative move check, log
`/tmp/tcpc_servo_logs/linear-small-1.csv`:

- X/Y/Z returned to the starting displayed position with LinuxCNC idle/in-pos
- max following error: X `0.000937 mm`, Y `0.010662 mm`, Z `0.000157 mm`
- max command/feedback lag during motion was about X `0.0307 mm`,
  Y `0.0405 mm`, Z `0.0300 mm`
- no B/C SSI invalid samples

Baseline rotary relative move check, log
`/tmp/tcpc_servo_logs/rotary-small-1.csv`, using the old B/C
`P=50`, `MAX_OUTPUT=8`:

- B peak following error `0.1325 deg`
- C peak following error `0.1813 deg`
- C PID output reached the old `8.0` limit during the fast C move
- no B/C SSI invalid samples

Live B/C tuning comparison:

- `P=75`, `MAX_OUTPUT=12` reduced the clean rotary peak following errors to
  B `0.0424 deg` and C `0.0480 deg`; no PID saturation and no SSI invalids
- at the active T3 offset `128.6067 mm`, this is roughly `0.095 mm` B and
  `0.108 mm` C equivalent tip error at the fastest tested rotary motion
- the slower `2 deg/s` portion was roughly `0.09 mm` equivalent tip error
- `P=100`, `MAX_OUTPUT=12` was worse, increasing rotary error to about
  `0.15 deg`; do not use that setting as the next candidate

Current persistent TCPC work-config rotary candidate:

- `[JOINT_3]` B: `P = 75.0`, `MAX_OUTPUT = 12.0`
- `[JOINT_4]` C: `P = 75.0`, `MAX_OUTPUT = 12.0`

Linear-axis motion check against the old Feb 2026 5-axis config:

- old main config reference:
  `/home/cnc5/Old System/Backup Feb 2026/linuxcnc/configs/5th_axis/5th_axis.ini`
- old main linear limits were X `250 mm/s`, `500 mm/s^2`;
  Y `250 mm/s`, `250 mm/s^2`; Z `250 mm/s`, `500 mm/s^2`
- current TCPC work config intentionally remains lower for commissioning:
  X/Y/Z `150 mm/s`, `300 mm/s^2`
- the first current-limit ramp exposed a Y stepgen headroom error:
  `[JOINT_1] MAX_ACCELERATION = 300` but `STEPGEN_MAXACCEL = 300`
- live change to `hm2_7i95.0.stepgen.01.maxaccel = 600` fixed the issue:
  Y LinuxCNC/Mesa stepgen following error dropped from `4.616 mm` to
  `0.000174 mm`
- the TCPC work INI now persists `[JOINT_1] STEPGEN_MAXACCEL = 600`;
  the shared SSI/3-axis config was not changed
- fresh restart verification confirmed the TCPC INI loads X/Y/Z stepgen
  acceleration headroom as `600/600/600`; this is no longer only a live HAL
  `setp` value
- longer linear-limit check at the current `150 mm/s` limit, log
  `/tmp/tcpc_servo_logs/linear-limit-current-150-yfix.csv`, completed cleanly:
  X stepgen following error `0.000956 mm`, Y `0.000172 mm`,
  Z `0.000178 mm`, with no PID saturation and all axes returning to the start
  position

Historical next servo/motion checks from 2026-05-08 (superseded):

- fresh restart verification completed with
  `/tmp/tcpc_servo_logs/rotary-p75-max12-fresh.csv`; the INI-loaded
  `P=75/MAX_OUTPUT=12` values were confirmed through HAL before motion
- fresh-run peak following errors were B `0.0417 deg` and C `0.0485 deg`,
  with zero PID saturation samples and zero B/C SSI invalid samples
- keep the current X/Y/Z `150 mm/s`, `300 mm/s^2` limits as the safe
  commissioning candidate unless a production path proves it needs more; the
  immediate linear defect was Y stepgen headroom, not the commanded axis limits
- keep G68.2/TWP disabled on the real machine; do not use TWP as a servo test
- after motion checks are stable, rerun the active `G43 H3` short-probe TCPC
  sphere validation as the final confirmation before production-style use
- run full real-world TCPC G-code motion checks with no tool installed before
  cutting production work; this should exercise normal post output and real
  B/C/XYZ blended motion without probing or spindle load
- fix/commission the Probe Basic tool graphic so the displayed tool follows B
  and C correctly in the TCPC config
- set up and commission the tool height setter before production tool changes
  rely on measured lengths
- flood/air auto-on is now wired in the TCPC HAL overlay: a spindle request
  forces the air output on and holds it for five seconds after spindle-off;
  the physical spindle relay/PWM enable and `spindle.0.at-speed` assert after
  a one-second air precharge delay
- no-probe TCPC entry/exit smoke was rerun after the linear motion updates,
  log `/tmp/tcpc_servo_logs/tcpc-entry-exit-smoke-after-yfix.csv`; the program
  completed with TCPC enabled during the move, TWP off throughout, probe input
  false throughout, final TCPC off, final active tool length cleared to zero,
  and B/C returned to `0/0`
- smoke log peak motion errors were X Mesa-stepgen `0.000375 mm`,
  Y Mesa-stepgen `0.000010 mm`, Z Mesa-stepgen `0.000005 mm`, B SSI
  `0.0344 deg`, and C SSI `0.0483 deg`, with no PID saturation and no SSI
  invalid samples
- the latest LinuxCNC logs contained only the intended `G49.1` guard error; no
  `Oon_abort`/abort-subroutine lookup error reappeared after unsetting
  `ON_ABORT_COMMAND`
- LinuxCNC status after homing/recovery showed `tool_in_spindle = 3` with
  `tool_offset = 0` and modal `G49`; restoring/showing T3 is acceptable, but
  production TCPC must treat active `motion.tooloffset.*`/G43 state as the
  source of truth before `G43.4`

Fresh startup/homing tool-restore check, 2026-05-07 21:10 +07:

- after a clean TCPC Probe Basic restart and homing, Probe Basic's tool table
  plugin restored the remembered spindle tool by issuing `M61 Q3 G43`
- live state became `tool_in_spindle = 3`, modal `G43`, and
  `motion.tooloffset.z = 128.6067` while TCPC remained off
- this is desired production safety behavior: if the machine is powered up with
  a physical tool still in the spindle, startup/homing should restore tool
  compensation before normal operator commands can crash the loaded tool
- do not disable `remember_tool_in_spindle` for the production TCPC config;
  instead, TCPC programs and checks must verify the live active TLO before
  `G43.4` and keep all `G43`/`G49` changes outside active TCPC

Historical TWP entry fault, 2026-05-07 21:20 +07:

- TCPC-only smoke checks passed, including the preserve-tool path that leaves
  T3/G43 active after `G49.1`
- `G68.2 B0 C0` while TCPC was off correctly raised
  `TWP mode enable requested while TCPC mode is not enabled`
- after `G43.4`, a subsequent `G68.2 B0 C0` caused XYZ following errors and
  dropped X/Y homing, even though final HAL state had TCPC off, TWP off, B/C at
  zero, and T3/G43 still active
- the real-machine remap now rejects all `G68.2` TWP entry attempts with a
  production lockout message until the TWP entry-continuity path is fixed and
  validated offline
- do not resume TWP tests on the machine from this session; close/restart and
  re-home before any further machine motion

Offline TWP continuity reproducer, 2026-05-08:

- added `tests/kinematics/head-head-twp-active-tool-continuity/` to exercise
  the original sim `G68.2` implementation with real-machine-style geometry,
  active `G43` tool length, and `headheadtwp.use_external_tool_offset = 1`
- the reproducer verifies three cases with joint-command continuity:
  active `G43 H1` then `G43.4`, a failed pre-TCPC `G68.2 B0 C0` followed by
  `G43.4`/`G68.2`, and a back-to-back `G43.4` + `G68.2 B0 C0` burst
- all offline cases were continuous within `0.005 mm`, so the real following
  error is not reproduced by active tool length alone or by the simple queued
  MDI sequence
- next TWP work should add real-machine instrumentation around entry
  transient state and only then prepare a dedicated no-cut retest; the
  production `G68.2` lockout remains in force

Startup fault, 2026-05-08:

- the first real-machine TCPC config launch after the offline tests opened
  Probe Basic but LinuxCNC tore down the Mesa hostmot2 driver during startup;
  Probe Basic then reported `linuxcnc.error: Error buffer invalid`
- `/tmp/linuxcnc.print.*` showed `hm2_eth` could not execute `iptables`
  while setting up its Ethernet packet filter rules
- installing the Debian `iptables` package restored `/usr/sbin/iptables`; the
  next launch created `linuxcncsvr`, `milltask`, `io`, `halui`, realtime, and
  Probe Basic normally

TCPC preserve-tool smoke, 2026-05-08:

- `tcpc_production_entry_exit_preserve_tool_smoke.ngc` passed on the real
  machine after startup tool restore loaded T3 and applied `G43 H3`
- final controller state was all axes homed, in position, `B0 C0`, TCPC off,
  TWP off, T3 still loaded, and `motion.tooloffset.z = 128.6067`
- the production smoke programs now include preview guards so Probe Basic's
  3D backplot does not run the live `_current_tool`/TCPC assertions while
  loading the files
- next live check is the short-probe sphere validation with active `G43 H3`
  and TCPC enabled with `G43.4`; TWP/`G68.2` remains disabled

No-probe TCPC checks, 2026-05-08:

- added and ran `tcpc_production_no_motion_state_smoke.ngc`; it contains no
  `G0`, `G1`, `G38`, or pause moves and only verifies active tool length,
  `G43.4` entry, displayed XYZ continuity, `G49.1` exit, and preserved G43
  tool length
- live result: start and end pose stayed
  `X468.776624 Y323.677576 Z-149.420448 B0 C0`; T3/G43 remained active with
  `motion.tooloffset.z = 128.606729`, TCPC off, and TWP off
- no-motion MDI guard sequence passed: while TCPC was active, `G43 H3` and
  `G49` both rejected with the tool-length guard message, and `G68.2 B0 C0`
  rejected with the production TWP lockout message; `G49.1` then exited
  cleanly with no position change
- no-motion idempotency sequence passed: `G68.2 B0 C0` rejected while TCPC was
  off, `G49.1` did not disturb the already-off state, repeated `G43.4` at
  `B0 C0` kept TCPC active without position change, and repeated `G49.1`
  exited/held off cleanly
- probing validation is deferred until after servo motion and machine behavior
  work is complete and the physical probe is installed; keep TWP/`G68.2`
  motion disabled on the real machine

Spindle air/flood interlock, 2026-05-10:

- implemented only in the TCPC Probe Basic overlay; the shared SSI/3-axis HAL
  still keeps the original direct `M8` flood wiring
- the TCPC overlay now unlinks the base spindle relay, PWM enable,
  `spindle.0.at-speed`, and flood SSR pins, then re-drives them through the
  local interlock
- `M8` still turns flood/air on manually, but `M3`/spindle-on also forces the
  same output on so bearing air does not depend on an operator remembering
  coolant
- the physical spindle enable path is delayed by one second after the raw
  spindle-on request; this gives the air output a precharge window before the
  spindle relay/PWM enable and the synthetic at-speed signal assert
- after spindle-off, the forced air request remains active for five seconds
  unless `M8` is still holding the output on manually
- initial restart caught a HAL load-order conflict with pendant pause wiring
  already using `or2.1`; the TCPC air interlock now uses its own named
  `logic` OR component instead
- restart validation confirmed the named `logic` OR loads cleanly; next live
  validation should confirm `M8`, `M9`, `M3`, and `M5` behavior with the
  spindle clear and supervised

Probe Basic backplot restoration, 2026-05-10:

- loaded G-code text was visible but the VTK loaded-program path was missing
  after the head-head TCPC tool display changes
- QtPyVCP `VTKCanon` had an instance attribute named `tool_offset`, which
  shadowed the canonical `tool_offset()` callback used by the interpreter when
  startup `G49` runs; the attribute was renamed so `G43`/`G49` preview callbacks
  remain callable
- the LinuxCNC HAL-based TWP/TCPC tool-length guards now return false inside
  the UI preview interpreter (`_task == 0`) and remain active in milltask; this
  prevents preview-only `G49` startup parsing from consulting live HAL guard
  state while preserving production lockouts for executed G-code
- final visual check after restart showed the loaded program path rendered in
  Probe Basic again, and `qtpyvcp.log` no longer reported `CANON ERROR` during
  file load

## Pause Status - 2026-04-27 10:50 +07

TCPC work was paused so the machine can be prepared for later 3-axis work.

Runtime state before pausing:

- the TCPC Probe Basic config launched successfully after the HAL load-order
  fix and the compact UI indicator fix
- `headheadtwp.tcpc_enabled = FALSE`
- `headheadtwp.motion_enabled = FALSE`
- no fitted starting geometry had been applied live at the pause point
- live `headheadkins` geometry remained at the provisional startup values:
  - `nominal-c-to-b = X0.000000 Y0.000000 Z-270.000000`
  - `nominal-b-to-tool = X2.000000 Y-22.000000 Z-305.517000`
  - `b-zero-offset = 0.000000`
  - `c-zero-offset = 0.000000`
  - all `cal-c-to-b` and `cal-b-to-tool` corrections `0.000000`
- `motion.tooloffset.z` was present but `0.000000` and is not currently wired
  into `headheadkins`

For normal 3-axis work, do not use this TCPC config. Close it and launch one of
the existing `trivkins` maintenance/setup configs.

`G55` is locked out for staff 3-axis setup work as of 2026-04-27. Do not use,
probe, overwrite, or otherwise modify `G55` from TCPC calibration or validation
work until the operator explicitly releases it.

## Runtime Update - 2026-04-27 18:55 +07

Slow no-cut TCPC visual checks passed for:

- `B2/B0` at `C0`
- `B5/B0` at `C0`
- `B2/B0` at `C90`
- `B2/B0` at `C180`

The attempted positive C quadrant continuation exposed a C feedback wrap issue:
with the physical C axis just over `+180 deg`, the single-turn SSI path reported
about `-178 deg`. LinuxCNC then saw a near-360 degree joint-4 following error
even though the servo drive had no alarm.

Fix applied in this TCPC config only:

- added realtime HAL component `rotaryunwrap`
- rewired C feedback as:
  `c_ssi_axis_scale.out -> c_ssi_unwrap.wrapped -> c_ssi_unwrap.unwrapped -> c-pos-fb`
- `c_ssi_unwrap.command` follows `c-pos-cmd`
- `c_ssi_unwrap.wrap-period = 360.0`

This is command-referenced continuous feedback, not persistent multi-turn
absolute position. Restart this test config with C at a known safe side of the
wrap, preferably C0. If LinuxCNC is restarted while physical C is beyond the
single-turn wrap, verify the displayed C convention before commanding C motion.

After restart at C0, verified:

- `rotaryunwrap` loaded
- `c_ssi_unwrap.correction = 0`
- `c_ssi_unwrap.unwrapped` is writing `c-pos-fb`
- `joint.4.motor-pos-fb` matches the unwrapped SSI feedback near C0
- `headheadtwp.tcpc_enabled = TRUE`

Validation completed after homing all axes:

```ngc
G21 G90 G94
F50
G1 C170
G1 C185
G1 C170
G1 C0
```

Result: passed. The C axis crossed the `+180/-180` single-turn SSI wrap without
a joint-4 following error, returned to C0, and `c_ssi_unwrap.correction`
returned to `0`.

Follow-up quadrant validation also passed at slow no-cut feed:

- `C270`, `B2`, `B0`, `C0`
- TCPC correction direction was visually correct in all four quadrants:
  `C0`, `C90`, `C180`, and `C270`
- final live state at `19:14 +07`: idle, in position, TCPC enabled, C near
  zero, `c_ssi_unwrap.correction = 0`, unwrap error about `0.00015 deg`

## First Visual Starting Geometry

The following values were derived from the saved C-sweep and curated B-vector
data as a first visual TCPC starting point. They are now the startup geometry in
`5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`, but they are not final cutting data.

Direct-vector convention for the current `headheadkins` model:

```hal
setp headheadkins.nominal-c-to-b.x 0.010934
setp headheadkins.nominal-c-to-b.y 0.000000
setp headheadkins.nominal-c-to-b.z -270.000000
setp headheadkins.nominal-b-to-tool.x -0.668710
setp headheadkins.nominal-b-to-tool.y -26.721365
setp headheadkins.nominal-b-to-tool.z -308.980001
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

Fit references:

- last complete `B0` C-sweep circle center:
  `X=305.680751 Y=326.095031`, radius `26.751963 mm`, residual about
  `+/-0.022 mm`
- curated `C0` B-sweep X/Z circle center:
  `X=305.669816 Z=-589.742446`, radius `308.963734 mm`, residual within about
  `0.020 mm`

Current calibration-correction state after discovering the old vector-sign
error:

```hal
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.000000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

The vector probing routines were corrected to match the current B-axis sign
convention before this fit. The earlier wrong-sign vector datasets are not used
for final fitting. The repeated corrected data still cannot distinguish a small
`B` zero angular error from a small B-to-tool X translation error, so this
reset intentionally clears all calibration corrections and keeps only the
nominal starting geometry.

A later test of `cal-b-to-tool.x=-0.200000` and
`cal-b-to-tool.z=+0.160000` was rejected because it increased the small-pose
validation drift. The previous retained `-0.100000/+0.030000` correction was
also cleared because it was rooted in the old wrong-sign vector data.

These values are only for slow no-cut fixed-tip visual validation. The fit still
needs repeat validation after restart and final handling of tool length before
production TCPC use.

Important limitations:

- first-pass visual validation geometry values are loaded in
  `5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`
- only the first sign-corrected small TCPC geometry correction has been fitted
  from real sphere data; it is not final cutting data
- first slow no-cut real-machine B/C direction validation has passed in all C
  quadrants, including the C wrap crossing after `rotaryunwrap`
- live `G43.4/G49.1` switching is now guarded and regression-tested, but
  first real-machine validation should still be a no-cut commissioning run
- do not use this config for unsupervised cutting until the entry/exit smoke
  path and short-probe sphere validation pass on the machine; TWP remains
  locked out until a separate continuity fix is validated

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/launch_xyzbc_ssi_tcpc_probe_basic.sh
```

First validation path:

1. Launch and confirm the machine starts with `TCPC OFF` and without enabling TWP.
2. Home all axes.
3. In MDI at safe clearance, run `G0 B0 C0`, then `G43.4`, and confirm
   `TCPC ON`.
4. Run a slow no-cut TCPC entry/exit smoke path:
   `G0 B0 C0`, `G43.4`, safe B/C move, return to `B0 C0`, `G49.1`.
5. Confirm `G43.4` is rejected away from `B0 C0`, and `G49.1` is rejected if
   B/C are not back at the entry orientation.
6. Confirm `G68.2` is rejected with the production lockout message. Do not run
   TWP motion checks on the real machine until the entry-continuity issue is
   fixed offline.

## Runtime Update - 2026-04-27 20:11 +07

Automated small-pose fixed-tip validation completed with:

- `nc_files/calibration/tcpc_small_pose_vector_sphere_auto.ngc`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-small-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-small-pose-vector-2pass-raw-points.csv`

The program ran with TCPC enabled from startup and completed:

- `B0 C0` baseline
- `B+2 C0`
- `B-2 C0`
- `B+2 C+10`
- `B+2 C-10`
- closing `B0 C0`

Accepted pass-2 center drift from the first accepted `B0 C0` baseline:

- `B+2 C0`: `0.095684 mm`
- `B-2 C0`: `0.031309 mm`
- `B+2 C+10`: `0.114722 mm`
- `B+2 C-10`: `0.132373 mm`
- closing `B0 C0`: `0.047793 mm`

Result: first real fixed-tip validation is close to the practical `0.10 mm`
target. Do not over-fit from this single run; the closing baseline repeat moved
about `0.048 mm`, and corrected sphere diameters still show probe calibration
or effective-diameter error.

Follow-up on 2026-04-28 found about `0.035-0.040 mm` X reversal lost motion and
about `0.029 mm` Y reversal lost motion at the tested location.
Commanded-distance verification is deferred until suitable tooling is available
or a distance/scale problem is suspected.

## Runtime Update - 2026-04-28 Small-Pose Repeat

Repeat automated small-pose fixed-tip validation completed with the table mold
present and B kept well inside the operator-requested `+/-50 deg` limit.

Program/feed state:

- `nc_files/calibration/tcpc_small_pose_vector_sphere_auto.ngc`
- probe `F50`
- linear positioning `F400`
- rotary index `F100`
- startup TCPC enabled

Accepted pass-2 center drift from the first accepted `B0 C0` baseline:

- `B+2 C0`: `0.093955 mm`
- `B-2 C0`: `0.016757 mm`
- `B+2 C+10`: `0.106861 mm`
- `B+2 C-10`: `0.111113 mm`
- closing `B0 C0`: `0.002118 mm`

Result: the current geometry is inside the `0.2 mm` practical TCPC target for
this small-pose set. The excellent closing repeat means the remaining pattern
is useful diagnostic data rather than obvious sphere/probe drift.

Current candidate causes for the remaining X-heavy error are B effective
radius, B zero/alignment, local X mechanics, and B-to-spindle centerline offset.
Legacy configs contain old `5axiskins` fractional `x-offset` values, and the
simulation notes record a previous spindle-center error of about `2 mm`, but
those old values should not be copied directly into `headheadkins`. The current
active lateral representation is `headheadkins.nominal-b-to-tool.x = -0.668710`;
adjust only after a wider B/C validation set confirms which term is dominant.

## Runtime Update - 2026-04-28 Wide-Pose Validation

First wider mixed-pose fixed-tip validation completed with:

- `nc_files/calibration/tcpc_wide_pose_vector_sphere_auto.ngc`
- `nc_files/calibration/tcpc_wide_b0c0_closure_resume.ngc`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-wide-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-wide-pose-vector-2pass-raw-points.csv`

The program ran with startup TCPC enabled, probe `F50`, linear positioning
`F400`, rotary index `F100`, and B kept inside the table-mold clearance limit.

The first full sweep stopped during closing `B0 C0` because the wireless probe
false-tripped during a non-probe move. The operator identified nearby laser
cutter interference as the likely cause. After the laser finished, the
closure-only resume file completed the missing `B0 C0` two-pass repeat.

Accepted pass-2 center drift from the first accepted `B0 C0` baseline:

- `B+5 C0`: `0.061160 mm`
- `B-5 C0`: `0.037473 mm`
- `B+5 C+20`: `0.141757 mm`
- `B+5 C-20`: `0.078422 mm`
- closing `B0 C0`: `0.007091 mm`

Result: still inside the current `0.2 mm` practical TCPC target. The strong
closing repeat means the mixed-pose error is real pose-dependent signal. The
largest error is `B+5 C+20` and is mostly XY, so the next analysis should look
at C/B geometry interaction, C-axis center/zero/alignment, head squareness, and
local X/Y mechanics before changing offsets.

Feed update for 2026-04-29 onward TCPC validation programs:

- probe feed stays `F50`
- linear positioning feed increases to `F600`
- rotary indexing feed increases to `F200`
- do not edit or reload the active program while a cycle is running

## Runtime Update - 2026-04-28 Zero-Correction Handoff

The old vector-probing sign was corrected, then all TCPC calibration
corrections were reset to zero because the previous nonzero corrections were
derived from wrong-sign data.

Current startup correction state:

```hal
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.000000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

Two corrected symmetric validation runs with zero correction completed inside
the current `0.2 mm` practical target. Tilted absolute centers repeated about
`0.013-0.019 mm`, final closing `B0 C0` repeated about `0.0015 mm`, and the
starting `B0 C0` shifted about `0.036 mm` between runs.

Decision:

- keep TCPC calibration corrections at zero for now
- do not fit new offsets from the small-angle dataset alone
- use the prepared B0 approach/reversal diagnostic next:
  `nc_files/calibration/tcpc_b0_approach_reversal_sphere_auto.ngc`
- B and C are closed-loop on direct SSI encoders at the rotary output; if SSI
  readback repeats, LinuxCNC backlash settings should not leave a static
  B/C output-position split
- trust SSI encoder data as the B/C output position, while still testing B
  zero, C zero, B/C axis alignment, head squareness, and kinematic geometry
  mapping as separate TCPC setup tasks
- future B/C feedback, backlash, and servo tuning remains a separate machine
  control workstream before production TCPC use
- for normal 3-axis work, close this TCPC config and use a `trivkins`
  maintenance/setup config
- `G55` remains reserved for staff 3-axis work unless the operator explicitly
  releases it

## Runtime Update - 2026-04-29 B/C Backlash Compensation

The B0 approach/reversal diagnostic found a repeatable split between
`B+5 -> B0` and `B-5 -> B0`:

- sphere-center X split: about `0.121722 mm`
- direct B SSI zeroed-position split: about `0.022202 deg`
- expected TCP motion at a `309 mm` lever arm: about `0.119735 mm`

This confirms the direct SSI encoder data should be trusted. The issue was that
the TCPC test config still had LinuxCNC backlash compensation active on the
rotary joints:

- previous B `[JOINT_3]BACKLASH = 0.022`
- previous C `[JOINT_4]BACKLASH = 0.010`

Because B and C feedback is from direct SSI encoders at the rotary output,
backlash compensation changes the physical output position while logical
`joint.N.pos-cmd` remains on target. For TCPC calibration that creates exactly
the approach-dependent TCP shift we measured.

Current TCPC test config:

```ini
[JOINT_3]
BACKLASH = 0.0

[JOINT_4]
BACKLASH = 0.0
```

Restart LinuxCNC before rerunning the B0 approach/reversal diagnostic; the
running session will not pick up INI changes.

Post-restart result:

- `joint.3.backlash-corr = 0`
- `joint.4.backlash-corr = 0`
- direct B SSI approach split after disabling backlash: `0.000000 deg`
- accepted sphere center approach split after disabling backlash: `0.004201 mm`

The backlash-compensation removal is validated for TCPC testing.

First post-fix symmetric TCPC validation:

- program:
  `nc_files/calibration/tcpc_symmetric_pose_vector_sphere_auto.ngc`
- probe `F50`, linear positioning `F600`, rotary indexing `F200`
- one prior attempt was invalid due to probe double-pulse noise on retract
- final complete run closed `B0 C0` at `0.004406 mm`
- tilted-pose drift from the starting `B0 C0` was about `0.089-0.102 mm`

This is inside the current `0.2 mm` practical TCPC target. The remaining
pattern is now geometry/alignment signal, not the old B backlash-compensation
artifact. Repeat the same symmetric run once before fitting new TCPC
corrections.

The immediate repeat was stable: closing `B0 C0` drift was `0.004268 mm`,
tilted-pose drift remained about `0.091-0.101 mm`, and accepted centers
repeated within about `0.006 mm` against the previous valid post-fix run.
Proceeding to the expanded C-quadrant / B `+/-50` matrix is justified before
fitting corrections.

Expanded TCPC diagnostic program prepared:

- `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc`
- C quadrants: `C0/C90/C180/C270`
- B groups: `0`, `+/-10`, `+/-30`, `+/-50`
- B0 C0 closure between groups
- probe `F50`, linear positioning `F600`, rotary indexing `F200`
- pauses between B groups with `M0`
- uses separate `tcpc-expanded-pose-vector-*` CSV logs

The calibration sphere is on a `45 deg` post. The known clearance concern is
around `C45` with B more negative than `-10 deg`; `C225` is acceptable. The
first expanded program uses C quadrants only and avoids the known risky
`C45 / B < -10` sector.

Servo tuning is a separate future scope. The B/C closed-loop SSI feedback path
is functional, but it has not been fine-tuned. Current rotary following-error
limits are loose commissioning values:

```ini
[JOINT_3]
FERROR = 2
MIN_FERROR = 0.5

[JOINT_4]
FERROR = 2
MIN_FERROR = 0.5
```

Schedule a dedicated servo-motion tuning session for all axes, especially the
B/C rotary feedback loops, before treating this config as production TCPC.

## Runtime Update - 2026-04-29 Expanded TCPC Matrix

The expanded TCPC diagnostic completed before the machine was handed back for
3-axis work:

- program:
  `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc`
- result log:
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-expanded-pose-vector-2pass-results.csv`
- rotary SSI log:
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-expanded-pose-vector-rotary-ssi-state.csv`
- result set: `64` result rows, with `32` accepted pass-2 centers
- TCPC calibration corrections remained zero for this run
- B/C backlash compensation remained disabled in this TCPC test config

Accepted `B0 C0` closures from the initial baseline:

- after B0 C-only group: `0.006710 mm`
- after B `+/-10` group: `0.011584 mm`
- after B `+/-30` group: `0.010126 mm`
- final after B `+/-50` group: `0.017328 mm`

Maximum drift from each group's preceding `B0 C0` closure:

- B0 C-only group: `0.144343 mm` at `B0 C180`
- B `+/-10` group: `0.278010 mm` at `B-10 C0`
- B `+/-30` group: `0.796227 mm` at `B-30 C90`
- B `+/-50` group: `1.316641 mm` at `B-50 C90`

The closure data is tight enough to trust the pose pattern. The large high-B
residuals are not explained by rotary following error in this run: accepted
pass-2 maximum absolute following error was about `229 microdeg` on B and
`2403 microdeg` on C.

No new TCPC geometry correction has been applied yet. Next TCPC work is offline
sensitivity fitting from the expanded matrix, followed by a small correction
and slow no-cut validation. For current 3-axis work, close this TCPC config and
use a normal `trivkins` maintenance/setup config. `G55` remains reserved for
staff 3-axis setup unless the operator explicitly releases it.

## Offline Correction Candidate - 2026-04-29

The first expanded-matrix sensitivity fit is loaded in the TCPC test overlay
for the next restart. It is still test-only and must be validated with slow
no-cut probing before any cutting use.

Candidate full simple correction:

```hal
setp headheadkins.cal-c-to-b.x -0.065000
setp headheadkins.cal-c-to-b.y 0.014000
setp headheadkins.cal-c-to-b.z 0.000000
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.815000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset -0.024500
```

These values are mirrored to the matching `headheadtwp.*` pins in
`5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`.

Expected result:

- last symmetric repeat predicted worst tilted residual: about `0.034 mm`
- expanded matrix predicted B `+/-30` worst residual: about `0.196 mm`
- expanded matrix predicted B `+/-50` worst residual: about `0.437 mm`

Validation order:

1. Restart this TCPC test config so the candidate values load.
2. Run the symmetric program first.
3. If signs and residuals improve, run the expanded program. It now defaults
   to B `+/-30` only with `#707 = 30.0`.
4. Set `#707 = 50.0` only after B `+/-30` validation passes and clearance is
   deliberately confirmed.
5. Treat remaining B `+/-50` error as likely alignment/squareness work unless
   a repeat data set shows a clean simple-offset pattern.

## Runtime Update - 2026-04-29 Correction Validation

The full simple correction candidate above was loaded and validated on the
real machine with slow no-cut sphere probing.

Current live correction state:

```hal
setp headheadkins.cal-c-to-b.x -0.065000
setp headheadkins.cal-c-to-b.y 0.014000
setp headheadkins.cal-c-to-b.z 0.000000
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.815000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset -0.024500
```

The same values are mirrored to `headheadtwp.*`.

Validation completed:

- visual TCPC correction direction checks remained correct in all C quadrants
- corrected symmetric validation passed with worst tilted-pose drift
  `0.044784 mm` and closing `B0 C0` drift `0.021471 mm`
- corrected expanded validation through B `+/-30` passed with group max drift
  `0.084764 mm` for the B0 C-only group, `0.099723 mm` for B `+/-10`, and
  `0.171569 mm` for B `+/-30`
- B `+/-30` is inside the current `0.2 mm` practical TCPC target

B `+/-50` validation result:

- first attempts were interrupted by wireless/optical probe faults reported as
  `Probe tripped during non-probe move`
- after the probe/receiver reset and the workshop closed, a clean B `+/-50`
  resume block completed
- clean block starts at data row `200` in
  `tcpc-expanded-pose-vector-2pass-results.csv`
- B `+/-30` group from the fresh `B0 C0` baseline:
  max `0.175977 mm` at `B-30 C90`, RMS `0.122098 mm`, closure
  `0.019881 mm`
- B `+/-50` group from the B30 closure baseline:
  max `0.427632 mm` at `B-50 C90`, RMS `0.266161 mm`, closure
  `0.014415 mm`
- overall start-to-final `B0 C0` closure across the clean block:
  `0.032135 mm`
- accepted pass-2 rotary following error stayed small:
  B max about `229 microdeg`, C max about `1030 microdeg`

Interpretation:

- B `+/-30` is validated inside the current `0.2 mm` practical TCPC target.
- B `+/-50` is usable diagnostic data and matches the earlier offline
  prediction closely. Remaining high-B error is more likely machine/head
  alignment, squareness, or mechanical geometry than a simple TCPC offset.

The expanded program has been restored to safe defaults:

```ngc
#706 = 1.0
#707 = 30.0
#708 = 0.0
#709 = 10.0
```

It also supports a deliberate B `+/-60` extension. For a B60-only diagnostic
after the completed B50 run, set:

```ngc
#707 = 60.0
#708 = 1.0
#709 = 60.0
```

Do not leave B60 as the default. Confirm clearance and probe receiver stability
before running it.

## Shutdown Handoff - 2026-04-30

The late-night full expanded sphere run reached B60 but was stopped by repeat
wireless/optical probe false trips. The operator observed probe flashes with no
contact. The sphere was moved after those attempts, so the next run must be a
fresh data set, not a resume from the old sphere position.

Data state:

- Current log boundary after the moved sphere:
  `tcpc-expanded-pose-vector-2pass-results.csv` line `314`,
  `tcpc-expanded-pose-vector-2pass-raw-points.csv` line `1566`, rotary logs
  line `314`.
- Rows `243-306` are the best pre-shutdown full-run block through B `+/-50`.
- Rows `307-314` are incomplete B60 attempts and should be treated as trend
  data only.
- Rows `243-306` final B0 C0 closure after B `+/-50` was about `0.010627 mm`.
- Rows `243-306` B `+/-30` remains inside the practical `0.2 mm` target; B
  `+/-50` remains outside it with about `0.355 mm` max at B+50 and `0.404 mm`
  max at B-50.
- Rotary following error was not the limiting factor: accepted pass-2 rows in
  the block stayed around B `305 microdeg` max and C `1030 microdeg` max.

Interpretation:

- There is enough data for first-pass TCPC/mechanical analysis and fault
  direction.
- There is not enough data for a final TCPC fit because B60 is incomplete, the
  sphere moved, and false trips disturbed the last attempts.
- A practical TCPC parameter fit only reduces the rows `243-306` RMS from about
  `0.155 mm` to about `0.142 mm`; do not apply new offsets from this alone.
- Treat remaining high-B residual as mixed geometry/alignment/mechanics until a
  stable repeat confirms a clean offset pattern.

Morning program state:

```ngc
#704 = 1.0
#706 = 1.0
#707 = 60.0
#708 = 0.0
#709 = 10.0
#515 = 5.0
```

This is a conservative fresh full B `+/-60` rerun with pause-before-pose and
pause-between-groups enabled, plus a +5 mm Z lift before rotary index moves.

## Diagnostic Half-Step Correction - 2026-04-30

The latest completed B `+/-90` data confirms repeatable pose-dependent error:
B0 closures stayed tight while residuals grew with B angle. A linear sensitivity
check against the modeled TCPC joint travel ranked the strongest apparent terms
as Z error with large Z travel, Y error with large Y travel, then Y/Z
squareness-type coupling. This does not prove the physical source, but it gives
a practical direction for the next small software verification.

A small half-step correction has been loaded in the TCPC test overlay only. It
is intentionally not a final compensation:

```hal
setp headheadkins.cal-c-to-b.x -0.111675
setp headheadkins.cal-c-to-b.y 0.004925
setp headheadkins.cal-c-to-b.z 0.000000
setp headheadkins.cal-b-to-tool.x 0.064339
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.757746
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset -0.024800
```

The same values are mirrored to `headheadtwp.*`.

Predicted effect against the latest clean group-baselined data:

- B `+/-30`: RMS `0.115 mm` to `0.113 mm`, max `0.163 mm` to `0.154 mm`
- B `+/-50`: RMS `0.244 mm` to `0.214 mm`, max `0.390 mm` to `0.305 mm`
- B `+/-60`: RMS `0.317 mm` to `0.265 mm`, max `0.534 mm` to `0.440 mm`
- B `+/-90`: RMS `0.566 mm` to `0.477 mm`, max `0.891 mm` to `0.774 mm`

The active expanded program has also been reset out of the temporary B90 resume
state:

```ngc
#704 = 0.0
#706 = 1.0
#707 = 60.0
#708 = 0.0
#709 = 10.0
#710 = 0.0
#515 = 25.0
```

Validation intent:

- restart the TCPC test config so the new values load
- run only slow no-cut probing
- first confirm B `+/-30` does not get worse
- then compare B `+/-50` and B `+/-60` against the prior data
- if high-B residuals do not reduce in the predicted direction, revert this
  half-step and prioritize mechanical/linear-axis alignment tests

## Historical Probe Gate Runtime Note - 2026-04-30

The supervised probe-gate process is working well for the current TCPC probing:
the active program enables `motion.digital-out-00` only during the actual
`G38.3` probe move and disables it immediately after contact. This prevented
the repeated false/double pulse from stopping transport and retract moves.

Operator observation from the last full run:

- the wireless probe flashed a second time about `3-4` times after contact
- this did not stop the gated program
- likely cause is low battery alarm behavior rather than a real second touch

Future probe robustness task:

- add a timed post-contact gate, about `2-3 seconds`, after a valid probe hit
- ignore/block additional probe pulses during that window
- log or display a non-stopping operator warning such as suspected probe low
  battery/double pulse
- keep real probe-hit safety active during every intentional `G38` move
- treat this as a separate task from TCPC geometry fitting

Implemented disposition on `2026-08-22`: campaign 2026082202 showed that a
`1.0 s` ignore was insufficient. The current realtime gate admits probe input
only for actual G38 motion, uses a `10.0 s` post-contact abnormal-monitor
quarantine, stretches a later event for `0.5 s` without pausing the
interpreter, and requires a separate `20.0 s` continuously clear proof before
the next G38 in the dedicated Attempt-7 sphere runners.

## Half-Step Verification Result - 2026-04-30

The diagnostic half-step above was tested through B `+/-50` and then stopped.
The result is a failed direction test:

- new run starts at `tcpc-expanded-pose-vector-2pass-results.csv` data row
  `432` / file line `433`
- B0 C-only sweep stayed stable: prior RMS `0.101 mm`, new RMS `0.098 mm`
- B `+/-30` worsened: RMS `0.115 mm` to `0.143 mm`, max `0.163 mm` to
  `0.216 mm`
- B `+/-50` worsened: RMS `0.244 mm` to `0.297 mm`, max `0.390 mm` to
  `0.497 mm`
- B0 closures remained good, so the failed result is a useful correction-sign
  diagnostic rather than a general repeatability failure

The failed half-step mainly pushed the tilted-pose residuals farther in the
same direction. Linear projection of old-to-new residuals predicts that the
opposite empirical half-step should improve the same B `+/-30` and B `+/-50`
groups:

- B `+/-30`: predicted RMS about `0.107 mm`, max about `0.134 mm`
- B `+/-50`: predicted RMS about `0.213 mm`, max about `0.286 mm`

The TCPC test overlay has therefore been prepared for the next session with the
opposite empirical half-step:

```hal
setp headheadkins.cal-c-to-b.x -0.018325
setp headheadkins.cal-c-to-b.y 0.023075
setp headheadkins.cal-c-to-b.z 0.000000
setp headheadkins.cal-b-to-tool.x -0.064339
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.872254
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset -0.024200
```

The same values are mirrored to `headheadtwp.*`.

The expanded program is now set to B `+/-30` only for the next first check:

```ngc
#704 = 0.0
#706 = 1.0
#707 = 30.0
#708 = 0.0
#709 = 10.0
#710 = 0.0
#515 = 25.0
```

Next-session rule:

- restart the TCPC config before running so the opposite correction loads
- run the B `+/-30` check first
- if B `+/-30` is worse than the prior validated candidate, revert to:
  `cal-c-to-b.x=-0.065000`, `cal-c-to-b.y=0.014000`,
  `cal-b-to-tool.x=0.000000`, `cal-b-to-tool.z=0.815000`,
  `c-zero-offset=-0.024500`
- if B `+/-30` improves, extend deliberately to B `+/-50`; do not run B60
  until B50 confirms the direction

## Current Hold Status - 2026-05-02

The opposite empirical half-step was rejected after the 100% feed override
rerun. B `+/-30` and the B0 C-only sweep were both worse than the prior
validated candidate, so the TCPC test config has been reverted to:

```hal
setp headheadkins.cal-c-to-b.x -0.065000
setp headheadkins.cal-c-to-b.y 0.014000
setp headheadkins.cal-c-to-b.z 0.000000
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.815000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset -0.024500
```

The same values are mirrored to `headheadtwp.*`.

The active expanded program is prepared for a clean B `+/-30` validation rerun
only:

```ngc
#506 = 50.0
#507 = 1200.0
#705 = 200.0
#707 = 30.0
```

The first reverted rerun was stopped during the B-30 group because the wireless
probe showed a constant low-battery flash. Do not use that interrupted run for
TCPC fitting. Resume TCPC calibration only after new probe batteries are fitted,
then rerun B `+/-30` at 100% feed override before expanding range again.

Shutdown handover, 2026-05-02 20:50 +07:

- replacement probe batteries are several days away
- PC shutdown is safe from the repository/config side
- after restart, launch only one TCPC Probe Basic instance, home, verify probe
  parameters, and rerun the current B `+/-30` validation before any further
  fitting

## Current Probe Validation Handoff - 2026-05-04

The 2026-05-02 hold status above has been superseded by later probe runs and
offline fitting.

The non-persistent decision recorded in this section has also been superseded:
as of 2026-05-07 the refined B-harmonic/B-cross candidate is persistent and
enabled in this TCPC work config for continued commissioning.

Startup HAL is now prepared with the validated C-center correction:

```hal
setp headheadkins.cal-c-to-b.x 0.035886006
setp headheadkins.cal-c-to-b.y 0.009526306
setp headheadtwp.cal_c_to_b_x 0.035886006
setp headheadtwp.cal_c_to_b_y 0.009526306
```

The earlier high-B B-harmonic-only candidate passed offline math checks and a
dedicated LinuxCNC sim fixed-tip smoke test with `0.000000000 mm`
disabled/enabled TCP error, but the later refined B/C cross candidate replaced
it as the persistent work-config candidate.

Current live decision after the C0/C180/C90/C270 candidate-on validations and
offline B/C cross fitting:

- keep only the validated C-center correction
- keep `headheadkins.sim-bharm-enable = FALSE`
- do not make any B-harmonic or B/C cross candidate persistent
- restart this config before the next candidate test so the new
  `headheadkins.bcross.*` pins exist

Reason:

- candidate-on C0/C180 combined non-B0 RMS/max was
  `0.128105 / 0.228885 mm`
- candidate-on C90/C270 side-quadrant RMS/max was
  `0.408282 / 0.615783 mm`
- the side result shows the machine-fixed B-harmonic candidate is not a general
  TCPC correction

Latest B/C cross candidate result:

- manual HAL file:
  `configs/sim/head_head_5axis/head_head_bharmonic_candidate.hal`
- the live `#711 = 4.0` C0 + C180 + C90/C270 validation completed
- measured all-validation RMS/max: `0.096378 / 0.176626 mm`
- measured C90/C270 side RMS/max: `0.079909 / 0.105982 mm`
- worst remaining point: `B+60 C180` at `0.176626 mm`
- the candidate remains non-persistent while the new rows are folded into the
  next offline fit

Do not enable `headheadkins.sim-bharm-enable` for normal machine use. It should
remain `FALSE` unless deliberately running a gated diagnostic candidate from
the current offline plan.

Refined B/C cross candidate result:

- refined HAL file:
  `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`
- the live `#711 = 4.0` C0 + C180 + C90/C270 validation completed
- measured all-validation RMS/max: `0.076818 / 0.125893 mm`
- the candidate is the best validated live candidate so far
- it remains non-persistent and manually gated
- offline persistence review did not justify a retune or another correction
  family
- two targeted `#711 = 5.0` repeats completed after that review:
  - repeat 1 RMS/max: `0.129502 / 0.153150 mm`
  - repeat 2 RMS/max: `0.149119 / 0.191962 mm`
- both targeted repeats were probe-clean but showed a shifted B0 reference
  state versus the earlier refined validation
- stop live probing for now; do not retune or persist the refined candidate
  until the session/reference movement is understood
- this machine has no pitch error compensation and no thermal compensation at
  this time; both are future projects
- because it is a large steel machine, thermal drift is expected and must not
  be mistaken for a head kinematics error during persistence decisions
- the shifted B0 reference may be room-temperature/machine-frame movement or a
  bumped/relaxed sphere stand; the current data cannot separate those causes
  without a short B0-only reference check
- the current TCPC data also used only one probe stickout, while
  `motion.tooloffset.z` is not wired into `headheadkins`; keep the refined
  candidate provisional until a short-probe and long-probe back-to-back
  validation passes
- current refined candidate is inside the core `0.2 mm` band for all accepted
  live plus targeted non-B0 rows
- current refined candidate is not yet a hard-max pass for the secondary
  `0.1 mm` band
- the next prepared run is the B0-only reference check in
  `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` with
  `#711 = 6.0`; keep `headheadkins.sim-bharm-enable = FALSE` for that check

Extended short-probe candidate validation:

- `headheadkins` now has additional zero-default, gated correction pins:
  `headheadkins.charm.*`, `headheadkins.bcross.sinb-sin2c.*`, and
  `headheadkins.bcross.sinb-cos2c.*`
- diagnostic candidate HAL:
  `configs/sim/head_head_5axis/head_head_short_probe_extended_candidate.hal`
- validation report:
  `configs/5th_axis_xyzbc_ssi_probe_basic/TCPC_EXTENDED_CANDIDATE_VALIDATION_REPORT.md`
- full safe-grid validation completed in two segments:
  - first segment accepted pass-2 rows `409-471`
  - resume segment accepted pass-2 rows `473-529`
- first segment stopped at `B-90 C90` pass 1 with
  `-U side touch did not record point data`; `#711 = 14.0` was added to resume
  from that point with an `8 mm` side probe vector
- total accepted candidate-on pass-2 rows: `61`
- no expected safe-grid pass-2 points are missing
- combined per-segment-reference nonzero-B RMS/max:
  `0.091875 / 0.189695 mm`
- worst vector: line `491`, `B-60 C180`,
  `dX=-0.173795`, `dY=-0.073580`, `dZ=+0.019114`,
  magnitude `0.189695 mm`
- current decision:
  - this candidate validates under the core `0.2 mm` target
  - it does not meet the secondary `0.1 mm` target everywhere
  - keep the candidate non-persistent and gated off while validation rows are
    folded into the next offline fit
- tool-state caveat:
  - UI/current tool showed tool `0`, but the program fallback logged probe tool
    `3`, probe calibration `0.134533`, and zero motion tool offsets
  - current TCPC kinematics do not use tool length compensation, so this run is
    still usable
  - fix tool state before short/long probe comparison

Extended candidate mid-B diagnostic:

- `headheadkins` now also has zero-default, gated mid-B pins:
  `headheadkins.bmid.base.*`, `.cosc.*`, `.sinc.*`, `.cos2c.*`, `.sin2c.*`
- the basis is `sin(2B)^2`, so it is zero at `B0` and `B+/-90`
- refit report:
  `configs/5th_axis_xyzbc_ssi_probe_basic/TCPC_EXTENDED_CANDIDATE_REFIT_REPORT.md`
- diagnostic HAL:
  `configs/sim/head_head_5axis/head_head_short_probe_extended_midb_candidate.hal`
- offline fit on rows `409-471` and `473-529`:
  - current candidate: `0.091875 / 0.189695 mm`
  - mid-B diagnostic candidate: `0.051958 / 0.099935 mm`
- holdouts are not strong enough to make the mid-B candidate persistent; use it
  only for one gated confirmation run
- next run should be the full safe grid:
  `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`, `#711 = 13.0`
- keep `headheadkins.sim-bharm-enable = FALSE` except during the deliberate
  diagnostic run, and disable it immediately after completion or any error

Balanced final short-probe candidate:

- report:
  `configs/5th_axis_xyzbc_ssi_probe_basic/TCPC_SHORT_PROBE_BALANCED_FINAL_REPORT.md`
- HAL:
  `configs/sim/head_head_5axis/head_head_short_probe_balanced_final_candidate.hal`
- expected combined short-probe RMS/max:
  `0.054136 / 0.110879 mm`
- this is the last planned short-probe-only confidence candidate before
  production integration work
- after this confirmation, stop TCPC probing until the long probe arrives
- next machine work should move to:
  - production Probe Basic config with TCPC/TWP
  - servo speed/acceleration tuning
  - Probe Basic setup for the real workflow

Balanced final short-probe validation result:

- result rows: `652-771`
- same-run same-C B0-reference RMS/max:
  `0.055446 / 0.113585 mm`
- B0 same-C drift reached about `0.052 mm`; operator reported elevated spindle
  temperature and possible fractional tool-tip growth
- production-required TCPC accuracy is met under the current `<0.2 mm` target
- do not continue short-probe-only TCPC refinement now
- keep future TCPC refinement for the short/long probe comparison after the
  long stylus arrives

## Probe Basic TCPC Display and B Homing Check - 2026-05-10 +07

During Probe Basic TCPC display validation, homing-all initially failed with:

```text
Exceeded POSITIVE soft limit (100.00000) on joint 3
```

The physical B axis was at B0, but the TCPC overlay's flipped B SSI mapping
reported the equivalent position as `+360.0004 deg`. LinuxCNC does not normalize
that value for joint soft-limit checks, so B was outside the configured
`-100..+100 deg` limit before X/Y/Z homing.

The TCPC overlay now keeps the same calibrated B0 equivalent near zero:

```hal
setp hm2_7i95.0.ssi.00.abs.scale 2912.711111111111
setp b_ssi_zero.in1 -177.0848
```

Restart validation after the correction:

- B joint actual after startup: `0.000390 deg`
- C joint actual after startup: `0.001007 deg`
- homing-all completed normally
- no startup or homing errors remained

Two no-tool Probe Basic display/motion checks were added:

- `nc_files/calibration/tcpc_no_tool_display_motion_check.ngc`
- `nc_files/calibration/tcpc_no_tool_display_motion_wide_check.ngc`

Real-machine no-tool result:

- tool `0`, active tool offsets zero
- TCPC entered with `G43.4` at B0/C0 and exited with `G49.1`
- Probe Basic plot/tool followed B/C motion correctly after the QtPyVCP
  backplot patch
- small check passed through B `+/-5` and C `+/-15`
- wide check passed through B `+/-30` and C `+/-90`
- final faster segment at `F480` reached the current configured `8 deg/s`
  rotary velocity limit without visible issue
- final state after the wide check: idle, B/C command effectively zero,
  TCPC off, TWP off, active tool offsets zero, no fresh LinuxCNC errors

The QtPyVCP backplot change is in the separate local checkout
`/home/cnc5/dev/qtpyvcp`, file
`src/qtpyvcp/widgets/display_widgets/vtk_backplot/vtk_backplot.py`; it is not
part of this LinuxCNC repository.

## TCPC Combined XYZBC Motion Check - 2026-05-10 +07

Added:

- `nc_files/calibration/tcpc_servo_tune_tcpc_xyzbc_motion.ngc`

Purpose:

- no tool installed, tool `0`, active tool offsets zero
- enter TCPC at B0/C0 with `G43.4`
- move combined X/Y/Z and B/C paths while TCPC is active
- stage feeds at `F1200`, `F3000`, and `F6000`
- return to B0/C0 and exit TCPC with `G49.1`

Real-machine result:

- all three staged combined XYZBC sections ran correctly
- no visible servo issue was reported by the operator
- no XYZ following errors occurred during B/C TCPC motion
- final state: idle, in position, B/C command zero, TCPC off, TWP off,
  active tool offsets zero, no fresh LinuxCNC errors

This is the first positive check that the current conservative XYZ acceleration
and rotary limits are compatible with TCPC-driven linear compensation for
small production-style 5-axis moves. Future speed increases should still be
made incrementally while watching for linear-axis following errors and rotary
servo amp faults.

## TCPC Active Tool-Length and Probe Basic Tip Display - 2026-05-10 +07

Validated active `G43 H3` TCPC behavior with no physical tool installed.

Added checks:

- `nc_files/calibration/tcpc_h3_b0_b90_z_log_check.ngc`
- `nc_files/calibration/tcpc_h3_b45_c45_tip_hold_check.ngc`
- `nc_files/calibration/tcpc_h3_tool_length_visibility_check.ngc`
- `nc_files/calibration/tcpc_servo_tune_tcpc_xyzbc_h3_motion.ngc`

Findings:

- `G43 H3` loads `motion.tooloffset.z = 128.606729` and feeds
  `headheadkins.active-tool-offset.z`
- machine motion confirms TCPC includes the active tool length, not only the
  spindle-nose B-to-tool vector
- the simple B0/B90 test showed the expected large Z compensation with H3
  active; spindle-nose-only compensation would have been about `180 mm`, while
  H3-active compensation is about `309 mm`
- the B45/C45 tip-hold check looked correct on the machine and in Probe Basic:
  the TCP stayed fixed while the top of the displayed tool moved through the
  rotary arc
- final state after the B45/C45 check: B0/C0, TCPC off, TWP off, active tool
  offsets zero
- final post-push smoke check: B0/B90 and B45/C45 H3 display checks both
  looked correct in Probe Basic; each finished with B0/C0, TCPC off, TWP off,
  active tool offsets zero, and no LinuxCNC errors

QtPyVCP Probe Basic display fixes are in `/home/cnc5/dev/qtpyvcp`:

- `vtk_backplot/linuxcnc_datasource.py` now returns the current tool-offset
  value tuple from `getToolOffset()`
- `vtk_backplot/vtk_canon.py` skips ordinary 3-axis tool-offset path shifting
  for the head-head XYZBC kinematics
- `vtk_backplot/vtk_backplot.py` keeps breadcrumbs at the reported TCP and
  uses the head-head TCPC tool display path
- `vtk_backplot/tool_actor.py` adds a head-head TCPC tool-bit actor that draws
  a tube from the TCP tip to the calculated tool-holder end, so the displayed
  tip remains anchored while B/C rotate

This is display-only work in QtPyVCP; it does not affect the LinuxCNC motion
path. The machine-side H3 TCPC behavior was already confirmed through live HAL
and visible motion before the final display correction.

## TCPC Tool Height Setter Prep - 2026-05-10 +07

The shared SSI Probe Basic toolsetter macros were not safe to use directly in
the TCPC work config because the TCPC overlay gates `motion.probe-input` with
`motion.digital-out-00`. Without opening that gate around the toolsetter
`G38` move, the wired toolsetter input would be blocked.

Added TCPC-local subroutine overrides in
`configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/subroutines/`:

- `probe_spindle_nose.ngc`
- `tool_touch_off.ngc`
- `tool_setter_param_update.ngc`

These shadow the shared Probe Basic subroutines only in the TCPC config because
the TCPC config's `[RS274NGC] SUBROUTINE_PATH` searches its local subroutine
directory first. The shared SSI/3-axis config is unchanged.

Behavior added for the TCPC-local toolsetter macros (the `M64/M65` details in
this historical list are now superseded by the real-time gate described below):

- reject the toolsetter routines if TCPC is enabled
- reject if TWP motion is active
- reject unless B and C are within `0.05 deg` of zero
- clear legacy motion digital output P0 before setup and after probing with
  `M65 P0`
- check the raw toolsetter input is clear before each probe stroke
- retain the historical `M64/M65 P0` sequence, although those commands no
  longer authorize the physical probe gate
- use `G38.3` plus explicit `#5070` checks so a no-contact event can close the
  probe gate before aborting
- make the tool touch-off button compatible with the Probe Basic widget names
  such as `fast_probe_fr_3004`, `z_max_travel_3007`, and
  `spindle_zero_height_3010`
- add a TCPC-local `tool_setter_param_update.ngc` so the Probe Basic
  `UPDATE TOOL SETTER PARAMETERS` button can write the numbered toolsetter
  parameter values
- require active `G43` tool length compensation before tool touch-off and show
  a blocking `M0` warning for the operator to verify the active tool length is
  within `+/-5 mm` from holder face to tool tip before resuming
- require the active Z tool length to be at least `50.00 mm`, because no valid
  tool on this machine is shorter than that and stale zero offsets are unsafe
- leave Y at the current machine position during tool touch-off; the presetter
  only needs X and Z
- use `M66 E0 L0` sync points before HAL input checks so queued retract moves
  complete before the macro evaluates whether the setter has released
- approach the setter with the current tuned profile: `G53 Z0` and setter X at
  `F3000`, down to 200 mm above the setter at `F3000`, then down to 10 mm
  above the setter at `F1000`
- retract after each touch and return to `G53 Z0` at `F3000`

Offline interpreter preview check:

```text
/tmp/tcpc_toolsetter_subroutine_preview.ngc
```

completed without parser errors and confirmed the preview guard exits both
subroutines without trying to access live HAL pins. Full execution still needs
real-machine validation because the guarded probing path intentionally depends
on live HAL input pins.

Next toolsetter commissioning steps:

- start the TCPC Probe Basic config with B0/C0 and TCPC/TWP off
- verified on the machine that the tool presetter changes
  `hm2_7i95.0.inmux.00.input-08` / `toolset-in`
- verify the wireless/touch probe input
  `hm2_7i95.0.inmux.00.input-09` / `t_probe-in` is idle before toolsetter
  probing; the base HAL ORs both `input-08` and `input-09` into `probe-mux`
- set the tool touch position with the Probe Basic `SET TOOL TOUCH OFF
  POSITION` workflow or `G30.1` at a safe machine-coordinate location
- verify the trimmed `#3010` value below by rerunning `TOUCH OFF CURRENT TOOL`
  on T24 and confirming it returns close to `Z+138.739000`
- repeat with one short and one longer tool when available, then verify active
  `G43 Hn` TCPC motion still behaves as expected

Live commissioning note:

- The presetter was first calibrated from known tool `T24/H24`
  (`Z+138.739000`). The machine was referenced with `G59 Z0` at the top of the
  presetter, but the actual switch trip occurred at `Z-634.624733` in the
  toolsetter probing frame. The correct `#3010` spindle-zero value for the
  setter trip point is therefore `773.363733`.
- The first automatic touch-off stopped after the fast stroke because the
  earlier routine was still using the stock long fast-probe approach from
  machine Z0/G49. The TCPC-local `tool_touch_off.ngc` has been reworked to
  match the DMG-style process used here: require the active tool length to be
  manually set within `+/-5 mm`, keep `G43` active, position to the calibrated
  setter clearance, run a slow touch, retract, run a second slow touch, then
  correct the current tool length from the measured trip-point error.
- The first clean two-touch toolsetter run completed with Y held fixed and
  updated T24 from `Z+138.739000` to `Z+138.835417`. The repeatable offset was
  therefore `+0.096417 mm` from the target reference.
- The live toolsetter calibration was trimmed by that amount for the next
  verification pass: `#3010`/`spindle_zero_height_3010` changed from
  `773.3637` to `773.2673`. T24 was reset to `Z+138.739000` before shutdown.
- Next session should rerun `TOUCH OFF CURRENT TOOL` on T24 after confirming
  the UI warning-screen call is passing `spindle_zero_height_3010 = 773.2673`.
  If the result is close to `138.739000`, continue with repeatability checks;
  if not, trim `#3010` by the remaining measured difference.

## TCPC Tool Height Setter Commissioning - 2026-05-11 +07

The TCPC-local toolsetter workflow was improved and live-tested on T24.

Changes made:

- replaced the earlier `(MSG)`/debug notification operator checks with a
  Probe Basic/QtPyVCP modal popup on the TCPC status tab
- the popup shows the current tool number, active `G43` Z length, tool-table
  Z length for that tool, and active-minus-table difference
- the popup has a centered `Continue` button which resumes the paused `M0`
  program, matching the operator behavior of the manual tool-change dialog
- the first toolsetter touch now probes at `F100`
- the inter-touch retract is now `Z+5.0`
- the second toolsetter touch now probes at `F20`
- the final retract remains `F3000`

Live result:

- T24/H24 touch-off completed cleanly through the full macro
- active tool offset after the run was `Z+138.7459667`
- shared tool table T24 was updated to `Z+138.745967`
- this is about `+0.007 mm` from the earlier known reference value
  `Z+138.739000`, so the setter is close enough for current use but should get
  a repeatability sample before trimming the sensor calibration again
- the toolsetter still uses the `G59` setter reference: X/Y come from
  `#5181/#5182`, the macro switches to `G59` for the probe frame, and it
  restores the previous workspace at the end

Deferred toolsetter tasks:

- add a dedicated toolsetter sensor calibration routine which uses a known
  reference tool to fine-tune the sensor calibration value instead of folding
  that adjustment into every normal tool touch-off
- add automatic large-tool X offset handling: read the active tool diameter,
  and when the diameter is greater than `10 mm`, shift X by the tool radius so
  the side of the end mill is centered over the toolsetter sensor

## TCPC Forward Plan - 2026-05-11 +07

Current agreed sequence:

- finish the active 3-axis work before making further TCPC/QtPyVCP code
  changes
- after the 3-axis work is complete, inspect and correct the Probe Basic
  backplot offset issue seen with `G43` active: the loaded plotted toolpath is
  below the live tool-follow path, so the display appears to be mixing tool
  length offset frames. Important display rule for this machine: all production
  G-code is programmed at the tooltip/TCP. The loaded G-code path and toolpath
  backplot should therefore remain at the tooltip path. Tool length should only
  change the length/holder end of the displayed tool and the real machine
  compensation, not translate the programmed path away from the tooltip.
- after the display issue is understood, run the final TCPC verification
  probing pass with the short probe to confirm current fitted corrections,
  error vectors, and error magnitudes
- once verification probing is acceptable, set the CNC up for TCPC 5-axis trim
  work and test the real trim workpath without assuming more calibration work
  is required
- use the trim workpath test to surface any remaining production issues; fix
  only issues that actually affect the production workflow or operator safety

Remaining TCPC/production tasks to continue as time allows:

- repeat the T24 toolsetter cycle enough times to establish repeatability
  before trimming the sensor calibration again
- add the known-tool toolsetter sensor calibration routine
- add automatic large-tool X offset handling for tools over `10 mm` diameter
- run full TCPC g-code motion checks with no cutting tool installed
- continue servo acceleration/speed checks with TCPC and active tool length,
  prioritizing controlled 5-axis ABS trim motion over maximum speed
- finish production behavior checks for startup, `G43`, `G49`, `G43.4`,
  `G49.1`, TWP/TCPC lockouts, M6 lockouts, and spindle/flood air-bearing
  behavior

## Probe Basic Backplot Tooltip Rule - 2026-05-11 +07

The backplot offset issue seen in 3-axis work with `G43` active was traced to
the VTK backplot's remaining generic 3-axis tool-length path adjustment. The
previous TCPC display fix only skipped that path adjustment for `headheadkins`,
so the normal SSI/3-axis `trivkins coordinates=XYZBC` config could still plot
loaded G-code and live breadcrumb/tool-follow points in different tool-length
frames.

Display rule now applied in `/home/cnc5/dev/qtpyvcp`:

- any `XYZBC` machine config used here is treated as tooltip-programmed for
  backplot purposes
- loaded G-code path points are not translated by active tool length
- live breadcrumb/tool-follow points are not translated by active tool length
- active `G43` remains available to size the displayed tool geometry, so tool
  length changes the displayed holder/tool extension but not the programmed
  path

Changed files:

- `src/qtpyvcp/widgets/display_widgets/vtk_backplot/vtk_canon.py`
- `src/qtpyvcp/widgets/display_widgets/vtk_backplot/vtk_backplot.py`
- `src/qtpyvcp/widgets/display_widgets/vtk_backplot/tool_actor.py`

Syntax was checked with a no-bytecode `compile()` pass because the normal
`py_compile` command tried to write `.pyc` files into the QtPyVCP source tree.
Next step is a live UI reload/screenshot check with `G43` active to confirm the
loaded path and live follow path now overlay.

## TCPC Trim Work Readiness - 2026-05-11 +07

Short-probe TCPC verification was rerun with the corrected probe gate pattern
in `tcpc_symmetric_pose_vector_sphere_auto.ngc`.

Latest conservative verification envelope:

- B/C poses checked: `B0 C0`, `B+5 C+20`, `B+5 C-20`, `B-5 C+20`,
  `B-5 C-20`, and closing `B0 C0`
- closing `B0 C0` drift from the accepted opening reference was about
  `0.008 mm`
- worst accepted small-angle pose-center vector error was about `0.045 mm`
- result is inside the current production requirement of `<0.2 mm` and inside
  the preferred local target of `<0.1 mm`
- this verifies the conservative trim-style motion range only; it is not a
  full high-B calibration validation

Backlash decision for production TCPC trim startup:

- keep LinuxCNC backlash compensation disabled in the TCPC config
- B/C backlash compensation remains intentionally set to `0.0` because direct
  SSI feedback is at the rotary output and the previous software backlash
  values created approach-dependent TCP error
- measured X/Y lost-motion values remain diagnostic only; do not add X/Y
  backlash compensation before the first 5-axis trim work because the values
  were measured at one location and have not been separated from local rack,
  scale, compliance, or thermal effects
- the current TCPC fit and verification are valid for the config as tested;
  adding backlash compensation now would change reversal behavior and require
  a new verification pass

Production setup changes:

- TCPC Probe Basic now opens the file browser in the mounted CNC share path
  `/home/cnc5/mnt/cnc/5th axis`. This is the configured mount location for the
  CNC share; it corresponds to the requested `/mnt/cnc/5th axis` working area
  on this machine.
- a desktop launcher for TCPC trim work is provided as
  `TCPC Trim Work.desktop` and points at
  `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/launch_xyzbc_ssi_tcpc_probe_basic.sh`

Known deferred issue:

- the Probe Basic/VTK backplot tooltip display work is still WIP. Machine
  motion with active tool length checked correctly, but the display alignment
  issue has not been fully closed, so do not use the backplot alone as the
  authority for TCPC tooltip behavior.

Operational update - 2026-05-12 +07:

- early 5-axis TCPC trim work with this config is working correctly in real
  operations so far
- TCPC entry and exit are working correctly in mixed TCPC-on/TCPC-off cut files
- continue treating this as the active trim-work config while monitoring for
  any toolpath, TCPC entry/exit, tool-length, probing, or servo-following issues
- long-probe validation and deeper interpreter tool-state cleanup remain
  deferred follow-up work, not blockers for the current trim workload

## Probe Basic Probing Gate Compatibility - 2026-05-11 +07

The original Probe Basic probing routines in the shared subroutine folder were
stopping on the first touch in the TCPC config and not retracting. This was a
side effect of the TCPC probe-gate safety layer: the old routines call `G38`
directly and do not explicitly open `motion.digital-out-00`, so the raw probe
touch was seen by the abnormal-pulse monitor while the gated LinuxCNC
`motion.probe-input` stayed closed.

The current TCPC HAL overlay authorizes the physical probe path only while the
real-time motion controller reports active probing motion:

- `motion.motion-type == 5` is converted through `tcpc_motion_type_float`
- `tcpc_probe_motion_window` detects the probing-motion window
- `tcpc_probe_motion_window.out` drives `and2.1` directly, so raw `probe-mux`
  can reach `motion.probe-input` and the physical SSR only during that window
- `motion.digital-out-00/01` do not authorize the physical probe gate or inhibit
  its abnormal-pulse monitor; guarded routines require them clear, and retained
  `M64/M65` commands only manipulate those unused legacy outputs
- `tcpc_probe_gate_ignore.width` was historically increased from `0.25 s` to
  `1.0 s`; campaign 2026082202 proved that value insufficient for this wireless
  receiver, so the active/saved value is now `10.0 s`

Probe Basic stores the probing UI values in settings widgets and mirrors them
into numbered interpreter parameters with `touch_probe_param_update.ngc`. The
TCPC Probe Basic machine name is included in the startup sync path so persisted
UI values are pushed into `#3014..#3036` after startup, not only after the
operator edits a probing field. Normal UI edits still trigger the same update
button when the edit is committed.

Expected behavior after restart:

- original Probe Basic probing routines should again touch, record the point,
  retract, and continue their fast/slow sequence
- probe false-pulse monitoring remains active outside actual probing moves and
  the 10-second post-touch quarantine; the dedicated campaign runner then
  proves 20 continuously clear seconds before its next G38
- shared Probe Basic probing macros now validate the loaded probe with the
  live HAL `#<_hal[iocontrol.0.tool-number]>` value instead of `#5400`; this
  keeps the wrong-tool guard active while avoiding stale interpreter tool state
  where both `#5400` and `#<_current_tool>` reported `0` while status/HAL
  showed tool 3 loaded
- shared Probe Basic probing macros now read probe diameter from the live
  table-backed HAL value `#<_hal[halui.tool.diameter]>` instead of volatile
  `#5410`; live debugging showed `#5410 = 0.000000` while
  `halui.tool.diameter = 6.000000` for T3, which made X/Y WCS probing set the
  work offset at the raw touch point instead of applying the probe radius
- probe macros now abort if the live tool diameter is zero so a missing or
  incomplete tool-table diameter cannot silently corrupt a work offset

## Runtime Update - 2026-06-16 B-Axis Home-Zero Trim

After the loose conical shaft clamp was found and retorqued, the B encoder was
treated as trustworthy because it is a direct-coupled output-shaft encoder. The
remaining error is treated as a LinuxCNC B home-zero reference error, not an
encoder feedback error.

The first sphere data after the sphere moved starts at
`tcpc-b-angle-scaling-diagnostic-2pass-results.csv` line `775`; earlier rows
from the old sphere position are not used. The accepted C0-only B sweep
produced a tight opening/closing B0 repeat of about `0.011 mm`, so the run is
usable for B-zero trim. The paired B `+/-30` and B `+/-60` Z deltas at the
current effective `~308 mm` B-to-probe-tip lever arm indicate a B-zero trim of
about `0.026 deg`. B `+/-90` was downweighted because the remaining X-heavy
high-B residual includes known non-B-zero machine geometry/alignment error.

Applied TCPC-test-config-only trim:

```hal
setp b_ssi_zero.in1 -176.1245
```

This replaces the post-clamp dial-gauge value `-176.0981`. The change moves the
commanded B0 physical output by about `+0.0264 deg` while keeping LinuxCNC
rotary backlash compensation disabled.

Immediate rerun caveat: rows `791-802` were started after this trim but are not
valid for another adjustment. The operator saw the sphere move on a Z probe
touch, and the run stopped after accepted `B+90 C0` pass 2 before `B-90` and
the closing `B0` repeat. Treat rows `791-802` as contaminated/incomplete; the
next heavy-base rerun should start from line `803`.

Heavy-base rerun caveat: rows `803-808` also do not form a usable B-zero fit.
The opening `B0` and `B+30` accepted rows were clean enough to show that the
trim moved the positive-B Z error in the correct direction, but the operator
reported probe errors during `B-30`. The logged `B-30` pass-2 row had corrected
diameters around `29.52 mm` and a multi-millimeter center jump, so discard row
`808` and the run as a whole before applying any further B-zero adjustment.
After the probe issue is cleared, rerun from a fresh B0 baseline; new candidate
data should start after line `808`.

Probe-reset heavy-base rerun rows `809-824` completed cleanly. Accepted pass-2
diameters returned to the expected range, and the opening/closing B0 repeat was
about `0.019 mm`. The first B-zero trim improved the positive-B Z error but
slightly overshot the paired `+/-30` and `+/-60` Z balance. B `+/-90` still
contains larger non-B-zero geometry/alignment residual, so the second B-zero
trim intentionally used only the `+/-30` and `+/-60` pairs. Applied
TCPC-test-config-only value:

```hal
setp b_ssi_zero.in1 -176.1160
```

This is a conservative back-off from `-176.1245`; repeat the same C0-only B
sweep after restart before making any further B-zero change.

Restarted C0-only sweep rows `825-838` were interrupted by a probe fault at
`B-90`. Rows `825-836` are usable through `B+90`; row `838` is invalid and is
discarded because the corrected diameters fell to about `29.30/29.33 mm`.
The resume program
`nc_files/calibration/tcpc_b_angle_scaling_resume_bminus90_c0.ngc` then ran a
fresh `B0 C0` seed, `B-90 C0`, and closing `B0 C0` in rows `839-844`. The
combined valid set has an opening/closing B0 repeat of about `0.0116 mm`; the
resume-only B0 seed-to-close repeat is about `0.0093 mm`.

Final B-zero assessment at `b_ssi_zero.in1 = -176.1160`: using the valid
low-angle `+/-30` and `+/-60` pairs, the remaining indicated trim is only about
`+0.0058 deg` and `-0.0007 deg` respectively, averaging about `+0.0026 deg`.
That is within the current repeatability/noise of this setup, so no further
B home-zero change was applied. The `B-90` row still shows a larger
X/Y/Z-heavy residual, so treat that as remaining high-B machine geometry /
alignment error rather than a clean B-zero-home error.

Operational context from the owner/operator: this machine cuts large vacuum
formed parts and is not expected to behave like a high-rigidity precision
5-axis machining center. For this recovery work, focus B-axis diagnostics on
balanced `+B/-B` motion around the output-shaft encoder zero, not on forcing a
global fit through every remaining TCPC residual. If the balanced B sweep is
around `0.1 mm` or better at the probe tip, that is sufficient for the intended
machine use; larger high-B vector residuals should be handled later as separate
machine geometry, stiffness, probe-length, or alignment work.

Session close-out: no further B-home-zero changes are planned for now. The next
major calibration task should wait until the long probe arrives so short/long
probe comparison runs can separate tool/probe-length effects from machine
geometry. Laser alignment and correction-table work remains a future project
only if the machine's production needs warrant that level of correction.

Follow-up:

- investigate why the interpreter volatile current-tool parameters
  `#5400/#5410/#<_current_tool>` remain zero after the Probe Basic remembered
  tool restore (`M61 Q3 G43`) even though LinuxCNC status, `iocontrol`, HAL
  tool offset, and `halui.tool.diameter` are correct
- investigate the Probe Basic UI/toolbox versus live runtime tool-offset
  mismatch seen during the 2026-06-16 B-axis recovery run: the UI/toolbox
  could show the intended T3 probe data while LinuxCNC's active
  `motion.tooloffset.z`/`halui.tool.length_offset.z` still held the previous
  T97 length (`168.306`) instead of T3 H3 (`128.606729`). Future TCPC probing
  preflight must verify the live runtime pins/status, not only the displayed
  tool row.
- investigate intermittent wireless probe electrical/charge noise through the
  machine: during the 2026-06-16 B-axis recovery run the probe could show a
  multi-flash fault and a faint flicker on the diagnostic LEDs, without a
  solid input-on state. Unseating and reseating the probe in the spindle
  cleared the symptom. Treat this as a physical/electrical probe contact,
  grounding, shielding, or charge-coupling investigation before blaming TCPC or
  calibration G-code.
- keep probing routines on the HAL/status tool source unless the interpreter
  current-tool model is made reliable again for this non-random toolchanger

## 2026-08-24 Relocated-Sphere Campaign 2026082404

The accepted campaign-03 anchor is retained at
`X1024.957789 Y844.074417 Z-302.468115`. Before primary acquisition, the T4
training grid was revised from 59 to 101 poses. New paired
`B+/-5,+/-10,+/-15` blocks use `C0,45,90,180,225,270,0`; C135/C315 remain
omitted known post-collision sectors. Existing `B+/-30,+/-45,+/-60,+/-90`
blocks remain at C90 steps. T3 remains a 31-pose untouched holdout.

Exact configured-limit replay passed 41,063 combined samples with
`182.860993 mm` remaining worst linear margin. This does not qualify physical
clearance. At `2026-08-24T23:42:38+07:00`, the operator explicitly accepted T4
clearance for `B-5/-10/-15 C45/C225` with no interference issues. This is
operator evidence rather than a replay-model result. The operator declined
further fast envelope sweeps. The authoritative procedure is
`TCPC_RELOCATED_SPHERE_CAMPAIGN_2026082404.md`.
