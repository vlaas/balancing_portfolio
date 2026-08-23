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

## Top 15 of 1598 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 0.94 | 0.95 | 1.06 [0.67–1.77] | 1.08 → 1.05 | 231/1082 | -18.75% | 0.36 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.5 | QQQ<SMA200 | 1.00 | 0.94 | 1.10 [0.74–1.67] | 1.13 → 0.93 | 154/851 | -16.75% | 0.34 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 0.99 | 0.92 | 1.09 [0.69–1.83] | 0.98 → 1.18 | 107.5/1005 | -19.06% | 0.38 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.7 | QQQ<SMA200 | 0.97 | 0.92 | 1.05 [0.68–1.80] | 1.03 → 1.12 | 132.5/1069 | -18.83% | 0.37 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.6 | QQQ<SMA200 | 0.95 | 0.91 | 1.07 [0.76–1.47] | 1.13 → 1.01 | 117/780 | -21.41% | 0.42 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.5 | QQQ<SMA200 | 0.94 | 0.90 | 1.08 [0.82–1.76] | 1.09 → 0.98 | 165.5/551 | -17.70% | 0.34 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 0.90 | 0.92 | 1.01 [0.76–1.82] | 1.05 → 1.09 | 218/784 | -19.54% | 0.36 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 0.97 | 0.91 | 1.11 [0.84–1.51] | 1.20 → 0.90 | 96.5/497 | -19.97% | 0.38 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.7 | QQQ<SMA200 | 0.92 | 0.90 | 1.05 [0.71–1.49] | 1.10 → 1.15 | 111.5/967 | -23.16% | 0.44 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 0.94 | 0.89 | 1.09 [0.92–1.47] | 1.14 → 0.95 | 152.5/290 | -20.42% | 0.39 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 0.95 | 0.89 | 1.06 [0.77–1.88] | 0.95 → 1.21 | 171.5/721 | -19.61% | 0.38 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.8 | QQQ<SMA200 | 0.92 | 0.89 | 1.08 [0.69–1.56] | 1.07 → 1.22 | 122/1027 | -24.10% | 0.46 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.7 | QQQ<SMA200 | 0.92 | 0.89 | 1.03 [0.76–1.86] | 1.00 → 1.15 | 158/775 | -19.62% | 0.37 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.6 | QQQ<SMA200 | 0.92 | 0.88 | 1.05 [0.84–1.42] | 1.08 → 1.03 | 182/490 | -21.88% | 0.42 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@VIX/VIX3M@1>=1.00 | 0.2 | 0.8 | QQQ<SMA200 | 0.90 | 0.88 | 1.05 [0.88–1.75] | 0.94 → 0.93 | 106.5/369 | -19.07% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.34 | - | 0.65 [0.22–1.27] | 0.35 → 0.54 | - | -44.74% | - | - |
| TQQQ50/DBMF50 | 0.47 | - | 0.54 [0.28–1.12] | 0.38 → 0.96 | - | -46.94% | - | - |
| TQQQ50/KMLM50 | 0.47 | - | 0.51 [0.30–1.04] | 0.40 → 0.86 | - | -45.62% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.53 | - | 0.82 [0.45–1.07] | 0.61 → 0.42 | - | -30.99% | - | - |
| TQQQ50/BTAL25/KMLM25 | 0.41 | - | 0.60 [0.29–1.14] | 0.38 → 0.72 | - | -44.63% | - | - |
| SPY benchmark | 0.61 | - | 0.71 [0.40–1.19] | 0.55 → 1.00 | - | -24.45% | - | - |
