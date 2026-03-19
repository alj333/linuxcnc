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

- TWP origin comes from the current tool-tip position
- `B/C` define the stored tilted-plane orientation when supplied
- if `B/C` are omitted, `G68.2` captures the current rotary orientation
- optional `R` defines plane rotation about the plane normal
- active TWP immediately switches ordinary `G0/G1 X/Y/Z` into plane-local motion
- active TWP rejects rotary changes away from the stored `B/C`
- active TWP also rejects:
  - tool length compensation changes (`G43`, `G43.1`, `G43.2`, `G49`)
  - tool changes / current-tool-number changes (`M6`, `M61`)

Current `G69` semantics:

- preserve the current world tool-tip position
- disable TWP motion
- cancel and reset the stored TWP definition
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
- estop / machine-off clears TWP and restores the default TCPC-on state
- re-home / unhome-home events clear TWP and preserve the current TCPC mode
- with TCPC on and TWP off, manual `B/C` motion is allowed
- after `G69`, manual `B/C` motion is allowed again before the next `G68.2`

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

Current prototype files that remain useful:

- [head_head_twp_state.py](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_twp_state.py)
- [headheadkins.c](/home/cnc5/linuxcnc-dev/src/emc/kinematics/headheadkins.c)
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

## Recommended Build Order

1. Extend `headheadkins` with explicit TCPC/TWP state inputs.
2. Add a sim-only runtime test proving that active TWP changes ordinary
   `G0/G1` interpretation.
3. Add operator-facing on/off wrappers for TCPC and TWP.
4. Freeze the posted-code contract.
5. Build the Fusion post around that contract.

## Decision

For this project, the target is:

- Fanuc-like workflow
- not strict Fanuc syntax if strict syntax makes the controller worse
- standard-looking posted code
- ordinary `G0/G1` motion in active TWP mode
