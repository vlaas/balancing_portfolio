"""MONTHLY_GATE_SPEC §6 — the monthly-read gate: is the SMA-200's daily series
load-bearing?

M1 the two signals' month-end calendars on both roots, M2 the tool extension's
behaviour, M3 the anchors §4 rests on and the frozen dry-run counts, M4 the §2.4
pilot pins, M5 the consultation calendar §2.1 rests on. The gate kind, the
indicator and the grammar all exist since COMPOSITION_SPEC and no engine file is
touched by this spec, so a failure here is a data, tool or grammar regression,
never a modelling choice.
"""

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from indicators import sma, sma_monthly
from main import run_bundle
from prices import _read_close
from score_report import main as score_main
from score_report import report, signals
from spec import build_bundle

DATA = Path(__file__).parent / "data"
NET = DATA / "2026-08-24-net15"  # the decision dataset (§4.1, §4.2)
SYN = DATA / "2026-08-24-syn-net15"  # the bear era (§4.3)
RESULTS = Path(__file__).parents[1] / "results"

U = {"kind": "avg", "months": [1, 3, 6, 12]}  # COMPOSITION_SPEC's score, for M2

# §4's cost map: the blend map plus BIL at one tick.
COSTS = {"TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6,
         "QQQ": 1, "SPY": 0.7, "BIL": 0.5, "*": 6}
SMA200 = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}
SMA10M = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_months": 10}

B75K25 = {"BTAL": 0.75, "KMLM": 0.25}
B75D25 = {"BTAL": 0.75, "DBMF": 0.25}
B50K50 = {"BTAL": 0.5, "KMLM": 0.5}
SLEEVES = (("B75K25", B75K25), ("B75D25", B75D25), ("B50K50", B50K50))

LANE_2021 = "2020-12-18"
TEST_2021 = "2025-01-02"  # the 2021 lane's snapped holdout start
LANE_2019 = "2019-05-08"
TEST_2019 = "2024-01-02"  # the 2019 lane's snapped holdout start
LANE_SYN = "2000-01-03"
END_SYN = "2011-12-30"

SPY = "SPY benchmark"


def vt(safe: dict | str, gate: dict | None) -> dict:
    """The winners' coordinate: λ0.80, σ0.20, w_max 0.8 (§4.1)."""
    entry = {
        "type": "vol_target", "risk": "TQQQ", "safe": safe, "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.80}, "leverage": 3,
        "sigma_target": 0.20, "w_max": 0.8,
    }
    if gate is not None:
        entry["gate"] = gate
    return entry


def bundle(start: str, entries: list[dict], end: str | None = None) -> dict:
    config = {"start": start, "initial_capital": 10000, "monthly_contribution": 500,
              "cost_bps": COSTS, "cash_yield": 0.03}
    if end is not None:
        config["end"] = end
    return {
        "schema_version": 1,
        "config": config,
        "strategies": entries + [{"type": "fixed", "label": SPY, "weights": {"SPY": 1.0}}],
    }


def run(spec: dict, data_dir: Path) -> dict:
    return {r.label: r for r in run_bundle(build_bundle(spec), data_dir)}


def label(safe: str, gate: str = "") -> str:
    return f"VT TQQQ/{safe} t20 w0-80 QQQ:VOL_EWMA80{gate}"


# The three gate arms of every lane, in §4's grid order.
ARMS = ((""), (" gate QQQ<SMA200"), (" gate QQQ<SMA10M"))
SAFE_STR = {"B75K25": "BTAL75+KMLM25", "B75D25": "BTAL75+DBMF25",
            "B50K50": "BTAL50+KMLM50"}

# Each lane run whole, so every arm is measured against the lane's own traded
# set — exactly what the sweep of §4 does, window by window.
ROSTER_2021 = [vt(safe, gate) for _, safe in SLEEVES for gate in (None, SMA200, SMA10M)]
ROSTER_2019 = [vt(B75D25, gate) for gate in (None, SMA200, SMA10M)]
ROSTER_SYN = [vt("BIL", gate) for gate in (None, SMA200, SMA10M)]


@pytest.fixture(scope="module")
def lane_2021():
    return run(bundle(LANE_2021, ROSTER_2021), NET)


@pytest.fixture(scope="module")
def holdout_2021():
    return run(bundle(TEST_2021, ROSTER_2021), NET)


@pytest.fixture(scope="module")
def lane_2019():
    return run(bundle(LANE_2019, ROSTER_2019), NET)


@pytest.fixture(scope="module")
def holdout_2019():
    return run(bundle(TEST_2019, ROSTER_2019), NET)


@pytest.fixture(scope="module")
def lane_syn():
    return run(bundle(LANE_SYN, ROSTER_SYN, end=END_SYN), SYN)


# --- M1 — the calendars, through the tool's machinery (§2.2) -----------------

# root, start, end, month-ends, SMA200 (closed, changes), SMA10M (closed,
# changes), both, the SMA10M-only dates. §2.2's table, measured on this clone.
CALENDARS = (
    ("net15", NET, dt.date(2012, 1, 3), None,
     175, (27, 20), (29, 24), 27, ("2016-06-30", "2019-05-31")),
    ("syn-net15", SYN, dt.date(2000, 1, 3), dt.date(2011, 12, 30),
     144, (60, 27), (62, 27), 60, ("2005-03-31", "2011-11-30")),
)


def gate_calendar(root: Path, start: dt.date, end: dt.date | None) -> pl.DataFrame:
    return signals(root, "QQQ", None, 0.0, start, end, 200, 10)


@pytest.mark.parametrize(
    "name,root,start,end,count,daily,monthly,both,only",
    CALENDARS, ids=[row[0] for row in CALENDARS],
)
def test_m1_the_two_signals_month_end_calendars(
    name, root, start, end, count, daily, monthly, both, only
):
    from score_report import state_changes

    ends = gate_calendar(root, start, end)

    assert len(ends) == count
    assert (int(ends["sma_off"].sum()), state_changes(ends["sma_off"].to_list())) == daily
    assert (int(ends["score_off"].sum()), state_changes(ends["score_off"].to_list())) == monthly
    assert int((ends["sma_off"] & ends["score_off"]).sum()) == both
    # The daily read never closes alone on either root (§2.2).
    assert int((ends["sma_off"] & ~ends["score_off"]).sum()) == 0
    monthly_only = ends.filter(~pl.col("sma_off") & pl.col("score_off"))
    assert tuple(str(d) for d in monthly_only["date"]) == only


@pytest.mark.parametrize(
    "name,root,start,end", [row[:4] for row in CALENDARS], ids=[row[0] for row in CALENDARS]
)
def test_m1_the_monthly_signal_closes_a_strict_superset(name, root, start, end):
    ends = gate_calendar(root, start, end)

    # SMA200-closed => SMA10M-closed, month-end by month-end.
    assert not (ends["sma_off"] & ~ends["score_off"]).any()
    assert (ends["score_off"] & ~ends["sma_off"]).any()


def test_m1_every_2022_month_end_is_closed_by_both():
    ends = gate_calendar(NET, dt.date(2012, 1, 3), None)
    y2022 = ends.filter(pl.col("date").dt.year() == 2022)

    assert len(y2022) == 12
    assert int(y2022["sma_off"].sum()) == 12
    assert int(y2022["score_off"].sum()) == 12


# --- M2 — the tool extension (§5) -------------------------------------------

# A root whose two signals disagree in both directions on a two-bar window: the
# daily SMA closes alone at 2020-05-29 (a spike two days before), the monthly
# one alone at 2020-06-30. The final row is never a month-end.
FIXTURE = (
    ("2020-01-30", 10.0), ("2020-01-31", 10.0),
    ("2020-02-27", 10.0), ("2020-02-28", 8.0),
    ("2020-03-30", 8.0), ("2020-03-31", 12.0),
    ("2020-04-29", 12.0), ("2020-04-30", 9.0),
    ("2020-05-28", 20.0), ("2020-05-29", 10.4),
    ("2020-06-29", 10.0), ("2020-06-30", 10.2),
    ("2020-07-01", 10.2),
)


def write_csv(data_dir: Path, symbol: str, rows) -> None:
    lines = ["time,close"] + [f"{date},{close}" for date, close in rows]
    (data_dir / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def fixture_root(tmp_path: Path) -> Path:
    write_csv(tmp_path, "A", FIXTURE)
    return tmp_path


def fixture_report(tmp_path: Path) -> str:
    return report(fixture_root(tmp_path), "A", None, 0.0, dt.date(2020, 1, 30), None, 2, 2)


def test_m2_exactly_one_comparison_side_is_required(tmp_path):
    root = str(fixture_root(tmp_path))

    with pytest.raises(SystemExit):
        score_main(["--data", root])
    with pytest.raises(SystemExit):
        score_main(["--data", root, "--score", "{}", "--sma-months", "2"])


def test_m2_the_comparison_side_is_the_gates_own_indicator():
    # The factory `strategies/gate.py` uses, and its name (§5).
    indicator = sma_monthly(10)
    assert indicator.name == "SMA10M"

    frame = _read_close(NET, "QQQ")
    want = frame.with_columns(value=indicator.fn(frame))
    ends = gate_calendar(NET, dt.date(2012, 1, 3), None)
    got = ends.join(want.select("date", "value"), on="date")

    assert got["score"].to_list() == got["value"].to_list()


def test_m2_the_fixture_roots_contingency_and_disagreements(tmp_path):
    text = fixture_report(tmp_path)

    assert "# Gate calendar: A<SMA2M vs A<SMA2" in text
    assert "- month-ends in the window: 6, last 2020-06-30" in text
    assert "- A<SMA2M: 3, state changes 5" in text
    assert "- A<SMA2: 3, state changes 4" in text
    assert "| window | both | SMA2 only | SMA2M only | neither |" in text
    assert "| full | 2 | 1 | 1 | 2 |" in text
    assert "| 2022 | 0 | 0 | 0 | 0 |" in text
    # The disagreement rows carry the close and both SMA values (§5).
    assert "| date | closed by | close | SMA2 | SMA2M |" in text
    assert "| 2020-05-29 | SMA2 only | 10.4000 | 15.2000 | 9.7000 |" in text
    assert "| 2020-06-30 | SMA2M only | 10.2000 | 10.1000 | 10.3000 |" in text


def test_m2_the_sma_months_report_drops_the_threshold_ladder(tmp_path):
    assert "## Threshold ladder" not in fixture_report(tmp_path)
    assert "## Threshold ladder" in report(
        fixture_root(tmp_path), "A", {"months": 1}, 0.0, dt.date(2020, 1, 30), None, 2
    )


@pytest.mark.parametrize(
    "entry,name",
    [(U, "score_report_u.md"), ({"months": 12}, "score_report_12m.md")],
    ids=["u", "12m"],
)
def test_m2_the_score_mode_output_is_byte_unchanged(entry, name):
    # The extension may not move a single byte of the committed reports (§5).
    got = report(NET, "QQQ", entry, 0.0, dt.date(2012, 1, 3), None, 200)

    assert got == (RESULTS / name).read_text()


# --- M3 — the anchors §4 rests on (§2.3) ------------------------------------

# The committed rows of `results/sweep_comp_2021`, `_2019` and `sweep_syn_2000`,
# full-window Calmar. A mismatch is a bug in this change, not data drift (§9.0).
ANCHORS_2021 = {
    "B75K25": (0.83354496, 0.85294307),
    "B75D25": (0.81272474, 0.85739876),
    "B50K50": (0.81407574, 0.88489974),
}


@pytest.mark.parametrize("name", ANCHORS_2021, ids=list(ANCHORS_2021))
def test_m3_the_2021_anchors_reproduce(name, lane_2021):
    plain, gated = ANCHORS_2021[name]
    safe = SAFE_STR[name]

    assert round(lane_2021[label(safe)].stats["calmar"], 8) == plain
    assert round(lane_2021[label(safe, " gate QQQ<SMA200")].stats["calmar"], 8) == gated


def test_m3_the_2021_holdout_anchors_reproduce(holdout_2021):
    tests = {"B75K25": 0.84701986, "B75D25": 0.88253297, "B50K50": 1.16742198}

    for name, want in tests.items():
        row = holdout_2021[label(SAFE_STR[name], " gate QQQ<SMA200")]
        assert round(row.stats["calmar"], 8) == want


def test_m3_the_2019_anchors_reproduce(lane_2019, holdout_2019):
    safe = SAFE_STR["B75D25"]

    assert round(lane_2019[label(safe)].stats["calmar"], 8) == 0.93984909
    assert round(lane_2019[label(safe, " gate QQQ<SMA200")].stats["calmar"], 8) == 0.93621129
    assert round(holdout_2019[label(safe, " gate QQQ<SMA200")].stats["calmar"], 8) == 0.91868785


def test_m3_the_synthetic_anchor_reproduces(lane_syn):
    assert round(lane_syn["VT TQQQ/BIL t20 w0-80 QQQ:VOL_EWMA80"].stats["calmar"], 8) == 0.0103309
    gated = lane_syn["VT TQQQ/BIL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA200"]
    assert round(gated.stats["calmar"], 8) == 0.10460356


# --- M4 — the pilot pins (§2.4) ---------------------------------------------

FIELDS = ("calmar", "cagr", "max_drawdown", "turnover")


@pytest.mark.parametrize("name", [n for n, _ in SLEEVES], ids=[n for n, _ in SLEEVES])
@pytest.mark.parametrize("window", ["full", "test"])
def test_m4_the_2021_twins_are_identical(name, window, lane_2021, holdout_2021):
    # §2.1's consultation calendar in its sharpest form: the 2021 lane's two
    # signals agree on every month-end and every window start, so the twins are
    # the same portfolio (§10.5).
    rows = lane_2021 if window == "full" else holdout_2021
    daily = rows[label(SAFE_STR[name], " gate QQQ<SMA200")].stats
    monthly = rows[label(SAFE_STR[name], " gate QQQ<SMA10M")].stats

    for field in FIELDS:
        assert monthly[field] == pytest.approx(daily[field], abs=1e-8)


def test_m4_the_2019_twin_pins(lane_2019, holdout_2019):
    safe = SAFE_STR["B75D25"]
    full = lane_2019[label(safe, " gate QQQ<SMA10M")].stats

    assert round(full["calmar"], 8) == 0.92721074
    assert round(full["cagr"], 8) == 0.18649453
    assert round(full["max_drawdown"], 8) == -0.20113499
    # The holdout window's calendar agrees everywhere: bit-identical (§2.4).
    assert round(holdout_2019[label(safe, " gate QQQ<SMA10M")].stats["calmar"], 8) == 0.91868785


def test_m4_the_synthetic_twin_pins(lane_syn):
    stats = lane_syn["VT TQQQ/BIL t20 w0-80 QQQ:VOL_EWMA80 gate QQQ<SMA10M"].stats

    assert round(stats["calmar"], 8) == 0.10525207
    assert round(stats["cagr"], 8) == 0.03774067
    assert round(stats["max_drawdown"], 8) == -0.35857411


# --- M5 — the consultation calendar (§2.1) ----------------------------------

# Q's two month-end closes before the window are both 10, so the carried SMA2M
# is 10 on the non-month-end deployment day; the day's own close decides.
DEPLOY_DATES = ("2020-01-30", "2020-01-31", "2020-02-27", "2020-02-28",
                "2020-03-02", "2020-03-03", "2020-03-31", "2020-04-01")


def deployment_root(tmp_path: Path, deploy_close: float) -> Path:
    write_csv(tmp_path, "Q", list(zip(DEPLOY_DATES,
                                      [10.0, 10.0, 10.0, 10.0, deploy_close, 10.0, 10.0, 10.0])))
    write_csv(tmp_path, "R", list(zip(DEPLOY_DATES,
                                      [100.0, 100.0, 100.0, 100.0, 100.0, 98.0, 99.0, 101.0])))
    write_csv(tmp_path, "S", list(zip(DEPLOY_DATES,
                                      [50.0, 50.0, 50.0, 50.0, 50.0, 49.0, 50.0, 51.0])))
    return tmp_path


@pytest.mark.parametrize(
    "deploy_close,held", [(9.0, False), (11.0, True)], ids=["closed", "open"]
)
def test_m5_the_gate_is_consulted_on_the_deployment_day(tmp_path, deploy_close, held):
    spec = {
        "schema_version": 1,
        "config": {"start": "2020-03-02", "initial_capital": 10000,
                   "monthly_contribution": 500},
        "strategies": [
            {"type": "fixed", "weights": {"R": 0.5, "S": 0.5},
             "gate": {"symbol": "Q", "assets": ["R"], "sma_months": 2}},
            {"type": "fixed", "label": "S bench", "weights": {"S": 1.0}},
        ],
    }
    results = run_bundle(build_bundle(spec), deployment_root(tmp_path, deploy_close))

    allocations = results[0].allocations
    day_one = allocations.filter(
        (pl.col("date") == dt.date(2020, 3, 2)) & (pl.col("asset") == "R")
    )
    assert len(day_one) == 1
    assert (day_one["actual"][0] > 0) is held


def test_m5_the_synthetic_lane_has_a_start_date_disagreement():
    # 2005-07-05, the snapped 2005-07-03 sensitivity start: the daily SMA has
    # crossed intramonth, the carried month-end value has not. No month-end
    # report can show it (§2.2, §12).
    frame = _read_close(SYN, "QQQ")
    frame = frame.with_columns(daily=sma(200).fn(frame), monthly=sma_monthly(10).fn(frame))
    row = frame.filter(pl.col("date") == dt.date(2005, 7, 5)).row(0, named=True)

    assert row["close"] < row["daily"]
    assert not row["close"] < row["monthly"]


# Every window start of §4.1 and §4.2 — the full/fit start, the sensitivity
# starts and the snapped holdout start — read off the lanes they copy.
STARTS_2021 = ("2020-12-18", "2021-06-18", "2021-12-20", "2022-06-21",
               "2022-12-19", "2023-06-20", "2025-01-02")
STARTS_2019 = ("2019-05-08", "2019-11-08", "2020-05-08", "2020-11-09", "2021-05-10",
               "2021-11-08", "2022-05-09", "2022-11-08", "2023-05-08", "2024-01-02")


@pytest.mark.parametrize("start", STARTS_2021 + STARTS_2019)
def test_m5_every_lane_window_start_carries_agreeing_flags(start):
    frame = _read_close(NET, "QQQ")
    frame = frame.with_columns(daily=sma(200).fn(frame), monthly=sma_monthly(10).fn(frame))
    row = frame.filter(pl.col("date") == dt.date.fromisoformat(start)).row(0, named=True)

    assert (row["close"] < row["daily"]) == (row["close"] < row["monthly"])
