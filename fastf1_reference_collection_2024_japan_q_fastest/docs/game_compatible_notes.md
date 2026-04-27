# FastF1 Japan 기준랩 게임 원본 호환 버전

- 입력 파일: `analysis_frames_fastf1_resampled_5m.csv`
- 출력 파일: `analysis_frames_fastf1_resampled_5m_game_compatible.csv`
- 기준 스키마: `analysis_frames_20260426_211750.csv`
- 총 행 수: `1151`

## 컬럼 처리 방식

### FastF1 실값으로 채운 컬럼
- `session_time`, `lap_num`, `lap_distance_m`, `total_distance_m`, `sector`
- `speed_kph`, `throttle`, `brake`, `gear`, `rpm`
- `pos_x`, `pos_z`

### 계산 기반 추정 컬럼
- `steer`: 위치 곡률을 이용한 pseudo-steer
- `g_lat`: `v^2 * curvature / g`
- `g_long`: `v * dv/ds / g`

### 형식 호환용 임의값
- `session_uid`: FastF1 Japan 기준랩용 고정 해시 ID
- `frame_id`: 0부터 시작하는 순차 번호
- `player_car_index`, `lap_player_index`: 단일 기준랩이므로 `0`
- `lap_packet_seen`: `1`
- `lap_join_status`: `reference`
- `lap_context_age_s`: `0.0`
- `lap_packet_frame_id`: `frame_id` 복사
- `lap_parser_version`: `fastf1_compatible_v1`
- `lap_parse_valid`: `1`
- `lap_join_defaulted`: `0`

## 제거한 컬럼

- `lap_time_s`: 최신 게임 원본 `analysis_frames`에는 없음
- `drs`: 최신 게임 원본 `analysis_frames`에는 없음

## 추정 방식 메모

- 좌표와 속도는 중앙 이동평균(window=5)으로 한 번 스무딩 후 미분했습니다.
- heading은 `atan2(dz/ds, dx/ds)`로 계산했습니다.
- curvature는 `d(heading)/ds`로 계산했습니다.
- `steer`는 `atan(3.6 * curvature)`를 구한 뒤, 실제 게임 데이터의 steer 99퍼센타일 절댓값에 맞춰 스케일링했습니다.
- `g_lat`, `g_long`은 물리식 기반 추정값이며, FastF1가 직접 제공한 센서값은 아닙니다.
- `g_lat`, `g_long`은 최신 게임 원본 분포의 99퍼센타일 절댓값을 기준으로 클리핑해 급격한 좌표 노이즈를 줄였습니다.