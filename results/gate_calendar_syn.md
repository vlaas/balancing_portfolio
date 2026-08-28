# Gate calendar: QQQ<SMA10M vs QQQ<SMA200

## Data

- QQQ: 1999-03-10 -> 2026-08-24 (6907 rows)
- window: 2000-01-03 -> 2011-12-30
- month-ends in the window: 144, last 2011-12-30

## Month-ends closed

- QQQ<SMA10M: 62, state changes 27
- QQQ<SMA200: 60, state changes 27

| year | month-ends | SMA10M | SMA200 |
|---|---|---|---|
| 2000 | 12 | 6 | 6 |
| 2001 | 12 | 12 | 12 |
| 2002 | 12 | 12 | 12 |
| 2003 | 12 | 1 | 1 |
| 2004 | 12 | 4 | 4 |
| 2005 | 12 | 3 | 2 |
| 2006 | 12 | 4 | 4 |
| 2007 | 12 | 0 | 0 |
| 2008 | 12 | 11 | 11 |
| 2009 | 12 | 3 | 3 |
| 2010 | 12 | 2 | 2 |
| 2011 | 12 | 4 | 3 |

## Contingency with QQQ<SMA200 on month-ends

| window | both | SMA200 only | SMA10M only | neither |
|---|---|---|---|---|
| full | 60 | 0 | 2 | 82 |
| 2022 | 0 | 0 | 0 | 0 |

## Disagreements

| date | closed by | close | SMA200 | SMA10M |
|---|---|---|---|---|
| 2005-03-31 | SMA10M only | 31.9197 | 31.9033 | 32.0474 |
| 2011-11-30 | SMA10M only | 50.5551 | 50.3590 | 50.9615 |
