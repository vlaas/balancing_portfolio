"""EU_SUBSTITUTE_SPEC §8 T5 — `synb_report.py`: the frozen windows and grid,
the zero-beta solve exact on constructed returns, the quantization and its
tie rule, the monthly-rebalanced blend index, the worst-decile rule, the F4
year table and the verdict grammar. The pinned w_S* and the falsifier values
on the frozen decision root are added in the freeze commit (§3.6).
"""

import datetime as dt
import itertools

import polars as pl
import pytest

from synb_report import (
    BENCH, E4_WINDOW, ESTIMATION, GRID, LONG, PROXY, SHORT, SIGNAL, INDEX, WINDOW_START,
    arm_verdict, blend_index, f2, f4, month_end_rows, monthly_returns, quantize, returns,
    solve_w,
)


def test_the_windows_and_the_grid_are_frozen():
    assert GRID == (0.40, 0.45, 0.50)
    assert ESTIMATION == ("2020-05-01", "2023-12-31")
    assert WINDOW_START == "2020-05-01"
    assert E4_WINDOW == ("2020-09-01", "2021-03-31")
    assert (LONG, SHORT, BENCH, PROXY, SIGNAL, INDEX) == (
        "MVEA", "XSPS", "CSPX", "BTAL", "CNDX", "SPY"
    )


def daily_from_monthly(x, long, short, first=dt.date(2020, 4, 30)):
    """A daily frame whose month-end returns are exactly the given series: one
    month-end bar plus a mid-month filler bar per month (the filler carries the
    previous month-end's close, so it never moves a month-end return)."""
    dates, c, m, s = [], [1.0], [1.0], [1.0]
    year, month = first.year, first.month
    rows = [(first, 1.0, 1.0, 1.0)]
    for rc, rm, rs in zip(x, long, short):
        month += 1
        if month == 13:
            year, month = year + 1, 1
        rows.append((dt.date(year, month, 15), rows[-1][1], rows[-1][2], rows[-1][3]))
        rows.append((dt.date(year, month, 28), rows[-1][1] * (1 + rc),
                     rows[-1][2] * (1 + rm), rows[-1][3] * (1 + rs)))
    rows.append((dt.date(year, month, 28) + dt.timedelta(days=3), *rows[-1][1:]))  # never a month-end
    return pl.DataFrame({"date": [r[0] for r in rows], BENCH: [r[1] for r in rows],
                         LONG: [r[2] for r in rows], SHORT: [r[3] for r in rows]})


X = [0.02, -0.03, 0.01, 0.04, -0.02, 0.03, -0.01, 0.02, -0.04, 0.01, 0.03, -0.02]


def test_month_end_rows_are_filtered_before_differencing():
    daily = daily_from_monthly(X, X, X)
    ends = month_end_rows(daily, "2020-05-01", "2020-12-31")
    assert ends["date"].to_list()[0] == dt.date(2020, 5, 28)
    assert ends["date"].to_list()[-1] == dt.date(2020, 12, 28)
    r = returns(ends)
    assert len(r) == len(ends) - 1 == 7
    assert r["date"][0] == dt.date(2020, 6, 28)  # the May→June return, not April→May
    assert r[BENCH].to_list() == pytest.approx(X[1:8])


@pytest.mark.parametrize("k_long,k_short,expected", [(0.5, -0.5, 0.5), (0.6, -0.8, 0.6 / 1.4)])
def test_the_zero_beta_solve_is_exact_on_proportional_returns(k_long, k_short, expected):
    daily = daily_from_monthly(X, [k_long * r for r in X], [k_short * r for r in X])
    assert solve_w(monthly_returns(daily, "2020-05-01")) == pytest.approx(expected)


@pytest.mark.parametrize("w,expected", [
    (0.41, 0.40), (0.44, 0.45), (0.48, 0.50), (0.2854, 0.40), (0.9, 0.50),
    (0.425, 0.40), (0.475, 0.45),  # exact ties resolve to the lower point
])
def test_quantize_picks_the_nearest_grid_point(w, expected):
    assert quantize(w) == expected


def test_the_blend_index_compounds_at_month_ends_and_holds_between():
    # Two months, three bars each; both legs move within the month.
    dates = [dt.date(2020, 1, d) for d in (2, 15, 31)] + [dt.date(2020, 2, d) for d in (3, 14, 28)]
    long = [10.0, 11.0, 12.0, 12.0, 9.0, 15.0]
    short = [5.0, 4.0, 4.5, 4.5, 6.0, 3.0]
    w = 0.4
    index = blend_index(pl.DataFrame({"date": dates, LONG: long, SHORT: short}), w)["index"].to_list()
    # Within January the legs are held from the first bar.
    assert index[1] == pytest.approx(0.6 * 11 / 10 + 0.4 * 4 / 5)
    jan = 0.6 * 12 / 10 + 0.4 * 4.5 / 5
    assert index[2] == pytest.approx(jan)
    # February rebalances to (0.6, 0.4) at the January month-end (index 2).
    assert index[4] == pytest.approx(jan * (0.6 * 9 / 12 + 0.4 * 6 / 4.5))
    feb = 1 + 0.6 * (15 / 12 - 1) + 0.4 * (3 / 4.5 - 1)
    assert index[5] == pytest.approx(jan * feb)


def test_the_worst_decile_is_floor_n_over_ten_cndx_months():
    n = 20
    signal = [float(i) for i in range(n)]  # CNDX months in ascending order
    r = pl.DataFrame({"date": [dt.date(2021, 1, 28)] * n, SIGNAL: signal,
                      LONG: [0.01 * i for i in range(n)], SHORT: [0.0] * n})
    mean, k = f2(r, 0.5)
    assert k == 2
    assert mean == pytest.approx(0.5 * (0.0 + 0.01) / 2)


def test_f4_reports_the_monthly_held_short_leg_per_calendar_year():
    r = pl.DataFrame({
        "date": [dt.date(2021, 11, 30), dt.date(2021, 12, 31), dt.date(2022, 1, 31)],
        SHORT: [-0.10, 0.05, 0.20], INDEX: [0.10, -0.05, -0.15],
    })
    rows = f4(r)
    assert [(y["year"], y["months"]) for y in rows] == [(2021, 2), (2022, 1)]
    assert rows[0]["xsps_pct"] == pytest.approx((0.9 * 1.05 - 1) * 100)
    assert rows[0]["short_spy_pct"] == pytest.approx((0.9 * 1.05 - 1) * 100)
    assert rows[0]["shortfall_pp"] == pytest.approx(0.0)
    assert rows[1]["shortfall_pp"] == pytest.approx((0.20 - 0.15) * 100)


@pytest.mark.parametrize("f1_ok,f2_ok,f3_ok", list(itertools.product([True, False], repeat=3)))
def test_the_verdict_grammar(f1_ok, f2_ok, f3_ok):
    expected = "FAIL" if not (f2_ok and f3_ok) else ("PROXY" if f1_ok else "ARM-ONLY")
    assert arm_verdict(f1_ok, f2_ok, f3_ok) == expected


# The committed Phase-2 run on the frozen decision root (EU_SUBSTITUTE_SPEC
# §3.6, §5): the solve, the grid point, and every falsifier, pinned from the
# first run and compared to the artefacts.

from pathlib import Path  # noqa: E402

USD = Path(__file__).parent / "data" / "2026-09-02-net15-usd"
ARTEFACTS = Path(__file__).parents[1] / "results" / "synb"
ROOT = pytest.mark.skipif(not USD.exists(), reason="the decision root is committed with the freeze")


@pytest.fixture(scope="module")
def frozen():
    from synb_report import report
    return report(USD)


@ROOT
def test_the_estimation_window_is_44_month_ends_and_43_returns(frozen):
    e, w = frozen["estimation"], frozen["window"]
    assert (e["first_month_end"], e["last_month_end"]) == ("2020-05-29", "2023-12-29")
    assert (e["n_month_ends"], e["n_returns"]) == (44, 43)
    assert (w["first_month_end"], w["last_month_end"]) == ("2020-05-29", "2026-08-28")
    assert (w["n_month_ends"], w["n_returns"]) == (76, 75)


@ROOT
def test_w_star_and_the_grid_point_are_pinned(frozen):
    e = frozen["estimation"]
    assert e["beta_long"] == pytest.approx(0.7739439, abs=1e-6)
    assert e["beta_short"] == pytest.approx(-0.97813058, abs=1e-6)
    assert e["w_star"] == pytest.approx(0.44173002, abs=1e-6)
    assert e["chosen"] == 0.45 == quantize(e["w_star"])


@ROOT
@pytest.mark.parametrize("key,corr,mean_pp,synb_dd,ratio,verdict", [
    ("0.40", 0.33189196, 0.32897616, -0.03472936, 0.11159914, "ARM-ONLY"),
    ("0.45", 0.52453114, 0.87284472, -0.04227021, 0.13583087, "PROXY"),
    ("0.50", 0.65557494, 1.41671327, -0.05502082, 0.17680363, "PROXY"),
])
def test_the_falsifiers_are_pinned_per_grid_point(frozen, key, corr, mean_pp, synb_dd, ratio, verdict):
    a = frozen["arms"][key]
    assert a["primary"] == (key == "0.45")
    assert a["f1_corr"] == pytest.approx(corr, abs=1e-6)
    assert a["f2_mean_pp"] == pytest.approx(mean_pp, abs=1e-6) and a["f2_k"] == 7
    assert a["f3_synb_dd"] == pytest.approx(synb_dd, abs=1e-6)
    assert a["f3_btal_dd"] == pytest.approx(-0.31119733, abs=1e-6)
    assert a["f3_ratio"] == pytest.approx(ratio, abs=1e-6)
    assert a["verdict"] == verdict


@ROOT
def test_the_committed_artefacts_are_the_rounded_report(frozen):
    import json
    import results_json
    assert results_json._round(frozen) == json.loads((ARTEFACTS / "synb.json").read_text())
