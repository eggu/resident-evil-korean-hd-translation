"""Generate current resources from caller-supplied originals, then make a copy-only ZIP."""
import argparse,json,os,re,shutil,struct,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
PROJECT='Resident Evil - Korean HD Translation'
sys.path.insert(0,str(ROOT))


def allowed_path(name):
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        return False
    return bool(re.fullmatch(
        r'mod_korean_translation/(?:[a-z0-9_]+\.(?:xml|flag)|manifest\.txt|korean_subtitle\.dll|'
        r'text/ROOM_[0-9a-f]+_[0-9]+\.xml|FILE/FILEM_[A-Z0-9]+\.png|'
        r'ITEM_M2/TEXTM_[A-Z0-9]+\.TIM|sentences(?:-sd)?/[0-9]{5}-[0-9]{2}\.tim)|'
        r'hires/misc/[A-F0-9]{8}\.webp|movie/(?:PJ|Ed4|Ed5)\.srt|'
        r'jpn/Item_m2/TEXTM_P0\.TIM|jpn/Data/EN0[57]\.TIM|'
        r'korean_subtitle\.(?:dll|ini)|README\.txt|release\.json',name))


def collect_payload():
    build=ROOT/'build';mod=build/'mod_korean_translation';payload={}
    for path in mod.rglob('*'):
        if path.is_file() and path.name!='coverage.json':
            payload['mod_korean_translation/'+path.relative_to(mod).as_posix()]=path
    report=json.loads((build/'document-hd-trial/report.json').read_text(encoding='utf-8'))
    for name in report['assets']:
        path=build/'document-hd-trial'/name
        payload[name]=path
    for name in ('PJ','Ed4','Ed5'):
        payload[f'movie/{name}.srt']=build/'movie-subtitles'/f'{name}.srt'
    for name in ('EN05.TIM','EN07.TIM'):
        payload['jpn/Data/'+name]=build/'ending-caption-fix/jpn/Data'/name
    payload['jpn/Item_m2/TEXTM_P0.TIM']=mod/'ITEM_M2/TEXTM_P0.TIM'
    payload['korean_subtitle.dll']=build/'korean_subtitle.dll'
    payload['korean_subtitle.ini']=ROOT/'korean_subtitle.ini'
    payload['README.txt']=ROOT/'packaging/README.txt'
    for name,path in payload.items():
        if not allowed_path(name) or path.is_symlink() or not path.is_file():
            raise ValueError(f'Unexpected release file: {name}')
    data=payload['korean_subtitle.dll'].read_bytes()
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[:2]!=b'MZ' or data[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',data,pe+4)[0]!=0x14c:
        raise ValueError('Renderer must be a 32-bit Windows PE DLL')
    if data!=payload['mod_korean_translation/korean_subtitle.dll'].read_bytes():
        raise ValueError('Root and mod renderer DLLs differ')
    coverage=json.loads((mod/'coverage.json').read_text(encoding='utf-8'))
    if coverage['visible_source_codes'] or not coverage['sentences'] or not coverage['textures']:
        raise ValueError('Subtitle coverage is incomplete')
    return payload,coverage


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist')
    args=parser.parse_args()
    # Validate all input environment paths before removing prior generated intermediates.
    import build_paths
    version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',version):
        raise ValueError('Invalid VERSION')
    build=ROOT/'build'
    if build.is_symlink():
        raise ValueError('Build directory must not be a symlink')
    if build.exists():shutil.rmtree(build)
    build.mkdir()
    for script in ('build_all_subtitles.py','build_document_hd.py','build_movie_subtitles.py','build_ending_captions.py'):
        subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,check=True)
    payload,coverage=collect_payload()
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    status=subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True)
    metadata={'project':PROJECT,'version':version,'source_commit':commit.stdout.strip() if commit.returncode==0 else None,
              'source_dirty':bool(status.stdout.strip()),
              'sentences':coverage['sentences'],'tiles_per_mode':coverage['textures']}
    manifest=build/'release.json';manifest.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    payload['release.json']=manifest
    args.output_dir.mkdir(parents=True,exist_ok=True)
    target=args.output_dir/f'Resident-Evil-Korean-HD-Translation-{version}.zip'
    with tempfile.TemporaryDirectory(dir=args.output_dir) as directory:
        staged=Path(directory)/target.name
        with zipfile.ZipFile(staged,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for name,path in sorted(payload.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                archive.writestr(info,path.read_bytes())
        os.replace(staged,target)
    target.with_suffix('.zip.sha256').unlink(missing_ok=True)
    print(json.dumps({'package':target.name,'files':len(payload),'bytes':target.stat().st_size}))


if __name__=='__main__':main()
