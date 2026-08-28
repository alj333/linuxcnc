# Task and Close-Open Diagnostic Result 2026-08-24

No motion, homing, machine-enable, MDI, Cycle Start, resume, tool, offset, or
TCPC command was issued by the diagnostic procedure. Production INI/HAL hashes
matched the pre-diagnostic incident archive throughout.

## Attempt 1

- Launch: `19:50:31`, diagnostic task-capture INI.
- Probe Basic PID `373740` received native `SIGBUS` at `19:52:31` before a
  diagnostic file-open request.
- The LinuxCNC launcher entered cleanup and sent `SIGKILL` to still-responsive
  milltask PID `373748`; wrapper wait status 137 is cleanup collateral.
- The guarded A request later failed at its initial read-only status poll and
  sent no `program_open` command.
- This full-launcher-cleanup process pattern is distinct from the earlier
  milltask-only losses.

## Production Control

- The unchanged production INI ran with Probe Basic and stock milltask for
  more than three minutes, disabled and unhomed, without the GUI failure.
- It was deliberately shut down to perform the requested diagnostic retry.

## Attempt 2

- Launch: `20:03:27`, diagnostic task-capture INI.
- Probe Basic PID `377603`; real milltask PID `377611`, process start ticks
  `29194033`; one-second health monitor enabled.
- File A hash:
  `e825273cd078a607f9b2d03561cd0b078b1012131c7cd296094f56f43325a70c`.
- File A opened `20:06:49.659` to `20:06:49.711`, returned `RCS_DONE`, and
  produced zero commanded/actual XYZBC delta.
- The disabled, unhomed, idle controller then soaked for more than 20 minutes.
  The same task PID/start ticks survived and every sampled status poll passed.
- File B hash:
  `edbd08b538173f4dac4e9181c193123a94c55aa5a77131a140811e30486997db`.
- File B opened `20:27:30.059` to `20:27:30.110`, returned `RCS_DONE`, and
  produced zero commanded/actual XYZBC delta.
- Neither diagnostic file was executed.

## Conclusion

The disabled close/open transition and 20-minute idle interval did not
reproduce a task loss. Close/open remains a possible internal trigger in a
different interpreter state, but it is not established as the cause and the
caller does not signal milltask. M2 with TCPC active remains relevant only to
the post-anchor incident, not as a general explanation for all losses.

Diagnostic conclusion state: the diagnostic INI was running, disabled and
unhomed, with file B selected at line 0. That snapshot was later superseded by
the reviewed homed/enabled T4 no-contact-envelope load recorded in
`TCPC_CALIBRATION_RESUME_STATE.md`. Physical calibration still requires
operator motion authority.
