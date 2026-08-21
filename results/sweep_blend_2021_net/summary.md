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

## Top 15 of 498 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL25+KMLM75 | 0.2 | 0.4 | QQQ<SMA200 | 0.90 | 0.86 | 1.02 [0.51–1.36] | 1.18 → 0.93 | 228/467 | -19.99% | 0.31 | yes* |
| BTAL75+KMLM25 | 0.2 | 0.8 | QQQ<SMA200 | 0.86 | 0.86 | 0.98 [0.77–1.77] | 0.91 → 0.86 | 116.5/268 | -19.06% | 0.38 | yes* |
| BTAL25+KMLM75 | 0.25 | 0.5 | QQQ<SMA200 | 0.88 | 0.86 | 1.03 [0.60–1.24] | 1.08 → 0.94 | 187.5/417 | -24.21% | 0.39 |  |
| BTAL50+KMLM50 | 0.2 | 0.8 | QQQ<SMA200 | 0.89 | 0.85 | 1.05 [0.59–1.67] | 1.15 → 1.19 | 151/422 | -20.90% | 0.38 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.5 | QQQ<SMA200 | 0.88 | 0.84 | 1.07 [0.61–1.54] | 1.21 → 0.97 | 207/402 | -18.89% | 0.34 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.6 | QQQ<SMA200 | 0.84 | 0.87 | 1.00 [0.57–1.61] | 1.13 → 1.09 | 223/430 | -20.82% | 0.36 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.7 | QQQ<SMA200 | 0.87 | 0.84 | 1.02 [0.58–1.65] | 1.14 → 1.14 | 195.5/429 | -20.90% | 0.37 | yes* |
| BTAL50+KMLM50 | 0.25 | 0.6 | QQQ<SMA200 | 0.88 | 0.84 | 1.00 [0.68–1.31] | 1.05 → 0.99 | 149/350 | -22.96% | 0.42 |  |
| BTAL50+KMLM50 | 0.25 | 0.7 | QQQ<SMA200 | 0.84 | 0.84 | 0.99 [0.63–1.35] | 1.05 → 1.11 | 168/384 | -24.91% | 0.44 |  |
| BTAL75+DBMF25 | 0.2 | 0.8 | QQQ<SMA200 | 0.86 | 0.84 | 0.98 [0.80–1.73] | 0.90 → 0.89 | 104.5/241 | -19.07% | 0.38 | yes* |
| KMLM | 0.3 | 0.6 | QQQ<SMA200 | 0.85 | 0.84 | 0.97 [0.55–1.09] | 0.99 → 1.00 | 186.5/434 | -30.77% | 0.46 |  |
| BTAL50+KMLM50 | 0.25 | 0.5 | QQQ<SMA200 | 0.89 | 0.86 | 1.03 [0.74–1.32] | 1.10 → 0.84 | 141/308 | -21.57% | 0.39 |  |
| BTAL50+KMLM50 | 0.25 | 0.8 | QQQ<SMA200 | 0.85 | 0.84 | 1.02 [0.62–1.42] | 1.05 → 1.18 | 166.5/390 | -25.81% | 0.46 | yes* |
| BTAL25+KMLM75 | 0.2 | 0.8 | QQQ<SMA200 | 0.86 | 0.84 | 0.97 [0.45–1.52] | 1.17 → 1.29 | 195.5/476 | -24.03% | 0.38 | yes* |
| BTAL25+KMLM75 | 0.3 | 0.6 | QQQ<SMA200 | 0.85 | 0.84 | 0.96 [0.65–1.14] | 0.99 → 0.95 | 160/377 | -28.66% | 0.46 |  |

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
