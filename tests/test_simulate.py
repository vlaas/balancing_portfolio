import datetime as dt
import math
from pathlib import Path

import polars as pl
import pytest

from polars.testing import assert_frame_equal

from simulate import Config, fee_schedule, simulate
from strategy import MarketDay, Strategy

GOLDEN_DIR = Path(__file__).parent / "data"  # frozen snapshot; numbers are pinned to it
START = dt.date(2020, 1, 2)


def frame(columns: dict[str, list[float]], rebalance: list[bool]) -> pl.DataFrame:
    """Build a synthetic price frame whose first date is START.

    `columns` holds the close of each symbol and any indicator columns, which
    the loader names "SYMBOL:INDICATOR".
    """
    dates = [START + dt.timedelta(days=i) for i in range(len(rebalance))]
    return pl.DataFrame(
        {"date": dates, **columns, "is_rebalance_day": rebalance},
        schema={
            "date": pl.Date,
            **{name: pl.Float64 for name in columns},
            "is_rebalance_day": pl.Boolean,
        },
    )


def half_and_half() -> Strategy:
    return Strategy(label="test", weights={"A": 0.5, "B": 0.5})


class Gated(Strategy):
    """50/50 A and B, refusing to buy the assets in `blocked` on days the
    "A:GATE" column reads 0."""

    label = "gated"
    weights = {"A": 0.5, "B": 0.5}
    blocked = ()

    def allow_buy(self, asset: str, ctx: MarketDay) -> bool:
        return asset not in self.blocked or ctx.indicator("A", "GATE") == 1.0


class Capped(Strategy):
    """50/50 A and B, capping buys of the assets in `capped` at `cap` dollars
    on days the "A:GATE" column reads 0."""

    label = "capped"
    weights = {"A": 0.5, "B": 0.5}
    capped = ()
    cap: float | None = 0.0

    def buy_cap(self, asset: str, ctx: MarketDay) -> float | None:
        if asset in self.capped and ctx.indicator("A", "GATE") == 0.0:
            return self.cap
        return None


def test_initial_buy():
    # 10000 buys floor(5000/30) = 166 of A (4980) and floor(5000/7) = 714 of B
    # (4998), leaving 22 in cash. The second day's prices reveal the holdings.
    prices = frame({"A": [30.0, 31.0], "B": [7.0, 8.0]}, [False, False])
    config = Config(START, 10000.0, 500.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert result["flow"].to_list() == [10000.0, 0.0]
    assert result["value"][0] == pytest.approx(166 * 30.0 + 714 * 7.0 + 22.0)
    assert result["value"][0] == pytest.approx(10000.0)
    assert result["value"][1] == pytest.approx(166 * 31.0 + 714 * 8.0 + 22.0)

    assert trades["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    assert trades["asset"].to_list() == [None, "A", "B"]
    assert trades["shares"].to_list() == [None, 166, 714]
    assert trades["amount"].to_list() == pytest.approx([10000.0, 4980.0, 4998.0])
    assert trades["cash_after"][-1] == pytest.approx(22.0)

    assert allocations["asset"].to_list() == ["A", "B", "CASH"]
    assert allocations["target"].to_list() == pytest.approx([0.5, 0.5, 0.0])
    assert allocations["actual"].to_list() == pytest.approx([0.498, 0.4998, 0.0022])


def test_rebalance_sells_the_overweight_asset():
    # Day 0: 50 of each at 10.0, no cash. Day 1: A has risen to 21.0, so with the
    # 100 contribution total = 1050 + 500 + 100 = 1650. Targets are
    # floor(825/21) = 39 of A (sell 11, +231 cash) and floor(825/10) = 82 of B
    # (buy 32, -320 cash), leaving 331 - 320 = 11 in cash.
    prices = frame({"A": [10.0, 21.0, 100.0], "B": [10.0, 10.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert result["flow"].to_list() == [1000.0, 100.0, 0.0]
    assert result["value"][0] == pytest.approx(1000.0)
    assert result["value"][1] == pytest.approx(1650.0)
    # Day 2's lopsided prices pin down the exact share counts and the cash.
    assert result["value"][2] == pytest.approx(39 * 100.0 + 82 * 1.0 + 11.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "SELL", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 11, 32]


def test_rebalance_contribution_covers_the_underweight_buy():
    # Same start, but a 500 contribution against a milder move in A: total =
    # 550 + 500 + 500 = 1550. Targets are floor(775/11) = 70 of A and
    # floor(775/10) = 77 of B — both above the 50 held, so nothing is sold.
    prices = frame({"A": [10.0, 11.0, 100.0], "B": [10.0, 10.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 500.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert result["value"][1] == pytest.approx(1550.0)
    assert result["value"][2] == pytest.approx(70 * 100.0 + 77 * 1.0 + 10.0)
    assert "SELL" not in trades["action"].to_list()


def test_single_asset_only_accumulates():
    closes = [30.0, 7.0, 12.5, 40.0, 16.0, 50.0, 10.0, 32.0, 8.0, 64.0, 25.0, 20.0]
    rebalance = [i in (1, 3, 5, 7, 9) for i in range(len(closes))]
    prices = frame({"A": closes}, rebalance)
    config = Config(START, 10000.0, 500.0)
    strategy = Strategy(label="test", weights={"A": 1.0})

    # With a single asset the rebalance degenerates to "spend the cash on as many
    # whole shares as it buys", which never sells and always leaves cash < close.
    shares, cash, expected = 0, 0.0, []
    for close, is_rebalance in zip(closes, rebalance):
        if not expected:
            cash += config.initial_capital
            shares = math.floor(cash / close)
            cash -= shares * close
        elif is_rebalance:
            cash += config.monthly_contribution
            bought = math.floor(cash / close)
            assert bought >= 0
            shares += bought
            cash -= bought * close
            assert cash < close
        expected.append(shares * close + cash)

    assert simulate(prices, strategy, config)[0]["value"].to_list() == pytest.approx(expected)
    assert shares == 451


def test_gate_redirects_the_blocked_budget():
    # Day 0 buys 50 of each at 10.0 with the gate open. Day 1 closes the gate on
    # A: total = 500 + 500 + 100 = 1100, and A's natural target of floor(550/10)
    # = 55 is capped at the 50 already held. That leaves 1100 - 500 = 600 for B,
    # the only asset still open, so B goes to floor(600/10) = 60 and cash to 0.
    prices = frame(
        {
            "A": [10.0, 10.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Gated(blocked=("A",)), config)

    assert result["value"][1] == pytest.approx(1100.0)
    assert result["value"][2] == pytest.approx(50 * 100.0 + 60 * 1.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "BUY"]
    assert day1["asset"].to_list() == [None, "B"]
    assert day1["shares"].to_list() == [None, 10]

    # Post-trade allocation shows the gate's footprint: A stuck at its held
    # 500/1100 against a 50% target, B over-target with the redirected budget.
    day1_alloc = allocations.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1_alloc["asset"].to_list() == ["A", "B", "CASH"]
    assert day1_alloc["target"].to_list() == pytest.approx([0.5, 0.5, 0.0])
    assert day1_alloc["actual"].to_list() == pytest.approx(
        [500 / 1100, 600 / 1100, 0.0]
    )


def test_gate_still_sells_the_blocked_asset():
    # A gated but overweight: A trebles to 30.0, so total = 1500 + 500 + 100 =
    # 2100 and A's target of floor(1050/30) = 35 is below the 50 held. The gate
    # blocks buys only, so A sells 15 (+450), and the 2100 - 1050 = 1050 left
    # over takes B to floor(1050/10) = 105, a buy of 55 that spends the cash
    # exactly.
    prices = frame(
        {
            "A": [10.0, 30.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Gated(blocked=("A",)), config)

    assert result["value"][1] == pytest.approx(2100.0)
    assert result["value"][2] == pytest.approx(35 * 100.0 + 105 * 1.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "SELL", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 15, 55]


def test_every_asset_gated_leaves_the_contribution_in_cash():
    # Both assets blocked and neither overweight, so the rebalance has nothing to
    # do: the 100 contribution simply sits in cash until a later rebalance.
    prices = frame(
        {
            "A": [10.0, 10.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Gated(blocked=("A", "B")), config)

    assert result["value"][1] == pytest.approx(1100.0)
    assert result["value"][2] == pytest.approx(50 * 100.0 + 50 * 1.0 + 100.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT"]


def test_balance_can_move_the_weights():
    class Tilt(Strategy):
        """All in A, then all in B from the second day on."""

        label = "tilt"
        weights = {"A": 1.0, "B": 0.0}

        def balance(self, ctx: MarketDay) -> dict[str, float]:
            if ctx.date > START:
                return {"A": 0.0, "B": 1.0}
            return self.weights

    # Day 0 puts the whole 1000 into 100 of A. Day 1 flips the weights: total =
    # 1000 + 100 = 1100, so A sells all 100 and B buys floor(1100/20) = 55.
    prices = frame({"A": [10.0, 10.0, 100.0], "B": [10.0, 20.0, 1.0]}, [False, True, False])
    config = Config(START, 1000.0, 100.0)

    result, trades, allocations = simulate(prices, Tilt(), config)

    assert result["value"][0] == pytest.approx(1000.0)
    assert result["value"][1] == pytest.approx(1100.0)
    assert result["value"][2] == pytest.approx(55 * 1.0)

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "SELL", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 100, 55]


def test_market_day_missing_value_is_none_but_missing_column_raises():
    day = MarketDay({"date": START, "A": 10.0, "A:SMA200": None})

    assert day.date == START
    assert day.close("A") == 10.0
    assert day.indicator("A", "SMA200") is None
    with pytest.raises(KeyError):
        day.close("B")  # symbol never loaded
    with pytest.raises(KeyError):
        day.indicator("A", "RSI")  # typo'd indicator name


def test_real_data_invariants():
    from prices import load_prices

    start = dt.date(2017, 1, 3)
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL", "SPY"], start)
    config = Config(start, 10000.0, 500.0)
    strategy = Strategy(label="test", weights={"TQQQ": 0.5, "BTAL": 0.5})

    result, trades, allocations = simulate(prices, strategy, config)

    assert len(result) == len(prices)
    assert result["date"].to_list() == prices["date"].to_list()
    assert result["flow"].sum() == pytest.approx(67500.0)
    assert result["value"].min() > 0.0
    deposits = trades.filter(pl.col("action") == "DEPOSIT")
    assert deposits["amount"].sum() == pytest.approx(67500.0)
    assert trades["cash_after"].min() >= 0.0

    from stats import imbalance

    off = imbalance(allocations)
    assert 0.0 <= off["misallocated"].min() and off["misallocated"].max() < 1.0
    # Without gates only integer rounding misbalances the plain 50/50.
    assert off["misallocated"].mean() < 0.01


def test_truncated_run_is_a_prefix_of_the_full_run():
    # SWEEP_SPEC.md T1: with end = E the curve equals the full run's first rows
    # on every row except the last, which differs only in that no
    # contribution/rebalance happens on it.
    from prices import load_prices

    start, end = dt.date(2017, 1, 3), dt.date(2020, 6, 30)
    strategy = Strategy(label="test", weights={"TQQQ": 0.5, "BTAL": 0.5})
    full_prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL"], start)
    trunc_prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL"], start, end=end)

    # E is a month-end trading day: the full run trades on it, the truncated
    # run holds it as a valuation day.
    assert full_prices.filter(pl.col("date") == end)["is_rebalance_day"].item()
    assert trunc_prices["date"].last() == end
    assert trunc_prices["is_rebalance_day"].last() is False

    full, _, _ = simulate(full_prices, strategy, Config(start, 10000.0, 500.0))
    trunc, _, _ = simulate(trunc_prices, strategy, Config(start, 10000.0, 500.0, end))

    n = len(trunc)
    assert_frame_equal(trunc.head(n - 1), full.head(n - 1))
    assert trunc["flow"][n - 1] == 0.0
    assert full["flow"][n - 1] == 500.0
    # Trades at E's closes conserve value, so the gap is exactly the deposit.
    assert full["value"][n - 1] - trunc["value"][n - 1] == pytest.approx(500.0)


# The buy_cap engine semantics — DECLARATIVE_SPEC.md T4.


def gate_prices() -> pl.DataFrame:
    """The test_gate_redirects_the_blocked_budget setup: gate open on day 0,
    closed from day 1 on."""
    return frame(
        {
            "A": [10.0, 10.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )


def test_buy_cap_zero_matches_allow_buy_false():
    config = Config(START, 1000.0, 100.0)

    capped = simulate(gate_prices(), Capped(capped=("A",), cap=0.0), config)
    gated = simulate(gate_prices(), Gated(blocked=("A",)), config)

    for got, want in zip(capped, gated):
        assert_frame_equal(got, want)


def test_buy_cap_none_matches_allow_buy_true():
    config = Config(START, 1000.0, 100.0)

    capped = simulate(gate_prices(), Capped(capped=("A",), cap=None), config)
    open_ = simulate(gate_prices(), half_and_half(), config)

    for got, want in zip(capped, open_):
        assert_frame_equal(got, want)


def test_buy_cap_limits_the_buy_in_dollars():
    # Day 1: total = 500 + 500 + 1000 = 2000, so A's natural target is
    # floor(1000/10) = 100. The 300.0 cap allows floor(300/10) = 30 more shares
    # on top of the 50 held, so A stops at 80 and the declined budget takes B,
    # the only open asset, to floor((2000 - 800)/10) = 120. Cash lands on 0.
    config = Config(START, 1000.0, 1000.0)

    result, trades, allocations = simulate(
        gate_prices(), Capped(capped=("A",), cap=300.0), config
    )

    day1 = trades.filter(pl.col("date") == START + dt.timedelta(days=1))
    assert day1["action"].to_list() == ["DEPOSIT", "BUY", "BUY"]
    assert day1["asset"].to_list() == [None, "A", "B"]
    assert day1["shares"].to_list() == [None, 30, 70]
    assert result["value"][2] == pytest.approx(80 * 100.0 + 120 * 1.0)


def test_buy_cap_leaves_sells_unchanged():
    # A trebles while capped: its target of floor(1050/30) = 35 is below the 50
    # held, so the sell happens exactly as with a plain gate — a cap limits
    # buys, never sells.
    prices = frame(
        {
            "A": [10.0, 30.0, 100.0],
            "B": [10.0, 10.0, 1.0],
            "A:GATE": [1.0, 0.0, 0.0],
        },
        [False, True, False],
    )
    config = Config(START, 1000.0, 100.0)

    capped = simulate(prices, Capped(capped=("A",), cap=300.0), config)
    gated = simulate(prices, Gated(blocked=("A",)), config)

    for got, want in zip(capped, gated):
        assert_frame_equal(got, want)


class Recording(Strategy):
    label = "recording"
    weights = {"A": 1.0}

    def __init__(self):
        self.seen = []

    def balance(self, ctx: MarketDay) -> dict[str, float]:
        self.seen.append(ctx.contribution)
        return self.weights


def test_market_day_contribution():
    assert MarketDay({"date": START}).contribution == 0.0

    config = Config(START, 1000.0, 100.0)

    strategy = Recording()
    simulate(frame({"A": [10.0, 10.0, 10.0]}, [False, True, False]), strategy, config)
    assert strategy.seen == [1000.0, 100.0]

    # A day 0 that is also a rebalance day sees both flows at once.
    strategy = Recording()
    simulate(frame({"A": [10.0, 10.0]}, [True, False]), strategy, config)
    assert strategy.seen == [1100.0]


# The cost model — COST_MODEL_SPEC.md T1-T4.


def test_zero_costs_are_bit_identical_to_the_defaults():
    # COST_MODEL_SPEC.md T1: explicit zeros take the same code path as the
    # defaults — every frame identical, the fee column all-zero. The untouched
    # golden numbers in test_main.py anchor the defaults to the pre-cost engine.
    from prices import load_prices

    start = dt.date(2017, 1, 3)
    prices = load_prices(GOLDEN_DIR, ["TQQQ", "BTAL"], start)
    strategy = Strategy(label="test", weights={"TQQQ": 0.5, "BTAL": 0.5})

    base = simulate(prices, strategy, Config(start, 10000.0, 500.0))
    explicit = simulate(
        prices, strategy, Config(start, 10000.0, 500.0, cost_bps=0.0, cash_yield=0.0)
    )

    for got, want in zip(explicit, base):
        assert_frame_equal(got, want)
    assert base[1]["fee"].to_list() == [0.0] * len(base[1])


def test_fee_schedule_resolves_flat_mapping_and_star():
    assert fee_schedule(50.0, ["A", "B"]) == {"A": 0.005, "B": 0.005}
    assert fee_schedule({"A": 10.0, "*": 50.0}, ["A", "B"]) == {"A": 0.001, "B": 0.005}
    with pytest.raises(ValueError, match="'B'"):
        fee_schedule({"A": 10.0}, ["A", "B"])


def test_flat_fees_reconcile_the_cash_ledger():
    # COST_MODEL_SPEC.md T2, flat 50 bps (0.005 per side). Day 0: A buys its
    # full 166 (fee 24.90, cash 4995.10), then B's cap floor(4995.10/7.035) =
    # 710 binds below the gross target of 714 (fee 24.85, cash 0.25). Day 1:
    # contribution 500, total = 166*31 + 710*8 + 500.25 = 11326.25, so B sells
    # 3 (fee 0.12) and A buys 16 (fee 2.48), leaving 25.65.
    prices = frame({"A": [30.0, 31.0], "B": [7.0, 8.0]}, [False, True])
    config = Config(START, 10000.0, 500.0, cost_bps=50.0)

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert trades["action"].to_list() == [
        "DEPOSIT", "BUY", "BUY", "DEPOSIT", "SELL", "BUY",
    ]
    assert trades["asset"].to_list() == [None, "A", "B", None, "B", "A"]
    assert trades["shares"].to_list() == [None, 166, 710, None, 3, 16]
    assert trades["amount"].to_list() == pytest.approx(
        [10000.0, 4980.0, 4970.0, 500.0, 24.0, 496.0]
    )
    # Every BUY/SELL fee is exactly amount x 0.005; DEPOSIT rows carry 0.0.
    for row in trades.iter_rows(named=True):
        expected = row["amount"] * 0.005 if row["action"] != "DEPOSIT" else 0.0
        assert row["fee"] == expected
    assert trades["cash_after"].to_list() == pytest.approx(
        [10000.0, 4995.10, 0.25, 500.25, 524.13, 25.65]
    )


def test_per_asset_fees_charge_each_symbol_its_own_rate():
    # COST_MODEL_SPEC.md T2, per-asset {"A": 10, "*": 50}: A at 0.001, B falls
    # back to the "*" rate 0.005. A buys 166 (fee 4.98, cash 5015.02); B's cap
    # floor(5015.02/7.035) = 712 binds (fee 24.92).
    prices = frame({"A": [30.0, 31.0], "B": [7.0, 8.0]}, [False, False])
    config = Config(START, 10000.0, 500.0, cost_bps={"A": 10.0, "*": 50.0})

    result, trades, allocations = simulate(prices, half_and_half(), config)

    assert trades["shares"].to_list() == [None, 166, 712]
    fees = {row["asset"]: row for row in trades.iter_rows(named=True)}
    assert fees["A"]["fee"] == fees["A"]["amount"] * 0.001
    assert fees["B"]["fee"] == fees["B"]["amount"] * 0.005


def test_unresolved_traded_symbol_raises_before_the_first_day():
    prices = frame({"A": [30.0], "B": [7.0]}, [False])
    config = Config(START, 10000.0, 500.0, cost_bps={"A": 10.0})

    with pytest.raises(ValueError, match="'B'"):
        simulate(prices, half_and_half(), config)


def test_affordability_cap_keeps_cash_non_negative():
    # COST_MODEL_SPEC.md T3, adversarial: all-in one asset at 500 bps (5%).
    # Day 0: gross target floor(1000/10) = 100 is capped at
    # floor(1000/10.5) = 95 (fee 47.50, cash 2.50). Day 1: cash 102.50, total
    # 1052.50, target 105; the cap allows floor(102.50/10.5) = 9 more
    # (fee 4.50, cash 8.00). The residual shows up in the CASH allocation row.
    prices = frame({"A": [10.0, 10.0]}, [False, True])
    config = Config(START, 1000.0, 100.0, cost_bps=500.0)
    strategy = Strategy(label="test", weights={"A": 1.0})

    result, trades, allocations = simulate(prices, strategy, config)

    assert trades["action"].to_list() == ["DEPOSIT", "BUY", "DEPOSIT", "BUY"]
    assert trades["shares"].to_list() == [None, 95, None, 9]
    assert trades["fee"].to_list() == pytest.approx([0.0, 47.5, 0.0, 4.5])
    assert trades["cash_after"].min() >= 0.0
    cash_rows = allocations.filter(pl.col("asset") == "CASH")
    assert cash_rows["actual"].to_list() == pytest.approx(
        [2.5 / 1000.0, 8.0 / 1052.5]
    )


def test_cash_yield_accrues_over_calendar_gaps():
    # COST_MODEL_SPEC.md T4: Thu 2020-01-02, Fri, weekend, Mon (rebalance),
    # Tue; a strategy holding 50% cash at cash_yield = 0.10. Day 0 accrues
    # nothing; Friday accrues 1 day; Monday accrues 3 (the weekend), then
    # deposits and trades; Tuesday accrues 1 day on the post-trade balance.
    dates = [
        dt.date(2020, 1, 2), dt.date(2020, 1, 3),
        dt.date(2020, 1, 6), dt.date(2020, 1, 7),
    ]
    prices = pl.DataFrame(
        {
            "date": dates,
            "A": [10.0, 10.0, 10.0, 10.0],
            "is_rebalance_day": [False, False, True, False],
        },
        schema={"date": pl.Date, "A": pl.Float64, "is_rebalance_day": pl.Boolean},
    )
    strategy = Strategy(label="test", weights={"A": 0.5})
    config = Config(START, 1000.0, 100.0, cash_yield=0.10)

    result, trades, allocations = simulate(prices, strategy, config)

    # Day 0: 50 shares at 10.0, cash exactly 500 — no interest on day 0.
    assert trades["cash_after"].to_list()[:2] == [1000.0, 500.0]
    c_fri = 500.0 * 1.1 ** (1 / 365)
    assert result["value"][1] == pytest.approx(500.0 + c_fri, abs=1e-9)
    # Monday: Friday's cash x 1.1^(3/365), then the 100 deposit, then trades.
    c_mon = c_fri * 1.1 ** (3 / 365) + 100.0
    total = 500.0 + c_mon  # ~1100.52, so the target grows to 55 and A buys 5
    assert trades["cash_after"][2] == pytest.approx(c_mon, abs=1e-9)
    assert trades["shares"].to_list() == [None, 50, None, 5]
    assert result["value"][2] == pytest.approx(total, abs=1e-9)
    assert result["value"][3] == pytest.approx(
        550.0 + (c_mon - 50.0) * 1.1 ** (1 / 365), abs=1e-9
    )

    # Interest is internal return, not flow: same flows as the yield-0 run,
    # strictly higher time-weighted return.
    from stats import twr

    base, base_trades, _ = simulate(prices, strategy, Config(START, 1000.0, 100.0))
    assert result["flow"].to_list() == base["flow"].to_list() == [1000.0, 0.0, 100.0, 0.0]
    assert twr(result)["index"][-1] > twr(base)["index"][-1]
