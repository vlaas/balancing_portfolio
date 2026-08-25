# Specification: monthly momentum indicators and the cross-sectional rotation strategy

Repo: `vlaas/balancing_portfolio` · baseline commit: `0c9c731` ("New data for advanced strategies") · status: implemented (branch `rotation`, errata §12)

All numbers in this spec are from sandbox runs on a fresh clone at `0c9c731`.

## 1. Goal

The strategy-landscape survey (2026-08, session catalog) identified a staged testing
order for community/academic long-only strategies. Stage 1–2 — GEM dual momentum,
Faber GTAA-5, Accelerating Dual Momentum, Keller HAA-Simple and HAA-Balanced, plus
VAA-G4 as a skeptical reference — all reduce to one mechanism the engine cannot yet
express: **rank a universe by a monthly momentum score, hold the top-k equal-weight,
and route disqualified or canary-flagged mass to a defensive selection.** Everything
else in those strategies (monthly cadence, month-end signals, TR closes, per-side
costs, cash residual) the engine already does.

This spec adds two orthogonal pieces and amends the data conventions for the new
55-symbol dataset:

1. **A monthly momentum indicator family** in `indicators.py` — month-end total
   returns over k months, weighted/unweighted multi-horizon combinations (Keller's
   13612W/13612U), and the price-vs-monthly-SMA gap (Faber's filter as a score).
2. **A `rotation` strategy type** — `strategies/rotation.py` plus its `spec.py`
   grammar and sweep registration.
3. **Phase-0 data amendments** — resolving the 412 red tests the new data introduced,
   fixing four layout defects found during verification, and cutting the frozen
   snapshot the rotation work will run on.

`prices.py`, `simulate.py`, `stats.py`, `results_json.py` are untouched. The only
core-file change is additive factories in `indicators.py` (this spec is their
authorization). `SCHEMA_VERSION` stays 4; `SPEC_SCHEMA_VERSION` stays 1 — a new
strategy type is additive, and old code reading a new spec fails loudly on the
unknown `type`, which is the behavior we want.

Explicitly not in scope (§10): FRED macro ingestion (GTT/LAA), value-averaging
(9Sig), BAA's ranked defensive top-3, gate/vol-target composition with rotation,
synthetic pre-inception series. NTSX/RSSB/RSST/GDE static blends need **no new
features** — they are `fixed` strategies over the new data and can be tested the day
Phase 0 lands.

## 2. State of the repo at baseline — measured

Fresh clone, deps installed, full suite: **509 passed, 412 failed.** Every failure
is `tests/test_indicators.py::test_sma_matches_the_tradingview_column`, and every
failing parameter is a live `data/` or `data/price/` file from the new export batch.
Cause: the new exports carry the header `time,open,high,low,close,Volume` — the
Pine SMA overlay columns (`SMA50,SMA100,SMA200,SMA15`) are absent, and `CSV_FILES`
rglobs both roots. No code or frozen-snapshot regression: the commit touched
`data/` only, and every golden and invariant test passes.

Data verification, run across all 43 paired symbols in `data/` × `data/price/`:

- **Pair calendars identical** per symbol (except VIX/VIX3M, §3.4).
- **Adjustment ratio `R = A/P` monotone within noise, `R_last = 1.000000`
  everywhere.** The five leveraged ETFs show negative ln-steps from export
  quantization — worst −4.31e-08 (TQQQ, 2010-02-16), then QLD −2.07e-08,
  SSO −8.42e-09, UPRO −7.61e-09, SPXL −5.48e-09 — all far inside the established
  `TAU = 1e-6`. Not a data problem.
- **Implied distribution yields all land in plausible bands** (%/yr, full file
  history): HYG 6.23, PDBC 6.85, DBMF 5.80, EDV 4.85, KMLM 4.37, VNQ 4.29,
  LQD 4.13, VGK 3.57, UPAR 3.54, TLT 3.44, GDE 3.28, AGG 3.19, TIP 3.17, BND 3.16,
  VEA 3.01, NTSI 2.71, VEU 2.77, SCZ 2.71, EFA 2.67, ACWX 2.59, VWO 2.61,
  RPAR 2.48, TMF 2.13, SHY 1.90, EEM 1.90, RSSB 1.86, SPY 1.79, VTI 1.75,
  IWN 1.67, AVUV 1.58, RSBT 1.52, SPXL 1.47, BWX 1.45, BIL 1.39 (full-period
  average across the ZIRP years — plausible), EWJ 1.31, NTSX 1.20, IWM 1.17,
  DBC 1.13, BTAL 1.07, SSO 1.02, RSST 0.70, QLD 0.68, QQQ 0.62, UPRO 0.38,
  TQQQ 0.31.
- **History extended on refresh:** SPY now reaches 1993-01-29, QQQ 1999-03-10,
  EWJ 1996-03-18. Selected inceptions that gate strategy windows (§9):
  IWM 2000-05-26, IWN 2000-07-28, VTI 2001-05-31, EFA 2001-08-17,
  IEF/TLT/SHY/LQD 2002-07-26, EEM 2003-04-11, AGG 2003-09-26, TIP 2003-12-05,
  VNQ 2004-09-29, GLD 2004-11-18, VGK/VWO 2005-03-10, DBC 2006-02-03,
  XNDX 2006-11-08, VEU 2007-03-08, BND 2007-04-10, HYG 2007-04-11,
  BIL 2007-05-30, VEA 2007-07-26, BWX 2007-10-05, SCZ 2007-12-12,
  EDV 2007-12-13, ACWX 2008-03-31.
- **Note:** XNDX (Nasdaq-100 TR index) starts 2006-11-08 on TradingView, not
  1999 — the pre-2006 Nasdaq-100 TR series is QQQ's adjusted export itself
  (1999-03-10 on). Recorded for the future synthetic-TQQQ project.

Four layout defects, resolved in §3:

1. 412 red tests from SMA-less exports (§3.1).
2. `GLD`, `SPX`, `XNDX`, `UNRATE`, `RRSFS`, `INDPRO`, `DTB3` exist **only** under
   `data/price/`, which the loader never reads — GLD is untradeable and the
   signal series are unloadable as-is (§3.2, §3.3).
3. `data/VIX.csv` and `data/VIX3M.csv` end 2026-08-21 while their `price/` copies
   end 2026-08-24 — a stale-by-one-session drift between export batches; the
   forward-fill rule would silently serve three-day-old VIX on 08-22..24 (§3.4).
4. The FRED files are monthly observation-stamped series whose timestamps are not
   availability dates — loadable today only as a look-ahead bug (§3.3).

## 3. Phase 0 — data-convention amendments (prerequisite; suite green before feature work)

### 3.1 TV SMA-parity fixture scope

**Decision: the Pine SMA overlay is no longer part of the export procedure**, and
`test_sma_matches_the_tradingview_column` collects only files whose header carries
the SMA columns. Concretely: `CSV_FILES` keeps its rglob, and collection filters on
the header line containing `SMA200`.

Reasons: (a) the fixture's original job — proving `indicators.sma(n)` reproduces
TradingView — is permanently discharged by the frozen snapshots, which keep their
SMA columns and stay in scope; (b) a two-pass export of 48 paired symbols with a
chart overlay attached per pass is exactly the operator burden that produces
mismatched sessions, the error class the pair invariants exist to catch; (c) the
live-data guard duty transfers to §3.5, which is a stronger check on the columns
the engine actually reads. `data/README.md`'s export procedure drops the Pine
step; the within-file `time` monotonicity/duplicate asserts in `_read_close`
remain for every file.

### 3.2 Single-series symbols move to `data/` top level

`XNDX.csv` and `SPX.csv` move from `data/price/` to `data/` — they are indices
(XNDX has dividends embedded by construction, SPX excludes them by construction;
neither has a toggle), signal-only, and the loader resolves any read — traded,
`extra`, or indicator `inputs` — against `data/<SYM>.csv`.

`GLD` is traded (Golden-Butterfly-family references, future sleeves), has never
paid a distribution, and was correctly exported once. `data/GLD.csv` becomes a
byte-identical copy of `data/price/GLD.csv`, and the pair test asserts `R ≡ 1`
exactly — the identical pair *is* the invariant for a zero-distribution fund, and
it is precisely the check that fires if GLD ever starts distributing and a refresh
forgets the adjusted pass.

`data/README.md` gains a table of the three file classes: paired ETFs
(adjusted + `price/` twin), single-series indices at top level, and macro series
(§3.3).

### 3.3 FRED series are quarantined in `data/macro/`

`UNRATE.csv`, `RRSFS.csv`, `INDPRO.csv`, `DTB3.csv` move to `data/macro/`, which
the loader does not and must not read. These are not price series: UNRATE/RRSFS/
INDPRO are monthly observations stamped at the observation month (UNRATE from
1948-01-01) whose values are published ~1–5 weeks *after* that stamp and then
revised; DTB3 is daily on its own calendar. Loading any of them through
`load_prices` today would forward-fill a value from a date on which it was not
yet knowable — a silent look-ahead in every macro-gated backtest.

The ingestion convention (availability-date shift, monthly-to-daily carry rule,
revised-vintage caveat and its pre-registered +1-month conservative-lag check)
is the substance of a future `MACRO_DATA_SPEC` and is deliberately not decided
here. Until then the files are inert, and `data/README.md` says why in one loud
paragraph. GTT/LAA remain blocked on that spec.

### 3.4 VIX / VIX3M refresh

`data/VIX.csv` and `data/VIX3M.csv` are replaced by the newer exports currently
sitting at `data/price/VIX*.csv` (identical history, one extra bar 2026-08-24,
same session as the ETF batch), and the `price/` copies are removed — indices
have no pair, and a second copy that can drift is a standing trap; defect 3 is
the proof. The 58-holiday-artefact caveat in the README carries over unchanged.

### 3.5 Live-data pair invariants — the new standing guard

`tests/test_total_return.py` gains a live-data lane running over every
`data/<SYM>.csv` + `data/price/<SYM>.csv` pair (currently 44 with GLD):

- (a) identical `time` columns per pair;
- (b) `R` non-decreasing within `TAU = 1e-6` in ln, `R_last = 1` exactly to float
  print, flat between jumps;
- (c) per-symbol implied-yield bands from a committed table of the §2 measured
  values, band `[y·0.5, y·1.5]` — wide enough for slow drift as history appends,
  tight enough that a toggle-off export (`y ≈ 0`) or a double-adjusted one fails
  loudly. **Zero-distribution symbols are the exception, not a floor case:**
  GLD asserts `y < 1e-4` (with (a) making the pair bytewise-equal check nearly
  free). BIL is the positive control at the other end — nearly all of its return
  is distribution, its price series near-flat.

These run on live data by design — unlike the goldens, they guard *future
refreshes*, and a failure means the export is wrong, never that the band needs
loosening (the TOTAL_RETURN_SPEC rule: a ceiling that cannot be met is a finding).

### 3.6 Frozen snapshot and net-15 derivation

New append-only snapshot `tests/data/2026-08-24/`: verbatim copy of `data/`
(all symbols, both series, `macro/` included for provenance) plus a README with
export date, the measured yield table, and the §2 tolerances. Assert before
freezing that every *traded-class* ETF shares the last bar 2026-08-24 (they do
today; VIX/VIX3M after §3.4 do too).

`make_net_tr.py` derives `tests/data/2026-08-24-net15/` from the frozen pairs —
**the decision series for all rotation runs**, per the NET_TR_SPEC rule. The
stakes are larger here than in the safe-swap: withholding drag at w=0.15 is
~93 bp/yr on HYG, ~62 bp/yr on LQD, ~64 bp/yr on VNQ, ~52 bp/yr on TLT, ~48 bp/yr
on AGG, and ~0 on GLD — differential across exactly the assets a momentum ranking
compares, and of the same order as published TAA edges.

## 4. Monthly momentum indicators — `indicators.py` additions

All three factories follow the house rules: named, causal, computed on the loaded
`close` (so TR or net-TR by dataset), null during warm-up, month-end defined by
the `sma_monthly` rule — a row is a month-end iff its month differs from the next
row's, on the symbol's **own** bar calendar; the value on a month-end row includes
that day's close and is carried forward to every later row until the next
month-end (`join_asof` backward). The papers' "monthly closes" convention maps
onto the engine's existing one exactly: signals form at the month-end close, and
the engine trades at that same close (§6.6).

### 4.1 `mom_monthly(k)` → `MOM{k}M`

At month-end t: `close_t / close_{t−k month-ends} − 1`; null until k+1 month-ends
exist. `k >= 1`. GEM is k=12; ADM's defensive pick is k=1.

### 4.2 `mom_multi(months, weights=None)` → `MOMM{...}`

`sum_i w_i · (close_t / close_{t−m_i} − 1)` over month-end closes; `months` a
strictly ascending tuple of ints ≥ 1, `weights` positive floats of equal length,
or None for the unweighted mean. Null until max(months)+1 month-ends exist.

Name: `"MOMM" + "-".join(months)` + (`"U"` if unweighted else
`"W" + "-".join(weights rendered %g)`). So Keller's 13612W is
`mom_multi((1,3,6,12), (12,4,2,1))` → `MOMM1-3-6-12W12-4-2-1`, 13612U is
`mom_multi((1,3,6,12))` → `MOMM1-3-6-12U`, ADM's operator is
`mom_multi((1,3,6))` → `MOMM1-3-6U`. Ranking and sign are invariant to positive
scaling, so the weighted **sum** is the definition; Keller's published /4
normalizations differ by a constant factor only, which the spec notes once and
the labels ignore.

### 4.3 `sma_gap(m)` → `SMAGAP{m}M`

`close_t / SMA_mM(t) − 1` at month-ends, carried forward; reuses the
`sma_monthly(m)` window (m month-end closes, today's included). `m >= 2`.
Faber's 10-month filter is the sign of `sma_gap(10)`; BAA's SMA12 ranking
(13-point mean) is `sma_gap(13)`, deferred but expressible.

## 5. The `rotation` strategy — `strategies/rotation.py`

A `Strategy` subclass; no simulate/loader changes. The universe trick is the
SafeSwitch precedent: `weights` = every symbol the strategy can ever hold, all at
0.0, and `balance()` returns the full key set each rebalance day with 0.0 for the
unheld — `set(balance) == set(weights)` holds always, and day-0/warm-up capital
sits in cash.

Constructor: `assets` (offensive list), `k`, `score` (an Indicator from §4),
`filter_on: str | None`, `hurdle: str | None`, `filter_none: bool` (mutually
exclusive with the two above), `fallback` (None | symbol | sleeve dict |
`BestOf(symbols, score)`), `canary: Canary(symbols, breadth, score) | None`,
`label`, optional `rebalance` cadence.

### 5.1 Balance semantics — normative, in order

On a rebalance day (and on the contribution-only month-end branch, which calls
the same pure `balance()`):

1. **Warm-up short-circuit.** The required values are: the main score of every
   offensive asset, of `filter_on` if set, of `hurdle` if set; the canary score
   of every canary symbol; the fallback score of every `best_of` symbol. If
   **any** is None → return all-0.0 weights (all cash). Reason: a ranking over
   partial scores silently reorders the universe, and warm-up cash is loud in
   the allocations frame. The run's `start` should normally postdate warm-up
   (§9); the short-circuit is the safety net, not the plan.
2. **Canary fraction.** `n_bad = #{c in canary.symbols : canary_score(c) <= 0}`;
   `d = min(1, n_bad / breadth)`; without a canary, `d = 0`. Note `<= 0`, per
   Keller ("non-positive").
3. **Ranking.** Offensive assets sorted by score descending; **ties broken by
   `assets` list order** (deterministic; exact float ties are the degenerate
   case, but a pinned rule beats a hash-order surprise). Top-k selected.
4. **Qualification.** If `filter_none` is set: every top-k slot qualifies, no
   test at all (ranking without an absolute filter). Else if `filter_on` is
   set: one test for all slots — `score(filter_on) > (score(hurdle) if hurdle
   else 0)` (Antonacci's absolute-momentum-on-SPY form). Else per slot:
   `score(asset) > (score(hurdle) if hurdle else 0)`. Strict `>`.
5. **Allocation.** Each qualified slot's asset gets `(1−d)/k`; each unqualified
   slot's `(1−d)/k` joins the defensive pool. Pool = `d` + failed-slot mass.
6. **Defensive routing.** Pool to `fallback`: None → stays in cash; symbol →
   all of it; sleeve dict → by fractions (sum 1, validated); `best_of` →
   argmax of the fallback score over its symbols, ties by list order, all to
   the winner — no further sign filter, because listing BIL (or SHY) among the
   candidates *is* the floor, exactly as HAA uses it.
7. **Role collisions add.** An asset selected offensively and simultaneously
   the best defensive (IEF can be both in HAA-Balanced) accumulates weight.

`data` = the declared symbols not in `weights` (hurdle, filter_on, canary
symbols as applicable); `indicators` = the name-keyed per-symbol merge, exactly
the VolTarget pattern, so a canary sharing the main score declares it once.

### 5.2 What v1 deliberately does not compose

No `gate`, no vol-target interaction, no SafeSwitch fallback. Each is a real
combination someone will eventually want (a VT-sized TQQQ whose *safe sleeve* is
a rotation, say), and each multiplies the test surface; the catalog's Stage 1–2
strategies need none of them. If a rotation survives the anti-overfitting
protocol, composing it is its own spec with its own placebo design.

## 6. JSON grammar — `spec.py`

New entry in `_TYPES` and `REQUIRED_KEYS["rotation"] =
frozenset({"type", "assets", "k", "score"})`; optional keys
`{"filter", "fallback", "canary", "label", "rebalance"}`. Validation follows the
house rule: every error names the JSON path; unknown keys fail.

### 6.1 `score` object (shared by main, canary, best_of)

- `{"months": k}` — k int ≥ 1 → `mom_monthly(k)`;
- `{"kind": "avg", "months": [m1, m2, ...]}` — strictly ascending unique ints
  ≥ 1, length ≥ 2 → unweighted `mom_multi`;
- `{"kind": "weighted", "months": [...], "weights": [...]}` — same months rule,
  weights all > 0, equal length → weighted `mom_multi`;
- `{"kind": "sma_gap", "months": m}` — m int ≥ 2 → `sma_gap(m)`.

### 6.2 `filter`

`{"on": SYM?, "hurdle": SYM?}` — at least one key present (an empty object
fails: absence is the spelling of the default, per-asset > 0). `on` and
`hurdle` may be any symbol, including offensive assets; `on == hurdle` fails.

`{"kind": "none"}` is the unconditional form — every ranked slot qualifies,
no absolute test — and takes no other key (`on`/`hurdle` alongside `kind`
fail). It is a spelling absence cannot carry: in a sweep grid a `null` over an
optional key deletes it, which resolves to the per-asset default, not to
unconditional (SWEEP_SPEC §11.3). Ranking-without-a-filter is the relative
half of the dual-momentum decomposition, and `k = len(assets)` with it is a
monthly-rebalanced equal weight of the universe — the in-type static null.

### 6.3 `fallback`

`null` (cash, the default) | `"SYM"` | a sleeve dict (fractions > 0, sum 1,
≥ 2 symbols — the single-symbol dict fails with "use the string form", matching
`_safe`) | `{"kind": "best_of", "symbols": [...], "score": {...}?}` — symbols
≥ 2 unique (one symbol is the string form), score defaulting to the main score.

### 6.4 `canary`

`{"symbols": [...], "breadth": B, "score": {...}?}` — symbols ≥ 1 unique,
`1 <= B <= len(symbols)`, score defaulting to the main score. VAA-G4's
"any offensive negative → all defensive" is `symbols` = the offensive list,
`breadth` 1; DAA's fractional rule is `symbols` [VWO, BND], `breadth` 2; HAA's
is [TIP], 1.

### 6.5 Other validation

`assets` non-empty, unique, `1 <= k <= len(assets)`. `rebalance` reuses
`_rebalance` unchanged (papers are monthly, the engine default; the key exists
so the REBALANCE_SPEC-style cadence robustness check is expressible without a
grammar change). The normalised spec fills every default explicitly — including
inherited canary/best_of scores — so `results.json` stays byte-stable and
self-describing.

### 6.6 Execution-timing convention — documented deviation

Signals form on month-end TR closes and the engine trades at that same close;
several papers trade the next session (Keller: "trade on the first trading day
of the next month"). The engine keeps its existing single-close convention (the
SMA gate already works this way, and two conventions in one engine is how
windows become incomparable). The deviation costs one day's return per switch
and is direction-neutral; it goes in the strategy docs and in any comparison
against published tables.

## 7. Labels and sweep integration

`score_str`: `{"months":12}` → `12M`; avg → `1-3-6U` (and `1-3-6-12U`);
weighted `(1,3,6,12)/(12,4,2,1)` → the canonical `13612W`; other weighted →
`1-3-6-12w12-4-2-1`; sma_gap → `gap10M`.

Auto-label:
`ROT {A+B+…} top{k} {score}{filter}{canary} fb {fallback}{rb-suffix}` where
`filter` renders as `` (default), ` all` (unconditional — a word, so it takes
the separating space the operator forms do not), `>BIL`, `@SPY` (`on` without
hurdle), or `@SPY>BIL`; `canary` as ` can TIP/1` — score appended `@13612W`-style only when
it differs from the main score; `fallback` as `cash`, `AGG`,
`IEF60+TLT40`, or `best(BIL+IEF)` / `best(TIP+TLT@1M)`. Examples the tests pin:

- GEM: `ROT SPY+VEU top1 12M@SPY>BIL fb AGG`
- GTAA-5: `ROT SPY+EFA+IEF+DBC+VNQ top5 gap10M fb cash`
- ADM: `ROT SPY+SCZ top1 1-3-6U fb best(TIP+TLT@1M)`
- HAA-Balanced: `ROT SPY+IWM+VEA+VWO+VNQ+DBC+IEF+TLT top4 1-3-6-12U can TIP/1 fb best(BIL+IEF)`

Slug uniqueness is enforced by `build_bundle` as today. Sweep: the
`REQUIRED_KEYS` entry is the only mandatory change; `_param_value` gains
renderings for `("assets",)`, `("score",)`, `("filter",)`, `("canary",)` and
`("fallback",)` reusing the label fragments, so grid params stay hashable
strings, per the REGIME_SPEC precedent.

## 8. Tests

- **T1 — indicator units.** Synthetic frames with hand-computed month-end
  returns: `MOM{k}M` values at month-ends, carry-forward between them, null
  warm-up length exactly k month-ends; `MOMM` weighted sum against a hand
  calculation; `SMAGAP{m}M` consistency with `sma_monthly(m)`
  (`gap = close/SMA − 1` on every month-end row). Includes the own-calendar
  case: a symbol missing the calendar month-end uses its own last bar of the
  month, same as `sma_monthly` today.
- **T2 — GEM mechanics.** A hand-built fixture (three symbols plus hurdle,
  ~30 months) whose ranking, hurdle crossings and fallback transitions are
  hand-verifiable per rebalance day; assert the allocations frame's target
  weights row-by-row, including the absolute-on-SPY form vs the per-asset form
  differing on a constructed month.
- **T3 — canary and slot replacement.** Fractional breadth: n_bad = 1 of B = 2
  → exactly 50% defensive with the offensive half still top-k; n_bad = 2 → 100%.
  A slot failing per-asset qualification routes exactly `(1−d)/k` to the
  fallback; role collision (asset both offensive and best-defensive) sums.
- **T4 — warm-up.** A run starting before scores exist holds cash (allocations
  frame all-CASH) through the last None-score rebalance day and invests on the
  first warm one.
- **T5 — determinism.** Constructed exact tie → `assets` order decides; repeated
  runs byte-identical `results.json`.
- **T6 — grammar.** `build_bundle` round-trips the four §7 example specs;
  normalised spec fills inherited scores; loud failures for k > len(assets),
  duplicate assets, empty filter object, `on == hurdle`, single-symbol
  best_of/sleeve dict, breadth out of range, unknown score kind,
  months/weights length mismatch, non-ascending months.
- **T7 — labels/slugs.** The four pinned labels above; slug collision between
  two rotations differing only in structured params fails at build.
- **T8 — real-data golden.** The `default`-style bundle on
  `tests/data/2026-08-24-net15/`: GEM (EFA variant, §9 window), GTAA-5, and the
  SPY benchmark, `Config` window pinned, `GOLDEN_ROT` dict (final value, CAGR,
  max DD) to the cent — produced once by the implementation, eyeballed against
  direction (GEM's 2008–09 drawdown must undercut SPY's on the same window;
  its CAGR may not beat SPY's, per the out-of-sample literature — the golden
  pins whatever is measured). Same rule as every golden: a later failure means
  the engine changed; never refresh the snapshot to fix it.
- **T9 — Phase-0 data lane.** §3.5 invariants over live pairs; GLD `R ≡ 1` and
  `y < 1e-4`; BIL positive control; the SMA-parity fixture collects exactly the
  files carrying SMA columns (count asserted so silent scope shrink is loud);
  snapshot calendar cross-check against the previous snapshot's dates for the
  six original symbols (T6 of TOTAL_RETURN_SPEC, extended to the new date).

## 9. Windows the data supports — recorded, not decided

Earliest clean start = latest inception among a strategy's traded+signal symbols
plus score warm-up, rounded to a month-end:

| strategy | binding symbol | earliest score | practical start |
|---|---|---|---|
| GEM (SPY/VEU/AGG, hurdle BIL) | BIL 2007-05-30 | ~2008-06 | 2008-07 |
| GEM (SPY/EFA/AGG, hurdle BIL) | BIL 2007-05-30 | ~2008-06 | 2008-07 |
| ADM (SPY/SCZ, TIP/TLT) | SCZ 2007-12-12 | ~2008-06 (6m) | 2008-07 |
| GTAA-5 (SPY/EFA/IEF/DBC/VNQ) | DBC 2006-02-03 | ~2006-12 (10m) | 2007-01 |
| HAA-Balanced (8 assets, TIP canary) | VEA 2007-07-26 | ~2008-08 | 2008-09 |
| HAA-Simple (SPY, TIP canary, BIL/IEF) | BIL 2007-05-30 | ~2008-06 | 2008-07 |
| VAA-G4 (SPY/EFA/EEM/AGG + LQD/IEF/SHY) | AGG 2003-09-26 | ~2004-10 | 2004-11 |

Every strategy except VAA-G4 and GTAA-5 misses the 2008 top and all miss
2000–02 — the one-era caveat from the holdout-regime lesson applies with full
force, and published 1970s-onward numbers for these strategies rest on proxy
data this repo does not yet carry. A pre-2007 T-bill hurdle via DTB3 belongs to
`MACRO_DATA_SPEC`; mutual-fund/index proxies belong to a synthetic-history spec.
Neither blocks Stage 1: the 2007/2008-onward windows contain 2008-tail, 2011,
2015-16, 2018, 2020, 2022 and 2025 — enough regimes for the fit/holdout/
sensitivity protocol to say something falsifiable, and the pre-registered
expectation from the survey is *drawdown reduction without a CAGR win* for the
momentum family. A CAGR win over SPY would be the surprise to distrust first.

## 10. Out of scope

- **`MACRO_DATA_SPEC`** — availability-shifted monthly FRED ingestion, the
  DTB3 hurdle, GTT/LAA. Blocked-on, quarantine per §3.3.
- **9Sig** — value-averaging signal-line accounting and contribution modeling;
  a different simulation contract, reference-tier priority.
- **BAA's ranked defensive top-3 and SMA12 offense** — expressible additions
  (`best_of` top-n, `sma_gap(13)` as main score) once Stage-2 results justify a
  parameter-rich Stage-3 model; not before.
- **Rotation composed with gates / vol targeting / switches** (§5.2).
- **Synthetic pre-inception series** (XNDX/SPX/SPXTR-based; SPXTR itself not
  yet exported — SPX is price-only and must never seed a TR sim).
- **NTSX/RSSB/RSST/GDE/RPAR/UPAR testing** — no engine work; `fixed` strategies
  on the new snapshot, runnable immediately after Phase 0.

## 11. Implementation order

1. Phase 0 (§3): layout moves, fixture scope, live-pair invariants, snapshot +
   net15 — **suite green at the end of this phase**, 0 skipped-by-accident
   (T9's count assert).
2. §4 indicators + T1.
3. §5–§7 rotation type, grammar, labels, sweep keys + T2–T7.
4. T8 golden on the net15 snapshot; verdict work (sweep specs per strategy
   family, pre-registered thresholds) is **not** this spec — each family gets
   its own run spec with kill conditions, as with every sweep so far.

## 12. Errata

Measured during implementation; each item is recorded in the commit that
fixed it.

**Phase 0:**

1. **§2/§3.5 pair counts.** "All 43 paired symbols" measures **47** (§2 also
   undercounts its own yield list); "currently 44 with GLD" is **48**. The
   §3.5 universe pin is 48.
2. **§2 yield table omissions.** IEF (2.81 %/yr) and NTSE (2.85 %/yr) exist
   in both roots but are absent from the table; both are in the committed
   band table with bands derived the same way.
3. **§3.4 "identical history" is false for VIX.** On the shared dates,
   1,285 VIX closes differ between the pre-batch `data/VIX.csv` and the new
   export (all since 2021-05-21; 574 beyond ±0.01, four beyond 0.05, worst
   0.28 on 2023-06-07 — TradingView revisions/rounding). VIX3M is a true
   no-op (0 differing closes). Frozen snapshots keep their own VIX copies,
   so no pinned number moves; recorded in `data/README.md` and the
   2026-08-24 snapshot README.
4. **§3.1 leaves zero live files in the parity fixture.** The only live
   SMA-bearing files were the pre-batch VIX/VIX3M, which §3.4 replaces — the
   fixture collects 20 files (80 params), all frozen snapshots or the flat
   legacy CSVs. T9 pins that count.
5. **NET_TR_SPEC §2.1 `JUMP_MIN` re-pinned 2e-5 → 1e-5.** The 48-pair
   universe contains a genuine distribution below the six-symbol universe's
   floor: BIL 2009-11-02, ln-step 1.247e-5 (~$0.0011 ZIRP-era payout).
   Largest flat step is unchanged at 1.62e-6 (TQQQ), so the dead zone
   (5e-6, 1e-5) stays empty and asserted. The 2026-08-20-net15 derivative is
   byte-unchanged except its README's constant line (N5 regenerates it).

**Phase 2 (§4–§7):**

6. **§4 T1 gap: the causality lanes.** INDICATORS_SPEC §7 T2 obliges every
   new factory to join the look-ahead guard, which §8 T1 does not mention.
   The two monthly causality tests generalise to a `MONTHLY_INDICATORS`
   parametrised lane (t+2 truncation slack plus the strict ×1000 tamper
   check) that the three factories join.
7. **§7 filter rendering: on-without-hurdle is `@SPY>0`, not `@SPY`.**
   `@X` and `>X` slugify identically, so two rotations differing only in
   the filter's structure would collide at `build_bundle` — breaking the
   REGIME_SPEC §5.2 rule that auto-labels stay unique by construction. The
   explicit zero hurdle is also the semantics. None of the four pinned
   example labels use the form; they stand as written.
8. **§7 overstates the `_param_value` requirement.** `sweep.py`'s
   `json.dumps` fallback already keeps structured params hashable; the
   `("assets",)`/`("score",)`/`("filter",)`/`("canary",)`/`("fallback",)`
   renderings are for readability and label-consistency, not correctness.
9. **§5 "warm-up capital sits in cash" covers indicator warm-up only.**
   `prices.py` asserts every `weights` symbol has a close on every row from
   `config.start`, so the all-0.0 universe forces a run to start after the
   universe's latest inception — there is no cash-during-price-warm-up. The
   §9 window table already respects this; recorded in
   STRATEGY_DEVELOPMENT.md with the type's documentation.
