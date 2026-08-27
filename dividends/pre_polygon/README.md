# Pre-Polygon distribution records

Polygon's dividend reference endpoint (`fetch_dividends.py`) returns nothing
before **2011-03-18** for QQQ — verified by asking it explicitly for history
from 1999. QQQ's first distribution was 2003-12-24, so the provider's boundary
cuts off eight years of a real record. The CSVs here carry that earlier
stretch; `extend_dividends.py` merges them into `dividends/<SYM>.parquet` with
a `source` column, so the parquet is the single reusable record and the
provenance of every row stays visible.

These are **as-paid** cash amounts. QQQ's only split (2-for-1, ex 2000-03-20)
predates every distribution the trust has ever made, so as-paid and
split-adjusted coincide and no adjustment is applied.

## QQQ.csv — 24 rows, 2003-12-24 → 2010-12-17

`source = sec-n30b2`: quoted verbatim in the trust's audited annual reports.
The 2004-12-17 amount appears as *"the Trust paid an ordinary income dividend
to shareholders of $.37858 per share"* in the N-30B-2 for the fiscal year
ended 2004-09-30 — it is a $3.00 Microsoft special dividend passing through,
which is why it is 28× any neighbour.

`source = dividendhistory`: dividendhistory.org and dividendhistory.net, which
agree to all five decimals. Every row is corroborated two ways:

- **Fiscal-year reconciliation.** The trust's audited Financial Highlights
  report distributions per share on a fiscal year ending 30 September. Summing
  the rows above by fiscal year reproduces each audited figure: FY2004 0.01358
  → (0.01), FY2005 0.41334 → (0.41), FY2006 0.17930 → (0.18), FY2007 0.14412 →
  (0.14), FY2008 0.14831 → (0.15), FY2009 0.17704 → (0.18), FY2010 0.32991 →
  (0.33). FY2000–FY2003 show "—", confirming 2003-12-24 is genuinely the first.
- **The ex-date rule.** The 2009 prospectus fixes the regular ex-date as the
  third Friday of March, June, September and December, or the preceding
  business day. Every row from 2004-12-17 on satisfies it, including
  2008-03-20 (the third Friday, 2008-03-21, was Good Friday). 2003-12-24 is
  off-cycle, consistent with a year-end RIC-compliance distribution.

Independently, all 24 amounts match the distributions implied by the
`tests/data/2026-08-24` gross pair (`adjusted / price`, TOTAL_RETURN_SPEC §4
invariant 4) to five decimals — the check `tests/test_synthetic.py` pins for
three of them (SYNTHETIC_HISTORY_SPEC S10).

Sources: SEC EDGAR CIK 0001067839 filings `c36210.txt` (FY2004),
`a2167148zn-30b_2.txt` (FY2005), `a06-24326_3n30b2.htm` (FY2006),
`a11-28102_1n30b2.htm` (FY2007–FY2011), `powershares_485bpos.htm` (the
prospectus); dividendhistory.org/payout/QQQ/.

Not used: digrin.com rounds to four decimals, diverges by ~0.5 % from
2007-06-15 on, and carries a phantom 2010-06-25 row that breaks the FY2010
reconciliation. stockanalysis.com, nasdaq.com and investing.com have no
pre-2012 rows at all.
