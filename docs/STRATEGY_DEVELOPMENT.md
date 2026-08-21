# Strategy development guide

How to add a strategy to the simulator: what you write, what the engine does
for you, what data you can use, and the sharp edges to watch for. For how the
machinery works internally, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Declarative strategies

**If it can be a spec, it should be a spec.** A strategy that is a `fixed` or
`vol_target` parametrisation needs no Python at all: describe it in a JSON
spec file under `specs/` and run the file directly:

```json
{
  "schema_version": 1,
  "config": { "start": "2017-01-03", "initial_capital": 10000, "monthly_contribution": 500 },
  "strategies": [
    { "type": "fixed", "label": "TQQQ/BTAL 50/50", "weights": { "TQQQ": 0.5, "BTAL": 0.5 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "BTAL": 0.5 },
      "gate": { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 } },
    { "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
      "vol": { "kind": "ewma", "lam": 0.94 }, "leverage": 3, "sigma_target": 0.45, "w_max": 0.5 },
    { "type": "fixed", "label": "SPY benchmark", "weights": { "SPY": 1.0 } }
  ]
}
```

```
uv run main.py --spec specs/my_idea.json
```

`config` mirrors `simulate.Config` exactly. `strategies` is an ordered list,
**benchmark last**, minimum two entries. Unknown or missing keys fail with the
JSON path (`strategies[1].gate.sma_day: unknown key`) — a typo never silently
becomes a default. `specs/default.json` reproduces the code-defined `default`
bundle; `specs/research.json` holds the current research candidates.

**Cost model** (COST_MODEL_SPEC.md): `config` takes two optional fields, both
defaulting to `0.0` so every cost-free result stays reproducible.
`"cost_bps"` is a per-side proportional trading cost — a number applies to
every asset, an object (`{"TQQQ": 1.5, "BTAL": 6, "*": 6}`) sets per-symbol
rates with `"*"` as the default; a traded symbol that resolves to neither is a
build-time error. Fees are paid from cash at execution; buys are capped so
cash never goes negative, sells always execute in full. `"cash_yield"` is an
annual rate accrued daily (ACT/365, weekends included) on the cash balance as
internal return — flows, TWR and XIRR need no adjustment. Ranges: cost rates
in [0, 1000] bps, yield in [0, 0.20]. The calibrated tastytrade base schedule
lives in `specs/sweep_vt_cbase.json`.

The two types (`spec.py` maps them to `strategies/fixed.py` and
`strategies/vol_target.py`):

- **`fixed`** — constant `weights` (values ≥ 0, sum ≤ 1; the residual is a
  deliberate cash reserve), optional `gate`.
- **`vol_target`** — volatility targeting on one leveraged risk asset:
  `w_risk = clip(sigma_target / (leverage · σ), w_min, w_max)`, where σ is the
  `vol` indicator (`{"kind": "ewma", "lam": 0.94}` or
  `{"kind": "realized", "n": 63}`) computed on `vol_symbol`. `safe` receives
  `1 − w_risk` (`null` leaves the residual in cash); `fallback` (default
  `w_max`) applies while σ is still `None`. Optional `gate`.

A **`gate`** belongs to either type: it is closed on days
`close(symbol) < SMA` (`sma_days` or `sma_months`, exactly one) and open while
either value is `None`. When closed, buys of its `assets` stop; with
`"contribution_exempt": true` they continue up to that day's external cash ×
the asset's weight of the day.

`label` is optional — a missing one is generated deterministically from the
parameters (`TQQQ50/BTAL50 gate QQQ<SMA200`,
`VT TQQQ/BTAL t45 w0-50 QQQ:VOL_EWMA94`) — and labels must be unique. The
normalised spec (defaults and labels filled in) is embedded in `results.json`,
so a committed result reproduces on its own.

Write a strategy class only when the behavior can't be expressed as a spec.
The rest of this guide covers that.

## Sweeps

**A sweep result is a table to read, not a parameter to adopt.** When the
question is "which parameters are good?", don't hand-write twenty spec entries
— write a sweep spec (`specs/sweep_*.json`, full grammar and semantics in
[SWEEP_SPEC.md](SWEEP_SPEC.md)) and run it:

```
uv run sweep.py specs/sweep_vt.json --data tests/data --out results/sweep_vt
```

- **Template**: one strategy entry in the ordinary grammar in which any leaf —
  including the whole `gate` object — may be `{"grid": [v1, v2, ...]}` (≥ 2
  distinct values). The Cartesian product in document order becomes the grid;
  a `null` grid value drops the key (that's how "no gate" is a grid point).
  Grid dimensions must be label-visible (`leverage`, `fallback`, `gate.assets`
  are not in auto-labels and collide loudly).
- **Windows** own the dates: `full` (`start`..`end`), an optional holdout split
  (`fit`/`test`, adjacent and disjoint) and rolling or anchored sensitivity
  windows. Requested dates snap to trading days and every snap is printed.
- **robust_score** = min(full objective, neighbourhood minimum, sensitivity
  median, holdout test). It is deliberately a minimum: a point only scores
  high if it is good itself, its neighbours are good, it is good in the median
  sub-window and it held up out of sample. Points on a grid boundary are
  flagged — extend the grid in that direction before believing them.
- **Artefacts** (`--out`, committed together with the spec):
  `strategies.json`, `runs.csv`, `runs.json`, `summary.json`, `summary.md`.
  `--dry-run` prints the expanded strategies × windows count and writes
  nothing.
- **Cost what-ifs**: the sweep `config` takes the same optional `cost_bps` /
  `cash_yield` as an ordinary spec, forwarded into every window.
  `--cost-bps X` replaces the whole schedule with a flat rate and
  `--cash-yield Y` the yield, for a stress rerun without a near-duplicate spec
  file; overrides are recorded in `runs.csv`, the `summary.json` costs record
  and the `summary.md` header.

## Quickstart

A fixed-weight strategy is a declaration, nothing more. Create
`strategies/my_mix.py`:

```python
from strategy import Strategy


class MyMix(Strategy):
    """One third each of SPY, TQQQ and BTAL."""

    label = "SPY/TQQQ/BTAL"          # shown in the table, charts and report
    weights = {"SPY": 1 / 3, "TQQQ": 1 / 3, "BTAL": 1 / 3}
```

Register it in `bundles.py` by importing it and adding an instance to a
bundle's strategy list (the `default` bundle, or a new `BUNDLES` entry). Keep
`SpyBenchmark()` last in every bundle — the last entry is the reference for
the correlation statistics. Run `uv run main.py [bundle]` and your strategy
appears as a new column in the table and a new line in every chart.

Requirements: every symbol in `weights` needs a `data/<SYM>.csv`, with price
history starting no later than the simulation start date (the bundle's
`Config.start` in `bundles.py`). The start date itself must be an actual
trading day.

## The hooks

The base class runs a fixed-weight strategy with no code. Behavior comes from
overriding these hooks. All of them are called only on **trade days** — the
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

### `buy_cap(asset, ctx) -> float | None` — the dollar gate

The dollar generalisation of `allow_buy`: `None` puts no limit on buying
`asset` that day, `0.0` blocks buys entirely, and a positive cap buys at most
`floor(cap / price)` extra shares. The default derives from `allow_buy`, so a
strategy overrides one or the other, never both. `ctx.contribution` — the
external cash added that day — is what a contribution-exempt gate multiplies:
`cap = contribution × weight`. One sharp edge: *any* asset with a non-`None`
cap is treated as gated by the engine, even when the cap doesn't bind — its
capped target counts as spent budget and it is excluded from the
redistribution — so return `None`, not a large number, to mean "no limit".

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

- CSVs live in `data/<SYM>.csv` in TradingView's export format. The file is the
  **dividend-adjusted (total-return) export** — the traded series; the
  unadjusted export from the same session sits in `data/price/<SYM>.csv` as
  reference, and the loader never reads it. The loader reads **only `time` and
  `close`**; every other column (`open`, `high`, `low`, `SMA*`, `Volume`) is
  ignored. See `data/README.md`.
- **Dataset roles**: decision numbers come from a **net-of-withholding
  total-return dataset** (`tests/data/2026-08-20-net15`, derived from the
  frozen gross snapshot by `make_net_tr.py`; `docs/NET_TR_SPEC.md`) at stated
  costs. Gross-TR roots (live `data/`, `tests/data/2026-08-20`) are for
  comparability to gross artefacts and the TR goldens; the flat price-series
  snapshot is legacy regression only.
- **Every indicator is computed on the loaded close** — for traded and signal
  symbols alike, with no per-indicator series switch; in a net dataset that is
  the net series. A price-series SMA or vol on a distributing symbol would
  read distributions as weakness or spurious volatility. To reproduce a signal
  on a TradingView chart, turn dividend adjustment **on**.
- **Indicators are computed by the simulator**, from `indicators.py`, and
  declared per strategy:

  ```python
  class TqqqBtalQqqSma200(Strategy):
      weights = {"TQQQ": 0.5, "BTAL": 0.5}
      data = ("QQQ",)
      indicators = {"QQQ": (sma(200),)}   # loads "QQQ:SMA200"
  ```

  Each one loads as `SYM:NAME` and is read with `ctx.indicator("QQQ", "SMA200")`.
  The name embeds every parameter (`SMA200`, `SMA10M`, `VOL_EWMA94`), so two
  parameterisations coexist and the name *is* the indicator's identity —
  declarations are merged across the bundle and deduplicated by name.
- A symbol you attach an indicator to must be one you trade (`weights`) or read
  (`data`); anything else is an assertion error at load time.
- Available factories: `sma(n)`, `sma_monthly(m)`, `realized_vol(n)`,
  `ewma_vol(lam)`, `drawdown()`, `momentum(n)`. Add one by writing a factory
  and adding it to the causality test's parameter list in
  `tests/test_indicators.py`.
- Every indicator is computed on the **symbol's own bar calendar**, before the
  join onto the traded calendar. Computing after the join would shift an SMA by
  one bar wherever a symbol has a gap (BTAL, 2017-01-24). Values are `None`
  during warm-up — never zero, never a partial window.
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
- **Look-ahead bias is your responsibility.** An indicator's value at row *t*
  may depend only on closes at rows ≤ *t* (a 200-day SMA obeys this; a
  full-period z-score would not). `tests/test_indicators.py` enforces it by
  recomputing on a truncated frame — add every new factory to its parameter
  list. The one documented exception is `sma_monthly`, which needs the *next
  row's date* to know today is a month-end; that is calendar look-ahead, never
  price look-ahead, and is the same trade `is_rebalance_day` already makes.
- **Think through `None`.** Gating on missing data doesn't just skip a buy —
  under redistribution it pushes the entire budget into the other assets. The
  POC's "missing → allow" choice is why it starts out identical to the plain
  50/50.
- **Charts stop at 20 strategies** — `report.py` picks colours dynamically
  (the brand palette through 4 strategies, then tab10/tab20) and asserts
  beyond 20; run larger bundles with `--no-charts`. Console columns widen to
  the longest label automatically.
- **New traded symbols constrain the start date** — the loader's completeness
  assert requires every *traded* symbol to have history by the start date, so
  the simulation can only start once all of them exist (e.g. KMLM data begins
  2020-12-18). (The calendar itself is a union of traded symbols' dates, so a
  new symbol can add trading days, never remove them.) `data`-only symbols
  don't have this constraint.

## Verifying a new strategy

1. `uv run main.py --tx` (a non-default bundle name goes first:
   `uv run main.py <bundle> --tx`, or `--tx` would consume it as a path) — read
   your strategy's section in `transactions.md`:
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
