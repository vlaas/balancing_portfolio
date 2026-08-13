"""Loading of daily close prices onto a shared trading calendar."""

import datetime as dt
import functools
from collections.abc import Iterable
from pathlib import Path

import polars as pl


def load_prices(data_dir: Path, symbols: Iterable[str], start: dt.date) -> pl.DataFrame:
    """Load close prices for `symbols` onto the union of their trading dates.

    Returns a frame of `date`, one Float64 column per symbol holding the
    forward-filled close, and `is_rebalance_day` (True on the last trading day
    of each month). The final row is never a rebalance day, since the data ends
    mid-month.
    """
    frames = [
        pl.read_csv(
            data_dir / f"{symbol}.csv",
            columns=["time", "close"],
            schema_overrides={"close": pl.Float64},
            try_parse_dates=True,
        ).rename({"time": "date", "close": symbol})
        for symbol in symbols
    ]

    prices = functools.reduce(
        lambda left, right: left.join(right, on="date", how="full", coalesce=True),
        frames,
    ).sort("date")

    # Fill before filtering, so a symbol whose data is missing on the start date
    # still carries a close forward from an earlier row.
    prices = prices.with_columns(pl.exclude("date").fill_null(strategy="forward"))
    prices = prices.filter(pl.col("date") >= start)
    assert sum(prices.null_count().row(0)) == 0

    return prices.with_columns(
        is_rebalance_day=(
            pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month()
        ).fill_null(False)
    )
