# Relocated-Sphere T4 Reachability Report

- measurement campaign: `2026082404`
- inherited anchor campaign: `2026082403`
- anchor attempt: `1`
- anchor center: `X1024.957789 Y844.074417 Z-302.468115` mm
- planned T4 primary poses: `101`
- planned T3 verification poses: `31`
- sampled kinematic points: `41063`
- frozen T4 primary SHA-256: `bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2`
- frozen T3 verification SHA-256: `ceaf8895626a2b3030fb1d36f5575f7ff5c3850630178303795279e9be483c18`
- required nominal AXIS/JOINT margin: `15.000 mm`
- reserved empirical measured-center allowance: `2.000 mm`
- reserved path/model allowance: `3.000 mm`
- required margin after allowances: `10.000 mm`
- status: `PASS`

| constraint | minimum margin | remaining after allowances | pose/sample | position |
| --- | ---: | ---: | --- | ---: |
| J0 | 601.460525 mm | 596.460525 mm | T4 B-90 C4 `transit_rotary` | 591.460525 mm |
| J1 | 395.153277 mm | 390.153277 mm | T4 B+90 C266 `transit_rotary` | 385.153277 mm |
| J2 | 187.860993 mm | 182.860993 mm | T4 B+90 C90 `transit_descend` | -712.149007 mm |
| X axis | 1012.075447 mm | 1007.075447 mm | T3 B+90 C180 `transit_xy` | 1002.075447 mm |
| Y axis | 831.192075 mm | 826.192075 mm | T3 B+90 C270 `transit_xy` | 821.192075 mm |
| Z axis | 254.585773 mm | 249.585773 mm | T3 B+0 C0 `transit_lift` | -254.585773 mm |

Rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`.

The 2 mm center allowance is a conservative campaign assumption, not a bound enforced by the probing runners. Each accepted pass is internally checked, but successive accepted centers can update the next pose origin. The observed baseline center errors are below 0.4 mm; any campaign result outside the 2 mm anchor envelope invalidates this reachability release.

The 3 mm path/model allowance covers omitted post-contact retract segments and the small TCPC entry-angle origin difference. The current zero C-frame and B-axis tilt settings are asserted before replay.

This report checks controller geometry and configured limits. It does not release probe-body, holder, sphere-post, cable, or fixture clearance. Every positive-B pose has a corresponding negative-B pose. At 2026-08-24T23:42:38+07:00, the operator explicitly accepted T4 physical clearance for B-5/-10/-15 at C45/C225; that is operator evidence, not a result of this replay model.

Detailed samples: `tcpc-relocated-sphere-reachability.csv`
