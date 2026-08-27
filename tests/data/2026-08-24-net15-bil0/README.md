# Net total-return snapshot — 2026-08-24-net15-bil0

Derived from the frozen `2026-08-24` snapshot by `make_net_tr.py` (NET_TR_SPEC §2–§3) at withholding w = 0.15: each distribution jump
factor k is replaced by k_net = w + (1 - w) * k, so every ex-date
reinvests (1 - w) * D instead of D; flat (pure price movement) rows
scale by the constant suffix product C only, and the net series anchors
to the parent at the last bar. `<SYM>.csv` carries columns `time,close`
only; `price/<SYM>.csv` is byte-copied from the parent. Step
classification (NET_TR_SPEC §2.1): FLAT_MAX = 5e-06,
JUMP_MIN = 1e-05, TAU = 1e-06.

Per-symbol rate override (CASH_SLEEVE_SPEC §10.5): BIL at w = 0. The flat
convention is a modelling choice, not a fact; BIL's income is US
Treasury interest, the clearest §871(k) interest-related-dividend case
there is, so its true NRA withholding is plausibly ~0%. This snapshot
exists to break a tie inside the bias band, not to replace the flat
root — a decision run still uses the flat one unless it says otherwise.

| symbol | jumps | y gross | y net |
|---|---|---|---|
| ACWX | 39 | 2.59%/yr | 2.20%/yr |
| AGG | 274 | 3.19%/yr | 2.71%/yr |
| AVUV | 27 | 1.58%/yr | 1.34%/yr |
| BIL | 125 | 1.39%/yr | 1.39%/yr | w = 0 |
| BND | 232 | 3.16%/yr | 2.68%/yr |
| BTAL | 8 | 1.07%/yr | 0.91%/yr |
| BWX | 171 | 1.45%/yr | 1.23%/yr |
| DBC | 9 | 1.13%/yr | 0.96%/yr |
| DBMF | 18 | 5.80%/yr | 4.91%/yr |
| EDV | 75 | 4.85%/yr | 4.11%/yr |
| EEM | 47 | 1.90%/yr | 1.61%/yr |
| EFA | 46 | 2.67%/yr | 2.27%/yr |
| EWJ | 48 | 1.31%/yr | 1.11%/yr |
| GDE | 8 | 3.28%/yr | 2.78%/yr |
| GLD | 0 | -0.00%/yr | -0.00%/yr |
| HYG | 232 | 6.23%/yr | 5.29%/yr |
| IEF | 288 | 2.81%/yr | 2.39%/yr |
| IWM | 105 | 1.17%/yr | 1.00%/yr |
| IWN | 104 | 1.67%/yr | 1.42%/yr |
| KMLM | 4 | 4.37%/yr | 3.69%/yr |
| LQD | 288 | 4.13%/yr | 3.51%/yr |
| NTSE | 22 | 2.85%/yr | 2.42%/yr |
| NTSI | 23 | 2.71%/yr | 2.30%/yr |
| NTSX | 34 | 1.20%/yr | 1.02%/yr |
| PDBC | 11 | 6.85%/yr | 5.74%/yr |
| QLD | 32 | 0.68%/yr | 0.58%/yr |
| QQQ | 88 | 0.62%/yr | 0.53%/yr |
| RPAR | 27 | 2.48%/yr | 2.11%/yr |
| RSBT | 2 | 1.52%/yr | 1.29%/yr |
| RSSB | 3 | 1.86%/yr | 1.57%/yr |
| RSST | 3 | 0.70%/yr | 0.60%/yr |
| SCZ | 39 | 2.71%/yr | 2.30%/yr |
| SHY | 288 | 1.90%/yr | 1.62%/yr |
| SPX | index | — | — |
| SPXL | 36 | 1.47%/yr | 1.24%/yr |
| SPY | 135 | 1.79%/yr | 1.52%/yr |
| SSO | 70 | 1.02%/yr | 0.87%/yr |
| TIP | 201 | 3.17%/yr | 2.69%/yr |
| TLT | 288 | 3.44%/yr | 2.92%/yr |
| TMF | 49 | 2.13%/yr | 1.80%/yr |
| TQQQ | 21 | 0.31%/yr | 0.26%/yr |
| UPAR | 18 | 3.54%/yr | 3.01%/yr |
| UPRO | 46 | 0.38%/yr | 0.32%/yr |
| VEA | 66 | 3.01%/yr | 2.56%/yr |
| VEU | 61 | 2.77%/yr | 2.35%/yr |
| VGK | 63 | 3.57%/yr | 3.03%/yr |
| VIX | index | — | — |
| VIX3M | index | — | — |
| VNQ | 87 | 4.29%/yr | 3.64%/yr |
| VTI | 101 | 1.75%/yr | 1.49%/yr |
| VWO | 62 | 2.61%/yr | 2.22%/yr |
| XNDX | index | — | — |
