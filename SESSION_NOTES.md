# Session Notes (2026-03-11)

## Working Bench Result
- LinuxCNC RIP tree reset clean, rebuilt, and `sudo make setuid` applied.
- `mesaflash` installed system-wide and available in `PATH`.
- Restored machine-style `configs/5th_axis` was left alone.
- Created isolated bench config for the test card:
  - `configs/7i95t_ssi_bench/7i95t_ssi_bench.ini`
  - `configs/7i95t_ssi_bench/7i95t_ssi_bench.hal`

## SSI Mapping
- `SSI.00` -> B axis
- `SSI.01` -> C axis

## Final Working Decode
- HostMot2 SSI format on both channels:
  - `crc%6unwarn%1bnerr%1babs%20ige`
- Meaning:
  - 6-bit CRC
  - 1-bit warning
  - 1-bit error
  - 20-bit absolute encoder
  - invert bits before Gray decode

## Proven Runtime Settings
- `hm2_7i95.0.dpll.01.timer-us = -350`
- `frequency-khz = 200`
- `timer-number = 1`
- `counts-per-rev = 1048576`

## Bench Behavior
- AXIS DRO is driven directly from:
  - `hm2_7i95.0.ssi.00.abs.position` for B
  - `hm2_7i95.0.ssi.01.abs.position` for C
- Encoders read correctly and smoothly with the `i` modifier enabled.

## Source Tree
- Repo remote:
  - `https://github.com/LinuxCNC/linuxcnc`
- Current commit at time of note:
  - `49509631f4`

## Update (2026-03-14)
- A new Mesa 7I95T bitfile was flashed and verified live with `mesaflash --readhmid`.
- Confirmed live resource mix:
  - `StepGen = 5`
  - `PWM = 1`
  - `SSI = 2`
- Confirmed exposed output layout:
  - five `Step/Dir` pairs
  - one `PWM/Dir` pair
  - two SSI channels
- Updated the bench HAL to match the flashed card:
  - `num_pwmgens=1`
  - `num_stepgens=5`
- Re-ran the bench encoder test with the same working decode:
  - `crc%6unwarn%1bnerr%1babs%20ige`
- Result:
  - LinuxCNC bench config starts cleanly
  - both encoders still read correctly
  - `data-invalid` remains false
  - the B/C DROs still follow the encoders correctly

## Update (2026-03-14, stable 2.9 machine-style copy)
- Created a machine-style SSI integration copy from the old `5th_axis` config:
  - `configs/5th_axis _SSI`
- Important constraint:
  - only the two SSI encoders were connected to the Mesa card during this phase
  - no other machine hardware was connected yet
- Forward-ported the copied config enough to start on the current stable branch.
- Switched the copied config to `trivkins` because this build does not contain
  the user's custom `5axiskins`.
- Disabled old optional or incompatible features in the copied config:
  - `classicladder`
  - `twp.hal`
  - `5axiskins`-specific startup HAL commands
  - `switchkins` startup logic
  - `M428/M429/M430/M431/M432`
  - `M254`
  - `ToolLengthControl.hal`
  - `probe_basic` display
- Added the proven SSI setup to the copied machine HAL:
  - `ssi_chan_0=crc%6unwarn%1bnerr%1babs%20ige`
  - `ssi_chan_1=crc%6unwarn%1bnerr%1babs%20ige`
  - `hm2_7i95.0.dpll.01.timer-us = -350`
- Integrated feedback in the copied machine HAL:
  - `SSI.00` -> B -> `joint.3.motor-pos-fb`
  - `SSI.01` -> C -> `joint.4.motor-pos-fb`
- Changed B/C index homing assumptions in the copied INI:
  - `HOME_USE_INDEX = NO`
- Result:
  - the copied machine-style config now starts
  - the encoders work inside that machine-style config
  - this is an encoder/config integration milestone only, not a full machine
    commissioning milestone

## Update (2026-03-14, Probe Basic test copy)
- Installed the Probe Basic development stack locally under:
  - `/home/cnc5/dev/qtpyvcp`
  - `/home/cnc5/dev/probe_basic`
  - `/home/cnc5/dev/venv`
- Installed the Debian Bookworm QtPyVCP / Probe Basic dependency set.
- Patched the local Probe Basic launchers to source the RIP environment when
  `/home/cnc5/linuxcnc-dev/scripts/rip-environment` exists.
- Created a separate Probe Basic UI test copy of the SSI machine config:
  - `configs/5th_axis_SSI_probe_basic`
- Added Probe Basic-specific files to that copy:
  - `custom_config.yml`
  - `pbsplash.png`
  - `user_buttons/`
  - `user_dro_display/`
  - `user_tabs/`
  - `probe_basic_postgui.hal`
  - `launch_probe_basic.sh`
- Probe Basic test copy uses:
  - `DISPLAY = probe_basic`
  - `POSTGUI_HALFILE = probe_basic_postgui.hal`
  - `DRO_DISPLAY = XYZBC`
- Important limitation:
  - LinuxCNC still has `XYZBCW`, but Probe Basic does not ship a stock `XYZBCW`
    DRO template, so `W` is intentionally omitted from the default Probe Basic
    DRO layout in this test copy.
