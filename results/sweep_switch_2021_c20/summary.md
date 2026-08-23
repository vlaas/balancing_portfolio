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

## Top 15 of 1596 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 0.89 | 0.91 | 1.02 [0.63–1.73] | 1.04 → 1.00 | 339.5/1136 | -19.20% | 0.36 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.5 | QQQ<SMA200 | 0.95 | 0.89 | 1.07 [0.70–1.63] | 1.10 → 0.89 | 223/909 | -17.13% | 0.34 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 0.92 | 0.88 | 1.07 [0.90–1.44] | 1.12 → 0.91 | 134.5/286 | -20.58% | 0.38 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.7 | QQQ<SMA200 | 0.91 | 0.87 | 1.02 [0.63–1.76] | 0.99 → 1.05 | 227.5/1126 | -19.29% | 0.37 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.6 | QQQ<SMA200 | 0.92 | 0.87 | 1.04 [0.73–1.44] | 1.10 → 0.98 | 110/776 | -21.58% | 0.42 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 0.94 | 0.87 | 1.03 [0.65–1.79] | 0.94 → 1.11 | 139/1081 | -19.29% | 0.38 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.7 | QQQ<SMA200 | 0.87 | 0.87 | 1.01 [0.67–1.46] | 1.06 → 1.10 | 145/1015 | -23.66% | 0.44 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.3 | 0.6 | QQQ<SMA200 | 0.88 | 0.86 | 1.01 [0.80–1.26] | 1.00 → 0.93 | 259/519 | -25.30% | 0.46 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 0.94 | 0.90 | 1.08 [0.81–1.49] | 1.17 → 0.86 | 84/486 | -20.09% | 0.38 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.8 | QQQ<SMA200 | 0.87 | 0.86 | 1.03 [0.65–1.52] | 1.03 → 1.16 | 166.5/1061 | -24.61% | 0.46 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.5 | QQQ<SMA200 | 0.89 | 0.85 | 1.03 [0.77–1.73] | 1.06 → 0.94 | 212.5/613 | -18.11% | 0.34 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 0.85 | 0.87 | 0.96 [0.71–1.76] | 1.01 → 1.03 | 297/851 | -19.99% | 0.36 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.3 | 0.7 | QQQ<SMA200 | 0.87 | 0.85 | 0.98 [0.73–1.23] | 0.95 → 1.04 | 288.5/763 | -26.67% | 0.50 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.3 | 0.6 | QQQ<SMA200 | 0.86 | 0.84 | 0.97 [0.78–1.24] | 0.91 → 0.93 | 323.5/499 | -25.74% | 0.46 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 0.89 | 0.84 | 1.01 [0.72–1.81] | 0.91 → 1.13 | 167.5/803 | -20.09% | 0.38 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.33 | - | 0.64 [0.22–1.26] | 0.34 → 0.52 | - | -44.89% | - | - |
| TQQQ50/DBMF50 | 0.47 | - | 0.54 [0.27–1.12] | 0.38 → 0.95 | - | -47.08% | - | - |
| TQQQ50/KMLM50 | 0.46 | - | 0.50 [0.30–1.04] | 0.40 → 0.85 | - | -45.78% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.52 | - | 0.82 [0.44–1.06] | 0.60 → 0.40 | - | -31.18% | - | - |
| TQQQ50/BTAL25/KMLM25 | 0.40 | - | 0.59 [0.28–1.13] | 0.38 → 0.71 | - | -44.78% | - | - |
| SPY benchmark | 0.60 | - | 0.71 [0.39–1.19] | 0.54 → 0.99 | - | -24.55% | - | - |
