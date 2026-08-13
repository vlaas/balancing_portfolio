import datetime as dt

import polars as pl
import pytest

from stats import (
    correlation,
    rolling_sharpe,
    summary,
    top_drawdowns,
    twr,
    xirr,
)

START = dt.date(2020, 1, 1)


def days(n: int) -> list[dt.date]:
    return [START + dt.timedelta(days=i) for i in range(n)]


def curve(values: list[float], flows: list[float], dates: list[dt.date] | None = None) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date": dates or days(len(values)),
            "value": [float(v) for v in values],
            "flow": [float(f) for f in flows],
        }
    )


def index_frame(values: list[float], dates: list[dt.date] | None = None) -> pl.DataFrame:
    return pl.DataFrame({"date": dates or days(len(values)), "index": [float(v) for v in values]})


def npv(rate: float, dates: list[dt.date], amounts: list[float]) -> float:
    return sum(
        cf * (1.0 + rate) ** (-((d - dates[0]).days) / 365) for d, cf in zip(dates, amounts)
    )


# 1. TWR flow adjustment


def test_flows_alone_produce_zero_returns():
    """Flat prices: value grows only by the flows, so every return is 0."""
    flows = [1000.0, 0.0, 500.0, 0.0, 500.0]
    values = [1000.0, 1000.0, 1500.0, 1500.0, 2000.0]

    frame = twr(curve(values, flows))

    assert frame["ret"][0] is None
    assert frame["ret"][1:].to_list() == [0.0, 0.0, 0.0, 0.0]
    assert frame["index"].to_list() == [1.0, 1.0, 1.0, 1.0, 1.0]


def test_flow_on_the_day_is_not_counted_as_return():
    with_flow = twr(curve([100.0, 110.0], [0.0, 10.0]))
    without_flow = twr(curve([100.0, 110.0], [0.0, 0.0]))

    assert with_flow["ret"][1] == pytest.approx(0.0)
    assert without_flow["ret"][1] == pytest.approx(0.10)


# 2. XIRR


def test_xirr_single_year_round_trip():
    dates = [START, START + dt.timedelta(days=365)]
    assert xirr(dates, [-1000.0, 1100.0]) == pytest.approx(0.10, abs=1e-6)


def test_xirr_multiple_flows_zeroes_the_npv():
    dates = [START, START + dt.timedelta(days=182), START + dt.timedelta(days=365)]
    amounts = [-1000.0, -500.0, 1700.0]

    rate = xirr(dates, amounts)

    assert npv(rate, dates, amounts) == pytest.approx(0.0, abs=1e-6)
    assert 0.0 < rate < 1.0


# 3. Drawdowns

DRAWDOWN_INDEX = [1.0, 1.1, 0.99, 1.05, 1.21, 0.9, 1.0, 1.22, 1.1]


def test_drawdown_episodes_are_deepest_first():
    d = days(len(DRAWDOWN_INDEX))

    episodes = top_drawdowns(index_frame(DRAWDOWN_INDEX))

    assert len(episodes) == 3

    deepest, second, ongoing = episodes
    assert (deepest.peak, deepest.trough, deepest.recovery) == (d[4], d[5], d[7])
    assert deepest.depth == pytest.approx(0.9 / 1.21 - 1)
    assert deepest.days == 3

    assert (second.peak, second.trough, second.recovery) == (d[1], d[2], d[4])
    assert second.depth == pytest.approx(0.99 / 1.1 - 1)
    assert second.days == 3

    assert (ongoing.peak, ongoing.trough) == (d[7], d[8])
    assert ongoing.recovery is None
    assert ongoing.days is None
    assert ongoing.depth == pytest.approx(1.1 / 1.22 - 1)


def test_drawdowns_are_limited_to_n():
    assert len(top_drawdowns(index_frame(DRAWDOWN_INDEX), n=2)) == 2


# 4. Rolling Sharpe


def test_rolling_sharpe_warmup_is_null():
    rets = [None, 0.01, -0.02, 0.03, 0.005, -0.01, 0.02, -0.005, 0.015, 0.0]
    frame = pl.DataFrame({"date": days(len(rets)), "ret": rets}, schema_overrides={"ret": pl.Float64})

    sharpe = rolling_sharpe(frame, window=3)["sharpe"]

    assert len(sharpe) == len(rets)
    assert sharpe.null_count() == 3
    assert sharpe[:3].to_list() == [None, None, None]


def test_rolling_sharpe_is_null_when_returns_are_constant():
    rets = [None] + [0.01] * 6
    frame = pl.DataFrame({"date": days(len(rets)), "ret": rets}, schema_overrides={"ret": pl.Float64})

    sharpe = rolling_sharpe(frame, window=3)["sharpe"]

    assert sharpe.to_list() == [None] * len(rets)


# Correlation


def test_correlation_of_a_series_with_itself_is_one():
    frame = twr(curve([100.0, 110.0, 105.0, 120.0], [0.0, 0.0, 0.0, 0.0]))
    assert correlation(frame, frame) == pytest.approx(1.0)


# 5. Summary

SUMMARY_KEYS = {
    "final_value",
    "total_contributed",
    "net_profit",
    "net_profit_pct",
    "cagr",
    "xirr",
    "sharpe",
    "volatility",
    "sortino",
    "calmar",
    "max_drawdown",
    "max_drawdown_days",
    "best_year",
    "worst_year",
}


def summary_curve() -> pl.DataFrame:
    dates = [
        dt.date(2020, 1, 1),
        dt.date(2020, 7, 1),
        dt.date(2021, 1, 1),
        dt.date(2021, 7, 1),
        dt.date(2022, 1, 1),
    ]
    return curve([1000.0, 900.0, 1500.0, 1400.0, 1800.0], [1000.0, 0.0, 500.0, 0.0, 0.0], dates)


def test_summary_money_figures():
    c = summary_curve()

    result = summary(c, twr(c))

    assert result["final_value"] == pytest.approx(1800.0)
    assert result["total_contributed"] == pytest.approx(1500.0)
    assert result["net_profit"] == pytest.approx(300.0)
    assert result["net_profit_pct"] == pytest.approx(0.2)


def test_summary_reports_every_contract_key():
    c = summary_curve()

    result = summary(c, twr(c))

    assert set(result) == SUMMARY_KEYS
    assert result["best_year"][0] in (2020, 2021, 2022)
    assert result["worst_year"][1] <= result["best_year"][1]
    assert result["max_drawdown"] < 0.0
