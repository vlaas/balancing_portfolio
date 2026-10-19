# Specification: execution robustness — does the winners' edge survive when they trade and at what price?

Repo: `vlaas/balancing_portfolio` · baseline commit: `9c649ed` (report provenance
merged; 1289 tests green) · status: **implemented** (branch `execution-robustness`,
per-phase commits; 1307 tests green) — all four VT rows read TIMING-FRAGILE and
FILL-ROBUST; verdict `notes/execution-verdict.md`; net15 / λ / 2012 follow-ups
pre-registered in §15 (branch `execution-followups`) ·
inputs: `specs/top_strategies_2021.json` (the four 2021 winners + SPY, as run in
`simulation/top/top2021/results.md`), REBALANCE_SPEC §7.2 ("phase luck").

## 1. Goal

Every number the winners carry comes from a backtest that trades **on one day** —
the last trading day of each month — and **at one price** — that day's close, the
same close the signal reads. A person running the machine does neither exactly.
This spec measures how much of the winners' edge over SPY survives:

1. **Timing** — the monthly session (deposit + rebalance) moved by up to ±N trading
   days around the month-end, randomly per month (a luck distribution) and by a
   fixed offset every month (a systematic scan).
2. **Price** — every trade filled at an adverse intraday price derived from the
   day's bar, at a severity α that is calibrated, not the literal high/low.

Nothing is adopted and no winner changes. The outputs are distributions, a severity
curve and two read-outs per strategy (§10).

## 2. What is already true at `9c649ed` (measured on this clone)

### 2.1 The engine trades on one day at one price

- The monthly contribution arrives on every `is_rebalance_day` row — the last
  trading day of the month (`prices.py:129-133`) — and a strategy without a
  `rebalance` cadence rebalances on the same rows (`simulate.py:73-77, 108-116`).
  Nothing trades on any other day. Day 0 is always a full rebalance; the last row
  is never a trade day.
- Fills, sizing and valuation all use one column per symbol, the adjusted close
  (`simulate.py:120-170`); the loader reads only `time,close` (`prices.py:32-43`).
- `Cadence.offset` moves whole periods, not days (`spec.py:207-221`); `sweep.py`
  expands Cartesian grids only and has no seed. Neither experiment is expressible
  in the existing grammar.

### 2.2 Intraday ranges dwarf the cost model

`tests/data/2026-08-24/unadjusted`, 2020-12-18 → 2026-08-24, basis points of the
close. Month-end = the 68 rows the machine trades on.

| sym | median (H−C)/C all / month-end | median (C−L)/C all / month-end | mean (H−C)/C month-end | mean (C−L)/C month-end | `cost_bps` |
|---|---|---|---|---|---|
| TQQQ | 135 / 130 | 200 / 188 | 223 | 262 | 1.5 |
| BTAL | 66 / 53 | 58 / 66 | 65 | 75 | 6 |
| KMLM | 35 / 43 | 36 / 25 | 59 | 34 | 6 |
| DBMF | 31 / 33 | 38 / 29 | 59 | 44 | 2.5 |
| SPY | 32 / 31 | 49 / 47 | 58 | 68 | 0.7 |
| BIL | ~1 | ~1 | ~1 | ~1 | 0.5 |

OHLC is present in every root's `unadjusted/` (and in gross roots' `adjusted/`).
One adjustment factor covers the whole bar (max |ln(adjX/X) − ln(adjC/C)| = 4.9e-8
for TQQQ, ≤ 7e-10 elsewhere), so the scale-free ratios H/C and L/C from
`unadjusted/` apply exactly to the adjusted close of any root that has the twin.
Zero-range bars exist on thin days (BTAL 254 in 2011–2018, KMLM 68, DBMF 78).

### 2.3 The baseline being perturbed

`uv run main.py --spec specs/exec_top_2021.json` on `data/` (commit `0ffe674`),
2020-12-18 → 2026-10-19, 1464 trading days, 70 month-ends (first at row 8, last 13
rows before the end). Identical to the five matching columns of
`simulation/top/top2021/results.md`.

| | B50K50 | B75D25 | B75K25 | flag BIL50+BTAL50 | SPY |
|---|---:|---:|---:|---:|---:|
| CAGR (TWR) | +19.47 % | +17.26 % | +17.20 % | +16.82 % | +14.60 % |
| XIRR | +19.78 % | +18.22 % | +17.92 % | +18.59 % | +16.55 % |
| Max drawdown | −20.75 % | −18.81 % | −18.82 % | −18.03 % | −23.98 % |
| Calmar | 0.94 | 0.92 | 0.91 | 0.93 | 0.61 |
| Turnover (1-sided, ann.) | 1.75 | 1.75 | 1.75 | 1.77 | 0.13 |

### 2.4 The lane — a deliberate deviation from CLAUDE.md §6

The user chose live `data/` (gross total return, through 2026-10-19), the lane of
`simulation/top/top2021/results.md`, over the net15 decision lane
(`tests/data/2026-08-24-net15`). **Every number this spec produces is gross-TR and
not decision-grade under CLAUDE.md §6**; artefacts and the verdict say so. A net15
rerun is the same command with a different `--data` (and the spec's `end` dropped).
`specs/exec_top_2021.json` pins `"end": "2026-10-19"` so a later refresh of `data/`
cannot silently move the window.

## 3. Experiment 1 — rebalance-date jitter

- **Anchors.** The month-end rows `M_1 … M_K` of the loaded frame
  (`is_rebalance_day`), K = 70 on this lane.
- **Offsets.** Month k trades on row `M_k + d_k`, `d_k` an integer in `[−N, N]`
  **trading days** of the frame's calendar; `--days N`, default 10.
- **Clamp.** A row outside `[1, last − 1]` is clamped into it: day 0 stays the fixed
  initial investment, the last row stays valuation-only.
- **Order.** Rows are made strictly increasing in month order: a row at or before
  its predecessor moves to predecessor + 1. If that pushes past `last − 1` the
  calendar is infeasible and the tool raises. The number of contributions is
  therefore exactly K in every calendar.
- **Counts.** Clamps and bumps are counted per calendar and reported.
- **Mechanism.** The calendar replaces the frame's `is_rebalance_day` column; every
  strategy then runs unmodified. Deposit and rebalance move together — **assumed:**
  the investor holds one monthly session, deposit then rebalance. Only strategies
  without a `rebalance` cadence are accepted (all five qualify); the tool rejects
  others.
- **Random draws.** `--draws` calendars (default 500), each `d_k` drawn uniformly
  from `[−N, N]` by one `random.Random(--seed)` consumed in draw order, month order
  — so the first k draws of any run are the k draws of a shorter run.
- **Common random numbers.** Draw i is one calendar for all five strategies, so
  every comparison with SPY is paired.
- **Fixed-offset scan.** 2N + 1 deterministic calendars, `d_k = d` for every k,
  d ∈ [−N, N]. It separates a systematic turn-of-month effect from luck.
  **d = 0 is the canonical run** and must reproduce `main.py` exactly.

## 4. Experiment 2 — adverse intraday fills

### 4.1 The model: adverse fraction α of the one-sided range

    buy fill  = C · (1 + α · (H/C − 1))
    sell fill = C · (1 − α · (1 − L/C))

with H/C, L/C from the bar in `unadjusted/` and C the adjusted close the engine
already uses. α = 0 is the close; α = 1 is the literal high (buys) and low (sells).

Why this shape:

- **Bounded by the real bar.** No fill outside [L, H].
- **Respects where the close sits.** A buy on a day that closed at its high has no
  adverse room — no time of day was worse than the close.
- **One knob, interpretable.** Calibrate α against a random-time trader: with the
  price as Brownian motion run backwards from the close and the trade time uniform
  over the session, the q-quantile adverse deviation from the close is 0.405σ at
  q = 0.75 and 0.869σ at q = 0.90, while the expected one-sided maximum excursion
  (what H − C measures) is √(2/π)σ = 0.798σ. So **α = 0.5 ≈ the 75th-percentile
  fill — worse than three in four random times of day — on every trade**; α = 1 ≈
  the 90th percentile on every trade.

### 4.2 Levels

`--alpha` (default `0 0.25 0.5 1`): α = 0 the identity check; **0.25 mild; 0.5 the
headline "reasonable worst case"; 1 the literal-H/L bound**, reported only as a
bound — every trade at the day's extreme is not a scenario anyone lives.

### 4.3 Mechanics

- `cost_bps` stays on top, charged on the fill notional — the spread and the
  intraday path are different costs and the experiment is a stress, so both bite.
- Sizing (integer-share targets) and valuation stay at the close; the adverse fill
  is an immediate mark-to-market loss.
- Day 0's buys and every contribution buy fill adversely too.
- A bar missing from `unadjusted/` gets ratio 1 (fills at the close) and is counted.

### 4.4 Rejected alternatives

- **The literal high/low** — the user's exclusion; kept only as the α = 1 bound.
- **Volatility-based fills** `C·e^{±kσ_P}` with σ_P the Parkinson range estimate:
  not bounded by the bar, blind to where the close sits, and at q = 0.90 TQQQ's
  ≈ 211 bp overshoots its median one-sided range (≈ 135 bp) — it would hit the
  high most days.
- **Random fills inside [L, H] (Monte Carlo)** — per-trade luck averages out over
  ~70 sessions × several assets, so the p5 outcome is a far milder "worst" than the
  question asks; not built.

## 5. Engine change — `simulate(..., fill=None)`

`simulate(prices, strategy, config, fill=None)`; `fill(row, asset, delta) -> price`
is the execution price of the trade of `delta` shares of `asset` on `row`.

- `None` keeps today's arithmetic exactly (`price = row[asset]`); the goldens in
  `tests/test_main.py` are untouched.
- With a fill: cash, fee and the logged `price` / `amount` use the fill price; the
  affordability cap runs whenever `f[asset] > 0` **or** the buy fill exceeds the
  close (a zero-fee buy above the close could otherwise overdraw cash); targets,
  `total`, allocations and the end-of-day value stay at the close.
- Consequence: `traded_value`, `turnover` and `total_fees` in `stats.summary` are on
  fill notional when a fill is given.

This is an engine-semantics extension; its commit says so (CLAUDE.md §6).

## 6. `execution_report.py` — the tool

    uv run execution_report.py jitter --spec SPEC --data ROOT [--days 10] [--draws 500]
                                      [--seed 20261020] [--out DIR]
    uv run execution_report.py fills  --spec SPEC --data ROOT [--alpha 0 0.25 0.5 1]
                                      [--out DIR]

- Builds the bundle with `load_spec`/`build_bundle`, loads prices once with
  `load_prices` + `main.collect_indicators` (as `run_bundle` does), and runs
  `simulate` + `stats.summary` per calendar or α. The benchmark is the bundle's
  last strategy (`bundles.py` convention).
- `--out` defaults to `results/<spec stem>`. `jitter` writes `jitter.json`,
  `jitter.md`, `jitter_draws.csv` (one row per draw × strategy); `fills` writes
  `fills.json`, `fills.md`. JSON through `results_json._round` / `dumps`. The
  markdown is also printed.
- Each artefact records the command, the data root and the last commit that
  touched it (`git log -1 -- ROOT`), the window, the costs and the parameters
  (N, draws, seed, α levels). No timestamp and no HEAD sha, so a rerun at the same
  inputs is byte-identical.
- Metrics per run: `final_value`, `cagr`, `xirr`, `max_drawdown`, `calmar`,
  `sharpe`, `total_fees`; for `fills` also slippage $ = Σ |fill − close| · shares
  and slippage bps of close notional, overall and per symbol × side.

## 7. Tests

`tests/test_simulate.py` (engine) and new `tests/test_execution.py` (tool). Tests
never read live `data/`; tool tests use the frozen gross root
`tests/data/2026-08-24` with the spec's `end` replaced by `2026-08-24`.

- **X1** An identity fill is frame-equal to `fill=None` on real data with a cost
  map (all three frames).
- **X2** Hand-computed adverse buy and sell on a synthetic frame with fees: logged
  price = fill, amount = shares × fill, fee = amount × rate, cash ledger exact.
- **X3** Zero fees, buy fill above the close: the affordability cap binds and cash
  never goes negative.
- **X4** Calendar: N = 0 is the identity; exactly K rows, strictly increasing;
  |shift| ≤ N except counted clamps / bumps; first-month clamp to row 1; a
  collision bumps; an infeasible tail raises.
- **X5** Draws: deterministic per seed; prefix property; all 2N + 1 offsets occur.
- **X6** `jitter` on the frozen root: scan d = 0 equals `run_bundle` for all five
  (`final_value`, `cagr`, `max_drawdown`); the payload is reproducible.
- **X7** `fills` on the frozen root: α = 0 equals `run_bundle` with zero slippage;
  every α > 0 lowers each VT row's final value; H/C ≥ 1 ≥ L/C on every row.
- **X8** CLI writes the five artefacts with the documented names.

## 7a. Docs

`notes/execution-verdict.md` (the read, §9–§10). `docs/STRATEGY_DEVELOPMENT.md`
gets one paragraph on `fill` next to the cost model. The winners file is **not**
edited — gross-lane numbers do not belong in it.

## 8. Run protocol

1. Phase 0 commit: this spec + `specs/exec_top_2021.json` — the pre-registration;
   no experiment has run.
2. Phase 1 commit: the `fill` hook + X1–X3.
3. Phase 2 commit: `execution_report.py` + X4–X8 + docs.
4. Phase 3 commit: the two runs below, artefacts + verdict + checklist + errata.

```
uv run execution_report.py jitter --spec specs/exec_top_2021.json --data data \
  --days 10 --draws 500 --seed 20261020 --out results/exec_top_2021
uv run execution_report.py fills --spec specs/exec_top_2021.json --data data \
  --alpha 0 0.25 0.5 1 --out results/exec_top_2021
```

Every quoted number names its basis: gross TR, `data/` @ `0ffe674`, the spec's
`cost_bps` map, `cash_yield` 0.03.

## 9. Read protocol

- **Jitter, per strategy:** the canonical value and its percentile in the draw
  distribution; mean, sd, min, p5, p25, p50, p75, p95, max of CAGR, XIRR, max
  drawdown and Calmar; paired P(beats SPY) per metric; P(best of five) on CAGR and
  Calmar; the scan table (metric by d).
- **Fills:** strategy × α table (CAGR, XIRR, max drawdown, Calmar, Sharpe, fees,
  slippage $ and bps, Δ vs α = 0, edge over SPY at the same α); the break-even α of
  each VT row's CAGR and Calmar edge (linear between levels; "> max α" if it never
  closes); slippage bps per symbol × side at each α.

## 10. Read-outs and predictions — frozen at the pre-registration commit

### 10.1 Read-outs (no adoption follows from either)

- **TIMING-ROBUST** iff the canonical Calmar sits inside the draws' p10–p90 **and**
  paired P(Calmar > SPY) ≥ 0.90; otherwise **TIMING-FRAGILE**.
- **FILL-ROBUST** iff the CAGR edge over SPY is still > 0 at α = 0.5; otherwise
  **FILL-FRAGILE**, quoting the break-even α.

### 10.2 Predictions

Back-of-envelope behind the fill predictions: turnover 1.75 one-sided ⇒ ≈ 3.5× the
portfolio traded per year, about half of it TQQQ (≈ 120 bp per side at α = 0.5
on mean month-end ranges) and half the sleeve (≈ 30 bp) ⇒ ≈ 2.6 pp/yr of drag.

1. **Jitter P1** — every VT row's canonical Calmar sits inside its p10–p90.
2. **Jitter P2** — paired P(Calmar > SPY) ≥ 0.90 for every VT row (edge ≈ 0.3).
3. **Jitter P3** — paired P(CAGR > SPY) ≥ 0.90 for B50K50 (edge 4.9 pp) and
   ≥ 0.75 for the other three (edges 2.2–2.7 pp).
4. **Jitter P4** — SPY's CAGR range across draws is < 0.3 pp: fully invested, its
   TWR barely sees the deposit day.
5. **Jitter P5** — d = 0 is neither the best nor the worst scan point on Calmar for
   any VT row (month-end is not special).
6. **Fills P6** — at α = 0.5 every VT row loses 1.5–3.0 pp of CAGR; SPY < 0.1 pp.
7. **Fills P7** — break-even α of the CAGR edge: B50K50 in [0.6, 1.0]; B75D25,
   B75K25 and the flag variant in [0.3, 0.6]. So B50K50 reads FILL-ROBUST and the
   other three FILL-FRAGILE.
8. **Fills P8** — the Calmar edge survives α = 0.5 for every VT row (max drawdown
   barely moves).
9. **Fills P9** — at α = 1 the realised slippage bps per symbol × side is within
   ×0.5–×1.5 of §2.2's month-end mean range.

## 11. Honest limitations

- **Gross lane** (§2.4): not decision-grade; the net15 lane would shave every row,
  the BTAL-heavy ones most.
- **One window, 2020-12 → 2026-10**: ~70 sessions. The jitter distribution is luck
  *within this path*, not across market histories.
- **α is a stress, not an estimate.** A random-time trader's expected adverse
  deviation is zero; α > 0 on every trade is a deliberately pessimistic
  conjunction. α = 0.5 is "unlucky every time", not "typical".
- **The signal still reads the trade day's close.** A real session that trades
  intraday computes its signal from an earlier price; that look-ahead is untouched
  (next-day execution is out of scope).
- **Cost overlap.** H and L are trade prints and already contain bid-ask bounce;
  charging `cost_bps` on top double-counts part of the spread — conservative by
  construction.
- **Uniform offsets.** Real sessions cluster (e.g. on weekends' eves); uniform is
  the agnostic choice.

## 12. Deliberately not in scope

Jitter × fills combined; next-day-open or next-close execution lag; jittering the
start date (KMLM's first bar is 2020-12-18); any change to a winner; `sweep.py`
integration; a net15 rerun (one command away, §2.4).

## 13. Acceptance checklist

- [x] Pre-registration commit: this spec + `specs/exec_top_2021.json`, before any run
- [x] `simulate(..., fill=None)` per §5; goldens untouched; commit names the semantics change
- [x] `execution_report.py` with `jitter` and `fills` per §3, §4, §6; deterministic
- [x] Tests X1–X8 green; suite count > 1289 (1307)
- [x] `docs/STRATEGY_DEVELOPMENT.md` paragraph on `fill`
- [x] Artefacts `results/exec_top_2021/{jitter.json,jitter.md,jitter_draws.csv,fills.json,fills.md}` committed together
- [x] `notes/execution-verdict.md` per §9–§10, every number labelled gross TR
- [x] Errata (below) for every deviation found while implementing

## 14. Errata (found during implementation)

1. **KMLM has no bar on 80 sessions of the lane** (2020-12-21 → 2022-01-19, thin
   first year: 6 in 2020, 71 in 2021, 3 in 2022), in `adjusted/` and `unadjusted/`
   alike. §2.2 did not mention it. The loader already forward-fills KMLM's close
   over those days, so the engine trades it at the carried close. §4.3's rule
   (ratio 1, counted) applies unchanged and `fills.md` reports `KMLM 80`. Jitter
   sessions can land on these days in any draw; that is existing engine behaviour,
   not new.
2. **§11 omitted a small-account artefact**, and it decides two predictions
   (P4, the SPY half of P6). With $500 initial capital and $500 a month in whole
   shares, the time-weighted return counts the first year as much as the last, and
   the first year carries a 9.1 % mean cash share for SPY. Contribution timing and
   per-buy slippage therefore move SPY's CAGR. Verified with `initial_capital`
   $100,000:
   - SPY's α = 0.5 Δ CAGR is −0.018 pp, against −0.443 pp at $500.
   - Its fixed-offset scan range is 0.020 pp, against 0.427 pp.
   - B50K50's Δ CAGR barely changes, −1.99 pp against −2.11 pp: the VT drag is
     turnover, not account size.
3. **§2.2's BIL "~1"** rounds the measured month-end means of 0.8 bp (H−C) and
   0.5 bp (C−L). P9 is read against those values.
4. **Tests beyond §7.**
   - Two additions: a cadence-rejection test (`jitter` refuses a strategy with a
     `rebalance` cadence) and a unit test for the break-even interpolation.
   - X6's reproducibility is checked as the prefix property: the same seed with
     fewer draws gives the identical per-draw rows.
   - The byte-identity of the committed artefacts was verified by rerunning both
     commands into the same `--out` and diffing. There is no test for it, because
     tests do not read live `data/`.

## 15. Follow-up runs — pre-registered after the verdict (branch `execution-followups`)

The verdict (`notes/execution-verdict.md` §6) left two residuals: the numbers are
gross, and the fixed-offset scan's phase pattern has no explanation. Both are run
here with the unchanged tool. No code changes and no adoption follow from any of
them: λ 0.94 is a diagnostic probe, not a candidate. Every run uses the decision
root `tests/data/2026-08-24-net15`, the same costs (`cost_bps` map, `cash_yield`
0.03), and `--days 10 --draws 500 --seed 20261020`.

### 15.1 Runs

| id | spec | lane | rows | modes |
|---|---|---|---|---|
| F1 | `specs/exec_top_2021_net15.json` | 2020-12-18 → 2026-08-24, 68 sessions | the five rows of §2.3 | `jitter`, `fills` |
| F2 | `specs/exec_lam94_2021_net15.json` | same as F1 | the four VT rows at `lam` 0.94, plus SPY | `jitter` |
| F3 | `specs/exec_flag_2012_net15.json` | 2012-01-03 → 2026-08-24 | flag variant at λ 0.80 and 0.94, plus SPY | `jitter` |

- **Specs.** F1 is `exec_top_2021.json` with `end` dropped; the root is frozen.
  F2 and F3 differ from F1 only in `vol.lam`, the labels (suffix `lam0.94`) and,
  for F3, `start`.
- **F3 is the flag variant only.** KMLM starts 2020-12-18 and DBMF 2019-05-08, so
  only the BIL + BTAL sleeve reaches back to the repo's 2012 lane start.
- **F1 and F2 run on identical calendars.** `draw_offsets` depends only on the
  month count, N, the draw count and the seed, so draw i is the same calendar in
  both. The comparison is paired by construction; checked as identical `clamps` /
  `bumps` columns.

```
uv run execution_report.py jitter --spec specs/exec_top_2021_net15.json \
  --data tests/data/2026-08-24-net15 --days 10 --draws 500 --seed 20261020
uv run execution_report.py fills --spec specs/exec_top_2021_net15.json \
  --data tests/data/2026-08-24-net15 --alpha 0 0.25 0.5 1
uv run execution_report.py jitter --spec specs/exec_lam94_2021_net15.json \
  --data tests/data/2026-08-24-net15 --days 10 --draws 500 --seed 20261020
uv run execution_report.py jitter --spec specs/exec_flag_2012_net15.json \
  --data tests/data/2026-08-24-net15 --days 10 --draws 500 --seed 20261020
```

Artefacts go to `results/<spec stem>/`, the tool's default.

### 15.2 Canonical baselines (`main.py`, measured before any run)

| | B50K50 | B75D25 | B75K25 | flag | SPY |
|---|---:|---:|---:|---:|---:|
| F1 CAGR / Calmar / max DD | +18.63 % / 0.89 / −20.88 % | +16.48 % / 0.87 / −18.94 % | +16.41 % / 0.87 / −18.97 % | +16.45 % / 0.91 / −18.12 % | +14.67 % / 0.62 / −23.68 % |
| F2 (λ 0.94) CAGR / Calmar | +16.05 % / 0.77 | +13.98 % / 0.76 | +13.79 % / 0.78 | +14.15 % / 0.79 | same as F1 |
| F1 → F2 turnover | 1.72 → 0.83 | 1.73 → 0.84 | 1.72 → 0.83 | 1.74 → 0.85 | 0.13 |

F3, 2012 lane: flag λ 0.80 +20.08 % / 0.82 / −24.44 %; flag λ 0.94 +18.54 % /
0.71 / −25.95 %; SPY +14.60 % / 0.43 / −33.74 %.

**Disclosure.** Phase 2's smoke runs used `tests/data/2026-08-24`, the gross twin
of F1's window:
- `fills` at α = 0 and 1. The F1 fill predictions below lean on it.
- `jitter` at ±2 days with 20 draws.

No ±10-day jitter has been run on any 2026-08-24 root, and nothing has been run
on the 2012 lane.

### 15.3 Read-out added for F2 / F3 — the amplifier test

Per VT row, compare λ 0.94 with λ 0.80 on the same calendars (F2 against F1; F3's
two rows against each other):
- *s* = sd of CAGR across draws, ratio λ 0.94 / λ 0.80;
- *r* = range (max − min) of the fixed-offset scan's Calmar, same ratio.

The read-out:
- **AMPLIFIER-CONFIRMED** if *s* ≤ 0.70 **and** *r* ≤ 0.70 for at least 3 of F2's
  4 rows;
- **AMPLIFIER-REJECTED** if *s* ≥ 0.90 **and** *r* ≥ 0.90 for at least 3 of 4;
- **INCONCLUSIVE** otherwise.

F3's single pair is reported alongside, as corroboration only.

**PHASE-PERSISTS** (F3, flag λ 0.80) iff the scan's best-Calmar offset is in
[−5, −1] **and** its worst in [+2, +8]. These are the bands every row of the
gross run fell in (verdict §2). Otherwise **PHASE-LOCAL**.

### 15.4 Predictions

1. **F1 jitter:** all four rows TIMING-FRAGILE, with P(Calmar > SPY) in
   [0.75, 0.90]. Every row's scan has its best Calmar offset in [−5, −1] and its
   worst in [+2, +8]. 68 of the gross run's 70 sessions are shared, and net15 only
   rescales distributions.
2. **F1 fills.**
   - B50K50 stays FILL-ROBUST, with an α = 0.5 CAGR edge of +1.5 to +2.8 pp and a
     break-even α ≥ 0.9.
   - B75D25 and B75K25 turn FILL-FRAGILE: α = 0.5 edge in [−0.6, +0.1] pp,
     break-even α in [0.35, 0.55].
   - The flag variant is borderline: α = 0.5 edge in [−0.3, +0.6] pp, break-even α
     in [0.4, 0.65].

   Basis: the canonical net15 edges are 1.7–2.2 pp narrower than the gross ones,
   and the α-drag is about 2 pp per 0.5.
3. **F2: AMPLIFIER-CONFIRMED.** A five-day-memory σ re-reads a different weight
   each day, while a seventeen-day one barely moves. The scan pattern flattens with
   it.
4. **F3, timing:**
   - flag λ 0.80's CAGR sd across draws ≤ 0.70 × its F1 value (≈ 170 sessions
     average luck better than 68);
   - flag λ 0.80 reads TIMING-ROBUST (Calmar 0.82 against SPY's 0.43);
   - the λ 0.94 / λ 0.80 pair has *s* ≤ 0.70.
5. **F3, phase:** PHASE-LOCAL. The 2021+ pattern does not reproduce over 2012–2026.
   This is a low-confidence prediction.

### 15.5 Errata and results

Recorded in `notes/execution-verdict.md` §7 after the runs. This section stays as
pre-registered.
