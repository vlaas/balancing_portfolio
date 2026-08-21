# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-20; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-20; 6 sensitivity
- Costs: flat 20 bps (CLI override), cash yield 3% (CLI override)
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-20 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 126 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KMLM | 0.25 | 0.5 | QQQ<SMA200 | 0.86 | 0.82 | 0.96 [0.46–1.14] | 1.03 → 1.00 | 52.5/123 | -26.82% | 0.38 | yes* |
| KMLM | 0.3 | 0.6 | QQQ<SMA200 | 0.84 | 0.82 | 0.96 [0.54–1.08] | 0.98 → 0.99 | 44.5/111 | -30.85% | 0.46 |  |
| KMLM | 0.35 | 0.7 | QQQ<SMA200 | 0.82 | 0.81 | 0.92 [0.60–1.06] | 0.89 → 0.97 | 39/98 | -34.77% | 0.54 |  |
| KMLM | 0.3 | 0.8 | QQQ<SMA200 | 0.80 | 0.80 | 0.95 [0.48–1.14] | 0.95 → 1.12 | 52/122 | -33.89% | 0.53 | yes* |
| KMLM | 0.35 | 0.8 | QQQ<SMA200 | 0.81 | 0.80 | 0.92 [0.57–1.05] | 0.88 → 1.03 | 43/108 | -35.85% | 0.58 | yes* |
| KMLM | 0.4 | 0.8 | QQQ<SMA200 | 0.80 | 0.81 | 0.84 [0.65–1.10] | 0.81 → 0.96 | 40.5/89 | -38.57% | 0.62 | yes* |
| KMLM | 0.25 | 0.6 | QQQ<SMA200 | 0.82 | 0.80 | 0.92 [0.42–1.16] | 1.02 → 1.08 | 58/124 | -28.81% | 0.42 | yes* |
| KMLM | 0.25 | 0.7 | QQQ<SMA200 | 0.80 | 0.80 | 0.88 [0.40–1.22] | 1.02 → 1.15 | 61.5/126 | -30.66% | 0.44 | yes* |
| KMLM | 0.25 | 0.8 | QQQ<SMA200 | 0.80 | 0.80 | 0.87 [0.41–1.29] | 1.05 → 1.18 | 63/125 | -31.51% | 0.46 | yes* |
| KMLM | 0.3 | 0.7 | QQQ<SMA200 | 0.83 | 0.80 | 0.95 [0.51–1.10] | 0.96 → 1.05 | 51/115 | -32.06% | 0.50 |  |
| DBMF | 0.35 | 0.7 | QQQ<SMA200 | 0.80 | 0.78 | 0.83 [0.67–1.11] | 0.80 → 0.95 | 40.5/83 | -35.75% | 0.54 |  |
| DBMF | 0.4 | 0.8 | QQQ<SMA200 | 0.77 | 0.78 | 0.78 [0.65–1.14] | 0.75 → 0.91 | 50.5/76 | -39.41% | 0.62 | yes* |
| KMLM | 0.4 | 0.7 | QQQ<SMA200 | 0.81 | 0.77 | 0.92 [0.66–1.09] | 0.89 → 0.88 | 38/87 | -37.36% | 0.57 | yes* |
| DBMF | 0.35 | 0.8 | QQQ<SMA200 | 0.78 | 0.77 | 0.83 [0.64–1.10] | 0.79 → 0.95 | 43.5/90 | -36.70% | 0.58 | yes* |
| DBMF | 0.25 | 0.5 | QQQ<SMA200 | 0.79 | 0.77 | 0.93 [0.54–1.10] | 0.94 → 1.04 | 34/115 | -30.04% | 0.39 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.33 | - | 0.64 [0.22–1.26] | 0.34 → 0.52 | - | -44.89% | - | - |
| TQQQ50/DBMF50 | 0.47 | - | 0.54 [0.27–1.12] | 0.38 → 0.95 | - | -47.08% | - | - |
| TQQQ50/KMLM50 | 0.46 | - | 0.50 [0.30–1.04] | 0.40 → 0.85 | - | -45.78% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.52 | - | 0.82 [0.44–1.06] | 0.60 → 0.40 | - | -31.18% | - | - |
| SPY benchmark | 0.60 | - | 0.71 [0.39–1.19] | 0.54 → 0.99 | - | -24.55% | - | - |
