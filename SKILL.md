---
name: directional-sprite-actions
description: 승인한 픽셀 캐릭터와 방향별 포즈를 재사용해 걷기·공격·피격 등 게임 액션을 추가하거나 특정 프레임을 수정하고, 정렬된 시트·재생 미리보기·프레임 시간을 내보낼 때 사용한다.
---

# 방향별 픽셀 액션

사용자의 캐릭터 작업 폴더에 원본과 결과를 둔다. 이 스킬의 설치 폴더는 도구 위치다. 프로젝트에 game-asset-pipeline이나 pixel-pipeline 제작 규칙이 있으면 해당 규칙과 승인된 원화를 사용한다. 외부 사용자는 이 저장소만으로도 CLI를 실행할 수 있다.

1. 승인된 전신 원화, 방향별 정지 포즈, 게임의 셀 크기·발 기준점·장비 손·카메라 각도를 확인한다. 캐릭터마다 작업 폴더 하나를 쓴다. 처음에만 `scripts/actions.py init PROJECT --size 64`를 실행한다. 64는 예시다. 방향은 화면 기준이며 프로젝트의 character.json 순서가 시트 행 순서를 결정한다. 원본을 넣기 전에 확정한다.
2. `scripts/actions.py plan PROJECT ACTION`으로 누락된 방향·포즈를 확인한다. 요청이 특정 프레임 수정이면 해당 PNG만 교체하고 다시 빌드한다. 승인 전 생성본은 작업 폴더의 drafts/에, 승인된 셀만 frames/에 둔다. 정규 격자 시트는 `import-sheet PROJECT ACTION PNG`로 등록한다. 행은 방향, 열은 시간이다. 자유 배치 콘택트시트는 먼저 같은 기준점의 정사각 셀로 정렬한다.
3. 필요한 포즈를 만든다. 정지 포즈와 같은 방향의 직전 승인 프레임을 이미지 도구에 실제로 전달한다. 사용할 수 있는 이미지 도구 또는 작가가 그린 PNG를 사용한다. 여러 방향 한꺼번에 다시 그리는 비용을 피하려면 대표 방향에서 실루엣과 타이밍을 먼저 정한 후 빠진 포즈만 제작한다. 좌우 손이 다른 캐릭터는 반전할 때 장비·가림 순서를 보정한다.
   - 걷기는 양발의 교차와 지지발 위치, 마지막에서 첫 프레임으로 돌아가는 연결을 확인한다.
   - 공격은 무기·공격 방식에 맞춰 준비, 타격, 후속 동작, 복귀를 설계한다. 프라이팬 휘두르기라면 타격 키포즈에서 팬의 이동 궤적과 손잡이 위치가 읽혀야 한다. 전체 동작을 담는 공통 셀을 정하고 발의 축을 유지한다.
   - 피격은 간단한 반동이면 `scripts/draft_hit.py PROJECT PROJECT/drafts/hit.png`로 승인된 idle/stand에서 눌림·밀림·복귀를 만든다. 공격이 정면에서 들어오는 연출이며 옷이나 표정 변화가 필요하면 해당 키포즈만 다시 그린다. 시트 승인 후 import-sheet로 등록한다.
4. 한 방향만 준비됐으면 `scripts/actions.py build PROJECT ACTION --direction SE`로 먼저 재생한다. 마무리할 때 `scripts/actions.py build PROJECT ACTION`을 실행하고 GIF를 실제 속도로 본다. 손 바뀜, 발 미끄러짐, 뒤쪽에서 소품이 몸을 뚫는지, 공격 끝이 잘리는지 확인한다. sheet.png, preview.gif, clip.json과 미검증 사항을 전달한다. Unity에서는 Multiple / Grid by Cell Size로 셀을 나눈다. 별도 요청이 있을 때만 Animator나 씬까지 작업한다.

명령은 스킬 루트 기준이며 설치 폴더의 .venv/bin/python이 있으면 그 인터프리터로 실행한다(Windows는 .venv/Scripts/python.exe). 설치·호출 예제와 새 액션 정의는 [README](README.md)에 있다.
