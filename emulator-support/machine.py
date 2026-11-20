"""ctypes interface to the 65C02/ST2xxx board model."""
from pathlib import Path
import ctypes as C
import sys
import zlib

ROOT = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else ROOT


class Machine:
    def __init__(self, firmware=None):
        self.lib = C.CDLL(str(ROOT / "bbk7980.dll"))
        for name in ("bbk_run", "bbk_clocks", "bbk_instructions", "bbk_irqs", "bbk_iocount"):
            getattr(self.lib, name).restype = C.c_uint64
        self.lib.bbk_read.restype = self.lib.bbk_phys_read.restype = C.c_uint8
        self.lib.bbk_load.argtypes = [C.POINTER(C.c_uint8), C.c_uint32]
        self.lib.bbk_lcd.argtypes = [C.POINTER(C.c_uint8)]
        for name in ('bbk_nand_export',):
            getattr(self.lib,name).argtypes = [C.POINTER(C.c_uint8)]
        for name in ('bbk_nand_import','bbk_uart_send','bbk_uart_receive'):
            getattr(self.lib,name).argtypes = [C.POINTER(C.c_uint8),C.c_uint32]
        if hasattr(self.lib,'bbk_audio_read'):
            self.lib.bbk_audio_read.argtypes=[C.POINTER(C.c_int16),C.c_uint32]
        self.load(Path(firmware) if firmware else ROOT / "runtime/syscode.bin")

    def load(self, path):
        data = path.read_bytes()
        buf = (C.c_uint8 * len(data)).from_buffer_copy(data)
        if self.lib.bbk_load(buf, len(data)) != 0:
            raise ValueError("System image must be exactly 524288 bytes")
        self.lib.bbk_reset()

    def run(self, cycles):
        if not 0 <= cycles <= 0xffffffff:
            raise ValueError('Cycle budget must fit an unsigned 32-bit value')
        return self.lib.bbk_run(cycles)

    def state(self):
        d = dict(zip(("pc", "a", "x", "y", "sp", "p"),
                     (self.lib.bbk_reg(i) for i in range(6))))
        d.update(cycles=self.lib.bbk_clocks(), instructions=self.lib.bbk_instructions(),
                 interrupts=self.lib.bbk_irqs(), flags=self.lib.bbk_flags())
        return d

    def frame(self):
        pixels = (C.c_uint8 * (240 * 120))()
        self.lib.bbk_lcd(pixels)
        return bytes(pixels)

    def audio(self):
        if not hasattr(self.lib,'bbk_audio_read'):return b''
        samples=(C.c_int16*262144)();count=self.lib.bbk_audio_read(samples,len(samples))
        return bytes(samples)[:count*2]

    def save_nand(self, path):
        size = self.lib.bbk_nand_size()
        data = (C.c_uint8 * size)()
        self.lib.bbk_nand_export(data)
        path = Path(path)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(bytes(data))
        temporary.replace(path)

    def load_nand(self, path):
        data = Path(path).read_bytes()
        if str(path).endswith('.z'):data=zlib.decompress(data)
        buf = (C.c_uint8 * len(data)).from_buffer_copy(data)
        if self.lib.bbk_nand_import(buf, len(data)):
            raise ValueError("Invalid NAND size; expected 64 MiB plus 16-byte spare per page")


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=4_000_000)
    args = parser.parse_args()
    m = Machine()
    m.run(args.cycles)
    print(json.dumps(m.state(), indent=2))
    print("IO", {f"{a:02x}": [m.lib.bbk_read(a), m.lib.bbk_iocount(a, 0), m.lib.bbk_iocount(a, 1)]
                 for a in range(128) if m.lib.bbk_iocount(a, 0) or m.lib.bbk_iocount(a, 1)})
    print("history", [f"{m.lib.bbk_history(i):04x}" for i in range(20)])
