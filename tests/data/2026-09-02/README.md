# Frozen total-return snapshot — 2026-09-02

Verbatim copy of `data/` at the EU_SUBSTITUTE_SPEC Phase 0 baseline: the
2026-09-02 TradingView export batch — the nine EU lines and NDX exported
2026-09-02 after their own closes, every US pair re-exported 2026-09-03 after
the 16:00 ET close (§3.2; both passes, all anchors exact), the two FX singles
exported the same session — last bar 2026-09-02 on every top-level file
except `EURUSD.csv` / `GBPUSD.csv`, whose last label is 2026-09-01 because
TradingView stamps an FX_IDC daily bar by its 17:00 New York open (that bar
closes on 2026-09-02; `data/README.md`, "FX bar stamps"). 57 paired ETFs
(`<SYM>.csv` exported with **Adjust data for dividends: ON**, `price/<SYM>.csv`
with the toggle **OFF**, same session, identical date columns per symbol):
the 48 US pairs of the 2026-08 batch plus QQQ3, QQL3, LQQ, CNDX, CSPX, IB01,
MVEA, XSPS, DBMF_EU. Five single-series indices at top level (SPX, XNDX, VIX,
VIX3M, NDX — no `price/` twin), two FX singles (EURUSD, GBPUSD), and `macro/`
(UNRATE, RRSFS, INDPRO, DTB3) carried for provenance only — the loader must
never read it, and no derivative copies it. No Pine SMA overlay columns; the
header is `time,open,high,low,close,Volume`. Append-only, like every snapshot.

Currency: MVEA, LQQ and DBMF_EU are EUR lines (Xetra / Euronext Paris), XSPS
a GBX line (LSE, pence); the five other EU lines are USD (`data/README.md`,
"EU lines — line registry"). The raw files are in their trading currency;
the `-net15-usd` derivative converts them.

Measured on this snapshot (TOTAL_RETURN_SPEC §4/§7, ROTATION_SPEC §3.5;
test constants are pinned one order above the measurement):

- Pair calendars identical per symbol, all 57 pairs.
- Flat-segment noise in `ln R` (`R = adjusted / price`): worst monotonicity
  violation −2.69e-7 (LQQ — a EUR line quoted to three decimals; then TQQQ
  −4.31e-8, QLD −2.07e-8, SSO −8.42e-9, UPRO −7.61e-9, unchanged from the
  2026-08-24 batch) → `TAU = 1e-6` holds unchanged.
- `R_last = 1` exactly (0.0) on all 57 pairs; no bar with `R > 1 + 1e-6`;
  no step in the dead zone (5e-6, 1e-5).
- Largest flat step 1.62e-6 (TQQQ); smallest genuine jump 1.247e-5 (BIL
  2009-11-02) — `JUMP_MIN = 1e-5` holds unchanged.
- Implied cumulative distribution yields `y = −ln(R_first) / years` (%/yr,
  full file history): PDBC 6.83, HYG 6.25, DBMF 5.78, EDV 4.84, KMLM 4.35,
  VNQ 4.28, LQD 4.14, VGK 3.56, UPAR 3.52, TLT 3.45, GDE 3.26, AGG 3.20,
  BND 3.17, TIP 3.16, VEA 3.01, NTSE 2.84, IEF 2.82, VEU 2.77, SCZ 2.71,
  NTSI 2.69, EFA 2.67, VWO 2.61, ACWX 2.59, RPAR 2.47, TMF 2.12, SHY 1.91,
  EEM 1.90, RSSB 1.84, SPY 1.79, VTI 1.75, IWN 1.67, AVUV 1.57, RSBT 1.51,
  SPXL 1.47, BWX 1.46, BIL 1.40, EWJ 1.30, NTSX 1.20, IWM 1.17, DBC 1.13,
  BTAL 1.07, SSO 1.02, RSST 0.70, QLD 0.68, QQQ 0.62, UPRO 0.38, TQQQ 0.31,
  LQQ 0.07 (one distribution in 20.2 years, French-source, kept gross in the
  net derivative), and **`R ≡ 1` exactly** (never distributed, pair
  byte-identical) for GLD and the eight accumulating UCITS classes CNDX,
  CSPX, DBMF_EU, IB01, MVEA, QQL3, QQQ3, XSPS. These are the reference values
  behind the live-pair yield bands and the `ZERO_YIELD` set in
  `tests/test_total_return.py`.

EU line first bars: LQQ 2006-06-28, XSPS 2008-02-08, CNDX/CSPX 2010-09-15,
QQQ3 2012-12-17, IB01 2019-02-22, MVEA 2020-04-23, QQL3 2022-06-09, DBMF_EU
2025-03-17 (EU_SUBSTITUTE_SPEC §7). US `DBMF` is the restored original
(2019-05-08 →); `DBMF_EU` is the iMGP DBi UCITS ETF under the collision-safe
name (§3.1).

Derivatives: `2026-09-02-net15/` (`make_net_tr.py 2026-09-02 --rate-override
LQQ=0 --out 2026-09-02-net15` — the README inside names itself
`-net15-lqq0`, the directory keeps the spec's name) and
`2026-09-02-net15-usd/` (`make_usd.py 2026-09-02-net15`), the **decision root
for every EU lane**; `2026-09-02-net15-usd-hc/` follows from Phase 1.
