# X/Y Backlash And Distance Verification Next Scope

Status: first X/Y reversal backlash pass completed on 2026-04-28. Commanded
distance verification is deferred until suitable tooling is available or a
distance/scale problem is suspected.

Purpose:

- quantify X and Y reversal backlash before more TCPC fitting
- verify commanded X/Y motion distance over short and long moves
- separate axis-scale or rack/screw motion error from rotary TCPC geometry error

Run this in a `trivkins` maintenance/setup config, not the TCPC config. Do not
use or modify `G55`; it is reserved for staff setup work until the operator
explicitly releases it.

## Setup

Recommended instruments:

- dial test indicator or linear indicator rigidly mounted to the table/spindle
- precision straightedge, gauge block stack, or calibrated reference bar for
  distance checks
- optional laser/linear scale if available for long moves

Machine setup:

- spindle stopped
- B and C at zero unless a specific reason exists otherwise
- use machine coordinates or a disposable calibration WCS, not `G55`
- warm the machine with gentle axis motion before final measurements
- keep first moves slow: `100-200 mm/min` for indicator work
- keep any non-measuring transfers conservative until the setup is proven

Do not change backlash compensation, step scale, encoder scale, or kinematics
from the first pass. Capture repeatable data first.

## X/Y Reversal Backlash Test

For each axis:

1. Preload the axis in the positive direction with a move large enough to take
   up clearance.
2. Zero the indicator.
3. Command small positive increments and record actual indicator movement.
4. Reverse direction with small negative increments and record when the
   indicator first responds.
5. Repeat with the axis preloaded in the negative direction.
6. Repeat at several table locations.

Suggested first increments:

- `0.01 mm`
- `0.02 mm`
- `0.05 mm`
- `0.10 mm`
- `0.50 mm`

Record:

- axis
- machine position
- preload direction
- commanded reversal amount
- measured indicator response
- estimated lost motion
- any audible/mechanical change

## X/Y Commanded-Distance Verification

For each axis, check both positive and negative travel.

Suggested first distances:

- `10 mm`
- `50 mm`
- `100 mm`
- `250 mm`
- longest safe distance practical for the current setup

Record:

- commanded distance
- measured distance
- error in mm
- error in mm/m
- starting machine coordinate
- direction of travel
- whether the approach was from the same direction or after reversal

Use repeated same-direction moves to identify scale/distance error. Use
reversal moves to identify backlash and compliance.

## First Backlash Results - 2026-04-28

Tooling/context:

- Dial indicator setup was available for reversal lost-motion checks.
- Suitable tooling for commanded-distance verification was not available, so
  distance verification is deferred.
- Values below are recorded using the operator's side labels from the live
  setup. Do not reinterpret sign conventions without checking the indicator
  mounting direction.

Measured X lost motion at the tested machine location:

| Side / direction label | Runs mm | Average mm |
| --- | --- | ---: |
| X pos side | `0.030, 0.035, 0.034` | `0.033` |
| X neg side | `0.045, 0.034, 0.035` | `0.038` |

Measured Y lost motion at the tested machine location:

| Direction group | Runs mm | Average mm |
| --- | --- | ---: |
| Y group 1 | `0.029, 0.031, 0.028` | `0.029` |
| Y group 2 | `0.027, 0.029, 0.031` | `0.029` |

Interpretation:

- X/Y reversal lost motion is repeatable and likely contributes materially to
  the TCPC fixed-tip error floor.
- Practical working values from this pass are about `0.035-0.040 mm` for X and
  about `0.029 mm` for Y at this location.
- This is a significant part of the `0.10 mm` practical TCPC target and should
  be considered before attempting tighter TCPC geometry fitting.
- Do not enable backlash compensation from this one location alone. If
  compensation is considered later, repeat at several machine positions first.
- Because distance verification was skipped, do not change axis scale or
  encoder scale from this data.

## Acceptance And Next Decision

Do not compensate from a single reading. First decide whether the error is:

- repeatable backlash/lost motion near reversal
- distance-scale error proportional to travel
- local rack/screw pitch error that changes with machine position
- compliance or setup movement

Only after that choose the correction path:

- mechanical adjustment if backlash is inconsistent or large
- LinuxCNC backlash compensation only if lost motion is repeatable and
  mechanically acceptable
- scale/INI adjustment only if distance error is proportional and verified over
  multiple travel lengths
- mapping or future compensation project if local position-dependent error
  dominates
