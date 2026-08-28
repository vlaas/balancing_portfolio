# Episode report: mg_points_2019.json

## Episodes (EPISODE_SPEC §3)

| id | name | window | trough |
|---|---|---|---|
| E1 | grind-2015 | 2014-11-28 → 2017-02-07 | 2015-08-25 |
| E2 | 2018-Q4 | 2018-08-31 → 2019-12-16 | 2019-06-03 |
| E3 | COVID | 2020-02-19 → 2020-07-06 | 2020-03-23 |
| E4 | anti-beta unwind | 2020-09-02 → 2021-09-03 | 2021-03-08 |
| E5 | 2022 grind | 2021-11-19 → 2023-06-15 | 2023-03-10 |
| E6 | tariff | 2024-07-10 → 2025-10-01 | 2025-04-08 |
| E7 | 2025-10 | 2025-10-29 → 2026-08-24 | 2026-03-27 |

- data: `tests/data/2026-08-24-net15`
- cells: episode return % of the TWR index / max drawdown % inside the window
- `·` where the lane has fewer than two bars in the window

## Episode return / in-window drawdown

| sleeve | E1 | E2 | E3 | E4 | E5 | E6 | E7 |
|---|---|---|---|---|---|---|---|
| `VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80` | · / · | +23.3 / -8.9 | -1.3 / -18.9 | +9.0 / -20.1 | +5.5 / -18.1 | +1.5 / -20.1 | -1.0 / -16.4 |
| `VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200` | · / · | +23.3 / -8.9 | -1.4 / -18.9 | +9.0 / -20.1 | +5.3 / -14.7 | +1.3 / -18.4 | -1.0 / -16.4 |
| `VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA10M` | · / · | +21.9 / -9.0 | -1.4 / -18.9 | +9.0 / -20.1 | +5.3 / -14.7 | +1.3 / -18.4 | -1.0 / -16.4 |
| `SPY benchmark` | · / · | +11.9 / -5.9 | -5.5 / -33.7 | +28.0 / -9.4 | -3.5 / -24.4 | +20.6 / -18.7 | +11.8 / -8.9 |
