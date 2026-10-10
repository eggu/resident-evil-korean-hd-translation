# Resident Evil - Korean HD Translation

GOG 일본어판 Resident Evil과 [Classic REbirth 1.1.4](https://classicrebirth.com/index.php/re1cb-changelog/)용 한글 HD 번역 모드입니다. 게임 대사·메뉴·문서·영상 자막을 포함합니다. REbirth 1.1.3은 지원하지 않습니다.

배포 ZIP은 게임 폴더에 그대로 복사하는 형식입니다. HD 문서에는 REbirth의 HD Loader가 필요합니다. 모드 표시 이름은 **Resident Evil - Korean HD Translation**입니다. 모드 폴더 이름은 `mod_korean_translation`입니다.

## 소스에서 직접 빌드

본인이 가진 원본 게임 자료로 빌드할 수 있습니다. Python 3.12 이상과 아래 원본 파일이 필요합니다.

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

`RE1_GAME_ORIGINAL_DIR`는 필수이며 설치 폴더를 자동 추측하지 않습니다. `RE1_BUILD_FONT`는 TTF/OTF/TTC 파일 경로입니다. 기본값은 macOS의 AppleMyungjo, Windows의 Batang이고 Linux에서는 직접 지정해야 합니다. TTC는 첫 번째 face를 사용합니다. 다른 폰트의 글리프 누락·넘침은 생성 단계에서 검사하며 이미지 배치는 달라질 수 있습니다.

결과: `dist/Resident-Evil-Korean-HD-Translation-R9.zip`. 버전은 `VERSION`에서 관리합니다.

## 번역과 생성 코드

- `translation/dialogue.csv`, `messages.csv`, `resources.csv`: 검수하는 번역 원본
- `translation/layout.json`, `resource_layout.json`: 원문·메시지 슬롯·제어 코드 기준 자료
- `translation/movie_subtitles.json`, `movie_durations.json`: 영상 자막과 원본 10fps 시간표
- `source/encoding.xml`: [RE1 Mod SDK](https://github.com/Gemini-Loboto3/RE1-Mod-SDK)의 기본 문자 매핑 소스
- `build_*.py`: 현재 버전의 대사 타일·문서·영상 자막 생성기
- `src/`: 현재 렌더러와 영상 폰트 설정 코드
- `scripts/package_release.py`: 전체 생성과 복사용 ZIP 패키징

## 영상 자막 폰트

게임 루트의 `korean_subtitle.ini`에서 `[MovieSubtitles] Fonts`를 편집합니다. 세미콜론으로 구분한 파일을 왼쪽부터 시도하며 기본 첫 후보는 Windows 바탕 `batang.ttc`입니다. 파일명만 쓰면 Windows Fonts 폴더에서, 경로를 쓰면 해당 위치에서 찾습니다. 변경 뒤 게임을 재시작합니다. 이 설정은 영상 SRT에만 적용되며 이미지로 생성된 게임 대사와 문서에는 적용되지 않습니다.
