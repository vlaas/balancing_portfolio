# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-20; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-20; 6 sensitivity
- Costs: flat 20 bps (CLI override), cash yield 3% (CLI override)
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-20 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 54 feasible grid strategies by robust_score

| safe | gate | rebalance | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| BTAL50+KMLM50 | QQQ<SMA200 | 3m+2 | 0.87 | - | 1.06 [0.73–2.57] | 0.97 → 1.10 | 17.5/39 | -24.96% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | - | 0.85 | - | 1.00 [0.56–1.61] | 1.11 → 1.14 | 24.5/52 | -21.25% | 0.38 |  |
| BTAL50+KMLM50 | - | 3m+2 | 0.84 | - | 1.09 [0.72–1.69] | 0.91 → 1.14 | 20.5/42 | -24.97% | 0.40 |  |
| BTAL50+KMLM50 | - | 2m | 0.83 | - | 0.92 [0.62–1.41] | 0.87 → 1.07 | 35/50 | -22.93% | 0.40 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | - | 0.82 | - | 0.93 [0.76–1.64] | 0.86 → 0.83 | 23.5/38 | -19.20% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 3m+2 | 0.81 | - | 1.06 [0.82–2.23] | 0.92 → 0.85 | 13.5/39 | -24.80% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 2m | 0.80 | - | 0.86 [0.56–1.44] | 0.84 → 1.00 | 40/53 | -22.93% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200 | - | 0.82 | - | 0.94 [0.73–1.73] | 0.88 → 0.80 | 21.5/33 | -19.20% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 3m+1 | 0.80 | - | 0.98 [0.48–1.36] | 0.81 → 0.98 | 42/54 | -21.34% | 0.36 |  |
| BTAL75+KMLM25 | - | - | 0.79 | - | 0.90 [0.81–1.41] | 0.87 → 0.84 | 24/37 | -19.90% | 0.40 |  |
| BTAL50+KMLM50 | - | - | 0.78 | - | 1.03 [0.65–1.41] | 1.06 → 1.10 | 29.5/46 | -22.92% | 0.40 |  |
| BTAL75+KMLM25 | - | 3m+2 | 0.78 | - | 1.02 [0.79–1.71] | 0.90 → 0.79 | 19/43 | -24.10% | 0.40 |  |
| BTAL50+KMLM50 | - | 3m+1 | 0.77 | - | 0.98 [0.52–1.12] | 0.78 → 0.97 | 36.5/53 | -21.34% | 0.38 |  |
| BTAL75+DBMF25 | - | 3m+2 | 0.77 | - | 1.00 [0.81–1.63] | 0.86 → 0.89 | 20/45 | -24.80% | 0.40 |  |
| BTAL75+DBMF25 | - | - | 0.77 | - | 0.86 [0.83–1.29] | 0.86 → 0.86 | 24/44 | -20.51% | 0.40 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| TQQQ50/BTAL50 rb 1w | 0.33 | - | 0.64 [0.20–1.30] | 0.35 → 0.51 | - | -45.56% | - | - |
| 50/50 | 0.33 | - | 0.64 [0.22–1.26] | 0.34 → 0.52 | - | -44.89% | - | - |
| TQQQ50/BTAL50 rb 3m | 0.38 | - | 0.61 [0.25–1.30] | 0.37 → 0.70 | - | -43.77% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 1w | 0.45 | - | 0.77 [0.34–1.11] | 0.52 → 0.42 | - | -34.39% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.52 | - | 0.82 [0.44–1.06] | 0.60 → 0.40 | - | -31.18% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 rb 3m | 0.48 | - | 0.70 [0.37–0.90] | 0.53 → 0.40 | - | -30.65% | - | - |
| SPY benchmark | 0.60 | - | 0.71 [0.39–1.19] | 0.54 → 0.99 | - | -24.55% | - | - |
