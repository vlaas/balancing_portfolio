"""Run each strategy plus the SPY benchmark and report them side by side."""

import argparse
import datetime as dt
from pathlib import Path

from prices import load_prices
from report import (
    StrategyResult,
    print_report,
    save_charts,
    save_markdown,
    save_transactions,
)
from simulate import Config, simulate
from stats import correlation, rolling_sharpe, summary, top_drawdowns, twr
from strategies.spy_benchmark import SpyBenchmark
from strategies.tqqq_100 import Tqqq100
from strategies.tqqq_btal_5050 import TqqqBtal5050
from strategies.tqqq_btal_qqq_sma200 import TqqqBtalQqqSma200

STRATEGIES = [
    TqqqBtal5050(),
    Tqqq100(),
    TqqqBtalQqqSma200(),
    SpyBenchmark(),  # last: the correlation reference
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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

    start = dt.date(2017, 1, 3)
    traded = sorted({s for st in STRATEGIES for s in st.weights})
    extra = sorted({s for st in STRATEGIES for s in st.data} - set(traded))
    prices = load_prices(Path("data"), traded, start, extra=extra)
    config = Config(start=start, initial_capital=10_000, monthly_contribution=500)

    results = []
    for st in STRATEGIES:
        curve, trades = simulate(prices, st, config)
        twr_frame = twr(curve)
        results.append(
            StrategyResult(
                label=st.label,
                curve=curve,
                twr=twr_frame,
                roll=rolling_sharpe(twr_frame),
                stats=summary(curve, twr_frame),
                drawdowns=top_drawdowns(twr_frame),
                trades=trades,
            )
        )

    bench = results[-1]
    correlations = [(r.label, correlation(r.twr, bench.twr)) for r in results[:-1]]

    print_report(results, correlations)

    out_dir = args.charts
    save_charts(results, out_dir)
    print(f"\nSaved {out_dir}/equity.png, {out_dir}/drawdown.png, {out_dir}/rolling_sharpe.png")

    if args.md:
        save_markdown(results, correlations, args.md, out_dir)
        print(f"Saved {args.md}")

    if args.tx:
        save_transactions(results, args.tx)
        print(f"Saved {args.tx}")


if __name__ == "__main__":
    main()
