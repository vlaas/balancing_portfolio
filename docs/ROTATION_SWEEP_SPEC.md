# Specification: Stage-1 rotation sweeps — GEM, GTAA-5, HAA-Simple

Repo: `vlaas/balancing_portfolio` · baseline commit: `761ab57` (rotation merge, 626 tests green) · status: draft for review

All numbers in this spec are from sandbox runs on a fresh clone at `761ab57`, including
an independent recomputation of the T8 golden (TWR CAGR and max DD rebuilt from the
equity curves, matching `stats.py` to rounding: GEM 309,125.31 / 8.42% / −33.8%,
GTAA-5 199,414.05 / 4.25% / −14.0%, SPY 546,186.86 / 12.0% / −47.2% on
`2026-08-24-net15`, window 2008-07-01 → 2026-08-24).

## 1. Goal — and why this sweep's purpose is inverted

Every sweep so far asked "which parameters are good?". This one must not. GEM, GTAA-5
and HAA-Simple are **published strategies with pre-registered rules** — that is
precisely why they were staged first — and the moment a neighbor outscoring the
published point becomes a candidate, we have converted someone else's pre-registration
into our own in-sample fit. So, normatively:

**The only adoptable configuration per family is the as-published point.** The grid
exists to measure whether that point sits on a plateau (neighborhood as falsifier),
the sensitivity/holdout machinery to measure whether its behavior is regime-stable,
and the baselines to test whether its timing signal adds anything over a no-timing
static of the same ingredients — the anti-switcher lesson from SAFE_SWITCH applied to
momentum. A neighbor with a better `robust_score` is a *robustness datum about the
published point* (fragile if the published point is a local dip; reassuring if the
region is flat), never a promotion candidate.

Verdict tiers per the session's admission rule (strategies may lose on one axis and
stay as reference): PROMOTE / REFERENCE / DOCUMENT-ONLY / KILL, with numeric bars
frozen in §7 before any sweep runs.

Pre-registered expectations, written down now so the verdict cannot quietly move the
goalposts: per the out-of-sample literature, the momentum family should **reduce max
drawdown materially and lose to SPY on CAGR** (the golden already shows this shape:
−33.8% vs −47.2% DD, 8.4% vs 12.0% CAGR); the 2023-01 → 2026-08 holdout is a nearly
uninterrupted bull, where trend/momentum lags by construction, so a negative holdout
CAGR gap vs SPY is *expected* and is not a kill condition — failing to deliver the
drawdown edge is (§7 K2).

## 2. Pre-implementation: the unconditional filter form

Two ablation arms are currently inexpressible:

- **Relative-only GEM** (ranking without the absolute filter — the Antonacci
  decomposition: is all the crash protection in absolute momentum, as he claims?);
- **in-type statics** (`k = N`, no qualification = monthly-rebalanced equal weight of
  the universe).

The grammar has no "always hold the top-k": `filter` absent means per-asset `> 0`.
And a bare `null` cannot be the new spelling, because in a sweep grid `null` over an
optional key means *the key is deleted* (`sweep._substitute`), which resolves to the
default, not to unconditional. Therefore:

**Addition:** `"filter": {"kind": "none"}` — every ranked slot qualifies
unconditionally; `on`/`hurdle` are rejected alongside `kind`. Runtime: a
`filter_none: bool` on `Rotation` short-circuiting §5.1 step 4 (canary and warm-up
rules unchanged; with `kind: none` the main score of `filter_on`/`hurdle` drops out
of the required set). Label fragment: ` all` (e.g. `ROT SPY+VEU top1 12M all fb AGG`);
`_param_value(("filter",))` renders `"all"`. Normalised spec carries
`{"kind": "none"}` verbatim. Tests: grammar acceptance/rejection, label, a balance
test where a negative-momentum slot is held anyway, and a sweep-grid test proving
`{"grid": [{"kind": "none"}, {"on": "SPY", "hurdle": "BIL"}]}` produces both forms
(and that `null` in that grid still means absent-default — three distinct behaviors,
three distinct labels).

One more runner capability this spec depends on, to be pinned by a test rather than
assumed: a numeric grid **inside** the score object —
`"score": {"months": {"grid": [10, 12, 14]}}` — must register as dotted param
`score.months` with full one-step neighborhood semantics (SWEEP_SPEC §4.5 defines
neighbors for any numeric dimension; the existing rotation sweep test only covers a
grid over the whole score object, which is categorical).

## 3. Datasets, cost lanes, contribution schedule

- **Primary lane:** `tests/data/2026-08-24-net15`, `cost_bps` = the extended base map
  below, `cash_yield` 0.03. Decision-grade numbers come from this lane's committed
  `runs.json`/`summary.json` only.
- **Brackets** (§6, as-published points + baselines only, no grids): gross-TR
  (`tests/data/2026-08-24`, same costs) and cost-stress (`net15`, flat
  `{"*": 20}` bps).
- **Contributions:** house schedule, `initial_capital` 10 000, `monthly_contribution`
  500.

**Extended cost map** (per-side bps): the measured six keep their calibration
(SPY 0.7, QQQ 1, TQQQ 1.5, BTAL 6, KMLM 6, DBMF 3); the new tickers are **tiered by
liquidity class, not measured** — mega-liquid 1 (IEF, TLT, SHY, AGG, EFA, EEM, IWM,
VTI, BIL, LQD 1.5, VNQ 1.5, BND 1.5, VEA 1.5, TIP 2), standard 2–3 (VEU 2, VWO 2,
DBC 3, ACWX 3), thin 5–6 (SCZ 5, `"*"` 6). This is a modeling choice and the spec
says so: only the original six have NBBO-measured spreads (Round-Trip doc). The
uniform 20 bps bracket bounds any mis-tiering, and at these strategies' turnover
(GEM switched ~30 times in 18 years in the literature; one full switch/year ≈ 2
round-trip sides) a ±2 bp tier error moves CAGR by well under 1 bp/yr — recorded so
nobody later mistakes the map for data.

`cash_yield` 0.03 carries its standing contingency (idle USD at tastytrade earns ~0;
the yield assumes active SGOV/BIL parking). It is material here for the first time on
the *strategy* side: GTAA-5's published cash sleeve. The grid therefore carries
`fallback ∈ {null, "BIL"}` — BIL as a traded fallback is the more honest model (real
TR, real withholding) and removes the contingency from the verdict path.

## 4. Windows — and the warm-up collision that shapes the grids

House machinery throughout: `holdout: "2023-01-01"`, `sensitivity:
{every_months: 6, length_years: 5}`, objective `calmar`, constraint
`max_drawdown ≥ −0.50`.

**Native windows** (the crisis test — each family's earliest clean start per
ROTATION_SPEC §9):

- GEM, HAA-Simple: start **2008-07-01**. Binding chain: BIL first bar 2007-05-30 →
  13 month-ends → first `MOM12M` value 2008-05-30; the 2008-07 start is warm for
  every 12-month score.
- GTAA-5: start **2007-03-01** (not 2007-01): `sma_gap(12)` — the widest lookback in
  the grid — needs 12 DBC month-ends (first bar 2006-02-03) → first value
  2007-01-31; starting 2007-03 keeps every grid point warm from its first rebalance,
  so no point spends its opening months in the §5.1.1 cash short-circuit.

**The collision:** on the GEM native window a `months = 14` neighbor would need 15
BIL month-ends → first value 2009-07-31 — i.e. the neighbor sits in warm-up cash
through the entire crash, printing an artificially shallow drawdown and corrupting
the neighborhood comparison. This is data-bound (BIL's 2007 inception), not a design
choice, so the resolution is split by lane:

- **Native lane: `months` fixed at the published 12.** Only categorical dimensions
  vary; `robust_score` there degrades to `min(full, sens median, holdout test)` —
  documented, expected.
- **2012 lane (start 2012-01-03, the incumbents' anchor): full grid including
  `months {10, 12, 14}`**, all warm years before the window. This lane carries the
  numeric plateau test *and* the comparability read against the reigning
  B75K25/B50K50 machine (context only — §7 explicitly bars cross-family promotion
  arithmetic, different mechanism, different data era).

Native-lane sensitivity spans ≈ 2008–2021 starts (~28 rolling 5y windows for GEM,
~30 for GTAA); fit = start → 2022-12, test = 2023-01 → 2026-08 (3.6y, above the 2y
warning line).

## 5. Family sweeps — grids, published points, baselines

Six spec files: `specs/sweep_rot_{gem,gtaa,haa}_{native,2012}.json` (native = 2008 /
2007-03 / 2008 respectively). Baselines are never ranked; SPY last (benchmark slot).
The **as-published point** is marked here and in the verdict doc; it is always an
interior or explicitly-edge-noted grid member.

### 5.1 GEM (Antonacci dual momentum)

Template (`k` 1, fallback `"AGG"` fixed):

- `assets`: grid `[["SPY","VEU"], ["SPY","EFA"], ["SPY","ACWX"]]` — published
  universe is US + all-world-ex-US (VEU/ACWX both proxy it; EFA is the
  developed-only variant common in replications). Categorical.
- `score`: native lane `{"months": 12}` fixed; 2012 lane
  `{"months": {"grid": [10, 12, 14]}}`.
- `filter`: grid `[{"on": "SPY", "hurdle": "BIL"}, {"hurdle": "BIL"}]` — the
  published absolute-on-SPY form vs the winner-qualifies variant replications
  disagree on. Categorical.

Native 6 points, 2012 lane 18. **Published point:** `SPY+VEU, 12, @SPY>BIL`.

Baselines: `fixed` 60/40 SPY/AGG (the null the OOS literature says GEM lost to);
`fixed` ⅓/⅓/⅓ SPY/VEU/AGG (equal-weight-of-ingredients null); rotation
`[SPY] k1 @SPY>BIL fb AGG` (absolute-only ablation — Antonacci's claimed engine);
rotation `SPY+VEU top1 12M all fb AGG` (relative-only ablation, §2 form); `fixed`
SPY benchmark last.

### 5.2 GTAA-5 (Faber)

Template (`assets` fixed `["SPY","EFA","IEF","DBC","VNQ"]`, `k` 5):

- `score`: `{"kind": "sma_gap", "months": {"grid": [8, 10, 12]}}` — published 10,
  two-sided, warm on both lanes per §4.
- `fallback`: grid `[null, "BIL"]` — published "cash/T-bills"; BIL is the traded
  spelling, `null` the cash-yield spelling. Categorical.

6 points per lane. **Published point:** `gap10M, fb BIL` (primary spelling of the
published rule; the `null` twin measures the cash-yield-model delta).

Baselines: `fixed` 20%×5 equal weight (the no-timing null — GTAA's entire published
claim is that the per-asset trend filter beats holding the five); `fixed` SPY
benchmark last.

### 5.3 HAA-Simple (Keller & Keuning)

Template (`assets` `["SPY"]`, `k` 1):

- `score`: grid `[{"kind":"avg","months":[1,3,6,12]},
  {"kind":"weighted","months":[1,3,6,12],"weights":[12,4,2,1]}, {"months":12}]` —
  published 13612U, Keller's own 13612W, and plain 12M. Categorical. Canary and
  best-of scores inherit the main score, which is faithful at the published point
  (Keller uses one operator throughout) and sweeps coherently elsewhere — noted.
- `canary`: grid `[{"symbols":["TIP"],"breadth":1}, null]` — the canary ablation
  rides inside the grid (`null` = key deleted = no canary, existing semantics).
- `fallback`: grid `[{"kind":"best_of","symbols":["BIL","IEF"]}, "IEF"]` —
  published best-of vs fixed-IEF.

12 points per lane. **Published point:** `13612U, canary TIP/1, fb best(BIL+IEF)`.

Baselines: `fixed` 60/40 SPY/IEF; `fixed` SPY benchmark last. (The no-canary
ablation is already a grid axis; the all-cash degenerate is not worth a slot.)

Compute check: the largest lane is HAA-2012 at 12 points × ~25 windows ≈ 300
simulations ≈ 35 s at the measured ~0.11 s/run — all six files together stay under
ten minutes single-process.

## 6. Bracket runs

One bundle spec, `specs/rot_points.json`: the three as-published points, the five
GEM/GTAA/HAA baselines above (deduplicated), SPY last; native-window start compromise
is not needed — brackets run per family window is overkill; **decision: brackets run
on the common 2012-01-03 window**, where all points are warm and the incumbent
context lives. Executed twice:

- `--data tests/data/2026-08-24` (gross-TR bracket, cbase costs) — the tax bracket;
- `--data tests/data/2026-08-24-net15` with the flat-20 config twin
  `specs/rot_points_c20.json` — the cost bracket.

Committed artefacts: both `results.json` files under `results/rot_points_*`, next to
the six sweeps' `runs.json`/`summary.json`.

## 7. Pre-registered verdict procedure

All conditions evaluate the **as-published point, primary lane, native window**
unless stated. SPY numbers are the same lane's baseline row. Frozen before any sweep
executes; the verdict doc (`notes/rot-verdict.md`) quotes them verbatim and fills a
table, one row per condition, PASS/FAIL, no prose re-litigation.

- **K1 — null dominance (kill):** the family's no-timing static (60/40 for GEM and
  HAA-Simple, EW-5 for GTAA) beats the published point on *both* full-window CAGR
  and max DD → **KILL** the family (the anti-switcher pattern: the signal calendar
  carries no information the static doesn't).
- **K2 — insurance that doesn't insure (kill):** holdout-test max DD worse than
  SPY's *and* holdout-test CAGR below SPY's *and* full-window max-DD edge over SPY
  under 5 points → **KILL**.
- **R1 — does the published job:** full-window max DD better than SPY's by ≥ 10
  percentage points.
- **R2 — timing adds information:** full-window Calmar > the no-timing null's, and
  holdout-test Calmar ≥ the null's holdout-test Calmar.
- **R3 — not a spike:** `robust_score` ≥ 0.75 × own full-window objective; on the
  2012 lane, the published point's full objective ≥ 0.85 × the best grid point's
  (a neighbor may score higher — by less than 15%, or the published rule is a
  fluke of its own parameters).
- **Brackets:** the R1 max-DD edge retained (≥ 10 points) under both §6 brackets.

Tiers: **PROMOTE** = R1 ∧ R2 ∧ R3 ∧ brackets ∧ full-window CAGR ≥ SPY's.
**REFERENCE** = R1 ∧ R2 ∧ R3 ∧ brackets (CAGR condition waived — the expected
outcome for this family). **DOCUMENT-ONLY** = anything else short of a kill.
Ablation arms (absolute-only, relative-only, no-canary) are never tiered; their job
is one sentence each in the verdict: where the drawdown protection lives.

Explicitly barred: promoting a non-published grid point; using the 2012-lane
incumbent comparison (B75K25/B50K50 rows from `winners.json`, quoted for context)
as a promotion axis — complementarity analysis (active-return correlation against
the incumbents) is follow-up work on the committed curves, not part of this verdict.

## 8. Stage 2 — defined now, gated on Stage 1

Run only after the Stage-1 verdict doc is merged, unchanged machinery:

- **ADM** (native 2008-07): `assets ["SPY","SCZ"]`, `k` 1, score
  `{"kind":"avg","months":[1,3,6]}` (grid: that ±{[1,3],[1,3,6,12]} categorical),
  fallback `{"kind":"best_of","symbols":["TIP","TLT"], "score":{"months":1}}`;
  null: 60/40 SPY/TLT. SCZ tier-5 cost note applies.
- **HAA-Balanced** (native 2008-09): `assets` the published G8, `k` 4, score
  13612U, canary TIP/1, fallback best(BIL+IEF); grid only over
  `k {3, 4, 5}` and the §5.3 score triple; null: EW-8.
- **VAA-G4** (native 2004-11, the longest window): reference-tier from the start
  per the survey's OOS findings; grid = published point only + nulls.

## 9. Tests

- **T1 — filter none** (§2): grammar, label, balance semantics, sweep-grid
  three-way distinction.
- **T2 — nested numeric score grid:** `score.months` grid registers as a numeric
  dimension: dotted param present, neighbors and `edge` computed (synthetic 3-point
  grid with known objectives).
- **T3 — spec files parse:** all six sweep files and both bracket bundles
  `--dry-run` clean with the expected expansion counts (6/18, 6/6, 12/12; brackets
  9 strategies); every as-published label matches the frozen string in the verdict
  doc skeleton.
- **T4 — warm-start invariant:** on each native window, the first rebalance day of
  every grid point allocates (no all-cash row) — the §4 warm-up analysis asserted,
  not trusted.
- **T5 — baseline immunity:** baselines appear in every window's runs with
  `is_baseline` true and never in ranks (existing behavior, re-asserted on a
  rotation sweep).

## 10. Out of scope

Return-stacked statics (NTSX/RSSB/RSST/GDE — a plain bundle spec whenever wanted,
no dependency on this work); GTT/LAA (blocked on `MACRO_DATA_SPEC`); BAA and the
ranked defensive top-3; pre-2007 T-bill hurdles (DTB3); synthetic pre-inception
history; any composition of rotation with gates or vol targeting; complementarity
tooling (active-return correlation reports).

## 11. Run order and deliverables

1. §2 grammar addition + T1/T2 (engine work, small).
2. Commit the six sweep specs + two bracket bundles + the verdict-doc skeleton with
   the §7 table and frozen labels — **the pre-registration commit, before any run**.
3. Execute native lanes, then 2012 lanes, then brackets; commit
   `results/sweep_rot_*/{runs.json,summary.json}` and `results/rot_points_*`.
4. Fill `notes/rot-verdict.md` strictly from committed artefacts; verdict PR.
