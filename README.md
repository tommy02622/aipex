# AIPEX

AIPEX는 F1 게임 텔레메트리와 FastF1 레퍼런스 데이터를 활용해 주행을 분석하고, 경기 종료 후 피드백을 제공하는 프로젝트입니다.

## 포함 파일

- `index.html`
  - 브라우저에서 바로 열 수 있는 경기 종료 후 분석 화면 데모

## FastF1 기준 데이터

저장소에는 일본 스즈카 퀄리파잉 fastest lap 기준의 두 가지 CSV를 포함합니다.

### 1. 최소형 기준 데이터

- `fastf1_reference_collection_2024_japan_q_fastest/ground_truth/ground_truth_japan_resampled_5m.csv`

설명:
- `lap_distance_m`, `speed_kph`, `throttle`, `brake`만 포함한 최소형 기준 데이터입니다.
- 모델에서 정답 신호나 기준 랩 곡선을 단순하게 사용할 때 적합합니다.
- 거리축 기준으로 `5m` 간격 보간이 적용되어 있습니다.

### 2. 확장형 기준 데이터

- `fastf1_reference_collection_2024_japan_q_fastest/normalized/analysis_frames_fastf1_resampled_5m.csv`

설명:
- 최소형 데이터에 더해 `gear`, `rpm`, `pos_x`, `pos_z`, `sector`, `session_time` 등이 포함된 확장형 기준 데이터입니다.
- 게임 원본 collection 형식과 유사하게 맞춘 버전이라, 후처리나 비교 파이프라인에 바로 붙이기 쉽습니다.
- 이 파일도 거리축 기준 `5m` 간격 보간이 적용되어 있습니다.

## 실행 방법

1. 저장소를 클론합니다.
2. `index.html`을 브라우저에서 엽니다.

별도 빌드나 패키지 설치 없이 바로 확인할 수 있습니다.
