# Head-Head 5-Axis Simulation Baseline

## Scope

This directory is the starting point for head-head 5-axis kinematics R&D.

It is intentionally not a runnable simulation yet. The goal of this first step
is to lock:

- machine conventions
- nominal travels
- nominal rotary geometry
- calibration requirements

before building:

- a new head-head kinematics component
- TCP support
- TWP support
- a full visual LinuxCNC simulation

## Locked Production Convention

The future machine math should use standard right-hand industrial convention:

- `+X` right
- `+Y` away from operator
- `+Z` up
- `+B` follows the right-hand rule about `+Y`
- `+C` follows the right-hand rule about `+Z`
- `B=0`, `C=0` => tool points in `-Z`

This convention is the production target even if interim rebuild stages use
temporary opposite signs or offsets.

## Nominal Travels

- `X = 0 .. 3310 mm`
- `Y = 0 .. 1700 mm`
- `Z = -900 .. 0 mm`
- `B = -100 .. +100 deg`
- `C = -360 .. +360 deg`

Home pose:

- `X=0`
- `Y=0`
- `Z=0`
- `B=0`
- `C=0`

## Nominal Head Geometry

Current nominal starting model:

- `C` center to `B` center = `(0, 0, 0) mm`
- spindle centerline offset is approximately `+25 mm` in `Y`
- `B` center to spindle nose reference is approximately `180 mm`

Approximate nominal vector from `B` center to spindle nose at `B=0`, `C=0`:

- `(0, +25, -180) mm`

## Calibration Requirement

The final machine must support calibrated geometry, not idealized-only
kinematics.

The simulation and future kinematics should expose parameters for:

- rotary zero offsets
- `C` to `B` center offsets
- `B` to spindle/tool reference offsets
- spindle/tool centerline assembly error

Known example of real error from the previous assembly:

- spindle center offset relative to the `B` axis was about `2 mm`

## Next Steps

1. Build a math-only simulation around the values in `geometry_baseline.ini`
2. Add a parameterized forward/inverse kinematics model
3. Add TCP behavior on top of the same transform model
4. Add TWP behavior on top of the same transform model
5. Build a visual machine model from Fusion 360 geometry

## Fusion 360 Inputs Needed Later

- home-pose screenshots with axis arrows
- pivot dimensions
- simplified STL exports
- known test poses for validation
