# Sweep summary

- Data: 2019-05-08..2026-08-24
- Data dir: tests/data/2026-08-24
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-24; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-24; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| weights | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| {"BIL":0.5,"NTSX":0.5} | 0.50 | - | 0.29 [0.15–1.53] | 0.39 → 1.40 | 1/1 | -16.37% | - |  |
| {"BIL":0.375,"NTSX":0.625} | 0.47 | - | 0.28 [0.12–1.41] | 0.37 → 1.28 | 2/2 | -20.29% | - |  |
| {"BIL":0.25,"NTSX":0.75} | 0.45 | - | 0.27 [0.10–1.33] | 0.36 → 1.21 | 3/3 | -24.10% | - |  |
| {"NTSX":1.0} | 0.43 | - | 0.25 [0.08–1.23] | 0.33 → 1.12 | 4/4 | -31.33% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.95 | - | 0.94 [0.64–1.46] | 1.04 → 0.95 | - | -20.07% | 0.38 | - |
| VT TQQQ/BIL50+BTAL50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.99 | - | 0.96 [0.64–1.56] | 1.04 → 1.08 | - | -19.41% | 0.38 | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.16] | 0.59 → 0.81 | - | -37.72% | - | - |
| SPY benchmark | 0.47 | - | 0.43 [0.27–1.22] | 0.39 → 1.13 | - | -33.68% | - | - |
