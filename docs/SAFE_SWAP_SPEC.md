# Specification: safe-asset swap sweep

Repo: `vlaas/balancing_portfolio` · baseline commit: `afd637e` ("net-TR merge", 395 tests green) · status: proposal

## 1. Goal

Answer the standing research question: **should BTAL remain the safe leg** of the VT
strategy, or be replaced by a positive-carry diversifier (DBMF, KMLM) or by plain cash
(which now earns `cash_yield`)? The data pipeline exists precisely for this comparison
— on net-TR data the implied carries are BTAL 0.91%/yr, DBMF 4.92%/yr, KMLM 3.70%/yr,
cash ~3% — and the gross-of-distribution bias that would have decided it by accident
is gone.

Three parts, in dependency order:

1. one **sweep-grammar fix**: a `null` grid value over `vol_target`'s
   required-but-nullable `safe` must substitute literal `null` (= cash), not delete
   the key — the documented SWEEP_SPEC errata-3 limitation, which currently makes the
   cash arm inexpressible in a grid (verified at `afd637e`: the null combination dies
   in `build_bundle` on the missing required key);
2. three **sweep specs** — a primary ranked lane on the common KMLM-constrained window
   and two longer sanity lanes that trade candidates for history;
3. a **run-and-read protocol** whose withholding bracket (net vs gross rerun of the
   primary lane) operationalises the NET_TR_SPEC §11 tripwire.

All numbers below are from sandbox runs at `afd637e` on
`tests/data/2026-08-20-net15`. Not in scope: §9.

## 2. Grammar fix — `null` in grids over required keys

### 2.1 Rule

In `sweep.expand`, a `null` grid value at a **top-level** template path whose key is
**required** for the template's `type` substitutes literal `null`; everywhere else —
optional keys (`gate`, `w_max`, …) and nested paths — the existing delete semantics
stand unchanged. This supersedes SWEEP_SPEC errata #3's "optional keys only"
limitation; "null means absent" only ever made sense where absence is legal, and
where the grammar says required-but-nullable, null must mean null.

### 2.2 Implementation shape

The per-type required-key sets already exist as literals inside each builder's
validation in `spec.py`. Factor them into shared module-level metadata —
`spec.REQUIRED_KEYS: dict[str, frozenset[str]]` (`vol_target`:
`{type, risk, safe, vol_symbol, vol, sigma_target}`, `fixed`: `{type, weights}`) —
consumed by both the builders and `sweep._substitute`, so the two cannot drift.
`_substitute` gains the template's `type` (it is in scope in `expand`).

Consequences, verified with a prototype of exactly this rule: the §4 template expands
to 128 unique labels, 32 per safe arm; the cash arm labels render as
`VT TQQQ/cash t25 w0-50 QQQ:VOL_EWMA80` (the existing `safe or 'cash'` label path);
`params` carries `"safe": null` (distinguished from baselines by `is_baseline`, as
always); the normalised entry carries `"safe": null` explicitly. A `null` grid value
over a required key of `fixed` (`weights`) substitutes and fails loudly in the
builder with the JSON path — never silently.

### 2.3 Tests (in `tests/test_sweep.py`)

**T1** — `safe: {"grid": ["BTAL", null]}` expands to two entries; the null one has
`entry["safe"] is None`, a `/cash` label, `params["safe"] is None`, and builds into a
one-asset-universe strategy. **T2** — regression: `gate: {"grid": [null, {...}]}`
still deletes; a null grid over `w_max` still deletes (builder default applies).
**T3** — `weights: {"grid": [{...}, null]}` on a `fixed` template raises `ValueError`
naming the path. **T4** — `REQUIRED_KEYS` is the single source: the builders'
missing-key validation uses it (assert by import identity or equality).

## 3. Windows — the KMLM constraint and the three lanes

KMLM's history begins **2020-12-18** (1,343 net-TR rows), DBMF's **2019-05-08**
(1,805); every window of a sweep that trades KMLM is bounded below by its inception,
because the loader's completeness assert covers the union of traded symbols across
the whole bundle. The common all-candidates window is therefore ~5.7 years — two
stress episodes (2022, 2025), no COVID. That scarcity is irreducible; the design
answer is one ranked lane on the common window plus two longer lanes that drop the
young candidates, so horizon-dependence is *observed* rather than assumed.

Window structures below are measured with the real `sweep.windows` machinery on the
net snapshot's calendar:

| lane | traded universe | full window | holdout | test length | sensitivity |
|---|---|---|---|---|---|
| 2021 (primary, ranked) | TQQQ, BTAL, DBMF, KMLM, SPY | 2020-12-18..2026-08-20 | 2025-01-02 | 1.63y (**short-test warning, accepted**) | 3y every 6mo → **6 windows** (starts 2020-12-18 … 2023-06-20) |
| 2019 (adds COVID; no KMLM) | TQQQ, BTAL, DBMF, SPY | 2019-05-08..2026-08-20 | 2024-01-02 | 2.63y | 3y every 6mo → **9 windows** (starts 2019-05-08 … 2023-05-08) |
| 2012 (full BTAL history; BTAL vs cash) | TQQQ, BTAL, SPY | 2012-01-03..2026-08-20 | 2023-01-03 | 3.63y | 5y every 6mo → **20 windows**, the consolidated-sweep convention |

Holdout rationale: 2025-01-01 puts the 2025 drawdown — the only post-2022 stress —
into the primary lane's test window; the warning its 1.63y length triggers is the
honest price and is quoted in the verdict, not suppressed. The 2019 lane's fit
contains COVID and 2022, its test the 2024 bull and 2025 drawdown. The 2012 lane
keeps the consolidated sweep's holdout for comparability with every VT artefact to
date.

## 4. Sweep specs

### 4.1 `specs/sweep_safe_2021.json` — the primary lane

```json
{
  "schema_version": 1,
  "config": {
    "initial_capital": 10000, "monthly_contribution": 500,
    "cost_bps": { "TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6, "QQQ": 1, "SPY": 0.7, "*": 6 },
    "cash_yield": 0.03
  },
  "windows": {
    "start": "2020-12-18", "end": null, "holdout": "2025-01-01",
    "sensitivity": { "every_months": 6, "length_years": 3 }
  },
  "template": {
    "type": "vol_target", "risk": "TQQQ",
    "safe": { "grid": ["BTAL", "DBMF", "KMLM", null] },
    "vol_symbol": "QQQ", "vol": { "kind": "ewma", "lam": 0.80 }, "leverage": 3,
    "sigma_target": { "grid": [0.25, 0.30, 0.35, 0.40] },
    "w_max": { "grid": [0.5, 0.6, 0.7, 0.8] },
    "gate": { "grid": [null, { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 }] }
  },
  "baselines": [
    { "type": "fixed", "label": "50/50", "weights": { "TQQQ": 0.5, "BTAL": 0.5 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "DBMF": 0.5 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "KMLM": 0.5 } },
    { "type": "fixed", "weights": { "TQQQ": 0.5, "BTAL": 0.5 },
      "gate": { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 } },
    { "type": "fixed", "label": "SPY benchmark", "weights": { "SPY": 1.0 } }
  ],
  "objective": "calmar",
  "constraint": { "max_drawdown": -0.50 }
}
```

Grid: 4 safes × 4 σ × 4 w_max × 2 gates = **128 points** (verified expansion: 128
unique labels, 32 per arm). Design decisions:

- **λ fixed at 0.80** — the plateau's λ, interior in the consolidated λ-grid
  {0.75–0.90}. Re-sweeping it quadruples the grid without touching the safe question;
  the safe dimension is what this experiment varies.
- **`w_max` extends down to 0.5**, folding in the standing edge-flag cleanup: the
  current robust top-1 sits on the w0.6 boundary, footnoted per protocol. This grid
  either resolves it or pushes the flag to 0.5, in which case extend again before
  believing.
- **σ_target and w_max stay swept per arm** rather than pinned at the candidate:
  the VT formula sizes only TQQQ (`w = clip(σ_t/(3σ_QQQ))`), so the *rule* is
  safe-invariant, but the *tolerable* σ_target may differ by diversifier — a better
  hedge earns more TQQQ. The per-arm grid lets the data say so.
- **Costs**: the tastytrade base schedule extended with an explicit
  `"DBMF": 2.5` (calibration doc: 2–3 bp base case) — under `sweep_vt_cbase.json`'s
  schedule DBMF would have inherited the 6 bp wildcard, overstating its friction.
  KMLM's 6 is stated explicitly rather than inherited. Identical schedule across all
  three lanes.
- **Cash arm economics**: `safe: null` leaves `1 − w` in cash earning the 3%
  `cash_yield` — the T-bill proxy COST_MODEL_SPEC reserved for exactly this
  configuration. The cash arm is a real competitor, not a placebo.
- **Baselines** include a fixed 50/50 per candidate, so each arm's grid answers "is
  VT adding anything beyond the safe swap itself" against its own static twin.

### 4.2 `specs/sweep_safe_2019.json` — the COVID lane

Same `config`, `template`, `objective`, `constraint`, with:
`"safe": { "grid": ["BTAL", "DBMF", null] }`;
`"windows": { "start": "2019-05-08", "end": null, "holdout": "2024-01-01",
"sensitivity": { "every_months": 6, "length_years": 3 } }`;
baselines: 50/50, TQQQ50/DBMF50, gated 50/50, SPY benchmark.
Grid **96 points**. Its sensitivity windows start 2020-05-08 and 2020-11-09 among
others — the COVID crash and recovery that the primary lane structurally cannot see.

### 4.3 `specs/sweep_safe_2012.json` — the full-history lane

Same `config`, `template`, `objective`, `constraint`, with:
`"safe": { "grid": ["BTAL", null] }`;
`"windows": { "start": "2012-01-03", "end": null, "holdout": "2023-01-01",
"sensitivity": { "every_months": 6, "length_years": 5 } }`;
baselines: 50/50, gated 50/50, SPY benchmark.
Grid **64 points**. This is BTAL-vs-cash over BTAL's whole life — 2015–16, 2018,
COVID, 2022, 2025 — and the direct check on whether BTAL earns its place against a
3%-yielding nothing.

Measured cost of all three lanes: ~4,000 simulations at ~0.02 s each on the 2021
window — about a minute single-process. Runtime is not a constraint on this design.

## 5. Run protocol

```
uv run sweep.py specs/sweep_safe_2021.json --data tests/data/2026-08-20-net15 --out results/sweep_safe_2021_net
uv run sweep.py specs/sweep_safe_2021.json --data tests/data/2026-08-20       --out results/sweep_safe_2021_tr
uv run sweep.py specs/sweep_safe_2019.json --data tests/data/2026-08-20-net15 --out results/sweep_safe_2019
uv run sweep.py specs/sweep_safe_2012.json --data tests/data/2026-08-20-net15 --out results/sweep_safe_2012
```

The second run is the **withholding bracket**, and it is what discharges the
NET_TR_SPEC §11 tripwire without any per-fund tax research: the gross-TR snapshot
*is* the `w = 0` bound, the net snapshot the `w = 15%` bound, and the true
withholding on every fund's distributions lies between them. A safe-arm ordering
that holds on **both** datasets is withholding-robust by bracketing. If the ordering
flips between them — plausibly DBMF or KMLM overtaking BTAL at `w = 0` — the
per-symbol withholding extension (`--withholding {"SYM": w, "*": w}`) must be
specified and the true rates estimated from fund distribution-character data
**before any verdict is trusted**. The bracket applies to the primary lane only; the
sanity lanes run net-only.

Optional fifth run, cheap and directly aimed at KMLM's known weakness (3–38 bp
spread range): `… sweep_safe_2021.json --data …-net15 --cost-bps 20 --cash-yield
0.03 --out results/sweep_safe_2021_c20` — does the KMLM arm survive a flat 20 bp
stress that its wide-spread executions might actually realise.

All artefact sets are committed together with the specs, as always.

## 6. Read protocol — what the verdict must contain

The summary machinery ranks within a lane; **cross-lane numbers are never compared**
(different windows), only orderings and directions. The verdict sentence for project
memory answers, in order:

1. **Primary ranking** (2021 net): top-15 composition by safe arm; each arm's best
   `robust_score` and its params region; whether any arm dominates or the plateau is
   mixed. Quote `robust_score`, holdout test and `rank_worst` per protocol — never
   `full` alone — and quote the short-test warning alongside.
2. **Withholding bracket**: is the arm ordering of (1) direction-stable on
   `sweep_safe_2021_tr`? If not, stop: the tripwire fires and the per-symbol
   withholding spec precedes any conclusion.
3. **Horizon stability**: does the 2019 lane (with COVID in-window) preserve the
   BTAL/DBMF/cash ordering of the primary lane; does the 2012 lane preserve
   BTAL-vs-cash? An arm whose advantage exists only in the 2021 lane is
   window-luck until proven otherwise.
4. **VT additivity**: each arm's grid against its own fixed 50/50 baseline — a safe
   that only wins as a static mix is a different (cheaper) proposal than VT.
5. **Equal-risk check**: the exposure block's average TQQQ weight for the arms'
   top points — a winning arm must not simply be holding more TQQQ; this was the
   decisive column in the first experiment and stays mandatory.
6. **Edge flags**: any top-15 point on the σ 0.25/0.40 or w_max 0.5/0.8 boundaries
   gets the standard footnote — extend before believing.
7. **Cash-rate asymmetry** (2012 lane): the flat 3% `cash_yield` is anachronistic
   over 2012–2021 (T-bills paid ~0–2%, mostly ~0), so the cash arm there is an
   **upper bound on cash**, not history. Read it one-sidedly: BTAL beating the
   flattered cash arm is a strong conclusion; BTAL losing to it is **inconclusive**
   and triggers the BIL follow-up (§9) before any "drop BTAL for cash" verdict. The
   2021 lane is roughly rate-neutral (realised short rates over 2020-12..2026-08
   average near 3%), so its ranking stands on its own.

What the read refuses to do, mirroring SWEEP_SPEC §4.6: no cross-lane score
merging, no "best safe" declared from a single lane, no quoting the primary lane's
holdout test without its length warning.

## 7. Honest limitations

- **VT models only TQQQ's vol.** The safe leg's own volatility and its correlation
  to TQQQ are absorbed, not sized; a KMLM sleeve is a materially different risk
  object than a BTAL sleeve at the same dollar weight. Max-drawdown and Calmar
  capture the realised consequence, not the mechanism. Risk parity over both legs is
  a different strategy family and deliberately not smuggled in here (§9).
- **The primary lane's evidence is thin by construction**: 5.7 years, two stresses,
  six overlapping sensitivity windows, a 1.63y holdout test. The design compensates
  with the auxiliary lanes and the bracket, not with more grid — no amount of
  parameter resolution manufactures regimes that KMLM has not lived through.
- **KMLM's and DBMF's carry is strategy return, not yield**: managed-futures
  distributions vary enormously year to year (KMLM: 4 distributions in 5.7 years),
  so their net-TR "carry" is far noisier than BTAL's expense-driven drag or cash's
  policy rate. The lanes measure what happened, and what happened is a small sample.
- **`cash_yield` is a constant, not data.** There is no rate series anywhere in the
  repo; 3% is a hand-set calibration to the Aug-2026 front end. The cash arm
  therefore earns the same rate in 2013 as in 2023, which flatters it over the ZIRP
  years by roughly 2%/yr — the §6.7 read rule is the containment; a data-native cash
  definition is the fix (§9, BIL).

## 8. Acceptance checklist

- [x] `spec.REQUIRED_KEYS` shared metadata; `sweep._substitute` null rule per §2;
      SWEEP_SPEC errata #3 note updated (superseded by this spec)
- [x] Tests T1–T4 in `tests/test_sweep.py`; whole suite green from a fresh clone
      with `pip install polars matplotlib pytest`
- [x] `specs/sweep_safe_2021.json`, `sweep_safe_2019.json`, `sweep_safe_2012.json`
      exactly per §4
- [x] The four §5 runs (plus the optional c20 stress) committed with their specs
- [x] Docs: STRATEGY_DEVELOPMENT "Sweeps" — the null-grid rule sentence;
      CLAUDE.md protocol unchanged (net-TR decision line already covers this)
- [x] Verdict per §6 into project memory; numbers stay in the repo

## 9. Deliberately not in scope

- **Risk parity / dual-leg vol sizing** (sizing the safe leg by its own vol or by
  covariance): the long-standing horizon item, a new strategy type with its own
  spec — this sweep decides *which* safe, not *how much* of it beyond `1 − w`.
- **Per-symbol withholding rates**: armed by the §5 bracket, fired only if the
  bracket flips the ordering.
- **BIL as the data-native cash definition** — the designated follow-up, fired by
  §6.7 (or on its own merits if the cash arm contends anywhere). `safe: "BIL"`
  earns *historical* short rates through the ordinary pipeline — real prices,
  monthly distributions, ER, trading friction, TR/net-TR conventions and every
  invariant test — with zero engine change. Preconditions, in order: (1) a **paired
  same-session export** (`data/BIL.csv` adjusted + `data/price/BIL.csv` unadjusted;
  the initial BIL commit at `4ae17c7` is the unadjusted series alone, sitting in
  the TR slot — flat at ~91.6 for 19.2 years, −0.002%/yr end-to-end, the exact
  toggle-off signature T2 catches); (2) `tests/test_total_return.py` symbol
  discovery switched from the hardcoded `SYMBOLS` list to a glob over the root's
  `*.csv`, so BIL — and any future symbol — actually enters the invariant battery
  instead of silently bypassing it; (3) a fresh **seven-symbol export session** →
  new snapshot pair + regenerated net twin (append-only; the date will differ from
  `2026-08-20`, so no naming collision); (4) the affected lane rerun with BIL in
  the safe grid. Withholding note: BIL's income is US Treasury interest, the
  clearest §871(k) interest-related-dividend case in the universe — its true NRA
  withholding is plausibly ~0%, so under the flat-15% net convention BIL sits near
  its gross bound and is the **first candidate for a per-symbol rate**
  (`{"BIL": 0}`) if it enters a close verdict.
- **A FRED/`fredapi` rate series is rejected** as the cash fix: it would make
  `Config.cash_yield` time-varying (engine change, schema bump, a second data
  convention outside the CSV pipeline) and introduce a runtime API dependency into
  a repo whose artefacts are byte-reproducible from committed inputs. If a rate
  *series* is ever genuinely needed, the pattern is a committed CSV produced by a
  checked-in fetch script (`fetch_dividends.py` precedent) — but BIL supersedes the
  need: it is the same information as a T-bill rate series, already net of
  realistic implementation cost, delivered through machinery that exists and is
  tested.
- **Multi-safe blends** (e.g. BTAL+KMLM split): expressible today as `fixed`
  weights but not as a `vol_target` safe; a blend arm is a follow-up spec if two
  candidates tie.
- **Asymmetric gate speeds, band rebalancing**: unchanged backlog, orthogonal to
  the safe question.
- **Synthetic pre-inception history for DBMF/KMLM**: the financing-model spec
  remains its own item; extending managed-futures ETFs backward with index data is
  a research project, not a data patch.

## 10. Errata — deviations found and fixed during implementation

Validated against the code before implementation; the design stands as proposed,
with two factual corrections (the sections above are left as written):

1. **§1 "dies in `build_bundle`"**: the null combination dies earlier, inside
   `sweep.expand` — every expanded entry is validated through `spec._TYPES` at
   `sweep.py:184` under the `template` path prefix, so the failure is
   `template.safe: missing key` and `build_bundle` never sees it. The fix
   location (`_substitute`) and the required-key premise are unaffected.
2. **§6.5 "the exposure block"**: `summary.json` carries no exposure at all.
   Average weights live in `runs.csv`/`runs.json` as `exposure.<SYM>.avg` (and
   `.min`), and in `summary.md` as the single `avg risk wt` column, which
   resolves `<SYM>` from the entry's `risk` key — so `fixed` baselines render
   `-` there. The §6.4 and §6.5 baseline comparisons therefore read `runs.csv`,
   not `summary.md`.

Confirmed as proposed: the §3 window structures reproduce exactly (6/9/20
sensitivity windows, the 2023-06-18 → 2023-06-20 snap, the primary lane's
595-day test window tripping the short-test warning), and §2.2's expansion
prediction holds verbatim — 128 unique labels, 32 per arm, the cash arm
rendering `VT TQQQ/cash t25 w0-50 QQQ:VOL_EWMA80`, `params["safe"] = null`.
The header's "395 tests" was 399 at `afd637e`; T1–T4 take it to 403.
