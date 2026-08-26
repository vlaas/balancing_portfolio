# Verdict: momentum-score gate composition on the incumbent machine

Spec: [COMPOSITION_SPEC.md](../docs/COMPOSITION_SPEC.md) · read protocol and bars:
§10, **frozen at commit `3bd6737` before any lane was run** · branch `composition` ·
data `tests/data/2026-08-24-net15` (primary), gross-TR bracket
`tests/data/2026-08-24`, flat-20 stress `specs/comp_points_c20.json` · objective
`calmar`, constraint `max_drawdown ≥ −0.50` · incumbent lanes' blend cost map
(`TQQQ 1.5 / BTAL 6 / DBMF 2.5 / KMLM 6 / QQQ 1 / SPY 0.7 / * 6` bp per side),
`cash_yield` 3% · windows: 2012 lanes 2012-01-03 (holdout 2023-01-01), 2021 lane
2020-12-18 (holdout 2025-01-01), 2019 lane 2019-05-08 (holdout 2024-01-01) ·
predecessors: [regime verdict](regime-verdict.md) (the gate-composition
precedent, not adopted), [Stage-3 rotation verdict](rot3-verdict.md) (the
rotation catalog, closed).

**Nothing adopted. The SMA-200 gate stands; the score gate is retained as a
tested, inert option.** `1-3-6-12U ≤ 0` on QQQ is a *worse* trend filter than
SMA-200 on this machine — worse on `robust_score`, `rank_worst` and the holdout
test on all six lane × sleeve rows, and on the 2012 lane worse than the no-gate
null (0.6924 vs 0.7162). The OR adds four month-ends in fourteen and a half
years and moves the full-window drawdown by 0.48 pp, less than half of step 2's
1 pp bar, while costing 0.84 pp of CAGR and dropping the holdout test from 1.112
to 0.950. The one arm that beats `G_sma` at all — `OR_um2`, +0.004 on
`robust_score` — is "a substitute, not an improvement" by §10.1's own wording:
its `rank_worst` is worse (5 vs 4), its holdout test is worse (1.063 vs 1.112),
and it loses on all five winner rows. **All nine §11 predictions survived**; not
one was falsified, and the pilot's full-window numbers reproduced to three
decimals throughout. Two findings are worth more than the verdict: the
protection on this machine is the *trend filter*, not the multi-horizon score
(the plain 12-month sign beats `1-3-6-12U` in both forms, reversing HAA's
finding), and a **monthly-read SMA-10 gate reproduces the daily SMA-200 gate to
0.004 on the full window** — but not under the robustness machinery, which is
where the daily read earns its keep.

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

## 2. Anchors confirmed before anything else was read (§9)

| where | arm | required | measured |
|---|---|---|---|
| §7.2 | no gate | 0.71623794 | **0.71623794** |
| §7.2 | `G_sma` | 0.86123626 | **0.86123626** |
| §7.2 | SPY baseline | 0.43404677 | **0.43404677** |
| §7.4 | `G_sma` × B75K25 / B75D25 / B50K50 | 0.8529 / 0.8574 / 0.8849 | **0.8529 / 0.8574 / 0.8849** |
| §7.5 | `G_sma` × B75D25 | 0.9362 | **0.9362** |
| step 0 | `results/score_report_u.md` | reproduces §2.4 | **reproduces it exactly** |

Every lane's only snap note is `windows.holdout 2023-01-01 -> 2023-01-03`
(2012 lanes); no warnings on any lane.

## 3. Step 0 — the calendar

`results/score_report_u.md`, `results/score_report_12m.md`, QQQ 2012-01-03 →
2026-08-24, **175 month-ends** (last 2026-07-31):

| signal | closed | both | SMA only | signal only | 2022 | state changes |
|---|---|---|---|---|---|---|
| `QQQ<SMA200` | 27 | — | — | — | 12 of 12 | 20 |
| `MOMM1-3-6-12U ≤ 0` | 22 | 18 | 9 | 4 | 10 of 12 | 20 |
| `MOM12M ≤ 0` | 16 | 13 | 14 | 3 | 9 of 12 | 8 |

The four month-ends `1-3-6-12U` adds to the SMA gate's calendar are
**2016-06-30, 2019-05-31, 2023-01-31, 2023-02-28** — 4 of 175, **2.3 %**. By
§10.0's rule (an arm closed on fewer than ~5 % of month-ends beyond `G_sma`'s is
**inert** with respect to it) every `OR_x` arm at `threshold ≤ 0` is inert, as
§2.4 predicted, and the two 2023 dates are inside the holdout. The substitute
loses nine month-ends the SMA gate closes, two of them in 2022 (2022-01-31 at
+0.0026 and 2022-03-31 at +0.0286).

`MOM12M` is a different shape: it closes fewer month-ends (16) but flips state
only 8 times against SMA-200's 20 — a much quieter signal, and its three
signal-only dates (2023-01-31, -02-28, -03-31) are all in the holdout bull.

## 4. Step 1 — Q1: a better indicator than SMA-200? **No.**

`robust_score` / `rank_worst` / holdout `test`, against `G_sma` on its own lane:

| lane · sleeve | `G_sma` | `G_u` | `G_12m` | `G_sma10m` | no gate |
|---|---|---|---|---|---|
| 2012 · BTAL | **0.8612** / 4 / 1.112 | 0.6924 / 14 / 0.955 | 0.7198 / 12 / 0.918 | 0.8572 / 7 / 1.112 | 0.7162 / 13 / 1.328 |
| 2021 · B75K25 | **0.8470** / 9 / 0.847 | 0.7252 / 20 / 0.877 | — | — | 0.8335 / 17 / 0.874 |
| 2021 · B75D25 | **0.8574** / 11 / 0.883 | 0.7246 / 21 / 0.915 | — | — | 0.8127 / 15 / 0.909 |
| 2021 · B50K50 | **0.8849** / 14 / 1.167 | 0.7583 / 18 / 1.213 | — | — | 0.8141 / 18 / 1.121 |
| 2019 · BTAL | 0.6280 / 10 / 0.789 | 0.5555 / 14 / 0.804 | — | — | **0.6361** / 14 / 0.800 |
| 2019 · B75D25 | **0.9187** / 5 / 0.919 | 0.7129 / 13 / 0.935 | — | — | 0.8396 / 8 / 0.844 |

`G_u` is 0.073–0.206 below `G_sma` on `robust_score` on every one of the six
rows and its `rank_worst` is worse on every one — nowhere near §10.1's ±0.02
substitute band, so it is not even "a substitute". It also loses to the
**no-gate null** on the 2012 lane (0.6924 vs 0.7162) and on both 2021 sleeves it
does not gate at all better than doing nothing. `G_12m` is likewise below both
`G_sma` and the null.

`G_sma10m` is the one arm the band applies to: `robust_score` 0.8572 vs 0.8612
(−0.004), holdout test identical (1.112), full-window episodes identical, but
`rank_worst` 7 vs 4 and sensitivity median 0.8875 vs 0.9009. **A substitute, not
an improvement** — §10.1's exact case. (Residual 1.)

## 5. Step 2 — Q2: does stacking help? **No arm clears the bar.**

The bar: **drawdown shallower by ≥ 1 pp, CAGR within −0.5 pp, holdout test not
worse.** Against `G_sma` on the 2012 lane (max DD −27.65 %, CAGR 23.82 %, test
1.112, `robust_score` 0.8612, worst sensitivity-window DD −27.33 %):

| arm | Δ max DD | Δ CAGR | Δ holdout test | Δ robust | worst sens DD | verdict |
|---|---|---|---|---|---|---|
| `OR_u` | **+0.48 pp** (−27.17) | −0.84 pp | −0.162 | −0.015 | −27.17 | fails all three |
| `OR_um2` | **+0.41 pp** (−27.24) | −0.25 pp ✓ | −0.049 | +0.004 | −27.17 | fails 1 and 3 |
| `OR_up2` | **+0.49 pp** (−27.16) | −2.37 pp | −0.162 | −0.072 | −27.16 | fails all three |

Every OR arm fails the **first** clause: the composition moves the full-window
drawdown by less than half a point, because the incumbent's maximum has already
moved off the 2022 episode onto COVID's −27.2 %, which no cap arm touches. On
the winners' lanes the OR loses outright — `OR_u` by 0.045–0.085 `robust_score`
on all five rows, `OR_um2` by 0.013–0.027 on full Calmar (0.8277 / 0.8306 /
0.8595 vs 0.8529 / 0.8574 / 0.8849 in 2021; 0.6150 / 0.9166 vs 0.6280 / 0.9362
in 2019) — so §10.8's "improves at least two of the three winners" is failed by
every arm, and §10.8's "does not worsen B75D25 in §7.5" is failed too.

Per-episode drawdowns (`results/comp_points.json`, top-5 blocks, keyed by the
episode's **peak**; `·` = below that arm's fifth-deepest, REGIME_SPEC erratum 8):

| arm | 2015-08 | 2018-Q4 | COVID | 2020-09 | 2022 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| no gate | · | −25.8 | −27.2 | −25.1 | **−34.6** | −24.5 | · |
| `G_sma` | −22.5 | · | −27.2 | −25.1 | −27.7 | · | −23.1 |
| `G_sma0` | −36.1 | · | −27.2 | −25.1 | · | −23.0 | −29.3 |
| `G_sma10m` | −22.5 | · | −27.2 | −25.1 | −27.7 | · | −23.1 |
| `G_u` | · | −25.7 | −27.2 | −25.1 | −32.3 | · | −23.1 |
| `G_u30` | −25.5 | −25.8 | −27.2 | −25.1 | −32.3 | · | · |
| `G_u0` | **−39.0** | −25.8 | −27.2 | −25.1 | −32.3 | · | · |
| `G_12m` | · | −25.8 | −27.2 | −25.1 | −32.0 | −24.5 | · |
| `G_12m0` | −28.7 | −26.6 | −27.2 | −25.1 | −30.6 | · | · |
| `OR_u` | −22.5 | · | −27.2 | −25.1 | −26.9 | · | −23.1 |
| `OR_u30` | −25.5 | · | −27.2 | −25.1 | −26.9 | · | −23.1 |
| `OR_u0` | −39.0 | −24.8 | −27.2 | −25.1 | · | · | −23.1 |
| `OR_um2` | −22.5 | · | −27.2 | −25.1 | −27.2 | · | −23.1 |
| `OR_up2` | −22.5 | · | −27.2 | −25.1 | −26.9 | · | −23.1 |
| SPY | −13.2 | −19.5 | **−33.7** | · | −24.6 | −18.8 | · |

The whole of the composition's effect is the 2022 column: `G_sma` −27.7,
`OR_u` −26.9, `OR_um2` −27.2 — and the arm's *maximum* is COVID's −27.2 either
way. **COVID is −27.2 % in every single arm**, exactly as §1 said it would be:
the score reads +0.0607 on 2020-02-28 and the SMA gate closes only at the
following month-end. (Prediction 7 stands; the 2025 cells are bounded by panel
depth — `G_sma` and every score cap arm hide theirs below their fifth-deepest,
while the two arms that never gated 2025's leg down, no gate and `G_12m`, show
−24.5.)

## 6. Step 3 — the exit and tilt arms, on their own line

| arm | robust | full | max DD | CAGR | turnover | 2020 | 2022 | 2025 | flat-20 cost |
|---|---|---|---|---|---|---|---|---|---|
| `G_sma` | **0.8612** | 0.8612 | −27.65 | 23.82 | 0.88 | +27.7 | −21.8 | +13.3 | **0.31** |
| `G_sma0` | 0.5344 | 0.5541 | −36.13 | 20.02 | 1.24 | +18.6 | −0.9 | +2.5 | 0.50 |
| `G_u30` | 0.6658 | 0.6658 | −32.29 | 21.50 | 0.93 | +27.7 | −28.0 | +13.4 | 0.33 |
| `G_u0` | 0.4556 | 0.4587 | **−39.02** | 17.90 | 1.23 | +18.6 | −20.3 | +13.9 | 0.47 |
| `G_12m0` | 0.6498 | 0.6988 | −30.56 | 21.35 | 1.00 | +27.7 | −18.2 | +13.2 | 0.38 |
| `OR_u30` | 0.7763 | 0.8118 | −27.16 | 22.05 | 0.91 | +27.7 | −21.8 | +12.4 | 0.33 |
| `OR_u0` | 0.4752 | 0.4752 | −39.02 | 18.54 | 1.16 | +18.6 | −4.0 | +2.5 | 0.45 |

**`G_u0` is the worst number in the incumbent line**: −39.02 %, deeper than the
no-gate null's −34.57 %, from an episode running 2015-07-20 → 2016-11-14 — the
score sold TQQQ at the 2015-08-31 month-end and the re-entry failure REGIME_SPEC
§3 measured for the ratio repeats. The exits also give up the 2020 rebound
wholesale: +18.6 % against +27.7 % for every cap arm.

No `w_off` arm clears step 2's bar on §7.2, so the **costed bar is not reached**;
it is reported anyway because §10.3 carries it. Every arm in the program pays
0.30–0.50 points of CAGR under flat-20 — against the binary canaries' 2.66
(BAA-G12), 3.07 (BAA-G4) and 3.68 (VAA-G4). Turnover explains it: 0.86–1.24 here
against VAA-G4's 7.60. **Cost does not decide this spec.**

Drawdown edge over SPY (points, primary / gross-TR / flat-20; SPY's max DD
−33.74 / −33.66 / −33.77 %) — positive is shallower than SPY:

| arm | flat-20 cost | DD edge | turnover |
|---|---|---|---|
| no gate | 0.34 | −0.83 / −0.92 / −1.02 | 0.98 |
| `G_sma` | 0.31 | 6.08 / 6.11 / 5.92 | 0.88 |
| `G_sma10m` | 0.30 | 6.08 / 6.11 / 5.92 | 0.88 |
| `G_u` | 0.30 | 1.45 / 1.37 / 1.36 | 0.89 |
| `G_12m` | 0.31 | 1.77 / 1.70 / 1.68 | 0.91 |
| `G_12m0` | 0.38 | 3.18 / 3.11 / 3.04 | 1.00 |
| `OR_u` | 0.30 | **6.57 / 6.50 / 6.53** | 0.86 |
| `OR_um2` | 0.30 | 6.50 / 6.50 / 6.37 | 0.87 |
| `G_u0` | 0.47 | −5.28 / −5.39 / −6.16 | 1.23 |
| `OR_u0` | 0.45 | −5.29 / −5.39 / −6.16 | 1.16 |

Both brackets are inert: the withholding bracket moves every edge by ≤ 0.09
points and the flat-20 bracket by ≤ 0.9.

**The one cell §11 said to check rather than dismiss.** 2021 · B50K50 `G_u0`:
`robust_score` 0.8945 vs `G_sma`'s 0.8849 (+0.0096, inside the ±0.02 substitute
band), max DD −18.33 % vs −20.90 % — **2.57 pp shallower, the drawdown clause
passed** — worst sensitivity-window DD −18.34 % (the best on that lane), holdout
test 1.216 vs 1.167 (better). It fails on **CAGR: 16.40 % vs 18.49 %, −2.09 pp,
four times the clause's width**, and on `rank_worst` (16 vs 14). It is also the
only one of the six lane × sleeve rows where any exit arm does this, so §10.8's
"two of the three winners" is out of reach regardless. Retained as residual 3.

## 7. Step 4 — the threshold surface (§7.3)

`G_u`, full Calmar by `threshold` × `w_off` (`neighbour_min` in brackets):

| threshold | cap | `w_off 0.3` | exit |
|---|---|---|---|
| −0.03 † | 0.7202 [0.7195] | 0.7165 [0.7071] | 0.6832 [0.6528] |
| −0.02 | 0.7195 [0.6958] | 0.7071 [0.6828] | 0.6528 [0.4889] |
| −0.01 | 0.6958 [0.6924] | 0.6828 [0.6658] | 0.4889 [0.4587] |
| 0 | 0.6924 [0.6866] | 0.6658 [0.6580] | 0.4587 [0.4503] |
| +0.01 | 0.6866 [0.6459] | 0.6580 [0.6052] | 0.4503 [0.3958] |
| +0.02 | 0.6459 [0.6866] | 0.6052 [0.6580] | 0.3958 [0.4503] |
| +0.03 † | **0.7854** [0.6459] | 0.7376 [0.6052] | 0.4688 [0.3958] |

† on the grid edge. **Not one of the 21 points reaches `G_sma`'s
`robust_score` of 0.8612** — the surface's maximum `robust_score` is 0.7195
(threshold −0.03, cap), an edge point, and the highest `neighbour_min` anywhere
on it is 0.7195. The +0.03 spike is exactly what §11 called it: `full` 0.7854
where the score finally covers all twelve 2022 month-ends (35 closed in total),
but its one in-grid neighbour reads 0.6459, so its `robust_score` is 0.6459 and
its `edge` flag is set. The surface is monotone toward inert as the threshold
falls — at −0.03 the gate closes 15 month-ends, 14 of them shared with SMA-200,
and prints 0.7202 against the **no-gate null's 0.7162**. Extending the grid
downward walks to "no gate", not to the incumbent. §10.4's luck check has
nothing to fire on: no `G_u` point beats `G_sma` at any threshold, one step or
otherwise.

## 8. Step 5 — the operator ablation: HAA's finding reverses here

| pair | form | `robust_score` | full Calmar | max DD |
|---|---|---|---|---|
| `G_12m` vs `G_u` | cap | 0.7198 vs 0.6924 (**+0.027**) | 0.7198 vs 0.6924 | −31.97 vs −32.29 |
| `G_12m0` vs `G_u0` | exit | 0.6498 vs 0.4556 (**+0.194**) | 0.6988 vs 0.4587 (**+0.240**) | −30.56 vs −39.02 (**+8.46 pp**) |
| `G_sma10m` vs `G_sma` | cap | 0.8572 vs 0.8612 (−0.004) | 0.8572 vs 0.8612 | −27.66 vs −27.65 |

On the rotation machine the protection lived in the multi-horizon score
(plain-`12M` −33.7 % vs `1-3-6-12U` −19.9 %, rot-verdict §5). **On this machine
the 12-month sign wins in both forms**, by 0.24 Calmar and 8.46 drawdown points
in the exit form — the number §11 predicted to two decimals. The protection here
is the *trend filter*: `G_sma10m`, a monthly-read Faber filter already in the
grammar, reproduces the daily SMA-200 gate to 0.004 full Calmar with identical
episodes, identical holdout test and identical turnover. The multi-horizon score
is a slower, noisier version of the same signal, and a slower one is worse.

## 9. Step 6 — R2d, insurance in the holdout

Holdout-test max drawdown (%), from the `kind == "test"` rows of each lane's
`runs.json`. 2012 lane (holdout 2023-01-03 → 2026-08-24; the lane's own no-timing
null is the `no gate` arm at −24.46):

| arm | test max DD | vs null | vs `G_sma` |
|---|---|---|---|
| no gate | −24.46 | — | −1.36 |
| `G_sma` | −23.10 | **+1.36** | — |
| `G_sma10m` | −23.10 | +1.36 | 0.00 |
| `G_u` / `G_u30` / `G_u0` | −23.09 | +1.37 | +0.01 |
| `OR_u` / `OR_up2` / `OR_u0` | −23.08 | +1.38 | +0.02 |
| `OR_u30` / `OR_um2` | −23.07 | +1.39 | +0.03 |
| `G_12m` / `G_12m0` | −24.45 | +0.01 | −1.35 |
| `G_sma0` | −29.25 | **−4.79** | −6.15 |

Twelve of fourteen arms insure — the reverse of the rotation program's 1 of 8 —
but the insurance is the trend filter's, not the composition's: every score and
OR arm lands within 0.03 pp of `G_sma`. `G_12m` does not insure at all (it is
open through the whole holdout drawdown), and the SMA **exit** arm actively
un-insures by 4.79 pp. On the winners' lanes the spread is smaller still
(2021 · B75K25: null −16.18, every arm −16.16 to −16.22; 2021 · B50K50: null
−15.96, `G_sma` −14.86, `G_u` −14.81; 2019 · B75D25: null −20.09, `G_sma`
−18.19, `G_u0` −16.82 the best, `OR_u0` −19.81 the worst). Handoff §3.4's caveat
applies in full: every 2023–26 drawdown is 15–29 %, a shallow episode, and this
diagnostic does not tier anything.

## 10. Step 7 — whipsaw

Month-end state changes over 175 month-ends: `QQQ<SMA200` 20 (1.38 / yr),
`MOMM1-3-6-12U ≤ 0` 20 (1.38 / yr), `MOM12M ≤ 0` 8 (0.55 / yr). The
multi-horizon score's whipsaw is *identical* to the incumbent's, which is why
§13 left hysteresis out and why nothing here argues for adding it.

Turnover, 2012 lane full window: no gate 0.98; cap gates 0.86–0.91 (`OR_u`
lowest at 0.86 — a closed gate blocks buys, so stacking gates lowers turnover);
`w_off 0.3` 0.91–0.93; exits 1.16–1.24. The 2021 and 2019 lanes run 1.62–1.84
throughout, dominated by the sleeve's own rebalancing. All of it is an order of
magnitude under VAA-G4's 7.60.

## 11. Step 8 — decision

**Not adopted.** §10.8 requires all four clauses; the composition fails every
one of them:

- *clears step 2's bar on §7.2* — **no**: the best OR arm moves the drawdown
  0.48 pp against a 1 pp bar, and its holdout test is worse.
- *improves at least two of the three winners in §7.4* — **no**: every OR and
  score arm is below `G_sma` on all three sleeves, by 0.019–0.078
  `robust_score`.
- *does not worsen B75D25 in §7.5* — **no**: `OR_u` 0.8341, `OR_um2` 0.8635,
  `G_u` 0.7129 against `G_sma`'s 0.9187.
- *the costed bar for a `w_off` arm* — not reached, and would not have bound
  (0.45–0.50 against 2.66).

No coordinate is adopted from §7.3 either; §10 forbids it and the surface never
gets within 0.14 of `G_sma` anyway. **The SMA-200 gate stands.**
`WINNING_STRATEGIES.md` is unchanged — the file has never existed
(SAFE_SWITCH_SPEC erratum 8) and step 8 said no, so it is not created.

What is kept: the `score` gate kind, its grammar, `score_report.py`, and the
1 450 simulations that say the composition is a substitute at best. The engine
gained a fourth gate kind that composes with `AnyGate` for free and makes a
score-conditioned `SafeSwitch` expressible; the research line gained a measured
"no".

### Predictions, scored (§11, frozen at `3bd6737`)

| # | claim | outcome |
|---|---|---|
| 1 | the substitute loses to the incumbent on every lane and to the 2012 null | **held** — 0.6924 vs 0.7162 vs 0.8612; gap 0.073–0.206 on all six rows |
| 2 | the OR at threshold 0 fails the bar on the first clause | **held** — +0.48 pp, CAGR −0.84, test 0.950; loses 0.045–0.085 on all five winner rows |
| 3 | the only gain in the program is one month-end | **held** — `OR_um2` +0.004 robust, fit Calmar 0.834 = `G_sma`'s, test 1.063 < 1.112, `rank_worst` 5 vs 4; loses 0.013–0.027 on all five winner rows |
| 4 | every exit arm is dominated; the score exit is the worst number in the line | **held** — −39.02 %, peak 2015-07-20; B50K50 `G_u0` fails CAGR by 2.09 pp |
| 5 | `w_off 0.3` never beats its cap twin | **held on the 2012 lane** (0.6658 vs 0.6924; 0.8118 vs 0.8460); §7.4 / §7.5 carry no `w_off 0.3` arm, so the "inert at the winners' coordinate" half is untested here |
| 6 | the operator finding reverses on this machine | **held** — `G_12m0` beats `G_u0` by 0.240 Calmar and 8.46 DD points; `G_sma10m` reproduces `G_sma` to 0.004 |
| 7 | no arm changes a fast crash | **held** — COVID −27.2 % in all fourteen arms |
| 8 | cost does not decide this spec | **held** — 0.30–0.50 points against 2.66–3.68 |
| 9 | the surface is monotone toward inert with one spike | **held** — max `neighbour_min` 0.7195 vs `G_sma`'s 0.8612; +0.03 spike's `neighbour_min` 0.6459 |

The pilot harness's full-window numbers reproduced to three decimals on every
arm it quoted, and the brackets to two — the §11 table can be read as measured,
not merely as expected.

## Residuals worth remembering

1. **`G_sma10m` is the free arm the program never ran, and it nearly wins.** A
   monthly-read Faber filter reproduces the daily SMA-200 gate to 0.004 full
   Calmar, with the same episodes, the same holdout test (1.112), the same
   turnover (0.88) and the same flat-20 cost. Where it loses is exactly where
   the robustness machinery is designed to look: `rank_worst` 7 vs 4,
   sensitivity median 0.8875 vs 0.9009. So the daily read *is* load-bearing —
   but for stability across sub-windows, not for the headline. A monthly-only
   implementation of the incumbent remains on the table and now has a number
   attached to what it would cost.
2. **The 2019 · BTAL lane's gate is not load-bearing at all**: the no-gate null
   (0.6361) beats `G_sma` (0.6280) there. Any gate comparison on that lane is
   bounded by that fact, and it is why §7.5 exists as a "does not worsen" check
   rather than as evidence.
3. **2021 · B50K50 `G_u0`** is the single cell in the program where a score arm
   clears the drawdown clause: −18.33 % vs −20.90 % (2.57 pp), worst
   sensitivity-window DD −18.34 % (best on the lane), holdout test 1.216 vs
   1.167. It dies on CAGR (−2.09 pp) and `rank_worst` (16 vs 14). If a
   drawdown-first variant of the B50K50 arm is ever wanted, this is where to
   start — and the first thing to check is whether the edge is the 2015-style
   re-entry failure showing up as a *benefit* in a window that has no 2015 in it.
4. **`MOM12M` is the quiet operator.** 8 state changes against 20, and in the
   exit form it beats `1-3-6-12U` by 0.24 Calmar. Nothing in this spec wants an
   exit form, but if one is ever built the operator is the 12-month sign, not
   the multi-horizon mean — the opposite of the rotation catalog's conclusion,
   and the cleanest evidence yet that the two machines want different signals.
5. **Every single arm carries the 2020-09-02 → 2021-03-08 drawdown at −25.1 %**,
   identical to two decimals across all fourteen. QQQ held above its SMA-200 and
   the score stayed positive throughout; no gate in the catalog — trend, term
   structure or momentum — touches it. It is the machine's uninsured episode.
6. **The OR's two added holdout month-ends are the cost, not the benefit.**
   2023-01-31 and 2023-02-28 are the first two months of the 2023 bull; closing
   the gate there is why every OR arm's holdout test sits at 0.950 against
   `G_sma`'s 1.112. §12's note stands: the holdout contains the month-ends the
   OR adds, and only synthetic pre-inception history (handoff §7) separates "the
   score does not insure" from "this holdout had nothing to insure against" —
   except that the 2012 lane *does* contain 2022, and the score under-covers it
   by two month-ends.
7. **`OR_um3` was never run.** §11 claimed it is identical to `OR_um2`; §7.2's
   grid carries no such arm and §7.3's threshold surface has no OR column, so
   the claim is untested. It is one grid point if anyone wants it.
