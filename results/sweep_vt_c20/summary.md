# Sweep summary

- Data: 2012-01-03..2026-08-14
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-14; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-14; 20 sensitivity
- Costs: flat 20 bps (CLI override), cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 96 feasible grid strategies by robust_score

| vol.lam | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.3 | 0.6 | QQQ<SMA200 | 0.81 | 0.79 | 0.87 [0.56–1.27] | 0.81 → 1.01 | 21/55 | -28.42% | 0.51 | yes* |
| 0.8 | 0.35 | 0.7 | QQQ<SMA200 | 0.79 | 0.78 | 0.80 [0.52–1.26] | 0.78 → 1.10 | 44/75 | -34.88% | 0.60 |  |
| 0.75 | 0.35 | 0.6 | QQQ<SMA200 | 0.81 | 0.78 | 0.88 [0.57–1.29] | 0.80 → 1.07 | 13.5/63 | -30.87% | 0.53 | yes* |
| 0.8 | 0.3 | 0.7 | QQQ<SMA200 | 0.84 | 0.77 | 0.82 [0.57–1.34] | 0.85 → 1.01 | 18.5/83 | -29.23% | 0.56 |  |
| 0.75 | 0.4 | 0.7 | QQQ<SMA200 | 0.79 | 0.77 | 0.80 [0.53–1.25] | 0.78 → 1.12 | 29/70 | -37.05% | 0.62 | yes* |
| 0.75 | 0.3 | 0.7 | QQQ<SMA200 | 0.79 | 0.77 | 0.81 [0.53–1.40] | 0.80 → 0.99 | 36/85 | -30.56% | 0.56 | yes* |
| 0.8 | 0.4 | 0.8 | QQQ<SMA200 | 0.77 | 0.77 | 0.77 [0.46–1.27] | 0.74 → 1.13 | 43.5/84 | -41.08% | 0.68 | yes* |
| 0.75 | 0.25 | 0.6 | QQQ<SMA200 | 0.76 | 0.77 | 0.81 [0.50–1.19] | 0.76 → 0.84 | 47/80 | -25.89% | 0.48 | yes* |
| 0.75 | 0.3 | 0.6 | QQQ<SMA200 | 0.82 | 0.76 | 0.88 [0.56–1.31] | 0.84 → 0.96 | 20/57 | -27.86% | 0.51 | yes* |
| 0.8 | 0.25 | 0.6 | QQQ<SMA200 | 0.79 | 0.76 | 0.84 [0.53–1.20] | 0.79 → 0.86 | 36.5/77 | -25.27% | 0.48 | yes* |
| 0.85 | 0.25 | 0.7 | QQQ<SMA200 | 0.80 | 0.76 | 0.77 [0.50–1.19] | 0.79 → 0.93 | 49/89 | -25.29% | 0.51 | yes* |
| 0.75 | 0.35 | 0.7 | QQQ<SMA200 | 0.79 | 0.76 | 0.84 [0.54–1.31] | 0.80 → 1.08 | 32.5/76 | -34.27% | 0.59 | yes* |
| 0.75 | 0.4 | 0.8 | QQQ<SMA200 | 0.77 | 0.76 | 0.79 [0.49–1.32] | 0.76 → 1.12 | 41/86 | -40.42% | 0.68 | yes* |
| 0.8 | 0.35 | 0.8 | QQQ<SMA200 | 0.80 | 0.76 | 0.76 [0.51–1.33] | 0.79 → 1.09 | 32/88 | -35.82% | 0.65 | yes* |
| 0.75 | 0.4 | 0.6 | QQQ<SMA200 | 0.78 | 0.76 | 0.86 [0.55–1.31] | 0.76 → 1.04 | 23/66 | -33.73% | 0.54 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.52 | - | 0.70 [0.26–1.66] | 0.45 → 1.14 | - | -45.15% | - | - |
| TQQQ60/BTAL40 | 0.52 | - | 0.65 [0.23–1.54] | 0.44 → 1.21 | - | -54.62% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.59 | - | 0.70 [0.40–1.63] | 0.56 → 0.89 | - | -37.74% | - | - |
| SPY benchmark | 0.38 | - | 0.44 [0.21–0.91] | 0.31 → 1.15 | - | -34.08% | - | - |
