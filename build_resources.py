"""Build item/UI XML and the original 43 document pages from resources.csv."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET

from build_paths import ROOT, GAME, FONT
XML_FILES = ('item_simple.xml', 'desc.xml', 'save2.xml', 'config.xml')
CIPHER_TOKEN = '[[원본암호]]'
CIPHER_RECT = (132, 80, 196, 104)


def load_resources(directory=ROOT / 'translation'):
    from fontTools.ttLib import TTFont
    from build_rebirth_documents import default_documents, DEFAULTS
    with (directory / 'resources.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    references=json.loads((ROOT/'translation/resource_layout.json').read_text(encoding='utf-8'))
    expected = {f'{name}:{i}' for name in XML_FILES for i, _ in enumerate(references[name]['entries'])}
    expected |= {p.name for p in (GAME / 'jpn/Item_m2').glob('TEXTM_*.TIM')}
    expected |= {p.name for p in default_documents().glob('*.png')}
    ids = [row['id'] for row in rows]
    if len(set(ids)) != len(ids) or set(ids) != expected:
        raise ValueError('Resource CSV contains duplicate, unknown or missing entries')
    for row in rows:
        name = row['파일']
        if row['종류'] in ('문서 페이지', '문서 PNG 페이지'):
            png = row['종류'] == '문서 PNG 페이지'
            folder = 'FILE/' if png else 'ITEM_M2/'
            if name != folder + row['id'] or row['항목'] != '0':
                raise ValueError(f"Document path changed: {row['id']}")
            path = (DEFAULTS / 'FILE' if png else GAME / 'jpn/Item_m2') / row['id']
            if row['id'] in ('TEXTM_U2.TIM', 'FILEM_U04.png') and row['번역문'].count(CIPHER_TOKEN) != 1:
                raise ValueError('Document U2 must retain the original cipher image placeholder')
            if row['id'] not in ('TEXTM_U2.TIM', 'FILEM_U04.png') and CIPHER_TOKEN in row['번역문']:
                raise ValueError('Cipher placeholder outside document U2')
        else:
            if name not in XML_FILES or row['id'] != f"{name}:{int(row['항목'])}":
                raise ValueError(f"XML path/index changed: {row['id']}")
            original = references[name]['entries'][int(row['항목'])]
            if row['원본SHA256'] != references[name]['source_sha256']:
                raise ValueError(f"XML source provenance changed: {row['id']}")
            if row['원문'] != original:
                raise ValueError(f"Resource source changed: {row['id']}")
            if re.findall(r'\{[^}]*\}', original) != re.findall(r'\{[^}]*\}', row['번역문']):
                raise ValueError(f"Resource controls changed: {row['id']}")
            if name == 'save2.xml' and int(row['항목']) in (18, 19) and row['번역문'] != original:
                raise ValueError('ASCII save filename identifiers must remain unchanged')
        if row['종류'] in ('문서 페이지', '문서 PNG 페이지') and hashlib.sha256(path.read_bytes()).hexdigest() != row['원본SHA256']:
            raise ValueError(f'Original resource hash changed: {path}')
        if not row['번역문'].strip() and row['검수상태'] != '원문 없음/제어 슬롯':
            raise ValueError(f"Empty resource translation: {row['id']}")
        if any(0xe000 <= ord(c) <= 0xf8ff for c in row['번역문']):
            raise ValueError(f"Reserved marker in translation: {row['id']}")
    cmap=TTFont(FONT,fontNumber=0).getBestCmap()
    for row in rows:
        if row['종류'] in ('문서 페이지','문서 PNG 페이지'):
            missing={c for c in row['번역문'] if not c.isspace() and ord(c) not in cmap}
            if missing: raise ValueError(f"Document font missing glyphs: {row['id']} {sorted(missing)}")
    return rows


def build_xml(out, rows=None):
    rows = load_resources() if rows is None else rows
    out.mkdir(parents=True, exist_ok=True)
    for name in XML_FILES:
        entries = sorted((row for row in rows if row['파일'] == name), key=lambda row: int(row['항목']))
        root = ET.Element('Strings')
        for row in entries:
            ET.SubElement(root, 'Text').text = row['번역문']
        ET.ElementTree(root).write(out / name, encoding='utf-8', xml_declaration=False)
    return rows


def read_document(path):
    from PIL import Image
    data = path.read_bytes()
    if struct.unpack_from('<II', data) != (16, 9):
        raise ValueError(f'Expected original 8-bit TIM: {path}')
    palette_size, _, _, colors, palettes = struct.unpack_from('<IHHHH', data, 8)
    offset = 8 + palette_size
    size, _, _, words, height = struct.unpack_from('<IHHHH', data, offset)
    if (colors, palettes, words, height, size) != (256, 1, 128, 256, 65548):
        raise ValueError(f'Unexpected document layout: {path}')
    palette_words = struct.unpack_from('<256H', data, 20)
    palette = [((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31) for v in palette_words]
    pixels = Image.frombytes('L', (256, 256), data[offset + 12:])
    return data[:offset + 12], pixels, palette


def wrap_document(text, font):
    lines = []
    for paragraph in text.split('\n'):
        if CIPHER_TOKEN in paragraph:
            lines.append(paragraph)
            continue
        line = ''
        for char in paragraph:
            if line and font.getlength(line + char) > 240:
                cut = line.rfind(' ')
                if cut > len(line) // 2:
                    lines.append(line[:cut]); line = line[cut + 1:] + char
                else:
                    lines.append(line); line = char
            else:
                line += char
        lines.append(line)
    return lines


def render_document(row):
    from PIL import Image, ImageDraw, ImageFont
    header, original, palette = read_document(GAME / 'jpn/Item_m2' / row['id'])
    text = row['번역문'].replace('\r\n', '\n').replace('\r', '\n')
    if '{' in text or '}' in text:
        raise ValueError(f"Unexpected document control text: {row['id']}")
    for size in (12, 11, 10, 9):
        font = ImageFont.truetype(str(FONT), size)
        lines = wrap_document(text, font)
        step = size + 3
        height = sum(24 if CIPHER_TOKEN in line else step for line in lines)
        if height <= 240:
            break
    else:
        raise ValueError(f"Document page does not fit, shorten the CSV translation: {row['id']}")
    ink = Image.new('L', (256, 256))
    draw = ImageDraw.Draw(ink)
    y = 60 if len(lines) == 1 else 8
    cipher_target = None
    for line in lines:
        label = line.replace(CIPHER_TOKEN, '')
        x = (256 - font.getlength(label)) / 2 if len(lines) == 1 else 8
        for char in label:
            # AppleMyungjo has a malformed embedded space bitmap; only advance spaces.
            if not char.isspace():
                position = (round(x), y + font.getmetrics()[0])
                bounds = draw.textbbox(position, char, font=font, anchor='ls')
                if bounds[0] < 0 or bounds[2] > 248 or bounds[3] > 248:
                    raise ValueError(f"Document glyph out of bounds: {row['id']} {char}")
                draw.text(position, char, font=font, fill=255, anchor='ls')
            x += font.getlength(char)
        if CIPHER_TOKEN in line:
            cipher_target = (round(x) + 5, y)
            if cipher_target[0] + 64 > 248 or y + 24 > 248:
                raise ValueError('Cipher image does not fit document U2')
        y += 24 if CIPHER_TOKEN in line else step
    # Reuse the original CLUT. Transparent background and engine TIM dimensions stay fixed.
    shades = [i for i, c in enumerate(palette) if i and max(c) - min(c) <= 8 and max(c) >= 32]
    if not shades:
        raise ValueError('Document palette lacks text shades')
    lookup = [0 if v < 32 else min(shades, key=lambda i: sum(abs(channel - v) for channel in palette[i])) for v in range(256)]
    pixels = ink.point(lookup)
    cipher_report = None
    if cipher_target:
        cipher = original.crop(CIPHER_RECT)
        pixels.paste(cipher, cipher_target)
        box = (*cipher_target, cipher_target[0] + 64, cipher_target[1] + 24)
        if pixels.crop(box).tobytes() != cipher.tobytes():
            raise ValueError('Cipher pixels changed')
        cipher_report = {'source_rect': CIPHER_RECT, 'target_rect': box, 'pixels_sha256': hashlib.sha256(cipher.tobytes()).hexdigest()}
    preview = Image.new('RGB', pixels.size)
    preview.putdata([palette[v] for v in pixels.tobytes()])
    return header + pixels.tobytes(), preview, {'file': row['파일'], 'font_size': size, 'lines': len(lines), 'cipher': cipher_report}


def build_documents(out, rows=None):
    from build_rebirth_documents import build_pages
    rows = load_resources() if rows is None else rows
    preview_dir = ROOT / 'build/document-preview'
    preview_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for row in rows:
        if row['종류'] != '문서 페이지':
            continue
        data, preview, report = render_document(row)
        target = out / row['파일']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        preview.resize((512, 512)).save(preview_dir / (row['id'] + '.png'))
        report['sha256'] = hashlib.sha256(data).hexdigest()
        reports.append(report)
    png_reports = build_pages(out, rows)
    report = {'documents': reports, 'page_count': len(reports), 'png_documents': png_reports, 'png_page_count': len(png_reports), 'font_sizes': dict(collections.Counter(x['font_size'] for x in reports)), 'runtime': 'Not verified in game'}
    (preview_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    rows = build_xml(ROOT / 'build/resource-text')
    print(json.dumps(build_documents(ROOT / 'build/mod_korean_serif', rows), ensure_ascii=False))
