# Frozen total-return snapshot — 2026-08-24

Verbatim copy of `data/` at the ROTATION_SPEC Phase 0 baseline: the 2026-08
TradingView two-pass export batch (taken 2026-08-25), last bar 2026-08-24 on
every top-level file. 48 paired ETFs (`<SYM>.csv` exported with **Adjust data
for dividends: ON**, `price/<SYM>.csv` with the toggle **OFF**, same chart and
session, identical date columns per symbol), four single-series indices at top
level (SPX, XNDX, VIX, VIX3M — no `price/` twin), and `macro/` (UNRATE, RRSFS,
INDPRO, DTB3) carried for provenance only — the loader must never read it, and
`make_net_tr.py` does not copy it into the net derivative (observation-stamped
FRED series; loading them is a look-ahead until `MACRO_DATA_SPEC` exists).
This batch carries no Pine SMA overlay columns (ROTATION_SPEC §3.1); the
header is `time,open,high,low,close,Volume`. Append-only, like every snapshot.

Measured on this snapshot (TOTAL_RETURN_SPEC §4/§7, ROTATION_SPEC §2/§3.5;
test constants are pinned one order above the measurement):

- Pair calendars identical per symbol, all 48 pairs.
- Flat-segment noise in `ln R` (`R = adjusted / price`): worst monotonicity
  violation −4.31e-8 (TQQQ 2010-02-16; then QLD −2.07e-8, SSO −8.42e-9,
  UPRO −7.61e-9, SPXL −5.48e-9 — export quantization on the leveraged ETFs)
  → `TAU = 1e-6` holds unchanged.
- `R_last = 1` exactly (0.0) on all 48 pairs; no bar with `R > 1 + 1e-6`.
- Largest flat step 1.62e-6 (TQQQ); smallest genuine jump 1.247e-5 (BIL
  2009-11-02, a ZIRP-era ~$0.0011 distribution) — **below the six-symbol
  universe's `JUMP_MIN = 2e-5`**, so `make_net_tr.py` re-pins
  `JUMP_MIN = 1e-5` in the same commit (dead zone (5e-6, 1e-5) still empty
  across all pairs; the 2026-08-20 net derivative is byte-unchanged except
  its README's constant line).
- Implied cumulative distribution yields `y = −ln(R_first) / years` (%/yr,
  full file history): PDBC 6.85, HYG 6.23, DBMF 5.80, EDV 4.85, KMLM 4.37,
  VNQ 4.29, LQD 4.13, VGK 3.57, UPAR 3.54, TLT 3.44, GDE 3.28, AGG 3.19,
  TIP 3.17, BND 3.16, VEA 3.01, NTSE 2.85, IEF 2.81, VEU 2.77, SCZ 2.71,
  NTSI 2.71, EFA 2.67, VWO 2.61, ACWX 2.59, RPAR 2.48, TMF 2.13, SHY 1.90,
  EEM 1.90, RSSB 1.86, SPY 1.79, VTI 1.75, IWN 1.67, AVUV 1.58, RSBT 1.52,
  SPXL 1.47, BWX 1.45, BIL 1.39 (full-period average across the ZIRP years),
  EWJ 1.31, NTSX 1.20, IWM 1.17, DBC 1.13, BTAL 1.07, SSO 1.02, RSST 0.70,
  QLD 0.68, QQQ 0.62, UPRO 0.38, TQQQ 0.31, GLD 0.00 (never distributed;
  its pair is byte-identical, `R ≡ 1` exactly). These are the reference
  values behind the live-pair yield bands in `tests/test_total_return.py`.

`VIX.csv` and `VIX3M.csv` are the newer exports of this batch (ROTATION_SPEC
§3.4): the pre-batch `data/` copies ended 2026-08-21, and on the shared
history 1,285 VIX closes differ (all since 2021-05-21; 574 beyond ±0.01, four
beyond 0.05, worst 0.28 on 2023-06-07 — TradingView revisions/rounding).
VIX3M is identical on every shared date. VIX still carries values on 58 US
market holidays that VIX3M lacks — TradingView artefacts, kept out of every
rolling window by the cross-symbol loader's intersection rule. XNDX starts
2006-11-08 (TradingView's Nasdaq-100 TR history), SPX is price-only by
construction and must never seed a TR sim.
