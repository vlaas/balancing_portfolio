# Verdict: regime-conditional safe sleeve

Spec: [SAFE_SWITCH_SPEC.md](../docs/SAFE_SWITCH_SPEC.md) · read protocol: §6 ·
branch `safe-switch` · data `tests/data/2026-08-20-net15` (primary), gross-TR
bracket `tests/data/2026-08-20`, c20 stress `--cost-bps 20 --cash-yield 0.03` ·
objective `calmar`, constraint `max_drawdown ≥ −0.50` · blend cost map,
`cash_yield` 3% · predecessors: [safe-blend verdict](safe-blend-verdict.md),
[regime verdict](regime-verdict.md).

**No switcher is adopted. The §6.3 anti-switcher placebo fired in every
artefact — the pre-registered family kill-switch — and §6.1's nested-null
promotion test failed for all 24 true switchers before it. The switch form
joins `ts_regime` as tested, inert machinery.** The result is not symmetric
noise, though: the mirrors *win*, systematically. The hypothesis had the
sign backwards, and per the pre-registration discipline that observation is
a residual for a future spec, not a promotion (§8: a new hypothesis enters
through its own spec and placebo design, never through this one's grid).

## 0. Fitted-surface accounting (§6.0)

Optimized: arm identity over 32 `safe` values × σ_target (5) × w_max (5) ×
gate (2) = 1,600 points (850 in the 2019 lane), read at the arm-best
coordinate by `robust_score`. Frozen: all four switching conditions and every
threshold, smoothing and hysteresis (§4.1, fixed by prior verdicts for other
purposes); the sleeve ratios (the blend grid's coarse triple); the windows,
costs and baselines (inherited from the blend lanes verbatim). Every claim
below is arm-best vs arm-best within one artefact.

## 1. §6.1 nested-null promotion — 0 of 24 pass

Primary lane (net), arm-best `robust_score`:

| pair | on-static B25M75 | off-static B75M25 | best true switcher | verdict |
|---|---|---|---|---|
| KMLM | **0.857** | 0.856 | 0.836 (`~B75K25@r10`) | loses to both |
| DBMF | 0.811 | **0.842** | 0.797 (`~B75D25@r10`) | loses to both |

All 16 primary-lane switchers lose to their on-static; the 8 with `off:
"BTAL"` beat pure BTAL (0.678) — the better sleeve diluted with turnover,
exactly the failure mode §6.1 names — and every one loses to its pair's
incumbent. The 2019 lane repeats it: best switcher 0.867 vs on-static 0.897
vs off-static/incumbent 0.917; there the switchers lose to the off-static
too. Verdict-ending on its own.

## 2. §6.2 window floor — no switcher improves it

`rank_worst` of the arm-best switcher never beats the incumbent's in any
lane (net KMLM: incumbent 728, best switcher 1,134; net DBMF: 627 vs 879;
2019: 463 vs 610). The floor — the entire point of paying rotation costs —
is worse everywhere.

## 3. §6.3 anti-switcher placebo — the kill-switch fires

An anti-switcher had to rank below **both** component statics. Instead,
anti-switchers beat both statics in every artefact, and the SMA-conditioned
anti is the **top-ranked arm of the whole primary lane**:

| artefact | antis beating both statics | strongest (rs vs better static) |
|---|---|---|
| net (primary) | 7 of 8 | `B75K25~B25K75@QQQ<SMA200` 0.943 vs 0.857 |
| gross-TR | 7 of 8 | same arm, 0.980 vs 0.890 |
| 2019 | 2 of 4 | `B75D25~B25D75@QQQ<SMA200` 1.008 vs 0.917 |
| c20 | 5 of 8 | same arm shape, 0.890 vs 0.832 |

Per the pre-registered rule the family verdict is: **no timing information
in the hypothesized direction; nothing is adopted.** The anti-symmetry (true
switchers depressed by roughly what mirrors gain, §4's sign table) says the
calendars are *not* pure noise at monthly cadence — they carry the opposite
sign: BTAL-heavy risk-on, MF-heavy risk-off. That is consistent with what
2022 actually was (the managed-futures banner year inside the SMA-off
window) and with the safe-blend verdict's warning that the diversifier edge
is window-conditional. It is also precisely the configuration this spec's
§1 hypothesis excluded, so it gets no promotion here.

## 4. §6.4 cross-condition sign — consistently wrong

`switcher − on-static` (robust_score, off = B75M25), primary lane:

| pair | `QQQ<SMA200` | `@1>=1.00` | `@10>=1.00<0.95` | `@10>=0.95<0.90` |
|---|---|---|---|---|
| KMLM | −0.076 | −0.024 | −0.021 | −0.022 |
| DBMF | −0.058 | −0.027 | −0.014 | −0.028 |

Negative under all four conditions, both pairs, all four artefacts — the
mirror image of the ≥3-of-4 non-negative bar. The §4.1 asymmetry prediction
held in shape: `@10>=1.00<0.95` (zero 2022 flips) is the *least* negative —
the near-placebo moved least — and the 2022-covering conditions
(`QQQ<SMA200`, 12 of 12) moved most, in the wrong direction.

## 5. §6.5 leave-one-episode-out — moot

Zero promotion candidates reached it. The machinery is delivered anyway:
`regime_report.py` now prints each off-episode's span (15 episodes for the
research default, e.g. `2018-10-17 -> 2019-02-04 (74 days)`), so the next
lane that needs episode deletion has the calendar in the causal tool.

## 6. §6.6 standard battery

- **Withholding bracket**: direction-stable. The §1–§4 orderings, the §6.1
  failures and the §6.3 kill pattern are identical on net and gross-TR
  (7 of 8 antis kill on both); no comparison changes sign.
- **Equal-risk exposure**: the VT rule is safe-invariant as required — max
  spread of average TQQQ weight across all 32 arms at matched (σ, w_max,
  gate) coordinates is 0.40 pp (median 0.09 pp), execution-level only.
- **Edge flags**: the winning antis sit at σ_target = 0.2, the grid edge,
  flagged `edge` — one more reason the mirror observation needs its own spec
  (with an extended σ grid) before being believed.
- **Holdout**: quoted with its warning — the primary test window
  (2025-01-02 → 2026-08-20, 1.63 y) contains exactly **one** off-episode
  (spring 2025) on every condition; its switcher-vs-static delta is a sample
  of one and decided nothing above.

## 7. §6.7 turnover and c20

Switchers pay for rotation: arm-best turnover 0.83–3.26 vs 0.68–1.71 for
the statics (the `@10>=0.95<0.90` arms are the 2.5–3.3 outliers — 44
month-ends of flips). The switcher premium over the on-static is negative
gross, negative net, and negative at c20 with the same sign everywhere — a
rotation strategy that loses even gross has answered the research question
in the negative before costs enter. (At c20 three KMLM switchers do edge
past the *incumbent* — flat 20 bp punishes the incumbent's high-turnover
best coordinate — but each still trails its on-static, which is §6.1's
dilution, not timing.)

## 8. Decision (§6.8)

§6.1 failed (0 of 24) and §6.3 killed the family (any single failure
suffices; there is no partial adoption). **Nothing is adopted;
WINNING_STRATEGIES.md is not created** (it has never existed — the spec's
"changes" would have been its creation). The static incumbents stand:
`B75M25` per the safe-blend verdict, SMA-200 as the only gate per the regime
verdict. What this line leaves behind, tested and engine-invariant: the
`safe` switch grammar (`{kind, on, off, when}` → `SafeSwitch` +
`Gate(assets=[])` pure conditions), the factored `_condition` kind block
shared by gates and switches, `safe_str`'s `~` rendering through the sweep
params, the pinned pure-condition Gate behaviour, and episode spans in
`regime_report.py`. A future conditional-sleeve idea is one spec file away —
and this verdict is the placebo bar it has to clear.

## Residuals worth remembering

1. **The mirror wins everywhere.** `B75M25~B25M75@QQQ<SMA200` tops the
   primary lane (0.943 vs best static 0.857), beats both statics in all four
   artefacts, survives c20, and improves `rank_worst` (551–1,082 vs the
   statics' 627–1,509). Under this spec's own §6.3 logic that is timing
   information with the opposite sign: hold BTAL-heavy while risk-on, rotate
   *into* the MF-heavy sleeve when the regime fires. Before believing it,
   remember what it is fitted to: one 2022 inside 5.7 years, σ at the grid
   edge, and the same calendars this spec froze. If it is ever specced, it
   needs its own §6.3-style placebo, an extended σ grid, and the 2019 lane's
   COVID check — where its SMA arm also won (1.008) but two of four
   conditions did not kill the placebo bar.
2. The `off: "BTAL"` switchers beat pure BTAL in every lane while losing to
   everything else — a reminder that "beats one of its sleeves" is the
   dilution signature, and §6.1's three-way bar (both sleeves *and* the
   incumbent) is what kept it from reading as signal.
3. The r10 research default was the least-negative switcher and the
   least-positive anti — a condition that fires on zero 2022 month-ends is
   inert for this decade's defining regime year, in both directions, exactly
   as §4.1 predicted in advance.
