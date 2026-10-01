# Specification: one self-describing layout for live and frozen data

Repo: `vlaas/balancing_portfolio` · baseline commit: `f1e4be3` ("Merge pull request #23", 1243 tests green, none skipped) · status: proposed

## 1. Goal

Whether a file carries distributions is not readable from its path today:

- Every dataset root keeps the dividends-ON (total-return) TradingView export at
  `<root>/<SYM>.csv` and the dividends-OFF twin at `<root>/price/<SYM>.csv`. Every
  file is a price series; `price/` does not say *which* toggle state it holds.
- The flat legacy set `tests/data/*.csv` is **dividends-OFF at the top level**, the
  exact inverse of every dated root beside it. TOTAL_RETURN_SPEC §3 kept it there
  because moving it "would touch every test file for zero benefit"; the benefit is
  that no directory needs a README to be read correctly.
- The FRED series sit in `macro/`, named after their content rather than their
  source, and the Polygon dividend records sit at the repo root in `dividends/`,
  outside every dataset.

Snapshots are frozen copies of live `data/` (`2026-08-24` and `2026-09-02` are
verbatim copies), so the fix is **one root layout**, shared by live `data/` and every
`tests/data/<name>/`. This spec renames folders; it changes no byte of data, no root
path and no engine code.

## 2. The root layout — normative

A **root** is a directory the loader is pointed at (`--data <root>`). Live `data/` is
the undated root; `tests/data/<name>/` are frozen ones.

```
<root>/
  README.md
  <SYM>.csv        ETF: the dividends-ON (total-return) export — the traded series
                   index / FX: the single series (no adjustment toggle)
  unadjusted/      ETF: the dividends-OFF export, same session — reference only
  fred/            FRED macro series — quarantined, never loaded (ROTATION_SPEC §3.3)
  dividends/       Polygon dividend records + pre_polygon/ — reference only
  fx_lines.json    the make_usd.py line map (live root)
```

- The loader is unchanged: it reads `<root>/<SYM>.csv` and nothing else, so
  `unadjusted/`, `fred/` and `dividends/` are unreachable from a spec by
  construction.
- Every folder is optional. A generated root (`make_net_tr.py`, `make_usd.py`,
  `make_haircut.py`, `make_synthetic.py`) holds the top-level files, `unadjusted/`
  where its parent has twins, and its README; generators glob the root only.
- Freezing copies `data/` verbatim, so a future snapshot carries `dividends/` and
  `fx_lines.json`; the existing snapshots predate both and stay as they are.

## 3. What moves

| old path | new path |
|---|---|
| `<root>/price/<SYM>.csv` (live `data/` and all 11 dated roots) | `<root>/unadjusted/<SYM>.csv` |
| `<root>/macro/` (`data/`, `tests/data/2026-08-24/`, `tests/data/2026-09-02/`) | `<root>/fred/` |
| `tests/data/<SYM>.csv` (the flat 2026-08-14 set: BTAL, DBMF, KMLM, QQQ, SPY, TQQQ) | `tests/data/2026-08-14-unadjusted/<SYM>.csv` |
| `dividends/` (repo root, with `pre_polygon/`) | `data/dividends/` |

**Every root path stays as it is.** Committed artefacts record roots
(`run.data_dir`, sweep `data_dir`, `summary.json` `data.dir`, the episode and
overlap reports) and never a subfolder, so every committed result stays valid with
no edit under `results/`.

**Older specs and `notes/` keep their wording**; read them through this table.
Clauses whose paths it replaces:

- TOTAL_RETURN_SPEC §3 (`<DIR>/price/`, the flat set staying in place, the `-price`
  suffix) and §6 (export step 2) — see its erratum.
- ROTATION_SPEC §3.2–§3.3 (`data/price/`, the `data/macro/` quarantine — the
  quarantine itself stands, under `fred/`).
- NET_TR_SPEC §3 (`SRC/price/*.csv → DST/price/`).
- SYNTHETIC_HISTORY_SPEC §3 (`GROSS/macro/DTB3.csv`, `price/` without twins) and
  erratum 7's `dividends/pre_polygon/`.
- EU_SUBSTITUTE_SPEC §3 and §6.3 (`price/` twins and their handling in
  `make_usd.py` / `make_haircut.py`).
- CASH_SLEEVE_SPEC B1 (`dividends/BIL.parquet`).

## 4. Root names — normative

The rules are spread over data/README, TOTAL_RETURN_SPEC §3, NET_TR_SPEC §4,
SYNTHETIC_HISTORY_SPEC erratum 1, EU_SUBSTITUTE_SPEC §3.6/§6.3 and CASH_SLEEVE_SPEC
§10.5; collected here:

```
<date>[-syn][-netNN[-<sym>NN]...][-usd][-hc]      top level dividends-ON (or derived from it)
<date>-unadjusted                                 top level dividends-OFF
```

| part | meaning | written by |
|---|---|---|
| `<date>` | last bar of the root's TQQQ export | the freeze |
| `-syn` | TQQQ and BIL extended backward by a model | `make_synthetic.py` (inserted before `-net`) |
| `-netNN` | distributions net of NN % withholding | `make_net_tr.py` |
| `-<sym>NN` | per-symbol withholding override, e.g. `-bil0` | `make_net_tr.py --rate-override` |
| `-usd` | non-USD lines converted to USD | `make_usd.py` |
| `-hc` | US symbols haircut toward their EU substitutes | `make_haircut.py` |
| `-unadjusted` | the top-level files are the dividends-OFF export | the freeze; replaces the reserved `-price` |

`<date>` must stay a pure ISO date for the gross roots
(`tests/test_total_return.py` parses it), and code keys on `-net` in a name
(`make_synthetic.py`, `overlap_report.py`, `tests/test_indicators.py`); `-unadjusted`
contains neither.

## 5. Code and test changes

- Generators: the `"price"` path segment becomes `"unadjusted"` and `"macro"` becomes
  `"fred"` in `make_net_tr.py`, `make_usd.py`, `make_haircut.py`, `make_synthetic.py`,
  including their README templates. The generated READMEs of the eight derived roots
  are regenerated by the committed generators with their original arguments, and the
  regeneration must leave every CSV byte-identical.
- `fetch_dividends.py`, `extend_dividends.py`: `OUT_DIR = Path("data/dividends")`.
- Tests: the same renames; `GOLDEN_DIR` points at `tests/data/2026-08-14-unadjusted`
  in the modules that load the flat set, and their dated roots hang off a
  `DATA = tests/data` base. Modules that use `GOLDEN_DIR` only as that base keep it.
- Untouched: `prices.py`, `simulate.py`, `strategy.py`, `spec.py`, `sweep.py`,
  `results_json.py`, every spec and every result.

## 6. Acceptance checklist

- [ ] `price/` → `unadjusted/` in `data/` and the 11 dated roots; `macro/` → `fred/`
      in `data/`, `2026-08-24`, `2026-09-02`
- [ ] The four generators read and write the new names; the eight generated READMEs
      regenerated by them, every CSV byte-identical
- [ ] Flat set at `tests/data/2026-08-14-unadjusted/` with a README; `GOLDEN` and
      `COST_GOLDEN` unchanged
- [ ] `data/dividends/`; `fetch_dividends.py`, `extend_dividends.py` and
      `tests/test_cash_sleeve.py` read it there
- [ ] SHA-256 manifest: every CSV and parquet byte-identical under the §3 map, no
      file lost or added
- [ ] Suite: the baseline's passed and skipped counts and skip reasons
- [ ] Zero changes under `results/`; a committed `main.py` result reproduces
      byte-for-byte on its recorded root
- [ ] Docs: `data/README.md` (opening table, export procedure, snapshot list),
      ARCHITECTURE, STRATEGY_DEVELOPMENT, README, CLAUDE.md; erratum in
      TOTAL_RETURN_SPEC §3

## 7. Deliberately not in scope

- Renaming any root. 292 committed results record a root as `data_dir`, and a
  results file is never edited by hand.
- Giving indices and FX their own folders: the loader resolves one directory per
  root, and splitting it is a loader change for a naming gain.
- Rewriting older specs or notes (§3 is their decoder).
- The untracked top-level `adjusted/` and `price/` folders (the staging copy of the
  `2026-08-20` export), left to the operator.
- A shared test-constants module.
