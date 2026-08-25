# Sweep summary

- Data: 2007-06-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2007-06-01..2026-08-24; fit 2007-06-01..2022-12-30; test 2023-01-03..2026-08-24; 29 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 6 of 6 feasible grid strategies by robust_score

| score.months | fallback | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 8 | - | 0.59 | 0.41 | 0.67 [0.28–1.18] | 0.55 → 1.14 | 1/3 | -10.23% | - | yes* |
| 10 | - | 0.41 | 0.42 | 0.62 [0.20–1.15] | 0.37 → 1.18 | 3/5 | -13.53% | - |  |
| 12 | - | 0.42 | 0.41 | 0.47 [0.17–1.11] | 0.37 → 0.97 | 4/5 | -13.10% | - | yes* |
| 8 | BIL | 0.46 | 0.35 | 0.54 [0.11–1.08] | 0.40 → 1.19 | 3/6 | -11.65% | - | yes* |
| 10 | BIL | 0.35 | 0.37 | 0.48 [0.12–1.02] | 0.30 → 1.23 | 5/6 | -13.84% | - |  |
| 12 | BIL | 0.37 | 0.35 | 0.34 [0.07–1.01] | 0.30 → 1.01 | 6/6 | -13.16% | - | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY20/EFA20/IEF20/DBC20/VNQ20 | 0.12 | - | 0.27 [0.02–0.77] | 0.08 → 1.18 | - | -47.20% | - | - |
| SPY benchmark | 0.19 | - | 0.55 [-0.03–1.19] | 0.14 → 1.19 | - | -55.27% | - | - |
