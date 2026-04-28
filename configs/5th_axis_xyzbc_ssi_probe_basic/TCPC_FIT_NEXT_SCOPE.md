# TCPC Fit Next Scope

Status: TCPC direction checks and repeat small-pose fixed-tip validation have
passed on the real machine. The latest automated small-pose run completed on
2026-04-28 with worst accepted 3D drift about `0.111 mm` and closing `B0 C0`
repeat drift about `0.002 mm`. Current practical acceptance target is
`0.2 mm`; refine toward `0.1 mm` only after mechanical backlash/alignment work
is better characterized.

Earlier on 2026-04-27 staff started epoxy preparation on a mold on the machine,
and the start was bumped near the end of the B-axis session. TCPC work was
paused at `10:50 +07` for 3-axis work, then resumed in the dedicated TCPC test
config after the machine was stable again.

`G55` is reserved for staff 3-axis setup work from this point. Do not select,
probe, overwrite, or use `G55` for TCPC calibration/validation until the
operator explicitly releases it.

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
- Live `G43.4/G49.1` switching produced a large kinematics discontinuity when
  enabling TCPC from identity mode. The TCPC test config now starts with TCPC
  enabled, accepts `G43.4` only as an already-on confirmation, and blocks
  `G49.1` until a safe transition strategy is implemented.
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
  feed is `400 mm/min`; use lower feeds again if clearance or setup confidence
  changes
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

Recommended next TCPC check:

- keep the mold/table clearance constraint and stay within `B +/-50 deg`
- run a slightly wider automated validation set before changing geometry, for
  example `B+5/B-5` at `C0`, then `B+5` at `C+20/C-20`, closing `B0 C0`
- if worst drift remains below `0.2 mm`, expand gradually; if a directional
  pattern grows, use that pattern to decide whether to adjust the B/tool vector
  or investigate axis/alignment error first
