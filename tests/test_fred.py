"""DATA_LAYOUT_V2_SPEC §5 — live `data/fred/` as `fetch_fred.py` writes it.

The values move with every fetch (FRED revises), so only the shape is pinned:
`time,close`, ascending unique ISO dates, no nulls, and no history lost
against the first observations the TradingView copies started on.
"""

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

FRED_DIR = Path(__file__).parents[1] / "data" / "fred"
FIRST = {
    "UNRATE": dt.date(1948, 1, 1),
    "RRSFS": dt.date(1992, 1, 1),
    "INDPRO": dt.date(1919, 1, 1),
    "DTB3": dt.date(1954, 1, 4),
}


@pytest.mark.parametrize("sid", sorted(FIRST))
def test_a_fetched_series_is_time_close_ascending_and_complete(sid: str) -> None:
    frame = pl.read_csv(FRED_DIR / f"{sid}.csv", try_parse_dates=True)
    assert frame.columns == ["time", "close"]
    assert frame.schema["time"] == pl.Date
    assert frame["time"].is_sorted() and frame["time"].n_unique() == len(frame)
    assert frame.null_count().row(0) == (0, 0)
    assert frame["time"][0] <= FIRST[sid]


def test_the_folder_holds_exactly_the_fetched_series() -> None:
    assert sorted(p.stem for p in FRED_DIR.glob("*.csv")) == sorted(FIRST)
