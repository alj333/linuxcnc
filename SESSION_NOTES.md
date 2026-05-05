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

# 2026-04-23 - Probe Basic SSI operating baseline updates

- Probe Basic probe calibration value `0.096025` is now operationally locked in through the Probe Basic settings layer and startup sync path.
- The SSI Probe Basic config now has live spindle output wiring matching the older machine config pattern:
  - spindle enable wired to `hm2_7i95.0.ssr.00.out-00`
  - spindle PWM command wired to `hm2_7i95.0.pwmgen.00`
  - `spindle.0.at-speed` is still forced true because real spindle RPM feedback is not yet wired
- Flood/M8 in the SSI Probe Basic config now drives spindle air on `hm2_7i95.0.ssr.00.out-03`.
- Verified at the machine that the spindle output path works and that flood air works.
- Important launch behavior for this config:
  - Probe Basic/LinuxCNC must be fully shut down before relaunch
  - duplicate desktop-side sessions will stack and cause UI lock/slow behavior if the previous session is not completely cleared first
- For a short 3-axis task, the current SSI Probe Basic config was temporarily raised from the earlier slow calibration-safe limits.
- Current loaded 3-axis motion settings in `configs/5th_axis_xyzbc_ssi_probe_basic/5th_axis_xyzbc_ssi_probe_basic.ini` are now:
  - `[TRAJ] MAX_LINEAR_VELOCITY = 240` (`60%` of the original `5th_axis` `400`)
  - X: `MAX_VELOCITY = 150`, `MAX_ACCELERATION = 300`
  - Y: `MAX_VELOCITY = 150`, `MAX_ACCELERATION = 300`
  - Z: `MAX_VELOCITY = 150`, `MAX_ACCELERATION = 300`
- After a clean restart, LinuxCNC reported the Probe Basic SSI session back in `ON/IDLE` with live `max_velocity = 240.0`.

# 2026-04-23 - Probe Basic SSI spindle calibration and RPM cap

- The Probe Basic SSI spindle path remains open-loop analog/PWM control. There is still no real spindle RPM feedback wired into LinuxCNC.
- Spindle speed behavior was checked against external tach readings and did not match a simple linear scale:
  - earlier checks showed `S1000 -> 1350`, `S10000 -> 3920`, and `S15000 -> 12000`
  - after the first software correction pass, follow-up checks showed approximately `1070`, `2440`, `5160`, `8700` across the tested range
- Because the spindle response was clearly non-linear, the direct `spindle.0.speed-out-abs -> pwmgen` mapping in `configs/5th_axis_xyzbc_ssi_probe_basic/5th_axis_xyzbc_ssi_probe_basic.hal` was replaced with a piecewise open-loop correction block built from HAL `scale`, `comp`, `mux2`, and `limit1` components.
- The current machine-specific spindle correction is now parameterized in `configs/5th_axis_xyzbc_ssi_probe_basic/5th_axis_xyzbc_ssi_probe_basic.ini` under `[SPINDLE_0]`:
  - `CAL_LOW_BREAK_RPM = 1070`
  - `CAL_MID_BREAK_RPM = 2440`
  - `CAL_HIGH_BREAK_RPM = 5160`
  - `CAL_LOW_GAIN = 0.6922810661`
  - `CAL_LOWMID_GAIN = 4.4069119534`
  - `CAL_MIDHIGH_GAIN = 1.6576906607`
  - `CAL_HIGH_GAIN = 0.6992224644`
  - with matching offsets and a corrected-command clamp of `CAL_MAX_COMMAND_RPM = 15000`
- Added an explicit requested-speed clamp ahead of the spindle correction map:
  - `[SPINDLE_0] MAX_RPM = 10000`
  - live HAL verification showed `spindle_target_limit.max = 10000`
- Operationally, the spindle should now be treated as capped at `10000 RPM` in this Probe Basic SSI config until further tach-based tuning or real spindle feedback is added.

# 2026-04-26 - Resume context

- Current active operator/config baseline remains `configs/5th_axis_xyzbc_ssi_probe_basic/`.
- Current locked fallback baseline remains `configs/5th_axis_xyzbc_ssi_maintenance/`.
- Latest pushed machine-config commit is `4eb66d790a` (`Calibrate SSI Probe Basic spindle map`).
- Current Probe Basic SSI baseline includes:
  - X/Y/Z homing enabled
  - B/C SSI-based rotary feedback path
  - probe wiring live through `motion.probe-input`
  - spindle enable/PWM wiring live
  - flood/M8 driving spindle air
  - open-loop spindle calibration map with requested spindle cap at `10000 RPM`
  - temporary faster 3-axis motion limits for short 3-axis work:
    - `[TRAJ] MAX_LINEAR_VELOCITY = 240`
    - X/Y/Z `MAX_VELOCITY = 150`
    - X/Y/Z `MAX_ACCELERATION = 300`
- Probe Basic/LinuxCNC should still be fully shut down before relaunch to avoid duplicate desktop-side sessions and UI lock/slow behavior.
- Current operator intent is to leave Probe Basic running in the SSI Probe Basic config; do not shut it down unless explicitly requested.
- Current next intent from the operator session:
  - refresh Codex context
  - then update the local Codex program/environment before continuing machine work

# 2026-04-26 - TCPC calibration target clarified

- Machine context:
  - large steel CNC machine
  - no temperature compensation yet; that is a future project
  - most 5-axis work target is vacuum-formed part cutout
- Practical TCPC acceptance target is about `0.10 mm`.
- Calibration strategy should avoid overfitting below the current thermal/mechanical envelope.
- Prioritize repeatable safe TCPC behavior across practical B/C poses over single-digit micron fixed-tip results.
- Small mechanical errors, backlash, and compliance are expected and will be refined in future work.
- Current TCPC calibration should focus on the dominant rotary/tool geometry and avoid using geometry offsets to mask small mechanical imperfections.

# 2026-04-26 - Probe calibration offset updated

- User repeated the 50.001 mm calibration-ring probe calibration multiple times.
- Current consistent probe calibration offset is `0.134533`.
- This supersedes the earlier `0.096025` probe calibration value for the active TCPC calibration session.
- Before sphere-center capture, ensure Probe Basic shows calibration offset `0.134533` and press `UPDATE PROBE PARAMS` so `#3032` matches the accepted value.
- For calibration probing tasks, use `50 mm/min` slow probe, `100 mm/min` fast probe, and keep traverse/transfer moves at or below `300 mm/min` while setting up and testing.
- Probe Basic has no native sphere calibration workflow. The 30 mm sphere cycle is custom and should only borrow Probe Basic setup values that explicitly map to the custom cycle.

# 2026-04-26 - 30 mm sphere test pass

- First loose-sphere `B0 C0` test pass completed successfully as a motion-validation run only.
- Logged test result:
  - relative center `X=-2.007917 Y=-1.207917 Z=104.777029`
  - absolute center `X=306.333197 Y=352.762646 Z=-280.900367`
  - measured side diameters `X=29.709767 Y=29.704766`
  - top contact `Z=122.642496`
- The large Probe Basic production clearance was confirmed to be inappropriate for the sphere cycle: startup values included `xy_clearance=20`, causing a `20 mm` retract and up to `40 mm` slow re-probe distance on each side.
- `nc_files/calibration/30mm_sphere_measure_current_pose.ngc` now caps sphere-cycle `xy_clearance` at `2.0 mm` while leaving normal Probe Basic saved settings unchanged.
- After the test pass, LinuxCNC returned to `G54` because the config startup modal includes `G54`. The operator has saved the old project offsets and is willing to use `G54` as the calibration WCS for the current session if it reduces workflow friction.
- Keep the sphere wrapper WCS-neutral: do not force `G54` or `G55` in the file; use whichever WCS the operator deliberately sets before the run.

# 2026-04-26 - Secured B0 C0 sphere baseline

- Three secured `B0 C0` sphere runs completed after the loose motion-validation pass.
- Secured-run baseline average:
  - absolute center `X=306.368475 Y=352.795840 Z=-280.750222`
  - measured side diameters `X=29.771711 Y=29.674210`
- Secured-run repeatability range:
  - absolute center `X=0.001667 Y=0.001667 Z=0.000900`
  - measured side diameters `X=0.004999 Y=0.002500`
- This is comfortably inside the practical `0.10 mm` TCPC target and is good enough as the first `B0 C0` baseline for the C-axis sweep.

# 2026-04-26 - C sweep started

- First `B0 C90` sphere run completed.
- Result:
  - absolute center `X=278.915280 Y=326.726812 Z=-280.758967`
  - measured side diameters `X=29.766434 Y=29.691433`
- Delta from secured `B0 C0` baseline average:
  - `dX=-27.453195 dY=-26.069028 dZ=-0.008745`
- This is the first C-axis geometry signal; continue with `B0 C180`, `B0 C270`, then repeat `B0 C0`.
- `B0 C180` sphere run completed.
- Result:
  - absolute center `X=305.047781 Y=299.355562 Z=-280.737367`
  - measured side diameters `X=29.767267 Y=29.698099`
- Delta from secured `B0 C0` baseline average:
  - `dX=-1.320694 dY=-53.440278 dZ=+0.012855`
- `B0 C270` sphere run completed.
- Result:
  - absolute center `X=332.451531 Y=325.422646 Z=-280.749100`
  - measured side diameters `X=29.606434 Y=29.683100`
- Delta from secured `B0 C0` baseline average:
  - `dX=+26.083056 dY=-27.373194 dZ=+0.001122`
- Note: C270 X side diameter is about `0.16 mm` lower than the other C-sweep side diameters. After the closing `B0 C0` repeat, consider repeating C270 once to distinguish measurement/contact error from geometry.
- Closing `B0 C0` sphere run completed after the C sweep.
- Result:
  - absolute center `X=306.377781 Y=352.791396 Z=-280.769167`
  - measured side diameters `X=29.773100 Y=29.681433`
- Delta from secured `B0 C0` baseline average:
  - `dX=+0.009306 dY=-0.004444 dZ=-0.018945`
- C sweep closure is good enough for the current `0.10 mm` TCPC target.
- Updated `probe_sphere_center.ngc` to probe sphere sides at `sphere_center_z + 1.5 mm` instead of `+3.0 mm`. Reload the program before the next run.
- Added `nc_files/calibration/30mm_sphere_c_sweep_b0_auto.ngc` for an automatic `B0 C0/C90/C180/C270/C0` sweep.
- The auto sweep uses measured X/Y hints from the first sweep and does not assume machine alignment is correct.
- The auto sweep is WCS-neutral, indexes B/C at `F300`, caps probe traverse at `300`, and appends each pose to `sphere-center-results.csv`.
- After the first auto sweep, operator confirmed the extra `25 mm` lift before C indexing is not required. `#<index_retract_z>` in the auto sweep was changed to `0.0`; the routine now relies on the sphere subroutine's normal top-clearance position.

# 2026-04-26 - Auto C sweep with +1.5 mm side height

- First automatic `B0 C0/C90/C180/C270/C0` sweep completed using side probe height `sphere_center_z + 1.5`.
- Auto-sweep baseline row:
  - `B0 C0`: `X=306.364864 Y=352.810563 Z=-280.754300`, diameters `X=30.165601 Y=30.068100`
- Auto-sweep deltas from the first auto `B0 C0` row:
  - `B0 C90`: `dX=-27.449584 dY=-26.058751 dZ=+0.019933`, diameters `X=30.150600 Y=30.077266`
  - `B0 C180`: `dX=-1.301666 dY=-53.438751 dZ=+0.034867`, diameters `X=30.168100 Y=30.081433`
  - `B0 C270`: `dX=+26.081667 dY=-27.362084 dZ=+0.012300`, diameters `X=30.010600 Y=30.070600`
  - closing `B0 C0`: `dX=+0.008750 dY=+0.005833 dZ=+0.000566`, diameters `X=30.163100 Y=30.064766`
- Closure is good in X/Y/Z for the current practical target.

# 2026-04-26 - Linear-axis error caution

- Operator noted that at least one linear axis uses a rack drive and may have tight/loose points; Y/Z ball-screw behavior may also contribute local position error.
- Treat rack/screw pitch, backlash, straightness, and local tight spots as separate machine-error sources from TCPC rotary geometry.
- Do not overfit C/B pivot offsets to cancel local linear-axis error from one table position.
- For current TCPC work, use repeated measurements at the same physical sphere location and consistent approach directions where possible.
- Later machine-alignment work should add dedicated probing routines for bidirectional repeatability, local pitch/rack error, squareness, backlash, and rotary runout.

# 2026-04-26 - B-axis vector probing preparation

- Operator confirmed the hard part for the head-head machine: at nonzero `B`, probing must move relative to the tilted head/probe vector, not fixed machine `Z`.
- The existing sphere center routine should be treated as `B0`-only for geometry data. It is not valid as the final B-axis calibration routine because it assumes machine-aligned top/side probing.
- Added `configs/5th_axis_xyzbc_ssi_probe_basic/B_AXIS_VECTOR_PROBING_PLAN.md`.
- Added `nc_files/calibration/b_axis_vector_dry_run_b0_c0.ngc` as the first
  non-contact B-axis vector sign check.
- The dry run:
  - makes no probe moves
  - writes no WCS offsets
  - indexes only `B0`, `B+15`, `B-15`, `B+30`, `B-30`, closing `B0`, all at
    `C0`
  - returns to the operator's starting `XYZ` before each vector check
  - uses short `3.0 mm` vector moves at `150 mm/min` and rotary indexing at
    `200 mm/min`
- Operator completed the vector dry run and reported that the small vector moves
  looked correct.
- Added `nc_files/calibration/b_axis_vector_top_touch_current_pose.ngc` for the
  first B-axis contact validation.
- The top-touch test is deliberately current-pose only:
  - it does not auto-index `B/C`
  - it does not write WCS offsets
  - it makes one slow `G38.2` touch along local `W`
  - it returns to the operator's starting `XYZ`
  - it logs to `b-axis-vector-results.csv`
- First `B+15 C0` vector top-touch test completed and looked correct to the
  operator.
- Logged top-touch result:
  - touch point `X=220.246198 Y=352.916396 Z=-274.362493`
  - estimated center from W/top contact
    `X=224.870121 Y=352.916396 Z=-291.619209`
- Added `nc_files/calibration/b_axis_vector_sphere_current_pose.ngc` for the
  first current-pose five-contact vector sphere measurement.
- The five-contact routine:
  - does not auto-index `B/C`
  - does not write WCS offsets
  - probes top along `W`, then side contacts from `-U/+U` and `-V/+V`
  - keeps probing at `50 mm/min` and transfer moves at `150 mm/min`
  - logs raw points to `b-axis-vector-raw-points.csv`
  - logs a rough current-pose center to `b-axis-vector-sphere-results.csv`
- `B+15 C0` five-contact routine status:
  - first pass confirmed the operator's concern: top-derived center was about
    `1.66 mm` off in local `U`
  - after jogging `+U` by about `1.66 mm`, the second and third passes repeated
    tightly
  - accepted repeat pair from passes 2 and 3:
    - pass 2 center `X=226.451909 Y=352.893271 Z=-291.112385`
    - pass 3 center `X=226.451756 Y=352.892855 Z=-291.111817`
    - pass 3 minus pass 2 center delta
      `dX=-0.000153 dY=-0.000416 dZ=+0.000568`
    - corrected diameters repeated at about `U=30.107 mm`,
      `V=30.207-30.209 mm`
  - current-pose repeatability is good enough to proceed to `B-15 C0`, but the
    initial centering must be corrected manually or by a future auto-centering
    pass before trusting a full B sweep.
- Next implementation should start with a vector dry-run:
  - define local `W` as the probe/tool vector at commanded `B/C`
  - define local `U/V` perpendicular side-probe vectors
  - verify signs with short non-contact vector moves before any probing
  - then log raw trigger points and fit sphere centers offline
- Initial B data should start conservatively at `B0`, `B+15`, `B-15`, `B+30`, `B-30`, closing `B0`, all at `C0`, before widening the tilt range.
- Do not enable TCPC/TWP until vector signs, raw contact data, and fit residuals are understood.

# 2026-04-26 - End-of-day B-axis vector checkpoint

- Operator is stopping for the day and intends to leave the current Probe
  Basic/LinuxCNC session running. No shutdown or machine command was issued by
  Codex.
- Current live context if power is lost:
  - active calibration config remains
    `configs/5th_axis_xyzbc_ssi_probe_basic/`
  - current probe calibration offset remains `0.134533`
  - B-axis vector probing has been validated at `B+15 C0` and `B-15 C0`
  - TCPC/TWP is still not enabled
  - current-pose vector sphere routine ends at top clearance, not at the
    original start position
- `B+15 C0` accepted repeat pair:
  - pass 2 center `X=226.451909 Y=352.893271 Z=-291.112385`
  - pass 3 center `X=226.451756 Y=352.892855 Z=-291.111817`
  - pass 3 minus pass 2 center delta
    `dX=-0.000153 dY=-0.000416 dZ=+0.000568`
  - corrected diameters repeated at about `U=30.107 mm`,
    `V=30.207-30.209 mm`
- `B-15 C0` data collected after the `B+15` repeat:
  - the full five-contact sphere routine was run directly at `B-15 C0` instead
    of the top-touch-only check; it completed cleanly
  - first `B-15 C0` pass center:
    `X=386.227701 Y=352.617855 Z=-291.477656`
  - first `B-15 C0` corrected diameters:
    `U=30.198675 mm`, `V=30.207167 mm`
  - first-pass local centering errors from side-pair midpoints:
    `U=-0.185417 mm`, `V=+0.202918 mm`
  - operator jogged approximately `X=-0.18`, `Y=+0.20`, `Z=+0.05` and reran
    the full current-pose routine
  - corrected `B-15 C0` pass center:
    `X=386.140321 Y=352.717855 Z=-291.445826`
  - corrected `B-15 C0` diameters:
    `U=30.202008 mm`, `V=30.210500 mm`
  - corrected local centering error is about `U=+0.001458 mm`,
    `V=+0.001459 mm`
- Important algorithm note:
  - the current single-pass result center in
    `b-axis-vector-sphere-results.csv` is a rough center from averaging U/V
    pair midpoints
  - the automatic two-pass routine should use the full U-pair midpoint error for
    local `U` and the full V-pair midpoint error for local `V`; do not halve the
    correction by averaging the pair midpoints
- Next safe implementation step:
  - add a new filename for a current-pose automatic two-pass vector sphere
    routine so Probe Basic reloads it cleanly
  - pass 1 should probe the five contacts, compute local `U/V` centering error,
    sanity-check the move, shift the start/clearance position internally, then
    run pass 2 automatically
  - do not write WCS offsets
  - do not auto-index `B/C` yet
  - keep probe moves at `50 mm/min` and transfers at `150 mm/min`
  - abort if either local correction is more than about `2.0 mm`
  - abort if either corrected diameter is outside about `29.5-30.5 mm`
  - log both pass 1 and pass 2, and treat pass 2 as the accepted result
- After the two-pass routine is implemented and validated, continue the B-axis
  pose set with `B+30 C0`, `B-30 C0`, and closing `B0 C0`.

# 2026-04-27 - B-axis two-pass routine prepared

- Added `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc`.
- Added two-pass result logs:
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-2pass-raw-points.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-2pass-results.csv`
- The two-pass routine is current-pose only:
  - no WCS writes
  - no `B/C` auto-indexing
  - no `G49`; active tool-length state is left unchanged
  - pass 1 probes top, `-U/+U`, and `-V/+V`
  - pass 1 computes full local `U/V` midpoint errors
  - pass 1 aborts before auto-correction if either local correction exceeds
    `2.0 mm`
  - pass 1 aborts before auto-correction if either corrected diameter is
    outside `29.5-30.5 mm`
  - pass 2 starts at top clearance above the corrected center and is marked as
    accepted in the two-pass result CSV
- Static checks completed:
  - no G-code line over `80` characters
  - `git diff --check` clean for the new routine and CSV headers
  - a parser pass on a temporary verification copy completed successfully after
    replacing live probe moves with feed moves and removing runtime abort guards
- Next live validation step:
  - do not go to `B+30 C0` yet
  - validate the new two-pass routine at a known pose first, preferably current
    `B-15 C0` if the machine has not been moved far
  - start `3-8 mm` clear along the opposite stylus vector
  - use Single Block for the first validation run
  - if pass 1 correction and pass 2 result look sane, then continue to
    `B+30 C0` with the two-pass routine

# 2026-04-27 - B-axis two-pass validation run

- First live validation of
  `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc` completed.
- Important: the validation log shows the run was at `B+15 C0`, not `B-15 C0`.
- Pass 1 result:
  - center `X=225.707563 Y=353.656813 Z=-291.478044`
  - local centering correction requested by the routine:
    `U=+1.692917 mm`, `V=-1.519167 mm`
  - corrected diameters `U=29.970342 mm`, `V=30.051333 mm`
  - both correction and diameter sanity checks passed
- Pass 2 accepted result after automatic internal recenter:
  - center `X=226.486276 Y=352.897855 Z=-291.117802`
  - remaining local centering error `U=-0.002083 mm`, `V=+0.001250 mm`
  - corrected diameters `U=30.095341 mm`, `V=30.210500 mm`
- Difference from the prior accepted manual `B+15 C0` repeat:
  - `dX=+0.034520 dY=+0.005000 dZ=-0.005985`
  - `dU_diam=-0.011667 dV_diam=+0.003333`
- Conclusion:
  - automatic two-pass centering is validated at `B+15 C0`
  - it is safe to continue to `B+30 C0` with the two-pass routine, using Single
    Block for the first `B+30` run
  - verify DRO pose before the next run so `B+15` and `B-15` are not confused

# 2026-04-27 - B+30 C0 two-pass data

- Ran `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc` at
  `B+30 C0`.
- Pass 1 result:
  - center `X=151.728385 Y=352.906605 Z=-321.872175`
  - local centering correction `U=+0.580000 mm`, `V=+0.018750 mm`
  - corrected diameters `U=30.272369 mm`, `V=30.192167 mm`
  - correction and diameter sanity checks passed
- Pass 2 accepted result:
  - center `X=151.969455 Y=352.913688 Z=-321.714304`
  - remaining local centering error `U=-0.004583 mm`, `V=-0.004583 mm`
  - corrected diameters `U=30.276536 mm`, `V=30.208833 mm`
- Current accepted B-axis vector centers:
  - `B+15 C0`: `X=226.486276 Y=352.897855 Z=-291.117802`
  - `B+30 C0`: `X=151.969455 Y=352.913688 Z=-321.714304`
- Next live step:
  - move to `B-30 C0`
  - verify DRO before Cycle Start
  - use the same two-pass current-pose routine with Single Block for the first
    `B-30` run

# 2026-04-27 - B-30 C0 two-pass data

- Ran `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc` at
  `B-30 C0`.
- Pass 1 result:
  - center `X=460.743594 Y=352.778271 Z=-322.524478`
  - local centering correction `U=-0.509167 mm`, `V=-0.275417 mm`
  - corrected diameters `U=30.134036 mm`, `V=30.198833 mm`
  - correction and diameter sanity checks passed
- Pass 2 accepted result:
  - center `X=460.527766 Y=352.638896 Z=-322.390804`
  - remaining local centering error `U=+0.001667 mm`, `V=-0.003333 mm`
  - corrected diameters `U=30.139036 mm`, `V=30.211333 mm`
- Current accepted B-axis vector centers:
  - `B+15 C0`: `X=226.486276 Y=352.897855 Z=-291.117802`
  - `B+30 C0`: `X=151.969455 Y=352.913688 Z=-321.714304`
  - `B-30 C0`: `X=460.527766 Y=352.638896 Z=-322.390804`
- Next live step:
  - run closing `B0 C0` using the two-pass routine
  - verify DRO is exactly `B0 C0` before Cycle Start
  - use Single Block for the closing run

# 2026-05-03 - TCPC B90 clean shutdown handoff

Session state at shutdown:

- Local time checkpoint: `2026-05-03 19:25 +07`.
- LinuxCNC/Probe Basic program is stopped.
- Probe gate state after the clean B90 run is safe:
  - `halui.program.is-running = FALSE`
  - `motion.digital-out-00 = FALSE`
  - `motion.digital-out-01 = FALSE`
  - `motion.probe-input = FALSE`
- The operator intends to shut down for the night.

Important operator instruction:

- Trust the differential angles from the SSI encoders.
- For fitting, treat machine geometry as variable. Do not assume ideal C/Z
  alignment, ideal B/C orthogonality, ideal B centering, ideal tool/probe vector,
  or ideal linear-axis squareness/scale.
- Continue checking SSI feedback for gross errors, but do not explain repeatable
  mm-scale TCP residuals by encoder differential angle noise unless future data
  contradicts this.

Program/data state:

- New B90 diagnostic program:
  - `nc_files/calibration/tcpc_b90_b_axis_diagnostic.ngc`
  - currently untracked in git
  - configured for B90 diagnostic mode with `#707=90.0`, `#708=1.0`,
    `#709=90.0`
- Expanded program:
  - `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc`
  - still in B50 redo mode with `#707=50.0`, `#708=1.0`, `#709=50.0`
  - do not run it as a normal full sweep until those controls are reset
- Both TCPC vector programs now include pass-2 sanity checks before accepting a
  center for the next pose:
  - pass-2 U/V residual abort threshold: `0.10 mm`
  - pass-2 corrected diameter abort window: `29.5-30.5 mm`
  - this was added after the earlier probe reset produced a bad accepted
    `B0 C180` center

Probe/reset caveat:

- Earlier B90 attempt had a probe reset during the run.
- The bad accepted row was `tcpc-b90-b-axis-diagnostic-2pass-results.csv` line
  `17`, `B0 C180`, with corrected diameters about `29.172 / 29.220 mm` and Z
  about `+4.10 mm` from expected.
- Exclude line `17` and the following aborted `B-90 C180` attempt from any
  geometry fitting.

Clean B90 rerun:

- Clean rerun starts at
  `tcpc-b90-b-axis-diagnostic-2pass-results.csv` line `18`.
- It completed at `19:15 +07` with
  `TCPC_B90_B_AXIS_DIAGNOSTIC complete`.
- Accepted pass-2 centers repeated against the earlier clean common rows within
  about `0.008-0.019 mm`, so the high-B errors are repeatable.
- Corrected diameters in the clean B90 rerun remained valid, about
  `30.166-30.194 mm` in U and `30.204-30.220 mm` in V.

Clean B90 local deltas versus the immediately preceding B0 baseline:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.042834` | `-0.212500` | `+0.067708` | `0.227102` |
| `B-90 C0` | `-0.190496` | `-0.123125` | `+0.620805` | `0.660944` |
| `B+90 C180` | `-0.177921` | `-0.224257` | `+0.054792` | `0.291461` |
| `B-90 C180` | `-0.052201` | `+0.177427` | `+0.632291` | `0.658785` |

B0 repeat/closure checks from the clean B90 rerun:

- C0 B0 closures were about `0.033 mm`, `0.030 mm`, and `0.013 mm`.
- C180 B0 closures were about `0.014 mm`, `0.024 mm`, and `0.011 mm`.
- This argues against simple thermal drift or random probe noise as the source
  of the B90 error.

Interpretation as of shutdown:

- B-axis centering is not correct enough for TCPC, but the error is not one
  simple B-center offset.
- Individual implied B-center X/Z corrections from the clean B90 data disagree
  strongly between `B+90` and `B-90`:
  - `B+90 C0` implies about `dbx=-0.012 mm`, `dbz=-0.055 mm`
  - `B-90 C0` implies about `dbx=+0.406 mm`, `dbz=-0.215 mm`
  - `B+90 C180` implies about `dbx=+0.062 mm`, `dbz=-0.116 mm`
  - `B-90 C180` implies about `dbx=+0.342 mm`, `dbz=-0.290 mm`
- C-axis center error is also present. Clean B0 C180 versus B0 C0 implies about
  `-0.104 mm` X and `+0.009 mm` Y C-center correction.
- Existing `headheadkins` translation and zero-offset knobs are insufficient:
  fitting current HAL-style knobs to the latest expanded plus clean B90 data
  still leaves roughly `0.50 mm` max residual at B90.
- XYZ motor command/feedback following errors and rotary SSI following errors
  are too small to explain the mm-scale TCP errors.
- Main remaining suspects are repeatable geometry/mechanics:
  - C axis not parallel to machine Z
  - B axis not exactly orthogonal to C or not exactly local Y
  - B pivot/tool-vector angular error
  - probe/tool vector not matching the modeled spindle vector
  - linear-axis scale/squareness/pitch/straightness error under the large
    X/Z/Y moves required by high B angles
  - repeatable flex or angle/load-dependent head deflection

Next recommended live diagnostic:

- Do not rerun the same B90 C0/C180 diagnostic first; it already repeated.
- Build/run a B90 C-quadrant diagnostic:
  - `B0 C0`
  - `B+90` and `B-90` at `C0`, `C90`, `C180`, and `C270`
  - B0 closures between groups
  - keep avoiding the known risky `C45` sector
- Purpose:
  - if the high-B residual rotates with C, prioritize rotary head geometry
    terms
  - if the high-B residual stays fixed to machine XYZ, prioritize linear-axis
    scale/squareness/pitch/straightness and volumetric correction

Kinematics correction expansion direction:

- It is reasonable to expand TCPC math to compensate repeatable mechanical
  deficiencies. Treat it as practical compensation, not as proof the machine is
  mechanically aligned.
- The current `headheadkins` model assumes C about machine Z and B about local
  Y. It only exposes translations and B/C zero offsets.
- Next kinematics work should add bounded HAL pins and offline fitting support
  for:
  - C-axis direction tilt relative to machine Z, preferably two small-angle
    terms or a normalized axis vector
  - B-axis direction/skew relative to the C frame, preferably two small-angle
    terms or a normalized axis vector
  - non-orthogonality between B and C
  - B/C zero offsets retained as variables
  - B and C pivot translations retained as variables
  - tool/probe vector angular error, ideally tool-specific later
  - optional linear-axis affine/volumetric correction terms or maps after
    deciding whether high-B residuals are fixed in machine XYZ
- Fit these offline first with bounds and held-out poses. Do not apply a new
  compensation family live until the residual report shows it improves both
  mid-B and high-B data without damaging B0 C-only closure.

## 2026-05-04 B90 C-Quadrant Run Complete

The C90 resume run of `tcpc_b90_c_quadrant_diagnostic.ngc` completed at
`10:02:56 +07`. LinuxCNC was stopped afterwards, and the probe gate outputs
were both false:

- `halui.program.is-running = FALSE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`
- `motion.probe-input = FALSE`

Data quality:

- The previous aborted `B0 C90` pass 2 remains the only accepted bad row in
  `tcpc-b90-c-quadrant-diagnostic-2pass-results.csv`.
- That bad row is line `13`: corrected diameters `29.700500` and `29.739667`,
  center Z about `2.89 mm` too high. Exclude it from fitting.
- The completed resume rows passed the tighter `29.9 mm` diameter floor and
  pass-2 centering residual checks.
- `tcpc_b90_c_quadrant_diagnostic.ngc` has been reset to `#710 = 0.0` so the
  next run is a normal full B90 C-quadrant diagnostic.

B0 C-axis closure/orbit from valid pass-2 rows:

| C | mean X mm | mean Y mm | mean Z mm | X range | Y range | Z range |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `468.760084` | `323.675216` | `-858.976929` | `0.031124` | `0.016667` | `0.003000` |
| `90` | `468.851656` | `323.569747` | `-858.956054` | `0.010833` | `0.030417` | `0.008042` |
| `180` | `468.964434` | `323.666878` | `-858.941637` | `0.028624` | `0.011667` | `0.003208` |
| `270` | `468.861386` | `323.768933` | `-858.950276` | `0.003041` | `0.028468` | `0.001958` |

Relative to the C0 mean, the B0 C sweep follows a clean C-axis center orbit:

- `C90`: `+0.091572 X`, `-0.105469 Y`, `+0.020875 Z`
- `C180`: `+0.204350 X`, `-0.008337 Y`, `+0.035291 Z`
- `C270`: `+0.101302 X`, `+0.093717 Y`, `+0.026653 Z`

This fits the expected `e - R(C)e` pattern with about `0.102 mm` C-center
error in X and near-zero Y in the current fit convention. Verify sign in a
simulation before applying any live kinematics correction; it likely maps to an
additional negative X C-center correction in `headheadkins`.

Accepted B90 local deltas versus adjacent B0 closures:

| Pose | dX mm | dY mm | dZ mm | 3D drift mm |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.050270` | `-0.204791` | `+0.071000` | `0.222503` |
| `B-90 C0` | `-0.165771` | `-0.126459` | `+0.617562` | `0.651809` |
| `B+90 C90` | `-0.104999` | `-0.190271` | `-0.011188` | `0.217608` |
| `B-90 C90` | `-0.011354` | `+0.496312` | `+0.810062` | `0.950082` |
| `B+90 C180` | `-0.177021` | `-0.222083` | `+0.058604` | `0.289986` |
| `B-90 C180` | `-0.057875` | `+0.183750` | `+0.630896` | `0.659654` |
| `B+90 C270` | `-0.221946` | `+0.474761` | `+0.244541` | `0.578325` |
| `B-90 C270` | `-0.161601` | `-0.178643` | `+0.550479` | `0.600879` |

Important interpretation:

- The B0 C orbit is clean and strongly supports a C-axis center/alignment term.
- The high-B residual is not explained by one B-center translation.
- B-90 has a consistent large positive Z residual around `0.55-0.81 mm`.
- The largest residuals occur in side-quadrant high-B poses that drive Y motor
  position near either end of travel, especially `B-90 C90` and `B+90 C270`.
- Current `headheadkins` translation/zero-offset pins still cannot fit this
  pattern cleanly. A simple fit using existing B-to-tool and zero-offset terms
  still leaves about `0.49-0.61 mm` max local B90 residual.

Next work:

1. Do not run another long probe program yet.
2. Fit the valid quadrant data offline, excluding bad line `13`.
3. Expand the candidate model beyond current `headheadkins` translations:
   C-axis direction tilt, B-axis skew/non-orthogonality, B zero as a fitted
   variable, tool/probe vector angular error, and only then machine-fixed
   linear-axis affine terms if residuals remain fixed in XYZ.
4. Simulate the sign of the C-center correction before loading any live HAL
   values.

## 2026-05-04 Expanded Offline Fit Started

Created `tcpc_expanded_geometry_fit.py` and generated
`TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` in
`configs/5th_axis_xyzbc_ssi_probe_basic/`.

Data used:

- training: `20` valid pass-2 rows from the B90 C-quadrant diagnostic
- holdout: `10` valid pass-2 rows from the clean B90 C0/C180 rerun
- excluded bad false-top `B0 C90` row by diameter floor

First fit conclusions:

- B0-only C-center fit is clean:
  - `dcx = +0.100886006 mm`
  - `dcy = -0.004473694 mm`
  - equivalent test-only `cal-c-to-b.x = +0.035886006`
  - equivalent test-only `cal-c-to-b.y = +0.009526306`
  - B0 C-orbit RMS/max improves from `0.102863 / 0.118339 mm` to
    `0.019566 / 0.030016 mm`
- Current `headheadkins` pins improve the all-row fit but are rank-deficient,
  so do not load those current-pin fit values.
- C/B axis-vector terms alone improve only modestly beyond the current pins:
  training RMS/max `0.224540 / 0.489239 mm`, holdout RMS/max
  `0.238502 / 0.471294 mm`.
- Adding linear-axis diagonal terms improves both training and holdout:
  training RMS/max `0.164906 / 0.352968 mm`, holdout RMS/max
  `0.149801 / 0.308334 mm`.
- The linear fit is diagnostic only: `lin_xx` hits the `-0.002` bound and the
  problem is ill-conditioned. This points to possible machine-fixed linear-axis
  contribution, but it is not a solved compensation map.

Next engineering step:

- Simulate/verify the sign of the clean C-center correction first.
- Then add simulation-only expanded `headheadkins` support for C-axis tilt,
  B-axis skew, retained B/C zeros, and debug pins.
- Do not run another long probe program until the model says which validation
  data is needed next.

## 2026-05-04 Expanded Kinematics Scaffold

Implemented zero-default expanded-axis support in
`src/emc/kinematics/headheadkins.c` and rebuilt `rtlib/headheadkins.so`.

New input pins:

- `headheadkins.c-axis-tilt.x`
- `headheadkins.c-axis-tilt.y`
- `headheadkins.b-axis-tilt.x`
- `headheadkins.b-axis-tilt.z`

New debug output pins:

- `headheadkins.c-axis-vector.x/y/z`
- `headheadkins.b-axis-vector.x/y/z`

The expanded math path matches the offline fit model:

- C frame tilt is applied as `Ry(c-axis-tilt.y) * Rx(c-axis-tilt.x)`
- B rotates about a normalized local axis built from
  `b-axis-tilt.x/z`
- zero values reproduce the old ideal `Rz(C) * Ry(B)` behavior
- TWP plane axes now use the same expanded axis-vector path

The currently running LinuxCNC session will not see the new pins until restart.
No live HAL values were changed.

C-center sign simulation:

- current B0 C-orbit RMS/max: `0.102863 / 0.118339 mm`
- fitted sign RMS/max: `0.019566 / 0.030016 mm`
- opposite sign RMS/max: `0.202916 / 0.219278 mm`
- test-only values after sign verification:
  - `cal-c-to-b.x = +0.035886006`
  - `cal-c-to-b.y = +0.009526306`

Next validation should be a restart-level check only: confirm new pins exist,
confirm all new pins are zero, and confirm zero-default tool-offset/tool-vector
values match the previous model before any live motion test.

## 2026-05-04 Live C-Center Validation

Restarted the TCPC Probe Basic config, confirmed the expanded kinematics pins
exist and are zero by default, then loaded the C-center correction only:

- `headheadkins.cal-c-to-b.x = +0.035886006`
- `headheadkins.cal-c-to-b.y = +0.009526306`
- same values mirrored to `headheadtwp`
- all new axis-vector tilt pins remain `0.0`

Ran a B0-only C-quadrant validation using
`tcpc_b90_c_quadrant_diagnostic.ngc` temporarily set to:

- `#707 = 0.0`
- `#708 = 0.0`
- `#709 = 90.0`
- `#710 = 0.0`

The run completed with no probe errors. LinuxCNC is idle and the probe gates are
clear:

- `halui.program.is-idle = TRUE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`
- `motion.probe-input = FALSE`

Validation result from the latest pass-2 rows:

- unique `C0/C90/C180/C270` B0 orbit RMS/max: `0.015700 / 0.018205 mm`
- XY-only RMS/max: `0.011276 / 0.016818 mm`
- closure, final `C0` minus first `C0`: `-0.004053 X`, `-0.003002 Y`,
  `-0.000500 Z`, `0.005068 mm` 3D
- pass-2 max residuals: `err_u <= 0.003750 mm`, `err_v <= 0.002500 mm`
- prior B0 closure orbit before this correction was about
  `0.114023 mm` RMS, so the correction is confirmed in the live direction

The remaining C-dependent error is mostly small Z variation, about
`0.030 mm` peak-to-peak across the four C quadrants. That likely needs C-axis
tilt / spindle-vector / machine-fixed terms, not another C-center XY tweak.

After the run, `tcpc_b90_c_quadrant_diagnostic.ngc` was restored to B90
diagnostic defaults:

- `#707 = 90.0`
- `#708 = 1.0`
- `#709 = 90.0`
- `#710 = 0.0`

Recommended next live run:

- Keep the current live C-center correction active.
- From the current above-sphere position, rerun the restored B90 C-quadrant
  diagnostic.
- This will show high-B residuals after removing the large B0 C-axis center
  orbit, and should be the next data used for expanded B-axis / linear-axis
  fitting.

## 2026-05-04 B90 C-Quadrant Rerun With C-Center Active

The restored B90 C-quadrant diagnostic completed at `12:41:29 +07` after
operator-paused probe settling/recovery. Treat the pause/reset actions as probe
recovery, not as automatic program causes.

End state:

- `halui.program.is-idle = TRUE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`
- `motion.probe-input = FALSE`
- live C-center correction still active:
  - `headheadkins.cal-c-to-b.x = +0.035886006`
  - `headheadkins.cal-c-to-b.y = +0.009526306`

Latest appended result rows:

- `tcpc-b90-c-quadrant-diagnostic-2pass-results.csv` lines `54-93`
- `40` rows total, `20` pass-2 accepted centers

Data quality:

- all expected rows were logged
- pass-2 corrected diameter ranges:
  - U `30.158000..30.205020`
  - V `30.160141..30.244667`
- pass-2 max residuals:
  - U `0.061250 mm`
  - V `0.007500 mm`
- the `0.061250 mm` U residual is below the `0.10 mm` abort threshold but
  should be treated cautiously because the wireless probe was misbehaving

B0 closure/orbit by C from this rerun:

| C | n | mean X | mean Y | mean Z | X range | Y range | Z range | RMS |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `3` | `468.895029` | `323.664227` | `-858.979290` | `0.082500` | `0.041041` | `0.003875` | `0.038723` |
| `90` | `3` | `468.889161` | `323.729115` | `-858.962581` | `0.008092` | `0.025292` | `0.003416` | `0.011711` |
| `180` | `3` | `468.793108` | `323.706769` | `-858.945872` | `0.033751` | `0.007988` | `0.003626` | `0.014299` |
| `270` | `3` | `468.824505` | `323.592605` | `-858.952150` | `0.019969` | `0.026720` | `0.003875` | `0.014945` |

High-B deltas versus adjacent B0 closures:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.052875` | `-0.198228` | `+0.069230` | `0.216525` |
| `B-90 C0` | `-0.203375` | `-0.137813` | `+0.659229` | `0.703518` |
| `B+90 C90` | `-0.094271` | `-0.242146` | `-0.084833` | `0.273347` |
| `B-90 C90` | `-0.012100` | `+0.421370` | `+0.886208` | `0.981358` |
| `B+90 C180` | `-0.112354` | `-0.220592` | `-0.012021` | `0.247848` |
| `B-90 C180` | `+0.022229` | `+0.169999` | `+0.712771` | `0.733100` |
| `B+90 C270` | `-0.223969` | `+0.539925` | `+0.170062` | `0.608771` |
| `B-90 C270` | `-0.149642` | `-0.115378` | `+0.633603` | `0.661179` |

High-B delta RMS/max: `0.610965 / 0.981358 mm`.

Immediate interpretation:

- The validated C-center correction fixed the B0 C-axis orbit, but it did not
  solve the high-B error.
- The large remaining pattern is still dominated by B-90 positive Z residuals
  and side-quadrant Y-extreme poses.
- X/Y/Z following errors at the logged accepted rows are effectively zero, so
  servo following error is not the explanation.
- Stop long probing until the probe is stable. The next work should be offline
  fitting with this corrected high-B dataset, using the probe-quality caveat.

## 2026-05-04 Run-State-Aware Offline Fit

Updated `tcpc_expanded_geometry_fit.py` so every observation carries the
kinematic C-center that was active when that row was measured. This fixes the
analysis issue where pre-correction and post-correction rows were previously
being compared as though the same TCPC offset had been active for every run.

Regenerated `TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` with these data groups:

- pre-correction B90 C-quadrant: `20` pass-2 points, old C-center
- B0 C-center validation: `5` pass-2 points, validated C-center
- corrected B90 C-quadrant: `20` pass-2 points, validated C-center
- clean B90 C0/C180 holdout: `10` pass-2 points, old C-center

Confirmed C-center remains the only live correction candidate:

- `dcx = +0.100886006 mm`
- `dcy = -0.004473694 mm`
- equivalent `headheadkins.cal-c-to-b.x = +0.035886006`
- equivalent `headheadkins.cal-c-to-b.y = +0.009526306`
- validation-row RMS/max with fixed C-center: `0.0157 / 0.0201 mm`

Corrected B90 run with C-center fixed:

| Model | corrected B90 RMS/max | B-axis holdout RMS/max |
| --- | ---: | ---: |
| C-center fixed only | `0.3562 / 0.8735` | `0.2778 / 0.5509` |
| B-zero only | `0.3110 / 0.7336` | `0.2591 / 0.3952` |
| B-zero plus B-to-tool Z | `0.2526 / 0.4930` | `0.2706 / 0.4080` |
| current pins, C fixed | `0.2440 / 0.4898` | `0.2654 / 0.4102` |
| axis vectors, C fixed | `0.2384 / 0.4667` | `0.2581 / 0.4010` |
| axis vectors plus linear diagonal, C fixed | `0.1825 / 0.3374` | `0.1807 / 0.2744` |

Training on corrected B90 plus the clean B90 C0/C180 holdout gives similar
diagnostic improvement but still hits bounds:

- post+B-axis axis-vector plus linear-diagonal fit:
  - corrected B90 RMS/max `0.1845 / 0.3523 mm`
  - B-axis holdout RMS/max `0.1703 / 0.2583 mm`
  - `b_axis_x` hits the `-0.5 deg` bound
  - `c_zero` trends near `-0.49 deg`
  - `lin_xx` hits the `-0.002` bound

Decision:

- Keep the validated C-center correction.
- Do not load any high-B correction from the current fit.
- The residual is not solved by current pins or simple C/B axis-vector terms.
- Linear/affine terms are useful diagnostic evidence, but not a live
  compensation candidate while they hit bounds and remain ill-conditioned.

Next code/math work:

1. Keep the run-state-aware fitter as the source of truth for mixed data.
2. Add `headheadkins` debug output pins for the actual expanded U/V/W probe
   frame.
3. Add simulation-only machine-linear affine correction with identity defaults.
4. Refit with C-center fixed after collecting B-angle scaling data.

Next live machine data after probe stabilization:

- C0 reduced sequence first:
  `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`
- repeat at C180 only if C0 is clean
- keep the current C-center correction active
- do not rerun the same long B90 C-quadrant diagnostic until the wireless
  probe is stable
- Existing `tcpc_b90_b_axis_diagnostic.ngc` is not the exact next run: its
  B30/B60 blocks probe all C quadrants and include the older B50 path. Prepare
  a dedicated short B-angle scaling NGC before the next live run.
- Rationale for fewer B0 cycles: the B0 closure data is now consistent enough
  that an opening and closing B0 at each C should catch drift/sphere movement
  without spending time on every intermediate B0 return. Add intermediate B0
  checks back only if the opening/closing B0 spread grows or the probe becomes
  suspect again.

## 2026-05-04 Short B-Angle Scaling NGC Prepared

LinuxCNC live check before preparing the next run:

- `halui.program.is-idle = TRUE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`
- `motion.probe-input = FALSE`
- `headheadkins.cal-c-to-b.x = +0.03588601`
- `headheadkins.cal-c-to-b.y = +0.009526306`
- `headheadtwp.cal_c_to_b_x = +0.03588601`
- `headheadtwp.cal_c_to_b_y = +0.009526306`

No LinuxCNC restart is needed for the current run because the live C-center
correction is still active and no live kinematics code was changed.

Prepared new program:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`

Default sequence, C0 only:

- `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`

The optional C180 repeat is disabled by default:

- `#711 = 0.0`
- set `#711 = 1.0` only after C0 data is clean and the program is not running

New logs were initialized with headers:

- `tcpc-b-angle-scaling-diagnostic-2pass-results.csv`
- `tcpc-b-angle-scaling-diagnostic-2pass-raw-points.csv`
- `tcpc-b-angle-scaling-diagnostic-rotary-joint-state.csv`
- `tcpc-b-angle-scaling-diagnostic-rotary-ssi-state.csv`
- `tcpc-b-angle-scaling-diagnostic-axis-state.csv`

## 2026-05-04 B-Angle Scaling Abort And Transit Fix

The first short B-angle scaling attempt was interrupted by probe instability.
The result log has partial data through `B-90 C0` pass 1:

- `tcpc-b-angle-scaling-diagnostic-2pass-results.csv` has `20` lines including
  header
- no valid `B-90 C0` pass 2 or final closing `B0 C0` row was logged

Operator observed that the program tried to index back toward B0 from the last
touch location instead of first returning to the top-clear point. The issue was
inherited from the older diagnostic transit path: between poses it lifted only
in machine Z before indexing B. At high B, a machine-Z-only lift is not
necessarily a stylus pull-away from the sphere.

Patched `tcpc_b_angle_scaling_diagnostic.ngc` so every later pose transition:

1. recomputes the current B/C probe W vector
2. moves to the last accepted center's top-clear point in the current pose
3. then lifts in machine Z
4. then indexes B/C
5. then moves to the next pose's top-clear start point

Before the next attempt:

- reload the NGC in Probe Basic so the patched file is active
- do not resume from the stopped touch point
- manually position at/near B0 C0, 3-8 mm above the sphere
- clear stuck gates with MDI `M65 P0` and `M65 P1`

## 2026-05-04 Resume-Only Tail Program

To avoid rerunning the whole short scaling sequence after the probe fault,
prepared a resume-only program:

- `nc_files/calibration/tcpc_b_angle_scaling_resume_bminus90_c0.ngc`

It appends to the same B-angle scaling logs and only measures:

- `B-90 C0`
- closing `B0 C0`

The resume program does not remeasure opening B0. It seeds the safe transit
calculation from the latest accepted B0 C0 pass-2 row in the interrupted run:

- results CSV line `9`
- `X468.863916 Y323.669451 Z-858.972978`

Operator setup for this resume:

- start at/near `B0 C0`, `3-8 mm` above the sphere
- load the resume NGC, not the full scaling NGC
- the program will first retract to the seeded B0 top-clear point, then lift Z,
  index to `B-90 C0`, measure, and then measure closing `B0 C0`

## 2026-05-04 B-Angle Scaling C0 Complete

The resume-only tail completed the missing `B-90 C0` and closing `B0 C0`
points. Controller/probe state after completion:

- `halui.program.is-idle = TRUE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`
- `motion.probe-input = FALSE`

Use these final accepted pass-2 rows from
`tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

| CSV line | Pose | X | Y | Z |
| ---: | --- | ---: | ---: | ---: |
| `9` | `B0 C0 open` | `468.863916` | `323.669451` | `-858.972978` |
| `11` | `B+30 C0` | `468.887475` | `323.593617` | `-858.937660` |
| `13` | `B-30 C0` | `468.848484` | `323.683200` | `-858.927606` |
| `15` | `B+60 C0` | `468.867390` | `323.495283` | `-858.912287` |
| `17` | `B-60 C0` | `468.804196` | `323.620491` | `-858.713674` |
| `19` | `B+90 C0` | `468.828863` | `323.462158` | `-858.916590` |
| `22` | `B-90 C0` | `468.704249` | `323.549868` | `-858.332770` |
| `24` | `B0 C0 close` | `468.888833` | `323.661534` | `-858.973103` |

Exclude the earlier interrupted/restart rows before line `9` and the abandoned
`B-90 C0` pass-1 row at line `20`.

Data quality:

- opening/closing B0 drift: `+0.024917 X`, `-0.007917 Y`,
  `-0.000125 Z`, `0.026145 mm` 3D
- accepted pass-2 residual max: U `0.007917 mm`, V `0.008334 mm`
- accepted corrected diameter ranges:
  - U `30.154216..30.246536 mm`
  - V `30.213000..30.236333 mm`
- probe tool number logged as `0`; the program still used the known 6 mm
  fallback diameter and `0.134533 mm` calibration offset, so keep this as a
  tool-state caveat rather than rejecting the centers

Deltas relative to the average of opening/closing B0:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+30 C0` | `+0.011100` | `-0.071876` | `+0.035380` | `0.080877` |
| `B-30 C0` | `-0.027891` | `+0.017707` | `+0.045435` | `0.056176` |
| `B+60 C0` | `-0.008984` | `-0.170210` | `+0.060754` | `0.180950` |
| `B-60 C0` | `-0.072179` | `-0.045002` | `+0.259367` | `0.272958` |
| `B+90 C0` | `-0.047512` | `-0.203335` | `+0.056451` | `0.216307` |
| `B-90 C0` | `-0.172126` | `-0.115625` | `+0.640271` | `0.673010` |

First interpretation:

- Reduced-B0 strategy worked for data collection; closure was good enough.
- B-90 Z error grows strongly with B angle and is already visible at B-60.
- B+ side mainly shows Y drift with smaller Z error.
- A simple `sin(B)` plus `1-cos(B)` model leaves about `0.091 mm` RMS, while
  adding a `sin(2B)` diagnostic term drops this C0-only residual to about
  `0.020 mm` RMS. Do not treat that as a live correction yet; it is a strong
  clue that the high-B error has more than one B-dependent term.

Next work:

- stop probing for now
- fold these C0 scaling rows into the offline fitter
- fit with the C-center fixed and keep this data as the angle-scaling set
- only request C180 if the fit cannot separate C0-only B-angle terms from
  machine-fixed terms

## 2026-05-04 C0 Scaling Added To Offline Fit

`tcpc_expanded_geometry_fit.py` now includes the completed C0 B-angle scaling
set as a first-class data set:

- file: `tcpc-b-angle-scaling-diagnostic-2pass-results.csv`
- accepted lines: `9, 11, 13, 15, 17, 19, 22, 24`
- active correction during the run: validated C-center
  `cal-c-to-b.x = +0.035886006`, `cal-c-to-b.y = +0.009526306`

Updated fit/report files:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc_expanded_geometry_fit.py`
- `configs/5th_axis_xyzbc_ssi_probe_basic/TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md`

Fit results with C-center fixed:

- C0 scaling only:
  - fixed C-center RMS/max: `0.2265 / 0.5219 mm`
  - bounded machine-fixed B-harmonic model: `0.0166 / 0.0277 mm`, with
    corrected B90 evaluation `0.2316 / 0.6278 mm` and clean B90 holdout
    `0.1036 / 0.2805 mm`
  - best flexible linear-diagonal model: `0.0830 / 0.1268 mm`
  - but that same fit evaluates at about `4.46 mm` RMS on the B90 quadrant
    data, so it is not a general correction
- corrected B90 plus clean B90 holdout plus C0 scaling:
  - machine-fixed B-harmonic RMS/max:
    - C0 scaling: `0.0651 / 0.1221 mm`
    - corrected B90: `0.2058 / 0.5687 mm`
    - clean B90 C0/C180 holdout: `0.0917 / 0.1630 mm`
    - rank `9`, condition `2.52e+00`
  - C-frame B-harmonic RMS/max:
    - C0 scaling: `0.0912 / 0.1935 mm`
    - corrected B90: `0.1910 / 0.4678 mm`
    - clean B90 C0/C180 holdout: `0.1332 / 0.3049 mm`
  - combined machine/C-frame harmonic is not identifiable; condition is about
    `7.31e+16`
  - axis-vector plus linear-diagonal RMS/max:
    - C0 scaling: `0.1092 / 0.1492 mm`
    - corrected B90: `0.1854 / 0.3527 mm`
    - clean B90 C0/C180 holdout: `0.1723 / 0.2816 mm`
  - the fit still drives `b_axis_x` and `lin_xx` to bounds, so do not load
    it live
- all curated data plus C0 scaling:
  - axis-vector plus linear-diagonal RMS/max:
    - C0 scaling: `0.1122 / 0.1586 mm`
    - corrected B90: `0.1877 / 0.3654 mm`
    - clean B90 C0/C180 holdout: `0.1688 / 0.2917 mm`
    - B0 validation: `0.1386 / 0.1739 mm`
  - this is still diagnostic only because the model remains ill-conditioned
    and bound-limited

Current decision:

- Keep the live C-center correction.
- Do not load any high-B correction from this fit.
- The C0 scaling data confirms a strong B-dependent missing term, especially
  on the negative-B side.
- The strongest bounded non-affine diagnostic is now the machine-fixed
  B-harmonic model; do not load it live until it exists in simulation and the
  inverse kinematics path is verified.
- Next work is offline math/code: add debug output for the actual U/V/W tool
  frame, then implement the B-harmonic correction path in simulation only with
  all coefficients defaulting to zero.
- Do not request a C180 B-angle scaling pass unless the next offline model
  cannot separate rotary-frame terms from machine-fixed terms with current
  data.

## 2026-05-04 Headheadkins Offline Diagnostic Pins Added

LinuxCNC was closed by the operator, so the rebuilt kinematics module was
compiled, setuid-applied, and checked in `halrun`.

Code change:

- file: `src/emc/kinematics/headheadkins.c`
- added tool-frame debug outputs:
  - `headheadkins.tool-frame-u.x/y/z`
  - `headheadkins.tool-frame-v.x/y/z`
  - `headheadkins.tool-frame-w.x/y/z`
- added simulation-gated B-harmonic correction pins:
  - enable: `headheadkins.sim-bharm-enable`
  - machine-fixed coefficients: `headheadkins.bharm-m.sin/omc/sin2.x/y/z`
  - C-frame coefficients: `headheadkins.bharm-c.sin/omc/sin2.x/y/z`

Default behavior:

- `sim-bharm-enable` defaults `FALSE`
- all B-harmonic coefficients default `0`
- with the enable pin false, the new harmonic path contributes zero correction
- tool-frame debug defaults at `B0 C0` are:
  - U = `+X`
  - V = `+Y`
  - W = `-Z`, matching the existing stylus/tool vector convention

Verification performed:

- `make -j2` in `src`
- `sudo make setuid` in `src`
- regenerated `TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md`
- `python3 -m py_compile tcpc_expanded_geometry_fit.py`
- `halrun` loaded `headheadkins coordinates=XYZBC` and showed:
  - `tool-frame-u.x = 1`
  - `tool-frame-v.y = 1`
  - `tool-frame-w.z = -1`
  - `sim-bharm-enable = FALSE`
  - representative B-harmonic pins present and zero
- `halrun -U` unloaded the test realtime session afterward

Important: do not enable `sim-bharm-enable` on the real machine yet. The report
now contains a simulation-only HAL load block for the machine-fixed diagnostic
candidate, but it still needs simulation motion verification before any live
test.

## 2026-05-04 Offline B-Harmonic Verification Started

Next step in progress:

- add a non-GUI offline verification script for the `headheadkins` B-harmonic
  math
- verify zero-default behavior is unchanged
- verify the U/V/W tool-frame convention against the probing program formulas
- verify forward/inverse consistency with the machine-fixed diagnostic
  candidate enabled in software only

This is offline math verification only. No live machine movement or LinuxCNC
machine config launch is required.

## 2026-05-04 Offline B-Harmonic Verification Passed

Added:

- `configs/sim/head_head_5axis/headhead_bharmonic_verify.py`
- `configs/sim/head_head_5axis/head_head_bharmonic_candidate.hal`
- `configs/sim/head_head_5axis/tcp_bharmonic_candidate_sequence.ngc`

Verification script result:

- zero/default max offset delta: `0 mm`
- tool-frame formula max delta: `0`
- active tool-frame orthogonality max error: `5.55e-17`
- machine-fixed candidate forward/inverse round-trip max error:
  `8.04e-14 mm`

The script verifies:

- `sim-bharm-enable = FALSE` keeps behavior unchanged, even if coefficients are
  loaded
- zero coefficients keep behavior unchanged even when the harmonic path is
  enabled
- U/V/W debug-frame math matches the probing program convention when B/C zero
  offsets are zero
- the active machine geometry frame remains orthonormal
- the machine-fixed candidate does not break forward/inverse fixed-tip
  consistency in the offline math model

Machine-fixed candidate harmonic offsets at `C0`:

| B | dX | dY | dZ |
| ---: | ---: | ---: | ---: |
| `-90` | `+0.104666146` | `-0.037540322` | `-0.682739468` |
| `-60` | `+0.078975340` | `-0.049648828` | `-0.292649762` |
| `-30` | `+0.040664872` | `-0.035908116` | `-0.042749773` |
| `0` | `+0.000000000` | `+0.000000000` | `+0.000000000` |
| `+30` | `-0.011693203` | `+0.045138160` | `-0.054910233` |
| `+60` | `+0.029148401` | `+0.084095821` | `-0.071822343` |
| `+90` | `+0.111581336` | `+0.106434308` | `-0.046204742` |

Candidate HAL file check:

- loaded `headheadkins coordinates=XYZBC` in `halrun`
- sourced `head_head_bharmonic_candidate.hal`
- confirmed `headheadkins.sim-bharm-enable = FALSE`
- confirmed representative coefficient pins loaded:
  - `headheadkins.bharm-m.sin.z = 0.3182674`
  - `headheadkins.bharm-m.omc.z = -0.3644721`
  - `headheadkins.bharm-m.sin2.z = -0.1907726`
- unloaded `halrun` afterward

Next offline step is a full LinuxCNC sim run only, with the candidate HAL file
loaded and `sim-bharm-enable` toggled in simulation. Do not include this HAL
file in the real machine config.

Prepared sim G-code:

- `tcp_bharmonic_candidate_sequence.ngc`
- holds `X1500 Y850 Z-600` fixed
- runs the C0 B-angle scaling poses and B90 C-quadrant poses
- starts with `G43.4`
- intended run order:
  1. candidate HAL loaded with `sim-bharm-enable = FALSE`
  2. same sequence with `sim-bharm-enable = TRUE` in simulation only

## 2026-05-04 Full LinuxCNC B-Harmonic Sim Smoke Passed

Added:

- `configs/sim/head_head_5axis/head_head_bharmonic_sim.ini`
- `configs/sim/head_head_5axis/headhead_bharmonic_linuxcnc_smoke.py`

The dedicated sim INI:

- uses `headheadkins coordinates=XYZBC`
- opens `tcp_bharmonic_candidate_sequence.ngc`
- includes the candidate HAL file after the normal math/TWP HAL
- leaves `headheadkins.sim-bharm-enable = FALSE` at startup
- is a sim-only config; do not use it for the real machine

Runtime checks:

- launched:
  `linuxcnc -r configs/sim/head_head_5axis/head_head_bharmonic_sim.ini`
- confirmed candidate coefficients were loaded and disabled:
  - `headheadkins.sim-bharm-enable = FALSE`
  - `headheadkins.bharm-m.sin.z = 0.3182674`
  - `headheadkins.tool-frame-w.z = -1`
- ran `headhead_bharmonic_linuxcnc_smoke.py`

LinuxCNC sim smoke result:

- disabled max fixed-tip TCP error: `0.000000000 mm`
- enabled max fixed-tip TCP error: `0.000000000 mm`

The first smoke attempt exposed two script issues, both corrected:

- this sim must use home-all instead of sequential homing
- TCP verification must use `joint.N.pos-fb`, not `joint.N.motor-pos-fb`,
  because the Z joint has a home motor offset

The smoke test left `sim-bharm-enable = TRUE` for inspection, then the temporary
sim realtime session was unloaded with `halrun -U`. A follow-up `halcmd getp`
confirmed the `headheadkins` pins were gone.

Current offline conclusion:

- zero-default behavior is verified
- HAL pin loading is verified
- non-GUI math is verified
- LinuxCNC sim forward/inverse fixed-tip behavior is verified with the
  machine-fixed B-harmonic candidate enabled
- this is still not a live-machine candidate until the visual sim check and
  operator review are complete

## 2026-05-04 Offline Handoff Ready for Next Probe Run

Reran the dedicated head-head B-harmonic LinuxCNC sim before preparing the live
handoff:

- launched
  `linuxcnc -r configs/sim/head_head_5axis/head_head_bharmonic_sim.ini`
- ran `configs/sim/head_head_5axis/headhead_bharmonic_linuxcnc_smoke.py`
- disabled max fixed-tip TCP error: `0.000000000 mm`
- enabled max fixed-tip TCP error: `0.000000000 mm`
- unloaded the temporary sim realtime session with `halrun -U`
- confirmed `headheadkins.sim-bharm-enable` was gone after unload

Startup config correction:

- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic.hal`
  now persists the validated C-center correction at restart:
  - `headheadkins.cal-c-to-b.x = +0.035886006`
  - `headheadkins.cal-c-to-b.y = +0.009526306`
  - `headheadtwp.cal_c_to_b_x = +0.035886006`
  - `headheadtwp.cal_c_to_b_y = +0.009526306`
- the previous `cal-b-to-tool.z = +0.815000` and
  `c-zero-offset = -0.024500` startup values were left unchanged because those
  were part of the validated live test state before the high-B fitting work.

Next machine probing status:

- ready for a limited diagnostic probe run after the operator restarts the TCPC
  Probe Basic test config, homes, and positions over the sphere
- do not add `head_head_bharmonic_candidate.hal` to the real machine config
- if testing the B-harmonic candidate, load the candidate pins manually while
  idle, leave the enable pin false until immediately before the run, then set
  it false again when the run finishes
- use `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- leave `#711 = 0.0` for the first run so it collects C0 only:
  `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`
- do not run the C180 repeat or C-quadrant high-B program until the C0
  candidate-on result is inspected offline

Pre-run checks after restart:

- `headheadkins.cal-c-to-b.x` should read about `0.035886006`
- `headheadkins.cal-c-to-b.y` should read about `0.009526306`
- `headheadtwp.cal_c_to_b_x` should read about `0.035886006`
- `headheadtwp.cal_c_to_b_y` should read about `0.009526306`
- `headheadkins.sim-bharm-enable` should read `FALSE` before deliberate
  candidate testing
- `motion.digital-out-00`, `motion.digital-out-01`, and `motion.probe-input`
  should all be `FALSE` before cycle start

## 2026-05-04 Candidate-On C0 Probe Validation

The operator manually checked the probe trigger, cleared the paused state, and
the controller returned to:

- `halui.program.is-idle = TRUE`
- `halui.program.is-paused = FALSE`
- `motion.probe-input = FALSE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`

Loaded the machine-fixed B-harmonic diagnostic coefficients from
`configs/sim/head_head_5axis/head_head_bharmonic_candidate.hal` with
`headheadkins.sim-bharm-enable = FALSE`, then enabled it at `B0 C0`. The B0
tool offset did not jump when enabled. The path was disabled immediately after
the completed probe run:

- `headheadkins.sim-bharm-enable = FALSE`

The first candidate-on attempt was aborted for probe behavior. It logged only
these result CSV rows and should not be used for fit validation:

- `tcpc-b-angle-scaling-diagnostic-2pass-results.csv` lines `25-27`
- line `27` is `B+30 C0` pass 1 only

The second candidate-on C0 run completed cleanly. Use only accepted pass-2
result rows:

- lines `29, 31, 33, 35, 37, 39, 41, 43`

Candidate-on C0 quality:

- B0 open/close drift: `+0.018077 X`, `+0.001405 Y`, `-0.002832 Z`,
  `0.018351 mm` 3D
- pass-2 max residuals: U `0.006865 mm`, V `0.008333 mm`
- pass-2 corrected diameters:
  - U `30.142549..30.219870 mm`
  - V `30.216333..30.229667 mm`
- X/Y/Z motor following errors remained effectively zero in the logged axis
  state rows

Candidate-off versus candidate-on C0 result:

| State | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| candidate off, prior clean C0 | `0.320592 mm` | `0.673010 mm` |
| candidate on, clean C0 | `0.108201 mm` | `0.189342 mm` |

Candidate-on C0 deltas versus its B0 open/close average:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+30 C0` | `-0.009897` | `-0.040287` | `-0.025141` | `0.048508` |
| `B-30 C0` | `+0.004306` | `-0.019662` | `+0.005996` | `0.021003` |
| `B+60 C0` | `+0.010792` | `-0.083620` | `-0.012162` | `0.085187` |
| `B-60 C0` | `+0.008176` | `-0.094871` | `-0.028618` | `0.099430` |
| `B+90 C0` | `+0.063705` | `-0.101798` | `+0.006001` | `0.120238` |
| `B-90 C0` | `-0.068462` | `-0.169714` | `-0.048583` | `0.189342` |

Interpretation:

- The B-harmonic candidate materially improved the C0 high-B result.
- The old `B-90` positive-Z signature was mostly removed.
- Remaining error is now mostly machine-Y at high B, especially `B-90`.
- The result is within the practical `0.2 mm` current target for C0, but it is
  not yet proven at C180 or other C quadrants.

Program update:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` now supports
  `#711 = 2.0` for C180-only validation, avoiding another C0 rerun.
- Mode meanings:
  - `#711 = 0.0`: C0 only
  - `#711 = 1.0`: C0 then C180
  - `#711 = 2.0`: C180 only
- current file mode has been set to `#711 = 2.0` for the next run; reload the
  NGC in Probe Basic before cycle start

Next live recommendation:

- keep the machine idle while deciding
- if continuing now, run C180-only with the same B-harmonic candidate enabled
  temporarily
- after that run, disable `headheadkins.sim-bharm-enable` immediately and
  compare C180 against the C0 improvement before any C90/C270 quadrant test

## 2026-05-04 Candidate-On C180 Probe Validation

The C180-only candidate-on pass completed with no probe errors. The diagnostic
path was disabled immediately after completion:

- `headheadkins.sim-bharm-enable = FALSE`
- `halui.program.is-idle = TRUE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`
- `motion.probe-input = FALSE`

Use accepted pass-2 rows from
`tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

- lines `45, 47, 49, 51, 53, 55, 57, 59`

Candidate-on C180 quality:

- B0 open/close drift: `-0.011150 X`, `+0.004700 Y`, `+0.001091 Z`,
  `0.012149 mm` 3D
- pass-2 max residuals: U `0.007699 mm`, V `0.003335 mm`
- pass-2 corrected diameters:
  - U `30.148024..30.250744 mm`
  - V `30.210500..30.217996 mm`
- X/Y/Z motor following errors remained effectively zero in the logged axis
  state rows

Candidate-on C180 deltas versus its B0 open/close average:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+30 C180` | `-0.112635` | `-0.047842` | `-0.048767` | `0.131733` |
| `B-30 C180` | `-0.018993` | `+0.031533` | `+0.027880` | `0.046178` |
| `B+60 C180` | `-0.193129` | `-0.103929` | `-0.065487` | `0.228885` |
| `B-60 C180` | `-0.095269` | `+0.063543` | `+0.020045` | `0.116257` |
| `B+90 C180` | `-0.065450` | `-0.119525` | `-0.014121` | `0.137001` |
| `B-90 C180` | `+0.059216` | `+0.134433` | `-0.030788` | `0.150089` |

Candidate-on C0/C180 summary:

| Set | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| C0 | `0.108201 mm` | `0.189342 mm` |
| C180 | `0.145308 mm` | `0.228885 mm` |
| C0 + C180 combined | `0.128105 mm` | `0.228885 mm` |

Interpretation:

- The B-harmonic candidate is effective at both C0 and C180.
- C180 is slightly weaker than C0 and exceeds the practical `0.2 mm` target at
  `B+60 C180`.
- The old large high-B Z error is still mostly removed.
- Remaining error is C-dependent and includes a significant X component at
  positive B on C180, so do not make this candidate persistent yet.

Recommended next step:

- stop live probing temporarily and fold the candidate-on C0/C180 data into
  the offline fitter
- only after that, decide whether the next live run should be a very short
  side-quadrant check at `C90/C270` and `B+90/B-90`, rather than a full long
  quadrant program

## 2026-05-04 Offline Fold-In After Candidate-On C0/C180

Updated `tcpc_expanded_geometry_fit.py` and regenerated
`TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` so the fitter now tracks:

- candidate-on C0 validation rows: `29, 31, 33, 35, 37, 39, 41, 43`
- candidate-on C180 validation rows: `45, 47, 49, 51, 53, 55, 57, 59`
- those rows are modeled with the validated C-center plus the machine-fixed
  B-harmonic candidate as the active kinematic state

Report conclusions:

- candidate-on C0 non-B0 RMS/max: `0.108201 / 0.189342 mm`
- candidate-on C180 non-B0 RMS/max: `0.145308 / 0.228885 mm`
- candidate-on C0+C180 combined non-B0 RMS/max:
  `0.128105 / 0.228885 mm`
- the candidate should remain diagnostic-only; do not make it persistent
- existing side-quadrant data predicts the highest remaining risk at
  `C90/C270` high-B poses:
  - predicted side-quadrant high-B RMS/max: `0.3782 / 0.4238 mm`
  - predicted worst rows are around `B+90 C270` and `B-90 C270`

Prepared next short live test:

- `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` now supports
  `#711 = 3.0`
- current file mode is set to `#711 = 3.0`
- this mode runs only:
  - `C90`: `B0`, `B+90`, `B-90`, `B0`
  - `C270`: `B0`, `B+90`, `B-90`, `B0`
- it skips C0 and C180 and avoids the full long quadrant program

Next live handoff:

- reload `tcpc_b_angle_scaling_diagnostic.ngc` in Probe Basic before cycle
  start
- keep the B-harmonic candidate disabled until immediately before the run
- enable it only after confirming LinuxCNC is idle, probe input is false, gates
  are false, and B/C are at a known safe start pose
- disable `headheadkins.sim-bharm-enable` immediately after the pass

## 2026-05-04 Candidate-On Side-Quadrant Validation

The short side-quadrant run completed and the B-harmonic diagnostic path was
disabled afterward. Use accepted pass-2 rows in
`tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

- C90/C270 side validation: lines `61, 63, 65, 67, 69, 71, 73, 75`

Candidate-on side result:

| Set | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| C90 high-B | `0.334257 mm` | `0.457914 mm` |
| C270 high-B | `0.470808 mm` | `0.615783 mm` |
| C90 + C270 high-B | `0.408282 mm` | `0.615783 mm` |
| C0 + C180 + side combined | `0.232339 mm` | `0.615783 mm` |

Worst side pose:

- `B+90 C270`: dX `-0.123188`, dY `+0.580494`, dZ `+0.164440`,
  `0.615783 mm` 3D

Offline refit with the side rows added:

| Model | all direct RMS/max | side direct RMS/max | note |
| --- | ---: | ---: | --- |
| current live candidate | `0.232339 / 0.615783 mm` | `0.408282 / 0.615783 mm` | diagnostic only |
| incremental C-frame on live candidate | `0.202139 / 0.494928 mm` | `0.312621 / 0.494928 mm` | improves side, regresses C0/C180 |
| replacement machine plus C-frame | `0.197311 / 0.434945 mm` | `0.283429 / 0.434945 mm` | ill-conditioned, do not trust |
| C-tilted replacement machine plus C-frame | `0.185867 / 0.408958 mm` | `0.251974 / 0.408958 mm` | best current clue, still too large |

Decision:

- keep the validated C-center correction loaded in the TCPC config
- do not make the machine-fixed B-harmonic candidate persistent
- do not run another live probe pass yet
- the C-axis tilt coupling model is the strongest clue so far, but it is still
  too flexible and leaves too much side error
- continue offline work on a smaller constrained C-tilt/harmonic correction
  family and simulation verification before returning to machine probing

## 2026-05-04 B/C Cross-Harmonic Candidate Prepared

Continued offline fitting after the machine was reported idle. The side error
has a strong `sin(B) * sin(C)` signature in machine Y/Z, and a same-direction
side residual is explained by `(1-cos(B)) * sin(C)^2`. These terms are zero at
`B0`, so enabling the candidate at `B0` should not move the TCP.

Added a simulation-gated machine-world B/C cross correction family to
`headheadkins`:

- existing gate: `headheadkins.sim-bharm-enable`
- new pins:
  - `headheadkins.bcross.sinb-sinc.x/y/z`
  - `headheadkins.bcross.omcb-sinc.x/y/z`
  - `headheadkins.bcross.omcb-sin2c.x/y/z`
  - `headheadkins.bcross.sinb-cosc.x/y/z`
  - `headheadkins.bcross.omcb-cosc.x/y/z`
- all new pins default to zero
- with `sim-bharm-enable = FALSE`, the path contributes zero

The candidate is incremental on top of the previously tested machine-fixed
B-harmonic terms. Offline direct-metric prediction:

| Data set | current machine B-harmonic | next B/C cross candidate |
| --- | ---: | ---: |
| C0 candidate-on | `0.108201 / 0.189342 mm` | `0.078760 / 0.116901 mm` |
| C180 candidate-on | `0.145308 / 0.228885 mm` | `0.111771 / 0.166446 mm` |
| C90/C270 side candidate-on | `0.408282 / 0.615783 mm` | `0.085480 / 0.085480 mm` |
| all candidate-on validation | `0.232339 / 0.615783 mm` | `0.094009 / 0.166446 mm` |

Holdout-style checks:

- original C0 scaling prediction: `0.073636 / 0.115399 mm`
- corrected B90 C-quadrant prediction: `0.103511 / 0.148967 mm`
- clean B-axis holdout prediction: `0.095375 / 0.132854 mm`

Candidate coefficients are now in:

- `configs/sim/head_head_5axis/head_head_bharmonic_candidate.hal`

Verification completed:

- `python3 -m py_compile` passed for the fitter and sim verification scripts
- `python3 configs/sim/head_head_5axis/headhead_bharmonic_verify.py` passed:
  - zero/default max offset delta: `0 mm`
  - tool-frame formula max delta: `0`
  - candidate forward/inverse max error: `8.04e-14 mm`
- `make -j2` completed in `src`
- `sudo make setuid` completed
- `git diff --check` passed
- RS274 preview parse passed for
  `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc`
- RS274 task-mode parse reached the first simulated probe move and aborted at
  the expected no-contact probe check, so syntax before motion is valid

Prepared next validation run:

- `tcpc_b_angle_scaling_diagnostic.ngc` now supports `#711 = 4.0`
- current file is set to `#711 = 4.0`
- sequence:
  - C0: `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`
  - C180: `B0, B+30, B-30, B+60, B-60, B+90, B-90, B0`
  - side: C90 and C270 with `B0, B+90, B-90, B0`

Important handoff:

- the running LinuxCNC session still has the old loaded kinematics module
- close/restart the TCPC Probe Basic config before testing this candidate so
  the new `bcross.*` pins exist
- after restart, confirm `headheadkins.sim-bharm-enable = FALSE` before loading
  coefficients
- do not make the B/C cross candidate persistent until the live validation
  passes

## 2026-05-04 B/C Cross-Harmonic Live Validation Complete

The B/C cross candidate run completed after one operator pause/reset of the
wireless probe. The accepted pass-2 probe rows looked clean; pass-1 rows are
intentionally rejected and no pass-2 rows were rejected.

Accepted pass-2 rows in
`configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

- C0: `77,79,81,83,85,87,89,91`
- C180: `93,95,97,99,101,103,105,107`
- C90/C270 side: `109,111,113,115,117,119,121,123`

Immediate live-state cleanup was completed:

- `headheadkins.sim-bharm-enable = FALSE`
- `halui.program.is-idle = TRUE`
- `motion.probe-input = FALSE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`

Probe quality on the accepted pass-2 rows:

- max U center residual: `0.008136 mm`
- max V center residual: `0.004583 mm`
- corrected U diameter range: `30.146536..30.255703 mm`
- corrected V diameter range: `30.158000..30.241334 mm`
- max X/Y/Z motor following error in the captured axis-state rows:
  `0.000002 / 0.000000 / 0.000000 mm`

Live direct validation compared with the previous machine B-harmonic-only
candidate:

| Set | B-harmonic only RMS/max | B-harmonic plus B/C cross RMS/max |
| --- | ---: | ---: |
| C0 | `0.108201 / 0.189342 mm` | `0.083627 / 0.127554 mm` |
| C180 | `0.145308 / 0.228885 mm` | `0.116273 / 0.176626 mm` |
| C90/C270 side | `0.408282 / 0.615783 mm` | `0.079909 / 0.105982 mm` |
| all validation | `0.232339 / 0.615783 mm` | `0.096378 / 0.176626 mm` |

Worst remaining point is `B+60 C180` at `0.176626 mm`. The side quadrants are
now much better than with the B-harmonic-only candidate.

`tcpc_expanded_geometry_fit.py` and
`TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` have been updated so the new run is
modeled with the active C-center, machine B-harmonic, and B/C cross correction
subtracted before any further offline model is applied.

Next action:

- do not rerun the same long validation immediately
- keep the B/C cross candidate non-persistent and gated off
- continue offline fitting against the new B/C cross validation rows before
  selecting the next live probe task

## 2026-05-04 Refined B/C Cross Candidate Prepared

Continued offline work after the machine was shut down for the night. The new
B/C-cross-active rows were used as an independent live-state data set, not
merged blindly with the older B-harmonic-only rows.

Refit result:

- current B/C cross candidate on combined live rows:
  `0.095201 / 0.176626 mm`
- refined replacement machine plus B/C cross fit on combined live rows:
  `0.072421 / 0.133632 mm`
- corrected B90 holdout direct RMS/max with refined fit:
  `0.098309 / 0.150983 mm`
- clean B-axis holdout direct RMS/max with refined fit:
  `0.080505 / 0.100168 mm`
- original C0 scaling direct RMS/max with refined fit:
  `0.042392 / 0.076438 mm`
- direct fit rank/condition: `24 / 2.85e+00`

Prepared files:

- refined candidate HAL:
  `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`
- dedicated sim config now points at the refined HAL:
  `configs/sim/head_head_5axis/head_head_bharmonic_sim.ini`
- `tcpc_expanded_geometry_fit.py` and
  `TCPC_EXPANDED_GEOMETRY_FIT_REPORT.md` now include the post-B/C-cross refit
  and the refined candidate parameters

Verification completed:

- `python3 -m py_compile` passed for the fitter and B-harmonic verification
  scripts
- `python3 configs/sim/head_head_5axis/headhead_bharmonic_verify.py` passed:
  - zero/default max offset delta: `0 mm`
  - tool-frame formula max delta: `0`
  - candidate forward/inverse max error: `8.04e-14 mm`
- dedicated LinuxCNC sim smoke test passed:
  - disabled max fixed-tip TCP error: `0.000000000 mm`
  - enabled max fixed-tip TCP error: `0.000000000 mm`
- the temporary sim HAL session was stopped and unloaded afterward

Next live task:

- start the TCPC Probe Basic config fresh
- confirm `headheadkins.sim-bharm-enable = FALSE`
- load `head_head_bharmonic_refined_candidate.hal`, not the previous
  `head_head_bharmonic_candidate.hal`
- verify at least:
  - `headheadkins.bharm-m.sin.z = 0.312123080`
  - `headheadkins.bharm-m.omc.y = 0.111703959`
  - `headheadkins.bcross.sinb-sinc.y = 0.325723886`
  - `headheadkins.bcross.omcb-sin2c.y = -0.255875638`
- enable `headheadkins.sim-bharm-enable` only immediately before cycle start
- run `nc_files/calibration/tcpc_b_angle_scaling_diagnostic.ngc` with
  `#711 = 4.0`
- disable `headheadkins.sim-bharm-enable` immediately after completion or any
  stop/error

## 2026-05-05 Refined B/C Cross Candidate Live Validation Complete

The refined candidate run completed cleanly. The candidate was disabled
immediately after completion and verified off:

- `headheadkins.sim-bharm-enable = FALSE`
- `halui.program.is-idle = TRUE`
- `motion.probe-input = FALSE`
- `motion.digital-out-00 = FALSE`
- `motion.digital-out-01 = FALSE`

Accepted pass-2 rows in
`configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-b-angle-scaling-diagnostic-2pass-results.csv`:

- C0: `125,127,129,131,133,135,137,139`
- C180: `141,143,145,147,149,151,153,155`
- C90/C270 side: `157,159,161,163,165,167,169,171`

Probe quality:

- max U center residual: `0.010268 mm`
- max V center residual: `0.005000 mm`
- corrected U diameter range: `30.138857..30.249869 mm`
- corrected V diameter range: `30.156807..30.243000 mm`
- X/Y/Z motor following error remained effectively zero in the captured rows

Measured direct validation:

| Set | non-B0 RMS | non-B0 max |
| --- | ---: | ---: |
| C0 | `0.044921 mm` | `0.094234 mm` |
| C180 | `0.098680 mm` | `0.125893 mm` |
| C90/C270 side | `0.077269 mm` | `0.097132 mm` |
| all validation | `0.076818 mm` | `0.125893 mm` |

Live progression:

| Candidate | all-validation RMS/max |
| --- | ---: |
| machine B-harmonic only | `0.232339 / 0.615783 mm` |
| B/C cross | `0.096378 / 0.176626 mm` |
| refined B/C cross | `0.076818 / 0.125893 mm` |

The refined candidate is the best validated live candidate so far, but it is
still simulation-gated and not persistent. A post-refined refit using all live
rows slightly lowers combined RMS but worsens maximum error, so do not retune
again or rerun the long validation until the persistence criteria are reviewed.
