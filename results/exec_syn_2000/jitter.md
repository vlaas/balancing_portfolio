# Execution robustness — rebalance-date jitter: `exec_syn_2000.json`

Reproduce:

```
uv run execution_report.py jitter --spec specs/exec_syn_2000.json --data tests/data/2026-08-24-syn-net15 --days 10 --draws 500 --seed 20261020
```

- Data: `tests/data/2026-08-24-syn-net15` @ `b81aa6c`, 2000-01-03 → 2011-12-30, 3019 trading days, 143 monthly sessions
- Costs: `cost_bps` per side TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6; `cash_yield` 0.03
- Benchmark (paired comparisons): SPY benchmark
- Jitter: each month's session (deposit + rebalance) moved by a uniform offset in ±10 trading days; 500 draws, seed 20261020; one calendar per draw for every strategy
- Calendar edits: clamps in 0 of 500 draws (mean 0.00 per draw), bumps in 113 (at most 3 in one draw)

## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1)

| strategy | canonical Calmar | p10 | p90 | P(Calmar > SPY benchmark) | read-out |
|---|---:|---:|---:|---:|---|
| VT TQQQ+BIL gated | 0.111 | 0.015 | 0.110 | 0.934 | **TIMING-FRAGILE** |
| VT TQQQ+BIL gated mg10 | 0.111 | 0.023 | 0.117 | 0.960 | **TIMING-ROBUST** |

## CAGR (TWR) across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT TQQQ+BIL gated | +3.97 % | 0.91 | +2.25 % | 1.32 % | -1.73 % | +0.07 % | +1.49 % | +2.23 % | +3.10 % | +4.51 % | +6.27 % |
| VT TQQQ+BIL gated mg10 | +3.99 % | 0.90 | +2.41 % | 1.27 % | -1.71 % | +0.41 % | +1.62 % | +2.38 % | +3.19 % | +4.54 % | +6.06 % |
| SPY benchmark | +0.29 % | 0.08 | +0.31 % | 0.01 % | +0.27 % | +0.29 % | +0.30 % | +0.31 % | +0.31 % | +0.33 % | +0.36 % |

## Calmar across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT TQQQ+BIL gated | 0.111 | 0.91 | 0.061 | 0.038 | -0.040 | 0.002 | 0.036 | 0.058 | 0.084 | 0.128 | 0.194 |
| VT TQQQ+BIL gated mg10 | 0.111 | 0.88 | 0.067 | 0.038 | -0.039 | 0.011 | 0.042 | 0.064 | 0.089 | 0.130 | 0.231 |
| SPY benchmark | 0.005 | 0.08 | 0.006 | 0.000 | 0.005 | 0.005 | 0.005 | 0.006 | 0.006 | 0.006 | 0.007 |

## Max drawdown across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT TQQQ+BIL gated | -35.85 % | 0.75 | -38.53 % | 3.64 % | -51.51 % | -44.76 % | -40.96 % | -38.44 % | -35.89 % | -32.89 % | -29.00 % |
| VT TQQQ+BIL gated mg10 | -35.85 % | 0.63 | -37.15 % | 3.42 % | -50.55 % | -42.39 % | -39.50 % | -37.01 % | -34.87 % | -31.99 % | -25.09 % |
| SPY benchmark | -55.36 % | 0.36 | -55.35 % | 0.01 % | -55.38 % | -55.37 % | -55.36 % | -55.35 % | -55.35 % | -55.34 % | -55.33 % |

## XIRR across draws

| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VT TQQQ+BIL gated | +7.17 % | 0.94 | +4.90 % | 1.43 % | +0.61 % | +2.56 % | +4.00 % | +4.82 % | +5.90 % | +7.35 % | +10.11 % |
| VT TQQQ+BIL gated mg10 | +7.18 % | 0.94 | +5.20 % | 1.39 % | +0.93 % | +3.11 % | +4.24 % | +5.24 % | +6.14 % | +7.34 % | +9.44 % |
| SPY benchmark | +2.96 % | 0.50 | +2.96 % | 0.03 % | +2.86 % | +2.90 % | +2.94 % | +2.96 % | +2.98 % | +3.01 % | +3.04 % |

## Paired against SPY benchmark — share of draws the strategy is ahead

Max drawdown: ahead = shallower. Best of all: share of draws the strategy ranks first among every row, the benchmark included.

| strategy | CAGR | XIRR | max drawdown | Calmar | Sharpe | best CAGR | best Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|
| VT TQQQ+BIL gated | 0.926 | 0.920 | 1.000 | 0.934 | 0.904 | 0.384 | 0.364 |
| VT TQQQ+BIL gated mg10 | 0.954 | 0.954 | 1.000 | 0.960 | 0.938 | 0.578 | 0.602 |
| SPY benchmark | · | · | · | · | · | 0.038 | 0.034 |

## Fixed-offset scan — Calmar, every month's session moved by d trading days

| d | VT TQQQ+BIL gated | VT TQQQ+BIL gated mg10 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|---:|
| -10 | 0.072 | 0.085 | 0.006 | 0 | 0 |
| -9 | 0.063 | 0.071 | 0.006 | 0 | 0 |
| -8 | 0.087 | 0.087 | 0.005 | 0 | 0 |
| -7 | 0.062 | 0.101 | 0.006 | 0 | 0 |
| -6 | 0.103 | 0.124 | 0.006 | 0 | 0 |
| -5 | 0.084 | 0.160 | 0.006 | 0 | 0 |
| -4 | 0.065 | 0.100 | 0.005 | 0 | 0 |
| -3 | 0.095 | 0.088 | 0.005 | 0 | 0 |
| -2 | 0.074 | 0.074 | 0.006 | 0 | 0 |
| -1 | 0.020 | 0.103 | 0.006 | 0 | 0 |
| +0 (canonical) | 0.111 | 0.111 | 0.005 | 0 | 0 |
| +1 | 0.094 | 0.060 | 0.006 | 0 | 0 |
| +2 | 0.082 | 0.082 | 0.006 | 0 | 0 |
| +3 | 0.043 | 0.044 | 0.006 | 0 | 0 |
| +4 | 0.044 | 0.052 | 0.006 | 0 | 0 |
| +5 | 0.056 | 0.045 | 0.006 | 0 | 0 |
| +6 | 0.055 | 0.051 | 0.006 | 0 | 0 |
| +7 | 0.048 | 0.056 | 0.006 | 0 | 0 |
| +8 | 0.042 | 0.014 | 0.006 | 0 | 0 |
| +9 | 0.097 | 0.038 | 0.006 | 0 | 0 |
| +10 | 0.051 | 0.050 | 0.006 | 0 | 0 |

## Fixed-offset scan — CAGR, every month's session moved by d trading days

| d | VT TQQQ+BIL gated | VT TQQQ+BIL gated mg10 | SPY benchmark | clamps | bumps |
|---:|---:|---:|---:|---:|---:|
| -10 | +3.02 % | +3.55 % | +0.31 % | 0 | 0 |
| -9 | +2.48 % | +2.62 % | +0.31 % | 0 | 0 |
| -8 | +3.20 % | +3.13 % | +0.30 % | 0 | 0 |
| -7 | +2.23 % | +3.42 % | +0.31 % | 0 | 0 |
| -6 | +3.07 % | +3.48 % | +0.31 % | 0 | 0 |
| -5 | +3.07 % | +4.59 % | +0.31 % | 0 | 0 |
| -4 | +2.23 % | +2.95 % | +0.29 % | 0 | 0 |
| -3 | +3.26 % | +3.02 % | +0.30 % | 0 | 0 |
| -2 | +2.40 % | +2.42 % | +0.34 % | 0 | 0 |
| -1 | +0.85 % | +3.59 % | +0.33 % | 0 | 0 |
| +0 (canonical) | +3.97 % | +3.99 % | +0.29 % | 0 | 0 |
| +1 | +3.49 % | +2.32 % | +0.32 % | 0 | 0 |
| +2 | +3.24 % | +3.25 % | +0.30 % | 0 | 0 |
| +3 | +1.61 % | +1.64 % | +0.33 % | 0 | 0 |
| +4 | +1.60 % | +1.91 % | +0.32 % | 0 | 0 |
| +5 | +1.77 % | +1.47 % | +0.31 % | 0 | 0 |
| +6 | +1.94 % | +1.84 % | +0.31 % | 0 | 0 |
| +7 | +1.80 % | +2.06 % | +0.31 % | 0 | 0 |
| +8 | +1.76 % | +0.59 % | +0.32 % | 0 | 0 |
| +9 | +4.07 % | +1.60 % | +0.31 % | 0 | 0 |
| +10 | +2.12 % | +2.08 % | +0.33 % | 0 | 0 |
