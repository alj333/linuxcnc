# Head-Head Visual Acceptance Checklist

Use this checklist with:

- `configs/sim/head_head_5axis/head_head_visual_sim.ini`
- the cyan alignment post/cross
- the green table centerlines
- the table corner markers

## Setup

1. Launch the visual sim.
2. Home all axes.
3. Confirm the tool tip is visibly above the table.
4. Confirm the cyan post/cross and green guides move with the table.

## Travel Direction

### X

1. Jog `X+`.
2. Confirm the head/tool moves to the right.
3. Jog `X-`.
4. Confirm the head/tool moves to the left.

### Y

1. Jog `Y+`.
2. Confirm the table moves in the visually opposite direction expected for a
   moving-table axis.
3. Confirm the cyan post/cross moves with the table.

### Z

1. Jog `Z+`.
2. Confirm the tool tip moves up.
3. Jog `Z-`.
4. Confirm the tool tip moves down toward the table.

## Rotary Direction

These checks assume the preferred production right-hand convention.

### B

1. Set `C=0`.
2. Jog `B+`.
3. Confirm the tool tilts toward `-X`.
4. Jog `B-`.
5. Confirm the tool tilts toward `+X`.

### C

1. Set `B=0`.
2. View from above.
3. Jog `C+`.
4. Confirm the head rotates counterclockwise.
5. Jog `C-`.
6. Confirm the head rotates clockwise.

## Fixed-Tip TCP

1. Run `tcp_test_sequence.ngc`.
2. At each `M0`, check the tool tip against the cyan post/cross.
3. Accept only if the tip stays fixed while `B/C` change.

## Moving TCP

1. Run `tcp_motion_sequence.ngc`.
2. Watch the tip path relative to the cyan post/cross and green guide lines.
3. Accept only if the tip path is smooth and orientation changes do not create
   visible path jumps.

## TWP

1. Run `twp_test_sequence.ngc`.
2. Confirm the path stays in the intended tilted plane.
3. Confirm the path orientation is consistent with the current `B/C` pose.

## Fail Conditions

Any of these are failures:

- tip drift during fixed-tip TCP
- reversed X/Y/Z travel
- reversed B/C direction
- table guide markers moving inconsistently with the table
- path discontinuities during moving TCP
- TWP path leaving the expected tilted plane
