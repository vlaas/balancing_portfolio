# Sweep summary

- Data: 2008-08-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2008-08-01..2026-08-24; fit 2008-08-01..2022-12-30; test 2023-01-03..2026-08-24; 27 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, GLD 1, HYG 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, VGK 2, EWJ 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 6 of 6 feasible grid strategies by robust_score

| k | canary.score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 7 | 1-3-6-12U | 0.56 | 0.57 | 0.66 [0.21–1.04] | 0.52 → 1.31 | 5/6 | -14.40% | - | yes* |
| 6 | 13612W | 0.54 | 0.51 | 0.66 [0.14–1.03] | 0.66 → 0.52 | 4/6 | -14.18% | - |  |
| 7 | 13612W | 0.51 | 0.54 | 0.66 [0.13–0.94] | 0.65 → 0.48 | 4/6 | -14.51% | - | yes* |
| 5 | 1-3-6-12U | 0.48 | 0.57 | 0.68 [0.21–0.86] | 0.46 → 0.79 | 3/6 | -16.26% | - | yes* |
| 6 | 1-3-6-12U | 0.57 | 0.48 | 0.70 [0.25–0.95] | 0.52 → 1.20 | 2/5 | -15.00% | - |  |
| 5 | 13612W | 0.51 | 0.54 | 0.66 [0.15–0.86] | 0.62 → 0.32 | 3/6 | -13.69% | - | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| EW-12 | 0.20 | - | 0.34 [0.16–0.89] | 0.15 → 1.42 | - | -37.27% | - | - |
| ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF) | 0.58 | - | 1.09 [0.29–1.75] | 0.54 → 1.38 | - | -19.91% | - | - |
| SPY benchmark | 0.26 | - | 0.55 [0.18–1.15] | 0.21 → 1.19 | - | -47.10% | - | - |
