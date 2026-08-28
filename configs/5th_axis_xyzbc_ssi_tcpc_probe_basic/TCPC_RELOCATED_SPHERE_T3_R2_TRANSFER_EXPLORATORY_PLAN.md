# Relocated-Sphere T3 R2-Transfer Exploratory Plan

Status: `EXPLORATORY BASELINE-ONLY`; `R2 NOT ACCEPTED`.

This plan freezes campaign `2026082601`, mode `30`, attempt `1`. It collects
one uninterrupted 31-row T3 dataset under the existing baseline correction.
It is not the previously planned formal mode-24 T3 acceptance run, does not
load R2, and cannot accept R2 or authorize a production change.

## Scope And Frozen Identity

- runner: `nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc`
- runner SHA-256: `90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5`
- diagnostic INI: `5th_axis_xyzbc_ssi_tcpc_probe_basic_task_capture_t3_exploratory_a1.ini`
- diagnostic INI SHA-256: `347a0bfb9f616875fa7c68a24d9134269a0e4dce967deca11b21d278a2b49a47`
- campaign / mode / attempt: `2026082601 / 30 / 1`
- tool: T3/H3 short probe, live Z length `128.606729 mm`
- probe ball / sphere: `6.000000 / 30.000000 mm`
- frozen probe calibration: `#3032=0.117658`
- accepted rows / source-local closures: exactly `31 / 14`
- programmed holds: exactly one initial, pre-motion `M0`

The dedicated INI is derived from the baseline task-capture configuration and
adds only observation counters. The existing persistent baseline correction
must be enabled. The R2 overlay must be absent. The runner read-checks all 30
pins that R2 would change against their baseline totals before the hold,
during live guards, before motion, and before logging; it writes no correction
coefficient or enable pin.

## Exact Pose Schedule

Every pose uses two complete four-contact passes: W, sign-aware upper U, -V,
and +V. A bounded quality rejection permits at most one complete-pose retry.

| seq | block | anchor | pose | role |
| ---: | ---: | ---: | --- | --- |
| 1 | 100 | 1 | B0 C0 | opening B0 reference |
| 2 | 100 | 2 | B0 C90 | opening B0 quadrant |
| 3 | 100 | 3 | B0 C180 | opening B0 quadrant |
| 4 | 100 | 4 | B0 C270 | opening B0 quadrant |
| 5 | 100 | 5 | B0 C0 | opening B0 block closure |
| 6 | 45 | 1 | B+45 C0 | B+45 open |
| 7 | 45 | 2 | B+45 C90 | B+45 quadrant |
| 8 | 45 | 3 | B+45 C180 | B+45 quadrant |
| 9 | 45 | 4 | B+45 C270 | B+45 quadrant |
| 10 | 45 | 5 | B+45 C0 | B+45 closure |
| 11 | -45 | 1 | B-45 C0 | B-45 open |
| 12 | -45 | 2 | B-45 C90 | B-45 quadrant |
| 13 | -45 | 3 | B-45 C180 | B-45 quadrant |
| 14 | -45 | 4 | B-45 C270 | B-45 quadrant |
| 15 | -45 | 5 | B-45 C0 | B-45 closure |
| 16 | 500 | 1 | B0 C0 | midpoint reference |
| 17 | 90 | 1 | B+90 C0 | B+90 open |
| 18 | 90 | 2 | B+90 C90 | B+90 quadrant |
| 19 | 90 | 3 | B+90 C180 | A5 failing-pose transfer target |
| 20 | 90 | 4 | B+90 C270 | B+90 quadrant |
| 21 | 90 | 5 | B+90 C0 | B+90 closure |
| 22 | -90 | 1 | B-90 C0 | B-90 open |
| 23 | -90 | 2 | B-90 C90 | B-90 quadrant |
| 24 | -90 | 3 | B-90 C180 | paired-sign target |
| 25 | -90 | 4 | B-90 C270 | B-90 quadrant |
| 26 | -90 | 5 | B-90 C0 | B-90 closure |
| 27 | 200 | 1 | B0 C0 | closing B0 reference |
| 28 | 200 | 2 | B0 C90 | closing B0 quadrant |
| 29 | 200 | 3 | B0 C180 | closing B0 quadrant |
| 30 | 200 | 4 | B0 C270 | closing B0 quadrant |
| 31 | 200 | 5 | B0 C0 | closing B0 block closure |

Transitions retract along the current W vector to top-clear, lift `25 mm` in
machine Z, index at high Z, move XY, and then lower Z. B changes occur at C0;
a B-sign change transits through B0/C0. No nonzero-B C135/C315 or tilted
oblique pose is in this run.

## Exact Closure Contract

Every closure is wholly inside attempt 1 and has a hard `0.050 mm` norm limit.

| closure ID | open -> close | pose | purpose |
| ---: | ---: | --- | --- |
| 100 | 1 -> 5 | B0 C0 | opening B0 sweep |
| 45 | 6 -> 10 | B+45 C0 | positive mid-B block |
| -45 | 11 -> 15 | B-45 C0 | negative mid-B block |
| 905 | 5 -> 16 | B0 C0 | opening-to-midpoint drift |
| 90 | 17 -> 21 | B+90 C0 | positive high-B block |
| -90 | 22 -> 26 | B-90 C0 | negative high-B block |
| 911 | 1 -> 27 | B0 C0 | opening/closing phase pair |
| 906 | 16 -> 27 | B0 C0 | midpoint-to-closing drift |
| 912 | 2 -> 28 | B0 C90 | opening/closing phase pair |
| 913 | 3 -> 29 | B0 C180 | opening/closing phase pair |
| 914 | 4 -> 30 | B0 C270 | opening/closing phase pair |
| 915 | 5 -> 31 | B0 C0 | opening/closing phase pair |
| 200 | 27 -> 31 | B0 C0 | closing B0 sweep |
| 900 | 1 -> 31 | B0 C0 | whole-run closure |

A failed closure is logged before the runner aborts. It must not be bypassed.

## A5-Driven Diagnostic Logic

The translated four-source A5 composite passed 11 of 12 frozen R2 diagnostic
calculations. Its sole failure was maximum unique-pose worsening at B+90/C180:
`0.090202 > 0.075000 mm`. That source row had a clean `0.001930 mm` two-pass
center delta and belonged to a block with a `0.009112 mm` local closure, so it
must not be discarded as a bad touch. A5 nevertheless remains a four-source,
three-translation diagnostic rather than formal same-acquisition evidence.

The mode-30 analysis therefore uses these predeclared rules:

1. Establish acquisition eligibility first: exact 31 result and state rows,
   exact pose order, all 14 closures passing, correct campaign/mode/attempt,
   T3/H3 and baseline state invariant, and no terminal contact/gap trace fault.
2. Never splice attempts, apply source translations inside this run, remove an
   eligible pose, or specially exclude B+90/C180 after viewing its value.
3. For each tilted block, form the translation- and first-order-drift-resistant
   local contrast
   `D(B,C) = center(B,C) - mean(center(B,C0-open), center(B,C0-close))`
   for C90, C180, and C270.
4. At each absolute B and C, report paired-sign components
   `even=(D(+B,C)+D(-B,C))/2` and `odd=(D(+B,C)-D(-B,C))/2`.
   B+90/C180 and B-90/C180 are mandatory primary readouts; B+/-45 provides
   the predeclared angle-scale check instead of a post-hoc pose search.
5. Separately average repeated identical poses within this acquisition to 20
   equal-weight unique poses. Report globally centered T3 RMS/max before and
   after an offline frozen-R2 counterfactual, with each pattern centered by
   its own 20-pose mean.
6. The R2 counterfactual must use the already frozen ten-term lambda-10 R2
   totals and T3/H3 kinematics. T3 may not select terms, coefficients, signs,
   scale factors, translations, exclusions, thresholds, or a new fit.
7. Compare the T3 local contrasts with the immutable mode-23 T4 baseline using
   the same formulas. Use the 14 closures and per-pose pass-center deltas as
   the observed repeatability/drift context. An isolated B+90/C180 difference
   is not robust tool-length evidence; support requires coherent paired-sign,
   quadrant, and B45/B90 behavior beyond that context.

Because T3 and T4 are different physical probe assemblies, even coherent
evidence is described only as tool/probe-assembly transfer evidence. This
experiment cannot uniquely separate active tool-length dependence from probe
seating, stylus eccentricity, or a common spindle/probe vector.

These calculations are exploratory readouts, not new acceptance gates. A
favorable T3 counterfactual does not cure the failed A5 T4 gate.

## Output Contract

Attempt 1 writes only these dedicated, initially header-only files:

- `tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-results.csv`
- `tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-state.csv`
- `tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-closures.csv`
- `tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-contact-trace.csv`
- `tcpc-relocated-sphere-t3-r2-transfer-exploratory-attempt1-gap-trace.csv`

The completed result/state/closure counts must be exactly `31 / 31 / 14`.
Contact and inter-contact gap traces must reconcile every attempted G38
transaction, including any bounded rejected-pose retry. Retain all raw rows;
do not delete retry traces or average them into accepted-row provenance.

Once any G38 transaction or accepted row has occurred, these attempt-1 files
are immutable evidence. Do not truncate, clear, append a restarted run, or
reuse them.

## Operator Setup And Sole M0

Only the operator may launch LinuxCNC, enable, home, install or reseat T3,
apply tool length or TCPC, position, load the runner, Cycle Start, Resume,
Feed Hold, Abort, or make recovery motion.

Before loading:

1. Clean-start only the dedicated T3 exploratory INI. Confirm the R2 overlay
   is absent and the persistent baseline correction is enabled.
2. Confirm the base HAL remains the reviewed baseline, all five axes are
   homed, B/C SSI feedback is valid, TWP is clear, and the spindle is stopped.
3. Install T3 in its normal keyed state. Establish T3/H3 and `G43 H3` before
   `G43.4`; confirm all three live Z-offset views read `128.606729 mm`.
4. Secure the certified 30 mm sphere with the post direction X-,Y+,Z-. Confirm
   the probe input is released and the five output files contain headers only.
5. At B0/C0, place the T3 ball 3-5 mm above the sphere at the reviewed top
   point. Keep direct observation and feed-hold/stop control available.

Cycle Start may advance only to the runner's sole pre-motion `M0`. At that M0,
the operator must explicitly confirm current physical clearance for the T3
body, holder, cable, sphere, post, every listed pose, and every high-Z transit,
including B+90/C180 and B-90/C180. Historical runs and configured-limit replay
do not establish physical clearance at the relocated sphere. There are no
intermediate inspection holds. Resume once only after that confirmation; do
not jog, use MDI, change WCS/tool state, or reseat the probe during the run.

## Abort, Reseat, And Attempt Boundary

Any operator Abort, program abort, missed touch, incomplete run, manual
recovery that breaks continuity, or probe removal/reseat retires attempt 1.
Preserve all five partial outputs and runtime evidence. Do not resume or splice
the partial. Return to a reviewed safe state under operator control, prepare a
new runner and five new output names with the next attempt ID, and repeat the
offline preflight before motion. A runner-managed bounded whole-pose quality
retry is the only retry allowed inside one attempt.

## No-Fit And Release Boundary

`R2 IS NOT ACCEPTED.` This campaign is baseline-only and diagnostic. Do not:

- load the R2 overlay for T3 motion;
- refit, tune, rescale, or select R2 from these T3 rows;
- use T3 to remove the A5 B+90/C180 failure;
- relabel A5 as a formal uninterrupted T4 pass;
- authorize the formal mode-24 T3 stage or a production HAL/INI change.

Any later candidate or release requires a separately declared campaign,
pre-motion frozen scoring and artifacts, independent review, and its own
formal same-acquisition acceptance evidence.
