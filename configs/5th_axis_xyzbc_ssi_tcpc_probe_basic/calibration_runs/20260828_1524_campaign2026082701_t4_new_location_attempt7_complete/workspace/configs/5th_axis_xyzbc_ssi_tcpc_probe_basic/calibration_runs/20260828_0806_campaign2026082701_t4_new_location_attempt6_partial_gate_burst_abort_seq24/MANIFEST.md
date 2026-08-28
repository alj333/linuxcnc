# T4 New-Location Attempt-6 Partial-Stop Archive

- sealed at: `2026-08-28T08:10:26+07:00`
- campaign / mode / attempt: `2026082701 / 40 / 6`
- status: `PARTIAL - GATE-CLOSED BURST ABORT BEFORE SEQUENCE-24 CONTACT 2`
- accepted rows: sequences `10..23` (`14` rows)
- accepted transactions: `112/112` contact/gap traces
- retained Attempt-6 closures: `2/2`, both pass
- runner SHA-256: `2448eb37a33c9df1929fa11bb97115ad755000032dc4edafa2236313985f5310`
- Attempt-6 pre-load archive root: `639bb502ea5029911e9d1cd745fb11a41839c2c54c39a35c74c91c7ef2b2fddc`

Attempt 6 is retired. It must not be resumed, appended, restarted, or reused.
Its accepted sequences `10..23`, two passing same-run closures, and `112/112`
complete trace transactions remain valid for the final composite.

Sequence 24 pass 1 contact 1 was a valid top touch with exactly one gated
edge. Eight matched raw/mux repeat edges occurred while the gate was closed,
followed by one further matched raw/mux edge during gate-closed reposition.
The combined diagnostic extra count was `9`, exceeding the runner's bound of
`8`. QtPyVCP recorded the exact abort at `01:12:15.194` before the contact-2
G38. The gated counter remained `618` for all nine repeat edges.

Sequence 24's one contact row and two gap rows are diagnostic-only partial
records and must not enter the fit or accepted composite. A fresh continuation
must begin at sequence 24 with a new attempt identity and six new output files.
The complete ownership target is A4 sequences `1..9`, A6 sequences `10..23`,
and the continuation sequences `24..101`.

The read-only stop pose is absolute
`X2479.642700100176 Y696.528615621598 Z-298.779137642143 B10 C0`.
It is the exact U-start point, with modeled physical clearance `4.000 mm`.
A straight move from there to either reconstructed top-clear or G54 work zero
intersects the sphere envelope. The archived audit report defines the safe
two-leg radial escape and the immutable accepted sequence-23 center that a
recovery runner must use.

`workspace/` preserves repository-relative paths and contains the exact
runner, six stopped outputs, report, validation INI, base and length-model HAL
files, probe counter HAL, and tool table. `evidence/` contains an exact bounded
QtPyVCP excerpt, an exact 27-event edge-monitor excerpt covering the contact,
eight repeats, ninth edge, reposition and stop, and the frozen read-only
controller/HAL snapshot. `prerequisite_roots/` binds the sealed Attempt-6
pre-load manifest and hash inventory.

All source runner and output copies were verified byte-identical. All accepted
row identities, trace topology, counter invariants, closure ownership, and
quality limits passed an independent audit. `SHA256SUMS` binds every regular
file below this archive except itself.

The inspection and archive operation issued no LinuxCNC program-control,
program-load, Cycle Start, Resume, MDI, homing, motion, HAL write, or standalone
`rs274` command. Source output files were copied without modification.
