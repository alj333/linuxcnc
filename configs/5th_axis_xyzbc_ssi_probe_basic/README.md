# 5th Axis XYZBC SSI Probe Basic Config

This directory is the Probe Basic calibration copy of the locked
`5th_axis_xyzbc_ssi_maintenance` baseline.

Scope:

- keep the live machine motion, homing, limits, probe wiring, and B/C SSI
  feedback path identical to the locked AXIS maintenance config
- switch the UI to Probe Basic for probing, calibration, and upcoming TCPC work
- leave the AXIS maintenance config untouched as the fallback machine baseline

Current machine assumptions:

- axes present: `X/Y/Z/B/C`
- kinematics remain `trivkins coordinates=XYZBC`
- X/Y/Z homing remains enabled exactly as in the locked maintenance config
- B/C use the validated SSI zero constants and wrap normalization
- the touch probe path is live through `motion.probe-input`
- manual tool release still uses the spindle-off interlock on input `16`

Probe Basic-specific additions:

- `DISPLAY = probe_basic`
- local `custom_config.yml`, `probe_basic_postgui.hal`, and `pbsplash.png`
- local `python/`, `subroutines/`, `remap_subs/`, and Probe Basic UI folders
- manual tool-change nets exported for Probe Basic's dialog

Important limitation:

- this is still a `trivkins` machine config
- TCPC/TWP remaps are not enabled yet
- use this build to continue probing and calibration work before the TCPC
  integration pass

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_probe_basic/launch_xyzbc_ssi_probe_basic.sh
```

Fallback:

- `configs/5th_axis_xyzbc_ssi_maintenance` remains the locked AXIS fallback
