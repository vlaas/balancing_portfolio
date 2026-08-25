# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, GLD 1, HYG 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, VGK 2, EWJ 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 6 of 6 feasible grid strategies by robust_score

| k | canary.score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1-3-6-12U | 0.58 | 0.62 | 0.73 [0.46–0.93] | 0.56 → 0.79 | 3/5 | -13.80% | - | yes* |
| 6 | 1-3-6-12U | 0.62 | 0.58 | 0.75 [0.45–0.93] | 0.55 → 1.20 | 2/5 | -13.68% | - |  |
| 7 | 1-3-6-12U | 0.58 | 0.62 | 0.72 [0.44–1.03] | 0.52 → 1.31 | 3.5/6 | -14.35% | - | yes* |
| 6 | 13612W | 0.49 | 0.46 | 0.61 [0.21–0.94] | 0.59 → 0.52 | 4.5/6 | -14.18% | - |  |
| 7 | 13612W | 0.46 | 0.49 | 0.64 [0.19–0.97] | 0.59 → 0.48 | 4.5/6 | -14.51% | - | yes* |
| 5 | 13612W | 0.47 | 0.49 | 0.63 [0.19–0.94] | 0.60 → 0.32 | 4/6 | -13.67% | - | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| EW-12 | 0.33 | - | 0.33 [0.17–0.46] | 0.23 → 1.42 | - | -24.38% | - | - |
| ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF) | 0.97 | - | 1.15 [0.74–1.74] | 0.91 → 1.38 | - | -13.43% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
