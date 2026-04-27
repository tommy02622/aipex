from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "collection_20260426_211750" / "normalized" / "analysis_frames_20260426_211750.csv"
SOURCE_PATH = ROOT / "fastf1_reference_collection_2024_japan_q_fastest" / "normalized" / "analysis_frames_fastf1_resampled_5m.csv"
OUTPUT_PATH = ROOT / "fastf1_reference_collection_2024_japan_q_fastest" / "normalized" / "analysis_frames_fastf1_resampled_5m_game_compatible.csv"
DOC_PATH = ROOT / "fastf1_reference_collection_2024_japan_q_fastest" / "docs" / "game_compatible_notes.md"

GRAVITY = 9.80665
STEER_WHEELBASE_M = 3.6
SMOOTHING_WINDOW = 5
LAP_JOIN_STATUS = "reference"
LAP_PARSER_VERSION = "fastf1_compatible_v1"


def stable_session_uid(label: str) -> int:
    digest = hashlib.sha256(label.encode("utf-8")).digest()[:8]
    return int.from_bytes(digest, byteorder="big", signed=False)


def centered_rolling(values: np.ndarray, window: int) -> np.ndarray:
    series = pd.Series(values)
    return series.rolling(window=window, center=True, min_periods=1).mean().to_numpy(dtype=float)


def build_template_stats(template: pd.DataFrame) -> dict[str, float]:
    stats: dict[str, float] = {}
    for col in ["steer", "g_lat", "g_long"]:
        s = pd.to_numeric(template[col], errors="coerce").dropna()
        if s.empty:
            stats[f"{col}_q99_abs"] = 1.0
            stats[f"{col}_q95_abs"] = 1.0
            continue
        stats[f"{col}_q99_abs"] = float(s.abs().quantile(0.99))
        stats[f"{col}_q95_abs"] = float(s.abs().quantile(0.95))
    return stats


def estimate_motion_fields(df: pd.DataFrame, template_stats: dict[str, float]) -> pd.DataFrame:
    distances = df["lap_distance_m"].to_numpy(dtype=float)
    speed_ms = df["speed_kph"].to_numpy(dtype=float) / 3.6

    x = centered_rolling(df["pos_x"].to_numpy(dtype=float), SMOOTHING_WINDOW)
    z = centered_rolling(df["pos_z"].to_numpy(dtype=float), SMOOTHING_WINDOW)
    speed_ms_smooth = centered_rolling(speed_ms, SMOOTHING_WINDOW)

    dx_ds = np.gradient(x, distances)
    dz_ds = np.gradient(z, distances)
    heading = np.unwrap(np.arctan2(dz_ds, dx_ds))
    curvature = np.gradient(heading, distances)

    g_lat = (speed_ms_smooth ** 2) * curvature / GRAVITY
    g_long = speed_ms_smooth * np.gradient(speed_ms_smooth, distances) / GRAVITY

    steer_angle = np.arctan(STEER_WHEELBASE_M * curvature)
    steer_q99 = np.quantile(np.abs(steer_angle), 0.99)
    target_steer_q99 = template_stats["steer_q99_abs"]
    scale = target_steer_q99 / steer_q99 if steer_q99 > 1e-9 else 1.0
    steer = np.clip(steer_angle * scale, -1.0, 1.0)

    g_lat = np.clip(g_lat, -template_stats["g_lat_q99_abs"], template_stats["g_lat_q99_abs"])
    g_long = np.clip(g_long, -template_stats["g_long_q99_abs"], template_stats["g_long_q99_abs"])

    df["steer"] = np.round(steer, 6)
    df["g_lat"] = np.round(g_lat, 6)
    df["g_long"] = np.round(g_long, 6)
    return df


def build_placeholder_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["lap_packet_seen"] = 1
    df["lap_join_status"] = LAP_JOIN_STATUS
    df["lap_context_age_s"] = 0.0
    df["lap_packet_frame_id"] = df["frame_id"]
    df["lap_player_index"] = df["player_car_index"]
    df["lap_parser_version"] = LAP_PARSER_VERSION
    df["lap_parse_valid"] = 1
    df["lap_join_defaulted"] = 0
    return df


def build_game_compatible_frame(template_columns: list[str]) -> pd.DataFrame:
    source = pd.read_csv(SOURCE_PATH)
    template = pd.read_csv(TEMPLATE_PATH, usecols=["steer", "g_lat", "g_long"])
    stats = build_template_stats(template)

    compatible = source.drop(columns=["lap_time_s", "drs"]).copy()
    compatible["session_uid"] = stable_session_uid("fastf1_2024_japan_q_ver")
    compatible["frame_id"] = np.arange(len(compatible), dtype=int)
    compatible["player_car_index"] = 0
    compatible["lap_invalid"] = compatible["lap_invalid"].fillna(0).astype(int)
    compatible["pit_status"] = compatible["pit_status"].fillna(0).astype(int)

    compatible = estimate_motion_fields(compatible, stats)
    compatible = build_placeholder_columns(compatible)

    compatible["lap_num"] = compatible["lap_num"].astype(int)
    compatible["sector"] = compatible["sector"].astype(int)
    compatible["gear"] = compatible["gear"].astype(int)

    compatible = compatible.loc[:, template_columns]
    return compatible


def write_notes(output: pd.DataFrame) -> None:
    lines = [
        "# FastF1 Japan 기준랩 게임 원본 호환 버전",
        "",
        f"- 입력 파일: `{SOURCE_PATH.name}`",
        f"- 출력 파일: `{OUTPUT_PATH.name}`",
        f"- 기준 스키마: `{TEMPLATE_PATH.name}`",
        f"- 총 행 수: `{len(output)}`",
        "",
        "## 컬럼 처리 방식",
        "",
        "### FastF1 실값으로 채운 컬럼",
        "- `session_time`, `lap_num`, `lap_distance_m`, `total_distance_m`, `sector`",
        "- `speed_kph`, `throttle`, `brake`, `gear`, `rpm`",
        "- `pos_x`, `pos_z`",
        "",
        "### 계산 기반 추정 컬럼",
        "- `steer`: 위치 곡률을 이용한 pseudo-steer",
        "- `g_lat`: `v^2 * curvature / g`",
        "- `g_long`: `v * dv/ds / g`",
        "",
        "### 형식 호환용 임의값",
        "- `session_uid`: FastF1 Japan 기준랩용 고정 해시 ID",
        "- `frame_id`: 0부터 시작하는 순차 번호",
        "- `player_car_index`, `lap_player_index`: 단일 기준랩이므로 `0`",
        "- `lap_packet_seen`: `1`",
        "- `lap_join_status`: `reference`",
        "- `lap_context_age_s`: `0.0`",
        "- `lap_packet_frame_id`: `frame_id` 복사",
        f"- `lap_parser_version`: `{LAP_PARSER_VERSION}`",
        "- `lap_parse_valid`: `1`",
        "- `lap_join_defaulted`: `0`",
        "",
        "## 제거한 컬럼",
        "",
        "- `lap_time_s`: 최신 게임 원본 `analysis_frames`에는 없음",
        "- `drs`: 최신 게임 원본 `analysis_frames`에는 없음",
        "",
        "## 추정 방식 메모",
        "",
        f"- 좌표와 속도는 중앙 이동평균(window={SMOOTHING_WINDOW})으로 한 번 스무딩 후 미분했습니다.",
        "- heading은 `atan2(dz/ds, dx/ds)`로 계산했습니다.",
        "- curvature는 `d(heading)/ds`로 계산했습니다.",
        f"- `steer`는 `atan({STEER_WHEELBASE_M} * curvature)`를 구한 뒤, 실제 게임 데이터의 steer 99퍼센타일 절댓값에 맞춰 스케일링했습니다.",
        "- `g_lat`, `g_long`은 물리식 기반 추정값이며, FastF1가 직접 제공한 센서값은 아닙니다.",
        "- `g_lat`, `g_long`은 최신 게임 원본 분포의 99퍼센타일 절댓값을 기준으로 클리핑해 급격한 좌표 노이즈를 줄였습니다.",
    ]
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    template_header = pd.read_csv(TEMPLATE_PATH, nrows=0).columns.tolist()
    output = build_game_compatible_frame(template_header)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    write_notes(output)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
