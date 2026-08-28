# TCPC Length-Aware T3 Attempt-2 Recovery Closeout

Status: `COMPOSITE ENGINEERING PASS - NOT FORMAL UNINTERRUPTED T3 RELEASE`

## Disposition

The T3 `q=1` endpoint passes the frozen length-aware model gates. The accepted
composite contains Attempt-1 canonical rows `1..22` and recovery Attempt-2 rows
`3..11`, mapped without coordinate alignment or source-data modification to
canonical rows `23..31`. Recovery rows 1 and 2 are continuity bridges only.

Attempt 1 stopped correctly before accepting row 23 after a false electrical
pass-2 W touch. The rejected transaction, subsequent probe flashing, and later
machine power loss are retained as provenance; none of that rejected geometry
enters this result. Because the accepted field spans a probe reseat, power cycle,
and two acquisition identities, the result is an engineering validation rather
than a formal uninterrupted release.

## Frozen Identity

- model ID: `2026082601`
- recovery campaign / mode / attempt: `2026082602 / 34 / 2`
- probe: T3 / H3 / `128.606729 mm`, `q=1`
- probe offset: `#3032=0.117658 mm`
- runner SHA-256:
  `1924e4af8be964a29442f23903e3566daceb4e65dde0e334bd595ba2dcb31294`
- validator SHA-256:
  `cb8960567f39d08bf0ef303110e49910fe50f1d9bb828b200803ba4a6ebe47a1`

## Validation Result

The file-only validator and an independent second audit both pass.

| metric | length-aware `H0+S+D` | reconstructed length-independent `H0` | reduction |
| --- | ---: | ---: | ---: |
| raw 31-row RMS | `0.107172 mm` | `0.222423 mm` | `51.8%` |
| raw 31-row maximum | `0.238596 mm` | `0.627672 mm` | `62.0%` |
| equal 20-pose RMS | `0.103060 mm` | `0.251775 mm` | `59.1%` |
| equal 20-pose maximum | `0.218333 mm` | `0.592990 mm` | `63.2%` |

The frozen development prediction for the T3 equal-pose field was
`0.099481/0.206612 mm` RMS/max. The untouched validation result is therefore
within `0.003579/0.011721 mm` of that prediction.

Signed-B and B0 groups use the same global centered field; groups are not
independently recentered.

| group | length-aware RMS | reconstructed H0 RMS | reduction |
| --- | ---: | ---: | ---: |
| positive B | `0.089938 mm` | `0.208666 mm` | `56.9%` |
| negative B | `0.111950 mm` | `0.318974 mm` | `64.9%` |
| B0 | `0.108919 mm` | `0.162422 mm` | `32.9%` |

Both B signs improve strongly. The largest individual-pose worsening is only
`0.008584 mm`. This supports a real tool-length-dependent error field and does
not indicate that the correction is merely trading one B sign against the other.

## Continuity And Closure

- post-reseat B0 bridge: `0.005719 mm`
- post-reseat B-90 bridge: `0.013314 mm`
- worst reconstructed canonical closure: `0.016482 mm`
- recovery closure maximum: `0.013314 mm`
- closure limit: `0.050000 mm`

All six recovery closures pass. The two cross-attempt bridges show that the
accepted rows on either side of the reseat and power cycle remain consistent at
the machine's observed repeatability level.

## Probe Transaction Evidence

The recovery contains exactly `11/11/11` result/state/model-state rows, six
closure rows, and `88/88` contact/gap trace rows. Sequences are exactly `1..11`
with no duplicate or missing identity. All 88 gated probe contacts succeeded;
there is no gap activity, terminal failure, consistency fault, release fault, or
counter discontinuity.

Four delayed post-contact raw/mux edges occurred across three contacts in a
`1,2,1` distribution. None reached the gated motion input. All second-pass
travels exactly match their contact traces. The worst two-pass center delta is
`0.024217 mm`, fitted diameters span `30.120500..30.285512 mm`, and the worst
radial residual is `0.142756 mm`; no bad accepted probe point was found. The
counter chain begins at raw/mux/gated `2/2/0` after the two manual checks and
ends at `94/94/88`. This validates the bounded duplicate-pulse filter for this
run, not arbitrary future probe faults.

## Engineering Interpretation

T4 at `229.407000 mm` formally validated the common `q=0` correction bank at
`0.107589/0.241710 mm` equal-pose RMS/max. This T3 composite validates the
differential `q=1` bank at `0.103060/0.218333 mm`. Together they support the
length-aware interpolation between the two probe lengths for the current sphere
location and machine condition.

The remaining roughly `0.10 mm` pose-field RMS is not evidence for a single
correctable B-axis zero or alignment term. It can contain B-axis alignment,
X/Y/Z rail geometry, spindle seating and wear, head geometry, probe repeatability,
and table-position effects. A later second table location is still required to
separate repeatable rotary structure from machine-volume error.

Accuracy evidence currently covers only the physical T3-to-T4 bracket
`128.606729..229.407000 mm`. The software guard and bounded coefficient audit
cover `100..430 mm`, but longer-tool accuracy remains extrapolation until the
planned dial-gauge endpoint test near `425..430 mm` is completed. A second
endpoint near `100..115 mm` remains preferable.

## Provenance

- Attempt-1 partial archive:
  `calibration_runs/20260827_1351_campaign2026082602_t3_length_aware_attempt1_partial_quality_abort_seq23`
- Attempt-1 partial `SHA256SUMS` SHA-256:
  `1e53f1908d54781aad8344e071767816479052ee50d70aa12731ec89c8e7998c`
- Attempt-2 recovery preflight archive:
  `calibration_runs/20260827_1416_campaign2026082602_t3_length_aware_attempt2_recovery_preflight`
- Attempt-2 preflight `SHA256SUMS` SHA-256:
  `1dc155d08c27272d2755a4e63b5e7707cd8846aabe5712aa6e23694e9b3f4d77`
- recovery result SHA-256:
  `fbc94c6599ec5f02ca47fc706146e3e9425d999901f2e73f481382f3423002d5`
- recovery state SHA-256:
  `942b51ce4c916cd4b97728c119997f0ad1b47e573da81c53a9cd054ed4e6e792`
- recovery model-state SHA-256:
  `20c0d0779c9d9cbb033c64411f05056695d0ce9b5aa112deb93f6189cdee500f`
- recovery closures SHA-256:
  `6991dc6660b9df0c2153d43961634d0b1759ab6ed3f15090eb2b11108d455870`
- recovery contact trace SHA-256:
  `777630adbafe8c82bc1c16768d37e78d42a6f04c83ba20fd4be888d19ab4f2f8`
- recovery gap trace SHA-256:
  `a67fd0481be6806a7e795f810b2698961973c9fea97527fad68e0f7193db681e`

The validator is file-only: it imports no LinuxCNC or HAL module and issues no
machine command.
