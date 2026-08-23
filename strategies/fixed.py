"""Fixed target weights, optionally behind a gate — the declarative form of
the hand-written strategies."""

from strategies.gate import AnyGate, Gate
from strategy import MarketDay, Strategy


class Fixed(Strategy):
    """Constant weights, rebalanced every month; the residual is cash. A gate,
    when given, caps buys of its assets while closed and, with `w_off`, clips
    their target weight."""

    def __init__(
        self,
        weights: dict[str, float],
        gate: Gate | AnyGate | None = None,
        label: str | None = None,
    ):
        self.weights = weights
        self.gate = gate
        if label is not None:
            self.label = label
        self.data = tuple(s for s in gate.symbols if s not in weights) if gate else ()
        self.indicators = gate.indicators if gate else {}

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        return self.gate.clip(self.weights, ctx) if self.gate else self.weights

    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        if self.gate is None:
            return None
        return self.gate.buy_cap(asset, ctx, self.balance(ctx))
