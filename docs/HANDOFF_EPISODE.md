# Handoff: after the episode verdict — state, conventions, and what is worth doing next

Written at `4eecc76` (episode attribution merged; 979 tests green on a fresh clone).
Supersedes `HANDOFF_COMPOSITION.md` as the entry point; that file's §1–§6 are still
correct and are not repeated here except where something changed. Read this, then
CLAUDE.md §6, then the verdict you are about to build on. Everything decision-grade
is in committed artefacts; nothing in any previous conversation is needed.

## 1. The task for the next conversation

Pick **one** increment from §7 — the recommendation is §7.1, the return-stacked
statics, with §7.2 (the monthly-read gate) as the alternative — and write its spec
under the Option A protocol: fresh clone, suite green, inspect the surface it
touches, measure, pilot, pre-register, hand off. Do not open a sleeve spec (§4) or
a gate spec (§4) without new data; both lines are closed on their own terms.

## 2. Standing verdicts (authoritative files, all in `notes/` and `docs/`)

| line | spec → verdict | outcome, one line |
|---|---|---|
| cadence | REBALANCE_SPEC → §7 of the spec | monthly stands; weekly whipsaws in 2025–26 |
| safe swap | SAFE_SWAP_SPEC → `safe-swap-verdict.md` | keep BTAL over (flat-3 %) cash; MF arms not crowned |
| safe blend | SAFE_BLEND_SPEC → `safe-blend-verdict.md` | **the winners**: B75K25, B75D25, B50K50 |
| safe switch | SAFE_SWITCH_SPEC → `safe-switch-verdict.md` | zero promotions; anti-switcher placebo beat the switchers |
| regime gate | REGIME_SPEC → `regime-verdict.md` | VIX/VIX3M gate is a substitute for SMA-200 at best |
| rotation ×3 | ROTATION_* → `rot-`, `rot2-`, `rot3-verdict.md` | catalog closed; nothing beats the machine on its lanes |
| composition | COMPOSITION_SPEC → `comp-verdict.md` | momentum-score gate: substitute at best; gate line hits a structural ceiling (−27.2 % COVID floor) |
| synthetic history | SYNTHETIC_HISTORY_SPEC → `syn-verdict.md` | winners' coordinate feasible in 2000–02 and 2008; σ0.30/w0.6 **infeasible in the GFC on cash**; caveat downgraded to "BTAL sleeve untested before 2011-09" |
| cash sleeve | CASH_SLEEVE_SPEC → `cash-verdict.md` | half-swap not adopted; **pure BTAL dominated at σ0.20 on all three real lanes** |
| episode attribution | EPISODE_SPEC → `episode-verdict.md` | **the hinge is E4 (2020-09 → 2021-09), not 2022**; the winners' 2022 return is KMLM's, their deepest hole is BTAL's |

The winners are unchanged since the blend verdict: `vol_target` on TQQQ against
QQQ's EWMA vol, λ0.80, σ0.20, w_max 0.8, leverage 3, monthly, SMA-200 gate on QQQ,
sleeves `BTAL75+KMLM25` / `BTAL75+DBMF25` / `BTAL50+KMLM50`. Their numbers and every
standing flag live in `docs/WINNING_STRATEGIES_CASH_SLEEVE.md` (`robust_score` 0.8470
/ 0.8574 / 0.8849 from `results/sweep_comp_2021/summary.json`); the previous
winners-file path is a one-line stub (EPISODE_SPEC §7.2). That file records; it does
not decide.

## 3. Findings that shape whatever comes next

- **The gate line is at a structural ceiling on the 2012 lane.** COVID prints
  −27.2 % in every cap-only arm and the uninsured 2020-09 episode sits at −25 %
  behind it; no monthly buy-cap gate — trend, term-structure or momentum — can move
  the max drawdown below −27.2 %, and the best possible 2022 gate is worth 0.5 pp.
  SMA-200 → VIX/VIX3M → score is three signal families, zero adoptions, one floor.
- **The sleeve line has been asked every question the data can answer**: swap,
  blend, switch, cash fraction, attribution. The corrected sentence (episode residual
  1): BTAL is insurance against fast correlated equity falls *and* a short position
  in high beta leading, and 2012–2026 contained more of the second. E4 alone costs
  more return than the four bears together earn (−27.0 vs +14.4 pp against cash) and
  half their drawdown benefit. E6 (the tariff episode) is the one window where BTAL
  is unambiguously the right sleeve and the managed-futures arms deepen the machine.
- **A monthly-read SMA-10 gate reproduces the daily SMA-200 gate to 0.004 on the 2012
  lane** (comp residual 1; `sma_months: 10` is already in the grammar). Never run on
  the 2021 / 2019 lanes. If it holds there, the live rule can be one number read once
  a month.
- **The 2021 lane's holdout is noise** by the runner's own warning (twenty months);
  its `robust_score` moves ~0.01 per four trading days. The 2012 lane carries the
  weight of every comparison; the 2021 lane is read for direction.
- **`robust_score` is not comparable across lanes of different grid shape** (cash
  residual 3). Adding a σ dimension to the 2021 lane gave every point a neighbour the
  anchor lane never had, and two anchors could not reproduce. State anchors on the
  full-window objective; read `robust_score` only within its lane.
- **E4 is now specifiable**: 2020-09-02 → 2021-09-03, trough 2021-03-08. It is the
  winners' own floor for two of three, and it partitions the 2012 lane's windows
  10/10 against 2/10 where 2022 gives 7/7 and 5/13. The candidate rule (CLAUDE.md §6)
  requires every sleeve candidate to name it.

## 4. What is closed — do not reopen without new data

- **The SMA-200 gate** (regime, composition). A bear-first gate spec is the only
  reopening path, and it needs pre-inception data that does not exist for BTAL.
- **The sleeve at the winners' coordinates** (swap, blend, switch, cash, episode).
  A BTAL-heavy-on-regime variant returns only with an E4 kill condition and a placebo
  arm, and SAFE_SWITCH says to expect nothing.
- **The rotation catalog** (three stages). Reopening it needs pre-2002 proxies for
  EFA / IEF / DBC / VNQ — a new export class.
- **Cadence**, **λ0.80 over λ0.94**, **the plateau** — all re-tested through two
  synthetic bears and unchanged.

## 5. Fixed conventions (do not re-derive) — additions since HANDOFF_COMPOSITION §5

Everything in HANDOFF_COMPOSITION §5 and §6 still holds. Added since:

- **Data roots**: `tests/data/2026-08-24` (gross pair) / `-net15` (primary) / `-syn`
  and `-syn-net15` (synthetic pre-inception, falsifiers only) / `-net15-bil0` (BIL at
  its own ~0 % withholding, the CASH §10.5 tie-breaker). `make_net_tr.py` takes
  `--rate-override SYM=RATE`; `make_synthetic.py` fits per root and takes
  `--withholding`. `data/macro/` is unloadable by design.
- **Cost map**: the incumbent lanes' blend map — TQQQ 1.5 / BTAL 6 / DBMF 2.5 / KMLM 6
  / QQQ 1 / SPY 0.7 / **BIL 0.5** / `*` 6 bp per side; flat-20 as stress; `cash_yield`
  3 % on uninvested residue only (cash in a sleeve is `BIL`).
- **Lane windows**: 2012 lane start 2012-01-03, holdout 2023-01-01, sens 6 m / 5 y
  (23 windows); 2021 lane 2020-12-18, holdout 2025-01-01, sens 6 m / 3 y (9); 2019
  lane 2019-05-08, holdout 2024-01-01, sens 6 m / 3 y (12); bear lanes 2000-01-03 →
  2011-12-30 (holdout 2008-01-02) and 2000-01-03 → end (holdout 2012-01-03).
- **Anchors that must reproduce** are listed in §8; state new anchors on the
  full-window objective, never on `robust_score`.
- **The episode table** (`episode_report.EPISODES`, seven windows E1–E7) is frozen;
  a refresh is a spec change. Report tools: `regime_report.py` (ratio signals),
  `score_report.py` (monthly scores), `episode_report.py` (`bundle` and `partition`
  modes; the bundle mode reruns in-process because `results.json` carries no curve).

## 6. Conventions settled in the last five specs that are written nowhere else

These are the things a fresh context would otherwise relearn the hard way.

1. **A spec is frozen from its pre-registration commit.** Afterwards it is touched
   only through its errata section — always the last numbered section, numbering
   continuing from the one before; a spec without one gets one appended, first
   entry dated as post-hoc (REBALANCE §11 is the precedent). Decision rules,
   checklists (ticked or not), and pilot tables are all frozen text. Verdicts in
   `notes/` are never edited.
2. **Living documents are an allowlist**: `docs/HANDOFF_*.md`, `docs/ARCHITECTURE.md`,
   `docs/STRATEGY_DEVELOPMENT.md`, `docs/DECLARATIVE_SPEC.md`, `CLAUDE.md`, `README.md`,
   and `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`. A guard test over living docs greps
   an allowlist, never `docs/*.md`; specs are never in scope. **This file goes into
   A7's allowlist in the commit that adds it** (`tests/test_episode.py`), which is why
   it does not spell the stub's path.
3. **The winners file has two kinds of section.** "Sleeve composition — what has
   been asked and answered" is a ledger (question, verdict's own answer quoted,
   an `Open:` line that later specs *close* rather than delete); "Standing flags"
   is where facts that travel with the winners go. A verdict adds a ledger entry
   and, if warranted, a flag; it never rewrites a prior verdict's quoted answer.
4. **Test ids take a fresh letter per spec** — used so far: T (total return), N
   (net TR), R (regime), C (composition), S (synthetic), B (cash sleeve), A
   (episode) — and must not collide with the spec's own ids (EPISODE_SPEC's tests
   were E1–E7 until they collided with episodes E1–E7).
5. **Pilot tables and predictions**: every number in a spec comes from a sandbox run
   or a committed artefact, never from memory; a pilot is full-window only and says
   so; a prediction's falsifier must not be one the spec's own pilot table already
   contradicts (SYNTHETIC prediction 4 was scored falsified on a number two
   paragraphs above it); count the windows before predicting a partition (the 2021
   lane has six sensitivity windows, not nine); adding a grid dimension changes the
   statistic, so a bar carried from a lane of different grid shape is a different
   bar (CASH erratum 5). Predictions about *shape* (monotone, "at least as clean")
   fail on the letter more often than predictions about *direction*; prefer the
   latter and pin the former.
6. **Pins are not predictions.** A test that pins a number already measurable from
   committed data ships with the tool commit and is not scored in the verdict; only
   claims about new runs are predictions.
7. **Commit order is four commits**: (1) engine/tool + tests + docs, (2) the
   pre-registration commit — specs, bars, predictions, nothing run, (3) artefacts,
   (4) the verdict. A test that reads a spec file created in (2) ships in (2)
   (CASH erratum 4, EPISODE erratum 2). The verification step after implementation
   is: fresh clone, suite, `git diff --stat <prereg> <verdict> -- specs/` empty,
   every headline number recomputed from `summary.json` / `runs.json` / the bundles.
8. **Withholding is per-series in shape**: a leveraged fund's tiny distributions are
   a constant absorbed by a fitted drag (4.6 bp/yr on TQQQ); a T-bill fund's are
   proportional to the rate and need `(1 − w)` on the accrual (SYNTHETIC §2.5).
   BIL's true NRA rate is plausibly ~0 (§871(k)); the `bil0` root exists for any
   margin under 0.02 that involves BIL.
9. **Every σ point in a two-value grid is an edge point**; `neighbour_min` is then
   the one neighbour that exists. Extend before believing a neighbourhood-bound score.

## 7. Open threads — the candidates for the next spec, with their shapes

### 7.1 Return-stacked statics (recommended)

NTSX (2018-08-02), GDE (2022-03-17), RSST (2023-09-06), RSSB (2023-12-05), and their
kin (NTSI/NTSE 2021-05-20, RPAR 2019-12-13, UPAR 2022-01-04, RSBT 2023-02-08) are all
in the 2026-08-24 pair. The question is whether a *static* return-stacked ETF (or a
static blend of them) is a substitute for the machine — no gate, no VT, one ticker.
Shape: a plain `fixed` bundle on the lanes where each exists (NTSX reaches the 2019
lane; the rest only the 2021 lane or shorter), against the winners and SPY, with the
per-episode panel; no engine work; bar pre-registered as "beats a winner on the
2019 lane's `robust_score` with a floor not deeper" and the honest expectation that a
static loses on floor (it has no gate). Cheap, orthogonal to the incumbents, closes
the longest-standing item on the handoff list. If a static blend is proposed as a
*sleeve* member, it is a sleeve candidate and §6's candidate rule applies.

### 7.2 The monthly-read gate (`sma_months: 10`) on the 2021 and 2019 lanes

One arm per lane (comp residual 1). If it reproduces `G_sma` within 0.02 of
`robust_score` and 1 pp of floor at the winners' coordinate, the live rule becomes a
single month-end read and the winners' documentation says so; if not, the daily read
is load-bearing and that is worth knowing too. Half a day. Could be folded into 7.1's
lanes as a control arm, but a spec answers one question.

### 7.3 `MACRO_DATA_SPEC`

FRED availability-lag ingestion; gates GTT / LAA. Only worth doing if the rotation
catalog reopens, which needs pre-2002 proxies. Low value now.

### 7.4 σ below 0.20 (syn residual 1)

Every feasible bear-lane point sits at the grid's lowest σ. A bear-first re-fit spec
with its own holdout design; explicitly a re-fit, and the real lanes will price a
lower σ against ~3 pp of CAGR. Not before 7.1 / 7.2.

### 7.5 BTAL-heavy-on-regime (SAFE_SWITCH territory)

Returns only with an E4 kill condition (must not deepen E4 by > 1 pp), a placebo
anti-switcher arm, and a leave-one-episode-out lane with E4 deleted. Expect nothing.

### 7.6 Data need with no path

A pre-2011 anti-beta proxy. The AQR BAB factor is monthly and academic — a different
data class. Without it, the sleeve caveat ("untested before 2011-09") stands and every
sleeve verdict inherits it.

### 7.7 Rotation leftovers

Defensive-sleeve isolation (rot3 residual 6); Stage-1 residual 6 (relative-only
momentum −50.30 % on the crisis window). Catalog closed; noted for completeness.

## 8. Verification expectations for the next conversation

Fresh clone at ≥ `4eecc76`; `uv sync`; suite **979** green. Before writing anything,
reproduce at least these from the committed artefacts (not from this file):

- 2012 lane, `VT TQQQ/BTAL t30 w0-60 λ0.80 gate QQQ<SMA200`, `2026-08-24-net15`,
  2012-01-03 →, blend costs: full Calmar **0.86123626**, CAGR 0.23817105, max DD
  −0.27654555 (`results/sweep_cash_2012`, also `syn_bridge_2012`); no-gate twin
  0.71623794; SPY 0.43404677.
- Winners on `results/sweep_comp_2021/summary.json`: robust 0.8470 / 0.8574 / 0.8849,
  full 0.8529 / 0.8574 / 0.8849, `rank_worst` 9 / 11 / 14.
- Cash lane, σ0.20 / w0.8, 2012: `BTAL` full 0.69991357, `BIL` 0.79914190,
  `BIL50+BTAL50` robust 0.7847 vs `BTAL` 0.6590 (+0.1257).
- Synthetic: `W_gate` on 2000–2011 Calmar 0.1046 / CAGR 3.75 % / max DD −35.86 %;
  `R_gate` −50.35 % (infeasible); fitted `c` 1.8970 (gross) / 1.9431 (net15).
- Episode: `uv run episode_report.py bundle specs/cash_points_2012.json --data
  tests/data/2026-08-24-net15 --baseline BIL --sigma 0.20 --w-max 0.8` reproduces
  `results/episode_2012.md` byte-for-byte; BTAL's E4 marginal −27.0 / −10.7; KMLM's
  E5 marginal return +16.5 vs BTAL's +8.3.

Then read `notes/episode-verdict.md` and the winners file's flags, and start the
spec from the surface it touches — for 7.1 that is `specs/winners.json`'s bundle
grammar and the inception dates above; for 7.2 it is `strategies/gate.py`'s
`sma_months` kind and `results/sweep_comp_2012` where `G_sma10m` already ran.

## 9. Startup prompt for the next conversation

Paste this as the first message:

> Continue the `vlaas/balancing_portfolio` program. Start by reading
> `docs/HANDOFF_EPISODE.md` (the entry point), then `CLAUDE.md` §6, then
> `notes/episode-verdict.md`. Follow the Option A protocol: fresh clone at or after
> `4eecc76`, `uv sync`, suite 979 green, reproduce the §8 anchors from committed
> artefacts before writing anything, cite only numbers from your own sandbox runs or
> committed files. The task is HANDOFF_EPISODE §7.1 — a spec for the return-stacked
> statics (NTSX / GDE / RSST / RSSB and kin) as a static alternative to the machine:
> measure inceptions and lane coverage, pilot on full windows, pre-register the bar
> and predictions per §6's conventions, no engine work. If you judge §7.2 (the
> monthly-read gate) the better first increment, say why before writing. Deliver the
> spec as `docs/<NAME>_SPEC.md` in the house structure (goal · measured facts ·
> design · tests with a fresh letter · lanes · docs · run protocol · read protocol ·
> frozen decision rule · pilot with falsifiable predictions · limitations · not in
> scope · checklist · errata).
