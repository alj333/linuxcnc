# Head-Head TCP/TWP Design Baseline

Status: design background. The authoritative implemented TWP and Fusion post
contract is
[TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md).

## Scope

This note defines the intended kinematic model and simulation plan for the
upgraded head-head 5-axis machine.

It is separate from the completed SSI work:

- Mesa firmware/resource definition
- SSI absolute encoder integration
- Probe Basic machine startup baseline

The purpose of this document is to lock the machine conventions before
implementing:

- a new head-head kinematics component
- TCP behavior
- TWP behavior
- a LinuxCNC simulation model

Current branch status:

- `headheadkins` provides the commissioned `XYZBC` forward/inverse TCPC path
- the active `G43` tool offset and length-aware calibration revision
  `2026082601` are evaluated inside that path
- synchronized TWP is implemented as switchkins type 1 in the same module
- type 1 reuses the complete TCPC/tool-length evaluation and adds only the
  reciprocal tilted program-frame transform
- guarded `G68.2`/`G53.1`/`G69` remaps and interpreter restrictions are
  implemented and physically commissioned through B `+/-30 deg`
- a production-equivalent T3/T4 test passed 18,931 consecutive servo samples
  across four stationary type switches, including nonzero G54, Fusion rotating
  `ZXZ` I/J/K input, `R17`, and a wrapped C assertion, with public TCPC off
- the physical low-angle T4 grid completed all 24 signed-B/C poses and 112
  motion-gated contacts; WORLD closure was `0.052759 mm` and maximum
  transformed center error was `0.205463 mm`
- component-loss/restart and all 15 legacy TCPC/TWP behavior scenarios pass
- the default real-machine cut-test INI remains TWP-locked; the dedicated
  supervised INI is physically validated and is released for controlled CAM
  cut testing only

## Machine Topology

Physical stack, tool to base:

- spindle
- B axis
- C axis
- Z axis
- X axis
- frame
- Y axis

This is a head-head machine:

- both rotary axes are on the tool side
- there is no rotary table on the work side

## Coordinate Conventions

### Preferred Production Convention

If the mechanical rebuild still allows it, the machine should be brought into
standard right-hand industrial convention rather than preserving provisional
non-standard sign choices.

Preferred production convention:

- `+X` moves to the right
- `+Y` moves away from the operator
- `+Z` moves up, away from the table
- positive rotary motion follows the right-hand rule
- `B = 0`, `C = 0` keeps the tool vector in `-Z`

Preferred rotary convention under the right-hand rule:

- `+B` is positive rotation about `+Y`
- `+C` is positive rotation about `+Z`

Consequences of the preferred production convention:

- positive `C` is counterclockwise when viewed from above
- positive `B` tilts the tool toward `-X` from the `-Z` home vector

This is the recommended long-term convention because it aligns:

- machine kinematics
- LinuxCNC math
- simulation
- CAM/post assumptions
- future troubleshooting

### Provisional Convention Captured During Rebuild

Standing at the front of the machine:

- `+X` moves from left to right
- `+Y` moves from the back of the machine toward the operator
- `+Z` moves up, away from the table

Home rotary pose:

- `B = 0`
- `C = 0`
- tool vector points in `-Z` toward the table

Rotary axis directions:

- `B` axis is parallel to machine `Y`
- `C` axis is parallel to machine `Z`

Rotary positive directions:

- `+B` tilts the tool toward `+X`
- `+C` is clockwise when viewed from above looking down along `+Z`

Rotary limits:

- `B`: `-100` to `+100` degrees
- `C`: `-360` to `+360` degrees

These values were captured during the rebuild discussion and are useful as a
record of the current understanding. They should be treated as provisional if
the machine is reworked to match standard industrial convention.

## Mathematical Sign Mapping

### Preferred Production Mapping

If the machine is standardized to right-hand convention, the kinematic signs
become simpler:

- physical `+B` corresponds to mathematical `Ry(+B)`
- physical `+C` corresponds to mathematical `Rz(+C)`

Starting tool vector:

- `t0 = (0, 0, -1)`

Then:

```text
t(B, C) = Rz(C) * Ry(B) * t0
```

### Provisional Mapping From Rebuild Discussion

The physical axis directions above are not the same as standard right-hand
positive rotation used in most rotation matrices.

For the provisional rebuild convention:

- physical `+B` corresponds to mathematical rotation `Ry(-B)`
- physical `+C` corresponds to mathematical rotation `Rz(-C)`

Starting tool vector:

- `t0 = (0, 0, -1)`

Tool direction with the current physical sign convention:

```text
t(B, C) = Rz(-C) * Ry(-B) * t0
```

If the machine is not standardized, this provisional convention must be used
consistently in:

- forward kinematics
- inverse kinematics
- TCP
- TWP
- simulation

## Geometry Model

The real machine must not assume perfect intersecting rotary axes.

The kinematics model must support both:

- nominal geometry from CAD
- calibrated geometry from real machine measurements

The following machine parameters are required.

Rotary zero offsets:

- `b_zero_offset_deg`
- `c_zero_offset_deg`

Rotary center offsets:

- `c_to_b_x`
- `c_to_b_y`
- `c_to_b_z`

Spindle / tool reference offsets from B:

- `b_to_tool_x`
- `b_to_tool_y`
- `b_to_tool_z`

Tool length:

- tool length is applied along the spindle axis
- this should remain separate from fixed head geometry where practical

Known current assumption:

- spindle centerline is offset about `+25 mm` in `Y` from the `C` axis center
- nominal `C` center to `B` center offset for the current visual/kinematic
  scaffold is `(0, 0, -270) mm`
- nominal `B` center to tool reference offset is `(0, +25, -180) mm`

Unknowns to be finalized after the head and Z-frame rebuild:

- exact `C` to `B` offset
- exact `B` to spindle/tool reference offset
- residual manufacturing and assembly error

## Calibration Requirement

Calibration is a first-class requirement, not a later cleanup item.

The implementation must allow real-machine correction of:

- rotary zero positions
- rotary center offsets
- spindle/tool reference offsets
- small non-ideal assembly deviations

Expected calibration stages:

1. nominal values from Fusion 360 / CAD
2. manual measured values on the rebuilt machine
3. refined calibration from test cuts / probe routines / reference sphere tests

The kinematics code should read parameters from HAL or INI, not compile-time
constants.

Current simulation constraint:

- the head-head simulation now uses one shared geometry baseline for both
  `headheadkins` and the vismach model
- the visual model must not carry hidden pivot offsets that differ from the
  kinematics pins
- axis `Z` remains the user-facing tool-tip travel range
- internal `JOINT_2` is the `C` pivot-center axis and therefore has a
  different travel range in the simulation:
  - `MIN_LIMIT = -630`
  - `MAX_LIMIT = 450`
  - `HOME = 450`
- the visual sim renders moving-table `Y` with inverted table motion so travel
  direction matches a table-axis machine
- the visual sim includes table-mounted alignment aids for TCP checking:
  - cyan post and cross
  - green centerlines
  - corner markers

## TCP Requirements

When TCP is enabled:

- the tool tip must remain stationary in Cartesian space when `B` or `C`
  changes and no Cartesian motion is commanded
- `X/Y/Z` must be compensated automatically by the kinematics
- behavior must be consistent in:
  - jogging
  - MDI
  - G-code execution

TCP is not optional glue around existing motion. It must be designed into the
kinematics behavior and state model.

## TWP Requirements

When TWP is enabled:

- the user sets the tilted work plane using `B` and `C`
- motion commanded in the rotated work plane is transformed back to machine
  coordinates through the kinematics
- TWP must be coherent with TCP, not a separate approximation layer

Expected operator model:

- choose plane orientation
- work/program in the rotated plane
- LinuxCNC resolves this to machine `XYZBC`

Recommended first operator interface:

- define TWP from current `B/C`
- define TWP origin from current tool-tip position
- activate / cancel explicitly
- keep TWP state visible in the UI at all times
- keep the first implementation narrow and predictable before adding richer
  plane-definition workflows

## Current TWP Architecture

The production-facing implementation uses two switchkins types exported by
the same `headheadkins` component:

- type 0: normal world-programming frame; `G43.4` optionally enables TCPC
- type 1: the separate tilted-work-plane frame with public TCPC disabled

Both types call the same active-tool snapshot and the same
`evaluate_tool_offset_world()` function. This includes the complete nominal
geometry, fitted common correction, tool-length differential correction,
coefficient-set ID checks, length-domain checks, and tool-reference handling.
There is no second TWP calibration or reduced tool model. Type 1 captures the
same calibrated tool-offset reference internally without asserting the public
`G43.4` TCPC state.

`G68.2` defines the frame but leaves type 0 selected. It accepts Fusion/Fanuc
`X/Y/Z/I/J/K` using rotating `ZXZ` Euler angles, as well as the commissioning
`B/C/R` assertion form. B/C must already have reached the matching orientation.
`G53.1` then performs the stationary type-1 handoff and latches:

- the exact reached `B/C` values, including the continuous C branch
- optional plane-normal rotation `R`
- the coordinate layer produced by rotating about the requested work-frame
  `X/Y/Z` pivot
- an internal calibrated tool-offset reference
- the current world point as the tilted-frame anchor

The first successful type-1 forward transform asserts a frame-ready pin. The
local coordinate at activation is the fully transformed coordinate about that
pivot, so changing kinematics type does not request joint motion. Normal
`G0/G1 X/Y/Z` blocks then map through the latched plane basis while `B/C` stay
fixed.

`G69` is a two-stage transaction. It first requests world kinematics and waits
for a successful world forward transform. Only after that confirmation does it
clear the stored frame. This ordering prevents live TWP or TCPC state from
being erased underneath an active type-1 transform.

Loss of the `headheadtwp` userspace process is a restart-only fault. The HAL
registration and last values can remain stale while the latched type-1
kinematics stays stationary, so neither continued motion nor an in-place `G69`
is an accepted recovery. A full LinuxCNC teardown and fresh launch restores
ready world type 0 with all TWP frame and transaction state clear.

The earlier HAL commands and `G88.5` transformed-motion path remain useful as
legacy simulation tools. They are not the production workpath.

Initial synchronized-TWP scope is intentionally narrow:

- linear `G0/G1` XYZ motion, non-faulting `G38.3`, and `G4` dwell
- fixed reached `B/C` for the life of the frame
- no `G38.2/G38.4/G38.5`, arcs, canned cycles, cutter compensation, WCS
  changes, G52/G92, tool selection/change, tool-offset changes, or program end
  before `G69`
- `G38.3` is limited to reviewed, supervised fixed-B/C routines and must return
  to a known clear point in the active frame before `G69`
- fail-closed length-model and state-transition checks

## Recommended Software Architecture

The current `trivkins` setup was only a bring-up path.

Production direction should be:

1. new head-head kinematics component
2. TCP support built into that kinematics model
3. TWP support built on the same transform model
4. Probe Basic as the primary UI path
5. AXIS retained only for troubleshooting

Implementation recommendation:

- write the new kinematics around the preferred standard right-hand convention
- if the interim machine wiring/signs differ during rebuild, handle that with
  temporary offsets or sign parameters
- do not bake a provisional non-standard sign convention permanently into the
  production math unless the final mechanics truly require it

Recommended branch separation:

- keep `ssi-invert-bench-2.9` as the encoder/machine baseline
- create a new branch for kinematics R&D, for example:
  - `head-head-kinematics-rnd`

## Simulation Plan

Target: full visual machine simulation in LinuxCNC to validate:

- kinematic math
- TCP behavior
- TWP behavior
- posted G-code behavior
- operator workflow before final machine commissioning

Recommended simulation phases:

### Phase 1: Mathematical Simulation

Build a simulation config that uses:

- the new head-head kinematics component
- fake joints / simulated axes
- no physical I/O dependencies

Purpose:

- validate forward and inverse kinematics
- validate TCP compensation
- validate TWP transforms
- validate sign conventions and rotary limits

### Phase 2: Visual Machine Simulation

Build a visual machine model using LinuxCNC simulation tools.

Preferred direction:

- custom `vismach` model
- STL or simplified geometry exported from Fusion 360

Purpose:

- see head motion and tool orientation
- confirm rotary sequence visually
- inspect reachable poses
- validate posted 5-axis paths before hardware testing

### Phase 3: Machine Config Integration

Once the math and visual sim are correct:

- integrate the kinematics into the real Probe Basic machine config
- retain AXIS as a fallback debug path

## Fusion 360 Use

The Fusion 360 model should be used for:

- nominal pivot geometry
- rotary axis locations
- spindle centerline offsets
- home pose confirmation
- STL export for visual simulation
- known validation poses for kinematic tests

Useful deliverables from Fusion:

- home-pose screenshots with axis arrows
- pivot dimension table
- exported STL or simplified meshes
- several known poses with expected `XYZBC`

## Acceptance Tests

Minimum acceptance tests for the new kinematics stack:

1. forward/inverse round-trip tests for known poses
2. tool vector test at `B=0`, `C=0` equals `-Z`
3. under the preferred production convention, positive `B` tilts toward `-X`
4. under the preferred production convention, positive `C` rotates
   counterclockwise from top view
5. TCP keeps the tool tip fixed while changing `B/C`
6. TWP transforms Cartesian motion correctly into machine motion
7. rotary limits are enforced correctly
8. simulation visual pose matches expected physical pose
9. posted Fusion 360 5-axis test programs run correctly in simulation
10. every servo cycle across G53.1/G69 entry and exit is free of joint-command
    and physical-TCP transients for both calibrated probe lengths
11. equivalent wrapped C assertions preserve the reached continuous branch
12. the commissioned length-model ID, evaluated length, correction blend, and
    internal TWP tool reference remain valid across the frame switch while
    public TCPC stays off

Current visual acceptance aids:

- cyan alignment post and cross for tool-tip coincidence checks
- green table centerlines for travel reading
- corner markers for table motion awareness
- moving-table `Y` visual inversion so the rendered table motion matches the
  intended machine behavior

## Open Geometry Items

These are intentionally unresolved until the rebuild is complete:

- final Z-frame geometry
- final head geometry
- exact `C` to `B` offset
- exact `B` to spindle/tool reference offset
- final calibration workflow

That does not block simulation work. The implementation should start with
nominal geometry and expose all critical offsets as configurable parameters.
