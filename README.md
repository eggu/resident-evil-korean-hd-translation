# Resident Evil - Korean HD Translation

GOG 일본어판 Resident Evil과 [Classic REbirth 1.1.4](https://classicrebirth.com/index.php/re1cb-changelog/)용 한글 HD 번역 모드입니다. 게임 대사·메뉴·문서·영상 자막을 포함합니다. 현재 실게임 확인 환경은 macOS/Wine입니다.

배포 ZIP은 게임 폴더에 그대로 복사하는 형식입니다. 별도 설치·제거 프로그램은 없으며, 사용자 설정·세이브·게임 실행 파일·성능 모드·영상·폰트 파일은 포함하지 않습니다. HD 문서에는 REbirth의 HD Loader가 필요합니다. 모드 표시 이름은 **Resident Evil - Korean HD Translation**입니다. 기존 프리셋과의 호환을 위해 폴더 이름 `mod_korean_serif`는 유지합니다.

## 소스에서 직접 빌드

저장소 Secret이나 CI 입력 파일 없이, 본인이 가진 원본 게임 자료로 빌드할 수 있습니다. Python 3.12 이상과 아래 원본 파일이 필요합니다.

```text
원본 게임 폴더/
  ddraw.dll                       # Classic REbirth 1.1.4
  jpn/Data/PBFONT1.TIM
  jpn/Data/EN05.TIM
  jpn/Data/EN07.TIM
  jpn/Item_m2/TEXTM_*.TIM
```

이미 한글패치를 덮어쓴 문서·엔딩 파일은 원본 입력으로 사용할 수 없습니다. 원본 폴더는 읽기만 하며, 출력은 저장소의 `build/`와 `dist/`에만 작성합니다. 지원 버전과 원본 해시가 다르면 빌드를 중단합니다. 문서 기본 PNG는 해당 REbirth DLL의 기본 자료에서 추출합니다. 게임 영상 파일은 빌드에 필요하지 않습니다.

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export RE1_GAME_ORIGINAL_DIR="/path/to/original/Resident Evil"
# Linux 또는 다른 글꼴로 빌드할 때 지정:
export RE1_BUILD_FONT="/path/to/korean-font.ttf"
.venv/bin/python scripts/package_release.py
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:RE1_GAME_ORIGINAL_DIR = 'D:\Games\Resident Evil Original'
# 생략하면 Windows의 Fonts\batang.ttc를 사용:
$env:RE1_BUILD_FONT = 'C:\Windows\Fonts\batang.ttc'
.venv\Scripts\python.exe scripts\package_release.py
```

`RE1_GAME_ORIGINAL_DIR`는 필수이며 설치 폴더를 자동 추측하지 않습니다. `RE1_BUILD_FONT`는 TTF/OTF/TTC 파일 경로입니다. 기본값은 macOS의 AppleMyungjo, Windows의 Batang이고 Linux에서는 직접 지정해야 합니다. TTC는 첫 번째 face를 사용합니다. CI와 현재 검증된 이미지의 빌드 폰트는 AppleMyungjo입니다. 다른 폰트의 글리프 누락·넘침은 생성 단계에서 검사하며 이미지 배치는 달라질 수 있습니다.

결과: `dist/Resident-Evil-Korean-HD-Translation-R9.zip`과 ZIP SHA-256 파일. ZIP 내부에는 파일별 `SHA256SUMS.txt`와 소스·폰트 해시를 기록한 `release.json`이 있습니다. 버전은 `VERSION`에서 관리합니다.

## 번역과 생성 코드

- `translation/dialogue.csv`, `messages.csv`, `resources.csv`: 검수하는 번역 원본
- `translation/layout.json`, `resource_layout.json`: 원문·메시지 슬롯·제어 코드 기준 자료
- `translation/movie_subtitles.json`, `movie_durations.json`: 영상 자막과 원본 10fps 시간표
- `source/encoding.xml`: [RE1 Mod SDK](https://github.com/Gemini-Loboto3/RE1-Mod-SDK)의 기본 문자 매핑 소스
- `build_*.py`: 현재 버전의 대사 타일·문서·영상 자막 생성기
- `src/`: 현재 렌더러와 영상 폰트 설정 코드
- `scripts/package_release.py`: 전체 생성과 복사용 ZIP 패키징

생성된 DLL, TIM, PNG, WebP, SRT, `sentence_records.h`, ZIP과 중간 산출물은 커밋하지 않습니다. 예전 버전·실험 렌더러·설치 도구·게임 원본·개인 경로·백업도 저장소에 포함하지 않습니다.

## 영상 자막 폰트

게임 루트의 `korean_subtitle.ini`에서 `[MovieSubtitles] Fonts`를 편집합니다. 세미콜론으로 구분한 파일을 왼쪽부터 시도하며 기본 첫 후보는 Windows 바탕 `batang.ttc`입니다. 파일명만 쓰면 Windows Fonts 폴더에서, 경로를 쓰면 해당 위치에서 찾습니다. 변경 뒤 게임을 재시작합니다. 이 설정은 영상 SRT에만 적용되며 이미지로 생성된 게임 대사와 문서에는 적용되지 않습니다.

## 검증과 GitHub Actions

로컬 빌드 후:

```sh
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
```

네이티브 호출 검증은 같은 원본 경로에 지원되는 `Biohazard.exe`와 RE:Enhance `bio1hd.asi`가 있을 때 실행합니다.

```sh
.venv/bin/python verification/check_markers.py
.venv/bin/python verification/check_hd_sd.py
.venv/bin/python verification/check_config_screen.py
.venv/bin/python verification/check_empty_box.py
.venv/bin/python verification/check_movie_outline.py
.venv/bin/python verification/check_movie_font.py
```

원래 x86 호출·인자·스택·텍스처·메뉴 경로를 에뮬레이션합니다. GPU/드라이버와 실제 게임 화면 검증을 대체하지 않습니다.

[Build release package](https://github.com/eggu/resident-evil-korean-hd-translation/actions/workflows/package.yml)는 main push 또는 수동 실행에서 동일한 생성·패키징 스크립트와 검증을 실행하고, 성공한 `dist/`만 Artifact로 업로드합니다. 생성 결과를 Git에 다시 커밋하지 않습니다.

GitHub 호스팅 러너에는 게임 원본이 없어, 이 저장소의 CI만 비공개 draft release `ci-build-inputs`의 암호화된 원본 픽스처와 `BUILD_INPUTS_KEY` Secret을 사용합니다. 복호화된 입력 경로를 `RE1_GAME_ORIGINAL_DIR`/`RE1_BUILD_FONT`로 넘기는 준비 단계이며, 로컬 빌더와 분리되어 있습니다. 원본·폰트·Secret과 복호화된 입력은 공개하거나 Artifact로 올리지 않습니다. 포크에서는 본인 원본 경로를 제공하는 러너를 구성하거나 로컬 명령으로 빌드할 수 있습니다.
