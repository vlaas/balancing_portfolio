# Verdict: safe-sleeve blends

Spec: [SAFE_BLEND_SPEC.md](../docs/SAFE_BLEND_SPEC.md) · read protocol: §6 ·
branch `safe-blend` · data `tests/data/2026-08-20-net15` unless stated ·
objective `calmar`, constraint `max_drawdown ≥ −0.50` · tastytrade base costs,
`cash_yield` 3% · predecessor: [safe-swap verdict](safe-swap-verdict.md).

**The complementarity thesis is confirmed, and it selects a BTAL-heavy sleeve.**

`BTAL75+KMLM25` and `BTAL75+DBMF25` are the promotion candidates: the only
ratios that beat both of their components *and* improve the window floor, in
both lanes. At matched risk settings a blend **strictly dominates pure BTAL** —
more return and a shallower drawdown, not a trade between them. Two caveats
carry real weight: the BTAL+KMLM blend loses to pure KMLM under a 20 bp cost
stress, and the grid extension moved the edge flags rather than resolving them.

## 1. Primary ranking — 2021 lane, net

498 of 500 points feasible; the two rejects are cash arms at σ 0.40. Top-15
composition: **14 blends** (13 BTAL+KMLM, 1 BTAL+DBMF) and one pure KMLM.
BTAL, DBMF and cash do not appear at all.

| arm | best `robust_score` | full | test | sens median | `rank_worst` | maxdd | region |
|---|---|---|---|---|---|---|---|
| BTAL25+KMLM75 | **0.857** | 0.900 | 0.934 | 1.019 | 467 | −19.99% | σ0.20 / w0.4 |
| BTAL75+KMLM25 | 0.856 | 0.856 | 0.857 | 0.984 | **268** | −19.06% | σ0.20 / w0.8 |
| BTAL50+KMLM50 | 0.849 | 0.890 | 1.193 | 1.050 | 422 | −20.90% | σ0.20 / w0.8 |
| KMLM | 0.842 | 0.852 | 1.004 | 0.973 | 434 | −30.77% | σ0.30 / w0.6 |
| BTAL75+DBMF25 | 0.842 | 0.859 | 0.886 | 0.981 | **241** | −19.07% | σ0.20 / w0.8 |
| BTAL50+DBMF50 | 0.830 | 0.865 | 0.859 | 1.031 | 330 | −18.65% | σ0.20 / w0.4 |
| BTAL25+DBMF75 | 0.811 | 0.836 | 0.951 | 0.918 | 310 | −29.50% | σ0.30 / w0.6 |
| DBMF | 0.801 | 0.810 | 0.965 | 0.851 | 342 | −35.69% | σ0.35 / w0.7 |
| cash | 0.746 | 0.804 | 1.310 | 0.897 | 297 | −23.22% | σ0.20 / w0.8 |
| BTAL | 0.678 | 0.724 | 0.852 | 0.937 | 303 | −28.30% | σ0.30 / w0.8 |

All six blends beat both of their components, so §6.1's promotion test passes
**6 of 6**. Every point above is gated.

The holdout test window is 2025-01-02..2026-08-20, **1.63 years**, and carries
the runner's short-test warning: *its metrics are noise*. It is quoted because
the protocol requires it, not because it decides anything.

## 2. Withholding bracket

Rerunning on the gross-TR snapshot keeps every blend above both of its
components and gives 12 blends in the top-15 (against 14 on net). The ordering
is direction-stable, so the NET_TR_SPEC §11 tripwire **does not fire** and no
per-symbol withholding work is owed.

## 3. Complementarity — the thesis, and its own falsifier

§6.2 predicted that blends would *lose the extremes of both regimes and raise
the window minimum*. Median Calmar across each arm's grid, per window:

| window | BTAL | BTAL75+KMLM25 | BTAL50+KMLM50 | BTAL25+KMLM75 | KMLM | leader |
|---|---|---|---|---|---|---|
| sens 2020-12-18 | 0.568 | 0.688 | 0.800 | 0.883 | **0.943** | KMLM |
| sens 2021-06-18 | 0.923 | 1.034 | **1.070** | 1.047 | 1.027 | blend |
| sens 2021-12-20 | 0.689 | 0.763 | 0.823 | 0.853 | **0.870** | KMLM |
| sens 2022-06-21 | **1.021** | 0.886 | 0.761 | 0.643 | 0.536 | BTAL |
| sens 2022-12-19 | **1.344** | 1.236 | 1.149 | 1.053 | 0.992 | BTAL |
| sens 2023-06-20 | 0.887 | **0.913** | 0.889 | 0.880 | 0.874 | (cash 1.041) |
| test 2025-01-02 | 0.529 | 0.704 | 0.843 | 0.913 | **0.976** | KMLM |
| **window minimum** | 0.529 | 0.688 | **0.761** | 0.643 | 0.536 | — |

That is the predicted signature exactly: the blends win almost nothing and lose
almost nothing, and the floor rises from ~0.53 to 0.76.

**But `rank_worst` — the falsifier the spec actually named — is stricter and
splits the ratios.** Only the BTAL-heavy blends improve on *both* components:

| arm | `rank_worst` (best point) | arm minimum |
|---|---|---|
| BTAL75+DBMF25 | **241** | **163** |
| BTAL75+KMLM25 | **268** | **163** |
| BTAL | 303 | 194 |
| DBMF | 342 | 298 |
| BTAL50+KMLM50 | 422 | 244 |
| KMLM | 434 | 357 |
| BTAL25+KMLM75 | 467 | 296 |

The 50/50 and 25/75 ratios are *worse* than pure BTAL on this measure. So the
floor genuinely improves, but which ratio earns the credit depends on whether
you read the arm as a whole or the single point you would actually pick. The
BTAL-heavy ratio is the only one that survives both readings.

## 4. Ratio flatness

BTAL+KMLM scores 0.856 / 0.849 / 0.857 across its three ratios; BTAL+DBMF
0.842 / 0.830 / 0.811 — flat and mildly monotonic respectively. Neither is a
spike, so neither reads as a curve-fit.

Worth stating plainly, though: **the objective is flat in the ratio while the
robustness measures are strongly monotonic in BTAL weight.** Flatness in Calmar
is not flatness in `rank_worst`, and reading only the former would have picked
the wrong ratio.

## 5. Equal-risk check, and what the blend actually buys

Average TQQQ weight spans **0.4373–0.4400** across all ten arms — a spread of
0.0027. Nothing here is explained by one arm holding more equity.

At matched σ 0.25 / w_max 0.6 / gated:

| arm | avg TQQQ wt | CAGR | max drawdown | Calmar |
|---|---|---|---|---|
| BTAL75+KMLM25 | 0.420 | 17.96% | **−20.38%** | **0.881** |
| BTAL50+KMLM50 | 0.420 | 20.11% | −22.96% | 0.876 |
| BTAL25+KMLM75 | 0.420 | 22.17% | −25.77% | 0.860 |
| KMLM | 0.419 | **24.15%** | −28.51% | 0.847 |
| BTAL | 0.421 | 15.73% | −21.01% | 0.749 |
| cash | 0.421 | 20.13% | −28.53% | 0.706 |

Two things follow. **`BTAL75+KMLM25` strictly dominates pure BTAL** — 2.2 pp/yr
more CAGR *and* a shallower drawdown. And blend drawdowns beat linear
interpolation of their components by 1.8–2.5 pp: a 50/50 of −21.01% and −28.51%
would interpolate to about −24.8%, and lands at −22.96%. That gap is the
diversification the thesis predicted, measured rather than assumed.

This is the question the safe-swap verdict handed back — whether the safe leg
is for drawdown protection or for return — and the blend dissolves it rather
than answering it.

## 6. Dual objective

439 of 498 points clear the gated 50/50's full-window CAGR of 16.29%. Re-ranked
by shallowest drawdown subject to that floor, the top-15 is **15/15 blends** —
no pure arm appears at all.

| arm | region | max drawdown | CAGR | Calmar |
|---|---|---|---|---|
| BTAL50+KMLM50 | σ0.20 / w0.5 | −18.89% | 16.68% | 0.883 |
| BTAL75+KMLM25 | σ0.25 / w0.5 | −18.90% | 17.01% | 0.900 |
| BTAL75+KMLM25 | σ0.20 / w0.8 | −19.06% | 16.31% | 0.856 |
| BTAL75+DBMF25 | σ0.20 / w0.8 | −19.07% | 16.37% | 0.859 |

For the first time in this research line **the two objectives crown the same
family**, so the verdict does not have to choose between them. Under safe-swap
they pointed opposite ways.

## 7. Horizon — the 2019 lane

The only out-of-thesis check available, its fit window containing COVID and
2022 both. All three BTAL+DBMF blends beat both components, and
**`BTAL75+DBMF25` is both the arm best (0.917) and the best `rank_worst` (154,
against BTAL 207 and DBMF 282)** — the same ratio the primary lane selects, on
different data. Top-15: 11 blends, 4 DBMF.

## 8. Cost stress — the one casualty

At a flat 20 bp, aimed squarely at three-leg rebalancing with two 6 bp legs:

| arm | base costs | flat 20 bp |
|---|---|---|
| BTAL25+KMLM75 | 0.857 | 0.832 |
| BTAL50+KMLM50 | 0.849 | 0.829 |
| KMLM | 0.842 | **0.824** |
| BTAL75+KMLM25 | 0.856 | **0.801** ← falls below pure KMLM |
| BTAL75+DBMF25 | 0.842 | 0.799 (DBMF 0.779) |

**The ratio that wins the robustness test is the one costs hurt most.** The
50/50 and 25/75 still edge KMLM, but the margin roughly halves. `BTAL75+DBMF25`
survives its stress because DBMF's leg is 2.5 bp rather than 6. KMLM's real
spread — 3–38 bp — is now the binding uncertainty on any BTAL+KMLM
recommendation, and §7 named this in advance.

## 9. Edge flags

**9 of the top-15** in the primary lane and **13 of 15** in the 2019 lane sit on
a grid boundary. Extending σ down to 0.20 and w_max to 0.4 moved the flags
rather than resolving them: every arm-best now sits on one of the new bounds.
Extend again before believing any specific point — the *family* conclusion is
robust to this, the coordinates are not.

## 10. VT additivity

Every blend beats its own static three-way twin by **+0.36 to +0.49** full
Calmar (`TQQQ50/BTAL25/KMLM25` scores 0.410, `TQQQ50/BTAL25/DBMF25` 0.552). The
blend is not a cheaper static mix wearing a vol-target's name.

## 11. What this does not say

Scores are **not** pooled with `sweep_safe_*` — the extended grid changes both
neighbourhoods and ranks, so the pure arms' re-runs inside these artefacts are
the only valid comparison surface. Three ratios per pair is a coarse grid with
no neighbourhood metric, so §4 is a heuristic and not a flatness statistic. And
the thesis was fitted on the same 5.7 years that produced it — the
complementary-windows observation *is* the training data. The 2019 lane
mitigates that; it does not eliminate it.

The sweep also still does not size the safe leg by its own volatility or its
covariance with TQQQ. A blend with fixed sleeve fractions is deliberately the
simplest structure that tests complementarity; risk parity remains a separate
family.

## 12. Follow-ups this arms

1. **Ratio refinement as a numeric dimension** — now fired (§9 made it
   conditional on a blend winning). Needs template restructuring so the ratio
   gets a real neighbourhood, which would also give the ratio an edge flag.
2. **Another grid extension** below σ 0.20 and around w_max, per §9.
3. **KMLM execution cost** is the binding uncertainty, not a modelling gap:
   the BTAL+KMLM recommendation stands or falls on the realised spread.

## Artefacts

`results/sweep_blend_2021_net`, `_tr`, `results/sweep_blend_2019`,
`results/sweep_blend_2021_c20` — five files each, never hand-edited. Specs in
`specs/sweep_blend_{2021,2019}.json`.
