"""Convert the non-USD lines of a dataset root into USD.

Reads a dataset root in the TOTAL_RETURN_SPEC §3 convention and the committed
line map `data/fx_lines.json` (EU_SUBSTITUTE_SPEC §3.5): for every mapped
symbol the close is multiplied by the same-date close of its FX series and by
a per-line scale (1 for a EUR line, 0.01 for a GBX line quoted in pence). The
FX series is read from the root itself — it is an index-class single series
that every generator byte-copies — and forward-filled onto the symbol's own
calendar, so the snapshot stays reproducible from committed inputs alone. The
~1 h offset between the Xetra/LSE close and the 17:00 New York FX stamp is
accepted and documented. Every other file is byte-copied. A converted
`<SYM>.csv` carries `time,close` only and has no `price/` twin: a converted
series has no unadjusted twin in its trading currency, and the parent keeps
the original. Deterministic by construction — no clock, no environment — so
the committed snapshot is byte-reproducible from the committed parent and
this script (T2).

Run: uv run make_usd.py tests/data/2026-09-02-net15 [--map data/fx_lines.json]
     [--out DIR] [--force]
"""

import argparse
import json
import shutil
from pathlib import Path

import polars as pl


def read_close(path: Path) -> tuple[list[str], list[float]]:
    """One CSV as (time, close). `time` is read as a string and passed through
    untouched so a converted file carries identical date values."""
    frame = pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"time": pl.String, "close": pl.Float64},
    )
    return frame["time"].to_list(), frame["close"].to_list()


def load_map(path: Path) -> dict[str, tuple[str, float]]:
    """`{SYM: {"fx": FXSYM, "scale": s}}` — both keys required, s > 0."""
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: the line map must be a JSON object")
    fx_map = {}
    for symbol, entry in raw.items():
        if not isinstance(entry, dict) or set(entry) != {"fx", "scale"}:
            raise ValueError(f'{path}: {symbol} wants {{"fx": SYM, "scale": s}}')
        fx, scale = entry["fx"], entry["scale"]
        if not isinstance(fx, str) or not fx:
            raise ValueError(f"{path}: {symbol} fx must be a symbol name")
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or scale <= 0:
            raise ValueError(f"{path}: {symbol} scale must be a positive number")
        fx_map[symbol] = (fx, float(scale))
    return fx_map


def fx_on(symbol: str, fx_times: list[str], fx_values: list[float],
          times: list[str]) -> tuple[list[float], int]:
    """The FX close carried onto `times` (same-date, else the latest earlier
    bar) and the count of bars that took an earlier bar's rate. ISO dates
    compare as strings. A bar before the FX series begins is a hard error."""
    if any(b <= a for a, b in zip(fx_times, fx_times[1:])):
        raise ValueError(f"{symbol}: FX series is not strictly ascending")
    filled, stale, i, last, last_time = [], 0, 0, None, None
    for time in times:
        while i < len(fx_times) and fx_times[i] <= time:
            last, last_time = fx_values[i], fx_times[i]
            i += 1
        if last is None:
            raise ValueError(f"{symbol} {time}: no FX bar on or before this date")
        filled.append(last)
        stale += last_time != time
    return filled, stale


def build(src: Path, fx_map: dict[str, tuple[str, float]]) -> dict:
    """Read and convert every mapped symbol under src. All computation and
    validation happen here, before anything is written — a hard error can
    never leave a partial dataset behind."""
    symbols = sorted(path.stem for path in src.glob("*.csv"))
    if not symbols:
        raise ValueError(f"{src}: no <SYM>.csv files found")
    unknown = sorted(set(fx_map) - set(symbols))
    if unknown:
        raise ValueError(f"{src}: the line map names absent symbols {unknown}")
    converted = {}
    for symbol, (fx, scale) in sorted(fx_map.items()):
        if fx not in symbols:
            raise ValueError(f"{symbol}: FX series {fx} not in {src}")
        times, closes = read_close(src / f"{symbol}.csv")
        rate, stale = fx_on(symbol, *read_close(src / f"{fx}.csv"), times)
        converted[symbol] = {
            "times": times,
            "close": [c * r * scale for c, r in zip(closes, rate)],
            "fx": fx,
            "scale": scale,
            "stale": stale,
            "first_rate": rate[0],
            "last_rate": rate[-1],
        }
    return {
        "symbols": symbols,
        "pairs": sorted(path.stem for path in (src / "price").glob("*.csv")),
        "converted": converted,
    }


def _table(results: dict) -> list[str]:
    lines = [
        "| symbol | fx | scale | bars | stale FX bars | first rate | last rate |",
        "|---|---|---|---|---|---|---|",
    ]
    for symbol, r in results["converted"].items():
        lines.append(
            f"| {symbol} | {r['fx']} | {r['scale']:g} | {len(r['times'])} | {r['stale']} "
            f"| {r['first_rate']!r} | {r['last_rate']!r} |"
        )
    return lines


def render_readme(parent: str, results: dict) -> str:
    """The snapshot README. References the parent by directory basename and
    carries no timestamps — T2 regenerates into a temp directory and
    byte-compares."""
    lines = [
        f"# USD-converted snapshot — {parent}-usd",
        "",
        f"Derived from the frozen `{parent}` snapshot by `make_usd.py`",
        "(EU_SUBSTITUTE_SPEC §3.5): each mapped symbol's close is multiplied by",
        "the same-date close of its FX series (read from the parent root,",
        "forward-filled onto the symbol's own calendar — a bar with no FX bar",
        "on its date takes the latest earlier one, counted as stale below) and by",
        "the line's scale (1 for a EUR line, 0.01 for a GBX line quoted in",
        "pence). The ~1 h offset between the Xetra/LSE close and the 17:00 New",
        "York FX stamp is accepted. A converted `<SYM>.csv` carries `time,close`",
        "only and has no `price/` twin — a converted series has no unadjusted",
        "twin in its trading currency; the parent keeps the original. Every",
        "other file, `price/` twins included, is byte-copied from the parent.",
        "",
    ]
    return "\n".join(lines + _table(results)) + "\n"


def write_dataset(dst: Path, src: Path, results: dict, readme: str) -> None:
    (dst / "price").mkdir(parents=True, exist_ok=True)
    converted = results["converted"]
    for symbol in results["symbols"]:
        if symbol in converted:
            r = converted[symbol]
            rows = "\n".join(f"{t},{c!r}" for t, c in zip(r["times"], r["close"]))
            (dst / f"{symbol}.csv").write_text(f"time,close\n{rows}\n")
        else:
            shutil.copyfile(src / f"{symbol}.csv", dst / f"{symbol}.csv")
    for symbol in results["pairs"]:
        if symbol in converted:
            continue  # a converted series has no unadjusted twin
        shutil.copyfile(src / "price" / f"{symbol}.csv", dst / "price" / f"{symbol}.csv")
    (dst / "README.md").write_text(readme)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "src", type=Path,
        help="parent dataset root in the TOTAL_RETURN_SPEC §3 convention",
    )
    parser.add_argument(
        "--map", type=Path, default=Path("data/fx_lines.json"),
        help="the line map (default: data/fx_lines.json)",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="output dataset root (default: <SRC>-usd)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="write into an existing --out directory",
    )
    args = parser.parse_args(argv)

    dst = args.out or args.src.with_name(f"{args.src.name}-usd")
    if dst.exists() and not args.force:
        parser.error(f"{dst} exists; pass --force to overwrite")

    results = build(args.src, load_map(args.map))
    write_dataset(dst, args.src, results, render_readme(args.src.name, results))

    print("\n".join(_table(results)))
    print(f"Saved {dst}")


if __name__ == "__main__":
    main()
