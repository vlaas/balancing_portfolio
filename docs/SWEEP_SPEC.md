# Specification: sweeps with robustness metrics

Repo: `vlaas/balancing_portfolio` · baseline commit: `33c275f` ("declarative bundles") · status: implemented (§11 errata; `--jobs` deferred)

## 1. Goal

Turn "which parameters are good?" into a repeatable, machine-readable procedure that is
hard to fool. Three parts, in dependency order:

1. **`Config.end`** — a window has two ends; today it has one. Needed for holdout and for
   disjoint sensitivity windows.
2. **Exposure metrics** in `results.json` — average/min/max weight per asset. Without them a
   vol-target result cannot be told apart from "just more TQQQ" (this was the decisive
   column in the first experiment).
3. **`sweep.py`** — grid expansion over a strategy template, evaluation over a set of
   windows, and a summary that ranks by a *robust* objective (neighbourhood minimum,
   holdout test, rank stability) rather than by the best in-sample number.

Plus a first grid, `specs/sweep_vt.json`, centred on the region the first experiment found.

Not in scope: cost model, band rebalancing, asymmetric gates, MCP server (§10).

## 2. `Config.end`

`simulate.Config` gains `end: dt.date | None = None`. `load_prices` gains `end=None` and
applies `date <= end` right after the `date >= start` filter and **before**
`is_rebalance_day` is computed, so the final row of the truncated frame is never a rebalance
day (same rule as today, same reason: it is a valuation day, not a trade day).

Rules:

- `end` must be ≥ `start` and ≤ the last date in the data; otherwise `ValueError` (silent
  truncation would make windows incomparable). `start` stays strict: it must be a trading
  day (`simulate` asserts it), the sweep runner is responsible for snapping (§4.3).
- Spec files: `config.end` optional string date; absent or `null` means "to the end of the
  data". `normalised_spec` and `results.json` `config.end` carry the resolved value.
- CLI: `--end YYYY-MM-DD` overrides a bundle's or spec's end (as `--data` overrides the
  directory). No `--start`: it would need snapping and belongs to the sweep runner.
- Invariant (test): the curve of a run with `end = E` equals the first rows of the full run
  on every row except the last, which differs only in that no contribution/rebalance
  happens on it.

## 3. Exposure metrics — `stats.py`, `results_json.py`

`stats.exposure(allocations) -> dict[str, dict]`: for each asset in the allocations frame,
including `CASH`, over all trade days:

```
{asset: {"avg_target": mean(target), "avg": mean(actual), "min": min(actual), "max": max(actual)}}
```

Attached to each strategy in `results.json` as `"exposure"`, keyed by asset, and shown in
`print_report`/`save_markdown` as one line per traded asset (`Avg weight TQQQ  0.58`),
placed after the misallocation rows. `SCHEMA_VERSION` → 3, additive. `summary()` itself
stays flat and unchanged so nothing else moves.

## 4. Sweep — new module and CLI `sweep.py`

`python sweep.py SPEC --data DIR --out DIR [--jobs N] [--dry-run]`. Never charts, never
prints the side-by-side report; prints one line per window with the count of strategies
and elapsed time, then the top-N table (§4.6). `--dry-run` prints the number of expanded
strategies × windows and exits.

### 4.1 Sweep spec file

```json
{
  "schema_version": 1,
  "config": { "initial_capital": 10000, "monthly_contribution": 500 },
  "windows": {
    "start": "2012-01-03",
    "end": null,
    "holdout": "2023-01-01",
    "sensitivity": { "every_months": 6, "length_years": 5 }
  },
  "template": {
    "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
    "vol": { "kind": "ewma", "lam": { "grid": [0.90, 0.94, 0.97] } },
    "leverage": 3,
    "sigma_target": { "grid": [0.30, 0.35, 0.40, 0.45, 0.50] },
    "w_max": { "grid": [0.6, 0.7, 0.8] },
    "gate": { "grid": [null, { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 }] }
  },
  "baselines": [
    { "type": "fixed", "label": "50/50", "weights": { "TQQQ": 0.5, "BTAL": 0.5 } },
    { "type": "fixed", "weights": { "TQQQ": 0.6, "BTAL": 0.4 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "BTAL": 0.5 },
      "gate": { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 } },
    { "type": "fixed", "label": "SPY benchmark", "weights": { "SPY": 1.0 } }
  ],
  "objective": "calmar",
  "constraint": { "max_drawdown": -0.50 }
}
```

- `config` has no `start`/`end`; windows own the dates. Unknown keys → `ValueError` with
  path, as in `spec.py`.
- `template` is one strategy entry in the ordinary spec grammar in which any leaf value —
  including nested ones and including the whole `gate` object — may be replaced by
  `{"grid": [v1, v2, …]}`. Every `grid` list must have ≥ 2 distinct values.
- `baselines`: ordinary strategy entries, run in every window alongside the grid, never
  ranked; the last one is the benchmark for correlation, as in a bundle.
- `objective`: one of `calmar`, `sharpe`, `sortino`, `cagr`, `xirr` (higher is better).
  Default `calmar`.
- `constraint`: optional; keys are summary metrics, values are the minimum acceptable
  (for `max_drawdown`, since it is negative, `-0.50` means "no worse than −50%"). Evaluated
  on the **full** window; violating grid points are still run and reported but marked
  `feasible: false` and excluded from ranking.

### 4.2 Expansion (`sweep.expand(template) -> list[dict]`)

Depth-first walk collecting every `grid` in document order → Cartesian product in that
order; each combination substituted back yields an ordinary strategy entry, built via
`spec._TYPES` exactly as `build_bundle` does (so validation, defaults and auto-labels are
shared, not duplicated). Each expanded entry gets `params`: a flat dict of the varied leaves
with dotted keys — `{"vol.lam": 0.94, "sigma_target": 0.35, "w_max": 0.7, "gate": "QQQ<SMA200"}`
(objects are rendered through the same string the auto-label uses; `null` → `null`).
Auto-labels are unique by construction because every varied parameter is in the label; the
`slug` collision assertion still runs. `expand` is pure and deterministic; the expanded
list is written to `--out/strategies.json`.

### 4.3 Windows (`sweep.windows(spec, calendar) -> list[Window]`)

`Window(name, kind, start, end)`, `kind ∈ {full, fit, test, sens}`. `calendar` is the traded
symbols' date column from one `load_prices` call at `windows.start` (cheap: ~10 ms). Every
date is snapped to the **first trading day on or after** it; `end` dates to the last on or
before.

- `full`: `[start, end]` (end null → last date).
- Holdout, when `holdout` is set: `fit = [start, day before holdout]`, `test = [holdout,
  end]`. Adjacent, disjoint. Test window shorter than 2 years → warning in the summary
  (metrics on it are noise), never an error.
- Sensitivity, when set: starts at `start`, `start + every_months`, … ; each window is
  `[s, s + length_years]` when `length_years` is set (rolling, fixed length — preferred),
  otherwise `[s, end]` (anchored, overlapping — allowed, but the summary says so). Windows
  whose end would pass `end` are dropped. Names `sens_2012-01-03` etc.

Sensitivity windows overlap by construction; the summary reports dispersion across them as
a description, not as a statistical test — the spec says this in the output header.

### 4.4 Running (`sweep.run_sweep(spec, data_dir, jobs=1) -> tuple[pl.DataFrame, dict]`)

For each window: one `load_prices` (with the window's `start`/`end` and the union of
indicators of grid + baselines), then `simulate` for every grid strategy and baseline;
`summary()`, `exposure()`. Reuse `main.run_bundle` by building a `Bundle` per window
(`Config(start, initial_capital, contribution, end)`) — no second simulation path.
Measured cost: ~0.11 s per strategy on 3 675 rows; the first grid (94 strategies × ~23
windows ≈ 2 200 simulations) is ~4 minutes single-process. `--jobs N` runs windows in a
`ProcessPoolExecutor` (frames pickle; results are per-window lists) — optional, do it last.

Long table `--out/runs.csv` (and `runs.json`), one row per (strategy, window):
`label, kind, window, start, end, is_baseline, feasible, params.* (one column per varied
leaf, null for baselines), <every summary() key>, exposure.<asset>.avg, exposure.<asset>.min`.
`final_value` and `xirr` are only comparable within a window; the summary uses TWR metrics.

### 4.5 Summary (`--out/summary.json`, `--out/summary.md`)

Per grid strategy:

- `full`: objective and all summary metrics on the full window; `feasible`.
- `holdout`: objective on `fit` and on `test`; `test_minus_fit`.
- `sensitivity`: over the sens windows — `median`, `min`, `max`, `iqr` of the objective and
  of `max_drawdown`; `rank_median` and `rank_worst`, where rank is this strategy's rank by
  objective among all feasible grid strategies within the same window (1 = best).
- `neighbourhood`: for each numeric grid dimension, the immediate neighbours are the
  strategies identical in every other parameter and one grid step away in this one (1 or 2
  of them; the gate/categorical dimension has no neighbours). `neighbour_min` = the minimum
  full-window objective over all neighbours across all dimensions; `neighbour_mean`
  likewise; `edge` = true if the point lies on the boundary of any dimension.
- `robust_score` = `min(full.objective, neighbour_min, sensitivity.median)`; if a holdout
  is defined, also `min(…, holdout.test)`. This is the ranking key. It is deliberately a
  minimum: a point only scores high if it is good itself, its neighbours are good, it is
  good in the median sub-window and it held up out of sample.

Baselines get `full`, `holdout`, `sensitivity` blocks (no neighbourhood, no rank), so the
top table can show them next to the grid.

`summary.md`: header (data range, windows used, objective, constraint, warnings), then a
table of the top 15 grid strategies by `robust_score` — columns `params…, full obj, nbr
min, sens median [min–max], holdout fit → test, rank med/worst, maxdd full, avg risk wt,
edge` — followed by the same columns for the baselines. `edge` points ranked in the top 15
get a footnote: extend the grid in that direction before believing them.

### 4.6 What the runner refuses to do

No automatic "best". `summary.md` ranks and shows; the decision stays with the reader.
No refitting inside windows. No metric that mixes windows of different length except via
TWR-based ratios. No silent snapping: every snapped date is printed once in the header.

## 5. Interaction with `main.py`

None beyond `--end`. Sweeps are their own entry point on purpose: `main.py` renders one
bundle; `sweep.py` produces tables. Both share `spec.py`, `run_bundle`, `stats`.

## 6. Tests

**T1 — `Config.end`.** Truncated run equals the prefix of the full run except the last row
(§2 invariant); `end < start`, `end` past data end → `ValueError`; last row of a truncated
frame is never a rebalance day; `--end` on the CLI reaches `results.json` `config.end`.

**T2 — Exposure.** Fixed 50/50 on `tests/data`: `avg_target` exactly 0.5 for both assets,
`avg` in `[0.49, 0.5]`; CASH present; a VT strategy has `min < avg < max`; the block is
present in `results.json` and rendered in the report.

**T3 — Expansion.** The §4.1 template expands to 90 entries in the documented order; each
has `params` with the four dotted keys; labels unique; a `grid` of one value → `ValueError`;
a `grid` inside `gate` and one for the whole `gate` object both work; `expand` is
deterministic (`==` across two calls).

**T4 — Windows.** With a synthetic calendar: snapping forward for starts and backward for
ends; holdout produces adjacent disjoint fit/test; rolling windows have equal length and
drop the ones overrunning `end`; anchored mode when `length_years` is null; short test
window sets the warning.

**T5 — Neighbourhood and ranks.** A synthetic 3×3 grid with known objectives yields the
expected `neighbour_min`, `edge` flags, and per-window ranks; a categorical dimension has
no neighbours; baselines are excluded from ranks.

**T6 — End to end.** A 2×2 grid, one baseline, one sens window on `tests/data` runs;
`runs.csv` has `strategies × windows` rows; `summary.json` has every block; `--dry-run`
prints the counts and writes nothing.

**T7 — Golden untouched.** The default bundle test still passes; `end=None` paths are
byte-identical to today's `results.json` except `schema_version` and the new `exposure`
block (assert by deleting those keys and comparing).

## 7. First grid — `specs/sweep_vt.json`

Exactly the §4.1 document. Rationale, from the first experiment: σ35/w0.7 had Calmar 0.69,
σ45/w0.7 0.60, so the neighbourhood is not flat and the grid must bracket 30–50 in 5-point
steps; `w_max` 0.6–0.8 brackets 0.7; λ 0.90–0.97 spans half-lives of 6.6–23 days; the gate
is the one categorical dimension since gate + VT compounded at high σ. Baselines are the
mixes VT should be measured against at equal exposure. Start 2012-01-03 gives BTAL its
full history and 5-year rolling windows every 6 months → 18 sensitivity windows; holdout
at 2023 leaves 3.6 years of test containing one bull leg and 2025's drawdown.

Expected artefacts committed with the sweep: `results/sweep_vt/{strategies.json, runs.csv,
summary.json, summary.md}`.

## 8. Docs and protocol

- `docs/STRATEGY_DEVELOPMENT.md`: "Sweeps" section — template grammar, windows,
  robust_score, and the sentence "a sweep result is a table to read, not a parameter to
  adopt".
- `docs/ARCHITECTURE.md`: `sweep.py` in the diagram; `Config.end`; schema 3.
- `CLAUDE.md` agent protocol: sweeps are proposed as `specs/sweep_*.json`, run with
  `uv run sweep.py specs/X.json --data tests/data --out results/X`, and the four artefacts
  are committed together; an agent reporting a sweep quotes `robust_score`, holdout test
  and rank_worst, never `full` alone.

## 9. Acceptance checklist

- [x] `Config.end`, `load_prices(end=)`, `--end`, spec `config.end`
- [x] `stats.exposure`, `results.json` `exposure`, report lines, `SCHEMA_VERSION = 3`
- [x] `sweep.py`: `expand`, `windows`, `run_sweep`, summary, CLI with `--dry-run`
- [x] `specs/sweep_vt.json`; `results/sweep_vt/*` produced from `tests/data` and committed
- [x] Tests T1–T7 green from a fresh clone
- [ ] `--jobs` (optional, last) — deferred; §11.10
- [x] Docs per §8

## 10. After this

Cost model (`Config.cost_bps`, `cash_yield`) so the sweep can be rerun with friction;
asymmetric gates and band rebalancing as new template dimensions; a `sweep` tool on an MCP
server wrapping `run_sweep`.

## 11. Errata — deviations found and fixed during implementation

Validated against the code before implementation; these corrections were
agreed and applied (the sections above are left as proposed):

1. **§2 location**: `load_prices` lives in `prices.py`, not `simulate.py`; the
   change lands there. "The last date in the data" means the last date of the
   loaded *traded* calendar (files drift at the edges: DBMF/KMLM currently run
   two days past the rest, and extras never extend the calendar).
2. **§2 "carries the resolved value"**: `normalised_spec` and `results.json`
   emit `config.end` only when an end was actually set ("resolved" = after a
   CLI override). An unset end writes no key at all — T7's byte-identity for
   `end=None` runs wins, and the run's actual last date is already in
   `data.end`.
3. **§4.1 `"gate": {"grid": [null, …]}`**: the builders treat key *presence*
   as "has a gate", so a `null` grid value deletes the key from the entry
   rather than substituting `None`. Consequence: `[null, …]` grids work for
   optional keys only — not for `vol_target`'s required-but-nullable `safe`.
4. **§4.1 grids inside lists** (e.g. over `gate.assets` elements) are a
   `ValueError`, not supported.
5. **§4.2 "objects are rendered through the same string the auto-label
   uses"**: the label renders a gate as `" gate QQQ<SMA200"`; the shared
   renderer `spec.gate_str` (`QQQ<SMA200`, plus `+contrib`) was factored out
   so `params` and the label suffix cannot drift. A non-gate object dimension
   renders as compact sorted JSON.
6. **§4.2 "auto-labels are unique by construction"** holds only for
   label-visible leaves. `leverage`, `fallback` and `gate.assets` are absent
   from labels, and λ is rounded to two digits in the indicator name
   (`VOL_EWMA94`), so grids over those collide loudly in `build_bundle`
   ("duplicate label") — grid dimensions must be label-visible.
7. **§4.3**: neighbour steps follow grid-list order, so write grids
   monotonically; `edge` covers numeric dimensions only; neighbours are not
   feasibility-filtered. Anchored sensitivity stops when the snapped start
   reaches `end`; the rolling drop rule compares the raw `s + length_years`
   against the snapped `end`. Snap notes cover the user-supplied dates
   (`windows.start`, `windows.end`, `holdout`); derived boundaries (fit end,
   sensitivity starts) snap silently by construction.
8. **§4.4 runs table**: the `best_year`/`worst_year` tuples flatten to
   `best_year` + `best_year_return` (and `worst_*`) — a CSV cell cannot hold
   a tuple, so "every summary() key" is 20 columns. Baselines carry
   `feasible: true` (the constraint applies to grid points; `is_baseline`
   already separates them). A `None` metric (`max_drawdown_days` ongoing)
   fails a constraint on it. `runs.json` is written through the same
   rounding/serialisation as `results.json` rather than
   `DataFrame.write_json`: polars' threaded means differ in the last ulp
   between reruns, and artefacts must be byte-reproducible.
9. **§4.5**: `robust_score` simply omits absent components (no holdout, no
   sensitivity windows, no numeric dimensions). Infeasible points carry
   `null` rank fields. The top-15 table shows §4.5's columns exactly;
   `robust_score` itself lives in `summary.json`.
10. **§4/§7 CLI and artefacts**: `--out` defaults to `results/<spec stem>`
    (the §8 convention); `--data` defaults to `data` as in `main.py`.
    `runs.json` is produced and committed alongside §7's four artefacts.
    `--jobs` is deferred: per-window tasks and results are plain dicts
    (strategies are rebuilt inside the worker via `build_bundle`), so a
    `ProcessPoolExecutor` over windows remains a drop-in.
11. **§7 "18 sensitivity windows"**: §4.3's rules over `tests/data` (ends
    2026-08-14) give 20 rolling windows (starts 2012-01-03 … 2021-07-03);
    ~4 minutes was also pessimistic — the full grid runs in well under a
    minute single-process. Every top-15 point sits on the λ = 0.90 boundary,
    footnoted per §4.5: extend the λ grid downward before believing them.
12. **Risk noted, unhandled**: `stats.xirr` brackets (−99.99 %, +1000 %) and
    asserts a sign change; a catastrophic enough window would abort the sweep.
    None of the §7 windows comes close. Widening the bracket is an engine
    change and needs its own commit saying so.
