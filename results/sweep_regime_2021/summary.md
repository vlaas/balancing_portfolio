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

## Top 15 of 21 feasible grid strategies by robust_score

| safe | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL50+KMLM50 | QQQ<SMA200 | 0.89 | - | 1.05 [0.59–1.67] | 1.15 → 1.19 | 12.5/15 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200|VIX/VIX3M@1>=1.00 | 0.89 | - | 1.05 [0.59–1.67] | 1.15 → 1.19 | 12.5/15 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 | 0.89 | - | 1.05 [0.59–1.67] | 1.15 → 1.19 | 12.5/15 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200|VIX/VIX3M@10>=0.95<0.90 | 0.89 | - | 1.05 [0.59–1.67] | 1.15 → 1.19 | 15/18 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | VIX/VIX3M@1>=1.00 | 0.88 | - | 1.07 [0.74–1.45] | 1.10 → 1.24 | 10/18 | -20.91% | 0.40 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.89 | 7.5/16 | -19.07% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.89 | 7.5/16 | -19.07% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@10>=0.95<0.90 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.89 | 6.5/18 | -19.07% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@1>=1.00 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.89 | 7.5/19 | -19.07% | 0.38 |  |
| BTAL75+DBMF25 | VIX/VIX3M@1>=1.00 | 0.86 | - | 1.00 [0.85–1.48] | 0.89 → 0.92 | 11/21 | -19.07% | 0.40 |  |
| BTAL75+KMLM25 | QQQ<SMA200|VIX/VIX3M@10>=0.95<0.90 | 0.86 | - | 0.98 [0.77–1.77] | 0.91 → 0.86 | 11/13 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200 | 0.86 | - | 0.98 [0.77–1.77] | 0.91 → 0.86 | 9.5/10 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200|VIX/VIX3M@1>=1.00 | 0.86 | - | 0.98 [0.77–1.77] | 0.91 → 0.86 | 10.5/13 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 | 0.86 | - | 0.98 [0.77–1.77] | 0.91 → 0.86 | 9.5/10 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | VIX/VIX3M@1>=1.00 | 0.85 | - | 0.98 [0.91–1.48] | 0.91 → 0.89 | 10.5/19 | -19.06% | 0.40 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.34 | - | 0.65 [0.22–1.27] | 0.35 → 0.54 | - | -44.74% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.82 [0.45–1.07] | 0.61 → 0.42 | - | -30.99% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
