# Specification: net-of-withholding total-return dataset

Repo: `vlaas/balancing_portfolio` · baseline commit: `8b7303f` ("total-return merge", 365 tests green) · status: proposal

## 1. Goal

The gross-TR convention reinvests every distribution in full at the ex-date close. An
Estonian retail holder of US ETFs loses 15% treaty withholding (W-8BEN) on each
distribution, and that loss is final: not reclaimable from the IRS (it is the treaty
rate) and not creditable in Estonia, where the dividend is exempt under the
taxed-abroad rule (TuMS §18(1¹)) and, received into the investeerimiskonto, is
declared as a contribution. **The withholding applies to dividends and fund
distributions only — never to transactions.** A nonresident's US capital gains carry
no withholding at source (all six symbols are RIC ETFs, not PTPs, so §1446(f) never
fires), and realized trading P/L defers inside the investeerimiskonto until net
withdrawal — uniformly across every strategy being compared, so it cancels out of the
ranking. The distribution leak is therefore the *only* tax term that belongs in the
data, which is why the §2 construction scales the ex-date jumps and leaves every flat
(pure price movement) row bit-for-bit untouched. The resulting bias of the gross
convention *favors* high distributors, and — decisively for the safe-swap sweep — it
is **differential across exactly the candidates being compared**. Measured on the
`2026-08-20` snapshot via the implied distribution series (all numbers in this spec are
from sandbox runs at `8b7303f`):

| symbol | y gross | y net (w=0.15) | drag |
|---|---|---|---|
| TQQQ | 0.31%/yr | 0.26%/yr | ~5 bp/yr |
| BTAL | 1.07%/yr | 0.91%/yr | ~16 bp/yr |
| QQQ | 0.62%/yr | 0.53%/yr | ~9 bp/yr |
| SPY | 1.79%/yr | 1.52%/yr | ~27 bp/yr |
| DBMF | 5.81%/yr | 4.92%/yr | **~89 bp/yr** |
| KMLM | 4.38%/yr | 3.70%/yr | **~68 bp/yr** |

A gross safe-swap would hand DBMF/KMLM a known ~50–70 bp/yr head start over BTAL —
the same order as a plausible verdict margin. The fix is again a **data change, not an
engine change**: a committed generator script derives a net-TR dataset from the frozen
gross pair, and decision runs point `--data` at it. `prices.py`, `simulate.py`,
`indicators.py`, `stats.py`, `results_json.py`, `spec.py` are untouched;
`SCHEMA_VERSION` stays 4. The single code change outside the generator and tests is a
small provenance addition to `sweep.py` (§6), motivated by there now being three
dataset conventions with identical date ranges. Not in scope: §11.

## 2. Construction — normative

Inputs per symbol: the frozen pair `A` (gross-adjusted close) and `P` (price close)
with identical `time` columns; the ratio `R_t = A_t / P_t` and its log-steps
`Δ_t = ln R_t − ln R_{t−1}` (a positive step *into* row *t* marks *t* as an ex-date;
`k_t = R_{t−1}/R_t = 1 − D_t/P_{t−1}` is TV's back-adjustment factor).

### 2.1 Step classification

Three-way, with an asserted-empty middle so classification can never be ambiguous:

```
FLAT:  |Δ_t| ≤ FLAT_MAX          FLAT_MAX = 5e-6
JUMP:   Δ_t  ≥ JUMP_MIN          JUMP_MIN = 2e-5
DEAD:   FLAT_MAX < Δ_t < JUMP_MIN   → hard error
        Δ_t < −TAU                  → hard error (TAU = 1e-6, as in T2)
```

Constants pinned from the measured step distribution of the `2026-08-20` snapshot:
largest flat step 1.62e-6 (TQQQ; 3× below `FLAT_MAX`), smallest jump 5.08e-5 (BTAL;
2.5× above `JUMP_MIN`), worst negative step −4.31e-8 (TQQQ; 23× above −`TAU`), dead
zone empty on all six symbols. `FLAT_MAX` deliberately equals the existing T2 up-jump
criterion (`5·TAU`), so `test_total_return.py` and the generator agree on what a jump
is. (TQQQ's lone 1.62e-6 flat step implies a sub-hundredth-of-a-cent residue —
classifying it flat forgoes withholding of 0.15 × 1.6e-6 in log terms, irrelevant;
what matters is that the classification is deterministic.)

### 2.2 The net series

A withheld distribution reinvests `(1−w)·D` instead of `D`; in TV's multiplicative
convention that replaces each jump's factor by

```
k^net_s = w + (1−w) · k_s
```

The net series is built **from `A` directly**, not by recomposing `R^net · P`:

```
A^net_t = A_t · C_t,     C_t = ∏ over JUMP rows s > t of (k^net_s / k_s)
```

computed in one backward pass (`C = 1` at and after the last jump; multiply the
accumulator by `k^net_s/k_s` when passing jump row *s*). Reasons for this
formulation: flat rows preserve `A`'s own values bit-for-bit up to one multiplication;
`w = 0` gives `C ≡ 1.0` and hence output values *exactly* equal to the parent (a real
test, N6); and `ln(A^net/A) = ln C` is exactly a non-increasing step function, which
is what the scaled invariants pin. Since `k^net > k` for `w > 0`, `C_t ≥ 1` and
`R ≤ R^net ≤ 1`: the net series sits between gross-TR and price, anchored with them at
the last bar (`C_last = 1`, so `A^net_last = A_last = P_last`).

Consequences, each pinned by a test: the net jump set equals the gross jump set; the
implied net distribution at each jump is exactly `(1−w)·D` (measured reconstruction
error ≤ 1.6e-13 dollars across all 274 jumps); and the cumulative yield contracts to
`y^net/y^gross ∈ [0.98·(1−w), (1−w)]` — the upper bound is Bernoulli
(`(1−d)^{1−w} ≤ 1−(1−w)d`), the lower bound absorbs the second-order term of the
largest jumps (KMLM's 2022 distribution, `d ≈ 13%`, is the extreme). Measured for
`w = 0.15`: ratios 0.8441 (KMLM) to 0.8498 (TQQQ/QQQ), all inside
`[0.833, 0.85]`.

The definitions above are normative; the implementation may use Polars or plain
Python so long as §8's tests pass. Prefer `k_s = (A_{s−1}·P_s)/(A_s·P_{s−1})` (exact
ratios) over `exp(−Δ_s)`; either agrees far below the test tolerances.

## 3. Generator contract — `make_net_tr.py` (new, repo root, next to `fetch_dividends.py`)

```
uv run make_net_tr.py SRC_DIR [--withholding 0.15] [--out DST_DIR] [--force]
```

- `SRC_DIR` is a dataset root in the TOTAL_RETURN_SPEC §3 convention
  (`<SYM>.csv` + `price/<SYM>.csv`). Symbols are discovered from `SRC_DIR/*.csv`.
- `--withholding` in `[0, 1)`, default `0.15`. `--out` defaults to
  `<SRC_DIR>-net{round(w*100)}` (`tests/data/2026-08-20-net15`). An existing `DST_DIR`
  is refused without `--force` — regeneration for verification goes to a temp dir; the
  committed snapshot is written once.
- Per symbol: read the pair, assert identical `time` columns; classify steps per §2.1,
  **hard error** (named symbol, row date, step value) on any dead-zone or
  below-`−TAU` step; build `A^net` per §2.2; write `DST/<SYM>.csv` with columns
  `time,close` **only** — a generated file carries no `SMA*` reference columns, real
  or imitated (§7 for the T4 consequence).
- Copy `SRC/price/*.csv → DST/price/` byte-identical (self-containment: the net root
  is a complete, independently verifiable dataset whose invariants need `P`).
- Write `DST/README.md` from a template: parent snapshot, `w`, the §2.1 constants,
  and a per-symbol table of jump count and `y gross → y net`. **No timestamps
  anywhere** — the generator is deterministic and the committed snapshot must be
  byte-reproducible from the committed parent + committed code (N5). Stdout mirrors
  the README table.
- Validation errors before any file is written; a partial dataset is never left
  behind (write to `DST` only after all symbols computed).

## 4. Dataset convention and snapshot

- New frozen snapshot `tests/data/2026-08-20-net15/`, generated from
  `tests/data/2026-08-20/` and committed in the same PR as the generator. Append-only
  as always. The `-net15` suffix is the self-describing marker the TOTAL_RETURN_SPEC
  §3 naming rule anticipated; tests and the T4 filter key on `"-net"` in the path.
- **Live `data/` stays gross-TR.** No maintained live net twin: decision runs use
  frozen snapshots anyway (established protocol), and a live twin would add a
  regeneration step to every export for no consumer. A what-if net twin of any root
  is one generator invocation away.
- Dataset roles after this change, stated in the docs and CLAUDE.md protocol:
  **net-TR = decision series** (quote it, with dataset name and cost assumption);
  gross-TR = comparability to gross artefacts and the TR goldens; price = legacy
  regression only.

## 5. Signal series

Unchanged rule, one sentence in the docs: every indicator is computed on the `close`
of the file the loader reads — in a net dataset that is the net series. The QQQ
signals move by ≤ 15% of the already-measured gross-vs-price deltas (1 gate state of
115, ≤ 1.66% relative EWMA vol), so no new delta test is warranted; the uniform
convention simply carries over.

## 6. Sweep provenance — `sweep.py`

Sweep artefacts currently record only the date range (`summary.json` `data:
{start, end}`); with three conventions sharing identical ranges, the dataset is
identifiable only by output-directory naming. Additive fix, same self-description
precedent as the cost columns (COST_MODEL_SPEC §5):

- `summary.json` `data` block gains `"dir": str(data_dir)`;
- `summary.md` header gains a `- Data dir: …` line;
- `runs.csv` gains a constant `data_dir` column.

No schema field exists in sweep artefacts to bump. Committed artefact sets are files
and stay untouched; a rerun of an old spec now emits one more column, which is the
point.

## 7. Golden interaction

- All existing goldens — price, cost, TR, TR-cost — and all committed artefacts stay
  pinned to their snapshots, untouched. No engine or loader change exists to move
  them.
- `tests/test_indicators.py` `CSV_FILES` excludes any path with a `-net` dataset root
  (top-level net files have no `SMA*` columns; their `price/` copies are byte-verified
  duplicates of already-tested files). The compensating control against silent
  retirement: N1 asserts net top-level files carry **exactly** `time,close`, so
  unverified reference columns cannot ride in.
- **Net goldens** (N7): the `default` bundle on the net snapshot with
  `end = 2026-08-14` (the matched window shared by the price and TR goldens; the
  parent's calendar pin covers the net snapshot by byte-copy). Reference values from
  the §2 construction, which the implementation must reproduce to the cent — a larger
  deviation is a construction bug, not float noise (`C` is a product of ≤ 135 doubles;
  cross-implementation drift is ~1e-15 relative, ≪ $0.01):

  | strategy | final | CAGR | max DD |
  |---|---|---|---|
  | TQQQ/BTAL 50/50 | $254,913.36 | +24.67% | −44.78% |
  | TQQQ 100% | $688,470.64 | +42.22% | −81.67% |
  | TQQQ/BTAL SMA gate | $245,139.65 | +24.00% | −37.73% |
  | SPY benchmark | $167,200.29 | +15.21% | −33.74% |

  Eyeball guidance: for this bundle the net−gross gap is small (~−0.19%/yr CAGR on
  the 50/50) because BTAL's yield is small — the correction's weight is in the
  safe-swap universe, not here. The sandwich is the structural claim and is asserted
  cross-snapshot: `price < net < gross` finals for the 50/50 and the SPY benchmark.
- **Net cost golden**: same bundle under the tastytrade base schedule
  (`{"TQQQ": 1.5, "BTAL": 6, "QQQ": 1, "SPY": 0.7, "*": 6}`, `cash_yield = 0.03`) —
  the exact configuration of every decision run from here on, pinned by the
  implementation once.

## 8. Tests — `tests/test_net_tr.py` (new) plus the §7 T4 edit

Constants (`TAU`, `FLAT_MAX`, `JUMP_MIN`) are defined in `make_net_tr.py` and
imported by this module; `tests/test_total_return.py` keeps its own local `TAU`
untouched.

**N1 — Layout and self-containment.** `tests/data/2026-08-20-net15/` holds six
`<SYM>.csv` whose columns are exactly `time,close`; `price/<SYM>.csv` per symbol,
byte-identical (`filecmp`) to the parent snapshot's; `README.md` present. The `time`
column of each net file equals the parent's.

**N2 — Scaled ratio invariants.** Per symbol, with `R` from the parent pair and
`R^net = A^net/P`: `R − 1e-12 ≤ R^net ≤ 1 + 1e-6` everywhere;
`R^net_last = R_last`; `Q = ln(R^net/R) ≥ 0`, non-increasing forward
(steps ≤ 1e-12), exactly flat (|step| < 1e-12) off the parent's jump rows, and 0 from
the last jump on; the net jump set (steps ≥ `JUMP_MIN`) equals the parent's.

**N3 — Per-jump exactness.** At every parent jump row *s*:
`P_{s−1}·(1 − R^net_{s−1}/R^net_s) == (1−w) · P_{s−1}·(1 − R_{s−1}/R_s)` within
1e-9 dollars (measured ≤ 1.6e-13). This is the withholding semantics in one line; a
Polygon-anchored twin of the parent's T3 would be redundant with it and is
deliberately omitted.

**N4 — Yield contraction.** Per symbol, `y^net/y^gross ∈ [0.98·(1−w), (1−w) + 1e-12]`
(measured 0.8441–0.8498 at `w = 0.15`), with the Bernoulli upper bound and the
second-order lower bound stated in a comment.

**N5 — Byte-reproducibility.** Run the generator on the parent snapshot into a temp
directory with defaults; `filecmp` every produced file — six net CSVs, six price
copies, the README — against the committed net snapshot. This is the test that makes
the committed dataset exactly what the committed code produces; it is the analogue of
`results_json`'s byte-stability and the reason nothing in the generator may read a
clock.

**N6 — Generator guards.** On synthetic pairs: `w = 0` output closes equal the parent
adjusted closes exactly (`Series.equals`, the §2.2 formulation makes this exact); a
step planted at 1e-5 (dead zone) raises with symbol, date and value in the message;
a step below `−TAU` raises; `--withholding` outside `[0, 1)` and mismatched pair
`time` columns raise; an existing `--out` without `--force` is refused and leaves the
directory untouched.

**N7 — Net goldens** per §7, including the cross-snapshot sandwich asserts.

**N8 — Sweep provenance.** A small sweep run (reuse the existing 2×2 fixture) shows
the data directory in `summary.json` `data.dir`, the `summary.md` header line, and a
constant `runs.csv` `data_dir` column.

## 9. Rerun protocol — what this spec exists for

After merge and snapshot commit:

```
uv run sweep.py specs/sweep_vt_cbase.json --data tests/data/2026-08-20-net15 --out results/sweep_vt_net_cbase
```

Read against `results/sweep_vt_tr_cbase` as a **confirmation gate, not an
experiment**: for the TQQQ/BTAL universe the net correction is ~16 bp/yr on half the
book, so the expected outcome is a near-identical plateau (top-15 overlap), an intact
gate advantage, and 96/96 over the gated 50/50 — one verdict sentence for memory. Any
material movement means the generator or the read of §1 is wrong. This run also
produces the candidate's net-cbase numbers, the ones all future comparisons quote.

Then the safe-swap sweep spec (`safe ∈ {BTAL, DBMF, KMLM, null}`) is written **against
the net snapshot** — DBMF and KMLM are precisely where gross-vs-net moves the verdict,
which is why this spec lands first.

## 10. Acceptance checklist

- [ ] `make_net_tr.py` per §3: classification constants, §2.2 construction, README
      template, `--force` guard, deterministic output
- [ ] `tests/data/2026-08-20-net15/` committed, generated by the committed script
      from the committed parent (N5 is the proof)
- [ ] `sweep.py` provenance per §6
- [ ] `tests/test_net_tr.py` N1–N8; `tests/test_indicators.py` net-root exclusion;
      whole suite green from a fresh clone with `pip install polars matplotlib pytest`
- [ ] No change to `prices.py`, `simulate.py`, `indicators.py`, `stats.py`,
      `results_json.py` (`SCHEMA_VERSION` stays 4), `spec.py`
- [ ] Docs: STRATEGY_DEVELOPMENT (net convention, dataset roles); ARCHITECTURE (the
      generator in the data-flow paragraph, sweep provenance fields); data READMEs;
      CLAUDE.md protocol: **decision numbers come from the net-TR dataset at stated
      costs** — gross-TR for comparability to gross artefacts, price for legacy
      regression
- [ ] §9 rerun committed: `results/sweep_vt_net_cbase/*`

## 11. Deliberately not in scope

- **Per-symbol withholding rates.** Flat 15% on every distribution is an **upper
  bound**: US RIC distributions to nonresident aliens can include exempt components —
  capital-gain distributions, return of capital, and §871(k) interest-related /
  short-term-gain dividends where the fund reports them — so the true drag on
  DBMF/KMLM is *at most* the §1 figures and plausibly lower. Modelling that needs
  fund-level 1042-S-grade detail. Tripwire, mirroring the last spec's: if the
  safe-swap verdict *against* a managed-futures candidate is within its ~70–90 bp/yr
  upper-bound drag, a per-symbol `--withholding {"SYM": w, "*": w}` extension (same
  mapping pattern as `cost_bps`) gets specified before the verdict is trusted — the
  candidate would deserve the benefit of the doubt it loses under the flat rate. The
  15%-unrecoverable-inside-investeerimiskonto premise itself is the user's tax fact
  to confirm, not something this repo can verify.
- **Pay-date cash modelling** (distribution arrives as cash, reinvests at the next
  rebalance): engine change, second-order timing effect, same verdict as before.
- **A maintained live net twin** (§4) and net twins of the price-series snapshots
  (nothing consumes them).
- **The safe-swap sweep spec** — next in line, blocked on this one; its design
  content is the KMLM-constrained window problem, not the data.
