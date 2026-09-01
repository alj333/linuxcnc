# TWP Sphere Low-Angle Grid - T4 Operator Plan

Date: 2026-09-01
Campaign: `2026090103`
Calibration revision: `2026082601` frozen
Program: `nc_files/calibration/twp_sphere_grid_low_angle_t4.ngc`

## Purpose

This is a TWP commissioning screen, not a calibration fit. It expands the
accepted B+5/B-5 C0 lifecycle tests to a symmetric low-angle matrix:

- B: `+5, -5, +15, -15, +30, -30 degrees`
- C: `0, 90, 180, 270 degrees`
- 24 target poses, with every positive B pose immediately followed by its
  negative counterpart

Every target performs a complete CAM-style transaction: world-mode indexing,
literal rotating-ZXZ `G68.2`, `G53.1`, reversible local-Z preflight, one
four-contact sphere measurement, `G69`, and world-mode retraction. Public
`G43.4` remains off. No coefficient, B/C zero, WCS, tool-table value, probe
offset, or model ID is changed.

## Pose Identity

| Seq | B | C | I | J | K |
|---:|---:|---:|---:|---:|---:|
| 1 | +5 | 0 | 90 | 5 | -90 |
| 2 | -5 | 0 | -90 | 5 | 90 |
| 3 | +15 | 0 | 90 | 15 | -90 |
| 4 | -15 | 0 | -90 | 15 | 90 |
| 5 | +30 | 0 | 90 | 30 | -90 |
| 6 | -30 | 0 | -90 | 30 | 90 |
| 7 | +5 | 90 | 180 | 5 | -90 |
| 8 | -5 | 90 | 0 | 5 | 90 |
| 9 | +15 | 90 | 180 | 15 | -90 |
| 10 | -15 | 90 | 0 | 15 | 90 |
| 11 | +30 | 90 | 180 | 30 | -90 |
| 12 | -30 | 90 | 0 | 30 | 90 |
| 13 | +5 | 180 | -90 | 5 | -90 |
| 14 | -5 | 180 | 90 | 5 | 90 |
| 15 | +15 | 180 | -90 | 15 | -90 |
| 16 | -15 | 180 | 90 | 15 | 90 |
| 17 | +30 | 180 | -90 | 30 | -90 |
| 18 | -30 | 180 | 90 | 30 | 90 |
| 19 | +5 | 270 | 0 | 5 | -90 |
| 20 | -5 | 270 | 180 | 5 | 90 |
| 21 | +15 | 270 | 0 | 15 | -90 |
| 22 | -15 | 270 | 180 | 15 | 90 |
| 23 | +30 | 270 | 0 | 30 | -90 |
| 24 | -30 | 270 | 180 | 30 | 90 |

## Transition Workpath

The direct B-5-to-B+15 simulator transition correctly tripped the existing
160 mm physical-tool positioning bound. The program does not weaken that
guard. It now changes B first and C second in at most 10-degree world-mode
increments, re-centering the physical probe at the common 80 mm sphere-clear
point after every increment. TWP is clear during every B/C move.

The complete actual-program simulator passed:

- 24/24 target poses and 24/24 TWP entries/exits
- 24/24 reversible local-Z preflights
- 112/112 raw, mux, and motion-gated contacts
- no rotary motion while TWP was active
- minimum fixed-sphere rotary-transition clearance `70.824641 mm`
- WORLD opening-to-closing closure `0.001195 mm`
- final commanded B0/C0 in world type 0 with TWP/TCPC clear
- byte-identical restoration of all three production evidence files

## Operator Start

1. Use only the dedicated TWP validation INI.
2. Home all five joints.
3. Install T4 and set `M61 Q4`, then ordinary `G43 H4`. Do not use `G43.4`.
4. Return to commanded B0/C0 and the standard sphere-top point, with the probe
   3-5 mm above the accessible sphere surface on the probe axis.
5. Confirm the unchanged sphere/post fixture is secure and all previously
   cleared probe positions remain unobstructed. The sphere-to-post direction
   is X-, Y+, Z-.
6. Confirm spindle and laser off and the wireless-probe inputs quiet.
7. Start the program and inspect the initial M0 text. There are no later
   planned holds.
8. Keep the run supervised. The 112 contacts and stepped indexing make this
   materially longer than the single-pose cycles.

The program finishes in world mode at commanded B0/C0 with a 25 mm world-Z
safe lift.

## Recovery

Do not restart from line. After Stop or Abort while TWP may be active, remain
stationary, issue `G69`, and verify world type 0 and all TWP state clear. If
that state cannot be established, close LinuxCNC, restart cleanly, home, and
re-establish T4/H4 and the standard B0/C0 sphere-top start.

Completed target rows are appended immediately to
`twp-sphere-grid-low-angle-t4-poses.csv`. A recovery copy is made by increasing
`#<_twp_grid_attempt>` and setting `#<_twp_grid_start_pose>` to the first
uncompleted pose. Opening and closing WORLD pairs are reacquired on every
attempt, and the gated-contact total adjusts to the remaining pose count. The
operator should report the stop before a recovery file is prepared.

The `2.000 mm` target-center gate is diagnostic and intentionally tolerant of
the known machine geometry. It is not an acceptance target and must not be
used to retune the shared calibration during this TWP commissioning run.
