# Sweep summary

- Data: 2000-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-syn-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2000-01-03..2026-08-24; fit 2000-01-03..2011-12-30; test 2012-01-03..2026-08-24; 44 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| vol.lam | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.2 | 0.8 | QQQ<SMA200 | 0.37 | 0.33 | 0.61 [-0.10–1.67] | 0.10 → 0.80 | 2/4 | -35.86% | 0.39 | yes* |
| 0.94 | 0.2 | 0.8 | QQQ<SMA200 | 0.34 | 0.30 | 0.57 [-0.09–1.39] | 0.09 → 0.71 | 3/4 | -35.96% | 0.35 | yes* |
| 0.8 | 0.2 | 0.6 | QQQ<SMA200 | 0.35 | 0.30 | 0.61 [-0.08–1.57] | 0.11 → 0.76 | 2/4 | -35.86% | 0.36 | yes* |
| 0.94 | 0.2 | 0.6 | QQQ<SMA200 | 0.32 | 0.29 | 0.54 [-0.09–1.36] | 0.09 → 0.67 | 3/4 | -35.96% | 0.35 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ buy-and-hold | -0.03 | - | 0.34 [-0.67–1.55] | -0.40 → 0.53 | - | -99.98% | - | - |
| TQQQ50/BIL50 gate QQQ<SMA200 | 0.21 | - | 0.56 [-0.12–1.37] | 0.02 → 0.59 | - | -64.40% | - | - |
| QQQ | 0.10 | - | 0.53 [-0.21–1.44] | -0.05 → 0.56 | - | -82.94% | - | - |
| SPY benchmark | 0.14 | - | 0.43 [-0.06–1.14] | 0.01 → 0.43 | - | -55.35% | - | - |
