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

## Top 9 of 9 feasible grid strategies by robust_score

| safe | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL50+KMLM50 | QQQ<SMA200 | 0.88 | - | 1.05 [0.59–1.67] | 1.15 → 1.17 | 5.5/8 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA10M | 0.88 | - | 1.05 [0.59–1.67] | 1.15 → 1.17 | 5.5/8 | -20.90% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.88 | 3/7 | -19.07% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA10M | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.88 | 3/7 | -19.07% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200 | 0.85 | - | 0.98 [0.77–1.77] | 0.91 → 0.85 | 4/5 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA10M | 0.85 | - | 0.98 [0.77–1.77] | 0.91 → 0.85 | 4/5 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | - | 0.83 | - | 0.94 [0.86–1.47] | 0.91 → 0.87 | 6/8 | -19.54% | 0.40 |  |
| BTAL50+KMLM50 | - | 0.81 | - | 1.08 [0.68–1.47] | 1.12 → 1.12 | 7/9 | -22.59% | 0.40 |  |
| BTAL75+DBMF25 | - | 0.81 | - | 0.91 [0.87–1.35] | 0.90 → 0.91 | 7/9 | -20.13% | 0.40 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
