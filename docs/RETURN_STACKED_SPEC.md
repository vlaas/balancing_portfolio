# Specification: return-stacked statics — is one ticker a substitute for the machine?

Repo: `vlaas/balancing_portfolio` · baseline commit: `e5edd30` (handoff after the episode
verdict; 979 tests green on a fresh clone) · status: **proposed** · inputs:
`HANDOFF_EPISODE.md` §7.1 (the recommended increment), §3 (the gate ceiling, the E4
hinge), §5–§6 (conventions) · predecessors: `notes/episode-verdict.md`,
`notes/cash-verdict.md`, `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`.

## 1. Goal

Every spec so far has asked a question *inside* the machine — its gate, its sleeve, its
cadence, its coordinate. This one asks the question a reader outside the program asks
first: **is the machine worth running at all, against a single return-stacked ETF held
statically?** NTSX (90 % S&P 500 + 60 % Treasuries), RSSB (100 % global equity + 100 %
Treasuries), RSST (100 % US equity + 100 % managed-futures trend), GDE (90 % equity +
90 % gold) and their kin sell, in one ticker, most of what the machine builds by hand:
leverage, a diversifier, no decisions. The handoff has carried this item since
`HANDOFF_COMPOSITION` §7 as "runnable anytime, no engine work"; this spec runs it.

The shape is the plainest the grammar allows: `fixed` bundles of the statics on the lanes
their inceptions reach, the winners beside them as baselines, the per-episode panel, and
one pre-registered bar — a static is a *substitute* only if it beats the winner on the
2019 lane's score **and** does not deepen the window floor. The honest expectation,
stated in the handoff and confirmed by the pilot (§2.4), is that no static clears it:
a static has no gate, so 2022 is its floor, and 2022 is inside every three-year window
but one on the 2019 lane. The spec is written so that its *second* output survives that
expectation: the **simplicity premium** — how much CAGR the machine earns over the
best static at a matched floor — is read and recorded whatever the bar says (§10.2),
because that number, not the bar, is what a reader weighing the machine's operational
cost against a single ticker actually needs.

Three measured facts shaped the design (§2 has the tables):

- **Lane coverage is partitioned by inception, and the loader enforces it.** Only NTSX
  (2018-08-02) reaches the 2019 lane; NTSX and RPAR (2019-12-13) reach the 2021 lane;
  NTSI / NTSE / UPAR / GDE need a 2022-03-17 start, and RSBT / RSST / RSSB a
  2023-12-05 one — 2.7 years, full window only. A bundle whose start precedes any traded
  symbol's first bar dies in `load_prices`' completeness assert (§2.2).
- **The scoring statistic is the same on both sides of the grid/baseline line.** A
  categorical `weights` grid has no neighbours, so the runner's `robust_score` is
  `min(full, sensitivity median, holdout test)`; that three-term minimum, recomputed by
  hand from the committed `sweep_comp_2019` records, reproduces its `robust_score`
  **exactly** (0.9187 for `BTAL75+DBMF25`, 0.6280 for `BTAL`). A winner run as a
  baseline on identical windows is therefore scored by the same formula as the statics
  (§2.3); `rank_worst` is the one column that cannot cross the line, and §10 replaces it
  with a per-window win count.
- **The static's floor is 2022; the machine's is the anti-beta unwind.** On the 2019
  lane NTSX's deepest hole is E5 (−31.4 %, 2021-12-27 → 2022-10-14) and B75D25's is E4
  (−20.1 %, 2020-09-02 → 2021-03-08). The static wins every anti-beta episode (E4 +23.5
  / −8.9 against +9.0 / −20.1; E6, E7 likewise) and loses both bears (E3 −28.3 against
  −18.9; E5 −31.4 against −14.7). On the 2023-12-05 window, which contains neither bear,
  NTSX and RSSB print shallower floors than all three winners. Which lane a static is
  read on decides its floor, and the decision lane is the one with both bears inside.

## 2. What is already true at `e5edd30` (measured on this clone)

### 2.1 The statics on the 2026-08-24 pair (net15 unless stated; own full window)

| symbol | first bar (years to 2026-08-24) | CAGR net15 | CAGR gross | bias pp/yr | max DD (peak → trough) | 2020 | 2022 | 2025 | ρ_m TQQQ | ρ_m SPY |
|---|---|---|---|---|---|---|---|---|---|---|
| NTSX | 2018-08-02 (8.1) | 12.53 % | 12.73 % | 0.20 | **−31.43 %** (2021-12-27 → 2022-10-14) | +24.7 | **−26.0** | +18.6 | 0.93 | 0.98 |
| NTSI | 2021-05-20 (5.3) | 6.08 % | 6.51 % | 0.43 | −34.33 % (2021-09-03 → 2022-09-27) | — | −19.6 | +29.6 | 0.62 | 0.78 |
| NTSE | 2021-05-20 (5.3) | 5.19 % | 5.64 % | 0.45 | −43.24 % (2021-06-04 → 2022-10-24) | — | −26.7 | +35.6 | 0.63 | 0.65 |
| RPAR | 2019-12-13 (6.7) | 3.92 % | 4.31 % | 0.39 | −30.66 % (2021-11-09 → 2023-10-25) | +19.2 | −23.3 | +17.4 | 0.69 | 0.76 |
| UPAR | 2022-01-04 (4.6) | −1.09 % | −0.56 % | 0.53 | −39.63 % (2022-01-12 → 2023-10-25) | — | — | +23.2 | 0.65 | 0.77 |
| GDE | 2022-03-17 (4.4) | 28.84 % | 29.48 % | 0.65 | −32.01 % (2022-03-30 → 2022-10-14) | — | — | **+72.6** | 0.63 | 0.71 |
| RSBT | 2023-02-08 (3.5) | −0.41 % | −0.18 % | 0.23 | −23.87 % (2023-02-13 → 2025-05-14) | — | — | +9.8 | 0.14 | 0.26 |
| RSST | 2023-09-06 (3.0) | 19.41 % | 19.54 % | 0.13 | −30.81 % (2024-07-10 → 2025-04-08) | — | — | +19.7 | 0.75 | 0.80 |
| RSSB | 2023-12-05 (2.7) | 19.30 % | 19.64 % | 0.34 | **−16.34 %** (2024-12-06 → 2025-04-08) | — | — | +24.5 | 0.73 | 0.86 |

References on the same basis: SPY from 2019-05-08 15.75 % / −33.78 %, from 2020-12-18
14.91 % / −24.63 %; QQQ 20.73 % / −35.18 % and 16.19 % / −35.18 %; BIL 2.26 % and 2.66 %.
Correlations are of month-end returns over each static's own window. Withholding bias
(gross minus net15 CAGR) is 0.13–0.65 pp/yr — the statics distribute little, so the
net15 convention costs them less than it costs the sleeve arms (CASH §2.1: DBMF 0.97).
NTSX's month-end correlation with SPY is 0.98: it is levered SPY with a bond overlay,
and its 2022 (−26.0 against SPY's −18.2) is the overlay's bill.

### 2.2 Lane coverage — what the loader allows

`load_prices` full-joins the traded symbols, forward-fills, filters to `start`, then
asserts zero nulls on the traded set (`prices.py` line 100; pinned by
`test_null_traded_close_still_trips_the_assert`). A `fixed` bundle holding RSST at
`start: 2019-05-08` dies there with a bare `AssertionError` — verified on this clone.
So a lane's traded set must be alive at its start, which partitions the statics:

| lane start | statics alive | winners alive | windows (6 m / 3 y sens) | reads |
|---|---|---|---|---|
| **2019-05-08** (decision lane) | NTSX | B75D25 only (KMLM is 2020-12-18) | full, fit → 2023-12-29, test 2024-01-02 →, **9** sens | the bar |
| 2020-12-18 (winners' lane) | NTSX, RPAR | all three | full, fit → 2024-12-31, test 2025-01-02 → (noise, under 2 y), **6** sens | direction |
| 2022-03-17 | + NTSI, NTSE, UPAR, GDE | all three | full, fit → 2024-06-28, test 2024-07-01 → (2.15 y, no warning), **3** sens | reported |
| 2023-12-05 | + RSBT, RSST, RSSB | all three | full window only (2.7 y; no holdout ≥ 2 y with a fit ≥ 2 y) | reported |

Windows measured through `sweep.windows` on this clone; the 2019 lane's are exactly
`sweep_comp_2019`'s / `sweep_cash_2019`'s, the 2021 lane's exactly `sweep_comp_2021`'s.
The 2023 window cannot become a lane with a two-year holdout and three three-year
sensitivity windows before **2027-12** (RSSB's first bar + 4 years).

### 2.3 What the grammar already does, and what the statistic is

- `weights` is a categorical grid leaf: `{"type": "fixed", "weights": {"grid": [{"NTSX":
  1.0}, {"NTSX": 0.75, "BIL": 0.25}, …]}}` expands (`--dry-run`: `4 grid + 4 baselines x
  12 windows = 96 runs` on the 2019 lane) with `params.weights` rendered as the
  sorted-key JSON string (`{"BIL":0.25,"NTSX":0.75}`), auto-labels `NTSX100`,
  `NTSX75/BIL25`, `NTSX62.5/BIL37.5` (slug `ntsx62-5-bil37-5`), `NTSX50/BIL50`.
- `type` cannot be gridded (`REQUIRED_KEYS.get(dict)` would raise), so a `vol_target`
  winner and a `fixed` static cannot share a grid without runner work. The winner runs
  as a **baseline** on the same windows.
- On a categorical-only grid `neighbours()` returns nothing, `neighbour_min` is `null`,
  and `robust_score = min(full.objective, sensitivity.objective.median, holdout.test)`
  (`sweep.py` lines 586–592). Call that three-term minimum **score₃**. Recomputed by hand
  from `results/sweep_comp_2019/summary.json` — a lane whose only grid dimension was the
  categorical gate — it equals every grid point's committed `robust_score` to eight
  decimals (`BTAL75+DBMF25` 0.91868785, `BTAL` 0.62795483); on `sweep_cash_2019`, which
  grids σ, it does not (0.9406 against 0.8734 for `BIL50+BTAL50`), which is CASH erratum
  5 seen from the other side. A baseline block carries `full`, `holdout` and
  `sensitivity`, so its score₃ is computable and is the same statistic as the grid's.
- `rank_worst` is a rank among *feasible grid strategies* per window; a baseline never
  ranks. §10 uses the per-window Calmar win count from `runs.json` instead.
- `episode_report.py bundle` runs `fixed` entries (`_keep` never drops them); its
  `--baseline` needs a `/SYM ` label pattern, so a static panel reads the raw
  return / in-window-drawdown table, not the marginal one.
- No cost calibration exists for any of the nine tickers (`Round-Trip_Trading_Costs.md`
  covers six symbols); the blend map's `*` 6 bp applies. A single-ticker static trades
  only its contributions (turnover 0.083/yr for `NTSX100` against 1.655 for B75D25), so
  the map barely reaches it: flat-20 moves `NTSX100`'s CAGR by **0.02 pp** and B75D25's
  by **0.61 pp** (§2.4). Cost is not what decides this spec.

### 2.4 The pilot in one table (full windows; §11 has the brackets and the panels)

`tests/data/2026-08-24-net15`, blend cost map + `BIL 0.5`, `cash_yield` 3 %, 10 000 +
500 / month, monthly rebalancing. Calmar · CAGR · max DD; the test column is the lane's
holdout window run as its own bundle (start 2024-01-02, the snapped test start).

**2019 lane, 2019-05-08 →:**

| strategy | Calmar · CAGR · max DD | test (2024-01-02 →) | 2020 | 2022 | 2025 |
|---|---|---|---|---|---|
| `NTSX100` | 0.4172 · 13.11 · **−31.43** | 1.1036 | +24.6 | **−26.0** | +18.6 |
| `NTSX75/BIL25` | 0.4374 · 10.58 · −24.19 | 1.1812 | +18.6 | −19.5 | +14.7 |
| `NTSX62.5/BIL37.5` | 0.4538 · 9.25 · **−20.39** | 1.2368 | +15.5 | −16.2 | +12.8 |
| `NTSX50/BIL50` | 0.4802 · 7.91 · −16.46 | 1.3319 | +12.5 | −12.8 | +10.9 |
| **B75D25** (the incumbent) | **0.9362 · 18.83 · −20.11** | **0.9187** | +19.1 | **−7.9** | +18.8 |
| `VT TQQQ/BIL50+BTAL50` (σ0.20 flag) | 0.9765 · 18.95 · −19.40 | 1.0306 | +22.7 | −14.7 | +21.1 |
| `TQQQ50/BTAL50 gate` | 0.5577 · 21.03 · −37.72 | 0.7872 | +43.6 | −27.7 | +5.7 |
| SPY | 0.4657 · 15.68 · −33.67 | 1.1166 | +17.8 | −18.2 | +17.5 |

B75D25, `BIL50+BTAL50` and SPY reproduce `sweep_comp_2019` / `sweep_cash_2019` to eight
decimals (0.93621129 / 0.18830107 / −0.20113095; 0.97652213; 0.46572974), and B75D25's
test-window Calmar reproduces its committed holdout test **0.91868785** — which is also
its committed `robust_score`, the sens median (0.9200) being the only other candidate.
The NTSX62.5 point is the deleveraging surface's *matched-floor* point, chosen from the
pilot's linear interpolation between 0.75 (−24.19) and 0.50 (−16.46); it lands 0.28 pp
deeper than the incumbent at **9.6 pp/yr less CAGR**. Every static beats B75D25 on the
holdout test window (1.10–1.33 against 0.92) — the 2024–26 window is a bull market with
the tariff dip, where a bond-hedged static is shallower — so clause (ii) of the bar
passes for all four and clauses (i) and (iii) are load-bearing. `NTSX100` cannot
outscore SPY on this lane: its full Calmar 0.4172 bounds its score₃ from above, and
SPY's committed score₃ is 0.4205.

**2021 lane, 2020-12-18 →** (test 2025-01-02 →, noise by the runner's warning):

| strategy | Calmar · CAGR · max DD | test | 2021 | 2022 | 2025 |
|---|---|---|---|---|---|
| `NTSX100` | 0.3270 · 10.27 · −31.42 | 1.0284 | +22.0 | −26.0 | +18.6 |
| `RPAR100` | **0.0504 · 1.55** · −30.66 | 1.7841 | +7.2 | −23.3 | +17.4 |
| `NTSX50/RPAR50` | 0.1950 · 5.92 · −30.34 | 1.3576 | +14.4 | −24.5 | +18.1 |
| `NTSX75/BIL25` | 0.3543 · 8.57 · −24.18 | 1.0906 | +16.2 | −19.5 | +14.7 |
| `NTSX50/BIL50` | 0.4093 · 6.73 · −16.44 | 1.2283 | +10.6 | −12.8 | +10.9 |
| B75K25 | 0.8529 · 16.26 · −19.06 | 0.8470 | +25.9 | −6.2 | +16.5 |
| B75D25 | 0.8574 · 16.35 · −19.07 | 0.8825 | +26.5 | −7.3 | +18.7 |
| B50K50 | 0.8849 · 18.49 · −20.90 | 1.1674 | +29.6 | −4.7 | +17.9 |
| SPY | **0.6059** · 14.82 · −24.45 | 0.9983 | +28.2 | −18.2 | +17.4 |

The winners reproduce `sweep_comp_2021` (full 0.8529 / 0.8574 / 0.8849, test 0.8470 /
0.8825 / 1.1674). **Plain SPY beats every static on this lane on Calmar, CAGR and
drawdown**: a levered 60/40 bought at the end of 2020 paid for its bond leg through
2022–23 and never recovered the difference. Risk parity (RPAR) compounds at 1.55 %.

**2022 lane, 2022-03-17 →** (test 2024-07-01 →, 2.15 y): `NTSX100` 0.4092 · 10.73 ·
−26.23 (test 0.9968); `NTSI100` 0.3366 · 9.15 · −27.19 (1.2831); `NTSE100` 0.3587 ·
10.95 · −30.52 (1.4141); `RPAR100` 0.0592 · 1.53 · −25.86 (0.9572); `UPAR100` 0.0113 ·
0.41 · −36.26 (0.8344); **`GDE100` 0.9007 · 28.81 · −31.99 (2.0695)**; `NTSX50/GDE50`
0.6815 · 19.79 · −29.04 (1.9145); `NTSX34/NTSI33/NTSE33` 0.3947 · 10.54 · −26.69
(1.3785); B75K25 1.1035 · 19.48 · −17.65 (**0.4699**); B75D25 1.0940 · 20.05 · −18.32
(**0.4647**); B50K50 0.9891 · 20.64 · −20.87 (**0.5256**); SPY 0.6642 · 14.47 · −21.79
(0.9646). The winners' two-year test window is E6-bound: their test Calmars are the
lowest numbers in the column. GDE is gold's 2022–26 run in one ticker: +33.3 / +43.2 /
+72.5 in 2023 / 2024 / 2025.

**2023 window, 2023-12-05 →** (full only; `results/rs_points_2023.json` will hold it):

| strategy | Calmar · CAGR · max DD (peak → trough) | 2024 | 2025 | 2026 → |
|---|---|---|---|---|
| `RSST100` | 0.7352 · 22.64 · **−30.80** (2024-07-10 → 2025-04-08, E6's own dates) | +18.3 | +19.7 | +17.8 |
| `RSSB100` | **1.1800** · 19.27 · **−16.33** (2024-12-06 → 2025-04-08) | +10.3 | +24.5 | +10.3 |
| `RSBT100` | 0.2670 · 5.07 · −18.98 | −2.9 | +9.8 | +5.3 |
| `GDE100` | **2.2090 · 50.04** · −22.65 (2026-01-28 → 2026-03-26, inside E7) | +43.2 | +72.5 | +14.9 |
| `NTSX100` | 1.1689 · 19.74 · −16.89 | +19.9 | +18.6 | +9.7 |
| `UPAR100` | 0.7948 · 12.91 · −16.25 | −2.7 | +23.2 | +8.8 |
| `RPAR100` | 0.9128 · 10.41 · **−11.40** | −0.3 | +17.4 | +6.7 |
| `RSSB50/RSST50` | 0.9417 · 21.13 · −22.44 | +14.5 | +22.3 | +14.0 |
| `RSSB34/RSST33/RSBT33` | 0.7891 · 15.71 · −19.91 | +8.5 | +18.2 | +11.1 |
| B75K25 | 1.0765 · 18.92 · −17.57 (2024-07-10 → 2025-04-08) | +16.9 | +16.3 | +5.8 |
| B75D25 | 1.0968 · 19.93 · −18.17 (same) | +18.4 | +18.5 | +5.0 |
| B50K50 | 1.0045 · 20.85 · −20.76 (same) | +15.3 | +17.7 | +10.4 |
| SPY | 1.1767 · 21.83 · −18.55 | +24.3 | +17.4 | +12.3 |

On a window with no TQQQ bear in it, **RSSB, NTSX and SPY all beat the three winners on
Calmar with shallower floors**; RSST — the trend-stacked one — is the deepest thing in
the panel, because E6 (the April 2025 whipsaw) is exactly where trend loses. These are
2.7-year numbers with one episode of one kind in them; §10.3 says what they can and
cannot decide.

### 2.5 The per-episode panel (`episode_report.py bundle`, net15, same bundles)

Episode return % / max drawdown % inside the window (EPISODE_SPEC §3's frozen table; a
lane starting inside a window reads it from its first bar):

**2019 lane:**

| strategy | E2 | E3 COVID | E4 anti-beta | E5 2022 | E6 tariff | E7 |
|---|---|---|---|---|---|---|
| `NTSX100` | +13.3 / −4.1 | −0.2 / **−28.3** | **+23.5 / −8.9** | −14.3 / **−31.4** | **+21.3 / −16.9** | +8.4 / −9.2 |
| `NTSX75/BIL25` | +10.2 / −3.1 | +0.1 / −21.6 | +17.3 / −6.7 | −9.7 / −24.2 | +17.1 / −12.6 | +7.1 / −6.8 |
| `NTSX62.5/BIL37.5` | +8.6 / −2.6 | +0.2 / −18.2 | +14.3 / −5.6 | −7.4 / −20.4 | +15.0 / −10.5 | +6.3 / −5.6 |
| `NTSX50/BIL50` | +7.1 / −2.1 | +0.3 / −14.6 | +11.3 / −4.5 | −5.2 / −16.5 | +12.9 / −8.4 | +5.6 / −4.4 |
| B75D25 | +23.3 / −8.9 | −1.4 / **−18.9** | +9.0 / **−20.1** | **+5.3 / −14.7** | +1.3 / −18.4 | −1.0 / −16.4 |
| `BIL50+BTAL50` machine | +21.0 / −9.5 | −1.4 / −19.4 | +13.5 / −18.2 | +1.1 / −19.3 | +5.7 / −17.4 | −0.2 / −17.0 |
| SPY | +11.9 / −5.9 | −5.5 / −33.7 | +28.0 / −9.4 | −3.5 / −24.4 | +20.6 / −18.7 | +11.8 / −8.9 |

The static loses the two bears by 9.4 pp (E3) and 16.7 pp (E5) of drawdown and 19.6 pp
of E5 return, and wins the three anti-beta episodes by 11.2 (E4), 1.5 (E6) and 7.2 (E7)
pp of drawdown and 14.5 / 20.0 / 9.4 pp of return. This is the BTAL-versus-cash pattern
of the episode verdict seen from outside the machine: the machine *is* its anti-beta
sleeve in E4, E6 and E7, and the static is what a reader who never bought insurance
holds. Deleveraging with BIL scales every cell toward zero and changes no sign.

**2021 lane** (E1–E3 empty; E4 read from 2020-12-18): `RPAR100` +6.7 / −6.4 · −19.3 /
−29.6 · +11.9 / −11.4 · +5.9 / −8.1; `NTSX50/RPAR50` +13.0 / −5.4 · −16.7 / −30.2 · +16.7
/ −12.4 · +7.3 / −8.2; `NTSX100` +19.5 / −5.6 · −14.3 / −31.4 · +21.3 / −16.9 · +8.4 /
−9.2; winners E4 −19.1 / −19.1 / −16.1, E5 −13.5 / −14.3 / −15.1, E6 −17.7 / −18.3 /
−20.9, E7 −16.2 / −16.4 / −14.9 (reproducing `results/episode_2021.md`). Every static is
deeper than every winner in E5 and shallower than every winner in E4, E6 and E7;
`NTSX50/BIL50` (−16.4) is the only static within 2 pp of a winner in E5.

**2023 window** (E6, E7 only): `RSST100` +2.5 / **−30.8** · +18.7 / −11.7; `RSSB100`
+22.5 / −16.3 · +9.3 / −11.6; `RSBT100` −7.7 / −19.0 · +6.4 / −6.1; `GDE100` +72.8 /
−16.4 · +23.6 / **−22.7**; `NTSX100` +21.3 / −16.9 · +8.4 / −9.2; `UPAR100` +14.3 /
−16.2 · +8.3 / −11.2; `RPAR100` +11.9 / −11.4 · +5.9 / −8.1; `RSSB50/RSST50` +12.3 /
−22.4 · +13.9 / −11.2; winners +0.2 / −17.6 · −0.5 / −16.2, +1.1 / −18.2 · −1.1 / −16.4,
+0.3 / −20.8 · +4.0 / −14.9. In the tariff episode the bond-stacked statics (RSSB, NTSX,
UPAR, RPAR) are shallower than every winner and earn +12 to +23 pp where the winners
earn ~0; the trend-stacked one is deeper than every winner by 10 pp. GDE's only deep
hole is E7 — gold's 2026 correction — where it is the deepest thing on the panel.

## 3. The question, and what can be adopted — pre-registered

**Q: is a static return-stacked ETF, or a static blend of them, a substitute for the
machine — one ticker, no gate, no volatility targeting?** The candidates are the grid
points of §4, all `fixed`, all monthly-rebalanced through the ordinary engine. The only
thing this spec can adopt is a *static alternative* entry in the winners file (§10.1);
it cannot move a winner, a coordinate, a sleeve or the gate. A static that wins on
Calmar at a deeper floor is a trade and is handed back as the cash verdict handed back
the half-swap; a static that wins on the 2023 window alone is a 2.7-year number and is
written into the ledger's `Open:` line with the date it can be re-read (§10.3).

No static is proposed as a *sleeve* member here; that would make it a sleeve candidate
under CLAUDE.md §6's episode rule and belongs to a different spec (§13). Nothing about
BTAL, KMLM or DBMF is asked.

The deleveraging surface (`NTSX` × `BIL` at 100 / 75 / 62.5 / 50 % NTSX) is not a
search for a better static; it exists so that the floor clause gets a fair answer and
so that §10.2's premium is read at a matched floor rather than at the static's own.
The 62.5 point is pre-registered from the pilot's interpolation; if no grid point's
window floor lands within 1 pp of the incumbent's, the premium is interpolated linearly
between the two that bracket it and the verdict says so (§9 step 2).

## 4. Lanes

All on `tests/data/2026-08-24-net15`, objective Calmar, constraint max drawdown
≥ −50 %, 10 000 + 500 / month, blend cost map + `BIL 0.5` (the nine statics at `*` 6 bp),
`cash_yield` 0.03. Windows copied from the lane each one extends so that every incumbent
reproduces its committed number.

### 4.1 `specs/sweep_rs_2019.json` — the decision lane (4 points)

Windows as `sweep_comp_2019` (start 2019-05-08, holdout 2024-01-01, sensitivity 6 m / 3 y
→ 12 windows). Template `{"type": "fixed", "weights": {"grid": [{"NTSX": 1.0}, {"NTSX":
0.75, "BIL": 0.25}, {"NTSX": 0.625, "BIL": 0.375}, {"NTSX": 0.5, "BIL": 0.5}]}}`.
Baselines, in order: B75D25 (`vol_target`, `BTAL75+DBMF25`, λ0.80, σ0.20, w_max 0.8,
gate SMA-200), `VT TQQQ/BIL50+BTAL50` at the same coordinate (the σ0.20 flag's
reference), gated `TQQQ50/BTAL50`, SPY. Anchors: B75D25's baseline block reproduces
full 0.93621129 / 0.18830107 / −0.20113095 and test 0.91868785, and its score₃ equals
its committed `robust_score` 0.91868785; `BIL50+BTAL50` 0.97652213; SPY 0.46572974.

### 4.2 `specs/sweep_rs_2021.json` — the winners' lane (5 points)

Windows as `sweep_comp_2021` (start 2020-12-18, holdout 2025-01-01, sensitivity 6 m / 3 y
→ 9 windows; the runner's "test window shorter than 2 years" warning applies and is
quoted). Grid: `NTSX`, `RPAR`, `NTSX50/RPAR50`, `NTSX75/BIL25`, `NTSX50/BIL50`.
Baselines: the three winners, SPY. Anchors: the winners' full Calmars 0.8529 / 0.8574 /
0.8849 and tests 0.8470 / 0.8825 / 1.1674; their score₃ equal their committed
`robust_score` (that lane had no numeric dimension either).

### 4.3 `specs/sweep_rs_2022.json` — the 2022 cohort (8 points, 3 windows)

Start 2022-03-17 (GDE's first bar), holdout 2024-07-01 (test 2.15 y — no warning; fit
2.3 y), sensitivity 6 m / 3 y → 6 windows of which **3** sens (2022-03-17, 2022-09-19,
2023-03-17 starts). Grid: `NTSX`, `NTSI`, `NTSE`, `RPAR`, `UPAR`, `GDE`, `NTSX50/GDE50`,
`NTSX34/NTSI33/NTSE33` (a global 90/60). Baselines: the three winners, SPY. Three
windows rank nothing; this lane is run so that the 2022 cohort has the same columns as
the others and is read under §10.3 only.

### 4.4 `specs/rs_points_2023.json` — the 2023 panel (9 statics + 3 winners + SPY)

Start 2023-12-05, a bundle, `--json`. Grid-equivalent: `RSST`, `RSSB`, `RSBT`, `GDE`,
`NTSX`, `UPAR`, `RPAR`, `RSSB50/RSST50`, `RSSB34/RSST33/RSBT33`; winners; SPY. Full
window only, by construction (§2.2).

### 4.5 Brackets — `_tr` and `_c20` twins of §4.1

§4.1 rerun on the gross root `tests/data/2026-08-24` (`--out results/sweep_rs_2019_tr`)
and with `cost_bps: {"*": 20}` on net15 (`specs/sweep_rs_2019_c20.json` →
`results/sweep_rs_2019_c20`). The other lanes are direction lanes and get no brackets.

### 4.6 Panels — `episode_report.py bundle`

Run on three bundles: `specs/rs_points_2019.json` (the §4.1 grid and baselines as a
bundle, start 2019-05-08), `specs/rs_points_2021.json` (§4.2 likewise) and §4.4 —
`results/episode_rs_2019.md`, `episode_rs_2021.md`, `episode_rs_2023.md`. No
`--baseline`. Plus `episode_report.py partition results/sweep_rs_2019/runs.json --pair
"<B75D25 label>" "NTSX100"` (and the same pair against `NTSX62.5/BIL37.5`) →
`results/episode_rs_partitions.md`.

### 4.7 Size

`--dry-run`: **96** (4 + 4 × 12), **81** (5 + 4 × 9), **72** (8 + 4 × 6); brackets ×2 of
the first; one bundle of 13; three episode bundles of 8 / 9 / 13. About 480 runs, well
under five minutes. Dual pre-flight (handoff §6): every traded symbol is alive at its
lane's start (§2.2's table, measured); no indicator wider than SMA-200 on QQQ; the
loader's completeness assert covers each lane's traded set.

## 5. No engine work

`prices.py`, `simulate.py`, `indicators.py`, `stats.py`, `results_json.py`,
`strategy.py`, `strategies/*`, `spec.py`, `sweep.py`, `episode_report.py`:
**untouched**. `SCHEMA_VERSION` stays 4. Everything in §4 was run through `main.py`,
`sweep.py --dry-run` and `episode_report.py` unmodified in the pilot.

## 6. Tests — new `tests/test_return_stacked.py`

Cite as "RETURN_STACKED_SPEC D·" (T, N, R, C, S, B, A are taken; K, Q and G appear as
parameter names in earlier specs).

**D1 — Inceptions and lane partition.** The nine statics' first bars on both 2026-08-24
roots (identical on both) are exactly §2.1's; the net15 README's jump counts for them
are 34 / 23 / 22 / 27 / 18 / 8 / 2 / 3 / 3 (NTSX … RSSB in §2.1's order); `load_prices`
on `["NTSX", "BIL", "SPY", "TQQQ", "BTAL", "DBMF"]` at 2019-05-08 succeeds and on the same
set plus `RPAR` at 2019-05-08 raises `AssertionError`. (The assert itself is already
pinned in `test_prices.py`; this pins the fact §4 rests on.)

**D2 — score₃ is the runner's statistic on a categorical grid.** (a) `build_summary`
on a `fixed` `weights` grid of two dicts with a holdout and three sensitivity windows
(the `t5_spec` / `stats_of` fixtures) gives every point `neighbourhood == {"neighbour_min":
None, "neighbour_mean": None, "edge": False}` and `robust_score == min(full, median(sens),
test)`; `params.weights` is the sorted-key JSON string. (b) On the committed
`results/sweep_comp_2019/summary.json` and `sweep_comp_2021/summary.json`, `min(full.
objective, sensitivity.objective.median, holdout.test)` equals `robust_score` for every
grid strategy to 1e-8, and `neighbourhood.neighbour_min` is `null` throughout. (c) On
`sweep_cash_2019/summary.json` the identity fails for at least one point — the σ grid
gives it a neighbour — so the pin is about grid shape, not a tautology.

**D3 — Anchors through the new specs.** `--dry-run` counts 96 / 81 / 72 (§4.7; ships in
the pre-registration commit beside the specs, CASH erratum 4); through `run_bundle` on
net15, §4.1's baselines on the full window → 0.93621129 / 0.18830107 / −0.20113095,
0.97652213, 0.46572974, and on 2024-01-02 → B75D25 0.91868785; §4.2's winners on the
full window → 0.8529 / 0.8574 / 0.8849 to 4 dp.

**D4 — Pilot pins (§2.4–§2.5).** `NTSX100` on 2019-05-08 → : 0.41724492 / 0.13113533 /
−0.31428863 with the trough on 2022-10-14; `NTSX62.5/BIL37.5` max DD −0.20387913;
`NTSX100`'s episode cells E3 −28.3, E4 +23.5 / −8.9, E5 −14.3 / −31.4, E6 +21.3 / −16.9
to 0.1; on 2023-12-05 → `RSSB100` −0.16334022 and `RSST100`'s drawdown dated
2024-07-10 → 2025-04-08, `GDE100`'s 2026-01-28 → 2026-03-26; flat-20 moves `NTSX100`'s
full CAGR by less than 0.05 pp and B75D25's by more than 0.5 pp.

**D5 — Grammar.** `{"NTSX": 0.625, "BIL": 0.375}` builds, labels `NTSX62.5/BIL37.5`,
slugs `ntsx62-5-bil37-5`, normalises and rebuilds to the same spec; a `weights` grid
containing it expands and renders `{"BIL":0.375,"NTSX":0.625}` in `params.weights`.

## 7. Docs

- `docs/WINNING_STRATEGIES_CASH_SLEEVE.md`: a new ledger section, **"Alternatives to the
  machine — what has been asked and answered"**, with this spec's entry (§10.4) and its
  `Open:` line; one standing flag — the simplicity premium (§10.2) — whatever the bar
  says. If §10.1 adopts, the static enters the winners table as a fourth row flagged
  "static", with its committed numbers.
- `docs/HANDOFF_EPISODE.md` §7.1: a pointer to this spec and its verdict (living doc).
- No change to `CLAUDE.md`, `COST_MODEL_SPEC.md` (frozen; the nine tickers' cost note is
  §2.3 of this spec) or `Round-Trip_Trading_Costs.md`.

## 8. Run protocol

```
uv run pytest                                                                          # D1–D5 green
uv run sweep.py specs/sweep_rs_2019.json     --data tests/data/2026-08-24-net15 --out results/sweep_rs_2019
uv run sweep.py specs/sweep_rs_2019.json     --data tests/data/2026-08-24       --out results/sweep_rs_2019_tr
uv run sweep.py specs/sweep_rs_2019_c20.json --data tests/data/2026-08-24-net15 --out results/sweep_rs_2019_c20
uv run sweep.py specs/sweep_rs_2021.json     --data tests/data/2026-08-24-net15 --out results/sweep_rs_2021
uv run sweep.py specs/sweep_rs_2022.json     --data tests/data/2026-08-24-net15 --out results/sweep_rs_2022
uv run main.py --spec specs/rs_points_2023.json --data tests/data/2026-08-24-net15 --json results/rs_points_2023.json --no-charts --quiet
uv run episode_report.py bundle specs/rs_points_2019.json --data tests/data/2026-08-24-net15 > results/episode_rs_2019.md
uv run episode_report.py bundle specs/rs_points_2021.json --data tests/data/2026-08-24-net15 > results/episode_rs_2021.md
uv run episode_report.py bundle specs/rs_points_2023.json --data tests/data/2026-08-24-net15 > results/episode_rs_2023.md
uv run episode_report.py partition results/sweep_rs_2019/runs.json \
    --pair "VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200" "NTSX100" \
    --pair "VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200" "NTSX62.5/BIL37.5" > results/episode_rs_partitions.md
```

Commit order (handoff §6.7): (1) `tests/test_return_stacked.py` D1, D2, D4, D5 and D3's
`run_bundle` legs; (2) the **pre-registration commit** — the four sweep specs, the four
bundle specs, D3's `--dry-run` legs, §3, §10, §11, nothing run; (3) artefacts; (4) the
verdict, `notes/rs-verdict.md`. Verification after (4): fresh clone, suite, `git diff
--stat <prereg> <verdict> -- specs/` empty, every headline number recomputed from
`summary.json` / `runs.json` / the bundles. Confirm every §4 anchor before reading a
single new number.

## 9. Read protocol

Steps in order; every number from `summary.json`, `runs.json`, the bundles or the
episode reports.

0. **Anchors** (§4.1–§4.2) reproduce; the 2021 lane's holdout warning is quoted; the
   2022 lane's absence of one is noted.
1. **The decision lane, §4.1.** For each of the four statics: `robust_score`, full
   Calmar, CAGR, max drawdown, holdout test, sensitivity median and min, and the
   **window floor** (minimum over the 9 sensitivity windows of `max_drawdown`, from
   `runs.json`); for B75D25: score₃ by hand and the same columns. Then the **win
   count**: the number of sensitivity windows in which the static's Calmar exceeds
   B75D25's, and which windows they are.
2. **The matched floor, §10.2.** Along the deleveraging surface, the grid point whose
   window floor is within 1 pp of B75D25's (either side); if none is, the linear
   interpolation in NTSX fraction between the two grid points whose floors bracket
   B75D25's, applied to their full CAGRs; that point's full CAGR; the **simplicity
   premium** = B75D25's full CAGR minus it.
3. **Brackets, §4.5.** Steps 1–2 reread on `_tr` and `_c20`: each clause of §10.1 keeps
   its sign or not; how much score₃ and `robust_score` move on each.
4. **The winners' lane, §4.2.** Step 1's columns for the five statics against each of
   the three winners and SPY; read for direction.
5. **The 2022 cohort, §4.3.** Step 1's columns against the three winners; three windows,
   read under §10.3 only; GDE's and `NTSX50/GDE50`'s standing named explicitly.
6. **The 2023 panel, §4.4.** Full Calmar, CAGR, max drawdown (dated) for all thirteen;
   which statics beat all three winners on Calmar with a shallower floor; the `Open:`
   line's content.
7. **Episodes, §4.6.** The three tables; for the decision lane, the partition by E3's,
   E4's and E5's troughs for both pairs. Which episodes the static wins and loses, on
   in-window drawdown and on episode return, against B75D25 (2019) and against each
   winner (2021).
8. **Exposure control** (SAFE_SWAP §6.5, mandatory in spirit): the statics hold no
   TQQQ, so the column is `exposure.NTSX.avg` etc. — printed to show the deleveraging
   points hold what their labels say (0.50–1.00 of NTSX, the rest BIL) and nothing else.
9. **The decision, §10.**

## 10. Decision rule — frozen at the pre-registration commit

10.1 **The substitute bar (2019 lane).** A static S is a *substitute for the machine*
only if, on `results/sweep_rs_2019`: (i) S's `robust_score` exceeds B75D25's score₃ by
more than 0.02 (score₃ = `min(full.objective, sensitivity.objective.median,
holdout.test)` from the baseline block; it reproduces 0.91868785 by D3); (ii) S's
holdout test Calmar is not below B75D25's; (iii) S's **window floor is not deeper** than
B75D25's (minimum sensitivity-window `max_drawdown` ≥ the incumbent's); (iv) S wins
Calmar against B75D25 in **at least 5 of the 9** sensitivity windows — the place of the
safe-blend bar's `rank_worst` clause, which cannot be read across the grid/baseline
line; (v) clauses (i)–(iii) keep their sign on both brackets. Clause (iii) is the cash
verdict's clause (iv) and carries the same meaning: a static that buys Calmar at a
deeper floor is a trade, not a substitute. If S clears all five it enters the winners
file as a fourth row flagged "static", and the handoff's next item is a spec that asks
whether S can be the machine's risk asset.

10.2 **The matched-floor read — executed whatever 10.1 says.** Along §4.1's
deleveraging surface, the grid point whose window floor is within 1 pp of B75D25's, or
failing that the linear interpolation between the two bracketing points (§9 step 2),
and its full CAGR; the **simplicity premium** = B75D25's full CAGR minus that CAGR, in
pp/yr, with the NTSX fraction it sits at. Written into the winners file as a standing flag:
*"A static NTSX / BIL blend deleveraged to the machine's window floor on the 2019 lane
earns X pp/yr less than B75D25 (RETURN_STACKED_SPEC, `notes/rs-verdict.md`)."* This is
the number a reader weighing the machine's operational cost against one ticker needs,
and it does not depend on the bar.

10.3 **What the other lanes can decide: nothing.** The 2021 lane is read for direction
(its holdout is noise). The 2022 lane has three sensitivity windows. The 2023 panel has
one episode of one kind in it. A static that beats the winners on any of them while
failing 10.1 is **reported, not promoted** — as era-dependence if on the 2021 or 2022
lane, as an `Open:` line if on the 2023 panel, with the date the panel becomes a lane:
*"RSSB / RSSB50+RSST50 not decidable before 2027-12."* A static that beats the winners
on a short lane on Calmar *and* floor is named in the `Open:` line; one that beats them
on Calmar at a deeper floor is not (it is the trade 10.1(iii) refuses).

10.4 **Outputs.** (a) Adoption per 10.1, or (b) — the pre-registered expectation — the
ledger entry: *"Is a static return-stacked ETF a substitute for the machine? No, on the
lanes that contain a TQQQ bear: on the 2019 lane NTSX's floor is 2022 (−31.4 %) against
the machine's anti-beta unwind (−20.1 %), and at a matched floor the static earns X
pp/yr less (10.2). The static wins every anti-beta episode (E4, E6, E7) and loses both
bears (E3, E5); on a window without a bear (2023-12 →) RSSB and NTSX beat the winners
on Calmar with shallower floors, which is the machine's insurance premium seen in a
year it was not needed."* Either way: the 2023 `Open:` line, and the simplicity-premium
flag. Verdict: `notes/rs-verdict.md`, steps 0–9 plus residuals.

10.5 **Episode reads are recorded, not scored.** A static is not a sleeve candidate, so
CLAUDE.md §6's E4 rule does not bind it; the verdict records which episodes each static
wins and loses against the incumbent on both measures (§9 step 7) so that a future
risk-asset spec inherits the table.

## 11. Pilot measurements — what to expect, and what would falsify it

Every number in §2 is from `main.py` or `episode_report.py` on the committed roots
through the unmodified grammar, full windows and the snapped holdout windows only; no
sensitivity windows, no ranks, no floors. The episode tables slice the same full-window
curves and are therefore pins (D4), not predictions. Expectations, not findings:

**2019 brackets, full window** (Calmar · CAGR): gross root — `NTSX100` 0.4251 · 13.32,
`NTSX75/BIL25` 0.4495 · 10.83, `NTSX62.5/BIL37.5` 0.4700 · 9.54, `NTSX50/BIL50` 0.5019 ·
8.21, B75D25 0.9529 · 19.13, `BIL50+BTAL50` 0.9894 · 19.20, SPY 0.4734 · 15.94; flat-20 —
0.4164 · 13.09, 0.4349 · 10.53, 0.4506 · 9.21, 0.4761 · 7.85, **0.8919 · 18.22**, 0.9385
· 18.31, 0.4698 · 15.68. Turnover / fee drag on net15: `NTSX100` 0.083 / 0.060 %/yr,
B75D25 1.655 / 0.816 %/yr.

Predictions, each a falsifiable line for the verdict:

1. **10.1 fails for every static on clause (i) by more than 0.40.** Every static's
   `robust_score` is at most its full Calmar (0.4172–0.4802), so the new information is
   the sensitivity median; B75D25's score₃ is 0.9187. Falsified if any static's
   `robust_score` exceeds 0.52.
2. **Clause (iii) passes for exactly one grid point.** `NTSX100`'s window floor is deeper
   than −30 %; `NTSX75/BIL25`'s deeper than −23 %; `NTSX62.5/BIL37.5`'s deeper than
   B75D25's (−20.11 %) by less than 1 pp; `NTSX50/BIL50`'s shallower by more than 3 pp.
   Every static's floor is set by a window containing E5's decline. Falsified by any of
   the four inequalities, or by a floor set elsewhere than 2022.
3. **The windows partition by 2021-12-27.** In each of the six sensitivity windows that
   start before NTSX's 2022 peak (2019-05-08 … 2021-11-08 starts), `NTSX100` loses
   Calmar to B75D25 *and* is deeper — its in-window drawdown is E3's or E5's (≥ 28 %)
   against the machine's ≤ 20.1 % anywhere. Of the three that start after it, it wins at
   most two, so clause (iv) fails with at most 2 of 9. Every deleveraged point wins at
   most 3 of 9. Falsified by a `NTSX100` win in an early window, three or more wins in
   total, or a deleveraged point at 4+.
4. **The matched-floor point is the 62.5 grid point itself, and the simplicity premium
   lands between 9 and 11 pp/yr.** Window floors are expected to equal full-window
   drawdowns for every NTSX point because the 2021-11-08 window contains all of E5, so
   `NTSX62.5/BIL37.5`'s floor sits 0.28 pp deeper than B75D25's — inside §9 step 2's
   1 pp band — and the premium is 18.83 − 9.25 = **9.6 pp/yr** at fraction 0.625. Had
   the band not caught it, the pilot's interpolation would give fraction 0.616 and
   9.7 pp. Falsified by a premium outside 9–11 pp or a matched point outside 0.60–0.63.
5. **The brackets keep every sign, and cost reaches the machine, not the static.** On
   `_c20` B75D25's score₃ falls by more than 0.02 (its full Calmar alone falls 0.044)
   and no static's `robust_score` falls by more than 0.01; on `_tr` no point rises by
   more than 0.03; no clause of 10.1 changes sign on either. Falsified by a sign flip, a
   static moving more than 0.01, or the machine moving less than 0.02.
6. **On the winners' lane every winner's score₃ exceeds every static's `robust_score` by
   more than 0.30, and SPY's score₃ (0.6059, its full Calmar; committed sens median
   0.7118, test 0.9983) exceeds every static's by more than 0.15.** The best static's
   full Calmar is 0.4093. Falsified by any static within 0.30 of a winner or within 0.15
   of SPY.
7. **On the 2022 lane, gold clears clause (i) and fails clause (iii).** `GDE100`'s and
   `NTSX50/GDE50`'s `robust_score` exceed all three winners' score₃ — which are bound by
   their E6-containing test windows at 0.4647–0.5256 — while their window floors are
   deeper than every winner's by more than 5 pp (GDE's first window holds its −32 %
   2022; the winners' floors are E6, −17.65 to −20.87 %); every other static on the lane
   fails (i). Recorded under 10.3 as era-dependence — gold's 2022–26 run — not
   promoted. Falsified if GDE fails (i) against any winner, if its floor is within 5 pp
   of any winner's, or if any other static clears (i).
8. **The episode that sets the static's floor is not the one that partitions the
   windows.** For the pair (B75D25, NTSX100) the partition tool splits by trough
   containment, and the table's E5 trough (2023-03-10, the 50/50 arm's) sits five
   months after NTSX's own (2022-10-14): E5's with-set is the six windows starting
   2020-05-08 … 2022-11-08, two of which begin after the static's 2022 decline. So
   **E6's trough (2025-04-08) gives the cleanest floor split**: NTSX is shallower in
   none of the six windows without it and in at least two of the three with it
   (2022-11-08 and 2023-05-08 starts, where its in-window drawdown is E6's −16.9 %
   against the machine's −18.4 %; the 2022-05-09 window still holds the last leg of its
   2022 fall, −19.3 % on its own closes), while E5's with-set holds it shallower in at
   most two of six and its without-set in exactly one of three. This is the mirror image
   of the episode verdict's finding for the sleeve, where E4 partitioned and 2022 did
   not. Falsified if NTSX is shallower in any window without E6's trough, or in fewer
   than two of the three with it.

Six of the eight are about direction; 2 and 4 pin a shape (a floor within 1 pp, a
premium within 2 pp) and are the ones most likely to be scored "held in part" (handoff
§6.5). The pre-registered outcome is 10.4(b) with prediction 7 as the one place a
static clears clause (i) anywhere.

## 12. Honest limitations

- **One decision lane, one static on it.** NTSX is the only return-stacked fund old
  enough to carry a holdout and nine three-year windows. Everything said about RSSB,
  RSST, GDE and the rest is said on windows without a TQQQ bear in them, and the whole
  argument of §1 is that the bear is what decides. The spec is honest about this by
  giving the young cohort a dated `Open:` line rather than a verdict.
- **The static's floor is a bond-market fact, not a fund fact.** NTSX's −31.4 % is what
  a 90/60 does when stocks and Treasuries fall together; RSSB and RSST would have done
  the same or worse in 2022 had they existed (NTSI, the international sibling alive
  since 2021-05, printed −34.3 %). A future bear in which bonds rally would reprice
  every NTSX-family number here in the static's favour, and the 2023 window is a
  small sample of exactly that regime.
- **Nine tickers at a default cost.** No measured spread exists for any of them; `*` 6
  bp is the blend map's catch-all and the `_c20` bracket is the stress. Because a static
  trades only its contributions the cost model barely touches it (§2.3), so a
  mis-calibration cannot flip a clause — but the cost line in the winners file, if a
  static ever enters, would be an assumption, not a measurement.
- **`robust_score` here has no neighbour term.** score₃ is a weaker minimum than the
  four-term one the σ/w lanes use, on both sides of the comparison. It is comparable
  across the grid/baseline line within this spec's lanes and not with any lane that
  grids a numeric dimension; the verdict states anchors on full-window Calmar (handoff
  §5).
- **The per-window win count is a coarser statistic than `rank_worst`.** It counts a
  pairwise comparison against one incumbent; it says nothing about where the static
  stands among the machine's own plateau. That is deliberate — the question is "one
  ticker or the machine", not "one ticker or the machine's 96th-best coordinate".
- **Monthly rebalancing of a static blend is the engine's convention, not the fund's.**
  A reader holding `RSSB50/RSST50` would rebalance rarely; the engine rebalances every
  month-end and charges for it. The bias is small (turnover 0.21–0.25 for the blends)
  and against the static.

## 13. Deliberately not in scope

A static blend as a **sleeve member** of the machine (`safe: {"NTSX": …}`) — a sleeve
candidate under CLAUDE.md §6, needing named episodes and the E4 kill condition, and a
different question. NTSX or RSSB as the machine's **risk asset** (`risk: "NTSX"` with a
vol symbol) — that is the follow-on 10.1 names if a static ever clears the bar, and a
spec of its own if not. A static with the **SMA-200 gate** or under **VT sizing** —
that is a new machine, not a static. A **synthetic 90/60 from SSO + IEF** to extend the
2019 lane backward — a new export class of question, and NTSX's own 2018–2019 bars are
not enough to change the lane. Re-fitting anything about the winners. `NTSX + BTAL`
statics (the old `TQQQ50/BTAL50` idea with a different risk asset — a new machine).
Any `_tr` / `_c20` bracket on the direction lanes.

## 14. Acceptance checklist

- [ ] `tests/test_return_stacked.py` D1–D5 green from a fresh clone; suite count 979 → N stated in the verdict
- [ ] Docs per §7 (winners-file ledger section and flag, HANDOFF_EPISODE §7.1 pointer)
- [ ] **Pre-registration commit**: `specs/sweep_rs_2019.json`, `_c20`, `sweep_rs_2021.json`, `sweep_rs_2022.json`, `rs_points_2019.json`, `rs_points_2021.json`, `rs_points_2023.json`, D3's dry-run legs, §3, §10, §11 — before any run
- [ ] Artefacts: five sweep directories, one bundle JSON, three episode reports, one partition report, committed together; §4 anchors confirmed in the verdict
- [ ] `notes/rs-verdict.md` per §9–§10; the ledger entry and the simplicity-premium flag written per 10.4; the 2023 `Open:` line dated
- [ ] No engine file touched; `SCHEMA_VERSION` 4

## 15. Errata (found during implementation)

1. **§10.3's illustrative `Open:` line names a static the rule excludes.** The wording
   *"RSSB / RSSB50+RSST50 not decidable before 2027-12"* was written before the panel was
   run. §10.3's own clause names a static only if it beats the winners on Calmar **and**
   floor; on `results/rs_points_2023.json` `RSSB50/RSST50` scores 0.9417 against the best
   winner's 1.0968 and does not qualify, while `NTSX100` (1.1689, floor −16.89) does. The
   line as written in the verdict is *"RSSB / NTSX not decidable before 2027-12"*. The
   date and the rule are unchanged.

2. **§2.5's "Deleveraging with BIL … changes no sign" is contradicted by its own table.**
   Every cell does scale toward zero, but E3's episode return crosses zero: `NTSX100`
   −0.2 against `NTSX75/BIL25` +0.1, `NTSX62.5/BIL37.5` +0.2, `NTSX50/BIL50` +0.3
   (`results/episode_rs_2019.md` reproduces the pilot exactly). It is the only sign change
   in the panel, and it is the arithmetic of a COVID round trip that the levered arm
   finishes barely under water and the deleveraged arms barely above it.

(Two items found during the pilot belong to other documents and are
recorded here for the handoff, not as errata of this spec: `HANDOFF_EPISODE.md` §8
attributes the no-gate twin 0.71623794 to `syn_bridge_2012`, which holds only the
`BIL`-sleeve twins — the number is in `results/sweep_comp_2012/summary.json`; and
`load_prices`' completeness assert (`prices.py` line 100) fails without naming the
symbol, which cost the pilot one probe — a message naming the null columns would be
engine work and is not requested here.)
