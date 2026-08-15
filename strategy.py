"""The API a strategy is written against: one day's data, and the base class."""

import datetime as dt


class MarketDay:
    """Read-only view of one trading day's data."""

    def __init__(self, row: dict):
        self._row = row

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

    def __init__(self, **overrides):
        for name, value in overrides.items():
            setattr(self, name, value)

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        """The target weights to rebalance to on `ctx`'s day, over the same assets."""
        return self.weights

    def allow_buy(self, asset: str, ctx: MarketDay) -> bool:
        """Whether `asset` may be bought on `ctx`'s day. Sells are never gated."""
        return True
