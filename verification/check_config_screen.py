"""Exercise REbirth 1.1.4's actual target-switch row and Exit lookup."""
import json,struct,sys,subprocess,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_EBP,UC_X86_REG_EDI,UC_X86_REG_ESI,UC_X86_REG_ESP
from check_markers import Markers
from verify_renderer import ROOT,STACK

def main():
    original=json.loads((ROOT/'translation/resource_layout.json').read_text(encoding='utf-8'))['config.xml']['entries'];built=ET.parse(ROOT/'build/mod_korean_serif/config.xml').getroot()
    assert len(original)==len(built)==14
    assert [original[i] for i in (10,11,12,13)]==['Change Target','Exit','Confirm changes','Leave']
    mapping=sorted((ord(e.attrib['Char']),int(e.attrib['Encode'],0)) for e in ET.parse(ROOT/'build/mod_korean_serif/encoding.xml').getroot())
    with tempfile.TemporaryDirectory() as tmp:
        dll=Path(tmp)/'config-check.dll';subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-I',str(ROOT/'src'),'-o',str(dll),str(ROOT/'verification/renderer_shim.c')],check=True)
        for kind,expected in [('target',10),('exit',11)]:
            e=Markers(dll);table=0x2204000;utf8=0x2206000;raw=0x2207000
            e.u.mem_write(table,b''.join(struct.pack('<HHI',c,0,k) for c,k in mapping));e.put(0x1229e0c0,table);e.put(0x1229e0c4,table+8*len(mapping));e.put(0x1229e0cc,0x1b)
            data=bytearray();offsets=[]
            for entry in built:
                e.u.mem_write(utf8,entry.text.encode()+b'\0');e.u.reg_write(UC_X86_REG_EDX,raw);e.call(0x1004d2f0,(0,),this=utf8)
                code=bytes(e.u.mem_read(raw,e.u.reg_read(UC_X86_REG_EAX)));offsets.append(len(data));data+=code
            e.u.mem_write(0x2209000,bytes(data));e.u.mem_write(0x220a000,struct.pack('<14H',*offsets));e.put(0x1229e36c,0x2209000);e.put(0x1229e37c,0x220a000)
            e.u.mem_write(0x2208000,bytes([0,8])*238);e.put(0x1229e284,0x2208000);e.put(0x1229e288,0x2208000+476)
            e.u.reg_write(UC_X86_REG_EBP,0x220b100);e.u.reg_write(UC_X86_REG_ESP,STACK);e.put(0x220b100-24,123);e.put(0x220b100-8,0)
            if kind=='target':
                e.u.reg_write(UC_X86_REG_EDI,30);assert e.u.mem_read(0x103b97a0+30,1)==b'\x0a';e.run(0x1006b6b8,0x1006b6d5)
                callsite,end=0x1006b6d5,0x1006b6da
            else:
                e.u.reg_write(UC_X86_REG_ESI,0x220b200);e.u.reg_write(UC_X86_REG_EAX,0x220a000);e.run(0x1006b72f,0x1006b750)
                callsite,end=0x1006b750,0x1006b755
            sp=e.u.reg_read(UC_X86_REG_ESP)
            assert e.rd(sp+12)==0x2209000+offsets[expected],(kind,hex(e.rd(sp+12)),hex(0x2209000+offsets[expected]))
            e.run(callsite,end)
            assert e.draws and e.uploads
            sid=0
            for c in data[offsets[expected]+1:offsets[expected]+5]:sid=sid*16+c-0xa5
            sentences=json.loads((ROOT/'build/sentence-map.json').read_text(encoding='utf-8'))
            assert sid==sentences['조준 대상 변경' if kind=='target' else '나가기']
    print('PASS: actual 1.1.4 config lookup/draw selects Change Target (10) and Exit (11)')

if __name__=='__main__':main()
