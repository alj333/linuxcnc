# Head-Head Fanless PC Rebuild Notes

This is the migration note for rebuilding the current head-head sim and Probe
Basic stack on a new fanless PC later.

It captures the current software assumptions on this test machine so the rebuild
is repeatable instead of depending on memory.

## Repo Baseline

Primary repo:

- `/home/cnc5/linuxcnc-dev`

Current working branch during this calibration pass:

- `head-head-kinematics-rnd-pushable`

Important committed checkpoints in this branch:

- `b174eed7fa` `Add head-head TCPC/TWP simulation and calibration workflow`
- `be24909ef5` `Add head-head machine bring-up and calibration guidance`

## Repo-Local Launch Points

Visual sim:

- [head_head_visual_sim.ini](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_visual_sim.ini)

Probe Basic sim:

- [head_head_probe_basic.ini](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_probe_basic.ini)
- [launch_probe_basic.sh](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/launch_probe_basic.sh)

Calibration tab:

- [five_axis_calibration.py](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/user_tabs/five_axis_calibration/five_axis_calibration.py)

## Required Non-Repo Local Dependencies

These are not provided by the LinuxCNC repo itself and must be recreated or
re-pointed on the new PC.

### 1. Python virtualenv for Probe Basic

Current path on this test machine:

- `/home/cnc5/dev/venv`

The current launcher assumes:

- `source /home/cnc5/dev/venv/bin/activate`

### 2. Probe Basic checkout

Current path:

- `/home/cnc5/dev/probe_basic`

The current INI references assets in that tree:

- splash screen
- ATC button set
- DRO set
- macro/subroutine paths

### 3. QtPyVCP checkout

Current path:

- `/home/cnc5/dev/qtpyvcp`

### 4. Local QtPyVCP patch

This machine has a local patch outside the LinuxCNC repo:

- `/home/cnc5/dev/qtpyvcp/src/qtpyvcp/hal/hal_qlib.py`

Reason:

- suppress shutdown/restart noise from:
  - `RuntimeError: Invalid operation on closed HAL component`

This patch is not committed in `/home/cnc5/linuxcnc-dev`.
It must be either:

- reapplied on the new PC, or
- replaced with an upstream fix if the local QtPyVCP tree changes

### 5. Reduced STL directory

Current external path:

- `/home/cnc5/Vismach/reduced`

The current head-head vismach uses that reduced STL set as the live visual
baseline.

If the STL files live somewhere else on the new PC, update the vismach config
or copy the directory accordingly.

### 6. Desktop launcher

Current local launcher:

- `/home/cnc5/Desktop/Head-Head Probe Basic.desktop`

Useful to recreate, but not required for function.

## Rebuild Order

1. Clone or copy the LinuxCNC repo to the new PC.
2. Check out `head-head-kinematics-rnd-pushable`.
3. Build or restore the RIP environment for the repo.
4. Recreate the Python virtualenv used for Probe Basic.
5. Restore or clone the `probe_basic` and `qtpyvcp` trees.
6. Reapply the local `hal_qlib.py` shutdown patch if still needed.
7. Restore the reduced STL directory.
8. Launch the visual sim first.
9. Launch Probe Basic second.
10. Run the acceptance matrix before trusting the stack.

## First Validation On The New PC

### Visual sim

Run:

```bash
cd /home/cnc5/linuxcnc-dev
source scripts/rip-environment
linuxcnc configs/sim/head_head_5axis/head_head_visual_sim.ini
```

Check:

- LinuxCNC starts cleanly
- reduced STL vismach loads
- TCPC/TWP sample programs can be loaded

### Probe Basic

Run:

```bash
cd /home/cnc5/linuxcnc-dev
configs/sim/head_head_5axis/launch_probe_basic.sh
```

Check:

- Probe Basic opens full-screen
- `5 AXIS CALIBRATION` tab loads
- ATC tab is visible
- no fatal QtPyVCP HAL shutdown error on close/restart

## Acceptance Sequence After Rebuild

Use:

- [software_acceptance_matrix.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/software_acceptance_matrix.md)

Minimum gate before real-machine use:

- automated sim tests pass
- visual sim looks correct
- Probe Basic calibration tab works
- generated summary still updates
- reduced STL vismach still behaves believably

## Files To Ignore Or Recreate Locally

Do not treat these as migration-critical repo content:

- `.vcp_persistent_data.pickle`
- `linuxcnc.varold`
- `five_axis_calibration_draft.json`
- `head_head_vismach.py.pre_stl_backup`

These are local runtime or backup artifacts, not source of truth.
