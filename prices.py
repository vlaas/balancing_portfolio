"""Loading of daily close prices onto a shared trading calendar."""

import datetime as dt
import functools
from collections.abc import Iterable, Mapping
from pathlib import Path

import polars as pl

from indicators import Indicator


def _read_close(data_dir: Path, symbol: str) -> pl.DataFrame:
    """Read one CSV as `date` and `close`. Every other CSV column is ignored."""
    frame = pl.read_csv(
        data_dir / f"{symbol}.csv",
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    ).rename({"time": "date"})
    assert frame["date"].is_sorted(), f"{symbol}: dates are not ascending"
    assert frame["date"].n_unique() == len(frame), f"{symbol}: duplicate dates"
    assert frame["close"].null_count() == 0, f"{symbol}: null close"
    return frame


def _read_symbol(
    data_dir: Path, symbol: str, indicators: Iterable[Indicator] = ()
) -> pl.DataFrame:
    """Read one CSV as `date` and the close as `SYM`, plus a `SYM:NAME` per indicator.

    Each indicator is computed on the symbol's own bar calendar, before the
    join onto the traded calendar, and deduplicated by name. A cross-symbol
    indicator (non-empty `inputs`) is computed on the intersection of the
    host's and every input's calendars and carried back onto the host's rows
    by date, null outside the intersection (REGIME_SPEC §3.2).
    """
    own = _read_close(data_dir, symbol)
    frame = own.rename({"close": symbol})
    unique = {indicator.name: indicator for indicator in indicators}
    for name, indicator in unique.items():
        column = f"{symbol}:{name}"
        if not indicator.inputs:
            frame = frame.with_columns(indicator.fn(own).alias(column))
            continue
        joined = own
        for sym in indicator.inputs:
            joined = joined.join(
                _read_close(data_dir, sym).rename({"close": sym}), on="date", how="inner"
            )
        assert len(joined) > 0, (
            f"{symbol}:{name}: empty intersection with {indicator.inputs}"
        )
        values = joined.select("date", indicator.fn(joined).alias(column))
        frame = frame.join(values, on="date", how="left")
    return frame


def load_prices(
    data_dir: Path,
    symbols: Iterable[str],
    start: dt.date,
    end: dt.date | None = None,
    extra: Iterable[str] = (),
    indicators: Mapping[str, Iterable[Indicator]] = {},
) -> pl.DataFrame:
    """Load close prices for `symbols` onto the union of their trading dates.

    `extra` names symbols a strategy reads but does not trade; they are joined
    onto that calendar and never extend it. `indicators` maps a symbol to the
    indicators to compute for it, each loaded as `SYM:NAME`. `end` truncates
    the frame after that date; it must lie between `start` and the last date
    in the data, else ValueError — silent truncation would make two windows
    incomparable.

    Returns a frame of `date`, one forward-filled column per loaded value, and
    `is_rebalance_day` (True on the last trading day of each month). The final
    row is never a rebalance day — whether the data ends mid-month or `end`
    truncated it, it is a valuation day, not a trade day. Only the traded
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

    if end is not None:
        if end < start:
            raise ValueError(f"end {end} is before start {start}")
        last = prices["date"].max()
        if end > last:
            raise ValueError(f"end {end} is past the last data date {last}")
        prices = prices.filter(pl.col("date") <= end)

    return prices.with_columns(
        is_rebalance_day=(
            pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month()
        ).fill_null(False)
    )
