# Sweep summary

- Data: 2019-05-08..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-20; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-20; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 32 feasible grid strategies by robust_score

| safe | gate | rebalance | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BTAL75+DBMF25 | QQQ<SMA200 | - | 0.94 | - | 0.92 [0.62–1.39] | 1.02 → 0.92 | 9/24 | -20.11% | 0.38 |  |
| BTAL75+DBMF25 | - | - | 0.94 | - | 0.84 [0.63–1.38] | 1.03 → 0.85 | 12/26 | -20.13% | 0.40 |  |
| BTAL75+DBMF25 | - | 2w | 0.81 | - | 0.91 [0.61–1.49] | 0.85 → 0.91 | 10/18 | -20.10% | 0.39 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 2w | 0.79 | - | 1.04 [0.60–1.42] | 0.81 → 1.01 | 7/14 | -20.10% | 0.37 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 3m+2 | 0.71 | - | 0.98 [0.65–1.90] | 0.72 → 0.84 | 9/30 | -31.20% | 0.39 |  |
| BTAL75+DBMF25 | - | 1w | 0.85 | - | 0.98 [0.61–1.49] | 1.00 → 0.70 | 10/22 | -20.13% | 0.38 |  |
| BTAL75+DBMF25 | - | 3m+2 | 0.69 | - | 0.81 [0.56–1.38] | 0.69 → 0.85 | 10/28 | -31.20% | 0.40 |  |
| BTAL | QQQ<SMA200 | 3m+2 | 0.67 | - | 0.94 [0.58–1.79] | 0.70 → 0.72 | 12/28 | -29.76% | 0.39 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 2m+1 | 0.66 | - | 0.94 [0.60–1.53] | 0.73 → 0.77 | 5/18 | -27.16% | 0.39 |  |
| BTAL | - | 3m+2 | 0.64 | - | 0.83 [0.50–1.28] | 0.67 → 0.74 | 17/23 | -29.76% | 0.40 |  |
| BTAL | - | - | 0.64 | - | 0.78 [0.37–1.68] | 0.71 → 0.80 | 24/28 | -26.00% | 0.40 |  |
| BTAL75+DBMF25 | - | 2m+1 | 0.63 | - | 0.88 [0.44–1.48] | 0.67 → 0.78 | 15/21 | -27.16% | 0.40 |  |
| BTAL | QQQ<SMA200 | - | 0.63 | - | 0.96 [0.36–1.37] | 0.70 → 0.79 | 16/29 | -26.02% | 0.38 |  |
| BTAL75+DBMF25 | - | 2w+1 | 0.82 | - | 0.98 [0.44–1.49] | 0.97 → 0.62 | 15/24 | -21.29% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 3m+1 | 0.61 | - | 0.65 [0.50–1.44] | 0.59 → 1.05 | 21/30 | -27.14% | 0.36 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 rb 1w | 0.48 | - | 0.34 [0.21–1.34] | 0.47 → 0.87 | - | -45.31% | - | - |
| 50/50 | 0.48 | - | 0.35 [0.20–1.31] | 0.48 → 0.82 | - | -44.78% | - | - |
| TQQQ50/BTAL50 rb 3m | 0.55 | - | 0.39 [0.26–1.32] | 0.55 → 0.90 | - | -43.70% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 1w | 0.57 | - | 0.53 [0.36–1.20] | 0.57 → 0.89 | - | -37.33% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.80 | - | -37.72% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 3m | 0.55 | - | 0.57 [0.37–1.15] | 0.56 → 0.80 | - | -35.77% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
