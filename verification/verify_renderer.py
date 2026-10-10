"""Read-only x86 renderer regression check. Run from any directory; never installs a mod.
Original game code runs through TIM conversion, sprite submission, surface sizing and UV
normalization. Win32 allocation and GPU boundaries are stubbed; GPU repeat sampling is
modeled with nearest-neighbor pixels (not a DXVK/driver or antialiasing fidelity test).
"""
from pathlib import Path
import hashlib, json, math, struct, re, subprocess, sys
import pefile
from PIL import Image
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_BLOCK
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_paths import GAME
OUT=ROOT/'build/native-verification'
HASHES={'Biohazard.exe':'25be34d4f4586e9ec84e39412915ae1de38af1fc5924c02824d38e15c8406458',
        'bio1hd.asi':'5cdc4ed20822b4e6619d870f57acead6026bc186a15503b96014a61fc0926f99'}
END=0x30000000; STACK=0x2fff000; SLOT=0x699314
class Engine:
    def __init__(self):
        self.u=Uc(UC_ARCH_X86,UC_MODE_32);self.heap=0x3000000;self.apis={};self.draws=[];self.uploads=[]
        self.u.mem_map(0,4096);self.u.mem_map(0x2000000,0x3000000);self.u.mem_map(END,4096)
        for name,base in [('Biohazard.exe',0x400000),('bio1hd.asi',0x18000000)]:
            data=(GAME/name).read_bytes();digest=hashlib.sha256(data).hexdigest()
            # The second hash changes only the LAA header flag, preserving all code.
            assert digest==HASHES[name] or (
                name=='Biohazard.exe' and digest=='9fd220aa2e8f336629edb1545cd172a5229b6c73d57e3f900e91e17785e8aad8'
            ),name
            pe=pefile.PE(data=data);pe.relocate_image(base)
            self.u.mem_map(base,(pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
            self.u.mem_write(base,pe.get_memory_mapped_image())
            for dll in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in dll.imports:
                    at=END+0x100+len(self.apis)*4
                    assert at<END+0xe00
                    self.apis[at]=imp.name.decode() if imp.name else str(imp.ordinal)
                    self.put(imp.address,at)
        self.u.hook_add(UC_HOOK_BLOCK,self.hook)
    def rd(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
    def put(self,a,v):self.u.mem_write(a,struct.pack('<I',v))
    def ret(self,value=0,pop=0):
        sp=self.u.reg_read(UC_X86_REG_ESP)
        self.u.reg_write(UC_X86_REG_EAX,value);self.u.reg_write(UC_X86_REG_EIP,self.rd(sp));self.u.reg_write(UC_X86_REG_ESP,sp+4+pop)
    def hook(self,uc,a,n,_):
        sp=self.u.reg_read(UC_X86_REG_ESP)
        if a in self.apis:
            name=self.apis[a]
            if name=='SetRect':self.u.mem_write(self.rd(sp+4),bytes(self.u.mem_read(sp+8,16)));self.ret(1,20)
            elif name=='HeapFree':self.ret(1,12) # Isolated case owns the entire emulated heap.
            else:raise AssertionError('Unsupported API: '+name)
        elif a==0x49bc10:
            size=self.rd(sp+4);p=self.heap;self.heap+=(size+31)&~15
            assert self.heap<0x4f00000;self.ret(p)
        elif a==0x43f290:
            obj=self.rd(sp+4);w,h,pitch=struct.unpack('<HHH',self.u.mem_read(obj+0x1a,6))
            assert self.u.mem_read(obj+0x20,1)==b'\x20'
            pixels=bytes(self.u.mem_read(self.rd(obj+4),pitch*h))
            self.uploads.append(Image.frombytes('RGBA',(w,h),pixels,'raw','BGRA',pitch))
            self.ret(1)
        elif a==0x47a9b0:
            self.draws.append(bytes(self.u.mem_read(self.rd(sp+4),52)));self.ret(1,8)
        elif a in (0x43d360,0x43d370):raise AssertionError('Engine error at '+hex(a))
        elif not (0x401000<=a<0x4aa000 or 0x18001000<=a<0x18005000):raise AssertionError('Unsupported code '+hex(a))
    def run(self,start,end=END):
        self.u.emu_start(start,end,count=100000000)
        assert self.u.reg_read(UC_X86_REG_EIP)==end,'Instruction limit reached'
    def call(self,address,args=(),this=0):
        self.u.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),END,*args))
        self.u.reg_write(UC_X86_REG_ESP,STACK);self.u.reg_write(UC_X86_REG_ECX,this);self.run(address)
    def load(self,tim):
        self.u.mem_write(0x2100000,tim);self.call(0x4983f0,this=SLOT)
        self.call(0x43f700,(0x2100000,31,0,1));assert len(self.uploads)==1
        return self.uploads[0]
    def sprite(self,width,height,v=0):
        d=0x2200000;self.u.mem_write(d,bytes(32))
        self.u.mem_write(d+4,struct.pack('<hhhhHBBHH',-126,64,width,height,31,0,v,0,480))
        self.u.mem_write(0x4aa360,struct.pack('<hh',160,120));self.call(0x441120,(d,2))
        assert len(self.draws)==1
        return struct.unpack('<8h',self.draws[0][8:24])
    def allocation(self,w,h):
        d=0x2201000;self.put(d+8,h);self.put(d+12,w)
        self.u.reg_write(UC_X86_REG_ESI,d);self.run(0x472b0a,0x472b64)
        native=(self.u.reg_read(UC_X86_REG_EAX),self.u.reg_read(UC_X86_REG_EDX))
        self.u.reg_write(UC_X86_REG_ESP,STACK);self.run(0x18003de0,0x18003df5)
        physical=(self.u.reg_read(UC_X86_REG_EAX),self.u.reg_read(UC_X86_REG_EDX))
        # RE:Enhance's texture normalization hook, before image replacement lookup.
        frame=0x2202000;wp=0x2202100;hp=wp+4
        self.put(wp,physical[0]);self.put(hp,physical[1])
        for off,val in [(12,2),(16,hp),(20,wp)]:self.put(frame+off,val)
        self.u.reg_write(UC_X86_REG_EBP,frame);self.run(0x18003493,0x180034a7)
        logical=(self.rd(wp),self.rd(hp));assert logical==native
        return native,physical,logical
    def u_end(self,command_width,logical_width):
        d=0x2203000;vertex=0x2203100
        self.u.mem_write(d+20,struct.pack('<h',command_width-1))
        self.u.mem_write(STACK+0x5c,struct.pack('<f',1/logical_width))
        self.u.reg_write(UC_X86_REG_ESP,STACK);self.u.reg_write(UC_X86_REG_EDX,d)
        self.u.reg_write(UC_X86_REG_ECX,vertex);self.u.reg_write(UC_X86_REG_EBP,0x2203200)
        self.run(0x481b8b,0x481ba5)
        return struct.unpack('<f',self.u.mem_read(vertex+0x38,4))[0]
