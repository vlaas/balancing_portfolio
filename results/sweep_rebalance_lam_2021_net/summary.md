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

## Top 15 of 72 feasible grid strategies by robust_score

| vol.lam | sigma_target | rebalance | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.8 | 0.2 | - | 0.86 | 0.79 | 0.98 [0.80–1.73] | 0.90 → 0.89 | 11/24 | -19.07% | 0.38 | yes* |
| 0.8 | 0.3 | 3m+2 | 0.89 | 0.77 | 1.06 [0.83–1.28] | 0.91 → 1.11 | 13.5/36 | -30.98% | 0.55 | yes* |
| 0.8 | 0.3 | - | 0.79 | 0.76 | 0.91 [0.70–1.25] | 0.78 → 0.99 | 28/52 | -28.34% | 0.53 | yes* |
| 0.8 | 0.2 | 2m | 0.74 | 0.73 | 0.81 [0.64–1.32] | 0.80 → 0.78 | 48/63 | -22.93% | 0.38 | yes* |
| 0.8 | 0.3 | 2m | 0.73 | 0.74 | 0.80 [0.55–1.11] | 0.68 → 1.09 | 39/70 | -33.46% | 0.54 | yes* |
| 0.9 | 0.3 | 2m | 0.79 | 0.73 | 0.87 [0.69–1.11] | 0.84 → 0.83 | 35.5/57 | -30.13% | 0.52 | yes* |
| 0.8 | 0.2 | 3m+2 | 0.82 | 0.71 | 1.07 [0.83–2.28] | 0.93 → 0.88 | 10/27 | -24.79% | 0.38 | yes* |
| 0.9 | 0.3 | - | 0.76 | 0.70 | 0.89 [0.72–1.13] | 0.83 → 0.79 | 35/39 | -28.27% | 0.52 | yes* |
| 0.9 | 0.2 | - | 0.83 | 0.75 | 0.98 [0.76–1.78] | 0.98 → 0.69 | 17/32 | -18.29% | 0.35 | yes* |
| 0.9 | 0.2 | 3m+2 | 0.71 | 0.67 | 0.88 [0.70–1.54] | 0.79 → 0.73 | 36/54 | -22.28% | 0.35 | yes* |
| 0.9 | 0.3 | 3m+2 | 0.77 | 0.64 | 0.94 [0.64–1.13] | 0.78 → 0.93 | 34.5/51 | -30.96% | 0.52 | yes* |
| 0.9 | 0.2 | 2m | 0.77 | 0.74 | 0.87 [0.71–1.66] | 0.90 → 0.62 | 42.5/48 | -21.13% | 0.35 | yes* |
| 0.9 | 0.2 | 3m+1 | 0.86 | 0.61 | 1.18 [0.78–1.31] | 0.93 → 0.67 | 5.5/29 | -18.07% | 0.36 | yes* |
| 0.8 | 0.2 | 3m+1 | 0.77 | 0.61 | 1.13 [0.69–1.31] | 0.80 → 0.81 | 23.5/47 | -20.18% | 0.36 | yes* |
| 0.8 | 0.3 | 3m+1 | 0.61 | 0.61 | 0.85 [0.53–1.05] | 0.63 → 0.70 | 51.5/69 | -32.39% | 0.51 | yes* |

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
