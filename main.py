"""Run a strategy bundle — each strategy plus the SPY benchmark — and report them side by side."""

import argparse
import dataclasses
import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from bundles import Bundle, BUNDLES
from indicators import Indicator
from prices import load_prices
from report import (
    StrategyResult,
    print_report,
    save_charts,
    save_markdown,
    save_transactions,
)
from results_json import save_curves, save_json
from simulate import simulate
from spec import build_bundle, load_spec, normalised_spec
from stats import correlation, imbalance, rolling_sharpe, summary, top_drawdowns, twr
from strategy import Strategy


def collect_indicators(
    strategies: Iterable[Strategy],
) -> dict[str, tuple[Indicator, ...]]:
    """Merge every strategy's indicator declarations, deduplicated by name."""
    merged: dict[str, dict[str, Indicator]] = {}
    for st in strategies:
        for symbol, declared in st.indicators.items():
            assert symbol in st.weights or symbol in st.data, (
                f"{st.label}: indicator on undeclared symbol {symbol}"
            )
            merged.setdefault(symbol, {}).update({i.name: i for i in declared})
    return {symbol: tuple(d.values()) for symbol, d in merged.items()}


def run_bundle(bundle: Bundle, data_dir: Path) -> list[StrategyResult]:
    """Load `data_dir` and simulate every strategy in `bundle`, benchmark last."""
    strategies = bundle.strategies
    traded = sorted({s for st in strategies for s in st.weights})
    extra = sorted({s for st in strategies for s in st.data} - set(traded))
    prices = load_prices(
        data_dir,
        traded,
        bundle.config.start,
        end=bundle.config.end,
        extra=extra,
        indicators=collect_indicators(strategies),
    )

    results = []
    for st in strategies:
        curve, trades, allocations = simulate(prices, st, bundle.config)
        twr_frame = twr(curve)
        results.append(
            StrategyResult(
                label=st.label,
                curve=curve,
                twr=twr_frame,
                roll=rolling_sharpe(twr_frame),
                stats=summary(curve, twr_frame, allocations),
                drawdowns=top_drawdowns(twr_frame),
                trades=trades,
                allocations=allocations,
                imbalance=imbalance(allocations),
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bundle",
        nargs="?",
        default=None,
        choices=list(BUNDLES),
        help="strategy bundle to run (default: default)",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=None,
        help="build the bundle from a spec file instead of a named bundle",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data"),
        help="price data directory (default: data)",
    )
    parser.add_argument(
        "--end",
        type=dt.date.fromisoformat,
        default=None,
        help="override the bundle's or spec's end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--md",
        nargs="?",
        const=Path("report.md"),
        default=None,
        type=Path,
        help="also write a Markdown report (default path: report.md)",
    )
    parser.add_argument(
        "--charts",
        type=Path,
        default=Path("charts"),
        help="directory for the chart PNGs (default: charts)",
    )
    parser.add_argument(
        "--json",
        nargs="?",
        const=Path("results.json"),
        default=None,
        type=Path,
        help="also write machine-readable results (default path: results.json)",
    )
    parser.add_argument(
        "--curves",
        nargs="?",
        const=Path("curves"),
        default=None,
        type=Path,
        help="also write a per-strategy daily curve CSV here (default dir: curves)",
    )
    parser.add_argument(
        "--tx",
        nargs="?",
        const=Path("transactions.md"),
        default=None,
        type=Path,
        help="also write a Markdown transaction log (default path: transactions.md)",
    )
    parser.add_argument(
        "--no-charts", action="store_true", help="skip writing the chart PNGs"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress the console report"
    )
    args = parser.parse_args()
    if args.spec and args.bundle is not None:
        parser.error("bundle and --spec are mutually exclusive")

    if args.spec:
        bundle, name = build_bundle(load_spec(args.spec)), args.spec.stem
    else:
        name = args.bundle or "default"
        bundle = BUNDLES[name]
    if args.end is not None:
        bundle = dataclasses.replace(
            bundle, config=dataclasses.replace(bundle.config, end=args.end)
        )
    spec_doc = normalised_spec(bundle) if args.spec else None
    results = run_bundle(bundle, args.data)

    bench = results[-1]
    correlations = [(r.label, correlation(r.twr, bench.twr)) for r in results[:-1]]

    if not args.quiet:
        print_report(results, correlations)

    out_dir = None if args.no_charts else args.charts
    if out_dir is not None:
        save_charts(results, out_dir)
        print(
            f"\nSaved {out_dir}/equity.png, {out_dir}/drawdown.png, "
            f"{out_dir}/rolling_sharpe.png, {out_dir}/imbalance.png"
        )

    if args.md:
        save_markdown(results, correlations, args.md, out_dir)
        print(f"Saved {args.md}")

    if args.tx:
        save_transactions(results, args.tx)
        print(f"Saved {args.tx}")

    if args.json:
        save_json(
            bundle, name, results, correlations, args.json,
            data_dir=args.data, spec_path=args.spec, spec=spec_doc,
        )
        print(f"Saved {args.json}")

    if args.curves:
        save_curves(results, args.curves)
        print(f"Saved {args.curves}/<strategy>.csv")


if __name__ == "__main__":
    main()
