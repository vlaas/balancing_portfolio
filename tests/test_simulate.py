import datetime as dt
import math
from pathlib import Path

import polars as pl
import pytest

from simulate import Config, simulate

DATA_DIR = Path(__file__).parent.parent / "data"
START = dt.date(2020, 1, 2)


def frame(closes: dict[str, list[float]], rebalance: list[bool]) -> pl.DataFrame:
    """Build a synthetic price frame whose first date is START."""
    dates = [START + dt.timedelta(days=i) for i in range(len(rebalance))]
    return pl.DataFrame(
        {"date": dates, **closes, "is_rebalance_day": rebalance},
        schema={
            "date": pl.Date,
            **{symbol: pl.Float64 for symbol in closes},
            "is_rebalance_day": pl.Boolean,
        },
    )


def test_initial_buy():
    # 10000 buys floor(5000/30) = 166 of A (4980) and floor(5000/7) = 714 of B
    # (4998), leaving 22 in cash. The second day's prices reveal the holdings.
    prices = frame({"A": [30.0, 31.0], "B": [7.0, 8.0]}, [False, False])
    config = Config(START, 10000.0, 500.0, {"A": 0.5, "B": 0.5})

    result, trades = simulate(prices, config)

    assert result["flow"].to_list() == [10000.0, 0.0]
    assert result["value"][0] == pytest.approx(166 * 30.0 + 714 * 7.0 + 22.0)
    assert result["value"][0] == pytest.approx(10000.0)
    assert result["value"][1] == pytest.approx(166 * 31.0 + 714 * 8.0 + 22.0)

    assert trades["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    assert trades["asset"].to_list() == [None, "A", "B"]
    assert trades["shares"].to_list() == [None, 166, 714]
    assert trades["amount"].to_list() == pytest.approx([10000.0, 4980.0, 4998.0])
    assert trades["cash_after"][-1] == pytest.approx(22.0)


def test_rebalance_sells_the_overweight_asset():
    # Day 0: 50 of each at 10.0, no cash. Day 1: A has risen to 21.0, so with the
    # 100 contribution total = 1050 + 500 + 100 = 1650. Targets are
    # floor(825/21) = 39 of A (sell 11, +231 cash) and floor(825/10) = 82 of B
    # (buy 32, -320 cash), leaving 331 - 320 = 11 in cash.
    prices = frame({"A": [10.0, 21.0, 100.0], "B": [10.0, 10.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 100.0, {"A": 0.5, "B": 0.5})

    result, trades = simulate(prices, config)

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
    config = Config(START, 1000.0, 500.0, {"A": 0.5, "B": 0.5})

    result, trades = simulate(prices, config)

    assert result["value"][1] == pytest.approx(1550.0)
    assert result["value"][2] == pytest.approx(70 * 100.0 + 77 * 1.0 + 10.0)
    assert "SELL" not in trades["action"].to_list()


def test_single_asset_only_accumulates():
    closes = [30.0, 7.0, 12.5, 40.0, 16.0, 50.0, 10.0, 32.0, 8.0, 64.0, 25.0, 20.0]
    rebalance = [i in (1, 3, 5, 7, 9) for i in range(len(closes))]
    prices = frame({"A": closes}, rebalance)
    config = Config(START, 10000.0, 500.0, {"A": 1.0})

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

    assert simulate(prices, config)[0]["value"].to_list() == pytest.approx(expected)
    assert shares == 451


def test_real_data_invariants():
    from prices import load_prices

    start = dt.date(2017, 1, 3)
    prices = load_prices(DATA_DIR, ["TQQQ", "BTAL", "SPY"], start)
    config = Config(start, 10000.0, 500.0, {"TQQQ": 0.5, "BTAL": 0.5})

    result, trades = simulate(prices, config)

    assert len(result) == len(prices)
    assert result["date"].to_list() == prices["date"].to_list()
    assert result["flow"].sum() == pytest.approx(67500.0)
    assert result["value"].min() > 0.0
    deposits = trades.filter(pl.col("action") == "DEPOSIT")
    assert deposits["amount"].sum() == pytest.approx(67500.0)
    assert trades["cash_after"].min() >= 0.0
