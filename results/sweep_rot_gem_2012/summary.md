# Sweep summary

- Data: 2012-01-03..2026-08-24
- Data dir: tests/data/2026-08-24-net15
- Objective: calmar
- Constraint: max_drawdown >= -0.5
- Windows: full 2012-01-03..2026-08-24; fit 2012-01-03..2022-12-30; test 2023-01-03..2026-08-24; 20 sensitivity
- Costs: per-asset (SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3, IEF 1, TLT 1, SHY 1, AGG 1, EFA 1, EEM 1, IWM 1, VTI 1, BIL 1, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2, VEU 2, VWO 2, DBC 3, ACWX 3, SCZ 5, * 6) bps, cash yield 3%
- Snapped: windows.holdout 2023-01-01 -> 2023-01-03
- Sensitivity windows overlap by construction; the dispersion reported across them is a description, not a statistical test.

## Top 15 of 18 feasible grid strategies by robust_score

| assets | score.months | filter | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|---|---|
| SPY+VEU | 14 | @SPY>BIL | 0.32 | 0.29 | 0.31 [0.10–1.12] | 0.26 → 0.88 | 9/13 | -33.72% | - | yes* |
| SPY+ACWX | 10 | @SPY>BIL | 0.30 | 0.29 | 0.34 [0.09–1.10] | 0.25 → 0.83 | 8/18 | -33.72% | - | yes* |
| SPY+ACWX | 14 | @SPY>BIL | 0.32 | 0.29 | 0.31 [0.10–1.12] | 0.26 → 0.88 | 9/15 | -33.74% | - | yes* |
| SPY+VEU | 10 | @SPY>BIL | 0.29 | 0.29 | 0.33 [0.06–1.10] | 0.23 → 0.83 | 9.5/18 | -33.69% | - | yes* |
| SPY+VEU | 10 | >BIL | 0.31 | 0.29 | 0.39 [0.06–1.10] | 0.23 → 1.00 | 6.5/17 | -33.69% | - | yes* |
| SPY+VEU | 14 | >BIL | 0.32 | 0.29 | 0.31 [0.10–1.12] | 0.26 → 0.88 | 9/13 | -33.72% | - | yes* |
| SPY+ACWX | 10 | >BIL | 0.32 | 0.29 | 0.40 [0.09–1.10] | 0.25 → 0.99 | 6/15 | -33.72% | - | yes* |
| SPY+ACWX | 14 | >BIL | 0.32 | 0.29 | 0.31 [0.10–1.12] | 0.26 → 0.88 | 9/15 | -33.74% | - | yes* |
| SPY+EFA | 10 | >BIL | 0.32 | 0.27 | 0.44 [0.13–0.98] | 0.25 → 0.96 | 3/11 | -33.70% | - | yes* |
| SPY+EFA | 12 | >BIL | 0.27 | 0.29 | 0.27 [0.04–0.58] | 0.20 → 0.89 | 11/17 | -33.72% | - |  |
| SPY+EFA | 14 | >BIL | 0.29 | 0.27 | 0.29 [0.10–1.07] | 0.26 → 0.70 | 7/18 | -33.70% | - | yes* |
| SPY+EFA | 10 | @SPY>BIL | 0.29 | 0.26 | 0.34 [0.13–0.98] | 0.25 → 0.74 | 4/16 | -33.70% | - | yes* |
| SPY+EFA | 12 | @SPY>BIL | 0.26 | 0.29 | 0.26 [0.04–0.53] | 0.20 → 0.85 | 11/17 | -33.72% | - |  |
| SPY+EFA | 14 | @SPY>BIL | 0.30 | 0.26 | 0.31 [0.10–1.07] | 0.26 → 0.75 | 7/17 | -33.70% | - | yes* |
| SPY+ACWX | 12 | @SPY>BIL | 0.29 | 0.30 | 0.26 [0.05–0.63] | 0.22 → 0.93 | 13/15 | -33.75% | - |  |

\* on the grid boundary — extend the grid in that direction before believing this point.

## Baselines

| baseline | full calmar | nbr min | sens median [min–max] | holdout fit → test | rank med/worst | maxdd full | avg risk wt | edge |
|---|---|---|---|---|---|---|---|---|
| SPY60/AGG40 | 0.44 | - | 0.47 [0.25–1.34] | 0.36 → 1.27 | - | -21.60% | - | - |
| EW SPY/VEU/AGG | 0.35 | - | 0.34 [0.14–0.62] | 0.26 → 1.43 | - | -23.39% | - | - |
| ROT SPY top1 12M@SPY>BIL fb AGG | 0.31 | - | 0.32 [0.07–0.65] | 0.25 → 0.94 | - | -33.73% | - | - |
| ROT SPY+VEU top1 12M all fb AGG | 0.40 | - | 0.47 [0.22–1.13] | 0.33 → 1.10 | - | -33.77% | - | - |
| SPY benchmark | 0.43 | - | 0.52 [0.26–1.14] | 0.36 → 1.19 | - | -33.74% | - | - |
