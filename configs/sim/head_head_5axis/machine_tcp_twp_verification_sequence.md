# Machine TCP/TWP Verification Sequence

## Purpose

This is the first practical machine-side verification sequence after the head-head
geometry is close enough to trust visually.

Use it with:

- qualified OMP40-style wireless probe
- 20 mm sphere on the tall 45 degree stand
- large granite square

The goal is not final calibration math. The goal is to prove:

1. fixed-tip TCPC behaves believably on the sphere
2. moving TCP behaves smoothly
3. TWP looks sensible against a known flat reference

## Preconditions

- machine is in a safe verified state for 5-axis motion
- probe is qualified in the 50 mm ring
- 20 mm sphere is mounted in a reachable area
- granite square is positioned for a clear visual plane check
- no active TWP state before starting
- TCPC is off before starting

Expected controls:

- `G43.4` = TCPC on
- `G49.1` = TCPC off
- `G68.2` = define/activate TWP
- `G69` = cancel TWP

## Run Order

1. Run [machine_tcp_fixed_tip_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_fixed_tip_probe_check.ngc)
2. Run [machine_tcp_motion_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_motion_probe_check.ngc)
3. Run [machine_twp_granite_square_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_twp_granite_square_check.ngc)

Do not move on to the next program if the previous one shows obvious drift,
tip swing, or a recovery error.

## Stage 1: Fixed-Tip TCP On Sphere

Program:

- [machine_tcp_fixed_tip_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_fixed_tip_probe_check.ngc)

Operator method:

1. Probe the 20 mm sphere center at `B0 C0`.
2. Leave the probe tip centered on the sphere.
3. Run the program and watch only the tip-to-sphere relationship.
4. At each stop, decide whether the tip stayed centered or visibly walked.
5. When the program returns to `B0 C0`, confirm the same sphere center is recovered.

Pass condition:

- no visible tip swing off the sphere center through the programmed `B/C` poses

If it fails:

- check `B_ZERO_OFFSET` and `C_ZERO_OFFSET` first
- then review `cal-c-to-b` and `cal-b-to-tool`

## Stage 2: Moving TCP

Program:

- [machine_tcp_motion_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_motion_probe_check.ngc)

Operator method:

1. Start from the same verified area used for the fixed-tip check.
2. Run the moving TCP program.
3. Watch for any abrupt change in tip behavior when XYZ and `B/C` move together.
4. Pay attention to path continuity and return-to-start repeatability.

Pass condition:

- path looks smooth
- no visible jump at orientation changes
- return to the start pose is believable

## Stage 3: TWP Granite-Square Sanity Check

Program:

- [machine_twp_granite_square_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_twp_granite_square_check.ngc)

Operator method:

1. Position the granite square so the head motion can be judged clearly.
2. Run the TWP check only after TCP is believable.
3. Watch the local `U/V/W` moves and compare them to the expected tilted plane.
4. Confirm `G69` cleanly restores world-coordinate behavior.

Pass condition:

- local tilted-plane moves look geometrically sensible
- cancel and recovery are clean

## Record Keeping

Log the result in the Probe Basic `5 AXIS CALIBRATION` tab:

- what artifact was used
- which program passed or failed
- what pose first showed drift
- whether the problem looked like rotary zero, pivot offset, or tool offset
