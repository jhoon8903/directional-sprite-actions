# Directional Sprite Actions

사람·동물·몬스터의 방향별 픽셀 포즈로 게임 액션을 제작하는 **Codex 스킬과 Python CLI**입니다. 승인된 PNG를 재사용해 원하는 방향만 먼저 검토하고, 전체 액션을 스프라이트시트로 묶습니다.

| 준비할 것 | 얻는 것 |
|---|---|
| 같은 크기의 투명 RGBA PNG 프레임 또는 규격화한 시트 | 방향별 시트 PNG, 재생 미리보기 GIF, 프레임 위치·시간·반복 여부를 담은 JSON |
| 방향별 정지 포즈 | CPU로 생성한 3프레임 피격 초안 |
| 신규 액션의 이름과 타이밍 | 필요한 포즈 목록. 새 그림은 이미지 도구로 만들거나 직접 그려 등록합니다. |

## 설치

Python 3.9 이상과 Pillow를 사용합니다. macOS와 Linux에서 저장소의 **Code → HTTPS** 주소를 복사한 후 실행하세요.

```sh
git clone <복사한-저장소-URL> ~/.codex/skills/directional-sprite-actions
cd ~/.codex/skills/directional-sprite-actions
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/actions.py --help
```

팀 프로젝트 안에 설치하려면 복제 경로를 `.agents/skills/directional-sprite-actions`로 바꾸세요. CLI만 쓸 때는 원하는 폴더에 복제해도 됩니다.

새 Codex 채팅에서 이렇게 요청할 수 있습니다.

> $directional-sprite-actions 승인한 요리 모험가에게 프라이팬 휘두르기 공격을 추가해줘. 오른손에 팬을 들고, 타격 포즈가 가장 잘 보이는 방향부터 보여줘.

## 기존 시트로 시작하기

아래 명령은 스킬 루트에서 실행합니다. `P`는 게임 밖의 캐릭터 제작 폴더로 설정해도 됩니다.

```sh
P=../cook-sprite-work
python scripts/actions.py init "$P" --size 64
python scripts/actions.py import-sheet "$P" walk /path/to/walk.png
python scripts/actions.py build "$P" walk
python scripts/actions.py plan "$P" attack
```

기본 행은 **S, SW, W, NW, N, NE, E, SE**이며, 화면 아래가 S입니다. 64px 캐릭터의 기본 걷기 시트는 4열 × 8행으로 256×512px입니다. 임포트 입력은 투명 배경의 RGBA PNG이며 방향·프레임 순서는 프로젝트 설정과 일치해야 합니다.

## 대상의 움직임 선택

`python scripts/actions.py init ./characters/wolf --size 64 --motion quadruped`로 시작합니다. 동물·몬스터라는 분류보다 실제 이동 방식을 고릅니다.

| 프로필 | 이동 시안에 쓸 기본 액션 | 검수 포인트 |
|---|---|---|
| biped (기본) | walk | 지지발과 반대발 |
| quadruped | trot | 대각선 발쌍이 교대로 닿는 속보 |
| flying | flap | 날개 끝의 여백과 몸 중심 |
| hopping | hop | 눌림·공중·착지 실루엣 |
| slithering | slither | 몸통과 꼬리의 굴곡 전파 |
| 임의 ID (예: mimic) | idle과 hit에서 시작해 add로 등록 | 뚜껑 경첩 등 대상 고유의 회전축 |

프로필은 처음에 복사하는 동작 정의입니다. 실제 그림은 대상 원화와 포즈를 사용합니다. 걷다가 나는 드래곤도 한 폴더에서 trot, flap, bite 등을 함께 관리할 수 있습니다. 기존 프로젝트는 그대로 열고 add로 확장합니다. 방향 수와 순서는 character.json의 directions로 지정합니다.

피격 초안의 눌림은 기본적으로 실루엣의 바닥을 고정합니다. flying은 실루엣 중심을 유지하며 초기화 시 `--anchor center` 또는 `--anchor ground`로 선택할 수 있습니다. 이 값은 절차적 눌림의 기준입니다. Unity 피벗은 프로젝트 임포트 설정에서 지정합니다.

## 원하는 액션 등록
게임에서 필요한 동작마다 ID, 키포즈 순서, 각 프레임의 시간(ms)을 정의합니다. 한 번 재생하는 것이 기본이며 반복 동작에는 `--loop`를 붙입니다.

```sh
python scripts/actions.py list "$P"
python scripts/actions.py add "$P" stir-fry lift:130 toss:80 catch:140 --loop
python scripts/actions.py add "$P" taste scoop:130 taste:220 @idle/stand:120
python scripts/actions.py plan "$P" taste
```

추가한 정의는 캐릭터 폴더의 `actions/<ID>.json`에 저장됩니다. 이 파일에서 타이밍과 순서를 조정할 수 있습니다. 키포즈가 준비되면 모든 액션에 같은 build 명령을 사용합니다. 예를 들어 SE의 scoop과 taste를 그리면 복귀 프레임은 기존 idle/stand를 읽습니다.

## 기본 프리셋

| 액션 | 기본 타이밍 | 제작 방법 |
|---|---|---|
| 정지 | 500ms | 방향별 기준 포즈 1장 |
| 걷기 | 140ms × 4 | 접지와 통과 포즈를 좌우 교대로 반복 |
| 공격 | 140 / 70 / 100 / 140ms | 준비 → 타격 → 후속 동작 → 복귀. 무기의 궤적을 키포즈로 제작 |
| 피격 | 80 / 100 / 120ms | 눌림 → 반동 → 복귀. 정지 포즈로 절차적 초안을 만들거나 직접 작화 |

정지 시트는 **1열 × 방향 수**입니다. 먼저 등록하면 피격 초안을 로컬에서 바로 만들 수 있습니다.

```sh
python scripts/actions.py import-sheet "$P" idle /path/to/idle-column.png
python scripts/draft_hit.py "$P" "$P/drafts/hit-v1.png" --distance 2
# 시안을 확인한 뒤
python scripts/actions.py import-sheet "$P" hit "$P/drafts/hit-v1.png"
python scripts/actions.py build "$P" hit
```

작업 폴더의 `actions.json`에 키를 추가하면 새 액션이 됩니다. 예를 들어 다음 항목을 추가하면 마법 시전 3프레임을 같은 방식으로 관리합니다.

```json
"cast": {"loop": false, "frames": [["gather", 180], ["release", 70], ["settle", 160]]}
```

승인된 포즈는 `frames/<액션>/<방향>/<프레임 이름>.png`에 둡니다. 예를 들어 동쪽 공격 타격만 고칠 때는 `frames/attack/E/strike.png`를 수정한 뒤 attack을 다시 빌드합니다. 원본 승인 자료와 생성 중인 시안을 따로 보관하면 다른 방향을 다시 그릴 필요가 없습니다.

## Unity에서 사용

`build/<액션>/sheet.png`를 Sprite (2D and UI) / Multiple / Point로 임포트하고 프로젝트 셀 크기로 자릅니다. `preview.gif`는 동작 확인용, `clip.json`은 방향·프레임 영역·재생 시간과 반복 여부를 전달하는 파일입니다. Unity Animation 창이나 프로젝트의 임포터에서 이 값을 적용합니다. 액션마다 발 기준점과 PPU를 통일합니다.

## 승인한 프레임 참조

여러 액션에서 같은 포즈를 쓰려면 프로젝트의 액션 정의에서 프레임 이름 대신 `@idle/stand`를 사용합니다. 예를 들어 공격의 마지막 항목을 `["@idle/stand", 140]`으로 바꾸면 방향별 정지 PNG를 직접 읽어 복귀 동작으로 재사용합니다. 공유 참조가 있는 액션은 원본 프레임을 각각 등록해 빌드합니다.

피격 생성기는 기존 시안을 덮어쓰지 않습니다. 반동을 다르게 시험할 때는 `hit-v2.png`처럼 새 이름을 지정합니다. 머리카락이나 무기가 잘릴 정도로 여백이 작으면 도구가 해당 방향을 알려줍니다.

처음 만드는 공격도 한 방향만 먼저 확인할 수 있습니다. SE 포즈들을 작성한 후 `python scripts/actions.py build "$P" attack --direction SE`를 실행하면 `build/attack/directions/SE/`에 그 방향의 시트와 GIF가 생성됩니다. 전체 빌드는 설정한 모든 방향의 입력이 준비된 뒤 실행합니다. clip.json의 rect 좌표는 PNG의 왼쪽 위가 원점입니다.
