"""Exercise clipping and packing in the actual public C drawing implementation."""
from pathlib import Path
import ctypes as C
import os
import shutil
import subprocess
import unittest
SDK=Path(__file__).resolve().parents[1]

class Graphics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out=SDK/'build/host-tests';out.mkdir(parents=True,exist_ok=True)
        source=out/'graphics_host.c'
        source.write_text('#define __fastcall__\nunsigned char arena[7232];\n#define BBK_FRAMEBUFFER (arena+16)\n#include "'+(SDK/'src/graphics.c').as_posix()+'"\n',encoding='utf8')
        compiler=shutil.which('gcc')
        if not compiler:raise RuntimeError('GCC required for host graphics tests')
        env=os.environ.copy();env['PATH']=str(Path(compiler).parent)+os.pathsep+env.get('PATH','')
        subprocess.run([compiler,'-O2','-shared','-fPIC','-static-libgcc','-I',str(SDK/'include'),str(source),'-o',str(out/'graphics.dll')],check=True,env=env)
        cls.lib=C.CDLL(str(out/'graphics.dll'));cls.memory=(C.c_ubyte*7232).in_dll(cls.lib,'arena')
        for name,n in [('bbk_pixel',3),('bbk_fill',5),('bbk_hline',4),('bbk_vline',4)]:getattr(cls.lib,name).argtypes=[C.c_ubyte]*n
        cls.lib.bbk_tile12.argtypes=[C.c_ubyte,C.c_ubyte,C.POINTER(C.c_ubyte),C.c_ubyte]
        cls.lib.bbk_mono.argtypes=[C.c_ubyte,C.c_ubyte,C.POINTER(C.c_ubyte),C.c_ubyte,C.c_ubyte,C.c_ubyte]
    def setUp(self):
        for i in range(7232):self.memory[i]=0xa5 if i<16 or i>=7216 else 0
    def tearDown(self):
        self.assertEqual(bytes(self.memory[:16]),b'\xa5'*16);self.assertEqual(bytes(self.memory[7216:]),b'\xa5'*16)
    def pixels(self):return [(self.memory[16+y*60+(x>>2)]>>(6-2*(x&3)))&3 for y in range(120) for x in range(240)]
    def test_unaligned_rectangle_preserves_other_pixels(self):
        self.lib.bbk_fill(1,2,7,3,2)
        self.assertEqual(self.pixels(),[2 if 1<=x<8 and 2<=y<5 else 0 for y in range(120) for x in range(240)])
    def test_rectangle_clips_right_bottom_and_masks_shade(self):
        self.lib.bbk_fill(238,118,255,255,7)
        self.assertEqual(self.pixels(),[3 if x>=238 and y>=118 else 0 for y in range(120) for x in range(240)])
    def test_outside_and_zero_extent_are_noops(self):
        for args in [(240,0,3,3,3),(0,120,3,3,3),(255,255,255,255,3),(0,0,0,10,3),(0,0,10,0,3)]:self.lib.bbk_fill(*args)
        self.assertFalse(any(self.pixels()))
    def test_all_four_pixels_pack_high_bits_first(self):
        for x in range(4):self.lib.bbk_pixel(x,0,x)
        self.assertEqual(self.memory[16],0x1b)
    def test_tile_unaligned_and_clipped(self):
        tile=(C.c_ubyte*36)(*([0xff]*36));self.lib.bbk_tile12(237,117,tile,0)
        self.assertEqual(self.pixels(),[3 if x>=237 and y>=117 else 0 for y in range(120) for x in range(240)])
    def test_aligned_mono_is_transparent_and_matches_bit_order(self):
        self.lib.bbk_fill(0,0,240,120,1)
        bits=(C.c_ubyte*4)(0xa5,0xd0,0x3c,0x60)
        self.lib.bbk_mono(4,2,bits,12,2,3)
        expected=[]
        for y in range(120):
            for x in range(240):
                on=2<=y<4 and 4<=x<16 and bits[(y-2)*2+((x-4)>>3)]&(128>>((x-4)&7))
                expected.append(3 if on else 1)
        self.assertEqual(self.pixels(),expected)
if __name__=='__main__':unittest.main()
