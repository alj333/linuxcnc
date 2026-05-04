# B-Axis Vector Probing Plan

Purpose: collect B-axis sphere data on the head-head machine without assuming
that machine Z remains the probe/tool vector after the head tilts.

## Current State

- 2026-05-03 update: this early B-axis vector probing plan is superseded for
  live TCPC work by `TCPC_FIT_NEXT_SCOPE.md` and the clean B90 diagnostic
  handoff. The historical routine notes below remain useful for understanding
  the vector probing method, but the next live step is a B90 C-quadrant TCPC
  diagnostic, not the early current-pose `trivkins` B-vector workflow.
- The active TCPC calibration work now uses the dedicated TCPC Probe Basic
  config, not the original `trivkins` phase.
- The `B0` C-axis sweep is repeatable enough for the practical `0.10 mm`
  target.
- Latest automatic C sweep uses side probing at `sphere_center_z + 1.5 mm`.
- Current-pose vector sphere probing has been validated manually at
  `B+15 C0` and `B-15 C0`; the automatic two-pass routine is validated at
  `B+15 C0`, `B+30 C0`, `B-30 C0`, and closing `B0 C0`.
- The latest closing `B0 C0` accepted result is usable with a caveat because
  epoxy preparation started on a mold on the machine and the start was bumped.
- Linear-axis rack/screw errors are known possible contributors and must not be
  hidden inside rotary geometry offsets.

## Why B Needs A Different Routine

The current sphere routine is acceptable for `B0` C sweeps because the probe is
effectively vertical in machine coordinates. At nonzero `B`, the probe vector is
tilted. A correct B-axis routine must probe along local head vectors, not fixed
machine `X/Y/Z` directions.

Use a local orthonormal frame at each `B/C` pose:

- `W`: probe/tool vector, pointing along the stylus axis.
- `U`: one side-probe vector perpendicular to `W`.
- `V`: second side-probe vector perpendicular to both `W` and `U`.

The routine should move/probe along `-W`, `+U`, `-U`, `+V`, and `-V`, then log
raw trigger points. Center fitting should initially be done offline so we can
inspect residuals before using the data for TCPC offsets.

## First Safe Implementation

1. Add a vector-only dry-run program that indexes B/C and makes short non-probing
   vector moves in `X/Y/Z`: `nc_files/calibration/b_axis_vector_dry_run_b0_c0.ngc`.
2. Verify vector signs visually at small B angles, with no sphere contact.
3. Validate the first real contact with a current-pose top-touch program:
   `nc_files/calibration/b_axis_vector_top_touch_current_pose.ngc`.
4. Add a raw-contact sphere probing routine using slow feeds only.
   First current-pose routine:
   `nc_files/calibration/b_axis_vector_sphere_current_pose.ngc`.
5. Log raw machine-space trigger points plus commanded `B/C`, probe diameter,
   calibration offset, and feed settings.
6. Add an automatic two-pass current-pose routine before wider B data:
   pass 1 measures, computes local `U/V` centering error, shifts internally,
   then pass 2 repeats and becomes the accepted result.
   Current two-pass routine:
   `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc`.
7. Fit sphere centers offline from raw contacts; do not write WCS offsets.
8. Use repeated measurements and consistent approach direction to separate rotary
   geometry from rack/screw local error.

## Two-Pass Centering Requirement

The first `B+15 C0` and `B-15 C0` runs showed that the operator can be close
visually while still starting off the tilted `W` centerline. Manual local
corrections fixed the data, so the routine should automate that step.

Required behavior:

- Keep it current-pose only; do not auto-index `B/C`.
- Do not write WCS offsets.
- Use the full U-pair midpoint error for local `U` correction.
- Use the full V-pair midpoint error for local `V` correction.
- Do not halve the correction by averaging the U and V midpoint estimates.
- Abort if either local correction is greater than about `2.0 mm`.
- Abort if either corrected diameter is outside about `29.5-30.5 mm`.
- Log both passes and mark pass 2 as the accepted result.
- Validate the two-pass routine at `B-15 C0` or `B+15 C0` before using it at
  `B+30 C0`.

Validation status:

- The two-pass routine has been validated at `B+15 C0`.
- Pass 1 corrected `U=+1.692917 mm`, `V=-1.519167 mm`.
- Pass 2 residual centering error was `U=-0.002083 mm`, `V=+0.001250 mm`.
- `B+30 C0` pass 2 accepted center:
  `X=151.969455 Y=352.913688 Z=-321.714304`.
- `B-30 C0` pass 2 accepted center:
  `X=460.527766 Y=352.638896 Z=-322.390804`.
- Closing `B0 C0` pass 2 accepted center:
  `X=306.338526 Y=352.821813 Z=-280.762445`.
- One later full `B0 C0` two-pass repeat exists after the bumped start. Preserve
  it as raw data, but do not use it in the first TCPC fit candidate.
- Machine probing is paused until the mold/epoxy work is clear and the sphere
  setup is stable again.

## Initial B Pose Set

Start conservative:

- `B0 C0`
- `B+15 C0`
- `B-15 C0`
- `B+30 C0`
- `B-30 C0`
- closing `B0 C0`

Only widen to `B+45/B-45` after vector signs and clearance are verified.

## Next Scope

- Build the first offline TCPC fit candidate from accepted rows only.
- Use `tcpc-fit-input-candidates.csv` as the controlled input list, not the raw
  logs directly.
- Treat `B-15 C0` as lower-confidence because it came from a corrected
  single-pass run, not the automatic two-pass routine.
- Repeat closing `B0 C0` and preferably `B-15 C0` with the two-pass routine
  after the machine environment is stable.
- Do not write INI/HAL kinematics offsets until the fit report and residuals are
  reviewed.

## Safety Rules

- Keep probe feeds at `50 mm/min` slow and `100 mm/min` fast.
- Keep transfer moves at or below `300 mm/min`.
- Use short vector step distances for the first dry run.
- Do not assume axis alignment is perfect.
- Do not compensate rack/screw tight spots by changing rotary geometry.
- Do not enable TCPC/TWP until the vector probing data and fit residuals are
  understood.
