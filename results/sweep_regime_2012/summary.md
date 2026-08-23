# Sweep summary

- Data: 2012-01-03..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-20; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-20; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 13 of 13 feasible grid strategies by robust_score

| gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| QQQ<SMA200 | 0.86 | - | 0.90 [0.61–1.29] | 0.83 → 1.12 | 2/7 | -27.65% | 0.51 |  |
| QQQ<SMA200|VIX/VIX3M@1>=1.00 | 0.86 | - | 0.90 [0.61–1.29] | 0.83 → 1.12 | 3.5/8 | -27.65% | 0.51 |  |
| QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 | 0.86 | - | 0.89 [0.60–1.28] | 0.83 → 1.12 | 4/9 | -27.65% | 0.51 |  |
| QQQ<SMA200|VIX/VIX3M@10>=0.95<0.90 | 0.80 | - | 0.82 [0.45–1.25] | 0.76 → 1.12 | 8/11 | -27.64% | 0.50 |  |
| - | 0.72 | - | 0.86 [0.39–1.54] | 0.65 → 1.34 | 5/8 | -34.57% | 0.53 |  |
| VIX/VIX3M@1>=1.00 | 0.71 | - | 0.86 [0.38–1.53] | 0.64 → 1.42 | 6/10 | -34.88% | 0.53 |  |
| VIX/VIX3M@10>=1.00<0.95 | 0.70 | - | 0.93 [0.38–1.37] | 0.63 → 1.34 | 5.5/10 | -34.57% | 0.52 |  |
| VIX/VIX3M@10>=1.00<0.95 off0 | 0.61 | - | 0.80 [0.32–1.13] | 0.56 → 1.18 | 11/13 | -36.34% | 0.50 |  |
| VIX/VIX3M@1>=1.00 off0 | 0.60 | - | 0.73 [0.31–1.32] | 0.54 → 1.28 | 10/13 | -36.34% | 0.50 |  |
| VIX/VIX3M@10>=0.95<0.90 | 0.60 | - | 0.78 [0.22–1.27] | 0.51 → 1.41 | 9/13 | -36.55% | 0.51 |  |
| QQQ<SMA200|VIX/VIX3M@1>=1.00 off0 | 0.59 | - | 0.67 [0.38–0.96] | 0.60 → 0.69 | 10/12 | -36.34% | 0.47 |  |
| QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 off0 | 0.58 | - | 0.62 [0.34–0.90] | 0.56 → 0.96 | 11/13 | -36.34% | 0.49 |  |
| QQQ<SMA200 off0 | 0.55 | - | 0.78 [0.43–1.22] | 0.59 → 0.54 | 7/13 | -36.13% | 0.47 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.53 | - | 0.71 [0.29–1.67] | 0.46 → 1.23 | - | -44.81% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 0.98 | - | -37.73% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
