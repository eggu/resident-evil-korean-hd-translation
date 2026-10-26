"""Check the delivered ZIP, input isolation and unsafe release paths."""
import io,json,os,re,shutil,struct,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.package_release import allowed_path


class PackageTests(unittest.TestCase):
    def test_only_runtime_files_and_current_resources(self):
        package=ROOT/'dist'/f"Resident-Evil-Korean-HD-Translation-{(ROOT/'VERSION').read_text(encoding='utf-8').strip()}.zip"
        with zipfile.ZipFile(package) as archive:
            names=archive.namelist()
            self.assertEqual(len(names),len(set(names)))
            self.assertTrue(all(allowed_path(name) for name in names))
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('korean_subtitle.dll'),archive.read('mod_korean_translation/korean_subtitle.dll'))
            self.assertEqual(archive.read('optional/winmm.dll')[:2],b'MZ')
            self.assertIn('Name = Resident Evil - Korean HD Translation',archive.read('mod_korean_translation/manifest.txt').decode())
            self.assertEqual(archive.read('jpn/Item_m2/TEXTM_P0.TIM'),archive.read('mod_korean_translation/ITEM_M2/TEXTM_P0.TIM'))
            self.assertEqual(archive.read('mod_korean_translation/ko_sentence.flag'),b'KOSENT07')
            for page in ('FILEM_P01.png','FILEM_W01.png'):
                image=Image.open(io.BytesIO(archive.read('mod_korean_translation/FILE/'+page))).convert('RGBA')
                self.assertEqual(image.tobytes(),bytes(256*192*4),page)
            records=[tuple(map(int,x.split(','))) for x in re.findall(r'\{([0-9,]+)\}',(ROOT/'build/sentence_records.h').read_text(encoding='utf-8'))]
            expected=set()
            for sid,(w,h,_,size,*rest) in enumerate(records):
                for tile in range(((w+63)//64)*((h+63)//64)):
                    for mode in ('sentences','sentences-sd'):
                        name=f'mod_korean_translation/{mode}/{sid:05d}-{tile:02d}.tim'
                        expected.add(name);data=archive.read(name)
                        self.assertEqual(len(data),size,name)
                        self.assertEqual(struct.unpack_from('<II',data),(16,8),name)
            actual={name for name in names if '/sentences' in name}
            self.assertEqual(actual,expected,'Missing current tiles or stale older tiles')
            for name in ('movie/PJ.srt','movie/Ed4.srt','movie/Ed5.srt'):
                self.assertIn(' --> ',archive.read(name).decode('utf-8'))
            metadata=json.loads(archive.read('release.json'))
            self.assertEqual(metadata['sentences'],len(records))
            self.assertEqual(metadata['tiles_per_mode']*2,len(expected))

    def test_original_path_must_be_explicit(self):
        env=dict(os.environ);env.pop('RE1_GAME_ORIGINAL_DIR',None)
        result=subprocess.run([sys.executable,'-c','import build_paths'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Set RE1_GAME_ORIGINAL_DIR',result.stderr)

    def test_patched_original_document_is_rejected(self):
        from build_paths import GAME
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder);shutil.copytree(GAME/'jpn/Item_m2',fake/'jpn/Item_m2')
            shutil.copyfile(GAME/'ddraw.dll',fake/'ddraw.dll')
            target=fake/'jpn/Item_m2/TEXTM_P0.TIM'
            data=bytearray(target.read_bytes());data[-1]^=1;target.write_bytes(data)
            env=dict(os.environ,RE1_GAME_ORIGINAL_DIR=str(fake))
            result=subprocess.run([sys.executable,'-c','from build_resources import load_resources;load_resources()'],
                                  cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Original resource hash changed',result.stderr)

    def test_release_paths_exclude_game_user_and_build_files(self):
        for name in ('../config.ini','/tmp/korean_subtitle.dll','config.ini','Biohazard.exe',
                     'savedata/save.dat','local/build-inputs.key','build/coverage.json',
                     'mod_korean_translation/coverage.json','mod_korean_translation/sentences/00000-99.tim.bak'):
            self.assertFalse(allowed_path(name),name)


if __name__=='__main__':unittest.main()
