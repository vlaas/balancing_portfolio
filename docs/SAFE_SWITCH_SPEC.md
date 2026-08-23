# Specification: regime-conditional safe sleeve

Repo: `vlaas/balancing_portfolio` · baseline commit: `600f3a3` ("regime-gate
merge", 535 tests green) · status: **implemented; nothing adopted** — the §6.3
placebo fired in every artefact
([notes/safe-switch-verdict.md](../notes/safe-switch-verdict.md)) · errata: §9

## 1. Goal

Test the hypothesis left standing at the junction of two verdicts. The
safe-blend verdict confirmed complementarity — BTAL leads the risk-off windows,
the managed-futures arms lead the trend windows — and resolved it *statically*,
with a BTAL-heavy sleeve held at all times. The regime verdict built and
retained tested condition machinery (SMA state, VIX/VIX3M `ts_regime`) but
found it useless *as a gate*. The untested combination: hold the MF-heavy
sleeve in the risk-on regime and rotate to the BTAL-heavy sleeve when the
condition fires — timing the sleeve *composition*, not the risk weight.

Machinery audit at `600f3a3`, this sandbox:

- **Static sleeves exist** (`safe` as a weighted dict, SAFE_BLEND) and both
  condition families exist, tested and causal, on both decision-grade
  snapshots.
- **The conditional sleeve is inexpressible.** A switch-shaped `safe` value
  dies in validation (`safe.kind: expected a fraction > 0, got 'switch'` —
  measured). The only adjacent mechanism, a `w_off` gate listing a safe asset,
  has *inverted* semantics: `clip` redistributes the clipped weight pro rata
  across all non-gated assets **including the risk asset** — on a risk-off
  close with `assets: ["KMLM"]`, `w_off: 0`, a `{TQQQ: 0.40, BTAL: 0.15,
  KMLM: 0.45}` allocation becomes `{TQQQ: 0.727, BTAL: 0.273, KMLM: 0}`
  (measured). A risk-off signal that buys TQQQ is not the hypothesis; there is
  also no "inverted" gate to tilt *toward* MF while risk-on.
- **One enabling fact**: a `Gate` constructed with `assets=[]` is already a
  pure condition — `closed()` works, `buy_cap` returns `None` for every asset,
  `clip` is the identity (measured). The runtime needs no new condition class.

So: one grammar/strategy extension (§2), then two sweep lanes (§4) whose read
protocol (§6) is built around the overfitting problem this hypothesis
maximally invites — a conditional structure with more parameters, fitted on
the same 5.7 years that produced the complementarity observation, switched by
signals whose entire monthly information content is **13–44 month-ends in
fourteen years** (§4.3, measured). The design answer is pre-registration:
every switching condition is frozen at values chosen by *prior* verdicts for
*other* purposes, and the sweep never tunes a threshold.

Engine untouched (`simulate.py`, `strategy.py` — no diff). `SCHEMA_VERSION`
unchanged. No new data. Not in scope: §8.

## 2. `safe` gains a conditional form — normative

### 2.1 Grammar

`safe: str | null | dict`. A dict containing the key `"kind"` is the **switch
form**; any other dict remains a sleeve. (Backward compatible by construction:
a sleeve with a `"kind"` key was never valid — its value fails the fraction
check — so no previously legal spec changes meaning.)

```json
"safe": {
  "kind": "switch",
  "on":   { "BTAL": 0.25, "KMLM": 0.75 },
  "off":  { "BTAL": 0.75, "KMLM": 0.25 },
  "when": { "symbol": "VIX", "denominator": "VIX3M",
            "ratio_sma": 10, "fire": 1.00, "hysteresis": 0.05 }
}
```

Validation, each failure a `ValueError` naming the JSON path:

- `kind` must be `"switch"`; fields exactly `{kind, on, off, when}`;
- `on` and `off` each validate through the existing `_safe` rules as
  `str | null | sleeve dict` — **no nested switch** ("one level of
  conditionality");
- `on ≠ off` after normalisation — an equal pair is the static form under a
  second spelling and is rejected with "use the static form", the same
  one-strategy-one-spelling principle as the one-key sleeve rule. (This also
  rejects `null`/`null`.);
- `when` is the gate grammar's *condition* subset: `{symbol}` plus exactly one
  of `sma_days` / `sma_months`, or the regime keys (`denominator`,
  `ratio_sma`, `fire`, optional `hysteresis`), with identical per-key
  validation shared with `_gate_object` (factor the kind block; do not copy
  it). `assets`, `w_off`, `contribution_exempt` are **forbidden** here — a
  switch observes, it never caps or clips.

`when` parses to `Gate(symbol=…, assets=[], …)` — the measured pure-condition
behaviour of §1 is the implementation, and `closed(ctx)` / `symbols` /
`indicators` come for free, including the None-open rule.

### 2.2 Semantics

- **Universe.** `_sleeve(safe)` for the switch form is
  `_sleeve(on) ∪ _sleeve(off)`; the strategy universe is `{risk}` ∪ that
  union, and the gate universe check picks it up unchanged.
- **Allocation.** On a rebalance day, `active = off if when.closed(ctx) else
  on`; the allocation is `{risk: w}` ∪ `{s: (1−w)·f_s}` over the *active*
  sleeve ∪ `{s: 0.0}` for symbols only in the inactive sleeve — every universe
  symbol present on every rebalance day (the SAFE_BLEND zero-weight precedent).
  `weights` (the engine assert / fallback allocation) is built from `on`.
- **Warm-up.** While any input of `when` is `None`, the sleeve is `on` — the
  gate's "open while None" rule, applied to composition.
- **Rotation is real turnover.** The monthly rebalance sells the outgoing
  sleeve and buys the incoming one at the cost model's per-leg bps; a
  contribution-only day never sells (existing engine rule), so a mid-month
  flip waits for month-end. This is priced, not assumed away — §6.7.
- **Gate interaction, no engine change.** A closed gate's blocked risk budget
  redistributes to the open assets by weight; the inactive sleeve holds weight
  0.0 and receives 0 — redistribution lands in *active-sleeve* proportion
  automatically. `w_off` clips likewise operate on the returned weights.

### 2.3 Rendering — `safe_str`, one function, three consumers

Switch form: `{safe_str(on)}~{safe_str(off)}@{condition}` — the condition
rendered by the existing gate condition renderer, e.g.

```
BTAL25+KMLM75~BTAL75+KMLM25@QQQ<SMA200
KMLM~BTAL@VIX/VIX3M@10>=1.00<0.95
```

`~` because `/`, `+`, `|` are taken (portfolio, sleeve, OR); the double `@` in
the regime form is accepted — labels are rendered and asserted unique, never
parsed. Auto-label example:
`VT TQQQ/BTAL25+KMLM75~BTAL75+KMLM25@QQQ<SMA200 t30 w0-70 QQQ:VOL_EWMA80 gate QQQ<SMA200`.

`sweep._param_value` needs **no change**: the `("safe",)` path already routes
any structured value through `safe_str` (verified at `600f3a3`,
`sweep.py:172`), so `params.safe` renders the string above. `REQUIRED_KEYS` is
untouched — `safe` stays required, a null grid value over it still means the
cash arm.

## 3. Tests — `test_spec.py`, `test_vol_target.py`, `test_sweep.py`

**T1 — Validation.** The §2.1 example builds; `on == off` (dict, both-null,
and equal-string cases), a nested switch, `kind: "sleeve"`, missing `when`,
`when` carrying `assets` / `w_off` / `contribution_exempt`, and both condition
kinds at once each raise `ValueError` with the path. Str / null / sleeve
`safe` values produce byte-identical normalised specs (regression).

**T2 — Rendering.** `safe_str` on the switch form as §2.3, key order of the
sleeves irrelevant; `params.safe` in a sweep equals it (import identity, the
`gate_str` precedent); slug uniqueness across on/off permutations (the
switcher and its mirror get distinct labels).

**T3 — Allocation.** With a stubbed condition: closed → off-sleeve fractions,
open → on, indicator `None` → on; inactive-sleeve symbols present at exactly
0.0; universe is the union; hand-computed numbers at interior `w`, `w = w_max`,
and under a closed risk gate (redistribution in active-sleeve proportion — the
SAFE_BLEND §2.2 synthetic fixture rerun with a switch).

**T4 — Real-data pin.** On `tests/data/2026-08-20-net15`, a
`B25K75~B75K25@QQQ<SMA200` strategy's `balance` on **2022-06-30** (SMA closed —
the R4 calendar) returns the off fractions, and on a 2021 risk-on month-end
the on fractions; the r10lo condition flips on **2025-03-31** (10-day SMA
0.952 ≥ fire 0.95 — the R4 spot pin).

**T5 — Sweep.** A `safe` grid mixing `"BTAL"`, a sleeve dict, `null`, and two
switch objects expands to five entries with distinct labels and `params.safe`
strings; the mirror arm expands as its own entry.

**T6 — End to end.** A switch strategy through `run_bundle` on the net
snapshot: universe-wide `exposure` block, the switch object embedded verbatim
in the strategy `spec`, `results.json` round-trips.

**T7 — Goldens untouched** (suite invariant; zero engine diff).

## 4. Sweep specs

Both lanes reuse the blend `config` verbatim (tastytrade per-asset map,
`cash_yield` 0.03), `objective: calmar`, `constraint: {max_drawdown: -0.50}`,
λ 0.80, `sigma_target {0.20…0.40}`, `w_max {0.4…0.8}`, gate grid
`{null, QQQ<SMA200}`.

### 4.1 Pre-registered conditions — frozen before any run

The entire switching signal set, with its month-end calendar as measured in
this sandbox (`regime_report.py`, net snapshot, 2012-01-03 → 2026-08-20,
3,679 joint days, 175 month-ends):

| condition | month-ends off | of them 2022 | provenance |
|---|---|---|---|
| `QQQ<SMA200` | 27 | 12 | the incumbent gate signal |
| `VIX/VIX3M@1>=1.00` | 13 | 2 | REGIME_SPEC §8 arm |
| `VIX/VIX3M@10>=1.00<0.95` | 13 | 0 | the research default |
| `VIX/VIX3M@10>=0.95<0.90` | 44 | 7 | REGIME_SPEC's 2022-coverage arm |

**No threshold, smoothing, or hysteresis appears in any grid.** Every value
was fixed by a prior spec for a prior purpose; the sweep may only choose
*among* these four, and the read (§6.4) treats even that choice with
suspicion. This is the load-bearing anti-overfitting decision: the one new
fitted dimension is the arm identity, on sleeves inherited from the blend
grid's coarse ratio triple.

Two of the four are worth naming now. `@10>=1.00<0.95` fired on **zero** 2022
month-ends — as a switcher it is a near-placebo for grind years by
construction, and the read expects it weakest. `@10>=0.95<0.90` was the worst
*gate* in the regime verdict because its 44 closed month-ends each forfeited
TQQQ upside; a *switch's* false positive costs only a sleeve rotation of a few
bp, so the setting rejected under gate economics is precisely the plausible
candidate under switch economics. That asymmetry is the reason this spec
exists despite the regime verdict's "not adopted".

### 4.2 `specs/sweep_switch_2021.json` — primary

Windows identical to `sweep_blend_2021.json` (start 2020-12-18, holdout
2025-01-01 with its short-test warning, 3y/6mo sensitivity). One `safe` grid,
32 arms, per pair M ∈ {KMLM, DBMF}:

- **statics** (the in-grid nulls): `BTAL`, `null` (cash), `M`,
  `{BTAL:.25, M:.75}`, `{BTAL:.75, M:.25}` — 8 unique arms;
- **switchers**: `on = B25M75`, `off ∈ {B75M25, BTAL}`, × 4 conditions —
  16 arms;
- **anti-switchers**: the exact mirror `on = B75M25, off = B25M75`,
  × 4 conditions — 8 arms.

Grid 32 × 5 × 5 × 2 = **1,600 points**. Baselines: the gated 50/50 benchmark
set carried since the safe-swap lane. The anti-switchers are in the grid, not
an afterthought: they share every coordinate with the true switchers, pay the
same rotation costs, and read the same calendars backwards — the placebo the
verdict stands on (§6.3).

### 4.3 `specs/sweep_switch_2019.json` — the COVID check

Windows identical to `sweep_blend_2019.json` (start 2019-05-08, holdout
2024-01-01). DBMF half only (KMLM inception excludes it, as in the blend
lane): 5 statics + 8 switchers + 4 anti-switchers = 17 arms, **850 points**.
This lane's fit window contains COVID *and* 2022 — the only window where a
condition gets to prove both archetypes in-fit.

Budget: to be measured at implementation via `expand` counts before running;
projected from the blend lanes' measured rate (~9–12 window-sims per point,
~8,250 sims in 4–5 minutes), the two lanes plus the c20 stress land around
40k sims, ~20–25 minutes single-process. If materially worse, trim the KMLM
anti-switchers first (the DBMF set already carries the placebo in both lanes).

## 5. Run protocol

```
uv run sweep.py specs/sweep_switch_2021.json --data tests/data/2026-08-20-net15 --out results/sweep_switch_2021_net
uv run sweep.py specs/sweep_switch_2021.json --data tests/data/2026-08-20       --out results/sweep_switch_2021_tr
uv run sweep.py specs/sweep_switch_2019.json --data tests/data/2026-08-20-net15 --out results/sweep_switch_2019
uv run sweep.py specs/sweep_switch_2021.json --data tests/data/2026-08-20-net15 --cost-bps 20 --cash-yield 0.03 --out results/sweep_switch_2021_c20
```

The c20 stress is **not optional**: a flip between the two ratio sleeves
trades the full inter-ratio distance (0.50 of sleeve notional out, 0.50 in —
one sleeve-notional of round-trip per flip), on top of the blend family's
already-highest monthly turnover, with 6 bp KMLM legs. The gross-TR bracket
keeps the withholding discipline — the MF-heavy on-sleeves sit closest to
their gross bound.

## 6. Read protocol — separating edge from fit

The order matters: each step can end the verdict on its own.

**6.0 Fitted-surface accounting.** The verdict opens by stating what was
optimized (arm identity over 32, σ, w_max, gate — ~1,600 points) and what was
frozen (all four conditions and every threshold; the ratio grid). Any later
claim is read against that count.

**6.1 Nested-null promotion test** (same artefact only, arm-best vs
arm-best). A switcher earns promotion only if, on `robust_score`, it beats
**all three** of: its on-sleeve static, its off-sleeve static, and the blend
verdict's static incumbent for its pair (`B75M25`) in the primary lane — and
does not lose to its off-sleeve static in the 2019 lane. Beating one sleeve
but not the other is the better sleeve diluted with turnover; beating both
but not the incumbent is a worse answer than the one already on file.

**6.2 Window floor.** The timing thesis predicts what the blend thesis
predicted, more strongly: the switcher should hold the blend's windows *and*
recover part of each regime's extreme. `rank_worst` must improve on the
static incumbent's; a switcher whose floor is no better than `B75M25`'s is
refuted regardless of its mean, because the entire point of paying rotation
costs is the floor.

**6.3 Anti-switcher placebo — the family kill-switch.** Every anti-switcher
must rank below both of its component statics on `robust_score`. The mirror
holds the *wrong* sleeve in every regime while paying identical rotation
costs, so if timing carries information its score must be depressed by
roughly the true switcher's gain. **If any anti-switcher beats its statics,
the family verdict is "no detectable timing information" and nothing is
adopted** — a symmetric result means the calendars are noise at monthly
cadence, however good the best true switcher looks.

**6.4 Cross-condition sign consistency.** The four conditions are correlated
reads of one latent state. A real regime effect should put
`switcher − on-static ≥ 0` (robust_score) under at least three of the four
conditions per pair; a single-condition win is treated as a fit to that
condition's particular 13–44 month-ends. Expected asymmetry, stated in
advance: `@10>=1.00<0.95` (zero 2022 flips) weakest; `@10>=0.95<0.90` and
`QQQ<SMA200` (7 and 12 of 12) carrying any 2022-driven gain.

**6.5 Leave-one-episode-out on the finalists.** For ≤3 promotion candidates,
a confirm bundle (`main.py` runs, not new machinery): full-window daily
equity of switcher vs on-sleeve static, the delta grouped by off-episode
using the §4.1 calendars (`regime_report.py` prints the episodes). Adoption
requires the full-window advantage to survive deletion of the single largest
contributing episode. This is the direct counter to the regime verdict's
residual 1, where two month-ends 1.1–1.4 % over threshold carried an entire
positive result — with 13–44 decision points, one lucky episode *is* the
null hypothesis.

**6.6 Standard battery, unchanged.** Withholding bracket
direction-stability; equal-risk exposure check (the VT rule is
safe-invariant, so average TQQQ weight must match across all 32 arms at
matched coordinates); edge flags on σ/w_max, extend before believing;
holdout quoted with its warning — and noted explicitly that the primary
lane's 1.63-year test window contains **exactly one** off-episode (spring
2025) on every condition, so its switcher-vs-static delta is a sample of one.

**6.7 Turnover and the c20 read.** Per-arm turnover reported; the switcher
premium over its statics must survive c20 with the same sign. The blend
verdict's one casualty was cost-driven; a rotation strategy that only wins
gross has answered the research question in the negative.

**6.8 Verdict.** All of 6.1–6.5 pass in both lanes and 6.7 holds →
`notes/safe-switch-verdict.md` promotes at most one candidate per pair and
WINNING_STRATEGIES.md changes. Any single failure → the verdict names it,
nothing is adopted, and the switch form joins `ts_regime` as tested, inert
machinery (the regime-verdict precedent). There is no partial adoption.

## 7. What this spec deliberately concedes

Even passing every test above, the result rests on the same 2012–2026
Nasdaq-era data that produced the complementarity thesis; the 2019 lane
mitigates, it does not eliminate. The conditions' 2022 coverage was *known*
when the four were frozen — pre-registration here means "fixed by earlier
verdicts for other purposes", which is weaker than out-of-sample. The honest
claim ceiling, written into the verdict template: "switching survived every
falsifier available in this data", never "switching works".

## 8. Deliberately not in scope

- **Per-regime `sigma_target` / `w_max` / gate** — the natural next
  conditional and the actual overfit trap: it multiplies the fitted surface
  by the regime dimension exactly where §6.0's accounting warns. Only to be
  specced if a sleeve switch passes §6, and then with its own placebo design.
- **Three-state switching** (the armed band as a third sleeve) — a parameter
  with almost no month-ends to act on, per REGIME_SPEC §14.
- **`fixed`-strategy switching** — a new family (REGIME_SPEC §12's note),
  not needed to answer the question.
- **VRP or any new condition** — a new signal enters through
  `regime_report.py` and a calendar pin first (CLAUDE.md rule), then this
  spec's grid, never directly.
- **Cross-pair switches** (KMLM-on / DBMF-off) and **three-way sleeves** —
  arm growth without a lane that motivates them.
- **Threshold/smoothing grids** — excluded by design, not by budget; tuning
  the condition inside the sweep would convert §6.4 from a falsifier into a
  formality.

## 9. Errata (implementation, 2026-08-23)

Deviations found while implementing at `600f3a3`; the code follows these
corrected readings.

1. **§2.2 "`weights` … is built from `on`"** was under-specified: taken
   literally it breaks `simulate.py:117`'s `set(weights) == set(assets)`
   assert on the first off day. Implemented as the *union* key set — the `on`
   allocation at `fallback`, padded with off-only symbols at 0.0 (the same
   paragraph's "every universe symbol present" sentence, applied to `weights`
   too). `_allocation` gained an active-sleeve parameter for the same reason.
2. **§2.2 omitted `data` / `indicators`**: only the gate's symbols and
   indicators were merged before; the `when` condition's merge alongside
   them, name-deduplicated (the `AnyGate.indicators` pattern), or the
   `main.py` declaration asserts fire on a regime `when` with no gate.
3. **§1 "`SCHEMA_VERSION` unchanged"** is three constants:
   `results_json.SCHEMA_VERSION` (4), `spec.SPEC_SCHEMA_VERSION` (1),
   `sweep.SWEEP_SCHEMA_VERSION` (1). All three are unchanged (the SAFE_BLEND
   precedent: a grammar extension is not a version bump).
4. **§3 T4 "a 2021 risk-on month-end"** must be late 2021: indicators are
   computed causally from the window start (2020-12-18, KMLM inception), so
   the SMA200 only warms up ~2021-10. The pinned date is **2021-11-30**.
5. **§4.2 "the gated 50/50 benchmark set carried since the safe-swap lane"**
   grew over the lanes; the switch specs carry the **blend** sets verbatim
   (6 baselines in 2021, 5 in 2019, SPY benchmark last — the correlation
   anchor), consistent with inheriting the blend config.
6. **§4.3's budget counts three runs but §5 lists four** — the gross-TR
   bracket adds another 14,454, so the protocol is ~53.6k sims, not ~40k.
   "Single-process" is the only mode: `--jobs` is documented in SWEEP_SPEC
   §4.4 but was never built.
7. **§6.5 "`regime_report.py` prints the episodes"** — it printed only the
   episode count and mean length. The tool now lists each off-episode's span
   (`first -> last (N days)`), pinned by tests; the §6.5 read itself was moot
   (zero promotion candidates).
8. **§6.8 "WINNING_STRATEGIES.md changes"** — the file has never existed; a
   promoting verdict would have *created* it. (It did not: nothing was
   adopted.)
9. **§3 T6 "embedded verbatim"** is read as "as a structured object": the
   normalised switch form (`hysteresis` filled on a regime `when`, the
   regime-gate precedent), not the raw input bytes.

Validation notes recorded at implementation: every "(measured)" claim in §1
reproduced exactly; `sweep._param_value` needed no change as §2.3 stated; the
`Gate(assets=[])` pure-condition behaviour was emergent and untested at
`600f3a3` and is now pinned in `tests/test_gate.py`. The §4.3 pre-run budget
measurement: `1600 grid + 6 baselines x 9 windows = 14454 runs`,
`850 grid + 5 baselines x 12 windows = 10260 runs` (both `--dry-run`).
