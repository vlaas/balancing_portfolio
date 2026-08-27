# Sweep summary

- Data: 2019-05-08..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-24; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-24; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 12 of 12 feasible grid strategies by robust_score

| safe | sigma_target | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL75+DBMF25 | 0.2 | 0.94 | 0.95 | 0.92 [0.62–1.39] | 1.02 → 0.92 | 3/9 | -20.11% | 0.38 | yes* |
| BIL50+BTAL50 | 0.2 | 0.98 | 0.87 | 0.94 [0.63–1.51] | 1.03 → 1.03 | 6/6 | -19.40% | 0.38 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.2 | 0.99 | 0.94 | 0.83 [0.76–1.29] | 1.04 → 0.97 | 3/8 | -21.02% | 0.38 | yes* |
| BTAL75+DBMF25 | 0.25 | 0.95 | 0.94 | 0.78 [0.72–1.20] | 1.00 → 0.93 | 4/12 | -24.03% | 0.46 | yes* |
| BIL50+BTAL50 | 0.25 | 0.87 | 0.98 | 0.78 [0.55–1.38] | 0.90 → 0.99 | 8/9 | -26.05% | 0.46 | yes* |
| BIL75+DBMF25 | 0.2 | 0.96 | 0.89 | 0.76 [0.55–1.35] | 0.97 → 1.00 | 6/11 | -23.30% | 0.38 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.25 | 0.94 | 0.99 | 0.74 [0.62–1.26] | 0.97 → 0.95 | 7/11 | -25.90% | 0.46 | yes* |
| BIL75+DBMF25 | 0.25 | 0.89 | 0.96 | 0.70 [0.49–1.31] | 0.90 → 0.97 | 8/12 | -28.85% | 0.46 | yes* |
| BIL | 0.2 | 0.85 | 0.81 | 0.64 [0.47–1.41] | 0.86 → 1.02 | 9/11 | -24.82% | 0.38 | yes* |
| BTAL | 0.2 | 0.63 | 0.80 | 0.96 [0.36–1.37] | 0.70 → 0.79 | 10/12 | -26.02% | 0.38 | yes* |
| BTAL | 0.25 | 0.80 | 0.63 | 0.83 [0.51–1.38] | 0.85 → 0.94 | 7/11 | -25.75% | 0.46 | yes* |
| BIL | 0.25 | 0.81 | 0.85 | 0.61 [0.43–1.35] | 0.80 → 0.99 | 10/12 | -30.64% | 0.46 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.79 | - | -37.72% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
