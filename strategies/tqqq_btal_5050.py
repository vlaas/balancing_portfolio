from strategy import Strategy


class TqqqBtal5050(Strategy):
    """Half TQQQ, half BTAL, rebalanced every month."""

    label = "TQQQ/BTAL 50/50"
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
