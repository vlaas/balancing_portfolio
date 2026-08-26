"""A gate a strategy owns: caps buys of chosen assets while closed, and
optionally clips their target weight. Four kinds, one class (REGIME_SPEC §4,
COMPOSITION_SPEC §3): sma closes while the symbol trades below its SMA; regime
closes while the term-structure state machine on symbol/denominator reads
risk-off; score closes while a monthly momentum score is at or below its
threshold."""

from indicators import Indicator, sma, sma_monthly, ts_regime
from strategy import MarketDay


class Gate:
    """Closed on a day iff its indicator says so; open while any needed value
    is None. When closed it blocks buys of `assets` — or, with
    contribution_exempt, still allows buys up to the day's external cash times
    the asset's weight. With `w_off`, `clip` additionally caps the assets'
    target weight at `w_off` while closed (REGIME_SPEC §4.2)."""

    def __init__(
        self,
        symbol: str,
        assets: list[str],
        sma_days: int | None = None,
        sma_months: int | None = None,
        denominator: str | None = None,
        ratio_sma: int | None = None,
        fire: float | None = None,
        hysteresis: float = 0.0,
        score: Indicator | None = None,
        threshold: float | None = None,
        contribution_exempt: bool = False,
        w_off: float | None = None,
    ):
        kinds = (
            (sma_days is not None) + (sma_months is not None)
            + (fire is not None) + (score is not None)
        )
        assert kinds == 1, "exactly one of sma_days / sma_months / fire / score"
        self._regime = fire is not None
        if self._regime:
            assert denominator is not None and ratio_sma is not None, (
                "denominator and ratio_sma are required with fire"
            )
            assert denominator != symbol, "symbol and denominator must be distinct"
            self.indicator = ts_regime(denominator, ratio_sma, fire, hysteresis)
            self.symbols = (symbol, denominator)
        else:
            assert denominator is None and ratio_sma is None, (
                "denominator and ratio_sma require fire"
            )
            if score is not None:
                assert threshold is not None, "threshold is required with score"
                # A multiple of 0.001, so gate_str renders it losslessly.
                assert not isinstance(threshold, bool) and abs(
                    threshold * 1000 - round(threshold * 1000)
                ) < 1e-9, f"threshold must be a multiple of 0.001, got {threshold}"
                self.indicator = score
            else:
                self.indicator = (
                    sma(sma_days) if sma_days is not None else sma_monthly(sma_months)
                )
            self.symbols = (symbol,)
        assert score is not None or threshold is None, "threshold requires score"
        assert w_off is None or 0 <= w_off <= 1, f"w_off must be in [0, 1], got {w_off}"
        self.symbol = symbol
        self.assets = tuple(assets)
        self.column = self.indicator.name
        self.contribution_exempt = contribution_exempt
        self.w_off = w_off
        self.denominator = denominator
        self.ratio_sma = ratio_sma
        self.fire = fire
        self.hysteresis = hysteresis
        self.score = score
        self.threshold = threshold

    @property
    def indicators(self) -> dict:
        return {self.symbol: (self.indicator,)}

    def closed(self, ctx: MarketDay) -> bool:
        if self._regime:
            return ctx.indicator(self.symbol, self.column) == 1.0
        value = ctx.indicator(self.symbol, self.column)
        if self.score is not None:
            # `<=`, the rotation family's "non-positive is bad" convention
            # (COMPOSITION_SPEC §3.1).
            return value is not None and value <= self.threshold
        close = ctx.close(self.symbol)
        return close is not None and value is not None and close < value

    def buy_cap(self, asset: str, ctx: MarketDay, weights: dict[str, float]) -> float | None:
        """The owning strategy's buy_cap for `asset`, given its weights today."""
        if asset not in self.assets or not self.closed(ctx):
            return None
        if self.contribution_exempt:
            return ctx.contribution * weights[asset]
        return 0.0

    def clip(self, weights: dict[str, float], ctx: MarketDay) -> dict[str, float]:
        """`weights` with each gated asset capped at `w_off` while closed.

        The excess moves to the assets not in `assets`, pro rata to their
        current weights; with nothing to receive it, it is left in cash. Never
        raises a gated asset's weight, never changes the key set, preserves
        sum <= 1. Open, or without `w_off`, returns `weights` itself.
        """
        if self.w_off is None or not self.closed(ctx):
            return weights
        clipped = dict(weights)
        excess = 0.0
        for asset in self.assets:
            if asset in clipped and clipped[asset] > self.w_off:
                excess += clipped[asset] - self.w_off
                clipped[asset] = self.w_off
        if excess == 0.0:
            return weights
        sleeve = {a: w for a, w in weights.items() if a not in self.assets}
        total = sum(sleeve.values())
        if total > 0:
            for asset, weight in sleeve.items():
                clipped[asset] = weight + excess * (weight / total)
        return clipped


class AnyGate:
    """OR-composition of gates: closed iff any member is closed. Same
    duck-typed surface as Gate (REGIME_SPEC §4.3)."""

    def __init__(self, members: tuple[Gate, ...]):
        members = tuple(members)
        assert len(members) >= 2, "AnyGate needs at least two members"
        self.members = members
        self.symbols = tuple(dict.fromkeys(s for m in members for s in m.symbols))

    @property
    def indicators(self) -> dict:
        merged: dict[str, dict] = {}
        for member in self.members:
            for symbol, declared in member.indicators.items():
                merged.setdefault(symbol, {}).update({i.name: i for i in declared})
        return {symbol: tuple(d.values()) for symbol, d in merged.items()}

    def closed(self, ctx: MarketDay) -> bool:
        return any(member.closed(ctx) for member in self.members)

    def buy_cap(self, asset: str, ctx: MarketDay, weights: dict[str, float]) -> float | None:
        """The most restrictive member's cap: the minimum over non-None caps."""
        caps = [
            cap
            for cap in (m.buy_cap(asset, ctx, weights) for m in self.members)
            if cap is not None
        ]
        return min(caps) if caps else None

    def clip(self, weights: dict[str, float], ctx: MarketDay) -> dict[str, float]:
        for member in self.members:
            weights = member.clip(weights, ctx)
        return weights
