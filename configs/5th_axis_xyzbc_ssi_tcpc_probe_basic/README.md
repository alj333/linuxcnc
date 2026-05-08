# 5th Axis XYZBC SSI TCPC Probe Basic Config

This is the separate real-machine TCPC/TWP Probe Basic config. It is not the
maintenance or setup config, and it remains a commissioning work config until
the full TCPC/TWP task list is complete.

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
- `M6` and `M61` are rejected while any spindle is active through
  `TOOL_CHANGE_REJECT_SPINDLE_ON = 1`; tool/current-tool changes require an
  explicit `M5` first, matching the old machine safety behavior
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
- active `G43 Hn` length is included in the head-head kinematics as local tool
  length, so the same B-to-spindle-nose geometry can handle different tools
- `G68.2` TWP entry is temporarily disabled in the real-machine config pending
  entry-continuity validation; TCPC entry/exit is validated, but the TWP motion
  enable path is not yet production safe
- the TCPC tool-length guard is enabled by
  `headheadtwp.tcpc_tool_length_guard`; the real fail-safe state wrapper sets
  this pin true so the interpreter blocks tool-length changes only for guarded
  TCPC configs
- the TCPC config intentionally leaves `ON_ABORT_COMMAND` unset; abort recovery
  is manual so automatic cleanup cannot hide or disturb active TCPC/tool-length
  state. Return B/C to `B0 C0`, run `G49.1`, and only then clear tool length
  with `G49` if required.

Recommended production program envelope:

```ngc
G17 G21 G40 G49 G54 G64 P0.001 G80 G90 G92.1 G94
(machine enabled and homed before this program starts)
Tn M6
G43 Hn
G0 B0 C0
G43.4
(normal TCPC or TWP work)
G69     (only needed if TWP was used)
G0 B0 C0
G49.1
G49
M30
```

Production-release items still open:

- restart LinuxCNC before testing; currently running processes do not pick up
  rebuilt kinematics/interpreter code
- validate the spindle-nose split with tool 3 active: `G43 H3` before `G43.4`
  should reproduce the previous short-probe TCPC fit
- run the no-cut smoke program and one active-`G43 H3` sphere validation pass
- current production guidance remains that tool changes/current-tool changes
  happen outside TCPC; `M6`/`M61` now share the spindle-active lockout and TWP
  already blocks tool/current-tool changes
- repeat short/long probe validation when the long probe arrives

Headless regression added:

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-tcpc-entry-exit
rm -f sim.var
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

This test verifies fail-safe startup, `G43.4` entry continuity, idempotent
`G43.4`, ordinary `G49`/`G43.1` rejection while TCPC is active, rotary TCPC
compensation, unsafe `G49.1` rejection away from entry B/C, continuous
`G49.1` exit after returning to entry B/C, `G68.2` rejection while TCPC is off,
and `G49.1` rejection while TWP is active.

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

TWP entry fault, 2026-05-07 21:20 +07:

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
- probing validation is deferred until the physical probe is installed; keep
  TWP/`G68.2` motion disabled on the real machine

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

## Probe Gate Runtime Note - 2026-04-30

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
