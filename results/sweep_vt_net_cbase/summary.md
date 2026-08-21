# Sweep summary

- Data: 2012-01-03..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-20; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-20; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 96 feasible grid strategies by robust_score

| vol.lam | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.3 | 0.6 | QQQ<SMA200 | 0.86 | 0.82 | 0.90 [0.61–1.29] | 0.83 → 1.12 | 16.5/56 | -27.65% | 0.51 | yes* |
| 0.75 | 0.35 | 0.6 | QQQ<SMA200 | 0.86 | 0.81 | 0.91 [0.61–1.30] | 0.82 → 1.17 | 13/53 | -30.14% | 0.53 | yes* |
| 0.8 | 0.35 | 0.7 | QQQ<SMA200 | 0.82 | 0.81 | 0.83 [0.55–1.29] | 0.80 → 1.18 | 36.5/75 | -34.12% | 0.60 |  |
| 0.8 | 0.3 | 0.7 | QQQ<SMA200 | 0.89 | 0.81 | 0.84 [0.61–1.37] | 0.87 → 1.12 | 14.5/83 | -28.47% | 0.56 |  |
| 0.75 | 0.3 | 0.7 | QQQ<SMA200 | 0.84 | 0.81 | 0.84 [0.57–1.43] | 0.83 → 1.09 | 31.5/84 | -29.75% | 0.56 | yes* |
| 0.75 | 0.4 | 0.7 | QQQ<SMA200 | 0.83 | 0.81 | 0.84 [0.57–1.29] | 0.80 → 1.18 | 25.5/72 | -36.33% | 0.62 | yes* |
| 0.75 | 0.25 | 0.6 | QQQ<SMA200 | 0.80 | 0.82 | 0.85 [0.57–1.21] | 0.79 → 0.98 | 43.5/71 | -25.69% | 0.48 | yes* |
| 0.75 | 0.3 | 0.6 | QQQ<SMA200 | 0.87 | 0.80 | 0.92 [0.65–1.35] | 0.87 → 1.07 | 14/58 | -27.07% | 0.51 | yes* |
| 0.8 | 0.25 | 0.6 | QQQ<SMA200 | 0.83 | 0.80 | 0.87 [0.60–1.23] | 0.81 → 1.00 | 34.5/74 | -25.09% | 0.48 | yes* |
| 0.85 | 0.25 | 0.8 | QQQ<SMA200 | 0.83 | 0.80 | 0.81 [0.46–1.22] | 0.80 → 1.10 | 56/88 | -26.59% | 0.53 | yes* |
| 0.85 | 0.25 | 0.7 | QQQ<SMA200 | 0.85 | 0.80 | 0.82 [0.53–1.23] | 0.82 → 1.08 | 45.5/89 | -25.09% | 0.51 | yes* |
| 0.75 | 0.35 | 0.7 | QQQ<SMA200 | 0.83 | 0.80 | 0.87 [0.58–1.34] | 0.82 → 1.17 | 25.5/77 | -33.48% | 0.59 | yes* |
| 0.75 | 0.4 | 0.8 | QQQ<SMA200 | 0.81 | 0.80 | 0.81 [0.52–1.35] | 0.78 → 1.17 | 43/86 | -39.65% | 0.68 | yes* |
| 0.8 | 0.4 | 0.8 | QQQ<SMA200 | 0.80 | 0.81 | 0.79 [0.49–1.30] | 0.76 → 1.18 | 44.5/85 | -40.35% | 0.68 | yes* |
| 0.75 | 0.4 | 0.6 | QQQ<SMA200 | 0.81 | 0.79 | 0.89 [0.59–1.33] | 0.78 → 1.11 | 21/57 | -33.06% | 0.54 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.53 | - | 0.71 [0.29–1.67] | 0.46 → 1.23 | - | -44.81% | - | - |
| TQQQ60/BTAL40 | 0.53 | - | 0.66 [0.24–1.55] | 0.45 → 1.26 | - | -54.22% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 0.98 | - | -37.73% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
