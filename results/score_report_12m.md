# Score report: QQQ:MOM12M<=0

## Data

- QQQ: 1999-03-10 -> 2026-08-24 (6907 rows)
- window: 2012-01-03 -> 2026-08-24
- month-ends in the window: 175, last 2026-07-31

## Month-ends closed

- QQQ:MOM12M<=0: 16, state changes 8
- QQQ<SMA200: 27, state changes 20

| year | month-ends | score | SMA |
|---|---|---|---|
| 2012 | 12 | 0 | 2 |
| 2013 | 12 | 0 | 0 |
| 2014 | 12 | 0 | 0 |
| 2015 | 12 | 0 | 2 |
| 2016 | 12 | 2 | 3 |
| 2017 | 12 | 0 | 0 |
| 2018 | 12 | 1 | 3 |
| 2019 | 12 | 1 | 1 |
| 2020 | 12 | 0 | 1 |
| 2021 | 12 | 0 | 0 |
| 2022 | 12 | 9 | 12 |
| 2023 | 12 | 3 | 0 |
| 2024 | 12 | 0 | 0 |
| 2025 | 12 | 0 | 2 |
| 2026 | 7 | 0 | 1 |

## Contingency with QQQ<SMA200 on month-ends

| window | both | SMA only | score only | neither |
|---|---|---|---|---|
| full | 13 | 14 | 3 | 145 |
| 2022 | 9 | 3 | 0 | 0 |

## Disagreements

| date | closed by | score |
|---|---|---|
| 2012-10-31 | SMA only | +0.1301 |
| 2012-12-31 | SMA only | +0.1789 |
| 2015-08-31 | SMA only | +0.0549 |
| 2015-09-30 | SMA only | +0.0395 |
| 2016-01-29 | SMA only | +0.0388 |
| 2018-10-31 | SMA only | +0.1234 |
| 2018-11-30 | SMA only | +0.0988 |
| 2020-03-31 | SMA only | +0.0675 |
| 2022-01-31 | SMA only | +0.1589 |
| 2022-02-28 | SMA only | +0.1085 |
| 2022-03-31 | SMA only | +0.1406 |
| 2023-01-31 | score only | -0.1834 |
| 2023-02-28 | score only | -0.1482 |
| 2023-03-31 | score only | -0.1090 |
| 2025-03-31 | SMA only | +0.0616 |
| 2025-04-30 | SMA only | +0.1256 |
| 2026-03-31 | SMA only | +0.2359 |

## Threshold ladder

| threshold | closed | shared with SMA |
|---|---|---|
| -0.03 | 13 | 10 |
| -0.02 | 13 | 10 |
| -0.01 | 13 | 10 |
| +0 | 16 | 13 |
| +0.01 | 16 | 13 |
| +0.02 | 19 | 13 |
| +0.03 | 20 | 13 |
