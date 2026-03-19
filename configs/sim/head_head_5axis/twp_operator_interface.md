# Head-Head TWP Operator Interface Proposal

## Scope

This note defines a practical operator-facing TWP model for the head-head
machine. It is a design target for later LinuxCNC integration, not an
implemented feature yet.

Companion controller/post target:

- [fanuc_like_twp_tcpc_contract.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/fanuc_like_twp_tcpc_contract.md)

The goal is to keep the operator model close to standard industrial behavior
while remaining realistic for a LinuxCNC remap/UI implementation.

## Design Principles

- TWP is layered on top of the existing head-head TCP-capable transform model.
- TWP must not change the physical machine zero conventions.
- TWP must be explicit and stateful:
  - off
  - defined
  - active
- TWP must be cancellable without ambiguity.
- Probe Basic should be the primary operator path.
- G-code/remap support should mirror the same state model used by the UI.

## Recommended Operator Model

### 1. World Mode

Default state:

- no tilted plane is active
- programming is in the normal world/work coordinate frame
- `B/C` are ordinary machine/tool orientation axes

### 2. Define TWP

The operator defines:

- TWP origin in world coordinates
- plane orientation from `B/C`
- optional plane-local rotation about plane normal

Recommended initial implementation:

- use the current `B/C` pose as the plane orientation source
- use the current tool-tip position as the default TWP origin
- allow explicit origin override later

### 3. Activate TWP

When active:

- linear commands are interpreted in plane-local coordinates
- the kinematics layer transforms them back into world `XYZBC`
- TCP remains coherent with the tilted plane

### 4. Cancel TWP

Cancellation returns motion interpretation to the normal world/work frame
without silently changing the machine pose.

## Recommended Control Surfaces

### Probe Basic UI

Primary controls:

- `Set TWP From Current BC`
- `Set TWP Origin From Current Position`
- `Activate TWP`
- `Cancel TWP`
- `Reset TWP`

Display fields:

- TWP state: off / defined / active
- TWP origin `XYZ`
- TWP orientation `BC`
- optional plane-local angle about the plane normal

### G-code / Remap Layer

Recommended long-term target:

- align with familiar industrial semantics where practical
- avoid inventing arbitrary one-off commands if standard behavior can be
  represented clearly

Pragmatic staged approach:

1. UI + HAL/internal state first
2. remap commands second
3. post/CAM workflow last

## First Implementation Slice

The first production-oriented TWP implementation should support only:

- define TWP from the current tool tip plus programmed `B/C`
- optional plane-normal rotation
- activate / cancel
- plane-local linear motion at fixed stored `B/C`
- rejection of rotary changes while TWP motion is active

Current simulation prototype:

- `head_head_twp_state.py`
- `head_head_twp_state.hal`

Current prototype commands:

- `cmd_set_origin_from_current`
- `cmd_set_orientation_from_current`
- `cmd_set_from_current`
- `cmd_set_normal_rotation`
- `cmd_activate`
- `cmd_cancel`
- `cmd_reset`

Current debug/helper M-code binding:

- `M150` set origin from current tool-tip position
- `M151` set orientation from current `B/C`
- `M152` set both from current pose
- `M153` activate
- `M154` cancel
- `M155` reset
- `M156 P...` set plane-normal rotation

Current prototype outputs:

- `twp_origin_{x,y,z}`
- `twp_b_angle`
- `twp_c_angle`
- `twp_normal_rotation`
- `plane_x_*`, `plane_y_*`, `plane_z_*`
- `state_code`
- `valid`
- `active`

Current `state_code` values:

- `0` undefined
- `1` partial
- `2` defined
- `3` active

Current machine-facing sample-data path:

- `G43.4` TCPC on
- `G68.2 [B.. C..] [R..]` define and activate TWP from current tool tip
- ordinary `G0/G1` in plane-local coordinates
- `G69` cancel TWP
- `G49.1` TCPC off

The older M-codes remain useful for manual debugging, but they are no longer
the intended post target.

Current machine-facing motion model:

- active `G68.2` changes ordinary `G0/G1 X/Y/Z` into plane-local motion
- with TCPC on and TWP off, manual `B/C` positioning is allowed
- `G68.2` may omit `B/C` and capture the current rotary orientation
- `G69` returns motion to normal world coordinates and allows `B/C` moves again

Legacy helper path still available for debugging:

- `G88.5 P.. Q.. R.. [L..]`
- explicit helper moves in the stored plane
- useful for transform debugging and regression tests, but not the operator model

It should explicitly not try to solve on day one:

- arbitrary 3-point plane fitting
- dynamic in-cut plane changes
- post-specific command compatibility
- automatic plane solving from work features

## State Model

Recommended internal state:

- `twp-enabled` boolean
- `twp-valid` boolean
- `twp-origin.{x,y,z}`
- `twp-b-angle`
- `twp-c-angle`
- `twp-normal-rotation`

Later extensions:

- plane basis vectors
- source coordinate system id
- saved presets

## Safety / Predictability Rules

- TWP activation should fail if the plane definition is incomplete
- cancelling TWP must not jump the machine unexpectedly
- tool length compensation changes must be rejected while TWP is active
- tool changes and current-tool-number changes must be rejected while TWP is active
- after `G69`, normal tool-state operations must work again without leftover TWP state
- a TWP move that exceeds travel limits must fail without partial motion
- after a limit reject, operators must be able to recover with:
  - `G69`
  - safe reposition
  - re-entering `G43.4` / `G68.2` if needed
- with TCPC on and TWP off, manual `B/C` moves are allowed
- while TWP is active, `B/C` moves are blocked
- after `G69`, operators may move `B/C` first and then enter `G68.2`
- program abort should leave TWP/TCPC state unchanged until explicit cancel
- estop should clear TWP automatically
- re-home should clear TWP automatically
- UI must make the active frame obvious
- the operator must always be able to see:
  - current world pose
  - current plane definition
  - whether motion is being interpreted in TWP or world mode

## Validation Expectations

The operator interface is acceptable only if:

- activating TWP does not move the tool unexpectedly
- cancelling TWP does not move the tool unexpectedly
- jog and MDI behavior match file-execution behavior
- the same `B/C` and origin produce the same plane in UI, remap, and sim
