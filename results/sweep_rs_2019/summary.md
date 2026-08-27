# Sweep summary

- Data: 2019-05-08..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-24; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-24; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| weights | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| {"BIL":0.5,"NTSX":0.5} | 0.48 | - | 0.28 [0.14–1.46] | 0.38 → 1.33 | 1/1 | -16.46% | - |  |
| {"BIL":0.375,"NTSX":0.625} | 0.45 | - | 0.27 [0.11–1.36] | 0.36 → 1.24 | 2/2 | -20.39% | - |  |
| {"BIL":0.25,"NTSX":0.75} | 0.44 | - | 0.26 [0.10–1.30] | 0.34 → 1.18 | 3/3 | -24.19% | - |  |
| {"NTSX":1.0} | 0.42 | - | 0.25 [0.07–1.21] | 0.33 → 1.10 | 4/4 | -31.43% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.94 | - | 0.92 [0.62–1.39] | 1.02 → 0.92 | - | -20.11% | 0.38 | - |
| VT TQQQ/BIL50+BTAL50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.98 | - | 0.94 [0.63–1.51] | 1.03 → 1.03 | - | -19.40% | 0.38 | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.79 | - | -37.72% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
