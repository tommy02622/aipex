# AIPEX

AIPEX는 F1 게임 텔레메트리와 FastF1 레퍼런스 랩을 결합해 주행을 분석하고, 경기 종료 후 코칭 리포트를 제공하는 프로젝트입니다.

## 저장소 구성

```text
aipex/
├─ index.html
├─ README.md
├─ scripts/
│  └─ build_fastf1_game_compatible.py
├─ docs/
│  └─ fastf1-game-compatible.md
└─ data/
   └─ reference/
      └─ japan/
         ├─ japan_ground_truth_5m.csv
         ├─ japan_reference_expanded_5m.csv
         └─ japan_reference_game_compatible_5m.csv
```

## 파일 설명

### `index.html`
- 경기 종료 후 분석 화면 데모입니다.
- 발표에서 post-session 결과 UI를 보여줄 때 사용합니다.

### `scripts/build_fastf1_game_compatible.py`
- FastF1 일본 스즈카 기준랩을 최신 게임 원본 `analysis_frames` 형식에 맞게 변환하는 스크립트입니다.
- `steer`, `g_lat`, `g_long`은 계산 기반 추정값으로 생성합니다.

### `docs/fastf1-game-compatible.md`
- 어떤 컬럼이 FastF1 실값인지, 어떤 컬럼이 추정값인지, 어떤 컬럼이 placeholder인지 설명한 문서입니다.

### `data/reference/japan/japan_ground_truth_5m.csv`
- 최소형 기준 데이터입니다.
- 포함 컬럼:
  - `lap_distance_m`
  - `speed_kph`
  - `throttle`
  - `brake`

### `data/reference/japan/japan_reference_expanded_5m.csv`
- 확장형 기준 데이터입니다.
- 최소형 데이터에 더해 `gear`, `rpm`, `pos_x`, `pos_z`, `sector`, `session_time` 등이 포함됩니다.

### `data/reference/japan/japan_reference_game_compatible_5m.csv`
- 최신 게임 원본 `analysis_frames`와 같은 컬럼 구조를 갖는 호환 버전입니다.
- FastF1에 직접 없는 `steer`, `g_lat`, `g_long`은 계산 기반 추정값으로 채웠습니다.
- packet/join 관련 메타 컬럼은 형식 호환용 값으로 채웠습니다.

## 데이터 분류

### 1. FastF1 실값으로 채운 컬럼
- `session_time`
- `lap_num`
- `lap_distance_m`
- `total_distance_m`
- `sector`
- `speed_kph`
- `throttle`
- `brake`
- `gear`
- `rpm`
- `pos_x`
- `pos_z`

### 2. 계산 기반 추정 컬럼
- `steer`
  - 곡률 기반 `pseudo-steer`
- `g_lat`
  - `v^2 * curvature / g`
- `g_long`
  - `v * dv/ds / g`

### 3. 형식 호환용 컬럼
- `session_uid`
- `frame_id`
- `player_car_index`
- `lap_packet_seen`
- `lap_join_status`
- `lap_context_age_s`
- `lap_packet_frame_id`
- `lap_player_index`
- `lap_parser_version`
- `lap_parse_valid`
- `lap_join_defaulted`

## 실행 방법

### UI 확인
브라우저에서 `index.html`을 열면 됩니다.

### FastF1 호환 CSV 재생성
```powershell
python scripts/build_fastf1_game_compatible.py
```

## 비고

- 기준 reference는 일본 스즈카 FastF1 fastest lap 기준입니다.
- 기준 데이터는 거리축 `5m` 간격으로 보간되어 있습니다.
- 이 저장소에는 발표에 필요한 핵심 산출물만 남기고, 수집 원본/캐시/실험 파일은 제외했습니다.
