"""Exercise REbirth PNG pixel conversion before document transparency/CRC checks."""
import hashlib, sys, zlib
from PIL import Image
from unicorn.x86_const import UC_X86_REG_EDX, UC_X86_REG_ESP
from verify_renderer import Engine, GAME, ROOT, STACK
from check_markers import Markers, DDHASH
sys.path.insert(0, str(ROOT))
from build_rebirth_documents import render_page
from build_resources import load_resources
from build_document_hd import texture_key


class PagePixels(Engine):
    module = Markers.module

    def __init__(self):
        super().__init__()
        assert hashlib.sha256((GAME / 'ddraw.dll').read_bytes()).hexdigest() == DDHASH
        self.module(GAME / 'ddraw.dll', 0x10000000)

    def hook(self, uc, address, size, user):
        if address == 0x100f20f8:
            count = self.rd(self.u.reg_read(UC_X86_REG_ESP) + 4)
            pointer = self.heap
            self.heap += (count + 31) & ~15
            assert self.heap < 0x4f00000
            self.ret(pointer)
        elif 0x10000000 <= address < 0x12500000:
            pass
        else:
            super().hook(uc, address, size, user)

    def convert(self, image):
        source, obj, buffer = 0x2100000, 0x2200000, 0x2300000
        self.u.mem_write(source, image.tobytes())
        self.u.mem_write(obj, bytes(16))
        self.call(0x10043600, (source, *image.size), this=obj)
        assert self.u.reg_read(UC_X86_REG_ESP) == STACK + 16
        pixels = self.rd(obj + 8)
        self.u.mem_write(buffer, b'\0\0\0\xff' * (256 * 256))
        self.u.mem_write(buffer, bytes(self.u.mem_read(pixels, 256 * 192 * 4)))
        self.u.reg_write(UC_X86_REG_EDX, 256)
        self.call(0x1004ffc0, (256, 256), this=buffer)
        self.u.reg_write(UC_X86_REG_EDX, 256)
        self.call(0x10050050, (256, 256), this=buffer)
        return bytes(self.u.mem_read(buffer, 256 * 256 * 4))


def main():
    old = PagePixels().convert(Image.new('RGBA', (256, 192), (255, 255, 255, 0)))
    assert old[:4] == b'\xff' * 4, 'White RGB reproduces the opaque-page regression'
    rows = [r for r in load_resources() if r['id'] in ('FILEM_P01.png', 'FILEM_W01.png')]
    assert len(rows) == 2
    for row in rows:
        page, info = render_page(row)
        assert info['blank'] and not any(page.tobytes()), row['id']
        converted = PagePixels().convert(page)
        assert converted[:256 * 192 * 4] == b'\x01\0\0\0' * (256 * 192)
        assert converted[256 * 192 * 4:] == bytes(256 * 64 * 4)
        assert f'{zlib.crc32(converted):08X}' == texture_key(page) == 'B7A90456'
    print('Pass Number / Important File: native PNG transparency and HD CRC passed')


if __name__ == '__main__':
    main()
