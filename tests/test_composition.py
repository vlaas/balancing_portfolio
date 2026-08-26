# score_report.py's real-data pins and the incumbent anchors through the score
# gate's code path — COMPOSITION_SPEC C5, C6, C7.

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from main import collect_indicators, run_bundle
from prices import load_prices
from score_report import LADDER, report, signals, state_changes
from simulate import simulate
from spec import _score, build_bundle, load_spec

DATA = Path(__file__).parent / "data"
NET15 = DATA / "2026-08-24-net15"  # the decision dataset (§7)
GROSS = DATA / "2026-08-24"  # its gross-TR twin
SPECS = Path(__file__).parents[1] / "specs"

U = {"kind": "avg", "months": [1, 3, 6, 12]}
START = dt.date(2012, 1, 3)


def month_end_signals(root: Path, score_entry: dict = None, threshold: float = 0.0):
    score, _ = _score(score_entry or U, "score")
    return signals(root, "QQQ", score, threshold, START, None, 200)


# --- C5: the signal's own calendar, against §2.4 -----------------------------


def test_c5_the_calendar_of_the_multi_horizon_score():
    ends = month_end_signals(NET15)

    assert len(ends) == 175  # the file's final partial month is never a month-end
    assert ends["date"].max() == dt.date(2026, 7, 31)
    assert int(ends["sma_off"].sum()) == 27
    assert int(ends["score_off"].sum()) == 22
    assert int((ends["sma_off"] & ends["score_off"]).sum()) == 18
    assert int((ends["sma_off"] & ~ends["score_off"]).sum()) == 9
    assert int((~ends["sma_off"] & ends["score_off"]).sum()) == 4

    # The four month-ends the OR adds to the SMA gate's calendar; the last two
    # are inside the holdout, at the trough of the incumbent's deepest drawdown.
    assert ends.filter(~pl.col("sma_off") & pl.col("score_off"))["date"].to_list() == [
        dt.date(2016, 6, 30), dt.date(2019, 5, 31),
        dt.date(2023, 1, 31), dt.date(2023, 2, 28),
    ]

    # 2022 is where the substitute under-covers: 12 of 12 against 10 of 12.
    y2022 = ends.filter(pl.col("date").dt.year() == 2022)
    assert (int(y2022["sma_off"].sum()), int(y2022["score_off"].sum())) == (12, 10)

    # Whipsaw is identical, which is why hysteresis is out of scope (§13).
    assert state_changes(ends["sma_off"].to_list()) == 20
    assert state_changes(ends["score_off"].to_list()) == 20


SPOTS = {  # date -> MOMM1-3-6-12U on QQQ, COMPOSITION_SPEC §2.2
    "2020-01-31": 0.1516,
    "2020-02-28": 0.0607,
    "2020-03-31": -0.0241,
    "2022-01-31": 0.0026,
    "2022-12-30": -0.1163,
    "2025-02-28": 0.0511,
    "2025-03-31": -0.0332,
}


def test_c5_spot_values():
    ends = month_end_signals(NET15)
    for date, value in SPOTS.items():
        row = ends.filter(pl.col("date") == dt.date.fromisoformat(date))
        assert row["score"].item() == pytest.approx(value, abs=5e-5), date

    # Neither signal sees a one-month crash: the score is positive on the
    # month-end before both legs down (§1).
    for date in ("2020-02-28", "2025-02-28"):
        row = ends.filter(pl.col("date") == dt.date.fromisoformat(date))
        assert not row["score_off"].item() and not row["sma_off"].item(), date


@pytest.mark.parametrize("threshold,closed", [(-0.02, 18), (0.0, 22), (0.02, 31)])
def test_c5_threshold_ladder(threshold, closed):
    ends = month_end_signals(NET15, threshold=threshold)
    assert int(ends["score_off"].sum()) == closed
    assert threshold in LADDER


def test_c5_the_scores_calendar_is_invariant_to_the_withholding_rescale():
    # A ratio of closes: the net-15 rescale cannot move it. The SMA's calendar
    # is not invariant — the gross root loses two 2012 closes.
    ends = month_end_signals(GROSS)

    assert len(ends) == 175
    assert int(ends["score_off"].sum()) == 22
    assert int(ends["sma_off"].sum()) == 25
    assert int((ends["sma_off"] & ends["score_off"]).sum()) == 18


def test_c5_the_report_renders_its_counts():
    text = report(NET15, "QQQ", U, 0.0, START, None, 200)

    assert "# Score report: QQQ:MOMM1-3-6-12U<=0" in text
    assert "- month-ends in the window: 175, last 2026-07-31" in text
    assert "- QQQ:MOMM1-3-6-12U<=0: 22, state changes 20" in text
    assert "- QQQ<SMA200: 27, state changes 20" in text
    assert "| full | 18 | 9 | 4 | 144 |" in text
    assert "| 2022 | 10 | 2 | 0 | 0 |" in text
    assert "| 2023-02-28 | score only | -0.0412 |" in text
    assert "| +0.03 | 35 | 26 |" in text


# --- C6: the incumbent anchors through the new code path ---------------------

COSTS = {"TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6, "QQQ": 1, "SPY": 0.7, "*": 6}


def vt_entry(gate: dict | None = None) -> dict:
    entry = {
        "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.80}, "leverage": 3,
        "sigma_target": 0.30, "w_max": 0.6,
    }
    if gate is not None:
        entry["gate"] = gate
    return entry


def bundle_of(*entries: dict):
    return build_bundle(
        {
            "schema_version": 1,
            "config": {
                "start": "2012-01-03", "initial_capital": 10000,
                "monthly_contribution": 500, "cost_bps": COSTS, "cash_yield": 0.03,
            },
            "strategies": [
                *entries,
                {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}},
            ],
        }
    )


G_SMA = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}

# (root, gated Calmar/CAGR/max DD, plain Calmar/CAGR/max DD) — §2.3's table.
ANCHORS = {
    "2026-08-20-net15": (
        (0.86254363, 0.2385326, -0.27654555),
        (0.71731262, 0.2479853, -0.34571440),
    ),
    "2026-08-24-net15": (
        (0.86123626, 0.2381710, -0.27654555),
        (0.71623794, 0.2476138, -0.34571440),
    ),
}


@pytest.mark.parametrize("root", ANCHORS)
def test_c6_the_2012_anchors_reproduce(root):
    # A mismatch is a bug in this change, not data drift (§9).
    gated_want, plain_want = ANCHORS[root]
    results = run_bundle(bundle_of(vt_entry(G_SMA), vt_entry()), DATA / root)

    for result, (calmar, cagr, drawdown) in zip(results, (gated_want, plain_want)):
        assert result.stats["calmar"] == pytest.approx(calmar, abs=1e-7)
        assert result.stats["cagr"] == pytest.approx(cagr, abs=1e-6)
        assert result.stats["max_drawdown"] == pytest.approx(drawdown, abs=1e-7)


def test_c6_declaring_the_score_alone_changes_nothing():
    # A mean of total returns never reaches -1, so this gate is never closed:
    # declaring the indicator must not move a single row.
    never_closes = {"symbol": "QQQ", "assets": ["TQQQ"], "score": dict(U),
                    "threshold": -1.0}
    bundle = bundle_of(vt_entry(never_closes), vt_entry())
    gated, plain = bundle.strategies[0], bundle.strategies[1]
    prices = load_prices(
        NET15, sorted(gated.weights), bundle.config.start,
        extra=sorted(set(gated.data) | set(plain.data)),
        indicators=collect_indicators([gated, plain]),
    )
    assert "QQQ:MOMM1-3-6-12U" in prices.columns

    for got, want in zip(
        simulate(prices, gated, bundle.config), simulate(prices, plain, bundle.config)
    ):
        assert_frame_equal(got, want)
# --- C7: the §7.6 bundles are covered by the spec auto-discovery test --------


@pytest.mark.parametrize(
    "name", ["comp_points", "comp_points_c20", "comp_points_tr"]
)
def test_c7_the_bracket_bundles_run_on_the_flat_snapshot(name):
    # test_spec.py::every_strategy skips a spec whose symbols are absent from
    # the flat root (REGIME_SPEC erratum 3); these three must not be skipped.
    bundle = build_bundle(load_spec(SPECS / f"{name}.json"))
    symbols = {s for st in bundle.strategies for s in (*st.weights, *st.data)}

    assert symbols == {"TQQQ", "BTAL", "QQQ", "SPY"}
    assert all((DATA / f"{s}.csv").exists() for s in symbols)
    assert len(bundle.strategies) == 15  # the fourteen §7.2 arms plus SPY
