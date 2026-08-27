# Sweep summary

- Data: 2000-01-03..2011-12-30
- Data dir: tests/data/2026-08-24-syn-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2000-01-03..2011-12-30; fit 2000-01-03..2007-12-31; test 2008-01-02..2011-12-30; 18 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| vol.lam | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.2 | 0.8 | QQQ<SMA200 | 0.10 | 0.08 | 0.15 [-0.26–1.25] | 0.11 → 0.19 | 3/4 | -35.86% | 0.30 | yes* |
| 0.94 | 0.2 | 0.6 | QQQ<SMA200 | 0.09 | 0.07 | 0.12 [-0.24–1.44] | 0.15 → 0.08 | 1/4 | -35.96% | 0.27 | yes* |
| 0.8 | 0.2 | 0.6 | QQQ<SMA200 | 0.11 | 0.07 | 0.19 [-0.26–1.29] | 0.13 → 0.17 | 2.5/3 | -35.86% | 0.29 | yes* |
| 0.94 | 0.2 | 0.8 | QQQ<SMA200 | 0.09 | 0.05 | 0.12 [-0.24–1.44] | 0.15 → 0.08 | 2.5/4 | -35.96% | 0.28 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ buy-and-hold | -0.40 | - | -0.21 [-0.89–0.85] | -0.49 → -0.17 | - | -99.98% | - | - |
| TQQQ50/BIL50 gate QQQ<SMA200 | 0.02 | - | 0.10 [-0.33–1.72] | 0.02 → 0.04 | - | -64.40% | - | - |
| QQQ | -0.05 | - | 0.06 [-0.42–1.11] | -0.09 → 0.06 | - | -82.94% | - | - |
| SPY benchmark | 0.01 | - | 0.01 [-0.28–1.66] | 0.03 → -0.03 | - | -55.35% | - | - |
