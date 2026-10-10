"""Run production config selection, tile loading and native drawing in both modes."""
import json,re,struct,subprocess,sys,tempfile
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX
from check_markers import Markers,ROOT,END
class Modes(Markers):
    def __init__(self,dll):
        self.profile={};self.files=[]
        super().__init__(dll)
    def hook(self,u,a,n,data):
        if a in self.apis and self.apis[a]=='GetPrivateProfileIntA':
            sp=u.reg_read(UC_X86_REG_ESP)
            assert self.cstr(self.rd(sp+4))=='DLL'
            assert self.cstr(self.rd(sp+16))=='.\\config.ini'
            key=self.cstr(self.rd(sp+8));assert key in ('HDLoader','LowResEnable')
            self.ret(self.profile.get(key,self.rd(sp+12)),16)
        else:
            if a==END+0xe00:self.files.append(self.cstr(self.rd(u.reg_read(UC_X86_REG_ESP)+4)))
            super().hook(u,a,n,data)
def main():
    records=[tuple(map(int,m.split(','))) for m in re.findall(r'\{([0-9,]+)\}',(ROOT/'build/sentence_records.h').read_text(encoding='utf-8'))]
    for sid,(width,height,last,size,newline,line_height) in enumerate(records):
        for tile in range(((width+63)//64)*((height+63)//64)):
            path=f'{sid:05d}-{tile:02d}.tim'
            hd=(ROOT/'build/mod_korean_translation/sentences'/path).read_bytes()
            sd=(ROOT/'build/mod_korean_translation/sentences-sd'/path).read_bytes()
            assert len(sd)==len(hd)==size and sd[:8]==hd[:8]
            start=8+struct.unpack_from('<I',sd,8)[0]+12
            pixels=sd[start:];assert len(pixels)==32768
            assert not any(pixels[64*128:]),'SD ink exceeds one logical tile vertically'
            assert all(not any(pixels[y*128+32:(y+1)*128]) for y in range(64)),'SD ink exceeds one logical tile horizontally'
    with tempfile.TemporaryDirectory() as tmp:
        dll=Path(tmp)/'modes.dll'
        subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-I',str(ROOT/'src'),'-o',str(dll),str(ROOT/'verification/renderer_shim.c')],check=True)
        e=Modes(dll)
        for profile,want in [({},1),({'HDLoader':0,'LowResEnable':0},1),({'HDLoader':1,'LowResEnable':0},0),({'HDLoader':1,'LowResEnable':1},1),({'HDLoader':0,'LowResEnable':1},1)]:
            e.profile=profile;e.call(e.exports['verify_configure_subtitles'])
            assert e.u.reg_read(UC_X86_REG_EAX)==want,(profile,want)
        fragments=json.loads((ROOT/'build/sentence-map.json').read_text(encoding='utf-8'));sid=fragments['엄청난 저택이군.']
        raw=0x2202000;d=0xc30030
        e.u.mem_write(raw,bytes([0xa4]+[0xa5+((sid>>s)&15) for s in (12,8,4,0)]))
        positions=[]
        for sd in (0,1,0):
            e.profile={'HDLoader':1,'LowResEnable':sd};e.call(e.exports['verify_configure_subtitles'])
            e.draws.clear();e.uploads.clear();e.files.clear()
            e.u.mem_write(d,bytes(32));e.u.mem_write(d+4,struct.pack('<hhhhHBBHH',-126,64,14,14,30,0,0,0,480))
            e.call(e.exports['ko_draw'],(d,2,raw))
            assert e.draws
            bounds=[struct.unpack('<8H',c[8:24]) for c in e.draws];positions.append([b[:4] for b in bounds])
            scale=1 if sd else 4
            for x,y,xx,yy,u,v,uu,vv in bounds:assert uu+1==(xx-x+1)*scale and vv+1==(yy-y+1)*scale
            if len(positions)<3:
                assert e.files and all(p.startswith('sentences-sd/' if sd else 'sentences/') for p in e.files)
                assert len(e.uploads)==len(bounds)
            else:assert not e.uploads and not e.files,'HD cache reused SD tile'
        assert positions[0]==positions[1]==positions[2],'Mode changed text layout'
    print('PASS: config/default selection, HD/SD assets and UV scales, same layout, mode-specific cache reuse')
if __name__=='__main__':main()
