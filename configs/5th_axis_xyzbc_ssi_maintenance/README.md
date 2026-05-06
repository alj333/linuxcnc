# 5th Axis XYZBC SSI Maintenance Config

Locked maintenance config copied from the validated `5th_axis_xyzbc_ssi_feedback_test` state.

Purpose:

- move `X/Y/Z/B/C` during machine setup and testing
- keep homing disabled on startup for assembly work
- drive `B` and `C` with the original 5th Axis stepgen servo style
- use the new SSI absolute encoders as B/C servo feedback for maintenance motion

Important:

- B/C are intentionally speed-limited for SSI closed-loop maintenance: angular jog max `8 deg/s`, default `2 deg/s`; B/C joint max velocity `8 deg/s`; B/C joint accel `24 deg/s^2`; B/C PID output cap `8 deg/s`; B/C stepgen max velocity `12 deg/s`; B/C stepgen accel `48 deg/s^2`
- `B` and `C` motor feedback is the zeroed SSI encoder position
- SSI encoder pins feed zeroing math, and the zeroed outputs feed `joint.3/4.motor-pos-fb`
- the AXIS PyVCP side panel shows zeroed SSI alignment positions and data-invalid LEDs
- the zeroed feedback/display offsets are in `b_ssi_zero.in1` and `c_ssi_zero.in1`; the raw HostMot2 SSI pins are unchanged
- B/C can start near the SSI single-turn wrap, so this maintenance config normalizes the `-360` startup branch back into the local angle range before feeding the joints
- C display/feedback applies `c_ssi_axis_scale.in1 = -1.0`, matching the validated SSI feedback test direction
- pendant jogging uses the old known-good `axis.*.jog-*` path, not direct `joint.*` jog pins
- manual tool release uses `hm2_7i95.0.inmux.00.input-16` to drive `hm2_7i95.0.ssr.00.out-05` through a spindle-on interlock; the solenoid cannot energize while `spindle.0.on` is true

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh
```

## Maintenance Scope

Use this config for XYZBC maintenance motion with B/C SSI feedback. It is not a
production machining or cutting config.

Assumptions:

- axes present: `X/Y/Z/B/C`
- homing is not required on startup
- B/C drive outputs still use the original 5th Axis stepgen output path
- B/C motor feedback comes from the zeroed SSI encoder position
- B SSI feedback/display is 1:1 zeroed encoder delta
- C SSI feedback/display is inverted after the startup wrap-branch normalization to match the validated C-axis command direction
- pendant jogging stays on the known-good `axis.*.jog-*` path

The locked no-SSI maintenance fallback remains:

- `configs/5th_axis_xyzbc_maintenance`

Use that fallback config for maintenance servo motion without SSI feedback.

## Safety Scope

This is for maintenance motion using B/C SSI feedback. It was validated with
jog and MDI motion at the current conservative limits, but live programs still
need proving for coordinated motion, blending, reversals, and larger B/C moves.
If feedback direction or following-error behavior is wrong, return to the locked
no-SSI `5th_axis_xyzbc_maintenance` config.
