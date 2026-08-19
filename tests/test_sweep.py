# Sweep expansion and windows — SWEEP_SPEC.md T3, T4.

import copy
import datetime as dt
import re

import pytest

from sweep import Window, _window_plan, expand, windows

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
