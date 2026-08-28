# TCPC Positive-B C45 Short/Long Baseline Plan

Status: owner-directed campaign `2026082202` is reviewed and prepared for T3
short followed by T4 long. T3 attempts 3, 4, and 5 are excluded partials. The
two Attempt-6 executions are excluded as a zero-row electrical/probe-state
fault; their corrupted partial acquisition is not calibration evidence. The
operator stopped, returned B/C and X/Y to zero, retracted Z 100 mm clear, and
`blank.ngc` is loaded. Attempt 7 is prepared but barred until T3 is physically
reset and passes the documented no-motion electrical qualification.
This is a separate diagnostic from campaign `2026082201` paired modes 15-18. It
does not append to that campaign's CSV and does not complete or replace its
excluded mode-17 attempt 1.

## Purpose And Limits

Measure the current production-correction error on the certified 30 mm sphere
with the two calibrated probe lengths at B `0`, `+5`, `+15`, and `+30 deg` and
C in safe 45-degree sectors. The result is a first two-leg baseline used to
choose the next calibration work.

Keep these values frozen:

```text
T3/H3 short: length 128.606729 mm, ball 6 mm, #3032 0.117658 mm
T4/H4 long:  length 229.407000 mm, ball 6 mm, #3032 0.154742 mm
length separation: 100.800271 mm
```

The current persistent production correction stays enabled. Do not change
WCS, G52/G92, B/C zeros, TCPC geometry, correction coefficients, backlash,
tool X/Y, rail compensation, sphere position, probe feeds, or measurement
logic between legs.

Short then long without a closing short leg cannot separate tool length from
elapsed drift, spindle/probe reseating, rail position, trigger response, or
temperature. Positive B alone cannot separate B-sign parity or identify B-zero.
The dataset is diagnostic baseline evidence only and cannot authorize a model,
zero, tool-table, backlash, rail, or production-release change.

## Sphere Post Exclusion

The 45-degree support runs from its base to the sphere in `X+, Y-, Z+`; from
the sphere toward the base it is therefore `X-, Y+, Z-`.

Historical live evidence records C135 and C315 as collision sectors whenever B
is nonzero. They are mandatory omissions for both tools. C45 and C225 were
confirmed clear with T3 and remain watch sectors, not assumed-clear long-probe
poses. The programs never descend to or probe C135/C315 at tilted B. They do
rotate through those angles only at the established 25 mm high-Z transit.

## Canonical Grid

The companion file `tcpc-positive-b-c45-baseline-grid.csv` declares all 37
semantic slots. Required accepted rows retain their canonical slot number;
unsafe omissions remain gaps rather than being renumbered or imputed.

```text
slots  1-9:  B0   C0,45,90,135,180,225,270,315,0
slots 10-18: B+5  C0,45,90,[135 skip],180,225,270,[315 skip],0
slots 19-27: B+15 C0,45,90,[135 skip],180,225,270,[315 skip],0
slots 28-36: B+30 C0,45,90,[135 skip],180,225,270,[315 skip],0
slot      37: B0 C0 whole-run closure
```

Each leg therefore logs exactly 31 accepted rows. B changes occur only at C0.
Every later pose first retracts to the current tool-vector top-clear point,
lifts 25 mm in machine Z, indexes B/C, moves XY while raised, then descends to
the calculated top-clear point.

## Guarded Programs

```text
nc_files/calibration/tcpc_positive_b_c45_baseline_t3.ngc
  #711=19 #715=2026082202 #716=1 #717=0.117658 #727=7

nc_files/calibration/tcpc_positive_b_c45_baseline_t4.ngc
  #711=19 #715=2026082202 #716=2 #717=0.154742 #727=1
```

Both files freeze the known physical probe-ball diameter at `6.000 mm`; they do
not use the currently stale `halui.tool.diameter` metadata. The exact live T3
or T4 number and all three live Z tool-length sources remain mandatory guards,
and the diameter constant is snapshotted before the initial hold and checked
unchanged throughout the run.

Each exact runner also restores its own frozen ring-qualified `#3032` after
the exact live-tool and TLO guards pass: T3 writes `0.117658`, and T4 writes
`0.154742`. It immediately reads that value back before calculating probe
geometry, and later guards abort if it changes. Preview exits before the
assignment. The runners do not calculate or requalify either value.

Both files retain the reviewed two-pass sphere routine, bounded release guard,
tool/TLO/diameter checks, TCPC/TWP/correction checks, SSI checks, WCS/offset
immutability, rotary pose checks, and linear-axis state logging. Pass 1 is
acquisition-only and permits corrected diameters `29.5-31.0 mm`; accepted pass
2 remains `29.9-30.5 mm` with `0.10 mm` U/V residual and corrected-center
agreement limits. Every recorded contact must travel at least `1.0 mm`, and a
quality rejection permits one complete-pose retry.

Confirmed delayed secondary receiver pulses occurred more than `1 s` and less
than approximately `8 s` after valid contacts. The `10.0 s` falling-edge,
retriggerable post-G38 HAL quarantine suppresses early outside-G38 events. It
does not open `motion.probe-input`, which remains enabled only while realtime
motion type is G38. The release guard requires two clear raw/mux samples
`0.05 s` apart within the 10-second timeout and normally exits early.

Immediately before every G38, a separate guard waits for quarantine expiry and
then performs a synchronized all-clear check of the raw, mux, gated, and fault
states. An unignored outside-G38 pulse drives a retriggerable, monitor-only
`0.5 s` event latch but does not request `halui.program.pause`; the pendant
Pause remains available. There is no fixed post-contact settle delay or
continuous-clear dwell. The raw G38 path is unchanged, so a pulse during G38
is never hidden.

The first Cycle Start executes only non-motion setup and guards, restores the
matching frozen `#3032`, and stops at a mandatory pre-motion M0. The sphere,
post, stylus, and holder paths have now been verified for both probes, so the
released mode-19 T3 and T4 legs have no pose-by-pose inspection M0s. All
high-clearance transit geometry and live-state guards remain active.

Each B group's closing C0 center must be within 0.05 mm of its opening C0
center. Slot 37 must be within 0.05 mm of slot 1. A failed closure retains the
partial data but rejects the attempt. Any abort requires a new attempt ID and a
complete restart; never splice a suffix.

After slot 37, the program moves along the reviewed current-pose path to B0/C0
top-clear, clears both legacy digital requests, and ends. This is measurement
clearance, not tool-change clearance.

## Logging And Analysis

Accepted rows append only to:

```text
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-results.csv
```

The existing paired CSV and analyzer remain untouched. The dedicated analyzer
is `analyze_tcpc_positive_b_c45_baseline.py`. Its `--leg-only 1` path validates
the complete T3 leg before tool change without performing cross-tool math. Its
default two-leg path selects the highest complete attempt for each leg. Both
paths require exactly the manifest-declared slots, reject undeclared gaps,
reordering, duplicates and wrapped negative substitutes for positive B, and
apply machine-state, measurement, and closure QA. The two-leg report includes:

- per-group and whole-run closure vectors
- raw aligned-pose `long minus short` XYZ and norm
- group-C0-referenced C-shape differences
- same-C B0-referenced positive-B differential
- length-normalized XYZ slope and small-angle magnitude
- per-B/per-C RMS and maximum values
- declared unsafe and any non-common slots without imputation

Raw long-minus-short includes installation and elapsed drift. Relative results
remove selected constant references but do not prove that the removed term was
not a real length error. State both forms and the no-S2/positive-B limitations
in every report.

## Operator Sequence

1. Keep the laser cutter and other observed EMI sources inactive.
2. Before Attempt 7, apply LinuxCNC E-stop/disable at the current 100 mm clear
   pose, remove T3, wait for every probe/receiver LED to extinguish, and reseat
   it using the same controlled clocking and retention practice. Do not enable
   or move the CNC while T3 is absent.
3. Run the read-only qualification in `qualify_tcpc_probe_reset.py`: a
   60-second disabled untouched soak, three one-second hand deflections with
   30 seconds clear after each, another 60-second disabled soak, then a
   120-second enabled but motionless soak. Any glow, spontaneous/repeated edge,
   latch reset, stuck input, or raw/mux disagreement bars the run.
4. With qualified T3/H3 and TCPC active at B0/C0, establish the tip 4-5 mm
   above the sphere. Confirm the post direction and all physical clearances.
5. Select the exact T3 runner. Verify its hash, selectors, the excluded
   attempt-3/4/5 CSV prefix ending at attempt-5 sequence 2, T3/H3, correction
   state, probe inputs, homing, B0/C0, WCS, offsets, limits, spindle, and
   clearance. The exact runner restores frozen T3 `#3032` itself.
6. Cycle Start only to the initial M0. This runs guards and the frozen-offset
   assignment but no axis motion. Recheck; then resume under explicit operator
   authority. There are no further programmed inspection holds.
7. After T3 completes, snapshot the exact runner and appended interval, run the
   following exact single-leg validation, and accept the leg only if it exits
   `0` with all structure, state, and closure gates passing:

   ```bash
   python3 configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/analyze_tcpc_positive_b_c45_baseline.py \
     configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-results.csv \
     --grid configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-positive-b-c45-baseline-grid.csv \
     --leg-only 1
   ```
8. From B0/C0 top-clear, establish larger verified linear clearance while TCPC
   remains active. At B0/C0 perform the normal controlled `G49.1`, `G49`, and
   manual T4 tool-change sequence.
9. Apply T4/H4, enter TCPC using the reviewed order, and establish a fresh
   operator-confirmed 4-5 mm B0/C0 sphere start. The exact T4 runner restores
   frozen `#3032 = 0.154742` after its live-tool and TLO guards pass.
10. Select and preflight the exact T4 runner, confirm the verified longer-probe
   path remains unobstructed, then run the identical guarded grid. There are no
   pose-by-pose inspection holds. Never use automatic tool change or automatic
   Cycle Start.
11. After T4 completes, snapshot/analyze the isolated campaign data before
   planning any further pose, S2, negative-B, metrology, or model work. Use the
   analyzer's default two-leg mode; do not pass `--leg-only` for the final
   comparison.

## Ring Disposition

For this provisional current-calibration baseline, the owner/operator has
directed that repeat ring verification be skipped because the machine's
capability does not justify the incremental check. Both existing qualified
offsets remain frozen; neither is recalculated. This disposition applies to
the planned T3-to-T4 baseline tool change. Attempt 6's electrical fault and
physical T3 reseat ended the prior undisturbed-installation basis. Before
Attempt 7, explicitly reconfirm whether the owner waiver remains in force; do
not recalculate `#3032` or insert a ring cycle implicitly. Any collision,
further false or abnormal trigger, visible damage, unexpected seating behavior,
lost home, or tool/offset mismatch rejects the affected attempt.
