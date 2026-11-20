"""Use the bundled GPL board/UI with firmware supplied by an existing emulator."""
from pathlib import Path
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import os
ROOT=Path(__file__).resolve().parents[1]

def prepare(emulator):
    from emulator import normalize
    emulator=normalize(emulator)
    support=ROOT/'emulator-support'
    if not support.exists():return Path(emulator).resolve()
    dll=support/'bbk7980.dll';digest=hashlib.sha256(dll.read_bytes()).hexdigest()
    work=ROOT/'build/emulator-board'/digest[:12];(work/'runtime').mkdir(parents=True,exist_ok=True)
    if not (work/'bbk7980.dll').exists():shutil.copy2(dll,work/'bbk7980.dll')
    firmware=(Path(emulator)/'runtime/syscode.bin').read_bytes()
    if hashlib.sha256(firmware).hexdigest()!='1f020acdb26a3081839e89f89f325649c231b89e7541505f9fa01edc4d4533a1':
        raise ValueError('Unsupported original firmware')
    target=work/'runtime/syscode.bin'
    if not target.exists() or hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(firmware).digest():
        with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as f:f.write(firmware);temporary=f.name
        os.replace(temporary,target)
    spec=importlib.util.spec_from_file_location('machine',support/'machine.py')
    module=importlib.util.module_from_spec(spec);sys.modules['machine']=module;spec.loader.exec_module(module)
    module.ROOT=work
    sys.path[:0]=[str(support),str(support/'tools')]
    return support
