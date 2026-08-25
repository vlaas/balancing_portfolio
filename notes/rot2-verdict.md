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

**Pre-registration. This file is committed before any sweep runs; the §7/§2 bars
and the labels below are frozen here so the verdict cannot move its own
goalposts. Every cell is filled afterwards from the committed artefacts only.**

## 0. What is under test, and what a win would mean

The inverted purpose carries over from Stage 1 verbatim: these are published
strategies with pre-registered rules, so **the only adoptable configuration per
family is the as-published point** (§1). The grid is a falsifier, not a search —
a neighbour with a better `robust_score` is a robustness datum about the
published point, reassuring if the region is flat and damning if the published
point is a local dip, and never a promotion candidate. Promoting a non-published
grid point is explicitly barred.

Pre-registered expectation (§1): all three families should **beat SPY on max
drawdown and lose on CAGR** — REFERENCE is the ceiling we expect any of them to
reach. The 2023-01 → 2026-08 holdout remains a bull where this family lags by
construction, so a negative holdout CAGR gap vs SPY is expected and is not a kill
condition. VAA-G4 additionally carries the survey's documented out-of-sample
degradation as a skeptical prior — no formal tier cap, but a strong VAA result
should be distrusted first, not celebrated.

The headline question is HAA-Balanced (§1): Stage 1 located HAA-Simple's entire
protection in the `13612U` score and stopped at REFERENCE on CAGR alone (11.58%
vs SPY's 12.03%). Whether diversified selection across a top-4 of eight assets
closes that gap without surrendering the drawdown edge is what the `k` and score
axes are here to answer.

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
| K1 | null beats the point on full-window CAGR **and** max DD → KILL | | | |
| K2 | holdout-test max DD worse than SPY's **and** holdout-test CAGR below SPY's **and** full-window max-DD edge over SPY under 5 points → KILL | | | |
| R1 | full-window max DD better than SPY's by ≥ 10 points | | | |
| R2 | full-window Calmar > the null's, **and** holdout-test Calmar ≥ the null's | | | |
| R3a′ | `rank_median` ≤ ⌈N/2⌉ on **both** lanes, N = the lane's grid size | | | |
| R3b | 2012 lane: published point's full objective ≥ 0.85 × the best grid point's | | | |
| B | R1's max-DD edge (≥ 10 points) retained under both §5 brackets | | | |
| | **tier** | | | |

Tiers: **PROMOTE** = R1 ∧ R2 ∧ R3 ∧ brackets ∧ full-window CAGR ≥ SPY's.
**REFERENCE** = the same without the CAGR clause — the expected outcome for this
family. **DOCUMENT-ONLY** = anything else short of a kill. **KILL** = K1 or K2.

**R3a′ bars, frozen** (§2; N is the lane's **grid size**, not the count of
feasible points, so an infeasible arm cannot loosen the bar):

| family | native N | native bar | 2012 N | 2012 bar |
|---|---|---|---|---|
| ADM | 2 | ≤ 1 | 3 | ≤ 2 |
| HAA-Balanced | 9 | ≤ 5 | 9 | ≤ 5 |
| VAA-G4 | 2 | ≤ 1 | 2 | ≤ 1 |

R3a′ replaces Stage-1's R3a, which §2 proved cannot fire on a crisis-anchored
window: the full-window Calmar is the minimum component of `robust_score`
whenever the window contains the crisis, so `robust = full` by construction and
the bar is met identically. `rank_worst` was considered and rejected — the most
defensive point ranks last in bull sub-windows by design.

## 3. Supporting numbers

Per family, from `results/sweep_rot2_<family>_<lane>/summary.json`. Quoted
together per `CLAUDE.md` §6 — never `full` alone. `grid rank` is the point's
position when the lane's grid is sorted by `robust_score` descending.

| family | lane | `robust_score` | holdout `test` | `rank_median` | `rank_worst` | grid rank | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|---|---|---|---|
| ADM | native | | | | | | | | |
| ADM | 2012 | | | | | | | | |
| HAA-Balanced | native | | | | | | | | |
| HAA-Balanced | 2012 | | | | | | | | |
| VAA-G4 | native | | | | | | | | |
| VAA-G4 | 2012 | | | | | | | | |

Baselines and SPY on the same lanes:

| label | lane | holdout `test` | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|
| | | | | | |

## 4. Brackets (§5, 2012-01-03 window, 8-strategy roster)

Max-DD edge over `SPY benchmark`, in percentage points. The first column is the
primary lane's own 2012 window (not part of §5) so that a window effect cannot
be read as a friction effect.

| point | primary net15 + cbase, 2012 lane | gross-TR + cbase (`rot2_points_tr.json`) | net15 + flat-20 (`rot2_points_c20.json`) |
|---|---|---|---|
| ADM | | | |
| HAA-Balanced | | | |
| VAA-G4 | | | |

## 5. Ablations and context rows

One sentence each, never tiered (§7).

- **The `k` concentration axis** (`top3` vs `top4` vs `top5`, HAA-Balanced) —
- **Recency weighting** (`13612W` vs `1-3-6-12U`, VAA-G4 and HAA-Balanced) —
- **Plain `12M`** (HAA-Balanced's third score arm, Stage 1's protection finding) —
- **Balanced vs Simple** (§4.2 context row) —

§4.2's pre-registered reading of the context row: if Balanced beats Simple on
`robust_score` on both lanes *and* on full-window CAGR, that is the trigger for a
future HAA-consolidation note. It is **not** a tier condition here.

A baseline block carries no `robust_score` field, so Simple's is recomputed here
with `sweep.py`'s own formula over the components its block does carry —
`min(full.objective, sensitivity.objective.median, holdout.test)`. Balanced's own
`robust_score` additionally mins over `neighbour_min` (the numeric `k`
dimension), so the comparison is **conservative against Balanced**: the extra
component can only lower its side.

## 6. Decision

## Residuals worth remembering
