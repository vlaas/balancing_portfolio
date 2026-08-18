"""Volatility targeting on one leveraged risk asset, vol measured on its
underlying (e.g. TQQQ sized by QQQ's vol × 3)."""

from indicators import Indicator
from strategies.gate import Gate
from strategy import MarketDay, Strategy


class VolTarget(Strategy):
    """w_risk = clip(sigma_target / (leverage · σ), w_min, w_max), recomputed
    each rebalance day from the vol indicator on vol_symbol; `safe` receives
    1 − w_risk (None leaves the residual in cash). While σ is still None,
    w_risk = fallback. A gate, when given, caps buys as in Fixed."""

    def __init__(
        self,
        risk: str,
        safe: str | None,
        vol_symbol: str,
        vol: Indicator,
        sigma_target: float,
        leverage: float = 1.0,
        w_max: float = 1.0,
        w_min: float = 0.0,
        fallback: float | None = None,
        gate: Gate | None = None,
        label: str | None = None,
    ):
        fallback = w_max if fallback is None else fallback
        assert 0 <= w_min <= w_max <= 1
        assert w_min <= fallback <= w_max
        self.risk = risk
        self.safe = safe
        self.vol_symbol = vol_symbol
        self.vol = vol
        self.sigma_target = sigma_target
        self.leverage = leverage
        self.w_max = w_max
        self.w_min = w_min
        self.fallback = fallback
        self.gate = gate
        if label is not None:
            self.label = label

        self.weights = self._allocation(fallback)  # the universe the engine sees
        self.data = tuple(
            s
            for s in dict.fromkeys((vol_symbol, *((gate.symbol,) if gate else ())))
            if s not in self.weights
        )
        indicators = {vol_symbol: (vol,)}
        if gate:
            indicators[gate.symbol] = indicators.get(gate.symbol, ()) + (gate.indicator,)
        self.indicators = indicators

    def _allocation(self, w: float) -> dict[str, float]:
        if self.safe is None:
            return {self.risk: w}
        return {self.risk: w, self.safe: 1.0 - w}

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        sigma = ctx.indicator(self.vol_symbol, self.vol.name)
        if sigma is None:
            return self._allocation(self.fallback)
        w = min(max(self.sigma_target / (self.leverage * sigma), self.w_min), self.w_max)
        return self._allocation(w)

    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        if self.gate is None:
            return None
        return self.gate.buy_cap(asset, ctx, self.balance(ctx))
