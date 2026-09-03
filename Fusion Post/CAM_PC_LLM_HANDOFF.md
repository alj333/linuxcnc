# MotionX Fusion Post CAM-PC LLM Handoff

Status: `FUSION POST ERRORS REPORTED - EXACT DIAGNOSTICS PENDING`

Date: 2026-09-03

Repository: `https://github.com/alj333/linuxcnc.git`

Branch: `head-head-kinematics-rnd-pushable`

## Immediate Objective

Run the MotionX post in the actual Fusion 360 post engine, capture the complete
error, and make the smallest source change needed to generate reviewable
three-axis, simultaneous-TCPC, and indexed-TWP programs. Do not change the
LinuxCNC controller contract or calibration merely to suppress a Fusion error.

The editable post is `pocketnc-motionX 3.cps`. Its pre-debug baseline was
introduced by commit `5679acd836b6022a0884ca1f88efd282f56beb48`; the baseline
file SHA-256 is
`517429a2809c43be982ed36cdd3cae9e12d32f89bed97ab4a4fd5b8b0c066420`.
The operator reported on 2026-09-03 that Fusion generates errors, but the exact
message, callback, line number, Fusion build, setup, and post properties were
not available on the Linux machine. Linux-only static checks cannot reproduce
Fusion host API errors.

## First Actions On The CAM PC

1. Pull this branch and confirm a clean worktree before editing.
2. Confirm Fusion 360 version/build and the post kernel/revision shown in the
   post log.
3. Reproduce once with the unedited pulled post.
4. Preserve the complete Fusion post log and exact error text, including the
   `.cps` line number and callback/function name.
5. Record the setup type, operation strategy, tool orientation, WCS, tool
   number, H/length-offset number, and these post properties:
   `useTCP`, `useTWP`, `safePositionMethod`, and `goHomeBetweenOperations`.
6. Preserve any partial NGC output. Do not hand-edit it before diagnosis.
7. Classify the failure before changing code:
   - parse/syntax failure;
   - missing or changed Fusion API;
   - an intentional `validate()` or `error()` contract rejection;
   - machine-angle/work-plane solution failure;
   - ordinary three-axis regression;
   - TCPC state/positioning failure;
   - TWP state/positioning failure.

If repository evidence is retained, create a dated directory below
`Fusion Post/cam_pc_evidence/` containing the post log, unedited generated or
partial NGC, post-property record, and a short reproduction note. Do not commit
customer geometry or a Fusion design unless the owner explicitly approves it.

## Relevant Files

- `pocketnc-motionX 3.cps`: editable MotionX LinuxCNC post.
- `README.md`: current release state and offline validation entry point.
- `validate_motionx_twp_output.py`: fail-closed checker for generated NGC.
- `FANUC_30i_Matsuura_MAM72_3VS.cps`: modern Fusion/Fanuc API and TWP state
  reference only. It controls a table-table machine; do not copy its rotary
  geometry, clamps, positioning, or tool-length calculations into MotionX.
- `../configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/`
  `TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md`: authoritative controller
  contract.
- `../tests/kinematics/head-head-fusion-post-static/test.py`: source-contract
  regression check.

## Machine Geometry

MotionX is a head-head XYZBC machine:

- B is the tilt axis, embedded as head rotation about `[0, -1, 0]`.
- C is the head rotary axis, embedded about `[0, 0, -1]`.
- Both rotary axes are head axes (`table:false`).
- Machine B range is `-100..+100 deg`.
- Machine C branch is `-359..+359 deg` and is noncyclic in this post.
- Physically commissioned TWP output is restricted to `|B| <= 30 deg`.
- TWP uses rotating `ZXZ` Euler angles (`EULER_ZXZ_R`).

Do not replace this with the Matsuura table-table model. Confirm the Fusion
setup/machine definition is compatible with this embedded head-head model when
diagnosing angle-solution errors.

## Tool-Length Authority

LinuxCNC's tool table and the active ordinary `G43 Hn` value are authoritative.
The H number comes from Fusion's positive `tool.lengthOffset`. The post must not
use Fusion gauge length, body length, holder length, or stick-out to calculate
TWP entry coordinates. The controller validates the live effective tool length
when TCPC or TWP is engaged.

The machine has no automatic tool changer. `Tn M6` invokes the accepted manual
tool-change popup. Do not add carousel or table-table tool-change behavior from
the Fanuc reference.

## Required Mode Contracts

### Ordinary Three-Axis

- `useTCP=false`, `useTWP=false`.
- Select the tool and issue ordinary `G43 Hn`.
- Do not emit `G43.4`, `G68.2`, `G53.1`, or `G69`.

### Simultaneous TCPC

- The operation is simultaneous multi-axis and `useTCP=true`.
- Establish ordinary positive `G43 Hn` first.
- Return B/C to machine zero before `G43.4`.
- Use public `G43.4` only for the simultaneous section.
- Return B/C to machine zero, then cancel with `G49.1`.
- Ordinary `G49` may follow only after TCPC is off.

### Indexed TWP

- The operation is fixed-axis indexed and `useTWP=true`.
- Public `G43.4` must remain off.
- Establish ordinary positive `G43 Hn`.
- Retract in world/machine coordinates.
- Position both B and C in world mode.
- Establish a second reviewed world/machine Z retract at the reached pose.
- Emit a complete `G68.2 X Y Z I J K` block.
- Emit `G53.1` alone on the immediately following block.
- While TWP is active, hold B/C fixed and output local XYZ motion only.
- Retract local Z before `G69`.
- Cancel TWP with `G69` before any world move, WCS change, rotary move, tool
  state change, or program end.

`G68.2`, `G53.1`, and `G69` are stationary controller transactions. `G68.2`
does not command B/C. Public TCPC is not a TWP prepositioning mechanism.

## Current Deliberate Restrictions

Do not remove these merely to make a test post:

- TWP above `|B| = 30 deg` is rejected.
- `Clearance Height` is rejected for TWP; use `G28` or `G53` safe retracts.
- Controller cutter compensation is rejected in TWP; use Fusion computer
  compensation.
- Rotary words and simultaneous five-axis callbacks are rejected while TWP is
  defined or active.
- Manual NC cannot inject raw `G68.2`, `G53.1`, or `G69`.
- Unsupported active-TWP arcs are linearized and supported drilling cycles are
  expanded; other cycles are rejected.
- Tool, coolant, spindle, WCS, and machine-state changes are not allowed inside
  the active TWP lifecycle.

An error containing one of these contract messages may indicate an invalid CAM
setup or unsupported operation, not a broken post. Record the triggering
operation before deciding whether code should change.

## Primary Source Hotspots

Use the exact Fusion stack/line number first. The TWP additions are concentrated
in these functions:

- `onOpen`: embedded head-head machine configuration.
- `validateTWPEntry`: fail-closed entry conditions.
- `positionTWPRotaries`: world B/C output.
- `activateTWP`: retract, index, Euler/pivot output, and local entry.
- `cancelTWP`: local clearance and `G69`.
- `getWorkPlaneMachineABC`: Fusion plane-to-machine-angle solution.
- `onSection` and `onSectionEnd`: mode selection and lifecycle.
- `writeRetract`: G28/G53 output.

Host API compatibility candidates to check only when implicated by the actual
error include `currentSection.workPlane.getEuler2(EULER_ZXZ_R)`,
`currentSection.workOrigin`, `machineConfiguration.isHeadConfiguration()`,
`Vector.isNonZero()`, and the availability/argument contract of `validate()`.
This list is diagnostic guidance, not evidence that any listed API is faulty.
Use the bundled current Fanuc post to compare API usage, then preserve MotionX
geometry and controller sequencing.

## Minimum Fusion Test Matrix

Generate four small programs with one simple tool and a positive H number:

1. Three-axis: one B0/C0 contour, both mode properties off.
2. TWP: one fixed indexed section at approximately B+5/C0 with `useTWP=true`.
3. TCPC: one simultaneous section with `useTCP=true`.
4. Mixed: three-axis, indexed TWP, then simultaneous TCPC, proving complete
   closeout between modes.

Add B-5/C90 and B+15/C180 indexed cases after the first TWP case posts. Keep
every initial test within the commissioned B envelope. Posting success alone
is not physical authorization.

## Offline Checks After Every Edit

From the repository root:

```bash
python3 tests/kinematics/head-head-fusion-post-static/test.py
python3 "Fusion Post/validate_motionx_twp_output.py" --self-test
python3 "Fusion Post/validate_motionx_twp_output.py" path/to/generated.ngc
git diff --check
```

The source-contract test is intentionally not a Fusion runtime test. Do not
weaken its assertions or the NGC validator to make an invalid output pass.
Update a test only when the controller contract genuinely changes and document
that change explicitly.

## Completion Evidence

Before returning the work to the CNC PC, commit and push:

- the corrected `.cps`;
- exact Fusion version and reproduction details;
- the original error text and disposition;
- unedited minimal three-axis, TWP, TCPC, and mixed NGC samples;
- passing offline-validator output;
- updated `Fusion Post/README.md` with the new post SHA-256.

State clearly which paths Fusion actually executed. Do not describe the post
as physically accepted until the generated NGC has separately passed CNC-side
review, LinuxCNC load, supervised air motion, and a controlled material cut.
