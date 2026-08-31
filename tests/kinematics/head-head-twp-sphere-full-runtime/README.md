# Head-head TWP sphere full runtime

This fixture runs the actual
`nc_files/calibration/twp_sphere_probe_stage1_t4.ngc` in AUTO with the
commissioned 2026082601 length-aware overlay, T4/H4, G43.4, B+5 C0, and a
nonzero G54 XYZ offset.

The simulated 30 mm sphere is fixed in world space. During real G38 motion the
UI independently reconstructs the physical probe ball center from joint
commands, the evaluated kinematics tool vector, and the TCPC origin. It drives
the raw receiver input at the program's 17.845258 mm contact envelope. The HAL
then passes that signal through the production-style raw mux, motion-type-5
gate, short test-only falling-edge ignore, and sticky `counter.2` edge count.

The test checks the M0 contract, reversible TWP Z preflight, all 24 contacts,
six pass rows, one accepted result row, physical WORLD/TWP/WORLD center closure,
final G69/world state, fixed B/C, T4/model state, and final safe lift. Because
the production program writes absolute production CSV paths, `test.sh` backs up
both files and restores and compares them in an EXIT trap on success or failure.
