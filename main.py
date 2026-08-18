"""Run a strategy bundle — each strategy plus the SPY benchmark — and report them side by side."""

import argparse
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
from simulate import simulate
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
        default="default",
        choices=list(BUNDLES),
        help="strategy bundle to run (default: default)",
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
        "--tx",
        nargs="?",
        const=Path("transactions.md"),
        default=None,
        type=Path,
        help="also write a Markdown transaction log (default path: transactions.md)",
    )
    args = parser.parse_args()

    results = run_bundle(BUNDLES[args.bundle], Path("data"))

    bench = results[-1]
    correlations = [(r.label, correlation(r.twr, bench.twr)) for r in results[:-1]]

    print_report(results, correlations)

    out_dir = args.charts
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


if __name__ == "__main__":
    main()
