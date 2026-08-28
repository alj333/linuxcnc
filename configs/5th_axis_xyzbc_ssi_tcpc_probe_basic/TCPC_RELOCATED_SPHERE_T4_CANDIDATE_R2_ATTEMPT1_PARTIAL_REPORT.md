# Campaign-04 T4 R2 Candidate Attempt-1 Partial Report

Status: `FORMAL CONTRACT FAIL; PROVISIONAL CORRECTION RESPONSE FAVORABLE`.

This report analyzes the immutable mode-26 attempt-1 files after the runner
aborted by design at closure block 911. It does not waive the frozen contract,
impute missing rows, or authorize production use.

## Acquisition Integrity

- Result/state rows: `93 / 93`, contiguous sequences `1-93`.
- Closure rows: `17`; the first 16 pass and their worst norm is
  `0.039689 mm`.
- All 93 result/state rows individually pass the existing exact schema, pose,
  identity, tool/TLO, TCPC/TWP, SSI, contact, travel, diameter, endpoint, and
  state validators.
- All 76 canonical unique B/C poses are present, including every signed high-B
  pose.
- Sequence 93, closing `B0/C0`, was accepted before closure 911 compared it
  with sequence 1. The logged vector is
  `+0.035156 / +0.033230 / +0.014069 mm`, norm `0.050380 mm`.
- The frozen closure limit is `0.050000 mm`. The `0.000380 mm` exceedance is a
  definite closure-contract failure and correctly stopped the runner before
  sequences `94-101`.
- Missing sequences are the final repeated B0 sweep at
  `C45/90/135/180/225/270/315/0`. Attempt 1 must not be resumed, appended,
  truncated, relabelled, or reused.

Immutable input hashes:

```text
results   b96051b207c8c90ae16e1850420e540f9ff9c1fa565f2840ac949f3af0fbb7dc
state     89eb547fc08899b75c8b66ee1744dca64eb5922e87a30b298c8a9591e5cf35a6
closures  8d9a8abfa2ed498d69949dc0f9288d2f42fb3094bfcba6f02ecf3095e4b0a415
```

The sealed raw-attempt archive is
`calibration_runs/20260825_1412_campaign04_t4_candidate_r2_attempt1_partial_closure_stop`.
Its `SHA256SUMS` SHA-256 is
`2026776b2b3a1b7b98fc74af2881fe99b2498ddbb7aa0899f8033977ef8156a0`.

## Provisional Metrics

These use the frozen centering and residual conventions, but candidate B0
averages contain only the available repetitions. They are sensitivity results,
not formal acceptance values.

| Metric | Baseline | R2 partial | Change |
|---|---:|---:|---:|
| Equal-76 RMS | 0.219602 | 0.086446 | 60.6% better |
| Equal-76 maximum | 0.709875 | 0.221643 | 68.8% better |
| Positive high-B RMS | 0.232068 | 0.087004 | 62.5% better |
| Negative high-B RMS | 0.346272 | 0.103197 | 70.2% better |
| B0 RMS | 0.133686 | 0.082729 | 38.1% better |

- Candidate maximum: `0.221643 mm` at `B-90/C180`.
- Maximum unique-pose worsening: `0.055205 mm` at `B-45/C0`, below the
  `0.075 mm` limit. Twelve of 76 poses worsen; none exceeds the limit.
- Raw-93 candidate RMS/max: `0.088453 / 0.222863 mm`.
- Raw-93 actual-versus-frozen-prediction pattern RMS/max:
  `0.024691 / 0.055345 mm`, below the proxy `0.050 / 0.120 mm` limits.
- Worst pattern discrepancy: `0.055345 mm` at sequence 55, `B+30/C270`.

The result strongly supports the R2 correction sign and scale. It is close to
the frozen equal-76 prediction of `0.085763 / 0.204948 mm` and removes most of
the original signed high-B error.

## Contact Sensitivity

Sequence 85 at `B+90/C180` is a review flag despite passing every frozen gate:
its two-pass center delta is `0.059229 mm`, and W travel is `4.941327 mm`,
about `0.058673 mm` short of nominal. Sequence 82 at `B-60/C0` is a lesser
similar flag at `0.038052 / 4.962281 mm`. Neither point drives the favorable
result:

| Treatment | Equal-76 RMS / max | Positive-B RMS | Negative-B RMS | Max worsening |
|---|---:|---:|---:|---:|
| Original partial | 0.086446 / 0.221643 | 0.087004 | 0.103197 | 0.055205 |
| Exclude both | 0.085639 / 0.222778 | 0.084821 | 0.102557 | 0.053478 |
| Frozen-model replace both | 0.086228 / 0.221445 | 0.087344 | 0.102125 | 0.055609 |
| Data-infer both | 0.086086 / 0.221572 | 0.086712 | 0.102174 | 0.055599 |

Across deletion, replacement, and inference cases, raw pattern RMS/max remain
within `0.024120-0.024769 / 0.054614-0.055345 mm`. A deliberately adverse
physical replay that shifts sequence 85 by its full W-travel shortfall raises
its per-pose worsening to `0.071653 mm`, still below the `0.075 mm` limit but
with only about `0.003 mm` margin. Attempt 2 remains necessary to replace this
partial sensitivity evidence with a complete fresh acquisition.

## Frozen Gate Disposition

No final gate may be recorded as passed because exact `101 / 101 / 28`
structural acceptance is a prerequisite.

1. Equal-76 improvement and ceilings: provisional pass; final unavailable
   because closing B0 repetitions are missing.
2. Positive- and negative-B high-tilt RMS: provisional pass with all high-B
   measurements present; final global centering still depends on complete B0
   averages.
3. B0 and per-pose worsening: provisional pass; final unavailable.
4. Raw-101 ceilings: unavailable. The raw-93 proxy passes.
5. Raw-101 prediction-pattern gates: unavailable. The raw-93 proxy passes.
6. Closure/data contract: definite fail at block 911.

Sensitivity checks do not change this disposition. Replacing the eight missing
rows either with their opening measurements or with the observed sequence-1 to
sequence-93 drift gives equal-76 RMS `0.086507` or `0.086205 mm`. A conservative
bound that allows every missing point to vary within the observed
`0.050380 mm` drift envelope still gives equal-76 RMS/max
`0.094239 / 0.224131 mm`, raw-101 `0.102278 / 0.230324 mm`, and prediction
pattern `0.038831 / 0.086664 mm`. These checks show robustness but cannot repair
the failed audit trail.

## Required Follow-Up

A separately versioned full attempt 2 is required for the predeclared formal
acceptance path. It must use fresh output files while retaining the exact R2
overlay, 101-pose order, motion, `0.050 mm` closure limit, pin/state guards, and
statistical gates. A short closing-B0 supplement may be useful only as a
separate diagnostic; it cannot complete or repair attempt 1.

T3 must not run under the candidate overlay. After the final T4 disposition,
clean-close the candidate configuration and restore the baseline task-capture
INI before any T3 transfer check.
