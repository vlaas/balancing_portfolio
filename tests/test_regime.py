# regime_report.py — REGIME_SPEC §6 function tests, the R4 real-data pins,
# and the R10 anchors through the new code path.

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from main import collect_indicators, run_bundle
from prices import load_prices
from regime_report import episodes, month_ends, report, signal_frame
from simulate import simulate
from spec import build_bundle

NET_DIR = Path(__file__).parent / "data" / "2026-08-20-net15"


def write_csv(data_dir: Path, symbol: str, rows: list[tuple]) -> None:
    lines = ["time,close"] + [f"{date},{close}" for date, close in rows]
    (data_dir / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def test_episodes_are_consecutive_risk_off_runs():
    assert episodes([]) == []
    assert episodes([None, 0.0, 1.0, 1.0, 0.0, 1.0]) == [2, 1]
    assert episodes([1.0, 1.0, 1.0]) == [3]
    assert episodes([0.0, None, 0.0]) == []


def test_month_ends_follow_the_rebalance_day_rule():
    frame = pl.DataFrame(
        {
            "date": [dt.date(2020, 1, 30), dt.date(2020, 1, 31),
                     dt.date(2020, 2, 3), dt.date(2020, 2, 28), dt.date(2020, 3, 2)],
            "close": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    # 01-31 and 02-28 end their months; the final row never does.
    assert month_ends(frame)["date"].to_list() == [
        dt.date(2020, 1, 31), dt.date(2020, 2, 28),
    ]


DATES = ["2020-01-30", "2020-01-31", "2020-02-03", "2020-02-28", "2020-03-02"]


def synthetic_root(tmp_path: Path) -> Path:
    # Ratio path (B = 1) crossing the 1.00/0.95 band; A has one extra date the
    # denominator lacks; Q closes below its 2-day SMA on both month-ends.
    a_rows = list(zip(DATES, [0.9, 1.05, 0.96, 0.9, 1.1]))
    a_rows.insert(3, ("2020-02-04", 7.0))  # host-only day, off every calendar
    write_csv(tmp_path, "A", a_rows)
    write_csv(tmp_path, "B", [(date, 1.0) for date in DATES])
    write_csv(tmp_path, "Q", list(zip(DATES, [10.0, 9.0, 10.0, 8.0, 10.0])))
    return tmp_path


def test_signal_frame_is_the_joint_calendar(tmp_path):
    frame = signal_frame(synthetic_root(tmp_path), "A", "B", 1, 1.00, 0.05)

    assert frame["date"].to_list() == [dt.date.fromisoformat(d) for d in DATES]
    assert frame["ratio"].to_list() == [0.9, 1.05, 0.96, 0.9, 1.1]
    assert frame["off"].to_list() == [0.0, 1.0, 1.0, 0.0, 1.0]


def test_report_counts_on_a_synthetic_root(tmp_path):
    text = report(
        synthetic_root(tmp_path), "A", "B", 1, 1.00, 0.05,
        start=dt.date(2020, 1, 30), end=None, sma_symbol="Q", sma_days=2,
    )

    assert "- window: 2020-01-30 -> 2020-03-02, 5 joint days" in text
    assert "- A-only rows in the window: 1, on Q's calendar: 0" in text
    assert "- risk-off: 3 of 5 (60.0%)" in text
    assert "- episodes: 2, mean length 1.5 days" in text
    assert "- month-ends in the window: 2, risk-off: 1" in text
    assert "| 2020 | 2 | 1 |" in text
    # 01-31: both off; 02-28: SMA only (Q 8 < SMA 9, regime released).
    assert "| full | 1 | 1 | 0 | 0 |" in text
    assert "| 2022 | 0 | 0 | 0 | 0 |" in text


# --- R4: real-data pins on the net snapshot (VIX files byte-equal in both) ---


def net_report(n: int, fire: float, hysteresis: float) -> str:
    return report(
        NET_DIR, "VIX", "VIX3M", n, fire, hysteresis,
        start=dt.date(2012, 1, 3), end=None, sma_symbol="QQQ", sma_days=200,
    )


def test_r4_calendar_and_the_research_default():
    text = net_report(10, 1.00, 0.05)

    assert "- VIX: 1990-01-03 -> 2026-08-21 (9246 rows)" in text
    assert "(4671 joint rows, full intersection)" in text
    assert "- window: 2012-01-03 -> 2026-08-20, 3679 joint days" in text
    assert "- VIX-only rows in the window: 22, on QQQ's calendar: 0" in text
    assert "- risk-off: 305 of 3679 (8.3%)" in text
    assert "- month-ends in the window: 175, risk-off: 13" in text
    # QQQ<SMA200 closes 27 month-ends on the net series (the gross root gives
    # 25); the 2022 line is the research's falsification criterion: 0 of 12.
    assert "| full | 9 | 18 | 4 | 144 |" in text
    assert "| 2022 | 0 | 12 | 0 | 0 |" in text


def test_r4_raw_ratio_and_low_threshold():
    raw = net_report(1, 1.00, 0.0)
    assert "- risk-off: 249 of 3679 (6.8%)" in raw
    assert "- month-ends in the window: 175, risk-off: 13" in raw
    assert "| full | 7 | 20 | 6 | 142 |" in raw
    assert "| 2022 | 12 | 2 |" in raw  # per-year line: 2 of 12 month-ends off

    low = net_report(10, 0.95, 0.05)
    assert "- risk-off: 964 of 3679 (26.2%)" in low
    assert "- month-ends in the window: 175, risk-off: 44" in low
    assert "| full | 20 | 7 | 24 | 124 |" in low
    assert "| 2022 | 12 | 7 |" in low


SPOTS = {  # date -> (raw ratio, 10-day SMA), REGIME_SPEC R4
    "2020-01-31": (1.011, 0.920),
    "2020-02-28": (1.344, 1.074),
    "2022-02-28": (1.017, 0.974),
    "2022-04-29": (1.006, 0.926),
    "2025-03-31": (1.014, 0.952),
}


def test_r4_spot_values():
    frame = signal_frame(NET_DIR, "VIX", "VIX3M", 10, 1.00, 0.05)
    for date, (raw, smoothed) in SPOTS.items():
        row = frame.filter(pl.col("date") == dt.date.fromisoformat(date))
        assert row["ratio"].item() == pytest.approx(raw, abs=5e-4), date
        assert row["smoothed"].item() == pytest.approx(smoothed, abs=5e-4), date


# --- R10: the 2012-lane anchor through the new code path ---------------------

COSTS = {"TQQQ": 1.5, "BTAL": 6, "DBMF": 2.5, "KMLM": 6, "QQQ": 1, "SPY": 0.7, "*": 6}


def vt_entry(gate: dict | None = None) -> dict:
    entry = {
        "type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.80}, "leverage": 3,
        "sigma_target": 0.30, "w_max": 0.6,
    }
    if gate is not None:
        entry["gate"] = gate
    return entry


def bundle_of(*entries: dict):
    return build_bundle(
        {
            "schema_version": 1,
            "config": {
                "start": "2012-01-03", "initial_capital": 10000,
                "monthly_contribution": 500, "cost_bps": COSTS, "cash_yield": 0.03,
            },
            "strategies": [
                *entries,
                {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}},
            ],
        }
    )


def test_r10_the_2012_anchor_reproduces():
    # results/sweep_safe_2012/runs.csv, window `full` — a mismatch is a bug in
    # this change, not data drift (REGIME_SPEC §9).
    sma_gate = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}
    results = run_bundle(bundle_of(vt_entry(sma_gate), vt_entry()), NET_DIR)

    gated, plain = results[0], results[1]
    assert gated.stats["calmar"] == pytest.approx(0.86254363, abs=1e-7)
    assert gated.stats["cagr"] == pytest.approx(0.2385326, abs=1e-6)
    assert gated.stats["max_drawdown"] == pytest.approx(-0.27654555, abs=1e-7)
    assert plain.stats["calmar"] == pytest.approx(0.71731262, abs=1e-7)
    assert plain.stats["cagr"] == pytest.approx(0.2479853, abs=1e-6)
    assert plain.stats["max_drawdown"] == pytest.approx(-0.3457144, abs=1e-6)


def test_r10_an_always_open_regime_gate_equals_the_no_gate_twin():
    never_fires = {
        "symbol": "VIX", "denominator": "VIX3M", "assets": ["TQQQ"],
        "ratio_sma": 10, "fire": 2.0,
    }
    bundle = bundle_of(vt_entry(never_fires), vt_entry())
    gated, plain = bundle.strategies[0], bundle.strategies[1]
    prices = load_prices(
        NET_DIR, sorted(gated.weights), bundle.config.start,
        extra=sorted(set(gated.data) | set(plain.data)),
        indicators=collect_indicators([gated, plain]),
    )
    for got, want in zip(
        simulate(prices, gated, bundle.config), simulate(prices, plain, bundle.config)
    ):
        assert_frame_equal(got, want)
