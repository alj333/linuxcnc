# Milltask Exit and Close-Open Diagnostic

This diagnostic continuously bounds an otherwise silent task exit and tests
next-file close/open as one hypothesis. It issues no axis, spindle, coolant,
digital-output, tool, offset, TCPC, or TWP command.

Use only after the current invalid controller session has been shut down and a
clean launch of `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini` has
completed. The diagnostic INI is mechanically identical to the production INI
except for diagnostic `DEBUG`/`LOG_LEVEL` values and `[TASK] TASK` naming
`milltask_exit_capture.sh`. The wrapper runs the same `bin/milltask`, enables
core files, and records its child PID and final wait status under
`diagnostics/task_exit_captures/`.

The first phase needs no homing or machine enable:

1. Keep LinuxCNC in E-stop and disabled after the clean diagnostic launch.
2. Start `monitor_milltask_health.py` for the recorded child `milltask_pid`.
   Confirm the PID exists and two LinuxCNC status polls succeed. CPU time and
   context-switch counts may remain unchanged while an idle task is blocked.
3. Record commanded and actual XYZBC. Load
   `task_close_open_a_load_only.ngc` without starting it, then repeat the PID,
   status-poll, and position checks.
4. Leave the disabled controller idle for at least 20 minutes while the
   one-second monitor continues. Issue no controller commands during the soak.
5. Immediately before the second load, confirm the same PID remains live and
   status polls still succeed. Load `task_close_open_b_load_only.ngc` without
   starting it, then repeat all checks. This tests the close/open boundary even
   though file A has never run.
6. Inspect the monitor CSV, wrapper log, launcher stdout/stderr, and any
   captured core or backtrace. A loss during a load supports the close/open
   hypothesis; a loss during the idle soak falsifies it for that incident.

Only if the disabled load-only phase survives, the secondary test is:

1. The operator homes and re-establishes the reviewed T4/H4, B0/C0,
   TCPC-on, TWP-clear state.
2. Load `tcpc_lazy_close_stage1.ngc`. Confirm load-only caused no XYZBC change.
3. The operator starts it to its mandatory M0, then resumes once. It contains
   no motion command and ends at M2 with TCPC still active.
4. Confirm the task PID and heartbeat remain live, record XYZBC, then load
   `tcpc_lazy_close_stage2_load_only.ngc` without starting it.
5. Recheck XYZBC, task liveness, wrapper log, launcher logs, and captured core.

Do not use the production calibration runners until this load-only transition
survives and the normal production config is relaunched and revalidated.

## Result: 2026-08-24

Attempt 2 passed the complete disabled phase. File A returned `RCS_DONE` at
`20:06:49`; after more than 20 minutes of uninterrupted one-second task and
status monitoring, file B returned `RCS_DONE` at `20:27:30`. Both load-only
checks preserved the same task PID/start time and produced zero commanded and
actual XYZBC deltas. Neither file was executed.

Attempt 1 ended before file A was requested because Probe Basic received
native `SIGBUS`. LinuxCNC launcher cleanup then killed the still-healthy task,
so wrapper status 137 in that attempt is cleanup collateral, not a milltask
failure. Keep this distinct from the three earlier milltask-only incidents.
