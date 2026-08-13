import datetime as dt
from pathlib import Path

import polars as pl

from prices import load_prices

DATA_DIR = Path(__file__).parent.parent / "data"


def write_csv(data_dir: Path, symbol: str, rows: list[tuple[str, float]]) -> None:
    lines = ["time,open,high,low,close"]
    lines += [f"{date},0,0,0,{close}" for date, close in rows]
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


def test_real_data():
    start = dt.date(2017, 1, 3)
    prices = load_prices(DATA_DIR, ["TQQQ", "BTAL", "SPY"], start)

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
