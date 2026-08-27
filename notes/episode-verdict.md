# Verdict: the hinge is 2020-09, not 2022 — and the winners' 2022 is mostly KMLM's

EPISODE_SPEC, implemented on branch `episode-attribution` from `6faeed0`. Tool
`episode_report.py`, tests A1–A7 (923 → 979), specs frozen at `6581105` before any
run, artefacts at `0d1b36e`. Everything on `tests/data/2026-08-24-net15` at the
blend cost map plus `BIL 0.5` and `cash_yield` 3 %. **No parameter, coordinate or
sleeve moves** (§10.1); this spec adopts nothing and can adopt nothing.

## 0. Step 0 — the pins hold on a fresh clone

The A3–A5 pins are on committed data and reproduce exactly, not to their stated
±0.2 pp: every cell of §11's two 2012 tables, every A4 cell on the 2021 lane, and
the §2.2 partition. `sweep_episode_2012 --dry-run` prints
`5 grid + 1 baselines x 27 windows = 162 runs`, the count §5.4 pre-registered.
979 tests green.

## 1. Step 1 — the 2012 attribution (`results/episode_2012.md`)

Episode return % of the TWR index / max drawdown % inside the window, σ0.20 / w0.8:

| sleeve | E1 | E2 | E3 | **E4** | E5 | E6 | E7 |
|---|---|---|---|---|---|---|---|
| `BTAL` | +0.2 / −21.8 | +0.4 / −23.5 | +1.1 / −16.6 | **+0.5 / −26.0** | +4.6 / −16.1 | +0.2 / −16.3 | −4.9 / −17.6 |
| `BIL25+BTAL75` | +0.5 / −22.5 | +0.1 / −24.0 | −0.1 / −18.0 | +6.9 / −21.2 | +2.7 / −17.2 | +3.0 / −16.3 | −2.6 / −17.2 |
| `BIL50+BTAL50` | +0.6 / −23.9 | −0.3 / −24.4 | −1.4 / −19.4 | +13.5 / −18.2 | +0.7 / −19.6 | +5.8 / −17.4 | −0.2 / −17.0 |
| `BIL75+BTAL25` | +0.7 / −25.4 | −0.7 / −24.9 | −2.7 / −20.8 | +20.4 / −16.4 | −1.4 / −22.3 | +8.5 / −19.2 | +2.1 / −16.9 |
| `BIL` | +0.6 / −27.1 | −1.1 / −25.9 | −4.0 / −22.2 | +27.5 / −15.3 | −3.7 / −25.1 | +11.3 / −21.4 | +4.3 / −16.8 |
| SPY | +15.0 / −13.2 | +12.3 / −19.5 | −5.5 / −33.7 | +28.2 / −9.5 | −3.7 / −24.6 | +20.6 / −18.8 | +11.8 / −8.9 |

Marginal against `BIL` (points, `+` = higher return / shallower):

| sleeve | E1 | E2 | E3 | **E4** | E5 | E6 | E7 |
|---|---|---|---|---|---|---|---|
| `BTAL` | −0.4 / +5.3 | +1.5 / +2.3 | +5.1 / +5.7 | **−27.0 / −10.7** | +8.2 / +9.1 | −11.1 / +5.1 | −9.3 / −0.8 |
| `BIL25+BTAL75` | −0.1 / +4.6 | +1.2 / +1.9 | +3.9 / +4.2 | −20.6 / −5.9 | +6.4 / +7.9 | −8.3 / +5.1 | −6.9 / −0.4 |
| `BIL50+BTAL50` | +0.0 / +3.2 | +0.8 / +1.4 | +2.6 / +2.8 | −14.0 / −2.9 | +4.4 / +5.6 | −5.5 / +4.0 | −4.6 / −0.2 |
| `BIL75+BTAL25` | +0.1 / +1.7 | +0.4 / +1.0 | +1.3 / +1.4 | −7.1 / −1.1 | +2.3 / +2.8 | −2.7 / +2.2 | −2.3 / −0.1 |

**The sums §9 step 1 asks for.** Over the four TQQQ bears (E1, E2, E3, E5) pure
BTAL earns **+14.4 pp of return and +22.4 pp of drawdown** against holding cash in
its place. Over the three anti-beta episodes (E4, E6, E7) it pays **−47.4 pp of
return and −6.4 pp of drawdown**. E4 alone (−27.0 / −10.7) costs more return than
the four bears together earn and gives back half their drawdown benefit. That is
the arithmetic behind the standing flag that pure BTAL is dominated at σ0.20 —
over 2012–2026 the payments exceed the earnings, and they are concentrated in one
episode.

The BIL fraction buys the sleeve out of E4 monotonically (−27.0 → −20.6 → −14.0 →
−7.1 → 0 of marginal return, −10.7 → −5.9 → −2.9 → −1.1 → 0 of drawdown) and sells
out of the bears at the same rate. Nothing here is a free lunch; it is a dial
between two episode families.

**The three-year lane** (`results/sweep_episode_2012/summary.json`, 27 windows, no
warnings, holdout snapped to 2023-01-03) says the same in aggregate:
`BIL75+BTAL25` `robust_score` **0.8217** (test 1.3008, `rank_worst` 4),
`BIL50+BTAL50` **0.8208** (1.2901, 3), `BIL25+BTAL75` **0.8005** (1.1455, 4), `BIL`
**0.7991** (1.2849, 5), pure `BTAL` last at **0.6999** (0.9750, 5). σ and `w_max`
are scalars here, so no point has a neighbourhood and `robust_score` is not
comparable to the five-year lane's — this sweep exists to feed `partition`, and its
ranking is quoted only as a consistency check.

## 2. Step 2 — the 2021 attribution (`results/episode_2021.md`, `episode_2021_T.md`)

The lane starts 2020-12-18, so E1–E3 are empty and E4 is read from its first bar.
Marginal against `BIL` (return pp / drawdown pp):

| sleeve | E4 | E5 | E6 | E7 |
|---|---|---|---|---|
| `BIL75+BTAL25` | −2.9 / −1.8 | +2.3 / +2.8 | −2.8 / +2.2 | −2.3 / −0.1 |
| `BIL50+BTAL50` | −5.8 / −3.7 | +4.4 / +5.5 | −5.5 / +4.0 | −4.6 / −0.2 |
| `BIL75+KMLM25` | +2.2 / +1.7 | +4.3 / +3.2 | −2.8 / −0.8 | +2.2 / +1.1 |
| `BIL50+KMLM50` | +4.4 / +2.6 | +8.3 / +6.0 | −5.5 / −2.5 | +4.5 / +2.2 |
| `BIL75+DBMF25` | +2.5 / +1.3 | +2.2 / +1.8 | −1.8 / −1.4 | +1.6 / +0.9 |
| `BIL50+DBMF50` | +4.9 / +2.6 | +4.4 / +3.5 | −3.7 / −3.7 | +3.3 / +1.2 |
| `BTAL` | **−11.6 / −7.4** | +8.3 / **+8.5** | −11.2 / **+5.0** | −9.3 / −0.8 |
| `KMLM` | +8.8 / +3.9 | **+16.5** / +5.8 | −10.7 / −5.9 | +9.1 / +4.3 |
| `DBMF` | +10.0 / +2.9 | +8.2 / +5.2 | −7.3 / −8.2 | +6.6 / +1.3 |
| `BTAL75+KMLM25` | −6.5 / −4.5 | +10.7 / **+11.0** | −10.9 / +3.6 | −4.8 / +0.6 |
| `BTAL75+DBMF25` | −6.3 / −4.5 | +8.6 / +10.2 | −10.0 / +3.0 | −5.3 / +0.5 |
| `BTAL50+KMLM50` | −1.5 / −1.6 | +13.0 / +9.4 | −10.8 / +0.4 | −0.2 / +2.0 |
| T(`B75K25`) | −2.2 / −1.4 | +7.7 / +7.5 | −6.8 / +1.4 | −1.3 / +1.0 |
| T(`B75D25`) | −1.9 / −1.4 | +5.6 / +6.1 | −5.9 / +0.8 | −1.8 / +0.8 |
| T(`B50K50`) | +1.4 / +0.5 | +10.9 / +7.7 | −8.1 / −1.0 | +2.1 / +2.1 |

**Which component earns E5, which pays E4.** The 2022 grind's *return* is KMLM's:
**+16.5 pp against BTAL's +8.3** and DBMF's +8.2. The 2022 grind's *drawdown* is
BTAL's: **+8.5 pp against KMLM's +5.8** and DBMF's +5.2. The two arms are not
substitutes in that episode — they buy different halves of it. E4 is BTAL's alone:
it pays **−11.6 pp of return and −7.4 pp of drawdown** where KMLM collects
+8.8 / +3.9 and DBMF +10.0 / +2.9. Every BTAL-containing sleeve is negative in E4
and every BTAL-free one positive; the sign flips exactly on the presence of BTAL.

**Complementarity is visible per episode.** `BTAL75+KMLM25`'s E5 marginal drawdown
is **+11.0 pp, above both its components** (+8.5 and +5.8) — the blend buys more
2022 floor than either arm alone. Same for `BTAL75+DBMF25` (+10.2 against +8.5 and
+5.2) and `BTAL50+KMLM50` (+9.4 against +8.5 and +5.8). On return,
`BTAL50+KMLM50`'s +13.0 exceeds BTAL's +8.3 but not KMLM's +16.5. So the sleeve's
edge over its parts is a *drawdown* edge, and it lives in E5.

**The T-transforms halve both sides, symmetrically.** T(`B75K25`) gives back 3.0 pp
of E5 marginal return (+10.7 → +7.7) and recovers 4.3 pp in E4 (−6.5 → −2.2);
T(`B75D25`) 3.0 and 4.4; T(`B50K50`) 2.1 and 2.9. The asymmetry is 1.3, 1.4 and
0.8 pp — under the 2 pp bar §11 set. Replacing half the BTAL with cash removes
roughly the BTAL share of both the earning and the paying, which is why the cash
verdict found it bought rank with floor and cleared no clause.

**E6 is the episode nothing insures.** Every arm loses return — BTAL −11.2, KMLM
−10.7, DBMF −7.3 — and only BTAL shallows the drawdown (**+5.0** against KMLM's
**−5.9** and DBMF's **−8.2**). The managed-futures arms' own 2025 drawdown deepens
the machine in the tariff episode. This is the one episode where the BTAL-heavy
sleeve is unambiguously the right sleeve, and it is not a bear.

## 3. Step 3 — the partitions (`results/episode_partitions.md`)

Per §9 step 3, the episode whose trough splits a pair's sensitivity windows most
cleanly (largest gap between the with- and without- win rates, Calmar and floor
summed):

| pair | lane | cleanest | gap (Calmar / floor) | runner-up |
|---|---|---|---|---|
| `BTAL` vs `BIL50+BTAL50` | 2012, 5 y | **E4** | +0.80 / +1.00 | E3 (+1.20 total) |
| `BTAL` vs `BIL` | 2012, 5 y | **E4** | +0.70 / +0.90 | E3 (+1.40) |
| `BTAL` vs `BIL50+BTAL50` | 2012, 3 y | **E4** | +0.56 / +0.94 | E7 (+1.17, n=1) |
| `BTAL` vs `BIL` | 2012, 3 y | **E4** | +0.39 / +0.83 | E3 (+1.00) |
| `B75K25` vs T | 2021, 3 y | **E4** | +0.40 / +1.00 | E6 (+0.33) |
| `B75D25` vs T | 2021, 3 y | **E4** | +0.40 / +1.00 | E6 (+0.33) |
| `B50K50` vs T | 2021, 3 y | E6 | +1.00 / +0.00 | E7 (+0.60); E4 −0.60 |
| `BTAL` vs `BIL50+BTAL50` | 2021, 3 y | E7 / **E4** tie | +0.40 / +0.80 each | E6 (+0.67) |

E4 is the cleanest partitioner in six of eight pairs and ties in a seventh. E5 is
the cleanest in none, and is *negative* on the 2021 lane for all four pairs.

**The five-year 2012 partition, again** (§2.2 reproduced): by E4's trough, 10
windows contain it → 10 Calmar wins and 10 shallower for the half-swap, 10 without
→ 2 and 0. By E5's, 7 → 7 and 6, 13 → 5 and 4. By E3's, 10 → 9 and 8, 10 → 3 and 2.

**The three-year lane isolates E3 from E4, and that is this spec's sharpest
result.** At five years every window holding COVID's trough but one also holds the
unwind's, so E3's apparent split is borrowed. Splitting the windows three ways:

| subset | 5 y (n, B Calmar, B shallower, mean Δfloor) | 3 y |
|---|---|---|
| E3's trough but **not** E4's | 2, 1, **0**, **−0.88 pp** | 2, 1, **0**, **−0.87 pp** |
| E4's trough but **not** E3's | 2, **2**, **2**, **+3.72 pp** | 2, **2**, **2**, **+3.72 pp** |
| both | 8, 8, 8, +3.22 pp | 4, 4, 4, +4.90 pp |

COVID *alone* goes to pure BTAL on the floor, on both lanes, in every window.
The anti-beta unwind *alone* goes to the half-swap on both measures, on both
lanes, in every window, by 3.72 pp of floor. The five-year table's E3 column was
E4's signal wearing E3's dates.

At three years E4 remains the cleanest split (6 of 6 with the trough on both
measures; 8 of 18 Calmar and 1 of 18 shallower without) while **E5 barely
partitions at all** — 4 of 6 against 10 of 18 on Calmar, 2 of 6 against 5 of 18 on
the floor. Whatever the disagreement between the 2012 and 2021 lanes is about, the
windows say it is not about how often 2022 happens.

## 4. Step 4 — the winners' deepest hole

From `results/cash_points_2021.json`, each winner's deepest drawdown, and its E4
depth beside it:

| winner | deepest | = full-window floor | E4 depth | E4's rank |
|---|---|---|---|---|
| B75K25 | **E4** 2021-01-26 → 2021-03-08, −19.06 % | −19.06 % | −19.06 % | 1st |
| B75D25 | **E4** 2021-01-26 → 2021-03-08, −19.07 % | −19.07 % | −19.07 % | 1st |
| B50K50 | E6 2024-07-10 → 2025-04-08, −20.90 % | −20.90 % | −16.12 % | 2nd |

Each winner's deepest episode *is* its full-window maximum drawdown to eight
decimals. Two of the three have E4 as that episode; the third has E4 second and E6
first. Beside it, BTAL's E4 marginal drawdown on this lane is **−7.4 pp** and the
BTAL-75 sleeves' is **−4.5 pp** — the winners' floor is a BTAL-made hole, dug in a
reflation rally, not in a TQQQ bear. Neither 2022 nor COVID appears in any
winner's top two.

## 5. Step 5 — the decision (§10)

**10.1 holds by construction.** Nothing moved.

**10.2(a) holds.** On the 2012 lane BTAL's marginal drawdown against `BIL` is
shallower in **four of four** bears (+5.3 / +2.3 / +5.7 / +9.1, against a bar of
three) and deeper in E4 by **10.7 pp**, against a bar of 5.

**10.2(b) holds.** KMLM's E5 marginal return **+16.5** exceeds BTAL's **+8.3**.

**10.2(c) holds on its second clause.** The first clause is not decidable: the
2021 lane has six three-year windows, of which exactly one contains E4's trough
and five contain E5's, so no count there can be "cleaner" in a meaningful sense
(§11 prediction 5 said so in advance). It holds anyway for two of the three
winners on the gap measure. The second clause — A6's pin, the winners' deepest
episode is E4 — holds for B75K25 and B75D25 outright and for B50K50 at second
place.

All three conditions hold, so **the ledger's `Open:` line is closed with the full
statement and the first flag is written** (§7.1, §10.2).

**10.3 — the candidate rule is adopted**, as it would have been regardless: every
future sleeve candidate names, in its pre-registration commit, the episode ids it
must win against the incumbent, on marginal drawdown or marginal return, stated;
and E4 as the episode it must not deepen by more than 1 pp. A candidate that
clears a lane's aggregate bar but deepens E4 is not promoted. Recorded in
`CLAUDE.md` §6 and as a standing flag.

**10.4 — the flags.** (i) *"The winners' deepest hole is BTAL-made (E4)"* — A6's
pin holds, written. (ii) *"KMLM earns 2022, BTAL earns 2022's drawdown"* — (b)
holds and BTAL's E5 marginal drawdown (+8.5) exceeds KMLM's (+5.8), written into
the same flag. (iii) The HANDOFF §7 leave-one-episode-out entry is retargeted from
2022 to E4 — (c) holds, done.

### Predictions, scored (§11, frozen at `6581105`)

| # | claim | outcome |
|---|---|---|
| 1 | §10.2(a) holds: BTAL shallower in all four bears (+5.3 / +2.3 / +5.7 / +9.1), E4 deeper by 10.7 pp | **held** — exactly, to the decimal |
| 2 | §10.2(b) holds: KMLM E5 +16.5 vs BTAL +8.3, BTAL's E5 drawdown the larger (+8.5 vs +5.8); flag (ii) fires | **held** — exactly; flag written |
| 3 | complementarity per episode: `B75K25`'s E5 drawdown +11.0 above both components, `B50K50`'s E5 return +13.0 above BTAL's | **held** — and for all three winners on drawdown (+11.0, +10.2, +9.4 against best-component +8.5) |
| 4 | the 3-year windows isolate E4 from E3: E3-only windows go to pure BTAL on drawdown, E4-only to the half-swap; E4's split at least as clean as at 5 y, E3's less clean | **held in part** — the isolation is exact and on both lanes (E3-only 0 of 2 shallower, −0.87 pp; E4-only 2 of 2, +3.72 pp) and E3's 3-year split is less clean (gaps 0.33/0.50 against 0.60/0.60 at 5 y); but E4's own 3-year gaps (0.56/0.94) are *narrower* than its 5-year ones (0.80/1.00), so "at least as clean" fails on the letter. The falsifier's own clause — E3 partitioning at least as cleanly as E4 — did not fire |
| 5 | the 2021 partition is reported, not decided: one E4 window, five E5; §10.2(c) rests on A6's pin; the one E4 window favours T on Calmar and the winner on the floor | **held in part** — the window counts are exact and (c) does rest on A6's pin. The one E4 window favours **T on both** measures for B75K25 and B75D25, and the **winner on both** for B50K50 — never the split the prediction described. Not falsified by its own clause (no window went the other way on both) but the floor half is wrong for two winners of three |
| 6 | the T-transforms halve both sides: 3.0 / 4.3, 3.0 / 4.4, 2.1 / 2.9 of E5 return against E4 recovery, asymmetry under 2 pp | **held** — every figure exact; asymmetries 1.3, 1.4, 0.8 pp |
| 7 | E6 is where every insurance arm loses return (−11.2 / −10.7 / −7.3) and only BTAL shallows the floor (+5.0 vs −5.9, −8.2) | **held** — exactly |
| 8 | E7 is open and decides nothing: every sleeve's E7 drawdown within 1 pp of the BIL sleeve's (−16.8 to −17.6); no §10 condition reads it | **held on the 2012 lane** (−16.8 to −17.6, spread 0.8 pp) **and not on the 2021 lane**, whose wider component panel spans −0.8 pp (BTAL) to +4.3 pp (KMLM) of marginal E7 floor. No §10 condition reads it either way |

Six held, two held in part, none falsified. Both partial results are about the
*shape* of a partition rather than its direction, and in both the direction is the
predicted one.

## Residuals worth remembering

1. **The story the program told itself was wrong, and the correction is one
   episode wide.** "The BTAL-heavy sleeve exists for 2022" survives as far as the
   *drawdown* half of E5 (+8.5 pp, the largest single-arm contribution) and no
   further: 2022's return is KMLM's, 2022 partitions nothing, and the sleeve's
   deepest hole is a reflation rally. The corrected sentence is that BTAL is
   insurance against fast, correlated equity falls and a short position in high
   beta leading — and 2012–2026 contained more of the second than of the first.

2. **The 2012 / 2021 disagreement is not about 2022's frequency.** The cash
   verdict's residual 2 framed it as "weight 2022 at one year in six and the
   BTAL-heavy sleeve is right; at one in fourteen the half-swap is". The windows
   say the split that matters is E4's, on both lanes and both window lengths, and
   E5's is the weakest of the seven on the winners' lane. A leave-one-episode-out
   lane is still the sharp falsifier — but with **E4** deleted, not 2022. That
   deletion is now specifiable: 2020-09-02 → 2021-09-03, one year, and it is the
   winners' own floor.

3. **The marginal-against-BIL decomposition prices an arm, not a covariance.** It
   measures what a component buys relative to cash at the same sleeve weight
   inside the VT sizing; it cannot separate the arm's own return from its
   covariance with TQQQ. The clean episode-level complementarity result (the blend
   beating both components on E5 floor) is the closest this decomposition gets to
   the covariance term, and it is a hint, not a measurement.

4. **Seven episodes, one machine, one coordinate.** The table is the incumbent's
   own drawdown list at σ0.20 / w0.8. At σ0.30 / w0.6 the pure-BTAL machine's
   deepest is 2021-12 → 2023-03 at −27.65 % — 2022 — and a table nominated there
   would put E5 first and might reproduce the old story. The table is frozen so
   the attribution is stable, not because it is canonical; a refresh is a spec
   change and both modes print the dates they used.

5. **E7 is open and E6 is one episode of one kind.** Three of the seven windows
   (E4, E6, E7) are anti-beta episodes and two of those three are the last two
   years. The "BTAL pays when high beta leads" finding rests on E4 for its size
   and on E6/E7 for its repetition, and E7's recovery has not happened.

6. **Nothing here tests the sleeve before 2011-09.** The synthetic verdict's
   caveat is inherited whole, and it bites harder now than it did: E4-shaped
   episodes — an anti-beta crash inside a growth drawdown — are exactly what
   2000–02 may or may not contain, no proxy exists, and the whole of this verdict
   turns on how often E4 recurs.

7. **The three-year 2012 lane bought less isolation than hoped.** It was
   provisioned to separate E3 from E4 and it does, but it separates them into the
   same 2 + 2 windows the five-year lane already had; what it added was four
   both-windows instead of eight, which sharpened the contrast rather than the
   count. A one-year or two-year sensitivity length would isolate more, at the
   price of Calmar estimates on windows too short to mean much.

## Artefacts

Tool `episode_report.py`; tests `tests/test_episode.py` (A1–A7, 923 → 979). Specs
`specs/sweep_episode_2012.json`, `specs/episode_points_2021.json`, frozen at
`6581105`. Results `results/sweep_episode_2012/`,
`results/episode_points_2021.json`, `results/episode_2012.md`,
`results/episode_2021.md`, `results/episode_2021_T.md`,
`results/episode_partitions.md`. Read against the committed
`results/cash_points_{2012,2021}.json`, `results/sweep_cash_2012/runs.json` and
`results/sweep_cash_2021/runs.json`. Data `tests/data/2026-08-24-net15`
throughout. Errata: `docs/EPISODE_SPEC.md` §15, three entries.
