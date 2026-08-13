# Balancing portfolio simulator

The purpose of this program is to simulate a long portfolio of multiple assets which is
rebalanced monthly to fixed target ratios (a Shannon's Demon style strategy), with a fixed
monthly capital contribution. The simulation is compared against buying SPY with the same
cash flows.

# Rules

- Configuration defines one or more named strategies. Each strategy assigns assets a
  target fraction of the portfolio by current value (example: 60% value in asset A, 40%
  value in asset B). Every strategy is simulated independently with identical cash flows
  and reported side by side.
- Configuration defines the start date, initial capital, and monthly added capital.
- Only integer amounts of shares can be bought or sold — no fractional shares. Perfect
  balance therefore cannot be achieved; the simulator gets as close as integer shares allow.
- All trades execute at the **close price** of the trade day.
- **Initial purchase:** on the start date, buy shares of each asset at that day's close so
  the portfolio matches the target ratios as closely as integer shares allow (for each
  asset: `floor(capital × target_ratio / close)` shares). Unspent capital remains as cash.
- **Monthly rebalance:** on the last trading day of each month:
  1. Add the configured monthly contribution to cash.
  2. Compute total capital = market value of holdings (at close) + cash.
  3. For each asset, compute the target share count:
     `floor(total × target_ratio / close)`.
  4. Sell or buy the difference between current and target share counts. (This naturally
     uses the contribution to buy the underweight asset first and only sells the
     overweight asset when the contribution isn't enough.)
- Leftover cash carries forward to the next month and earns no interest.
- No transaction costs, no taxes, no dividends (see Input data).
- The simulation runs from the start date until the last date available in the data.

# Input data

Daily OHLC prices per asset, in CSV form with columns `time,open,high,low,close`
(`time` is `YYYY-MM-DD`).

Available data files:

- SPY: `data/SPY.csv`
- BTAL: `data/BTAL.csv`
- TQQQ: `data/TQQQ.csv`

Data notes:

- Prices are split-adjusted but **not** dividend-adjusted. Dividends are ignored; results
  are price-return only. This understates absolute returns for both the portfolio and the
  SPY benchmark, but consistently so.
- **Missing dates:** BTAL is missing ~73 trading days that SPY/TQQQ have. The trading
  calendar is the union of all assets' dates. For valuation on a day where an asset has no
  row, carry its last known close forward. If the last trading day of a month is missing
  for an asset, its trades that month execute at its most recent available close.

# Output

Because capital is added monthly, raw portfolio value is misleading (deposits mask
losses), so:

- Return-based statistics are computed on a **time-weighted return (TWR)** equity curve
  built from daily returns adjusted for cash flows.
- Additionally report the **money-weighted return (XIRR)** — "how did my actual dollars do".

Reported statistics (for each strategy and for the SPY benchmark):

- Final value, total capital contributed, and net profit
  (final value − total contributed), absolute and in %.
- CAGR (from TWR) and money-weighted annual return (XIRR).
- Drawdowns, computed on the TWR curve:
  - Maximum drawdown: depth and duration (peak to recovery).
  - The next top drawdowns (top 5 total) with depth and duration.
- Sharpe ratio: from daily TWR, annualized (√252), risk-free rate 0%
  (limitation: no rate data available).
  - "Over time": 12-month rolling Sharpe.
- Other common statistics: annualized volatility, Sortino ratio, Calmar ratio,
  best/worst year, and correlation of each strategy to the SPY benchmark.

Output form:

- A printed summary table in the console (all strategies and the SPY benchmark side by
  side).
- Saved charts: equity curve, drawdown curve, 12-month rolling Sharpe — each showing all
  strategies and the benchmark.

# Comparison to SP500

The benchmark strategy invests the same cash flows into SPY: the initial capital at the
start date's close, plus the monthly contribution on the same last-trading-day-of-month
dates. Integer shares only; when cash is insufficient for a whole share it accumulates
until it is. The same statistics are computed for the benchmark.

# Programming language

The program is written in Python.

- Polars as the data library.
- Other libraries may be used as needed (e.g. matplotlib for charts).

# Configuration

Configuration is a simple Python class/dataclass with values (no config file needed).

# Initial configuration

- Start date: 2017-01-03
- Starting capital: USD 10,000
- Strategy 1 — TQQQ/BTAL 50/50:
  - TQQQ — 50% of value
  - BTAL — 50% of value
- Strategy 2 — TQQQ 100%:
  - TQQQ — 100% of value
- Monthly added capital: USD 500
