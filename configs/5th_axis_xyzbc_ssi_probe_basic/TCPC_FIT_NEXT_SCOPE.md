# TCPC Fit Next Scope

Status: TCPC direction and first small-pose fixed-tip validation completed on
2026-04-27. Earlier in the day staff started epoxy preparation on a mold on the
machine, and the start was bumped near the end of the B-axis session. TCPC work
was paused at `10:50 +07` for 3-axis work, then resumed in the dedicated TCPC
test config after the machine was stable again.

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
- keep transfer moves at or below `300 mm/min`
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
