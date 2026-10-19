"""Merge a tview batch into live `data/` without losing history (DATA_REFRESH_SPEC).

Reads the `csv/` output of `~/code/tview/dl.sh` together with its `list`, `ndiv`
and `started` stamp, and updates `data/adjusted/`, `data/unadjusted/` and
`data/index/` (DATA_LAYOUT_V2_SPEC §2). A symbol's class is the folder it already
has in `data/`; a symbol `data/` does not hold is refused, never guessed.

Per symbol (§3): bars that had not closed when the run started are trimmed;
the new file wins from its own first bar; older rows are kept (an `adjusted/`
row rescaled by the overlap ratio). Rows the batch serves before `data/`'s
first bar, and any revision of the history `data/` already holds, are taken
only for a symbol named in `--accept` — a revision stops the refresh without
it; a broken batch stops it outright. Everything is validated before anything
is written, and nothing is written without `--write` (§4).

Run: uv run refresh_data.py [TVIEW_DIR] [--data DIR] [--accept SYM ...] [--write]
"""

import argparse
import datetime as dt
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

HEADER = "time,open,high,low,close,Volume"

# §3.3 — when the bar dated D is final, per TradingView exchange prefix:
# (zone, local time, days after D). An FX_IDC bar opens at 22:00 UTC on its
# label date, summer and winter alike (§2.3), and closes 24 h later.
CLOSES = {
    "AMEX": ("America/New_York", dt.time(16, 0), 0),
    "NASDAQ": ("America/New_York", dt.time(16, 0), 0),
    "SP": ("America/New_York", dt.time(16, 0), 0),
    "CBOE": ("America/New_York", dt.time(16, 15), 0),
    "LSE": ("Europe/London", dt.time(16, 35), 0),
    "XETR": ("Europe/Berlin", dt.time(17, 35), 0),
    "EURONEXT": ("Europe/Paris", dt.time(17, 35), 0),
    "FX_IDC": ("UTC", dt.time(22, 0), 1),
}

# §3.5 V3 — largest spread of ln(new/old) over an adjusted overlap that still
# counts as one constant rescale. Measured worst 1.91e-7 (BND, §2.4), pinned one
# order above its magnitude — the suite's TAU — and 12x below the smallest
# genuine distribution jump (1.247e-5), so a revised dividend cannot hide in it.
LN_C_SPREAD_MAX = 1e-6


@dataclass
class Series:
    """One CSV file: the header and its (date, line) rows, ascending."""
    header: str
    rows: list[tuple[str, str]]

    @property
    def dates(self) -> list[str]:
        return [d for d, _ in self.rows]

    def close(self, i: int) -> float:
        return float(self.rows[i][1].split(",")[4])


@dataclass
class Plan:
    symbol: str
    accepted: bool = False
    cls: str = ""
    files: dict[str, str] = field(default_factory=dict)  # folder -> merged text
    notes: list[str] = field(default_factory=list)
    revisions: list[str] = field(default_factory=list)
    extended: bool = False  # the batch serves rows before data/'s first bar
    stops: list[str] = field(default_factory=list)


def read_series(path: Path) -> Series:
    header, *lines = path.read_text().splitlines()
    return Series(header, [(line.split(",", 1)[0], line) for line in lines if line])


def read_batch(tview: Path) -> tuple[dt.datetime, list[tuple[str, str, bool]]]:
    """The run's UTC start and its (symbol, market, single-pass) entries.

    `list` lines are `MARKET:TICKER [RENAME]`; a line in `ndiv` had no
    dividends pass."""
    started = dt.datetime.fromisoformat((tview / "started").read_text().strip())
    ndiv = {line.strip() for line in (tview / "ndiv").read_text().splitlines() if line.strip()}
    entries = []
    for line in (tview / "list").read_text().splitlines():
        if not line.strip():
            continue
        tv_symbol, *rename = line.split()
        market, ticker = tv_symbol.split(":")
        entries.append((rename[0] if rename else ticker, market, tv_symbol in ndiv))
    return started, entries


def closes_at(market: str, date: str) -> dt.datetime:
    zone, local, days = CLOSES[market]
    day = dt.date.fromisoformat(date) + dt.timedelta(days=days)
    return dt.datetime.combine(day, local, ZoneInfo(zone))


def trim(series: Series, market: str, started: dt.datetime) -> tuple[Series, list[str]]:
    """Drop the trailing bars that had not closed when the run started (§3.1)."""
    rows = list(series.rows)
    trimmed = []
    while rows and closes_at(market, rows[-1][0]) > started:
        trimmed.append(rows.pop()[0])
    return Series(series.header, rows), trimmed


def rescale(line: str, c: float) -> str:
    """An adjusted row with open/high/low/close multiplied by c (§3.2)."""
    date, *prices, volume = line.split(",")
    return ",".join([date, *(repr(float(v) * c) for v in prices), volume])


def merge(plan: Plan, folder: str, old: Series, new: Series) -> None:
    """Validate one new file against its `data/` predecessor and stage the
    merged text in plan.files[folder] (§3.2–§3.3)."""
    if new.dates[-1] < old.dates[-1]:
        plan.stops.append(f"{folder}: batch ends {new.dates[-1]}, before data/'s {old.dates[-1]}")
        return
    earlier = sum(1 for d in new.dates if d < old.dates[0])
    if earlier:
        plan.extended = True
        if plan.accepted:
            plan.notes.append(f"{folder}: took {earlier} rows before data/'s first bar {old.dates[0]}")
        else:
            new = Series(new.header, new.rows[earlier:])
            plan.notes.append(f"{folder}: skipped {earlier} rows before data/'s first bar"
                              f" {old.dates[0]} (--accept {plan.symbol} takes them)")
    first = new.dates[0]
    old_index = {d: i for i, d in enumerate(old.dates)}
    new_index = {d: i for i, d in enumerate(new.dates)}
    lo = max(old.dates[0], first)
    old_span = {d for d in old.dates if d >= lo}
    new_span = {d for d in new.dates if lo <= d <= old.dates[-1]}
    if old_span != new_span:
        added, removed = sorted(new_span - old_span), sorted(old_span - new_span)
        plan.revisions.append(f"{folder}: calendar +{added} -{removed}")
    common = sorted(old_span & new_span)
    if not common:
        plan.stops.append(f"{folder}: no date in common with data/")
        return
    if folder == "adjusted":
        ln_c = [math.log(new.close(new_index[d]) / old.close(old_index[d])) for d in common]
        spread = max(ln_c) - min(ln_c)
        if spread > LN_C_SPREAD_MAX:
            plan.revisions.append(f"adjusted: ratio not constant (ln spread {spread:.3g})")
    else:
        changed = [d for d in common if new.close(new_index[d]) != old.close(old_index[d])]
        if changed:
            plan.revisions.append(f"{folder}: close changed on {len(changed)} dates ({changed[-1]} last)")
    kept = [line for d, line in old.rows if d < first]
    if kept and folder == "adjusted":
        c = new.close(new_index[common[0]]) / old.close(old_index[common[0]])
        kept = [rescale(line, c) for line in kept]
    if kept:
        plan.notes.append(f"{folder}: kept {len(kept)} rows before {first}")
    lines = [HEADER, *kept, *(line for _, line in new.rows)]
    plan.files[folder] = "\n".join(lines) + "\n"


def plan_symbol(symbol: str, market: str, single: bool, started: dt.datetime,
                tview: Path, data: Path, accepted: bool) -> Plan:
    plan = Plan(symbol, accepted)
    if (data / "index" / f"{symbol}.csv").exists():
        plan.cls, sources = "index", {"index": "price"}
    elif (data / "adjusted" / f"{symbol}.csv").exists():
        plan.cls = "paired"
        sources = {"adjusted": "price" if single else "dividends", "unadjusted": "price"}
    else:
        plan.stops.append("not in data/ — add a new symbol by hand (§3.4)")
        return plan
    if market not in CLOSES:
        plan.stops.append(f"no market close for {market} (§3.1)")
        return plan

    new = {}
    for folder, source in sources.items():
        path = tview / "csv" / source / f"{symbol}.csv"
        if not path.exists():
            plan.stops.append(f"{folder}: no {path.relative_to(tview)}")
            continue
        series = read_series(path)
        if series.header != HEADER:
            plan.stops.append(f"{folder}: header {series.header!r}")
            continue
        if series.dates != sorted(set(series.dates)):
            plan.stops.append(f"{folder}: dates not ascending and unique")
            continue
        series, trimmed = trim(series, market, started)
        if trimmed:
            plan.notes.append(f"{folder}: trimmed unclosed {trimmed}")
        if not series.rows:
            plan.stops.append(f"{folder}: no closed bars")
            continue
        new[folder] = series
    if plan.stops:
        return plan

    if plan.cls == "paired":
        a, p = new["adjusted"], new["unadjusted"]
        if a.dates != p.dates:
            plan.stops.append("the two passes' calendars differ")
            return plan
        if a.close(-1) != p.close(-1):
            plan.stops.append(f"the two passes' last closes differ (R_last {a.close(-1) / p.close(-1)!r})")
            return plan

    for folder, series in new.items():
        old = read_series(data / folder / f"{symbol}.csv")
        if old.header != HEADER:
            plan.stops.append(f"{folder}: data/ header {old.header!r}")
            return plan
        merge(plan, folder, old, series)
    return plan


def build(tview: Path, data: Path, accept: set[str]) -> tuple[list[Plan], list[str]]:
    """Plan every symbol of the batch. All validation happens here, before
    anything is written (§4). Returns the plans and the run-level stops."""
    started, entries = read_batch(tview)
    plans = [plan_symbol(s, m, single, started, tview, data, s in accept) for s, m, single in entries]
    for plan in plans:
        if plan.revisions and not plan.accepted:
            plan.stops.append(f"revision not accepted (--accept {plan.symbol})")
    stops = []
    listed = {plan.symbol for plan in plans}
    for symbol in sorted(accept - {plan.symbol for plan in plans if plan.revisions or plan.extended}):
        stops.append(f"--accept {symbol}: nothing to accept")
    held = {p.stem for folder in ("adjusted", "index") for p in (data / folder).glob("*.csv")}
    for symbol in sorted(held - listed):
        stops.append(f"{symbol}: in data/ but not in the batch's list")
    return plans, stops


def report(plans: list[Plan], stops: list[str], data: Path) -> list[str]:
    lines = []
    for plan in plans:
        status = "STOP" if plan.stops else ("accepted" if plan.accepted else "ok")
        changed = [f for f, text in plan.files.items()
                   if (data / f / f"{plan.symbol}.csv").read_text() != text]
        lines.append(f"{plan.symbol:8} {plan.cls:7} {status:8} changes: {', '.join(changed) or '—'}")
        for item in plan.revisions:
            lines.append(f"    revision: {item}")
        for item in plan.notes:
            lines.append(f"    {item}")
        for item in plan.stops:
            lines.append(f"    STOP: {item}")
    lines += [f"STOP: {item}" for item in stops]
    return lines


def write(plans: list[Plan], data: Path) -> int:
    written = 0
    for plan in plans:
        for folder, text in plan.files.items():
            path = data / folder / f"{plan.symbol}.csv"
            if path.read_text() != text:
                path.write_text(text)
                written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tview", type=Path, nargs="?", default=Path.home() / "code" / "tview",
                        help="the tview folder (default: ~/code/tview)")
    parser.add_argument("--data", type=Path, default=Path("data"), help="live root (default: data)")
    parser.add_argument("--accept", action="append", default=[], metavar="SYM",
                        help="take this symbol's reported revisions, repeatable")
    parser.add_argument("--write", action="store_true", help="write the merged files")
    args = parser.parse_args(argv)

    plans, stops = build(args.tview, args.data, set(args.accept))
    print("\n".join(report(plans, stops, args.data)))
    if stops or any(plan.stops for plan in plans):
        print("Refused: nothing written.")
        return 1
    if not args.write:
        print("Dry run: nothing written; pass --write to apply.")
        return 0
    print(f"Wrote {write(plans, args.data)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
