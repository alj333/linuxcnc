# TCPC Relocated-Sphere Campaign 2026082403

Status updated `2026-08-24T20:52:23+07:00`.

Superseded before primary acquisition by campaign `2026082404`; the T4/T3
measurement CSVs remained header-only. This file and its frozen identities are
retained as campaign-03 provenance.

This is the authoritative next-stage procedure. It supersedes the operator
orders in campaigns `2026082201` and `2026082202`; their data and execution
history remain valid provenance and must not be appended to this campaign.

No HAL, INI, tool-table, B/C zero, rigid geometry, or correction coefficient
has been changed from the completed measurements. The active correction is the
existing short-probe-derived candidate under test.

## Offline Finding Before Relocation

- T4 current centered error: `0.132379 mm RMS / 0.283916 mm maximum`.
- The constrained existing-angle fit predicts T4 improvement to
  `0.106117 / 0.223753 mm`, but worsens the untouched trusted T3 maximum from
  `0.375766` to `0.396364 mm`. It is rejected.
- Full additive fits overfit: the best T4 training maximum is `0.081212 mm`,
  while leave-one-B-out expands to approximately `0.961 mm`.
- The trusted B0 long-minus-short signal corresponds to a rotating lateral
  vector of `X -0.001632 / Y -0.033841 mm` across `100.800271 mm` length
  separation, with `0.005299 mm` maximum reconstruction residual. This is real
  length-dependent evidence but remains confounded with probe seating,
  spindle wear, and rail-position error. It is not a loadable correction.
- Therefore no current-data parameter family is authorized for live loading.

The reproducible analysis is `fit_tcpc_dual_probe.py`; its report is
`TCPC_DUAL_PROBE_OFFLINE_FIT_REPORT.md`.

## Current Passive Machine Check

At the capture time LinuxCNC was enabled, idle, in position, and all five
joints were homed. T4/H4 `229.407000 mm`, TCPC, and the persistent correction
were active; spindle speed and current velocity were zero. Commanded machine
position was approximately:

```text
X1024.747449 Y844.756916 Z-281.365857 B0 C0
```

The selected file was still the stopped historical
`tcpc_t4_mode19_high_b_combined.ngc`. This observation is not motion authority
and must be revalidated before the anchor. The large positive-Y relocation is
consistent with clearing the old B90/C270 soft-limit failure, but only the
measured anchor replay can release later paths.

At `2026-08-24T18:36:02+07:00`, a load-only request was refused without
changing the selected file or machine position. Passive process inspection
then showed that the task/interpreter process was no longer present while the
GUI, NML server, I/O, and realtime motion components retained stale idle
status. Do not rely on that displayed state and do not attempt to resume it.
The next operator stage starts with a clean LinuxCNC restart using this config,
followed by homing and re-establishing the T4 anchor entry contract. Loading a
program is not authorization to run it.

## Anchor Attempt 1 Result

T4 anchor attempt 1 completed at `2026-08-24T18:57:33+07:00` and passed the
corrected wrapped-angle validator. The accepted center is:

```text
X1024.957789 Y844.074417 Z-302.468115
```

Center correction was `0.008821 mm`, pass-to-pass center delta was
`0.019449 mm`, and the largest radial contact residual was `0.056502 mm`.
The logged rotary pose was `B-0.000010 C+0.000320 deg`; the B SSI value near
`-360 deg` is the wrapped equivalent of B0 and is within the runner's
`0.01 deg` gate.

Combined configured-limit replay passed over 29,349 sampled T4/T3 path points.
The worst remaining linear margin is `182.860993 mm` after the 2 mm center and
3 mm path/model allowances. All 85 live replay-geometry pins matched the clean
config within `0.0001`.

Generated no-contact runner identities:

```text
T4 f4ec525156b6692c6b6f5c1ffd13c58104cb21371e588ee3b65ca654302ce22d
T3 0fe18a880bea26fd7f977ea44e59bd1e7f71fa4604acbda7e6a5410df04ddb08
```

These files are generated but not yet operator-qualified. Every positive-B
pose has a corresponding negative-B pose at the same C angle and with the same
multiplicity. The envelopes retain one initial pre-motion `M0` and have no
intermediate B-block holds. The next physical stage remains the T4 no-contact
envelope. The completed anchor provenance is in
`calibration_runs/20260824_1900_relocated_sphere_anchor_attempt1_complete`.

## Post-Anchor Task-Process Loss

After the accepted anchor and all offline anchor/reachability/envelope checks,
a load-only request for the T4 no-contact envelope returned `-1`/timed out.
The selected file remained `tcpc_relocated_sphere_t4_anchor.ngc`, commanded and
actual XYZBC did not change, and no motion occurred. Passive process inspection
then found that `milltask` PID `353251` was absent while the GUI, NML server,
I/O, HALUI, realtime motion, and stale `interp353251` HAL entry remained.

The final anchor message was emitted only after both accepted CSV rows had
been written and closed. Independent validation passed, so this controller
fault does not invalidate or justify repeating the anchor. Its accepted final
top-clear endpoint remains approximately:

```text
X1024.957785 Y844.074417 Z-279.622857 B-0.000010 C+0.000320
```

Do not load, start, or resume any program in the current controller session;
the displayed idle state is stale and is not motion authority. A clean restart
is required before the no-contact stage. The exact termination point was not
observed in any of the three incidents. In the best-bounded case, direct
process inspection found PID `314951` alive at `18:13:46` and absent at
`18:27:57`, more than four minutes before the failed file-open request at
`18:32:18`; the nearby `kill 344915` targeted a separate hung offline analyzer.
The later file open therefore detected an existing loss in that incident.
Deferred previous-program close/reset remains one controlled hypothesis, not
an established cause. Failed CSV logging and anchor measurement failure are
not supported. The next launch must preserve exit-status/signal evidence and
continuously record task liveness. Incident evidence is in
`calibration_runs/20260824_1917_post_anchor_task_lost`.

The disabled load-only diagnostic completed on `2026-08-24`. Attempt 1 did
not test file open: Probe Basic received native `SIGBUS` at `19:52:31`, then
the LinuxCNC launcher shut down the session and deliberately sent `SIGKILL` to
the still-healthy task after its cleanup grace period. This is a separate GUI
failure class and does not match the three earlier milltask-only process
patterns. Attempt 2 loaded diagnostic file A at `20:06:49`, remained disabled
and idle for more than 20 minutes with one-second liveness/status capture, and
loaded file B at `20:27:30`. Both opens returned `RCS_DONE`; commanded and
actual XYZBC deltas were exactly zero, the original task PID/start time
survived, and neither file was executed. Close/open was not reproduced as an
idle load-only failure. No TCPC coefficient or production machine setting was
changed.

At the `2026-08-24T20:50:46+07:00` load-only handoff, the diagnostic INI was
running with all five axes homed, machine enabled, T4/H4 `229.407000 mm`, TCPC
active, TWP clear, spindle stopped, and probe inputs clear. The revised T4
no-contact envelope was selected at line 0 and had not been started. Commanded
position was approximately `X1024.747449 Y844.756916 Z-281.365857 B0 C0`,
`1.883639 mm` from the accepted top-clear endpoint. The same instrumented task
PID and start time survived the reload and XYZBC did not change. This is a
recorded load-only state, not authorization for motion; the operator owns Cycle
Start and Resume.

## Required Order

1. T4 anchor, mode 22: `tcpc_relocated_sphere_t4_anchor.ngc`.
2. Validate its one result/state row with
   `analyze_tcpc_relocated_sphere_anchor.py`.
3. Run `analyze_tcpc_relocated_sphere_reachability.py`. It checks the exact
   frozen T4 and T3 program contracts, Cartesian AXIS limits, inverse JOINT
   limits, probe paths, and rotary transits. A PASS still does not prove
   probe-body, cable, post, or fixture clearance.
4. Run `generate_tcpc_relocated_sphere_envelopes.py`. It refuses to publish
   either no-contact runner until the anchor and combined T4/T3 reachability
   replay pass. It also rejects a grid unless every positive-B pose has the
   matching negative-B pose at the same C angle and multiplicity. Operator-
   qualify the generated envelopes under continuous visual observation for
   body, stylus, cable, sphere, and post clearance. There is one initial
   pre-motion `M0`; after operator Resume the envelope runs continuously to
   `M2` without intermediate B-block holds.
5. T4 primary training, mode 23: `tcpc_relocated_sphere_t4_primary.ngc`.
6. Fit candidates using T4 only. Do not inspect T3 to select a family.
7. T3 untouched verification, mode 24:
   `tcpc_relocated_sphere_t3_verification.ngc`.
8. Validate both completed datasets with
   `analyze_tcpc_relocated_sphere_campaign.py`; only then compare the frozen
   T4-selected candidate against T3.

Frozen runner identities:

```text
T4 anchor       4d1db5b89ae9a3b833381a64c8667aa475e0adc17b00fb2c49e318f9ace0fcaf
T4 primary      bd1a9ee59d9ee2c7640ebaf2832779bbcfa17c13691b354ac182d7dae3ce34fd
T3 verification 8163d996b85c5d6b764be28b81ca9950bc94106a80c6a94d46a0c8acfb718e49
```

The operator owns every Cycle Start, Feed Hold, Abort, recovery move, and tool
change. Offline preparation or program loading never authorizes motion.

## Anchor Entry Contract

- Certified 30 mm sphere secured; post from sphere toward base remains
  `X-,Y+,Z-`.
- T4 installed in its normal keyed orientation; live T4 and G43 H4 all agree
  at `229.407000 mm`.
- B0/C0, TCPC active, TWP clear, spindle stopped, all axes homed.
- Probe ball is 3-5 mm above the sphere at the operator-confirmed top point.
- Anchor output files contain headers only before attempt 1.
- One executable M0 occurs before motion. The runner issues no rotary command
  in its one-pose body and uses eight nominal contacts: two four-contact passes.
- A pre-G38 fault at a side start can leave the probe beside the sphere. Do not
  resume from that block; manually return to the reviewed top start, archive
  the partial, advance the attempt, and restart.

## T4 Primary Grid

The primary contains 59 accepted rows:

```text
1-9    B0:  C0,45,90,135,180,225,270,315,0
10-14  B+30 C0,90,180,270,0
15-19  B-30 C0,90,180,270,0
20-24  B+45 C0,90,180,270,0
25-29  B-45 C0,90,180,270,0
30     B0 C0 midpoint
31-35  B+60 C0,90,180,270,0
36-40  B-60 C0,90,180,270,0
41-45  B+90 C0,90,180,270,0
46-50  B-90 C0,90,180,270,0
51-59  B0:  C0,45,90,135,180,225,270,315,0
```

Balanced signs separate odd `sin(B)`/`sin(2B)` behavior from even
`1-cos(B)`. B45 is included because the current T4 maximum occurs there and
the mid-B envelope peaks there. Tilted C obliques are excluded: their U or V
paths align with the 45-degree post. The unsupported `sin(B)*sin(2C)` family
must remain frozen unless a separate physically cleared oblique campaign is
later justified.

The 59-pose T4 grid is sufficient for the first relocated-sphere fit: it
balances nine B levels, covers all C quadrants, includes B0 obliques, and adds
same-pose block/run closures. More stable T4 poses may be added after this
baseline only if residuals show an identifiable gap. Do not add tilted
C45/C135/C225/C315 poses merely for count; they face the stand geometry. Any
expanded grid requires a new campaign ID, no-contact qualification, frozen
runner hash, and matching analyzer contract before execution.

Each multi-row block and the complete run have a `0.050 mm` same-pose closure
gate. `<=0.010 mm` is excellent for this machine. The error gate within a pose
remains wider because it is not a same-pose closure measurement.

## T3 Holdout Grid

The shorter untouched run contains 31 rows:

```text
1-5    B0   C0,90,180,270,0
6-10   B+45 C0,90,180,270,0
11-15  B-45 C0,90,180,270,0
16     B0 C0 midpoint
17-21  B+90 C0,90,180,270,0
22-26  B-90 C0,90,180,270,0
27-31  B0   C0,90,180,270,0
```

T3 rows are verification only. T3 has its own no-contact body-clearance check
because the shorter probe puts the spindle body closer to the sphere.

## Probe Electrical Handling

- The HAL gate exposes probe contact to motion only during G38.
- The 10-second post-contact quarantine remains active.
- There is no 20-second settle dwell in these runners.
- T4 is the primary probe because it remained electrically stable.
- If T3 shows its known LED glow, repeated spontaneous pulses, or unstable
  release, stop and reseat it. Do not splice rows across a reseat or resume a
  missed pose.

## Release Boundary

A calibration candidate must improve T4 training and whole-B holdouts, remain
identifiable under the balanced grid, improve the frozen T3 prediction without
refitting, and preserve closures. Machine mechanical error that does not scale
consistently with probe length must not be forced into TCPC geometry.

The reachability replay reserves an empirical 2 mm center envelope plus a
3 mm path/model allowance and requires 10 mm remaining configured linear
margin. The probing runners do not enforce the 2 mm anchor envelope before
motion; any accepted center outside it invalidates the reachability release.
The replay checks configured HAL/INI geometry, so a clean launch and unchanged
live kinematics are prerequisites. Physical stand, holder, probe-body, and
cable clearance is released only by the operator-observed no-contact runners.
