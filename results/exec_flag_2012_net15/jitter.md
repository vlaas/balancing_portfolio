# Execution robustness — rebalance-date jitter: `exec_flag_2012_net15.json`

Reproduce:

```
uv run execution_report.py jitter --spec specs/exec_flag_2012_net15.json --data tests/data/2026-08-24-net15 --days 10 --draws 500 --seed 20261020
```

- Data: `tests/data/2026-08-24-net15` @ `b81aa6c`, 2012-01-03 → 2026-08-24, 3681 trading days, 175 monthly sessions
- Costs: `cost_bps` per side TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6; `cash_yield` 0.03
- Benchmark (paired comparisons): SPY benchmark
- Jitter: each month's session (deposit + rebalance) moved by a uniform offset in ±10 trading days; 500 draws, seed 20261020; one calendar per draw for every strategy
- Calendar edits: clamps in 0 of 500 draws (mean 0.00 per draw), bumps in 101 (at most 3 in one draw)

## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1)

| strategy | canonical Calmar | p10 | p90 | P(Calmar > SPY benchmark) | read-out |
|---|---:|---:|---:|---:|---|
| 4 flag variant - VT BIL50+BTAL50 gated | 0.821 | 0.521 | 0.934 | 0.984 | **TIMING-ROBUST** |
| 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | 0.714 | 0.568 | 0.866 | 0.986 | **TIMING-ROBUST** |

## CAGR (TWR) across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated | +20.08 % | 0.42 | +20.26 % | 1.76 % | +13.97 % | +17.36 % | +19.03 % | +20.38 % | +21.52 % | +23.03 % | +25.48 % |
| 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | +18.54 % | 0.61 | +18.26 % | 0.87 % | +15.71 % | +16.74 % | +17.72 % | +18.28 % | +18.89 % | +19.61 % | +20.83 % |
| SPY benchmark | +14.60 % | 0.90 | +14.58 % | 0.02 % | +14.54 % | +14.55 % | +14.56 % | +14.58 % | +14.59 % | +14.60 % | +14.62 % |

## Calmar across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated | 0.821 | 0.70 | 0.724 | 0.165 | 0.290 | 0.480 | 0.591 | 0.720 | 0.846 | 1.000 | 1.209 |
| 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | 0.714 | 0.60 | 0.691 | 0.121 | 0.369 | 0.537 | 0.602 | 0.664 | 0.787 | 0.915 | 1.015 |
| SPY benchmark | 0.433 | 0.72 | 0.432 | 0.001 | 0.431 | 0.431 | 0.432 | 0.432 | 0.433 | 0.433 | 0.434 |

## Max drawdown across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated | -24.44 % | 0.78 | -29.07 % | 5.13 % | -48.15 % | -38.37 % | -33.60 % | -28.22 % | -24.77 % | -22.47 % | -19.09 % |
| 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | -25.95 % | 0.59 | -27.09 % | 4.01 % | -42.89 % | -31.65 % | -29.92 % | -27.75 % | -23.55 % | -21.03 % | -19.59 % |
| SPY benchmark | -33.74 % | 0.28 | -33.72 % | 0.03 % | -33.77 % | -33.77 % | -33.74 % | -33.72 % | -33.70 % | -33.68 % | -33.66 % |

## XIRR across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated | +18.56 % | 0.41 | +18.87 % | 1.95 % | +12.23 % | +15.35 % | +17.59 % | +18.94 % | +20.18 % | +21.81 % | +25.32 % |
| 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | +17.00 % | 0.60 | +16.75 % | 0.98 % | +13.90 % | +15.10 % | +16.14 % | +16.74 % | +17.45 % | +18.34 % | +19.58 % |
| SPY benchmark | +14.63 % | 0.75 | +14.62 % | 0.02 % | +14.57 % | +14.59 % | +14.61 % | +14.62 % | +14.63 % | +14.64 % | +14.67 % |

## Paired against SPY benchmark — share of draws the strategy is ahead

Max drawdown: ahead = shallower. Best of all: share of draws the strategy ranks first among every row, the benchmark included.

| strategy | CAGR | XIRR | max drawdown | Calmar | Sharpe | best CAGR | best Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|
| 4 flag variant - VT BIL50+BTAL50 gated | 0.998 | 0.982 | 0.752 | 0.984 | 0.714 | 0.948 | 0.536 |
| 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | 1.000 | 0.980 | 0.966 | 0.986 | 0.808 | 0.052 | 0.454 |
| SPY benchmark | · | · | · | · | · | 0.000 | 0.010 |

## Fixed-offset scan — Calmar, every month's session moved by d trading days

| d | 4 flag variant - VT BIL50+BTAL50 gated | 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|---:|
| -10 | 0.789 | 0.684 | 0.432 | 0 | 0 |
| -9 | 0.592 | 0.625 | 0.434 | 0 | 0 |
| -8 | 0.515 | 0.600 | 0.434 | 0 | 0 |
| -7 | 0.612 | 0.623 | 0.433 | 0 | 0 |
| -6 | 0.637 | 0.622 | 0.433 | 0 | 0 |
| -5 | 0.825 | 0.630 | 0.432 | 0 | 0 |
| -4 | 1.037 | 0.748 | 0.434 | 0 | 0 |
| -3 | 0.888 | 0.751 | 0.433 | 0 | 0 |
| -2 | 0.669 | 0.717 | 0.432 | 0 | 0 |
| -1 | 0.832 | 0.692 | 0.432 | 0 | 0 |
| +0 (canonical) | 0.821 | 0.714 | 0.433 | 0 | 0 |
| +1 | 0.594 | 0.823 | 0.432 | 0 | 0 |
| +2 | 0.586 | 0.784 | 0.432 | 0 | 0 |
| +3 | 0.618 | 0.760 | 0.432 | 0 | 0 |
| +4 | 0.789 | 0.838 | 0.432 | 0 | 0 |
| +5 | 0.685 | 0.787 | 0.431 | 0 | 0 |
| +6 | 0.703 | 0.731 | 0.431 | 0 | 0 |
| +7 | 0.825 | 0.836 | 0.432 | 0 | 0 |
| +8 | 0.762 | 0.732 | 0.432 | 0 | 0 |
| +9 | 0.635 | 0.606 | 0.433 | 0 | 0 |
| +10 | 0.680 | 0.706 | 0.432 | 0 | 0 |

## Fixed-offset scan — CAGR, every month's session moved by d trading days

| d | 4 flag variant - VT BIL50+BTAL50 gated | 4 flag variant - VT BIL50+BTAL50 gated lam0.94 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|---:|
| -10 | +22.65 % | +18.61 % | +14.59 % | 0 | 0 |
| -9 | +19.43 % | +18.09 % | +14.62 % | 0 | 0 |
| -8 | +18.93 % | +17.85 % | +14.60 % | 0 | 0 |
| -7 | +21.62 % | +18.81 % | +14.59 % | 0 | 0 |
| -6 | +22.08 % | +19.22 % | +14.60 % | 0 | 0 |
| -5 | +22.07 % | +18.84 % | +14.58 % | 0 | 0 |
| -4 | +22.27 % | +19.25 % | +14.60 % | 0 | 0 |
| -3 | +21.29 % | +19.32 % | +14.59 % | 0 | 0 |
| -2 | +19.80 % | +18.81 % | +14.59 % | 0 | 0 |
| -1 | +21.20 % | +18.68 % | +14.60 % | 0 | 0 |
| +0 (canonical) | +20.08 % | +18.54 % | +14.60 % | 0 | 0 |
| +1 | +17.40 % | +17.77 % | +14.56 % | 0 | 0 |
| +2 | +18.29 % | +17.87 % | +14.55 % | 0 | 0 |
| +3 | +17.97 % | +17.61 % | +14.56 % | 0 | 0 |
| +4 | +19.32 % | +17.75 % | +14.57 % | 0 | 0 |
| +5 | +17.19 % | +16.69 % | +14.56 % | 0 | 0 |
| +6 | +17.51 % | +16.95 % | +14.56 % | 0 | 0 |
| +7 | +19.01 % | +17.55 % | +14.56 % | 0 | 0 |
| +8 | +17.44 % | +16.72 % | +14.57 % | 0 | 0 |
| +9 | +17.78 % | +16.45 % | +14.58 % | 0 | 0 |
| +10 | +19.51 % | +17.55 % | +14.57 % | 0 | 0 |
