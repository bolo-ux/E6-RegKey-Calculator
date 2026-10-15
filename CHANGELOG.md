# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

### Added

- E013/E014 registration key computation from machine code or 96-bit UID input
- Interactive, CLI (`--mc` / `--uid`), batch (`--file`) and self-test (`--selftest`) modes
- Automatic UID word-order detection (wafer-coordinate heuristic), tolerant input parsing
- Optional real-firmware emulation cross-check via `--firmware` (Unicorn)
- Bilingual full disclaimer (`DISCLAIMER.md`), MIT `LICENSE`, structured `README.md`
- Reverse-engineering methodology write-up (`docs/methodology.md`)
- Example batch input file (`examples/devices.txt`)

### Notes

- Core tool: zero third-party dependencies (Python 3.6+ standard library only)
- Algorithm verified by dual channel (instruction-level emulation + pure formula)
  on two known devices; full regression available via `--selftest`

[1.0.0]: https://github.com/<your-name>/E6-RegKey-Calculator/releases/tag/v1.0.0
