# Verdict: the winners' risk is *when* they trade, not *at what price*

EXECUTION_ROBUSTNESS_SPEC, implemented on branch `execution-robustness` from
`9c649ed`. Spec and run input frozen at `816ac02` before any run; `fill` hook at
`7be806a`; tool `execution_report.py` at `31b07bf`; tests 1289 → 1307. Artefacts in
`results/exec_top_2021/`, reproduced byte for byte by a second run.

**Basis: gross TR, live `data/` @ `0ffe674`, 2020-12-18 → 2026-10-19 (1464 days,
70 monthly sessions). The user chose this lane, and under CLAUDE.md §6 it is not
decision-grade.** Costs: the spec's `cost_bps` map (TQQQ 1.5, BTAL 6, DBMF 2.5,
KMLM 6, SPY 0.7, BIL 0.5) and `cash_yield` 3 %. No winner and no parameter moves.

## 1. Read-outs (§10.1)

| strategy | timing (±10 trading days) | fills (α = 0.5) |
|---|---|---|
| B50K50 | **TIMING-FRAGILE**: P(Calmar > SPY) 0.868 | **FILL-ROBUST**: edge +3.21 pp, survives the α = 1 bound |
| B75D25 | **TIMING-FRAGILE**: 0.826 | **FILL-ROBUST**: edge +0.82 pp, break-even α 0.72 |
| B75K25 | **TIMING-FRAGILE**: 0.818 | **FILL-ROBUST**: edge +0.87 pp, break-even α 0.74 |
| flag BIL50+BTAL50 | **TIMING-FRAGILE**: 0.816 | **FILL-ROBUST**: edge +0.80 pp, break-even α 0.76 |

All four VT rows fail the timing read-out on its paired clause (P(Calmar > SPY)
≥ 0.90), not on its band clause: each canonical Calmar sits inside its own p10–p90.

## 2. Timing: an uncertainty about as large as the edge itself

Each month's session moves by a uniform offset in ±10 trading days. There are 500
draws, and each draw uses one calendar for all five rows.

| | canonical CAGR | median | p5 | sd | canonical max DD | median | p5 | P(CAGR > SPY) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B50K50 | +19.47 % | +18.59 % | +14.50 % | 2.51 pp | −20.75 % | −21.71 % | −31.26 % | 0.954 |
| B75D25 | +17.26 % | +16.60 % | +12.68 % | 2.50 pp | −18.81 % | −20.70 % | −29.31 % | 0.814 |
| B75K25 | +17.20 % | +16.41 % | +12.38 % | 2.55 pp | −18.82 % | −20.46 % | −29.31 % | 0.790 |
| flag | +16.82 % | +16.28 % | +12.57 % | 2.41 pp | −18.03 % | −21.31 % | −28.49 % | 0.786 |
| SPY | +14.60 % | +14.38 % | +14.19 % | 0.13 pp | −23.98 % | −23.91 % | −24.20 % | · |

- **The published month-end numbers are on the lucky side.** Canonical CAGR sits
  at the 58th–65th percentile of the draws. Canonical max drawdown is shallower than
  61–94 % of draws; for the flag variant, −18.0 % is the 94th percentile. A fair
  quote for a session held "around month-end" is the median: CAGR about 0.5–0.9 pp
  lower, max drawdown about 1–3.3 pp deeper, Calmar 0.77–0.85 instead of 0.91–0.94.
- **The edge over SPY mostly survives.** B50K50 beats SPY on CAGR in 95 % of
  draws. The other three do so in 79–81 %, and all four beat it on Calmar in
  82–87 %. One timing path in five to seven loses to SPY on risk-adjusted terms.
- **The fixed-offset scan shows a phase pattern, spread across years.**
  - Sessions 1–5 days *before* month-end score Calmar 0.82–1.34.
  - Sessions 1–8 days *after* score 0.50–0.75. At d = +2…+8 the CAGR edge over SPY
    is gone for B75D25, B75K25 and the flag variant.
  - It is not one episode. Taking B50K50 by calendar year, d = +5 trails d = 0 in
    every year but 2022, and d = −4 leads it in every year but 2025.
  - **Not actionable.** It is one path of 70 sessions, and "trade four days before
    month-end" would be fitted to it.
  - A likely amplifier is the λ = 0.80 EWMA: about five days of memory, so the
    target weight depends strongly on the day it is read. A falsifier is the same
    jitter run with a slower λ, or on a longer lane.

## 3. Fills: a real cost, not a verdict-changer

Buys fill at C·(1 + α(H/C − 1)) and sells at C·(1 − α(1 − L/C)), with
`cost_bps` on top.

| | Δ CAGR α = 0.25 | α = 0.5 | α = 1 | slippage bp of notional, α = 0.5 | CAGR edge α = 0.5 / 1 | Calmar edge α = 0.5 / 1 |
|---|---:|---:|---:|---:|---:|---:|
| B50K50 | −1.06 pp | −2.11 pp | −4.20 pp | 55.0 | +3.21 / +1.40 pp | +0.215 / +0.103 |
| B75D25 | −1.12 pp | −2.28 pp | −4.45 pp | 56.5 | +0.82 / −1.07 pp | +0.162 / +0.022 |
| B75K25 | −1.11 pp | −2.18 pp | −4.30 pp | 56.4 | +0.87 / −0.96 pp | +0.183 / +0.060 |
| flag | −0.90 pp | −1.87 pp | −3.71 pp | 49.5 | +0.80 / −0.76 pp | +0.200 / +0.081 |
| SPY | −0.27 pp | −0.44 pp | −0.72 pp | 27.0 | · | · |

- **The drag is linear in α**, at about 2 pp of CAGR per 0.5 of α.
- **α = 0.5 means paying about 50–57 bp per traded dollar**, roughly ten to forty
  times the cost model. It still leaves every VT row ahead of SPY on both CAGR and
  Calmar.
- **The Calmar edge survives even the literal high/low.** On CAGR, only B50K50
  survives it.
- **TQQQ carries the slippage:** 70 bp on buys and 95 bp on sells at α = 0.5. The
  sleeve legs cost 18–39 bp.
- **Practical reading:** filling worse than three in four random times of day on
  every trade costs about 2 pp a year. Any execution habit better than "unlucky
  every time" costs proportionally less.

## 4. SPY's sensitivity is a small-account artefact

SPY moved more than predicted: a CAGR range of 0.73 pp across draws, and −0.44 pp
at α = 0.5 on only $96 of total slippage. The cause is the $500 start with $500 a
month in whole shares. The time-weighted return counts the first, tiny-portfolio
year (mean cash share 9.1 %) as much as the last. **Verified:** with
`initial_capital` $100,000, SPY's α = 0.5 Δ CAGR falls to −0.018 pp and its scan
range to 0.020 pp. B50K50's is −1.99 pp, against −2.11 pp at $500. So the VT drag
is turnover, not account size.

## 5. Predictions (§10.2) — 4 of 9 held cleanly

| # | prediction | outcome |
|---|---|---|
| P1 | canonical Calmar inside p10–p90 | ✅ percentiles 0.65 / 0.70 / 0.69 / 0.81 |
| P2 | P(Calmar > SPY) ≥ 0.90 | ❌ 0.868 / 0.826 / 0.818 / 0.816 |
| P3 | P(CAGR > SPY) ≥ 0.90 for B50K50, ≥ 0.75 for the rest | ✅ 0.954; 0.814 / 0.790 / 0.786 |
| P4 | SPY CAGR range < 0.3 pp | ❌ 0.73 pp, the §4 artefact |
| P5 | d = 0 neither best nor worst on Calmar | ✅ the best is d = −4 for every row, the worst +4…+7 |
| P6 | α = 0.5 costs VT 1.5–3.0 pp, SPY < 0.1 pp | ½: VT −1.87…−2.28 ✅; SPY −0.44 ❌ (§4) |
| P7 | break-even α: B50K50 in [0.6, 1.0], the rest in [0.3, 0.6] | ❌ B50K50 > 1, the rest 0.72–0.76; more robust than predicted |
| P8 | Calmar edge survives α = 0.5 | ✅ +0.16…+0.22, and it survives α = 1 |
| P9 | α = 1 slippage within ×0.5–×1.5 of the §2.2 means | ½: five priced symbols 0.62–1.05 ✅; BIL sells 0.0 bp against a 0.5 bp mean ❌ (tick-bound) |

Both misses that matter point the same way. P2 says timing is a bigger risk than
expected. P7 says price is a smaller one.

## 6. Residuals

1. **The phase pattern (§2).** Is it the fast EWMA, turn-of-month seasonality, or
   this path's luck? This needs a longer lane (the 2012 net15 lane, or the
   synthetic root as a falsifier only) and a λ comparison. No offset should be
   adopted from this window.
2. **The net15 rerun:** the same two commands with `--data
   tests/data/2026-08-24-net15` and the spec's `end` dropped. It would make these
   numbers decision-grade.
3. **Jitter × fills combined** was left out of scope. The two effects are close to
   additive in kind (variance against bias), but unmeasured together.
