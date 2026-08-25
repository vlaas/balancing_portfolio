# Verdict: Stage-2 rotation — ADM, HAA-Balanced, VAA-G4

Spec: [ROTATION_STAGE2_SPEC.md](../docs/ROTATION_STAGE2_SPEC.md) · read
protocol: ROTATION_SWEEP_SPEC §7 with **R3a′** (§2) in place of R3a · branch
`rotation-sweeps-2` · data `tests/data/2026-08-24-net15` (primary), gross-TR
bracket `tests/data/2026-08-24`, c20 stress `specs/rot2_points_c20.json` (flat
20 bps on net15) · objective `calmar`, constraint `max_drawdown ≥ −0.50` ·
ROTATION_SWEEP_SPEC §3 extended cost map, `cash_yield` 3% · windows per §3's
pre-flight: ADM native 2008-07-01, HAA-Balanced native **2008-08-01**, VAA-G4
native **2004-10-01**, all three 2012 lanes 2012-01-03 · predecessor:
[Stage-1 verdict](rot-verdict.md).

**All three families → DOCUMENT-ONLY. None is killed and all three clear R1 by
a wide margin — 21 to 34 drawdown points better than SPY — but all three fail
R2 on the same clause: the no-timing static beats them on holdout-test Calmar
in the 2023-01 → 2026-08 bull. HAA-Balanced clears every other bar including
both brackets; ADM and VAA-G4 fail more. The headline question is answered in
the negative: diversified selection buys HAA 5.3 drawdown points over
HAA-Simple and costs 1.9 CAGR points, so the §4.2 consolidation trigger does
not fire, and HAA-Simple stands as the family's REFERENCE. Nothing promoted,
nothing killed, no repo change.**

## 0. Fitted-surface accounting

**Optimized: nothing.** Every published point was written from its source paper
before a single simulation ran, and no bar moved after the fact — the specs,
the labels and §2's R3a′ bars were committed in `d6841f4`, the artefacts in
`85d5079`, and this file reads only those.

Surfaces: ADM 2 native / 3 on 2012, HAA-Balanced 9 / 9, VAA-G4 2 / 2 — 13
native and 14 on-2012 grid points plus baselines, **1,224 simulations** against
Stage 1's 1,981. Not one of the 27 points is promotable: §7 bars promoting a
non-published grid coordinate, so every non-published arm below is a robustness
datum about its family's published point and nothing else.

## 1. Frozen labels

The as-published point per family, as the auto-labels render them:

| family | as-published label | lane files |
|---|---|---|
| ADM | `ROT SPY+SCZ top1 1-3-6U fb best(TIP+TLT@1M)` | `sweep_rot2_adm_{native,2012}` |
| HAA-Balanced | `ROT SPY+IWM+VEA+VWO+VNQ+DBC+IEF+TLT top4 1-3-6-12U can TIP/1 fb best(BIL+IEF)` | `sweep_rot2_haab_{native,2012}` |
| VAA-G4 | `ROT SPY+EFA+EEM+AGG top1 13612W can SPY+EFA+EEM+AGG/1 fb best(LQD+IEF+SHY)` | `sweep_rot2_vaa_{native,2012}` |

The no-timing nulls and the context row (never tiered — §7, §4.2):

| role | label |
|---|---|
| ADM null (K1) | `SPY60/TLT40` |
| ADM ingredients null | `EW SPY/SCZ/TIP/TLT` |
| HAA-Balanced null (K1), EW-8 | `SPY12.5/IWM12.5/VEA12.5/VWO12.5/VNQ12.5/DBC12.5/IEF12.5/TLT12.5` |
| HAA-Balanced context row | `ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)` |
| VAA-G4 null (K1), EW-4 | `SPY25/EFA25/EEM25/AGG25` |
| VAA-G4 static context | `SPY60/AGG40` |
| benchmark | `SPY benchmark` |

## 2. §7 conditions, with R3a′

All conditions evaluate the as-published point on the **primary lane, native
window**, except R3a′ (both lanes), R3b (2012 lane) and B (§5 brackets). SPY
numbers are the same lane's baseline row.

| # | condition | ADM | HAA-Balanced | VAA-G4 |
|---|---|---|---|---|
| K1 | null beats the point on full-window CAGR **and** max DD → KILL | pass (null loses both: 8.52% vs 13.38%, −27.76% vs −25.81%) | pass (null loses both: 6.03% vs 9.70%, −39.93% vs −14.59%) | pass (null loses both: 7.19% vs 10.10%, −47.64% vs −21.63%) |
| K2 | holdout-test max DD worse than SPY's **and** holdout-test CAGR below SPY's **and** full-window max-DD edge over SPY under 5 points → KILL | pass — test DD −17.63% beats SPY's −18.63% | pass — test DD −14.48% beats SPY's | pass — test DD −14.23% beats SPY's |
| R1 | full-window max DD better than SPY's by ≥ 10 points | **PASS** 21.35 | **PASS** 32.51 | **PASS** 33.71 |
| R2 | full-window Calmar > the null's, **and** holdout-test Calmar ≥ the null's | **FAIL** 0.5184 vs 0.3069; 0.7643 vs 0.9374 | **FAIL** 0.6647 vs 0.1510; 0.6692 vs 1.0352 | **FAIL** 0.4667 vs 0.1508; 0.4401 vs 1.4015 |
| R3a′ | `rank_median` ≤ ⌈N/2⌉ on **both** lanes | **PASS** 1 of 2 (bar 1); 1.0 of 3 (bar 2) | **PASS** 1 of 9; 2.0 of 9 (bar 5 both) | **FAIL** 1.0 of 2 native passes; 2.0 of 2 on 2012 misses its bar of 1 |
| R3b | 2012 lane: published point's full objective ≥ 0.85 × the best grid point's | **PASS** 0.4182 / 0.4659 = 0.898 | **PASS** 0.6259 / 0.6259 = 1.000 | **FAIL** 0.3047 / 0.5144 = 0.592 |
| B | R1's max-DD edge (≥ 10 points) retained under both §5 brackets | **FAIL** 8.29 gross-TR, 6.33 flat-20 | **PASS** 19.25 / 18.22 | **FAIL** 13.67 gross-TR, **6.98** flat-20 |
| | **tier** | **DOCUMENT-ONLY** | **DOCUMENT-ONLY** | **DOCUMENT-ONLY** |

Tiers: **PROMOTE** = R1 ∧ R2 ∧ R3 ∧ brackets ∧ full-window CAGR ≥ SPY's.
**REFERENCE** = the same without the CAGR clause — the expected outcome for this
family. **DOCUMENT-ONLY** = anything else short of a kill. **KILL** = K1 or K2.

**R3a′ bars, as frozen** (§2; N is the lane's **grid size**, not the count of
feasible points, so an infeasible arm cannot loosen the bar — no arm was
infeasible in any lane):

| family | native N | native bar | native `rank_median` | 2012 N | 2012 bar | 2012 `rank_median` |
|---|---|---|---|---|---|---|
| ADM | 2 | ≤ 1 | 1 | 3 | ≤ 2 | 1.0 |
| HAA-Balanced | 9 | ≤ 5 | 1 | 9 | ≤ 5 | 2.0 |
| VAA-G4 | 2 | ≤ 1 | 1.0 | 2 | ≤ 1 | **2.0** |

R3a′ fires exactly where it was designed to. It is discriminating (VAA-G4 fails
where the unfireable R3a would have passed: VAA's native `robust_score` is
0.4401 against a full objective of 0.4667, a ratio of 0.943, clearing 0.75
comfortably), and it separates the two things a single-lane rank cannot —
VAA-G4 is the median-window winner of its own two-point grid on the crisis
window and the median-window loser of the same grid from 2012, which is the
regime instability the bar exists to catch.

**R2 is the binding condition, and it binds identically on all three.** Every
family clears the first clause by a wide margin — full-window Calmar 1.7× to
4.4× the null's — and fails the second. The holdout is 2023-01 → 2026-08, the
regime §1 pre-registered as one "where this family lags by construction", and
in it the no-timing static wins on Calmar for every family. Stage 1's
HAA-Simple cleared the same clause (1.3811 vs 1.2836) because its offense is
SPY itself and it participated in the bull; every Stage-2 offense is
diversified (HAA-Balanced, VAA-G4) or half small-cap-international (ADM), and
none of them did. The bars were frozen before the runs and are applied as
written; the tension between R2's holdout clause and §1's own expectation is
recorded as residual 1, not resolved here.

## 3. Supporting numbers

Per family, from `results/sweep_rot2_<family>_<lane>/summary.json`. Quoted
together per `CLAUDE.md` §6 — never `full` alone. `grid rank` is the point's
position when the lane's grid is sorted by `robust_score` descending.

| family | lane | `robust_score` | holdout `test` | `rank_median` | `rank_worst` | grid rank | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|---|---|---|---|
| ADM | native | 0.5184 | 0.7643 | 1 | 2 | **1 of 2** | 0.5184 | 13.38% | −25.81% |
| ADM | 2012 | 0.4182 | 0.7643 | 1.0 | 3 | 2 of 3 | 0.4182 | 10.78% | −25.78% |
| HAA-Balanced | native | 0.4960 | 0.6692 | 1 | 4 | 2=3 of 9 | **0.6647** | 9.70% | −14.59% |
| HAA-Balanced | 2012 | 0.4449 | 0.6692 | 2.0 | 4 | 2=3 of 9 | **0.6259** | 9.13% | −14.58% |
| VAA-G4 | native | 0.4401 | 0.4401 | 1.0 | 2 | **1 of 2** | 0.4667 | 10.10% | −21.63% |
| VAA-G4 | 2012 | 0.3047 | 0.4401 | 2.0 | 2 | 2 of 2 | 0.3047 | 6.18% | −20.27% |

HAA-Balanced tops its own grid on **full Calmar** on both lanes (ratio 1.000
against the best grid point, which is why R3b passes at exactly 1) while
ranking joint-second by `robust_score` — the gap is `neighbour_min`, the
component the numeric `k` dimension adds and no other rotation point in the
program has. The tie is exact and not a coincidence: `top4`'s `robust_score` is
`top3`'s full Calmar to the last digit (0.4959645 native, 0.4448771 on 2012),
because `top3` is its worse neighbour and `top3`'s own full objective is that
point's minimum component too. See §5.

Baselines and SPY on the same native lanes:

| label | lane | holdout `test` | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|
| `SPY60/TLT40` | adm native | 0.9374 | 0.3069 | 8.52% | −27.76% |
| `EW SPY/SCZ/TIP/TLT` | adm native | 0.8012 | 0.2261 | 6.21% | −27.45% |
| `SPY benchmark` | adm native (2008-07) | 1.1893 | 0.2551 | 12.03% | −47.16% |
| `SPY12.5/…/TLT12.5` (EW-8) | haab native | 1.0352 | 0.1510 | 6.03% | −39.93% |
| `ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)` | haab native | 1.3811 | 0.5818 | 11.58% | −19.91% |
| `SPY benchmark` | haab native (2008-08) | 1.1893 | 0.2593 | 12.21% | −47.10% |
| `SPY25/EFA25/EEM25/AGG25` (EW-4) | vaa native | 1.4015 | 0.1508 | 7.19% | −47.64% |
| `SPY60/AGG40` | vaa native | 1.2730 | 0.2128 | 7.68% | −36.10% |
| `SPY benchmark` | vaa native (2004-10) | 1.1893 | 0.1950 | 10.79% | −55.34% |

**ADM is the only point in the entire rotation program to beat SPY on
full-window CAGR** — 13.38% against 12.03% on its native window, with 21.35
drawdown points in hand. §1 pre-registered a CAGR win as "the surprise to
distrust first", and it does not survive the second look: on the 2012 lane the
same point returns 10.78% against SPY's 14.64%, so the excess is the 2008-07
start, where a small-cap-international momentum sleeve sidestepped the crash
and then caught the 2009–2013 recovery. It is a window result, not an edge.

## 4. Brackets (§5, 2012-01-03 window, 8-strategy roster)

Max-DD edge over `SPY benchmark`, in percentage points. The first column is the
primary lane's own 2012 window (not part of §5) so a window effect cannot be
read as a friction effect.

| point | primary net15 + cbase, 2012 lane | gross-TR + cbase (`rot2_points_tr.json`) | net15 + flat-20 (`rot2_points_c20.json`) |
|---|---|---|---|
| ADM | 7.96 | 8.29 | 6.33 |
| HAA-Balanced | **19.15** | **19.25** | **18.22** |
| VAA-G4 | 13.47 | 13.67 | 6.98 |

Two different failures. **ADM's is a window effect**: its edge is already under
the 10-point bar on the primary 2012 lane before any bracket is applied, so
like GEM in Stage 1 the protection is the 2008 crash and little else — 21.35
points on the native window, 7.96 from 2012. **VAA-G4's is a friction effect**:
13.47 points survive the tax bracket at 13.67 and then halve to 6.98 under flat
20 bps. Its CAGR falls 6.72% → 3.04% across that bracket, against HAA-Balanced's
9.86% → 7.60% and ADM's 11.28% → 9.30%. The canary-equals-universe rule flips
the whole portfolio between offense and defense on a single non-positive score,
and §4.1's warning about turnover — written for ADM's short lookbacks — lands
on VAA-G4 instead.

HAA-Balanced retains 18.22 of 19.15 points under the harshest bracket, the
cleanest bracket result in the rotation program after GTAA-5's.

## 5. Ablations and context rows

One sentence each, never tiered (§7).

- **The `k` concentration axis** — the published `top4` has the best full Calmar
  of the three on both lanes (0.6647 / 0.6259) and the best native
  `rank_median`, but `top5` has the best `robust_score` (0.6268 / 0.5910) and
  `top3` is the worst point of the axis on drawdown (−19.87% vs −14.59%): more
  slots buy stability, fewer buy nothing, and the published 4 sits one step
  from a `top3` whose full Calmar of 0.4960 *is* its `neighbour_min` — the
  single reason its `robust_score` trails its own full objective.
- **Recency weighting, `13612W` vs `1-3-6-12U`** — the unweighted mean wins
  everywhere it is tested: all three HAA-Balanced `13612W` arms score below
  their `1-3-6-12U` twins on both lanes (0.3336/0.2401/0.1672 against
  0.6268/0.4960/0.4960 native), and VAA-G4's published `13612W` ties `U` on the
  native full window (0.4667 vs 0.4655) while losing its holdout by half
  (0.4401 vs 0.8942) and the 2012 lane outright (0.3047 vs 0.5144); Keller's
  published weighting is the weaker operator on this data, and it is the whole
  reason VAA-G4 fails R3a′ and R3b.
- **Plain `12M`** — the weakest score family on HAA-Balanced's native lane
  (`robust_score` 0.2770–0.3045, drawdowns −20.03% to −22.06% against the
  published arm's −14.59%), reproducing Stage 1's finding that the protection
  lives in the multi-horizon score and not in the canary.
- **ADM's score axis** — `1-3U` beats the published `1-3-6U` on full Calmar
  (0.5682 vs 0.5184) and on the holdout (1.0767 vs 0.7643) while losing on
  `robust_score` (0.4054, its sensitivity median), and on the 2012 lane the
  arm §3 had to exclude from native, `1-3-6-12U`, tops the grid at 0.4659 —
  the published lookback is not the best of its own three anywhere except by
  median rank.
- **Balanced vs Simple** (§4.2 context row) — Balanced is 5.32 drawdown points
  better than Simple on the shared native lane (−14.59% vs −19.91%) and 1.88
  CAGR points worse (9.70% vs 11.58%), and Simple wins `robust_score` on both
  lanes (0.5818 vs 0.4960 native; 0.9669 vs 0.4449 on 2012).

**§4.2's trigger does not fire.** It required Balanced to beat Simple on
`robust_score` on *both* lanes and on full-window CAGR; it does neither, on
either lane. There is no HAA-consolidation note to write, and HAA-Simple stands
as the family's REFERENCE unchanged. The headline question of §1 — whether
diversified selection closes HAA-Simple's CAGR gap to SPY without surrendering
the drawdown edge — is answered in the negative on the second half of the
clause only: the drawdown edge grows, and the CAGR gap to SPY widens from 0.63
points to 2.51 on the same window.

A baseline block carries no `robust_score` field, so Simple's is recomputed
here with `sweep.py`'s own formula over the components its block does carry —
`min(full.objective, sensitivity.objective.median, holdout.test)`. Balanced's
own `robust_score` additionally mins over `neighbour_min`, so the comparison is
**conservative against Balanced**: the extra component can only lower its side.
It does — Balanced's full objective is 0.6647 and its `robust_score` 0.4960 —
and it does not change the answer, because Simple wins on full CAGR too, where
no such asymmetry exists.

## 6. Decision

**ADM → DOCUMENT-ONLY.** R2 fails on the holdout clause and B fails outright:
the edge is 21.35 points on the native window and 7.96 from 2012, so like GEM
its protection is the 2008 crash. Its full-window CAGR win over SPY is the
program's only one and does not replicate on the second window. Recorded, not
adopted.

**HAA-Balanced → DOCUMENT-ONLY.** The strongest Stage-2 result and the only one
that clears R1, R3a′, R3b and both brackets: 32.51 drawdown points over SPY on
the native window, 18.22 retained under flat 20 bps, top of its own grid by
full Calmar on both lanes. It misses REFERENCE on R2's holdout clause alone.
Against its own family's incumbent it is the worse instrument — better
drawdowns, materially worse CAGR and `robust_score` — so it does not displace
HAA-Simple and does not trigger a consolidation note.

**VAA-G4 → DOCUMENT-ONLY.** The skeptical prior §1 asked for was warranted.
The published `13612W` operator loses to the unweighted mean on the 2012 lane
(R3b 0.592, the worst ratio in the whole rotation program) and is that lane's
median-window loser (R3a′), and its drawdown edge halves under the cost bracket.
Its 33.71-point native edge is real and is also the longest window in the
program — 2004-10 onward, the only one containing 2008 top to bottom — which
makes it the most useful of the three to keep on file and the least promotable.

**Repo changes: none.** No spec, strategy or default moves. The rotation
program's standing verdict is unchanged from Stage 1: **HAA-Simple REFERENCE,
everything else DOCUMENT-ONLY.**

**Stage 3 is not unblocked by this.** ROTATION_SWEEP_SPEC §10 and
ROTATION_STAGE2_SPEC §7 gate BAA and the ranked defensive top-3 on "Stage-2
results first"; six published points across two stages have now produced one
REFERENCE and five DOCUMENT-ONLYs, which is an argument for spending the next
increment on the residuals below rather than on a parameter-richer model.

## Residuals worth remembering

1. **R2's holdout clause and §1's pre-registered expectation are in tension,
   and R2 won.** §1 says this family lags in the 2023-01 → 2026-08 bull "by
   construction"; R2's second clause requires it not to lag the no-timing
   static on Calmar in exactly that window. All three Stage-2 families failed
   on that clause and nothing else — HAA-Balanced would be REFERENCE without
   it. The bars were frozen and are applied as written; whether the clause
   should be conditioned on the holdout regime is a question for the next
   spec's design, and re-tiering these three on it now would be exactly the
   goalpost move the pre-registration exists to prevent. What is needed is a
   bear-market holdout the current data does not contain.
2. **Stage-1 residual 2 is confirmed: the `fb cash` advantage was the modeled
   cash yield.** `results/rot_points_cy15.json`, 2012 lane, net15 + cbase:
   halving `cash_yield` from 3% to 1.5% closes **91%** of `gap8M fb cash`'s CAGR
   advantage over `gap10M fb BIL` (+0.56 → +0.05 points) and **85%** of
   `gap10M fb cash`'s (+0.60 → +0.09), with Calmar edges falling 0.2098 → 0.1159
   and 0.1695 → 0.0586. The `cash_yield` contingency stays documented; the BIL
   spread/withholding model needs no look.
3. **`13612W` is the weaker operator on this data, everywhere.** Four distinct
   arms across two families, each on both lanes, and the unweighted mean wins
   every one of them. Keller's published recency weighting is the single
   largest source of Stage-2 condition failures. Worth its own note before any
   future spec adopts a weighted momentum score by default.
4. **`k = 5` outscores the published `k = 4` on `robust_score` on both lanes.**
   Not promotable (§7) and not a large gap, but it is the concentration
   direction the paper did not take, and it is the reason HAA-Balanced's
   `robust_score` understates its full-window result.
5. **ADM's 2012-lane winner is the arm the native lane could not carry.**
   `1-3-6-12U` tops the 2012 grid at 0.4659 with a 1.1610 holdout, and §3
   excluded it from native only because SCZ's inception leaves it cold until
   2008-12-31. A pre-2007 international small-cap proxy would let the two lanes
   test the same three arms; that is synthetic-history work, out of scope here.
6. **VAA-G4 is the program's turnover outlier.** Its flat-20 bracket costs
   3.68 CAGR points against HAA-Balanced's 2.26 and ADM's 1.98. §4.1 attributed
   the turnover risk to ADM's short lookbacks; the measurement says the
   binary canary-equals-universe rule dominates lookback length. Any future
   canary design should be costed before it is scored.
7. **The 2008-window dependence, now measured three times.** GEM 13.42 → 0.03,
   ADM 21.35 → 7.96, VAA-G4 33.71 → 13.47 points of drawdown edge from native
   to 2012. Only HAA-Simple (27.24 → 20.31) and HAA-Balanced (32.51 → 19.15)
   keep a double-digit edge on the post-crisis window. Whatever the rotation
   family is worth, the canary-plus-multi-horizon-score construction is where
   it lives.
