# T4 R2 Attempt-4 Recovery Preflight

Status: `PASS`

- campaign / mode / attempt: `2026082404 / 28 / 4`
- recovery sequences: `1-9 + 67-101` (`44` rows)
- expected recovery closures: `19`
- program SHA-256: `f4dd59e60219e3c0a5d83f3f76fbcb451871a9996d186adae6d2fdd6fd480364`
- analyzer SHA-256: `61c6ed90e6773fbd348ac07a1310ca0b6c729c8678f7e057f89b4634b6e5bb7d`
- sealed attempt-3 checksum-set SHA-256: `d77d728bccc11c36cd97ccbd7ae28fb6832aa5b2695cd3244e527e0b9bde3072`
- recovery INI SHA-256: `66d2b123e2df19eab2a0c1f53875e699c666b32e3a19800ac9427d8eafbabd3b`
- observation-only counter HAL SHA-256: `6ab8cee6f23c5330964edd1cf262d3502f4f3c7b9ae3da7dc2c0945ea2588f34`

The sealed attempt-3 34-row prefix and terminal gap-burst evidence validate exactly.
All five attempt-4 outputs are exact header-only files. The in-tree RS274 preview parser passed.
No LinuxCNC, HAL, MDI, or machine-control command is issued by this analyzer.
