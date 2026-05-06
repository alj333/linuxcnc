# TCPC Corrected B90 Offline Investigation

Date: 2026-05-04

This note analyzes the B90 C-quadrant rerun taken after the validated C-center
correction was active.

## Data Boundaries

- Pre-correction B90 C-quadrant data:
  `tcpc-b90-c-quadrant-diagnostic-2pass-results.csv` lines `2-43`,
  excluding the bad false-top line `13`.
- C-center validation data:
  same CSV lines `44-53`.
- Corrected B90 C-quadrant data:
  same CSV lines `54-93`.
- Clean B90 C0/C180 holdout:
  `tcpc-b90-b-axis-diagnostic-2pass-results.csv` lines `18-37`.

The corrected B90 run has a wireless-probe quality caveat. The operator reset
the probe during transit paths, not during accepted probe moves, so the accepted
rows remain usable but should not be treated as final metrology quality.

## Corrected High-B Pattern

High-B deltas versus adjacent B0 closures after C-center correction:

| Pose | dX | dY | dZ | 3D drift |
| --- | ---: | ---: | ---: | ---: |
| `B+90 C0` | `-0.052875` | `-0.198228` | `+0.069230` | `0.216525` |
| `B-90 C0` | `-0.203375` | `-0.137813` | `+0.659229` | `0.703517` |
| `B+90 C90` | `-0.094271` | `-0.242146` | `-0.084833` | `0.273347` |
| `B-90 C90` | `-0.012100` | `+0.421370` | `+0.886208` | `0.981358` |
| `B+90 C180` | `-0.112354` | `-0.220592` | `-0.012021` | `0.247848` |
| `B-90 C180` | `+0.022229` | `+0.169999` | `+0.712771` | `0.733100` |
| `B+90 C270` | `-0.223969` | `+0.539925` | `+0.170062` | `0.608771` |
| `B-90 C270` | `-0.149642` | `-0.115378` | `+0.633603` | `0.661179` |

High-B delta RMS/max: `0.610965 / 0.981358 mm`.

Compared with the pre-correction B90 C-quadrant run, the high-B residual pattern
barely changed. That confirms the C-center correction was correctly isolated:
it fixed the B0 C orbit, but the high-B problem is a separate error family.

## Fit Findings

The offline fitter must treat each run with its own active kinematics. Lines
`54-93` were measured with the C-center correction already active, while older
rows were measured with the previous C-center values.

Using the corrected B90 run with the C-center held fixed:

| Model | Corrected-run RMS | Corrected-run max | Notes |
| --- | ---: | ---: | --- |
| C-center fixed only | `0.3562` | `0.8735` | Baseline after B0 C correction |
| B-zero only | `0.3110` | `0.7336` | Helps, but cannot explain pattern |
| B-zero plus B-to-tool Z | `0.2526` | `0.4930` | Better, still incomplete |
| current exposed pins, C fixed | `0.2440` | `0.4898` | Not enough |
| axis-vector terms, C fixed | `0.2384` | `0.4667` | Hits bounds; reject live use |
| axis-vector plus linear diagonal, C fixed | `0.1825` | `0.3374` | Diagnostic only; hits bounds |

When training on corrected B90 plus the clean B90 C0/C180 holdout, the
axis-vector plus linear-diagonal model gives similar behavior:

- corrected B90 RMS/max: `0.1845 / 0.3523 mm`
- clean B90 holdout RMS/max: `0.1703 / 0.2583 mm`
- `b_axis_x` hits the `-0.5 deg` bound
- `c_zero` trends near the `-0.49 deg` bound
- `lin_xx` hits the `-0.002` bound

Those bound hits mean this is not a live correction candidate. It is evidence
that the current model is missing a machine-fixed or load/flex term.

Allowing the fit to move C-center again improves some high-B residuals, but it
degrades the already validated B0 C-center result. Do not change the C-center
from:

- `headheadkins.cal-c-to-b.x = +0.035886006`
- `headheadkins.cal-c-to-b.y = +0.009526306`

## Residual Structure

Post-correction high-B averages:

- B+90 Z residual mean: `+0.035609 mm`
- B-90 Z residual mean: `+0.722953 mm`
- B-90 Z residual range: `+0.633603..+0.886208 mm`

Simple diagnostic correlations against high-B motor positions:

- dY vs Y motor: `-0.821`
- dZ vs Z motor: `+0.984`

The dZ/Z-motor correlation is strongly confounded with B sign because the
high-B TCPC moves place Z motor position about 2 mm apart between B+90 and
B-90. Treat it as evidence that the remaining error is not pure C-center, not
as proof of Z scale.

The logged X/Y/Z following errors at accepted high-B rows were effectively
zero, so servo following error is not the explanation.

## TCPC Math Plan

Do not load the high-B fit parameters live.

The offline fitter has now been updated to implement the run-state-aware
normalization described below. Remaining code/math work should stay
simulation-only until a bounded correction survives held-out data.

1. Keep the offline fitter run-state-aware so each observation subtracts the
   kinematic offset that was active during that run, then applies the candidate
   model. This avoids mixing pre- and post-C-center data incorrectly.
2. Keep the C-center correction fixed while fitting high-B data.
3. Add tool-frame debug output pins to `headheadkins` for the current expanded
   U/V/W frame, not only the tool vector and B/C axis vectors. Future diagnostic
   probing should use the same frame that TCPC uses; otherwise nonzero axis
   tilt tests will be measured with the old ideal probe vectors.
4. Add a simulation-only machine-linear affine correction family with identity
   defaults:
   - forward: reported TCP uses `A * joint_xyz + rotary_offset`
   - inverse: commanded joints use `A^-1 * (requested_tcp - rotary_offset)`
   - expose bounded HAL pins for the small off-diagonal/scale terms
5. Refit with these families against pre-correction B90, corrected B90, clean
   B90 C0/C180, and the B10/B30/B50 angle-scaling data.

## Next Live Data

Do not run another long B90 C-quadrant diagnostic until the wireless probe is
stable.

After the probe is stable, the next useful live run should be shorter and aimed
at B-angle scaling, not C-center:

- C0 only first: `B0, B+30, B0, B-30, B0, B+60, B0, B-60, B0, B+90, B0, B-90, B0`
- repeat the same at C180 if C0 is clean
- keep the current C-center correction active

The purpose is to separate terms that scale with `sin(B)`, `1-cos(B)`, and
machine-position effects before applying any new TCPC correction.
