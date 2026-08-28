# T4 New-Location Attempt-5 Zero-Row Retirement

Status: `RETIRED - ZERO DATA ROWS`

## Identity

- campaign / mode / attempt: `2026082701 / 39 / 5`
- runner SHA-256: `372babc4289d67b700704e88c4c138a30ef66a403e5026556287d146c548ddb1`
- pre-load archive root: `f93b7cf6cb187d252f305fd337dfc20128b2248da4b78c9589032ca2c60c0fdc`
- frozen handoff: `X2500.972727063 Y696.550278557 Z-279.730797759 B0 C0`
- absolute handoff envelope: `0.050 mm` per linear axis

## Event

The Attempt-5 runner was selected at approximately `23:00:32`. The edge
monitor still recorded the exact frozen handoff and an idle interpreter.

QtPyVCP records the operator MDI command `G1F100X0Y0Z0` at `23:10:19.202`.
The independent motion monitor records ordinary motion type 2 beginning at
`23:10:19.214` and completing at `23:10:20.144`, without any probe signal,
probe gate, or counter change. The resulting commanded position was:

`X2501.941254485 Y696.899347451 Z-280.866128272 B0 C0`

Relative to the frozen handoff, this is
`[+0.968527422, +0.349068894, -1.135330513] mm`. The runner therefore rejected
X before reaching its sole M0. QtPyVCP logged the same resume-X guard at
`23:10:33.794`, `23:10:42.005`, and `23:14:45.639`.

## Zero-Row Proof

All six Attempt-5 output files remained regular one-link ASCII files with
exactly one schema-header line and zero data rows. There was no Attempt-5 M0,
G38 probing move, accepted pose, closure, or contact/gap transaction.

The continuous edge monitor remained at raw/mux/gated counters
`1034/1034/505`. A read-only state snapshot at
`2026-08-27T23:18:07.292738525+07:00` showed LinuxCNC on, AUTO and idle,
unpaused, queue zero, current/motion line zero, velocity and distance-to-go
zero, and in-position at the displaced XYZ. T4 remained selected with all
three observed Z tool offsets `229.407 mm`; TCPC was active and length model
`2026082601` remained configured, valid, and fault-free. Raw, mux, gated,
ignore, abnormal, fault, and motion-probe signals were all false.

## Disposition

Attempt 5 is retired. Do not Resume, restart, append, or reuse its runner or
six output paths. The guard abort happened before data acquisition, so
Attempt 4 remains the sole owner of canonical sequences `1..9`. A continuation
must use a new attempt identity and six fresh headers from a newly verified
handoff position.

This report and its archive were produced from read-only LinuxCNC status,
QtPyVCP log, continuous edge-monitor evidence, and filesystem inspection. No
controller, HAL, program-control, Cycle Start, Resume, MDI, homing, motion, or
standalone `rs274` command was issued during the inspection or archival work.
