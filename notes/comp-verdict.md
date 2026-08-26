# Verdict: momentum-score gate composition on the incumbent machine

Spec: [COMPOSITION_SPEC.md](../docs/COMPOSITION_SPEC.md) · read protocol and bars:
§10, **frozen at this commit, before any lane was run** · branch `composition` ·
data `tests/data/2026-08-24-net15` (primary), gross-TR bracket
`tests/data/2026-08-24`, flat-20 stress `specs/comp_points_c20.json` · objective
`calmar`, constraint `max_drawdown ≥ −0.50` · incumbent lanes' blend cost map
(`TQQQ 1.5 / BTAL 6 / DBMF 2.5 / KMLM 6 / QQQ 1 / SPY 0.7 / * 6` bp per side),
`cash_yield` 3% · windows: 2012 lanes 2012-01-03 (holdout 2023-01-01), 2021 lane
2020-12-18 (holdout 2025-01-01), 2019 lane 2019-05-08 (holdout 2024-01-01) ·
predecessors: [regime verdict](regime-verdict.md) (the gate-composition
precedent, not adopted), [Stage-3 rotation verdict](rot3-verdict.md) (the
rotation catalog, closed).

**Verdict: pending — this file is the pre-registration skeleton.** Sections 0–8
are filled from the committed artefacts in the next commit; §1's labels, §2's
bars and §3's predictions are frozen here so the read cannot be fitted to what
the numbers turn out to be.

## 1. Frozen labels

The §7.1 named gate objects and the arms they spell on the 2012 lane's
coordinate (`VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80`, gate suffix shown):

| name | gate object | rendering |
|---|---|---|
| — | absent | (no gate) |
| `G_sma` | `{"symbol":"QQQ","assets":["TQQQ"],"sma_days":200}` | `QQQ<SMA200` |
| `G_sma0` | `G_sma` + `"w_off":0` | `QQQ<SMA200 off0` |
| `G_sma10m` | `{"symbol":"QQQ","assets":["TQQQ"],"sma_months":10}` | `QQQ<SMA10M` |
| `U` | `{"kind":"avg","months":[1,3,6,12]}` | `1-3-6-12U` |
| `G_u` | `{"symbol":"QQQ","assets":["TQQQ"],"score":U}` | `QQQ:MOMM1-3-6-12U<=0` |
| `G_u30` | `G_u` + `"w_off":0.3` | `QQQ:MOMM1-3-6-12U<=0 off30` |
| `G_u0` | `G_u` + `"w_off":0` | `QQQ:MOMM1-3-6-12U<=0 off0` |
| `G_um2` | `G_u` + `"threshold":-0.02` | `QQQ:MOMM1-3-6-12U<=m2` |
| `G_up2` | `G_u` + `"threshold":0.02` | `QQQ:MOMM1-3-6-12U<=2` |
| `G_12m` | `{"symbol":"QQQ","assets":["TQQQ"],"score":{"months":12}}` | `QQQ:MOM12M<=0` |
| `G_12m0` | `G_12m` + `"w_off":0` | `QQQ:MOM12M<=0 off0` |
| `OR_x` | `[G_sma, G_x]` | `QQQ<SMA200|<G_x>` |

The fourteen §7.2 arms in expansion order: no gate, `G_sma`, `G_sma0`,
`G_sma10m`, `G_u`, `G_u30`, `G_u0`, `G_12m`, `G_12m0`, `OR_u`, `OR_u30`,
`OR_u0`, `OR_um2`, `OR_up2`. The seven §7.4 / §7.5 arms: no gate, `G_sma`,
`G_u`, `G_u0`, `OR_u`, `OR_um2`, `OR_u0`.

Lane sizes, pinned by `--dry-run` before the runs (§7.7, test C3): 391 / 598 /
216 / 204.

## 2. The bars, frozen (§10)

The incumbent line's bars (REGIME_SPEC §10) inherited unchanged, plus the two
additions the rotation program earned (R2d, the costed comparison). The rotation
program's R-bars are **not** inherited: the composition is not a published
point, R3a′ is blind to holdout collapse, and R2 was written for a static null
this machine does not have.

0. **The calendar first.** An arm closed on fewer than ~5 % of month-ends beyond
   what `G_sma` closes is **inert** with respect to `G_sma`; report it so.
1. **Q1 — a better indicator than SMA-200?** `G_u`, `G_12m`, `G_sma10m` against
   `G_sma` on `robust_score`, `rank_worst` and the holdout `test`. "Better"
   needs all three; within ±0.02 on `robust_score` with a worse `rank_worst` is
   **"a substitute, not an improvement"**. Cross-check on §7.4 (any two of three
   winners) and §7.5 (both sleeves).
2. **Q2 — does stacking help?** `OR_u`, `OR_um2`, `OR_up2` against `G_sma`, per
   lane. **The bar: drawdown shallower by ≥ 1 pp with CAGR within −0.5 pp and
   holdout test not worse.**
3. **The exit and tilt arms on their own line.** A `w_off` arm clearing step 2's
   bar must also clear the **costed bar**: a flat-20 CAGR cost at or above
   **2.66** points (BAA-G12, the cheapest of the three binary canaries) is a
   binary flip by the program's own measure and is not adopted whatever else it
   does.
4. **The surface (§7.3).** A `G_u` point that beats `G_sma` at one threshold
   only is one month-end; its two neighbours decide.
5. **Operator ablation.** `G_12m` vs `G_u` (cap), `G_12m0` vs `G_u0` (exit),
   `G_sma10m` vs `G_sma` (daily vs monthly read).
6. **R2d — insurance in the holdout.** Every arm's holdout-test max drawdown
   against the lane's `null` arm's and against `G_sma`'s, from the
   `kind == "test"` rows of each `runs.json`. Non-tiering.
7. **Whipsaw.** Month-end state changes per year; turnover from the runs.
8. **Decision rule.** A gate change is adopted into WINNING_STRATEGIES.md only
   if it clears step 2's bar on §7.2 **and** improves at least two of the three
   winners in §7.4 (`robust_score` higher by more than 0.02 with `rank_worst`
   not worse and holdout test not worse) **and** does not worsen B75D25 in §7.5
   **and**, if it carries `w_off`, clears step 3's costed bar. Otherwise the
   SMA-200 gate stands and the score gate is retained as a tested, inert option.
   No coordinate is adopted from §7.3 alone: the surface is a falsifier.

## 3. Predictions, frozen (§11)

From the spec's pilot harness (full windows only, no robustness windows, no
ranks). Each is a falsifiable line; the artefacts replace them.

1. **The substitute loses to the incumbent on every lane, and on the 2012 lane
   to the no-gate null** (0.692 vs 0.716). The whole gap is 2022. *Falsified if
   `G_u` matches `G_sma` on `robust_score` within 0.02 on any lane.*
2. **The OR at threshold 0 fails step 2's bar on the first clause** — DD
   −27.2 % vs −27.7 % (0.5 pp), CAGR −0.8 pp, holdout test 0.950 vs 1.112 — and
   loses on all five winner rows by 0.04–0.08 Calmar. *Falsified if `OR_u`
   clears the bar on §7.2 or improves any winner.*
3. **The only gain in the program is one month-end.** `OR_um2` adds exactly
   2023-02-28 to `G_sma`'s calendar; full-window gain +0.004, holdout test lower
   (1.063 vs 1.112), loses on all five winner rows by 0.013–0.027. *Falsified if
   it beats `G_sma` by more than 0.02 with a `rank_worst` not worse.*
4. **Every exit arm is dominated, and the score exit is the worst number in the
   incumbent line**: `G_u0` prints −39.0 %, deeper than the no-gate null
   (−34.6 %), its deepest episode starting 2015-08-31. The one cell to check
   rather than dismiss: B50K50 `G_u0` (0.894 vs 0.885, DD −18.3 %, CAGR
   −2.1 pp). *Falsified if any `w_off` arm clears step 2's bar on §7.2 or §7.4.*
5. **`w_off 0.3` is inert at the winners' coordinate**, barely binds on the 2019
   lane, and is merely costly at the 2012 one. *Falsified if a `w_off 0.3` arm
   beats its cap twin anywhere.*
6. **The operator finding reverses on this machine.** `G_12m` cap ≈ no gate;
   `G_12m0` beats `G_u0` by 0.24 Calmar and 8.4 drawdown points; `G_sma10m`
   reproduces `G_sma` to 0.004. *Falsified if `G_u` beats `G_sma10m` or `G_u0`
   beats `G_12m0` on `robust_score`.*
7. **No arm changes a fast crash.** COVID −27.2 % and 2025 unchanged in every
   cap arm. *Falsified by any COVID or 2025 cell in the panel that differs from
   `G_sma`'s.*
8. **Cost does not decide this spec.** Cap arms pay 0.30–0.34 points under
   flat-20, exits 0.45–0.50 — an order of magnitude under the canary
   strategies' 2.66–3.68. The costed bar is carried and expected not to bind.
9. **The surface is monotone toward inert, with one spike** at +0.03 (0.785),
   an edge point whose one in-grid neighbour reads 0.646. *Falsified by a `G_u`
   point with `neighbour_min` above `G_sma`'s `robust_score`.*

## 4. Anchors to confirm before reading anything (§9)

| where | arm | full Calmar |
|---|---|---|
| §7.2 | no gate | 0.71623794 |
| §7.2 | `G_sma` | 0.86123626 |
| §7.4 | `G_sma` × B75K25 / B75D25 / B50K50 | 0.8529 / 0.8574 / 0.8849 |
| §7.5 | `G_sma` × B75D25 | 0.9362 |
| step 0 | `results/score_report_u.md` | reproduces §2.4 |

A mismatch is a bug in this change, not data drift.

## 0. The calendar

*pending*

## 5. Q1 — a better indicator than SMA-200?

*pending*

## 6. Q2 — does stacking help?

*pending*

## 7. The exit and tilt arms, the surface, the ablation, R2d, whipsaw

*pending*

## 8. Decision

*pending*

## Residuals worth remembering

*pending*
