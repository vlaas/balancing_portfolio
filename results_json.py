"""Machine-readable results: one diffable JSON per run, plus optional curve CSVs.

The console report and `report.md` carry pre-formatted strings; this module emits
the raw numbers instead, with sorted keys and a fixed float precision, so two runs
can be committed and diffed. `generated_at` is the one line that changes on every
re-run; it is confined to the `run` block, away from the numbers.
"""

import datetime as dt
import json
import re
import subprocess
from pathlib import Path

from bundles import Bundle
from report import StrategyResult
from stats import drawdown_curve, yearly_returns

SCHEMA_VERSION = 4
PRECISION = 8

IMBALANCE_KEYS = (
    "avg_misallocation",
    "max_misallocation",
    "avg_asset_deviation",
    "max_asset_deviation",
)


def slug(label: str) -> str:
    """A filesystem-safe name for a display label: `TQQQ/BTAL 50/50` -> `tqqq-btal-50-50`."""
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _slugs(results: list[StrategyResult]) -> list[str]:
    """Every result's slug; collisions would silently overwrite a curve CSV."""
    slugs = [slug(r.label) for r in results]
    assert len(set(slugs)) == len(slugs), f"strategy slugs collide: {slugs}"
    return slugs


def _git() -> tuple[str | None, bool | None]:
    """The commit the run was made from, and whether the tree had uncommitted changes.

    Both are None outside a git checkout — a results file is still worth writing.
    """

    def run(*args: str) -> str | None:
        done = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False
        )
        return done.stdout.strip() if done.returncode == 0 else None

    sha = run("rev-parse", "HEAD")
    status = run("status", "--porcelain")
    return sha, None if status is None else status != ""


def _round(value):
    """Every float in the payload to `PRECISION` decimals; -0.0 normalized to 0.0."""
    if isinstance(value, float):
        return round(value, PRECISION) + 0.0
    if isinstance(value, dict):
        return {key: _round(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round(item) for item in value]
    return value


def _summary(stats: dict) -> dict:
    """The summary() contract verbatim, with the two year tuples as objects."""
    out = dict(stats)
    for key in ("best_year", "worst_year"):
        year, value = out[key]
        out[key] = {"year": year, "return": value}
    return out


def _strategy(
    strategy, result: StrategyResult, name: str, correlation: float | None
) -> dict:
    assert strategy.label == result.label
    return {
        "label": result.label,
        "slug": name,
        "class": type(strategy).__name__,
        "spec": getattr(strategy, "spec", None),
        "weights": dict(strategy.weights),
        "data": list(strategy.data),
        "indicators": {
            symbol: [i.name for i in declared]
            for symbol, declared in strategy.indicators.items()
        },
        "correlation_to_benchmark": correlation,
        "summary": _summary(result.stats),
        "exposure": result.exposure,
        "drawdowns": [
            {
                "peak": d.peak.isoformat(),
                "trough": d.trough.isoformat(),
                "recovery": None if d.recovery is None else d.recovery.isoformat(),
                "depth": d.depth,
                "days": d.days,
            }
            for d in result.drawdowns
        ],
        # The final year is partial — the data ends mid-month.
        "yearly_returns": [
            {"year": year, "return": value} for year, value in yearly_returns(result.twr)
        ],
        "imbalance": {
            **{key: result.stats[key] for key in IMBALANCE_KEYS},
            "by_date": [
                {
                    "date": row["date"].isoformat(),
                    "misallocated": row["misallocated"],
                    "max_deviation": row["max_deviation"],
                }
                for row in result.imbalance.iter_rows(named=True)
            ],
        },
    }


def results_payload(
    bundle: Bundle,
    name: str,
    results: list[StrategyResult],
    correlations: list[tuple[str, float]],
    generated_at: str,
    *,
    data_dir: Path,
    spec_path: Path | None = None,
    spec: dict | None = None,
) -> dict:
    """The whole run as plain JSON types. `strategies` keeps bundle order, benchmark last."""
    curve = results[0].curve
    sha, dirty = _git()
    to_benchmark = dict(correlations)
    symbols = {s for st in bundle.strategies for s in st.weights} | {
        s for st in bundle.strategies for s in st.data
    }

    return _round(
        {
            "run": {
                "schema_version": SCHEMA_VERSION,
                "git_sha": sha,
                "git_dirty": dirty,
                "bundle": name,
                "data_dir": str(data_dir),
                "spec_path": None if spec_path is None else str(spec_path),
                "generated_at": generated_at,
            },
            "config": {
                "start": bundle.config.start.isoformat(),
                "initial_capital": bundle.config.initial_capital,
                "monthly_contribution": bundle.config.monthly_contribution,
                # Number or per-asset object, exactly as configured; both keys
                # always present — explicit beats absent.
                "cost_bps": bundle.config.cost_bps
                if isinstance(bundle.config.cost_bps, (int, float))
                else dict(bundle.config.cost_bps),
                "cash_yield": bundle.config.cash_yield,
            }
            | ({"end": bundle.config.end.isoformat()} if bundle.config.end else {}),
            "data": {
                "start": curve["date"][0].isoformat(),
                "end": curve["date"][-1].isoformat(),
                "trading_days": len(curve),
                "symbols": sorted(symbols),
            },
            "benchmark": results[-1].label,
            "spec": spec,
            "strategies": [
                # The benchmark correlates with itself; it gets no entry.
                _strategy(st, r, s, to_benchmark.get(r.label))
                for st, r, s in zip(bundle.strategies, results, _slugs(results))
            ],
        }
    )


def dumps(payload: dict) -> str:
    """Serialize sorted and indented; a NaN fails here rather than writing invalid JSON."""
    return json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n"


def save_json(
    bundle: Bundle,
    name: str,
    results: list[StrategyResult],
    correlations: list[tuple[str, float]],
    out_path: Path,
    *,
    data_dir: Path,
    spec_path: Path | None = None,
    spec: dict | None = None,
) -> None:
    """Write the run's results as JSON, stamped with the current UTC time."""
    generated_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = results_payload(
        bundle, name, results, correlations, generated_at,
        data_dir=data_dir, spec_path=spec_path, spec=spec,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(dumps(payload))


def save_curves(results: list[StrategyResult], out_dir: Path) -> None:
    """Write every strategy's daily series as `<slug>.csv` into `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, r in zip(_slugs(results), results):
        frame = (
            r.curve.join(r.twr, on="date")
            .join(drawdown_curve(r.twr), on="date")
            .join(r.roll, on="date")
            .rename({"sharpe": "rolling_sharpe"})
        )
        frame.write_csv(out_dir / f"{name}.csv", float_precision=PRECISION)
