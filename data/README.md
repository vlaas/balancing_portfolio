# Price data

Daily bars exported from **TradingView**, one CSV per symbol, named `<SYM>.csv`.

## Layout

```
time,open,high,low,close,SMA50,SMA100,SMA200,SMA15,Volume
2011-09-13,25.5,25.5,24.19,24.75,,,,,10500
```

`time` is `YYYY-MM-DD`, one row per trading day, ascending and unique.

## What the simulator reads

**Only `time` and `close`.** `prices.py::_read_symbol` whitelists those two
columns; everything else in the file is ignored at runtime. The engine trades and
values on close, so no other price field has a meaning here.

## What the `SMA*` columns are for

They are a **verification fixture, not an input.** Indicators are computed in
Python (`indicators.py`) and declared per strategy. The exported `SMA15`, `SMA50`,
`SMA100` and `SMA200` columns are the independent reference that proves the Python
implementation matches TradingView:
`tests/test_indicators.py::test_sma_matches_the_tradingview_column` compares
`indicators.sma(n)` against column `SMA{n}` in every CSV, for
`n ∈ {15, 50, 100, 200}`, requiring agreement to `1e-9` and an identical null
count. Measured agreement is ~2e-12.

Because the comparison happens *within* a file, it stays valid when the export is
refreshed. Keep the `SMA*` columns in future exports — dropping them would
silently retire the check.

`Volume` is exported but unused.

## Export settings

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

## Frozen snapshot

`tests/data/` holds a byte-identical copy of this directory, taken at the
2026-08-14 export. Every test that asserts a number reads from there, so
refreshing `data/` can never move a pinned result. **The snapshot is
append-only** — never overwrite it; add `tests/data/<newdate>/` if a second one
is ever needed. Live `data/` gets exactly one test
(`test_every_bundle_loads_from_the_live_export`), which makes no numeric claims.
