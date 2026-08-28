# T3 R2 Transfer Closeout And R3 Plan

Date: `2026-08-26`

## Disposition

- The T3 acquisition is complete, sealed, and electrically valid.
- R2 is **not accepted** for live calibration use.
- No TCPC coefficient, B/C zero, rigid geometry, tool-table value, probe
  scalar, INI, or production HAL value is authorized to change.
- The next work is offline R3 feasibility and model selection. No operator or
  machine motion is required until one candidate, runner, analyzer, hashes,
  correction envelope, and numerical gates are frozen.

The deterministic feasibility stage is complete:

```text
assess_tcpc_r3_feasibility.py
  4520081bb7e7b4088a555e498ad7e6430dd3f5fc2d3d93a8a1e4c9867eaa6dd1
TCPC_R3_FEASIBILITY_REPORT.md
  5b5b747e7c3f5ef0df9a0c5e41a5518e0a6f281a79917df5388c1d015d29bee2
```

Its disposition is `NO R3 COEFFICIENTS RELEASED`. The self-test, deterministic
report check, Python compile, archive hash guards, semantic T3
state/contact/gap/closure checks, arbitrary-output-path rejection, and static
diff checks pass.

## Completed Evidence

The direct T3 composite owns all 31 requested rows without averaging or source
translation:

```text
A1 owns sequences 1-14
A2 owns sequences 15-22
A4 owns sequence 23
A5 owns sequences 24-31
```

Attempt 5 completed exact sequences 24-31 with `8/8/1` result, state, and
closure rows plus `64/64` contact and gap traces. All 64 direct probe contacts
advanced raw/mux/gated counters by exactly `1/1/1`; every repeat and gap delta
was `0/0/0`. No touch, release, state, pose, closure, or terminal-fault gate
failed. Its B0 closure was `0.008580 mm`.

The immutable archive is:

```text
calibration_runs/20260826_1612_campaign2026082601_t3_exploratory_attempt5_complete
MANIFEST.md  d93982d4c47798d9f841c8ac4840635fb4ea73d5d231a50e593eeecda552aaa6
SHA256SUMS   ef9e1c3957a9c2c30011d2f8c127737df53ab5a10b3f70bc1bab82b28c2ff03b
```

The frozen four-source report is
`TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_ATTEMPT5_FOUR_SOURCE_REPORT.md`,
SHA-256
`0a7176f6fcb3edc00c4dc461fe3b39c3d750c499f8f907400d3a2b0ce3095a07`.

## R2 Result

R2 improves the common pose field but fails three predeclared transfer gates:

| metric | baseline | R2 counterfactual | limit/result |
| --- | ---: | ---: | --- |
| T3 equal-20 RMS/max | `0.251155 / 0.617559` | `0.148716 / 0.328314` | FAIL `0.120 / 0.280` |
| T3 raw-31 RMS/max | `0.221011 / 0.650680` | `0.149044 / 0.352450` | FAIL `0.120 / 0.280` |
| maximum pose worsening | n/a | `+0.119219` at B+90/C0 | FAIL `0.075` |

Positive-B RMS improves only about `11.8%`; negative-B RMS improves about
`62.8%`. B+90/C180 controls both remaining maximum-error ceilings. B+90/C270
also worsens by `0.078339 mm`.

At B+90/C0, the direct R2 correction is approximately
`[-0.007605,+0.075153,+0.088334] mm`. It is dominated by `b_sin.z` and the
unstable `bc_sinb_cos2c` X/Y vector. At B+90/C270, large opposing cross-term Y
contributions overshoot while the X terms add. The failure is a high-B
transfer/model problem, not a bad touch.

## Identifiability Boundary

- T4 baseline pose error is about `0.201 / 0.711 mm` RMS/max while its
  same-acquisition closure is only `0.0148 / 0.0271 mm`. A repeatable
  pose-dependent field is therefore present well above touch noise.
- Centered T3-minus-T4 mismatch is `0.164424 / 0.264629 mm`. A correction
  common to both tools cannot remove this mismatch; it can only choose a
  compromise.
- The B0 C sweep contains a repeatable rotating effective probe/spindle vector
  of roughly `0.034-0.050 mm` over the `100.800271 mm` tool-length difference.
  This is consistent with an effective angle around `0.024-0.029 deg`, but the
  two probe assemblies at one artifact height cannot separate spindle tilt,
  keyed probe eccentricity, seating, B zero, and Z-rail/head geometry.
- Existing rigid and zero fits are ill-conditioned and do not transfer. No B
  zero, C zero, pivot, per-tool XY, or rail correction is authorized.
- Current within-run repeatability is commonly `10-30 um`; between-source or
  reseat shifts reach `20-70 um`. A global sub-10 um claim is unsupported.

## R3 Offline Contract

R3 remains inside the existing TCPC tuning-pin surface. It must not add or fit
physical B/C zeros, rigid geometry, tool-table offsets, or a new tool-vector
kinematics term.

1. Use the immutable T4 mode-23 101-row baseline as primary evidence.
2. Treat the current split T3 composite and the split T4 R2 validation as
   consumed development/stress evidence, never as untouched acceptance data.
3. Keep the existing ten-term R2 family as the maximum family. Keep the
   unidentified nonzero-B sin(2C) terms excluded.
4. Penalize or constrain the selection-unstable `b_sin2`,
   `bc_sinb_cos2c`, and `bmid_cos2c` groups. Audit every candidate on the full
   configured B range `[-100,+100]` and a complete C cycle.
5. Require correction exactly zero at B0/C0 and a dense correction maximum no
   greater than `0.700 mm` for the primary fit and every selection refit.
6. Do not nominate a candidate unless both tools have useful numerical margin
   to the frozen `0.120 / 0.280 mm` RMS/max ceilings in development scoring.
7. Freeze the model, pin totals, runner, analyzer, hashes, reachability replay,
   and all gates before any candidate configuration is loaded.

The stable seven terms alone are not adequate: their representative
lambda-30 fit gives approximately `0.111474 / 0.288058 mm` on T4 training and
`0.151898 / 0.352274 mm` on the T3 design set. A shared ten-term compromise is
numerically feasible but currently has little margin, so no R3 coefficient is
released by this closeout.

The fixed ten-term feasibility illustration demonstrates that limitation. A
sum-loss lambda-30 case gives T4 equal-76 `0.106656 / 0.247541 mm`, T3 equal-20
`0.117686 / 0.268980 mm`, and T3 raw-31 `0.124315 / 0.291521 mm`. Under the
equivalent equal-tool averaged-loss lambda-30 normalization, the T3 equal-20
RMS moves outside the limit at `0.121014 mm` and raw-31 remains outside at
`0.126287 / 0.297833 mm`. The apparent equal-20 crossing is therefore not
normalization-robust and cannot nominate a live candidate.

## Next Machine Evidence

After R3 is frozen, use T4/H4 first. The minimum development screen is one
uninterrupted 31-row run:

```text
B0:   C0,90,180,270,0
B+45: C0,90,180,270,0
B-45: C0,90,180,270,0
B0/C0 midpoint
B+90: C0,90,180,270,0
B-90: C0,90,180,270,0
B0:   C0,90,180,270,0
```

This screen is not a full-domain release. A release over the existing measured
domain requires a fresh uninterrupted T4 101-row/28-closure candidate run,
followed without retuning by a fresh uninterrupted T3 31-row/14-closure
transfer run. The sphere must remain fixed. The T3 and T4 runs can be separate
controller acquisitions, but each tool run must be internally uninterrupted.

The 14 short-grid closures are:

```text
1->5, 6->10, 11->15, 5->16, 17->21, 22->26,
1->27, 16->27, 2->28, 3->29, 4->30, 5->31,
27->31, 1->31
```

Every closure must be at most `0.050 mm`. No pose, especially B+90/C180, may
be excluded after measurement.

## Probe Contract

- Laser cutting remains off for the whole acquisition.
- After installation, two manual deflections must advance raw and mux counters
  twice while the G38-gated counter remains unchanged.
- Require a 30-second quiet qualification before loading and again at the sole
  initial M0.
- Gate `motion.probe-input` only during G38.
- Before each G38, require two clear `0.05 s` samples within a bounded `10 s`
  settle window, followed by immediate final guards.
- Each accepted direct touch must be exact raw/mux/gated `1/1/1`.
- Matched raw/mux repeats or gap pulses are diagnostic only when gated delta is
  zero. Abort on any gated gap/repeat, raw/mux mismatch, no-touch, held
  release, counter reversal, or settle timeout.
- Do not add a fixed 20-second dwell or pulse-width debounce. Good and false
  pulse widths overlap.
- A reseat, skipped pose, manual recovery, or cross-file splice retires that
  acquisition as formal evidence.

No ring verification is required unless the probe ball, stylus, or frozen
scalar `#3032` calibration changes.
