# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-20; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-20; 6 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-20 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 54 feasible grid strategies by robust_score

| safe | gate | rebalance | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BTAL50+KMLM50 | QQQ<SMA200 | - | 0.89 | - | 1.05 [0.59–1.67] | 1.15 → 1.19 | 25.5/51 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 3m+2 | 0.88 | - | 1.08 [0.74–2.62] | 0.98 → 1.12 | 20.5/41 | -24.97% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | - | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.89 | 25/36 | -19.07% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200 | - | 0.86 | - | 0.98 [0.77–1.77] | 0.91 → 0.86 | 23/31 | -19.06% | 0.38 |  |
| BTAL50+KMLM50 | - | 3m+2 | 0.85 | - | 1.11 [0.73–1.73] | 0.92 → 1.16 | 23.5/43 | -24.97% | 0.40 |  |
| BTAL50+KMLM50 | - | 2m | 0.84 | - | 0.94 [0.63–1.43] | 0.88 → 1.11 | 38/50 | -22.92% | 0.40 |  |
| BTAL75+KMLM25 | - | - | 0.84 | - | 0.94 [0.86–1.47] | 0.91 → 0.88 | 24.5/34 | -19.54% | 0.40 |  |
| BTAL50+KMLM50 | - | - | 0.82 | - | 1.08 [0.68–1.47] | 1.12 → 1.15 | 30/46 | -22.59% | 0.40 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 3m+2 | 0.82 | - | 1.07 [0.83–2.28] | 0.93 → 0.88 | 16/40 | -24.79% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 2m | 0.82 | - | 0.88 [0.57–1.45] | 0.86 → 1.03 | 41.5/54 | -22.92% | 0.38 |  |
| BTAL75+DBMF25 | - | - | 0.81 | - | 0.91 [0.87–1.35] | 0.90 → 0.91 | 26.5/41 | -20.13% | 0.40 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 3m+1 | 0.81 | - | 1.00 [0.48–1.38] | 0.83 → 0.98 | 45/54 | -21.33% | 0.36 |  |
| BTAL75+KMLM25 | - | 2m | 0.80 | - | 0.85 [0.71–1.46] | 0.88 → 0.80 | 39/48 | -22.03% | 0.40 |  |
| BTAL75+KMLM25 | - | 3m+2 | 0.79 | - | 1.04 [0.80–1.74] | 0.91 → 0.81 | 21/44 | -24.09% | 0.40 |  |
| BTAL50+KMLM50 | - | 3m+1 | 0.78 | - | 0.99 [0.53–1.14] | 0.79 → 0.97 | 39.5/54 | -21.33% | 0.38 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 rb 1w | 0.35 | - | 0.66 [0.21–1.32] | 0.36 → 0.52 | - | -45.26% | - | - |
| 50/50 | 0.34 | - | 0.65 [0.22–1.27] | 0.35 → 0.54 | - | -44.74% | - | - |
| TQQQ50/BTAL50 rb 3m | 0.39 | - | 0.62 [0.26–1.31] | 0.37 → 0.71 | - | -43.68% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 1w | 0.46 | - | 0.78 [0.35–1.12] | 0.53 → 0.43 | - | -34.26% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.82 [0.45–1.07] | 0.61 → 0.42 | - | -30.99% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 3m | 0.48 | - | 0.71 [0.37–0.91] | 0.54 → 0.41 | - | -30.56% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
