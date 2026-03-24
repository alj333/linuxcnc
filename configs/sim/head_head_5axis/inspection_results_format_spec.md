# Head-Head Inspection Results Format Spec

## Purpose

This note defines the first production file format for inspection, surfacing
probe, and mold-alignment result files on the head-head machine.

It is intentionally based on the old Fusion-friendly result log pattern, but it
adds the frame metadata that was missing in the old workflow.

Goals:

- keep file-based Fusion import practical
- keep the format readable by operators
- make the active coordinate frame explicit
- prevent WCS / rotary / TWP ambiguity during alignment correction

## Design Basis

Reuse from the old system:

- `RESULTSFILE`
- `DOCUMENTID`
- `MODELVERSION`
- `TOOLPATHID`
- `TOOLPATH`
- `G331`
- `G330`
- repeated `G800` / `G801`

Add for the new machine:

- active WCS
- active `B`
- active `C`
- TCPC state
- TWP state
- machine/config revision
- result status

## File Naming

Recommended default names:

- `PROBE-RESULTS.log`
- `INSPECTION-RESULTS.log`
- `ALIGNMENT-RESULTS.log`
- `PROBE-AND-ALIGNMENT-RESULTS.log`

Preferred future naming for archived exports:

```text
YYYYMMDD-HHMMSS-<job>-<result-type>.log
```

Example:

```text
20260324-153210-mold12-alignment-results.log
```

## Required Header Fields

The file header must contain, in this order where practical:

1. `START`
2. `RESULTSFILE <name>`
3. `DOCUMENTID <id>`
4. `MODELVERSION <id>`
5. `TOOLPATHID <id>`
6. `TOOLPATH <name>`
7. `MACHINECFG <branch-or-config-id>`
8. `TIMESTAMP <iso8601-or-local-agreed-format>`
9. `ACTIVE_WCS <G54/G55/...>`
10. `ACTIVE_B <deg>`
11. `ACTIVE_C <deg>`
12. `TCPC <ON/OFF>`
13. `TWP <ON/OFF>`
14. `TWP_ROT <deg>` when relevant, else `0`
15. `PROBE_TOOL <tool-id>`
16. `RESULT_STATUS <RAW/REVIEWED/APPLIED>`
17. `ARTIFACT <sphere/ring/surface/feature-name>`
18. `CALIBRATED RADIUS <value>`
19. `ECCENTRICITY X <value>`
20. `ECCENTRICITY Y <value>`

## Required Meaning Of Header Fields

### `ACTIVE_WCS`

Must record the exact work offset active during probing.

Examples:

- `ACTIVE_WCS G54`
- `ACTIVE_WCS G55`

### `ACTIVE_B` / `ACTIVE_C`

Must record the programmed rotary pose used for that measurement set.

Even if the file is nominally “world frame,” the rotary pose must still be
explicit.

### `TCPC`

Allowed values:

- `ON`
- `OFF`

### `TWP`

Allowed values:

- `ON`
- `OFF`

For production mold alignment, this should normally be:

- `TWP OFF`

### `RESULT_STATUS`

Allowed values:

- `RAW`
- `REVIEWED`
- `APPLIED`

Meaning:

- `RAW` = just measured, not yet trusted for correction
- `REVIEWED` = reviewed and accepted for correction planning
- `APPLIED` = correction has already been applied from this data set

This field exists to stop the same result set being applied twice.

## Legacy-Compatible Transform Records

Keep these records because they are already close to what the old Fusion
inspection flow used.

### `G331`

Nominal setup / transform record from the CAM side.

Keep the old shape, but allow the post to extend metadata elsewhere in the
header instead of overloading this line.

### `G330`

Reference identity transform / baseline record.

Keep the old shape for compatibility.

## Point Records

### `G800`

Nominal feature/point record.

Keep the old basic pattern:

```text
G800 N<point> X<nominalX> Y<nominalY> Z<nominalZ> I<i> J<j> K<k> O<offset> U<upperTol> L<lowerTol>
```

Meaning:

- `N` = point number
- `XYZ` = nominal target point in the declared probing frame
- `IJK` = nominal feature normal / direction
- `O` = nominal surface offset or feature offset
- `U/L` = upper and lower tolerance

### `G801`

Measured point record.

Keep the old basic pattern:

```text
G801 N<point> X<measuredX> Y<measuredY> Z<measuredZ> R<probeRadius>
```

Meaning:

- measured point must belong to the same declared frame as the matching `G800`
- it must not be silently transformed into another WCS or TWP frame later

## Optional Additional Records

These are recommended but not mandatory for the first production revision.

### `COMMENT`

Free-form human note.

Example:

```text
COMMENT sphere check after B0/C0 zero reset
```

### `CORRECTION_TARGET`

Explicitly states where correction is intended to be applied.

Allowed values:

- `FUSION_SETUP`
- `LINUXCNC_WCS`
- `REVIEW_ONLY`

Recommended default:

- `CORRECTION_TARGET FUSION_SETUP`

### `FRAME_POLICY`

Example:

```text
FRAME_POLICY G54-G69-NO_TWP
```

Useful for quick review and operator sanity checking.

## Example Header

```text
START
RESULTSFILE ALIGNMENT-RESULTS
DOCUMENTID F7EB2B15-E301-4EB2-9C3A-2D37FE5B68D0
MODELVERSION HEADHEAD-2026-03-24
TOOLPATHID 740.00001
TOOLPATH INSPECT1
MACHINECFG head-head-kinematics-rnd-pushable
TIMESTAMP 2026-03-24T15:32:10+07:00
ACTIVE_WCS G54
ACTIVE_B 0.000
ACTIVE_C 0.000
TCPC ON
TWP OFF
TWP_ROT 0.000
PROBE_TOOL T3
RESULT_STATUS RAW
ARTIFACT mold_surface_a
CORRECTION_TARGET FUSION_SETUP
FRAME_POLICY G54-G69-NO_TWP
CALIBRATED RADIUS 2.999000
ECCENTRICITY X 0.001
ECCENTRICITY Y 0.001
```

## Blocked Behaviors

The result-file writer must not:

- omit `ACTIVE_WCS`
- omit `ACTIVE_B` / `ACTIVE_C`
- write `TWP ON` unless probing in TWP was intentionally validated
- rewrite WCS during the same default alignment workflow without recording it
- output data that was measured in one frame and labeled as another

## Fusion Post Consequence

The new inspection post should:

- preserve the legacy `G331/G330/G800/G801` style
- add the missing frame metadata lines
- default to `RESULT_STATUS RAW`
- default to `CORRECTION_TARGET FUSION_SETUP` for mold alignment

## LinuxCNC Consequence

The LinuxCNC-side probing workflow should:

- know the active WCS when writing the file
- know the active `B/C`
- know whether `G43.4` is active
- know whether `G68.2` is active
- emit those values into the file header before the first `G800`
