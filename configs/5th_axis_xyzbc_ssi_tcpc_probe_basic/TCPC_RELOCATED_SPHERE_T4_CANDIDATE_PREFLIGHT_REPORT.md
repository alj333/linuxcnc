# T4 Loaded-Candidate Verification Preflight

Status: `REJECTED PRE-MOTION`. This historical R1 preflight did not authorize
a load or run. Use only a separately frozen R2 candidate.

Historical R1 preflight: `PASS` (offline preparation only; nothing was loaded
and no machine action was taken).

## Frozen Stage

- campaign / mode / attempt: `2026082404 / 25 / 1`
- tool state required by the runner: `T4`, `G43 H4`, `229.407000 mm`, `#3032=0.154742`
- accepted rows / closures: `101 / 28`
- holds: one initial `M0`; no intermediate holds
- overlay: exactly 27 absolute totals for the frozen nine-term lambda-30 fit
- candidate pins are read-guarded before the initial hold, through every live guard, before per-pose motion, and immediately before accepted logging
- G-code coefficient writes: none

## Offline Checks

- base HAL unchanged and hash-locked: `PASS`
- candidate INI is the exact task-capture INI plus one final HALFILE: `PASS`
- overlay matches an independent recomputation from immutable T4 attempt 1: `PASS`
- in-tree `bin/rs274 -g` preview parse: `PASS`
- exact 101-pose order and positive/negative-B pairing: `PASS`
- anchor attempt / center: `1` / `X1024.957789 Y844.074417 Z-302.468115`
- candidate-geometry reachability samples: `30702`
- worst configured linear margin: `187.878641 mm`
- remaining margin after 2 mm center and 3 mm path allowances: `182.878641 mm` (`PASS`)

## Frozen Files

| file | SHA-256 |
| --- | --- |
| `5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` | `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` |
| `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini` | `afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519` |
| `tcpc_relocated_sphere_t4_candidate_lambda30.hal` | `7df9c650d5571172f62132a586256ce6a499773827de540a3bd88bdbdc2a8df1` |
| `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate.ini` | `4340fab84d965e632e34a1c349b94317b9d8842e5c3e94831b85317262184491` |
| `tcpc_relocated_sphere_t4_candidate_verification.ngc` | `5803746d4973cd3ea6322d9f128be016a706b2b136224806eac1b1e5566df522` |
| `tcpc-relocated-sphere-t4-candidate-verification-results.csv` | `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93` |
| `tcpc-relocated-sphere-t4-candidate-verification-state.csv` | `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7` |
| `tcpc-relocated-sphere-t4-candidate-verification-closures.csv` | `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f` |

## T4 Gates

A completed mode-25 run is accepted only if its exact schema, pose, tool/TLO, contact-quality, state, endpoint, and all 28 closure contracts pass, and:

1. Centered RMS and maximum each improve over immutable mode-23 attempt 1 by both 10% and 0.010/0.020 mm respectively.
2. Centered RMS improves by at least 10% separately for the positive- and negative-B high-tilt groups (`|B|>=30`).
3. B0 centered RMS does not worsen by more than 0.010 mm.
4. No row's centered residual norm worsens by more than 0.075 mm.
5. Actual raw-row centered RMS / max are at most 0.130 / 0.300 mm (offline prediction: 0.099990 / 0.237606 mm).
6. Against the frozen offline predicted centered residual vectors, pattern-difference RMS / max are at most 0.050 / 0.120 mm.

These gates test implementation and sign on the same measured grid. They do not authorize extrapolation to omitted C sectors, a general live correction, or a production HAL/INI change.

## Mandatory Rollback

T3 must not run under this candidate configuration. After the T4 test, close LinuxCNC and clean-restart the baseline `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini`; verify the base HAL SHA-256 is `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` before any current-calibration T3 holdout run.

Detailed configured-limit replay: `tcpc-relocated-sphere-t4-candidate-reachability.csv`
