# Verdict: VIX/VIX3M term-structure regime gate

Spec: [REGIME_SPEC.md](../docs/REGIME_SPEC.md) · read protocol: §10 ·
branch `regime-gate` · data `tests/data/2026-08-20-net15` · objective
`calmar`, constraint `max_drawdown ≥ −0.50` · blend cost map, `cash_yield` 3% ·
research note: [VIX-Term-Structure.md](../docs/VIX-Term-Structure.md) ·
predecessor: [safe-blend verdict](safe-blend-verdict.md).

**The VIX/VIX3M gate is not adopted. The SMA-200 gate stands, and the regime
machinery is retained as a tested, inert option.** All four pilot predictions
(§11) held; none was falsified. Standalone, the term-structure gate is worse
than SMA-200 on every lane's robust score; stacked (OR), it changes at most
−0.0004 of anything the SMA gate does; the exit action (`w_off = 0`) is
dominated everywhere it appears; and the tuning surface is monotone toward
the gate doing nothing at all.

## 0. The signal's own calendar

From the three committed reports (`results/regime_report_{r10,r1,r10lo}.md`),
window 2012-01-03 → 2026-08-20, 3,679 joint days, 175 month-ends:

| setting | days off | episodes (mean len) | month-ends off | **2022 month-ends off** |
|---|---|---|---|---|
| `@10>=1.00<0.95` (research default) | 305 (8.3%) | 15 (20.3 d) | 13 | **0 of 12** |
| `@1>=1.00` (raw month-end read) | 249 (6.8%) | 87 (2.9 d) | 13 | 2 of 12 |
| `@10>=0.95<0.90` (2022 coverage) | 964 (26.2%) | 33 (29.2 d) | 44 | 7 of 12 |

The research's falsification criterion was met on day one: the default
setting was risk-off on **zero** 2022 month-ends (the SMA gate: 12 of 12).
At 13 of 175 month-ends the two 1.00-threshold settings sit just above the
~5% inertness bar — enough to measure, not enough to matter without the OR.
The only setting that covers 2022 buys that coverage by being closed a
quarter of all trading days.

## 1. Q1 — a better indicator than SMA-200? No.

§8.3 (`results/sweep_regime_2012`), standalone arms:

| arm | robust_score | rank_worst | holdout test | full max DD | CAGR |
|---|---|---|---|---|---|
| `G_sma` | **0.8625** | 7 | 1.1185 | −27.7% | 23.9% |
| `G_r1` | 0.7097 | 10 | 1.4169 | −34.9% | 24.8% |
| `G_r10` | 0.7001 | 10 | 1.3357 | −34.6% | 24.2% |
| `G_r10lo` | 0.6002 | 13 | 1.4113 | −36.6% | 21.9% |
| no gate | 0.7173 | 8 | 1.3357 | −34.6% | 24.8% |

"Better" needed all three of robust_score, rank_worst and holdout test; the
regime arms lose the first two by wide margins (−0.15 robust) and only win
the holdout because the 2023+ window contains no drawdown the SMA gate can
dodge. **No standalone regime arm even matches the no-gate baseline.**
Cross-checks agree in direction: on the 2021 winners `G_r1` is a substitute
(0.8545/0.8568/0.8824 vs `G_sma`'s 0.8556/0.8585/0.8903, same drawdown,
worse rank_worst); on the 2019 lane `G_r1` beats `G_sma` on BTAL (robust
0.6950 vs 0.6278, +1.8 pp CAGR, same DD — the pilot's prediction 4) but with
worse rank_worst (14 vs 11), and on B75D25 its robust is *lower* (0.8896 vs
0.9200). A gain that appears in one sleeve of one lane with a worse
worst-rank is margin, not signal — and §4 below shows where it comes from.

## 2. Q2 — does stacking help? No.

The bar: drawdown shallower by ≥ 1 pp with CAGR within −0.5 pp and holdout
test not worse. OR arms vs `G_sma`, per lane:

- **2012**: Δrobust −0.0004 (`OR_r1`) to −0.058 (`OR_r10lo`); Δfull max DD
  **0.0 pp** (−27.65% in every OR arm, −27.65% for `G_sma`); ΔCAGR −0.01 to
  −1.6 pp; holdout test identical (1.1185); worst sensitivity-window DD
  −27.3% everywhere. The bar fails at the first clause.
- **2021**: the OR arms are *identical* to `G_sma` to four decimals on all
  three winner sleeves — in that window the ratio closes no month-end that
  SMA-200 does not already close.
- **2019**: `OR_r1` gains robust +0.062 on BTAL entirely through CAGR
  (+1.6 pp, DD unchanged) — the same two month-ends as Q1's gain; the
  drawdown clause still fails.

Per-episode portfolio drawdowns (§8.6 confirm bundle, top-5 blocks; `·` =
below that arm's fifth-deepest):

| arm | 2015-08 | 2018-Q4 | COVID | 2022 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| no gate | · | −25.8 | −27.2 | −34.6 | −24.5 | · |
| `G_sma` | −22.5 | · | −27.2 | −27.7 | · | −23.1 |
| `G_r10` cap | · | · | −27.2 | −34.6 | −24.5 | −23.1 |
| `OR_r1` cap | −22.5 | · | −27.2 | −27.7 | · | −23.1 |
| `OR_r10` cap | −22.5 | · | −27.2 | −27.7 | · | −23.1 |

**Every cap-only arm rides COVID to −27.2%** — the February 2020 month-end
was the last look before the leg down, and a gate that never sells has
nothing to do with holdings already held (§1's measured fact, now in the
artefacts). The fast crashes are exactly where a term-structure gate was
supposed to pay, and at monthly cadence it structurally cannot.

## 3. The exit arms, on their own line

Every `w_off = 0` arm is dominated: §8.3 robust 0.538–0.613 (vs 0.8625),
full max DD deepens to −36.1…−36.6%, turnover rises to 1.15–1.47 (vs 0.89).
The COVID save is real but ruinously financed: `G_r1` exit has no
Feb-2020 episode in its top five (the pilot measured −7.4%) yet replaces it
with a **−36.3%, 1,016-day** drawdown from 2020-09-02 — sold out by a regime
release, it missed the recovery (2020 return +25.5% vs +27.7%, then the
whipsaw compounds into 2022). `OR_r1` exit's 2022 calendar return of −4.0%
(vs −21.8% for `G_sma`) is paid for in 2025: +2.5% vs +13.3% — the same
re-entry failure REBALANCE_SPEC §7.3 measured for weekly cadence, now caused
by a regime release instead of a week.

The luck check settles provenance. On the §8.2 surface at `n = 1`,
`hysteresis = 0`, `w_off = 0`: full Calmar 0.125 / 0.276 / **0.601** / 0.714
at fire 0.90 / 0.95 / 1.00 / 1.05. The COVID exit exists only at exactly
1.00 — 2020-01-31's ratio was 1.011 (a 1.1% margin, not reached at any
smoothing above n = 1) and 2025-03-31's was 1.014. One grid step to 1.05
erases both trades and the arm collapses onto the no-gate baseline. That is
a threshold coincidence, not a signal.

## 4. The §8.2 surface

Monotone, not plateaued. Mean full Calmar of the cap-only arms rises with
`fire`: 0.567 (0.90) → 0.630 (0.95) → 0.685 (1.00) → 0.714 (1.05); the
entire top-12 by robust_score sits at `fire = 1.05` — the most inert corner,
every one flagged `edge` — and no point on the surface has
robust_score above the no-gate 0.7173. **There is no plateau below 1.00**:
the practitioner 0.90–0.95 thresholds (research §2) are closed 26–84% of
days and give up 2–3 pp/yr of CAGR for zero drawdown relief, so prediction 2
stands and the §14 futures-curve validation is not worth doing. The
research's 5-vs-10-day smoothing advice has nothing to act on: at monthly
cadence the smoothing only decides which 13 month-ends the gate sees, and
none of the choices buys anything.

## 5. Whipsaw

On its own calendar the raw ratio breaches the research's stop rule badly
(87 episodes ≈ 6/yr, mean 2.9 days); the default setting is calm (15
episodes ≈ 1/yr, 20.3 days). At monthly cadence what counts is month-end
state changes: ≈ 1.8/yr for the 1.00-threshold settings — inside the rule —
but ≈ 6/yr for `@10>=0.95<0.90`, which is why its CAGR bleeds. Cap-only
turnover is unchanged (0.85–0.98 vs 0.89 gated / 0.98 ungated); the exit
arms' 1.15–1.47 is where their costs live.

## 6. Decision

- Step 2's bar on §8.3: **not cleared** (drawdown delta 0.0 pp).
- §8.4: the OR form improves **0 of 3** winners (identical to `G_sma`).
- §8.5: B75D25 `OR_r1` robust 0.9200 = `G_sma`'s 0.9200 — not worsened, not
  improved.

Per §10 step 6 the gate change is **not adopted**; no WINNING_STRATEGIES.md
is created. The SMA-200 gate remains the incumbent. What this line leaves
behind is machinery, all tested and engine-invariant: cross-symbol
indicators (`Indicator.inputs`), the `ts_regime` state machine, the `w_off`
weight clip, `AnyGate` composition, the `regime_report.py` calendar tool,
and VIX/VIX3M as index symbols in both decision-grade snapshots. A future
signal (VIX9D/VIX, VRP) is a two-line factory plus a report run away — and
this verdict is the bar it has to clear.

## Residuals worth remembering

1. The 2019-lane `G_r1` cap gain (+0.07 robust, +1.6–1.8 pp CAGR, same DD on
   both sleeves' full window) is the one genuinely positive regime result.
   It rests on two month-ends 1.1–1.4% over the 1.00 threshold and vanishes
   at `fire = 1.05`; if a later dataset adds more such month-ends, re-read
   §8.5 before dismissing it again.
2. The holdout windows (2023+) contain no crash the SMA gate helps with, so
   every regime arm "wins" the holdout while losing everything else — a
   reminder that `robust_score`'s min() is doing the work, and single-window
   Calmar would have told a different (wrong) story.
3. At monthly cadence a buy-cap gate cannot cut a fast crash's drawdown
   (COVID −27.2% in every cap arm, SMA-200 included). Any future de-risking
   idea aimed at COVID/2025-class events needs either an exit that survives
   its own re-entry problem, or a faster look — both already examined and
   rejected (here and in REBALANCE_SPEC).
