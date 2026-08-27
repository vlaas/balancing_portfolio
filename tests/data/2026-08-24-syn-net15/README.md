# Synthetic pre-inception snapshot — 2026-08-24-syn-net15

Derived from the frozen `2026-08-24-net15` snapshot by `make_synthetic.py`
(SYNTHETIC_HISTORY_SPEC §2–§4), with the index leg (`QQQ`), the accrual
calendar (`SPY`) and the floating rate (`macro/DTB3`) read from the
gross root `2026-08-24` — a swap pays the gross total return in either
convention. `TQQQ.csv` and `BIL.csv` carry columns `time,close,source`:
rows before the real fund's first bar are modelled (`synthetic`), rows from
it on are the parent's own values (`real`), and the two meet
multiplicatively at the splice. Every other `<SYM>.csv` and every
`price/<SYM>.csv` is byte-copied from the parent; `price/TQQQ.csv` and
`price/BIL.csv` are deliberately absent — a modelled segment has no
unadjusted twin — and `macro/` is not copied.

**A synthetic root is a falsifier, never a fitting lane**: no parameter is
adopted from a window that contains synthetic bars (§10). Any run whose
window starts on or after 2010-02-11 reads only real bars and
reproduces the parent root's numbers exactly (§4).

## The models (§2.3, §2.5)

```
3x fund:     r_t = 3*s_t - 2*y_(t-1)*d_t/360 - c*d_t/365
T-bill fund:  r_t = (1 - 0.15)*y_(t-1)*d_t/360 - c_b*d_t/365
```

`s` the index total return, `y` DTB3 forward-filled onto the bar calendar
and lagged one row, `d` calendar days since the previous bar. Each constant
is the closed-form mean-residual estimate on log returns, fitted against the
parent's own real segment, so the model ends the overlap at the real
series' level exactly. Withholding w = 0.15 enters the bill accrual
proportionally and the leveraged fund not at all — a leveraged fund's own
distributions are tiny and roughly constant, so its constant absorbs them
(§2.5).

## Fitted constants

| model | overlap | n | c %/yr | used %/yr | beta | daily residual | max cum. dev. |
|---|---|---|---|---|---|---|---|
| TQQQ — 3x QQQ | 2010-02-11 → 2026-08-20 | 4155 | 1.9431 | 1.9431 | 2.9772 | 17.66 bp | 9.57% |
| BIL — DTB3 accrual | 2007-05-30 → 2026-08-20 | 4837 | 0.0931 | 0.0931 | — | 3.05 bp | 1.10% |

## The splice

| symbol | synthetic rows | first bar | real rows | first real bar | scale |
|---|---|---|---|---|---|
| TQQQ | 2749 | 1999-03-10 | 4158 | 2010-02-11 | 32.26983675770822 |
| BIL | 3609 | 1993-01-29 | 4840 | 2007-05-30 | 46.04507841743029 |

## QQQ's pre-inception distributions (§2.2, S10)

24 implied ex-dates on 2003-12-24 → 2010-12-31 from the gross
pair, the first on 2003-12-24 — the dot-com stretch is dividend-free by
construction, the one era where a mis-embedded dividend could not matter.
Implied yield by year:

| year | implied yield |
|---|---|
| 2003 | 0.04%/yr |
| 2004 | 0.95%/yr |
| 2005 | 0.33%/yr |
| 2006 | 0.32%/yr |
| 2007 | 0.30%/yr |
| 2008 | 0.36%/yr |
| 2009 | 0.56%/yr |
| 2010 | 0.73%/yr |

Operator spot check against the issuer's published distribution history:

| ex-date | implied | published | delta |
|---|---|---|---|
| 2003-12-24 | 0.01358 | 0.01358 | +0.00000 |
| 2004-12-17 | 0.37858 | 0.37858 | +0.00000 |
| 2005-12-16 | 0.10110 | 0.10110 | -0.00000 |
