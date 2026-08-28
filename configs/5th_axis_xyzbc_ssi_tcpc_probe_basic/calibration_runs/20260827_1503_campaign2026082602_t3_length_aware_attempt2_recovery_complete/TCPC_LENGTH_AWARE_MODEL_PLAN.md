# TCPC Length-Aware Model Plan

## Status

`REAL-MACHINE VALIDATION CANDIDATE - NOT PRODUCTION RELEASED`

The reviewed rigid head-head transform remains suitable. The current empirical
B/C surface is tool-length independent, so it cannot explain the repeatable T3/T4
difference. The next candidate therefore uses:

```text
H(B,C,L) = H0(B,C) + S(B,C) + q(L) D(B,C)
q(L) = (229.407000 - L) / 100.800271
```

`H0` is the accepted baseline surface, `S` is a ten-term common increment, and
`D` is a five-term T3 endpoint differential. `q=0` at T4 and `q=1` at T3.
Runtime evaluation must use the active G43 Z length synchronously inside the
kinematics calculation. It must not asynchronously rewrite coefficient pins and
must not clamp at either calibration probe length. Each forward/inverse call must
use one snapshot of the active offset, bracket coefficient evaluation with the
expected model ID, and fail on a nonfinite complete transform.
The generated overlay is startup-only: never source or reload it in a running
LinuxCNC session. Every coefficient revision requires a new model ID and a clean
restart; the ID is not a supported live-reload mechanism.

## Full Tool Domain

The active table contains `54` tools from T60 `114.677000 mm`
through T51 `411.810000 mm`, a `297.133000 mm` span.
The tracked predecessor used T69 at `425.022000 mm`. To cover both
the current table and that recently used tool, the declared hard runtime domain is
`100.000000..430.000000 mm`, with only
`0.002 mm` boundary-comparison tolerance. The nominal hard domain is
`100.000..430.000 mm`; the exact guard acceptance interval is
`99.998..430.002 mm`.
Zero/nonfinite Z, nonfinite offset fields, nonzero X/Y/A/B/C/U/V/W offsets, or a
length outside that interval must make G43.4 fail closed. The guard uses the live
active offset because normal tool touch-off legitimately updates table lengths.
Every table edit refreshes sealed traceability; an inside-domain edit does not expand
the coefficient domain, while an outside-domain edit requires explicit domain/cap
requalification and remains blocked. The domain must never expand implicitly.

| length mm | q | dense incremental max mm | dense length-bank max mm | dense total max mm |
| ---: | ---: | ---: | ---: | ---: |
| 99.998000 | +1.283816 | 0.667971 | 0.245715 | 1.112224 |
| 100.000000 | +1.283796 | 0.667969 | 0.245711 | 1.112224 |
| 114.677000 | +1.138191 | 0.656810 | 0.217843 | 1.107983 |
| 128.606729 | +1.000000 | 0.646288 | 0.191394 | 1.104091 |
| 229.407000 | +0.000000 | 0.572376 | 0.000000 | 1.121951 |
| 411.810000 | -1.809549 | 0.470585 | 0.346337 | 1.282174 |
| 425.022000 | -1.940620 | 0.492394 | 0.371423 | 1.294172 |
| 430.000000 | -1.990005 | 0.500650 | 0.380875 | 1.298708 |
| 430.002000 | -1.990024 | 0.500653 | 0.380879 | 1.298710 |

The dense audit covers `B=-100..+100` and a complete C cycle at
`0.25 deg` spacing. It enforces incremental `<=0.700 mm`,
length-bank `<=0.400 mm`, total empirical `<=1.350 mm`, and
exact zero correction at B0/C0. The two permitted comparison-tolerance endpoints
`99.998000` and
`430.002000 mm` are included. A global derivative bound
adds the worst possible half-grid-cell change in both B and C. The resulting continuous
low/high endpoint upper bounds are respectively
`0.674266 / 0.247089 / 1.121483 mm` and
`0.507717 / 0.383009 / 1.309149 mm`.
Because correction is affine in length and vector norm is convex, the two outer
length endpoints plus these angular bounds cover every intermediate B/C/L point.

## Evidence Boundary

The numerical envelope covers the hard software domain, but present accuracy evidence does
not. T3 and T4 identify one straight slope only. The current table maximum is 181% of the
T3-to-T4 span beyond T4, where nonlinear rail, spindle, or probe-length behavior is
not identifiable from the existing data; the 430 mm endpoint is 199% beyond T4.
Therefore only the T3-to-T4 bracket may
be accepted until an independent physical endpoint test is complete.

Consumed-data development scores are T4 `0.107256/0.247250 mm` RMS/max and T3
`0.099481/0.206612 mm`; all 20 unique T3 poses improve. These are model-development
results, not release validation.

## Release Sequence

1. Implement synchronous length evaluation, fail-closed guards, diagnostics, and
   forward/inverse simulation tests while leaving the production configuration unchanged.
2. The dedicated validation INI now uses `lengthmodel=1 lengthmodelid=2026082601`
   with `[TCPC] LENGTH_MODEL_REQUIRED=1` and loads the exact coefficient overlay
   only during startup, never by sourcing it into a running session.
3. Freeze code, coefficients, model ID, domain, caps, analyzer, and hashes.
4. Run a fresh uninterrupted T4 101-row/28-closure validation, followed by a fresh
   uninterrupted T3 31-row/14-closure validation without retuning.
5. T4 is the longest available touch probe. Validate the `425-430 mm` endpoint later
   with the planned dial-gauge method on an equivalent pose grid. A second endpoint
   near `100-115 mm` is preferable.
6. If the long endpoint fails, fit continuous short-side and long-side slopes anchored
   at T4, freeze again, and require a new untouched endpoint validation.

## Traceability

All `7` top-level real TCPC INIs resolve to the audited canonical
tool table and define no TOOL_DATABASE override. Length-model promotion is limited to
the validation-only `5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`; every production and legacy capture INI
remains unpromoted.
Kinematics source SHA-256: `cd3b4ba9c9dc82ab6cec266280d48f7fd6c5b0ad4064f16c3b87cfc7caff4fa0`.
Base HAL SHA-256: `b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778`.
Canonical tool table SHA-256: `e7d459a2c875f56f2fcdeeefd3c8fa889809a5545cd3eab1309176c8c623092d`.
Generated real-machine validation candidate HAL SHA-256: `8ed28898b247b023038cdf2cb0278fabe2995d2d691df95970783284fec7cb14`.
The compiled headless integration test independently checks runtime coefficients,
range/tolerance faults, caps, model ID, and forward/inverse continuity.

This auditor imports neither LinuxCNC nor HAL and cannot issue machine commands.
