# TWP Implementation And Fusion Post Contract

Status: current authoritative contract

Date: 2026-09-01

Controller branch: `head-head-kinematics-rnd-pushable`

Shared calibration revision: `2026082601`

## Authority And Release State

This document is the single current contract for generating and reviewing
Fusion output that uses tilted work plane on this machine. It replaces the
earlier simulation proposals that described `G68.2` as a mode layered on
public `G43.4`, or as a command that also moves B/C.

The synchronized TWP implementation has passed supervised physical lifecycle
commissioning with T4/H4 at:

- B `+/-5`, `+/-15`, and `+/-30 deg`
- C `0`, `90`, `180`, and `270 deg`
- 24 complete `G68.2` / `G53.1` / `G69` transactions
- 112 motion-gated sphere contacts

The result releases TWP for controlled CAM cut testing. It does not release
unattended or general production use. Physical TWP validation currently ends
at `|B| = 30 deg`; the machine limits remain B `-100..+100 deg` and C
`-359..+359 deg`, but the untested remainder is outside the commissioned TWP
envelope.

Only the dedicated supervised INI currently opts in with `[TWP] ENABLE=1`:

- `5th_axis_xyzbc_ssi_tcpc_probe_basic_twp_probe_validation_2026083101.ini`

The default cut-test INI remains TWP-locked. Updating a Fusion post does not
by itself authorize TWP use in another configuration.

## Current Fusion Post Release Candidate

The reviewed MotionX implementation was committed and pushed on 2026-09-01:

- branch: `head-head-kinematics-rnd-pushable`
- commit: `5679acd836b6022a0884ca1f88efd282f56beb48`
- source: `Fusion Post/pocketnc-motionX 3.cps`
- SHA-256:
  `517429a2809c43be982ed36cdd3cae9e12d32f89bed97ab4a4fd5b8b0c066420`

Repository static checks, generated-output validator self-tests, and the TWP
sphere-program static/coordinate checks pass. This is a post release
candidate, not completed physical post acceptance: no real Fusion-generated
NGC has yet been retained and reviewed, loaded in LinuxCNC, air-run, or cut on
material. The acceptance sequence and shutdown handoff are in
`TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md`.

The first posted file must remain unedited long enough to establish whether a
failure originated in Fusion/post output or in a later machine/setup layer.
Do not change the frozen controller calibration merely to make an unreviewed
posted file run.

## Mode Separation

World, TCPC, and TWP are distinct public modes.

| Mode | Public commands | Program frame | Rotary behavior |
|---|---|---|---|
| World | ordinary `G43 H` optional | active G5X/world | B/C may index |
| TCPC | `G43.4` on, `G49.1` off | active G5X/world | simultaneous B/C allowed |
| TWP | `G68.2`, `G53.1`, `G69` | tilted local XYZ | B/C fixed while active |

TWP must not be nested inside public TCPC. The required TWP state is:

- ordinary positive `G43 Hn` active
- public `G43.4` TCPC off
- the commissioned length model valid
- B/C already at the required indexed orientation

Internally, TWP type 1 uses the same `evaluate_tool_offset_world()` path as
TCPC. It captures the calibrated active-tool reference without setting the
public TCPC bit. There is no TWP-only coefficient set and no TWP calibration
trim.

## Controller Lifecycle

The required indexed-section lifecycle is:

1. Complete any prior local retract while the old TWP is still active.
2. Issue `G69` and confirm return to world mode.
3. Select the required G5X work offset while in world mode.
4. Establish the tool and ordinary positive tool length with `Tn M6` or the
   reviewed manual equivalent, followed by `G43 Hn`.
5. Move to a collision-cleared world position.
6. Position B/C in world mode. `G68.2` will not position the rotary axes.
7. Establish the intended collision-cleared physical entry at the reached B/C
   pose. The MotionX post uses a second reviewed machine retract here; it does
   not infer the live tool length from Fusion.
8. Define the tilted frame with a complete Fusion/Fanuc `G68.2` block.
9. Activate it on the immediately following `G53.1` block.
10. Run fixed-B/C local XYZ motion.
11. Retract to a known clear point in the active local frame.
12. Issue `G69` before any world move, WCS change, rotary move, tool-state
    change, or program end.

`G68.2`, `G53.1`, and `G69` are stationary transactions. A correct transition
must not request joint motion. The post remains responsible for all safe XYZ
and B/C positioning around those transactions.

## `G68.2` Definition

### Production Fusion Form

Fusion output must use:

```ngc
G68.2 X<pivot-x> Y<pivot-y> Z<pivot-z> I<euler-i> J<euler-j> K<euler-k>
G53.1
```

Rules:

- `X`, `Y`, and `Z` are a complete triplet or are all omitted.
- `I`, `J`, and `K` are a complete triplet.
- The Euler convention is rotating `ZXZ`, Fusion constant `EULER_ZXZ_R`:

  ```text
  R = Rz(I) * Rx(J) * Rz(K)
  ```

- The `X/Y/Z` pivot is expressed in the active work coordinate frame.
- The active G5X XYZ translation is supported and is part of the coordinate
  layer captured at entry.
- The I/J/K plane normal must agree with the reached machine B/C tool axis to
  within `0.100 deg`.
- B/C must not move between `G68.2` and `G53.1`; the reached-pose latch is
  checked to `0.001 deg`.
- `G53.1` must be a separate block immediately after `G68.2`.
- Do not combine `I/J/K` with `B/C/R`.

For a nominal pure machine B/C orientation, the accepted Euler branches used
by physical commissioning are useful post-output checks:

```text
B >= 0: I = normalize(C + 90), J = B,    K = -90
B <  0: I = normalize(C - 90), J = -B,   K = +90
```

These identities are validation checks, not a replacement for Fusion's work
plane calculation. The post must use the CAM work-plane matrix and the actual
head-head machine configuration.

### Commissioning Assertion Form

The controller also accepts:

```ngc
G68.2 X... Y... Z... B<reached-b> C<reached-c> R<normal-rotation>
G53.1
```

This is retained for reviewed diagnostics. B/C are reached-pose assertions,
not motion commands. It is not the Fusion post target.

Equivalent wrapped C assertions are accepted, but the exact live continuous C
branch is latched. The post must not unwind or reselect a C branch while TWP is
defined or active.

## Active TWP Command Envelope

The current active-frame motion scope is deliberately narrow.

Supported:

- `G0` local XYZ
- `G1` local XYZ
- reviewed non-faulting `G38.3` local XYZ probing
- `G80`
- `G4` dwell
- `G69` cancellation

Rejected while the frame is defined or active:

- A/B/C/U/V/W motion words
- `G2` or `G3` arcs
- canned cycles and other motion modes
- `G53` motion
- G5X coordinate-system changes
- G52/G92 changes or coordinate-parameter writes
- G5X XY rotation
- cutter compensation other than `G40`
- tool selection, `M6`, or `M61`
- `G43`, `G43.1`, `G43.2`, or `G49`
- `M2`, `M30`, top-level `M99`, or M70/M73 restoration before `G69`

The Fusion post must therefore:

- use indexed 3+2 TWP only, with fixed B/C per section
- linearize every active-TWP arc
- expand every active-TWP canned cycle into permitted linear blocks, or reject
  the operation during posting
- use computer compensation in Fusion and keep controller cutter compensation
  off
- cancel TWP before any work-offset, tool, rotary, or program-end block

Simultaneous 5-axis work is not a TWP section. It uses the separate TCPC
workflow and must never be emitted with TWP active.

## Tool And Offset Contract

Before `G68.2`:

- the selected tool number must match the physical tool
- ordinary positive `G43 Hn` must be active
- tool X/Y and A/B/C/U/V/W offsets must be zero
- the effective Z tool length must be inside the configured calibrated domain
  `100.000..430.000 mm`
- calibration/length-model ID must be `2026082601`
- public TCPC must be off

The current physical TWP release was acquired with T4/H4 at `229.407 mm`.
The length-aware kinematics is shared across the full configured domain, but
tools outside the physically checked T3/T4 bracket remain subject to the
existing TCPC length-model qualification limits.

For this manual-tool machine, normal posted programs should use `Tn M6` so the
operator confirmation remains visible. `M61 Qn` silently declares the tool in
the spindle and should be reserved for a reviewed setup where installation has
already been confirmed. Both must occur with TWP and TCPC off.

## Fusion Post Changes

The Matsuura Fanuc 30i post in `Fusion Post/` is a table-table sequencing
reference because it already emits rotating-`ZXZ` `G68.2` plus `G53.1`. Its
table kinematics and tool-length positioning are not transferable to the
MotionX head-head machine.

Current post and reference:

- `Fusion Post/pocketnc-motionX 3.cps`
- `Fusion Post/FANUC_30i_Matsuura_MAM72_3VS.cps`

Required settings and behavior:

- enable the post property `useTWP` for indexed 3+2 output
- use `EULER_ZXZ_R` directly from `currentSection.workPlane`
- keep `useTCP` independent for simultaneous sections and mixed programs
- use the reviewed embedded MotionX head-head orientation: B about `[0,-1,0]`
  and C about `[0,0,-1]`
- enforce B `-100..+100 deg`, C `-359..+359 deg`, and the current physical TWP
  release `|B| <= 30 deg`
- do not copy the Matsuura table-table geometry or positioning sequence

The MotionX TWP path implements these controller-specific changes:

1. Do not call `disableLengthCompensation()` merely because a TWP section is
   starting. This controller requires ordinary `G43 Hn` to remain active.
2. Do not output `G43.4` to preposition a TWP section. Public TCPC and TWP are
   mutually exclusive here.
3. Cancel the previous plane with `G69` before world positioning or indexing.
4. Perform a reviewed machine/world retract before positioning B/C.
5. Position the actual B/C axes before `G68.2`.
6. Output the complete `G68.2 X/Y/Z/I/J/K` block.
7. Output `G53.1` on the next block and only then mark TWP active in post state.

The stock Fanuc initial-positioning path is not used. The MotionX post
keeps the live LinuxCNC `G43 Hn` active, retracts in world mode, indexes B/C,
repeats the machine retract at the reached pose, activates TWP, and only then
approaches the Fusion section start in local coordinates. It does not use
Fusion gauge, body, or holder length for this entry.

The post maintains independent state variables for:

- ordinary `G43 H` tool-length compensation
- public `G43.4` TCPC
- TWP defined/active state

Do not reuse a single `lengthCompensationActive` or `tcpIsActive` flag to infer
all three states.

The circular and cycle callbacks must fail closed:

- when TWP is active, `onCircular()` must linearize
- active-TWP drilling/canned cycles must expand to permitted `G0/G1`, or the
  post must raise an error
- the post must never emit an unsupported block and rely on LinuxCNC to stop
  at the machine

## Posted Section Example

This is the required block order, not a universal collision-clearance path:

```ngc
(TOOL AND WCS ESTABLISHED IN WORLD MODE)
T4 M6
G54
G43 H4
G40

(REVIEWED WORLD CLEARANCE AND INDEX)
G28 G91 Z0
G90
G0 B30.000 C90.000
G28 G91 Z0
G90

(FUSION ROTATING-ZXZ FRAME DEFINITION)
G68.2 X0.000 Y0.000 Z0.000 I180.000 J30.000 K-90.000
G53.1

(FIXED-BC LOCAL TWP MOTION)
G0 X... Y... Z...
G1 X... Y... Z... F...

(LOCAL CLEARANCE BEFORE STATIONARY CANCEL)
G0 Z...
G69

(WORLD MODE AGAIN)
G0 X... Y... Z...
G49
M30
```

For a subsequent tilted section, keep `G43 Hn` active if the tool is unchanged,
move through reviewed world clearance, index the new B/C pose, and issue a new
`G68.2` / `G53.1` pair.

## TCPC Sections In The Same Post

If the post also supports simultaneous 5-axis TCPC sections, route them
separately:

1. Be in world mode with TWP fully cancelled.
2. Establish ordinary `G43 Hn` at B0/C0.
3. Enable public TCPC with `G43.4` at B0/C0.
4. Run world-frame simultaneous XYZBC motion.
5. Return B/C to the TCPC entry orientation.
6. Cancel public TCPC with `G49.1`.

Never output `G68.2` or `G53.1` while public TCPC is active. Never use plain
`G49` as the TCPC cancel; `G49` is LinuxCNC's ordinary tool-length cancel.

## Recovery Contract

After Stop or Abort while TWP may be active:

- do not jog
- do not restart from line
- do not change WCS, tool, or tool length
- if the state owner is healthy and the machine is stationary, issue `G69`
  and verify world type 0 with all TWP state clear
- if `G69` cannot complete, the task process was lost, or the state component
  is unavailable, close LinuxCNC completely and start a fresh session
- after a clean restart, home all axes and re-establish the tool, ordinary
  `G43 H`, WCS, and safe world start

An E-stop, machine-off transition, or re-home invalidates the stored TWP frame.
The post must not assume modal TWP state survives a controller reset.

## Fusion Post Acceptance Gate

Before a generated post is used for cutting, retain and review one posted file
that proves all of the following:

1. ordinary `G43 H` is active before every `G68.2`
2. no `G43.4` appears in a TWP lifecycle
3. B/C positioning occurs before `G68.2`
4. each `G68.2` contains complete X/Y/Z and I/J/K triplets
5. each `G68.2` is followed immediately by `G53.1`
6. no B/C, arc, canned-cycle, WCS, tool, or offset block occurs before `G69`
7. local clearance is reached before `G69`
8. world clearance precedes every subsequent B/C index
9. `G69` precedes tool change and program end
10. the file previews and loads in the dedicated TWP configuration

The first machine run must be a supervised air path or noncritical cut within
the physically commissioned `|B| <= 30 deg` envelope.

## Current Evidence

Physical acceptance:

- `TWP_SPHERE_FULL_CYCLE_BPLUS5_T4_CLOSEOUT_2026090101.md`
- `TWP_SPHERE_FULL_CYCLE_BMINUS5_T4_CLOSEOUT_2026090102.md`
- `TWP_SPHERE_GRID_LOW_ANGLE_T4_CLOSEOUT_2026090103.md`

Primary implementation:

- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/python/remap.py`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/python/headhead_twp_state.py`
- `src/emc/kinematics/headheadkins.c`
- `src/emc/rs274ngc/interp_convert.cc`

Current actual-program runtime:

- `tests/kinematics/head-head-twp-sphere-grid-runtime`
- `tests/kinematics/head-head-twp-switchkins-continuity`
- `tests/kinematics/head-head-twp-component-loss-restart`
- `tests/kinematics/head-head-twp-sphere-program-static/test.py`

Fusion post release and review tooling:

- `Fusion Post/pocketnc-motionX 3.cps`
- `Fusion Post/validate_motionx_twp_output.py`
- `tests/kinematics/head-head-fusion-post-static/test.py`
- `TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md`
