"""Package the SDK sources, minimal toolchain, examples and validation evidence."""
from pathlib import Path
import hashlib
import json
import os
import zipfile
from verify_examples import EXAMPLES, verify
ROOT=Path(__file__).resolve().parents[1]
VERSION=json.loads((ROOT/'SDK.json').read_text(encoding='utf8'))['version']

def release_files():
    for name in ['README.md','LICENSE','THIRD_PARTY.md','CHANGELOG.md','SDK.json','build-examples.cmd','requirements-images.txt','.gitignore','.gitattributes']:
        yield Path(name),(ROOT/name).read_bytes()
    for folder in ['include','cfg','src','tools','tests','docs','research','third_party','validation','.github']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts: yield p.relative_to(ROOT),p.read_bytes()
    for p in sorted((ROOT/'emulator-support').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.dll': yield p.relative_to(ROOT),p.read_bytes()
    yield Path('emulator-support/bbk7980.dll'),(ROOT/'emulator-support/bbk7980.dll').read_bytes()
    for p in sorted((ROOT/'toolchain/cc65').rglob('*')):
        if p.is_file(): yield p.relative_to(ROOT),p.read_bytes()
    for name in ['bbk7980-v110.lib','crt0.o','runtime.json']:
        yield Path('lib')/name,(ROOT/'lib'/name).read_bytes()
    for example in EXAMPLES:
        project=ROOT/'examples'/example
        for p in sorted(project.iterdir()):
            if p.is_file(): yield p.relative_to(ROOT),p.read_bytes()
        for p in sorted((project/'build').glob('*.exe')):
            yield Path('bin')/p.name,p.read_bytes()
            yield p.relative_to(ROOT),p.read_bytes()
        for name in ['app.bin','build.json']:
            p=project/'build'/name
            yield p.relative_to(ROOT),p.read_bytes()
    yield Path('validation/ci-report.json'),(ROOT/'build/ci-report.json').read_bytes()

def package():
    if os.name!='nt': raise RuntimeError('The win64 bundle must be built on Windows')
    verify()
    files=sorted(release_files(),key=lambda entry:entry[0].as_posix())
    names=[p.as_posix() for p,_ in files]
    if len(set(names))!=len(names): raise ValueError('Duplicate release path')
    manifest=''.join(hashlib.sha256(data).hexdigest()+'  '+path.as_posix()+'\n' for path,data in files)
    files.append((Path('SHA256SUMS.txt'),manifest.encode('utf8')))
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/f'BBK7980-SDK-{VERSION}-win64.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path,data in files:
            info=zipfile.ZipInfo(f'BBK7980-SDK-{VERSION}/'+path.as_posix(),date_time=(2026,11,20,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,data,compresslevel=9)
    with zipfile.ZipFile(target) as z:
        if z.testzip(): raise ValueError('Archive CRC failure')
    report=dist/'build-report.json';report.write_bytes((ROOT/'build/ci-report.json').read_bytes())
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in [target,report])
    (dist/'SHA256SUMS.txt').write_text(sums,encoding='utf8',newline='\n')
    print(sums)
    return target

if __name__=='__main__': package()
