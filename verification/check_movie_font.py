"""Execute the real 1.1.4 FreeType caller through the configurable font hook."""
import struct,subprocess,sys,tempfile
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EBP,UC_X86_REG_ECX,UC_X86_REG_EAX
from check_markers import Markers,ROOT,STACK
class Fonts(Markers):
    def __init__(self,dll):
        self.profile=None;self.available=set();self.attempts=[];self.windows='C:\\Windows'
        super().__init__(dll)
    def hook(self,u,a,n,data):
        sp=u.reg_read(UC_X86_REG_ESP)
        if a==0x100f6750:
            library,path,index,face=[self.rd(sp+k) for k in (4,8,12,16)]
            assert library==0x123456 and face==0x220403c
            path=self.cstr(path);self.attempts.append((path,index))
            if path in self.available:self.put(face,0x12345678)
            self.ret(0 if path in self.available else 1)
        elif a==self.exports['verify_snprintf']:
            dst,size,fmt=self.rd(sp+4),self.rd(sp+8),self.cstr(self.rd(sp+12))
            args=tuple(self.cstr(self.rd(sp+16+4*i)) for i in range(fmt.count('%s')))
            out=(fmt%args).encode();assert len(out)<size
            u.mem_write(dst,out+b'\0');self.ret(len(out))
        elif a in self.apis and self.apis[a]=='GetPrivateProfileStringA':
            section,key,default,dst,size,file=[self.rd(sp+k) for k in (4,8,12,16,20,24)]
            assert (self.cstr(section),self.cstr(key),self.cstr(file))==('MovieSubtitles','Fonts','.\\korean_subtitle.ini')
            value=self.cstr(default) if self.profile is None else self.profile
            out=value.encode()[:size-1];u.mem_write(dst,out+b'\0');self.ret(len(out),24)
        elif a in self.apis and self.apis[a]=='GetWindowsDirectoryA':
            dst,size=self.rd(sp+4),self.rd(sp+8);out=self.windows.encode()
            assert len(out)<size;u.mem_write(dst,out+b'\0');self.ret(len(out),8)
        elif a in self.apis and self.apis[a] in ('strlen','strcmp'):
            left=self.cstr(self.rd(sp+4))
            self.ret(len(left) if self.apis[a]=='strlen' else int(left!=self.cstr(self.rd(sp+8))))
        else:super().hook(u,a,n,data)
    def load(self,name='segoeuib.ttf',index=0):
        self.attempts=[];self.put(0x2204038,0x123456);self.put(0x220403c,0)
        ebp=0x2206000;self.put(ebp-0x24,15);self.put(ebp-0x1c,0x2204000)
        assert len(name)<16;self.u.mem_write(ebp-0x38,name.encode()+b'\0')
        self.u.reg_write(UC_X86_REG_EBP,ebp);self.u.reg_write(UC_X86_REG_ECX,0x2204000)
        self.u.reg_write(UC_X86_REG_ESP,STACK)
        # Original caller pushes face, index=0, path and library, then CALLs the hook.
        self.run(0x10086beb,0x10086c08)
        assert self.u.reg_read(UC_X86_REG_ESP)==STACK-16,'cdecl stack changed'
        return self.u.reg_read(UC_X86_REG_EAX)
def main():
    with tempfile.TemporaryDirectory() as tmp:
        dll=Path(tmp)/'fonts.dll'
        subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-I',str(ROOT/'src'),'-o',str(dll),str(ROOT/'verification/renderer_shim.c')],check=True)
        e=Fonts(dll);at=0x10086c03
        assert bytes(e.u.mem_read(at,1))==b'\xe8'
        assert at+5+struct.unpack('<i',e.u.mem_read(at+1,4))[0]==0x100f6750
        e.call(e.exports['verify_movie_font']);wrapper=e.u.reg_read(UC_X86_REG_EAX)
        e.put(at+1,(wrapper-at-5)&0xffffffff)
        e.available={'C:\\Windows\\Fonts\\batang.ttc'}
        assert e.load()==0 and e.attempts==[('C:\\Windows\\Fonts\\batang.ttc',0)]
        e.profile=' missing.ttf ; ; fonts\\custom.otf ; batang.ttc '
        e.available={'fonts\\custom.otf'}
        assert e.load()==0 and e.attempts==[('C:\\Windows\\Fonts\\missing.ttf',0),('fonts\\custom.otf',0)]
        assert e.rd(0x220403c)==0x12345678
        e.profile='broken.ttf';e.available={'segoeuib.ttf'}
        assert e.load()==0 and e.attempts==[('C:\\Windows\\Fonts\\broken.ttf',0),('segoeuib.ttf',0)]
        e.profile='';e.available=set()
        assert e.load()!=0 and e.attempts==[('segoeuib.ttf',0)]
        e.profile='x'*2048
        assert e.load()!=0 and e.attempts==[('segoeuib.ttf',0)]
        e.profile='batang.ttc';e.available={'arial.ttf'}
        assert e.load('arial.ttf')==0 and e.attempts==[('arial.ttf',0)]
    print('PASS: native call/ABI, Batang default, ordered custom files, blanks, failed/truncated list fallback and unchanged native retries')
if __name__=='__main__':main()
