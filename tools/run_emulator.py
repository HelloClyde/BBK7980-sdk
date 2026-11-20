"""Run the native examples with an existing emulator and a separate session directory."""
from pathlib import Path
import argparse
import importlib.util
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--emulator',type=Path,required=True)
    p.add_argument('--nand',type=Path);p.add_argument('--minesweeper',action='store_true');p.add_argument('--smoke-test')
    p.add_argument('--example',choices=['minesweeper','hello','diagnostics','storage','music'])
    a=p.parse_args()
    from emulator import normalize
    emulator=normalize(a.emulator)
    from emulator_backend import prepare
    viewer=prepare(emulator)
    io=a.example in ['storage','music']
    session=ROOT/'build'/('io-session' if io else 'emulator-session');session.mkdir(parents=True,exist_ok=True)
    nand=a.nand.resolve() if a.nand else session/'sdk-nand.bin.z'
    if not a.nand:
        from emulator import install
        selected=[('storage','存储演示.exe'),('music','音乐演示.exe')] if io else [('minesweeper','扫雷.exe'),('hello','开发演示.exe'),('diagnostics','开发自检.exe')]
        programs=[ROOT/'examples'/n/'build'/f for n,f in selected]
        saved=session/'data/nand.bin'
        source=saved if saved.exists() else emulator/'runtime/installed-nand.bin.z'
        install(emulator,source,programs,nand)
    sys.path.insert(0,str(viewer))
    spec=importlib.util.spec_from_file_location('bbk7980_sdk_viewer',viewer/'app.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.APP_DIR=session
    class Viewer(module.Emulator):
        def launch_minesweeper(self):
            index={'minesweeper':6,'hello':7,'diagnostics':8,'storage':6,'music':7}[a.example or 'minesweeper']
            for code in [43]*8+[index]:
                self.machine.lib.bbk_key(code//8,code%8,1);self.machine.run(300_000)
                self.machine.lib.bbk_key(code//8,code%8,0);self.machine.run(40_000_000 if code==index else 5_000_000)
    window=module.tk.Tk()
    Viewer(window,SimpleNamespace(nand=str(nand),minesweeper=a.minesweeper or bool(a.example),smoke_test=a.smoke_test))
    window.mainloop()
