"""Fetch the quarantined FRED macro series into `data/fred/` with `fredapi`.

DATA_LAYOUT_V2_SPEC §5: a checked-in fetch script producing committed CSVs
(the `fetch_dividends.py` precedent), never a runtime dependency. Each series is
written as `time,close` — ISO dates, ascending, unique — with FRED's missing
observations (bank holidays, the 2025-10 shutdown months) dropped, which
`make_synthetic.py` requires. Values and units are FRED's own, latest vintage
(RRSFS in millions). Only live `data/fred/` is written; the frozen roots'
`fred/` stay as committed.

Run: FRED_API_KEY=... uv run --with fredapi fetch_fred.py
"""

from pathlib import Path

import polars as pl
from fredapi import Fred

SERIES = ["UNRATE", "RRSFS", "INDPRO", "DTB3"]
OUT_DIR = Path("data/fred")


def main() -> None:
    fred = Fred()  # reads FRED_API_KEY from the environment
    for sid in SERIES:
        series = fred.get_series(sid).dropna()
        frame = pl.DataFrame(
            {"time": series.index.date.tolist(), "close": series.to_numpy()},
            schema={"time": pl.Date, "close": pl.Float64},
        )
        out = OUT_DIR / f"{sid}.csv"
        frame.write_csv(out)
        print(f"{sid}: {len(frame)} rows, {frame['time'][0]} -> {frame['time'][-1]}; saved {out}")


if __name__ == "__main__":
    main()
