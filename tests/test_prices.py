import datetime as dt
from collections.abc import Iterable
from pathlib import Path

import polars as pl
import pytest

from bundles import BUNDLES
from indicators import sma
from main import collect_indicators
from prices import load_prices

GOLDEN_DIR = Path(__file__).parent / "data"  # frozen snapshot; numbers are pinned to it
DATA_DIR = Path(__file__).parent.parent / "data"  # live export; no numeric assertions


def write_csv(
    data_dir: Path, symbol: str, rows: list[tuple], extra_columns: Iterable[str] = ()
) -> None:
    """Write a TradingView-shaped CSV of (date, close) rows plus any `extra_columns`."""
    header = ",".join(["time", "open", "high", "low", "close", *extra_columns])
    lines = [header]
    lines += [
        f"{date},0,0,0," + ",".join(str(value) for value in values) for date, *values in rows
    ]
    (data_dir / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def test_missing_date_is_forward_filled(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0), ("2020-01-06", 12.0)])
    write_csv(tmp_path, "B", [("2020-01-02", 20.0), ("2020-01-06", 22.0)])

    prices = load_prices(tmp_path, ["A", "B"], dt.date(2020, 1, 2))

    assert prices["date"].to_list() == [
        dt.date(2020, 1, 2),
        dt.date(2020, 1, 3),
        dt.date(2020, 1, 6),
    ]
    assert prices["B"].to_list() == [20.0, 20.0, 22.0]
    assert prices["A"].to_list() == [10.0, 11.0, 12.0]
    assert prices["A"].dtype == pl.Float64


def test_forward_fill_across_start_boundary(tmp_path):
    write_csv(
        tmp_path,
        "A",
        [("2020-01-02", 10.0), ("2020-01-03", 11.0), ("2020-01-06", 12.0)],
    )
    write_csv(tmp_path, "B", [("2020-01-02", 20.0), ("2020-01-06", 22.0)])

    prices = load_prices(tmp_path, ["A", "B"], dt.date(2020, 1, 3))

    assert prices["date"].to_list() == [dt.date(2020, 1, 3), dt.date(2020, 1, 6)]
    # B has no row on the start date; it carries forward from 2020-01-02.
    assert prices["B"].to_list() == [20.0, 22.0]


def test_rebalance_days_are_last_trading_day_of_month(tmp_path):
    dates = [
        "2020-11-27",
        "2020-11-30",  # last trading day of November
        "2020-12-01",
        "2020-12-31",  # last trading day of December, into a new year
        "2021-01-04",
        "2021-01-29",  # last trading day of January
        "2021-02-01",
        "2021-02-02",  # partial final month: not a rebalance day
    ]
    write_csv(tmp_path, "A", [(date, 10.0) for date in dates])

    prices = load_prices(tmp_path, ["A"], dt.date(2020, 11, 27))

    assert prices["is_rebalance_day"].to_list() == [
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        False,
    ]
    assert prices["is_rebalance_day"].last() is False


def test_extra_symbol_indicator_is_namespaced(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0)])
    write_csv(tmp_path, "X", [("2020-01-02", 5.0), ("2020-01-03", 6.0)])

    prices = load_prices(
        tmp_path, ["A"], dt.date(2020, 1, 2), extra=("X",), indicators={"X": (sma(2),)}
    )

    assert prices.columns == ["date", "A", "X", "X:SMA2", "is_rebalance_day"]
    assert prices["X"].to_list() == [5.0, 6.0]
    assert prices["X:SMA2"].to_list() == [None, 5.5]


def test_extra_symbol_does_not_extend_the_calendar(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0)])
    write_csv(
        tmp_path,
        "X",
        [("2020-01-02", 5.0), ("2020-01-03", 6.0), ("2020-01-06", 7.0)],
    )

    prices = load_prices(tmp_path, ["A"], dt.date(2020, 1, 2), extra=("X",))

    # X trades on 2020-01-06 but A does not, so the day is not on the calendar.
    assert prices["date"].to_list() == [dt.date(2020, 1, 2), dt.date(2020, 1, 3)]


def test_extra_symbol_is_null_before_its_history_starts(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0)])
    write_csv(tmp_path, "X", [("2020-01-03", 6.0)])

    prices = load_prices(
        tmp_path, ["A"], dt.date(2020, 1, 2), extra=("X",), indicators={"X": (sma(1),)}
    )

    assert prices["X"].to_list() == [None, 6.0]
    assert prices["X:SMA1"].to_list() == [None, 6.0]


def test_null_traded_close_still_trips_the_assert(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0)])
    write_csv(tmp_path, "B", [("2020-01-03", 20.0)])

    # B has nothing to carry forward onto the start date.
    with pytest.raises(AssertionError):
        load_prices(tmp_path, ["A", "B"], dt.date(2020, 1, 2))


def test_traded_symbol_indicator_is_namespaced_and_may_be_null(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0)])

    prices = load_prices(tmp_path, ["A"], dt.date(2020, 1, 2), indicators={"A": (sma(2),)})

    assert prices.columns == ["date", "A", "A:SMA2", "is_rebalance_day"]
    assert prices["A"].to_list() == [10.0, 11.0]
    # The no-nulls assert covers the close only, not the indicator beside it.
    assert prices["A:SMA2"].to_list() == [None, 10.5]


def test_indicator_forward_fills_across_a_date_its_symbol_lacks(tmp_path):
    write_csv(
        tmp_path,
        "A",
        [("2020-01-02", 1.0), ("2020-01-03", 1.0), ("2020-01-06", 1.0), ("2020-01-07", 1.0)],
    )
    # X does not trade on 2020-01-06, so its SMA is computed over three bars only.
    write_csv(tmp_path, "X", [("2020-01-02", 5.0), ("2020-01-03", 6.0), ("2020-01-07", 10.0)])

    prices = load_prices(
        tmp_path, ["A"], dt.date(2020, 1, 2), extra=("X",), indicators={"X": (sma(2),)}
    )

    assert prices["X"].to_list() == [5.0, 6.0, 6.0, 10.0]
    # 2020-01-06 carries 2020-01-03's value; the 01-07 value averages 6 and 10,
    # so the missing day never entered the window.
    assert prices["X:SMA2"].to_list() == [None, 5.5, 5.5, 8.0]


def test_declaring_the_same_indicator_twice_loads_one_column(tmp_path):
    write_csv(tmp_path, "A", [("2020-01-02", 10.0), ("2020-01-03", 11.0)])

    prices = load_prices(
        tmp_path, ["A"], dt.date(2020, 1, 2), indicators={"A": (sma(2), sma(2))}
    )

    assert prices.columns == ["date", "A", "A:SMA2", "is_rebalance_day"]


def test_csv_columns_beyond_close_are_not_loaded(tmp_path):
    write_csv(
        tmp_path,
        "A",
        [("2020-01-02", 10.0, 9.0, 1000), ("2020-01-03", 11.0, 9.5, 2000)],
        extra_columns=("SMA50", "Volume"),
    )

    prices = load_prices(tmp_path, ["A"], dt.date(2020, 1, 2))

    assert prices.columns == ["date", "A", "is_rebalance_day"]


def test_real_data():
    start = dt.date(2017, 1, 3)
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL", "SPY"], start)

    assert prices.columns == ["date", "TQQQ", "BTAL", "SPY", "is_rebalance_day"]
    assert prices["date"].first() == start
    assert prices["date"].is_sorted()
    assert sum(prices.null_count().row(0)) == 0

    # BTAL has no row on 2017-01-24; it carries 2017-01-23's close forward.
    missing_day = prices.filter(pl.col("date") == dt.date(2017, 1, 24))
    assert missing_day["BTAL"].item() == 19.57

    rebalance_days = prices.filter(pl.col("is_rebalance_day")).filter(
        pl.col("date") <= dt.date(2026, 7, 31)
    )["date"]
    assert len(rebalance_days) == 115
    assert rebalance_days.first() == dt.date(2017, 1, 31)


def test_real_data_with_extra_symbol():
    start = dt.date(2017, 1, 3)
    prices = load_prices(
        GOLDEN_DIR,
        ["TQQQ", "BTAL", "SPY"],
        start,
        extra=("QQQ",),
        indicators={"QQQ": (sma(200),)},
    )

    assert prices.columns == [
        "date",
        "TQQQ",
        "BTAL",
        "SPY",
        "QQQ",
        "QQQ:SMA200",
        "is_rebalance_day",
    ]
    assert len(prices) == 2417
    assert prices["date"].last() == dt.date(2026, 8, 14)

    # QQQ's history reaches back to 1999, so it is warmed up from the first row.
    assert prices.filter(pl.col("date") == start)["QQQ"].item() == 119.54
    assert prices["QQQ:SMA200"].null_count() == 0

    rebalance_days = prices.filter(pl.col("is_rebalance_day")).filter(
        pl.col("date") <= dt.date(2026, 7, 31)
    )["date"]
    assert len(rebalance_days) == 115


@pytest.mark.parametrize("name", list(BUNDLES))
def test_every_bundle_loads_from_the_live_export(name):
    """The live `data/` moves with each export; only that every bundle still loads."""
    bundle = BUNDLES[name]
    traded = sorted({s for st in bundle.strategies for s in st.weights})
    extra = sorted({s for st in bundle.strategies for s in st.data} - set(traded))

    prices = load_prices(
        DATA_DIR,
        traded,
        bundle.config.start,
        extra=extra,
        indicators=collect_indicators(bundle.strategies),
    )

    assert prices["date"].first() == bundle.config.start
