import json
from pathlib import Path

import pytest

from bundles import BUNDLES
from indicators import ewma_vol, ratio_sma, sma
from main import collect_indicators, main, run_bundle
from strategy import Strategy

GOLDEN_DIR = Path(__file__).parent / "data"


# T7 — Declaration guard.


def test_indicators_merge_across_strategies_and_dedup_by_name():
    one = Strategy(
        label="one", weights={"A": 1.0}, data=("X",), indicators={"X": (sma(200),)}
    )
    two = Strategy(
        label="two",
        weights={"A": 1.0},
        data=("X",),
        indicators={"X": (sma(200), ewma_vol(0.94)), "A": (sma(10),)},
    )

    merged = collect_indicators([one, two])

    assert sorted(merged) == ["A", "X"]
    assert [i.name for i in merged["X"]] == ["SMA200", "VOL_EWMA94"]
    assert [i.name for i in merged["A"]] == ["SMA10"]


def test_indicator_on_an_undeclared_symbol_is_rejected():
    rogue = Strategy(label="rogue", weights={"A": 1.0}, indicators={"QQQ": (sma(200),)})

    with pytest.raises(AssertionError, match="rogue: indicator on undeclared symbol QQQ"):
        collect_indicators([rogue])


def test_indicator_with_an_undeclared_input_is_rejected():
    # REGIME_SPEC §3.3 — the host and every input must be declared.
    rogue = Strategy(
        label="rogue",
        weights={"A": 1.0},
        data=("VIX",),
        indicators={"VIX": (ratio_sma("VIX3M", 10),)},
    )

    with pytest.raises(
        AssertionError,
        match="rogue: indicator VIX:RATIO_VIX3M_SMA10 reads undeclared symbol VIX3M",
    ):
        collect_indicators([rogue])


def test_indicator_with_a_declared_input_passes():
    fine = Strategy(
        label="fine",
        weights={"A": 1.0},
        data=("VIX", "VIX3M"),
        indicators={"VIX": (ratio_sma("VIX3M", 10),)},
    )

    merged = collect_indicators([fine])

    assert [i.name for i in merged["VIX"]] == ["RATIO_VIX3M_SMA10"]
    assert merged["VIX"][0].inputs == ("VIX3M",)


# T8 — Golden regression against the frozen snapshot.
#
# The inputs never change, so a failure here means the engine changed. Fix the
# bug, or update this dict in the same commit with the reason in the message.
# Never "fix" it by refreshing the snapshot.

GOLDEN = {
    "TQQQ/BTAL 50/50": (237_275.03, 0.2366, -0.4497),
    "TQQQ 100%": (661_164.25, 0.4159, -0.8175),
    "TQQQ/BTAL SMA gate": (224_725.33, 0.2269, -0.3773),
    "SPY benchmark": (153_938.16, 0.1370, -0.3397),
}


def test_default_bundle_reproduces_the_golden_numbers():
    results = run_bundle(BUNDLES["default"], GOLDEN_DIR)

    assert [r.label for r in results] == list(GOLDEN)
    for result in results:
        final, cagr, max_dd = GOLDEN[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["cagr"] == pytest.approx(cagr, abs=0.00005)
        assert result.stats["max_drawdown"] == pytest.approx(max_dd, abs=0.00005)


# Cost golden — COST_MODEL_SPEC.md T7. The default bundle under the tastytrade
# base schedule (per-asset, "*" covering future safe-asset swaps) and 3% cash
# yield, same snapshot, same rule as above. Pins the fee arithmetic and the
# per-asset/"*" resolution end to end. Produced by the implementation once and
# eyeballed: the 50/50 loses ~0.26% of final value to friction, TQQQ 100%
# almost nothing (it never sells), and the SPY benchmark comes out slightly
# ahead — interest on idle cash exceeds its fees.

COST_GOLDEN = {
    "TQQQ/BTAL 50/50": (236_655.36, 344.26),
    "TQQQ 100%": (661_163.13, 10.12),
    "TQQQ/BTAL SMA gate": (224_297.69, 262.53),
    "SPY benchmark": (153_978.98, 4.71),
}


def test_default_bundle_reproduces_the_cost_golden_numbers():
    import dataclasses

    bundle = BUNDLES["default"]
    config = dataclasses.replace(
        bundle.config,
        cost_bps={"TQQQ": 1.5, "BTAL": 6, "QQQ": 1, "SPY": 0.7, "*": 6},
        cash_yield=0.03,
    )
    results = run_bundle(dataclasses.replace(bundle, config=config), GOLDEN_DIR)

    assert [r.label for r in results] == list(COST_GOLDEN)
    for result in results:
        final, fees = COST_GOLDEN[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["total_fees"] == pytest.approx(fees, abs=0.005)

    turnover = {r.label: r.stats["turnover"] for r in results}
    # The gate blocks buy-side rebalancing while TQQQ sits below its SMA, so
    # the gated 50/50 turns over less than the plain one; both dwarf the
    # never-selling TQQQ 100%, which shows only the contribution floor.
    assert turnover["TQQQ 100%"] < turnover["TQQQ/BTAL SMA gate"] < turnover["TQQQ/BTAL 50/50"]


# The spec CLI — DECLARATIVE_SPEC.md T9.


def test_spec_cli_writes_json_and_nothing_else(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out.json"
    charts = tmp_path / "charts"
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--spec", str(Path(__file__).parents[1] / "specs" / "research.json"),
            "--data", str(GOLDEN_DIR),
            "--json", str(out),
            "--charts", str(charts),
            "--no-charts",
            "--quiet",
        ],
    )

    main()

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines and all(line.startswith("Saved") for line in lines)
    assert not charts.exists()

    payload = json.loads(out.read_text())
    assert payload["run"]["schema_version"] == 4
    assert payload["run"]["bundle"] == "research"
    assert payload["run"]["data_dir"] == str(GOLDEN_DIR)
    assert payload["run"]["spec_path"].endswith("research.json")
    assert len(payload["spec"]["strategies"]) == 6
    assert all(entry["spec"] for entry in payload["strategies"])


def test_end_cli_reaches_results_json_config(tmp_path, monkeypatch):
    out = tmp_path / "out.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--spec", str(Path(__file__).parents[1] / "specs" / "research.json"),
            "--data", str(GOLDEN_DIR),
            "--end", "2024-12-31",
            "--json", str(out),
            "--no-charts",
            "--quiet",
        ],
    )

    main()

    payload = json.loads(out.read_text())
    assert payload["config"]["end"] == "2024-12-31"
    assert payload["spec"]["config"]["end"] == "2024-12-31"
    assert payload["data"]["end"] <= "2024-12-31"


def test_bundle_and_spec_are_mutually_exclusive(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv", ["main.py", "default", "--spec", "specs/research.json"]
    )

    with pytest.raises(SystemExit):
        main()

    assert "mutually exclusive" in capsys.readouterr().err
