# TCPC Length-Aware T3 Validation Preflight

Status: `PASS`

- campaign / mode / attempt: `2026082602 / 33 / 1`
- model ID: `2026082601`
- probe: `T3 / H3 / 128.606729 mm / #3032=0.117658`
- canonical acquisition: `31` result/state/model-state rows, `14` closures, `248` contact and gap traces
- parser: standalone in-tree `bin/rs274 -g` passed under an isolated temporary HOME
- controller-process gate: no LinuxCNC, linuxcncsvr, milltask, rtapi_app, Probe Basic, or QtPyVCP process was active, and /tmp/linuxcnc.lock was absent

## Sealed Inputs

- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`: `24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc_length_aware_candidate_2026082601.hal`: `8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14`
- `nc_files/calibration/tcpc_length_aware_t3_validation_2026082601_attempt1.ngc`: `d6158b9ff91f5fa73a11071d314c64a442d6747f6758587415ece7c867e53bd6`
- `nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc`: `90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5`
- `nc_files/calibration/tcpc_length_aware_t4_validation_2026082601_attempt2.ngc`: `d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/assess_tcpc_length_aware_bounds.py`: `b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_LENGTH_AWARE_MODEL_PLAN.md`: `b8306e4612dff6ad52914ea0cd146bff39a093643f96a766836d82337ddc826e`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_anchor.py`: `30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_campaign.py`: `d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_reachability.py`: `e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/assess_tcpc_r3_feasibility.py`: `4520081bb7e7b4088a555e498ad7e6430dd3f5fc2d3d93a8a1e4c9867eaa6dd1`
- `src/emc/kinematics/headheadkins.c`: `cd3b4ba9c9dc82ab6cec266280d48f7fd6c5b0ad4064f16c3b87cfc7caff4fa0`
- `rtlib/headheadkins.so`: `1cc5b7023bed01bd2eb56bb52139e74f964cf17754b440aff42a987f4b22ac4c`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc_probe_attempt3_edge_counters.hal`: `6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/SHA256SUMS`: `546377e7ed7c98f4e24e6fc239b05810ea664ea101e6bd5d79e3c36558f9a880`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1026_campaign2026082602_t4_length_aware_attempt2_complete/TCPC_LENGTH_AWARE_T4_ATTEMPT2_VALIDATION_REPORT.md`: `0b17f37f2fa625d942a9f4bc161fa533b6d6a6562e7ee320a05ae111800e42ae`
- validator: `88ddd9a4ead0d5a461cb7de7caa919cb878e0dcaf9dcf7633902abd86a8fbdae`

## Fresh Outputs

All six attempt-1 files are exact header-only ASCII files:

| output | columns | header SHA-256 |
| --- | ---: | --- |
| `tcpc-length-aware-t3-validation-2026082601-attempt1-results.csv` | 33 | `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93` |
| `tcpc-length-aware-t3-validation-2026082601-attempt1-state.csv` | 35 | `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7` |
| `tcpc-length-aware-t3-validation-2026082601-attempt1-model-state.csv` | 22 | `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd` |
| `tcpc-length-aware-t3-validation-2026082601-attempt1-closures.csv` | 15 | `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f` |
| `tcpc-length-aware-t3-validation-2026082601-attempt1-contact-trace.csv` | 32 | `df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8` |
| `tcpc-length-aware-t3-validation-2026082601-attempt1-gap-trace.csv` | 24 | `e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2` |

## Contract

The frozen runner has one initial M0, no M1, no long dwell, no whole-pose retry, no direct HAL or coefficient mutation, and only its reviewed deassert-only M65 P0/P1 safety clears. The canonical 31-pose/14-closure T3 grid, sealed T3 motion subroutines, sealed Attempt-2 safety subroutines, every G38 transaction layer, model/live/final guards, exact 31/14/248 runtime guards, and six isolated LOGAPPEND destinations passed static and mutation checks.

The bounded duplicate-pulse rule accepts at most two matched raw/mux extras only when G38 succeeds, exactly one gated edge reaches motion, no gated repeat occurs, and the probe passes the two-sample release guard. All extras remain visible in the trace outputs.

The deterministic full-length-domain model audit passed. Every model row is required to match `q=1`, the offline differential D vector, and the total H0+S+D vector. The independent historical synthetic check reproduces the documented H0 and candidate metrics and proves the same-acquisition reconstruction sign without using consumed data for runtime acceptance.

The immutable T4 completion manifest and archived formal PASS report were verified. Every manifest entry matches its archive member; no member is missing, surplus, nested, or symlinked. Semantic checks additionally require ownership and hashes of the runner, validator, completed results, kinematics source, compiled kinematics module, and probe-counter HAL. The current source/module/probe-counter artifacts exactly match those archived T4 members. T3 is therefore gated on the accepted physical q=0 endpoint and the same implementation/safety dependencies, rather than code provenance alone.

Runtime acceptance requires raw-31 and equal-20 RMS/max at or below 0.120/0.280 mm, the prescribed relative and absolute improvements against reconstructed same-acquisition H0, at least 10% RMS improvement for both B signs on globally centered equal-20 residuals, B0 RMS worsening no greater than 0.010 mm on those same residuals, and no unique-pose centered-norm worsening above 0.050 mm.
Targeted rejection fixtures exercise raw and equal absolute RMS/max ceilings, both branches of every relative/fixed-minimum improvement gate, positive-B, negative-B, B0, and single-pose worsening boundaries. Result/state/closure schema and geometry validation remains delegated to the sealed imported campaign analyzers.

A passing acquisition validates the physical T3 endpoint and the T3-to-T4 evidence bracket. It does not validate extrapolation to tools outside that bracket.

This validator imports neither LinuxCNC nor HAL and issues no machine-control command.
