# TWP Sphere Full Cycle B+5 - T4 Physical Closeout

Date: 2026-09-01
Campaign: `2026090101`
Calibration revision: `2026082601` unchanged

## Result

The first physical CAM-style B0/B+5/B0 TWP cycle passed. T4/H4 was active at
`229.407 mm`; public `G43.4` TCPC remained off. The program established the
opening B0 WORLD reference, positioned and indexed to B+5 in world mode,
executed `G68.2 X0 Y0 Z0 I90 J5 K-90` followed by `G53.1`, completed local TWP
probing, cancelled with `G69`, returned to B0, and passed the closing WORLD
reference.

Accepted result:

- 24/24 motion-gated contacts and six complete pass rows
- reached/return pose `B5 C0 / B0 C0`
- WORLD opening-to-closing closure `0.006120 mm`
- transformed B+5 TWP center error against the mean WORLD center `0.039035 mm`
- opening WORLD / B+5 TWP / closing WORLD pair deltas
  `0.006026 / 0.007905 / 0.009274 mm`
- corresponding V diameters
  `30.174250 / 30.181332 / 30.186333 mm`
- maximum radial residuals `0.088598 / 0.091539 / 0.095250 mm`

The B+5 transformed-center error components relative to the mean opening and
closing WORLD center are approximately:

- X: `-0.031966 mm`
- Y: `-0.002259 mm`
- Z: `+0.022289 mm`

This is a coherent nonzero-angle result below the project's secondary
`0.100 mm` target. It is larger than the accepted neutral B0 TWP error
`0.001965 mm`, as expected when the physical rotary geometry is exercised.
No calibration coefficient, B/C zero, work offset, tool-table entry, probe
offset, or length-model ID was changed.

## Operator Intervention

Rapid override was initially 0%. After the opening eight contacts and the
guarded lift to the common world-clearance point, the program waited on its
`G0 B5 C0` block. B had advanced only about `0.000012 degrees`; TWP was clear
and the probe remained at the safe transition point. The operator raised rapid
override to 10%, after which the queued B move and program continued normally.
There was no Stop, Abort, restart-from-line, offset change, jog, or MDI command
during the program.

## Probe Edge Provenance

The final counters were raw/mux/gated `31/31/24`. The timestamped edge monitor
accounts for the seven non-motion pulses:

- six delayed post-contact pulses occurred during motion type 2 retracts with
  `ignore_active=1`; none reached the gated probe input
- one pulse occurred at `11:08:53.654 +07` during the safe world-mode B index,
  at approximately `B4.695390 C-0.000022`
- the B-index pulse briefly asserted the abnormal/fault event, remained absent
  from `motion.probe-input`, and cleared in about half a second
- the program then reached B5, passed its probe-quiet and live-state guards,
  and entered TWP normally

The one out-of-motion pulse is documented probe-system behavior, not a sphere
contact. It does not invalidate the 24 independently motion-gated contacts or
the accepted geometric result.

## Final State

Read-only closeout found:

- interpreter idle, machine in position, and all five joints still homed
- commanded B0/C0; feedback approximately B `-0.000010 degrees`,
  C `+0.000320 degrees`
- world switchkins type 0 active
- TWP valid/active/motion/origin/orientation/synchronized state all clear
- public TCPC clear
- T4/H4 `229.407 mm` and length model `2026082601` valid with no model fault
- B/C SSI valid
- raw, mux, gated, abnormal, fault-pause, and motion probe levels all clear
- final programmed 25 mm world-Z safe lift complete

## Disposition

Accept this as the first supervised physical nonzero-angle TWP lifecycle test.
It validates program-controlled positioning, literal CAM-form TWP entry,
local-plane probing, `G69`, and program-controlled return. Retain the result
row in `twp-sphere-full-cycle-bplus5-t4-results.csv` and all six diagnostics in
`twp-sphere-full-cycle-bplus5-t4-passes.csv`.

Before any wider-angle or cutting test, review whether the next evidence should
be the corresponding B-5 symmetry cycle or a low-clearance-free CAM motion
cycle. Do not adjust the shared TCPC/TWP calibration from this single B+5 TWP
result.
