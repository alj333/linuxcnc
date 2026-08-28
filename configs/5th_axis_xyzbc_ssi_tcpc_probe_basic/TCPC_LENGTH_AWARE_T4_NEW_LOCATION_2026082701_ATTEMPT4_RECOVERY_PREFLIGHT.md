# T4 New-Location Attempt-4 Recovery Preflight

Status: `CONSTRUCTION PASS ONLY - EXECUTION HOLD`

Recorded: `2026-08-27 +07`

## Frozen Artifacts

- runner: `66366ff90b038b738e47ada847902b739475fbad787b4652cb978f51d2b0e77b`
- results header: `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93`
- state header: `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7`
- model-state header: `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd`
- closures header: `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f`
- contact-trace header: `df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8`
- gap-trace header: `e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2`

All six outputs are new regular files, have distinct inodes, contain exactly
one schema header and zero data rows, and use only the Attempt-4 prefix.

## Construction Audit

Read-only ordinary-file checks establish:

- identity selectors are exactly mode `38`, attempt `4`, row count `92`
- acquired topology and bridges remain `1..9,17,20..101` and `3709/3717/3720`
- completion guards remain `#726=101`, summaries/model `92`, closures `30`, traces `736/736`
- every released/logging output path is Attempt-4 isolated
- the normalized source delta is limited to reviewed identity/output text, operator-contract text, four `G4 P10.0` lines, and the A4-only final ignore-window guard
- the four dwells follow the W/U/-V/+V successful retracts, execute twice per pose, and do not occur in no-touch branches or transit code
- immediately after the final `M66 E0 L0`, the non-delaying guard rejects an active `tcpc_probe_gate_ignore.out` before the existing gate/input/counter checks and every `G38.3`
- construction wrote no archived or workspace Attempt-3 path

No controller, HAL, LinuxCNC, or `rs274` command was invoked. No reachability
replay was run during construction. The read-only Attempt-4 validator passed
its static, fresh-output preflight, and mutation-test modes against the frozen
runner and six one-line outputs.

## Pending Gates

This report is not an execution release. Exact Attempt-4 reachability,
probe-filter disposition, post-acquisition validation, and all live
machine/physical gates remain pending. The six frozen header hashes must be
verified again immediately before any load authorization.
