"""Compare document keys with the verified bio1hd downsample/alpha/CRC machine code."""
import argparse
import hashlib
import sys
from pathlib import Path
import struct

import pefile
from PIL import Image
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_document_hd import texture_key
from build_resources import load_resources
from build_rebirth_documents import render_page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loader', type=Path, required=True)
    args = parser.parse_args()
    data = args.loader.read_bytes()
    assert hashlib.sha256(data).hexdigest() == '5cdc4ed20822b4e6619d870f57acead6026bc186a15503b96014a61fc0926f99'
    pe = pefile.PE(data=data)
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    u.mem_map(0x10000000, 0x10000)
    u.mem_write(0x10000000, pe.get_memory_mapped_image())
    source, target, stack, stop = 0x20000000, 0x20400000, 0x20800000, 0x20801000
    u.mem_map(source, 0x801000 + 0x1000)

    def call(address, ecx, edx, *arguments):
        u.mem_write(stack, struct.pack('<' + 'I' * (len(arguments) + 1), stop, *arguments))
        u.reg_write(UC_X86_REG_ESP, stack)
        u.reg_write(UC_X86_REG_ECX, ecx)
        u.reg_write(UC_X86_REG_EDX, edx)
        u.emu_start(address, stop)
        return u.reg_read(UC_X86_REG_EAX)

    count = 0
    for row in load_resources():
        if row['종류'] != '문서 PNG 페이지':
            continue
        page, info = render_page(row)
        if info.get('blank'):
            continue
        canvas = Image.new('RGBA', (256, 256))
        canvas.paste(page)
        expanded = canvas.resize((1024, 1024), Image.Resampling.NEAREST)
        u.mem_write(source, expanded.tobytes('raw', 'BGRA'))
        u.mem_write(target, bytes(1024 * 1024 * 4))
        # 25f0 delegates its pixel packing to 2560, then copies it back in place.
        call(0x10002560, target, source, 1024, 1024)
        call(0x10002650, target, 1024, 1024)
        native = call(0x10002470, target, 256, 256)
        assert f'{native:08X}' == texture_key(page, legacy=True), row['id']
        count += 1
    print(f'bio1hd native downsample/alpha/CRC matched {count} nonblank document pages')


if __name__ == '__main__':
    main()
