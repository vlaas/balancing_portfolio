# The VolTarget strategy — DECLARATIVE_SPEC.md T6.

import datetime as dt
from pathlib import Path

import pytest

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
