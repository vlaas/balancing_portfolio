# Specification: refreshing live `data/` from a tview batch without losing history

Repo: `vlaas/balancing_portfolio` · baseline commit: `a25c260` (`main`, "Handoff: tview
fixes and the no-overwrite merge tool", 1267 tests green, none skipped) · status: implemented (2026-10-19, branch `data-refresh`) — verification in §9

## 1. Goal

Live `data/` is produced by the TradingView downloader in `~/code/tview` (`dl.sh`), not
by the manual *Export chart data…* procedure `data/README.md` describes: the 2026-09-02
batch's `csv/` was written 2026-09-03 00:35 and data commit `d49a1b9` landed at 00:41,
bit-identical. Copying `csv/` over `data/` is an overwrite: it silently loses rows the
provider no longer serves (SPX's first 32 bars on 2026-10-19, §2.4), takes a partial
last bar, and takes every revision of history unseen.

This spec adds `refresh_data.py`, which merges a tview batch into `data/adjusted/`,
`data/unadjusted/` and `data/index/` (DATA_LAYOUT_V2_SPEC §2). It never drops a row
`data/` holds; it trims bars that had not closed when the batch started; it reports
every revision of existing history and refuses it unless the symbol is named in an
explicit `--accept`; it validates the whole batch before writing anything, and writes
nothing without `--write`.

No engine code, no frozen root, no result and no loader behaviour changes. FRED
(`fetch_fred.py`) and the Polygon dividend records (`fetch_dividends.py`) are out of
scope.

## 2. The downloader and its batch — measured

### 2.1 tview fixes

`~/code/tview` has a local git history now, with no remote. The handoff's §4 fixes
landed there on 2026-10-19:

| commit | change |
|---|---|
| `5b46e4e` | `list` and `ndiv` tracked; `.gitignore` covers `price/`, `dividends/`, `csv/`, `token`, `started` |
| `2b7dbfd` | the parquet time index is written in ns. pandas 3 makes it `datetime64[s]`, which fastparquet stored as `TIMESTAMP_MILLIS` holding floor(s / 1000), so every `csv/` date read 1970-01-01 |
| `c23d02a` | 40 pages of 1,000 bars. 20 pages capped SPX at exactly 21,000 rows, and each refresh would have pushed its start later |
| `46112f6` | `list` drops the four `FRED:` lines (now `fetch_fred.py`) and `LSE:JMFP` (it returned nothing); `ndiv` gains `NASDAQ:NDX` |
| `0cd6848` | the auth token is read from the untracked `token` file, and the `set_auth_token` message is never logged |
| `5921dda` | `dl.sh` clears `price/`, `dividends/`, `csv/` first and writes the UTC start to `started` |

- `list` holds 64 symbols: `data/`'s 57 pairs plus its 7 indices.
- `ndiv` holds 8: VIX, VIX3M, XNDX, SPX, GLD, EURUSD, GBPUSD, NDX.
- A batch is 64 `price/` files plus 56 `dividends/` files.
- `convtocsv.py` is unchanged.

### 2.2 The post-close batch of 2026-10-19

- **Run.** `started` is `2026-10-19T20:15:24Z` (16:15 ET), and the run took about
  12 minutes.
- **Completion.** All 120 passes stopped on "history exhausted": none reached the
  40-page cap, none timed out, no session aborted.
- **Real dates (handoff §7).** QQQ runs 1999-03-10 → 2026-10-19 in both passes, 6,946
  rows.
- **SPX.** It has 25,339 rows from **1871-02-01**: one bar a month until 1927-12-30,
  daily from then on. `data/index/SPX.csv` starts 1943-04-14, so the batch serves 4,307
  rows before it (§3.4).

### 2.3 Bar stamps

The UTC bar-open time of the last 300 bars of every `price/` parquet:

| market | summer | winter | local open |
|---|---|---|---|
| `AMEX`, `NASDAQ`, `SP`, Cboe-listed ETFs | 13:30 | 14:30 | 09:30 New York |
| `CBOE:VIX` | 07:15 | 08:15 | 03:15 New York (global trading hours) |
| `LSE`, `XETR`, `EURONEXT` | 07:00 | 08:00 | 08:00 London / 09:00 CET |
| `FX_IDC` | 22:00 | 22:00 | a fixed 22:00 UTC (17:00 EST, 18:00 EDT) |

- **FX bars.** An `FX_IDC` bar labelled D runs from D 22:00 UTC to D+1 22:00 UTC. The
  label sits on the open, as `data/README.md` "FX bar stamps" describes. Its
  boundary is fixed in UTC rather than at 17:00 New York.
- **Last bars of the batch.** Every market's last bar is 2026-10-19, except FX at
  2026-10-18, a bar that was still open.
- **Previous download.** The 2026-09-02 batch was written at 21:35 UTC. That is before
  the 22:00 UTC close of the FX bar labelled 2026-09-01.

### 2.4 The batch against `data/` (the 2026-09-02 batch)

- **Passes.** For all 57 pairs the two passes share their calendar and their last
  close (`R_last = 1`).
- **Calendars.** No date is added or removed inside any overlap, in any of the 121
  destination files. No file starts later than its `data/` counterpart; only SPX
  starts earlier.
- **Closes.** Every `unadjusted/` close is bit-identical on the overlap. So is every
  `index/` close except one: **EURUSD 2026-09-01**, 1.15877 → 1.15878 (8.6e-6). That
  bar was still open at the previous download (§2.3), so V2 catches it, and §3.3
  would have trimmed it.
- **Other columns.** These are not compared (§3.5):
  - Volume of the old last bar (2026-09-02) differs in both passes of all 44 US pairs
    (TMF's adjusted pass: two rows) and in NDX. Consolidated volume posts after the
    close.
  - EURUSD's high differs on 33 rows and its low on 89, scattered through history;
    open differs once for EURUSD and once for GBPUSD.
- **Adjusted ratio.** The spread of `ln(new close / old close)` over the overlap:
  - worst **1.91e-7** (BND), then TQQQ 8.94e-8, QLD 5.11e-8, and ≤ 1.7e-8 everywhere
    else;
  - exactly 0 for 24 of the 57 pairs.
  - Open, high and low behave the same (worst 1.91e-7, BND).
  - The smallest genuine distribution jump in the repo is 1.247e-5 (BIL, `make_net_tr.py`).
  - `LN_C_SPREAD_MAX = 1e-6` is the suite's `TAU`: one order above the measured
    magnitude, and 12× below that jump.
- **The mid-session evidence.** The 2026-10-19 run at 13:19–13:29 ET is kept outside
  the repo:
  - CNDX had a 2025-11-21 bar in its dividends-OFF pass only, and IB01 had it in both
    passes.
  - The post-close batch serves it in neither.
  - So it was a transient provider bar, not a revision. S2 catches the first shape and
    V1 the second.
  - The same run's partial US last bars are what S2's last-close check catches.

### 2.5 Format

For all 121 destination files, the merge of §3 equals the batch's `csv/` text
byte-for-byte, apart from §3.3's trims and §3.4's skipped rows. `convtocsv.py` and the
current `data/` files share polars' shortest float rendering, so a new row needs no
re-rendering.

## 3. Merge rules — normative

### 3.1 Input

`refresh_data.py` reads the tview folder (default `~/code/tview`):

- `list`: one `MARKET:TICKER [RENAME]` per line. The symbol is `RENAME` when it is
  given (`EURONEXT:DBMF DBMF_EU`), else `TICKER`; `MARKET` selects the §3.3 close.
- `ndiv`: the `list` lines that get no dividends pass.
- `started`: the UTC instant `dl.sh` began, ISO 8601 with `Z`.
- `csv/price/<SYM>.csv` (`adjustment=splits`) and `csv/dividends/<SYM>.csv`
  (`adjustment=dividends`): `convtocsv.py`'s output, already the repo layout
  `time,open,high,low,close,Volume`.

It reads `csv/`, not the parquet: a new row is copied as text, so it lands in `data/`
byte-identical to the batch (§2.5), and no float is re-rendered except the rescaled
rows of §3.4.

### 3.2 Classes and destinations

A symbol's class is the folder it already has in `data/` (DATA_LAYOUT_V2_SPEC §2: a
file's class is its folder), never inferred from `ndiv` or from a missing twin:

| class in `data/` | `ndiv` | source | destination |
|---|---|---|---|
| `index/<SYM>.csv` | — | `csv/price/<SYM>.csv` | `index/<SYM>.csv` |
| `adjusted/<SYM>.csv` | no | `csv/dividends/<SYM>.csv` | `adjusted/<SYM>.csv` |
| | | `csv/price/<SYM>.csv` | `unadjusted/<SYM>.csv` |
| `adjusted/<SYM>.csv` (GLD) | yes | `csv/price/<SYM>.csv` | `adjusted/<SYM>.csv` and `unadjusted/<SYM>.csv`, byte-identical |

`csv/dividends/` is never read for an index. **The batch's symbols must be exactly
`data/`'s** (`adjusted/` ∪ `index/`). A batch symbol `data/` lacks stops the refresh,
because adding a symbol is a manual step: its class is a decision, and its pins
(`tests/test_layout.py` counts, `LIVE_PAIRS`, the yield bands) move in the same commit.
A `data/` symbol the batch lacks stops it too, because a refresh that silently skips a
symbol lets `data/`'s last bars drift apart.

### 3.3 Closed bars only

The bar dated D is final at its market's close, in the market's own zone:

| `MARKET` | zone | final at |
|---|---|---|
| `AMEX`, `NASDAQ`, `SP` | America/New_York | 16:00 on D |
| `CBOE` | America/New_York | 16:15 on D (VIX, VIX3M; the Cboe-listed ETFs take the later time) |
| `LSE` | Europe/London | 16:35 on D (after the closing auction) |
| `XETR` | Europe/Berlin | 17:35 on D |
| `EURONEXT` | Europe/Paris | 17:35 on D |
| `FX_IDC` | UTC | 22:00 on D + 1 |

Every trailing bar whose close is after `started` is **trimmed** from every pass of
the symbol, and the report names it. The next refresh picks it up, since the new file
wins from its first bar (§3.4). An `FX_IDC` bar opens at 22:00 UTC on its label date
and runs 24 h (§2.3), so a weekday batch always ends in an open FX bar. Stopping on it
would block every refresh, and that is why the rule trims instead of stopping. A
`MARKET` missing from the table stops the refresh.

### 3.4 Authoritative range and history protection

After trimming, the new file **wins from its own first bar onward**, with one
exception: **rows the batch serves before `data/`'s first bar are taken only for a
symbol named in `--accept`**. Otherwise they are skipped and the report counts them.
`data/`'s first bars never move silently. SPX's 1871–1943 rows (§2.2), monthly before
1928, would break the one-row-per-trading-day layout of `data/README.md`.

Rows of the `data/` file strictly before the new first bar are **kept**:

- `index/` and `unadjusted/` rows are kept verbatim.
- `adjusted/` rows have open, high, low and close multiplied by
  `c = new close / old close` at the first common date. Volume is kept verbatim, and
  each product is written as Python `repr` (shortest round-trip, the same rendering as
  polars). TradingView's adjustment is multiplicative, and a new ex-date rescales all
  earlier history by one factor (§2.4). Multiplying by `c` therefore gives the rows the
  values the provider would serve if it still served them.

The kept rows are what preserves SPX's history if the provider ever serves less than
`data/` holds.

### 3.5 Checks

**Hard stops** (no flag overrides them):

- S1 — a source file is missing; a header (batch or `data/`) is not
  `time,open,high,low,close,Volume`; batch dates are not ascending and unique; no bar
  survives the trim.
- S2 — a paired symbol's two passes differ in calendar or in last close after the trim
  (`R_last ≠ 1`, which the live-pair lane asserts exactly).
- S3 — the batch ends before `data/` does (a stale or failed download).
- S4 — no date in common with `data/`.
- S5 — the symbol sets of §3.2 differ; a `MARKET` has no close; `started` is missing.
- S6 — `--accept SYM` where SYM has nothing to accept (no revision and no earlier
  rows), so a stale accept can never ride along.

**Revisions** stop the refresh unless the symbol is named in `--accept`. The report
names what was accepted:

- V1 — **calendar**: a date inside `[max(old first, new first), old last]` was added
  or removed (CNDX/IB01's 2025-11-21).
- V2 — **close**: an `unadjusted/` or `index/` close differs from `data/` on a common
  date. The comparison is exact (§2.4).
- V3 — **adjusted ratio**: the spread `max − min` of `ln(new close / old close)` over
  the common dates exceeds `LN_C_SPREAD_MAX` (§2.4). That is a revised or inserted
  distribution, not a new ex-date.

Only `close` is compared, because the simulator reads only `time,close`
(`prices.py::_read_symbol`). Open, high, low and Volume are taken with the winning row;
their revision counts are in §2.4. A new first bar later than `data/`'s is history
protection (§3.4) and is reported, not stopped.

### 3.6 All or nothing

Every symbol is planned and every check run before any file is written, as in
`make_net_tr.py`'s `build`/`write_dataset` split. A refresh with any stop writes
nothing, `--write` or not. A refresh without stops writes only the files whose text
changed. The live root is under git, so `git restore data/` undoes a written refresh.

## 4. `refresh_data.py` — contract

```
uv run refresh_data.py [TVIEW_DIR] [--data DIR] [--accept SYM ...] [--write]
```

- `TVIEW_DIR` defaults to `~/code/tview`, and `--data` to `data`.
- It prints one line per symbol (class, status `ok` / `accepted` / `STOP`, and the
  folders whose file would change), followed by the revisions, trims, kept, taken or
  skipped rows and stops under it. Run-level stops (S5, S6) are listed last.
- Exit status 1 with `Refused: nothing written.` on any stop. Exit 0 with
  `Dry run: …` when `--write` is absent, and with `Wrote N files.` when it is present.
- Standard library only. It is a repo-root script like `fetch_fred.py`, never imported
  by the engine.

After a written refresh, `uv run pytest -q` runs the guards already in the suite: the
live-pair lane of `tests/test_total_return.py` (pair invariants, implied-yield bands,
`LIVE_PAIRS == 57`), `tests/test_layout.py` (live 57 / 7 / 57) and
`tests/test_prices.py` (every bundle loads from live `data/`). Freezing a
`tests/data/<TQQQ last bar>/` snapshot and generating derivatives remain the operator's
decision. Snapshots stay append-only.

## 5. Tests — `tests/test_refresh_data.py` (new)

Each test builds a throwaway tview folder and live root under `tmp_path`. No test reads
or writes the repo's `data/` or `~/code/tview`.

- A clean batch appends, a dry run writes nothing, and `--write` makes each
  destination equal to its source.
- A new ex-date on the appended bar rescales the whole overlap and is not a revision.
- History protection: `index/` rows before the new first bar are kept verbatim, and
  `adjusted/` rows are kept × c with the `unadjusted/` twin verbatim.
- Rows before `data/`'s first bar are skipped without `--accept` and taken with it.
- Trim: a US bar before 16:00 ET leaves every pass. An FX bar is final at 22:00 UTC
  the day after its label: kept at 22:00:00, trimmed at 21:59:59.
- V1, V2 and V3 each stop. V1 accepted writes the batch. Ratio noise below
  `LN_C_SPREAD_MAX` is not a revision.
- S2 stops even with `--accept`, and the unused accept is itself an S6 stop. S3 and
  S1 (a missing file) stop. S5 stops in both directions.
- A refused `--write` leaves every file in the root byte-identical.
- A single-pass pair (GLD) writes two byte-identical files.

## 6. Docs

- `data/README.md`: "Export settings" becomes the tview procedure. It covers `dl.sh`,
  `list`/`ndiv`, the token file, `started`, this tool, the suite, and the commit. The
  §3.2 table replaces the manual two-pass recipe, and the after-close rule becomes
  §3.3's trim.
- `README.md` ("Data notes") and `docs/ARCHITECTURE.md` (the total-return decision):
  one sentence each naming `refresh_data.py` as the way live `data/` is refreshed.

## 7. Acceptance checklist

- [x] tview fixes landed in `~/code/tview` (§2.1); a fresh post-close batch has real
      dates (QQQ 1999-03-10 → 2026-10-19)
- [x] `refresh_data.py` per §3–§4
- [x] `tests/test_refresh_data.py` per §5; suite = 1267 + the new tests, none skipped
- [x] Dry run on the 2026-10-19 post-close batch: the report matches §2.4 (which
      symbols stop, which trims)
- [x] A written refresh of live `data/` (`--accept EURUSD`) passes the whole suite,
      including the live lane (§4), and equals the batch byte-for-byte (§2.5); `data/` is
      then restored with `git restore data/`, because committing a refresh is the
      operator's call
- [x] Docs per §6; no change to `prices.py`, `simulate.py`, `strategy.py`, any frozen
      root or `results/`

## 8. Deliberately not in scope

- **Applying the 2026-10-19 refresh** and freezing a snapshot from it. The tool reports,
  and the operator decides what to accept and commit (handoff §5).
- FRED (`fetch_fred.py`) and the Polygon dividend records.
- Adding a symbol: a manual step by design (§3.2).
- Splits. A split rescales the unadjusted history of both passes, so it shows as a V2
  revision across the whole overlap. Accepting it takes the new basis. The
  implied-distribution literals of `tests/test_total_return.py` T3 then move, as their
  comment already says.

## 9. Errata (implementation)

1. **No deviation from §3–§6.** The commits are Phase 0 (spec), Phase 1
   (`refresh_data.py` and its 18 tests), Phase 2 (docs) and Phase 3 (this
   section), with the suite green after each one. It goes from 1267 to 1285,
   none skipped. The tview fixes of §2.1 are commits in `~/code/tview`, not here.
2. **The handoff's "after 23:00 local is always safe" holds for the exchanges,
   not for FX.** An `FX_IDC` bar closes at 22:00 UTC the day after its label
   (§2.3), so a weekday batch always ends in an open FX bar. That is why §3.3
   trims instead of stopping, and why `dl.sh` has no clock guard. For a refresh
   to keep the day's bars, the start must still come after 16:15 ET. The batch
   of §2.2 cleared Cboe's 16:15 close by 24 seconds.
3. **Verification, as run at the Phase 2 commit**, on the §2.2 batch:
   - Dry run: exit 1, `Refused: nothing written.` 63 symbols are `ok`. EURUSD
     stops on V2 (2026-09-01). EURUSD and GBPUSD trim their bar labelled
     2026-10-18. SPX skips 4,307 rows before 1943-04-14.
   - `--accept EURUSD --write` writes 121 files. Every one equals its batch
     source byte-for-byte, apart from the two trimmed FX bars and SPX's skipped
     rows.
   - With that `data/` live, `uv run pytest -q` gives 1285 passed, including the
     live-pair lane over all 57 pairs and the 57 / 7 / 57 layout pins.
   - `git restore data/` then returns the live root to `main`'s bytes, and the
     suite passes again (1285).
   - `git diff main..HEAD` touches no engine file, no frozen root and nothing
     under `results/`.
