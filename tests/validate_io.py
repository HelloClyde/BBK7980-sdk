"""Validate real native file mutation/persistence and PSG music output."""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import json
import struct
import sys
import wave
import zlib
SDK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SDK/'tools'))
from emulator import install

def validate(emulator):
    emulator=Path(emulator).resolve();out=SDK/'build/validation';out.mkdir(parents=True,exist_ok=True)
    from emulator_backend import prepare
    prepare(emulator)
    m,installed=install(emulator,emulator/'runtime/installed-nand.bin.z',
        [SDK/'examples/storage/build/存储演示.exe',SDK/'examples/music/build/音乐演示.exe'],out/'io-nand.bin.z')
    from capture_games import tap,menu,PALETTE
    from install_probe import Link
    from machine import Machine
    from PIL import Image
    checks=[]
    def require(condition,label):
        if not condition:raise AssertionError(label)
        checks.append(label)
    def symbols(name):return json.loads((SDK/'examples'/name/'build/build.json').read_text(encoding='utf8'))['symbols']
    def rd(sym,name,n=1):return sum(m.lib.bbk_read(sym['_'+name]+i)<<(8*i) for i in range(n))
    def image(name):
        im=Image.frombytes('P',(240,120),m.frame());im.putpalette(PALETTE)
        im.resize((960,480),Image.Resampling.NEAREST).convert('RGB').save(out/(name+'.png'))
    def save(path):
        buf=(C.c_uint8*m.lib.bbk_nand_size())();m.lib.bbk_nand_export(buf)
        path.write_bytes(zlib.compress(bytes(buf),9))
    def link():
        m.lib.bbk_reset();m.run(80_000_000)
        for _ in range(10):tap(m,43)
        tap(m,0,30_000_000);l=Link(m);l.connect();return l
    menu(m);tap(m,6,40_000_000);s=symbols('storage')
    require(rd(s,'ok')==1 and rd(s,'wrote',2)==600,'Create/write/close/read 600 bytes across a NAND page')
    image('storage-written');tap(m,49,30_000_000)
    save(out/'storage-persisted.bin.z')
    m=Machine();m.load_nand(out/'storage-persisted.bin.z');l=link()
    original=bytes((i*37+11)&255 for i in range(600))
    require(l.get('SDKTEST.DAT')==original,'File survives NAND export/import and full CPU reset; original UART reads exact bytes')
    require(hashlib.sha256(l.get('font.bin')).hexdigest()==hashlib.sha256((emulator/'runtime/font.bin').read_bytes()).hexdigest(),'Native writes preserve the original font file')
    menu(m);tap(m,6,40_000_000);tap(m,44,100_000_000)
    flags=rd(s,'edge_flags')
    for bit,label in [(1,'UPDATE plus absolute seek preserves untouched bytes'),(2,'Exclusive create rejects existing file'),
                      (4,'Read-only stream rejects writes and still closes'),(8,'REPLACE truncates an existing file'),
                      (16,'Create/delete removes only the requested data file'),(32,'Current/EOF seeks and ROM-literal writes produce sho!t+')]:
        require(flags&bit,label)
    image('storage-updated');tap(m,49,30_000_000);l=link()
    require(l.get('SDKTEST.DAT')==b'sho!t+','Updated six-byte file is readable through original UART')
    save(out/'storage-final.bin.z')
    menu(m);tap(m,7,40_000_000);s=symbols('music');image('music-ready')
    require(hasattr(m.lib,'bbk_audio_read'),'PSG-enabled board is available')
    def start():
        m.lib.bbk_key(6,2,1)
        for _ in range(300):
            m.run(20_000)
            if rd(s,'playing') and m.lib.bbk_read(0x16)==6:break
        else:raise AssertionError('Music did not start')
        m.lib.bbk_key(6,2,0);m.lib.bbk_audio_clear()
    start();before=m.state();pcm=[];preloads=set();sampled=0
    # Inspect real SDK instructions while the first note and original IRQs run.
    for _ in range(20_000):
        flags=m.lib.bbk_flags();bank=m.lib.bbk_read(0x32)|(m.lib.bbk_read(0x33)<<8)
        if bank==0x120 and 0x4000<=m.lib.bbk_pc()<0x8000 and not flags&5:
            if m.lib.bbk_reg(5)&4:raise AssertionError('Music masks interrupts')
            sampled+=1
        m.run(1)
    pcm.append(m.audio());image('music-playing')
    for _ in range(400):
        m.run(100_000);pcm.append(m.audio())
        preloads.add(m.lib.bbk_read(0x10)|((m.lib.bbk_read(0x11)&15)<<8))
        if not rd(s,'playing'):break
    raw=b''.join(pcm);samples=struct.unpack('<'+'h'*(len(raw)//2),raw)
    require(rd(s,'completed')==1 and rd(s,'result')==0,'Original PSG registers play the complete 17-note/rest score')
    require(len(preloads)>=7,'Melody changes pitch through actual PSG frequency register writes')
    require(sampled>100 and m.state()['interrupts']>before['interrupts']+200,'Music C instructions leave IRQ enabled and system IRQs keep running')
    require(any(samples) and max(samples)>0 and min(samples)<0,'PSG device model produces non-silent bipolar PCM')
    crossings=[i for i in range(1,min(2205,len(samples))) if samples[i-1]<=0<samples[i]]
    frequency=22050*(len(crossings)-1)/(crossings[-1]-crossings[0]) if len(crossings)>1 else 0
    require(abs(frequency-262)<3,'First note measures approximately 262 Hz in the emulated output')
    require(m.lib.bbk_read(0x16)==0 and m.lib.bbk_read(0x17)==0,'Music completion shuts down PSG output')
    wav=out/'music-preview.wav'
    with wave.open(str(wav),'wb') as w:w.setparams((1,2,22050,0,'NONE','not compressed'));w.writeframes(raw)
    for key,label in [(49,'Esc'),(52,'Home')]:
        start();tap(m,key,30_000_000)
        require(m.state()['flags']&1 and m.state()['sp']==134 and not m.state()['p']&4 and m.lib.bbk_read(0x16)==0,
                label+' cancels music, silences PSG and returns to the original shell')
        if key==49:menu(m);tap(m,7,40_000_000)
    report=dict(result='passed',checks=checks,installed=installed,music_sdk_instruction_samples=sampled,
                first_note_hz=frequency,wav_seconds=len(raw)/44100,pcm_sha256=hashlib.sha256(raw).hexdigest(),
                wav_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),
                io_profile='storage and music occupy entertainment entries 7 and 8')
    (out/'io-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--emulator',required=True,type=Path);validate(p.parse_args().emulator)
