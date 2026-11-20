"""Install BJBBK applications through an unmodified guest's UART file service."""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import json
import struct
import sys
import zlib

FIRMWARE_SHA256='1f020acdb26a3081839e89f89f325649c231b89e7541505f9fa01edc4d4533a1'

def normalize(path):
    path=Path(path).resolve()
    for candidate in [path,path/'_internal',path/'source']:
        if (candidate/'runtime/syscode.bin').is_file():return candidate
    raise ValueError('Emulator folder must contain runtime/syscode.bin (or _internal/runtime)')

def parse(path):
    raw=Path(path).read_bytes()
    if len(raw)<128 or raw[:9]!=b'BJBBK.110':raise ValueError('Not a BJBBK.110 application')
    size,checksum,header=struct.unpack_from('<III',raw,96)
    if header!=128 or len(raw)!=128+size or sum(raw[128:])&0xffffffff!=checksum:raise ValueError('Invalid container checksum or size')
    payload=raw[128:]
    if size%0x4000:raise ValueError('Application payload is not bank-aligned')
    for offset in range(0,size,0x4000):
        a=c=0
        for v in payload[offset:offset+0x4000]:
            total=a+v+c;a=total&255;c=total>>8
        if a:raise ValueError('Invalid native bank checksum')
    return raw[32:96].split(b'\0')[0].decode('gbk'),payload,int.from_bytes(raw[26:28],'little')

def install(emulator,source,applications,output=None):
    emulator=normalize(emulator)
    if hashlib.sha256((emulator/'runtime/syscode.bin').read_bytes()).hexdigest()!=FIRMWARE_SHA256:raise ValueError('Unsupported system firmware; expected original 7980 V1.10')
    # A PyInstaller _internal directory contains Python/Tk binaries. It is an
    # asset source, never a Python import path for the SDK's interpreter.
    if (emulator/'machine.py').exists():sys.path.insert(0,str(emulator))
    if (emulator/'tools/install_probe.py').exists():sys.path.insert(0,str(emulator/'tools'))
    from machine import Machine
    from install_probe import Link
    from capture_games import tap
    records=[parse(p) for p in applications]
    machine=Machine();machine.load_nand(source);machine.run(80_000_000)
    for _ in range(10):tap(machine,43)
    tap(machine,0,30_000_000)
    link=Link(machine);link.connect();report=[]
    for name,data,flags in records:
        link.put(name,data,flags)
        if link.get(name)!=data:raise RuntimeError('Native file readback mismatch: '+name)
        report.append(dict(name=name,sha256=hashlib.sha256(data).hexdigest(),readback='identical'))
    if output:
        output=Path(output).resolve()
        if output==Path(source).resolve():raise ValueError('Output must differ from source')
        if output.suffix!='.z':raise ValueError('Output must end in .z (compressed NAND)')
        output.parent.mkdir(parents=True,exist_ok=True)
        buf=(C.c_uint8*machine.lib.bbk_nand_size())();machine.lib.bbk_nand_export(buf)
        output.write_bytes(zlib.compress(bytes(buf),9))
        output.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return machine,report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emulator',required=True,type=Path);p.add_argument('--source',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);p.add_argument('applications',nargs='+',type=Path)
    a=p.parse_args();install(a.emulator,a.source,a.applications,a.output)
