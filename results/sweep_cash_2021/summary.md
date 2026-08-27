# Sweep summary

- Data: 2020-12-18..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-24; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-24; 6 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-24 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 24 feasible grid strategies by robust_score

| safe | sigma_target | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL75+KMLM25 | 0.25 | 0.85 | 0.85 | 0.97 [0.75–1.37] | 0.99 → 0.94 | 13.5/21 | -23.09% | 0.46 | yes* |
| BTAL75+KMLM25 | 0.2 | 0.85 | 0.85 | 0.98 [0.77–1.77] | 0.91 → 0.85 | 11/18 | -19.06% | 0.38 | yes* |
| BIL37.5+BTAL37.5+KMLM25 | 0.2 | 0.90 | 0.84 | 1.07 [0.78–1.37] | 1.04 → 1.19 | 9/12 | -19.89% | 0.38 | yes* |
| BIL37.5+BTAL37.5+KMLM25 | 0.25 | 0.84 | 0.90 | 0.95 [0.77–1.22] | 0.87 → 1.15 | 14.5/17 | -25.03% | 0.46 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.88 | 0.84 | 1.05 [0.59–1.67] | 1.15 → 1.17 | 13/24 | -20.90% | 0.38 | yes* |
| BTAL50+KMLM50 | 0.25 | 0.84 | 0.88 | 1.02 [0.62–1.42] | 1.05 → 1.15 | 14/23 | -25.81% | 0.46 | yes* |
| BTAL75+DBMF25 | 0.2 | 0.86 | 0.84 | 0.98 [0.80–1.73] | 0.90 → 0.88 | 9/15 | -19.07% | 0.38 | yes* |
| BTAL75+DBMF25 | 0.25 | 0.84 | 0.86 | 0.95 [0.78–1.28] | 0.92 → 0.95 | 13.5/16 | -23.47% | 0.46 | yes* |
| BIL25+BTAL25+KMLM50 | 0.2 | 0.88 | 0.84 | 1.04 [0.61–1.44] | 1.10 → 1.26 | 12/23 | -22.35% | 0.38 | yes* |
| BIL25+BTAL25+KMLM50 | 0.25 | 0.84 | 0.88 | 1.00 [0.64–1.27] | 1.00 → 1.16 | 15.5/20 | -27.10% | 0.46 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.2 | 0.88 | 0.83 | 1.02 [0.81–1.27] | 0.95 → 1.21 | 8/11 | -20.53% | 0.38 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.25 | 0.83 | 0.88 | 0.93 [0.77–1.23] | 0.82 → 1.15 | 15/18 | -25.43% | 0.46 | yes* |
| BIL50+KMLM50 | 0.2 | 0.86 | 0.83 | 1.07 [0.62–1.25] | 1.03 → 1.27 | 12.5/22 | -23.79% | 0.38 | yes* |
| BIL50+KMLM50 | 0.25 | 0.83 | 0.86 | 0.97 [0.65–1.12] | 0.90 → 1.18 | 16.5/19 | -28.39% | 0.46 | yes* |
| BIL75+KMLM25 | 0.2 | 0.88 | 0.82 | 0.93 [0.78–1.26] | 0.83 → 1.29 | 13.5/18 | -22.11% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.52 | - | 0.82 [0.45–1.07] | 0.61 → 0.40 | - | -30.99% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
