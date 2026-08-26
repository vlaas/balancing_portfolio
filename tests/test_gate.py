# The Gate component — DECLARATIVE_SPEC.md T5, REGIME_SPEC R5.

import datetime as dt

import pytest

from indicators import mom_multi
from strategies.fixed import Fixed
from strategies.gate import AnyGate, Gate

from strategy import MarketDay

DAY = dt.date(2020, 1, 2)


def market_day(close, sma, contribution=0.0) -> MarketDay:
    return MarketDay(
        {"date": DAY, "QQQ": close, "QQQ:SMA200": sma}, contribution=contribution
    )


def gate(**kwargs) -> Gate:
    return Gate("QQQ", ["TQQQ"], sma_days=200, **kwargs)


def test_closed_iff_close_below_sma():
    assert gate().closed(market_day(99.0, 100.0))
    assert not gate().closed(market_day(100.0, 100.0))  # the equal case stays open
    assert not gate().closed(market_day(101.0, 100.0))


def test_open_while_either_value_is_none():
    assert not gate().closed(market_day(None, 100.0))
    assert not gate().closed(market_day(99.0, None))
    assert not gate().closed(market_day(None, None))


def test_exactly_one_sma_length():
    with pytest.raises(AssertionError):
        Gate("QQQ", ["TQQQ"])
    with pytest.raises(AssertionError):
        Gate("QQQ", ["TQQQ"], sma_days=200, sma_months=10)


def test_buy_cap():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    open_day = market_day(101.0, 100.0)
    closed_day = market_day(99.0, 100.0, contribution=500.0)

    assert gate().buy_cap("TQQQ", open_day, weights) is None
    assert gate().buy_cap("BTAL", closed_day, weights) is None  # not a gated asset
    assert gate().buy_cap("TQQQ", closed_day, weights) == 0.0

    exempt = gate(contribution_exempt=True)
    assert exempt.buy_cap("TQQQ", closed_day, weights) == 500.0 * 0.5
    assert exempt.buy_cap("TQQQ", open_day, weights) is None
    # A closed day without external cash allows nothing even when exempt.
    assert exempt.buy_cap("TQQQ", market_day(99.0, 100.0), weights) == 0.0


def test_monthly_variant_reads_the_monthly_column():
    monthly = Gate("QQQ", ["TQQQ"], sma_months=10)
    assert monthly.column == "SMA10M"
    day = MarketDay({"date": DAY, "QQQ": 99.0, "QQQ:SMA10M": 100.0})
    assert monthly.closed(day)


def test_fixed_declares_the_gate_symbol():
    st = Fixed(weights={"TQQQ": 0.5, "BTAL": 0.5}, gate=gate())
    assert st.data == ("QQQ",)
    assert [i.name for i in st.indicators["QQQ"]] == ["SMA200"]

    traded = Fixed(weights={"QQQ": 1.0}, gate=Gate("QQQ", ["QQQ"], sma_days=200))
    assert traded.data == ()
    assert [i.name for i in traded.indicators["QQQ"]] == ["SMA200"]


# REGIME_SPEC R5 — the regime kind, w_off / clip, and AnyGate composition.

REGIME_COLUMN = "VIX:REGIME_VIX3M_10_100_5"


def regime_day(state, contribution=0.0) -> MarketDay:
    return MarketDay(
        {"date": DAY, "VIX": 15.0, REGIME_COLUMN: state}, contribution=contribution
    )


def regime_gate(**kwargs) -> Gate:
    return Gate(
        "VIX", ["TQQQ"], denominator="VIX3M", ratio_sma=10, fire=1.00,
        hysteresis=0.05, **kwargs,
    )


def test_regime_gate_closed_iff_the_column_reads_one():
    assert regime_gate().closed(regime_day(1.0))
    assert not regime_gate().closed(regime_day(0.0))
    assert not regime_gate().closed(regime_day(None))  # warm-up stays open


def test_gate_symbols_and_indicators_for_both_kinds():
    sma_kind = gate()
    assert sma_kind.symbols == ("QQQ",)
    assert sma_kind.indicators["QQQ"][0].inputs == ()

    regime = regime_gate()
    assert regime.symbols == ("VIX", "VIX3M")
    declared = regime.indicators
    assert list(declared) == ["VIX"]
    assert declared["VIX"][0].name == "REGIME_VIX3M_10_100_5"
    assert declared["VIX"][0].inputs == ("VIX3M",)


def test_exactly_one_gate_kind_and_its_required_keys():
    with pytest.raises(AssertionError):  # fire alongside an sma kind
        Gate("QQQ", ["TQQQ"], sma_days=200, denominator="VIX3M", ratio_sma=10, fire=1.0)
    with pytest.raises(AssertionError):  # denominator without fire
        Gate("QQQ", ["TQQQ"], sma_days=200, denominator="VIX3M")
    with pytest.raises(AssertionError):  # fire without ratio_sma
        Gate("VIX", ["TQQQ"], denominator="VIX3M", fire=1.0)
    with pytest.raises(AssertionError):  # denominator equals the symbol
        Gate("VIX", ["TQQQ"], denominator="VIX", ratio_sma=10, fire=1.0)
    with pytest.raises(AssertionError):  # w_off outside [0, 1]
        gate(w_off=1.5)


def test_a_gate_with_no_assets_is_a_pure_condition():
    # SAFE_SWITCH_SPEC §1: assets=[] observes — closed() works, buy_cap is
    # None for every asset even while closed, clip is the identity.
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    condition = Gate("QQQ", [], sma_days=200)
    closed = market_day(99.0, 100.0, contribution=500.0)
    assert condition.closed(closed)
    assert not condition.closed(market_day(101.0, 100.0))
    assert condition.buy_cap("TQQQ", closed, weights) is None
    assert condition.buy_cap("BTAL", closed, weights) is None
    assert condition.clip(weights, closed) is weights
    assert Gate("QQQ", [], sma_days=200, w_off=0.0).clip(weights, closed) is weights
    assert condition.symbols == ("QQQ",)
    assert [i.name for i in condition.indicators["QQQ"]] == ["SMA200"]

    regime = Gate("VIX", [], denominator="VIX3M", ratio_sma=10, fire=1.00,
                  hysteresis=0.05)
    assert regime.closed(regime_day(1.0))
    assert not regime.closed(regime_day(None))
    assert regime.buy_cap("TQQQ", regime_day(1.0), weights) is None
    assert regime.symbols == ("VIX", "VIX3M")


def test_clip_is_the_identity_while_open():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    assert gate(w_off=0.0).clip(weights, market_day(101.0, 100.0)) is weights
    # Closed without w_off is today's gate exactly.
    assert gate().clip(weights, market_day(99.0, 100.0)) is weights


def test_clip_tilts_to_the_sleeve_while_closed():
    closed = market_day(99.0, 100.0)
    assert gate(w_off=0.0).clip({"TQQQ": 0.5, "BTAL": 0.5}, closed) == {
        "TQQQ": 0.0, "BTAL": 1.0,
    }
    assert gate(w_off=0.2).clip({"TQQQ": 0.5, "BTAL": 0.5}, closed) == {
        "TQQQ": 0.2, "BTAL": pytest.approx(0.8),
    }
    # A three-asset sleeve absorbs the excess in sleeve proportion.
    assert gate(w_off=0.0).clip({"TQQQ": 0.6, "BTAL": 0.3, "KMLM": 0.1}, closed) == {
        "TQQQ": 0.0, "BTAL": pytest.approx(0.75), "KMLM": pytest.approx(0.25),
    }


def test_clip_with_no_sleeve_leaves_the_excess_in_cash():
    clipped = gate(w_off=0.0).clip({"TQQQ": 0.5}, market_day(99.0, 100.0))
    assert clipped == {"TQQQ": 0.0}  # the sum drops; cash absorbs it


def test_clip_never_raises_a_gated_weight():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    assert gate(w_off=0.6).clip(weights, market_day(99.0, 100.0)) is weights


def test_buy_cap_is_unchanged_by_w_off():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    closed = market_day(99.0, 100.0, contribution=500.0)
    assert gate(w_off=0.0).buy_cap("TQQQ", closed, weights) == 0.0
    assert gate(w_off=0.0, contribution_exempt=True).buy_cap("TQQQ", closed, weights) == 250.0


def both_day(close, sma_value, state, contribution=0.0) -> MarketDay:
    return MarketDay(
        {"date": DAY, "QQQ": close, "QQQ:SMA200": sma_value,
         "VIX": 15.0, REGIME_COLUMN: state},
        contribution=contribution,
    )


def test_composite_is_closed_iff_any_member_is():
    both = AnyGate((gate(), regime_gate()))
    assert not both.closed(both_day(101.0, 100.0, 0.0))
    assert both.closed(both_day(99.0, 100.0, 0.0))  # sma member only
    assert both.closed(both_day(101.0, 100.0, 1.0))  # regime member only
    assert both.closed(both_day(99.0, 100.0, 1.0))


def test_composite_buy_cap_is_the_most_restrictive_member():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    plain_and_exempt = AnyGate((gate(), regime_gate(contribution_exempt=True)))
    # 0.0 beats an exempt cap beats None.
    assert plain_and_exempt.buy_cap("TQQQ", both_day(99.0, 100.0, 1.0, 500.0), weights) == 0.0
    assert plain_and_exempt.buy_cap("TQQQ", both_day(101.0, 100.0, 1.0, 500.0), weights) == 250.0
    assert plain_and_exempt.buy_cap("TQQQ", both_day(101.0, 100.0, 0.0, 500.0), weights) is None


def test_composite_symbols_union_and_indicator_merge():
    both = AnyGate((gate(), regime_gate()))
    assert both.symbols == ("QQQ", "VIX", "VIX3M")
    assert [i.name for i in both.indicators["QQQ"]] == ["SMA200"]
    assert [i.name for i in both.indicators["VIX"]] == ["REGIME_VIX3M_10_100_5"]
    # A duplicate indicator name collapses to one declaration.
    twins = AnyGate((gate(), gate(contribution_exempt=True)))
    assert [i.name for i in twins.indicators["QQQ"]] == ["SMA200"]


def test_composite_clip_applies_members_in_order():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    day = both_day(99.0, 100.0, 1.0)
    forward = AnyGate((gate(w_off=0.3), regime_gate(w_off=0.2))).clip(weights, day)
    backward = AnyGate((regime_gate(w_off=0.2), gate(w_off=0.3))).clip(weights, day)
    # Members gate the same assets, so order cannot change the result beyond
    # float rounding (REGIME_SPEC §4.3).
    assert forward == {"TQQQ": 0.2, "BTAL": pytest.approx(0.8)}
    assert backward == {key: pytest.approx(value) for key, value in forward.items()}


def test_composite_rejects_a_single_member():
    with pytest.raises(AssertionError):
        AnyGate((gate(),))


# --- COMPOSITION_SPEC C1: the score kind -------------------------------------

SCORE_COLUMN = "QQQ:MOMM1-3-6-12U"


def score_day(value, close=100.0, contribution=0.0) -> MarketDay:
    return MarketDay(
        {"date": DAY, "QQQ": close, "QQQ:SMA200": 100.0, SCORE_COLUMN: value},
        contribution=contribution,
    )


def score_gate(threshold=0.0, **kwargs) -> Gate:
    return Gate(
        "QQQ", ["TQQQ"], score=mom_multi((1, 3, 6, 12)), threshold=threshold, **kwargs
    )


def test_a_score_gate_closes_at_or_below_its_threshold():
    # `<=`, not `<`: the rotation family's "non-positive is bad" convention,
    # so threshold 0 closes exactly where HAA's absolute filter disqualifies.
    at_zero = score_gate()
    assert at_zero.closed(score_day(-0.01))
    assert at_zero.closed(score_day(0.0))
    assert not at_zero.closed(score_day(0.01))
    assert not at_zero.closed(score_day(None))  # open during warm-up

    negative = score_gate(threshold=-0.02)
    assert negative.closed(score_day(-0.02))
    assert not negative.closed(score_day(-0.019))


def test_score_gate_surface():
    st = score_gate()
    assert st.symbols == ("QQQ",)
    assert [i.name for i in st.indicators["QQQ"]] == ["MOMM1-3-6-12U"]
    assert st.column == "MOMM1-3-6-12U"
    assert st.fire is None  # every `if gate.fire is not None` branch untouched
    assert st.threshold == 0.0


def test_the_score_kind_extends_the_exactly_one_rule():
    with pytest.raises(AssertionError):  # score alongside an sma kind
        Gate("QQQ", ["TQQQ"], sma_days=200, score=mom_multi((1, 3, 6, 12)), threshold=0.0)
    with pytest.raises(AssertionError):  # threshold without score
        Gate("QQQ", ["TQQQ"], sma_days=200, threshold=0.0)
    with pytest.raises(AssertionError):  # threshold not a multiple of 0.001
        score_gate(threshold=0.0155)


def test_score_gate_clip_and_buy_cap_match_the_other_kinds():
    weights = {"TQQQ": 0.5, "BTAL": 0.5}
    closed = score_day(-0.01, contribution=500.0)
    assert score_gate(w_off=0.0).clip(weights, closed) == {"TQQQ": 0.0, "BTAL": 1.0}
    assert score_gate(w_off=0.0).clip(weights, score_day(0.01)) is weights
    assert score_gate().buy_cap("TQQQ", closed, weights) == 0.0
    assert score_gate(contribution_exempt=True).buy_cap("TQQQ", closed, weights) == 250.0


def test_an_sma_score_composite_is_the_or_form():
    both = AnyGate((gate(), score_gate()))
    # close 99 < SMA 100 closes the sma member; score +0.01 leaves the other open.
    assert both.closed(score_day(0.01, close=99.0))
    assert both.closed(score_day(-0.01, close=101.0))
    assert not both.closed(score_day(0.01, close=101.0))
    # Both members read QQQ, so the shared symbol carries both columns.
    assert both.symbols == ("QQQ",)
    assert [i.name for i in both.indicators["QQQ"]] == ["SMA200", "MOMM1-3-6-12U"]
