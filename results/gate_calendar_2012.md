# Gate calendar: QQQ<SMA10M vs QQQ<SMA200

## Data

- QQQ: 1999-03-10 -> 2026-08-24 (6907 rows)
- window: 2012-01-03 -> 2026-08-24
- month-ends in the window: 175, last 2026-07-31

## Month-ends closed

- QQQ<SMA10M: 29, state changes 24
- QQQ<SMA200: 27, state changes 20

| year | month-ends | SMA10M | SMA200 |
|---|---|---|---|
| 2012 | 12 | 2 | 2 |
| 2013 | 12 | 0 | 0 |
| 2014 | 12 | 0 | 0 |
| 2015 | 12 | 2 | 2 |
| 2016 | 12 | 4 | 3 |
| 2017 | 12 | 0 | 0 |
| 2018 | 12 | 3 | 3 |
| 2019 | 12 | 2 | 1 |
| 2020 | 12 | 1 | 1 |
| 2021 | 12 | 0 | 0 |
| 2022 | 12 | 12 | 12 |
| 2023 | 12 | 0 | 0 |
| 2024 | 12 | 0 | 0 |
| 2025 | 12 | 2 | 2 |
| 2026 | 7 | 1 | 1 |

## Contingency with QQQ<SMA200 on month-ends

| window | both | SMA200 only | SMA10M only | neither |
|---|---|---|---|---|
| full | 27 | 0 | 2 | 146 |
| 2022 | 12 | 0 | 0 | 0 |

## Disagreements

| date | closed by | close | SMA200 | SMA10M |
|---|---|---|---|---|
| 2016-06-30 | SMA10M only | 101.2721 | 100.9087 | 101.3035 |
| 2019-05-31 | SMA10M only | 167.2957 | 167.2291 | 167.9708 |
