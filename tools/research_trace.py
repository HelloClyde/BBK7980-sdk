"""Build an observation-only board variant for tracing original firmware calls."""
from pathlib import Path
import ctypes as C
import os
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]

def traced_machine(emulator):
    emulator=Path(emulator).resolve();out=ROOT/'build/research-trace';out.mkdir(parents=True,exist_ok=True)
    source=(emulator/'src/machine.c').read_text()
    source=source.replace('#include "../vendor/s6502.c"','#include "'+(emulator/'vendor/s6502.c').as_posix()+'"')
    helper=r'''
static uint32_t trace_rows[1024][32], trace_count, trace_mask, trace_io_seen[128];
static void observe(uint32_t kind,uint32_t address,uint32_t value) {
    if (trace_count>=1024) return;
    uint32_t *row=trace_rows[trace_count++];
    row[0]=(uint32_t)clocks;row[1]=cpu.pc;row[2]=io[0x32]|(io[0x33]<<8);
    row[3]=cpu.ac;row[4]=cpu.ix;row[5]=cpu.sp;
    row[6]=rd(0x100|((cpu.sp+1)&255))|(rd(0x100|((cpu.sp+2)&255))<<8);
    row[7]=kind;row[8]=address;row[9]=value;
    for (int i=0;i<20;i++)row[10+i]=rd(0x6c0+i);
}
API void bbk_trace_reset(uint32_t mask) {trace_count=0;trace_mask=mask;memset(trace_io_seen,0,sizeof(trace_io_seen));}
API uint32_t bbk_trace_export(uint32_t *dest,uint32_t size) {
    uint32_t count=trace_count<size?trace_count:size;memcpy(dest,trace_rows,count*sizeof(trace_rows[0]));return count;
}
'''
    marker='static void wr(uint16_t a, uint8_t v) {'
    if marker not in source:raise RuntimeError('Board source layout changed')
    source=source.replace(marker,helper+'\n'+marker+'''
    if ((trace_mask&2) && a>=0x10 && a<=0x17 && trace_io_seen[a]++<16) observe(1,a,v);
''')
    source=source.replace('history[history_pos++&63]=cpu.pc;',r'''
        uint32_t tb=io[0x32]|(io[0x33]<<8);
        if ((trace_mask&1) && !irq_service && tb==7 &&
            (cpu.pc==0x6435 || cpu.pc==0x680e || cpu.pc==0x6aa8 || cpu.pc==0x778b || cpu.pc==0x7aa7 || cpu.pc==0x7e46)) observe(0,0,0);
        history[history_pos++&63]=cpu.pc;
''')
    cfile=out/'traced.c';cfile.write_text(source,encoding='utf8')
    compiler=shutil.which('gcc');env=os.environ.copy();env['PATH']=str(Path(compiler).parent)+os.pathsep+env.get('PATH','')
    subprocess.run([compiler,'-O2','-shared','-static-libgcc','-std=gnu11',str(cfile),'-o',str(out/'bbk7980.dll')],check=True,env=env)
    sys.path[:0]=[str(emulator),str(emulator/'tools')]
    import machine
    machine.ROOT=out
    m=machine.Machine(emulator/'runtime/syscode.bin')
    m.lib.bbk_trace_export.argtypes=[C.POINTER(C.c_uint32),C.c_uint32]
    def records():
        buf=(C.c_uint32*(1024*32))();count=m.lib.bbk_trace_export(buf,1024)
        return [list(buf[i*32:(i+1)*32]) for i in range(count)]
    return m,records
