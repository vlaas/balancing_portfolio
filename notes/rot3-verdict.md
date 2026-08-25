# Verdict: Stage-3 rotation — BAA-G12 and BAA-G4

Spec: [ROTATION_STAGE3_SPEC.md](../docs/ROTATION_STAGE3_SPEC.md) · read
protocol: ROTATION_SWEEP_SPEC §7 with **R3a′** (ROTATION_STAGE2_SPEC §2), **R2
deliberately unchanged** (§6) · branch `rotation-sweeps-3` · data
`tests/data/2026-08-24-net15` (primary), gross-TR bracket
`tests/data/2026-08-24`, c20 stress `specs/rot3_points_c20.json` (flat 20 bps on
net15) · objective `calmar`, constraint `max_drawdown ≥ −0.50` ·
ROTATION_SWEEP_SPEC §3 extended cost map **as amended by §3** (GLD 1, HYG 1,
VGK 2, EWJ 2), `cash_yield` 3% · windows per §4's pre-flight: both native lanes
**2008-08-01**, both 2012 lanes 2012-01-03 · predecessors:
[Stage-1 verdict](rot-verdict.md), [Stage-2 verdict](rot2-verdict.md).

**Both families → DOCUMENT-ONLY, as §1 pre-registered. Neither is killed and
both clear R1 by a wide margin — 33 and 27 drawdown points better than SPY on
the native lane — and both fail R2 on the same clause that stopped all three
Stage-2 families: the no-timing static beats them on holdout-test Calmar in the
2023-01 → 2026-08 bull. They then fail in opposite places. BAA-G12 survives both
brackets and fails both robustness bars; BAA-G4 passes both robustness bars and
fails the cost bracket. The program-level question §1 asked is answered in the
negative: nothing in BAA's added machinery — ranked defensive top-3, the BIL
floor, the aggressive G4 offense — beats HAA-Simple on the same lanes, which
keeps `robust_score` on both lanes and 3.90 CAGR points over BAA-G12 while
giving up 5.73 points of native-window drawdown. Nothing promoted, nothing
killed, no repo change. The rotation catalog is closed.**

## 0. Fitted-surface accounting

**Optimized: nothing.** Both published points were written from Keller &
Keuning (SSRN 4166845, July 2022) before a single simulation ran, and no bar
moved after the fact — the engine feature landed in `a700383`, the specs, the
labels and the bars in `5db6c9e`, the artefacts in `349382b`, and this file
reads only those.

Surfaces: BAA-G12 6 native / 6 on 2012, BAA-G4 4 / 4 — **20 grid points** plus
baselines, **848 simulations**, the smallest stage of the three against Stage
2's 1,224 and Stage 1's 1,981. The grid is not there to explore BAA's parameter
space (the paper already did, in-sample, over 1970–2022) but to ask the two
questions Stages 1–2 sharpened: does concentration matter (`k`), and does the
canary operator survive contact with Stage-2 residual 3. Not one of the 20
points is promotable: §7 bars promoting a non-published grid coordinate, and §1
restates it — **the only adoptable configurations are the two as-published
points**.

## 1. Frozen labels

The as-published point per family, as the auto-labels render them:

| family | as-published label | lane files |
|---|---|---|
| BAA-G12 | `ROT QQQ+SPY+IWM+VGK+EWJ+VWO+VNQ+DBC+GLD+TLT+HYG+LQD top6 gap13M all can SPY+VEA+VWO+BND/1@13612W fb best3(TIP+DBC+BIL+IEF+TLT+LQD+AGG>BIL)` | `sweep_rot3_baa12_{native,2012}` |
| BAA-G4 | `ROT QQQ+VWO+VEA+BND top1 gap13M all can SPY+VEA+VWO+BND/1@13612W fb best3(TIP+DBC+BIL+IEF+TLT+LQD+AGG>BIL)` | `sweep_rot3_baa4_{native,2012}` |

The no-timing nulls and the context row (never tiered — §7, §6):

| role | label |
|---|---|
| BAA-G12 null (K1), EW-12 | `EW-12` |
| BAA-G4 null (K1), EW-4 | `QQQ25/VWO25/VEA25/BND25` |
| context row, the Stage-1 REFERENCE | `ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)` |
| benchmark | `SPY benchmark` |

`EW-12` carries an explicit label: twelve 1/12 weights auto-render to a
159-character string, and the roster and the tables below have to quote it.

## 2. §7 conditions, with R3a′

All conditions evaluate the as-published point on the **primary lane, native
window**, except R3a′ (both lanes), R3b (2012 lane) and B (§7 brackets). SPY
numbers are the same lane's baseline row. K1 nulls: `EW-12` (G12),
`QQQ25/VWO25/VEA25/BND25` (G4).

| # | condition | BAA-G12 | BAA-G4 |
|---|---|---|---|
| K1 | null beats the point on full-window CAGR **and** max DD → KILL | pass (null loses both: 7.30% vs 7.68%, −37.27% vs −14.18%) | pass (null loses both: 7.80% vs 8.76%, −39.29% vs −20.04%) |
| K2 | holdout-test max DD worse than SPY's **and** holdout-test CAGR below SPY's **and** full-window max-DD edge over SPY under 5 points → KILL | pass — test DD −10.62% beats SPY's −18.63% | pass on the **third clause only** — test DD −19.87% is worse than SPY's −18.63% and test CAGR 1.33% is far below SPY's 22.15%, but the full-window edge is 27.06 points, not under 5 |
| R1 | full-window max DD better than SPY's by ≥ 10 points | **PASS** 32.93 | **PASS** 27.06 |
| R2 | full-window Calmar > the null's, **and** holdout-test Calmar ≥ the null's | **FAIL** 0.5419 vs 0.1960; 0.5178 vs 1.4225 | **FAIL** 0.4371 vs 0.1985; 0.0669 vs 1.4235 |
| R3a′ | `rank_median` ≤ ⌈N/2⌉ on **both** lanes | **FAIL** 4 of 6 native and 4.5 of 6 on 2012, both against a bar of 3 | **PASS** 2 of 4 native, 2.0 of 4 on 2012 (bar 2 both) |
| R3b | 2012 lane: published point's full objective ≥ 0.85 × the best grid point's | **FAIL** 0.4856 / 0.6233 = 0.779 | **PASS** 0.4289 / 0.4926 = 0.871 |
| B | R1's max-DD edge (≥ 10 points) retained under both §7 brackets | **PASS** 20.36 gross-TR, 13.22 flat-20 | **FAIL** 13.83 gross-TR, **7.62** flat-20 |
| | **tier** | **DOCUMENT-ONLY** | **DOCUMENT-ONLY** |
| R2d | *diagnostic, non-tiering:* holdout-test max DD vs the K1 null's | **−0.39** (−10.62% vs −10.23%) | **−8.04** (−19.87% vs −11.83%) |

Tiers: **PROMOTE** = R1 ∧ R2 ∧ R3 ∧ brackets ∧ full-window CAGR ≥ SPY's.
**REFERENCE** = the same without the CAGR clause. **DOCUMENT-ONLY** = anything
else short of a kill. **KILL** = K1 or K2.

**R2 was kept exactly as Stage 1 wrote it (§6), and it binds again.** Both
families clear its first clause by a wide margin — full-window Calmar 2.8× and
2.2× the null's — and fail the second in the same 2023-01 → 2026-08 bull that
stopped ADM, HAA-Balanced and VAA-G4. That is now six of eight published points
failing on one clause, and the clause was left unamended on purpose: knowing
which clause binds and which way, moving it would have been fitting the bar to
the desired outcome. Its resolution is still the bear holdout the data does not
contain.

**R3a′ bars, as frozen** (N is the lane's **grid size**, not the count of
feasible points, so an infeasible arm cannot loosen the bar — no arm was
infeasible in any lane):

| family | native N | native bar | native `rank_median` | 2012 N | 2012 bar | 2012 `rank_median` |
|---|---|---|---|---|---|---|
| BAA-G12 | 6 | ≤ 3 | **4** | 6 | ≤ 3 | **4.5** |
| BAA-G4 | 4 | ≤ 2 | 2 | 4 | ≤ 2 | 2.0 |

R3a′ fires on BAA-G12 and clears BAA-G4, and the second half of that is worth
distrusting rather than celebrating: BAA-G4's published point is **grid rank 4
of 4 on both lanes** by `robust_score`, dead last, while its median-window rank
is top-half. The two disagree because `rank_median` is computed across the
rolling five-year sensitivity windows and never sees the holdout, whereas
`robust_score` mins over it — and BAA-G4's holdout `test` is 0.0669, the worst
number in the rotation program. R3a′ was designed to catch a spike in the
sensitivity windows and it does; it is blind by construction to a point that is
mediocre-but-consistent in-sample and collapses out of sample. Recorded as
residual 4.

**R2d — insurance delivered in the holdout** (§6, explicitly non-tiering). The
published point's holdout-`test` max drawdown against its own K1 null's, in the
identical 2023-01-03 → 2026-08-24 window, read from each lane's committed
`runs.json` on the rows with `kind == "test"` (the summary's holdout block
carries objective values only). Recomputed here for all eight published points;
the Stage-1/2 artefacts were not re-run and not touched.

| published point | holdout-test max DD | K1 null's | delta, points |
|---|---|---|---|
| GEM | −18.76% | −11.12% (`SPY60/AGG40`) | **−7.64** |
| GTAA-5 | −6.34% | −10.39% (`SPY20/EFA20/IEF20/DBC20/VNQ20`) | **+4.05** |
| HAA-Simple | −10.96% | −10.63% (`SPY60/IEF40`) | −0.33 |
| ADM | −17.63% | −12.65% (`SPY60/TLT40`) | −4.98 |
| HAA-Balanced | −14.48% | −11.10% (EW-8) | −3.38 |
| VAA-G4 | −14.23% | −10.77% (`SPY25/EFA25/EEM25/AGG25`) | −3.46 |
| BAA-G12 | −10.62% | −10.23% (`EW-12`) | −0.39 |
| BAA-G4 | −19.87% | −11.83% (`QQQ25/VWO25/VEA25/BND25`) | **−8.04** |

**Seven of eight delivered a worse holdout drawdown than their own no-timing
null.** Only GTAA-5 insured, and it is the family whose signal is a per-asset
trend filter rather than a canary. This is the input §6 wanted collected and it
cuts against the comfortable reading of Stage-2 residual 1: in this holdout the
timing families did not merely lose on return-per-unit-risk because the bull
punished timing, they lost the drawdown comparison too. The caveat is the same
one that motivates the residual — every drawdown in the table is between 6% and
20%, so this is a comparison over a shallow episode and not a bear test — but
"R2's holdout clause is only measuring the bull" is now a weaker defence than it
was before this table existed. It moves no tier this stage.

**The displacement bar for the context row does not fire, and it is not close.**
After Stage 2 the bar was `robust_score` on both lanes *and* full-window CAGR.
BAA-G12 loses all three: 0.5083 vs 0.5818 native, 0.4612 vs 0.9669 on 2012,
7.68% vs 11.58% CAGR. BAA-G4 loses them by more. HAA-Simple's `robust_score` is
recomputed by hand as pre-registered — a baseline block carries none (Stage-2
§10-4) — with the runner's own formula over the components it does carry,
`min(full.objective, sensitivity.objective.median, holdout.test)`: native
`min(0.5818, 1.0949, 1.3811) = 0.5818`, 2012 `min(0.9669, 1.1533, 1.3811) =
0.9669`. A BAA point's own score additionally mins over `neighbour_min`, so the
comparison is conservative against BAA; it did not change the answer.

## 3. Supporting numbers

Per family, from `results/sweep_rot3_<family>_<lane>/summary.json`. Quoted
together per `CLAUDE.md` §6 — never `full` alone. `grid rank` is the point's
position when the lane's grid is sorted by `robust_score` descending.

| family | lane | `robust_score` | holdout `test` | `rank_median` | `rank_worst` | grid rank | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|---|---|---|---|
| BAA-G12 | native | 0.5083 | 0.5178 | 4 | 6 | 2 of 6 | 0.5419 | 7.68% | **−14.18%** |
| BAA-G12 | 2012 | 0.4612 | 0.5178 | 4.5 | 6 | 4 of 6 | 0.4856 | 6.89% | −14.18% |
| BAA-G4 | native | 0.0669 | 0.0669 | 2 | 4 | **4 of 4** | 0.4371 | 8.76% | −20.04% |
| BAA-G4 | 2012 | 0.0669 | 0.0669 | 2.0 | 4 | **4 of 4** | 0.4289 | 8.60% | −20.05% |

Both published points have `robust_score` = holdout `test` on at least one lane
— the holdout is the minimum component, which is the same degeneracy Stage 1
found with the full window and R3a. BAA-G12's native `robust_score` is instead
pinned by `neighbour_min` 0.5083 (the `k` dimension is numeric, so the
neighbourhood term exists here; BAA-G4's grid is purely categorical and its
`neighbour_min` is `null`).

Baselines and SPY on the same native lane (2008-08-01 → 2026-08-24, identical
for both families):

| label | holdout `test` | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|
| `EW-12` | 1.4225 | 0.1960 | 7.30% | −37.27% |
| `QQQ25/VWO25/VEA25/BND25` | 1.4235 | 0.1985 | 7.80% | −39.29% |
| `ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)` | 1.3811 | 0.5818 | 11.58% | −19.91% |
| `SPY benchmark` | 1.1893 | 0.2593 | 12.21% | −47.10% |

The surprise worth naming: **BAA-G12's −14.18% is the shallowest full-window
drawdown of the five 2008-anchored published points**, better than
HAA-Balanced's −14.59%, HAA-Simple's −19.92%, ADM's −25.81% and GEM's −33.75%,
and it holds to the second decimal on the 2012 lane. Only GTAA-5 is shallower
anywhere in the program, at −13.84% on a lane starting 2007-06-01 that is not
directly comparable. The machinery does what Keller built it to do. It buys
that with the program's second-lowest CAGR: 7.68%, ahead only of GTAA-5's 4.86%,
and 4.53 points behind SPY.

## 4. Brackets (§7, 2012-01-03 window, 6-strategy roster)

Max-DD edge over `SPY benchmark` in percentage points, with the primary lane's
own 2012 window first so a window effect cannot be mistaken for a friction one,
plus §7's pre-registered flat-20 CAGR cost per point.

| point | primary net15 + cbase, 2012 lane | gross-TR + cbase (`rot3_points_tr.json`) | net15 + flat-20 (`rot3_points_c20.json`) | flat-20 CAGR cost |
|---|---|---|---|---|
| BAA-G12 | 19.56 | **20.36** | **13.22** | 2.66 |
| BAA-G4 | 13.69 | 13.83 | **7.62** | 3.07 |

Neither point has a window problem — every first-column figure is within 0.8
points of its gross-TR twin, unlike ADM's 7.96-vs-8.29-vs-6.33 pattern. Both
have a friction problem, and §7 pre-registered exactly where to look. Ranked by
flat-20 CAGR cost the program now reads: **VAA-G4 3.68, BAA-G4 3.07, BAA-G12
2.66, HAA-Balanced 2.26, ADM 1.98, HAA-Simple 1.98** — the three
all-or-nothing-canary strategies take the top three places, and their turnovers
order the same way (VAA-G4 7.60, BAA-G4 6.37, BAA-G12 5.32, ADM 4.07,
HAA-Balanced 3.32, HAA-Simple 2.36). Stage-2 residual 6's finding survives its
first out-of-family test: binary canary switching, not lookback length,
dominates turnover, and the ranked defensive top-3 does not soften it — BAA-G4
flips the same 0-or-1 switch VAA-G4 does and pays nearly as much for it.

BAA-G4's drawdown edge collapses from 13.83 to 7.62 across the bracket, losing
6.21 of its 13.83 points to friction alone; that is what fails condition B and
it is the same shape as VAA-G4's 13.67 → 6.98. BAA-G12 loses 7.13 points and
still clears the bar, because it started 6.5 points higher.

## 5. Ablations and context rows

One sentence each, never tiered (§7).

- **The `k` axis (G12: 5 / 6 / 7) says concentration barely matters.** The
  published `k = 6` is interior on both lanes with `edge: false` and a
  neighbourhood that is flat to three decimals — native `neighbour_min` 0.5083
  against `neighbour_mean` 0.5098, on 2012 0.4612 against 0.4666 — and across
  the six arms full-window drawdown moves only from −13.69% to −16.26% while
  CAGR moves from 7.00% to 8.48%; there is no concentration story here, which is
  itself the answer to one of the two questions §0 said the grid was for.
- **The canary operator answers the other one, against the published choice:**
  the unweighted `1-3-6-12U` beats Keller's `13612W` on `robust_score` in 9 of
  the 10 matched pairs across the four lanes (the exception is G12 native at
  `k = 6`, 0.5083 to 0.4792) and on holdout `test` in all five distinct
  comparisons, by margins that are not subtle — G4's 0.0669 against 0.3891 at
  the published ranking score, G12's 0.5178 against 1.1950 at `k = 6`.
- **Stage-2 residual 3 is now the best-supported finding in the program:**
  `13612W` is the weaker momentum operator on this data in every place it has
  been tested — four arms across two Stage-2 families, ten more across two
  Stage-3 families, both lanes each time, and never once the reverse on a
  holdout number.
- **G4 against G12 — concentration against breadth, inside one paper.** The
  aggressive top-1-of-4 buys 1.08 CAGR points on the native lane (8.76% against
  7.68%) and pays 5.86 drawdown points (−20.04% against −14.18%), 0.44 of
  `robust_score` on the native lane and 0.39 on 2012, the entire bracket margin,
  and the worst holdout number in the program; on this data BAA's breadth is
  the half of the paper that works.
- **BAA against the HAA-Simple context row: HAA-Simple wins the comparison that
  matters and loses the one it was expected to lose.** It keeps `robust_score`
  on both lanes (0.5818 / 0.9669 against G12's 0.5083 / 0.4612) and 3.90 CAGR
  points, while BAA-G12 takes 5.73 points of native-window drawdown off it
  (−14.18% against −19.91%) — which of BAA's three additions buys those points
  is *not* identified here, because no grid axis varied the fallback and the two
  points differ in offense, canary and defensive sleeve at once.

## 6. Decision

**BAA-G12 → DOCUMENT-ONLY.** It clears R1 by 32.93 points, prints the
shallowest full-window drawdown in the program, and survives both brackets — and
it fails R2's holdout clause, R3a′ on both lanes and R3b on the 2012 lane. The
robustness failures are not marginal: its published coordinate is 22% below the
best point on its own 2012 grid, and that better point differs from it only in
the canary operator.

**BAA-G4 → DOCUMENT-ONLY.** It is the second point in the program, after GEM,
to fail two of K2's three clauses and be saved from a KILL solely by the third;
it passes R3a′ and R3b, and fails R2 and the cost bracket. Its holdout `test` of 0.0669 is the
worst number the rotation program has produced, and its grid rank is last of
four on both lanes.

**Repo changes: none.** No spec under `specs/` other than the Stage-3
pre-registration files, no change to `winners.json`, no engine semantics
touched. The `best_of` `n`/`floor` feature stays — it is now the expression of a
published rule and is covered by tests — and BAA is the strategy that motivated
it, not a strategy that earned adoption.

**The rotation catalog is closed.** Eight published points across three stages:
one REFERENCE (HAA-Simple) and seven DOCUMENT-ONLYs, no KILLs, no PROMOTEs. Per
§10 the next increment is the composition spec — the multi-horizon score as an
alternative or OR-combined gate on the incumbent TQQQ machine — which begins in
a fresh conversation with this verdict as its input.

## Residuals worth remembering

1. **R2's holdout clause has now stopped six of eight published points, and R2d
   makes the case for amending it weaker, not stronger.** Stage-2 residual 1
   read the clause as miscalibrated against a bull-only holdout; the §2 table
   shows seven of eight points also delivered a *worse* holdout drawdown than
   their own null, so the clause is not only measuring returns. The honest
   position is unchanged and now better evidenced: the whole holdout is a
   shallow-drawdown regime, and only synthetic pre-inception history or a real
   bear will separate "these strategies do not insure" from "this window had
   nothing to insure against".
2. **`13612W` is the weaker operator on this data, everywhere, with 14 arms
   across four families behind it now.** Every family that carries it as its
   published choice — VAA-G4, BAA-G12, BAA-G4 — would score better with
   `1-3-6-12U`, and none of them may adopt that, correctly, because the
   published rule is the only adoptable coordinate. If the composition work ever
   wants a multi-horizon momentum score, this is the one to start from.
3. **BAA-G12 is the best drawdown on any 2008-anchored lane and nearly the worst
   CAGR in the catalog.** −14.18% full-window on a lane containing 2008, against
   7.68% CAGR; only GTAA-5 is shallower anywhere (−13.84%) and only GTAA-5 gives
   up more return for it (4.86%). The whole 2008-dependence discussion (Stage-2
   residual 7) applies: the 2012-lane edge of 19.56 points is real, and it is
   bought at 6.89% CAGR against SPY's 14.64%.
4. **R3a′ is blind to the holdout, and BAA-G4 is the demonstration.** A point
   that is top-half in the median sensitivity window and dead last on
   `robust_score` passes the bar, twice. `rank_median` is computed across the
   rolling five-year windows only; the fix — if the bar is ever revisited — is a
   rank on `robust_score`, not on the sensitivity objective. Not changed here:
   the bar was frozen before the runs.
5. **The all-or-nothing canary is the program's cost driver, confirmed out of
   family.** Flat-20 CAGR cost ranks VAA-G4 3.68, BAA-G4 3.07, BAA-G12 2.66
   above every per-asset or per-slot mechanism, and turnover ranks the same way.
   Any future composition that reaches for a binary regime flip should carry
   this number, not the 1.98 the incumbent machine pays.
6. **The ranked defensive top-3 with a floor is untested on its own terms.**
   This stage's grids never varied the fallback — every one of the 20 points
   carries the same `best3(…>BIL)` — so the mechanism rode along inside two
   DOCUMENT-ONLY results and was never isolated against `best(BIL+IEF)` or a
   plain top-1. It is in the engine and covered by tests. If a defensive sleeve
   is ever revisited on its own terms, this is the axis to sweep, held apart
   from the binary canary that carries BAA's costs.
