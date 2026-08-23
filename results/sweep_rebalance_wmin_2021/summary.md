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

## Top 15 of 24 feasible grid strategies by robust_score

| rebalance | w_min | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| - | 0 | 0.86 | 0.86 | 0.98 [0.80–1.73] | 0.90 → 0.89 | 9/17 | -19.07% | 0.38 | yes* |
| - | 0.1 | 0.86 | 0.85 | 0.98 [0.80–1.73] | 0.90 → 0.89 | 9/17 | -19.07% | 0.38 |  |
| 3m+2 | 0 | 0.82 | 0.82 | 1.07 [0.83–2.28] | 0.93 → 0.88 | 8/17 | -24.79% | 0.38 | yes* |
| 3m+2 | 0.1 | 0.82 | 0.82 | 1.07 [0.83–2.28] | 0.93 → 0.88 | 8/17 | -24.79% | 0.38 |  |
| 3m+2 | 0.2 | 0.82 | 0.82 | 1.07 [0.83–2.28] | 0.93 → 0.88 | 8/17 | -24.79% | 0.38 |  |
| 3m+2 | 0.3 | 0.82 | 0.82 | 1.07 [0.83–2.28] | 0.94 → 0.87 | 11/20 | -24.81% | 0.39 | yes* |
| 2m | 0 | 0.74 | 0.74 | 0.81 [0.64–1.32] | 0.80 → 0.78 | 19.5/22 | -22.93% | 0.38 | yes* |
| 2m | 0.1 | 0.74 | 0.74 | 0.81 [0.64–1.32] | 0.80 → 0.78 | 19.5/22 | -22.93% | 0.38 |  |
| - | 0.2 | 0.85 | 0.72 | 0.97 [0.80–1.61] | 0.89 → 0.89 | 11.5/17 | -19.07% | 0.38 |  |
| - | 0.3 | 0.72 | 0.85 | 0.87 [0.64–1.15] | 0.70 → 1.01 | 20/24 | -21.22% | 0.40 | yes* |
| 2m | 0.2 | 0.74 | 0.70 | 0.81 [0.64–1.32] | 0.80 → 0.78 | 19.5/22 | -22.93% | 0.38 |  |
| 2m | 0.3 | 0.70 | 0.74 | 0.75 [0.58–1.01] | 0.75 → 0.73 | 22/24 | -22.95% | 0.39 | yes* |
| 2w | 0.3 | 0.83 | 0.87 | 1.15 [0.70–1.49] | 0.95 → 0.62 | 7.5/22 | -19.51% | 0.37 | yes* |
| 2w | 0.2 | 0.87 | 0.83 | 1.16 [0.80–1.54] | 1.02 → 0.56 | 6/16 | -17.71% | 0.36 |  |
| 2w | 0 | 0.86 | 0.86 | 1.17 [0.85–1.52] | 1.07 → 0.41 | 9/14 | -17.23% | 0.36 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 rb 1w | 0.35 | - | 0.66 [0.21–1.32] | 0.36 → 0.52 | - | -45.26% | - | - |
| 50/50 | 0.34 | - | 0.65 [0.22–1.27] | 0.35 → 0.54 | - | -44.74% | - | - |
| TQQQ50/BTAL50 rb 3m | 0.39 | - | 0.62 [0.26–1.31] | 0.37 → 0.71 | - | -43.68% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 1w | 0.46 | - | 0.78 [0.35–1.12] | 0.53 → 0.43 | - | -34.26% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.82 [0.45–1.07] | 0.61 → 0.42 | - | -30.99% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 3m | 0.48 | - | 0.71 [0.37–0.91] | 0.54 → 0.41 | - | -30.56% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
