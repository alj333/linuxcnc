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

The local Autodesk Fanuc post remains the recommended starting point:

- `/home/cnc5/Fusion/fanuc(1).cps`

It must not be used unchanged. In particular, its stock head positioning can
cancel ordinary tool length or force `G43.4` before TWP; both behaviors are
incompatible with this controller and are covered explicitly in the current
contract.
