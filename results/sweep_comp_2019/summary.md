# Sweep summary

- Data: 2019-05-08..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-24; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-24; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 14 of 14 feasible grid strategies by robust_score

| safe | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL75+DBMF25 | QQQ<SMA200 | 0.94 | - | 0.92 [0.62–1.39] | 1.02 → 0.92 | 3/5 | -20.11% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2 | 0.92 | - | 0.86 [0.58–1.34] | 0.99 → 0.92 | 4/9 | -20.11% | 0.38 |  |
| BTAL75+DBMF25 | - | 0.94 | - | 0.84 [0.63–1.38] | 1.03 → 0.84 | 5/8 | -20.13% | 0.40 |  |
| BTAL75+DBMF25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 | 0.87 | - | 0.83 [0.49–1.21] | 0.92 → 0.92 | 5/14 | -20.11% | 0.37 |  |
| BTAL75+DBMF25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 off0 | 0.79 | - | 0.94 [0.65–1.45] | 0.87 → 0.72 | 3/14 | -20.10% | 0.35 |  |
| BTAL75+DBMF25 | QQQ:MOMM1-3-6-12U<=0 | 0.83 | - | 0.71 [0.39–1.23] | 0.85 → 0.93 | 11/13 | -20.11% | 0.38 |  |
| BTAL75+DBMF25 | QQQ:MOMM1-3-6-12U<=0 off0 | 0.75 | - | 0.71 [0.43–1.34] | 0.72 → 1.02 | 9/11 | -20.10% | 0.36 |  |
| BTAL | - | 0.64 | - | 0.78 [0.37–1.68] | 0.71 → 0.80 | 9/14 | -26.00% | 0.40 |  |
| BTAL | QQQ<SMA200 | 0.63 | - | 0.96 [0.36–1.37] | 0.70 → 0.79 | 8/10 | -26.02% | 0.38 |  |
| BTAL | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2 | 0.61 | - | 0.91 [0.33–1.32] | 0.68 → 0.79 | 8/11 | -26.02% | 0.38 |  |
| BTAL | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 | 0.58 | - | 0.80 [0.28–1.19] | 0.63 → 0.79 | 9/12 | -26.02% | 0.37 |  |
| BTAL | QQQ:MOMM1-3-6-12U<=0 | 0.56 | - | 0.60 [0.21–1.20] | 0.58 → 0.80 | 13/14 | -26.02% | 0.38 |  |
| BTAL | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 off0 | 0.52 | - | 0.76 [0.40–1.31] | 0.59 → 0.59 | 8/14 | -26.00% | 0.35 |  |
| BTAL | QQQ:MOMM1-3-6-12U<=0 off0 | 0.49 | - | 0.56 [0.24–1.21] | 0.48 → 0.81 | 12/14 | -26.00% | 0.36 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.48 | - | 0.35 [0.20–1.31] | 0.48 → 0.81 | - | -44.78% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.79 | - | -37.72% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
