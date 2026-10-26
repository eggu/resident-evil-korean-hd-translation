"""REbirth hook points: the fixed 1.1.3 table and 1.1.4+ discovery both match real ddraw.dll builds."""
import os,re,struct,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DLLS={'1.1.4':ROOT/'.ci-inputs/game/ddraw.dll','1.1.3':Path(os.environ.get('RE1_REBIRTH_113','missing'))}
KNOWN_114={'sprite':0x128c,'width':0x61b90,'mods':0x229e290,'reader':0x69f00,'movie_update':0x87670,'movie_font':0xf6750,
           'sprite_sites':[0x613d2,0x6164f,0x61f8f],'width_sites':[0x61d22,0x61efb,0x6e902,0x6eaaa,0x6efcb,0x6f3a7,0x6f518],
           'movie_sites':[0x861b9,0x86c03]}
HARNESS=r'''#include <stdio.h>
#include <stdlib.h>
#include "rebirth_discover.h"
int main(int argc,char **argv) {
    FILE *f=fopen(argv[1],"rb");fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);
    uint8_t *data=malloc(size+64);memset(data,0,size+64);fread(data,1,size,f);fclose(f);
    struct Discovered d;
    if(!discover_rebirth(data,(uint32_t)strtoul(argv[2],0,0),&d)) { puts("none");return 0; }
    printf("sprite %u\nwidth %u\nmods %u\nreader %u\nmovie_update %u\nmovie_font %u\n",d.sprite,d.width,d.mods,d.reader,d.movie_update,d.movie_font);
    printf("sprite_sites %u %u %u\nmovie_sites %u %u\nwidth_sites",d.sprite_sites[0],d.sprite_sites[1],d.sprite_sites[2],d.movie_sites[0],d.movie_sites[1]);
    for(unsigned i=0;i<d.width_count;i++) printf(" %u",d.width_sites[i]);
    puts("");return 0;
}
'''


def mapped(path):
    import pefile
    pe=pefile.PE(str(path));return pe,pe.get_memory_mapped_image()


class RebirthVersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(tempfile.mkdtemp())
        (cls.folder/'harness.c').write_text(HARNESS)
        subprocess.run([sys.executable,'-m','ziglang','cc','-O1','-I',str(ROOT/'src'),'-o',str(cls.folder/'harness'),str(cls.folder/'harness.c')],check=True)

    def discover(self,path):
        pe,image=mapped(path);dump=self.folder/'image.bin';dump.write_bytes(image)
        out=subprocess.run([str(self.folder/'harness'),str(dump),str(pe.OPTIONAL_HEADER.ImageBase)],capture_output=True,text=True,check=True).stdout
        if out.strip()=='none': return None
        found={}
        for line in out.splitlines():
            key,*values=line.split();values=[int(v) for v in values]
            found[key]=values if key.endswith('sites') else values[0]
        return found

    def test_discovery_reproduces_114(self):
        if not DLLS['1.1.4'].is_file(): self.skipTest('1.1.4 ddraw.dll not available')
        self.assertEqual(self.discover(DLLS['1.1.4']),KNOWN_114)

    def test_discovery_refuses_113(self):
        if not DLLS['1.1.3'].is_file(): self.skipTest('set RE1_REBIRTH_113')
        self.assertIsNone(self.discover(DLLS['1.1.3']),'1.1.3 must use its fixed table, not 1.1.4 discovery')

    def test_113_table_matches_binary(self):
        if not DLLS['1.1.3'].is_file(): self.skipTest('set RE1_REBIRTH_113')
        source=(ROOT/'src/korean_subtitle.c').read_text()
        body=source[source.index('rebirth_113={'):source.index(';',source.index('rebirth_113={'))]
        n=[int(x,0) for x in re.findall(r'0x[0-9a-f]+|\b\d+\b',body.split(',',2)[2])]
        sprite,width,_,_,_,_,*sites=n
        pe,image=mapped(DLLS['1.1.3'])
        self.assertEqual((pe.FILE_HEADER.TimeDateStamp,pe.OPTIONAL_HEADER.SizeOfImage),(0x5fcc2a03,0x22ce000))
        for site,target in zip(sites[:10],[sprite]*3+[width]*7):
            self.assertEqual(image[site],0xe8,hex(site))
            self.assertEqual((site+5+struct.unpack_from('<i',image,site+1)[0])&0xffffffff,target,hex(site))


if __name__=='__main__':unittest.main()
