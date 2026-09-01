# TWP Sphere Full Cycle B+5 - T4 Operator Plan

Date: 2026-09-01

## Purpose

This supervised test validates the complete CAM-style lifecycle from the
standard B0/C0 sphere-top start. The program establishes the sphere reference,
positions the physical probe for B+5, enters TWP through the Fusion/Fanuc
`G68.2` / `G53.1` sequence, probes, exits through `G69`, returns to B0/C0, and
checks physical closure. It does not change any work offset, tool-table value,
or TCPC calibration coefficient.

Use only:

- launcher: `launch_xyzbc_ssi_twp_probe_validation.sh`
- INI: `5th_axis_xyzbc_ssi_tcpc_probe_basic_twp_probe_validation_2026083101.ini`
- program: `twp_sphere_full_cycle_bplus5_t4.ngc`

## Operator Setup

1. Keep the sphere fixed in the position used by the accepted Stage 1 run.
2. Start the dedicated TWP validation configuration and home all five joints.
3. Install T4 in its repeatable orientation. At B0/C0 apply `M61 Q4` and
   `G43 H4`; confirm public `G43.4` TCPC is off.
4. Position the probe at the standard start, 3-5 mm above the accessible sphere
   surface along the B0/C0 probe axis. The sphere-to-post direction remains
   `X- Y+ Z-`.
5. Confirm the spindle and laser are off and all probe inputs are quiet.
6. Load the full-cycle program. It has one operator hold, the initial `M0`.
   Recheck the setup and then resume once. Do not jog, use MDI, restart from a
   line, or alter offsets during the cycle.

## Program Sequence

1. Measure two four-contact WORLD references at B0/C0.
2. Move the physical probe-ball center to a common world point 80 mm above the
   measured sphere center.
3. Index B from 0 to +5 degrees in world mode with TWP and TCPC clear.
4. Approach the B+5 sphere-top start along the reached probe axis.
5. Execute the literal postprocessor transition:

   ```ngc
   G68.2 X0 Y0 Z0 I90 J5 K-90
   G53.1
   ```

6. Verify a reversible 1 mm local +Z move, then measure two four-contact TWP
   references at B+5/C0.
7. Execute `G69`, retract along the B+5 probe axis, return through the common
   80 mm world-clearance point, and index back to B0/C0.
8. Approach the standard B0 sphere-top point, measure two closing WORLD
   references, lift world Z by 25 mm, and finish with TWP/TCPC off.

The full test makes 24 gated `G38.3` contacts. B/C motion is limited to the two
world-mode transitions. There are no clearance-test holds or fast exploratory
moves.

## Acceptance

The program fails closed unless all of these hold:

- exactly one gated edge per contact and 24 total gated contacts
- every two-pass center pair is within 0.100 mm
- every measured V diameter is 29.9 to 30.5 mm
- every four-contact radial residual is at most 0.250 mm
- opening-to-closing B0 world-center closure is at most 0.100 mm
- the transformed B+5 TWP center is within 0.250 mm of the mean B0 world center
- the commissioned length-aware model remains valid and T4/H4 remains active
- the reached rotary pose is B+5/C0 and the completed return is B0/C0

Pass diagnostics append to `twp-sphere-full-cycle-bplus5-t4-passes.csv`. A
single accepted full-cycle row appends to
`twp-sphere-full-cycle-bplus5-t4-results.csv` only after every final gate passes.

## Recovery

Do not resume part-way through this test. After any Stop or Abort while TWP may
be active, keep the machine stationary. If controller state is healthy, issue
`G69` and verify ready world type 0 with TWP clear. If state health is uncertain,
close LinuxCNC completely, restart the dedicated configuration, home, reapply
T4/H4 at B0/C0, return to the standard sphere-top start, and run from the
beginning.

The program's guarded probe routine retracts to each contact start before
evaluating a failed touch. Program-detected active-TWP faults request `G69`
before aborting, but operator recovery must still verify the actual controller
state before any jog or restart.

## Offline Validation

Static program, lifecycle-order, O-code structure, coordinate-source, and CSV
schema checks pass. With the physical controller closed, the dedicated
full-cycle runtime fixture executed the actual production G-code against a
fixed simulated sphere and passed:

- B0/B+5/B0 reached and returned with exactly one TWP entry and exit
- no B/C motion while TWP was active
- minimum rotary-transition sphere clearance `79.734424 mm`
- reversible local +Z preflight `1.000000 mm`, zero return closure
- 24/24 contacts and six complete pass rows
- WORLD return closure `0.000410 mm`
- transformed B+5 TWP center error `0.000606 mm`
- final B0/C0 world state, TWP/TCPC clear, and 25 mm safe lift
- byte-identical restoration of both production evidence CSVs after shutdown

The program is ready for the first supervised physical full-cycle run. Loading
or starting it still requires explicit operator clearance.

## Physical Attempt 1 - Accepted

The first supervised physical run passed on 2026-09-01. It completed the full
B0/B+5/TWP/B0 lifecycle, 24/24 gated contacts, six pass rows, and one accepted
result row. WORLD return closure was `0.006120 mm`; transformed B+5 TWP center
error was `0.039035 mm`. Full metrics, the initial 0% rapid-override wait, seven
ungated-pulse provenance, and final state are recorded in
`TWP_SPHERE_FULL_CYCLE_BPLUS5_T4_CLOSEOUT_2026090101.md`.
