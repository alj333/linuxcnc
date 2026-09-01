# MotionX Fusion Post

## Release State

The current release candidate is commit
`5679acd836b6022a0884ca1f88efd282f56beb48` on branch
`head-head-kinematics-rnd-pushable`. The SHA-256 of
`pocketnc-motionX 3.cps` is
`517429a2809c43be982ed36cdd3cae9e12d32f89bed97ab4a4fd5b8b0c066420`.

Static source-contract, output-validator self-test, and TWP sphere-program
checks pass. A real Fusion-generated program has not yet completed manual
review, LinuxCNC load testing, an air path, or a material cut. Until those
steps pass, this is a supervised test candidate rather than a production post.
The current checklist is
`configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md`.

## Files

- `pocketnc-motionX 3.cps` is the editable MotionX LinuxCNC post.
- `FANUC_30i_Matsuura_MAM72_3VS.cps` is a table-table Fanuc 30i reference.
  Its Fusion TWP state sequencing is relevant; its machine geometry, rotary
  positioning, clamps, and tool-length positioning are not used on MotionX.
- `validate_motionx_twp_output.py` checks a Fusion-generated NGC file before
  LinuxCNC load testing.

## Modes

The post keeps three separate controller modes:

- ordinary three-axis: `G43 Hn`, with `useTWP` disabled
- simultaneous TCPC: `G43 Hn`, then `G43.4`; cancel with `G49.1`
- indexed TWP: `G43 Hn`, world retract and B/C index, `G68.2`, separate
  immediately following `G53.1`, fixed-B/C local motion, local retract, `G69`

Set `useTCP` for simultaneous operations. Set `useTWP` for indexed 3+2
operations. Both may be enabled in a mixed program because their section paths
are mutually exclusive. Indexed TWP is limited to the commissioned
`|B| <= 30 deg` envelope.

Use `G28` or `G53` for the Safe Retracts property when TWP is enabled.
Clearance Height is rejected because it does not establish a reviewed machine
retract before head indexing.

## Tool Length

The LinuxCNC tool table and active `G43 Hn` value are authoritative. The post
uses Fusion's H offset number but does not use Fusion gauge length, body length,
holder length, or a Fanuc table-table positioning calculation for TWP entry.
The controller validates the live effective tool length when `G68.2` is
requested.

Public TCPC is not used to preposition a TWP section. It must be off before
`G68.2`, and the commissioned TCPC closeout returns B/C to zero before
`G49.1`.

## Offline Gate

After posting in Fusion, run:

```bash
python3 "Fusion Post/validate_motionx_twp_output.py" path/to/program.ngc
```

The validator checks TLO and mode order, complete rotating-ZXZ frame words,
immediate `G53.1`, the B release limit, world and local retracts, active-frame
motion restrictions, and final TCPC/TWP closeout.

The first posted three-axis, TCPC, TWP, and mixed-mode samples still require
manual review. TWP output must then be previewed and load-tested in the
dedicated TWP-enabled LinuxCNC configuration before any supervised air path.

At the 2026-09-01 closeout LinuxCNC was fully closed with no controller
process or lock remaining. The next machine session must start cleanly and
re-establish homing, tool, live `G43 H`, G5X, and mode state; no modal state
from post development or prior sphere testing may be assumed.
