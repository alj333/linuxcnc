# Machine Rotary Zeroing Sequence

## Purpose

This is the first machine-side alignment step before TCP or TWP calibration.

The goal is to establish trustworthy `B0` and `C0` because the new rotary
encoders are mounted directly on the gearbox output. Once the zero reference is
set correctly, the encoder feedback should give repeatable rotary positioning.

## Use This Before

- sphere center drift mapping
- fixed-tip TCPC checks
- moving TCP checks
- TWP checks

## Reference Artifacts

For `B0`:

- granite square
- short probe or gauge in the spindle

For `C0`:

- sphere stand orientation
- table reference feature
- any clear spindle-facing machine reference

## Programs

- [machine_b_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_b_zero_alignment_check.ngc)
- [machine_c_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_c_zero_alignment_check.ngc)

## Method

1. Keep `TCPC` off.
2. Keep `TWP` cancelled with `G69`.
3. Run the `B` zero program first.
4. Align `B0` mechanically and by offset so the spindle/probe axis matches the granite-square reference.
5. Use the small `+5 / -5` and `+15 / -15` checks to confirm:
   - positive direction is correct
   - negative direction is correct
   - symmetry around zero looks right
   - return to zero is repeatable
6. Run the `C` zero program second.
7. Align `C0` so the spindle/probe faces the intended machine reference.
8. Use the `+5 / -5` and `90 / 180 / -90` checks to confirm the C-axis sign and indexing logic.
9. Only after both `B0` and `C0` are believable should you move on to sphere mapping and TCP.

## Pass Condition

- `B0` agrees with the granite-square reference
- `C0` agrees with the intended machine-forward reference
- small positive and negative moves look symmetric
- return to zero is visually repeatable

## If It Fails

- correct rotary zero first
- do not try to hide the problem in `cal-c-to-b` or `cal-b-to-tool`
- repeat the zeroing sequence until the zero behavior is stable
