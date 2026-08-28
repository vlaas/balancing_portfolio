# Sweep summary

- Data: 2000-01-03..2011-12-30
- Data dir: tests/data/2026-08-24-syn-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2000-01-03..2011-12-30; fit 2000-01-03..2007-12-31; test 2008-01-02..2011-12-30; 18 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 2 of 2 feasible grid strategies by robust_score

| gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| QQQ<SMA10M | 0.11 | - | 0.19 [-0.26–1.25] | 0.11 → 0.19 | 1/2 | -35.86% | 0.30 |  |
| QQQ<SMA200 | 0.10 | - | 0.15 [-0.26–1.25] | 0.11 → 0.19 | 1/2 | -35.86% | 0.30 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY benchmark | 0.01 | - | 0.01 [-0.28–1.66] | 0.03 → -0.03 | - | -55.35% | - | - |
