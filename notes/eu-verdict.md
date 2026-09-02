# Verdict: the machine runs from IBKR IE — QQQ3 tracks TQQQ within 0.14 %/yr, a two-ETF blend fills BTAL's slot, and the managed-futures arm is blocked

Spec `docs/EU_SUBSTITUTE_SPEC.md`, frozen at `246eafb` before any run · §4.4
(the asynchronous-close reading) pre-registered at `bfdbca2` before any
Phase-3 run · errata 13–14 (P3's basis, P4/P5 recorded) at `3c549a7` before
this verdict · branch `eu-substitute` · decision root
`tests/data/2026-09-02-net15-usd` (haircut lanes `-hc`) · costs: the §6.4
**placeholder** EU spreads (QQQ3 15, CNDX 4, CSPX 2, IB01 2, MVEA 12, XSPS 12,
DBMF_EU 15, `*` 15 bp per side) with the tastytrade map for US symbols,
`cash_yield` 0.03, and the mandatory flat-20 twin of every lane · suite 1067
→ 1242 passed · no engine file is touched and `SCHEMA_VERSION` stays 4.

**Phase 1.** Of the seven registered substitutes, **QQQ3 passes** as TQQQ's
twin (quarterly β 0.998, R² 0.985, drift −0.14 %/yr → h = 0.14), **IB01
passes by erratum** as BIL's (drift +0.09 against gross BIL; +0.48 against
the net-15 root it was pre-registered on, because an Irish accumulating fund
does not pay the withholding the net-15 convention charges Treasury
interest), **QQL3 fails** on drift (−3.78 %/yr, the physical-replication
financing cost the memo warned about), **DBMF_EU fails** outright (weekly
corr 0.655 with US DBMF, a 9.7 %/yr residual and a +4.9 %/yr drift — a
different strategy, not the close gap), and **CSPX and CNDX fail the R² bar**
at 0.979 and 0.983 against 0.99 while passing β and drift (+0.00 / −0.14):
the residual of the ~4.5 h London-to-New-York close gap, which the monthly
bars of §4.2 measured wholesale (R² ≈ 0.95 on every LSE line, §4.4) and which
the quarterly reading leaves at ~2 % of variance. Both stay the benchmark and
the signal of every lane as pre-written (erratum 14).

**Phase 2.** The synthesis arm solves at **w_S\* = 0.4417 → 0.45**, the
pre-written primary, and is a **PROXY** for BTAL by the frozen grammar: corr
0.525 against a 0.50 bar, +0.87 pp mean return over the seven worst CNDX
months, and a peak-to-trough of −4.2 % over 2020-09-01 → 2021-03-31 against
BTAL's −31.1 % (ratio 0.14 against a 1.5 ceiling). The last number is the
finding: SYNB clears the proxy bar and is nothing like BTAL in the episode
that is the US machine's hinge.

**Phase 3.** On the eu-2020 direct lane the **EU flag variant** (VT QQQ3 /
IB01 50 + SYNB 50, CNDX signal) makes **23.68 % / −23.19 %** against CSPX's
18.26 % / −24.25 % (flat-20: 23.31 / −23.39 against 18.25 / −24.23), and its
ancestor's haircut lanes still beat CSPX and SPY on both bars on 2019 and
2021 — **IMPLEMENTABLE** under errata 13–14, with the translation of its
substitutable components costing 0.06–0.08 pp/yr. `EU SYNB100` (22.82 %
/ −23.28 %) clears the same bars as a **NEW BLEND** with no heritage. The
faithful expression of B75D25 is **BLOCKED(DBMF_EU)**; B50K50 and B75K25 are
**BLOCKED(KMLM)** by construction. The US flag variant on the *same* window
makes 17.63 % / −19.12 %: the EU expression's 6 pp of extra CAGR is SYNB's
E4 (−4 % against −31 %), bought with a 4 pp deeper 2022 floor, and the
program's one-era caveat applies with an even shorter direct record.

## 1. Phase 0 — what the data needed (§2–§3)

The batch's failure class was the one the guards were built for, plus two the
spec did not itemize: the two-pass procedure had dropped `price/` copies of
the five index series and the four macro series (the fresh post-close index
exports were promoted, the twins deleted), and both passes of every US pair
had run mid-session (re-exported after the close, all 57 anchors exact).
`DBMF` had already been restored in `677133f`. Currency, operator-recorded:
MVEA, LQQ and DBMF_EU are EUR lines, XSPS is GBX — so `fx_lines.json`
carries a pence scale and `GBPUSD.csv` joined the FX singles. TradingView
stamps an FX bar by its 17:00 New York open, so `make_usd.py` joins the bar
labelled the day before (erratum 12); a same-date join would look a day
ahead. The chain: `2026-09-02` → `-net15` (LQQ gross) → `-net15-usd` →
`-hc`, every derivative byte-reproducible from its parent.

## 2. Phase 1 — overlap validation (§4, `results/overlap_eu/overlap.md`)

Decision horizon quarterly (§4.4; P6 weekly), drift as α, thresholds as
pre-registered; the monthly intercept reading is the letter of §4.2.

| pair | n | β | R² | drift %/yr | resid %/yr | §4.4 verdict | §4.2 letter | consequence |
|---|---|---|---|---|---|---|---|---|
| P1 QQQ3 / TQQQ | 54 | 0.9976 | 0.9846 | −0.14 | 7.38 | **PASS** | FAIL | h(TQQQ) = 0.1421 |
| P2 QQL3 / TQQQ | 16 | 1.0718 | 0.9786 | −3.78 | 9.05 | **FAIL** | FAIL | not usable |
| P3 IB01 / BIL (gross basis) | 29 | 1.0053 | 0.9551 | +0.09 | 0.23 | **PASS-BY-ERRATUM** | PASS | h(BIL) = 0 |
| P3 on the net-15 basis | 29 | 1.1769 | 0.9508 | +0.48 | 0.24 | FAIL (outperforms) | — | erratum 13 |
| P4 CSPX / SPY | 63 | 0.9792 | 0.9794 | +0.00 | 2.11 | **FAIL** (R²) | FAIL | benchmark as pre-written |
| P5 CNDX / QQQ | 63 | 1.0047 | 0.9828 | −0.14 | 2.44 | **FAIL** (R²) | FAIL | signal as pre-written |
| P6 DBMF_EU / DBMF (weekly) | 75 | 0.9465 | 0.4290 | +4.90 | 9.66 | **FAIL** (corr 0.655) | FAIL | MF slot unfilled |
| P7 LQQ_usd / QQQ | 80 | 2.0235 | 0.9858 | +8.29 | 4.80 | characterization | — | L = 2 confirmed, no adoption |
| P8 DBMF_EU / KMLM | 5 | −0.0787 | 0.0122 | +20.85 | 7.11 | documentation | — | not KMLM's job |

Three readings. **The close gap is a constant ~3 % per period** (QQQ3's
residual 11.4 %/yr monthly = 3.3 % per month, 7.4 %/yr quarterly = 3.7 % per
quarter, 2.8 %/yr annual), so it is ~6 % of a monthly move's variance and the
§4.2 monthly bars could not be met by any LSE line; β and R² recover with the
horizon (QQQ3 0.957 / 0.955 → 0.998 / 0.985 → 1.020 / 0.998) and the drift,
which the gap enters only at the window's ends, does not move. **P4/P5 fail
by the gap's residual**, not by tracking: their annual R² is 0.993 / 0.997,
their drift is the 15 % fund-level withholding to within 0.14 %/yr, and the
benchmark choice moves no bar (CSPX 18.26 % against SPY 18.39 % CAGR on the
direct lane). **P6's failure is real**: a 9.7 %/yr residual against the same
manager's US fund on 75 weeks, +5 %/yr ahead of it, and quarterly n = 5 — the
UCITS ETF is not a DBMF twin on this record, and its slot stays unfilled.
Monthly n = 17 gives corr 0.83, the `Open:` line at 2028-03 stands.

## 3. Phase 2 — the synthesis arm (§5, `results/synb/synb.md`)

Estimation month-ends 2020-05-29 → 2023-12-29 (44 month-ends, 43 returns):
β(MVEA, CSPX) 0.774, β(XSPS, CSPX) −0.978, w_S\* = 0.4417 → **0.45**.
Falsifiers on 2020-05-29 → 2026-08-28 (75 returns):

| w_S | F1 corr(SYNB, BTAL) ≥ 0.50 | F2 mean over 7 worst CNDX months > 0 | F3 E4 peak-to-trough, ≤ 1.5 × BTAL's −31.12 % | verdict |
|---|---|---|---|---|
| 0.40 | 0.332 ❌ | +0.33 pp ✅ | −3.47 % (0.11) ✅ | ARM-ONLY |
| **0.45** | 0.525 ✅ | +0.87 pp ✅ | −4.23 % (0.14) ✅ | **PROXY** |
| 0.50 | 0.656 ✅ | +1.42 pp ✅ | −5.50 % (0.18) ✅ | PROXY |

F4, the daily-reset short leg held monthly against −1 × SPY: −0.65 and −0.35
pp in 2020–21, then +4.3, +7.8, +9.2, +5.5, +4.6 pp in 2022–26 — the
collateral yield of an inverse swap ETF at 4–5 % rates, not decay. F1 is
cleared by 0.025 at the primary; the arm's proxy status is one bar wide.

## 4. Phase 3 — the lanes (§6, `results/eu_points_*.json`)

### 4.1 eu-2020 direct lane, 2020-04-23 → 2026-09-02 (`-net15-usd`)

| arm | base CAGR / max DD | flat-20 CAGR / max DD | vs CSPX (base) | 2022 | 2023 |
|---|---|---|---|---|---|
| EU SYNB100 w45 (primary) | 22.82 % / −23.28 % | 22.61 % / −23.41 % | +4.56 pp / +0.97 pp | −17.8 % | +57.6 % |
| EU SYNB100 w40 (sens.) | 23.66 % / −24.49 % | 23.40 % / −24.63 % | +5.40 / **−0.24** | −18.7 % | +58.9 % |
| EU SYNB100 w50 (sens.) | 22.11 % / −22.08 % | 21.87 % / −22.01 % | +3.85 / +2.17 | −16.5 % | +56.4 % |
| **EU flag variant** IB01 50 + SYNB 50 | **23.68 % / −23.19 %** | **23.31 % / −23.39 %** | +5.42 / +1.06 | −18.3 % | +60.4 % |
| REF: primary with the QQQ signal (look-ahead) | 20.28 % / −25.27 % | 19.98 % / −25.37 % | +2.02 / **−1.02** | −20.3 % | +45.2 % |
| US REF flag variant (BIL 50 + BTAL 50, TQQQ, QQQ signal) | 17.63 % / −19.12 % | — | −0.63 / +5.13 | −14.5 % | +40.4 % |
| US REF B75D25 | 16.77 % / −20.12 % | — | −1.49 / +4.13 | −7.6 % | +34.2 % |
| US REF BTAL100 (SYNB100's analogue) | 13.78 % / −25.99 % | — | −4.48 / −1.74 | −8.0 % | +32.9 % |
| CSPX benchmark | 18.26 % / −24.25 % | 18.25 % / −24.23 % | — | −18.6 % | +26.5 % |
| SPY benchmark | 18.39 % / −24.49 % | 18.39 % / −24.45 % | — | −18.3 % | +25.7 % |

Every EU arm's deepest drawdown is the 2022 grind (2021-11-22 → 2022-10),
not E4; the flat-20 twin moves each arm by 0.2–0.4 pp of CAGR and 0.1–0.2 pp
of floor, and no verdict. The w40 point fails the drawdown bar by 0.24 pp;
the look-ahead reference fails it by 1.02 pp — signal-source purity is worth
+2.5 pp of CAGR and 2 pp of floor *in the contemporaneous signal's favour*.
Average QQQ3 exposure 0.375, turnover 1.7, fee drag 2.5–3.1 %/yr at the
placeholder spreads (against 0.6–0.9 %/yr for the US winners on their lanes).

### 4.2 Haircut lanes — component isolation on the promotion lanes (`-hc`)

TQQQ carries 0.1421 %/yr, BIL 0 (h = 0 is the byte-copy path), DBMF absent
(P6 FAIL), BTAL and KMLM uncarried: their columns are **translation-
incomplete**. The un-haircut parent run of the same bundles isolates the
haircut itself.

| lane | winner | parent CAGR / DD | haircut CAGR / DD | Δ pp | flat-20 | CSPX | SPY |
|---|---|---|---|---|---|---|---|
| 2019 | B75D25 (DBMF, BTAL untranslated) | 18.76 / −20.11 | 18.70 / −20.12 | −0.06 / −0.01 | 18.08 / −20.45 | 15.70 / −33.47 | 15.66 / −33.67 |
| 2019 | flag variant (BTAL untranslated) | 18.83 / −19.40 | 18.77 / −19.42 | −0.06 / −0.02 | 18.11 / −19.55 | 15.70 / −33.47 | 15.66 / −33.67 |
| 2019 | REF B75D25 with the CNDX signal | 22.17 / −22.08 | 22.10 / −22.11 | −0.06 / −0.03 | 21.45 / −22.38 | 15.70 / −33.47 | 15.66 / −33.67 |
| 2021 | B50K50 (KMLM, BTAL untranslated) | 18.75 / −20.88 | 18.62 / −20.91 | −0.13 / −0.02 | 17.98 / −21.25 | 14.58 / −23.82 | 14.64 / −23.68 |
| 2021 | B75D25 (DBMF, BTAL untranslated) | 16.40 / −18.94 | 16.31 / −18.76 | −0.08 / +0.17 | 15.69 / −19.01 | 14.58 / −23.82 | 14.64 / −23.68 |
| 2021 | B75K25 (KMLM, BTAL untranslated) | 16.45 / −18.97 | 16.38 / −18.79 | −0.07 / +0.17 | 15.71 / −19.03 | 14.58 / −23.82 | 14.64 / −23.68 |
| 2021 | flag variant (BTAL untranslated) | 16.31 / −18.12 | 16.23 / −18.07 | −0.08 / +0.05 | 15.52 / −18.44 | 14.58 / −23.82 | 14.64 / −23.68 |

The measured translation cost of the substitutable components is 0.06–0.13
pp of CAGR — 0.14 %/yr at 0.38 average exposure — and no floor moves by more
than 0.17 pp. The composed estimate (§6.3) EU-winner ≈ US-winner − Σh gives
18.76 − 0.14 = 18.62 for B75D25 and 18.83 − 0.14 = 18.69 for the flag variant
on 2019, within 0.08 pp of the measured haircut lanes; it is an estimate of
the *translatable* part only. The CNDX-signal reference on the 2019 lane —
B75D25 with real TQQQ and a signal read 4.5 h earlier — makes 22.10 % against
18.70 %: signal-source sensitivity is +3.4 pp on seven real years, again in
CNDX's favour, which is a gate-timing statement about these windows, not a
promotion.

### 4.3 eu-2025 lane, 2025-03-17 → 2026-09-02 — DOCUMENT-ONLY

EU-B75D25 (SYNB75 + DBMF_EU25) 29.83 % / −16.09 %, `IB01 50 + DBMF_EU 50`
37.48 % / −17.02 %, `DBMF_EU 100` 44.38 % / −17.50 %, SYNB100 26.71 % /
−16.43 %, CSPX 24.20 % / −13.08 %. Every arm beats CSPX on CAGR and none on
drawdown; eighteen months of one rebound decide nothing (the RSSB lesson), and
DBMF_EU failed its own validation.

## 5. The decision (§6.5)

- **EU flag variant** (VT QQQ3 / IB01 50 + SYNB(w45) 50, CNDX signal and
  volatility, SMA-200 gate, λ 0.80, σ 0.20, w_max 0.8): **IMPLEMENTABLE**
  under errata 13–14. It beats CSPX on CAGR and max drawdown at base and
  flat-20 costs on the direct lane; its ancestor's haircut lanes beat CSPX and
  SPY on both bars on 2019 and 2021 at base and flat-20; its components are
  P1 PASS, P3 PASS-BY-ERRATUM and SYNB PROXY. Under the letter of §4.2 it is
  BLOCKED three times over (P3 by an outperforming cash fund, P5 by a signal
  whose R² is 0.983 against 0.99, and P1 by the monthly close gap) — the
  operator's amendments are what make the sentence writable, and they are
  recorded in the spec's errata, not in this note alone.
- **EU SYNB100** (w45): a **NEW BLEND** that clears the direct-lane bars at
  base and flat-20 (22.82 % / −23.28 %); it inherits nothing — its US analogue
  (VT TQQQ / BTAL100) makes 13.78 % / −25.99 % on the same window and was
  dominated on every cash-sleeve lane. The w40 sensitivity fails the drawdown
  bar; w50 passes both.
- **EU-B75D25**: **BLOCKED(DBMF_EU)** — the only faithful expression of a
  promoted winner rests on the one component that failed its phase, and its
  direct record is eighteen months.
- **B50K50, B75K25**: **BLOCKED(KMLM)** — no MLM-index product exists in
  Europe; the haircut lanes carry their TQQQ translation (−0.07 to −0.13 pp)
  with the KMLM and BTAL columns untranslated.
- **QQL3**: FAIL, not usable. **CSPX / CNDX**: FAIL on R² by the close gap's
  residual, used as benchmark and signal as pre-written (erratum 14).
- Nothing here re-ranks the tastytrade winners; the EU verdict is the
  parallel section in `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`.

Caveats stated, not footnoted: (i) the EU direct record is 6.4 years —
E4, the 2022 grind and the 2025 tariff episode, no COVID and no pre-2011 bear
— the program's one-era caveat with an even shorter record; (ii) the EU
spreads are placeholders until the operator measures five-session medians at
the London close, and the flat-20 twin brackets them by 0.2–0.4 pp;
(iii) seven of the lane's 77 rebalance days fall on a holiday of one exchange
and trade forward-filled closes on the other (2020-08-31, 2021-05-31,
2026-08-31 on the four LSE lines and the CNDX signal; every 12-31 on MVEA) —
the engine's union calendar, unchanged, documented; (iv) IBKR commissions and
EUR→USD conversion are excluded, as Wise's 45 bp is on the US side.

## 6. Predictions, scored (§2.4, §4.2, frozen at `246eafb`)

1. *"The async close is real and large … month-end horizons, where the missing
   overlap is ~3 % of the window."* ❌ **Falsified** in the second half: the gap
   is ~6 % of a monthly move's variance, not 3 % of its time; the monthly bars
   measured it wholesale and §4.4 was needed.
2. *"QQQ3 looks like the substitute the memo hoped for; QQL3 does not."*
   ✅ **Confirmed**: drift −0.14 against −3.78 %/yr.
3. *"IB01 is a near-perfect BIL twin (drift +0.11 %/yr)."* ✅ **Confirmed** on
   the gross basis (+0.09) and ❌ **falsified by construction** on the net-15
   basis the pair was pre-registered on (+0.48) — erratum 13.
4. *"The Irish Acc convention matches the program's net15 basis."*
   ✅ **Confirmed**: CSPX / CNDX drift +0.00 / −0.14 %/yr against net-15 SPY /
   QQQ.
5. *"The regression that matters (UCITS vs US DBMF) … at best PROVISIONAL
   PASS."* ❌ **Falsified**: FAIL on every horizon; the UCITS ETF is not the
   US fund's twin on this record.
6. *"P2 … expected FAIL on α (session −5.25)."* ✅ **Confirmed** (−3.78 on the
   quarterly drift).
7. *"The eu-2020 lane contains E4 …"* ✅ **Confirmed** — and E4 is not the EU
   machine's hinge: every EU arm's floor is the 2022 grind.

## Residuals worth remembering

1. **The bars measured the clock, not the fund.** A pre-registered R² at a
   monthly horizon is a statement about the variance share of the close gap;
   on an LSE line it can never exceed ≈ 0.95. Any future EU validation reads
   β and R² at a horizon where the gap is negligible and the drag from the
   endpoint drift.
2. **SYNB is a proxy by the grammar and a different instrument in fact.** It
   clears F1 by 0.025 and F3 by a factor of ten in the other direction; the EU
   expression's 6 pp of extra CAGR over the US flag variant on the same window
   is that E4 behaviour, and its 4 pp deeper 2022 floor is the price. It is a
   better sleeve on 2020–26 and an untested one in a BTAL-style regime.
3. **A net-15 root is the wrong basis for a Treasury-interest pair.** IB01
   fails a two-sided bar by winning; the `-bil0` convention CASH_SLEEVE_SPEC
   §10.5 argued for is the one this cycle needed.
4. **The signal series moves the machine by ±3 pp on these windows** — CNDX
   ahead of QQQ on both lanes, with and without look-ahead. The gate is ten
   month-end numbers (MONTHLY_GATE_SPEC), and which ten matters more than the
   verdicts of this cycle assumed.
5. **DBMF_EU is its own fund.** +5 %/yr ahead of US DBMF with a 9.7 %/yr
   residual on 75 weeks; whatever it is, it is not a substitute, and the
   `Open:` line at 2028-03 is about a different question than the memo posed.
6. **TradingView's FX bars are stamped by their open.** A same-date join of an
   FX_IDC daily bar looks a day ahead; the alignment test (monthly R² of the
   converted lines against their references) says so as loudly as the Brexit
   bar does.

## Artefacts

- Roots: `tests/data/2026-09-02/`, `-net15/`, `-net15-usd/`, `-net15-usd-hc/`.
- Generators: `make_usd.py`, `make_haircut.py`; reports: `overlap_report.py`,
  `synb_report.py`.
- Phase 1: `results/overlap_eu/{overlap.json,overlap.md,haircuts.json}`;
  Phase 2: `results/synb/{synb.json,synb.md}`.
- Lanes: `specs/eu_points_{2020,2020_c20,2025,2025_c20,2019_hc,2019_hc_c20,
  2021_hc,2021_hc_c20,2020_usref}.json` and `results/` of the same names, plus
  `results/eu_points_{2019,2021}_hc_parent.json` (the un-haircut references).
- Tests: `tests/test_usd.py` (T2), `tests/test_overlap.py` (T3),
  `tests/test_haircut.py` (T4), `tests/test_synb.py` (T5),
  `tests/test_eu_bundles.py` (T6), the freeze pins in
  `tests/test_total_return.py` / `tests/test_net_tr.py`. Suite 1242.
- Spec: `docs/EU_SUBSTITUTE_SPEC.md` §4.4 and errata 1–15; data conventions
  in `data/README.md` (line registry, FX bar stamps, export rules).
