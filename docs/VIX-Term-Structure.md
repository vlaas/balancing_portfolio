# Measuring the VIX Term-Structure Slope on a Budget: A Regime Indicator for a Monthly-Rebalanced TQQQ/Safe-Asset System

## TL;DR
- **Your premise is wrong in the way that matters most: you do NOT need VIX futures *options* prices to measure the term-structure slope.** The slope is defined by the VIX *futures* prices themselves (VX1 vs VX2, or VX1 vs spot VIX), and those settlement prices are free from CBOE back to 2004. Even cheaper and cleaner: the cash index ratio **VIX/VIX3M** is computable from two free daily CSVs and proxies the futures slope well enough for a monthly regime gate.
- **Recommended primary signal: the VIX/VIX3M ratio (formerly VIX/VXV), smoothed with a ~5–10 day moving average, with dual thresholds (hysteresis).** It is free and permanent (CBOE + Yahoo), covers your 2012 backtest start with room to spare (VIX3M daily data begins 4 Dec 2007), is a one-line causal CSV column, and disagrees with the actual tradeable futures curve on only about 7% of days.
- **Honest limitation you must design around: term-structure signals catch volatility-shock crashes (2008, 2020) but structurally MISS slow grinding bears (2022), and even in fast crashes they often flip only after the drawdown is underway.** Treat this as a de-risking gate that reduces (not eliminates) drawdown, and pair it with your existing EWMA realized-vol on QQQ as a second, independent trigger.

## Key Findings

1. **Options data are not required.** The VIX futures term-structure slope is a relationship between futures prices, not option prices. CBOE/CFE publishes end-of-day VIX futures settlement data free, and the cash volatility indices (VIX, VIX9D, VIX3M, VIX6M) are free daily CSVs. VIX futures *options* are the one genuinely expensive dataset — and they are irrelevant to slope measurement.

2. **Three tiers of measure, in descending fidelity and descending cost/complexity:**
   - **True futures slope** (VX1/VX2 or VX1/spot): highest fidelity, but requires stitching individual contract CSVs or trusting a continuous series.
   - **Cash index ratio** (VIX/VIX3M): ~93% agreement with the futures regime, trivially free and permanent, best cost/effort/fidelity trade-off.
   - **VRP / realized-vol proxies** (VIX vs realized vol; VIX vs its own moving average): need no vol-index data at all, but measure a different (though related) thing and are noisier as a *term-structure* proxy.

3. **The literature is consistent that the slope predicts volatility-ETP returns and carries information about equity risk**, though the equity-return R² is low. Simon & Campasano (2014) is the canonical futures-basis paper; Johnson (2017) and Cheng (2019) formalize that the *slope* (not the level) carries the priced variance-risk-premium information.

4. **Contango is the normal state the large majority of days.** Since VIX futures launched in 2004, contango has been the default state about 84% of the time, with the M1:M2 average daily contango around 5.6% (median 6.3%); Eco3min puts it at "roughly 85% of trading days" using CFE and FRED data, with total backwardation on only ~5% of days. So a contango-gated strategy is "risk-on" most of the time and de-risks only in the rare, clustered stress windows.

5. **The 2022 blind spot is real and important:** in the slow, rate-driven 2022 bear the curve mostly stayed in contango because VIX3M rose alongside VIX. A pure term-structure gate would have largely stayed risk-on through a bear market that ran −25.4% from the S&P 500's 3 Jan 2022 peak of 4,796.56 to its 12 Oct 2022 trough of 3,577.03 (282 days). This is the single most important failure mode for your use case.

## Details

### 1. Direct measurement from VIX futures settlement prices

**Free sources and history depth:**
- **CBOE/CFE historical futures data** — free CSVs of daily OHLC + settlement for every individual VIX futures contract, covering the whole history from VIX futures launch on 26 March 2004. This is the authoritative source (the "Settle" column is the official settlement; expired contracts show a final settlement row with OHLC/volume zeroed). Downside: it is *per-contract*; to build a VX1/VX2 series you must stitch contracts and handle rolls yourself.
- **TradingView continuous contracts** `CBOE:VX1!` (front) and `CBOE:VX2!` (second month): adequate for charting and for a slope *ratio* signal, because VX1!/VX2! is roll-invariant on any given day (both legs are same-day prices, so the discontinuity at roll affects levels, not the same-day ratio). For backtesting you should be aware TradingView continuous series are back-adjusted/roll-stitched and their deep history and adjustment convention are not fully transparent — fine for a regime ratio, risky for precise level-based P&L.
- **FRED** carries spot VIX (VIXCLS, from 1990) but does NOT carry VIX futures — so FRED alone cannot give you the futures slope.
- **Nasdaq Data Link (formerly Quandl)** historically hosted CBOE VIX futures (the free "CHRIS/CBOE_VX*" continuous series were deprecated); today reliable free futures history is best taken directly from CBOE.

**Data-quality issues:** roll convention (calendar vs volume), the fact that VX1 has a shrinking time-to-maturity (so the VX1/spot basis mechanically shrinks toward expiry), and constant-maturity construction (the "30-day" and "constant-maturity" series like SPVXSTR require weighting VX1 and VX2 by days-to-roll). For a *ratio* regime signal these are second-order; for anything measuring roll yield in points/day they matter.

**Practitioner slope conventions on the futures themselves:**
- The VX1/spot-VIX ratio typically sits between 1.04 and 1.08 in normal contango — VX1 priced 4 to 8% above spot; in backwardation the ratio drops below 1.00, and the extreme episodes (March 2020, August 2024) saw it fall to 0.75–0.80 (per Eco3min).
- The VX2/VX1 "contango %" is commonly considered risk-on above roughly +5% and risk-off below −5%.
- Simon & Campasano's "daily roll" = (front VIX future − spot VIX) / (trading days to settlement). Their published strategy shorts the nearest future (≥10 trading days to settle) when the daily roll is **more favorable than 0.10 VIX points/day** (buys when in backwardation with daily roll less than −0.10), and exits when it falls below **0.05 points/day** or after a maximum of **9 business days** (note: many secondary summaries cite a "5 trading day" baseline — the paper's headline profitability exhibit uses 9 business days). Over 2006–2011 the hedged version (short VIX futures in contango, long in backwardation, hedged with E-mini S&P 500 futures) generated a 53% annual compound return per CXO Advisory (short trades: 62 trades, avg life 6.4 days, mean profit ~$861/contract; Sortino ratios ~0.75/0.53 for hedged short/long). Crucially, roughly half the profit came from the 2008 crisis and the edge decayed materially after mid-2010.

### 2. Index-based proxies from free spot volatility indices

**The core ratios and their meaning:**
- **VIX/VIX3M** (a.k.a. IVTS, implied-volatility term structure; formerly VIX/VXV): the standard. Below 1.0 = contango/calm; above 1.0 = backwardation/stress. This is the single most widely used cash proxy.
- **VIX9D/VIX**: a *faster* signal (9-day vs 30-day). Flips earlier but is much noisier — useful as an early-warning tripwire, too whippy as a sole gate.
- **VIX3M/VIX6M** (or VIX/VIX6M): a *slower*, smoother read of the mid-curve; flattening here is a "fear becoming structural" signal.

**Fidelity to the true futures curve:** The cash VIX/VIX3M ratio agrees with the tradeable futures regime the large majority of the time. The cleanest published disagreement statistic comes from Harbourfront/Relative Value Arbitrage (24 Nov 2024): from January 2013 to July 2024, VX futures were in backwardation while the spot 1M<3M relationship still showed contango only about 7% of the time — though that divergence then spiked to 53% of days from 1 August to 4 November 2024, an unusual episode. A well-known practitioner refinement is that the cash ratio needs a threshold around **0.90–0.95, not 1.0**, to align with when the tradeable futures roll actually turns negative — i.e., the cash ratio reads "contango" slightly too optimistically relative to the futures curve, because spot VIX carries no roll/time premium. No rigorous peer-reviewed correlation coefficient between the cash ratio and the VX1/VX2 basis appears to be published; this is a genuine gap in the literature, so treat "~93% regime agreement / ~0.90 practitioner threshold" as the best available characterization rather than a precise R².

**Common thresholds in practice:**
- VIX/VIX3M > 1.0 = backwardation (standard); > 1.10 = deep backwardation/panic.
- The classic VIX/VXV work used 0.90/0.917 as entry/exit bands for inverse-vol timing (dual thresholds already baked in).
- A "> 0.95 = early warning, > 1.0 = confirmed" scheme is a natural hysteresis pair.

**Availability and exact history start dates (all free):**
- **VIX**: CBOE + FRED (VIXCLS) from 1990; Yahoo `^VIX`.
- **VIX3M** (formerly VXV): CBOE daily CSV from **4 December 2007**; Yahoo `^VIX3M`. (Six Figure Investing has calculated a synthetic VIX3M-style series back to 1990, but that is a private reconstruction, not official.)
- **VIX9D**: CBOE from **October 2013** (per third-party index-start listings); Yahoo `^VIX9D`.
- **VIX6M**: CBOE from **4 June 2014** per one index-start listing (note: VIX6M as an index was published earlier under the VXMT name; confirm the exact CSV start on CBOE if you need pre-2014).
- **VIX1D**: launched 24 April 2023 (with CBOE-provided backtest history); too new for your backtest.
- **CBOE direct-download pattern**: `cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv` (and analogous filenames for VIX, VIX9D, VIX6M).

For your backtest starting 2012-01-03, **VIX/VIX3M is fully covered** (VIX3M from Dec 2007). VIX9D and VIX6M do NOT cover 2012 (they start 2013–2014), which is a decisive point in favor of VIX/VIX3M as the primary.

### 3. ETP-based proxies (VXX/VIXY, VXX/VXZ, SPVXSTR/SPVXMTR)

- **VXX/VIXY drift vs spot VIX** and the **VXX/VXZ ratio** encode the roll yield (short-term vs mid-term futures). The VXX:VXZ ratio has a steady structural downtrend precisely because short-term contango decay exceeds mid-term.
- **Pros:** these are traded prices, so they reflect the *actual* futures roll investors experience.
- **Cons for your use:** (a) VXX history is contaminated by structure changes (the 2019 VXX→VXXB→VXX ticker/issuer episode) and by reverse splits; (b) VXX only launched Jan 2009 and VIXY May 2011; (c) the ETP price mixes level and roll, so it is a *worse clean slope proxy* than the cash ratio. The underlying S&P indices **SPVXSTR** (short-term) and **SPVXMTR** (mid-term) are cleaner than the ETPs and free from S&P Global, but they still start in the 2009 era and are more work to obtain than two CBOE CSVs. **Net: for a slope regime gate, cash VIX/VIX3M dominates ETP proxies on cleanliness, history, and effort.**

### 4. Realized-vol / price-based alternatives (no vol-index data needed)

Because your pipeline already computes EWMA realized vol on QQQ, you can build a **variance-risk-premium (VRP) sign** signal with zero extra data:
- **VRP proxy** = VIX − (realized vol of SPX/QQQ). Positive (implied > realized) = calm/risk-on; negative = stress. This is the DDN/Trading-the-Odds/VolatilityMadeSimple family of signals. A representative published rule: 5-day average of [VIX − (10-day realized vol of SPY ×100)] > 0 → short-vol, else long-vol.
- **VIX vs its own moving average**: crudest regime read; captures "vol is rising" but has no term-structure information at all.

**Honest comparison:** VRP and term-structure slope are *correlated but distinct*. The slope (VIX/VIX3M) is the cleaner, lower-lag *term-structure* measure; VRP is a different edge (implied-vs-realized mispricing) and is notoriously prone to a specific failure: after a spike, realized vol keeps rising while VIX falls, driving VRP negative exactly when you'd want to re-risk — a whipsaw. For *regime detection specifically*, the term-structure slope is generally regarded as the more robust single signal, but VRP is valuable as an **independent confirmer** and, crucially for 2022, may catch grind-downs that the term structure misses.

### 5. Evidence on signal quality

- **Simon & Campasano (2014), *The VIX Futures Basis*, J. of Derivatives 21(3):54–69:** the basis has forecasting power for VIX futures *returns* (not for spot-VIX changes); shorting when in contango / buying when in backwardation is profitable and robust to costs. Their regressions nonetheless "explain only about 10% of the variation of VIX futures price changes" — a real but modest edge. This is the empirical backbone for using the slope to time vol ETPs.
- **Johnson (2017), *Risk Premia and the VIX Term Structure*:** the second principal component, **SLOPE**, summarizes nearly all the predictive information in the curve, forecasting variance-swap, VIX-futures, and straddle returns — a rejection of the expectations hypothesis in favor of a priced variance risk premium.
- **Cheng (2019), *The VIX Premium*:** VIX premiums predict VIX-futures excess returns (coefficient ~0.92); documents the "low premium-response puzzle" (premium falls as risk rises) — relevant because it warns the signal can weaken exactly when you need it.
- **Fassas & Papanicolaou-type work:** an inverted VIX curve has a significant positive relation with subsequent S&P 500 returns 2010–2017 (contrarian), while normal curves have little predictive power — R² is low (0.01–0.035), so this is a *risk gate*, not an alpha engine.
- **Frequency of contango:** ~84–85% of trading days since 2004; total backwardation ~5% of days and rarely lasting more than a few weeks; the longest continuous contango stretch was 273 trading days between 2004 and 2005. Backwardation has preceded essentially every major drawdown, but with false positives.

**Whipsaw, lag, and smoothing:**
- Raw daily VIX/VIX3M whipsaws around 1.0. Backwardation occurred on only ~7.7% of days since ~2009/2010, in ~43 clustered episodes — many of them brief, self-reversing dips in bull markets.
- Cash-index ratios can lag the actual futures by a day or so and read contango slightly too generously (hence the ~0.90 practitioner threshold).
- **Recommended smoothing: a 5–10 day moving average of the ratio**, and a look-ahead-free rule such as "act when the 5-day-average VIX/VIX3M crosses 1.0." For a *monthly* rebalance cadence this smoothing is almost mandatory — you do not want a single panicky close to flip a monthly allocation.

**Failure modes to design around:**
- **Feb 2018 "Volmageddon":** the cash curve (VIX9D>VIX, then VIX>VIX3M) actually flashed warnings in the days *before* Feb 5, so a fast proxy would have helped — but the move was so violent that a monthly gate could still have been caught mid-event.
- **COVID March 2020:** backwardation persisted ~43 straight days (Feb 24–Apr 23, 2020) while the S&P fell ~30% at the worst — the signal *worked* as a de-risk gate but triggered after the initial leg down.
- **2022 bear:** the term structure barely inverted; VIX3M rose with VIX, so VIX/VIX3M mostly stayed <1. A pure slope gate would have stayed risk-on through the full −25.4% peak-to-trough drawdown. **This is the dominant weakness for your system** and the reason to pair the slope with your QQQ realized-vol/trend logic.
- **General:** backwardation signals frequently trigger *after* the drawdown is underway (the signal confirms stress, it does not forecast it). Use it to reduce further damage and to avoid re-risking too early, not to call tops.

### 6. Practical recommendation for your specific system

**Primary signal — VIX/VIX3M, computed as a causal daily-close CSV column:**
- **Data:** CBOE `VIX_History.csv` and `VIX3M_History.csv` (or Yahoo `^VIX`/`^VIX3M`). Both free, permanent, daily close.
- **History:** VIX3M from 4 Dec 2007 → fully covers your 2012-01-03 sweep start with a 4-year warmup buffer.
- **Column:** `ivts = VIX / VIX3M`, then `ivts_smooth = ivts.rolling(window).mean()` (start with 10-day; test 5). Null during warmup (first `window−1` rows) matches your causal/null-during-warmup semantics. Everything is same-day close, so there is no look-ahead.

**Threshold / hysteresis scheme (dual thresholds strongly advised):**
- **Risk-on (normal rebalance):** smoothed VIX/VIX3M **< 0.95**.
- **Early-warning tilt (partial shift to safe assets):** **0.95 ≤ smoothed ratio < 1.00**.
- **Risk-off (full tilt to BTAL/KMLM/DBMF/cash):** smoothed ratio **≥ 1.00**.
- Hysteresis prevents flip-flopping right at 1.0: e.g., require the smoothed ratio to fall back **below 0.95** to re-risk after a risk-off trigger. This asymmetry (arm at 0.95, disarm at 0.95 only after touching ≥1.0) is the practitioner-standard way to cut whipsaws.

**Why VIX/VIX3M over the alternatives for you:**
- Free and permanent (unlike anything requiring futures-options or paid feeds).
- Longest usable free history that covers 2012 (VIX9D/VIX6M do not).
- One-line, causal, close-only computation — drops straight into your indicator framework.
- ~93% regime agreement with the true futures curve — more than adequate for a monthly gate that only needs to distinguish "calm" from "stressed," not to trade the roll intraday.

**Belt-and-suspenders (recommended):** because of the 2022 blind spot, gate on **VIX/VIX3M OR your existing QQQ EWMA-realized-vol trigger** — i.e., de-risk if *either* the term structure inverts *or* realized vol breaches its threshold. The term structure catches vol-shock crashes; realized-vol/trend catches slow grinds. This union is materially more robust than either alone and costs you nothing extra in data.

**Optional higher-fidelity upgrade:** if you later want to confirm the cash signal against the tradeable curve, add `VX1!/VX2!` from TradingView (or stitch CBOE contract CSVs) as a secondary column and require agreement for the full risk-off tilt. Not necessary for v1.

## Recommendations

1. **Ship VIX/VIX3M as your primary regime column now.** Pull the two free CBOE CSVs, compute `ivts = VIX/VIX3M`, smooth with a 10-day MA, null-during-warmup. This directly refutes the "need expensive options data" premise and covers your 2012 backtest window.
2. **Use dual thresholds with hysteresis:** risk-on < 0.95, early-warning 0.95–1.00, risk-off ≥ 1.00; re-risk only after the smoothed ratio drops back under 0.95. Tune the smoothing window (5 vs 10 day) and the 0.95 arming level in your existing sweep.
3. **Combine with your QQQ EWMA realized-vol trigger as an OR-gate** to cover the 2022-style slow bear that the term structure misses. Benchmark: if a backtest shows the slope-only gate stayed >90% risk-on through calendar-2022 while drawdown exceeded ~20%, that is the signal to require the realized-vol OR-condition.
4. **Validate fidelity once:** for a sample period, compute the actual VX1/VX2 slope from CBOE contract CSVs and measure how often it disagrees with your cash signal at your chosen threshold. If disagreement at the monthly decision points is materially above ~7–10%, shift your cash threshold from 1.0 toward 0.90.
5. **Do NOT buy VIX futures-options data.** It is the one expensive dataset and is irrelevant to slope measurement. Do not pay for continuous-futures vendors (Portara/CQG) either unless you later need precise intraday roll-yield P&L.

**Thresholds that would change the recommendation:** If your backtest shows the smoothed VIX/VIX3M gate adds no drawdown reduction versus your realized-vol trigger alone, drop it and keep the realized-vol gate (simpler). If it shows the gate whipsaws the monthly allocation more than ~2–3 times/year, widen the hysteresis band or lengthen the smoothing window.

## Caveats
- **The slope is a de-risking gate, not a forecaster.** It confirms stress, often after the first leg down; expect it to reduce, not prevent, drawdowns.
- **2022 blind spot:** term-structure signals structurally miss slow, rate-driven grind-downs where VIX3M rises with VIX. This is the single biggest risk to relying on the slope alone.
- **No published clean correlation** between the cash VIX/VIX3M ratio and the tradeable VX1/VX2 basis exists; the "~93% agreement / ~7% disagreement" characterization comes from a single credible practitioner source (Harbourfront/Relative Value Arbitrage), corroborated by contango-frequency figures across many sources, not from peer-reviewed work.
- **Cash ratio reads contango slightly too generously** (spot VIX has no roll premium); the ~0.90–0.95 practitioner threshold, not 1.0, is the empirically better contango/backwardation divide for matching the futures curve.
- **History-start dates:** VIX3M (Dec 2007) covers 2012; VIX9D (2013) and VIX6M (2014) do not — verify exact CSV start dates on CBOE before relying on them for early backtest years.
- **Simon & Campasano holding-period discrepancy:** the primary paper uses a 9-business-day max hold with 0.10/0.05 roll thresholds; widely repeated "5 trading days" figures come from secondary summaries.
- **Source mix:** academic papers (Simon & Campasano, Johnson, Cheng) are high quality; many threshold conventions and frequency stats come from reputable practitioner blogs (Six Figure Investing, Volatility Made Simple, Macroption, Harbourfront, QuantVPS, Eco3min) and should be re-verified in your own backtest rather than taken as ground truth.