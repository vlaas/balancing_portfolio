# Verdict: Stage-1 rotation — GEM, GTAA-5, HAA-Simple

Spec: [ROTATION_SWEEP_SPEC.md](../docs/ROTATION_SWEEP_SPEC.md) · read protocol:
§7 · branch `rotation-sweeps` · data `tests/data/2026-08-24-net15` (primary),
gross-TR bracket `tests/data/2026-08-24`, c20 stress `specs/rot_points_c20.json`
(flat 20 bps on net15) · objective `calmar`, constraint `max_drawdown ≥ −0.50` ·
§3 extended cost map, `cash_yield` 3% · windows per §4 as amended by §12.1–2:
GEM native 2008-07-01, GTAA-5 native **2007-06-01**, HAA-Simple native
2008-07-01, all three 2012 lanes 2012-01-03 · predecessors:
[safe-switch verdict](safe-switch-verdict.md), [regime verdict](regime-verdict.md).

**HAA-Simple is adopted at REFERENCE. GEM and GTAA-5 are DOCUMENT-ONLY, neither
killed. Nothing is promoted: no family clears SPY on CAGR, which §1 pre-registered
as the expected — and desirable — outcome.** The three failures are each specific
and each is a fact about the published rule rather than about the grid: GEM's
timing loses to a 60/40 static on both Calmar and the holdout (R2), and its
drawdown edge is *entirely* the 2008 crash — on the 2012 window it is 0.03
points (brackets); GTAA-5's published `gap10M` sits 27% below the best point in
its own 2012 grid (R3b). HAA-Simple's published point is the top of its grid by
`robust_score` on **both** lanes, which is the strongest plateau result any
family produced.

## 0. Fitted-surface accounting

Optimized: nothing. §1 bars promoting a non-published grid point, so the grids
are read as falsifiers only and every tiering number below is the as-published
coordinate. Frozen before any run (`92f0b0e`, the pre-registration commit): the
§7 bars, the frozen labels, the windows, the cost map, the objective, the
constraint and the baselines. Surface sizes: GEM 4 native / 18 on 2012, GTAA-5
6/6, HAA-Simple 12/12 — 1,981 simulations.

## 1. Frozen labels

| family | as-published label | lane files |
|---|---|---|
| GEM | `ROT SPY+VEU top1 12M@SPY>BIL fb AGG` | `sweep_rot_gem_{native,2012}` |
| GTAA-5 | `ROT SPY+EFA+IEF+DBC+VNQ top5 gap10M fb BIL` | `sweep_rot_gtaa_{native,2012}` |
| HAA-Simple | `ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)` | `sweep_rot_haa_{native,2012}` |

| role | label |
|---|---|
| GEM null (K1) | `SPY60/AGG40` |
| GEM ingredients null | `EW SPY/VEU/AGG` |
| GEM absolute-only ablation | `ROT SPY top1 12M@SPY>BIL fb AGG` |
| GEM relative-only ablation | `ROT SPY+VEU top1 12M all fb AGG` |
| GTAA-5 null (K1) | `SPY20/EFA20/IEF20/DBC20/VNQ20` |
| HAA-Simple null (K1) | `SPY60/IEF40` |
| benchmark | `SPY benchmark` |

## 2. §7 conditions

All conditions evaluate the as-published point on the **primary lane, native
window**, except R3b (2012 lane) and B (§6's brackets, 2012 window). SPY numbers
are the same lane's baseline row.

| # | condition | GEM | GTAA-5 | HAA-Simple |
|---|---|---|---|---|
| K1 | null beats the point on full-window CAGR **and** max DD → KILL | pass (null wins DD −30.65% vs −33.75%, loses CAGR 8.36% vs 9.11%) | pass (null wins CAGR 5.52% vs 4.86%, loses DD −47.20% vs −13.84%) | pass (null loses both: 8.47% vs 11.58%, −28.77% vs −19.92%) |
| K2 | holdout-test DD worse than SPY's **and** holdout-test CAGR below SPY's **and** full DD edge under 5 points → KILL | pass — on the third clause only (edge 13.42) | pass (test DD −6.34% beats SPY's −18.63%) | pass (test DD −10.96% beats SPY's) |
| R1 | full-window max DD better than SPY's by ≥ 10 points | **PASS** 13.42 | **PASS** 41.43 | **PASS** 27.24 |
| R2 | full Calmar > the null's **and** holdout-test Calmar ≥ the null's | **FAIL** 0.2700 vs 0.2727; 0.9362 vs 1.2730 | **PASS** 0.3508 vs 0.1170; 1.2303 vs 1.1784 | **PASS** 0.5814 vs 0.2943; 1.3811 vs 1.2836 |
| R3a | `robust_score` ≥ 0.75 × own full objective | PASS 0.2700 / 0.2700 | PASS 0.3508 / 0.3508 | PASS 0.5814 / 0.5814 |
| R3b | 2012 lane: published full objective ≥ 0.85 × the best grid point's | **PASS** 0.2926 / 0.3236 = 0.904 | **FAIL** 0.5800 / 0.7898 = 0.734 | **PASS** 0.9669 / 0.9669 = 1.000 |
| B | R1's DD edge (≥ 10 points) retained under both §6 brackets | **FAIL** 0.01 gross-TR, 0.00 flat-20 | **PASS** 25.50 / 23.89 | **PASS** 20.25 / 19.99 |
| | **tier** | **DOCUMENT-ONLY** | **DOCUMENT-ONLY** | **REFERENCE** |

R3a passed everywhere and told us nothing: all three published points have
`robust_score` exactly equal to their full-window objective, because the full
window is the minimum of the components. On the two lanes with no numeric
dimension there is no `neighbour_min` to lower it either. R3a as written can
only fire when a point is worse on its own full window than in the median
sub-window — worth rewording before Stage 2 rather than re-reading here.

## 3. Supporting numbers

Per family from `results/sweep_rot_<family>_<lane>/summary.json`. Quoted with
the holdout `test` and `rank_worst`, never `full` alone.

| family | lane | `robust_score` | holdout `test` | `rank_worst` | grid rank | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|---|---|---|
| GEM | native | 0.2700 | 0.9362 | 3 | **1 of 4** | 0.2700 | 9.11% | −33.75% |
| GEM | 2012 | 0.2624 | 0.9362 | 17 | 16 of 18 | 0.2926 | 9.86% | −33.70% |
| GTAA-5 | native | 0.3508 | 1.2303 | 6 | 5 of 6 | 0.3508 | 4.86% | −13.84% |
| GTAA-5 | 2012 | 0.4957 | 1.2303 | 6 | 5 of 6 | 0.5800 | 5.23% | −9.02% |
| HAA-Simple | native | 0.5814 | 1.3811 | 12 | **1 of 12** | 0.5814 | 11.58% | −19.92% |
| HAA-Simple | 2012 | 0.9669 | 1.3811 | 6 | **1 of 12** | 0.9669 | 12.98% | −13.43% |

Nulls and the benchmark on the same native windows:

| label | lane | holdout `test` | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|
| `SPY60/AGG40` | gem native | 1.2730 | 0.2727 | 8.36% | −30.65% |
| `EW SPY/VEU/AGG` | gem native | 1.4338 | 0.1924 | 6.86% | −35.64% |
| `SPY benchmark` | gem/haa native | 1.1893 | 0.2551 | 12.03% | −47.16% |
| `SPY20/EFA20/IEF20/DBC20/VNQ20` | gtaa native | 1.1784 | 0.1170 | 5.52% | −47.20% |
| `SPY benchmark` | gtaa native (2007-06) | 1.1893 | 0.1880 | 10.39% | −55.27% |
| `SPY60/IEF40` | haa native | 1.2836 | 0.2943 | 8.47% | −28.77% |

Every family beat SPY on drawdown and lost to it on CAGR — the §1
pre-registration, confirmed on all three, which is the main reason to believe
the machinery is measuring what it claims.

## 4. Brackets (§6, 2012-01-03 window, 10-strategy roster)

Max-DD edge over SPY, in percentage points:

| point | primary net15 + cbase, 2012 lane | gross-TR + cbase (`rot_points_tr.json`) | net15 + flat-20 (`rot_points_c20.json`) |
|---|---|---|---|
| GEM | 0.03 | 0.01 | 0.00 |
| GTAA-5 | 24.71 | 25.50 | 23.89 |
| HAA-Simple | 20.31 | 20.25 | 19.99 |

The first column is not part of §6; it is the same 2012 window on the primary
lane, read out of the committed 2012 sweeps, and it is what makes the GEM
bracket failure legible. §6's brackets change the tax treatment and the cost
map **and** the window at the same time, so a bare bracket failure is
ambiguous. Here it is not: GEM's edge is already 0.03 points on the primary
lane at the same window, so the loss is the window, not the friction. GTAA-5
and HAA-Simple lose 0.3–0.8 points between the primary lane and the flat-20
bracket, which is the honest cost of the cost model, and nothing more.

## 5. Ablations — where the drawdown protection lives

Never tiered (§7); one sentence each, from the GEM native lane and the HAA
native grid.

- **Absolute-only** (`ROT SPY top1 12M@SPY>BIL fb AGG`, GEM baseline): Calmar
  0.3121, max DD −33.77%, holdout test 0.9357 — statistically the whole of GEM,
  and slightly *better* than it: the absolute filter is the engine, exactly as
  Antonacci claims.
- **Relative-only** (`ROT SPY+VEU top1 12M all fb AGG`, the §2 form): Calmar
  0.1969, max DD **−50.30%** — deeper than SPY's own −47.16%. Ranking without
  the absolute test does not merely fail to protect; on this window it makes
  the drawdown worse, because the loser leg is sold into the winner at exactly
  the wrong month-ends.
- **No canary** (HAA grid arm `ROT SPY top1 1-3-6-12U fb best(BIL+IEF)`):
  `robust_score` 0.5503 vs 0.5814, max DD −20.82% vs −19.92%, holdout test
  1.9331 vs 1.3811 — the canary is worth about one drawdown point and costs
  most of the 2023–26 bull. HAA-Simple's protection is not the canary: it is
  the multi-horizon score. All four plain-`12M` arms print −33.7% drawdowns,
  canary or not, against −19.9% for `1-3-6-12U`.

## 6. Decision

**HAA-Simple → REFERENCE.** The published point is #1 of 12 by `robust_score`
on the native lane and #1 of 12 on the 2012 lane, holdout test 1.3811 against
SPY's 1.1893, drawdown 27.2 points better than SPY's and holding 20 points of
that under both brackets. It fails PROMOTE only on CAGR (11.58% vs 12.03%),
which §1 pre-registered as expected and §7 waives for REFERENCE. It is not
adopted into any live allocation by this verdict — REFERENCE means it stands as
the momentum-family reference point that later work is measured against.

**GEM → DOCUMENT-ONLY.** Not killed: it survives K1 (the 60/40 null wins on
drawdown but loses on CAGR) and K2 (only on the third clause — the full-window
drawdown edge is 13.42 points, well over the 5-point bar). But R2 fails on both
halves — a 60/40 SPY/AGG static matches its full-window Calmar (0.2727 vs
0.2700) and beats its holdout test by a third (1.2730 vs 0.9362) — and the
bracket condition fails outright. The published point does top its own native
grid (#1 of 4), so this is not a fragility result; it is the anti-switcher
result. The signal calendar carries information the static does not *only* in
2008.

**GTAA-5 → DOCUMENT-ONLY.** Not killed, and the strongest drawdown result of
the three (41.4 points better than SPY on the native window, 24–26 under every
bracket). It fails R3b: the published `gap10M` reaches 0.734 of the best 2012
grid point, well under the 0.85 bar, and it is #5 of 6 by `robust_score` on
*both* lanes. Two separate things push it down and they should not be conflated
— see the residuals.

**Repo changes: none.** No spec is promoted into `specs/winners.json`, no
default changes, no engine change beyond the §2 grammar addition that this work
required. The `filter: {"kind": "none"}` form stays: it is what expressed the
relative-only ablation, and it is the in-type static null Stage 2 needs.

**Stage 2 (§8) is unblocked** by this verdict being merged. Its three families
inherit the machinery unchanged, and two Stage-1 findings should shape how they
are read: HAA-Balanced shares HAA-Simple's `13612U` score, which §5 above shows
is doing the work; and ADM's absolute test is on the same footing as GEM's, so
the §5 absolute-only reading transfers.

## Residuals worth remembering

1. **GEM's drawdown edge is one event.** 13.42 points over SPY on the native
   window, 0.03 on the 2012 window, on the primary lane. Every out-of-sample
   claim for dual momentum in this repo rests on 2008 alone; the data cannot
   reach 2000–02, and §9 of ROTATION_SPEC already says so. Not a kill, but any
   future GEM number quoted without its window is meaningless.
2. **GTAA-5's `fb cash` twin beats `fb BIL` in every months arm**
   (`gap8M fb cash` `robust_score` 0.4084 native / 0.7495 on 2012, against
   0.3508 / 0.4957 for the published BIL spelling). This is very likely the
   `cash_yield` model, not a finding: a flat 3% credited every year of
   2012–2021 is generous against what BIL actually returned then, and BIL also
   pays spread and withholding. The honest spelling is the one that loses.
   §3 added the BIL arm precisely to keep this contingency off the verdict
   path, and it worked — the published point is the BIL arm — but it means
   R3b's 0.734 is measured against a partly-modelled competitor. A `cash_yield`
   sensitivity is the follow-up, not a re-read of this artefact.
3. **`gap8M` beats `gap10M` on both lanes and both fallbacks.** Faber's
   published 10-month is a local dip in its own neighbourhood on this data
   (native `neighbour_min` 0.3707 against the point's own 0.3508). One step,
   one direction, both lanes — a consistent tilt rather than noise, and it is
   the one genuine plateau failure in Stage 1.
4. **HAA-Simple's canary is nearly inert; its score is not.** Documented in §5.
   If a later spec wants to cheapen HAA, the canary is the part to question —
   but only after checking what it does in a *bear* holdout, which this one
   does not contain.
5. **R3a cannot fail as written.** See §2. Reword before Stage 2.
6. **The relative-only arm's −50.30% drawdown** is the sharpest single number
   in this work and deserves its own follow-up: cross-sectional momentum with
   no absolute filter was worse than buy-and-hold on the crisis window. That is
   an argument about the *shape* of the anti-switcher lesson, and it belongs to
   its own spec, not to this grid.
