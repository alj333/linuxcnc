# TWP Sphere Stage 1 - T4 Operator Plan

Date: 2026-08-31

## Purpose

This is the first supervised physical validation of synchronized `G68.2` using
the certified 30 mm sphere and the stable T4 long touch probe. It compares the
same sphere center in `WORLD / TWP / WORLD` without changing the TCPC
calibration, work offsets, tool table, or length-model coefficients.

The normal cut-test launcher remains TWP-locked. Use only:

- launcher: `launch_xyzbc_ssi_twp_probe_validation.sh`
- INI: `5th_axis_xyzbc_ssi_tcpc_probe_basic_twp_probe_validation_2026083101.ini`
- program: `twp_sphere_probe_stage1_t4.ngc`

## First Run

1. Confirm the laser and spindle inverter are isolated/off and the sphere is
   secure. Keep the machine supervised throughout the run.
2. Start the dedicated TWP validation launcher and home all five joints.
3. Install T4 in its repeatable orientation. In world mode apply `M61 Q4` and
   `G43 H4` at `B0 C0`. Confirm `G43.4` TCPC is off.
4. Keep the first run at `B0 C0`. Position the probe 3-5 mm above the accessible
   sphere surface along the probe axis. The sphere-to-post direction is
   `X- Y+ Z-`.
5. Load the stage-1 program. At its single initial `M0`, recheck T4/H4,
   `G43.4` off, clearance, quiet probe inputs, spindle off, and laser off;
   then resume.
6. Do not jog, change offsets, change tools, or issue MDI commands during the
   run.

The routine makes 24 gated `G38.3` contacts. Its adaptive quiet wait normally
holds for the configured 10 second post-contact ignore period, so a clean run
takes several minutes. The first TWP motion is a reversible 1 mm local `+Z`
move away from the sphere, followed by a closure check, before probing starts.

## Acceptance

The program fails closed unless all of these hold:

- exactly one gated edge per contact and 24 total gated contacts
- every two-pass center pair is within 0.100 mm
- every measured V diameter is 29.9 to 30.5 mm
- every four-contact radial residual is at most 0.250 mm
- opening-to-closing world center closure is at most 0.050 mm
- transformed TWP center error against the mean world center is at most
  0.050 mm
- B/C remain fixed and the commissioned length model remains valid throughout

Per-pass diagnostics append to `twp-sphere-stage1-t4-passes.csv` and can include
data from an attempt that later fails a pair or closing gate. Archive or clear
that diagnostic file between supervised attempts when unambiguous provenance
is required. The physical world-center row is appended to
`twp-sphere-stage1-t4-results.csv` only after the complete run passes every
final gate.

## Follow-On Runs

Review the complete B0 result before continuing. If it is coherent, repeat as
two separate operator-set runs at `B+5 C0` and `B-5 C0`. Reach each pose while
TWP is off, reposition the probe 3-5 mm above the same sphere along its current
axis, and restart the full program from its beginning. Do not combine poses in
one program at this stage.

## Recovery

Program-detected contact faults retract to the contact start, and all
program-detected active-TWP faults request `G69` before aborting. Do not resume
part-way through this WORLD/TWP/WORLD sequence.

After any operator Stop or Abort while TWP may be active, do not jog, reload,
or restart from line. If the controller and state component are healthy and the
machine is stationary, issue `G69` in MDI and verify ready world type 0 with
TWP clear. If `G69` is unavailable or state health is uncertain, close
LinuxCNC completely and use the clean-restart procedure below.

If LinuxCNC task/state health is lost, if the TWP state component disappears,
or if the displayed state is uncertain: stop motion, close LinuxCNC completely,
confirm all LinuxCNC processes have exited, relaunch the dedicated INI, home,
reapply T4/H4 with `G43.4` off, reposition above the sphere, and start the full
program again. A clean restart must begin in world kinematics with TWP clear.

## TWP Command Contract

`G43.4` and TWP are separate modes. The stage-1 program uses this sequence:

1. `G68.2` defines the tilted coordinate frame while world kinematics remains
   active.
2. `G53.1` activates the already defined frame through a stationary switchkins
   handoff. It does not enable the public TCPC state.
3. Fixed-B/C local XYZ motion and probing run in the tilted frame.
4. `G69` returns to world kinematics and clears the frame.

The implementation evaluates the same commissioned length-aware geometry used
by `G43.4` internally. It does not maintain a second TWP calibration. Fusion
`G68.2 X Y Z I J K` input uses rotating `ZXZ` Euler angles; the first release
expects the post to preposition B/C before `G68.2`/`G53.1`.

## Attempt 1 Status - 2026-09-01

The first physical B0/C0 attempt is a partial diagnostic run, not an accepted
TWP result. Its opening WORLD phase completed eight valid contacts and wrote
two pass rows. After stationary `G68.2`/`G53.1`, the independent coordinate
guard detected that the implementation had captured the homing-adjusted motor
layer instead of machine joint coordinates. It cancelled with `G69` before the
1 mm local preflight, so no physical local-TWP motion occurred.

The implementation now uses `joint.N.pos-cmd` for both remap frame capture and
the TWP state component. A headless replay reproducing the measured
joint/motor separation and exact captured B/C/G54 state completed all 24
contacts with `0.000965 mm` WORLD closure and `0.000510 mm` transformed TWP
error. The normal B+5/C0 case and all focused/legacy regressions also passed.
Calibration revision `2026082601` was not changed.

For the next physical attempt, close/restart the dedicated config, home all
five joints, reapply T4/H4 with `G43.4` off, return 3-5 mm above the sphere at
B0/C0, and run the complete program from its beginning. Do not resume after
the two retained WORLD rows from Attempt 1.
