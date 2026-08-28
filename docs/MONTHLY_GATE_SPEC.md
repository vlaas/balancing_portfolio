# Specification: the monthly-read gate — is the SMA-200's daily series load-bearing?

Repo: `vlaas/balancing_portfolio` · baseline commit: `49f007f` (return-stacked merged;
1023 tests green on a fresh clone) · status: **proposed** · inputs: `HANDOFF_EPISODE.md`
§7.2 (the frozen band: ±0.02 `robust_score`, 1 pp floor), `notes/comp-verdict.md` §4
residual 1 · predecessors: `docs/COMPOSITION_SPEC.md` (which built the `sma_months` gate
kind and ran it once), `notes/rs-verdict.md` (the previous cycle).

## 1. Goal

The winners' gate is `QQQ < SMA-200`: a daily 200-bar average, read at each month-end.
Executing it live requires a correct daily TR series and a correct daily SMA — exactly
the two artefacts the TradingView → programmatic migration must keep bit-true, and the
only daily inputs the machine has (the EWMA sizing needs daily closes too, but those
come with any source; a 200-day *average parity* is the fragile part). The alternative
the composition sweep already built and ran once is `sma_months: 10`: the mean of the
last ten month-end closes — ten numbers a person can keep in a notebook. On the 2012
lane it printed `robust_score` 0.8572 against the incumbent's 0.8612, holdout test
identical, and the composition verdict filed it as residual 1: *"a substitute, not an
improvement."* The handoff's §7.2 froze the question and the bar: run it at the
winners' coordinates on the 2021 and 2019 lanes; if it reproduces `G_sma` within 0.02
of `robust_score` and 1 pp of window floor, **the live rule becomes a single month-end
read and the winners' documentation says so**; if not, the daily read is load-bearing
and that is worth knowing too.

The pilot (§2.4) makes the expected answer unusually sharp, because the question turns
out to be almost entirely a calendar question. The machine consults its gate only on
month-ends and on a window's deployment day (§2.1) — and on the 2021 lane the two
signals **agree on all 68 month-ends and all seven window starts**, so the three
monthly-read twins are *numerically identical* to the incumbents, to eight decimals,
turnover included. On the 2019 lane they disagree exactly once, at the lane's first
month-end (2019-05-31, a hairline crossing), and the twin gives back 0.18 pp of CAGR
for one gated June; its holdout test is bit-identical. Across the full 2012-01-03 →
2026-07-31 real calendar and the 2000-01-03 → 2011-12-30 synthetic bear, the monthly
signal closes a strict superset of the daily one's month-ends — 27 shared plus 2, and
60 shared plus 2 — every extra close a hairline. The spec's job is to turn that
measurement into a pre-registered verdict with the runner's own statistics, and to
ship the one tool this program lacks for it: a committed calendar report comparing the
two signals, so the verdict's mechanism read does not rest on ad-hoc arithmetic.

## 2. What is already true at `49f007f` (measured on this clone)

### 2.1 The two signals, and when the machine actually looks at them

`sma(200)` is the daily rolling mean; `sma_monthly(10)` is the mean of the last ten
month-end closes, carried forward between month-ends, where a month-end is a row whose
month differs from the next row's — the same rule as `is_rebalance_day`, so the value
on a rebalance day includes that day's close and the file's final partial-month row is
never a month-end (`indicators.py`). The gate closes while the symbol's close is below
the value; closed, it blocks buys of the gated assets (no `w_off` at the winners'
coordinate).

`simulate.py` acts only when `i == 0` (the deployment day: initial capital arrives and
a full rebalance runs) or on `is_rebalance_day` (the monthly contribution arrives and,
at monthly cadence, the full rebalance runs — the two calendars coincide). Every other
day is skipped. **So for the monthly-rebalanced machine, the gate's entire consultation
calendar is the window's start date plus its month-ends**, and two signals that agree
on that calendar produce bit-identical portfolios. Each sweep window is an independent
simulation from fresh capital, so the claim holds window by window.

### 2.2 The calendars — where the two signals disagree

Month-end closed flags on QQQ (net15 closes; both indicators computed on the full
series before the start filter, as the loader does):

| window | month-ends | SMA200 closed (state changes) | SMA10M closed (changes) | both | SMA200-only | SMA10M-only | 2022 |
|---|---|---|---|---|---|---|---|
| real, 2012-01-03 → (last 2026-07-31) | 175 | 27 (20) | 29 (24) | 27 | **0** | **2** | 12/12 both |
| real, 2019-05-08 → | 87 | 16 (8) | 17 (9) | 16 | 0 | 1 | 12/12 both |
| real, 2020-12-18 → | 68 | 15 (6) | 15 (6) | 15 | **0** | **0** | 12/12 both |
| synthetic, 2000-01-03 → 2011-12-30 | 144 | 60 (27) | 62 (27) | 60 | **0** | **2** | — |

The monthly signal's closed set is a **strict superset** of the daily one's, on both
roots, over 26 years and two bears. The four extra closes, each a hairline crossing
(close above SMA-200 and below SMA-10M by fractions of a percent):

| month-end | close | SMA200 (close vs) | SMA10M (close vs) |
|---|---|---|---|
| 2016-06-30 | 101.27 | 100.91 (+0.36 %) | 101.30 (−0.03 %) |
| 2019-05-31 | 167.30 | 167.23 (+0.04 %) | 167.97 (−0.40 %) |
| 2005-03-31 (syn) | 31.920 | 31.903 (+0.05 %) | 32.047 (−0.40 %) |
| 2011-11-30 (syn) | 50.555 | 50.359 (+0.39 %) | 50.961 (−0.80 %) |

**Start dates** (the deployment-day consultations §2.1 adds): every window start on the
2021 lane (2020-12-18, six sensitivity starts, holdout 2025-01-02) and the 2019 lane
(2019-05-08, nine sensitivity starts, holdout 2024-01-02) carries agreeing flags. The
synthetic lane has **one start-date disagreement: 2005-07-05** (the snapped 2005-07-03
sensitivity start), where the daily SMA has crossed intramonth (closed) and the carried
month-end value has not (open) — a disagreement no month-end report can show, found by
direct measurement and pinned by M5.

Consequences, before anything is run: on the 2021 lane the twins must be identical
everywhere; on the 2019 lane only the full window and the first sensitivity window
(2019-05-08 start) can differ, and only through June 2019; on the synthetic lane the
differing windows are exactly the six whose span contains 2005-03-31 (starts
2002-07-03 … 2005-01-03), the one deployed 2005-07-05, the fit (contains 2005-03-31),
the test (2008-01-02 →, contains 2011-11-30) and the full window.

### 2.3 The committed rows (nothing here is re-run)

`results/sweep_comp_2012` — the one place `G_sma10m` has already run, at the 2012
winner's coordinate (`BTAL` t30 w0-60):

| arm | robust | full | window floor | holdout test |
|---|---|---|---|---|
| `gate QQQ<SMA200` | 0.86123626 | 0.86123626 | −27.3341 | 1.11185727 |
| `gate QQQ<SMA10M` | 0.85720170 | 0.85720170 | −27.3380 | **1.11185727** |
| no gate | 0.71623794 | 0.71623794 | −34.5709 | 1.32823587 |

Δ robust −0.0040, Δ floor 0.0039 pp, holdout test **identical to eight decimals** —
the test window (2023-01-03 →) contains neither real disagreement date. The two dates
it does not contain are the mechanism in miniature.

`results/sweep_comp_2021`, winners' coordinate (σ0.20 w0.8 λ0.80 t20 w0-80):
gated `B75K25` / `B75D25` / `B50K50` robust 0.84701986 / 0.85739876 / 0.88489974,
floors −19.0626 / −19.0682 / −20.8772, tests 0.84701986 / 0.88253297 / 1.16742198;
no-gate twins robust 0.83354496 / 0.81272474 / 0.81407574, floors −19.5303 / −20.1448 /
−22.5732. `results/sweep_comp_2019`, `B75D25`: gated robust 0.91868785 (= its test),
full 0.93621129, floor −20.1131; no-gate robust 0.83960162, full 0.93984909, floor
−20.1389, test 0.84406819. `results/sweep_syn_2000`, the W coordinate (`BIL` t20
w0-80, EWMA80): gated robust 0.07664352, full 0.10460356, floor −36.1178, test
0.18771366; no-gate robust −0.01811905, full 0.01033090, floor −60.7450. All
reproduced on this clone before writing.

### 2.4 The pilot in one table (full windows and the snapped holdout windows, net15)

Blend cost map + `BIL 0.5`, `cash_yield` 3 %, 10 000 + 500 / month, monthly
rebalancing; Calmar · CAGR · max DD at eight decimals where the claim needs them.

**2021 lane, 2020-12-18 → (holdout twin from 2025-01-02):** for each of the three
winners' sleeves, the `gate QQQ<SMA10M` arm is **identical to the `gate QQQ<SMA200`
arm to eight decimals on every printed field — Calmar, CAGR, max DD, holdout Calmar,
and turnover** (0.85294307 · 0.16259332 · −0.19062623 · 0.84701986 · 1.7013 for B75K25;
0.85739876 · 0.16349089 · −0.19068245 · 0.88253297 · 1.7056 for B75D25; 0.88489974 ·
0.18491311 · −0.20896504 · 1.16742198 · 1.7030 for B50K50). The no-gate arms reproduce
§2.3's committed values.

**2019 lane, 2019-05-08 → (holdout twin from 2024-01-02):**

| arm (B75D25 sleeve) | full Calmar | CAGR | max DD | test Calmar | turnover |
|---|---|---|---|---|---|
| no gate | 0.93984909 | 18.92 | −20.1312 | 0.84406819 | 1.7235 |
| `gate QQQ<SMA200` | 0.93621129 | 18.83 | −20.1131 | 0.91868785 | 1.6553 |
| `gate QQQ<SMA10M` | **0.92721074** | **18.65** | −20.1135 | **0.91868785** | 1.6571 |

The monthly twin differs from the incumbent by −0.0090 of full Calmar and −0.18 pp of
CAGR — one gated June 2019, the lane's first month, where QQQ rallied — while its max
DD sits 0.0004 pp away and its holdout test is **bit-identical** (the test window's
consultation calendar agrees everywhere). The residue below the fourth decimal is
integer-share path noise after the twins re-converge at the 2019-06-28 rebalance.

**Synthetic bear, 2000-01-03 → 2011-12-30** (`--end`, W coordinate): `gate QQQ<SMA200`
0.10460356 · 3.75 · −35.8578 (turnover 1.3554); `gate QQQ<SMA10M` **0.10525207 · 3.77 ·
−35.8574** (1.3541); SPY 0.00553231 · 0.31 · −55.35. On the one bear era available, the
monthly read is *microscopically better* — the two extra gated month-ends were down
months — and the floor moves 0.0004 pp.

### 2.5 The tool surface

`score_report.py` (COMPOSITION_SPEC §5) prints the month-end calendar of a *momentum
score* against the SMA gate — closed counts per year, the contingency, the disagreement
dates, the threshold ladder — building the score through `spec._score` so the report
cannot drift from the signal. It has no way to put `SMA10M` on the comparison side:
`--score` is required and goes through the score factories. `regime_report.py` owns the
`month_ends` / `contingency` helpers it imports. Nothing else in the repo prints a
signal calendar. §2.2's tables are ad-hoc measurements; §5 commits the read.

## 3. The question, and what can be adopted — pre-registered

**Q: is `sma_months: 10` a drop-in for `sma_days: 200` at the winners' coordinates —
same `robust_score` within 0.02, same window floor within 1 pp, on the 2021 and 2019
lanes?** The band is the handoff's, frozen before this spec was written.

What adoption means — and does not mean. On a pass, the winners' **documentation**
records the monthly read as an approved live execution of the gate: the winners file's
gate bullet gains the sentence, a small twin table (the four monthly-read rows'
`robust_score` / full / CAGR / floor / test, so a monthly executor has their own
expectation numbers), and the divergence calendar (the dates on which live behaviour
would have differed from the backtest). **The winners themselves are not redefined**:
every committed anchor stays `sma_days: 200`, no results file moves, and no follow-on
re-run of any lane is triggered. This is a documentation adoption in the exact sense
the handoff froze — "the live rule becomes a single month-end read and the winners'
documentation says so." On a fail, the ledger records that the daily read is
load-bearing, and the migration inherits the daily-SMA parity requirement explicitly.

The synthetic lane is attached as a robustness read, not a bar (§10.3): the band was
frozen on the real lanes, but adopting a live-rule equivalence that broke on the only
bear era available would be dishonest, so a severe synthetic divergence attaches a
verbatim caveat to the flag.

`m = 10` is the only value run. This is an equivalence check against the one committed
arm (Faber's convention, the arm the composition sweep built), not a fit; a grid over
`m` would be a re-fit of the gate and is out of scope (§13).

## 4. Lanes

All sweeps: objective Calmar, constraint max drawdown ≥ −0.50, 10 000 + 500 / month,
blend cost map + `BIL 0.5`, `cash_yield` 0.03. Windows copied from the lane each one
extends, so every incumbent row reproduces its committed number inside the new sweep.

### 4.1 `specs/sweep_mg_2021.json` — the winners' lane (90 runs)

`tests/data/2026-08-24-net15`; windows as `sweep_comp_2021` (start 2020-12-18, holdout
2025-01-01, sensitivity 6 m / 3 y → 9 windows; the runner's short-test warning applies
and is quoted). Template: `vol_target` at the winners' coordinate with `safe: {"grid":
[B75K25, B75D25, B50K50]}` × `gate: {"grid": [null, G_sma, G_sma10m]}` — the same
nested-grid shape as `sweep_comp_2021` — where `G_sma10m = {"symbol": "QQQ", "assets":
["TQQQ"], "sma_months": 10}`. Baseline: SPY. `--dry-run`: **9 grid + 1 baselines × 9
windows = 90 runs**. Anchors: the six committed §2.3 rows.

### 4.2 `specs/sweep_mg_2019.json` — the long lane (48 runs)

Windows as `sweep_comp_2019` (start 2019-05-08, holdout 2024-01-01, 6 m / 3 y → 12
windows). `safe` fixed at B75D25, the same gate grid. Baseline: SPY. `--dry-run`: **3
grid + 1 baselines × 12 windows = 48 runs**. Anchors: the two committed §2.3 rows.

### 4.3 `specs/sweep_mg_syn.json` — the bear era, reported (84 runs)

`tests/data/2026-08-24-syn-net15`; windows as `sweep_syn_2000` (start 2000-01-03, end
2011-12-30, holdout 2008-01-02, 6 m / 3 y → 21 windows, 18 sens). Template: the W
coordinate (`risk: TQQQ`, `safe: "BIL"`, EWMA80, σ0.20, w_max 0.8) with the same gate
grid. Baseline: SPY. `--dry-run`: **3 grid + 1 baselines × 21 windows = 84 runs**.
Anchors: the two committed §2.3 rows and SPY.

### 4.4 Calendars — the committed read (§5's tool)

```
uv run score_report.py --data tests/data/2026-08-24-net15     --sma-months 10 --start 2012-01-03                  > results/gate_calendar_2012.md
uv run score_report.py --data tests/data/2026-08-24-syn-net15 --sma-months 10 --start 2000-01-03 --end 2011-12-30 > results/gate_calendar_syn.md
```

### 4.5 Panel — `specs/mg_points_2019.json`

The §4.2 grid and baseline as a bundle (start 2019-05-08) through `episode_report.py
bundle` → `results/episode_mg_2019.md`. The 2019 lane is the only one where the twins
differ at all, and E2 (read from the lane's first bar, 2019-05-08 → 2019-12-16) is the
only episode whose window touches the divergence; the panel shows the confinement. No
2021 panel (identical arms print an identical table) and no synthetic panel (the
episode table is defined on the real lanes).

### 4.6 No cost brackets — pre-registered reason

The twins' turnover differs by ≤ 0.002/yr on every pilot row (2021: 0.0000; 2019:
+0.0018; syn: −0.0013), so any flat per-side cost moves both arms of a pair by the same
amount to within a tenth of a basis point of CAGR: cost cannot separate them, and a
bracket would re-run 222 sweeps to print equalities. The blend-vs-flat question was
settled for these coordinates by the composition and cash cycles.

### 4.7 Size

222 sweep runs + one bundle of 4 + one episode bundle; a minute or two. Pre-flight: no
indicator wider than SMA-200 / SMA-10M on QQQ, both valid at every lane start on both
roots (QQQ's history begins 1999-03-10 on both); every traded symbol alive at its
lane's start.

## 5. Tooling — the one addition; core engine untouched

`score_report.py` gains `--sma-months M`, mutually exclusive with `--score` (exactly
one required). In this mode the comparison side is the flag `close < SMA{M}M`, with the
column built by **`indicators.sma_monthly(M)` — the same factory the gate uses**, so
the report cannot drift from the signal (the reason the tool exists at all). The
report keeps its sections — closed counts and contingency per calendar year, the
window contingency (both / SMA-{days}-only / SMA-{M}M-only / neither), the disagreement
dates with close and both SMA values, and the state-change counts — and drops the
threshold ladder, which is score-specific. Month-ends only: the report is the *live*
calendar (a person executes at month-ends); deployment-day artefacts are the
backtest's and are pinned by M5, not printed here.

`prices.py`, `simulate.py`, `indicators.py`, `stats.py`, `results_json.py`,
`strategy.py`, `strategies/*`, `spec.py`, `sweep.py`, `main.py`, `episode_report.py`,
`regime_report.py`: **untouched**. `SCHEMA_VERSION` stays 4. The gate kind, the
indicator and the grammar all exist since COMPOSITION_SPEC; nothing new is simulated.

## 6. Tests — new `tests/test_monthly_gate.py`

Cite as "MONTHLY_GATE_SPEC M·" (T, N, R, C, S, B, A, D are taken).

**M1 — The calendars, through the tool's machinery.** On `2026-08-24-net15` QQQ from
2012-01-03: 175 month-ends, SMA200 closed 27 with 20 state changes, SMA10M closed 29
with 24, both 27, SMA200-only **0**, SMA10M-only exactly `{2016-06-30, 2019-05-31}`;
every 2022 month-end closed by both. On `2026-08-24-syn-net15` QQQ, 2000-01-03 →
2011-12-30: 144 month-ends, 60 (27 changes) against 62 (27), both 60, SMA10M-only
exactly `{2005-03-31, 2011-11-30}`. The superset property (SMA200-closed ⇒
SMA10M-closed) holds on both roots.

**M2 — Tool behaviour.** Exactly one of `--score` / `--sma-months` (both or neither
exits with the argparse error); the comparison column is named `SMA{M}M` and built via
`indicators.sma_monthly`; a small written-fixture root yields the right contingency
cells and disagreement rows; the sma-months report contains no threshold-ladder
section; the score mode's output on an existing fixture is byte-unchanged by the
extension.

**M3 — Anchors through the new specs.** `--dry-run` prints 90 / 48 / 84 (ships in the
pre-registration commit beside the specs); through `run_bundle` on the right roots, the
committed rows reproduce: on the 2021 full window 0.85294307 / 0.85739876 / 0.88489974
gated and 0.83354496 / 0.81272474 / 0.81407574 ungated; on the 2019 full window
0.93621129 gated and 0.93984909 ungated, and on its test window 0.91868785; on the
synthetic full window 0.10460356 gated.

**M4 — Pilot pins.** On the 2021 full and holdout bundles, each sleeve's `SMA10M` arm
equals its `SMA200` arm to 1e-8 on Calmar, CAGR, max drawdown and turnover. On the
2019 full window the `SMA10M` arm prints 0.92721074 / 0.18649453 / −0.20113499 and on
its test window 0.91868785; on the synthetic full window 0.10525207 / 0.03774067 /
−0.35857411.

**M5 — The consultation calendar.** On a written fixture, a gated strategy's
deployment-day (`i == 0`) buys are blocked when the carried `SMA{M}M` flag is closed on
a non-month-end start date — the gate is consulted at deployment, not only at
month-ends. On the synthetic root, 2005-07-05's flags computed through `sma(200)` and
`sma_monthly(10)` disagree (daily closed, monthly open), and every window start date of
§4.1 and §4.2 (including both holdout starts) carries agreeing flags.

## 7. Docs

- `tests/test_episode.py` A7 `LIVING` — **housekeeping, in the tool commit**:
  `docs/HANDOFF_EPISODE.md` and `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` join the
  allowlist. The first completes HANDOFF_EPISODE §6.2's own bolded instruction ("this
  file goes into A7's allowlist in the commit that adds it"), which commit `e5edd30`
  did not carry out; the second is named as living by the same section's prose but
  absent from the tuple. Both files are clean of the guarded literal on this clone, so
  the suite stays green and A7's parametrized count rises by two. In the same commit,
  §6.2's sentence is corrected in place (a living doc stays accurate) to record the
  late fulfilment and the commit that made it. No other test changes; the guard's
  semantics are untouched — the two most-edited living documents simply come under it.
- `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`: on a pass, the "SMA-200 gate stands"
  bullet gains the monthly-read sentence, the four-row twin table, and the divergence
  calendar (§10.2); on a fail, the ledger gains the load-bearing entry (§10.4). Either
  way one entry in "what has been asked and answered".
- `docs/HANDOFF_EPISODE.md` §7.2: a pointer to this spec and its verdict (living doc).
- Nothing else beyond the A7 housekeeping above. `CLAUDE.md`, `COST_MODEL_SPEC.md`,
  the migration notes: untouched — the migration consequence (a pass removes daily-SMA
  parity from the live-execution critical path; T1's parity fixture remains a
  backtest-reproduction requirement) is stated in the verdict and the winners file,
  where the migration spec will read it.

## 8. Run protocol

```
uv run pytest                                                                          # M1–M5 green
uv run sweep.py specs/sweep_mg_2021.json --data tests/data/2026-08-24-net15     --out results/sweep_mg_2021
uv run sweep.py specs/sweep_mg_2019.json --data tests/data/2026-08-24-net15     --out results/sweep_mg_2019
uv run sweep.py specs/sweep_mg_syn.json  --data tests/data/2026-08-24-syn-net15 --out results/sweep_mg_syn
uv run score_report.py --data tests/data/2026-08-24-net15     --sma-months 10 --start 2012-01-03                  > results/gate_calendar_2012.md
uv run score_report.py --data tests/data/2026-08-24-syn-net15 --sma-months 10 --start 2000-01-03 --end 2011-12-30 > results/gate_calendar_syn.md
uv run episode_report.py bundle specs/mg_points_2019.json --data tests/data/2026-08-24-net15 > results/episode_mg_2019.md
```

Commit order (handoff §6.7): (1) the tool extension + `tests/test_monthly_gate.py` M1,
M2, M4, M5 and M3's `run_bundle` legs, plus the A7 `LIVING` housekeeping and the
handoff §6.2 correction (§7); (2) the **pre-registration commit** — the three
sweep specs, `specs/mg_points_2019.json`, M3's `--dry-run` legs, §3, §10, §11, nothing
run; (3) artefacts; (4) the verdict, `notes/mg-verdict.md`. Verification after (4):
fresh clone, suite, `git diff --stat <prereg> <verdict> -- specs/` empty, every
headline number recomputed from `summary.json` / `runs.json` / the reports; §4 anchors
confirmed before any new number is read.

## 9. Read protocol

Steps in order; every number from `summary.json`, `runs.json`, the calendar reports or
the panel.

0. **Anchors** (§2.3 rows inside the new sweeps) reproduce; the 2021 lane's holdout
   warning quoted; dry-run counts match §4.
1. **The identity, §4.1.** For each of the three sleeves, the `SMA10M` and `SMA200`
   rows compared on **every column of `runs.json` in all 9 windows** (label, slug and
   `params.gate` aside). Equal or not, per pair, per window.
2. **The 2019 lane, §4.2.** The twin's `robust_score`, full, CAGR, max DD, test,
   sensitivity median and min, window floor (min sensitivity `max_drawdown` from
   `runs.json`); the deltas against the incumbent; which windows are bit-identical.
3. **The band.** For each of the four winner rows (2021 × 3, 2019 × 1): |Δ
   `robust_score`| and |Δ window floor|, against 0.02 and 1 pp; the committed 2012 row
   (−0.0040 / 0.0039 pp) quoted alongside.
4. **The bear era, §4.3.** The same columns for the W pair; the window partition
   (which of the 18 sensitivity windows differ, against §2.2's predicted seven); Δ
   test, Δ robust, Δ floor. Reported under §10.3.
5. **The calendars, §4.4.** Both reports read against §2.2; the disagreement dates,
   the superset property, the state-change counts.
6. **The panel, §4.5.** The E2 cell's divergence and the E3–E7 cells' confinement.
7. **Exposure sanity.** `exposure.TQQQ.avg` per twin pair — equal on the 2021 lane,
   and within 0.002 on the 2019 lane.
8. **The decision, §10.**

## 10. Decision rule — frozen at the pre-registration commit

10.1 **The band (the handoff's, verbatim).** The monthly read is a drop-in iff, for
each of the four winner rows — B75K25, B75D25, B50K50 on `sweep_mg_2021` and B75D25 on
`sweep_mg_2019` — the `SMA10M` arm's `robust_score` is within **0.02** of the `SMA200`
arm's and its window floor within **1 pp**. All four must pass. (The lanes are
categorical-only, so `robust_score` is the three-term minimum on both arms; the
committed 2012 row is quoted beside the verdict but was decided by the composition
cycle and is not re-scored.)

10.2 **Adoption — documentation only.** On a pass, the winners file's gate bullet
gains: *"The gate may be executed as a month-end read: QQQ's month-end close against
the mean of its last ten month-end closes (`sma_months: 10`). At the winners'
coordinates this reproduces the daily rule within [the verdict's measured deltas];
the two rules disagreed on [the dates] in 2012-01 → [the calendar's last month-end],
every disagreement a sub-percent crossing where the monthly rule closed and the daily
did not"* — plus the four-row twin table (`robust_score`, full Calmar, CAGR, window
floor, holdout test) on the net15 basis, and a pointer here. **No winner is redefined;
no committed anchor moves; no lane is re-run with the monthly gate.** The live reads
must use the same net-TR-adjusted basis as the dataset; ten month-end values of the
maintained net-TR series suffice, which is the point.

10.3 **The bear era can only add a caveat.** The band was frozen on the real lanes and
the synthetic lane does not score it. But if the synthetic twin is infeasible or its
window floor is more than **5 pp** deeper than the daily arm's, the 10.2 flag must
carry that sentence verbatim, and the adoption stands only as "equivalent on 2012–2026
and cautioned on the synthetic bear". (The pilot's full-window read — the monthly arm
0.0006 *better*, floor 0.0004 pp apart — makes this a formality, pre-registered
anyway.)

10.4 **The fail path.** If any winner row misses the band, nothing is adopted; the
ledger records *"the daily read is load-bearing at [the failing row], by [the
margin]"*, and the migration keeps daily-SMA parity on its live-execution critical
path. Partial passes are fails: a rule a person executes must be one rule.

10.5 **The mechanism is recorded either way.** The 2021 identity (or its failure) pins
the consultation-calendar claim of §2.1: the machine looks at its gate only on window
starts and month-ends, so signal equivalence on that calendar is portfolio identity.
If any 2021 window shows any difference, §2.1's model of the engine is wrong somewhere,
and finding where matters more than this spec's verdict.

## 11. Pilot measurements — what to expect, and what would falsify it

Every §2 number is from `main.py`, committed artefacts, or direct indicator arithmetic
on the committed roots; full windows and the snapped holdout windows only — no
sensitivity windows, no floors, no tool output yet. The calendar tables are ad-hoc
measurements that M1/M5 pin through committed code. Predictions, each a falsifiable
line for the verdict:

1. **The 2021 lane prints identity, nine windows deep.** For each sleeve, the `SMA10M`
   row equals the `SMA200` row on every numeric column of `runs.json` in every one of
   the 9 windows — each window a fresh simulation whose consultation calendar carries
   agreeing flags throughout. Falsified by any inequality in any cell of any window.
2. **The 2019 lane's Δ `robust_score` is 0.00000000.** Both arms bind on the
   bit-identical holdout test 0.91868785: the incumbent's sensitivity median belongs
   to the 2021-11-08 window (0.91995598, committed `runs.json`), which is bit-identical
   for the twin, and the one differing window (2019-05-08) ranks sixth at 1.07833624 —
   its Calmar would have to fall by more than 0.158 to touch the median, against an
   expected one-gated-June effect near 0.02. Sensitivity windows 2–9 are
   bit-identical; the 2019-05-08 window differs by at most 0.05 of Calmar; and the
   window floor — set by that same window, −20.1131, through E4, which both twins
   traverse after their 2019-06-28 re-convergence — differs by at most 0.01 pp (the
   full window measured the same episode's gap at 0.0004 pp). Falsified by a nonzero
   Δ robust, a difference in any window after the first, or a floor gap above 0.01 pp.
3. **The synthetic partition is exactly seven of eighteen.** The differing sensitivity
   windows are the six whose span contains 2005-03-31 (starts 2002-07-03 …
   2005-01-03) plus the one deployed 2005-07-05; the other eleven are bit-identical;
   fit, test and full all differ (2005-03-31 sits in the fit, 2011-11-30 in the test).
   |Δ test| ≤ 0.03, |Δ `robust_score`| ≤ 0.02, |Δ window floor| ≤ 0.5 pp. Falsified by
   an eighth differing window, a bit-identical fit or test, or any bound breached.
4. **The band passes with two orders of magnitude to spare.** Across the four winner
   rows, max |Δ `robust_score`| = 0.00000000 and max |Δ window floor| ≤ 0.01 pp —
   against a band of 0.02 and 1 pp. Falsified if any row consumes even a tenth of
   either band arm.
5. **The panel confines the divergence to E2.** The 2019 twins' E2 cells differ — the
   `SMA10M` arm's episode return lower by 0.5 to 3.0 pp (the gated June 2019) — and
   every E3–E7 cell prints identically at the report's one-decimal precision.
   Falsified by a visible difference in any later episode, or an E2 gap outside the
   range.
6. **Turnover cannot tell the twins apart.** |Δ turnover| ≤ 0.005/yr on every window
   of both real lanes. Falsified by any window above it.

Predictions 1, 2 and 3 are jointly a test of §2.1's engine model, sharper than any
equivalence band: they claim bit-level identity wherever the calendars agree and
divergence exactly where they do not. The pre-registered outcome is a pass of 10.1
with 10.2's documentation adoption, no synthetic caveat, and residual 1 of the
composition verdict closed.

## 12. Honest limitations

- **The equivalence is empirical, not structural.** The two signals are genuinely
  different functions; 26 years of real and synthetic data put every one of their four
  month-end disagreements at sub-percent crossings, and nothing forces the future to
  do the same. A market that hovers at its SMA for months would split them — the
  monthly rule would flip on hairlines the daily rule steps over, and vice versa. The
  adoption is of a documented equivalent *on this data*, with the divergence calendar
  written next to it; it is re-checkable in one tool run whenever the dataset rolls.
- **The superset property is an observation, not a theorem.** SMA-10M sits above
  SMA-200 at every crossing in this sample because of how this market's recoveries
  shaped the two averages; nothing guarantees the daily rule can never close alone.
- **Live-versus-backtest divergence is real on one date.** Inside the winners' lanes
  the rules disagree once (2019-05-31; 2016-06-30 predates both lanes). A monthly
  executor's 2019 would have differed from the committed backtest by one gated month.
  The twin table exists so that expectation is stated, not discovered.
- **The month-end report cannot show deployment-day artefacts.** 2005-07-05 was found
  by direct measurement and lives in M5, not in the calendar report — the report is
  the live rule's calendar, and live execution has no deployment days. Anyone reusing
  the report to reason about *backtest* identity must remember the start dates.
- **One era, one bear, one `m`.** The synthetic lane is one generated history; `m = 10`
  is one convention, deliberately untested against its neighbours (§13). If a future
  spec fits `m`, it starts from a different question and must carry its own
  anti-overfitting design.
- **Basis discipline moves to the executor.** The backtest gates on net15 TR closes;
  the live read must use the same basis. Ten month-end values of the maintained net-TR
  series make that easy, but a reader gating on a broker's raw price chart is running
  a third rule this spec never tested.

## 13. Deliberately not in scope

Redefining any winner with `sma_months` (documentation adoption only; every anchor
stays daily-gated). A grid over `m` (8–12) — a fit, not an equivalence check, and a
reopening of the gate line the composition verdict closed. `w_off` variants of the
monthly gate. Score gates, OR-combinations, regime gates (closed by COMPOSITION_SPEC
and REGIME_SPEC). Re-running the 2012 lane (committed). Cost brackets (§4.6's measured
reason). Any change to the migration specs — they read this spec's verdict, not the
other way around.

## 14. Acceptance checklist

- [ ] Tool extension per §5; score mode byte-unchanged; `tests/test_monthly_gate.py` M1–M5 green from a fresh clone; A7's `LIVING` gains the two docs and HANDOFF_EPISODE §6.2 is corrected in the same commit (§7); suite count 1023 → N stated in the verdict (N includes A7's +2)
- [ ] **Pre-registration commit**: `specs/sweep_mg_2021.json`, `sweep_mg_2019.json`, `sweep_mg_syn.json`, `mg_points_2019.json`, M3's dry-run legs, §3, §10, §11 — before any run
- [ ] Artefacts: three sweep directories, two calendar reports, one episode report, committed together; §2.3 anchors confirmed in the verdict
- [ ] `notes/mg-verdict.md` per §9–§10; the winners-file edit per 10.2 or 10.4; comp residual 1 closed with a pointer
- [ ] Core engine files untouched; `SCHEMA_VERSION` 4

## 15. Errata (found during implementation)

None yet.
