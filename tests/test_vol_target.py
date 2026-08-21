# The VolTarget strategy — DECLARATIVE_SPEC.md T6.

import datetime as dt
from pathlib import Path

import pytest
from test_simulate import START, frame

from indicators import ewma_vol
from main import collect_indicators
from prices import load_prices
from simulate import Config, simulate
from stats import exposure
from strategies.gate import Gate
from strategies.vol_target import VolTarget
from strategy import MarketDay

GOLDEN_DIR = Path(__file__).parent / "data"
DAY = dt.date(2020, 1, 2)


def vt(**kwargs) -> VolTarget:
    args = dict(
        risk="TQQQ", safe="BTAL", vol_symbol="QQQ", vol=ewma_vol(0.94),
        sigma_target=0.45, leverage=3.0, w_max=0.5, label="vt",
    )
    args.update(kwargs)
    return VolTarget(**args)


def market_day(sigma) -> MarketDay:
    return MarketDay({"date": DAY, "QQQ:VOL_EWMA94": sigma})


def test_weight_formula_and_clips():
    # 0.45 / (3 · 0.5) = 0.3
    assert vt().balance(market_day(0.5)) == {"TQQQ": 0.3, "BTAL": 0.7}
    # 0.45 / (3 · 0.15) = 1.0, clipped to w_max
    assert vt().balance(market_day(0.15)) == {"TQQQ": 0.5, "BTAL": 0.5}
    assert vt(w_min=0.2).balance(market_day(10.0)) == {"TQQQ": 0.2, "BTAL": 0.8}


def test_fallback_while_vol_is_none():
    assert vt().balance(market_day(None)) == {"TQQQ": 0.5, "BTAL": 0.5}
    assert vt(fallback=0.25).balance(market_day(None)) == {"TQQQ": 0.25, "BTAL": 0.75}


def test_safe_none_leaves_the_residual_in_cash():
    st = vt(safe=None)
    assert st.weights == {"TQQQ": 0.5}
    assert st.balance(market_day(0.5)) == {"TQQQ": 0.3}


def test_a_sleeve_splits_the_residual_by_its_fractions():
    st = vt(safe={"BTAL": 0.75, "KMLM": 0.25}, w_max=0.7)

    # The universe is _allocation(fallback): three assets, sleeve at 1 - 0.7.
    assert st.weights == pytest.approx({"TQQQ": 0.7, "BTAL": 0.225, "KMLM": 0.075})
    # 0.45 / (3 · 0.375) = 0.4, so the sleeve splits 0.6 as 0.45 / 0.15.
    assert st.balance(market_day(0.375)) == pytest.approx(
        {"TQQQ": 0.4, "BTAL": 0.45, "KMLM": 0.15}
    )
    assert st.balance(market_day(None)) == pytest.approx(st.weights)


def test_a_sleeve_keeps_its_keys_at_both_ends_of_the_clip():
    # The engine asserts set(balance) == set(weights) every rebalance day, so
    # the legs must be present at 0.0 rather than dropped.
    full = vt(safe={"BTAL": 0.5, "KMLM": 0.5}, w_max=1.0, sigma_target=1.0)
    assert full.balance(market_day(0.1)) == {"TQQQ": 1.0, "BTAL": 0.0, "KMLM": 0.0}

    # w = 0 is the worst case for the engine's sum(weights) <= 1 + 1e-9 assert.
    none = vt(safe={"BTAL": 0.5, "KMLM": 0.5}, w_min=0.0, sigma_target=0.0)
    weights = none.balance(market_day(0.5))
    assert weights == {"TQQQ": 0.0, "BTAL": 0.5, "KMLM": 0.5}
    assert sum(weights.values()) <= 1 + 1e-9


def test_a_sleeve_leaves_the_indicator_shape_alone():
    st = vt(safe={"BTAL": 0.5, "KMLM": 0.5}, gate=Gate("QQQ", ["TQQQ"], sma_days=200))
    assert st.data == ("QQQ",)
    assert [i.name for i in st.indicators["QQQ"]] == ["VOL_EWMA94", "SMA200"]


def test_a_gated_risk_asset_splits_its_budget_across_the_sleeve():
    # SAFE_BLEND_SPEC §2.2. QQQ closes below its SMA from the first rebalance,
    # so TQQQ is gated to zero shares and its whole budget goes to the sleeve
    # in sleeve proportion: open_weight = 0.45 + 0.15 = 0.6, so BTAL takes
    # floor(20000 · (0.45/0.6) / 10) = 1500 and KMLM floor(20000 · (0.15/0.6)
    # / 4) = 1250 — 15,000 : 5,000, the sleeve's own 3:1. The share counts
    # differ from that ratio only because the prices do.
    prices = frame(
        {
            "TQQQ": [10.0, 10.0],
            "BTAL": [10.0, 10.0],
            "KMLM": [4.0, 4.0],
            "QQQ": [100.0, 100.0],
            "QQQ:SMA200": [200.0, 200.0],
            "QQQ:VOL_EWMA94": [0.375, 0.375],
        },
        [False, False],
    )
    st = vt(
        safe={"BTAL": 0.75, "KMLM": 0.25}, w_max=0.7,
        gate=Gate("QQQ", ["TQQQ"], sma_days=200),
    )

    _, trades, _ = simulate(prices, st, Config(START, 20_000.0, 0.0))

    # Buys run in ascending delta order, so KMLM's 1250 precedes BTAL's 1500;
    # TQQQ never appears, its delta being zero.
    assert trades["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    assert trades["asset"].to_list() == [None, "KMLM", "BTAL"]
    assert trades["shares"].to_list() == [None, 1250, 1500]
    assert trades["cash_after"].to_list() == pytest.approx([20_000.0, 15_000.0, 0.0])


def test_validated_at_construction():
    with pytest.raises(AssertionError):
        vt(w_min=0.6)  # w_min > w_max
    with pytest.raises(AssertionError):
        vt(fallback=0.9)  # outside [w_min, w_max]


def test_gate_indicators_merge_on_the_shared_symbol():
    st = vt(gate=Gate("QQQ", ["TQQQ"], sma_days=200))
    assert st.data == ("QQQ",)
    assert [i.name for i in st.indicators["QQQ"]] == ["VOL_EWMA94", "SMA200"]


def test_full_run_on_the_snapshot():
    st = vt()
    assert set(st.weights) == {"TQQQ", "BTAL"}
    assert st.data == ("QQQ",)

    config = Config(dt.date(2017, 1, 3), 10_000.0, 500.0)
    prices = load_prices(
        GOLDEN_DIR, sorted(st.weights), config.start,
        extra=st.data, indicators=collect_indicators([st]),
    )
    curve, trades, allocations = simulate(prices, st, config)

    assert len(curve) == 2417
    assert curve["value"][-1] > 0

    # A vol-target actually varies its weight: min < avg < max (SWEEP_SPEC T2).
    exp = exposure(allocations)
    assert set(exp) == {"TQQQ", "BTAL", "CASH"}
    assert exp["TQQQ"]["min"] < exp["TQQQ"]["avg"] < exp["TQQQ"]["max"]
