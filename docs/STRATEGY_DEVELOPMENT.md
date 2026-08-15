# Strategy development guide

How to add a strategy to the simulator: what you write, what the engine does
for you, what data you can use, and the sharp edges to watch for. For how the
machinery works internally, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Quickstart

A fixed-weight strategy is a declaration, nothing more. Create
`strategies/my_mix.py`:

```python
from strategy import Strategy


class MyMix(Strategy):
    """One third each of SPY, TQQQ and BTAL."""

    label = "SPY/TQQQ/BTAL"          # keep ≤ 20 characters (report column width)
    weights = {"SPY": 1 / 3, "TQQQ": 1 / 3, "BTAL": 1 / 3}
```

Register it in `main.py` by importing it and adding an instance to
`STRATEGIES`. Keep `SpyBenchmark()` last — the last entry is the reference for
the correlation statistics. Run `uv run main.py` and your strategy appears as a
new column in the table and a new line in every chart — but note that `COLORS`
in `report.py` has exactly as many entries as shipped strategies (four), so
adding a strategy also means adding a chart color there, or the charts silently
drop it (see Pitfalls).

Requirements: every symbol in `weights` needs a `data/<SYM>.csv`, with price
history starting no later than the simulation start date (`start` in
`main.py`). The start date itself must be an actual trading day.

## The two hooks

The base class runs a fixed-weight strategy with no code. Behavior comes from
overriding one or both hooks. Both are called only on **trade days** — the
first simulation day and the last trading day of each month — and receive a
`MarketDay` (`ctx`) with that day's data.

### `balance(ctx) -> dict[str, float]` — dynamic target weights

Return the allocation you want *this* rebalance. Rules, asserted by the engine:

- same asset keys as `weights` (assets can't appear or vanish mid-simulation);
- every weight ≥ 0;
- weights may sum to **less than 1** — the remainder is a deliberate cash
  reserve, which the engine keeps in cash even when gate redistribution fires.

Setting an asset's weight to `0.0` sells it entirely at that rebalance — this
is how you express a forced exit (a gate alone never sells, see below).

### `allow_buy(asset, ctx) -> bool` — the purchase gate

Return `False` to refuse *buying* `asset` that day. The engine's gate policy
(uniform for all strategies, so you don't implement it):

- a gated asset is never bought; it keeps what it holds;
- if the gated asset is *overweight*, the normal rebalance sell down to its
  target still executes — a gate blocks accumulation, not risk reduction;
- the budget the gated asset declines is **redistributed** to the non-gated
  assets in proportion to their weights among themselves (the portfolio stays
  fully invested apart from any deliberate cash reserve);
- if *every* asset is gated, the month's contribution simply idles in cash.

## Reading market data

`ctx` gives row-level access to everything that was loaded:

```python
ctx.date                          # datetime.date of the trade day
ctx.close("QQQ")                  # close price, or None before QQQ's history
ctx.indicator("QQQ", "SMA200")    # "QQQ:SMA200" column, or None before it exists
```

- To read a symbol you don't trade, declare it: `data = ("QQQ",)`. Symbols in
  `weights` are always loaded.
- **`None` means "no value yet"** — the column exists but this date precedes
  its history. Your hook must decide what that means; it is a strategy
  decision, not a data error. The SMA-gate strategy treats missing data as
  gate-open so it behaves like its plain twin until the signal exists.
- **`KeyError` means you made a mistake** — the column was never loaded (typo'd
  indicator name, symbol missing from `data`). This is deliberate: under
  redistribution, a silently-returned `None` would silently reshape the whole
  portfolio.

## Data files and indicators

- CSVs live in `data/<SYM>.csv` with columns `time,open,high,low,close` —
  TradingView's export format. Only `close` is used for trading and valuation.
- Any **additional column becomes an indicator**, loaded as `SYM:COL`:
  `data/QQQ.csv` has an `SMA200` column → `ctx.indicator("QQQ", "SMA200")`.
  Indicators are precomputed in the CSV (e.g. by TradingView), not calculated
  by the simulator.
- The trading calendar is defined by the **traded** symbols only. `data`
  symbols are joined onto it: their extra dates are ignored, their gaps are
  forward-filled, and they may begin after the simulation start (values are
  `None` until then).
- Traded symbols must cover the whole simulation; a traded symbol with no
  history at the start date fails the loader's completeness assert.

## What the engine does for you

You never write money mechanics. Per trade day the engine: deposits the
contribution, calls your hooks, computes integer-share targets
(`floor(total · weight / close)` — no fractional shares), applies the gate
policy, executes sells before buys so cash never goes negative, and records
three artifacts per strategy: the daily equity curve, a full transaction
ledger, and post-trade target-vs-actual allocations. The report layer turns
those into the stats table (incl. misallocation statistics), four charts, and
the optional `report.md` / `transactions.md`.

## Worked examples

### A gate: don't accumulate TQQQ below QQQ's SMA200

The shipped proof of concept, `strategies/tqqq_btal_qqq_sma200.py`:

```python
from strategy import MarketDay, Strategy


class TqqqBtalQqqSma200(Strategy):
    label = "TQQQ/BTAL SMA gate"
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    data = ("QQQ",)                        # read QQQ without trading it

    def allow_buy(self, asset: str, ctx: MarketDay) -> bool:
        if asset != "TQQQ":
            return True                    # gate only applies to TQQQ
        close = ctx.close("QQQ")
        sma = ctx.indicator("QQQ", "SMA200")
        if close is None or sma is None:
            return True                    # no signal yet -> behave like plain 50/50
        return close >= sma
```

While QQQ trades below its SMA200, monthly TQQQ purchases stop and that budget
buys BTAL instead; TQQQ holdings are kept (and still sold down if a rally makes
them overweight). In the 2017–2026 data this fires on 21 rebalance days and the
misallocation chart shows exactly when.

### A dynamic balance: risk-off allocation with a cash reserve

```python
from strategy import MarketDay, Strategy


class RiskOff(Strategy):
    label = "TQQQ risk-off"
    weights = {"TQQQ": 0.7, "BTAL": 0.3}
    data = ("QQQ",)

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        close = ctx.close("QQQ")
        sma = ctx.indicator("QQQ", "SMA200")
        if close is not None and sma is not None and close < sma:
            return {"TQQQ": 0.2, "BTAL": 0.6}   # sum 0.8 -> 20% held as cash
        return self.weights
```

Below the SMA this *sells TQQQ down* to 20%, holds 60% BTAL, and parks 20% in
cash until the regime flips back.

### Combining them

`balance()` moves the target; `allow_buy()` limits how the engine may move
toward it. A common pattern: use `balance()` for regime shifts that should
force sells, and `allow_buy()` for "stop adding, don't dump" conditions.

## Pitfalls

- **Hooks run only on trade days.** A signal that fires mid-month and clears
  before month-end is invisible. That is the product's design (monthly
  cadence), not a bug — don't expect stop-loss-like behavior.
- **Look-ahead bias is your responsibility.** Indicator columns come
  precomputed; make sure each row's value uses only data up to that date (a
  200-day SMA does; a full-period z-score would not).
- **Think through `None`.** Gating on missing data doesn't just skip a buy —
  under redistribution it pushes the entire budget into the other assets. The
  POC's "missing → allow" choice is why it starts out identical to the plain
  50/50.
- **A fifth strategy needs a fifth chart color** — `COLORS` in `report.py` has
  four entries and `zip` silently drops extra strategies from charts.
  Keep `label` within 20 characters or the console table misaligns.
- **New traded symbols constrain the start date** — the loader's completeness
  assert requires every *traded* symbol to have history by the start date, so
  the simulation can only start once all of them exist (e.g. KMLM data begins
  2020-12-18). (The calendar itself is a union of traded symbols' dates, so a
  new symbol can add trading days, never remove them.) `data`-only symbols
  don't have this constraint.

## Verifying a new strategy

1. `uv run main.py --tx` — read your strategy's section in `transactions.md`:
   the BALANCE row after each rebalance shows actual/target percents per asset
   and for cash, and every BUY/SELL is listed with its price and running cash.
2. Check the misallocation column and `charts/imbalance.png` — spikes should
   appear exactly when your gate/balance logic deviates from the static
   weights, and collapse when it re-converges.
3. For hook logic worth keeping, add a hand-computed test following the pattern
   of `test_gate_redirects_the_blocked_budget` in `tests/test_simulate.py`:
   build a tiny synthetic frame (the `frame()` helper accepts indicator columns
   like `"A:GATE"`), work out the expected integer share counts on paper, and
   assert the trades and allocations. Run `uv run pytest`.
