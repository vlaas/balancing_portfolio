# Round-Trip Trading Costs for Six US ETFs (TQQQ, BTAL, DBMF, KMLM, QQQ, SPY): Estonian Retail Investor via tastytrade vs Interactive Brokers Ireland

## TL;DR
- **The single most important finding is an availability blocker, not a cost number:** Interactive Brokers' Ireland entity (IBKR IE), which serves Estonian residents, cannot sell any of these six US-domiciled ETFs to a retail client because none has a PRIIPs Key Information Document (KID). Per Interactive Brokers' own guidance, "IBKR is required to block trading in a PRIIP if a KID is not available." For an Estonian retail investor, **tastytrade (a US SEC/FINRA-regulated broker that lists Estonia as an eligible country) is effectively the only viable route** to trade TQQQ/BTAL/DBMF/KMLM/QQQ/SPY directly.
- At tastytrade, stock/ETF commission is **$0**, so the real per-side cost is **half-spread + slippage + tiny regulatory fees on sells**. Measured average spreads (ETF Research Center / AltaVista, NBBO-based, ~Aug 2026): SPY ~0.3 bp, QQQ ~0.5–1 bp, TQQQ ~1–2 bp, DBMF 3 bp, BTAL 9 bp, KMLM 9 bp (range up to 38 bp).
- **Recommended calibration:** per-side `cost_bps` ≈ 1 (SPY/QQQ/TQQQ), 2–3 (DBMF), 5–7 (BTAL/KMLM). The spec's **5 bps realistic anchor is well-chosen** as a blended TQQQ+BTAL figure; the **20 bps stress anchor is reasonable** for BTAL/KMLM in stressed markets. The **3% cash-yield proxy is realistic** (SOFR 3.65% on Aug 18, 2026; 3-month T-bill ~3.6%) but only if cash is actively parked; idle USD at tastytrade earns ~0%.

## Key Findings

1. **PRIIPs blocks IBKR IE entirely for these tickers.** EU law (PRIIPs Regulation EU No 1286/2014) requires a KID for any packaged product sold to EU retail. US ETF issuers do not produce KIDs, so IBKR is legally required to block the buy order. This applies to all six tickers.
2. **tastytrade sidesteps PRIIPs** as a US SEC/FINRA-regulated broker, and Estonia is explicitly on its eligible-countries list. This makes it the practical choice.
3. **Commissions are a near-zero cost component** for the viable route (tastytrade = $0 on stocks/ETFs). IBKR's schedule (Fixed $0.005/share min $1; Tiered $0.0035/share min $0.35) is only relevant for UCITS alternatives or elective-professional clients.
4. **Bid-ask half-spread dominates the per-side cost.** BTAL and KMLM are the wide names (~9 bp average each); TQQQ/QQQ/SPY are extremely tight; DBMF is surprisingly tight (3 bp) given its ~$3.2B AUM.
5. **FX is a one-time drag on contributions, not a per-trade cost** — it should not be baked into `cost_bps`.
6. **Cash yield ~3% is achievable** but requires action (a T-bill ETF like SGOV at tastytrade); idle cash pays ~0% at tastytrade and 3.13% only above $10k at IBKR.

## Details

### 1. Availability / PRIIPs (the decisive constraint)

Interactive Brokers' Campus guidance ("Trading Overseas with IBKR") states: *"Issuers of U.S. listed ETFs do not as a rule create Key Information Documents (KIDs). This means that EEA and UK Retail clients cannot purchase the product, according to the Packaged Retail and Insurance-based Investment Products Regulation – EU No 1286/2014. IBKR is required to block trading in a PRIIP if a KID is not available."* Estonian residents are onboarded under **IBKR Ireland (Central Bank of Ireland regulated)**, so they fall squarely under this block. None of TQQQ, BTAL, DBMF, KMLM, QQQ, or SPY publishes an EU KID.

Workarounds at IBKR IE: (a) trade the US ETF as a **CFD** (issued by IBKR's EU entity — different risk/tax profile, not equivalent to holding shares); (b) qualify for **elective professional status** (MiFID II — generally requires meeting 2 of 3 tests including a portfolio over EUR 500,000, which drops to EUR 250,000 under the incoming EU Retail Investment Strategy), which exempts you from PRIIPs; or (c) buy **UCITS equivalents** that do have KIDs. Note that if an Estonian retail client sells a cash-secured put on a US ETF at IBKR and it is assigned, IBKR cash-settles rather than delivering shares, because delivery would breach PRIIPs.

**UCITS alternatives (buyable at IBKR IE), for reference only:**
- 3x Nasdaq-100: **LQQ3/QQQ3** (WisdomTree/Leverage Shares 3x) — leveraged ETPs with higher TERs (~0.75%+) and their own tracking/roll costs; spreads meaningfully wider than TQQQ.
- S&P 500: **CSPX / SXR8** (iShares Core S&P 500 UCITS) — TER 0.07%, very tight spreads.
- Nasdaq-100: **EQQQ (Invesco)** / **CNDX (iShares)** — TER 0.30%/0.33%.
- Managed-futures / anti-beta UCITS: there is **no clean UCITS twin** for BTAL, DBMF, or KMLM; the closest are broad liquid-alternative / managed-futures UCITS from a handful of issuers with different methodologies. This is a genuine gap — the alternative-strategy sleeve is effectively only accessible via a US broker.

### 2. Commissions

**tastytrade:** Stocks and ETFs are **$0 commission** to open and close, with no per-share minimum. There is no account minimum and no inactivity fee. Only pass-through regulatory fees apply on sells (see §7).

**IBKR (Pro; the only plan available to non-US/Singapore clients — IBKR Lite is US/Singapore only):**
- **Fixed:** USD 0.005/share, USD 1.00 minimum per order, capped at 1% of trade value.
- **Tiered:** USD 0.0035/share at the entry tier, USD 0.35 minimum, plus exchange/regulatory/clearing pass-through.

Commission in bps depends on share price and order size (the min-fee drag hits small orders hardest). Illustrative Fixed-plan commission (were these ETFs purchasable):

| Order | TQQQ (~$70) | BTAL (~$12) | QQQ (~$600) | SPY (~$670) |
|---|---|---|---|---|
| $1,000 | $1 min = 10 bp | $1 min = 10 bp | $1 min = 10 bp | $1 min = 10 bp |
| $5,000 | $1 min = 2 bp | $2.08 = 4.2 bp | $1 min = 2 bp | $1 min = 2 bp |
| $10,000 | $1 min = 1 bp | $4.17 = 4.2 bp | $1 min = 1 bp | $1 min = 1 bp |
| $25,000 | $1.79 = 0.7 bp | $10.42 = 4.2 bp | $1 min = 0.4 bp | $1 min = 0.4 bp |

Key insight: **the min-fee/per-share structure penalizes low-priced tickers (BTAL) and small orders.** For the viable route (tastytrade), all of this is moot: commission = $0.

### 3. Bid-Ask Spreads (dominant cost component)

Measured average NBBO spreads from ETF Research Center (etfrc.com, powered by AltaVista Research; up to 3-month NBBO averages on NASDAQ tick data), as-of ~August 2026, plus liquidity context:

| Ticker | Price (mid-2026) | AUM | Avg daily volume | Avg spread | Half-spread |
|---|---|---|---|---|---|
| SPY | ~$670 | ~$700B+ | massive | ~0.003% (0.3 bp) | ~0.16 bp |
| QQQ | ~$600 | ~$400B+ | 2nd most-traded US ETF | <0.01% (~0.5–1 bp) | ~0.3–0.5 bp |
| TQQQ | ~$50–73 | ~$33B | ~67–105M shares/day | ~1–2 bp | ~0.5–1 bp |
| DBMF | ~$30–31 | ~$3.2B | ~1.2M shares/day | 3 bp (range 3–4) | ~1.5 bp |
| BTAL | ~$12.25 | ~$317M | ~0.7–1.0M shares/day | 9 bp (range 8–17) | ~4.5 bp |
| KMLM | ~$28–29 | ~$420M | ~150–195K shares/day | 9 bp (range 3–38) | ~4.5 bp |

Notes:
- **SPY**'s issuer (State Street) cites an average spread of about 0.003% — essentially zero; ETF.com similarly reports SPY at 0.0032%.
- **TQQQ** snapshot: bid $72.04 / ask $72.06 = $0.02 = 0.28 bp; the multi-day average is a bit wider (~1–2 bp) but still very tight given its enormous volume.
- **KMLM** has the widest range (3–38 bp) reflecting its modest ~150–195K-share daily volume; spread quality is highly time-of-day dependent.
- **BTAL** at ~9 bp / 0.09% is the structurally widest average (low $12 price and ~$317M AUM); its 8–17 bp range confirms the spec's expectation of "meaningfully wider."
- Fund fact sheets (AGF, KraneShares, iMGP) do **not** publish spread statistics; the etfrc/AltaVista figures are the strongest public measured source, and etf.com/etfdb.com gate the exact dollar figures behind login.

### 4. Slippage / Execution Quality

For SPY, QQQ, and TQQQ (deep books, penny-wide or near-penny spreads), slippage beyond the half-spread is negligible with marketable limit orders near the touch. For **BTAL, KMLM, and DBMF**, use **limit orders**, avoid the opening and closing auctions and the first/last ~15 minutes, and consider SMART-type routing and midpoint pegs, which can capture part of the spread. KMLM in particular can show transient wide quotes (up to ~38 bp), so passive/limit execution materially reduces realized cost. A slippage allowance of ~0.5 bp for the liquid names and ~1–2 bp for BTAL/KMLM is prudent.

### 5. FX Costs (EUR→USD)

**IBKR:** manual spot conversion on IDEALPRO costs **0.20 bp (0.002%) of value, USD 2.00 minimum**, at interbank rate with no markup; auto-conversion costs **~0.03% (3 bp)** baked into the rate. Breakeven is ~$6,667: above it, manual wins. This is a **one-time cost on each EUR contribution**, not per-trade — and not applicable to IBKR for these tickers anyway (blocked).

**tastytrade:** accepts **USD only**; you must convert EUR before/at deposit. tastytrade does not run an in-account multicurrency FX desk for retail, so the practical route is a third-party converter such as **Wise** (~0.4–0.5% for EUR→USD) or a bank wire (higher). Wire withdrawals cost **$25 domestic / $45 international**; ACH deposits via Wise are cheaper and can arrive same-day. **This FX cost (~40–50 bp on contributions via Wise) is the single largest friction for the tastytrade route** — but it is a one-time cost on new money, not a per-trade `cost_bps` input. It should be modeled as a contribution haircut, not folded into per-trade cost.

### 6. Cash Yield on Idle USD

- **IBKR IE:** pays **3.13% on USD cash above USD 10,000** for accounts with NAV > $100,000; nothing on the first $10,000, and a lower blended rate for NAV < $100,000 (scaling up toward the threshold).
- **tastytrade:** historically pays **little or nothing** on uninvested cash. To earn yield, park cash in a T-bill ETF (e.g., **SGOV/BIL** — US ETFs, buyable at tastytrade), yielding roughly SOFR minus a few bp.
- **Benchmark rates (mid-Aug 2026):** SOFR **3.65%** (Aug 18, 2026, per the New York Fed / FRED); 3-month T-bill ~**3.6%** (secondary-market discount basis was 3.61% in March 2026); Fed funds roughly in line. The 3-month T-bill-minus-Fed-funds spread was slightly negative (~−0.04% in Feb 2026), indicating a flat/slightly inverted front end.
- **Verdict on the 3% spec assumption:** realistic. Net of the small drag from the uninvested first $10k (IBKR) or the need to actively sweep into SGOV (tastytrade), **~3% is a fair, mildly conservative proxy**. If cash is left truly idle at tastytrade, use ~0%; if swept to SGOV, use ~3.3–3.5%.

### 7. Other Frictions (regulatory fees on sells)

- **SEC Section 31 fee:** **$20.60 per $1,000,000** of sales, effective April 4, 2026 (per the SEC Fee Rate Advisory for FY2026; the rate had been $0.00 from mid-May 2025 through April 3, 2026). That is **0.206 bp, on sells only**. tastytrade confirms it passes this through: "As of April 4 2026, the sale of equity securities is $20.60 for every $1,000,000 in sales."
- **FINRA TAF:** **$0.000195 per share** effective Jan 1, 2026 (up from $0.000166; cap $9.79/trade), on sells only. Per-share, this is ~0.03 bp for a $70 share, ~0.16 bp for a $12 share (BTAL), ~0.07 bp for KMLM (~$28).
- **Combined sell-side regulatory drag: ~0.25–0.4 bp**, applied only to sells and only at the US broker. Negligible but included for completeness.
- **IBKR IE:** inactivity fees abolished; one free withdrawal per month.
- **Estonian tax context:** under the **investeerimiskonto** (investment account) regime, tax is deferred until net withdrawal, so **there is no per-trade tax friction**. US dividend withholding is 15% under the US–Estonia treaty with a W-8BEN; dividends on these tickers are small and are excluded per instruction.

### Synthesis: per-side all-in cost (bps) at tastytrade (the viable broker)

| Ticker | Commission | Half-spread | Slippage allow. | Sell reg fees | **Per-side buy** | **Per-side sell** |
|---|---|---|---|---|---|---|
| SPY | 0 | 0.16 | 0.3 | 0.25 | **~0.5 bp** | **~0.7 bp** |
| QQQ | 0 | 0.4 | 0.3 | 0.25 | **~0.7 bp** | **~1 bp** |
| TQQQ | 0 | 0.75 | 0.5 | 0.25 | **~1.3 bp** | **~1.5 bp** |
| DBMF | 0 | 1.5 | 1.0 | 0.3 | **~2.5 bp** | **~2.8 bp** |
| BTAL | 0 | 4.5 | 1.5 | 0.4 | **~6 bp** | **~6.4 bp** |
| KMLM | 0 | 4.5 | 1.5 | 0.3 | **~6 bp** | **~6.3 bp** |

(FX ~40–50 bp one-time on EUR contributions handled separately, not per-trade. Note: at IBKR, if these were tradable, commission would add ~0.4–10 bp per the §2 table and FX ~0.2 bp manual — but IBKR is blocked for retail, so this table is the operative one.)

## Recommendations

**Broker choice:** For an Estonian retail investor who must trade these specific US tickers, **use tastytrade**. IBKR IE cannot execute buys in any of them for a retail client. Only pursue IBKR IE if (a) you will substitute UCITS equivalents, or (b) you qualify for elective professional status (portfolio > EUR 500k, meeting 2 of 3 MiFID II tests).

**cost_bps calibration (per side), for use in `fee = cost_bps/10,000 × trade value`:**
- SPY, QQQ, TQQQ: **1 bp** base case.
- DBMF: **2–3 bp** base case.
- BTAL, KMLM: **5–7 bp** base case (use **6 bp**).
- **Blended portfolio realistic value (TQQQ- and BTAL-dominated):** if trade flow is split roughly between TQQQ (~1 bp) and BTAL/KMLM (~6 bp), a single blended figure of **~4 bp** is accurate; **the spec's 5 bps is a sound, slightly conservative realistic anchor — keep it.**
- **Stress value:** **20 bps is a reasonable stress anchor** for BTAL/KMLM (their spreads widen toward 17–38 bp in thin/volatile conditions, plus slippage). For a TQQQ-heavy sleeve, a ~10 bp stress is more representative; 20 bps is appropriately conservative portfolio-wide. **Keep 20 bps as the stress case.**

**cash_yield:** **Keep 3%** as the base assumption; it matches the current front end (SOFR 3.65%, T-bill ~3.6%) net of realistic frictions. Sensitivity: model 0% (idle cash at tastytrade) as a downside and 3.5% (cash swept to SGOV) as an upside. A Fed cutting cycle pushing SOFR below ~2.5% would argue for lowering to ~2%.

**Staged next steps:** (1) Open a tastytrade international account (Estonia eligible; USD-only funding via Wise). (2) Model FX as a ~45 bp haircut on each EUR contribution, separate from per-trade cost. (3) Use limit orders for BTAL/KMLM/DBMF and avoid the open/close. (4) Sweep idle USD into SGOV to realize the ~3% cash yield. (5) Re-check spreads quarterly, especially KMLM.

## Caveats
- **Spread figures are point-in-time averages** (etfrc/AltaVista, ~Aug 2026) and will drift with volume and volatility; KMLM's 3–38 bp range means its realized cost is highly execution-dependent.
- **TQQQ's price is volatile** (traded ~$49 in April 2026 and ~$72 in another 2026 snapshot); bps figures are robust to price level, but share-count-based commissions are not (irrelevant at tastytrade's $0).
- **IBKR's 3.13% USD rate and the SEC/TAF rates are current as of 2026 and change periodically** (Section 31 reset from $0 to $20.60 on April 4, 2026; TAF rose to $0.000195 on Jan 1, 2026).
- **The PRIIPs block is the load-bearing conclusion.** If the EU Retail Investment Strategy or a future reform restores retail access to US ETFs, or if you opt up to professional status, IBKR IE becomes viable and its cash-yield/FX edge would make it competitive with tastytrade.
- FX via Wise (~0.4–0.5%) is an estimate of typical retail EUR→USD cost and varies with amount and market conditions.
- BTAL's identity: the fund is now branded **AGF U.S. Market Neutral Anti-Beta** (formerly QuantShares); it switched from passive index-tracking to an active rules-based negative-beta strategy on Feb 14, 2022, and carries a high expense ratio (gross 1.65%) — a holding cost separate from the trading `cost_bps`.