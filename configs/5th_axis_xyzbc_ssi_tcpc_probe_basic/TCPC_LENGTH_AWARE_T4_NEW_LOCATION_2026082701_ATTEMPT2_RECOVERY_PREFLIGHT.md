# T4 New-Location Attempt-2 Recovery Preflight

Status: `HISTORICAL PREFLIGHT PASS - ATTEMPT RETIRED AT SEQUENCE 21`

Recorded: `2026-08-27 18:14 +07`

## Frozen Release

- identity: campaign `2026082701`, mode `36`, attempt `2`
- model: `2026082601`, T4/H4 `229.407000 mm`, q=`0`
- probe calibration: `#3032=0.154742`
- runner: `nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.ngc`
- runner SHA-256: `c027a0bab19f403e5e625f01fb50d6d050b51188fa0a0885dbaa795035b5c758`
- exact start: `X2501.941254485 Y696.899347451 Z-280.866128272 B0 C0`

Attempt 2 has six isolated, exact header-only output files. It may be run once
only. Any execution stop, fault, output append outside the intended run, or
machine setup change retires this identity.

## Recovery Contract

- preserve sealed Attempt-1 canonical rows `1..17`
- exclude all of the incomplete Attempt-1 row-18 prefix
- recovery rows `1..9`: repeated B0 sweep and continuity evidence
- recovery rows `10..16`: deliberately absent
- recovery row `17`: repeated B-5/C0 continuity evidence
- recovery rows `18..101`: reacquired canonical data
- exact recovery outputs: `94/94/94` summary rows, `29` closures, and
  `752/752` contact/gap transactions
- exact composite: Attempt-1 rows `1..17` plus recovery rows `18..101`
- hard cross-attempt bridges at canonical rows `9` and `17`, each limited to
  `0.050 mm`
- one initial M0, no M1, no motion before M0, no later hold, and no whole-pose
  retry

Every successful G38 still requires raw/mux agreement, exactly one gated
motion edge, zero gated repeat edges, a released probe, and valid live/model
state. Only matched raw/mux activity while the real-time G38 gate is closed is
allowed up to the frozen bound of eight. The first post-M0 baseline must be
completely quiet.

## Verification

- primary validator: `validate_tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.py`
- primary validator SHA-256: `8eb205238aa3507484ce1f17201fdb4f0f2cbe29507157c833af94c70b7c39c5`
- Python compile: `PASS`
- primary `--static`: `PASS`
- primary `--preflight`: `PASS`
- primary mutation `--self-test`: `PASS`
- independent audit: `audit_tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.py`
- independent audit SHA-256: `51aac8c72dd42ab651154b017cc44c6d220f721e254312606615ed4004c438b3`
- independent audit: `PASS (171 checks)`
- reachability analyzer SHA-256: `06c7b69cdafc05c086a86c1ee56295db17f4c38160414fba0ae4219a1202c50c`
- reachability self-test and regenerated report: `PASS`
- reachability samples: `28,734` over `94` recovery poses
- worst configured-limit margin after all reserves: `181.641553 mm` at J2

Both validators are ordinary-file readers. They import no LinuxCNC, HAL, or
subprocess module and do not invoke rs274. A standalone rs274 parse was
deliberately not run because LinuxCNC is active; the previously reviewed
runner primitives and subroutines remain byte-equivalent to Attempt 1.

## Sealed Prerequisite

Attempt 1 is retired and sealed at
`calibration_runs/20260827_1754_campaign2026082701_t4_new_location_attempt1_partial_gap_abort_seq18`.
Its 21-entry inventory verifies and its root `SHA256SUMS` SHA-256 is
`2cef1968a26d61cf3f14c6a8807541ce3462f92a8927e6a44e643901234ac6f2`.
The accepted 17 rows and their first 136 contact/gap transactions pass. The
rejected row-18 prefix is identified by its terminal matched `4/4/0`
raw/mux/gated gap and is not used in the composite.

## Live Pre-Load State

At `18:12 +07`, LinuxCNC was enabled, homed on joints 0..4, idle, queue zero,
in position, unpaused, and stationary. T4/H4 was active with tool offset
`Z229.407000`; G43.4 was active, the spindle was stopped, and the live probe
input was clear. The length model was configured and valid at q=`0`, fault
code `0`; B/C SSI invalid signals were clear. Commanded XYZBC was
`2501.941254485, 696.899347451, -280.866128272, 0, 0`; actual B/C was within
`0.000024 deg`. Raw/mux/gated counters were `713/713/225`.

The selected file was still the retired Attempt-1 runner at this checkpoint.
Loading the frozen recovery runner is authorized by the operator's explicit
clearance. Loading does not authorize Cycle Start, Resume, MDI, homing, or
motion.

## Sealed Pre-Run Archive

The complete pre-run evidence package is
`calibration_runs/20260827_1817_campaign2026082701_t4_new_location_attempt2_recovery_preflight`.
Its 65-entry inventory verifies, contains no symlinks or special files, and
the root `SHA256SUMS` SHA-256 is
`bf8230e538399364cbe36d1234b82e7bec656e7a7ff1c24b4f71dcd8e71d8f82`.
The archive was sealed before the recovery runner was loaded or started.

## Post-Load Checkpoint

At `2026-08-27 18:19 +07`, LinuxCNC accepted and selected the exact frozen
runner. The commanded and actual coordinates did not change. LinuxCNC remained
enabled, homed, idle, queue-zero, unpaused, in position and stationary with
T4/H4, G43.4, model q0, spindle stop, clear probe/fault signals and valid SSI.
`current/read/motion` lines were `0/0/0`, all six acquisition outputs remained
exact header-only files, and counters remained `713/713/225`. No Cycle Start,
Resume, MDI, homing, or motion command was issued.

## Operator Boundary

After load, the operator may press Cycle Start once to reach the sole M0. At
that hold, do not jog, use MDI, alter tool/WCS/TLO, or touch the probe. Confirm
laser off, sphere and nearby fixtures secure and clear, post direction
base-to-sphere X+/Y-/Z+, and observe a fresh continuously quiet 30-second
interval. Resume remains a separate operator decision after those checks.

## M0 Checkpoint

The operator pressed Cycle Start once and reached the sole M0 without motion.
From `2026-08-27 18:21:36` through `18:22:50 +07`, the 100 Hz diagnostic
monitor recorded a continuous `74.400 s` quiet interval. It contained only
heartbeat rows; counters remained `713/713/225`; all raw, mux, gated,
gate-enable, abnormal, fault-pause, motion-probe and motion-type values stayed
clear; and XYZBC remained unchanged. All six acquisition outputs were still
header-only. The workshop is closed and no further laser work will occur.
Physical sphere, fixture-clearance, and post-direction confirmation remains
the final operator gate before Resume.

## Attempt Closeout

The operator confirmed the physical gate and resumed. At
`2026-08-27 18:48:46 +07`, the runner stopped itself on canonical sequence 21
B-5/C225 after the -V contact triggered at `0.609798 mm`, below the 1 mm
minimum-travel guard. Attempt 2 is retired and must not be resumed or reused.
Accepted recovery rows are exactly `1..9,17..20`; all sequence-21 traces are
excluded. The authoritative forensic record is
`TCPC_LENGTH_AWARE_T4_NEW_LOCATION_2026082701_ATTEMPT2_RECOVERY_PARTIAL_REPORT.md`.
