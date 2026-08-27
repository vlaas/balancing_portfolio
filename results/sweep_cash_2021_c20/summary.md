# Sweep summary

- Data: 2020-12-18..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-24; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-24; 6 sensitivity
- Costs: per-asset (* 20) bps, cash yield 3%
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-24 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 24 feasible grid strategies by robust_score

| safe | sigma_target | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL75+KMLM25 | 0.25 | 0.81 | 0.82 | 0.93 [0.71–1.32] | 0.94 → 0.90 | 13/20 | -23.52% | 0.46 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.84 | 0.80 | 1.00 [0.56–1.61] | 1.11 → 1.11 | 13/24 | -21.25% | 0.38 | yes* |
| BTAL50+KMLM50 | 0.25 | 0.80 | 0.84 | 0.97 [0.59–1.39] | 1.01 → 1.11 | 14/22 | -26.24% | 0.46 | yes* |
| BIL37.5+BTAL37.5+KMLM25 | 0.2 | 0.85 | 0.80 | 1.02 [0.74–1.32] | 0.99 → 1.12 | 9/14 | -20.25% | 0.38 | yes* |
| BIL37.5+BTAL37.5+KMLM25 | 0.25 | 0.80 | 0.85 | 0.91 [0.73–1.16] | 0.83 → 1.10 | 14.5/17 | -25.49% | 0.46 | yes* |
| BIL25+BTAL25+KMLM50 | 0.2 | 0.83 | 0.80 | 0.99 [0.57–1.40] | 1.06 → 1.21 | 12/23 | -22.70% | 0.38 | yes* |
| BIL25+BTAL25+KMLM50 | 0.25 | 0.80 | 0.83 | 0.96 [0.61–1.23] | 0.95 → 1.13 | 14/20 | -27.54% | 0.46 | yes* |
| BTAL75+DBMF25 | 0.2 | 0.82 | 0.80 | 0.93 [0.76–1.64] | 0.86 → 0.83 | 10/15 | -19.20% | 0.38 | yes* |
| BTAL75+DBMF25 | 0.25 | 0.80 | 0.82 | 0.90 [0.74–1.24] | 0.88 → 0.91 | 13.5/17 | -23.91% | 0.46 | yes* |
| BTAL75+KMLM25 | 0.2 | 0.82 | 0.81 | 0.94 [0.73–1.73] | 0.88 → 0.79 | 11/21 | -19.20% | 0.38 | yes* |
| BIL50+KMLM50 | 0.2 | 0.82 | 0.79 | 1.02 [0.58–1.21] | 0.99 → 1.23 | 13/22 | -24.14% | 0.38 | yes* |
| BIL50+KMLM50 | 0.25 | 0.79 | 0.82 | 0.93 [0.62–1.07] | 0.86 → 1.14 | 16.5/19 | -28.82% | 0.46 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.2 | 0.83 | 0.79 | 0.97 [0.76–1.21] | 0.90 → 1.15 | 9/12 | -20.90% | 0.38 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.25 | 0.79 | 0.83 | 0.89 [0.73–1.18] | 0.77 → 1.11 | 15/18 | -25.89% | 0.46 | yes* |
| BIL75+KMLM25 | 0.2 | 0.83 | 0.78 | 0.90 [0.74–1.20] | 0.79 → 1.24 | 13/18 | -22.48% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.51 | - | 0.82 [0.44–1.06] | 0.60 → 0.38 | - | -31.18% | - | - |
| SPY benchmark | 0.60 | - | 0.71 [0.39–1.19] | 0.54 → 0.99 | - | -24.55% | - | - |
