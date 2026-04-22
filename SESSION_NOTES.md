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
- This was the initial placeholder stage before `headheadkins` was added.
- It was intended to validate axis ranges and coordinate ordering before custom
  head-head kinematics, TCP, and TWP were implemented.
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
  - initial nominal `C` to `B` offset assumption = `0,0,0`
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
- Added a separate rough visual simulation path:
  - `configs/sim/head_head_5axis/head_head_visual_sim.ini`
  - `configs/sim/head_head_5axis/head_head_vismach.hal`
  - `configs/sim/head_head_5axis/head_head_vismach.py`
- The visual model is approximate and intended for TCP/sign/order debugging.
- It can optionally display a local-only static STL overlay through the
  `HEAD_HEAD_FULL_STL` environment variable.
- Fixed `head_head_vismach.hal` to reuse the existing `Xpos/Ypos/Zpos/Bpos/Cpos`
  sim signals instead of relinking `joint.*.motor-pos-fb`.
- Extended `headheadkins` with HAL outputs for:
  - `tool-offset.{x,y,z}`
  - `tool-vector.{x,y,z}`
- Added `configs/sim/head_head_5axis/tcp_compensation.py` to calculate nominal
  pivot-center `XYZ` compensation for a `B/C` pose change while keeping the
  tool tip fixed.
- Added `configs/sim/head_head_5axis/generate_tcp_test_ngc.py` and a generated
  `tcp_test_sequence.ngc` to exercise the current inverse kinematics as a
  simple TCP validation mode in the visual sim.
- Updated `head_head_visual_sim.ini` to use the sim directory as
  `PROGRAM_PREFIX` and to open `tcp_test_sequence.ngc` by default.
- Confirmed in the visual sim that the fixed-tip TCP validation showed no
  visible drift and the center held position.
- Added `configs/sim/head_head_5axis/generate_tcp_motion_ngc.py` and
  `tcp_motion_sequence.ngc` for moving TCP validation with simultaneous
  `XYZBC` changes.
- Added a first TWP math scaffold:
  - `configs/sim/head_head_5axis/twp_transform.py`
  - `configs/sim/head_head_5axis/generate_twp_test_ngc.py`
  - `configs/sim/head_head_5axis/twp_test_sequence.ngc`
- The current TWP scaffold is an offline plane-local to world transform at
  fixed `B/C`, not yet a production LinuxCNC TWP mode.
# 2026-03-14 - Head-head sim geometry aligned to imported vismach

- Updated the head-head simulation baseline to match the richer vismach model.
- Shared nominal geometry is now:
  - `C->B = (0, 0, -270) mm`
  - `B->tool = (0, +25, -180) mm`
- `head_head_vismach.py` no longer stacks hidden `C->B` and spindle-tip offsets
  on top of the HAL geometry pins.
- `headheadkins`, the math sim HAL, and the vismach HAL now use the same
  geometry semantics.
- The visual sim now also includes:
  - moving-table `Y` rendered with inverted table motion
  - cyan tool-tip alignment post and cross on the table
  - green table centerlines and corner markers for travel checking
- Current simulation `Z` convention:
  - axis `Z` remains the user-facing tool-tip travel `-900 .. 0`
  - internal `JOINT_2` is the `C` pivot-center axis and now uses:
    - `MIN_LIMIT = -630`
    - `MAX_LIMIT = 450`
    - `HOME = 450`
- Added next-phase operator/test notes for TWP development:
  - `configs/sim/head_head_5axis/twp_operator_interface.md`
  - `configs/sim/head_head_5axis/visual_acceptance_checklist.md`
- Added a first prototype TWP state component for the simulation:
  - `configs/sim/head_head_5axis/head_head_twp_state.py`
  - `configs/sim/head_head_5axis/head_head_twp_state.hal`
- The prototype can now:
  - snapshot current tool-tip origin from the sim pose
  - snapshot current `B/C` orientation
  - store plane-normal rotation
  - activate/cancel/reset explicit TWP state
- Added prototype M-code bindings in the sim directory:
  - `M150` origin from current
  - `M151` orientation from current
  - `M152` set both from current
  - `M153` activate
  - `M154` cancel
  - `M155` reset
  - `M156 P...` plane-normal rotation
- Validated live behavior with HAL smoke testing:
  - `M152` stores origin and `B/C` from the current sim pose
  - `M153` sets `headheadtwp.active = TRUE`
  - `M154` returns the component to the defined-but-not-active state
- Added the first live fixed-plane TWP motion path in simulation:
  - remapped `G88.5 P.. Q.. R.. [L..]`
  - reads stored TWP origin, stored `B/C`, and plane basis from `headheadtwp`
  - expands local `UVW` into world `XYZBC`
  - executes a world `G1` while holding the stored TWP orientation

# 2026-03-14 - TWP pause point and next debug step

- The head-head visual simulation is currently running cleanly with:
  - corrected moving-table `Y` visualization
  - cyan alignment post/cross
  - green centerlines and corner markers
  - shared geometry baseline:
    - `C->B = (0, 0, -270) mm`
    - `B->tool = (0, +25, -180) mm`
- User validated:
  - fixed-tip TCP check: no visible drift
  - moving TCP check: looks correct
  - updated vismach geometry: looks correct
- The current open issue is in the prototype TWP state demo flow around the
  boundary between the positioning move and the first TWP state commands.
- The demo program was reduced to the minimum baseline path:
  - `G0 X1500 Y850 Z-600 B45 C90`
  - `G4 P0.2`
  - `M152`
  - `M153`
  - `M0`
  - `M154`
  - `M155`
- `M156 P0.0` was removed from the baseline demo because:
  - normal rotation already defaults to `0.0`
  - it added another possible failure point without helping the first test
- The most likely remaining issue is not kinematics geometry. It is the runtime
  behavior of the prototype external M-code path, specifically separating:
  - `M152` pose snapshot
  - `M153` activation
- Next resume step:
  1. In MDI, run:
     - `G0 X1500 Y850 Z-600 B45 C90`
     - `G4 P0.2`
     - `M152`
  2. Check:
     - `halcmd getp headheadtwp.state_code`
     - `halcmd getp headheadtwp.valid`
     - `halcmd getp headheadtwp.twp_origin_x`
     - `halcmd getp headheadtwp.twp_origin_y`
     - `halcmd getp headheadtwp.twp_origin_z`
     - `halcmd getp headheadtwp.twp_b_angle`
     - `halcmd getp headheadtwp.twp_c_angle`
  3. Then run `M153`
  4. Check:
     - `halcmd getp headheadtwp.active`
     - `halcmd getp headheadtwp.state_code`
- Expected values:
  - after `M152`:
    - `state_code = 2`
    - `valid = TRUE`
  - after `M153`:
    - `active = TRUE`
    - `state_code = 3`
- Important environment note:
  - previous HAL smoke testing used `halrun -U`, which resets the active
    realtime session
  - avoid that while preserving the current desktop sim session
- Local machine backup trees remain intentionally untouched and untracked:
  - `configs/5th_axis/`
  - `configs/5th_axis _SSI/`

# 2026-03-16 - Post-power-loss TWP recheck

- Resumed the saved head-head visual simulation work after the machine power
  failure and re-ran the recorded TWP debug sequence on
  `head-head-kinematics-rnd-pushable`.
- LinuxCNC visual sim still starts, but the vismach window continues to emit
  the previously seen OpenGL redraw warning:
  - `GLError 1285` (`out of memory`) in the Tk/OpenGL HUD path
- That OpenGL issue did not block the TWP HAL/component checks.
- Verified manual MDI sequence:
  - `G0 X1500 Y850 Z-600 B45 C90`
  - `G4 P0.2`
  - `M152`
  - check pins
  - `M153`
- Verified results after `M152`:
  - `headheadtwp.state_code = 2`
  - `headheadtwp.valid = TRUE`
  - `headheadtwp.twp_origin = (1500, 850, -600)`
  - `headheadtwp.twp_b_angle = 45`
  - `headheadtwp.twp_c_angle = 90`
- Verified results after `M153`:
  - `headheadtwp.active = TRUE`
  - `headheadtwp.state_code = 3`
- Also re-ran the reduced demo program:
  - `configs/sim/head_head_5axis/twp_state_demo.ngc`
- Current observed behavior of the demo program:
  - runs to the programmed `M0`
  - holds the expected active TWP state at the pause
  - resumes cleanly
  - `M154` and `M155` clear the state back to:
    - `active = FALSE`
    - `valid = FALSE`
    - `state_code = 0`
- Current conclusion:
  - the March 14 suspected boundary issue between the positioning move and the
    first TWP state commands does not reproduce in the current tree
  - no code change was required for this recheck
  - the next meaningful development step is beyond state capture/activation and
    should focus on the actual live TWP motion/remap path

# 2026-03-16 - Live TWP remap ordering fix

- Continued from the post-power-loss recheck and exercised the live TWP remap
  path with:
  - `configs/sim/head_head_5axis/twp_live_demo.ngc`
- Initial finding before the fix:
  - running the demo in `AUTO` failed immediately with:
    - `TWP move requested with no valid TWP definition`
- Root cause:
  - `G88.5` was reading `headheadtwp.*` HAL state during interpreter read-ahead
  - earlier `M152` / `M153` side effects were not yet synchronized into the
    interpreter-visible runtime state
  - this was an execution-order / queue-buster problem, not a geometry problem
- Fix applied:
  - updated `configs/sim/head_head_5axis/python/remap.py`
  - changed `twp_move()` into a Python generator remap
  - added an initial `yield INTERP_EXECUTE_FINISH` before reading any
    `headheadtwp.*` pins
  - this forces a task/interpreter sync so prior `M152` / `M153` effects are
    visible before the remap validates and expands the stored plane move
- Verified after restart:
  - `twp_live_demo.ngc` now runs in `AUTO` to each programmed `M0`
  - stored TWP state remains active through the plane moves
  - the transformed world positions match the helper math from
    `twp_transform.py`
- Verified demo positions:
  - `G88.5 P150 Q0 R0` -> `XYZ = (1500.000, 956.066, -706.066)`
  - `G88.5 P150 Q100 R0` -> `XYZ = (1400.000, 956.066, -706.066)`
  - `G88.5 P150 Q100 R50` -> `XYZ = (1400.000, 991.421, -670.711)`
- End-of-demo state remains correct:
  - `M154` / `M155` clear the prototype TWP state back to:
    - `active = FALSE`
    - `valid = FALSE`
    - `state_code = 0`
- Current next step:
  - extend the prototype from fixed stored-plane linear moves toward broader
    TWP behavior and operator workflow, now that the remap ordering issue is
    resolved
  - keep the new regression passing:
    - `tests/remap/head-head-twp-queuebuster`
    - covers runtime `M152` / `M153` plus `G88.5` ordering without GUI vismach

# 2026-03-17 - Runtime regression extended with M156 coverage

- Continued from the queue-buster regression and explored whether the next
  prototype step could remap ordinary `G0` / `G1` into stored-plane TWP
  motion.
- Important LinuxCNC constraint confirmed from local remap documentation:
  - existing builtin remaps are supported for `T`, `M`, `S`, and `F`
  - ordinary `G0` / `G1` are not supported as redefined builtins in this
    remap path
  - result:
    - a `G0` / `G1` modal-TWP implementation cannot be carried by the current
      Python remap mechanism alone
- Action taken:
  - dropped the attempted `G0` / `G1` remap path before keeping any of it
  - kept the working explicit `G88.5` remap as the supported live-motion path
  - extended the headless runtime regression instead
- Regression updates:
  - test directory:
    - `tests/remap/head-head-twp-queuebuster`
  - added local `M156`
  - extended `test.ngc` and `test-ui.py` to cover both:
    - baseline `G88.5` queue-buster behavior after `M152` / `M153`
    - `M156 P90.0` plane-normal rotation before the same `G88.5` sequence
- Verified headless run:
  - command:
    - `scripts/rip-environment linuxcnc -r test.ini`
  - result:
    - `pause 1 ok`
    - `pause 2 ok`
    - `pause 3 ok`
    - `pause 4 ok`
    - `pause 5 ok`
    - `pause 6 ok`
    - `pause 7 ok`
    - `pause 8 ok`
    - `program complete`
- Verified rotated-plane positions for `M156 P90.0`:
  - `G88.5 P150 Q0 R0` -> `XYZ = (1325.000, 722.721, -997.279)`
  - `G88.5 P150 Q100 R0` -> `XYZ = (1325.000, 652.010, -926.569)`
  - `G88.5 P150 Q100 R50` -> `XYZ = (1325.000, 687.365, -891.213)`
- Verified state semantics:
  - active stored TWP state remains `state_code = 3` through the rotated moves
  - `twp_normal_rotation = 90.0` during the rotated sequence
  - final `M154` / `M155` returns:
    - `active = FALSE`
    - `valid = FALSE`
    - `state_code = 0`
    - `twp_normal_rotation = 0.0`
- Recommended next development step:
  - if operator workflow must become more natural than explicit `G88.5`, the
    next implementation path likely needs either:
    - a wider helper-code family built on unallocated G-codes, or
    - interpreter/core work beyond the current Python remap mechanism

# 2026-03-17 - Fanuc-like controller contract written down

- Direction clarified for the real machine:
  - target operator behavior is Fanuc-like
  - exact Fanuc syntax is not mandatory if it makes LinuxCNC integration worse
  - the important requirement is standard-looking posted code and normal
    `G0/G1` behavior while TWP is active
- Added controller/post behavior spec:
  - `configs/sim/head_head_5axis/fanuc_like_twp_tcpc_contract.md`
- Key decision captured there:
  - TCPC and TWP are controller modes
  - active TWP must reinterpret ordinary `G0/G1`
  - explicit `G88.5` remains only a prototype/math-validation path
  - Fusion post work should target the controller contract, not the current
    prototype remap syntax
- Cross-linked the new contract from:
  - `configs/sim/head_head_5axis/twp_operator_interface.md`
  - `configs/sim/head_head_5axis/README.md`
- Recommended implementation path from here:
  - extend `headheadkins` with explicit TCPC/TWP mode inputs
  - prove ordinary `G0/G1` behavior in sim/runtime tests
  - only then freeze the final posted syntax

# 2026-03-17 - First headheadkins TWP-mode attempt is exploratory only

- Started the first kinematics-level implementation attempt for the Fanuc-like
  target:
  - added exploratory TWP-mode inputs to `src/emc/kinematics/headheadkins.c`
  - added exploratory `motion_enabled` state to
    `configs/sim/head_head_5axis/head_head_twp_state.py`
  - added exploratory `G68.2` / `G69` remap hooks for mode toggle
  - added a new headless regression scaffold:
    - `tests/kinematics/head-head-twp-g0g1`
- Important current status:
  - this work is **not validated yet**
  - the new kinematics-level path currently fails before the first programmed
    pause in the headless test
  - symptom:
    - the initial world-mode move to `G0 X1500 Y850 Z-600 B45 C90` does not
      settle to the expected pose in the new `headheadkins` test harness
  - conclusion:
    - there is still a reciprocity / transition issue in the exploratory
      `headheadkins` TWP-mode implementation
    - it is not ready to treat as the new controller path yet
- Safety check performed:
  - reran the existing explicit prototype regression:
    - `tests/remap/head-head-twp-queuebuster`
  - result:
    - still passes through `pause 8 ok` and `program complete`
  - meaning:
    - the existing `G88.5` + `M156` prototype path still works
    - the new failure is isolated to the exploratory kinematics-level path
- Recommended next debug step:
  - isolate the `headheadkins` world-mode mismatch first
  - do **not** assume the new `tests/kinematics/head-head-twp-g0g1` path is
    authoritative until the initial non-TWP move is correct

# 2026-03-17 - Sample-data `G0/G1` TWP path now passes in headheadkins

- Continued the kinematics-level sample-data path in:
  - `src/emc/kinematics/headheadkins.c`
  - `configs/sim/head_head_5axis/python/remap.py`
  - `configs/sim/head_head_5axis/head_head_twp_state.py`
  - `tests/kinematics/head-head-twp-g0g1`
- Current status:
  - the new `headheadkins`-based sample-data regression now passes
  - active TWP mode drives ordinary `G0/G1` moves in the stored tilted plane
  - `G69` now returns control to normal world-coordinate motion without moving
    the tool tip
- Important implementation detail:
  - `G68.2` and `G69` currently use Python remap hooks only as mode toggles
  - the actual local-to-world / world-to-local interpretation is in
    `headheadkins`
  - this keeps the motion behavior on the kinematics side while still letting
    the sim exercise Fanuc-like mode changes with sample data
- Cleaned up the remap transition logic:
  - refactored the temporary motion-origin math into a shared helper in
    `configs/sim/head_head_5axis/python/remap.py`
  - removed the temporary `G68.2 enable ...` / `G69 disable ...` debug prints
  - documented why the enable/disable remaps adjust
    `headheadkins.twp-motion-origin.*` during the transition
- Strengthened the headless regression:
  - `tests/kinematics/head-head-twp-g0g1/test.ngc` now pauses immediately after
    each `G69`
  - `tests/kinematics/head-head-twp-g0g1/test-ui.py` now proves:
    - after `G69`, `motion_enabled = FALSE`
    - `active = TRUE`, `valid = TRUE`, `state_code = 3` still remain until
      `M154` / `M155`
    - the world tool-tip position is unchanged at the instant TWP motion is
      disabled
    - the subsequent non-TWP `G0` world move still lands at the expected
      sample-data pose
- Verified with:
  - `tests/kinematics/head-head-twp-g0g1`
    - `/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini`
    - result:
      - `pause 1 ok` through `pause 14 ok`
      - `program complete`
  - `tests/remap/head-head-twp-queuebuster`
    - reran after the remap cleanup to confirm no regression to the explicit
      prototype path
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`
- Practical conclusion:
  - with sample data, the branch now has a working proof that ordinary
    `G0/G1` can run in active TWP mode for the head-head machine model
  - the next step should stay focused on controller semantics and operator/post
    contract details, not Fusion integration yet

# 2026-03-17 - Visual sim launch error traced to vismach HUD

- The LinuxCNC visual sim launch error dialogs were not caused by the new TWP
  remap or `headheadkins` path.
- Captured traceback from `/tmp/linuxcnc.debug.*`:
  - `OpenGL.error.GLError`
  - `err = 1285`
  - `description = b'out of memory'`
  - raised in `lib/python/vismach.py` from `Hud.draw()` at `glOrtho(...)`
- Local fix applied in:
  - `configs/sim/head_head_5axis/head_head_vismach.py`
- Behavior change:
  - the vismach HUD overlay is now disabled by default
  - it can still be enabled explicitly with:
    - `HEAD_HEAD_ENABLE_HUD=1`
- Verification:
  - relaunched `configs/sim/head_head_5axis/head_head_visual_sim.ini`
  - startup reached normal Axis notes with no Python/OpenGL traceback in the
    terminal
- Conclusion:
  - current launch issue was a vismach/OpenGL frontend problem
  - it is separate from the TWP `G0/G1` sample-data path

# 2026-03-17 - Explicit TCPC mode added to the sample-data controller path

- Added explicit TCPC controller state to:
  - `configs/sim/head_head_5axis/head_head_twp_state.py`
- New state semantics:
  - `headheadtwp.tcpc_enabled` is now an explicit output pin
  - new command pins:
    - `cmd_enable_tcpc`
    - `cmd_disable_tcpc`
  - disabling TCPC forces `motion_enabled = FALSE`
- Updated TWP mode enable behavior:
  - `configs/sim/head_head_5axis/python/remap.py`
  - `G68.2` now rejects TWP motion enable unless TCPC mode is already enabled
  - current interpreter error text:
    - `TWP mode enable requested while TCPC mode is not enabled`
- Added temporary sample-data TCPC wrappers:
  - `configs/sim/head_head_5axis/M170`
  - `configs/sim/head_head_5axis/M171`
- Important syntax note:
  - first attempt used `M430` / `M431`
  - LinuxCNC rejected those with:
    - `M-code greater than 199`
  - switched the sample-data wrapper pair to valid user M-codes:
    - `M170` = TCPC on
    - `M171` = TCPC off
  - this still matches the Fanuc-like behavior goal even though the final
    machine syntax may change later
- Updated positive sample-data regression:
  - `tests/kinematics/head-head-twp-g0g1`
  - program now runs:
    - world pose
    - `M170`
    - define/activate TWP
    - ordinary `G0/G1`
    - `G69`
    - `M154` / `M155`
    - `M171`
  - assertions now also verify `tcpc_enabled`
- Added negative regression:
  - `tests/kinematics/head-head-twp-requires-tcpc`
  - proves that `G68.2` fails if TCPC has not been enabled first
- Verified with:
  - `tests/kinematics/head-head-twp-g0g1`
    - result:
      - `pause 1 ok` through `pause 16 ok`
      - `program complete`
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - expected interpreter error observed:
        - `TWP mode enable requested while TCPC mode is not enabled`
  - `tests/remap/head-head-twp-queuebuster`
    - rerun to confirm the older explicit `G88.5` prototype still works
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`
- Practical conclusion:
  - the sample-data controller path now has explicit mode sequencing:
    - TCPC on
    - TWP define / activate
    - ordinary `G0/G1`
    - TWP off
    - TCPC off
  - that is much closer to the intended Fanuc-like operator model

# 2026-03-17 - Startup default switched to TCPC-on

- Direction agreed:
  - for this head-head machine, operator startup should default to TCPC on
  - posted/sample programs should still use explicit TCPC on/off commands
  - this keeps the safer local shop behavior while preserving Fanuc-like file
    semantics
- Implemented in:
  - `configs/sim/head_head_5axis/head_head_twp_state.py`
- Behavior change:
  - `headheadtwp.tcpc_enabled` now starts `TRUE` when the state component loads
  - explicit sample-data wrappers remain:
    - `M170` = TCPC on
    - `M171` = TCPC off
- Regression updates:
  - `tests/kinematics/head-head-twp-g0g1`
    - now expects TCPC already on at startup
    - still keeps the explicit `M170` / `M171` posted-workflow pattern
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - now explicitly runs `M171` first
    - then proves `G68.2` is rejected with TCPC off
- Verified with:
  - `tests/kinematics/head-head-twp-g0g1`
    - result:
      - `pause 1 ok` through `pause 16 ok`
      - `program complete`
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - expected interpreter error observed:
        - `TWP mode enable requested while TCPC mode is not enabled`
  - `tests/remap/head-head-twp-queuebuster`
    - rerun after the startup-default change
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`

# 2026-03-17 - TCPC post target switched to `G43.4` / `G49.1`

- Chosen machine-facing TCPC syntax for the post target:
  - `G43.4` = TCPC on
  - `G49.1` = TCPC off
- Reasoning:
  - `G43.4` is close to Fanuc intent and available as an unallocated remapped
    G-code in this LinuxCNC tree
  - built-in `G49` cannot be repurposed because LinuxCNC already uses it for
    tool-length cancellation
  - `G49.1` keeps the cancel intent recognizable while avoiding the `G49`
    conflict
- Implemented remap entry points in:
  - `configs/sim/head_head_5axis/python/remap.py`
  - `configs/sim/head_head_5axis/head_head_visual_sim.ini`
  - `configs/sim/head_head_5axis/head_head_math_sim.ini`
  - `tests/kinematics/head-head-twp-g0g1/test.ini`
  - `tests/kinematics/head-head-twp-requires-tcpc/test.ini`
- Updated sample-data programs:
  - positive runtime path now uses `G43.4` / `G49.1`
  - negative runtime path now uses `G49.1` to force TCPC off before proving the
    `G68.2` rejection
- Important LinuxCNC quirk discovered:
  - although the remap docs discuss modal groups broadly, this branch only
    accepts `modalgroup=1` for remapped G-codes
  - initial attempt to place `G43.4` / `G49.1` in modal group 8 failed during
    interpreter initialization
  - switched both remaps to `modalgroup=1`
- Verified with:
  - `tests/kinematics/head-head-twp-g0g1`
    - result:
      - `pause 1 ok` through `pause 16 ok`
      - `program complete`
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - expected interpreter error observed:
        - `TWP mode enable requested while TCPC mode is not enabled`
  - `tests/remap/head-head-twp-queuebuster`
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`

2026-03-18 Probe Basic 5-axis calibration workflow:

- Expanded the head-head Probe Basic calibration tab into a shop-facing wizard:
  - added `Probe Qual` step for the OMP40-style probe and 50 mm ring
  - setup/notes now reference the 20 mm sphere on the tall 45 degree stand and
    the granite square
  - summary now includes measurement metadata as well as calibration values
  - draft save/reload now persists the metadata fields too
- Added a first written machine procedure at:
  - `configs/sim/head_head_5axis/five_axis_calibration_procedure.md`
- Added runnable calibration sample programs:
  - `configs/sim/head_head_5axis/calibration_sphere_capture_sequence.ngc`
  - `configs/sim/head_head_5axis/calibration_bc_alignment_check.ngc`
  - `configs/sim/head_head_5axis/calibration_tcpc_fixed_tip_check.ngc`
  - `configs/sim/head_head_5axis/calibration_tcpc_motion_check.ngc`
- Updated the Probe Basic wizard verify page to load those programs directly.
- Relaunched Probe Basic and verified the updated wizard renders with the new
  `Probe Qual` step and revised verification controls.
- Observed one recurring QtPyVCP shutdown-only traceback during restart:
  - `RuntimeError: Invalid operation on closed HAL component`
  - this appears during restart/exit cleanup, not during normal wizard use.

2026-03-18 calibration drift-map workflow:

- Added `Sphere Map` to the Probe Basic 5-axis calibration wizard.
- Operators can now:
  - run `calibration_sphere_capture_sequence.ngc`
  - probe the 20 mm sphere center at standard B/C poses
  - capture current XYZBC into the wizard for each pose
  - see a first-pass drift map before changing offsets
- The written procedure now uses this order:
  - probe qualification
  - basic B/C alignment
  - sphere-center drift map
  - rotary zero cleanup
  - fixed-tip TCPC check
  - moving 5-axis TCP check
- The drift map is currently a guided operator aid, not an automatic solver:
  - opposite-sign paired drift suggests rotary-zero cleanup first
  - common residual drift suggests geometry correction next

2026-03-18 Probe Basic layout and vismach STL intake:

- Fixed the head-head Probe Basic calibration tab so it no longer distorts the
  base Probe Basic layout:
  - the `5 AXIS CALIBRATION` tab now uses its own scroll area
  - the step pages are now hosted in a `QStackedWidget`
  - full-screen startup was restored after the tab stopped forcing the main
    layout taller than the stock Probe Basic Mill ATC Metric screen
- Patched the local QtPyVCP HAL wrapper shutdown path:
  - `dev/qtpyvcp/src/qtpyvcp/hal/hal_qlib.py`
  - suppresses the noisy restart-time traceback:
    - `RuntimeError: Invalid operation on closed HAL component`
  - this was a shutdown/restart cleanup race, not a calibration-wizard bug
- New reduced STL files were dropped in:
  - `/home/cnc5/Vismach/reduced`
  - files:
    - `Frame_reduced.stl`
    - `Y_Axis_Table_reduced.stl`
    - `X_Axis_Frame_reduced.stl`
    - `Z_Axis_Frame_reduced.stl`
    - `C_Axis_Body_reduced.stl`
    - `B_Axis_Body_reduced.stl`
    - `Spindle_reduced.stl`
- STL assessment:
  - all seven files are structurally valid binary STL files
  - the file split matches the current moving vismach groups well
  - triangle counts are reasonable for vismach prototyping:
    - frame: `15988`
    - table: `12306`
    - X frame: `4104`
    - Z frame: `1474`
    - C body: `2915`
    - B body: `130`
    - spindle: `488`
  - current blocker:
    - `head_head_vismach.py` uses `AsciiSTL(...)`
    - LinuxCNC `vismach.py` in this tree exposes `AsciiSTL`, not a binary STL
      loader
  - conclusion:
    - the meshes look usable for vismach after conversion to ASCII STL or after
      adding a binary STL loader path
    - they are not directly drop-in with the current `head_head_vismach.py`
      implementation as-is
- Bounding-box spot check suggests the exports share a common assembly-space
  origin and plausible machine-scale dimensions, so the next integration risk is
  transform/pivot alignment rather than gross export corruption.

# 2026-03-18 - TWP now blocks tool length and tool changes

- Added interpreter-level TWP-active guards in:
  - `src/emc/rs274ngc/interp_convert.cc`
- Current behavior while `headheadtwp.active` is true:
  - reject tool length compensation changes:
    - `G43`
    - `G43.1`
    - `G43.2`
    - `G49`
  - reject tool-state changes:
    - `M6`
    - `M61`
- This keeps the tool tip and stored TWP frame from changing underneath an
  active tilted plane, which matches the intended Fanuc-like safety model for
  the head-head machine.
- Added runtime regressions:
  - `tests/kinematics/head-head-twp-reject-tool-length`
    - proves `G43.1 Z...` is rejected during active TWP
  - `tests/kinematics/head-head-twp-reject-tool-change`
    - proves `T1 M6` is rejected during active TWP
- Verified with:
  - `tests/kinematics/head-head-twp-g0g1`
    - result:
      - `pause 1 ok` through `pause 14 ok`
      - `program complete`
  - `tests/remap/head-head-twp-queuebuster`
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`

# 2026-03-18 - Reduced STL vismach model accepted as new baseline

- Backed up the pre-STL vismach script at:
  - `configs/sim/head_head_5axis/head_head_vismach.py.pre_stl_backup`
- Switched the head-head visual sim to use the reduced STL part set in:
  - `/home/cnc5/Vismach/reduced`
- Added a local binary STL loader to:
  - `configs/sim/head_head_5axis/head_head_vismach.py`
- Current reduced STL parts in the live motion chain are:
  - `Frame_reduced.stl`
  - `Y_Axis_Table_reduced.stl`
  - `X_Axis_Frame_reduced.stl`
  - `Z_Axis_Frame_reduced.stl`
  - `C_Axis_Body_reduced.stl`
  - `B_Axis_Body_reduced.stl`
  - `Spindle_reduced.stl`
- The user confirmed the reduced STL exports are already aligned in correct home
  position for the machine, so the vismach model now treats those meshes as the
  true home assembly rather than as a loose overlay.
- Measured the spindle mesh tip directly from the binary STL and used it as the
  first-pass nominal `B->tool` reference relative to the B pivot:
  - STL-derived spindle tip:
    - approximately `(2.26, -99.72, -305.46)` mm from the B pivot
  - current nominal geometry now set to:
    - `B_TO_SPINDLE_X = 2.0`
    - `B_TO_SPINDLE_Y = -99.565`
    - `B_TO_SPINDLE_Z = -305.517`
- Applied that same first-pass nominal `B->tool` vector in:
  - `configs/sim/head_head_5axis/geometry_baseline.ini`
  - `configs/sim/head_head_5axis/head_head_math_sim.hal`
  - `configs/sim/head_head_5axis/head_head_vismach.hal`
- Adjusted the vismach tooltip marker so the pink trace is anchored at the
  bottom of the yellow TT marker instead of the top edge.
- Compensated the reduced STL Z assembly for the current joint-home offset so
  the visual Z no longer lifts unrealistically high during LinuxCNC homing.
- User review of the reduced STL model:
  - overall alignment is now close enough to use as the machine-side reference
  - current visual state is good enough to move onto the real machine
- Important follow-up:
  - the live head-head sim now uses STL-derived nominal geometry
  - the existing headless TCPC/TWP regression harnesses still use the older
    nominal `B->tool = (0.0, 25.0, -180.0)` baseline in their local
    `core_sim.hal` files
  - those harnesses should be updated deliberately in a separate pass once the
    real machine calibration direction is confirmed

# 2026-03-18 - Head-head machine-side baseline moved back toward real Y offset

- User confirmed the reduced STL vismach is a good representation of the real
  machine overall, but the spindle placement inside that STL assembly should not
  drive the machine-side `B->tool.y` nominal toward `-99` mm.
- Updated the current machine-side nominal geometry to keep the B-to-tool Y
  offset near the real machine direction:
  - `B_TO_SPINDLE_X = 2.0`
  - `B_TO_SPINDLE_Y = -22.0`
  - `B_TO_SPINDLE_Z = -305.517`
- Synced that baseline through the live sim and TWP state files:
  - `configs/sim/head_head_5axis/geometry_baseline.ini`
  - `configs/sim/head_head_5axis/head_head_math_sim.hal`
  - `configs/sim/head_head_5axis/head_head_vismach.hal`
  - `configs/sim/head_head_5axis/head_head_twp_state.hal`
- Kept the STL spindle correction as a visual-only vismach adjustment in:
  - `configs/sim/head_head_5axis/head_head_vismach.py`
- Synced the headless head-head test harnesses to the same baseline by updating:
  - all `tests/kinematics/head-head-*/core_sim.hal`
  - `tests/remap/head-head-twp-queuebuster/core_sim.hal`
- Updated the remap queuebuster expected world positions in:
  - `tests/remap/head-head-twp-queuebuster/test-ui.py`
- Verified against the `B->tool.y = -22.0` baseline:
  - `tests/kinematics/head-head-twp-g0g1`
    - result:
      - `pause 1 ok` through `pause 14 ok`
      - `program complete`
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - expected error observed:
        - `TWP mode enable requested while TCPC mode is not enabled`
  - `tests/remap/head-head-twp-queuebuster`
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`
    - updated queuebuster world positions now reflect the current baseline:
      - `UVW=(150,0,0)` -> `XYZ=(1522.000, 741.447, -1193.513)`
      - `UVW=(150,100,0)` -> `XYZ=(1422.000, 741.447, -1193.513)`
      - `UVW=(150,100,50)` -> `XYZ=(1422.000, 776.802, -1158.158)`

# 2026-03-18 - Live AXIS/vismach sample programs checked against STL model

- Relaunched the head-head visual sim with the reduced STL model and current
  `B->tool.y = -22.0` baseline.
- Used the live AXIS instance to run the fresh manual demo programs without
  forcing a complete home cycle, since:
  - `NO_FORCE_HOMING = 1` is already set in the visual sim INI
  - JOINT_2 / Z currently does not report homed cleanly through the live AXIS
    API path even though there is no error reported
- Fresh TCPC sample program checked in the live visual sim:
  - `configs/sim/head_head_5axis/tcp_tcpc_fresh_demo.ngc`
  - observed pause positions:
    - pause 1: `(1500.0, 850.0, -600.0, 0.0, 0.0)`
    - pause 2: `(1500.0, 850.0, -600.0, 0.0, 0.0)` (`G43.4` enabled)
    - pause 3: `(1500.0, 850.0, -600.0, 45.0, 0.0)`
    - pause 4: `(1500.0, 850.0, -600.0, 45.0, 90.0)`
    - pause 5: `(1500.0, 850.0, -600.0, -30.0, 180.0)`
    - pause 6: `(1600.0, 850.0, -600.0, -30.0, 180.0)`
    - pause 7: `(1600.0, 950.0, -560.0, 20.0, 180.0)`
    - pause 8: `(1500.0, 850.0, -600.0, 0.0, 0.0)`
    - pause 9: `(1500.0, 850.0, -600.0, 0.0, 0.0)` (`G49.1` cancelled)
  - program completed cleanly at:
    - `(1500.0, 850.0, -600.0, 0.0, 0.0)`
- Fresh TWP sample program checked in the live visual sim:
  - `configs/sim/head_head_5axis/twp_g68_2_fresh_demo.ngc`
  - observed pause positions:
    - pause 1: `(1500.0, 850.0, -600.0, 45.0, 90.0)`
    - pause 2: `(1500.0, 850.0, -600.0, 45.0, 90.0)` (`G43.4` enabled)
    - pause 3: `(1500.0, 850.0, -600.0, 45.0, 90.0)` (`G68.2` active)
    - pause 4: `(1600.0, 850.0, -600.0, 45.0, 90.0)` (local +U)
    - pause 5: `(1600.0, 970.0, -600.0, 45.0, 90.0)` (local +V)
    - pause 6: `(1600.0, 970.0, -560.0, 45.0, 90.0)` (local +W)
    - pause 7: `(1500.0, 850.0, -600.0, 45.0, 90.0)` (return local origin)
  - program completed cleanly at:
    - `(1500.0, 850.0, -600.0, 45.0, 90.0)`
- Current conclusion:
  - the reduced STL vismach is now good enough to use as the visual reference
    while checking TCP and TWP behavior
  - the live manual sample programs are behaving coherently on the current
    machine-side baseline

# 2026-03-18 - Added first practical machine TCP/TWP verification package

- Added an operator-facing machine verification package built around the actual
  shop tooling:
  - qualified OMP40-style wireless probe
  - 20 mm sphere on the tall 45 degree stand
  - granite square
- New machine-side programs:
  - `configs/sim/head_head_5axis/machine_tcp_fixed_tip_probe_check.ngc`
  - `configs/sim/head_head_5axis/machine_tcp_motion_probe_check.ngc`
  - `configs/sim/head_head_5axis/machine_twp_granite_square_check.ngc`
- New operator reference:
  - `configs/sim/head_head_5axis/machine_tcp_twp_verification_sequence.md`
- Updated the broader calibration references to include that package:
  - `configs/sim/head_head_5axis/five_axis_calibration_procedure.md`
  - `configs/sim/head_head_5axis/README.md`
- Updated the Probe Basic `5 AXIS CALIBRATION` verify page so operators can load
  the new machine-side TCP/TWP check programs directly from the wizard.
- Extended the Probe Basic verify page with explicit machine verification log
  fields for:
  - fixed-tip TCP result / first drift pose / likely cause
  - moving TCP result / first drift pose / likely cause
  - TWP granite-square result / first drift pose / likely cause
- Those fields are saved in the wizard draft and included in the generated
  summary output.
- Verified the updated wizard Python loads cleanly with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic successfully after the update.
- Current intent:
  - use the reduced STL model and the live sim as the visual reference
  - use the new machine-side programs as the first structured on-machine TCP/TWP
    proof sequence before solving final calibration numbers

# 2026-03-19 - Added first-step B/C rotary zeroing workflow

- Added a dedicated first-step rotary zeroing package to assist the home / zero
  alignment of the B and C axes before TCP work:
  - `configs/sim/head_head_5axis/machine_rotary_zeroing_sequence.md`
  - `configs/sim/head_head_5axis/machine_b_zero_alignment_check.ngc`
  - `configs/sim/head_head_5axis/machine_c_zero_alignment_check.ngc`
- This is aimed at the new direct-output rotary encoders:
  - get the zero reference right first
  - then rely on the encoder feedback for accurate repeatable rotary positioning
- Updated the Probe Basic `Rotary Zero Offsets` page to include:
  - direct load buttons for the B-zero and C-zero programs
  - rotary zeroing log fields for:
    - B zero reference
    - B zero observed error
    - C zero reference
    - C zero observed error
    - zeroing pass result
- Updated:
  - `configs/sim/head_head_5axis/five_axis_calibration_procedure.md`
  - `configs/sim/head_head_5axis/README.md`
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified the wizard still syntax-checks and relaunched Probe Basic after the update.

# 2026-03-19 - Added first-pass solve assistant to the sphere map

- Extended the Probe Basic calibration wizard so the `Sphere Map` page now
  computes a first-pass recommended next adjustment from the captured drift
  pattern.
- Current solve-assistant outputs:
  - suggested first adjustment:
    - `B_ZERO_OFFSET`
    - `C_ZERO_OFFSET`
    - `cal-c-to-b`
    - `cal-b-to-tool`
  - supporting drift breakdown:
    - B paired antisymmetric drift
    - C paired antisymmetric drift
    - B common residual
    - C common residual
    - mixed B/C residual
    - overall common residual
- The recommendation block now also gives a sign-guided first trial:
  - small positive/negative test changes are evaluated against the current
    sphere-map residual
  - the wizard suggests the first small move to try, for example:
    - positive or negative `B_ZERO_OFFSET`
    - positive or negative `C_ZERO_OFFSET`
    - first likely axis/sign for `cal-c-to-b`
    - first likely axis/sign for `cal-b-to-tool`
- The generated summary now also includes the recommended-next-adjustment block
  so the operator record carries both the raw capture and the suggested first
  move.
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the solve assistant is live.

# 2026-03-20 - Added machine bring-up checklist to the calibration workflow

- Added a dedicated operator bring-up reference:
  - `configs/sim/head_head_5axis/machine_bringup_checklist.md`
- Extended the Probe Basic calibration wizard `Setup` page to include:
  - direct load buttons for:
    - B/C alignment
    - B zero check
    - C zero check
    - machine fixed-tip TCP check
    - machine TWP granite-square check
  - a machine bring-up checklist log with staged status fields for:
    - power/reset
    - home/reference
    - probe qualification
    - sphere setup
    - B/C zeroing
    - sphere map capture
    - fixed-tip TCP
    - moving TCP
    - TWP check
    - overall bring-up state
- Updated the generated summary so the bring-up checklist status is carried in
  the operator output along with the calibration values.
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
  - `configs/sim/head_head_5axis/five_axis_calibration_procedure.md`
  - `configs/sim/head_head_5axis/README.md`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the bring-up checklist is live.

# 2026-03-20 - Added bring-up recovery guidance to the Verify page

- Extended the Probe Basic `Verify` page with a read-only recovery guidance
  block that points the operator back to the first page to revisit when a
  bring-up stage is marked `fail` or `hold`.
- Current guidance logic:
  - fixed-tip TCP failure -> return first to `Rotary Zero` and `Sphere Map`
  - moving TCP failure -> return first to `B To Tool` and `C To B`
  - TWP failure -> verify the granite-square setup, then re-check fixed-tip TCP
  - rotary zero blocker -> return to the dedicated B/C zero checks
  - sphere-map blocker -> return to `Probe Qual` and `Sphere Map`
  - all key stages passed -> keep the summary as the machine record
- The same recovery guidance is now included in the generated summary block so
  the operator handoff carries both the calibration values and the current next
  action if a stage failed.
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the Verify page guidance is live.

# 2026-03-20 - Added pose-by-pose acceptance logging for machine verification

- Extended the Probe Basic `Verify` page so the operator can log each machine
  verification pose explicitly instead of relying only on a free-form drift
  note.
- Added dedicated pose-status groups for:
  - fixed-tip TCP:
    - `B0/C0` entry
    - `B20/C0`
    - `B45/C0`
    - `B45/C90`
    - `B0/C180`
    - `B-30/C-90`
    - return to `B0/C0`
  - moving TCP:
    - start pose
    - each programmed XYZBC move
    - return to start
  - TWP:
    - tilted start
    - local `+U`
    - local `+V`
    - local `+W`
    - return to local origin
- The generated summary now:
  - records compact pose-status lines for fixed-tip TCP, moving TCP, and TWP
  - infers the first drift pose from the first `fail` or `hold` pose if the
    operator did not fill the explicit first-drift field manually
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the pose logging is live.

# 2026-03-20 - Added pose-specific follow-up guidance to machine verification

- Extended the Probe Basic `Verify` page so the recovery guidance now uses the
  first flagged machine verification pose to narrow the next likely adjustment.
- Current pose-specific hints include:
  - B-dominant fixed-tip failures -> look at `B_ZERO_OFFSET` first
  - C-heavy or mixed fixed-tip failures -> look at `C_ZERO_OFFSET` and
    C-related common residual first
  - first moving-TCP failure on the early B-dominant move -> re-check
    `cal-b-to-tool` and B-related geometry first
  - first moving-TCP failure on the C-heavy or mixed moves -> re-check
    `cal-c-to-b` / C-related geometry first
  - TWP `+U/+V/+W` failures -> distinguish plane-entry, plane-orientation, and
    plane-normal follow-up checks
- The generated summary now also includes a `Pose-based follow-up` block so the
  operator handoff carries the likely next adjustment area from the first
  failed pose.
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the pose-specific guidance is
  live.

# 2026-03-20 - Added trial-change plans to the calibration wizard

- Extended the Probe Basic machine-verification guidance so it now turns the
  dominant sphere-map recommendation plus the first flagged machine pose into a
  small trial-change plan.
- Current trial plan behavior:
  - uses the existing sign-guided first trial from the sphere-map assistant
  - chooses a first re-check pose from the earliest failed fixed-tip, moving
    TCP, or TWP pose when available
  - falls back to a sensible default re-check pose for:
    - `B_ZERO_OFFSET`
    - `C_ZERO_OFFSET`
    - `cal-c-to-b`
    - `cal-b-to-tool`
  - tells the operator what to re-run next if the first small change helps
  - tells the operator to revert and try the runner-up adjustment if it gets
    worse
- The same trial plan is now included in the generated summary output under
  `Trial change plan`.
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the trial-change plan is live.

# 2026-03-20 - Added one-click suggested re-check helpers

- Extended the Probe Basic `Verify` page with direct operator actions for the
  current suggested re-check:
  - `Load Suggested Re-check`
  - `Go To Suggested Pose`
- Current behavior:
  - chooses a suggested program from the current failed pose family or dominant
    adjustment bucket:
    - fixed-tip TCP
    - moving TCP
    - TWP granite-square
  - builds an MDI sequence for the suggested pose with the needed TCPC/TWP mode
    setup for that pose family
  - uses the same dominant-adjustment and first-failed-pose logic as the trial
    change plan
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the re-check helpers are live.

# 2026-03-20 - Streamlined the Verify page for operator use

- Cleaned up the Probe Basic `Verify` page so the real-machine workflow is the
  first visible path and the older sim/reference programs are separated into a
  secondary `Reference and sim tools` section.
- Added quick pose-log status helpers for each machine verification group:
  - fixed-tip TCP
  - moving TCP
  - TWP
- Each pose group now has one-click `Mark Pending`, `Mark Pass`, `Mark Hold`,
  and `Mark Fail` buttons so operators do not need to edit every pose field by
  hand during a run.
- Updated:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Verified with:
  - `python3 -m py_compile configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Relaunched Probe Basic after the update so the cleaned-up Verify page is
  live.

# 2026-03-20 - Added software acceptance matrix and fanless-PC rebuild notes

- Added a formal software-hardening acceptance checklist at:
  - `configs/sim/head_head_5axis/software_acceptance_matrix.md`
- Current acceptance matrix covers:
  - automated sim/runtime checks for:
    - TWP `G0/G1`
    - TCPC-required guard
    - rotary rejection
    - tool/TLO protections
    - tooling recovery after `G69`
    - limit reject and recovery
    - abort / estop / re-home semantics
    - remap queuebuster regression
  - manual sim acceptance checks
  - the ordered real-machine acceptance path once hardware is ready
- Added a rebuild/migration note for the future fanless PC at:
  - `configs/sim/head_head_5axis/fanless_pc_rebuild_notes.md`
- Current rebuild note records the non-repo dependencies on this test machine:
  - Probe Basic virtualenv in `/home/cnc5/dev/venv`
  - local Probe Basic checkout in `/home/cnc5/dev/probe_basic`
  - local QtPyVCP checkout in `/home/cnc5/dev/qtpyvcp`
  - local QtPyVCP `hal_qlib.py` shutdown patch
  - reduced STL directory in `/home/cnc5/Vismach/reduced`
  - desktop launcher path
- Updated:
  - `configs/sim/head_head_5axis/README.md`
- No runtime verification was needed for this documentation pass.

# 2026-03-20 - Added automated acceptance runner and Fusion post requirements

- Added a one-command head-head acceptance runner at:
  - `configs/sim/head_head_5axis/run_head_head_acceptance.sh`
- Current runner behavior:
  - launches the automated head-head LinuxCNC test harnesses in sequence
  - checks expected output patterns from each test
  - writes per-test logs under `/tmp` by default
  - supports:
    - `--stop-on-fail`
    - `--logs DIR`
- Verified locally:
  - shell syntax check:
    - `bash -n configs/sim/head_head_5axis/run_head_head_acceptance.sh`
  - help output:
    - `configs/sim/head_head_5axis/run_head_head_acceptance.sh --help`
  - first real run on this PC required escalation outside the sandbox because
    LinuxCNC test harnesses need normal runtime and display access
  - runner fixes discovered during first live use:
    - it must source the RIP environment and prefer each harness `test.sh`
      entry point instead of calling `linuxcnc -r test.ini` directly
    - it must temporarily relax `set -u` while sourcing
      `scripts/rip-environment`
  - after those fixes, the corrected runner completes
    `head-head-twp-g0g1` and advances into the next harness in sequence on this
    PC
- Added a machine-specific Fusion post requirements note at:
  - `configs/sim/head_head_5axis/fusion_post_requirements.md`
- Current post requirement decision:
  - use local `fanuc(1).cps` as the better starting base for the milling post
  - use local `fanuc inspection(1).cps` as the better starting base for the
    inspection/probing post
  - keep local `linuxcnc(1).cps` as a reference for LinuxCNC-friendly file and
    startup conventions, but not as the primary 5-axis base
- Reason captured in the note:
  - the local LinuxCNC Fusion post explicitly disables tilted workplane/TCP
    support
  - the Fanuc-family posts already carry the right TCP/TWP/probing concepts for
    this machine contract
- Updated:
  - `configs/sim/head_head_5axis/README.md`

# 2026-03-18 - Added remaining tool-state safety coverage

- Added runtime regression:
  - `tests/kinematics/head-head-twp-reject-tool-number`
    - proves `M61 Q1` is rejected while TWP is active
- Added positive recovery regression:
  - `tests/kinematics/head-head-twp-tooling-after-g69`
    - proves `G69` returns the controller to normal tooling behavior
    - verified sequence:
      - `G69`
      - `M61 Q1`
      - `G43 H1`
      - `G49`
- This confirms the intended operator rule:
  - while TWP is active, tooling state changes are blocked
  - after `G69`, tooling state changes are allowed again
- Verified with:
  - `tests/kinematics/head-head-twp-reject-tool-number`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - expected interpreter error observed:
        - `Cannot change current tool number while TWP is active`
  - `tests/kinematics/head-head-twp-tooling-after-g69`
    - result:
      - `pause 1 ok` through `pause 7 ok`
      - `program complete`

# 2026-03-18 - Added TWP limit reject and recovery coverage

- Added realistic-limit regression:
  - `tests/kinematics/head-head-twp-limit-reject`
    - uses the head-head style travel limits from the sim config instead of the
      wide-open math-test limits
    - proves a TWP local move is rejected with:
      - `Linear move on line 11 would exceed joint 1's positive limit`
- Added recovery regression:
  - `tests/kinematics/head-head-twp-limit-recovery`
    - proves the controller can recover from that reject with:
      - `G69`
      - `G49.1`
      - safe world reposition
      - `G43.4`
      - `G68.2 B45 C90`
      - a smaller safe TWP move
- Observed behavior:
  - the rejected TWP move does not partially move the tool
  - TWP state remains active after the reject until explicit cancel
  - the validated recovery sequence successfully re-enters TWP and resumes motion
- Verified with:
  - `tests/kinematics/head-head-twp-limit-reject`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - expected limit error observed:
        - `Linear move on line 11 would exceed joint 1's positive limit`
  - `tests/kinematics/head-head-twp-limit-recovery`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - expected limit error observed
      - `recovery step 1 ok` through `recovery step 6 ok`

# 2026-03-18 - Added abort/reset semantics and manual demo programs

- Updated the TWP state component to watch:
  - machine enabled state via `iocontrol.0.user-enable-out`
  - homed state via `joint.N.homed`
- Current controller behavior is now:
  - program abort leaves TWP/TCPC state unchanged until explicit cancel
  - estop / machine-off clears TWP and restores default TCPC-on
  - unhome/home or re-home clears TWP and preserves the current TCPC mode
- Verified with:
  - `tests/kinematics/head-head-twp-abort-state`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - `abort state ok`
      - `abort recovery ok`
  - `tests/kinematics/head-head-twp-estop-reset`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - `estop clear ok`
      - `reset clear ok`
      - `re-enter after estop ok`
      - `post-estop recovery cancel ok`
- Added manual sample programs in `configs/sim/head_head_5axis`:
  - `twp_abort_state_demo.ngc`
  - `twp_estop_reset_demo.ngc`
  - `twp_rehome_reset_demo.ngc`
  - `twp_limit_recovery_demo.ngc`
- Note:
  - `tests/kinematics/head-head-twp-rehome-reset` was drafted for the same
    policy, but I did not get a clean automated verification run for it in this
    session because the harness DISPLAY process did not start reliably under the
    current exec-session churn.

# 2026-03-18 - Manual B/C workflow clarified

- Locked the operator rule:
  - manual `B/C` motion is allowed when TCPC is on and TWP is off
  - `B/C` motion remains blocked while TWP is active
  - after `G69`, operators may move `B/C` first and then enter `G68.2`
- Clarified `G68.2` semantics:
  - `G68.2` may omit `B/C`
  - if omitted, current `B/C` are captured as the TWP orientation
- Added runtime regression:
  - `tests/kinematics/head-head-twp-manual-bc-entry`
    - proves:
      - TCPC-on / TWP-off manual `B/C` motion
      - `G68.2` entry from current `B/C`
      - `G69` followed by another manual `B/C` move and re-entry
- Added manual sample program:
  - `configs/sim/head_head_5axis/twp_manual_bc_entry_demo.ngc`
- Verified with:
  - `tests/kinematics/head-head-twp-manual-bc-entry`
    - result:
      - `pause 1 ok` through `pause 11 ok`
      - `program complete`

# 2026-03-18 - Re-home regression verified

- Closed the remaining automation gap in:
  - `tests/kinematics/head-head-twp-rehome-reset`
- Root cause:
  - the harness was asserting immediately after `status.homed` dropped to 4 on
    `unhome(0)`
  - `headheadtwp` clears from a separate userspace polling loop, so the test had
    a race between LinuxCNC status and HAL state propagation
- Fix:
  - added a `wait_for_twp_state(...)` helper in
    `tests/kinematics/head-head-twp-rehome-reset/test-ui.py`
  - changed the `unhome` and `home` phases to wait for the cleared TWP state
    instead of asserting it in the same cycle
  - restored the test HAL component name back to `test-ui`
- Verified with:
  - `tests/kinematics/head-head-twp-rehome-reset`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - `abort before rehome ok`
      - `unhome clear ok`
      - `rehome clear ok`
      - `re-enter after rehome ok`
      - `post-rehome recovery cancel ok`

# 2026-03-18 - Added fresh manual demo programs for current TCPC/TWP flow

- Added a new TCPC-focused sample program:
  - `configs/sim/head_head_5axis/tcp_tcpc_fresh_demo.ngc`
  - uses the current controller contract:
    - `G43.4`
    - fixed-tip `B/C` reorientation checks
    - short world-coordinate TCP motion with TCPC left active
    - `G49.1`
- Added a new TWP-focused sample program:
  - `configs/sim/head_head_5axis/twp_g68_2_fresh_demo.ngc`
  - uses the current controller contract:
    - `G43.4`
    - `G68.2 B45 C90`
    - ordinary `G0/G1 X/Y/Z` in the tilted local frame
    - `G69`
    - `G49.1`
- Updated the head-head README demo list to include both files.

# 2026-03-18 - Added initial head-head Probe Basic sim config

- Added a dedicated Probe Basic entry point for the current head-head sim:
  - `configs/sim/head_head_5axis/head_head_probe_basic.ini`
  - `configs/sim/head_head_5axis/custom_config.yml`
  - `configs/sim/head_head_5axis/probe_basic_postgui.hal`
  - `configs/sim/head_head_5axis/launch_probe_basic.sh`
- Current approach is intentionally minimal:
  - reuse the existing head-head HAL, remaps, vismach, and kinematics
  - swap `DISPLAY = probe_basic`
  - use the stock Probe Basic `XYZBC` DRO assets from the local dev checkout
  - avoid pulling over the older SSI machine-specific Probe Basic customizations
- Next verification step is to launch `launch_probe_basic.sh` and fix any first-run
  Probe Basic integration issues from the real UI path.

# 2026-03-18 - Enabled Probe Basic ATC tab as a placeholder UI

- Switched the head-head Probe Basic sim to show the Probe Basic ATC tab:
  - `ATC_TAB_DISPLAY = 1`
  - `USER_ATC_BUTTONS_PATH` now points at the Probe Basic `atc_sim` asset set
- Added a minimal `[ATC]` section with placeholder values for:
  - `POCKETS = 12`
  - `Z_TOOL_CHANGE_HEIGHT = -100.0`
  - `Z_TOOL_CLEARANCE_HEIGHT = 0.0`
- Added safe placeholder ATC actions in the head-head sim directory so the ATC UI
  can be present before real ATC hardware/logic exists:
  - `M11`
  - `M12`
  - `M13`
  - `retractatc.ngc`
  - `extendatc.ngc`
  - `clamptool.ngc`
  - `unclamptool.ngc`
  - `orientspindle.ngc`
  - `move_head_above_carousel.ngc`
  - `move_tool_to_carousel_height.ngc`
- Current intent:
  - keep the ATC panel visible in Probe Basic now
  - allow the Z-position helper buttons to operate safely in sim
  - leave carousel/clamp/orient actions as placeholders until real ATC work starts

# 2026-03-18 - Added 5-axis calibration wizard tab for Probe Basic

- Added a dedicated Probe Basic user tab path in:
  - `configs/sim/head_head_5axis/head_head_probe_basic.ini`
- Added a new main-tab calibration wizard at:
  - `configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py`
- Current wizard content:
  - setup/safety page with common mode-reset and pose buttons
  - rotary zero-offset page
  - `C->B` correction page
  - `B->tool` correction page
  - verification page with quick-load buttons for the fresh TCP/TWP demos
  - summary page that generates the matching `setp` block for both:
    - `headheadkins`
    - `headheadtwp`
- The wizard saves and reloads a local draft file:
  - `configs/sim/head_head_5axis/five_axis_calibration_draft.json`
- The summary is staging-only for now:
  - it does not yet write values back into HAL automatically
  - it is meant to guide the operator and produce the values to carry into the
    config/model cleanly

# 2026-03-18 - `G68.2` now defines and activates TWP directly

- Shifted the sample-data posted TWP path away from helper M-codes:
  - `G68.2` now defines and activates TWP directly
  - `G69` now cancels and resets TWP directly
- Current sample-data machine-facing path is now:
  - `G43.4`
  - `G68.2 B.. C.. [R..]`
  - ordinary `G0/G1`
  - `G69`
  - `G49.1`
- Implemented in:
  - `configs/sim/head_head_5axis/head_head_twp_state.py`
  - `configs/sim/head_head_5axis/python/remap.py`
  - `src/emc/kinematics/headheadkins.c`
- New `G68.2` semantics:
  - origin is taken from the current tool-tip position
  - `B/C` come from the block, or default to the current `B/C` if omitted
  - optional `R` sets plane-normal rotation
  - the remap captures that definition, activates TWP, enables TWP motion, and
    zeros local `XYZ` with `G92`
- New `G69` semantics:
  - preserve the current world tool-tip position
  - exit TWP motion mode
  - cancel and reset the stored TWP definition
- Added kinematics-level guard:
  - active TWP now rejects rotary changes away from the stored `B/C`
  - current observed runtime error text is:
    - `Linear move on line 11 fails kinematicsInverse`
- Updated runtime tests:
  - `tests/kinematics/head-head-twp-g0g1`
    - now uses `G68.2 B45 C90` and `G68.2 B45 C90 R90`
    - no longer depends on `M152` / `M153` / `M156` / `M154` / `M155`
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - now proves `G68.2 B45 C90` is rejected if `G49.1` turned TCPC off first
  - added `tests/kinematics/head-head-twp-reject-rotary`
    - proves a linear block with a changed `B` word is rejected while TWP is active
- Important LinuxCNC detail:
  - `G68.2` needed `argspec=bcr` in the remap lines before `B/C/R` words were
    visible to the Python handler
- Verified with:
  - `tests/kinematics/head-head-twp-g0g1`
    - result:
      - `pause 1 ok` through `pause 14 ok`
      - `program complete`
  - `tests/kinematics/head-head-twp-requires-tcpc`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - expected interpreter error observed:
        - `TWP mode enable requested while TCPC mode is not enabled`
  - `tests/kinematics/head-head-twp-reject-rotary`
    - result:
      - `pause 1 ok`
      - `pause 2 ok`
      - `pause 3 ok`
      - expected runtime error observed:
        - `Linear move on line 11 fails kinematicsInverse`
  - `tests/remap/head-head-twp-queuebuster`
    - result:
      - `pause 1 ok` through `pause 8 ok`
      - `program complete`

# 2026-03-20 - software acceptance runner hardened and green

- Added one-command automated acceptance runner:
  - `configs/sim/head_head_5axis/run_head_head_acceptance.sh`
- Added Fusion post requirements note:
  - `configs/sim/head_head_5axis/fusion_post_requirements.md`
- Post direction captured from the local Fusion baselines on this PC:
  - use `fanuc(1).cps` as the milling post base
  - use `fanuc inspection(1).cps` as the inspection/probing post base
  - keep `linuxcnc(1).cps` only as a reference for LinuxCNC-friendly file and
    startup conventions
- Hardened the acceptance runner:
  - source `scripts/rip-environment` before each harness
  - prefer each harness `test.sh` instead of bypassing it
  - relax `set -u` while sourcing the RIP environment
  - add a short cooldown between harnesses
  - retry the known LinuxCNC realtime teardown race when `homemod` /
    `headheadkins` have not fully released yet
- Updated the limit harnesses to match the current head-head baseline:
  - `tests/kinematics/head-head-twp-limit-reject`
  - `tests/kinematics/head-head-twp-limit-recovery`
- Current limit-harness adjustments:
  - safe starting pose moved to `G0 X1500 Y1400 Z-600 B45 C90`
  - intentional overtravel now uses local `G1 Y400.0`
  - expected error text generalized to `positive limit`
  - position tolerance relaxed to `0.5`
- Verified with:
  - `configs/sim/head_head_5axis/run_head_head_acceptance.sh --stop-on-fail --logs /tmp/head_head_acceptance_latest5`
  - result:
    - `14 passed, 0 failed`
  - passing harnesses:
    - `twp_g0g1`
    - `twp_requires_tcpc`
    - `twp_reject_rotary`
    - `twp_reject_tool_length`
    - `twp_reject_tool_change`
    - `twp_reject_tool_number`
    - `twp_tooling_after_g69`
    - `twp_limit_reject`
    - `twp_limit_recovery`
    - `twp_abort_state`
    - `twp_estop_reset`
    - `twp_rehome_reset`
    - `twp_manual_bc_entry`
    - `twp_queuebuster`

# 2026-03-24 - inspection alignment contract added

- Added:
  - `configs/sim/head_head_5axis/inspection_alignment_contract.md`
- Purpose:
  - define the approved WCS/alignment workflow for inspection and mold
    alignment
  - prevent the earlier failure mode where valid probe data was applied in the
    wrong frame
- Current production-default alignment rule:
  - probe in `G54`
  - `G69` active
  - indexed `B/C` allowed
  - TCPC allowed if needed for safe head-head motion
  - apply correction once, preferably in the Fusion setup
  - verify in the same frame used for measurement
- Linked the alignment contract from:
  - `configs/sim/head_head_5axis/fusion_post_requirements.md`
  - `configs/sim/head_head_5axis/README.md`
- No runtime verification required for this pass because it is a machine/process
  contract document, not code.

# 2026-03-24 - old probing workflow reviewed

- Reviewed legacy probing files from:
  - `/home/cnc5/Old System/probing`
  - `/home/cnc5/Old System/Backup Feb 2026/linuxcnc/configs/5th_axis`
- Added:
  - `configs/sim/head_head_5axis/legacy_probe_workflow_review.md`
- Useful legacy pattern confirmed:
  - Fusion-style file-based result logs with:
    - `RESULTSFILE`
    - `G331`
    - `G330`
    - repeated `G800` / `G801` entries
- Main legacy risk confirmed:
  - many old probe macros wrote directly to the active WCS with `G10 L2 P#5220`
  - the old config also used a dynamic rotary-aware work-offset remap:
    - `dynamic-work-offsets-v2.ngc`
    - remapped as `M254`
- Key old-system frame-mixing evidence:
  - `Probe101.ngc` used `G54`
  - `Probe#1 Alt WCS.ngc` used `G55`
- Current decision:
  - keep the legacy file-based results pattern
  - do not carry the dynamic-WCS correction behavior into the default
    mold-alignment workflow
- Linked the legacy review from:
  - `configs/sim/head_head_5axis/inspection_alignment_contract.md`
  - `configs/sim/head_head_5axis/README.md`

# 2026-03-24 - inspection results file spec added

- Added:
  - `configs/sim/head_head_5axis/inspection_results_format_spec.md`
- Purpose:
  - define the first production inspection/alignment results-file target for the
    head-head machine
  - keep the legacy Fusion-friendly `G331` / `G330` / `G800` / `G801` pattern
    but add the missing frame metadata
- New required header metadata:
  - `ACTIVE_WCS`
  - `ACTIVE_B`
  - `ACTIVE_C`
  - `TCPC`
  - `TWP`
  - `TWP_ROT`
  - `MACHINECFG`
  - `TIMESTAMP`
  - `RESULT_STATUS`
  - `ARTIFACT`
  - optional `CORRECTION_TARGET` / `FRAME_POLICY`
- Current production-default intent:
  - file-based Fusion import remains the first production inspection path
  - mold-alignment result sets should default to:
    - `RESULT_STATUS RAW`
    - `CORRECTION_TARGET FUSION_SETUP`
- Linked the new results-file spec from:
  - `configs/sim/head_head_5axis/fusion_post_requirements.md`
  - `configs/sim/head_head_5axis/README.md`

# 2026-03-24 - first machine power-up note for partial reassembly

- The machine is being reassembled and first power-up may only have `X/Y`
  available.
- Current config status:
  - the main head-head Probe Basic config already allows unhomed motion:
    - `configs/sim/head_head_5axis/head_head_probe_basic.ini`
  - the head-head sim configs already allow unhomed motion:
    - `configs/sim/head_head_5axis/head_head_visual_sim.ini`
    - `configs/sim/head_head_5axis/head_head_math_sim.ini`
  - the current legacy machine config also already allows unhomed motion:
    - `configs/5th_axis/5th_axis.ini`
- Relevant setting:
  - `NO_FORCE_HOMING = 1`
- Practical consequence:
  - the PC can be moved to the machine and used for first-power `X/Y` motion
    checks before a full homing path exists
  - do not attempt a fake full-home just to get motion during partial
    reassembly
- Updated:
  - `configs/sim/head_head_5axis/machine_bringup_checklist.md`

# 2026-03-30 - XYZ maintenance config prepared for unhomed assembly work

- Added a separate temporary maintenance config so the main machine setup does
  not need to be repurposed for assembly motion:
  - `configs/5th_axis_xyz_maintenance/5th_axis_xyz_maintenance.ini`
  - `configs/5th_axis_xyz_maintenance/5th_axis_xyz_maintenance.hal`
  - `configs/5th_axis_xyz_maintenance/xhc.hal`
  - `configs/5th_axis_xyz_maintenance/xhc-hb04-layout2_mm.ini`
  - `configs/5th_axis_xyz_maintenance/launch_xyz_maintenance.sh`
- Intent:
  - real machine maintenance / assembly work only
  - `X/Y/Z` motion only
  - no homing required on startup
  - keep `B/C/W`, spindle, probe, and remap-specific behavior out of this
    temporary config
- Key config state:
  - `DISPLAY = axis`
  - `JOINTS = 3`
  - `KINEMATICS = trivkins coordinates=XYZ`
  - `NO_FORCE_HOMING = 1`
  - all `X/Y/Z` joints set with:
    - `HOME_SEARCH_VEL = 0`
    - `HOME_USE_INDEX = NO`
- Pendant state:
  - `WHB04B-6` wiring is mapped only to `joint.0/1/2`
  - the pendant's fourth selector position is intentionally left unused in this
    config
  - conservative jog tuning retained:
    - `coefs = 0.25`
    - `scales = 0.5/-0.5/0.5/0.5`
    - `jogmode = vnormal`
    - reduced `mpg_accels`
- Desktop launch shortcut added:
  - `/home/cnc5/Desktop/XYZ Maint.desktop`
- Verified live startup:
  - launched `/home/cnc5/linuxcnc-dev/configs/5th_axis_xyz_maintenance/launch_xyz_maintenance.sh`
  - LinuxCNC started and stayed running
  - Mesa `7I95T` was detected successfully on `10.10.10.10`
  - no fatal INI or HAL load errors were seen during startup
- Non-fatal startup warning:
  - `hm2_eth` reported missing `iptables`
  - this affects realtime network-access restriction only and did not block
    LinuxCNC startup
- Next resume point:
  - use `XYZ Maint` on the desktop for assembly / maintenance motion
  - if motion quality issues remain, compare keyboard jog versus pendant jog
    inside this stripped-down config before changing the main machine config

# 2026-04-02 - XYZ maintenance handwheel issue resolved

- The `WHB04B-6` hand controller was still jumpy in the temporary XYZ
  maintenance config even after USB receiver testing, receiver swap, and USB
  port changes.
- Important debug result:
  - standalone `xhc-whb04b-6 -ue` testing showed the USB / wireless path had
    separate issues during diagnosis, but the final LinuxCNC motion problem was
    not caused by the reduced axis acceleration values.
- Root cause in the maintenance config:
  - `configs/5th_axis_xyz_maintenance/xhc.hal` had been rewritten to jog
    `joint.0/1/2` directly.
  - the original known-good machine config in:
    - `/home/cnc5/Old System/Backup Feb 2026/linuxcnc/configs/5th_axis/xhc.hal`
    used the standard axis path instead:
    - `halui.axis.*.select`
    - `axis.*.jog-scale`
    - `axis.*.jog-counts`
    - `axis.*.jog-enable`
    - `axis.*.jog-vel-mode`
- Fix applied:
  - replaced the maintenance `xhc.hal` wiring with the old-style axis-based
    jog path for `X/Y/Z`
  - restored the pendant mode wiring used by the known-good config:
    - auto/manual/mdi/joint/teleop status and commands
  - kept the config limited to `X/Y/Z` only
  - corrected the AXIS `[DISPLAY]INCREMENTS` line in
    `5th_axis_xyz_maintenance.ini` from:
    - `INCREMENTS = JOG ...`
    to a plain numeric list that AXIS accepts
- Result:
  - restarted `XYZ Maint`
  - pendant motion is now working correctly
  - user confirmed: `Fixed!`
- Current known-good temporary maintenance launcher remains:
  - `/home/cnc5/linuxcnc-dev/configs/5th_axis_xyz_maintenance/launch_xyz_maintenance.sh`
  - desktop shortcut: `/home/cnc5/Desktop/XYZ Maint.desktop`
- Practical lesson for future temporary configs:
  - do not replace the WHB04B-6 axis jog path with direct `joint.*` jog wiring
    unless there is a proven machine-specific reason to do so

# 2026-04-11 - XYZBC maintenance config added for B/C setup

- Added a separate temporary maintenance config copied from the known-good XYZ
  maintenance setup:
  - `configs/5th_axis_xyzbc_maintenance/5th_axis_xyzbc_maintenance.ini`
  - `configs/5th_axis_xyzbc_maintenance/5th_axis_xyzbc_maintenance.hal`
  - `configs/5th_axis_xyzbc_maintenance/xhc.hal`
  - `configs/5th_axis_xyzbc_maintenance/encoder_alignment.xml`
  - `configs/5th_axis_xyzbc_maintenance/encoder_alignment_postgui.hal`
  - `configs/5th_axis_xyzbc_maintenance/launch_xyzbc_maintenance.sh`
- Intent:
  - real-machine setup/testing only
  - `X/Y/Z/B/C` motion
  - no homing required on startup
  - B/C driven with the original 5th Axis stepgen servo style
  - new B/C SSI encoders displayed for alignment only
- Important feedback choice:
  - `joint.3.motor-pos-fb` remains `hm2_7i95.0.stepgen.03.position-fb`
  - `joint.4.motor-pos-fb` remains `hm2_7i95.0.stepgen.04.position-fb`
  - `hm2_7i95.0.ssi.00.abs.position` and `hm2_7i95.0.ssi.01.abs.position`
    are exposed in the AXIS PyVCP side panel but are not connected to the servo
    drive feedback path yet
- Pendant choice:
  - kept the old known-good `axis.*.jog-*` path
  - did not use direct `joint.*.jog-*` injection, because that caused the jumpy
    WHB04B-6 behavior in the previous maintenance config
- Validation performed:
  - XML parse check for `encoder_alignment.xml`
  - shell syntax check for `launch_xyzbc_maintenance.sh`
  - grep check confirmed no direct `joint.*.jog-*` wiring in the new config
- Not yet performed:
  - live LinuxCNC launch against the machine hardware

# 2026-04-11 - XYZBC maintenance launch test

- Launched:
  - `configs/5th_axis_xyzbc_maintenance/launch_xyzbc_maintenance.sh`
- Startup result:
  - LinuxCNC started and stayed running
  - Mesa `7I95T` detected at `10.10.10.10`
  - HostMot2 reported five stepgen pairs and two SSI channels as expected
- Known non-fatal warning still present:
  - missing `iptables` prevents hm2_eth from installing realtime network access
    restriction rules
  - this warning did not block startup
- Live SSI checks:
  - `hm2_7i95.0.ssi.00.data-invalid = FALSE`
  - `hm2_7i95.0.ssi.00.abs.position = -98.47939`
  - `hm2_7i95.0.ssi.01.data-invalid = FALSE`
  - `hm2_7i95.0.ssi.01.abs.position = -185.9199`
- PyVCP panel check:
  - `pyvcp.b-ssi-position` is connected to `b-ssi-position`
  - `pyvcp.c-ssi-position` is connected to `c-ssi-position`
- B/C servo feedback remains monitor-safe:
  - `b-pos-fb` is linked from `hm2_7i95.0.stepgen.03.position-fb` to
    `joint.3.motor-pos-fb` and `pid.b.feedback`
  - `c-pos-fb` is linked from `hm2_7i95.0.stepgen.04.position-fb` to
    `joint.4.motor-pos-fb` and `pid.c.feedback`
  - SSI encoder positions are not connected to B/C motor feedback yet
- Current practical state:
  - config is suitable for visual encoder alignment checks with B/C drives
    still unpowered
  - next live step is to power B/C drives when ready and test very small B/C
    jogs while watching both AXIS commanded position and the SSI panel

# 2026-04-11 - XYZBC maintenance confirmed by user

- User confirmed the launched `XYZBC` maintenance config is working correctly.
- Current validated state:
  - LinuxCNC starts and stays running
  - B/C SSI encoder display is live in the AXIS PyVCP panel
  - B/C servo feedback remains on stepgen feedback, not SSI feedback
  - B/C servo drives were still unpowered during this confirmation
- Next practical step when ready:
  - power B/C drives and test very small B/C jogs while watching commanded B/C
    position against the SSI encoder panel.

# 2026-04-11 - XYZBC maintenance restart after encoder centering

- Restarted the running `XYZBC` maintenance LinuxCNC session with Ctrl-C and
  relaunched the same launcher.
- Shutdown produced the known AXIS/Tk Ctrl-C traceback and an xhc component
  assertion during cleanup, but LinuxCNC cleaned up and unloaded HostMot2.
- Relaunch result:
  - LinuxCNC started again
  - Mesa `7I95T` detected again at `10.10.10.10`
  - five stepgens and two SSI channels were present again
- Post-restart SSI readings:
  - B `hm2_7i95.0.ssi.00.abs.rawcounts = -531025`
  - B `hm2_7i95.0.ssi.00.abs.position = 182.313`
  - B `hm2_7i95.0.ssi.00.data-invalid = FALSE`
  - C `hm2_7i95.0.ssi.01.abs.rawcounts = -526659`
  - C `hm2_7i95.0.ssi.01.abs.position = 180.814`
  - C `hm2_7i95.0.ssi.01.data-invalid = FALSE`
- Interpretation:
  - after restart, the absolute encoder reports on the other side of the
    midpoint/wrap convention, so the scaled display is near `+180` rather than
    the earlier `-180`
  - both channels are still valid and near the intended mid-range alignment

# 2026-04-11 - XYZBC SSI display zeroed

- Adjusted only the `XYZBC` maintenance display path so the B/C SSI alignment
  panel reads near zero at the current mechanical reference.
- Added `sum2` components in:
  - `configs/5th_axis_xyzbc_maintenance/5th_axis_xyzbc_maintenance.hal`
- Current display offsets:
  - `b_ssi_zero.in1 = -182.5739`
  - `c_ssi_zero.in1 = -180.8140`
- Important distinction:
  - raw HostMot2 SSI absolute positions are unchanged
  - B/C motor feedback remains on stepgen feedback, not SSI feedback
  - only the AXIS PyVCP alignment display is zeroed
- Restarted LinuxCNC after the change.
- Post-restart check:
  - raw B display source `b-ssi-abs-position = 182.5739`
  - zeroed B panel signal `b-ssi-position = -9.313965e-06`
  - raw C display source `c-ssi-abs-position = 180.8137`
  - zeroed C panel signal `c-ssi-position = -0.0003250732`
- Practical result:
  - the B/C SSI alignment panel now reads approximately `0.000` for both axes
    at the current locked mechanical positions.

# 2026-04-11 - C SSI display changed to 2:1 axis scale

- User requested the C SSI display in the maintenance config be treated as a
  2:1 C-axis relationship for display only.
- Updated only the display path in:
  - `configs/5th_axis_xyzbc_maintenance/5th_axis_xyzbc_maintenance.hal`
- Added:
  - `loadrt mult2 names=c_ssi_axis_scale`
  - `setp c_ssi_axis_scale.in1 2.0`
  - `c_ssi_zero.out` now feeds `c_ssi_axis_scale.in0`
  - PyVCP `c-ssi-position` now receives `c_ssi_axis_scale.out`
- B display path is unchanged.
- B/C servo feedback remains unchanged and still uses stepgen feedback, not SSI.
- Restarted LinuxCNC after the edit.
- Post-restart check:
  - `c-ssi-abs-position = 180.6444`
  - `c-ssi-zeroed-position = -0.1695832`
  - `c-ssi-position = -0.3391664`
- Interpretation:
  - the C panel is now displaying twice the zeroed 1:1 SSI encoder delta
  - this is display-only for the maintenance config; feedback integration is a
    later config step

# 2026-04-11 - C SSI display ratio corrected to 0.5

- User observed the previous C display scale was backwards:
  - a roughly 90 degree C-axis rotation displayed roughly 180 degrees on the SSI
    panel
  - B display was tracking correctly
- Corrected only the C display multiplier in:
  - `configs/5th_axis_xyzbc_maintenance/5th_axis_xyzbc_maintenance.hal`
- Changed:
  - `c_ssi_axis_scale.in1 = 2.0`
  - to `c_ssi_axis_scale.in1 = 0.5`
- Applied the same change live with `halcmd setp c_ssi_axis_scale.in1 0.5`.
- Post-change live check:
  - `c-ssi-zeroed-position = -0.2732667`
  - `c-ssi-position = -0.1366333`
- Interpretation:
  - the AXIS C SSI panel now displays half of the zeroed encoder delta
  - expected result is that a 90 degree C-axis move displays about 90 degrees
    instead of 180 degrees
- B display path remains unchanged.
- B/C servo feedback remains unchanged and still uses stepgen feedback, not SSI.

# 2026-04-11 - C SSI display ratio corrected to 1.0

- User tested the prior `0.5` C SSI display multiplier and found a 90 degree C
  move displayed about 45 degrees.
- Combined with the earlier `2.0` test displaying about 180 degrees for a 90
  degree move, this shows the zeroed SSI delta already matches C-axis display
  degrees for this maintenance panel.
- Corrected C display multiplier to:
  - `c_ssi_axis_scale.in1 = 1.0`
- Applied live with:
  - `halcmd setp c_ssi_axis_scale.in1 1.0`
- Updated:
  - `configs/5th_axis_xyzbc_maintenance/5th_axis_xyzbc_maintenance.hal`
  - `configs/5th_axis_xyzbc_maintenance/README.md`
- Post-change live check:
  - `c_ssi_axis_scale.in1 = 1`
  - `c-ssi-zeroed-position = -0.4768571`
  - `c-ssi-position = -0.4768571`
- Interpretation:
  - the C SSI panel is now one-to-one with the zeroed SSI encoder delta
  - B/C servo feedback remains unchanged and still uses stepgen feedback, not SSI

# 2026-04-11 - XYZBC maintenance config locked as current baseline

- User confirmed the C display confusion came from older implementation planning.
- Locked the current `XYZBC` maintenance config as the baseline for full 5-axis
  maintenance work:
  - axes: `X/Y/Z/B/C`
  - no homing required on startup
  - B/C servo output uses original 5th Axis stepgen servo style
  - B/C motor feedback remains on stepgen feedback
  - SSI encoder values remain display-only
  - B SSI display is 1:1 zeroed encoder delta
  - C SSI display is 1:1 zeroed encoder delta
  - pendant jog wiring remains on the known-good `axis.*.jog-*` path
- Confirmed by grep:
  - no SSI-to-`joint.3/4.motor-pos-fb` links in the maintenance config
  - `joint.3.motor-pos-fb` is fed by `hm2_7i95.0.stepgen.03.position-fb`
  - `joint.4.motor-pos-fb` is fed by `hm2_7i95.0.stepgen.04.position-fb`
- Updated:
  - `configs/5th_axis_xyzbc_maintenance/README.md`
- Next-stage SSI servo feedback work should be done in a separate config, not by
  changing this locked maintenance baseline.

# 2026-04-11 - XYZBC maintenance scope clarified

- User clarified the locked `XYZBC` maintenance config will be used only for
  moving servos during maintenance work.
- Updated the config README to state it is not a production machining,
  calibration, or SSI-feedback commissioning config.
- This config remains maintenance servo-motion only.

# 2026-04-11 - XYZBC SSI feedback test config created

- Created a separate next-stage dev/test copy from the locked maintenance
  baseline:
  - `configs/5th_axis_xyzbc_ssi_feedback_test/`
- Purpose:
  - test using the B/C SSI absolute encoders as the actual B/C servo feedback
  - keep the locked `configs/5th_axis_xyzbc_maintenance/` config as the
    maintenance fallback with no SSI feedback in the servo loop
- New launcher:
  - `configs/5th_axis_xyzbc_ssi_feedback_test/launch_xyzbc_ssi_feedback_test.sh`
- Renamed config files:
  - `5th_axis_xyzbc_ssi_feedback_test.ini`
  - `5th_axis_xyzbc_ssi_feedback_test.hal`
  - `5th_axis_xyzbc_ssi_feedback_test.var`
- Feedback routing in the new test config:
  - `hm2_7i95.0.ssi.00.abs.position` -> `b_ssi_zero.in0`
  - `b_ssi_zero.out` -> `b-pos-fb`
  - `b-pos-fb` -> `pid.b.feedback`
  - `b-pos-fb` -> `joint.3.motor-pos-fb`
  - `hm2_7i95.0.ssi.01.abs.position` -> `c_ssi_zero.in0`
  - `c_ssi_zero.out` -> `c_ssi_axis_scale.in0`
  - `c_ssi_axis_scale.out` -> `c-pos-fb`
  - `c-pos-fb` -> `pid.c.feedback`
  - `c-pos-fb` -> `joint.4.motor-pos-fb`
- Stepgen feedback is no longer the B/C motor feedback source in this new test
  config, but it remains exposed as monitor-only signals:
  - `b-stepgen-pos-fb <= hm2_7i95.0.stepgen.03.position-fb`
  - `c-stepgen-pos-fb <= hm2_7i95.0.stepgen.04.position-fb`
- C SSI scale remains one-to-one for the zeroed display/feedback path:
  - `c_ssi_axis_scale.in1 = 1.0`
- Static checks performed:
  - XML parse check for `encoder_alignment.xml`
  - shell syntax check for `launch_xyzbc_ssi_feedback_test.sh`
  - grep confirmed B/C motor feedback is sourced from zeroed SSI signals in the
    new test config
- Not yet performed:
  - live LinuxCNC launch of the SSI feedback test config
- Safety note:
  - start with B/C drives disabled or mechanically safe
  - test one axis at a time with tiny jogs
  - if feedback direction or following-error behavior is wrong, go back to the
    locked `5th_axis_xyzbc_maintenance` config


# 2026-04-11 - XYZBC SSI feedback test launch and C startup wrap correction

- Launched `configs/5th_axis_xyzbc_ssi_feedback_test/launch_xyzbc_ssi_feedback_test.sh` after shutting down the locked maintenance session.
- First power-on attempt produced repeated joint 4 following errors. Live HAL showed SSI data valid, but C feedback was outside the tight startup following-error window.
- Updated only the SSI feedback test config; locked maintenance config remains unchanged.
- Tightened B/C zero offsets and added C startup wrap-branch normalization:
  - `b_ssi_zero.in1 = -182.1640`
  - `c_ssi_zero.in1 = -179.0476`
  - `c_ssi_wrap_add` adds `360.0` when the zeroed C startup branch lands below `-180.0`
  - `c_ssi_startup_normalized` feeds `c_ssi_axis_scale.in0`, then `c-pos-fb` feeds `pid.c.feedback` and `joint.4.motor-pos-fb`
- Relaunched the feedback test config. Live checks after relaunch:
  - `b-pos-fb` approximately `0.000 deg`
  - `c-ssi-zeroed-position` approximately `-360 deg`
  - `c-ssi-startup-normalized` approximately `0.000 deg`
  - `c-pos-fb` approximately `0.000 deg`
  - B/C SSI `data-invalid` pins `FALSE`
  - joint 4 not f-errored before drive enable
- Note: this is still a dev/test startup branch correction near the current home range, not a complete future-proof C-axis power-up position validation scheme.

# 2026-04-11 - C SSI feedback direction matched to servo setup

- While the feedback-test config was live, C SSI feedback and C stepgen position moved in opposite signs:
  - C SSI feedback was approximately `+0.870 deg`
  - C stepgen position feedback was approximately `-0.829 deg`
- With joint 4 amp-enable false, set live `c_ssi_axis_scale.in1 = -1.0` and confirmed C SSI feedback became approximately `-0.869 deg`, matching the C stepgen sign.
- Updated only `configs/5th_axis_xyzbc_ssi_feedback_test/5th_axis_xyzbc_ssi_feedback_test.hal` so C uses `setp c_ssi_axis_scale.in1 -1.0` on restart.
- B direction has not yet been proven under motion in this feedback-test config.

# 2026-04-11 - SSI feedback direction verification caution

- User correctly noted that stepgen position feedback is calculated from the command/pulse train and is not definitive real machine position because the servo drive has its own position control.
- Treat the C `c_ssi_axis_scale.in1 = -1.0` change as provisional until verified by an actual tiny commanded C move and the corresponding SSI feedback direction.
- Correct proof for B/C SSI feedback sign: during a small positive LinuxCNC command, the SSI-derived `joint.N.motor-pos-fb` must move positive in the same coordinate sense; during a small negative command it must move negative.
- Do not use stepgen position feedback as absolute truth for B/C machine position; at most it is a command-side reference from the previous maintenance setup.

# 2026-04-11 - Stepgen feedback use clarified

- User clarified stepgen position feedback can be used for direction and estimates only, not as definitive B/C machine position.
- Current feedback-test interpretation: C `c_ssi_axis_scale.in1 = -1.0` is a provisional direction match against the command-side/stepgen direction estimate, while final sign proof still requires a tiny commanded motion with SSI feedback moving in the same command sign.

# 2026-04-11 - SSI feedback test B/C safety limits reduced

- User reported continued following error and asked whether the INI/HAL need larger changes for closed-loop B/C SSI feedback.
- Interpretation: using SSI as real feedback is not just a display reroute; B/C need conservative outer-loop tuning and startup behavior because the old maintenance setup closed the LinuxCNC loop against calculated stepgen position.
- Updated only the feedback-test config with slower B/C commissioning limits:
  - `[DISPLAY]`/`[TRAJ]` angular jog default `0.25 deg/s`, max `1 deg/s`
  - `[AXIS_B]`/`[AXIS_C]` max velocity `1 deg/s`, max acceleration `3 deg/s^2`
  - `[JOINT_3]`/`[JOINT_4]` max velocity `1 deg/s`, max acceleration `3 deg/s^2`
  - B/C `STEPGEN_MAXVEL = 1.5`, `STEPGEN_MAXACCEL = 6`
  - B/C `P = 50.0`, `MAX_OUTPUT = 1.0`
  - B/C following error windows set to `FERROR = 2`, `MIN_FERROR = 0.5`
- Relaunched feedback-test config. AXIS reported angular jog max `1 deg/s`, default `0.25 deg/s`. Live HAL confirmed B/C PID/output/stepgen limits loaded, B/C command and feedback matched at idle, and both SSI data-invalid pins were `FALSE`.

# 2026-04-11 - SSI feedback test confirmed B/C motion

- User confirmed motion on both B and C axes in the SSI feedback test config after the conservative B/C limits were applied.
- Live HAL snapshot after motion:
  - B enabled `TRUE`, command `1.103569 deg`, SSI feedback `1.103746 deg`, f-error approx `-0.000177 deg`, `joint.3.f-errored = FALSE`, `pid.b.output` approx `0.008313 deg/s`
  - C enabled `TRUE`, command `0.929413 deg`, SSI feedback `0.929695 deg`, f-error approx `0.000061 deg`, `joint.4.f-errored = FALSE`, `pid.c.output` approx `0.003036 deg/s`
  - B/C SSI `data-invalid` pins were both `FALSE`
- This confirms the SSI closed-loop feedback test config can move B and C under the current conservative settings. Continue using tiny moves while verifying direction, scaling, and following-error behavior before increasing limits.

# 2026-04-11 - SSI feedback MDI check returned B/C to zero

- User completed MDI check and reported both B and C returned to zero satisfactorily.
- Final live HAL checkpoint after return to zero:
  - B command `0.011 deg`, SSI feedback `0.010950 deg`, f-error approx `-0.000293 deg`, `joint.3.f-errored = FALSE`, `pid.b.output` approx `0.002518 deg/s`
  - C command `0.005 deg`, SSI feedback `0.004784 deg`, f-error approx `0.000216 deg`, `joint.4.f-errored = FALSE`, `pid.c.output` approx `-0.006358 deg/s`
  - `motion.in-position = TRUE`
  - B/C SSI `data-invalid` pins both `FALSE`
- Current status: SSI feedback test config is working for conservative B/C MDI motion under the temporary low-speed/low-output limits.

# 2026-04-11 - SSI feedback test speeds bumped and B wrap normalized

- User asked to bump speeds up a bit after successful conservative MDI testing.
- Updated only the SSI feedback test config limits:
  - angular jog default `0.5 deg/s`, max `2 deg/s`
  - B/C axis and joint max velocity `2 deg/s`, max acceleration `6 deg/s^2`
  - B/C `STEPGEN_MAXVEL = 3`, `STEPGEN_MAXACCEL = 12`
  - B/C `MAX_OUTPUT = 2.0`, with `P = 50.0` unchanged
- After restart, B came up on the SSI wrap branch (`b-ssi-zeroed-position` approx `-363.205 deg`). Stopped LinuxCNC and added B wrap normalization matching the C below-`-180` branch handling.
- Relaunched after B wrap fix. Live HAL showed:
  - B raw zeroed branch approx `-363.205 deg`, normalized `b-pos-fb` approx `-3.205 deg`
  - C `c-pos-fb` approx `-3.242 deg`
  - joint 3/4 command and feedback matched, joint 3/4 f-errored `FALSE`
  - B/C PID maxoutput loaded as `2`, SSI data-invalid pins both `FALSE`

# 2026-04-11 - SSI feedback test speeds bumped to 4 deg/s

- User reported the `2 deg/s` feedback-test setup still looked good and asked to bump speeds again.
- Updated only the SSI feedback test config limits:
  - angular jog default `1 deg/s`, max `4 deg/s`
  - B/C axis and joint max velocity `4 deg/s`, max acceleration `12 deg/s^2`
  - B/C `STEPGEN_MAXVEL = 6`, `STEPGEN_MAXACCEL = 24`
  - B/C `MAX_OUTPUT = 4.0`, with `P = 50.0` unchanged
  - B/C following-error windows unchanged at `FERROR = 2`, `MIN_FERROR = 0.5`
- Relaunched feedback-test config. AXIS reported angular jog max `4 deg/s`, default `1 deg/s`. Live HAL confirmed B/C PID maxoutput `4`, stepgen maxvel `6`, stepgen maxaccel `24`, B/C near zero, no B/C f-error, and both SSI data-invalid pins `FALSE`.

# 2026-04-11 - SSI feedback test speeds bumped to 8 deg/s

- User reported the `4 deg/s` feedback-test setup still looked good and asked to bump speeds again.
- Updated only the SSI feedback test config limits:
  - angular jog default `2 deg/s`, max `8 deg/s`
  - B/C axis and joint max velocity `8 deg/s`, max acceleration `24 deg/s^2`
  - B/C `STEPGEN_MAXVEL = 12`, `STEPGEN_MAXACCEL = 48`
  - B/C `MAX_OUTPUT = 8.0`, with `P = 50.0` unchanged
  - B/C following-error windows unchanged at `FERROR = 2`, `MIN_FERROR = 0.5`
- Relaunched feedback-test config. AXIS reported angular jog max `8 deg/s`, default `2 deg/s`. Live HAL confirmed B/C PID maxoutput `8`, stepgen maxvel `12`, stepgen maxaccel `48`, B/C command and feedback matched near zero, no B/C f-error, and both SSI data-invalid pins `FALSE`.

# 2026-04-11 - SSI feedback test ready for live program testing

- User reported current B/C motion looks good at the `8 deg/s` SSI feedback test settings and noted the real test will be live programs.
- Current comparison to locked maintenance/original config:
  - commanded angular max and B/C joint max velocity are `8 deg/s` vs original `10 deg/s` (`80%`)
  - B/C joint max acceleration is `24 deg/s^2` vs original `30 deg/s^2` (`80%`)
  - correction loop is still softer/capped: B/C `P = 50` vs original `1000`, B/C `MAX_OUTPUT = 8`, B `STEPGEN_MAXVEL = 12` vs original `65`, C `STEPGEN_MAXVEL = 12` vs original `50`
- Live checkpoint after current motion looked good:
  - B command `-0.011 deg`, SSI feedback `-0.011023 deg`, f-error approx `0.000023 deg`, `joint.3.f-errored = FALSE`, `pid.b.output` approx `0.001151 deg/s`
  - C command `0.005 deg`, SSI feedback `0.004784 deg`, f-error approx `-0.000127 deg`, `joint.4.f-errored = FALSE`, `pid.c.output` approx `-0.006358 deg/s`
  - B/C SSI `data-invalid` pins both `FALSE`, `motion.in-position = TRUE`
- Remaining caveat: jogging/MDI validates basic feedback direction and stability, but live programs still need testing for coordinated motion, blending, reversals, and larger B/C moves.

# 2026-04-11 - Locked XYZBC SSI maintenance config

- User asked to lock the current working SSI feedback state as a maintenance XYZBC-SSI config.
- Created separate locked config copy:
  - `configs/5th_axis_xyzbc_ssi_maintenance/`
  - launcher: `configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh`
  - INI: `5th_axis_xyzbc_ssi_maintenance.ini`
  - HAL: `5th_axis_xyzbc_ssi_maintenance.hal`
  - VAR: `5th_axis_xyzbc_ssi_maintenance.var`
- This locked maintenance-SSI config preserves the validated current state:
  - B/C SSI feedback routed to `joint.3/4.motor-pos-fb` and `pid.b/c.feedback`
  - B/C below-`-180` startup wrap normalization
  - C SSI display/feedback scale `c_ssi_axis_scale.in1 = -1.0`
  - angular jog default `2 deg/s`, max `8 deg/s`
  - B/C max velocity `8 deg/s`, max acceleration `24 deg/s^2`
  - B/C `STEPGEN_MAXVEL = 12`, `STEPGEN_MAXACCEL = 48`
  - B/C `P = 50.0`, `MAX_OUTPUT = 8.0`
  - B/C following-error windows `FERROR = 2`, `MIN_FERROR = 0.5`
- Existing configs remain intact:
  - no-SSI fallback: `configs/5th_axis_xyzbc_maintenance/`
  - dev/test source: `configs/5th_axis_xyzbc_ssi_feedback_test/`
- Static checks performed on the new maintenance-SSI copy:
  - `bash -n launch_xyzbc_ssi_maintenance.sh` passed
  - PyVCP XML parse check passed for `encoder_alignment.xml`
  - grep confirmed new INI references `5th_axis_xyzbc_ssi_maintenance` machine, preference, parameter, and HAL files
  - grep confirmed B/C SSI feedback and wrap-normalization links in the new HAL
- Did not launch the new locked maintenance-SSI copy yet; the currently running LinuxCNC session was left undisturbed.

# 2026-04-11 - Pause handoff and power-loss checkpoint

- User paused the task for a few hours and requested notes, session details, commit, and push in case of PC power loss.
- Current machine/control status before shutdown:
  - LinuxCNC was running from `configs/5th_axis_xyzbc_ssi_feedback_test/launch_xyzbc_ssi_feedback_test.sh` with the same settings now locked into `configs/5th_axis_xyzbc_ssi_maintenance/`.
  - Live HAL snapshot: B command `-0.010680 deg`, B SSI feedback `-0.010336 deg`, B f-error `0`, `joint.3.f-errored = FALSE`, `pid.b.output = 0`.
  - Live HAL snapshot: C command `-0.005173 deg`, C SSI feedback `-0.005173 deg`, C f-error `0`, `joint.4.f-errored = FALSE`, `pid.c.output = 0`.
  - B/C SSI `data-invalid` pins were both `FALSE`; `motion.in-position = TRUE`.
- Locked working baseline configs for resume:
  - no-SSI fallback maintenance: `configs/5th_axis_xyzbc_maintenance/`
  - SSI closed-loop maintenance baseline: `configs/5th_axis_xyzbc_ssi_maintenance/`
  - SSI development/test source: `configs/5th_axis_xyzbc_ssi_feedback_test/`
- Current SSI maintenance baseline details:
  - B/C SSI feedback feeds `joint.3/4.motor-pos-fb` and `pid.b/c.feedback`.
  - B/C have below-`-180` startup wrap normalization.
  - C SSI feedback/display scale is `c_ssi_axis_scale.in1 = -1.0`.
  - angular jog default `2 deg/s`, max `8 deg/s`.
  - B/C max velocity `8 deg/s`, max acceleration `24 deg/s^2`.
  - B/C `STEPGEN_MAXVEL = 12`, `STEPGEN_MAXACCEL = 48`, `P = 50.0`, `MAX_OUTPUT = 8.0`.
  - B/C following-error windows are `FERROR = 2`, `MIN_FERROR = 0.5`.
- Next planned phase after pause: create/use a new TCP calibration config copied from `configs/5th_axis_xyzbc_ssi_maintenance/`, wire/validate the wireless touch probe, and use the 30 mm sphere to collect logged probe data for B/C zero and TCP pivot/offset solving.
- Suggested calibration approach: G-code programs should perform safe, repeatable probing and log data; offline Python should calculate B/C zero corrections and TCP offsets from the logged sphere-center data.

# 2026-04-11 - LinuxCNC shutdown before pause

- After the pause checkpoint, stopped the running LinuxCNC session that had been launched from `configs/5th_axis_xyzbc_ssi_feedback_test/launch_xyzbc_ssi_feedback_test.sh`.
- Shutdown completed cleanly at the HAL/HostMot2 level: shutdown script ran, `hm2_eth` reset/unloaded, and HostMot2 unloaded.
- No LinuxCNC/milltask/AXIS/HALUI/XHC processes were left running after shutdown.

# 2026-04-11 - End-of-day lock-in and next-session plan

- User finished for the day and asked to lock in progress, current status, and planning for the next session.
- Current working machine baseline is the AXIS-based SSI maintenance config, not Probe Basic:
  - `configs/5th_axis_xyzbc_ssi_maintenance/`
  - launcher: `configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh`
- Reason for using AXIS now: maintenance work needed to release/bypass the homing requirement; Probe Basic work is paused and will be revisited later.
- Locked baselines available for resume:
  - no-SSI maintenance fallback: `configs/5th_axis_xyzbc_maintenance/`
  - SSI closed-loop maintenance baseline: `configs/5th_axis_xyzbc_ssi_maintenance/`
  - SSI dev/test source config: `configs/5th_axis_xyzbc_ssi_feedback_test/`
- Current machine status at end of day:
  - LinuxCNC was shut down cleanly after the pause checkpoint.
  - No LinuxCNC/milltask/AXIS/HALUI/XHC/HostMot2 processes were left running.
  - Last live B/C state before shutdown was in-position, SSI data valid on both channels, and no B/C following-error flags.
- Current SSI maintenance baseline summary:
  - B/C SSI feedback feeds `joint.3/4.motor-pos-fb` and `pid.b/c.feedback`.
  - B/C below-`-180` startup wrap normalization is active.
  - C SSI feedback/display scale is `c_ssi_axis_scale.in1 = -1.0`.
  - angular jog default `2 deg/s`, max `8 deg/s`.
  - B/C max velocity `8 deg/s`, max acceleration `24 deg/s^2`.
  - B/C `STEPGEN_MAXVEL = 12`, `STEPGEN_MAXACCEL = 48`, `P = 50.0`, `MAX_OUTPUT = 8.0`.
  - B/C following-error windows are `FERROR = 2`, `MIN_FERROR = 0.5`.
- Next session plan:
  - Start by launching the locked SSI maintenance config if machine motion needs to be rechecked.
  - Create a new TCP/probe calibration config copied from `configs/5th_axis_xyzbc_ssi_maintenance/`; do not edit the locked maintenance baseline directly.
  - Working name for the new config: `configs/5th_axis_xyzbc_tcp_calibration/`.
  - Add/validate wireless touch probe input into `motion.probe-input`.
  - Use the 30 mm sphere as the calibration artifact.
  - Write G-code routines for safe repeatable probing and CSV-style logging; use offline Python to calculate B/C zero corrections and TCP offsets.
  - Account for probe length and spindle/C-axis non-concentricity in the offline geometry model rather than assuming the spindle is concentric to C.
  - Keep Probe Basic migration as a later task after the calibration/maintenance path is stable.

# 2026-04-15 - Shutdown/restart context checkpoint

- User is shutting down the PC soon and asked to save memory/context for restart.
- Latest pushed branch: `head-head-kinematics-rnd-pushable` on remote `alj333`, latest commit `b79afff637 Document XYZBC SSI calibration handoff`.
- LinuxCNC is not running; process check found no `linuxcnc`, `milltask`, `axis`, `halui`, `xhc`, or HostMot2 processes.
- Resume baseline: `configs/5th_axis_xyzbc_ssi_maintenance/` using launcher `configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh`.
- This AXIS-based maintenance config is the locked basic fully functional XYZBC machine setup with B/C SSI closed-loop feedback. Probe Basic work remains paused because AXIS was needed to bypass/release homing requirements for maintenance work.
- Keep the locked maintenance config stable. For the next phase, create a new config copied from it, planned as `configs/5th_axis_xyzbc_tcp_calibration/`.
- Next phase goal: calibrate B/C zero points and solve TCP/pivot offsets using the wireless touch probe and 30 mm sphere.
- Calibration approach: G-code routines should move/probe safely and log data; offline Python should solve corrections. Account for probe length and the spindle not being concentric with the C axis.
- Known unrelated dirty/untracked files remain in the worktree, mainly older Probe Basic/sim/runtime files. Do not treat them as part of the locked XYZBC SSI maintenance baseline unless explicitly requested.

# 2026-04-21 - XYZ homing locked into SSI maintenance baseline

- Relaunched `configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh` after power loss and recovered the live maintenance session.
- Verified live X/Y/Z home input wiring in the SSI maintenance config:
  - `hm2_7i95.0.inmux.00.input-00 -> home-x -> joint.0.home-sw-in`
  - `hm2_7i95.0.inmux.00.input-01 -> home-y -> joint.1.home-sw-in`
  - `hm2_7i95.0.inmux.00.input-02 -> home-z -> joint.2.home-sw-in`
- Confirmed live behavior during check:
  - initial read showed X/Y/Z home inputs inactive
  - subsequent live check showed all three asserted `TRUE` together at the HAL signal and joint home-switch pins
- Enabled X/Y/Z homing in the locked SSI maintenance INI to match the working `configs/5th_axis/5th_axis.ini` baseline:
  - X / `JOINT_0`: `HOME_OFFSET=-10`, `HOME_SEARCH_VEL=-20`, `HOME_LATCH_VEL=0.2`, `HOME_FINAL_VEL=10`, `HOME_USE_INDEX=YES`, `HOME_INDEX_NO_ENCODER_RESET=YES`, `HOME_SEQUENCE=1`
  - Y / `JOINT_1`: `HOME_OFFSET=-10`, `HOME_SEARCH_VEL=-20`, `HOME_LATCH_VEL=0.2`, `HOME_FINAL_VEL=20`, `HOME_USE_INDEX=YES`, `HOME_INDEX_NO_ENCODER_RESET=YES`, `HOME_SEQUENCE=1`
  - Z / `JOINT_2`: `HOME_OFFSET=10`, `HOME_SEARCH_VEL=20`, `HOME_LATCH_VEL=-0.2`, `HOME_FINAL_VEL=20`, `HOME_USE_INDEX=YES`, `HOME_INDEX_NO_ENCODER_RESET=YES`, `HOME_SEQUENCE=0`
- No HAL changes were needed for X/Y/Z homing; the SSI maintenance HAL already had the `home-sw-in` and encoder `index-enable` links.
- Restarted the SSI maintenance session after the INI edit so the new homing settings are now the active locked baseline.

# 2026-04-21 - SSI maintenance baseline refined and restarted

- Tightened the parked B/C zero reference in the locked SSI maintenance HAL by adjusting the SSI zero constants:
  - `b_ssi_zero.in1 = -182.0335`
  - `c_ssi_zero.in1 = -178.9192`
- Verified after restart that the parked `B0 C0` state now lands essentially on zero:
  - `joint.3.pos-cmd = 0`, `joint.3.pos-fb = 0`
  - `joint.4.pos-cmd = 0`, `joint.4.pos-fb = 0`
  - residual motor-space offsets were approximately `-0.00034` on B and `-0.00036` on C
  - `pid.b.error = 0`, `pid.c.error = 0`
- This confirmed the earlier `~0.130 / ~0.128` discrepancy at parked `B0 C0` was an encoder-zero issue, not a servo stiffness/tuning problem.

- Updated the locked SSI maintenance travel limits to match the desired current machine envelope:
  - X axis/joint: `-10` to `3350.01`
  - Y axis/joint: `-10` to `1730.01`
  - Z axis: `-900.01` to `0`
  - Z joint: `-900.01` to `10`
  - B axis/joint: `-100` to `100`
  - C axis/joint: `-359` to `359`

- CNC control power was later cycled while LinuxCNC was still running.
- The stale pre-cycle session then showed the expected live-fault symptoms:
  - HostMot2 read errors
  - joint 4 following error
- Shut that stale session down and relaunched `configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh`.
- Current status after the clean relaunch:
  - Mesa at `10.10.10.10` is reachable
  - AXIS, `halui`, `milltask`, and the SSI maintenance config are running again
  - startup only showed the usual `hm2_eth` `iptables` warning
  - the locked SSI maintenance baseline now includes:
    X/Y/Z homing, corrected B/C zero offsets, and the revised X/Y/Z/B/C limits

# 2026-04-21 - B manual zero calibration

- User manually calibrated the physical B axis and requested that the current pose become the new `B0`.
- Checked the live SSI maintenance session and confirmed this required another B encoder-zero adjustment, not PID tuning.
- Updated the locked SSI maintenance HAL B zero constant in `configs/5th_axis_xyzbc_ssi_maintenance/5th_axis_xyzbc_ssi_maintenance.hal`:
  - final value: `b_ssi_zero.in1 = -182.9921`
- Restarted LinuxCNC to load the new B zero reference.
- Verified after restart that the current physical B pose now lands essentially on zero:
  - `joint.3.pos-cmd = -0.000042`
  - `joint.3.pos-fb = -0.000042`
  - `joint.3.motor-pos-cmd = -0.000042`
  - `joint.3.motor-pos-fb = -0.000042`
  - `pid.b.error = 0`
- Result: the manual-calibrated B position is now the effective `B0` reference in the locked SSI maintenance baseline.

# 2026-04-21 - C manual zero calibration and end-of-day state

- User manually calibrated the physical C axis and requested that the current pose become the new `C0`.
- Checked the live SSI maintenance session and confirmed this required another C encoder-zero adjustment, not PID tuning.
- Updated the locked SSI maintenance HAL C zero constant in `configs/5th_axis_xyzbc_ssi_maintenance/5th_axis_xyzbc_ssi_maintenance.hal`:
  - final value: `c_ssi_zero.in1 = -180.8538`
- Restarted LinuxCNC to load the new C zero reference.
- Verified after restart that the current physical C pose now lands essentially on zero:
  - `joint.4.pos-cmd = -0.000044`
  - `joint.4.pos-fb = -0.000044`
  - `joint.4.motor-pos-cmd = -0.000044`
  - `joint.4.motor-pos-fb = -0.000044`
  - `pid.c.error = 0`
- Result: the manual-calibrated C position is now the effective `C0` reference in the locked SSI maintenance baseline.

- End-of-day resume state:
  - active branch: `head-head-kinematics-rnd-pushable`
  - resume launcher: `configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh`
  - LinuxCNC was left running in the locked SSI maintenance config at end of session
  - locked SSI maintenance baseline now includes:
    X/Y/Z homing enabled, corrected B/C zero references, and the current X/Y/Z/B/C limits
  - latest locked B/C zero constants:
    `b_ssi_zero.in1 = -182.9921`
    `c_ssi_zero.in1 = -180.8538`

# 2026-04-22 - Rotary zero refinement and probe wiring

- Fine-tuned the live parked rotary reference again so the current physical pose became the effective `B0 C0`.
- Final locked SSI maintenance rotary zero constants in `configs/5th_axis_xyzbc_ssi_maintenance/5th_axis_xyzbc_ssi_maintenance.hal` are now:
  - `b_ssi_zero.in1 = -182.9152`
  - `c_ssi_zero.in1 = -180.8703`
- Verified after the final restart that the parked rotary readback is essentially zero:
  - `joint.3.pos-fb = -0.000046`
  - `joint.4.pos-fb = -0.000023`
  - `pid.b.error = 0`
  - `pid.c.error = 0`

- Ported the known-good probe wiring pattern from the machine-style `5th_axis` config into the locked SSI maintenance config.
- Added `or2`-based probe mux wiring in `configs/5th_axis_xyzbc_ssi_maintenance/5th_axis_xyzbc_ssi_maintenance.hal`:
  - `input-09` wired as `t_probe-in`
  - `input-08` wired as `toolset-in`
  - `probe-mux` wired to both `motion.probe-input` and `hm2_7i95.0.ssr.00.out-02`
- Restarted LinuxCNC and verified the live HAL path exists:
  - `t_probe-in`
  - `toolset-in`
  - `probe-mux`
  - `motion.probe-input`
- User then manually triggered the touch probe and confirmed the signal flashes in Halshow, which verifies the live probe signal is reaching the SSI maintenance HAL path.

# 2026-04-22 - Locked baseline and next UI direction

- Current locked machine baseline remains `configs/5th_axis_xyzbc_ssi_maintenance/`.
- This SSI maintenance config is now the source baseline for the next UI/config migration work.
- Next configuration task:
  - create a new config copied from the locked SSI maintenance baseline
  - move probing and calibration work into a Probe Basic-based UI config
- Operational UI direction for this machine:
  - Probe Basic `Mill ATC metric` will be the production/operator-facing UI
  - the current AXIS SSI maintenance config remains the locked maintenance fallback/baseline
- Immediate next work planned from this point:
  - perform mechanical alignment checks
  - then begin TCPC calibration work using the Probe Basic-based calibration workflow

# 2026-04-22 - Probe Basic calibration config created from the locked SSI baseline

- Created a new config directory: `configs/5th_axis_xyzbc_ssi_probe_basic/`.
- The new config is copied from the locked `configs/5th_axis_xyzbc_ssi_maintenance/` machine baseline, then converted to Probe Basic while preserving the validated machine core:
  - same `XYZBC` trivkins machine layout
  - same X/Y/Z homing values
  - same X/Y/Z/B/C limits
  - same B/C SSI zero constants and wrap-normalized feedback path
  - same probe wiring into `motion.probe-input`
  - same pendant and manual tool-release machine HAL behavior
- Added the Probe Basic support layer locally in the new config:
  - `DISPLAY = probe_basic`
  - local `custom_config.yml`
  - local `probe_basic_postgui.hal`
  - local `pbsplash.png`
  - local `python/`, `subroutines/`, `remap_subs/`, `user_buttons/`, `user_dro_display/`, and `user_tabs/`
  - dedicated launcher: `configs/5th_axis_xyzbc_ssi_probe_basic/launch_xyzbc_ssi_probe_basic.sh`
- Adjusted the new config HAL to export Probe Basic manual-tool-change nets:
  - `tool-change-request`
  - `tool-change-confirmed`
  - `tool-number`
- First Probe Basic launch failed because `probe_basic_postgui.hal` tried to `loadrt not` even though the machine HAL already had a `not` component loaded for the spindle/tool-release interlock.
- Fixed the postgui file by removing that duplicate realtime load and driving the cycle timer from the existing `pdnt.program-is-running` signal instead.
- Relaunched the new Probe Basic config and verified from the LinuxCNC and QtPyVCP logs that:
  - LinuxCNC reached `DISPLAY = probe_basic`
  - QtPyVCP loaded the Probe Basic UI and postgui HAL
  - the VTK backplot initialized
- Verified live HAL wiring in the running Probe Basic session:
  - `motion.probe-input <== probe-mux`
  - `probe-mux ==> hm2_7i95.0.ssr.00.out-02 ==> motion.probe-input <== or2.0.out ==> qtpyvcp.probe-led.on`
- Current role split is now explicit:
  - `configs/5th_axis_xyzbc_ssi_maintenance/` remains the locked AXIS maintenance fallback
  - `configs/5th_axis_xyzbc_ssi_probe_basic/` is the active Probe Basic calibration/probing config for the next TCPC phase
- TCPC/TWP remaps are still not enabled in this new config yet; this build is the UI and probing/calibration migration step before the TCPC integration pass.
