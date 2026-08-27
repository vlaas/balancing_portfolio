"""Episode attribution — what a sleeve component earns, and when it pays (EPISODE_SPEC §3–§4).

Read-only and deterministic. `bundle` builds a spec's bundle through the same
`build_bundle`/`run_bundle` the engine uses — `results/*.json` carries no daily
curve, so the time-weighted index has to be rebuilt in-process (§2.4) — and
slices every strategy's index by the frozen `EPISODES` table. `partition` reads
a sweep's `runs.json` and splits its sensitivity windows by whether they contain
an episode's trough. Both cite the table by id and window, so a refresh of the
committed `drawdowns` is a visible spec change, not a silent drift.

Run: uv run episode_report.py bundle SPEC --data ROOT [--baseline BIL]
         [--sigma 0.20 --w-max 0.8]
     uv run episode_report.py partition RUNS_JSON --pair "LABEL_A" "LABEL_B" [--pair ...]
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import polars as pl

from main import run_bundle
from spec import build_bundle, load_spec, safe_str

# EPISODE_SPEC §3, frozen: peak -> recovery of the incumbent machine's own
# drawdown blocks at the winners' coordinate, plus the 2022 grind from the 50/50
# arm and the open 2025-10 episode. A lane starting inside a window reads it from
# its own first bar.
EPISODES = (
    ("E1", "grind-2015", "2014-11-28", "2015-08-25", "2017-02-07"),
    ("E2", "2018-Q4", "2018-08-31", "2019-06-03", "2019-12-16"),
    ("E3", "COVID", "2020-02-19", "2020-03-23", "2020-07-06"),
    ("E4", "anti-beta unwind", "2020-09-02", "2021-03-08", "2021-09-03"),
    ("E5", "2022 grind", "2021-11-19", "2023-03-10", "2023-06-15"),
    ("E6", "tariff", "2024-07-10", "2025-04-08", "2025-10-01"),
    ("E7", "2025-10", "2025-10-29", "2026-03-27", "2026-08-24"),
)


def _date(text: str) -> dt.date:
    return dt.date.fromisoformat(text)


def episode_slice(
    twr_frame: pl.DataFrame, peak: str, recovery: str
) -> tuple[float | None, float | None]:
    """(episode return, in-window max drawdown) of the TWR index, or (None, None).

    Both ends inclusive; the lane's first bar substitutes for a peak before it.
    The drawdown runs from the window's own running peak, so an arm already
    falling at the window's start shows a shallower number than its full-history
    episode (§12).
    """
    window = twr_frame.filter(pl.col("date").is_between(_date(peak), _date(recovery)))
    if len(window) < 2:
        return None, None
    index = window["index"]
    drawdown = window.select(pl.col("index") / pl.col("index").cum_max() - 1.0)["index"]
    return index[-1] / index[0] - 1.0, drawdown.min()


def _cell(value: float | None, scale: float = 100.0) -> str:
    return "·" if value is None else f"{value * scale:+.1f}"


def _table(rows: list[tuple[str, str, dict]], marginal: dict | None) -> list[str]:
    """One row per strategy: `return / drawdown` per episode, or the marginal in
    points against `marginal` (`+` meaning shallower)."""
    lines = [
        "| sleeve | " + " | ".join(e for e, *_ in EPISODES) + " |",
        "|---" * (len(EPISODES) + 1) + "|",
    ]
    for label, _, cells in rows:
        out = []
        for eid, *_ in EPISODES:
            ret, drawdown = cells[eid]
            if marginal is None:
                out.append(f"{_cell(ret)} / {_cell(drawdown)}")
            else:
                base_ret, base_drawdown = marginal[eid]
                out.append(
                    f"{_cell(None if ret is None else ret - base_ret)}"
                    f" / {_cell(None if drawdown is None else drawdown - base_drawdown)}"
                )
        lines.append(f"| `{label}` | " + " | ".join(out) + " |")
    return lines


def _names(strategies: list) -> list[str]:
    """Row names: the sleeve alone where that is unique in the bundle — the §11
    tables' spelling — and the full label where two sleeves would collide (an
    unfiltered multi-coordinate bundle)."""
    short = [safe_str(st.spec["safe"]) if "safe" in st.spec else st.label for st in strategies]
    return short if len(set(short)) == len(short) else [st.label for st in strategies]


def _keep(entry: dict, sigma: float | None, w_max: float | None) -> bool:
    """A coordinate filter that never drops the benchmark: an entry without the
    keys — `fixed`, `rotation` — has no coordinate to miss."""
    for key, wanted in (("sigma_target", sigma), ("w_max", w_max)):
        if wanted is not None and key in entry and entry[key] != wanted:
            return False
    return True


def episode_rows(
    spec_path: Path, data_dir: Path, sigma: float | None = None, w_max: float | None = None
) -> list[tuple[str, str, dict]]:
    """(row name, label, {episode id: (return, drawdown)}) per strategy, in bundle order."""
    spec = load_spec(spec_path)
    spec = spec | {"strategies": [e for e in spec["strategies"] if _keep(e, sigma, w_max)]}
    bundle = build_bundle(spec)
    results = run_bundle(bundle, data_dir)
    return [
        (name, r.label, {eid: episode_slice(r.twr, peak, recovery)
                         for eid, _, peak, _, recovery in EPISODES})
        for name, r in zip(_names(bundle.strategies), results)
    ]


def bundle_report(
    spec_path: Path, data_dir: Path, baseline: str | None,
    sigma: float | None, w_max: float | None,
) -> str:
    rows = episode_rows(spec_path, data_dir, sigma, w_max)

    coordinate = "" if sigma is None and w_max is None else (
        f", σ{'*' if sigma is None else format(sigma, '.2f')}"
        f" / w_max {'*' if w_max is None else format(w_max, 'g')}"
    )
    lines = [
        f"# Episode report: {spec_path.name}{coordinate}",
        "",
        "## Episodes (EPISODE_SPEC §3)",
        "",
        "| id | name | window | trough |",
        "|---|---|---|---|",
    ] + [
        f"| {eid} | {name} | {peak} → {recovery} | {trough} |"
        for eid, name, peak, trough, recovery in EPISODES
    ] + [
        "",
        f"- data: `{data_dir}`",
        "- cells: episode return % of the TWR index / max drawdown % inside the window",
        "- `·` where the lane has fewer than two bars in the window",
        "",
        "## Episode return / in-window drawdown",
        "",
    ] + _table(rows, None)

    if baseline is not None:
        matches = [cells for _, label, cells in rows if f"/{baseline} " in label]
        if not matches:
            raise SystemExit(
                f"--baseline {baseline}: no strategy in {spec_path} holds it alone;"
                f" have {', '.join(name for name, *_ in rows)}"
            )
        lines += [
            "",
            f"## Marginal against `{baseline}` (points, `+` = higher return / shallower)",
            "",
        ] + _table([r for r in rows if f"/{baseline} " not in r[1]], matches[0])
    return "\n".join(lines) + "\n"


def sens_rows(runs: list[dict], label: str, source: Path | str = "") -> dict[str, dict]:
    """The strategy's sensitivity-window rows, keyed by window name."""
    rows = {r["window"]: r for r in runs if r["kind"] == "sens" and r["label"] == label}
    if not rows:
        have = sorted({r["label"] for r in runs})
        raise SystemExit(f"{source}: no sens rows for {label!r}; have\n  " + "\n  ".join(have))
    return rows


def split_by_trough(a: dict[str, dict], trough: str) -> tuple[list[str], list[str]]:
    """(windows containing the trough, windows without it) — a window contains an
    episode when its own span does, which is what §2.2's 10/10 partition counts."""
    inside = [
        w for w in a if _date(a[w]["start"]) <= _date(trough) <= _date(a[w]["end"])
    ]
    return inside, [w for w in a if w not in inside]


def split(
    a: dict[str, dict], b: dict[str, dict], windows: list[str]
) -> tuple[int, int, int, float, float]:
    """n, B's Calmar wins, B's shallower windows, mean ΔCalmar, mean Δdrawdown."""
    if not windows:
        return 0, 0, 0, 0.0, 0.0
    calmar = sum(b[w]["calmar"] > a[w]["calmar"] for w in windows)
    shallower = sum(b[w]["max_drawdown"] > a[w]["max_drawdown"] for w in windows)
    d_calmar = sum(b[w]["calmar"] - a[w]["calmar"] for w in windows) / len(windows)
    d_drawdown = sum(b[w]["max_drawdown"] - a[w]["max_drawdown"] for w in windows) / len(windows)
    return len(windows), calmar, shallower, d_calmar, d_drawdown


def partition_report(runs_path: Path, pairs: list[list[str]]) -> str:
    runs = json.loads(runs_path.read_text())
    lines = [f"# Episode partition: `{runs_path}`", ""]

    for label_a, label_b in pairs:
        a, b = sens_rows(runs, label_a, runs_path), sens_rows(runs, label_b, runs_path)
        shared = {w: row for w, row in a.items() if w in b}
        lines += [
            f"## A `{label_a}` vs B `{label_b}`",
            "",
            f"- {len(shared)} shared sensitivity windows,"
            f" {list(shared.values())[0]['start']} → {list(shared.values())[-1]['end']}",
            "",
            "| split by | side | n | B wins Calmar | B shallower | mean ΔCalmar | mean Δdrawdown |",
            "|---|---|---|---|---|---|---|",
        ]
        for eid, name, _, trough, _ in EPISODES:
            inside, outside = split_by_trough(shared, trough)
            for side, windows in (("with", inside), ("without", outside)):
                n, calmar, shallower, d_calmar, d_drawdown = split(a, b, windows)
                cells = (
                    f"{n} | · | · | · | ·" if not n else
                    f"{n} | {calmar} | {shallower}"
                    f" | {d_calmar:+.4f} | {100 * d_drawdown:+.2f} pp"
                )
                lines.append(f"| {eid} {name} ({trough}) | {side} | {cells} |")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)

    bundle = modes.add_parser("bundle")
    bundle.add_argument("spec", type=Path)
    bundle.add_argument("--data", type=Path, required=True)
    bundle.add_argument("--baseline", default=None)
    bundle.add_argument("--sigma", type=float, default=None)
    bundle.add_argument("--w-max", type=float, default=None)

    partition = modes.add_parser("partition")
    partition.add_argument("runs", type=Path)
    partition.add_argument("--pair", nargs=2, action="append", required=True)

    args = parser.parse_args(argv)
    if args.mode == "bundle":
        text = bundle_report(args.spec, args.data, args.baseline, args.sigma, args.w_max)
    else:
        text = partition_report(args.runs, args.pair)
    print(text, end="")


if __name__ == "__main__":
    main()
