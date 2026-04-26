# B-Axis Vector Probing Plan

Purpose: collect B-axis sphere data on the head-head machine without assuming
that machine Z remains the probe/tool vector after the head tilts.

## Current State

- The active config is still `trivkins`; TCPC/TWP is not enabled yet.
- The `B0` C-axis sweep is repeatable enough for the practical `0.10 mm`
  target.
- Latest automatic C sweep uses side probing at `sphere_center_z + 1.5 mm`.
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
6. Fit sphere centers offline from raw contacts; do not write WCS offsets.
7. Use repeated measurements and consistent approach direction to separate rotary
   geometry from rack/screw local error.

## Initial B Pose Set

Start conservative:

- `B0 C0`
- `B+15 C0`
- `B-15 C0`
- `B+30 C0`
- `B-30 C0`
- closing `B0 C0`

Only widen to `B+45/B-45` after vector signs and clearance are verified.

## Safety Rules

- Keep probe feeds at `50 mm/min` slow and `100 mm/min` fast.
- Keep transfer moves at or below `300 mm/min`.
- Use short vector step distances for the first dry run.
- Do not assume axis alignment is perfect.
- Do not compensate rack/screw tight spots by changing rotary geometry.
- Do not enable TCPC/TWP until the vector probing data and fit residuals are
  understood.
