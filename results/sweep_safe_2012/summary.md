# Sweep summary

- Data: 2012-01-03..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-20; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-20; 20 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 62 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL | 0.3 | 0.6 | QQQ<SMA200 | 0.86 | 0.83 | 0.90 [0.61–1.29] | 0.83 → 1.12 | 10.5/33 | -27.65% | 0.51 |  |
| BTAL | 0.35 | 0.7 | QQQ<SMA200 | 0.82 | 0.81 | 0.83 [0.55–1.29] | 0.80 → 1.18 | 21/44 | -34.12% | 0.60 |  |
| BTAL | 0.3 | 0.7 | QQQ<SMA200 | 0.89 | 0.81 | 0.84 [0.61–1.37] | 0.87 → 1.12 | 10/51 | -28.47% | 0.56 |  |
| BTAL | 0.4 | 0.8 | QQQ<SMA200 | 0.80 | 0.81 | 0.79 [0.49–1.30] | 0.76 → 1.18 | 30.5/50 | -40.35% | 0.68 | yes* |
| BTAL | 0.35 | 0.6 | QQQ<SMA200 | 0.84 | 0.79 | 0.91 [0.59–1.30] | 0.80 → 1.16 | 9/39 | -31.14% | 0.53 |  |
| BTAL | 0.4 | 0.7 | QQQ<SMA200 | 0.81 | 0.79 | 0.83 [0.54–1.27] | 0.78 → 1.16 | 15.5/41 | -37.33% | 0.62 | yes* |
| BTAL | 0.25 | 0.7 | QQQ<SMA200 | 0.84 | 0.80 | 0.78 [0.55–1.25] | 0.82 → 1.07 | 28/59 | -25.40% | 0.51 | yes* |
| BTAL | 0.35 | 0.8 | QQQ<SMA200 | 0.84 | 0.80 | 0.78 [0.54–1.36] | 0.81 → 1.16 | 24.5/56 | -35.10% | 0.65 | yes* |
| - | 0.25 | 0.5 | QQQ<SMA200 | 0.81 | 0.79 | 0.77 [0.51–1.20] | 0.74 → 1.22 | 26.5/51 | -28.55% | 0.43 | yes* |
| BTAL | 0.25 | 0.5 | QQQ<SMA200 | 0.77 | 0.83 | 0.98 [0.58–1.41] | 0.75 → 0.99 | 19/61 | -25.41% | 0.43 | yes* |
| BTAL | 0.25 | 0.6 | QQQ<SMA200 | 0.83 | 0.77 | 0.87 [0.60–1.23] | 0.81 → 1.00 | 18.5/54 | -25.09% | 0.48 | yes* |
| BTAL | 0.3 | 0.5 | QQQ<SMA200 | 0.86 | 0.77 | 1.00 [0.65–1.46] | 0.82 → 1.15 | 4/49 | -25.07% | 0.45 | yes* |
| BTAL | 0.25 | 0.8 | QQQ<SMA200 | 0.80 | 0.81 | 0.76 [0.50–1.23] | 0.78 → 1.11 | 30.5/62 | -27.60% | 0.54 | yes* |
| - | 0.25 | 0.6 | QQQ<SMA200 | 0.83 | 0.79 | 0.76 [0.51–1.30] | 0.77 → 1.19 | 18.5/58 | -29.31% | 0.48 | yes* |
| BTAL | 0.3 | 0.8 | QQQ<SMA200 | 0.81 | 0.80 | 0.76 [0.55–1.40] | 0.76 → 1.15 | 18/60 | -31.89% | 0.60 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.53 | - | 0.71 [0.29–1.67] | 0.46 → 1.23 | - | -44.81% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.61 | - | 0.74 [0.43–1.66] | 0.57 → 0.98 | - | -37.73% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
