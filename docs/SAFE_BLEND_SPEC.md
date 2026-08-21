# Specification: safe-sleeve blends

Repo: `vlaas/balancing_portfolio` · baseline commit: `9695970` ("safe-swap merge", 403 tests green) · status: proposal

## 1. Goal

The safe-swap verdict's own follow-up: the safe arms win in **complementary
windows** — BTAL leads the risk-off windows (sens 2022-06, 2022-12), the
managed-futures arms lead the trend windows and the recent test window — which is
the textbook case for a *blend* rather than a swap. Today a blend is inexpressible
as a `vol_target`: `safe` is `str | null`, and a dict dies with a raw
`TypeError: unhashable type: 'dict'` (measured at `9695970`), not even a clean
validation error. Three parts:

1. **`vol_target.safe` extended to a weighted dict** — sleeve fractions, one small
   strategy/parser change, no engine change;
2. **two blend sweeps** on the existing lanes, which also carry the safe-swap
   verdict's other follow-up: the grid extension below σ 0.25 / w_max 0.5 that its
   edge flags demand;
3. a **dual-objective read** that makes the verdict's open value question — is the
   safe leg for drawdown protection or for return — explicit, from the same
   artefacts, at zero simulation cost.

All numbers below are from sandbox runs at `9695970` on
`tests/data/2026-08-20-net15`. No new data, no snapshot change, `SCHEMA_VERSION`
stays 4. Not in scope: §9.

## 2. `safe` as a weighted dict — normative

### 2.1 Grammar

`safe: str | null | dict[str, float]`, where the dict maps safe symbols to
**fractions of the safe sleeve** (not of the portfolio):

```json
{ "type": "vol_target", "risk": "TQQQ",
  "safe": { "BTAL": 0.5, "KMLM": 0.5 }, ... }
```

Validation, each failure a `ValueError` naming the JSON path:

- ≥ 2 keys — a one-key dict is rejected with "use the string form", so the same
  strategy can never exist under two spellings (and two labels);
- every key a symbol string, none equal to `risk`;
- every value > 0; values sum to 1 within 1e-9 — the sleeve is fully allocated.
  Blend-with-cash is deliberately inexpressible: `null` is the cash arm, and a
  partial-sum sleeve would smuggle a second cash definition into the arm taxonomy.

### 2.2 Semantics

`_allocation(w)` for a dict safe returns
`{risk: w} | {s: (1 − w) · f_s for each sleeve symbol}` — verified by hand:
`w = 0.4` with a 75/25 sleeve gives `{TQQQ: 0.4, BTAL: 0.45, KMLM: 0.15}`, sum 1.
Everything else follows from machinery that already exists and needs **no
change**:

- `weights` (the engine's universe assert) is `_allocation(fallback)`; all sleeve
  symbols are present on every rebalance day (weight 0.0 at `w = w_max = 1` is
  legal);
- monthly rebalancing restores the sleeve's internal proportions automatically —
  the blend is not buy-and-hold inside the sleeve, and that intra-sleeve turnover
  is real friction the cost model prices;
- **gate redistribution splits the blocked budget across the sleeve in sleeve
  proportion** — engine-side behaviour, verified hand-computed: a fully gated
  risk asset with a 3:1 sleeve yields exactly the 3:1 integer-share targets
  (1500/1250 shares on the synthetic fixture);
- exposure, imbalance, `results.json` blocks all key by asset and pick the third
  symbol up automatically.

### 2.3 Rendering — one shared `safe_str`

Factor `spec.safe_str(safe)`: a string renders as itself, `null` as `cash`, a
dict as sleeve symbols with integer sleeve-percentages, **sorted by symbol**,
joined by `+` — `BTAL75+KMLM25`. Sorted so the same blend written in different
key orders cannot produce two labels (and two slugs). Used by three consumers so
they cannot drift: the auto-label (`VT TQQQ/BTAL50+KMLM50 t30 w0-70
QQQ:VOL_EWMA80 gate QQQ<SMA200`), `sweep._param_value` for the `("safe",)` path
(the `params.safe` column reads `BTAL50+KMLM50`, not compact JSON), and the
summary tables. The `+` separator is deliberate: `fixed`'s `/` joins *portfolio*
fractions; `+` joins *sleeve* fractions — different semantics, different glyph.
The normalised spec embeds the dict as written (results.json's global key
sorting canonicalises it). The gate-universe check becomes
`{risk} | set(safe)` for the dict form. `REQUIRED_KEYS` and the null-grid rule
are untouched — a dict is an ordinary grid value, and `expand` already
substitutes objects (verified: the §4 template expands cleanly).

## 3. Tests — additions to `tests/test_vol_target.py`, `test_spec.py`, `test_sweep.py`

**T1 — Validation.** Dict safe with 2+ keys summing to 1 builds; one-key dict,
sum ≠ 1, value ≤ 0, key = risk, non-string key each raise `ValueError` with the
path; the string and null forms are byte-unchanged in the normalised spec
(regression).

**T2 — Rendering.** `{"KMLM": 0.25, "BTAL": 0.75}` labels as `BTAL75+KMLM25`
regardless of key order; explicit label wins; `params.safe` in a sweep equals the
label's sleeve component (assert both call `safe_str` — import identity, the
`gate_str` precedent).

**T3 — Allocation math.** With a stub σ: blend weights are
`{risk: w, s_i: (1−w)·f_i}` hand-computed for interior `w`, `w = w_min`,
`w = w_max = 1` (sleeve legs 0.0, keys present); fallback path; universe is all
three assets; `data`/`indicators` unchanged in shape.

**T4 — Engine redistribution.** The §2.2 synthetic fixture as a committed test:
gated risk, 3:1 sleeve, expected integer share targets asserted exactly.

**T5 — Sweep.** `safe: {"grid": ["BTAL", {"BTAL": 0.5, "KMLM": 0.5}, null]}`
expands to three entries with distinct labels and `params.safe` values
`BTAL` / `BTAL50+KMLM50` / `null`; slug uniqueness holds.

**T6 — End to end.** A blend strategy runs on the net snapshot through
`run_bundle`; `results.json` has three-asset `exposure` and embeds the dict in
the strategy `spec`.

**T7 — Goldens untouched** (suite invariant; no engine file changes at all).

## 4. Sweep specs

Both lanes reuse the safe-swap `config` verbatim (tastytrade base schedule with
`DBMF: 2.5`, `cash_yield` 0.03), `objective: calmar`,
`constraint: {max_drawdown: -0.50}`, λ 0.80, gate grid `{null, SMA200}` — and
both extend the numeric grids one step down per the edge protocol:
`sigma_target {0.20, 0.25, 0.30, 0.35, 0.40}`, `w_max {0.4, 0.5, 0.6, 0.7, 0.8}`.

### 4.1 `specs/sweep_blend_2021.json` — primary

Windows identical to `sweep_safe_2021.json` (start 2020-12-18, holdout
2025-01-01 with its short-test warning, 3y/6mo sensitivity → 9 windows,
verified). Safe grid, ten arms:

```json
"safe": { "grid": [
  "BTAL", "DBMF", "KMLM", null,
  { "BTAL": 0.75, "KMLM": 0.25 }, { "BTAL": 0.5, "KMLM": 0.5 }, { "BTAL": 0.25, "KMLM": 0.75 },
  { "BTAL": 0.75, "DBMF": 0.25 }, { "BTAL": 0.5, "DBMF": 0.5 }, { "BTAL": 0.25, "DBMF": 0.75 }
] }
```

Grid 10 × 5 × 5 × 2 = **500 points** (+ the safe-swap baselines and a
`TQQQ50/BTAL25/KMLM25` static blend twin, so the blends get their own VT-additivity
check). The four pure arms re-run on the extended grid inside the same artefact,
which is what resolves — or moves — the σ0.25/w0.5 edge flags with full
comparability. Three ratios per pair because `safe` is categorical (no numeric
neighbourhood): the ratio triple is the poor-man's flatness check — a blend whose
advantage exists at exactly one ratio is a curve-fit, and the read (§6) treats it
as such.

### 4.2 `specs/sweep_blend_2019.json` — the COVID check

Windows identical to `sweep_safe_2019.json` (start 2019-05-08, holdout
2024-01-01, 12 windows, verified). Six arms: `BTAL`, `DBMF`, `null`, and the
three BTAL+DBMF ratios — 300 points. The blend case *is* regime robustness, so it
must be tested in the lane whose fit window contains COVID and 2022 both. No
KMLM (inception), no 2012 rerun (no diversifier exists there; that lane's
BTAL-vs-cash verdict stands as committed).

Measured budget: ~4,550 + ~3,700 sims for the lanes, ~4,550 more for the
bracket — about 4–5 minutes single-process total.

## 5. Run protocol

```
uv run sweep.py specs/sweep_blend_2021.json --data tests/data/2026-08-20-net15 --out results/sweep_blend_2021_net
uv run sweep.py specs/sweep_blend_2021.json --data tests/data/2026-08-20       --out results/sweep_blend_2021_tr
uv run sweep.py specs/sweep_blend_2019.json --data tests/data/2026-08-20-net15 --out results/sweep_blend_2019
uv run sweep.py specs/sweep_blend_2021.json --data tests/data/2026-08-20-net15 --cost-bps 20 --cash-yield 0.03 --out results/sweep_blend_2021_c20
```

The bracket run keeps the withholding discipline — a blend inherits its
components' withholding differentials, so the KMLM/DBMF-heavy ratios sit closest
to their gross bound. The c20 stress is **not optional this time**: blends
rebalance three assets monthly, structurally the highest-turnover configuration
yet, with two 6 bp legs in the KMLM blends — the stress is aimed at exactly them.

## 6. Read protocol

Everything from the safe-swap read carries over (per-arm robust bests and
medians quoted with holdout warnings; withholding bracket direction-stability;
equal-risk exposure check — the VT rule is still safe-invariant so average TQQQ
weight must match across all ten arms; edge flags, now at σ0.20/w0.4, extend
again before believing). Added for blends:

1. **Blend vs best component**: a blend earns promotion only if it beats *both*
   of its components' arm-bests on `robust_score` in the primary lane **and**
   does not lose to its BTAL component in the 2019 lane — otherwise it is just
   the better component diluted.
2. **Per-window complementarity**: the §3 table redone with blend columns — the
   thesis predicts blends lose the *extremes* of both regimes but raise the
   window *minimum*; `rank_worst` is the single number that should improve most.
   A blend whose rank_worst is no better than its components' refutes the
   thesis regardless of its mean.
3. **Ratio flatness**: the winning pair's three ratios should score similarly;
   a spike at one ratio is treated as curve-fit and reported as such.
4. **Dual-objective table** — the verdict's handed-back decision, made explicit:
   from the primary lane's full-window `runs.csv` rows, a secondary ranking of
   feasible grid points by **shallowest max_drawdown subject to
   `cagr ≥ the gated 50/50 baseline's full-window cagr`**, top-15 arm
   composition quoted next to the Calmar table. Zero simulations, pure read. If
   the two objectives crown different arms, the verdict names both and the
   choice between them — what the safe leg is *for* — is made in the verdict
   sentence, in words, not implied by a metric.

Cross-artefact discipline: the blend sweep's extended grid changes
neighbourhoods and ranks, so its scores are **not** pooled with `sweep_safe_*`
numbers — the pure arms' re-runs inside this artefact are the only valid
comparison surface.

## 7. Honest limitations

- Three ratios per pair is a coarse ratio grid with no neighbourhood metric;
  §6.3 is a heuristic, not a flatness statistic. If a blend wins, a dedicated
  ratio refinement (finer grid, made a *numeric* dimension by restructuring the
  template) is the follow-up, not an extrapolation from three points.
- The blend thesis is fitted on the same 5.7 years that produced it — the
  complementary-windows observation *is* the training data. The 2019 lane is
  the only out-of-thesis check available; treat a primary-lane-only blend win
  accordingly.
- BTAL+KMLM blends still trade KMLM at 6 bp with a 3–38 bp real spread range;
  the c20 stress bounds this but monthly three-leg rebalancing at true KMLM
  spreads is the least certain cost in the system.

## 8. Acceptance checklist

- [x] `safe` dict form: validation per §2.1, `_allocation` per §2.2,
      `spec.safe_str` shared by label, `params`, and summary rendering
- [x] Tests T1–T7; whole suite green from a fresh clone with
      `pip install polars matplotlib pytest`
- [x] No change to `simulate.py`, `prices.py`, `indicators.py`, `stats.py`,
      `results_json.py`
- [ ] `specs/sweep_blend_2021.json`, `sweep_blend_2019.json` per §4
- [ ] The four §5 runs committed with the specs
- [x] Docs: STRATEGY_DEVELOPMENT (`safe` dict form, one paragraph + the sleeve
      semantics sentence); SWEEP_SPEC/SAFE_SWAP_SPEC cross-reference notes
- [ ] Verdict per §6 into project memory — including the dual-objective call —
      numbers stay in the repo

## 9. Deliberately not in scope

- **Ratio refinement as a numeric dimension** — fired only if a blend wins
  (§7); requires template restructuring so the ratio gets a real neighbourhood.
- **Diversifier-diversifier blends** (DBMF+KMLM): same family, not the
  complementary-regime thesis; nothing in the verdict argues for them.
- **Risk parity / covariance sizing of the sleeve**: the standing separate
  family — a blend with *fixed* sleeve fractions is deliberately the simplest
  structure that tests the complementarity thesis.
- **BIL, per-symbol withholding**: armed, untriggered, unchanged.
- **Three-way blends** (BTAL+DBMF+KMLM): 2^n arm growth for a hypothesis no
  lane has motivated; two-way results first.
