# AIPEX

AIPEX는 F1 게임 텔레메트리와 FastF1 레퍼런스 랩을 결합해 주행을 분석하고, 경기 종료 후 코칭 리포트를 제공하는 프로젝트입니다.

## 포함 파일

- `index.html`
  - 경기 종료 후 분석 화면 데모
- `build_fastf1_game_compatible.py`
  - FastF1 Japan 기준랩을 최신 게임 원본 `analysis_frames` 형식으로 변환하는 스크립트

## FastF1 기준 데이터

### 1. 최소형 정답 데이터
- `fastf1_reference_collection_2024_japan_q_fastest/ground_truth/ground_truth_japan_resampled_5m.csv`

설명:
- `lap_distance_m`, `speed_kph`, `throttle`, `brake`만 포함합니다.
- 모델에서 기준 신호만 간단히 쓰고 싶을 때 적합합니다.
- 거리축 기준 `5m` 간격 보간이 적용되어 있습니다.

### 2. 확장형 기준 데이터
- `fastf1_reference_collection_2024_japan_q_fastest/normalized/analysis_frames_fastf1_resampled_5m.csv`

설명:
- 최소형 데이터에 더해 `gear`, `rpm`, `pos_x`, `pos_z`, `sector`, `session_time` 등이 포함됩니다.
- FastF1 원본 정보를 게임 쪽 분석 파이프라인에 붙이기 쉽게 만든 버전입니다.
- `lap_time_s`, `drs` 같은 FastF1 편의 컬럼도 포함되어 있습니다.

### 3. 게임 원본 호환 기준 데이터
- `fastf1_reference_collection_2024_japan_q_fastest/normalized/analysis_frames_fastf1_resampled_5m_game_compatible.csv`

설명:
- 최신 게임 원본 파일 `collection_20260426_211750/normalized/analysis_frames_20260426_211750.csv`와 컬럼 구성이 동일합니다.
- `lap_time_s`, `drs`는 제거했습니다.
- FastF1에 없는 `steer`, `g_lat`, `g_long`은 계산 기반 추정값으로 채웠습니다.
- 게임 수집 파이프라인 메타 컬럼은 형식 호환을 위해 placeholder 값을 넣었습니다.

## 컬럼 처리 기준

### FastF1 실값
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

### 계산 기반 추정값
- `steer`
  - 위치 곡률로부터 pseudo-steer 추정
- `g_lat`
  - `v^2 * curvature / g`
- `g_long`
  - `v * dv/ds / g`

### 형식 호환용 placeholder
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

자세한 처리 기준은 아래 문서에 정리되어 있습니다.

- `fastf1_reference_collection_2024_japan_q_fastest/docs/game_compatible_notes.md`

## 실행 방법

1. 저장소를 클론합니다.
2. `index.html`을 브라우저로 열면 경기 종료 후 분석 화면을 볼 수 있습니다.
3. FastF1 호환 CSV를 다시 생성하려면 아래 명령을 실행합니다.

```powershell
python build_fastf1_game_compatible.py
```
