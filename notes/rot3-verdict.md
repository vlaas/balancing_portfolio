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

*Skeleton committed before any Stage-3 run (§9 step 2). Every bar, label and
window below is frozen here; the numbers are filled in the verdict commit from
the artefacts committed in the runs commit, and from nothing else.*

**VERDICT — to be filled.**

## 0. Fitted-surface accounting

**Optimized: nothing.** Both published points were written from Keller &
Keuning (SSRN 4166845, July 2022) before a single simulation ran, and no bar
moved after the fact — the engine feature landed in `a700383`, the specs, the
labels and the bars below in the pre-registration commit, the artefacts in the
runs commit, and this file reads only those.

Surfaces: BAA-G12 6 native / 6 on 2012, BAA-G4 4 / 4 — **20 grid points** plus
baselines, the smallest stage of the three. The grid is not there to explore
BAA's parameter space (the paper already did, in-sample, over 1970–2022) but to
ask the two questions Stages 1–2 sharpened: does concentration matter (`k`), and
does the canary operator survive contact with Stage-2 residual 3. Not one of the
20 points is promotable: §7 bars promoting a non-published grid coordinate, and
§1 restates it — **the only adoptable configurations are the two as-published
points**.

Simulations: to be filled.

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
| K1 | null beats the point on full-window CAGR **and** max DD → KILL | — | — |
| K2 | holdout-test max DD worse than SPY's **and** holdout-test CAGR below SPY's **and** full-window max-DD edge over SPY under 5 points → KILL | — | — |
| R1 | full-window max DD better than SPY's by ≥ 10 points | — | — |
| R2 | full-window Calmar > the null's, **and** holdout-test Calmar ≥ the null's | — | — |
| R3a′ | `rank_median` ≤ ⌈N/2⌉ on **both** lanes | — | — |
| R3b | 2012 lane: published point's full objective ≥ 0.85 × the best grid point's | — | — |
| B | R1's max-DD edge (≥ 10 points) retained under both §7 brackets | — | — |
| | **tier** | — | — |
| R2d | *diagnostic, non-tiering:* holdout-test max DD vs the K1 null's | — | — |

Tiers: **PROMOTE** = R1 ∧ R2 ∧ R3 ∧ brackets ∧ full-window CAGR ≥ SPY's.
**REFERENCE** = the same without the CAGR clause. **DOCUMENT-ONLY** = anything
else short of a kill. **KILL** = K1 or K2.

**R2 is kept exactly as Stage 1 wrote it (§6).** It is the clause that stopped
all three Stage-2 families, and its miscalibration against a bull-only holdout
is recorded as Stage-2 residual 1. Amending it now, knowing which clause binds
and which way, would be fitting the bar to the desired outcome; the
comparability of all eight published points under identical frozen bars is worth
more than a ninth tier. Its resolution remains the bear holdout that synthetic
pre-inception history would provide.

**R3a′ bars, as frozen** (N is the lane's **grid size**, not the count of
feasible points, so an infeasible arm cannot loosen the bar):

| family | native N | native bar | native `rank_median` | 2012 N | 2012 bar | 2012 `rank_median` |
|---|---|---|---|---|---|---|
| BAA-G12 | 6 | ≤ 3 | — | 6 | ≤ 3 | — |
| BAA-G4 | 4 | ≤ 2 | — | 4 | ≤ 2 | — |

**R2d — insurance delivered in the holdout** (§6, explicitly non-tiering): the
published point's holdout-`test` max drawdown against its K1 null's, in the same
window, for both Stage-3 points *and* recomputed for all six prior published
points. `summary.json`'s holdout block carries objective values only, so the
numbers are read from each lane's committed `runs.json` on the rows with
`kind == "test"` — the Stage-1/2 artefacts are not re-run and not touched. R2d
moves no tier this stage; it is the input to the bar redesign that accompanies a
bear holdout, collected now while the lanes are identical.

**The displacement bar for the context row** (§6): after Stage 2 the bar for
displacing HAA-Simple is `robust_score` on **both** lanes *and* full-window
CAGR, and no BAA point may be adopted past it on any lesser showing — nor at all
except at the two published coordinates. One reading is pre-registered here
because the machinery does not hand it to us: a baseline block carries no
`robust_score` (Stage-2 §10-4), so HAA-Simple's is recomputed with the runner's
own formula over the components its block does carry,
`min(full.objective, sensitivity.objective.median, holdout.test)`. A BAA point's
own score additionally mins over `neighbour_min`, so the comparison is
conservative against BAA — said out loud rather than papered over.

## 3. Supporting numbers

Per family, from `results/sweep_rot3_<family>_<lane>/summary.json`. Quoted
together per `CLAUDE.md` §6 — never `full` alone. `grid rank` is the point's
position when the lane's grid is sorted by `robust_score` descending.

| family | lane | `robust_score` | holdout `test` | `rank_median` | `rank_worst` | grid rank | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|---|---|---|---|
| BAA-G12 | native | — | — | — | — | — | — | — | — |
| BAA-G12 | 2012 | — | — | — | — | — | — | — | — |
| BAA-G4 | native | — | — | — | — | — | — | — | — |
| BAA-G4 | 2012 | — | — | — | — | — | — | — | — |

Baselines and SPY on the same native lanes: to be filled.

## 4. Brackets (§7, 2012-01-03 window, 6-strategy roster)

Max-DD edge over `SPY benchmark` in percentage points, primary lane first so a
window effect cannot be mistaken for a friction one, plus §7's pre-registered
flat-20 CAGR cost per point — BAA's all-or-nothing canary is the same binary
flip mechanism that made VAA-G4 the program's turnover outlier at 3.68 CAGR
points (Stage-2 residual 6).

| point | primary net15 + cbase, 2012 lane | gross-TR + cbase (`rot3_points_tr.json`) | net15 + flat-20 (`rot3_points_c20.json`) | flat-20 CAGR cost |
|---|---|---|---|---|
| BAA-G12 | — | — | — | — |
| BAA-G4 | — | — | — | — |

## 5. Ablations and context rows

One sentence each, never tiered (§7).

- The `k` axis (G12, 5 / 6 / 7): to be filled.
- The canary operator, `13612W` vs `1-3-6-12U` — Stage-2 residual 3's fourth and
  fifth data points: to be filled.
- G4 vs G12, concentration against breadth: to be filled.
- BAA against the HAA-Simple context row: to be filled.

## 6. Decision

To be filled.

## Residuals worth remembering

To be filled.
