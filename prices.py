"""Loading of daily close prices onto a shared trading calendar."""

import datetime as dt
import functools
from collections.abc import Iterable
from pathlib import Path

import polars as pl


def _read_symbol(data_dir: Path, symbol: str) -> pl.DataFrame:
    """Read one CSV as `date`, the close as `SYM`, and any other column as `SYM:COL`."""
    frame = pl.read_csv(
        data_dir / f"{symbol}.csv",
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    ).drop("open", "high", "low")
    renames = {"time": "date", "close": symbol}
    renames |= {col: f"{symbol}:{col}" for col in frame.columns if col not in renames}
    # Indicators with long empty stretches can be inferred as strings.
    return frame.rename(renames).with_columns(pl.exclude("date").cast(pl.Float64))


def load_prices(
    data_dir: Path,
    symbols: Iterable[str],
    start: dt.date,
    extra: Iterable[str] = (),
) -> pl.DataFrame:
    """Load close prices for `symbols` onto the union of their trading dates.

    `extra` names symbols a strategy reads but does not trade; they are joined
    onto that calendar and never extend it. Every loaded symbol contributes its
    close as `SYM` plus one `SYM:COL` column per indicator in its CSV.

    Returns a frame of `date`, one forward-filled column per loaded value, and
    `is_rebalance_day` (True on the last trading day of each month). The final
    row is never a rebalance day, since the data ends mid-month. Only the traded
    closes are guaranteed non-null; an `extra` symbol's columns and any
    indicator are null until that column's history begins.
    """
    symbols = list(symbols)

    prices = functools.reduce(
        lambda left, right: left.join(right, on="date", how="full", coalesce=True),
        (_read_symbol(data_dir, symbol) for symbol in symbols),
    )
    for symbol in extra:
        prices = prices.join(_read_symbol(data_dir, symbol), on="date", how="left")
    prices = prices.sort("date")

    # Fill before filtering, so a symbol whose data is missing on the start date
    # still carries a close forward from an earlier row.
    prices = prices.with_columns(pl.exclude("date").fill_null(strategy="forward"))
    prices = prices.filter(pl.col("date") >= start)
    assert sum(prices.select(symbols).null_count().row(0)) == 0

    return prices.with_columns(
        is_rebalance_day=(
            pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month()
        ).fill_null(False)
    )
