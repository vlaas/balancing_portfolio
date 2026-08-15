from strategy import Strategy


class Tqqq100(Strategy):
    """Everything in TQQQ."""

    label = "TQQQ 100%"
    weights = {"TQQQ": 1.0}
