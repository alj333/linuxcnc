# Head-head TWP low-angle sphere-grid runtime

This fixture runs the actual
`nc_files/calibration/twp_sphere_grid_low_angle_t4.ngc` in AUTO with the
commissioned 2026082601 length-aware overlay, T4/H4, public TCPC off, and a
nonzero G54 XYZ offset. It starts at the standard sphere-top B0/C0 point,
measures a paired opening WORLD reference, and runs the 24-pose matrix
`B +/-5, +/-15, +/-30` at `C 0, 90, 180, 270`. Every positive B pose is
immediately followed by its negative counterpart.

Each pose begins at the common 80 mm physical-probe clearance point. The
actual production program indexes B/C with TWP clear, approaches along the
reached tool axis, executes its rotating-ZXZ `G68.2` / `G53.1` transition,
performs a reversible local-Z preflight and one four-contact sphere pass,
cancels with `G69`, and retracts in world mode. A paired closing WORLD
reference checks full-run drift before the final B0/C0 return and safe lift.

The simulated 30 mm sphere is fixed in world space. During real G38 motion the
UI independently reconstructs the physical probe-ball center from joint
commands and the evaluated kinematics tool vector, then drives the production-
style raw receiver, motion-type-5 gate, ignore window, and sticky counters.
The simulated homing state retains the large physical separation between
machine joint coordinates and `motor-pos-cmd`.

The test checks all 24 poses and Euler identities, 24 TWP entries/exits, 24
local-Z preflights, absence of B/C motion in TWP, at least 50 mm rotary
clearance, all 112 gated contacts, 28 pass rows, 24 pose rows, one complete
summary row, reconstructed physical centers, final `G69`/world state,
T4/model state, and the final safe lift. `test.sh` backs up and byte-verifies
restoration of all three production CSVs on success or failure.

Captured linear states can be replayed with `TWP_SPHERE_TEST_G54` and
`TWP_SPHERE_TEST_START_WORK`; both take three comma-separated values. B0/C0
remains the fixed start and return pose.
