"""An SMA gate a strategy owns: caps buys of chosen assets while the gate
symbol trades below its SMA."""

from indicators import sma, sma_monthly
from strategy import MarketDay


class Gate:
    """Closed on a day iff the symbol's close is below its SMA; open while
    either value is None. When closed it blocks buys of `assets` — or, with
    contribution_exempt, still allows buys up to the day's external cash times
    the asset's weight."""

    def __init__(
        self,
        symbol: str,
        assets: list[str],
        sma_days: int | None = None,
        sma_months: int | None = None,
        contribution_exempt: bool = False,
    ):
        assert (sma_days is None) != (sma_months is None)
        self.symbol = symbol
        self.assets = tuple(assets)
        self.indicator = sma(sma_days) if sma_days is not None else sma_monthly(sma_months)
        self.column = self.indicator.name
        self.contribution_exempt = contribution_exempt

    @property
    def indicators(self) -> dict:
        return {self.symbol: (self.indicator,)}

    def closed(self, ctx: MarketDay) -> bool:
        close = ctx.close(self.symbol)
        value = ctx.indicator(self.symbol, self.column)
        return close is not None and value is not None and close < value

    def buy_cap(self, asset: str, ctx: MarketDay, weights: dict[str, float]) -> float | None:
        """The owning strategy's buy_cap for `asset`, given its weights today."""
        if asset not in self.assets or not self.closed(ctx):
            return None
        if self.contribution_exempt:
            return ctx.contribution * weights[asset]
        return 0.0
