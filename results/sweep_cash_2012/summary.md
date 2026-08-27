# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 30 feasible grid strategies by robust_score

| safe | sigma_target | w_max | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BIL50+BTAL50 | 0.2 | 0.6 | 0.83 | 0.82 | 0.82 [0.59–1.37] | 0.79 → 1.21 | 5/20 | -22.46% | 0.42 | yes* |
| BTAL | 0.3 | 0.6 | 0.86 | 0.81 | 0.90 [0.61–1.29] | 0.83 → 1.11 | 4.5/20 | -27.65% | 0.51 | yes* |
| BIL25+BTAL75 | 0.3 | 0.6 | 0.83 | 0.81 | 0.84 [0.57–1.26] | 0.80 → 1.19 | 9/25 | -29.26% | 0.51 | yes* |
| BIL25+BTAL75 | 0.2 | 0.6 | 0.85 | 0.80 | 0.82 [0.58–1.27] | 0.83 → 1.09 | 9/26 | -20.93% | 0.42 | yes* |
| BIL25+BTAL75 | 0.25 | 0.6 | 0.91 | 0.79 | 0.86 [0.63–1.36] | 0.88 → 1.13 | 5/14 | -23.55% | 0.48 | yes* |
| BIL50+BTAL50 | 0.2 | 0.8 | 0.82 | 0.78 | 0.83 [0.43–1.20] | 0.78 → 1.29 | 13/27 | -24.44% | 0.46 | yes* |
| BIL50+BTAL50 | 0.25 | 0.6 | 0.86 | 0.78 | 0.81 [0.58–1.32] | 0.82 → 1.18 | 9/18 | -25.80% | 0.48 | yes* |
| BIL25+BTAL75 | 0.2 | 0.8 | 0.80 | 0.79 | 0.78 [0.44–1.17] | 0.78 → 1.15 | 12/28 | -23.95% | 0.46 | yes* |
| BIL50+BTAL50 | 0.3 | 0.6 | 0.80 | 0.80 | 0.78 [0.52–1.23] | 0.76 → 1.20 | 13.5/27 | -31.15% | 0.51 | yes* |
| BIL25+BTAL75 | 0.25 | 0.8 | 0.79 | 0.80 | 0.78 [0.49–1.26] | 0.75 → 1.17 | 15/24 | -28.90% | 0.54 | yes* |
| BIL75+BTAL25 | 0.2 | 0.8 | 0.82 | 0.77 | 0.78 [0.42–1.22] | 0.76 → 1.30 | 17/26 | -25.43% | 0.46 | yes* |
| BTAL | 0.3 | 0.8 | 0.81 | 0.80 | 0.76 [0.55–1.40] | 0.76 → 1.14 | 14/21 | -31.89% | 0.60 | yes* |
| BIL50+BTAL50 | 0.25 | 0.8 | 0.78 | 0.80 | 0.75 [0.48–1.28] | 0.73 → 1.21 | 15.5/26 | -30.22% | 0.54 | yes* |
| BIL75+BTAL25 | 0.25 | 0.6 | 0.81 | 0.77 | 0.75 [0.51–1.28] | 0.76 → 1.19 | 14.5/24 | -28.11% | 0.48 | yes* |
| BIL75+BTAL25 | 0.2 | 0.6 | 0.79 | 0.81 | 0.75 [0.52–1.33] | 0.73 → 1.23 | 10/28 | -24.45% | 0.42 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 0.97 | - | -37.73% | - | - |
| TQQQ50/BIL50 gate QQQ<SMA200 | 0.59 | - | 0.61 [0.31–1.20] | 0.51 → 1.09 | - | -41.45% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
