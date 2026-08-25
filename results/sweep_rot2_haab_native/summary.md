# Sweep summary

- Data: 2008-08-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2008-08-01..2026-08-24; fit 2008-08-01..2022-12-30; test 2023-01-03..2026-08-24; 27 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 9 of 9 feasible grid strategies by robust_score

| k | score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1-3-6-12U | 0.63 | 0.66 | 0.70 [0.31–1.27] | 0.63 → 0.75 | 2/5 | -14.47% | - | yes* |
| 3 | 1-3-6-12U | 0.50 | 0.66 | 0.63 [0.26–1.30] | 0.72 → 0.51 | 6/9 | -19.87% | - | yes* |
| 4 | 1-3-6-12U | 0.66 | 0.50 | 0.73 [0.38–1.37] | 0.75 → 0.67 | 1/4 | -14.59% | - |  |
| 5 | 13612W | 0.43 | 0.33 | 0.48 [0.18–1.27] | 0.45 → 0.39 | 5/8 | -15.90% | - | yes* |
| 3 | 12M | 0.30 | 0.34 | 0.42 [0.09–0.63] | 0.25 → 0.60 | 7/9 | -22.06% | - | yes* |
| 4 | 12M | 0.34 | 0.29 | 0.37 [0.15–0.60] | 0.27 → 0.80 | 7/8 | -20.03% | - |  |
| 5 | 12M | 0.29 | 0.34 | 0.28 [0.13–0.63] | 0.23 → 0.87 | 8/9 | -21.50% | - | yes* |
| 4 | 13612W | 0.33 | 0.28 | 0.47 [0.09–1.18] | 0.54 → 0.24 | 5/9 | -20.83% | - |  |
| 3 | 13612W | 0.28 | 0.33 | 0.40 [0.08–1.43] | 0.40 → 0.17 | 6/9 | -25.56% | - | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY12.5/IWM12.5/VEA12.5/VWO12.5/VNQ12.5/DBC12.5/IEF12.5/TLT12.5 | 0.15 | - | 0.27 [0.12–0.87] | 0.12 → 1.04 | - | -39.93% | - | - |
| ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF) | 0.58 | - | 1.09 [0.29–1.75] | 0.54 → 1.38 | - | -19.91% | - | - |
| SPY benchmark | 0.26 | - | 0.55 [0.18–1.15] | 0.21 → 1.19 | - | -47.10% | - | - |
