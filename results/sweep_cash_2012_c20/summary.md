# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (* 20) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 30 feasible grid strategies by robust_score

| safe | sigma_target | w_max | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BTAL | 0.3 | 0.6 | 0.84 | 0.78 | 0.88 [0.59–1.27] | 0.82 → 1.09 | 4.5/19 | -27.85% | 0.51 | yes* |
| BIL25+BTAL75 | 0.3 | 0.6 | 0.82 | 0.77 | 0.82 [0.56–1.25] | 0.79 → 1.17 | 7/22 | -29.51% | 0.51 | yes* |
| BIL50+BTAL50 | 0.2 | 0.6 | 0.79 | 0.77 | 0.79 [0.55–1.33] | 0.75 → 1.15 | 5/20 | -22.93% | 0.42 | yes* |
| BIL50+BTAL50 | 0.3 | 0.6 | 0.78 | 0.77 | 0.76 [0.51–1.22] | 0.74 → 1.18 | 12/27 | -31.41% | 0.51 | yes* |
| BIL25+BTAL75 | 0.25 | 0.6 | 0.89 | 0.75 | 0.83 [0.61–1.33] | 0.86 → 1.10 | 5/14 | -23.80% | 0.48 | yes* |
| BIL25+BTAL75 | 0.2 | 0.6 | 0.82 | 0.75 | 0.77 [0.55–1.23] | 0.80 → 1.04 | 9.5/26 | -21.21% | 0.42 | yes* |
| BIL25+BTAL75 | 0.25 | 0.8 | 0.75 | 0.75 | 0.74 [0.46–1.22] | 0.71 → 1.11 | 15.5/24 | -29.46% | 0.54 | yes* |
| BIL50+BTAL50 | 0.2 | 0.8 | 0.77 | 0.74 | 0.79 [0.40–1.13] | 0.73 → 1.21 | 17/27 | -25.03% | 0.46 | yes* |
| BIL50+BTAL50 | 0.25 | 0.6 | 0.83 | 0.74 | 0.78 [0.56–1.29] | 0.80 → 1.15 | 8/18 | -26.06% | 0.48 | yes* |
| BIL25+BTAL75 | 0.2 | 0.8 | 0.75 | 0.75 | 0.73 [0.40–1.10] | 0.73 → 1.09 | 15.5/29 | -24.53% | 0.46 | yes* |
| BIL75+BTAL25 | 0.2 | 0.8 | 0.76 | 0.73 | 0.73 [0.38–1.15] | 0.70 → 1.25 | 21.5/28 | -26.30% | 0.46 | yes* |
| BTAL | 0.3 | 0.8 | 0.78 | 0.76 | 0.73 [0.53–1.36] | 0.74 → 1.11 | 13/22 | -32.34% | 0.60 | yes* |
| BIL75+BTAL25 | 0.25 | 0.6 | 0.79 | 0.73 | 0.72 [0.49–1.26] | 0.74 → 1.16 | 14/24 | -28.37% | 0.48 | yes* |
| BIL50+BTAL50 | 0.25 | 0.8 | 0.74 | 0.77 | 0.71 [0.45–1.23] | 0.69 → 1.14 | 17/26 | -30.80% | 0.54 | yes* |
| BIL75+BTAL25 | 0.2 | 0.6 | 0.76 | 0.76 | 0.71 [0.49–1.29] | 0.69 → 1.19 | 10.5/28 | -24.92% | 0.42 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.60 | - | 0.74 [0.43–1.65] | 0.57 → 0.96 | - | -37.74% | - | - |
| TQQQ50/BIL50 gate QQQ<SMA200 | 0.59 | - | 0.60 [0.31–1.19] | 0.50 → 1.08 | - | -41.46% | - | - |
| SPY benchmark | 0.43 | - | 0.53 [0.25–1.14] | 0.36 → 1.19 | - | -33.77% | - | - |
