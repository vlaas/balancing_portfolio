"""A monthly signal on its own calendar (COMPOSITION_SPEC §5, MONTHLY_GATE_SPEC §5).

A read-only report: reads one symbol's closes, builds the comparison signal
through the same factory the gate uses (so the report cannot drift from the
signal), and prints markdown to stdout — month-ends closed by the comparison
signal and by the SMA gate, their contingency per calendar year, and the
month-ends they disagree on. The comparison side is either a momentum score
(`--score`, through `spec._score`, with the threshold ladder) or the
monthly-read gate `close < SMA{m}M` (`--sma-months`, through
`indicators.sma_monthly`); exactly one is required.

Run: uv run score_report.py --data DIR --score '{"kind":"avg","months":[1,3,6,12]}'
     [--symbol QQQ] [--threshold 0] [--start 2012-01-03] [--end YYYY-MM-DD]
     [--sma-days 200]
     uv run score_report.py --data DIR --sma-months 10 [--symbol QQQ] [--start ...]
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import polars as pl

from indicators import Indicator, sma, sma_monthly
from prices import _read_close
from regime_report import contingency, month_ends
from spec import _score

LADDER = (-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03)


def signals(
    data_dir: Path, symbol: str, score: Indicator | None, threshold: float,
    start: dt.date, end: dt.date | None, sma_days: int, sma_months: int | None = None,
) -> pl.DataFrame:
    """The symbol's month-end rows in the window, with `score`, `sma` and the
    two closed flags. One symbol, one calendar: no intersection to take.

    `sma_months` switches the comparison side to `close < SMA{m}M` — the
    monthly-read gate, built by the same `sma_monthly` factory the gate uses —
    and `score` is then ignored (MONTHLY_GATE_SPEC §5)."""
    frame = _read_close(data_dir, symbol)
    comparison = sma_monthly(sma_months) if sma_months is not None else score
    frame = frame.with_columns(
        comparison.fn(frame).alias("score"), sma(sma_days).fn(frame).alias("sma")
    )
    ends = month_ends(frame).filter(
        pl.col("date").is_between(start, end or frame["date"].max())
    )
    closed = (
        pl.col("close") < pl.col("score")
        if sma_months is not None
        else pl.col("score") <= threshold
    )
    return ends.with_columns(
        score_off=pl.col("score").is_not_null() & closed,
        sma_off=pl.col("sma").is_not_null() & (pl.col("close") < pl.col("sma")),
    )


def state_changes(flags: list[bool]) -> int:
    """Month-ends whose state differs from the previous month-end's — the
    whipsaw count of the read protocol (COMPOSITION_SPEC §10.7)."""
    return sum(a != b for a, b in zip(flags, flags[1:]))


def report(
    data_dir: Path, symbol: str, score_entry: dict | None, threshold: float,
    start: dt.date, end: dt.date | None, sma_days: int, sma_months: int | None = None,
) -> str:
    frame = _read_close(data_dir, symbol)
    end = end or frame["date"].max()
    sma_name = f"{symbol}<SMA{sma_days}"
    if sma_months is None:
        score, _ = _score(score_entry, "score")
        score_name = f"{symbol}:{score.name}<={threshold:g}"
        title = f"# Score report: {score_name}"
        score_hdr, sma_hdr = "score", "SMA"
    else:
        score = sma_monthly(sma_months)
        score_name = f"{symbol}<{score.name}"
        title = f"# Gate calendar: {score_name} vs {sma_name}"
        score_hdr, sma_hdr = score.name, f"SMA{sma_days}"
    ends = signals(data_dir, symbol, score, threshold, start, end, sma_days, sma_months)

    lines = [
        title,
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
        f"| year | month-ends | {score_hdr} | {sma_hdr} |",
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
        f"| window | both | {sma_hdr} only | {score_hdr} only | neither |",
        "|---|---|---|---|---|",
        f"| full | {contingency(ends, 'sma_off', 'score_off')} |",
        f"| 2022 | "
        f"{contingency(ends.filter(pl.col('date').dt.year() == 2022), 'sma_off', 'score_off')} |",
        "",
        "## Disagreements",
        "",
    ]
    if sma_months is None:
        lines += [f"| date | closed by | {score_hdr} |", "|---|---|---|"]
    else:
        lines += [
            f"| date | closed by | close | {sma_hdr} | {score_hdr} |",
            "|---|---|---|---|---|",
        ]
    for row in ends.filter(pl.col("score_off") != pl.col("sma_off")).iter_rows(named=True):
        who = f"{sma_hdr} only" if row["sma_off"] else f"{score_hdr} only"
        if sma_months is None:
            lines.append(f"| {row['date']} | {who} | {row['score']:+.4f} |")
        else:
            lines.append(
                f"| {row['date']} | {who} | {row['close']:.4f}"
                f" | {row['sma']:.4f} | {row['score']:.4f} |"
            )
    if sma_months is not None:
        # The ladder is score-specific: a monthly SMA has no threshold (§5).
        return "\n".join(lines) + "\n"
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
    side = parser.add_mutually_exclusive_group(required=True)
    side.add_argument("--score", type=json.loads)
    side.add_argument("--sma-months", type=int)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2012, 1, 3))
    parser.add_argument("--end", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--sma-days", type=int, default=200)
    args = parser.parse_args(argv)

    print(
        report(
            args.data, args.symbol, args.score, args.threshold,
            args.start, args.end, args.sma_days, args.sma_months,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
