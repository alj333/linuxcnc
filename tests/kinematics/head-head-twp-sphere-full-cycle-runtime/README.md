# Head-head TWP sphere full-cycle runtime

This fixture runs the actual
`nc_files/calibration/twp_sphere_full_cycle_bplus5_t4.ngc` in AUTO with the
commissioned 2026082601 length-aware overlay, T4/H4, public TCPC off, and a
nonzero G54 XYZ offset. It starts at the standard sphere-top B0/C0 point. The
production program measures the opening world reference, moves the physical
probe to a guarded clearance point, indexes B+5/C0, approaches the B+5 start,
executes the CAM-style `G68.2 X0 Y0 Z0 I90 J5 K-90` / `G53.1` transition,
probes in TWP, exits with `G69`, and returns to B0/C0 for closure.

The simulated homing state retains the large XYZ separation between machine
joint coordinates and `motor-pos-cmd` observed on the physical controller.
This prevents motor-layer coordinates from passing as valid TWP frame inputs
merely because a zero-offset simulator made the two layers numerically
identical.

The simulated 30 mm sphere is fixed in world space. During real G38 motion the
UI independently reconstructs the physical probe ball center from joint
commands and the evaluated kinematics tool vector. It drives
the raw receiver input at the program's 17.845258 mm contact envelope. The HAL
then passes that signal through the production-style raw mux, motion-type-5
gate, short test-only falling-edge ignore, and sticky `counter.2` edge count.

The test checks the M0 contract, B0-to-B+5 and B+5-to-B0 clearance, one TWP
entry and exit at B+5, absence of rotary motion while TWP is active, reversible
local-Z preflight, all 24 contacts, six pass rows, one accepted result row,
physical WORLD/TWP/WORLD center closure, final G69/world state, T4/model state,
and final safe lift. Because the production program writes absolute production
CSV paths, `test.sh` backs up both files and restores and compares them in an
EXIT trap on success or failure.

Captured linear states can be replayed with `TWP_SPHERE_TEST_G54` and
`TWP_SPHERE_TEST_START_WORK`; both take three comma-separated values. B0/C0 and
B+5/C0 are deliberately fixed because they are part of the production-cycle
contract. Regardless of linear overrides, the fixture asserts that the large
configured homing offsets remain present between `joint.N.pos-cmd` and
`joint.N.motor-pos-cmd` throughout setup.
