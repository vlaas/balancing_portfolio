# Balancing portfolio simulator

The purpose of this program is to simulate a long portfolio of multiple assets which is
rebalanced monthly to fixed target ratios (a Shannon's Demon style strategy), with a fixed
monthly capital contribution. The simulation is compared against buying SPY with the same
cash flows.

# Rules

- Strategies are classes in `strategies/`, one file each, extending `Strategy` from
  `strategy.py` and combined into named bundles in `bundles.py`. The bundle to run is
  selected at run time (`uv run main.py [bundle]`, default `default`). Every strategy in
  the bundle is simulated independently with identical cash flows and reported side by
  side.
- A strategy declares `label`, `weights` (traded assets → target fraction of portfolio
  value) and optionally `data` (extra symbols its hooks read but never trade), and may
  override two hooks, each receiving a `MarketDay` view of the day's data
  (`ctx.close(sym)`, `ctx.indicator(sym, name)` — `None` before a series' history
  begins, `KeyError` for a column that was never loaded):
  - `balance(ctx) -> weights` — dynamic target weights per rebalance day (default: the
    static `weights`; must cover the same assets, be non-negative, sum ≤ 1).
  - `allow_buy(asset, ctx) -> bool` — the gate: whether `asset` may be bought that day.
    A gated asset is never bought (natural rebalance sells still execute); its budget is
    redistributed across the non-gated assets in proportion to their weights. If every
    asset is gated, the contribution stays in cash.
- Each bundle defines its configuration: the start date, initial capital, and monthly
  added capital.
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

Daily OHLC prices per symbol, in CSV form with columns `time,open,high,low,close`
(`time` is `YYYY-MM-DD`). Only `time` and `close` are read; see `data/README.md`.
Indicators are computed by the simulator from `indicators.py` and declared per
strategy (`indicators = {"QQQ": (sma(200),)}`); each loads as `SYM:NAME` (e.g.
`QQQ:SMA200`) and is read via `ctx.indicator("QQQ", "SMA200")`. Symbols listed only in
a strategy's `data` join the trading calendar without extending it (their extra dates
are ignored) and may be null before their history begins.

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
- Imbalance, measured after the trades of every rebalance point against the weights the
  strategy's `balance()` asked for (gates and integer shares leave residual deviation):
  - misallocation = ½ Σ |actual − target| over assets and cash — the fraction of the
    portfolio in the wrong place (average and worst rebalance reported);
  - worst-asset deviation = the single worst asset's |actual − target| (cash excluded).

Output form:

- A printed summary table in the console (all strategies and the SPY benchmark side by
  side).
- Saved charts: equity curve, drawdown curve, 12-month rolling Sharpe, and post-rebalance
  misallocation — each showing all strategies and the benchmark. Output directory
  selectable with `--charts` (default `charts/`); the Markdown report's image links
  follow it.
- Optionally (`--md` flag) a Markdown report file with the summary table, drawdown
  tables, correlations, and the charts embedded via relative links.
- Optionally (`--tx` flag) a Markdown transaction log: every deposit, buy and sell per
  strategy with date, shares, price, amount, cash after, and that day's portfolio value.
  Each rebalance day ends with a BALANCE row showing actual/target percents per asset.
- Optionally (`--json` flag) a machine-readable results file: the schema version, the
  commit it was run from, the bundle's configuration, the data range, and per strategy
  the summary statistics, drawdown table, yearly returns, imbalance stats (aggregate and
  per rebalance day) and correlation to the benchmark. Keys are sorted and every float
  is rounded to 8 decimals, so two runs diff cleanly in git; `generated_at` is the only
  field that changes when nothing else does.
- Optionally (`--curves` flag) one CSV per strategy of every daily series the charts are
  drawn from — `date, value, flow, ret, index, drawdown, rolling_sharpe` — named after
  the strategy's slug (`tqqq-btal-50-50.csv`).

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

Shared settings (start date, initial capital, monthly contribution) are a `Config`
dataclass defined in `simulate.py`. A bundle in `bundles.py` pairs a list of strategies
with its own `Config`; select one with `uv run main.py [bundle]` (default: `default`).
Put the bundle name before the flags — `--md` and `--tx` take an optional path and would
otherwise consume the name. Per-strategy behavior lives in the strategy classes.

# Initial configuration

The `default` bundle's settings:

- Start date: 2017-01-03
- Starting capital: USD 10,000
- Strategy 1 — TQQQ/BTAL 50/50:
  - TQQQ — 50% of value
  - BTAL — 50% of value
- Strategy 2 — TQQQ 100%:
  - TQQQ — 100% of value
- Monthly added capital: USD 500
