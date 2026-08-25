# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 6 of 6 feasible grid strategies by robust_score

| score.months | fallback | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 8 | - | 0.79 | 0.75 | 0.85 [0.40–1.30] | 0.70 → 1.14 | 1/3 | -7.33% | - | yes* |
| 10 | - | 0.75 | 0.62 | 0.78 [0.41–1.25] | 0.67 → 1.18 | 2/5 | -7.78% | - |  |
| 12 | - | 0.62 | 0.75 | 0.69 [0.20–1.08] | 0.52 → 0.97 | 4/5 | -9.59% | - | yes* |
| 8 | BIL | 0.63 | 0.58 | 0.79 [0.23–1.21] | 0.51 → 1.19 | 3/6 | -8.30% | - | yes* |
| 10 | BIL | 0.58 | 0.50 | 0.65 [0.26–1.12] | 0.48 → 1.23 | 4/6 | -9.02% | - |  |
| 12 | BIL | 0.50 | 0.58 | 0.61 [0.10–0.92] | 0.38 → 1.01 | 6/6 | -10.67% | - | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY20/EFA20/IEF20/DBC20/VNQ20 | 0.27 | - | 0.26 [0.10–0.48] | 0.20 → 1.18 | - | -26.10% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
