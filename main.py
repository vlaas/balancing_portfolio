"""Run a strategy bundle — each strategy plus the SPY benchmark — and report them side by side."""

import argparse
from pathlib import Path

from bundles import BUNDLES
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

    bundle = BUNDLES[args.bundle]
    strategies = bundle.strategies
    traded = sorted({s for st in strategies for s in st.weights})
    extra = sorted({s for st in strategies for s in st.data} - set(traded))
    prices = load_prices(Path("data"), traded, bundle.config.start, extra=extra)

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
