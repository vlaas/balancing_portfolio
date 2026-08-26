# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 14 of 14 feasible grid strategies by robust_score

| gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2 | 0.87 | - | 0.90 [0.61–1.29] | 0.83 → 1.06 | 3/5 | -27.24% | 0.51 |  |
| QQQ<SMA200 | 0.86 | - | 0.90 [0.61–1.29] | 0.83 → 1.11 | 2/4 | -27.65% | 0.51 |  |
| QQQ<SMA10M | 0.86 | - | 0.89 [0.59–1.28] | 0.83 → 1.11 | 3.5/7 | -27.66% | 0.51 |  |
| QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 | 0.85 | - | 0.88 [0.59–1.28] | 0.83 → 0.95 | 4.5/7 | -27.17% | 0.51 |  |
| QQQ<SMA200|QQQ:MOMM1-3-6-12U<=2 | 0.79 | - | 0.85 [0.57–1.27] | 0.75 → 0.95 | 6/10 | -27.16% | 0.50 |  |
| QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 off30 | 0.81 | - | 0.78 [0.55–1.23] | 0.79 → 0.94 | 8.5/11 | -27.16% | 0.50 |  |
| QQQ:MOM12M<=0 | 0.72 | - | 0.81 [0.43–1.47] | 0.70 → 0.92 | 7/12 | -31.97% | 0.51 |  |
| - | 0.72 | - | 0.86 [0.39–1.54] | 0.65 → 1.33 | 4/13 | -34.57% | 0.53 |  |
| QQQ:MOMM1-3-6-12U<=0 | 0.69 | - | 0.77 [0.41–1.27] | 0.67 → 0.96 | 9/14 | -32.29% | 0.51 |  |
| QQQ:MOMM1-3-6-12U<=0 off30 | 0.67 | - | 0.70 [0.40–1.22] | 0.63 → 0.96 | 11.5/13 | -32.29% | 0.51 |  |
| QQQ:MOM12M<=0 off0 | 0.70 | - | 0.65 [0.48–1.17] | 0.68 → 0.92 | 11/12 | -30.56% | 0.49 |  |
| QQQ<SMA200 off0 | 0.55 | - | 0.78 [0.43–1.22] | 0.59 → 0.53 | 9/12 | -36.13% | 0.47 |  |
| QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 off0 | 0.48 | - | 0.56 [0.23–1.00] | 0.47 → 0.81 | 13/14 | -39.02% | 0.47 |  |
| QQQ:MOMM1-3-6-12U<=0 off0 | 0.46 | - | 0.46 [0.23–1.00] | 0.42 → 0.96 | 14/14 | -39.02% | 0.48 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.53 | - | 0.71 [0.29–1.67] | 0.46 → 1.22 | - | -44.81% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 0.97 | - | -37.73% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
