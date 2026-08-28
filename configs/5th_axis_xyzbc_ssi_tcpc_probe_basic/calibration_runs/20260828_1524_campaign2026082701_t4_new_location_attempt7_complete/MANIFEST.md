# T4 New-Location Attempt-7 Completion Archive

- sealed at: `2026-08-28T15:35:33+07:00`
- campaign / mode / attempt: `2026082701 / 41 / 7`
- program output completed: `2026-08-28T14:45:24+07:00`
- tool / model: `T4 H4 229.407000 mm / 2026082601 / q=0`
- acquisition status: `PASS - DATA INTEGRITY`
- disposition: `DIAGNOSTIC ONLY - NO TCPC CALIBRATION CHANGE`

## Accepted Ownership

Attempt 4 owns canonical sequences `1..9`, Attempt 6 owns `10..23`, and
Attempt 7 owns `24..101`. The completed composite contains exactly `101`
result/state/model rows, `28` retained closures, and `808/808` contact/gap
transactions. Attempt 7 itself contains `78` rows, `25` closures, and
`624/624` contact/gap transactions.

Every accepted contact has exactly one gated G38 edge. No outside-G38 gated
edge, terminal probe failure, consistency fault, or release fault was accepted.
The composite recorded `97` matched raw/mux extras with the motion gate closed;
Attempt 7 accounts for `53`. Its adaptive quiet handler recorded `22` quiet
episodes, `368.50 s` total quiet time, and `13` timer resets.

The populated-output validator and its `5/5` mutation self-test pass. The
pre-load recovery validator remains a header-only preflight validator and is
not used to validate completed outputs.

## Accuracy And Location Diagnostic

- new-location equal-76 centered RMS / max: `0.146265 / 0.337105 mm`
- reference-location equal-76 centered RMS / max: `0.107589 / 0.241710 mm`
- rigid-shift-removed new-minus-reference RMS / max:
  `0.155952 / 0.491649 mm`
- location-delta axis RMS X/Y/Z:
  `0.069887 / 0.137923 / 0.020344 mm`
- equal-pose sphere displacement new minus reference:
  `+1475.889832 / -147.498845 / -0.042642 mm`

The opposing-contact V-pair supplies the strongest axis-local evidence. At
C90/C270, V lies on machine X; its new-minus-reference diameter mean is
`-0.095543983 mm`. At C0/C180, V lies on machine Y; the corresponding mean is
only `+0.009148627 mm`. The X-minus-Y change is `-0.104692610 mm` and retains
the same sign in every signed-B band.

This is consistent with a location-dependent linear-axis or machine-volume
term. It directly identifies an X-oriented indicated-span change and makes
X-axis-local metrology or X-associated cross-axis geometry a leading
hypothesis, but it does not establish a rail cause or show which X region is
wrong. The reference X span was high, the new-location X/Y spans are nearly
isotropic, the sphere move also changed Y, and T4 was removed/reseated between
campaigns. A same-seating X-only and Y-only location series with paired
B0/B+45/B-45/B+90/B-90 poses is required before an axis correction table is
fitted.

This dataset must not be used to edit the TCPC model, empirical coefficient
surface, kinematics, HAL pins, tool table, or probe calibration. A global B/C
TCPC retune would absorb a location term and over-correct the reference
location.

## Controller Boundary

Immediately after the operator reported completion, read-only inspection found
the loaded Attempt-7 runner at `M2`, interpreter idle, queue zero, unpaused,
in-position, enabled, and velocity zero. T4/H4, G43.4, TLO `229.407000 mm`,
and length model `2026082601 q=0` remained active. Raw/mux/gated counters were
`2307/2307/1242`; raw, mux, gated, abnormal, fault, and ignore levels were
clear.

No LinuxCNC control, program load, Cycle Start, Resume, MDI, homing, tool
change, motion, HAL write, or standalone `rs274` command was issued during
completion validation, spatial analysis, or archive construction. LinuxCNC
was left running in its completed idle state.

## Contents

`workspace/` preserves repository-relative paths. It contains the exact
Attempt-7 runner and all six completed outputs, A4/A6 composite sources,
completion and preflight validators, reachability inputs, configuration/model
dependencies, completion report, spatial analyzer/report, and the sealed
reference-location and baseline archives needed by the comparison analyzer.

`evidence/` records the exact offline validation outputs and completion file
boundary. `prerequisite_roots/` binds the Attempt-7 pre-load and accepted
reference-location inventories.

All archive entries are regular files or directories; there are no symlinks.
`SHA256SUMS` authenticates every archived regular file except itself. After
checksum verification, write permission is removed from every archive member
and directory while executable bits are preserved.
