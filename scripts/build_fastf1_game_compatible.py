from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "collection_20260426_211750" / "normalized" / "analysis_frames_20260426_211750.csv"
SOURCE_PATH = REPO_ROOT / "data" / "reference" / "japan" / "japan_reference_expanded_5m.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "reference" / "japan" / "japan_reference_game_compatible_5m.csv"
DOC_PATH = REPO_ROOT / "docs" / "fastf1-game-compatible.md"

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
            continue
        stats[f"{col}_q99_abs"] = float(s.abs().quantile(0.99))
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
        "# FastF1 Game-Compatible Reference",
        "",
        f"- source: `{SOURCE_PATH.name}`",
        f"- output: `{OUTPUT_PATH.name}`",
        f"- schema template: `{TEMPLATE_PATH.name}`",
        f"- rows: `{len(output)}`",
        "",
        "## Column Sources",
        "",
        "### Direct from FastF1",
        "- `session_time`, `lap_num`, `lap_distance_m`, `total_distance_m`, `sector`",
        "- `speed_kph`, `throttle`, `brake`, `gear`, `rpm`",
        "- `pos_x`, `pos_z`",
        "",
        "### Derived from FastF1",
        "- `steer`: curvature-based pseudo-steer",
        "- `g_lat`: `v^2 * curvature / g`",
        "- `g_long`: `v * dv/ds / g`",
        "",
        "### Placeholder values for schema compatibility",
        "- `session_uid`: stable hash ID for this reference lap",
        "- `frame_id`: sequential row index",
        "- `player_car_index`, `lap_player_index`: `0`",
        "- `lap_packet_seen`: `1`",
        "- `lap_join_status`: `reference`",
        "- `lap_context_age_s`: `0.0`",
        "- `lap_packet_frame_id`: copied from `frame_id`",
        f"- `lap_parser_version`: `{LAP_PARSER_VERSION}`",
        "- `lap_parse_valid`: `1`",
        "- `lap_join_defaulted`: `0`",
        "",
        "## Removed columns",
        "",
        "- `lap_time_s`: not present in the latest game `analysis_frames` schema",
        "- `drs`: not present in the latest game `analysis_frames` schema",
        "",
        "## Derivation Details",
        "",
        f"- Position and speed are smoothed with a centered rolling mean (window={SMOOTHING_WINDOW}) before taking gradients.",
        "- Heading is computed as `atan2(dz/ds, dx/ds)`.",
        "- Curvature is computed as `d(heading)/ds`.",
        f"- `steer` is estimated from `atan({STEER_WHEELBASE_M} * curvature)` and scaled to match the 99th percentile absolute steer magnitude from real game data.",
        "- `g_lat` and `g_long` are calculated estimates, not direct FastF1 sensor channels.",
        "- `g_lat` and `g_long` are clipped to the 99th percentile absolute range observed in the real game template to reduce coordinate-noise spikes.",
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
