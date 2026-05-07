# 5th Axis XYZBC SSI Probe Basic Config

This directory is the Probe Basic calibration copy of the locked
`5th_axis_xyzbc_ssi_maintenance` baseline.

Scope:

- keep the live machine motion, limits, probe wiring, and B/C SSI feedback path
  aligned with the locked AXIS maintenance config; B/C homing now uses absolute
  encoder mode so rotary zero cannot be redefined at an arbitrary position
- switch the UI to Probe Basic for probing, calibration, and upcoming TCPC work
- leave the AXIS maintenance config untouched as the fallback machine baseline

Current machine assumptions:

- axes present: `X/Y/Z/B/C`
- kinematics remain `trivkins coordinates=XYZBC`
- X/Y/Z homing remains enabled exactly as in the locked maintenance config
- B/C use the validated SSI zero constants and wrap normalization
- B/C backlash compensation is disabled because the rotary output position is
  already measured directly by SSI feedback
- B/C use `HOME_ABSOLUTE_ENCODER = 2`, so homing preserves the SSI-derived
  rotary angle instead of redefining the current position as B0/C0
- `nc_files/calibration/rotary_ssi_zero_verify.ngc` is available as a
  no-motion post-home B/C SSI zero check
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
- current TCPC fit preparation notes are in `TCPC_FIT_NEXT_SCOPE.md`; use the
  curated `tcpc-fit-input-candidates.csv` rows for the first offline fit instead
  of fitting every raw log row

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_probe_basic/launch_xyzbc_ssi_probe_basic.sh
```

Fallback:

- `configs/5th_axis_xyzbc_ssi_maintenance` remains the locked AXIS fallback

Latest TCPC fitting status, 2026-05-04:

- validated C-center correction remains the only persistent correction
- the simulation-gated B/C cross candidate measured all-validation RMS/max of
  `0.096378 / 0.176626 mm`
- a refined replacement machine plus B/C cross candidate is prepared in
  `configs/sim/head_head_5axis/head_head_bharmonic_refined_candidate.hal`
- refined candidate non-GUI verification and LinuxCNC sim smoke have passed
- keep all candidates non-persistent and `headheadkins.sim-bharm-enable = FALSE`
- continue from `TCPC_FIT_NEXT_SCOPE.md` for the next machine probing steps
