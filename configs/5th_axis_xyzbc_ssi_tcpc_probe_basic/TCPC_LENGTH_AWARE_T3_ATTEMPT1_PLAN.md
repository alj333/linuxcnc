# TCPC Length-Aware T3 Attempt 1 Plan

Status: `READY - OFFLINE PREFLIGHT PASS; NOT LOADED OR RUN`

## Purpose

This is the short-probe verification leg for the startup-only length-aware
model. The completed T4 Attempt 2 validated the common bank at `q=0`; this
run evaluates the T3/H3 endpoint at `q=1` using the frozen 31-row T3 schedule.
It collects verification evidence only. It does not fit coefficients, change
the kinematics, authorize production release, or append any earlier T3 data.

## Frozen Identity

- campaign / mode / attempt: `2026082602 / 33 / 1`
- model ID / expected model ID: `2026082601 / 2026082601`
- model scale: exactly `q=1`
- tool: `T3 / H3 / 128.606729 mm`
- probe ball / sphere: `6.000000 / 30.000000 mm`
- probe calibration: `#3032=0.117658`
- configuration: `5th_axis_xyzbc_ssi_tcpc_probe_basic_length_model_validation_2026082601.ini`
- runner: `nc_files/calibration/tcpc_length_aware_t3_validation_2026082601_attempt1.ngc`
- runner SHA-256: `d6158b9ff91f5fa73a11071d314c64a442d6747f6758587415ece7c867e53bd6`
- validator:
  `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/validate_tcpc_length_aware_t3_attempt1.py`
  SHA-256 `88ddd9a4ead0d5a461cb7de7caa919cb878e0dcaf9dcf7633902abd86a8fbdae`
- preflight report:
  `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/TCPC_LENGTH_AWARE_T3_ATTEMPT1_PREFLIGHT_REPORT.md`
  SHA-256 `dc09e6df1b77426fcdb1530fda1c146cec831758a37480450a154e7e208523d0`
- read-only pre-run archive:
  `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1119_campaign2026082602_t3_length_aware_attempt1_preflight`
- motion/grid source runner:
  `nc_files/calibration/tcpc_relocated_sphere_t3_r2_transfer_exploratory_attempt1.ngc`
  SHA-256 `90ce79b0457e3148113dd5763506d14fd29c331afc3017b29fe6ae4d87494ab5`
- safety-source runner: T4 Attempt 2 SHA-256
  `d27a83ac73404dac8fb65426afea34683a38366b9a59584ec7f8a480d4b0884d`
- accepted / unique poses: exactly `31 / 20`
- closures: exactly `14`
- contact / gap traces: exactly `248 / 248`
- programmed holds: exactly one initial, pre-motion `M0`

## Exact Pose Schedule

Every pose uses two complete four-contact passes: W, sign-aware upper U, -V,
and +V. There is one acquisition try per pose and no whole-pose retry.

| seq | block | anchor | pose |
| ---: | ---: | ---: | --- |
| 1 | 100 | 1 | B0 C0 |
| 2 | 100 | 2 | B0 C90 |
| 3 | 100 | 3 | B0 C180 |
| 4 | 100 | 4 | B0 C270 |
| 5 | 100 | 5 | B0 C0 |
| 6 | 45 | 1 | B+45 C0 |
| 7 | 45 | 2 | B+45 C90 |
| 8 | 45 | 3 | B+45 C180 |
| 9 | 45 | 4 | B+45 C270 |
| 10 | 45 | 5 | B+45 C0 |
| 11 | -45 | 1 | B-45 C0 |
| 12 | -45 | 2 | B-45 C90 |
| 13 | -45 | 3 | B-45 C180 |
| 14 | -45 | 4 | B-45 C270 |
| 15 | -45 | 5 | B-45 C0 |
| 16 | 500 | 1 | B0 C0 |
| 17 | 90 | 1 | B+90 C0 |
| 18 | 90 | 2 | B+90 C90 |
| 19 | 90 | 3 | B+90 C180 |
| 20 | 90 | 4 | B+90 C270 |
| 21 | 90 | 5 | B+90 C0 |
| 22 | -90 | 1 | B-90 C0 |
| 23 | -90 | 2 | B-90 C90 |
| 24 | -90 | 3 | B-90 C180 |
| 25 | -90 | 4 | B-90 C270 |
| 26 | -90 | 5 | B-90 C0 |
| 27 | 200 | 1 | B0 C0 |
| 28 | 200 | 2 | B0 C90 |
| 29 | 200 | 3 | B0 C180 |
| 30 | 200 | 4 | B0 C270 |
| 31 | 200 | 5 | B0 C0 |

Nonzero B uses only C0/C90/C180/C270. C135/C315 and tilted oblique poses
remain excluded near the sphere post. The secured sphere-to-post direction is
`X- Y+ Z-`.

## Exact Closure Contract

Each closure has a hard `0.050 mm` norm limit and is logged before an abort.

| ID | open -> close | pose |
| ---: | ---: | --- |
| 100 | 1 -> 5 | B0 C0 |
| 45 | 6 -> 10 | B+45 C0 |
| -45 | 11 -> 15 | B-45 C0 |
| 905 | 5 -> 16 | B0 C0 |
| 90 | 17 -> 21 | B+90 C0 |
| -90 | 22 -> 26 | B-90 C0 |
| 911 | 1 -> 27 | B0 C0 |
| 906 | 16 -> 27 | B0 C0 |
| 912 | 2 -> 28 | B0 C90 |
| 913 | 3 -> 29 | B0 C180 |
| 914 | 4 -> 30 | B0 C270 |
| 915 | 5 -> 31 | B0 C0 |
| 200 | 27 -> 31 | B0 C0 |
| 900 | 1 -> 31 | B0 C0 |

The runner counts closure rows and requires exactly `14` before completion.

## Motion And Probe Safety

The physical motion and 31-pose grid are unchanged from the sealed T3 source
runner above. The guarded probe-transaction layer is unchanged from sealed T4
Attempt 2 apart from the dedicated output path and T3 wording:

- probe feed `50 mm/min`, transit feed `1200 mm/min`, rotary feed `200 deg/min`;
- top probe vector `7 mm`, top clearance `5 mm`, side clearance `4 mm`;
- side probe vector `6 mm`, side retract `3 mm`, machine-Z transit lift `25 mm`;
- retract along current W before the machine-Z lift;
- index at high Z, then XY, then lower Z;
- transit through B0/C0 at high Z before a B-sign change;
- no clearance-test motion and no hold after the initial `M0`.

The T3 probe calibration changes only the derived effective contact radius.
The HAL-qualified G38 gate, contact directions, two-clear-sample ready/release
guards, state guards, and motion ordering are otherwise unchanged.

## Duplicate-Pulse Contract

A successful G38 transaction may continue with zero, one, or two filtered
extra edges only when all of these conditions hold:

- direct raw and mux deltas match and contain at least one edge;
- exactly one direct gated edge reached motion;
- repeat raw and mux deltas match;
- no gated repeat occurred;
- total raw and mux deltas match;
- total raw-minus-gated extras are in the inclusive range `0..2`;
- G38 succeeded with valid travel;
- the probe passed the two-consecutive-clear-sample release guard.

Every extra is logged. The runner still aborts on a raw/mux mismatch, missing
or repeated gated edge, more than two combined extras, failed touch, failed
release, unstable pre-G38 state, model fault, or guarded machine-state change.

## Length-Model Contract

The read-only guard requires:

- model configured and valid, fault code zero;
- live and expected model IDs both `2026082601`;
- reference/span/minimum/maximum/tolerance/caps unchanged;
- evaluated tool length within `0.002 mm` of `128.606729 mm`;
- `q=1` within `0.000001`;
- differential XYZ and norm finite and within the `0.400000 mm` cap;
- total empirical XYZ and norm finite and within the `1.350000 mm` cap.

Each accepted pose logs the complete model-state snapshot. The coefficient
bank is startup-only and must not be sourced or reloaded during the run.

## Fresh Output Contract

These files are dedicated to this attempt and currently contain one header
line only:

- `tcpc-length-aware-t3-validation-2026082601-attempt1-results.csv`
  SHA-256 `9785983d8f89a4955082aa04d8a9e16bf2e2bdc00caccb4cd19f66e545416e93`
- `tcpc-length-aware-t3-validation-2026082601-attempt1-state.csv`
  SHA-256 `ac9e7ddd425e187444dd4ee339466a8e1713ca6e7104ccc76eba6076281427c7`
- `tcpc-length-aware-t3-validation-2026082601-attempt1-model-state.csv`
  SHA-256 `340cdd51e2507d7fbd41c8d4afdef911e83d3e5b4d3354d5fb84a83a7ea428cd`
- `tcpc-length-aware-t3-validation-2026082601-attempt1-closures.csv`
  SHA-256 `1f2e125d08ab2a0ea5d2210577c4a593f8cea1fc8cc348f67e3ed2a4a987437f`
- `tcpc-length-aware-t3-validation-2026082601-attempt1-contact-trace.csv`
  SHA-256 `df95e36f729b7bc1e1cef54bf4490ef8530f2e74d52e50671a4c452062c6bbe8`
- `tcpc-length-aware-t3-validation-2026082601-attempt1-gap-trace.csv`
  SHA-256 `e8e24f1617d5eb0bf637bdadc42f052d7e96130e808761ab07410cdb85e0d6e2`

Once any G38 transaction or accepted row occurs, this attempt is immutable.
Do not truncate, append a restarted run, resume from an intermediate pose, or
combine it with an earlier T3 acquisition.

## Current Verification Boundary

The full controller-off preflight passes. It covers source and runtime hashes,
the accepted T4 prerequisite archive, schedule, identity, output headers,
line length, ASCII, holds, trace topology, no-retry behavior, bounded pulse
filtering, model vectors, acceptance-metric mutations, and the isolated
in-tree RS274 parser. The current `headheadkins.c`, `headheadkins.so`, and
probe-counter HAL match the exact artifacts preserved with T4 Attempt 2.
LinuxCNC was not launched, the six outputs remain header-only, and
`/tmp/linuxcnc.lock` is absent.

## Result Acceptance

The post-run validator rejects the acquisition unless all of these gates pass:

- exact counts of `31/31/31` result/state/model-state rows, `14` closures, and
  `248/248` contact/gap transactions in strict try-1/pass/contact order;
- every closure at or below `0.050 mm`;
- raw-31 and equal-weight unique-20 centered RMS/max each at or below
  `0.120/0.280 mm`;
- same-acquisition H0 reconstructed as the observed q=1 center minus the
  offline `S+D` increment at that pose;
- for both raw-31 and equal-20, candidate RMS at most the smaller of 90% of H0
  or H0 minus `0.010 mm`, and candidate max at most the smaller of 90% of H0
  or H0 minus `0.020 mm`;
- positive-B and negative-B globally centered unique-pose RMS each improve by
  at least 10%, B0 RMS worsens by no more than `0.010 mm`, and no unique pose
  worsens by more than `0.050 mm`.

Passing these gates verifies the physical T3 endpoint and supports only the
T3-to-T4 length bracket. It does not validate extrapolation to shorter or
longer tools.

## Operator Setup And Run

Only the operator may enable, home, install/reseat T3, apply tool length or
TCPC, position, Cycle Start, Resume, Feed Hold, Abort, or make recovery motion.

1. Clean-launch only the dedicated revision-2026082601 validation INI and home
   all five axes.
2. Keep the spindle inverter isolated, spindle stopped, and laser off.
3. Install T3 in its keyed orientation, select T3/H3, and apply `G43 H3`
   before `G43.4`.
4. Confirm all non-Z tool offsets are zero and every live Z tool-offset view is
   `128.606729 mm`.
5. At B0/C0, position the T3 ball 3-5 mm above the secured sphere top.
6. Deflect T3 twice, confirm both releases, and observe 30 seconds of quiet.
7. Load the exact hashed runner and press Cycle Start once to the sole `M0`.
8. At M0, reconfirm the laser is off, physical clearance for the full schedule,
   and another continuously quiet 30-second interval.
9. Resume once. There are no later planned holds.

Do not jog, use MDI, change WCS/tool state, reseat the probe, or reload the
model during the acquisition. Any operator Abort, program abort, missed touch,
probe reseat, or manual recovery retires Attempt 1 and preserves all partial
outputs. A new attempt requires new filenames and another offline preflight.

## Completion Contract

A clean complete acquisition must contain exactly:

- `31` results;
- `31` machine-state rows;
- `31` model-state rows;
- `14` closures;
- `248` contact traces;
- `248` gap traces.

Offline validation and archive sealing are required after a clean LinuxCNC
shutdown. This T3 run verifies the differential endpoint; it does not itself
release the model for production or establish behavior beyond the tested tool
length range.
