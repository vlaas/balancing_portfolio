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

## Top 5 of 5 feasible grid strategies by robust_score

| weights | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| {"BIL":0.5,"NTSX":0.5} | 0.41 | - | 0.62 [0.19–1.43] | 0.32 → 1.23 | 1/1 | -16.44% | - |  |
| {"BIL":0.25,"NTSX":0.75} | 0.35 | - | 0.52 [0.14–1.26] | 0.27 → 1.09 | 2/2 | -24.18% | - |  |
| {"NTSX":1.0} | 0.33 | - | 0.46 [0.12–1.18] | 0.24 → 1.03 | 3/3 | -31.42% | - |  |
| {"NTSX":0.5,"RPAR":0.5} | 0.20 | - | 0.25 [-0.03–1.03] | 0.07 → 1.36 | 4/4 | -30.34% | - |  |
| {"RPAR":1.0} | 0.05 | - | 0.00 [-0.20–0.58] | -0.11 → 1.78 | 5/5 | -30.66% | - |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| VT TQQQ/BTAL75+KMLM25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.85 | - | 0.98 [0.77–1.77] | 0.91 → 0.85 | - | -19.06% | 0.38 | - |
| VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.88 | - | -19.07% | 0.38 | - |
| VT TQQQ/BTAL50+KMLM50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200 | 0.88 | - | 1.05 [0.59–1.67] | 1.15 → 1.17 | - | -20.90% | 0.38 | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
