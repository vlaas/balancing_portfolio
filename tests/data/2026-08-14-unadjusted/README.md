# Unadjusted snapshot — 2026-08-14-unadjusted

The first frozen snapshot: TradingView daily exports of six symbols with
**Adjust data for dividends: OFF**, so every `<SYM>.csv` is a price-only
(unadjusted) series and a run on this root ignores distributions. It is the
one root whose top level is dividends-OFF; the `-unadjusted` suffix says so
(DATA_LAYOUT_SPEC §4). Until DATA_LAYOUT_SPEC these files sat flat in
`tests/data/`; the move changed no byte.

| symbol | first bar | last bar |
|---|---|---|
| BTAL | 2011-09-13 | 2026-08-14 |
| DBMF | 2019-05-08 | 2026-08-17 |
| KMLM | 2020-12-18 | 2026-08-17 |
| QQQ | 1999-03-10 | 2026-08-14 |
| SPY | 1993-01-29 | 2026-08-14 |
| TQQQ | 2010-02-11 | 2026-08-14 |

The files keep the export's Pine overlay columns
(`time,open,high,low,close,SMA50,SMA100,SMA200,SMA15,Volume`) and stay in the
scope of `tests/test_indicators.py::test_sma_matches_the_tradingview_column`.

Kept byte-identical as the gross-of-distribution regression anchor: `GOLDEN`
and `COST_GOLDEN` in `tests/test_main.py`, and every test whose `GOLDEN_DIR`
points here. Price-only numbers are legacy regression artefacts, never decision
numbers. The closes match the `unadjusted/` files of `tests/data/2026-08-20/`
on every shared date (max diff 0.0; that snapshot's README).
