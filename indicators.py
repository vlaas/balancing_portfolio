"""Named, causal indicators computed from one symbol's own close series."""

import math
from collections.abc import Callable
from dataclasses import dataclass

import polars as pl

TRADING_DAYS = 252


@dataclass(frozen=True)
class Indicator:
    """A named, causal function of one symbol's close series.

    `fn` receives the symbol's own frame with columns `date` (ascending, unique)
    and `close` (Float64, non-null) and returns a Float64 Series of the same
    length, null during warm-up. `name` is the column suffix and the identity:
    two Indicators with the same name are the same indicator.
    """

    name: str
    fn: Callable[[pl.DataFrame], pl.Series]


def _log_returns(frame: pl.DataFrame) -> pl.Series:
    """Daily log returns; null on the first row, which has no previous close."""
    return (frame["close"] / frame["close"].shift(1)).log()


def sma(n: int) -> Indicator:
    """Arithmetic mean of the last `n` closes, today's included."""
    return Indicator(f"SMA{n}", lambda frame: frame["close"].rolling_mean(n))


def sma_monthly(m: int) -> Indicator:
    """Mean of the last `m` month-end closes, carried forward between month-ends.

    A row is a month-end iff its month differs from the next row's — the same
    rule as `is_rebalance_day`, so the value on a rebalance day includes that
    day's close and the file's final (partial-month) row is never a month-end.
    """

    def fn(frame: pl.DataFrame) -> pl.Series:
        month_end = (
            pl.col("date").dt.month() != pl.col("date").shift(-1).dt.month()
        ).fill_null(False)
        month_ends = frame.filter(month_end).select(
            "date", value=pl.col("close").rolling_mean(m)
        )
        return frame.join_asof(month_ends, on="date", strategy="backward")["value"]

    return Indicator(f"SMA{m}M", fn)


def realized_vol(n: int) -> Indicator:
    """Annualised sample standard deviation of the last `n` log returns."""
    return Indicator(
        f"VOL{n}",
        lambda frame: _log_returns(frame).rolling_std(n, ddof=1)
        * math.sqrt(TRADING_DAYS),
    )


def ewma_vol(lam: float = 0.94) -> Indicator:
    """Annualised RiskMetrics EWMA volatility: zero-mean, no bias correction.

    Null for the first 20 rows, so estimates still dominated by the seed
    (`s²_1 = r_1²`) are never read by a strategy.
    """

    def fn(frame: pl.DataFrame) -> pl.Series:
        variance = (_log_returns(frame) ** 2).ewm_mean(
            alpha=1 - lam, adjust=False, min_samples=20
        )
        return (variance * TRADING_DAYS).sqrt()

    return Indicator(f"VOL_EWMA{round(lam * 100)}", fn)


def drawdown() -> Indicator:
    """Fraction below the running maximum close over the file's whole history."""
    return Indicator("DD", lambda frame: frame["close"] / frame["close"].cum_max() - 1)


def momentum(n: int) -> Indicator:
    """Total return over the last `n` bars."""
    return Indicator(f"MOM{n}", lambda frame: frame["close"] / frame["close"].shift(n) - 1)
