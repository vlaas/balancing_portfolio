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

## Top 15 of 498 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL25+KMLM75 | 0.2 | 0.4 | QQQ<SMA200 | 0.94 | 0.89 | 1.12 [0.55–1.45] | 1.26 → 0.95 | 224.5/464 | -19.87% | 0.31 | yes* |
| BTAL25+KMLM75 | 0.25 | 0.5 | QQQ<SMA200 | 0.91 | 0.88 | 1.08 [0.63–1.30] | 1.14 → 0.96 | 204/415 | -24.11% | 0.39 |  |
| BTAL50+KMLM50 | 0.2 | 0.5 | QQQ<SMA200 | 0.92 | 0.87 | 1.11 [0.65–1.61] | 1.27 → 1.02 | 206.5/390 | -18.72% | 0.34 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.6 | QQQ<SMA200 | 0.87 | 0.89 | 1.04 [0.60–1.68] | 1.16 → 1.13 | 227.5/430 | -20.67% | 0.36 | yes* |
| BTAL75+KMLM25 | 0.2 | 0.8 | QQQ<SMA200 | 0.87 | 0.87 | 1.01 [0.81–1.81] | 0.93 → 0.88 | 120/258 | -19.06% | 0.38 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.8 | QQQ<SMA200 | 0.92 | 0.87 | 1.09 [0.62–1.74] | 1.18 → 1.25 | 157/421 | -20.79% | 0.38 | yes* |
| BTAL50+DBMF50 | 0.2 | 0.4 | QQQ<SMA200 | 0.91 | 0.87 | 1.09 [0.79–1.61] | 1.16 → 0.89 | 89/311 | -18.33% | 0.31 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.7 | QQQ<SMA200 | 0.89 | 0.87 | 1.05 [0.61–1.72] | 1.17 → 1.20 | 201/429 | -20.79% | 0.37 | yes* |
| BTAL50+KMLM50 | 0.25 | 0.6 | QQQ<SMA200 | 0.90 | 0.87 | 1.04 [0.71–1.36] | 1.10 → 1.00 | 159/344 | -22.82% | 0.42 |  |
| BTAL50+DBMF50 | 0.25 | 0.5 | QQQ<SMA200 | 0.90 | 0.87 | 1.03 [0.83–1.31] | 1.05 → 0.90 | 125/236 | -22.19% | 0.39 |  |
| BTAL50+KMLM50 | 0.25 | 0.7 | QQQ<SMA200 | 0.87 | 0.86 | 1.02 [0.66–1.40] | 1.09 → 1.13 | 175.5/384 | -24.81% | 0.44 |  |
| KMLM | 0.3 | 0.6 | QQQ<SMA200 | 0.88 | 0.86 | 1.02 [0.58–1.16] | 1.04 → 1.02 | 201.5/434 | -30.74% | 0.46 |  |
| KMLM | 0.2 | 0.4 | QQQ<SMA200 | 0.90 | 0.86 | 0.96 [0.39–1.30] | 1.19 → 1.05 | 279.5/494 | -23.39% | 0.31 | yes* |
| KMLM | 0.25 | 0.5 | QQQ<SMA200 | 0.90 | 0.86 | 1.04 [0.51–1.23] | 1.11 → 1.04 | 234.5/472 | -26.67% | 0.38 |  |
| BTAL25+KMLM75 | 0.2 | 0.8 | QQQ<SMA200 | 0.89 | 0.86 | 1.02 [0.48–1.62] | 1.20 → 1.31 | 204.5/477 | -23.97% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.34 | - | 0.66 [0.22–1.29] | 0.36 → 0.55 | - | -44.77% | - | - |
| TQQQ50/DBMF50 | 0.50 | - | 0.57 [0.30–1.16] | 0.40 → 0.98 | - | -46.13% | - | - |
| TQQQ50/KMLM50 | 0.49 | - | 0.53 [0.33–1.06] | 0.42 → 0.87 | - | -44.75% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.54 | - | 0.84 [0.45–1.10] | 0.62 → 0.42 | - | -30.91% | - | - |
| TQQQ50/BTAL25/KMLM25 | 0.42 | - | 0.61 [0.30–1.16] | 0.40 → 0.72 | - | -44.13% | - | - |
| SPY benchmark | 0.63 | - | 0.72 [0.42–1.21] | 0.57 → 0.99 | - | -24.08% | - | - |
