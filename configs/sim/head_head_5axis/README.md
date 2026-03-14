# Head-Head 5-Axis Simulation Baseline

## Scope

This directory is the starting point for head-head 5-axis kinematics R&D.

It now contains a runnable math sim and a runnable visual sim. The goal is to
lock:

- machine conventions
- nominal travels
- nominal rotary geometry
- calibration requirements

before building:

- a new head-head kinematics component
- TCP support
- TWP support
- a full visual LinuxCNC simulation

## Current Scaffold

This directory now also contains a first runnable math scaffold:

- `head_head_math_sim.ini`
- `head_head_math_sim.hal`
- `head_head_twp_state.hal`
- `head_head_twp_state.py`

Purpose of the scaffold:

- validate the agreed axis envelope
- validate `XYZBC` coordinate ordering
- validate nominal home and rotary limit assumptions
- validate the first `C then B` head-head forward/inverse model
- provide the starting point for TCP/TWP work

Current limitation:

- it uses a nominal geometry-only `headheadkins` module
- it does not implement production-grade TCP mode semantics beyond tool-tip
  `XYZBC` kinematics
- it does not implement TWP
- it is still a development simulation, not a production machine model

Launch:

```bash
cd ~/linuxcnc-dev
source scripts/rip-environment
linuxcnc configs/sim/head_head_5axis/head_head_math_sim.ini
```

Visual launch:

```bash
cd ~/linuxcnc-dev
source scripts/rip-environment
linuxcnc configs/sim/head_head_5axis/head_head_visual_sim.ini
```

## Locked Production Convention

The future machine math should use standard right-hand industrial convention:

- `+X` right
- `+Y` away from operator
- `+Z` up
- `+B` follows the right-hand rule about `+Y`
- `+C` follows the right-hand rule about `+Z`
- `B=0`, `C=0` => tool points in `-Z`

This convention is the production target even if interim rebuild stages use
temporary opposite signs or offsets.

## Nominal Travels

- `X = 0 .. 3310 mm`
- `Y = 0 .. 1700 mm`
- `Z = -900 .. 0 mm`
- `B = -100 .. +100 deg`
- `C = -360 .. +360 deg`

Home pose:

- `X=0`
- `Y=0`
- `Z=0`
- `B=0`
- `C=0`

Important distinction:

- axis `Z` is the user-facing tool-tip travel range
- `JOINT_2` is the internal pivot-center `Z` joint
- because the head has a long offset below the `C` pivot, `JOINT_2` must have
  additional positive travel above axis `Z=0`
- current simulation setting:
  - `JOINT_2 = -630 .. +450`
  - `JOINT_2 HOME = 450`

## Nominal Head Geometry

Current nominal starting model:

- `C` center to `B` center = `(0, 0, -270) mm`
- spindle centerline offset is approximately `+25 mm` in `Y`
- `B` center to spindle nose reference is approximately `180 mm`

Approximate nominal vector from `B` center to spindle nose at `B=0`, `C=0`:

- `(0, +25, -180) mm`

This is now the shared baseline for both:

- `headheadkins`
- `head_head_vismach.py`

The visual model no longer adds hidden rotary offsets on top of the HAL pins.
`C->B` and `B->tool` are driven from the same nominal geometry values used by
the kinematics math.

## Current Kinematics Model

The current `headheadkins` scaffold assumes:

- `X/Y/Z` joints locate the `C` pivot center in world space
- `C` rotates about `+Z`
- `B` rotates about `+Y` in the `C`-rotated frame
- world `XYZ` represent the tool reference point

Current compensation model:

```text
tool_offset_world = Rz(C + c_zero) * (c_to_b + Ry(B + b_zero) * b_to_tool)
tool_tip_world    = [X, Y, Z] + tool_offset_world
```

This is sufficient to expose sign, order, and pivot-offset mistakes early,
which is the immediate goal of the math simulation.

Current TCP interpretation:

- in this scaffold, world `XYZ` are already tool-tip coordinates
- that means coordinated `XYZBC` motion already behaves as TCP in the sim
- what is still missing is production-level operator semantics, mode handling,
  and later TWP integration

Current TWP interpretation:

- the branch now has a prototype TWP state component plus the earlier offline
  preprocessor
- `headheadtwp` can snapshot:
  - current tool-tip origin
  - current `B/C` orientation
  - optional plane-normal rotation
- for now, live TWP motion is still not implemented
- the offline transform remains the path-generation test tool
- plane-local `UVW` points at fixed `B/C` are transformed into world `XYZ`
- that transformed `XYZBC` path is then executed by the existing TCP-capable
  kinematics scaffold
- this is a math-validation step, not yet a production TWP mode inside LinuxCNC

Prototype TWP state commands from a terminal:

```bash
halcmd setp headheadtwp.cmd_set_from_current 1
halcmd setp headheadtwp.cmd_set_from_current 0
halcmd getp headheadtwp.state_code
halcmd getp headheadtwp.twp_origin_x
halcmd getp headheadtwp.twp_origin_y
halcmd getp headheadtwp.twp_origin_z
halcmd getp headheadtwp.twp_b_angle
halcmd getp headheadtwp.twp_c_angle
```

Activate / cancel:

```bash
halcmd setp headheadtwp.cmd_activate 1
halcmd setp headheadtwp.cmd_activate 0
halcmd setp headheadtwp.cmd_cancel 1
halcmd setp headheadtwp.cmd_cancel 0
```

`state_code` meanings:

- `0` undefined
- `1` partial definition
- `2` defined
- `3` active

Prototype TWP M-codes:

- `M150` set TWP origin from current tool tip
- `M151` set TWP orientation from current `B/C`
- `M152` set both origin and orientation from current pose
- `M153` activate stored TWP state
- `M154` cancel active TWP state
- `M155` reset TWP state
- `M156 P...` set plane-normal rotation

Demo program:

- [twp_state_demo.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/twp_state_demo.ngc)

Important limit:

- these M-codes currently control only the stored TWP state
- they do not yet cause LinuxCNC motion to be interpreted in the tilted plane

Reference pose calculator:

```bash
cd ~/linuxcnc-dev
python3 configs/sim/head_head_5axis/reference_poses.py
```

This prints the nominal tool offset from the `C` pivot center for a small set
of `B/C` reference poses. It is intended to catch sign and rotary-order errors
before TCP or visual simulation is layered on.

TCP compensation calculator:

```bash
cd ~/linuxcnc-dev
python3 configs/sim/head_head_5axis/tcp_compensation.py --start-b 0 --start-c 0 --end-b 90 --end-c 0
```

This prints the nominal `XYZ` compensation required to change from one `B/C`
pose to another while keeping the tool tip fixed.

TCP validation program:

```bash
cd ~/linuxcnc-dev
python3 configs/sim/head_head_5axis/generate_tcp_test_ngc.py
```

Generated program:

- [tcp_test_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/tcp_test_sequence.ngc)

How to use it:

1. Launch the visual sim.
2. Open `configs/sim/head_head_5axis/tcp_test_sequence.ngc`.
3. Run the program.
4. At each `M0`, check whether the visual tool tip stays on the same target
   point while `B/C` change.

Test intent:

- `XYZ` stays constant in the G-code
- only `B/C` change
- inverse kinematics must solve the internal pivot-center `XYZ` compensation
- if the tip wanders, the current transform model or sign convention is wrong

Moving TCP validation program:

```bash
cd ~/linuxcnc-dev
python3 configs/sim/head_head_5axis/generate_tcp_motion_ngc.py
```

Generated program:

- [tcp_motion_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/tcp_motion_sequence.ngc)

Test intent:

- move the tool tip in `XYZ` while changing `B/C`
- confirm the tip follows the commanded path while orientation changes
- use this only after `tcp_test_sequence.ngc` shows no fixed-tip drift

TWP transform helper:

```bash
cd ~/linuxcnc-dev
python3 configs/sim/head_head_5axis/twp_transform.py --b 45 --c 90 --local-u 150 --local-v 0 --local-w 0
```

Generated TWP validation program:

- [generate_twp_test_ngc.py](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/generate_twp_test_ngc.py)
- [twp_test_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/twp_test_sequence.ngc)
- [twp_operator_interface.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/twp_operator_interface.md)
- [visual_acceptance_checklist.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/visual_acceptance_checklist.md)

How to use it:

1. Launch the visual sim.
2. Open `configs/sim/head_head_5axis/twp_test_sequence.ngc`.
3. Run the program.
4. Confirm the path stays in the tilted plane while `B/C` remain fixed.

Test intent:

- validate the plane basis for a fixed `B/C` orientation
- validate plane-local to world `XYZ` transformation
- establish the math before implementing a production TWP operator mode

## Rough Visual Model

The visual config adds:

- [head_head_visual_sim.ini](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_visual_sim.ini)
- [head_head_vismach.hal](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_vismach.hal)
- [head_head_vismach.py](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_vismach.py)

Purpose:

- provide a rough articulated model for sign/order checking
- help expose TCP compensation mistakes early
- remain independent of the final CAD split work

The visual model is deliberately approximate. It follows the current kinematic
chain and nominal geometry, not final machine cosmetics.

Current visual debugging aids:

- moving-table `Y` is visually inverted so table motion matches a table-axis
  machine
- cyan alignment post and cross move with the table
- green table centerlines move with the table
- corner markers make travel direction easier to read

These aids are there to make TCP and travel-direction errors visible quickly.

Optional local STL overlay:

- set `HEAD_HEAD_FULL_STL` to a local ASCII STL path before launch
- the STL is used only as a static visual reference and is not required
- this branch intentionally does not commit the large mesh file

Example:

```bash
cd ~/linuxcnc-dev
source scripts/rip-environment
HEAD_HEAD_FULL_STL=/tmp/5th_Axis_from_gmsh.stl \
linuxcnc configs/sim/head_head_5axis/head_head_visual_sim.ini
```

## Calibration Requirement

The final machine must support calibrated geometry, not idealized-only
kinematics.

The simulation and future kinematics should expose parameters for:

- rotary zero offsets
- `C` to `B` center offsets
- `B` to spindle/tool reference offsets
- spindle/tool centerline assembly error

Known example of real error from the previous assembly:

- spindle center offset relative to the `B` axis was about `2 mm`

## Next Steps

1. Build a math-only simulation around the values in `geometry_baseline.ini`
2. Add a parameterized forward/inverse kinematics model
3. Add production TCP mode semantics on top of the same transform model
4. Add production TWP mode semantics on top of the same transform model
5. Build a visual machine model from Fusion 360 geometry

## Fusion 360 Inputs Needed Later

- home-pose screenshots with axis arrows
- pivot dimensions
- simplified STL exports
- known test poses for validation

## Local CAD Tooling Status

Installed on this PC:

- `freecad`
- `freecadcmd`
- `gmsh`

Current result with the uploaded machine model:

- `freecadcmd` imports the STEP model to 100% and then segfaults on this
  assembly
- `gmsh` successfully reads the STEP file and exports STL from the command line

Known working conversion command on this machine:

```bash
gmsh /home/cnc5/dev/5thAxis/5th_Axis.step -0 -format stl -o /tmp/5th_Axis_from_gmsh.stl
```

Observed output:

- resulting STL size was about `113 MB`
- the STEP assembly names were preserved well enough during import to confirm
  major groups like `BaseFrame`, `CrossBeam`, `Z-Axis Frame`, `Head`, `Table`,
  and `Spindle`

Practical implication:

- local mesh conversion is now possible
- the next visual-sim step should use `gmsh` or a later simplified CAD export,
  not `freecadcmd`, unless the FreeCAD crash is resolved

Local whole-machine mesh note:

- the `gmsh` export works locally, but the resulting STL is about `113 MB`
- that is above GitHub's normal file limit, so the mesh is intentionally not
  committed on this branch
- regenerate locally when needed with:

```bash
gmsh /home/cnc5/dev/5thAxis/5th_Axis.step -0 -format stl -o /tmp/5th_Axis_from_gmsh.stl
```

Current split-planning files:

- [step_product_inventory.txt](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/step_product_inventory.txt)
- [mesh_split_strategy.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/mesh_split_strategy.md)

Current conclusion:

- the uploaded STEP file is good enough for a full-machine reference mesh
- it is not granular enough to articulate `B` and `C` separately
- the next CAD export should provide separate moving groups for:
  - base/table
  - Y gantry
  - X carriage
  - Z carriage
  - C body
  - B body
  - spindle
