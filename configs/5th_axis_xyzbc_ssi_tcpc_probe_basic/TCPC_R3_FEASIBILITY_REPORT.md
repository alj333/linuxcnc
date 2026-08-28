# TCPC R3 Offline Feasibility Assessment

## Decision

`NO R3 COEFFICIENTS RELEASED`

The existing evidence diagnoses a real T3/T4 transfer conflict and shows
that a mathematical compromise exists. It does not support a calibration
release. The four-source T3 composite is development-only evidence, not an
independent or same-acquisition holdout. A future R3 must be frozen before
fresh uninterrupted T4 and T3 validation runs.

The preferred exploratory path can proceed without another machine run:
keep T4 as the primary fit evidence and use the current T3 composite only
as noisy development compatibility evidence. Because that consumes the T3
responses, only a fresh T3 run may accept the frozen result. A clean T3
baseline is required before fitting only if a formal equal-tool joint
objective is chosen.

This report is offline-only. The generator imports neither LinuxCNC nor HAL
and cannot write a pin, overlay, INI, tool table, or live configuration.

## Frozen Evidence

- T4 training: campaign `2026082404`, mode `23`, attempt `1`; `101` raw
  rows collapsed to `76` equal-weight poses; `28` strict closures.
- T3 development composite: A1 sequences `1-14`, A2 `15-22`, A4 `23`,
  and A5 `24-31`; `31` raw rows collapsed to `20` equal-weight poses.
- T3 source-local closures: `4`; this does not satisfy the formal
  same-acquisition `31 / 31 / 14` contract.
- Every logged T3 closure passes `0.050 mm`. Every accepted source row
  satisfies the logged TCPC, SSI-valid, T3/tool-length, three-way TLO,
  exact gated-contact, zero gated-repeat, and zero gated-gap contracts.
  The A1 no-touch and A2 gap-burst terminal forensic rows are checked
  separately and are never promoted into accepted result rows.
- Every calculation input is tied to its archive seal and independently
  checked against the SHA-256 values embedded in the generator.

| evidence | SHA-256 |
| --- | --- |
| T4/R2 archive seal | `602cf8bf0bef86fcb4e80f1b1b7323a8a7608fc2c7baad35e3d2ed909d759835` |
| T4 primary results | `70e346c0db543a4ac052c68027e6f9854cd3d9a45b97b6432849586deb4d9468` |
| R2 pin audit | `d3481e51cd98b6fc4c8ac8484a781b6fe88321ab371b53bc5081248f72c1e2b6` |
| R2 residual map | `8de7e98a4767eba6545ee3e6f3a0688bf56e43427153bea79c08c4787f59ade1` |
| T3 A1 archive seal | `85306077f177700c49fc122fc79d2e24edbc7ab5d11b25209a8e7eb35439d700` |
| T3 A2 archive seal | `053344b2cf1676f6ae06ec3ae53a65ec3b7decd9e726839ed7fb94ed595a3df2` |
| T3 A4 archive seal | `5f0fa30df3b7cf3e326e44671c30cd231e4c6d74b82059d9fd359fc14923ebfa` |
| T3 A5 archive seal | `ef9e1c3957a9c2c30011d2f8c127737df53ab5a10b3f70bc1bab82b28c2ff03b` |
| assessment generator | `4520081bb7e7b4088a555e498ad7e6430dd3f5fc2d3d93a8a1e4c9867eaa6dd1` |

## R2 T3 Failure

| frozen calculation | result | limit | status |
| --- | ---: | ---: | --- |
| equal-20 RMS | `0.148716274` | `0.120000000` | `FAIL` |
| equal-20 maximum | `0.328314143` | `0.280000000` | `FAIL` |
| raw-31 RMS | `0.149044164` | `0.120000000` | `FAIL` |
| raw-31 maximum | `0.352449968` | `0.280000000` | `FAIL` |
| maximum pose worsening | `0.119218671` | `0.075000000` | `FAIL` |

Equal-20 improves from `0.251154900 / 0.617559442`
to `0.148716274 / 0.328314143 mm`, but
the remaining positive-high-B field controls all three failed gates. Raw
sequence 19 at B+90/C180 is the `0.352449968 mm` maximum.

- positive-B RMS: `0.207278246 -> 0.182814470 mm`
  (`11.802%` improvement)
- negative-B RMS: `0.321714766 -> 0.119781730 mm`
  (`62.768%` improvement)
- B0 RMS: `0.149881940 -> 0.122658320 mm`
  (change `-0.027223620 mm`)
- B+90/C0: `0.108526463 -> 0.227745135 mm`, worsening
  `+0.119218671 mm`
- B+90/C270: `0.073291274 -> 0.151630045 mm`, worsening
  `+0.078338771 mm`

## B+90 Attribution

At B+90/C0 the direct R2 correction is `[-0.007605, +0.075153, +0.088334]`
mm. Global centering changes the scored correction to
`[-0.041617, +0.000172, +0.133307]` mm, which aligns with the
baseline residual `[-0.071425, +0.060572, +0.054841]` and increases
its norm. The direct terms are:

| term | basis value | direct XYZ mm | norm mm |
| --- | ---: | ---: | ---: |
| `b_sin` | `+1.000000000` | `+0.020076, +0.005583, +0.092145` | `0.094472` |
| `bc_sinb_sinc` | `-0.000427606` | `+0.000030, -0.000068, +0.000006` | `0.000075` |
| `bc_sinb_cos2c` | `+0.999999634` | `-0.027711, +0.069638, -0.003817` | `0.075046` |

`b_sin.z` is the dominant direct C0 component. The unstable
`bc_sinb_cos2c` X/Y vector reinforces it. `c_cos` is exactly zero at C0;
any apparent C0 effect from that term in a centered attribution is only a
change of the global reference center.

At B+90/C270 the direct R2 correction is
`[+0.114255, +0.174520, +0.003199]` mm; the scored centered correction
is `[+0.080243, +0.099539, +0.048172]` mm:

| term | basis value | direct XYZ mm | norm mm |
| --- | ---: | ---: | ---: |
| `c_cos` | `-1.000427514` | `+0.020470, -0.076398, -0.017047` | `0.080909` |
| `b_sin` | `+1.000000000` | `+0.020076, +0.005583, +0.092145` | `0.094472` |
| `bc_sinb_sinc` | `-0.999999909` | `+0.069868, -0.159542, +0.015113` | `0.174825` |
| `bc_omcb_sin2c` | `+0.999999817` | `-0.023870, +0.474515, -0.090830` | `0.483719` |
| `bc_sinb_cos2c` | `-0.999999634` | `+0.027711, -0.069638, +0.003817` | `0.075046` |

The positive X correction is mainly `bc_sinb_sinc`,
`bc_sinb_cos2c`, and `b_sin`. The Y result is a large cancellation between
the positive `bc_omcb_sin2c.y` contribution and negative
`bc_sinb_sinc.y`, `c_cos.y`, and `bc_sinb_cos2c.y` contributions.
`b_sin2` and every `bmid_*` basis are zero at B90 and cannot directly cure
either endpoint.

## Common-Surface Limit

The centered T3-minus-T4 common-grid mismatch is `0.164423503 /
0.264629483 mm` RMS/maximum. Adding any identical pose correction
to both tools cancels exactly from this mismatch. A completely unrestricted
shared pose surface could at best split the difference between the tools,
giving the theoretical equal-tool lower bound `0.082211751 /
0.132314741 mm`. A common R3 can compromise; it cannot remove
the tool/mechanical differential.

## T4-Only Stable7 Check

The seven R2 terms selected in all eight paired-|B| folds were refitted to
the frozen T4 76-pose data at lambda 30:

```text
c_cos, b_sin, bc_sinb_sinc, bc_omcb_sin2c, bmid_base, bmid_cosc, bmid_sinc
```

| evaluation | RMS / maximum mm |
| --- | ---: |
| T4 training | `0.111474 / 0.288058` |
| T3 development counterfactual | `0.151898 / 0.352274` |
| T3 maximum pose worsening | `0.069992` at `B+90/C0` |

Stable7 does not meet the T3 ceilings. The transfer failure is therefore
not resolved by simply deleting the three selection-unstable R2 terms.

## Joint-Development Illustration

For feasibility only, the fixed ten-term R2 family was refitted with one
center per tool and equal total T4/T3 tool weight. No term was added or
selected. T4 features set the scale; T3 features are separately centered and
its 20 rows are weighted by `sqrt(76/20)`.

For standardized correction coefficients A, the implemented sum objective is
`D4 + D3 + lambda_sum*||A||^2`, where `D4=||Y4+Z4*A||^2` and
`D3=(76/20)*||Y3+Z3*A||^2`. Thus each tool supplies data weight 76.
The first column uses `lambda_sum=30`. An equal-tool averaged objective
`0.5*(D4+D3) + 30*||A||^2` is algebraically the same normal equation as
the sum implementation at `lambda_sum=60`; that is reported as the required
normalization sensitivity.

| evaluation | sum lambda 30 | averaged-loss lambda 30 (sum lambda 60) |
| --- | ---: | ---: |
| T4 equal-76 RMS / max mm | `0.106656305 / 0.247541359` | `0.114060555 / 0.261638021` |
| T3 equal-20 RMS / max mm | `0.117685732 / 0.268980083` | `0.121013881 / 0.275411863` |
| T3 raw-31 RMS / max mm | `0.124315035 / 0.291520953` | `0.126287231 / 0.297832544` |
| T3 maximum pose worsening mm | `0.042816641` at `B+90/C0` | `0.037260763` at `B+90/C0` |
| dense configured correction mm | `0.695646358` at `B-100.00/C272.00` | `0.632943586` at `B-100.00/C272.00` |

The sum-lambda-30 equal-20 result only just crosses the `0.120 / 0.280 mm`
ceiling and its raw-31 result remains outside at `0.124315 / 0.291521 mm`.
Under the averaged-loss normalization, equal-20 RMS moves outside to
`0.121014 mm` and raw-31 remains outside at `0.126287 / 0.297833 mm`.
The threshold crossing is not robust to objective normalization. Both cases
are consumed development illustrations; their coefficients are intentionally
not reported or written, and neither supplies a release candidate.

## R3 Protocol Boundary

A defensible R3 stage requires:

1. Treat this four-source T3 dataset as development evidence only.
2. For the preferred immediate path, use the equal-pose T4 grouped objective
   `J=RMS_signed-B + RMS_paired-|B| + 0.5*RMS_C-sector` and the frozen
   lambda grid `{1,3,10,30,100}`. Use current T3 only as a compatibility
   constraint or rejection screen. It may influence development, never
   acceptance.
3. Obtain a clean uninterrupted baseline T3 development acquisition first
   only if a formal equal-tool joint objective is selected.
4. Freeze the family, exact sum-versus-average objective normalization,
   regularization and penalty grid, dense correction bound, coefficients,
   scorer, and hashes before candidate motion.
5. In a formal joint fit, use equal total tool weight and one nuisance center
   per complete tool acquisition. Do not fit per-pose or incomplete-source
   translations.
6. Keep T4 paired-|B| blocks and antipodal-C pairs outside each nested
   training fold. No held response may affect scaling or selection.
7. Keep the R2 ten-term family fixed, retain the collision-unidentified
   sin(2C) exclusions, and strongly regularize the three unstable terms with
   predeclared penalty multipliers rather than response-driven term deletion.
8. Require each tool to meet equal-pose and raw `0.120 / 0.280 mm` ceilings,
   at least 10% plus `0.010 / 0.020 mm` RMS/maximum improvement, positive-
   and negative-B improvement, B0 worsening no more than `0.010 mm`, and
   unique-pose worsening no more than `0.050 mm`.
9. Bound the primary and every nested refit to `0.700 mm` on a dense complete
   configured B[-100,+100]/C-cycle audit, with exact zero correction at B0/C0.
10. After freezing R3, acquire an untouched uninterrupted T4 `101/28`
    validation and a fresh predeclared shorter T3 verification covering every
    acceptance gate, both B signs, and the B+90/C0 and C270 endpoints. Freeze
    its exact poses and closure contract before motion. Neither run may trigger
    coefficient tuning.

Only a repeatable pose field common to both tools is eligible for the shared
TCPC surface. Acquisition translations, probe reseat/insertion behavior,
spindle or stylus eccentricity, rail-position straightness, electrical pulse
faults, and unexplained T3/T4 differences remain in the mechanical and
measurement error budget. A length-dependent vector term requires separate
reseat and clocking evidence before it is physically identifiable.
