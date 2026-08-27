# Specification: VIX/VIX3M term-structure regime gate

Repo: `vlaas/balancing_portfolio` · baseline commit: `184f02b` ("VIX and VIX3M data",
434 tests green) · status: **implemented** (branch `regime-gate`, per-phase commits;
verdict: `notes/regime-verdict.md` — not adopted, SMA-200 stands; errata §15)

## 1. Goal

Add the first *external* regime signal to the machine: the implied-volatility term
structure, read as the cash ratio VIX/VIX3M (`docs/VIX-Term-Structure.md`). Three parts,
in dependency order:

1. **Data** — `data/VIX.csv` and `data/VIX3M.csv` (committed at `184f02b`, TradingView
   exports in the standard layout) become loadable as signal symbols, including on the
   frozen snapshots the decision-grade lanes run on.
2. **Indicator + gate** — a cross-symbol indicator (the first one; today every
   `Indicator` is a function of one symbol's own closes) that computes the smoothed ratio
   and a hysteresis risk-off state, and a second *kind* of `gate` that reads it. The gate
   gains two things the research needs and the SMA gate never had: an optional **weight
   clip while closed** (`w_off`, the research's "full tilt to safe"), and **composition**
   (`gate` may be a list; closed iff any member is closed — the recommended OR with the
   existing trend/vol logic).
3. **Four sweep lanes** answering the two questions asked: is VIX/VIX3M a better risk
   indicator than the incumbent SMA-200 gate, and does stacking the two reduce drawdown
   without giving back CAGR.

Two measured facts, from this sandbox on the committed data, shaped the design and should
be read before the grammar (§11 has the full pilot):

- **At monthly cadence the research's default signal is nearly inert.** With a 10-day
  smoothing, fire at 1.00 and re-risk below 0.95, the regime is risk-off on 13 of the 175
  month-ends from 2012-01 to 2026-07 — 9 of which the SMA-200 gate already closes. It adds
  4 month-ends in fourteen years, and **zero in 2022** (the documented blind spot, now
  measured: the ratio never held ≥ 1.00 across a 2022 month-end at 10-day smoothing). The
  grid must therefore bracket *lower* thresholds (0.95, 0.90) and *shorter* smoothing
  (down to the raw month-end ratio) or it tests four trades.
- **A buy-cap gate cannot cut a fast crash's drawdown at monthly cadence, only an exit
  can.** COVID's portfolio drawdown is −27.2 % at the 2012-lane coordinate for *every*
  cap-only arm, SMA-200 included: the February 2020 month-end was the last look before
  the leg down, and a gate that never sells has nothing to do with holdings already held.
  The one arm that changed COVID was an *exit* on the raw ratio (−7.4 %) — from a single
  reading of 1.011 on 2020-01-31. The exit action is in scope precisely so that this can be
  judged by the robustness machinery (neighbour-min over `fire`, sensitivity windows)
  rather than by one lucky month-end; the pilot says it is dominated everywhere else.

Not in scope (§14): the tradeable VX1/VX2 curve, VIX9D/VIX6M, a VRP signal, the armed
"partial tilt" band, regime-conditional `sigma_target`, daily cadence.

## 2. Data — VIX and VIX3M as signal symbols

### 2.1 What is already true at `184f02b` (measured)

`data/VIX.csv` (1990-01-03 → 2026-08-21, 9,246 rows) and `data/VIX3M.csv` (2007-12-05 →
2026-08-21, 4,671 rows) are ordinary TradingView exports (`time,open,high,low,close,
SMA50,SMA100,SMA200,SMA15,Volume`), so `prices._read_symbol` already loads them as extra
symbols with no change, and T1 SMA parity already runs over both (the suite is green with
them present). They have no `price/` twin: cash indices carry no distributions, and
`make_net_tr.py`/`tests/test_total_return.py` iterate a fixed symbol list, so nothing
breaks. Two calendar facts the indicator must live with:

- **VIX3M's dates are a subset of VIX's.** Every QQQ trading day from 2012-01-03 is in
  both files (0 missing either way). VIX has **58 rows VIX3M lacks**: 36 in 2009 and
  **22 since 2012** — every one a US market holiday (Memorial Day, MLK, Presidents' Day,
  Juneteenth, 4 July, Labor Day, Thanksgiving, 2025-01-09) on which TradingView carries a
  VIX value and no VIX3M value. None of the 22 is on QQQ's calendar. They are not real
  observations and must not enter a rolling window.
- **Ratio distribution, 2012-01-03 → 2026-08-21** (3,680 joint days): median 0.890, min
  0.710, max 1.431; ≥ 0.90 on 39.5 % of days, ≥ 0.95 on 18.1 %, ≥ 1.00 on 6.8 %, ≥ 1.05 on
  2.5 %, ≥ 1.10 on 1.5 %. The 6.8 % matches the research note's "~7.7 % of days since
  2009/10" well enough to trust the export.

### 2.2 Frozen snapshots — additive

- Copy `data/VIX.csv` and `data/VIX3M.csv` **verbatim** (as at `184f02b`) into
  `tests/data/2026-08-20/`. This adds two files and changes no byte of any existing one, so
  every number pinned on that snapshot stands; the snapshot README gains one paragraph
  (index series, no `price/` twin, the holiday-row fact above, last bar 2026-08-21 — one
  day past TQQQ's, harmless because extras never extend the traded calendar, exactly as
  DBMF/KMLM already run past it).
- `make_net_tr.py` gains a **pass-through rule**: a `<SYM>.csv` under the parent with no
  `price/<SYM>.csv` twin is an index series with no distributions — it is byte-copied into
  the net snapshot, and the README table lists it as `| VIX | index | — | — |`. Nothing
  else in the generator changes; the six ETF files it already produces are bit-identical
  before and after (guarded by N5 regenerating and comparing).
- Regenerate `tests/data/2026-08-20-net15/` with the generator (never by hand). The
  diff must be exactly: `VIX.csv`, `VIX3M.csv` added; `README.md` gains two table rows;
  nothing else. N5's file count becomes 15.
- The flat `tests/data/*.csv` price snapshot is **not** touched — no regime lane runs
  there.

## 3. Indicators — `indicators.py`, `prices.py`, `main.py`

### 3.1 `Indicator.inputs` — cross-symbol indicators

```python
@dataclass(frozen=True)
class Indicator:
    name: str
    fn: Callable[[pl.DataFrame], pl.Series]
    inputs: tuple[str, ...] = ()   # other symbols fn reads, by column name
```

When `inputs` is empty nothing changes (every existing factory, every existing test).
When it is not, `fn` receives a frame with columns `date`, `close` **and one column per
input symbol**, on the **intersection** of the host's and every input's calendars, and
returns a Series of that frame's length. The loader then carries the result back onto the
host's own rows by date; host rows outside the intersection get null. Consequences, all
tested (§7):

- the rolling windows of a cross-symbol indicator count only joint trading days — the 22
  VIX holiday rows never enter a window and never yield a value;
- INDICATORS_SPEC §2 holds unchanged: close-only, computed before the join onto the traded
  calendar, causal (truncating the *joined* frame at *t* leaves row *t* unchanged), null
  during warm-up, deterministic, named with every parameter embedded;
- the `name` stays the identity; two declarations with equal names dedupe as today.

### 3.2 Loader — `prices._read_symbol`

Factor the CSV read into `_read_close(data_dir, symbol) -> DataFrame[date, close]` (the
existing whitelist, rename, sorted/unique/non-null asserts). For each unique indicator of
the host: if `inputs` is empty, today's path; else

```python
joined = own
for sym in indicator.inputs:
    joined = joined.join(_read_close(data_dir, sym).rename({"close": sym}), on="date", how="inner")
assert len(joined) > 0, f"{symbol}:{indicator.name}: empty intersection with {indicator.inputs}"
column = f"{symbol}:{indicator.name}"
values = joined.select("date", indicator.fn(joined).alias(column))
frame = frame.join(values, on="date", how="left")   # null on host rows outside the intersection
```

`load_prices` is unchanged in signature and in everything downstream (full join over traded
symbols, left join of extras, forward-fill, `start`/`end`, `is_rebalance_day`). A host row
with a null indicator value is forward-filled on the traded calendar like any indicator
column — and in the shipped data that situation never arises, because the only host rows
outside the intersection are holiday rows absent from every traded calendar (pinned, R4).

### 3.3 Declaration rule — `main.collect_indicators`

INDICATORS_SPEC §2.7 extends to inputs: a strategy may attach a cross-symbol indicator only
if the host **and every input** are among the symbols it trades (`weights`) or reads
(`data`). Assertion message names the strategy, the host, the input. The `Gate` (§4) puts
both symbols in `symbols`, and `Fixed`/`VolTarget` derive `data` from it, so a spec author
never declares anything by hand.

### 3.4 Factories

| Factory | `name` | Definition | First non-null row of the intersection |
|---|---|---|---|
| `ratio_sma(denominator, n)` | `RATIO_{denominator}_SMA{n}` | `(close / denominator).rolling_mean(n)` | `n − 1` |
| `ts_regime(denominator, n, fire, hysteresis=0.0)` | `REGIME_{denominator}_{n}_{round(fire·100)}_{round(hysteresis·100)}` | §3.5 | `n − 1` |

`n ≥ 1` (`n = 1` is the raw ratio). `fire` and `hysteresis` must be non-negative multiples
of 0.01 with `hysteresis < fire` — asserted, so the name embeds them losslessly (the λ
two-digit rounding of SWEEP_SPEC errata 6 is a collision we do not repeat). `NAME` still
matches `[A-Z0-9_]+`. Examples: `VIX:RATIO_VIX3M_SMA10`, `VIX:REGIME_VIX3M_10_100_5`,
`VIX:REGIME_VIX3M_1_100_0`.

### 3.5 `ts_regime` — the state machine (normative)

With `s_t` the smoothed ratio of §3.4 (null for the first `n − 1` joint rows):

```
off_t = null                                  while s_t is null (warm-up)
off_t = False                                 on the first non-null s_t unless s_t ≥ fire
off_t = True   if not off_{t-1} and s_t ≥ fire
off_t = False  if     off_{t-1} and s_t <  fire − hysteresis
off_t = off_{t-1}  otherwise
REGIME_t = 1.0 if off_t else 0.0              (Float64, like every indicator column)
```

A plain Python loop over the Series is the implementation *and* the test reference; the
column is never null after warm-up. With `hysteresis = 0` the machine collapses exactly to
`s_t ≥ fire` (tested): the research's dual-threshold scheme and a single threshold are one
factory, and the sweep grids the difference. The machine runs **daily**, on the signal's
own calendar; a strategy reads it on its rebalance days only, so a spike that fires and
releases inside a month is invisible by design, while a spike that fires and is still
above `fire − hysteresis` at month-end is not — which is the whole point of the hysteresis
at this cadence.

The research's third state (armed, `fire − hysteresis ≤ s < fire` before firing) has no
action in this spec and is not represented; §14.

## 4. Gate — `strategies/gate.py`, `strategies/fixed.py`, `strategies/vol_target.py`

### 4.1 Two kinds, one class

`Gate` keeps its public surface (`symbol`, `assets`, `contribution_exempt`, `indicators`,
`closed(ctx)`, `buy_cap(asset, ctx, weights)`) and gains:

| attribute | sma kind | regime kind |
|---|---|---|
| `indicator` | `sma(n)` / `sma_monthly(m)` on `symbol` | `ts_regime(denominator, ratio_sma, fire, hysteresis)` on `symbol` with `inputs=(denominator,)` |
| `symbols` | `(symbol,)` | `(symbol, denominator)` |
| `closed(ctx)` | `close < SMA` | `ctx.indicator(symbol, name) == 1.0` |
| open when | either value `None` | value `None` |
| `w_off` | optional | optional |

Constructor: `Gate(symbol, assets, sma_days=None, sma_months=None, denominator=None,
ratio_sma=None, fire=None, hysteresis=0.0, contribution_exempt=False, w_off=None)`;
exactly one of `sma_days` / `sma_months` / `fire`; `denominator` and `ratio_sma` required
with `fire` and forbidden without; `0 ≤ w_off ≤ 1` when given. `symbol` and `denominator`
distinct.

### 4.2 `w_off` — the weight clip while closed

`Gate.clip(weights, ctx) -> dict`: returns `weights` unchanged when open or when `w_off` is
`None`. When closed with `w_off` set, for every asset in `assets` whose weight exceeds
`w_off`: set it to `w_off` and move the excess to the assets **not** in `assets`, pro rata to
their current weights; if those weights sum to zero the excess is left unallocated (cash —
the `safe: null` arm and `TQQQ100` tilt to cash, as they should). Never raises a weight
of a gated asset, never changes the key set, preserves `sum ≤ 1`.

`w_off = 0` is the research's "full tilt to safe": a closed gate then **sells** the asset
down to zero on a rebalance day and the sleeve absorbs it in sleeve proportion. Absent
`w_off` is today's gate exactly: holdings untouched, buys capped. Intermediate values are
partial tilts. The buy cap of §4.1 applies in every case (a closed gate still returns
`0.0` / the exempt cap for its assets), so on a contribution-only day (REBALANCE_SPEC §2.2)
a closed `w_off` gate behaves as today's gate — the clip lowers a *target* and a
contribution-only day never sells.

Where it is applied — the only two strategy-side changes:

- `Fixed.balance(ctx)`: `return self.gate.clip(self.weights, ctx) if self.gate else self.weights`
  (today the base `Strategy.balance` returns `self.weights`).
- `VolTarget.balance(ctx)`: the VT allocation, then `self.gate.clip(...)` when a gate is set.
  `buy_cap` keeps calling `self.balance(ctx)`, so a contribution-exempt cap multiplies the
  *clipped* weight.

Engine invariance: with no `w_off` anywhere, `balance()` returns exactly what it returns
today; `simulate.py` and `strategy.py` are **not touched**; T8 and every committed
artefact reproduce.

### 4.3 Composition — `AnyGate`

`AnyGate(members: tuple[Gate, ...])`, ≥ 2 members, same duck-typed surface as `Gate`:

- `symbols` = union in member order; `indicators` = merge (dedup by name, as
  `collect_indicators` does);
- `closed(ctx)` = any member closed;
- `buy_cap(asset, ctx, weights)` = the **minimum** over members' non-`None` caps (`None` if
  all are `None`) — the most restrictive member wins, so `cap_buys` ∨ `contribution_exempt`
  resolves to the cap;
- `clip(weights, ctx)` = members' clips applied in order (each only lowers gated assets, so
  order cannot matter for the result beyond float rounding; tested on a 2-member case).

`Fixed`/`VolTarget` accept `gate: Gate | AnyGate | None`; their `data` derives from
`gate.symbols` (today `gate.symbol`). `VolTarget` adds `gate.indicators` into its own dict
as today, merging on the host symbol.

## 5. Grammar — `spec.py`, `sweep.py`

### 5.1 `gate` object

| Key | Type | Default | Kind | Meaning |
|---|---|---|---|---|
| `symbol` | str | required | both | host symbol (`QQQ`, `VIX`) |
| `assets` | list[str] | required | both | as today |
| `sma_days` / `sma_months` | int | — | sma | as today |
| `denominator` | str | required with `fire` | regime | `VIX3M` |
| `ratio_sma` | int ≥ 1 | required with `fire` | regime | smoothing window; `1` = raw ratio |
| `fire` | float | — | regime | close when smoothed ratio ≥ `fire` |
| `hysteresis` | float ≥ 0 | `0.0` | regime | reopen only below `fire − hysteresis` |
| `contribution_exempt` | bool | `false` | both | as today |
| `w_off` | float in [0, 1] | absent | both | clip the assets' target weight to this while closed (§4.2) |

Exactly one of `sma_days` / `sma_months` / `fire`; regime-only keys with an sma kind (or the
reverse) → `ValueError` naming the path; `fire`, `hysteresis` multiples of 0.01 and
`hysteresis < fire`; `denominator == symbol` → error; `assets` ⊆ strategy universe as
today. Integer-valued JSON numbers (`0`, `1`) are accepted where floats are expected,
booleans are not.

**Composite:** `gate` may be a **list of ≥ 2 gate objects**; no nesting; paths read
`strategies[0].gate[1].fire`. A one-element list is an error ("use the object form").

Normalised spec (what `results.json` embeds): per kind, the keys given plus filled
defaults — `hysteresis` always present on a regime gate, `w_off` present only when given;
a composite normalises to a list in member order.

### 5.2 Rendering — `gate_str`, shared by labels and sweep `params`

```
sma:        QQQ<SMA200                 (+contrib)        ( off{pct})
regime:     VIX/VIX3M@10>=1.00         (+contrib)        ( off{pct})
            VIX/VIX3M@10>=1.00<0.95    when hysteresis > 0  ("closes at ≥ 1.00, reopens below 0.95")
composite:  members joined by "|"      QQQ<SMA200|VIX/VIX3M@1>=1.00 off0
```

Thresholds render with two decimals; `off{pct}` uses `spec._pct` (`off0`, `off30`). Every
grid-visible parameter is in the rendering, so auto-labels stay unique by construction
(SWEEP_SPEC errata 6); `build_bundle`'s slug-collision assertion remains the backstop.
Label examples: `VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate VIX/VIX3M@10>=1.00<0.95`,
`TQQQ50/BTAL50 gate QQQ<SMA200 off0`.

### 5.3 Sweeps

No runner change. `_param_value` already renders the whole `gate` through `gate_str`, and
that now covers composites. Grids **inside** a regime gate object (`gate.ratio_sma`,
`gate.fire`, `gate.hysteresis`, `gate.w_off`) work as nested leaves today do: numeric lists
get neighbourhoods and edge flags; `gate.w_off: {"grid": [null, 0.3, 0]}` is categorical
(the `null` deletes the key per the optional-key rule, SWEEP_SPEC errata 3). Grids inside
a composite *list* remain unsupported (errata 4) — a composite is gridded as a whole
object.

## 6. `regime_report.py` — the signal's own calendar

A small read-only CLI, the research note's "validate once" step made repeatable:

```
uv run regime_report.py --data DIR [--symbol VIX --denominator VIX3M] --ratio-sma N --fire F
    [--hysteresis H] [--start 2012-01-03] [--end YYYY-MM-DD] [--sma-symbol QQQ --sma-days 200]
```

Loads nothing through the engine: reads the three CSVs with `prices._read_close`, builds
the intersection ratio and `ts_regime` through the same factories the gate uses (so the
report cannot drift from the signal), and prints markdown to stdout, deterministic:

1. data ranges, intersection row count, host-only rows in the window and how many of them
   fall on the SMA symbol's calendar (must be 0 for the shipped data);
2. trading days risk-off (count, %), episodes (count, mean length in days);
3. month-ends in the window (the SMA symbol's calendar), month-ends risk-off, **per
   calendar year**;
4. contingency with the SMA gate on month-ends: both / SMA only / regime only / neither,
   plus the same four for calendar 2022 — the research's falsification line ("stayed
   > 90 % risk-on through 2022").

~80 lines; one test pins its numbers (R4). It is the first step of the read protocol (§10)
and the tool for any later signal (VIX9D/VIX, VRP).

## 7. Tests — `tests/test_indicators.py`, `test_prices.py`, `test_gate.py`, `test_spec.py`, `test_sweep.py`, `test_net_tr.py`, new `tests/test_regime.py`

Cite as "REGIME_SPEC R·" in test comments.

**R1 — Cross-symbol loader.** Synthetic host `A` and input `B` on overlapping calendars with
rows each lacks: the column `A:RATIO_B_SMA1` equals `A/B` on the intersection, is null on
A-only dates, and B-only dates never appear; `A:RATIO_B_SMA3` at an A-row counts only joint
days (a B-only day between two joint days does not enter the window); missing input CSV →
`FileNotFoundError` naming the input; disjoint calendars → the §3.2 assertion; an indicator
without inputs is unaffected (frame-equal to `184f02b`'s loader on `tests/data`).

**R2 — Factories.** `ratio_sma(den, n).fn(joined)` equals `sma(n).fn` applied to the ratio
to 1e-12, `n = 1` equals the raw ratio; `ts_regime` on a synthetic ratio path that exercises
every transition (below band → armed without firing → fire → linger inside the band → release
→ immediate re-fire) matches the §3.5 loop; `hysteresis = 0` equals `s ≥ fire` row for row;
warm-up: first non-null index `n − 1` for both; names as §3.4; `fire = 0.955` → assertion
(not a multiple of 0.01); `hysteresis ≥ fire` → assertion.

**R3 — Causality.** Add `ratio_sma("B", 10)` and `ts_regime("B", 10, 1.0, 0.05)` to the
T2 strict lane, run on the *joined* frame (the property is "truncating every input and the
host after row *t* leaves row *t* unchanged"); also the price-look-ahead form: multiplying
every `close` and every input after *t* by 1000 changes nothing at *t*.

**R4 — Real-data pins** (VIX/VIX3M from `tests/data/2026-08-20/`, QQQ from
`tests/data/2026-08-20-net15/`, via `regime_report.py`'s functions):

- VIX 1990-01-03 → 2026-08-21; VIX3M 2007-12-05 → 2026-08-21; VIX3M ⊆ VIX; intersection
  4,671 rows; host-only rows from 2012-01-03: **22**, on QQQ's calendar: **0**.
- Window 2012-01-03 → 2026-08-20, 3,679 joint days, 175 month-ends (last 2026-07-31);
  `QQQ<SMA200` closed on **27** month-ends, 12 of them in 2022 (the gross root gives 25 —
  the two extra 2012 closes are the net series' rescaling; pin the net value, note the gross):

| signal | days off | month-ends off | both | SMA only | regime only | 2022 month-ends off |
|---|---|---|---|---|---|---|
| `@1>=1.00` | 249 (6.8 %) | 13 | 7 | 20 | 6 | 2 |
| `@10>=1.00<0.95` | 305 (8.3 %) | 13 | 9 | 18 | 4 | **0** |
| `@10>=0.95<0.90` | 964 (26.2 %) | 44 | 20 | 7 | 24 | 7 |

- Spot values (raw ratio / 10-day SMA): 2020-01-31 **1.011** / 0.920; 2020-02-28 1.344 /
  1.074; 2022-02-28 1.017 / 0.974; 2022-04-29 1.006 / 0.926; 2025-03-31 1.014 / 0.952.

**R5 — Gate semantics** (`test_gate.py`, stub `MarketDay`). Regime gate closed iff the
column is `1.0`, open on `None` and `0.0`; `symbols` and `indicators` for both kinds
(`inputs == (denominator,)`); `clip`: open → same dict object; closed `w_off = 0` on
`{TQQQ: .5, BTAL: .5}` → `{TQQQ: 0, BTAL: 1}`; `w_off = 0.2` → `{0.2, 0.8}`; three-asset
sleeve keeps sleeve proportion; `safe: null` leaves the excess in cash (sum drops);
`w_off` above the current weight changes nothing; `buy_cap` unchanged by `w_off`.
Composite: closed iff any; `buy_cap` is the minimum (`0.0` beats an exempt cap beats
`None`); `symbols` union; `indicators` merged with a duplicate name collapsed; one-member
composite rejected.

**R6 — Engine effect** (`test_simulate.py`, synthetic two-asset prices). A closed
`w_off = 0` gate on a rebalance day **sells** the asset to zero and the proceeds buy the
other asset (compare trades to a `Fixed({B: 1})` run: same buys, plus the sell); the same
gate without `w_off` leaves holdings untouched (frame-equal to today's `allow_buy → False`
path); on a contribution-only day (a 2-month cadence strategy, REBALANCE_SPEC) a closed
`w_off = 0` gate never sells.

**R7 — Grammar** (`test_spec.py`). Each of: `fire` with `sma_days`; `denominator` without
`fire`; `fire` without `ratio_sma`; `ratio_sma: 0`; `hysteresis: 1.0` with `fire: 1.0`;
`fire: 0.955`; `w_off: 1.5`; `w_off: true`; `denominator == symbol`; one-element list;
nested list; unknown key inside `gate[1]` — raises `ValueError` whose message contains the
JSON path. Valid forms build; normalised spec as §5.1; the five label renderings of §5.2
exactly; `results.json` round-trips a composite.

**R8 — Sweep** (`test_sweep.py`). A template with `gate: {"grid": [null, <sma>, <regime>,
[<sma>, <regime>]]}` expands to 4 entries with `params.gate` = `[null, "QQQ<SMA200",
"VIX/VIX3M@1>=1.00", "QQQ<SMA200|VIX/VIX3M@1>=1.00"]`; a template with nested grids
`gate.ratio_sma`, `gate.fire`, `gate.w_off: [null, 0]` expands to the product, `fire` is
numeric with neighbours and edges, `w_off` is categorical; `--dry-run` counts on
`specs/sweep_regime_tune_2012.json` print 144 × 23.

**R9 — Snapshot and generator** (`test_net_tr.py`). N5 regenerates 15 files byte-for-byte;
the six ETF net files are unchanged from `184f02b`, pinned by SHA-256 (measured at
`184f02b`):

| file | sha256 |
|---|---|
| `BTAL.csv` | `93d1752638d2f8de4349a953bfbecc2a275758a681427f597d9c13d574669fbf` |
| `DBMF.csv` | `7af62a046680a9b7072f1d0848ab92010afa4d4e51f2be93949eca4360bd775c` |
| `KMLM.csv` | `c63907b899fc3e7ead79a10e030c3e3d229d8f475bc9b49d1f5d74eece80c0c8` |
| `QQQ.csv` | `c9afaffa020c6ea195d2ebdeec4c2b339555c4871f75dc6e2e114668bb8236af` |
| `SPY.csv` | `c885eedcbcdc3529a14de5e04684af9acb6ca798e58c56881a33f85bdfec4357` |
| `TQQQ.csv` | `398911f0c9148318d71902cd467aa3a406c30c1be48ea022f39d9a3ededdf47f` |

`VIX.csv` and `VIX3M.csv` in the net root are byte-equal to the parent's; a synthetic
parent with one paired and one unpaired symbol nets the first and copies the second, and
its README lists the second as an index row.

**R10 — Goldens untouched.** The whole suite; and the 2012-lane anchor reproduced through
the new code path: `VT TQQQ/BTAL t30 w0-60 λ0.80 gate QQQ<SMA200` on
`tests/data/2026-08-20-net15`, 2012-01-03 → 2026-08-20, the blend cost map, `cash_yield`
0.03 → full Calmar **0.86254363**, CAGR 0.2385326, max drawdown −0.27654555 (from
`results/sweep_safe_2012/runs.csv`, window `full`); the no-gate twin 0.71731262 /
0.2479853 / −0.3457144. A run with `VIX` and `VIX3M` declared but the gate open on every
rebalance day (`fire: 2.0`) equals the no-gate twin frame for frame.

## 8. Sweep specs

All four on `tests/data/2026-08-20-net15` (with the §2.2 index files), the blend cost map
(`TQQQ 1.5 / BTAL 6 / DBMF 2.5 / KMLM 6 / QQQ 1 / SPY 0.7 / * 6` bp per side), `cash_yield`
0.03, objective Calmar, constraint max drawdown ≥ −50 %. Windows are copied from the lane
each one extends, so the `null`/SMA-200 arms reproduce committed numbers to the third
decimal and the new arms are read against them.

### 8.1 Named gate objects (used verbatim below)

```
G_sma      {"symbol":"QQQ","assets":["TQQQ"],"sma_days":200}
G_sma0     G_sma + "w_off":0
G_r1       {"symbol":"VIX","denominator":"VIX3M","assets":["TQQQ"],"ratio_sma":1, "fire":1.00}
G_r1_0     G_r1 + "w_off":0
G_r10      {"symbol":"VIX","denominator":"VIX3M","assets":["TQQQ"],"ratio_sma":10,"fire":1.00,"hysteresis":0.05}
G_r10_0    G_r10 + "w_off":0
G_r10lo    {"symbol":"VIX","denominator":"VIX3M","assets":["TQQQ"],"ratio_sma":10,"fire":0.95,"hysteresis":0.05}
OR_x       [G_sma, G_x]   for x ∈ {r1, r1_0, r10, r10_0, r10lo}
```

`G_r10` is the research note's default; `G_r1` is the raw month-end read (the pilot's one
COVID call); `G_r10lo` is the setting with 2022 coverage (7 month-ends) at the cost of
being closed a quarter of all days.

### 8.2 `specs/sweep_regime_tune_2012.json` — the signal's parameter surface (144 points)

Windows as `sweep_safe_2012` (start 2012-01-03, holdout 2023-01-01, sensitivity 6 m / 5 y,
20 windows). Template: the 2012 lane's robust leader, gate parameters gridded inside the
gate object:

```json
"template": {
  "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
  "vol": { "kind": "ewma", "lam": 0.80 }, "leverage": 3, "sigma_target": 0.30, "w_max": 0.6,
  "gate": {
    "symbol": "VIX", "denominator": "VIX3M", "assets": ["TQQQ"],
    "ratio_sma":  { "grid": [1, 5, 10, 20] },
    "fire":       { "grid": [0.90, 0.95, 1.00, 1.05] },
    "hysteresis": { "grid": [0, 0.05, 0.10] },
    "w_off":      { "grid": [null, 0.3, 0] }
  }
}
```

Baselines: the same VT with no gate, with `G_sma`, with `G_sma0`; plain 50/50; gated 50/50;
SPY. Three numeric dimensions give every point a neighbourhood; `fire` ∈ {0.90, 1.05} and
`ratio_sma` ∈ {1, 20} are the edges on purpose — 0.90/0.10 is closed 84 % of days and
brackets the plateau from below, 1.05 tests whether any 1.00 result survives a threshold
nudge. Runtime ≈ 3,300 simulations, ~6 min single-process.

### 8.3 `specs/sweep_regime_2012.json` — head-to-head and combination (13 points)

Same windows and template, `gate` as one **categorical** grid:
`[null, G_sma, G_sma0, G_r1, G_r1_0, G_r10, G_r10_0, G_r10lo, OR_r1, OR_r1_0, OR_r10, OR_r10_0, OR_r10lo]`.
Baselines: 50/50, gated 50/50, SPY. Pure categorical → `robust_score = min(full, sensitivity
median, holdout test)` for every arm alike, the comparison the questions need; its absolute
level is not poolable with §8.2 (numeric neighbours re-enter there — REBALANCE_SPEC §3).

### 8.4 `specs/sweep_regime_2021.json` — the three winners (21 points)

Windows as `sweep_blend_2021` (start 2020-12-18, holdout 2025-01-01, sensitivity 6 m / 3 y).
Template: `safe` ∈ {B75K25, B75D25, B50K50} × `gate` ∈ `[null, G_sma, G_r1, OR_r1, OR_r1_0,
OR_r10, OR_r10lo]`, at the winners' coordinate (λ 0.80, σ 0.20, w_max 0.8). Baselines as
the blend lane (plain and gated 50/50, SPY).

### 8.5 `specs/sweep_regime_2019.json` — the COVID check (14 points)

Windows as `sweep_blend_2019` (start 2019-05-08, holdout 2024-01-01, sensitivity 6 m / 3 y).
`safe` ∈ {BTAL, B75D25} × the same seven gates. The `sens_2019-05-08` window's max
drawdown per arm is the one number the exit arms exist to change.

### 8.6 `specs/regime_confirm_2012.json` — the drawdown panel

An ordinary bundle (not a sweep) of the 13 arms of §8.3 plus SPY, full window, same costs,
run with `--json results/regime_confirm_2012.json --no-charts --quiet`. Its `drawdowns`
blocks supply the per-episode table the read protocol needs (2015-08, 2018-Q4, COVID,
2022, 2025) — `runs.csv` carries only a window's *max* drawdown.

## 9. Run protocol

```
uv run make_net_tr.py tests/data/2026-08-20 --out tests/data/2026-08-20-net15   # after §2.2; diff must be the two files + README rows
uv run pytest
uv run regime_report.py --data tests/data/2026-08-20-net15 --ratio-sma 10 --fire 1.00 --hysteresis 0.05 > results/regime_report_r10.md
uv run regime_report.py --data tests/data/2026-08-20-net15 --ratio-sma 1  --fire 1.00                    > results/regime_report_r1.md
uv run regime_report.py --data tests/data/2026-08-20-net15 --ratio-sma 10 --fire 0.95 --hysteresis 0.05 > results/regime_report_r10lo.md
uv run sweep.py specs/sweep_regime_tune_2012.json --data tests/data/2026-08-20-net15 --out results/sweep_regime_tune_2012
uv run sweep.py specs/sweep_regime_2012.json      --data tests/data/2026-08-20-net15 --out results/sweep_regime_2012
uv run sweep.py specs/sweep_regime_2021.json      --data tests/data/2026-08-20-net15 --out results/sweep_regime_2021
uv run sweep.py specs/sweep_regime_2019.json      --data tests/data/2026-08-20-net15 --out results/sweep_regime_2019
uv run main.py --spec specs/regime_confirm_2012.json --data tests/data/2026-08-20-net15 --json results/regime_confirm_2012.json --no-charts --quiet
```

Commit specs with their artefacts (CLAUDE.md §6). Before reading anything else, confirm the
anchors: §8.3's `null` arm and `G_sma` arm reproduce `results/sweep_safe_2012`'s
0.717 / 0.863 full Calmar; §8.4's `G_sma` arms reproduce 0.856 / 0.859 / 0.890; §8.5's
B75D25 `G_sma` arm reproduces 0.937. A mismatch is a bug in this change, not "data drift".

## 10. Read protocol

0. **The signal's calendar first.** The three `regime_report` files. A setting that is
   risk-off on fewer than ~5 % of month-ends (≈ 9 of 175) cannot be separated from the
   no-gate baseline by Calmar; report such an arm as **inert**, never as "neutral" or
   "harmless". Quote the 2022 line of each: at `G_r10` it is 0 of 12 — the research's
   falsification criterion is met on day one, which settles that the OR-form is the only
   form in which the research default can matter.
1. **Q1 — better indicator than SMA-200?** From §8.3: `G_r1`, `G_r10`, `G_r10lo` against
   `G_sma` on `robust_score`, `rank_worst` and the holdout `test` objective. "Better" needs
   all three; a `robust_score` within ±0.02 with a worse `rank_worst` is "**a substitute,
   not an improvement**". Cross-check direction on §8.4 (any two of three winners) and
   §8.5 (both arms).
2. **Q2 — does stacking help?** `OR_x` against `G_sma`, per lane: Δ`robust_score`,
   Δ full max drawdown, Δ CAGR, Δ holdout test, and the minimum over sensitivity windows
   of max drawdown. The bar the question sets: **drawdown shallower by ≥ 1 pp with CAGR
   within −0.5 pp and holdout test not worse**. Then the per-episode panel from §8.6 — the
   fast crashes (COVID, 2025) are where a term-structure gate is supposed to pay; 2022 is
   where it is known not to. Report each arm's five episode drawdowns next to `G_sma`'s.
3. **The exit arms on their own line.** `w_off = 0` changes turnover and drawdown together;
   quote both, plus 2020's and 2025's calendar-year returns from the confirm bundle's
   `yearly_returns`. The pilot (§11) predicts they are dominated; if one survives, check
   whether its edge is a single month-end (2020-01-31 at `fire` 1.00) by reading its
   `fire = 1.05` neighbour in §8.2 — a result that disappears one grid step away is luck.
4. **The surface, §8.2.** Is there a plateau anywhere in (`ratio_sma`, `fire`,
   `hysteresis`) where `neighbour_min` is close to `full`? Where do the edge flags sit?
   The research's tuning advice (5 vs 10 day, 0.95 arming) is read here.
5. **Whipsaw.** Episodes per year from the reports and turnover from the runs: the
   research's own stop rule is "more than ~2–3 allocation flips a year → widen the band or
   lengthen the smoothing"; at monthly cadence count month-end state changes.
6. **Decision rule.** A gate change is adopted into WINNING_STRATEGIES.md only if it clears
   step 2's bar on §8.3 **and** improves at least two of the three winners in §8.4 **and**
   does not worsen B75D25 in §8.5. Otherwise the verdict is written up and the SMA-200 gate
   stands, with the regime machinery retained as a tested, inert option — which is a
   legitimate outcome of a research line, not a failed one.

## 11. Pilot measurements — what to expect, and what would falsify it

A throwaway harness in this sandbox (regime column computed outside the loader and joined
onto the prices frame; a `VolTarget` subclass with the §4 semantics; full windows only,
**no** robustness windows, **no** ranks) on `2026-08-20-net15` + the index files, base
costs, `cash_yield` 0.03. The harness reproduces the committed anchors to five decimals
(0.71731 / 0.86254 at the 2012 coordinate), so the numbers are comparable to the lanes'
`full` column — and to nothing else. They are expectations to be replaced by the
artefacts, not findings.

**2012 lane, VT t30 / w0.6 / λ0.80 / BTAL, full window** (Calmar · CAGR · max DD · avg
TQQQ weight · turnover):

| arm | cap only | with `w_off = 0` |
|---|---|---|
| no gate | 0.717 · 24.8 % · −34.6 % · 0.526 · 0.98 | — |
| `G_sma` | **0.863** · 23.9 % · −27.7 % · 0.511 · 0.89 | 0.555 · 20.1 % · −36.1 % · 0.472 · 1.24 |
| `G_r1` | 0.710 · 24.8 % · −34.9 % · 0.525 · 0.95 | 0.601 · 21.8 % · −36.3 % · 0.500 · 1.47 |
| `G_r10` | 0.700 · 24.2 % · −34.6 % · 0.523 · 0.98 | 0.613 · 22.3 % · −36.3 % · 0.503 · 1.24 |
| `G_r10lo` | 0.600 · 21.9 % · −36.6 % · 0.512 · 0.88 | 0.208 · 7.8 % · −37.5 % · 0.423 · 2.24 |
| `@10>=0.90` | 0.664 · 21.7 % · −32.8 % · 0.502 · 0.84 | 0.152 · 6.3 % · −41.3 % · 0.352 · 2.80 |
| `OR_r1` | 0.862 · 23.8 % · −27.7 % · 0.511 · 0.89 | 0.585 · 21.3 % · −36.3 % · 0.473 · 1.35 |
| `OR_r10` | 0.858 · 23.7 % · −27.7 % · 0.510 · 0.89 | 0.584 · 21.2 % · −36.3 % · 0.489 · 1.15 |
| `OR_r10lo` | 0.804 · 22.2 % · −27.6 % · 0.504 · 0.85 | 0.257 · 9.7 % · −37.7 % · 0.413 · 2.13 |

Per-episode portfolio drawdowns at the same coordinate (2015-08 · 2018-Q4 · COVID · 2022 ·
2025):

| arm | episodes | 2020 / 2022 / 2025 calendar returns |
|---|---|---|
| no gate | −20.6 · −25.8 · −27.2 · −34.6 · −24.5 | +27.7 / −30.5 / +13.2 |
| `G_sma` | −21.9 · −21.1 · −27.2 · −27.7 · −22.0 | +27.7 / −21.8 / +13.3 |
| `G_r10` cap | −21.9 · −21.1 · −27.2 · −34.6 · −24.5 | +26.0 / −30.5 / +13.2 |
| `OR_r10` cap | −21.9 · −21.1 · −27.2 · −27.7 · −22.0 | +26.0 / −21.8 / +13.3 |
| `G_r1` exit | −20.6 · −25.2 · **−7.4** · −34.9 · −22.5 | +25.5 / −30.7 / +13.9 |
| `OR_r1` exit | −27.1 · −18.2 · **−7.4** · −21.8 · −27.9 | +25.5 / −4.0 / +2.5 |
| `G_r10` exit | −27.1 · −18.2 · −21.0 · −34.8 · −24.5 | +7.3 / −30.5 / +1.8 |

**Winners' coordinate (t20 / w0.8 / λ0.80), full windows** (Calmar · CAGR · max DD):

| lane · sleeve | no gate | `G_sma` | `G_r1` cap | `OR_r1` cap | `OR_r1` exit | `G_r10lo` cap |
|---|---|---|---|---|---|---|
| 2021 · B75D25 | 0.814 · 16.4 · −20.1 | **0.859** · 16.4 · −19.1 | 0.857 · 16.3 · −19.1 | 0.858 · 16.4 · −19.1 | 0.653 · 16.0 · −24.4 | 0.778 · 15.7 · −20.1 |
| 2019 · B75D25 | 0.941 · 18.9 · −20.1 | 0.937 · 18.9 · −20.1 | **1.019** · 20.5 · −20.1 | 1.017 · 20.4 · −20.1 | 0.727 · 20.1 · −27.6 | 0.838 · 16.9 · −20.1 |
| 2019 · BTAL | 0.636 · 16.5 · −26.0 | 0.628 · 16.3 · −26.0 | **0.695** · 18.1 · −26.0 | 0.690 · 17.9 · −26.0 | 0.512 · 17.3 · −33.8 | 0.555 · 14.4 · −26.0 |

What this predicts, each a falsifiable line for the verdict:

1. **Cap-only regime gates at `fire` ≥ 1.00 are substitutes for, or slightly worse than,
   SMA-200 on the 2012 lane**, and the OR adds nothing there (0.858–0.862 vs 0.863): the
   two signals close almost the same month-ends, and the ones the ratio adds (4–6 in
   fourteen years) cost a little upside. Falsified if any `G_r*` cap arm beats `G_sma` on
   `robust_score` in §8.3.
2. **Lower thresholds hurt**: `fire` 0.95 is closed 26 % of days and gives up 2 pp/yr for
   no drawdown relief (its 2022 coverage, 7 month-ends, is the same months SMA-200 already
   covers). Falsified if the §8.2 surface has a plateau below 1.00.
3. **The exit action is dominated in every lane** — it raises drawdown (2019 lane −27.6 % vs
   −20.1 %) and turnover together, and its 2022 "win" (−4.0 % calendar return for `OR_r1`)
   is paid for in 2025 (+2.5 % vs +13.3 %): the same re-entry failure the weekly cadence
   showed (REBALANCE_SPEC §7.3), now caused by a regime release instead of a week. Falsified
   if any `w_off = 0` arm clears step 2's bar in §8.3 or §8.4.
4. **The one genuine gain is the 2019 lane at `G_r1`** (+0.08 Calmar, +1.6 pp CAGR, same
   drawdown) and it comes from blocking TQQQ buys on month-ends where the raw ratio was just
   over 1.00 ahead of a down month. Its `robust_score` and `rank_worst` in §8.5, and its
   `fire = 1.05` neighbour in §8.2, decide whether that is signal or margin. Note that the
   only COVID *drawdown* save (−7.4 %) needs the exit action and rests on 1.011 on
   2020-01-31 — a 1.1 % margin over the threshold at `n = 1`, and not reached at `n = 5, 10,
   20` (0.973 / 0.920 / 0.888 that day).

## 12. Honest limitations

- **Monthly cadence is the binding constraint**, not the signal. A term-structure inversion
  is a days-scale event; read at 12 points a year it degenerates to "was the curve inverted
  at month-end", which in this data is 13 month-ends in fourteen years at the research
  default. REBALANCE_SPEC already found that faster looks lose on the 2025 test window; the
  honest statement is that this system cannot use an intra-month signal as anything but a
  month-end filter, and this spec measures exactly that.
- **The cash ratio reads contango generously** (research §2); the 0.90–0.95 practitioner
  thresholds are in the grid, but no validation against the tradeable VX1/VX2 curve is
  done here. If the §8.2 surface favours 0.90–0.95, that validation (§14) becomes worth
  doing before adoption.
- **Two fast crashes, one grind.** COVID (2019/2012 lanes), 2025 (every lane), 2022 (every
  lane); 2018-Q4 and 2015-08 only in the 2012 lane at a coordinate chosen on that lane.
  n = 1–2 per archetype, as in every verdict of this research line.
- **The holiday rows are a TradingView artefact**, handled by the intersection rule; a CBOE
  `VIX_History.csv` export would not have them. If the data source ever changes, R4's
  22-row pin is the alarm.
- `w_off` on a `fixed` strategy is a new strategy family (trend/regime switching on a
  static mix) that has never been run here; it is in the baselines of §8.2 (`G_sma0` on
  the 50/50 is *not* included — add it to the confirm bundle if the exit arms surprise).

## 13. Acceptance checklist

- [x] `Indicator.inputs`; `prices._read_close`, intersection join and carry-back in `_read_symbol`; `collect_indicators` input assertion
- [x] `indicators.ratio_sma`, `indicators.ts_regime` with the §3.5 loop; T2 lane extended (as new tests in T2 style — errata 6)
- [x] `Gate` regime kind, `symbols`, `w_off` + `clip`; `AnyGate`; `Fixed.balance` and `VolTarget.balance` apply `clip`; `simulate.py`/`strategy.py` untouched
- [x] `spec.py` grammar (§5.1), `gate_str` (§5.2), composite parsing with `gate[i]` paths; `results.json` round-trip
- [x] `regime_report.py`
- [x] `tests/data/2026-08-20/{VIX,VIX3M}.csv` + README paragraph; `make_net_tr.py` pass-through; net snapshot regenerated (diff = two files + README rows); N5 count 15
- [x] Tests R1–R10 green from a fresh clone with `uv run pytest`
- [x] Five specs (§8.2–§8.6) and their artefacts committed together; anchors of §9 confirmed in the verdict
- [x] Docs: STRATEGY_DEVELOPMENT.md ("Declarative strategies" gate table, composite, `w_off`; "Data files and indicators" cross-symbol inputs), ARCHITECTURE.md (`Indicator.inputs`, loader intersection rule, gate kinds), `data/README.md` (index series paragraph), CLAUDE.md §6 (one line: a new external signal starts with `regime_report.py`)
- [x] `notes/regime-verdict.md` per §10; WINNING_STRATEGIES.md changed only if step 6 says so (step 6 said no — the file is not created)

## 14. Deliberately not in scope

The tradeable curve (`VX1!/VX2!` from TradingView or stitched CBOE contracts) as a
fidelity check of the cash ratio — worth doing only if §8.2 pulls the threshold below 1.00.
VIX9D/VIX (starts 2013) and VIX3M/VIX6M (2014) — they do not cover the 2012 start, and the
cross-symbol machinery built here makes them a two-line factory each later. A VRP signal
(VIX − realized vol) — zero extra data, different failure mode, its own spec. The armed
band as a third state with a partial action — `w_off ∈ (0, 1)` already tests partial tilt
in the fired state; adding a second band adds a parameter with no month-end to act on.
Regime-conditional `sigma_target` (tightening the vol target instead of clipping the
weight) and asymmetric gate speeds — both are gate changes REBALANCE_SPEC §10 flagged, and
both should wait for this spec's verdict on whether the signal carries anything at monthly
cadence at all.

## 15. Errata (found during implementation)

1. **§5.3 "No runner change" was wrong.** `sweep._param_value` returned any
   non-dict value raw, so a composite gate grid value (a JSON list) would have
   landed in `params` as an unhashable list and crashed `build_summary`'s
   `by_combo` keys. One-line fix: list values route through the renderers too
   (`sweep.py`); R8's own expected strings already assumed it.
2. **§2.1 "make_net_tr.py … iterate[s] a fixed symbol list" was wrong** about
   the generator: `build()` globs `*.csv`, so copying the index files into the
   parent without the §2.2 pass-through rule would have broken it. The
   fixed-list claim is true only of `tests/test_total_return.py` /
   `tests/test_net_tr.py`. The §2.2 design stands unchanged.
3. **§8.6's confirm bundle collides with the spec auto-discovery test.**
   `tests/test_spec.py::every_strategy` runs every non-`sweep_` spec against
   the flat `tests/data` snapshot, which §2.2 forbids extending — so
   `specs/regime_confirm_2012.json` would `FileNotFoundError` there. Resolution
   (user-approved): `every_strategy` skips a spec whose declared symbols are
   absent from the flat snapshot; the confirm bundle is covered by R10 and the
   §9 run instead.
4. **`regime_report.py` default window end** is pinned to
   `min(last joint day, SMA symbol's last day)` so the §9 invocations (no
   `--end`) reproduce R4's window (… → 2026-08-20, 3,679 joint days) even
   though VIX/VIX3M run one day further.
5. **§4.3's "order cannot matter" for `AnyGate.clip`** holds only when the
   members' `assets` coincide (every shipped composite). With disjoint asset
   sets a later member can re-inflate what an earlier one clipped. Normative
   semantics: clips apply in member order; the order-invariance property is
   tested for the shared-assets case only.
6. **R3 "add to the T2 strict lane"** could not be a literal parametrize
   entry — that lane feeds single-symbol frames. The causality tests land as
   new tests in T2 style on a synthetic joined frame (truncation invariance
   plus the ×1000 price-look-ahead form), as R3's own wording describes.
7. **R10's "λ0.80" label shorthand** — the artefact label spells it
   `QQQ:VOL_EWMA80`; same arm.
8. **§8.6's per-episode table is bounded by the `drawdowns` block depth**
   (top 5 per strategy): an episode shallower than an arm's fifth-deepest
   drawdown does not appear for that arm. The verdict's panel marks those
   cells `·`; every episode the read protocol needed was visible.
9. **The winners file named in §10 step 6 now lives at
   `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`; the checklist's parenthetical was
   true when ticked.** (EPISODE_SPEC §7.2.)
