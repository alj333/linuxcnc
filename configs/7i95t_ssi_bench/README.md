# 7I95T SSI Bench Notes

## Scope

This directory is a bench-only LinuxCNC config for validating:

- Mesa 7I95T Ethernet communication
- two SSI absolute encoders
- HostMot2 serial absolute decode
- AXIS DRO display from the encoder positions

It is intentionally not a machine config. No drives, motors, or machine mechanics are required.

## Hardware Mapping

- `SSI.00` -> B axis encoder -> `joint.0`
- `SSI.01` -> C axis encoder -> `joint.1`

The original restored `configs/5th_axis` tree should be treated separately. It targets different hardware assumptions and should not be used as the bench base for the 7I95T encoder work.

## Final Working Decode

Both SSI channels use the same serial format string:

```text
crc%6unwarn%1bnerr%1babs%20ige
```

Field meaning:

- `crc%6u` = 6-bit CRC field
- `nwarn%1b` = 1-bit warning flag
- `nerr%1b` = 1-bit error flag
- `abs%20ige` = 20-bit absolute position with:
  - `i` = invert bits before further decode
  - `g` = Gray decode
  - `e` = encoder position field

The important bench result is that these encoders do not decode correctly with `ge` alone. They require invert-before-Gray, so `ige` is the working format.

## HostMot2 Changes In This Branch

The branch adds support for the `i` modifier in the Mesa HostMot2 SSI decoder:

- `src/hal/drivers/mesa-hostmot2/abs_encoder.c`
- `src/hal/drivers/mesa-hostmot2/sserial.c`
- `src/hal/drivers/mesa-hostmot2/sserial.h`

Implementation intent:

- accept `i` in the format parser
- set a decode flag during format parsing
- invert the raw field bits before Gray decode for unsigned and encoder fields

This branch is a local validation branch in the user's fork. It is not intended to be pushed to LinuxCNC upstream until machine use confirms the behavior.

## Proven Bench Settings

These settings were validated on the test bench:

- board IP: `10.10.10.10`
- DPLL timer: `hm2_7i95.0.dpll.01.timer-us = -350`
- SSI clock: `200 kHz`
- timer number: `1`
- counts per rev: `1048576`

The bench HAL is in:

- `configs/7i95t_ssi_bench/7i95t_ssi_bench.hal`

The bench INI is in:

- `configs/7i95t_ssi_bench/7i95t_ssi_bench.ini`

## Bench Runtime Behavior

The AXIS DRO is driven directly from the encoder positions:

- `hm2_7i95.0.ssi.00.abs.position` -> B DRO
- `hm2_7i95.0.ssi.01.abs.position` -> C DRO

This is acceptable only because the config is a bench test with no machine connected.

The config uses large following-error limits and no homing requirement so LinuxCNC can start cleanly while the DRO follows the live encoder values.

## Launch

From the RIP tree:

```bash
cd ~/linuxcnc-dev
source scripts/rip-environment
linuxcnc configs/7i95t_ssi_bench/7i95t_ssi_bench.ini
```

Useful watch command:

```bash
watch -n 0.2 '
halcmd getp hm2_7i95.0.ssi.00.data-invalid
halcmd getp hm2_7i95.0.ssi.00.abs.rawcounts
halcmd getp hm2_7i95.0.ssi.00.abs.position
halcmd getp hm2_7i95.0.ssi.01.data-invalid
halcmd getp hm2_7i95.0.ssi.01.abs.rawcounts
halcmd getp hm2_7i95.0.ssi.01.abs.position
'
```

Expected bench behavior:

- `data-invalid` remains `FALSE`
- both encoders move smoothly in the DRO
- `rawcounts` and `position` change consistently with shaft rotation

## Limits Of This Bench Config

- no step/dir servo integration
- no PID or closed-loop axis control
- no machine homing logic
- no production-safe axis feedback architecture

This config only proves that the Mesa card, SSI transport, and HostMot2 decode path are correct for the tested encoders.

## Recommended Path To Machine Integration

When moving this into a real machine:

1. Keep the machine config separate from the bench config.
2. Confirm the production Mesa firmware exposes the required resources for the target machine.
3. Decide whether the SSI encoders are primary axis feedback or auxiliary position references.
4. If they become primary feedback, wire them into the actual joint feedback path and rework homing accordingly.
5. Validate scaling, sign, and any mechanical ratio at the axis level, not by changing the decode semantics.
6. Confirm the invert-before-Gray logic on the machine hardware before proposing the change upstream.

## Branch Context

The working branch for this effort is:

- `ssi-invert-bench`

The intended remote for collaboration is the user's fork:

- `https://github.com/alj333/linuxcnc`

Local bench notes may also exist in `SESSION_NOTES.md`, but this `README.md` is the tracked reference that should travel with the branch.
