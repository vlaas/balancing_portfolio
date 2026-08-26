"""A monthly momentum score on its own calendar (COMPOSITION_SPEC §5).

A read-only report: reads one symbol's closes, builds the score through the
same `spec._score` the gate uses (so the report cannot drift from the signal),
and prints markdown to stdout — month-ends closed by the score and by the SMA
gate, their contingency per calendar year, the month-ends they disagree on,
and the threshold ladder.

Run: uv run score_report.py --data DIR --score '{"kind":"avg","months":[1,3,6,12]}'
     [--symbol QQQ] [--threshold 0] [--start 2012-01-03] [--end YYYY-MM-DD]
     [--sma-days 200]
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import polars as pl

from indicators import Indicator, sma
from prices import _read_close
from regime_report import contingency, month_ends
from spec import _score

LADDER = (-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03)


def signals(
    data_dir: Path, symbol: str, score: Indicator, threshold: float,
    start: dt.date, end: dt.date | None, sma_days: int,
) -> pl.DataFrame:
    """The symbol's month-end rows in the window, with `score`, `sma` and the
    two closed flags. One symbol, one calendar: no intersection to take."""
    frame = _read_close(data_dir, symbol)
    frame = frame.with_columns(
        score.fn(frame).alias("score"), sma(sma_days).fn(frame).alias("sma")
    )
    ends = month_ends(frame).filter(
        pl.col("date").is_between(start, end or frame["date"].max())
    )
    return ends.with_columns(
        score_off=pl.col("score").is_not_null() & (pl.col("score") <= threshold),
        sma_off=pl.col("sma").is_not_null() & (pl.col("close") < pl.col("sma")),
    )


def state_changes(flags: list[bool]) -> int:
    """Month-ends whose state differs from the previous month-end's — the
    whipsaw count of the read protocol (COMPOSITION_SPEC §10.7)."""
    return sum(a != b for a, b in zip(flags, flags[1:]))


def report(
    data_dir: Path, symbol: str, score_entry: dict, threshold: float,
    start: dt.date, end: dt.date | None, sma_days: int,
) -> str:
    score, _ = _score(score_entry, "score")
    frame = _read_close(data_dir, symbol)
    end = end or frame["date"].max()
    ends = signals(data_dir, symbol, score, threshold, start, end, sma_days)
    sma_name = f"{symbol}<SMA{sma_days}"
    score_name = f"{symbol}:{score.name}<={threshold:g}"

    lines = [
        f"# Score report: {score_name}",
        "",
        "## Data",
        "",
        f"- {symbol}: {frame['date'].min()} -> {frame['date'].max()} ({len(frame)} rows)",
        f"- window: {start} -> {end}",
        f"- month-ends in the window: {len(ends)}, last {ends['date'].max()}",
        "",
        "## Month-ends closed",
        "",
        f"- {score_name}: {int(ends['score_off'].sum())},"
        f" state changes {state_changes(ends['score_off'].to_list())}",
        f"- {sma_name}: {int(ends['sma_off'].sum())},"
        f" state changes {state_changes(ends['sma_off'].to_list())}",
        "",
        "| year | month-ends | score | SMA |",
        "|---|---|---|---|",
    ]
    for (year,), rows in ends.group_by(ends["date"].dt.year(), maintain_order=True):
        lines.append(
            f"| {year} | {len(rows)} | {int(rows['score_off'].sum())}"
            f" | {int(rows['sma_off'].sum())} |"
        )
    lines += [
        "",
        f"## Contingency with {sma_name} on month-ends",
        "",
        "| window | both | SMA only | score only | neither |",
        "|---|---|---|---|---|",
        f"| full | {contingency(ends, 'sma_off', 'score_off')} |",
        f"| 2022 | "
        f"{contingency(ends.filter(pl.col('date').dt.year() == 2022), 'sma_off', 'score_off')} |",
        "",
        "## Disagreements",
        "",
        "| date | closed by | score |",
        "|---|---|---|",
    ]
    for row in ends.filter(pl.col("score_off") != pl.col("sma_off")).iter_rows(named=True):
        who = "SMA only" if row["sma_off"] else "score only"
        lines.append(f"| {row['date']} | {who} | {row['score']:+.4f} |")
    lines += [
        "",
        "## Threshold ladder",
        "",
        "| threshold | closed | shared with SMA |",
        "|---|---|---|",
    ]
    for step in LADDER:
        off = ends["score"].is_not_null() & (ends["score"] <= step)
        lines.append(
            f"| {step:+g} | {int(off.sum())} | {int((off & ends['sma_off']).sum())} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", default="QQQ")
    parser.add_argument("--score", type=json.loads, required=True)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2012, 1, 3))
    parser.add_argument("--end", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--sma-days", type=int, default=200)
    args = parser.parse_args(argv)

    print(
        report(
            args.data, args.symbol, args.score, args.threshold,
            args.start, args.end, args.sma_days,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
