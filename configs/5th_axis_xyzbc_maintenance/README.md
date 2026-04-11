# 5th Axis XYZBC Maintenance Config

Temporary real-machine setup config copied from `5th_axis_xyz_maintenance`.

Purpose:

- move `X/Y/Z/B/C` during machine setup and testing
- keep homing disabled on startup for assembly work
- drive `B` and `C` with the original 5th Axis stepgen servo style
- display the new SSI absolute encoders for B/C alignment only

Important:

- `B` and `C` motor feedback is still `hm2_7i95.0.stepgen.03/04.position-fb`
- SSI encoder pins `hm2_7i95.0.ssi.00/01.abs.position` are not connected to `joint.3/4.motor-pos-fb`
- the AXIS PyVCP side panel shows zeroed SSI alignment positions and data-invalid LEDs
- the zeroed display offsets are in `b_ssi_zero.in1` and `c_ssi_zero.in1`; the raw HostMot2 SSI pins are unchanged
- C display applies an additional `c_ssi_axis_scale.in1 = 1.0` multiplier for the corrected C-axis display relationship
- pendant jogging uses the old known-good `axis.*.jog-*` path, not direct `joint.*` jog pins

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_maintenance/launch_xyzbc_maintenance.sh
```
## Locked Baseline

Use this config only for moving servos during maintenance/setup work. It is not a
production machining, calibration, or SSI-feedback commissioning config.

Locked assumptions:

- maintenance servo motion only; no cutting or production operation
- axes present: `X/Y/Z/B/C`
- homing is not required on startup
- B/C drives use the original 5th Axis stepgen servo output path
- B/C motor feedback stays on stepgen feedback
- SSI encoders are display-only and are not part of the servo loop
- B SSI display is 1:1 zeroed encoder delta
- C SSI display is 1:1 zeroed encoder delta
- pendant jogging stays on the known-good `axis.*.jog-*` path

Do not connect SSI to `joint.3/4.motor-pos-fb` in this maintenance config. Make
a separate next-stage config when we are ready to test SSI feedback in the servo
loop.
