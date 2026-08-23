# Sweep summary

- Data: 2020-12-18..2026-08-20
- Data dir: tests/data/2026-08-20
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
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 0.98 | 0.98 | 1.10 [0.72–1.96] | 1.12 → 1.08 | 221/1005 | -18.54% | 0.36 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.5 | QQQ<SMA200 | 1.05 | 0.98 | 1.17 [0.80–1.88] | 1.17 → 0.96 | 140/720 | -16.50% | 0.34 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.7 | QQQ<SMA200 | 1.01 | 0.95 | 1.09 [0.73–2.00] | 1.07 → 1.15 | 154.5/996 | -18.67% | 0.37 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 1.01 | 0.95 | 1.12 [0.74–1.97] | 1.01 → 1.22 | 132.5/941 | -19.06% | 0.38 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.5 | QQQ<SMA200 | 0.98 | 0.93 | 1.12 [0.88–1.85] | 1.13 → 1.01 | 163/456 | -17.42% | 0.34 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 0.93 | 0.95 | 1.04 [0.80–1.89] | 1.08 → 1.13 | 205/708 | -19.28% | 0.36 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.6 | QQQ<SMA200 | 0.98 | 0.93 | 1.11 [0.80–1.52] | 1.17 → 1.04 | 149/702 | -21.25% | 0.42 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 1.01 | 0.95 | 1.14 [0.89–1.57] | 1.25 → 0.93 | 119/397 | -19.76% | 0.38 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 0.98 | 0.92 | 1.13 [0.97–1.52] | 1.18 → 0.97 | 153.5/249 | -20.17% | 0.38 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.7 | QQQ<SMA200 | 0.95 | 0.92 | 1.09 [0.75–1.54] | 1.14 → 1.18 | 132/919 | -23.02% | 0.44 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.7 | QQQ<SMA200 | 0.96 | 0.91 | 1.06 [0.80–1.93] | 1.03 → 1.19 | 209/725 | -19.39% | 0.37 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 0.98 | 0.91 | 1.09 [0.82–1.93] | 0.98 → 1.25 | 204.5/661 | -19.41% | 0.38 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.6 | QQQ<SMA200 | 0.95 | 0.91 | 1.09 [0.88–1.47] | 1.12 → 1.07 | 214/447 | -21.65% | 0.42 |  |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.25 | 0.8 | QQQ<SMA200 | 0.95 | 0.91 | 1.11 [0.73–1.61] | 1.09 → 1.25 | 156.5/998 | -23.98% | 0.46 | yes* |
| BTAL75+KMLM25~BTAL25+KMLM75@QQQ<SMA200 | 0.3 | 0.6 | QQQ<SMA200 | 0.93 | 0.90 | 1.07 [0.86–1.34] | 1.08 → 0.98 | 314.5/490 | -25.01% | 0.46 |  |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.34 | - | 0.66 [0.22–1.29] | 0.36 → 0.55 | - | -44.77% | - | - |
| TQQQ50/DBMF50 | 0.50 | - | 0.57 [0.30–1.16] | 0.40 → 0.98 | - | -46.13% | - | - |
| TQQQ50/KMLM50 | 0.49 | - | 0.53 [0.33–1.06] | 0.42 → 0.87 | - | -44.75% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.54 | - | 0.84 [0.45–1.10] | 0.62 → 0.42 | - | -30.91% | - | - |
| TQQQ50/BTAL25/KMLM25 | 0.42 | - | 0.61 [0.30–1.16] | 0.40 → 0.72 | - | -44.13% | - | - |
| SPY benchmark | 0.63 | - | 0.72 [0.42–1.21] | 0.57 → 0.99 | - | -24.08% | - | - |
