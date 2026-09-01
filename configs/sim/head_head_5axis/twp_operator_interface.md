# Superseded TWP Operator Interface Proposal

Status: historical simulation proposal

This document's earlier UI/HAL proposal and sample `G88.5` workflow were
superseded by the implemented `G68.2` / `G53.1` / `G69` switchkins path. The
filename remains so older links resolve safely.

Current operator and posted-code behavior is defined in:

- [TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md)

Current physical acceptance is recorded in:

- [TWP_SPHERE_GRID_LOW_ANGLE_T4_CLOSEOUT_2026090103.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_SPHERE_GRID_LOW_ANGLE_T4_CLOSEOUT_2026090103.md)

Do not use the legacy M150-M156 or `G88.5` helper commands as a Fusion post
target. They remain simulator/debug fixtures only.
