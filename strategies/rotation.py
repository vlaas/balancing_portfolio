"""Cross-sectional momentum rotation: rank a universe by a monthly score, hold
the top-k equal-weight, route disqualified or canary-flagged mass to a
defensive selection (ROTATION_SPEC §5)."""

from dataclasses import dataclass

from indicators import Indicator
from strategy import MarketDay, Strategy


@dataclass(frozen=True)
class BestOf:
    """Defensive selection: the whole routed pool to the argmax of `score`
    over `symbols`, ties by list order. No further sign filter — listing BIL
    (or SHY) among the candidates *is* the floor, exactly as HAA uses it."""

    symbols: tuple[str, ...]
    score: Indicator


@dataclass(frozen=True)
class Canary:
    """Keller's canary: `d = min(1, n_bad / breadth)` of the portfolio goes
    defensive, where n_bad counts canary symbols with score <= 0
    ("non-positive")."""

    symbols: tuple[str, ...]
    breadth: int
    score: Indicator


def _held(fallback: str | dict | BestOf | None) -> tuple[str, ...]:
    """The symbols a fallback can put money into — empty for cash."""
    if fallback is None:
        return ()
    if isinstance(fallback, BestOf):
        return fallback.symbols
    if isinstance(fallback, dict):
        return tuple(fallback)
    return (fallback,)


class Rotation(Strategy):
    """Each rebalance day: rank `assets` by `score` descending (ties by list
    order), take the top `k`; a slot qualifies via strict `>` against the
    hurdle score (0 without a `hurdle` symbol) — one absolute test on
    `filter_on` for all slots when set, else per asset; `filter_none` skips
    the test entirely and every ranked slot qualifies. Each qualified slot
    holds `(1 - d) / k`; the canary fraction `d` plus every failed slot's
    share is routed to `fallback` (None = cash). An asset selected both
    offensively and defensively accumulates weight. While any required score
    is still None, everything sits in cash — a ranking over partial scores
    would silently reorder the universe (§5.1.1).

    The universe trick is the SafeSwitch precedent: `weights` holds every
    symbol the strategy can ever own at 0.0, and `balance()` returns the full
    key set every rebalance day, so `set(balance) == set(weights)` holds
    always."""

    def __init__(
        self,
        assets: list[str] | tuple[str, ...],
        k: int,
        score: Indicator,
        filter_on: str | None = None,
        hurdle: str | None = None,
        filter_none: bool = False,
        fallback: str | dict[str, float] | BestOf | None = None,
        canary: Canary | None = None,
        label: str | None = None,
    ):
        assets = tuple(assets)
        assert assets and len(set(assets)) == len(assets), (
            f"rotation: assets must be non-empty and unique, got {assets}"
        )
        assert 1 <= k <= len(assets), (
            f"rotation: need 1 <= k <= {len(assets)}, got {k}"
        )
        assert filter_on is None or filter_on != hurdle, (
            f"rotation: filter_on equals hurdle {hurdle!r}"
        )
        assert not (filter_none and (filter_on or hurdle)), (
            "rotation: filter_none excludes filter_on and hurdle"
        )
        if isinstance(fallback, dict):
            assert abs(sum(fallback.values()) - 1) <= 1e-9, (
                f"rotation: fallback sleeve fractions sum to {sum(fallback.values()):g}"
            )
        self.assets = assets
        self.k = k
        self.score = score
        self.filter_on = filter_on
        self.hurdle = hurdle
        self.filter_none = filter_none
        self.fallback = fallback
        self.canary = canary
        if label is not None:
            self.label = label

        self.weights = {
            s: 0.0 for s in dict.fromkeys((*assets, *_held(fallback)))
        }
        self.data = tuple(
            s
            for s in dict.fromkeys(
                (
                    *(() if filter_on is None else (filter_on,)),
                    *(() if hurdle is None else (hurdle,)),
                    *(canary.symbols if canary else ()),
                )
            )
            if s not in self.weights
        )
        # Name-keyed per-symbol merge like VolTarget.indicators, so a canary
        # or best_of sharing the main score declares it once.
        merged: dict[str, dict[str, Indicator]] = {}
        for symbol in (*assets, filter_on, hurdle):
            if symbol is not None:
                merged.setdefault(symbol, {})[score.name] = score
        if canary:
            for symbol in canary.symbols:
                merged.setdefault(symbol, {})[canary.score.name] = canary.score
        if isinstance(fallback, BestOf):
            for symbol in fallback.symbols:
                merged.setdefault(symbol, {})[fallback.score.name] = fallback.score
        self.indicators = {s: tuple(d.values()) for s, d in merged.items()}

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        scores = {s: ctx.indicator(s, self.score.name) for s in self.assets}
        hurdle = ctx.indicator(self.hurdle, self.score.name) if self.hurdle else 0.0
        gate = ctx.indicator(self.filter_on, self.score.name) if self.filter_on else None
        canary = (
            [ctx.indicator(s, self.canary.score.name) for s in self.canary.symbols]
            if self.canary
            else []
        )
        best = (
            [ctx.indicator(s, self.fallback.score.name) for s in self.fallback.symbols]
            if isinstance(self.fallback, BestOf)
            else []
        )
        required = [*scores.values(), hurdle, *canary, *best]
        if self.filter_on:
            required.append(gate)
        # 1. Warm-up short-circuit: all cash until every required score exists.
        if any(v is None for v in required):
            return {s: 0.0 for s in self.weights}

        # 2. Canary fraction.
        d = 0.0
        if self.canary:
            n_bad = sum(1 for v in canary if v <= 0)
            d = min(1.0, n_bad / self.canary.breadth)

        # 3-4. Rank (stable sort over `assets` order breaks exact ties) and
        # qualify each top-k slot with strict `>` — unconditionally under
        # `filter_none`, which is ranking without an absolute test.
        top = sorted(self.assets, key=lambda s: -scores[s])[: self.k]
        if self.filter_none:
            qualified = top
        elif self.filter_on:
            qualified = top if gate > hurdle else []
        else:
            qualified = [s for s in top if scores[s] > hurdle]

        # 5. Each qualified slot (1 - d) / k; the rest joins the pool.
        slot = (1.0 - d) / self.k
        allocation = {s: 0.0 for s in self.weights}
        for s in qualified:
            allocation[s] += slot
        pool = d + slot * (self.k - len(qualified))

        # 6-7. Defensive routing; a role collision accumulates. Cash fallback
        # simply leaves the pool unallocated.
        if pool > 0 and self.fallback is not None:
            if isinstance(self.fallback, BestOf):
                # max keeps the first maximal element: ties go to list order.
                winner = max(range(len(best)), key=best.__getitem__)
                allocation[self.fallback.symbols[winner]] += pool
            elif isinstance(self.fallback, dict):
                for s, f in self.fallback.items():
                    allocation[s] += pool * f
            else:
                allocation[self.fallback] += pool
        return allocation
