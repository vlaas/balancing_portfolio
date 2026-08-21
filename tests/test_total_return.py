"""Total-return dataset invariants — TOTAL_RETURN_SPEC §4, §7.

A dataset directory holds `<SYM>.csv` (dividend-adjusted export, the traded
series) and `price/<SYM>.csv` (unadjusted export from the same session,
reference only). T1–T3 are parametrised over two roots: the frozen TR snapshot
(numeric claims allowed) and live `data/` (structural claims only — they are
structural by construction), so a bad refresh fails the suite the day it lands.
"""

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

TR_DIR = Path(__file__).parent / "data" / "2026-08-20"
LIVE_DIR = Path(__file__).parents[1] / "data"
ROOTS = [TR_DIR, LIVE_DIR]
SYMBOLS = ["TQQQ", "BTAL", "QQQ", "SPY", "DBMF", "KMLM"]

# Flat-segment noise ceiling for ln R. Spec ceiling 1e-3; the 2026-08-20
# exports carry full-precision closes and the measured worst monotonicity
# violation is 4.3e-8 (TQQQ), so the constant is pinned one order above the
# measurement's magnitude at 1e-6 — still far below the smallest distribution
# jump the T2 up-jump count relies on (9.97e-5, TQQQ 2015).
TAU = 1e-6

# Cumulative implied yield bands for y = -ln(R_first) / years. Every symbol
# must show distributions (y ~ 0 means the export was made with the dividend
# toggle off — the most likely operator error); heavy distributors carry a
# stricter floor. BTAL measures 1.07%/yr where the spec assumed ~3%/yr (eight
# distributions ever, none 2013-2017, each verified against Polygon), so its
# floor is 0.008 instead of the spec's 0.015 — see the spec errata.
Y_MAX = 0.20
Y_MIN = {"BTAL": 0.008, "DBMF": 0.015, "KMLM": 0.015}
Y_MIN_DEFAULT = 0.001


def read_close(path: Path) -> pl.DataFrame:
    return pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    )


def ratio_series(root: Path, symbol: str) -> tuple[pl.DataFrame, pl.Series]:
    """The price frame and the adjustment ratio R = adjusted / price."""
    adjusted = read_close(root / f"{symbol}.csv")
    price = read_close(root / "price" / f"{symbol}.csv")
    assert adjusted["time"].equals(price["time"])
    return price, adjusted["close"] / price["close"]


root_param = pytest.mark.parametrize("root", ROOTS, ids=lambda p: p.name)


# T1 — Pairing: both exports exist, same session, snapshot self-describing.


@root_param
def test_paired_files_come_from_one_export_session(root: Path) -> None:
    for symbol in SYMBOLS:
        assert (root / f"{symbol}.csv").exists()
        assert (root / "price" / f"{symbol}.csv").exists()
        ratio_series(root, symbol)  # asserts identical time columns

    if root == TR_DIR:
        assert (root / "README.md").exists()
        last_bar = dt.date.fromisoformat(root.name)
        for symbol in ("TQQQ", "BTAL", "QQQ", "SPY"):
            assert read_close(root / f"{symbol}.csv")["time"][-1] == last_bar


# T2 — Ratio invariants: the shape TradingView's dividend adjustment must have.
# R is a non-decreasing step function in (0, 1], anchored at 1 on the last bar,
# jumping only at ex-dates; the cumulative implied yield sits in per-symbol
# bands. "Toggle was off" (R = 1, y = 0) and "files swapped" (R >= 1, monotone
# down) are unmissable here.


@root_param
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_adjustment_ratio_invariants(root: Path, symbol: str) -> None:
    price, ratio = ratio_series(root, symbol)
    r = ratio.log()
    steps = r.diff().slice(1)

    assert 0 < ratio.min()
    assert ratio.max() <= 1 + 1e-6
    assert abs(ratio[-1] - 1) <= 1e-6
    assert steps.min() >= -TAU
    assert (steps > 5 * TAU).sum() >= 4

    years = (price["time"][-1] - price["time"][0]).days / 365.25
    y = -r[0] / years
    assert Y_MIN.get(symbol, Y_MIN_DEFAULT) <= y <= Y_MAX


# T3 — Implied-distribution spot checks: the only external-data anchor, pinning
# the adjustment *semantics* (amount and ex-date), not just its shape.
#
# Published per-share amounts from Polygon's reference dividends API, fetched
# by fetch_dividends.py (records pulled and checked 2026-08-21); every entry is
# a single Polygon record. Amounts are stated in the current split basis: TQQQ
# split 2:1 on 2025-11-20 (Polygon splits API), so its earlier ex-dates would
# imply half the published amount and are deliberately not used. By the same
# arithmetic a *future* split rescales the implied amounts on refreshed data —
# restate these literals in the new basis in the refresh commit if that happens.
# Dividend-only refreshes leave R_{t-1}/R_t — and so this test — unchanged.

DISTRIBUTIONS = {
    "TQQQ": [(dt.date(2025, 12, 24), 0.085544), (dt.date(2026, 6, 24), 0.171229)],
    "BTAL": [(dt.date(2023, 12, 27), 1.0409), (dt.date(2024, 12, 30), 0.644903)],
    "QQQ": [(dt.date(2023, 12, 18), 0.80826), (dt.date(2024, 12, 23), 0.83466)],
    "SPY": [(dt.date(2024, 12, 20), 1.965548), (dt.date(2025, 12, 19), 1.993368)],
    "DBMF": [(dt.date(2021, 12, 30), 2.6772), (dt.date(2022, 12, 28), 2.2474)],
    "KMLM": [(dt.date(2021, 12, 29), 1.838123), (dt.date(2022, 12, 28), 4.0377)],
}


@root_param
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_implied_distributions_match_published_amounts(root: Path, symbol: str) -> None:
    price, ratio = ratio_series(root, symbol)
    index = {date: i for i, date in enumerate(price["time"])}

    for ex_date, amount in DISTRIBUTIONS[symbol]:
        i = index[ex_date]
        implied = price["close"][i - 1] * (1 - ratio[i - 1] / ratio[i])
        # Spec ceiling $0.02; measured max deviation $0.000011 -> $0.0001.
        assert implied == pytest.approx(amount, abs=1e-4)
