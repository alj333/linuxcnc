# 5th Axis XYZBC SSI Feedback Test Config

Temporary dev/test config copied from the locked `5th_axis_xyzbc_maintenance` baseline.

Purpose:

- move `X/Y/Z/B/C` during machine setup and testing
- keep homing disabled on startup for assembly work
- drive `B` and `C` with the original 5th Axis stepgen servo style
- use the new SSI absolute encoders as B/C feedback for dev/test

Important:

- B/C are intentionally speed-limited for early SSI closed-loop testing: angular jog max `8 deg/s`, default `2 deg/s`; B/C joint max velocity `8 deg/s`; B/C joint accel `24 deg/s^2`; B/C PID output cap `8 deg/s`; B/C stepgen max velocity `12 deg/s`; B/C stepgen accel `48 deg/s^2`
- `B` and `C` motor feedback is the zeroed SSI encoder position
- SSI encoder pins feed zeroing math, and the zeroed outputs feed `joint.3/4.motor-pos-fb`
- the AXIS PyVCP side panel shows zeroed SSI alignment positions and data-invalid LEDs
- the zeroed feedback/display offsets are in `b_ssi_zero.in1` and `c_ssi_zero.in1`; the raw HostMot2 SSI pins are unchanged
- B/C can start near the SSI single-turn wrap, so this test config normalizes the `-360` startup branch back into the local angle range before feeding the joints
- C display/feedback currently applies `c_ssi_axis_scale.in1 = -1.0`; verify this against actual commanded motion before treating C SSI feedback direction as proven
- pendant jogging uses the old known-good `axis.*.jog-*` path, not direct `joint.*` jog pins

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_feedback_test/launch_xyzbc_ssi_feedback_test.sh
```

## Feedback Test Scope

Use this config only for the next B/C SSI feedback development step. It is not a
production machining or cutting config.

Assumptions:

- axes present: `X/Y/Z/B/C`
- homing is not required on startup
- B/C drive outputs still use the original 5th Axis stepgen output path
- B/C motor feedback comes from the zeroed SSI encoder position
- B SSI feedback/display is 1:1 zeroed encoder delta
- C SSI feedback/display is currently inverted after the startup wrap-branch normalization; this still needs a tiny-motion direction check against the actual C axis
- pendant jogging stays on the known-good `axis.*.jog-*` path

The locked maintenance fallback remains:

- `configs/5th_axis_xyzbc_maintenance`

Use that fallback config for maintenance servo motion without SSI feedback.

## Safety Scope

This is for SSI feedback development/testing only. Start with B/C drives disabled
or mechanically safe, then test one axis at a time with very small jogs. If
feedback direction or following error behavior is wrong, return to the locked
`5th_axis_xyzbc_maintenance` config.
