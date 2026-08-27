# Specification: the cash sleeve — BIL, BTAL, and the fraction between them

Repo: `vlaas/balancing_portfolio` · baseline commit: `be6b2d0` (synthetic history
merged; 876 tests green on a fresh clone) · status: **proposed** · inputs:
`SAFE_SWAP_SPEC.md` §6.7 and §9 (the BIL follow-up, "fired by §6.7 or on its own
merits if the cash arm contends anywhere"), `notes/syn-verdict.md` §3 and prediction 8
(the cash arm contended: BIL beat BTAL on Calmar at the winners' coordinate on the
2012 lane) · predecessors: `notes/safe-swap-verdict.md`, `notes/safe-blend-verdict.md`.

## 1. Goal

The safe-swap lane could not price cash. Its cash arm earned a flat 3 %/yr over a
decade in which T-bills paid ~0, so a BTAL loss to it was ruled inconclusive and BIL was
designated the follow-up (SAFE_SWAP §6.7, §9). The preconditions are now met — a paired
same-session BIL export in the 2026-08-24 roots, its adjustment semantics pinned by
the live-pair battery (T4, yield 1.39 %/yr) and by SYNTHETIC_HISTORY S3 (a T-bill
accrual reproduces BIL's total return with a residual equal to its expense ratio) —
and the synthetic-history bridge has already produced the number that fires the
follow-up: on real 2012–2026 bars at the winners' coordinate, `VT TQQQ/BIL` prints
Calmar 0.7991 against `VT TQQQ/BTAL`'s 0.6999, buying 3.45 pp of CAGR for 1.08 pp of
drawdown.

This spec asks the question that number raises, on real data only, with no engine
work: **how much of the sleeve should be BTAL, and how much cash?** Three lanes — the
2012 lane where BTAL's drift has fourteen years to compound, the 2021 lane where the
winners were chosen and 2022 is one year in six, and the 2019 lane with COVID inside —
each reading the same **single pre-registered candidate**: replace half the sleeve's
BTAL with BIL. The bar is the safe-blend verdict's, unchanged: a sleeve is promoted
only if it beats what it replaces *and* does not deepen the window floor. A sleeve that
buys Calmar with return at a drawdown cost is reported as the trade it is and handed
back, as the safe-swap verdict handed back the managed-futures arms.

Three measured facts shaped the design (§2 has the tables):

- **BTAL's drift is the cost and its anti-beta is the product.** Over 2012–2026 BTAL
  compounded at −3.43 %/yr net against BIL's +1.29 %, and at −5.97 % against +2.66 %
  since the winners' lane began; yet in every one of TQQQ's eight worst months since
  2012 it printed +2.8 % to +9.3 % (monthly correlation −0.61). The sleeve pays ~4.7
  pp/yr for insurance it collects on eight month-ends in fourteen years.
- **The right BTAL fraction depends on the coordinate.** On the 2012 lane pure BTAL
  is the best sleeve at σ0.30 (both w_max) and at σ0.25 / w0.8; a 75/25 blend is best
  at σ0.25 / w0.6 and σ0.20 / w0.6; and at the winners' coordinate σ0.20 / w0.8 the
  best sleeve holds 25–50 % BTAL and pure BTAL is last of five. The pilot does not
  supply a one-line mechanism (a larger sleeve at w0.6 wants *more* BTAL, not less),
  and the spec does not pretend to one.
- **The winners' lane prices 2022 and the 2012 lane prices the decade around it.** At
  σ0.20 on the 2021 lane, the half-BTAL sleeve improves two of three winners on Calmar
  and gives back 0.8–1.5 pp of full-window drawdown; on 2022 alone it loses 4–5 pp to
  the BTAL-heavy sleeve. That is the trade the bar is written to price.

The net15 convention over-withholds BIL: its income is US Treasury interest, the
clearest §871(k) case in the universe, so its true NRA withholding is plausibly ~0 %.
The bias is measured (0.23 pp/yr of sleeve return on the 2012 lane, 0.47 on the 2021
lane) and read one-sidedly (§10): a BIL-containing sleeve that wins on net15 wins a
fortiori; one that loses inside the bias band triggers a per-symbol-rate root before
any conclusion.

## 2. What is already true at `be6b2d0` (measured on this clone)

### 2.1 The sleeve candidates on real data (net15 unless stated)

| symbol · window | CAGR net15 | CAGR gross | withholding bias | max DD | 2020 | 2022 | 2025 |
|---|---|---|---|---|---|---|---|
| BTAL · 2012-01-03 → | **−3.43 %** | −3.29 % | 0.14 pp/yr | −52.70 % | −13.7 % | **+21.5 %** | −20.2 % |
| BIL · 2012-01-03 → | **+1.29 %** | +1.52 % | **0.23 pp/yr** | −0.35 % | +0.3 % | +1.2 % | +3.5 % |
| KMLM · 2020-12-18 → | +6.17 % | +6.90 % | 0.73 pp/yr | −27.47 % | — | +27.1 % | −4.4 % |
| DBMF · 2019-05-08 → | +8.29 % | +9.26 % | 0.97 pp/yr | −20.39 % | +0.3 % | +19.1 % | +12.0 % |
| BTAL · 2020-12-18 → | −5.97 % | −5.65 % | 0.33 pp/yr | −47.83 % | | | |
| BIL · 2020-12-18 → | +2.66 % | +3.13 % | **0.47 pp/yr** | −0.13 % | | | |

Monthly correlation with TQQQ, 2012 →: BTAL −0.610, BIL −0.002. TQQQ's eight worst
months since 2012 and BTAL in the same month: 2020-03 −38.1 / **+9.3**; 2022-04 −37.2 /
+8.5; 2022-09 −30.5 / +2.8; 2022-06 −27.4 / +7.6; 2018-12 −26.8 / +4.2; 2018-10 −26.6 /
+5.6; 2022-12 −26.2 / +3.5; 2022-01 −25.7 / +5.2. BTAL was positive in all eight.

### 2.2 BIL's pair on the 2026-08-24 root

4,840 rows from 2007-05-30; unadjusted price 91.22–92.48 over nineteen years (a T-bill
fund's price is flat by construction); implied yield 1.387 %/yr; 125 ex-date jumps
(monthly, with the ZIRP years' near-zero distributions below the jump floor); most
recent implied amounts $0.2699 (2026-05-01), $0.2692 (2026-06-01), $0.2676
(2026-07-01), $0.2730 (2026-08-03). The live-pair battery pins BIL at 1.39 %/yr as the
"positive control at the other end — nearly all of its return is distribution". BIL is
**not** in the golden-root `SYMBOLS` battery (T1–T3 run on the 2026-08-20 root, which
predates the paired BIL export) and has no `dividends/BIL.parquet`; §6 B1 closes that.

### 2.3 What the grammar already does

`safe` accepts a weighted dict (SAFE_BLEND_SPEC); three-way dicts and non-integer
percentages build and render today — `{"BIL": 0.375, "BTAL": 0.375, "KMLM": 0.25}` →
`BIL37.5+BTAL37.5+KMLM25`, slug `bil37-5-btal37-5-kmlm25` (verified in the pilot
through `main.py`). A `safe` grid in a sweep is categorical (whole dicts), so the
BTAL-fraction surface has no `neighbour_min`; the verdict reads it by hand as the blend
verdict did. No engine, grammar or runner change is needed anywhere in this spec.

### 2.4 The pilot in one table (full windows, §11 has the rest)

`VT TQQQ/<sleeve> σ0.20 w_max 0.8 λ0.80 gate SMA-200`, net15, Calmar · CAGR · max DD:

| lane | BTAL | 75 / 25 | **50 / 50** | 25 / 75 | BIL |
|---|---|---|---|---|---|
| 2012 → | 0.6999 · 18.21 · −26.02 | 0.8005 · 19.17 · −23.95 | **0.8208 · 20.06 · −24.44** | 0.8217 · 20.89 · −25.43 | 0.7991 · 21.66 · −27.10 |
| 2019 → | 0.6280 · 16.34 · −26.02 | | **0.9765 · 18.95 · −19.40** | | 0.8520 · 21.15 · −24.82 |
| 2021 → | 0.6347 · 13.93 · −21.96 | | | | 0.7440 · 18.22 · −24.49 |

At the winners' σ, pure BTAL is the worst sleeve of five on the 2012 lane and the
worst of three on the other two; the 50/50 sleeve beats *both* its components on
Calmar and on max drawdown on the 2012 and 2019 lanes — the blend verdict's "strictly
dominates" shape, on real bars. That is why the candidate is a half-swap and not a
full one.

## 3. The candidate — one transformation, pre-registered

**T: replace half of a sleeve's BTAL weight with BIL.** Applied to the winners:

| winner | sleeve today | after T | BIL twin (the surface's far endpoint, not a candidate) |
|---|---|---|---|
| B75K25 | `BTAL75+KMLM25` | **`BIL37.5+BTAL37.5+KMLM25`** | `BIL75+KMLM25` |
| B75D25 | `BTAL75+DBMF25` | **`BIL37.5+BTAL37.5+DBMF25`** | `BIL75+DBMF25` |
| B50K50 | `BTAL50+KMLM50` | **`BIL25+BTAL25+KMLM50`** | `BIL50+KMLM50` |

and to the pure-BTAL sleeve, `BTAL` → `BIL50+BTAL50`. T is the only thing this spec
can adopt. The full BIL twins, pure BIL, and the 75/25 and 25/75 points are the
fraction surface around it, run so the verdict can say where on the surface T sits and
whether the surface is monotone — they are not candidates, and a twin that outscores T
somewhere does not become one (that would be a grid search on a categorical
dimension with no neighbourhood, i.e. the thing SWEEP_SPEC §4.6 forbids).

## 4. Lanes

All on `tests/data/2026-08-24-net15`, objective Calmar, constraint max drawdown ≥ −50 %,
contributions 10 000 + 500 / month, `cash_yield` 0.03 (uninvested residue only — BIL
*is* the cash), the blend cost map plus `BIL 0.5` bp per side. Windows copied from the
lane each one extends so that every incumbent arm reproduces its committed number.

### 4.1 `specs/sweep_cash_2012.json` — the fraction surface across σ (30 points)

Windows as `sweep_comp_2012` (start 2012-01-03, holdout 2023-01-01, sensitivity 6 m /
5 y → 23 windows). Template: gate SMA-200, λ0.80, `safe` ∈ {`BTAL`, `BIL25+BTAL75`,
`BIL50+BTAL50`, `BIL75+BTAL25`, `BIL`} (categorical) × `sigma_target` ∈ {0.20, 0.25,
0.30} × `w_max` ∈ {0.6, 0.8} (both numeric → neighbours in σ and w). Baselines: gated
`TQQQ50/BTAL50`, gated `TQQQ50/BIL50`, SPY. Anchors: the `BTAL` arm at σ0.30 / w0.6
reproduces 0.86123626; at σ0.20 / w0.8, `BTAL` 0.6999 and `BIL` 0.7991 reproduce
`syn_bridge_2012`.

### 4.2 `specs/sweep_cash_2021.json` — the winners and T (24 points)

Windows as `sweep_blend_2021` (start 2020-12-18, holdout 2025-01-01, sensitivity 6 m /
3 y → 9 windows; the runner's "test window shorter than 2 years" warning applies and
is quoted). Template: gate SMA-200, λ0.80, w_max 0.8, `sigma_target` ∈ {0.20, 0.25},
`safe` ∈ the twelve sleeves — the three winners, their three T-transforms, their three
BIL twins, `BTAL`, `BIL`, `BIL50+BTAL50`. Baselines: gated `TQQQ50/BTAL50`, SPY.
Anchors: the three winners at σ0.20 reproduce `sweep_comp_2021`'s `G_sma` rows
(0.8529 / 0.8574 / 0.8849 full; 0.8470 / 0.8574 / 0.8849 robust).

### 4.3 `specs/sweep_cash_2019.json` — COVID inside (12 points)

Windows as `sweep_blend_2019` (start 2019-05-08, holdout 2024-01-01, sensitivity 6 m /
3 y → 12 windows). `safe` ∈ {`BTAL`, `BIL`, `BIL50+BTAL50`, `BTAL75+DBMF25`,
`BIL37.5+BTAL37.5+DBMF25`, `BIL75+DBMF25`} × `sigma_target` ∈ {0.20, 0.25}, w_max 0.8.
Anchor: `BTAL75+DBMF25` at σ0.20 reproduces `sweep_comp_2019` (0.9362 full, 0.9187
robust).

### 4.4 Brackets — `_tr` and `_c20` twins of §4.1 and §4.2

Each rerun on the gross root `tests/data/2026-08-24` (`--out results/sweep_cash_2012_tr`
etc.) and with `cost_bps: {"*": 20}` on net15 (`_c20`). The gross root is also the
"BIL at its true withholding" reading, with every other symbol flattered alongside —
useful as a bound, not as a per-symbol bracket (§10.5 has the per-symbol root, built
only if needed).

### 4.5 Panels — `specs/cash_points_2012.json`, `specs/cash_points_2021.json`

The five 2012-lane sleeves at σ0.20 / w0.8 and σ0.30 / w0.6 (10 strategies + SPY) on
the 2012 window, and the twelve 2021-lane sleeves at σ0.20 (+ SPY) on the 2021
window, `--json` for `drawdowns` and `yearly_returns`: the per-episode panel (2015-08,
2018-Q4, COVID, 2022, 2025, 2026) and the 2020 / 2022 / 2025 calendar years, which
`runs.csv` cannot supply.

### 4.6 Size

`--dry-run`: 33 × 23 = 759 (× 3 with brackets), 26 × 9 = 234 (× 3), 14 × 12 = 168, two
bundles of 11 and 13 — about 3,150 runs, under ten minutes. Dual pre-flight (handoff
§6): every symbol read is real from before every lane's start (BIL 2007-05-30, BTAL
2011-09-13, DBMF 2019-05-08, KMLM 2020-12-18); no indicator is wider than SMA-200 on
QQQ; the loader's completeness assert covers the traded set.

## 5. No engine work

`prices.py`, `simulate.py`, `indicators.py`, `stats.py`, `results_json.py`,
`strategy.py`, `strategies/*`, `spec.py`, `sweep.py`: **untouched**. `SCHEMA_VERSION`
stays 4. Everything in §4 is expressible in today's grammar and was run through
`main.py` unmodified in the pilot.

## 6. Tests — new `tests/test_cash_sleeve.py`, one addition in `tests/test_total_return.py`

Cite as "CASH_SLEEVE_SPEC B·".

**B1 — BIL enters the golden battery.** `uv run fetch_dividends.py BIL` →
`dividends/BIL.parquet` (Polygon's reference data reaches BIL's 2015+ monthly
distributions; the pre-2015 boundary is printed as SYNTHETIC_HISTORY erratum 7 made
it). Two entries in `DISTRIBUTIONS["BIL"]` from that parquet, checked against the
2026-08-24 root's implied amounts to $0.0001 (T3's tolerance). Because the golden
`ROOTS` list holds the 2026-08-20 root, which has no paired BIL, the test adds the
2026-08-24 root to `ROOTS` for T1–T3 and the paired-symbol list becomes per-root: the
2026-08-20 root keeps its six, the 2026-08-24 root runs seven. SAFE_SWAP §9's
precondition (2) is thereby met on the goldens, not only on the live pair.

**B2 — The withholding bias is pinned.** BIL gross-minus-net15 CAGR on 2012-01-03 →
2026-08-24 = 0.23 ± 0.02 pp/yr; on 2020-12-18 → = 0.47 ± 0.02 pp/yr. These are the
numbers §10.5's one-sided read is stated against, so a data refresh that moves them
moves the read.

**B3 — Three-way sleeves round-trip.** `{"BIL": 0.375, "BTAL": 0.375, "KMLM": 0.25}`
builds, renders `BIL37.5+BTAL37.5+KMLM25`, slugs `bil37-5-btal37-5-kmlm25`, normalises
and rebuilds to the same normalised spec; a sweep `safe` grid over two three-way dicts
renders both in `params.safe` and expands to two points. (Grammar already does this;
the test pins it because §4 depends on it.)

**B4 — Anchors through the new specs.** Each spec's `--dry-run` count per §4.6; the
`BTAL` σ0.30 / w0.6 arm of §4.1 on net15 → 0.86123626 / 0.23817105 / −0.27654555
through `run_bundle`; the σ0.20 / w0.8 `BTAL` and `BIL` arms → 0.69991357 and
0.79914190 (the bridge's values, 8 decimals from `results/syn_bridge_2012.json`).

**B5 — Sleeve facts.** The §2.1 CAGR / max-drawdown cells for BTAL and BIL on the 2012
and 2021 windows to 0.02 pp; the eight worst TQQQ months and BTAL's sign in each
(all positive) from the net15 root's month-end closes.

## 7. Docs

- `docs/WINNING_STRATEGIES.md` (or its successor): changed only if §10.6 adopts;
  otherwise gains the §10.6(b) sentence. **Created** by this spec's verdict, the
  file having been named by four specs and never written (erratum 7).
- `docs/SAFE_SWAP_SPEC.md` §9: the BIL follow-up gains a pointer to this spec and its
  verdict; `docs/HANDOFF_COMPOSITION.md` §7 likewise.
- `docs/COST_MODEL_SPEC.md`: `BIL 0.5` bp per side added to the cost table with the
  reason (a T-bill ETF at one tick, spread 1 ¢ on $92).
- `CLAUDE.md` §6, one line: *cash in a sleeve is `BIL`, a traded symbol with real
  distributions; `cash_yield` is for uninvested residue only.*

## 8. Run protocol

```
uv run fetch_dividends.py BIL && uv run pytest                                    # B1–B5 green
uv run sweep.py specs/sweep_cash_2012.json --data tests/data/2026-08-24-net15 --out results/sweep_cash_2012
uv run sweep.py specs/sweep_cash_2012.json --data tests/data/2026-08-24       --out results/sweep_cash_2012_tr
uv run sweep.py specs/sweep_cash_2012_c20.json --data tests/data/2026-08-24-net15 --out results/sweep_cash_2012_c20
uv run sweep.py specs/sweep_cash_2021.json --data tests/data/2026-08-24-net15 --out results/sweep_cash_2021
uv run sweep.py specs/sweep_cash_2021.json --data tests/data/2026-08-24       --out results/sweep_cash_2021_tr
uv run sweep.py specs/sweep_cash_2021_c20.json --data tests/data/2026-08-24-net15 --out results/sweep_cash_2021_c20
uv run sweep.py specs/sweep_cash_2019.json --data tests/data/2026-08-24-net15 --out results/sweep_cash_2019
uv run main.py --spec specs/cash_points_2012.json --data tests/data/2026-08-24-net15 --json results/cash_points_2012.json --no-charts --quiet
uv run main.py --spec specs/cash_points_2021.json --data tests/data/2026-08-24-net15 --json results/cash_points_2021.json --no-charts --quiet
```

(`_c20` specs are the primaries with `cost_bps` replaced, as the rotation program's
were.) Commit order: (1) B1's parquet + tests + docs; (2) the **pre-registration
commit** — the seven specs, §3's candidate, §10's bars and §11's predictions, before any
run; (3) artefacts; (4) the verdict. Confirm every §4 anchor before reading a single
new number.

## 9. Read protocol

Steps in order; every number from `summary.json`, `runs.json`, or the two bundles.

0. **Anchors** (§4.1–4.3) reproduce; the 2021 lane's holdout warning is quoted.
1. **The surface, §4.1.** For each (σ, w_max): the five sleeves' `robust_score`, full
   Calmar, CAGR, max drawdown, holdout test, `rank_worst`, and the **window floor** —
   the minimum over sensitivity windows of max drawdown, from `runs.json`. Where on the
   fraction does the best sleeve sit at each σ, and is the surface monotone between
   its endpoints? The pre-registered shape: the best BTAL fraction rises with σ.
2. **T on the 2012 lane** at σ0.20 / w0.8 and σ0.30 / w0.6: `BIL50+BTAL50` vs `BTAL`
   on all of step 1's columns.
3. **T on the winners' lane, §4.2**, per winner: the T-transform vs the winner on
   `robust_score`, full Calmar, CAGR, max drawdown, holdout test, `rank_worst`, window
   floor; then the BIL twin beside it as the surface's endpoint. Then the 2022 and
   2025 calendar years from `cash_points_2021.json` — the year T pays and the year it
   collects.
4. **T on the COVID lane, §4.3**: `BIL37.5+BTAL37.5+DBMF25` vs `BTAL75+DBMF25`, and
   `BIL50+BTAL50` vs `BTAL`, same columns; the 2020 calendar year.
5. **Brackets.** Every step-2/3 comparison re-read on `_tr` and `_c20`: same sign or
   not. The withholding read of §10.5.
6. **Exposure control** (SAFE_SWAP §6.5, mandatory): average and minimum TQQQ weight
   for every compared pair — a sleeve must not win by holding more TQQQ. (The VT
   sizing does not see the sleeve, so the pilot shows identical `wT` to three
   decimals; the column is printed anyway.)
7. **The decision, §10.6.**

## 10. Decision rule — frozen at the pre-registration commit

10.1 **The bar is the safe-blend verdict's.** A sleeve *replaces* the one it is
compared with only if it (i) beats it on `robust_score` by more than 0.02, (ii) has a
`rank_worst` not worse, (iii) a holdout test not worse, **and (iv) a window floor not
deeper** (its minimum sensitivity-window max drawdown ≥ the incumbent's). Clause (iv) is
what separates a complement from a trade: the blend verdict promoted `BTAL75+KMLM25`
because it had "more return and a shallower drawdown, not a trade between them", and
this spec cannot use a weaker standard to move the other way.

10.2 **"Not worse" for a third winner** means `robust_score` within −0.02, `rank_worst`
not worse by more than one, and clause (iv).

10.3 **T is adopted for the winners' set** only if: (a) on §4.1 at σ0.20 / w0.8,
`BIL50+BTAL50` replaces `BTAL` under 10.1; (b) on §4.2, T replaces the winner under 10.1
for at least two of the three winners and is not worse (10.2) for the third; (c) on
§4.3, T is not worse (10.2) for `BTAL75+DBMF25`; (d) every clause of (a)–(c) keeps its
sign on both brackets; (e) §10.5 does not veto. If adopted, all three transformed
sleeves become the winners (the set stays coherent; 10.3(b)'s third-winner clause is
what protects it), the previous three are retained in the winners file as "prior
winners, sleeve superseded", and every quoted number comes from these artefacts.

10.4 **If (a) holds and (b) fails** — the pre-registered expectation, §11 — the
verdict is **era-dependence, no adoption**: at the winners' σ the 2012 and 2019 lanes
say the sleeve carries too much BTAL, the winners' lane says 2022 is what the BTAL was
for. The winners file gains one sentence: *"At σ0.20, pure BTAL is dominated by a
half-BTAL / half-BIL sleeve on the 2012 and 2019 lanes; the BTAL-heavy sleeves were
chosen on a lane where 2022 is one year in six, and the half-swap buys Calmar there
with return at a 0.8–1.5 pp drawdown cost (CASH_SLEEVE_SPEC, `notes/cash-verdict.md`)."*
No sleeve moves.

10.5 **The withholding read, one-sided.** The net15 convention costs a BIL-containing
sleeve `0.23 × f_BIL` pp/yr of sleeve return on the 2012 lane and `0.47 × f_BIL` on the
2021 lane, where `f_BIL` is BIL's weight in the sleeve (B2). A T-transform that clears
10.1 on net15 clears it a fortiori at BIL's true rate. A T-transform that **fails
clause (i) by less than 0.02** on a lane — the band inside which the bias could
plausibly flip the sign — is *inconclusive on that lane*, and then, and only then,
`make_net_tr.py` gains a per-symbol override (`--rate-override BIL=0`, output root
`2026-08-24-net15-bil0`, append-only, README naming the override) and the affected
lane is rerun there as the tie-breaker. Clauses (ii)–(iv) are not subject to the read:
a rank or a floor does not move by a quarter-point of yield.

10.6 **Outputs.** (a) Adoption per 10.3, or (b) the 10.4 sentence. Either way: the
fraction surface of step 1 is recorded per σ, and `BTAL` at σ0.20 is flagged
*"dominated by `BIL50+BTAL50` on every real lane at this σ"* wherever it is quoted as a
baseline — including this spec's own §4.1 baseline row in future lanes, which becomes
`BIL50+BTAL50` if the flag holds. Verdict: `notes/cash-verdict.md`, steps 0–7 plus
residuals.

## 11. Pilot measurements — what to expect, and what would falsify it

Every number below is from `main.py` on the committed roots through the unmodified
grammar, full windows (and the holdout windows where stated); no sensitivity windows,
no ranks, no floors. Expectations, not findings.

**2012 lane, gate SMA-200, λ0.80, net15 — full window, Calmar · CAGR · max DD:**

| σ / w_max | BTAL | 75/25 | 50/50 | 25/75 | BIL |
|---|---|---|---|---|---|
| **0.20 / 0.8** | 0.6999 · 18.21 · −26.02 | 0.8005 · 19.17 · −23.95 | **0.8208 · 20.06 · −24.44** | 0.8217 · 20.89 · −25.43 | 0.7991 · 21.66 · −27.10 |
| 0.20 / 0.6 | 0.6590 · 16.95 · −25.72 | **0.8527 · 17.84 · −20.93** | 0.8311 · 18.67 · −22.46 | 0.7947 · 19.43 · −24.45 | 0.7613 · 20.12 · −26.43 |
| 0.25 / 0.6 | 0.8272 · 20.75 · −25.09 | **0.9126 · 21.49 · −23.55** | 0.8594 · 22.17 · −25.80 | 0.8110 · 22.79 · −28.11 | 0.7669 · 23.36 · −30.46 |
| 0.25 / 0.8 | **0.8016 · 22.13 · −27.60** | 0.7938 · 22.95 · −28.90 | 0.7847 · 23.71 · −30.22 | 0.7744 · 24.42 · −31.54 | 0.7630 · 25.08 · −32.87 |
| **0.30 / 0.6** | **0.8612 · 23.82 · −27.65** | 0.8350 · 24.43 · −29.26 | 0.8020 · 24.98 · −31.15 | 0.7698 · 25.48 · −33.10 | 0.7386 · 25.93 · −35.11 |
| 0.30 / 0.8 | **0.8082 · 25.77 · −31.89** | 0.8063 · 26.44 · −32.80 | 0.8028 · 27.07 · −33.72 | 0.7976 · 27.64 · −34.66 | 0.7757 · 28.17 · −36.32 |

Holdout 2023-01-03 → at σ0.20 / w0.8: BTAL 0.9750, 75/25 1.1455, 50/50 1.2901, 25/75
1.3008, BIL 1.2849, SPY 1.1893. Calendar years at σ0.20 / w0.8 (BTAL → BIL, five
sleeves): 2020 +15.3 / +19.1 / +22.8 / +26.4 / +29.8; **2022 −8.9 / −12.1 / −15.2 /
−18.4 / −21.6**; 2025 +15.1 / +18.1 / +21.1 / +24.1 / +27.0. Gross root, σ0.20 / w0.8:
0.7052 / 0.8088 / 0.8299 / 0.8290 / 0.8069; flat-20: 0.6632 / 0.7483 / 0.7671 / 0.7603 /
0.7462; σ0.30 / w0.6 gross 0.8691 / 0.8431 / 0.8105 / 0.7784 / 0.7473, flat-20 0.8442 /
0.8169 / 0.7846 / 0.7534 / 0.7232 — same orderings as net15 on both.

**2021 lane, σ0.20 / w0.8 — full · holdout 2025-01-02 → · gross · flat-20 Calmar, then
CAGR · max DD, then 2022 · 2025:**

| sleeve | full · test · gross · c20 | CAGR · max DD | 2022 · 2025 |
|---|---|---|---|
| `BTAL75+KMLM25` (winner) | 0.8529 · 0.8470 · 0.8708 · 0.8161 | 16.26 · −19.06 | **−6.2** · +16.5 |
| **T: `BIL37.5+BTAL37.5+KMLM25`** | **0.9018** · 1.1876 · 0.9304 · 0.8545 | 17.93 · −19.89 | −11.1 · +20.9 |
| `BIL75+KMLM25` | 0.8778 · 1.2894 · 0.9055 · 0.8326 | 19.41 · −22.11 | −16.1 · +25.3 |
| `BTAL75+DBMF25` (winner) | 0.8574 · 0.8825 · 0.8767 · 0.8195 | 16.35 · −19.07 | **−7.3** · +18.7 |
| **T: `BIL37.5+BTAL37.5+DBMF25`** | **0.8771** · 1.2109 · 0.9081 · 0.8294 | 18.01 · −20.53 | −12.2 · +23.1 |
| `BIL75+DBMF25` | 0.8564 · 1.2668 · 0.8877 · 0.8107 | 19.48 · −22.74 | −17.2 · +27.6 |
| `BTAL50+KMLM50` (winner) | **0.8849** · 1.1674 · 0.9108 · 0.8417 | 18.49 · −20.90 | **−4.7** · +17.9 |
| **T: `BIL25+BTAL25+KMLM50`** | 0.8757 · 1.2563 · 0.9030 · 0.8336 | 19.57 · −22.35 | −8.1 · +20.8 |
| `BIL50+KMLM50` | 0.8631 · 1.2737 · 0.8926 · 0.8238 | 20.53 · −23.79 | −11.7 · +23.7 |
| `BTAL` | 0.6347 · 0.5610 · 0.6455 · 0.6053 | 13.93 · −21.96 | −7.7 · +15.0 |
| `BIL` | 0.7440 · 1.2927 · 0.7645 · 0.7086 | 18.22 · −24.49 | −20.6 · +26.9 |
| SPY | 0.6059 · 0.9983 · 0.6252 · 0.5982 | 14.82 · −24.45 | −18.2 · +17.4 |

**2019 lane, σ0.20 / w0.8, full, net15:** `BTAL` 0.6280 · 16.34 · −26.02; `BIL` 0.8520
· 21.15 · −24.82; `BIL50+BTAL50` **0.9765 · 18.95 · −19.40**; `BTAL75+DBMF25` 0.9362 ·
18.83 · −20.11; T `BIL37.5+BTAL37.5+DBMF25` **0.9852** · 20.71 · −21.02; `BIL75+DBMF25`
0.9592 · 22.35 · −23.30. Calendar 2020: +15.2 / +29.8 / +22.7 / +19.1 / +24.6 / +29.9.

Predictions, each a falsifiable line for the verdict:

1. **The surface is single-peaked at every coordinate, and the peak's BTAL fraction
   is where §1 says it is**: 25–50 % at σ0.20 / w0.8 with pure BTAL last of five;
   75 % at σ0.20 / w0.6 and σ0.25 / w0.6; 100 % at σ0.25 / w0.8 and both σ0.30
   coordinates, monotone down to BIL. Falsified by a σ0.30 point other than `BTAL`
   on top, by pure BTAL above the midpoint at σ0.20 / w0.8, or by a non-single-peaked
   row.
2. **10.3(a) holds.** `BIL50+BTAL50` beats `BTAL` at σ0.20 / w0.8 on the 2012 lane by
   +0.12 full Calmar with 1.6 pp *less* drawdown, +1.85 pp CAGR, and a holdout test of
   1.29 vs 0.98; expected to clear all four clauses of 10.1 including the floor, on
   both brackets (gross +0.125, flat-20 +0.104). Falsified if it fails any clause.
3. **10.3(b) fails on clause (iv), and the expected outcome is 10.4.** T's full-window
   drawdown is deeper than the winner's on all three (−19.89 vs −19.06; −20.53 vs
   −19.07; −22.35 vs −20.90), and the window floor is set by the 2022-containing
   sensitivity windows where the BTAL-heavy sleeve is shallower (2022 calendar year:
   T gives back 4.9 / 4.9 / 3.4 pp). T is a return trade on this lane: +1.67 / +1.66 /
   +1.08 pp of CAGR. On clause (i) alone it would pass for B75K25 (+0.049 full; robust
   expected ≈ full since its holdout is 1.19 against the winner's holdout-bound 0.847)
   and sit at the bar for B75D25 (+0.020), and fail for B50K50 (−0.009). Falsified if
   T's floor is not deeper than the winner's for two of three.
4. **The BIL twins are the far endpoint, not a better candidate**: they add CAGR
   (+3.15 / +3.13 / +2.04 pp) and drawdown (+3.0 / +3.7 / +2.9 pp) and lose 2022 by
   9.9 / 9.9 / 7.0 pp; on Calmar they beat one winner (B75K25 +0.025) and lose to one
   (B50K50 −0.022). Reported, not adopted, whatever they print.
5. **On the 2019 lane T is a complement, not a trade**: `BIL50+BTAL50` beats `BTAL`
   by +0.35 Calmar with 6.6 pp less drawdown, and T beats `BTAL75+DBMF25` by +0.049
   with 0.9 pp more. Expect 10.3(c)'s "not worse" to hold and clause (iv) to be the
   only close call. Falsified if T is worse under 10.2.
6. **The brackets keep every sign.** Gross and flat-20 reproduce every ordering in
   the tables above; no comparison in steps 2–4 flips. Falsified by a sign flip.
7. **The withholding read does not bind.** T's clause-(i) margins are far from the
   ±0.02 band on the 2012 lane (+0.12) and the K25 winner (+0.05), so §10.5's
   tie-breaker root is not built. Falsified if any T comparison lands inside the
   band, in which case the `bil0` root is built and that lane reread.
8. **Exposure is identical across sleeves** (VT sizes TQQQ without seeing the
   sleeve): average TQQQ weight 0.461–0.462 at σ0.20 / w0.8 on the 2012 lane for all
   five sleeves, 0.377–0.379 on the 2021 lane for all twelve. Falsified by a
   difference above 0.005 — which would mean a sleeve changed the gate or the sizing,
   i.e. a bug.

## 12. Honest limitations

- **One candidate, three lanes, and the lanes disagree by construction.** The 2012 lane
  contains 2022 once in fourteen years; the 2021 lane once in six. The bar prices the
  disagreement through the window floor rather than resolving it, and 10.4 is the
  honest output if the floor decides. Whether 2022-shaped grinds recur at one-in-six
  or one-in-fourteen is the question no lane answers.
- **BTAL's drift is not a constant of nature.** −3.4 %/yr over 2012–2026 includes a
  −20 % 2025; the pre-2012 behaviour of a long-low-beta / short-high-beta sleeve is
  exactly what the synthetic verdict left untested, and a bear where low beta is
  bid (2000–02) would reprice every number here in BTAL's favour.
- **BIL's withholding is treated as a bias, not fixed.** §10.5 builds the per-symbol
  root only if a comparison lands inside the band. If BIL's true rate matters to a
  reader for other reasons, that root is a one-flag build.
- **Three-way sleeves are categorical.** No `neighbour_min`; the fraction surface's
  smoothness is read by eye across five points per σ on the 2012 lane and three per
  winner on the 2021 lane. A T that wins by more than its neighbours' spread is a
  finding; one that wins by less is a point.
- **The 2021 lane's holdout is noise**, as the runner says and as the composition
  verification measured (0.01 of `robust_score` per four trading days). Every 2021
  comparison is read with that width; the 2012 lane carries the weight.

## 13. Deliberately not in scope

Cash inside the *rotation* fallback (`fb best(BIL+IEF)` — the catalog is closed).
`SHY` / `IEF` / `TLT` as sleeve members (duration is a different bet from cash; the
first question is the cash fraction, and a duration sleeve is its own spec with 2022
as its own kill condition). A time-varying `cash_yield` in `Config` (BIL is the
time-varying cash; the constant stays for residue). Re-fitting σ or w_max for the
transformed sleeves (10.3 adopts T at the winners' coordinates or not at all; a
sleeve-and-σ joint fit is a grid search on the winners' lane). `KMLM` / `DBMF`
fraction changes (the blend verdict's question, closed). Any change to the gate or
the VT sizing.

## 14. Acceptance checklist

- [x] `dividends/BIL.parquet`; BIL in the golden battery with the 2026-08-24 root (B1); B2–B5 green from a fresh clone; suite count 876 → 923
- [x] Docs per §7 (BIL cost line, SAFE_SWAP §9 pointer, CLAUDE.md line)
- [x] **Pre-registration commit** `25a40a7`: seven specs (§4.1–§4.3, their two `_c20` twins, §4.5's two bundles), §3, §10, §11 — before any run
- [x] Artefacts: seven sweep directories, two bundle JSONs, committed together; §4 anchors confirmed in the verdict (two robust anchors unmeetable — erratum 5)
- [x] §10.5's band fired: `--rate-override`, `tests/data/2026-08-24-net15-bil0`, `results/sweep_cash_2021_bil0` (erratum 8)
- [x] `notes/cash-verdict.md` per §9–§10; winners file created per 10.6 (erratum 7); `BTAL` flagged at σ0.20 per 10.6
- [x] No engine file touched; `SCHEMA_VERSION` 4

## 15. Errata (found during implementation)

1. **§6 B1 "Polygon's reference data reaches BIL's 2015+ monthly distributions;
   the pre-2015 boundary is printed"** — it reaches 2007-07-02, BIL's *first*
   distribution, one month after its 2007-05-30 inception. There is no boundary
   to print and nothing for `extend_dividends.py` to carry, unlike QQQ's. 126
   records; the pin is in `test_polygon_covers_bil_from_its_first_distribution`.
   (The parquet and the fetcher's BIL entry landed on `main` at `82cadfe` /
   `bf743e6`, before this branch.)
2. **§2.1's `max DD` column is measured on the gross root**, not the net15 one
   its "(net15 unless stated)" header implies: BTAL prints −52.70 % / −47.83 %
   on `tests/data/2026-08-24` against −53.63 % / −48.03 % on the net twin, and
   KMLM's −27.47 % and DBMF's −20.39 % are likewise gross. BIL's cells are
   identical on both roots to four decimals. B5 pins the column against the
   gross root and both CAGR columns against their stated ones.
3. **§6 B1 "symbol discovery switched to a glob"** (SAFE_SWAP §9 precondition 2)
   is implemented as a per-root `ROOT_SYMBOLS` map instead. A glob over the
   root's `*.csv` would sweep in the index series (`VIX`, `VIX3M`, `SPX`,
   `XNDX`) that have no `price/` twin by design, so T1–T3 would fail on files
   they are not about. The 2026-08-20 root keeps its six, the 2026-08-24 root
   and live `data/` run seven; T6's cross-snapshot calendar pin stays on the six.
4. **§8's commit order puts B4 before the specs it reads.** B4 has two legs —
   the `run_bundle` anchors, which need no spec file, and the `--dry-run` counts,
   which need all five sweep specs. The anchors ship in commit (1) with the rest
   of the battery; the counts ship in the pre-registration commit (2) beside the
   specs, so every commit is green and the freeze is still one commit.
5. **§4.2's robust anchor is unmeetable as written.** It asks the three winners
   at σ0.20 to reproduce `sweep_comp_2021`'s `robust_score` (0.8470 / 0.8574 /
   0.8849), but that lane held `sigma_target` fixed and so had
   `neighbour_min: null`, while §4.2 grids σ and gives every point a neighbour.
   For `BTAL75+DBMF25` and `BTAL50+KMLM50` the neighbour binds and they print
   0.8389 and 0.8429. The **full-window** Calmars reproduce exactly on all three,
   and that is the comparability statement the anchor should have made; every
   comparison inside a lane is unaffected, since all twelve sleeves are scored
   the same way at the same coordinate. Recorded as residual 3 of the verdict.
6. **§9 step 4 reads a calendar year no artefact supplies.** It asks for the
   2019 lane's 2020 calendar year, but §4.5 provisions panels for the 2012 and
   2021 lanes only and `runs.csv` carries `best_year`/`worst_year` rather than a
   full calendar. The COVID *episode* is covered by `cash_points_2012.json`'s
   `drawdowns`; a third panel would have been an addition to a pre-registered set
   after the runs and was not made. The decision does not turn on it — §10.3(c)
   fails on `robust_score` and on the window floor.
7. **§7's "`docs/WINNING_STRATEGIES.md` (or its successor)"** — the file has
   never existed (SAFE_SWITCH erratum 8, COMPOSITION erratum 7) and
   `specs/winners.json` is a strict bundle spec that cannot hold prose. §10.6(b)
   therefore *creates* it, carrying the three winners with their committed
   numbers, the §10.4 sentence and the σ0.20 flag.
8. **§10.5's tie-breaker fired** (§11 prediction 7 said it would not), so
   `make_net_tr.py` gained `--rate-override SYM=RATE` and
   `tests/data/2026-08-24-net15-bil0` was built and committed. The rate reaches
   only `build`'s per-symbol loop; a snapshot without overrides is byte-identical
   to before, which N5 checks. The reread changed no clause.
