# T4 R2 Loaded-Candidate Verification Preflight

Status: `PASS` (offline preparation only; nothing was loaded and no machine action was taken).

## Frozen Stage

- campaign / mode / attempt: `2026082404 / 26 / 1`
- tool state required by the runner: `T4`, `G43 H4`, `229.407000 mm`, `#3032=0.154742`
- accepted rows / closures: `101 / 28`
- holds: one initial `M0`; no intermediate holds
- overlay: exactly 30 absolute totals for the frozen ten-term lambda-10 R2 fit
- candidate pins are read-guarded before the initial hold, through every live guard, before per-pose motion, and immediately before accepted logging
- G-code coefficient writes: none

## Offline Checks

- base HAL unchanged and hash-locked: `PASS`
- candidate INI is the exact task-capture INI plus one final HALFILE: `PASS`
- overlay matches an independent recomputation from immutable T4 attempt 1: `PASS`
- runner is the archived runnable R1 program with only audited R2 identity substitutions: `PASS`
- in-tree `bin/rs274 -g` preview parse: `PASS`
- exact 101-pose order and positive/negative-B pairing: `PASS`
- anchor attempt / center: `1` / `X1024.957789 Y844.074417 Z-302.468115`
- candidate-geometry reachability samples: `30702`
- worst configured linear margin: `187.861514 mm`
- remaining margin after 2 mm center and 3 mm path allowances: `182.861514 mm` (`PASS`)
- maximum correction on the replayed verification trajectory: `0.670166 mm`
- maximum correction on the authorized diagnostic domain B[-90,+90] over a complete C cycle, using a 0.25-degree grid plus local quadratic interpolation: `0.671900 mm` at `B-90.0000 C272.8566` (`PASS` against 0.750 mm)
- configured-range extrapolation over B[-100,+100] and a complete C cycle: `0.764644 mm` at `B-100.0000 C272.6561` (reported limitation; not a protocol gate)

## Frozen Files

| file | SHA-256 |
| --- | --- |
| `5th_axis_xyzbc_ssi_tcpc_probe_basic.hal` | `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` |
| `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini` | `afa989840f35278c471ede6b438006546fd3f7484ae4addebfad35212400d519` |
| `fit_tcpc_relocated_sphere_t4_r2.py` | `faae48919e01f5f7cf5a9e8f29da40fc77bdf359d21bec1848bdcdfb979c71bb` |
| `TCPC_RELOCATED_SPHERE_T4_FIT_R2_REPORT.md` | `c4c625eb44254e60d0f95ce8544713d406743c45810f0d4fb6d5bce6306095b9` |
| `tcpc-relocated-sphere-t4-fit-r2-residuals.csv` | `8de7e98a4767eba6545ee3e6f3a0688bf56e43427153bea79c08c4787f59ade1` |
| `tcpc-relocated-sphere-t4-fit-r2-pins.csv` | `d3481e51cd98b6fc4c8ac8484a781b6fe88321ab371b53bc5081248f72c1e2b6` |
| `tcpc-relocated-sphere-t4-fit-r2-checkpoint.json` | `d3a76e7149e251a1a422bcb54cf3bd0f1629f53178f9c64a3929bd99e7134d33` |
| `tcpc_relocated_sphere_t4_candidate_verification.ngc` | `5803746d4973cd3ea6322d9f128be016a706b2b136224806eac1b1e5566df522` |
| `tcpc_relocated_sphere_t4_candidate_r2.hal` | `0bfefdb068bb353282fc41067d5cd7464f76ea6a4f520204f0ab5c914ee1673a` |
| `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t4_candidate_r2.ini` | `1ab3b84611b93fbf10083e21f87b90d19eea5c3c8a8fe66373570a7cace3d77e` |
| `tcpc_relocated_sphere_t4_candidate_r2_verification.ngc` | `a1358c407399ad3606a5a2a449cc973cd39c6ea705233c1f87fdfc0dcb45b7f4` |
| `tcpc-relocated-sphere-t4-candidate-r2-attempt1-results.csv` | `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93` |
| `tcpc-relocated-sphere-t4-candidate-r2-attempt1-state.csv` | `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7` |
| `tcpc-relocated-sphere-t4-candidate-r2-attempt1-closures.csv` | `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f` |

## T4 Gates

A completed mode-26 run is accepted only if its exact schema, pose, tool/TLO, contact-quality, state, endpoint, and all 28 closure contracts pass, and:

1. On 76 equal-weight unique poses, centered RMS and maximum each improve over immutable mode-23 attempt 1 by both 10% and 0.010/0.020 mm.
2. On those globally centered unique-pose residuals, positive- and negative-B high-tilt RMS each improve by at least 10%.
3. Unique-pose B0 RMS does not worsen by more than 0.010 mm, and no unique pose worsens by more than 0.075 mm.
4. Unique-pose centered RMS / max are at most 0.120 / 0.280 mm (offline prediction: 0.085763 / 0.204948 mm).
5. Raw-101 centered RMS / max are at most 0.120 / 0.280 mm (offline prediction: 0.087176 / 0.207789 mm).
6. Raw-101 actual-versus-predicted centered pattern RMS / max are at most 0.050 / 0.120 mm; both use their own raw-101 global mean.

These gates test implementation and sign on the same measured grid. They do not authorize extrapolation to omitted C sectors, a general live correction, or a production HAL/INI change.

## Explicit Limitations

- weak paired-B selection stability: `b_sin2` 0/8; `bc_sinb_cos2c` and `bmid_cos2c` 3/8
- selection-adjusted antipodal-C outer RMS / max: `0.253374 / 0.837828 mm`
- the 0.750 mm protocol cap was imposed on measured poses; the largest outer-fit value was `0.749996 mm`; this preflight separately checks the primary densely and along the run path
- the primary reaches `0.764644 mm` near `B-100/C272.6561` inside the configured B range but outside the authorized B +/-90 diagnostic domain; no manual, MDI, or jog motion is permitted under the candidate configuration
- `bharm-c` vectors were excluded by the declared model scope, not selected against the 17-term pool
- the forward-plus-swap protocol was frozen before fresh T4/T3 candidate data, but after inspection of the baseline T4 data

## Mandatory Rollback

T3 must not run under this candidate configuration. After the T4 test, close LinuxCNC and clean-restart the baseline `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini`; verify the base HAL SHA-256 is `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778` before any current-calibration T3 holdout run.

Detailed configured-limit replay: `tcpc-relocated-sphere-t4-candidate-r2-reachability.csv`
