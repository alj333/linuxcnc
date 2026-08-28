# T4 New-Location Attempt-7 Continuation Reachability

Status: `PASS`

- campaign / mode / attempt: `2026082701 / 41 / 7`
- frozen model / T4 length: `2026082601 / 229.407000 mm`
- active WCS / work start: `G54 / X0.000 Y0.000 Z0.000`
- frozen G54 offsets: `X2501.941254485 Y696.899347451 Z-510.273128272` mm
- nominal B0/C0 absolute start: `X2501.941254485 Y696.899347451 Z-280.866128272` mm
- frozen Attempt-6 sequence-23 center seed: `X2501.156895000 Y696.528585000 Z-302.580083000` mm
- center-derived B0/C0 top-clear: `X2501.156895000 Y696.528585000 Z-279.734825000` mm
- nominal first handoff distance: `1.425668857 mm`
- nominal / worst-vertex physical sphere clearance: `3.886021634 / 3.833512880 mm`
- nominal / worst-vertex effective post clearance: `14.871096020 / 14.797951493 mm`
- minimum sphere / effective-post clearance over first entry: `3.833512880 / 14.797951493 mm`
- worst physical-start deviation XYZ: `-0.050, -0.050, -0.050` mm at `X2501.891254485 Y696.849347451 Z-280.916128272` mm
- coordinate guard enumeration: `1728` simultaneous layer vertices -> `64` distinct mapped physical starts
- sampled grid/path points: `33837` over `64` physical-start handoffs, nominal handoff, and `78` recovery poses
- automatic chatter quiet: `15.0 s` continuous, `900.0 s` cumulative context cap, `0.25 s` samples
- center / path-model / handoff reserves: `2.000 / 3.000 / 0.050 mm`
- required margin after `5.050 mm` reserve: `10.000 mm`
- frozen runner SHA-256: `fad7b3cf7a1a63d8137993fd943fabe6a07d08b2cce6bf2de7524eb5ccb8339d`

| constraint | nominal margin | after reserve | limiting pose/sample | position |
| --- | ---: | ---: | --- | ---: |
| J0 | 416.916340 mm | 411.866340 mm | B-90 C184 `transit_rotary` | 2933.093660 mm |
| J1 | 247.388420 mm | 242.338420 mm | B-90 C94 `transit_rotary` | 237.388420 mm |
| J2 | 187.772857 mm | 182.722857 mm | B+90 C180 `transit_descend` | -712.237143 mm |
| X axis | 826.007847 mm | 820.957847 mm | B+90 C0 `transit_xy` | 2524.002153 mm |
| Y axis | 683.683327 mm | 678.633327 mm | B+90 C270 `transit_xy` | 673.683327 mm |
| Z axis | 254.734825 mm | 249.684825 mm | B+0 C0 `transit_lift` | -254.734825 mm |

Rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`.

The exact replay starts at guarded active-G54 work X0/Y0/Z0 and first moves to the B0/C0 top-clear derived from the immutable accepted Attempt-6 sequence-23 center. It then applies the runner's 25 mm Z lift, B10/C0 index, XY positioning, Z descent, full sequence-24 reacquisition, and exact sequence-24-to-101 tail.

The simultaneous start guards were not collapsed by assertion. For each axis the analyzer solves the bounded work, G54, TLO, and absolute-position identity polytope: 12 vertices per axis, 1,728 XYZ layer-state vertices, and 64 distinct mapped physical starts. Every mapped start is replayed to the one fixed center-derived top-clear; the nominal start is replayed separately. The absolute guard makes this enumeration the exact physical projection, while the separate post-M0 hold guard restricts movement to 0.001 mm.

Every first-segment sample remains at least `21.663954728 mm` above the sphere center, greater than the `17.845258000 mm` effective contact radius. The first handoff, 25 mm lift, B10 index, XY move, and descent retain positive modeled sphere and post clearance. The post ray begins at the sphere surface and extends toward X-, Y+, Z- (base-to-sphere X+, Y-, Z+), so it does not consume the sphere itself. Its 18 mm effective radius conservatively bounds a post no wider than the 30 mm sphere plus the 3 mm probe-ball radius.

The full 0.050 mm start envelope is additive to the 2 mm center and 3 mm path/model reserves for configured-limit reporting.

The complete sequence-24-to-101 trajectory is replayed against configured joint/axis limits. The effective-post calculation applies to the noncontact first-entry path only; it deliberately excludes intended sphere contact/overtravel samples and does not claim a body/holder/fixture proof. The operator's prior pose-clearance confirmation remains the authority for those physical clearances, along with the secured sphere and laser-off checks.

All automatic quiet loops are stationary: they contain sampled dwell/synchronization plus live, model, pose, counter, level, and fault guards, with no axis/rotary motion, gate write, or operator hold. Therefore the quiet policy adds no geometric path samples. Normal no-chatter contacts wait only for physical release and the existing 10.0 second HAL ignore window; matched gate-closed activity resets a 15.0 second continuous quiet timer within a cumulative 900.0 second contact or gap budget.

The policy is based on the stationary observation in which raw/mux counters rose together from 1259 to 1283 while gated remained 618 over roughly 50 seconds, then became quiet after 08:40:28. Matched raw/mux extras are diagnostic; any outside-G38 gated change, final cumulative mismatch, uncleared fault/levels, or cumulative timeout remains fatal.

Because X, Y, and Z all changed from the reference location, this is a machine-volume transfer test, not an isolated X-axis straightness measurement.

Detailed samples: `tcpc-length-aware-t4-new-location-2026082701-attempt7-recovery-reachability.csv`
