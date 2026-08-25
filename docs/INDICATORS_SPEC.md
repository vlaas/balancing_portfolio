# Specification: computing indicators in Python

Repo: `vlaas/balancing_portfolio` · baseline commit: `4a1b99f` ("Fresh dataset") · status: implemented

## 1. Goal

Move indicator computation out of TradingView exports and into the simulator, so that
adding an indicator, changing a parameter, or sweeping a parameter is a code change
(testable, reviewable, agent-executable) rather than a manual re-export of every
`data/*.csv`.

TradingView keeps two roles: it is the **price source**, and its exported `SMA*` columns
become a **verification fixture** for the Python implementation. It stops being a
runtime input.

Non-goals (separate specs): declarative strategy specs, JSON results, sweeps, MCP server.

## 2. Semantics — rules every indicator obeys

1. **Source is `close` only.** Consistent with the engine, which trades and values on close.
2. **Computed on the symbol's own bar calendar**, i.e. on the rows of `data/<SYM>.csv`,
   *before* the symbol is joined onto the traded calendar and forward-filled. This is what
   TradingView does; computing after the join would shift an SMA by one bar wherever a
   symbol has a gap (BTAL 2017-01-24).
3. **Causal.** The value at row *t* depends only on closes at rows ≤ *t*. Enforced by test.
4. **Null during warm-up.** No value is invented (no zero, no partial-window mean unless the
   indicator is defined that way). The existing contract holds: `ctx.indicator()` returns
   `None` before the value exists, `KeyError` if the column was never loaded.
5. **Column naming.** Loaded as `SYM:NAME`, exactly like CSV indicators today. `NAME` is
   produced by the factory and **embeds every parameter** (`SMA200`, `VOL_EWMA94`,
   `SMA10M`), so two parameterisations of the same indicator coexist and the name is the
   indicator's identity. `NAME` matches `[A-Z0-9_.\-]+` (originally `[A-Z0-9_]+`;
   widened for the ROTATION_SPEC §4.2 multi-horizon names, whose month lists are
   `-`-separated and whose `%g`-rendered weights may carry `.` — errata §11).
6. **Deterministic.** Same file, same code → bit-identical column. No randomness, no
   dependence on today's date.
7. **Symbols must be declared.** A strategy may only attach indicators to symbols it trades
   (`weights`) or reads (`data`). Anything else is an assertion error at load time, with the
   symbol and strategy label in the message.

## 3. Public API — `indicators.py` (new module)

```python
from collections.abc import Callable
from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class Indicator:
    """A named, causal function of one symbol's close series.

    `fn` receives the symbol's own frame with columns `date` (ascending, unique)
    and `close` (Float64, non-null) and returns a Float64 Series of the same
    length, null during warm-up. `name` is the column suffix and the identity:
    two Indicators with the same name are the same indicator.
    """
    name: str
    fn: Callable[[pl.DataFrame], pl.Series]
```

`Indicator` is frozen but wraps a closure, so `sma(3) != sma(3)`: every merge and every
dedup is **by `name`**, never by value or identity.

Factories (all return `Indicator`). Definitions are normative; the implementation may use
Polars expressions or plain Python as long as the tests in §7 pass.

| Factory | `name` | Definition | First non-null row (0-based) |
|---|---|---|---|
| `sma(n)` | `SMA{n}` | arithmetic mean of the last `n` closes incl. today | `n-1` |
| `sma_monthly(m)` | `SMA{m}M` | mean of the last `m` month-end closes (§3.1) | first row on/after the `m`-th month-end |
| `realized_vol(n)` | `VOL{n}` | sample std (ddof=1) of the last `n` log returns × √252 | `n` |
| `ewma_vol(lam=0.94)` | `VOL_EWMA{round(lam*100)}` | RiskMetrics zero-mean EWMA of squared log returns (§3.2), √ and × √252 | `20` |
| `drawdown()` | `DD` | `close / cummax(close) - 1` over the file's whole history (≤ 0) | `0` |
| `momentum(n)` | `MOM{n}` | `close / close.shift(n) - 1` | `n` |
| `mom_monthly(k)` | `MOM{k}M` | `close / close.shift(k) - 1` over month-end closes (§3.1 rule), carried forward (ROTATION_SPEC §4.1) | first row on/after the `k+1`-th month-end |
| `mom_multi(months, weights=None)` | `MOMM{m1}-{m2}…` + `U` \| `W{w1}-{w2}…` | `Σ wᵢ · (close / close.shift(mᵢ) - 1)` over month-end closes; unweighted mean when `weights` is None (ROTATION_SPEC §4.2) | first row on/after the `max(months)+1`-th month-end |
| `sma_gap(m)` | `SMAGAP{m}M` | `close / sma_monthly(m) - 1` at month-ends, carried forward (ROTATION_SPEC §4.3) | first row on/after the `m`-th month-end |

`sma(200)` must reproduce today's `QQQ:SMA200` exactly (this is what keeps the shipped
SMA-gate strategy's results unchanged, §8).

### 3.1 `sma_monthly(m)` — month-end definition

A row is a *month-end* iff its month differs from the next row's month; the last row of the
file is never a month-end (same rule as `is_rebalance_day` in `prices.py`, and for the same
reason: the export ends mid-month). Compute `rolling_mean(m)` over month-end closes only,
then carry each month-end's value forward to the following rows until the next month-end.
Consequences, which the tests pin down:

- on a month-end row the value **includes that row's close** — this is the Faber-style
  10-month rule as evaluated on the rebalance day;
- intra-month rows carry the previous month-end's value;
- null until `m` month-ends have been observed.

Deciding that row *t* is a month-end reads row *t+1*'s **date**, never its close.
That is calendar look-ahead, and it is the same trade `is_rebalance_day` already makes;
the value itself still obeys §2.3, depending only on closes at rows ≤ *t*. The practical
consequence is that `sma_monthly` is truncation-invariant from *t+2* on rather than from
*t+1*, which is why T2 tests it in a separate lane.

### 3.2 `ewma_vol(lam)` — recursion

With `r_t = ln(close_t / close_{t-1})` for `t ≥ 1`:

```
s²_1 = r_1²
s²_t = lam · s²_{t-1} + (1 - lam) · r_t²      (t ≥ 2)
VOL_EWMA_t = sqrt(252 · s²_t)
```

Zero-mean, no bias correction (`adjust=False` in Polars/pandas terms). Report null for the
first 20 rows (rows 0..19) so early estimates that are dominated by the seed are never read
by a strategy. In Polars this is `pl.col("r2").ewm_mean(alpha=1 - lam, adjust=False,
min_samples=20)` (the argument was named `min_periods` before Polars 1.21); the
reference in the tests is a plain loop, and the two agree to 5.6e-17.

Note for strategy authors (not for the indicator): vol-targeting on TQQQ should read QQQ's
vol and multiply by 3, not compute vol on TQQQ.

## 4. Strategy declaration — `strategy.py`

Add one class attribute next to `data`:

```python
class Strategy:
    label: str
    weights: dict[str, float]
    data: tuple[str, ...] = ()                       # symbols read but never traded
    indicators: dict[str, tuple[Indicator, ...]] = {}  # per symbol; symbol must be in weights or data
```

Example — the shipped SMA-gate strategy after migration (hook body unchanged):

```python
class TqqqBtalQqqSma200(Strategy):
    label = "TQQQ/BTAL SMA gate"
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    data = ("QQQ",)
    indicators = {"QQQ": (sma(200),)}

    def allow_buy(self, asset, ctx):
        ...
        sma = ctx.indicator("QQQ", "SMA200")   # unchanged
```

Because `Strategy.__init__` accepts attribute overrides, `TqqqBtalQqqSma200(indicators=
{"QQQ": (sma(150),)})` still fails at runtime with `KeyError` on `"SMA200"` — correct, and
the reason parametrised strategies should build the name from the parameter (`f"SMA{self.n}"`).
That refactor is part of the later declarative-spec work, not this one.

## 5. Loader — `prices.py` and `main.py`

`_read_symbol(data_dir, symbol, indicators=())`:

- keep only `time` and `close` from the CSV (**whitelist**, replacing today's
  drop-`open/high/low` blacklist — this also stops `Volume` from loading as
  `SYM:Volume`, which it does since the fresh dataset);
- rename to `date`, `SYM`; assert `date` is sorted and unique and `close` is non-null;
- for each `Indicator` in `indicators` add column `f"{symbol}:{ind.name}"` =
  `ind.fn(frame.select("date", pl.col(symbol).alias("close")))`;
- return the frame. Everything downstream (full join over traded symbols, left join of
  extras, forward-fill, `start` filter, `is_rebalance_day`) is unchanged, so indicator
  columns forward-fill across calendar gaps exactly as CSV indicators did.

`load_prices(data_dir, symbols, start, extra=(), indicators: Mapping[str, Iterable[Indicator]] = {})`
passes the per-symbol tuple through; the loaded columns must be identical whether the same
indicator was declared by one strategy or by several.

`main.py` merges declarations across the bundle:

```python
indicators: dict[str, dict[str, Indicator]] = {}
for st in strategies:
    for sym, inds in st.indicators.items():
        assert sym in st.weights or sym in st.data, f"{st.label}: indicator on undeclared symbol {sym}"
        indicators.setdefault(sym, {}).update({i.name: i for i in inds})
prices = load_prices(Path("data"), traded, bundle.config.start, extra=extra,
                     indicators={s: tuple(d.values()) for s, d in indicators.items()})
```

Deduplication is by name only (§2.5). Later `--json`/`--spec` work should call the same
merge; keep it as a small function (`collect_indicators(strategies)`) rather than inline
if that is where it ends up being reused.

## 6. Data files and migration

- `data/*.csv` keep TradingView's export layout: `time,open,high,low,close,SMA50,SMA100,
  SMA200,SMA15,Volume`. The loader ignores everything but `time,close`; the `SMA*` columns
  are the reference for test T1 and are documented as such in `data/README.md` (new, one
  paragraph: source, export settings, which columns are reference-only, the Pine script
  that produced them).
- The Pine script that produces the reference columns is in `data/README.md`; source is
  `close`. Pine requires `plot()` titles to be compile-time constants, so the header
  (`TITLE_n`) and the length (`input.int` default) are separate declarations that must be
  edited together — the pairing is a convention the script documents, not something Pine
  enforces. T1 is the backstop: a header that disagrees with its length fails the suite.
- `docs/STRATEGY_DEVELOPMENT.md` §"Data files and indicators" and §"Pitfalls / Look-ahead":
  replace "indicators are precomputed in the CSV" with the declaration form above and the
  rules of §2. Remove the "extra columns become indicators" sentence.
- `docs/ARCHITECTURE.md` (data-flow diagram, the `load_prices` signature, the `SYM:COL`
  and null-policy bullets, and "all indicators arrive precomputed as CSV columns") and
  `README.md` §"Input data" state the same retired contract and need the same treatment.
- **Frozen test dataset.** `tests/data/` holds all six `data/*.csv` files verbatim from
  `4a1b99f` (committed in `77d939c`). It is append-only: never overwrite it, add
  `tests/data/<newdate>/` if a second snapshot is ever needed. Every test that asserts a
  number reads from it via a module constant (`GOLDEN_DIR = Path(__file__).parent /
  "data"`), not from `data/`. No loader change is required — `load_prices` already takes
  `data_dir`.
- Live `data/` continues to move with exports and gets exactly one test: it loads for
  the traded/extra symbols of every bundle in `BUNDLES` and covers each bundle's
  `Config.start`, with no numeric assertions.
- `tests/test_prices.py::test_real_data` and `::test_real_data_with_extra_symbol` are
  currently pinned to the pre-fresh-dataset shape (they fail on `4a1b99f`: 15 extra
  `SYM:*` columns, 2417 rows). Re-point them to `GOLDEN_DIR` and re-pin to the new
  loader (no CSV columns beyond close; expected columns are exactly the declared
  indicators). Two further assertions in the second test are also stale under the fresh
  dataset: QQQ's history now starts 1999-03-10, so it is **not** null on the 2017-01-03
  start date (it is 119.54), and QQQ no longer runs a day past the traded files — every
  file ends 2026-08-14. Correct pins: 2417 rows, last date 2026-08-14, 115 rebalance days
  on or before 2026-07-31.
- Three synthetic loader tests assert that a CSV's `SMA200` column loads as `X:SMA200`
  (`test_extra_symbol_columns_are_namespaced`,
  `test_extra_symbol_is_null_before_its_history_starts`,
  `test_traded_symbol_indicator_is_namespaced_and_may_be_null`). The whitelist ends that
  contract; rewrite all three against declared indicators. `tests/test_simulate.py::
  test_real_data_invariants` asserts numbers against `data/` and moves to `GOLDEN_DIR`
  under the rule above.

## 7. Tests — `tests/test_indicators.py` (new) plus loader tests

**T1 — TradingView parity (the migration's proof).** Parametrised over every CSV in
both `GOLDEN_DIR` and live `data/`, and `n ∈ {15, 50, 100, 200}`: `sma(n)` on the file's
closes equals the file's `SMA{n}` column with `abs diff ≤ 1e-9` and identical null
count. Compares columns within a file, so it is safe on live data. (Measured on
`4a1b99f`: max diff 2e-12 across all 24 columns.)

**T2 — Causality.** For every factory in §3 with default-ish parameters and for at least
QQQ and BTAL, over cut points *t* ∈ {warm-up row, warm-up+1, a mid-history month-end, the
row before a month-end, last row}. This is the look-ahead guard for all future indicators;
new factories must be added to its parameter list. Two lanes:

- **strict** (`sma`, `realized_vol`, `ewma_vol`, `drawdown`, `momentum`): computing on
  `frame[: t+1]` gives the same value at *t* as computing on the full frame.
- **one row of slack** (`sma_monthly`): the same, on `frame[: t+2]`. `frame[: t+1]` would
  hide the month-end flag itself (§3.1) — measured on QQQ at row 3455 (2012-11-30), the
  full frame gives 65.722 and `frame[: t+1]` gives 65.195, the previous month-end carried
  forward. The property that actually matters is asserted separately and strictly:
  multiplying every close *after* row *t* by 1000 leaves the value at *t* unchanged, i.e.
  no price look-ahead.

**T3 — Warm-up.** First non-null index equals the table in §3 for each factory, on a
synthetic strictly-positive random-walk close series of 600 rows.

**T4 — EWMA reference.** On the synthetic series, `ewma_vol(0.94)` matches a plain-Python
loop of §3.2 to `1e-12`, including the null rows.

**T5 — Monthly SMA.** Synthetic daily calendar of 36 months with known month-end closes:
value on a month-end row = mean of that and the previous `m-1` month-end closes; each
intra-month row equals the preceding month-end's value; null before the `m`-th month-end;
the file's final (partial-month) row is not a month-end.

**T6 — Loader.** `load_prices(tmp_path, ["A"], start, extra=("X",), indicators={"X": (sma(3),)})`
yields columns `["date", "A", "X", "X:SMA3", "is_rebalance_day"]`; the indicator forward-fills
across a date X lacks (and that date never enters the window, since the indicator is
computed on X's own calendar); declaring the same indicator twice yields one column
(dedup by name, since `sma(3) != sma(3)`); extra CSV columns (`SMA50`, `Volume`) are not
loaded.

**T7 — Declaration guard.** A strategy with `indicators={"QQQ": ...}` but QQQ in neither
`weights` nor `data` raises `AssertionError` from the merge in `main.py` (test the
`collect_indicators` helper directly).

**T8 — Golden regression.** Running the `default` bundle's strategies and `Config` against
`GOLDEN_DIR` (not `data/`) reproduces the numbers in §8 to the cent — a hard-coded dict
in the test, no fixture machinery. `main.py` grows a `run_bundle(bundle, data_dir)` that
`main()` calls with `Path("data")` and T8 calls with `GOLDEN_DIR`, so the test guards the
production path rather than a copy of it. Add it if it does not already exist as one; it is the
acceptance gate for every future engine-touching change. Because the inputs are frozen,
a T8 failure means the engine changed: fix the bug, or update the dict in the same
commit with the reason in the message. Never "fix" T8 by refreshing the snapshot.

## 8. Golden numbers (`tests/data/2026-08-14/` = `4a1b99f` data, `default` bundle, start 2017-01-03, $10,000 + $500/month)

| Strategy | Final value | CAGR (TWR) | Max DD |
|---|---|---|---|
| TQQQ/BTAL 50/50 | $237,275.03 | +23.66% | −44.97% |
| TQQQ 100% | $661,164.25 | +41.59% | −81.75% |
| TQQQ/BTAL SMA gate | $224,725.33 | +22.69% | −37.73% |
| SPY benchmark | $153,938.16 | +13.70% | −33.97% |

The SMA-gate row is the one that exercises the new path (`QQQ:SMA200` from `sma(200)`
instead of the CSV). Any deviation is a bug in the indicator or the loader, not a
"small numerical difference".

## 9. Acceptance checklist

- [x] `indicators.py` with `Indicator` and the six factories of §3
- [x] `Strategy.indicators` attribute; `TqqqBtalQqqSma200` migrated
- [x] `_read_symbol` whitelist + indicator computation; `load_prices(indicators=...)`
- [x] `main.py` `collect_indicators` merge with undeclared-symbol assertion, and
      `run_bundle(bundle, data_dir)`
- [x] `tests/data/` frozen snapshot (verbatim from `4a1b99f`); all numeric tests read
      `GOLDEN_DIR`; one non-numeric smoke test per bundle on live `data/`
- [x] `tests/test_indicators.py` T1–T5, loader tests T6 in `tests/test_prices.py`,
      T7–T8 in `tests/test_main.py`
- [x] `pytest` green from a fresh `git clone` with `pip install polars matplotlib pytest`
- [x] `docs/STRATEGY_DEVELOPMENT.md`, `docs/ARCHITECTURE.md`, `README.md` updated;
      `data/README.md` written, including the Pine source
- [x] No change to `simulate.py`, `stats.py`, `report.py`

## 10. Deliberately not in scope

Parametrised strategy classes / declarative specs, sweeps, cost model, MCP server. Each
depends on this spec landing first; none should be folded into it. (`--json` output has
since landed — see `results_json.py` and `docs/ARCHITECTURE.md`.)

## 11. Errata (amendments)

1. **Name charset widened to `[A-Z0-9_.\-]+`** (was `[A-Z0-9_]+`; 2026-08-25,
   ROTATION_SPEC §4.2). The multi-horizon momentum names separate month lists
   with `-` (`MOMM1-3-6-12W12-4-2-1`) and render weights with `%g`, which may
   carry `.` (`MOMM1-3W0.5-1`). The convention was documented, never enforced
   in code; names stay lossless and remain the indicator's identity. Earlier
   specs restating the old charset (REGIME_SPEC §3.4) describe the factories
   they introduced, all of which still satisfy it.
2. **The month-end causality lane is a parametrised list** (`MONTHLY_INDICATORS`
   in `tests/test_indicators.py`): every factory built on the §3.1 month-end
   rule joins the T2 one-row-of-slack lane and the strict tamper check, the
   same obligation §7 T2 states for the strict lane. Added with the
   ROTATION_SPEC §4 family.
