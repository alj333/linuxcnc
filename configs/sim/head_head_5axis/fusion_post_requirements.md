# Fusion Postprocessor Requirements

Status: superseded compatibility index

The simulation-era requirements previously stored here no longer match the
commissioned TWP implementation. This filename remains only to preserve
existing repository links.

The complete current Fusion post contract is:

- [TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md)

Critical changes from the old proposal:

- indexed TWP uses ordinary `G43 H`; public `G43.4` must be off
- B/C are safely positioned before `G68.2`
- production output uses rotating-`ZXZ` `G68.2 X/Y/Z/I/J/K`
- `G53.1` is a separate mandatory stationary activation block
- B/C stay fixed until `G69`
- active TWP supports linear XYZ only; arcs and canned cycles must be
  linearized/expanded or rejected by the post
- simultaneous 5-axis work is a separate TCPC workflow, not TWP

The implemented MotionX post and its review tooling are now:

- `Fusion Post/pocketnc-motionX 3.cps`
- `Fusion Post/validate_motionx_twp_output.py`
- `tests/kinematics/head-head-fusion-post-static/test.py`

Release candidate `5679acd836b6022a0884ca1f88efd282f56beb48` passed the
repository static and validator self-tests. Its first actual Fusion output,
LinuxCNC load, air path, and material cut are still pending. Use the current
handoff:

- [TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md)

`Fusion Post/FANUC_30i_Matsuura_MAM72_3VS.cps` is retained only as a
table-table sequencing reference. Its geometry, stock positioning, clamps,
and tool-length calculations must not be transferred to this head-head
machine.
