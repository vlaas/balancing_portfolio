import datetime as dt
import math
import random
from pathlib import Path

import polars as pl
import pytest

from indicators import (
    Indicator,
    drawdown,
    ewma_vol,
    momentum,
    realized_vol,
    sma,
    sma_monthly,
)

GOLDEN_DIR = Path(__file__).parent / "data"
DATA_DIR = Path(__file__).parent.parent / "data"

# NET_TR_SPEC §7: net dataset roots carry no SMA reference columns; their
# price/ copies are byte-verified duplicates of already-tested files (N1).
CSV_FILES = [
    p
    for p in sorted(GOLDEN_DIR.rglob("*.csv")) + sorted(DATA_DIR.rglob("*.csv"))
    if not any("-net" in part for part in p.parts)
]


def read_closes(path: Path) -> pl.DataFrame:
    """A symbol's own bar calendar: `date` and `close`, as an Indicator sees it."""
    return pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    ).rename({"time": "date", "close": "close"})


def synthetic(rows: int = 600, seed: int = 1) -> pl.DataFrame:
    """A strictly-positive random walk on `rows` consecutive weekdays."""
    rng = random.Random(seed)
    closes = [100.0]
    while len(closes) < rows:
        closes.append(max(1.0, closes[-1] * (1 + rng.gauss(0, 0.01))))

    dates, day = [], dt.date(2000, 1, 3)
    while len(dates) < rows:
        if day.weekday() < 5:
            dates.append(day)
        day += dt.timedelta(days=1)

    return pl.DataFrame({"date": dates, "close": closes})


def month_end_mask(frame: pl.DataFrame) -> pl.Series:
    return (
        frame["date"].dt.month() != frame["date"].shift(-1).dt.month()
    ).fill_null(False)


def first_value_index(series: pl.Series) -> int | None:
    """Index of the first non-null value, or None if there is none."""
    return series.is_not_null().arg_max() if series.null_count() < len(series) else None


# T1 — TradingView parity: the proof that the Python SMA reproduces the export.


@pytest.mark.parametrize("path", CSV_FILES, ids=lambda p: str(p.relative_to(DATA_DIR.parent)))
@pytest.mark.parametrize("n", [15, 50, 100, 200])
def test_sma_matches_the_tradingview_column(path: Path, n: int) -> None:
    frame = pl.read_csv(path, schema_overrides={"close": pl.Float64}, try_parse_dates=True)
    reference = frame[f"SMA{n}"].cast(pl.Float64)
    computed = sma(n).fn(frame.select(pl.col("time").alias("date"), "close"))

    assert computed.null_count() == reference.null_count()
    assert (computed - reference).abs().max() <= 1e-9


# T2 — Causality: no value at row t may depend on a close after t.

STRICT_INDICATORS = [
    sma(200),
    realized_vol(20),
    ewma_vol(0.94),
    drawdown(),
    momentum(20),
]


def cut_points(frame: pl.DataFrame) -> list[int]:
    """Warm-up rows, a mid-history month-end, the row before one, and the last row."""
    month_ends = [i for i, flag in enumerate(month_end_mask(frame)) if flag]
    middle = month_ends[len(month_ends) // 2]
    return [199, 200, middle, middle - 1, len(frame) - 1]


@pytest.mark.parametrize("symbol", ["QQQ", "BTAL"])
@pytest.mark.parametrize("indicator", STRICT_INDICATORS, ids=lambda i: i.name)
def test_truncating_the_future_does_not_change_the_past(
    symbol: str, indicator: Indicator
) -> None:
    frame = read_closes(GOLDEN_DIR / f"{symbol}.csv")
    full = indicator.fn(frame)

    for t in cut_points(frame):
        assert indicator.fn(frame[: t + 1])[t] == full[t], f"{indicator.name} at row {t}"


@pytest.mark.parametrize("symbol", ["QQQ", "BTAL"])
def test_monthly_sma_is_causal_one_row_past_the_month_end_flag(symbol: str) -> None:
    """`sma_monthly` needs row t+1's *date* to know t is a month-end — never its close.

    So it is truncation-invariant from t+2 on, not from t+1, exactly like
    `is_rebalance_day`. The next test pins the part that matters: no price
    look-ahead.
    """
    frame = read_closes(GOLDEN_DIR / f"{symbol}.csv")
    indicator = sma_monthly(10)
    full = indicator.fn(frame)

    for t in cut_points(frame):
        truncated = indicator.fn(frame[: min(t + 2, len(frame))])
        assert truncated[t] == full[t], f"SMA10M at row {t}"


@pytest.mark.parametrize("symbol", ["QQQ", "BTAL"])
def test_monthly_sma_ignores_every_close_after_the_row(symbol: str) -> None:
    frame = read_closes(GOLDEN_DIR / f"{symbol}.csv")
    indicator = sma_monthly(10)
    full = indicator.fn(frame)

    for t in cut_points(frame)[:-1]:
        tampered = frame.with_columns(
            close=pl.when(pl.int_range(pl.len()) > t)
            .then(pl.col("close") * 1000)
            .otherwise(pl.col("close"))
        )
        assert indicator.fn(tampered)[t] == full[t], f"SMA10M at row {t}"


# T3 — Warm-up: the first row that carries a value, per the table in the spec.


def test_warm_up_lengths() -> None:
    frame = synthetic()
    month_ends = [i for i, flag in enumerate(month_end_mask(frame)) if flag]

    assert first_value_index(sma(200).fn(frame)) == 199
    assert first_value_index(sma_monthly(10).fn(frame)) == month_ends[9]
    assert first_value_index(realized_vol(20).fn(frame)) == 20
    assert first_value_index(ewma_vol(0.94).fn(frame)) == 20
    assert first_value_index(drawdown().fn(frame)) == 0
    assert first_value_index(momentum(20).fn(frame)) == 20


def test_drawdown_is_never_positive() -> None:
    values = drawdown().fn(synthetic())
    assert values.max() == 0.0
    assert values.min() < 0.0


# T4 — EWMA reference: the vectorised form must match the recursion in the spec.


def test_ewma_vol_matches_the_reference_recursion() -> None:
    frame = synthetic()
    returns = (frame["close"] / frame["close"].shift(1)).log().to_list()

    expected: list[float | None] = [None] * len(frame)
    variance = 0.0
    for t in range(1, len(frame)):
        variance = returns[t] ** 2 if t == 1 else 0.94 * variance + 0.06 * returns[t] ** 2
        expected[t] = math.sqrt(252 * variance)
    expected[:20] = [None] * 20

    computed = ewma_vol(0.94).fn(frame).to_list()
    for t, (got, want) in enumerate(zip(computed, expected)):
        assert (got is None) == (want is None), f"null mismatch at row {t}"
        if want is not None:
            assert abs(got - want) <= 1e-12, f"row {t}"


# T5 — Monthly SMA: month-end semantics on a calendar with known month-ends.


def monthly_frame() -> tuple[pl.DataFrame, list[int], list[float]]:
    """36 whole months plus a partial 37th, one close per weekday, close = row index."""
    dates, day = [], dt.date(2020, 1, 1)
    while day < dt.date(2023, 1, 15):
        if day.weekday() < 5:
            dates.append(day)
        day += dt.timedelta(days=1)

    frame = pl.DataFrame(
        {"date": dates, "close": [float(i + 1) for i in range(len(dates))]}
    )
    month_ends = [i for i, flag in enumerate(month_end_mask(frame)) if flag]
    return frame, month_ends, frame["close"].to_list()


def test_monthly_sma_on_a_month_end_includes_that_close() -> None:
    frame, month_ends, closes = monthly_frame()
    values = sma_monthly(10).fn(frame)

    for k in range(9, len(month_ends)):
        window = [closes[i] for i in month_ends[k - 9 : k + 1]]
        assert values[month_ends[k]] == pytest.approx(sum(window) / 10)


def test_monthly_sma_carries_the_previous_month_end_forward() -> None:
    frame, month_ends, _ = monthly_frame()
    values = sma_monthly(10).fn(frame)

    for start, end in zip(month_ends[9:], month_ends[10:]):
        for row in range(start + 1, end):
            assert values[row] == values[start]


def test_monthly_sma_is_null_before_the_mth_month_end() -> None:
    frame, month_ends, _ = monthly_frame()
    values = sma_monthly(10).fn(frame)

    assert values[: month_ends[9]].null_count() == month_ends[9]
    assert values[month_ends[9]] is not None


def test_the_partial_final_month_has_no_month_end() -> None:
    frame, month_ends, _ = monthly_frame()

    assert month_ends[-1] < len(frame) - 1
    assert not month_end_mask(frame)[-1]
    # The trailing rows of the partial month carry the last whole month's value.
    values = sma_monthly(10).fn(frame)
    assert values[-1] == values[month_ends[-1]]
