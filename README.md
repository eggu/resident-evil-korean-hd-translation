# Resident Evil - Korean HD Translation

GOG 일본어판 Resident Evil과 [Classic REbirth 1.1.4](https://classicrebirth.com/index.php/re1cb-changelog/)용 한글 HD 번역 모드입니다. 게임 대사·메뉴·문서·영상 자막을 포함합니다. REbirth 1.1.3은 지원하지 않습니다.

배포 ZIP은 게임 폴더에 그대로 복사하는 형식입니다. HD 문서에는 REbirth의 HD Loader가 필요합니다. 모드 표시 이름은 **Resident Evil - Korean HD Translation**입니다. 모드 폴더 이름은 `mod_korean_translation`입니다.

## 처음 설치하는 분을 위한 안내

아래 순서대로 진행하세요. **추천은 방법 2(RE:Enhance + REbirth 1.1.4)**입니다. 그림과 영상 품질도 함께 개선됩니다. 방법 1은 원래 게임 화면을 유지하면서 한글패치를 설치하는 방법입니다.

### 0. 준비하기

1. 게임을 구입하고 설치합니다. 필요한 게임은 **1996년 원작 PC판**입니다. `Resident Evil HD REMASTER`는 다른 게임입니다.
   - [GOG Resident Evil 구입 페이지](https://www.gog.com/en/game/resident_evil)
   - [Steam Resident Evil (1996) 구입 페이지](https://store.steampowered.com/app/4249100/Resident_Evil_1996/)
2. 게임이 실행 중이면 종료합니다. 처음 설치한다면 게임을 한 번 실행해서 정상적으로 켜지는지 확인하고 종료하세요.
3. 앞으로 파일을 복사하기 전에 게임 폴더 전체를 다른 곳에 복사해 두세요. 문제가 생겼을 때 이 복사본으로 되돌릴 수 있습니다.
4. ZIP 파일은 압축된 상자입니다. 다운로드한 ZIP을 마우스 오른쪽 버튼으로 눌러 **모두 압축 풀기**를 선택합니다. 복사할 때는 압축을 푼 폴더 안으로 들어가 `Ctrl+A` → `Ctrl+C`를 누르고, 붙여넣을 폴더에서 `Ctrl+V`를 누르세요. 같은 이름의 파일이 있다는 창이 나오면 **대상 폴더의 파일 덮어쓰기/바꾸기**를 선택합니다.

### 1. 일본어 게임 파일과 설치 폴더 준비

#### GOG

1. 설치할 때 언어를 **Japanese / 日本語 / 일본어**로 선택합니다.
2. 이미 다른 언어로 설치했다면 GOG GALAXY에서 게임을 오른쪽 클릭 → **설치 관리(Manage installation)** → **설정(Configure)** → 언어를 일본어로 변경하고 다운로드가 끝날 때까지 기다립니다. [GOG 공식 언어 변경 안내](https://support.gog.com/hc/en-us/articles/360003935197-How-can-I-change-a-GOG-game-s-language)
3. 게임을 오른쪽 클릭 → **설치 관리** → **폴더 표시(Show folder)**를 엽니다. 오프라인 설치 파일을 사용했다면 설치할 때 지정한 폴더를 엽니다.
4. `Biohazard.exe` 파일과 `jpn` 폴더가 있는지 확인합니다. **이 폴더를 아래에서 ‘게임 폴더’라고 부릅니다.**

#### Steam

1. Steam에서 위의 **Resident Evil (1996)**을 설치합니다.
2. 라이브러리에서 게임을 오른쪽 클릭 → **관리(Manage)** → **로컬 파일 보기(Browse local files)**를 누릅니다.
3. 이곳은 **Steam 루트 폴더**입니다. 그 안의 `japanese` 폴더를 엽니다.
4. `japanese` 안에 `Biohazard.exe`와 `jpn` 폴더가 있는지 확인합니다. **Steam에서는 이 `japanese` 폴더가 ‘게임 폴더’입니다.** 한글패치와 RE:Enhance는 여기에 넣습니다. Steam의 화면 언어를 바꾸는 것만으로는 설치 위치를 대신할 수 없습니다.

```text
GOG 설치 폴더 = 게임 폴더
  Biohazard.exe
  jpn/

Steam 루트 폴더
  4249100_Launcher.exe
  japanese/                 ← Steam의 게임 폴더
    Biohazard.exe
    jpn/
```

### 방법 1. Classic REbirth 1.1.4만 설치하기

#### GOG

1. [공식 Biohazard PC CD-ROM 1.01 패치 페이지](https://classicrebirth.com/index.php/download/biohazard-pc-cd-rom-patch-version-1-01/)에서 패치를 다운로드하고 압축을 풉니다. REbirth가 사용하는 일본어 1.01 실행 파일을 준비하는 단계입니다.
2. 압축 안의 `Biohazard.exe`를 **게임 폴더**에 복사하고 기존 파일을 바꿉니다.
3. [Classic REbirth 공식 다운로드 페이지](https://classicrebirth.com/index.php/download/resident-evil-dll-fix-for-classic-edition/)에서 **Resident Evil Classic REbirth 1.1.4** 일반 패키지를 다운로드합니다. Steam 전용 파일은 이 경우 선택하지 않습니다.
4. 압축 안의 `ddraw.dll`, `SDL3.dll`, `gamecontrollerdb.txt` 등 **내용물 전체**를 게임 폴더에 복사합니다. 다운로드 폴더 자체를 통째로 넣으면 안 됩니다. `Biohazard.exe` 바로 옆에 `ddraw.dll`이 있어야 합니다.
5. 아래 **‘마지막 단계. 한글패치 설치’**로 이동합니다.

#### Steam

1. [Classic REbirth 공식 다운로드 페이지](https://classicrebirth.com/index.php/download/resident-evil-dll-fix-for-classic-edition/)에서 **1.1.4의 Steam 전용 패키지**를 다운로드합니다.
2. 압축을 풀면 `4249100_Launcher.exe`와 `japanese` 폴더가 나옵니다.
3. 이 두 항목을 **Steam 루트 폴더**에 복사하고 덮어씁니다. 패키지의 `japanese` 폴더가 게임의 `japanese` 폴더와 합쳐져야 합니다.
4. 확인: Steam 루트에는 새 `4249100_Launcher.exe`, 그 안의 `japanese`에는 `ddraw.dll`, `SDL3.dll`, `gamecontrollerdb.txt`가 있어야 합니다.
5. 아래 한글패치 설치에서는 **`japanese` 안에** 파일을 붙여넣습니다. `japanese`의 내용물을 루트로 옮기거나 게임 실행 파일 이름을 바꾸지 마세요.

### 방법 2. RE:Enhance 설치 후 REbirth 1.1.4로 업데이트하기 — 추천

1. [RE:Enhance v2 GOG 전체 패키지 다운로드 페이지](https://www.moddb.com/downloads/re-enhance-re1-v2-for-gog-version)를 엽니다. **Download**를 누르고 다운로드가 끝날 때까지 기다립니다. 파일 이름은 `RE-ENHANCE_RE1_v2.0_GOG.zip`이며 약 2.14GB입니다. 이 전체 패키지는 HD 모드와 고화질 영상도 포함합니다. 별도의 작은 텍스처 전용 패키지는 처음 설치하는 분의 선택지가 아닙니다.
2. 압축을 풉니다. `Biohazard.exe` 등 게임 파일이 들어 있는 위치까지 들어갑니다.
3. **내용물 전체**를 위에서 확인한 **게임 폴더**에 복사하고 덮어씁니다. GOG는 `Biohazard.exe`가 있는 설치 폴더, Steam은 `japanese` 안입니다.
4. RE:Enhance에 포함된 REbirth를 최신 지원 버전인 **1.1.4로 업데이트**합니다.
   - **GOG:** [Classic REbirth 공식 다운로드 페이지](https://classicrebirth.com/index.php/download/resident-evil-dll-fix-for-classic-edition/)에서 1.1.4 일반 패키지를 받고 압축 안의 내용물을 **게임 폴더**에 복사합니다.
   - **Steam:** 같은 페이지에서 **1.1.4 Steam 전용 패키지**를 받아 `4249100_Launcher.exe`와 `japanese` 폴더를 **Steam 루트 폴더**에 복사합니다. 위 방법 1의 Steam 설치와 같은 위치입니다.
5. RE:Enhance가 넣은 `Biohazard.exe`는 그대로 둡니다. **방법 1의 1.01 실행 파일 패치를 다시 덮어쓰지 마세요.** RE:Enhance에는 준비된 실행 파일이 포함되어 있습니다.
6. 아래 한글패치를 **마지막으로** 설치합니다. 이후 RE:Enhance나 REbirth를 다시 덮어쓰면 한글패치 파일이 바뀔 수 있으므로 한글패치를 다시 설치해야 합니다.

참고: [RE:Enhance 제작자 페이지](https://www.moddb.com/mods/reenhance-re1), [제작자의 Steam 설치 안내](https://www.moddb.com/mods/reenhance-re1/tutorials/reenhance-re1-for-the-steam-version). 제작자의 이전 Steam 안내와 달리, 여기서는 최신 REbirth 1.1.4 공식 Steam 런처 패키지를 사용하여 `japanese` 폴더 구조를 유지합니다.

### 마지막 단계. 한글패치 설치 — 두 방법 공통

1. [한글패치 최신 Release 다운로드 페이지](https://github.com/eggu/resident-evil-korean-hd-translation/releases/latest)를 엽니다.
2. 페이지 아래 **Assets**에서 `Resident-Evil-Korean-HD-Translation-1.0.1.zip`을 클릭해 다운로드합니다. GitHub 로그인은 필요하지 않습니다. `Source code`는 설치용 한글패치가 아니므로 선택하지 마세요.
3. 받은 ZIP을 마우스 오른쪽 버튼으로 눌러 **모두 압축 풀기**를 선택합니다.
4. 압축을 푼 폴더 안에 다음 항목이 보이면 맞게 연 것입니다. **이 항목 전체**를 게임 폴더에 복사하고 덮어씁니다.

```text
게임 폴더/                   ← Biohazard.exe가 있는 곳
  ddraw.dll                  ← 앞에서 설치한 REbirth 1.1.4
  korean_subtitle.dll        ← 한글패치의 렌더러
  korean_subtitle.ini
  mod_korean_translation/
  hires/
  jpn/
  movie/
```

5. GOG는 `Biohazard.exe`로, Steam은 Steam 라이브러리의 **플레이**로 실행합니다.
6. REbirth 설정 창에서 아래처럼 설정합니다.
   - **Enable HD loader:** 켜기
   - **Retro Mode:** 끄기
   - **Enable Japanese:** 끄기 — 원본 게임 파일은 일본어판을 쓰지만, 이 설정은 한글 모드에 맞춰 끕니다.
   - **Enable movies:** 켜기
7. **MOD SELECTION**에서 **Resident Evil - Korean HD Translation**을 체크합니다. 다른 번역 모드가 체크되어 있으면 체크를 해제하세요. **OK**를 눌러 게임을 시작합니다.
8. 새 게임을 시작해서 대사가 한글로 나오는지, 문서가 한글로 열리는지 확인합니다.

### 잘 안 될 때

- **모드 이름이 안 보임:** `mod_korean_translation`이 `Biohazard.exe` 바로 옆에 있는지 확인합니다. `게임 폴더/압축을 푼 폴더/mod_korean_translation`처럼 한 단계 더 안에 넣었다면 내용물을 게임 폴더로 옮깁니다.
- **문서가 원문이거나 작게 보임:** `Enable HD loader`를 켜고 `Retro Mode`를 끈 뒤 다시 실행합니다.
- **대사가 원문으로 나옴:** 한글 모드가 체크되어 있는지 확인하고, 한글패치의 `korean_subtitle.dll`과 모드 폴더를 모두 복사했는지 확인합니다.
- **영상 자막 글꼴이 이상함:** 아래 ‘영상 자막 폰트’ 안내를 확인합니다. 설정을 바꾼 다음에는 게임을 완전히 종료하고 다시 실행합니다.
- **Steam에서 실행되지 않음:** 루트의 런처와 `japanese` 안의 DLL 위치를 위 그림과 비교합니다. 위치가 맞아도 문제가 남으면 사용한 버전과 오류를 알려주세요.

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

결과: `dist/Resident-Evil-Korean-HD-Translation-1.0.1.zip`. 버전은 `VERSION`에서 관리합니다.

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
