# Changes

## 1.1.1 — 2026-11-21

- Accept PNG directly in project.json's icon field, while keeping raw/default icons dependency-free.
- Add tools/convert_icon.py with four-shade conversion, white alpha compositing, aspect-preserving 32x24 fitting and PNG preview.
- Add optional pinned Pillow dependency, 10 icon tests and build-container integration checks.
- Document all 11 native categories and the desktop's visible 32x24 icon area.
- Keep all five device binaries byte-identical to the emulator-validated 1.1.0 baseline.

## 1.1.0 — 2026-11-21

- First public source repository with pinned cc65 source bootstrap and GitHub Actions/Release.
- Rebuilt all five examples from the pinned source toolchain; exact prior emulator-validated binaries retained.
- Added public build instructions, license boundaries and relative runtime screenshots.

- Added native file create/open/write/seek/close/delete and storage example.
- Moved the C stack from NAND scratch RAM to an original heap allocation.
- Matched the native eight-byte metadata-pointer argument and seek origin codes.
- Added interrupt-friendly PSG note sequences and a music example with Esc/Home cancellation.
- Added a PSG PCM model, optional WinMM output, and bundled GPL emulator support sources.
- Verified file persistence through CPU reset/NAND reload and original UART readback.
- Added measured melody capture and 19 I/O checks; retained the 1.0 release archive.

## 1.0.0 — 2026-11-20

First standalone community release for original 7980 V1.10.

- C/65C02 startup, initialized DATA/BSS and clean native return.
- Zero-page ABI bridge for original banked system calls; native IRQs remain active.
- Original event pump, raw/translated input and periodic notifications.
- System 12/16/24-dot font access, GBK text, clipped four-shade graphics.
- Read-only native file lookup, size and ranged reading.
- Original bank checksums, transfer headers, caption and icon.
- Fixed Windows toolchain, prebuilt runtime, new-project tool and three examples.
- Minesweeper migrated from GPIO polling/global IRQ masking to the native event API.
- Native validation, host graphics/rules tests and relocatable release rebuild checks.

Physical device and PCLINK validation are pending; API scope is documented in README.
