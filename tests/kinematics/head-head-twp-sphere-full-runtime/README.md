# Head-head TWP sphere full runtime

This fixture runs the actual
`nc_files/calibration/twp_sphere_probe_stage1_t4.ngc` in AUTO with the
commissioned 2026082601 length-aware overlay, T4/H4, public TCPC off, B+5 C0,
and a nonzero G54 XYZ offset. Its simulated homing state also retains the large
XYZ separation between machine joint coordinates and `motor-pos-cmd` observed
on the physical controller. This prevents motor-layer coordinates from passing
as valid TWP frame inputs merely because a zero-offset simulator made the two
layers numerically identical.

The simulated 30 mm sphere is fixed in world space. During real G38 motion the
UI independently reconstructs the physical probe ball center from joint
commands and the evaluated kinematics tool vector. It drives
the raw receiver input at the program's 17.845258 mm contact envelope. The HAL
then passes that signal through the production-style raw mux, motion-type-5
gate, short test-only falling-edge ignore, and sticky `counter.2` edge count.

The test checks the M0 contract, reversible TWP Z preflight, all 24 contacts,
six pass rows, one accepted result row, physical WORLD/TWP/WORLD center closure,
final G69/world state, fixed B/C, T4/model state, and final safe lift. Because
the production program writes absolute production CSV paths, `test.sh` backs up
both files and restores and compares them in an EXIT trap on success or failure.

Captured physical states can be replayed with `TWP_SPHERE_TEST_B`,
`TWP_SPHERE_TEST_C`, `TWP_SPHERE_TEST_G54`, and
`TWP_SPHERE_TEST_START_WORK`. The two vector variables take three
comma-separated values. Regardless of overrides, the fixture asserts that the
large configured homing offsets remain present between `joint.N.pos-cmd` and
`joint.N.motor-pos-cmd` throughout setup.
