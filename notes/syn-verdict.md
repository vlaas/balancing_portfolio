Spec: `docs/SYNTHETIC_HISTORY_SPEC.md` · read protocol and kill conditions: §10,
**frozen at commit `2dfb937` before any lane was run** · branch `synthetic-history` ·
primary data `tests/data/2026-08-24-syn-net15`, brackets `tests/data/2026-08-24-syn`
(gross) and two uncommitted `--drag 0.0129` / `--drag 0.0413` roots · objective Calmar,
constraint max drawdown ≥ −50 % · costs TQQQ 1.5 / BTAL 6 / QQQ 1 / SPY 0.7 / BIL 0.5
bps per side, `*` 6, `cash_yield` 0.03 · contributions 10 000 + 500/month · lanes
`sweep_syn_2000` (2000-01-03 → 2011-12-30, holdout 2008-01-02, 18 sensitivity windows)
and `sweep_syn_full` (2000-01-03 → 2026-08-24, holdout 2012-01-03, 44 sensitivity
windows) · predecessors: `notes/comp-verdict.md`, `notes/rot3-verdict.md`.

**Nothing adopted — and the standing caveat is downgraded.** The winners' coordinate
(λ 0.80 / σ 0.20 / w_max 0.8 / SMA-200 gate) is feasible in both bears, ranks **first of
sixteen on both lanes** (`robust_score` 0.0766 and 0.3250), and clears every clause of
§10.7(a): on 2000–2011 it prints Calmar 0.1046 against SPY's 0.0055, CAGR +3.75 %
against +0.31 %, and max drawdown **−35.86 % against SPY's −55.35 %**, with its gate
beating its null on `robust_score` on both lanes. The program-wide "tested on one era"
caveat therefore becomes **"the BTAL sleeve is untested before 2011-09"**.

Two findings are worth more than the verdict. First, **the 2012-lane regime coordinate
(σ 0.30 / w_max 0.6) would have breached the program's own −50 % constraint in the GFC**
— −50.35 % on the primary root and −50.18 / −50.22 / −50.79 % across every drag and
withholding bracket, infeasible at all four. So would every ungated point. Only four of
sixteen grid points survive the bear lane, and all four are gated σ 0.20. Second, **R2 is
answered**: in the 2008–2011 holdout the gated winners' coordinate drew down −30.06 %
against its own null's −36.97 % and SPY's −51.94 %. This machine does insure, in a real
bear, by 21.9 points against the benchmark.

## 1. Frozen labels

| name | spec | rendered |
|---|---|---|
| `W_gate` | λ0.80, σ0.20, w_max 0.8, BIL, gate | `VT TQQQ/BIL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200` |
| `W_null` | the same, no gate | `VT TQQQ/BIL t20 w0-80 QQQ:VOL_EWMA80` |
| `R_gate` | λ0.80, σ0.30, w_max 0.6, BIL, gate | `VT TQQQ/BIL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200` |
| `R_null` | the same, no gate | `VT TQQQ/BIL t30 w0-60 QQQ:VOL_EWMA80` |
| `W_btal`, `R_btal` | the two gated arms on the incumbent sleeve | `VT TQQQ/BTAL …` |
| `S50` | gated static | `TQQQ50/BIL50 gate QQQ<SMA200` |

`W_gate` is the winners' coordinate; `R_gate` is the 2012-lane regime coordinate.

## 2. Anchors confirmed before anything else was read (§9)

| required | measured |
|---|---|
| S9 full Calmar 0.86123626 | **0.86123626** (`syn_bridge_2012`, `W_btal`'s σ0.30 sibling `R_btal`) |
| S9 CAGR 0.2381710 | 0.23817105 (§15 erratum 3: the spec quotes one digit too few) |
| S9 max drawdown −0.27654555 | **−0.27654555** |
| S9 no-gate twin 0.71623794 | 0.71623794 |
| splice: TQQQ 2,749 synthetic + 4,158 real, first bar 1999-03-10 | as stated |
| splice: BIL 3,609 + 4,840, first bar 1993-01-29 | as stated |
| fitted `c` gross / net15 | 1.8970 / 1.9431 %/yr |
| fitted `c_b` gross / net15 | 0.1089 / 0.0931 %/yr |

The 2012 composition anchor reproduces **bit for bit** through the synthetic root, so
the no-contamination invariant of §4 holds where it is load-bearing.

## 3. Step 0 — the bridge: what the cash sleeve costs on real bars

`results/syn_bridge_2012.json`, 2012-01-03 → 2026-08-24, real bars only:

| coordinate | BIL sleeve | BTAL sleeve | Δ max DD | Δ CAGR |
|---|---|---|---|---|
| σ0.30 / w0.6 gated | 0.7386 · 25.93 % · **−35.11 %** | 0.8612 · 23.82 % · **−27.65 %** | BIL **−7.46 pp** | BIL **+2.11 pp** |
| σ0.20 / w0.8 gated | 0.7991 · 21.66 % · **−27.10 %** | 0.6999 · 18.21 % · **−26.02 %** | BIL **−1.08 pp** | BIL **+3.45 pp** |

§7.5 anticipated "7–8 drawdown points" and that is right at σ0.30 — but **at the
winners' coordinate the substitution costs only 1.08 points of drawdown, and BIL wins
on Calmar** (0.7991 vs 0.6999) because it buys 3.45 pp of CAGR. This is the single most
important correction to the spec's priors: the bias carried into every bear-era number
below is about one drawdown point at `W_gate`, not seven. §7.5's estimate compared
σ0.30's BIL arm to σ0.30's BTAL arm; the σ0.20 BTAL twin did not exist until this run.

## 4. Step 1 — K1: feasibility. **Four of sixteen survive.**

Full-window max drawdown, `sweep_syn_2000` (2000–2011) and `sweep_syn_full` (2000–2026)
— identical on both lanes, because both worst drawdowns fall inside the bear era:

| λ | σ | w_max | gate | max DD | feasible |
|---|---|---|---|---|---|
| 0.80 | 0.20 | 0.6 / 0.8 | gate | **−35.86 %** | **yes** |
| 0.94 | 0.20 | 0.6 / 0.8 | gate | **−35.96 %** | **yes** |
| 0.80 | 0.20 | 0.6 / 0.8 | null | −60.74 % | no |
| 0.94 | 0.20 | 0.6 / 0.8 | null | −53.27 % | no |
| 0.80 | 0.30 | 0.6 | **gate** | **−50.35 %** | **no** |
| 0.80 | 0.30 | 0.8 | gate | −50.72 % | no |
| 0.94 | 0.30 | 0.6 / 0.8 | gate | −50.28 / −50.27 % | no |
| 0.80 | 0.30 | 0.6 / 0.8 | null | −77.35 % | no |
| 0.94 | 0.30 | 0.6 / 0.8 | null | −70.34 % | no |

**`R_gate` — the coordinate the 2012 regime lane chose — is infeasible in the GFC on a
cash sleeve**, and it is *on the boundary* in §10.1's sense: −50.35 % is 0.35 pp past
the constraint, and the `c` bracket spans −50.18 % (gross) / −50.22 % (`c_lo`) /
−50.35 % (primary) / −50.79 % (`c_hi`). Every one of those is past −50 %. It fails on
the wrong side at every drag and both withholding conventions, so the flag is not a
bracket artefact. Marked **"infeasible in the GFC on a cash sleeve"** wherever it is
quoted, per §10.7(b).

All four σ0.30 gated points cluster in −50.2 to −50.8 %: the constraint is not
*narrowly* missed by one coordinate, it is missed by the whole σ0.30 row.

## 5. Step 2 — Q1: does the gate earn its keep in a bear? **Yes, by three to four times.**

Gate minus null, every (λ, σ, w_max), on `robust_score`:

| λ | σ | w_max | bear lane gate → null | Δ | full lane gate → null | Δ |
|---|---|---|---|---|---|---|
| 0.80 | 0.20 | 0.6 | 0.0710 → −0.0250 | **+0.0960** | 0.3019 → 0.1686 | +0.1333 |
| 0.80 | 0.20 | 0.8 | 0.0766 → −0.0181 | **+0.0947** | 0.3250 → 0.1866 | **+0.1384** |
| 0.80 | 0.30 | 0.6 | 0.0710 → −0.0250 | +0.0960 | 0.2941 → 0.1686 | +0.1255 |
| 0.80 | 0.30 | 0.8 | 0.0543 → −0.0250 | +0.0793 | 0.3019 → 0.1686 | +0.1333 |
| 0.94 | 0.20 | 0.6 | 0.0746 → 0.0015 | +0.0731 | 0.2941 → 0.1881 | +0.1060 |
| 0.94 | 0.20 | 0.8 | 0.0543 → −0.0114 | +0.0657 | 0.3046 → 0.1989 | +0.1057 |
| 0.94 | 0.30 | 0.6 | 0.0543 → −0.0250 | +0.0793 | 0.2941 → 0.1686 | +0.1255 |
| 0.94 | 0.30 | 0.8 | 0.0388 → −0.0181 | +0.0569 | 0.2941 → 0.1866 | +0.1075 |

**Every gated point beats its null on both lanes**, so Q1's kill condition does not
fire anywhere. In drawdown the gate is worth **+24.89 pp** at σ0.20 λ0.80, **+27.00 pp**
at σ0.30 λ0.80, +17.31 and +20.07 pp at λ0.94 — against **+6.92 pp** on the 2012 lane
(`comp_points.json`: −27.65 % gated vs −34.57 % null). The gate is worth roughly **four
times more drawdown protection in a bear than in the era it was chosen in**, which is
the answer the whole program wanted: the 2012-lane finding was not an era artefact, it
was an *understatement*.

One honest wrinkle. On the 2008–2011 holdout window alone, measured by Calmar, the
**null narrowly beats the gate** at both named coordinates: 0.1948 vs 0.1877 at σ0.20 /
w0.8, 0.1198 vs 0.1015 at σ0.30 / w0.6. The ungated arms fell further and rebounded
harder, and Calmar over a four-year window rewards that. Their drawdowns in the same
window are −36.97 % and −51.35 % against the gated −30.06 % and −42.39 %. The gate
trades rebound for depth, and on this window Calmar prices that trade as roughly a wash
while the drawdown constraint does not.

## 6. Step 3 — Q2: does the machine beat its benchmark where the benchmark was terrible?

`sweep_syn_2000` full window, 2000-01-03 → 2011-12-30:

| strategy | Calmar | CAGR | max DD | turnover |
|---|---|---|---|---|
| **`W_gate`** | **0.1046** | **+3.75 %** | **−35.86 %** | 1.36 |
| `W_null` | 0.0103 | +0.63 % | −60.74 % | 1.48 |
| **`R_gate`** | 0.0710 | +3.57 % | −50.35 % | 0.77 |
| `R_null` | −0.0250 | −1.94 % | −77.35 % | 0.90 |
| `S50` | 0.0199 | +1.28 % | −64.40 % | 0.30 |
| QQQ | −0.0483 | −4.01 % | −82.94 % | 0.08 |
| SPY | 0.0055 | +0.31 % | −55.35 % | 0.07 |
| TQQQ buy-and-hold | −0.3965 | **−39.64 %** | **−99.98 %** | 0.11 |

`W_gate` beats SPY on all three axes — 19× the Calmar, 12× the CAGR, 19.5 points less
drawdown — over a twelve-year window in which the S&P compounded at 0.31 %/yr. It beats
the gated static `S50` on all three as well. Calendar years, from `syn_points.json`:

| strategy | 2000 | 2001 | 2002 | 2008 | 2009 |
|---|---|---|---|---|---|
| `R_gate` | −31.9 | −0.5 | **+1.1** | −42.0 | +54.6 |
| `R_null` | −33.2 | −30.2 | −34.9 | −45.4 | +66.6 |
| **`W_gate`** | −20.8 | **+0.7** | **+1.1** | **−29.1** | +35.7 |
| `W_null` | −21.7 | −19.6 | −23.6 | −31.9 | +43.1 |
| `S50` | −48.1 | −3.9 | +0.8 | −46.5 | +57.6 |
| QQQ | −38.3 | −33.3 | −37.3 | −41.8 | +54.5 |
| SPY | −8.9 | −11.9 | −21.7 | −37.0 | +25.9 |
| TQQQ | −92.3 | −88.8 | −86.1 | −88.4 | +197.7 |

The gate turns 2001 and 2002 from −20 %/−24 % into **+0.7 %/+1.1 %** — it sat the grind
out in cash at 3 %. That is the pre-registered "wins the grind" pattern, emphatically.
The "loses the first leg" half is where the prediction breaks; see prediction 4 below.

## 7. Step 4 — Q3: the plateau. **It survives, and it narrows.**

On `sweep_syn_full`, the eight gated points span **0.0309** of `robust_score` (0.2941 to
0.3250) — well inside §10.4's 0.10 bar. On `sweep_syn_2000` they span **0.0378** (0.0388
to 0.0766). The plateau is real across 26.6 years including both bears.

λ0.80 vs λ0.94 at each (σ, w_max), gated, on `robust_score`:

| σ, w_max | bear lane | full lane |
|---|---|---|
| 0.20, 0.6 | 0.0710 vs **0.0746** — λ0.94 wins | **0.3019** vs 0.2941 |
| 0.20, 0.8 | **0.0766** vs 0.0543 | **0.3250** vs 0.3046 |
| 0.30, 0.6 | **0.0710** vs 0.0543 | 0.2941 vs 0.2941 — tie |
| 0.30, 0.8 | **0.0543** vs 0.0388 | **0.3019** vs 0.2941 |

λ0.80 wins three of four on each lane, with one loss on the bear lane and one tie on the
full lane. The RiskMetrics control does not overturn the choice, but "λ0.80 beats λ0.94
at every (σ, w_max)" is **not** true here (prediction 6, falsified in part).

σ0.20 and σ0.30 interleave rather than order cleanly — the σ0.30 points' best
(0.0710 bear, 0.3019 full) sits above the σ0.20 points' worst (0.0543, 0.2941) — but no
σ0.30 point sits above *every* σ0.20 point, so §11's stated falsifier does not fire.
The decisive separation between the rows is not `robust_score` at all: it is K1.

`rank_worst` over the sensitivity sets: 4 on the bear lane for `W_gate` (median 3 of 4
feasible competitors) and 4 on the full lane (median 2). With only four feasible points
competing, the rank columns carry little information here and are reported for the
record, not leaned on.

## 8. Step 5 — Q4: the brackets. **Inert. No flag moves.**

`syn_points.json` on four roots — primary net15, gross `-syn`, `c_lo` 1.29 %/yr,
`c_hi` 4.13 %/yr — full window 2000-01-03 → 2026-08-24:

| arm | primary | gross | `c_lo` | `c_hi` | spread |
|---|---|---|---|---|---|
| `W_gate` max DD | −35.86 % | −35.61 % | −35.75 % | −36.22 % | 0.61 pp |
| `W_gate` CAGR | 13.16 % | 13.40 % | 13.26 % | 12.89 % | 0.51 pp |
| `R_gate` max DD | **−50.35 %** | **−50.18 %** | **−50.22 %** | **−50.79 %** | 0.61 pp |
| `R_gate` CAGR | 15.20 % | 15.42 % | 15.29 % | 14.86 % | 0.57 pp |

Every §10 flag is identical on all four roots: `W_gate` feasible everywhere, `R_gate`
infeasible everywhere, the gate ahead of the null everywhere. The widest movement in any
arm is 0.91 pp of drawdown (`W_null`, an infeasible arm); the gated arms move 0.61 pp,
marginally past §11's ≤ 0.6 pp bound and nowhere near enough to change a reading.

## 9. Step 6 — the R2 question, finally answerable

From `sweep_syn_2000`'s `kind == "test"` rows — 2008-01-02 → 2011-12-30, a real bear
that was never in any fitting window for these parameters:

| strategy | max DD | Calmar | CAGR |
|---|---|---|---|
| **`W_gate`** | **−30.06 %** | 0.1877 | +5.64 % |
| `W_null` | −36.97 % | 0.1948 | +7.20 % |
| `R_gate` | −42.39 % | 0.1015 | +4.30 % |
| `R_null` | −51.35 % | 0.1198 | +6.15 % |
| `S50` | −45.10 % | 0.0448 | +2.02 % |
| QQQ | −49.31 % | 0.0637 | +3.14 % |
| SPY | −51.94 % | −0.0334 | −1.73 % |
| TQQQ buy-and-hold | −92.76 % | −0.1688 | −15.66 % |

**In points: the gated winners' coordinate insured 21.88 points against SPY and 6.91
points against its own ungated twin, while earning +5.64 %/yr where SPY lost 1.73 %/yr.**
The rotation program's R2 tension — "these strategies do not insure" against "this
holdout had nothing to insure against" — resolves for *this* machine in favour of the
second reading. Its holdout genuinely had nothing to insure against; given one that did,
it insures. That says nothing about the rotation strategies themselves, which were never
run on these roots (§13).

## 10. Step 7 — the decision

**(a) fires.** `W_gate` is feasible on both lanes (−35.86 %), beats SPY on
`sweep_syn_2000`'s full-window Calmar (0.1046 vs 0.0055) with a shallower max drawdown
(−35.86 % vs −55.35 %), and its gate beats its null on `robust_score` on both lanes
(+0.0947 and +0.1384). The program-wide caveat is downgraded from **"tested on one
era"** to **"the BTAL sleeve is untested before 2011-09"**, and
`docs/HANDOFF_COMPOSITION.md` §7 is rewritten to say so.

**(b) fires** for the σ0.30 row and every ungated point: marked *infeasible in the GFC
on a cash sleeve*, with the bracket values beside `R_gate` wherever it is quoted.

**(c) does not fire.** The gate passes Q1 on both lanes at every coordinate; the gate
line stays closed.

**(d) holds. No parameter moves.** Nothing here is adopted. σ0.20 / w_max 0.8 / λ0.80 /
SMA-200 gate remains the incumbent because the 2012 lanes chose it, not because these
lanes agree — they are a falsifier that failed to falsify.

### Predictions, scored (§11, frozen at `2dfb937`)

| # | claim | outcome |
|---|---|---|
| 1 | σ0.30 / w0.6 infeasible on both lanes at every drag | **held** — −50.35 / −50.18 / −50.22 / −50.79 %, infeasible on all four roots |
| 2 | σ0.20 / w0.8 feasible on both lanes and clears §10.7(a) | **held** — −35.86 % vs SPY −55.35 %, CAGR 3.75 % vs 0.31 %, Calmar 0.1046 vs 0.0055, gate 0.1046 vs null 0.0103 |
| 3 | the gate is worth more in a bear than on the 2012 lane | **held** — +0.094 Calmar / +24.89 pp at σ0.20, +0.096 / +27.00 pp at σ0.30, against +0.145 / +6.92 pp on 2012–2026; no gated point loses to its null on either lane |
| 4 | loses the first leg, wins the grind | **falsified** — the grind half held emphatically (2001–02: +0.7/+1.1 % and −0.5/+1.1 % against SPY's −11.9/−21.7 %), but `W_gate` **won** the 2008 first leg, −29.1 % against SPY's −37.0 %. The stated falsifier ("a first-leg calendar-year win over SPY at either coordinate") fires on the spec's own pre-registered number |
| 5 | 3× buy-and-hold annihilated, gated static no substitute | **held** — TQQQ −99.98 % and −39.64 %/yr on 2000–2011; `S50` −64.40 %, infeasible, at +1.28 %/yr |
| 6 | plateau survives but tilts | **held in part** — the eight gated points span 0.0309 (full) and 0.0378 (bear), inside the 0.10 bar; but λ0.80 loses to λ0.94 at σ0.20/w0.6 on the bear lane and ties at σ0.30/w0.6 on the full lane, so "λ0.80 beats λ0.94 at every (σ, w_max)" is false. σ0.20 and σ0.30 interleave; the stated σ0.30 falsifier does not fire |
| 7 | the brackets are inert | **held on substance** — no K1 flag and no Q1/Q2 sign differs across the four roots; the numeric bound is marginally exceeded, gated arms moving 0.61 pp of drawdown against the predicted ≤ 0.6 pp |
| 8 | the sleeve is the largest known bias, pointing one way | **materially revised** — BIL costs 7.46 drawdown points against BTAL at σ0.30/w0.6 but only **1.08** at σ0.20/w0.8, where BIL also wins Calmar 0.7991 vs 0.6999 on +3.45 pp of CAGR. At the winners' coordinate the bear-era drawdowns are near-unbiased, not upper bounds by 7–8 points |

## Residuals worth remembering

1. **Every feasible point is on the grid boundary.** All four sit at σ0.20, the lowest
   σ in the §7.1 grid, and the sweep flags `edge: yes` on each. The bear lanes are
   asking for a *lower* volatility target than the grid contains, and §13 forbids
   re-fitting here. A bear-first spec with its own holdout design (§10.7(c)'s shape,
   applied to σ rather than the gate) is the honest way to find out whether σ0.15 or
   σ0.10 is better still — and it must not be answered on these roots.

2. **`R_gate` is 0.35 points past the constraint, not 5.** −50.35 % is a hair over the
   line, and the line is a round number the program chose. The finding is not that the
   regime coordinate is reckless; it is that it has **no margin at all** against a
   GFC-shaped event on a cash sleeve, and that its 2012-era numbers gave no hint of it
   (−27.65 % on BTAL, −35.11 % on BIL). Whether BTAL would have closed that 15-point gap
   in 2008 is exactly what cannot be known — see 4.

3. **The gate loses the 2008–2011 window on Calmar and wins it on depth.** Null beats
   gate 0.1948 vs 0.1877 (σ0.20) and 0.1198 vs 0.1015 (σ0.30) over the holdout, while
   drawing down 6.9 and 9.0 points deeper. Anyone reading a single Calmar number over a
   single four-year bear-and-recovery window will conclude the gate is worthless. It is
   the drawdown column and the full-window `robust_score` that carry the finding.

4. **The one thing still untested is the sleeve, and it is now the whole caveat.** BTAL
   starts 2011-09-13 and has no pre-2011 proxy this repo can validate (§13). Step 0
   narrowed the known bias at the winners' coordinate to ~1 drawdown point on the real
   era, but 2000–02 is precisely the window where a long-low-beta / short-high-beta
   sleeve would have behaved *least* like a T-bill fund. The bear-era numbers are the
   machine-with-cash, and that is all they are.

5. **2000 is a Nasdaq event, not a "first leg".** `W_gate` lost 2000 to SPY by 11.9
   points (−20.8 vs −8.9) and won 2008 by 7.9 (−29.1 vs −37.0). The pre-registered
   "loses the first leg" story reads the two bears as the same shape; they are not.
   In 2000 the machine's underlying index fell −38.3 % while SPY fell −8.9 %, so the
   gap is the asset, not the timing. In 2008 both fell together and the gate had time to
   fire. A future prediction about gate behaviour should condition on whether the bear
   is index-wide.

6. **TQQQ buy-and-hold prints −99.98 % and never recovers.** Its second-deepest episode
   in the whole 26 years is −39.7 % in January 2000, because the dot-com drawdown never
   ends — everything after is inside it. `S50`, the gated static, prints −64.40 %.
   Volatility targeting is not a refinement at 3×; it is the difference between a
   portfolio and a total loss.
