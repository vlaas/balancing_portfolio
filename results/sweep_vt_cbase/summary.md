# Sweep summary

- Data: 2012-01-03..2026-08-14
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-14; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-14; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 96 feasible grid strategies by robust_score

| vol.lam | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.3 | 0.6 | QQQ<SMA200 | 0.83 | 0.81 | 0.89 [0.58–1.29] | 0.82 → 1.03 | 22.5/60 | -28.23% | 0.51 | yes* |
| 0.75 | 0.3 | 0.7 | QQQ<SMA200 | 0.81 | 0.80 | 0.84 [0.55–1.42] | 0.82 → 1.01 | 34.5/84 | -30.25% | 0.56 | yes* |
| 0.8 | 0.3 | 0.7 | QQQ<SMA200 | 0.86 | 0.80 | 0.85 [0.59–1.36] | 0.87 → 1.04 | 17.5/83 | -28.98% | 0.56 |  |
| 0.8 | 0.35 | 0.7 | QQQ<SMA200 | 0.80 | 0.79 | 0.82 [0.53–1.28] | 0.79 → 1.12 | 44/75 | -34.63% | 0.60 |  |
| 0.85 | 0.25 | 0.8 | QQQ<SMA200 | 0.81 | 0.79 | 0.80 [0.45–1.23] | 0.80 → 1.00 | 59/88 | -26.59% | 0.53 | yes* |
| 0.75 | 0.35 | 0.6 | QQQ<SMA200 | 0.82 | 0.79 | 0.89 [0.58–1.30] | 0.81 → 1.08 | 15/65 | -30.69% | 0.53 | yes* |
| 0.75 | 0.4 | 0.7 | QQQ<SMA200 | 0.81 | 0.79 | 0.82 [0.54–1.27] | 0.79 → 1.13 | 31.5/73 | -36.82% | 0.62 | yes* |
| 0.75 | 0.25 | 0.6 | QQQ<SMA200 | 0.79 | 0.81 | 0.83 [0.52–1.22] | 0.78 → 0.87 | 44.5/79 | -25.69% | 0.48 | yes* |
| 0.75 | 0.3 | 0.6 | QQQ<SMA200 | 0.83 | 0.79 | 0.90 [0.58–1.32] | 0.86 → 0.98 | 20/57 | -27.65% | 0.51 | yes* |
| 0.8 | 0.25 | 0.6 | QQQ<SMA200 | 0.81 | 0.79 | 0.86 [0.55–1.22] | 0.81 → 0.89 | 33/75 | -25.09% | 0.48 | yes* |
| 0.8 | 0.4 | 0.8 | QQQ<SMA200 | 0.78 | 0.79 | 0.79 [0.48–1.29] | 0.75 → 1.15 | 44.5/85 | -40.81% | 0.68 | yes* |
| 0.85 | 0.25 | 0.7 | QQQ<SMA200 | 0.83 | 0.78 | 0.80 [0.52–1.22] | 0.81 → 0.97 | 42.5/89 | -25.09% | 0.51 | yes* |
| 0.75 | 0.35 | 0.7 | QQQ<SMA200 | 0.81 | 0.78 | 0.86 [0.56–1.33] | 0.81 → 1.10 | 31.5/77 | -34.00% | 0.59 | yes* |
| 0.75 | 0.4 | 0.8 | QQQ<SMA200 | 0.79 | 0.78 | 0.81 [0.50–1.34] | 0.78 → 1.14 | 41.5/87 | -40.12% | 0.68 | yes* |
| 0.8 | 0.35 | 0.8 | QQQ<SMA200 | 0.82 | 0.78 | 0.78 [0.53–1.35] | 0.81 → 1.12 | 29/89 | -35.54% | 0.65 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.52 | - | 0.70 [0.27–1.67] | 0.46 → 1.15 | - | -45.01% | - | - |
| TQQQ60/BTAL40 | 0.52 | - | 0.65 [0.23–1.55] | 0.44 → 1.22 | - | -54.52% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.59 | - | 0.70 [0.41–1.64] | 0.56 → 0.90 | - | -37.73% | - | - |
| SPY benchmark | 0.39 | - | 0.44 [0.21–0.92] | 0.31 → 1.16 | - | -34.03% | - | - |
