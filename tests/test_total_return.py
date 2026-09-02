"""Total-return dataset invariants — TOTAL_RETURN_SPEC §4, §7; ROTATION_SPEC §3.5.

A dataset directory holds `<SYM>.csv` (dividend-adjusted export, the traded
series) and `price/<SYM>.csv` (unadjusted export from the same session,
reference only). T1–T3 are parametrised over three roots — both frozen TR
snapshots and live `data/` — with a per-root symbol list: the 2026-08-20
snapshot predates the paired BIL export and keeps the six original symbols,
while the 2026-08-24 snapshot and live `data/` run seven (CASH_SLEEVE_SPEC B1,
discharging SAFE_SWAP_SPEC §9 precondition (2) on the goldens). T4 runs the
pair invariants and the committed implied-yield bands over every live pair, so
a bad refresh fails the suite the day it lands.
"""

import dataclasses
import datetime as dt
import filecmp
from pathlib import Path

import polars as pl
import pytest

from bundles import BUNDLES
from indicators import ewma_vol, sma
from main import run_bundle
from make_net_tr import FLAT_MAX, JUMP_MIN
from prices import load_prices

GOLDEN_DIR = Path(__file__).parent / "data"
TR_DIR = Path(__file__).parent / "data" / "2026-08-20"
NEW_TR_DIR = GOLDEN_DIR / "2026-08-24"
EU_TR_DIR = GOLDEN_DIR / "2026-09-02"  # EU_SUBSTITUTE_SPEC §3.6
LIVE_DIR = Path(__file__).parents[1] / "data"
ROOTS = [TR_DIR, NEW_TR_DIR, EU_TR_DIR, LIVE_DIR]
# FX singles are stamped by their 17:00 New York open, so their last label is
# the day before the snapshot date (data/README.md, "FX bar stamps").
FX_SINGLES = {"EURUSD", "GBPUSD"}
SYMBOLS = ["TQQQ", "BTAL", "QQQ", "SPY", "DBMF", "KMLM"]

# The battery's symbol list is per-root, not global: BIL was exported in the
# 2026-08-24 session, so the older snapshot has no pair to check and T6's
# cross-snapshot calendar pin stays on SYMBOLS. Adding a symbol here is how it
# enters T1-T3 — the alternative, a glob over the root, would also sweep in the
# index series (VIX, SPX) that have no `price/` twin by design.
ROOT_SYMBOLS = {
    TR_DIR: SYMBOLS,
    NEW_TR_DIR: SYMBOLS + ["BIL"],
    EU_TR_DIR: SYMBOLS + ["BIL"],
    LIVE_DIR: SYMBOLS + ["BIL"],
}
ROOT_SYMBOL_PAIRS = [(root, symbol) for root, syms in ROOT_SYMBOLS.items() for symbol in syms]

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
root_symbol_param = pytest.mark.parametrize(
    "root,symbol", ROOT_SYMBOL_PAIRS, ids=lambda v: v if isinstance(v, str) else v.name
)


# T1 — Pairing: both exports exist, same session, snapshot self-describing.


@root_param
def test_paired_files_come_from_one_export_session(root: Path) -> None:
    for symbol in ROOT_SYMBOLS[root]:
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


@root_symbol_param
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
    # BIL distributes monthly; Polygon's reference data covers it from
    # 2007-07-02, its first distribution (CASH_SLEEVE_SPEC erratum 1 — the spec
    # expected a 2015 boundary). The later of the two is the most recent record,
    # $0.2730 on 2026-08-03, the amount the snapshot README's 1.39%/yr rests on.
    "BIL": [(dt.date(2024, 12, 19), 0.382797), (dt.date(2026, 8, 3), 0.272951)],
}


@root_symbol_param
def test_implied_distributions_match_published_amounts(root: Path, symbol: str) -> None:
    price, ratio = ratio_series(root, symbol)
    index = {date: i for i, date in enumerate(price["time"])}

    for ex_date, amount in DISTRIBUTIONS[symbol]:
        i = index[ex_date]
        implied = price["close"][i - 1] * (1 - ratio[i - 1] / ratio[i])
        # Spec ceiling $0.02; measured max deviation $0.000011 -> $0.0001.
        assert implied == pytest.approx(amount, abs=1e-4)


# T4 — Live-pair invariants (ROTATION_SPEC §3.5): every data/<SYM>.csv +
# data/price/<SYM>.csv pair. Unlike the goldens these run on live data by
# design — they guard *future refreshes*, and a failure means the export is
# wrong, never that a band needs loosening (the TOTAL_RETURN_SPEC rule: a
# ceiling that cannot be met is a finding).

LIVE_PAIRS = sorted(p.stem for p in (LIVE_DIR / "price").glob("*.csv"))

# Cumulative implied yields measured on the 2026-08-24 export (%/yr, full file
# history) — the ROTATION_SPEC §2 table plus the two symbols it omitted
# (IEF, NTSE; spec errata). Band [y/2, 1.5y]: wide enough for slow drift as
# history appends, tight enough that a toggle-off export (y ~ 0) or a
# double-adjusted one fails loudly. GLD is the zero-distribution exception
# (asserted R == 1 exactly, not banded); BIL is the positive control at the
# other end — nearly all of its return is distribution, its price near-flat.
LIVE_YIELDS = {
    "PDBC": 6.85, "HYG": 6.23, "DBMF": 5.80, "EDV": 4.85, "KMLM": 4.37,
    "VNQ": 4.29, "LQD": 4.13, "VGK": 3.57, "UPAR": 3.54, "TLT": 3.44,
    "GDE": 3.28, "AGG": 3.19, "TIP": 3.17, "BND": 3.16, "VEA": 3.01,
    "NTSE": 2.85, "IEF": 2.81, "VEU": 2.77, "SCZ": 2.71, "NTSI": 2.71,
    "EFA": 2.67, "VWO": 2.61, "ACWX": 2.59, "RPAR": 2.48, "TMF": 2.13,
    "SHY": 1.90, "EEM": 1.90, "RSSB": 1.86, "SPY": 1.79, "VTI": 1.75,
    "IWN": 1.67, "AVUV": 1.58, "RSBT": 1.52, "SPXL": 1.47, "BWX": 1.45,
    "BIL": 1.39, "EWJ": 1.31, "NTSX": 1.20, "IWM": 1.17, "DBC": 1.13,
    "BTAL": 1.07, "SSO": 1.02, "RSST": 0.70, "QLD": 0.68, "QQQ": 0.62,
    "UPRO": 0.38, "TQQQ": 0.31,
    # EU_SUBSTITUTE_SPEC §3.4: LQQ (Amundi Nasdaq-100 2x, Euronext) is the one
    # distributing EU line — a single early distribution, measured 0.066 %/yr
    # over 20.2 years; the derived band is [0.033, 0.099].
    "LQQ": 0.066,
}

# Zero-distribution pairs: the identical pair *is* the invariant (R == 1
# exactly, ROTATION_SPEC §3.2). GLD never distributed; the eight EU lines of
# the 2026-09-02 batch are accumulating UCITS share classes, so their export
# is the total-return series by construction (EU_SUBSTITUTE_SPEC §2.1, §3.4).
ZERO_YIELD = {"GLD", "CNDX", "CSPX", "DBMF_EU", "IB01", "MVEA", "QQL3", "QQQ3", "XSPS"}


def test_live_pair_universe_is_pinned() -> None:
    # A refresh that adds or drops a paired symbol updates this pin and the
    # yield table in the same commit — silent scope shrink is the failure
    # class this guards (ROTATION_SPEC §8 T9). 57 = the 48 pairs of the
    # 2026-08 batch + the nine EU lines of 2026-09-02 (EU_SUBSTITUTE_SPEC
    # §3.4 — NDX joined the single-series index class instead).
    assert len(LIVE_PAIRS) == 57
    assert set(LIVE_PAIRS) == set(LIVE_YIELDS) | ZERO_YIELD


@pytest.mark.parametrize("symbol", LIVE_PAIRS)
def test_live_pair_invariants(symbol: str) -> None:
    price, ratio = ratio_series(LIVE_DIR, symbol)  # asserts identical times
    r = ratio.log()
    steps = r.diff().slice(1)

    # R is a non-decreasing step function anchored at 1 on the last bar:
    # monotone within TAU in ln, flat between jumps (no step between export
    # noise and the smallest genuine distribution — make_net_tr's bounds).
    assert steps.min() >= -TAU
    assert ratio[-1] == 1.0
    assert ((steps > FLAT_MAX) & (steps < JUMP_MIN)).sum() == 0

    years = (price["time"][-1] - price["time"][0]).days / 365.25
    y = -r[0] / years
    if symbol in ZERO_YIELD:
        # The identical pair *is* the invariant for a zero-distribution fund:
        # this fires if it ever starts distributing and a refresh forgets
        # the adjusted pass (ROTATION_SPEC §3.2).
        assert (ratio == 1.0).all()
        assert abs(y) < 1e-4
    else:
        reference = LIVE_YIELDS[symbol] / 100
        assert 0.5 * reference <= y <= 1.5 * reference


# T5 — Signal-series deltas: switching the signal series from price to TR
# barely moves the QQQ signals on the matched window. A violation means the
# export is not the dividend adjustment §4 describes. Measured on the
# 2026-08-20 snapshot: 1 of 115 gate states differs (2019-05-31), max EWMA94
# vol delta 1.66% relative.

MATCHED_START = dt.date(2017, 1, 3)
MATCHED_END = dt.date(2026, 8, 14)


def rebalance_days(data_dir: Path) -> pl.DataFrame:
    frame = load_prices(
        data_dir,
        ("QQQ",),
        MATCHED_START,
        end=MATCHED_END,
        indicators={"QQQ": (sma(200), ewma_vol(0.94))},
    )
    return frame.filter(pl.col("is_rebalance_day"))


def test_sma_gate_state_changes_on_at_most_four_rebalance_days() -> None:
    tr, price = rebalance_days(TR_DIR), rebalance_days(GOLDEN_DIR)
    assert tr["date"].equals(price["date"])

    gate_tr = tr["QQQ"] < tr["QQQ:SMA200"]
    gate_price = price["QQQ"] < price["QQQ:SMA200"]
    assert (gate_tr != gate_price).sum() <= 4


def test_ewma_vol_moves_at_most_two_percent_relative() -> None:
    tr, price = rebalance_days(TR_DIR), rebalance_days(GOLDEN_DIR)

    relative = (tr["QQQ:VOL_EWMA94"] - price["QQQ:VOL_EWMA94"]) / price["QQQ:VOL_EWMA94"]
    assert relative.abs().max() <= 0.02


# T6 — Cross-snapshot calendar: the refresh neither lost nor invented
# sessions, which is what T5's join and the golden comparability rest on.
# If TradingView ever revises history, that is a finding: document the diff
# in the snapshot README and adjust this pin in the same commit.


@pytest.mark.parametrize("symbol", ["TQQQ", "BTAL", "QQQ", "SPY"])
def test_snapshot_calendars_agree_through_the_old_end(symbol: str) -> None:
    old = read_close(GOLDEN_DIR / f"{symbol}.csv")["time"]
    new = read_close(TR_DIR / f"{symbol}.csv")["time"]
    assert new.filter(new <= MATCHED_END).to_list() == old.to_list()


# The same pin extended to the 2026-08-24 snapshot (ROTATION_SPEC §8 T9),
# against the previous snapshot's dates for the six original symbols. BIL is
# deliberately not here: the older snapshot has no BIL file to compare against.


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_new_snapshot_calendar_agrees_with_the_previous_snapshot(symbol: str) -> None:
    old = read_close(TR_DIR / f"{symbol}.csv")["time"]
    new = read_close(NEW_TR_DIR / f"{symbol}.csv")["time"]
    assert new.filter(new <= dt.date(2026, 8, 20)).to_list() == old.to_list()


def test_new_snapshot_is_self_describing() -> None:
    # ROTATION_SPEC §3.6: README present; every traded-class file shares the
    # last bar the directory is named after.
    assert (NEW_TR_DIR / "README.md").exists()
    last_bar = dt.date.fromisoformat(NEW_TR_DIR.name)
    for path in sorted(NEW_TR_DIR.glob("*.csv")):
        assert read_close(path)["time"][-1] == last_bar, path.stem


# The EU_SUBSTITUTE_SPEC §3.6 snapshot: the 57 pairs of the live lane, five
# indices, two FX singles, `macro/` carried; the same pins as above, with the
# FX singles ending on the label before the snapshot date.


def test_eu_snapshot_is_self_describing() -> None:
    assert (EU_TR_DIR / "README.md").exists()
    last_bar = dt.date.fromisoformat(EU_TR_DIR.name)
    tops = sorted(EU_TR_DIR.glob("*.csv"))
    assert len(tops) == 64 and len(list((EU_TR_DIR / "price").glob("*.csv"))) == 57
    assert sorted(p.stem for p in (EU_TR_DIR / "price").glob("*.csv")) == LIVE_PAIRS
    for path in tops:
        expected = last_bar - dt.timedelta(days=1) if path.stem in FX_SINGLES else last_bar
        assert read_close(path)["time"][-1] == expected, path.stem


@pytest.mark.parametrize("symbol", SYMBOLS + ["BIL"])
def test_eu_snapshot_calendar_agrees_with_the_previous_snapshot(symbol: str) -> None:
    old = read_close(NEW_TR_DIR / f"{symbol}.csv")["time"]
    new = read_close(EU_TR_DIR / f"{symbol}.csv")["time"]
    assert new.filter(new <= dt.date(2026, 8, 24)).to_list() == old.to_list()


@pytest.mark.parametrize("symbol", sorted(ZERO_YIELD))
def test_eu_snapshot_zero_distribution_pairs_are_byte_identical(symbol: str) -> None:
    assert filecmp.cmp(EU_TR_DIR / f"{symbol}.csv", EU_TR_DIR / "price" / f"{symbol}.csv",
                       shallow=False)


# T7 — TR golden. The default bundle on the TR snapshot, ended at 2026-08-14 so
# the run shares the price golden's trading days, deposits and rebalance days
# (T6 pins the calendar). Produced by the implementation once and eyeballed:
# every number beats its price twin — the 50/50 by ~1.2%/yr CAGR (BTAL's
# 2017-onward yield on half the book plus TQQQ's own), the SMA gate by more
# (it holds more BTAL), the SPY benchmark by its dividend yield compounded,
# TQQQ 100% by ~0.5%/yr — and drawdowns are marginally shallower. Same rule as
# every golden: a later failure means the engine changed; fix the bug or update
# the dict in the same commit with the reason. Never refresh the snapshot.

GOLDEN_TR = {
    "TQQQ/BTAL 50/50": (258_250.59, 0.2486, -0.4477),
    "TQQQ 100%": (693_431.07, 0.4234, -0.8166),
    "TQQQ/BTAL SMA gate": (248_417.28, 0.2419, -0.3773),
    "SPY benchmark": (169_549.44, 0.1547, -0.3356),
}


def matched_window_bundle(**config_changes):
    bundle = BUNDLES["default"]
    config = dataclasses.replace(bundle.config, end=MATCHED_END, **config_changes)
    return dataclasses.replace(bundle, config=config)


def test_default_bundle_reproduces_the_tr_golden_numbers() -> None:
    results = run_bundle(matched_window_bundle(), TR_DIR)

    assert [r.label for r in results] == list(GOLDEN_TR)
    for result in results:
        final, cagr, max_dd = GOLDEN_TR[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["cagr"] == pytest.approx(cagr, abs=0.00005)
        assert result.stats["max_drawdown"] == pytest.approx(max_dd, abs=0.00005)

    # Cross-snapshot, same window: distributions can only add value.
    price_finals = {
        r.label: r.stats["final_value"] for r in run_bundle(BUNDLES["default"], GOLDEN_DIR)
    }
    for label in ("TQQQ/BTAL 50/50", "SPY benchmark"):
        assert GOLDEN_TR[label][0] > price_finals[label]


# T8 — TR cost golden. As T7 under the tastytrade base schedule and 3% cash
# yield — the same literals as the price cost golden and the exact
# configuration of the §8 rerun, so this regression anchor sits on the
# decision path, not beside it.

COST_GOLDEN_TR = {
    "TQQQ/BTAL 50/50": (257_536.83, 357.23),
    "TQQQ 100%": (693_312.41, 10.12),
    "TQQQ/BTAL SMA gate": (247_835.99, 279.52),
    "SPY benchmark": (169_596.21, 4.70),
}


def test_default_bundle_reproduces_the_tr_cost_golden_numbers() -> None:
    bundle = matched_window_bundle(
        cost_bps={"TQQQ": 1.5, "BTAL": 6, "QQQ": 1, "SPY": 0.7, "*": 6},
        cash_yield=0.03,
    )
    results = run_bundle(bundle, TR_DIR)

    assert [r.label for r in results] == list(COST_GOLDEN_TR)
    for result in results:
        final, fees = COST_GOLDEN_TR[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["total_fees"] == pytest.approx(fees, abs=0.005)
