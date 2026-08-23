"""The term-structure regime signal on its own calendar (REGIME_SPEC §6).

A read-only report: loads nothing through the engine, builds the intersection
ratio and regime state through the same factories the gate uses, and prints
markdown to stdout — data ranges, risk-off days and episodes, month-ends
risk-off per calendar year, and the contingency with the SMA gate.

Run: uv run regime_report.py --data DIR --ratio-sma N --fire F [--hysteresis H]
     [--symbol VIX --denominator VIX3M] [--start 2012-01-03] [--end YYYY-MM-DD]
     [--sma-symbol QQQ --sma-days 200]
"""

import argparse
import datetime as dt
from pathlib import Path

import polars as pl

from indicators import ratio_sma, sma, ts_regime
from prices import _read_close


def signal_frame(
    data_dir: Path, symbol: str, denominator: str, n: int, fire: float, hysteresis: float
) -> pl.DataFrame:
    """The joint calendar with `ratio`, `smoothed` and `off` columns."""
    host = _read_close(data_dir, symbol)
    joint = host.join(
        _read_close(data_dir, denominator).rename({"close": denominator}),
        on="date", how="inner",
    )
    return joint.with_columns(
        (pl.col("close") / pl.col(denominator)).alias("ratio"),
        ratio_sma(denominator, n).fn(joint).alias("smoothed"),
        ts_regime(denominator, n, fire, hysteresis).fn(joint).alias("off"),
    )


def month_ends(frame: pl.DataFrame) -> pl.DataFrame:
    """The frame's month-end rows: month differs from the next row's, the last
    row never — the `is_rebalance_day` rule."""
    flag = (frame["date"].dt.month() != frame["date"].shift(-1).dt.month()).fill_null(False)
    return frame.filter(flag)


def episodes(off: list) -> list[int]:
    """Lengths of the consecutive risk-off runs in the `off` column."""
    runs, current = [], 0
    for value in off:
        if value == 1.0:
            current += 1
        elif current:
            runs.append(current)
            current = 0
    if current:
        runs.append(current)
    return runs


def report(
    data_dir: Path, symbol: str, denominator: str, n: int, fire: float,
    hysteresis: float, start: dt.date, end: dt.date | None,
    sma_symbol: str, sma_days: int,
) -> str:
    host = _read_close(data_dir, symbol)
    joint = signal_frame(data_dir, symbol, denominator, n, fire, hysteresis)
    sma_frame = _read_close(data_dir, sma_symbol)
    sma_frame = sma_frame.with_columns(sma(sma_days).fn(sma_frame).alias("sma"))
    ends = month_ends(sma_frame)

    # The window is bounded by the slower of the signal's and the SMA symbol's
    # calendars, so the no-`--end` §9 commands reproduce the R4 pins.
    end = end or min(joint["date"].max(), sma_frame["date"].max())
    window = joint.filter(pl.col("date").is_between(start, end))
    host_only = host.filter(pl.col("date").is_between(start, end))["date"].to_list()
    host_only = sorted(set(host_only) - set(window["date"].to_list()))
    on_sma_calendar = set(host_only) & set(sma_frame["date"].to_list())

    off_days = int(window["off"].eq(1.0).sum())
    runs = episodes(window["off"].to_list())

    # Regime and SMA state at each month-end, regime carried forward by date.
    ends = ends.filter(pl.col("date").is_between(start, end))
    ends = ends.join_asof(window.select("date", "off"), on="date", strategy="backward")
    ends = ends.with_columns(
        regime_off=pl.col("off") == 1.0,
        sma_off=pl.col("sma").is_not_null() & (pl.col("close") < pl.col("sma")),
    )

    def contingency(rows: pl.DataFrame) -> str:
        both = int((rows["regime_off"] & rows["sma_off"]).sum())
        sma_only = int((~rows["regime_off"] & rows["sma_off"]).sum())
        regime_only = int((rows["regime_off"] & ~rows["sma_off"]).sum())
        neither = len(rows) - both - sma_only - regime_only
        return f"{both} | {sma_only} | {regime_only} | {neither}"

    sma_name = f"{sma_symbol}<SMA{sma_days}"
    lines = [
        f"# Regime report: {symbol}/{denominator}@{n} >= {fire:.2f}"
        + (f" < {fire - hysteresis:.2f}" if hysteresis else ""),
        "",
        "## Data",
        "",
        f"- {symbol}: {host['date'].min()} -> {host['date'].max()} ({len(host)} rows)",
        f"- {denominator}: -> {joint['date'].max()} ({len(joint)} joint rows, full intersection)",
        f"- window: {start} -> {end}, {len(window)} joint days",
        f"- {symbol}-only rows in the window: {len(host_only)},"
        f" on {sma_symbol}'s calendar: {len(on_sma_calendar)}",
        "",
        "## Trading days",
        "",
        f"- risk-off: {off_days} of {len(window)} ({100 * off_days / len(window):.1f}%)",
        f"- episodes: {len(runs)}"
        + (f", mean length {sum(runs) / len(runs):.1f} days" if runs else ""),
        "",
        f"## Month-ends ({sma_symbol} calendar)",
        "",
        f"- month-ends in the window: {len(ends)},"
        f" risk-off: {int(ends['regime_off'].sum())}",
        "",
        "| year | month-ends | risk-off |",
        "|---|---|---|",
    ]
    for (year,), rows in ends.group_by(ends["date"].dt.year(), maintain_order=True):
        lines.append(f"| {year} | {len(rows)} | {int(rows['regime_off'].sum())} |")
    lines += [
        "",
        f"## Contingency with {sma_name} on month-ends",
        "",
        "| window | both | SMA only | regime only | neither |",
        "|---|---|---|---|---|",
        f"| full | {contingency(ends)} |",
        f"| 2022 | {contingency(ends.filter(pl.col('date').dt.year() == 2022))} |",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--symbol", default="VIX")
    parser.add_argument("--denominator", default="VIX3M")
    parser.add_argument("--ratio-sma", type=int, required=True)
    parser.add_argument("--fire", type=float, required=True)
    parser.add_argument("--hysteresis", type=float, default=0.0)
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2012, 1, 3))
    parser.add_argument("--end", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--sma-symbol", default="QQQ")
    parser.add_argument("--sma-days", type=int, default=200)
    args = parser.parse_args(argv)

    print(
        report(
            args.data, args.symbol, args.denominator, args.ratio_sma, args.fire,
            args.hysteresis, args.start, args.end, args.sma_symbol, args.sma_days,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
