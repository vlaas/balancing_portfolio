# Specification: Stage-2 rotation sweeps — ADM, HAA-Balanced, VAA-G4

Repo: `vlaas/balancing_portfolio` · baseline commit: `a4ae7a4` (Stage-1 verdict merge,
652 tests green) · status: implemented (branch `rotation-sweeps-2`, errata §10) ·
predecessor: `docs/ROTATION_SWEEP_SPEC.md` (+ §12 errata), `notes/rot-verdict.md`

All numbers in this spec are from sandbox runs on a fresh clone at `a4ae7a4`: the
Stage-1 verdict's headline numbers were independently recomputed from the committed
`summary.json`/`results` artefacts before this spec was written (they all reproduce),
and every window and calibration figure below was measured against
`tests/data/2026-08-24-net15`.

## 1. Goal

Run the three Stage-2 families defined in ROTATION_SWEEP_SPEC §8 — Accelerating Dual
Momentum, HAA-Balanced, VAA-G4 — through the unchanged Stage-1 machinery, with two
amendments frozen here before any run: the R3a rewording the Stage-1 verdict
requested (§2), and the pre-flight window discipline the §12 errata taught (§3).

The inverted purpose carries over verbatim: **the only adoptable configuration per
family is the as-published point**; grids are falsifiers, baselines are the
no-timing nulls, and a better-scoring neighbor is a robustness datum, never a
candidate.

The headline question is HAA-Balanced. Stage 1 located HAA-Simple's entire
protection in the `13612U` score (every plain-`12M` arm printed −33.7% drawdowns
against `1-3-6-12U`'s −19.9%, canary or not), and HAA-Simple stopped at REFERENCE
only on CAGR (11.58% vs SPY's 12.03%). HAA-Balanced carries the same score across a
top-4 of eight assets — the open question is whether diversified selection closes
that CAGR gap without surrendering the drawdown edge.

Pre-registered expectations, so the verdict cannot drift: all three families should
beat SPY on max drawdown and lose on CAGR (REFERENCE is the ceiling we *expect* any
of them to reach); the 2023-01 → 2026-08 holdout remains a bull where this family
lags by construction; VAA-G4 additionally carries the survey's documented
out-of-sample degradation (Allocate Smartly's live replication under the published
in-sample figures) as a skeptical prior — no formal tier cap, the §7 bars are
strict enough, but a strong VAA result should be distrusted first, not celebrated.

## 2. Amendment: R3a′ replaces R3a

Stage 1 proved R3a (`robust_score ≥ 0.75 ×` own full objective) cannot fire on
crisis-anchored windows: the full-window Calmar is the minimum component of
`robust_score` whenever the window contains the crisis, so the two sides are equal
by construction (all three Stage-1 points printed exactly `robust = full`).

**R3a′ — regime-stable rank:** the published point's `rank_median` (already in
every `summary.json` sensitivity block) must be **≤ ⌈N/2⌉ on both lanes**, N = the
lane's grid size. Intent unchanged — "not a spike" — but measured where the spike
would show: across the rolling five-year sensitivity windows, the published point
must sit in the top half of its own grid in the median window.

Calibration against the committed Stage-1 artefacts (the legitimacy of using
Stage-1 data to freeze a Stage-2 bar is exactly that it is frozen *now*, before any
Stage-2 run):

| Stage-1 point | native `rank_median`/N | 2012 `rank_median`/N | R3a′ verdict |
|---|---|---|---|
| HAA-Simple | 2 / 12 | 2 / 12 | pass both |
| GEM | 1 / 4 | 15 / 18 | fail (2012) |
| GTAA-5 | 5 / 6 | 4 / 6 | fail (both) |

Discriminating (fires on two of three), calibrated (the adopted strategy clears it
comfortably), and it would not have changed any Stage-1 tier — GEM and GTAA-5
already fell on R2/B and R3b respectively. `rank_worst` was considered and
rejected: HAA-Simple, the strongest Stage-1 result, printed `rank_worst` 12 of 12
on its native lane, because the most defensive point ranks last in bull
sub-windows; that is the family working as designed, not fragility.

Everything else in the Stage-1 §7 procedure — K1, K2, R1, R2, R3b, B, the tier
logic, the ban on promoting non-published points — is inherited unchanged.

## 3. Pre-flight — the dual window check, run and recorded

The §12 lesson institutionalized: every native window needs **two** independent
checks per grid point — the first value date of the widest score in the lane
(silent failure mode: warm-up cash through the crisis) and the maximum inception
among *traded* symbols including fallback-held ones (loud failure mode:
`load_prices` completeness assert). Measured on `2026-08-24-net15`:

| family | max traded inception | widest native score, first value | native start |
|---|---|---|---|
| ADM | SCZ 2007-12-12 (SPY/SCZ/TIP/TLT) | `1-3-6U` on SCZ → 2008-06-30 | **2008-07-01** |
| HAA-Balanced | VEA 2007-07-26 (8 offensive + BIL/IEF) | `13612U` on VEA → 2008-07-31 (BIL best-of score → 2008-05-30) | **2008-08-01** |
| VAA-G4 | AGG 2003-09-26 (4 offensive + LQD/IEF/SHY) | `13612W` on AGG → 2004-09-30 | **2004-10-01** |

One collision found and resolved the §12-1 way: **ADM's `avg[1,3,6,12]` score
variant has its first SCZ value on 2008-12-31** — on the native window it would sit
in the §5.1 cash short-circuit through Lehman, corrupting the comparison. It is
excluded from the native lane and carried on the 2012 lane, where every symbol is
warm years before the window.

VAA-G4's native window is the longest in the rotation program and the only one
containing the complete 2008 episode top-to-bottom.

Standing caveat, inherited from Stage 1: the first month-end after an inception is
a partial month, so the earliest k-month returns span slightly less than k months.
It affects only the first values, all of which precede the window starts above.

## 4. Family definitions

House settings throughout (inherited §3–§4 of the Stage-1 spec): primary lane
`tests/data/2026-08-24-net15` + extended cost map + `cash_yield` 0.03; holdout
`2023-01-01`; sensitivity `{every_months: 6, length_years: 5}`; objective `calmar`;
constraint `max_drawdown ≥ −0.50`; contributions 10 000 + 500/mo. Six files:
`specs/sweep_rot2_{adm,haab,vaa}_{native,2012}.json`, 2012 lanes starting
2012-01-03.

### 4.1 ADM (EngineeredPortfolio's Accelerating Dual Momentum)

Template: `assets ["SPY","SCZ"]`, `k` 1, `fallback
{"kind":"best_of","symbols":["TIP","TLT"],"score":{"months":1}}` fixed. Score grid:
native `[avg[1,3], avg[1,3,6]]` (2 points); 2012 adds `avg[1,3,6,12]` (3 points).
The engine's default per-asset qualification (`score > 0`) **is** ADM's published
absolute rule — hold the winner only if its momentum is positive, else defensive —
so no `filter` key appears.

**Published point:** `ROT SPY+SCZ top1 1-3-6U fb best(TIP+TLT@1M)`.

Baselines: `SPY60/TLT40` (K1 null), `EW SPY/SCZ/TIP/TLT` (ingredients null),
`SPY benchmark` last.

Recorded caveats: SCZ carries the tier-5 cost assignment (thin, ~5 bp) and is the
data-thinnest instrument in the program; the survey flagged the SCZ leg as ADM's
replication weakness. The short lookbacks (1–6 months) are the highest-turnover
score family yet tested — the flat-20 bracket matters more here than anywhere in
Stage 1.

### 4.2 HAA-Balanced (Keller & Keuning G8/T4)

Template: `assets ["SPY","IWM","VEA","VWO","VNQ","DBC","IEF","TLT"]`; `k`
`{"grid": [3, 4, 5]}` — a numeric dimension with full neighborhood semantics, the
first in the rotation program; score grid categorical `[13612U, 13612W,
{"months": 12}]`; `canary {"symbols":["TIP"],"breadth":1}` fixed; `fallback
{"kind":"best_of","symbols":["BIL","IEF"]}` fixed, score inherited. 9 points per
lane. The engine's slot-replacement semantics (each selected slot with score ≤ 0
routes its `(1−d)/k` to the fallback) is Keller's published rule verbatim.

**Published point:**
`ROT SPY+IWM+VEA+VWO+VNQ+DBC+IEF+TLT top4 1-3-6-12U can TIP/1 fb best(BIL+IEF)`.

Baselines: `EW-8` equal weight of the offensive universe (K1 null); **the
HAA-Simple published point** (`ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)`)
as a context row — the Stage-1 REFERENCE on the same lane, warm well before
2008-08; and `SPY benchmark` last. Pre-registered reading for the context row: if
Balanced beats Simple on `robust_score` on both lanes *and* on full-window CAGR,
that is the trigger for a future HAA-consolidation note — it is not a tier
condition here.

The `k` dimension doubles as the concentration ablation: `k=3` vs `k=5` brackets
the published 4 and tells the concentration-vs-dilution story in one row each.

### 4.3 VAA-G4 (Keller & Keuning, Vigilant)

Template: `assets ["SPY","EFA","EEM","AGG"]`, `k` 1, `canary
{"symbols":["SPY","EFA","EEM","AGG"],"breadth":1}` fixed — the published "any
offensive negative → 100% defensive" is the canary-equals-universe, breadth-1
spelling; `fallback {"kind":"best_of","symbols":["LQD","IEF","SHY"]}` fixed, score
inherited. Score grid `[13612W (published), 13612U]` — 2 points per lane, and the
recency-weighting question it answers ties directly to Stage 1's "the score does
the work" finding.

No `filter` key, and none is needed — the default per-asset test is provably inert
here: if every canary score is positive, the top-1's score is positive (it is one
of the canaries), so qualification auto-passes; if the top-1's score is ≤ 0, then
`n_bad ≥ 1`, `d = 1`, and no offensive mass exists for the filter to act on. One
unit test pins both branches (§8 T5) so the reasoning is asserted, not trusted.

**Published point:**
`ROT SPY+EFA+EEM+AGG top1 13612W can SPY+EFA+EEM+AGG/1 fb best(LQD+IEF+SHY)`.

Baselines: `EW-4` of the offensive universe (K1 null), `SPY60/AGG40`,
`SPY benchmark` last.

## 5. Brackets and the Stage-1 residual closure

**Stage-2 brackets:** one roster, `specs/rot2_points.json` — the three as-published
points, the HAA-Simple point, the three K1 nulls, `SPY benchmark` last (8 rows) —
executed on the 2012-01-03 window twice: gross-TR (`tests/data/2026-08-24`, cbase)
and flat-20 (`specs/rot2_points_c20.json`, net15). Condition B reads these.

**Residual-2 closure (rides along, never tiered):** `specs/rot_points_cy15.json` —
`cash_yield` 0.015, cbase, net15, 2012 window; roster: GTAA-5 published (`fb BIL`),
the two `fb cash` grid arms (`gap8M`/`gap10M fb cash`), `EW-5`, `SPY benchmark`.
Deliverable is one number in the verdict doc: how much of the `fb cash` arms'
Stage-1 advantage over `fb BIL` was the modeled 3% yield. If halving the yield
closes most of the gap, Stage-1 residual 2 is confirmed and the `cash_yield`
contingency stays documented; if not, the BIL spread/withholding model deserves a
look.

## 6. Verdict procedure

Stage-1 §7 verbatim with R3a′ (§2) in place of R3a. Per-family K1 nulls:
`SPY60/TLT40` (ADM), `EW-8` (HAA-Balanced), `EW-4` (VAA-G4). All conditions on the
as-published point, primary lane, native window, except R3a′ (both lanes), R3b
(2012 lane) and B (§5 brackets). The verdict doc (`notes/rot2-verdict.md`)
inherits the Stage-1 skeleton: fitted-surface accounting, frozen labels, the
condition table, supporting numbers quoted with holdout `test` and `rank_median`,
bracket table, ablation sentences (the `k` concentration story, the
13612W-vs-U recency story, the Balanced-vs-Simple context row), decision,
residuals.

Surface sizes for the accounting section: ADM 2/3, HAA-Balanced 9/9, VAA-G4 2/2 —
13 native + 14 on 2012 grid points plus baselines; well under Stage 1's 1,981
simulations.

## 7. Out of scope

BAA and the ranked defensive top-3 (still gated — Stage-2 results first, per the
staged plan); GTT/LAA (blocked on `MACRO_DATA_SPEC`); the relative-only −50.30%
follow-up (Stage-1 residual 6 — its own note, not this grid); any HAA
consolidation or canary-removal work (gated on the §4.2 context-row trigger *and*
on a bear-market holdout the current data does not contain); rotation composed
with gates or vol targeting; synthetic pre-inception history.

## 8. Tests

- **T1 — spec parse and counts.** All six sweep files `--dry-run` clean with
  expansions 2/3, 9/9, 2/2; both bracket bundles and `rot_points_cy15.json` parse;
  the bracket rosters are frozen as label lists (§12-3 precedent), not counts.
- **T2 — warm-start assertion.** On each native lane, every grid point allocates
  at its first rebalance day (no all-cash opening row) — the §3 table asserted
  against the actual simulation, per family. This is the institutionalized form
  of the check that caught ACWX, BIL, and now ADM's 12-month arm.
- **T3 — frozen labels.** The three published-point labels and the HAA-Simple
  context label render exactly as §4 writes them (grammar → auto-label
  round-trip), and match the verdict skeleton.
- **T4 — R3a′ inputs exist.** `rank_median` present in the sensitivity block of
  every lane's summary for every grid point (guards against a runner change
  silently emptying the block Stage 2's tiering reads).
- **T5 — VAA filter inertness.** Synthetic fixture hitting both §4.3 branches:
  all-canaries-positive → fully invested top-1; top-1 score ≤ 0 → `d = 1`, fully
  defensive, zero offensive weight. Pins the no-`filter` reasoning.
- **T6 — k neighborhood.** The `k` grid registers as numeric with one-step
  neighbors and `edge` flags on the 3-point dimension (synthetic check, T2-of-
  Stage-1 pattern applied to the new dimension).

## 9. Run order

1. §8 tests that precede runs (T1, T3, T5, T6) + the R3a′ text into the verdict
   skeleton.
2. **Pre-registration commit**: six sweep specs, three bracket/sensitivity
   bundles, `notes/rot2-verdict.md` skeleton with frozen labels, §2 bars, §3
   window table.
3. Native lanes, then 2012 lanes (T2 asserts on the native runs), then brackets
   and `cy15`.
4. Commit `results/sweep_rot2_*/{runs.json,summary.json}`, `results/rot2_points_*`,
   `results/rot_points_cy15.json`; fill the verdict strictly from committed
   artefacts; verdict PR.

## 10. Errata — deviations found during execution

Measured on a fresh run of the six lanes; each item is recorded in the commit
that carried it. The sections above are left as proposed.

1. **§3's pre-flight table reproduces exactly, and so does its collision.**
   Independently recomputed on `2026-08-24-net15` before the specs were
   written: `MOMM1-3-6U` first values on SCZ 2008-06-30, `MOMM1-3-6-12U` on VEA
   2008-07-31, BIL's best-of score 2008-05-30, `MOMM1-3-6-12W12-4-2-1` on AGG
   2004-09-30, and ADM's `avg[1,3,6,12]` on SCZ **2008-12-31**. All four window
   starts (including 2012-01-03) are trading days, so no lane snaps its start.
   §8 T2 is load-bearing and was confirmed so: putting ADM's 12-month arm back
   on the native lane leaves `SCZ:MOMM1-3-6-12U` null at the opening rebalance.

2. **§8 T2 does not have to wait for the runs.** §9 step 3 says "T2 asserts on
   the native runs", but the check reads `balance()` off a truncated price
   frame and never simulates, so it belongs in the step-2 pre-registration
   commit — where it is a pre-flight rather than a post-mortem. It ships there.

3. **§9.4's artefact list is narrower than what is committed.** It names
   `results/sweep_rot2_*/{runs.json,summary.json}`; all five files per lane are
   committed, matching Stage-1's `a2b01bc` and `CLAUDE.md` §6. The wording is
   inherited from ROTATION_SWEEP_SPEC §11.3 and is a shorthand, not a rule.

4. **§4.2's context-row trigger reads a field baselines do not carry.** It asks
   whether Balanced beats Simple on `robust_score`, but `summary.json` emits
   `robust_score` only on grid points — a baseline block has `full`, `holdout`
   and `sensitivity` and nothing else (`sweep.py` `build_summary`). Simple's is
   therefore recomputed by hand with the runner's own formula over the
   components its block does carry, `min(full.objective,
   sensitivity.objective.median, holdout.test)`, frozen in the verdict skeleton
   before any run. Balanced's own score additionally mins over `neighbour_min`,
   so the comparison is conservative against Balanced; it did not change the
   answer, which Simple wins on full CAGR as well.

5. **§2's R3a′ needed one reading fixed in advance.** "N = the lane's grid
   size" is taken literally rather than as the count of feasible points, so an
   infeasible arm cannot loosen a bar. Inert this time — no arm was infeasible
   in any of the six lanes — and recorded because the two readings diverge the
   first time the `max_drawdown ≥ −0.50` constraint bites.

6. **§4.1's turnover caveat lands on the wrong family.** It warned that ADM's
   1–6 month lookbacks make it "the highest-turnover score family yet tested"
   and that the flat-20 bracket "matters more here than anywhere in Stage 1".
   Measured, VAA-G4 is the outlier: it loses 3.68 CAGR points across the
   gross-TR → flat-20 bracket against ADM's 1.98 and HAA-Balanced's 2.26, and
   its max-DD edge halves from 13.67 to 6.98 points. Binary
   canary-equals-universe switching dominates lookback length. ADM's bracket
   failure is a window effect, not a friction one.

7. **§1's expectation and §7's R2 collide, and R2 was applied as written.**
   §1 pre-registers that the 2023-01 → 2026-08 holdout "remains a bull where
   this family lags by construction"; R2's second clause requires the published
   point's holdout-test Calmar to reach the no-timing null's in that same
   window. All three families failed on that clause and no other, and
   HAA-Balanced would be REFERENCE without it. Recorded as residual 1 of the
   verdict rather than fixed here: changing a frozen bar after reading the
   artefacts is the move pre-registration exists to prevent.
