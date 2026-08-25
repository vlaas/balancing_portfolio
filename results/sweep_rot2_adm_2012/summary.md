# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 3 of 3 feasible grid strategies by robust_score

| score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 1-3-6-12U | 0.47 | - | 0.47 [0.20–0.80] | 0.37 → 1.16 | 2.5/3 | -24.79% | - |  |
| 1-3-6U | 0.42 | - | 0.48 [0.22–0.95] | 0.38 → 0.76 | 1/3 | -25.78% | - |  |
| 1-3U | 0.42 | - | 0.35 [0.24–0.88] | 0.35 → 1.08 | 2/3 | -22.53% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY60/TLT40 | 0.32 | - | 0.60 [0.16–1.34] | 0.28 → 0.94 | - | -27.74% | - | - |
| EW SPY/SCZ/TIP/TLT | 0.24 | - | 0.39 [0.09–1.06] | 0.20 → 0.80 | - | -26.82% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
