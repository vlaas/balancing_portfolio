# Specification: trading costs, cash yield, turnover

Repo: `vlaas/balancing_portfolio` · baseline commit: `39443f5` ("sweep_vt_ext results") · status: proposal, v2

v2: validated against the broker/cost research of Aug 2026 ("Round-Trip Trading Costs",
project context). Operative assumption from it: **the broker is tastytrade** (IBKR IE
cannot sell US-domiciled ETFs to EEA retail under PRIIPs — none of the six tickers has a
KID), so commission is $0 and the per-side cost is half-spread + slippage + sell-side
regulatory fees. Structural consequence: costs differ ~6× between tickers (TQQQ ~1.5 bp
vs BTAL/KMLM ~6 bp), so `cost_bps` becomes per-asset (§2). All constants are
point-in-time (~Aug 2026); re-check quarterly, KMLM especially.

## 1. Goal

Every result so far is gross: trades are free and cash earns nothing. The current sweep
winner (VT + gate) trades more than the 50/50, so friction is the cheapest way the finding
could die — it must be tested before anything else is built on it. Three parts:

1. `Config.cost_bps` — proportional cost on every buy and sell;
2. `Config.cash_yield` — annual rate accrued on the cash balance (also the T-bill proxy
   for future `safe: null` configurations);
3. **turnover and total costs** in `summary()`/`results.json`, without which a cost
   sensitivity cannot be interpreted.

Both fields default to `0.0`: the golden dataset, golden test, and all committed sweep
artefacts remain valid and untouched. Not in scope: §10.

## 2. Config

```python
@dataclass(frozen=True)
class Config:
    start: dt.date
    initial_capital: float
    monthly_contribution: float
    end: dt.date | None = None
    cost_bps: float | Mapping[str, float] = 0.0
    # per-side, proportional: fee = f(asset)/10_000 × trade value.
    # float: flat rate for every asset. Mapping: per-symbol rate; key "*" is the
    # default for symbols not listed (absent "*" → flat 0 for them is an error:
    # every traded symbol must resolve, ValueError at build time otherwise).
    cash_yield: float = 0.0    # annual rate, ACT/365, accrued daily on the cash balance
```

In spec JSON: `"cost_bps": 4` or `"cost_bps": {"TQQQ": 1.5, "BTAL": 6, "*": 4}`.
Per-asset is not gold-plating: the safe-asset swap experiment (BTAL vs DBMF vs KMLM)
is next on the list, and DBMF trades at half BTAL's cost — a flat rate would erase a
real difference between the candidates being compared.

Validation (in `build_bundle` and the sweep spec parser, not in the frozen dataclass):
every rate in `0 ≤ f ≤ 1000`, `0 ≤ cash_yield ≤ 0.20`, every traded and gated symbol
resolves; outside → `ValueError` with the JSON path. Per-order fixed commissions ($0 at
tastytrade), borrow costs (inside the ETFs), and taxes (investeerimiskonto) are
deliberately not modelled. Sell-side regulatory fees (SEC §31 + FINRA TAF, ~0.25–0.4 bp,
sells only) are absorbed into the per-side constants rather than modelled asymmetrically —
at 0.3 bp the asymmetry is far below the spread noise it would sit on.

**Calibration constants (tastytrade, ~Aug 2026, from the research doc):**

| Symbol | base `cost_bps` | source figures (per-side buy/sell) |
|---|---|---|
| SPY | 0.7 | 0.5 / 0.7 |
| QQQ | 1 | 0.7 / 1 |
| TQQQ | 1.5 | 1.3 / 1.5 |
| DBMF | 3 | 2.5 / 2.8 |
| BTAL | 6 | 6 / 6.4 |
| KMLM | 6 | 6 / 6.3 (spread range 3–38 bp — most execution-dependent name) |

Stress: flat 20 portfolio-wide (BTAL/KMLM spreads widen to 17–38 bp in thin markets);
~10 would be representative for a TQQQ-only sleeve. `cash_yield`: base `0.03` — matches
SOFR 3.65% / 3-mo T-bill ~3.6% net of frictions, **but only if idle USD is swept into a
T-bill ETF (SGOV)**; truly idle tastytrade cash earns ~0. Sensitivities: `0.0` (idle
downside), `0.035` (SGOV upside). The SGOV sweep itself is an implementation action item,
not part of the model.

## 3. Engine — `simulate.py`

### 3.1 Cash yield accrual

At the top of the daily loop, before deposits and trading. Resolve the fee schedule once
before the loop — `f = {a: rate(a) / 10_000 for a in assets}` where `rate` handles the
float/Mapping/`"*"` forms — and let `y = cash_yield`:

```python
if i > 0 and y:
    cash *= (1.0 + y) ** ((row["date"] - prev_date).days / 365.0)
prev_date = row["date"]
```

Calendar-day gaps, so weekends and holidays accrue (a Monday accrues 3 days). Interest is
internal return, **not** external flow: `flow` is unchanged, so TWR and XIRR account for
it correctly with no further changes. No interest on day 0 (the capital arrives that day).

### 3.2 Trading costs

Fees are paid from cash at execution. The existing order — sells before buys — is kept;
one guard is added so cash can never go negative from fees:

```python
for asset in sorted(assets, key=lambda a: deltas[a]):
    delta = deltas[asset]
    if delta > 0 and f[asset]:
        # Affordability cap: shares whose cost including fee fits in cash.
        delta = min(delta, math.floor(cash / (row[asset] * (1.0 + f[asset]))))
    fee = abs(delta) * row[asset] * f[asset]
    cash -= delta * row[asset] + fee
    shares[asset] += delta
    if delta:
        log(row["date"], "BUY" if delta > 0 else "SELL", asset, delta, row[asset],
            abs(delta) * row[asset], fee=fee)
```

Properties, each pinned by a test:

- **All-zero `f` is bit-identical to today.** The cap becomes `floor(cash / price)`, which
  the floor-based target construction already guarantees is ≥ `delta`, so it never binds;
  `fee` is 0.0 everywhere. This is what keeps the golden test green with no fixture change.
- Sells always execute in full (fee reduces proceeds, never blocks the sell).
- Buys are capped sequentially in the existing deterministic order; the shortfall against
  target is at most `fee / price` shares per asset and shows up as cash — measured by the
  existing misallocation metrics, no new mechanism.
- `assert cash >= -1e-6` unchanged and now provably safe under any `f`.
- `buy_cap` (contribution exemption) caps the **gross** trade value, fee excluded — one
  sentence in the docstring; the cap is an intent limit, not an accounting identity.

### 3.3 Trades frame

New column `fee: pl.Float64` on every row (0.0 for DEPOSIT). `log()` gains `fee=0.0`
keyword. `cash_after` continues to reflect the balance after the trade including its fee.

## 4. Metrics — `stats.py`, `results_json.py`, `report.py`

`summary()` gains a fourth argument `trades` and four keys:

```
"traded_value":  Σ amount over BUY and SELL rows
"total_fees":    Σ fee   over all rows   (identity: total_fees == Σ_a f[a] × traded_value_a)
"turnover":      (traded_value / 2) / mean(curve.value) / years     # annualised, one-sided
"fee_drag":      total_fees / total_contributed
```

`years` as in `cagr` (ACT/365 over the curve). The one-sided convention (half of buys +
sells) is stated in the docstring together with its caveat: monthly contributions put a
floor under turnover — a buy-and-hold contributor still shows ~`contribution × 12 / avg
value` — so turnover is comparable **between strategies on the same Config**, not across
Configs. Rendered in `print_report`/`save_markdown` as `Turnover (1-sided, ann.)`,
`Total fees`, after the exposure rows. `results.json`: keys appear via the summary dict;
`config` block gains `cost_bps` (number or object, exactly as configured) and `cash_yield`
(always, even when 0 — explicit beats absent); `SCHEMA_VERSION = 4`.

## 5. Spec and sweep plumbing

- Bundle spec `config`: optional `cost_bps`, `cash_yield` (default 0). `normalised_spec`
  always emits them. Unknown-key/range errors with JSON paths as everywhere.
- Sweep spec `config`: same two optional fields, forwarded into every window's `Config`.
- `sweep.py --cost-bps X` and `--cash-yield Y`: override the spec's values for a what-if
  rerun without committing a near-duplicate spec file. `--cost-bps` is scalar only and
  replaces the **whole** schedule with a flat rate — that is what a stress case means;
  per-asset schedules live in spec files. Recorded in `summary.json` header and
  `summary.md` ("Costs: flat 20 bps (CLI override), cash yield 3%"). `main.py` gets no
  such flags — bundles are rendered from their spec, and a bundle what-if is a spec edit.
- `runs.csv` gains `cost_bps` (the flat number, or the JSON object serialised as a string
  for per-asset schedules) and `cash_yield` columns (constant per file today, but the
  file should be self-describing).

## 6. Golden interaction

No new snapshot, no golden change: defaults reproduce current behaviour exactly (§3.2).
Add one **cost golden** to the regression suite so the fee path itself is pinned: the
default bundle on `tests/data` with the §2 per-asset base schedule and `cash_yield=0.03`,
final values hardcoded to the cent, produced once by the implementation and eyeballed for
plausibility (fees of the right order; the 50/50 turns over far less than VT+gate). This
pins both the fee arithmetic and the `"*"`/per-asset resolution. Same rule as always: a
later failure means the engine changed.

## 7. Tests

**T1 — Neutrality.** `cost_bps=0, cash_yield=0`: `simulate` output frames bit-identical
to a run on today's code path (assert against the existing golden numbers; also
frame-equality of trades including the all-zero `fee` column). The affordability cap is
exercised and inert.

**T2 — Fee accounting.** Synthetic two-asset prices. Flat `cost_bps=50`: every BUY/SELL
row has `fee == amount × 0.005` exactly; `summary.total_fees == 0.005 ×
summary.traded_value`; `cash_after` sequences reconcile hand-computed. Per-asset
`{"A": 10, "*": 50}`: A's rows at 0.001, B's at 0.005, identity per asset; a schedule
that leaves a traded symbol unresolved (no entry, no `"*"`) raises at build time with
the symbol named.

**T3 — Affordability.** Adversarial synthetic (all-in single asset, `cost_bps=500`): cash
never negative on any day; the capped buy is exactly `floor(cash / (price × 1.05))`;
the residual appears in the CASH allocation row.

**T4 — Accrual.** Synthetic with a weekend gap, `cash_yield=0.10`, a strategy holding 50%
cash (`fixed` weights summing to 0.5): Monday's cash is Friday's × `1.1^(3/365)` net of
that day's trades, hand-computed; day 0 accrues nothing; `flow` column identical to the
yield-0 run (interest is not flow); TWR strictly greater than the yield-0 run.

**T5 — Turnover.** Known trade log: `traded_value`, `turnover`, `fee_drag` equal
hand-computed values; DEPOSIT rows excluded from `traded_value`.

**T6 — Plumbing.** Bundle spec and sweep spec with the fields parse and reach `Config`;
out-of-range values raise with path; `--cost-bps` override lands in `runs.csv` and the
summary header; `results.json` `config` always has both keys and `schema_version == 4`.

**T7 — Cost golden** per §6.

## 8. Rerun protocol — the experiment this spec exists for

After merge, run the consolidated grid (λ {0.75–0.90}, σ {0.25–0.40}, w_max {0.6–0.8},
gate {null, SMA200}, baselines as committed) three times on `tests/data`:

```
sweep.py specs/sweep_vt_consolidated.json --data tests/data --out results/sweep_vt_c00
sweep.py specs/sweep_vt_cbase.json        --data tests/data --out results/sweep_vt_cbase
sweep.py specs/sweep_vt_cbase.json --cost-bps 20 --data tests/data --out results/sweep_vt_c20
```

`sweep_vt_cbase.json` = the consolidated spec plus
`"cost_bps": {"TQQQ": 1.5, "BTAL": 6, "QQQ": 1, "SPY": 0.7, "*": 6}, "cash_yield": 0.03`
— the tastytrade base schedule from §2 (`"*"` covers future safe-asset swaps
conservatively). The c20 run is the flat stress via CLI override, cash yield kept at 3%.
Optional fourth reading, no separate run needed: the idle-cash downside (`cash_yield=0`)
only matters for `safe: null` configs, none of which are in this grid. Commit all three
artefact sets. Read
them as: does the plateau survive (top-15 overlap between c00 and c20; robust_score
deltas), does the *gate* survive (it adds turnover — compare gate/no-gate pairs' fee_drag
and robust_score gap by cost level), and does VT still beat the gated 50/50 baseline at
flat 20 bps. Expected order of magnitude, worth checking against the output: at ~0.5×
annual one-sided turnover and a ~2–3 bp blended rate, fee drag should land in single-digit
bps per year — if it comes out 10× that, suspect the turnover accounting before the
strategy. The verdict sentence — which of the three survive — is what goes into project
memory; the numbers stay in the repo.

## 9. Acceptance checklist

- [ ] `Config.cost_bps`, `Config.cash_yield`, range validation in both spec parsers
- [ ] Accrual and fee deduction per §3, `fee` column, `log(fee=)`
- [ ] `summary(trades=…)` with `traded_value`, `total_fees`, `turnover`, `fee_drag`;
      report lines; `SCHEMA_VERSION = 4`; config keys always emitted
- [ ] Sweep: config fields, CLI overrides, `runs.csv` columns, header lines
- [ ] Tests T1–T7 green from a fresh clone; existing golden untouched
- [ ] `specs/sweep_vt_consolidated.json`, `specs/sweep_vt_cbase.json` + the three §8 runs
      committed
- [ ] Docs: STRATEGY_DEVELOPMENT (cost model §, one paragraph), ARCHITECTURE (schema 4),
      CLAUDE.md protocol: comparisons intended for real decisions quote cost-adjusted
      numbers (state bps) — gross numbers are for regression only

## 10. Deliberately not in scope

BTAL total-return correction (own spec: touches data conventions and needs a new snapshot
directory per the append-only rule); per-order fixed commissions and market-impact models
(false precision at this portfolio size, and commission is $0 at the assumed broker);
negative cash / margin; tax modelling (investeerimiskonto); synthetic pre-2010 history
(own spec, the financing model is the substance there).

**EUR→USD FX (~40–50 bp per contribution via Wise, tastytrade being USD-only)** is
deliberately not in the model: it is a haircut on external flow, hits every strategy
identically, and therefore cannot change any comparison or ranking this system produces —
it only shifts absolute levels. It belongs in real-world return expectations (roughly
−45 bp on contributed capital, once) and in the eventual implementation checklist
(convert via Wise, sweep idle USD to SGOV, limit orders on BTAL/KMLM/DBMF away from the
open/close), not in `Config`. If it ever matters for a model question — e.g. comparing a
UCITS-at-IBKR variant where FX is ~0 — that is a different broker assumption and a spec
revision, not a parameter.
