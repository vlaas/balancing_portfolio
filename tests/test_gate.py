# The Gate component — DECLARATIVE_SPEC.md T5.

import datetime as dt

import pytest

from strategies.fixed import Fixed
from strategies.gate import Gate

from strategy import MarketDay

DAY = dt.date(2020, 1, 2)


def market_day(close, sma, contribution=0.0) -> MarketDay:
    return MarketDay(
        {"date": DAY, "QQQ": close, "QQQ:SMA200": sma}, contribution=contribution
    )


def gate(**kwargs) -> Gate:
    return Gate("QQQ", ["TQQQ"], sma_days=200, **kwargs)


def test_closed_iff_close_below_sma():
    assert gate().closed(market_day(99.0, 100.0))
    assert not gate().closed(market_day(100.0, 100.0))  # the equal case stays open
    assert not gate().closed(market_day(101.0, 100.0))


def test_open_while_either_value_is_none():
    assert not gate().closed(market_day(None, 100.0))
    assert not gate().closed(market_day(99.0, None))
    assert not gate().closed(market_day(None, None))


def test_exactly_one_sma_length():
    with pytest.raises(AssertionError):
        Gate("QQQ", ["TQQQ"])
    with pytest.raises(AssertionError):
        Gate("QQQ", ["TQQQ"], sma_days=200, sma_months=10)


def test_buy_cap():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    open_day = market_day(101.0, 100.0)
    closed_day = market_day(99.0, 100.0, contribution=500.0)

    assert gate().buy_cap("TQQQ", open_day, weights) is None
    assert gate().buy_cap("BTAL", closed_day, weights) is None  # not a gated asset
    assert gate().buy_cap("TQQQ", closed_day, weights) == 0.0

    exempt = gate(contribution_exempt=True)
    assert exempt.buy_cap("TQQQ", closed_day, weights) == 500.0 * 0.5
    assert exempt.buy_cap("TQQQ", open_day, weights) is None
    # A closed day without external cash allows nothing even when exempt.
    assert exempt.buy_cap("TQQQ", market_day(99.0, 100.0), weights) == 0.0


def test_monthly_variant_reads_the_monthly_column():
    monthly = Gate("QQQ", ["TQQQ"], sma_months=10)
    assert monthly.column == "SMA10M"
    day = MarketDay({"date": DAY, "QQQ": 99.0, "QQQ:SMA10M": 100.0})
    assert monthly.closed(day)


def test_fixed_declares_the_gate_symbol():
    st = Fixed(weights={"TQQQ": 0.5, "BTAL": 0.5}, gate=gate())
    assert st.data == ("QQQ",)
    assert [i.name for i in st.indicators["QQQ"]] == ["SMA200"]

    traded = Fixed(weights={"QQQ": 1.0}, gate=Gate("QQQ", ["QQQ"], sma_days=200))
    assert traded.data == ()
    assert [i.name for i in traded.indicators["QQQ"]] == ["SMA200"]
