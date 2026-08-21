# Sweep summary

- Data: 2019-05-08..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-20; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-20; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 298 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL75+DBMF25 | 0.2 | 0.8 | QQQ<SMA200 | 0.94 | 0.92 | 0.92 [0.62–1.39] | 1.02 → 0.92 | 74/154 | -20.11% | 0.38 | yes* |
| BTAL25+DBMF75 | 0.25 | 0.8 | QQQ<SMA200 | 0.91 | 0.90 | 0.93 [0.54–1.16] | 0.99 → 0.90 | 48/258 | -29.69% | 0.46 | yes* |
| BTAL50+DBMF50 | 0.2 | 0.8 | QQQ<SMA200 | 0.96 | 0.94 | 0.99 [0.63–1.30] | 1.07 → 0.89 | 25/231 | -22.19% | 0.38 | yes* |
| BTAL75+DBMF25 | 0.2 | 0.7 | QQQ<SMA200 | 0.92 | 0.89 | 0.90 [0.63–1.37] | 1.00 → 0.90 | 60/165 | -19.98% | 0.37 | yes* |
| BTAL50+DBMF50 | 0.2 | 0.7 | QQQ<SMA200 | 0.94 | 0.91 | 0.99 [0.62–1.29] | 1.04 → 0.88 | 24/247 | -22.19% | 0.37 | yes* |
| BTAL50+DBMF50 | 0.2 | 0.6 | QQQ<SMA200 | 0.91 | 0.88 | 0.97 [0.62–1.27] | 0.99 → 0.89 | 27/252 | -22.10% | 0.36 | yes* |
| BTAL25+DBMF75 | 0.25 | 0.7 | QQQ<SMA200 | 0.90 | 0.88 | 0.90 [0.55–1.16] | 0.93 → 0.92 | 63/260 | -28.99% | 0.45 |  |
| DBMF | 0.25 | 0.8 | QQQ<SMA200 | 0.89 | 0.88 | 0.92 [0.46–1.15] | 0.95 → 0.88 | 59/282 | -32.67% | 0.46 | yes* |
| BTAL25+DBMF75 | 0.2 | 0.8 | QQQ<SMA200 | 0.91 | 0.89 | 1.03 [0.50–1.23] | 1.03 → 0.87 | 15/276 | -25.90% | 0.38 | yes* |
| BTAL25+DBMF75 | 0.2 | 0.6 | QQQ<SMA200 | 0.87 | 0.88 | 1.01 [0.49–1.17] | 0.95 → 0.88 | 18/286 | -25.83% | 0.36 | yes* |
| BTAL25+DBMF75 | 0.2 | 0.7 | QQQ<SMA200 | 0.89 | 0.87 | 1.03 [0.49–1.21] | 1.00 → 0.87 | 17/278 | -25.91% | 0.37 | yes* |
| DBMF | 0.2 | 0.8 | QQQ<SMA200 | 0.88 | 0.86 | 1.04 [0.40–1.21] | 0.97 → 0.86 | 26/295 | -29.51% | 0.38 | yes* |
| DBMF | 0.25 | 0.7 | QQQ<SMA200 | 0.88 | 0.86 | 0.88 [0.46–1.14] | 0.90 → 0.91 | 72/281 | -32.06% | 0.45 |  |
| DBMF | 0.3 | 0.8 | QQQ<SMA200 | 0.88 | 0.86 | 0.86 [0.52–1.20] | 0.90 → 0.93 | 99/260 | -35.19% | 0.53 | yes* |
| BTAL50+DBMF50 | 0.25 | 0.8 | QQQ<SMA200 | 0.94 | 0.90 | 0.86 [0.64–1.18] | 1.00 → 0.92 | 48/216 | -26.64% | 0.46 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.48 | - | 0.35 [0.20–1.31] | 0.48 → 0.82 | - | -44.78% | - | - |
| TQQQ50/DBMF50 | 0.60 | - | 0.41 [0.21–1.21] | 0.55 → 0.95 | - | -46.94% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.80 | - | -37.72% | - | - |
| TQQQ50/BTAL25/DBMF25 | 0.55 | - | 0.36 [0.24–1.18] | 0.52 → 0.89 | - | -45.33% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
