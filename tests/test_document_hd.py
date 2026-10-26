import os
from pathlib import Path
import unittest
from PIL import Image

# The pixel conversion does not read game assets, but build_paths validates inputs.
os.environ.setdefault('RE1_GAME_ORIGINAL_DIR', str(Path(__file__).resolve().parents[1] / '.ci-inputs/game'))
from build_document_hd import hd_page


class DocumentEdges(unittest.TestCase):
    def test_113_key_preserves_fractional_alpha(self):
        import zlib
        from build_document_hd import texture_key
        page = Image.new('RGBA', (256, 192))
        page.putpixel((0, 0), (230, 230, 218, 128))
        expected = bytes((218, 230, 230, 128)) + bytes(256 * 256 * 4 - 4)
        self.assertEqual(texture_key(page, legacy=True), f'{zlib.crc32(expected):08X}')
        opaque = page.copy()
        opaque.putpixel((0, 0), (230, 230, 218, 255))
        self.assertNotEqual(texture_key(page, legacy=True), texture_key(opaque, legacy=True))

    def test_document_font_fits_every_page(self):
        from build_resources import load_resources, render_document
        from build_rebirth_documents import render_page
        for row in load_resources():
            if row['종류'] == '문서 페이지':
                render_document(row)
            elif row['종류'] == '문서 PNG 페이지':
                render_page(row)
                render_page(row, 4)

    def test_diary_dates_stay_whole_without_losing_text(self):
        import hashlib
        import re
        from build_resources import load_resources
        from build_rebirth_documents import render_page
        rows = sorted((r for r in load_resources() if re.fullmatch(r'FILEM_N\d\d.png', r['id'])),
                      key=lambda r: r['id'])
        self.assertEqual(len(rows), 11)
        for row, day in zip(rows[1:10], (9, 10, 11, 12, 13, 14, 16, 19, 21)):
            self.assertTrue(row['번역문'].startswith(f'1998년 5월 {day}일\n'))
            self.assertEqual(len(re.findall(r'1998년 5월 \d+일', row['번역문'])), 1)
            render_page(row, 4)
        text = re.sub(r'\s+', '', ''.join(r['번역문'] for r in rows))
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),
                         '980d7f95a111121d69954176e090e01da265bc318a963f72ebc177604ff3c6fa')

    def test_hd_text_has_solid_light_strokes_and_black_outline(self):
        from build_rebirth_documents import render_page
        from build_resources import load_resources
        row = next(r for r in load_resources() if r['파일'] == 'FILE/FILEM_001.png')
        page, _ = render_page(row, 4)
        colors = set(page.getdata())
        self.assertIn((230, 230, 218, 255), colors)
        self.assertIn((0, 0, 0, 255), colors)
        self.assertEqual(page.size, (1024, 768))

    def test_cutout_keeps_edge_brightness_and_background_transparency(self):
        page = Image.new('RGBA', (3, 1))
        page.putdata([(230, 230, 218, 0), (230, 230, 218, 128), (230, 230, 218, 255)])
        result = hd_page(page)
        self.assertEqual(list(result.getdata()), [(0, 0, 0, 0), (115, 115, 109, 255), (230, 230, 218, 255)])
        self.assertEqual(page.getpixel((1, 0)), (230, 230, 218, 128))


if __name__ == '__main__':
    unittest.main()
