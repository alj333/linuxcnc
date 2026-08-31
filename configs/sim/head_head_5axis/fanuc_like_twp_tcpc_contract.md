# Fanuc-Like TWP / TCPC Controller Contract

## Purpose

This note defines the target controller behavior for the head-head machine.

The goal is:

- operator workflow close to Fanuc
- Fusion post output that looks and behaves like a normal industrial 5-axis post
- freedom to simplify exact syntax where strict Fanuc compatibility adds pain
  without real value

This is a behavior contract first and a syntax contract second.

## Core Position

The machine should behave like this:

- `G0/G1` remain the normal motion commands
- TCPC and TWP are controller modes
- when TWP is active, ordinary `G0/G1 X/Y/Z` are interpreted in the tilted
  plane
- the post must not pre-transform every move into machine coordinates

That means the long-term implementation belongs in the kinematics/interpreter
path, not in a Python remap that tries to replace `G0/G1`.

## Modes

### 1. World Mode

Default behavior:

- no TWP active
- `X/Y/Z` are in the normal work/world frame
- `B/C` are ordinary rotary orientation axes

### 2. TCPC Mode

Behavior:

- tool center point compensation is active
- programming remains in the normal work/world frame
- rotary changes keep the tool tip coherent

### 3. TWP Mode

Behavior:

- a tilted plane is defined from:
  - TWP origin
  - TWP orientation
  - optional rotation about the plane normal
- ordinary `G0/G1 X/Y/Z` are interpreted in plane-local coordinates
- the controller transforms plane-local motion back into machine motion
- TCPC remains coherent underneath

For the first production slice:

- TWP should use a fixed stored `B/C` orientation
- `B/C` words during active TWP should be rejected unless explicitly designed
  later

## Syntax Policy

### Preferred Operator/Post Semantics

The preferred mental model is Fanuc-like:

- TCPC on
- TWP define
- TWP activate
- normal `G0/G1`
- TWP cancel
- TCPC cancel

### Preferred Code Families

Where practical, favor familiar Fanuc-style intent:

- TCPC:
  - on equivalent to `G43.4`
  - off equivalent to `G49`
- TWP:
  - on/set equivalent to `G68.2`
  - cancel equivalent to `G69`

### Current LinuxCNC Target Syntax

For this controller branch, the machine-facing TCPC syntax target is:

- `G43.4` = TCPC on
- `G49.1` = TCPC off

For this controller branch, the machine-facing TWP syntax target is:

- `G68.2 [B.. C..] [R..]` = define and activate TWP
- `G69` = cancel TWP

Current `G68.2` semantics:

- TCPC must already be active through `G43.4`
- the operator or program reaches the required `B/C` pose before `G68.2`
- `B/C` on the `G68.2` block are assertions of that reached pose, not rotary
  motion commands; both must be present or both omitted
- if `B/C` are omitted, `G68.2` captures the current rotary orientation
- an equivalent wrapped C assertion is accepted, but the exact live continuous
  C branch is latched
- the current world TCP is captured as the frame anchor
- the active G5X XYZ translation becomes the local coordinate at that anchor
- optional `R` defines plane rotation about the plane normal
- entry is a stationary, acknowledged switchkins transaction; it is complete
  only after the new forward transform reports its frame ready
- active TWP switches ordinary `G0/G1 X/Y/Z` into plane-local motion
- the complete commissioned G43.4 geometry and length-aware tool model remain
  underneath the plane transform

Initial active-TWP command envelope:

- supported motion: `G0`, `G1`, non-faulting `G38.3`, `G80`, and `G4` dwell
- fixed `B/C`; `A/B/C/U/V/W` axis words are rejected
- `G38.2`, `G38.4`, `G38.5`, arcs, threading, canned cycles, and G53 are
  rejected
- `G38.3` is reserved for reviewed, supervised probing routines with an
  external fixed-B/C live-state guard; it must retract in the same active frame
  before `G69`
- coordinate-system selection, G52/G92, and coordinate-parameter writes are
  rejected
- cutter compensation must remain off
- tool selection/change and tool-length changes are rejected
- `M2`, `M30`, top-level `M99`, and M70/M73 context restoration are rejected
  until `G69` has completed

Current `G69` semantics:

- preserve the current world tool-tip position
- request world kinematics and wait for its successful forward transform
- preserve the latched frame if the return to world mode cannot be confirmed
- clear the stored TWP definition only after world mode is confirmed
- preserve the active G43.4 TCPC state and tool-length model
- once `G69` completes, normal tool-state operations are allowed again:
  - `M6`
  - `M61`
  - `G43` / `G43.1` / `G43.2`
  - `G49`

Current limit-reject recovery expectation:

- a TWP move that would exceed travel limits must be rejected before motion
- the stored TWP state remains active until the operator or program cancels it
- the validated recovery sequence is:
  - `G69`
  - optional `G49.1`
  - safe world-space reposition
  - `G43.4`
  - `G68.2 ...`

Current abort/reset/home expectation:

- program abort leaves active TWP and TCPC state unchanged until explicit cancel
- loss of the `headheadtwp` userspace process is not recoverable in place; its
  HAL registration may remain stale while switchkins type 1 stays stationary
- after state-component loss, do not continue or attempt `G69`: close LinuxCNC
  completely and start a fresh session
- the validated fresh start restores type 0, a ready one-hot world frame, TCPC
  off/default, and clear TWP frame, origin, coordinate, and transaction state
- estop / machine-off clears TWP and restores the configured default TCPC
  state; the real-machine safe wrapper defaults TCPC off
- re-home / unhome-home events clear TWP and preserve the current TCPC mode
- with TCPC on and TWP off, manual `B/C` motion is allowed
- after `G69`, manual `B/C` motion is allowed again before the next `G68.2`

Current release status:

- the production-equivalent T3/T4 switchkins regression passed 8,323 sampled
  servo cycles across four entry/exit edges with no joint or physical-TCP
  transient beyond its `0.000005 mm/deg` thresholds
- the default real-machine INIs omit `[TWP] ENABLE=1`, so their `G68.2` remains
  fail-closed; one dedicated supervised sphere-validation INI opts in
- restart-only recovery after userspace state-component loss is validated; an
  in-place recovery remains intentionally unsupported

Reason:

- `G43.4` is close to the Fanuc mental model and is available as an unallocated
  remapped G-code in this tree
- plain `G49` is already used by LinuxCNC tool-length cancellation and cannot
  be repurposed cleanly
- `G49.1` keeps the cancel intent recognizable while avoiding the built-in
  `G49` conflict

Temporary sample-data M-code wrappers may still exist for manual testing, but
they are not the intended post target.

### Acceptable Deviation

Exact Fanuc syntax is not required if it makes LinuxCNC integration awkward.

Acceptable fallback:

- keep the same mode behavior
- keep the same operator sequence
- keep the Fusion post logic the same
- use simpler controller-specific wrapper codes if needed

If we deviate from exact Fanuc syntax, we should still preserve:

- explicit mode-on and mode-off commands
- predictable cancel behavior
- ordinary `G0/G1` motion while TWP is active

## Postprocessor Contract

The Fusion post should be able to assume:

- TWP is an explicit controller mode
- TCPC is an explicit controller mode
- no per-block post-side coordinate transformation is required once the mode is
  active
- posted code can use ordinary linear blocks while TWP is active
- cancel sequences are explicit before tool changes, safe retracts, and end of
  program

The post should not depend on:

- ad-hoc `G88.5`-style transformed motion for every line
- operator-side manual plane math
- hidden state changes

## Required Behavioral Rules

These rules are not optional:

- activating TWP must not move the machine unexpectedly
- cancelling TWP must not move the machine unexpectedly
- activating or cancelling TCPC must be explicit
- file execution, MDI, and jog behavior must agree
- work offsets and tool length compensation must remain predictable
- the active frame must always be obvious in the UI

## First Production Scope

The first usable controller release should support:

- TCPC on/off
- define TWP from current tool-tip position and programmed `B/C`
- optional plane-normal rotation
- activate TWP
- cancel TWP
- ordinary `G0/G1` linear motion in the tilted plane
- rejection of `B/C` changes while TWP motion is active

It may defer:

- 3-point plane solve
- arbitrary plane definitions from feature vectors
- arcs in TWP
- canned cycles in TWP
- simultaneous changing `B/C` during active TWP

## Implementation Consequence

Because `G0/G1` cannot be replaced cleanly by the current Python remap path,
the implementation target should be:

- mode/state in HAL plus controller state
- TWP-aware behavior inside `headheadkins` and/or the interpreter path
- remap or M-code wrappers only for mode control commands

Current implementation files:

- [head_head_twp_state.py](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_twp_state.py)
- [headheadkins.c](/home/cnc5/linuxcnc-dev/src/emc/kinematics/headheadkins.c)
- [production remap.py](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/python/remap.py)

The central invariant is:

```text
G68.2 geometry = commissioned G43.4 geometry + tilted coordinate frame
```

The TWP path must never copy, approximate, bypass, or separately tune the
active-tool or length-aware correction model.
- [twp_operator_interface.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/twp_operator_interface.md)

Current prototype path that is not the final operator model:

- [remap.py](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/python/remap.py)
- explicit `G88.5 P/Q/R` motion

Current operator model to target:

- `G43.4`
- manual `B/C` positioning as needed while TWP is off
- `G68.2 [B.. C..] [R..]`
- ordinary `G0/G1`
- `G69`
- optional `G49.1`

## Commissioning Order

1. Prove stationary type-0/type-1 entry and exit at every servo cycle with T3
   and T4 and the commissioned length model.
2. Prove local XYZ direction and reversible linear motion at positive and
   negative B, including a wrapped C assertion.
3. Validate userspace-loss and restart recovery while the real-machine opt-in
   remains absent.
4. Run a supervised, no-tool, no-cut real-machine switch test at safe clearance.
5. Run bounded no-cut paths before any posted cutting program.
6. Freeze the posted-code contract and update the Fusion post.

## Decision

For this project, the target is:

- Fanuc-like workflow
- not strict Fanuc syntax if strict syntax makes the controller worse
- standard-looking posted code
- ordinary `G0/G1` motion in active TWP mode
