# TCPC Relocated-Sphere Campaign 2026082404

Prepared `2026-08-24T21:16:35+07:00`. Released for load-only at
`2026-08-24T23:42:38+07:00` after the operator explicitly accepted T4 physical
clearance for the new negative-B C45/C225 watch sectors.

This measurement campaign inherits the certified-sphere anchor accepted under
campaign `2026082403`, attempt 1. The anchor center remains:

```text
X1024.957789 Y844.074417 Z-302.468115
```

Do not rerun or relabel the anchor. Campaign `2026082403` and its 59-pose T4
plan are immutable provenance and completed with zero primary measurement rows.

## T4 Training Grid

The revised primary contains 101 accepted rows:

```text
1-9     B0:   C0,45,90,135,180,225,270,315,0
10-16   B+5:  C0,45,90,180,225,270,0
17-23   B-5:  C0,45,90,180,225,270,0
24-30   B+10: C0,45,90,180,225,270,0
31-37   B-10: C0,45,90,180,225,270,0
38-44   B+15: C0,45,90,180,225,270,0
45-51   B-15: C0,45,90,180,225,270,0
52-56   B+30: C0,90,180,270,0
57-61   B-30: C0,90,180,270,0
62-66   B+45: C0,90,180,270,0
67-71   B-45: C0,90,180,270,0
72      B0 C0 midpoint
73-77   B+60: C0,90,180,270,0
78-82   B-60: C0,90,180,270,0
83-87   B+90: C0,90,180,270,0
88-92   B-90: C0,90,180,270,0
93-101  B0:   C0,45,90,135,180,225,270,315,0
```

There are 41 positive-B rows, 41 matching negative-B rows, and 19 B0 rows.
Every positive `(abs(B), C)` pose has the negative counterpart with identical
multiplicity. The program and generator reject a mismatched signed grid.

The low-B C45 subset deliberately omits C135 and C315. Those are established
post-collision sectors whenever B is nonzero. C45/C225 have accepted historical
T4 evidence at positive B, but no accepted negative-B oblique evidence. The new
`B-5/-10/-15 C45/C225` paths are therefore a new physical-clearance class.
Configured-limit replay cannot qualify the probe body, holder, cable, sphere,
or post. At `2026-08-24T23:42:38+07:00`, the operator explicitly confirmed
that those poses are clear with no interference issues. That confirmation is
the physical-clearance evidence; it is not an inference from the replay model.

## T3 Holdout

The untouched T3 measurement grid remains 31 poses at B0 and paired
`B+/-45,+/-90`, using C0/90/180/270/0. Only its measurement-campaign metadata
changed to `2026082404` so T4 training and T3 holdout rows share one campaign.
T3 must not be inspected to select the fit family.

## Frozen Identities

```text
T4 primary      bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2
T3 verification ceaf8895626a2b3030fb1d36f5575f7ff5c3850630178303795279e9be483c18
T4 envelope     c0e505fab6851496b3abdb429211ffae694cae3c47a329cbf7edc3ce9933c080
T3 envelope     f21d537ab40d05f23b32be02683549e737f7b2a74c4cfb209dcdf901d2a05358
```

The generated envelopes are offline contract artifacts only. The operator
declined further fast clearance sweeps; neither revised envelope is to be
loaded or run. This does not convert unobserved physical clearance into a pass.

## Offline Release Checks

- T4/T3 configured-limit replay: PASS over 41,063 samples.
- Worst remaining linear margin after allowances: `182.860993 mm`.
- Configured B/C margins: `10.000 / 44.000 deg`.
- T4 rows/closures: `101 / 28`; T3 rows/closures: `31 / 14`.
- Reachability, campaign-analyzer, and generator self-tests: PASS.
- Historical in-tree `bin/rs274 -g` parse of both probing runners: PASS. Those
  pre-isolation previews must not be repeated under a live controller `HOME`;
  see the SIGBUS finding below.
- T4 mode-23 attempt 1 subsequently completed `101/101/28`
  result/state/closure rows and passed its exact validator. T3 mode-24 remains
  header-only and untouched.
- The R2 analyzer self-test and final offline preflight pass. The complete
  reproducible package is sealed under
  `calibration_runs/20260825_0940_campaign04_t4_candidate_r2_attempt1_final_preflight`;
  its `SHA256SUMS` SHA-256 is
  `a7025be38f8e191070bbf301d2715f4787c6ce5bb7bc3df10a93ce61c25a3802`.
- After attempt 1 stopped at closure 911, a separately versioned attempt-2
  analyzer and runner passed active and sealed self-test, parser, reachability,
  correction, attempt-isolation, and full preflight checks. Its package is
  `calibration_runs/20260825_1425_campaign04_t4_candidate_r2_attempt2_final_preflight`;
  `SHA256SUMS` SHA-256
  `dc2c0415d128a3710bb5b0f5ec0b37880908ec35a154450cd6c901941a4f6e27`.
- Attempt 2 stopped under its designed no-touch guard while attempting
  sequence 49 at `B-15/C225`. Its synchronized `48 / 48 / 6` partial and
  passive end state are sealed under
  `calibration_runs/20260825_1654_campaign04_t4_candidate_r2_attempt2_partial_no_touch_seq49`;
  `SHA256SUMS` SHA-256
  `5a8e2562c3ad85601cd701207aba87e061c2eb9ce4e767f6519b314748a07895`.
- CCTV review then confirmed an error state with continual visible T4 pulsing
  around `16:14`. The current `10.0 s` post-G38 mask and transient `0.50 s`
  abnormal-event one-shot did not retain that condition; the next U probe move
  raised only the downstream no-touch error. The attempt is therefore
  probe-fault contaminated. Volatile task/GUI/health evidence is sealed under
  `calibration_runs/20260825_1716_campaign04_attempt2_probe_fault_trace`;
  `SHA256SUMS` SHA-256
  `cf141d46a543dc3558d051633501d6b061b49083641517235eec2179ff81eed8`.

## Completed T4 Result

- Current-calibration centered RMS/max: `0.201016 / 0.711434 mm`.
- Worst row: sequence 91, `B-90 C270`, `0.711434 mm`.
- All 28 closures pass; worst `0.027115 mm`, whole-run `0.023988 mm`.
- All 101 rows remain eligible for T4-only fitting.
- Completed raw acquisition archive:
  `calibration_runs/20260825_0756_campaign04_t4_primary_attempt1_complete`.

Candidate R1 (nine terms, lambda 30) was prepared offline but rejected by the
final statistical audit before any load or motion. Lambda 10 and 3 both
outperformed 30 after its term family was fixed, and the family-selection
uncertainty was not fully nested in the original report. R1 is preserved only
as rejected provenance under
`calibration_runs/20260825_0833_campaign04_t4_candidate_r1_rejected_pre_motion`;
its active overlay and runner are disarmed.

R2 is now frozen as ten terms at lambda 10; its fit and audit are archived
under `calibration_runs/20260825_0909_campaign04_t4_fit_r2_frozen`. Final
offline preflight passed and is sealed in the archive identified above. The
candidate is authorized only for the exact versioned mode-26 T4 same-grid
implementation diagnostics, not production or T3 transfer. The authorized
`B+/-90` correction peak is
`0.671900 mm`; the configured `B+/-100` scan reaches `0.764644 mm` and is an
explicit release blocker.

Mode-26 attempt 1 accepted sequences `1-93`, then stopped by design when
closure 911 measured `0.050380 mm` against the unchanged `0.050000 mm` limit.
The final repeated B0 sequences `94-101` and 11 closures are absent. Attempt 1
is formally incomplete and immutable under
`calibration_runs/20260825_1412_campaign04_t4_candidate_r2_attempt1_partial_closure_stop`.
All 76 unique poses are present, and provisional equal-76 RMS/max improve to
`0.086446 / 0.221643 mm`; this is favorable sensitivity evidence, not a pass.
See `TCPC_RELOCATED_SPHERE_T4_CANDIDATE_R2_ATTEMPT1_PARTIAL_REPORT.md`.

Attempt 2 retained unchanged motion, poses, guards, overlay, closure limit, and
statistical gates. It accepted sequences 1-48 and six closures, all passing
between `0.002647` and `0.015379 mm`. During sequence 49 at `B-15/C225`, the
contact-2 U-side probe move recorded no touch. The routine retracted and
returned top clear before aborting. No sequence-49 row exists. Attempt 2 is a
formal incomplete acquisition and cannot be resumed or reused.

The isolated candidate identities are:

```text
base HAL        b2f4ea3082ff7769f59a6de866c1678a3e8a68d49264689e198d4af3f1e85778
candidate INI   1ab3b84611b93fbf10083e21f87b90d19eea5c3c8a8fe66373570a7cace3d77e
R2 overlay      0bfefdb068bb353282fc41067d5cd7464f76ea6a4f520204f0ab5c914ee1673a
attempt-1 runner a1358c407399ad3606a5a2a449cc973cd39c6ea705233c1f87fdfc0dcb45b7f4
attempt-2 runner 6421c2f8cb8c12a7e4d8ace98f956e4270974482058815609cce9b5f22dbea86
```

## Attempt-3 Recovery

Attempt 2 remains immutable and retired after the sequence-49 probe-fault
stop. It must not be interpreter-resumed, rerun, appended, truncated,
relabelled, or used as a machine-run namespace.

Attempt 3 is a fresh mode-27 recovery acquisition. It is not an interpreter
continuation and cannot become a formal uninterrupted 101-row pass. It acquires
original sequences `1-9` and `45-101`, for `66` accepted rows and `23`
closures. The opening B0 block provides within-acquisition references; the
sequence namespace is then seeded to 44, the complete B-15 block is rerun, and
the exact remaining B+/-30, B+/-45, midpoint B0, B+/-60, B+/-90, and closing
B0 blocks follow. Sequences `10-44` remain omitted. The analyzer may create an
optional diagnostic composite from those immutable attempt-2 rows using a
separate nuisance translation for each acquisition, but the composite is not
acceptance evidence and must never be reported as a same-run pass.

The recovery keeps the attempt-2 motion, feeds, probe vectors, release
sampling, and protected guards. It has one initial pre-motion `M0`, no
intermediate holds, and no 10 or 20 second settle dwell. Persistent,
observation-only counters track the raw T4 receiver, probe mux, and gated
motion input without driving motion, pause, enable, probe, or hardware-output
pins. Per-G38 contact traces and inter-contact-gap traces retain levels and
edge counts. At most two true post-contact repeat edges are accepted; excess
repeats, a gated edge in a gap, raw/mux inconsistency, an invalid successful-
contact gated count, or activity after the initial M0 baseline logs and aborts
through the protected retract path.

The final post-review identities are:

```text
attempt-3 runner 1e1dee457a6b9792585f2afe4abb2f99b09951e20bdfe2f174b863896b77579d
analyzer         0508f819ddb26000194c4c336b6a162212d8ffbdf3439a95b34933baa0cfa15f
preflight report 2730a4b917006d7b8f6f85cfb2222c5816f6cb90b5184c8981dbdfed2f9b4e82
recovery A3 INI  66d2b123e2df19eab2a0c1f53875e699c666b32e3a19800ac9427d8eafbabd3b
counter HAL      6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34
edge monitor     83531e3dcbb26b516a60fe9a89f32aaf0cf85180e5fd33b88ec7b3664b629aea
monitor wrapper  0793ddfed545562ffeffe50dbe91b4a0a74ec45e6d0e16153f344288994db49c
```

The post-review package is sealed at
`calibration_runs/20260825_1743_c04_r2_a3_recovery_preflight`; its
`SHA256SUMS` SHA-256 is
`698f4768e0422cfa8b2b72a6eaa6496f0c8a9410737d3083816e59b6a647ef24`.
Both active-workspace and archived-workspace offline preflights pass. At seal
time the results, state, closures, contact-trace, and gap-trace files were exact
header-only files.

After the operator returned the machine to the standard B0/C0 start, the prior
R2 session's `milltask` terminated with `SIGBUS` at
`2026-08-25T17:34:18+07:00`. The milltask log, health trace, and core were
captured under `diagnostics/task_exit_captures`; this is failure evidence, not
a root-cause determination. A clean recovery-A3 INI launched at
`2026-08-25T17:58:54+07:00`, and the exact frozen runner was loaded at line 0
with zero motion. The operator subsequently completed setup and ran the
recovery. Attempt 3 accepted exact sequences `1-9,45-69` (`34 / 66` rows),
five passing closures, 273 contact traces, and 274 gap traces. Worst closure
was `0.020390 mm`; standalone centered RMS / maximum residual was
`0.076430 / 0.141219 mm`.

At sequence 70 (`B-45/C270`), contact 1 completed and retracted. The runner was
stationary at the clear contact-2 U-side start before G38 when two additional
raw/mux edges combined with the prior permitted repeat to make a terminal
extra-edge count of three. It persisted the terminal gap and auto-aborted with
`Electrical retrigger burst exceeded two repeats across inter-contact gap`.
The in-position endpoint was approximately
`X1025.285920 Y828.615696 Z-286.989540 B-45 C270`, with inputs clear. No
sequence-70 result/state row exists.

Attempt 3 is an immutable valid partial, not a formal same-acquisition pass. It
must not be interpreter-resumed, rerun, appended, truncated, imputed, or
relabelled. The partial is sealed at
`calibration_runs/20260825_2249_campaign04_t4_candidate_r2_attempt3_partial_gap_burst_seq70`;
its `SHA256SUMS` SHA-256 is
`d77d728bccc11c36cd97ccbd7ae28fb6832aa5b2695cd3244e527e0b9bde3072`.

## Attempt-4 Recovery

After the operator returned to the exact standard B0/C0 sphere-top start, the
recovery-A3 `milltask` PID `459090` terminated with `SIGBUS` at
`2026-08-25T23:04:57+07:00`. The retired attempt-3 runner was still selected
and attempt 4 had not been opened in that controller session. The core is
preserved under `diagnostics/task_exit_captures` with SHA-256
`bab1380c1e5fb8c86705ce25562be17b9a1671f3126aa31302ab1b5526d99f61`.
This records the failure symptom only and makes no causal claim about program
preparation or file selection.

A clean recovery-A3 controller launched at `23:09:13`; new `milltask` PID
`471211` started at `23:09:14`, selected only `blank.ngc`, and exposed fresh
raw/mux/gated edge counters at `0/0/0`. Homing, T4/H4 and TCPC restoration,
probe reset/qualification, and the return to the standard start remain operator
actions.

Attempt 4 is a fresh mode-28 acquisition, not an interpreter continuation. It
owns original sequences `1-9` and `67-101`, for `44` rows and `19` closures.
The exact order is opening B0, complete B-45, midpoint B0, B+60, B-60, B+90,
B-90, and closing B0. The opening block aligns the two earlier immutable
partials for an analyzer-only diagnostic composite:

```text
attempt 2 owns 10-44  (35 rows, 5 closures)
attempt 3 owns 45-66  (22 rows, 4 closures)
attempt 4 owns 1-9 and 67-101 (44 rows, 19 closures)
```

This explicit ownership covers sequences 1-101 and all 28 canonical closures
without averaging duplicates or creating cross-acquisition closures. Separate
attempt-2 and attempt-3 translation nuisance terms align their nine-row opening
B0 means to attempt 4. The resulting composite remains diagnostic: it is not a
formal uninterrupted pass, chronological drift history, production release,
or T3-transfer result.

The attempt-4 runner retains attempt 3's motion, feeds, probe vectors,
retractions, release sampling, and protected raw/mux/gated counter guards. It
has one initial pre-motion `M0`, no intermediate holds, and fresh header-only
outputs. Final identities are:

```text
attempt-4 runner f4dd59e60219e3c0a5d83f3f76fbcb451871a9996d186adae6d2fdd6fd480364
analyzer         61c6ed90e6773fbd348ac07a1310ca0b6c729c8678f7e057f89b4634b6e5bb7d
preflight report 29d74db8a52efab260f63808e199dab3a2b076e5edd79267db2f46cc8b264b26
```

The immutable package is
`calibration_runs/20260825_2312_c04_r2_a4_recovery_preflight`; its
`SHA256SUMS` SHA-256 is
`0459c30465ee93d23d7d1d28fc2dfb722c8de0bd73e82c068a02489bcaa9c3f7`.
Active and archived analyzer self-tests and preflights pass. The sealed
attempt-2 and attempt-3 dependencies validate exactly, the explicit composite
owns all 101 sequences and all 28 canonical closures, active/archive identity
passes, and all 96 archive checksum entries pass.

Attempt 4 subsequently accepted exact sequences `1-9,67-96`: `39 / 44`
result/state rows, 12 passing closures, 318 contact traces, and 318 gap traces.
At sequence 97 (`B0/C180`), acquisition 1 pass 2 contact 2 traversed the full
`6.000 mm` probe vector without a gated touch after six successful contacts.
The runner retracted and failed closed; no sequence-97 result/state row was
written. The partial is immutable and sealed at
`calibration_runs/20260826_0100_campaign04_t4_candidate_r2_attempt4_partial_no_touch_seq97`;
its `SHA256SUMS` SHA-256 is
`7bcc0bd32c995f9f9805eb77594dbe18421bc979e8d90964be2b66ca9b576ee6`.

## Attempt-5 Restart-Safe Recovery

After attempt 4 was sealed, milltask PID `471211` terminated with SIGBUS at
`2026-08-26T01:12:58+07:00`. Passive core and source analysis establishes the
cause: this tree's standalone `bin/rs274` calls `tool_mmap_creator()` before
parsing `-g` or `-T`, opening `$HOME/.tool.mmap` with `O_TRUNC`. Live milltask
maps the same file and faulted in `tool_mmap_mutex_get()` at mapping offset
zero. The same command-to-core signature repeats across PIDs `426717`,
`459090`, and `471211`. Exact source references and evidence are in
`diagnostics/SIGBUS_RS274_TOOL_MMAP_CAUSE_20260826.md`.

The PID `471211` exit erased the volatile interpreter state required by the
first attempt-5 draft. Its sealed, never-run `20260826_0119` package is
superseded and must not be loaded. The replacement runner is restart-safe: it
does not read attempt-4 numbered parameters and validates attempt-4 provenance
from the sealed archive instead.

Attempt 5 is a fresh mode-29/attempt-5 acquisition of the complete 19-row B0
set: sequences `1-9`, midpoint `72`, and closing `93-101`. It creates 14
closures wholly within attempt 5, has one initial pre-motion `M0`, no
intermediate holds, and retains attempt 4's protected motion and probe logic.
Exact diagnostic composite ownership is:

```text
attempt 2  sequences 10-44           35 rows   5 closures
attempt 3  sequences 45-66           22 rows   4 closures
attempt 4  sequences 67-71,73-92     25 rows   5 closures
attempt 5  sequences 1-9,72,93-101   19 rows  14 closures
total      sequences 1-101          101 rows  28 closures
```

Every closure is source-local. The composite is diagnostic, not a single
chronological pass.

```text
attempt-5 runner 779f18f20d70ada82bea0f06caf91f5111dfa746ea4ae2a5bab3da55abf0e6b6
analyzer         e41ceaf962d2639ecc00872223de0e42d91e294c960c1d4b5552a4146e44a6c0
preflight report 2f346bf4271d19aff3f9c4aae5a74f68ac427026934921e13fe288336a4496b2
```

The restart-safe package is sealed at
`calibration_runs/20260826_0133_c04_r2_a5_restart_safe_preflight`; its
`SHA256SUMS` SHA-256 is
`fa72869d8f85ca6ee7affdb1e299238d618fe79c59dc394838f807ca31ea4563`.
All 130 checksums, active/archive self-tests, preflights, sealed attempt-4
validation, and independent static runner review pass. Every RS274 subprocess
now receives a private temporary `HOME`; the live `.tool.mmap` content hash
remained unchanged across validation.

Attempt 5 subsequently completed all 19 assigned B0 rows at
`2026-08-26T02:41:32+07:00`. It produced 19 result rows, 19 state rows, 14
passing source-local closures, 152 successful contact traces, and 152 clean
inter-contact gap traces. Eight isolated post-contact raw/mux repeat edges
were recorded and all eight were suppressed from the gated probe input. The
worst closure is `0.019998 mm`; every structured trace and state fault flag is
zero. The immutable raw acquisition is sealed at
`calibration_runs/20260826_0244_campaign04_t4_candidate_r2_attempt5_complete_raw`;
its `SHA256SUMS` SHA-256 is
`2fbbc4021d51ef7afd5fbdddcf21a1171762f2b0baec915f7c63843ff775a90d`.
This completes the source ownership needed for the diagnostic four-source
composite, but is not a formal uninterrupted 101-row acceptance pass.

After the operator cleanly closed LinuxCNC, the exact copied-workspace
Attempt-5 analyzer exited `0` with `RECOVERY CONTRACT PASS`. The sealed
analysis archive is
`calibration_runs/20260826_0902_campaign04_t4_candidate_r2_attempt5_complete_analysis`;
its `SHA256SUMS` SHA-256 is
`3b155b67b718509d3228c1c2517ccfd7a4ca4a4d12ba98b9105d311c27de966c`.
The diagnostic composite measured equal-76 RMS/max
`0.089045 / 0.190827 mm`, raw-101 RMS/max `0.090001 / 0.194441 mm`, and
actual-versus-predicted pattern RMS/max `0.030038 / 0.068496 mm`.

The recovery-contract pass does not enforce the frozen R2 statistical gates.
An independent reconstruction passes 11 of 12 diagnostic gate calculations.
The maximum unique-pose worsening gate fails at `B+90 C180`:
`0.090202 mm > 0.075000 mm`. All whole-grid values remain diagnostic because
the four acquisitions require three nuisance translations. R2 therefore
remains unaccepted and the formal predeclared T3 verification is not
authorized. A separately declared exploratory T3 holdout may still be
collected under the baseline configuration, but cannot authorize R2, cure the
failed gate, support a production change, or relabel this as a formal T4 pass.

## Operator Order

1. Operator clearance for `B-5/-10/-15 C45/C225`: accepted at
   `2026-08-24T23:42:38+07:00`.
2. Frozen T4 primary runner loaded at `2026-08-24T23:44:07+07:00` at the
   established B0/C0 top start. Load-only verification found line 0, zero
   commanded/actual XYZBC change, and unchanged task PID/start time. Loading
   does not authorize motion.
3. Completed primary-run step: Cycle Start advanced only to the single initial
   pre-motion `M0`.
4. Completed primary-run check: T4/H4 `229.407000 mm`, TCPC active, TWP clear,
   spindle off, probe clear, post direction `X-,Y+,Z-`, and the low-B
   watch-sector decision were rechecked.
5. Completed primary-run step: operator Resume started the 101-pose probing
   run, which had no programmed intermediate holds.
6. Completed: validate and archive the 101-pose T4 attempt.
7. Completed: freeze and audit R2, seal the guarded mode-26 attempt-1 package,
   launch the isolated candidate INI, and run attempt 1.
8. Attempt 1 disposition: immutable `93 / 93 / 17` partial. Closure 911 failed
   by `0.000380 mm`; do not restart, resume, append, truncate, or relabel it.
9. Completed: seal attempt 1, evaluate its explicitly provisional metrics, and
   prepare a fresh attempt-2 package with unchanged gates and motion.
10. Completed load-only transition: after fresh live preflight and explicit
    operator clearance, the exact attempt-2 runner was loaded at line 0. The
    candidate INI remains live, homed, idle, with T4/H4 and TCPC/R2 active at
    B0/C0 top clear. Load caused zero XYZBC change and no output row.
11. Attempt 2 disposition: immutable `48 / 48 / 6` partial. The sequence-49
    `B-15/C225` contact-2 probe move recorded no touch; do not restart, resume,
    append, truncate, or relabel it.
12. Completed fault classification: CCTV confirms continual T4 pulsing during
    the failure interval. Treat the no-touch as probe electrical/receiver
    contamination, not a pose-specific reach result.
13. Completed offline: freeze and independently preflight the fresh mode-27
    attempt-3 recovery, including persistent pulse counters and exact contact
    and gap traces. The post-review package and identities above are the only
    attempt-3 authority; attempt 2 remains retired.
14. Recorded transition: after the operator returned to the B0/C0 start, the
    prior R2 `milltask` terminated with `SIGBUS` at `17:34:18`. Core and health
    evidence were captured. That session is retired; the later repeated-event
    forensic finding identifies standalone RS274 tool-mmap truncation as the
    cause.
15. Completed load-only transition: clean recovery A3 launched at `17:58:54`,
    and the exact frozen runner loaded at line 0 with zero motion. Operator
    setup and the initial M0 checks then completed before Resume.
16. Attempt 3 disposition: immutable valid partial with `34 / 66` rows at
    sequences `1-9,45-69` and five passing closures. Sequence 70 auto-aborted
    at the clear contact-2 U-side start before G38 after the structured
    inter-contact extra-edge count reached three.
17. Completed: validate and seal the five exact outputs, partial report,
    counter evidence, and bounded task logs. Do not resume, rerun, append,
    truncate, impute, or relabel attempt 3.
18. Under the overlay, permit only operator startup/homing/state establishment,
    the sole setup move to the exact B0/C0 sphere-top start, and the exact
    runner. No other manual, MDI, jog, exploratory, or full-range motion is
    permitted. Do not bypass a guard.
19. Immediately after the final T4 disposition, clean-close the candidate and
    restart the baseline task-capture INI. Verify the base HAL hash above and
    overlay absence before any T3 run.
20. Recorded transition: after the operator returned to the exact B0/C0 start,
    recovery-A3 `milltask` PID `459090` terminated with `SIGBUS` at `23:04:57`.
    Attempt 4 had not been opened. Preserve the core and do not reuse that
    controller session; the later repeated-event forensic finding identifies
    standalone RS274 tool-mmap truncation as the cause.
21. Completed offline: clean recovery-A3 controller launched at `23:09:13`,
    Home All completed, and the exact attempt-4 package above was sealed and
    independently verified. Only `blank.ngc` remains selected until final live
    setup passes.
22. Before load, require all five axes homed; T4/H4 `229.407000 mm`; TCPC
    active and TWP clear; spindle and probe inputs clear; B0/C0; the operator-
    confirmed 3-5 mm sphere-top start; and two deliberate hand deflections
    producing matched raw/mux edges with no gated edge. Any extra or unmatched
    edge bars the run. Attempt 4 has one explicitly recorded exception: the
    operator is remote and cannot make a physical deflection. Stable `0/0/0`
    counts and clear levels permit load and guarded execution, but do not prove
    receiver function; the first G38 no-touch path must fail closed if the
    receiver is inactive.
23. Load only the exact mode-28 attempt-4 runner above. Verify line 0, idle/in-
    position state, unchanged XYZBC, unchanged task PID, exact fresh header-
    only outputs, and no controller error. Loading authorizes no motion.
    Completed at `23:35:10`: every listed load-only check passed with task PID
    `471211`, exact zero commanded/actual XYZBC delta, `0/0/0` counters, and no
    output row.
24. Operator Cycle Start may advance only to the single initial pre-motion
    `M0`. Recheck the live setup, clear inputs, counters, file identity, and
    zero output rows there. Only the operator may Resume the uninterrupted
    probing body. Completed at `23:36:38`: the M0 boundary passed every listed
    check with unchanged task PID and start position. The operator then
    resumed the uninterrupted probing body.
25. Attempt 4 disposition: immutable valid partial with 39 accepted rows at
    sequences `1-9,67-96`, 12 passing closures, and a structured no-touch at
    sequence 97 pass 2 contact 2. Do not resume, append, truncate, impute, or
    relabel it.
26. Completed offline: seal attempt 4, establish the repeated RS274/tool-mmap
    SIGBUS cause, and supersede the first attempt-5 draft after PID `471211`
    exited. Never run repository `bin/rs274` under the controller's `HOME`.
27. Completed offline: seal and independently validate the restart-safe
    attempt-5 package identified above. At that pre-run checkpoint its five
    live outputs were exact header-only files. The analyzer isolates every
    RS274 preview with a private temporary `HOME`.
28. Completed: the exact recovery-A3 INI launched at
    `2026-08-26T01:48:37+07:00`; the operator homed all five axes, restored
    T4/H4 `229.407000 mm` and TCPC, and established the confirmed B0/C0
    sphere-top start. Overlay/candidate pins, WCS, TWP-off state, spindle,
    SSI, limits, probe levels, and fresh edge counters passed.
29. Completed after explicit operator clearance: load only the exact mode-29
    runner with SHA-256
    `779f18f20d70ada82bea0f06caf91f5111dfa746ea4ae2a5bab3da55abf0e6b6`.
    Verify line 0, idle/in-position state, zero XYZBC load delta, unchanged task
    identity, no error, and five exact header-only outputs. Loading authorizes
    no motion. All listed load-only checks passed.
30. Completed under operator control: Cycle Start advanced to the initial M0,
    the post-hold state passed, and Resume ran the uninterrupted 19-row B0
    acquisition. It completed normally with `19 / 19 / 14 / 152 / 152`
    result/state/closure/contact/gap rows and returned idle at B0/C0 above the
    sphere.
31. Completed read-only: three structured audits passed and the exact raw
    acquisition was sealed at the archive and checksum identity above. No
    live output, controller configuration, geometry, zero, or tool-table value
    was changed.
32. Completed: the operator cleanly closed LinuxCNC. The exact copied-workspace
    Attempt-5 analyzer exited `0`; the composite report, command, environment,
    stdout, parent provenance, and all inputs are sealed in the analysis
    archive above. Never run standalone repository `bin/rs274` under a live
    controller `HOME`.
33. Current disposition: R2 is not accepted because the diagnostic per-pose
    worsening gate fails at `B+90 C180`, and the translated four-source
    composite cannot be a formal uninterrupted pass. Do not refit R2 from this
    validation data. This does not authorize the formal predeclared T3
    verification stage. If the operator elects to continue tool-length
    diagnosis, the next permitted acquisition is a separately declared
    exploratory short-T3 holdout under a clean baseline task-capture restart.
    Verify the frozen base-HAL hash and R2-overlay absence, then use a frozen
    scoring method and a reviewed shorter runner before any operator setup or
    motion. T3 cannot cure the failed T4 gate.

The operator owns Cycle Start, Resume, Feed Hold, Abort, recovery, and every
clearance decision. No production/base INI or HAL, rigid geometry, B/C zero,
tool table, or kinematic setting changed; R2 exists only in the separate
candidate INI and overlay.

## Separate T3 Transfer Exploration

The next diagnostic is deliberately outside formal campaign-04 acceptance. It
uses separate identity `2026082601/30/1` and baseline correction only. R2 is
not loaded and remains unaccepted. The frozen package is documented in
`TCPC_RELOCATED_SPHERE_T3_R2_TRANSFER_EXPLORATORY_PLAN.md`; its offline
preflight report records a pass for the exact 31-pose T3 runner, the
baseline-plus-counter INI, five fresh outputs, isolated-HOME parser, and
configured-limit replay.

The new run retains B+/-45 and B+/-90 C-quadrant pairs so tool-length transfer
can be checked over 20 equal-weight unique poses after only one global
translation. It is not a T3 coefficient fit. Even a supportive result cannot
cure the failed T4 B+90/C180 gate, relabel the translated T4 composite as a
formal pass, accept R2, or authorize production changes.

At `2026-08-26T10:04:30+07:00` the baseline-plus-counter diagnostic INI was
launched and the exact mode-30 runner was loaded at line 0. Load-only checks
passed with zero motion, machine disabled/unhomed, T0 and zero TLO, clear
probe levels, `0/0/0` counters, untouched output headers, and no controller
error. No program was started; operator setup and motion authority remain
outstanding.
