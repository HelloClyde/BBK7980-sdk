"""Exercise the same C rules compiled into the native 7980 program."""
from pathlib import Path
import ctypes as C
import os
import shutil
import subprocess
import unittest
APP=Path(__file__).resolve().parents[1]/'examples/minesweeper'

class Game(C.Structure):
    _fields_=[('cells',C.c_ubyte*96),('queue',C.c_ubyte*96),('seed',C.c_ushort),
              ('state',C.c_ubyte),('opened',C.c_ubyte),('flags',C.c_ubyte),('placed',C.c_ubyte)]

def neighbors(p):
    return [i for i in range(96) if i!=p and abs(i%12-p%12)<=1 and abs(i//12-p//12)<=1]

class Rules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler=shutil.which('gcc')
        if not compiler:raise RuntimeError('GCC required for host rules tests')
        (APP/'build').mkdir(parents=True,exist_ok=True)
        env=os.environ.copy();env['PATH']=str(Path(compiler).parent)+os.pathsep+env.get('PATH','')
        subprocess.run([compiler,'-O2','-shared','-fPIC','-static-libgcc',str(APP/'game.c'),'-o',str(APP/'build/rules.dll')],check=True,env=env)
        cls.lib=C.CDLL(str(APP/'build/rules.dll'))
        cls.lib.game_new.argtypes=[C.POINTER(Game),C.c_ushort]
        for name in ('game_open','game_flag','game_chord'):getattr(cls.lib,name).argtypes=[C.POINTER(Game),C.c_ubyte]

    def new(self,seed=1234,first=0):
        g=Game();self.lib.game_new(C.byref(g),seed)
        if first is not None:self.lib.game_open(C.byref(g),first)
        return g

    def test_first_click_safe_and_exact_mine_count(self):
        for seed in (0,1,17,1234,65535):
            for first in range(96):
                g=self.new(seed,first)
                self.assertEqual(sum(bool(v&128) for v in g.cells),15)
                self.assertFalse(any(g.cells[i]&128 for i in neighbors(first)+[first]))
                self.assertEqual(g.cells[first]&15,0)

    def test_neighbor_numbers_and_flood_boundary(self):
        g=self.new()
        for p,v in enumerate(g.cells):
            if not v&128:self.assertEqual(v&15,sum(bool(g.cells[i]&128) for i in neighbors(p)))
            if v&16 and not v&15:
                self.assertTrue(all(g.cells[i]&16 for i in neighbors(p)))
        self.assertGreater(g.opened,1)
        self.assertEqual(g.opened,sum(bool(v&16) for v in g.cells))

    def test_flag_protects_a_cell_before_first_open(self):
        g=self.new(first=None)
        self.lib.game_flag(C.byref(g),0);self.lib.game_open(C.byref(g),0)
        self.assertEqual((g.flags,g.placed,g.opened),(1,0,0))
        self.lib.game_flag(C.byref(g),0);self.lib.game_open(C.byref(g),0)
        self.assertEqual(g.flags,0);self.assertTrue(g.placed)

    def test_loss_freezes_actions_and_restart_clears_everything(self):
        g=self.new();p=next(i for i,v in enumerate(g.cells) if v&128)
        self.lib.game_open(C.byref(g),p);self.assertEqual(g.state,2)
        before=bytes(g.cells);self.lib.game_flag(C.byref(g),2);self.lib.game_open(C.byref(g),95)
        self.assertEqual(bytes(g.cells),before)
        self.lib.game_new(C.byref(g),42)
        self.assertEqual((g.state,g.opened,g.flags,g.placed),(0,0,0,0))
        self.assertFalse(any(g.cells))

    def test_revealing_all_safe_cells_wins(self):
        g=self.new()
        for p in range(96):
            if not g.cells[p]&128:self.lib.game_open(C.byref(g),p)
        self.assertEqual((g.state,g.opened,g.flags),(3,81,15))
        self.assertTrue(all(v&32 for v in g.cells if v&128))

    def test_correct_flags_allow_chording(self):
        g=self.new()
        p=next(p for p,v in enumerate(g.cells) if v&16 and v&15 and
               any(not g.cells[i]&(128|16) for i in neighbors(p)))
        for i in neighbors(p):
            if g.cells[i]&128:self.lib.game_flag(C.byref(g),i)
        before=g.opened;self.lib.game_chord(C.byref(g),p)
        self.assertNotEqual(g.state,2);self.assertGreater(g.opened,before)

    def test_incorrect_flags_can_lose_on_chord(self):
        g=self.new();p=next(p for p,v in enumerate(g.cells) if v&16 and v&15 and
                           any(not g.cells[i]&(128|16) for i in neighbors(p)))
        mines=[i for i in neighbors(p) if g.cells[i]&128]
        wrong=next(i for i in neighbors(p) if not g.cells[i]&(128|16))
        for i in mines[1:]+[wrong]:self.lib.game_flag(C.byref(g),i)
        self.lib.game_chord(C.byref(g),p);self.assertEqual(g.state,2)

if __name__=='__main__':unittest.main()
