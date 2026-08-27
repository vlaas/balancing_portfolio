# Market data

Daily bars exported from **TradingView**, in three file classes
(ROTATION_SPEC §3.2–§3.3):

| class | files | loader reads |
|---|---|---|
| **Paired ETF** (48) | `<SYM>.csv` — the **dividend-adjusted (total-return) export**, the traded series; `price/<SYM>.csv` — the unadjusted export from the **same session**, reference only | `<SYM>.csv` |
| **Single-series index** (SPX, XNDX, VIX, VIX3M) | `<SYM>.csv` only — indices have no adjustment toggle (XNDX embeds dividends by construction, SPX excludes them; VIX/VIX3M are cash vol indices), so no `price/` twin. XNDX before 2010-01-04 is stamped one day late and must not be used as a reference there (SYNTHETIC_HISTORY_SPEC §2.6) | `<SYM>.csv`, signal-only |
| **Macro** (`macro/`: UNRATE, RRSFS, INDPRO, DTB3) | quarantined FRED series — see "Macro series" below | **never** |

The loader resolves every read — traded, `extra`, or indicator `inputs` —
against `data/<SYM>.csv` and never looks inside `price/` or `macro/`; the
`price/` twin exists so the adjustment is verifiable (see "The adjustment
ratio" below).

## Layout

Both files of a pair use the same export layout:

```
time,open,high,low,close,Volume
1993-01-29,24.13552346,24.13562776,24.01541892,24.11861661,1003200.0
```

`time` is `YYYY-MM-DD`, one row per trading day, ascending and unique. The
paired files of a symbol have identical `time` columns (asserted by the tests);
files across symbols may end on different dates.

## What the simulator reads

**Only `time` and `close`, from `<SYM>.csv`.** `prices.py::_read_symbol`
whitelists those two columns; everything else in the file is ignored at
runtime. The engine trades and values on the total-return close, so results
include distributions reinvested at the ex-date close (gross of withholding).

## Where the SMA verification fixture went

Exports up to the 2026-08 batch carried Pine overlay columns
(`SMA50,SMA100,SMA200,SMA15`) proving `indicators.sma(n)` reproduces
TradingView. That proof is **permanently discharged by the frozen snapshots**,
which keep their SMA columns and stay in scope of
`tests/test_indicators.py::test_sma_matches_the_tradingview_column` — the
test collects only files whose header carries the columns, with the count
pinned so a silent scope shrink is loud. The overlay is no longer part of the
export procedure (a two-pass export of 48 paired symbols with a chart overlay
attached per pass is exactly the operator burden that produces mismatched
sessions); live-data guard duty transferred to the pair invariants and
per-symbol yield bands of `tests/test_total_return.py` (ROTATION_SPEC
§3.1/§3.5). The overlay's Pine source survives in git history (this README
before the 2026-08 batch).

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

Measured tolerances are pinned per snapshot: `tests/data/2026-08-20/README.md`
(SMA parity ≤ 2.0e-12, implied distributions within $0.000011 of published
amounts) and `tests/data/2026-08-24/README.md` (48 pairs: flat-segment noise
≤ 4.3e-8, smallest genuine jump 1.247e-5, the full yield table behind the
live-pair bands).

## Export settings

Two passes per symbol, same chart, same session:

1. Chart settings → **Adjust data for dividends: ON** → *Export chart data…* →
   `data/<SYM>.csv`.
2. Toggle **OFF** → export again → `data/price/<SYM>.csv`.
3. Toggle back **ON**, so the chart's resting state matches the traded series.

- Symbol: the ETF's primary listing; chart interval **1D**.
- No indicator on the chart (the Pine SMA overlay left the procedure with the
  2026-08 batch — see "Where the SMA verification fixture went").
- Exported via *Chart → Export chart data…*, ISO dates, `.` decimal
  separator, `,` field separator.
- The full available history is exported; files therefore start at different
  dates (SPY 1993, QQQ 1999, TQQQ 2010, BTAL 2011, DBMF 2019, KMLM 2020) and may
  end on different dates.

## Macro series (`macro/`) — quarantined, never loaded

`UNRATE.csv`, `RRSFS.csv`, `INDPRO.csv`, `DTB3.csv` are FRED series, **not
price series**, and the loader does not and must not read `macro/`.
UNRATE/RRSFS/INDPRO are monthly observations stamped at the observation month
(UNRATE from 1948-01-01) whose values are published ~1–5 weeks *after* that
stamp and then revised; DTB3 is daily on its own calendar. Loading any of them
through `load_prices` would forward-fill a value from a date on which it was
not yet knowable — a silent look-ahead in every macro-gated backtest. They
stay inert until a `MACRO_DATA_SPEC` pins the availability-date shift, the
monthly-to-daily carry rule and the revised-vintage caveat (ROTATION_SPEC
§3.3); GTT/LAA remain blocked on that spec.

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
- `tests/data/2026-08-24/` — the ROTATION_SPEC Phase 0 snapshot: the full
  2026-08 batch (48 pairs, four single-series indices, `macro/` carried for
  provenance), no SMA columns.
- `tests/data/2026-08-24-net15/` — its net-of-withholding derivative, the
  **decision series for all rotation runs**. `macro/` is deliberately absent
  (`make_net_tr.py` globs the root only).
- `tests/data/2026-08-24-syn/`, `tests/data/2026-08-24-syn-net15/` — the
  **synthetic-extended** derivatives of the two above, generated by
  `make_synthetic.py` (`docs/SYNTHETIC_HISTORY_SPEC.md`). See below.

Live `data/` runs the bundle-loading smoke test plus the live-pair lane of
`tests/test_total_return.py` — pair invariants and the committed per-symbol
implied-yield bands over all 48 pairs — so a bad refresh fails the suite the
day it lands.

## Synthetic roots (`-syn`, `-syn-net15`)

`make_synthetic.py` extends a frozen root backward past its funds' inceptions
(`docs/SYNTHETIC_HISTORY_SPEC.md`). A daily-rebalanced 3× fund is modelled as
`r = 3·s − 2·y·d/360 − c·d/365` on QQQ's real total return, and a T-bill fund
as `r = (1−w)·y·d/360 − c_b·d/365`, with `y` the 3-month bill (`macro/DTB3`)
forward-filled onto the bar calendar and lagged one row and `d` calendar days
since the previous bar. Each constant is fitted on the parent's own real
segment, so a root's synthetic bars are in its own withholding convention.

The modelled series is **spliced strictly before the real first bar** and
scaled so the two meet there multiplicatively, so TQQQ reaches 1999-03-10 and
BIL 1993-01-29 while the real segments (from 2010-02-11 and 2007-05-30) are
copied value-for-value. `TQQQ.csv` and `BIL.csv` carry a third column,
`source ∈ {synthetic, real}` — the loader whitelists `time,close` and ignores
it. `price/TQQQ.csv` and `price/BIL.csv` are deliberately absent: a modelled
segment has no unadjusted twin, so no pair test runs on a synthetic root.
`macro/` is not copied.

**The no-contamination invariant**: any run whose window starts on or after
the real inception reads only real bars and reproduces the parent root's
numbers exactly, bit for bit.

**A synthetic root is a falsifier, never a fitting lane**: no parameter is
adopted from a window that contains synthetic bars. It exists to test the
machine chosen on 2012–2026 against the two bears that era does not contain.

## Index series (SPX, XNDX, VIX, VIX3M)

Single-series indices have no adjustment toggle and hence no `price/` twin;
`make_net_tr.py` byte-copies them into a net snapshot as
`| SYM | index | — | — |`. All four are **signal symbols**, never traded.
`XNDX` (Nasdaq-100 TR) starts 2006-11-08 on TradingView; `SPX` excludes
dividends by construction and must never seed a TR sim. **XNDX rows before
2010-01-04 are stamped one trading day late relative to every ETF export**
(same-day correlation with QQQ ≈ 0, next-day 0.97–0.99;
SYNTHETIC_HISTORY_SPEC §2.6): the file is signal-only and no strategy reads
it, but it must not be used as a reference before 2010. Shifting the stretch
back one row still leaves a 58.6 bp daily residual, so it is not a clean lag
and the stretch is unusable rather than repairable here. `VIX.csv` and
`VIX3M.csv` are cash volatility indices; VIX carries values on US market
holidays that VIX3M (and every traded symbol) lacks — TradingView artefacts,
kept out of every rolling window by the cross-symbol loader's intersection
rule (`docs/REGIME_SPEC.md` §2–§3). The 2026-08 refresh revised VIX history:
1,285 closes changed against the pre-batch export (all since 2021-05-21, four
beyond 0.05, worst 0.28 on 2023-06-07); VIX3M was untouched
(ROTATION_SPEC §3.4 errata). `regime_report.py` is the standing tool for
reading a signal like this on its own calendar before running any lane.
