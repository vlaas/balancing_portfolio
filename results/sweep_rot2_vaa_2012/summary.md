# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 2 of 2 feasible grid strategies by robust_score

| score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 1-3-6-12U | 0.51 | - | 0.42 [0.24–1.67] | 0.48 → 0.89 | 1/2 | -16.17% | - |  |
| 13612W | 0.30 | - | 0.40 [-0.00–1.18] | 0.33 → 0.44 | 2/2 | -20.27% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY25/EFA25/EEM25/AGG25 | 0.30 | - | 0.27 [0.07–0.42] | 0.20 → 1.40 | - | -25.68% | - | - |
| SPY60/AGG40 | 0.44 | - | 0.47 [0.25–1.34] | 0.36 → 1.27 | - | -21.60% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
