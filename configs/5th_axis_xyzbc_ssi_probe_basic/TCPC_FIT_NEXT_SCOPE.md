# TCPC Fit Next Scope

Status: TCPC direction checks, small-pose fixed-tip validation, wider mixed-pose
validation, post-backlash symmetric validation, and the first expanded
C-quadrant / B `+/-50 deg` matrix have run on the real machine. B/C LinuxCNC
backlash compensation is disabled in the TCPC test config, and all TCPC
calibration corrections remain zero. The expanded run shows tight `B0 C0`
closures but pose-dependent error increasing with B angle, so the next work is
offline sensitivity fitting and alignment diagnosis, not more direction-only
checks. Current practical acceptance target is `0.2 mm`; refine toward
`0.1 mm` only after mechanical backlash, alignment, servo tuning, and
thermal/return-path repeatability are better characterized.

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
  feed is `600 mm/min`; use lower feeds again if clearance or setup confidence
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

B `+/-50` diagnostic status:

- `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc` was
  temporarily set to `#707 = 50.0` and later `#706 = 0.0` so the proven groups
  run without operator stops.
- Repeated B `+/-50` attempts were interrupted by wireless/optical probe
  faults, logged by Probe Basic as `Probe tripped during non-probe move`.
- The operator identified likely optical receiver interference from laser tube
  cutters and other workshop IR/reflection sources.
- The first restart produced a clean B0 C-only group with closure
  `0.005963 mm` but stopped after `B+10 C0` pass 1.
- A resume-mode retry started from a fresh accepted `B0 C0` baseline at
  `X=357.533806 Y=317.969502 Z=-858.917885`, completed accepted pass-2 rows
  through `B-10 C180`, then stopped during the move after `B-10 C270` pass 1.
- The latest partial resume rows are useful as a fault record only; do not use
  them as the final expanded B `+/-50` validation because the B `+/-10` group
  did not close and B `+/-30`/`+/-50` were not reached.

Temporary program state for the next after-hours run:

- `#706 = 0.0`: no stops between B groups.
- `#707 = 50.0`: B `+/-50` diagnostic enabled.
- `#708 = 1.0`: resume mode enabled. The program probes a fresh `B0 C0`
  baseline, skips the full B0 C quadrant sweep, then runs B `+/-10`,
  B `+/-30`, and B `+/-50`.

Next action:

- Run the resume-mode program only when likely optical probe interference is
  removed. Treat the next clean block after a fresh accepted `B0 C0` baseline
  as the active B `+/-50` diagnostic. Exclude the partial false-trip blocks.

## Handoff For 3-Axis Machine Use - 2026-04-29

The TCPC session is paused after repeated probe/optical faults during the
B `+/-50` diagnostic.

Current TCPC test-config state to return to:

- B/C LinuxCNC backlash compensation disabled in the TCPC test config
- direct SSI rotary logging is available for symmetric and expanded programs
- the first simple correction candidate is loaded in the TCPC test config and
  mirrored to `headheadtwp.*`
- corrected symmetric validation and corrected B `+/-30` expanded validation
  passed inside the current `0.2 mm` practical target
- corrected B `+/-50` validation is still incomplete because the wireless
  probe false-tripped before the B `+/-30` and B `+/-50` groups in the latest
  resume attempt
- the active expanded program is intentionally in temporary B `+/-50` resume
  mode with `#706 = 0.0`, `#707 = 50.0`, and `#708 = 1.0`

For 3-axis work:

- close the TCPC config and use a normal `trivkins` maintenance/setup config
- keep `G55` reserved for staff 3-axis setup work unless the operator releases
  it
- do not use the TCPC test config for cutting
- when TCPC resumes, restart at a known safe C side of the wrap, preferably
  C0, home, confirm TCPC status, then run only slow no-cut validation first

Future servo-tuning scope:

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
