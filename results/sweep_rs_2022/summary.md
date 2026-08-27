# Sweep summary

- Data: 2022-03-17..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2022-03-17..2026-08-24; fit 2022-03-17..2024-06-28; test 2024-07-01..2026-08-24; 3 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 8 of 8 feasible grid strategies by robust_score

| weights | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| {"GDE":1.0} | 0.90 | - | 2.62 [0.59–2.98] | 0.42 → 2.07 | 1/1 | -31.99% | - |  |
| {"GDE":0.5,"NTSX":0.5} | 0.68 | - | 1.82 [0.42–2.00] | 0.33 → 1.91 | 2/2 | -29.04% | - |  |
| {"NTSX":1.0} | 0.41 | - | 1.06 [0.22–1.07] | 0.21 → 1.00 | 4/5 | -26.23% | - |  |
| {"NTSE":0.33,"NTSI":0.33,"NTSX":0.34} | 0.39 | - | 1.07 [0.15–1.15] | 0.08 → 1.38 | 4/5 | -26.69% | - |  |
| {"NTSE":1.0} | 0.36 | - | 0.72 [0.03–0.97] | -0.06 → 1.41 | 6/6 | -30.52% | - |  |
| {"NTSI":1.0} | 0.34 | - | 1.01 [0.16–1.13] | 0.08 → 1.28 | 4/5 | -27.19% | - |  |
| {"RPAR":1.0} | 0.06 | - | 0.42 [-0.13–0.59] | -0.24 → 0.96 | 7/7 | -25.86% | - |  |
| {"UPAR":1.0} | 0.01 | - | 0.28 [-0.18–0.47] | -0.28 → 0.83 | 8/8 | -36.26% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| VT TQQQ/BTAL75+KMLM25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 1.10 | - | 1.17 [1.15–1.26] | 2.17 → 0.47 | - | -17.65% | 0.34 | - |
| VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 1.09 | - | 1.20 [1.16–1.24] | 2.25 → 0.46 | - | -18.32% | 0.34 | - |
| VT TQQQ/BTAL50+KMLM50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.99 | - | 1.04 [0.91–1.17] | 2.14 → 0.53 | - | -20.87% | 0.34 | - |
| SPY benchmark | 0.66 | - | 1.10 [0.46–1.12] | 0.52 → 0.96 | - | -21.79% | - | - |
