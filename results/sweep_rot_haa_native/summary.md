# Sweep summary

- Data: 2008-07-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2008-07-01..2026-08-24; fit 2008-07-01..2022-12-30; test 2023-01-03..2026-08-24; 27 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 12 of 12 feasible grid strategies by robust_score

| score | canary | fallback | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| 1-3-6-12U | TIP/1 | best(BIL+IEF) | 0.58 | - | 1.12 [0.29–1.68] | 0.54 → 1.38 | 2/12 | -19.92% | - |  |
| 1-3-6-12U | TIP/1 | IEF | 0.57 | - | 0.90 [0.27–1.50] | 0.53 → 1.37 | 3/12 | -19.91% | - |  |
| 1-3-6-12U | - | best(BIL+IEF) | 0.55 | - | 0.60 [0.25–1.05] | 0.46 → 1.93 | 6/11 | -20.82% | - |  |
| 13612W | TIP/1 | best(BIL+IEF) | 0.59 | - | 0.77 [0.31–1.69] | 0.63 → 0.55 | 4/10 | -15.52% | - |  |
| 1-3-6-12U | - | IEF | 0.55 | - | 0.61 [0.27–0.81] | 0.43 → 2.16 | 5/9 | -21.20% | - |  |
| 13612W | - | best(BIL+IEF) | 0.44 | - | 0.43 [0.09–1.30] | 0.42 → 1.23 | 8/12 | -22.05% | - |  |
| 13612W | TIP/1 | IEF | 0.40 | - | 0.76 [0.08–1.31] | 0.42 → 0.60 | 6/12 | -22.73% | - |  |
| 13612W | - | IEF | 0.35 | - | 0.36 [0.06–1.30] | 0.31 → 1.44 | 10/12 | -28.18% | - |  |
| 12M | - | best(BIL+IEF) | 0.33 | - | 0.38 [0.07–0.86] | 0.27 → 1.05 | 9/12 | -33.74% | - |  |
| 12M | - | IEF | 0.33 | - | 0.38 [0.07–0.86] | 0.26 → 1.09 | 9/12 | -33.73% | - |  |
| 12M | TIP/1 | best(BIL+IEF) | 0.32 | - | 0.49 [0.21–1.44] | 0.29 → 0.81 | 7/11 | -33.77% | - |  |
| 12M | TIP/1 | IEF | 0.32 | - | 0.45 [0.18–1.34] | 0.29 → 0.78 | 9/12 | -33.75% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY60/IEF40 | 0.29 | - | 0.59 [0.24–1.58] | 0.25 → 1.28 | - | -28.77% | - | - |
| SPY benchmark | 0.26 | - | 0.54 [0.14–1.12] | 0.20 → 1.19 | - | -47.16% | - | - |
