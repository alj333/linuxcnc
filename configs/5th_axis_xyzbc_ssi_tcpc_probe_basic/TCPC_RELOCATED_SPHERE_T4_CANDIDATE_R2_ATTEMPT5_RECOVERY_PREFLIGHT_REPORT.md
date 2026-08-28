# T4 R2 Attempt-5 Recovery Preflight

Status: `PASS`

- campaign / mode / attempt: `2026082404 / 29 / 5`
- recovery sequences: `1-9 + 72 + 93-101` (`19` rows)
- expected recovery closures: `14`
- program SHA-256: `779f18f20d70ada82bea0f06caf91f5111dfa746ea4ae2a5bab3da55abf0e6b6`
- analyzer SHA-256: `e41ceaf962d2639ecc00872223de0e42d91e294c960c1d4b5552a4146e44a6c0`
- sealed attempt-4 checksum-set SHA-256: `7bcc0bd32c995f9f9805eb77594dbe18421bc979e8d90964be2b66ca9b576ee6`
- recovery INI SHA-256: `66d2b123e2df19eab2a0c1f53875e699c666b32e3a19800ac9427d8eafbabd3b`
- observation-only counter HAL SHA-256: `6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34`

The sealed attempt-4 39-row prefix and terminal no-touch evidence validate exactly.
Attempt-4 provenance is archive-backed; the runner reads no volatile attempt-4 interpreter parameters.
This supersedes the sealed 20260826_0119 preflight before motion after the task-process SIGBUS exit.
All five attempt-5 outputs are exact header-only files. The in-tree RS274 preview parser passed under an isolated temporary HOME.
No LinuxCNC, HAL, MDI, or machine-control command is issued by this analyzer.
