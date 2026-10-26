"""Generate the current Korean HD/SD subtitle resources and renderer DLL."""
from pathlib import Path
import argparse, hashlib, json, math, re, shutil, struct, subprocess, sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from build_resources import build_documents
from build_paths import ROOT, GAME, FONT

def wrap(text,font,width):
    result=[]
    for paragraph in re.split(r'\\+n',text):
        line=''
        for ch in paragraph:
            if line and font.getlength(line+ch)>width:
                # Prefer whitespace, falling back to a syllable boundary for long Korean words.
                cut=line.rfind(' ')
                if cut>len(line)//2:
                    result.append(line[:cut]); line=line[cut+1:]+ch
                else: result.append(line); line=ch
            else: line+=ch
        result.append(line)
    assert all(font.getlength(s)<=width for s in result)
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font-size',type=int,default=44)
    ap.add_argument('--render-scale',type=int,choices=(1,2,4),default=4)
    args=ap.parse_args()
    if not 12<=args.font_size<=96 or args.font_size%args.render_scale: ap.error('font size must be 12..96 and divisible by render scale')
    scale=args.render_scale; logical_size=args.font_size//scale; texwidth=256*scale
    subprocess.run([sys.executable,str(ROOT/'build_full_text.py'),'--no-wrap','--no-index'],check=True)
    source=ROOT/'build/full-text-renderer'; out=ROOT/'build/mod_korean_translation'
    (out/'sentences').mkdir(parents=True,exist_ok=True)
    (out/'sentences-sd').mkdir(parents=True,exist_ok=True)
    opening=ET.parse(source/'text/ROOM_106_0.xml').getroot()
    preview_texts={part for entry in list(opening)[11:19] for part in re.split(r'\{[^}]+\}',entry.text or '') if part.strip()}
    font=ImageFont.truetype(str(FONT),args.font_size,layout_engine=ImageFont.Layout.BASIC); step=args.font_size+3*scale
    original=(GAME/'jpn/Data/PBFONT1.TIM').read_bytes()
    expected=json.loads((ROOT/'input_hashes.json').read_text(encoding='utf-8'))['jpn/Data/PBFONT1.TIM']
    assert hashlib.sha256(original).hexdigest()==expected
    block=8+struct.unpack_from('<I',original,8)[0]
    header=original[:block]
    fragments={}; records=[]; preview=[]; counts={'entries':0,'room_entries':0,'common_entries':0,'resource_entries':0,'save_menu_entries':0}; tile_count=0
    menu_font=ImageFont.truetype(str(FONT),11*scale,layout_engine=ImageFont.Layout.BASIC)
    def encode(match,save_menu=False):
        nonlocal tile_count
        text=match.group(0)
        if not text.strip(): return text
        key='save2.xml:'+text if save_menu else text
        draw_font=menu_font if save_menu else font
        line_step=14*scale if save_menu else step
        if key not in fragments:
            sid=len(records); assert sid<65536
            fragments[key]=sid
            lines=wrap(text,draw_font,236*scale)
            height=len(lines)*line_step; assert height<=220*scale,(height,text)
            ink=Image.new('L',(texwidth,height)); draw=ImageDraw.Draw(ink)
            for row,line in enumerate(lines):
                x=2.0*scale
                baseline=12*scale-max((draw_font.getbbox(c,anchor='ls')[3] for c in line if not c.isspace()),default=0) if save_menu else 2*scale+draw_font.getmetrics()[0]
                for char in line:
                    # AppleMyungjo's embedded space bitmap is malformed in FreeType;
                    # whitespace advances the pen without painting a glyph.
                    if not char.isspace():
                        pos=(round(x),baseline+row*line_step)
                        box=draw.textbbox(pos,char,font=draw_font,anchor='ls')
                        assert box[2]<=240*scale and box[1]>=row*line_step and box[3]<=(row+1)*line_step,(box,char,line)
                        draw.text(pos,char,font=draw_font,anchor='ls',fill=255)
                    x+=draw_font.getlength(char)
            border=ink.point(lambda v:255 if v>=24 else 0).filter(ImageFilter.MaxFilter(2*scale+1))
            width=min(240,max(1,math.ceil(max(map(draw_font.getlength,lines))/scale)+4))
            last=min(240,max(1,math.ceil(draw_font.getlength(lines[-1])/scale)+4))
            height//=scale
            # Keep the high-resolution raster. Native textures remain safe 256px squares;
            # each tile is displayed at 256/scale logical pixels by the GPU.
            tile_size=256//scale; cols=math.ceil(width/tile_size); rows=math.ceil(height/tile_size)
            assert cols*rows<=16
            for row in range(rows):
                for col in range(cols):
                    box=(col*256,row*256,(col+1)*256,(row+1)*256)
                    glyph=ink.crop(box); edge=border.crop(box)
                    indices=Image.new('L',(256,256))
                    indices.paste(8,mask=edge.point(lambda v:255 if v>=64 else 0))
                    shades=glyph.point(lambda v:max(1,7-round(v*6/255)))
                    indices.paste(shades,mask=glyph.point(lambda v:255 if v>=24 else 0))
                    values=indices.tobytes()
                    pixels=bytes(a|(b<<4) for a,b in zip(values[::2],values[1::2]))
                    tim=header+struct.pack('<IHHHH',12+len(pixels),0,0,64,256)+pixels
                    (out/'sentences'/f'{sid:05d}-{row*cols+col:02d}.tim').write_bytes(tim)
                    sd_glyph=glyph.resize((256//scale,256//scale),Image.Resampling.LANCZOS)
                    sd_edge=sd_glyph.point(lambda v:255 if v>=24 else 0).filter(ImageFilter.MaxFilter(3))
                    sd_indices=Image.new('L',(256,256))
                    sd_indices.paste(8,(0,0),sd_edge.point(lambda v:255 if v>=64 else 0))
                    sd_indices.paste(sd_glyph.point(lambda v:max(1,7-round(v*6/255))),(0,0),sd_glyph.point(lambda v:255 if v>=24 else 0))
                    sd_values=sd_indices.tobytes()
                    sd_pixels=bytes(a|(b<<4) for a,b in zip(sd_values[::2],sd_values[1::2]))
                    (out/'sentences-sd'/f'{sid:05d}-{row*cols+col:02d}.tim').write_bytes(header+struct.pack('<IHHHH',12+len(sd_pixels),0,0,64,256)+sd_pixels)
                    tile_count+=1
            records.append((width,height,last,len(tim),int(bool(re.match(r'^\\+n',text))),line_step//scale))
            if text in preview_texts:
                rgba=Image.new('RGB',ink.size,'#393939')
                rgba.paste((18,18,25),mask=border); rgba.paste((230,230,218),mask=ink)
                preview.append((text,rgba.crop((0,0,240*scale,height*scale))))
        sid=fragments[key]
        return chr(0xe000)+''.join(chr(0xe001+((sid>>shift)&15)) for shift in (12,8,4,0))
    for path in sorted(source.rglob('*.xml')):
        tree=ET.parse(path)
        if path.name=='save2.xml':
            counts['save_menu_entries']=len(tree.getroot())
        for index,e in enumerate(tree.getroot()):
            # Keep character names and filename identifiers in the native ASCII font.
            if path.name=='save2.xml' and index in (6,7,18,19):
                counts['entries']+=1
                continue
            before=e.text or ''
            e.text=''.join(part if part.startswith('{') else re.sub(r'.+',lambda m:encode(m,path.name=='save2.xml'),part,flags=re.S) for part in re.split(r'(\{[^}]+\})',before))
            assert re.findall(r'\{[^}]+\}',before)==re.findall(r'\{[^}]+\}',e.text)
            counts['entries']+=1
            counts['common_entries' if path.name=='misc.xml' else 'room_entries' if path.parent.name=='text' else 'resource_entries']+=1
        dest=out/path.relative_to(source); dest.parent.mkdir(parents=True,exist_ok=True)
        tree.write(dest,encoding='utf-8',xml_declaration=False)
    choice_ids=[]
    empty_text=ET.parse(source/'item_simple.xml').getroot()[0].text or ''
    empty_item_id=fragments[empty_text] if empty_text.strip() else '0xffffffffu'
    for label in ('예','아니요'):
        encode(re.match(r'.+',label)); choice_ids.append(fragments[label])
    encoding=ET.parse(ROOT/'source/encoding.xml')
    for e in list(encoding.getroot()):
        if int(e.attrib['Encode'],0) in range(0xa4,0xb5):encoding.getroot().remove(e)
    for i in range(17): ET.SubElement(encoding.getroot(),'Entry',Encode=hex(0xa4+i),Char=chr(0xe000+i),width='0',indent='0')
    codes=[int(e.attrib['Encode'],0) for e in encoding.getroot()]
    assert max(codes)<0xee and len(codes)<=max(codes)+1
    encoding.write(out/'encoding.xml',encoding='utf-8',xml_declaration=False)
    (out/'ko_sentence.flag').write_bytes(b'KOSENT07')
    (out/'manifest.txt').write_text('[MOD]\nName = Resident Evil - Korean HD Translation\nModule = korean_subtitle.dll\nJapanese = 0\nUseRdtXml = 1\n',encoding='utf-8')
    (ROOT/'build/sentence_records.h').write_text('/* Generated by build_all_subtitles.py */\n#define SENTENCE_COUNT '+str(len(records))+'\n#define LINE_HEIGHT '+str(step//scale)+'\n#define RENDER_SCALE '+str(scale)+'\n#define CHOICE_YES '+str(choice_ids[0])+'\n#define CHOICE_NO '+str(choice_ids[1])+'\n#define EMPTY_ITEM '+str(empty_item_id)+'\nstatic const unsigned sentence_records[][6]={'+','.join('{'+','.join(map(str,r))+'}' for r in records)+'};\n',encoding='utf-8')
    documents=build_documents(out)
    report={**counts,'sentences':len(records),'textures':tile_count,'document_pages':documents['page_count'],'document_png_pages':documents['png_page_count'],'document_font_sizes':documents['font_sizes'],'font':FONT.name,'font_size':args.font_size,'display_font_size':logical_size,'render_scale':scale,'downsample':'GPU display of native high-resolution tiles','line_height':step//scale,'save_menu_display_font_size':11,'save_menu_line_height':14,'timing_tags':'preserved','visible_source_codes':False,'runtime':'not verified','dynamic_strings':'item-name CSV markers; original substitution controls preserved','translation_source':'translation/*.csv','csv_sha256':{name:hashlib.sha256((ROOT/'translation'/name).read_bytes()).hexdigest() for name in ('dialogue.csv','messages.csv','resources.csv')}}
    (out/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'build/sentence-map.json').write_text(json.dumps(fragments,ensure_ascii=False,indent=2),encoding='utf-8')
    if preview:
        unique={t:im for t,im in preview}; sheet=Image.new('RGB',(240*scale,sum(im.height+5 for im in unique.values())),'#393939'); y=0
        for im in unique.values():sheet.paste(im,(0,y));y+=im.height+5
        sheet.save(ROOT/'build/subtitle-preview.png')
    # Marker round-trip including capacity edge; no high two-byte engine codes.
    for sid in (0,15,16,255,256,len(records)-1,65535):
        chars=chr(0xe000)+''.join(chr(0xe001+((sid>>s)&15)) for s in (12,8,4,0))
        decoded=0
        for ch in chars[1:]: decoded=decoded*16+ord(ch)-0xe001
        assert decoded==sid
    subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-I',str(ROOT/'build'),'-o',str(ROOT/'build/korean_subtitle.dll'),str(ROOT/'src/korean_subtitle.c')],check=True)
    shutil.copy2(ROOT/'build/korean_subtitle.dll',out/'korean_subtitle.dll')
    subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu','-shared','-Os','-o',str(ROOT/'build/winmm.dll'),str(ROOT/'src/autoselect.c')],check=True)
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
