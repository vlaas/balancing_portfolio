# Sweep summary

- Data: 2012-01-03..2026-08-20
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-20; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-20; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 96 feasible grid strategies by robust_score

| vol.lam | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.3 | 0.6 | QQQ<SMA200 | 0.87 | 0.83 | 0.90 [0.61–1.29] | 0.84 → 1.14 | 18/56 | -27.55% | 0.51 | yes* |
| 0.75 | 0.35 | 0.6 | QQQ<SMA200 | 0.86 | 0.82 | 0.91 [0.61–1.30] | 0.82 → 1.19 | 13/53 | -30.05% | 0.53 | yes* |
| 0.8 | 0.35 | 0.7 | QQQ<SMA200 | 0.83 | 0.82 | 0.83 [0.55–1.29] | 0.80 → 1.20 | 36.5/75 | -34.03% | 0.60 |  |
| 0.8 | 0.3 | 0.7 | QQQ<SMA200 | 0.89 | 0.81 | 0.84 [0.61–1.37] | 0.87 → 1.14 | 14.5/83 | -28.38% | 0.56 |  |
| 0.75 | 0.3 | 0.7 | QQQ<SMA200 | 0.84 | 0.81 | 0.84 [0.57–1.43] | 0.83 → 1.12 | 31.5/84 | -29.67% | 0.56 | yes* |
| 0.75 | 0.4 | 0.7 | QQQ<SMA200 | 0.84 | 0.81 | 0.84 [0.57–1.29] | 0.81 → 1.20 | 25/71 | -36.24% | 0.62 | yes* |
| 0.75 | 0.25 | 0.6 | QQQ<SMA200 | 0.81 | 0.83 | 0.86 [0.57–1.21] | 0.79 → 1.01 | 44/71 | -25.69% | 0.48 | yes* |
| 0.75 | 0.3 | 0.6 | QQQ<SMA200 | 0.88 | 0.81 | 0.92 [0.65–1.35] | 0.87 → 1.10 | 14/58 | -26.96% | 0.51 | yes* |
| 0.8 | 0.25 | 0.6 | QQQ<SMA200 | 0.83 | 0.81 | 0.88 [0.60–1.23] | 0.82 → 1.03 | 32.5/73 | -25.09% | 0.48 | yes* |
| 0.85 | 0.25 | 0.8 | QQQ<SMA200 | 0.83 | 0.81 | 0.82 [0.46–1.22] | 0.80 → 1.13 | 56.5/88 | -26.59% | 0.54 | yes* |
| 0.75 | 0.35 | 0.7 | QQQ<SMA200 | 0.84 | 0.80 | 0.87 [0.58–1.34] | 0.82 → 1.19 | 25.5/77 | -33.38% | 0.60 | yes* |
| 0.75 | 0.4 | 0.8 | QQQ<SMA200 | 0.81 | 0.80 | 0.81 [0.52–1.35] | 0.78 → 1.19 | 43.5/86 | -39.57% | 0.68 | yes* |
| 0.85 | 0.25 | 0.7 | QQQ<SMA200 | 0.85 | 0.80 | 0.82 [0.53–1.23] | 0.82 → 1.10 | 45/89 | -25.09% | 0.51 | yes* |
| 0.75 | 0.4 | 0.6 | QQQ<SMA200 | 0.82 | 0.80 | 0.90 [0.59–1.33] | 0.79 → 1.13 | 21/56 | -32.97% | 0.54 | yes* |
| 0.8 | 0.35 | 0.6 | QQQ<SMA200 | 0.84 | 0.80 | 0.91 [0.59–1.30] | 0.80 → 1.18 | 16.5/58 | -31.04% | 0.53 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.53 | - | 0.71 [0.29–1.67] | 0.47 → 1.26 | - | -44.81% | - | - |
| TQQQ60/BTAL40 | 0.53 | - | 0.66 [0.24–1.55] | 0.45 → 1.27 | - | -54.17% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 1.01 | - | -37.73% | - | - |
| SPY benchmark | 0.44 | - | 0.53 [0.26–1.19] | 0.37 → 1.20 | - | -33.66% | - | - |
