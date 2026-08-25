# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 12 of 12 feasible grid strategies by robust_score

| score | canary | fallback | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| 1-3-6-12U | TIP/1 | best(BIL+IEF) | 0.97 | - | 1.15 [0.74–1.74] | 0.91 → 1.38 | 2/6 | -13.43% | - |  |
| 1-3-6-12U | TIP/1 | IEF | 0.84 | - | 0.98 [0.67–1.51] | 0.79 → 1.37 | 3/5 | -15.08% | - |  |
| 1-3-6-12U | - | best(BIL+IEF) | 0.62 | - | 0.71 [0.25–1.05] | 0.51 → 1.93 | 6/10 | -20.83% | - |  |
| 1-3-6-12U | - | IEF | 0.61 | - | 0.64 [0.27–0.81] | 0.48 → 2.16 | 5/7 | -21.21% | - |  |
| 13612W | TIP/1 | best(BIL+IEF) | 0.69 | - | 0.94 [0.30–1.75] | 0.75 → 0.55 | 3.5/9 | -13.43% | - |  |
| 13612W | TIP/1 | IEF | 0.38 | - | 0.89 [0.08–1.34] | 0.40 → 0.60 | 5/12 | -22.71% | - |  |
| 13612W | - | best(BIL+IEF) | 0.40 | - | 0.38 [0.10–0.70] | 0.34 → 1.23 | 8.5/11 | -22.02% | - |  |
| 12M | - | best(BIL+IEF) | 0.34 | - | 0.35 [0.08–0.85] | 0.26 → 1.05 | 9/12 | -33.70% | - |  |
| 12M | - | IEF | 0.33 | - | 0.33 [0.08–0.71] | 0.24 → 1.09 | 9/12 | -33.76% | - |  |
| 12M | TIP/1 | best(BIL+IEF) | 0.32 | - | 0.47 [0.20–1.42] | 0.28 → 0.81 | 7/11 | -33.73% | - |  |
| 12M | TIP/1 | IEF | 0.32 | - | 0.43 [0.16–1.35] | 0.28 → 0.78 | 9/12 | -33.72% | - |  |
| 13612W | - | IEF | 0.30 | - | 0.30 [0.07–0.71] | 0.23 → 1.44 | 11/12 | -28.17% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY60/IEF40 | 0.43 | - | 0.50 [0.25–1.39] | 0.36 → 1.28 | - | -21.38% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
