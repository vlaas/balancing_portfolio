# Net total-return snapshot — 2026-09-02-net15-lqq0

Derived from the frozen `2026-09-02` snapshot by `make_net_tr.py` (NET_TR_SPEC §2–§3) at withholding w = 0.15: each distribution jump
factor k is replaced by k_net = w + (1 - w) * k, so every ex-date
reinvests (1 - w) * D instead of D; flat (pure price movement) rows
scale by the constant suffix product C only, and the net series anchors
to the parent at the last bar. `<SYM>.csv` carries columns `time,close`
only; `price/<SYM>.csv` is byte-copied from the parent. Step
classification (NET_TR_SPEC §2.1): FLAT_MAX = 5e-06,
JUMP_MIN = 1e-05, TAU = 1e-06.

Per-symbol rate override (CASH_SLEEVE_SPEC §10.5): LQQ at w = 0. The flat
convention is a modelling choice, not a fact; BIL's income is US
Treasury interest, the clearest §871(k) interest-related-dividend case
there is, so its true NRA withholding is plausibly ~0%. This snapshot
exists to break a tie inside the bias band, not to replace the flat
root — a decision run still uses the flat one unless it says otherwise.

| symbol | jumps | y gross | y net |
|---|---|---|---|
| ACWX | 39 | 2.59%/yr | 2.20%/yr |
| AGG | 275 | 3.20%/yr | 2.72%/yr |
| AVUV | 27 | 1.57%/yr | 1.34%/yr |
| BIL | 126 | 1.40%/yr | 1.19%/yr |
| BND | 233 | 3.17%/yr | 2.69%/yr |
| BTAL | 8 | 1.07%/yr | 0.91%/yr |
| BWX | 172 | 1.46%/yr | 1.24%/yr |
| CNDX | 0 | -0.00%/yr | -0.00%/yr |
| CSPX | 0 | -0.00%/yr | -0.00%/yr |
| DBC | 9 | 1.13%/yr | 0.96%/yr |
| DBMF | 18 | 5.78%/yr | 4.89%/yr |
| DBMF_EU | 0 | -0.00%/yr | -0.00%/yr |
| EDV | 75 | 4.84%/yr | 4.10%/yr |
| EEM | 47 | 1.90%/yr | 1.61%/yr |
| EFA | 46 | 2.67%/yr | 2.27%/yr |
| EURUSD | index | — | — |
| EWJ | 48 | 1.30%/yr | 1.11%/yr |
| GBPUSD | index | — | — |
| GDE | 8 | 3.26%/yr | 2.76%/yr |
| GLD | 0 | -0.00%/yr | -0.00%/yr |
| HYG | 233 | 6.25%/yr | 5.31%/yr |
| IB01 | 0 | -0.00%/yr | -0.00%/yr |
| IEF | 289 | 2.82%/yr | 2.40%/yr |
| IWM | 105 | 1.17%/yr | 1.00%/yr |
| IWN | 104 | 1.67%/yr | 1.42%/yr |
| KMLM | 4 | 4.35%/yr | 3.67%/yr |
| LQD | 289 | 4.14%/yr | 3.52%/yr |
| LQQ | 1 | 0.07%/yr | 0.07%/yr | w = 0 |
| MVEA | 0 | -0.00%/yr | -0.00%/yr |
| NDX | index | — | — |
| NTSE | 22 | 2.84%/yr | 2.41%/yr |
| NTSI | 23 | 2.69%/yr | 2.29%/yr |
| NTSX | 34 | 1.20%/yr | 1.02%/yr |
| PDBC | 11 | 6.83%/yr | 5.73%/yr |
| QLD | 32 | 0.68%/yr | 0.57%/yr |
| QQL3 | 0 | -0.00%/yr | -0.00%/yr |
| QQQ | 88 | 0.62%/yr | 0.53%/yr |
| QQQ3 | 0 | -0.00%/yr | -0.00%/yr |
| RPAR | 27 | 2.47%/yr | 2.10%/yr |
| RSBT | 2 | 1.51%/yr | 1.28%/yr |
| RSSB | 3 | 1.84%/yr | 1.56%/yr |
| RSST | 3 | 0.70%/yr | 0.59%/yr |
| SCZ | 39 | 2.71%/yr | 2.30%/yr |
| SHY | 289 | 1.91%/yr | 1.63%/yr |
| SPX | index | — | — |
| SPXL | 36 | 1.47%/yr | 1.24%/yr |
| SPY | 135 | 1.79%/yr | 1.52%/yr |
| SSO | 70 | 1.02%/yr | 0.87%/yr |
| TIP | 201 | 3.16%/yr | 2.69%/yr |
| TLT | 289 | 3.45%/yr | 2.93%/yr |
| TMF | 49 | 2.12%/yr | 1.80%/yr |
| TQQQ | 21 | 0.31%/yr | 0.26%/yr |
| UPAR | 18 | 3.52%/yr | 2.99%/yr |
| UPRO | 46 | 0.38%/yr | 0.32%/yr |
| VEA | 66 | 3.01%/yr | 2.56%/yr |
| VEU | 61 | 2.77%/yr | 2.35%/yr |
| VGK | 63 | 3.56%/yr | 3.02%/yr |
| VIX | index | — | — |
| VIX3M | index | — | — |
| VNQ | 87 | 4.28%/yr | 3.64%/yr |
| VTI | 101 | 1.75%/yr | 1.48%/yr |
| VWO | 62 | 2.61%/yr | 2.22%/yr |
| XNDX | index | — | — |
| XSPS | 0 | -0.00%/yr | -0.00%/yr |
