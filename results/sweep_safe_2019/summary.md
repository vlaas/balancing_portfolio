# Sweep summary

- Data: 2019-05-08..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-20; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-20; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 94 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DBMF | 0.25 | 0.8 | QQQ<SMA200 | 0.89 | 0.88 | 0.92 [0.46–1.15] | 0.95 → 0.88 | 2/94 | -32.67% | 0.46 | yes* |
| DBMF | 0.25 | 0.7 | QQQ<SMA200 | 0.88 | 0.86 | 0.88 [0.46–1.14] | 0.90 → 0.91 | 9/93 | -32.06% | 0.45 | yes* |
| DBMF | 0.3 | 0.8 | QQQ<SMA200 | 0.88 | 0.86 | 0.86 [0.52–1.20] | 0.90 → 0.93 | 14/85 | -35.19% | 0.53 | yes* |
| DBMF | 0.3 | 0.6 | QQQ<SMA200 | 0.84 | 0.85 | 0.87 [0.55–1.24] | 0.82 → 0.98 | 12/86 | -35.19% | 0.47 |  |
| DBMF | 0.3 | 0.7 | QQQ<SMA200 | 0.86 | 0.84 | 0.87 [0.53–1.21] | 0.86 → 0.95 | 13/87 | -35.20% | 0.50 |  |
| DBMF | 0.25 | 0.5 | QQQ<SMA200 | 0.83 | 0.85 | 0.90 [0.49–1.18] | 0.81 → 0.96 | 8/93 | -31.51% | 0.39 | yes* |
| DBMF | 0.25 | 0.6 | QQQ<SMA200 | 0.86 | 0.83 | 0.89 [0.47–1.15] | 0.85 → 0.93 | 7/92 | -31.54% | 0.42 | yes* |
| DBMF | 0.3 | 0.5 | QQQ<SMA200 | 0.85 | 0.82 | 0.92 [0.55–1.24] | 0.83 → 0.97 | 9/88 | -33.68% | 0.42 | yes* |
| DBMF | 0.35 | 0.6 | QQQ<SMA200 | 0.85 | 0.82 | 0.88 [0.61–1.29] | 0.84 → 0.98 | 12/83 | -37.39% | 0.50 |  |
| DBMF | 0.4 | 0.7 | QQQ<SMA200 | 0.85 | 0.84 | 0.81 [0.61–1.29] | 0.85 → 0.97 | 19/76 | -40.92% | 0.58 | yes* |
| DBMF | 0.35 | 0.7 | QQQ<SMA200 | 0.84 | 0.85 | 0.80 [0.58–1.28] | 0.83 → 0.98 | 21/81 | -38.68% | 0.55 |  |
| DBMF | 0.35 | 0.8 | QQQ<SMA200 | 0.86 | 0.84 | 0.79 [0.55–1.24] | 0.86 → 0.95 | 23/82 | -38.68% | 0.58 | yes* |
| DBMF | 0.35 | 0.5 | QQQ<SMA200 | 0.82 | 0.79 | 0.83 [0.52–1.20] | 0.81 → 0.94 | 18/89 | -35.11% | 0.44 | yes* |
| DBMF | 0.4 | 0.6 | QQQ<SMA200 | 0.84 | 0.79 | 0.79 [0.58–1.25] | 0.83 → 0.95 | 22/84 | -38.77% | 0.52 | yes* |
| DBMF | 0.25 | 0.8 | - | 0.84 | 0.83 | 0.78 [0.48–1.09] | 0.93 → 0.84 | 25/91 | -34.02% | 0.48 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.48 | - | 0.35 [0.20–1.31] | 0.48 → 0.82 | - | -44.78% | - | - |
| TQQQ50/DBMF50 | 0.60 | - | 0.41 [0.21–1.21] | 0.55 → 0.95 | - | -46.94% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.80 | - | -37.72% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
