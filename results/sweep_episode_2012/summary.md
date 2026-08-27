# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 24 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 5 of 5 feasible grid strategies by robust_score

| safe | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| BIL75+BTAL25 | 0.82 | - | 0.85 [0.16–2.08] | 0.76 → 1.30 | 2.5/4 | -25.43% | 0.46 |  |
| BIL50+BTAL50 | 0.82 | - | 0.93 [0.17–2.04] | 0.78 → 1.29 | 3/3 | -24.44% | 0.46 |  |
| BIL25+BTAL75 | 0.80 | - | 0.95 [0.18–1.99] | 0.78 → 1.15 | 2.5/4 | -23.95% | 0.46 |  |
| BIL | 0.80 | - | 0.80 [0.15–2.12] | 0.72 → 1.28 | 4/5 | -27.10% | 0.46 |  |
| BTAL | 0.70 | - | 0.88 [0.19–1.91] | 0.70 → 0.97 | 5/5 | -26.02% | 0.46 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY benchmark | 0.43 | - | 0.72 [0.21–2.26] | 0.36 → 1.19 | - | -33.74% | - | - |
