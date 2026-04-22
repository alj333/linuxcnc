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
- Do not edit WCS/WCO during the sphere data collection pass. Keep one coordinate system active for the whole session.
- Before every sphere run, manually jog to a safe clearance position above the sphere at the target `B/C` pose. The current sphere cycle does not auto-index rotaries on purpose.

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

Recommended first-pass pose list:

- `B-45 C0`
- `B0 C0`
- `B+45 C0`
- repeat `B0 C0`

Recommended second-pass widening if needed:

- `B-60 C0`
- `B-30 C0`
- `B0 C0`
- `B+30 C0`
- `B+60 C0`

What to look for:

- center movement versus `B` angle is the key signal for tilt-axis pivot location errors

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
6. Only after that start the TCPC/TWP integration pass.
