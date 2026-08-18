"""Loading of daily close prices onto a shared trading calendar."""

import datetime as dt
import functools
from collections.abc import Iterable, Mapping
from pathlib import Path

import polars as pl

from indicators import Indicator


def _read_symbol(
    data_dir: Path, symbol: str, indicators: Iterable[Indicator] = ()
) -> pl.DataFrame:
    """Read one CSV as `date` and the close as `SYM`, plus a `SYM:NAME` per indicator.

    Only `time` and `close` are read; every other CSV column is ignored. Each
    indicator is computed on the symbol's own bar calendar, before the join onto
    the traded calendar, and deduplicated by name.
    """
    frame = pl.read_csv(
        data_dir / f"{symbol}.csv",
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    ).rename({"time": "date", "close": symbol})
    assert frame["date"].is_sorted(), f"{symbol}: dates are not ascending"
    assert frame["date"].n_unique() == len(frame), f"{symbol}: duplicate dates"
    assert frame[symbol].null_count() == 0, f"{symbol}: null close"

    own = frame.select("date", pl.col(symbol).alias("close"))
    unique = {indicator.name: indicator for indicator in indicators}
    return frame.with_columns(
        [
            indicator.fn(own).alias(f"{symbol}:{name}")
            for name, indicator in unique.items()
        ]
    )


def load_prices(
    data_dir: Path,
    symbols: Iterable[str],
    start: dt.date,
    extra: Iterable[str] = (),
    indicators: Mapping[str, Iterable[Indicator]] = {},
) -> pl.DataFrame:
    """Load close prices for `symbols` onto the union of their trading dates.

    `extra` names symbols a strategy reads but does not trade; they are joined
    onto that calendar and never extend it. `indicators` maps a symbol to the
    indicators to compute for it, each loaded as `SYM:NAME`.

    Returns a frame of `date`, one forward-filled column per loaded value, and
    `is_rebalance_day` (True on the last trading day of each month). The final
    row is never a rebalance day, since the data ends mid-month. Only the traded
    closes are guaranteed non-null; an `extra` symbol's columns and any
    indicator are null until that column's history begins.
    """
    symbols = list(symbols)

    def read(symbol: str) -> pl.DataFrame:
        return _read_symbol(data_dir, symbol, indicators.get(symbol, ()))

    prices = functools.reduce(
        lambda left, right: left.join(right, on="date", how="full", coalesce=True),
        (read(symbol) for symbol in symbols),
    )
    for symbol in extra:
        prices = prices.join(read(symbol), on="date", how="left")
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
