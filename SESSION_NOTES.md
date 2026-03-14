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
