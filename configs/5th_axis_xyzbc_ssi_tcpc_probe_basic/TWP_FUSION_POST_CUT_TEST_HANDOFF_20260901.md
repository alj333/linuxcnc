# TWP Fusion Post Cut-Test Handoff 20260901

Status: `POST RELEASE CANDIDATE COMMITTED - PHYSICAL CUT TEST PENDING`

Controller branch: `head-head-kinematics-rnd-pushable`

Shared calibration revision: `2026082601` (frozen)

## Completed Basis

The synchronized TWP controller path has completed supervised sphere testing
with T4/H4 over B `+/-5`, `+/-15`, and `+/-30 deg` at C
`0/90/180/270 deg`. The 24-pose grid completed 24 TWP entries/exits, 24 local
preflights, and 112 motion-gated contacts. It is accepted for supervised CAM
cut testing inside `|B| <= 30 deg`.

TCPC and TWP use the same length-aware kinematics and calibration revision.
No TWP-specific trim was fitted. The remaining pose-dependent error agrees
with the known shared machine/rotary geometry and is not a reason to alter the
frozen coefficients before the cut test.

## Fusion Post Release Candidate

The MotionX Fusion post was committed and pushed on 2026-09-01:

- repository: `https://github.com/alj333/linuxcnc.git`
- branch: `head-head-kinematics-rnd-pushable`
- commit: `5679acd836b6022a0884ca1f88efd282f56beb48`
- file: `Fusion Post/pocketnc-motionX 3.cps`
- file SHA-256:
  `517429a2809c43be982ed36cdd3cae9e12d32f89bed97ab4a4fd5b8b0c066420`

The post supports three separate paths:

- ordinary three-axis with `G43 Hn`
- simultaneous TCPC with `G43 Hn`, `G43.4`, and `G49.1`
- indexed TWP with world-mode B/C positioning, `G68.2`, separate `G53.1`,
  fixed-B/C local motion, local retract, and `G69`

LinuxCNC's live `G43 Hn` offset is the only tool-length authority. Fusion
gauge, body, and holder length are not used for TWP entry positioning. Public
TCPC is not used to preposition a TWP section.

The `useTWP` post property defaults to `false`. It must be explicitly enabled
for indexed 3+2 sections. `useTCP` remains independent for simultaneous
sections. TWP posting enforces the physically commissioned `|B| <= 30 deg`
limit and requires a machine-coordinate safe-retract method (`G28` or `G53`).

## Verification Completed

The release candidate passed:

- MotionX Fusion post static contract test
- generated-output validator self-test
- TWP sphere-program static and coordinate-math validation
- ECMAScript parse before the final whitespace-only cleanup
- staged diff whitespace/error check

No Fusion 360 engine is installed on this Linux host. Therefore no real
Fusion-generated NGC file has yet been retained, reviewed, loaded, air-run, or
cut on material. Those are tomorrow's acceptance steps, not completed
evidence.

## Next Controlled Test

1. Import the exact post file and confirm its SHA-256 or source commit.
2. Post a small reviewed program within `|B| <= 30 deg`; enable `useTWP` only
   for indexed TWP operations and select `G28` or `G53` safe retracts.
3. Run `Fusion Post/validate_motionx_twp_output.py` against the generated NGC.
4. Manually verify every TWP lifecycle against
   `TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md`.
5. Retain the posted NGC before editing it and load-test it in the dedicated
   TWP-enabled configuration. Loading is not Cycle Start authorization.
6. After a cold start, home normally and verify the physical tool, active
   `G43 H`, work offset, length-model ID `2026082601`, fault code `0`, and
   collision-clearance path.
7. Run a supervised air path or single-block check at restricted overrides
   before the first noncritical material cut.

The generated file must prove ordinary `G43 H` before `G68.2`, B/C indexing
before `G68.2`, immediate separate `G53.1`, fixed B/C while TWP is active,
local clearance before `G69`, and world clearance before the next index. No
public `G43.4` may occur inside a TWP lifecycle.

Retain the Fusion setup description, post-property values, generated NGC,
validator output, LinuxCNC load result, and operator disposition as the first
post acceptance evidence. Any failure should be classified as post output,
transition/lifecycle, setup/clearance, or cutting result before changing
controller calibration.

## Release Limits

- TWP remains a supervised commissioning feature, not an unattended or
  general production release.
- Physical TWP evidence ends at `|B| = 30 deg`.
- The default cut-test INI remains TWP-locked; use only the reviewed dedicated
  TWP-enabled configuration until a separate promotion is approved.
- Active-TWP rotary motion, controller arcs, unsupported canned cycles, tool
  or offset changes, and work-offset changes remain prohibited.
- Tools outside the physically checked T3/T4 length bracket remain governed
  by the existing length-model qualification limits.
- Linear-axis mapping and machine-volume correction remain a separate future
  calibration campaign.

## Shutdown State

The operator reported the CNC homed and then closed LinuxCNC for the night.
At `2026-09-01T18:19:21+07:00`, no LinuxCNC, Probe Basic, milltask, RTAPI, or
HAL process and no LinuxCNC lock file remained. Hardware power-down is
operator-owned and was not inferred from the software check.

At the next launch assume no homing, tool, TLO, G5X, TCPC, TWP, or probe state
is retained. LinuxCNC must be started cleanly and the complete setup
re-established before any test program is authorized to run.
