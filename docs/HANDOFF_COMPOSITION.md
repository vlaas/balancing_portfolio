# Handoff: rotation program closed → composition spec next

Written 2026-08 at the close of the rotation catalog. Audience: the fresh
conversation that will produce the composition spec. Repo state at handoff:
`vlaas/balancing_portfolio` @ `c25dfcf`, **720 tests green** on a fresh clone.
Protocol unchanged (Option A): re-clone, suite green, inspect code and committed
artefacts, recompute headline numbers independently, then write; decision-grade
numbers only from committed `runs.json` / `summary.json`.

## 1. The task

Write the **composition spec**: the multi-horizon monthly momentum score
(`1-3-6-12U`) as an alternative — or OR-combined — gate on the incumbent
TQQQ machine (VT + SMA-200 gate + BTAL-heavy sleeve), agreed as the next
increment after Stage 3. Composition of rotation machinery with gates/VT was
explicitly out of scope through all three rotation stages; this spec opens it.

**Done:** [COMPOSITION_SPEC.md](COMPOSITION_SPEC.md) → verdict
[comp-verdict.md](../notes/comp-verdict.md) — nothing adopted; the score gate is
a substitute at best, the protection on this machine is the trend filter, and
the 12-month sign beats `1-3-6-12U` here (§3.2's finding does not transplant).

## 2. Standing verdicts (authoritative files in repo `notes/` and `docs/`)

- **Incumbents unchanged:** B75K25 (robust-score leader), B75D25 (robustness /
  rank_worst pick), B50K50 (return variant) — all VT + SMA-200-gate + sleeve;
  cost-sensitivity verdict: plateau survives cbase and flat-20.
- **Rotation catalog closed** (`rot-verdict.md`, `rot2-verdict.md`,
  `rot3-verdict.md`): eight published points, three stages —
  **HAA-Simple REFERENCE**, GEM / GTAA-5 / ADM / HAA-Balanced / VAA-G4 /
  BAA-G12 / BAA-G4 all DOCUMENT-ONLY, no kills, no promotes. REFERENCE means
  benchmark-for-later-work, not live allocation.
- Earlier: SAFE_SWITCH zero promotions (anti-switcher pattern); REGIME_SPEC's
  VIX/VIX3M gate designed, with the known blind spot (term structure misses
  slow grinding bears like 2022; OR-gate with EWMA realized vol addresses it).

## 3. Findings that shape the composition spec

1. **Operator choice is settled: `1-3-6-12U` (unweighted mean of 1/3/6/12-month
   month-end TR), not Keller's `13612W`.** 14 matched arms across four families,
   both lanes each, and never once a holdout reversal. Engine spelling:
   `{"kind":"avg","months":[1,3,6,12]}` → indicator `MOMM1-3-6-12U`, already
   implemented and tested.
2. **The protection lives in the multi-horizon score itself.** HAA ablations:
   canary worth ~1 drawdown point; every plain-`12M` arm printed −33.7% where
   `1-3-6-12U` printed −19.9%. The composition hypothesis is precisely that
   this signal, read on QQQ, adds to (or substitutes for) the SMA-200 gate.
3. **Binary all-or-nothing regime flips are the program's cost driver.**
   Flat-20 CAGR cost ranking: VAA-G4 3.68, BAA-G4 3.07, BAA-G12 2.66 — the
   three binary-canary strategies — above every per-asset/per-slot mechanism;
   turnover orders identically. The composition should prefer the incumbent
   gate's shape (hysteresis / `w_off` clip precedent from REGIME_SPEC) and must
   carry a costed comparison; a new binary flip needs to beat these numbers,
   not the incumbent's.
4. **R2d (insurance-in-holdout diagnostic): 7 of 8 rotation points delivered a
   worse 2023-01→2026-08 holdout drawdown than their own no-timing null**; only
   GTAA-5 (per-asset trend) insured. Caveat: all drawdowns in that window are
   6–20%, a shallow episode. Set composition expectations accordingly and keep
   the diagnostic in the new spec's verdict skeleton (source: `kind=="test"`
   rows of committed `runs.json`, the K2 source — summary holdout blocks carry
   objectives only).
5. **Known bar defects, if bars are inherited:** R3a is unfireable on
   crisis-anchored windows (Stage-1 §2 of rot-verdict); its replacement R3a′
   (`rank_median ≤ ⌈N/2⌉`, both lanes) is blind to holdout collapse — BAA-G4
   passed it while dead last on `robust_score` (rot3 residual 4; fix if
   revisited: rank on `robust_score`). R2 was deliberately kept frozen across
   all three stages for comparability; amending bars is legitimate only in a
   pre-registration commit before runs.

## 4. Engine surface relevant to the composition (verify on fresh clone)

Exists and tested: `mom_monthly` / `mom_multi` (incl. `1-3-6-12U`) / `sma_gap`
indicators (monthly, own-calendar, carried forward, null warm-up); `rotation`
type with `filter {"kind":"none"}`, canary breadth, `best_of` `n ≥ 2` + `floor`
(floor requires explicit `n ≥ 2` — inert at n=1 since floor must be a member);
`Gate`/`AnyGate` with `w_off` clip; `VolTarget`; sweep runner with nested
numeric grids (e.g. `score.months`), R3a′ inputs (`rank_median`) in summaries.
**Gap the spec must design:** the VT machine's gate grammar conditions on
SMA/price or the `ts_regime` indicator; a momentum-score-sign (or threshold)
gate condition on an arbitrary indicator does not exist yet — inspect
`strategies/gate.py` + `spec.py` gate grammar on the fresh clone before
writing, and check whether OR-composition (AnyGate) covers the SMA∨momentum
form or needs extension.

## 5. Fixed conventions (do not re-derive)

Primary data `tests/data/2026-08-24-net15` (frozen; gross twin
`tests/data/2026-08-24`); decision runs net15. Cost map: ROTATION_SWEEP_SPEC §3
as amended by STAGE3 §3 (GLD 1, HYG 1, VGK 2, EWJ 2); only the original six
symbols are spread-measured, the rest tiered, bounded by flat-20 stress.
`cash_yield` 3% with the standing SGOV contingency (halving it closed 85–91% of
GTAA's `fb cash` edge — rot2 residual 2). House sweep settings: holdout
2023-01-01, sensitivity {6mo, 5y}, objective `calmar`, constraint DD ≥ −0.50,
contributions 10 000 + 500/mo. Incumbent-machine sweeps anchor at 2012-01-03.
Core files (`prices.py`, `simulate.py`, `indicators.py`, `stats.py`,
`results_json.py`) modified only under explicit spec authorization; frozen
artefacts never regenerated; golden tests never refreshed to pass.

## 6. Dual pre-flight rule (institutionalized; it has caught five defects)

Every window × every grid point: (a) first-value date of the widest score in
the lane — including **data-only** symbols (canary/hurdle; the VEA canary bound
BAA-G12's window) — against warm-up cash through a crisis; (b) max inception
over **traded** symbols including fallback-held ones, against the loader's
completeness assert. Composition on the incumbent's 2012 lanes is warm
everywhere for QQQ-based scores (QQQ data from 1999), so (a)/(b) are trivial
there — but any new lane or symbol re-triggers the rule.

## 7. Open threads deliberately not chosen now

- **Synthetic pre-inception history** — **done**: `docs/SYNTHETIC_HISTORY_SPEC.md`
  → `notes/syn-verdict.md`. Nothing adopted; the winners' coordinate
  (λ0.80 / σ0.20 / w_max 0.8 / SMA-200 gate) is feasible in both bears and
  ranks first of sixteen on both lanes, so **the program-wide caveat is
  downgraded from "tested on one era" to "the BTAL sleeve is untested before
  2011-09"**. Two flags to carry: the 2012-lane regime coordinate
  (σ0.30 / w_max 0.6) is **infeasible in the GFC on a cash sleeve** (−50.35 %,
  and past −50 % at every drag bracket), as is every ungated point; and R2 is
  answered for this machine — in the 2008–2011 holdout the gated winners'
  coordinate drew down −30.06 % against SPY's −51.94 %. Roots
  `tests/data/2026-08-24-syn{,-net15}`; a synthetic root is a falsifier, never
  a fitting lane.
- **The cash sleeve — how much of it should be BTAL** — `docs/CASH_SLEEVE_SPEC.md`
  → `notes/cash-verdict.md`. Fired by the bridge above: at the winners'
  coordinate BIL beat BTAL on Calmar on real 2012–2026 bars, so SAFE_SWAP §9's
  BIL follow-up came due. One pre-registered candidate — replace half a sleeve's
  BTAL with BIL — read on three lanes against the safe-blend bar, with the
  window floor as the clause that separates a complement from a trade. BIL is
  now in the golden battery on the 2026-08-24 root and `cash_yield` is demoted
  to uninvested residue.
- `MACRO_DATA_SPEC` (FRED availability-lag ingestion) — gates GTT/LAA; FRED
  files quarantined in `data/macro/`, loader must not read them.
- NTSX/RSSB/RSST/GDE statics — plain `fixed` bundle, runnable anytime, no
  engine work.
- Defensive-sleeve isolation (rot3 residual 6): `best3(…>BIL)` rode inside two
  DOCUMENT-ONLYs and was never swept on its own terms.
- Stage-1 residual 6: relative-only momentum printed −50.30% (worse than SPY's
  −47.16%) on the crisis window — unexplored follow-up note.
- BTAL-heavy-on regime variant: sharp falsifier remains leave-one-episode-out
  with 2022 deleted.

## 8. Verification expectations for the next conversation

Fresh clone at ≥ `c25dfcf`; suite ≥ 720 green; before writing the composition
spec, re-verify at least: the incumbent winners' numbers from `winners.json` /
their committed sweep artefacts on the 2012 lane (the comparison baseline the
composition must beat), and the `MOMM1-3-6-12U` indicator semantics against a
hand computation. The composition verdict's comparison set must include the
unmodified incumbents on identical lanes — the composition is adopted only if
it beats the machine it modifies, under the same frozen-bars discipline the
rotation program just spent three stages honoring.
