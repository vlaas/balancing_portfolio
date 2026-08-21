# Market data

Daily bars exported from **TradingView**, two CSVs per symbol:

- `<SYM>.csv` — the **dividend-adjusted (total-return) export**. This is the
  traded series: the close the loader reads and every indicator is computed on.
- `price/<SYM>.csv` — the unadjusted export from the **same session**, reference
  only. The loader never looks inside `price/`; the pair exists so the
  adjustment is verifiable (see "The adjustment ratio" below).

## Layout

Both files use the same export layout:

```
time,open,high,low,close,SMA50,SMA100,SMA200,SMA15,Volume
2011-09-13,21.73271823,21.73271823,20.6162531,21.09352063,,,,,10500
```

`time` is `YYYY-MM-DD`, one row per trading day, ascending and unique. The
paired files of a symbol have identical `time` columns (asserted by the tests);
files across symbols may end on different dates.

## What the simulator reads

**Only `time` and `close`, from `<SYM>.csv`.** `prices.py::_read_symbol`
whitelists those two columns; everything else in the file is ignored at
runtime. The engine trades and values on the total-return close, so results
include distributions reinvested at the ex-date close (gross of withholding).

## What the `SMA*` columns are for

They are a **verification fixture, not an input.** Indicators are computed in
Python (`indicators.py`) and declared per strategy. The exported `SMA15`, `SMA50`,
`SMA100` and `SMA200` columns are the independent reference that proves the Python
implementation matches TradingView:
`tests/test_indicators.py::test_sma_matches_the_tradingview_column` compares
`indicators.sma(n)` against column `SMA{n}` in every CSV — adjusted and
`price/` alike, since Pine's `close` follows the chart's adjustment setting —
for `n ∈ {15, 50, 100, 200}`, requiring agreement to `1e-9` and an identical
null count. Measured agreement is ~2e-12. That is why the dividend toggle must
be set **before** each export: the indicator columns and the close column of
one file must describe the same series.

Because the comparison happens *within* a file, it stays valid when the export
is refreshed. Keep the `SMA*` columns in future exports — dropping them would
silently retire the check.

`Volume` is exported but unused.

## The adjustment ratio

For a paired symbol let `R_t = adjusted_t / price_t`. Under TradingView's
multiplicative back-adjustment (`tests/test_total_return.py` asserts all of
this, on this directory as well as on the frozen snapshot):

- `0 < R ≤ 1` everywhere and `R` is non-decreasing — flat between ex-dates,
  jumping up at each one.
- `R = 1` on the last bar: the adjusted series is anchored at the latest price.
- Splits are adjusted identically in both exports (the toggle controls
  dividends only), so `R` is split-invariant.
- The implied per-share distribution at a jump,
  `D = price_{t−1} · (1 − R_{t−1}/R_t)`, matches published amounts — the pinned
  spot checks sit in `tests/test_total_return.py` with their sources. Amounts
  are stated in the current split basis: TQQQ split 2:1 on 2025-11-20, so
  earlier published amounts are twice today's per-share figures.
- The cumulative implied yield `y = −ln(R_first) / years` per symbol sits in
  the per-symbol bands of the tests; `y ≈ 0` means the toggle was off — the
  most likely operator error, and a loud test failure.

**An adjusted export is not append-stable**: every new ex-date rescales the
entire history, and integer shares plus fixed dollar contributions are not
scale-invariant, so a run on live `data/` can move in the cents between
refreshes even over an identical window. Pinned numbers only ever come from
frozen snapshots, which is already the rule.

**Live signal note**: to reproduce a signal on a TradingView chart, turn
dividend adjustment **on** — the chart then shows the series the simulator
trades.

Measured on the 2026-08-20 export (pinned in `tests/data/2026-08-20/README.md`):
flat-segment noise in `ln R` ≤ 4.3e-8, SMA parity ≤ 2.0e-12, implied
distributions within $0.000011 of published amounts.

## Export settings

Two passes per symbol, same chart, same session:

1. Chart settings → **Adjust data for dividends: ON** → *Export chart data…* →
   `data/<SYM>.csv`.
2. Toggle **OFF** → export again → `data/price/<SYM>.csv`.
3. Toggle back **ON**, so the chart's resting state matches the traded series.

- Symbol: the ETF's primary listing; chart interval **1D**.
- One indicator on the chart: *SMAs (50,100,200,15) by Veta* (source below), all four
  SMAs enabled, source `close`, lengths 50 / 100 / 200 / 15 — the plot order, and so the
  column order in the export.
- Exported via *Chart → Export chart data…*, "Chart data" with visible indicator
  columns, ISO dates, `.` decimal separator, `,` field separator.
- The full available history is exported; files therefore start at different
  dates (SPY 1993, QQQ 1999, TQQQ 2010, BTAL 2011, DBMF 2019, KMLM 2020) and may
  end on different dates.

### Pine script

Pine requires `plot()` titles to be compile-time constants, so the column header
(`TITLE_n`) and the length it describes (`input.int` default) are two separate
declarations that must be edited **together** — the script says so where they sit.
Nothing in Pine enforces the pairing, and changing a length on the chart without
touching the title would export a mislabelled column. That is precisely what T1
catches: it compares `indicators.sma(n)` against column `SMA{n}`, so a header that
disagrees with its length fails the suite loudly rather than silently poisoning a
backtest.

```pine
//@version=6
// Four SMAs in a single indicator slot. v6 port of "SMAs (10,50,100,200) by Veta".

indicator(title = "SMAs (50,100,200,15) by Veta", shorttitle = "SMAs", overlay = true)

// ── Plot titles ───────────────────────────────────────────────────────────────
// plot() titles must be compile-time constants in Pine, so they cannot be
// driven by inputs. These strings are the column headers in exported chart
// data — edit them together with the default lengths in the inputs below.
string TITLE_1 = "SMA50"
string TITLE_2 = "SMA100"
string TITLE_3 = "SMA200"
string TITLE_4 = "SMA15"

// ── Inputs ────────────────────────────────────────────────────────────────────
string G1 = "1st SMA"
string G2 = "2nd SMA"
string G3 = "3rd SMA"
string G4 = "4th SMA"

bool  show1 = input.bool(true,     title = "Enable", inline = "sma1", group = G1)
int   len1  = input.int(50,        title = "Length", minval = 1, inline = "sma1", group = G1)
float src1  = input.source(close,  title = "Source", inline = "sma1", group = G1)

bool  show2 = input.bool(true,     title = "Enable", inline = "sma2", group = G2)
int   len2  = input.int(100,        title = "Length", minval = 1, inline = "sma2", group = G2)
float src2  = input.source(close,  title = "Source", inline = "sma2", group = G2)

bool  show3 = input.bool(true,     title = "Enable", inline = "sma3", group = G3)
int   len3  = input.int(200,       title = "Length", minval = 1, inline = "sma3", group = G3)
float src3  = input.source(close,  title = "Source", inline = "sma3", group = G3)

bool  show4 = input.bool(true,     title = "Enable", inline = "sma4", group = G4)
int   len4  = input.int(15,       title = "Length", minval = 1, inline = "sma4", group = G4)
float src4  = input.source(close,  title = "Source", inline = "sma4", group = G4)

// ── Calculations ──────────────────────────────────────────────────────────────
float sma1 = ta.sma(src1, len1)
float sma2 = ta.sma(src2, len2)
float sma3 = ta.sma(src3, len3)
float sma4 = ta.sma(src4, len4)

// ── Plots ─────────────────────────────────────────────────────────────────────
plot(show1 ? sma1 : na, title = TITLE_1, color = color.new(color.green,  50), linewidth = 3)
plot(show2 ? sma2 : na, title = TITLE_2, color = color.new(color.teal,   50), linewidth = 4)
plot(show3 ? sma3 : na, title = TITLE_3, color = color.new(color.blue,   50), linewidth = 5)
plot(show4 ? sma4 : na, title = TITLE_4, color = color.new(color.purple, 50), linewidth = 6)
```

## Frozen snapshots

Every test that asserts a number reads from a frozen snapshot under
`tests/data/`, so refreshing `data/` can never move a pinned result. Snapshots
are **append-only** — never overwrite one; add `tests/data/<newdate>/` for a
new one, where `<newdate>` is the last bar of its TQQQ export.

- `tests/data/*.csv` — the flat 2026-08-14 **price-only** snapshot, kept
  byte-identical as the gross-of-distribution regression anchor (`GOLDEN`,
  `COST_GOLDEN`, committed sweep artefacts).
- `tests/data/2026-08-20/` — the first **total-return** snapshot: both series,
  copied verbatim from the export, plus a README pinning the measured
  tolerances. A dated snapshot holds `<SYM>.csv` (adjusted) and
  `price/<SYM>.csv`; if a same-date price-only snapshot is ever needed,
  suffix the directory `-price`.
- `tests/data/2026-08-20-net15/` — the **net-of-withholding** derivative of
  the snapshot above, generated by `make_net_tr.py` (`docs/NET_TR_SPEC.md`):
  each distribution jump reinvests `(1−w)·D` at `w = 0.15`, flat rows are
  untouched. `<SYM>.csv` carries `time,close` only; `price/` is byte-copied
  from the parent. This is the **decision series**; live `data/` stays gross —
  a net twin of any root is one invocation away
  (`uv run make_net_tr.py <ROOT>`).

Live `data/` runs the bundle-loading smoke test plus the structural
total-return invariants of `tests/test_total_return.py`, none of which make
numeric claims — a bad refresh fails the suite the day it lands.
