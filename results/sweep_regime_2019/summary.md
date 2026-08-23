# Sweep summary

- Data: 2019-05-08..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-20; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-20; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 14 of 14 feasible grid strategies by robust_score

| safe | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL75+DBMF25 | QQQ<SMA200 | 0.94 | - | 0.92 [0.62–1.39] | 1.02 → 0.92 | 3/10 | -20.11% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@1>=1.00 | 1.02 | - | 0.92 [0.62–1.39] | 1.15 → 0.92 | 3/12 | -20.11% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 | 0.93 | - | 0.92 [0.62–1.39] | 1.01 → 0.92 | 4/10 | -20.12% | 0.38 |  |
| BTAL75+DBMF25 | VIX/VIX3M@1>=1.00 | 1.02 | - | 0.89 [0.62–1.53] | 1.15 → 0.94 | 5/12 | -20.11% | 0.39 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@10>=0.95<0.90 | 0.86 | - | 0.90 [0.34–1.39] | 0.91 → 0.92 | 8/12 | -20.10% | 0.37 |  |
| BTAL75+DBMF25 | - | 0.94 | - | 0.84 [0.63–1.38] | 1.03 → 0.85 | 6/12 | -20.13% | 0.40 |  |
| BTAL | VIX/VIX3M@1>=1.00 | 0.69 | - | 0.77 [0.37–1.69] | 0.81 → 0.80 | 9/14 | -26.02% | 0.39 |  |
| BTAL | QQQ<SMA200|VIX/VIX3M@1>=1.00 | 0.69 | - | 0.96 [0.36–1.37] | 0.80 → 0.79 | 8/12 | -26.02% | 0.38 |  |
| BTAL | - | 0.64 | - | 0.78 [0.37–1.68] | 0.71 → 0.80 | 9/13 | -26.00% | 0.40 |  |
| BTAL | QQQ<SMA200 | 0.63 | - | 0.96 [0.36–1.37] | 0.70 → 0.79 | 9/11 | -26.02% | 0.38 |  |
| BTAL | QQQ<SMA200|VIX/VIX3M@10>=1.00<0.95 | 0.62 | - | 0.96 [0.36–1.37] | 0.69 → 0.79 | 9/13 | -26.02% | 0.38 |  |
| BTAL | QQQ<SMA200|VIX/VIX3M@10>=0.95<0.90 | 0.57 | - | 0.96 [0.15–1.37] | 0.61 → 0.79 | 9/14 | -26.00% | 0.37 |  |
| BTAL75+DBMF25 | QQQ<SMA200|VIX/VIX3M@1>=1.00 off0 | 0.73 | - | 0.77 [0.46–1.69] | 0.93 → 0.48 | 5/14 | -27.59% | 0.35 |  |
| BTAL | QQQ<SMA200|VIX/VIX3M@1>=1.00 off0 | 0.51 | - | 0.69 [0.27–1.51] | 0.69 → 0.35 | 10/14 | -33.79% | 0.35 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.48 | - | 0.35 [0.20–1.31] | 0.48 → 0.82 | - | -44.78% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.80 | - | -37.72% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
