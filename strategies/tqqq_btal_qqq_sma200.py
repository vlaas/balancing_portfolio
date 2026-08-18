from indicators import sma
from strategy import MarketDay, Strategy


class TqqqBtalQqqSma200(Strategy):
    """Half TQQQ, half BTAL, but TQQQ is only bought while QQQ trades at or above
    its 200-day SMA. Before QQQ has an SMA the gate stays open, so the strategy
    starts out as the plain 50/50."""

    label = "TQQQ/BTAL SMA gate"
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    data = ("QQQ",)
    indicators = {"QQQ": (sma(200),)}

    def allow_buy(self, asset: str, ctx: MarketDay) -> bool:
        if asset != "TQQQ":
            return True
        close = ctx.close("QQQ")
        sma = ctx.indicator("QQQ", "SMA200")
        if close is None or sma is None:
            return True
        return close >= sma
