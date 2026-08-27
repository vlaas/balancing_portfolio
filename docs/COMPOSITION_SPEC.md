# Specification: momentum-score gate composition on the incumbent machine

Repo: `vlaas/balancing_portfolio` · baseline commit: `f58d8d4` ("Handoff: rotation
program closed → composition spec next", 720 tests green on a fresh clone) · status:
**implemented; nothing adopted** (branch `composition`, per-phase commits, errata
§15) — all nine §11 predictions held, the SMA-200 gate stands and the score gate
is retained as a tested, inert option; verdict: `notes/comp-verdict.md` ·
input: `docs/HANDOFF_COMPOSITION.md` · predecessors: `REGIME_SPEC.md`
(the gate-composition precedent, not adopted), `notes/rot3-verdict.md` (the rotation
catalog, closed).

## 1. Goal

Test the one composition the rotation program left open: the multi-horizon monthly
momentum score `1-3-6-12U`, read on QQQ, as an **alternative to** or **OR-combined with**
the SMA-200 gate on the incumbent TQQQ machine (VT + SMA-200 gate + BTAL-heavy sleeve).
Three parts, in dependency order:

1. **Gate** — a fourth gate kind, `score`: closed while a monthly score indicator on the
   gate's symbol is at or below a threshold. The kind the handoff §4 identified as the
   gap; nothing else in the engine changes. `AnyGate` already gives the OR form.
2. **Grammar and rendering** — `score` / `threshold` keys on the gate object, a
   lossless label fragment, nested numeric grids over `threshold`.
3. **Four sweep lanes and two brackets** on the incumbent's own lanes, the unmodified
   incumbent an arm in every one, read against the incumbent line's frozen bars
   (REGIME_SPEC §10) with the two additions the rotation program earned: the
   insurance-in-holdout diagnostic (R2d) and the costed comparison for any exit form.

Three measured facts from this sandbox on the committed data shaped the design and
should be read before the grammar (§11 has the full pilot):

- **The score and the SMA-200 gate close nearly the same month-ends.** On the 2012 lane's
  175 month-ends, SMA-200 closes 27, `1-3-6-12U ≤ 0` closes 22, and 18 are shared. The OR
  adds exactly four month-ends in fourteen years — 2016-06-30, 2019-05-31, 2023-01-31,
  2023-02-28 — the last two inside the holdout, at the trough of the incumbent's deepest
  drawdown. The substitute loses nine month-ends the SMA gate closes, two of them in 2022.
- **Neither signal sees a one-month crash.** The score reads +0.061 on 2020-02-28 and
  +0.051 on 2025-02-28; both gates close only at the following month-end. Every cap-only
  arm rides COVID to −27.2 % exactly as REGIME_SPEC §1 measured — the multi-horizon score
  is a slower reader than the daily SMA, not a faster one.
- **The HAA finding does not transplant.** On the rotation machine the protection lived
  in the score (plain-`12M` −33.7 % vs `1-3-6-12U` −19.9 %, rot-verdict §5). On this
  machine, in the same exit form, the 12-month sign beats the multi-horizon score
  (Calmar 0.699 vs 0.459, max DD −30.6 % vs −39.0 %), and a *monthly-read* SMA-10 gate
  (`sma_months: 10`, already in the grammar) reproduces the daily SMA-200 gate to 0.004.
  The pilot's prediction is therefore that this composition is a substitute at best; the
  lanes exist to falsify that under the robustness machinery, not to confirm it.

Not in scope (§13): hysteresis on the score, regime-conditional `sigma_target`, the
score on TQQQ or SPY, daily-cadence reads, a score-conditioned `SafeSwitch` sweep.

## 2. What is already true at `f58d8d4` (measured)

### 2.1 Engine surface

`strategies/gate.py`: `Gate` has exactly three kinds — `sma_days`, `sma_months`, `fire`
(regime) — asserted by `kinds == 1`; `closed()` for the sma kinds is `close < value`, for
the regime kind `value == 1.0`; open while any needed value is `None`; `w_off` + `clip`
and `contribution_exempt` are kind-independent. `AnyGate` is OR over ≥ 2 members with
the minimum buy cap and clips in member order (REGIME_SPEC §4.3, erratum 5).
`spec._condition` is shared by a gate and a switch's `when`; `spec._score` parses the
ROTATION_SPEC §6.1 score object and `score_str` renders it (`1-3-6-12U`, `12M`,
`gap10M`). `sweep._grid_dims` refuses a grid inside a list ("grid is not supported
inside lists"), so a composite gate is gridded as a whole object (REGIME_SPEC §5.3).

### 2.2 The indicator, against a hand computation

`mom_multi((1, 3, 6, 12))` → column `MOMM1-3-6-12U`. On QQQ from
`tests/data/2026-08-24-net15` (1999-03-10 → 2026-08-24, 6,907 rows): at every month-end
the engine value equals `mean(close_t / close_{t−m} − 1 for m in 1, 3, 6, 12)` over
month-end closes with **maximum absolute error 0**; null until twelve prior month-ends
exist (first value 2000-03-31); on every non-month-end row it equals the previous
month-end's value (0 carry-forward mismatches). Spot values: 2020-01-31 +0.1516,
2020-02-28 +0.0607, 2020-03-31 −0.0241, 2022-01-31 +0.0026, 2022-12-30 −0.1163,
2025-02-28 +0.0511, 2025-03-31 −0.0332.

### 2.3 The incumbent anchors, recomputed

`VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200`, 2012-01-03 →, blend cost map,
`cash_yield` 0.03, run from this clone:

| snapshot | gate | full Calmar | CAGR | max DD | source of the pin |
|---|---|---|---|---|---|
| `2026-08-20-net15` | `G_sma` | **0.86254363** | 0.2385326 | −0.27654555 | REGIME_SPEC R10, `results/sweep_regime_2012` |
| `2026-08-20-net15` | none | 0.71731262 | 0.2479853 | −0.34571440 | same |
| `2026-08-24-net15` | `G_sma` | **0.86123626** | 0.2381710 | −0.27654555 | this spec's anchor (§9) |
| `2026-08-24-net15` | none | 0.71623794 | 0.2476138 | −0.34571440 | this spec's anchor |

The 08-20 pins reproduce to eight decimals; the 08-24 values differ by the two added
trading days only, and the 08-24 SPY benchmark (0.43404677) equals the rotation 2012
lanes' baseline row to eight decimals. The 2021 winners reproduce from
`results/sweep_regime_2021/summary.json`: `G_sma` full Calmar 0.8556 / 0.8585 / 0.8903
for B75K25 / B75D25 / B50K50 (WINNING_STRATEGIES.md's 0.856 / 0.859 / 0.890).

### 2.4 The signal's own calendar (the §10 step-0 read, done once here)

QQQ from `2026-08-24-net15`, month-ends 2012-01-31 → 2026-07-31 (175; the file's final
partial-month row is never a month-end):

| signal | month-ends off | both | SMA only | score only | 2022 off | month-end state changes |
|---|---|---|---|---|---|---|
| `QQQ<SMA200` | 27 | — | — | — | 12 of 12 | 20 (1.38 / yr) |
| `MOMM1-3-6-12U ≤ 0` | 22 | 18 | 9 | 4 | 10 of 12 | 20 (1.38 / yr) |
| `MOM12M ≤ 0` | 16 | | | | | |
| `SMAGAP10M ≤ 0` | 29 | | | | | |

The thirteen disagreements, with the score's value: SMA-only 2012-10-31 (+0.015),
2012-12-31 (+0.038), 2018-10-31 (+0.015), 2018-11-30 (+0.001), 2019-01-31 (+0.010),
**2022-01-31 (+0.003)**, **2022-03-31 (+0.029)**, 2025-04-30 (+0.009), 2026-03-31
(+0.023); score-only 2016-06-30 (−0.014), 2019-05-31 (−0.004), **2023-01-31 (−0.019)**,
**2023-02-28 (−0.041)**. Threshold sensitivity, month-ends closed by `score ≤ thr` /
shared with SMA-200: −0.03 → 15 / 14, −0.02 → 18 / 17, −0.01 → 21 / 18, 0 → 22 / 18,
+0.01 → 27 / 22, +0.02 → 31 / 24, +0.03 → 35 / 26 (2022 becomes 12 of 12 at +0.03).
Whipsaw is identical to the incumbent's, which is why §13 leaves hysteresis out.

## 3. Gate — `strategies/gate.py`

### 3.1 The `score` kind

`Gate` keeps its public surface and gains a fourth kind:

| attribute | sma kinds | regime kind | **score kind** |
|---|---|---|---|
| `indicator` | `sma(n)` / `sma_monthly(m)` | `ts_regime(…)` | the `Indicator` passed as `score` |
| `symbols` | `(symbol,)` | `(symbol, denominator)` | `(symbol,)` |
| `closed(ctx)` | `close < SMA` | `value == 1.0` | `value <= threshold` |
| open when | either value `None` | value `None` | value `None` |
| `w_off`, `contribution_exempt` | as today | as today | as today |

Constructor: `Gate(symbol, assets, sma_days=None, sma_months=None, denominator=None,
ratio_sma=None, fire=None, hysteresis=0.0, score=None, threshold=None,
contribution_exempt=False, w_off=None)`. Exactly one of `sma_days` / `sma_months` / `fire`
/ `score` (the `kinds == 1` assertion extends). `score` is an `Indicator` (spec.py builds
it through `_score`, so a `Gate` never parses a score object itself); `threshold` is
required with `score`, forbidden without, stored as given, and must be a multiple of
0.001 (asserted, so the rendering of §4.2 is lossless — the REGIME_SPEC §3.4 rule).
`self.column = score.name` as for every kind; `self.threshold` and `self.score` are
attributes so `gate_str` and tests can read them; `self.fire` stays `None` on a score
gate so every existing `if gate.fire is not None` branch is untouched.

**`<=`, not `<`.** The rotation family's rule is "non-positive is bad": a slot qualifies
by strict `>` against its hurdle, a canary counts `<= 0`. A score gate at `threshold: 0`
closes on the same month-ends HAA's absolute filter would disqualify SPY, so an
ablation on the two machines compares like with like. An exact tie never occurs on
real data; the convention is stated so a synthetic test can pin it.

**Semantics are the SMA gate's, one indicator swapped.** Cap-only by default: a closed
score gate blocks buys of `assets`, never sells, and reroutes the blocked budget into
the sleeve (ARCHITECTURE.md step 5). `w_off` is the exit / partial-tilt action, exactly
REGIME_SPEC §4.2. The score is monthly and carried forward, so a gate reading it on a
rebalance day sees that day's own month-end value (the `_month_end_values` rule: a
month-end row includes its own close); reading it on a non-month-end cadence
(REBALANCE_SPEC weekly) sees the last month-end's value, stale by design — no lane here
does that.

`AnyGate`, `Fixed`, `VolTarget`, `SafeSwitch`: **no change.** `symbols` and `indicators`
already derive from the member gates; the OR form `[G_sma, G_score]` composes today
once the kind exists (verified in the pilot harness with the shipped `AnyGate`).
`simulate.py`, `strategy.py`, `indicators.py`, `prices.py`, `stats.py`, `results_json.py`:
**not touched.** `SCHEMA_VERSION` stays 4.

## 4. Grammar — `spec.py`, `sweep.py`

### 4.1 `gate` object

| Key | Type | Default | Kind | Meaning |
|---|---|---|---|---|
| `symbol` | str | required | all | host symbol (`QQQ`) |
| `assets` | list[str] | required | all | as today |
| `sma_days` / `sma_months` | int | — | sma | as today |
| `denominator`, `ratio_sma`, `fire`, `hysteresis` | | | regime | as today (REGIME_SPEC §5.1) |
| **`score`** | score object | — | score | a ROTATION_SPEC §6.1 score: `{"months": k}`, `{"kind": "avg", "months": [...]}`, `{"kind": "weighted", ...}`, `{"kind": "sma_gap", "months": m}` |
| **`threshold`** | float | `0.0` | score | close while `score <= threshold`; multiple of 0.001 |
| `contribution_exempt` | bool | `false` | all | as today |
| `w_off` | float in [0, 1] | absent | all | as today |

Exactly one of `sma_days` / `sma_months` / `fire` / `score` (`_condition` extends its
count and error text: "exactly one of sma_days / sma_months / fire / score");
`threshold` without `score` → `ValueError` at `…gate.threshold` ("requires score");
`threshold` not a multiple of 0.001, or a boolean → error naming the path; errors
inside the score object carry the nested path (`strategies[0].gate.score.months`),
which `_score` already produces. `_condition` is shared with a switch's `when`, so a
score-conditioned `SafeSwitch` becomes expressible for free; it is not swept here
(§13). Integer JSON numbers are accepted where floats are expected, as today.

Normalised spec: the score kind normalises to `{"score": <normalised score>,
"threshold": <float>}` with `threshold` always present (the `hysteresis` precedent) and
the score's `kind` filled the way `_score` fills it (`{"kind": "avg", "months": [1, 3, 6,
12]}`; a plain `{"months": 12}` stays as written). `_condition_normalised` gains the
branch; a composite normalises to a list in member order as today.

### 4.2 Rendering — `gate_str`

```
sma:        QQQ<SMA200
regime:     VIX/VIX3M@10>=1.00<0.95
score:      QQQ:MOMM1-3-6-12U<=0          symbol, colon, indicator column, "<=", threshold
            QQQ:MOMM1-3-6-12U<=m2         threshold −0.02   (percent via spec._pct, "-" → "m")
            QQQ:MOMM1-3-6-12U<=2 off0     threshold +0.02, w_off 0
            QQQ:MOM12M<=0                 the plain 12-month sign
composite:  QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0
```

`symbol:column` is the convention the VT label already uses (`QQQ:VOL_EWMA80`), and the
column embeds every score parameter losslessly (ROTATION_SPEC §4). The threshold renders
in percent with `_pct` (`0`, `2`, `0.5`) and a leading `m` for negatives, because
`results_json.slug` strips every non-alphanumeric character: `<=-0.02` and `<=0.02` would
both slug to `0-02` and collide at build (measured), where `m2` / `2` do not. `+contrib`
and ` off{pct}` attach as for every kind. Auto-label example:
`VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200|QQQ:MOMM1-3-6-12U<=m2`.

### 4.3 Sweeps

Grids inside a score gate object work as nested leaves today do: `gate.threshold: {"grid":
[-0.03, …, 0.03]}` is numeric (neighbourhoods, edge flags), `gate.w_off: {"grid": [null,
0.3, 0]}` categorical, `gate.score: {"grid": [{"kind": "avg", "months": [1, 3, 6, 12]},
{"months": 12}]}` categorical. One runner change, the REGIME_SPEC erratum-1 pattern:
`sweep._param_value` renders the path `("gate", "score")` through `score_str` (today an
un-special-cased dict falls through to `json.dumps`, which is hashable but unreadable in
`params`). Grids inside a composite list stay unsupported; §7.2 enumerates the OR
thresholds as whole objects and the verdict reads that neighbourhood by hand.

## 5. `score_report.py` — the signal's calendar

The REGIME_SPEC §6 tool for this signal, ~70 lines, read-only, sharing
`regime_report.month_ends` and its contingency rendering rather than re-implementing
them:

```
uv run score_report.py --data DIR [--symbol QQQ] --score '{"kind":"avg","months":[1,3,6,12]}'
    [--threshold 0] [--start 2012-01-03] [--end YYYY-MM-DD] [--sma-days 200]
```

Reads the symbol with `prices._read_close`, builds the score through `spec._score` (so the
report cannot drift from the gate), and prints deterministic markdown: data range and
month-end count; month-ends closed by `score <= threshold`, by `close < SMA`, and the
four-way contingency, in total and per calendar year; month-end state changes for each
signal; the list of disagreeing month-ends with the score's value; the same threshold
ladder as §2.4. One test pins its numbers (C5). It is step 0 of the read protocol and
the tool for any later score (`13612W`, `gap10M`, a score on SPY).

## 6. Tests — `tests/test_gate.py`, `test_spec.py`, `test_sweep.py`, `test_simulate.py`, new `tests/test_composition.py`

Cite as "COMPOSITION_SPEC C·" in test comments. Existing tests are not edited.

**C1 — Gate semantics** (`test_gate.py`, stub `MarketDay`). A score gate with
`threshold 0.0` is closed at `-0.01` and at exactly `0.0`, open at `+0.01` and on `None`;
with `threshold -0.02` closed at `-0.02`, open at `-0.019`; `symbols == (symbol,)`,
`indicators == {symbol: (score,)}`, `column == score.name`, `fire is None`; `score` with
`sma_days` → assertion; `threshold` without `score` → assertion; `threshold 0.0155` →
assertion; `clip` and `buy_cap` behave as the R5 cases with the kind swapped (one case
each, not the full table); a two-member `AnyGate` of an sma and a score gate is closed iff
either is, and its `indicators` on the shared symbol carry both columns.

**C2 — Grammar** (`test_spec.py`). Each of: `score` with `sma_days`; `threshold` without
`score`; `threshold: 0.0155`; `threshold: true`; `score: {"months": 0}` (path
`…gate.score.months`); `score: {"kind": "avg", "months": [3, 1]}` — raises `ValueError`
whose message contains the JSON path. Valid forms build, `threshold` defaults to `0.0`
and normalises as §4.1; the five renderings of §4.2 exactly; the auto-label of §4.2;
`results.json` round-trips a score gate and a composite `[sma, score]` (build →
normalise → build → same normalised spec); a `SafeSwitch` `when` with a score condition
builds and renders `on~off@QQQ:MOMM1-3-6-12U<=0`.

**C3 — Sweep** (`test_sweep.py`). A template with `gate: {symbol, assets, score,
threshold: {grid: [-0.02, 0, 0.02]}, w_off: {grid: [null, 0]}}` expands to 6 with
`params` keys `gate.threshold` (numeric: neighbours, `edge` on ±0.02) and `gate.w_off`
(categorical); a template with `gate.score: {grid: [<avg 1-3-6-12>, {months: 12}]}` puts
`1-3-6-12U` / `12M` in `params["gate.score"]`; a template whose `gate` grid lists
`[null, <sma>, <score>, [<sma>, <score>]]` renders `params.gate` as `[null, "QQQ<SMA200",
"QQQ:MOMM1-3-6-12U<=0", "QQQ<SMA200|QQQ:MOMM1-3-6-12U<=0"]`; `--dry-run` on the four §7
specs prints the counts of §7.7.

**C4 — Engine effect** (`test_simulate.py`, synthetic two-asset prices with ≥ 14
month-ends so the score warms up). A score gate closed on a rebalance day blocks the
buy and leaves holdings untouched (frame-equal to the `allow_buy → False` path); the
same gate with `w_off = 0` sells the asset to zero and the other asset absorbs it;
during warm-up (score `None`) the gate is open and the run equals the ungated twin.

**C5 — Real-data pins** (`tests/test_composition.py`, via `score_report.py`'s functions,
QQQ from `tests/data/2026-08-24-net15`, window 2012-01-03 → 2026-08-24): 175
month-ends, last 2026-07-31; `QQQ<SMA200` closed on 27; `MOMM1-3-6-12U <= 0` on 22;
both 18, SMA-only 9, score-only 4 and their dates (§2.4); 2022 → 12 / 10; state changes
20 / 20; the seven spot values of §2.2; the threshold ladder at −0.02 / 0 / +0.02 (18 /
22 / 31 closed). Also the gross root `tests/data/2026-08-24`: SMA-200 closed on **25**,
score on **22**, both 18 — the score's calendar is invariant to the withholding rescale
(a ratio of closes), the SMA's is not (R4's two extra 2012 closes, again). The flat
golden snapshot is an older export (29 / 23 / 21) and is not pinned.

**C6 — Goldens untouched and the anchors through the new code path.** The whole
suite; `VT TQQQ/BTAL t30 w0-60 λ0.80 gate QQQ<SMA200` on `2026-08-20-net15`, 2012-01-03 →
2026-08-20, blend cost map, `cash_yield` 0.03 → full Calmar **0.86254363**, CAGR
0.2385326, max drawdown −0.27654555 (R10's pin, unchanged); the same on
`2026-08-24-net15` → **0.86123626** / 0.2381710 / −0.27654555 and the no-gate twin
0.71623794 / 0.2476138 / −0.34571440 (§2.3); a score gate at `threshold: -1.0` (a mean
of total returns never reaches −1) with `MOMM1-3-6-12U` declared equals the no-gate twin
frame for frame, so declaring the indicator changes nothing by itself.

**C7 — Spec auto-discovery.** The three §7.6 bundles under `specs/` run in
`test_spec.py::every_strategy` on the flat snapshot without a skip (their symbols
TQQQ / BTAL / QQQ / SPY are all present there) — a free contract test on every arm.

## 7. Sweep specs

All on `tests/data/2026-08-24-net15`, objective Calmar, constraint max drawdown ≥ −50 %,
contributions 10 000 + 500 / month, `cash_yield` 0.03, and the **incumbent lanes' blend
cost map** (`TQQQ 1.5 / BTAL 6 / DBMF 2.5 / KMLM 6 / QQQ 1 / SPY 0.7 / * 6` bp per side —
`specs/winners.json`'s). This deviates from the handoff §5 cost map in one entry
(DBMF 3 there): the anchors this spec must reproduce (§2.3, §9) were priced with 2.5,
and the flat-20 bracket bounds the half-basis-point either way. Windows are copied from
the lane each one extends, so the `null` / `G_sma` arms are the unmodified incumbents on
identical lanes and the new arms are read against them (handoff §8).

### 7.1 Named gate objects (used verbatim below)

```
G_sma      {"symbol":"QQQ","assets":["TQQQ"],"sma_days":200}
G_sma0     G_sma + "w_off":0
G_sma10m   {"symbol":"QQQ","assets":["TQQQ"],"sma_months":10}
U          {"kind":"avg","months":[1,3,6,12]}
G_u        {"symbol":"QQQ","assets":["TQQQ"],"score":U}                       (threshold 0)
G_u30      G_u + "w_off":0.3
G_u0       G_u + "w_off":0
G_um2      G_u + "threshold":-0.02
G_up2      G_u + "threshold":0.02
G_12m      {"symbol":"QQQ","assets":["TQQQ"],"score":{"months":12}}
G_12m0     G_12m + "w_off":0
OR_x       [G_sma, G_x]   for x ∈ {u, u30, u0, um2, up2}
```

`G_sma10m` is the monthly-read trend filter already in the grammar (Faber's 10-month,
read as a gate): it separates "monthly cadence" from "multi-horizon score" in one arm.
`G_12m` / `G_12m0` are the operator ablation the handoff §3.2 asks for, in both the cap
and the exit form, because HAA's finding was measured in the exit form.

### 7.2 `specs/sweep_comp_2012.json` — head-to-head and combination (14 points)

Windows as `sweep_regime_2012` (start 2012-01-03, holdout 2023-01-01, sensitivity 6 m /
5 y → 20 windows, 23 in all). Template: the 2012 lane's coordinate the regime lane used,
so the two verdicts read side by side —

```json
"template": {
  "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
  "vol": { "kind": "ewma", "lam": 0.80 }, "leverage": 3, "sigma_target": 0.30, "w_max": 0.6,
  "gate": { "grid": [null, G_sma, G_sma0, G_sma10m, G_u, G_u30, G_u0, G_12m, G_12m0,
                     OR_u, OR_u30, OR_u0, OR_um2, OR_up2] }
}
```

Baselines: plain 50/50, gated 50/50, SPY. Pure categorical → `robust_score = min(full,
sensitivity median, holdout test)` for every arm alike. `OR_um2` / `OR_up2` are the OR
form's hand-read threshold neighbourhood (§4.3).

### 7.3 `specs/sweep_comp_thr_2012.json` — the threshold surface (21 points)

Same windows and template, `gate` = `G_u` with two grids inside it:

```json
"gate": { "symbol": "QQQ", "assets": ["TQQQ"], "score": U,
          "threshold": { "grid": [-0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03] },
          "w_off":     { "grid": [null, 0.3, 0] } }
```

Baselines: the same VT with no gate, with `G_sma`, with `G_sma0`; gated 50/50; SPY. The
numeric `threshold` dimension gives every point a `neighbour_min` and flags the two
edges; ±0.03 brackets the whole disagreement zone of §2.4 (every disagreeing month-end
has |score| < 0.042) and +0.03 is where the score first covers all twelve 2022
month-ends. The luck check of REGIME_SPEC §10.3 lives here: a result that disappears
one 0.01 step away is one month-end.

### 7.4 `specs/sweep_comp_2021.json` — the three winners (21 points)

Windows as `sweep_blend_2021` (start 2020-12-18, holdout 2025-01-01, sensitivity 6 m /
3 y → 9 windows). Template: `safe` ∈ {B75K25, B75D25, B50K50} × `gate` ∈ `[null, G_sma,
G_u, G_u0, OR_u, OR_um2, OR_u0]` at the winners' coordinate (λ 0.80, σ 0.20, w_max 0.8).
Baselines as the blend lane. `OR_u30` is deliberately absent: at this coordinate it is
identical to `OR_u` to four decimals (§11) — VT already sizes TQQQ below 0.3 on every
month-end the gate is closed, so a 0.3 clip never binds.

### 7.5 `specs/sweep_comp_2019.json` — the COVID check (14 points)

Windows as `sweep_blend_2019` (start 2019-05-08, holdout 2024-01-01, sensitivity 6 m /
3 y → 12 windows). `safe` ∈ {BTAL, B75D25} × the same seven gates. The
`sens_2019-05-08` window's max drawdown per arm is the one number an exit arm exists to
change; the pilot says no arm changes it.

### 7.6 `specs/comp_points.json`, `comp_points_c20.json`, `comp_points_tr.json` — the brackets and the panel

Three ordinary bundles of the fourteen §7.2 arms plus SPY on the 2012 window:

| file | data | costs | supplies |
|---|---|---|---|
| `comp_points.json` | `2026-08-24-net15` | blend map | `drawdowns` (per-episode panel), `yearly_returns`, the primary-lane column of the bracket table |
| `comp_points_c20.json` | `2026-08-24-net15` | `{"*": 20}` | flat-20 CAGR cost per arm, flat-20 DD edge |
| `comp_points_tr.json` | `2026-08-24` (gross TR) | blend map | withholding bracket |

Run with `--json results/<name>.json --no-charts --quiet`. The primary bundle is the
confirm bundle of REGIME_SPEC §8.6 by another name: `runs.csv` carries only a window's
max drawdown, and the 2015-08 / 2018-Q4 / COVID / 2022 / 2025 / 2026 panel needs the
top-5 `drawdowns` blocks (bounded by their depth, REGIME_SPEC erratum 8 — mark cells
below an arm's fifth-deepest `·`). The flat-20 CAGR cost is the rotation program's
definition exactly: CAGR on the primary bundle minus CAGR on the c20 bundle, same
window, same data, so the numbers sit in the same table as VAA-G4 3.68 / BAA-G4 3.07 /
BAA-G12 2.66 / HAA-Simple 1.98.

### 7.7 Size

`--dry-run`: 14 + 3 × 23 = 391; 21 + 5 × 23 = 598; 21 + 3 × 9 = 216; 14 + 3 × 12 = 204;
plus three bundles of 15 — about 1,450 simulations, ~3 minutes single-process. The
dual pre-flight rule (handoff §6) is trivially satisfied: the widest score is
`1-3-6-12U` on QQQ, warm from 2000-03-31, and no lane adds a symbol; the loader's
completeness assert covers the traded set as today. Recorded here so the rule is seen
to have been applied, not skipped.

## 8. Docs

- `docs/STRATEGY_DEVELOPMENT.md` "Declarative strategies": the gate table gains the
  score kind and the §4.2 rendering; the worked gate example gains one sentence naming
  the alternative.
- `docs/DECLARATIVE_SPEC.md`: gate keys `score` / `threshold`, the four-kind rule.
- `docs/ARCHITECTURE.md`: gate kinds line (four), `score_report.py` beside
  `regime_report.py`.
- `CLAUDE.md` §6, one line: a new gate signal starts with its calendar report
  (`regime_report.py` for a ratio, `score_report.py` for a monthly score).

## 9. Run protocol

```
uv run pytest                                                       # C1–C7 green from a fresh clone
uv run score_report.py --data tests/data/2026-08-24-net15 --score '{"kind":"avg","months":[1,3,6,12]}' > results/score_report_u.md
uv run score_report.py --data tests/data/2026-08-24-net15 --score '{"months":12}'                     > results/score_report_12m.md
uv run sweep.py specs/sweep_comp_2012.json     --data tests/data/2026-08-24-net15 --out results/sweep_comp_2012
uv run sweep.py specs/sweep_comp_thr_2012.json --data tests/data/2026-08-24-net15 --out results/sweep_comp_thr_2012
uv run sweep.py specs/sweep_comp_2021.json     --data tests/data/2026-08-24-net15 --out results/sweep_comp_2021
uv run sweep.py specs/sweep_comp_2019.json     --data tests/data/2026-08-24-net15 --out results/sweep_comp_2019
uv run main.py --spec specs/comp_points.json     --data tests/data/2026-08-24-net15 --json results/comp_points.json     --no-charts --quiet
uv run main.py --spec specs/comp_points_c20.json --data tests/data/2026-08-24-net15 --json results/comp_points_c20.json --no-charts --quiet
uv run main.py --spec specs/comp_points_tr.json  --data tests/data/2026-08-24        --json results/comp_points_tr.json  --no-charts --quiet
```

Commit order, as the rotation stages did: (1) engine + tests + docs; (2) the
**pre-registration commit** — the seven specs, the frozen labels of §7.1, the bars of
§10 and the predictions of §11, before any run; (3) the artefacts; (4) the verdict.
Before reading anything else, confirm the anchors: §7.2's `null` and `G_sma` arms print
full Calmar 0.71623794 and 0.86123626 (§2.3); §7.4's `G_sma` arms print 0.8529 / 0.8574
/ 0.8849 (the 08-24 values of the 08-20 pins 0.8556 / 0.8585 / 0.8903 — §11); §7.5's
B75D25 `G_sma` arm 0.9362. A mismatch is a bug in this change, not data drift. The
frozen snapshots are not regenerated; no golden is refreshed.

## 10. Read protocol and decision rule — frozen at the pre-registration commit

The incumbent line's bars (REGIME_SPEC §10), inherited unchanged, with two additions.
The rotation program's R-bars are *not* inherited: the composition is not a published
point (rot-verdict §0 bars promoting a grid coordinate — here every arm is a grid
coordinate), R3a′ is blind to holdout collapse (handoff §3.5), and R2 was written for a
static null that this machine does not have. What is inherited from the rotation
program is R2d and the costed comparison, because both were earned.

0. **The calendar first.** `results/score_report_u.md` (must reproduce §2.4 — it is the
   same computation) and `_12m.md`. An arm closed on fewer than ~5 % of month-ends
   beyond what `G_sma` closes is **inert** with respect to `G_sma`, and the OR at
   `threshold ≤ 0` is inert by this definition already (4 of 175); report it so.
1. **Q1 — a better indicator than SMA-200?** From §7.2: `G_u`, `G_12m`, `G_sma10m`
   against `G_sma` on `robust_score`, `rank_worst` and the holdout `test`. "Better"
   needs all three; within ±0.02 on `robust_score` with a worse `rank_worst` is "a
   substitute, not an improvement". Cross-check direction on §7.4 (any two of three
   winners) and §7.5 (both sleeves).
2. **Q2 — does stacking help?** `OR_u`, `OR_um2`, `OR_up2` against `G_sma`, per lane:
   Δ`robust_score`, Δ full max drawdown, Δ CAGR, Δ holdout test, and the minimum over
   sensitivity windows of max drawdown. **The bar: drawdown shallower by ≥ 1 pp with
   CAGR within −0.5 pp and holdout test not worse.** Then the per-episode panel from
   `comp_points.json` — every arm's six episode drawdowns next to `G_sma`'s.
3. **The exit and tilt arms on their own line.** `w_off` changes turnover and drawdown
   together; quote both, plus 2020 / 2022 / 2025 calendar-year returns. A `w_off` arm
   that clears step 2's bar must also clear the **costed bar**: its flat-20 CAGR cost
   (§7.6) is read against the binary-canary numbers, and an arm at or above 2.66 (the
   cheapest of the three) is a binary flip by the program's own measure and is not
   adopted whatever else it does. The incumbent's own cost (`G_sma`, §11) is the
   reference the number is *reported* against, not the bar.
4. **The surface, §7.3.** Is there a plateau in `threshold` where `neighbour_min` is
   close to `full`, and where do the edge flags sit? A `G_u` point that beats `G_sma`
   only at one threshold is one month-end; its two neighbours decide.
5. **Operator ablation.** `G_12m` vs `G_u` (cap) and `G_12m0` vs `G_u0` (exit): does the
   multi-horizon score beat the 12-month sign on *this* machine, as it did on HAA's? And
   `G_sma10m` vs `G_sma`: is the daily read worth anything over the monthly one?
6. **R2d — insurance in the holdout.** From the `kind == "test"` rows of each lane's
   `runs.json`: every arm's holdout-test max drawdown against the lane's `null` arm's
   and against `G_sma`'s, in points. Non-tiering; the caveat of handoff §3.4 applies
   (every 2023–26 drawdown is shallow). Kept so the table the rotation program started
   grows by fourteen rows on a different machine.
7. **Whipsaw.** Month-end state changes per year from the reports; turnover from the
   runs.
8. **Decision rule.** A gate change is adopted into WINNING_STRATEGIES.md only if it
   clears step 2's bar on §7.2 **and** improves at least two of the three winners in §7.4
   — *improves* meaning `robust_score` higher by more than 0.02 with `rank_worst` not
   worse and holdout test not worse — **and** does not worsen B75D25 in §7.5 **and**, if
   it carries `w_off`, clears step 3's costed bar. Otherwise the verdict is written up,
   the SMA-200 gate stands, and the score gate is retained as a tested, inert option.
   No grid coordinate is adopted from §7.3 alone: the surface is a falsifier.

Verdict file: `notes/comp-verdict.md`, sections 0–8 as above plus "Residuals worth
remembering", every number from the committed `summary.json` / `runs.json` /
`comp_points*.json`, never `full` alone.

## 11. Pilot measurements — what to expect, and what would falsify it

A throwaway harness in this sandbox (a duck-typed score gate with the §3 semantics,
composed with the **shipped** `VolTarget` / `AnyGate` / `Fixed`, run through
`main.run_bundle`; full windows only, **no** robustness windows, **no** ranks) on
`2026-08-24-net15`, blend costs, `cash_yield` 0.03. The harness reproduces §2.3's anchors
to eight decimals, so the numbers are comparable to the lanes' `full` column — and to
nothing else. They are expectations to be replaced by the artefacts, not findings.

**2012 lane, VT t30 / w0.6 / λ0.80 / BTAL, full window** (Calmar · CAGR · max DD · avg
TQQQ weight · turnover):

| arm | cap only | `w_off = 0.3` | `w_off = 0` |
|---|---|---|---|
| no gate | 0.716 · 24.8 % · −34.6 % · 0.526 · 0.98 | — | — |
| `G_sma` | **0.861** · 23.8 % · −27.7 % · 0.511 · 0.88 | — | 0.554 · 20.0 % · −36.1 % · 0.472 · 1.24 |
| `G_sma10m` | 0.857 · 23.7 % · −27.7 % · 0.511 · 0.88 | — | — |
| `G_u` | 0.692 · 22.4 % · −32.3 % · 0.511 · 0.89 | 0.666 · 21.5 % · −32.3 % · 0.508 · 0.93 | 0.459 · 17.9 % · **−39.0 %** · 0.481 · 1.23 |
| `G_12m` | 0.720 · 23.0 % · −32.0 % · 0.511 · 0.91 | — | 0.699 · 21.4 % · −30.6 % · 0.492 · 1.00 |
| `OR_u` | 0.846 · 23.0 % · −27.2 % · 0.507 · 0.86 | 0.812 · 22.1 % · −27.2 % · 0.503 · 0.91 | 0.475 · 18.5 % · −39.0 % · 0.474 · 1.16 |
| `OR_um2` | 0.865 · 23.6 % · −27.2 % · 0.510 · 0.87 | — | — |
| `OR_up2` | 0.790 · 21.4 % · −27.2 % · 0.501 · 0.87 | — | — |

Per-episode portfolio drawdowns at the same coordinate (2015-08 · 2018-Q4 · COVID · 2022 ·
2025 · 2026; `·` = below that arm's fifth-deepest):

| arm | 2015-08 | 2018-Q4 | COVID | 2022 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| no gate | · | −25.8 | −27.2 | −34.6 | −24.5 | · |
| `G_sma` | −22.5 | · | −27.2 | −27.7 | · | −23.1 |
| `G_sma10m` | −22.5 | · | −27.2 | −27.7 | · | −23.1 |
| `G_u` cap | · | −25.7 | −27.2 | −32.3 | · | −23.1 |
| `G_u` exit | **−39.0** | −25.8 | −27.2 | −32.3 | · | · |
| `G_12m` cap | · | −25.8 | −27.2 | −32.0 | −24.5 | · |
| `G_12m` exit | −28.7 | −26.6 | −27.2 | −30.6 | · | · |
| `OR_u` cap | −22.5 | · | −27.2 | −26.9 | · | −23.1 |
| `OR_um2` cap | −22.5 | · | −27.2 | −27.2 | · | −23.1 |

Holdout (2023-01-03 →) and fit (→ 2022-12-30) windows, full Calmar: `G_sma` 1.112 /
0.834; `G_u` 0.955 / 0.668; `OR_u` 0.950 / 0.829; `OR_um2` 1.063 / **0.834**; no gate
1.328 / 0.652; `G_u` exit 0.961 / 0.420; SPY 1.189 / 0.364.

Threshold surface (`G_u`, full Calmar at −0.03 / −0.02 / −0.01 / 0 / +0.01 / +0.02 /
+0.03): cap 0.720 / 0.720 / 0.696 / 0.692 / 0.687 / 0.646 / **0.785**; `w_off 0.3` 0.717
/ 0.707 / 0.683 / 0.666 / 0.658 / 0.605 / 0.738; exit 0.683 / 0.653 / 0.489 / 0.459 /
0.450 / 0.396 / 0.469. OR cap at −0.03 / −0.02 / −0.01 / 0 / +0.01: 0.865 / 0.865 / 0.850
/ 0.846 / 0.838.

**Winners' coordinate (t20 / w0.8 / λ0.80), full windows** (Calmar · CAGR · max DD):

| lane · sleeve | no gate | `G_sma` | `G_u` cap | `G_u` exit | `OR_u` cap | `OR_um2` cap | `OR_u` exit |
|---|---|---|---|---|---|---|---|
| 2021 · B75K25 | 0.834 · 16.3 · −19.5 | **0.853** · 16.3 · −19.1 | 0.725 · 13.8 · −19.1 | 0.753 · 14.4 · −19.1 | 0.780 · 14.9 · −19.1 | 0.828 · 15.8 · −19.1 | 0.766 · 15.4 · −20.1 |
| 2021 · B75D25 | 0.813 · 16.4 · −20.1 | **0.857** · 16.3 · −19.1 | 0.725 · 13.8 · −19.1 | 0.753 · 14.4 · −19.1 | 0.780 · 14.9 · −19.1 | 0.831 · 15.8 · −19.1 | 0.776 · 15.4 · −19.8 |
| 2021 · B50K50 | 0.814 · 18.4 · −22.6 | 0.885 · 18.5 · −20.9 | 0.758 · 15.8 · −20.9 | **0.894** · 16.4 · **−18.3** | 0.814 · 17.0 · −20.9 | 0.860 · 18.0 · −20.9 | 0.825 · 17.6 · −21.3 |
| 2019 · BTAL | 0.636 · 16.5 · −26.0 | 0.628 · 16.3 · −26.0 | 0.556 · 14.5 · −26.0 | 0.489 · 12.7 · −26.0 | 0.583 · 15.2 · −26.0 | 0.615 · 16.0 · −26.0 | 0.518 · 13.5 · −26.0 |
| 2019 · B75D25 | 0.940 · 18.9 · −20.1 | 0.936 · 18.8 · −20.1 | 0.832 · 16.7 · −20.1 | 0.749 · 15.1 · −20.1 | 0.871 · 17.5 · −20.1 | 0.917 · 18.4 · −20.1 | 0.790 · 15.9 · −20.1 |

`OR_u` with `w_off 0.3` equals `OR_u` cap to four decimals on the three 2021 rows
(0.7804 / 0.7796 / 0.8138); on the 2019 lane it costs 0.005–0.006 (0.578 vs 0.583 BTAL,
0.864 vs 0.871 B75D25) — the clip binds on a handful of COVID-era month-ends there.

**Brackets, 2012 window** (flat-20 CAGR cost in points; max-DD edge over SPY in points,
primary / gross-TR / flat-20; SPY's max DD −33.74 / −33.66 / −33.77 %):

| arm | flat-20 cost | DD edge | turnover |
|---|---|---|---|
| no gate | 0.34 | −0.83 / −0.92 / −1.02 | 0.98 |
| `G_sma` | **0.31** | 6.08 / 6.11 / 5.92 | 0.88 |
| `G_sma` exit | 0.50 | −2.40 / −2.50 / −3.06 | 1.24 |
| `G_u` cap | 0.30 | 1.45 / 1.37 / 1.36 | 0.89 |
| `G_u` exit | 0.47 | −5.28 / −5.39 / −6.16 | 1.23 |
| `G_12m` exit | 0.38 | 3.18 / 3.11 / 3.04 | 1.00 |
| `OR_u` cap | 0.30 | 6.57 / 6.50 / 6.53 | 0.86 |
| `OR_um2` cap | 0.30 | 6.50 / 6.50 / 6.37 | 0.87 |
| `OR_u` exit | 0.45 | −5.29 / −5.39 / −6.16 | 1.16 |

What this predicts, each a falsifiable line for the verdict:

1. **The substitute loses to the incumbent on every lane, and on the 2012 lane to the
   no-gate null** (0.692 vs 0.716). The whole gap is 2022: the score is open on
   2022-01-31 (+0.003) and 2022-03-31 (+0.029), the SMA gate is closed, and the 2022
   episode prints −32.3 % against −27.7 %. Falsified if `G_u` matches `G_sma` on
   `robust_score` within 0.02 on any lane.
2. **The OR at threshold 0 fails step 2's bar on the first clause** — max drawdown
   −27.2 % vs −27.7 % (0.5 pp; the maximum moves from the 2022 episode to COVID's
   −27.2 %, which no cap arm changes), CAGR −0.8 pp, holdout test 0.950 vs 1.112 — and
   loses on all five winner rows by 0.04–0.08 Calmar because the two added month-ends
   are 2023-01-31 and 2023-02-28, the first two months of the 2023 bull. Falsified if
   `OR_u` clears the bar on §7.2 or improves any winner.
3. **The only gain in the program is one month-end.** `OR_um2` (and `OR_um3`, identical)
   adds exactly 2023-02-28 to `G_sma`'s calendar; its fit-window Calmar equals `G_sma`'s
   to three decimals (0.834), its full-window gain is +0.004, its holdout test is lower
   (1.063 vs 1.112), and it loses on all five winner rows by 0.013–0.027. Under
   `robust_score` it lands within ±0.02 of `G_sma` — "substitute, not improvement" —
   and its `rank_worst` decides which. Falsified if it beats `G_sma` by more than 0.02
   with a `rank_worst` not worse.
4. **Every exit arm is dominated, and the score exit is the worst number in the
   incumbent line**: `G_u0` prints −39.0 %, deeper than the no-gate null (−34.6 %), with
   its deepest episode starting 2015-08-31 — the score sold TQQQ into the August 2015
   month-end and the re-entry failure REGIME_SPEC §3 measured for the ratio and
   REBALANCE_SPEC §7.3 for weekly cadence repeats. The one cell to check rather than
   dismiss: B50K50 `G_u0` (0.894 vs 0.885, DD −18.3 % vs −20.9 %, CAGR −2.1 pp) fails
   the bar's CAGR clause by four times its width; its sensitivity windows and holdout
   say whether even that survives. Falsified if any `w_off` arm clears step 2's bar on
   §7.2 or §7.4.
5. **`w_off 0.3` is inert at the winners' coordinate on the 2021 lane**, barely binds
   on the 2019 lane (−0.005 to −0.006), and is merely costly at the 2012 one (0.666 vs
   0.692): with σ-target 0.20 and the gate closed only in high-vol months, VT's own
   sizing is already under 0.3 almost everywhere. The partial tilt has nothing to clip.
   Falsified if a `w_off 0.3` arm beats its cap twin anywhere.
6. **The operator finding reverses on this machine.** `G_12m` cap ≈ no gate (0.720 vs
   0.716); in the exit form `G_12m0` beats `G_u0` by 0.24 Calmar and 8.4 drawdown
   points; and `G_sma10m` reproduces `G_sma` (0.857 vs 0.861, identical episodes). The
   protection on the incumbent machine is the *trend filter*, and its daily read is
   worth ~0.004; the multi-horizon score adds a slower, noisier version of the same
   signal. Falsified if `G_u` beats `G_sma10m` or `G_u0` beats `G_12m0` on `robust_score`.
7. **No arm changes a fast crash.** COVID −27.2 % and 2025 unchanged in every cap arm,
   for the reason §1 states: the score is positive on the month-end before both legs
   down. Falsified by any COVID or 2025 cell in the panel that differs from `G_sma`'s.
8. **Cost does not decide this spec.** Cap arms pay 0.30–0.34 points under flat-20,
   exits 0.45–0.50 — an order of magnitude under the canary strategies' 2.66–3.68 —
   because this machine's turnover is 0.86–1.24 against VAA-G4's 7.60. The costed bar
   of step 3 is carried, and expected not to bind.
9. **The surface is monotone toward inert, with one spike.** `G_u` cap improves as the
   threshold falls (closing fewer month-ends) and jumps only at +0.03 (0.785), where the
   score finally covers all twelve 2022 month-ends and closes 35 in total — an edge
   point whose one in-grid neighbour reads 0.646, so its `neighbour_min` is 0.646 and
   its `robust_score` cannot exceed that. Falsified by a `G_u` point with
   `neighbour_min` above `G_sma`'s `robust_score`.

## 12. Honest limitations

- **Monthly cadence is the binding constraint again**, and the score is monthly by
  construction, so unlike the ratio gate it cannot even be argued that a faster read
  would help: `1-3-6-12U` is what HAA reads and it read +0.061 on 2020-02-28.
- **Two fast crashes, one grind**, n = 1–2 per archetype, as in every verdict of this
  line; 2018-Q4 and 2015-08 only on the 2012 lane at a coordinate chosen on that lane.
- **The 2012 lane's coordinate (t30 / w0.6) is the regime lane's, not the plateau's
  representative point** (λ0.80 / σ0.30 / w_max 0.7 of the cost verdict). Chosen for
  side-by-side legibility with `sweep_regime_2012`; the 2021 and 2019 lanes read the
  same gates at the winners' coordinate, so a gate result that depends on the
  coordinate would show as a disagreement between lanes.
- **The holdout contains the two month-ends the OR adds.** That is a fact about the
  data, not a design choice, and it is why prediction 3 expects the holdout to be the
  binding component of `robust_score` for every OR arm. The R2/bear-holdout tension of
  the rotation program applies unchanged: only synthetic pre-inception history (handoff
  §7) separates "the score does not insure" from "this holdout had nothing to insure
  against" — except that here the 2012-anchored lane *does* contain 2022, and the score
  under-covers it.
- **`G_sma10m` is a free arm the program never ran**; if it reproduces `G_sma` under the
  robustness machinery as it does on the full window, the daily SMA-200 read is not
  load-bearing and a monthly-only implementation of the incumbent is on the table — a
  residual for the verdict, not a decision for this spec.

## 13. Deliberately not in scope

Hysteresis on the score (`ts_regime`-style state machine over month-end values): the
measured whipsaw is 20 state changes in 175 month-ends, identical to SMA-200's, so
there is nothing to damp; a two-line extension if a later score needs it. The score on
SPY or TQQQ as the gate symbol (HAA reads SPY; the incumbent's signal has always been
QQQ, and a symbol grid on top of a threshold grid doubles the surface for a question
this spec's calendar already answers in QQQ's favour — 22 closes vs a broader index's
would be a different spec). Regime-conditional `sigma_target` (REGIME_SPEC §14, still
deferred behind a positive gate result). `13612W` as a gate score (the operator finding
of rot3 residual 2 is settled against it; `G_12m` is the ablation that matters here). A
score-conditioned `SafeSwitch` (expressible after this spec; SAFE_SWITCH_SPEC's zero
promotions and the anti-switcher pattern stand until a signal calendar says otherwise).
Daily-cadence reads (REBALANCE_SPEC). Amending the incumbent line's step-2 bar: it was
written for exactly this question and it has one verdict behind it.

## 14. Acceptance checklist

- [ ] `Gate` score kind: `score` / `threshold`, four-kind assertion, `<=` semantics, threshold multiple of 0.001; `AnyGate` / `Fixed` / `VolTarget` / `SafeSwitch` untouched; core files untouched, `SCHEMA_VERSION` 4
- [ ] `spec.py`: `_condition` four kinds, `_condition_normalised` score branch, `_gate_object` builds through `_score`, `gate_str` §4.2 with the `m` sign; `sweep._param_value` renders `gate.score`
- [ ] `score_report.py`
- [ ] Tests C1–C7 green from a fresh clone with `uv run pytest`; suite count > 720
- [ ] Docs per §8
- [ ] **Pre-registration commit**: seven specs (§7.2–§7.6), §7.1 labels, §10 bars, §11 predictions — before any run
- [ ] Artefacts: four sweep directories (`strategies.json`, `runs.csv`, `runs.json`, `summary.json`, `summary.md`), three bundle JSONs, two score reports, committed together; §9 anchors confirmed in the verdict
- [ ] `notes/comp-verdict.md` per §10; WINNING_STRATEGIES.md changed only if step 8 says so
- [ ] `docs/HANDOFF_COMPOSITION.md` gains a one-line pointer to this spec and its verdict

## 15. Errata (found during implementation)

1. **§5's "sharing … its contingency rendering" needed a lift.** `contingency`
   was a closure inside `regime_report.report()` with the column names
   hard-coded, so it could not be imported. It is now a module-level
   `contingency(rows, primary, other)`; the rendered strings are unchanged and
   R4's pins (`| full | 9 | 18 | 4 | 144 |`) are untouched. This is the only
   edit `regime_report.py` took.
2. **§6's "C1–C7 green" cannot all land in the engine commit.** C3's `--dry-run`
   clause and C7 pin files the *pre-registration* commit creates, so they land
   there. The engine commit carries C1–C6 (720 → 754); the pre-registration
   commit carries the rest (754 → 806, of which 45 are the free contract cases
   the three bundles add to `every_strategy`).
3. **§7.6's `comp_points_tr.json` is byte-identical to `comp_points.json`.** The
   data root is a CLI argument, not a spec key, so the "gross TR" column of the
   bracket table is a different `--data`, not a different spec. It is still a
   separate file, because §14 counts seven specs and C7 names three bundles;
   the rotation program instead ran one spec against two roots and named the
   outputs apart (`results/rot3_points_tr.json`).
4. **§7.4 / §7.5's "Baselines as the blend lane"** means the *regime* lanes'
   three (plain 50/50, gated 50/50, SPY), not `sweep_blend_2021.json`'s six.
   §7.7's arithmetic requires three — `(21 + 3) × 9 = 216`, `(14 + 3) × 12 =
   204` — and `sweep_regime_2021.json` / `sweep_regime_2019.json`, the lanes
   actually copied, carry exactly those three. Read §7.7's `a + b × w` as
   `(a + b) × w`.
5. **§11's per-episode panel keys an episode by its drawdown's peak, not its
   trough.** `G_u0`'s −39.0 % runs 2015-07-20 → 2016-11-14, so a trough-keyed
   read puts it in 2016 and loses the 2015-08 cell the prediction names.
6. **A seventh episode is present in every arm** and §11's six-column panel
   omits it: 2020-09-02 → 2021-03-08, −25.1 %, identical to two decimals across
   all fourteen arms. The verdict's panel carries it as its own column
   (residual 5).
7. **`WINNING_STRATEGIES.md` has never existed** (SAFE_SWITCH_SPEC erratum 8).
   §10 step 8 said no, so §14's "changed only if step 8 says so" resolves to
   "not created", as it did for REGIME_SPEC.
8. **§11's parenthetical "`OR_um3`, identical" is untested.** §7.2's grid has no
   such arm and §7.3's surface has no OR column, so nothing in the program
   measures it (verdict residual 7).
9. **Line 93 cites 0.856 / 0.859 / 0.890 from the project-level winners document
   as it stood on the 2026-08-20 snapshot**; `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`
   carries the 2026-08-24 values (0.8470 / 0.8574 / 0.8849) and is the file §10
   step 8 and the checklist now refer to. (EPISODE_SPEC §7.2.)
