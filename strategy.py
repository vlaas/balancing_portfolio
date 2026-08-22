"""The API a strategy is written against: one day's data, and the base class."""

import datetime as dt
from dataclasses import dataclass

import polars as pl

from indicators import Indicator

_WEEK_EPOCH = dt.date(1970, 1, 5)  # a Monday; week periods are counted from it


@dataclass(frozen=True)
class Cadence:
    """A rebalance calendar: the last trading day of every `every`-th week or
    month, phase-shifted by `offset` periods. Anchored to the calendar (weeks
    since a fixed Monday, months since year 0, phase 0 = calendar period ends), never to the run's start, so
    overlapping windows trade on the same days. The engine's default, the
    month-end `is_rebalance_day` column, equals `Cadence("months")`."""

    unit: str  # "weeks" | "months"
    every: int = 1
    offset: int = 0

    def __post_init__(self):
        assert self.unit in ("weeks", "months")
        assert self.every >= 1 and 0 <= self.offset < self.every

    def period(self, date: dt.date) -> int:
        if self.unit == "weeks":
            return (date - _WEEK_EPOCH).days // 7
        # year*12 + month: offset 0 lands on the calendar's own period ends
        # (Mar/Jun/Sep/Dec for every=3, Jun/Dec for 6, Dec for 12).
        return date.year * 12 + date.month

    def mask(self, dates: pl.Series) -> pl.Series:
        """True on the last trading day of each selected period; the final
        row is never True (a valuation day, as for the month-end column)."""
        period = pl.Series([self.period(d) for d in dates])
        last_of_period = (period != period.shift(-1)).fill_null(False)
        selected = (period - self.offset) % self.every == 0
        return last_of_period & selected


class MarketDay:
    """Read-only view of one trading day's data."""

    def __init__(self, row: dict, contribution: float = 0.0):
        self._row = row
        self._contribution = contribution

    @property
    def contribution(self) -> float:
        """External cash added today: the initial capital on day 0, the monthly
        contribution on a rebalance day (their sum when day 0 is also a
        rebalance day), 0.0 otherwise."""
        return self._contribution

    @property
    def date(self) -> dt.date:
        return self._row["date"]

    def close(self, symbol: str) -> float | None:
        """The symbol's close, or None before its history begins.

        Raises KeyError for a symbol that was never loaded — declare it in the
        strategy's `data` (or trade it) rather than silently reading None.
        """
        return self._row[symbol]

    def indicator(self, symbol: str, name: str) -> float | None:
        """The symbol's `name` indicator, or None before it has a value.

        Raises KeyError if no such column was loaded (e.g. a typo'd name).
        """
        return self._row[f"{symbol}:{name}"]


class Strategy:
    """A fixed-weight strategy; subclass to make the weights or the buys dynamic."""

    label: str
    weights: dict[str, float]
    data: tuple[str, ...] = ()  # symbols the hooks read but never trade
    # When to rebalance; None = the engine's month-end column. Contributions
    # stay monthly either way (simulate.simulate).
    rebalance: Cadence | None = None
    # Indicators to compute per symbol; each symbol must be in weights or data.
    indicators: dict[str, tuple[Indicator, ...]] = {}

    def __init__(self, **overrides):
        for name, value in overrides.items():
            setattr(self, name, value)

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        """The target weights to rebalance to on `ctx`'s day, over the same assets."""
        return self.weights

    def allow_buy(self, asset: str, ctx: MarketDay) -> bool:
        """Whether `asset` may be bought on `ctx`'s day. Sells are never gated."""
        return True

    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        """Max USD of `asset` to buy today; None = unlimited. Sells are never capped.

        The default derives from allow_buy(), so strategies overriding only
        allow_buy() are unchanged.
        """
        return None if self.allow_buy(asset, ctx) else 0.0
