# Dynamic chart colours and console column widths — DECLARATIVE_SPEC.md T10.

import datetime as dt

import polars as pl
import pytest

from report import NAME_W, StrategyResult, print_report, save_charts

PNGS = ["equity.png", "drawdown.png", "rolling_sharpe.png", "imbalance.png"]


def result(label: str) -> StrategyResult:
    dates = [dt.date(2020, 1, 2) + dt.timedelta(days=i) for i in range(3)]
    return StrategyResult(
        label=label,
        curve=pl.DataFrame({"date": dates, "value": [100.0, 101.0, 102.0]}),
        twr=pl.DataFrame(
            {"date": dates, "ret": [0.0, 0.01, 0.01], "index": [1.0, 1.01, 1.0201]}
        ),
        roll=pl.DataFrame({"date": dates, "sharpe": [None, 0.5, 0.6]}),
        stats={
            "final_value": 102.0,
            "total_contributed": 100.0,
            "net_profit": 2.0,
            "net_profit_pct": 0.02,
            "cagr": 0.02,
            "xirr": 0.02,
            "volatility": 0.1,
            "sharpe": 1.0,
            "sortino": 1.5,
            "calmar": 0.5,
            "max_drawdown": -0.05,
            "max_drawdown_days": 10,
            "best_year": (2020, 0.02),
            "worst_year": (2020, 0.02),
            "avg_misallocation": 0.01,
            "max_misallocation": 0.02,
            "avg_asset_deviation": 0.01,
            "max_asset_deviation": 0.02,
        },
        drawdowns=[],
        trades=pl.DataFrame(),
        allocations=pl.DataFrame(),
        imbalance=pl.DataFrame({"date": dates, "misallocated": [0.01, 0.02, 0.01]}),
        exposure={
            "A": {"avg_target": 0.5, "avg": 0.49, "min": 0.45, "max": 0.52},
            "CASH": {"avg_target": 0.5, "avg": 0.51, "min": 0.48, "max": 0.55},
        },
    )


@pytest.mark.parametrize("n", [6, 20])
def test_charts_handle_bundles_beyond_the_brand_palette(n, tmp_path):
    save_charts([result(f"strategy {i}") for i in range(n)], tmp_path)

    for name in PNGS:
        assert (tmp_path / name).stat().st_size > 0


def test_more_than_twenty_strategies_refuse_to_chart(tmp_path):
    with pytest.raises(AssertionError, match="no-charts"):
        save_charts([result(f"strategy {i}") for i in range(21)], tmp_path)


def test_long_labels_keep_the_columns_aligned(capsys):
    long = "a strategy with a 30-char name"
    assert len(long) == 30

    print_report([result("short"), result(long)], correlations=[])

    lines = capsys.readouterr().out.splitlines()
    rule = next(line for line in lines if line and set(line) == {"-"})
    header = lines[lines.index(rule) - 1]
    first_metric = lines[lines.index(rule) + 1]

    value_w = len(long) + 2
    assert len(header) == len(rule) == len(first_metric) == NAME_W + 2 * value_w
    assert header.endswith(long)
    assert first_metric.startswith("Final value")


def test_exposure_rows_render_after_misallocation(capsys):
    print_report([result("one"), result("two")], correlations=[])

    lines = capsys.readouterr().out.splitlines()
    rule = next(line for line in lines if line and set(line) == {"-"})
    misallocation = next(l for l in lines if l.startswith("Max worst-asset dev"))
    row = next(l for l in lines if l.startswith("Avg weight A"))

    assert lines.index(row) == lines.index(misallocation) + 1
    assert len(row) == len(rule)
    assert row.split()[-1] == "0.49"
    assert not any(l.startswith("Avg weight CASH") for l in lines)
