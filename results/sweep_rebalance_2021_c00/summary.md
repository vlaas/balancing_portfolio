# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-20; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-20; 6 sensitivity
- Costs: flat 0 bps (CLI override), cash yield 3% (CLI override)
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-20 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 54 feasible grid strategies by robust_score

| safe | gate | rebalance | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BTAL50+KMLM50 | QQQ<SMA200 | - | 0.90 | - | 1.06 [0.60–1.68] | 1.16 → 1.21 | 25.5/51 | -20.83% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 3m+2 | 0.89 | - | 1.08 [0.74–2.63] | 0.98 → 1.12 | 20.5/42 | -24.95% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | - | 0.87 | - | 0.99 [0.81–1.73] | 0.91 → 0.90 | 25.5/37 | -19.02% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200 | - | 0.87 | - | 1.00 [0.78–1.79] | 0.92 → 0.86 | 23.5/31 | -19.01% | 0.38 |  |
| BTAL50+KMLM50 | - | 3m+2 | 0.85 | - | 1.12 [0.73–1.73] | 0.93 → 1.17 | 24.5/43 | -24.96% | 0.40 |  |
| BTAL75+KMLM25 | - | - | 0.85 | - | 0.94 [0.87–1.48] | 0.92 → 0.90 | 25/33 | -19.45% | 0.40 |  |
| BTAL50+KMLM50 | - | 2m | 0.84 | - | 0.94 [0.63–1.43] | 0.89 → 1.12 | 39/50 | -22.93% | 0.40 |  |
| BTAL50+KMLM50 | - | - | 0.83 | - | 1.09 [0.69–1.50] | 1.13 → 1.16 | 29.5/46 | -22.49% | 0.40 |  |
| BTAL75+DBMF25 | - | - | 0.82 | - | 0.92 [0.88–1.36] | 0.91 → 0.92 | 27.5/41 | -20.04% | 0.40 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 3m+2 | 0.82 | - | 1.08 [0.84–2.29] | 0.93 → 0.88 | 17/40 | -24.78% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 2m | 0.82 | - | 0.88 [0.57–1.45] | 0.86 → 1.04 | 42/53 | -22.93% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 3m+1 | 0.81 | - | 1.00 [0.49–1.39] | 0.83 → 0.99 | 45/54 | -21.32% | 0.36 |  |
| BTAL75+KMLM25 | - | 2m | 0.80 | - | 0.86 [0.72–1.45] | 0.89 → 0.80 | 39/48 | -22.01% | 0.40 |  |
| BTAL75+KMLM25 | - | 3m+2 | 0.79 | - | 1.05 [0.81–1.75] | 0.91 → 0.81 | 21.5/44 | -24.08% | 0.40 |  |
| BTAL50+KMLM50 | - | 3m+1 | 0.79 | - | 0.99 [0.53–1.14] | 0.79 → 0.98 | 39.5/54 | -21.32% | 0.38 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 rb 1w | 0.35 | - | 0.66 [0.22–1.33] | 0.37 → 0.53 | - | -45.20% | - | - |
| 50/50 | 0.34 | - | 0.65 [0.22–1.27] | 0.35 → 0.54 | - | -44.72% | - | - |
| TQQQ50/BTAL50 rb 3m | 0.39 | - | 0.62 [0.26–1.31] | 0.38 → 0.71 | - | -43.63% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 1w | 0.47 | - | 0.79 [0.35–1.13] | 0.54 → 0.43 | - | -34.18% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.83 [0.45–1.07] | 0.61 → 0.42 | - | -30.95% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 3m | 0.48 | - | 0.71 [0.38–0.91] | 0.54 → 0.41 | - | -30.51% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
