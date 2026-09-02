"""Compound a haircut into the carried US symbols of a dataset root.

Reads a dataset root in the TOTAL_RETURN_SPEC §3 convention and the pinned
haircut map `results/overlap_eu/haircuts.json` (EU_SUBSTITUTE_SPEC §4.3,
`{US_SYMBOL: h}` in %/yr): for every mapped symbol with h > 0 the close is
compounded down by h/252 per bar from the symbol's first bar in the root —
`close'_t = close_t * (1 - h/100/252) ** k`, k bars since the first — so a
haircut lane (§6.3) measures the translation cost of a substitutable
component on the winner's own window. A symbol with h = 0 takes the byte-copy
path, so the no-contamination invariant holds by construction rather than by
a multiplication by 1.0 (T4). A haircut `<SYM>.csv` carries `time,close` only
and has no `price/` twin — a modelled series has no unadjusted twin
(`make_synthetic.py` precedent). Unsubstitutable slots (KMLM, BTAL) are absent
from the map by design and take no fictitious haircut; their columns are
flagged translation-incomplete in the verdict. Every other file is
byte-copied. Deterministic by construction — no clock, no environment — so
the committed snapshot is byte-reproducible from the committed parent and
this script.

Run: uv run make_haircut.py tests/data/2026-09-02-net15-usd
     [--haircuts results/overlap_eu/haircuts.json] [--out DIR] [--force]
"""

import argparse
import json
import shutil
from pathlib import Path

import polars as pl


def read_close(path: Path) -> tuple[list[str], list[float]]:
    """One CSV as (time, close). `time` is read as a string and passed through
    untouched so a haircut file carries identical date values."""
    frame = pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"time": pl.String, "close": pl.Float64},
    )
    return frame["time"].to_list(), frame["close"].to_list()


def load_haircuts(path: Path) -> dict[str, float]:
    """`{SYM: h}` — h in %/yr, a number >= 0 (a bool is not a number)."""
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: the haircut map must be a JSON object")
    haircuts = {}
    for symbol, h in raw.items():
        if isinstance(h, bool) or not isinstance(h, (int, float)) or h < 0:
            raise ValueError(f"{path}: {symbol} h must be a number >= 0 (%/yr)")
        haircuts[symbol] = float(h)
    return haircuts


def haircut(closes: list[float], h: float) -> list[float]:
    """The closes compounded down by h/252 per bar: close_t * (1 - d) ** k with
    d = h / 100 / 252 and k = 0 at the first bar. A power, not a running
    product, so bar k depends on k alone."""
    d = h / 100 / 252
    return [c * (1 - d) ** k for k, c in enumerate(closes)]


def build(src: Path, haircuts: dict[str, float]) -> dict:
    """Read and haircut every mapped symbol under src. All computation and
    validation happen here, before anything is written — a hard error can
    never leave a partial dataset behind."""
    symbols = sorted(path.stem for path in src.glob("*.csv"))
    if not symbols:
        raise ValueError(f"{src}: no <SYM>.csv files found")
    unknown = sorted(set(haircuts) - set(symbols))
    if unknown:
        raise ValueError(f"{src}: the haircut map names absent symbols {unknown}")
    cut, untouched = {}, []
    for symbol, h in sorted(haircuts.items()):
        if h == 0:
            untouched.append(symbol)  # the byte-copy path, never a multiply
            continue
        times, closes = read_close(src / f"{symbol}.csv")
        cut[symbol] = {
            "times": times,
            "close": haircut(closes, h),
            "h": h,
            "final_factor": (1 - h / 100 / 252) ** (len(closes) - 1),
        }
    return {
        "symbols": symbols,
        "pairs": sorted(path.stem for path in (src / "price").glob("*.csv")),
        "cut": cut,
        "untouched": untouched,
    }


def _table(results: dict) -> list[str]:
    lines = [
        "| symbol | h %/yr | bars | final factor |",
        "|---|---|---|---|",
    ]
    rows = {s: f"| {s} | 0 | — | byte-copied |" for s in results["untouched"]}
    for symbol, r in results["cut"].items():
        rows[symbol] = (
            f"| {symbol} | {r['h']:g} | {len(r['times'])} | {r['final_factor']!r} |"
        )
    return lines + [rows[s] for s in sorted(rows)]


def render_readme(parent: str, results: dict) -> str:
    """The snapshot README. References the parent by directory basename and
    carries no timestamps — T4 regenerates into a temp directory and
    byte-compares."""
    lines = [
        f"# Haircut snapshot — {parent}-hc",
        "",
        f"Derived from the frozen `{parent}` snapshot by `make_haircut.py`",
        "(EU_SUBSTITUTE_SPEC §6.3): each carried US symbol's close is compounded",
        "down by h/252 per bar from its first bar in the root — formula",
        "`close_t × (1 − h/100/252)^k`, k bars since the first — so a haircut",
        "lane measures the translation cost of a substitutable component on the",
        "winner's own window. A haircut `<SYM>.csv` carries `time,close` only and",
        "has no `price/` twin — a modelled series has no unadjusted twin. A",
        "symbol with h = 0 is byte-copied (the no-contamination invariant holds",
        "by construction). Unsubstitutable slots (KMLM, BTAL) are absent from",
        "the map by design and take no fictitious haircut; their columns are",
        "flagged translation-incomplete in the verdict. Every other file,",
        "`price/` twins included, is byte-copied from the parent.",
        "",
    ]
    return "\n".join(lines + _table(results)) + "\n"


def write_dataset(dst: Path, src: Path, results: dict, readme: str) -> None:
    (dst / "price").mkdir(parents=True, exist_ok=True)
    cut = results["cut"]
    for symbol in results["symbols"]:
        if symbol in cut:
            r = cut[symbol]
            rows = "\n".join(f"{t},{c!r}" for t, c in zip(r["times"], r["close"]))
            (dst / f"{symbol}.csv").write_text(f"time,close\n{rows}\n")
        else:
            shutil.copyfile(src / f"{symbol}.csv", dst / f"{symbol}.csv")
    for symbol in results["pairs"]:
        if symbol in cut:
            continue  # a modelled series has no unadjusted twin
        shutil.copyfile(src / "price" / f"{symbol}.csv", dst / "price" / f"{symbol}.csv")
    (dst / "README.md").write_text(readme)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "src", type=Path,
        help="parent dataset root in the TOTAL_RETURN_SPEC §3 convention",
    )
    parser.add_argument(
        "--haircuts", type=Path, default=Path("results/overlap_eu/haircuts.json"),
        help="the haircut map (default: results/overlap_eu/haircuts.json)",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="output dataset root (default: <SRC>-hc)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="write into an existing --out directory",
    )
    args = parser.parse_args(argv)

    dst = args.out or args.src.with_name(f"{args.src.name}-hc")
    if dst.exists() and not args.force:
        parser.error(f"{dst} exists; pass --force to overwrite")

    results = build(args.src, load_haircuts(args.haircuts))
    write_dataset(dst, args.src, results, render_readme(args.src.name, results))

    print("\n".join(_table(results)))
    print(f"Saved {dst}")


if __name__ == "__main__":
    main()
