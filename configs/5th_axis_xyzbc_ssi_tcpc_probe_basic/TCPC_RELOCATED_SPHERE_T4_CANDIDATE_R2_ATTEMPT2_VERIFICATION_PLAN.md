# Campaign-04 T4 R2 Candidate Attempt 2 Verification Plan

Status: `OFFLINE PREPARATION`. This is a separately versioned retry of the
guarded same-grid T4 diagnostic. It is not a released calibration.

## Attempt-1 Disposition

Attempt 1 is immutable failed/incomplete evidence. It accepted sequences
`1-93`, then closure `911` measured `0.050380 mm` against the frozen
`0.050000 mm` limit and aborted before sequence 94. It must not be resumed,
truncated, relabelled, or appended.

The complete attempt-1 capture is sealed at:

`calibration_runs/20260825_1412_campaign04_t4_candidate_r2_attempt1_partial_closure_stop`

Its `SHA256SUMS` file has SHA-256
`2026776b2b3a1b7b98fc74af2881fe99b2498ddbb7aa0899f8033977ef8156a0`.
The attempt-2 analyzer verifies that checksum set and the live attempt-1
runner, analyzer, and three partial outputs before any preflight or result
validation.

## Frozen Scope

- campaign / mode / attempt: `2026082404 / 26 / 2`
- probe: T4 long probe only, `T4`, `G43 H4`, length `229.407000 mm`
- probe calibration parameter: `#3032=0.154742`
- grid: the exact 101-row mode-23 T4 grid, collapsed to 76 equal-weight poses
  for primary statistics
- closures: all 28 original checks, each with the unchanged `0.050 mm` limit
- holds: one initial `M0`; no intermediate holds
- overlay: the unchanged 30 absolute totals from the frozen ten-term,
  lambda-10 R2 fit

The base HAL, production INI, task-capture INI, candidate INI, R2 overlay,
rigid geometry, and rotary zeros are not modified for attempt 2.

## Attempt-2 Artifacts

The machine runner is:

`/home/cnc5/linuxcnc-dev/nc_files/calibration/tcpc_relocated_sphere_t4_candidate_r2_attempt2_verification.ngc`

The offline contract is:

`analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt2.py`

The runner is byte-for-byte attempt 1 after normalizing only:

- `#727 = 2.0` back to `#727 = 1.0`
- five attempt-2 output-name occurrences back to attempt-1 names

No motion, feed, pose, probing, retry, release, live-state, pin, endpoint,
closure, or error-handling statement differs. The analyzer proves this exact
normalization, then proves the normalized attempt-1 runner's original R1
derivation. It also checks all 30 read-only overlay guards and rejects a test
mutation to the 101-row contract. Its row-count, unique-pose collapse,
residual, threshold, and statistical-gate functions must be exact text matches
to the hash-locked attempt-1 analyzer; only the attempt identity and artifact
namespace differ.

## Output Isolation

Only these fresh, initially header-only files may receive attempt-2 rows:

- `tcpc-relocated-sphere-t4-candidate-r2-attempt2-results.csv`: exactly 101
  rows using the frozen 33-column schema
- `tcpc-relocated-sphere-t4-candidate-r2-attempt2-state.csv`: exactly 101 rows
  using the frozen 35-column schema
- `tcpc-relocated-sphere-t4-candidate-r2-attempt2-closures.csv`: exactly 28
  rows using the frozen 15-column closure schema

Every row must identify campaign `2026082404`, mode `26`, and attempt `2`.
Attempt-1 output names are forbidden in the attempt-2 runner. The analyzer
rejects extra rows, mixed attempts, missing or duplicate sequences, schema or
pose changes, tool/TLO or TCPC state changes, contact-quality failures,
endpoint errors, and any failed closure.

Do not truncate or reuse attempt-2 outputs after any accepted row. A stopped,
aborted, or incomplete attempt 2 is preserved and any later retry requires a
new attempt identity, fresh output namespace, and new offline preflight.

## Offline Preflight

From the repository root:

```bash
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt2.py --self-test
python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_relocated_sphere_t4_candidate_r2_attempt2.py --preflight
```

Preflight must pass with all three attempt-2 files still exact header-only. It
verifies attempt isolation, the sealed attempt-1 archive, immutable fit inputs,
base/candidate configuration hashes, all R2 totals, exact runner derivation,
the 101-pose grid, `rs274 -g` parsing, configured limits, full trajectory
reachability, and dense correction checks.

The authorized B +/-90 candidate peak remains `0.671900 mm`, below the
`0.750 mm` diagnostic cap. The configured but unauthorized B +/-100 scan
reaches `0.764644 mm`; that remains an explicit release blocker. No manual,
MDI, or jog motion is authorized while the candidate overlay is active after
the reviewed start position has been established.

## Frozen Acceptance Gates

Only an exact complete attempt-2 run may be evaluated. All original gates are
unchanged:

1. Equal-76 globally centered RMS and maximum each improve over immutable
   mode-23 attempt 1 by both 10% and `0.010/0.020 mm`.
2. Equal-76 positive- and negative-B high-tilt RMS each improve by at least
   10%.
3. Equal-76 B0 RMS worsens by no more than `0.010 mm`, and no pose's centered
   norm worsens by more than `0.075 mm`.
4. Equal-76 centered RMS / maximum are at most `0.120 / 0.280 mm`; frozen
   prediction is `0.085763 / 0.204948 mm`.
5. Raw-101 centered RMS / maximum are at most `0.120 / 0.280 mm`; frozen
   prediction is `0.087176 / 0.207789 mm`.
6. Raw-101 actual-versus-predicted centered-pattern RMS / maximum are at most
   `0.050 / 0.120 mm`, with each pattern using its own raw-101 global mean.

The closure threshold remains `0.050 mm`. Attempt 1's borderline failure does
not change or relax it. Any future protocol change must be declared and
versioned before collecting data and cannot retroactively pass attempt 1.

## Interpretation And Rollback

A pass establishes R2 implementation/sign agreement only on the measured T4
grid. Weak term-selection stability, the `0.253374 / 0.837828 mm`
selection-adjusted antipodal-C outer result, the B +/-100 extrapolation, and
the missing T3 transfer check remain release blockers.

T3 must never run under the candidate INI or overlay. After the T4 diagnostic,
clean-close LinuxCNC, restart
`5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture.ini`, and verify base HAL
SHA-256
`b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`
before any current-calibration T3 holdout run.
