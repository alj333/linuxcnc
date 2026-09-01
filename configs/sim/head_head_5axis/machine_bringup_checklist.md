# Superseded Head-Head Machine Bring-Up Checklist

Status: historical pre-build checklist

The former checklist allowed partial/unhomed motion and referenced obsolete
20 mm sphere, granite-square, and prototype TWP programs. It must not be used
on the operational CNC.

Current controller setup and recovery requirements are in:

- [replacement-cnc-pc-setup.md](/home/cnc5/linuxcnc-dev/docs/replacement-cnc-pc-setup.md)
- [README.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/README.md)
- [TCPC_CALIBRATION_RESUME_STATE.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_CALIBRATION_RESUME_STATE.md)
- [TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md)

The operational configuration requires all five joints homed before calibrated
TCPC/TWP mode changes. Legacy simulation programs in this directory are not
released machine bring-up programs.
