# Specification: one folder per series class in every data root

Repo: `vlaas/balancing_portfolio` · baseline commit: `bd843ac` ("Merge pull request #24", 1243 tests green, none skipped) · status: draft

## 1. Goal

DATA_LAYOUT_SPEC gave the dividends-OFF twin its own folder (`unadjusted/`) but left
three different kinds of file side by side at the top of every root:

- the dividends-ON (total-return) ETF exports the simulator trades,
- the single series with no dividend toggle — the indices SPX, XNDX, VIX, VIX3M,
  NDX and the FX singles EURUSD, GBPUSD,
- the modelled or derived traded series of a generated root (net-TR closes,
  synthetic TQQQ/BIL, USD-converted EU lines, the haircut TQQQ).

The downloader (`~/code/tview/dl.sh`) produces exactly two passes per ETF —
`adjustment=dividends` and `adjustment=splits` — and one pass per single series; a
refresh, and the no-overwrite merge tool that will perform it, should map each pass
onto one folder without consulting a symbol list. This spec gives every series class
its own folder. It **reverses DATA_LAYOUT_SPEC §7's second bullet** ("Giving indices
and FX their own folders … a loader change for a naming gain"): the gain is that a
file's class is readable from its path in every root, which is what the refresh
needs.

It also switches the live FRED series to a checked-in `fredapi` fetch (§5); the
frozen roots' `fred/` stay as committed.

This spec moves files; it changes no byte of any CSV in a frozen root, no root path,
no engine code (`simulate.py`, `strategy.py`) and no result.

## 2. The root layout — normative

```
<root>/
  README.md
  adjusted/<SYM>.csv     every series the simulator trades, in the root's convention:
                         the dividends-ON ETF export, or the net-TR / synthetic /
                         USD-converted / haircut series a generator derived from it
  unadjusted/<SYM>.csv   ETF: the dividends-OFF export, same session — reference only
  index/<SYM>.csv        no dividend toggle: SPX XNDX VIX VIX3M NDX, FX EURUSD GBPUSD
  fred/                  FRED macro series — quarantined, never loaded (ROTATION_SPEC §3.3)
  dividends/             Polygon dividend records + pre_polygon/ — reference only (live)
  fx_lines.json          the make_usd.py line map (live)
```

- **No CSV sits at the top level of any root.**
- **The loader's rule** (`prices.py`): a root's *series folder* is `adjusted/` if the
  root has one, else `unadjusted/` (a price-only root, §4). A symbol resolves to
  exactly one of `<series folder>/<SYM>.csv` or `index/<SYM>.csv`; neither is a
  `FileNotFoundError` naming the symbol, both is a `ValueError`. This holds for traded
  symbols, `extra` symbols and cross-symbol indicator `inputs` alike. `fred/` and
  `dividends/` stay unreachable from a spec by construction.
- **A file's class is its folder.** Generators classify by folder, never by whether a
  twin exists: the old "no `unadjusted/` twin ⇒ index" rule would misfile the modelled
  series, which have no twin either.
- Every folder is optional. A generated root holds `adjusted/`, `index/` (copied
  verbatim from its parent), `unadjusted/` where its parent has twins, and its README;
  `fred/` is never copied.

## 3. What moves

| old path | new path |
|---|---|
| `<root>/<SYM>.csv`, SYM ∈ {SPX, XNDX, VIX, VIX3M, NDX, EURUSD, GBPUSD} | `<root>/index/<SYM>.csv` |
| `tests/data/2026-08-14-unadjusted/<SYM>.csv` (the price-only flat set) | `tests/data/2026-08-14-unadjusted/unadjusted/<SYM>.csv` |
| every other `<root>/<SYM>.csv` | `<root>/adjusted/<SYM>.csv` |

The class of a file is decided by the explicit index set above, never by the absence
of a twin. 602 files move; per root (adjusted / index / unadjusted after the move):

| root | adjusted | index | unadjusted |
|---|---|---|---|
| `data` | 57 | 7 | 57 |
| `2026-08-14-unadjusted` | — | — | 6 |
| `2026-08-20`, `-net15` | 6 | 2 (VIX VIX3M) | 6 |
| `2026-08-24`, `-net15`, `-net15-bil0` | 48 | 4 (SPX VIX VIX3M XNDX) | 48 |
| `2026-08-24-syn`, `-syn-net15` | 48 | 4 | 46 |
| `2026-09-02`, `-net15` | 57 | 7 | 57 |
| `2026-09-02-net15-usd` | 57 | 7 | 53 |
| `2026-09-02-net15-usd-hc` | 57 | 7 | 52 |

**Every root path stays as it is**, so every `data_dir` recorded under `results/`
stays valid.

**Older specs and `notes/` keep their wording**; read their `<root>/<SYM>.csv` through
this table. Clauses it replaces: DATA_LAYOUT_SPEC §2, §4 (the `-unadjusted` row) and
§7 (second bullet) — see its erratum 4; NET_TR_SPEC §3; SYNTHETIC_HISTORY_SPEC §3;
EU_SUBSTITUTE_SPEC §3.5 and §6.3; ROTATION_SPEC §3.2–§3.4; REGIME_SPEC §2.2 (an
index is now a file in `index/`, not a top-level file without a twin).

## 4. Root names

The grammar of DATA_LAYOUT_SPEC §4 stands. One row is restated:

| part | meaning |
|---|---|
| `-unadjusted` | the root has no `adjusted/`; its series folder is `unadjusted/` (the dividends-OFF export) |

## 5. FRED via `fredapi`

`fetch_fred.py` (new, repo root; precedent `fetch_dividends.py` — a checked-in fetch
script producing committed CSVs, never a runtime dependency, SAFE_SWAP_SPEC):

- Run: `FRED_API_KEY=… uv run --with fredapi fetch_fred.py`. `fredapi` is not a
  project dependency.
- Series UNRATE, RRSFS, INDPRO, DTB3, written to `data/fred/<SID>.csv` as `time,close`:
  ISO `YYYY-MM-DD`, ascending, unique, no nulls. FRED's missing observations (bank
  holidays, the 2025-10 shutdown months) are dropped, as in the TradingView copies;
  `make_synthetic.py` requires it (`time`/`close` columns, string-compared ISO dates,
  no nulls).
- Units and values are FRED's own, latest vintage: RRSFS is in millions (the
  TradingView copy carried it ×10⁶). Vintages and availability dates remain
  MACRO_DATA_SPEC's.
- Only live `data/fred/` is rewritten. `tests/data/2026-08-24/fred/` and
  `tests/data/2026-09-02/fred/` stay TradingView-sourced and byte-identical, so no
  pinned number moves.

## 6. Code and test changes

- **`prices.py`**: `_read_close` resolves its file by §2's rule. Nothing else in the
  loader changes; the reports that import `_read_close` inherit it.
- **Generators** — classify by folder, copy `index/` verbatim, never copy `fred/`:
  - `make_net_tr.py`: nets every `adjusted/` file against its `unadjusted/` twin and
    lists `index/` files as `index` in its table (symbols sorted over both folders, so
    the table order is unchanged). An `adjusted/` file without a twin is now an error
    (it was copied and labelled `index`); no committed root is derived that way.
  - `make_usd.py`: mapped symbols must be in `adjusted/`, their FX series in `index/`.
  - `make_haircut.py`: mapped symbols must be in `adjusted/`.
  - `make_synthetic.py`: reads `adjusted/` (parent TQQQ/BIL; gross QQQ, SPY),
    `unadjusted/QQQ` and `fred/DTB3` from the gross root; writes the spliced series to
    `adjusted/` and copies `index/`.
  - README templates and docstrings name the folders. The eight generated READMEs are
    regenerated with their original arguments; every regenerated CSV is byte-identical
    to the moved one.
- **Tests**: paths follow §3; top-level counts become per-folder counts (§3 table);
  temp-root fixtures write `adjusted/` and `index/`. New: loader resolution (index
  input for an adjusted host, both folders, price-only root, no fallback when
  `adjusted/` exists); `make_net_tr` refuses an unpaired `adjusted/` file; a layout
  test over all 13 roots (no top-level CSV, `adjusted/` ∩ `index/` = ∅, `index/` ⊆
  the index set, the §3 counts); `tests/test_fred.py` on live `data/fred/`.

## 7. Acceptance checklist

- [ ] The repo-root staging folders `adjusted/` and `price/` deleted (all 12 files
      byte-identical to `tests/data/2026-08-20/` and its `unadjusted/`)
- [ ] §3 applied to `data/` and the 12 frozen roots; no top-level CSV anywhere
- [ ] `prices.py` resolves by §2; the four generators classify by folder; the eight
      generated READMEs regenerated, every CSV byte-identical
- [ ] SHA-256 manifest: every CSV, parquet and JSON of the baseline maps one-to-one
      under §3; only READMEs (and, after §5, the four live FRED files) differ
- [ ] Suite: the baseline's 1243 plus the new tests pass, none skipped
- [ ] Zero changes under `results/`; five committed `main.py` results (`comp_points`,
      `comp_points_tr`, `eu_points_2021_hc`, `syn_points`, `regime_confirm_2012`)
      reproduce on their recorded roots except `generated_at`/`git_sha`/`git_dirty`
- [ ] `fetch_fred.py` committed with its output; DTB3 agrees with the frozen
      TradingView copy on common dates
- [ ] Docs: `data/README.md`, the four hand-written root READMEs, `README.md`,
      ARCHITECTURE, STRATEGY_DEVELOPMENT; erratum 4 in DATA_LAYOUT_SPEC

## 8. Deliberately not in scope

- Renaming any root, editing any result, rewriting older specs or notes (§3 is their
  decoder).
- The tview fixes (timestamp bug, pagination cap, run-after-close, FRED lines in its
  `list`) and the no-overwrite merge tool — the next specs, which build on §2.
- FRED vintages and availability dates (MACRO_DATA_SPEC).

## 9. Errata (implementation)

(none yet)
