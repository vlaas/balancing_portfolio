# Specification: total-return data convention

Repo: `vlaas/balancing_portfolio` · baseline commit: `22d15c5` ("cost model merge", 259 tests green) · status: implemented (2026-08-21, branch `total-return`) — deviations in the errata at the end

## 1. Goal

Every price CSV is a TradingView export whose close series excludes distributions.
Measured on the frozen snapshot, BTAL's close fell from 24.75 (2011-09-13) to 11.86
(2026-08-14) — a price-only drift of **−4.93%/yr over 14.9 years** — of which roughly
3%/yr is not loss but distributions the simulation never sees. DBMF and KMLM distribute
even more heavily. Every committed result is therefore biased *against* high-distributing
assets, and the upcoming safe-swap sweep (`safe ∈ {BTAL, DBMF, KMLM, null}`) would be a
comparison of distribution policies, not strategies.

The fix is a **data convention change, not an engine change**: the traded close series
becomes the dividend-adjusted (total-return, "TR") series. `prices.py`, `simulate.py`,
`indicators.py`, `stats.py`, `results_json.py`, `spec.py`, `sweep.py` are all untouched;
`SCHEMA_VERSION` stays 4 (no `results.json` key changes — a run's dataset is identified
by `run.data_dir`, exactly as cost-free vs cost runs are identified by `config`).
All committed price-series artefacts remain valid as gross-of-distribution regression
anchors. Not in scope: §10.

## 2. Source of truth — decision

Two candidates were on the table:

1. **TradingView's dividend-adjustment toggle** ("Adjust data for dividends"): export
   each symbol twice, once adjusted, once not. The adjusted export *is* the TR series.
2. **Explicit distribution table** (`ex_date, amount` per symbol) applied by the loader
   to construct TR from the price series.

**Decision: option 1.** Reasons:

- **Verifiability.** With both exports of one session in hand, the adjustment is fully
  checkable *internally*: the ratio `R_t = adjusted_t / price_t` must be a
  non-decreasing step function ending at 1.0, whose jumps sit only on ex-dates and whose
  implied per-share amounts can be spot-checked against published distributions (§4).
  Option 2 is *less* verifiable, not more: matching TradingView's undocumented
  adjustment arithmetic and rounding to a tight tolerance is not realistic, so its
  parity test against a TV adjusted export would need a loose tolerance — a weak test
  guarding hand-typed data.
- **Data-entry risk.** Option 2 requires transcribing hundreds of distribution rows
  (six symbols, up to 33 years, BTAL and SPY alone are frequent payers); one wrong
  amount silently reshapes a backtest. Option 1's failure modes (toggle in the wrong
  state, mismatched export sessions) are exactly what the §4 invariants catch loudly.
- **Zero loader code.** The adjusted export has the same layout as today's files;
  `_read_symbol` reads it unchanged. Option 2 adds an adjustment implementation plus
  its own convention decisions (multiplicative vs additive, factor rounding) to the
  trusted codebase.

Two properties of the TV convention the spec relies on (both asserted by tests, not
assumed): splits are adjusted in *both* exports identically (the toggle controls
dividends only), so `R` is split-invariant; and the adjusted series is anchored at the
latest bar, so `R = 1` from the last ex-date onward.

One honest cost, documented in `data/README.md`: an adjusted export is **not
append-stable** — every new ex-date rescales the entire history, and integer shares plus
fixed dollar contributions are not scale-invariant, so a run on live `data/` can move in
the cents between refreshes even over an identical window. This changes nothing in
practice: pinned numbers only ever come from frozen snapshots, which is already the rule.

## 3. File and dataset convention

**TR is a dataset convention, not a new column.** A *dataset directory* contains, per
symbol:

```
<DIR>/<SYM>.csv          # dividend-adjusted export — the traded series (loader input)
<DIR>/price/<SYM>.csv    # unadjusted export from the same session — reference only
```

Both files use today's export layout (`time,open,high,low,close,SMA50,SMA100,SMA200,
SMA15,Volume`); the loader still whitelists `time,close` and never looks inside
`price/`. The paired files must come from the same export session: identical date
columns per symbol (asserted, §7 T1), files across symbols may drift at the tail as
today (DBMF/KMLM currently run to 2026-08-17 vs 2026-08-14).

- **Live `data/` switches to this convention.** `data/<SYM>.csv` becomes the adjusted
  export; `data/price/<SYM>.csv` is added. Rationale for repointing rather than adding
  a parallel `data_tr/`: `--data` defaults to `data` in both `main.py` and `sweep.py`,
  and a default that silently runs the biased series is a standing footgun. Committed
  artefacts are unaffected — they are pinned to the frozen snapshot and to their
  recorded `run.data_dir`.
- **New frozen snapshot** `tests/data/<date>/` per the append-only rule, where `<date>`
  is the last bar of the new TQQQ export (assert TQQQ/BTAL/QQQ/SPY share that last
  bar, as they do today, else re-export). It contains all six symbols in both series,
  copied verbatim from the fresh export, plus a one-paragraph `README.md` (export
  date, toggle states, the measured tolerances of §7). The existing flat
  `tests/data/*.csv` snapshot stays byte-identical where it is — moving it into a
  dated subdirectory would touch every test file for zero benefit. If a same-date
  price-only snapshot is ever needed, suffix it `-price`; the directory's `price/`
  subfolder and README make each snapshot self-describing regardless.

Module constant in tests: `TR_DIR = Path(__file__).parent / "data" / "<date>"`,
next to the existing `GOLDEN_DIR`.

## 4. The adjustment ratio — normative invariants

For a paired symbol let `P_t` be the price close, `A_t` the adjusted close,
`R_t = A_t / P_t`. Under TV's multiplicative back-adjustment, a distribution of `D` per
share going ex on bar *t* multiplies all bars before *t* by `k_t = 1 − D / P_{t−1}`;
therefore:

1. `0 < R_t ≤ 1` everywhere, and `R` is **non-decreasing** in *t*;
2. `R` is **piecewise constant**: flat between ex-dates, jumping up at each ex-date by
   `R_t / R_{t−1} = 1 / k_t`;
3. `R = 1` on the last bar (anchor at the latest price);
4. the **implied per-share distribution** at a jump is
   `D_t = P_{t−1} · (1 − R_{t−1} / R_t)`, and this quantity is *refresh-stable*: a later
   export rescales `R` globally, leaving the ratio `R_{t−1}/R_t` — and hence `D_t` —
   unchanged. Spot checks against published amounts therefore hold on any export;
5. the **cumulative implied distribution yield** `y = −ln(R_first) / years` is the
   file-level sanity number: `y = 0` means the adjusted export was made with the toggle
   off — the single most likely operator error — and the per-symbol bands in §7 T2 make
   that a loud failure.

Tolerances: exported price closes are tick-rounded (BTAL at 2 decimals), and whether TV
exports *adjusted* closes at full float precision or rounded to the price scale cannot
be determined without the export in hand. The tests therefore carry **ceiling**
tolerances stated in §7, and the implementation **pins the measured values** (max
flat-segment noise in `ln R`, max SMA parity diff on adjusted files) in the snapshot
README and tightens the constants to one order above the measurement, in the same
commit. A ceiling that cannot be met is a finding to bring back, not a constant to
raise.

## 5. Signal series — which series each indicator reads, and why

**Uniform rule: every indicator is computed on the `close` of the file the loader
reads.** In a TR dataset that is the TR series — for the traded symbols and for signal
symbols alike. There is no dual plumbing, no per-indicator series switch. Per signal:

- **SMA trend gate on QQQ → TR.** A price-series SMA on a distributing symbol embeds a
  structural downward drift equal to the yield — the gate would read distributions as
  weakness. For QQQ (~0.6%/yr) the effect on gate *state* is near nil, and §7 T5 pins
  it: on the frozen price snapshot, only **1 of 115** rebalance days since 2017-01-03
  has QQQ's close within 0.5% of its SMA200 (4 within 1%), while the TR/price ratio
  moves ≲ 0.3% relative to the SMA within any 200-day window — so at most a handful of
  gate states can differ, and the measured count goes in the commit message. The
  convention must nonetheless be TR, because it has to generalise to gating a
  high-distributing symbol without a sign error.
- **EWMA vol on QQQ (drives vol targeting) → TR.** Ex-date price drops are not economic
  volatility; a price series counts them as losses. On QQQ (median EWMA94 vol on
  rebalance days 17.8%, min 6.7% — measured on the frozen snapshot) a ~0.15% quarterly
  drop is noise; on KMLM a large annual distribution would print a spurious vol spike.
  Vol continues to be measured on QQQ × leverage, never on TQQQ, as before.
- **`momentum`, `drawdown`, `sma_monthly` → TR** by the same rule. In particular
  drawdown statistics on BTAL/DBMF/KMLM stop overstating.
- **TV-parity fixture (indicators T1) → both, within-file.** The adjusted export's
  `SMA*` columns are TradingView's SMAs *of the adjusted close* (Pine `close` follows
  the chart's adjustment setting), so the within-file comparison stays valid on TR
  files, and equally on the `price/` files. The export procedure requires the toggle to
  be set **before** exporting so the indicator columns and the close column agree —
  T1 is the backstop.
- **Live execution note** (docs): to reproduce a signal on a TradingView chart, turn
  dividend adjustment **on**.

## 6. Export procedure — `data/README.md`

Rewrite the "Export settings" section as a two-pass procedure per symbol, same chart,
same session:

1. Chart settings → **Adjust data for dividends: ON** → *Export chart data…* →
   `data/<SYM>.csv`.
2. Toggle **OFF** → export again → `data/price/<SYM>.csv`.
3. Toggle back ON (so the chart's resting state matches the traded series).

Plus: the Pine script section unchanged; a new paragraph stating the §4 invariants in
one sentence each, the append-instability caveat (§2), the live-signal note (§5), and
the pinned tolerances. The frozen-snapshot paragraph gains the `tests/data/<date>/`
layout of §3.

## 7. Tests — `tests/test_total_return.py` (new) plus edits

Invariant tests (T1–T3) are parametrised over **two dataset roots**: `TR_DIR` (frozen,
numeric claims allowed) and live `data/` (structural claims only, same assertions —
they are structural by construction). This makes a bad refresh fail the suite the day
it lands, in the spirit of the live smoke test.

**T1 — Pairing.** For each of the six symbols in the root: both files exist; the
`time` columns are identical (same session); TQQQ/BTAL/QQQ/SPY share their last bar
and it equals the snapshot directory's name (frozen root only); the snapshot README
exists.

**T2 — Ratio invariants.** Per symbol, with `r_t = ln R_t`: (a) `R_last == 1` within
1e-6 relative; (b) monotone up to noise: `r_t ≥ r_{t−1} − τ` with ceiling `τ = 1e-3`,
tightened to the measured flat-segment noise per §4; (c) at least 4 up-jumps above
`5τ` (every symbol has distributed at least annually over a multi-year file);
(d) cumulative implied yield `y = −r_first / years` within bands:
`[0.001, 0.20]` for all six, and additionally `y ≥ 0.015` for BTAL, DBMF, KMLM. Band
(d) is what makes "toggle was off" (`R ≡ 1`, `y = 0`) and "files swapped"
(`R ≥ 1`, monotone down) unmissable.

**T3 — Implied-distribution spot checks.** A hand-entered table of ~2 published
distributions per distributing symbol (ex-date, per-share amount, source URL in a
comment — issuer or Nasdaq dividend history, checked by a human at implementation):
`D̂ = P_{t−1} · (1 − R_{t−1}/R_t)` at the known ex-date matches within `$0.02`
(ceiling; tighten per §4). Refresh-stable by §4.4, so it runs on live data too. This is
the only external-data anchor and it pins the adjustment *semantics*, not just its
shape.

**T4 — SMA/TV parity extended.** `tests/test_indicators.py::CSV_FILES` changes from
`glob("*.csv")` to `rglob("*.csv")` on both roots, so the new snapshot's TR files, its
`price/` files, and live `data/price/` all enter the existing within-file comparison.
Tolerance stays 1e-9 for price files. If adjusted files fail at 1e-9 due to export
quantisation of the adjusted close (§4), the TR-file lane gets its own pinned, measured
tolerance — the test's job (a header disagreeing with its length, a mislabelled column)
survives at 1e-3; silently loosening the price lane does not happen.

**T5 — Signal-series deltas.** On the matched window (start 2017-01-03, end
2026-08-14): (a) the number of rebalance days where the SMA200 gate state
(`QQQ close < SMA200`) differs between `TR_DIR` and the old price snapshot is ≤ 4, the
measured count recorded in the commit message; (b) `VOL_EWMA94` on QQQ differs by ≤ 2%
relative on every rebalance day between the two datasets. Both ceilings follow from
the §5 measurements; the point of the test is that a *violation* means the export is
not what §4 says it is.

**T6 — Cross-snapshot calendar.** Per symbol in {TQQQ, BTAL, QQQ, SPY}: the TR
snapshot's date set restricted to ≤ 2026-08-14 equals the old snapshot's date set.
Pins that the refresh neither lost nor invented sessions, which T7's comparability
rests on. If TradingView has genuinely revised history, that is a finding: document
the diff in the snapshot README and adjust this pin in the same commit — never paper
over it.

**T7 — TR golden.** The `default` bundle on `TR_DIR` with
`Config(end=dt.date(2026, 8, 14))` — the same trading days, deposits and rebalance
days as the price golden, so the two are directly comparable — reproduces a
`GOLDEN_TR` dict (final value, CAGR, max DD per strategy) to the cent, produced once
by the implementation and eyeballed: every number should beat its price twin, the
50/50 and SMA-gate rows by roughly BTAL's yield on half the book, the SPY benchmark by
roughly SPY's dividend yield compounded, TQQQ 100% by little. Two directional asserts
are part of the test (cross-snapshot, same window): `final_TR > final_price` for
"TQQQ/BTAL 50/50" and "SPY benchmark". Same rule as every golden: a later failure
means the engine changed; never fix it by refreshing the snapshot.

**T8 — TR cost golden.** As T7 under the tastytrade base schedule and 3% cash yield
(`cost_bps = {"TQQQ": 1.5, "BTAL": 6, "QQQ": 1, "SPY": 0.7, "*": 6}`,
`cash_yield = 0.03` — the same literals as the existing cost golden), pinning final
values and total fees. This is the exact configuration the §8 rerun runs under, so the
regression anchor sits on the decision path, not beside it.

The existing goldens — `GOLDEN`, `COST_GOLDEN`, the results-JSON byte-stability tests,
and all committed sweep artefacts — stay pinned to the flat price snapshot, untouched.

## 8. Rerun protocol — what this spec exists for

After merge and snapshot commit (`<date>` = the new snapshot):

```
uv run sweep.py specs/sweep_vt_cbase.json --data tests/data/<date> --out results/sweep_vt_tr_cbase
```

— the consolidated VT grid (λ, σ, w_max, gate, baselines as committed) under the
calibrated tastytrade schedule, on total-return data. Commit the artefact set. Read it
against `results/sweep_vt_cbase` (same grid, same costs, price series):

1. does the **plateau survive the data convention** (top-15 overlap, robust_score
   deltas);
2. does the **gate survive** now that BTAL's carry is no longer understated (the gate
   reroutes contributions into BTAL below the SMA — TR data makes that reroute more
   attractive, so the gate advantage should hold or widen; if it *narrows*, that is a
   real finding about what the gate was actually harvesting);
3. does VT still beat the **gated 50/50 baseline**, whose BTAL sleeve gains the most
   from the correction.

The verdict sentence goes into project memory; the numbers stay in the repo. Then, and
only then, the safe-swap sweep spec (`safe ∈ {BTAL, DBMF, KMLM, null}`) is written
against the TR snapshot — DBMF and KMLM are the heaviest distributors in the universe,
which is why this spec must land first.

## 9. Acceptance checklist

- [ ] Live `data/` re-exported per §6: six adjusted files + `data/price/`,
      `data/README.md` rewritten
- [ ] Frozen snapshot `tests/data/<date>/` with both series, verbatim, plus README
      with pinned tolerances; existing flat snapshot byte-identical
- [ ] `tests/test_total_return.py` T1–T3, T5–T8; `tests/test_indicators.py` rglob
      (T4); measured tolerances and the T5 gate-delta count in the commit message
- [ ] No change to `prices.py`, `simulate.py`, `indicators.py`, `stats.py`,
      `results_json.py` (`SCHEMA_VERSION` stays 4), `spec.py`, `sweep.py`
- [ ] Whole suite green from a fresh clone with `pip install polars matplotlib pytest`
- [ ] Docs: `data/README.md` per §6; STRATEGY_DEVELOPMENT "Data files and indicators"
      (TR convention, signals on TR, live-signal note); ARCHITECTURE (data-flow: the
      loaded close is total-return, `price/` is reference-only); CLAUDE.md protocol:
      numbers quoted for real decisions come from a **TR dataset** at stated costs —
      price-series numbers are regression artefacts only
- [ ] §8 rerun committed: `results/sweep_vt_tr_cbase/*`

## 10. Deliberately not in scope

- **Net-of-withholding total return.** The TR series reinvests distributions gross at
  the ex-date close; an Estonian holder of US ETFs loses 15% treaty withholding on
  each distribution even inside the investeerimiskonto. The residual bias is therefore
  *for* high distributors at 15% of yield — opposite sign and ~6.7× smaller than the
  bias this spec removes (order: QQQ ~9 bp/yr, BTAL ~45 bp/yr, KMLM potentially
  > 100 bp/yr in heavy years). This is deliberately deferred, **with a tripwire**: if
  the safe-swap sweep's verdict margin between candidates is within ~1%/yr CAGR, the
  withholding correction (a loader option reconstructing net-TR from the paired files
  via the §4 implied distributions) gets its own spec before the verdict is trusted.
- **Cash-distribution modelling** (dividends as engine cash events with pay-date lag,
  interacting with `cash_yield` and rebalancing): strictly more faithful, but an
  engine change with a new event type for a second-order timing effect (≤ 1 month's
  delay on ~3% yield ≈ single-digit bp/yr).
- **An explicit distribution table** as data (rejected in §2; revisit only if the
  net-of-withholding spec is written, where the implied series may suffice anyway).
- **Synthetic pre-2010 history** (own spec; the financing model is the substance
  there) and the safe-swap sweep spec itself (next in line, blocked on this one).

## 11. Errata (implementation, 2026-08-21)

- **§1 / §7 T2(d) — BTAL's yield.** Measured 1.07%/yr, not the ~3%/yr §1
  assumed: eight distributions ever, none 2013–2017, each verified against
  Polygon records. Its band floor is 0.008 instead of 0.015 (DBMF 5.81%/yr and
  KMLM 4.38%/yr keep 0.015). The §1 bias estimate was overstated; the
  direction, and everything §8 tests, stand — measured, the 50/50 golden gains
  1.2%/yr CAGR from the correction, not ~1.5%.
- **§4 / §7 T2 — τ.** The exports carry full-precision adjusted closes;
  measured flat-segment noise tops out at 4.3e-8 (TQQQ), so `TAU = 1e-6`,
  global — no per-symbol dict needed. Note the §7 ceiling `τ = 1e-3` could
  never have satisfied T2(c) for QQQ or SPY (per-jump `ln R` ≈ 1.5e-3 / 3e-3,
  below `5τ = 5e-3`): the measured tightening was constitutive, not hardening.
- **§4.4 — refresh stability of `D_t`.** Holds for dividend refreshes only; a
  *split* rescales split-adjusted implied amounts. TQQQ split 2:1 on
  2025-11-20, so its pre-split published amounts appear at half in today's
  basis — T3 uses post-split TQQQ ex-dates and states the restatement rule.
- **§7 T3 — source.** Published amounts come from Polygon's reference
  dividends API via the committed `fetch_dividends.py` (each chosen ex-date a
  single Polygon record), not hand-typed issuer/Nasdaq pages; tolerance
  $0.0001 (measured $0.000011 against the ceiling $0.02).
- **§7 T4.** Adjusted files pass the existing 1e-9 unchanged (measured
  ≤ 1.3e-12); no separate tolerance lane was needed.
- **§9 — docs.** The checklist omitted the root `README.md`, whose
  "price-return only" data note the convention change falsifies; fixed in the
  docs commit.
