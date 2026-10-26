import csv
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentPagination(unittest.TestCase):
    def test_layout_keeps_readable_type_and_password_names(self):
        from build_resources import load_resources
        from build_rebirth_documents import render_page
        rows = load_resources()
        pages = [r for r in rows if r['종류'] == '문서 PNG 페이지']
        self.assertEqual(len(pages), 70)
        optimized = json.loads((ROOT / 'translation/document-pages.json').read_text())
        for row in pages:
            _, report = render_page(row, 4)
            if row['id'][6] in optimized:
                self.assertEqual(report['font_size'], 12, row['id'])
        letter = ''.join(r['번역문'] for r in pages if r['id'].startswith('FILEM_U'))
        self.assertIn('에이다(ADA)', letter)
        self.assertIn('존(JOHN)', letter)
        with (ROOT / 'translation/resources.csv').open(encoding='utf-8-sig') as stream:
            original = list(csv.DictReader(stream))
        tim = ''.join(r['번역문'] for r in original if r['id'].startswith('TEXTM_U'))
        self.assertIn('에이다(ADA)', tim)
        self.assertIn('존(JOHN)', tim)

    def test_layout_rejects_missing_translation(self):
        from build_rebirth_documents import optimize_pages
        with (ROOT / 'translation/resources.csv').open(encoding='utf-8-sig') as stream:
            rows = list(csv.DictReader(stream))
        layout = json.loads((ROOT / 'translation/document-pages.json').read_text())
        layout['L'][0] = layout['L'][0][1:]
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / 'document-pages.json').write_text(json.dumps(layout))
            with self.assertRaisesRegex(ValueError, 'changes source text'):
                optimize_pages(rows, Path(temp))

    def test_limits_switch_restore_and_preserve_other_mods(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('native C compiler unavailable')
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'limits.c'
            source.write_text('''#include <assert.h>
#include "document_pagination.h"
int main(void) {
    unsigned char table[16];
    memcpy(table,original_document_counts,16);
    assert(apply_document_counts(table,1)==1);
    assert(!memcmp(table,document_page_counts,16));
    assert(apply_document_counts(table,1)==2);
    assert(apply_document_counts(table,0)==1);
    assert(!memcmp(table,original_document_counts,16));
    table[0]=99;
    assert(apply_document_counts(table,1)==0 && table[0]==99);
    assert(apply_document_counts(table,0)==0 && table[0]==99);
    return 0;
}
''')
            binary = Path(temp) / 'limits'
            subprocess.run([compiler, '-I', str(ROOT / 'src'), '-I', str(ROOT / 'build'),
                            str(source), '-o', str(binary)], check=True, capture_output=True)
            subprocess.run([str(binary)], check=True)

    def test_original_game_stops_at_new_limits_and_can_go_back(self):
        import pefile
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP
        from build_paths import GAME
        from build_rebirth_documents import DOCUMENT_GROUPS
        pe = pefile.PE(str(GAME / 'Biohazard.exe'))
        self.assertEqual(pe.get_data(0x2b70f, 5), bytes.fromhex('e81c080000'))
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x990000)
        u.mem_write(0x400000, pe.get_memory_mapped_image())
        state, stack, stop = 0x2000000, 0x2001000, 0x2002000
        u.mem_map(state, 0x3000)
        counts = json.loads((ROOT / 'build/document-preview/page-counts.json').read_text())
        u.mem_write(0x4af1e8, bytes(counts[g] for g in DOCUMENT_GROUPS))
        catalog = bytes(u.mem_read(0x4af5d0, 32))

        def boundary(uc, address, size, unused):
            if address in (0x468310, 0x42c080):  # Sound and page animation are outside this input/limit test.
                sp = uc.reg_read(UC_X86_REG_ESP)
                uc.reg_write(UC_X86_REG_EIP, struct.unpack('<I', uc.mem_read(sp, 4))[0])
                uc.reg_write(UC_X86_REG_ESP, sp + 4)
        u.hook_add(UC_HOOK_CODE, boundary)
        for book, group in enumerate(DOCUMENT_GROUPS):
            # 42c9a0 resolves catalog sentinel FE to the acquired L/M variant before opening.
            index = catalog.index(0xfe) if book < 2 else catalog.index(book)
            u.mem_write(0x4af5d0 + index, bytes([book]))
            for page, key, end in ((counts[group] - 2, 0x2000, False),
                                   (counts[group] - 1, 0x2000, True), (0, 0x8000, False)):
                raw = bytearray(32)
                raw[4], raw[5], raw[7] = index // 8 % 2, index % 8, index // 16
                raw[6] = page
                u.mem_write(state, bytes(raw))
                u.mem_write(0xc3f8dc, struct.pack('<HHH', 0, 0, key))
                u.mem_write(stack, struct.pack('<II', stop, state))
                u.reg_write(UC_X86_REG_ESP, stack)
                u.emu_start(0x42bf90, stop, count=10000)
                self.assertEqual(u.reg_read(UC_X86_REG_EIP), stop)
                result = bytes(u.mem_read(state, 32))
                self.assertEqual(bool(result[16]), end, group)
                self.assertEqual(bool(result[9]), key == 0x2000 and not end, group)
                self.assertLess(result[6], counts[group])


if __name__ == '__main__':
    unittest.main()
