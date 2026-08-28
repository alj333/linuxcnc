# TCPC Length-Aware T4 Attempt 1 Partial Report

Status: `RETIRED - PRESERVE, DO NOT RESUME OR APPEND`

## Identity

- campaign / mode / attempt: `2026082602 / 32 / 1`
- model ID: `2026082601`
- tool: `T4 / H4 / 229.407000 mm`
- runner SHA-256: `0c25bad2be98eae5e927c765fea83d1b877e652635f446ff637dbf8160e308be`

## Acquired Data

- complete result/state/model-state rows: `36 / 36 / 36`
- complete closures: `4`
- contact/gap trace rows: `290 / 290`
- last complete pose: sequence `36`, `B-10 C270`
- interrupted pose: sequence `37`, `B-10 C0`, pass `1`, contact `2`
- stop time: `2026-08-26 23:44:38 +07:00`

Attempt 1 has 288 trace transactions backing its 36 complete poses and two
additional partial sequence-37 transactions. It cannot satisfy the exact
101-row/808-transaction validation contract and must not be appended or
resumed in place.

## Stop Evidence

The terminal contact was a successful G38 touch with direct raw/mux/gated
deltas `2 / 2 / 1`, repeat deltas `0 / 0 / 0`, one filtered extra edge, and a
clean two-sample release. The length model remained valid with fault code `0`.

The 1 kHz edge monitor recorded the valid raw/mux/gated edge at
`23:44:35.045`. The real-time G38 gate and motion type closed at
`23:44:35.055`. A second raw/mux edge occurred at `23:44:35.105` while the
gated count remained unchanged. The duplicate therefore could not alter the
captured G38 point. Attempt 1 stopped because the runner required exactly one
direct raw/mux edge, not because motion received a second probe edge.

## Frozen Output Hashes

| output | SHA-256 |
| --- | --- |
| closures | `ca086e8885b9102ca308ecc320a05a5a3f50471f082a088f44ba4e57e25a7b3c` |
| contact trace | `67896606e44ccdfbb521c349805c4c169bfc1c5d1aa6addf001de5949289e057` |
| gap trace | `ec15fe4aed367087621aa5ff4f2c5d6d2b554a076c470bdc35aaae9ce3b69c95` |
| model state | `d1dd67bb78252055ec0ebe8151601c251904030f1fd41d17beacbcfd8215a044` |
| results | `f5a91b051890ea87edb550aea9f00e02bdb419a7e5bfe5f20f30071d83736ac8` |
| state | `eb54795841b71fa002151946f4d26c8713f0c48cc018ac7302d7aac44738edaf` |

## Next Attempt

Attempt 2 is a fresh full 101-pose acquisition with separate output files. It
accepts at most two matched raw/mux extras only when G38 succeeds, exactly one
gated edge reaches motion, no gated repeat occurs, and the probe passes the
release guard. Counter mismatch, more than two extras, a missing or repeated
gated edge, no-touch, or release failure remains a hard stop.
