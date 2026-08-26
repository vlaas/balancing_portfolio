# Sweep summary

- Data: 2020-12-18..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2020-12-18..2026-08-24; fit 2020-12-18..2024-12-31; test 2025-01-02..2026-08-24; 6 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2025-01-01 -> 2025-01-02
- Warning: test window 2025-01-02..2026-08-24 is shorter than 2 years; its metrics are noise
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 21 feasible grid strategies by robust_score

| safe | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|
| BTAL50+KMLM50 | QQQ:MOMM1-3-6-12U<=0 off0 | 0.89 | - | 1.02 [0.51–1.31] | 0.96 → 1.22 | 15.5/16 | -18.33% | 0.36 |  |
| BTAL50+KMLM50 | QQQ<SMA200 | 0.88 | - | 1.05 [0.59–1.67] | 1.15 → 1.17 | 9.5/14 | -20.90% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2 | 0.86 | - | 0.99 [0.54–1.60] | 1.11 → 1.17 | 11.5/16 | -20.91% | 0.38 |  |
| BTAL75+DBMF25 | QQQ<SMA200 | 0.86 | - | 0.98 [0.80–1.73] | 0.90 → 0.88 | 4.5/11 | -19.07% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200 | 0.85 | - | 0.98 [0.77–1.77] | 0.91 → 0.85 | 4.5/9 | -19.06% | 0.38 |  |
| BTAL75+KMLM25 | - | 0.83 | - | 0.94 [0.86–1.47] | 0.91 → 0.87 | 7.5/17 | -19.54% | 0.40 |  |
| BTAL75+DBMF25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2 | 0.83 | - | 0.95 [0.75–1.66] | 0.86 → 0.88 | 6.5/15 | -19.07% | 0.38 |  |
| BTAL75+KMLM25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2 | 0.83 | - | 0.96 [0.72–1.70] | 0.88 → 0.85 | 7.5/13 | -19.06% | 0.38 |  |
| BTAL50+KMLM50 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 off0 | 0.82 | - | 0.92 [0.33–1.71] | 1.18 → 0.92 | 12.5/21 | -21.31% | 0.35 |  |
| BTAL50+KMLM50 | - | 0.81 | - | 1.08 [0.68–1.47] | 1.12 → 1.12 | 8.5/18 | -22.59% | 0.40 |  |
| BTAL50+KMLM50 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 | 0.81 | - | 0.93 [0.44–1.47] | 1.02 → 1.17 | 13.5/19 | -20.89% | 0.37 |  |
| BTAL75+DBMF25 | - | 0.81 | - | 0.91 [0.87–1.35] | 0.90 → 0.91 | 12/15 | -20.13% | 0.40 |  |
| BTAL75+KMLM25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 | 0.78 | - | 0.90 [0.61–1.57] | 0.81 → 0.85 | 13.5/16 | -19.06% | 0.37 |  |
| BTAL75+DBMF25 | QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0 | 0.78 | - | 0.90 [0.62–1.52] | 0.79 → 0.88 | 12/17 | -19.07% | 0.37 |  |
| BTAL50+KMLM50 | QQQ:MOMM1-3-6-12U<=0 | 0.76 | - | 0.88 [0.45–1.11] | 0.85 → 1.21 | 17/18 | -20.89% | 0.38 |  |

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.33 | - | 0.65 [0.22–1.27] | 0.35 → 0.52 | - | -44.74% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.52 | - | 0.82 [0.45–1.07] | 0.61 → 0.40 | - | -30.99% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
