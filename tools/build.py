"""Build the V1.10 runtime and a 7980 application with pinned cc65."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
VERSION='1.1.0'

def compiler_path(value=None):
    exe='cl65.exe' if os.name=='nt' else 'cl65'
    candidates=[value,os.environ.get('CC65_HOME') and str(Path(os.environ['CC65_HOME'])/'bin'/exe),
                ROOT/'toolchain/cc65/bin'/exe,shutil.which('cl65')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():return Path(candidate).resolve()
    raise RuntimeError('cc65 not found: run tools/install_toolchain.py, pass --compiler PATH, or use the Windows SDK bundle.')

def run(command):
    subprocess.run([str(v) for v in command],check=True)

def runtime(compiler):
    out=ROOT/'lib';out.mkdir(exist_ok=True)
    sources=[ROOT/'src'/s for s in ['os.s','time.c','font.c','files.c','graphics.c','music.c']]
    tracked=[ROOT/'src/crt0.s',ROOT/'include/bbk7980.h',*sources]
    version=subprocess.run([str(compiler),'--version'],capture_output=True,text=True,check=True).stderr.strip()
    digest=hashlib.sha256(version.encode()+b''.join(p.read_bytes() for p in tracked)).hexdigest()
    stamp=out/'runtime.json'
    if stamp.exists() and json.loads(stamp.read_text())['source_sha256']==digest and all((out/p).exists() for p in ['bbk7980-v110.lib','crt0.o']):return out
    objects=[]
    for source in [ROOT/'src/crt0.s',*sources]:
        target=out/(source.stem+'.o')
        run([compiler,'--cpu','65c02','-t','none','-Oirs','-I',ROOT/'include','-c','-o',target,source])
        if source.stem!='crt0':objects.append(target)
    lib=out/'bbk7980-v110.lib'
    if lib.exists():lib.unlink()
    run([compiler.with_name('ar65'+compiler.suffix),'a',lib,*objects])
    stamp.write_text(json.dumps(dict(sdk=VERSION,compiler=version,source_sha256=digest),indent=2),encoding='utf-8')
    return out

def checksum_banks(payload):
    for offset in range(0,len(payload),0x4000):
        a=c=0
        for v in payload[offset:offset+0x3fff]:
            total=a+v+c;a=total&255;c=total>>8
        payload[offset+0x3fff]=(-a-c)&255

def default_icon():
    pixels=[0]*1024
    for y in range(2,30):
        for x in range(2,30):pixels[y*32+x]=3 if x in (2,29) or y in (2,29) else 1
    for y in range(8,24):
        for x in range(8,24):
            if (x//4+y//4)&1:pixels[y*32+x]=3
    return bytes(sum(pixels[y*32+x+i]<<(6-2*i) for i in range(4)) for y in range(32) for x in range(0,32,4))

def build(project,compiler=None,output=None):
    project=Path(project).resolve()
    spec=json.loads((project/'project.json').read_text(encoding='utf-8'))
    name=spec['name'];caption=name.encode('gbk');filename=(name+'.exe').encode('gbk')
    if not caption or len(caption)>8 or any(c in name for c in '/\\:\0'):raise ValueError('Name must fit 8 GBK bytes and contain no path separators')
    category=int(spec.get('category',9))
    if not 1<=category<=11:raise ValueError('Category must be 1..11')
    compiler=compiler_path(compiler);lib=runtime(compiler)
    out=Path(output).resolve() if output else project/'build';out.mkdir(parents=True,exist_ok=True)
    objects=[]
    for i,value in enumerate(spec.get('sources',['main.c'])):
        source=(project/value).resolve()
        if not source.is_relative_to(project):raise ValueError('Source must be within project')
        target=out/f'app-{i}.o';objects.append(target)
        run([compiler,'--cpu','65c02','-t','none','-Oirs','-I',ROOT/'include','-I',project,'-c','-o',target,source])
    run([compiler,'--cpu','65c02','-t','none','-C',ROOT/'cfg/7980-v110.cfg','-m',out/'app.map','-Ln',out/'app.lbl',
         '-o',out/'code.bin',lib/'crt0.o',*objects,lib/'bbk7980-v110.lib'])
    code=(out/'code.bin').read_bytes()
    if len(code)!=0x3fff:raise ValueError('Unexpected linked bank size')
    payload=bytearray(0x8000);payload[:len(code)]=code
    payload[0x4000:0x4008]=caption.ljust(8,b' ')
    icon=(project/spec['icon']).read_bytes() if 'icon' in spec else default_icon()
    if len(icon)!=256:raise ValueError('Icon must be 256 bytes, packed 32x32 at 2bpp')
    payload[0x4010:0x4110]=icon;payload[0x7c00:0x7c00+len(caption)]=caption;payload[0x7c14]=0xff
    checksum_banks(payload)
    header=bytearray(128);header[:9]=b'BJBBK.110';header[12:16]=b'exe\0'
    header[16:20]=bytes([0x6e,0,0,0xff]);header[23:26]=b'\xff'*3
    header[26:28]=bytes([category,1]);header[32:32+len(filename)]=filename
    struct.pack_into('<III',header,96,len(payload),sum(payload)&0xffffffff,128)
    header[108:127]=b'2026/11/20 00:00:00'
    (out/'app.bin').write_bytes(payload);container=header+payload
    (out/(name+'.exe')).write_bytes(container)
    symbols={}
    for line in (out/'app.lbl').read_text().splitlines():
        fields=line.split()
        if len(fields)==3 and fields[0]=='al':symbols[fields[2].lstrip('.')]=int(fields[1],16)
    report=dict(sdk=VERSION,target='7980-v110',name=name,category=category,
                payload_sha256=hashlib.sha256(payload).hexdigest(),sha256=hashlib.sha256(container).hexdigest(),symbols=symbols)
    (out/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out/(name+'.exe'));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path)
    parser.add_argument('--compiler',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();build(args.project,args.compiler,args.output)
