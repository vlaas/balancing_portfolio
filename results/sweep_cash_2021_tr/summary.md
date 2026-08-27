# Sweep summary

- Data: 2020-12-18..2026-08-24
- Data dir: tests/data/2026-08-24
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
| BTAL75+KMLM25 | 0.2 | 0.87 | 0.87 | 1.01 [0.81–1.81] | 0.93 → 0.87 | 10.5/18 | -19.06% | 0.38 | yes* |
| BTAL75+KMLM25 | 0.25 | 0.87 | 0.87 | 1.01 [0.77–1.43] | 1.01 → 0.97 | 13.5/20 | -22.97% | 0.46 | yes* |
| BIL37.5+BTAL37.5+KMLM25 | 0.2 | 0.93 | 0.86 | 1.12 [0.82–1.45] | 1.08 → 1.22 | 8.5/12 | -19.70% | 0.38 | yes* |
| BIL37.5+BTAL37.5+KMLM25 | 0.25 | 0.86 | 0.93 | 0.98 [0.80–1.25] | 0.90 → 1.18 | 15.5/17 | -24.91% | 0.46 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.91 | 0.86 | 1.09 [0.62–1.74] | 1.18 → 1.23 | 13/24 | -20.79% | 0.38 | yes* |
| BTAL50+KMLM50 | 0.25 | 0.86 | 0.91 | 1.04 [0.65–1.46] | 1.07 → 1.17 | 14.5/23 | -25.76% | 0.46 | yes* |
| BTAL75+DBMF25 | 0.2 | 0.88 | 0.86 | 1.01 [0.83–1.79] | 0.92 → 0.92 | 9.5/14 | -19.04% | 0.38 | yes* |
| BTAL75+DBMF25 | 0.25 | 0.86 | 0.88 | 0.97 [0.80–1.33] | 0.96 → 0.97 | 14.5/17 | -23.32% | 0.46 | yes* |
| BIL25+BTAL25+KMLM50 | 0.2 | 0.90 | 0.86 | 1.07 [0.64–1.51] | 1.13 → 1.29 | 11.5/23 | -22.21% | 0.38 | yes* |
| BIL25+BTAL25+KMLM50 | 0.25 | 0.86 | 0.90 | 1.04 [0.67–1.34] | 1.04 → 1.19 | 15.5/21 | -27.01% | 0.46 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.2 | 0.91 | 0.85 | 1.06 [0.84–1.33] | 1.00 → 1.26 | 8.5/10 | -20.28% | 0.38 | yes* |
| BIL37.5+BTAL37.5+DBMF25 | 0.25 | 0.85 | 0.91 | 0.96 [0.80–1.26] | 0.85 → 1.17 | 15/18 | -25.24% | 0.46 | yes* |
| BIL75+KMLM25 | 0.2 | 0.91 | 0.85 | 0.99 [0.82–1.29] | 0.88 → 1.31 | 12.5/18 | -21.96% | 0.38 | yes* |
| BIL75+KMLM25 | 0.25 | 0.85 | 0.91 | 0.89 [0.74–1.26] | 0.79 → 1.20 | 16.5/21 | -26.83% | 0.46 | yes* |
| BIL50+KMLM50 | 0.2 | 0.89 | 0.85 | 1.10 [0.65–1.31] | 1.08 → 1.30 | 12.5/21 | -23.65% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.84 [0.45–1.10] | 0.62 → 0.40 | - | -30.91% | - | - |
| SPY benchmark | 0.63 | - | 0.72 [0.42–1.21] | 0.57 → 0.98 | - | -24.08% | - | - |
