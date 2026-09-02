"""EU_SUBSTITUTE_SPEC §8 T3 — `overlap_report.py`: the registered pairs and
carried slots are frozen, the joint period calendars respect both lines'
holidays, the OLS is exact on a constructed line, the §4.2 verdict grammar
and the §4.3 haircut pins behave at their boundaries, and a run writes the
three artefacts. Golden rows on the frozen decision root are pinned in the
freeze commit (§3.6).
"""

import datetime as dt
import json
import math
import random
from pathlib import Path

import polars as pl
import pytest

from overlap_report import (
    CARRIED, DECISION, GROSS_BASIS, LETTER, PAIRS, PERIODS, gross_root, haircuts, joint,
    period_ends, regress, verdict,
)
from overlap_report import main as overlap_main


def write_csv(data_dir: Path, symbol: str, rows) -> None:
    lines = ["time,close"] + [f"{date},{close}" for date, close in rows]
    (data_dir / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def test_the_registered_pairs_and_carried_slots_are_frozen():
    assert PAIRS == (
        ("P1", "QQQ3", "TQQQ", "MECHANICAL"),
        ("P2", "QQL3", "TQQQ", "MECHANICAL"),
        ("P3", "IB01", "BIL", "MECHANICAL"),
        ("P4", "CSPX", "SPY", "MECHANICAL"),
        ("P5", "CNDX", "QQQ", "MECHANICAL"),
        ("P6", "DBMF_EU", "DBMF", "FUNCTIONAL"),
        ("P7", "LQQ", "QQQ", "PARAMETRIC"),
        ("P8", "DBMF_EU", "KMLM", "—"),
    )
    assert CARRIED == {"P1": "TQQQ", "P3": "BIL", "P6": "DBMF"}
    assert DECISION == {"P6": "weekly"}
    assert LETTER == {"P6": "weekly"}
    assert GROSS_BASIS == {"P3"}
    assert PERIODS == {"monthly": 12, "quarterly": 4, "weekly": 52}


def test_the_gross_parent_is_the_root_name_before_its_first_net_suffix():
    assert gross_root(Path("tests/data/2026-09-02-net15-usd")) == Path("tests/data/2026-09-02")
    assert gross_root(Path("tests/data/2026-09-02-net15")) == Path("tests/data/2026-09-02")
    assert gross_root(Path("x/root")) == Path("x/root")  # its own gross basis


def test_joint_month_ends_respect_both_calendars(tmp_path):
    # 01-31 is an EU-only bar, so the joint January ends on 01-30; the final
    # row never ends a period.
    write_csv(tmp_path, "EU", [("2020-01-30", 1), ("2020-01-31", 2), ("2020-02-27", 3),
                               ("2020-02-28", 4), ("2020-03-02", 5)])
    write_csv(tmp_path, "US", [("2020-01-30", 1), ("2020-02-27", 3), ("2020-02-28", 4),
                               ("2020-03-02", 5)])
    frame = joint(tmp_path, "EU", "US")
    assert frame.columns == ["date", "eu", "us"]
    assert period_ends(frame, "monthly")["date"].to_list() == [
        dt.date(2020, 1, 30), dt.date(2020, 2, 28)
    ]


def test_quarter_ends_are_the_joint_calendars_last_bar_per_quarter():
    frame = pl.DataFrame({
        "date": [dt.date(2020, 3, 30), dt.date(2020, 3, 31), dt.date(2020, 4, 1),
                 dt.date(2020, 6, 30), dt.date(2020, 12, 31), dt.date(2021, 1, 4)],
        "eu": [1.0] * 6, "us": [1.0] * 6,
    })
    assert period_ends(frame, "quarterly")["date"].to_list() == [
        dt.date(2020, 3, 31), dt.date(2020, 6, 30), dt.date(2020, 12, 31)
    ]


def test_week_ends_follow_iso_weeks_across_the_year_boundary():
    frame = pl.DataFrame({
        "date": [dt.date(2020, 12, 30), dt.date(2020, 12, 31), dt.date(2021, 1, 4),
                 dt.date(2021, 1, 5), dt.date(2021, 1, 11)],
        "eu": [1.0] * 5, "us": [1.0] * 5,
    })
    # 2020-12-30/31 are ISO week 53 of 2020, 01-04/05 week 1 of 2021.
    assert period_ends(frame, "weekly")["date"].to_list() == [
        dt.date(2020, 12, 31), dt.date(2021, 1, 5)
    ]


def test_ols_is_exact_on_a_constructed_line():
    # log EU return = 2 x log US return + 0.001 per month, 13 returns.
    x = [0.02, -0.01, 0.03, 0.00, -0.04, 0.05, 0.01, -0.02, 0.02, 0.03, -0.03, 0.01, 0.04]
    us, eu = [100.0], [50.0]
    for r in x:
        us.append(us[-1] * math.exp(r))
        eu.append(eu[-1] * math.exp(2 * r + 0.001))
    dates = [dt.date(2020 + (m // 12), m % 12 + 1, 28) for m in range(len(us))]
    got = regress(pl.DataFrame({"date": dates, "eu": eu, "us": us}), 12)
    assert got["n"] == 13
    assert got["beta"] == pytest.approx(2.0)
    assert got["r2"] == pytest.approx(1.0)
    assert got["corr"] == pytest.approx(1.0)
    assert got["alpha_yr"] == pytest.approx(0.001 * 12 * 100)
    assert got["resid_yr"] == pytest.approx(0.0, abs=1e-9)
    diff = [r + 0.001 for r in x]  # y - x
    assert got["drift_yr"] == pytest.approx(sum(diff) / 13 * 1200)
    sums = [sum(diff[i:i + 12]) * 100 for i in range(2)]
    assert got["td_min"] == pytest.approx(min(sums))
    assert got["td_max"] == pytest.approx(max(sums))
    assert got["td_median"] == pytest.approx(sum(sums) / 2)
    worst = max(range(13), key=lambda i: abs(diff[i]))
    assert got["worst_date"] == dates[worst + 1].isoformat()
    assert got["worst_pp"] == pytest.approx(diff[worst] * 100)


def test_fewer_than_three_periods_cannot_be_regressed():
    frame = pl.DataFrame({"date": [dt.date(2020, 1, 31), dt.date(2020, 2, 28),
                                   dt.date(2020, 3, 31)],
                          "eu": [1.0, 1.1, 1.2], "us": [1.0, 1.1, 1.2]})
    with pytest.raises(ValueError, match="too few"):
        regress(frame, 12)


def stats(beta=1.0, r2=0.99, alpha=0.0, resid=0.5, corr=0.99):
    # The drag estimator under test is the drift (§4.4); the intercept is set
    # to something the bars would reject, so a wrong column choice is loud.
    return {"beta": beta, "r2": r2, "drift_yr": alpha, "alpha_yr": 99.0,
            "resid_yr": resid, "corr": corr}


@pytest.mark.parametrize("pair_id,s,expected", [
    ("P1", stats(alpha=-1.0), "PASS"),
    ("P1", stats(alpha=0.5), "PASS"),
    ("P1", stats(alpha=0.51), "FAIL"),
    ("P1", stats(alpha=-2.0), "CONDITIONAL"),
    ("P1", stats(alpha=-2.9), "CONDITIONAL"),
    ("P1", stats(alpha=-3.0), "FAIL"),
    ("P1", stats(beta=0.96, alpha=-1.0), "FAIL"),
    ("P1", stats(r2=0.979, alpha=-1.0), "FAIL"),
    ("P2", stats(alpha=-5.25), "FAIL"),
    ("P2", stats(r2=0.98, alpha=-2.5), "CONDITIONAL"),
    ("P3", stats(beta=0.4, r2=0.5, alpha=0.30, resid=0.75), "PASS"),
    ("P3", stats(alpha=-0.31), "FAIL"),
    ("P3", stats(alpha=0.1, resid=0.76), "FAIL"),
    ("P4", stats(alpha=-0.60), "PASS"),
    ("P4", stats(alpha=0.10), "PASS"),
    ("P4", stats(alpha=-0.61), "FAIL"),
    ("P4", stats(r2=0.989), "FAIL"),
    ("P5", stats(beta=1.03), "PASS"),
    ("P5", stats(beta=1.031), "FAIL"),
    ("P6", stats(corr=0.90, beta=0.8, alpha=1.5), "PROVISIONAL PASS"),
    ("P6", stats(corr=0.89), "FAIL"),
    ("P6", stats(beta=1.21), "FAIL"),
    ("P6", stats(alpha=-1.51), "FAIL"),
    ("P7", stats(beta=1.7, r2=0.8), "characterization"),
    ("P8", stats(beta=0.2, r2=0.0), "documentation"),
])
def test_verdict_grammar_on_the_drift(pair_id, s, expected):
    assert verdict(pair_id, s) == expected


def test_the_letter_reads_the_intercept():
    s = {**stats(alpha=-1.0), "alpha_yr": -1.0}
    assert verdict("P1", s, "alpha_yr") == "PASS"
    s["alpha_yr"] = -3.5
    assert verdict("P1", s, "alpha_yr") == "FAIL"


def row(pair_id, verdict, quarterly_drift, weekly_drift=0.0):
    return {"id": pair_id, "verdict": verdict,
            "monthly": {"drift_yr": 99.0},  # never the decision horizon
            "quarterly": {"drift_yr": quarterly_drift}, "weekly": {"drift_yr": weekly_drift}}


def test_haircuts_pin_minus_drift_floored_at_zero_for_carried_passing_slots_only():
    rows = [
        row("P1", "PASS", -0.6),
        row("P2", "CONDITIONAL", -2.5),      # passing but not a carried slot
        row("P3", "PASS", +0.1),             # negative drag pins h = 0
        row("P4", "PASS", -0.3),             # adoption bar, never carried
        row("P6", "PROVISIONAL PASS", -9.0, weekly_drift=-1.0),  # decides weekly
    ]
    assert haircuts(rows) == {"TQQQ": 0.6, "BIL": 0.0, "DBMF": 1.0}
    rows[0] = row("P1", "FAIL", -4.0)
    assert "TQQQ" not in haircuts(rows)


@pytest.fixture
def twin_root(tmp_path):
    # Every EU line is its US original exactly (β 1, R² 1, α 0), on two years
    # of business days, so the run exercises the whole pipeline end to end.
    rng = random.Random(0)
    day, dates = dt.date(2024, 1, 1), []
    while len(dates) < 520:
        if day.weekday() < 5:
            dates.append(day)
        day += dt.timedelta(days=1)
    for us, eu in [("TQQQ", ["QQQ3", "QQL3"]), ("BIL", ["IB01"]), ("SPY", ["CSPX"]),
                   ("QQQ", ["CNDX", "LQQ"]), ("DBMF", ["DBMF_EU"]), ("KMLM", [])]:
        closes, value = [], 100.0
        for _ in dates:
            value *= math.exp(rng.gauss(0.0003, 0.01))
            closes.append(round(value, 6))
        for symbol in [us, *eu]:
            write_csv(tmp_path, symbol, zip(map(str, dates), closes))
    return tmp_path


def test_a_run_writes_the_three_artefacts(twin_root, tmp_path):
    out = tmp_path / "out"
    overlap_main(["--data", str(twin_root), "--out", str(out)])
    payload = json.loads((out / "overlap.json").read_text())
    assert payload["root"] == twin_root.name
    assert [p["id"] for p in payload["pairs"]] == [p[0] for p in PAIRS]
    for pair in payload["pairs"][:5]:
        expected = "PASS-BY-ERRATUM" if pair["id"] == "P3" else "PASS"
        assert (pair["verdict"], pair["verdict_letter"]) == (expected, "PASS")
        assert pair["basis"] == twin_root.name  # no -net suffix: its own gross basis
        assert pair["decision_horizon"] == "quarterly" and pair["letter_horizon"] == "monthly"
        for horizon in PERIODS:
            assert pair[horizon]["beta"] == pytest.approx(1.0)
            assert pair[horizon]["r2"] == pytest.approx(1.0)
            assert pair[horizon]["drift_yr"] == pytest.approx(0.0, abs=1e-6)
    p6 = payload["pairs"][5]
    assert p6["verdict"] == "PROVISIONAL PASS"
    assert p6["decision_horizon"] == p6["letter_horizon"] == "weekly"
    assert p6["weekly"]["n"] > p6["monthly"]["n"] > p6["quarterly"]["n"]
    assert payload["haircuts"] == {"TQQQ": 0.0, "BIL": 0.0, "DBMF": 0.0}
    assert payload["pairs"][2]["net_basis"]["root"] == twin_root.name
    assert json.loads((out / "haircuts.json").read_text()) == payload["haircuts"]
    md = (out / "overlap.md").read_text()
    assert md.count("| P1 |") == 3 and md.count("| P8 |") == 3
    assert "| **PASS** |" in md and "| letter: PASS |" in md
    assert "| **PASS-BY-ERRATUM** |" in md and "P3 on `" in md
    assert "| BIL | 0.0000 |" in md


# The committed Phase-1 run on the frozen decision root (EU_SUBSTITUTE_SPEC
# §3.6, §4.4): every pair's decision-horizon row, both verdicts, and the
# haircut map, pinned from the first run and byte-compared to the artefacts.

USD = Path(__file__).parent / "data" / "2026-09-02-net15-usd"
ARTEFACTS = Path(__file__).parents[1] / "results" / "overlap_eu"
ROOT = pytest.mark.skipif(not USD.exists(), reason="the decision root is committed with the freeze")

# id: (decision horizon, n, beta, r2, drift_yr, verdict, letter verdict)
GOLDEN_ROWS = {
    "P1": ("quarterly", 54, 0.99764916, 0.98462007, -0.14206396, "PASS", "FAIL"),
    "P2": ("quarterly", 16, 1.07181571, 0.97863386, -3.77922656, "FAIL", "FAIL"),
    # P3 on its gross basis (erratum 13): IB01 against gross BIL.
    "P3": ("quarterly", 29, 1.00526208, 0.95506755, 0.09234548, "PASS-BY-ERRATUM", "PASS"),
    "P4": ("quarterly", 63, 0.97918548, 0.97942306, 0.00030675, "FAIL", "FAIL"),
    "P5": ("quarterly", 63, 1.00469251, 0.98277252, -0.13596175, "FAIL", "FAIL"),
    "P6": ("weekly", 75, 0.94648114, 0.42898342, 4.89624001, "FAIL", "FAIL"),
    "P7": ("quarterly", 80, 2.02345753, 0.98582913, 8.29159235, "characterization", "characterization"),
    "P8": ("quarterly", 5, -0.07871749, 0.01221914, 20.84556578, "documentation", "documentation"),
}


@pytest.fixture(scope="module")
def frozen():
    from overlap_report import report
    return report(USD)


@ROOT
@pytest.mark.parametrize("pair_id", list(GOLDEN_ROWS))
def test_golden_rows_on_the_frozen_root(frozen, pair_id):
    horizon, n, beta, r2, drift, verdict, letter = GOLDEN_ROWS[pair_id]
    row = next(p for p in frozen["pairs"] if p["id"] == pair_id)
    assert row["decision_horizon"] == horizon
    s = row[horizon]
    assert s["n"] == n
    assert s["beta"] == pytest.approx(beta, abs=1e-6)
    assert s["r2"] == pytest.approx(r2, abs=1e-6)
    assert s["drift_yr"] == pytest.approx(drift, abs=1e-6)
    assert (row["verdict"], row["verdict_letter"]) == (verdict, letter)


@ROOT
def test_the_monthly_letter_is_the_close_gap_and_the_quarterly_reading_recovers(frozen):
    # §4.4: monthly R² ≈ 0.95 on every LSE line, quarterly ≥ 0.98; P6's weekly
    # corr fails its bar on a 9.7 %/yr residual — a strategy difference, not
    # the gap; P3 fails the two-sided drift bar by outperforming net-15 BIL.
    p1, p3, p6 = (next(p for p in frozen["pairs"] if p["id"] == i) for i in ("P1", "P3", "P6"))
    assert p1["monthly"]["r2"] == pytest.approx(0.95451997, abs=1e-6)
    assert p1["monthly"]["alpha_yr"] == pytest.approx(1.68159075, abs=1e-6)  # attenuation bias
    assert p6["weekly"]["corr"] == pytest.approx(0.65496826, abs=1e-6)
    assert p6["weekly"]["resid_yr"] == pytest.approx(9.65936321, abs=1e-6)
    assert p6["monthly"]["n"] == 17
    # P3: gross basis passes; the pre-registered net-15 basis fails by outperforming.
    assert p3["basis"] == "2026-09-02" and frozen["gross"] == "2026-09-02"
    net = p3["net_basis"]["quarterly"]
    assert p3["net_basis"]["root"] == "2026-09-02-net15-usd"
    assert net["drift_yr"] == pytest.approx(0.48157531, abs=1e-6)
    assert net["resid_yr"] == pytest.approx(0.23682501, abs=1e-6)
    assert verdict("P3", net) == "FAIL"


@ROOT
def test_the_committed_artefacts_are_the_rounded_report(frozen):
    import results_json
    payload = results_json._round(frozen)
    assert payload == json.loads((ARTEFACTS / "overlap.json").read_text())
    assert json.loads((ARTEFACTS / "haircuts.json").read_text()) == {"BIL": 0.0, "TQQQ": 0.14206396}
    assert payload["haircuts"] == {"BIL": 0.0, "TQQQ": 0.14206396}
