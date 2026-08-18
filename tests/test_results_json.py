import json
import re
from pathlib import Path

import pytest

from bundles import BUNDLES
from main import run_bundle
from results_json import PRECISION, dumps, results_payload, save_curves, slug
from stats import correlation

GOLDEN_DIR = Path(__file__).parent / "data"
STAMP = "2026-01-01T00:00:00Z"

CURVE_COLUMNS = ["date", "value", "flow", "ret", "index", "drawdown", "rolling_sharpe"]


@pytest.fixture(scope="module")
def run():
    """The default bundle over the frozen snapshot, as main() assembles it."""
    results = run_bundle(BUNDLES["default"], GOLDEN_DIR)
    bench = results[-1]
    correlations = [(r.label, correlation(r.twr, bench.twr)) for r in results[:-1]]
    return results, correlations


@pytest.fixture(scope="module")
def payload(run):
    results, correlations = run
    return results_payload(
        BUNDLES["default"], "default", results, correlations, STAMP, data_dir=GOLDEN_DIR
    )


# T9 - The file has to be diffable: identical inputs, identical bytes.


def test_the_same_run_serializes_to_the_same_bytes(run):
    results, correlations = run

    first, second = (
        dumps(results_payload(
        BUNDLES["default"], "default", results, correlations, STAMP, data_dir=GOLDEN_DIR
    ))
        for _ in range(2)
    )

    assert first == second


def _floats(value):
    """Every float anywhere in the payload."""
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _floats(item)
    elif isinstance(value, list):
        for item in value:
            yield from _floats(item)


def test_every_float_is_written_at_a_fixed_precision(payload):
    text = dumps(payload)

    # On the values, so the ones Python renders as 7.036e-05 are covered too.
    written = list(_floats(json.loads(text)))
    assert written
    assert all(f == round(f, PRECISION) for f in written)
    assert not any(str(f).startswith("-0.0") and f == 0 for f in written)
    assert not re.search(rf"\.\d{{{PRECISION + 1},}}", text)
    assert json.loads(text) == payload


def test_keys_are_sorted_but_the_benchmark_stays_last(payload):
    text = dumps(payload)

    assert text == json.dumps(json.loads(text), sort_keys=True, indent=2) + "\n"
    assert [s["label"] for s in payload["strategies"]] == [
        "TQQQ/BTAL 50/50",
        "TQQQ 100%",
        "TQQQ/BTAL SMA gate",
        "SPY benchmark",
    ]
    assert payload["benchmark"] == "SPY benchmark"


# T10 - The payload's contract.


def test_the_payload_carries_the_run_config_and_data_range(payload):
    assert set(payload) == {"run", "config", "data", "benchmark", "spec", "strategies"}
    assert payload["run"]["schema_version"] == 2
    assert payload["run"]["bundle"] == "default"
    assert payload["run"]["data_dir"] == str(GOLDEN_DIR)
    assert payload["run"]["spec_path"] is None
    assert payload["run"]["generated_at"] == STAMP
    # A bundle run has no spec to embed, at either level.
    assert payload["spec"] is None
    assert all(s["spec"] is None for s in payload["strategies"])
    assert payload["config"] == {
        "start": "2017-01-03",
        "initial_capital": 10_000,
        "monthly_contribution": 500,
    }
    assert payload["data"]["start"] == "2017-01-03"
    assert payload["data"]["symbols"] == ["BTAL", "QQQ", "SPY", "TQQQ"]
    assert payload["data"]["trading_days"] == 2417
    assert payload["data"]["end"] == "2026-08-14"


def test_every_strategy_reports_the_whole_summary_contract(run, payload):
    results, _ = run

    for result, entry in zip(results, payload["strategies"]):
        assert set(entry["summary"]) == set(result.stats)
        assert set(entry["summary"]["best_year"]) == {"year", "return"}
        assert len(entry["drawdowns"]) == len(result.drawdowns)
        assert [y["year"] for y in entry["yearly_returns"]] == list(range(2017, 2027))
        assert len(entry["imbalance"]["by_date"]) == len(result.imbalance)


def test_only_the_benchmark_has_no_correlation_to_itself(payload):
    correlations = [s["correlation_to_benchmark"] for s in payload["strategies"]]

    assert correlations[-1] is None
    assert all(isinstance(c, float) for c in correlations[:-1])


def test_the_numbers_match_the_stats_they_came_from(run, payload):
    results, _ = run

    for result, entry in zip(results, payload["strategies"]):
        assert entry["summary"]["final_value"] == pytest.approx(
            result.stats["final_value"], abs=1e-8
        )
        assert entry["drawdowns"][0]["depth"] == pytest.approx(
            result.stats["max_drawdown"], abs=1e-8
        )
        assert entry["imbalance"]["avg_misallocation"] == pytest.approx(
            result.stats["avg_misallocation"], abs=1e-8
        )


# T11 - Slugs and the curve CSVs.


def test_labels_slugify_to_unique_filesystem_safe_names(payload):
    slugs = [s["slug"] for s in payload["strategies"]]

    assert slugs == ["tqqq-btal-50-50", "tqqq-100", "tqqq-btal-sma-gate", "spy-benchmark"]
    assert len(set(slugs)) == len(slugs)


def test_curves_write_one_csv_per_strategy(run, tmp_path):
    results, _ = run

    save_curves(results, tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        f"{slug(r.label)}.csv" for r in results
    )
    for result in results:
        lines = (tmp_path / f"{slug(result.label)}.csv").read_text().splitlines()
        assert lines[0].split(",") == CURVE_COLUMNS
        assert len(lines) == len(result.curve) + 1
