# Superseded Machine Rotary Zeroing Sequence

Status: historical pre-calibration procedure

The former visual granite-square sequence predates the SSI commissioning,
certified sphere campaigns, long/short tool model, and frozen calibration
revision `2026082601`. Do not use it to change B/C zeros or kinematic
coefficients.

Current calibration state and restrictions are in:

- [TCPC_CALIBRATION_RESUME_STATE.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_CALIBRATION_RESUME_STATE.md)
- [TCPC_LONG_SHORT_PROBE_CALIBRATION_PLAN.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_LONG_SHORT_PROBE_CALIBRATION_PLAN.md)
- [TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md)

Any future rotary-zero or rail/alignment campaign must be separately planned,
measured, and reviewed. TWP cut testing must use the frozen shared calibration
and must not infer new zeros from a single workpiece or table position.
