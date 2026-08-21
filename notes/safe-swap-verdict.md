# Verdict: safe-asset swap sweep

Spec: [SAFE_SWAP_SPEC.md](../docs/SAFE_SWAP_SPEC.md) · read protocol: §6 ·
branch `safe-swap` · data `tests/data/2026-08-20-net15` (net-of-15%-withholding
total return) unless stated · objective `calmar`, constraint
`max_drawdown ≥ −0.50` · costs: tastytrade base schedule, `cash_yield` 3%.

**Keep BTAL over cash. Do not promote KMLM or DBMF yet.**

The managed-futures arms win the primary lane on Calmar at equal TQQQ exposure,
and that survives both the withholding bracket and a 20 bp cost stress. But
their advantage is window-conditional, and what they actually buy is *return*,
not drawdown protection. Calmar prices that trade one way; a drawdown-first
objective would price it the other. That is the decision this sweep hands back
rather than makes.

## 1. Primary ranking — 2021 lane, net

126 of 128 grid points feasible; the two rejects are cash arms at σ 0.40
(w_max 0.7 → −51.3%, w_max 0.8 → −53.2% drawdown). Top-15 composition:
**KMLM 10, DBMF 5, BTAL 0, cash 0** — and every one of the fifteen is gated.

| arm | best `robust_score` | full | holdout test | sens median | `rank_worst` | region | edge |
|---|---|---|---|---|---|---|---|
| KMLM | **0.847** | 0.872 | 1.015 | 0.977 | 123/126 | σ0.25 / w0.5 / gate | both bounds |
| DBMF | 0.801 | 0.810 | 0.965 | 0.851 | 82/126 | σ0.35 / w0.7 / gate | interior |
| BTAL | 0.724 | 0.782 | 0.744 | 0.960 | 47/126 | σ0.25 / w0.8 / gate | yes |
| cash | 0.697 | 0.698 | 0.983 | 0.845 | 79/126 | σ0.25 / w0.5 / gate | yes |

Arm *medians* reorder the tail: KMLM 0.769 > DBMF 0.727 > **cash 0.584 > BTAL
0.533**. BTAL leads cash only at its best point; across the whole grid the cash
arm is the steadier of the two. No arm dominates — the plateau is arm-separated,
not mixed.

The holdout test window is 2025-01-02..2026-08-20, **1.63 years**, and carries
the runner's short-test warning: *its metrics are noise*. It is quoted above
because the protocol requires it, not because it decides anything.

## 2. Withholding bracket — the §11 tripwire did not fire

Rerunning the primary lane on the gross-TR snapshot (`tests/data/2026-08-20`)
bounds the true withholding from the other side.

| arm | net (w = 15%) | gross (w = 0) | Δ |
|---|---|---|---|
| KMLM | 0.847 | 0.875 | +0.028 |
| DBMF | 0.801 | 0.823 | +0.022 |
| BTAL | 0.724 | 0.735 | +0.011 |
| cash | 0.697 | 0.700 | +0.003 |

Identical ordering, identical 10/5 top-15 split. Each arm lifts in proportion to
its carry, exactly as the mechanism predicts, and nothing crosses. The true
withholding lies between these two runs, so the arm ordering is
**withholding-robust by bracketing**. No per-symbol withholding work is owed.

## 3. Horizon stability — directions hold, sub-windows do not

Cross-lane scores are never compared, only directions.

- **2019 lane** (COVID in-window, no KMLM): DBMF 0.876 > BTAL 0.769 > cash
  0.669, with DBMF taking all fifteen top slots. Same direction as the primary.
- **2012 lane** (BTAL vs cash over BTAL's whole life): BTAL 0.828 > cash 0.769,
  top-15 BTAL 13 / cash 2.

But the per-window read is where this stops being a promotion. Median Calmar
across each arm's grid, primary lane:

| window | BTAL | DBMF | KMLM | cash | leader |
|---|---|---|---|---|---|
| sens 2020-12-18 | 0.545 | 0.731 | **0.866** | 0.502 | KMLM |
| sens 2021-06-18 | 0.869 | 0.905 | **0.983** | 0.648 | KMLM |
| sens 2021-12-20 | 0.603 | 0.666 | **0.796** | 0.501 | KMLM |
| sens 2022-06-21 | **1.016** | 0.681 | 0.608 | 0.912 | BTAL |
| sens 2022-12-19 | **1.350** | 1.106 | 1.041 | 1.271 | BTAL |
| sens 2023-06-20 | 0.948 | 1.001 | 0.908 | **1.032** | cash |
| test 2025-01-02 | 0.622 | 0.958 | **0.965** | 0.925 | KMLM |

**KMLM is last in all three three-year windows starting mid-2022 or later.**
That is what `rank_worst` 123/126 encodes — the top-ranked point in the lane
also ranks 123rd out of 126 somewhere. The 2019 lane does the same thing to
DBMF, which loses the three windows starting Nov-2021 through Nov-2022 to BTAL
(1.413 vs 1.025 on sens 2022-11-08) and the last to cash.

The 2012 lane is the exception that holds up: BTAL leads **20 of 23** windows,
losing only sens 2016-07, sens 2020-07 and the holdout test.

## 4. VT additivity

Every arm beats its own static twin by a wide margin on full Calmar, so the safe
swap is nowhere a cheaper substitute for volatility targeting:

| arm | VT best | static twin | Δ |
|---|---|---|---|
| BTAL | 0.782 | 50/50 — 0.337 | **+0.445** |
| KMLM | 0.872 | TQQQ50/KMLM50 — 0.467 | +0.405 |
| DBMF | 0.810 | TQQQ50/DBMF50 — 0.474 | +0.336 |

For reference the gated 50/50 scores 0.525 and the SPY benchmark 0.606. No
static cash twin exists among the baselines, so that one comparison is unmade.

## 5. Equal-risk check — passes, and exposes the real mechanism

This was the decisive column in the first experiment and it is decisive again,
though not in the direction the ranking suggests. At matched (σ, w_max, gate)
the average TQQQ weight is **identical across arms to three decimals** — at
σ0.25/w0.5 it is 0.386 / 0.385 / 0.385 / 0.387 for BTAL / DBMF / KMLM / cash,
and the arm means span 0.5037–0.5051. Nothing here is explained by one arm
holding more equity, exactly as the VT formula implies (`w` sizes only TQQQ from
QQQ's vol, so the rule is safe-invariant).

Decomposing Calmar over the sixteen gated (σ, w_max) cells:

| arm | CAGR | max drawdown | Calmar | Sharpe | turnover | fee drag |
|---|---|---|---|---|---|---|
| DBMF | 27.1% | −34.2% | 0.792 | 0.94 | 1.06 | 0.26% |
| KMLM | 26.9% | −32.7% | 0.823 | 0.96 | 1.06 | 0.49% |
| cash | 23.0% | −34.4% | 0.673 | 0.87 | **0.52** | **0.09%** |
| BTAL | **19.5%** | **−28.4%** | 0.694 | 0.84 | 1.06 | 0.44% |

**BTAL is the best drawdown hedge by 4–5 pp and pays about 7 pp/yr of CAGR for
it.** The diversifier arms are not better hedges; they are hedges that also
earn. Whether that is an improvement depends on what the safe leg is for — a
question the objective function answers silently, and which this sweep cannot
settle on the user's behalf.

The cash arm's turnover (0.52 vs 1.06) and fee drag (9 bp vs 26–49 bp) are
already inside these numbers: doing nothing with the residual is genuinely
cheaper, and it still loses.

## 6. Edge flags

**Eleven of the top-15 sit on a grid boundary**, and KMLM's top-1 sits on
*both* σ 0.25 and w_max 0.5 — the low corner of the grid. §4.1 anticipated
precisely this ("pushes the flag to 0.5, in which case extend again before
believing"), so it stands: extend σ below 0.25 and w_max below 0.5 before that
point is worth anything.

DBMF's arm-best (σ0.35/w0.7) is the only interior arm-best in the primary lane,
which makes it the least grid-contaminated result in the table. The 2012 lane's
BTAL best (σ0.3/w0.6) is also interior.

## 7. Cash-rate asymmetry — read one-sidedly

The flat 3% `cash_yield` is anachronistic over 2012–2021, when T-bills paid
roughly nothing, so the 2012 lane's cash arm is an **upper bound on cash**, not
history. Per §6.7 that makes only one direction conclusive — and it is the one
that occurred: **BTAL beats the flattered cash arm** 0.828 to 0.769, takes 13 of
15 top slots and leads 20 of 23 windows. BTAL earns its place against a
3%-yielding nothing over its whole life. The BIL follow-up is not triggered.

The 2021 lane is roughly rate-neutral (realised short rates over 2020-12..
2026-08 average near 3%), so its ranking stands on its own.

## 8. Cost stress

At a flat 20 bp — aimed at KMLM's known 3–38 bp spread range — the ordering is
unchanged: KMLM 0.824 > DBMF 0.779 > BTAL 0.697 > cash 0.690. Execution
friction does not decide this question.

## 9. What this does not say

No cross-lane scores were merged; no "best safe" is declared from a single lane;
the primary lane's holdout test is never quoted without its length warning. The
sweep also does not model the safe leg's own volatility or its correlation to
TQQQ — a KMLM sleeve is a materially different risk object than a BTAL sleeve at
the same dollar weight, and only the realised consequence shows up here. Risk
parity over both legs remains a separate strategy family (§9).

The evidence is thin by construction: 5.7 years, two stress episodes, six
overlapping sensitivity windows, and managed-futures carry that is strategy
return rather than yield (KMLM paid four distributions in the whole window).

## 10. Follow-ups this arms

1. **Extend the grid down** — σ below 0.25, w_max below 0.5 (§6).
2. **A blend arm** (BTAL + diversifier). The arms win in complementary windows,
   which is the case for a blend rather than a swap; expressible today only as
   `fixed` weights, so it needs a `vol_target` safe-blend spec.
3. Unchanged and untriggered: per-symbol withholding (bracket held), BIL as a
   data-native cash definition (§6.7 did not fire).

## Artefacts

`results/sweep_safe_2021_net`, `_tr`, `results/sweep_safe_2019`,
`results/sweep_safe_2012`, `results/sweep_safe_2021_c20` — five files each,
never hand-edited. Specs in `specs/sweep_safe_{2021,2019,2012}.json`.
