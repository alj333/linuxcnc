# Milltask SIGBUS Cause - Standalone RS274 Tool-Mmap Truncation

Date: `2026-08-26` (Asia/Bangkok, UTC+07:00)

Status: causal link established to a strong engineering and forensic standard.
This analysis was passive. It issued no LinuxCNC, HAL, MDI, program-load, or
machine-control command.

## Finding

Running this tree's standalone `bin/rs274` while LinuxCNC is active truncates
the live controller's `/home/cnc5/.tool.mmap`. The next milltask access to the
mapped tool-data mutex can receive `SIGBUS` / `BUS_ADRERR`.

This applies before command-line parsing, so both `rs274 -g` and `rs274 -T`
are unsafe under the live controller's `HOME`. Analyzer `--self-test` and
`--preflight` modes were affected because they invoked `bin/rs274 -g`.

## Repeated Timeline

All times below are local UTC+07:00.

| Acquisition | Analyzer command window | Milltask exit/core | Delta from start |
| --- | --- | --- | --- |
| attempt 3 | 17:34:17.892-17:34:18.821 | PID 426717 SIGBUS at 17:34:18.394 | 0.502 s |
| attempt 4 | 23:04:56.910-23:04:57.567 | PID 459090 core at 23:04:57.498 | 0.588 s |
| attempt 5 | 01:12:57.580-01:12:58.241 | PID 471211 core at 01:12:58.176 | 0.596 s |

The command windows come from the Codex JSONL execution records. Each analyzer
self-test calls `run_rs274_preview()`, which launches the repository
`bin/rs274 -g`.

The separate seeded `rs274 -T` test completed at 01:12:52.692 and was another
unsafe exposure. The immediate attempt-5 trigger was the analyzer's internal
`rs274 -g` invocation in the 01:12:57.580-01:12:58.241 command window.

## Core Signature

The two usable ELF cores are instruction-identical after ASLR normalization:

```text
PID 459090: RIP libtooldata.so.0 + 0x246d
PID 471211: RIP libtooldata.so.0 + 0x246d
symbol:     tool_mmap_mutex_get()
source:     src/rtapi/rtapi_bitops.h:48
            src/rtapi/rtapi_mutex.h:60
            src/emc/tooldata/tooldata_mmap.cc:89
instruction: lock btsq $0x0,0x0(%rbp)
signal:      SIGBUS (7), si_code=2 BUS_ADRERR
si_addr:     exact first byte of the /home/cnc5/.tool.mmap mapping
```

Core identities:

```text
PID 426717  9d0a6361ff42277a44e74c7d57338c0d0c34f537952818fc9e22d6f0b7a8a9b6
PID 459090  bab1380c1e5fb8c86705ce25562be17b9a1671f3126aa31302ab1b5526d99f61
PID 471211  1132dd1fbf2856dff59e4ef5e3dd0755a53df97dfcfb4869dfa3fde1ce57ac49
```

The PID 426717 core file has no usable ELF notes, but its capture wrapper
records wait status 135 / signal 7 at the matching analyzer command time.

## Source Mechanism

`src/emc/sai/driver.cc` calls `tool_mmap_creator()` unconditionally before
`getopt()` processes `-g` or `-T`:

```text
src/emc/sai/driver.cc:566-570  unconditional tool_mmap_creator(...)
src/emc/sai/driver.cc:577-592  later command-line option parsing
```

The exact file lifecycle is in `src/emc/tooldata/tooldata_mmap.cc`:

```text
lines 31-34    .tool.mmap and creator O_RDWR | O_CREAT | O_TRUNC flags
lines 74-79    path construction from secure_getenv("HOME")
lines 82-89    mutex acquisition at mapping offset zero
lines 125-151  creator open, truncate, resize, and MAP_SHARED mapping
lines 167-190  user open and MAP_SHARED mapping
```

Live milltask calls `tool_mmap_user()` at
`src/emc/task/emctaskmain.cc:3342`. The standalone creator's `O_TRUNC` creates
a zero-length race window before lines 140-149 resize the file. A concurrent
milltask access beyond the temporary end of that existing file-backed mapping
raises `BUS_ADRERR`. Both usable cores show exactly that access at mapping
offset zero. The implicated built `lib/libtooldata.so.0` SHA-256 is
`fc8ec5b68497dd24f40c7a672dadd9d5d605f54bdce3234eb2ab9fe45a7be2c0`.

No system-call trace was active to record the individual `open(O_TRUNC)`, but
the exact source mechanism, exact mapped fault address, identical core
signature, and three independent sub-second temporal repetitions establish
causation beyond reasonable engineering doubt.

## Required Controls

1. Never invoke repository `bin/rs274` under the live controller's `HOME`.
2. Analyzer preview must use a private temporary `HOME`, or be omitted while a
   controller is active.
3. Do not use `-T` for offline preview against a live HAL session.
4. Treat pre-hardening attempt-3/4/5 analyzer self-tests and preflights as
   controller-affecting, despite their former offline-only labels.
5. After any milltask restart, do not depend on volatile numbered interpreter
   parameters from the prior process.

## Implemented Containment

The restart-safe attempt-5 analyzer now wraps every standalone RS274 preview
in `tempfile.TemporaryDirectory()` and supplies that directory as the child
process `HOME`. Active and archive-local self-tests and preflights pass with
that isolation, and the live controller `.tool.mmap` content hash remained
unchanged across the validation. The attempt-5 runner also removed all
dependencies on volatile attempt-4 numbered parameters.

Older attempt-3 and attempt-4 analyzers retain their historical behavior and
must not be run while a controller uses the same `HOME` unless they receive the
same isolation fix. This containment prevents recurrence in the immediate
recovery workflow; it is not a source-level fix for standalone `rs274` itself.
