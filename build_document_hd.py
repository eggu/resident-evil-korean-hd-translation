"""Build all document HD replacements for REbirth 1.1.4's texture lookup."""
import argparse, json, zlib
from pathlib import Path
from PIL import Image
from build_resources import load_resources
from build_rebirth_documents import ROOT, GAME, render_page


def texture_key(page):
    pixels = bytearray(256*256*4)
    raw = page.tobytes('raw', 'BGRA')
    # REbirth retains the transparent sentinel 1 until after its full-image CRC.
    for i in range(0, len(raw), 4):
        b, g, r, a = raw[i:i+4]
        pixels[i:i+4] = bytes((b, g, r, 255)) if a else b'\x01\0\0\0'
    return f'{zlib.crc32(pixels):08X}'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=ROOT/'build/mod_korean_translation');args=ap.parse_args()
    rows = [r for r in load_resources() if r['종류'] == '문서 PNG 페이지']
    out = ROOT / 'build/document-hd-trial'
    pages = []; assets = set()
    for row in rows:
        base, _ = render_page(row)
        installed = Image.open(args.source / row['파일']).convert('RGBA')
        assert base.tobytes() == installed.tobytes(), ('Installed document differs', row['파일'])
        high, info = render_page(row, 4)
        # Pass Number P01 is transparent so its underlying numbered background shows through.
        blank = info.get('blank')
        # Pad 256x192 pages to the loader's 256x256 UV allocation, scaled 4x.
        canvas = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0) if blank else (0, 0, 0, 255))
        if not blank: canvas.paste(high, (0, 0))
        relative = 'hires/misc/' + texture_key(base) + '.webp'
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative in assets:
            assert Image.open(target).convert('RGBA').tobytes() == canvas.tobytes(), ('CRC collision', relative)
        else:
            canvas.save(target, lossless=True, exact=True)
            assert Image.open(target).convert('RGBA').tobytes() == canvas.tobytes()
            assets.add(relative)
        pages.append({'page': row['파일'], 'texture': relative, 'layout': info})
    report = {'pages': pages, 'assets': sorted(assets), 'page_resolution': [1024, 768], 'physical_texture': [1024, 1024]}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pages': len(pages), 'unique_assets': len(assets)},ensure_ascii=False))


if __name__ == '__main__': main()
