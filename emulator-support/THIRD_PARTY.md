# Third-party code and data

`vendor/s6502.c` is derived from the CPU implementation in
[HelloClyde / BBK9288-gam4980](https://github.com/HelloClyde/BBK9288-gam4980).
That project's documented upstreams are
[无云 / BBK-simulator](https://gitee.com/BA4988/BBK-simulator/tree/BA4988/BA4988) and
[iyzsong / gam4980](https://codeberg.org/iyzsong/gam4980).
It is used under GPLv3; see COPYING. Changes add ST2xxx RTI, WAI and STP hooks
and replace the platform header with stdint.h. GAM4980 HLE/AOT hooks are disabled.
The corresponding interpreter, board, UI, keyboard, audio and UART source is
included here. This folder is GPL-3.0-or-later; it is optional and separate from
the MIT SDK runtime. Its DLL is built from these sources for the Windows ZIP.

The independently written board model was checked against register and banking
behavior documented by MAME's BSD-3-Clause source:
[st2204.cpp](https://github.com/mamedev/mame/blob/master/src/devices/cpu/m6502/st2204.cpp),
[st2xxx.cpp](https://github.com/mamedev/mame/blob/master/src/devices/cpu/m6502/st2xxx.cpp).
No MAME CPU implementation is linked into this project.

This source folder and the SDK Release include no original system ROM, full
NAND, system font, voice data, 8.BIN/E.BIN or stock application dumps.
The user supplies runtime assets from an existing emulator; their original
rights remain separate and are not licensed under this folder's GPL.

Pillow and Python/Tk are optional external UI dependencies and are not bundled.
