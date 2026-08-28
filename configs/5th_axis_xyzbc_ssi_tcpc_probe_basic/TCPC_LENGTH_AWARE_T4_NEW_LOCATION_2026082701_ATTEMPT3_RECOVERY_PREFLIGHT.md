# T4 New-Location Attempt-3 Recovery Preflight

Status: `OFFLINE PREFLIGHT PASS - HOLD FOR OPERATOR RESET, START RESTORE, AND LOAD GATE`

Recorded: `2026-08-27 +07`

## Frozen Build

- identity: campaign `2026082701`, mode `37`, attempt `3`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery.ngc`
- runner SHA-256: `bf76ab273c76a32046e6f2066f6b865ea8e0a448266cff0399186e262c5a061a`
- clean rows: summaries `92/92/92`, closures `30`, traces `736/736`
- acquired IDs: `1..9,17,20..101`
- immutable composite: Attempt 1 `1..17`, Attempt 2 `18..20`, Attempt 3 `21..101`

The runner and all six outputs are frozen. Do not edit or regenerate them
after this report without assigning a new identity and recomputing every hash.

## Isolated Header Files

All paths use prefix
`configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-length-aware-t4-new-location-2026082701-attempt3-recovery`.
Each file has exactly one schema header and no data row:

- results: `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93`
- state: `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7`
- model-state: `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd`
- closures: `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f`
- contact-trace: `df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8`
- gap-trace: `e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2`

Each header is byte-identical to its corresponding Attempt-2 schema. Every
absolute Attempt-3 output path occurs exactly twice in the runner: once in
the release header and once in its logging subroutine. No Attempt-2 output
prefix occurs in the runner.

## Salvage Audit

Attempt-2 summary/state/model IDs are exactly `1..9,17..20`. Its contact and
gap traces each have `108` data rows. The accepted boundary is the first
`104`; the remaining four rows in each file are rejected sequence-21 pass-1
contacts `1..4` and are excluded in full. Only Attempt-2 canonical rows
`18..20` are admitted to the composite. No coordinate translation or refit is
applied.

## Static Verification

A read-only ordinary-file audit passed `67` checks:

- mode/attempt/count selectors are exactly `37/3/92`
- matched-extra ceiling is `8`, minimum travel is `1`, and one acquisition means zero retries
- all 21 Attempt-2 subroutines match after output-prefix normalization
- all six outputs are header-only with preserved schemas and isolated paths
- acquired IDs expand exactly to `1..9,17,20..101`
- derived counts are `92` summaries and `736/736` transactions
- bridges `3709/3717/3720` and their immutable coordinates occur exactly once
- completion guards require `#726=101`, `#788=92`, `#977=92`, `#978=30`, and `#973=#974=736`
- there is exactly one executable M0, no M1, no top-level pre-M0 motion, and the counter baseline follows M0
- named conditional/loop blocks are balanced

The audit imported no LinuxCNC, HAL, rs274, or subprocess module and issued no
controller command. It read ordinary files only.

## Exact Reachability

The dedicated Attempt-3 replay passes from the frozen B0/C0 start. It samples
`28,345` points over the exact `1..9,17,20..101` order, including the new
direct B-5/C0 to B-5/C180 high-Z transition. The worst configured linear
margin after the conservative 5 mm reserve is `181.641553 mm`; rotary margins
are B `10 deg` and C `44 deg`.

- replay:
  `analyze_tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery_reachability.py`
- replay SHA-256:
  `4af0e489ca919d66799468ae3b34ce02face41cc21d1555a58c7c728e62bbff9`
- report:
  `TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT3_RECOVERY_REACHABILITY_REPORT.md`
- detailed CSV SHA-256:
  `bd75edc01ad802791096019d9c3795107a2af508dc92b42debca6c36c9cfe0d2`

The read-only Attempt-3 validator also passes compile, static, fresh-header,
and mutation self-tests. Its `--validate` mode correctly rejects the current
header-only outputs as incomplete.

- validator:
  `validate_tcpc_length_aware_t4_new_location_2026082701_attempt3_recovery.py`
- validator SHA-256:
  `7bb80f4aa04af2b0bbfaabc49a274a0c8fbe6d52a294a28e00f1172aac422413`

## Remaining Live Hold

This is not an execution release. The controller remains idle at the retired
Attempt-2 B-5/C225 abort pose with Attempt 2 still loaded. Do not Resume it.
The operator must reset or reseat and qualify T4, re-establish the frozen
B0/C0 start, and explicitly clear a fresh load. After load, the sole M0 and a
separate quiet/physical confirmation remain mandatory. Live tool/TLO/model,
probe, SSI, sphere security, post direction, and fixture clearance must all
be checked at those boundaries.

The retired Attempt-2 runner must not be resumed.
