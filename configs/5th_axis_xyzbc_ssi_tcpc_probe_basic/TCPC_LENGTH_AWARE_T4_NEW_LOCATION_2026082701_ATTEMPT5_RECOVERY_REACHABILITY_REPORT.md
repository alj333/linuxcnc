# T4 New-Location Attempt-5 Continuation Reachability

Status: `PASS`

- campaign / mode / attempt: `2026082701 / 39 / 5`
- frozen model / T4 length: `2026082601 / 229.407000 mm`
- B0/C0 operator start: `X2500.972727063 Y696.550278557 Z-279.730797759` mm
- frozen Attempt-4 row-9 center seed: `X2500.940456000 Y696.558194000 Z-302.576056000` mm
- seeded top-clear radius: `22.845258 mm`
- sampled grid/path points: `28309` over `92` recovery poses
- center / path-model / handoff reserves: `2.000 / 3.000 / 0.050 mm`
- required margin after `5.050 mm` reserve: `10.000 mm`

| constraint | nominal margin | after reserve | limiting pose/sample | position |
| --- | ---: | ---: | --- | ---: |
| J0 | 417.132779 mm | 412.082779 mm | B-90 C184 `transit_rotary` | 2932.877221 mm |
| J1 | 247.418029 mm | 242.368029 mm | B-90 C94 `transit_rotary` | 237.418029 mm |
| J2 | 187.776884 mm | 182.726884 mm | B+90 C180 `transit_descend` | -712.233116 mm |
| X axis | 826.224286 mm | 821.174286 mm | B+90 C0 `transit_xy` | 2523.785714 mm |
| Y axis | 683.712936 mm | 678.662936 mm | B+90 C270 `transit_xy` | 673.712936 mm |
| Z axis | 254.730798 mm | 249.680798 mm | B+0 C0 `transit_lift` | -254.730798 mm |

Rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`.

The exact replay starts from the verified Attempt-4 row-9 B0/C0 top-clear command. The full 0.050 mm absolute handoff envelope is additive to the 2 mm center and 3 mm path/model reserves. The separate post-load hold guard permits only 0.001 mm change before motion.

This is a configured-limit and kinematic-path proof. The operator remains responsible for confirming the unchanged post direction (base to sphere X+, Y-, Z+), nearby fixture clearance, secured sphere, and laser-off condition.

Because X, Y, and Z all changed from the reference location, this is a machine-volume transfer test, not an isolated X-axis straightness measurement.

Detailed samples: `tcpc-length-aware-t4-new-location-2026082701-attempt5-recovery-reachability.csv`
