# Verdict: one ticker is not the machine — and matching its floor costs 9.6 pp/yr

Spec: [RETURN_STACKED_SPEC.md](../docs/RETURN_STACKED_SPEC.md) · read protocol and bars:
§9–§10, **frozen at commit `ede53d3` before any lane was run** · branch `return-stacked`
from `dd2b4a8` · data `tests/data/2026-08-24-net15` (the `_tr` bracket on
`tests/data/2026-08-24`) · blend cost map plus `BIL 0.5`, the nine statics at the `*` 6 bp
catch-all, `cash_yield` 3 %, 10 000 + 500 / month, monthly rebalancing · objective
`calmar`, constraint `max_drawdown ≥ −0.50` · tests D1–D5 (979 → **1023**) · **no engine
file is touched and `SCHEMA_VERSION` stays 4**; this spec adopts nothing and could only
ever have adopted a *static alternative* row (§3).

**No static is a substitute for the machine.** On the decision lane every one of the four
grid points fails clause (i) of the bar by 0.63–0.67 of `robust_score` (0.2482–0.2846
against B75D25's score₃ 0.9187, where the bar wanted +0.02) and clause (iv) with at most
2 wins of 9 sensitivity windows; clause (iii) passes for exactly one point, `NTSX50/BIL50`,
whose floor is 3.66 pp shallower than the incumbent's. Clause (ii) passes for all four —
the 2024–26 holdout is a bull market with a tariff dip, where a bond-hedged static is the
better thing to hold — and that is the whole of what the statics win. The pre-registered
outcome, **10.4(b)**, fires exactly as written.

The number the spec was really built to produce is §10.2's, and it is read whatever the
bar says: deleveraged with BIL until its window floor matches the machine's, a static NTSX
blend earns **9.58 pp/yr less CAGR** than B75D25 — 9.25 % against 18.83 %, at NTSX
fraction 0.625, floors −20.39 % against −20.11 %. That is the price of the machine's
operational cost, stated in the currency a reader outside the program actually spends.

## 1. Frozen labels

Grid, decision lane: `NTSX100`, `NTSX75/BIL25`, `NTSX62.5/BIL37.5`, `NTSX50/BIL50`.
Winners' lane adds `RPAR100`, `NTSX50/RPAR50`. 2022 cohort: `NTSI100`, `NTSE100`,
`UPAR100`, `GDE100`, `NTSX50/GDE50`, `NTSX34/NTSI33/NTSE33`. 2023 panel: `RSST100`,
`RSSB100`, `RSBT100`, `RSSB50/RSST50`, `RSSB34/RSST33/RSBT33`. Baselines:
`VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200` (B75D25),
`VT TQQQ/BTAL75+KMLM25 …` (B75K25), `VT TQQQ/BTAL50+KMLM50 …` (B50K50),
`VT TQQQ/BIL50+BTAL50 …` (the σ0.20 flag's machine), `TQQQ50/BTAL50 gate QQQ<SMA200`,
`SPY benchmark`.

## 2. Step 0 — the anchors reproduce, to eight decimals, with the statics in the traded set

The one way a static could have disturbed the incumbents is by joining the traded set: the
lane's calendar is the union of its traded symbols' dates, and that calendar is what the
sensitivity windows snap against. It does not move.

| where | arm | required | measured |
|---|---|---|---|
| `sweep_rs_2019` full | B75D25 | 0.93621129 / 0.18830107 / −0.20113095 | **exact** |
| `sweep_rs_2019` holdout | B75D25 test | 0.91868785 (= its committed `robust_score`) | **exact** |
| `sweep_rs_2019` full | `BIL50+BTAL50` | 0.97652213 | **exact** |
| `sweep_rs_2019` full | SPY | 0.46572974 (score₃ 0.42047588) | **exact** |
| `sweep_rs_2021` full | B75K25 / B75D25 / B50K50 | 0.85294307 / 0.85739876 / 0.88489974 | **exact** |
| `sweep_rs_2021` holdout | the same | 0.84701986 / 0.88253297 / 1.16742198 | **exact** |

B75D25's score₃ — `min(full 0.93621129, sens median 0.91995598, test 0.91868785)` —
is **0.91868785**, the number D2 shows is also the runner's own `robust_score` on a
categorical lane. The three lanes dry-run to `96` / `81` / `72`, the counts pre-registered
in `ede53d3`. The 2021 lane carries its warning verbatim — *"test window
2025-01-02..2026-08-24 is shorter than 2 years; its metrics are noise"* — and the 2022
lane carries none (test 2024-07-01 → 2026-08-24, 2.15 y). 1023 tests green.

## 3. Step 1 — the decision lane. **Every clause that matters fails, and the margin is not close.**

`results/sweep_rs_2019` (9 sensitivity windows; window floor = the minimum
`max_drawdown` over them, from `runs.json`):

| strategy | score | full | CAGR | max DD | test | sens med | sens min | window floor | wins /9 |
|---|---|---|---|---|---|---|---|---|---|
| `NTSX100` | 0.2482 | 0.4172 | 13.11 | −31.43 | 1.1036 | 0.2482 | 0.0693 | **−31.42** | **0** |
| `NTSX75/BIL25` | 0.2621 | 0.4374 | 10.58 | −24.19 | 1.1812 | 0.2621 | 0.0957 | −24.19 | 2 |
| `NTSX62.5/BIL37.5` | 0.2718 | 0.4538 | 9.25 | −20.39 | 1.2368 | 0.2718 | 0.1132 | **−20.39** | 2 |
| `NTSX50/BIL50` | 0.2846 | 0.4802 | 7.91 | −16.46 | 1.3319 | 0.2846 | 0.1368 | −16.46 | 2 |
| **B75D25** (score₃) | **0.9187** | 0.9362 | **18.83** | −20.11 | 0.9187 | 0.9200 | 0.6241 | **−20.11** | — |

Clause by clause: **(i) fails for all four**, by 0.6341 to 0.6705 — the bar wanted the
static *above* 0.9387. **(ii) passes for all four** (1.10–1.33 against 0.9187). **(iii)
passes for exactly one**, `NTSX50/BIL50` at +3.66 pp; `NTSX62.5/BIL37.5` misses by 0.27 pp,
`NTSX75/BIL25` by 4.08 pp, `NTSX100` by 11.31 pp. **(iv) fails for all four**: 0, 2, 2 and
2 of 9 against the required 5.

Two things in that table are worth more than the verdict they produce. The first is that a
static's `robust_score` is set by its **sensitivity median**, not by its holdout: the
median three-year Calmar of a 90/60 held through this period is 0.25–0.28 against a full
window 0.42–0.48, so the static is not merely worse than the machine, it is much less
stable window to window (sens min 0.07–0.14 against the machine's 0.62). The second is
that the two wins every deleveraged point records are the *same two windows* — the
2022-11-08 and 2023-05-08 starts, the only two that begin after NTSX's 2021-12-27 peak and
therefore contain no part of its 2022 fall.

Every static's floor is set by a window containing E5's decline: `NTSX100`'s and
`NTSX50/BIL50`'s by the 2019-11-08 start, `NTSX75/BIL25`'s and `NTSX62.5/BIL37.5`'s by the
2020-11-09 start. The machine's own floor is set by the first window, 2019-05-08, and is
E4's, not 2022's — the episode verdict's finding, seen from the other side of the table.

`NTSX100` does not outscore plain SPY on this lane: 0.2482 against SPY's score₃ 0.4205.
Nor does any other point (best 0.2846).

## 4. Step 2 — the matched floor. **The simplicity premium is 9.58 pp/yr, at NTSX 0.625.**

| point | window floor | gap to B75D25 | full CAGR |
|---|---|---|---|
| `NTSX100` | −31.42 | −11.31 pp | 13.11 |
| `NTSX75/BIL25` | −24.19 | −4.08 pp | 10.58 |
| **`NTSX62.5/BIL37.5`** | **−20.39** | **−0.27 pp** | **9.25** |
| `NTSX50/BIL50` | −16.46 | +3.66 pp | 7.91 |
| B75D25 | −20.11 | — | 18.83 |

The pre-registered 62.5 point lands 0.27 pp inside §9 step 2's 1 pp band, so the premium is
read at the grid point itself and no interpolation is needed:

> **18.83 − 9.25 = 9.58 pp/yr**, at NTSX fraction 0.625.

This is the flag §10.2 requires, and it does not depend on the bar. It is also, read the
other way, what the machine charges for its 2022: the two portfolios have the same
three-year worst hole, and one of them compounds at twice the rate.

## 5. Step 3 — the brackets. **Every clause keeps its verdict; one clause changes its sign by 0.012 pp.**

| bracket | B75D25 score₃ | B75D25 CAGR | B75D25 floor | best static score | its floor | clause verdicts |
|---|---|---|---|---|---|---|
| net15 | 0.9187 | 18.83 | −20.11 | 0.2846 | −16.46 | (i) ✗ (ii) ✓ (iii) 1 of 4 (iv) ✗ |
| `_tr` (gross) | 0.9406 | 19.13 | −20.11 | 0.2949 | −16.37 | identical |
| `_c20` (flat 20 bp) | 0.8596 | 18.22 | −20.43 | 0.2793 | −16.51 | (iii) **2** of 4 |

Cost reaches the machine and not the static, exactly as §2.3 said it would: on `_c20`
B75D25's score₃ falls 0.0591 and its full Calmar 0.0443, while no static's `robust_score`
falls by more than 0.0053. Turnover is why — `NTSX100` trades 0.083/yr against B75D25's
1.655/yr, fee drag 0.060 %/yr against 0.816 %/yr.

The one sign change: on `_c20` the machine's window floor deepens to **−20.4320** while
`NTSX62.5/BIL37.5`'s deepens only to **−20.4201**, so clause (iii) flips from fail to pass
for that point by **0.012 pp**. It changes nothing — the point still fails (i) by 0.59 and
(iv) with 2 of 9 — but it is a sign flip of a 10.1 clause on a bracket, which is precisely
what §11's prediction 5 named as its own falsifier. It is scored as such below.

## 6. Step 4 — the winners' lane. **Direction only, and the direction is emphatic.**

`results/sweep_rs_2021`, holdout noise by the runner's own warning:

| strategy | score | full | CAGR | max DD | test | sens med | floor |
|---|---|---|---|---|---|---|---|
| `NTSX100` | 0.3270 | 0.3270 | 10.27 | −31.42 | 1.0284 | 0.4640 | −31.43 |
| `RPAR100` | **0.0040** | 0.0504 | **1.55** | −30.66 | 1.7841 | 0.0040 | −30.66 |
| `NTSX50/RPAR50` | 0.1950 | 0.1950 | 5.92 | −30.34 | 1.3576 | 0.2541 | −30.34 |
| `NTSX75/BIL25` | 0.3543 | 0.3543 | 8.57 | −24.18 | 1.0906 | 0.5174 | −24.18 |
| `NTSX50/BIL50` | 0.4093 | 0.4093 | 6.73 | −16.44 | 1.2283 | 0.6171 | −16.44 |
| B75K25 | 0.8470 | 0.8529 | 16.26 | −19.06 | 0.8470 | 0.9844 | −19.06 |
| B75D25 | 0.8574 | 0.8574 | 16.35 | −19.07 | 0.8825 | 0.9814 | −19.07 |
| B50K50 | 0.8849 | 0.8849 | 18.49 | −20.90 | 1.1674 | 1.0496 | −20.88 |
| SPY | 0.6059 | 0.6059 | 14.82 | −24.45 | 0.9983 | 0.7118 | −24.45 |

The weakest winner's score₃ beats the best static by **0.4378**; SPY's beats it by
**0.1966**. Risk parity bought at the end of 2020 compounds at 1.55 %/yr and scores 0.0040.
**Plain SPY beats every static on this lane on score, on CAGR and on floor** — a levered
60/40 bought into the 2021 bond peak paid for its Treasury leg through 2022–23 and has not
recovered the difference.

## 7. Step 5 — the 2022 cohort. **Gold clears clause (i) and fails clause (iii) by 14 pp. Recorded, not promoted.**

`results/sweep_rs_2022`, three sensitivity windows — this lane ranks nothing (§10.3):

`GDE100` **0.9007** · 28.81 · −31.99 (test 2.0695, sens median 2.6225, floor −31.99);
`NTSX50/GDE50` **0.6815** · 19.79 · −29.04 (test 1.9145, floor −29.04); `NTSX100` 0.4092 ·
10.73 · −26.23; `NTSX34/NTSI33/NTSE33` 0.3947 · 10.54 · −26.69; `NTSE100` 0.3587;
`NTSI100` 0.3366; `RPAR100` 0.0592; `UPAR100` 0.0113 · 0.41 · −36.26. The winners'
score₃ are bound by their E6-containing test windows at **0.4699 / 0.4647 / 0.5256**
(their full Calmars are 1.1035 / 1.0940 / 0.9891); SPY's is 0.6642.

So the two gold-stacked points clear clause (i) against all three winners — and only
those two; every other static on the lane fails it. Their floors are **14.35 pp** and
**11.40 pp** deeper than the shallowest winner's (−17.64). This is `GDE100`'s 2022–26 run
in one ticker (+33.3 / +43.2 / +72.5 in 2023 / 2024 / 2025) read on a lane that starts at
gold's own launch date and holds no TQQQ bear. Under §10.3 it is **era-dependence,
reported and not promoted**; under 10.1(iii) buying Calmar at a floor 14 pp deeper is the
trade the bar refuses.

## 8. Step 6 — the 2023 panel. **On a window with no bear, two statics beat all three winners on both measures.**

`results/rs_points_2023.json`, full window only (2.7 y):

| strategy | Calmar | CAGR | max DD | peak → trough |
|---|---|---|---|---|
| `GDE100` | **2.2090** | **50.04** | −22.65 | 2026-01-28 → 2026-03-26 |
| `RSSB100` | **1.1800** | 19.27 | **−16.33** | 2024-12-06 → 2025-04-08 |
| SPY | 1.1767 | 21.83 | −18.55 | 2025-02-19 → 2025-04-08 |
| `NTSX100` | **1.1689** | 19.74 | **−16.89** | 2024-12-06 → 2025-04-08 |
| B75D25 | 1.0968 | 19.93 | −18.17 | 2024-07-10 → 2025-04-08 |
| B75K25 | 1.0765 | 18.92 | −17.57 | 2024-07-10 → 2025-04-08 |
| B50K50 | 1.0045 | 20.85 | −20.76 | 2024-07-10 → 2025-04-08 |
| `RSSB50/RSST50` | 0.9417 | 21.13 | −22.44 | 2025-02-18 → 2025-04-08 |
| `RPAR100` | 0.9128 | 10.41 | **−11.40** | 2024-10-01 → 2025-04-08 |
| `UPAR100` | 0.7948 | 12.91 | −16.25 | 2024-10-01 → 2025-04-08 |
| `RSSB34/RSST33/RSBT33` | 0.7891 | 15.71 | −19.91 | 2024-07-16 → 2025-04-08 |
| `RSST100` | 0.7352 | 22.64 | **−30.80** | 2024-07-10 → 2025-04-08 |
| `RSBT100` | 0.2670 | 5.07 | −18.98 | 2024-07-10 → 2025-05-14 |

**`RSSB100` and `NTSX100` beat all three winners on Calmar with a shallower floor than any
of them.** `GDE100` beats them on Calmar at a floor deeper than two of the three, so under
§10.3's own clause it is not named in the `Open:` line — it is the trade 10.1(iii)
refuses. `RSSB50/RSST50` does not clear the winners' best (0.9417 against 1.0968).

The panel's shape is the machine's insurance premium in a year the insurance was not
needed: the deepest thing in it is `RSST100`, the trend-stacked one, whose −30.80 % runs
2024-07-10 → 2025-04-08 — E6's own dates, exactly where trend loses.

> **Open:** whether `RSSB` or `NTSX` held statically beats the machine on a window that
> contains a TQQQ bear. The 2023-12-05 panel says they do on a window that does not, with
> shallower floors; it is 2.7 years with one episode of one kind in it and it decides
> nothing. **Not decidable before 2027-12** — RSSB's first bar plus four years, the
> earliest date the window can carry a two-year holdout and three three-year sensitivity
> windows (§2.2).

## 9. Step 7 — episodes. **The static wins every anti-beta episode and loses both bears; the split is E6's, not E5's.**

`results/episode_rs_2019.md`, `NTSX100` against B75D25 (episode return / in-window
drawdown, points, `+` = static ahead):

| | E2 | E3 COVID | E4 anti-beta | E5 2022 | E6 tariff | E7 |
|---|---|---|---|---|---|---|
| `NTSX100` | +13.3 / −4.1 | −0.2 / −28.3 | +23.5 / −8.9 | −14.3 / −31.4 | +21.3 / −16.9 | +8.4 / −9.2 |
| B75D25 | +23.3 / −8.9 | −1.4 / −18.9 | +9.0 / −20.1 | +5.3 / −14.7 | +1.3 / −18.4 | −1.0 / −16.4 |
| **static −** | **−10.0 / +4.8** | +1.2 / **−9.4** | **+14.5 / +11.2** | **−19.6 / −16.7** | **+20.0 / +1.5** | **+9.4 / +7.2** |

Recorded under §10.5, not scored: the static **wins** E4, E6 and E7 on both measures — the
three episodes in which the anti-beta factor itself fell — and **loses** E5 on both and E3
on drawdown. E2 is the one mixed cell: the static wins the drawdown by 4.8 pp and loses
the return by 10.0 pp. Deleveraging with BIL scales every cell toward zero; the only sign
it changes is E3's return, which crosses from −0.2 to +0.1 (spec erratum 2).

On the winners' lane every static is deeper than every winner in E5 and shallower than
every winner in E4, E6 and E7; `NTSX50/BIL50` (−16.4) is the only static within 2 pp of a
winner in E5. On the 2023 panel the bond-stacked statics (RSSB −16.3, NTSX −16.9, UPAR
−16.2, RPAR −11.4) are shallower than every winner in E6 and earn +12 to +23 pp where the
winners earn ~0; `RSST100` is deeper than every winner by more than 10 pp; `GDE100`'s only
deep hole is E7, gold's 2026 correction, where at −22.7 it is the deepest thing on the
panel.

`results/episode_rs_partitions.md`, pair (B75D25, `NTSX100`) over the 9 sensitivity
windows: **E6's trough gives the clean floor split** — the static is shallower in **2 of
the 3** windows containing 2025-04-08 and in **0 of the 6** without it. E5's trough
(2023-03-10) does not split: 1 of 6 with, 1 of 3 without, because that trough sits five
months after NTSX's own (2022-10-14) and two of its with-windows begin after the static's
fall. E4's split is 0 of 4 with and 2 of 5 without. Against `NTSX62.5/BIL37.5` the same
shape holds, wider: 3 of 3 shallower with E6's trough (mean Δdrawdown **+7.19 pp**), 1 of 6
without (**−1.61 pp**). Calmar never crosses — the static wins 0 of 9 windows outright and
the deleveraged point 2 of 9, both of them E6-containing.

This is the mirror of the episode verdict's finding for the sleeve: there, E4 partitioned
and 2022 did not; here, the episode that sets the static's floor (E5) is not the one that
partitions its windows (E6).

## 10. Step 8 — exposure control

Average held weight over all trade days, decision lane, full window: `NTSX100` NTSX 0.999;
`NTSX75/BIL25` NTSX 0.749 / BIL 0.249; `NTSX62.5/BIL37.5` NTSX 0.624 / BIL 0.374;
`NTSX50/BIL50` NTSX 0.499 / BIL 0.499. Every point holds what its label says and nothing
else; the missing thousandths are the contribution residue in `CASH`. For contrast the
machine holds TQQQ 0.380 / BTAL 0.465 / DBMF 0.155.

## 11. Step 9 — the decision (§10)

**10.1 fails, for every static, on the decision lane and on both brackets.** (i) fails by
0.63–0.67; (ii) passes for all four; (iii) passes for `NTSX50/BIL50` only (and, on
`_c20` alone, for `NTSX62.5/BIL37.5` by 0.012 pp); (iv) fails with 0–2 of the required 5.
No static enters the winners file, and the follow-on spec 10.1 names — whether a static
can be the machine's risk asset — is not triggered by this result.

**10.2 executes and is the spec's product.** The matched-floor point is the pre-registered
`NTSX62.5/BIL37.5` (floor 0.27 pp inside the band); the **simplicity premium is 9.58 pp/yr
at NTSX fraction 0.625**. Written into the winners file as a standing flag.

**10.3 binds on all three short lanes.** The 2021 lane is direction (holdout noise); the
2022 lane's gold points are era-dependence, reported not promoted; the 2023 panel gets the
dated `Open:` line of §8 above naming `RSSB` and `NTSX` — the two statics that beat all
three winners on Calmar *and* floor — and not `GDE100`, which beats them at a deeper floor.

**10.4(b) is the output**, as pre-registered, with the ledger entry and the flag written
per §7. **10.5**: the episode reads of §9 are recorded, not scored; a static is not a
sleeve candidate and CLAUDE.md §6's E4 rule does not bind it.

### Predictions, scored (§11, frozen at `ede53d3`)

| # | claim | outcome |
|---|---|---|
| 1 | 10.1 fails for every static on clause (i) by more than 0.40; falsified above 0.52 | **held** — by 0.63–0.67; the best static scores 0.2846, less than half the falsifier |
| 2 | clause (iii) passes for exactly one grid point, with the four stated inequalities and every floor set by a 2022 window | **held** — `NTSX50/BIL50` alone; −31.42 (< −30), −24.19 (< −23), −20.39 (0.27 pp deep, < 1 pp), −16.46 (3.66 pp shallow, > 3); floors set by the 2019-11-08 and 2020-11-09 windows, both containing E5's decline |
| 3 | the windows partition by 2021-12-27: `NTSX100` loses and is deeper in all six early windows, wins at most 2 of 9, deleveraged points at most 3 | **held** — 0 of 9 for `NTSX100`, its early in-window drawdowns −28.3 to −31.4 against the machine's ≤ −20.11; 2 of 9 for each deleveraged point, both wins in late windows |
| 4 | the matched point is the 62.5 grid point and the premium is 9–11 pp/yr at fraction 0.60–0.63 | **held** — 9.58 pp/yr at 0.625. The mechanism given for it is wrong: floors do equal full-window drawdowns (to 0.01 pp) but are set by the 2019-11-08 / 2020-11-09 windows, not by 2021-11-08, which is the deepest window for no NTSX point |
| 5 | the brackets keep every sign; the machine moves > 0.02 on `_c20`, no static > 0.01, nothing rises > 0.03 on `_tr` | **falsified** — on its own sign clause. The magnitudes are all right (machine −0.0591, statics ≤ 0.0053, `_tr` rises ≤ 0.0219), but clause (iii) for `NTSX62.5/BIL37.5` flips fail → pass on `_c20`, the machine's floor deepening past the static's by **0.012 pp**. No clause *verdict* and no decision changes |
| 6 | on the winners' lane every winner's score₃ beats every static by > 0.30 and SPY's by > 0.15 | **held** — 0.4378 and 0.1966; the best static's full Calmar is 0.4093, the figure predicted to the decimal |
| 7 | on the 2022 lane gold clears (i) and fails (iii) by > 5 pp; no other static clears (i) | **held** — `GDE100` 0.9007 and `NTSX50/GDE50` 0.6815 against winners' score₃ 0.4647–0.5256; floors 14.35 pp and 11.40 pp deeper than the shallowest winner's; the other six all fail (i) |
| 8 | E6's trough, not E5's, gives the clean floor split: shallower in none of the six without it and ≥ 2 of the 3 with it | **held** — 2 of 3 with, 0 of 6 without, for `NTSX100`; 3 of 3 and 1 of 6 for `NTSX62.5/BIL37.5`. E5 splits 1 of 6 and 1 of 3, as predicted |

Seven held, one falsified. The falsification is the smallest quantity in this document —
a floor crossing 0.012 pp wide on a stress bracket — and its cause is the one the spec
itself named: a 20 bp cost reaches a portfolio that trades 1.655/yr and barely touches one
that trades 0.133/yr, so at some cost level the two floors must cross. The spec predicted
the mechanism and then predicted it would not fire inside the bracket. It fires.

## Residuals worth remembering

1. **The statics' weakness is dispersion, not level.** On the decision lane the four
   points' full Calmars (0.42–0.48) are respectable and barely below SPY's 0.4657; their
   sensitivity medians (0.25–0.28) are half of that, and their sensitivity minima
   (0.07–0.14) are a tenth of the machine's 0.62. `robust_score` is a minimum, so this is
   what decides clause (i) — not the headline. A reader comparing full-window Calmars
   would conclude the gap is 0.5; the gap the bar sees is 0.67.

2. **On the two lanes with a bear in them, a static return-stacked ETF is worse than plain
   SPY on the sweep's own statistic.** 0.2846 against 0.4205 on the 2019 lane, 0.4093
   against 0.6059 on the 2021 lane, on floor as well as score on the second. The question
   §1 asks is "one ticker or the machine"; the answer on these windows is that the
   interesting comparison was never NTSX against the machine but NTSX against SPY, and a
   levered 60/40 loses that one too. The reason is entirely 2022 — the one bear in this
   data where Treasuries fell with stocks.

3. **The premium is a same-floor number, and same-floor is the only honest way to quote
   it.** 9.58 pp/yr compares two portfolios whose worst three-year hole is the same to
   0.27 pp. Quoted at the static's own floor the machine's edge looks like 5.7 pp
   (18.83 against 13.11) and the static looks 11.3 pp riskier; quoted at the machine's,
   it is 9.6 pp and the risk is matched. The second is the number a reader deciding
   whether to run the program actually needs.

4. **Cost is the one dimension on which the static wins, and it nearly mattered.** Turnover
   0.083–0.141/yr against 1.655; fee drag 0.060 %/yr against 0.816 %/yr. At the blend map
   that is worth 0.02 pp of CAGR to the static and 0.61 pp to the machine; at a flat 20 bp
   it is enough to move a floor across a clause boundary. No measured spread exists for
   any of the nine tickers — the `*` 6 bp catch-all is an assumption, and if a static ever
   does enter the winners file its cost line would be an assumption too.

5. **The 2023 panel is a regime sample, not a fund fact.** `RSSB100` and `NTSX100` beat
   every winner there on both measures because the window contains no bear at all — the
   deepest hole in it is E6, where the machine's anti-beta sleeve pays and a bond overlay
   does not. NTSX's −31.4 % is what a 90/60 does when stocks and Treasuries fall together;
   NTSI, alive since 2021-05, printed −34.3 % in the same episode. A future bear in which
   bonds rally reprices every number in this document in the statics' favour, and the
   `Open:` line is dated for exactly that reason.

6. **The E5/E6 asymmetry is the sleeve's own asymmetry, inverted.** The episode verdict
   found the machine's hinge at E4 rather than 2022; this lane finds the static's floor at
   2022 and its *partition* at E6. The two documents describe the same trade from opposite
   sides — the machine buys E5 with E4 and E6, the static buys E4, E6 and E7 with E3 and
   E5 — and a spec that ever asks whether a static can be the machine's risk asset
   inherits both tables.

7. **`robust_score` here has no neighbour term, on either side of the comparison.** score₃
   is a weaker minimum than the four-term one the σ/w lanes take, which is why D2 pins
   both that it *is* the runner's statistic on a categorical grid and that it is *not* on
   `sweep_cash_2019`. Nothing in this verdict is comparable to a lane that grids a numeric
   dimension; the anchors are stated on full-window Calmar throughout (handoff §5).

## Artefacts

Tests `tests/test_return_stacked.py` (D1–D5, 979 → **1023**), no engine file touched.
Specs `specs/sweep_rs_2019.json`, `sweep_rs_2019_c20.json`, `sweep_rs_2021.json`,
`sweep_rs_2022.json`, `rs_points_2019.json`, `rs_points_2021.json`,
`rs_points_2023.json`, frozen at `ede53d3`. Results `results/sweep_rs_2019/`,
`sweep_rs_2019_tr/`, `sweep_rs_2019_c20/`, `sweep_rs_2021/`, `sweep_rs_2022/`,
`results/rs_points_2023.json`, `results/episode_rs_2019.md`, `episode_rs_2021.md`,
`episode_rs_2023.md`, `episode_rs_partitions.md`, all at `36db8d5`. Data
`tests/data/2026-08-24-net15` throughout except the `_tr` bracket
(`tests/data/2026-08-24`). Errata: `docs/RETURN_STACKED_SPEC.md` §15, two entries.
