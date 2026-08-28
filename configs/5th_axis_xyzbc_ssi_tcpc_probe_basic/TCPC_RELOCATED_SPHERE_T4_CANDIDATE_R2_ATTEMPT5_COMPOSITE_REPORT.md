# T4 R2 Attempt-5 Recovery Report

Status: `RECOVERY CONTRACT PASS`

- campaign / mode / attempt: `2026082404 / 29 / 5`
- accepted recovery rows: `19 / 19`
- validated closures: `14`
- worst recovery closure: `0.019998 mm`
- validated per-G38 contact traces: `152`
- validated inter-contact gap traces: `152`
- retrigger bursts: `0`
- terminal trace: `none`
- standalone centered RMS / max: `0.078560 / 0.119618 mm`

This is a 19-row finish-recovery acquisition, not a formal same-acquisition 101-row candidate pass.

## Composite Diagnostic Only

This diagnostic uses attempt-5 sequences 1-9,72,93-101; sealed attempt-4 sequences 67-71,73-92; sealed attempt-3 sequences 45-66; and immutable attempt-2 sequences 10-44.
Attempt-2, attempt-3, and attempt-4 rows are independently translated into the attempt-5 opening-B0 frame.
- attempt-2 nuisance translation XYZ / norm: `0.049518, 0.029954, -0.041879 / 0.071436 mm`
- attempt-3 nuisance translation XYZ / norm: `0.020310, 0.009756, -0.034627 / 0.041312 mm`
- attempt-4 nuisance translation XYZ / norm: `-0.008827, -0.016465, -0.008973 / 0.020725 mm`
- aligned attempt-4/5 opening overlap RMS / max: `0.012516 / 0.020022 mm`
- aligned attempt-4/5 midpoint overlap RMS / max: `0.021092 / 0.021092 mm`
- aligned attempt-4/5 closing-prefix overlap RMS / max: `0.021646 / 0.027844 mm`
- composite raw-101 centered RMS / max: `0.090001 / 0.194441 mm`
- composite equal-76 centered RMS / max: `0.089045 / 0.190827 mm`
- canonical within-acquisition closures: `28` (attempt 2 / 3 / 4 / 5: `5 / 4 / 5 / 14`)

The alignment removes one translation per acquisition. It cannot remove probe reseat, spindle, axis-position, or time-dependent changes.
Closures remain valid only inside their source acquisition; the composite creates no cross-acquisition closure evidence.
These metrics are diagnostic and must not be labeled a formal 101-row pass.
