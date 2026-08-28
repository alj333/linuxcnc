# T4 New-Location Reachability

Status: `PASS`

- campaign / mode / attempt: `2026082701 / 35 / 1`
- frozen model / T4 length: `2026082601 / 229.407000 mm`
- B0/C0 operator start: `X2501.941254485 Y696.899347451 Z-280.866128272` mm
- conservative center estimate: `X2501.941254485 Y696.899347451 Z-303.711386272` mm
- center estimate rule: start Z minus top-clear radius `22.845258 mm`
- sampled grid/path points: `30653` over `101` poses
- center uncertainty / path-model reserve: `2.000 / 3.000 mm`
- required margin after `5.000 mm` reserve: `10.000 mm`

| constraint | nominal margin | after reserve | limiting pose/sample | position |
| --- | ---: | ---: | --- | ---: |
| J0 | 416.131981 mm | 411.131981 mm | B-90 C184 `transit_rotary` | 2933.878019 mm |
| J1 | 247.759182 mm | 242.759182 mm | B-90 C94 `transit_rotary` | 237.759182 mm |
| J2 | 186.641553 mm | 181.641553 mm | B+90 C180 `transit_descend` | -713.368447 mm |
| X axis | 825.223488 mm | 820.223488 mm | B+90 C0 `transit_xy` | 2524.786512 mm |
| Y axis | 684.054089 mm | 679.054089 mm | B+90 C270 `transit_xy` | 674.054089 mm |
| Z axis | 255.866128 mm | 250.866128 mm | B+0 C0 `transit_lift` | -255.866128 mm |

Rotary configured-limit margins: B `10.000 deg`, C `44.000 deg`.

The center estimate assumes the operator start is the intended 5 mm top-clear point. The 2 mm reserve covers the stated 3-5 mm physical start clearance. Moving the start more than 2 mm from the recorded XYZ invalidates this release until replayed.

This is a configured-limit and kinematic-path proof. The operator remains responsible for confirming the unchanged post direction (base to sphere X+, Y-, Z+), nearby fixture clearance, secured sphere, and laser-off condition.

Because X, Y, and Z all changed from the reference location, this is a machine-volume transfer test, not an isolated X-axis straightness measurement.

Detailed samples: `tcpc-length-aware-t4-new-location-2026082701-attempt1-reachability.csv`
