"""Volatility targeting on one leveraged risk asset, vol measured on its
underlying (e.g. TQQQ sized by QQQ's vol × 3)."""

from dataclasses import dataclass

from indicators import Indicator
from strategies.gate import AnyGate, Gate
from strategy import MarketDay, Strategy


@dataclass(frozen=True)
class SafeSwitch:
    """A conditional sleeve: hold `on`, or `off` while `when` is closed.
    `when` is a pure condition — a Gate with no assets, so it observes and
    never caps or clips; while any of its inputs is still None it reads open,
    so the sleeve is `on` during warm-up (SAFE_SWITCH_SPEC §2)."""

    on: str | dict[str, float] | None
    off: str | dict[str, float] | None
    when: Gate

    def active(self, ctx: MarketDay) -> str | dict[str, float] | None:
        return self.off if self.when.closed(ctx) else self.on


def _symbols(sleeve: str | dict[str, float] | None) -> tuple[str, ...]:
    if sleeve is None:
        return ()
    if isinstance(sleeve, dict):
        return tuple(sleeve)
    return (sleeve,)


class VolTarget(Strategy):
    """w_risk = clip(sigma_target / (leverage · σ), w_min, w_max), recomputed
    each rebalance day from the vol indicator on vol_symbol; `safe` receives
    1 − w_risk (None leaves the residual in cash; a dict splits it across the
    sleeve by its fractions; a SafeSwitch splits it across whichever of its
    sleeves is active, the inactive one's symbols held at 0.0). While σ is
    still None, w_risk = fallback. A gate, when given, caps buys as in
    Fixed."""

    def __init__(
        self,
        risk: str,
        safe: str | dict[str, float] | SafeSwitch | None,
        vol_symbol: str,
        vol: Indicator,
        sigma_target: float,
        leverage: float = 1.0,
        w_max: float = 1.0,
        w_min: float = 0.0,
        fallback: float | None = None,
        gate: Gate | AnyGate | None = None,
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

        if isinstance(safe, SafeSwitch):
            # The universe the engine sees is the on/off union: off-only
            # symbols ride at 0.0 so set(balance) == set(weights) holds on
            # every rebalance day.
            base = self._allocation(fallback, safe.on)
            self.weights = base | {s: 0.0 for s in _symbols(safe.off) if s not in base}
        else:
            self.weights = self._allocation(fallback, safe)
        condition = safe.when if isinstance(safe, SafeSwitch) else None
        self.data = tuple(
            s
            for s in dict.fromkeys(
                (
                    vol_symbol,
                    *(gate.symbols if gate else ()),
                    *(condition.symbols if condition else ()),
                )
            )
            if s not in self.weights
        )
        # Name-keyed like AnyGate.indicators, so a switch sharing the gate's
        # condition declares it once.
        merged: dict[str, dict[str, Indicator]] = {vol_symbol: {vol.name: vol}}
        for owner in (gate, condition):
            if owner:
                for symbol, declared in owner.indicators.items():
                    merged.setdefault(symbol, {}).update({i.name: i for i in declared})
        self.indicators = {s: tuple(d.values()) for s, d in merged.items()}

    def _allocation(
        self, w: float, sleeve: str | dict[str, float] | None
    ) -> dict[str, float]:
        if sleeve is None:
            return {self.risk: w}
        if isinstance(sleeve, dict):
            return {self.risk: w} | {
                s: (1.0 - w) * f for s, f in sleeve.items()
            }
        return {self.risk: w, sleeve: 1.0 - w}

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        sigma = ctx.indicator(self.vol_symbol, self.vol.name)
        if sigma is None:
            w = self.fallback
        else:
            w = min(max(self.sigma_target / (self.leverage * sigma), self.w_min), self.w_max)
        if isinstance(self.safe, SafeSwitch):
            allocation = self._allocation(w, self.safe.active(ctx))
            allocation |= {s: 0.0 for s in self.weights if s not in allocation}
        else:
            allocation = self._allocation(w, self.safe)
        return self.gate.clip(allocation, ctx) if self.gate else allocation

    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        if self.gate is None:
            return None
        return self.gate.buy_cap(asset, ctx, self.balance(ctx))
