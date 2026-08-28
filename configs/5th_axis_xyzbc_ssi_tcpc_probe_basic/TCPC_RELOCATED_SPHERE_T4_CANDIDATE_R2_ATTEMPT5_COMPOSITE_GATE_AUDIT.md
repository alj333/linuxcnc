# T4 R2 Attempt-5 Composite Gate Audit

Status: `DIAGNOSTIC 11/12; R2 NOT ACCEPTED`

The sealed Attempt-5 analyzer validates the recovery contract and source
partition. It intentionally does not apply the frozen R2 whole-grid
statistical gates. This audit reconstructs those formulas on the translated
four-source composite. Because the data span four acquisition times and use
three fitted nuisance translations, every result below is diagnostic rather
than a formal uninterrupted-run gate.

| frozen calculation | result | diagnostic contract |
| --- | --- | ---: |
| equal-76 RMS improvement | `PASS` | `0.089045 <= 0.197642 mm` |
| equal-76 maximum improvement | `PASS` | `0.190827 <= 0.638888 mm` |
| positive high-B RMS | `PASS` | `0.096662 <= 0.208861 mm` |
| negative high-B RMS | `PASS` | `0.104606 <= 0.311644 mm` |
| B0 RMS | `PASS` | `0.084454 <= 0.143686 mm` |
| maximum unique-pose worsening | `FAIL` | `0.090202 > 0.075000 mm` |
| equal-76 RMS ceiling | `PASS` | `0.089045 <= 0.120000 mm` |
| equal-76 maximum ceiling | `PASS` | `0.190827 <= 0.280000 mm` |
| raw-101 RMS ceiling | `PASS` | `0.090001 <= 0.120000 mm` |
| raw-101 maximum ceiling | `PASS` | `0.194441 <= 0.280000 mm` |
| predicted-pattern RMS | `PASS` | `0.030038 <= 0.050000 mm` |
| predicted-pattern maximum | `PASS` | `0.068496 <= 0.120000 mm` |

The failing pose is `B+90 C180`, original sequence 85, supplied by Attempt 4.
Its immutable-baseline centered norm is `0.076479 mm`; its aligned-composite
norm is `0.166681 mm`; the frozen prediction is `0.122408 mm`. Attempt 4's
B+90 local closure is `0.009112 mm`, and sequence 85's pass-center delta is
`0.001930 mm`. The point is internally clean and must not be discarded as a
bad touch.

Observed performance remains close to the frozen R2 prediction:

- equal-76 RMS differs by `+0.003282 mm`; maximum differs by `-0.014121 mm`
- raw-101 RMS differs by `+0.002825 mm`; maximum differs by `-0.013348 mm`
- pattern RMS / max remain inside `0.050 / 0.120 mm`

The correct disposition is to keep R2 unaccepted and unchanged. The next
formal predeclared T3 verification stage is not authorized. If the operator
elects to continue the tool-length diagnosis, a separately declared
exploratory T3 holdout may be run only under the baseline task-capture INI with
the R2 overlay absent and with its scoring method frozen before motion. Do not
use T3 to cure the failed T4 gate or relabel the translated T4 composite as a
formal pass, and do not refit R2 from this validation composite.
