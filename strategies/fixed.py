"""Fixed target weights, optionally behind a gate — the declarative form of
the hand-written strategies."""

from strategies.gate import Gate
from strategy import MarketDay, Strategy


class Fixed(Strategy):
    """Constant weights, rebalanced every month; the residual is cash. A gate,
    when given, caps buys of its assets while closed."""

    def __init__(
        self,
        weights: dict[str, float],
        gate: Gate | None = None,
        label: str | None = None,
    ):
        self.weights = weights
        self.gate = gate
        if label is not None:
            self.label = label
        self.data = (gate.symbol,) if gate and gate.symbol not in weights else ()
        self.indicators = gate.indicators if gate else {}

    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        if self.gate is None:
            return None
        return self.gate.buy_cap(asset, ctx, self.balance(ctx))
