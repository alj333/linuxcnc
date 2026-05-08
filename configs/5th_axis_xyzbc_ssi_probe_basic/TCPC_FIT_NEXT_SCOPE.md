# TCPC Fit Next Scope

Status: TCPC direction checks, fixed-tip validation, corrected expanded
validation, B50 redo data, clean B90 diagnostics, C0 B-angle scaling, the
B/C-cross candidate run, and the refined B/C-cross candidate run have now run
on the real machine. The current guidance is the
`Refined B/C Cross Candidate Live Result - 2026-05-05` section near the end of
this document. Older early-fit sections remain for provenance only and should
not be treated as the next live sequence without checking the latest status.
Current practical acceptance target is `0.2 mm`; refine toward `0.1 mm` only
after mechanical backlash, alignment, servo tuning, and thermal/return-path
repeatability are better characterized.

Earlier on 2026-04-27 staff started epoxy preparation on a mold on the machine,
and the start was bumped near the end of the B-axis session. TCPC work was
paused at `10:50 +07` for 3-axis work, then resumed in the dedicated TCPC test
config after the machine was stable again.

`G55` is reserved for staff 3-axis setup work from this point. Do not select,
probe, overwrite, or use `G55` for TCPC calibration/validation until the
operator explicitly releases it.

## TCPC Tool-Length Integration - 2026-05-07

The TCPC work config now treats `headheadkins.nominal-b-to-tool.*` as
B-axis centerline to spindle nose. The previous short-probe tip baseline was
kept as the reference data point by removing T3 H3 from the Z term:

- previous nominal `b-to-tool.z`: `-308.980001`
- current T3 H3 tool length: `+128.606729 mm`
- new nominal B-to-spindle-nose `z`: `-180.373272`
- retained fitted `cal-b-to-tool.z`: `+0.815000`

`motion.tooloffset.x/y/z` is now netted into
`headheadkins.active-tool-offset.x/y/z`. In the kinematics, active Z tool
length is applied along the local negative tool axis, so `G43 H3` reconstructs
the same short-probe tip geometry used for the current fitted correction.

Interpreter guard added: ordinary tool-length changes (`G43`, `G43.1`,
`G43.2`, and `G49`) are rejected while `headheadtwp.tcpc_enabled` is true.
The required order is `G43 Hn` before `G43.4`, then `G49.1` before any `G49`
or different `G43 Hn`. The guard is gated by
`headheadtwp.tcpc_tool_length_guard`; the real TCPC fail-safe wrapper enables
that pin, while older simulator configs without the guard pin keep their
historical behavior.

The TCPC work config intentionally leaves `ON_ABORT_COMMAND` unset. Automatic
abort cleanup can hide or disturb active TCPC/tool-length state, and subroutine
lookup proved unreliable during the guard-smoke tests. `G43.4` is now locked to
explicit `B0 C0` entry, so recovery order after a TCPC abort is to make the
machine safe, return B/C to `B0 C0`, run `G49.1`, then use `G49` if tool length
must be cleared.

## TCP Production Readiness Checkpoint - 2026-05-07

The current TCPC work config is close enough for controlled production
validation, but it is not released as the default production configuration yet.
Live checks completed on 2026-05-07:

- `M6` and `M61 Qn` reject correctly while the spindle is active.
- `G43.4` rejects unless B/C are at explicit `B0 C0`.
- ordinary `G49`/`G43.1` changes reject while TCPC is active.
- `G49.1` rejects away from the TCPC entry orientation, leaves TCPC active,
  and manual recovery with `G0 B0 C0`, `G49.1`, then `G49` clears cleanly.
- unsetting `ON_ABORT_COMMAND` eliminated the earlier unreliable
  `Oon_abort` lookup error during the guard smoke test.
- after manual TCPC recovery, T3 may remain the current tool while active
  `motion.tooloffset.*` is zero/G49 if the operator finished with `G49`.
- on fresh Probe Basic startup after all axes are homed, the tool table plugin
  may intentionally restore the remembered spindle tool with `M61 Qn G43`.
  Keep this behavior for crash prevention when a physical tool is still loaded;
  TCPC checks must use live `motion.tooloffset.*`/G43 state as the source of
  truth before `G43.4`.
- TCPC-only smoke checks passed, but real-machine TWP entry is not production
  safe yet: after `G43.4`, `G68.2 B0 C0` caused XYZ following errors and
  dropped X/Y homing. The TCPC work config now rejects `G68.2` pending an
  offline TWP entry-continuity fix.
- Offline active-tool reproducer added on 2026-05-08: real-style geometry,
  active T3-length `G43`, external tool offset wiring, failed pre-TCPC
  `G68.2`, and back-to-back `G43.4`/`G68.2` did not produce a joint command
  discontinuity in sim. The remaining TWP fault is likely a real-machine
  transient/instrumentation problem, not the static active-tool-length math.
- Real TCPC preserve-tool smoke run passed on 2026-05-08 with tool 3 restored
  by Probe Basic startup and active `G43 H3`. Final state was all axes homed,
  `B0 C0`, TCPC off, TWP off, T3 still loaded, and
  `motion.tooloffset.z = 128.6067`. The smoke programs now include preview
  guards so the 3D backplot does not evaluate live tool/TCPC checks while the
  file is only being loaded.
- The first attempted small-pose sphere validation on 2026-05-08 was invalid:
  the physical probe was not loaded, so the first `G38.2` ended with no
  contact. No new rows were written to the small-pose result CSV. Recovery
  left the controller idle at `B0 C0`, TCPC off, TWP off, and T3/G43 active.
  The small-pose validation now has a one-time start `M0` confirmation before
  any probe motion.
- No-probe TCPC tests on 2026-05-08 passed while the machine was reserved for
  mold work. Added `tcpc_production_no_motion_state_smoke.ngc`, which contains
  no `G0`/`G1`/`G38` moves and only checks `G43.4`/`G49.1` state continuity.
  Live run completed with no position change and left T3/G43 active. A separate
  no-motion MDI guard sequence confirmed `G43 H3`, `G49`, and `G68.2 B0 C0`
  are rejected while TCPC is active, with TCPC staying active until `G49.1`.
  A no-motion idempotency sequence also passed: `G68.2 B0 C0` rejected while
  TCPC was off, `G49.1` was harmless while off, repeated `G43.4` at `B0 C0`
  was harmless, and repeated `G49.1` exited/held off with no position change.
- Servo work started in the TCPC work config only on 2026-05-08. Baseline
  linear relative motion was acceptable for the current commissioning stage
  (worst Y following error `0.0107 mm`). Baseline rotary motion with B/C
  `P=50`, `MAX_OUTPUT=8` showed too much dynamic lag, especially C
  (`0.181 deg`) because the output limit was reached. Live tuning found
  `P=75`, `MAX_OUTPUT=12` as the current rotary candidate, reducing clean peak
  errors to B `0.042 deg` and C `0.048 deg` with no SSI invalids or PID
  saturation. `P=100` was worse at about `0.15 deg`, so it is rejected.
  The TCPC work INI now carries the `P=75/MAX_OUTPUT=12` B/C candidate; restart
  the TCPC config before treating it as persistent-test validated.
- Fresh restart verification later on 2026-05-08 confirmed the persisted
  `P=75/MAX_OUTPUT=12` values were loaded from the TCPC INI. The fresh rotary
  small-motion run returned idle/in-position at the starting B/C pose with peak
  following errors B `0.0417 deg` and C `0.0485 deg`, zero PID saturation
  samples, and zero B/C SSI invalid samples.

Before production release, still cover these items:

- Restart LinuxCNC so the rebuilt `headheadkins`, interpreter, and Probe Basic
  TCPC config are actually loaded.
- Treat the persisted B/C servo tune as the current TCPC work-config candidate.
  The fresh-run target of below about `0.05 deg` B/C following error with zero
  PID saturation has been met once from a restarted session.
- With tool 3 loaded, run `G43 H3` before `G43.4` and confirm the short-probe
  effective tip position matches the pre-tool-length baseline.
- Rerun the no-cut TCPC entry/exit smoke program from a fresh LinuxCNC session
  as the final release check after any further guard or startup-state changes.
- Keep `G68.2`/TWP disabled on the real machine until the continuity problem is
  reproduced and fixed in sim/offline checks, then validated with a dedicated
  no-motion/no-cut machine test.
- Add entry instrumentation before any TWP retest: log pre/post
  `axis.*.pos-cmd`, `joint.*.motor-pos-cmd`, `headheadkins.twp-motion-origin.*`,
  `headheadtwp.tcpc_origin_*`, and `motion.tooloffset.*` around the remap
  phases.
- Run one short-probe sphere validation pass with active `G43 H3`; compare
  residuals against the last accepted refined-fit data. This final TCPC probe
  check is deferred until after servo motion and machine behavior work is
  complete, so rotary/linear following behavior is no longer a moving variable
  in the TCPC validation.
- Confirm abort recovery: while TCPC is active, abort must not clear tool
  length. Recovery remains manual-safe: make the machine safe, return B/C to
  `B0 C0`, run `G49.1`, then `G49` if required.
- Confirm `M6` and `M61` rejection with the spindle active. The SSI Probe Basic
  configs now set `TOOL_CHANGE_REJECT_SPINDLE_ON = 1`, so tool/current-tool
  changes should abort until the program or operator has issued `M5`.
- Review tool-change paths and post output. Production programs should not
  issue `M6`, `M61`, `G43`, `G43.1`, `G43.2`, or `G49` inside active TCPC/TWP.
  `M6`/`M61` now share spindle-active lockouts and TWP lockouts, but production
  post output should still keep them outside TCPC.
- When the long probe arrives, run short/long back-to-back validation using
  `G43 H3` and the long-probe `G43 Hn`. This is still the key test for whether
  remaining errors are true rotary geometry versus tool-vector/tool-length
  model errors.
- Before enabling TWP for production, validate TWP entry/exit with a real post
  sample after the continuity fix: `G43 Hn -> G0 B0 C0 -> G43.4 -> optional
  G68.2/G69 -> return B/C to B0 C0 -> G49.1 -> G49`.

## Current Shutdown Status - 2026-05-03

This section supersedes the older first-fit direction-test guidance below for
the next TCPC session.

The B90 diagnostic was rerun cleanly after the probe reset issue. The clean run
starts at `tcpc-b90-b-axis-diagnostic-2pass-results.csv` line `18` and
completed with no errors. The earlier line `17` `B0 C180` row is invalid
because a probe reset produced corrected diameters of about `29.172/29.220 mm`
and a Z center about `+4.10 mm` from normal.

Clean B90 local deltas versus the nearest B0 baseline:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.042834` | `-0.212500` | `+0.067708` | `0.227102` |
| `B-90 C0` | `-0.190496` | `-0.123125` | `+0.620805` | `0.660944` |
| `B+90 C180` | `-0.177921` | `-0.224257` | `+0.054792` | `0.291461` |
| `B-90 C180` | `-0.052201` | `+0.177427` | `+0.632291` | `0.658785` |

Repeatability checks:

- accepted centers repeated against the earlier clean common B90 rows within
  about `0.008-0.019 mm`
- B0 closures in the clean B90 run stayed about `0.011-0.033 mm`
- corrected diameters were inside the normal window
- `motion.digital-out-00`, `motion.digital-out-01`, and `motion.probe-input`
  were all `FALSE` after program end

Interpretation:

- The large `B-90` error is real and repeatable.
- SSI differential angles should be trusted. The B/C encoder feedback is not
  the primary explanation for the mm-scale TCP residuals.
- B-axis centering is part of the problem space, but one static B-center offset
  cannot fit the observed pattern. The implied B-center correction differs
  strongly between `B+90` and `B-90`.
- A C-axis center correction of roughly `-0.104 mm X`, `+0.009 mm Y` is visible
  from B0 C180 versus B0 C0.
- Existing `headheadkins` translation and zero-offset pins cannot correct the
  full pattern; fits still leave about `0.5 mm` high-B residual.

Next live diagnostic:

- Do not rerun the same B90 C0/C180 sequence first.
- Prepare a B90 C-quadrant diagnostic with `B+90/B-90` at
  `C0/C90/C180/C270`, with B0 closures between groups.
- Use this to separate rotary-frame errors from machine-fixed linear-axis
  errors:
  - residual rotating with C -> rotary head geometry / C/B angular model
  - residual fixed in machine XYZ -> linear-axis scale/squareness/pitch or
    volumetric compensation problem

Expanded TCPC correction scope:

- Treat all geometry as variable except the differential SSI angle readings,
  unless later direct evidence contradicts them.
- The current kinematics assumes ideal C and B axis directions. Expand the
  model before attempting another final TCPC fit.
- Add bounded fit variables/HAL pins for:
  - C-axis tilt relative to machine Z
  - B-axis direction/skew relative to the C frame
  - B/C non-orthogonality
  - B/C pivot translations and zero offsets
  - tool/probe vector angular error
  - optional machine-linear affine or map-based correction after the quadrant
    diagnostic shows whether residuals are machine-fixed
- Apply no live correction until an offline least-squares fit with held-out
  poses improves mid-B and high-B residuals without degrading B0 C-only closure.

## Current Data Set

Use the curated input file for the first fit pass:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-fit-input-candidates.csv`

Included B-axis candidate centers:

- `B0 C0` closing two-pass accepted center:
  `X=306.338526 Y=352.821813 Z=-280.762445`
- `B+15 C0` two-pass accepted center:
  `X=226.486276 Y=352.897855 Z=-291.117802`
- `B-15 C0` corrected single-pass accepted center:
  `X=386.140321 Y=352.717855 Z=-291.445826`
- `B+30 C0` two-pass accepted center:
  `X=151.969455 Y=352.913688 Z=-321.714304`
- `B-30 C0` two-pass accepted center:
  `X=460.527766 Y=352.638896 Z=-322.390804`

Data caveats:

- The closing `B0 C0` point is usable only with the epoxy/bumped-start caveat.
- The latest raw B-vector CSV also contains one extra full `B0 C0` two-pass
  repeat after the bumped start. Its accepted center was
  `X=306.331442 Y=352.822021 Z=-280.761945`, which is close to the previous
  closing point, but it is excluded from the first candidate input because the
  run was unintended and the setup environment was no longer clean.
- The `B-15 C0` point came from the corrected single-pass routine, not the
  automatic two-pass routine.
- The observed B-axis candidate Y range is about `0.274792 mm`; this may be
  real head alignment, local machine error, setup disturbance, or some
  combination. Do not hide that by forcing the rotary geometry fit.
- Corrected sphere diameters are commonly around `30.1-30.3 mm`, so fit work
  should use center repeatability and residuals rather than diameter alone.

## First Offline Fit

Start with analysis only. Do not change INI, HAL, kinematics constants, WCS, or
Probe Basic settings from these numbers until the residual report is reviewed.

Recommended steps:

1. Read the C-axis sweep from `sphere-center-results.csv`.
2. Read accepted B-vector rows from the curated candidate CSV.
3. Fit the C-axis center from the stable `B0` C-sweep.
4. Fit the B-axis candidate from the `C0` B sweep in machine `X/Z`.
5. Report residuals by pose, not just a single best-fit offset.
6. Decide whether to repeat `B0 C0` and `B-15 C0` before writing any TCPC
   offset values.

Preliminary sanity check from the current B candidate rows only:

- simple `X/Z` circle center: `X=305.669816 Z=-589.742446`
- simple radius: `308.963734 mm`
- residuals are within about `0.02 mm` for the candidate rows

This is only a geometry sanity check. The final TCPC setup still needs the
C-axis fit, sign convention verification, kinematics mapping, and a practical
fixed-tip validation pass.

## First Visual TCPC Starting Candidate

This candidate was computed on 2026-04-27 before pausing TCPC work for 3-axis
machine setup. It was promoted to the TCPC test config startup HAL when TCPC
work resumed, but only as first-pass visual validation geometry.

C-sweep fit from the last complete `B0` sweep:

- C circle center: `X=305.680751 Y=326.095031`
- C radius: `26.751963 mm`
- C residuals: about `+/-0.022 mm`
- combined B0/C0 XY offset: `X=-0.692863 Y=-26.721365`

B-sweep fit from the curated `C0` candidate rows:

- B X/Z circle center: `X=305.669816 Z=-589.742446`
- B radius: `308.963734 mm`
- B residuals: within about `0.020 mm`
- B0 vector from B pivot to tool in X/Z: `X=-0.668710 Z=-308.980001`

Candidate `headheadkins` direct-vector values for the next slow no-cut visual
test:

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

Interpretation caveats:

- These numbers intentionally keep `c-to-b.z` at the previous nominal
  `-270.000000 mm` and put the observed B radius into `nominal-b-to-tool.z`.
- This is a practical first visual check, not the final mechanical model.
- Tool table length correction is not solved yet; `motion.tooloffset.z` exists
  but is not currently wired into `headheadkins`.
- Live `G43.4/G49.1` switching originally produced a large kinematics
  discontinuity when enabling TCPC from identity mode. As of 2026-05-07, the
  TCPC Probe Basic config starts fail-safe with TCPC off; `G43.4` sets a TCPC
  entry origin in `headheadkins`, and `G49.1` is guarded so it can only exit
  after `G69` and after B/C return to the saved TCPC entry orientation.
- Positive C quadrant testing exposed the single-turn SSI wrap at physical
  `C180`: just over `+180 deg`, the old feedback path reported about
  `-178 deg`, causing a LinuxCNC joint-4 following error with no servo-drive
  alarm. The TCPC test config now inserts `rotaryunwrap` so C feedback is
  shifted by whole 360 degree periods to stay nearest `c-pos-cmd`.
- The unwrap is command-referenced and does not provide persistent multi-turn
  absolute recovery after a restart. Restart the TCPC test config with C at a
  known safe side of the wrap, preferably C0.
- C unwrap validation later passed with `C170 -> C185 -> C170 -> C0` at
  `F50`, followed by a successful `C270` quadrant check with `B2/B0`. TCPC
  correction directions were visually confirmed correct in all four C
  quadrants at slow no-cut feed.

## Resume Conditions

Before collecting more machine data:

- confirm the epoxy/mold work is not moving, loading, or thermally disturbing
  the calibration setup
- confirm the 30 mm sphere is rigid and has not shifted
- verify active WCS and probe parameters after Probe Basic restart
- confirm `G55` is still reserved or explicitly released before choosing any
  calibration WCS
- keep probing feeds at `50 mm/min` slow and `100 mm/min` fast
- for the current TCPC fixed-tip checks, operator-approved linear positioning
  feed is `1200 mm/min`; use lower feeds again if clearance or setup
  confidence changes
- rerun closing `B0 C0` with the two-pass routine as the first clean check
- after launching the TCPC config, confirm the candidate geometry loaded in
  `headheadkins` before running fixed-tip validation
- C unwrap and all-quadrant TCPC direction checks passed on 2026-04-27; next
  TCPC validation should move from direction/sanity checks to fixed-tip
  deviation checks, still at slow no-cut feeds

## Small-Pose TCPC Fixed-Tip Validation - 2026-04-27

Program:

- `nc_files/calibration/tcpc_small_pose_vector_sphere_auto.ngc`

Logs:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-small-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-small-pose-vector-2pass-raw-points.csv`

Setup/state:

- TCPC test config was running with startup TCPC enabled.
- Probe tool `T3` was loaded after the first attempted start exposed missing
  Probe Basic probe diameter state.
- The program now falls back to the known wireless probe diameter
  `6.000000 mm` and calibration offset `0.134533 mm` if LinuxCNC parameter
  state is missing or invalid.
- Program feeds remain conservative: probe `F50`, linear transfer `F150`,
  rotary index `F100`. During the live run the operator increased feed override
  because this was a monitored test pass.

Accepted pass-2 centers, compared to the first accepted `B0 C0` baseline
`X=305.346532 Y=326.053808 Z=-859.724433`:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B0 C0` baseline | +0.000000 | +0.000000 | +0.000000 | 0.000000 |
| `B+2 C0` | +0.095283 | -0.004150 | -0.007699 | 0.095684 |
| `B-2 C0` | +0.020950 | +0.016521 | -0.016383 | 0.031309 |
| `B+2 C+10` | +0.107496 | -0.039073 | -0.008895 | 0.114722 |
| `B+2 C-10` | +0.116839 | +0.046881 | -0.040907 | 0.132373 |
| closing `B0 C0` | +0.017500 | +0.013501 | -0.042375 | 0.047793 |

Interpretation:

- The first real fixed-tip result is close to the practical `0.10 mm` TCPC
  target for this machine.
- The combined `B+2/C+/-10` poses are the first useful geometry-refinement
  signals, with worst case about `0.132 mm`.
- Closing `B0 C0` moved about `0.048 mm`, so do not over-fit from this one run;
  some of the measured drift may be probe/machine repeatability, local axis
  error, sphere stability, or feed-override effects.
- Corrected diameters still read high/variable, roughly `30.15-30.33 mm`, so
  continue using center repeatability and pose deltas as the primary TCPC
  metric until the probe diameter/calibration path is cleaned up.

TCPC work is now paused. First X/Y reversal backlash checks on 2026-04-28 found
about `0.035-0.040 mm` X lost motion and about `0.029 mm` Y lost motion at the
tested location. Commanded-distance verification is deferred until suitable
tooling is available or a distance/scale problem is suspected. See
`XY_BACKLASH_DISTANCE_NEXT_SCOPE.md`.

## Small-Pose TCPC Fixed-Tip Validation - 2026-04-28

Program:

- `nc_files/calibration/tcpc_small_pose_vector_sphere_auto.ngc`

Logs:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-small-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-small-pose-vector-2pass-raw-points.csv`

Setup/state:

- TCPC test config was running with startup TCPC enabled.
- Table had a mold present; current test scope keeps B well inside the
  operator-requested `+/-50 deg` limit.
- Program sequence remained small: `B0 C0`, `B+2 C0`, `B-2 C0`,
  `B+2 C+10`, `B+2 C-10`, closing `B0 C0`.
- Program feeds: probe `F50`, linear positioning `F400`, rotary index `F100`.
- Probe calibration offset used: `0.134533 mm`; loaded probe tool logged as
  `T3`.

Accepted pass-2 centers, compared to the first accepted `B0 C0` baseline
`X=305.464232 Y=326.086678 Z=-859.747052`:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B0 C0` baseline | +0.000000 | +0.000000 | +0.000000 | 0.000000 |
| `B+2 C0` | +0.093563 | -0.008473 | +0.001314 | 0.093955 |
| `B-2 C0` | +0.012669 | +0.008341 | -0.007122 | 0.016757 |
| `B+2 C+10` | +0.095975 | -0.046961 | +0.001659 | 0.106861 |
| `B+2 C-10` | +0.107216 | +0.029101 | +0.001978 | 0.111113 |
| closing `B0 C0` | -0.002112 | +0.000160 | -0.000023 | 0.002118 |

Interpretation:

- Result is inside the current `0.2 mm` TCPC acceptance target.
- The closing `B0 C0` repeat is excellent for this setup, so the run is more
  useful than the 2026-04-27 first pass for geometry diagnostics.
- The combined `B+2/C+/-10` poses both carry a positive X component near
  `0.10 mm`; this points more toward remaining B/tool-vector geometry, X-axis
  mechanics, or head alignment than a simple C sign error.
- The `B+2` and `B-2` asymmetry is not enough by itself to change offsets. Use
  the next wider-but-still-safe pose set to separate geometry from backlash and
  local axis error.
- Corrected diameters are still high/variable, roughly `30.20-30.35 mm`; keep
  using center repeatability and pose deltas as the main TCPC metric.

B-axis centerline offset hypothesis:

- The operator reports a known possible assembly error where the spindle
  centerline is fractionally offset from the B-axis rotation center.
- Tracked legacy configs support this as a real prior correction, but not a
  directly portable value:
  - `configs/5th_axis/5th_axis.ini` used old `5axiskins` values
    `x-offset=0.8625`, `y-offset=37.595`, `pivot-length=180.15`
  - copied SSI configs used old `5axiskins` values `x-offset=-0.48`,
    `y-offset=-37.8`, `pivot-length=263.8795`
  - `configs/sim/head_head_5axis/geometry_baseline.ini` records a previous
    physical spindle-center error of about `2.0 mm`
- Do not copy these values blindly. The old `5axiskins` sign convention and
  offset model differ from current `headheadkins`.
- In the current model, a lateral spindle-center term maps to
  `headheadkins.nominal-b-to-tool.x` / `headheadkins.cal-b-to-tool.x`, but the
  measured X-heavy residual is not proof of that term by itself.
- At only `B2`, a `1.0 mm` local B-to-tool X error creates roughly
  `0.0006 mm` X change and `0.035 mm` Z change relative to `B0`; a `1.0 mm`
  B-to-tool Z/radius error creates roughly `0.035 mm` X change.
- Because the latest residuals are X-heavy with very small Z drift, also keep
  `nominal-b-to-tool.z`, `cal-b-to-tool.z`, `b-zero-offset`, and head/alignment
  error in the candidate list.
- Current startup geometry already includes a fitted fractional B-to-tool X
  term: `nominal-b-to-tool.x = -0.668710`.
- The next wider B/C validation should be used to decide whether this X term or
  the B effective-radius/zero terms need adjustment, instead of compensating the
  symptom with WCS or axis backlash values.

## Wide-Pose TCPC Fixed-Tip Validation - 2026-04-28

Programs:

- `nc_files/calibration/tcpc_wide_pose_vector_sphere_auto.ngc`
- `nc_files/calibration/tcpc_wide_b0c0_closure_resume.ngc`

Logs:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-wide-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-wide-pose-vector-2pass-raw-points.csv`

Setup/state:

- TCPC test config was running with startup TCPC enabled.
- Table still had a mold present; B was kept well inside the
  operator-requested `+/-50 deg` limit.
- Program sequence: `B0 C0`, `B+5 C0`, `B-5 C0`, `B+5 C+20`,
  `B+5 C-20`, closing `B0 C0`.
- Program feeds: probe `F50`, linear positioning `F400`, rotary index `F100`.
- Probe calibration offset used: `0.134533 mm`; loaded probe tool logged as
  `T3`.
- The first full sweep stopped during the closing `B0 C0` correction move
  because the wireless probe had a false trip from nearby laser-cutter
  interference. Accepted rows before the false trip are valid.
- After the laser finished, `tcpc_wide_b0c0_closure_resume.ngc` completed the
  missing closing `B0 C0` two-pass check and appended to the same wide-pose
  logs.

Accepted pass-2 centers, compared to the first accepted `B0 C0` baseline
`X=305.463641 Y=326.084119 Z=-859.744074`:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B0 C0` baseline | +0.000000 | +0.000000 | +0.000000 | 0.000000 |
| `B+5 C0` | +0.052316 | -0.029622 | +0.011232 | 0.061160 |
| `B-5 C0` | +0.031282 | +0.013841 | -0.015301 | 0.037473 |
| `B+5 C+20` | +0.080388 | -0.116445 | +0.008569 | 0.141757 |
| `B+5 C-20` | +0.054128 | +0.054622 | +0.015382 | 0.078422 |
| closing `B0 C0` | -0.006251 | -0.003332 | -0.000334 | 0.007091 |

Interpretation:

- Result is inside the current `0.2 mm` TCPC acceptance target.
- The final closing `B0 C0` repeat is strong, so the wider mixed-pose error is
  real pose-dependent signal rather than sphere/probe drift.
- `B+5 C0` and `B-5 C0` remain small, about `0.061 mm` and `0.037 mm`.
- `B+5 C+20` is the largest error at about `0.142 mm`; `B+5 C-20` is lower at
  about `0.078 mm`.
- The larger errors are mostly XY with small Z change. That points more toward
  C/B geometry interaction, C-axis center/zero/alignment, head squareness, or
  local X/Y mechanics than a simple B effective-radius-only error.
- Do not change offsets from this single wider run. The data is good enough to
  justify one repeated mixed-pose run or an offline sensitivity fit before
  changing `headheadkins` geometry.

## Symmetric Mixed-Pose TCPC Fixed-Tip Validation - 2026-04-28

Program:

- `nc_files/calibration/tcpc_symmetric_pose_vector_sphere_auto.ngc`

Logs:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-symmetric-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-symmetric-pose-vector-2pass-raw-points.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-symmetric-pose-vector-repeat-comparison.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-symmetric-pose-vector-rotary-joint-state.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-symmetric-pose-vector-rotary-ssi-state.csv`

Setup/state:

- TCPC test config was running with startup TCPC enabled.
- Table still had a mold present; B was kept well inside the
  operator-requested `+/-50 deg` limit.
- Morning sun was starting to heat the workshop near the end of the run, so
  some thermal drift may be present in the closing repeat.
- Program sequence: `B0 C0`, `B+5 C+20`, `B+5 C-20`, `B-5 C+20`,
  `B-5 C-20`, closing `B0 C0`.
- Program feeds: probe `F50`, linear positioning `F400`, rotary index `F100`.
- Probe calibration offset used: `0.134533 mm`; loaded probe tool logged as
  `T3`.
- After the repeat comparison, the program was updated to add high-resolution
  rotary state logging on future runs. It now logs LinuxCNC joint command /
  feedback and direct SSI absolute/zeroed/rawcount state for B and C at each
  sphere pass. Values are also logged in microdegrees where useful because the
  RS274 `LOG` output is fixed decimal text.

Accepted pass-2 centers, compared to the first accepted `B0 C0` baseline
`X=305.453432 Y=326.074181 Z=-859.740385`:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B0 C0` baseline | +0.000000 | +0.000000 | +0.000000 | 0.000000 |
| `B+5 C+20` | +0.079358 | -0.112898 | +0.007161 | 0.138184 |
| `B+5 C-20` | +0.053058 | +0.050778 | +0.015637 | 0.075087 |
| `B-5 C+20` | +0.009856 | -0.041648 | -0.013804 | 0.044969 |
| `B-5 C-20` | +0.075391 | +0.071578 | -0.015402 | 0.105093 |
| closing `B0 C0` | +0.110883 | -0.010302 | +0.002601 | 0.111391 |

Interpretation:

- Result is inside the current `0.2 mm` TCPC acceptance target for all tilted
  poses.
- `B+5 C+20` repeated the previous wide-pose result closely:
  about `0.138 mm` here versus about `0.142 mm` in the prior run.
- The mirrored poses do not form a simple one-term B-radius error pattern:
  `B-5 C+20` was low at about `0.045 mm`, while `B-5 C-20` was about
  `0.105 mm`.
- The final closing `B0 C0` repeat moved about `0.111 mm`, mostly in X. This is
  much weaker than the prior wide-pose closure of about `0.007 mm`, so the
  dataset includes thermal drift, return-path, backlash, rotary approach, probe,
  or local axis repeatability signal as well as TCPC geometry.
- Do not change `headheadkins` offsets from this run alone. It is useful as a
  diagnostic, but the closing repeat means geometry fitting must account for
  path-dependent error instead of forcing all residual into TCPC offsets.

Repeat run:

- The same program was rerun immediately after the first symmetric sequence
  while the workshop was heating.
- The second run's starting `B0 C0` accepted center was
  `X=305.561896 Y=326.053880 Z=-859.740621`.
- That starting `B0 C0` was about `0.110 mm` from the first run's starting
  `B0 C0`, mostly in X, but only about `0.011 mm` from the first run's closing
  `B0 C0`.
- The second run closed strongly: final `B0 C0` was only about `0.008 mm` from
  its own starting `B0 C0`.

Second-run accepted pass-2 centers, compared to the second-run `B0 C0`
baseline:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B0 C0` baseline | +0.000000 | +0.000000 | +0.000000 | 0.000000 |
| `B+5 C+20` | -0.040177 | -0.111418 | +0.004629 | 0.118531 |
| `B+5 C-20` | -0.065350 | +0.055040 | +0.013261 | 0.086463 |
| `B-5 C+20` | -0.107270 | -0.035079 | -0.016027 | 0.113992 |
| `B-5 C-20` | -0.042629 | +0.077849 | -0.018752 | 0.090716 |
| closing `B0 C0` | -0.008184 | +0.000750 | +0.001748 | 0.008402 |

Run-to-run absolute repeat of accepted pass-2 centers:

| Pose | dX run2-run1 mm | dY run2-run1 mm | dZ run2-run1 mm | 3D delta mm |
| --- | ---: | ---: | ---: | ---: |
| starting `B0 C0` | +0.108464 | -0.020301 | -0.000236 | 0.110348 |
| `B+5 C+20` | -0.011071 | -0.018821 | -0.002768 | 0.022010 |
| `B+5 C-20` | -0.009944 | -0.016039 | -0.002612 | 0.019051 |
| `B-5 C+20` | -0.008662 | -0.013732 | -0.002459 | 0.016421 |
| `B-5 C-20` | -0.009556 | -0.014030 | -0.003586 | 0.017350 |
| closing `B0 C0` | -0.010603 | -0.009249 | -0.001089 | 0.014112 |

Repeat interpretation:

- The tilted mixed poses repeat well in absolute machine coordinates, about
  `0.016-0.022 mm` run-to-run.
- The first run's large closing shift was effectively carried into the second
  run's starting baseline, then the second run closed at only `0.008 mm`.
- This supports the operator's observation that morning sun / workshop heating
  was starting to move the machine. Treat the baseline movement as thermal or
  setup drift, not a reason to change TCPC offsets.
- The repeat data is good enough to proceed to offline sensitivity analysis,
  but the fit must remove or model common baseline drift before evaluating
  geometry residuals.
- The `0.108-0.111 mm` X-heavy `B0 C0` baseline shift is large enough that a
  very small rotary angular error would matter: with an active B-to-tip radius
  near `309 mm`, `0.108 mm` at the tip is only about `0.020 deg` of B angle.
  However, B and C are closed-loop on direct SSI encoders at the rotary output,
  so a LinuxCNC backlash setting should not leave a static B/C output-position
  split if the feedback loop and SSI readback are repeating. Treat this as a
  reason to verify output repeatability, not as proof of rotary backlash.

High-resolution rotary-state rerun:

- The updated program was rerun after adding LinuxCNC joint and direct SSI
  logging. It completed the starting `B0 C0` and all four tilted poses, then
  stopped on a transient `Probe tripped during non-probe move` during the
  return toward final closing `B0 C0`. The probe input was false after the
  stop, so this is treated as another transient/wireless probe trip. No final
  closing `B0 C0` was logged for this third run.
- Run 3 starting `B0 C0` accepted center:
  `X=305.545620 Y=326.051919 Z=-859.736703`.
- Run 3 accepted tilted-pose drift from its own starting `B0 C0`:
  `0.118766 mm` at `B+5 C+20`, `0.089465 mm` at `B+5 C-20`,
  `0.114091 mm` at `B-5 C+20`, and `0.090701 mm` at `B-5 C-20`.
- Run 3 repeated run 2 closely in absolute coordinates for the shared accepted
  rows: about `0.016-0.019 mm` 3D run-to-run delta.
- Direct SSI rotary logging does not show B-axis output-angle movement large
  enough to explain the `~0.1 mm` TCP pattern. B feedback at `B0` was about
  `-13.7 microdegrees`; at `B+5` it was about `+5.000139 deg`; at `B-5` it was
  between about `-5.000139 deg` and `-4.999796 deg`. The observed B readback
  variation is only about `0.00034 deg`, which is roughly `0.002 mm` at a
  `309 mm` lever arm.
- Since the SSI encoders are direct to the rotary axis output on this build,
  the remaining `~0.09-0.12 mm` pose pattern is more likely TCPC geometry,
  head/spindle assembly compliance or alignment, local linear-axis effects, or
  thermal/setup drift than actual B-axis output-angle drift.
- Trust the direct SSI encoder position as the B/C output position unless the
  logs prove otherwise. Still test B zero, C zero, B/C axis alignment, head
  squareness, and the kinematic geometry mapping separately; those can be wrong
  even when the encoder position is fully repeatable.

Recommended next TCPC check:

- keep the mold/table clearance constraint and stay within `B +/-50 deg`
- keep the laser and other likely wireless-probe noise sources off during
  probing
- do not expand the machine pose envelope while the workshop is heating
- run an offline sensitivity fit using the repeated mixed-pose data, but remove
  common baseline drift before interpreting geometry residuals
- candidate adjustments remain `nominal-c-to-b.x/y`, `nominal-b-to-tool.z`,
  `b-zero-offset`, and `c-zero-offset`
- before changing TCPC geometry, run a focused `B0 C0` approach-repeat test:
  measure the sphere after approaching B0 from `B+5`, then after approaching
  from `B-5`, repeated enough times to check whether the center splits while
  the direct SSI output position remains consistent
- use the new rotary SSI logs in that approach-repeat test. If B SSI readback
  stays within a few hundred microdegrees while the sphere center splits by
  about `0.1 mm`, the error is not B output-angle drift.
- if later stable-temperature repeats show closing drift near `0.1 mm` while
  SSI output angle repeats, focus on thermal/return-path repeatability, linear
  axes, structure, probe behavior, and head alignment before changing TCPC
  offsets
- future machine-control work still needs dedicated B/C feedback, backlash, and
  servo tuning, but do not use TCPC sphere data alone to infer a rotary output
  position error when the SSI encoder says the output is repeating
- B/C zero and alignment testing should remain in scope for TCPC setup. The
  rule is to trust the encoder position measurement, not to assume the physical
  rotary axes are geometrically aligned or correctly zeroed.

## First Small TCPC Geometry Correction - 2026-04-28

Input data:

- repeated symmetric mixed-pose fixed-tip runs at `B +/-5`, `C +/-20`
- run 2 and run 3 tilted-pose centers were repeatable to about
  `0.016-0.019 mm` in absolute coordinates
- direct SSI logging showed B output-angle variation far too small to explain
  the remaining `~0.09-0.12 mm` fixed-tip pattern

Fit interpretation:

- The data has a real ambiguity between a small `B` zero angular correction and
  a small B-to-tool X translation correction.
- Because a `B` zero offset also changes tool-vector orientation, the first
  real-machine correction intentionally avoids changing `b-zero-offset`.
- The common X-heavy residual is not forced into TCPC geometry because it may
  include linear-axis/backlash, approach-state, or thermal/setup drift.

Applied startup HAL correction in the TCPC test config:

```hal
setp headheadkins.cal-b-to-tool.x -0.100000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.030000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

The same values are mirrored to `headheadtwp.*` in
`5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`.

Offline prediction against the run 2/run 3 averaged residuals:

| Pose | Before dr mm | Predicted after dr mm |
| --- | ---: | ---: |
| `B+5 C+20` | 0.118647 | 0.092674 |
| `B+5 C-20` | 0.087949 | 0.079148 |
| `B-5 C+20` | 0.114035 | 0.111451 |
| `B-5 C-20` | 0.090680 | 0.064121 |

This is a conservative first correction, not a final geometry solve. It should
reduce the C-sign Y/Z component while leaving enough of the residual visible to
identify backlash, thermal drift, or other alignment errors.

Follow-up correction:

- Later visual checking showed the vector probing program still used the old B
  lateral sign. This makes the above vector-run fit invalid for final TCPC
  fitting, although the machine stayed within the `0.2 mm` practical target.
- The vector probing files were corrected so `B+ C0` top/down vector motion is
  `X- Z-`, matching the current `headheadkins` convention.

Next validation:

- restart the TCPC test config so the HAL correction loads
- rerun `nc_files/calibration/tcpc_symmetric_pose_vector_sphere_auto.ngc`
- compare against the run 2/run 3 baseline, especially whether Y/Z improve and
  whether the common X residual remains
- if the common X residual remains near `0.05-0.10 mm`, do not keep forcing it
  into TCPC geometry; run the focused B0 approach-repeat/backlash check

## Sign-Corrected TCPC Vector Validation - 2026-04-28

The vector probing math was corrected in:

- `nc_files/calibration/tcpc_symmetric_pose_vector_sphere_auto.ngc`
- `nc_files/calibration/tcpc_small_pose_vector_sphere_auto.ngc`
- `nc_files/calibration/tcpc_wide_pose_vector_sphere_auto.ngc`
- `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc`
- the older B-vector helper programs

The corrected convention is:

```text
B+ C0 top/down vector motion = X- Z-
W = (-sin(B) cos(C), -sin(B) sin(C), -cos(B))
```

Two corrected symmetric runs were completed with the current provisional
startup correction loaded (`cal-b-to-tool.x=-0.100000`,
`cal-b-to-tool.z=+0.030000`).

Run-to-run repeat:

- tilted absolute centers repeated by about `0.016-0.023 mm`
- closing `B0 C0` repeat was `0.011 mm` in run 1 and `0.017 mm` in run 2
- run 2 starting `B0 C0` shifted about `0.022 mm` from run 1, consistent with
  slow machine/setup drift rather than a failed run

Average corrected-run residuals from each run's own starting `B0 C0`:

| Pose | Average dx mm | Average dy mm | Average dz mm | Average dr mm |
| --- | ---: | ---: | ---: | ---: |
| `B+5 C+20` | -0.023644 | -0.111684 | +0.022701 | 0.116394 |
| `B+5 C-20` | -0.046121 | +0.067007 | +0.022439 | 0.084383 |
| `B-5 C+20` | -0.121714 | -0.058205 | -0.011177 | 0.135377 |
| `B-5 C-20` | -0.059513 | +0.090432 | -0.016714 | 0.109540 |

Rejected next startup HAL correction, keeping rotary zero offsets unchanged:

```hal
setp headheadkins.cal-b-to-tool.x -0.200000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.160000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

The same values were mirrored to `headheadtwp.*` for the test only.

Offline prediction for this conservative correction against the averaged
corrected runs:

| Pose | Before dr mm | Predicted after dr mm |
| --- | ---: | ---: |
| `B+5 C+20` | 0.116394 | 0.090254 |
| `B+5 C-20` | 0.084383 | 0.071931 |
| `B-5 C+20` | 0.135377 | 0.121781 |
| `B-5 C-20` | 0.109540 | 0.079068 |

Validation result after restarting with this correction:

| Pose | Previous avg dr mm | Tested dr mm |
| --- | ---: | ---: |
| `B+5 C+20` | 0.116394 | 0.123785 |
| `B+5 C-20` | 0.084383 | 0.094971 |
| `B-5 C+20` | 0.135377 | 0.148197 |
| `B-5 C-20` | 0.109540 | 0.139037 |
| closing `B0 C0` | 0.011-0.017 | 0.006827 |

The test correction made all four tilted poses worse even though the closing
`B0 C0` was stable. Reverted startup HAL to the retained correction:

```hal
setp headheadkins.cal-b-to-tool.x -0.100000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.030000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

Follow-up decision:

- The retained `-0.100000/+0.030000` correction was also rooted in the old
  wrong-sign vector data.
- To restart the fit cleanly, the TCPC test config calibration corrections were
  reset to zero while keeping the nominal starting geometry unchanged:

```hal
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.000000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset 0.000000
```

Next validation should restart the TCPC config, rerun the corrected symmetric
vector program, and use that as the clean sign-corrected baseline before any
new TCPC correction is applied.

## Zero-Correction Clean Baseline - 2026-04-28

The TCPC config was restarted with all `cal-*` corrections reset to zero and
the corrected symmetric vector program was run twice.

Run 1 residuals from that run's starting `B0 C0`:

| Pose | dx mm | dy mm | dz mm | dr mm |
| --- | ---: | ---: | ---: | ---: |
| `B+5 C+20` | +0.014929 | -0.032846 | -0.000684 | 0.036086 |
| `B+5 C-20` | -0.001698 | +0.015523 | -0.000255 | 0.015618 |
| `B-5 C+20` | -0.076620 | +0.026219 | +0.002053 | 0.081008 |
| `B-5 C-20` | -0.005839 | +0.034674 | -0.005994 | 0.035669 |
| closing `B0 C0` | +0.045068 | +0.009373 | -0.000636 | 0.046037 |

Run 2 residuals from that run's starting `B0 C0`:

| Pose | dx mm | dy mm | dz mm | dr mm |
| --- | ---: | ---: | ---: | ---: |
| `B+5 C+20` | -0.036371 | -0.030673 | +0.000550 | 0.047581 |
| `B+5 C-20` | -0.050467 | +0.009512 | +0.000518 | 0.051358 |
| `B-5 C+20` | -0.126345 | +0.021870 | +0.001949 | 0.128239 |
| `B-5 C-20` | -0.059294 | +0.032991 | -0.005628 | 0.068087 |
| closing `B0 C0` | +0.010547 | +0.002356 | -0.000270 | 0.010810 |

Repeat interpretation:

- Tilted absolute centers repeated well, about `0.013-0.019 mm` between the
  two zero-correction runs.
- The two final closing `B0 C0` centers repeated extremely well, about
  `0.0015 mm` 3D.
- The starting `B0 C0` center changed about `0.036 mm` between runs, so using
  the starting `B0` as the only reference can misread return-state, thermal,
  probe, linear-axis, or structural movement as TCPC geometry error.
- With zero correction, all small tilted poses remain inside the current
  `0.2 mm` target, and most are inside or near the `0.1 mm` refinement target.

Decision:

- Keep TCPC calibration corrections at zero for now.
- Do not fit new offsets from this small-angle dataset alone.
- Next useful check is a B0 approach/reversal diagnostic or a controlled wider
  pose range, still within current mold clearance limits, to prove direct SSI
  rotary output repeatability and separate TCPC geometry from machine
  alignment, structure, thermal, probe, or linear-axis effects.

## Handoff For 3-Axis Machine Use - 2026-04-28

TCPC testing is paused while the machine is used for 3-axis work. For normal
3-axis setup/cutting, keep using the existing `trivkins` maintenance/setup
configs, not the TCPC test config.

Current TCPC state to return to:

- TCPC config starts with the nominal first-pass geometry loaded.
- All TCPC calibration corrections remain zero:
  `cal-b-to-tool.x/y/z = 0`, `cal-c-to-b.x/y/z = 0`,
  `b-zero-offset = 0`, and `c-zero-offset = 0`.
- The corrected vector probing convention is active in the TCPC validation
  programs: `B+ C0` top/down vector motion is `X- Z-`.
- `G55` remains locked out for staff 3-axis work unless the operator releases
  it.

Prepared next calibration program:

- `nc_files/calibration/tcpc_b0_approach_reversal_sphere_auto.ngc`

Purpose:

- measure the same `B0 C0` sphere position after alternating approaches from
  `B+5` and `B-5`
- determine whether the observed `B0` start/close split occurs while direct SSI
  B/C output position remains repeatable before applying any new TCPC geometry
  correction
- log direct SSI and LinuxCNC rotary feedback at each accepted sphere pass

Start conditions for the next session:

- launch the TCPC test config only after the 3-axis work is finished
- restart near a known safe C side, preferably `C0`
- confirm `TCPC ON`, TWP not active, and the probe tool/diameter/calibration
  offset are valid in Probe Basic
- place the probe close to sphere center, about `5 mm` above the sphere top
- keep probing feed `F50`, rotary index `F100`, and linear positioning `F400`
- keep B within `+/-5 deg`; this diagnostic stays well inside the current
  `+/-50 deg` table/mold clearance limit

2026-04-29 feed update for future TCPC validation programs:

- keep probing feed at `F50`
- increase linear positioning to `F600`
- increase rotary indexing to `F200`
- the currently running B0 approach/reversal file was not edited mid-cycle;
  update or reload it only after the active run finishes

New logs for that program:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b0-approach-reversal-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b0-approach-reversal-raw-points.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b0-approach-reversal-rotary-ssi-state.csv`

## B0 Approach/Reversal Diagnostic - 2026-04-29

Program:

- `nc_files/calibration/tcpc_b0_approach_reversal_sphere_auto.ngc`

Result from accepted pass-2 sphere centers:

- `B+5 -> B0` average center:
  `X=357.572052 Y=317.960266 Z=-859.746267`
- `B-5 -> B0` average center:
  `X=357.693774 Y=317.959641 Z=-859.745489`
- minus-plus split:
  `dX=+0.121722 dY=-0.000625 dZ=+0.000778`, 3D `0.121726 mm`

Direct SSI result:

- `B+5 -> B0` average direct B SSI zeroed position: `-0.001899 deg`
- `B-5 -> B0` average direct B SSI zeroed position: `+0.020303 deg`
- split: `0.022202 deg`, about `64.7` raw SSI counts
- at a `309 mm` B-to-tip lever arm, `0.022202 deg` is about `0.119735 mm`

Interpretation:

- The sphere X split matches the direct SSI B output-position split.
- This is not an encoder trust problem. The encoder data is doing its job and
  showing that the B output position is being shifted by the control path.
- The TCPC config still had `[JOINT_3]BACKLASH = 0.022`, and C had
  `[JOINT_4]BACKLASH = 0.010`.
- With direct SSI feedback at the rotary output, LinuxCNC backlash
  compensation should not be active for B/C during TCPC calibration because it
  intentionally changes `joint.N.motor-pos-cmd` while logical
  `joint.N.pos-cmd` remains at the target.

Applied TCPC-test-config-only change:

```ini
[JOINT_3]
BACKLASH = 0.0

[JOINT_4]
BACKLASH = 0.0
```

Restart LinuxCNC before rerunning the B0 approach/reversal diagnostic. The
expected result after restart is that `B+5 -> B0` and `B-5 -> B0` direct SSI
B positions should both settle near the same B0 output position, and the
`~0.12 mm` X split should largely disappear if no other issue is present.

Post-restart validation with B/C backlash disabled:

- live HAL confirmed `joint.3.backlash-corr = 0` and
  `joint.4.backlash-corr = 0`
- accepted `B+5 -> B0` average center:
  `X=357.701305 Y=317.959849 Z=-859.749323`
- accepted `B-5 -> B0` average center:
  `X=357.705402 Y=317.958947 Z=-859.749101`
- minus-plus sphere split:
  `dX=+0.004097 dY=-0.000903 dZ=+0.000222`, 3D `0.004201 mm`
- direct B SSI zeroed-position split: `0.000000 deg`
- raw SSI count split: `0.0 counts`

Conclusion:

- Disabling LinuxCNC B/C backlash compensation in the TCPC test config removed
  the approach-dependent rotary output split.
- The previous `~0.122 mm` X split was not TCPC geometry and not encoder
  inconsistency; it was caused by applying software backlash compensation on a
  direct-output closed-loop rotary axis.
- Keep B/C backlash compensation disabled for TCPC testing unless a later
  dedicated servo-tuning session proves a different strategy.
- Next TCPC geometry validation should rerun the corrected symmetric mixed-pose
  program with zero TCPC calibration correction and the updated `F600/F200`
  positioning/indexing feeds.

## Symmetric TCPC Validation After Backlash Disable - 2026-04-29

Program:

- `nc_files/calibration/tcpc_symmetric_pose_vector_sphere_auto.ngc`

Setup/state:

- TCPC test config running with B/C backlash compensation disabled.
- TCPC calibration corrections still zero.
- Program feeds: probe `F50`, linear positioning `F600`, rotary index `F200`.
- A prior attempt stopped due to probe double-pulse noise on retract. Treat
  that partial block as invalid probe-state noise; use only the last complete
  12-row block.

Accepted pass-2 centers, compared to the first accepted `B0 C0` baseline
`X=357.759398 Y=317.984091 Z=-859.762739`:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B0 C0` baseline | +0.000000 | +0.000000 | +0.000000 | 0.000000 |
| `B+5 C+20` | -0.085056 | -0.027580 | +0.001823 | 0.089434 |
| `B+5 C-20` | -0.098608 | -0.024933 | +0.004344 | 0.101804 |
| `B-5 C+20` | +0.087016 | +0.046468 | +0.010702 | 0.099225 |
| `B-5 C-20` | +0.093463 | -0.031996 | +0.006527 | 0.099003 |
| closing `B0 C0` | +0.001956 | +0.002597 | -0.002974 | 0.004406 |

Rotary SSI state in the same accepted pass-2 rows:

- starting and closing `B0 C0` direct B SSI zeroed position matched:
  `0.020303 deg`
- B/C rotary feedback is repeating well enough that the remaining
  `~0.09-0.10 mm` tilted-pose pattern should be treated as TCPC geometry,
  rotary zero/alignment, head alignment, linear-axis, probe, or structure
  signal, not backlash-compensation artifact

Interpretation:

- Removing B/C backlash compensation fixed the `B0` return problem.
- The current zero-correction TCPC result is inside the practical `0.2 mm`
  target and close to the refinement target.
- The residuals are now strongly sign-symmetric in B: `B+` poses are mostly
  negative X and `B-` poses mostly positive X. This points toward B-axis zero,
  B effective radius / B-to-tool Z, or B/C/head alignment rather than random
  probe drift.
- Do not change TCPC geometry from one post-fix run alone. Recommended next
  step is one repeat of the same symmetric program to confirm repeatability,
  then run an offline sensitivity fit for small B-zero and B-radius/tool-vector
  changes.

Repeat run:

- The same symmetric program was run again immediately after the first valid
  post-fix set.
- Closing `B0 C0` drift from that run's starting `B0 C0` was `0.004268 mm`.
- Tilted-pose drifts from that run's starting `B0 C0` were:
  - `B+5 C+20`: `0.090721 mm`
  - `B+5 C-20`: `0.100395 mm`
  - `B-5 C+20`: `0.100939 mm`
  - `B-5 C-20`: `0.099441 mm`
- Accepted pass-2 centers repeated against the previous valid post-fix run
  within `0.002441-0.005595 mm` 3D at all comparable poses.

Repeat interpretation:

- The post-backlash-disable symmetric data is now stable and fit-worthy.
- The remaining `~0.09-0.10 mm` tilted-pose pattern is repeatable, so it is no
  longer appropriate to attribute it to B backlash compensation or random
  probe noise.
- It is reasonable to proceed to the expanded C-quadrant / B `+/-50` matrix
  before fitting corrections, because the larger data set will better separate
  TCPC geometry from rotary zero/alignment and other mechanical effects.

## Expanded TCPC Alignment Data Set - 2026-04-29

Program:

- `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc`

Purpose:

- collect a larger B/C matrix to separate pure TCPC geometry from rotary zero,
  C-axis center/zero, B-axis alignment, head/spindle alignment, local linear
  axis error, probe behavior, and structural effects
- keep direct B/C SSI and LinuxCNC joint state logged at each pass

Machine/setup constraint:

- operator confirmed full C-axis scope is available and B can run to
  `+/-50 deg` comfortably
- the calibration sphere is mounted on a `45 deg` post; the known concern area
  is around `C45` with negative B more than `-10 deg`
- `C225` is acceptable per operator clearance assessment
- first expanded program uses C quadrants only, `C0/C90/C180/C270`, so it does
  not command the known risky `C45 / B < -10` sector

Pose groups:

- B0 C quadrants, then B0 C0 closure
- B `+/-10` at C quadrants, then B0 C0 closure
- B `+/-30` at C quadrants, then B0 C0 closure
- B `+/-50` at C quadrants, then final B0 C0 closure

Safety behavior:

- probe feed `F50`, linear positioning `F600`, rotary indexing `F200`
- the program pauses between B0, `+/-10`, `+/-30`, and `+/-50` groups
  using `M0`
- monitor the first B `+50/-50` group closely for support/post clearance,
  especially if later variants add C angles near `45 deg`

Logs:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-expanded-pose-vector-2pass-results.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-expanded-pose-vector-2pass-raw-points.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-expanded-pose-vector-rotary-joint-state.csv`
- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-expanded-pose-vector-rotary-ssi-state.csv`

Completed run summary:

- results file contains `64` result rows: `32` pass-1 rows and `32` accepted
  pass-2 centers
- raw-points file contains `320` data rows
- initial accepted `B0 C0` center:
  `X357.767490 Y317.985009 Z-859.767655`
- `B0 C0` closure drift from the first accepted baseline:
  - after B0 C-only group: `0.006710 mm`
  - after B `+/-10` group: `0.011584 mm`
  - after B `+/-30` group: `0.010126 mm`
  - final after B `+/-50` group: `0.017328 mm`
- group maximum 3D drift from each group's preceding `B0 C0` closure:
  - B0 C-only group: `0.144343 mm` at `B0 C180`
  - B `+/-10` group: `0.278010 mm` at `B-10 C0`
  - B `+/-30` group: `0.796227 mm` at `B-30 C90`
  - B `+/-50` group: `1.316641 mm` at `B-50 C90`
- accepted corrected diameters remain high but stable enough for center
  diagnostics:
  - U corrected diameter min/max/avg:
    `30.132102 / 30.303764 / 30.192689 mm`
  - V corrected diameter min/max/avg:
    `30.160500 / 30.213012 / 30.197181 mm`
- accepted rotary following error was small during the expanded run:
  - B maximum absolute following error about `229 microdeg`
  - C maximum absolute following error about `2403 microdeg`

Interpretation:

- The closure data is good enough to treat the expanded residual pattern as
  real pose-dependent geometry/alignment signal.
- The B0 C-only `0.144 mm` movement means C-axis center/zero/alignment still
  matters and should be included in the fit.
- Error growth with B angle, especially around `B-30/B-50 C90`, points to
  B-axis geometry, B zero, B-to-tool vector, head/spindle alignment, or axis
  squareness effects rather than servo following error.
- Do not apply a large correction directly from the expanded data. Use a small
  first offline sensitivity fit, then validate with the symmetric program and
  a reduced expanded subset.

## Offline Fit Candidate From Expanded Data - 2026-04-29

Fit method:

- use accepted pass-2 centers from
  `tcpc-expanded-pose-vector-2pass-results.csv`
- subtract the preceding accepted `B0 C0` closure for each pose group to reduce
  thermal/setup drift influence
- fit only physically modest terms first; do not use the full eight-parameter
  least-squares solution because `B` zero, B-to-tool X, and B-to-tool Z are
  highly correlated over this data set

Stable diagnostic fit:

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

Mirror the same values to `headheadtwp.*` if this candidate is applied to the
TCPC test overlay.

Applied state for the next TCPC session:

- the full simple candidate is now loaded in
  `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`
- the matching `headheadtwp.*` pins are mirrored to the same values
- the candidate only takes effect after restarting the TCPC test config

Why this fit is preferred as the first correction:

- it uses only simple TCPC geometry terms: C/B lateral X-Y, B-to-tool Z, and a
  small C zero offset
- it avoids B-to-tool X and B zero for now because those terms are not cleanly
  separated by the current data
- it matches the repeated symmetric data reasonably while not overfitting the
  small-angle set

Predicted effect using the expanded matrix:

- current group-baselined expanded RMS 3D residual: `0.513 mm`
- predicted RMS after candidate: about `0.167 mm`
- current worst group-baselined residual: `1.190 mm` at `B-50 C90`
- predicted worst residual after candidate: about `0.437 mm`, still at
  `B-50 C90`
- predicted B `+/-30` worst residual after candidate: about `0.196 mm`

Predicted effect on the last symmetric repeat:

- current tilted-pose RMS 3D residual: about `0.098 mm`
- predicted tilted-pose RMS after candidate: about `0.030 mm`
- predicted worst symmetric tilted-pose residual after candidate:
  about `0.034 mm`

Conservative half-step option:

```hal
setp headheadkins.cal-c-to-b.x -0.033000
setp headheadkins.cal-c-to-b.y 0.007000
setp headheadkins.cal-c-to-b.z 0.000000
setp headheadkins.cal-b-to-tool.x 0.000000
setp headheadkins.cal-b-to-tool.y 0.000000
setp headheadkins.cal-b-to-tool.z 0.408000
setp headheadkins.b-zero-offset 0.000000
setp headheadkins.c-zero-offset -0.012000
```

The half-step predicts only about `0.065 mm` worst residual on the symmetric
check, but it does not correct the high-B expanded matrix enough. Use it only
if we want a very cautious first no-cut confirmation of correction direction.

Recommended next TCPC validation sequence:

1. Leave the current 3-axis maintenance work alone; do not load the TCPC config
   while production/setup work is active.
2. When TCPC resumes, restart the TCPC test overlay so the full simple
   candidate loads.
3. Restart the TCPC config at a known safe C side of the wrap, preferably C0,
   then home.
4. Confirm TCPC ON, TWP OFF, B/C backlash compensation zero, probe tool `T3`,
   and probe calibration offset `0.134533`.
5. Run `nc_files/calibration/tcpc_symmetric_pose_vector_sphere_auto.ngc`.
6. If the full candidate is used, expect all tilted symmetric residuals to be
   well under `0.08 mm` and closing `B0 C0` under `0.02 mm`; stop and revert if
   the residuals grow or signs reverse.
7. If symmetric validation passes, run the expanded program. It now defaults
   to B `+/-30` only with `#707 = 30.0`.
8. If B `+/-30` is inside about `0.20-0.25 mm`, decide whether to run the
   B `+/-50` group by deliberately changing `#707` to `50.0`. Remaining high-B
   residual is likely alignment/squareness work, not a simple TCPC offset fit.

## Correction Candidate Validation - 2026-04-29

The full simple correction candidate above was loaded by restarting the TCPC
test config. Live correction state:

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

Validated checks:

- TCPC correction direction was visually correct in all C quadrants after the
  correction was loaded.
- The corrected symmetric run completed with tilted-pose drift of
  `0.006759-0.044784 mm` from its own `B0 C0` baseline and a closing `B0 C0`
  drift of `0.021471 mm`.
- The corrected expanded B `+/-30` validation completed. From each preceding
  `B0 C0` closure, max/RMS drift was:
  - B0 C-only group: max `0.084764 mm`, RMS `0.068839 mm`, closure
    `0.003543 mm`
  - B `+/-10` group: max `0.099723 mm`, RMS `0.064420 mm`, closure
    `0.007116 mm`
  - B `+/-30` group: max `0.171569 mm`, RMS `0.116421 mm`, closure
    `0.005957 mm`
- This validates the candidate inside the current `0.2 mm` practical target
  through B `+/-30`.

B `+/-50` diagnostic result:

- Repeated first attempts were interrupted by wireless/optical probe faults,
  logged by Probe Basic as `Probe tripped during non-probe move`.
- The operator reset the probe/receiver and repeated the run after the
  workshop closed; this produced a complete clean B `+/-50` data block.
- Latest clean block starts at data row `200` in
  `tcpc-expanded-pose-vector-2pass-results.csv`.
- Initial accepted `B0 C0` baseline:
  `X=357.587972 Y=317.971169 Z=-858.934552`.
- After the B `+/-30` group, closure from that baseline was `0.019881 mm`.
- B `+/-30` group max/RMS drift from the fresh baseline:
  max `0.175977 mm` at `B-30 C90`, RMS `0.122098 mm`.
- B `+/-50` group used the B30 closure as its baseline:
  `X=357.571222 Y=317.965505 Z=-858.925464`.
- B `+/-50` group max/RMS drift from that baseline:
  max `0.427632 mm` at `B-50 C90`, RMS `0.266161 mm`.
- Final `B0 C0` closure after the B `+/-50` group was `0.014415 mm` from the
  B50 group baseline.
- Overall start-to-final `B0 C0` closure across the clean block was
  `0.032135 mm`.
- Accepted pass-2 rotary following error stayed small: B max about
  `229 microdeg`, C max about `1030 microdeg`.
- Corrected diameters across the accepted clean block remained high but
  stable: U min/max/avg `30.133994 / 30.206677 / 30.168536 mm`, V min/max/avg
  `30.158000 / 30.225500 / 30.195040 mm`.

Interpretation:

- The candidate is validated through B `+/-30` inside the current `0.2 mm`
  practical target.
- B `+/-50` is now useful diagnostic data and closely matches the earlier
  offline prediction. Remaining high-B error is more likely head/spindle
  alignment, axis squareness, or mechanical geometry than a simple TCPC offset
  term.

Program state after lock-in:

- `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc` has been
  restored to safe defaults: `#706 = 1.0`, `#707 = 30.0`, `#708 = 0.0`,
  `#709 = 10.0`.
- The program now supports an explicit optional B `+/-60` diagnostic. For a
  B60-only extension after the completed B50 run, deliberately set:
  `#707 = 60.0`, `#708 = 1.0`, and `#709 = 60.0`.
- Do not leave B60 as the default. Use it only after confirming clearance,
  probe receiver stability, and no active workshop optical interference.

## Handoff After B50 Validation - 2026-04-29

The TCPC session has a complete corrected B `+/-50` validation data set.

Current TCPC test-config state to return to:

- B/C LinuxCNC backlash compensation disabled in the TCPC test config
- direct SSI rotary logging is available for symmetric and expanded programs
- the first simple correction candidate is loaded in the TCPC test config and
  mirrored to `headheadtwp.*`
- corrected symmetric validation and corrected B `+/-30` expanded validation
  passed inside the current `0.2 mm` practical target
- corrected B `+/-50` validation completed with max `0.427632 mm` at
  `B-50 C90`, RMS `0.266161 mm`, and final closure `0.014415 mm`
- the active expanded program is restored to safe defaults but supports a
  deliberate B `+/-60` extension with `#707 = 60.0`, `#708 = 1.0`, and
  `#709 = 60.0`

For 3-axis work:

- close the TCPC config and use a normal `trivkins` maintenance/setup config
- keep `G55` reserved for staff 3-axis setup work unless the operator releases
  it
- do not use the TCPC test config for cutting
- when TCPC resumes, restart at a known safe C side of the wrap, preferably
  C0, home, confirm TCPC status, then run only slow no-cut validation first

Future servo-tuning scope:

## Shutdown Handoff - 2026-04-30

Machine/testing state:

- The late-night full expanded TCPC sweep was stopped by repeat wireless probe
  false trips at the B60 stage.
- The operator confirmed the probe flashed with no contact; treat these stops
  as optical/wireless false trips, not sphere contact.
- The sphere was moved after the B60 false-trip attempts. Any future data must
  start as a fresh data set; do not continue a resume block from the old sphere
  position.
- Current log boundary after the moved sphere is:
  `tcpc-expanded-pose-vector-2pass-results.csv` line `314`,
  raw-points line `1566`, rotary joint line `314`, rotary SSI line `314`.
  The next morning full rerun starts at result line `315`.

Useful data before the sphere moved:

- Rows `243-306` are the best late-night full rerun through B `+/-50` closure.
- Rows `307-314` are incomplete B60 attempts. They are trend/clearance data
  only and should not be used for a final TCPC fit.
- Rows `243-306` B0 closure stayed good:
  final `B0 C0` after B `+/-50` was `0.010627 mm` from the run baseline.
- Rows `243-306` B `+/-30` remained inside the current practical target:
  max drift `0.169504 mm`, average group drift about `0.11-0.12 mm`.
- Rows `243-306` B `+/-50` remained outside the `0.2 mm` practical target:
  B+50 max `0.355050 mm`; B-50 max `0.404233 mm`.
- Rotary feedback was not the limiting error in that block. Accepted pass-2
  following error stayed about B `305 microdeg` max and C `1030 microdeg` max.

First-pass TCPC/mechanical interpretation:

- There is enough data for first-pass analysis and mechanical fault direction.
  There is not enough for a final geometry fit because B60 is incomplete, the
  sphere moved, and the probe false trips disturbed the end of the session.
- A direct TCPC-parameter least-squares fit only modestly improves the late
  full-run RMS, from about `0.155 mm` to about `0.142 mm` using the practical
  `cal-c-to-b.x/y`, `cal-b-to-tool.x/z`, and C-zero terms.
- The weak fit improvement means the remaining high-B error is not behaving
  like one clean kinematic offset. Treat it as mixed geometry plus machine
  alignment/mechanical error until a stable repeat confirms otherwise.
- The stable B0 closures argue against simple thermal drift or random probing
  as the main high-B error source.
- Primary suspects to investigate after a stable repeat:
  B-axis/spindle centerline offset or tilt, B-to-spindle squareness, C/B
  non-intersection or squareness, local linear-axis mechanics under large head
  angle, and Z rack/local motion effects.

Program state for the next morning:

- `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc` is set for a
  fresh full B `+/-60` rerun, not resume mode.
- Current run controls are:
  `#704 = 1.0` pause before each probing pose,
  `#706 = 1.0` pause between B groups,
  `#707 = 60.0` full B `+/-60`,
  `#708 = 0.0` no resume,
  `#709 = 10.0` start at B `+/-10`.
- The program includes `#515 = 5.0`, a +5 mm Z lift before rotary index moves.
- The experimental supervised `G38.3` travel retry idea was not left in the
  active file for the morning run. Revisit that later as a separate surface
  probing/noisy-probe robustness task.

- The B/C closed-loop SSI feedback path is functional but has not been
  fine-tuned.
- Current rotary following-error limits are intentionally loose enough to avoid
  nuisance faults during commissioning: `FERROR = 2 deg` and
  `MIN_FERROR = 0.5 deg`.
- At the current B-to-tip lever arm, those limits are far larger than the TCPC
  calibration target, so they are commissioning values, not production TCPC
  quality limits.
- Schedule a dedicated servo-motion tuning session for all axes, with special
  focus on B/C rotary feedback loops, following-error limits, PID gains,
  feed-forward, acceleration limits, and final backlash/compensation strategy.
- Do not use TCPC sphere residuals alone as a substitute for servo loop tuning.

## Diagnostic Half-Step Loaded - 2026-04-30

After the completed B `+/-90` expanded matrix, the data is now sufficient for a
small intent-verification correction. The aim is to check whether the high-B
residuals move in the predicted direction, not to create final production
compensation.

Latest clean group-baselined pass-2 residuals:

- B `+/-30`: RMS `0.115 mm`, max `0.163 mm`
- B `+/-50`: RMS `0.244 mm`, max `0.390 mm`
- B `+/-60`: RMS `0.317 mm`, max `0.534 mm`
- B `+/-90`: RMS `0.566 mm`, max `0.891 mm`

Linear-travel correlation against the current TCPC model ranked apparent
contributors as:

- Z error versus large Z travel, about `-1.1 mm/m`
- Y error versus large Y travel, about `-0.8 mm/m`
- Z error versus Y travel, about `-0.4` to `-0.5 mm/m`

These are diagnostic correlations only. They may represent real axis
scale/squareness error, but they may also be the projection of B/C head
geometry errors through the TCPC motion.

Loaded test-only half-step correction, relative to the previous validated
candidate:

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

Predicted half-step effect:

- B `+/-30`: RMS `0.115` to `0.113 mm`, max `0.163` to `0.154 mm`
- B `+/-50`: RMS `0.244` to `0.214 mm`, max `0.390` to `0.305 mm`
- B `+/-60`: RMS `0.317` to `0.265 mm`, max `0.534` to `0.440 mm`
- B `+/-90`: RMS `0.566` to `0.477 mm`, max `0.891` to `0.774 mm`

The expanded program has been reset to a fresh verification path:

```ngc
#704 = 0.0
#706 = 1.0
#707 = 60.0
#708 = 0.0
#709 = 10.0
#710 = 0.0
#515 = 25.0
```

Validation rule:

- If B `+/-30` gets worse, revert immediately.
- If B `+/-30` stays stable and B `+/-50`/B `+/-60` improve, keep this as a
  direction-confirming diagnostic and continue separating axis squareness,
  pitch/rack compensation, and rotary-head geometry.
- If high-B residuals do not move as predicted, do not keep fitting TCPC
  offsets from this data. Move to direct axis alignment and pitch/rack tests.

## Probe Gate Observation - 2026-04-30

The current supervised gate around `G38.3` probe moves is validated in practice.
The operator saw the wireless probe double-flash about `3-4` times during the
last full run, but the gated probe input prevented those post-contact pulses
from stopping retract or transport moves.

Likely cause is the probe low-battery alarm behavior. Replacement batteries are
on order. Future robustness work should add a timed post-contact filter/alarm:

- after a valid probe touch, suppress extra probe pulses for about `2-3`
  seconds
- if a pulse occurs in that suppression window, show/log a low-battery or
  double-pulse warning
- do not stop the active program for that warning
- never suppress the probe signal during an intentional `G38` move

Keep this separate from TCPC fitting. The current gate is sufficient for the
next supervised TCPC verification run.

## Half-Step Failed, Opposite Test Prepared - 2026-04-30

The diagnostic half-step loaded after the B `+/-90` matrix was tested through
B `+/-50` and then stopped. It failed the pass/fail rule:

- new half-step run starts at data row `432` in
  `tcpc-expanded-pose-vector-2pass-results.csv`
- B0 C-only sweep was essentially unchanged: previous RMS `0.101 mm`, new RMS
  `0.098 mm`
- B `+/-30` worsened: RMS `0.115 mm` to `0.143 mm`; max `0.163 mm` to
  `0.216 mm`
- B `+/-50` worsened: RMS `0.244 mm` to `0.297 mm`; max `0.390 mm` to
  `0.497 mm`
- B0 closures remained good: B30 closure `0.006 mm`, B50 closure `0.004 mm`

Interpretation:

- The failed result is not caused by general probing repeatability or B0 C
  closure drift.
- The correction-family direction was wrong for tilted B poses.
- The old-to-new residual delta is mostly reversible, so the opposite
  empirical half-step is a valid next small direction test.
- This still does not prove a final TCPC geometry correction; it is only a
  controlled sign/direction check.

Empirical opposite-half prediction, using `residual_next ~= 2*old - failed`:

- B `+/-30`: RMS about `0.107 mm`, max about `0.134 mm`
- B `+/-50`: RMS about `0.213 mm`, max about `0.286 mm`

Prepared next startup correction in the TCPC test overlay:

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

Prepared next probing default:

```ngc
#704 = 0.0
#706 = 1.0
#707 = 30.0
#708 = 0.0
#709 = 10.0
#710 = 0.0
#515 = 25.0
```

Next-session validation sequence:

1. Restart the TCPC config so the opposite correction loads.
2. Home and set up above the calibration sphere at B0 C0.
3. Run the expanded program as configured, B `+/-30` only.
4. Stop and revert if B `+/-30` is worse than the prior validated candidate.
5. If B `+/-30` improves, deliberately change `#707` to `50.0` and run B
   `+/-50`; keep B60 for a later confirmation only after B50 passes.

Prior validated candidate to revert to if needed:

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

## Opposite Test Rejected, Reverted - 2026-05-02

The empirical opposite-half correction was tested twice. The first run was
accidentally run at 200% feed override and was treated as diagnostic only. The
second run at 100% feed override still failed against the prior validated
candidate:

- B `+/-30` RMS was about `0.138 mm`, max about `0.193 mm`, worse than the
  prior validated B `+/-30` result of RMS `0.115 mm`, max `0.163 mm`.
- The B0 C-only sweep also worsened, with RMS about `0.179 mm` and max about
  `0.227 mm`.
- The result confirms the opposite-half correction should not be kept.

Action applied after the failed run:

- `5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` has been reverted to the prior
  validated candidate:
  `cal-c-to-b.x=-0.065000`, `cal-c-to-b.y=0.014000`,
  `cal-b-to-tool.x=0.000000`, `cal-b-to-tool.z=0.815000`,
  `c-zero-offset=-0.024500`.
- The same values are mirrored to `headheadtwp.*`.
- `tcpc_expanded_pose_vector_sphere_auto.ngc` is set for B `+/-30` validation
  only with probe feed `F50`, linear transit/positioning `F1200`, rotary index
  `F200`, and `#707 = 30.0`.

The attempted rerun after reverting was stopped during the B-30 group because
the wireless probe showed a constant flash, indicating batteries need
replacement. Treat that interrupted run as non-usable for TCPC fitting or
comparison.

Next resume after new probe batteries:

1. Restart the TCPC Probe Basic config and confirm only one LinuxCNC instance
   is running.
2. Home all axes, verify probe tool/diameter/calibration offset state, and set
   up over the calibration sphere at B0 C0.
3. Run the expanded program as currently configured for B `+/-30` only at 100%
   feed override.
4. Compare the clean run against the prior validated B `+/-30` target: RMS
   about `0.115 mm`, max about `0.163 mm`, and B0 closure about `0.009 mm`.
5. Only expand back to B `+/-50` after the reverted B `+/-30` result matches
   the prior candidate.

## Shutdown Handover - 2026-05-02 20:50 +07

Machine TCPC calibration is paused for several days while replacement wireless
probe batteries are on order. The PC may be fully shut down.

Do not continue TCPC probing with the current probe battery state. The constant
flash seen during the B-30 group indicates the probe signal is not trustworthy
enough for fitting data. Existing gated-probe handling remains useful for
post-contact double flashes, but it is not a substitute for a healthy probe
battery.

Resume sequence after battery replacement:

1. Start the TCPC Probe Basic config from the desktop launcher or
   `launch_xyzbc_ssi_tcpc_probe_basic.sh`.
2. Confirm only one LinuxCNC/Probe Basic instance is running.
3. Home all axes and verify the probe setup over the calibration sphere.
4. Run the current B `+/-30` validation program at 100% feed override.
5. Treat the interrupted low-battery B-30 run as invalid and compare only the
   clean post-battery run against the prior validated candidate.

## B90 C-Quadrant Diagnostic Complete - 2026-05-04

`tcpc_b90_c_quadrant_diagnostic.ngc` completed after a C90 resume. The program
had previously stopped at `B+90 C90` because the preceding `B0 C90` pass 2 was
corrupt: it false-touched high in Z and accepted corrected diameters
`29.700500` and `29.739667`. That row remains in the CSV for traceability but
must be excluded from fitting.

Files:

- results:
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b90-c-quadrant-diagnostic-2pass-results.csv`
- raw points:
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b90-c-quadrant-diagnostic-2pass-raw-points.csv`
- axis state:
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b90-c-quadrant-diagnostic-axis-state.csv`
- rotary joint/SSI state:
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b90-c-quadrant-diagnostic-rotary-joint-state.csv`
  and
  `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b90-c-quadrant-diagnostic-rotary-ssi-state.csv`

Current live/reverted kinematics during this run:

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

Exclude:

- line `13` in the results CSV:
  `B0 C90`, pass 2, center `468.839714,323.565782,-856.066624`,
  diameters `29.700500/29.739667`.

Valid B0 C-axis orbit from pass-2 accepted rows:

| C | mean X | mean Y | mean Z | dX from C0 | dY from C0 | dZ from C0 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `468.760084` | `323.675216` | `-858.976929` | `0.000000` | `0.000000` | `0.000000` |
| `90` | `468.851656` | `323.569747` | `-858.956054` | `+0.091572` | `-0.105469` | `+0.020875` |
| `180` | `468.964434` | `323.666878` | `-858.941637` | `+0.204350` | `-0.008337` | `+0.035291` |
| `270` | `468.861386` | `323.768933` | `-858.950276` | `+0.101302` | `+0.093717` | `+0.026653` |

This is a strong C-axis center/orbit signature. In the current fit convention,
the orbit corresponds to roughly `0.102 mm` X center error and very small Y
error. Do not apply sign directly; verify by simulating `headheadkins` inverse
behavior first.

Valid B90 local deltas, each compared to the average of adjacent B0 closures at
the same C:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.050270` | `-0.204791` | `+0.071000` | `0.222503` |
| `B-90 C0` | `-0.165771` | `-0.126459` | `+0.617562` | `0.651809` |
| `B+90 C90` | `-0.104999` | `-0.190271` | `-0.011188` | `0.217608` |
| `B-90 C90` | `-0.011354` | `+0.496312` | `+0.810062` | `0.950082` |
| `B+90 C180` | `-0.177021` | `-0.222083` | `+0.058604` | `0.289986` |
| `B-90 C180` | `-0.057875` | `+0.183750` | `+0.630896` | `0.659654` |
| `B+90 C270` | `-0.221946` | `+0.474761` | `+0.244541` | `0.578325` |
| `B-90 C270` | `-0.161601` | `-0.178643` | `+0.550479` | `0.600879` |

Linear-axis command locations at the high-B accepted pass-2 log points:

| Pose | X motor | Y motor | Z motor |
| --- | ---: | ---: | ---: |
| `B+90 C0` | `776.948` | `368.015` | `-589.568` |
| `B-90 C0` | `160.502` | `368.366` | `-587.685` |
| `B+90 C90` | `424.192` | `631.621` | `-589.627` |
| `B-90 C90` | `424.024` | `15.963` | `-587.473` |
| `B+90 C180` | `160.555` | `278.914` | `-589.545` |
| `B-90 C180` | `777.003` | `279.041` | `-587.636` |
| `B+90 C270` | `513.164` | `16.010` | `-589.366` |
| `B-90 C270` | `513.496` | `631.689` | `-587.726` |

Interpretation:

- B0 closures are stable enough that the quadrant run is valid for analytics.
- The C-only B0 orbit is cleaner than the tilted-B residuals and should be fit
  first as a C-center/alignment term.
- B-90 carries a repeatable large positive Z component. This may include B
  zero, B-axis vector error, tool/probe vector angular error, or load/geometry
  effects. Treat B zero as a fit variable now, even though SSI differential
  angles remain trusted.
- The side-quadrant high-B residuals are too large and too asymmetric for the
  existing translation-only `headheadkins` model. Fitting current B-to-tool and
  zero-offset variables to the local B90 deltas still leaves about
  `0.49-0.61 mm` max residual.
- The `Y`-extreme poses, especially `B-90 C90` and `B+90 C270`, should be
  checked for machine-fixed linear-axis contribution after the rotary geometry
  terms are fit.

Next engineering scope:

1. Do not collect more probe data until an offline fit report has been made
   from this quadrant run.
2. Build an offline model that separates:
   - C center/orbit term from B0 C quadrants
   - B zero and B-axis direction/skew from B90 quadrant residuals
   - tool/probe vector angular error
   - optional machine-fixed linear affine terms against X/Y/Z motor positions
3. Expand `headheadkins` only after the fit shows bounded parameters with
   held-out residual improvement.
4. The likely kinematics expansion is small-angle axis-vector support:
   - C-axis tilt about machine X/Y
   - B-axis skew/tilt in the C frame
   - retained C/B pivot translation and B/C zero offsets
   - optional debug pins for effective axis vectors and modeled TCP offset

## First Expanded Offline Fit - 2026-05-04

Created reproducible analysis script:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc_expanded_geometry_fit.py`

Generated report:

- `configs/5th_axis_xyzbc_ssi_probe_basic/TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md`

Fit setup:

- training set: `20` valid pass-2 rows from the B90 C-quadrant diagnostic
- holdout set: `10` valid pass-2 rows from the clean B90 C0/C180 rerun,
  results CSV lines `18-37`
- bad accepted false-top row remains excluded by the `29.9 mm` diameter floor
- model equation treats each run as having its own unknown sphere location and
  minimizes corrected center scatter within each run

Cleanest identified parameter:

- fitting only B0 C-quadrant rows gives:
  - `dcx = +0.100886006 mm`
  - `dcy = -0.004473694 mm`
  - equivalent test-only `cal-c-to-b.x = +0.035886006`
  - equivalent test-only `cal-c-to-b.y = +0.009526306`
  - B0 C-orbit RMS/max improves from `0.102863 / 0.118339 mm` to
    `0.019566 / 0.030016 mm`
- This is the strongest current evidence and should be verified in simulation
  as a C-center correction sign before any live test.

Model comparison from the report:

| Model | Train RMS | Train max | Holdout RMS | Holdout max |
| --- | ---: | ---: | ---: | ---: |
| current | `0.341093` | `0.760878` | `0.293278` | `0.554744` |
| C-center XY only | `0.325863` | `0.813475` | `0.276565` | `0.540773` |
| current pins only | `0.232722` | `0.503834` | `0.245820` | `0.490888` |
| C/B axis vectors | `0.224540` | `0.489239` | `0.238502` | `0.471294` |
| axis vectors plus linear diagonal | `0.164906` | `0.352968` | `0.149801` | `0.308334` |
| axis vectors plus full linear affine | `0.149291` | `0.303645` | `0.149598` | `0.267016` |

Interpretation:

- Existing `headheadkins` pins are rank-deficient on this data and should not
  be loaded as a new candidate.
- Axis-vector expansion alone gives only modest improvement over current pins.
  That means the high-B error is not only simple C/B skew.
- Adding machine-fixed linear-axis terms improves both training and holdout,
  but `lin_xx` hits the diagnostic bound and the Jacobian is ill-conditioned.
  Treat this as a strong reason to test linear-axis geometry, not as an axis
  compensation solution.
- The next code step should separate the clean C-center correction from the
  broader expanded model, then add simulation-only support for C/B axis-vector
  terms before live testing.

## Expanded Kinematics Scaffold Added - 2026-05-04

Added zero-default expanded-axis support to `src/emc/kinematics/headheadkins.c`
and rebuilt `rtlib/headheadkins.so`.

New HAL input pins:

```hal
headheadkins.c-axis-tilt.x
headheadkins.c-axis-tilt.y
headheadkins.b-axis-tilt.x
headheadkins.b-axis-tilt.z
```

New debug output pins:

```hal
headheadkins.c-axis-vector.x
headheadkins.c-axis-vector.y
headheadkins.c-axis-vector.z
headheadkins.b-axis-vector.x
headheadkins.b-axis-vector.y
headheadkins.b-axis-vector.z
```

Behavior:

- all new pins default to zero, so the current kinematics are unchanged until
  nonzero values are deliberately set after a restart
- `tool-offset.*`, `tool-vector.*`, and TWP plane axes now use the expanded
  model path
- the compiled module on disk is updated, but the currently running LinuxCNC
  instance will not see the new pins until the TCPC config is restarted

C-center sign check:

- fitted sign RMS/max: `0.019566 / 0.030016 mm`
- opposite sign RMS/max: `0.202916 / 0.219278 mm`
- this confirms the offline-fit sign convention for the current model
- the test-only C-center values remain:
  - `headheadkins.cal-c-to-b.x = +0.035886006`
  - `headheadkins.cal-c-to-b.y = +0.009526306`

This caution was superseded later on 2026-05-04 by the live C-center validation
below.

## Live C-Center Validation - 2026-05-04

The TCPC Probe Basic config was restarted and the expanded pins were confirmed
present. The new axis-vector pins remained zero. The C-center correction was
loaded live:

```hal
setp headheadkins.cal-c-to-b.x 0.035886006
setp headheadkins.cal-c-to-b.y 0.009526306
setp headheadtwp.cal_c_to_b_x 0.035886006
setp headheadtwp.cal_c_to_b_y 0.009526306
```

Validation run:

- temporary B0-only C sweep in `tcpc_b90_c_quadrant_diagnostic.ngc`
- latest result rows are CSV lines `44-53`
- run completed with no probe faults
- LinuxCNC ended idle with both probe gates false

Latest pass-2 centers:

| Pose | X | Y | Z |
| --- | ---: | ---: | ---: |
| `B0 C0` | `468.855999` | `323.679659` | `-858.974582` |
| `B0 C90` | `468.842667` | `323.659323` | `-858.959082` |
| `B0 C180` | `468.861739` | `323.678084` | `-858.944415` |
| `B0 C270` | `468.845904` | `323.677282` | `-858.953915` |
| `B0 C0 closure` | `468.851946` | `323.676657` | `-858.975082` |

Validation metrics:

- four-quadrant XYZ RMS/max: `0.015700 / 0.018205 mm`
- four-quadrant XY RMS/max: `0.011276 / 0.016818 mm`
- previous B0 closure orbit before correction: `0.114023 mm` RMS
- final C0 closure: `0.005068 mm` 3D, `0.005044 mm` XY
- pass-2 max residuals: `0.003750 mm` U and `0.002500 mm` V
- corrected diameter ranges: U `30.162167..30.207487`, V
  `30.163016..30.243000`

Interpretation:

- The C-center sign is confirmed on the machine.
- The C-center correction removes the dominant B0 C-axis orbit.
- The remaining C-dependent spread is mostly Z, around `0.030 mm` peak-to-peak,
  so the next fit should look at C-axis tilt, tool/probe vector angle, and
  machine-fixed effects rather than another XY C-center adjustment.

The diagnostic NGC has been restored to B90 defaults:

```ngc
#707 = 90.0
#708 = 1.0
#709 = 90.0
#710 = 0.0
```

Next live work:

1. Keep the validated live C-center correction active.
2. Rerun the restored B90 C-quadrant diagnostic from the above-sphere start.
3. Use the new high-B rows to fit B-axis vector/skew, B zero, tool/probe vector
   angle, and any machine-fixed linear-axis contribution after the large B0
   C-center orbit has been removed.

## Corrected B90 C-Quadrant Rerun - 2026-05-04

The restored B90 C-quadrant run completed with the validated C-center
correction still active. Result rows are lines `54-93` in
`tcpc-b90-c-quadrant-diagnostic-2pass-results.csv`.

Probe-quality caveat:

- The operator paused and reset/settled the wireless probe during the run
  because it was false-pulsing too often.
- All rows were still logged and pass-2 checks remained inside the programmed
  limits, but use this dataset with caution in fitting.

Data quality:

- pass-2 max residuals: U `0.061250 mm`, V `0.007500 mm`
- pass-2 corrected diameter ranges:
  - U `30.158000..30.205020`
  - V `30.160141..30.244667`
- X/Y/Z motor following errors in the accepted high-B rows were effectively
  zero.

High-B deltas versus adjacent B0 closures after the C-center correction:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.052875` | `-0.198228` | `+0.069230` | `0.216525` |
| `B-90 C0` | `-0.203375` | `-0.137813` | `+0.659229` | `0.703518` |
| `B+90 C90` | `-0.094271` | `-0.242146` | `-0.084833` | `0.273347` |
| `B-90 C90` | `-0.012100` | `+0.421370` | `+0.886208` | `0.981358` |
| `B+90 C180` | `-0.112354` | `-0.220592` | `-0.012021` | `0.247848` |
| `B-90 C180` | `+0.022229` | `+0.169999` | `+0.712771` | `0.733100` |
| `B+90 C270` | `-0.223969` | `+0.539925` | `+0.170062` | `0.608771` |
| `B-90 C270` | `-0.149642` | `-0.115378` | `+0.633603` | `0.661179` |

High-B delta RMS/max: `0.610965 / 0.981358 mm`.

Interpretation:

- The C-center correction remains validated, but high-B error remains large.
- B-90 positive Z error is still the dominant signature.
- Side-quadrant Y-extreme poses are still large, especially `B-90 C90` and
  `B+90 C270`.
- Do not spend more machine time on this same long run until the wireless probe
  is stable. Next step is offline fitting with this corrected dataset plus a
  probe-quality flag.

## Run-State-Aware Offline Fit - 2026-05-04

`tcpc_expanded_geometry_fit.py` now models the kinematic state active during
each run before applying any candidate correction. This matters because the
latest CSV contains both old-C-center rows and validated-C-center rows.

Active data boundaries:

- pre-correction B90 C-quadrant: CSV lines `2-43`, old C-center, bad line
  `13` excluded
- B0 C-center validation: CSV lines `44-53`, validated C-center
- corrected B90 C-quadrant: CSV lines `54-93`, validated C-center
- clean B90 C0/C180 holdout: B-axis diagnostic CSV lines `18-37`, old
  C-center

Generated report:

- `TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md`

Current decision:

- Keep `headheadkins.cal-c-to-b.x = +0.035886006`.
- Keep `headheadkins.cal-c-to-b.y = +0.009526306`.
- Do not load any high-B fit values.
- With C-center fixed, current pins reduce the corrected B90 RMS/max only to
  `0.2440 / 0.4898 mm`.
- Axis-vector terms improve only to `0.2384 / 0.4667 mm`.
- Axis-vector plus linear-diagonal terms improve to about
  `0.1825 / 0.3374 mm`, but the fit hits bounds, so it is diagnostic only.

Next math/code scope:

1. Add debug pins for the actual expanded U/V/W probe frame used by TCPC.
2. Add a simulation-only machine-linear affine family with identity defaults.
3. Keep the C-center fixed while fitting high-B terms.
4. Use the next B-angle scaling data to separate `sin(B)`, `1-cos(B)`, and
   machine-position effects before attempting another live correction.

Proposed `headheadkins` code order:

1. Debug-only frame pins, zero behavior risk:
   - add `headheadkins.tool-frame-u.x/y/z`
   - add `headheadkins.tool-frame-v.x/y/z`
   - add `headheadkins.tool-frame-w.x/y/z`
   - compute them from the same `rotary_vector_world()` path used by
     `tool-offset.*`, TWP plane axes, and current `tool-vector.*`
   - make `tool-frame-w.*` match the current stylus/tool vector direction
2. Simulation-only affine pins, disabled by default:
   - add an enable bit plus small delta pins for a 3x3 matrix
   - with enable false, forward/inverse kinematics remain byte-for-byte
     equivalent in behavior
   - with enable true in simulation:
     `reported_tcp = A * joint_xyz + rotary_offset`
   - inverse:
     `joint_xyz = A^-1 * (requested_tcp - rotary_offset)`
3. Do not load affine or axis-vector fit values on the real machine until the
   B-angle scaling data shows bounded terms and the B0 C-center validation
   remains good as a held-out check.

Next live data after wireless probe stabilization:

- C0 reduced sequence:
  `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`
- repeat at C180 only if C0 is clean
- keep the current C-center correction active
- avoid another long B90 C-quadrant rerun until probe behavior is stable
- Do not use `tcpc_b90_b_axis_diagnostic.ngc` as-is for this next run. Its
  B30/B60 blocks probe all C quadrants and the older B50 path; create a
  dedicated short B-angle scaling NGC first.
- Because the B0 closure rows are now repeatable, use opening and closing B0
  checks at each C angle rather than returning to B0 between every B sign. This
  still gives a drift/sphere-shift check while cutting probe time.

Prepared short run:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- default `#711 = 0.0`, so it runs C0 only
- C0 sequence:
  `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`
- set `#711 = 1.0` only after C0 is clean and LinuxCNC is idle if a C180
  repeat is wanted
- no LinuxCNC restart is required if the live C-center correction is still
  active
- The first interrupted attempt exposed a high-B transit problem: the inherited
  routine used a machine-Z-only lift before indexing B. The short program now
  first moves back along the current pose W vector to the last accepted
  top-clear point, then lifts Z, then indexes B/C. Reload the NGC before
  rerunning.
- To avoid rerunning the completed points, use
  `nc_files/calibration/tcpc_b_angle_scaling_resume_bminus90_c0.ngc` for this
  specific interruption. It appends to the same logs and only runs `B-90 C0`
  plus the closing `B0 C0`, seeded from the latest accepted B0 C0 center
  `X468.863916 Y323.669451 Z-858.972978`.

The resume tail completed. Use these final accepted pass-2 C0 scaling rows:

- CSV lines `9, 11, 13, 15, 17, 19, 22, 24`
- exclude earlier interrupted/restart rows before line `9`
- exclude abandoned `B-90 C0` pass-1 row at line `20`

Opening/closing B0 drift was `0.026145 mm` 3D, so the reduced-B0 approach is
acceptable for this run.

Key C0 deltas relative to average B0:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+30 C0` | `+0.011100` | `-0.071876` | `+0.035380` | `0.080877` |
| `B-30 C0` | `-0.027891` | `+0.017707` | `+0.045435` | `0.056176` |
| `B+60 C0` | `-0.008984` | `-0.170210` | `+0.060754` | `0.180950` |
| `B-60 C0` | `-0.072179` | `-0.045002` | `+0.259367` | `0.272958` |
| `B+90 C0` | `-0.047512` | `-0.203335` | `+0.056451` | `0.216307` |
| `B-90 C0` | `-0.172126` | `-0.115625` | `+0.640271` | `0.673010` |

Do not collect more probe data immediately. Fold this C0 scaling set into the
offline fitter first.

## C0 Scaling Folded Into Offline Fit - 2026-05-04

The C0 B-angle scaling set has been added to
`tcpc_expanded_geometry_fit.py` and the expanded report was regenerated:

- `configs/5th_axis_xyzbc_ssi_probe_basic/TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md`

Fit inputs now include:

- pre-correction B90 C-quadrant rows: `20`
- B0 C-center validation rows: `5`
- corrected B90 C-quadrant rows: `20`
- clean B90 C0/C180 holdout rows: `10`
- C0 B-angle scaling rows: `8`

Main results:

- C0 scaling only can be reduced from `0.2265 / 0.5219 mm` RMS/max to
  `0.0166 / 0.0277 mm` with bounded B-harmonic terms.
- The flexible linear-diagonal model can reduce the C0-only sequence, but it
  evaluates at about `4.46 mm` RMS on the corrected B90 quadrant data, so it is
  not a compensation candidate.
- Corrected B90 plus clean holdout plus C0 scaling with axis-vector plus
  linear-diagonal terms gives:
  - C0 scaling: `0.1092 / 0.1492 mm`
  - corrected B90: `0.1854 / 0.3527 mm`
  - clean B90 holdout: `0.1723 / 0.2816 mm`
- Corrected B90 plus clean holdout plus C0 scaling with a machine-fixed
  B-harmonic model gives:
  - C0 scaling: `0.0651 / 0.1221 mm`
  - corrected B90: `0.2058 / 0.5687 mm`
  - clean B90 holdout: `0.0917 / 0.1630 mm`
  - rank `9`, condition `2.52e+00`
- The C-frame B-harmonic model is slightly better on corrected B90
  (`0.1910 / 0.4678 mm`) but weaker on the clean holdout
  (`0.1332 / 0.3049 mm`).
- The combined machine/C-frame harmonic fit is too ill-conditioned to trust
  with the current data.
- All curated data plus C0 scaling gives a similar balanced result, but the
  fit remains bound-limited and ill-conditioned.

Decision:

- Keep the validated C-center correction active.
- Do not apply a high-B correction to the real machine yet.
- Current kinematics pins still cannot represent the missing high-B behavior
  cleanly.
- The machine-fixed B-harmonic model is now the strongest bounded non-affine
  diagnostic, but it must be implemented and verified in simulation before any
  live test.
- The next task is offline math/code, not probing:
  - add/debug the actual U/V/W tool-frame output in `headheadkins`
  - add simulation-only B-harmonic support with zero defaults
  - verify forward/inverse behavior before exposing live HAL pins
  - keep C-center fixed while fitting high-B terms
- Run a C180 B-angle scaling pass only if the next offline model cannot
  disambiguate rotary-frame and machine-fixed terms from the current data.

## Headheadkins Diagnostic Pin Update - 2026-05-04

`src/emc/kinematics/headheadkins.c` now includes the first offline code support
for the next diagnostic step.

Added debug outputs:

- `headheadkins.tool-frame-u.x/y/z`
- `headheadkins.tool-frame-v.x/y/z`
- `headheadkins.tool-frame-w.x/y/z`

These expose the same U/V/W convention used by the vector sphere probing
programs. At `B0 C0`, U is `+X`, V is `+Y`, and W is `-Z`.

Added simulation-gated B-harmonic pins:

- `headheadkins.sim-bharm-enable`
- `headheadkins.bharm-m.sin.x/y/z`
- `headheadkins.bharm-m.omc.x/y/z`
- `headheadkins.bharm-m.sin2.x/y/z`
- `headheadkins.bharm-c.sin.x/y/z`
- `headheadkins.bharm-c.omc.x/y/z`
- `headheadkins.bharm-c.sin2.x/y/z`

Defaults:

- enable pin is `FALSE`
- all coefficients are zero
- no live behavior changes unless the enable pin is deliberately set true

Runtime check:

- rebuilt `headheadkins.so`
- ran `sudo make setuid`
- loaded `headheadkins coordinates=XYZBC` in `halrun`
- confirmed tool-frame pins and representative B-harmonic pins exist
- unloaded the `halrun` realtime session after the check

Next offline task:

- run the head-head sim with `sim-bharm-enable = 0` and confirm old TCPC/TWP
  behavior is unchanged
- then enable the machine-fixed B-harmonic candidate from
  `TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` in simulation only
- verify forward/inverse consistency and fixed-tip behavior before considering
  any live-machine test

## Offline B-Harmonic Verification Script - 2026-05-04

Added non-GUI offline verification:

- `configs/sim/head_head_5axis/headhead_bharmonic_verify.py`
- `configs/sim/head_head_5axis/head_head_bharmonic_candidate.hal`
- `configs/sim/head_head_5axis/tcp_bharmonic_candidate_sequence.ngc`

Script result:

- zero/default max offset delta: `0 mm`
- tool-frame formula max delta: `0`
- active tool-frame orthogonality max error: `5.55e-17`
- candidate forward/inverse round-trip max error: `8.04e-14 mm`

Candidate HAL file behavior:

- loads the current machine-fixed candidate coefficients
- leaves `headheadkins.sim-bharm-enable` false
- was sourced successfully in `halrun` after loading `headheadkins`

Next offline task:

- launch the head-head sim only, not the real machine config
- source or include `head_head_bharmonic_candidate.hal`
- first verify behavior with `sim-bharm-enable = 0`
- then set `sim-bharm-enable = 1` in sim and run
  `tcp_bharmonic_candidate_sequence.ngc`
- do not apply the candidate to the real machine until the sim checks are
  complete and reviewed

## Full LinuxCNC B-Harmonic Sim Smoke - 2026-05-04

Added:

- `configs/sim/head_head_5axis/head_head_bharmonic_sim.ini`
- `configs/sim/head_head_5axis/headhead_bharmonic_linuxcnc_smoke.py`

The sim INI loads the B-harmonic candidate HAL file but leaves
`headheadkins.sim-bharm-enable` false by default.

Smoke result:

- disabled max fixed-tip TCP error: `0.000000000 mm`
- enabled max fixed-tip TCP error: `0.000000000 mm`

Notes:

- sequential homing was not reliable for this sim because Z remained in
  homing state; the smoke script now uses home-all
- Z has a home motor offset in this sim, so fixed-tip verification uses
  `joint.N.pos-fb + headheadkins.tool-offset.*`
- after the smoke run, the temporary sim realtime session was unloaded with
  `halrun -U`

Next offline task:

- perform a visual sim inspection with
  `configs/sim/head_head_5axis/head_head_bharmonic_sim.ini`
- run `tcp_bharmonic_candidate_sequence.ngc` with `sim-bharm-enable = FALSE`
  and then `TRUE`
- compare observed tool-tip behavior and joint travel before any live-machine
  decision

## Ready for Limited Machine Probe Validation - 2026-05-04

The dedicated sim smoke was rerun after the B-harmonic support and candidate
HAL were in place:

- disabled max fixed-tip TCP error: `0.000000000 mm`
- enabled max fixed-tip TCP error: `0.000000000 mm`
- the temporary sim realtime session was unloaded afterward
- a follow-up `halcmd getp headheadkins.sim-bharm-enable` returned pin not
  found, confirming no sim realtime session was left running

The TCPC Probe Basic test config startup HAL now persists the validated
C-center correction in both the kinematics and TWP state component:

```hal
setp headheadkins.cal-c-to-b.x 0.035886006
setp headheadkins.cal-c-to-b.y 0.009526306
setp headheadtwp.cal_c_to_b_x 0.035886006
setp headheadtwp.cal_c_to_b_y 0.009526306
```

The next live run is ready as a limited diagnostic only. It is not a production
TCPC correction and it should not be made persistent.

Recommended next machine run:

1. Restart `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic`.
2. Home and position the probe above the sphere at `B0 C0`.
3. Confirm the validated C-center pins above loaded correctly.
4. Confirm `headheadkins.sim-bharm-enable = FALSE`.
5. Load the B-harmonic candidate pins manually while idle.
6. Set `headheadkins.sim-bharm-enable = TRUE` only for the validation run.
7. Run `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` with the
   default `#711 = 0.0` C0-only setting.
8. After the run, set `headheadkins.sim-bharm-enable = FALSE` before doing
   anything else.

Manual candidate pin block for the live diagnostic session:

```hal
setp headheadkins.sim-bharm-enable 0
setp headheadkins.bharm-m.sin.x 0.003457595
setp headheadkins.bharm-m.sin.y 0.071987315
setp headheadkins.bharm-m.sin.z 0.318267363
setp headheadkins.bharm-m.omc.x 0.108123741
setp headheadkins.bharm-m.omc.y 0.034446993
setp headheadkins.bharm-m.omc.z -0.364472105
setp headheadkins.bharm-m.sin2.x -0.032225192
setp headheadkins.bharm-m.sin2.y 0.005230194
setp headheadkins.bharm-m.sin2.z -0.190772593
setp headheadkins.bharm-c.sin.x 0.000000000
setp headheadkins.bharm-c.sin.y 0.000000000
setp headheadkins.bharm-c.sin.z 0.000000000
setp headheadkins.bharm-c.omc.x 0.000000000
setp headheadkins.bharm-c.omc.y 0.000000000
setp headheadkins.bharm-c.omc.z 0.000000000
setp headheadkins.bharm-c.sin2.x 0.000000000
setp headheadkins.bharm-c.sin2.y 0.000000000
setp headheadkins.bharm-c.sin2.z 0.000000000
```

Acceptance guidance for this one run:

- B0 open/close should remain in the established good range, roughly
  `0.03 mm` 3D or better.
- Probe diameters should stay in the normal wireless-probe window, roughly
  U/V `30.15..30.25 mm` for this setup.
- The C0 high-B error should improve materially, especially the prior
  `B-90` positive-Z signature. If it does not, disable the candidate and
  inspect the data before any C180 or C-quadrant probing.

## Candidate-On C0 Result - 2026-05-04

The first candidate-on run attempt was aborted for probe behavior and should be
ignored for validation:

- `tcpc-b-angle-scaling-diagnostic-2pass-results.csv` lines `25-27`
- line `27` is `B+30 C0` pass 1 only

The second run completed cleanly with the B-harmonic candidate enabled. Use
accepted pass-2 lines:

- `29, 31, 33, 35, 37, 39, 41, 43`

Quality:

- B0 open/close drift: `0.018351 mm` 3D
- pass-2 max residuals: U `0.006865 mm`, V `0.008333 mm`
- pass-2 corrected diameters:
  - U `30.142549..30.219870 mm`
  - V `30.216333..30.229667 mm`

C0 improvement:

| State | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| candidate off, prior clean C0 | `0.320592 mm` | `0.673010 mm` |
| candidate on, clean C0 | `0.108201 mm` | `0.189342 mm` |

Candidate-on C0 deltas versus B0 average:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+30 C0` | `-0.009897` | `-0.040287` | `-0.025141` | `0.048508` |
| `B-30 C0` | `+0.004306` | `-0.019662` | `+0.005996` | `0.021003` |
| `B+60 C0` | `+0.010792` | `-0.083620` | `-0.012162` | `0.085187` |
| `B-60 C0` | `+0.008176` | `-0.094871` | `-0.028618` | `0.099430` |
| `B+90 C0` | `+0.063705` | `-0.101798` | `+0.006001` | `0.120238` |
| `B-90 C0` | `-0.068462` | `-0.169714` | `-0.048583` | `0.189342` |

Decision:

- The candidate is effective at C0 and brings this sequence inside the current
  practical `0.2 mm` target.
- The old `B-90` positive-Z error is mostly removed.
- Remaining C0 error is mostly machine-Y at high B.
- This is not yet a general TCPC correction because it has not been validated
  at C180 or side C quadrants.

Program change:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` now supports
  `#711 = 2.0` for a C180-only pass.
- Use C180-only next if continuing live validation; do not rerun C0 unless
  probe repeatability becomes suspect.
- The current file has been set to `#711 = 2.0`; reload it in Probe Basic
  before running the next pass.

## Candidate-On C180 Result - 2026-05-04

The C180-only pass completed cleanly with the B-harmonic candidate enabled.
The candidate was disabled immediately after the run.

Use accepted pass-2 lines:

- `45, 47, 49, 51, 53, 55, 57, 59`

Quality:

- B0 open/close drift: `0.012149 mm` 3D
- pass-2 max residuals: U `0.007699 mm`, V `0.003335 mm`
- pass-2 corrected diameters:
  - U `30.148024..30.250744 mm`
  - V `30.210500..30.217996 mm`

Candidate-on C180 deltas versus B0 average:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+30 C180` | `-0.112635` | `-0.047842` | `-0.048767` | `0.131733` |
| `B-30 C180` | `-0.018993` | `+0.031533` | `+0.027880` | `0.046178` |
| `B+60 C180` | `-0.193129` | `-0.103929` | `-0.065487` | `0.228885` |
| `B-60 C180` | `-0.095269` | `+0.063543` | `+0.020045` | `0.116257` |
| `B+90 C180` | `-0.065450` | `-0.119525` | `-0.014121` | `0.137001` |
| `B-90 C180` | `+0.059216` | `+0.134433` | `-0.030788` | `0.150089` |

Candidate-on summary:

| Set | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| C0 | `0.108201 mm` | `0.189342 mm` |
| C180 | `0.145308 mm` | `0.228885 mm` |
| C0 + C180 combined | `0.128105 mm` | `0.228885 mm` |

Decision:

- The B-harmonic candidate is effective at C0 and C180.
- It should still remain diagnostic-only because C180 has a `0.228885 mm`
  maximum at `B+60 C180`, and C90/C270 are unvalidated.
- Stop live probing for offline fitting unless the operator specifically wants
  one more limited side-quadrant check.
- If continuing live, make the next pass short: `C90/C270` with `B0`,
  `B+90`, `B-90`, `B0` only. Do not run the full long quadrant program yet.

## Offline Fold-In And Next Short Test - 2026-05-04

`tcpc_expanded_geometry_fit.py` now includes the candidate-on C0 and C180 rows
as active-candidate validation data, and
`TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` has been regenerated.

The report confirms:

- candidate-on C0 non-B0 RMS/max: `0.108201 / 0.189342 mm`
- candidate-on C180 non-B0 RMS/max: `0.145308 / 0.228885 mm`
- candidate-on combined C0+C180 non-B0 RMS/max:
  `0.128105 / 0.228885 mm`
- existing side-quadrant data predicts the highest remaining risk at C90/C270
  high-B poses:
  - predicted side-quadrant high-B RMS/max: `0.3782 / 0.4238 mm`

Next prepared live test:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- current mode is `#711 = 3.0`
- sequence:
  - `C90`: `B0`, `B+90`, `B-90`, `B0`
  - `C270`: `B0`, `B+90`, `B-90`, `B0`
- this skips C0/C180 and avoids the full long quadrant program

Do not enable the B-harmonic candidate until immediately before this run, after
idle/gate/probe/B/C checks.

## Candidate-On Side-Quadrant Result - 2026-05-04

The prepared `#711 = 3.0` side-quadrant run completed. Use accepted pass-2
rows in `tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

- `61, 63, 65, 67, 69, 71, 73, 75`

The machine-fixed B-harmonic candidate is not viable as a general live
correction by itself:

| Set | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| C0 | `0.108201 mm` | `0.189342 mm` |
| C180 | `0.145308 mm` | `0.228885 mm` |
| C90/C270 side | `0.408282 mm` | `0.615783 mm` |
| all candidate-on validation | `0.232339 mm` | `0.615783 mm` |

Side-quadrant refit results:

- incremental C-frame terms on top of the live candidate reduce all direct
  RMS/max to `0.202139 / 0.494928 mm`, but C0/C180 regress and side error is
  still too large
- replacement machine plus C-frame terms reduce all direct RMS/max to
  `0.197311 / 0.434945 mm`, but the fit condition is about `1.21e17`
- C-axis-tilted replacement machine plus C-frame terms reduce all direct
  RMS/max to `0.185867 / 0.408958 mm`, but the model is still too flexible and
  leaves too much side error
- axis-vector plus linear-diagonal terms are also ill-conditioned and are not
  a live correction candidate

Next scope:

- the next live probing candidate is now the B/C cross-harmonic candidate, but
  only after the TCPC config is restarted so the new pins exist
- keep the validated C-center correction
- keep all B-harmonic / expanded-variable results diagnostic-only
- load the candidate manually from
  `configs/sim/head_head_5axis/head_head_bharmonic_candidate.hal`
- verify any candidate in simulation or non-GUI math before enabling it on the
  machine

## B/C Cross-Harmonic Candidate - 2026-05-04

The next candidate is an incremental layer on top of the previous
machine-fixed B-harmonic terms. It adds machine-world B/C cross terms:

- `sin(B) * sin(C)`
- `(1-cos(B)) * sin(C)`
- `(1-cos(B)) * sin(C)^2`
- `sin(B) * cos(C)`
- `(1-cos(B)) * cos(C)`

Predicted direct validation:

| Set | RMS | Max |
| --- | ---: | ---: |
| C0 | `0.078760 mm` | `0.116901 mm` |
| C180 | `0.111771 mm` | `0.166446 mm` |
| C90/C270 side | `0.085480 mm` | `0.085480 mm` |
| all validation | `0.094009 mm` | `0.166446 mm` |

Prepared validation program:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- current mode: `#711 = 4.0`
- runs C0, C180, then C90/C270 side high-B check

Before running:

- close and restart the TCPC Probe Basic config to load the rebuilt
  `headheadkins`
- confirm `headheadkins.bcross.sinb-sinc.y` exists after restart
- confirm `headheadkins.sim-bharm-enable = FALSE`
- load the candidate HAL while idle
- enable only immediately before cycle start
- disable `headheadkins.sim-bharm-enable` immediately after completion

## B/C Cross-Harmonic Candidate Live Result - 2026-05-04

The `#711 = 4.0` C0 + C180 + C90/C270 validation run has completed. The
operator paused once to let/reset the wireless probe; accepted pass-2 rows
looked clean and no pass-2 rows were rejected.

Use these accepted pass-2 rows from
`tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

- C0: `77,79,81,83,85,87,89,91`
- C180: `93,95,97,99,101,103,105,107`
- C90/C270 side: `109,111,113,115,117,119,121,123`

Measured direct validation:

| Set | RMS | Max |
| --- | ---: | ---: |
| C0 | `0.083627 mm` | `0.127554 mm` |
| C180 | `0.116273 mm` | `0.176626 mm` |
| C90/C270 side | `0.079909 mm` | `0.105982 mm` |
| all validation | `0.096378 mm` | `0.176626 mm` |

The result is close to the offline prediction of `0.094009 / 0.166446 mm`.
The large side-quadrant failure from the B-harmonic-only candidate is removed.
The worst remaining point is `B+60 C180` at `0.176626 mm`.

Current scope:

- keep `headheadkins.sim-bharm-enable = FALSE`
- keep the B/C cross candidate non-persistent
- fold the new active-candidate rows into the offline fitter before any
  additional live probing
- do not rerun the same long validation immediately unless repeatability of
  the candidate itself becomes the next question

## Refined B/C Cross Candidate Ready For Next Test - 2026-05-04

The live B/C-cross-active rows have now been folded into the run-state-aware
offline fitter. The best constrained next diagnostic is a replacement fit of
the existing machine-fixed B-harmonic plus B/C cross correction families. It
does not add another kinematics family.

Direct validation metrics:

| Model | Combined live rows | Corrected B90 holdout | Clean B-axis holdout | Original C0 scaling |
| --- | ---: | ---: | ---: | ---: |
| current B/C cross | `0.095201 / 0.176626 mm` | `0.103511 / 0.148967 mm` | `0.095375 / 0.132854 mm` | `0.073636 / 0.115399 mm` |
| refined B/C cross | `0.072421 / 0.133632 mm` | `0.098309 / 0.150983 mm` | `0.080505 / 0.100168 mm` | `0.042392 / 0.076438 mm` |

Prepared next-candidate HAL:

- `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`

Verification passed:

- non-GUI B-harmonic math verification
- LinuxCNC sim fixed-tip smoke test:
  - disabled max TCP error: `0.000000000 mm`
  - enabled max TCP error: `0.000000000 mm`
- sim HAL unloaded after the test

Next live run:

- launch the TCPC Probe Basic config fresh
- confirm `headheadkins.sim-bharm-enable = FALSE`
- source or include `head_head_bharmonic_refined_candidate.hal`
- verify refined coefficients before enabling:
  - `headheadkins.bharm-m.sin.z = 0.312123080`
  - `headheadkins.bharm-m.omc.y = 0.111703959`
  - `headheadkins.bcross.sinb-sinc.y = 0.325723886`
  - `headheadkins.bcross.omcb-sin2c.y = -0.255875638`
- run `tcpc_b_angle_scaling_diagnostic.ngc` with `#711 = 4.0`
- disable `headheadkins.sim-bharm-enable` immediately after completion or any
  stop/error

## Refined B/C Cross Candidate Live Result - 2026-05-05

The refined `#711 = 4.0` validation run completed. The refined candidate was
loaded from:

- `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`

It was disabled immediately after completion and verified safe:

- `headheadkins.sim-bharm-enable = FALSE`
- `halui.program.is-idle = TRUE`
- `motion.probe-input = FALSE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`

Use accepted pass-2 rows:

- C0: `125,127,129,131,133,135,137,139`
- C180: `141,143,145,147,149,151,153,155`
- C90/C270 side: `157,159,161,163,165,167,169,171`

Measured direct validation:

| Set | non-B0 RMS/max |
| --- | ---: |
| refined C0 | `0.044921 / 0.094234 mm` |
| refined C180 | `0.098680 / 0.125893 mm` |
| refined C90/C270 side | `0.077269 / 0.097132 mm` |
| refined all validation | `0.076818 / 0.125893 mm` |

Compared with earlier live candidates:

| Candidate | all-validation RMS/max |
| --- | ---: |
| machine B-harmonic only | `0.232339 / 0.615783 mm` |
| B/C cross | `0.096378 / 0.176626 mm` |
| refined B/C cross | `0.076818 / 0.125893 mm` |

Current decision:

- The refined B/C cross candidate is the best validated live candidate so far.
- Keep all B-harmonic and B/C cross terms simulation-gated and non-persistent.
- A post-refined all-live refit slightly improves combined RMS
  (`0.073209 mm` versus `0.073916 mm`) but worsens maximum error
  (`0.136366 mm` versus `0.133632 mm`), so the live-tested refined candidate
  remains the current candidate.
- Offline persistence review is recorded in
  `TCPC_REFINED_PERSISTENCE_REVIEW.md`.
- The review did not justify another coefficient retune or an added correction
  family. Keep the refined candidate unchanged.

Next live data, if requested:

- two `#711 = 5.0` targeted repeats have now completed
- both repeats were probe-clean but showed a shifted B0 reference state versus
  the earlier refined validation
- repeat 1 non-B0 RMS/max: `0.129502 / 0.153150 mm`
- repeat 2 non-B0 RMS/max: `0.149119 / 0.191962 mm`
- repeat 2 B0 mean stayed within `0.026908 mm` at C180 and `0.021019 mm` at
  C270 of repeat 1, but both were about `0.09-0.12 mm` from the prior refined
  validation
- do not run more live probing immediately
- do not retune from the targeted repeats alone
- next work is offline investigation of the session/reference movement before
  changing or persisting coefficients

## Reference Movement And Tool-Length Gate - 2026-05-05

The shifted targeted-repeat B0 reference is a real gating issue for persistence.
It may be room-temperature/machine-frame movement, a bumped or relaxed
sphere/stand, or another setup-state change. The current data cannot separate
those causes by itself.

Machine envelope:

- the machine currently has no pitch error compensation
- the machine currently has no thermal compensation
- both are future projects, not active corrections in this TCPC work
- because this is a large steel machine, thermal drift is expected and may be
  comparable to the remaining `0.1-0.2 mm` TCPC residuals
- do not bury pitch error or thermal growth inside the head-head TCPC
  correction unless it is deliberately documented as an operating-state
  workaround

Observed pattern:

- targeted repeat 1 moved about `0.092-0.106 mm` from the earlier refined
  validation B0 reference
- targeted repeat 2 moved about `0.112-0.115 mm` from the earlier refined
  validation B0 reference
- targeted repeat 2 stayed much closer to targeted repeat 1:
  `0.026908 mm` at C180 and `0.021019 mm` at C270
- probe residuals were clean, so do not classify this first as probe noise

Next correction decision:

- keep the refined candidate unchanged and non-persistent
- do not run a broad live validation grid next
- inspect the sphere/stand and let the machine reach a stable thermal state
- then run a short B0-only reference check with the candidate disabled, for
  example `B0 C0/C90/C180/C270/C0`
- if the B0 reference returns to the earlier refined state, treat the targeted
  repeats as a disturbed setup state
- if the shifted B0 reference remains stable, split the datasets by session
  state before fitting

Tool-length limitation:

- all current TCPC probing used one physical wireless probe stickout
- `motion.tooloffset.z` is still not wired into `headheadkins`
- the refined candidate is therefore provisional until a short-probe and
  long-probe back-to-back validation passes
- when the longer probes arrive, run the same candidate with the short and long
  probes without moving the sphere or retuning between runs
- if residuals scale with added probe length, prioritize tool-vector, spindle
  alignment, and rotary-axis angular model corrections
- if residuals stay about the same, prioritize pivot/frame/reference movement
  rather than probe-length math

## Offline Acceptance Review - 2026-05-05

Use two acceptance bands from here:

- `0.2 mm`: current production/core-task requirement
- `0.1 mm`: secondary refinement target

The regenerated persistence review now counts accepted non-B0 rows against
both bands:

| Evaluation | <=0.2 mm | <=0.1 mm | Max |
| --- | ---: | ---: | ---: |
| current refined candidate on live validation rows | `48/48` | `41/48` | `0.133632 mm` |
| current refined candidate on targeted repeats | `10/10` | `2/10` | `0.191962 mm` |
| current refined candidate on live plus targeted rows | `58/58` | `43/58` | `0.191962 mm` |
| all-live-plus-targeted retune on live plus targeted rows | `58/58` | `44/58` | `0.151695 mm` |

Interpretation:

- the current refined candidate is good enough for the core task if the B0
  reference and tool-length caveats are accepted
- it is not a hard `0.1 mm` candidate yet
- the post-targeted retune does not justify replacing the live-tested refined
  candidate, because it still misses the hard `0.1 mm` target and may be
  absorbing thermal/setup movement
- no further offline correction family is justified before checking the
  reference state
- primary TCPC error metrics should stay session-local: each run/C group uses
  its own opening and closing B0 average as the reference for non-B0 poses
- absolute B0 movement between runs is a separate machine/setup-state
  diagnostic, not the main TCPC error baseline

Prepared next machine check:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- default `#711 = 6.0`
- sequence: `B0 C0`, `B0 C90`, `B0 C180`, `B0 C270`, `B0 C0`
- purpose: determine whether the shifted B0 state remains after thermal soak
  and sphere/stand inspection
- run with `headheadkins.sim-bharm-enable = FALSE`
- this is a reference check only, not a high-B TCPC validation

## B0 Reference Check Result - 2026-05-05

The `#711 = 6.0` B0-only reference check completed with accepted pass-2 rows
`209,211,213,215,217`.

Result:

- C0 opening/closing closure: `0.007718 mm`
- session-local C90/C180/C270 deltas from the C0 opening/closing average:
  - C90 `0.165419 mm`
  - C180 `0.226414 mm`
  - C270 `0.170183 mm`
- C180 and C270 now match targeted repeat 2 closely:
  - C180 within `0.016633 mm`
  - C270 within `0.014588 mm`
- the run did not return to the earlier refined validation reference state
- CSV rows logged `probe_tool_number=0`; confirm tool/probe parameter state
  before using this as a final retune input

Offline fit clue:

- the current validated C-center gives B0 sweep residual RMS/max
  `0.1105 / 0.1300 mm`
- fitting C-center X/Y from this sweep alone gives residual
  `0.0169 / 0.0196 mm`
- fitted `cal-c-to-b.x/y`: `-0.075529283`, `0.010558248`

Next decision:

- do not run high-B validation next
- do not apply the new C-center from one run
- do not blame the B90/B-90 harmonic/cross fit for the B0 orbit directly; the
  fitted high-B terms evaluate to zero at B0 and were disabled for this check
- focus the next offline/live step on C-center/reference/tool state before any
  more B90/B-90 fitting
- first confirm Probe Basic/tool state so the probe tool logs as expected
- then either repeat the same B0-only reference check, or deliberately test a
  C-center-only candidate based on the fitted values

## Detailed C Sweep Prepared - 2026-05-05

The next data collection program is now the detailed low-B C sweep:

- file: `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- default mode: `#711 = 7.0`
- B groups: `B0`, `B+10`, `B-10`, `B+30`, `B-30`
- C sequence in each B group:
  `C0/C45/C90/C135/C180/C225/C270/C315/C0`
- probe tool fallback now records Tool 3 if mirrored tool state and
  `#5400` are both zero/invalid
- keep the refined B-harmonic/B-cross candidate disabled for this run
- C45/C225 are stand-clearance watch points

Purpose:

- build a session-local C sweep at B0 and low B angles
- separate C-center/reference motion from B-dependent TCPC error
- avoid another B90/B-90 fit until the C-only B0 orbit is understood

## Detailed C Sweep Interrupted - 2026-05-05

The first `#711 = 7.0` detailed C sweep attempt was aborted because the probe
errored while the workshop was active. Treat the partial rows as disturbed.

Partial log state:

- accepted pass-2 rows began at `219`
- B0 C sweep reached closing C0 at `235`
- B+10 sweep reached C270 at `249`
- B+10 C315 line `250` was pass 1 only and bad/disturbed

Do not fit from this interrupted attempt. Rerun the same program during a quiet
period with the refined candidate disabled.

### Selected B0 C-Sweep Review

The completed B0 portion of the interrupted detailed sweep can be used for a
C-axis/C-center check. Use only accepted pass-2 rows
`219,221,223,225,227,229,231,233,235`.

Quality:

- Tool 3 logged correctly
- C0 opening/closing closure was `0.007299 mm`
- pass-2 U/V residuals were only a few microns
- corrected diameters stayed in the normal window

Main C-axis result:

- raw session-local C orbit reaches `0.220980 mm` at C180 and `0.225719 mm`
  at C225 from the C0 opening/closing average
- raw XY circle radius is `0.110996 mm`, with radial RMS/max
  `0.011939 / 0.018794 mm`
- this is a coherent C-center/reference orbit, not a high-B fit side effect

C-center fit from this B0 sweep:

- current validated C-center residual RMS/max: `0.1111 / 0.1341 mm`
- fitted C-center residual RMS/max: `0.0192 / 0.0287 mm`
- fitted `cal-c-to-b.x/y`: `-0.074115329`, `0.014377936`
- earlier quadrant-only B0 fit gave `-0.075529283`, `0.010558248`, so the
  required X correction is repeatable

Next:

- prepare/test a C-center-only candidate before any more high-B fitting
- continue excluding the interrupted B+10 and later rows from TCPC fits

### Short-Probe Tool-Length Baseline

The long probe is not available yet. Prepare the next live data as a
short-probe baseline only, with the same core to be repeated later when the
long probe is available.

Prepared in `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`:

- default mode `#711 = 8.0`
- C45 is clear and remains enabled
- C135 and C315 are skipped for all nonzero B groups
- C225 is clear and remains enabled
- B0 C reference:
  `B0 C0/C45/C90/C135/C180/C225/C270/C315/C0`
- B-grouped C sweeps for faster machine motion:
  `B+30/B+60/B+90 C0/C45/C180/C0`,
  `B-90/B-60/B-30 C0/C45/C180/C225/C0`
- final B0 closure: `B0 C0/C45/C135/C180/C225/C315/C0`
- C returns to C0 before each B change, avoiding combined B/C diagonal
  transitions between measured groups
- new tool-state log:
  `tcpc-b-angle-scaling-diagnostic-tool-state.csv`

The tool-state log records the program-selected probe tool, current tool,
tool-offset parameters `#5401/#5402/#5403`, `#5410`, the probe calibration
offset, and live `motion.tooloffset.x/y/z`.

Run with:

- short Tool 3 probe loaded
- `headheadkins.sim-bharm-enable = FALSE`
- start at/near `B0 C0`, `3-8 mm` above the sphere

Parser checks:

- `rs274 -g` passed
- `rs274 -T -g` reached the expected simulated probe abort

Live update:

- B0 reference passed, then the machine stopped at `B+30 C135`; that pose
  touched the sphere stand
- operator confirmed `C45` is clear; `C135` and `C315` are the collision C
  angles for tilted B groups
- operator confirmed `C225` is clear
- full baseline `#711 = 8.0` now skips `C135` and `C315` for all nonzero B
  groups, while retaining `C45` and `C225`
- current file default is `#711 = 9.0`, a resume mode that first probes fresh
  `B0 C0` to establish the current sphere center
- for the immediate resume, start at `B0 C0`, `3-8 mm` above the sphere; the
  program will probe `B0 C0`, then run the non-B0 B-grouped sweeps and final
  B0 closure

## Persistent Refined Candidate Decision - 2026-05-07

Operator decision: the TCPC Probe Basic work config will not be used for
production until the remaining commissioning tasks are complete, so the best
validated refined fit should be persistent for all further TCPC/TWP testing.

Applied to `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`:

- copied the refined B-harmonic/B-cross coefficients from
  `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`
- set `headheadkins.sim-bharm-enable = 1` at startup
- kept the base fixed-tip correction active:
  - `cal-c-to-b.x = 0.035886006`
  - `cal-c-to-b.y = 0.009526306`
  - `cal-b-to-tool.z = 0.815000`
  - `c-zero-offset = -0.024500`
- added `headheadtwp.use_external_tool_offset = 1` and netted
  `headheadkins.tool-offset.*` into `headheadtwp.external_tool_offset_*`, so
  TCPC/TWP state calculations use the same fitted tool offset as kinematics

Important caveat:

- the HAL pin still has the historical `sim-bharm-enable` name, but in this
  TCPC work config it is now the persistent refined-candidate enable
- this changes the commissioning baseline: future probe data should be treated
  as refined-candidate-on data unless the pin is deliberately set false and
  logged
