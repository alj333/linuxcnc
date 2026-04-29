# 5th Axis XYZBC SSI TCPC Probe Basic Config

This is a separate real-machine TCPC test config. It is not the maintenance or
setup config.

Current status:

- uses `headheadkins coordinates=XYZBC kinstype=B`
- reuses the proven Mesa/SSI motion HAL from
  `configs/5th_axis_xyzbc_ssi_probe_basic`
- reuses the existing Probe Basic UI, subroutines, XHC HAL, shutdown HAL, and
  tool table from the trivkins Probe Basic config
- uses its own LinuxCNC parameter file so test WCS changes do not write back to
  the normal Probe Basic parameter file
- starts with TCPC enabled so there is no live kinematics jump when testing
- `G43.4` is accepted only while TCPC is already enabled; `G49.1` is blocked in
  this test config until a safe live transition strategy is implemented
- `headheadtwp.tcpc_enabled` gates `headheadkins.tcpc-enable`
- unwraps the single-turn C SSI feedback to the nearest commanded C angle with
  `rotaryunwrap` before feeding joint 4
- requires homing before motion with `NO_FORCE_HOMING = 0`
- adds TCPC/TWP indicators to Probe Basic:
  - compact single-LED `TCPC OFF` / `TCPC ON` / `TCPC TWP` status in the
    user-button area
  - detailed `TCPC STATUS` user tab showing state, angles, tool vector, and
    tool offset pins

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
- live `G43.4/G49.1` TCPC switching is intentionally disabled for safety
- do not use this config for cutting until fixed-tip and moving TCP checks pass

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/launch_xyzbc_ssi_tcpc_probe_basic.sh
```

First validation path:

1. Launch and confirm the machine starts with `TCPC ON` and without enabling TWP.
2. Home all axes.
3. Run only no-cut, slow fixed-tip validation moves.
4. Do not use `G49.1`; close/restart the config to leave TCPC testing.

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

The first expanded-matrix sensitivity fit should remain inactive until the next
TCPC no-cut validation session.

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

Mirror these values to the matching `headheadtwp.*` pins if the candidate is
loaded into the TCPC overlay.

Expected result:

- last symmetric repeat predicted worst tilted residual: about `0.034 mm`
- expanded matrix predicted B `+/-30` worst residual: about `0.196 mm`
- expanded matrix predicted B `+/-50` worst residual: about `0.437 mm`

Validation order:

1. Run the symmetric program first.
2. If signs and residuals improve, run the expanded program through the B
   `+/-30` group and stop at the `M0` pause after the B30 closure.
3. Treat remaining B `+/-50` error as likely alignment/squareness work unless
   a repeat data set shows a clean simple-offset pattern.
