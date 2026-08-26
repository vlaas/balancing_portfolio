# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 21 feasible grid strategies by robust_score

| gate.threshold | gate.w_off | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| -0.03 | - | 0.72 | 0.72 | 0.82 [0.45–1.48] | 0.69 → 1.07 | 2.5/7 | -32.55% | 0.52 | yes* |
| -0.03 | 0.3 | 0.72 | 0.71 | 0.81 [0.44–1.47] | 0.69 → 1.04 | 4.5/9 | -32.40% | 0.51 | yes* |
| -0.02 | - | 0.72 | 0.70 | 0.81 [0.45–1.47] | 0.69 → 1.07 | 2.5/6 | -32.56% | 0.52 |  |
| -0.01 | - | 0.70 | 0.69 | 0.78 [0.41–1.29] | 0.67 → 0.96 | 8/16 | -32.29% | 0.51 |  |
| 0 | - | 0.69 | 0.69 | 0.77 [0.41–1.27] | 0.67 → 0.96 | 10/16 | -32.29% | 0.51 |  |
| -0.02 | 0.3 | 0.71 | 0.68 | 0.79 [0.44–1.41] | 0.68 → 1.04 | 5/9 | -32.40% | 0.51 |  |
| -0.01 | 0.3 | 0.68 | 0.67 | 0.76 [0.41–1.29] | 0.65 → 0.96 | 11/15 | -32.29% | 0.51 |  |
| 0 | 0.3 | 0.67 | 0.66 | 0.70 [0.40–1.22] | 0.63 → 0.96 | 13/16 | -32.29% | 0.51 |  |
| -0.03 | 0 | 0.68 | 0.65 | 0.74 [0.43–1.34] | 0.68 → 0.94 | 10/13 | -32.32% | 0.50 | yes* |
| 0.01 | - | 0.69 | 0.65 | 0.85 [0.41–1.27] | 0.66 → 0.95 | 9/18 | -32.29% | 0.51 |  |
| 0.02 | - | 0.65 | 0.69 | 0.83 [0.41–1.27] | 0.61 → 0.95 | 10.5/18 | -32.29% | 0.50 |  |
| 0.03 | - | 0.79 | 0.65 | 0.85 [0.56–1.27] | 0.75 → 0.95 | 2/12 | -27.17% | 0.50 | yes* |
| 0.01 | 0.3 | 0.66 | 0.61 | 0.70 [0.38–1.20] | 0.62 → 0.94 | 14.5/20 | -32.29% | 0.50 |  |
| 0.02 | 0.3 | 0.61 | 0.66 | 0.68 [0.38–1.20] | 0.56 → 0.94 | 15/20 | -32.29% | 0.50 |  |
| 0.03 | 0.3 | 0.74 | 0.61 | 0.80 [0.50–1.28] | 0.69 → 0.92 | 7/16 | -27.17% | 0.49 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 | 0.72 | - | 0.86 [0.39–1.54] | 0.65 → 1.33 | - | -34.57% | 0.53 | - |
| VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.86 | - | 0.90 [0.61–1.29] | 0.83 → 1.11 | - | -27.65% | 0.51 | - |
| VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200 off0 | 0.55 | - | 0.78 [0.43–1.22] | 0.59 → 0.53 | - | -36.13% | 0.47 | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 0.97 | - | -37.73% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
