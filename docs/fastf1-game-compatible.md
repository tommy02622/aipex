# FastF1 Game-Compatible Reference

- source: `japan_reference_expanded_5m.csv`
- output: `japan_reference_game_compatible_5m.csv`
- schema template: `analysis_frames_20260426_211750.csv`
- rows: `1151`

## Column Sources

### Direct from FastF1
- `session_time`, `lap_num`, `lap_distance_m`, `total_distance_m`, `sector`
- `speed_kph`, `throttle`, `brake`, `gear`, `rpm`
- `pos_x`, `pos_z`

### Derived from FastF1
- `steer`: curvature-based pseudo-steer
- `g_lat`: `v^2 * curvature / g`
- `g_long`: `v * dv/ds / g`

### Placeholder values for schema compatibility
- `session_uid`: stable hash ID for this reference lap
- `frame_id`: sequential row index
- `player_car_index`, `lap_player_index`: `0`
- `lap_packet_seen`: `1`
- `lap_join_status`: `reference`
- `lap_context_age_s`: `0.0`
- `lap_packet_frame_id`: copied from `frame_id`
- `lap_parser_version`: `fastf1_compatible_v1`
- `lap_parse_valid`: `1`
- `lap_join_defaulted`: `0`

## Removed columns

- `lap_time_s`: not present in the latest game `analysis_frames` schema
- `drs`: not present in the latest game `analysis_frames` schema

## Derivation Details

- Position and speed are smoothed with a centered rolling mean (window=5) before taking gradients.
- Heading is computed as `atan2(dz/ds, dx/ds)`.
- Curvature is computed as `d(heading)/ds`.
- `steer` is estimated from `atan(3.6 * curvature)` and scaled to match the 99th percentile absolute steer magnitude from real game data.
- `g_lat` and `g_long` are calculated estimates, not direct FastF1 sensor channels.
- `g_lat` and `g_long` are clipped to the 99th percentile absolute range observed in the real game template to reduce coordinate-noise spikes.