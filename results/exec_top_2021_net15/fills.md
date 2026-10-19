# Execution robustness — adverse intraday fills: `exec_top_2021_net15.json`

Reproduce:

```
uv run execution_report.py fills --spec specs/exec_top_2021_net15.json --data tests/data/2026-08-24-net15 --alpha 0 0.25 0.5 1
```

- Data: `tests/data/2026-08-24-net15` @ `b81aa6c`, 2020-12-18 → 2026-08-24, 1425 trading days, 68 monthly sessions
- Costs: `cost_bps` per side TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6; `cash_yield` 0.03
- Benchmark (paired comparisons): SPY benchmark
- Fill model (§4.1): buy at C·(1 + α(H/C − 1)), sell at C·(1 − α(1 − L/C)), ratios from the root's `unadjusted/` bars; `cost_bps` charged on top; sizing and valuation at the close
- α levels: 0, 0.25, 0.5, 1 — 0.5 the headline reasonable worst case, 1 the literal high/low (a bound, not a scenario)
- Days with no unadjusted bar (filled at the close): KMLM 80

## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1, α = 0.5)

| strategy | CAGR edge over SPY benchmark at α = 0.5 | break-even α, CAGR | break-even α, Calmar | read-out |
|---|---:|---:|---:|---|
| 1 B50K50 - VT BTAL50+KMLM50 gated | +2.18 pp | > max α | > max α | **FILL-ROBUST** |
| 2 B75D25 - VT BTAL75+DBMF25 gated | -0.04 pp | 0.49 | 0.96 | **FILL-FRAGILE** |
| 3 B75K25 - VT BTAL75+KMLM25 gated | -0.05 pp | 0.49 | > max α | **FILL-FRAGILE** |
| 4 flag variant - VT BIL50+BTAL50 gated | +0.25 pp | 0.58 | > max α | **FILL-ROBUST** |

## Strategy × α

Δ columns against α = 0. Slippage = Σ |fill − close| · shares; bps of the close notional traded.

| strategy | α | final value | CAGR | Δ CAGR | XIRR | max drawdown | Calmar | Δ Calmar | Sharpe | fees | slippage | slippage bps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 B50K50 - VT BTAL50+KMLM50 gated | 0 | $59,036.28 | +18.63 % | +0.00 pp | +18.69 % | -20.88 % | 0.892 | +0.000 | 0.93 | $185.53 | $0.00 | 0.0 |
| 1 B50K50 - VT BTAL50+KMLM50 gated | 0.25 | $57,163.96 | +17.51 % | -1.12 pp | +17.56 % | -21.35 % | 0.820 | -0.072 | 0.88 | $182.00 | $1,400.52 | 29.2 |
| 1 B50K50 - VT BTAL50+KMLM50 gated | 0.5 | $55,417.04 | +16.47 % | -2.15 pp | +16.46 % | -21.85 % | 0.754 | -0.138 | 0.84 | $178.22 | $2,735.46 | 58.2 |
| 1 B50K50 - VT BTAL50+KMLM50 gated | 1 | $52,148.15 | +14.40 % | -4.22 pp | +14.33 % | -22.83 % | 0.631 | -0.261 | 0.75 | $171.25 | $5,227.13 | 115.7 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 0 | $56,588.44 | +16.48 % | +0.00 pp | +17.20 % | -18.94 % | 0.870 | +0.000 | 0.86 | $161.52 | $0.00 | 0.0 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 0.25 | $54,776.44 | +15.33 % | -1.15 pp | +16.06 % | -19.28 % | 0.795 | -0.075 | 0.81 | $158.11 | $1,429.45 | 30.1 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 0.5 | $53,086.65 | +14.25 % | -2.23 pp | +14.96 % | -19.99 % | 0.713 | -0.157 | 0.76 | $154.93 | $2,796.69 | 60.0 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 1 | $49,818.74 | +12.01 % | -4.46 pp | +12.73 % | -21.33 % | 0.563 | -0.307 | 0.66 | $148.35 | $5,333.37 | 119.4 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 0 | $56,017.43 | +16.41 % | +0.00 pp | +16.84 % | -18.97 % | 0.865 | +0.000 | 0.86 | $182.32 | $0.00 | 0.0 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 0.25 | $54,213.34 | +15.28 % | -1.14 pp | +15.69 % | -19.37 % | 0.789 | -0.077 | 0.81 | $178.74 | $1,414.79 | 30.0 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 0.5 | $52,524.52 | +14.24 % | -2.17 pp | +14.58 % | -19.54 % | 0.729 | -0.136 | 0.77 | $175.06 | $2,762.74 | 59.8 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 1 | $49,288.80 | +12.09 % | -4.32 pp | +12.36 % | -20.40 % | 0.593 | -0.272 | 0.67 | $168.12 | $5,273.56 | 118.9 |
| 4 flag variant - VT BIL50+BTAL50 gated | 0 | $58,136.94 | +16.45 % | +0.00 pp | +18.15 % | -18.12 % | 0.908 | +0.000 | 0.86 | $115.69 | $0.00 | 0.0 |
| 4 flag variant - VT BIL50+BTAL50 gated | 0.25 | $56,545.26 | +15.51 % | -0.94 pp | +17.17 % | -18.57 % | 0.835 | -0.072 | 0.82 | $113.68 | $1,271.08 | 26.4 |
| 4 flag variant - VT BIL50+BTAL50 gated | 0.5 | $54,958.08 | +14.55 % | -1.90 pp | +16.17 % | -19.23 % | 0.757 | -0.151 | 0.78 | $111.51 | $2,495.90 | 52.8 |
| 4 flag variant - VT BIL50+BTAL50 gated | 1 | $52,010.74 | +12.71 % | -3.74 pp | +14.24 % | -20.24 % | 0.628 | -0.280 | 0.70 | $107.10 | $4,775.23 | 104.7 |
| SPY benchmark | 0 | $56,050.60 | +14.67 % | +0.00 pp | +16.86 % | -23.68 % | 0.619 | +0.000 | 0.92 | $2.40 | $0.00 | 0.0 |
| SPY benchmark | 0.25 | $56,039.79 | +14.43 % | -0.24 pp | +16.86 % | -23.89 % | 0.604 | -0.015 | 0.91 | $2.40 | $48.81 | 14.3 |
| SPY benchmark | 0.5 | $55,994.15 | +14.29 % | -0.38 pp | +16.83 % | -24.05 % | 0.594 | -0.025 | 0.90 | $2.40 | $100.34 | 29.4 |
| SPY benchmark | 1 | $55,841.09 | +13.97 % | -0.69 pp | +16.73 % | -24.38 % | 0.573 | -0.046 | 0.88 | $2.41 | $192.24 | 56.2 |

## Edge over SPY benchmark at the same α

| strategy | CAGR α=0 | CAGR α=0.25 | CAGR α=0.5 | CAGR α=1 | Calmar α=0 | Calmar α=0.25 | Calmar α=0.5 | Calmar α=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 B50K50 - VT BTAL50+KMLM50 gated | +3.96 pp | +3.08 pp | +2.18 pp | +0.43 pp | +0.272 | +0.216 | +0.160 | +0.058 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | +1.81 pp | +0.90 pp | -0.04 pp | -1.96 pp | +0.251 | +0.191 | +0.119 | -0.010 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | +1.75 pp | +0.85 pp | -0.05 pp | -1.88 pp | +0.246 | +0.185 | +0.135 | +0.020 |
| 4 flag variant - VT BIL50+BTAL50 gated | +1.78 pp | +1.08 pp | +0.25 pp | -1.27 pp | +0.288 | +0.231 | +0.162 | +0.055 |

## Realised slippage by symbol and side (bp of close notional, every strategy's trades)

| symbol | buy α=0 | sell α=0 | buy α=0.25 | sell α=0.25 | buy α=0.5 | sell α=0.5 | buy α=1 | sell α=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BIL | 0.0 | 0.0 | 0.2 | 0.0 | 0.4 | 0.0 | 0.8 | 0.0 |
| BTAL | 0.0 | 0.0 | 16.4 | 21.8 | 32.6 | 43.5 | 64.5 | 87.0 |
| DBMF | 0.0 | 0.0 | 12.4 | 10.1 | 24.8 | 20.2 | 49.8 | 40.5 |
| KMLM | 0.0 | 0.0 | 13.2 | 8.3 | 26.4 | 16.6 | 52.9 | 33.3 |
| SPY | 0.0 | · | 14.3 | · | 29.4 | · | 56.2 | · |
| TQQQ | 0.0 | 0.0 | 38.7 | 49.0 | 77.1 | 97.8 | 152.5 | 194.8 |
