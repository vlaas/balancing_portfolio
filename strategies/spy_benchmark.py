from strategy import Strategy


class SpyBenchmark(Strategy):
    """Everything in SPY, the yardstick the other strategies are measured against."""

    label = "SPY benchmark"
    weights = {"SPY": 1.0}
