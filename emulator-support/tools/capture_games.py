"""Capture actual stock firmware game screens through keyboard matrix input."""
from pathlib import Path
import sys
import json
import hashlib
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from machine import Machine,ROOT
from keyboard import KEYS

PALETTE=[235,241,220,153,169,131,83,105,65,26,45,25]+[0]*756
OUT=ROOT/'runtime/games'

def save(machine,name):
    im=Image.frombytes('P',(240,120),machine.frame());im.putpalette(PALETTE)
    path=OUT/name;im.resize((960,480),Image.Resampling.NEAREST).convert('RGB').save(path)
    return path

def tap(machine,code,settle=5_000_000):
    machine.lib.bbk_key(code//8,code%8,1);machine.run(300_000)
    machine.lib.bbk_key(code//8,code%8,0);machine.run(settle)

def menu(machine):
    machine.lib.bbk_reset();machine.run(80_000_000)
    for _ in range(8):tap(machine,43)
