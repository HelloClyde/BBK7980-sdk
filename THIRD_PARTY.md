# Licenses and provenance

- SDK core, API, bridge, build tools and hello/diagnostics/storage/music examples: newly authored,
  MIT (`LICENSE`). No original firmware implementation is copied into the library.
- Minesweeper rules and example: GPL-3.0-or-later (`examples/minesweeper/COPYING`).
  The tile art and icon were authored for this example. SDK core remains MIT.
- cc65 compiler and runtime: V2.19, Git eebf54a. Built from immutable commit
  `eebf54af545f4ae52f8489a2f6d4d5f93e7942d2` by `tools/install_toolchain.py`.
  Original license is retained in `third_party/CC65-LICENSE.txt` and, in the
  Windows bundle, `toolchain/cc65/LICENSE.txt`. No modifications to cc65 source.
  Source: https://github.com/cc65/cc65/tree/eebf54af545f4ae52f8489a2f6d4d5f93e7942d2
  Pinned source archive SHA256:
  `6a7880ce125fde77cfa523aedf629c174040bc0827c40cbd20994f6f5d17c32b`.
  The earlier local SDK used the official Windows snapshot at the same commit;
  the public source build must reproduce its five validated application files.
- Firmware ABI reference: original BBK 7980 V1.10 system and games from
  https://down.eebbk.net/xzzx/7980/1/7980sj.exe . Original rights retained.
  SDK archive contains no BBK ROM, full NAND image, font bitmaps or PCLINK.
- Chinese example text uses runtime glyphs from the device's existing font file.
  No font bitmaps are linked into these SDK example programs.
- `py65`, `pefile` and GCC are optional research/validation dependencies;
  they are not included in the SDK ZIP or required for an ordinary application build.
  Pillow is optional for PNG icons, previews and emulator/host validation.
- `emulator-support/`: GPL-3.0-or-later CPU/board/UI support copied from this
  workspace's BBK7980 emulator, including its full corresponding C/Python source
  and `COPYING`. The Git repository builds its DLL from source; the Release
  ZIP includes that DLL alongside the source. CPU provenance is retained in `vendor/s6502.c`.
  No ROM, NAND, font or voice data is distributed with this support folder.
- PSG register interpretation is cross-checked against original firmware writes
  and the Sitronix ST2202 v2.4 section 14 / ST2204B v1.1 section 10 manuals,
  linked in `docs/ABI.md`. Those PDF documents are not bundled.
- Validation screenshots show SDK examples and small runtime-rendered glyphs.
  The test font is a compatibility input, not verified original 7980 glyphs;
  original font rights remain separate. No standalone font is distributed.
  `validation/music-preview.wav` records the newly authored example's PSG notes.
- Optional PNG icon conversion/preview uses Pillow 12.3.0 under the MIT-CMU license.
  Install it separately with `requirements-images.txt`; no Pillow binaries or
  source are bundled in the SDK. Source/license: https://github.com/python-pillow/Pillow
  The grayscale `examples/minesweeper/icon.png` is exported from the example's
  existing, newly authored icon; it contains no system font or firmware assets.
