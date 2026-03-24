# Legacy Probe Workflow Review

## Purpose

This note captures what is useful from the old machine probing workflow and
what should not be carried forward into the head-head machine unchanged.

Source material reviewed:

- `/home/cnc5/Old System/probing`
- `/home/cnc5/Old System/Backup Feb 2026/linuxcnc/configs/5th_axis`

## Useful Legacy Pattern

The old system already produced Fusion-friendly probe and inspection result
logs in a consistent text format.

Observed result files:

- `/home/cnc5/Old System/probing/PROBE-RESULTS.log`
- `/home/cnc5/Old System/probing/INSPECTION-RESULTS.log`
- `/home/cnc5/Old System/probing/ALIGNMENT-RESULTS.log`
- `/home/cnc5/Old System/probing/PROBE-AND-ALIGNMENT-RESULTS.log`

Observed structure:

- `RESULTSFILE ...`
- `DOCUMENTID ...`
- `MODELVERSION ...`
- `TOOLPATHID ...`
- `TOOLPATH ...`
- `G331 ...`
- `G330 ...`
- repeated:
  - `G800 ...` nominal target / normal vector / tolerance
  - `G801 ...` measured point and probe radius

This is worth keeping.

Reason:

- it is already close to the style Fusion inspection expects
- it supports file-based import, which is still the preferred first production
  path for LinuxCNC
- it avoids making live connection a dependency for the first machine rollout

## Legacy Risk Pattern

The old system also mixed probing with direct work-offset rewriting.

Observed in the old config:

- many probing subroutines wrote directly to the active WCS with:
  - `G10 L2 P#5220 ...`
- examples:
  - `probe_x_plus_wco.ngc`
  - `probe_y_plus_wco.ngc`
  - `probe_z_minus_wco.ngc`
  - many corner / boss / pocket routines
- the old config also carried:
  - `dynamic-work-offsets-v2.ngc`
  - remapped as `M254`

What that remap did:

- read the current active work offset
- read live rotary state
- transform values
- write a new work offset with `G10 L2`

This is the main legacy risk.

Reason:

- valid probe data can become an invalid correction if the active WCS or rotary
  pose changed between measurement and offset application
- it hides the exact frame where the correction was really applied
- it makes it easy to double-apply an alignment:
  - once in the machine offset
  - again in Fusion/CAM

## Legacy Evidence Of Mixed Frames

The old probing programs were not all anchored to one WCS.

Examples:

- `/home/cnc5/Old System/probing/Probe101.ngc`
  - uses `G54`
- `/home/cnc5/Old System/probing/Probe Testing/Probe#1 Alt WCS.ngc`
  - uses `G55`

That is not automatically wrong, but it becomes risky when combined with:

- direct WCS rewriting macros
- dynamic rotary-aware offset remaps
- alignment import back into CAM

## Recommended Carry-Forward

Keep:

- the legacy file-based result format pattern
- explicit per-point nominal/measured logging
- result file names that clearly separate:
  - inspection
  - alignment
  - combined probe/alignment runs

Adapt:

- add explicit metadata to every result file for:
  - active WCS
  - active `B`
  - active `C`
  - TCPC state
  - TWP state
  - machine/config revision

Drop from the default workflow:

- probing routines that immediately rewrite the active work offset
- dynamic WCS remaps in the main mold-alignment path
- any default workflow that depends on the currently active WCS without logging
  it

## Current Replacement Rule

The replacement rule for the head-head machine is defined in:

- [inspection_alignment_contract.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/inspection_alignment_contract.md)

Short version:

- probe in one declared frame
- save results with explicit metadata
- apply the correction once, in one declared place
- verify in the same frame used for measurement

## Practical Consequence For Fusion Work

When building the new Fusion inspection post:

- reuse the legacy result-file style as the first target
- do not reproduce the old dynamic-WCS correction behavior
- treat machine-side offset rewriting as a separate explicit workflow, not the
  default alignment import path
