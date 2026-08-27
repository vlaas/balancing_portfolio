# Specification: rebalance cadence sweep

Repo: `vlaas/balancing_portfolio` · baseline commit: `4cecdc0` (blend verdict, 420
tests green) · status: implemented on branch `rebalance-cadence` (443 green); five
lanes run on `tests/data/2026-08-20-net15`; verdict §7.

## 1. Goal

Every result in this research line — the VT plateau, the gate advantage, the blend
verdict, the three winners — is a *monthly* result, because the engine has exactly one
trade calendar: the last trading day of each month, hard-wired in `prices.load_prices`
and doubling as the contribution day. The question "how does the machine change when it
looks at the market more or less often?" has never been asked. It matters in both
directions: faster cadence is where a vol-targeting rule is supposed to earn its keep
(de-risk *into* a spike, not a month after it) at the price of turnover; slower cadence
is the obvious cost saver and the Shannon-demon folklore says it forfeits harvest.

Daily rebalancing is out of scope: daily close-to-close data makes a daily rule a
pure function of one bar's noise and the integer-share engine would spend most days
trading one share. Weekly through quarterly is the range.

Three parts:

1. **`Cadence`** — a per-strategy rebalance calendar, weekly to quarterly, with phase.
2. **Contributions decoupled from rebalances** — the monthly deposit still arrives on
   every month-end and is invested that day; only *re-targeting* follows the cadence.
3. **Five sweep lanes** over the three winners and their pure-BTAL ancestor.

## 2. Engine — `strategy.Cadence`, `simulate.simulate`

### 2.1 `Cadence(unit, every=1, offset=0)` — `strategy.py`

`unit ∈ {"weeks", "months"}`, `every ≥ 1`, `0 ≤ offset < every`. A period index is
attached to every date — weeks since Monday 1970-01-05, or `year·12 + month` — and the
strategy rebalances on the **last trading day of every period whose index ≡ offset
(mod every)**. The last row of a frame is never a rebalance day (a valuation day, the
same rule `is_rebalance_day` has).

Two deliberate choices:

- **Anchored to the calendar, not to the run's start.** Two windows that overlap
  trade on the same days, so sensitivity windows and the holdout compare like with
  like. `year·12 + month` makes `offset 0` the calendar's own period end for every
  divisor of 12: `months: 3` at offset 0 is Mar/Jun/Sep/Dec, offset 1 is
  Jan/Apr/Jul/Oct, offset 2 is Feb/May/Aug/Nov. Weekly phase is relative to the fixed
  epoch — stable, but not "the first Friday of anything".
- **`Cadence("months")` is the month-end column, bit for bit** (test). A strategy
  without a cadence (`rebalance=None`, every existing strategy) uses
  `prices["is_rebalance_day"]` exactly as before — `load_prices` is untouched, the
  column keeps its name and meaning, and the goldens cannot move.

`Strategy.rebalance: Cadence | None = None` is the hook; `simulate` derives the mask
from `prices["date"]` per strategy.

### 2.2 Contribution-only days — `simulate.py`

The monthly contribution is a real-world constraint, not a tunable: it arrives on every
`is_rebalance_day` row regardless of cadence. On a month-end that is **not** a cadence
day the engine now runs a **contribution-only** trade: it calls `balance(ctx)` and
`buy_cap` exactly as on a rebalance day, but the budget is the day's deposit instead of
the whole portfolio and every target is anchored at the current holdings —

```
full rebalance:      target[a] = 0        + floor(total · w[a] / p[a])
contribution-only:   target[a] = shares[a] + floor(flow  · w[a] / p[a])
```

— with the identical gate cap and reroute afterwards (`remaining` is measured on the
*increment* over the base). Consequences:

- Buys only, never a sell: holdings drift until the next cadence day.
- The gate still bites: a closed gate sends the deposit to the sleeve in sleeve
  proportion, as on a rebalance day; `contribution_exempt` reduces to its own cap.
- The allocations frame records every trade day (rebalance or contribution), so
  `avg_misallocation` and `exposure` on a quarterly strategy see the drift a monthly
  one never accumulates. That is the point, not a bug.
- With `rebalance=None` the contribution branch never runs (`base = 0`, `budget =
  total` on every acting day): the default path is the old code with two renamed
  locals, which is why 420 tests stayed green without touching a snapshot.

The alternative — parking deposits in cash until the next rebalance — was rejected
because it would make a quarterly result partly a cash-drag result, and because nobody
runs a real account that way. It is not offered as an option (CLAUDE.md §2).

## 3. Grammar — `spec.py`, `sweep.py`

An optional `rebalance` key on either strategy type:

```json
"rebalance": { "weeks": 2 }
"rebalance": { "months": 3, "offset": 2 }
```

Exactly one of `weeks` / `months` (a positive integer), optional `offset` in
`[0, every)`; every other key is a `ValueError` with its JSON path. Absent means the
engine default and adds nothing to the label, so every existing spec, label and slug is
unchanged. Present, the auto-label gets ` rb 2w` / ` rb 3m+2` after the gate suffix
(`spec.rebalance_str`, shared with sweep `params` like `gate_str`/`safe_str`), and the
normalised spec embeds `{"months": 3, "offset": 2}` with the default offset filled in.

In a sweep template `rebalance` is a **categorical** dimension: a grid of objects and
`null` (null = default monthly, deleting the key per the optional-key rule). No
neighbourhood, no edge flag — the cadences are not on a numeric line (a week is not
"one step" from a month, and phases are not ordered). `robust_score` for a cadence
point is therefore `min(full, sensitivity median, holdout test)`; in a lane that also
grids a numeric parameter the neighbour minimum re-enters and the absolute scores are
not poolable with the pure cadence lane (same rule as the blend sweep).

## 4. Tests — `tests/test_rebalance.py` (23 tests, all green)

- **Masks**: weekly marks Sundays of a Monday-anchored synthetic calendar; the two
  phases of `weeks: 2` partition the weekly mask; `months: 3` offsets 0/1/2 select
  Mar-Jun-Sep / Jan-Apr-Jul-Oct / Feb-May-Aug-Nov month-ends; the last row is never
  True; a later start yields the same dates (calendar anchoring); bad unit or
  `offset ≥ every` assert.
- **Default equivalence**: `Cadence("months").mask(dates) == is_rebalance_day` on the
  golden calendar; a 50/50 with `rebalance=Cadence("months")` produces frames
  `assert_frame_equal` to the plain one (curve, trades, allocations).
- **Quarterly engine run** on `tests/data`: deposits on every month-end, sells only on
  quarter-ends, every month-end is an allocations row.
- **Contribution-only day**, synthetic: a doubled-and-doubled asset at 80 % of the book
  is *not* sold; the deposit buys `floor(50/40)=1` and `floor(50/10)=5`; the recorded
  allocation is the drifted one. With a closed gate the whole deposit goes to the open
  asset and cash ends at zero.
- **Grammar**: the four renderings, label suffix placement after the gate, absent key
  leaves label and spec untouched, six validation paths, sweep `params.rebalance`
  renders `["1w", null, "3m+1"]` and null removes the key.

## 5. Sweep specs

All on `tests/data/2026-08-20-net15`, tastytrade per-symbol base costs, `cash_yield`
3 %, objective Calmar, constraint max drawdown ≥ −50 %, windows identical to the blend
lanes they extend (so the `null` column reproduces the committed winners to the third
decimal: 0.856 / 0.859 / 0.890 full Calmar).

The cadence grid everywhere: `1w · 2w · 2w+1 · 1m (null) · 2m · 2m+1 · 3m · 3m+1 ·
3m+2`. Phases are in the grid because a slow cadence's result is a function of which
month-ends it happens to trade on, and a sweep that hid that would be lying.

| lane | spec | varies | points | out |
|---|---|---|---|---|
| primary | `sweep_rebalance_2021.json` | safe ∈ {B75K25, B75D25, B50K50} × gate ∈ {none, SMA200} × cadence | 54 | `results/sweep_rebalance_2021_net` |
| gross | same, `--cost-bps 0 --cash-yield 0.03` | | 54 | `…_2021_c00` |
| stress | same, `--cost-bps 20 --cash-yield 0.03` | | 54 | `…_2021_c20` |
| COVID | `sweep_rebalance_2019.json` | safe ∈ {BTAL, B75D25} × gate × cadence, windows from `sweep_blend_2019` | 36 | `results/sweep_rebalance_2019` |
| response | `sweep_rebalance_lam_2021.json` | B75D25 gated; λ ∈ {0.80, 0.90, 0.94, 0.97} × σ ∈ {0.20, 0.30} × cadence | 72 | `…_lam_2021_net` |
| floor | `sweep_rebalance_wmin_2021.json` | B75D25 gated; w_min ∈ {0, 0.1, 0.2, 0.3} × 6 cadences | 24 | `…_wmin_2021_net` |

Baselines in every lane: plain 50/50 and gated 50/50, each at 1w / 1m / 3m, and SPY —
the fixed-mix cadence effect (the Shannon question) read separately from the VT one.

## 6. Read protocol

1. Per winner, the nine cadence columns on `robust_score`, then separately on the fit
   and test halves of the holdout: a cadence that wins the score by winning only one
   window is reported as such.
2. **Phase dispersion** per slow cadence (3m across its three phases, 2m across two)
   is quoted as a range and compared with the *whole* cadence effect. If the phase
   range is as wide as the cadence range, the cadence is a lottery, not a parameter.
3. Gross vs net vs 20 bp: the part of a cadence's deficit explained by fees is the c00
   minus net gap; the rest is timing.
4. COVID lane: the `sens_2019-05-08` window's max drawdown per cadence is the one number
   a slow cadence must survive.
5. Fixed-mix baselines at three cadences answer the harvest question on their own.

## 7. Verdict — read from the committed artefacts

### 7.1 Monthly is the robust leader for every winner, in both lanes

`robust_score`, primary lane, gated arms (the three winners):

| cadence | 1w | 2w | 2w+1 | **1m** | 2m | 2m+1 | 3m | 3m+1 | 3m+2 |
|---|---|---|---|---|---|---|---|---|---|
| #1 BTAL75+KMLM25 | −0.04 | 0.32 | −0.09 | **0.856** | 0.72 | 0.30 | 0.17 | 0.74 | 0.77 |
| #2 BTAL75+DBMF25 | 0.03 | 0.41 | −0.03 | **0.859** | 0.74 | 0.34 | 0.21 | 0.77 | 0.82 |
| #3 BTAL50+KMLM50 | 0.20 | 0.65 | 0.14 | **0.890** | 0.82 | 0.51 | 0.32 | 0.81 | 0.88 |

The 2019 lane agrees: B75D25 gated 0.590 / 0.791 / 0.551 / **0.920** / 0.509 / 0.662 /
infeasible / 0.612 / 0.712. No cadence beats monthly on the protocol's key for any
winner in any lane; the closest is 3m+2 (0.01 to 0.09 behind — and a phase, see §7.2)
and 2w (0.24 to 0.53 behind).

### 7.2 Slower is dominated — by drawdown first, then by phase luck

- **COVID at calendar quarter-ends is a −56 % drawdown** (3m, both arms, gate or not):
  the Dec-31-2019 rebalance set TQQQ to w_max 0.8 at low vol and the next look was
  Mar 31. The point is infeasible under the −50 % constraint. The other quarterly phases
  rode it to −27 % / −31 %, bimonthly to −32 %; monthly and faster all held at −20 %.
  A vol-targeting rule that looks every quarter is not a vol-targeting rule.
- **Phase range ≥ cadence range.** Primary lane, #2 full Calmar: 3m 0.548 → 3m+2
  0.817 (Δ 0.27); 2m 0.743 → 2m+1 0.785; 2w 0.862 → 2w+1 0.600 (Δ 0.26). The entire
  spread from worst to best cadence *at a fixed phase* is about the same. 3m+2's
  21–22 % CAGR is real in this window and is the Feb/May/Aug/Nov calendar getting
  three crashes' timing right — it is not an adoptable coordinate.
- Fee drag is not what slow cadence buys: 0.2–0.3 % of contributions at 2m/3m vs
  0.6–0.7 % at monthly, worth ≈ 0.1 pp/yr.

### 7.3 Faster is not dominated — it loses on one episode, and costs are secondary

- **Fit window (2020-12 → 2024-12, the 2022 grind inside)**: weekly and biweekly beat
  monthly for every winner — #2 gated fit Calmar 1.050 / 1.068 / 0.995 vs 0.901 at
  monthly; #3 1.241 / 1.221 vs 1.149. Shallower max drawdown too (2w: −17.2 % vs
  −19.1 %).
- **COVID window (`sens_2019-05-08`)**: weekly 1.042 vs monthly 1.078, identical
  −20.1 % drawdown. Weekly went lower in TQQQ (min 0.042 vs 0.097) and was not
  punished — the recovery was slow enough to re-enter into.
- **Test window (2025-01 → 2026-08)** is where weekly collapses: #2 gated test Calmar
  0.031 vs 0.886; test TWR +1.0 % vs +24.6 % (SPY +31.5 %). Mechanism, from the
  allocations log: TQQQ actual 0.18 on Mar 31 → 0.11 (Apr 4) → 0.08 (Apr 11, the
  bottom) and then the gate pins it at ≤ 0.10 while the VT target climbs 0.12 → 0.37
  until QQQ recrosses its SMA-200 on May 16. Monthly never got to sell: Mar 31 held
  0.20, Apr 30 0.19, May 30 0.41. The same pattern recurs in Aug 2025 (−2.4 % vs
  +1.0 %) and Oct 2025 (−2.2 % vs **+9.2 %**): short vol spikes that revert inside the
  month, which weekly sells and monthly never sees. Roughly a third of the 2025–26 gap
  is the tariff V; the rest is whipsaw.
- **Costs**: gross vs net, #2 gated weekly 0.668 vs 0.650 full Calmar, monthly 0.866 vs
  0.859 — fees explain ≤ 0.02 of a 0.21 gap. At the 20 bp stress weekly pays 7.3 % of
  contributions (0.564 Calmar, −1.4 pp/yr) against monthly's 3.4 % (0.820): weekly is
  the one cadence the stress case materially hurts, but it lost on timing first.
- **Nothing on the grid rescues weekly**: no λ (weekly and biweekly robust ≤ 0.39 at
  every λ × σ and never the row's best — monthly, 2m or a quarterly phase leads every
  one of the eight rows, with the λ = 0.97 rows poor everywhere) and no floor (w_min
  0.3 lifts weekly test
  Calmar 0.03 → 0.29 against monthly's 0.89 → 1.01; test CAGR 5.8 % vs 16.5 %). The
  no-gate weekly also collapses in the test (0.11–0.38), so the gate's re-entry block
  adds ~0.1–0.15 of damage but is not the cause.

Honest reading: **the sign of the fast-cadence effect flips between the fit and test
halves** (+0.15 Calmar, then −0.85). That is not a robust effect in either direction;
`robust_score` resolves it to "monthly" because its minimum takes the test, and the
test is 1.6 years with one V-crash and three whipsaws. Monthly is adopted on the
protocol, not on a belief that weekly is structurally worse — and it is the
lower-turnover choice inside the undominated set (1.7×/yr vs 2.5–3.8×).

### 7.4 The Shannon question: cadence does nothing for the fixed mix

Plain 50/50, primary lane: 1w 0.345 / 1m 0.337 / 3m 0.386 full Calmar, CAGR 15.6 /
15.1 / **16.8** %; 2019 lane 0.484 / 0.480 / 0.546. Gated 50/50: 0.464 / 0.525 /
0.481. Rebalancing into BTAL more often harvests nothing measurable; rebalancing less
often simply leaves more in TQQQ, which is where the return is. This is the cadence
version of the standing conclusion that TQQQ/BTAL is not a Shannon's demon — the
harvest term is too small against BTAL's drift to show up at any frequency.

### 7.5 What changes in the trading rules

Nothing. The month-end rule in WINNING_STRATEGIES.md stands, now with a measured
reason: it is the coarsest cadence that still vol-targets through a fast crash
(COVID −20 % at monthly vs −27 … −56 % slower) and the finest one that does not sell
every intra-month spike. Turnover ~1.7×/yr remains the price.

## 8. Honest limitations

- The weekly verdict rests on one 20-month test window. The fit window and the COVID
  window both say the opposite. A third fast crash would settle it; the data does not
  contain one.
- Weekly phase is the epoch's, not "Friday close" — all weeks end on the last trading
  day before the Monday boundary, which is Friday except on holidays. Fine for the
  engine, slightly off for a live weekly rule that trades Thursdays.
- A contribution-only day invests at the *target* weights, not toward them: a 1 %
  deposit does not meaningfully rebalance a drifted book, by design. A "contribution
  buys the most underweight asset" rule would be a different (band-like) strategy and
  belongs to the threshold-rebalancing item on the horizon, not here.
- Categorical cadence means no neighbourhood term; the primary-lane `robust_score`
  is therefore slightly more generous than the blend lane's for the same monthly
  point (0.859 here vs 0.842 there for #2). Compare cadences within this artefact only.
- Integer shares at weekly cadence on a $10k–80k book: many weeks trade 1–3 shares of
  the sleeve; the fee model is proportional so this costs nothing, but a live
  commission-per-trade broker would change the weekly arithmetic.

## 9. Acceptance checklist

- [x] `strategy.Cadence`, `Strategy.rebalance`, mask anchored to the calendar
- [x] `simulate`: cadence mask per strategy; contribution-only days; default path bit-identical (420 → 443 green, no snapshot touched)
- [x] `spec.py` `rebalance` grammar, label suffix, `rebalance_str`; `sweep.py` params rendering
- [x] `tests/test_rebalance.py` — 23 tests
- [x] Six specs/lanes run on `2026-08-20-net15`; artefacts committed with the specs
- [x] Docs: STRATEGY_DEVELOPMENT (grammar), ARCHITECTURE (engine note), README (one line)
- [ ] Merge to main; WINNING_STRATEGIES.md gains one sentence pointing here for the cadence rationale (§7.5)

## 10. Deliberately not in scope

Daily cadence (noise, §1). Band/threshold rebalancing (a trigger, not a calendar — it
is the next spec and can reuse the contribution-only branch unchanged). A re-entry rule
for fast cadences (asymmetric gate speed, or buying back to the pre-gate weight) —
motivated by §7.3's mechanism, but it is a gate change, not a cadence one.

## 11. Errata

1. **This section was added after the fact, at EPISODE_SPEC's docs commit** —
   this spec's implementation produced no deviations, so it had none. The winners
   file named in §7.5 and the checklist now lives at
   `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` (created by CASH_SLEEVE §10.6(b),
   renamed at `68cac21`). Its "Monthly rebalancing stands" flag is the sentence
   the checklist asked for; the box is left as it was. (EPISODE_SPEC §7.2.)
