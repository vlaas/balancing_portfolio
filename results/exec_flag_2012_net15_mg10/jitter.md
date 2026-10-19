# Execution robustness — rebalance-date jitter: `exec_flag_2012_net15_mg10.json`

Reproduce:

```
uv run execution_report.py jitter --spec specs/exec_flag_2012_net15_mg10.json --data tests/data/2026-08-24-net15 --days 10 --draws 500 --seed 20261020
```

- Data: `tests/data/2026-08-24-net15` @ `b81aa6c`, 2012-01-03 → 2026-08-24, 3681 trading days, 175 monthly sessions
- Costs: `cost_bps` per side TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6; `cash_yield` 0.03
- Benchmark (paired comparisons): SPY benchmark
- Jitter: each month's session (deposit + rebalance) moved by a uniform offset in ±10 trading days; 500 draws, seed 20261020; one calendar per draw for every strategy
- Calendar edits: clamps in 0 of 500 draws (mean 0.00 per draw), bumps in 101 (at most 3 in one draw)

## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1)

| strategy | canonical Calmar | p10 | p90 | P(Calmar > SPY benchmark) | read-out |
|---|---:|---:|---:|---:|---|
| 4 flag variant - VT BIL50+BTAL50 gated mg10 | 0.821 | 0.522 | 0.945 | 0.984 | **TIMING-ROBUST** |

## CAGR (TWR) across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated mg10 | +20.08 % | 0.41 | +20.36 % | 1.75 % | +13.97 % | +17.33 % | +19.19 % | +20.47 % | +21.63 % | +23.14 % | +25.47 % |
| SPY benchmark | +14.60 % | 0.90 | +14.58 % | 0.02 % | +14.54 % | +14.55 % | +14.56 % | +14.58 % | +14.59 % | +14.60 % | +14.62 % |

## Calmar across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated mg10 | 0.821 | 0.69 | 0.731 | 0.166 | 0.290 | 0.485 | 0.593 | 0.731 | 0.864 | 1.006 | 1.209 |
| SPY benchmark | 0.433 | 0.72 | 0.432 | 0.001 | 0.431 | 0.431 | 0.432 | 0.432 | 0.433 | 0.433 | 0.434 |

## Max drawdown across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated mg10 | -24.44 % | 0.77 | -28.91 % | 5.15 % | -48.15 % | -38.37 % | -33.60 % | -27.90 % | -24.67 % | -22.29 % | -19.10 % |
| SPY benchmark | -33.74 % | 0.28 | -33.72 % | 0.03 % | -33.77 % | -33.77 % | -33.74 % | -33.72 % | -33.70 % | -33.68 % | -33.66 % |

## XIRR across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated mg10 | +18.56 % | 0.41 | +18.97 % | 1.95 % | +12.23 % | +15.60 % | +17.69 % | +19.08 % | +20.26 % | +21.93 % | +25.56 % |
| SPY benchmark | +14.63 % | 0.75 | +14.62 % | 0.02 % | +14.57 % | +14.59 % | +14.61 % | +14.62 % | +14.63 % | +14.64 % | +14.67 % |

## Paired against SPY benchmark — share of draws the strategy is ahead

Max drawdown: ahead = shallower. Best of all: share of draws the strategy ranks first among every row, the benchmark included.

| strategy | CAGR | XIRR | max drawdown | Calmar | Sharpe | best CAGR | best Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated mg10 | 0.998 | 0.988 | 0.754 | 0.984 | 0.730 | 0.998 | 0.984 |
| SPY benchmark | · | · | · | · | · | 0.002 | 0.016 |

## Fixed-offset scan — Calmar, every month's session moved by d trading days

| d | 4 flag variant - VT BIL50+BTAL50 gated mg10 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|
| -10 | 0.791 | 0.432 | 0 | 0 |
| -9 | 0.599 | 0.434 | 0 | 0 |
| -8 | 0.508 | 0.434 | 0 | 0 |
| -7 | 0.612 | 0.433 | 0 | 0 |
| -6 | 0.637 | 0.433 | 0 | 0 |
| -5 | 0.821 | 0.432 | 0 | 0 |
| -4 | 1.003 | 0.434 | 0 | 0 |
| -3 | 0.887 | 0.433 | 0 | 0 |
| -2 | 0.673 | 0.432 | 0 | 0 |
| -1 | 0.824 | 0.432 | 0 | 0 |
| +0 (canonical) | 0.821 | 0.433 | 0 | 0 |
| +1 | 0.594 | 0.432 | 0 | 0 |
| +2 | 0.594 | 0.432 | 0 | 0 |
| +3 | 0.618 | 0.432 | 0 | 0 |
| +4 | 0.789 | 0.432 | 0 | 0 |
| +5 | 0.685 | 0.431 | 0 | 0 |
| +6 | 0.779 | 0.431 | 0 | 0 |
| +7 | 0.837 | 0.432 | 0 | 0 |
| +8 | 0.768 | 0.432 | 0 | 0 |
| +9 | 0.654 | 0.433 | 0 | 0 |
| +10 | 0.697 | 0.432 | 0 | 0 |

## Fixed-offset scan — CAGR, every month's session moved by d trading days

| d | 4 flag variant - VT BIL50+BTAL50 gated mg10 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|
| -10 | +22.70 % | +14.59 % | 0 | 0 |
| -9 | +19.68 % | +14.62 % | 0 | 0 |
| -8 | +18.68 % | +14.60 % | 0 | 0 |
| -7 | +21.62 % | +14.59 % | 0 | 0 |
| -6 | +22.08 % | +14.60 % | 0 | 0 |
| -5 | +21.96 % | +14.58 % | 0 | 0 |
| -4 | +22.11 % | +14.60 % | 0 | 0 |
| -3 | +21.27 % | +14.59 % | 0 | 0 |
| -2 | +19.92 % | +14.59 % | 0 | 0 |
| -1 | +21.00 % | +14.60 % | 0 | 0 |
| +0 (canonical) | +20.08 % | +14.60 % | 0 | 0 |
| +1 | +17.40 % | +14.56 % | 0 | 0 |
| +2 | +18.53 % | +14.55 % | 0 | 0 |
| +3 | +17.97 % | +14.56 % | 0 | 0 |
| +4 | +19.32 % | +14.57 % | 0 | 0 |
| +5 | +17.19 % | +14.56 % | 0 | 0 |
| +6 | +17.83 % | +14.56 % | 0 | 0 |
| +7 | +19.29 % | +14.56 % | 0 | 0 |
| +8 | +17.58 % | +14.57 % | 0 | 0 |
| +9 | +18.30 % | +14.58 % | 0 | 0 |
| +10 | +20.01 % | +14.57 % | 0 | 0 |
