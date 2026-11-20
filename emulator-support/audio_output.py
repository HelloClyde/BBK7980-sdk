"""Small WinMM PCM queue; emulated PSG samples remain the only sound source."""
import ctypes as C
import sys

class Format(C.Structure):
    _fields_=[('tag',C.c_ushort),('channels',C.c_ushort),('rate',C.c_uint32),
              ('bytes_per_second',C.c_uint32),('alignment',C.c_ushort),('bits',C.c_ushort),('extra',C.c_ushort)]
class Header(C.Structure):
    _fields_=[('data',C.c_void_p),('length',C.c_uint32),('recorded',C.c_uint32),
              ('user',C.c_size_t),('flags',C.c_uint32),('loops',C.c_uint32),('next',C.c_void_p),('reserved',C.c_size_t)]

class AudioOutput:
    def __init__(self):
        self.available=False;self.pending=[];self.handle=C.c_void_p()
        if sys.platform!='win32':return
        self.winmm=C.WinDLL('winmm')
        self.winmm.waveOutOpen.argtypes=[C.POINTER(C.c_void_p),C.c_uint32,C.POINTER(Format),C.c_size_t,C.c_size_t,C.c_uint32]
        for name in ['waveOutPrepareHeader','waveOutUnprepareHeader','waveOutWrite']:
            getattr(self.winmm,name).argtypes=[C.c_void_p,C.POINTER(Header),C.c_uint32]
        for name in ['waveOutReset','waveOutClose']:getattr(self.winmm,name).argtypes=[C.c_void_p]
        fmt=Format(1,1,22050,44100,2,16,0)
        self.available=self.winmm.waveOutOpen(C.byref(self.handle),0xffffffff,C.byref(fmt),0,0,0)==0
    def write(self,pcm):
        if not self.available:return
        keep=[]
        for header,buffer in self.pending:
            if header.flags&1:self.winmm.waveOutUnprepareHeader(self.handle,C.byref(header),C.sizeof(header))
            else:keep.append((header,buffer))
        self.pending=keep
        if not pcm or len(self.pending)>=12:return
        buffer=C.create_string_buffer(pcm);header=Header(C.cast(buffer,C.c_void_p),len(pcm),0,0,0,0,None,0)
        if self.winmm.waveOutPrepareHeader(self.handle,C.byref(header),C.sizeof(header))!=0:return
        if self.winmm.waveOutWrite(self.handle,C.byref(header),C.sizeof(header))!=0:
            self.winmm.waveOutUnprepareHeader(self.handle,C.byref(header),C.sizeof(header));return
        self.pending.append((header,buffer))
    def clear(self):
        if not self.available:return
        self.winmm.waveOutReset(self.handle)
        for header,_ in self.pending:self.winmm.waveOutUnprepareHeader(self.handle,C.byref(header),C.sizeof(header))
        self.pending=[]
    def close(self):
        if self.available:
            self.clear();self.winmm.waveOutClose(self.handle);self.available=False
