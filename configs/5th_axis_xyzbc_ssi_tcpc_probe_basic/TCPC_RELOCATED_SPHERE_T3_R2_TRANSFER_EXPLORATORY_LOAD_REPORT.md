# T3 R2-Transfer Exploratory Load Report

- timestamp: `2026-08-26T10:04:30+07:00`
- status: `LOAD-ONLY PASS`
- disposition: `R2 NOT ACCEPTED`
- selected INI: `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t3_exploratory_a1.ini`
- selected runner: `tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc`
- runner SHA-256: `90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5`
- milltask PID/start: `524892 / 2026-08-26T10:03:10+07:00`
- task/interpreter: disabled, idle, line 0
- homed joints: `0 / 5`
- live tool/TLO: `T0 / 0.000000 mm`
- commanded load delta: `X0 Y0 Z0 B0 C0`
- actual load delta: `X0 Y0 Z0 B0 C0`
- raw/mux/gated levels: `false / false / false`
- raw/mux/gated edge counters: `0 / 0 / 0`
- outputs: five exact header-only files
- controller errors after load: none

The live correction pins match the baseline values and
`headheadkins.sim-bharm-enable` is true. The R2 overlay is absent. Loading did
not enable, home, jog, issue MDI, Cycle Start, Resume, write an output row, or
move an axis.

The controller is intentionally not ready for Cycle Start yet. The operator
must release/reset the machine state, Home All, install and select T3/H3,
establish the exact `128.606729 mm` live tool length and G43.4/TCPC state,
position the probe 3-5 mm above the sphere at B0/C0, and confirm all physical
T3 body/holder/cable/post clearances. The first operator Cycle Start may advance
only to the one pre-motion M0 for a second state and clearance check.
