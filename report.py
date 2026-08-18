"""Console summary table and charts comparing the strategies side by side."""

import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import polars as pl

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from stats import Drawdown, drawdown_curve

# Categorical slots 1-4 on the light chart surface, plus its chrome inks.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED_INK = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _pct(value: float) -> str:
    return f"{value:.2%}"


def _signed_pct(value: float) -> str:
    return f"{value:+.2%}"


def _ratio(value: float) -> str:
    return f"{value:.2f}"


def _days(value: int | None) -> str:
    return "ongoing" if value is None else f"{value:,}"


def _year(value: tuple[int, float]) -> str:
    year, ret = value
    return f"{year}: {ret:+.1%}"


METRICS = [
    ("Final value", "final_value", _money),
    ("Total contributed", "total_contributed", _money),
    ("Net profit", "net_profit", _money),
    ("Net profit %", "net_profit_pct", _signed_pct),
    ("CAGR (TWR)", "cagr", _signed_pct),
    ("XIRR (money-weighted)", "xirr", _signed_pct),
    ("Volatility (annualised)", "volatility", _pct),
    ("Sharpe", "sharpe", _ratio),
    ("Sortino", "sortino", _ratio),
    ("Calmar", "calmar", _ratio),
    ("Max drawdown", "max_drawdown", _signed_pct),
    ("Max drawdown days", "max_drawdown_days", _days),
    ("Best year", "best_year", _year),
    ("Worst year", "worst_year", _year),
    ("Avg misallocation", "avg_misallocation", _pct),
    ("Max misallocation", "max_misallocation", _pct),
    ("Avg worst-asset dev", "avg_asset_deviation", _pct),
    ("Max worst-asset dev", "max_asset_deviation", _pct),
]

NAME_W = 25
VALUE_W = 20
DD_HEADER = f"{'Peak':<13}{'Trough':<13}{'Recovery':<13}{'Depth':>10}{'Days':>8}"


@dataclass(frozen=True)
class StrategyResult:
    label: str
    curve: pl.DataFrame
    twr: pl.DataFrame
    roll: pl.DataFrame
    stats: dict
    drawdowns: list[Drawdown]
    trades: pl.DataFrame
    allocations: pl.DataFrame
    imbalance: pl.DataFrame


def _print_drawdowns(title: str, drawdowns: list[Drawdown]) -> None:
    print()
    print(title)
    print(DD_HEADER)
    print("-" * len(DD_HEADER))
    for dd in drawdowns:
        recovery = "ongoing" if dd.recovery is None else dd.recovery.isoformat()
        days = "-" if dd.days is None else f"{dd.days:,}"
        print(
            f"{dd.peak.isoformat():<13}{dd.trough.isoformat():<13}{recovery:<13}"
            f"{dd.depth:>10.2%}{days:>8}"
        )


def print_report(
    results: list[StrategyResult], correlations: list[tuple[str, float]]
) -> None:
    """Print the side-by-side metric table, drawdown tables and correlations."""
    print()
    print(" vs ".join(r.label for r in results))
    print()
    print(f"{'':<{NAME_W}}" + "".join(f"{r.label:>{VALUE_W}}" for r in results))
    print("-" * (NAME_W + len(results) * VALUE_W))
    for label, key, fmt in METRICS:
        print(
            f"{label:<{NAME_W}}"
            + "".join(f"{fmt(r.stats[key]):>{VALUE_W}}" for r in results)
        )

    for r in results:
        _print_drawdowns(f"Top drawdowns - {r.label}", r.drawdowns)

    print()
    for label, corr in correlations:
        print(f"Daily-return correlation, {label} to SPY benchmark: {corr:.2f}")


def _axes(title: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_title(title, color=INK, fontsize=13, loc="left", pad=14)
    ax.set_ylabel(ylabel, color=MUTED_INK, fontsize=10)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED_INK, length=0, labelsize=9)
    return fig, ax


def _plot(ax, frame: pl.DataFrame, column: str, label: str, color: str) -> None:
    frame = frame.drop_nulls(column)
    ax.plot(
        frame["date"].to_list(),
        frame[column].to_list(),
        label=label,
        color=color,
        linewidth=2,
        solid_joinstyle="round",
        solid_capstyle="round",
    )


def _save(fig, ax, path: Path) -> None:
    ax.legend(frameon=False, loc="best", fontsize=10, labelcolor=SECONDARY_INK)
    fig.savefig(path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def save_charts(results: list[StrategyResult], out_dir: Path) -> None:
    """Write equity.png, drawdown.png and rolling_sharpe.png into `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = _axes("Account value, identical cash flows", "USD")
    for r, color in zip(results, COLORS):
        _plot(ax, r.curve, "value", r.label, color)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    _save(fig, ax, out_dir / "equity.png")

    fig, ax = _axes("Drawdown from peak, time-weighted", "Drawdown")
    for r, color in zip(results, COLORS):
        _plot(ax, drawdown_curve(r.twr), "drawdown", r.label, color)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    _save(fig, ax, out_dir / "drawdown.png")

    fig, ax = _axes("252-day rolling Sharpe ratio", "Sharpe")
    ax.axhline(0, color=AXIS, linewidth=1)
    for r, color in zip(results, COLORS):
        _plot(ax, r.roll, "sharpe", r.label, color)
    _save(fig, ax, out_dir / "rolling_sharpe.png")

    fig, ax = _axes("Misallocation after each rebalance", "Misallocated")
    for r, color in zip(results, COLORS):
        _plot(ax, r.imbalance, "misallocated", r.label, color)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    _save(fig, ax, out_dir / "imbalance.png")


def save_markdown(
    results: list[StrategyResult],
    correlations: list[tuple[str, float]],
    out_path: Path,
    charts_dir: Path,
) -> None:
    """Write the full report as Markdown, linking the charts relatively."""
    first, last = results[0].curve["date"][0], results[0].curve["date"][-1]
    lines = [
        "# Portfolio strategy comparison",
        "",
        f"Simulated {first.isoformat()} to {last.isoformat()}.",
        "",
        "| | " + " | ".join(r.label for r in results) + " |",
        "|---" + "|---:" * len(results) + "|",
    ]
    for label, key, fmt in METRICS:
        lines.append(
            f"| {label} | " + " | ".join(fmt(r.stats[key]) for r in results) + " |"
        )

    for name, title in [
        ("equity.png", "Account value"),
        ("drawdown.png", "Drawdown"),
        ("rolling_sharpe.png", "Rolling Sharpe"),
        ("imbalance.png", "Imbalance"),
    ]:
        rel = os.path.relpath(charts_dir / name, out_path.parent)
        lines += ["", f"## {title}", "", f"![{title}]({rel})"]

    for r in results:
        lines += [
            "",
            f"## Top drawdowns — {r.label}",
            "",
            "| Peak | Trough | Recovery | Depth | Days |",
            "|---|---|---|---:|---:|",
        ]
        for dd in r.drawdowns:
            recovery = "ongoing" if dd.recovery is None else dd.recovery.isoformat()
            days = "-" if dd.days is None else f"{dd.days:,}"
            lines.append(
                f"| {dd.peak.isoformat()} | {dd.trough.isoformat()} | {recovery} "
                f"| {dd.depth:.2%} | {days} |"
            )

    lines.append("")
    for label, corr in correlations:
        lines.append(f"- Daily-return correlation, {label} to SPY benchmark: {corr:.2f}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def save_transactions(results: list[StrategyResult], out_path: Path) -> None:
    """Write every strategy's DEPOSIT/BUY/SELL ledger as one Markdown file."""
    lines = ["# Transaction log"]
    for r in results:
        ledger = r.trades.join(r.curve.select("date", "value"), on="date", how="left")
        # One compact "actual/target" percents cell per trade day, shown as a
        # BALANCE row after the day's trades.
        balances = {
            date: ", ".join(
                f"{a} {actual * 100:.1f}/{target * 100:.1f}"
                for a, target, actual in zip(group["asset"], group["target"], group["actual"])
            )
            for (date,), group in r.allocations.group_by(["date"], maintain_order=True)
        }
        lines += [
            "",
            f"## {r.label}",
            "",
            "| Date | Action | Asset | Shares | Price | Amount | Cash after | Portfolio value |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
        rows = list(ledger.iter_rows(named=True))
        for t, nxt in zip(rows, rows[1:] + [None]):
            asset = t["asset"] or ""
            shares = "" if t["shares"] is None else f"{t['shares']:,}"
            price = "" if t["price"] is None else _money(t["price"])
            lines.append(
                f"| {t['date'].isoformat()} | {t['action']} | {asset} | {shares} "
                f"| {price} | {_money(t['amount'])} | {_money(t['cash_after'])} "
                f"| {_money(t['value'])} |"
            )
            if nxt is None or nxt["date"] != t["date"]:
                lines.append(
                    f"| {t['date'].isoformat()} | BALANCE | {balances[t['date']]} "
                    f"| | | | | {_money(t['value'])} |"
                )

    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
