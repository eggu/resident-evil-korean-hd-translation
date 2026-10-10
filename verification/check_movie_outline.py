"""Execute native movie-style defaults and the actual caller through our wrapper."""
import struct,subprocess,sys,tempfile
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_ECX
from check_markers import Markers,ROOT,STACK
class Movie(Markers):
    def hook(self,u,a,n,data):
        if a==0x10087670:
            sp=u.reg_read(UC_X86_REG_ESP)
            assert u.reg_read(UC_X86_REG_ECX)==0x1229e8a0
            assert [self.rd(sp+k) for k in (4,8,12)]==[0x2206000-0x3c,320,240]
            self.ret(0x1357,12)
        else:super().hook(u,a,n,data)
def main():
    with tempfile.TemporaryDirectory() as tmp:
        dll=Path(tmp)/'movie.dll'
        subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-I',str(ROOT/'src'),'-o',str(dll),str(ROOT/'verification/renderer_shim.c')],check=True)
        e=Movie(dll);owner=0x1229e8a0
        assert bytes(e.u.mem_read(0x100861b9,1))==b'\xe8'
        assert 0x100861be+struct.unpack('<i',e.u.mem_read(0x100861ba,4))[0]==0x10087670
        e.call(e.exports['verify_movie_update']);wrapper=e.u.reg_read(UC_X86_REG_EAX)
        e.put(0x100861ba,(wrapper-0x100861be)&0xffffffff)
        for outline,radius,want in [(0xff000000,2,0),(0,2,0x80000000),(0xff000000,0,0x80000000)]:
            e.u.mem_write(owner,bytes(0xe8));e.u.reg_write(UC_X86_REG_ESI,owner)
            e.run(0x10081c51,0x10081cb2)
            assert [e.rd(owner+k) for k in (0xc0,0xc4,0xc8,0xcc)]==[0xffffffff,0xff000000,0x80000000,2]
            e.put(owner+0xc4,outline);e.put(owner+0xcc,radius)
            before=bytearray(e.u.mem_read(owner,0xe8))
            ebp=0x2206000;e.put(ebp-0x18,320);e.put(ebp-0x14,240)
            e.u.reg_write(UC_X86_REG_EBP,ebp);e.u.reg_write(UC_X86_REG_ESP,STACK)
            e.run(0x100861aa,0x100861be)
            before[0xc8:0xcc]=struct.pack('<I',want)
            assert bytes(e.u.mem_read(owner,0xe8))==before,'Changed another style field'
            assert e.u.reg_read(UC_X86_REG_ESP)==STACK and e.u.reg_read(UC_X86_REG_EAX)==0x1357
    print('PASS: real movie caller/ABI; background transparent only with visible outline; all other style fields preserved')
if __name__=='__main__':main()
