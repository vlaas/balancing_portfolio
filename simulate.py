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


def simulate(prices: pl.DataFrame, config: Config) -> pl.DataFrame:
    """Run the portfolio over `prices`, one row per trading day.

    Returns a frame of `date`, `value` (holdings at close plus cash) and `flow`
    (external capital added that day). Symbol columns not named in
    `config.weights` are ignored.
    """
    assets = list(config.weights)
    shares = dict.fromkeys(assets, 0)
    cash = 0.0
    rows = []

    for i, row in enumerate(prices.iter_rows(named=True)):
        flow = 0.0

        if i == 0:
            assert row["date"] == config.start
            cash += config.initial_capital
            flow += config.initial_capital
            for asset in assets:
                shares[asset] = math.floor(
                    config.initial_capital * config.weights[asset] / row[asset]
                )
                cash -= shares[asset] * row[asset]

        if row["is_rebalance_day"]:
            cash += config.monthly_contribution
            flow += config.monthly_contribution
            total = sum(shares[a] * row[a] for a in assets) + cash
            for asset in assets:
                target = math.floor(total * config.weights[asset] / row[asset])
                cash -= (target - shares[asset]) * row[asset]
                shares[asset] = target

        assert cash >= -1e-6
        rows.append(
            {
                "date": row["date"],
                "value": sum(shares[a] * row[a] for a in assets) + cash,
                "flow": flow,
            }
        )

    return pl.DataFrame(
        rows, schema={"date": pl.Date, "value": pl.Float64, "flow": pl.Float64}
    )
