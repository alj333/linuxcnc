# TWP Sphere Low-Angle Grid - T4 Physical Closeout

Date: 2026-09-01

Campaign: `2026090103`

Attempt: `1`

Calibration revision: `2026082601` unchanged

## Result

The supervised physical TWP grid completed without a recovery segment. T4/H4
was active at `229.407 mm`; public `G43.4` TCPC remained off. The program ran
the complete CAM-style lifecycle at all 24 requested orientations:

- B `+5, -5, +15, -15, +30, -30 deg`
- C `0, 90, 180, 270 deg`
- every positive B pose immediately followed by its negative counterpart

Each pose performed world-mode indexing, rotating-`ZXZ` `G68.2`, stationary
`G53.1` activation, a reversible local-Z preflight, one four-contact sphere
measurement, `G69`, and world-mode retraction.

Accepted acquisition:

- 24/24 pose rows
- 24/24 TWP entries and exits
- 24/24 local-Z preflights
- 112/112 motion-gated contacts
- 28 complete pass rows
- one complete summary row
- no rotary motion while TWP was active
- no Stop, Abort, restart, recovery attempt, or offset change

## Geometric Summary

WORLD opening-to-closing closure was `0.052759 mm`. Opening and closing
two-pass repeatability was `0.006406 mm` and `0.010418 mm` respectively.

Across the 24 transformed TWP centers:

- mean center-error norm: `0.141458 mm`
- RMS center-error norm: `0.150468 mm`
- minimum center error: `0.031116 mm`
- maximum center error: `0.205463 mm`
- worst center pose: B-30/C180
- worst center components: `(+0.196652, -0.026251, +0.053421) mm`
- maximum four-contact radial residual: `0.141089 mm`
- worst residual pose: B+30/C270

All program gates passed:

- WORLD closure limit `0.100 mm`
- same-pair repeatability limit `0.100 mm`
- per-pass radial-residual limit `0.250 mm`
- diagnostic target-center stop limit `2.000 mm`

The `2.000 mm` target-center limit was intentionally not an accuracy
acceptance threshold. The physical result is a lifecycle/coordinate-frame
commissioning pass. Several poses remain above the project's secondary
`0.100 mm` accuracy target and continue to represent the known shared rotary
geometry, rail alignment, spindle seating, and probe measurement limits.

## Implementation Disposition

This acquisition validates the commissioned implementation within the tested
envelope:

- Fusion/Fanuc rotating-`ZXZ` I/J/K interpretation at all four C quadrants
- positive and negative B Euler branches
- separate public TCPC and TWP modes
- ordinary `G43 H4` retained while public `G43.4` stays off
- program-controlled B/C indexing before `G68.2`
- stationary `G68.2` definition and `G53.1` activation
- fixed-B/C local XYZ motion
- stationary `G69` return to world mode
- repeated transitions between different signed B and C orientations

Earlier B+5 and B-5 physical comparisons already showed that the dominant
signed-B TWP error agrees with independent TCPC evidence. This grid does not
justify a TWP-specific trim and changes no shared calibration value.

Disposition: accept synchronized TWP for supervised CAM cut testing inside
`|B| <= 30 deg`. Do not treat this as an unattended production release or as
physical validation of the remaining B/C travel.

## Final Controller State

The completed program returned to:

- interpreter idle and machine in position
- all five joints homed
- commanded B0/C0
- world switchkins type 0 ready
- TWP valid/active/motion/synchronized state clear
- public TCPC clear
- T4/H4 retained at `229.407 mm`
- length model valid, ID `2026082601`, fault code 0
- spindle off
- motion probe input clear
- final programmed 25 mm world-Z safe lift complete

## Evidence

- program: [twp_sphere_grid_low_angle_t4.ngc](/home/cnc5/linuxcnc-dev/nc_files/calibration/twp_sphere_grid_low_angle_t4.ngc)
- operator plan: `TWP_SPHERE_GRID_LOW_ANGLE_T4_PLAN_2026090103.md`
- pass rows: `twp-sphere-grid-low-angle-t4-passes.csv`
- pose rows: `twp-sphere-grid-low-angle-t4-poses.csv`
- summary: `twp-sphere-grid-low-angle-t4-summary.csv`

Evidence SHA-256:

```text
955862dd553f49ec89cdf0d8bc766a5919f6870dd71322cc6ee7a6d5b6be137a  twp_sphere_grid_low_angle_t4.ngc
7c36aa000bace84364bf35b61bd2ef1fe9b16d622ed8b654a8f78f38042f3c5a  twp-sphere-grid-low-angle-t4-passes.csv
2e4fbccf556050033ac4698db9a1c2d734ba6b739bb1d595e85234bd4ce5351b  twp-sphere-grid-low-angle-t4-poses.csv
e80e29b80e85a3102677b699c5436a693eda7e4968ed80aa25696498a0688b8c  twp-sphere-grid-low-angle-t4-summary.csv
```
