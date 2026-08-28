# T4 New-Location Attempt-3 Zero-Row Failure

Status: `RETIRED - SEQUENCE-1 FALSE U TOUCH`

Recorded: `2026-08-27 20:34 +07`

## Stop

Attempt 3 (`2026082701 / mode 37 / attempt 3`) stopped itself at
`20:24:07 +07` during sequence 1, B0/C0, acquisition try 1, pass 1. The
controller reported `Sphere pose quality failed; retain partial and restart
with a new attempt`. LinuxCNC did not crash.

No result, state, model-state, or closure row was accepted. Those four files
remain exact header-only schemas. The contact and gap files each contain four
data rows for the rejected pass-1 acquisition only.

## Failed Criterion

Contact travel was:

- W: `3.882667 mm`
- sign-aware upper U: `0.039396 mm`
- -V: `3.570167 mm`
- +V: `4.271833 mm`

The runner requires every contact to travel at least `1.000000 mm`. The U
contact therefore set pass-1 travel rejection reason 1. With the frozen
one-whole-pose acquisition policy, no retry was allowed and the program
issued the quality abort before pass 2 or summary logging.

## Pulse Evidence

The initial baseline was quiet and W had one raw/mux/gated edge. Between W
and U, three matched raw/mux pulses occurred with the G38 gate closed and no
gated increment. U then produced one gated edge after only `0.039396 mm`.
During its post-contact release interval, another two matched raw/mux pulses
occurred while the gate was closed; neither reached the motion input. The -V
and +V contacts then each recorded one normal gated edge with no repeat.

This is a probe pulse episode, not evidence of a TCPC geometry error. The
trace cannot distinguish electrical/receiver instability from mechanical
stylus or probe-body instability, but the closed-gate activity and near-zero
U travel exclude the point from calibration.

## Frozen Files

- runner SHA-256:
  `bf76ab273c76a32046e6f2066f6b865ea8e0a448266cff0399186e262c5a061a`
- results:
  `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93`
- state:
  `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7`
- model-state:
  `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd`
- closures:
  `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f`
- contact trace:
  `487d08a5dd7a1d36f45c15df11d2cc0cdc004619c46803e17d7c8ee6d0a7e4e6`
- gap trace:
  `164f7c33e228eaa90552b3ac3b410d749bf78985f9b355c0d39170df21ecf201`

## Controller State

After the controlled abort, LinuxCNC was enabled, homed, idle, queue-zero,
in position and probe-clear with Attempt 3 still selected. Commanded XYZBC
was `2501.941317473,696.899347649,-279.748794997,0,0`. The program returned
to its derived top-clear point. Counters were `835/835/337`.

Do not Resume, restart, append to, or reuse Attempt 3. Preserve all eight
files. Reset or reseat and qualify T4 before returning to the frozen sphere-top
start. Because Attempt 3 accepted zero rows, a fresh attempt must repeat its
entire `1..9,17,20..101` acquisition topology with a new attempt ID and fresh
isolated outputs.
