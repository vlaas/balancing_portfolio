# regime_report.py — REGIME_SPEC §6 function tests and (R4) real-data pins.

import datetime as dt
from pathlib import Path

import polars as pl

from regime_report import episodes, month_ends, report, signal_frame


def write_csv(data_dir: Path, symbol: str, rows: list[tuple]) -> None:
    lines = ["time,close"] + [f"{date},{close}" for date, close in rows]
    (data_dir / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def test_episodes_are_consecutive_risk_off_runs():
    assert episodes([]) == []
    assert episodes([None, 0.0, 1.0, 1.0, 0.0, 1.0]) == [2, 1]
    assert episodes([1.0, 1.0, 1.0]) == [3]
    assert episodes([0.0, None, 0.0]) == []


def test_month_ends_follow_the_rebalance_day_rule():
    frame = pl.DataFrame(
        {
            "date": [dt.date(2020, 1, 30), dt.date(2020, 1, 31),
                     dt.date(2020, 2, 3), dt.date(2020, 2, 28), dt.date(2020, 3, 2)],
            "close": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    # 01-31 and 02-28 end their months; the final row never does.
    assert month_ends(frame)["date"].to_list() == [
        dt.date(2020, 1, 31), dt.date(2020, 2, 28),
    ]


DATES = ["2020-01-30", "2020-01-31", "2020-02-03", "2020-02-28", "2020-03-02"]


def synthetic_root(tmp_path: Path) -> Path:
    # Ratio path (B = 1) crossing the 1.00/0.95 band; A has one extra date the
    # denominator lacks; Q closes below its 2-day SMA on both month-ends.
    a_rows = list(zip(DATES, [0.9, 1.05, 0.96, 0.9, 1.1]))
    a_rows.insert(3, ("2020-02-04", 7.0))  # host-only day, off every calendar
    write_csv(tmp_path, "A", a_rows)
    write_csv(tmp_path, "B", [(date, 1.0) for date in DATES])
    write_csv(tmp_path, "Q", list(zip(DATES, [10.0, 9.0, 10.0, 8.0, 10.0])))
    return tmp_path


def test_signal_frame_is_the_joint_calendar(tmp_path):
    frame = signal_frame(synthetic_root(tmp_path), "A", "B", 1, 1.00, 0.05)

    assert frame["date"].to_list() == [dt.date.fromisoformat(d) for d in DATES]
    assert frame["ratio"].to_list() == [0.9, 1.05, 0.96, 0.9, 1.1]
    assert frame["off"].to_list() == [0.0, 1.0, 1.0, 0.0, 1.0]


def test_report_counts_on_a_synthetic_root(tmp_path):
    text = report(
        synthetic_root(tmp_path), "A", "B", 1, 1.00, 0.05,
        start=dt.date(2020, 1, 30), end=None, sma_symbol="Q", sma_days=2,
    )

    assert "- window: 2020-01-30 -> 2020-03-02, 5 joint days" in text
    assert "- A-only rows in the window: 1, on Q's calendar: 0" in text
    assert "- risk-off: 3 of 5 (60.0%)" in text
    assert "- episodes: 2, mean length 1.5 days" in text
    assert "- month-ends in the window: 2, risk-off: 1" in text
    assert "| 2020 | 2 | 1 |" in text
    # 01-31: both off; 02-28: SMA only (Q 8 < SMA 9, regime released).
    assert "| full | 1 | 1 | 0 | 0 |" in text
    assert "| 2022 | 0 | 0 | 0 | 0 |" in text
