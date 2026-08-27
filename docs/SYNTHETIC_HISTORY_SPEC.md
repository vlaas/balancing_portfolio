# Specification: synthetic pre-inception history — the bear test the data never had

Repo: `vlaas/balancing_portfolio` · baseline commit: `5d211f6` (composition merged;
806 tests green on a fresh clone) · status: **proposed** · input:
`docs/HANDOFF_COMPOSITION.md` §7 (the standing data need) · predecessors:
`TOTAL_RETURN_SPEC.md` / `NET_TR_SPEC.md` (the dataset conventions this extends),
`COST_MODEL_SPEC.md` §9 ("synthetic pre-2010 history — own spec, the financing model is
the substance there"), `ROTATION_SPEC.md` §10 ("SPX is price-only and must never seed a
TR sim").

## 1. Goal

Every verdict in this repository carries the same caveat: the incumbent machine has
been tested on one era. Its risk asset starts 2010-02-11 and its sleeve 2011-09-13, so
2000–02 and 2008 — the two bears a 3× fund is actually afraid of — are untested
everywhere, and the rotation program's R2 tension ("these strategies do not insure" vs
"this holdout had nothing to insure against") was left unresolved for want of a bear
holdout. This spec builds the data that resolves it for the incumbent machine, in three
parts:

1. **A financing model for a daily-rebalanced leveraged fund**, fitted on TQQQ's own
   sixteen years and validated on the crashes it contains, then applied to QQQ's real
   total-return history back to 1999-03-10. A T-bill accrual model does the same for
   BIL back to 1999 via DTB3. Both are **spliced onto the real series** at the real
   first bar, so every run that starts on or after the real inception is bit-identical
   to today's.
2. **Two frozen dataset roots** (`tests/data/2026-08-24-syn`, `-syn-net15`) built by a
   deterministic generator from committed inputs, in the append-only convention, with
   the engine, the loader and `SCHEMA_VERSION` untouched.
3. **Two bear lanes and a bridge**, read as **falsifiers of the 2012-chosen plateau**
   with pre-registered kill conditions. A synthetic root is never a fitting lane: no
   parameter is adopted from it, and a coordinate that fails on it is flagged, not
   re-fitted here.

Scope is the incumbent machine's inputs only — TQQQ and a cash sleeve — because those
are the two series with a defensible model and a real overlap to validate it on. The
BTAL sleeve has no pre-2011 proxy and is not synthesised (§13); the synthetic lanes run
the machine with a BIL sleeve, and a bridge lane on real 2012+ data measures what that
substitution costs, so the bear-era numbers are read with a known bias direction.
Rotation proxies (mutual-fund NAV series for the 2002–2007 inceptions) are a different
export class and out of scope (§13).

Three measured facts shaped the design (§2 has the full tables):

- **The floating rate is not optional.** A constant-drag model fitted to TQQQ gives
  1.93 %/yr on 2010–2018 and 7.98 %/yr on 2018–2026 — the ZIRP-to-hikes swing sits in
  the financing term. With DTB3 carried as the floating leg, the residual constant is
  1.33 vs 2.51 %/yr on the same halves, and the model reproduces every real TQQQ crash
  to within 0.3 pp of depth.
- **The pre-inception era has a real 2× fund in it.** QLD (2× QQQ) trades from
  2006-06-21, through the GFC and the ZIRP transition. The same model fitted on QLD
  gives 1.32 %/yr after 2010 and 2.41 %/yr across 2006–2010 (3.27 %/yr in the
  crisis-and-ZIRP stretch): swap financing over T-bills widened in the crisis, as the
  TED spread says it did. That widening sets the upper bracket of the drag constant
  (§2.4), and the pilot shows the bracket is inert for every machine-level conclusion.
- **The XNDX export is stamped one day late before 2010** (same-day correlation with
  QQQ ≈ 0, next-day 0.97–0.99, 2006-11 → 2009). XNDX is signal-only and unused by any
  adopted strategy; it is pinned as a defect (§6 S5) and plays no part in the synthetic
  series, which is built from QQQ's own total-return export — a series whose pre-2010
  dividend embedding is checked in §2.2 and carries no dividends at all before
  2003-12-24.

## 2. What is already true at `5d211f6` (measured on this clone)

### 2.1 Sources and inceptions

| series | file | first bar | role here |
|---|---|---|---|
| QQQ total return | `tests/data/2026-08-24/QQQ.csv` (gross pair, 6,907 rows) | 1999-03-10 | the index leg of the synthetic 3× |
| TQQQ total return | `…/TQQQ.csv` | 2010-02-11 | calibration overlap; the real segment |
| QLD, SSO (2×) | `…/QLD.csv`, `…/SSO.csv` | 2006-06-21 | era validation of the financing model |
| BIL total return | `…/BIL.csv` | 2007-05-30 | calibration overlap; the real segment |
| DTB3 (3-month T-bill, FRED) | `tests/data/2026-08-24/macro/DTB3.csv` (18,150 rows) | 1954-01-04 → 2026-08-20 | the floating rate; 1999-03 → 2010-02: 2,742 rows, 0.00–6.24 %, mean 2.83 % (2000: 5.82 %, 2009: 0.15 %) |
| XNDX (Nasdaq-100 TR index) | `…/XNDX.csv` | 2006-11-08 | cross-check from 2010 only (§2.5) |
| SPY total return | `…/SPY.csv` | 1993-01-29 | benchmark, real throughout |

QQQ's SMA-200 first prints on **1999-12-21**, so a lane anchored 2000-01-03 has the gate
from its first day and catches the 2000-03 top.

### 2.2 QQQ's total-return export on the pre-inception stretch

From the gross pair (`R = adjusted / price`, TOTAL_RETURN_SPEC §4): **24 implied
ex-dates 1999-03-10 → 2010-12-31, none before 2003-12-24**. Implied yield by year:
2003 0.04 %, 2004 0.95 % (one $0.379 distribution, 2004-12-17), 2005 0.33 %, 2006 0.32 %,
2007 0.30 %, 2008 0.36 %, 2009 0.56 %, 2010 0.73 %; full-file 0.62 %/yr, inside the
pinned band. The dot-com stretch is therefore dividend-free by construction — the one
era where a mis-embedded dividend could not matter — and 2004–2009 embeds at most
0.95 %/yr, i.e. at most ~2.9 %/yr of 3× exposure even if every one of those
distributions were wrong, inside the §2.4 drag bracket. Against XNDX from 2010-01-04
(the correctly stamped stretch, 4,184 days): drift −0.215 %/yr (QQQ's expense ratio),
daily residual 6.8 bp, max cumulative deviation 3.79 %.

### 2.3 The financing model, fitted on TQQQ

Daily simple return of a daily-rebalanced L× fund on an index total-return series,
with calendar-day financing on the borrowed (L−1) at the T-bill rate known the day
before, and one constant `c` for everything else (expense ratio, swap spread over
T-bills, tracking):

```
r_t = L · s_t − (L − 1) · y_{t−1} · d_t / 360 − c · d_t / 365
```

`s_t` the index's simple return over the bar, `y_{t−1}` DTB3 (decimal) forward-filled
onto the index calendar and lagged one row, `d_t` calendar days since the previous bar.
`c` is the closed-form mean-residual estimate on log returns,
`c = −Σ resid_t / Σ d_t · 365` with `resid_t = ln(1 + r^{real}_t) − ln(1 + L s_t − (L−1) y_{t−1} d_t/360)`,
so the fitted series ends the overlap at the real series' level exactly (`cum_end` 0).
Fitted on TQQQ vs QQQ, `L = 3`, gross root, overlap ending 2026-08-20 (DTB3's last bar):

| overlap | n | `c` %/yr | realised beta | daily residual | max cum. dev. |
|---|---|---|---|---|---|
| **full 2010-02-11 → 2026-08-20** | 4,155 | **1.90** | 2.977 | 17.7 bp (2.80 %/yr) | 9.14 % |
| H1 2010-02 → 2018-06 | 2,110 | 1.33 | 2.972 | 16.3 bp | 1.48 % |
| H2 2018-07 → 2026-08 | 2,044 | 2.51 | 2.980 | 19.0 bp | 5.19 % |
| ZIRP 2010-02 → 2015-12 | 1,482 | 1.24 | 2.968 | 17.9 bp | 1.45 % |
| hikes 2022-03 → 2026-08 | 1,122 | 2.61 | 2.974 | 10.9 bp | 0.91 % |

The same fit with **no floating leg** (constant drag only): full 4.90, H1 1.93, H2 7.98,
ZIRP 1.38, hikes 10.93 %/yr — a six-point swing between halves that the floating model
reduces to 1.2. The realised beta is 2.977, not 3.000; the 0.8 % of exposure is inside
the `c` bracket and the fund's contract is 3×, so `L = 3` is used as written.

**Validation on the crashes the overlap contains** (synthetic built from QQQ with
`c = 1.90`, never spliced, against real TQQQ): COVID −69.68 % vs −69.92 %, 2022 −81.47 %
vs −81.66 %, 2018-Q4 −58.20 % vs −58.08 %, 2025 −56.79 % vs −56.84 %. Within-year
returns agree to ±1.7 pp in every year but 2020 (−3.2 pp: +103.3 % vs +100.1 %). The
cumulative ratio real/synthetic over the 16.5-year overlap stays in [0.9915, 1.0960]
and ends at 1.0002.

### 2.4 The era the model will be used in: QLD and SSO

| fund | overlap | `c` %/yr | realised beta | daily residual | max cum. dev. |
|---|---|---|---|---|---|
| QLD (2× QQQ) | 2006-06-21 → 2010-02-10 (pre-TQQQ) | **2.41** | 1.963 | 54.9 bp | 3.11 % |
| | 2006-06 → 2008-08 (pre-Lehman) | 1.85 | 1.898 | 51.6 bp | 2.18 % |
| | 2008-09 → 2010-02 (crisis + ZIRP) | **3.27** | 1.993 | 59.8 bp | 4.09 % |
| | 2010-02-11 → 2026-08-20 | 1.32 | 1.999 | 9.8 bp | 3.95 % |
| SSO (2× SPY) | 2006-06-21 → 2010-02-10 | 2.05 | 1.899 | 48.2 bp | 3.19 % |
| | 2010-02-11 → 2026-08-20 | 1.38 | 2.006 | 9.7 bp | 2.55 % |

QLD's stamps are correctly aligned throughout (same-day correlation with QQQ 0.98–0.99
in every year 2006–2011); the 5× larger pre-2010 residual is early-ETF price/NAV noise,
not the XNDX defect. The model holds in the GFC — max cumulative deviation 4 % across
the crisis — but the constant is higher: the borrowed leg was priced over LIBOR, not
T-bills, and the TED spread blew out. **Bracket for the synthetic 3×**, expense-ratio
free and stated as offsets around whatever constant the root being built fits (§3):
`c_lo = c − 0.66` (the full fit less TQQQ's ZIRP fit, 1.90 − 1.24), `c_mid = c` (the
primary), `c_hi = c + 2 × (2.41 − 1.32) = c + 2.18` (twice QLD's crisis-era spread
widening, one unit borrowed → two). On the gross root that is 1.24 / 1.90 / 4.08 %/yr;
on the net15 root 1.29 / 1.94 / 4.13 (§2.5).

### 2.5 The T-bill accrual, fitted on BIL — and how withholding enters each model

`r_t = (1 − w) · y_{t−1} · d_t / 360 − c_b · d_t / 365`, with `w` the parent root's
withholding (0 on the gross root, 0.15 on net15). BIL vs DTB3, full overlap 2007-05-30 →
2026-08-20 (4,837 days): gross root **`c_b = 0.109 %/yr`** (BIL's expense ratio, to the
basis point), daily residual 3.0 bp, max cumulative deviation 1.13 %; halves 0.031 /
0.191 %/yr; ZIRP 0.105 %/yr with max deviation 0.26 %. Net15 root with `w = 0.15`:
**`c_b = 0.093 %/yr`**, max deviation 1.10 % — the same expense ratio again, so the
proportional term is the right shape. Forcing the gross model (`w = 0`) onto the net15
series instead gives `c_b = 0.317 %/yr` with a worse fit (2.27 %): a T-bill fund
distributes its whole accrual, so withholding on it scales with the rate and cannot be
a constant. At 2000's 5.8 % rates that is 0.87 %/yr on the sleeve.

The 3× is the opposite case. Refitting §2.3 against the **net15** TQQQ (index leg still
gross QQQ — a swap pays the gross total return) gives `c = 1.943 %/yr` against the gross
root's 1.897: a delta of **4.61 bp/yr**, which is 15 % × TQQQ's implied 0.307 %/yr
distribution yield (4.60 bp) to the hundredth of a basis point. A leveraged fund's own
distributions are tiny and roughly constant, so the constant absorbs their withholding
exactly. Hence §3's rule: **each root fits its own constants against its own real
segment**, the bill model carries `w` explicitly, and the two roots' synthetic segments
differ — by 4.6 bp/yr on TQQQ and by 15 % of the T-bill rate on BIL.

### 2.6 The XNDX export defect

QQQ vs XNDX daily log returns, same-day / next-day-XNDX correlation by year: 2006 0.10 /
0.99, 2007 −0.01 / 0.98, 2008 −0.11 / 0.97, 2009 0.05 / 0.88, 2010 onward 0.997–1.000 /
≈ 0. Shifting XNDX back one row over 2006-11 → 2009-12 still leaves a 58.6 bp daily
residual, so the misalignment is not a clean one-day lag and the stretch is unusable as
a reference. It is recorded, not repaired: XNDX is not an input to anything.

### 2.7 What the machine does through the bears (pilot, §11)

The prototype generator built three scratch roots in the net15 convention (`c` = 1.29 /
1.94 / 4.13, `c_b = 0.093`, `w = 0.15` on the bill) on the net15 parent and ran the
incumbent machine with a BIL sleeve from 2000-01-03. Headline at `c_mid`, 2000-01-03 →
2011-12-30: gated σ0.20/w0.8 CAGR **+3.8 %**, max DD **−35.9 %** (GFC), dot-com episode
−27.3 %; gated σ0.30/w0.6 CAGR +3.6 %, max DD **−50.4 %** — across the −50 % constraint;
both ungated twins −60.7 % / −77.3 %; TQQQ buy-and-hold −100.0 % (−99.95 % in the
dot-com alone); SPY +0.3 %, −55.4 %; QQQ −4.0 %, −82.9 %. The `c` bracket moves every
gated number by ≤ 0.6 pp from `c_mid`. (An earlier pilot pass built the net15 roots
with the gross-fitted constants and a gross bill; the withholding correction moved the
gated arms by 0.1–0.4 pp and nothing else.)

## 3. The generator — `make_synthetic.py`

A sibling of `make_net_tr.py`, deterministic by construction (no clock, no environment,
no network), ~150 lines:

```
uv run make_synthetic.py PARENT --gross GROSS --withholding W [--out DIR] [--drag C] [--bill-drag CB] [--force]
uv run make_synthetic.py tests/data/2026-08-24-net15 --gross tests/data/2026-08-24 --withholding 0.15
uv run make_synthetic.py tests/data/2026-08-24       --gross tests/data/2026-08-24 --withholding 0
```

- **Inputs**: `PARENT/TQQQ.csv`, `PARENT/BIL.csv` (the real segments, in the parent's
  withholding convention), `GROSS/QQQ.csv` (the index leg — a swap pays the gross
  total return, in both roots), `GROSS/SPY.csv`
  (the calendar the bill accrues on: it reaches 1993 and is the loader's widest traded
  calendar), `GROSS/macro/DTB3.csv` (the floating rate; read by the generator as a
  build input, **never by the loader** — the `macro/` quarantine of ROTATION_SPEC §3.3
  is about signal reads with an availability lag, and a rate lagged one row that
  prices yesterday's borrowing is not a signal).
- **Fit, per root**: `c` and `c_b` by the §2.3 / §2.5 estimators on the full overlap,
  **against the parent's own real segments** (the parent's TQQQ vs gross QQQ; the
  parent's BIL vs `(1 − w)` × DTB3), printed and written to the README. `--withholding`
  is required and must match the parent (guard: a parent whose basename contains
  `-net15` requires 0.15, any other requires 0); it enters the bill recursion as
  `(1 − w)` and the 3× recursion not at all (§2.5 — the constant carries it). So the two
  roots' synthetic segments differ, each in its own convention. `--drag` /
  `--bill-drag` override the fit (the bracket roots of §9 are built this way and are
  not committed).
- **Synthesis**: the §2.3 recursion from 1.0 at QQQ's first bar (1999-03-10) for the 3×;
  the §2.5 recursion with the root's `w` from 1.0 at SPY's first bar for the bill. DTB3 is joined onto the
  target calendar by date, forward-filled, then lagged one row; the first row's return
  is 0.
- **Splice**: the synthetic series is kept strictly before the real segment's first
  bar and scaled by `real_first / synthetic_at_first` so the two meet there
  multiplicatively; the real segment is copied value-for-value. Output columns
  `time,close,source` with `source ∈ {synthetic, real}` — the loader whitelists
  `time,close` and ignores the third (`prices._read_close`, verified), and the column
  is the audit trail.
- **Root layout** (`PARENT` basename + `-syn`): every parent top-level `<SYM>.csv`
  byte-copied except the two spliced files; `price/` byte-copied **without** twins for
  the spliced symbols (the synthetic segment has no unadjusted twin, and a missing file
  is the honest statement — no pair test runs on a synthetic root); `macro/` not copied
  (as `make_net_tr.py` does); a README naming the parent, the gross root, the fitted
  constants, the splice dates and ratios, and the §2.3 / §2.5 validation numbers as
  measured on this build.
- **Guards**: refuse an existing output without `--force`; refuse a parent whose
  TQQQ/BIL first bars are not 2010-02-11 / 2007-05-30 unless `--force` (a refreshed
  parent with a different inception is a different splice and must be looked at);
  assert the synthetic 3× has a bar on the real first date; assert `c` within
  [0.5, 4.5] %/yr and `c_b` within [−0.1, 0.4] %/yr (a fit outside those bands means
  the wrong file was passed).

No engine file changes. `prices.py`, `simulate.py`, `indicators.py`, `stats.py`,
`results_json.py`, `strategy.py`, `strategies/*`, `spec.py`, `sweep.py`: **untouched**.
`SCHEMA_VERSION` stays 4. The synthetic root is just another `--data`.

## 4. Roots — `tests/data/2026-08-24-syn`, `tests/data/2026-08-24-syn-net15`

Built once by §3 from the committed 2026-08-24 pair, committed, append-only. Sizes:
TQQQ.csv 6,907 rows (2,749 synthetic + 4,158 real), BIL.csv 8,449 rows (3,609 synthetic
+ 4,840 real); everything else identical to the parent. The two roots' synthetic
segments are not identical (§2.5): TQQQ's differ by the 4.6 bp/yr constant, BIL's by
the `(1 − w)` accrual. Byte-reproducible from the committed parent and the committed
generator (test S4).

**The no-contamination invariant**: any run whose window starts on or after 2010-02-11
and whose sleeve is not BIL reads only real bars and must reproduce the parent root's
numbers exactly (S9 pins the 2012-lane anchor 0.86123626 through the syn root). A run
with a BIL sleeve starting after 2007-05-30 likewise.

## 5. The XNDX note

`data/README.md` gains, under "Single-series index": *XNDX rows before 2010-01-04 are
stamped one trading day late relative to every ETF export (SYNTHETIC_HISTORY_SPEC §2.6);
the file is signal-only and no strategy reads it, but it must not be used as a
reference before 2010.* No file is edited; a re-export to see whether the feed or the
export is at fault is an operator task outside this spec.

## 6. Tests — new `tests/test_synthetic.py`, one edit in `tests/test_spec.py`

Cite as "SYNTHETIC_HISTORY_SPEC S·". Real-data pins run on the committed 2026-08-24
roots; model pins are computed by the generator's functions, not read from the README.

**S1 — The financing fit reproduces.** `fit_drag("TQQQ", "QQQ", L=3)` with the gross
root's TQQQ, overlap ending 2026-08-20: `c` = 0.01897 ± 0.0001, realised beta 2.977 ±
0.003, daily residual std 17.7 ± 0.3 bp, max cumulative deviation ≤ 0.095; on the halves
`c` = 0.0133 / 0.0251 (± 0.0002). With the net15 root's TQQQ: `c` = 0.01943 ± 0.0001, and
the difference equals 0.15 × TQQQ's implied distribution yield within 0.1 bp/yr. The
constant-only variant on the gross halves 0.0193 / 0.0798 — the test that says why the
floating leg exists.

**S2 — The era fit.** QLD, `L = 2`: 2006-06-21 → 2010-02-10 `c` = 0.0241 ± 0.0002;
2010-02-11 → 2026-08-20 `c` = 0.0132 ± 0.0002. QLD same-day correlation with QQQ ≥ 0.98
in every year 2006–2011 (the alignment guard that S5's XNDX fails).

**S3 — The bill fit.** BIL vs DTB3, full overlap: gross root, `w = 0`: `c_b` = 0.00109 ±
0.00003, max cumulative deviation ≤ 0.012; net15 root, `w = 0.15`: `c_b` = 0.00093 ±
0.00003, max deviation ≤ 0.012; net15 root with `w = 0` forced: `c_b` > 0.0030 and max
deviation > 0.02 — the shape test that keeps the proportional term.

**S4 — Reproducibility and layout.** `make_synthetic.py` into a temp dir from the
committed parents reproduces the committed `-syn` and `-syn-net15` roots file-for-file
and byte-for-byte (the N5 pattern); the spliced files carry `time,close,source`, the
`source` column flips exactly once, at 2010-02-11 / 2007-05-30; the real segment equals
the parent's file value-for-value; `price/` has no `TQQQ.csv` / `BIL.csv`; `macro/` is
absent; `load_prices(syn_root, ["TQQQ", "BIL"], start=2000-01-03)` returns a frame with
no nulls in either traded column.

**S5 — The XNDX defect pin.** Same-day QQQ/XNDX correlation < 0.2 and next-day > 0.95 for
each of 2007 and 2008; ≥ 0.99 for each of 2010–2025. If a re-export ever fixes the
stretch, this test fails loudly and the README note comes out.

**S6 — Crash replication.** Synthetic 3× from gross QQQ at the S1 `c`, unspliced,
against real TQQQ: max drawdown inside each of the four windows (2020-02-01 →
2020-04-30, 2021-11-01 → 2023-01-31, 2018-08-01 → 2018-12-31, 2025-02-01 → 2025-05-31)
within 0.5 pp of the real fund's; cumulative ratio over the overlap within [0.98, 1.11].

**S7 — Depths of the bears.** On the committed `-syn` root's TQQQ: max drawdown
2000-03-01 → 2003-03-31 ≤ −0.999 (measured −99.95 %), 2007-10-01 → 2009-03-31 ≤ −0.94
(measured −94.62 %); QQQ's on the same windows −82.98 % / −53.4 % (the real index, a
sanity anchor).

**S8 — Bracket inertness.** Generator into a temp dir from the net15 parent with
`--drag 0.0129` and `--drag 0.0413`; the gated σ0.20/w0.8 BIL-sleeve machine on
2000-01-03 → 2011-12-30 prints CAGR within 0.7 pp and max drawdown within 0.5 pp of the
committed root's on both.

**S9 — No contamination.** On `-syn-net15`, `VT TQQQ/BTAL t30 w0-60 λ0.80 gate
QQQ<SMA200` from 2012-01-03, blend costs, `cash_yield` 0.03 → full Calmar **0.86123626**,
CAGR 0.2381710, max drawdown −0.27654555 (the composition anchor, bit-equal); the no-gate
twin 0.71623794.

**S10 — QQQ's pre-inception dividends.** From the gross pair: 24 implied ex-dates on
1999-03-10 → 2010-12-31, first 2003-12-24, the §2.2 yield-by-year table to 0.01 pp, no
jump before 2003. Plus an operator spot check recorded in the root README: the
2004-12-17 implied distribution ($0.37858 in today's split basis) and two others against
the issuer's published history, in the TOTAL_RETURN_SPEC §4 manner.

**Edit — `tests/test_spec.py::every_strategy`.** Specs whose stem starts with `syn_` are
skipped like `sweep_`, with a comment: they start in 2000 and the flat golden snapshot's
TQQQ does not; the S-tests run them on the synthetic roots instead. (The composition's
errata 2 pattern, one line.)

## 7. Lanes and bundles

All with the incumbent lanes' blend cost map plus `BIL 0.5` bp per side (a T-bill ETF at
one tick; the flat-20 bracket bounds it), objective Calmar, constraint max drawdown
≥ −50 %, contributions 10 000 + 500 / month, `cash_yield` 0.03, primary data
`tests/data/2026-08-24-syn-net15`, gross bracket `-syn`.

### 7.1 The grid (shared by both lanes) — 16 points

```json
"template": {
  "type": "vol_target", "risk": "TQQQ", "safe": "BIL", "vol_symbol": "QQQ",
  "vol": { "kind": "ewma", "lam": { "grid": [0.80, 0.94] } }, "leverage": 3,
  "sigma_target": { "grid": [0.20, 0.30] }, "w_max": { "grid": [0.6, 0.8] },
  "gate": { "grid": [null, { "symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200 }] }
}
```

The winners' coordinate (0.80 / 0.20 / 0.8 / gate) and the 2012-lane regime coordinate
(0.80 / 0.30 / 0.6 / gate) are both grid points; λ 0.94 is the RiskMetrics control the
plateau finding was made against. Baselines: SPY, QQQ, gated `TQQQ50/BIL50`, and
`TQQQ` buy-and-hold (a baseline is not constrained, so its −100 % prints rather than
disappears).

### 7.2 `specs/sweep_syn_2000.json` — the bear era on its own (16 + 4 × ~21 windows)

Windows `start 2000-01-03, end 2011-12-30, holdout 2008-01-02, sensitivity 6 m / 3 y`.
Fit = 2000–2007 (the dot-com bear and its recovery), test = 2008–2011 (the GFC and
2011). Every window is out of sample with respect to the parameter choice, which was
made on 2012–2026, and the holdout is a bear — the design the rotation program could
not have.

### 7.3 `specs/sweep_syn_full.json` — two eras (16 + 4 × ~46 windows)

Windows `start 2000-01-03, holdout 2012-01-03, sensitivity 6 m / 5 y`. Fit = the
synthetic era, test = the real era where the parameters were chosen (contaminated as a
test, and read as such — it is the *fit* column and the ~43 sensitivity windows that
matter here). `robust_score` and `rank_worst` across 26.6 years, with 2000–02 and 2008
inside the sensitivity set for the first time.

### 7.4 `specs/syn_points.json` — the panel (2000-01-03 → end)

The two named coordinates of §7.1 — the winners' (0.80 / 0.20 / 0.8) and the 2012-lane
regime coordinate (0.80 / 0.30 / 0.6) — each with and without the gate (4 strategies),
plus the four baselines: 8 strategies in all, on the primary root, `--json` for
`drawdowns` and `yearly_returns`: the per-episode panel
(dot-com 2000-03 → 2002-10, GFC 2007-10 → 2009-03, 2011, COVID, 2022, 2025) and the
calendar-year table 2000 / 2001 / 2002 / 2008 / 2009. Run three more times without
committing data: on `-syn` (gross bracket), and on two temp roots built with `--drag
0.0129` / `--drag 0.0413` (the `c` bracket, §2.4 offsets around the net15 fit) — outputs committed as
`results/syn_points_tr.json`, `_clo.json`, `_chi.json` with the build command in the
verdict.

### 7.5 `specs/syn_bridge_2012.json` — the sleeve bridge (2012-01-03 → end)

The same eight strategies on the synthetic root from 2012 (only real bars are read),
plus BTAL-sleeve twins of the two gated VT arms: 10 strategies. The BTAL twins reproduce
the committed 2012-lane numbers (S9); the BIL arms measure the substitution cost.
Pilot: gated σ0.30/w0.6 with BIL 0.7386 / 25.93 % / −35.11 % against BTAL's 0.8612 /
23.82 % / −27.65 %; gated σ0.20/w0.8 with BIL 0.7991 / 21.66 % / −27.10 %. The BIL
sleeve is the worse sleeve by 7–8 drawdown points on the real era, so the bear-era
numbers understate the incumbent wherever BTAL would have helped (and a
long-low-beta / short-high-beta sleeve in 2000–02 is the case where it would have).

### 7.6 Size

`--dry-run`: 20 × 21 = 420 twelve-year runs, 20 × 46 = 920 twenty-seven-year runs, four
runs of the 8-strategy panel bundle and one 10-strategy bridge — a few minutes. Dual pre-flight (handoff §6): every symbol read (TQQQ,
BIL, QQQ, SPY) is present from 1999-03-10 on both synthetic roots; the widest indicator
is SMA-200 on QQQ, warm 1999-12-21; the loader's completeness assert covers the rest.

## 8. Docs

- `data/README.md`: a "Synthetic roots" section (the model in three lines, the splice
  rule, the `source` column, the no-contamination invariant, "never a fitting lane")
  and the §5 XNDX note.
- `docs/ARCHITECTURE.md`: dataset classes gain "synthetic-extended (`-syn`, `-syn-net15`)";
  `make_synthetic.py` beside `make_net_tr.py`.
- `docs/TOTAL_RETURN_SPEC.md` / `NET_TR_SPEC.md`: one cross-reference line each.
- `CLAUDE.md` §6: *a synthetic root is a falsifier, never a fitting lane; no parameter is
  adopted from a window that contains synthetic bars.*

## 9. Run protocol

```
uv run pytest                                                            # S1–S10 green from a fresh clone
uv run make_synthetic.py tests/data/2026-08-24-net15 --gross tests/data/2026-08-24 --withholding 0.15
uv run make_synthetic.py tests/data/2026-08-24       --gross tests/data/2026-08-24 --withholding 0
uv run pytest tests/test_synthetic.py                                    # S4 now byte-checks the committed roots
uv run sweep.py specs/sweep_syn_2000.json --data tests/data/2026-08-24-syn-net15 --out results/sweep_syn_2000
uv run sweep.py specs/sweep_syn_full.json --data tests/data/2026-08-24-syn-net15 --out results/sweep_syn_full
uv run main.py --spec specs/syn_points.json      --data tests/data/2026-08-24-syn-net15 --json results/syn_points.json      --no-charts --quiet
uv run main.py --spec specs/syn_points.json      --data tests/data/2026-08-24-syn       --json results/syn_points_tr.json   --no-charts --quiet
uv run make_synthetic.py tests/data/2026-08-24-net15 --gross tests/data/2026-08-24 --withholding 0.15 --drag 0.0129 --out /tmp/syn-clo && \
uv run main.py --spec specs/syn_points.json --data /tmp/syn-clo --json results/syn_points_clo.json --no-charts --quiet
uv run make_synthetic.py tests/data/2026-08-24-net15 --gross tests/data/2026-08-24 --withholding 0.15 --drag 0.0413 --out /tmp/syn-chi && \
uv run main.py --spec specs/syn_points.json --data /tmp/syn-chi --json results/syn_points_chi.json --no-charts --quiet
uv run main.py --spec specs/syn_bridge_2012.json --data tests/data/2026-08-24-syn-net15 --json results/syn_bridge_2012.json --no-charts --quiet
```

Commit order: (1) generator + tests + docs, **without** roots (S4's byte check is
skipped when the roots are absent and the generator test runs on a temp build); (2)
the two roots, S4 armed; (3) the **pre-registration commit** — the five specs, the §10
kill conditions and the §11 predictions, before any lane runs; (4) artefacts; (5) the
verdict. Before reading anything else, confirm S9 through `syn_bridge_2012`'s BTAL twin
(0.86123626) and the four splice facts in the root README.

## 10. Read protocol and kill conditions — frozen at the pre-registration commit

A synthetic root is a **falsifier**. Nothing is adopted from these lanes; the only
outputs are flags on the coordinates the 2012 lanes chose, and a downgrade or an upgrade
of the standing caveat.

0. **The bridge first** (§7.5): S9 holds; the BIL-sleeve substitution cost on the real
   era is quoted once (drawdown and CAGR at both coordinates) and carried as the bias
   direction for everything below.
1. **K1 — feasibility.** Any grid point with full-window max drawdown < −50 % on
   either lane is **infeasible on that lane** and is flagged in `WINNING_STRATEGIES.md`'s
   successor (the winners file, when it exists) and in `notes/`. A coordinate within
   1 pp of the constraint on either side is "on the boundary" and is said so, with the
   `c`-bracket values from §7.4 beside it.
2. **Q1 — does the gate earn its keep in a bear?** Per (λ, σ, w_max): gate vs null on
   `robust_score`, full max drawdown, and the fit-window (2000–2007) and test-window
   (2008–2011) Calmar of §7.2. The 2012-lane finding was +0.145 robust and +6.9 pp of
   drawdown; the bear lanes say whether that is an era effect.
3. **Q2 — does the machine beat its benchmark where the benchmark was terrible?**
   Each gated point vs SPY and vs gated 50/50 on §7.2's full window: Calmar, CAGR, max
   drawdown, and the 2000 / 2001 / 2002 / 2008 / 2009 calendar years from §7.4.
   Pre-registered reading rule: **the machine is expected to lose more than SPY in the
   first leg of each bear (2000, 2008) and to win the grind (2001–02)** — the 2012-lane
   pattern (COVID vs 2022) transplanted; a first-leg win would be the surprise to
   distrust.
4. **Q3 — the plateau.** On §7.3: is the λ0.80 / σ0.20–0.30 / w_max 0.6–0.8 plateau still
   a plateau across 26 years — do the eight gated points sit within 0.10 of each other
   on `robust_score`, and does λ0.80 still beat λ0.94 at every (σ, w_max)? `rank_worst`
   now runs over ~43 windows including both bears.
5. **Q4 — the brackets.** §7.4's four runs: the gross-TR and the two `c` roots. Any
   conclusion above that flips under a bracket is not a conclusion.
6. **The R2 question, finally answerable for this machine.** From §7.2's `kind == "test"`
   rows: the gated points' 2008–2011 max drawdown against the null's and against SPY's
   (−55.4 %). Insurance or not, in a real bear, in points.
7. **Decision rule.** (a) If the winners' coordinate (0.80 / 0.20 / 0.8 / gate) is
   feasible on both lanes, beats SPY on §7.2's full-window Calmar with a shallower max
   drawdown, and its gate beats its null on both lanes' `robust_score`, the program-wide
   caveat is downgraded from "one era" to "**the BTAL sleeve is untested before 2011-09**"
   and the winners' documentation says so. (b) Any coordinate that fails K1 is marked
   "infeasible in the GFC on a cash sleeve" wherever it is quoted. (c) A gate that fails
   Q1 on either lane reopens the gate line with a *bear-first* spec — not here. (d) No
   parameter moves. Verdict: `notes/syn-verdict.md`, sections 0–7 plus residuals, every
   number from committed artefacts.

## 11. Pilot measurements — what to expect, and what would falsify it

A prototype generator (the §3 semantics, scratch code) built net15-convention roots at
`c` = 1.29 / 1.94 / 4.13 %/yr (the §2.4 offsets around the net15 fit), `c_b` = 0.093 %/yr,
`w = 0.15` on the bill, and ran eight strategies through `main.run_bundle` on full
windows only — no robustness windows, no ranks. Expectations, not findings.

**2000-01-03 → 2011-12-30, `c_mid`** (Calmar · CAGR · max DD · turnover; episodes:
dot-com · GFC · 2011; calendar years 2000 · 2001 · 2002 · 2008 · 2009):

| strategy | Calmar · CAGR · max DD · TO | dot-com · GFC · 2011 | 2000 · 2001 · 2002 · 2008 · 2009 |
|---|---|---|---|
| VT BIL σ0.30 w0.6 **gate** | 0.071 · +3.6 % · **−50.4 %** · 0.77 | −41.2 · −50.4 · −25.3 | −31.9 · −0.5 · +1.1 · −42.0 · +54.6 |
| VT BIL σ0.30 w0.6 no gate | −0.025 · −1.9 % · −77.3 % · 0.90 | −77.3 · · · · | −33.2 · −30.2 · −34.9 · −45.4 · +66.6 |
| VT BIL σ0.20 w0.8 **gate** | **0.105** · **+3.8 %** · **−35.9 %** · 1.36 | −27.3 · −35.9 · −18.1 | −20.8 · +0.7 · +1.1 · −29.1 · +35.7 |
| VT BIL σ0.20 w0.8 no gate | 0.010 · +0.6 % · −60.7 % · 1.48 | −60.7 · · · −18.1 | −21.7 · −19.6 · −23.6 · −31.9 · +43.1 |
| TQQQ buy-and-hold | −0.396 · −39.6 % · −100.0 % · 0.11 | −100.0 · · · · | −92.3 · −88.8 · −86.1 · −88.4 · +197.7 |
| TQQQ50/BIL50 gate | 0.020 · +1.3 % · −64.4 % · 0.30 | −64.4 · · · −22.9 | −48.1 · −3.9 · +0.8 · −46.5 · +57.6 |
| QQQ | −0.048 · −4.0 % · −82.9 % · 0.08 | −82.9 · · · · | −38.3 · −33.3 · −37.3 · −41.8 · +54.5 |
| SPY | 0.006 · +0.3 % · −55.4 % · 0.07 | −47.7 · −55.4 · · | −8.9 · −11.9 · −21.7 · −37.0 · +25.9 |

(`·` = below that arm's fifth-deepest drawdown; TQQQ buy-and-hold never recovers, so
its GFC is inside its dot-com.)

**2000-01-03 → 2026-08-24, `c_mid`**: gated σ0.30/w0.6 Calmar 0.302 · 15.2 % · −50.4 %;
gated σ0.20/w0.8 **0.367 · 13.2 % · −35.9 %**; ungated twins 0.169 / 0.199; gated 50/50
0.212 · 13.6 % · −64.4 %; QQQ 0.102 · 8.4 % · −82.9 %; SPY 0.145 · 8.0 % · −55.4 %.

**Brackets** (gated σ0.20/w0.8, 2000–2011, Calmar · CAGR · max DD): `c_lo` 0.111 · 4.0 %
· −35.7 %; `c_mid` 0.105 · 3.8 % · −35.9 %; `c_hi` 0.088 · 3.2 % · −36.2 %. Gated
σ0.30/w0.6: −50.2 / −50.4 / −50.8 %. Nothing else moves by more than 0.6 pp from `c_mid`.

**Bridge, 2012-01-03 → 2026-08-24 (real bars only)**: gated σ0.30/w0.6 BIL 0.7386 ·
25.93 % · −35.11 % · 0.89 vs BTAL 0.8612 · 23.82 % · −27.65 % · 0.88; gated σ0.20/w0.8
BIL 0.7991 · 21.66 % · −27.10 % · 1.80; TQQQ buy-and-hold 0.5293 · 43.23 % · −81.67 %.
Identical to four decimals between the gross-fitted and the net15-fitted pilot roots —
the no-contamination invariant, seen once before S9 pins it.

Predictions, each a falsifiable line for the verdict:

1. **The σ0.30/w_max 0.6 coordinate is infeasible on both lanes**: GFC max drawdown
   −50.4 % at `c_mid`, −50.2 % at `c_lo`, −50.8 % at `c_hi` — across the constraint at
   every drag. The 2012-lane regime coordinate would have breached the program's own
   constraint in 2008 on a cash sleeve. Falsified if its full-window max drawdown on
   §7.2 is above −50 %.
2. **The winners' coordinate σ0.20/w_max 0.8 is feasible on both lanes and clears
   §10.7(a)**: max drawdown −35.9 % vs SPY −55.4 %, CAGR +3.8 % vs +0.3 %, Calmar 0.105
   vs 0.006 on 2000–2011; gate vs null 0.105 vs 0.010. Falsified if any clause fails
   under `robust_score`.
3. **The gate is worth more in a bear than it was on the 2012 lane**: +0.095 Calmar and
   +25 drawdown points at σ0.20/w0.8, +0.096 and +27 points at σ0.30/w0.6 — against
   +0.145 and +6.9 on 2012–2026. Falsified if any gated point loses to its null on
   `robust_score` on either lane.
4. **The machine loses the first leg and wins the grind.** 2000: −20.8 % / −31.9 %
   against SPY −8.9 %; 2008: −29.1 % / −42.0 % against −37.0 % (the σ0.30 coordinate
   loses *more* than SPY in 2008); 2001–02: +0.7 / +1.1 % and −0.5 / +1.1 % against
   −11.9 / −21.7 %. The COVID-vs-2022 pattern, twice more. Falsified by a first-leg
   calendar-year win over SPY at either coordinate.
5. **Buy-and-hold 3× is annihilated, and the gated static is not a substitute**: TQQQ
   −99.95 % in the dot-com; gated 50/50 −64.4 % and +1.3 %/yr. VT is not a detail at
   3×. Falsified if gated 50/50 is feasible on §7.2.
6. **The plateau survives but tilts**: on §7.3 the eight gated points stay within 0.10
   of each other on `robust_score`, λ0.80 still beats λ0.94 at every (σ, w_max), and the
   σ0.20 points rank above the σ0.30 points — the opposite of the 2012 lane's
   full-Calmar ordering, because the bear lanes price drawdown. Falsified by a
   σ0.30 point above every σ0.20 point on `robust_score`.
7. **The brackets are inert**: no §10 flag flips between `c_lo`, `c_mid`, `c_hi` or the
   gross root; every gated number moves ≤ 0.7 pp CAGR and ≤ 0.6 pp drawdown. Falsified
   by any K1 flag or Q1/Q2 sign that differs across roots.
8. **The sleeve is the largest known bias, and it points one way**: BIL costs 7–8
   drawdown points against BTAL on the real era; on the bear era the machine's
   drawdown numbers are therefore an upper bound on what the incumbent (BTAL) would
   have printed wherever BTAL's anti-beta helped, and no bound where it hurt (2009's
   rebound). Not a prediction to falsify; a caveat to carry into every table.

## 12. Honest limitations

- **A synthetic 3× fund is a model, not a fund.** It has no price/NAV noise (17.7 bp/day
  in the real one), no creation/redemption frictions, no closure risk — ProShares
  launched TQQQ in 2010 after two leveraged-fund families had survived 2008; a fund
  that lost 94.6 % in the GFC and 99.95 % in the dot-com would have been reverse-split
  repeatedly, and some of its peers would have closed. The machine holding it through
  a −99.95 % never *held* it: it held ≤ w_max of it, resized monthly, gated below
  trend. That is the point of the lane, and it is still a model.
- **The financing leg is T-bill plus a constant**, and the constant is known to be wrong
  in exactly the era that matters: swap financing was LIBOR-based and the TED spread
  reached ~4.5 % in October 2008. The `c_hi` bracket (twice QLD's measured crisis
  widening) is the honest bound, not a point estimate; the pilot says it moves the
  gated machine's 2008 by 0.4 pp. Anyone who needs the crisis financing to the basis
  point needs a LIBOR/OIS series this repo does not carry.
- **QQQ's total-return export before 2010 is checked by structure, not against an
  external record**: zero dividends before 2003-12-24, plausible yields after, and the
  S10 spot check is an operator task. The dot-com stretch is dividend-free either way.
- **The cash sleeve at BIL is not the incumbent's sleeve.** §7.5 quantifies it on the
  real era; nothing quantifies it on the bear era, and the direction is stated in
  prediction 8.
- **Two bears is still n = 2**, and both are inside one 26-year window with one
  monetary regime (falling rates). The lanes turn "untested" into "tested twice"; they
  do not make the machine safe.
- **DTB3 is FRED data with the quarantine caveat** — used here as a build input, lagged,
  for an accrual and a financing cost, not as a signal; the `macro/` directory stays
  unloadable and the synthetic root does not copy it. If `MACRO_DATA_SPEC` ever
  standardises FRED ingestion, the generator should read through it.

## 13. Deliberately not in scope

Synthetic BTAL (a long/short anti-beta sleeve has no daily proxy the repo can validate;
the AQR BAB factor is monthly and academic — a different data class and a different
spec). Synthetic DBMF / KMLM (SAFE_SWAP §9: extending managed-futures ETFs backward is
a research project). Rotation-universe proxies (EFA / IEF / TLT / DBC / VNQ before
2002–2006 need mutual-fund NAV series — a new export class; the rotation catalog is
closed and R2's resolution for those strategies waits on a reason to reopen it). SPXTR
/ a synthetic UPRO (the incumbent does not trade S&P leverage; SPY is real from 1993 and
suffices as the benchmark). Re-fitting the plateau on the bear lanes (§10.7(d) — a
coordinate that fails is flagged; a bear-first re-fit is its own spec with its own
holdout design). Fixing the XNDX export. A time-varying `cash_yield` (the BIL sleeve
*is* the time-varying cash; the constant stays for uninvested residue).

## 14. Acceptance checklist

- [ ] `make_synthetic.py`: §3 semantics, per-root fit, `--withholding` with the parent guard, fitted constants printed and written, `--drag` / `--bill-drag` / `--out` / `--force`; deterministic
- [ ] Roots `tests/data/2026-08-24-syn` and `-syn-net15` committed; README with fitted constants, splice facts, validation numbers, S10 spot check
- [ ] Tests S1–S10 green from a fresh clone; `every_strategy` skips `syn_`; suite count > 806; the SMA-parity fixture count still 20 (the spliced files carry no SMA header, so the `rglob` does not collect them — S4 asserts it)
- [ ] Docs per §8, including the XNDX note
- [ ] **Pre-registration commit**: five specs (§7.2–§7.5), §10 kill conditions, §11 predictions — before any run
- [ ] Artefacts: two sweep directories, five bundle JSONs (`syn_points`, `_tr`, `_clo`, `_chi`, `syn_bridge_2012`), committed together; S9 confirmed in the verdict
- [ ] `notes/syn-verdict.md` per §10; the standing caveat updated per §10.7 wherever it is quoted (`docs/HANDOFF_COMPOSITION.md` §7, the winners' documentation)
- [ ] No engine file touched; `SCHEMA_VERSION` 4

## 15. Errata (found during implementation)

1. **§3's default output name contradicts §4's.** "Root layout (`PARENT` basename +
   `-syn`)" makes the net root `2026-08-24-net15-syn`, but §4, §7 and §9 all name it
   `tests/data/2026-08-24-syn-net15`. Resolved in favour of the explicit name, which
   appears six times against the rule's once: `make_synthetic.default_out` inserts
   `-syn` before the withholding suffix, so a root reads snapshot, then extension,
   then convention. Both spellings contain `-net`, so `tests/test_indicators.py`'s
   `-net` exclusion is unaffected either way.

2. **"Max cumulative deviation" needed a definition.** §2.3's table reports it but
   does not say in which space. Three readings differ materially on the full TQQQ
   overlap: the level ratio gives 9.56 %, the exact log residual against the fitted
   series 9.13 %, and the *linearised* log residual — `max |Σ (resid_t + c·d_t/365)|`,
   the cumulative deviation of the same series whose mean-residual defines `c` — gives
   9.138 %. Only the third reproduces the table across all five windows (9.14 / 1.48 /
   5.19 / 1.45 / 0.91 measured as 9.138 / 1.480 / 5.189 / 1.454 / 0.913), and it is
   also the one for which §2.3's "`cum_end` 0" claim is exactly true. It is what
   `make_synthetic._fit` computes and what S1's `≤ 0.095` bound is stated against; the
   level reading would breach that bound. Reported per root: the `-syn-net15` root
   fits 9.57 % on its own series, which is not pinned anywhere and is not a defect —
   §2.3's table and S1's bound are gross-root numbers.

3. **S9's CAGR is quoted to one digit too few.** "CAGR 0.2381710" rounds from
   0.23817105, which at 7 decimals is 0.2381711. The test pins the committed
   artefact's 8-decimal value, 0.23817105; Calmar and max drawdown are unaffected.

4. **§14's "suite count > 806" lands in two steps.** The generator commit takes it to
   857 with the 19 root-dependent pins skipped (§9's own instruction: S4's byte check
   cannot run before the roots exist); the roots commit arms them, and the suite is
   876 with nothing skipped.

5. **§14's "five specs" is four.** §7.2–§7.5 name four spec files
   (`sweep_syn_2000`, `sweep_syn_full`, `syn_points`, `syn_bridge_2012`); the five is
   the count of *bundle artefacts*, because `syn_points.json` is run on four roots.
   §9's run protocol already lists four spec files, and the checklist's next line
   ("five bundle JSONs") is correct.

6. **§7.3's full lane is 47 windows, not ~46.** `--dry-run` prints 20 × 47 = 940 runs
   against §7.6's 920: `full` + `fit` + `test` + 44 five-year sensitivity windows
   starting every 6 months from 2000-01-03 and ending by 2026-08-24. §7.2 is exactly
   as predicted, 20 × 21 = 420. No reading changes; the sensitivity set is one window
   larger than the estimate.

7. **Polygon cannot supply S10's published amounts.** Its dividend reference data
   starts 2011-03-18 for QQQ — after the trust's first distribution (2003-12-24), so
   `dividends/QQQ.parquet` could not check a single pre-inception ex-date.
   `fetch_dividends.py` now requests from 1999 explicitly and prints each symbol's
   earliest ex-date, making the boundary a measured fact; `extend_dividends.py` merges
   the earlier record from `dividends/pre_polygon/` into the parquet with a `source`
   column. All 24 implied 2003–2010 distributions match the published amounts to five
   decimals, every fiscal-year sum reconciles to the trust's audited Financial
   Highlights, and 2004-12-17's $0.37858 is quoted verbatim in the N-30B-2 for the
   year ended 2004-09-30 — a $3.00 Microsoft special dividend passing through, which
   is why §2.2's 2004 yield is 0.95 % against neighbours near 0.3 %.

8. **§10 K1's "the winners file, when it exists"** — it exists:
   `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`. (EPISODE_SPEC §7.2.)
