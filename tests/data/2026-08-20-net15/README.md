# Net total-return snapshot — 2026-08-20-net15

Derived from the frozen `2026-08-20` snapshot by `make_net_tr.py` (NET_TR_SPEC §2–§3) at withholding w = 0.15: each distribution jump
factor k is replaced by k_net = w + (1 - w) * k, so every ex-date
reinvests (1 - w) * D instead of D; flat (pure price movement) rows
scale by the constant suffix product C only, and the net series anchors
to the parent at the last bar. `<SYM>.csv` carries columns `time,close`
only; `price/<SYM>.csv` is byte-copied from the parent. Step
classification (NET_TR_SPEC §2.1): FLAT_MAX = 5e-06,
JUMP_MIN = 2e-05, TAU = 1e-06.

| symbol | jumps | y gross | y net |
|---|---|---|---|
| BTAL | 8 | 1.07%/yr | 0.91%/yr |
| DBMF | 18 | 5.81%/yr | 4.92%/yr |
| KMLM | 4 | 4.38%/yr | 3.70%/yr |
| QQQ | 88 | 0.62%/yr | 0.53%/yr |
| SPY | 135 | 1.79%/yr | 1.52%/yr |
| TQQQ | 21 | 0.31%/yr | 0.26%/yr |
| VIX | index | — | — |
| VIX3M | index | — | — |
