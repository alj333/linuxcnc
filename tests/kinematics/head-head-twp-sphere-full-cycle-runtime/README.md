# Head-head TWP sphere full-cycle runtime

This fixture runs an actual TWP sphere full-cycle program in AUTO with the
commissioned 2026082601 length-aware overlay, T4/H4, public TCPC off, and a
nonzero G54 XYZ offset. The default is
`nc_files/calibration/twp_sphere_full_cycle_bplus5_t4.ngc`; the
`test-bminus5.sh` wrapper selects the corresponding B-5 production program.
Both start at the standard sphere-top B0/C0 point, measure the opening WORLD
reference, move through guarded clearance, index with TWP clear, execute the
literal CAM-style `G68.2` / `G53.1` transition, probe in TWP, exit with `G69`,
and return to B0/C0 for closure.

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

The test checks the M0 contract, start-to-target and target-to-start rotary
clearance, one TWP entry and exit at the requested pose, absence of rotary
motion while TWP is active, reversible local-Z preflight, all 24 contacts, six
pass rows, one accepted result row, physical WORLD/TWP/WORLD center closure,
final G69/world state, T4/model state, and final safe lift. Signed B and nonzero
C targets are supported. Because each production program writes absolute
production CSV paths, `test.sh` backs up both selected files and restores and
compares them in an EXIT trap on success or failure.

Program, evidence paths, target pose, and campaign can be selected with
`TWP_SPHERE_TEST_PROGRAM`, `TWP_SPHERE_TEST_PASSES`,
`TWP_SPHERE_TEST_RESULTS`, `TWP_SPHERE_TEST_TARGET_B`,
`TWP_SPHERE_TEST_TARGET_C`, and `TWP_SPHERE_TEST_CAMPAIGN`. Captured linear
states can be replayed with `TWP_SPHERE_TEST_G54` and
`TWP_SPHERE_TEST_START_WORK`; both take three comma-separated values. The
start and return pose remains B0/C0. Regardless of overrides, the fixture
asserts that the large configured homing offsets remain present between
`joint.N.pos-cmd` and `joint.N.motor-pos-cmd` throughout setup.
