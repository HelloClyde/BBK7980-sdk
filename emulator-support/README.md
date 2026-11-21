# Optional PSG emulator support (GPLv3)

This folder supplies the board, CPU and desktop UI used by the SDK demo runner.
It includes corresponding source and the GPL license. The Windows Release ZIP
also includes the DLL built from this source; Git tracks no DLL.
From the repository root, `python emulator-support/build.py` builds the DLL with
GCC on PATH. The CPU provenance is retained in
`vendor/s6502.c`; the board and UI are from the workspace BBK7980 emulator.

The board model uses 128 KiB of external SRAM, based on the V1.10 firmware's
program banks and concurrent heap allocations.

No original system ROM, full NAND or font files are present. The SDK runner takes
those inputs from the existing emulator selected with `--emulator`, copies the
system image into its own `build/emulator-board/` directory, and installs examples
through the original guest UART service. It does not replace existing emulator files.

The PSG model implements two square-wave tone channels and volume. Noise,
DAC voice decoding and physical analog/speaker characteristics are not modeled.
PCM is exposed at 22050 Hz; the Windows UI streams those samples through WinMM.
