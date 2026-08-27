"""RETURN_STACKED_SPEC §6 — return-stacked statics: is one ticker a substitute
for the machine?

D1 the inceptions and the lane partition §4 rests on, D2 score₃ is the runner's
statistic on a categorical grid, D3 the anchors and the frozen dry-run counts,
D4 the pilot's §2.4–§2.5 numbers, D5 the deleveraging point's grammar. Every
real-data pin runs on the committed 2026-08-24 roots; no engine file is touched
by this spec, so a failure here is a data or grammar regression, never a
modelling choice.
"""

import datetime as dt
import json
import re
from pathlib import Path

import polars as pl
import pytest

from episode_report import episode_slice
from main import run_bundle
from prices import load_prices
from results_json import slug
from spec import build_bundle, load_spec, normalised_spec
from sweep import Window, build_summary, expand
from sweep import main as sweep_main

GOLDEN_DIR = Path(__file__).parent / "data"
GROSS = GOLDEN_DIR / "2026-08-24"
NET = GOLDEN_DIR / "2026-08-24-net15"
SPECS = Path(__file__).parents[1] / "specs"
RESULTS = Path(__file__).parents[1] / "results"

# §4's cost map: the blend map plus BIL at one tick. The nine statics have no
# measured spread and fall to the `*` catch-all (§2.3).
COSTS = {"TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6,
         "QQQ": 1, "SPY": 0.7, "BIL": 0.5, "*": 6}
FLAT20 = {"*": 20}
SMA200 = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}

LANE_2019 = "2019-05-08"
LANE_2021 = "2020-12-18"
TEST_2019 = "2024-01-02"  # the 2019 lane's snapped holdout start
WINDOW_2023 = "2023-12-05"

B75D25 = "VT TQQQ/BTAL75+DBMF25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
B75K25 = "VT TQQQ/BTAL75+KMLM25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
B50K50 = "VT TQQQ/BTAL50+KMLM50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
MACHINE = "VT TQQQ/BIL50+BTAL50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
GATED_5050 = "TQQQ50/BTAL50 gate QQQ<SMA200"
SPY = "SPY benchmark"


def read_close(path: Path) -> pl.DataFrame:
    return pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    )


def static(weights: dict) -> dict:
    return {"type": "fixed", "weights": weights}


def vol_target(safe: dict) -> dict:
    """The winners' coordinate: λ0.80, σ0.20, w_max 0.8, SMA-200 gate (§4.1)."""
    return {
        "type": "vol_target", "risk": "TQQQ", "safe": safe, "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.80}, "leverage": 3,
        "sigma_target": 0.20, "w_max": 0.8, "gate": SMA200,
    }


def bundle(start: str, entries: list[dict], costs: dict | None = None) -> dict:
    return {
        "schema_version": 1,
        "config": {
            "start": start, "initial_capital": 10000, "monthly_contribution": 500,
            "cost_bps": COSTS if costs is None else costs, "cash_yield": 0.03,
        },
        "strategies": entries + [
            {"type": "fixed", "label": SPY, "weights": {"SPY": 1.0}}
        ],
    }


def run(spec: dict, data_dir: Path) -> dict:
    return {r.label: r for r in run_bundle(build_bundle(spec), data_dir)}


# The rosters of §4.1, §4.2 and §4.4, benchmark appended by `bundle`. Run whole,
# so that each anchor is measured against the lane's own traded set — a static
# joining the set is what could move the calendar the windows snap against.
ROSTER_2019 = [
    static({"NTSX": 1.0}), static({"NTSX": 0.75, "BIL": 0.25}),
    static({"NTSX": 0.625, "BIL": 0.375}), static({"NTSX": 0.5, "BIL": 0.5}),
    vol_target({"BTAL": 0.75, "DBMF": 0.25}), vol_target({"BIL": 0.5, "BTAL": 0.5}),
    {"type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5}, "gate": SMA200},
]
ROSTER_2021 = [
    static({"NTSX": 1.0}), static({"RPAR": 1.0}),
    static({"NTSX": 0.5, "RPAR": 0.5}), static({"NTSX": 0.75, "BIL": 0.25}),
    static({"NTSX": 0.5, "BIL": 0.5}),
    vol_target({"BTAL": 0.75, "KMLM": 0.25}), vol_target({"BTAL": 0.75, "DBMF": 0.25}),
    vol_target({"BTAL": 0.5, "KMLM": 0.5}),
]
ROSTER_2023 = [
    static({"RSST": 1.0}), static({"RSSB": 1.0}), static({"RSBT": 1.0}),
    static({"GDE": 1.0}), static({"NTSX": 1.0}), static({"UPAR": 1.0}),
    static({"RPAR": 1.0}), static({"RSSB": 0.5, "RSST": 0.5}),
    static({"RSSB": 0.34, "RSST": 0.33, "RSBT": 0.33}),
    vol_target({"BTAL": 0.75, "KMLM": 0.25}), vol_target({"BTAL": 0.75, "DBMF": 0.25}),
    vol_target({"BTAL": 0.5, "KMLM": 0.5}),
]


@pytest.fixture(scope="module")
def lane_2019():
    return run(bundle(LANE_2019, ROSTER_2019), NET)


@pytest.fixture(scope="module")
def lane_2021():
    return run(bundle(LANE_2021, ROSTER_2021), NET)


@pytest.fixture(scope="module")
def panel_2023():
    return run(bundle(WINDOW_2023, ROSTER_2023), NET)


# --- D1 — inceptions and the lane partition (§2.1, §2.2) ---------------------

# §2.1's order: first bar, and the net15 README's jump count.
STATICS = (
    ("NTSX", "2018-08-02", 34),
    ("NTSI", "2021-05-20", 23),
    ("NTSE", "2021-05-20", 22),
    ("RPAR", "2019-12-13", 27),
    ("UPAR", "2022-01-04", 18),
    ("GDE", "2022-03-17", 8),
    ("RSBT", "2023-02-08", 2),
    ("RSST", "2023-09-06", 3),
    ("RSSB", "2023-12-05", 3),
)
D1_TRADED = ["NTSX", "BIL", "SPY", "TQQQ", "BTAL", "DBMF"]


@pytest.mark.parametrize("root", [GROSS, NET], ids=["gross", "net15"])
@pytest.mark.parametrize(
    "symbol,first", [(s, f) for s, f, _ in STATICS], ids=[s for s, *_ in STATICS]
)
def test_d1_the_statics_first_bars_are_the_same_on_both_roots(root, symbol, first):
    assert read_close(root / f"{symbol}.csv")["time"][0] == dt.date.fromisoformat(first)


def test_d1_the_net15_readme_counts_the_statics_jumps():
    readme = (NET / "README.md").read_text()
    counted = dict(re.findall(r"^\| (\w+) \| (\d+) \|", readme, re.M))
    assert [int(counted[s]) for s, *_ in STATICS] == [j for *_, j in STATICS]


def test_d1_the_decision_lanes_traded_set_is_complete_from_its_start():
    prices = load_prices(NET, D1_TRADED, dt.date.fromisoformat(LANE_2019))

    assert prices["date"][0] == dt.date.fromisoformat(LANE_2019)
    assert sum(prices.select(D1_TRADED).null_count().row(0)) == 0


def test_d1_a_lane_that_predates_a_traded_symbol_dies_in_the_loader():
    # RPAR's first bar is 2019-12-13: nothing carries forward onto 2019-05-08,
    # which is what partitions the statics across §2.2's four lanes.
    with pytest.raises(AssertionError):
        load_prices(NET, D1_TRADED + ["RPAR"], dt.date.fromisoformat(LANE_2019))


# --- D2 — score₃ is the runner's statistic on a categorical grid (§2.3) ------
#
# A `weights` grid is dict-valued, so `sweep.neighbours` treats it as
# categorical: no neighbours, no edge, and robust_score collapses to
# min(full, sensitivity median, holdout test). That three-term minimum is
# computable for a baseline block too, which is what lets §10.1 compare a grid
# point with the incumbent across the grid/baseline line.

D2_WINDOWS = [
    Window("full", "full", dt.date(2020, 1, 2), dt.date(2026, 1, 2)),
    Window("fit", "fit", dt.date(2020, 1, 2), dt.date(2023, 12, 29)),
    Window("test", "test", dt.date(2024, 1, 2), dt.date(2026, 1, 2)),
    Window("sens_a", "sens", dt.date(2020, 1, 2), dt.date(2023, 1, 3)),
    Window("sens_b", "sens", dt.date(2020, 7, 1), dt.date(2023, 7, 3)),
    Window("sens_c", "sens", dt.date(2021, 1, 4), dt.date(2024, 1, 2)),
]
D2_OBJECTIVES = {  # per window, one value per grid point
    "full": [4, 5], "fit": [4, 5], "test": [1, 6],
    "sens_a": [3, 7], "sens_b": [3, 2], "sens_c": [9, 8],
}
SCORE3_LANES = ("sweep_comp_2019", "sweep_comp_2021")


def score3(block: dict) -> float:
    return min(
        block["full"]["objective"],
        block["sensitivity"]["objective"]["median"],
        block["holdout"]["test"],
    )


def test_d2_a_weights_grid_has_no_neighbourhood_and_scores_by_score3():
    from test_sweep import stats_of, t5_spec

    spec = t5_spec(
        {"type": "fixed",
         "weights": {"grid": [{"NTSX": 1.0}, {"NTSX": 0.625, "BIL": 0.375}]}}
    )
    expanded = expand(spec["template"])
    labels = [e["label"] for e in expanded]
    records = {
        w.name: {l: stats_of(o) for l, o in zip(labels, D2_OBJECTIVES[w.name])}
        | {"bench": stats_of(100)}
        for w in D2_WINDOWS
    }

    summary = build_summary(
        spec, D2_WINDOWS, expanded, ["bench"], records,
        {l: True for l in labels}, notes=[], warnings=[],
    )

    points = summary["strategies"]
    assert [p["label"] for p in points] == ["NTSX100", "NTSX62.5/BIL37.5"]
    for point in points:
        assert point["neighbourhood"] == {
            "neighbour_min": None, "neighbour_mean": None, "edge": False,
        }
        assert point["robust_score"] == score3(point)
    # min(4, median(3,3,9), 1) and min(5, median(7,2,8), 6).
    assert [p["robust_score"] for p in points] == [1, 5]
    assert [p["params"]["weights"] for p in points] == [
        '{"NTSX":1.0}', '{"BIL":0.375,"NTSX":0.625}',
    ]


@pytest.mark.parametrize("name", SCORE3_LANES, ids=SCORE3_LANES)
def test_d2_score3_is_the_committed_robust_score_on_a_categorical_lane(name):
    summary = json.loads((RESULTS / name / "summary.json").read_text())

    for point in summary["strategies"]:
        assert point["neighbourhood"]["neighbour_min"] is None, point["label"]
        assert score3(point) == pytest.approx(point["robust_score"], abs=1e-8), (
            point["label"]
        )


def test_d2_score3_is_not_the_robust_score_once_the_grid_has_a_numeric_dimension():
    # sweep_cash_2019 grids σ, so every point has a neighbour and the identity
    # fails — the pin is about grid shape, not a tautology (CASH erratum 5).
    summary = json.loads((RESULTS / "sweep_cash_2019" / "summary.json").read_text())

    assert [
        p["label"] for p in summary["strategies"]
        if abs(score3(p) - p["robust_score"]) > 1e-8
    ]
    half = next(
        p for p in summary["strategies"] if p["label"].startswith(MACHINE[:26])
    )
    assert round(half["robust_score"], 4) == 0.8734
    assert round(score3(half), 4) == 0.9406


# --- D3 — the anchors §4 rests on, and the frozen lane sizes -----------------

RS_LANES = {  # §4.7, pinned in the pre-registration commit before any run
    "sweep_rs_2019": "4 grid + 4 baselines x 12 windows = 96 runs",
    "sweep_rs_2021": "5 grid + 4 baselines x 9 windows = 81 runs",
    "sweep_rs_2022": "8 grid + 4 baselines x 6 windows = 72 runs",
}
RS_PANELS = {  # §4.6, §4.4 — the statics, in the order the tables read them
    "rs_points_2019": ["NTSX100", "NTSX75/BIL25", "NTSX62.5/BIL37.5", "NTSX50/BIL50"],
    "rs_points_2021": ["NTSX100", "RPAR100", "NTSX50/RPAR50",
                       "NTSX75/BIL25", "NTSX50/BIL50"],
    "rs_points_2023": ["RSST100", "RSSB100", "RSBT100", "GDE100", "NTSX100",
                       "UPAR100", "RPAR100", "RSSB50/RSST50",
                       "RSSB34/RSST33/RSBT33"],
}


def test_d3_the_decision_lanes_baselines_reproduce_on_the_full_window(lane_2019):
    machine = lane_2019[B75D25].stats
    assert round(machine["calmar"], 8) == 0.93621129
    assert round(machine["cagr"], 8) == 0.18830107
    assert round(machine["max_drawdown"], 8) == -0.20113095
    assert round(lane_2019[MACHINE].stats["calmar"], 8) == 0.97652213
    assert round(lane_2019[SPY].stats["calmar"], 8) == 0.46572974


def test_d3_the_incumbent_reproduces_its_committed_holdout_test():
    # The lane's test window run as its own bundle: 0.91868785 is both
    # B75D25's committed holdout test and its committed robust_score.
    stats = run(bundle(TEST_2019, ROSTER_2019), NET)[B75D25].stats

    assert round(stats["calmar"], 8) == 0.91868785


def test_d3_the_winners_lanes_baselines_reproduce_on_the_full_window(lane_2021):
    calmars = [round(lane_2021[w].stats["calmar"], 4) for w in (B75K25, B75D25, B50K50)]

    assert calmars == [0.8529, 0.8574, 0.8849]


@pytest.mark.parametrize("name", RS_LANES, ids=lambda n: n[len("sweep_rs_"):])
def test_d3_the_rs_lanes_dry_run_to_their_frozen_counts(
    name, tmp_path, monkeypatch, capsys
):
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(SPECS / f"{name}.json"),
         "--data", str(NET), "--out", str(out), "--dry-run"],
    )

    sweep_main()

    assert RS_LANES[name] in capsys.readouterr().out
    assert not out.exists()


@pytest.mark.parametrize("name,roster", RS_PANELS.items(), ids=list(RS_PANELS))
def test_d3_the_panels_hold_the_roster_they_are_read_for(name, roster):
    # test_spec.py::every_strategy skips a spec whose symbols are absent from
    # the flat tests/data snapshot, and none of the nine statics is in it.
    strategies = build_bundle(load_spec(SPECS / f"{name}.json")).strategies

    assert [st.label for st in strategies][:len(roster)] == roster
    assert strategies[-1].label == SPY


# --- D4 — the pilot's own numbers (§2.4, §2.5) -------------------------------
#
# Every cell here slices a full-window curve the pilot already measured on this
# clone, so these are pins, not predictions (handoff §6.6).

# NTSX100 on the decision lane: episode return / in-window drawdown, in points.
D4_EPISODES = {
    "E3": (-0.2, -28.3),
    "E4": (23.5, -8.9),
    "E5": (-14.3, -31.4),
    "E6": (21.3, -16.9),
}
D4_WINDOWS = {  # peak → recovery, from episode_report.EPISODES
    "E3": ("2020-02-19", "2020-07-06"),
    "E4": ("2020-09-02", "2021-09-03"),
    "E5": ("2021-11-19", "2023-06-15"),
    "E6": ("2024-07-10", "2025-10-01"),
}


def test_d4_ntsx100_on_the_decision_lane_is_the_pilots(lane_2019):
    stats = lane_2019["NTSX100"].stats
    assert round(stats["calmar"], 8) == 0.41724492
    assert round(stats["cagr"], 8) == 0.13113533
    assert round(stats["max_drawdown"], 8) == -0.31428863

    deepest = lane_2019["NTSX100"].drawdowns[0]
    assert (deepest.peak, deepest.trough) == (dt.date(2021, 12, 27), dt.date(2022, 10, 14))


def test_d4_the_matched_floor_points_drawdown_is_the_pilots(lane_2019):
    assert round(lane_2019["NTSX62.5/BIL37.5"].stats["max_drawdown"], 8) == -0.20387913


@pytest.mark.parametrize("episode", D4_EPISODES, ids=list(D4_EPISODES))
def test_d4_ntsx100s_episode_cells_are_the_pilots(lane_2019, episode):
    peak, recovery = D4_WINDOWS[episode]
    ret, drawdown = episode_slice(lane_2019["NTSX100"].twr, peak, recovery)
    want_ret, want_drawdown = D4_EPISODES[episode]

    assert 100 * ret == pytest.approx(want_ret, abs=0.1)
    assert 100 * drawdown == pytest.approx(want_drawdown, abs=0.1)


def test_d4_the_2023_panels_floors_are_the_pilots(panel_2023):
    assert round(panel_2023["RSSB100"].stats["max_drawdown"], 8) == -0.16334022

    trend = panel_2023["RSST100"].drawdowns[0]
    assert (trend.peak, trend.trough) == (dt.date(2024, 7, 10), dt.date(2025, 4, 8))
    gold = panel_2023["GDE100"].drawdowns[0]
    assert (gold.peak, gold.trough) == (dt.date(2026, 1, 28), dt.date(2026, 3, 26))


def test_d4_flat_twenty_reaches_the_machine_and_not_the_static(lane_2019):
    stressed = run(bundle(LANE_2019, ROSTER_2019, costs=FLAT20), NET)

    static_drag = lane_2019["NTSX100"].stats["cagr"] - stressed["NTSX100"].stats["cagr"]
    machine_drag = lane_2019[B75D25].stats["cagr"] - stressed[B75D25].stats["cagr"]
    assert 100 * static_drag < 0.05
    assert 100 * machine_drag > 0.5


# --- D5 — the deleveraging surface's grammar ---------------------------------


def test_d5_the_matched_floor_point_labels_slugs_and_round_trips():
    once = bundle(LANE_2019, [static({"NTSX": 0.625, "BIL": 0.375})])
    built = build_bundle(once)

    assert built.strategies[0].label == "NTSX62.5/BIL37.5"
    assert slug(built.strategies[0].label) == "ntsx62-5-bil37-5"
    assert built.strategies[0].weights == {"NTSX": 0.625, "BIL": 0.375}

    normalised = normalised_spec(built)
    assert normalised_spec(build_bundle(normalised)) == normalised


def test_d5_the_deleveraging_grid_expands_and_renders_sorted_key_strings():
    expanded = expand({"type": "fixed", "weights": {"grid": [
        {"NTSX": 1.0}, {"NTSX": 0.75, "BIL": 0.25},
        {"NTSX": 0.625, "BIL": 0.375}, {"NTSX": 0.5, "BIL": 0.5},
    ]}})

    assert [e["label"] for e in expanded] == [
        "NTSX100", "NTSX75/BIL25", "NTSX62.5/BIL37.5", "NTSX50/BIL50",
    ]
    assert [e["params"]["weights"] for e in expanded] == [
        '{"NTSX":1.0}', '{"BIL":0.25,"NTSX":0.75}',
        '{"BIL":0.375,"NTSX":0.625}', '{"BIL":0.5,"NTSX":0.5}',
    ]
