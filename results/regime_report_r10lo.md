# Regime report: VIX/VIX3M@10 >= 0.95 < 0.90

## Data

- VIX: 1990-01-03 -> 2026-08-21 (9246 rows)
- VIX3M: -> 2026-08-21 (4671 joint rows, full intersection)
- window: 2012-01-03 -> 2026-08-20, 3679 joint days
- VIX-only rows in the window: 22, on QQQ's calendar: 0

## Trading days

- risk-off: 964 of 3679 (26.2%)
- episodes: 33, mean length 29.2 days

## Month-ends (QQQ calendar)

- month-ends in the window: 175, risk-off: 44

| year | month-ends | risk-off |
|---|---|---|
| 2012 | 12 | 1 |
| 2013 | 12 | 1 |
| 2014 | 12 | 3 |
| 2015 | 12 | 3 |
| 2016 | 12 | 3 |
| 2017 | 12 | 1 |
| 2018 | 12 | 6 |
| 2019 | 12 | 5 |
| 2020 | 12 | 6 |
| 2021 | 12 | 0 |
| 2022 | 12 | 7 |
| 2023 | 12 | 2 |
| 2024 | 12 | 3 |
| 2025 | 12 | 2 |
| 2026 | 7 | 1 |

## Contingency with QQQ<SMA200 on month-ends

| window | both | SMA only | regime only | neither |
|---|---|---|---|---|
| full | 20 | 7 | 24 | 124 |
| 2022 | 7 | 5 | 0 | 0 |
