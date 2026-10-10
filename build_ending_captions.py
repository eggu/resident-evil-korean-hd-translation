"""Build Korean caption plates for the clear-reward ending scene."""
from pathlib import Path
import hashlib
import json
import struct

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from build_paths import ROOT, GAME, FONT
OUT = ROOT / 'build/ending-caption-fix'
PLATES = {
    'EN05.TIM': ((130, 160), (200, 215), (141, 156, 211)),
    'EN07.TIM': ((97, 127), (144, 159), (108, 124, 156)),
}
LINES = (('특수 열쇠를', '입수했습니다'), ('옷장을 찾아라',))


def build(name, expected):
    source = GAME / 'jpn/Data' / name
    data = source.read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected, f'Unexpected source: {name}'
    flags = struct.unpack_from('<I', data, 4)[0]
    assert flags == 8, f'Expected 4-bit indexed TIM: {name}'
    clut_size = struct.unpack_from('<I', data, 8)[0]
    assert struct.unpack_from('<HHHH', data, 12) == (0, 480, 16, 1)
    image_at = 8 + clut_size
    block_size, _, _, words, height = struct.unpack_from('<IHHHH', data, image_at)
    width = words * 4
    assert (width, height, block_size) == (256, (256 if name == 'EN05.TIM' else 168), 12 + 128 * height)
    palette_at = 20
    palette = [struct.unpack_from('<H', data, palette_at + i * 2)[0] for i in range(16)]
    pixels_at = image_at + 12
    raw = data[pixels_at:pixels_at + 128 * height]
    indices = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            byte = raw[y * (width // 2) + x // 2]
            indices[y * width + x] = (byte >> 4) & 15 if x & 1 else byte & 15

    first, second, baselines = PLATES[name]
    regions = (first, second)
    originals = bytes(indices)
    for top, bottom in regions:
        indices[top * width:bottom * width] = bytes(width * (bottom - top))

    font_px, scale, tracking = 14, 4, 2
    font = ImageFont.truetype(FONT, font_px * scale, layout_engine=ImageFont.Layout.BASIC)
    rendered = Image.new('L', (width * scale, height * scale))
    draw = ImageDraw.Draw(rendered)
    for lines, baseline_rows in zip(LINES, ((baselines[0], baselines[1]), (baselines[2],))):
        for text, baseline in zip(lines, baseline_rows):
            advance = [font.getlength(c) for c in text]
            total = sum(advance) + tracking * scale * (len(text) - 1)
            x = round((width * scale - total) / 2)
            for char, width_px in zip(text, advance):
                if not char.isspace():
                    draw.text((x, baseline * scale), char, font=font, fill=255, anchor='ls')
                x += round(width_px) + (tracking * scale if char != text[-1] else 0)

    ink = rendered.resize((width, height), Image.Resampling.LANCZOS)
    edge = ink.filter(ImageFilter.MaxFilter(3))
    shades = []
    for index, value in enumerate(palette):
        if index == 0:
            continue
        rgb = ((value & 31) * 255 // 31, ((value >> 5) & 31) * 255 // 31, ((value >> 10) & 31) * 255 // 31)
        shades.append((round(sum(rgb) / 3), index))
    outline = min(shades, key=lambda x: abs(x[0] - 84))[1]
    for y in range(height):
        if not any(top <= y < bottom for top, bottom in regions):
            continue
        for x in range(width):
            coverage = ink.getpixel((x, y))
            if coverage:
                level = round(112 + coverage * 143 / 255)
                indices[y * width + x] = min(shades, key=lambda s: abs(s[0] - level))[1]
            elif edge.getpixel((x, y)):
                indices[y * width + x] = outline

    packed = bytearray()
    for y in range(height):
        row = indices[y * width:(y + 1) * width]
        packed.extend(a | (b << 4) for a, b in zip(row[::2], row[1::2]))
    patched = data[:pixels_at] + packed + data[pixels_at + len(packed):]

    # The captions are the only pixels allowed to change.
    for y in range(height):
        if not any(top <= y < bottom for top, bottom in regions):
            assert indices[y * width:(y + 1) * width] == originals[y * width:(y + 1) * width]
    assert hashlib.sha256(patched).hexdigest() != expected

    preview = Image.new('RGB', (width, height), '#171717')
    preview.putdata([((palette[v] & 31) * 255 // 31, ((palette[v] >> 5) & 31) * 255 // 31, ((palette[v] >> 10) & 31) * 255 // 31) if v else (0, 0, 0) for v in indices])
    return patched, preview


def main():
    expected = json.loads((ROOT / 'input_hashes.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'translations': ['특수 열쇠를 입수했습니다', '옷장을 찾아라'], 'files': {}}
    for name in PLATES:
        data, preview = build(name, expected['jpn/Data/' + name])
        target = OUT / 'jpn/Data' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        preview.save(ROOT / 'build' / (name.lower().replace('.tim', '-caption-preview.png')))
        report['files'][name] = {'source_sha256': expected['jpn/Data/' + name], 'candidate_sha256': hashlib.sha256(data).hexdigest()}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
