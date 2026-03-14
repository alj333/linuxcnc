# 5th Axis SSI Integration Notes

## Scope

This directory is the forward-ported SSI integration copy of the original
`5th_axis` machine config.

It is intentionally separate from:

- `configs/5th_axis` = original restored config reference
- `configs/7i95t_ssi_bench` = isolated SSI bench validation config

## Current Status

This copy now starts on the stable `2.9` branch with the current Mesa 7I95T
firmware and reads both SSI encoders correctly.

Proven in this state:

- LinuxCNC starts
- Mesa 7I95T registers
- live firmware resource mix matches the HAL
- `SSI.00` reads as B
- `SSI.01` reads as C
- the working decode is still:

```text
crc%6unwarn%1bnerr%1babs%20ige
```

Not yet proven in this state:

- step/dir drive wiring
- machine I/O beyond the encoders
- real axis motion
- closed-loop behavior under machine load
- homing behavior on the real machine

At the time this note was written, only the two SSI encoders were connected to
the Mesa card.

## Firmware Assumption

This config assumes the live 7I95T firmware has:

- `5 StepGen`
- `1 PWM`
- `2 SSI`

The HAL uses:

- `num_stepgens=5`
- `num_pwmgens=1`
- `ssi_chan_0=crc%6unwarn%1bnerr%1babs%20ige`
- `ssi_chan_1=crc%6unwarn%1bnerr%1babs%20ige`

## Encoder Mapping

- `SSI.00` -> B axis -> `joint.3`
- `SSI.01` -> C axis -> `joint.4`

Current SSI setup in the HAL:

- DPLL timer: `-350`
- SSI clock: `200 kHz`
- timer number: `1`
- counts per rev: `1048576`

Current scale assumption:

- `-2912.711111111111` counts per degree for both B and C

That assumes a direct 20-bit single-turn encoder scaled in degrees.
If the production mechanics introduce gearing, this must be recalculated.

## Forward-Port Decisions

This config was copied from an older LinuxCNC environment, so several optional
or legacy features were disabled to get a clean startup on the current stable
branch.

Disabled in this copy:

- `classicladder` startup
- `twp.hal`
- `5axiskins`-specific startup pins
- `switchkins` startup control
- `M428/M429/M430/M431/M432` remaps
- `M254` dynamic work offset remap
- `ToolLengthControl.hal`
- `probe_basic` display

Current replacements:

- display = `probe_basic` in the Probe Basic test copy
- display = `axis` in the AXIS SSI baseline copy
- kinematics = `trivkins coordinates=XYZBCW`

These changes were made to get a stable machine-core startup on this branch.
They should be revisited only after hardware commissioning reaches the point
where those features are required again.

## Probe Basic Test Copy

This directory is the Probe Basic UI test variant of the SSI integration copy.

Additional Probe Basic-specific changes in this directory:

- `DISPLAY = probe_basic`
- `POSTGUI_HALFILE = probe_basic_postgui.hal`
- local `custom_config.yml`
- local `pbsplash.png`
- copied `user_buttons/`, `user_dro_display/`, and `user_tabs/`
- `launch_probe_basic.sh` to activate the venv and RIP tree before launch

Important limitation:

- Probe Basic does not ship a stock `XYZBCW` DRO layout
- this config uses `DRO_DISPLAY = XYZBC`
- the `W` axis is still present in LinuxCNC, but is not shown in the default PB DRO set

Launch:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_SSI_probe_basic/launch_probe_basic.sh
```

## Feedback Path Changes

B and C feedback were changed from stepgen position feedback to SSI absolute
feedback:

- B feedback comes from `hm2_7i95.0.ssi.00.abs.position`
- C feedback comes from `hm2_7i95.0.ssi.01.abs.position`

X, Y, Z, and W were left on their existing paths in this integration pass.

## Homing Changes

For B and C only, `HOME_USE_INDEX` was changed to `NO`.

Reason:

- the old config used encoder-index style assumptions
- the current B/C feedback path is now absolute SSI

This does not mean homing is finalized. It only means index-based homing was
removed from the copied config because it no longer matched the feedback path.

## Next Test Builds

When more hardware is connected, the next staged tests should be:

1. confirm startup remains clean with the real machine wiring
2. confirm B/C DRO direction matches physical axis direction
3. jog B slowly and verify sign and scale
4. jog C slowly and verify sign and scale
5. confirm step/dir outputs on X/Y/Z/B/C
6. confirm the spindle PWM/dir path
7. confirm home switch and limit input mapping

Only after those pass should old optional features be added back.

## Next Production Build Tasks

Production integration still needs:

1. final B/C scale validation against real machine motion
2. final B/C sign validation
3. homing strategy for B/C with absolute feedback
4. verification of stepgen output assignment and timing
5. restoration of optional features only if they are still needed
6. cleanup of the copied config directory structure and naming

## Notes On Directory State

This directory still contains old backup files, generated var files, and
historical support files from the copied machine config.

Those are not part of the proven SSI integration baseline.

For commits, prefer to track only:

- `5th_axis.ini`
- `5th_axis.hal`
- this `README.md`

and any other file only when it is actively validated.
