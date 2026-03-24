# Head-Head 5-Axis Machine Bring-Up Checklist

Use this as the first real-machine sequence before trusting any posted 5-axis
toolpath. The goal is to confirm the machine is sane, the rotary zero is
believable, and TCPC/TWP behavior is good enough to continue into calibration.

## Preconditions

- Probe Basic head-head config is running
- machine is powered and clear of faults
- probe, 20 mm sphere stand, and granite square are available
- safe travel around the sphere stand has already been checked
- current configs already allow unhomed motion on startup:
  - `head_head_probe_basic.ini`
  - `head_head_visual_sim.ini`
  - `head_head_math_sim.ini`
  - current legacy `5th_axis.ini`
- this means early power-up and jog/recovery work can be done before a full
  homing path is available

## Ordered Checklist

1. Power up and clear faults
   - release E-stop
   - power the machine
   - confirm drives and axis feedback look sane
   - if only `X/Y` are assembled, it is acceptable to move those axes without
     homing first
   - do not attempt a fake full-home just to get motion
   - log result as `pass`, `hold`, or `fail`

2. Establish reference state
   - if the machine is only partly assembled, skip full homing and use unhomed
     motion carefully for first-power checks
   - once the full axis set and home path are available, home/reference the
     machine using the normal shop method
   - cancel any leftover TWP with `G69`
   - disable TCPC with `G49.1`
   - move to a safe pose such as `G0 X1500 Y850 Z-600 B0 C0`
   - confirm no unexpected motion

3. Qualify the probe
   - qualify the OMP40-style probe in the 50 mm ring
   - repeat until repeatability is stable
   - do not continue if repeatability is poor

4. Set up the sphere artifact
   - mount the 20 mm sphere on the tall 45 degree stand
   - place it in a reachable area with safe clearance through the planned B/C poses
   - record the stand location in the wizard notes

5. Zero the rotary reference
   - run [machine_b_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_b_zero_alignment_check.ngc)
   - run [machine_c_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_c_zero_alignment_check.ngc)
   - use the granite square for `B0`
   - use a clear machine-forward spindle reference for `C0`
   - do not move on until `B0/C0` is believable

6. Capture the sphere map
   - run [calibration_sphere_capture_sequence.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/calibration_sphere_capture_sequence.ngc)
   - probe the sphere center at each stop
   - capture the results in the wizard `Sphere Map` page
   - use the recommendation block to choose the first small offset change

7. Verify fixed-tip TCP
   - run [machine_tcp_fixed_tip_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_fixed_tip_probe_check.ngc)
   - confirm the probe tip stays on the same sphere center while B/C change
   - if the tip walks, return to rotary zero and sphere-map interpretation first

8. Verify moving TCP
   - run [machine_tcp_motion_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_motion_probe_check.ngc)
   - confirm the TCP path looks smooth and returns cleanly
   - stop if you see visible tip swing or discontinuity

9. Verify TWP plane behavior
   - run [machine_twp_granite_square_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_twp_granite_square_check.ngc)
   - use the granite square as a sanity check on the active tilted plane
   - only treat TWP as usable after TCP is already believable

10. Record the outcome
   - update the wizard bring-up checklist fields
   - save the draft
   - copy the generated summary into the machine log or job note

## Stop Conditions

Stop and correct the setup before continuing if any of these occur:

- poor probe repeatability
- obvious B/C zero sign error
- clearance concerns during rotary checks
- fixed-tip TCP drift that is too large to explain by a small zero error
- moving TCP path discontinuity
- TWP plane motion that is visibly inconsistent with the granite square
