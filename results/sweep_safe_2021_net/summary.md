# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-20; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-20; 6 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-20 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 126 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KMLM | 0.25 | 0.5 | QQQ<SMA200 | 0.87 | 0.85 | 0.98 [0.48–1.15] | 1.05 → 1.01 | 56/123 | -26.74% | 0.38 | yes* |
| KMLM | 0.3 | 0.6 | QQQ<SMA200 | 0.85 | 0.84 | 0.97 [0.55–1.09] | 0.99 → 1.00 | 48/112 | -30.77% | 0.46 |  |
| KMLM | 0.3 | 0.8 | QQQ<SMA200 | 0.83 | 0.83 | 0.98 [0.51–1.17] | 0.98 → 1.15 | 47/121 | -33.48% | 0.53 | yes* |
| KMLM | 0.25 | 0.6 | QQQ<SMA200 | 0.85 | 0.83 | 0.95 [0.44–1.18] | 1.04 → 1.09 | 56.5/124 | -28.51% | 0.42 | yes* |
| KMLM | 0.25 | 0.7 | QQQ<SMA200 | 0.83 | 0.83 | 0.91 [0.43–1.25] | 1.05 → 1.17 | 58.5/126 | -30.28% | 0.44 | yes* |
| KMLM | 0.25 | 0.8 | QQQ<SMA200 | 0.83 | 0.83 | 0.91 [0.43–1.32] | 1.09 → 1.21 | 57/125 | -31.12% | 0.46 | yes* |
| KMLM | 0.3 | 0.7 | QQQ<SMA200 | 0.85 | 0.83 | 0.97 [0.53–1.12] | 0.98 → 1.07 | 48/115 | -31.93% | 0.50 |  |
| KMLM | 0.35 | 0.7 | QQQ<SMA200 | 0.83 | 0.82 | 0.94 [0.61–1.07] | 0.91 → 0.99 | 41/99 | -34.71% | 0.54 |  |
| KMLM | 0.35 | 0.8 | QQQ<SMA200 | 0.83 | 0.81 | 0.94 [0.59–1.08] | 0.90 → 1.05 | 41.5/107 | -35.77% | 0.58 | yes* |
| KMLM | 0.4 | 0.8 | QQQ<SMA200 | 0.81 | 0.82 | 0.86 [0.66–1.12] | 0.83 → 0.98 | 40/89 | -38.49% | 0.62 | yes* |
| DBMF | 0.35 | 0.7 | QQQ<SMA200 | 0.81 | 0.80 | 0.85 [0.69–1.13] | 0.82 → 0.96 | 41.5/82 | -35.69% | 0.54 |  |
| DBMF | 0.3 | 0.8 | QQQ<SMA200 | 0.80 | 0.79 | 0.93 [0.60–1.07] | 0.87 → 1.07 | 35.5/106 | -34.62% | 0.53 | yes* |
| DBMF | 0.35 | 0.8 | QQQ<SMA200 | 0.80 | 0.79 | 0.86 [0.66–1.12] | 0.82 → 0.98 | 41/87 | -36.61% | 0.58 | yes* |
| DBMF | 0.4 | 0.8 | QQQ<SMA200 | 0.79 | 0.80 | 0.80 [0.68–1.16] | 0.77 → 0.93 | 50.5/75 | -39.32% | 0.62 | yes* |
| DBMF | 0.25 | 0.5 | QQQ<SMA200 | 0.80 | 0.79 | 0.95 [0.56–1.12] | 0.97 → 1.06 | 36/116 | -29.85% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.34 | - | 0.65 [0.22–1.27] | 0.35 → 0.54 | - | -44.74% | - | - |
| TQQQ50/DBMF50 | 0.47 | - | 0.54 [0.28–1.12] | 0.38 → 0.96 | - | -46.94% | - | - |
| TQQQ50/KMLM50 | 0.47 | - | 0.51 [0.30–1.04] | 0.40 → 0.86 | - | -45.62% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.82 [0.45–1.07] | 0.61 → 0.42 | - | -30.99% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
