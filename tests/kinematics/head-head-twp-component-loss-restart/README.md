# Head-head TWP component-loss restart recovery

This headless simulation proves the required recovery boundary when the
`headheadtwp` userspace state component is lost while synchronized tilted-work-
plane kinematics type 1 is active. It imports the production remap, uses the
commissioned `2026082601` length model, and opts into `G68.2` only inside this
test fixture.

The shell driver starts LinuxCNC twice. In stage one it homes and enables the
simulated XYZBC machine, loads T4 with `G43 H4`, verifies the separate TCPC
mode, leaves TCPC off, reaches fixed `B5 C0`, defines TWP with `G68.2`, and
activates it with `G53.1`. It then identifies and sends `SIGKILL` only to the
Python process that owns the `headheadtwp` HAL component. The process must
disappear. HAL may remove the pins immediately or retain their stale registration
until teardown after this abnormal exit; in either case no owner process may
remain. The retained switchkins request must stay type 1, the frame must remain
one-hot and ready, and every joint and the physical TCP must remain stationary.

LinuxCNC is then allowed to shut down completely. Stage two removes the first
interpreter parameter file and launches a wholly new LinuxCNC process. It
requires a new `headheadtwp` process, ready world kinematics type 0, TCPC off,
all TWP state and transaction fields clear, the commissioned zero-orientation
plane vectors, and zero captured-origin and coordinate-offset layers before and
after enable/homing.

The driver refuses to start over an existing LinuxCNC process or lock file. A
process-group cleanup trap and post-stage checks prevent a failed test from
leaving simulated LinuxCNC processes or `/tmp/linuxcnc.lock` behind.
