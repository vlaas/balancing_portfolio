# SYNB — the synthesis arm on `2026-09-02-net15-usd` (EU_SUBSTITUTE_SPEC §5)

Estimation window (§5.2): month-ends 2020-05-29 → 2023-12-29, 44 month-ends, 43 monthly returns; β(MVEA, CSPX) = 0.7739, β(XSPS, CSPX) = -0.9781; **w_S\* = 0.4417 → 0.45** (nearest of 0.40, 0.45, 0.50).

Falsifier window (§5.3): month-ends 2020-05-29 → 2026-08-28, 75 monthly returns; E4 bound over 2020-09-01 → 2021-03-31.

| w_S | primary | F1 corr(SYNB, BTAL) ≥ 0.50 | F2 mean over worst-decile CNDX months (k) > 0 | F3 SYNB / BTAL peak-to-trough, ratio ≤ 1.5 | verdict |
|---|---|---|---|---|---|
| 0.40 | sens. | +0.332 ❌ | +0.33 pp (k = 7) ✅ | -3.47 % / -31.12 %, 0.11 ✅ | **ARM-ONLY** |
| 0.45 | **yes** | +0.525 ✅ | +0.87 pp (k = 7) ✅ | -4.23 % / -31.12 %, 0.14 ✅ | **PROXY** |
| 0.50 | sens. | +0.656 ✅ | +1.42 pp (k = 7) ✅ | -5.50 % / -31.12 %, 0.18 ✅ | **PROXY** |

## F4 — the daily-reset short leg, monthly-held XSPS against −1 × SPY (documentation, no bar)

| year | months | XSPS % | −1 × SPY % | shortfall pp |
|---|---|---|---|---|
| 2020 | 7 | -21.67 | -21.02 | -0.65 |
| 2021 | 12 | -24.41 | -24.07 | -0.35 |
| 2022 | 12 | +20.93 | +16.60 | +4.33 |
| 2023 | 12 | -14.75 | -22.52 | +7.76 |
| 2024 | 12 | -12.01 | -21.23 | +9.21 |
| 2025 | 12 | -10.86 | -16.35 | +5.49 |
| 2026 | 8 | -8.07 | -12.64 | +4.58 |
