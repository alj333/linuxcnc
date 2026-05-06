# TCPC Short-Probe Balanced Final Report

This is the final planned short-probe-only TCPC candidate before moving the
machine focus back to production Probe Basic/TCPC/TWP implementation and servo
tuning.

## Data Used

- Previous extended candidate validation:
  - rows `409-471`
  - rows `473-529`
- Mid-B diagnostic confirmation:
  - rows `530-649`
- All data is accepted pass-2 only and compared to the same-run same-C B0
  reference.

## Current State

The mid-B diagnostic candidate is already inside the current production need:

- confirmation RMS/max: `0.062482 / 0.126795 mm`
- previous extended-candidate RMS/max after applying the mid-B candidate
  offline: about `0.052 / 0.100 mm`
- practical conclusion: the machine is comfortably under the core `0.2 mm`
  target, but not proven as a hard `0.1 mm` machine with the short probe alone.

## Balanced Final Candidate

The balanced candidate keeps:

- validated C harmonic terms
- confirmed mid-B envelope terms

It refits only the existing B/B-C correction families against both short-probe
validation runs. This avoids adding another correction family before long-probe
data exists.

Diagnostic HAL:

`configs/sim/head_head_5axis/head_head_short_probe_balanced_final_candidate.hal`

Offline predicted metrics:

| data set | RMS mm | max mm |
| --- | ---: | ---: |
| previous extended validation rows | 0.054489 | 0.108865 |
| mid-B confirmation rows | 0.053781 | 0.110879 |
| combined | 0.054136 | 0.110879 |

This is a balanced confidence candidate, not a sub-`0.1 mm` claim.

## Decision

Run one final full safe-grid confirmation with the balanced candidate. If it
lands under `0.2 mm` and broadly matches the predicted `~0.11 mm` max behavior,
stop TCPC probing for now.

Do not chase the remaining few hundredths with the short probe only. The next
useful calibration data is a short-probe and long-probe back-to-back run after
the longer stylus arrives.

## Future Long/Short Probe Work

When the long probe arrives:

1. Do not move the sphere between short and long probe runs.
2. Warm the machine to a comparable state before both passes.
3. Run the same B0-referenced safe grid with the short probe.
4. Change only probe/stylus length and tool state, then run the same grid with
   the long probe.
5. Compare the residual change per added tool length.

That comparison should separate tool-length-dependent alignment errors from
machine-fixed B/C harmonic errors much better than short-probe data alone.

## Production Work After Final TCPC Test

After the final short-probe TCPC confidence test, move focus to:

- finish the production Probe Basic config with TCPC and TWP enabled
- make the TCPC/TWP behavior part of the full machine config rather than a
  calibration overlay
- servo tuning for practical speeds and accelerations
- Probe Basic UI/setup cleanup for the actual workflow
- general machine setup and safety polish

The current TCPC correction should remain diagnostic/gated until the production
config integration plan is explicit.
