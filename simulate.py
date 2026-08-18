"""Simulation of a monthly-rebalanced, integer-share portfolio."""

import datetime as dt
import math
from dataclasses import dataclass

import polars as pl

from strategy import MarketDay, Strategy


@dataclass(frozen=True)
class Config:
    start: dt.date
    initial_capital: float
    monthly_contribution: float


def simulate(
    prices: pl.DataFrame, strategy: Strategy, config: Config
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Run `strategy` over `prices`, one row per trading day.

    Returns three frames: the equity curve of `date`, `value` (holdings at close
    plus cash) and `flow` (external capital added that day); a transaction
    log of every DEPOSIT/BUY/SELL with the cash balance after each; and the
    post-trade allocations on each trade day — per asset (plus a CASH row) the
    fraction of the portfolio the strategy's balance() targeted and the fraction
    actually held. Columns the strategy does not trade — the extra symbols and
    indicators its hooks read — never count towards the portfolio's value.
    """
    assets = list(strategy.weights)
    shares = dict.fromkeys(assets, 0)
    cash = 0.0
    rows = []
    trades = []
    allocations = []

    def log(date, action, asset=None, delta=0, price=None, amount=0.0):
        trades.append(
            {
                "date": date,
                "action": action,
                "asset": asset,
                "shares": abs(delta) if delta else None,
                "price": price,
                "amount": amount,
                "cash_after": cash,
            }
        )

    for i, row in enumerate(prices.iter_rows(named=True)):
        flow = 0.0

        if i == 0:
            assert row["date"] == config.start
            cash += config.initial_capital
            flow += config.initial_capital
            log(row["date"], "DEPOSIT", amount=config.initial_capital)

        if row["is_rebalance_day"]:
            cash += config.monthly_contribution
            flow += config.monthly_contribution
            log(row["date"], "DEPOSIT", amount=config.monthly_contribution)

        if i == 0 or row["is_rebalance_day"]:
            ctx = MarketDay(row, contribution=flow)
            weights = strategy.balance(ctx)
            assert set(weights) == set(assets)
            assert all(w >= 0 for w in weights.values())
            assert sum(weights.values()) <= 1 + 1e-9
            total = sum(shares[a] * row[a] for a in assets) + cash

            # What each asset would hold if nothing were gated.
            target = {a: math.floor(total * weights[a] / row[a]) for a in assets}
            caps = {a: strategy.buy_cap(a, ctx) for a in assets}
            gated = [a for a in assets if caps[a] is not None]
            for asset in gated:
                assert caps[asset] >= 0
                target[asset] = min(
                    target[asset], shares[asset] + math.floor(caps[asset] / row[asset])
                )
            # The budget a gated asset declines is spent on the assets still open,
            # split by their weights among themselves. Scaling by the weight sum
            # keeps any cash fraction the strategy left unallocated uninvested.
            remaining = total * sum(weights.values()) - sum(
                target[a] * row[a] for a in gated
            )
            open_weight = sum(weights[a] for a in assets if a not in gated)
            if open_weight > 0:
                for asset in assets:
                    if asset not in gated:
                        target[asset] = math.floor(
                            remaining * (weights[asset] / open_weight) / row[asset]
                        )

            deltas = {a: target[a] - shares[a] for a in assets}
            # Sells before buys, so the running cash balance never goes negative.
            for asset in sorted(assets, key=lambda a: deltas[a]):
                delta = deltas[asset]
                cash -= delta * row[asset]
                shares[asset] += delta
                if delta:
                    log(
                        row["date"], "BUY" if delta > 0 else "SELL", asset,
                        delta, row[asset], abs(delta) * row[asset],
                    )

            # The trades happen at the closes used to value `total`, so the
            # post-trade allocation can be taken against the same total.
            for asset in assets:
                allocations.append(
                    {
                        "date": row["date"],
                        "asset": asset,
                        "target": weights[asset],
                        "actual": shares[asset] * row[asset] / total,
                    }
                )
            allocations.append(
                {
                    "date": row["date"],
                    "asset": "CASH",
                    "target": 1.0 - sum(weights.values()),
                    "actual": cash / total,
                }
            )

        assert cash >= -1e-6
        rows.append(
            {
                "date": row["date"],
                "value": sum(shares[a] * row[a] for a in assets) + cash,
                "flow": flow,
            }
        )

    curve = pl.DataFrame(
        rows, schema={"date": pl.Date, "value": pl.Float64, "flow": pl.Float64}
    )
    trades_frame = pl.DataFrame(
        trades,
        schema={
            "date": pl.Date,
            "action": pl.Utf8,
            "asset": pl.Utf8,
            "shares": pl.Int64,
            "price": pl.Float64,
            "amount": pl.Float64,
            "cash_after": pl.Float64,
        },
    )
    allocations_frame = pl.DataFrame(
        allocations,
        schema={
            "date": pl.Date,
            "asset": pl.Utf8,
            "target": pl.Float64,
            "actual": pl.Float64,
        },
    )
    return curve, trades_frame, allocations_frame
