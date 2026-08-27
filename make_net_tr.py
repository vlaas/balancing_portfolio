"""Derive a net-of-withholding total-return dataset from a frozen gross pair.

Reads a dataset root in the TOTAL_RETURN_SPEC §3 convention (`<SYM>.csv`
gross-adjusted + `price/<SYM>.csv`), replaces each distribution jump factor k
by k_net = w + (1 - w) * k (NET_TR_SPEC §2) so every ex-date reinvests
(1 - w) * D instead of D, and writes `<SYM>.csv` with columns `time,close`
plus a byte-copied `price/` and a README. Deterministic by construction — no
clock, no environment — so the committed snapshot is byte-reproducible from
the committed parent and this script (N5).

`--rate-override SYM=RATE` gives one symbol its own w (CASH_SLEEVE_SPEC §10.5,
the BIL tie-breaker): the flat convention is a modelling choice, not a fact, and
a symbol whose income is US Treasury interest is withheld at a different rate
from one paying ordinary dividends. The overrides are named in the README and in
the per-symbol table, so a snapshot always says which rate produced it.

Run: uv run make_net_tr.py tests/data/2026-08-20 [--withholding 0.15]
     [--rate-override BIL=0] [--out DIR] [--force]
"""

import argparse
import datetime as dt
import math
import shutil
from pathlib import Path

import polars as pl

# NET_TR_SPEC §2.1, re-pinned from the measured step distribution of the
# 48-pair 2026-08-24 universe (ROTATION_SPEC §3.5): largest flat step
# 1.62e-6 (TQQQ), smallest jump 1.247e-5 (BIL 2009-11-02, a ZIRP-era
# ~$0.0011 distribution under the six-symbol universe's old 2e-5 floor),
# worst negative step -4.31e-8. FLAT_MAX equals T2's up-jump criterion
# (5 * TAU) so tests/test_total_return.py and this generator agree on what
# a jump is; the dead zone between FLAT_MAX and JUMP_MIN is a hard error.
TAU = 1e-6
FLAT_MAX = 5e-6
JUMP_MIN = 1e-5


def read_pair(root: Path, symbol: str) -> tuple[list[str], list[float], list[float]]:
    """The (time, adjusted close, price close) triple for one symbol.

    `time` is read as a string and passed through untouched so the net file
    carries byte-identical date values (N1)."""
    kwargs = dict(
        columns=["time", "close"],
        schema_overrides={"time": pl.String, "close": pl.Float64},
    )
    adjusted = pl.read_csv(root / f"{symbol}.csv", **kwargs)
    price = pl.read_csv(root / "price" / f"{symbol}.csv", **kwargs)
    if not adjusted["time"].equals(price["time"]):
        raise ValueError(f"{symbol}: adjusted and price time columns differ")
    return adjusted["time"].to_list(), adjusted["close"].to_list(), price["close"].to_list()


def classify(symbol: str, times: list[str], a: list[float], p: list[float]) -> list[int]:
    """Jump row indices of the ratio series R = A/P (NET_TR_SPEC §2.1).

    Three-way with an asserted-empty middle: FLAT (|delta| <= FLAT_MAX),
    JUMP (delta >= JUMP_MIN), anything else is a hard error. The negative
    band overlaps FLAT on [-FLAT_MAX, -TAU), so it is checked first."""
    jumps = []
    for t in range(1, len(a)):
        delta = math.log((a[t] * p[t - 1]) / (a[t - 1] * p[t]))
        if delta < -TAU:
            raise ValueError(f"{symbol} {times[t]}: negative step {delta}")
        if abs(delta) <= FLAT_MAX:
            continue
        if delta >= JUMP_MIN:
            jumps.append(t)
            continue
        raise ValueError(f"{symbol} {times[t]}: dead-zone step {delta}")
    return jumps


def net_closes(a: list[float], p: list[float], jumps: list[int], w: float) -> list[float]:
    """A_net_t = A_t * C_t with C the backward suffix product of k_net/k over
    jump rows (NET_TR_SPEC §2.2). k in exact-ratio form, not exp(-delta).
    With w = 0 the factor is exactly 1.0, so the output equals A bitwise."""
    jump_set = set(jumps)
    out = [0.0] * len(a)
    c = 1.0
    out[-1] = a[-1] * c
    for t in range(len(a) - 2, -1, -1):
        s = t + 1
        if s in jump_set:
            k = (a[s - 1] * p[s]) / (a[s] * p[s - 1])
            k_net = w + (1.0 - w) * k
            c *= k_net / k
        out[t] = a[t] * c
    return out


def implied_yield(times: list[str], r_first: float) -> float:
    """Cumulative distribution yield implied by the first ratio value, per
    tests/test_total_return.py T2: -ln(R_first) / years."""
    span = dt.date.fromisoformat(times[-1]) - dt.date.fromisoformat(times[0])
    return -math.log(r_first) / (span.days / 365.25)


def build(src: Path, w: float, overrides: dict[str, float] | None = None) -> dict[str, dict]:
    """Read, classify and net every symbol under src. All computation and
    validation happen here, before anything is written — a hard error can
    never leave a partial dataset behind (NET_TR_SPEC §3)."""
    overrides = overrides or {}
    symbols = sorted(path.stem for path in src.glob("*.csv"))
    if not symbols:
        raise ValueError(f"{src}: no <SYM>.csv files found")
    unknown = sorted(set(overrides) - set(symbols))
    if unknown:
        raise ValueError(f"{src}: --rate-override names absent symbols {unknown}")
    results = {}
    for symbol in symbols:
        if not (src / "price" / f"{symbol}.csv").exists():
            # An index series with no distributions (REGIME_SPEC §2.2): the
            # parent file is byte-copied into the net snapshot.
            results[symbol] = {"index": True}
            continue
        rate = overrides.get(symbol, w)
        times, a, p = read_pair(src, symbol)
        jumps = classify(symbol, times, a, p)
        net = net_closes(a, p, jumps, rate)
        results[symbol] = {
            "times": times,
            "close": net,
            "jumps": len(jumps),
            "rate": rate,
            "y_gross": implied_yield(times, a[0] / p[0]),
            "y_net": implied_yield(times, net[0] / p[0]),
        }
    return results


def _table(results: dict[str, dict], overrides: dict[str, float] | None = None) -> list[str]:
    overrides = overrides or {}
    rows = [
        f"| {s} | index | — | — |"
        if r.get("index")
        else f"| {s} | {r['jumps']} | {100 * r['y_gross']:.2f}%/yr"
        f" | {100 * r['y_net']:.2f}%/yr |"
        + (f" w = {r['rate']:g} |" if s in overrides else "")
        for s, r in results.items()
    ]
    return ["| symbol | jumps | y gross | y net |", "|---|---|---|---|"] + rows


def suffix(overrides: dict[str, float]) -> str:
    """The name fragment a per-symbol rate adds: `{"BIL": 0}` -> `-bil0`.
    Empty without overrides, so an ordinary snapshot's name never moves."""
    return "".join(
        f"-{s.lower()}{round(rate * 100)}" for s, rate in sorted(overrides.items())
    )


def render_readme(parent: str, w: float, results: dict[str, dict],
                  overrides: dict[str, float] | None = None) -> str:
    """The snapshot README. References the parent by directory basename and
    names the snapshot from parent + rate, never from CLI paths, and carries
    no timestamps — N5 regenerates into a temp directory and byte-compares."""
    overrides = overrides or {}
    lines = [
        f"# Net total-return snapshot — {parent}-net{round(w * 100)}{suffix(overrides)}",
        "",
        f"Derived from the frozen `{parent}` snapshot by `make_net_tr.py`"
        f" (NET_TR_SPEC §2–§3) at withholding w = {w:g}: each distribution jump",
        "factor k is replaced by k_net = w + (1 - w) * k, so every ex-date",
        "reinvests (1 - w) * D instead of D; flat (pure price movement) rows",
        "scale by the constant suffix product C only, and the net series anchors",
        "to the parent at the last bar. `<SYM>.csv` carries columns `time,close`",
        "only; `price/<SYM>.csv` is byte-copied from the parent. Step",
        f"classification (NET_TR_SPEC §2.1): FLAT_MAX = {FLAT_MAX!r},",
        f"JUMP_MIN = {JUMP_MIN!r}, TAU = {TAU!r}.",
        "",
    ]
    if overrides:
        rates = ", ".join(f"{s} at w = {r:g}" for s, r in sorted(overrides.items()))
        lines += [
            f"Per-symbol rate override (CASH_SLEEVE_SPEC §10.5): {rates}. The flat",
            "convention is a modelling choice, not a fact; BIL's income is US",
            "Treasury interest, the clearest §871(k) interest-related-dividend case",
            "there is, so its true NRA withholding is plausibly ~0%. This snapshot",
            "exists to break a tie inside the bias band, not to replace the flat",
            "root — a decision run still uses the flat one unless it says otherwise.",
            "",
        ]
    return "\n".join(lines + _table(results, overrides)) + "\n"


def write_dataset(dst: Path, src: Path, results: dict[str, dict], readme: str) -> None:
    (dst / "price").mkdir(parents=True, exist_ok=True)
    for symbol, r in results.items():
        if r.get("index"):
            shutil.copyfile(src / f"{symbol}.csv", dst / f"{symbol}.csv")
            continue
        rows = "\n".join(f"{t},{c!r}" for t, c in zip(r["times"], r["close"]))
        (dst / f"{symbol}.csv").write_text(f"time,close\n{rows}\n")
        shutil.copyfile(src / "price" / f"{symbol}.csv", dst / "price" / f"{symbol}.csv")
    (dst / "README.md").write_text(readme)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "src", type=Path,
        help="parent dataset root in the TOTAL_RETURN_SPEC §3 convention",
    )
    parser.add_argument(
        "--withholding", type=float, default=0.15,
        help="withholding rate in [0, 1) (default: 0.15)",
    )
    parser.add_argument(
        "--rate-override", action="append", default=[], metavar="SYM=RATE",
        help="withholding rate for one symbol, repeatable (e.g. BIL=0)",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="output dataset root (default: <SRC>-net<rate*100>)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="write into an existing --out directory",
    )
    args = parser.parse_args(argv)

    w = args.withholding
    if not 0.0 <= w < 1.0:
        parser.error(f"--withholding must be in [0, 1): {w}")
    overrides = {}
    for item in args.rate_override:
        symbol, _, rate = item.partition("=")
        if not symbol or not rate:
            parser.error(f"--rate-override wants SYM=RATE: {item!r}")
        try:
            overrides[symbol] = float(rate)
        except ValueError:
            parser.error(f"--rate-override rate is not a number: {item!r}")
        if not 0.0 <= overrides[symbol] < 1.0:
            parser.error(f"--rate-override must be in [0, 1): {item!r}")
    dst = args.out or args.src.with_name(
        f"{args.src.name}-net{round(w * 100)}{suffix(overrides)}"
    )
    if dst.exists() and not args.force:
        parser.error(f"{dst} exists; pass --force to overwrite")

    results = build(args.src, w, overrides)
    write_dataset(dst, args.src, results,
                  render_readme(args.src.name, w, results, overrides))

    print("\n".join(_table(results, overrides)))
    print(f"Saved {dst}")


if __name__ == "__main__":
    main()
