"""Strategy bundles: named comparisons, each a list of strategies plus its Config.

The last strategy in every bundle is the benchmark — the reference for the
correlation statistics (main.py reads results[-1]).
"""

import datetime as dt
from dataclasses import dataclass

from simulate import Config
from strategies.spy_benchmark import SpyBenchmark
from strategies.tqqq_100 import Tqqq100
from strategies.tqqq_btal_5050 import TqqqBtal5050
from strategies.tqqq_btal_qqq_sma200 import TqqqBtalQqqSma200
from strategy import Strategy


@dataclass(frozen=True)
class Bundle:
    strategies: list[Strategy]  # benchmark last
    config: Config


BUNDLES = {
    "default": Bundle(
        strategies=[
            TqqqBtal5050(),
            Tqqq100(),
            TqqqBtalQqqSma200(),
            SpyBenchmark(),  # last: the correlation reference
        ],
        config=Config(
            start=dt.date(2017, 1, 3), initial_capital=10_000, monthly_contribution=500
        ),
    ),
}
