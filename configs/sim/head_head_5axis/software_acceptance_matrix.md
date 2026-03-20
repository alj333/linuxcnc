# Head-Head 5-Axis Software Acceptance Matrix

This is the software-hardening checklist for the current head-head branch.

Use it in two phases:

1. on the test PC now, to prove the controller/sim/UI behavior stays stable
2. on the future machine PC, before trusting any real-machine calibration run

The goal is to keep one ordered validation path instead of rediscovering the
same checks later.

One-command runner:

- [run_head_head_acceptance.sh](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/run_head_head_acceptance.sh)

Basic use:

```bash
cd /home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis
./run_head_head_acceptance.sh
```

Notes:

- the runner sources the RIP environment and prefers each harness `test.sh`
  entry point when present
- those harness entry points already clear `sim.var` before launch so tests do
  not leak parameter state into each other
- the runner now inserts a short cooldown between harnesses and retries the
  known LinuxCNC realtime teardown race if a previous session has not fully
  released `homemod` / `headheadkins` yet
- use `--stop-on-fail` to stop at the first failing harness
- use `--logs DIR` to keep a named log set

## Phase 1: Automated Sim Acceptance

Run these from `/home/cnc5/linuxcnc-dev`.

### 1. TWP `G0/G1` basic path

Command:

```bash
cd tests/kinematics/head-head-twp-g0g1
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- `pause 1 ok` through `pause 14 ok`
- `program complete`

Purpose:

- proves active `G68.2` drives ordinary `G0/G1 X/Y/Z`
- proves `G69` returns to world motion cleanly

### 2. TWP requires TCPC

Command:

```bash
cd tests/kinematics/head-head-twp-requires-tcpc
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- expected interpreter error:
  - `TWP mode enable requested while TCPC mode is not enabled`

Purpose:

- proves the controller contract is enforced, not just documented

### 3. TWP rejects rotary changes

Command:

```bash
cd tests/kinematics/head-head-twp-reject-rotary
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- expected runtime error:
  - `Linear move on line 11 fails kinematicsInverse`

Purpose:

- proves active TWP keeps the stored `B/C` orientation fixed

### 4. Tool/TLO protections while TWP is active

Run:

```bash
cd tests/kinematics/head-head-twp-reject-tool-length
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

```bash
cd tests/kinematics/head-head-twp-reject-tool-change
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

```bash
cd tests/kinematics/head-head-twp-reject-tool-number
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- `Cannot change tool length compensation while TWP is active`
- `Cannot change tools while TWP is active`
- `Cannot change current tool number while TWP is active`

Purpose:

- proves tooling state cannot change under active TWP

### 5. Tooling recovery after `G69`

Command:

```bash
cd tests/kinematics/head-head-twp-tooling-after-g69
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- `pause 1 ok` through `pause 7 ok`
- `program complete`

Purpose:

- proves normal tooling behavior returns after `G69`

### 6. Limit reject and recovery

Run:

```bash
cd tests/kinematics/head-head-twp-limit-reject
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

```bash
cd tests/kinematics/head-head-twp-limit-recovery
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- reject test shows a positive-limit error before motion
- recovery test shows:
  - expected limit error
  - clean `G69` / `G49.1` / reposition / `G43.4` / `G68.2` recovery path

Purpose:

- proves the controller behaves predictably near travel limits

### 7. Abort / estop / re-home semantics

Run:

```bash
cd tests/kinematics/head-head-twp-abort-state
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

```bash
cd tests/kinematics/head-head-twp-estop-reset
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

```bash
cd tests/kinematics/head-head-twp-rehome-reset
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- abort preserves active TWP/TCPC until explicit cancel
- estop clears TWP and restores default TCPC-on
- re-home clears TWP and preserves TCPC mode

Purpose:

- proves the controller state model remains stable through common recovery paths

### 8. Queuebuster / remap regression

Command:

```bash
cd tests/remap/head-head-twp-queuebuster
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- `pause 1 ok` through `pause 8 ok`
- `program complete`

Purpose:

- keeps the original remap ordering fix from regressing

### 9. Manual `B/C` entry contract

Command:

```bash
cd tests/kinematics/head-head-twp-manual-bc-entry
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Expected:

- `pause 1 ok` through `pause 11 ok`
- `program complete`

Purpose:

- proves TCPC-on / TWP-off manual `B/C` motion
- proves `G68.2` can capture current `B/C`
- proves `G69` -> manual `B/C` -> re-enter TWP is still valid

## Phase 2: Manual Sim Acceptance

Use these after a larger refactor or UI change:

- [tcp_tcpc_fresh_demo.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/tcp_tcpc_fresh_demo.ngc)
- [twp_g68_2_fresh_demo.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/twp_g68_2_fresh_demo.ngc)
- Probe Basic `5 AXIS CALIBRATION` tab
- reduced STL visual sim

Pass condition:

- no unexpected LinuxCNC popup storms
- vismach still gives believable TCP/TWP visual behavior
- Probe Basic calibration tab still loads and the summary updates live

## Phase 3: Real-Machine Acceptance

Run only after the machine is operational.

Ordered path:

1. [machine_bringup_checklist.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_bringup_checklist.md)
2. [machine_rotary_zeroing_sequence.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_rotary_zeroing_sequence.md)
3. [machine_tcp_twp_verification_sequence.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_twp_verification_sequence.md)

Machine programs:

- [machine_b_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_b_zero_alignment_check.ngc)
- [machine_c_zero_alignment_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_c_zero_alignment_check.ngc)
- [machine_tcp_fixed_tip_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_fixed_tip_probe_check.ngc)
- [machine_tcp_motion_probe_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_motion_probe_check.ngc)
- [machine_twp_granite_square_check.ngc](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_twp_granite_square_check.ngc)

Use the Probe Basic `5 AXIS CALIBRATION` tab to record:

- bring-up stage status
- sphere-map data
- pose-by-pose verification status
- recovery guidance
- trial-change plan

## Gate To Proceed

The software stack is ready for first real-machine calibration only when:

- all automated sim tests above still pass
- Probe Basic head-head config launches cleanly
- the calibration tab loads cleanly
- reduced STL vismach still renders and moves believably
- the machine-facing contract in
  [fanuc_like_twp_tcpc_contract.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/fanuc_like_twp_tcpc_contract.md)
  still matches the implementation
