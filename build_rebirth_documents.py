"""REbirth 1.1.4 English-mode FILE/ PNG pages, edited in resources.csv."""
from pathlib import Path
import hashlib
import struct
from PIL import Image, ImageDraw, ImageFont

from build_paths import ROOT, GAME
DEFAULTS = ROOT / 'build/rebirth-default-assets'
DDRAW_HASH = '144764bf113d0f19767a9f2e35927b30ccfbb978790a427189583544b6c52889'


def default_documents():
    data = (GAME / 'ddraw.dll').read_bytes()
    if hashlib.sha256(data).hexdigest() != DDRAW_HASH:
        raise ValueError('Document layout requires the verified REbirth 1.1.4 DLL')
    if not (DEFAULTS / 'FILE/FILEM_000.png').exists():
        # DATA/107 is the embedded 7z archive in this exact guarded image.
        pe = struct.unpack_from('<I', data, 0x3c)[0]
        count = struct.unpack_from('<H', data, pe + 6)[0]
        optional = struct.unpack_from('<H', data, pe + 20)[0]
        for i in range(count):
            section = pe + 24 + optional + i * 40
            size, rva, raw_size, raw = struct.unpack_from('<IIII', data, section + 8)
            if rva <= 37385544 < rva + size:
                offset = raw + 37385544 - rva
                archive = data[offset:offset + 877311]
                break
        else:
            raise ValueError('Default archive missing')
        if not archive.startswith(b"7z\xbc\xaf'\x1c"):
            raise ValueError('Default archive header changed')
        DEFAULTS.mkdir(parents=True, exist_ok=True)
        path = ROOT / 'build/rebirth-data107.7z'
        path.write_bytes(archive)
        import py7zr
        with py7zr.SevenZipFile(path) as source:
            source.extractall(path=DEFAULTS)
    return DEFAULTS / 'FILE'


def render_page(row, scale=1):
    from build_resources import FONT, CIPHER_TOKEN, CIPHER_RECT, wrap_document, read_document
    original = Image.open(DEFAULTS / row['파일']).convert('RGBA')
    if original.size != (256, 192):
        raise ValueError(f"Unexpected REbirth page size: {row['id']}")
    if not row['번역문'].strip():
        if original.getchannel('A').getbbox():
            raise ValueError(f"Nonblank page has no translation: {row['id']}")
        return original.resize((256*scale,192*scale)), {'file': row['파일'], 'blank': True}
    for size in (12, 11, 10, 9):
        font = ImageFont.truetype(str(FONT), size, layout_engine=ImageFont.Layout.BASIC)
        lines = wrap_document(row['번역문'], font)
        step = size + 3
        if sum(24 if CIPHER_TOKEN in line else step for line in lines) <= 176:
            break
    else:
        raise ValueError(f"PNG page does not fit; shorten/repage CSV: {row['id']}")
    preview = Image.new('RGBA', (256*scale,192*scale), (0, 0, 0, 0))
    draw_font = ImageFont.truetype(str(FONT), size*scale, layout_engine=ImageFont.Layout.BASIC)
    draw = ImageDraw.Draw(preview)
    cover = row['id'].endswith('00.png')
    y = 80 if cover else 8
    cipher_report = None
    for line in lines:
        label = line.replace(CIPHER_TOKEN, '')
        x = (256 - font.getlength(label))/2 if cover else 8
        for char in label:
            if not char.isspace():
                position = (round(x)*scale, (y + font.getmetrics()[0])*scale)
                bounds = draw.textbbox(position, char, font=draw_font, anchor='ls')
                if bounds[0] < 0 or bounds[2] > 248*scale or bounds[3] > 192*scale:
                    raise ValueError(f"PNG glyph out of bounds: {row['id']}")
                draw.text(position, char, font=draw_font, fill=(230, 230, 218, 255), anchor='ls')
            x += font.getlength(char)
        if CIPHER_TOKEN in line:
            _, pixels, palette = read_document(GAME / 'jpn/Item_m2/TEXTM_U2.TIM')
            cipher = Image.new('RGBA', (64, 24))
            cipher.putdata([(*palette[v], 255 if v else 0) for v in pixels.crop(CIPHER_RECT).tobytes()])
            target = (round(x)+5, y)
            if target[0]+64 > 248 or y+24 > 192:
                raise ValueError('PNG cipher does not fit')
            cipher = cipher.resize((64*scale,24*scale),Image.Resampling.NEAREST)
            target = (target[0]*scale,target[1]*scale)
            preview.paste(cipher, target)
            box = (*target, target[0]+64*scale, target[1]+24*scale)
            assert preview.crop(box).tobytes() == cipher.tobytes()
            cipher_report = {'rect': box, 'rgba_sha256': hashlib.sha256(cipher.tobytes()).hexdigest()}
        y += 24 if CIPHER_TOKEN in line else step
    return preview, {'file': row['파일'], 'font_size': size, 'lines': len(lines), 'cover': cover, 'cipher': cipher_report}


def build_pages(out, rows):
    reports = []
    previews = ROOT / 'build/document-preview'
    for row in rows:
        if row['종류'] != '문서 PNG 페이지':
            continue
        preview, report = render_page(row)
        target = out / row['파일']
        target.parent.mkdir(parents=True, exist_ok=True)
        preview.save(target)
        preview.resize((512, 384)).save(previews / row['id'])
        report['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        reports.append(report)
    return reports
