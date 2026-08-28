# TCPC Length-Aware T4 Validation Preflight

Status: `PASS`

- campaign / mode / attempt: `2026082602 / 32 / 1`
- model ID: `2026082601`
- probe: `T4 / H4 / 229.407000 mm / #3032=0.154742`
- canonical acquisition: `101` result/state/model-state rows, `28` closures, `808` contact and gap traces
- parser: standalone in-tree `bin/rs274 -g` passed under an isolated temporary HOME
- controller-process gate: no LinuxCNC, linuxcncsvr, milltask, rtapi_app, Probe Basic, or QtPyVCP process was active

## Sealed Inputs

- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`: `24e74a7aefa6155c7ad8320ec6525dff63f329681a24d1886d78943da97efc5a`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc_length_aware_candidate_2026082601.hal`: `8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14`
- `nc_files/calibration/tcpc_length_aware_t4_validation_2026082601.ngc`: `0c25bad2be98eae5e927c765fea83d1b877e652635f446ff637dbf8160e308be`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/assess_tcpc_length_aware_bounds.py`: `b84c9f6d86d39c31872cff3d4fb86758672087af55b439625fe07d3049bdfef2`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_LENGTH_AWARE_MODEL_PLAN.md`: `b8306e4612dff6ad52914ea0cd146bff39a093643f96a766836d82337ddc826e`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_anchor.py`: `30fc04745d3af287990f69ec161d2de9e3b996040f5f51327c80506a701c1b0d`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_campaign.py`: `d19d3d6d92f21e972709089be737ba0e735e894d3fabe09246bde5ea084f822a`
- `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_reachability.py`: `e78a94f075fcb9bea0cbc04c3f3c4f214bc0816b548569a53111b8bd90610607`
- validator: `6ebbd6ba910f9700e481b47c4bef89ad31039b286cbca5f659134ea7d616c7fb`

## Fresh Outputs

All six attempt-1 files are exact header-only ASCII files:

| output | columns | header SHA-256 |
| --- | ---: | --- |
| `tcpc-length-aware-t4-validation-2026082601-attempt1-results.csv` | 33 | `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93` |
| `tcpc-length-aware-t4-validation-2026082601-attempt1-state.csv` | 35 | `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7` |
| `tcpc-length-aware-t4-validation-2026082601-attempt1-model-state.csv` | 22 | `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd` |
| `tcpc-length-aware-t4-validation-2026082601-attempt1-closures.csv` | 15 | `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f` |
| `tcpc-length-aware-t4-validation-2026082601-attempt1-contact-trace.csv` | 32 | `df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8` |
| `tcpc-length-aware-t4-validation-2026082601-attempt1-gap-trace.csv` | 24 | `e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2` |

## Contract

The frozen runner has one initial M0, no M1, no long dwell, no direct HAL or coefficient mutation, and only its reviewed deassert-only M65 P0/P1 safety clears. The canonical 101-pose/28-closure T4 grid, every G38 transaction layer, model/live/final guards, and six isolated LOGAPPEND destinations passed static checks.

The deterministic full-length-domain model audit passed. This physical acquisition validates T4 at `q=0` only; it does not validate the differential length bank or extrapolated longer tools. Those remain assigned to later T3 and dial-gauge validation.

This validator imports neither LinuxCNC nor HAL and issues no machine-control command.
