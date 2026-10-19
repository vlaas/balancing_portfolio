"""EXECUTION_ROBUSTNESS_SPEC §7 — X4–X8 for execution_report.py (X1–X3 are in test_simulate.py)."""

import json
from pathlib import Path

import polars as pl
import pytest

import execution_report as er
from main import run_bundle
from spec import build_bundle, load_spec

# A frozen gross root with OHLC in unadjusted/; tests never read live data/.
ROOT = Path(__file__).parent / "data" / "2026-08-24"
SPEC_PATH = Path(__file__).parent.parent / "specs" / "exec_top_2021.json"
VT = 4  # the spec's first four rows; the fifth is the SPY benchmark


def frozen_spec() -> dict:
    """The run spec with its `end` moved onto the frozen root's last bar."""
    spec = load_spec(SPEC_PATH)
    return spec | {"config": spec["config"] | {"end": "2026-08-24"}}


@pytest.fixture(scope="module")
def canonical() -> dict[str, dict]:
    return {r.label: r.stats for r in run_bundle(build_bundle(frozen_spec()), ROOT)}


# --- X4: the session calendar --------------------------------------------------------


def test_zero_offsets_are_the_identity():
    anchors = [8, 29, 49, 70]
    assert er.calendar(anchors, [0] * 4, 80) == (anchors, 0, 0)


def test_rows_outside_the_tradeable_span_are_clamped():
    # Day 0 is the initial investment and the last row values only.
    assert er.calendar([3, 25], [-5, 0], 50) == ([1, 25], 1, 0)
    assert er.calendar([10, 40], [0, 20], 50) == ([10, 48], 1, 0)


def test_a_crossing_session_is_bumped_after_its_predecessor():
    assert er.calendar([10, 20], [8, -5], 50) == ([18, 19], 0, 1)


def test_an_infeasible_tail_raises():
    with pytest.raises(ValueError, match="do not fit"):
        er.calendar([47, 48], [5, 5], 50)


def test_random_calendars_keep_one_increasing_session_per_month():
    anchors = list(range(8, 1450, 21))
    for offsets in er.draw_offsets(len(anchors), 10, 50, seed=7):
        rows, clamps, bumps = er.calendar(anchors, offsets, 1464)
        assert len(rows) == len(anchors)
        assert all(a < b for a, b in zip(rows, rows[1:]))
        assert 1 <= rows[0] and rows[-1] <= 1462
        moved = sum(row != anchor + d for row, anchor, d in zip(rows, anchors, offsets))
        assert moved <= clamps + bumps


# --- X5: the draws -------------------------------------------------------------------


def test_draws_are_deterministic_and_prefix_stable():
    assert er.draw_offsets(70, 10, 5, seed=1) == er.draw_offsets(70, 10, 5, seed=1)
    assert er.draw_offsets(70, 10, 3, seed=1) == er.draw_offsets(70, 10, 10, seed=1)[:3]
    assert er.draw_offsets(70, 10, 3, seed=1) != er.draw_offsets(70, 10, 3, seed=2)


def test_draws_cover_every_offset_and_nothing_else():
    seen = {d for draw in er.draw_offsets(70, 10, 5, seed=0) for d in draw}
    assert seen == set(range(-10, 11))


# --- X6: jitter on the frozen root ---------------------------------------------------


@pytest.fixture(scope="module")
def jitter() -> tuple[dict, list[dict]]:
    return er.jitter_report(frozen_spec(), SPEC_PATH, ROOT, days=2, draws=4, seed=3)


def test_scan_offset_zero_is_the_canonical_run(jitter, canonical):
    payload, _ = jitter
    zero = next(s for s in payload["scan"] if s["d"] == 0)
    assert (zero["clamps"], zero["bumps"]) == (0, 0)
    assert list(zero["metrics"]) == list(canonical)
    for label, stats in canonical.items():
        for metric in ("final_value", "cagr", "max_drawdown"):
            assert zero["metrics"][label][metric] == stats[metric]
        assert payload["distribution"][label]["cagr"]["canonical"] == stats["cagr"]


def test_jitter_shape_and_reproducibility(jitter):
    payload, rows = jitter
    labels = payload["strategies"]
    assert [s["d"] for s in payload["scan"]] == [-2, -1, 0, 1, 2]
    assert len(rows) == 4 * len(labels)
    assert set(payload["paired"]) == set(labels[:-1]) == set(payload["readout"])
    for label in labels:
        d = payload["distribution"][label]["calmar"]
        assert d["min"] <= d["p10"] <= d["p50"] <= d["p90"] <= d["max"]
    assert sum(payload["best"][label]["calmar"] for label in labels) == pytest.approx(1.0)
    # Same seed, fewer draws: the first two draws are the same simulations.
    _, again = er.jitter_report(frozen_spec(), SPEC_PATH, ROOT, days=2, draws=2, seed=3)
    assert again == rows[: 2 * len(labels)]


def test_jitter_rejects_a_rebalance_cadence():
    spec = frozen_spec()
    first = spec["strategies"][0] | {"rebalance": {"months": 3}}
    spec = spec | {"strategies": [first, *spec["strategies"][1:]]}
    with pytest.raises(SystemExit, match="cadence"):
        er.jitter_report(spec, SPEC_PATH, ROOT, days=1, draws=1, seed=0)


# --- X7: fills on the frozen root ----------------------------------------------------


@pytest.fixture(scope="module")
def fills() -> dict:
    return er.fills_report(frozen_spec(), SPEC_PATH, ROOT, [0.5, 0.0])


def test_alpha_zero_is_the_canonical_run(fills, canonical):
    assert fills["params"]["alpha"] == [0.0, 0.5]
    for label, stats in canonical.items():
        row = fills["rows"][label]["0"]
        for metric in ("final_value", "cagr", "max_drawdown"):
            assert row[metric] == stats[metric]
        assert row["slippage"] == 0.0


def test_adverse_fills_cost_every_strategy(fills):
    for label in fills["strategies"]:
        rows = fills["rows"][label]
        assert rows["0.5"]["final_value"] < rows["0"]["final_value"]
        assert rows["0.5"]["slippage"] > 0.0
    assert set(fills["readout"]) == set(fills["strategies"][:VT])
    # KMLM printed no bar on 80 sessions of its thin first year (2020-12-21 →
    # 2022-01-19); the engine carries its close over them and so does the fill.
    assert fills["data"]["missing_bars"] == {
        "BIL": 0, "BTAL": 0, "DBMF": 0, "KMLM": 80, "SPY": 0, "TQQQ": 0,
    }


def test_range_ratios_bracket_the_close():
    bundle, prices = er.load(frozen_spec(), ROOT)
    symbols = sorted({s for st in bundle.strategies for s in st.weights})
    ranged, missing = er.with_ranges(prices, ROOT, symbols)
    assert ranged.height == prices.height
    for symbol in symbols:
        assert ranged[f"{symbol}:HR"].min() >= 1.0 >= ranged[f"{symbol}:LR"].max()


def test_break_even_interpolates_between_levels():
    assert er.break_even([0.0, 0.5, 1.0], [0.04, 0.01, -0.01]) == pytest.approx(0.75)
    assert er.break_even([0.0, 0.5], [0.02, 0.01]) is None
    assert er.break_even([0.0, 0.5], [-0.01, -0.02]) == 0.0


# --- X8: the CLI ---------------------------------------------------------------------


def test_cli_writes_the_documented_artefacts(tmp_path, capsys):
    spec = tmp_path / "exec.json"
    spec.write_text(json.dumps(frozen_spec()))
    er.main(["fills", "--spec", str(spec), "--data", str(ROOT), "--alpha", "0", "1",
             "--out", str(tmp_path / "out")])
    er.main(["jitter", "--spec", str(spec), "--data", str(ROOT), "--days", "1",
             "--draws", "2", "--out", str(tmp_path / "out")])

    names = sorted(p.name for p in (tmp_path / "out").iterdir())
    assert names == ["fills.json", "fills.md", "jitter.json", "jitter.md", "jitter_draws.csv"]
    payload = json.loads((tmp_path / "out" / "jitter.json").read_text())
    assert payload["command"].startswith("uv run execution_report.py jitter --spec")
    assert payload["params"] == {"days": 1, "draws": 2, "seed": 20261020}
    draws = pl.read_csv(tmp_path / "out" / "jitter_draws.csv")
    assert draws.height == 2 * 5
    assert "Read-out" in capsys.readouterr().out
