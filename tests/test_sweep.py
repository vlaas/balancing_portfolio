# Sweep expansion and windows — SWEEP_SPEC.md T3, T4.

import copy
import datetime as dt
import json
import re
from pathlib import Path

import polars as pl
import pytest

from spec import _TYPES, REQUIRED_KEYS, load_spec
from sweep import Window, _window_plan, build_summary, expand, run_sweep, validate, windows
from sweep import main as sweep_main

GOLDEN_DIR = Path(__file__).parent / "data"
SPECS = Path(__file__).parents[1] / "specs"

# The SWEEP_SPEC §4.1 template, verbatim.
TEMPLATE = {
    "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
    "vol": {"kind": "ewma", "lam": {"grid": [0.90, 0.94, 0.97]}},
    "leverage": 3,
    "sigma_target": {"grid": [0.30, 0.35, 0.40, 0.45, 0.50]},
    "w_max": {"grid": [0.6, 0.7, 0.8]},
    "gate": {"grid": [None, {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}]},
}


def template() -> dict:
    return copy.deepcopy(TEMPLATE)


# --- T3: expansion -----------------------------------------------------------


def test_template_expands_to_90_in_document_order():
    out = expand(template())

    assert len(out) == 90
    # Dimensions in document order (vol.lam, sigma_target, w_max, gate); the
    # last one varies fastest through the Cartesian product.
    assert out[0]["params"] == {
        "vol.lam": 0.90, "sigma_target": 0.30, "w_max": 0.6, "gate": None,
    }
    assert out[1]["params"] == {
        "vol.lam": 0.90, "sigma_target": 0.30, "w_max": 0.6, "gate": "QQQ<SMA200",
    }
    assert out[89]["params"] == {
        "vol.lam": 0.97, "sigma_target": 0.50, "w_max": 0.8, "gate": "QQQ<SMA200",
    }


def test_every_element_has_the_four_dotted_keys_and_a_unique_label():
    out = expand(template())

    assert all(
        set(e["params"]) == {"vol.lam", "sigma_target", "w_max", "gate"} for e in out
    )
    assert len({e["label"] for e in out}) == 90


def test_null_grid_branch_omits_the_key_from_the_entry():
    out = expand(template())

    assert "gate" not in out[0]["entry"]
    assert out[1]["entry"]["gate"] == {
        "symbol": "QQQ", "assets": ["TQQQ"],
        "contribution_exempt": False, "sma_days": 200,
    }
    # The entries are normalised: defaults and the auto-label are filled in.
    assert out[0]["entry"]["label"] == out[0]["label"]
    assert out[0]["entry"]["w_min"] == 0.0


def test_null_over_a_required_key_substitutes_the_literal_null():
    t = template()
    t["safe"] = {"grid": ["BTAL", None]}  # required-but-nullable: null means cash

    out = expand(t)

    assert len(out) == 180  # 2 safe x 3 lam x 5 sigma x 3 w_max x 2 gate
    cash = [e for e in out if e["params"]["safe"] is None]
    assert len(cash) == 90
    assert all(e["entry"]["safe"] is None for e in cash)
    assert cash[0]["label"] == "VT TQQQ/cash t30 w0-60 QQQ:VOL_EWMA90"
    # A null safe is a one-asset universe; the residual 1 - w stays in cash.
    st = _TYPES["vol_target"](cash[0]["entry"], "template")
    assert st.weights == {"TQQQ": 0.6}


def test_a_sleeve_is_an_ordinary_grid_value():
    t = template()
    t["safe"] = {"grid": ["BTAL", {"KMLM": 0.5, "BTAL": 0.5}, None]}

    out = expand(t)

    assert len(out) == 270  # 3 safe x 3 lam x 5 sigma x 3 w_max x 2 gate
    # params render through safe_str, not compact JSON: the column stays a
    # scalar the summary can rank and print.
    assert [e["params"]["safe"] for e in out[::90]] == ["BTAL", "BTAL50+KMLM50", None]
    blend = [e for e in out if e["params"]["safe"] == "BTAL50+KMLM50"]
    assert blend[0]["entry"]["safe"] == {"KMLM": 0.5, "BTAL": 0.5}
    assert blend[0]["label"] == "VT TQQQ/BTAL50+KMLM50 t30 w0-60 QQQ:VOL_EWMA90"
    assert len({e["label"] for e in out}) == 270


def test_null_over_an_optional_key_still_deletes_it():
    t = template()
    t["w_max"] = {"grid": [0.6, None]}

    out = expand(t)

    absent = [e for e in out if e["params"]["w_max"] is None]
    assert len(absent) == 30  # 3 lam x 5 sigma x 2 gate
    # Deleted rather than substituted, so the builder's default w_max = 1.0
    # applies; a substituted None would fail its 0 <= w_min <= w_max <= 1 check.
    assert all(e["entry"]["w_max"] == 1.0 for e in absent)
    assert absent[0]["label"] == "VT TQQQ/BTAL t30 w0-100 QQQ:VOL_EWMA90"


def test_null_over_a_required_key_the_builder_rejects_fails_loudly():
    t = {"type": "fixed", "weights": {"grid": [{"TQQQ": 0.5, "BTAL": 0.5}, None]}}

    with pytest.raises(ValueError, match=re.escape("template.weights")):
        expand(t)


def test_required_keys_is_the_builders_own_missing_key_set():
    assert REQUIRED_KEYS["vol_target"] == {
        "type", "risk", "safe", "vol_symbol", "vol", "sigma_target",
    }
    assert REQUIRED_KEYS["fixed"] == {"type", "weights"}

    valid = {
        "vol_target": {
            "type": "vol_target", "risk": "TQQQ", "safe": "BTAL",
            "vol_symbol": "QQQ", "vol": {"kind": "ewma", "lam": 0.9},
            "sigma_target": 0.35,
        },
        "fixed": {"type": "fixed", "weights": {"TQQQ": 1.0}},
    }
    for name, entry in valid.items():
        _TYPES[name](entry, "e")  # the full entry builds
        for key in REQUIRED_KEYS[name]:
            with pytest.raises(ValueError, match=re.escape(f"e.{key}: missing key")):
                _TYPES[name]({k: v for k, v in entry.items() if k != key}, "e")


def test_single_value_grid_raises():
    t = template()
    t["sigma_target"] = {"grid": [0.35]}
    with pytest.raises(ValueError, match=re.escape("template.sigma_target.grid")):
        expand(t)

    t["sigma_target"] = {"grid": [0.35, 0.35]}  # duplicates are not distinct
    with pytest.raises(ValueError, match=re.escape("template.sigma_target.grid")):
        expand(t)


def test_grid_inside_the_gate_object():
    t = template()
    t["gate"] = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": {"grid": [100, 200]}}

    out = expand(t)

    assert len(out) == 90  # 3 lam x 5 sigma x 3 w_max x 2 sma_days
    assert {e["params"]["gate.sma_days"] for e in out} == {100, 200}
    assert set(out[0]["params"]) == {"vol.lam", "sigma_target", "w_max", "gate.sma_days"}


def test_grid_inside_a_list_raises():
    t = template()
    t["gate"] = {
        "symbol": "QQQ",
        "assets": [{"grid": [["TQQQ"], ["TQQQ", "BTAL"]]}],
        "sma_days": 200,
    }
    with pytest.raises(ValueError, match=re.escape("template.gate.assets.0")):
        expand(t)


def test_expand_is_deterministic():
    assert expand(template()) == expand(template())


# --- REGIME_SPEC R8: regime and composite gates in grids ---------------------

G_SMA = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}
G_R1 = {
    "symbol": "VIX", "denominator": "VIX3M", "assets": ["TQQQ"],
    "ratio_sma": 1, "fire": 1.0,
}


def flat_template() -> dict:
    return {
        "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.80}, "leverage": 3,
        "sigma_target": 0.30, "w_max": 0.6,
    }


def test_categorical_gate_grid_renders_composites_as_strings():
    t = flat_template()
    t["gate"] = {"grid": [None, dict(G_SMA), dict(G_R1), [dict(G_SMA), dict(G_R1)]]}

    out = expand(t)

    assert [e["params"]["gate"] for e in out] == [
        None, "QQQ<SMA200", "VIX/VIX3M@1>=1.00", "QQQ<SMA200|VIX/VIX3M@1>=1.00",
    ]
    assert len({e["label"] for e in out}) == 4
    # The composite arm's entry embeds the normalised member list.
    assert [g["symbol"] for g in out[3]["entry"]["gate"]] == ["QQQ", "VIX"]


def test_nested_regime_grids_expand_to_the_product():
    t = flat_template()
    t["gate"] = G_R1 | {
        "ratio_sma": {"grid": [1, 10]},
        "fire": {"grid": [0.95, 1.00]},
        "w_off": {"grid": [None, 0]},
    }

    out = expand(t)

    assert len(out) == 8
    assert set(out[0]["params"]) == {"gate.ratio_sma", "gate.fire", "gate.w_off"}
    assert {e["params"]["gate.fire"] for e in out} == {0.95, 1.00}
    # The null branch deletes the optional key (SWEEP_SPEC errata 3): no w_off
    # in the entry, None in the params.
    without = [e for e in out if e["params"]["gate.w_off"] is None]
    assert len(without) == 4
    assert all("w_off" not in e["entry"]["gate"] for e in without)
    assert all(e["entry"]["gate"]["w_off"] == 0 for e in out if e not in without)
    assert len({e["label"] for e in out}) == 8


def test_fire_is_numeric_and_w_off_categorical_in_the_summary():
    t = flat_template()
    t["gate"] = G_R1 | {
        "fire": {"grid": [0.95, 1.00, 1.05]},
        "w_off": {"grid": [None, 0]},
    }
    spec = t5_spec(t)
    expanded = expand(spec["template"])
    labels = [e["label"] for e in expanded]
    wins = [Window("full", "full", dt.date(2020, 1, 2), dt.date(2026, 1, 2))]
    # Expansion order: fire varies slowest, w_off fastest.
    records = {"full": {l: stats_of(o) for l, o in zip(labels, [1, 2, 3, 4, 5, 6])}}
    records["full"]["bench"] = stats_of(0)

    summary = build_summary(
        spec, wins, expanded, ["bench"], records,
        {l: True for l in labels}, notes=[], warnings=[],
    )

    s = summary["strategies"]
    # (fire 1.00, w_off None) = 3: fire neighbours with the same w_off only.
    assert s[2]["neighbourhood"] == {
        "neighbour_min": 1, "neighbour_mean": 3.0, "edge": False,
    }
    # (fire 0.95, w_off 0) = 2: one fire neighbour, on the fire boundary.
    assert s[1]["neighbourhood"]["neighbour_min"] == 4
    assert s[1]["neighbourhood"]["edge"] is True


def test_an_ordinary_spec_names_the_right_entry_point():
    with pytest.raises(ValueError, match=re.escape("run it with `uv run main.py --spec")):
        validate(load_spec(SPECS / "research.json"))


# --- T4: windows -------------------------------------------------------------


def weekdays(start: dt.date, end: dt.date) -> list[dt.date]:
    days = []
    day = start
    while day <= end:
        if day.weekday() < 5:
            days.append(day)
        day += dt.timedelta(days=1)
    return days


CALENDAR = weekdays(dt.date(2020, 1, 1), dt.date(2026, 12, 31))


def spec_of(windows_block: dict) -> dict:
    return {"windows": windows_block}


def test_start_snaps_forward_and_end_snaps_backward():
    wins, notes, _ = _window_plan(
        spec_of({"start": "2020-01-04", "end": "2020-06-07"}), CALENDAR
    )

    # 2020-01-04 is a Saturday, 2020-06-07 a Sunday.
    assert wins == [Window("full", "full", dt.date(2020, 1, 6), dt.date(2020, 6, 5))]
    assert notes == [
        "windows.start 2020-01-04 -> 2020-01-06",
        "windows.end 2020-06-07 -> 2020-06-05",
    ]


def test_trading_day_dates_snap_nowhere_and_leave_no_notes():
    wins, notes, warnings = _window_plan(spec_of({"start": "2020-01-02"}), CALENDAR)

    assert len(wins) == 1
    assert wins[0].start == dt.date(2020, 1, 2)
    assert wins[0].end == CALENDAR[-1]  # end null -> the last trading day
    assert notes == [] and warnings == []


def test_holdout_produces_adjacent_disjoint_fit_and_test():
    wins = windows(
        spec_of({"start": "2020-01-02", "holdout": "2023-01-01"}), CALENDAR
    )

    full, fit, test = wins
    assert [w.kind for w in wins] == ["full", "fit", "test"]
    assert fit.start == full.start and test.end == full.end
    assert fit.end < test.start
    # Adjacent: not a single trading day falls between fit and test.
    between = [d for d in CALENDAR if fit.end < d < test.start]
    assert between == []
    assert test.start == dt.date(2023, 1, 2)  # 2023-01-01 is a Sunday
    assert fit.end == dt.date(2022, 12, 30)


def test_rolling_windows_keep_their_length_and_drop_overruns():
    wins = windows(
        spec_of({
            "start": "2020-01-02",
            "sensitivity": {"every_months": 12, "length_years": 2},
        }),
        CALENDAR,
    )

    sens = [w for w in wins if w.kind == "sens"]
    # Raw starts every Jan 2, 2020..2024 (2025 + 2y overruns the end); names
    # carry the snapped start, so weekend Jan 2nds move to the Monday.
    assert [w.name for w in sens] == [
        "sens_2020-01-02", "sens_2021-01-04", "sens_2022-01-03",
        "sens_2023-01-02", "sens_2024-01-02",
    ]
    for w in sens:
        assert 726 <= (w.end - w.start).days <= 731
        assert w.end <= wins[0].end


def test_anchored_mode_when_length_years_is_null():
    wins, _, warnings = _window_plan(
        spec_of({
            "start": "2020-01-02",
            "end": "2022-01-03",
            "sensitivity": {"every_months": 12, "length_years": None},
        }),
        CALENDAR,
    )

    sens = [w for w in wins if w.kind == "sens"]
    assert [w.start.isoformat() for w in sens] == ["2020-01-02", "2021-01-04"]
    assert all(w.end == wins[0].end for w in sens)  # anchored: every end is `end`
    assert any("anchored" in w for w in warnings)


def test_short_test_window_warns_but_never_errors():
    wins, _, warnings = _window_plan(
        spec_of({"start": "2020-01-02", "end": "2024-12-31", "holdout": "2024-01-02"}),
        CALENDAR,
    )

    assert [w.kind for w in wins] == ["full", "fit", "test"]
    assert any("shorter than 2 years" in w for w in warnings)


# --- T5: neighbourhood and ranks --------------------------------------------

# A 3x3 numeric grid with hand-picked full-window objectives:
#
#   sigma \ w_max   0.6  0.7  0.8
#            0.3      1    2    3
#            0.4      4    9    6
#            0.5      7    8    5
OBJ = [1, 2, 3, 4, 9, 6, 7, 8, 5]  # expansion order: sigma slower, w_max faster


def t5_spec(template: dict) -> dict:
    return {
        "schema_version": 1,
        "config": {"initial_capital": 10000, "monthly_contribution": 500},
        "windows": {"start": "2020-01-02"},
        "template": template,
        "baselines": [{"type": "fixed", "label": "bench", "weights": {"SPY": 1.0}}],
    }


def numeric_template() -> dict:
    return {
        "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.94},
        "sigma_target": {"grid": [0.3, 0.4, 0.5]},
        "w_max": {"grid": [0.6, 0.7, 0.8]},
    }


def stats_of(value: float, dd: float = -0.2) -> dict:
    return {
        "stats": {
            "calmar": value, "max_drawdown": dd,
            "best_year": (2020, 0.1), "worst_year": (2021, -0.1),
        },
        "exposure": {},
    }


def test_neighbourhood_ranks_and_robust_score():
    spec = t5_spec(numeric_template())
    expanded = expand(spec["template"])
    labels = [e["label"] for e in expanded]
    wins = [
        Window("full", "full", dt.date(2020, 1, 2), dt.date(2026, 1, 2)),
        Window("fit", "fit", dt.date(2020, 1, 2), dt.date(2022, 12, 30)),
        Window("test", "test", dt.date(2023, 1, 3), dt.date(2026, 1, 2)),
        Window("sens_a", "sens", dt.date(2020, 1, 2), dt.date(2025, 1, 2)),
        Window("sens_b", "sens", dt.date(2020, 7, 2), dt.date(2025, 7, 2)),
    ]
    # fit and both sens windows repeat the full objective; test is one lower.
    records = {}
    for w in wins:
        offset = -1 if w.kind == "test" else 0
        records[w.name] = {l: stats_of(o + offset) for l, o in zip(labels, OBJ)}
        records[w.name]["bench"] = stats_of(100)  # never ranked, however good
    feasible = {l: o != 7 for l, o in zip(labels, OBJ)}  # the 7 point is infeasible

    summary = build_summary(
        spec, wins, expanded, ["bench"], records, feasible, notes=[], warnings=[]
    )

    s = summary["strategies"]
    centre = s[4]  # objective 9
    assert centre["neighbourhood"] == {
        "neighbour_min": 2, "neighbour_mean": 5.0, "edge": False,
    }
    assert centre["sensitivity"]["rank_median"] == 1
    assert centre["sensitivity"]["rank_worst"] == 1
    assert centre["holdout"]["test_minus_fit"] == pytest.approx(-1.0)
    # min(full 9, neighbour_min 2, sens median 9, holdout test 8)
    assert centre["robust_score"] == 2

    corner = s[0]  # objective 1
    assert corner["neighbourhood"]["neighbour_min"] == 2  # neighbours 2 and 4
    assert corner["neighbourhood"]["edge"] is True
    assert corner["robust_score"] == 0  # its own holdout test: 1 - 1
    assert corner["sensitivity"]["rank_median"] == 8  # last among the 8 feasible

    assert s[1]["neighbourhood"]["neighbour_min"] == 1  # neighbours 1, 3 and 9
    assert s[7]["sensitivity"]["rank_median"] == 2  # objective 8

    infeasible = s[6]  # objective 7
    assert infeasible["full"]["feasible"] is False
    assert infeasible["sensitivity"]["rank_median"] is None
    assert infeasible["sensitivity"]["rank_worst"] is None

    bench = summary["baselines"][0]
    assert bench["label"] == "bench"
    assert "neighbourhood" not in bench and "robust_score" not in bench
    assert "params" not in bench and "feasible" not in bench["full"]
    assert "rank_median" not in bench["sensitivity"]
    assert bench["holdout"]["test_minus_fit"] == 0  # 100 in every window


def test_categorical_dimension_has_no_neighbours_and_no_edge():
    template = {
        "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.94}, "w_max": 0.7,
        "sigma_target": {"grid": [0.3, 0.4, 0.5]},
        "gate": {"grid": [None, {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}]},
    }
    spec = t5_spec(template)
    expanded = expand(spec["template"])
    labels = [e["label"] for e in expanded]
    wins = [Window("full", "full", dt.date(2020, 1, 2), dt.date(2026, 1, 2))]
    records = {"full": {l: stats_of(o) for l, o in zip(labels, [1, 2, 3, 4, 5, 6])}}
    records["full"]["bench"] = stats_of(0)

    summary = build_summary(
        spec, wins, expanded, ["bench"], records,
        {l: True for l in labels}, notes=[], warnings=[],
    )

    s = summary["strategies"]
    # (0.4, no gate): sigma neighbours with the same gate value only.
    assert s[2]["neighbourhood"] == {
        "neighbour_min": 1, "neighbour_mean": 3.0, "edge": False,
    }
    # (0.3, gated): one sigma neighbour; on the sigma boundary.
    assert s[1]["neighbourhood"]["neighbour_min"] == 4
    assert s[1]["neighbourhood"]["edge"] is True
    # No sens, no holdout: robust_score = min(full, neighbour_min).
    assert s[2]["robust_score"] == 1
    assert s[1]["holdout"] is None and s[1]["sensitivity"] is None


# --- T6: end to end ----------------------------------------------------------

T6_SPEC = {
    "schema_version": 1,
    "config": {"initial_capital": 10000, "monthly_contribution": 500},
    "windows": {
        "start": "2020-01-02",
        "holdout": "2023-01-03",
        "sensitivity": {"every_months": 12, "length_years": 6},
    },
    "template": {
        "type": "fixed",
        "weights": {"TQQQ": {"grid": [0.4, 0.6]}, "BTAL": {"grid": [0.4, 0.3]}},
    },
    "baselines": [{"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}}],
    "constraint": {"max_drawdown": -0.99},
}


def test_run_sweep_end_to_end():
    runs, summary = run_sweep(T6_SPEC, GOLDEN_DIR)

    # 4 grid strategies + 1 baseline over full, fit, test and one sens window
    # (the 2021 start + 6 years would overrun the data).
    assert runs.height == 5 * 4
    assert [w["kind"] for w in summary["windows"]] == ["full", "fit", "test", "sens"]

    baseline_rows = runs.filter(pl.col("is_baseline"))
    assert baseline_rows.height == 4
    assert baseline_rows["params.weights.TQQQ"].null_count() == 4
    assert baseline_rows["feasible"].all()

    for column in (
        "label", "kind", "window", "start", "end", "calmar", "max_drawdown",
        "best_year", "best_year_return", "worst_year", "worst_year_return",
        "params.weights.TQQQ", "params.weights.BTAL",
        "exposure.TQQQ.avg", "exposure.TQQQ.min", "exposure.SPY.avg",
        "cost_bps", "cash_yield", "data_dir",
    ):
        assert column in runs.columns

    # A cost-free sweep is self-describing about it.
    assert runs["cost_bps"].to_list() == [0.0] * runs.height
    assert runs["cash_yield"].to_list() == [0.0] * runs.height
    assert summary["costs"] == {"cost_bps": 0.0, "cash_yield": 0.0}

    assert len(summary["strategies"]) == 4
    for s in summary["strategies"]:
        assert s["full"]["feasible"] is True
        assert set(s["holdout"]) == {"fit", "test", "test_minus_fit"}
        assert set(s["sensitivity"]["objective"]) == {"median", "min", "max", "iqr"}
        assert s["sensitivity"]["rank_worst"] >= 1
        assert set(s["neighbourhood"]) == {"neighbour_min", "neighbour_mean", "edge"}
        assert "robust_score" in s
    assert summary["baselines"][0]["label"] == "SPY benchmark"


def test_sweep_config_costs_reach_every_window():
    # COST_MODEL_SPEC.md T6, sweep half: the fields are forwarded into every
    # window's Config — every run pays fees — and land in the artefacts.
    spec = copy.deepcopy(T6_SPEC)
    spec["config"]["cost_bps"] = {"TQQQ": 1.5, "*": 6}
    spec["config"]["cash_yield"] = 0.03

    runs, summary = run_sweep(spec, GOLDEN_DIR)

    schedule = json.dumps({"TQQQ": 1.5, "*": 6}, sort_keys=True)
    assert runs["cost_bps"].to_list() == [schedule] * runs.height
    assert runs["cash_yield"].to_list() == [0.03] * runs.height
    assert summary["costs"] == {"cost_bps": {"TQQQ": 1.5, "*": 6}, "cash_yield": 0.03}
    assert runs["total_fees"].min() > 0.0


def test_sweep_config_costs_out_of_range_names_the_path():
    spec = copy.deepcopy(T6_SPEC)
    spec["config"]["cost_bps"] = -1

    with pytest.raises(ValueError, match=re.escape("config.cost_bps")):
        validate(spec)


def test_cost_cli_overrides_land_in_the_artefacts(tmp_path, monkeypatch):
    spec_path = tmp_path / "grid.json"
    spec_path.write_text(json.dumps(T6_SPEC))
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        [
            "sweep.py", str(spec_path), "--data", str(GOLDEN_DIR), "--out", str(out),
            "--cost-bps", "20", "--cash-yield", "0.03",
        ],
    )

    sweep_main()

    runs = pl.read_csv(out / "runs.csv")
    assert runs["cost_bps"].to_list() == [20.0] * runs.height
    assert runs["cash_yield"].to_list() == [0.03] * runs.height
    summary = json.loads((out / "summary.json").read_text())
    assert summary["costs"] == {
        "cost_bps": 20.0, "cash_yield": 0.03,
        "cli_override": ["cost_bps", "cash_yield"],
    }
    md = (out / "summary.md").read_text()
    assert "- Costs: flat 20 bps (CLI override), cash yield 3% (CLI override)" in md


def test_cli_writes_the_five_artefacts(tmp_path, monkeypatch, capsys):
    spec_path = tmp_path / "grid.json"
    spec_path.write_text(json.dumps(T6_SPEC))
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(spec_path), "--data", str(GOLDEN_DIR), "--out", str(out)],
    )

    sweep_main()

    for name in ("strategies.json", "runs.csv", "runs.json", "summary.json", "summary.md"):
        assert (out / name).stat().st_size > 0
    assert len((out / "runs.csv").read_text().splitlines()) == 1 + 20
    printed = capsys.readouterr().out
    assert printed.count("strategies  ") == 4  # one progress line per window
    assert "## Baselines" in printed


def test_dry_run_prints_the_counts_and_writes_nothing(tmp_path, monkeypatch, capsys):
    spec_path = tmp_path / "grid.json"
    spec_path.write_text(json.dumps(T6_SPEC))
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(spec_path), "--data", str(GOLDEN_DIR), "--out", str(out), "--dry-run"],
    )

    sweep_main()

    assert "4 grid + 1 baselines x 4 windows = 20 runs" in capsys.readouterr().out
    assert not out.exists()


def test_dry_run_counts_of_the_regime_tune_lane(tmp_path, monkeypatch, capsys):
    # REGIME_SPEC R8: the §8.2 surface is 4 x 4 x 3 x 3 = 144 points over the
    # 2012 lane's 23 windows (full + fit + test + 20 sensitivity).
    net_dir = GOLDEN_DIR / "2026-08-20-net15"
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(SPECS / "sweep_regime_tune_2012.json"),
         "--data", str(net_dir), "--out", str(out), "--dry-run"],
    )

    sweep_main()

    assert "144 grid + 6 baselines x 23 windows = 3450 runs" in capsys.readouterr().out
    assert not out.exists()
