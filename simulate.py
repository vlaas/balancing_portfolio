"""Simulation of a monthly-rebalanced, integer-share portfolio."""

import datetime as dt
import math
from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class Config:
    start: dt.date
    initial_capital: float
    monthly_contribution: float
    weights: dict[str, float]


def simulate(prices: pl.DataFrame, config: Config) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Run the portfolio over `prices`, one row per trading day.

    Returns two frames: the equity curve of `date`, `value` (holdings at close
    plus cash) and `flow` (external capital added that day), and a transaction
    log of every DEPOSIT/BUY/SELL with the cash balance after each. Symbol
    columns not named in `config.weights` are ignored.
    """
    assets = list(config.weights)
    shares = dict.fromkeys(assets, 0)
    cash = 0.0
    rows = []
    trades = []

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
            for asset in assets:
                shares[asset] = math.floor(
                    config.initial_capital * config.weights[asset] / row[asset]
                )
                cash -= shares[asset] * row[asset]
                if shares[asset]:
                    log(
                        row["date"], "BUY", asset, shares[asset], row[asset],
                        shares[asset] * row[asset],
                    )

        if row["is_rebalance_day"]:
            cash += config.monthly_contribution
            flow += config.monthly_contribution
            log(row["date"], "DEPOSIT", amount=config.monthly_contribution)
            total = sum(shares[a] * row[a] for a in assets) + cash
            deltas = {
                a: math.floor(total * config.weights[a] / row[a]) - shares[a]
                for a in assets
            }
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
    return curve, trades_frame
