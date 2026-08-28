# TCPC Baseline Campaign 2026082202

Status: T3 attempts 1-2 are retired zero-row starts. Attempts 3, 4, and 5 are
excluded sequence-1-to-10, sequence-1-to-3, and sequence-1-to-2 partials. The
two Attempt-6 executions are excluded as a zero-row electrical/probe-state
fault. `blank.ngc` is loaded and T3 is 100 mm clear for a physical reset.
Attempt 7 is prepared but barred until the probe is reseated and passes the
no-motion electrical qualification.

Started: `2026-08-22 +07`

Authoritative procedure: `TCPC_POSITIVE_B_C45_BASELINE_PLAN.md`

## Owner Request

Run the calibrated T3 short probe followed by the calibrated T4 long probe on
the fixed certified 30 mm sphere. Measure the current correction at B0, B+5,
B+15, and B+30 using safe C45 sectors, then review the first error baseline
before choosing further calibration work.

The sphere is on a 45-degree post running base-to-sphere in `X+, Y-, Z+`.
C135/C315 are excluded at nonzero B from historical collision evidence. C45
and C225 remain measured watch sectors. No unsafe slot will be inferred.

## Superseded Prepared Run

Campaign `2026082201` S1 mode-17 attempt 2 was prepared and load-checked but
superseded before any axis/probe motion or CSV row. At supersession LinuxCNC was
idle at line 0 and the paired CSV remained 30 physical lines with SHA-256
`70ba9ef3748bc1f50188160831928cc0f49185690b5951d53563368fd8ab1972`.
Its exact armed runner hash
`9e370c91f49f0ca78d7cef1a5e3ccb3a472df1dd1afd2a899c452249c3580f49`
is preserved in its pre-run directory. Attempt ID 2 is retired; any future
mode-17 restart must use attempt 3. Attempt 1 remains excluded `13/20` partial
evidence and cannot be spliced.

## Current Machine Handoff

- After attempt 5, `milltask` and `halui` were found absent while the GUI and
  realtime processes remained. LinuxCNC was fully shut down and relaunched;
  the healthy server/IO/HALUI/realtime/milltask/Probe Basic process set is
  present, and the operator completed Home All. That controller recovery
  remains healthy.
- Attempt 6 was started twice with the exact same runner and selector. Severe
  false trips required operator-controlled pauses/resumes. The operator saw
  the probe in its known bad electrical state, including faint LED glow.
- The second execution completed one B0/C0 first pass, but its center was
  displaced `0.709062 mm` from the mean of four prior accepted B0/C0 centers.
  Pass 2 did not complete and no summary row was written. Attempt 6 is excluded
  in full; it cannot support calibration or mechanical inference.
- The operator stopped, returned X/Y/B/C to zero, and retracted Z exactly
  100 mm clear. Four samples were interpreter-idle, queue zero, in position,
  and zero velocity at commanded machine XYZ
  `1024.747449/444.756916/-282.166128 mm`, B/C `0/0 deg`.
- `blank.ngc` is loaded with zero position change. T3/H3 `128.606729 mm`
  remains the software selection, TCPC and the persistent correction remain
  active, and TWP is clear. LinuxCNC still reported enabled at the last sample;
  the operator must apply E-stop/disable before removing T3.
- Each revised exact runner restores its own accepted frozen `#3032` after
  exact live-tool and TLO validation, before calculating any probe geometry.
  T3 writes `0.117658`; T4 writes `0.154742`. Preview exits before the write,
  and later live guards abort on any change. This is frozen-state restoration,
  not offset requalification.
- Attempt 6 exposed a conflict: the abnormal-pulse oneshot was ORed into
  `halui.program.pause`, preventing the runner's own clear-settle loop from
  recovering automatically. The saved Attempt-7 design restores pendant-only
  pause wiring and converts the oneshot to a monitor-only `0.5 s` event latch.
  The G38-only realtime probe gate, 10-second quarantine, 20-second continuous-
  clear proof, and 60-second hard timeout remain. The saved changes are not
  live until a controlled HAL update or restart.
- `qualify_tcpc_probe_reset.py` provides the required read-only reset checks:
  disabled untouched soak, three deliberate deflections, final disabled soak,
  and powered-idle soak. Any LED glow, spontaneous/repeated edge, or raw/mux
  mismatch bars Attempt 7.
- Live tool number and all three T3 Z tool-length sources were correct, but
  `halui.tool.diameter` reported stale `0.201` metadata rather than the physical
  6 mm ball. The dedicated exact-tool runners freeze `6.000 mm` as an immutable
  campaign constant and still enforce live tool number plus all three TLO
  sources. No controller tool-table reload was performed.

Runtime observations must be revalidated after any motion, hold, restart,
enable change, tool change, or physical intervention.

## Frozen Experiment State

```text
campaign: 2026082202
stage/mode: 19
T3 leg/attempt: 1 / 7
T4 leg/attempt: 2 / 1
T3 offset: 0.117658 mm
T4 offset: 0.154742 mm
output: tcpc-positive-b-c45-baseline-results.csv
grid: tcpc-positive-b-c45-baseline-grid.csv
```

No offset recalculation is planned. The prior repeat-ring waiver must be
explicitly reconfirmed after the electrical-fault reseat; no ring cycle will be
inserted or skipped silently. No geometry, correction, zero, backlash, rail,
or tool-table change is authorized from this baseline alone.

## Data State

- Baseline CSV: ten excluded attempt-3 rows, three excluded attempt-4 rows,
  and two excluded attempt-5 rows.
- Attempts 1-2 and 6 logged no rows. Attempts 3-6 must not be resumed or
  spliced.
- Required accepted rows: 31 per complete leg.
- Unsafe canonical slots: `13,17,22,26,31,35`.
- Prior paired and ring CSV files remain unchanged.
- Initial frozen pre-run evidence:
  `calibration_runs/20260822_1737_positive_b_c45_baseline_pre_run/`.
- Attempt-3 partial:
  `calibration_runs/20260822_1855_positive_b_c45_T3_attempt3_partial_seq1_10/`.
- Attempt-4 pre-run:
  `calibration_runs/20260822_1903_positive_b_c45_T3_attempt4_pre_run/`.
- Attempt-4 partial:
  `calibration_runs/20260822_2050_positive_b_c45_T3_attempt4_partial_seq1_3/`.
- Attempt-5 pre-run:
  `calibration_runs/20260822_2110_positive_b_c45_T3_attempt5_pre_run/`.
- Attempt-5 partial:
  `calibration_runs/20260822_2210_positive_b_c45_T3_attempt5_partial_seq1_2/`.
- Superseded Attempt-6 pre-run, preserved before the controller task-process
  loss was understood:
  `calibration_runs/20260822_2220_positive_b_c45_T3_attempt6_pre_run/`.
- Revised Attempt-6 pre-run after clean restart and frozen-offset self-restore:
  `calibration_runs/20260822_2302_positive_b_c45_T3_attempt6_pre_run_r2/`.
- Attempt-6 zero-row electrical-fault record:
  `calibration_runs/20260822_2347_positive_b_c45_T3_attempt6_zero_row_probe_electrical_fault/`.

```text
14e3f59d8a46fc9b82bc7c1b683c2d3406827363730d9102c72ccfe00628a13c  prepared T3 attempt-7 runner
e816cc4c9e27a636726db6640c0c3ceab092b0dd3672d1fb36ea145650c18967  prepared T4 runner
4e4918cce60d8ea2130a1605fb46f0d555b5722179274f6036c42a040c765e1a  analyzer
e9d50c8cddde601b17274c64733a2324ffd3ed0a47da3671bcc351c3d66ccbd8  grid
53bd0e3ca122d9001419634ba8b095a0140fd71a418472cbb5dec2855da406bd  baseline CSV with excluded attempts 3-5
b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778  prepared HAL with 10-second quarantine and 0.5-second event latch
26f2833cfb0c35b3d5653a507503dc7f5925e5eb7b12a15de3807f1e2557c727  prepared pendant-only xhc pause wiring
bbbdc8aa28ea80c318a0dda3044ebcd0d9fa614557a1afe18721fbd7467cf934  read-only probe reset qualifier
02c8811a25a04263f0e14b0ec180cf592d9d5882714973e7ef8bd6fdb793874b  disarmed legacy sphere runner
15ded0868408874749a74e0690989372482394ad94002367643010de848cdff5  disarmed ring verifier
8bd5774727d4af217fc2827b5f0a9e06549c3e91bdc7211ebfd78ec5712df569  revised attempt-6 pre-run MANIFEST.md
d2425e713f1ddcaf9d7773076162d58aa49ac8ab1a3c4c2025be516af61e128a  attempt-6 zero-row electrical-fault MANIFEST.md
```

The analyzer self-test and compile check pass. `--leg-only 1` currently
returns data-quality exit `1` because there is no complete T3 attempt. After
attempt 7, it must exit `0` before tool change; after T4, default two-leg mode
must exit `0` before any calibration decision.

## T3 Attempt History

- Attempt 1 was physically executed twice from a start about 8.3 mm above
  contact; both bounded 7 mm top searches missed. Attempt 2 is retired unused
  because the second physical execution reused selector 1.
- Attempt 3 accepted B0 sequence 1-9 and B+5/C0 sequence 10. B0 closure norm
  was `0.003833 mm`. The unlogged B+5/C45 first pass then exceeded the
  `30.5 mm` U-diameter acquisition gate, so the attempt stopped and is
  excluded.
- At the owner's request, both runners now use a wider pass-1 acquisition-only
  diameter range of `29.5-31.0 mm` and emit the failed value. Accepted pass 2
  remains restricted to `29.9-30.5 mm` and `0.10 mm` U/V residual.
- Attempt 4 accepted sequences 1-3. At B0/C135, pass 1 was plausible
  (`30.145788/30.142455 mm` U/V diameters), but a delayed pulse straddled the
  pass-2 top G38 and became an approximately `0.000060 mm` zero-travel false
  contact. The strict U-diameter gate aborted below `29.9 mm`; the partial is
  excluded.
- Attempt 5 accepted sequences 1-2 at B0/C0 and B0/C45. Both unexpected pauses
  followed valid contacts during retract/return motion outside G38. The
  realtime motion gate protected the measurements, but the then-current `1 s`
  abnormal-monitor ignore was too short. The operator stopped at B0/C90 and
  moved T3 up and clear; the partial is excluded.
- Attempt 6 was executed twice under the same selector while the probe showed
  its known electrical fault and faint LED glow. Its second execution produced
  one corrupted B0/C0 pass-1 center displaced `0.709062 mm`; pass 2 did not
  complete, the CSV remained unchanged, and the attempt is excluded zero-row.
- Attempt 7 keeps the 10-second quarantine and 20-second continuous-clear
  proof, but a late pulse now drives only a `0.5 s` event latch sampled by the
  runner. It no longer pauses the interpreter. Attempt 7 remains barred until
  the physical reset and electrical qualification pass.

## Inspection Holds

- Initial Cycle Start: mandatory pre-motion M0.
- First B+5/C0: top-clear body/post inspection.
- B+30/C0: top-clear body/post inspection.
- B+30/C45 and B+30/C225: high-Z pre-descent inspection, controlled
  `200 mm/min` descent, then top-clear inspection before probing.

Every hold freezes XYZ and revalidates selectors, coordinate state, live
machine/tool/TCPC/probe state, and commanded/feedback/SSI rotary pose. The
long-probe swept-body clearance remains an operator physical check.
