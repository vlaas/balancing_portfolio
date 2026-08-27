# Winning strategies

The three incumbents, the artefacts their numbers come from, and the flags that
travel with them. **This file records; it does not decide.** A strategy enters or
leaves it only through a spec's decision rule, and every number here is copied
from a committed artefact, never recomputed by hand.

Created by CASH_SLEEVE_SPEC §10.6(b) — the file had been named by four specs
(REBALANCE §7.5, REGIME §6, SAFE_SWITCH §6.8, COMPOSITION step 8) and never
written, because until now no verdict had anything to put in it.

## The three winners

All three are the same machine at the same coordinate — `vol_target` on TQQQ
sized against QQQ's EWMA volatility, λ0.80, σ_target 0.20, `w_max` 0.8,
leverage 3, monthly rebalancing, SMA-200 gate on QQQ — and differ only in the
safe sleeve. Runnable as `specs/winners.json`.

| name | sleeve | `robust_score` | full Calmar | CAGR | max DD | holdout test | `rank_worst` |
|---|---|---|---|---|---|---|---|
| B75K25 | `BTAL75+KMLM25` | 0.8470 | 0.8529 | 16.26 % | −19.06 % | 0.8470 | 9 |
| B75D25 | `BTAL75+DBMF25` | 0.8574 | 0.8574 | 16.35 % | −19.07 % | 0.8825 | 11 |
| B50K50 | `BTAL50+KMLM50` | 0.8849 | 0.8849 | 18.49 % | −20.90 % | 1.1674 | 14 |

Source: `results/sweep_comp_2021/summary.json`, strategies `[1]`, `[8]`, `[15]`
— the 2020-12-18 → 2026-08-24 lane on `tests/data/2026-08-24-net15`, holdout
2025-01-01, sensitivity 6 m / 3 y (9 windows), objective `calmar`, constraint
`max_drawdown ≥ −0.50`, blend cost map, `cash_yield` 3 %. `rank_worst` is
relative to that lane's 21 grid points and is not comparable across lanes.

Promoted by `notes/safe-blend-verdict.md` (B75K25 the `robust_score` leader,
B75D25 the robustness / `rank_worst` pick, B50K50 the return variant). The
2021 lane's holdout is under two years and its test column is noise by the
runner's own warning; the 2012 lane carries the weight.

## Standing flags

- **`BTAL` alone is not a σ0.20 baseline.** At σ0.20 it is **dominated by
  `BIL50+BTAL50` on every real lane** — 2012 (Δ`robust_score` +0.126, window
  floor 1.45 pp shallower), 2019 (+0.246, 6.61 pp) and 2021 (+0.200, 3.00 pp),
  all four clauses of the safe-blend bar on each, on the gross and flat-20
  brackets too. Quote `BIL50+BTAL50` where a σ0.20 pure-BTAL baseline would have
  gone. The domination is coordinate-specific: at σ0.30 / w0.6 the same swap
  fails three of four clauses (CASH_SLEEVE_SPEC, `notes/cash-verdict.md` §3–§4).
- **The sleeve's cash is `BIL`**, a traded symbol with real distributions and a
  0.5 bp spread; `cash_yield` covers uninvested residue only.
- **The BTAL sleeve is untested before 2011-09.** The synthetic-history verdict
  downgraded the program-wide caveat to exactly this, and confirmed the winners'
  coordinate is feasible in both modelled bears (`notes/syn-verdict.md`).
- **The 2012-lane regime coordinate σ0.30 / w_max 0.6 is infeasible in the GFC
  on a cash sleeve** (−50.35 %), as is every ungated point (`notes/syn-verdict.md`).
- **Monthly rebalancing stands**, with a measured cadence rationale in
  `docs/REBALANCE_SPEC.md` §7.5.
- **The SMA-200 gate stands.** Neither the VIX/VIX3M regime gate
  (`notes/regime-verdict.md`) nor the momentum-score composition
  (`notes/comp-verdict.md`) beat it.
- **The winners' deepest hole is BTAL-made, not a TQQQ bear.** It is the 2021-01 →
  2021-03 anti-beta unwind (E4), where the BTAL-75 sleeves cost 4.5 pp of drawdown
  against cash. BTAL earns its keep in the TQQQ bears (E1, E2, E3, E5: +2 to +9 pp
  shallower) and pays for it when high beta leads (E4, E6, E7: −9 to −27 pp of
  episode return); over 2012–2026 at σ0.20 the payments exceed the earnings, which
  is why pure BTAL is dominated there. The winners' 2022 return is mostly KMLM's
  (+16.5 pp against BTAL's +8.3); BTAL's 2022 contribution is drawdown (+8.5 pp),
  and the blend's (+11.0 pp) exceeds either component's (EPISODE_SPEC,
  `notes/episode-verdict.md`).
- **Sleeve candidates are pre-registered against the episode table.** A candidate
  names, before it runs, the episodes of EPISODE_SPEC §3 it must win against the
  incumbent and states that it must not deepen E4 by more than 1 pp (§10.3).

## Sleeve composition — what has been asked and answered

- *Is a blended sleeve better than a single safe asset?* Yes —
  `notes/safe-blend-verdict.md` promoted the three above.
- *Should BTAL be swapped for a managed-futures arm?* No —
  `notes/safe-swap-verdict.md` kept BTAL and declined to crown KMLM.
- *Should the sleeve switch between arms on a signal?* No —
  `notes/safe-switch-verdict.md`, zero promotions.
- *Should half the sleeve's BTAL be cash?* **No, at these coordinates.**
  CASH_SLEEVE_SPEC's single candidate cleared no clause against any of the three
  winners, on any lane or bracket, or at BIL's own withholding rate:

  > At σ0.20, pure BTAL is dominated by a half-BTAL / half-BIL sleeve on the
  > 2012 and 2019 lanes; the BTAL-heavy sleeves were chosen on a lane where 2022
  > is one year in six, and the half-swap buys Calmar there with return at a
  > 0.8–1.5 pp drawdown cost (CASH_SLEEVE_SPEC, `notes/cash-verdict.md`).

  The "2022 is one year in six" framing in that answer is superseded by the next
  entry.

  Open: whether 2022-shaped grinds recur at one-in-six or one-in-fourteen. No
  lane answers it; a leave-one-episode-out lane with 2022 deleted is the
  falsifier (`docs/HANDOFF_COMPOSITION.md` §7).

  Closed by EPISODE_SPEC: the hinge is not 2022. Splitting the 2012 lane's windows
  by the 2021-03 anti-beta trough (E4) partitions BTAL against the half-swap 10/10
  and 2/10; splitting by 2022's trough gives 7/7 and 5/13
  (`notes/episode-verdict.md`).
- *Which episodes does each sleeve component earn, and which does it pay for?*
  BTAL earns the TQQQ bears and pays for them when high beta leads: against a cash
  sleeve on the 2012 lane it is +5.3 / +2.3 / +5.7 / +9.1 pp shallower in E1, E2,
  E3 and E5 and −27.0 pp of return / −10.7 pp of drawdown in E4 alone, so its four
  bears earn +14.4 pp of return against −47.4 pp paid in E4, E6 and E7. On the
  winners' lane the 2022 grind's return is KMLM's (+16.5 pp against BTAL's +8.3)
  while its drawdown is BTAL's (+8.5 against +5.8), and the blend buys more of that
  drawdown than either arm alone (+11.0) — `results/episode_2012.md`,
  `results/episode_2021.md`, `notes/episode-verdict.md`.
