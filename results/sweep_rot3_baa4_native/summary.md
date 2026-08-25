# Sweep summary

- Data: 2008-08-01..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2008-08-01..2026-08-24; fit 2008-08-01..2022-12-30; test 2023-01-03..2026-08-24; 27 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, GLD 1, HYG 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, VGK 2, EWJ 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 4 of 4 feasible grid strategies by robust_score

| score | canary.score | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| 1-3-6-12U | 1-3-6-12U | 0.44 | - | 0.53 [0.24–1.75] | 0.46 → 0.46 | 3/4 | -20.57% | - |  |
| gap13M | 1-3-6-12U | 0.41 | - | 0.52 [0.23–1.61] | 0.43 → 0.39 | 3/4 | -20.56% | - |  |
| 1-3-6-12U | 13612W | 0.49 | - | 0.78 [0.04–1.30] | 0.83 → 0.14 | 2/4 | -19.93% | - |  |
| gap13M | 13612W | 0.44 | - | 0.88 [0.00–1.27] | 0.69 → 0.07 | 2/4 | -20.04% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| QQQ25/VWO25/VEA25/BND25 | 0.20 | - | 0.33 [0.13–0.87] | 0.14 → 1.42 | - | -39.29% | - | - |
| ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF) | 0.58 | - | 1.09 [0.29–1.75] | 0.54 → 1.38 | - | -19.91% | - | - |
| SPY benchmark | 0.26 | - | 0.55 [0.18–1.15] | 0.21 → 1.19 | - | -47.10% | - | - |
