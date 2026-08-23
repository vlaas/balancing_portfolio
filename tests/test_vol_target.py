# The VolTarget strategy — DECLARATIVE_SPEC.md T6.

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from test_simulate import START, frame

from indicators import ewma_vol
from main import collect_indicators
from prices import load_prices
from simulate import Config, simulate
from stats import exposure
from strategies.gate import Gate
from strategies.vol_target import SafeSwitch, VolTarget
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


# The SafeSwitch conditional sleeve — SAFE_SWITCH_SPEC §2.2, T3.

B25K75 = {"BTAL": 0.25, "KMLM": 0.75}
B75K25 = {"BTAL": 0.75, "KMLM": 0.25}


def switch(on=B25K75, off=B75K25, when=None) -> SafeSwitch:
    return SafeSwitch(on=on, off=off, when=when or Gate("QQQ", [], sma_days=200))


def switch_day(sigma, close=101.0, sma=100.0) -> MarketDay:
    return MarketDay(
        {"date": DAY, "QQQ:VOL_EWMA94": sigma, "QQQ": close, "QQQ:SMA200": sma}
    )


def test_a_switch_holds_on_while_open_and_off_while_closed():
    st = vt(safe=switch(), w_max=0.7)
    # 0.45 / (3 · 0.375) = 0.4; QQQ 101 > SMA 100 is open → the on sleeve.
    assert st.balance(switch_day(0.375)) == pytest.approx(
        {"TQQQ": 0.4, "BTAL": 0.15, "KMLM": 0.45}
    )
    assert st.balance(switch_day(0.375, close=99.0)) == pytest.approx(
        {"TQQQ": 0.4, "BTAL": 0.45, "KMLM": 0.15}
    )
    # At w = w_max the active sleeve still splits the whole residual.
    assert st.balance(switch_day(0.15)) == pytest.approx(
        {"TQQQ": 0.7, "BTAL": 0.075, "KMLM": 0.225}
    )


def test_a_switch_holds_on_while_the_condition_warms_up():
    st = vt(safe=switch(), w_max=0.7)
    assert st.balance(switch_day(0.375, sma=None)) == pytest.approx(
        {"TQQQ": 0.4, "BTAL": 0.15, "KMLM": 0.45}
    )


def test_the_inactive_sleeve_is_present_at_exactly_zero():
    st = vt(safe=switch(on="KMLM", off="BTAL"), w_max=0.7)
    # weights is the on allocation at fallback, padded with the off symbols.
    assert st.weights == pytest.approx({"TQQQ": 0.7, "KMLM": 0.3, "BTAL": 0.0})
    assert st.balance(switch_day(0.375)) == pytest.approx(
        {"TQQQ": 0.4, "KMLM": 0.6, "BTAL": 0.0}
    )
    assert st.balance(switch_day(0.375, close=99.0)) == pytest.approx(
        {"TQQQ": 0.4, "BTAL": 0.6, "KMLM": 0.0}
    )

    # A null off side leaves the residual in cash while closed (§2.1).
    cash_off = vt(safe=switch(on="KMLM", off=None), w_max=0.7)
    weights = cash_off.balance(switch_day(0.375, close=99.0))
    assert weights == pytest.approx({"TQQQ": 0.4, "KMLM": 0.0})
    assert sum(weights.values()) <= 1 + 1e-9


def test_a_switch_merges_the_condition_into_data_and_indicators():
    regime_when = Gate(
        "VIX", [], denominator="VIX3M", ratio_sma=10, fire=1.00, hysteresis=0.05
    )
    st = vt(safe=switch(when=regime_when), gate=Gate("QQQ", ["TQQQ"], sma_days=200))
    assert st.data == ("QQQ", "VIX", "VIX3M")
    assert [i.name for i in st.indicators["QQQ"]] == ["VOL_EWMA94", "SMA200"]
    assert [i.name for i in st.indicators["VIX"]] == ["REGIME_VIX3M_10_100_5"]

    # A switch sharing the gate's condition declares SMA200 once.
    shared = vt(safe=switch(), gate=Gate("QQQ", ["TQQQ"], sma_days=200))
    assert [i.name for i in shared.indicators["QQQ"]] == ["VOL_EWMA94", "SMA200"]


def test_a_gated_risk_asset_splits_its_budget_across_the_active_sleeve():
    # The SAFE_BLEND §2.2 fixture rerun with a switch: QQQ below its SMA
    # closes the risk gate and the switch at once, so the off sleeve (B75K25)
    # receives TQQQ's whole budget in its own 3:1 — trades identical to the
    # static-sleeve fixture above.
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
    st = vt(safe=switch(), w_max=0.7, gate=Gate("QQQ", ["TQQQ"], sma_days=200))

    _, trades, _ = simulate(prices, st, Config(START, 20_000.0, 0.0))

    assert trades["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    assert trades["asset"].to_list() == [None, "KMLM", "BTAL"]
    assert trades["shares"].to_list() == [None, 1250, 1500]
    assert trades["cash_after"].to_list() == pytest.approx([20_000.0, 15_000.0, 0.0])


# SAFE_SWITCH_SPEC T4 — real-data pins on the net snapshot, KMLM-inception
# start (the primary lane's window).

NET_DIR = Path(__file__).parent / "data" / "2026-08-20-net15"


def net_prices(st):
    return load_prices(
        NET_DIR, sorted(st.weights), dt.date(2020, 12, 18),
        extra=st.data, indicators=collect_indicators([st]),
    )


def net_day(prices, date) -> MarketDay:
    return MarketDay(prices.filter(pl.col("date") == date).row(0, named=True))


def test_a_switch_flips_on_the_real_sma_calendar():
    st = vt(safe=switch())
    prices = net_prices(st)
    # 2022-06-30 is one of R4's 12 closed 2022 SMA month-ends → off fractions.
    off_day = st.balance(net_day(prices, dt.date(2022, 6, 30)))
    assert off_day["BTAL"] == pytest.approx(3 * off_day["KMLM"])
    # 2021-11-30 is risk-on — the causal SMA200 is warm from ~2021-10, so an
    # earlier month-end would test warm-up, not openness → on fractions.
    on_day = st.balance(net_day(prices, dt.date(2021, 11, 30)))
    assert on_day["KMLM"] == pytest.approx(3 * on_day["BTAL"])


def test_the_r10lo_condition_flips_the_sleeve_on_2025_03_31():
    # The R4 spot pin: the 10-day SMA prints 0.952 >= fire 0.95 on 2025-03-31.
    st = vt(safe=switch(when=Gate(
        "VIX", [], denominator="VIX3M", ratio_sma=10, fire=0.95, hysteresis=0.05,
    )))
    prices = net_prices(st)
    feb = st.balance(net_day(prices, dt.date(2025, 2, 28)))
    assert feb["KMLM"] == pytest.approx(3 * feb["BTAL"])
    mar = st.balance(net_day(prices, dt.date(2025, 3, 31)))
    assert mar["BTAL"] == pytest.approx(3 * mar["KMLM"])


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
