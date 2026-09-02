# Specification: EU-substitute instruments — the IBKR-IE expression of the winning machine

Repo: `vlaas/balancing_portfolio` · baseline commit: `c066eef` ("Fresh data";
suite **25 failed / 1070 passed** on a fresh clone — deliberately red, see §2.2)
· status: **proposed** · inputs: `docs/RESEARCH_RECAP.md`, the EU instrument
memo of 2026-08-31 (candidate tables, fidelity classes, tax findings) ·
predecessors: `TOTAL_RETURN_SPEC.md` / `NET_TR_SPEC.md` (dataset conventions),
`ROTATION_SPEC.md` §3 (data-convention amendments accompany every new export
class), `SYNTHETIC_HISTORY_SPEC.md` (derived-root generators, splice/haircut
precedent, no-contamination invariant), `COST_MODEL_SPEC.md` (cost map,
c20 stress).

## 1. Goal

The whole program to date answers "what should an Estonian investor run at
tastytrade." This cycle answers the parallel question the EU memo opened: **can
the same machine be run from an EU broker (IBKR IE) out of PRIIPs-compliant
instruments, and at what measured cost?** The machine and its coordinate
(λ 0.80, σ_target 0.20, w_max 0.8, SMA-200 gate, monthly everything) are
**frozen inputs** — nothing here re-fits them. This cycle promotes or demotes
*instruments*, in three phases with pre-registered bars:

1. **Phase 1 — do the arrived EU series validate at their claimed fidelity
   class?** MECHANICAL and PARAMETRIC candidates are validated by month-end
   tracking regressions against their US originals over the real overlap;
   each PASS pins a per-symbol drag constant `h`.
2. **Phase 2 — can BTAL's job be done by a two-ETF synthesis?** The memo's
   binding constraint: no European product runs BTAL's mandate. The candidate
   is a fixed MVEA + XSPS blend with pre-registered weights and falsifiers.
3. **Phase 3 — do the winners survive translation?** Direct lanes on real EU
   bars where they exist, component-isolation haircut lanes on the promotion
   lanes where they do not, and a decision bar restated against the benchmark
   the investor could actually hold (CSPX, not SPY).

A strategy verdict here is one of **IMPLEMENTABLE**, **IMPLEMENTABLE-PENDING**
(a component's validation is provisional for want of overlap), or
**BLOCKED(component)**. No promoted winner is redefined; the incumbent
tastytrade recommendation stands regardless of this cycle's outcome.

## 2. State of the repo at baseline — measured

All numbers in this section were measured this session on a fresh clone at
`c066eef`; the characterization tables come from throwaway sandbox runs and are
**provisional** — the committed record is produced by the Phase-1 tool (§4).

### 2.1 The 2026-09-02 batch — what arrived

Nine new symbols landed in `data/` (paired, both toggles), all ending
2026-09-02:

| symbol | instrument (per the EU memo) | first bar | rows | pair R |
|---|---|---|---|---|
| QQQ3 | WisdomTree NASDAQ 100 3x Daily Lev (IE00BLRPRL42), LSE USD | 2012-12-17 | 3 463 | 1 flat |
| QQL3 | Leverage Shares 3x Long Nasdaq 100 (XS2472197065), LSE USD | 2022-06-09 | 1 062 | 1 flat |
| LQQ | Amundi Nasdaq-100 2x Lev UCITS (FR0010342592), Euronext EUR | 2006-06-28 | 5 134 | R_min 0.986842 |
| CNDX | iShares Nasdaq 100 UCITS Acc (IE00B53SZB19), LSE USD | 2010-09-15 | 3 972 | 1 flat |
| CSPX | iShares Core S&P 500 UCITS Acc (IE00B5BMR087), LSE USD | 2010-09-15 | 3 980 | 1 flat |
| IB01 | iShares $ Treasury Bd 0-1yr UCITS Acc (IE00BGSF1X88), LSE USD | 2019-02-22 | 1 899 | 1 flat |
| MVEA | iShares Edge MSCI USA Min Vol UCITS (IE00BKVL7331), Xetra EUR | 2020-04-23 | 1 621 | 1 flat |
| XSPS | Xtrackers S&P 500 Inverse Daily Swap 1C (LU0322251520), LSE | 2008-02-08 | 4 623 | 1 flat |
| NDX | Nasdaq-100 **price** index | 1985-01-31 | 10 478 | R_last 1.0000045 |

`R = adjusted/price` flat at 1 confirms the accumulating classes carry no
distributions — for these symbols the export **is** the total-return series and
the net-15 derivation is a no-op by construction (no jumps, nothing to
reinvest). LQQ alone has jumps (implied yield ≈ 0.066 %/yr over 20.2 years —
early distributions); its withholding convention is French-source, not
US-source, and is deliberately left gross (§9).

The batch did **not** include: the iMGP DBi Managed Futures UCITS ETF as a new
symbol (see §2.3 — it arrived, destructively), JPM JMFP (ticker/ISIN status
unresolved in the memo), or any FX series.

### 2.2 The suite is red, and that is the guards working

25 failures, all in `tests/test_total_return.py` live lanes — exactly the
failure class ROTATION_SPEC §3.5 built the guard for ("a bad refresh fails the
suite the day it lands"). The batch landed without its convention amendments;
Phase 0 is those amendments. Itemized:

- `test_live_pair_universe_is_pinned`: **65 pairs found vs 48 pinned.**
- `test_live_pair_invariants[…]` KeyErrors for every new symbol: no committed
  yield-band entries (CNDX, CSPX, IB01, LQQ, MVEA, NDX, QQL3, QQQ3, XSPS), plus
  collateral parametrization failures (DTB3/INDPRO/RRSFS/UNRATE FileNotFound,
  SPX/VIX/VIX3M/XNDX/GLD assertion) from the universe change itself.
- `test_adjustment_ratio_invariants[data-TQQQ]`: last-bar anchor breach,
  `|R_last − 1| = 1.44e-4` (0.999855783097779) — the TQQQ pair's two exports
  are **not from the same session** (an ex-date sits between them).
- `test_adjustment_ratio_invariants[data-DBMF]` and
  `test_implied_distributions_match_published_amounts[data-DBMF]`: see §2.3.
- `test_live_pair_invariants[NDX]`: `R_last = 1.0000045 ≠ 1` — an index has no
  adjustment toggle and should never have had a `price/` twin (README single-
  series class).

### 2.3 The DBMF overwrite — a destructive collision

The Euronext ticker of the iMGP DBi Managed Futures UCITS ETF is literally
`DBMF`, and the export **overwrote the US original**:

- `data/DBMF.csv` now: 335 rows, **2025-03-17 →** 2026-09-02 (the UCITS
  series). At `fc77fce` (pre-batch): 2019-05-08 → 2026-08-24, last close 31.25
  (the US series).
- `data/price/DBMF.csv` still starts 2019-05-08 (2 149 rows — the old US twin
  with new rows appended) and carries **duplicated dates** at the tail
  (2026-09-01 ×2, 2026-09-02 ×2). The pair invariant fails on mismatched time
  columns.

Consequences until remediated: the 2019 lane cannot be reproduced from live
`data/` (frozen snapshots are unaffected — the pinned record is safe), and the
single most important Phase-1 regression — **UCITS DBMF against US DBMF, same
manager, same strategy** — is impossible inside the repo. Phase 0 restores the
US series and lands the UCITS series under a collision-safe name.

### 2.4 Session characterization — currency and the async close

Log-return regressions of each EU series on its US counterpart over the common
calendar, at daily and weekly horizons (weekly = calendar-week last bars;
residuals annualized; drift = difference of mean daily log returns × 252):

| eu | us | n_w | β weekly | resid %/yr (w) | β daily | resid %/yr (d) | drift %/yr |
|---|---|---|---|---|---|---|---|
| CSPX | SPY | 830 | 0.887 | 5.68 | 0.558 | 12.67 | −0.26 |
| CNDX | QQQ | 827 | 0.878 | 6.71 | 0.569 | 15.14 | −0.25 |
| QQQ3 | TQQQ | 715 | 0.887 | 20.81 | 0.558 | 46.23 | −0.57 |
| QQL3 | TQQQ | 221 | 0.891 | 22.04 | 0.602 | 48.87 | −5.25 |
| LQQ | QQQ | 1053 | 1.725 | 16.76 | 0.992 | 33.58 | +8.62 |
| XSPS | SPY | 969 | −1.120 | 12.17 | −0.650 | 20.38 | −22.73 |
| MVEA | SPY | 332 | 0.471 | 9.39 | 0.252 | 12.03 | −8.56 |
| IB01 | BIL | 393 | 0.951 | 0.28 | 0.411 | 0.71 | +0.11 |
| DBMF | KMLM | 76 | 0.224 | 9.68 | 0.336 | 13.18 | +9.96 |

Four readings shape the design:

1. **The async close is real and large.** USD LSE lines show daily β ≈ 0.56
   against their US twins (London closes ~4.5 h before New York) recovering to
   ≈ 0.89 weekly. Daily and weekly regressions are therefore **biased tools**
   for this dataset; Phase 1 pre-registers **month-end** horizons, where the
   missing overlap is ~3 % of the window. The same asynchrony creates a
   **look-ahead hazard in backtests**: a same-date join of a US-close signal
   with an EU-close trade uses information ~4.5–5.5 h *after* the EU close.
   §6.1 makes the contemporaneous CNDX signal the primary arm for that reason.
2. **Currency classification.** LQQ (β 1.725 ≠ 2, drift contaminated by
   EURUSD) and MVEA (β 0.471 against an expected ~0.7, residual double CSPX's)
   carry the EUR-line signature; XSPS's elevated residual (12.17 vs CSPX's
   5.68) suggests a GBX line. CSPX/CNDX/QQQ3/QQL3/IB01 are consistent with USD
   lines. The operator records the exported TradingView line per symbol
   (§3.5); non-USD lines are FX-converted or re-exported before any use.
3. **QQQ3 looks like the substitute the memo hoped for; QQL3 does not.**
   QQQ3's drift vs TQQQ is **−0.57 %/yr over 13.7 years** — inside the memo's
   2–3 %/yr reconsider-threshold with a wide margin. QQL3 bleeds
   **−5.25 %/yr** over its 4.2 years — the physical-replication financing cost
   the memo warned about, and prima facie a FAIL against the same bar.
4. **IB01 is a near-perfect BIL twin** (weekly residual 0.28 %/yr, drift
   +0.11 %/yr). The −0.26/−0.25 %/yr drifts of CSPX/CNDX against **gross** SPY/
   QQQ are consistent with fund-level 15 % WHT plus TER — i.e. the Irish Acc
   convention matches the program's net15 basis by construction, as the memo's
   tax section claimed.

DBMF(UCITS)-vs-KMLM (β 0.224) documents what everyone knew: the UCITS ETF does
US-DBMF's job, not KMLM's index. The regression that matters (UCITS vs US
DBMF) awaits §3.1.

## 3. Phase 0 — data remediation (prerequisite; suite green before feature work)

### 3.1 Restore US DBMF; land the UCITS series as `DBMF_EU`

Fresh full-history two-pass exports — **not** a restore from git or a frozen
snapshot: goldens are append-only anchors, never a live-data source, and an
adjusted export is not append-stable (the `fc77fce` series ends 2026-08-24;
every ex-date since rescales its whole history), so a splice would be invalid
by the README's own rule. The mapping, recorded in the §3.5 line registry:

- `AMEX:DBMF` (US original, NYSE Arca) → `data/DBMF.csv` +
  `data/price/DBMF.csv`, replacing the corrupted twin wholesale;
- `EURONEXT:DBMF` (iMGP DBi UCITS, Paris) → `data/DBMF_EU.csv` +
  `data/price/DBMF_EU.csv` — expected USD line and R=1 flat (Acc); if the
  chart shows an EUR line instead, `DBMF_EU` joins `fx_lines.json`.
**Naming rule, normative for all future EU imports:** an EU line whose ticker
collides with an existing repo symbol takes the `_EU` suffix; non-colliding EU
tickers keep their exchange ticker (as this batch already does). The loader
imposes no charset constraint beyond the filename; labels and cost maps key by
the same string.

### 3.2 Re-export the US pairs from one closed session

The 1.44e-4 anchor breach (§2.2) means an ex-date sits between the two TQQQ
exports; the 677133f batch replaced it with a second failure mode — passes run
**mid-US-session** (15:40 ET), leaving seven US pairs with cross-pass intraday
mismatches on the live bar (TQQQ 2.88 bp worst) and R > 1 on three. Normative
rule, twice bitten: **both passes of any US paired symbol run after 16:00 ET**
(EU lines are immune whenever the export happens after their own close). Both
toggles re-exported per the README procedure; the anchor and ratio tests are
the acceptance check.

### 3.3 NDX joins the single-series index class

Delete `data/price/NDX.csv`; register NDX in the README's single-series table.
NDX is the **price** index (no dividends, like SPX): reference and
documentation only, never a TR seed, never a gate/vol basis for a decision lane
(CNDX carries the TR-consistent signal role in §6.1; XNDX remains the TR index
reference with its known pre-2010 defect).

### 3.4 Universe pin and yield bands

`LIVE_PAIRS` pin moves 48 → 56 (48 incumbents + QQQ3, QQL3, LQQ, CNDX, CSPX,
IB01, MVEA, XSPS, DBMF_EU, minus NDX which leaves the pair class); the yield
table gains, in the same commit: zero-bands (y ∈ [0, 1e-4]) for the eight
R=1-flat symbols and DBMF_EU, and y ∈ [0.0004, 0.0009] for LQQ (measured
0.00066). Exact pin count is fixed at implementation time by the collected set;
the test's job is that the number is *written down*, not what it is.

### 3.5 Currency metadata, FX series, and `make_usd.py`

- The README gains a per-symbol **line registry** for every EU symbol: exported
  TradingView symbol string, exchange, trading currency — operator-recorded
  from the chart, not inferred. §2.4's classification is the cross-check, not
  the source of truth.
- New single-series exports (index class, no toggle): `EURUSD.csv` and — if the
  XSPS line is confirmed GBX — `GBPUSD.csv` (TradingView `FX_IDC:EURUSD` /
  `FX_IDC:GBPUSD` or equivalent; record the chosen feed in the registry).
- New generator `make_usd.py <ROOT>`, in the `make_net_tr.py` family: reads a
  committed map `data/fx_lines.json` (`{"MVEA": "EURUSD", "LQQ": "EURUSD",
  ...}`), writes `<ROOT>-usd` where each mapped symbol's close is multiplied by
  its FX close (FX forward-filled onto the symbol's own calendar, same-date
  join — both stamps are same-day closes; the ~1 h Xetra/LSE-vs-17:00-NY FX
  offset is accepted and documented), every other file byte-copied, plus a
  provenance README. **Preference order:** where a genuine USD trading line
  exists on an IBKR-tradable exchange, a re-export of that line replaces
  conversion (conversion is the fallback, not the goal); the choice per symbol
  is frozen in the registry before Phase 1 runs.
- Engine, loader, `SCHEMA_VERSION` (4) untouched — `make_usd.py` is a root
  generator like `make_net_tr.py`/`make_synthetic.py`.

### 3.6 Frozen snapshot chain

After §3.1–§3.5 land and the suite is green: freeze
`tests/data/<TQQQ-last-bar>/` (full batch, both series, per convention), derive
`-net15`, then `-net15-usd`. **`<date>-net15-usd` is the decision root for
every lane in this spec.** Append-only as always.

## 4. Phase 1 — overlap validation (`overlap_report.py`)

### 4.1 The tool

New standalone report (family of `regime_report.py` / `score_report.py`):
for each registered pair, on the **month-end common calendar** of the decision
root, OLS of EU monthly log returns on US monthly log returns. Emits per pair:
`n_months`, `beta`, `alpha_yr` (annualized intercept, %/yr), `r2`,
`resid_yr` (annualized residual vol), rolling-12-month tracking difference
(min/median/max), and the worst single-month deviation with its date. Output:
`results/overlap_eu/overlap.json` + a markdown table, committed. A
`--horizon weekly` flag exists for the underpowered pair (§4.2 P6) and for
documentation; monthly is the decision horizon.

### 4.2 Registered pairs and pre-registered bars

Both series net15-basis (US side) / as-exported (EU Acc side — §2.4 reading 4
says these are the same convention). Bars are frozen with this spec; a bar not
listed is not a bar.

| # | pair (EU / US) | class | expected n (mo) | bars | verdict grammar |
|---|---|---|---|---|---|
| P1 | QQQ3 / TQQQ | MECHANICAL | ~164 | β ∈ [0.97, 1.03]; R² ≥ 0.98; α ∈ (−2.0, +0.5] %/yr | PASS → pin h = −α̂. α ∈ (−3, −2] → CONDITIONAL (usable, flagged). else FAIL |
| P2 | QQL3 / TQQQ | MECHANICAL | ~51 | same as P1 | same; expected FAIL on α (session −5.25) — run and record either way |
| P3 | IB01 / BIL | MECHANICAL | ~90 | \|α\| ≤ 0.30 %/yr; resid ≤ 0.75 %/yr (β unbarred — ill-conditioned at near-zero vol) | PASS → h = −α̂ |
| P4 | CSPX / SPY | MECHANICAL | ~190 | β ∈ [0.97, 1.03]; R² ≥ 0.99; α ∈ [−0.60, +0.10] %/yr on the net15 root | PASS → CSPX adopted as the holdable benchmark |
| P5 | CNDX / QQQ | MECHANICAL | ~190 | same as P4 | PASS → CNDX adopted as the EU signal symbol |
| P6 | DBMF_EU / DBMF | FUNCTIONAL (near-MECHANICAL: same manager, same strategy) | ~17 (underpowered) | weekly supplement, n ≈ 76: corr ≥ 0.90; β ∈ [0.8, 1.2]; \|α\| ≤ 1.5 %/yr | at best **PROVISIONAL PASS**; full promotion deferred to ≥ 36 months of overlap — ledger `Open:` line at 2028-03 |
| P7 | LQQ_usd / QQQ | PARAMETRIC | ~242 | β ∈ [1.85, 2.15] reported; no adoption bar | characterization only — adopting L=2 would re-open w_max and is nobody's hypothesis |
| P8 | DBMF_EU / KMLM | — | ~17 | none | documentation: the UCITS ETF substitutes DBMF's job, not KMLM's index |

**No refit on failure.** A FAIL is recorded, not engineered around; the bars
were chosen before the committed runs and after only the session-level
provisional table of §2.4, which is disclosed exactly so this ordering is
auditable.

### 4.3 Haircut constants

Every PASS/CONDITIONAL/PROVISIONAL-PASS pair pins `h = −α̂` (%/yr, ≥ 0; a
negative-drag estimate pins h = 0) into `results/overlap_eu/haircuts.json`.
These constants are the **only** free numbers Phase 3's haircut lanes consume.

## 5. Phase 2 — the synthesis arm `SYNB` (BTAL's slot)

### 5.1 Construction

`SYNB` is not a new engine object: it is a fixed sleeve blend
`{MVEA(usd): 1 − w_S, XSPS(usd): w_S}` inside the existing `safe` grammar,
rebalanced monthly with the rest of the portfolio. Long min-vol, short S&P via
the −1x daily-swap ETF — the memo's SYNTHESIS class, with its coarseness
stated up front: no sector neutrality, no cross-sectional beta spread, a
daily-reset short leg that decays between rebalances (reported, §5.3 F4).

### 5.2 Weight registration — solved, quantized, frozen

Estimation window: month-ends **2020-05 → 2023-12** (43 monthly returns),
frozen here. Solve `w_S*` for zero portfolio beta against CSPX monthly returns
on that window; quantize to the nearest of **{0.40, 0.45, 0.50}**; the chosen
point is the primary `SYNB`, the other two run as sensitivity arms in every
Phase-3 lane. 2024-01 → last bar is thereby out-of-estimation for every
evaluation. No other weight is ever fitted.

### 5.3 Falsifiers against BTAL (common window 2020-05 → last bar, ~76 months)

- **F1 — proxy bar:** monthly corr(SYNB, BTAL) ≥ 0.50.
- **F2 — insurance bar:** mean SYNB monthly return > 0 over the worst-decile
  CNDX months of the window. This is the job description; failing it fails the
  arm, not just the proxy claim.
- **F3 — E4 bound:** SYNB peak-to-trough over 2020-09-01 → 2021-03-31 (the
  anti-beta unwind, the winners' hinge episode) ≤ 1.5 × BTAL's own
  peak-to-trough over the same dates.
- **F4 — decay documentation:** realized annual shortfall of the monthly-held
  XSPS leg against −1 × S&P TR, reported per calendar year. No bar.

Verdict grammar: **PROXY** (F1 ∧ F2 ∧ F3) — SYNB may stand in BTAL's slot and
inherit the slot's framing; **ARM-ONLY** (¬F1 ∧ F2 ∧ F3) — SYNB runs as its own
sleeve arm, never described as a BTAL proxy; **FAIL** (¬F2 ∨ ¬F3) — the BTAL
slot is unfilled in Europe, full stop.

### 5.4 The no-BTAL fallbacks run regardless

Two sleeve arms are registered alongside SYNB in every direct lane so a FAIL
still leaves a ranked EU answer: `{IB01: 0.5, DBMF_EU: 0.5}` and
`{DBMF_EU: 1.0}` (the latter only on lanes reaching 2025-03). Neither inherits
any winner's status; both are NEW BLENDS under §6.5's honesty rule.

## 6. Phase 3 — the EU expression of the winners

### 6.1 Signal convention — the look-ahead rule

Primary arm: **gate and volatility both read from CNDX** (`vol_symbol` and
`gate.symbol` = CNDX), contemporaneous with the EU trading session at the
London close — no look-ahead, and live-executable as one session exactly like
the incumbent rule. Reference arm: the same strategies with QQQ signals,
**flagged as carrying a ~4.5–5.5 h look-ahead** against EU-line trades; it
upper-bounds what signal-source purity is worth and is never a decision arm.
One long-lane reference on the US side closes the loop: incumbent B75D25 on the
2019 lane with CNDX substituted as its signal — signal-source sensitivity
measured on fourteen real years with no other change.

### 6.2 Instrument map and the heritage rule

| slot | US | EU | class | validated by |
|---|---|---|---|---|
| risk | TQQQ | QQQ3 | MECHANICAL | P1 |
| MF arm | DBMF | DBMF_EU | FUNCTIONAL | P6 (provisional) |
| MF arm | KMLM | — none exists — | — | — |
| insurance | BTAL | SYNB | SYNTHESIS | §5 |
| cash | BIL | IB01 | MECHANICAL | P3 |
| signal | QQQ | CNDX | MECHANICAL | P5 |
| benchmark | SPY | CSPX | MECHANICAL | P4 |

**Heritage rule (normative):** only **B75D25** has a faithful EU expression
(`EU-B75D25 = VT QQQ3 / SYNB75 + DBMF_EU25`). B50K50 and B75K25 do **not** —
KMLM is unsubstitutable (no MLM-index product in Europe) and swapping DBMF_EU
into the K slot creates blends the program never promoted. Their EU
re-expressions run, but labelled **NEW BLEND**, clearing bars on their own
evidence and inheriting nothing.

### 6.3 Lanes

- **eu-2020 direct lane** — start **2020-04-23** (MVEA first bar), decision
  root `-net15-usd`, bundle `specs/eu_points_2020.json`: VT QQQ3 with sleeves
  SYNB100 (three w_S points), IB01 50 + SYNB 50 (the flag variant's EU
  expression), IB01 50 + DBMF_EU 50 fallback (starts 2025-03; the loader's
  union-calendar rule cannot start this arm earlier, so it runs in the eu-2025
  lane instead if the runner rejects it here), CSPX and SPY benchmarks, plus
  the QQQ-signal reference twin of the primary arm.
- **eu-2025 direct lane** — start 2025-03-17 (DBMF_EU first bar): EU-B75D25
  and the §5.4 fallbacks. **DOCUMENT-ONLY** — eighteen months decides nothing
  (the RSSB lesson).
- **Haircut lanes — component isolation on the promotion lanes.** New
  generator `make_haircut.py <ROOT>` (family of `make_synthetic.py`): reads
  `results/overlap_eu/haircuts.json`, writes `<ROOT>-hc` with each mapped US
  symbol's close series compounded down by `h/252` per bar from its first bar,
  everything else byte-copied. No-contamination invariant: `h = 0` reproduces
  the parent root bit-for-bit (test T4). Lanes: the winners' own bundles rerun
  against `-net15-usd-hc` on the 2021 and 2019 windows — TQQQ carrying P1's h,
  BIL carrying P3's, DBMF carrying P6's, KMLM and BTAL **uncarried**
  (unsubstitutable slots take no fictitious haircut; their columns are flagged
  in the verdict as translation-incomplete). This isolates the measured
  translation cost of the substitutable components on fourteen and seven real
  years, including a real COVID for B75D25.
- **Composed estimate — arithmetic, not a run:** the verdict table composes
  EU-winner ≈ US-winner CAGR − Σh(components) alongside the direct-lane
  measurements, labelled an estimate. No new machinery.

### 6.4 Costs

The EU cost map extends `cost_bps`; the figures below are **placeholders**
pending operator-measured live quoted spreads (5-session median at the London
close, recorded in the line registry) — the pre-registration freeze binds the
measured values, not these: QQQ3 15, QQL3 20, CNDX 4, CSPX 2, IB01 2, MVEA 12,
XSPS 12, DBMF_EU 15, `*` 15. Same map convention as the incumbent
(`top_strategies_*.json`). The **c20 flat-stress twin is mandatory for every
lane** in this spec — EU spreads are the least-known cost input and the stress
bracket is the insurance against optimistic placeholders. IBKR commissions and
EUR→USD conversion are strategy-invariant and excluded, same convention as
Wise 45 bp (RECAP §8.6).

### 6.5 Decision bars

Per EU-expressed strategy, on the eu-2020 direct lane **and** surviving the
c20 stress there, and with its substitutable components' haircut lanes still
beating the benchmark on the 2021/2019 windows:

- **IMPLEMENTABLE**: beats **CSPX** on both CAGR and max drawdown on the
  direct lane (base and c20), and the haircut-lane winners it descends from
  still beat CSPX and SPY on their windows.
- **IMPLEMENTABLE-PENDING**: as above but resting on P6's provisional pass —
  re-read at the 2028-03 `Open:` line.
- **BLOCKED(component)**: any required component FAILed its phase; name the
  component. A BLOCKED verdict is a finding, not a defeat — "the EU expression
  is blocked at the insurance arm" is exactly the sentence this cycle exists
  to be able to write with numbers behind it.

Nothing here re-ranks the tastytrade winners; the EU verdict is a parallel
column in the winners file, not an edit to it.

## 7. Windows the data supports — recorded, not decided

| lane | start | binding constraint |
|---|---|---|
| P1 overlap | 2012-12-17 | QQQ3 first bar |
| P2 overlap | 2022-06-09 | QQL3 first bar |
| P3 overlap | 2019-02-22 | IB01 first bar |
| P4/P5 overlap | 2010-09-15 | CSPX/CNDX first bars |
| P6 overlap | 2025-03-17 | DBMF_EU first bar — underpowered until ≥ 2028-03 |
| SYNB estimation | 2020-05 → 2023-12 | frozen §5.2 |
| SYNB falsifiers / eu-2020 | 2020-04-23 | MVEA first bar |
| eu-2025 | 2025-03-17 | DBMF_EU first bar — DOCUMENT-ONLY |
| haircut 2021 / 2019 | 2020-12-18 / 2019-05-08 | inherited from the promotion lanes |

The eu-2020 lane contains E4, the 2022 grind and the 2025 tariff episode, but
no COVID and no pre-2011 bear; every EU verdict inherits the program's one-era
caveat with an even shorter direct record. That is stated in the verdict, not
footnoted.

## 8. Tests

- **T1** universe pin and yield bands updated in one commit (§3.4); the DBMF
  pair invariant green again after §3.1; TQQQ anchor green after §3.2.
- **T2** `make_usd.py`: deterministic (two runs byte-identical); unmapped
  symbols byte-copied; a mapped symbol's converted close equals close × FX on
  every bar (spot-pinned rows); missing FX file is a loud failure.
- **T3** `overlap_report.py`: golden run on the frozen root pins P1–P8 rows;
  month-end calendar construction asserted against a hand-built fixture.
- **T4** `make_haircut.py`: no-contamination (`h = 0` root bit-identical to
  parent); a pinned `h = 1.0` fixture row; unmapped symbols byte-copied.
- **T5** SYNB weight solve: reproducible from the frozen root (pinned `w_S*`
  and chosen grid point); estimation window boundaries asserted.
- **T6** bundle smoke: `eu_points_2020.json` and the haircut-lane reruns load,
  simulate, and name every symbol they read, on the frozen roots.

## 9. Out of scope

EUR-basis re-denomination of the whole program (the investor's consumption
currency — a real question, its own spec); JMFP (data absent, ticker/ISIN
status contradictory in the memo — a data request, §11); Tier-C UCITS mutual
funds (dealing mechanics differ; IBKR IE retail availability unverified);
adopting LQQ / L=2 (P7 characterizes only); distributing EU share classes and
their non-US withholding conventions (LQQ stays gross); a longer-history
min-vol long leg (SPMV-class, 2012 inceptions — optional request, §11); live
order mechanics beyond the cost map; any change to engine files or
`SCHEMA_VERSION`.

## 10. Implementation order

1. §3.1–§3.3 exports and deletions; suite locally green on the pair tests.
2. §3.4 pin + bands; §3.5 registry, FX exports, `fx_lines.json`,
   `make_usd.py` + T2. Full suite green.
3. §3.6 snapshot chain frozen; this spec committed **before** any §4–§6 run
   (the pre-registration commit).
4. `overlap_report.py` + T3; committed Phase-1 artefacts; haircuts pinned.
5. SYNB solve + T5; falsifier report committed.
6. `make_haircut.py` + T4; `-hc` roots; bundles + T6; lanes run; verdict
   (`notes/eu-verdict.md`) with the §6.5 vocabulary.
7. Byte-reproducibility pass on a fresh clone.

## 11. Data requests (operator)

1. **DBMF re-downloads** (two-pass, one session each): `AMEX:DBMF` →
   `DBMF.csv`, `EURONEXT:DBMF` → `DBMF_EU.csv` — resolves §2.3.
2. **US paired-symbol re-export after 16:00 ET** (both passes; at minimum
   ACWX, IEF, IWM, QQQ, SPY, TQQQ — a full US pass is cleaner) — clears the
   anchor/ratio breaches of §3.2.
3. **FX singles**: EURUSD (and GBPUSD if the XSPS line is confirmed GBX).
4. **Line registry entries** for all nine EU symbols: exact TradingView symbol
   string, exchange, trading currency, from the chart.
5. Optional, non-blocking: USD-line re-exports for MVEA (and XSPS) if such
   lines exist on an IBKR-tradable exchange; a 2012-inception US min-vol long
   leg (SPMV-class) to lengthen the SYNB record; JMFP once its live ISIN is
   resolved in IBKR Contract Search.

## 12. Errata

None at freeze.
