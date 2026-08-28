# T3 High-B C-Quadrant Supplemental

Status: attempt 1 completed and validated on 2026-08-24. The reusable runner
retains the initial confirmation M0 but no longer requests pose inspection
holds because the operator verified all sphere/post paths.

## Purpose

This mode-20 supplemental extends the accepted T3 short-probe sphere evidence
to positive `B45` and `B90` at `C0/C90/C180/C270`. It is deliberately separate
from campaign `2026082202` mode 19 and never writes to the positive-B paired
baseline CSV.

The historical expanded runner completed the same positive-B C quadrants,
including B90. That path is useful precedent, but the current run uses the
reviewed live guards, current T3 tool state, current certified sphere position,
and verified high-B paths.

## Frozen Run Identity

- Program: `nc_files/calibration/tcpc_high_b_t3_supplemental.ngc`
- Campaign: `2026082401`
- Mode: `20`
- Attempt: `1`
- Tool: live `T3`, `G43 H3`, length `128.606729 mm`
- Probe diameter: `6.000000 mm`
- Frozen `#3032`: `0.117658 mm`
- Sphere: certified `30.000 mm`
- Start guard: actual Attempt 7 segment3 M2 return-top-clear state, within
  `0.010 mm` of absolute `X1024.051006 Y443.392703 Z-380.390037`

The startup point is the live M2 return-top-clear readback captured after
segment3 completed. It is not the accepted-contact endpoint stored in the CSV;
that endpoint differs in X because the program subsequently returned to the
reconstructed centerline at top-clear.

The file changes neither WCS nor tool-length state. TCPC must already be active,
TWP must be clear, the persistent production correction must be enabled, all
five joints must be homed, and the spindle must be off.

## Four-Contact Method

The standard five-contact sphere cycle is not used. At B90 its `+U` starting
side is below the sphere and can load the sphere/post upward. Every pose,
including both B0 anchors, instead uses exactly four contacts:

1. W contact from top-clear.
2. Safe `-U` start probing toward `+U`.
3. `-V` start probing toward `+V`.
4. `+V` start probing toward `-V`.

For positive B, `U_z < 0`, so the retained `-U` start is the upper side. The
underside `+U` start and its motion are absent from the dedicated source.

With certified effective contact radius `R`, the reconstruction is:

```text
cw = dot(qW, W) + R
cu = dot(qU, U) + R
cv = (dot(qVminus, V) + dot(qVplus, V)) / 2
center = W*cw + U*cu + V*cv
```

Only the V pair provides a measured opposing-contact diameter. The results
schema records `contact_count=4` and `u_method_code=1`, where method 1 means
`certified_radius_single_side`. No U diameter is calculated or logged.

## Sequence And Transit

All transitions first return along the current W vector to top-clear, lift
`25 mm` in machine Z, index B/C, move XY at high Z, and only then descend.
B changes occur only at C0. The initial confirmation is the only programmed
M0; the verified pose paths have no additional inspection holds.

| Seq | Pose | Block | Hold |
| ---: | --- | ---: | --- |
| 1 | B0 C0 opening | 0 | initial confirmation only |
| 2 | B45 C0 opening | 45 | none |
| 3 | B45 C90 | 45 | none |
| 4 | B45 C180 | 45 | none |
| 5 | B45 C270 | 45 | none |
| 6 | B45 C0 closure | 45 | none |
| 7 | B90 C0 opening | 90 | none |
| 8 | B90 C90 | 90 | none |
| 9 | B90 C180 | 90 | none |
| 10 | B90 C270 | 90 | none |
| 11 | B90 C0 closure | 90 | none |
| 12 | B0 C0 outer closure | 190 | none |

Runtime programmed holds: `1` total, the initial confirmation.
No C45/C135/C225/C315 pose is commanded.

## Acceptance Gates

Each pose uses two passes and permits at most one complete-pose retry after a
bounded quality rejection. A no-touch event aborts immediately after returning
to the known clear point.

- Every W/U/V-/V+ travel must be at least `1.0 mm`.
- Pass 1 reconstructed-center correction norm must be below `2.0 mm`.
- Pass 1 measured V sphere diameter must be `29.5..31.0 mm`.
- Pass 1 individual contact radial residuals must be at most `1.0 mm`.
- Pass 2 measured V sphere diameter must be `29.9..30.5 mm`.
- Pass 2 correction norm and each contact radial residual must be at most
  `0.25 mm`.
- Pass-1 to pass-2 reconstructed center delta must be at most `0.10 mm`.
- B45 C0, B90 C0, and outer B0 C0 closure norms must be at most `0.250 mm`.

Probe readiness is immediate and fail-closed. There is no 20-second pre-probe
clear dwell. After a valid touch, the release guard allows the configured
10-second HAL quarantine but requires two consecutive clear samples before the
next probe move.

## Isolated Outputs

Accepted pose rows append only to:

`configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-high-b-t3-supplemental-results.csv`

Matching tool, rotary, endpoint, and linear-axis state rows append only to:

`configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-high-b-t3-supplemental-state.csv`

Closure records, including a failed record before abort, append only to:

`configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/tcpc-high-b-t3-supplemental-closures.csv`

Closure IDs are `45` for seq2-to-seq6, `90` for seq7-to-seq11, and `190` for
the seq1-to-seq12 outer closure.

## Operator Release Conditions

Before loading this file again, return to its frozen B0/C0 start guard, verify
the probe responds cleanly with no LED glow, confirm the sphere/post and
verified paths remain unobstructed, and keep the laser off. Loading and Cycle
Start remain operator-controlled.
