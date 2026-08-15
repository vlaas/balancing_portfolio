"""Return and risk statistics computed from a simulated equity curve.

The input curve is `date | value | flow` where `value` is the end-of-day portfolio
value and `flow` is external cash added at that day's close.
"""

import datetime as dt
import math
from dataclasses import dataclass

import polars as pl

TRADING_DAYS = 252


def twr(curve: pl.DataFrame) -> pl.DataFrame:
    """Time-weighted daily returns and the cumulative index built from them.

    Flows land at the close they are invested at, so they see no price move that
    day: r_t = (V_t - F_t) / V_{t-1} - 1.
    """
    out = curve.select(
        "date",
        ((pl.col("value") - pl.col("flow")) / pl.col("value").shift(1) - 1.0).alias("ret"),
    )
    return out.with_columns((pl.col("ret").fill_null(0.0) + 1.0).cum_prod().alias("index"))


def xirr(dates: list[dt.date], amounts: list[float]) -> float:
    """Money-weighted annual return, by bisection on the NPV."""
    days = [(d - dates[0]).days for d in dates]

    def npv(rate: float) -> float:
        return sum(cf * (1.0 + rate) ** (-n / 365) for cf, n in zip(amounts, days))

    lo, hi = -0.9999, 10.0
    npv_lo, npv_hi = npv(lo), npv(hi)
    assert npv_lo * npv_hi < 0, "XIRR bracket does not contain a sign change"
    while hi - lo > 1e-10:
        mid = (lo + hi) / 2
        if npv(mid) * npv_lo > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


@dataclass(frozen=True)
class Drawdown:
    peak: dt.date
    trough: dt.date
    recovery: dt.date | None
    depth: float
    days: int | None


def top_drawdowns(twr_frame: pl.DataFrame, n: int = 5) -> list[Drawdown]:
    """The n deepest non-overlapping drawdown episodes, deepest first."""
    dates = twr_frame["date"].to_list()
    values = twr_frame["index"].to_list()

    episodes: list[Drawdown] = []
    peak_value, peak_date = values[0], dates[0]
    trough_value, trough_date = None, None

    for date, value in zip(dates[1:], values[1:]):
        if value >= peak_value:
            if trough_value is not None:
                episodes.append(
                    Drawdown(
                        peak=peak_date,
                        trough=trough_date,
                        recovery=date,
                        depth=trough_value / peak_value - 1.0,
                        days=(date - peak_date).days,
                    )
                )
                trough_value, trough_date = None, None
            peak_value, peak_date = value, date
        elif trough_value is None or value < trough_value:
            trough_value, trough_date = value, date

    if trough_value is not None:
        episodes.append(
            Drawdown(
                peak=peak_date,
                trough=trough_date,
                recovery=None,
                depth=trough_value / peak_value - 1.0,
                days=None,
            )
        )

    episodes.sort(key=lambda d: d.depth)
    return episodes[:n]


def rolling_sharpe(twr_frame: pl.DataFrame, window: int = TRADING_DAYS) -> pl.DataFrame:
    """Annualized Sharpe over a trailing window; null during warmup and where std is 0."""
    mean = pl.col("ret").rolling_mean(window)
    std = pl.col("ret").rolling_std(window, ddof=1)
    sharpe = (
        pl.when(std > 0)
        .then(mean / std * math.sqrt(TRADING_DAYS))
        .otherwise(pl.lit(None, dtype=pl.Float64))
    )
    return twr_frame.select("date", sharpe.alias("sharpe"))


def correlation(twr_a: pl.DataFrame, twr_b: pl.DataFrame) -> float:
    """Pearson correlation of the two daily return series over their common dates."""
    joined = (
        twr_a.select("date", pl.col("ret").alias("a"))
        .join(twr_b.select("date", pl.col("ret").alias("b")), on="date", how="inner")
        .drop_nulls()
    )
    return joined.select(pl.corr("a", "b")).item()


def _yearly_returns(twr_frame: pl.DataFrame) -> list[tuple[int, float]]:
    """Calendar-year returns from the TWR index; the partial final year is included as-is."""
    year_ends = (
        twr_frame.sort("date")
        .group_by(pl.col("date").dt.year().alias("year"), maintain_order=True)
        .agg(pl.col("index").last())
    )
    previous = 1.0
    returns = []
    for year, value in zip(year_ends["year"].to_list(), year_ends["index"].to_list()):
        returns.append((year, value / previous - 1.0))
        previous = value
    return returns


def imbalance(allocations: pl.DataFrame) -> pl.DataFrame:
    """Per trade day, how far the post-trade allocation is from the target.

    `misallocated` is half the sum of |target - actual| over assets and cash —
    the fraction of the portfolio in the wrong place. `max_deviation` is the
    single worst asset's |target - actual| (cash excluded).
    """
    deviation = (pl.col("target") - pl.col("actual")).abs()
    return (
        allocations.group_by("date", maintain_order=True)
        .agg(
            misallocated=deviation.sum() / 2,
            max_deviation=deviation.filter(pl.col("asset") != "CASH").max(),
        )
    )


def summary(
    curve: pl.DataFrame, twr_frame: pl.DataFrame, allocations: pl.DataFrame
) -> dict[str, object]:
    dates = curve["date"].to_list()
    final_value = curve["value"].to_list()[-1]
    total_contributed = curve["flow"].sum()
    net_profit = final_value - total_contributed

    index_last = twr_frame["index"].to_list()[-1]
    years = (dates[-1] - dates[0]).days / 365.25
    cagr = index_last ** (1 / years) - 1.0

    flows = curve.filter(pl.col("flow") != 0.0)
    cash_dates = flows["date"].to_list() + [dates[-1]]
    cash_amounts = [-f for f in flows["flow"].to_list()] + [final_value]

    ret = twr_frame["ret"].drop_nulls()
    mean = ret.mean()
    volatility = ret.std(ddof=1) * math.sqrt(TRADING_DAYS)
    downside_dev = math.sqrt((ret.clip(upper_bound=0.0) ** 2).mean())

    drawdowns = top_drawdowns(twr_frame)
    max_drawdown = drawdowns[0].depth

    yearly = _yearly_returns(twr_frame)
    best_year = max(yearly, key=lambda y: y[1])
    worst_year = min(yearly, key=lambda y: y[1])

    off = imbalance(allocations)

    return {
        "avg_misallocation": off["misallocated"].mean(),
        "max_misallocation": off["misallocated"].max(),
        "avg_asset_deviation": off["max_deviation"].mean(),
        "max_asset_deviation": off["max_deviation"].max(),
        "final_value": final_value,
        "total_contributed": total_contributed,
        "net_profit": net_profit,
        "net_profit_pct": net_profit / total_contributed,
        "cagr": cagr,
        "xirr": xirr(cash_dates, cash_amounts),
        "sharpe": mean / ret.std(ddof=1) * math.sqrt(TRADING_DAYS),
        "volatility": volatility,
        "sortino": mean / downside_dev * math.sqrt(TRADING_DAYS),
        "calmar": cagr / abs(max_drawdown),
        "max_drawdown": max_drawdown,
        "max_drawdown_days": drawdowns[0].days,
        "best_year": best_year,
        "worst_year": worst_year,
    }
