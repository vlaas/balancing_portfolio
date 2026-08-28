# Sweep summary

- Data: 2019-05-08..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-24; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-24; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 3 of 3 feasible grid strategies by robust_score

| gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| QQQ<SMA200 | 0.94 | - | 0.92 [0.62–1.39] | 1.02 → 0.92 | 1/2 | -20.11% | 0.38 |  |
| QQQ<SMA10M | 0.93 | - | 0.92 [0.62–1.39] | 1.01 → 0.92 | 1/2 | -20.11% | 0.38 |  |
| - | 0.94 | - | 0.84 [0.63–1.38] | 1.03 → 0.84 | 3/3 | -20.13% | 0.40 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
