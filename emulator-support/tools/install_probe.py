"""Reverse-engineering harness; uses the stock download service over UART."""
from pathlib import Path
import sys
import ctypes as C
import struct
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from machine import Machine, ROOT

class Link:
    def __init__(self, m):self.m=m;self.buffer=bytearray()
    def send(self, data):
        buf=(C.c_uint8*len(data)).from_buffer_copy(data)
        if self.m.lib.bbk_uart_send(buf,len(data)):raise RuntimeError('UART queue full')
    def read(self, size):
        for _ in range(1000):
            if len(self.buffer)>=size:
                result=bytes(self.buffer[:size]);del self.buffer[:size];return result
            self.m.run(50_000)
            buf=(C.c_uint8*65536)();n=self.m.lib.bbk_uart_receive(buf,len(buf))
            self.buffer.extend(buf[:n])
        raise TimeoutError(f'UART: expected {size}, have {self.buffer.hex()}, PC={self.m.state()}')
    def input(self, data):
        marker=self.read(1)
        if marker!=b'U':raise RuntimeError(f'Expected input request, got {marker.hex()}')
        self.m.run(20_000)
        self.send(struct.pack('<HH',len(data),sum(data)&65535))
        self.m.run(20_000) # Allow the guest to switch its RX destination after the header.
        self.send(data)
    def output(self):
        size,checksum=struct.unpack('<HH',self.read(4));self.send(b'U');data=self.read(size)
        if sum(data)&65535!=checksum:raise RuntimeError('Guest packet checksum mismatch')
        return data
    def connect(self):
        self.send(b'U');assert self.read(1)==b'\xaa'
        self.send(b'B100HOST\0');assert self.read(9)==b'B100HOST\0'
        print('Device:',self.read(10).hex())
        self.send(b'\x02\0');self.input(struct.pack('<HH',0xe000,8192))
        assert self.output()==struct.pack('<H',8192)
    def put(self,name,data,flags=0):
        self.input(b'\x11');assert self.output()==b'\x11'
        self.input(b'\0') # Empty host-supplied progress message.
        meta=name.encode('gb18030').ljust(64,b'\0')+struct.pack('<II IHH',0,0,(len(data)+8191)//8192,sum(data)&65535,flags)
        self.input(meta)
        for start in range(0,len(data),8192):self.input(data[start:start+8192])
        print('Complete:',name,self.output())

    def get(self,name):
        self.input(b'\x10');assert self.output()==b'\x10';self.input(b'\0')
        self.input(name.encode('gb18030').ljust(64,b'\0'))
        count,size=struct.unpack('<II',self.output())
        data=b''.join(self.output() for _ in range(count))
        if len(data)!=size:raise RuntimeError('Guest file length mismatch')
        return data
