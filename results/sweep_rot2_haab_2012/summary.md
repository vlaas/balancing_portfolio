# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 9 of 9 feasible grid strategies by robust_score

| k | score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1-3-6-12U | 0.59 | 0.63 | 0.75 [0.45–1.40] | 0.86 → 0.75 | 2/4 | -14.46% | - | yes* |
| 3 | 1-3-6-12U | 0.44 | 0.63 | 0.60 [0.25–1.24] | 0.73 → 0.51 | 6/9 | -19.87% | - | yes* |
| 4 | 1-3-6-12U | 0.63 | 0.44 | 0.76 [0.44–1.40] | 0.91 → 0.67 | 2/4 | -14.58% | - |  |
| 3 | 12M | 0.42 | 0.46 | 0.47 [0.27–0.69] | 0.47 → 0.60 | 7/9 | -19.23% | - | yes* |
| 4 | 12M | 0.46 | 0.32 | 0.43 [0.27–0.56] | 0.37 → 0.80 | 7/8 | -17.62% | - |  |
| 5 | 12M | 0.32 | 0.46 | 0.34 [0.17–0.63] | 0.25 → 0.87 | 7.5/9 | -21.52% | - | yes* |
| 5 | 13612W | 0.40 | 0.30 | 0.53 [0.17–1.28] | 0.59 → 0.39 | 5/8 | -15.44% | - | yes* |
| 4 | 13612W | 0.30 | 0.27 | 0.46 [0.10–1.20] | 0.65 → 0.24 | 6/8 | -20.80% | - |  |
| 3 | 13612W | 0.27 | 0.30 | 0.43 [0.08–1.43] | 0.65 → 0.17 | 5.5/9 | -25.54% | - | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY12.5/IWM12.5/VEA12.5/VWO12.5/VNQ12.5/DBC12.5/IEF12.5/TLT12.5 | 0.27 | - | 0.26 [0.13–0.40] | 0.20 → 1.04 | - | -24.95% | - | - |
| ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF) | 0.97 | - | 1.15 [0.74–1.74] | 0.91 → 1.38 | - | -13.43% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
