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

## Top 15 of 498 feasible grid strategies by robust_score

| safe | sigma_target | w_max | gate | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BTAL25+KMLM75 | 0.2 | 0.4 | QQQ<SMA200 | 0.88 | 0.83 | 1.00 [0.49–1.34] | 1.17 → 0.92 | 220/470 | -20.16% | 0.31 | yes* |
| BTAL25+KMLM75 | 0.25 | 0.5 | QQQ<SMA200 | 0.87 | 0.83 | 1.01 [0.58–1.22] | 1.07 → 0.92 | 180/414 | -24.24% | 0.38 |  |
| BTAL50+KMLM50 | 0.25 | 0.5 | QQQ<SMA200 | 0.87 | 0.85 | 1.01 [0.72–1.30] | 1.08 → 0.83 | 127.5/305 | -21.61% | 0.39 |  |
| BTAL25+KMLM75 | 0.3 | 0.6 | QQQ<SMA200 | 0.84 | 0.83 | 0.94 [0.64–1.11] | 0.96 → 0.93 | 153.5/373 | -28.71% | 0.46 |  |
| KMLM | 0.3 | 0.6 | QQQ<SMA200 | 0.84 | 0.82 | 0.96 [0.54–1.08] | 0.98 → 0.99 | 174/433 | -30.85% | 0.46 |  |
| BTAL50+KMLM50 | 0.3 | 0.6 | QQQ<SMA200 | 0.84 | 0.82 | 0.91 [0.75–1.13] | 0.90 → 0.86 | 154/275 | -26.53% | 0.46 |  |
| KMLM | 0.35 | 0.7 | QQQ<SMA200 | 0.82 | 0.81 | 0.92 [0.60–1.06] | 0.89 → 0.97 | 163.5/395 | -34.77% | 0.54 |  |
| BTAL50+KMLM50 | 0.2 | 0.8 | QQQ<SMA200 | 0.85 | 0.81 | 1.00 [0.56–1.61] | 1.11 → 1.14 | 176.5/428 | -21.25% | 0.38 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.5 | QQQ<SMA200 | 0.85 | 0.81 | 1.03 [0.58–1.50] | 1.18 → 0.94 | 210.5/410 | -19.17% | 0.34 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.6 | QQQ<SMA200 | 0.81 | 0.83 | 0.96 [0.54–1.57] | 1.09 → 1.03 | 234/438 | -21.15% | 0.36 | yes* |
| BTAL50+KMLM50 | 0.2 | 0.7 | QQQ<SMA200 | 0.83 | 0.81 | 0.98 [0.54–1.60] | 1.10 → 1.09 | 211.5/430 | -21.25% | 0.37 | yes* |
| BTAL50+KMLM50 | 0.25 | 0.6 | QQQ<SMA200 | 0.85 | 0.81 | 0.97 [0.65–1.28] | 1.03 → 0.97 | 161.5/352 | -23.24% | 0.42 |  |
| BTAL50+KMLM50 | 0.25 | 0.7 | QQQ<SMA200 | 0.81 | 0.81 | 0.95 [0.60–1.32] | 1.01 → 1.09 | 187.5/391 | -25.32% | 0.44 |  |
| BTAL50+KMLM50 | 0.25 | 0.8 | QQQ<SMA200 | 0.81 | 0.81 | 0.97 [0.59–1.39] | 1.01 → 1.14 | 197/403 | -26.24% | 0.46 | yes* |
| KMLM | 0.2 | 0.4 | QQQ<SMA200 | 0.84 | 0.81 | 0.85 [0.34–1.16] | 1.07 → 1.01 | 280.5/494 | -23.63% | 0.31 | yes* |

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
