# TWP Sphere Full Cycle B-5 - T4 Physical Closeout

Date: 2026-09-01
Campaign: `2026090102`
Calibration revision: `2026082601` unchanged

## Result

The accepted physical CAM-style B0/B-5/B0 TWP cycle passed. T4/H4 was active
at `229.407 mm`; public `G43.4` TCPC remained off. The program established the
opening B0 WORLD reference, positioned and indexed to B-5 in world mode,
executed the exact Fusion/Fanuc rotating-ZXZ branch
`G68.2 X0 Y0 Z0 I-90 J5 K90` followed by `G53.1`, completed local TWP
probing, cancelled with `G69`, returned to B0, and passed the closing WORLD
reference.

Accepted result:

- 24/24 motion-gated contacts and six complete pass rows
- reached/return pose `B-5 C0 / B0 C0`
- WORLD opening-to-closing closure `0.008735 mm`
- transformed B-5 TWP center error against the mean WORLD center `0.187620 mm`
- opening WORLD / B-5 TWP / closing WORLD pair deltas
  `0.001675 / 0.004967 / 0.008813 mm`
- corresponding V diameters
  `30.174667 / 30.154666 / 30.171333 mm`
- maximum radial residuals `0.088991 / 0.079189 / 0.087335 mm`

The B-5 transformed-center components relative to the mean opening and closing
WORLD center are:

- X: `+0.187194 mm`
- Y: `-0.012535 mm`
- Z: `-0.001567 mm`

The result passes the program's commissioning limit of `0.250 mm`. It is above
the secondary `0.100 mm` project target, so it is accepted as diagnostic TWP
lifecycle evidence rather than an accuracy release at B-5. No calibration
coefficient, B/C zero, work offset, tool-table entry, probe offset, or
length-model ID was changed.

## Attempt Provenance

The first physical start was externally aborted at approximately `13:12:18
+07` after four valid opening WORLD contacts while the program was in its
post-contact ignore interval. The TWP frame had not been entered and no pass
or accepted-result row was written. LinuxCNC reported an external
`EMC_TASK_ABORT`; the program did not raise an `(abort,...)` error.

Afterward, while the controller was idle, the wireless receiver produced a
raw/mux pulse storm. The motion-gated counter did not advance. The operator
returned the probe to the standard B0/C0 sphere-top start, and an eight-second
read-only qualification observed 396 samples with all probe levels inactive
and no counter change.

The accepted restart then ran continuously from the initial M0 through M2. Its
counter delta was exactly raw/mux/gated `24/24/24`, so every edge in the
accepted acquisition was one motion-gated sphere contact and no extra receiver
pulse occurred during that retry.

## TCPC Comparison

The commissioned T4 TCPC validation file
`tcpc-length-aware-t4-validation-2026082601-attempt2-results.csv` provides an
independent comparison at the same sphere. Using the mean of its B0 sequence
1/9 centers and B-5 C0 sequence 17/23 centers gives:

- TCPC B-5 delta: `(+0.180134, +0.000898, -0.006274) mm`
- TCPC B-5 delta norm: `0.180245 mm`
- TWP B-5 delta: `(+0.187194, -0.012535, -0.001567) mm`
- TWP B-5 delta norm: `0.187620 mm`

Both independent modes show nearly the same magnitude and dominant +X
direction at B-5. This is strong evidence that the B-5 asymmetry belongs to
the shared calibrated rotary model or physical machine geometry, not to the
`G68.2` / `G53.1` transition layer. The TWP test must not be used to retune the
frozen shared calibration.

## Final State

Read-only closeout found:

- interpreter idle, machine in position, and all five joints homed
- commanded B0/C0 in world switchkins type 0
- TWP valid/active/motion/origin/orientation/synchronized state all clear
- public TCPC clear
- T4/H4 `229.407 mm` and length model `2026082601` valid with no model fault
- B/C SSI valid
- raw, mux, gated, abnormal, fault-pause, and motion probe levels all clear
- spindle off and the final programmed 25 mm world-Z safe lift complete

## Disposition

Accept this run as the signed-B counterpart to the B+5 TWP lifecycle test. It
validates program-controlled B-5 positioning, the alternate CAM Euler branch,
local-plane probing, `G69`, and program-controlled return. Retain the result
row in `twp-sphere-full-cycle-bminus5-t4-results.csv` and all six diagnostics
in `twp-sphere-full-cycle-bminus5-t4-passes.csv`.

The next staged test is the signed B+5/B-5 pair at C90. Continue to use frozen
calibration revision `2026082601`; do not infer or apply a TWP-specific
calibration from these lifecycle measurements.
