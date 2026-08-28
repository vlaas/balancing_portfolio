# Verdict: the daily series is not load-bearing — the gate is a ten-number month-end read

Spec: [MONTHLY_GATE_SPEC.md](../docs/MONTHLY_GATE_SPEC.md) · read protocol and bars:
§9–§10, **frozen at commit `5f1f846` before any lane was run** · branch `monthly-gate`
from `6cf409b` · data `tests/data/2026-08-24-net15` (the bear era on
`tests/data/2026-08-24-syn-net15`) · blend cost map plus `BIL 0.5`, `cash_yield` 3 %,
10 000 + 500 / month, monthly rebalancing · objective `calmar`, constraint
`max_drawdown ≥ −0.50` · tests M1–M5 (1023 → **1076**) · **no engine file is touched
and `SCHEMA_VERSION` stays 4**; this verdict adopts a *documentation* equivalence and
redefines no winner (§10.2).

**`sma_months: 10` is a drop-in for `sma_days: 200` at the winners' coordinates. All
four winner rows pass §10.1's band, and three of them pass it by being the same
portfolio.** On the 2021 lane the two signals agree on all 68 month-ends and all seven
window starts, so each sleeve's monthly twin is **bit-identical to its daily incumbent
across all 44 numeric columns of `runs.json` in all nine windows** — Δ `robust_score`
0.00000000, Δ window floor 0.0000 pp, turnover included. On the 2019 lane the twins
disagree once, at 2019-05-31, and the monthly arm gives back 0.0090 of full Calmar and
0.18 pp of CAGR for one gated June 2019 — while its `robust_score`, its holdout test,
its sensitivity median and its sensitivity minimum are all bit-identical, and its window
floor sits **0.0004 pp** away. Against a band of 0.02 and 1 pp, the worst row consumes
**zero** of the first arm and **0.04 %** of the second. The bear era attaches no caveat:
on 2000–2011 the monthly read is *microscopically better* (`robust_score` +0.00065, full
Calmar 0.10525207 against 0.10460356) at an identical window floor.

The mechanism is §2.1's, confirmed at bit level: the monthly-rebalanced machine consults
its gate only on window starts and month-ends, so two signals that agree on that calendar
produce the same portfolio. Four of the six §11 predictions survived. The two that failed
failed usefully, and one of them is worth more than the verdict: **a disagreeing month-end
is necessary but not sufficient for a portfolio difference**, because the gate blocks
*buys* — and at 2011-11-30, the synthetic test window's one disagreement, the machine was
selling.

## 1. Frozen labels

The three arms of every lane (§4), and the four winner rows §10.1 scores:

| name | gate object | rendering |
|---|---|---|
| — | absent | (no gate) |
| `G_sma` | `{"symbol":"QQQ","assets":["TQQQ"],"sma_days":200}` | `QQQ<SMA200` |
| `G_sma10m` | `{"symbol":"QQQ","assets":["TQQQ"],"sma_months":10}` | `QQQ<SMA10M` |

Winner rows: `B75K25`, `B75D25`, `B50K50` on `sweep_mg_2021` and `B75D25` on
`sweep_mg_2019`. Lane sizes, pinned by `--dry-run` in the pre-registration commit
(M3): **90 / 48 / 84**, confirmed on the runs.

## 2. Step 0 — the anchors reproduce, to eight decimals, inside the new sweeps

| where | arm | required (§2.3) | measured |
|---|---|---|---|
| `sweep_mg_2021` full | `G_sma` × B75K25 / B75D25 / B50K50 | 0.85294307 / 0.85739876 / 0.88489974 | **identical** |
| `sweep_mg_2021` full | no gate × the same three | 0.83354496 / 0.81272474 / 0.81407574 | **identical** |
| `sweep_mg_2019` full | `G_sma` / no gate | 0.93621129 / 0.93984909 | **identical** |
| `sweep_mg_2019` test | `G_sma` | 0.91868785 | **identical** |
| `sweep_mg_syn` full | `G_sma` / no gate | 0.10460356 / 0.01033090 | **identical** |
| `sweep_mg_syn` full | SPY baseline | 0.00553231 | **identical** |

Snap notes: `windows.holdout 2025-01-01 -> 2025-01-02` (2021 lane),
`windows.holdout 2024-01-01 -> 2024-01-02` (2019 lane), none on the synthetic lane.
The 2021 lane carries the runner's own warning, quoted as §9.0 requires:
*"test window 2025-01-02..2026-08-24 is shorter than 2 years; its metrics are noise"* —
so that lane's `test` column is read for direction, and the identity below is what
carries it.

## 3. Step 1 — the identity. **Nine windows deep, forty-four columns wide, zero differences.**

For each sleeve, the `G_sma10m` row against the `G_sma` row on **every column of
`runs.json`** (label and `params.gate` aside) in **all nine windows**:

| sleeve | windows | columns compared | differences | robust (both) | floor (both) | `rank_worst` (both) |
|---|---|---|---|---|---|---|
| `BTAL75+KMLM25` | 9 | 44 | **0** | 0.84701986 | −19.0626 % | 5 |
| `BTAL75+DBMF25` | 9 | 44 | **0** | 0.85739876 | −19.0682 % | 7 |
| `BTAL50+KMLM50` | 9 | 44 | **0** | 0.88489974 | −20.8772 % | 8 |

1188 cell comparisons, no inequality anywhere — Calmar, CAGR, max drawdown, turnover,
fees, traded value, exposure, best and worst year, all of it. This is §10.5's mechanism
check passing: the engine model of §2.1 is right, and signal equivalence on the
consultation calendar **is** portfolio identity.

## 4. Step 2 — the 2019 lane. **One gated June, and it costs nothing that is scored.**

| arm | robust | full | CAGR | max DD | sens median | sens min | floor | test | `rank_worst` |
|---|---|---|---|---|---|---|---|---|---|
| `G_sma` | 0.91868785 | 0.93621129 | 18.83 % | −20.1131 % | 0.91995598 | 0.62407788 | −20.1131 % | 0.91868785 | 2 |
| `G_sma10m` | **0.91868785** | 0.92721074 | 18.65 % | −20.1135 % | **0.91995598** | **0.62407788** | −20.1135 % | **0.91868785** | 2 |
| Δ | **+0.00000000** | −0.00900055 | −0.18 pp | −0.0004 pp | **0.00000000** | **0.00000000** | **−0.0004 pp** | **+0.00000000** | 0 |

Nine of the twelve windows are bit-identical, the holdout `test` among them. The three
that differ are exactly the three whose span contains 2019-05-31:

| window | span | `G_sma` Calmar | `G_sma10m` Calmar | Δ | Δ turnover |
|---|---|---|---|---|---|
| `full` | 2019-05-08 → 2026-08-24 | 0.93621129 | 0.92721074 | −0.00900055 | +0.0018 |
| `fit` | 2019-05-08 → 2023-12-29 | 1.02343031 | 1.00945672 | −0.01397359 | +0.0043 |
| `sens_2019-05-08` | 2019-05-08 → 2022-05-06 | 1.07833624 | 1.05646345 | −0.02187279 | +0.0078 |

`robust_score` is unmoved because it binds on the holdout test (0.91868785 < the
sensitivity median 0.91995598 < the full 0.92721074) on **both** arms, and the test
window's consultation calendar agrees everywhere. The window floor is set by
`sens_2019-05-08` on both arms — E4, which both twins traverse after re-converging at
the 2019-06-28 rebalance — and moves by four ten-thousandths of a percentage point.

## 5. Step 3 — the band (§10.1). **Four of four, with the whole band to spare.**

| row | Δ `robust_score` | band | Δ window floor | band | verdict |
|---|---|---|---|---|---|
| 2021 `B75K25` | +0.00000000 | 0.02 | +0.0000 pp | 1 pp | **PASS** |
| 2021 `B75D25` | +0.00000000 | 0.02 | +0.0000 pp | 1 pp | **PASS** |
| 2021 `B50K50` | +0.00000000 | 0.02 | +0.0000 pp | 1 pp | **PASS** |
| 2019 `B75D25` | +0.00000000 | 0.02 | −0.0004 pp | 1 pp | **PASS** |

Max |Δ `robust_score`| = **0.00000000**; max |Δ window floor| = **0.0004 pp**, one
2500th of the floor arm. The committed 2012 row, quoted beside the verdict and not
re-scored (it was decided by the composition cycle): `robust_score` 0.85720170 against
0.86123626 (−0.0040), window floor −27.3380 against −27.3341 (0.0039 pp), holdout test
identical. That row is the one place in the program where the monthly read costs
anything under the robustness machinery — and it costs a fifth of the band's first arm.

## 6. Step 4 — the bear era (§4.3, reported under §10.3). **No caveat is due.**

| arm | robust | full | CAGR | max DD | sens median | floor | test |
|---|---|---|---|---|---|---|---|
| `G_sma` | 0.10460356 | 0.10460356 | 3.75 % | −35.8578 % | 0.14801536 | −36.1178 % | 0.18771366 |
| `G_sma10m` | **0.10525207** | 0.10525207 | 3.77 % | −35.8574 % | 0.19142422 | **−36.1178 %** | **0.18771366** |
| Δ | **+0.00064851** | +0.00064851 | +0.02 pp | +0.0004 pp | +0.04340886 | **0.0000 pp** | **+0.00000000** |

The monthly twin is **not infeasible** and its window floor is **not deeper at all**, let
alone the 5 pp §10.3 would have required. On the only bear era available the extra gated
month-ends were down months, so the monthly read is microscopically *better*. **§10.3's
caveat does not attach**; the §10.2 flag ships without it.

Window partition: nine of the twenty-one windows differ — `full`, `fit`, and **seven of
the eighteen** sensitivity windows, exactly the predicted set (the six whose span
contains 2005-03-31: starts 2002-07-03, 2003-01-03, 2003-07-03, 2004-01-05, 2004-07-06,
2005-01-03; plus the one deployed 2005-07-05, where the daily SMA has crossed intramonth
and the carried month-end value has not). The twelve bit-identical windows include the
**holdout test**, which §11's prediction 3 said must differ. It does not, and why it does
not is §11's most useful result — see prediction 3 below.

## 7. Step 5 — the calendars (§4.4)

`results/gate_calendar_2012.md` and `results/gate_calendar_syn.md`, both through
`indicators.sma_monthly` — the factory the gate itself uses:

| root · window | month-ends | `SMA200` closed (changes) | `SMA10M` closed (changes) | both | `SMA200` only | `SMA10M` only |
|---|---|---|---|---|---|---|
| net15, 2012-01-03 → 2026-07-31 | 175 | 27 (20) | 29 (24) | 27 | **0** | **2** |
| syn-net15, 2000-01-03 → 2011-12-30 | 144 | 60 (27) | 62 (27) | 60 | **0** | **2** |

The superset property holds on both roots over 26 years and two bears: **every month-end
the daily rule closes, the monthly rule closes too.** All four extra closes are hairline
crossings, and the reports print them with both averages:

| month-end | close | `SMA200` | `SMA10M` | close vs `SMA200` | close vs `SMA10M` |
|---|---|---|---|---|---|
| 2016-06-30 | 101.2721 | 100.9087 | 101.3035 | +0.36 % | −0.03 % |
| 2019-05-31 | 167.2957 | 167.2291 | 167.9708 | +0.04 % | −0.40 % |
| 2005-03-31 (syn) | 31.9197 | 31.9033 | 32.0474 | +0.05 % | −0.40 % |
| 2011-11-30 (syn) | 50.5551 | 50.3590 | 50.9615 | +0.39 % | −0.80 % |

Every 2022 month-end is closed by both, on both signals — the year the gate exists for is
not a year the two rules can disagree about. The monthly rule whipsaws more (24 state
changes against 20 on the real root), which is the price of reading ten numbers instead
of two hundred, and it buys nothing and costs nothing at the winners' coordinates.

## 8. Step 6 — the panel (§4.5). **The divergence is confined to E2, exactly.**

`results/episode_mg_2019.md`, episode return % / in-window drawdown %:

| arm | E2 | E3 | E4 | E5 | E6 | E7 |
|---|---|---|---|---|---|---|
| no gate | +23.3 / −8.9 | −1.3 / −18.9 | +9.0 / −20.1 | +5.5 / −18.1 | +1.5 / −20.1 | −1.0 / −16.4 |
| `G_sma` | +23.3 / −8.9 | −1.4 / −18.9 | +9.0 / −20.1 | +5.3 / −14.7 | +1.3 / −18.4 | −1.0 / −16.4 |
| `G_sma10m` | **+21.9 / −9.0** | −1.4 / −18.9 | +9.0 / −20.1 | +5.3 / −14.7 | +1.3 / −18.4 | −1.0 / −16.4 |

E2 (2018-08-31 → 2019-12-16, read from the lane's first bar 2019-05-08) is the only
episode whose window touches 2019-05-31, and it is the only cell that moves: **−1.4 pp of
episode return**, with 0.1 pp of extra in-window drawdown. E3 through E7 print identically
to the report's precision. E1 is `·` on this lane (fewer than two bars).

## 9. Step 7 — exposure sanity

`exposure.TQQQ.avg`, twin against twin:

- 2021 lane, all three sleeves, all nine windows: max |Δ| = **0.0000000000** (the
  identity again).
- 2019 lane, twelve windows: max |Δ| = **0.0011926**, inside §9.7's 0.002 bar; on the
  full window 0.379947 against 0.379460.

The monthly twin holds fractionally *less* TQQQ on the 2019 lane, which is the gated
June 2019 and nothing else.

## 10. Step 8 — the decision (§10)

**§10.1 passes on all four winner rows, so §10.2 applies: the monthly read is adopted as
an approved live execution of the gate, in documentation only.** The winners file's
"SMA-200 gate stands" bullet gains the sentence, the four-row twin table and the
divergence calendar; `notes/comp-verdict.md`'s residual 1 is closed with a pointer.
**No winner is redefined, no committed anchor moves, and no lane is re-run with the
monthly gate** — every anchor stays `sma_days: 200`. §10.3's caveat does not attach
(§6). §10.4 does not apply.

The four-row twin table, on the net15 basis, as §10.2 requires:

| row | lane | `robust_score` | full Calmar | CAGR | window floor | holdout test |
|---|---|---|---|---|---|---|
| `B75K25` | 2021 | 0.84701986 | 0.85294307 | 16.26 % | −19.0626 % | 0.84701986 |
| `B75D25` | 2021 | 0.85739876 | 0.85739876 | 16.35 % | −19.0682 % | 0.88253297 |
| `B50K50` | 2021 | 0.88489974 | 0.88489974 | 18.49 % | −20.8772 % | 1.16742198 |
| `B75D25` | 2019 | 0.91868785 | 0.92721074 | 18.65 % | −20.1135 % | 0.91868785 |

The first three rows are the incumbents' own numbers, to eight decimals, because they
are the same portfolio. The fourth is the only place a monthly executor's history would
have differed from the committed backtest: **one gated June 2019.**

**The migration consequence, stated here so the migration spec can read it**: a correct
daily 200-bar SMA is no longer on the live-execution critical path. Ten month-end closes
of the maintained net-TR series are enough to run the gate. T1's daily-parity fixture
remains a *backtest-reproduction* requirement — the committed anchors are daily-gated and
must keep reproducing — but nobody has to compute a 200-day average to trade the machine.

## Predictions, scored (§11, frozen at `5f1f846`)

1. **The 2021 lane prints identity, nine windows deep.** ✅ **Confirmed.** Zero
   inequalities in 1188 cell comparisons (3 sleeves × 9 windows × 44 columns).
2. **The 2019 lane's Δ `robust_score` is 0.00000000.** ✅ **Confirmed**, on every clause:
   Δ robust exactly zero; sensitivity windows 2–9 bit-identical; the 2019-05-08 window
   differs by 0.0219 of Calmar against the 0.05 bound; the window floor gap is 0.0004 pp
   against the 0.01 pp bound. (§2.2's "Consequences" sentence and this prediction both
   enumerate the differing windows as *full* and *the first sensitivity window*; the
   `fit` window differs too, by the same mechanism and for the same reason — it starts
   2019-05-08 and therefore contains 2019-05-31. Recorded as erratum 2, not scored as a
   falsification: `fit` is not a scored window and the prediction's falsifier names
   windows "after the first".)
3. **The synthetic partition is exactly seven of eighteen.** ❌ **Falsified — on the test
   window, and instructively.** The partition itself is exactly right: seven of eighteen
   sensitivity windows differ, precisely the predicted set, and `fit` and `full` differ.
   Every bound holds (|Δ test| 0.00000000 ≤ 0.03; |Δ robust| 0.00064851 ≤ 0.02; |Δ floor|
   0.0000 pp ≤ 0.5 pp). But the prediction's own falsifier — *"a bit-identical fit or
   test"* — fires: **the test window is bit-identical** although it contains 2011-11-30,
   a month-end the monthly rule closes and the daily one does not.
   The reason is worth the failure. The gate **blocks buys**; it does not force a sale.
   At the 2011-11-30 rebalance the vol target was *cutting* TQQQ — the arms sell 6651
   shares at 0.349066 and buy BIL with the proceeds, identically on both — so a closed
   gate had nothing to block. **A disagreeing month-end is necessary but not sufficient
   for a portfolio difference**: it also has to be a month-end on which the machine
   wanted to buy the gated asset. Prediction 3 assumed the first condition was the whole
   of it, and §2.2's consequence tables inherit the same assumption.
4. **The band passes with two orders of magnitude to spare.** ✅ **Confirmed.** Max
   |Δ `robust_score`| = 0.00000000 (band 0.02); max |Δ window floor| = 0.0004 pp
   (band 1 pp). No row consumes a tenth of either arm.
5. **The panel confines the divergence to E2.** ✅ **Confirmed.** The E2 cells differ by
   1.4 pp of episode return, inside the predicted 0.5–3.0 pp; E3–E7 print identically.
6. **Turnover cannot tell the twins apart (|Δ| ≤ 0.005/yr on every window).** ❌
   **Falsified, on one window of twelve.** All twenty-seven of the 2021 lane's pairs
   (3 sleeves × 9 windows) are exactly 0.00000000; the 2019 lane's `sens_2019-05-08`
   window differs by
   **0.0078/yr**, above the 0.005 bound (its `fit` window, 0.0043, is inside it). The
   bound came from a full-window-only pilot (§4.6 measured +0.0018 there) and the
   sensitivity windows are shorter, so the same one gated month is spread over three
   years instead of seven. **§4.6's conclusion is unaffected**: 0.0078/yr of one-sided
   turnover at the blend map's 6 bp per side is under half a basis point of CAGR, so
   cost still cannot separate the twins and the omitted brackets were still the right
   call.

Four confirmed, two falsified. Predictions 1, 2 and 3 were jointly a test of §2.1's
engine model, and the model survives in the direction that matters: **wherever the
calendars agree, the portfolios are bit-identical** — 1188 cells on the 2021 lane, nine
windows on the 2019 lane, twelve on the synthetic. What the model got wrong is the
converse: calendars disagreeing does *not* guarantee portfolios differ.

## Residuals worth remembering

1. **A disagreeing month-end is not sufficient for divergence.** The gate blocks buys;
   on a month-end where the machine is selling the gated asset, a closed gate is inert.
   Any future spec that predicts a window partition from a signal calendar must
   intersect the calendar with the *direction of the rebalance*, not just the dates.
   (Prediction 3; the 2011-11-30 trade log is in §6's window.)
2. **The equivalence is empirical and re-checkable in one tool run.** §12's limitation
   stands unchanged: two genuinely different functions agreed at every one of their four
   crossings in 26 years because those crossings were all sub-percent. When the dataset
   rolls, `uv run score_report.py --sma-months 10` re-reads the calendar; the divergence
   table in the winners file is what a reader compares it against.
3. **The 2012 lane is the one place the monthly read is measurably worse** under the
   robustness machinery (`rank_worst` 7 against 4, sensitivity median 0.8875 against
   0.9009, `robust_score` −0.0040) — committed in `results/sweep_comp_2012`, not re-run
   here (§13), and inside the band it was later given. A reader choosing the monthly rule
   should know that its cost is not identically zero on every lane the program has run;
   it is zero on the two lanes the winners live on.
4. **A7's living-document allowlist is one entry short of its own instruction.**
   `docs/HANDOFF_EPISODE.md` §6.2 says the file "goes into A7's allowlist in the commit
   that adds it (`tests/test_episode.py`)"; commit `e5edd30` added the document without
   the entry, and `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` is absent from `LIVING` too.
   Both pass the guard today, so nothing is broken. Outside this spec's §7 scope and
   deliberately not fixed here.
5. **`m = 10` is still one convention, untested against its neighbours** (§13). This
   verdict adopts an equivalence, not a fit; nothing here licenses a grid over `m`.

## Artefacts

- `results/sweep_mg_2021/` (90 runs), `results/sweep_mg_2019/` (48),
  `results/sweep_mg_syn/` (84) — specs `specs/sweep_mg_2021.json`,
  `sweep_mg_2019.json`, `sweep_mg_syn.json`, frozen at `5f1f846`.
- `results/gate_calendar_2012.md`, `results/gate_calendar_syn.md` —
  `score_report.py --sma-months 10` on both roots.
- `results/episode_mg_2019.md` — `specs/mg_points_2019.json` through
  `episode_report.py bundle`.
- `tests/test_monthly_gate.py` M1–M5, 49 tests; the suite gains four more where
  T7's generic strategy contract picks up `specs/mg_points_2019.json`'s four
  strategies. Suite 1023 → **1076**.
