# Superseded Fanuc-Like TWP / TCPC Contract

Status: superseded on 2026-09-01

This filename is retained so historical links do not break. It is not the
current controller or postprocessor contract.

Use the authoritative real-machine document:

- [TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md)

Use the current generated-output and cut-test handoff:

- [TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md)

The previous content predated synchronized switchkins TWP and contained two
unsafe assumptions for the commissioned implementation:

- it required public `G43.4` TCPC to be active under TWP
- it described `G68.2` as defining and activating the plane in one command

The commissioned contract is instead:

```text
ordinary G43 H active, public G43.4 off
world clearance and B/C preposition
G68.2 X/Y/Z/I/J/K definition
G53.1 stationary activation
fixed-B/C local G0/G1 XYZ
local clearance
G69 stationary return to world mode
```

The legacy HAL command and `G88.5` paths in the simulation directory remain
test fixtures only. They are not targets for Fusion output or machine
operation.
