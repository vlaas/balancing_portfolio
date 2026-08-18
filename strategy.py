"""The API a strategy is written against: one day's data, and the base class."""

import datetime as dt

from indicators import Indicator


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
