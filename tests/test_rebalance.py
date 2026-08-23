"""Rebalance cadence (docs/REBALANCE_SPEC.md): the Cadence calendar, its
equivalence to the month-end default, contribution-only days, and the spec
grammar's `rebalance` key."""

import datetime as dt
import json
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from main import run_bundle
from prices import load_prices
from simulate import Config, simulate
from spec import build_bundle, rebalance_str
from strategy import Cadence, MarketDay, Strategy
from sweep import expand

GOLDEN_DIR = Path(__file__).parent / "data"


# --- Cadence masks -----------------------------------------------------------


def _dates(first: dt.date, n: int) -> pl.Series:
    return pl.Series([first + dt.timedelta(days=i) for i in range(n)], dtype=pl.Date)


def test_weeks_mask_marks_last_day_of_every_nth_week():
    # 2024-01-01 is a Monday; three full weeks plus a Monday.
    dates = _dates(dt.date(2024, 1, 1), 22)
    every_week = Cadence("weeks").mask(dates).to_list()
    assert [d for d, m in zip(dates, every_week) if m] == [
        dt.date(2024, 1, 7), dt.date(2024, 1, 14), dt.date(2024, 1, 21),
    ]
    # every 2nd week, both phases — together they cover every week once
    even = Cadence("weeks", 2, 0).mask(dates)
    odd = Cadence("weeks", 2, 1).mask(dates)
    assert (even & odd).sum() == 0
    assert (even | odd).to_list() == every_week
    assert even.sum() + odd.sum() == 3


def test_months_mask_with_offset_selects_one_month_of_every_n():
    dates = _dates(dt.date(2024, 1, 1), 366)  # all of 2024 (leap year)
    ends = {
        o: [d for d, m in zip(dates, Cadence("months", 3, o).mask(dates)) if m]
        for o in range(3)
    }
    assert [d.month for d in ends[0]] == [3, 6, 9]  # Dec is the last row
    assert [d.month for d in ends[1]] == [1, 4, 7, 10]
    assert [d.month for d in ends[2]] == [2, 5, 8, 11]
    assert all(d.day in (29, 30, 31) for o in ends for d in ends[o])


def test_last_row_is_never_a_rebalance_day():
    dates = _dates(dt.date(2024, 1, 1), 7)  # Mon..Sun: the week ends on the last row
    assert Cadence("weeks").mask(dates).last() is False


def test_cadence_is_anchored_to_the_calendar_not_the_start():
    a = _dates(dt.date(2024, 1, 1), 60)
    b = _dates(dt.date(2024, 1, 10), 51)  # same end, later start
    hits = lambda c, d: {x for x, m in zip(d, c.mask(d)) if m}
    for c in (Cadence("weeks", 2), Cadence("months", 2, 1)):
        assert hits(c, a) >= hits(c, b)
        assert hits(c, b) == {x for x in hits(c, a) if x >= dt.date(2024, 1, 10)}


def test_cadence_rejects_bad_arguments():
    with pytest.raises(AssertionError):
        Cadence("days")
    with pytest.raises(AssertionError):
        Cadence("weeks", 2, 2)


def test_monthly_cadence_equals_the_month_end_column():
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL"], dt.date(2020, 1, 2))
    assert (
        Cadence("months").mask(prices["date"]).to_list()
        == prices["is_rebalance_day"].to_list()
    )


# --- Engine ------------------------------------------------------------------


def _golden_config() -> Config:
    return Config(
        start=dt.date(2020, 1, 2), initial_capital=10_000, monthly_contribution=500,
        cost_bps=5.0, cash_yield=0.03,
    )


def test_monthly_cadence_is_bit_identical_to_the_default():
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL"], dt.date(2020, 1, 2))
    plain = Strategy(label="x", weights={"TQQQ": 0.5, "BTAL": 0.5})
    monthly = Strategy(
        label="x", weights={"TQQQ": 0.5, "BTAL": 0.5}, rebalance=Cadence("months")
    )
    for a, b in zip(simulate(prices, plain, _golden_config()),
                    simulate(prices, monthly, _golden_config())):
        assert_frame_equal(a, b)


def test_quarterly_trades_on_quarter_ends_and_invests_every_contribution():
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL"], dt.date(2020, 1, 2))
    st = Strategy(
        label="x", weights={"TQQQ": 0.5, "BTAL": 0.5}, rebalance=Cadence("months", 3)
    )
    curve, trades, allocations = simulate(prices, st, _golden_config())
    month_ends = prices.filter(pl.col("is_rebalance_day"))["date"].to_list()
    deposits = trades.filter(pl.col("action") == "DEPOSIT")["date"].to_list()
    assert deposits == [prices["date"][0]] + month_ends  # contributions stay monthly
    sells = trades.filter(pl.col("action") == "SELL")["date"].unique().to_list()
    assert all(d.month in (3, 6, 9, 12) for d in sells)  # only quarter-ends sell
    # every month-end is a trade day: the contribution is invested, not parked
    assert set(allocations["date"].to_list()) == {prices["date"][0], *month_ends}
    assert trades.filter(pl.col("action") == "BUY")["date"].n_unique() >= len(month_ends) - 1


def _frame(closes: dict[str, list[float]], contribution_days: list[bool]) -> pl.DataFrame:
    # Four consecutive days inside one ISO week, so a weekly cadence has no
    # period boundary in the frame: the only full rebalance is day 0.
    dates = [dt.date(2024, 1, 1) + dt.timedelta(days=i) for i in range(len(contribution_days))]
    return pl.DataFrame(
        {"date": dates, **closes, "is_rebalance_day": contribution_days},
        schema={"date": pl.Date, **{k: pl.Float64 for k in closes}, "is_rebalance_day": pl.Boolean},
    )


def test_contribution_only_day_buys_the_deposit_by_weight_and_never_sells():
    prices = _frame({"A": [10.0, 10.0, 40.0, 40.0], "B": [10.0, 10.0, 10.0, 10.0]},
                    [False, False, True, False])
    st = Strategy(label="x", weights={"A": 0.5, "B": 0.5}, rebalance=Cadence("weeks"))
    config = Config(start=dt.date(2024, 1, 1), initial_capital=1000, monthly_contribution=100)
    curve, trades, allocations = simulate(prices, st, config)
    day0 = trades.filter(pl.col("date") == dt.date(2024, 1, 1))
    assert day0.filter(pl.col("asset") == "A")["shares"].item() == 50
    assert day0.filter(pl.col("asset") == "B")["shares"].item() == 50
    # Day 2: A has quadrupled (80% of the book); a rebalance would sell A.
    day2 = trades.filter(pl.col("date") == dt.date(2024, 1, 3))
    assert day2["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    buys = {r["asset"]: r["shares"] for r in day2.filter(pl.col("action") == "BUY").iter_rows(named=True)}
    assert buys == {"A": 1, "B": 5}  # floor(50/40), floor(50/10): the deposit, by weight
    assert trades.filter(pl.col("action") == "SELL").is_empty()
    # The allocations row records the drift a rebalance would have removed.
    actual = {r["asset"]: r["actual"] for r in allocations.filter(pl.col("date") == dt.date(2024, 1, 3)).iter_rows(named=True)}
    assert actual["A"] == pytest.approx(51 * 40 / (51 * 40 + 55 * 10 + 10))


class _GatedA(Strategy):
    weights = {"A": 0.5, "B": 0.5}

    def allow_buy(self, asset, ctx: MarketDay) -> bool:
        return asset != "A" or ctx.indicator("A", "GATE") == 1.0


def test_contribution_only_day_reroutes_a_gated_deposit_to_the_open_asset():
    prices = _frame(
        {"A": [10.0, 10.0, 10.0, 10.0], "B": [10.0, 10.0, 10.0, 10.0],
         "A:GATE": [1.0, 1.0, 0.0, 0.0]},
        [False, False, True, False],
    )
    st = _GatedA(label="x", rebalance=Cadence("weeks"))
    config = Config(start=dt.date(2024, 1, 1), initial_capital=1000, monthly_contribution=100)
    _, trades, _ = simulate(prices, st, config)
    day2 = trades.filter((pl.col("date") == dt.date(2024, 1, 3)) & (pl.col("action") == "BUY"))
    assert day2["asset"].to_list() == ["B"]
    assert day2["shares"].item() == 10  # the whole deposit, none of A's holdings sold
    assert day2["cash_after"].item() == pytest.approx(0.0)


# --- Spec grammar and sweep params -------------------------------------------


def _spec(rebalance: dict | None, extra: dict = {}) -> dict:
    entry = {"type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5}} | extra
    if rebalance is not None:
        entry["rebalance"] = rebalance
    return {
        "schema_version": 1,
        "config": {"start": "2020-01-02", "initial_capital": 10000, "monthly_contribution": 500},
        "strategies": [entry, {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}}],
    }


@pytest.mark.parametrize("rebalance,text", [
    ({"weeks": 1}, "1w"), ({"weeks": 2, "offset": 1}, "2w+1"),
    ({"months": 3}, "3m"), ({"months": 3, "offset": 2}, "3m+2"),
])
def test_rebalance_key_builds_a_cadence_and_a_label_suffix(rebalance, text):
    st = build_bundle(_spec(rebalance)).strategies[0]
    assert rebalance_str(st.rebalance) == text
    assert st.label == f"TQQQ50/BTAL50 rb {text}"
    unit = "weeks" if "weeks" in rebalance else "months"
    assert st.spec["rebalance"] == {unit: rebalance[unit], "offset": rebalance.get("offset", 0)}


def test_absent_rebalance_leaves_label_and_spec_unchanged():
    st = build_bundle(_spec(None)).strategies[0]
    assert st.rebalance is None
    assert st.label == "TQQQ50/BTAL50"
    assert "rebalance" not in st.spec


def test_rebalance_on_vol_target_and_gate_ordering():
    spec = _spec(None)
    spec["strategies"][0] = {
        "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.8}, "sigma_target": 0.2, "w_max": 0.8,
        "gate": {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200},
        "rebalance": {"weeks": 2},
    }
    st = build_bundle(spec).strategies[0]
    assert st.label.endswith(" gate QQQ<SMA200 rb 2w")
    assert st.rebalance == Cadence("weeks", 2)


@pytest.mark.parametrize("rebalance,where", [
    ({"weeks": 1, "months": 1}, "strategies[0].rebalance"),
    ({}, "strategies[0].rebalance"),
    ({"months": 0}, "strategies[0].rebalance.months"),
    ({"months": 3, "offset": 3}, "strategies[0].rebalance.offset"),
    ({"weeks": 1.5}, "strategies[0].rebalance.weeks"),
    ({"weeks": 1, "phase": 0}, "strategies[0].rebalance.phase"),
])
def test_rebalance_validation_names_the_path(rebalance, where):
    with pytest.raises(ValueError, match=where.replace("[", r"\[").replace("]", r"\]")):
        build_bundle(_spec(rebalance))


def test_sweep_grid_over_rebalance_renders_params_and_null_means_default():
    template = {
        "type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5},
        "rebalance": {"grid": [{"weeks": 1}, None, {"months": 3, "offset": 1}]},
    }
    out = expand(template)
    assert [e["params"]["rebalance"] for e in out] == ["1w", None, "3m+1"]
    assert "rebalance" not in out[1]["entry"]
    assert len({e["label"] for e in out}) == 3

