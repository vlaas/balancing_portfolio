# Sweep summary

- Data: 2008-07-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2008-07-01..2026-08-24; fit 2008-07-01..2022-12-30; test 2023-01-03..2026-08-24; 27 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 2 of 2 feasible grid strategies by robust_score

| score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 1-3-6U | 0.52 | - | 0.60 [0.22–1.22] | 0.52 → 0.76 | 1/2 | -25.81% | - |  |
| 1-3U | 0.57 | - | 0.41 [0.24–1.50] | 0.55 → 1.08 | 2/2 | -22.54% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY60/TLT40 | 0.31 | - | 0.69 [0.16–2.26] | 0.27 → 0.94 | - | -27.76% | - | - |
| EW SPY/SCZ/TIP/TLT | 0.23 | - | 0.49 [0.08–1.49] | 0.20 → 0.80 | - | -27.45% | - | - |
| SPY benchmark | 0.26 | - | 0.54 [0.14–1.12] | 0.20 → 1.19 | - | -47.16% | - | - |
