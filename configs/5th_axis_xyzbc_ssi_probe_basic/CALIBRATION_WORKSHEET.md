# XYZBC Calibration Worksheet

Use this worksheet with the Probe Basic calibration config:

- launcher: `configs/5th_axis_xyzbc_ssi_probe_basic/launch_xyzbc_ssi_probe_basic.sh`
- ring qualification program: `nc_files/calibration/50mm_ring_probe_qualify.ngc`
- ring verification program: `nc_files/calibration/50mm_ring_probe_verify.ngc`
- sphere center measurement program: `nc_files/calibration/30mm_sphere_measure_current_pose.ngc`

## Ground Rules

- Do all early calibration work in the Probe Basic `trivkins` config. Do not enable TCPC yet.
- Fix the `50 mm` ring and `30 mm` sphere rigidly to the table and leave them there for the whole session.
- Use the same probe stylus, probe feedrates, and probing strategy for the whole dataset.
- In Probe Basic, set the probe tool number and probe parameters in the UI, then press `UPDATE PROBE PARAMS` once after startup so the values are mirrored into `#3014..#3036`.
- Current wireless probe tool is `T3`; set Probe Basic probe tool number to `3` before pressing `UPDATE PROBE PARAMS`.
- Current accepted probe calibration offset from repeated ring calibration runs on 2026-04-26 is `0.134533`.
- Keep calibration probe feedrates slow for this work: use `50 mm/min` slow probe, `100 mm/min` fast probe, and keep traverse/transfer moves at or below `300 mm/min`.
- Probe Basic does not provide a native sphere calibration workflow. The 30 mm sphere routine is a custom wrapper that only reuses Probe Basic's basic setup values where they map cleanly: probe tool, feeds, max distances, clearances, and calibration offset.
- Do not edit WCS/WCO during the sphere data collection pass. Keep one coordinate system active for the whole session.
- The calibration wrappers preserve the active WCS. Use a deliberate calibration WCS for the whole session. On 2026-04-26 the operator allowed use of `G54` after saving the project offsets externally.
- This config's startup modal includes `G54`, so after restart or program end, verify the active WCS before each run.
- `G55` is reserved for staff 3-axis setup work as of 2026-04-27. Do not use,
  probe, overwrite, or adjust `G55` for calibration until the operator releases
  it.
- Before every sphere run, manually jog to a safe clearance position above the sphere at the target `B/C` pose. The current sphere cycle does not auto-index rotaries on purpose.
- The sphere cycle appends numeric results to `sphere-center-results.csv` in this config directory.
- Practical TCPC target for this large steel machine is about `0.10 mm`; do not chase thermal drift below the machine's current no-temperature-compensation envelope.
- Most intended 5-axis work is vacuum-formed part cutout, so prioritize repeatable safe TCPC behavior over ultra-fine mold-finishing accuracy.
- Small mechanical errors, backlash, and compliance are expected. Treat those as future refinement work, not as blockers for the first TCPC geometry fit.

## Step 1: Ring Qualification

Purpose:

- qualify the probe
- establish the calibration offset used by the sphere center cycle

Program:

- `nc_files/calibration/50mm_ring_probe_qualify.ngc`

Start condition:

- probe tool loaded
- spindle stopped
- probe tip above the left inside edge of the ring
- tip roughly centered in `Y`
- safe `Z` above the ring top

What to record:

- suggested calibration offset from the Probe Basic calibration widget after the run

Repeat until stable:

- run the qualification cycle
- confirm the Probe Basic calibration offset field contains the accepted value
- run the verify cycle at least `3` times
- stop only when average diameter and center repeatability are stable

Recommended acceptance before moving on:

- averaged measured ring diameter within a few microns of `50.000 mm`
- center repeatability at the ring well below the geometry error you are trying to solve

## Step 2: Sphere Baseline At B0 C0

Purpose:

- establish the base sphere center reference with the machine at `B0 C0`

Program:

- `nc_files/calibration/30mm_sphere_measure_current_pose.ngc`

Before each run:

- set the target `B/C` pose manually
- jog to a safe point above the sphere top
- jog so the probe is roughly over the sphere center in `X/Y`
- confirm the Probe Basic calibration offset field is current and click `UPDATE PROBE PARAMS` if you changed it

What the sphere program logs:

- `B/C` pose
- probe tool number and calibration offset used by the run
- relative center `X/Y/Z`
- absolute machine center `X/Y/Z`
- equator diameters measured in `X` and `Y`
- top contact `Z`

Run count:

- measure `B0 C0` at least `3` times before using it as the baseline

Use the average of those `B0 C0` runs as the baseline reference center.

## Step 3: C-Axis Sweep

Purpose:

- isolate pure `C` geometry errors with `B` fixed at zero

Recommended pose list:

- `B0 C0`
- `B0 C90`
- `B0 C180`
- `B0 C270`
- repeat `B0 C0`

What to look for:

- solved sphere center should stay in one place
- drift in solved center across the `C` sweep points to `C` zero / axis-center / geometry error

## Step 4: B-Axis Sweep

Purpose:

- isolate `B` tilt-axis geometry with `C` fixed
- for the head-head machine, collect this with a B-aware vector routine, not
  the `B0` machine-Z sphere routine

Recommended first-pass pose list:

- `B0 C0`
- `B+15 C0`
- `B-15 C0`
- `B+30 C0`
- `B-30 C0`
- repeat `B0 C0`

Recommended second-pass widening if needed:

- `B0 C0`
- `B+45 C0`
- `B-45 C0`
- `B+60 C0`
- `B-60 C0`

What to look for:

- center movement versus `B` angle is the key signal for tilt-axis pivot location errors
- raw contact residuals and repeatability must be checked before fitting B-axis
  geometry, because local rack/screw error and alignment error can otherwise be
  mistaken for rotary pivot error

B-axis vector probing rule:

- At nonzero `B`, the probe/stylus vector is no longer machine `Z`.
- Use a local head frame: `W` along the probe vector, and `U/V` perpendicular
  side-probe vectors.
- First run a short non-contact vector dry-run to verify signs and clearance.
- Then log raw contact points and fit sphere center offline before using the
  data in TCPC geometry.
- Current B-axis vector routine:
  `nc_files/calibration/b_axis_vector_sphere_current_pose.ngc`.
- Current B-axis two-pass vector routine:
  `nc_files/calibration/b_axis_vector_sphere_2pass_current_pose.ngc`.
- Current B-axis vector logs:
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-raw-points.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-sphere-results.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-2pass-raw-points.csv`
  - `configs/5th_axis_xyzbc_ssi_probe_basic/b-axis-vector-2pass-results.csv`
- End-of-day status on 2026-04-26:
  - `B+15 C0` repeated tightly after manual local `U` correction
  - `B-15 C0` repeated tightly after manual local `U/V` correction
  - before collecting `B+30/B-30`, validate the two-pass routine at a known
    pose, then use it for the remaining B-axis data
- 2026-04-27 update:
  - two-pass routine validated at `B+15 C0`
  - pass 2 accepted center
    `X=226.486276 Y=352.897855 Z=-291.117802`
  - `B+30 C0` pass 2 accepted center
    `X=151.969455 Y=352.913688 Z=-321.714304`
  - `B-30 C0` pass 2 accepted center
    `X=460.527766 Y=352.638896 Z=-322.390804`
  - closing `B0 C0` pass 2 accepted center
    `X=306.338526 Y=352.821813 Z=-280.762445`
  - closing `B0 C0` has a caveat: staff started epoxy prep on a mold on the
    machine and the start was bumped, so do not treat this as the final thermal
    or setup-stability reference without a later repeat
  - one extra full `B0 C0` two-pass repeat was logged after the bumped start;
    keep it in the raw CSV record but exclude it from the first fit candidate
    because the run was unintended and the machine environment was disturbed
  - machine probing is paused until the mold/epoxy work is clear and the sphere
    setup is stable again
  - next scope is offline TCPC candidate fitting from the accepted C-sweep and
    curated B-vector data; see `TCPC_FIT_NEXT_SCOPE.md`
  - TCPC visual validation later confirmed B correction direction at `C0`,
    `C90`, and `C180`; the attempted positive C quadrant continuation exposed
    the single-turn C SSI wrap at physical `C180`
  - the TCPC test config now uses `rotaryunwrap` to feed joint 4 continuous C
    feedback nearest the commanded C angle
  - `C170 -> C185 -> C170 -> C0` unwrap validation passed at `F50`, then the
    `C270` quadrant check passed with correct `B2/B0` TCPC correction direction
  - slow no-cut TCPC correction direction has now been visually confirmed in
    all four C quadrants; next TCPC work should be fixed-tip deviation checks,
    not more direction-only checks
  - first automated small-pose fixed-tip TCPC validation completed on
    2026-04-27 with
    `nc_files/calibration/tcpc_small_pose_vector_sphere_auto.ngc`
  - accepted pass-2 fixed-tip drift from the first `B0 C0` baseline was about
    `0.096 mm` at `B+2 C0`, `0.031 mm` at `B-2 C0`, `0.115 mm` at
    `B+2 C+10`, `0.132 mm` at `B+2 C-10`, and `0.048 mm` on the closing
    `B0 C0` repeat
  - this is close enough to the practical `0.10 mm` target to pause TCPC
    geometry work and characterize X/Y reversal backlash and commanded-distance
    accuracy before further fitting; see `XY_BACKLASH_DISTANCE_NEXT_SCOPE.md`
  - 2026-04-28 first X/Y backlash pass measured about `0.035-0.040 mm` X lost
    motion and about `0.029 mm` Y lost motion at the tested location;
    commanded-distance verification was deferred because suitable tooling was
    not available
  - 2026-04-28 repeat automated small-pose fixed-tip TCPC validation completed
    with the table mold present and B kept inside the current `+/-50 deg`
    clearance limit
  - program feeds for that run were probe `F50`, linear positioning `F400`,
    and rotary index `F100`
  - accepted pass-2 drift from the first `B0 C0` baseline was about
    `0.094 mm` at `B+2 C0`, `0.017 mm` at `B-2 C0`, `0.107 mm` at
    `B+2 C+10`, `0.111 mm` at `B+2 C-10`, and `0.002 mm` on the closing
    `B0 C0` repeat
  - this is inside the current `0.2 mm` practical TCPC target; do not adjust
    offsets blindly from this small pose set
  - a known possible B-axis assembly issue is spindle centerline offset from
    the B rotation center; legacy configs show prior fractional `5axiskins`
    `x-offset` corrections, but those values are not directly portable to
    current `headheadkins`
  - treat current `headheadkins.nominal-b-to-tool.x = -0.668710` as the active
    first-pass representation of that lateral B-to-spindle offset, but note
    that the current X-heavy residual is also sensitive to B effective radius
    / `nominal-b-to-tool.z`, B zero, and head alignment
  - 2026-04-28 first wider mixed-pose fixed-tip TCPC validation completed with
    `B+5/B-5 C0` and `B+5 C+/-20`
  - accepted pass-2 drift from the first wide `B0 C0` baseline was about
    `0.061 mm` at `B+5 C0`, `0.037 mm` at `B-5 C0`, `0.142 mm` at
    `B+5 C+20`, `0.078 mm` at `B+5 C-20`, and `0.007 mm` on the final
    closing `B0 C0` repeat
  - the first full wide sweep had a wireless-probe false trip during the
    closing `B0 C0` correction move; nearby laser-cutter interference was the
    likely cause, and a closure-only resume completed the final repeat
  - this remains inside the current `0.2 mm` target; the largest error is
    mostly XY at `B+5 C+20`, so investigate C/B geometry interaction,
    alignment, and local X/Y mechanics before changing offsets
  - 2026-04-28 symmetric mixed-pose fixed-tip TCPC validation completed with
    `B+5/B-5 C+/-20`
  - accepted pass-2 drift from the first symmetric `B0 C0` baseline was about
    `0.138 mm` at `B+5 C+20`, `0.075 mm` at `B+5 C-20`, `0.045 mm` at
    `B-5 C+20`, `0.105 mm` at `B-5 C-20`, and `0.111 mm` on the final
    closing `B0 C0` repeat
  - the closing repeat is weaker than the prior wide-pose closure and was
    recorded as morning sun started heating the workshop; treat this run as
    useful diagnostic data, but do not fit TCPC offsets from it without a
    stable-temperature repeat or reverse-order confirmation
  - immediate rerun of the same symmetric program completed normally; the
    second run's first `B0 C0` was about `0.110 mm` from the first run's first
    `B0 C0`, but only about `0.011 mm` from the first run's closing `B0 C0`
  - tilted accepted pass-2 centers repeated between the two runs within about
    `0.016-0.022 mm` absolute, while the second run closed at about `0.008 mm`
    from its own starting `B0 C0`
  - this repeat supports treating the first run's large `B0 C0` closure shift
    as baseline drift or return-state behavior, not as direct TCPC geometry
    error
  - with a B-to-tip radius near `309 mm`, `0.108 mm` X shift at `C0` is only
    about `0.020 deg` of B angle, but B/C are closed-loop on direct SSI
    encoders at the rotary output, so a LinuxCNC backlash setting should not
    leave a static B/C output-position split if the feedback and SSI readback
    are repeating
  - future work still needs dedicated B/C feedback, backlash, and servo tuning,
    but the current TCPC fit should not infer rotary output-angle error unless
    the direct SSI logs show it
  - the symmetric TCPC program now also logs high-resolution B/C rotary state
    for future runs:
    `tcpc-symmetric-pose-vector-rotary-joint-state.csv` records LinuxCNC joint
    command/feedback, and `tcpc-symmetric-pose-vector-rotary-ssi-state.csv`
    records direct SSI absolute/zeroed/rawcount values plus microdegree
    following-error fields
  - the first run with high-resolution rotary logging completed the starting
    `B0 C0` and all four tilted poses, then stopped on a transient non-probe
    move trip before the final closing `B0 C0`
  - accepted tilted-pose drift from that run's starting `B0 C0` was about
    `0.119 mm` at `B+5 C+20`, `0.089 mm` at `B+5 C-20`, `0.114 mm` at
    `B-5 C+20`, and `0.091 mm` at `B-5 C-20`
  - direct SSI B feedback stayed within a few hundred microdegrees at the
    measured poses, far too small to explain a `~0.1 mm` TCP shift at a
    `309 mm` lever arm; this argues against B output-angle drift as the main
    cause of the mixed-pose pattern
  - trust direct SSI encoder data as the B/C output position unless logs prove
    otherwise, but still test B zero, C zero, B/C axis alignment, head
    squareness, and kinematic geometry mapping as separate TCPC setup items
  - first small real-machine TCPC geometry correction was applied in the TCPC
    test config only: `cal-b-to-tool.x = -0.100000 mm` and
    `cal-b-to-tool.z = +0.030000 mm`, mirrored to `headheadtwp.*`
  - `b-zero-offset` and `c-zero-offset` remain `0.000000` because the current
    sphere data cannot distinguish a small B angular zero error from a small
    B-to-tool X translation error without additional checks
  - offline prediction against the run 2/run 3 averaged symmetric residuals is
    modest: maximum tilted-pose drift should reduce from about `0.119 mm` to
    about `0.111 mm`; the main expected improvement is reduced C-sign Y/Z
    error, not removal of the common X-heavy residual
  - later visual checking caught that the vector probing files still used the
    old B lateral sign. Corrected vector convention is now `B+ C0` top/down
    vector motion = `X- Z-`, matching `headheadkins`.
  - the two corrected symmetric runs repeated well: tilted absolute centers
    repeated by about `0.016-0.023 mm`, and closing `B0 C0` was about
    `0.011-0.017 mm` from the starting `B0 C0`
  - a sign-corrected small TCPC correction of
    `cal-b-to-tool.x = -0.200000 mm` and
    `cal-b-to-tool.z = +0.160000 mm` was tested after restart, but rejected
    because all four tilted small poses got worse
  - the retained `cal-b-to-tool.x = -0.100000 mm` and
    `cal-b-to-tool.z = +0.030000 mm` correction was also cleared because it was
    rooted in the old wrong-sign vector data
  - current TCPC test config calibration corrections are reset to zero while
    keeping the nominal starting geometry unchanged; rerun the corrected
    symmetric vector program after restart to establish a clean baseline
  - zero-correction clean baseline was run twice after restart: tilted absolute
    centers repeated about `0.013-0.019 mm`, final closing `B0 C0` repeated
    about `0.0015 mm`, and all tilted poses remained within the current
    `0.2 mm` target
  - the starting `B0 C0` center shifted about `0.036 mm` between the two
    zero-correction runs, while final closing `B0 C0` repeated closely; with
    direct SSI closed-loop B/C feedback, treat this first as return-state,
    thermal, probe, linear-axis, structural, or alignment behavior unless SSI
    logs show actual rotary output-angle movement
  - keep TCPC calibration corrections at zero for now and do not fit new
    offsets from the small-angle dataset alone
  - TCPC work is paused on 2026-04-28 while the machine is used for 3-axis
    work; return using the TCPC test config only after the 3-axis task is clear
  - next prepared TCPC diagnostic is
    `nc_files/calibration/tcpc_b0_approach_reversal_sphere_auto.ngc`, which
    alternates `B+5 -> B0` and `B-5 -> B0` approaches and logs direct SSI
    rotary state to prove B/C output repeatability before blaming TCPC geometry
  - this diagnostic keeps B within `+/-5 deg`, uses probe `F50`, rotary
    indexing `F100`, and linear positioning `F400`
  - 2026-04-29 feed update for future TCPC validation programs: keep probe
    `F50`, increase linear positioning to `F600`, and increase rotary indexing
    to `F200`; do not edit the active B0 approach/reversal file while it is
    running
  - 2026-04-29 B0 approach/reversal diagnostic showed a repeatable
    `0.121722 mm` X split between `B+5 -> B0` and `B-5 -> B0`
  - direct SSI showed the B output position also split by `0.022202 deg`,
    about `64.7` raw counts, which matches about `0.119735 mm` at the
    `309 mm` B-to-tip lever arm
  - conclusion: trust the encoder data; it exposed that LinuxCNC B backlash
    compensation was shifting the rotary output position in the TCPC config
  - TCPC test config now sets B and C backlash compensation to zero; restart
    LinuxCNC and rerun the B0 approach/reversal diagnostic before changing TCPC
    geometry
  - post-restart rerun confirmed the fix: direct B SSI zeroed-position split
    from `B+5 -> B0` versus `B-5 -> B0` was `0.000000 deg`, raw SSI split was
    `0.0 counts`, and accepted sphere center split dropped to `0.004201 mm`
  - next TCPC geometry validation should rerun the corrected symmetric
    mixed-pose program with zero TCPC correction and updated `F600/F200`
    positioning/indexing feeds
  - the first post-fix symmetric run completed after one invalid probe
    double-pulse attempt; use only the final complete 12-row block
  - accepted post-fix tilted-pose drift from the starting `B0 C0` was about
    `0.089 mm` at `B+5 C+20`, `0.102 mm` at `B+5 C-20`, `0.099 mm` at
    `B-5 C+20`, and `0.099 mm` at `B-5 C-20`
  - closing `B0 C0` drift was only `0.004 mm`, so the remaining tilted-pose
    pattern is now useful TCPC geometry/alignment signal rather than the old
    backlash-compensation artifact
  - repeat of the same symmetric program was stable: closing `B0 C0` drift was
    `0.004 mm`, tilted-pose drift remained `0.091-0.101 mm`, and accepted
    centers repeated against the previous valid post-fix run within about
    `0.006 mm`
  - next recommended machine action is the expanded C-quadrant / B `+/-50`
    matrix, then an offline sensitivity fit for small B-zero and B effective
    radius / B-to-tool-vector adjustments
  - expanded TCPC data set is prepared as
    `nc_files/calibration/tcpc_expanded_pose_vector_sphere_auto.ngc`
  - expanded program uses C quadrants `C0/C90/C180/C270` and B groups
    `0`, `+/-10`, `+/-30`, `+/-50`, with B0 closures between groups
  - the sphere is on a `45 deg` post; the known clearance concern is around
    `C45` with B more negative than `-10 deg`, while `C225` is acceptable
  - the first expanded pass uses C quadrants only and avoids the known risky
    `C45 / B < -10` sector; it pauses between B groups for clearance checks
  - expanded logs use the `tcpc-expanded-pose-vector-*` CSV files
  - expanded run completed before the machine was handed back for 3-axis work:
    `64` result rows, `32` accepted pass-2 centers, and `320` raw point rows
  - accepted `B0 C0` closures from the first expanded baseline stayed tight:
    `0.006710 mm`, `0.011584 mm`, `0.010126 mm`, and final `0.017328 mm`
  - maximum group drift from each preceding `B0 C0` closure increased with
    B angle: `0.144343 mm` at `B0 C180`, `0.278010 mm` at `B-10 C0`,
    `0.796227 mm` at `B-30 C90`, and `1.316641 mm` at `B-50 C90`
  - expanded-run accepted rotary following error was small relative to the
    measured TCP residuals: about `229 microdeg` maximum absolute B following
    error and `2403 microdeg` maximum absolute C following error
  - no new TCPC geometry correction has been applied from the expanded data yet
  - future scope: run a dedicated servo-motion tuning session for all axes,
    especially B/C rotary SSI feedback loops; current rotary following-error
    limits are loose commissioning values, not final TCPC quality limits
  - the first expanded-matrix correction candidate was then loaded in the TCPC
    test config:
    `cal-c-to-b.x = -0.065000`,
    `cal-c-to-b.y = +0.014000`,
    `cal-b-to-tool.z = +0.815000`, and
    `c-zero-offset = -0.024500`
  - corrected symmetric validation passed with worst tilted-pose drift
    `0.044784 mm` and closing `B0 C0` drift `0.021471 mm`
  - corrected expanded validation through B `+/-30` passed inside the current
    `0.2 mm` practical target; group max drift was `0.084764 mm` for B0
    C-only, `0.099723 mm` for B `+/-10`, and `0.171569 mm` for B `+/-30`
  - repeated first B `+/-50` attempts stopped on wireless/optical probe faults
    logged as `Probe tripped during non-probe move`
  - after probe/receiver reset and workshop closure, the clean B `+/-50`
    resume block completed from data row `200`
  - clean B `+/-30` group from the fresh B0 baseline: max `0.175977 mm` at
    `B-30 C90`, RMS `0.122098 mm`, closure `0.019881 mm`
  - clean B `+/-50` group from the B30 closure baseline: max `0.427632 mm` at
    `B-50 C90`, RMS `0.266161 mm`, closure `0.014415 mm`
  - overall start-to-final B0 closure was `0.032135 mm`
  - accepted pass-2 rotary following error stayed small: B max about
    `229 microdeg`, C max about `1030 microdeg`
  - B `+/-50` residual is now useful diagnostic data but is outside the
    current `0.2 mm` target; treat remaining high-B error as likely
    machine/head alignment, squareness, or mechanical geometry rather than a
    simple TCPC offset-only problem
  - the active expanded program has been restored to safe defaults:
    `#706 = 1.0`, `#707 = 30.0`, `#708 = 0.0`, `#709 = 10.0`
  - optional B `+/-60` extension is now supported; for a B60-only diagnostic
    set `#707 = 60.0`, `#708 = 1.0`, and `#709 = 60.0` deliberately after
    confirming clearance and probe receiver stability

## Step 5: Mixed-Pose Cross Check

Purpose:

- confirm the geometry fit against mixed `B/C` poses before starting TCPC work

Recommended pose list:

- `B0 C0`
- `B0 C90`
- `B0 C180`
- `B+45 C0`
- `B+45 C180`
- `B-45 C0`
- `B-45 C180`

## Data To Keep

Use the CSV template:

- `configs/5th_axis_xyzbc_ssi_probe_basic/sphere_center_log_template.csv`

Current raw sphere CSV:

- `configs/5th_axis_xyzbc_ssi_probe_basic/sphere-center-results.csv`

Setup note:

- The custom 30 mm sphere wrapper caps `xy_clearance` at `2.0 mm` for this routine only. Probe Basic's normal large mold-work clearance can remain unchanged.

Initial loose-sphere motion test at `B0 C0`:

- relative center `X=-2.007917 Y=-1.207917 Z=104.777029`
- absolute center `X=306.333197 Y=352.762646 Z=-280.900367`
- side diameters `X=29.709767 Y=29.704766`
- top contact `Z=122.642496`
- use this as motion-validation only, not TCPC fit data

Secured `B0 C0` baseline from three repeat runs:

- average absolute center `X=306.368475 Y=352.795840 Z=-280.750222`
- absolute center repeatability range `X=0.001667 Y=0.001667 Z=0.000900`
- average side diameters `X=29.771711 Y=29.674210`
- side-diameter repeatability range `X=0.004999 Y=0.002500`
- use this average as the initial baseline for C/B sweep deltas

Record for every sphere run:

- stage
- pose label
- commanded `B`
- commanded `C`
- solved relative center `X/Y/Z`
- solved absolute center `X/Y/Z`
- solved `X` equator diameter
- solved `Y` equator diameter
- top-contact `Z`
- notes

After the first `B0 C0` baseline is stable, also compute:

- `dX = abs_x - baseline_abs_x`
- `dY = abs_y - baseline_abs_y`
- `dZ = abs_z - baseline_abs_z`

Those deltas are the values you fit against when solving the rotary geometry.

## Immediate Next Engineering Steps

2026-04-30 shutdown handoff:

- The late-night full expanded TCPC run produced useful rows through B `+/-50`
  before repeat wireless probe false trips at B60.
- Use rows `243-306` of
  `tcpc-expanded-pose-vector-2pass-results.csv` as the best pre-shutdown
  full-run data through B `+/-50`.
- Rows `307-314` are incomplete B60 attempts only. The sphere was moved after
  those attempts, so do not use them for final fitting.
- New data after the moved sphere starts at results line `315`.
- The morning program is set for a conservative fresh full B `+/-60` rerun:
  `#704=1.0`, `#706=1.0`, `#707=60.0`, `#708=0.0`, `#709=10.0`.
- The program now lifts +5 mm in Z before rotary index moves via `#515=5.0`.
- First-pass analysis says there is enough data to identify likely mechanical
  contributors, but not enough for a final TCPC fit. A practical TCPC fit only
  improves rows `243-306` RMS from about `0.155 mm` to about `0.142 mm`, so
  the remaining high-B residual is likely mixed geometry/alignment/mechanics,
  not one simple offset.
- Stable B0 closures and small rotary following error argue against random
  drift or B/C servo following error as the primary B `+/-50` source.

1. Get the ring calibration offset stable.
2. Get repeatable `B0 C0` sphere-center data.
3. Collect the `C` sweep.
4. Collect the `B` sweep.
5. Fit geometry from the absolute center deltas.
6. For current mold-cutout work, accept the first TCPC fit if fixed-tip error
   is repeatable under `0.20 mm` across the practical pose set; refine toward
   `0.10 mm` only after backlash/alignment work is characterized.
7. Only after that start the TWP integration pass.
