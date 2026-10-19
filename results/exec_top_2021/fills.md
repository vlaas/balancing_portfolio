# Execution robustness — adverse intraday fills: `exec_top_2021.json`

Reproduce:

```
uv run execution_report.py fills --spec specs/exec_top_2021.json --data data --alpha 0 0.25 0.5 1 --out results/exec_top_2021
```

- Data: `data` @ `0ffe674`, 2020-12-18 → 2026-10-19, 1464 trading days, 70 monthly sessions
- Costs: `cost_bps` per side TQQQ 1.5, BTAL 6, DBMF 2.5, KMLM 6, QQQ 1, SPY 0.7, BIL 0.5, * 6; `cash_yield` 0.03
- Benchmark (paired comparisons): SPY benchmark
- Fill model (§4.1): buy at C·(1 + α(H/C − 1)), sell at C·(1 − α(1 − L/C)), ratios from the root's `unadjusted/` bars; `cost_bps` charged on top; sizing and valuation at the close
- α levels: 0, 0.25, 0.5, 1 — 0.5 the headline reasonable worst case, 1 the literal high/low (a bound, not a scenario)
- Days with no unadjusted bar (filled at the close): KMLM 80

## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1, α = 0.5)

| strategy | CAGR edge over SPY benchmark at α = 0.5 | break-even α, CAGR | break-even α, Calmar | read-out |
|---|---:|---:|---:|---|
| 1 B50K50 - VT BTAL50+KMLM50 gated | +3.21 pp | > max α | > max α | **FILL-ROBUST** |
| 2 B75D25 - VT BTAL75+DBMF25 gated | +0.82 pp | 0.72 | > max α | **FILL-ROBUST** |
| 3 B75K25 - VT BTAL75+KMLM25 gated | +0.87 pp | 0.74 | > max α | **FILL-ROBUST** |
| 4 flag variant - VT BIL50+BTAL50 gated | +0.80 pp | 0.76 | > max α | **FILL-ROBUST** |

## Strategy × α

Δ columns against α = 0. Slippage = Σ |fill − close| · shares; bps of the close notional traded.

| strategy | α | final value | CAGR | Δ CAGR | XIRR | max drawdown | Calmar | Δ Calmar | Sharpe | fees | slippage | slippage bps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 B50K50 - VT BTAL50+KMLM50 gated | 0 | $63,613.99 | +19.47 % | +0.00 pp | +19.78 % | -20.75 % | 0.938 | +0.000 | 0.96 | $203.23 | $0.00 | 0.0 |
| 1 B50K50 - VT BTAL50+KMLM50 gated | 0.25 | $61,678.96 | +18.41 % | -1.06 pp | +18.72 % | -21.24 % | 0.867 | -0.071 | 0.92 | $199.20 | $1,448.90 | 27.5 |
| 1 B50K50 - VT BTAL50+KMLM50 gated | 0.5 | $59,764.21 | +17.36 % | -2.11 pp | +17.64 % | -21.76 % | 0.798 | -0.141 | 0.87 | $195.12 | $2,833.41 | 55.0 |
| 1 B50K50 - VT BTAL50+KMLM50 gated | 1 | $56,159.51 | +15.27 % | -4.20 pp | +15.52 % | -22.70 % | 0.673 | -0.265 | 0.79 | $186.98 | $5,403.52 | 109.5 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 0 | $60,783.64 | +17.26 % | +0.00 pp | +18.22 % | -18.81 % | 0.917 | +0.000 | 0.89 | $176.23 | $0.00 | 0.0 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 0.25 | $58,827.40 | +16.14 % | -1.12 pp | +17.10 % | -19.39 % | 0.832 | -0.085 | 0.84 | $172.42 | $1,467.21 | 28.3 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 0.5 | $56,962.92 | +14.97 % | -2.28 pp | +16.00 % | -20.09 % | 0.745 | -0.172 | 0.79 | $168.69 | $2,866.22 | 56.5 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | 1 | $53,472.28 | +12.80 % | -4.45 pp | +13.84 % | -21.63 % | 0.592 | -0.325 | 0.70 | $161.40 | $5,469.18 | 112.5 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 0 | $60,259.64 | +17.20 % | +0.00 pp | +17.92 % | -18.82 % | 0.914 | +0.000 | 0.90 | $198.83 | $0.00 | 0.0 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 0.25 | $58,352.48 | +16.10 % | -1.11 pp | +16.82 % | -19.22 % | 0.837 | -0.077 | 0.85 | $194.74 | $1,456.40 | 28.3 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 0.5 | $56,517.82 | +15.02 % | -2.18 pp | +15.73 % | -19.62 % | 0.766 | -0.149 | 0.80 | $190.43 | $2,839.95 | 56.4 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | 1 | $53,029.55 | +12.91 % | -4.30 pp | +13.56 % | -20.49 % | 0.630 | -0.284 | 0.71 | $182.53 | $5,419.57 | 112.4 |
| 4 flag variant - VT BIL50+BTAL50 gated | 0 | $61,441.65 | +16.82 % | +0.00 pp | +18.59 % | -18.03 % | 0.933 | +0.000 | 0.88 | $126.35 | $0.00 | 0.0 |
| 4 flag variant - VT BIL50+BTAL50 gated | 0.25 | $59,790.63 | +15.93 % | -0.90 pp | +17.66 % | -18.57 % | 0.858 | -0.075 | 0.84 | $124.10 | $1,301.40 | 24.8 |
| 4 flag variant - VT BIL50+BTAL50 gated | 0.5 | $58,102.17 | +14.95 % | -1.87 pp | +16.68 % | -19.11 % | 0.783 | -0.151 | 0.80 | $121.71 | $2,554.45 | 49.5 |
| 4 flag variant - VT BIL50+BTAL50 gated | 1 | $54,962.48 | +13.11 % | -3.71 pp | +14.78 % | -20.16 % | 0.651 | -0.282 | 0.71 | $116.68 | $4,890.28 | 98.6 |
| SPY benchmark | 0 | $57,880.95 | +14.60 % | +0.00 pp | +16.55 % | -23.98 % | 0.609 | +0.000 | 0.93 | $2.46 | $0.00 | 0.0 |
| SPY benchmark | 0.25 | $57,611.49 | +14.33 % | -0.27 pp | +16.39 % | -24.13 % | 0.594 | -0.015 | 0.91 | $2.48 | $50.30 | 14.2 |
| SPY benchmark | 0.5 | $57,487.52 | +14.15 % | -0.44 pp | +16.31 % | -24.29 % | 0.583 | -0.026 | 0.90 | $2.49 | $95.68 | 27.0 |
| SPY benchmark | 1 | $57,313.98 | +13.87 % | -0.72 pp | +16.21 % | -24.33 % | 0.570 | -0.039 | 0.88 | $2.45 | $190.79 | 54.9 |

## Edge over SPY benchmark at the same α

| strategy | CAGR α=0 | CAGR α=0.25 | CAGR α=0.5 | CAGR α=1 | Calmar α=0 | Calmar α=0.25 | Calmar α=0.5 | Calmar α=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 B50K50 - VT BTAL50+KMLM50 gated | +4.87 pp | +4.08 pp | +3.21 pp | +1.40 pp | +0.330 | +0.273 | +0.215 | +0.103 |
| 2 B75D25 - VT BTAL75+DBMF25 gated | +2.66 pp | +1.81 pp | +0.82 pp | -1.07 pp | +0.309 | +0.239 | +0.162 | +0.022 |
| 3 B75K25 - VT BTAL75+KMLM25 gated | +2.61 pp | +1.77 pp | +0.87 pp | -0.96 pp | +0.306 | +0.244 | +0.183 | +0.060 |
| 4 flag variant - VT BIL50+BTAL50 gated | +2.23 pp | +1.60 pp | +0.80 pp | -0.76 pp | +0.324 | +0.264 | +0.200 | +0.081 |

## Realised slippage by symbol and side (bp of close notional, every strategy's trades)

| symbol | buy α=0 | sell α=0 | buy α=0.25 | sell α=0.25 | buy α=0.5 | sell α=0.5 | buy α=1 | sell α=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BIL | 0.0 | 0.0 | 0.2 | 0.0 | 0.4 | 0.0 | 0.8 | 0.0 |
| BTAL | 0.0 | 0.0 | 16.1 | 19.5 | 32.0 | 39.0 | 63.3 | 78.1 |
| DBMF | 0.0 | 0.0 | 12.4 | 8.8 | 24.9 | 17.7 | 50.0 | 35.7 |
| KMLM | 0.0 | 0.0 | 13.2 | 8.7 | 26.4 | 17.5 | 52.9 | 34.9 |
| SPY | 0.0 | · | 14.2 | · | 27.0 | · | 54.9 | · |
| TQQQ | 0.0 | 0.0 | 34.9 | 47.6 | 69.6 | 95.2 | 138.3 | 189.7 |
