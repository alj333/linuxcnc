# Head-Head 5-Axis Calibration Procedure

## Scope

This is the first practical shop-floor procedure for calibrating the head-head
machine with:

- OMP40-style wireless probe
- 50 mm ID calibration ring
- 20 mm sphere on a tall 45 degree stand
- large granite square

It is intentionally staged. The goal is to establish:

1. rotary axis direction and zero agreement
2. repeatable B/C motion
3. repeatable sphere-center drift map across a standard pose set
4. stable fixed-tip TCPC behavior
5. stable moving 5-axis TCP behavior

This procedure does not yet automate solving the final offsets. It defines the
measurement and verification sequence the operators should follow while using
the Probe Basic calibration wizard.

Companion operator checklist:

- [machine_bringup_checklist.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_bringup_checklist.md)

Practical machine verification package:

- [machine_tcp_twp_verification_sequence.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_twp_verification_sequence.md)
- [machine_tcp_fixed_tip_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_fixed_tip_probe_check.ngc)
- [machine_tcp_motion_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_motion_probe_check.ngc)
- [machine_twp_granite_square_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_twp_granite_square_check.ngc)

Rotary zeroing package:

- [machine_rotary_zeroing_sequence.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_rotary_zeroing_sequence.md)
- [machine_b_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_b_zero_alignment_check.ngc)
- [machine_c_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_c_zero_alignment_check.ngc)

## Required Setup

- Probe Basic head-head config running
- machine homed
- no active TWP state
- TCPC off unless a step explicitly enables it
- probe qualified before any rotary or TCP checks

Known helper controls:

- `G43.4` = TCPC on
- `G49.1` = TCPC off
- `G69` = cancel TWP

Primary calibration tab:

- `5 AXIS CALIBRATION`

## Stage 1: Probe Qualification

Purpose:

- make sure the measurement chain is trustworthy before touching rotary offsets

Procedure:

1. Load the probe and home the machine.
2. Cancel any leftover TWP state with `G69`.
3. Make sure TCPC is off with `G49.1`.
4. Qualify the wireless probe in the 50 mm ring using the normal shop method.
5. Record measured repeatability in the wizard `Probe Qual` page.
6. Touch the 20 mm sphere several times at `B0 C0`.
7. Repeat at one additional rotary pose, preferably `B45 C90`, if reachable.
8. If repeatability is poor, stop and fix probe or fixturing issues first.

Acceptance:

- ring qualification repeatability is stable
- sphere center pickup repeats cleanly

## Stage 2: Basic Rotary Alignment

Purpose:

- confirm B and C move in the expected directions
- confirm commanded zero poses match the intended machine orientation
- establish the first believable `B0` and `C0` references before TCP work

Program:

- [calibration_bc_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_bc_alignment_check.ngc)

Procedure:

1. Keep TCPC off.
2. Move the probe clear of fixtures.
3. Run the rotary alignment check program.
4. If the machine is at the first real zeroing stage, run the dedicated zeroing sequence:
   - [machine_b_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_b_zero_alignment_check.ngc)
   - [machine_c_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_c_zero_alignment_check.ngc)
5. Because the new encoders are mounted directly on the gearbox output, focus on getting the zero reference right first.
4. At each stop, confirm:
   - B positive tilts in the expected direction
   - C positive rotates in the expected direction
   - the head returns cleanly to `B0 C0`
6. Use the granite square as a visual reference for `B0`.
7. Use the sphere or another clear visual reference to confirm `C0`, `C90`,
   `C180`, and `C-90` orientation logic.

Acceptance:

- no unexpected axis reversal
- no obvious zero sign mistake
- no clearance issue through the basic B/C poses

## Stage 3: Sphere Center Capture Map

Purpose:

- capture actual measured sphere-center drift at a repeatable set of B/C poses
- separate gross rotary-zero problems from remaining geometry error

Program:

- [calibration_sphere_capture_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_sphere_capture_sequence.ngc)

Wizard page:

- `Sphere Map`

Procedure:

1. Keep TCPC off for the first capture pass.
2. Run the sphere capture sequence.
3. At each stop, probe the 20 mm sphere center using the same cycle.
4. When the machine is sitting at the measured sphere center, press `Capture Current` for that pose in the wizard.
5. Use the wizard drift table to compare every pose back to the `B0 C0` reference.
6. Do not change offsets yet until the drift pattern is visible.

How to read the first-pass map:

- `B plus` and `B minus` drifting in opposite directions usually points to `B_ZERO_OFFSET` first.
- `C plus` and `C minus` drifting in opposite directions usually points to `C_ZERO_OFFSET` first.
- common drift that remains after zero cleanup usually points toward `cal-c-to-b` or `cal-b-to-tool`.

Acceptance:

- all standard poses are reachable safely
- the capture map is repeatable enough to guide offset changes

## Stage 4: Rotary Zero Correction Capture

Purpose:

- establish the first `B_ZERO_OFFSET` and `C_ZERO_OFFSET` values
- refine zero after the mechanical/reference alignment is already believable

Wizard page:

- `Rotary Zero`

Procedure:

1. Keep using the same qualified probe and sphere setup.
2. At `B0 C0`, confirm the spindle/probe axis agrees with the intended zero.
3. Check a second pose such as `B45 C90`.
4. Adjust only the small correction needed beyond the nominal zero model.
5. Enter trial values in the wizard.
6. Use `Apply To Running Sim` only as a staging check while proving the sign.

Acceptance:

- `B0 C0` looks correct
- the second check pose improves, not worsens
- sign convention is stable between checks

## Stage 5: Basic B/C Motion Verification

Purpose:

- prove the machine can move B and C repeatedly before TCPC is involved

Procedure:

1. Re-run [calibration_bc_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_bc_alignment_check.ngc).
2. Jog or MDI back to `B0 C0`.
3. Repeat selected B-only and C-only moves manually if needed.
4. Confirm the sphere stand remains in a safe reachable area.

Acceptance:

- repeatable return to `B0 C0`
- no axis hesitation or obvious mismatch between commanded and observed pose

## Stage 6: Fixed-Tip TCPC Verification

Purpose:

- verify TCP holds the measured sphere center while B and C change

Program:

- [calibration_tcpc_fixed_tip_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_tcpc_fixed_tip_check.ngc)

Procedure:

1. Start from a safe pose near the sphere.
2. Enable TCPC with `G43.4` or run the fixed-tip check program directly.
3. At each stop, confirm the probe tip stays on the same sphere center target
   while B and C change.
4. If the tool tip walks off the target:
   - check rotary zero corrections first
   - then review `C->B` and `B->tool` correction values

Acceptance:

- no obvious tip swing while only B/C change
- return to home orientation lands on the same sphere center

## Stage 7: Moving 5-Axis TCP Verification

Purpose:

- verify the machine can move XYZ and B/C together while keeping TCP coherent

Program:

- [calibration_tcpc_motion_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_tcpc_motion_check.ngc)

Procedure:

1. Run the moving TCPC check only after the fixed-tip check passes.
2. Watch the tool tip path as XYZ and B/C change together.
3. Confirm the path remains smooth with no visible discontinuity or swing.
4. Return to the start pose and confirm repeatability.

Acceptance:

- tool tip follows a smooth path
- no obvious jump at orientation changes
- return-to-start error is not visible

## Stage 8: Geometry Correction Capture

Purpose:

- collect the first usable `cal-c-to-b` and `cal-b-to-tool` values

Wizard pages:

- `C To B`
- `B To Tool`

Procedure:

1. Use the sphere as the common reference artifact.
2. Capture enough B/C poses to understand whether the error follows:
   - rotary zero only
   - C-to-B pivot offset
   - B-to-tool offset
3. Enter only the correction beyond the nominal geometry.
4. Apply the values to the running sim and repeat Stage 5 and Stage 6.

Acceptance:

- fixed-tip TCPC improves
- moving TCPC improves
- corrections remain small and coherent, not arbitrary large compensations

## Stage 9: Final Plane Sanity Check

Purpose:

- make sure the solved geometry still behaves sensibly against a known flat
  reference

Procedure:

1. Use the granite square as a final visual check after TCP is stable.
2. Tilt the head to a practical working orientation.
3. Confirm the spindle/probe axis and plane behavior remain believable.
4. Use this only as a sanity check, not as the primary source of numeric offset
   values.

## Current Calibration Program Set

- [calibration_sphere_capture_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_sphere_capture_sequence.ngc)
- [calibration_bc_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_bc_alignment_check.ngc)
- [calibration_tcpc_fixed_tip_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_tcpc_fixed_tip_check.ngc)
- [calibration_tcpc_motion_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_tcpc_motion_check.ngc)

Legacy development programs still available:

- [tcp_tcpc_fresh_demo.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/tcp_tcpc_fresh_demo.ngc)
- [tcp_test_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/tcp_test_sequence.ngc)
- [tcp_motion_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/tcp_motion_sequence.ngc)

## Initial Operator Rule

Use this order until the machine is fully calibrated:

1. qualify probe
2. verify basic B/C motion
3. build the sphere-center drift map
4. establish rotary zero corrections
5. verify fixed-tip TCPC
6. verify moving TCPC
7. only then move on to TWP work
