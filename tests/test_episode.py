"""EPISODE_SPEC §6 — episode attribution: which episodes a sleeve component
earns, and which it pays for.

A1 the seven-window table is frozen, A2 slicing is exact, A3 the 2012
attribution pins, A4 the 2021 attribution pins, A5 the partition pins on the
committed 2012 sweep, A6 the winners' deepest hole is E4 (or E6 with E4 second),
A7 no living document names the old winners-file path. No engine file is touched
by this spec, so a failure in A3–A6 is a tool bug or a data regression, never a
modelling choice.
"""

import datetime as dt
import json
from pathlib import Path

import polars as pl
import pytest

from episode_report import (
    EPISODES,
    bundle_report,
    episode_rows,
    episode_slice,
    sens_rows,
    split,
    split_by_trough,
)
from sweep import main as sweep_main

GOLDEN_DIR = Path(__file__).parent / "data"
NET = GOLDEN_DIR / "2026-08-24-net15"
SPECS = Path(__file__).parents[1] / "specs"
RESULTS = Path(__file__).parents[1] / "results"
DOCS = Path(__file__).parents[1] / "docs"
ROOT = Path(__file__).parents[1]


# --- A1 — the table is frozen (§3) ------------------------------------------

# The §3 table verbatim. A refresh of the committed `drawdowns` would move these
# dates, and the spec's contract is that such a move is a visible spec change.
FROZEN = (
    ("E1", "grind-2015", "2014-11-28", "2015-08-25", "2017-02-07"),
    ("E2", "2018-Q4", "2018-08-31", "2019-06-03", "2019-12-16"),
    ("E3", "COVID", "2020-02-19", "2020-03-23", "2020-07-06"),
    ("E4", "anti-beta unwind", "2020-09-02", "2021-03-08", "2021-09-03"),
    ("E5", "2022 grind", "2021-11-19", "2023-03-10", "2023-06-15"),
    ("E6", "tariff", "2024-07-10", "2025-04-08", "2025-10-01"),
    ("E7", "2025-10", "2025-10-29", "2026-03-27", "2026-08-24"),
)


def test_a1_the_episode_table_is_the_seven_frozen_windows():
    assert EPISODES == FROZEN
    assert len(EPISODES) == 7


@pytest.mark.parametrize("episode", EPISODES, ids=[e[0] for e in EPISODES])
def test_a1_every_trough_lies_inside_its_own_window(episode):
    _, _, peak, trough, recovery = episode
    assert peak < trough < recovery


def test_a1_the_windows_are_in_date_order():
    peaks = [peak for _, _, peak, _, _ in EPISODES]
    assert peaks == sorted(peaks)


# --- A2 — slicing is exact ---------------------------------------------------

# A hand-valued index: the running peak is 1.0, 1.10, 1.10, 1.20, 1.20, 1.32, so
# the two 10 % falls are the only drawdown the window can see.
HAND = pl.DataFrame(
    {
        "date": [dt.date(2020, 1, d) for d in (1, 2, 3, 6, 7, 8)],
        "index": [1.0, 1.10, 0.99, 1.20, 1.08, 1.32],
    }
)


@pytest.mark.parametrize(
    "start,end,ret,drawdown",
    [
        ("2020-01-01", "2020-01-08", 0.32, -0.1),          # the whole curve
        ("2020-01-03", "2020-01-07", 1.08 / 0.99 - 1, -0.1),  # from a trough
        ("2019-12-01", "2020-01-02", 0.10, 0.0),           # peak before the first bar
        ("2020-01-06", "2020-01-08", 0.10, -0.1),          # a peak inside the fall
    ],
    ids=["full", "trough-to-trough", "before-first-bar", "inside"],
)
def test_a2_episode_slicing_equals_the_hand_values(start, end, ret, drawdown):
    assert episode_slice(HAND, start, end) == (
        pytest.approx(ret, abs=1e-12),
        pytest.approx(drawdown, abs=1e-12),
    )


@pytest.mark.parametrize(
    "start,end",
    [("2020-01-08", "2020-01-08"), ("2021-01-01", "2021-06-01"), ("2019-01-01", "2019-06-01")],
    ids=["one-bar", "after-the-curve", "before-the-curve"],
)
def test_a2_a_window_with_fewer_than_two_bars_yields_none(start, end):
    assert episode_slice(HAND, start, end) == (None, None)


# --- A3 — the 2012 attribution pins (§6, §11) --------------------------------


def marginals(rows, baseline):
    """{row name: {episode id: (return pp, drawdown pp)}} against `baseline`.

    `None` where either side has fewer than two bars in the window — the 2021
    lane starts 2020-12-18 and so has no E1, E2 or E3.
    """
    cells = {name: c for name, _, c in rows}
    base = cells[baseline]

    def delta(value, floor):
        return None if value is None or floor is None else 100 * (value - floor)

    return {
        name: {
            eid: (delta(c[eid][0], base[eid][0]), delta(c[eid][1], base[eid][1]))
            for eid, *_ in EPISODES
        }
        for name, c in cells.items()
        if name != baseline
    }


# §6 A3: pure BTAL's marginal against BIL on the 2012 lane, and the half-swap's
# two decisive cells. E4 alone (-27.0 / -10.7) outweighs every bear together.
A3 = {
    "BTAL": {
        "E1": (-0.4, +5.3), "E2": (+1.5, +2.3), "E3": (+5.1, +5.7),
        "E4": (-27.0, -10.7), "E5": (+8.2, +9.1), "E6": (-11.1, +5.1),
        "E7": (-9.3, -0.8),
    },
    "BIL50+BTAL50": {"E4": (-14.0, -2.9), "E5": (+4.4, +5.6)},
}


@pytest.fixture(scope="module")
def lane_2012():
    return episode_rows(SPECS / "cash_points_2012.json", NET, sigma=0.20, w_max=0.8)


def test_a3_the_2012_panel_is_the_five_sleeves_at_the_winners_coordinate(lane_2012):
    assert [name for name, *_ in lane_2012] == [
        "BTAL", "BIL25+BTAL75", "BIL50+BTAL50", "BIL75+BTAL25", "BIL", "SPY benchmark"
    ]


A3_CELLS = [(s, e) for s, cells in A3.items() for e in cells]


@pytest.mark.parametrize(
    "sleeve,episode", A3_CELLS, ids=[f"{s}-{e}" for s, e in A3_CELLS]
)
def test_a3_the_2012_marginals_against_bil_reproduce(lane_2012, sleeve, episode):
    ret, drawdown = marginals(lane_2012, "BIL")[sleeve][episode]
    want_ret, want_drawdown = A3[sleeve][episode]
    assert ret == pytest.approx(want_ret, abs=0.2)
    assert drawdown == pytest.approx(want_drawdown, abs=0.2)


def test_a3_the_rendered_report_cites_the_table_by_id_and_window():
    text = bundle_report(SPECS / "cash_points_2012.json", NET, "BIL", 0.20, 0.8)
    for eid, _, peak, trough, recovery in EPISODES:
        assert f"| {eid} |" in text
        assert f"{peak} → {recovery} | {trough} |" in text
    # The marginal table's own §11 row, so the rendering is pinned beside the numbers.
    assert "| `BTAL` | -0.4 / +5.3 | +1.5 / +2.3 | +5.1 / +5.7 | -27.0 / -10.7 |" in text


# --- A4 — the 2021 attribution pins (§6, §11) --------------------------------

# §6 A4, (marginal return pp, marginal drawdown pp) against BIL on the 2021 lane;
# `None` where the spec pins only one of the two. The winners' 2022 is mostly
# KMLM's (+16.5 against BTAL's +8.3) while its drawdown is BTAL's (+8.5 against
# +5.8), and the blend beats both components (+11.0).
A4 = {
    ("BTAL", "E4"): (-11.6, -7.4),
    ("KMLM", "E4"): (+8.8, +3.9),
    ("DBMF", "E4"): (+10.0, +2.9),
    ("BTAL", "E5"): (+8.3, +8.5),
    ("KMLM", "E5"): (+16.5, +5.8),
    ("DBMF", "E5"): (+8.2, +5.2),
    ("BTAL75+KMLM25", "E5"): (None, +11.0),
    ("BTAL", "E6"): (-11.2, None),
    ("KMLM", "E6"): (-10.7, None),
    ("DBMF", "E6"): (-7.3, None),
}


@pytest.fixture(scope="module")
def lane_2021():
    return episode_rows(SPECS / "episode_points_2021.json", NET)


def test_a4_the_2021_panel_is_the_components_at_25_50_and_100_plus_the_winners(lane_2021):
    assert [name for name, *_ in lane_2021] == [
        "BIL",
        "BIL75+BTAL25", "BIL50+BTAL50",
        "BIL75+KMLM25", "BIL50+KMLM50",
        "BIL75+DBMF25", "BIL50+DBMF50",
        "BTAL", "KMLM", "DBMF",
        "BTAL75+KMLM25", "BTAL75+DBMF25", "BTAL50+KMLM50",
        "SPY benchmark",
    ]


@pytest.mark.parametrize("key", A4, ids=[f"{s}-{e}" for s, e in A4])
def test_a4_the_2021_marginals_against_bil_reproduce(lane_2021, key):
    sleeve, episode = key
    ret, drawdown = marginals(lane_2021, "BIL")[sleeve][episode]
    want_ret, want_drawdown = A4[key]

    if want_ret is not None:
        assert ret == pytest.approx(want_ret, abs=0.2)
    if want_drawdown is not None:
        assert drawdown == pytest.approx(want_drawdown, abs=0.2)


def test_a4_the_e5_drawdown_benefit_of_the_blend_beats_both_its_components(lane_2021):
    # Complementarity at the episode level (§11 prediction 3): the sleeve buys
    # more 2022 drawdown than either arm alone does.
    cells = marginals(lane_2021, "BIL")
    blend = cells["BTAL75+KMLM25"]["E5"][1]
    assert blend > cells["BTAL"]["E5"][1]
    assert blend > cells["KMLM"]["E5"][1]


# The §5.2 lane's frozen size, measured by --dry-run before it is run (§9 step 0).
def test_a4_the_three_year_lane_dry_runs_to_its_frozen_count(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(SPECS / "sweep_episode_2012.json"),
         "--data", str(NET), "--out", str(out), "--dry-run"],
    )
    sweep_main()
    assert "5 grid + 1 baselines x 27 windows = 162 runs" in capsys.readouterr().out
    assert not out.exists()


# --- A5 — the partition pins on the committed 2012 sweep (§2.2, §6) ----------

SWEEP_2012 = "results/sweep_cash_2012/runs.json"
PURE_BTAL = "VT TQQQ/BTAL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
HALF_SWAP = "VT TQQQ/BIL50+BTAL50 t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"

# §6 A5: (windows with the trough, B's Calmar wins, B shallower),
#        (windows without, B's Calmar wins, B shallower). E4 partitions perfectly.
A5 = {
    "E4": ((10, 10, 10), (10, 2, 0)),
    "E5": ((7, 7, 6), (13, 5, 4)),
    "E3": ((10, 9, 8), (10, 3, 2)),
}


@pytest.mark.parametrize("episode", A5, ids=list(A5))
def test_a5_the_2012_partition_reproduces(episode):
    runs = json.loads((ROOT / SWEEP_2012).read_text())
    a, b = sens_rows(runs, PURE_BTAL), sens_rows(runs, HALF_SWAP)
    trough = next(t for eid, _, _, t, _ in EPISODES if eid == episode)
    inside, outside = split_by_trough(a, trough)

    for windows, want in zip((inside, outside), A5[episode]):
        n, calmar, shallower, _, _ = split(a, b, windows)
        assert (n, calmar, shallower) == want


# --- A6 — the winners' deepest hole is E4 (§6, §10.2(c)) ---------------------

WINNERS = ("BTAL75+KMLM25", "BTAL75+DBMF25", "BTAL50+KMLM50")


@pytest.mark.parametrize("sleeve", WINNERS, ids=WINNERS)
def test_a6_each_winners_deepest_drawdown_is_its_full_window_floor(sleeve):
    panel = json.loads((RESULTS / "cash_points_2021.json").read_text())
    runs = json.loads((RESULTS / "sweep_cash_2021" / "runs.json").read_text())
    label = f"VT TQQQ/{sleeve} t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"

    deepest = next(s for s in panel["strategies"] if s["label"] == label)["drawdowns"][0]
    full = next(r for r in runs if r["kind"] == "full" and r["label"] == label)
    assert 100 * deepest["depth"] == pytest.approx(100 * full["max_drawdown"], abs=0.01)


# E4 is the deepest for the two BTAL-75 winners; for B50K50 it is E6, with E4
# second at -16.12 % — the "-16.1" of §6 A6's parenthetical, which quotes the
# winners' E4 depths against their deepest-drawdown depths. Pinned per winner as
# measured: (deepest, second).
DEEPEST = {
    "BTAL75+KMLM25": ("E4", "E6"),
    "BTAL75+DBMF25": ("E4", "E6"),
    "BTAL50+KMLM50": ("E6", "E4"),
}

# §6 A6's "-19.1 / -19.1 / -16.1": each winner's E4 depth in the 2021 panel.
E4_DEPTH = {"BTAL75+KMLM25": -19.06, "BTAL75+DBMF25": -19.07, "BTAL50+KMLM50": -16.12}


@pytest.mark.parametrize("sleeve", WINNERS, ids=WINNERS)
def test_a6_the_winners_deepest_hole_is_e4_or_e4_is_second(sleeve):
    panel = json.loads((RESULTS / "cash_points_2021.json").read_text())
    label = f"VT TQQQ/{sleeve} t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"
    drawdowns = next(s for s in panel["strategies"] if s["label"] == label)["drawdowns"]

    troughs = {t: eid for eid, _, _, t, _ in EPISODES}
    assert tuple(troughs.get(d["trough"]) for d in drawdowns[:2]) == DEEPEST[sleeve]
    assert "E4" in DEEPEST[sleeve]

    e4 = next(d for d in drawdowns if troughs.get(d["trough"]) == "E4")
    assert 100 * e4["depth"] == pytest.approx(E4_DEPTH[sleeve], abs=0.01)


# --- A7 — living documents do not name the old winners-file path (§7.2) ------

# An explicit allowlist, not a glob: these are the documents that are still
# edited. A new living document is added here when it is created; a spec never
# is — a spec is frozen from its pre-registration commit and its stale names are
# annotated by its own errata, not fixed (§7.2).
LIVING = (
    "docs/HANDOFF_COMPOSITION.md",
    "docs/ARCHITECTURE.md",
    "docs/STRATEGY_DEVELOPMENT.md",
    "docs/DECLARATIVE_SPEC.md",
    "CLAUDE.md",
    "README.md",
)


@pytest.mark.parametrize("name", LIVING, ids=LIVING)
def test_a7_no_living_document_names_the_old_winners_file(name):
    # The new name does not contain the literal, so no "unless followed by"
    # clause and no section-skipping is needed.
    assert "WINNING_STRATEGIES.md" not in (ROOT / name).read_text()


def test_a7_the_winners_file_and_its_stub_both_exist():
    assert (DOCS / "WINNING_STRATEGIES_CASH_SLEEVE.md").exists()

    stub = DOCS / "WINNING_STRATEGIES.md"
    assert stub.exists()
    lines = stub.read_text().strip().splitlines()
    assert len(lines) <= 3
    assert "WINNING_STRATEGIES_CASH_SLEEVE.md" in stub.read_text()
