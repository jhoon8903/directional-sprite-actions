---
name: directional-sprite-actions
description: 사람·동물·몬스터·오브젝트의 승인된 원화와 방향별 포즈를 재사용해 요청한 임의의 게임 액션을 추가하거나 특정 프레임을 수정하고, 정렬된 시트·재생 미리보기·프레임 시간을 내보낼 때 사용한다.
---

# 방향별 픽셀 액션

사용자의 캐릭터 작업 폴더에 원본과 결과를 둔다. 이 스킬의 설치 폴더는 도구 위치다. 프로젝트에 game-asset-pipeline이나 pixel-pipeline 제작 규칙이 있으면 해당 규칙과 승인된 원화를 사용한다. 외부 사용자는 이 저장소만으로도 CLI를 실행할 수 있다.

1. 원화에서 몸 구조, 이동 방식, 바닥 접촉 또는 부유 중심, 방향별로 식별할 꼬리·날개·도구와 카메라 각도를 확인한다. 종족보다 실제 동작으로 프로필을 고른다. 같은 새도 걸을 때와 날 때 필요한 키포즈가 다르다. 캐릭터마다 작업 폴더 하나를 쓴다. 처음에만 `scripts/actions.py init PROJECT --size 64 --motion PROFILE`를 실행한다. 64는 예시다. biped, quadruped, flying, hopping, slithering 또는 사용자 정의 ID를 쓴다. 여러 방식으로 움직이는 대상은 기존 작업 폴더에서 add로 동작을 추가한다. 방향은 화면 기준이며 프로젝트의 character.json 순서가 시트 행 순서를 결정한다. 원본을 넣기 전에 확정한다.
2. `scripts/actions.py list PROJECT`로 기존 액션을 확인한다. 새 동작은 사용자 표현에서 구체적인 동작 ID와 키포즈, 각 포즈의 지속 시간, 반복 여부를 정해 `scripts/actions.py add PROJECT ACTION POSE:MS ... [--loop]`로 등록한다. 예를 들어 재료 볶기는 들어올림·뒤집기·받기를 반복하고, 맛보기는 한 번 재생한 뒤 정지 포즈로 복귀한다. 기존 포즈를 다시 쓰면 같은 이름 또는 `@idle/stand` 참조를 사용한다. 이후 `scripts/actions.py plan PROJECT ACTION`으로 누락된 방향·포즈를 확인한다. 요청이 특정 프레임 수정이면 해당 PNG만 교체하고 다시 빌드한다. 승인 전 생성본은 작업 폴더의 drafts/에, 승인된 셀만 frames/에 둔다. 정규 격자 시트는 `import-sheet PROJECT ACTION PNG`로 등록한다. 행은 방향, 열은 시간이다. 자유 배치 콘택트시트는 먼저 같은 기준점의 정사각 셀로 정렬한다.
3. 필요한 포즈를 만든다. 정지 포즈와 같은 방향의 직전 승인 프레임을 이미지 도구에 실제로 전달한다. 사용할 수 있는 이미지 도구 또는 작가가 그린 PNG를 사용한다. 여러 방향 한꺼번에 다시 그리는 비용을 피하려면 대표 방향에서 실루엣과 타이밍을 먼저 정한 후 빠진 포즈만 제작한다. 좌우 손이 다른 캐릭터는 반전할 때 장비·가림 순서를 보정한다.
   - 이동은 이동 방식마다 검수한다. 두발 걷기는 지지발을, 네발 속보는 대각 발쌍의 접지를, 비행은 날갯짓과 몸 중심을, 점프는 압축·이륙·착지를, 뱀은 몸통에서 꼬리까지 이어지는 굴곡을 본다. 긴 꼬리나 펼친 날개까지 담을 공통 셀을 잡는다.
   - 공격은 무기·공격 방식에 맞춰 준비, 타격, 후속 동작, 복귀를 설계한다. 프라이팬 휘두르기라면 타격 키포즈에서 팬의 이동 궤적과 손잡이 위치가 읽혀야 한다. 전체 동작을 담는 공통 셀을 정하고 동작의 기준점을 유지한다.
   - 피격은 간단한 반동이면 `scripts/draft_hit.py PROJECT PROJECT/drafts/hit.png`로 승인된 idle/stand에서 눌림·밀림·복귀를 만든다. 공격이 정면에서 들어오는 연출이며 옷이나 표정 변화가 필요하면 해당 키포즈만 다시 그린다. 시트 승인 후 import-sheet로 등록한다.
4. 한 방향만 준비됐으면 `scripts/actions.py build PROJECT ACTION --direction SE`로 먼저 재생한다. 마무리할 때 `scripts/actions.py build PROJECT ACTION`을 실행하고 GIF를 실제 속도로 본다. 각 대상에서 중요한 접지·부유, 사지 개수, 비대칭 무늬·부속물 가림과 셀 경계를 확인한다. sheet.png, preview.gif, clip.json과 미검증 사항을 전달한다. Unity에서는 Multiple / Grid by Cell Size로 셀을 나눈다. 별도 요청이 있을 때만 Animator나 씬까지 작업한다.

명령은 스킬 루트 기준이며 설치 폴더의 .venv/bin/python이 있으면 그 인터프리터로 실행한다(Windows는 .venv/Scripts/python.exe). 설치·호출 예제와 새 액션 정의는 [README](README.md)에 있다.
