"""EU_SUBSTITUTE_SPEC §8 T6 — the eight lane bundles load, simulate on their
frozen roots, and name every symbol they read; the c20 twins differ from their
bases in the cost schedule alone; the 2020 primary is the solve's grid point.
"""

import json
from pathlib import Path

import pytest

from main import run_bundle
from spec import build_bundle, load_spec

SPECS = Path(__file__).parents[1] / "specs"
RESULTS = Path(__file__).parents[1] / "results"
USD = Path(__file__).parent / "data" / "2026-09-02-net15-usd"
HC = USD.with_name(USD.name + "-hc")
LANES = [
    ("eu_points_2020", USD), ("eu_points_2020_c20", USD),
    ("eu_points_2025", USD), ("eu_points_2025_c20", USD),
    ("eu_points_2019_hc", HC), ("eu_points_2019_hc_c20", HC),
    ("eu_points_2021_hc", HC), ("eu_points_2021_hc_c20", HC),
    ("eu_points_2020_usref", USD),  # the US winners on the eu-2020 window (reference)
]
ROOT = pytest.mark.skipif(not HC.exists(), reason="the roots are committed with the freeze")


@ROOT
@pytest.mark.parametrize("stem,root", LANES, ids=[s for s, _ in LANES])
def test_each_lane_loads_simulates_and_names_every_symbol_it_reads(stem, root):
    bundle = build_bundle(load_spec(SPECS / f"{stem}.json"))
    symbols = {s for st in bundle.strategies for s in (*st.weights, *st.data)}
    for symbol in symbols:
        assert (root / f"{symbol}.csv").exists(), symbol
    results = run_bundle(bundle, root)
    assert [r.label for r in results] == [st.label for st in bundle.strategies]
    assert results[-1].label == "SPY benchmark" and results[-2].label == "CSPX benchmark"
    committed = json.loads((RESULTS / f"{stem}.json").read_text())
    assert committed["run"]["data_dir"].endswith(root.name)
    assert committed["data"]["symbols"] == sorted(symbols)
    for got, want in zip(results, committed["strategies"]):
        assert got.label == want["label"]
        assert got.stats["cagr"] == pytest.approx(want["summary"]["cagr"], abs=1e-8)
        assert got.stats["max_drawdown"] == pytest.approx(want["summary"]["max_drawdown"], abs=1e-8)


@pytest.mark.parametrize("stem", [s for s, _ in LANES if not s.endswith(("_c20", "_usref"))])
def test_the_c20_twin_differs_from_its_base_in_the_cost_schedule_alone(stem):
    base = json.loads((SPECS / f"{stem}.json").read_text())
    twin = json.loads((SPECS / f"{stem}_c20.json").read_text())
    assert twin["config"]["cost_bps"] == {"*": 20}
    base["config"].pop("cost_bps"), twin["config"].pop("cost_bps")
    assert base == twin


def test_the_2020_primary_is_the_solved_grid_point():
    chosen = json.loads((RESULTS / "synb" / "synb.json").read_text())["estimation"]["chosen"]
    primary = json.loads((SPECS / "eu_points_2020.json").read_text())["strategies"][0]
    assert primary["safe"] == {"MVEA": round(1 - chosen, 6), "XSPS": chosen}
    flag = json.loads((SPECS / "eu_points_2020.json").read_text())["strategies"][3]
    assert flag["safe"] == {"IB01": 0.5, "MVEA": round(0.5 * (1 - chosen), 6), "XSPS": round(0.5 * chosen, 6)}
    b75 = json.loads((SPECS / "eu_points_2025.json").read_text())["strategies"][0]
    assert b75["safe"] == {"MVEA": round(0.75 * (1 - chosen), 6), "XSPS": round(0.75 * chosen, 6), "DBMF_EU": 0.25}
