# Frozen total-return snapshot — 2026-08-20

TradingView two-pass export taken 2026-08-21, last bar 2026-08-20 on all six
symbols. `<SYM>.csv` was exported with **Adjust data for dividends: ON** (the
traded, total-return series); `price/<SYM>.csv` with the toggle **OFF**, same
chart and session, identical date columns per symbol. Layout and indicator
settings as `data/README.md`. Append-only, like every snapshot.

Measured on this snapshot (TOTAL_RETURN_SPEC §4/§7; test constants are pinned
one order above the measurement):

- Flat-segment noise in `ln R` (`R = adjusted / price`): max monotonicity
  violation 4.3e-8 (TQQQ; every other symbol ≤ 7.1e-10) → `TAU = 1e-6`.
- `R_last = 1` exactly (0.0) on all six symbols; no bar with `R > 1`.
- SMA/TV parity max abs diff: 1.3e-12 on adjusted files, 2.0e-12 on `price/`
  files → the 1e-9 tolerance in `tests/test_indicators.py` holds unchanged,
  no separate lane for adjusted files.
- Implied cumulative distribution yields `y = −ln(R_first) / years`:
  TQQQ 0.31%/yr, BTAL 1.07%/yr, QQQ 0.62%/yr, SPY 1.79%/yr, DBMF 5.81%/yr,
  KMLM 4.38%/yr. **BTAL measures 1.07%/yr against the spec's assumed ≈3%/yr**
  (only 8 distributions ever, none 2013–2017; each verifies exactly against
  Polygon records) — its T2 band floor is 0.008 instead of the spec's 0.015,
  recorded in the spec errata.
- Implied per-share distributions at the twelve T3 ex-dates match Polygon
  records within $0.000011 → tolerance $0.0001. TQQQ split 2:1 on 2025-11-20,
  so published amounts with earlier ex-dates are in pre-split units (exactly
  half in today's basis); the T3 entries use post-split ex-dates only.
- `price/` closes are identical (max diff 0.0) to the flat `tests/data/`
  snapshot on every shared date ≤ 2026-08-14, all six symbols — TradingView
  revised no history, so the calendars T6 pins and the goldens T7 compares
  across snapshots sit on identical price data.
- T5 on the matched window (2017-01-03..2026-08-14, QQQ, rebalance days):
  1 of 115 SMA200 gate states differs from the flat snapshot (2019-05-31);
  max EWMA94 vol delta 1.66% relative.

`VIX.csv` and `VIX3M.csv` (added at the REGIME_SPEC baseline, verbatim from
`data/` at `184f02b`) are cash index series: no distributions, so no `price/`
twin — `make_net_tr.py` byte-copies them into the net snapshot. VIX carries
values on 58 US market holidays that VIX3M lacks (22 since 2012, none on any
traded symbol's calendar); they are TradingView artefacts, not observations,
and the cross-symbol loader's intersection rule keeps them out of every
rolling window. Last bar 2026-08-21, one day past TQQQ's — harmless, because
extra symbols never extend the traded calendar.
