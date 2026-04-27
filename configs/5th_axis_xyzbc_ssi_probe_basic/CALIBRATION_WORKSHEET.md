# XYZBC Calibration Worksheet

Use this worksheet with the Probe Basic calibration config:

- launcher: `configs/5th_axis_xyzbc_ssi_probe_basic/launch_xyzbc_ssi_probe_basic.sh`
- ring qualification program: `nc_files/calibration/50mm_ring_probe_qualify.ngc`
- ring verification program: `nc_files/calibration/50mm_ring_probe_verify.ngc`
- sphere center measurement program: `nc_files/calibration/30mm_sphere_measure_current_pose.ngc`

## Ground Rules

- Do all early calibration work in the Probe Basic `trivkins` config. Do not enable TCPC yet.
- Fix the `50 mm` ring and `30 mm` sphere rigidly to the table and leave them there for the whole session.
- Use the same probe stylus, probe feedrates, and probing strategy for the whole dataset.
- In Probe Basic, set the probe tool number and probe parameters in the UI, then press `UPDATE PROBE PARAMS` once after startup so the values are mirrored into `#3014..#3036`.
- Current wireless probe tool is `T3`; set Probe Basic probe tool number to `3` before pressing `UPDATE PROBE PARAMS`.
- Current accepted probe calibration offset from repeated ring calibration runs on 2026-04-26 is `0.134533`.
- Keep calibration probe feedrates slow for this work: use `50 mm/min` slow probe, `100 mm/min` fast probe, and keep traverse/transfer moves at or below `300 mm/min`.
- Probe Basic does not provide a native sphere calibration workflow. The 30 mm sphere routine is a custom wrapper that only reuses Probe Basic's basic setup values where they map cleanly: probe tool, feeds, max distances, clearances, and calibration offset.
- Do not edit WCS/WCO during the sphere data collection pass. Keep one coordinate system active for the whole session.
- The calibration wrappers preserve the active WCS. Use a deliberate calibration WCS for the whole session. On 2026-04-26 the operator allowed use of `G54` after saving the project offsets externally.
- This config's startup modal includes `G54`, so after restart or program end, verify the active WCS before each run.
- Before every sphere run, manually jog to a safe clearance position above the sphere at the target `B/C` pose. The current sphere cycle does not auto-index rotaries on purpose.
- The sphere cycle appends numeric results to `sphere-center-results.csv` in this config directory.
- Practical TCPC target for this large steel machine is about `0.10 mm`; do not chase thermal drift below the machine's current no-temperature-compensation envelope.
- Most intended 5-axis work is vacuum-formed part cutout, so prioritize repeatable safe TCPC behavior over ultra-fine mold-finishing accuracy.
- Small mechanical errors, backlash, and compliance are expected. Treat those as future refinement work, not as blockers for the first TCPC geometry fit.

## Step 1: Ring Qualification

Purpose:

- qualify the probe
- establish the calibration offset used by the sphere center cycle

Program:

- `nc_files/calibration/50mm_ring_probe_qualify.ngc`

Start condition:

- probe tool loaded
- spindle stopped
- probe tip above the left inside edge of the ring
- tip roughly centered in `Y`
- safe `Z` above the ring top

What to record:

- suggested calibration offset from the Probe Basic calibration widget after the run

Repeat until stable:

- run the qualification cycle
- confirm the Probe Basic calibration offset field contains the accepted value
- run the verify cycle at least `3` times
- stop only when average diameter and center repeatability are stable

Recommended acceptance before moving on:

- averaged measured ring diameter within a few microns of `50.000 mm`
- center repeatability at the ring well below the geometry error you are trying to solve

## Step 2: Sphere Baseline At B0 C0

Purpose:

- establish the base sphere center reference with the machine at `B0 C0`

Program:

- `nc_files/calibration/30mm_sphere_measure_current_pose.ngc`

Before each run:

- set the target `B/C` pose manually
- jog to a safe point above the sphere top
- jog so the probe is roughly over the sphere center in `X/Y`
- confirm the Probe Basic calibration offset field is current and click `UPDATE PROBE PARAMS` if you changed it

What the sphere program logs:

- `B/C` pose
- probe tool number and calibration offset used by the run
- relative center `X/Y/Z`
- absolute machine center `X/Y/Z`
- equator diameters measured in `X` and `Y`
- top contact `Z`

Run count:

- measure `B0 C0` at least `3` times before using it as the baseline

Use the average of those `B0 C0` runs as the baseline reference center.

## Step 3: C-Axis Sweep

Purpose:

- isolate pure `C` geometry errors with `B` fixed at zero

Recommended pose list:

- `B0 C0`
- `B0 C90`
- `B0 C180`
- `B0 C270`
- repeat `B0 C0`

What to look for:

- solved sphere center should stay in one place
- drift in solved center across the `C` sweep points to `C` zero / axis-center / geometry error

## Step 4: B-Axis Sweep

Purpose:

- isolate `B` tilt-axis geometry with `C` fixed
- for the head-head machine, collect this with a B-aware vector routine, not
  the `B0` machine-Z sphere routine

Recommended first-pass pose list:

- `B0 C0`
- `B+15 C0`
- `B-15 C0`
- `B+30 C0`
- `B-30 C0`
- repeat `B0 C0`

Recommended second-pass widening if needed:

- `B0 C0`
- `B+45 C0`
- `B-45 C0`
- `B+60 C0`
- `B-60 C0`

What to look for:

- center movement versus `B` angle is the key signal for tilt-axis pivot location errors
- raw contact residuals and repeatability must be checked before fitting B-axis
  geometry, because local rack/screw error and alignment error can otherwise be
  mistaken for rotary pivot error

B-axis vector probing rule:

- At nonzero `B`, the probe/stylus vector is no longer machine `Z`.
- Use a local head frame: `W` along the probe vector, and `U/V` perpendicular
  side-probe vectors.
- First run a short non-contact vector dry-run to verify signs and clearance.
- Then log raw contact points and fit sphere center offline before using the
  data in TCPC geometry.
- Current B-axis vector routine:
  `nc_files/calibration/b_axis_vector_sphere_current_pose.ngc`.
- Current B-axis two-pass vector routine:
  `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc`.
- Current B-axis vector logs:
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-raw-points.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-sphere-results.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-2pass-raw-points.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-2pass-results.csv`
- End-of-day status on 2026-04-26:
  - `B+15 C0` repeated tightly after manual local `U` correction
  - `B-15 C0` repeated tightly after manual local `U/V` correction
  - before collecting `B+30/B-30`, validate the two-pass routine at a known
    pose, then use it for the remaining B-axis data
- 2026-04-27 update:
  - two-pass routine validated at `B+15 C0`
  - pass 2 accepted center
    `X=226.486276 Y=352.897855 Z=-291.117802`
  - `B+30 C0` pass 2 accepted center
    `X=151.969455 Y=352.913688 Z=-321.714304`
  - `B-30 C0` pass 2 accepted center
    `X=460.527766 Y=352.638896 Z=-322.390804`
  - closing `B0 C0` pass 2 accepted center
    `X=306.338526 Y=352.821813 Z=-280.762445`
  - closing `B0 C0` has a caveat: staff started epoxy prep on a mold on the
    machine and the start was bumped, so do not treat this as the final thermal
    or setup-stability reference without a later repeat
  - one extra full `B0 C0` two-pass repeat was logged after the bumped start;
    keep it in the raw CSV record but exclude it from the first fit candidate
    because the run was unintended and the machine environment was disturbed
  - machine probing is paused until the mold/epoxy work is clear and the sphere
    setup is stable again
  - next scope is offline TCPC candidate fitting from the accepted C-sweep and
    curated B-vector data; see `TCPC_FIT_NEXT_SCOPE.md`

## Step 5: Mixed-Pose Cross Check

Purpose:

- confirm the geometry fit against mixed `B/C` poses before starting TCPC work

Recommended pose list:

- `B0 C0`
- `B0 C90`
- `B0 C180`
- `B+45 C0`
- `B+45 C180`
- `B-45 C0`
- `B-45 C180`

## Data To Keep

Use the CSV template:

- `configs/5th_axis_xyzbc_ssi_probe_basic/sphere_center_log_template.csv`

Current raw sphere CSV:

- `configs/5th_axis_xyzbc_ssi_probe_basic/sphere-center-results.csv`

Setup note:

- The custom 30 mm sphere wrapper caps `xy_clearance` at `2.0 mm` for this routine only. Probe Basic's normal large mold-work clearance can remain unchanged.

Initial loose-sphere motion test at `B0 C0`:

- relative center `X=-2.007917 Y=-1.207917 Z=104.777029`
- absolute center `X=306.333197 Y=352.762646 Z=-280.900367`
- side diameters `X=29.709767 Y=29.704766`
- top contact `Z=122.642496`
- use this as motion-validation only, not TCPC fit data

Secured `B0 C0` baseline from three repeat runs:

- average absolute center `X=306.368475 Y=352.795840 Z=-280.750222`
- absolute center repeatability range `X=0.001667 Y=0.001667 Z=0.000900`
- average side diameters `X=29.771711 Y=29.674210`
- side-diameter repeatability range `X=0.004999 Y=0.002500`
- use this average as the initial baseline for C/B sweep deltas

Record for every sphere run:

- stage
- pose label
- commanded `B`
- commanded `C`
- solved relative center `X/Y/Z`
- solved absolute center `X/Y/Z`
- solved `X` equator diameter
- solved `Y` equator diameter
- top-contact `Z`
- notes

After the first `B0 C0` baseline is stable, also compute:

- `dX = abs_x - baseline_abs_x`
- `dY = abs_y - baseline_abs_y`
- `dZ = abs_z - baseline_abs_z`

Those deltas are the values you fit against when solving the rotary geometry.

## Immediate Next Engineering Steps

1. Get the ring calibration offset stable.
2. Get repeatable `B0 C0` sphere-center data.
3. Collect the `C` sweep.
4. Collect the `B` sweep.
5. Fit geometry from the absolute center deltas.
6. Accept the first TCPC fit when fixed-tip error is repeatable around `0.10 mm` across the practical pose set.
7. Only after that start the TWP integration pass.
