"""Execute production C marker renderer plus actual REbirth post-hook advance code."""
import hashlib,json,struct,subprocess,sys,tempfile
from pathlib import Path
import re
from PIL import Image,ImageFont
import pefile
from unicorn.x86_const import *
from verify_renderer import Engine,ROOT,GAME,OUT,END,STACK,SLOT
from build_paths import FONT
DDHASH='144764bf113d0f19767a9f2e35927b30ccfbb978790a427189583544b6c52889'
class Markers(Engine):
    def module(self,path,base):
        p=pefile.PE(str(path));p.relocate_image(base)
        self.u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);self.u.mem_write(base,p.get_memory_mapped_image())
        for dll in p.DIRECTORY_ENTRY_IMPORT:
            for imp in dll.imports:
                at=END+0x100+len(self.apis)*4;assert at<END+0xe00
                self.apis[at]=imp.name.decode() if imp.name else str(imp.ordinal);self.put(imp.address,at)
        return {s.name.decode():base+s.address for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
    def __init__(self,dll):
        self.exports={};super().__init__()
        assert hashlib.sha256((GAME/'ddraw.dll').read_bytes()).hexdigest()==DDHASH
        self.module(GAME/'ddraw.dll',0x10000000);self.exports=self.module(dll,0x14000000)
        obj=0x2201000;vtable=0x2201100;mod_list=0x2201200
        self.put(obj,vtable);self.put(vtable+12,END+0xe00);self.put(mod_list,obj);self.put(0x1229e290,mod_list);self.put(0x1229e294,mod_list+32)
        self.call(self.exports['verify_init'],(0x10000000,3));self.call(0x4983f0,this=SLOT)
        self.u.mem_write(0x4aa360,struct.pack('<hh',160,120))
    def cstr(self,a):
        out=bytearray()
        while (v:=bytes(self.u.mem_read(a,1)))!=b'\0':out+=v;a+=1;assert len(out)<4096
        return out.decode()
    def hook(self,uc,a,n,_):
        sp=self.u.reg_read(UC_X86_REG_ESP)
        if a==self.exports.get('verify_snprintf'):
            dst,size,fmt=self.rd(sp+4),self.rd(sp+8),self.cstr(self.rd(sp+12))
            if fmt.startswith(('sentences/','sentences-sd/')):out=(fmt%(self.rd(sp+16),self.rd(sp+20))).encode()
            else:out=b'' # Diagnostics are not game text.
            assert len(out)<size;self.u.mem_write(dst,out+b'\0');self.ret(len(out))
        elif a==END+0xe00:
            path=self.cstr(self.rd(sp+4));assert path.startswith(('sentences/','sentences-sd/')) and '..' not in path
            data=(ROOT/'build/mod_korean_serif'/path).read_bytes();address=self.heap;self.heap+=(len(data)+31)&~15
            self.u.mem_write(address,data);self.put(self.rd(sp+8),len(data));self.ret(address,8)
        elif a==0x100f1d99:self.ret()
        elif a in self.apis and self.apis[a]=='fopen':self.ret(0)
        elif 0x10000000<=a<0x12500000 or 0x14000000<=a<0x14100000:pass
        else:super().hook(uc,a,n,_)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cases=[]
    fragments=json.loads((ROOT/'build/sentence-map.json').read_text(encoding='utf-8'))
    sid=fragments['엄청난 저택이군.']
    records=[tuple(map(int,m.split(','))) for m in re.findall(r'\{([0-9,]+)\}',(ROOT/'build/sentence_records.h').read_text(encoding='utf-8'))]
    expected_advance=records[sid][2]
    marker=bytes([0xa4]+[0xa5+((sid>>shift)&15) for shift in (12,8,4,0)])
    with tempfile.TemporaryDirectory() as tmp:
        dll=Path(tmp)/'renderer.dll'
        subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-I',str(ROOT/'src'),'-o',str(dll),str(ROOT/'verification/renderer_shim.c')],check=True)
        # Execute the actual 1.1.4 reader and its RET 8, not a reader-level mock.
        wrong_source=Path(tmp)/'wrong-reader.c'
        source=(ROOT/'src/korean_subtitle.c').read_text(encoding='utf-8')
        signature='(__stdcall *)(const char *,unsigned *)'
        assert source.count(signature)==1
        wrong_source.write_text(source.replace(signature,'(__cdecl *)(const char *,unsigned *)'),encoding='utf-8')
        wrong_shim=Path(tmp)/'wrong-shim.c'
        wrong_shim.write_text((ROOT/'verification/renderer_shim.c').read_text(encoding='utf-8').replace('#include "../src/korean_subtitle.c"',f'#include "{wrong_source}"'))
        wrong_dll=Path(tmp)/'wrong.dll'
        subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'src'),'-I',str(ROOT/'build'),'-o',str(wrong_dll),str(wrong_shim)],check=True)
        for candidate,label in [(dll,'file-reader-stdcall'),(wrong_dll,'wrong-cdecl-regression')]:
            e=Markers(candidate);path=0x2202000;size=0x2202100
            e.u.mem_write(path,f'sentences/{sid:05d}-00.tim'.encode()+b'\0')
            e.call(e.exports['verify_read_file'],(path,size))
            stack_delta=e.u.reg_read(UC_X86_REG_ESP)-STACK
            assert e.u.reg_read(UC_X86_REG_EAX)!=0 and e.rd(size)==records[sid][3]
            assert (stack_delta==4)==(candidate==dll),(label,stack_delta)
            cases.append({'case':label,'cdecl_wrapper_stack_delta':stack_delta,'expected_delta':4,
                          'known_failure_reproduced':candidate==wrong_dll,'pass':True})
        for caller,tail,end in [('message',0x10061654,0x10061662),('insert',0x100613d7,0x100613ed)]:
            e=Markers(dll)
            direct_argument='-dev_korean_serif'
            e.call(e.exports['verify_'+caller]);wrapper=e.u.reg_read(UC_X86_REG_EAX)
            d=0xc30030;raw=0x2202000
            e.u.mem_write(d,bytes(32));e.u.mem_write(d+4,struct.pack('<hhhhHBBHH',-126,64,14,14,30,0,0,0,480))
            e.u.mem_write(raw,marker)
            advances=[];positions=[]
            for i in range(5):
                e.u.reg_write(UC_X86_REG_ESI,raw+i+(caller=='insert'))
                e.call(wrapper,(d,2));advances.append(e.rd(e.exports['ko_advance']))
                e.run(tail,end);positions.append(struct.unpack('<h',e.u.mem_read(d+4,2))[0])
            assert advances==[expected_advance,0,0,0,0],advances
            assert len(e.draws)==len(e.uploads)==(records[sid][0]+63)//64*((records[sid][1]+63)//64)
            for command in e.draws:
                x0,y0,x1,y1,u0,v0,u1,v1=struct.unpack("<8H",command[8:24])
                assert (u1+1,v1+1)==((x1-x0+1)*4,(y1-y0+1)*4)
                assert u0==v0==0 and u1<256 and v1<256
            assert positions==[-126+expected_advance]*5,positions
            cases.append({'caller':caller,'advances':advances,'final_x_per_byte':positions,'draw_calls':len(e.draws),'pass':True})
        # Reproduce an item-name continuation starting far to the right. A leading
        # newline must return to the message margin, including a negative advance.
        newline=next(k for k in fragments if k.startswith(r'\n가져가시겠습니까?'))
        for text,label,start_x in [(newline,'item-newline',110),
                                  (max(fragments,key=lambda k:records[fragments[k]][1]),'multiline',-126)]:
            e=Markers(dll);sid=fragments[text];w,h,last,size,reset,line_height=records[sid]
            raw=0x2202000;d=0xc30030
            e.u.mem_write(raw,bytes([0xa4]+[0xa5+((sid>>shift)&15) for shift in (12,8,4,0)]))
            e.u.mem_write(d,bytes(32));e.u.mem_write(d+4,struct.pack('<hhhhHBBHH',start_x,40,14,14,30,0,0,0,480))
            e.u.reg_write(UC_X86_REG_ESI,raw)
            e.call(e.exports['verify_message']);wrapper=e.u.reg_read(UC_X86_REG_EAX)
            e.call(wrapper,(d,2));e.run(0x10061654,0x10061662)
            advance=struct.unpack('<i',e.u.mem_read(e.exports['ko_advance'],4))[0]
            if reset:assert advance==-126-start_x+last and advance<0
            assert struct.unpack('<h',e.u.mem_read(d+4,2))[0]==start_x+advance
            # Actual production calls must cover the rectangle exactly once, with
            # four distinct source texels per logical pixel and no wrapping.
            bounds=[struct.unpack('<8h',c[8:24]) for c in e.draws]
            left=min(c[0] for c in bounds);top=min(c[1] for c in bounds)
            coverage=Image.new('L',(w,h));composite=Image.new('RGB',(w*4,h*4))
            assert len(e.uploads)==len(bounds)
            for c,im in zip(bounds,e.uploads):
                x0,y0,x1,y1,u0,v0,u1,v1=c;tw=x1-x0+1;th=y1-y0+1
                assert u0==v0==0 and u1+1==tw*4 and v1+1==th*4 and u1<256 and v1<256
                assert im.size==(256,256)
                assert coverage.crop((x0-left,y0-top,x1-left+1,y1-top+1)).getbbox() is None
                coverage.paste(255,(x0-left,y0-top,x1-left+1,y1-top+1))
                composite.paste(im.crop((0,0,u1+1,v1+1)).convert('RGB'),((x0-left)*4,(y0-top)*4))
            assert coverage.getextrema()==(255,255)
            assert e.allocation(256,256)[2]==(256,256)
            composite.save(OUT/(label+'-current.png'))
            cases.append({'case':label,'advance':advance,'draw_calls':len(bounds),'coverage':'exactly once','pass':True})
        e=Markers(dll)
        # Apply the actual 1.1.4 start-x patch, then execute the game's choice caller.
        image=pefile.PE(str(GAME/'ddraw.dll')).get_memory_mapped_image()
        assert image[0x62955:0x6295f]==bytes.fromhex('c705271e4900d8000000')
        e.u.mem_write(0x491e27,image[0x6295b:0x6295f])
        e.u.mem_write(0x491e33,b'\xc3') # Return after the actual call/stack cleanup.
        e.u.reg_write(UC_X86_REG_EAX,202)
        e.call(0x491e1d)
        choices=[struct.unpack('<8h',c[8:24]) for c in e.draws]
        assert len(choices)==2 and [c[0] for c in choices]==[216,256]
        assert all(c[1]==218 and c[3]<236 for c in choices)
        assert choices[0][2]<244 and choices[1][2]<312
        cases.append({'case':'yes-no','xy_uv':choices,'pass':True})
    coverage=json.loads((ROOT/'build/mod_korean_serif/coverage.json').read_text(encoding='utf-8'))
    font=ImageFont.truetype(str(FONT),coverage['font_size'],layout_engine=ImageFont.Layout.BASIC)
    widths={s:font.getlength(s)/coverage['render_scale'] for s in ['엄청난 저택이군.']}
    assert widths['엄청난 저택이군.']<=236
    report={'direct_mod_argument':direct_argument,'text_widths_logical_pixels':widths,'ddraw_sha256' :DDHASH,'renderer_source_sha256':hashlib.sha256((ROOT/'src/korean_subtitle.c').read_bytes()).hexdigest(),'cases':cases}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'markers.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
