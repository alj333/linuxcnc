# Head-Head TWP Operator Interface Proposal

## Scope

This note defines a practical operator-facing TWP model for the head-head
machine. It is a design target for later LinuxCNC integration, not an
implemented feature yet.

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

- set TWP orientation from current `B/C`
- set TWP origin from current tool tip
- activate / cancel
- plane-local linear motion at fixed `B/C`

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

Current prototype M-code binding:

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

This is intentionally a HAL-driven prototype before any Probe Basic or remap
binding is added.

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
