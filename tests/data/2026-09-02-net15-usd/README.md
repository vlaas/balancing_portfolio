# USD-converted snapshot — 2026-09-02-net15-usd

Derived from the frozen `2026-09-02-net15` snapshot by `make_usd.py`
(EU_SUBSTITUTE_SPEC §3.5): each mapped symbol's close is multiplied by
the close of the FX bar that ends on its date and by the line's scale
(1 for a EUR line, 0.01 for a GBX line quoted in pence). TradingView
stamps an FX_IDC daily bar by its 17:00 New York open, so the bar that
closes on date D is labelled D − 1: the join takes the latest FX bar
labelled strictly before the symbol's date (read from the parent root),
carried across FX holidays — a bar whose FX bar is older than the
previous calendar day is counted as stale below. That close is ~5.5 h
after the London close, the same-day offset the spec accepts; the bar
labelled D would close on D + 1. A converted `<SYM>.csv` carries `time,close`
only and has no `price/` twin — a converted series has no unadjusted
twin in its trading currency; the parent keeps the original. Every
other file, `price/` twins included, is byte-copied from the parent.

| symbol | fx | scale | bars | stale FX bars | first rate | last rate |
|---|---|---|---|---|---|---|
| DBMF_EU | EURUSD | 1 | 335 | 0 | 1.09209 | 1.15877 |
| LQQ | EURUSD | 1 | 5134 | 1 | 1.2551 | 1.15877 |
| MVEA | EURUSD | 1 | 1621 | 0 | 1.07773 | 1.15877 |
| XSPS | GBPUSD | 0.01 | 4623 | 0 | 1.946 | 1.3481 |
