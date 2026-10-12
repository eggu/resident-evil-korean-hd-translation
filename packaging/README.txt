Resident Evil - Korean HD Translation (1.0.1)

지원: GOG 일본어판 Resident Evil + Classic REbirth 1.1.4.
REbirth 1.1.3은 지원하지 않습니다.
HD 문서 이미지는 REbirth HD Loader를 활성화한 환경에서 사용합니다.

설치
1. 게임을 종료합니다.
2. ZIP의 내용을 게임 폴더에 폴더 구조 그대로 복사합니다.
3. REbirth 모드 선택에서 Resident Evil - Korean HD Translation을 선택합니다.

영상 자막 폰트
게임 폴더의 korean_subtitle.ini에서 [MovieSubtitles] Fonts를 수정합니다.
세미콜론으로 구분한 파일을 왼쪽부터 시도하며 첫 기본 후보는 Windows 바탕(batang.ttc)입니다.
파일명만 쓰면 Windows Fonts 폴더, 경로를 쓰면 게임 폴더 기준 상대 경로나 절대 경로에서 찾습니다.
예: Fonts = fonts\my-serif.ttf;batang.ttc;segoeuib.ttf
TTC는 첫 번째 face를 사용하며 영문 파일명/경로를 권장합니다. 수정 후 게임을 재시작합니다.
선택된 파일은 korean_subtitle.log의 Movie subtitle font: 줄에 기록됩니다.
모든 후보 로드가 실패하면 기존 REbirth 폰트 로더로 돌아갑니다.
게임 대사와 문서는 생성된 이미지이므로 이 INI로 글꼴을 변경할 수 없습니다.
