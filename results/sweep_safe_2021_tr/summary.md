# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20
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
| KMLM | 0.25 | 0.5 | QQQ<SMA200 | 0.90 | 0.88 | 1.04 [0.51–1.23] | 1.11 → 1.04 | 55.5/123 | -26.67% | 0.38 | yes* |
| KMLM | 0.3 | 0.6 | QQQ<SMA200 | 0.88 | 0.86 | 1.02 [0.58–1.16] | 1.04 → 1.02 | 49/111 | -30.74% | 0.46 |  |
| KMLM | 0.25 | 0.6 | QQQ<SMA200 | 0.88 | 0.85 | 0.99 [0.47–1.26] | 1.10 → 1.11 | 57/124 | -28.43% | 0.42 | yes* |
| KMLM | 0.25 | 0.7 | QQQ<SMA200 | 0.85 | 0.86 | 0.95 [0.46–1.32] | 1.11 → 1.19 | 59.5/126 | -30.22% | 0.44 | yes* |
| KMLM | 0.25 | 0.8 | QQQ<SMA200 | 0.86 | 0.85 | 0.94 [0.46–1.41] | 1.12 → 1.23 | 59.5/125 | -31.11% | 0.46 | yes* |
| KMLM | 0.3 | 0.7 | QQQ<SMA200 | 0.87 | 0.85 | 1.01 [0.56–1.18] | 1.03 → 1.09 | 51/115 | -31.87% | 0.50 |  |
| KMLM | 0.3 | 0.8 | QQQ<SMA200 | 0.85 | 0.85 | 1.00 [0.54–1.23] | 1.03 → 1.16 | 49.5/121 | -33.42% | 0.53 | yes* |
| KMLM | 0.35 | 0.7 | QQQ<SMA200 | 0.85 | 0.84 | 0.98 [0.64–1.10] | 0.97 → 1.00 | 44.5/98 | -34.65% | 0.54 |  |
| KMLM | 0.35 | 0.8 | QQQ<SMA200 | 0.85 | 0.83 | 0.98 [0.62–1.11] | 0.96 → 1.06 | 46.5/107 | -35.71% | 0.58 | yes* |
| KMLM | 0.4 | 0.8 | QQQ<SMA200 | 0.83 | 0.84 | 0.93 [0.69–1.15] | 0.89 → 0.99 | 41.5/87 | -38.44% | 0.62 | yes* |
| DBMF | 0.25 | 0.5 | QQQ<SMA200 | 0.84 | 0.82 | 1.02 [0.59–1.24] | 1.01 → 1.08 | 27.5/114 | -29.54% | 0.39 | yes* |
| DBMF | 0.3 | 0.6 | QQQ<SMA200 | 0.84 | 0.82 | 0.98 [0.66–1.11] | 0.96 → 1.03 | 25.5/92 | -32.29% | 0.46 |  |
| DBMF | 0.35 | 0.7 | QQQ<SMA200 | 0.83 | 0.82 | 0.91 [0.71–1.16] | 0.88 → 0.98 | 36/82 | -35.51% | 0.54 |  |
| DBMF | 0.3 | 0.8 | QQQ<SMA200 | 0.82 | 0.82 | 0.98 [0.62–1.14] | 0.94 → 1.08 | 37/106 | -34.42% | 0.53 | yes* |
| DBMF | 0.25 | 0.6 | QQQ<SMA200 | 0.82 | 0.82 | 1.01 [0.57–1.24] | 0.98 → 1.10 | 45/116 | -30.68% | 0.42 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.34 | - | 0.66 [0.22–1.29] | 0.36 → 0.55 | - | -44.77% | - | - |
| TQQQ50/DBMF50 | 0.50 | - | 0.57 [0.30–1.16] | 0.40 → 0.98 | - | -46.13% | - | - |
| TQQQ50/KMLM50 | 0.49 | - | 0.53 [0.33–1.06] | 0.42 → 0.87 | - | -44.75% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.54 | - | 0.84 [0.45–1.10] | 0.62 → 0.42 | - | -30.91% | - | - |
| SPY benchmark | 0.63 | - | 0.72 [0.42–1.21] | 0.57 → 0.99 | - | -24.08% | - | - |
