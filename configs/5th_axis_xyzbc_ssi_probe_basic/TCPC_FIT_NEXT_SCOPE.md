# TCPC Fit Next Scope

Status: paused on 2026-04-27. Staff started epoxy preparation on a mold on the
machine, and the start was bumped near the end of the B-axis session. Do not
continue probing or treat new readings as clean calibration data until the mold
work is clear and the sphere setup is stable again.

## Current Data Set

Use the curated input file for the first fit pass:

- `configs/5th_axis_xyzbc_ssi_probe_basic/tcpc-fit-input-candidates.csv`

Included B-axis candidate centers:

- `B0 C0` closing two-pass accepted center:
  `X=306.338526 Y=352.821813 Z=-280.762445`
- `B+15 C0` two-pass accepted center:
  `X=226.486276 Y=352.897855 Z=-291.117802`
- `B-15 C0` corrected single-pass accepted center:
  `X=386.140321 Y=352.717855 Z=-291.445826`
- `B+30 C0` two-pass accepted center:
  `X=151.969455 Y=352.913688 Z=-321.714304`
- `B-30 C0` two-pass accepted center:
  `X=460.527766 Y=352.638896 Z=-322.390804`

Data caveats:

- The closing `B0 C0` point is usable only with the epoxy/bumped-start caveat.
- The latest raw B-vector CSV also contains one extra full `B0 C0` two-pass
  repeat after the bumped start. Its accepted center was
  `X=306.331442 Y=352.822021 Z=-280.761945`, which is close to the previous
  closing point, but it is excluded from the first candidate input because the
  run was unintended and the setup environment was no longer clean.
- The `B-15 C0` point came from the corrected single-pass routine, not the
  automatic two-pass routine.
- The observed B-axis candidate Y range is about `0.274792 mm`; this may be
  real head alignment, local machine error, setup disturbance, or some
  combination. Do not hide that by forcing the rotary geometry fit.
- Corrected sphere diameters are commonly around `30.1-30.3 mm`, so fit work
  should use center repeatability and residuals rather than diameter alone.

## First Offline Fit

Start with analysis only. Do not change INI, HAL, kinematics constants, WCS, or
Probe Basic settings from these numbers until the residual report is reviewed.

Recommended steps:

1. Read the C-axis sweep from `sphere-center-results.csv`.
2. Read accepted B-vector rows from the curated candidate CSV.
3. Fit the C-axis center from the stable `B0` C-sweep.
4. Fit the B-axis candidate from the `C0` B sweep in machine `X/Z`.
5. Report residuals by pose, not just a single best-fit offset.
6. Decide whether to repeat `B0 C0` and `B-15 C0` before writing any TCPC
   offset values.

Preliminary sanity check from the current B candidate rows only:

- simple `X/Z` circle center: `X=305.669816 Z=-589.742446`
- simple radius: `308.963734 mm`
- residuals are within about `0.02 mm` for the candidate rows

This is only a geometry sanity check. The final TCPC setup still needs the
C-axis fit, sign convention verification, kinematics mapping, and a practical
fixed-tip validation pass.

## Resume Conditions

Before collecting more machine data:

- confirm the epoxy/mold work is not moving, loading, or thermally disturbing
  the calibration setup
- confirm the 30 mm sphere is rigid and has not shifted
- verify active WCS and probe parameters after Probe Basic restart
- keep probing feeds at `50 mm/min` slow and `100 mm/min` fast
- keep transfer moves at or below `300 mm/min`
- rerun closing `B0 C0` with the two-pass routine as the first clean check
