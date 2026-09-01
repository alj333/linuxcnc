# Current Synchronized TWP Software Acceptance Matrix

Status: current test index, revised 2026-09-01

Controller and Fusion post behavior is defined by:

- [TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_IMPLEMENTATION_AND_FUSION_POST_CONTRACT.md)

The older matrix required public TCPC under TWP and exercised the original
single-command/prototype path. Those cases remain useful historical regression
fixtures, but they are not release evidence for synchronized TWP.

Run LinuxCNC harnesses serially. Each fixture owns RTAPI/HAL state and must
finish cleanup before the next starts.

## Static Program And Coordinate Checks

```bash
cd /home/cnc5/linuxcnc-dev
python3 tests/kinematics/head-head-twp-sphere-program-static/test.py
```

Required result:

```text
TWP sphere stage-1/full-cycle/grid static and coordinate-math validation passed
```

This verifies the production programs' lifecycle order, Euler identities,
coordinate-source rules, pose list, recovery settings, and evidence schemas.

## Fusion Post Checks

```bash
cd /home/cnc5/linuxcnc-dev
python3 tests/kinematics/head-head-fusion-post-static/test.py
python3 "Fusion Post/validate_motionx_twp_output.py" --self-test
```

Required results:

```text
MotionX Fusion post static contract: PASS
MotionX generated-output validator self-test: PASS
```

For a real Fusion-generated file, rerun the validator with the NGC path in
place of `--self-test`, retain that exact output, and complete the manual gate
in `TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md`.

## Switchkins Continuity

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-twp-switchkins-continuity
./test.sh
```

This is the primary stationary-entry/exit test. It covers T3 and T4, nonzero
G54, rotating-`ZXZ` I/J/K, plane-normal rotation, wrapped C, active-tool
continuity, unsupported-command guards, and servo-sample continuity while
public TCPC remains off.

## State-Owner Loss And Restart

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-twp-component-loss-restart
./test.sh
```

This proves that loss of the userspace state owner fails stationary and that a
wholly fresh LinuxCNC launch restores ready world type 0 with TWP state clear.
It intentionally does not authorize in-place recovery.

## Exact B0 Sphere Program

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-twp-sphere-full-runtime
./test.sh
```

This runs the exact production WORLD/TWP/WORLD B0 program with the physical
homing-layer separation, T4/H4, shared length model, motion-gated probe, and
evidence-file backup/restore.

## Complete Signed-B Lifecycles

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-twp-sphere-full-cycle-runtime
./test.sh
./test-bminus5.sh
```

These run the actual B0/B+5/B0 and B0/B-5/B0 programs, including guarded world
clearance, B/C indexing, `G68.2`, `G53.1`, local probing, `G69`, and world
return.

## Low-Angle B/C Grid

```bash
cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-twp-sphere-grid-runtime
./test.sh
```

Required coverage:

- 24/24 poses at B `+/-5`, `+/-15`, `+/-30` and C `0/90/180/270`
- 24/24 TWP entries and exits
- 24/24 local-Z preflights
- no B/C motion while TWP is active
- all 112 gated contacts
- at least 50 mm fixed-sphere rotary clearance
- final B0/C0 world type 0 with TWP and TCPC clear
- byte-identical restoration of all three production evidence CSVs

The accepted reference run produced minimum transition clearance
`70.824641 mm` and simulated WORLD return closure `0.001195 mm`.

## Source Checks

At minimum:

```bash
cd /home/cnc5/linuxcnc-dev
python3 -m py_compile \
  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/python/remap.py \
  configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/python/headhead_twp_state.py \
  tests/kinematics/head-head-twp-sphere-program-static/test.py \
  tests/kinematics/head-head-twp-sphere-grid-runtime/test-ui.py
bash -n tests/kinematics/head-head-twp-sphere-grid-runtime/test.sh
git diff --check
```

## Physical Gate

Software acceptance is necessary but not sufficient. The current physical
release evidence is:

- [TWP_SPHERE_GRID_LOW_ANGLE_T4_CLOSEOUT_2026090103.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_SPHERE_GRID_LOW_ANGLE_T4_CLOSEOUT_2026090103.md)

That result releases controlled CAM cut testing only inside the physically
tested `|B| <= 30 deg` envelope. It does not authorize unattended production,
untested arcs/cycles, changing B/C inside TWP, or physical use beyond the
tested angular envelope.

The current post-specific acceptance handoff is:

- [TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md](/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TWP_FUSION_POST_CUT_TEST_HANDOFF_20260901.md)

Passing the post self-test is not evidence that a particular Fusion-generated
program is safe or accepted. The generated file still requires validation,
manual lifecycle/clearance review, LinuxCNC load testing, and a supervised air
path before material cutting.

## Legacy Runner

`run_head_head_acceptance.sh` still runs the earlier prototype-era suite. Keep
it for regression history, but do not use its pass count as the synchronized
TWP release gate. The tests above and the physical closeout are authoritative.
