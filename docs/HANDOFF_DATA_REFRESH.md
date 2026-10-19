# Handoff: data layout V2 done → tview fixes and the no-overwrite merge tool

Written 2026-10-19 at `94f37b1` on branch `data-layout-v2`: five commits on top of
`main` @ `bd843ac`, **not pushed or merged**, **1267 tests green**. Audience: the
fresh conversation that fixes the TradingView downloader and builds the tool that
refreshes `data/` without losing history. Read this file, then `CLAUDE.md`, then
`data/README.md` and `docs/DATA_LAYOUT_V2_SPEC.md`. Nothing from the previous
conversation is needed: every finding it relied on is in this file.

## 1. The task

Two increments, in this order:

1. **Fix the downloader** in `~/code/tview` (§4), then re-run it **after the US
   close** to get a clean batch.
2. **Spec, then build, the merge tool** in this repo (§5): it takes a tview batch
   and updates `data/adjusted/`, `data/unadjusted/` and `data/index/`. It never
   loses rows the provider no longer serves, and it refuses or flags anything
   suspicious instead of overwriting.

FRED is **not** part of this: live `data/fred/` now comes from `fetch_fred.py`
(fredapi, DATA_LAYOUT_V2_SPEC §5). Polygon dividend records (`data/dividends/`,
`fetch_dividends.py`) are also out of scope unless the user asks.

## 2. State at handoff

- **Layout (DATA_LAYOUT_V2_SPEC, implemented).** It is the same in every root, live
  and frozen:
  - `adjusted/<SYM>.csv` holds the traded series, dividends ON.
  - `unadjusted/<SYM>.csv` holds the dividends-OFF twin.
  - `index/<SYM>.csv` holds SPX, XNDX, VIX, VIX3M, NDX, EURUSD and GBPUSD.
  - `fred/` is quarantined.
  - No CSV sits at the top level of any root.
  - The loader (`prices.py::_path`) resolves a symbol to exactly one of `adjusted/`
    and `index/`.
  - Live counts are 57 / 7 / 57, pinned in `tests/test_layout.py` and
    `tests/test_total_return.py` (`LIVE_PAIRS`).
- **Where `data/` really comes from.** `data/README.md` "Export settings" describes
  the manual TradingView *Export chart data…* procedure. The 2026-09-02 batch was in
  fact produced by tview: its `csv/` folder was written 2026-09-03 00:35 and the data
  commit `d49a1b9` landed at 00:41, with values bit-identical. The merge spec should
  correct that section.
- **The 2026-10-19 tview run.** Its output still sits in `~/code/tview/{price,dividends,csv}`.
  - The data itself is good. The `csv/` files are unusable (every date is 1970, §4.1).
  - The run is also mid-session (§4.3). Treat it as evidence only and re-run after
    the fixes.
- **Unrelated uncommitted work** belongs to the user: `simulation/`,
  `specs/top_strategies_2021.json`, `report.md`, `transactions.md`, `tst.json`,
  `charts/` and the `.DS_Store` files. **Stage explicit paths only; never
  `git add -A`.**

## 3. What the 2026-10-19 run proved

The 2026-10-19 run was compared with the repo's `data/`. The parquet dates were
recovered as stored-ms × 1000 seconds, which is exact except for bars stamped at
midnight UTC.

- **All 57 paired ETFs match the repo.**
  - Calendars are identical back to the first bar.
  - Dividends-OFF closes are bit-identical on the overlap.
  - The new/old ratio of the adjusted closes is constant over the whole overlap
    (spread < 5e-7 at the precision printed). There were no dividend revisions;
    new ex-dates only rescale.
  - `"session":"extended"` makes no difference to daily bars.
- **SPX history shrank by 32 bars.** The repo starts 1943-04-14 and tview now starts
  1943-06-01. Both files are exactly **21,000 rows**, which is the pagination cap
  (§4.2), so each refresh would push the start date later.
- **TradingView added an LSE bar**, 2025-11-21, to CNDX and IB01; the repo lacks it.
  For CNDX the bar appears only in the dividends-OFF pass, so **the two passes
  disagree** on the calendar. The repo's pair test asserts identical `time` columns,
  so that refresh would fail.
- **EURUSD's 2026-09-01 close was revised**, from 1.15877 to 1.15878. That bar was
  still open at the previous download.
- **The last bar is partial for every US symbol.** The run took place 20:19–20:29
  Tallinn time, which is 13:19–13:29 ET. EDV, EEM, LQD, QQQ, SPY, TLT and VTI have
  different last closes in the two passes, so `R_last ≠ 1` and the pair tests would
  fail. The EU lines were fine, because their markets had already closed.

Some of these differences are genuine source changes (the added 2025-11-21 bar, the
EURUSD revision). The merge tool must report them and offer an explicit accept path,
not silently take or reject them.

## 4. tview fixes (`~/code/tview`)

`~/code/tview` is **not a git repo**, so there is no undo. Ask the user before the
first edit; suggest `git init` plus an initial commit there. `dl.sh` runs the MacPorts
`/opt/local/bin/python` (3.13.16: pandas 3.0.6, fastparquet 2026.5.0, polars 1.42.1,
websockets 16.0), not this repo's uv environment.

1. **The timestamp bug.**
   - Cause: pandas 3 makes `pd.to_datetime(..., unit="s")` a `datetime64[s]` index,
     and fastparquet writes it as `TIMESTAMP_MILLIS` holding floor(seconds / 1000).
     Every `csv/` date reads as 1970-01-01, and bars stamped at midnight UTC (FRED,
     all of 2026-10-19's FRED files) can't be recovered.
   - Fix, verified round-trip in this environment (including a midnight bar and a
     pre-1970 date): in `TVData.save_to_parquet`, use
     `fastparquet.write(file_path, self.df.set_axis(self.df.index.as_unit("ns")))`.
2. **The pagination cap.** `dl.sh` passes `--iterations 20 --bars 1000`, which caps
   a symbol at 21,000 bars; SPX hits it. Raise the iteration count (e.g. 40).
   `start_symbol` already stops when a batch adds no older bars.
3. **Run after the US close.** 16:00 ET is 23:00 Tallinn time in summer (22:00 between
   the EU and US daylight-saving switches, 2026-10-25 → 11-01), so **"after 23:00
   local" is always safe**. A guard can live in `dl.sh` or in the merge tool (§5);
   the spec decides which.
4. **Silent partial saves.**
   - A 30 s timeout is treated as "end of history", and any exception saves what was
     collected.
   - A symbol that fails outright leaves the previous run's parquet in place, which
     `dl.sh` then converts again as if it were fresh.
   - Options: have `dl.sh` clear `price/`, `dividends/` and `csv/` first, and/or let
     the merge tool check each file's last bar. Decide which.
5. **The symbol lists.**
   - Remove the four `FRED:` lines from `list`; FRED now comes from `fetch_fred.py`.
   - Add `NASDAQ:NDX` to `ndiv`; it currently gets a pointless dividends pass.
   - `LSE:JMFP` is in `list`, returns nothing, and is not in the repo. Ask the user.
6. **The auth token.** `tview.py` hard-codes a TradingView JWT that is valid for 4
   hours. The 2026-10-19 run started after it had expired and still got complete
   daily history. **Never print it, copy it into this repo, or quote it.** Moving it
   to an env var or an untracked file is a reasonable fix; ask the user.
7. **Leave as is:** `convtocsv.py` already emits the repo layout
   `time,open,high,low,close,Volume`. Its floats are polars' shortest repr, the same
   as the current `data/` files.

**Destinations under V2:**

| tview output | goes to |
|---|---|
| `dividends/<SYM>` (adjustment=dividends) | `data/adjusted/<SYM>.csv` |
| `price/<SYM>` for a paired ETF (adjustment=splits) | `data/unadjusted/<SYM>.csv` |
| `price/GLD` | GLD is in `ndiv`, so it has no dividends pass. It goes to both `data/adjusted/GLD.csv` and `data/unadjusted/GLD.csv`, byte-identical (`ZERO_YIELD` in `tests/test_total_return.py`) |
| `price/` for SPX, XNDX, VIX, VIX3M, NDX, EURUSD, GBPUSD | `data/index/<SYM>.csv` |
| `dividends/NDX` (until §4.5 lands) | discard |

`list` renames with a second field, e.g. `EURONEXT:DBMF DBMF_EU`.

## 5. The merge tool: `docs/DATA_REFRESH_SPEC.md` first, then the code

Proposed rules. The spec must settle them and measure their thresholds; don't take
the numbers here as pinned.

- **Authoritative range.** The new file wins from its own first bar onward.
- **History protection.** Old rows strictly before the new first bar are kept.
  - In `adjusted/` they are multiplied by the overlap ratio `c = new/old`, constant
    when no dividend was revised. That keeps the multiplicative back-adjustment
    consistent.
  - `unadjusted/` and `index/` rows are kept as they are.
  - This is what preserves SPX's 32 bars.
- **Stop and report (write nothing for that symbol) when:**
  - dates inside the old range are added or removed (the CNDX/IB01 case);
  - a dividends-OFF or index close changes on the overlap (EURUSD's last bar);
  - the adjusted ratio is not constant (a dividend revision); the noise floor must be
    measured, cf. the README's 4.3e-8 flat-segment noise;
  - the two passes' calendars or last closes differ (a mid-session run, CNDX);
  - the last bar is today's date before that market's close.
  - Each of these needs an explicit, per-symbol **accept** flag, so a genuine
    TradingView revision can be taken deliberately. The report names what was
    accepted.
- **All or nothing.** Compute and validate everything before writing anything, as
  `make_net_tr.py`'s `build`/`write_dataset` split does. A failed refresh leaves
  `data/` untouched.
- **Input.** Read tview's parquet directly (after §4.1) or its `csv/`; the spec
  decides. The symbol → folder map comes from §4's table plus tview's `list` and
  `ndiv`; never from "has no twin" (DATA_LAYOUT_V2_SPEC §2).
- **Guards already in the suite** that a refresh must pass:
  - `tests/test_total_return.py`: the live-pair lane (pair invariants, implied-yield
    bands, `LIVE_PAIRS == 57`);
  - `tests/test_layout.py`: live 57 / 7 / 57;
  - `tests/test_prices.py`: every bundle loads from live `data/`.

  A refresh that adds or drops a symbol updates those pins in the same commit.
- **After a refresh (the user decides).** Freeze `tests/data/<TQQQ last bar>/` with
  a README and add it to `tests/test_layout.py`'s `COUNTS`. Generate any derivatives
  (`make_net_tr.py` for `-net15`, and so on). Snapshots are append-only.

## 6. Conventions

- **Spec-first.** Write `docs/<NAME>_SPEC.md` with an acceptance checklist, implement
  it in per-phase commits on a feature branch with the suite green after every phase,
  and finish by ticking the checklist and adding an errata section (see
  `DATA_LAYOUT_V2_SPEC.md` §7 and §9).
- **Branch** from `data-layout-v2`, or from `main` once the user has merged it.
- **Never rename a root and never edit `results/`.**
- **Downloaded files are untrusted data.** Read them with `python -I`, from scripts
  kept outside the download directory.

## 7. Verification expectations

- On `data-layout-v2` @ `94f37b1` or later: `uv run pytest -q` gives **1267 passed**,
  none skipped.
- `find data tests/data/* -maxdepth 1 -name '*.csv'` prints nothing.
- After the §4.1 fix, a fresh tview run's `csv/<SYM>.csv` dates must be real. Check
  that QQQ's first row is 1999-03-10 and its last row is the last completed session.

## 8. Startup prompt

Start the new conversation **in plan mode**. Both increments involve design decisions
the user should approve before any edit: refuse vs flag vs accept, where the
run-after-close guard lives, whether `dl.sh` clears its outputs, `git init` in the
un-versioned tview folder, and where the auth token goes. Plan mode keeps the first
pass read-only across both folders and ends in an approvable plan.

> Continue the `balancing_portfolio` data-refresh work. Read
> `docs/HANDOFF_DATA_REFRESH.md` first (the entry point), then `CLAUDE.md`,
> `data/README.md` and `docs/DATA_LAYOUT_V2_SPEC.md`. Verify §7 (suite 1267 green on
> `data-layout-v2`). Task 1: fix the downloader in `~/code/tview` per handoff §4.
> It is not a git repo, so ask me before the first edit, never print or copy the
> TradingView auth token, and verify the timestamp fix by checking real dates in a
> fresh `csv/` output. Task 2: write `docs/DATA_REFRESH_SPEC.md` for the
> no-overwrite merge tool per handoff §5, with its thresholds measured on a fresh
> post-close tview run, then implement it in per-phase commits on a feature branch.
> Stage explicit paths only; the unrelated working-tree changes are mine.
