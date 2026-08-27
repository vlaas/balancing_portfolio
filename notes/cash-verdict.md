# Verdict: the cash sleeve — BIL, BTAL, and the fraction between them

Spec: [CASH_SLEEVE_SPEC.md](../docs/CASH_SLEEVE_SPEC.md) · read protocol and bars: §9–§10,
**frozen at commit `25a40a7` before any lane was run** · branch `cash-sleeve` · data
`tests/data/2026-08-24-net15` (primary), gross-TR bracket `tests/data/2026-08-24`, flat-20
stress `specs/sweep_cash_*_c20.json`, §10.5 tie-breaker `tests/data/2026-08-24-net15-bil0`
· objective `calmar`, constraint `max_drawdown ≥ −0.50` · incumbent lanes' blend cost map
plus `BIL 0.5` bp per side (`TQQQ 1.5 / BTAL 6 / DBMF 2.5 / KMLM 6 / QQQ 1 / SPY 0.7 /
BIL 0.5 / * 6`), `cash_yield` 3% on uninvested residue only · windows: 2012-01-03 →
(holdout 2023-01-01, 6 m/5 y, 23), 2020-12-18 → (holdout 2025-01-01, 6 m/3 y, 9),
2019-05-08 → (holdout 2024-01-01, 6 m/3 y, 12) · predecessors:
[synthetic-history verdict](syn-verdict.md) §3, [safe-blend verdict](safe-blend-verdict.md),
[safe-swap verdict](safe-swap-verdict.md) §6.5, §6.7, §9.

**T is not adopted. The outcome is §10.4 — era-dependence — and it is the outcome the
spec pre-registered.** Replacing half a sleeve's BTAL with BIL clears every clause of the
bar against *pure BTAL* at the winners' σ, on all three lanes and both brackets; it clears
no clause against *the winners themselves*, on any lane, any bracket, or at BIL's own
withholding rate. The sleeve the winners hold is not too BTAL-heavy in general; it is too
BTAL-heavy on a fourteen-year lane and correctly BTAL-heavy on a lane where 2022 is one
year in six. No sleeve moves.

Two findings are worth more than the verdict. The first: **pure BTAL is dominated at
σ0.20 and it is not close.** `BIL50+BTAL50` replaces `BTAL` under all four clauses on the
2012 lane (Δrobust +0.126, floor 1.45 pp shallower), on the 2019 lane (+0.246, 6.61 pp)
and on the 2021 lane (+0.200, 3.00 pp) — three lanes, three eras, one direction. The
second: **the fraction surface is single-peaked at every coordinate and its peak walks
with σ**, from 25 % BTAL at σ0.20 / w0.8 to 100 % at both σ0.30 points. The sleeve
composition is not a constant to be fitted once; it is a function of how much risk the
sizing is already taking.

## 1. Frozen labels

| name | sleeve | rendered |
|---|---|---|
| `B75K25` | `{"BTAL": 0.75, "KMLM": 0.25}` | `VT TQQQ/BTAL75+KMLM25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200` |
| `B75D25` | `{"BTAL": 0.75, "DBMF": 0.25}` | `VT TQQQ/BTAL75+DBMF25 …` |
| `B50K50` | `{"BTAL": 0.5, "KMLM": 0.5}` | `VT TQQQ/BTAL50+KMLM50 …` |
| `T(B75K25)` | `{"BIL": 0.375, "BTAL": 0.375, "KMLM": 0.25}` | `VT TQQQ/BIL37.5+BTAL37.5+KMLM25 …` |
| `T(B75D25)` | `{"BIL": 0.375, "BTAL": 0.375, "DBMF": 0.25}` | `VT TQQQ/BIL37.5+BTAL37.5+DBMF25 …` |
| `T(B50K50)` | `{"BIL": 0.25, "BTAL": 0.25, "KMLM": 0.5}` | `VT TQQQ/BIL25+BTAL25+KMLM50 …` |
| `T(BTAL)` | `{"BIL": 0.5, "BTAL": 0.5}` | `VT TQQQ/BIL50+BTAL50 …` |
| twins | `BIL75+KMLM25`, `BIL75+DBMF25`, `BIL50+KMLM50` | the surface's far endpoints, never candidates |

## 2. Anchors confirmed before anything else was read (§9 step 0)

| where | arm | required | measured |
|---|---|---|---|
| `sweep_cash_2012` | `BTAL` σ0.30 / w0.6 | 0.86123626 · 0.23817105 · −0.27654555 | **0.86123626 · 0.23817105 · −0.27654555** |
| `sweep_cash_2012` | `BTAL` σ0.20 / w0.8 | 0.69991357 | **0.69991357** |
| `sweep_cash_2012` | `BIL` σ0.20 / w0.8 | 0.79914190 | **0.79914190** |
| `sweep_cash_2021` | the three winners, full | 0.8529 / 0.8574 / 0.8849 | **0.8529 / 0.8574 / 0.8849** |
| `sweep_cash_2021` | the three winners, robust | 0.8470 / 0.8574 / 0.8849 | 0.8470 / **0.8389** / **0.8429** |
| `sweep_cash_2019` | `BTAL75+DBMF25` | 0.9362 full / 0.9187 robust | **0.9362 / 0.9187** |

Every full-window number reproduces exactly. Two robust scores do not, and **cannot**:
§4.2 asks the winners to reproduce `sweep_comp_2021`'s values, but that lane held
`sigma_target` fixed and so had `neighbour_min: null`, while this lane grids σ and gives
every point a neighbour. For `B75D25` and `B50K50` that neighbour binds — their σ0.25
twins print 0.8389 and 0.8429 — and `robust_score = min(full, neighbour_min, sensitivity
median, holdout test)` takes it. The anchor is unmeetable as written (erratum 5). Nothing
downstream is affected: all twelve sleeves are scored the same way at the same coordinate,
so every comparison the bar is made of is like-for-like. It does mean **the bar is applied
to a differently-composed statistic than the one that promoted the winners**, which is
recorded as residual 3.

The 2021 lane's runner warning is quoted as §4.2 requires: *"test window
2025-01-02..2026-08-24 is shorter than 2 years; its metrics are noise."* Every σ point on
all three lanes carries `edge: true`, both σ grids being two or three values wide.

## 3. Step 1 — the fraction surface. **Single-peaked everywhere, and the peak walks with σ.**

2012 lane, `runs`/`summary` on net15, gate SMA-200, λ0.80. Full Calmar · CAGR % ·
max DD % · window floor % (the minimum sensitivity-window drawdown), best full Calmar in
bold:

| σ / w_max | `BTAL` | `BIL25+BTAL75` | `BIL50+BTAL50` | `BIL75+BTAL25` | `BIL` | peak |
|---|---|---|---|---|---|---|
| **0.20 / 0.8** | 0.6999 · 18.21 · −26.02 | 0.8005 · 19.17 · −23.95 | 0.8208 · 20.06 · −24.44 | **0.8217** · 20.89 · −25.43 | 0.7991 · 21.66 · −27.10 | **25 % BTAL** |
| 0.20 / 0.6 | 0.6590 · 16.95 · −25.72 | **0.8527** · 17.84 · −20.93 | 0.8311 · 18.67 · −22.46 | 0.7947 · 19.43 · −24.45 | 0.7613 · 20.12 · −26.43 | **75 %** |
| 0.25 / 0.6 | 0.8272 · 20.75 · −25.09 | **0.9126** · 21.49 · −23.55 | 0.8594 · 22.17 · −25.80 | 0.8110 · 22.79 · −28.11 | 0.7669 · 23.36 · −30.46 | **75 %** |
| 0.25 / 0.8 | **0.8016** · 22.13 · −27.60 | 0.7938 · 22.95 · −28.90 | 0.7847 · 23.71 · −30.22 | 0.7744 · 24.42 · −31.54 | 0.7630 · 25.08 · −32.87 | **100 %** |
| 0.30 / 0.6 | **0.8612** · 23.82 · −27.65 | 0.8350 · 24.43 · −29.26 | 0.8020 · 24.98 · −31.15 | 0.7698 · 25.48 · −33.10 | 0.7386 · 25.93 · −35.11 | **100 %** |
| 0.30 / 0.8 | **0.8082** · 25.77 · −31.89 | 0.8063 · 26.44 · −32.80 | 0.8028 · 27.07 · −33.72 | 0.7976 · 27.64 · −34.66 | 0.7757 · 28.17 · −36.32 | **100 %** |

Every row is single-peaked. The peak's BTAL fraction is 25 % / 75 % at σ0.20 (w0.8 / w0.6),
75 % at σ0.25 / w0.6, and 100 % at the three highest-risk coordinates, monotone down to
BIL — exactly the shape §11 prediction 1 named, coordinate by coordinate, with pure BTAL
last of five at σ0.20 / w0.8. The pre-registered "the best BTAL fraction rises with σ"
holds along both `w_max` columns.

The mechanism the spec declined to claim is visible in the drawdown columns rather than
the Calmar ones. CAGR rises monotonically with BIL at every coordinate — always, by 3.2 to
3.5 pp end to end — because BTAL costs 4.7 pp/yr to hold. Drawdown is where the rows
differ: at σ0.20 the sleeve is large enough that swapping BTAL for cash *reduces* the
drawdown over the first quarter of the swap (−26.02 → −23.95 at w0.8, −25.72 → −20.93 at
w0.6), because BTAL's own −52.7 % drawdown is a drag the anti-beta does not pay for
outside crashes; at σ0.30 the sleeve is small and TQQQ's drawdown dominates, so the
anti-beta is the only thing in the sleeve that matters and every point of BIL costs
drawdown monotonically. The turn is not at a fixed fraction — it is where the sleeve stops
being large enough for its own drift to matter.

`rank_worst` and the window floor tell the same story: at σ0.20 / w0.8 the floor is
shallowest at 25 % BIL (−24.13) and deepest at pure BIL (−27.69), with pure BTAL second
worst (−26.03); at σ0.30 / w0.6 the floor is monotone from −27.33 (BTAL) to −34.82 (BIL).

Baselines, 2012 lane: gated `TQQQ50/BTAL50` 0.6063 · 22.88 · −37.73; gated `TQQQ50/BIL50`
0.5932 · 24.59 · −41.45; SPY 0.4340 · 14.64 · −33.74. Every grid point beats all three on
Calmar.

## 4. Step 2 — T on the 2012 lane. **10.3(a) fires, on all four clauses and both brackets.**

`BIL50+BTAL50` against `BTAL`, σ0.20 / w0.8:

| bracket | (i) Δ`robust_score` | (ii) `rank_worst` | (iii) holdout test | (iv) window floor |
|---|---|---|---|---|
| net15 | **+0.1257** ✓ | 30 → 27 ✓ | 0.9750 → 1.2901 ✓ | −26.03 → −24.59, **+1.45 pp** ✓ |
| gross | **+0.1253** ✓ | 30 → 27 ✓ | 1.0032 → 1.3324 ✓ | −26.03 → −24.46, **+1.57 pp** ✓ |
| flat-20 | **+0.1084** ✓ | 30 → 27 ✓ | 0.9219 → 1.2129 ✓ | −26.32 → −25.23, **+1.08 pp** ✓ |

Four of four, three times. This is the safe-blend verdict's own shape — *"more return and
a shallower drawdown, not a trade between them"* — with +1.85 pp of CAGR thrown in. It is
the clause (iv) result that matters: the half-swap does not buy Calmar by accepting a
deeper hole, it makes the hole shallower.

At the *regime* coordinate σ0.30 / w0.6 the same swap fails three of four clauses
(Δrobust −0.0269, `rank_worst` 20 → 27, floor 3.51 pp **deeper**). §10.3(a) is written
against σ0.20 / w0.8 and only that coordinate; the σ0.30 result is the surface, not a
counter-example, and it is why §10.6's flag is scoped to σ0.20.

## 5. Step 3 — T on the winners' lane. **10.3(b) fails, for all three, on clauses (i) and (iv).**

σ0.20 / w0.8, net15. Full Calmar · CAGR % · max DD % · floor %, then the four clauses:

| sleeve | full · CAGR · maxDD · floor | robust | test | `rw` | 2022 | 2025 |
|---|---|---|---|---|---|---|
| `B75K25` | 0.8529 · 16.26 · −19.06 · −19.06 | 0.8470 | 0.8470 | 18 | **−6.2** | +16.5 |
| **T(B75K25)** | 0.9018 · 17.93 · −19.89 · −19.84 | 0.8441 | 1.1876 | 12 | −11.1 | +20.9 |
| `BIL75+KMLM25` | 0.8778 · 19.41 · −22.11 · −22.07 | 0.8194 | 1.2894 | 18 | −16.1 | +25.3 |
| `B75D25` | 0.8574 · 16.35 · −19.07 · −19.07 | 0.8389 | 0.8825 | 15 | **−7.3** | +18.7 |
| **T(B75D25)** | 0.8771 · 18.01 · −20.53 · −20.51 | 0.8311 | 1.2109 | 11 | −12.2 | +23.1 |
| `BIL75+DBMF25` | 0.8564 · 19.48 · −22.74 · −22.70 | 0.7874 | 1.2668 | 20 | −17.2 | +27.6 |
| `B50K50` | 0.8849 · 18.49 · −20.90 · −20.88 | 0.8429 | 1.1674 | 24 | **−4.7** | +17.9 |
| **T(B50K50)** | 0.8757 · 19.57 · −22.35 · −22.30 | 0.8371 | 1.2563 | 23 | −8.1 | +20.8 |
| `BIL50+KMLM50` | 0.8631 · 20.53 · −23.79 · −23.76 | 0.8284 | 1.2737 | 22 | −11.7 | +23.7 |
| `BTAL` | 0.6347 · 13.93 · −21.96 · −21.96 | 0.5610 | 0.5610 | 24 | −7.7 | +15.0 |
| `BIL` | 0.7440 · 18.22 · −24.49 · −24.49 | 0.7026 | 1.2927 | 23 | −20.6 | +26.9 |
| `BIL50+BTAL50` | 0.8569 · 16.24 · **−18.95** · −18.95 | 0.7606 | 0.9741 | 15 | −14.2 | +21.0 |
| SPY | 0.6059 · 14.82 · −24.45 · −24.45 | — | — | — | −18.2 | +17.4 |

Clause by clause, net15:

| pair | (i) Δrobust | (ii) `rw` | (iii) test | (iv) floor |
|---|---|---|---|---|
| `B75K25` → T | −0.0029 ✗ | 18 → 12 ✓ | 0.8470 → 1.1876 ✓ | −0.77 pp ✗ |
| `B75D25` → T | −0.0079 ✗ | 15 → 11 ✓ | 0.8825 → 1.2109 ✓ | −1.44 pp ✗ |
| `B50K50` → T | −0.0058 ✗ | 24 → 23 ✓ | 1.1674 → 1.2563 ✓ | −1.43 pp ✗ |

**T buys rank and holdout with drawdown, on every one of the three.** The floor is deeper
in each case, and the calendar tells you where it comes from: 2022, the year the sleeve
exists for. T gives back **4.9 / 4.9 / 3.4 pp** of 2022 and collects **4.4 / 4.4 / 2.9 pp**
of 2025 — almost exactly a swap, priced at 1.67 / 1.66 / 1.08 pp of CAGR. On this lane
2022 is one year in six; on the 2012 lane it is one in fourteen, and that single difference
in weighting is the whole disagreement between §4.1 and §4.2.

The per-episode panel (`results/cash_points_2021.json`) says the same thing from the other
side. Every T deepens the 2025 episode against its winner — −19.89 vs −17.69, −20.53 vs
−18.33, −22.35 vs −20.90 — and 2022's episode is where the BTAL-heavy sleeves are
shallower or drop off the top-five list entirely.

The BIL twins behave exactly as §3 said they would: +3.15 / +3.13 / +2.04 pp of CAGR,
+3.05 / +3.67 / +2.89 pp of drawdown, 2022 lost by 9.9 / 9.9 / 7.0 pp, beating one winner
on Calmar (`B75K25`, +0.0249) and losing to another (`B50K50`, −0.0218). **Reported, not
adopted** — a `safe` grid is categorical, so a twin that outscores T somewhere is a point
on a surface with no neighbourhood, and promoting it would be the grid search
SWEEP_SPEC §4.6 forbids.

## 6. Step 4 — T on the COVID lane. **10.3(c) fails too — and it is the prediction that broke.**

2019 lane, σ0.20 / w0.8, net15:

| sleeve | robust | full · CAGR · maxDD | test | `rw` | floor |
|---|---|---|---|---|---|
| `BTAL` | 0.6280 | 0.6280 · 16.34 · −26.02 | 0.7894 | 12 | −26.02 |
| `BIL` | 0.6430 | 0.8520 · 21.15 · −24.82 | 1.0227 | 11 | −24.67 |
| **`BIL50+BTAL50`** | **0.8734** | **0.9765** · 18.95 · **−19.40** | 1.0306 | 6 | **−19.40** |
| `BTAL75+DBMF25` | **0.9187** | 0.9362 · 18.83 · −20.11 | 0.9187 | 9 | −20.11 |
| **T(B75D25)** | 0.8342 | **0.9852** · 20.71 · −21.02 | 0.9653 | 8 | −21.02 |
| `BIL75+DBMF25` | 0.7643 | 0.9592 · 22.35 · −23.30 | 0.9984 | 11 | −23.30 |

`BIL50+BTAL50` against `BTAL` is the strongest complement anywhere in this spec: Δrobust
**+0.2455**, `rank_worst` 12 → 6, holdout 0.7894 → 1.0306, floor **6.61 pp shallower**.
All four clauses, by margins that are not arguable.

T against `BTAL75+DBMF25` is a different animal. On full Calmar T wins — 0.9852 against
0.9362, the highest full Calmar of any sleeve on any lane in this spec — but 10.2's "not
worse" is stated on `robust_score`, and there T loses by **0.0845**, four times the −0.02
tolerance, with the floor 0.90 pp deeper besides. §11 prediction 5 expected clause (iv) to
be the only close call and is **falsified**: its full-Calmar half is exact to the digit
(+0.049 Calmar, 0.91 pp more drawdown) and its conclusion is wrong, because the σ
neighbourhood this lane has and the pilot did not cuts T's robust score to its σ0.25
twin's.

## 7. Step 5 — brackets, and the §10.5 withholding read. **The read binds; the tie-breaker was built; it changes nothing.**

Every step-2 comparison keeps all four clause verdicts on both brackets (§4). Every step-3
comparison keeps its clause verdicts too — T fails (i) and (iv) on gross and on flat-20
exactly as on net15:

| pair | net15 Δrobust · Δfloor | gross | flat-20 |
|---|---|---|---|
| `B75K25` → T | −0.0029 · −0.77 | −0.0068 · −0.60 | **+0.0101** · −1.05 |
| `B75D25` → T | −0.0079 · −1.44 | −0.0055 · −1.23 | −0.0083 · −1.67 |
| `B50K50` → T | −0.0058 · −1.43 | −0.0049 · −1.39 | −0.0053 · −1.45 |

One number changes sign — `B75K25`'s Δrobust on flat-20, from −0.0029 to +0.0101 — and it
changes no clause, being still an order of magnitude short of the +0.02 bar. §11 prediction
6 is scored **held in part** on that basis.

**§10.5 fired, against prediction 7.** All three T margins on the winners' lane land inside
the ±0.02 band — the band inside which the net15 convention's over-withholding of BIL could
plausibly flip the sign — so the pre-registered tie-breaker was built rather than argued
about. `make_net_tr.py` gained `--rate-override BIL=0`; `tests/data/2026-08-24-net15-bil0`
differs from the flat root in exactly one file, and BIL's series there is its gross series
to the last bit (1.39 %/yr on both sides of the README's table). Rereading the lane:

| pair | net15 Δrobust | **bil0** Δrobust | bil0 floor |
|---|---|---|---|
| `B75K25` → T | −0.0029 | **+0.0040** | −19.06 → −19.76 |
| `B75D25` → T | −0.0079 | **−0.0010** | −19.07 → −20.38 |
| `B50K50` → T | −0.0058 | **−0.0017** | −20.88 → −22.24 |

The bias is real and it is small: worth +0.004 to +0.007 of `robust_score`, against a bar
of +0.02. **T does not clear clause (i) at BIL's plausible true rate either**, and clauses
(ii)–(iv) are exempt from the read by §10.5's own terms — the floor is still deeper for
all three. §10.3(e)'s veto is not reached, because (b) has already failed.

The measured biases behind the read, pinned by B2: BIL's gross-minus-net15 CAGR is
**0.23 pp/yr** on the 2012 lane and **0.47 pp/yr** on the 2021 lane, so a sleeve holding
BIL at `f_BIL = 0.375` pays 0.176 pp/yr of sleeve return for a convention that almost
certainly does not apply to Treasury interest.

## 8. Step 6 — exposure control (SAFE_SWAP §6.5, mandatory). **No sleeve won by holding more TQQQ.**

From `runs.csv`'s full-window rows, average and minimum TQQQ weight across every compared
sleeve at σ0.20 / w0.8:

| lane | avg TQQQ weight | spread | min TQQQ weight |
|---|---|---|---|
| 2012, five sleeves | 0.4611 – 0.4616 | **0.00045** | 0.0522 – 0.0588 |
| 2021, nine sleeves | 0.3775 – 0.3789 | **0.00140** | 0.0402 – 0.0451 |

Both spreads are an order of magnitude inside the 0.005 that would have meant a bug. The
VT sizing does not see the sleeve, so this was expected; it is printed because a sleeve
comparison that skipped it would not be readable as a sleeve comparison.

## 9. Step 7 — the decision (§10.3, §10.4)

**(a) fires.** On §4.1 at σ0.20 / w0.8, `BIL50+BTAL50` replaces `BTAL` under 10.1 —
Δrobust +0.1257, `rank_worst` 30 → 27, holdout 0.9750 → 1.2901, floor 1.45 pp shallower —
and keeps all four on both brackets.

**(b) fails.** T replaces no winner. Clause (i) fails for all three (−0.0029, −0.0079,
−0.0058 against a +0.02 bar) and clause (iv) fails for all three (floor 0.77, 1.44 and
1.43 pp deeper). The failures survive the gross bracket, the flat-20 bracket and the
§10.5 tie-breaker root.

**(c) fails.** On §4.3, T is worse than `BTAL75+DBMF25` under 10.2 by 0.0845 of
`robust_score` and 0.90 pp of floor.

**(d)** is moot; **(e)** is not reached.

Two of the three conditions in 10.3 are unmet, so **T is not adopted, and §10.4 is the
verdict**: at the winners' σ the 2012 and 2019 lanes say the sleeve carries too much BTAL,
the winners' lane says 2022 is what the BTAL was for, and the bar prices the disagreement
through the window floor rather than resolving it. The winners file gains the sentence
§10.4 pre-registered and **no sleeve moves**.

Per §10.6 the fraction surface of step 1 is recorded above per σ, and `BTAL` at σ0.20 is
flagged wherever it is quoted as a baseline: **dominated by `BIL50+BTAL50` on every real
lane at this σ** — 2012 (+0.126 robust, 1.45 pp shallower floor), 2019 (+0.246, 6.61 pp)
and 2021 (+0.200, 3.00 pp), all four clauses on each. `docs/WINNING_STRATEGIES.md` is
created to carry both, the file having been named by four specs and never written.

### Predictions, scored (§11, frozen at `25a40a7`)

| # | claim | outcome |
|---|---|---|
| 1 | the surface is single-peaked at every coordinate and the peak's BTAL fraction is 25–50 % at σ0.20/w0.8, 75 % at σ0.20/w0.6 and σ0.25/w0.6, 100 % at σ0.25/w0.8 and both σ0.30 points | **held** — every row single-peaked, every peak where named (25 % at σ0.20/w0.8, pure BTAL last of five), monotone down to BIL at all three high-σ coordinates |
| 2 | 10.3(a) holds: +0.12 Calmar, 1.6 pp less drawdown, +1.85 pp CAGR, holdout 1.29 vs 0.98, all four clauses on both brackets | **held** — +0.1209 full Calmar, 1.58 pp, +1.85 pp, 1.2901 vs 0.9750; four of four on net15, gross and flat-20 |
| 3 | 10.3(b) fails on clause (iv) for two of three; T is a return trade worth +1.67/+1.66/+1.08 pp of CAGR giving back 4.9/4.9/3.4 pp of 2022 | **held** — the floor is deeper for **all three**, and every CAGR and calendar figure is exact |
| 4 | the BIL twins add +3.15/+3.13/+2.04 pp CAGR and +3.0/+3.7/+2.9 pp drawdown, lose 2022 by 9.9/9.9/7.0 pp, beat `B75K25` by +0.025 and lose to `B50K50` by −0.022 | **held** — +3.15/+3.13/+2.04, +3.05/+3.67/+2.89, 9.9/9.9/7.0, +0.0249 and −0.0218; none adopted |
| 5 | on the 2019 lane T is a complement: 10.3(c)'s "not worse" holds and clause (iv) is the only close call | **falsified** — the full-Calmar half is exact (+0.0490, 0.91 pp) but T is worse under 10.2 by 0.0845 of `robust_score`, its σ0.25 neighbour binding |
| 6 | the brackets keep every sign; no comparison in steps 2–4 flips | **held in part** — every clause verdict holds on both brackets; `B75K25`'s Δrobust flips −0.0029 → +0.0101 on flat-20, inside the band, changing nothing |
| 7 | the withholding read does not bind; the `bil0` root is not built | **falsified** — all three T margins land inside ±0.02, the root was built and the lane reread; the bias is worth +0.004 to +0.007 and changes no clause |
| 8 | exposure is identical: avg TQQQ weight 0.461–0.462 (2012) and 0.377–0.379 (2021) | **held** — 0.4611–0.4616 and 0.3775–0.3789, spreads 0.00045 and 0.00140 |

Six held (one in part), two falsified, and both falsifications have the same cause: the σ
grid this spec added gives every point a neighbourhood the pilot's single-coordinate runs
did not have, and `robust_score` takes the minimum over it.

## Residuals worth remembering

1. **The half-swap against pure BTAL is the finding this spec did not set out to make, and
   it is bigger than the one it did.** `BIL50+BTAL50` replaces `BTAL` under all four
   clauses on three lanes spanning three eras, with the floor shallower every time — the
   safe-blend verdict's "strictly dominates" shape, at margins between +0.126 and +0.246.
   Anywhere `BTAL` is used as a σ0.20 baseline it is the wrong baseline. It is *not* a
   claim about the winners, which hold BTAL alongside a managed-futures arm and are a
   different object.

2. **The disagreement between the lanes is a disagreement about how often 2022 happens,
   and no lane answers it.** T gives back 3.4–4.9 pp of 2022 and collects 2.9–4.4 pp of
   2025. Weight 2022 at one year in six and the BTAL-heavy sleeve is right; weight it at
   one in fourteen and the half-swap is. §12 named this and it is still true: the bar
   prices the disagreement through the floor rather than resolving it. A
   leave-one-episode-out lane with 2022 deleted — already on the handoff's list for the
   BTAL-heavy regime variant — is the sharp falsifier.

3. **`robust_score` is not comparable across lanes with different grid shapes.** Two of the
   §4.2 anchors could not reproduce because `sweep_comp_2021` fixed σ and this lane grids
   it, so `neighbour_min` exists here and binds for two winners. Every comparison *inside*
   a lane is unaffected, but a future spec that carries a `robust_score` from one lane to
   another as a bar — as §4.2's anchor tried to — will be comparing two different
   statistics. The durable fix is to state anchors on the full-window objective, which
   reproduced exactly everywhere, and to read `robust_score` only within its own lane.

4. **Every σ point in this spec is an edge point.** Both σ grids are two or three values
   wide, so `edge: true` on all of them and `neighbour_min` is always the one neighbour
   that exists. SWEEP_SPEC's footnote applies — extend the grid before believing a
   neighbourhood-bound score. The 2012 lane's three-value σ grid is the least affected and
   is where the weight of this verdict sits.

5. **BIL's withholding is now a one-flag build, and it is small.** `--rate-override BIL=0`
   and `tests/data/2026-08-24-net15-bil0` exist and are tested; the bias is worth 0.23 pp/yr
   of BIL return on the 2012 lane and 0.47 on the 2021 lane, which is +0.004 to +0.007 of
   `robust_score` on a 37.5 %-BIL sleeve. That is large enough to matter inside a ±0.02
   band and far too small to rescue a comparison that fails by more. Any future spec whose
   verdict turns on a BIL-containing margin under 0.02 should build the root rather than
   reason about it.

6. **The 2019 lane's 2020 calendar year has no committed artefact.** §9 step 4 asks for it,
   but §4.5 provisions panels for the 2012 and 2021 lanes only, and `runs.csv` carries
   `best_year`/`worst_year` rather than a full calendar (erratum 6). The COVID *episode* is
   covered — `results/cash_points_2012.json` prints −16.59 / −18.01 / −19.43 / −20.84 /
   −22.24 across the five 2012-lane sleeves against SPY's −33.74 — and the decision does
   not turn on it, 10.3(c) having failed on `robust_score` and the floor. A third panel
   would have been an addition to a pre-registered set after the runs, so it was not made.

7. **Nothing here tests the sleeve before 2011-09.** The synthetic verdict's standing
   caveat is untouched: BTAL's −3.4 %/yr drift over 2012–2026 includes a −20 % 2025, and a
   bear where low beta is bid (2000–02) would reprice every row of §3 in BTAL's favour —
   in which case the peak of the fraction surface moves right at every σ. This spec ran on
   real bars only, by §4's own terms, and inherits that limit whole.

## Artefacts

Specs `specs/sweep_cash_{2012,2021,2019}.json`, `specs/sweep_cash_{2012,2021}_c20.json`,
`specs/cash_points_{2012,2021}.json`, all frozen at `25a40a7`. Results
`results/sweep_cash_2012{,_tr,_c20}`, `results/sweep_cash_2021{,_tr,_c20,_bil0}`,
`results/sweep_cash_2019`, `results/cash_points_{2012,2021}.json`. Data
`tests/data/2026-08-24-net15` (primary), `tests/data/2026-08-24` (gross bracket),
`tests/data/2026-08-24-net15-bil0` (§10.5 tie-breaker). Tests
`tests/test_cash_sleeve.py` (B1–B5), the per-root battery in
`tests/test_total_return.py`, the override guards in `tests/test_net_tr.py`.
