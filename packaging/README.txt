Resident Evil 한글 HD 번역 (1.1.1)
https://github.com/eggu/resident-evil-korean-hd-translation

필요한 것
- GOG판 또는 Steam판 Resident Evil(1996), 일본어로 설치
- Classic REbirth 1.1.4(권장) 또는 1.1.3
  1.1.3에서는 영상에 한글 자막이 나오지 않습니다. Steam판은 1.1.4만 지원합니다.

설치
1. 게임을 끕니다.
2. 이 ZIP의 내용물 전체를 Biohazard.exe가 있는 폴더에 덮어씁니다.
   (Steam판은 게임 설치 폴더 안의 japanese 폴더)
3. 게임을 실행하고 REbirth 설정을 아래처럼 맞춥니다.
   Enable HD loader 켜기 / Retro Mode 끄기 / Enable Japanese 끄기 / Enable movies 켜기
4. MOD SELECTION에서 Resident Evil - Korean HD Translation을 체크하고 시작합니다.

선택 사항: 모드 선택 창 건너뛰기
optional 폴더의 winmm.dll을 Biohazard.exe 옆으로 옮기면 한글 모드가 자동으로 켜집니다.
모드 선택 창이 필요할 때는 Shift를 누른 채 실행합니다.
Mac·Linux(Wine 계열)에서는 winmm을 native, builtin으로 설정해야 동작합니다.

영상 자막 글꼴 바꾸기 (REbirth 1.1.4)
korean_subtitle.ini의 [MovieSubtitles] Fonts 줄을 고칩니다.
글꼴 파일을 ; 로 구분해 적으면 앞에서부터 차례로 시도합니다. 기본값은 바탕(batang.ttc)입니다.
파일 이름만 쓰면 Windows 글꼴 폴더에서, 경로를 쓰면 그 위치에서 찾습니다.
예: Fonts = fonts\my-serif.ttf;batang.ttc
고친 뒤 게임을 다시 시작하세요. 대사와 문서 글꼴은 바뀌지 않습니다.
