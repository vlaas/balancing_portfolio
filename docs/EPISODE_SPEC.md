# Specification: episode attribution — which episodes each sleeve component earns, and which it pays for

Repo: `vlaas/balancing_portfolio` · baseline commit: `68cac21` (cash sleeve merged and
the winners file renamed; 923 tests green on a fresh clone) · status: **implemented**
(branch `episode-attribution`, per-phase commits; 979 tests green) — all three §10.2
conditions hold, the ledger's `Open:` line is closed and both flags are written;
verdict `notes/episode-verdict.md` ·
inputs: `notes/cash-verdict.md` residual 2 ("the disagreement between the lanes is a
disagreement about how often 2022 happens, and no lane answers it"), the
post-verification read of that verdict (the 2012 lane's sensitivity windows split by
2022 do *not* split the sleeves the way residual 2 assumes), `docs/HANDOFF_COMPOSITION.md`
§7 (leave-one-episode-out as the standing falsifier for the BTAL-heavy variant) ·
predecessors: `notes/safe-blend-verdict.md`, `notes/syn-verdict.md` residual 5.

## 1. Goal

Every sleeve verdict so far has been read on lane aggregates — `robust_score`, a
window floor, a calendar year — and the story that grew up around them is that the
BTAL-heavy sleeve exists for 2022. The committed artefacts say something else. The
pure-BTAL machine's deepest drawdown at the winners' coordinate is not COVID and not
2022: it is **2020-09-02 → 2021-03-08, −26.0 %**, the anti-beta unwind in the
reflation rally, and 2022 is not in its top five at all. Two of the three winners'
own max drawdowns, −19.1 %, are the same episode, clipped to their lane; the third's
second-deepest is. And when the 2012
lane's twenty five-year sensitivity windows are split by whether they contain that
episode's trough, the half-BTAL sleeve beats pure BTAL in **10 of 10** windows that do
and **2 of 10** that don't — a perfect partition that 2022 does not produce (7 of 7
and 5 of 13).

This spec turns that into a pre-registered, pinned, reproducible object:

1. **A frozen episode table** — seven windows taken from the committed drawdown
   blocks, not from a narrative — and a tool that slices any strategy's daily
   time-weighted index by them.
2. **Component attribution**: for each sleeve component (BTAL, KMLM, DBMF) at 25 %,
   50 % and 100 %, its *marginal* episode return and drawdown against the BIL sleeve,
   on both lanes. The question "what does BTAL buy, and when does it pay for it"
   answered per episode, in points.
3. **The leave-one-episode-out partition** of every sensitivity window a pair has,
   by each episode's trough, for the pairs the program has already compared — so
   "which episode is the pair's disagreement about" becomes a measured fact.
4. **The winners file rewritten** on that basis, and a rule for every future sleeve
   candidate: it is pre-registered against the episode table, naming the episodes it
   must win and the one it must not lose.

No parameter moves and no sleeve moves. This is an attribution spec: its outputs are
tables, flags, and a candidate rule. Its value is that the next sleeve spec — whatever
it proposes — cannot be written against "2022" when the data says the pivot is
2020-09.

The spec also closes a housekeeping gap the last verdict opened: `docs/WINNING_STRATEGIES.md`
was created by CASH_SLEEVE §10.6(b) and then renamed to
`docs/WINNING_STRATEGIES_CASH_SLEEVE.md`, leaving twelve references in `docs/` pointing
at a path that no longer exists — two in the living handoff, ten in frozen specs
(§7.2 treats the two kinds differently).

## 2. What is already true at `68cac21` (measured on this clone)

### 2.1 The episodes, as the machine experienced them

Top-five drawdowns (peak → trough → recovery, depth) of `VT TQQQ/<sleeve> σ0.20 w_max
0.8 λ0.80 gate SMA-200` on net15, from `results/cash_points_2012.json` and
`results/cash_points_2021.json`:

| sleeve · lane | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| BTAL · 2012 | 2014-11 → 2015-08 → 2017-02, −21.8 | 2018-08 → 2019-06 → 2019-12, −23.5 | 2020-02 → 2020-03 → 2020-07, −16.6 | **2020-09 → 2021-03 → 2021-09, −26.0** | 2025-10 → 2026-03 → open, −17.6 |
| BIL50+BTAL50 · 2012 | 2014-11 → 2016-06 → 2017-02, −23.9 | 2018-08 → 2018-10 → 2019-12, −24.4 | 2020-02 → 2020-03 → 2020-07, −19.4 | 2021-01 → 2021-05 → 2021-07, −18.2 | 2021-11 → 2023-03 → 2023-06, −19.6 |
| BIL · 2012 | 2015-03 → 2016-06 → 2017-02, −27.1 | 2018-08 → 2018-12 → 2019-12, −25.9 | 2020-02 → 2020-03 → 2020-08, −22.2 | 2021-11 → 2022-11 → 2023-07, −25.1 | 2024-12 → 2025-04 → 2025-07, −21.4 |
| B75K25 · 2021 | **2021-01 → 2021-03 → 2021-07, −19.1** | 2021-11 → 2022-01 → 2023-05, −13.5 | 2024-03 → 2024-04 → 2024-06, −13.8 | 2024-07 → 2025-04 → 2025-10, −17.7 | 2025-10 → 2026-03 → 2026-06, −16.2 |
| BTAL · 2021 | **2021-01 → 2021-03 → 2021-08, −22.0** | 2021-12 → 2022-08 → 2023-05, −16.0 | 2024-03 → 2024-04 → 2024-06, −13.7 | 2024-07 → 2024-07 → 2025-10, −16.3 | 2025-10 → 2026-03 → open, −17.6 |
| BIL · 2021 | 2021-11 → 2023-03 → 2023-07, −24.5 | 2024-03 → 2024-04 → 2024-06, −15.1 | 2024-07 → 2024-09 → 2024-12, −17.9 | 2024-12 → 2025-04 → 2025-07, −21.3 | 2025-10 → 2026-03 → 2026-05, −16.8 |

Two things are visible before any tool runs. Every BTAL-containing sleeve on the 2021
lane has 2021-01 → 2021-03 as its deepest or second-deepest episode and no BIL-heavy
sleeve has it at all; and the 2022 grind is the *shallowest* of the winners' five
episodes (−13.5 %) while it is the BIL sleeve's deepest (−24.5 %).

### 2.2 The partition (from `results/sweep_cash_2012/runs.json`, five-year windows)

`BIL50+BTAL50` against `BTAL` at σ0.20 / w0.8, the twenty sensitivity windows split by
whether a window contains an episode's trough:

| split by | windows containing it | 50/50 wins Calmar · shallower | windows without | 50/50 wins Calmar · shallower |
|---|---|---|---|---|
| COVID trough 2020-03-23 | 10 | 9 · 8 | 10 | 3 · 2 |
| **anti-beta trough 2021-03-08** | 10 | **10 · 10** | 10 | **2 · 0** |
| 2022 trough 2023-03-10 | 7 | 7 · 6 | 13 | 5 · 4 |

The eight windows starting 2012-01 → 2015-07 (none reaches 2020-09) all go to pure
BTAL on both Calmar (by 0.010–0.091) and drawdown (by 0.89–2.21 pp); the ten starting
2016-07 → 2021-01 all go to the half-swap (Calmar by 0.027–0.349, drawdown by 0.40–7.04
pp). 2022 is not the hinge; the anti-beta unwind is.

### 2.3 Component attribution (pilot, §11 has the tables)

A prototype of §4's tool reran the committed panel bundles in-process and sliced each
strategy's time-weighted index by the §3 windows. Pure BTAL against the BIL sleeve on
the 2012 lane earns +2.3 to +9.1 pp of shallower drawdown in the four bear episodes and
pays **−27.0 pp of return and −10.7 pp of drawdown** in the anti-beta unwind alone —
more return than the four bears earned combined, and half their drawdown benefit
given back in one episode. On the 2021 lane, in the 2022 grind, KMLM's
marginal return is **+16.5 pp against BTAL's +8.3**, while BTAL's marginal drawdown is
the larger (+8.5 vs +5.8), and `BTAL75+KMLM25` gets +11.0 pp of drawdown — more than
either component alone. The winners' 2022 is mostly KMLM's; the winners' deepest hole
is BTAL's.

### 2.4 What the engine can and cannot supply

`results/*.json` carries `drawdowns` and `yearly_returns` but **no daily curve**, and a
run restarted at an episode's peak sits in cash until its first month-end rebalance,
so episode returns cannot come from either the committed JSON or from re-windowed
runs. `stats.twr` builds the time-weighted index from `curve` in-process, and
`main.run_bundle` returns it per strategy (`StrategyResult.twr`, column `index`) —
which is what §4's tool reads. `sweep.py`'s `runs.json` carries every sensitivity
window's `start`, `end`, `calmar`, `max_drawdown` per strategy, which is what the
partition reads. Nothing in the engine changes.

## 3. The episode table — frozen

Seven windows, peak → recovery of the incumbent machine's own drawdowns at the winners'
coordinate on the 2012 lane (§2.1, pure-BTAL arm), plus the 2022 grind from the 50/50
arm (absent from pure BTAL's top five) and the open 2025-10 episode. Dates are the
committed `peak` and `recovery` fields; a lane that starts inside a window reads it
from its own first bar.

| id | name | window | trough | provenance |
|---|---|---|---|---|
| E1 | grind-2015 | 2014-11-28 → 2017-02-07 | 2015-08-25 | BTAL arm, 2012 lane |
| E2 | 2018-Q4 | 2018-08-31 → 2019-12-16 | 2019-06-03 | BTAL arm, 2012 lane |
| E3 | COVID | 2020-02-19 → 2020-07-06 | 2020-03-23 | BTAL arm, 2012 lane |
| **E4** | **anti-beta unwind** | **2020-09-02 → 2021-09-03** | **2021-03-08** | BTAL arm, 2012 lane |
| E5 | 2022 grind | 2021-11-19 → 2023-06-15 | 2023-03-10 | 50/50 arm, 2012 lane |
| E6 | tariff | 2024-07-10 → 2025-10-01 | 2025-04-08 | B75K25 arm, 2021 lane |
| E7 | 2025-10 | 2025-10-29 → 2026-08-24 (open) | 2026-03-27 | BTAL arm, 2012 lane |

E1, E2, E3, E5 are TQQQ bears (the sleeve's insurance is tested). E4, E6 and E7 are
episodes where the anti-beta factor itself fell — E4 with a TQQQ drawdown inside it,
E6 and E7 with a TQQQ recovery inside them (the sleeve's cost is tested). The table is
stored once, in `episode_report.EPISODES`, and every consumer reads it from there.

## 4. `episode_report.py` — the tool

Read-only, deterministic, ~150 lines, in the family of `regime_report.py` and
`score_report.py`. Two modes.

```
uv run episode_report.py bundle SPEC --data ROOT [--baseline BIL] [--sigma 0.20 --w-max 0.8]
uv run episode_report.py partition RUNS_JSON --pair "LABEL_A" "LABEL_B"
```

**`bundle`**: loads the spec, builds the bundle, calls `main.run_bundle` (the engine
runs unmodified; the tool never touches `simulate.py`), and for every strategy and
every §3 window prints the episode return of the time-weighted index (last / first −
1, both inside the window, the lane's first bar substituting for a peak before it) and
the max drawdown of that index inside the window (from the window's own running
peak). With `--baseline`, a second table gives every other strategy's **marginal**
episode return and marginal drawdown against the named sleeve, in points, `+` meaning
shallower. `--sigma` / `--w-max` filter a multi-coordinate bundle to one coordinate.
Deterministic markdown to stdout; the run protocol redirects it into `results/`.

**`partition`**: reads a sweep's `runs.json`, keeps `kind == "sens"` rows for the two
labels, and for each §3 episode prints: windows containing the episode's trough (n,
B-wins-Calmar count, B-shallower count, mean ΔCalmar, mean Δdrawdown), and the same
for windows without it. The 2.2 table, for any pair, from any lane.

Both modes cite the episode table by id and window so that a future refresh of the
committed `drawdowns` (which would move the dates) is a visible spec change, not a
silent drift.

## 5. Runs

All net15, the blend cost map plus `BIL 0.5`, no engine work.

### 5.1 `specs/episode_points_2021.json` — the component panel (13 + SPY)

At the winners' coordinate on the 2021 window: `BIL`; `BIL75+X25` and `BIL50+X50` for
X ∈ {BTAL, KMLM, DBMF}; pure `BTAL`, `KMLM`, `DBMF`; the three winners. The three
T-transforms are read from the existing `specs/cash_points_2021.json`. Reports:
`results/episode_2021.md` (this bundle, baseline `BIL`) and `results/episode_2021_T.md`
(`cash_points_2021`, baseline `BIL`). On the 2012 lane the existing
`specs/cash_points_2012.json` at `--sigma 0.20 --w-max 0.8` is the panel:
`results/episode_2012.md`.

### 5.2 `specs/sweep_episode_2012.json` — three-year windows for a finer partition (5 points)

Start 2012-01-03, holdout 2023-01-01, sensitivity 6 m / **3 y** (~24 windows, 27 in
all); template gate SMA-200, λ0.80, σ0.20, w_max 0.8; `safe` ∈ the five 2012-lane
sleeves. Baselines SPY. This exists only to feed `partition` with windows short
enough to isolate single episodes — E3 and E4 are seven months apart and every
five-year window that has one has the other.

### 5.3 Partitions read

From `results/sweep_cash_2012/runs.json` (5 y, committed), `results/sweep_episode_2012/runs.json`
(3 y, new) and `results/sweep_cash_2021/runs.json` (3 y, committed):

| pair | lanes | question |
|---|---|---|
| `BTAL` vs `BIL50+BTAL50` | 2012 (5 y and 3 y) | which episode is the hinge (§2.2 again, and at 3 y) |
| `BTAL` vs `BIL` | 2012 (5 y and 3 y) | the whole-sleeve version |
| each winner vs its T | 2021 (3 y) | is the winners' floor E4 or E5 |
| `BTAL` vs `BIL50+BTAL50` | 2021 (3 y) | the 2012 hinge on the winners' lane |

Written to `results/episode_partitions.md`.

### 5.4 Size

One sweep of 5 + 1 × 27 = 162 runs, one bundle of 14, three report runs (each reruns
a bundle of 11–14 in-process, seconds), four partition reads. Under two minutes.

## 6. Tests — new `tests/test_episode.py`

Cite as "EPISODE_SPEC A·" (episodes keep their E-ids; tests take A for attribution).

**A1 — The table is frozen.** `EPISODES` has exactly seven entries with the §3 ids,
windows and troughs; every trough lies inside its window; windows are in date order.

**A2 — Slicing is exact.** On a synthetic curve with known values, episode return and
in-window max drawdown equal hand values; a window starting before the curve's first
bar reads from the first bar; a window with fewer than two bars yields `None`.

**A3 — The 2012 attribution pins** (bundle mode on `specs/cash_points_2012.json`,
σ0.20 / w0.8, baseline `BIL`, net15). Pure BTAL's marginal (return pp / drawdown pp):
E1 −0.4 / +5.3, E2 +1.5 / +2.3, E3 +5.1 / +5.7, **E4 −27.0 / −10.7**, E5 +8.2 / +9.1,
E6 −11.1 / +5.1, E7 −9.3 / −0.8 — each to ±0.2 pp. `BIL50+BTAL50`'s: E4 −14.0 / −2.9,
E5 +4.4 / +5.6.

**A4 — The 2021 attribution pins** (bundle mode on `specs/episode_points_2021.json`,
baseline `BIL`). E5 marginal return: KMLM +16.5, DBMF +8.2, BTAL +8.3; E5 marginal
drawdown: BTAL +8.5, KMLM +5.8, DBMF +5.2, `BTAL75+KMLM25` **+11.0**; E4 marginal:
BTAL −11.6 / −7.4, KMLM +8.8 / +3.9, DBMF +10.0 / +2.9; E6 marginal return: BTAL
−11.2, KMLM −10.7, DBMF −7.3 — each ±0.2 pp.

**A5 — The partition pins** (partition mode on the committed
`results/sweep_cash_2012/runs.json`, `BTAL` vs `BIL50+BTAL50`): by E4's trough, 10
windows containing it → 10 Calmar wins and 10 shallower for the 50/50, 10 without →
2 and 0; by E5's trough, 7 → 7 and 6, 13 → 5 and 4; by E3's, 10 → 9 and 8, 10 → 3 and
2.

**A6 — The winners' deepest hole is E4.** From `results/cash_points_2021.json`, each
winner's deepest `drawdowns` entry has `peak` 2021-01-26 and `trough` 2021-03-08 and
its depth equals the winner's full-window max drawdown from `sweep_cash_2021` to
0.01 pp (−19.06 / −19.07 / −20.90 → the panel's −19.1 / −19.1 / −16.1: note B50K50's
deepest is E6 at −20.9, so the assertion is "E4 is the deepest or E6 is and E4 is
second" — pinned per winner as measured).

**A7 — Living documents do not name the old winners-file path.** The scope is an
explicit allowlist, not a glob: `docs/HANDOFF_COMPOSITION.md`, `docs/ARCHITECTURE.md`,
`docs/STRATEGY_DEVELOPMENT.md`, `docs/DECLARATIVE_SPEC.md`, `CLAUDE.md`, `README.md`.
For each, the literal string `WINNING_STRATEGIES.md` does not occur anywhere in the
file — the new name `WINNING_STRATEGIES_CASH_SLEEVE.md` does not contain that literal,
so no "unless followed by" clause and no section-skipping is needed. Two existence
checks ride along: `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` exists, and
`docs/WINNING_STRATEGIES.md` exists, is at most three lines, and names the new path.
No spec file is in scope, this one included: specs are frozen and annotated (§7.2),
and this spec must carry the old name in §7.2's own tables. The test's docstring
says that a new living document is added to the list when it is created, and that a
spec is never added.

## 7. Docs

### 7.1 The winners file

`docs/WINNING_STRATEGIES_CASH_SLEEVE.md` has two sections this spec touches, and they
are different kinds of thing. "Sleeve composition — what has been asked and answered"
is a **ledger**: each bullet is a question and the verdict that answered it, and the
blockquote under the fourth bullet (lines 70–73) is the cash verdict's own answer,
quoted. It stays verbatim — "No, at these coordinates" is still true and still that
verdict's finding. "Standing flags" is where facts that travel with the winners live.
So, if §10's conditions hold (they are expected to, §11):

**In the ledger** — the fourth bullet's `Open:` line (lines 75–77), which asks the
question this spec answers, is **closed**, not deleted:

> Closed by EPISODE_SPEC: the hinge is not 2022. Splitting the 2012 lane's windows by
> the 2021-03 anti-beta trough (E4) partitions BTAL against the half-swap 10/10 and
> 2/10; splitting by 2022's trough gives 7/7 and 5/13 (`notes/episode-verdict.md`).

and the quoted answer gains one trailing line, outside the quote: *"The '2022 is one
year in six' framing in that answer is superseded by the next entry."* A **fifth
bullet** is added: *Which episodes does each sleeve component earn, and which does it
pay for?* — answered in two sentences with the E1–E7 marginals for BTAL and the
KMLM-vs-BTAL 2022 split, and a pointer to `results/episode_2012.md`,
`results/episode_2021.md` and the verdict.

**Under Standing flags** — two new flags:

> **The winners' deepest hole is BTAL-made, not a TQQQ bear.** It is the 2021-01 →
> 2021-03 anti-beta unwind (E4), where the BTAL-75 sleeves cost 4.5 pp of drawdown
> against cash. BTAL earns its keep in the TQQQ bears (E1, E2, E3, E5: +2 to +9 pp
> shallower) and pays for it when high beta leads (E4, E6, E7: −9 to −27 pp of
> episode return); over 2012–2026 at σ0.20 the payments exceed the earnings, which is
> why pure BTAL is dominated there. The winners' 2022 return is mostly KMLM's (+16.5
> pp against BTAL's +8.3); BTAL's 2022 contribution is drawdown (+8.5 pp), and the
> blend's (+11.0 pp) exceeds either component's (EPISODE_SPEC, `notes/episode-verdict.md`).

> **Sleeve candidates are pre-registered against the episode table.** A candidate
> names, before it runs, the episodes of EPISODE_SPEC §3 it must win against the
> incumbent and states that it must not deepen E4 by more than 1 pp (§10.3).

The second flag is added whatever §10 finds (§10.3). Nothing else in the file moves.

### 7.2 Housekeeping — the winners file's name

`docs/WINNING_STRATEGIES.md` was created at `fa32da2` and renamed to
`docs/WINNING_STRATEGIES_CASH_SLEEVE.md` at `68cac21`. Twelve references in `docs/`
still name the old path. They divide by the repo's own rule — a spec is frozen from
its pre-registration commit and is annotated afterwards only through its errata —
not by whether a line is prose or a checklist:

**Renamed in place (2) — the living document:**

| file | line | text |
|---|---|---|
| `docs/HANDOFF_COMPOSITION.md` | 28, 138 | `docs/WINNING_STRATEGIES.md` → `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` |

**Left as written, annotated by a one-line erratum in each spec (10):**

Every spec's errata section is its last numbered section (the numbering continues
from the section before it; titles vary), and the entry goes at its end.
`REBALANCE_SPEC.md` has none — its implementation produced no deviations — so it
gains one as **`## 11. Errata`** after §10, an append with no existing line changed;
the earliest errata section in the repo (SAFE_SWAP §10) was itself added in a later
commit than its spec, so this is how the convention started. Its first entry opens
with *"This section was added after the fact, at this spec's docs commit."*

| file | line(s) | what the line is | erratum text (appended to that spec's errata section) |
|---|---|---|---|
| `docs/REBALANCE_SPEC.md` | 246, 278 | §7.5 verdict text; an unticked acceptance item | (new `## 11. Errata`, entry 1) *"This section was added after the fact, at EPISODE_SPEC's docs commit. The winners file named in §7.5 and the checklist now lives at `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` (created by CASH_SLEEVE §10.6(b), renamed at `68cac21`). Its 'Monthly rebalancing stands' flag is the sentence the checklist asked for; the box is left as it was."* |
| `docs/REGIME_SPEC.md` | 557, 665 | the frozen decision rule; a `[x]` record | *"The winners file named in §10 step 6 now lives at `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`; the checklist's parenthetical was true when ticked."* |
| `docs/COMPOSITION_SPEC.md` | 93, 493, 685 | a citation of numbers; the frozen decision rule; a checklist line | *"Line 93 cites 0.856 / 0.859 / 0.890 from the project-level winners document as it stood on the 2026-08-20 snapshot; `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` carries the 2026-08-24 values (0.8470 / 0.8574 / 0.8849) and is the file §10 step 8 and the checklist now refer to."* |
| `docs/SYNTHETIC_HISTORY_SPEC.md` | 456 | the frozen decision rule | *"'The winners file, when it exists' — it exists: `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`."* |
| `docs/CASH_SLEEVE_SPEC.md` | 231 | the docs section (its erratum 7 already records the creation) | *"The file §10.6(b) created was renamed to `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` at `68cac21`."* |
| `docs/SAFE_SWITCH_SPEC.md` | 317 | the frozen decision rule | *"The winners file named in §6.8 now lives at `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`."* |

Why not rename the ten in place: four of them are pre-registered decision rules and
two are checklist records, and a `git diff` of a closed spec against its
pre-registration commit should show nothing that was not an erratum; one
(COMPOSITION 93) cites numbers the new file does not contain, so renaming it would
point a citation at a document that contradicts it. The stub makes every old link
resolve, which is the only thing an in-place rename would have added.

**Not edited at all:** the `notes/*-verdict.md` files (frozen records —
`cash-verdict.md:282` correctly says the file was created under its old name); the
existing errata entries at `COMPOSITION_SPEC.md:720`, `CASH_SLEEVE_SPEC.md:513` and
`SAFE_SWITCH_SPEC.md:384` ("has never existed" was true when written); and
`specs/winners.json`, a bundle, not prose.

**The stub:** `docs/WINNING_STRATEGIES.md` becomes one line — *"Moved to
`WINNING_STRATEGIES_CASH_SLEEVE.md` at `68cac21`."* — so any link in an external note
still resolves.

**The guard (A7, §6):** an allowlist of living documents, checked for the literal
`WINNING_STRATEGIES.md`. Closed specs — this one included — are outside its scope by
design: their stale names are annotated, not fixed, and a spec that had to be
excluded by section would be a spec the guard should never have read. The next
rename is caught where it would matter.

### 7.3 Elsewhere

- `docs/HANDOFF_COMPOSITION.md` §7: the leave-one-episode-out entry for the BTAL-heavy
  variant gains the episode table's id for the deletion (*"with **E4** deleted, not
  2022"*) and a pointer here. The pointer says *"the old winners-file path is a stub
  (EPISODE_SPEC §7.2)"* without spelling that path — the HANDOFF is in A7's scope.
- `docs/ARCHITECTURE.md`: `episode_report.py` beside the other two report tools.
- `CLAUDE.md` §6, one line: *a sleeve candidate names, before it is run, the episodes of
  `episode_report.EPISODES` it must win and the one it must not deepen.*

## 8. Run protocol

```
uv run pytest                                                                     # A1–A7
uv run sweep.py specs/sweep_episode_2012.json --data tests/data/2026-08-24-net15 --out results/sweep_episode_2012
uv run main.py --spec specs/episode_points_2021.json --data tests/data/2026-08-24-net15 --json results/episode_points_2021.json --no-charts --quiet
uv run episode_report.py bundle specs/cash_points_2012.json    --data tests/data/2026-08-24-net15 --baseline BIL --sigma 0.20 --w-max 0.8 > results/episode_2012.md
uv run episode_report.py bundle specs/episode_points_2021.json --data tests/data/2026-08-24-net15 --baseline BIL > results/episode_2021.md
uv run episode_report.py bundle specs/cash_points_2021.json    --data tests/data/2026-08-24-net15 --baseline BIL > results/episode_2021_T.md
uv run episode_report.py partition results/sweep_cash_2012/runs.json    --pair "VT TQQQ/BTAL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200" "VT TQQQ/BIL50+BTAL50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"  > results/episode_partitions.md
uv run episode_report.py partition results/sweep_episode_2012/runs.json --pair … >> results/episode_partitions.md      # and the §5.3 pairs
uv run episode_report.py partition results/sweep_cash_2021/runs.json    --pair … >> results/episode_partitions.md
```

Commit order: (1) tool + tests + docs, **including §7.2's two renames, ten errata and the stub**;
(2) the **pre-registration commit** — the two specs, §3's table (already in the tool,
restated in the spec), §10's conditions and §11's predictions, before any run; (3)
artefacts; (4) the verdict. A3–A5 are pins on committed data and run in commit (1);
they are not predictions and are not scored as such.

## 9. Read protocol

0. The A3–A5 pins hold on the fresh clone; the sweep's `--dry-run` prints 27 windows.
1. **The 2012 attribution** (`episode_2012.md`): the five sleeves' episode return and
   drawdown for E1–E7, and the marginal table against `BIL`. Sum BTAL's marginal
   return over the bears (E1, E2, E3, E5) and over the unwinds (E4, E6, E7); same
   for drawdown.
2. **The 2021 attribution** (`episode_2021.md`, `episode_2021_T.md`): the three
   components at 25 / 50 / 100 %, the winners, and the T-transforms, for E4–E7. Which
   component earns E5, which pays E4, and whether the winners' drawdown benefit in E5
   exceeds the best single component's (complementarity at the episode level).
3. **The partitions** (`episode_partitions.md`): for each §5.3 pair, the episode whose
   trough partitions the windows most cleanly (largest gap between the with- and
   without- win rates), at 5 y and 3 y.
4. **The winners' deepest hole**: A6's pin, restated in the verdict with the E4
   marginal drawdown of BTAL on the 2021 lane beside it.
5. **The decision, §10.**

## 10. Decision rule and outputs — frozen at the pre-registration commit

10.1 **No parameter, coordinate or sleeve moves.** This spec adopts nothing and can
adopt nothing.

10.2 **The ledger's `Open:` line is closed and the first flag is added (§7.1)** if all
three hold on the committed reports: (a) on the 2012 lane, BTAL's marginal drawdown against `BIL` is shallower in at
least three of E1 / E2 / E3 / E5 and deeper by more than 5 pp in E4; (b) on the 2021
lane, KMLM's E5 marginal return exceeds BTAL's; (c) on the 2021 lane, the partition of
each winner vs its T is cleaner by E4's trough than by E5's, or the winners' deepest
episode is E4 (A6's pin). If (a) holds and (b) or (c) fails, the `Open:` line is closed with the
narrower statement of what held and the flag is written to match. If (a) fails, the
`Open:` line stays open with a pointer to this verdict recording why, and no flag is
added.

10.3 **The candidate rule is adopted regardless** (it is a rule about how specs are
written, not a finding): every future sleeve candidate names, in its pre-registration
commit, the episode ids it must win against the incumbent (on marginal drawdown or
marginal return, stated), and E4 as the episode it must not deepen by more than 1 pp.
A candidate that clears a lane's aggregate bar but deepens E4 is not promoted.

10.4 **Flags.** (i) *"The winners' deepest hole is BTAL-made (E4)"* if A6's pin holds;
(ii) *"KMLM earns 2022, BTAL earns 2022's drawdown"* if (b) holds and BTAL's E5
marginal drawdown exceeds KMLM's; (iii) the HANDOFF §7 leave-one-episode-out entry is
retargeted from 2022 to E4 if (c) holds.

10.5 Verdict: `notes/episode-verdict.md`, steps 0–5 plus residuals; every number from
the three reports, the partitions file, and the two panels.

## 11. Pilot measurements — what to expect, and what would falsify it

Every number below is from a prototype of §4's tool on the committed panel bundles
(rerun in-process on net15) and from `results/sweep_cash_2012/runs.json`. The A3–A5
pins in §6 restate the first two tables; the predictions concern the new material
(the 3-year windows, the 2021 partitions, the component panel's full read).

**2012 lane, σ0.20 / w0.8 — episode return % of the TWR index / max drawdown % inside
the window:**

| sleeve | E1 | E2 | E3 | **E4** | E5 | E6 | E7 |
|---|---|---|---|---|---|---|---|
| `BTAL` | +0.2 / −21.8 | +0.4 / −23.5 | +1.1 / −16.6 | **+0.5 / −26.0** | +4.6 / −16.1 | +0.2 / −16.3 | −4.9 / −17.6 |
| `BIL25+BTAL75` | +0.5 / −22.5 | +0.1 / −24.0 | −0.1 / −18.0 | +6.9 / −21.2 | +2.7 / −17.2 | +3.0 / −16.3 | −2.6 / −17.2 |
| `BIL50+BTAL50` | +0.6 / −23.9 | −0.3 / −24.4 | −1.4 / −19.4 | +13.5 / −18.2 | +0.7 / −19.6 | +5.8 / −17.4 | −0.2 / −17.0 |
| `BIL75+BTAL25` | +0.7 / −25.4 | −0.7 / −24.9 | −2.7 / −20.8 | +20.4 / −16.4 | −1.4 / −22.3 | +8.5 / −19.2 | +2.1 / −16.9 |
| `BIL` | +0.6 / −27.1 | −1.1 / −25.9 | −4.0 / −22.2 | +27.5 / −15.3 | −3.7 / −25.1 | +11.3 / −21.4 | +4.3 / −16.8 |
| SPY | +15.0 / −13.2 | +12.3 / −19.5 | −5.5 / −33.7 | +28.2 / −9.5 | −3.7 / −24.6 | +20.6 / −18.8 | +11.8 / −8.9 |

Marginal against `BIL` (return pp / drawdown pp, `+` = shallower):

| sleeve | E1 | E2 | E3 | **E4** | E5 | E6 | E7 |
|---|---|---|---|---|---|---|---|
| `BTAL` | −0.4 / +5.3 | +1.5 / +2.3 | +5.1 / +5.7 | **−27.0 / −10.7** | +8.2 / +9.1 | −11.1 / +5.1 | −9.3 / −0.8 |
| `BIL50+BTAL50` | +0.0 / +3.2 | +0.8 / +1.4 | +2.6 / +2.8 | −14.0 / −2.9 | +4.4 / +5.6 | −5.5 / +4.0 | −4.6 / −0.2 |

BTAL's four bears earn +14.4 pp of return and +22.4 pp of drawdown; its three unwinds
pay −47.4 pp of return and −6.4 pp of drawdown. E4 alone (−27.0 / −10.7) outweighs
every bear together on return and gives back half of their drawdown benefit.

**2021 lane, winners' coordinate — marginal against `BIL` (return pp / drawdown pp):**

| sleeve | E4 (from 2020-12-18) | E5 | E6 | E7 |
|---|---|---|---|---|
| `BIL75+BTAL25` | −2.9 / −1.8 | +2.3 / +2.8 | −2.8 / +2.2 | −2.3 / −0.1 |
| `BIL75+KMLM25` | +2.2 / +1.7 | +4.3 / +3.2 | −2.8 / −0.8 | +2.2 / +1.1 |
| `BIL75+DBMF25` | +2.5 / +1.3 | +2.2 / +1.8 | −1.8 / −1.4 | +1.6 / +0.9 |
| `BTAL` | −11.6 / −7.4 | +8.3 / +8.5 | −11.2 / +5.0 | −9.3 / −0.8 |
| `KMLM` | +8.8 / +3.9 | **+16.5** / +5.8 | −10.7 / −5.9 | +9.1 / +4.3 |
| `DBMF` | +10.0 / +2.9 | +8.2 / +5.2 | −7.3 / −8.2 | +6.6 / +1.3 |
| `BTAL75+KMLM25` | −6.5 / −4.5 | +10.7 / **+11.0** | −10.9 / +3.6 | −4.8 / +0.6 |
| `BTAL75+DBMF25` | −6.3 / −4.5 | +8.6 / +10.2 | −10.0 / +3.0 | −5.3 / +0.5 |
| `BTAL50+KMLM50` | −1.5 / −1.6 | +13.0 / +9.4 | −10.8 / +0.4 | −0.2 / +2.0 |
| T(`B75K25`) | −2.2 / −1.4 | +7.7 / +7.5 | −6.8 / +1.4 | −1.3 / +1.0 |
| T(`B75D25`) | −1.9 / −1.4 | +5.6 / +6.1 | −5.9 / +0.8 | −1.8 / +0.8 |
| T(`B50K50`) | +1.4 / +0.5 | +10.9 / +7.7 | −8.1 / −1.0 | +2.1 / +2.1 |

Predictions, each a falsifiable line for the verdict:

1. **§10.2(a) holds on the 2012 lane**: BTAL shallower in all four bears (+5.3 / +2.3 /
   +5.7 / +9.1) and deeper by 10.7 pp in E4. Falsified by fewer than three bears or an
   E4 penalty under 5 pp when the committed report is read.
2. **§10.2(b) holds**: KMLM's E5 marginal return +16.5 against BTAL's +8.3, with
   BTAL's E5 marginal drawdown the larger (+8.5 vs +5.8) — flag (ii) fires. Falsified
   if the committed report reverses either.
3. **Complementarity is visible per episode**: `BTAL75+KMLM25`'s E5 marginal drawdown
   (+11.0) exceeds both components' (+8.5, +5.8), and `BTAL50+KMLM50`'s E5 marginal
   return (+13.0) exceeds BTAL's. Falsified if the blend's E5 drawdown benefit is not
   above the best component's.
4. **The 3-year partition on the 2012 lane isolates E4 from E3**: with three-year
   windows, the windows containing E3's trough but not E4's (those ending between
   2020-07 and 2021-03) go to pure BTAL on drawdown, and the windows containing E4's
   trough but not E3's (those starting after 2020-03-23) go to the 50/50 — so that at
   3 y the E4 split is at least as clean as at 5 y (10 · 10 vs 2 · 0) and the E3 split
   is *less* clean than at 5 y. Falsified if E3 partitions the 3-year windows at least
   as cleanly as E4.
5. **On the winners' lane the partition is reported, not decided.** Its six
   three-year windows contain E4's trough in exactly one (start 2020-12-18) and E5's in
   five (all but the 2023-06 start), so neither split can be "cleaner" than the other
   in any meaningful count; §10.2(c) is expected to rest on its second clause (A6's
   pin). The direction to record: the one E4 window favours T on Calmar and the winner
   on the floor. Falsified only if that one window goes the other way on both.
6. **The T-transforms halve both sides**: T(`B75K25`) gives back 3.0 pp of E5 marginal
   return (+10.7 → +7.7) and recovers 4.3 pp in E4 (−6.5 → −2.2); T(`B75D25`) 3.0 and
   4.4; T(`B50K50`) 2.1 and 2.9 — roughly the BTAL share removed. Falsified by an
   asymmetry above 2 pp between the two sides for any T.
7. **E6 is the episode where every insurance component loses return** (BTAL −11.2,
   KMLM −10.7, DBMF −7.3) and only BTAL shallows the drawdown (+5.0 against KMLM −5.9,
   DBMF −8.2): the managed-futures arms' 2025 drawdown *deepens* the machine. Falsified
   if either MF arm shallows E6.
8. **E7 is open and decides nothing**: every sleeve's E7 drawdown is within 1 pp of the
   BIL sleeve's (−16.8 to −17.6), and no §10 condition reads it.

## 12. Honest limitations

- **Seven episodes, one machine, one coordinate.** The table is the incumbent's own
  drawdown list at σ0.20 / w0.8; a different coordinate would nominate different
  windows (the pure-BTAL machine at σ0.30 / w0.6 has 2022 at −27.65 % as its deepest).
  The table is frozen so that the attribution is stable, not because it is canonical.
- **Marginal against BIL is one decomposition among several.** It measures each
  component's contribution relative to holding cash in its place at the same sleeve
  weight; it does not separate the component's own return from its covariance with
  TQQQ inside the VT sizing. It is the decomposition the program can compute without
  engine work and the one that answers "what does this arm buy".
- **Episode returns are time-weighted, drawdowns are in-window.** A window's drawdown
  is measured from the window's own running peak, so a sleeve whose fall started before
  the peak date shows a shallower in-window number than its full-history episode. E4's
  BTAL number (−26.0) matches its `drawdowns` block because the window *is* that block;
  the 50/50's E4 (−18.2) is the same for the same reason.
- **The partitions on the 2021 lane have nine windows.** They are directional.
- **Nothing here tests the sleeve before 2011-09**; the synthetic verdict's caveat is
  inherited whole. E4-shaped episodes — an anti-beta crash inside a growth drawdown —
  are exactly the kind 2000–02 may or may not contain, and no proxy exists.

## 13. Deliberately not in scope

A sleeve candidate (this spec produces the rule a candidate must satisfy, not a
candidate; the obvious one — BTAL-heavy on a regime signal, BTAL-light when high beta
leads — is SAFE_SWITCH territory, where the anti-switcher placebo found nothing, and
it comes back only with an E4 kill condition and a placebo arm). Adding curves to
`results.json` (a `results_json.py` change and a schema bump for something the tool
does in-process). A time-varying episode table (frozen by design; a refresh is a spec
change). Rotation strategies (catalog closed). Editing frozen verdicts or errata to
the new winners-file name (§7.2).

## 14. Acceptance checklist

- [x] `episode_report.py` with `bundle` and `partition` modes, `EPISODES` frozen per §3; deterministic
- [x] Tests A1–A7 green from a fresh clone; suite count > 923
- [x] §7.2: two HANDOFF references renamed, six errata entries appended (one opening `REBALANCE_SPEC.md` §11), stub at `docs/WINNING_STRATEGIES.md`, A7 guard over living docs; `notes/`, existing errata and closed-spec text untouched
- [x] Docs per §7.3
- [x] **Pre-registration commit**: `specs/sweep_episode_2012.json`, `specs/episode_points_2021.json`, §10, §11 — before any run
- [x] Artefacts: `results/sweep_episode_2012/`, `results/episode_points_2021.json`, `results/episode_2012.md`, `results/episode_2021.md`, `results/episode_2021_T.md`, `results/episode_partitions.md`, committed together
- [x] `notes/episode-verdict.md` per §9–§10; winners file per §7.1 (ledger `Open:` closed, fifth entry, two flags — the cash verdict's quoted answer untouched); HANDOFF §7 per §10.4(iii)
- [x] No engine file touched; `SCHEMA_VERSION` 4

## 15. Errata (found during implementation)

1. **§12's "The partitions on the 2021 lane have nine windows"** — the lane has
   **six** sensitivity windows; nine is `sweep_cash_2021`'s total window count,
   `full` + `fit` + `test` + 6. §11 prediction 5's "six three-year windows" is
   the correct figure and the one §10.2(c) reads. The directional caveat stands
   and is stronger than §12 states.
2. **§8's commit order puts A4 before the spec it reads.** A4 pins `bundle` mode
   on `specs/episode_points_2021.json`, which §8's commit (2) creates, so
   "A3–A5 … run in commit (1)" cannot hold for it. Resolved as CASH_SLEEVE
   erratum 4 resolved the same conflict for B4: the legs that need no new spec
   file (A1, A2, A3, A5, A6, A7) ship in commit (1), A4 ships in the
   pre-registration commit beside the spec it reads. Every commit is green and
   the freeze is still one commit.
3. **§6 A6's "the panel's −19.1 / −19.1 / −16.1" is not the deepest-drawdown
   column** it sits beside — it is each winner's **E4** depth (−19.06 / −19.07 /
   −16.12), which for B50K50 is its second-deepest, not its deepest. The
   sentence is correct as written; the test pins both columns separately so the
   distinction cannot be lost.
