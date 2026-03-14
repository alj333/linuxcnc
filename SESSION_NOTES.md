# Session Notes (2026-03-11)

## Working Bench Result
- LinuxCNC RIP tree reset clean, rebuilt, and `sudo make setuid` applied.
- `mesaflash` installed system-wide and available in `PATH`.
- Restored machine-style `configs/5th_axis` was left alone.
- Created isolated bench config for the test card:
  - `configs/7i95t_ssi_bench/7i95t_ssi_bench.ini`
  - `configs/7i95t_ssi_bench/7i95t_ssi_bench.hal`

## SSI Mapping
- `SSI.00` -> B axis
- `SSI.01` -> C axis

## Final Working Decode
- HostMot2 SSI format on both channels:
  - `crc%6unwarn%1bnerr%1babs%20ige`
- Meaning:
  - 6-bit CRC
  - 1-bit warning
  - 1-bit error
  - 20-bit absolute encoder
  - invert bits before Gray decode

## Proven Runtime Settings
- `hm2_7i95.0.dpll.01.timer-us = -350`
- `frequency-khz = 200`
- `timer-number = 1`
- `counts-per-rev = 1048576`

## Bench Behavior
- AXIS DRO is driven directly from:
  - `hm2_7i95.0.ssi.00.abs.position` for B
  - `hm2_7i95.0.ssi.01.abs.position` for C
- Encoders read correctly and smoothly with the `i` modifier enabled.

## Source Tree
- Repo remote:
  - `https://github.com/LinuxCNC/linuxcnc`
- Current commit at time of note:
  - `49509631f4`

## Update (2026-03-14)
- A new Mesa 7I95T bitfile was flashed and verified live with `mesaflash --readhmid`.
- Confirmed live resource mix:
  - `StepGen = 5`
  - `PWM = 1`
  - `SSI = 2`
- Confirmed exposed output layout:
  - five `Step/Dir` pairs
  - one `PWM/Dir` pair
  - two SSI channels
- Updated the bench HAL to match the flashed card:
  - `num_pwmgens=1`
  - `num_stepgens=5`
- Re-ran the bench encoder test with the same working decode:
  - `crc%6unwarn%1bnerr%1babs%20ige`
- Result:
  - LinuxCNC bench config starts cleanly
  - both encoders still read correctly
  - `data-invalid` remains false
  - the B/C DROs still follow the encoders correctly

## Update (2026-03-14, stable 2.9 machine-style copy)
- Created a machine-style SSI integration copy from the old `5th_axis` config:
  - `configs/5th_axis _SSI`
- Important constraint:
  - only the two SSI encoders were connected to the Mesa card during this phase
  - no other machine hardware was connected yet
- Forward-ported the copied config enough to start on the current stable branch.
- Switched the copied config to `trivkins` because this build does not contain
  the user's custom `5axiskins`.
- Disabled old optional or incompatible features in the copied config:
  - `classicladder`
  - `twp.hal`
  - `5axiskins`-specific startup HAL commands
  - `switchkins` startup logic
  - `M428/M429/M430/M431/M432`
  - `M254`
  - `ToolLengthControl.hal`
  - `probe_basic` display
- Added the proven SSI setup to the copied machine HAL:
  - `ssi_chan_0=crc%6unwarn%1bnerr%1babs%20ige`
  - `ssi_chan_1=crc%6unwarn%1bnerr%1babs%20ige`
  - `hm2_7i95.0.dpll.01.timer-us = -350`
- Integrated feedback in the copied machine HAL:
  - `SSI.00` -> B -> `joint.3.motor-pos-fb`
  - `SSI.01` -> C -> `joint.4.motor-pos-fb`
- Changed B/C index homing assumptions in the copied INI:
  - `HOME_USE_INDEX = NO`
- Result:
  - the copied machine-style config now starts
  - the encoders work inside that machine-style config
  - this is an encoder/config integration milestone only, not a full machine
    commissioning milestone

## Update (2026-03-14, Probe Basic test copy)
- Installed the Probe Basic development stack locally under:
  - `/home/cnc5/dev/qtpyvcp`
  - `/home/cnc5/dev/probe_basic`
  - `/home/cnc5/dev/venv`
- Installed the Debian Bookworm QtPyVCP / Probe Basic dependency set.
- Patched the local Probe Basic launchers to source the RIP environment when
  `/home/cnc5/linuxcnc-dev/scripts/rip-environment` exists.
- Created a separate Probe Basic UI test copy of the SSI machine config:
  - `configs/5th_axis_SSI_probe_basic`
- Added Probe Basic-specific files to that copy:
  - `custom_config.yml`
  - `pbsplash.png`
  - `user_buttons/`
  - `user_dro_display/`
  - `user_tabs/`
  - `probe_basic_postgui.hal`
  - `launch_probe_basic.sh`
- Probe Basic test copy uses:
  - `DISPLAY = probe_basic`
  - `POSTGUI_HALFILE = probe_basic_postgui.hal`
  - `DRO_DISPLAY = XYZBC`
- Important limitation:
  - LinuxCNC still has `XYZBCW`, but Probe Basic does not ship a stock `XYZBCW`
    DRO template, so `W` is intentionally omitted from the default Probe Basic
    DRO layout in this test copy.

## Update (2026-03-14, head-head 5-axis requirements)
- Captured the intended long-term machine model for future TCP/TWP work.
- Head-head topology:
  - spindle -> B -> C -> Z -> X -> frame -> Y
- Coordinate conventions:
  - `+X` left to right
  - `+Y` back to front toward the operator
  - `+Z` up away from the table
- Rotary conventions:
  - `B` axis parallel to `Y`
  - `C` axis parallel to `Z`
  - `B=0`, `C=0` => tool points in `-Z`
  - `+B` tilts tool toward `+X`
  - `+C` is clockwise viewed from above
  - `B` range `-100` to `+100`
  - `C` range `-360` to `+360`
- The rebuilt head/Z structure means final offsets are not yet fixed.
- The future kinematics must support full calibration of axis and spindle
  offsets rather than assuming ideal intersecting rotary axes.
- Known current geometric assumption:
  - spindle centerline is approximately `+25 mm` in `Y` from the `C` axis
    centerline
- Future target:
  - custom head-head kinematics
  - TCP that holds tool tip position through `B/C` changes
  - TWP that transforms rotated-plane motion back to machine motion
  - full LinuxCNC visual simulation for validation
- Follow-up design decision:
  - if the rebuild allows it, move the machine to standard industrial
    right-hand sign conventions rather than preserving the provisional
    `+Y toward operator`, `+B toward +X`, `+C clockwise from above` mapping
  - preferred production convention is:
    - `+X` right
    - `+Y` away from operator
    - `+Z` up
    - `+B` by right-hand rule about `+Y`
    - `+C` by right-hand rule about `+Z`
- Began a separate kinematics R&D branch:
  - `head-head-kinematics-rnd`
- Added initial simulation baseline files:
  - `configs/sim/head_head_5axis/README.md`
  - `configs/sim/head_head_5axis/geometry_baseline.ini`
- Added a temporary runnable math-only scaffold:
  - `configs/sim/head_head_5axis/head_head_math_sim.ini`
  - `configs/sim/head_head_5axis/head_head_math_sim.hal`
- Current scaffold uses `trivkins` as a placeholder only.
- It is intended to validate axis ranges and coordinate ordering before custom
  head-head kinematics, TCP, and TWP are implemented.
- Installed local CAD tooling for the visual simulation path:
  - `freecad`
  - `freecadcmd`
  - `gmsh`
- Result:
  - `freecadcmd` segfaults on the uploaded `5th_Axis.step` assembly after
    import completes
  - `gmsh` successfully imports the STEP file and exports STL
- Known working conversion command:
  - `gmsh /home/cnc5/dev/5thAxis/5th_Axis.step -0 -format stl -o /tmp/5th_Axis_from_gmsh.stl`
- The whole-machine STL export works locally but was not committed on the
  pushable branch because it exceeds GitHub's normal file size limit.
- Inspected the STEP assembly structure and recorded the current split strategy:
  - `configs/sim/head_head_5axis/step_product_inventory.txt`
  - `configs/sim/head_head_5axis/mesh_split_strategy.md`
- Current finding:
  - the uploaded STEP export is sufficient for a whole-machine reference mesh
  - it is not granular enough to split `B` and `C` rotary stages cleanly for an
    articulated head-head visual simulation
- Next CAD requirement for visual sim:
  - separate exports for base, gantry, X carriage, Z carriage, C body, B body,
    and spindle
- Initial nominal simulation assumptions:
  - `X = 0 .. 3310`
  - `Y = 0 .. 1700`
  - `Z = -900 .. 0`
  - `B = -100 .. +100`
  - `C = -360 .. +360`
  - home at `X0 Y0 Z0 B0 C0`
  - nominal `C` to `B` offset = `0,0,0`
  - nominal `B` to spindle nose vector = `(0, +25, -180) mm`
  - calibration support is mandatory for real offsets and assembly error
## 2026-03-14 - Head-head kinematics scaffold started

- Branch: `head-head-kinematics-rnd`
- Added `src/emc/kinematics/headheadkins.c`
- Added build hooks in `src/Makefile` and `src/emc/kinematics/meson.build`
- Updated `configs/sim/head_head_5axis/head_head_math_sim.ini` to use
  `KINEMATICS = headheadkins coordinates=XYZBC kinstype=B`
- Updated `configs/sim/head_head_5axis/head_head_math_sim.hal` to set the
  nominal geometry pins directly
- Implemented first parameterized head-head forward/inverse model:
  - `X/Y/Z` locate the `C` pivot center
  - `C` rotates about `+Z`
  - `B` rotates about `+Y` in the `C` frame
  - tool reference offset is `Rz(C) * (C_to_B + Ry(B) * B_to_tool)`
- Exposed HAL pins for nominal geometry, calibration geometry, and rotary zero
  offsets so future TCP/TWP work can build on a calibratable model
- Added `configs/sim/head_head_5axis/reference_poses.py` to print nominal tool
  offsets for key `B/C` poses using the same baseline geometry used by the sim
