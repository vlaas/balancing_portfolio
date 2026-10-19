# Execution robustness — rebalance-date jitter: `exec_qqq_2000.json`

Reproduce:

```
uv run execution_report.py jitter --spec specs/exec_qqq_2000.json --data tests/data/2026-08-24-net15 --days 10 --draws 500 --seed 20261020
```

- Data: `tests/data/2026-08-24-net15` @ `b81aa6c`, 2000-01-03 → 2011-12-30, 3019 trading days, 143 monthly sessions
- Costs: `cost_bps` per side TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6; `cash_yield` 0.03
- Benchmark (paired comparisons): SPY benchmark
- Jitter: each month's session (deposit + rebalance) moved by a uniform offset in ±10 trading days; 500 draws, seed 20261020; one calendar per draw for every strategy
- Calendar edits: clamps in 0 of 500 draws (mean 0.00 per draw), bumps in 113 (at most 3 in one draw)

## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1)

| strategy | canonical Calmar | p10 | p90 | P(Calmar > SPY benchmark) | read-out |
|---|---:|---:|---:|---:|---|
| VT QQQ+cash gated | 0.145 | 0.042 | 0.130 | 1.000 | **TIMING-FRAGILE** |
| VT QQQ+cash gated mg10 | 0.145 | 0.047 | 0.129 | 1.000 | **TIMING-FRAGILE** |

## CAGR (TWR) across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT QQQ+cash gated | +5.05 % | 0.94 | +3.26 % | 1.07 % | +0.55 % | +1.54 % | +2.48 % | +3.17 % | +4.01 % | +5.10 % | +6.24 % |
| VT QQQ+cash gated mg10 | +5.05 % | 0.95 | +3.32 % | 0.98 % | +0.90 % | +1.77 % | +2.65 % | +3.24 % | +3.97 % | +5.04 % | +6.24 % |
| SPY benchmark | +0.29 % | 0.08 | +0.31 % | 0.01 % | +0.27 % | +0.29 % | +0.30 % | +0.31 % | +0.31 % | +0.33 % | +0.36 % |

## Calmar across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT QQQ+cash gated | 0.145 | 0.96 | 0.081 | 0.034 | 0.011 | 0.033 | 0.056 | 0.075 | 0.104 | 0.143 | 0.186 |
| VT QQQ+cash gated mg10 | 0.145 | 0.96 | 0.083 | 0.032 | 0.017 | 0.038 | 0.060 | 0.077 | 0.101 | 0.142 | 0.212 |
| SPY benchmark | 0.005 | 0.08 | 0.006 | 0.000 | 0.005 | 0.005 | 0.005 | 0.006 | 0.006 | 0.006 | 0.007 |

## Max drawdown across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT QQQ+cash gated | -34.87 % | 0.94 | -41.66 % | 4.14 % | -52.57 % | -47.85 % | -44.74 % | -42.00 % | -38.67 % | -34.61 % | -31.50 % |
| VT QQQ+cash gated mg10 | -34.86 % | 0.93 | -41.34 % | 4.24 % | -52.57 % | -47.82 % | -44.51 % | -41.46 % | -38.30 % | -34.40 % | -28.75 % |
| SPY benchmark | -55.36 % | 0.36 | -55.35 % | 0.01 % | -55.38 % | -55.37 % | -55.36 % | -55.35 % | -55.35 % | -55.34 % | -55.33 % |

## XIRR across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT QQQ+cash gated | +7.94 % | 0.95 | +6.39 % | 0.95 % | +3.00 % | +4.75 % | +5.78 % | +6.45 % | +7.05 % | +7.92 % | +9.04 % |
| VT QQQ+cash gated mg10 | +7.94 % | 0.96 | +6.57 % | 0.87 % | +4.04 % | +5.17 % | +5.98 % | +6.60 % | +7.19 % | +7.88 % | +9.34 % |
| SPY benchmark | +2.96 % | 0.50 | +2.96 % | 0.03 % | +2.86 % | +2.90 % | +2.94 % | +2.96 % | +2.98 % | +3.01 % | +3.04 % |

## Paired against SPY benchmark — share of draws the strategy is ahead

Max drawdown: ahead = shallower. Best of all: share of draws the strategy ranks first among every row, the benchmark included.

| strategy | CAGR | XIRR | max drawdown | Calmar | Sharpe | best CAGR | best Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|
| VT QQQ+cash gated | 1.000 | 1.000 | 1.000 | 1.000 | 0.996 | 0.404 | 0.412 |
| VT QQQ+cash gated mg10 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.596 | 0.588 |
| SPY benchmark | · | · | · | · | · | 0.000 | 0.000 |

## Fixed-offset scan — Calmar, every month's session moved by d trading days

| d | VT QQQ+cash gated | VT QQQ+cash gated mg10 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|---:|
| -10 | 0.097 | 0.100 | 0.006 | 0 | 0 |
| -9 | 0.070 | 0.078 | 0.006 | 0 | 0 |
| -8 | 0.094 | 0.097 | 0.005 | 0 | 0 |
| -7 | 0.089 | 0.106 | 0.006 | 0 | 0 |
| -6 | 0.158 | 0.193 | 0.006 | 0 | 0 |
| -5 | 0.127 | 0.182 | 0.006 | 0 | 0 |
| -4 | 0.114 | 0.139 | 0.005 | 0 | 0 |
| -3 | 0.106 | 0.102 | 0.005 | 0 | 0 |
| -2 | 0.109 | 0.109 | 0.006 | 0 | 0 |
| -1 | 0.034 | 0.124 | 0.006 | 0 | 0 |
| +0 (canonical) | 0.145 | 0.145 | 0.005 | 0 | 0 |
| +1 | 0.117 | 0.070 | 0.006 | 0 | 0 |
| +2 | 0.093 | 0.096 | 0.006 | 0 | 0 |
| +3 | 0.094 | 0.094 | 0.006 | 0 | 0 |
| +4 | 0.068 | 0.071 | 0.006 | 0 | 0 |
| +5 | 0.074 | 0.066 | 0.006 | 0 | 0 |
| +6 | 0.092 | 0.096 | 0.006 | 0 | 0 |
| +7 | 0.073 | 0.079 | 0.006 | 0 | 0 |
| +8 | 0.056 | 0.038 | 0.006 | 0 | 0 |
| +9 | 0.104 | 0.051 | 0.006 | 0 | 0 |
| +10 | 0.069 | 0.074 | 0.006 | 0 | 0 |

## Fixed-offset scan — CAGR, every month's session moved by d trading days

| d | VT QQQ+cash gated | VT QQQ+cash gated mg10 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|---:|
| -10 | +3.98 % | +4.10 % | +0.31 % | 0 | 0 |
| -9 | +2.90 % | +3.27 % | +0.31 % | 0 | 0 |
| -8 | +3.50 % | +3.58 % | +0.30 % | 0 | 0 |
| -7 | +3.43 % | +3.96 % | +0.31 % | 0 | 0 |
| -6 | +5.21 % | +5.83 % | +0.31 % | 0 | 0 |
| -5 | +4.71 % | +5.51 % | +0.31 % | 0 | 0 |
| -4 | +4.25 % | +4.57 % | +0.29 % | 0 | 0 |
| -3 | +3.83 % | +3.68 % | +0.30 % | 0 | 0 |
| -2 | +3.93 % | +3.93 % | +0.34 % | 0 | 0 |
| -1 | +1.64 % | +4.34 % | +0.33 % | 0 | 0 |
| +0 (canonical) | +5.05 % | +5.05 % | +0.29 % | 0 | 0 |
| +1 | +4.20 % | +3.04 % | +0.32 % | 0 | 0 |
| +2 | +3.67 % | +3.72 % | +0.30 % | 0 | 0 |
| +3 | +3.69 % | +3.68 % | +0.33 % | 0 | 0 |
| +4 | +2.88 % | +3.01 % | +0.32 % | 0 | 0 |
| +5 | +3.15 % | +2.81 % | +0.31 % | 0 | 0 |
| +6 | +3.49 % | +3.62 % | +0.31 % | 0 | 0 |
| +7 | +2.97 % | +3.23 % | +0.31 % | 0 | 0 |
| +8 | +2.43 % | +1.70 % | +0.32 % | 0 | 0 |
| +9 | +4.31 % | +2.28 % | +0.31 % | 0 | 0 |
| +10 | +2.89 % | +2.97 % | +0.33 % | 0 | 0 |
