# Sweep summary

- Data: 2008-07-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2008-07-01..2026-08-24; fit 2008-07-01..2022-12-30; test 2023-01-03..2026-08-24; 27 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| assets | filter | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| SPY+VEU | @SPY>BIL | 0.27 | - | 0.38 [0.04–0.75] | 0.21 → 0.94 | 1/3 | -33.75% | - |  |
| SPY+VEU | >BIL | 0.26 | - | 0.36 [0.04–0.75] | 0.20 → 0.90 | 2/4 | -33.74% | - |  |
| SPY+EFA | >BIL | 0.25 | - | 0.31 [0.04–0.65] | 0.19 → 0.89 | 3/3 | -33.75% | - |  |
| SPY+EFA | @SPY>BIL | 0.25 | - | 0.31 [0.04–0.65] | 0.19 → 0.85 | 3/4 | -33.75% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY60/AGG40 | 0.27 | - | 0.53 [0.20–1.31] | 0.23 → 1.27 | - | -30.65% | - | - |
| EW SPY/VEU/AGG | 0.19 | - | 0.37 [0.11–0.77] | 0.14 → 1.43 | - | -35.64% | - | - |
| ROT SPY top1 12M@SPY>BIL fb AGG | 0.31 | - | 0.41 [0.07–0.86] | 0.26 → 0.94 | - | -33.77% | - | - |
| ROT SPY+VEU top1 12M all fb AGG | 0.20 | - | 0.49 [0.03–1.08] | 0.15 → 1.10 | - | -50.30% | - | - |
| SPY benchmark | 0.26 | - | 0.54 [0.14–1.12] | 0.20 → 1.19 | - | -47.16% | - | - |
