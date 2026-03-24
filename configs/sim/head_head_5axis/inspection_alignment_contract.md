# Head-Head Inspection Alignment Contract

## Purpose

This note defines the allowed coordinate-system workflow for inspection,
surface probing, and mold alignment on the head-head machine.

The goal is to prevent a repeat of the earlier WCS/alignment failures where
valid probe data was applied in the wrong frame and produced bad corrections.

This is a machine/process contract first. The Fusion inspection post and the
LinuxCNC probing workflow must both follow it.

## Legacy Finding That Drove This Contract

The old system already showed the main failure mode this document is trying to
prevent.

Observed in the legacy files:

- old inspection programs existed in more than one WCS form:
  - `Probe101.ngc` used `G54`
  - `Probe#1 Alt WCS.ngc` used `G55`
- the old config also carried a dynamic work-offset remap:
  - `dynamic-work-offsets-v2.ngc`
- that remap read the currently active WCS and rotary state, then rewrote a
  target offset with `G10 L2`

That combination made it too easy to:

- measure in one frame
- rotate or change WCS
- then apply the correction in another frame without realizing it

So the current rule is deliberate:

- one declared probing frame
- one declared correction target
- no hidden dynamic offset remap in the default mold-alignment workflow

Companion review:

- [legacy_probe_workflow_review.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/legacy_probe_workflow_review.md)

## Core Rule

Alignment data must be measured in one explicit frame and applied in one
explicit frame.

Do not mix:

- machine coordinates
- work offsets
- manual rotary orientation state
- active tilted workplane state
- already-corrected CAM setups

If any of those are mixed, the correction cannot be trusted.

## Approved Alignment Frames

### 1. Baseline Alignment Frame

This is the default and preferred frame for alignment probing.

Use:

- `G54`
- `G69` active before probing
- no active TWP
- `B/C` at the programmed/indexed orientation for the inspection operation

Interpretation:

- reported measured points are treated as belonging to the active work offset
- the probing result is compared to the nominal Fusion setup in that same frame

### 2. Indexed Rotary Alignment Frame

This is allowed when the inspection requires the part to be viewed at a known
rotary pose.

Use:

- `G54` unless a documented alternate WCS is required
- `G69` active before probing
- no active TWP
- `B/C` explicitly commanded to the inspection pose before the probing cycle

Interpretation:

- the measurement belongs to the indexed machine pose
- the result must record the exact `B/C` used during the probe cycle

### 3. TWP Alignment Frame

Not approved for production alignment yet.

Rule:

- do not use active `G68.2` probing for mold-alignment correction until it is
  validated deliberately on the real machine

Reason:

- this adds another transform layer and makes it too easy to apply corrections
  in the wrong frame

## TCPC Rule During Alignment

TCPC may be on if needed for safe head-head behavior, but it must not change
the interpretation of the inspection result.

Approved default:

- `G43.4` allowed
- `G69` required
- active `B/C` must still be recorded with the measurement

Reason:

- on this machine, TCPC-on may be the safer operating state for long tools and
  head motion
- but the correction still belongs to the declared work frame, not to an
  implied transformed frame

## WCS Rule

The first production alignment workflow should use one primary work offset for
inspection and correction:

- `G54`

Use other WCS values only when there is a documented reason.

If another WCS is used, the inspection result must explicitly record:

- active WCS number
- whether that WCS was nominal, temporary, or already corrected

Do not import measured alignment data from one WCS and apply it to a different
WCS without an explicit conversion step.

## One-Correction Rule

For each alignment cycle, apply the correction in one place only.

Approved targets:

1. adjust the Fusion setup / work coordinate alignment in CAM
2. adjust the machine work offset in LinuxCNC

Do not do both for the same correction set.

Default preference:

- for mold/program alignment, prefer updating the Fusion setup from the
  inspection result
- keep the machine work offset simple and predictable unless there is a clear
  shop reason not to

## Required Metadata For Every Alignment Result

Every saved result set must include:

- machine config or branch identifier
- date/time
- active WCS
- active `B`
- active `C`
- TCPC state
- TWP state
- probe/tool identifier
- nominal artifact or feature reference
- whether the result is raw, reviewed, or already applied

If these fields are missing, the alignment result should not be trusted for
correction import.

## Recommended Alignment Workflow

### Phase 1: Preparation

1. qualify the probe
2. verify the probe in the ring
3. verify `B0` and `C0`
4. confirm no active TWP:
   - `G69`
5. move to the intended inspection `B/C` pose
6. confirm the intended WCS, normally `G54`

### Phase 2: Measurement

1. run the inspection or surfacing probe routine
2. capture results in the declared frame
3. save the result with WCS / `B/C` / mode metadata

### Phase 3: Correction

1. review the result in Fusion or the agreed review tool
2. apply the correction in one place only
3. mark that result set as applied

### Phase 4: Verification

1. rerun a short confirmation probe in the same frame
2. confirm the residual error improved
3. only then release the corrected setup for machining

## Explicitly Blocked Workflow

Do not do this:

1. probe with one WCS
2. change `B/C`, TWP, or WCS
3. import the old result as if it belonged to the new state

Do not do this:

1. probe in active TWP
2. export/import the result as if it were plain world/WCS data

Do not do this:

1. correct Fusion setup
2. also shift LinuxCNC work offset for the same measurement
3. then wonder why the part doubled the correction

## Fusion Post Consequence

The inspection post should default to:

- world or indexed probing
- explicit `B/C` orientation before the probing section
- no `G68.2` around normal alignment probing
- results written with enough metadata to recover the intended frame

The post should not assume that live connection is available.

File-based inspection import remains the first production path.

## LinuxCNC Consequence

The LinuxCNC side should make the active frame obvious to the operator.

Operator-facing checks should show:

- active WCS
- active `B/C`
- TCPC on/off
- TWP active/inactive

The operator should be able to reject or stop an alignment run if any of those
do not match the expected setup.

## First Production Decision

Until real-machine validation proves otherwise, the approved mold-alignment
workflow is:

- probe in `G54`
- `G69` active
- indexed `B/C` allowed
- TCPC allowed if needed for safe motion
- apply correction once, preferably in the Fusion setup
- verify in the same frame used for measurement
