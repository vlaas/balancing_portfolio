# Overlap validation — `2026-09-02-net15-usd` (EU_SUBSTITUTE_SPEC §4)

Verdicts: the **quarterly** table decides (§4.4, drift as α; P6 decides on the
weekly supplement); the **monthly** table records the letter of §4.2 (the
intercept as α), gap-attenuated for every LSE/Euronext line. `·` = not the
row's verdict horizon. P3 is read against gross BIL in `2026-09-02`
(erratum 13); its net-15 reading is listed under the haircuts.

## monthly horizon — the §4.2 letter (verdict column: intercept as α)

| pair | eu / us | class | first | last | n | β | α %/yr | drift %/yr | R² | corr | resid %/yr | TD12 min / med / max pp | worst period pp (date) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | QQQ3 / TQQQ | MECHANICAL | 2012-12-17 | 2026-09-02 | 164 | 0.9565 | +1.68 | +0.11 | 0.9545 | 0.9770 | 11.39 | -10.54 / -0.59 / +10.79 | -12.52 (2022-11-30) | letter: FAIL |
| P2 | QQL3 / TQQQ | MECHANICAL | 2022-06-09 | 2026-09-02 | 50 | 0.9729 | -1.72 | -2.91 | 0.9400 | 0.9695 | 14.43 | -16.18 / -3.81 / +9.20 | -12.61 (2022-11-30) | letter: FAIL |
| P3 | IB01 / BIL | MECHANICAL | 2019-02-22 | 2026-09-02 | 90 | 1.0102 | +0.08 | +0.10 | 0.8849 | 0.9407 | 0.22 | -0.40 / +0.08 / +0.73 | +0.35 (2020-03-31) | letter: PASS |
| P4 | CSPX / SPY | MECHANICAL | 2010-09-15 | 2026-09-02 | 191 | 0.9464 | +0.77 | +0.05 | 0.9460 | 0.9726 | 3.17 | -3.61 / +0.02 / +2.65 | +3.53 (2020-03-31) | letter: FAIL |
| P5 | CNDX / QQQ | MECHANICAL | 2010-09-15 | 2026-09-02 | 191 | 0.9629 | +0.60 | -0.05 | 0.9525 | 0.9760 | 3.65 | -4.27 / -0.17 / +3.55 | -4.26 (2022-11-30) | letter: FAIL |
| P6 | DBMF_EU / DBMF | FUNCTIONAL | 2025-03-17 | 2026-09-02 | 17 | 1.1596 | +2.76 | +5.76 | 0.6950 | 0.8337 | 7.00 | -1.97 / +1.86 / +7.78 | +5.05 (2025-04-30) | · |
| P7 | LQQ / QQQ | PARAMETRIC | 2006-06-28 | 2026-09-02 | 242 | 1.9571 | -6.45 | +8.02 | 0.9591 | 0.9793 | 7.53 | -61.25 / +11.77 / +42.63 | -18.61 (2008-01-31) | letter: characterization |
| P8 | DBMF_EU / KMLM | — | 2025-03-17 | 2026-09-02 | 17 | -0.1063 | +25.52 | +15.55 | 0.0078 | -0.0885 | 12.63 | +8.40 / +11.02 / +23.08 | -11.40 (2026-03-31) | letter: documentation |

## quarterly horizon — the §4.4 decision horizon (verdict column: drift as α)

| pair | eu / us | class | first | last | n | β | α %/yr | drift %/yr | R² | corr | resid %/yr | TD12 min / med / max pp | worst period pp (date) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | QQQ3 / TQQQ | MECHANICAL | 2012-12-17 | 2026-09-02 | 54 | 0.9976 | -0.05 | -0.14 | 0.9846 | 0.9923 | 7.38 | -6.52 / -1.07 / +7.10 | -9.86 (2022-12-30) | **PASS** |
| P2 | QQL3 / TQQQ | MECHANICAL | 2022-06-09 | 2026-09-02 | 16 | 1.0718 | -7.28 | -3.78 | 0.9786 | 0.9893 | 9.05 | -9.32 / -5.93 / +2.13 | -10.19 (2025-03-31) | **FAIL** |
| P3 | IB01 / BIL | MECHANICAL | 2019-02-22 | 2026-09-02 | 29 | 1.0053 | +0.08 | +0.09 | 0.9551 | 0.9773 | 0.23 | -0.39 / +0.06 / +0.69 | +0.43 (2020-03-31) | **PASS-BY-ERRATUM** |
| P4 | CSPX / SPY | MECHANICAL | 2010-09-15 | 2026-09-02 | 63 | 0.9792 | +0.28 | +0.00 | 0.9794 | 0.9897 | 2.11 | -3.27 / -0.06 / +2.17 | -2.60 (2020-06-30) | **FAIL** |
| P5 | CNDX / QQQ | MECHANICAL | 2010-09-15 | 2026-09-02 | 63 | 1.0047 | -0.22 | -0.14 | 0.9828 | 0.9913 | 2.44 | -3.33 / -0.17 / +2.17 | -3.39 (2022-12-30) | **FAIL** |
| P6 | DBMF_EU / DBMF | FUNCTIONAL | 2025-03-17 | 2026-09-02 | 5 | 0.1933 | +20.69 | +5.10 | 0.0205 | 0.1433 | 7.08 | -1.97 / +2.91 / +7.78 | +8.34 (2025-06-27) | · |
| P7 | LQQ / QQQ | PARAMETRIC | 2006-06-28 | 2026-09-02 | 80 | 2.0235 | -7.45 | +8.29 | 0.9858 | 0.9929 | 4.80 | -60.75 / +11.69 / +42.63 | -30.71 (2022-06-30) | **characterization** |
| P8 | DBMF_EU / KMLM | — | 2025-03-17 | 2026-09-02 | 5 | -0.0787 | +24.70 | +20.85 | 0.0122 | -0.1105 | 7.11 | +11.04 / +17.06 / +23.08 | +15.02 (2025-06-27) | **documentation** |

## weekly horizon — the supplement (decides P6, drift as α)

| pair | eu / us | class | first | last | n | β | α %/yr | drift %/yr | R² | corr | resid %/yr | TD12 min / med / max pp | worst period pp (date) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | QQQ3 / TQQQ | MECHANICAL | 2012-12-17 | 2026-09-02 | 714 | 0.8869 | +3.63 | -0.43 | 0.8589 | 0.9268 | 20.83 | -20.33 / -0.68 / +16.81 | +26.58 (2020-03-20) | · |
| P2 | QQL3 / TQQQ | MECHANICAL | 2022-06-09 | 2026-09-02 | 220 | 0.8899 | +0.26 | -4.22 | 0.8632 | 0.9291 | 22.11 | -16.18 / -3.41 / +8.93 | -14.18 (2025-04-11) | · |
| P3 | IB01 / BIL | MECHANICAL | 2019-02-22 | 2026-09-02 | 392 | 0.9509 | +0.23 | +0.10 | 0.5048 | 0.7105 | 0.28 | -0.48 / +0.08 / +0.81 | +0.40 (2020-03-27) | · |
| P4 | CSPX / SPY | MECHANICAL | 2010-09-15 | 2026-09-02 | 829 | 0.8860 | +1.60 | +0.05 | 0.8618 | 0.9284 | 5.70 | -6.29 / +0.03 / +5.64 | +9.55 (2020-03-20) | · |
| P5 | CNDX / QQQ | MECHANICAL | 2010-09-15 | 2026-09-02 | 826 | 0.8776 | +2.11 | -0.06 | 0.8620 | 0.9284 | 6.71 | -6.00 / -0.12 / +4.70 | +8.25 (2020-03-20) | · |
| P6 | DBMF_EU / DBMF | FUNCTIONAL | 2025-03-17 | 2026-09-02 | 75 | 0.9465 | +5.88 | +4.90 | 0.4290 | 0.6550 | 9.66 | -2.93 / +2.62 / +8.60 | +4.09 (2026-01-23) | **FAIL** |
| P7 | LQQ / QQQ | PARAMETRIC | 2006-06-28 | 2026-09-02 | 1052 | 1.8181 | -4.22 | +8.11 | 0.8566 | 0.9255 | 15.11 | -72.24 / +12.10 / +55.01 | -26.14 (2008-10-10) | · |
| P8 | DBMF_EU / KMLM | — | 2025-03-17 | 2026-09-02 | 75 | 0.1969 | +21.60 | +14.55 | 0.0312 | 0.1767 | 12.58 | +7.71 / +12.58 / +24.29 | -6.71 (2026-03-06) | · |

## Haircuts pinned (§4.3) — `h = max(0, −drift)` %/yr, carried slots only

| US symbol | h %/yr |
|---|---|
| BIL | 0.0000 |
| TQQQ | 0.1421 |

P3 on `2026-09-02-net15-usd` (quarterly, the net-15 basis the spec pre-registered): n 29, β 1.1769, drift +0.48 %/yr, resid 0.24 — verdict on that basis: FAIL.
