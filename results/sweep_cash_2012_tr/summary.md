# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 30 feasible grid strategies by robust_score

| safe | sigma_target | w_max | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BIL50+BTAL50 | 0.2 | 0.6 | 0.84 | 0.83 | 0.83 [0.59–1.38] | 0.79 → 1.26 | 5/20 | -22.48% | 0.42 | yes* |
| BTAL | 0.3 | 0.6 | 0.87 | 0.81 | 0.90 [0.61–1.29] | 0.84 → 1.14 | 5.5/21 | -27.55% | 0.51 | yes* |
| BIL25+BTAL75 | 0.3 | 0.6 | 0.84 | 0.81 | 0.84 [0.57–1.26] | 0.81 → 1.22 | 9/25 | -29.14% | 0.51 | yes* |
| BIL25+BTAL75 | 0.2 | 0.6 | 0.86 | 0.81 | 0.83 [0.58–1.28] | 0.84 → 1.13 | 9.5/26 | -20.93% | 0.42 | yes* |
| BIL25+BTAL75 | 0.25 | 0.6 | 0.92 | 0.80 | 0.86 [0.63–1.36] | 0.89 → 1.16 | 5/14 | -23.43% | 0.48 | yes* |
| BIL50+BTAL50 | 0.2 | 0.8 | 0.83 | 0.79 | 0.85 [0.44–1.20] | 0.78 → 1.33 | 13/27 | -24.39% | 0.46 | yes* |
| BIL50+BTAL50 | 0.25 | 0.6 | 0.87 | 0.79 | 0.81 [0.58–1.32] | 0.83 → 1.21 | 9/18 | -25.66% | 0.48 | yes* |
| BIL25+BTAL75 | 0.2 | 0.8 | 0.81 | 0.80 | 0.79 [0.45–1.18] | 0.78 → 1.18 | 11.5/28 | -23.90% | 0.46 | yes* |
| BIL25+BTAL75 | 0.25 | 0.8 | 0.80 | 0.81 | 0.79 [0.49–1.26] | 0.76 → 1.19 | 15/25 | -28.93% | 0.54 | yes* |
| BIL50+BTAL50 | 0.3 | 0.6 | 0.81 | 0.81 | 0.78 [0.53–1.24] | 0.76 → 1.23 | 13.5/27 | -31.02% | 0.51 | yes* |
| BIL75+BTAL25 | 0.2 | 0.8 | 0.83 | 0.78 | 0.79 [0.43–1.23] | 0.77 → 1.33 | 17/26 | -25.44% | 0.46 | yes* |
| BIL75+BTAL25 | 0.2 | 0.6 | 0.80 | 0.82 | 0.77 [0.52–1.34] | 0.73 → 1.27 | 9.5/28 | -24.46% | 0.42 | yes* |
| BIL50+BTAL50 | 0.25 | 0.8 | 0.79 | 0.81 | 0.76 [0.48–1.28] | 0.73 → 1.23 | 16/26 | -30.24% | 0.54 | yes* |
| BTAL | 0.3 | 0.8 | 0.81 | 0.81 | 0.76 [0.55–1.40] | 0.77 → 1.16 | 15/22 | -31.92% | 0.60 | yes* |
| BIL75+BTAL25 | 0.25 | 0.6 | 0.82 | 0.78 | 0.76 [0.52–1.28] | 0.76 → 1.22 | 14.5/23 | -27.95% | 0.48 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 1.00 | - | -37.73% | - | - |
| TQQQ50/BIL50 gate QQQ<SMA200 | 0.60 | - | 0.61 [0.31–1.20] | 0.51 → 1.11 | - | -41.35% | - | - |
| SPY benchmark | 0.44 | - | 0.53 [0.26–1.19] | 0.37 → 1.20 | - | -33.66% | - | - |
