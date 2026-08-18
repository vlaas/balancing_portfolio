# Specification: declarative bundles and parametrised strategies

Repo: `vlaas/balancing_portfolio` · baseline commit: `93d3f68` ("machine-readable results") · status: implemented (see §13)

## 1. Goal

Make a strategy proposal a JSON document, not a Python file, so that an agent (Claude in a
sandbox, Claude Code, later a sweep runner or MCP server) can go from "try a 10-month SMA
gate with the contribution exempt" to a `results.json` without touching `bundles.py` or
`strategies/`. Concretely:

- a **spec file** describing a `Config` and a list of strategies, run with `main.py --spec`;
- two **parametrised strategy types** — `fixed` and `vol_target` — and a **gate** component
  that either can carry, covering the shipped strategies plus the ones on the research list
  (SMA gate daily/monthly, contribution-exempt gate, volatility targeting, and their stack);
- one small **engine extension** (`buy_cap`) that the contribution exemption requires;
- CLI flags `--data`, `--no-charts`, `--quiet`;
- report fixes so bundles of any size render (dynamic colours, dynamic column width).

Sweeps, robustness metrics, cost model, MCP server: §11.

## 2. Spec file

JSON, chosen for symmetry with `results.json` and because it needs no new dependency.

```json
{
  "schema_version": 1,
  "config": { "start": "2017-01-03", "initial_capital": 10000, "monthly_contribution": 500 },
  "strategies": [
    { "type": "fixed", "label": "TQQQ/BTAL 50/50", "weights": { "TQQQ": 0.5, "BTAL": 0.5 } },
    { "type": "fixed", "weights": { "TQQQ": 1.0 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "BTAL": 0.5 },
      "gate": { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "BTAL": 0.5 },
      "gate": { "symbol": "QQQ", "assets": ["TQQQ"], "sma_months": 10, "contribution_exempt": true } },
    { "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
      "vol": { "kind": "ewma", "lam": 0.94 }, "leverage": 3, "sigma_target": 0.45, "w_max": 0.5,
      "gate": { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 } },
    { "type": "fixed", "label": "SPY benchmark", "weights": { "SPY": 1.0 } }
  ]
}
```

Rules:

- `config` has exactly the fields of `simulate.Config`; all required, no defaults.
- `strategies` is an ordered list; **the last entry is the benchmark**, exactly as in
  `bundles.py`. Minimum length 2 (one strategy plus benchmark).
- `label` is optional. When absent it is generated deterministically from the parameters
  (§3.4). Labels must be unique within a spec; `results_json._slugs` already asserts slug
  uniqueness, so add the same assertion in `build_bundle` with a clearer message.
- Unknown keys anywhere are an error (`ValueError` naming the JSON path, e.g.
  `strategies[2].gate.sma_day: unknown key`). Typos must not silently become defaults.
- Ship two files: `specs/default.json` (reproduces the `default` bundle exactly, §8) and
  `specs/research.json` (the example above minus nothing — the current research candidates).

## 3. Strategy types — new module `spec.py` plus `strategies/fixed.py`, `strategies/vol_target.py`, `strategies/gate.py`

`spec.py` owns parsing: `build_bundle(spec: dict) -> Bundle` and `load_spec(path) -> dict`.
It maps `type` to a class and passes validated params to its constructor. Every strategy
built from a spec gets a `spec` attribute holding the normalised entry (defaults filled,
label filled) — this is what `results.json` embeds (§5.3).

### 3.1 `gate` component (`strategies/gate.py`)

Not a strategy; an object a strategy owns. Reproduces `TqqqBtalQqqSma200` behaviour and adds
the monthly variant and the contribution exemption.

| Key | Type | Default | Meaning |
|---|---|---|---|
| `symbol` | str | required | symbol whose trend is tested (added to `data` if not traded) |
| `assets` | list[str] | required | traded assets whose *buys* the gate caps; each must be in the strategy's weights |
| `sma_days` | int | — | daily SMA length; indicator `sma(n)`, column `SMA{n}` |
| `sma_months` | int | — | month-end SMA length; indicator `sma_monthly(m)`, column `SMA{m}M` |
| `contribution_exempt` | bool | `false` | when closed, still allow buys up to that day's external cash × the asset's weight |

Exactly one of `sma_days` / `sma_months`. Semantics, matching the existing strategy line for
line: the gate is **closed** on a day iff `close(symbol) < SMA`; it is **open** if either
value is `None`. `Gate.indicators` returns `{symbol: (indicator,)}` for the owning strategy
to merge into its own; `Gate.buy_cap(asset, ctx, weights) -> float | None` returns `None`
for assets not in `assets` or when open, `0.0` when closed, and `ctx.contribution *
weights[asset]` when closed and exempt.

### 3.2 `fixed` (`strategies/fixed.py`)

| Key | Type | Default |
|---|---|---|
| `weights` | dict[str, float] | required; values ≥ 0, sum ≤ 1 (residual is cash, as today) |
| `gate` | gate object | none |

`balance()` returns `weights`; `buy_cap()` delegates to the gate. With no gate this is
exactly today's base `Strategy`; with `sma_days: 200` on QQQ for TQQQ it is exactly
`TqqqBtalQqqSma200` (proved by test T3).

### 3.3 `vol_target` (`strategies/vol_target.py`)

Volatility targeting on one leveraged risk asset, vol measured on its underlying, per the
research notes ("measure vol on QQQ, ×3").

| Key | Type | Default | Meaning |
|---|---|---|---|
| `risk` | str | required | the asset whose weight is scaled (`TQQQ`) |
| `safe` | str or null | required | receives `1 − w_risk`; `null` leaves the residual in cash |
| `vol_symbol` | str | required | symbol the vol indicator is computed on (`QQQ`); added to `data` if not traded |
| `vol` | `{"kind": "ewma", "lam": 0.94}` or `{"kind": "realized", "n": 63}` | required | maps to `ewma_vol(lam)` / `realized_vol(n)` |
| `leverage` | float | `1.0` | σ_risk = leverage × σ_vol_symbol (`3` for TQQQ on QQQ) |
| `sigma_target` | float | required | annualised target vol of the **risk asset position**, e.g. `0.45` (≈ 15% on QQQ × 3) |
| `w_max` | float | `1.0` | upper clip on w_risk |
| `w_min` | float | `0.0` | lower clip on w_risk |
| `fallback` | float | `w_max` | w_risk while the vol indicator is `None` |
| `gate` | gate object | none | as in §3.1; caps buys of `risk` (or whatever `assets` lists) |

`balance(ctx)`: `σ = ctx.indicator(vol_symbol, vol.name)`; if `None`, `w = fallback`; else
`w = clip(sigma_target / (leverage · σ), w_min, w_max)`. Returns `{risk: w, safe: 1 − w}` or
`{risk: w}` when `safe` is null. `weights` (the asset universe the engine asserts against)
is the fallback allocation. `w_min ≤ w_max ≤ 1`, all weights in `[0, 1]`, validated at
construction. Rebalance day only — the engine already calls `balance()` only on
`is_rebalance_day`, so this is monthly vol targeting on the month-end close.

### 3.4 Auto-labels

Deterministic, ASCII, built from the normalised params so two identical proposals collide
loudly and a sweep gets readable labels for free:

- `fixed`: symbols with integer percentages joined by `/`, e.g. `TQQQ50/BTAL50`, `SPY100`;
- `vol_target`: `VT {risk}/{safe|cash} t{sigma_target%} w{w_min%}-{w_max%} {vol_symbol}:{vol.name}`,
  e.g. `VT TQQQ/BTAL t45 w0-50 QQQ:VOL_EWMA94`;
- gate suffix: ` gate {symbol}<{column}` plus `+contrib` when exempt, e.g.
  ` gate QQQ<SMA10M+contrib`.

An explicit `label` always wins.

## 4. Engine extension — `buy_cap` (`strategy.py`, `simulate.py`)

Today: `allow_buy(asset, ctx) -> bool`; a gated asset's target is capped at its current
shares and its declined budget is redistributed to the open assets by weight. A
contribution exemption needs a *dollar* cap, not a boolean.

`strategy.py`:

```python
class MarketDay:
    def __init__(self, row: dict, contribution: float = 0.0): ...
    @property
    def contribution(self) -> float:
        """External cash added today: initial capital on day 0, the monthly
        contribution on a rebalance day, 0.0 otherwise."""

class Strategy:
    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        """Max USD of `asset` to buy today; None = unlimited. Sells are never capped.
        Default derives from allow_buy() so existing strategies are unchanged."""
        return None if self.allow_buy(asset, ctx) else 0.0
```

`simulate.py`, replacing the gated block, keeping the same structure so today's numbers are
reproduced exactly:

```python
ctx = MarketDay(row, contribution=flow)
weights = strategy.balance(ctx)
...
target = {a: math.floor(total * weights[a] / row[a]) for a in assets}
caps = {a: strategy.buy_cap(a, ctx) for a in assets}
gated = [a for a in assets if caps[a] is not None]           # same list as before when caps ∈ {None, 0.0}
for asset in gated:
    target[asset] = min(target[asset], shares[asset] + math.floor(caps[asset] / row[asset]))
# redistribution block unchanged
```

`flow` is already accumulated before this point in the loop; pass it into `MarketDay`.
Invariants: `buy_cap` returning `0.0` is bit-identical to `allow_buy` returning `False`;
returning `None` is bit-identical to `True`. `assert cap >= 0` for non-None caps. Both
hooks are documented in `docs/STRATEGY_DEVELOPMENT.md`; new strategies implement `buy_cap`,
`allow_buy` stays for the existing ones.

## 5. CLI and results

### 5.1 `main.py`

- `--spec PATH` — build the bundle from a spec file; mutually exclusive with the positional
  `bundle` (argparse group). `run.bundle` in `results.json` becomes the spec file stem.
- `--data DIR` — data directory, default `data`. Lets a JSON be produced from the frozen
  `tests/data` snapshot, and lets an agent point at any dataset. Recorded as `run.data_dir`.
- `--no-charts` — skip `save_charts`; the "Saved …png" line is not printed. Required for
  bundles beyond ~8 strategies (charts become unreadable) and for pure-JSON runs.
- `--quiet` — suppress `print_report`; only the "Saved …" lines are printed.
- All existing flags unchanged. `--md` with `--no-charts` writes the report without chart
  links (or with links to files that don't exist — pick "without" and note it in the docs).

### 5.2 Wiring

`run_bundle(bundle, data_dir)` is unchanged; `--spec` and the named bundles both produce a
`Bundle`. `collect_indicators` needs no change: `Fixed`/`VolTarget` expose `indicators` and
`data` like any strategy (gate symbol / vol symbol added to `data` when not traded).

### 5.3 `results.json` — bump `SCHEMA_VERSION` to 2, additive

- `run.data_dir` (string), `run.spec_path` (string or null);
- top-level `spec`: the normalised spec dict for `--spec` runs, else null;
- per strategy: `spec` (the strategy's normalised entry, or null for hand-written classes),
  keeping `class` as is.

Everything else byte-identical for a `default` run except `schema_version`.

## 6. Report — `report.py`

- **Colours**: replace `zip(results, COLORS)` with `_colours(n)`: the four existing brand
  colours for n ≤ 4, `matplotlib.colormaps["tab10"]` for 5–10, `tab20` for 11–20, and an
  assertion for n > 20 with the message "use --no-charts for larger bundles". Never
  truncate silently, which is what `zip` does today.
- **Console width**: `VALUE_W = max(20, max(len(r.label) for r in results) + 2)` computed
  in `print_report`, so long auto-labels don't misalign columns. `NAME_W` unchanged.

## 7. Existing strategies

`strategies/tqqq_btal_5050.py`, `tqqq_100.py`, `spy_benchmark.py`, `tqqq_btal_qqq_sma200.py`
and `bundles.py` are **left untouched** in this change; the golden test pins them. Test T3
proves the spec forms are equivalent; deleting the hand-written classes in favour of
`specs/default.json` is a follow-up decision, not part of this spec.

## 8. Golden — `specs/default.json` reproduces the `default` bundle

Running `main.py --spec specs/default.json --data tests/data --json …` must produce a
`results.json` whose `strategies[*].summary`, `drawdowns`, `yearly_returns` and `imbalance`
blocks are identical to the `default` bundle's from the same data (assert deep equality
after dropping `run`, `spec`, `class` and per-strategy `spec`). Final values on `tests/data`:
$237,275.03 / $661,164.25 / $224,725.33 / $153,938.16.

## 9. Tests — `tests/test_spec.py`, `tests/test_gate.py`, `tests/test_vol_target.py`, additions to `test_simulate.py`, `test_main.py`, `test_report.py`

**T1 — Parsing.** `build_bundle` on `specs/default.json` and `specs/research.json` succeeds;
each of: unknown top-level key, unknown strategy key, unknown gate key, missing required
field, both `sma_days` and `sma_months`, weights summing to 1.2, `w_min > w_max`, duplicate
labels, one-strategy list — raises `ValueError` whose message contains the JSON path.

**T2 — Auto-labels.** The examples of §3.4 exactly; explicit label wins; two identical
entries → duplicate-label error.

**T3 — Equivalence to hand-written strategies.** On `tests/data` with the default `Config`,
`Fixed(weights={"TQQQ":.5,"BTAL":.5})`, `Fixed(weights={"TQQQ":1})`,
`Fixed(weights={"SPY":1})` and the gated `Fixed(... sma_days=200)` produce curves
frame-equal (`polars.testing.assert_frame_equal`) to `TqqqBtal5050`, `Tqqq100`,
`SpyBenchmark`, `TqqqBtalQqqSma200`.

**T4 — `buy_cap` engine semantics.** Synthetic 2-asset prices, one rebalance day where the
strategy would buy asset A:
(a) `buy_cap → 0.0` gives the same trades as `allow_buy → False` (bit-identical frames);
(b) `buy_cap → None` same as `allow_buy → True`;
(c) `buy_cap → 300.0` buys `floor(300 / price_A)` shares of A and the declined budget goes to
B by weight;
(d) a cap on an asset that would be sold anyway leaves its sell unchanged;
(e) `MarketDay.contribution` equals `initial_capital` on day 0, `monthly_contribution` on
rebalance days, `0.0` otherwise (assert from inside a recording strategy).

**T5 — Gate.** Synthetic gate symbol crossing its SMA: closed iff `close < SMA`; open when
either is `None`; `contribution_exempt` closed-day cap equals `contribution × weight`; gate
`symbol` appears in the strategy's `data` and `indicators`; `sma_months` uses `SMA{m}M`.

**T6 — Vol target.** With a stub indicator value: `w = sigma_target/(leverage·σ)` clipped to
`[w_min, w_max]`; `fallback` used when σ is `None`; `safe: null` returns a one-key dict; a
full run on `tests/data` with `sigma_target: 0.45, w_max: 0.5, leverage: 3, ewma 0.94`
completes and its `weights` universe is `{TQQQ, BTAL}`.

**T7 — Strategy contract (generic, requirement 9 from the integration list).** For every
strategy in every `BUNDLES` entry and every shipped spec: on every rebalance day of
`tests/data`, `balance()` returns exactly the `weights` keys, all ≥ 0, sum ≤ 1 + 1e-9;
`buy_cap` is `None` or ≥ 0; running the same strategy object twice yields frame-equal
curves (no state leaks between runs).

**T8 — Golden equivalence of `specs/default.json`** as in §8.

**T9 — CLI.** `main.py --spec specs/research.json --data tests/data --json OUT --no-charts
--quiet` writes OUT, prints only "Saved" lines, creates no PNGs, and OUT has
`schema_version == 2`, `run.data_dir`, `spec`, and a `spec` per strategy; positional bundle
plus `--spec` is an argparse error.

**T10 — Report.** `save_charts` with 6 and with 20 synthetic results writes four PNGs;
21 raises the "use --no-charts" assertion; `print_report` with a 30-char label produces
aligned columns (check header and first metric line widths agree).

## 10. Docs and agent protocol

- `docs/STRATEGY_DEVELOPMENT.md`: new section "Declarative strategies" (spec format, both
  types, gate, auto-labels) placed *before* "writing a strategy class", with the sentence
  "if it can be a spec, it should be a spec"; `buy_cap` documented next to `allow_buy`.
- `docs/ARCHITECTURE.md`: `spec.py` in the diagram; `results.json` schema 2 fields.
- `CLAUDE.md`, new section **Agent protocol** (requirement 11): a proposal is a spec file
  under `specs/`; run it as `uv run main.py --spec specs/X.json --json results/X.json
  --no-charts --quiet` (with `--data tests/data` when a number must be comparable to the
  golden); commit spec + results together; results are never edited by hand; when a proposal
  needs a new type or parameter, change `spec.py`/`strategies/` with tests first and the
  spec second; never modify engine semantics to make a spec "work" without saying so in the
  commit.

## 11. Deliberately not in scope — and how this spec prepares for it

- **Sweep** (`sweep(spec_template, grid)` → params × metrics table, `--sweep`) together with
  **robustness metrics** (start-date sensitivity, neighbourhood flatness, holdout split).
  This spec supplies what a sweep needs: deterministic auto-labels from params, unlimited
  strategy count, `--quiet --no-charts`, a pure `build_bundle`, and the spec embedded in
  `results.json` so the table is a flatten. Sweep gets its own spec because its real design
  content is the robustness part.
- Asymmetric gate speeds (different SMA for exit and re-entry), band/threshold rebalancing,
  never-sell (sell caps), cost model, MCP server.

## 12. Acceptance checklist

- [x] `spec.py` (`load_spec`, `build_bundle`, validation with JSON paths, auto-labels)
- [x] `strategies/gate.py`, `strategies/fixed.py`, `strategies/vol_target.py`
- [x] `buy_cap` + `MarketDay.contribution` in `strategy.py`; `simulate.py` block per §4
- [x] `--spec`, `--data`, `--no-charts`, `--quiet`; `SCHEMA_VERSION = 2` with §5.3 fields
- [x] `report.py` dynamic colours (≤ 20, assert beyond) and dynamic `VALUE_W`
- [x] `specs/default.json`, `specs/research.json`
- [x] Tests T1–T10; whole suite green from a fresh clone with `pip install polars matplotlib pytest`
- [x] Existing golden test unchanged and green; existing strategy modules and `bundles.py` untouched
- [x] Docs per §10, including the CLAUDE.md agent protocol

## 13. Errata — deviations found and fixed during implementation

Validated against the code before implementation; these corrections were
agreed and applied (the sections above are left as proposed):

- **T4(e)**: `contribution == 0.0` is unobservable from inside a strategy —
  the engine constructs `MarketDay` only on day 0 and rebalance days, where
  the flow is non-zero. The test asserts the `0.0` default on a directly
  constructed `MarketDay` instead; and a day 0 that is also a rebalance day
  carries `initial_capital + monthly_contribution` (the §4 docstring wording
  covers this case now).
- **§2 uniqueness**: `build_bundle` asserts **slug** uniqueness (via
  `results_json.slug`), which subsumes label uniqueness — two distinct labels
  can still collide at slug level and would overwrite each other's curve CSV.
- **§3.1/§4 caps**: a *finite, non-binding* cap is not equivalent to `None` —
  any asset with a non-`None` cap counts as gated and is excluded from the
  redistribution. `{0.0 ≡ False, None ≡ True}` hold exactly as specified;
  documented under `buy_cap` in STRATEGY_DEVELOPMENT.md.
- **Gate × vol_target**: the contribution-exempt cap multiplies the weights
  `balance(ctx)` returns for the day (uniform for both types; for `fixed`
  those are the static weights).
- **§5.1 exclusion**: implemented as an explicit post-parse `parser.error()` —
  an argparse mutually-exclusive group is unreliable with an `nargs="?"`
  positional whose passed value equals its default. Same observable behavior
  (exit code 2).
- **§5.3**: `results_payload`/`save_json` grew keyword-only `data_dir`,
  `spec_path`, `spec` parameters; `tests/test_results_json.py`'s schema
  assertions were updated to v2 accordingly.
- **§8**: `specs/default.json` carries explicit labels on all four entries —
  auto-labels would break the slugs `tests/test_results_json.py` pins.
- **§9**: `tests/test_report.py` is a new file (the report layer had no
  tests); the T-numbers here are cited as "DECLARATIVE_SPEC T·" in test
  comments to avoid clashing with INDICATORS_SPEC's T-numbers already used in
  the suite.
- **§10**: STRATEGY_DEVELOPMENT.md has no "writing a strategy class" heading;
  "Declarative strategies" sits between the intro and Quickstart. The
  CLAUDE.md section is numbered (`## 6. Agent protocol`) to match the file's
  convention.
- **§12**: the suite is verified with `uv run pytest` (the repo is uv-based);
  the dependencies remain polars, matplotlib, pytest.
