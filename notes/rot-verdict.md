# Verdict: Stage-1 rotation — GEM, GTAA-5, HAA-Simple

Spec: [ROTATION_SWEEP_SPEC.md](../docs/ROTATION_SWEEP_SPEC.md) · read protocol:
§7 · branch `rotation-sweeps` · data `tests/data/2026-08-24-net15` (primary),
gross-TR bracket `tests/data/2026-08-24`, c20 stress `specs/rot_points_c20.json`
(flat 20 bps on net15) · objective `calmar`, constraint `max_drawdown ≥ −0.50` ·
§3 extended cost map, `cash_yield` 3% · windows per §4 as amended by §12.1–2:
GEM native 2008-07-01, GTAA-5 native **2007-06-01**, HAA-Simple native
2008-07-01, all three 2012 lanes 2012-01-03 · predecessors:
[safe-switch verdict](safe-switch-verdict.md), [regime verdict](regime-verdict.md).

**Pre-registration. This file is committed before any sweep runs; §7's bars and
the labels below are frozen here so the verdict cannot move its own goalposts.
Every cell is filled afterwards from the committed artefacts only.**

## 0. What is under test, and what a win would mean

These are published strategies with pre-registered rules, so **the only
adoptable configuration per family is the as-published point** (§1). The grid is
a falsifier, not a search: a neighbour with a better `robust_score` is a
robustness datum about the published point — reassuring if the region is flat,
damning if the published point is a local dip — and never a promotion candidate.
Promoting a non-published grid point is explicitly barred, as is using the
2012-lane incumbent comparison as a promotion axis.

Pre-registered expectation (§1): this family should **cut max drawdown
materially and lose to SPY on CAGR**. The 2023-01 → 2026-08 holdout is a nearly
uninterrupted bull, where trend/momentum lags by construction, so a negative
holdout CAGR gap vs SPY is expected and is not a kill condition. Failing to
deliver the drawdown edge is (K2). A CAGR win over SPY would be the surprise to
distrust first.

## 1. Frozen labels

The as-published point per family, as the auto-labels render them:

| family | as-published label | lane files |
|---|---|---|
| GEM | `ROT SPY+VEU top1 12M@SPY>BIL fb AGG` | `sweep_rot_gem_{native,2012}` |
| GTAA-5 | `ROT SPY+EFA+IEF+DBC+VNQ top5 gap10M fb BIL` | `sweep_rot_gtaa_{native,2012}` |
| HAA-Simple | `ROT SPY top1 1-3-6-12U can TIP/1 fb best(BIL+IEF)` | `sweep_rot_haa_{native,2012}` |

The no-timing nulls and the ablation arms (never tiered — §7):

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
window**, except R3's second clause (2012 lane) and the bracket row. SPY numbers
are the same lane's baseline row.

| # | condition | GEM | GTAA-5 | HAA-Simple |
|---|---|---|---|---|
| K1 | null beats the point on full-window CAGR **and** max DD → KILL | | | |
| K2 | holdout-test max DD worse than SPY's **and** holdout-test CAGR below SPY's **and** full-window max-DD edge over SPY under 5 points → KILL | | | |
| R1 | full-window max DD better than SPY's by ≥ 10 points | | | |
| R2 | full-window Calmar > the null's, **and** holdout-test Calmar ≥ the null's | | | |
| R3a | `robust_score` ≥ 0.75 × own full-window objective | | | |
| R3b | 2012 lane: published point's full objective ≥ 0.85 × the best grid point's | | | |
| B | R1's max-DD edge (≥ 10 points) retained under both §6 brackets | | | |
| | **tier** | | | |

Tiers: **PROMOTE** = R1 ∧ R2 ∧ R3 ∧ brackets ∧ full-window CAGR ≥ SPY's.
**REFERENCE** = the same without the CAGR clause — the expected outcome for this
family. **DOCUMENT-ONLY** = anything else short of a kill. **KILL** = K1 or K2.

## 3. Supporting numbers

Per family, from `results/sweep_rot_<family>_native/summary.json` unless the row
says otherwise. Quoted together per `CLAUDE.md` §6 — never `full` alone.

| family | lane | `robust_score` | holdout `test` | `rank_worst` | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|---|---|
| GEM | native | | | | | | |
| GEM | 2012 | | | | | | |
| GTAA-5 | native | | | | | | |
| GTAA-5 | 2012 | | | | | | |
| HAA-Simple | native | | | | | | |
| HAA-Simple | 2012 | | | | | | |

Baselines and SPY on the same lanes:

| label | lane | holdout `test` | full Calmar | full CAGR | full max DD |
|---|---|---|---|---|---|
| | | | | | |

## 4. Brackets (§6, 2012-01-03 window, 10-strategy roster)

| point | gross-TR (`results/rot_points_tr.json`) max DD vs SPY | flat-20 (`results/rot_points_c20.json`) max DD vs SPY |
|---|---|---|
| GEM | | |
| GTAA-5 | | |
| HAA-Simple | | |

## 5. Ablations — where the drawdown protection lives

One sentence each, never tiered (§7).

- **Absolute-only** (`ROT SPY top1 12M@SPY>BIL fb AGG`) —
- **Relative-only** (`ROT SPY+VEU top1 12M all fb AGG`) —
- **No canary** (HAA grid arm, `can` absent) —

## 6. Decision

## Residuals worth remembering
