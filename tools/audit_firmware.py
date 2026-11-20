"""Record ABI evidence from the original updater; do not redistribute its code."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS=[('context_init',2,0x4108,0x410e),('event_wait',2,0x410e,0x4120),
 ('event_translate',2,0x4120,0x4132),('keys_flush',2,0x43a5,0x43ab),
 ('font_glyph',5,0x40d2,0x4108),('file_find',7,0x4024,0x4036),
 ('file_size',3,0x4072,0x4084),('file_read_at',7,0x4072,0x40ae),
 ('heap_init',2,0x4132,0x4150),('heap_alloc',2,0x4150,0x4162),('heap_free',2,0x4162,0x4174),
 ('file_open',7,0x4000,0x4024),('file_write',7,0x4112,0x4136),('file_close',7,0x4036,0x4042),
 ('file_seek',7,0x4136,0x4160),('file_delete',7,0x4172,0x4184),('beep_hardware_reference',2,0x4264,0x426a)]

def audit(updater):
    import pefile
    updater=Path(updater);raw=updater.read_bytes();pe=pefile.PE(data=raw);pkg=None
    for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if not hasattr(kind,'directory'):continue
        for item in kind.directory.entries:
            if str(item.name)=='RC_PKG':
                e=item.directory.entries[0].data.struct;pkg=pe.get_data(e.OffsetToData,e.Size)
    pe.close()
    if pkg is None:raise ValueError('Original package resource missing')
    records=[];pos=0
    while pkg[pos:pos+9]==b'BJBBK.110':
        size,total,header=struct.unpack_from('<III',pkg,pos+96)
        if header!=128:raise ValueError('Header size')
        data=pkg[pos+128:pos+128+size]
        if sum(data)&0xffffffff!=total:raise ValueError('Original checksum')
        records.append((pkg[pos+32:pos+96].split(b'\0')[0].decode('gbk'),data))
        pos+=128+size
    if pkg[pos:pos+8]!=b'7980UPG!':raise ValueError('Original trailer')
    code=records[0][1];offset,length=struct.unpack_from('<II',code);rom=code[offset-128:offset-128+length]
    digest=hashlib.sha256(rom).hexdigest()
    if digest!='1f020acdb26a3081839e89f89f325649c231b89e7541505f9fa01edc4d4533a1':raise ValueError('Unknown firmware')
    functions=[]
    for name,bank,start,end in FUNCTIONS:
        pattern=b'\x20\xee\x86'+struct.pack('<HB',start,bank)
        callers=[dict(file=n,byte_offset=i) for n,data in records[1:] for i in range(len(data)-5) if data[i:i+6]==pattern]
        physical=(bank^1)*0x4000+(start&0x3fff)
        functions.append(dict(api=name,bank=bank,address=start,entry_sha256=hashlib.sha256(rom[physical:physical+end-start]).hexdigest(),original_app_byte_references=callers))
    samples=[]
    for name in ['炸弹小子.exe','五子棋.exe','黑白子.exe']:
        data=next(data for n,data in records if n==name)
        assert data[:6]==b'\x20\xee\x86\x08\x41\x02'
        samples.append(dict(file=name,payload_sha256=hashlib.sha256(data).hexdigest(),entry_calls_context_init=True))
    result=dict(source_url='https://down.eebbk.net/xzzx/7980/1/7980sj.exe',
                updater_sha256=hashlib.sha256(raw).hexdigest(),firmware_sha256=digest,record_count=len(records),
                samples=samples,functions=functions,
                method='Entry bodies decoded with a 65C02 disassembler, cross-checked against original callers and live unmodified guest calls. Byte-pattern references alone are not a control-flow proof.')
    dest=ROOT/'research/abi.json';dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(dest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('updater',type=Path);audit(p.parse_args().updater)
