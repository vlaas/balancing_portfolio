# Sweep summary

- Data: 2019-05-08..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-24; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-24; 9 sensitivity
- Costs: per-asset (* 20) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| weights | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| {"BIL":0.5,"NTSX":0.5} | 0.48 | - | 0.28 [0.13–1.46] | 0.37 → 1.32 | 1/1 | -16.50% | - |  |
| {"BIL":0.375,"NTSX":0.625} | 0.45 | - | 0.27 [0.11–1.36] | 0.35 → 1.23 | 2/2 | -20.43% | - |  |
| {"BIL":0.25,"NTSX":0.75} | 0.43 | - | 0.26 [0.09–1.29] | 0.34 → 1.17 | 3/3 | -24.21% | - |  |
| {"NTSX":1.0} | 0.42 | - | 0.25 [0.07–1.21] | 0.33 → 1.10 | 4/4 | -31.43% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.89 | - | 0.89 [0.59–1.32] | 0.98 → 0.86 | - | -20.43% | 0.38 | - |
| VT TQQQ/BIL50+BTAL50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.94 | - | 0.90 [0.60–1.43] | 1.00 → 0.96 | - | -19.51% | 0.38 | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.55 | - | 0.60 [0.38–1.12] | 0.58 → 0.78 | - | -37.73% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.27–1.20] | 0.39 → 1.12 | - | -33.38% | - | - |
