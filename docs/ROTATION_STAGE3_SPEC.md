# Specification: Stage-3 rotation sweeps — BAA-G4 and BAA-G12

Repo: `vlaas/balancing_portfolio` · baseline commit: `cfbce5f` (Stage-2 verdict
merge, 679 tests green) · status: draft for review · predecessors:
`docs/ROTATION_SWEEP_SPEC.md` (+§12), `docs/ROTATION_STAGE2_SPEC.md`,
`notes/rot-verdict.md`, `notes/rot2-verdict.md`

All numbers below are from sandbox runs on a fresh clone at `cfbce5f`: the Stage-2
verdict's headline numbers were independently recomputed from committed artefacts
before this spec was written (all reproduce, including the exact `robust_score` /
`neighbour_min` tie to the last digit), and every window and inception below was
measured against `tests/data/2026-08-24-net15`.

## 1. Goal

Run Keller & Keuning's Bold Asset Allocation — BAA-G4 and BAA-G12 (SSRN 4166845,
July 2022) — as the rotation program's deliberately **last** increment. The gate in
ROTATION_SWEEP_SPEC §10 ("Stage-2 results first") is opened knowingly: after six
published points produced one REFERENCE and five DOCUMENT-ONLYs, BAA is run not
because the odds improved but because the program should finish its catalog before
the composition work begins, and because BAA is the one family whose mechanics —
ranked defensive selection with a cash floor — the engine cannot yet express, so
testing it also completes the rotation feature set.

The inverted purpose holds: **the only adoptable configurations are the two
as-published points**; grids are falsifiers, nulls are the no-timing statics.

Pre-registered expectations — the most skeptical of the program, written before any
run: BAA was fit by its authors through June 2022 over a 1970–2022 sample;
Allocate Smartly flagged its complexity and preferred HAA; it spends roughly 60%
of months in its defensive universe, so the 2023-01 → 2026-08 bull holdout will
punish it on exactly the R2 clause that stopped all three Stage-2 families; and
Stage-2 residual 3 says its canary operator (13612W) is the weaker momentum form
on this data everywhere it has been tested. Expected outcome: DOCUMENT-ONLY for
both. The program-level question this stage actually answers is narrower and more
useful: **does anything in BAA's added machinery — ranked defensive top-3, the BIL
floor, the aggressive G4 offense — outperform the already-adopted HAA-Simple
reference on the same lanes?** A strong BAA result should be distrusted first
(§1 of Stage 1, unchanged).

## 2. Engine feature: ranked defensive selection with a floor

BAA's defensive rule: route the defensive pool to the **top-3** of
{TIP, DBC, BIL, IEF, TLT, LQD, AGG} by the ranking score, **replacing any selected
asset whose momentum is below BIL's with BIL**. The current `best_of` picks top-1
with no floor. Addition, backward-compatible:

```
"fallback": {"kind": "best_of", "symbols": [...], "n": 3, "floor": "BIL",
             "score": {...}?}
```

- `n`: int, `1 ≤ n ≤ len(symbols)`, default 1 (existing behavior unchanged).
- `floor`: optional symbol, **must be a member of `symbols`** (keeps the score
  set closed; BIL is a member in BAA). Absent = no floor (existing behavior).
- Semantics, normative: rank `symbols` by the fallback score descending, ties by
  list order; select the top-`n`; split the defensive pool equally, `pool/n` per
  slot; if `floor` is set, any selected symbol whose score is **not strictly
  greater than** the floor symbol's score routes its slice to the floor instead
  (strict `>` to keep, matching the engine's qualification convention; the floor
  selected on its own merits trivially routes to itself; floor mass accumulates).
- Label: `best{n}(A+B+…)` when n > 1, floor rendered as a hurdle:
  `best3(TIP+DBC+BIL+IEF+TLT+LQD+AGG>BIL)`. `n = 1` without floor keeps the
  existing `best(A+B)` rendering byte-for-byte (golden-label stability).
- Warm-up: the fallback score of every member is already in the §5.1 required
  set; unchanged.
- `_param_value(("fallback",))` renders the same fragment; normalised spec fills
  `n` explicitly.

Note what is *not* needed: BAA's offense has **no per-asset absolute filter** —
the canary is the all-or-nothing absolute mechanism and the TopX are held
regardless of sign — so the offense uses `filter: {"kind": "none"}`, the form
built for Stage-1's ablations. Unlike VAA-G4, the inertness argument does not
apply here (canary ≠ offensive universe: an offensive asset can be negative while
all four canaries are positive), so the explicit `none` is a fidelity
requirement, not an option. The canary carrying a different score than the
ranking (13612W vs `sma_gap(13)`) is already supported.

## 3. Cost-map amendment

Measured against the Stage-2 spec files: **HYG, GLD, EWJ and VGK are absent from
the extended cost map and fall to the `"*"` 6 bp tier.** GLD and HYG are among
the most liquid ETFs in the program; at BAA-G12's turnover a 5 bp overcharge on
two core holdings is material and one-directional. Amendment, same
tier-by-liquidity-class basis as Stage 1 (a modeling choice bounded by the
flat-20 bracket, not a measurement): **GLD 1, HYG 1, VGK 2, EWJ 2.** All other
entries unchanged; the amendment applies to the Stage-3 spec files only (earlier
results are frozen artefacts and no Stage-1/2 strategy trades these symbols).

## 4. Pre-flight — dual window check, measured

| family | max traded inception | binding score, first value | native start |
|---|---|---|---|
| BAA-G12 | BIL 2007-05-30 (12 offensive + 7 defensive) | canary `13612W` on VEA → **2008-07-31** | **2008-08-01** |
| BAA-G4 | VEA 2007-07-26 (4 offensive + 7 defensive) | canary/ranking on VEA → **2008-07-31** | **2008-08-01** |

Both native windows coincide with HAA-Balanced's, which makes the three
Keller-family results directly comparable on identical lanes. The G12 binding
constraint is notable: it is the *canary's* VEA (a data-only symbol), not any
traded asset — the exact silent-failure class the dual check exists for. Ranking
scores are warm earlier everywhere (`sma_gap(13)`: HYG 2008-04-30, BIL
2008-05-30, all others 2006 or before). The grid's alternative canary operator
(`13612U`, §5) has the same 13-month-end warm-up on the same symbols, so the
axis does not move the window. 2012 lanes start 2012-01-03 as always.

## 5. Family definitions

House settings inherited unchanged (net15 primary + §3-amended cost map,
`cash_yield` 0.03, holdout 2023-01-01, sensitivity 6/5, `calmar`, DD ≥ −0.50,
10 000 + 500/mo). Four sweep files:
`specs/sweep_rot3_{baa12,baa4}_{native,2012}.json`.

### 5.1 BAA-G12

Template: `assets ["QQQ","SPY","IWM","VGK","EWJ","VWO","VNQ","DBC","GLD","TLT",
"HYG","LQD"]`; `filter {"kind":"none"}`; score `{"kind":"sma_gap","months":13}`
(Keller's SMA12 — thirteen month-end closes including the current one); `canary
{"symbols":["SPY","VEA","VWO","BND"],"breadth":1}`; `fallback
{"kind":"best_of","symbols":["TIP","DBC","BIL","IEF","TLT","LQD","AGG"],"n":3,
"floor":"BIL"}` (score inherits the ranking `sma_gap(13)`, which is faithful).

Grid: `k {"grid":[5,6,7]}` (numeric, published 6 interior) × canary score
`{"grid":[13612W, 1-3-6-12U]}` (categorical; the published operator against the
one Stage-2 found stronger in all four tested arms) = **6 points per lane**.

**Published point:** `ROT QQQ+SPY+IWM+VGK+EWJ+VWO+VNQ+DBC+GLD+TLT+HYG+LQD top6
gap13M all can SPY+VEA+VWO+BND/1@13612W fb best3(TIP+DBC+BIL+IEF+TLT+LQD+AGG>BIL)`.

Baselines: `EW-12` of the offensive universe (K1 null), the HAA-Simple published
point (context row, warm well before 2008-08, never tiered), `SPY benchmark`
last.

### 5.2 BAA-G4

Template: `assets ["QQQ","VWO","VEA","BND"]` (the "aggressive" G4 — QQQ in place
of SPY), `k` 1, `filter {"kind":"none"}`, canary and fallback exactly as G12.

Grid: ranking score `{"grid":[sma_gap13, 1-3-6-12U]}` × canary score
`{"grid":[13612W, 1-3-6-12U]}` = **4 points per lane**. (When the ranking score
is swept, the fallback score sweeps with it by inheritance — the same noted,
acceptable coupling as HAA.)

**Published point:** `ROT QQQ+VWO+VEA+BND top1 gap13M all can
SPY+VEA+VWO+BND/1@13612W fb best3(TIP+DBC+BIL+IEF+TLT+LQD+AGG>BIL)`.

Baselines: `EW-4` `QQQ25/VWO25/VEA25/BND25` (K1 null), the HAA-Simple point
(context row), `SPY benchmark` last.

Surfaces: 6 + 6 + 4 + 4 = 20 grid points plus baselines — the smallest stage
yet, as befits the most parameter-rich model: the grid is not there to explore
BAA's parameter space (the paper already did, in-sample, for 52 years) but to
ask the two questions Stages 1–2 sharpened: does concentration matter (`k`), and
does the canary operator survive contact with residual 3.

## 6. Verdict procedure

Stage-1 §7 with R3a′, applied verbatim — **R2 is deliberately kept unchanged**.
Amending its holdout clause now, with full knowledge of exactly which clause
stopped three families, would be fitting the bar to the desired outcome; the
comparability of all eight published points under identical frozen bars is worth
more than a ninth tier. The clause's known miscalibration stays recorded where
Stage 2 put it (residual 1), and its resolution remains the bear holdout that
synthetic-history work would provide.

One addition, explicitly **non-tiering**: a diagnostic row **R2d — insurance
delivered in the holdout** — holdout-test max DD of the published point vs the
K1 null's, reported for both Stage-3 points *and* recomputed for all six prior
published points in the verdict's context section. It is the input to the future
bar redesign that accompanies a bear holdout, collected now while the lanes are
identical; it moves no tier this stage.

K1 nulls: `EW-12` (G12), `EW-4` (G4). The HAA-Simple context row carries the
same pre-registered reading as Stage 2's: relevant only as the family-incumbent
comparison, with the note that after Stage 2 the bar for displacing HAA-Simple
is `robust_score` on both lanes *and* full CAGR — no BAA point may be adopted
past it on any lesser showing, and none may be adopted at all except the two
published coordinates.

Verdict doc `notes/rot3-verdict.md`, Stage-2 skeleton: fitted-surface
accounting, frozen labels, condition table (K1, K2, R1, R2, R3a′, R3b, B, +R2d
diagnostic), supporting numbers with holdout `test` and `rank_median`, brackets,
ablation sentences (the `k` axis; canary 13612W vs U — residual 3's fourth and
fifth data points; G4-vs-G12 concentration; BAA-vs-HAA-Simple), decision,
residuals.

## 7. Brackets

`specs/rot3_points.json`: the two published points, both K1 nulls, HAA-Simple,
`SPY benchmark` last (6 rows), 2012-01-03 window; executed gross-TR
(`tests/data/2026-08-24`, §3-amended cbase) and flat-20
(`specs/rot3_points_c20.json`, net15). Condition B reads these. Given Stage-2
residual 6 (the canary-equals-universe rule made VAA the turnover outlier), the
bracket table adds one pre-registered row: **flat-20 CAGR cost** per point, so
BAA's all-or-nothing canary — the same binary flip mechanism — is costed in the
open next to VAA's 3.68 points.

## 8. Tests

- **T1 — grammar.** `n`/`floor` validation: acceptance of the BAA form;
  rejections for `n > len(symbols)`, `n < 1`, floor not a member, floor with
  `n` absent-defaulting; normalised spec fills `n`; `best(A+B)` rendering
  unchanged for `n = 1` (existing golden labels byte-stable).
- **T2 — floor semantics.** Synthetic fixture: top-3 split `pool/3` each; one
  selected symbol at exactly the floor's score routes to the floor (strict `>`);
  two below-floor selections accumulate `2·pool/3` on BIL; floor itself
  selected routes to itself.
- **T3 — spec parse and counts.** Four sweep files expand 6/6/4/4; both bracket
  bundles parse; published labels render exactly as §5 writes them and match
  the verdict skeleton (frozen label lists, §12-3 precedent).
- **T4 — warm-start assertion.** Every grid point on both native lanes
  allocates at its first rebalance day — the check that has now caught four
  window defects across three stages, including this stage's data-only VEA
  canary binding.
- **T5 — R3a′/R2d inputs.** `rank_median` present per point per lane; holdout
  `test` max-DD fields present for the R2d rows.
- **T6 — filter-none fidelity.** A G12-shaped fixture where an offensive asset
  with negative `sma_gap` is ranked top-6 while all canaries are positive: the
  asset is held (BAA rule), and the same fixture under the default filter would
  route it defensively — pinning that the `none` form is load-bearing here.

## 9. Run order

1. §2 feature + §3 cost amendment + T1/T2/T6.
2. **Pre-registration commit**: four sweep specs, two bracket bundles,
   `notes/rot3-verdict.md` skeleton with frozen labels, §6 procedure including
   the R2d diagnostic definition and the displacement bar.
3. Native lanes, 2012 lanes (T4 asserts on native), brackets.
4. Commit `results/sweep_rot3_*` and `results/rot3_points_*`; fill the verdict
   from committed artefacts only; verdict PR closes the rotation catalog.

## 10. Out of scope, and what follows

The ranked-defensive feature is scoped to `best_of` — no offensive top-n
weighting schemes, no defensive canaries. GTT/LAA stay blocked on
`MACRO_DATA_SPEC`; synthetic pre-inception history remains the standing data
need (it is the resolution path for R2's holdout tension and for the program's
one-era caveat, and it is deliberately *not* started here). Per the agreed
sequence, the next increment after this stage's verdict is the **composition
spec** — the multi-horizon score as an alternative or OR-combined gate on the
incumbent TQQQ machine — which begins in a fresh conversation with this stage's
verdict as its input.
