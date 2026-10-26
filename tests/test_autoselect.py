"""winmm.dll proxy: full export list, and (with Wine) that it runs before a REbirth-like ddraw.dll reads its arguments."""
import os,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WINE=os.environ.get('WINE') or shutil.which('wine')
FAKE_DDRAW=r'''#include <windows.h>
#include <stdio.h>
__declspec(dllexport) int probe(void) { return 1; }
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,void *unused) {
    if(reason==DLL_PROCESS_ATTACH) { FILE *f=fopen("probe.txt","w");fprintf(f,"%s\n%d\n",GetCommandLineA(),timeGetTime()>0);fclose(f); }
    return TRUE;
}
'''
GAME='__declspec(dllimport) int probe(void);\nint main(void) { return probe() ? 0 : 1; }\n'


def zig(*args):
    subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86-windows-gnu',*map(str,args)],check=True)


class AutoselectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(tempfile.mkdtemp())
        zig('-shared','-Os','-o',cls.folder/'winmm.dll',ROOT/'src/autoselect.c')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder)

    def test_exports_every_listed_name(self):
        import pefile
        names={e.name.decode() for e in pefile.PE(str(self.folder/'winmm.dll')).DIRECTORY_ENTRY_EXPORT.symbols}
        listed=set(re.findall(r'^X\((\w+)\)$',(ROOT/'src/winmm_exports.h').read_text(),re.M))
        self.assertEqual(names,listed)
        self.assertIn('timeGetTime',names)

    @unittest.skipUnless(WINE,'set WINE to a wine binary for the load-order check')
    def test_argument_reaches_rebirth_dllmain(self):
        game=self.folder/'game';game.mkdir()
        (self.folder/'ddraw.c').write_text(FAKE_DDRAW);(self.folder/'game.c').write_text(GAME)
        zig('-shared','-o',game/'ddraw.dll',self.folder/'ddraw.c','-lwinmm')
        zig('-o',game/'game.exe',self.folder/'game.c',game/'ddraw.dll')
        shutil.copy2(self.folder/'winmm.dll',game/'winmm.dll')
        env=dict(os.environ,WINEPREFIX=str(self.folder/'prefix'),WINEDLLOVERRIDES='winmm,ddraw=n,b',WINEDEBUG='-all')
        def run(*args):
            subprocess.run([WINE,'game.exe',*args],cwd=game,env=env,check=True,capture_output=True,timeout=300)
            return (game/'probe.txt').read_text().splitlines()
        self.assertEqual(run()[0].count(' -dev_korean_translation'),0,'no mod folder: unchanged')
        (game/'mod_korean_translation').mkdir()
        command,timer=run()
        self.assertTrue(command.endswith(' -dev_korean_translation'),command)
        self.assertEqual(timer,'1','forwarded winmm export works')
        self.assertNotIn('-dev_korean_translation',run('-config')[0],'user option keeps the menu')


if __name__=='__main__':unittest.main()
