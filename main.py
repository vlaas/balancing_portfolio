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

STRATEGIES = [
    ("TQQQ/BTAL 50/50", {"TQQQ": 0.5, "BTAL": 0.5}),
    ("TQQQ 100%", {"TQQQ": 1.0}),
    ("SPY benchmark", {"SPY": 1.0}),
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
        "--tx",
        nargs="?",
        const=Path("transactions.md"),
        default=None,
        type=Path,
        help="also write a Markdown transaction log (default path: transactions.md)",
    )
    args = parser.parse_args()

    prices = load_prices(Path("data"), ["TQQQ", "BTAL", "SPY"], dt.date(2017, 1, 3))

    results = []
    for label, weights in STRATEGIES:
        cfg = Config(
            start=dt.date(2017, 1, 3),
            initial_capital=10_000,
            monthly_contribution=500,
            weights=weights,
        )
        curve, trades = simulate(prices, cfg)
        twr_frame = twr(curve)
        results.append(
            StrategyResult(
                label=label,
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

    out_dir = Path("charts")
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
