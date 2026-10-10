# 번역 소스

`dialogue.csv`, `messages.csv`, `resources.csv`의 번역문을 편집합니다. UTF-8 CSV이며 id·원문·제어 코드·원본 해시·파일 경로는 보존합니다.

`layout.json`은 PC 원문과 표시 슬롯을, `resource_layout.json`은 메뉴/아이템 원문과 순서를 고정합니다. 빈 원문/제어 슬롯을 제외한 번역 누락, 중복 id, 바뀐 원문·제어 코드·원본 문서, 미지원 글리프와 넘치는 배치는 빌드에서 거부합니다. 저장 파일 식별자와 Chris/Jill 표시는 ASCII를 유지합니다.

영상은 `movie_subtitles.json`의 원본 10fps 프레임 시간표와 `movie_durations.json`의 길이 기준으로 SRT를 생성합니다. 문서 암호 그림은 사용자가 지정한 원본에서 보존합니다. 패스 넘버의 두 번째 페이지는 숫자 배경을 보이는 투명 오버레이입니다.

생성된 XML·이미지·SRT·헤더는 이 디렉터리에 넣거나 커밋하지 않습니다. 생성과 배포 명령은 루트 README를 따릅니다.
