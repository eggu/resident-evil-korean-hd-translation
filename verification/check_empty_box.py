"""Run the original item-box empty/occupied branch with our guarded label hook."""
import json,struct,subprocess,sys,tempfile
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ESI,UC_X86_REG_EBX,UC_X86_REG_EAX
from check_markers import Markers,ROOT,STACK
class Box(Markers):
    def __init__(self,dll):self.native=[];super().__init__(dll)
    def hook(self,u,a,n,data):
        if a in (0x4912c0,0x491830):
            sp=u.reg_read(UC_X86_REG_ESP);self.native.append((a,[self.rd(sp+k) for k in (4,8,12,16)]));self.ret(7)
        else:super().hook(u,a,n,data)
def main():
    with tempfile.TemporaryDirectory() as tmp:
        dll=Path(tmp)/'box.dll'
        subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-I',str(ROOT/'src'),'-o',str(dll),str(ROOT/'verification/renderer_shim.c')],check=True)
        e=Box(dll)
        assert bytes(e.u.mem_read(0x4b3a88,10))==b'_Nothing_\0'
        assert bytes(e.u.mem_read(0x44aa3c,1))==b'\xe8'
        assert 0x44aa41+struct.unpack('<i',e.u.mem_read(0x44aa3d,4))[0]==0x491830
        e.call(e.exports['verify_empty_box']);wrapper=e.u.reg_read(UC_X86_REG_EAX)
        e.put(0x44aa3d,(wrapper-0x44aa41)&0xffffffff)
        for sd,item in [(0,0),(1,0),(0,3)]:
            e.call(e.exports['verify_subtitle_mode'],(sd,))
            e.draws.clear();e.native.clear()
            e.u.mem_write(0xc387b4,bytes([item,0]));e.u.mem_write(STACK+0x12,b'\x01')
            e.u.reg_write(UC_X86_REG_EBX,0);e.u.reg_write(UC_X86_REG_ESI,35);e.u.reg_write(UC_X86_REG_ESP,STACK)
            e.run(0x44aa09,0x44aa59)
            assert e.u.reg_read(UC_X86_REG_ESP)==STACK
            if item:
                assert not e.draws and e.native==[(0x4912c0,[3,128,42,35])],e.native
            else:
                assert not e.native and not e.draws
    assert '빈 칸' not in json.loads((ROOT/'build/sentence-map.json').read_text(encoding='utf-8'))
    print('PASS: real item-box empty branch draws nothing in HD/SD; occupied items and caller stack preserved')
if __name__=='__main__':main()
