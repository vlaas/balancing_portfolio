"""CASH_SLEEVE_SPEC §6 — the cash sleeve: BIL, BTAL and the fraction between.

B1 BIL enters the golden battery (its ratio and implied-amount legs live in
tests/test_total_return.py, where the battery is; the coverage boundary is
pinned here), B2 the withholding bias, B3 three-way sleeves round-trip, B4 the
anchors the lanes are read against, B5 the sleeve facts §2.1 states. Every
real-data pin runs on the committed 2026-08-24 roots; no engine file is touched
by this spec, so a failure here is a data or grammar regression, never a
modelling choice.
"""

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from main import run_bundle
from results_json import slug
from spec import build_bundle, load_spec, normalised_spec, safe_str
from sweep import expand
from sweep import main as sweep_main

GOLDEN_DIR = Path(__file__).parent / "data"
GROSS = GOLDEN_DIR / "2026-08-24"
NET = GOLDEN_DIR / "2026-08-24-net15"
SPECS = Path(__file__).parents[1] / "specs"
DIVIDENDS = Path(__file__).parents[1] / "dividends"

# §4's cost map: the incumbent lanes' blend map plus BIL at one tick (a T-bill
# ETF's spread is 1 cent on $92). Identical to the syn family's.
COSTS = {"TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6,
         "QQQ": 1, "SPY": 0.7, "BIL": 0.5, "*": 6}
SMA200 = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}

# The two lane starts every §2.1 cell and every bias is stated against.
LANE_2012 = "2012-01-03"
LANE_2021 = "2020-12-18"


def read_close(path: Path) -> pl.DataFrame:
    return pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    )


def cagr(root: Path, symbol: str, start: str) -> float:
    """Compound annual growth from the first bar on or after `start`, the
    convention §2.1's cells are measured in."""
    frame = read_close(root / f"{symbol}.csv").filter(
        pl.col("time") >= dt.date.fromisoformat(start)
    )
    years = (frame["time"][-1] - frame["time"][0]).days / 365.25
    return (frame["close"][-1] / frame["close"][0]) ** (1 / years) - 1


def max_drawdown(root: Path, symbol: str, start: str) -> float:
    frame = read_close(root / f"{symbol}.csv").filter(
        pl.col("time") >= dt.date.fromisoformat(start)
    )
    peak, worst = frame["close"][0], 0.0
    for close in frame["close"]:
        peak = max(peak, close)
        worst = min(worst, close / peak - 1)
    return worst


def vol_target(safe, sigma: float, w_max: float, gate: bool = True,
               lam: float = 0.80) -> dict:
    entry = {
        "type": "vol_target", "risk": "TQQQ", "safe": safe, "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": lam}, "leverage": 3,
        "sigma_target": sigma, "w_max": w_max,
    }
    return entry | ({"gate": SMA200} if gate else {})


def bundle(start: str, entries: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "config": {
            "start": start, "initial_capital": 10000,
            "monthly_contribution": 500, "cost_bps": COSTS, "cash_yield": 0.03,
        },
        "strategies": entries + [
            {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}}
        ],
    }


def run(spec: dict, data_dir: Path) -> dict[str, dict]:
    return {r.label: r.stats for r in run_bundle(build_bundle(spec), data_dir)}


# --- B1 — BIL enters the golden battery ------------------------------------
#
# The battery legs (pairing, ratio invariants, implied amounts) are in
# test_total_return.py, where ROOT_SYMBOLS now runs seven symbols on the
# 2026-08-24 root and on live data/. What belongs here is the reference data's
# coverage boundary: §6 expected Polygon to reach only BIL's 2015+ records, and
# it reaches its first distribution instead, so there is no gap to carry as
# extend_dividends.py carries QQQ's (CASH_SLEEVE_SPEC erratum 1).


def test_polygon_covers_bil_from_its_first_distribution():
    records = pl.read_parquet(DIVIDENDS / "BIL.parquet")
    dates = records["ex_dividend_date"].sort()
    assert len(records) == 126
    assert dates[0] == "2007-07-02"
    assert dates[-1] == "2026-08-03"
    # BIL's own inception is 2007-05-30 (4,840 bars on the 2026-08-24 root),
    # one month before the first distribution — nothing is missing in front.
    assert len(read_close(GROSS / "BIL.csv")) == 4840
    assert read_close(GROSS / "BIL.csv")["time"][0] == dt.date(2007, 5, 30)
    assert records["dividend_type"].unique().to_list() == ["CD"]


def test_the_pinned_distributions_are_polygon_records():
    from test_total_return import DISTRIBUTIONS

    published = dict(
        zip(
            pl.read_parquet(DIVIDENDS / "BIL.parquet")["ex_dividend_date"],
            pl.read_parquet(DIVIDENDS / "BIL.parquet")["cash_amount"],
        )
    )
    for ex_date, amount in DISTRIBUTIONS["BIL"]:
        assert published[ex_date.isoformat()] == amount


# --- B2 — the withholding bias is pinned -----------------------------------
#
# §10.5 reads a BIL-containing sleeve's net15 result one-sidedly, and these two
# numbers are the width of that read: a data refresh that moves them moves it.
# BIL's income is US Treasury interest, the clearest §871(k) case there is, so
# the flat-15% convention over-withholds it and the true rate is plausibly ~0.


@pytest.mark.parametrize(
    "start,expected", [(LANE_2012, 0.23), (LANE_2021, 0.47)], ids=["2012", "2021"]
)
def test_the_net15_convention_over_withholds_bil_by_a_known_margin(start, expected):
    bias = (cagr(GROSS, "BIL", start) - cagr(NET, "BIL", start)) * 100
    assert bias == pytest.approx(expected, abs=0.02)


# --- B3 — three-way sleeves round-trip -------------------------------------
#
# §4 depends on a three-symbol sleeve with non-integer percentages building,
# rendering and slugging; the grammar has done this since SAFE_BLEND_SPEC, and
# this pins it because the T-transforms are unreadable if the rendering moves.

T_KMLM = {"BIL": 0.375, "BTAL": 0.375, "KMLM": 0.25}
T_DBMF = {"BIL": 0.375, "BTAL": 0.375, "DBMF": 0.25}


def test_a_three_way_sleeve_renders_and_slugs():
    assert safe_str(T_KMLM) == "BIL37.5+BTAL37.5+KMLM25"
    assert slug(safe_str(T_KMLM)) == "bil37-5-btal37-5-kmlm25"
    # Sorted by symbol, so the input order cannot spell a second label.
    assert safe_str({"KMLM": 0.25, "BTAL": 0.375, "BIL": 0.375}) == safe_str(T_KMLM)


def test_a_three_way_sleeve_normalises_and_rebuilds_unchanged():
    spec = bundle(LANE_2021, [vol_target(T_KMLM, 0.20, 0.8)])
    once = normalised_spec(build_bundle(spec))
    assert once["strategies"][0]["safe"] == T_KMLM
    assert once["strategies"][0]["label"] == (
        "VT TQQQ/BIL37.5+BTAL37.5+KMLM25 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
    )
    assert normalised_spec(build_bundle(once)) == once


def test_a_sweep_safe_grid_over_three_way_sleeves_expands_to_two_points():
    template = vol_target({"grid": [T_KMLM, T_DBMF]}, 0.20, 0.8)
    points = expand(template)
    assert [p["params"]["safe"] for p in points] == [
        "BIL37.5+BTAL37.5+KMLM25", "BIL37.5+BTAL37.5+DBMF25"
    ]


# --- B4 — the anchors, before a single new number is read ------------------
#
# §9 step 0 forbids reading the lanes until these reproduce. The σ0.30 / w0.6
# arm is sweep_comp_2012's committed gated row; the σ0.20 / w0.8 pair is the
# synthetic bridge's, and is the number that fired this spec — BIL buys 3.45 pp
# of CAGR for 1.08 pp of drawdown at the winners' coordinate.


CASH_LANES = {  # §4.6, pinned in the pre-registration commit before any run
    "sweep_cash_2012": "30 grid + 3 baselines x 23 windows = 759 runs",
    "sweep_cash_2012_c20": "30 grid + 3 baselines x 23 windows = 759 runs",
    "sweep_cash_2021": "24 grid + 2 baselines x 9 windows = 234 runs",
    "sweep_cash_2021_c20": "24 grid + 2 baselines x 9 windows = 234 runs",
    "sweep_cash_2019": "12 grid + 2 baselines x 12 windows = 168 runs",
}


@pytest.mark.parametrize("name", CASH_LANES, ids=lambda n: n[len("sweep_cash_"):])
def test_the_cash_lanes_dry_run_to_their_frozen_counts(name, tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(SPECS / f"{name}.json"),
         "--data", str(NET), "--out", str(out), "--dry-run"],
    )
    sweep_main()
    assert CASH_LANES[name] in capsys.readouterr().out
    assert not out.exists()


# §4.5: five sleeves at two coordinates plus SPY, and the twelve 2021 sleeves
# at the winners' coordinate plus SPY. The BIL counts are the point — the panel
# exists to supply the calendar years and per-episode drawdowns runs.csv cannot.
@pytest.mark.parametrize(
    "name,count,with_bil", [("cash_points_2012", 11, 8), ("cash_points_2021", 13, 8)]
)
def test_the_panels_hold_the_sleeves_they_are_read_for(name, count, with_bil):
    strategies = build_bundle(load_spec(SPECS / f"{name}.json")).strategies
    assert len(strategies) == count
    assert strategies[-1].label == "SPY benchmark"
    assert sum("BIL" in st.label for st in strategies) == with_bil
    assert all("gate QQQ<SMA200" in st.label for st in strategies[:-1])


def test_the_2012_regime_anchor_reproduces_through_the_cash_cost_map():
    stats = run(bundle(LANE_2012, [vol_target("BTAL", 0.30, 0.6)]), NET)
    arm = stats["VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate QQQ<SMA200"]
    assert round(arm["calmar"], 8) == 0.86123626
    assert round(arm["cagr"], 8) == 0.23817105
    assert round(arm["max_drawdown"], 8) == -0.27654555


def test_the_bridge_anchors_reproduce_at_the_winners_coordinate():
    stats = run(
        bundle(LANE_2012, [vol_target("BTAL", 0.20, 0.8), vol_target("BIL", 0.20, 0.8)]),
        NET,
    )
    btal = stats["VT TQQQ/BTAL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"]
    bil = stats["VT TQQQ/BIL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"]
    assert round(btal["calmar"], 8) == 0.69991357
    assert round(bil["calmar"], 8) == 0.79914190
    assert bil["cagr"] - btal["cagr"] == pytest.approx(0.0345, abs=0.0002)
    assert bil["max_drawdown"] - btal["max_drawdown"] == pytest.approx(-0.0108, abs=0.0002)


# --- B5 — the sleeve facts §2.1 and §1 state -------------------------------
#
# BTAL's drift is the cost and its anti-beta is the product: it compounds
# negatively over both lanes, yet it was positive in every one of TQQQ's eight
# worst months since 2012. Both halves are pinned, because the whole spec is
# about what that trade is worth.

SLEEVE_FACTS = [  # symbol, start, CAGR net15 %, CAGR gross %, max drawdown %
    ("BTAL", LANE_2012, -3.43, -3.29, -52.70),
    ("BIL", LANE_2012, 1.29, 1.52, -0.35),
    ("BTAL", LANE_2021, -5.97, -5.65, -47.83),
    ("BIL", LANE_2021, 2.66, 3.13, -0.13),
]


@pytest.mark.parametrize(
    "symbol,start,net15,gross,expected_dd", SLEEVE_FACTS,
    ids=[f"{s}-{t[:4]}" for s, t, _, _, _ in SLEEVE_FACTS],
)
def test_the_sleeve_components_measure_what_the_spec_states(
    symbol, start, net15, gross, expected_dd
):
    assert cagr(NET, symbol, start) * 100 == pytest.approx(net15, abs=0.02)
    assert cagr(GROSS, symbol, start) * 100 == pytest.approx(gross, abs=0.02)
    # §2.1's max-drawdown column is measured on the gross root, not the net15
    # one its header implies (CASH_SLEEVE_SPEC erratum 2). The distinction is
    # 0.9 pp for BTAL and nothing for BIL, whose drawdowns are a tenth of a
    # point either way.
    assert max_drawdown(GROSS, symbol, start) * 100 == pytest.approx(expected_dd, abs=0.02)


# TQQQ's eight worst month-end-to-month-end returns since 2012 and BTAL in the
# same month, in §2.1's order and to its precision. The insurance is collected
# on eight month-ends in fourteen years; §1's "~4.7 pp/yr" is what holding it
# between them costs.
WORST_MONTHS = [
    ((2020, 3), -38.1, 9.3), ((2022, 4), -37.2, 8.5),
    ((2022, 9), -30.5, 2.8), ((2022, 6), -27.4, 7.6),
    ((2018, 12), -26.8, 4.2), ((2018, 10), -26.6, 5.6),
    ((2022, 12), -26.2, 3.5), ((2022, 1), -25.7, 5.2),
]


def monthly_returns(symbol: str) -> dict[tuple[int, int], float]:
    frame = read_close(NET / f"{symbol}.csv").filter(
        pl.col("time") >= dt.date.fromisoformat(LANE_2012)
    )
    ends: dict[tuple[int, int], float] = {}
    for date, close in zip(frame["time"], frame["close"]):
        ends[(date.year, date.month)] = close  # last bar of each month wins
    months = sorted(ends)
    return {m: ends[m] / ends[p] - 1 for p, m in zip(months, months[1:])}


def test_btal_was_positive_in_every_one_of_tqqqs_eight_worst_months():
    tqqq, btal = monthly_returns("TQQQ"), monthly_returns("BTAL")
    assert sorted(tqqq, key=tqqq.get)[:8] == [m for m, _, _ in WORST_MONTHS]
    for month, risk, sleeve in WORST_MONTHS:
        assert tqqq[month] * 100 == pytest.approx(risk, abs=0.05), month
        assert btal[month] * 100 == pytest.approx(sleeve, abs=0.05), month
        assert btal[month] > 0, month
