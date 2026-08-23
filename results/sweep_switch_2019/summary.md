# Sweep summary

- Data: 2019-05-08..2026-08-20
- Data dir: tests/data/2026-08-20-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2019-05-08..2026-08-20; fit 2019-05-08..2023-12-29; test 2024-01-02..2026-08-20; 9 sensitivity
- Costs: per-asset (TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2024-01-01 -> 2024-01-02
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 848 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.8 | QQQ<SMA200 | 1.05 | 1.01 | 1.01 [0.69–1.54] | 1.10 → 1.03 | 49/415 | -20.10% | 0.38 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.7 | QQQ<SMA200 | 1.03 | 0.99 | 0.99 [0.70–1.52] | 1.08 → 1.01 | 99/490 | -19.97% | 0.37 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.6 | QQQ<SMA200 | 1.00 | 0.94 | 0.98 [0.69–1.50] | 1.03 → 1.01 | 68/566 | -19.84% | 0.36 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.8 | - | 0.98 | 0.93 | 0.97 [0.68–1.31] | 1.09 → 0.95 | 170/339 | -21.32% | 0.40 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@VIX/VIX3M@10>=0.95<0.90 | 0.2 | 0.8 | QQQ<SMA200 | 0.95 | 0.93 | 0.93 [0.68–1.49] | 1.03 → 0.96 | 122/535 | -22.15% | 0.38 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.8 | QQQ<SMA200 | 1.01 | 0.96 | 0.93 [0.72–1.26] | 1.07 → 1.02 | 74/443 | -24.64% | 0.46 | yes* |
| BTAL75+DBMF25 | 0.2 | 0.8 | QQQ<SMA200 | 0.94 | 0.92 | 0.92 [0.62–1.39] | 1.02 → 0.92 | 141/463 | -20.11% | 0.38 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.7 | - | 0.96 | 0.92 | 0.95 [0.68–1.26] | 1.07 → 0.93 | 124/459 | -21.31% | 0.39 | yes* |
| BTAL25+DBMF75 | 0.25 | 0.8 | QQQ<SMA200 | 0.91 | 0.90 | 0.93 [0.54–1.16] | 0.99 → 0.90 | 131/711 | -29.69% | 0.46 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.5 | QQQ<SMA200 | 0.90 | 0.90 | 1.01 [0.77–1.34] | 0.89 → 1.12 | 72/384 | -24.02% | 0.39 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.2 | 0.6 | - | 0.93 | 0.89 | 0.95 [0.68–1.23] | 1.02 → 0.94 | 150/579 | -21.24% | 0.38 | yes* |
| BTAL75+DBMF25 | 0.2 | 0.7 | QQQ<SMA200 | 0.92 | 0.89 | 0.90 [0.63–1.37] | 1.00 → 0.90 | 173/444 | -19.98% | 0.37 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@VIX/VIX3M@10>=0.95<0.90 | 0.2 | 0.7 | QQQ<SMA200 | 0.93 | 0.89 | 0.91 [0.67–1.47] | 1.00 → 0.94 | 97/616 | -22.14% | 0.37 | yes* |
| BTAL75+DBMF25~BTAL25+DBMF75@QQQ<SMA200 | 0.25 | 0.7 | QQQ<SMA200 | 0.99 | 0.92 | 0.89 [0.74–1.27] | 1.00 → 1.05 | 82/444 | -24.02% | 0.45 |  |
| BTAL75+DBMF25~BTAL25+DBMF75@VIX/VIX3M@10>=0.95<0.90 | 0.25 | 0.8 | QQQ<SMA200 | 0.93 | 0.89 | 0.96 [0.66–1.20] | 0.97 → 0.96 | 73/539 | -26.78% | 0.46 | yes* |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| 50/50 | 0.48 | - | 0.35 [0.20–1.31] | 0.48 → 0.82 | - | -44.78% | - | - |
| TQQQ50/DBMF50 | 0.60 | - | 0.41 [0.21–1.21] | 0.55 → 0.95 | - | -46.94% | - | - |
| TQQQ50/BTAL50 gate QQQ<SMA200 | 0.56 | - | 0.60 [0.38–1.13] | 0.59 → 0.80 | - | -37.72% | - | - |
| TQQQ50/BTAL25/DBMF25 | 0.55 | - | 0.36 [0.24–1.18] | 0.52 → 0.89 | - | -45.33% | - | - |
| SPY benchmark | 0.47 | - | 0.42 [0.26–1.20] | 0.38 → 1.12 | - | -33.67% | - | - |
