# T4 New-Location Attempt-6 Continuation Reachability

Status: `PASS`

- campaign / mode / attempt: `2026082701 / 40 / 6`
- frozen model / T4 length: `2026082601 / 229.407000 mm`
- active WCS / work start: `G54 / X0.000 Y0.000 Z0.000`
- frozen G54 offsets: `X2501.941254485 Y696.899347451 Z-510.273128272` mm
- nominal B0/C0 absolute start: `X2501.941254485 Y696.899347451 Z-280.866128272` mm
- frozen Attempt-4 row-9 center seed: `X2500.940456000 Y696.558194000 Z-302.576056000` mm
- center-derived B0/C0 top-clear: `X2500.940456000 Y696.558194000 Z-279.730798000` mm
- nominal first handoff distance: `1.551437433 mm`
- nominal / worst-corner physical sphere clearance: `3.890402681 / 3.837483000 mm`
- worst absolute-envelope corner: `---` at `X2501.891254485 Y696.849347451 Z-280.916128272` mm
- sampled unique grid/path points: `29719` over `8` envelope-corner handoffs, nominal handoff, and `92` recovery poses
- center / path-model / handoff reserves: `2.000 / 3.000 / 0.050 mm`
- required margin after `5.050 mm` reserve: `10.000 mm`
- frozen runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`

| constraint | nominal margin | after reserve | limiting pose/sample | position |
| --- | ---: | ---: | --- | ---: |
| J0 | 417.132779 mm | 412.082779 mm | B-90 C184 `transit_rotary` | 2932.877221 mm |
| J1 | 247.418029 mm | 242.368029 mm | B-90 C94 `transit_rotary` | 237.418029 mm |
| J2 | 187.776884 mm | 182.726884 mm | B+90 C180 `transit_descend` | -712.233116 mm |
| X axis | 826.224286 mm | 821.174286 mm | B+90 C0 `transit_xy` | 2523.785714 mm |
| Y axis | 683.712936 mm | 678.662936 mm | B+90 C270 `transit_xy` | 673.712936 mm |
| Z axis | 254.730798 mm | 249.680798 mm | B+0 C0 `transit_lift` | -254.730798 mm |

Rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`.

The exact replay starts at guarded active-G54 work X0/Y0/Z0 and moves directly to the B0/C0 top-clear derived from the immutable accepted Attempt-4 row-9 center. There is no motion through the archived Attempt-4 terminal-clear point. The full eight-corner 0.050 mm absolute-start cube is replayed; it conservatively contains every physical start admitted by the simultaneous work-coordinate, G54-offset, tool-length, and absolute-position guards. After the common top-clear endpoint, the exact sequence-10-to-101 trajectory is independent of the selected start corner.

The observed Attempt-4 terminal clear was `X2500.972727063 Y696.550278557 Z-279.730797759` mm, `0.033227635 mm` from the center-derived clear. That 0.033228 mm difference is archived provenance from the row-9 measured correction before Attempt 4 aborted at its closure; it is not an Attempt-6 waypoint or center seed.

Every handoff sample remains at least `21.659927728 mm` above the sphere center, greater than the `17.845258000 mm` effective contact radius. The post extends below the sphere toward X-, Y+, Z-, so this above-sphere handoff cannot intersect the reviewed post segment.

The full 0.050 mm handoff envelope is also additive to the 2 mm center and 3 mm path/model reserves for configured-limit reporting. The separate post-M0 hold guard permits only 0.001 mm physical movement before motion.

This is a configured-limit and kinematic-path proof. The operator remains responsible for confirming the unchanged post direction (base to sphere X+, Y-, Z+), nearby fixture clearance, secured sphere, and laser-off condition.

Because X, Y, and Z all changed from the reference location, this is a machine-volume transfer test, not an isolated X-axis straightness measurement.

Detailed samples: `tcpc-length-aware-t4-new-location-2026082701-attempt6-recovery-reachability.csv`
