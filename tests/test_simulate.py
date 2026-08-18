import datetime as dt
import math
from pathlib import Path

import polars as pl
import pytest

from simulate import Config, simulate
from strategy import MarketDay, Strategy

GOLDEN_DIR = Path(__file__).parent / "data"  # frozen snapshot; numbers are pinned to it
START = dt.date(2020, 1, 2)


def frame(columns: dict[str, list[float]], rebalance: list[bool]) -> pl.DataFrame:
    """Build a synthetic price frame whose first date is START.

    `columns` holds the close of each symbol and any indicator columns, which
    the loader names "SYMBOL:INDICATOR".
    """
    dates = [START + dt.timedelta(days=i) for i in range(len(rebalance))]
    return pl.DataFrame(
        {"date": dates, **columns, "is_rebalance_day": rebalance},
        schema={
            "date": pl.Date,
            **{name: pl.Float64 for name in columns},
            "is_rebalance_day": pl.Boolean,
        },
    )


def half_and_half() -> Strategy:
    return Strategy(label="test", weights={"A": 0.5, "B": 0.5})


class Gated(Strategy):
    """50/50 A and B, refusing to buy the assets in `blocked` on days the
    "A:GATE" column reads 0."""

    label = "gated"
    weights = {"A": 0.5, "B": 0.5}
    blocked = ()

    def allow_buy(self, asset: str, ctx: MarketDay) -> bool:
        return asset not in self.blocked or ctx.indicator("A", "GATE") == 1.0


def test_initial_buy():
    # 10000 buys floor(5000/30) = 166 of A (4980) and floor(5000/7) = 714 of B
    # (4998), leaving 22 in cash. The second day's prices reveal the holdings.
    prices = frame({"A": [30.0, 31.0], "B": [7.0, 8.0]}, [False, False])
    config = Config(START, 10000.0, 500.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert result["flow"].to_list() == [10000.0, 0.0]
    assert result["value"][0] == pytest.approx(166 * 30.0 + 714 * 7.0 + 22.0)
    assert result["value"][0] == pytest.approx(10000.0)
    assert result["value"][1] == pytest.approx(166 * 31.0 + 714 * 8.0 + 22.0)

    assert trades["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    assert trades["asset"].to_list() == [None, "A", "B"]
    assert trades["shares"].to_list() == [None, 166, 714]
    assert trades["amount"].to_list() == pytest.approx([10000.0, 4980.0, 4998.0])
    assert trades["cash_after"][-1] == pytest.approx(22.0)

    assert allocations["asset"].to_list() == ["A", "B", "CASH"]
    assert allocations["target"].to_list() == pytest.approx([0.5, 0.5, 0.0])
    assert allocations["actual"].to_list() == pytest.approx([0.498, 0.4998, 0.0022])


def test_rebalance_sells_the_overweight_asset():
    # Day 0: 50 of each at 10.0, no cash. Day 1: A has risen to 21.0, so with the
    # 100 contribution total = 1050 + 500 + 100 = 1650. Targets are
    # floor(825/21) = 39 of A (sell 11, +231 cash) and floor(825/10) = 82 of B
    # (buy 32, -320 cash), leaving 331 - 320 = 11 in cash.
    prices = frame({"A": [10.0, 21.0, 100.0], "B": [10.0, 10.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert result["flow"].to_list() == [1000.0, 100.0, 0.0]
    assert result["value"][0] == pytest.approx(1000.0)
    assert result["value"][1] == pytest.approx(1650.0)
    # Day 2's lopsided prices pin down the exact share counts and the cash.
    assert result["value"][2] == pytest.approx(39 * 100.0 + 82 * 1.0 + 11.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "SELL", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 11, 32]


def test_rebalance_contribution_covers_the_underweight_buy():
    # Same start, but a 500 contribution against a milder move in A: total =
    # 550 + 500 + 500 = 1550. Targets are floor(775/11) = 70 of A and
    # floor(775/10) = 77 of B — both above the 50 held, so nothing is sold.
    prices = frame({"A": [10.0, 11.0, 100.0], "B": [10.0, 10.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 500.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert result["value"][1] == pytest.approx(1550.0)
    assert result["value"][2] == pytest.approx(70 * 100.0 + 77 * 1.0 + 10.0)
    assert "SELL" not in trades["action"].to_list()


def test_single_asset_only_accumulates():
    closes = [30.0, 7.0, 12.5, 40.0, 16.0, 50.0, 10.0, 32.0, 8.0, 64.0, 25.0, 20.0]
    rebalance = [i in (1, 3, 5, 7, 9) for i in range(len(closes))]
    prices = frame({"A": closes}, rebalance)
    config = Config(START, 10000.0, 500.0)
    strategy = Strategy(label="test", weights={"A": 1.0})

    # With a single asset the rebalance degenerates to "spend the cash on as many
    # whole shares as it buys", which never sells and always leaves cash < close.
    shares, cash, expected = 0, 0.0, []
    for close, is_rebalance in zip(closes, rebalance):
        if not expected:
            cash += config.initial_capital
            shares = math.floor(cash / close)
            cash -= shares * close
        elif is_rebalance:
            cash += config.monthly_contribution
            bought = math.floor(cash / close)
            assert bought >= 0
            shares += bought
            cash -= bought * close
            assert cash < close
        expected.append(shares * close + cash)

    assert simulate(prices, strategy, config)[0]["value"].to_list() == pytest.approx(expected)
    assert shares == 451


def test_gate_redirects_the_blocked_budget():
    # Day 0 buys 50 of each at 10.0 with the gate open. Day 1 closes the gate on
    # A: total = 500 + 500 + 100 = 1100, and A's natural target of floor(550/10)
    # = 55 is capped at the 50 already held. That leaves 1100 - 500 = 600 for B,
    # the only asset still open, so B goes to floor(600/10) = 60 and cash to 0.
    prices = frame(
        {
            "A": [10.0, 10.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Gated(blocked=("A",)), config)

    assert result["value"][1] == pytest.approx(1100.0)
    assert result["value"][2] == pytest.approx(50 * 100.0 + 60 * 1.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "BUY"]
    assert day1["asset"].to_list() == [None, "B"]
    assert day1["shares"].to_list() == [None, 10]

    # Post-trade allocation shows the gate's footprint: A stuck at its held
    # 500/1100 against a 50% target, B over-target with the redirected budget.
    day1_alloc = allocations.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1_alloc["asset"].to_list() == ["A", "B", "CASH"]
    assert day1_alloc["target"].to_list() == pytest.approx([0.5, 0.5, 0.0])
    assert day1_alloc["actual"].to_list() == pytest.approx(
        [500 / 1100, 600 / 1100, 0.0]
    )


def test_gate_still_sells_the_blocked_asset():
    # A gated but overweight: A trebles to 30.0, so total = 1500 + 500 + 100 =
    # 2100 and A's target of floor(1050/30) = 35 is below the 50 held. The gate
    # blocks buys only, so A sells 15 (+450), and the 2100 - 1050 = 1050 left
    # over takes B to floor(1050/10) = 105, a buy of 55 that spends the cash
    # exactly.
    prices = frame(
        {
            "A": [10.0, 30.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Gated(blocked=("A",)), config)

    assert result["value"][1] == pytest.approx(2100.0)
    assert result["value"][2] == pytest.approx(35 * 100.0 + 105 * 1.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "SELL", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 15, 55]


def test_every_asset_gated_leaves_the_contribution_in_cash():
    # Both assets blocked and neither overweight, so the rebalance has nothing to
    # do: the 100 contribution simply sits in cash until a later rebalance.
    prices = frame(
        {
            "A": [10.0, 10.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Gated(blocked=("A", "B")), config)

    assert result["value"][1] == pytest.approx(1100.0)
    assert result["value"][2] == pytest.approx(50 * 100.0 + 50 * 1.0 + 100.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT"]


def test_balance_can_move_the_weights():
    class Tilt(Strategy):
        """All in A, then all in B from the second day on."""

        label = "tilt"
        weights = {"A": 1.0, "B": 0.0}

        def balance(self, ctx: MarketDay) -> dict[str, float]:
            if ctx.date > START:
                return {"A": 0.0, "B": 1.0}
            return self.weights

    # Day 0 puts the whole 1000 into 100 of A. Day 1 flips the weights: total =
    # 1000 + 100 = 1100, so A sells all 100 and B buys floor(1100/20) = 55.
    prices = frame({"A": [10.0, 10.0, 100.0], "B": [10.0, 20.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Tilt(), config)

    assert result["value"][0] == pytest.approx(1000.0)
    assert result["value"][1] == pytest.approx(1100.0)
    assert result["value"][2] == pytest.approx(55 * 1.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "SELL", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 100, 55]


def test_market_day_missing_value_is_none_but_missing_column_raises():
    day = MarketDay({"date": START, "A": 10.0, "A:SMA200": None})

    assert day.date == START
    assert day.close("A") == 10.0
    assert day.indicator("A", "SMA200") is None
    with pytest.raises(KeyError):
        day.close("B")  # symbol never loaded
    with pytest.raises(KeyError):
        day.indicator("A", "RSI")  # typo'd indicator name


def test_real_data_invariants():
    from prices import load_prices

    start = dt.date(2017, 1, 3)
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL", "SPY"], start)
    config = Config(start, 10000.0, 500.0)
    strategy = Strategy(label="test", weights={"TQQQ": 0.5, "BTAL": 0.5})

    result, trades, allocations = simulate(prices, strategy, config)

    assert len(result) == len(prices)
    assert result["date"].to_list() == prices["date"].to_list()
    assert result["flow"].sum() == pytest.approx(67500.0)
    assert result["value"].min() > 0.0
    deposits = trades.filter(pl.col("action") == "DEPOSIT")
    assert deposits["amount"].sum() == pytest.approx(67500.0)
    assert trades["cash_after"].min() >= 0.0

    from stats import imbalance

    off = imbalance(allocations)
    assert 0.0 <= off["misallocated"].min() and off["misallocated"].max() < 1.0
    # Without gates only integer rounding misbalances the plain 50/50.
    assert off["misallocated"].mean() < 0.01
