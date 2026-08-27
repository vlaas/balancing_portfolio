"""Extend a frozen dataset root backward with modelled pre-inception history.

Reads a dataset root in the TOTAL_RETURN_SPEC §3 / NET_TR_SPEC §3 convention
and writes a `-syn` sibling in which TQQQ and BIL reach back to the index
leg's own history. A daily-rebalanced L× fund is modelled as
`r_t = L*s_t - (L-1)*y_{t-1}*d_t/360 - c*d_t/365` and a T-bill fund as
`r_t = (1-w)*y_{t-1}*d_t/360 - c_b*d_t/365`, with `y` the 3-month bill
forward-filled onto the bar calendar and lagged one row (SYNTHETIC_HISTORY_SPEC
§2.3, §2.5). Both constants are fitted on the parent's own real segment, and
the modelled series is spliced strictly before the real first bar, so every run
starting on or after inception reads only real bars and is bit-identical to the
parent's (§4). Deterministic by construction — no clock, no environment — so
the committed snapshot is byte-reproducible from the committed parent and this
script (S4).

A synthetic root is a falsifier, never a fitting lane (§10).

Run: uv run make_synthetic.py tests/data/2026-08-24-net15
     --gross tests/data/2026-08-24 --withholding 0.15
     [--out DIR] [--drag C] [--bill-drag CB] [--force]
"""

import argparse
import datetime as dt
import math
import shutil
import statistics
from pathlib import Path

import polars as pl

# SYNTHETIC_HISTORY_SPEC §3. The index leg and the accrual calendar are read
# from the *gross* root in both conventions: a swap pays the gross total
# return, and SPY is the loader's widest traded calendar (1993-01-29).
RISK, BILL = "TQQQ", "BIL"
INDEX, CALENDAR, RATE = "QQQ", "SPY", "DTB3"
LEVERAGE = 3

# The inceptions the splice is pinned to. A refreshed parent with a different
# first bar is a different splice and must be looked at (--force).
INCEPTION = {RISK: "2010-02-11", BILL: "2007-05-30"}

# §3 sanity bands on the fitted (or overridden) constants: a value outside
# them means the wrong file was passed, not a surprising market.
DRAG_BAND = (0.005, 0.045)
BILL_DRAG_BAND = (-0.001, 0.004)

# §2.2 / S10 jump floor on the adjustment ratio, matching make_net_tr.JUMP_MIN.
JUMP_MIN = 1e-5

# §6 S10: the operator spot check against the issuer's published distribution
# history — the first distribution the trust ever made, the outlier, and the
# one after it. Pinned here (not read from `dividends/`) so the README line
# stays deterministic on the generator's declared inputs alone; the full
# 2003–2010 record and its provenance live in `dividends/pre_polygon/QQQ.csv`.
# 2004-12-17 is quoted verbatim in the trust's audited annual report for the
# fiscal year ended 2004-09-30 ("the Trust paid an ordinary income dividend to
# shareholders of $.37858 per share"), a $3.00 Microsoft special dividend
# passing through. QQQ's only split (2-for-1, 2000-03-20) predates every
# distribution it has ever made, so as-paid and split-adjusted coincide.
PUBLISHED = {"2003-12-24": 0.01358, "2004-12-17": 0.37858, "2005-12-16": 0.10110}


def default_out(parent: str) -> str:
    """`2026-08-24` -> `2026-08-24-syn`, `2026-08-24-net15` -> `2026-08-24-syn-net15`.

    The withholding suffix stays last, so a root's name reads snapshot, then
    extension, then convention (§4; §15 erratum 1)."""
    stem, marker, rate = parent.partition("-net")
    return f"{stem}-syn{marker}{rate}"


def read_close(path: Path) -> tuple[list[str], list[float]]:
    """One CSV as (time, close). `time` is read as a string and passed through
    untouched so a byte-copied or spliced file carries identical date values."""
    frame = pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"time": pl.String, "close": pl.Float64},
    )
    return frame["time"].to_list(), frame["close"].to_list()


def spans(times: list[str]) -> list[int]:
    """Calendar days since the previous bar; the first entry is 0."""
    days = [dt.date.fromisoformat(t) for t in times]
    return [0] + [(b - a).days for a, b in zip(days, days[1:])]


def carry(rate_times: list[str], rate_values: list[float], times: list[str]) -> list[float]:
    """The rate forward-filled onto `times` and lagged one row, as a decimal.

    `y[t]` is the rate known on the previous bar, which is what prices the
    borrowing over the bar ending at t (§3). `y[0]` is None: the first row has
    no return. Dates before the rate series begins carry None and would fail
    loudly; DTB3 reaches 1954 and no calendar here starts before 1993."""
    filled, i, last = [], 0, None
    for time in times:
        while i < len(rate_times) and rate_times[i] <= time:
            last = rate_values[i]
            i += 1
        filled.append(None if last is None else last / 100.0)
    return [None] + filled[:-1]


def _returns(closes: list[float]) -> list[float]:
    return [0.0] + [b / a - 1.0 for a, b in zip(closes, closes[1:])]


def window(times: list[str], start: str | None = None, end: str | None = None) -> list[str]:
    """The dates within [start, end]; ISO strings compare as dates."""
    return [
        t for t in times
        if (start is None or t >= start) and (end is None or t <= end)
    ]


def aligned(
    index: tuple[list[str], list[float]], fund: tuple[list[str], list[float]],
    start: str | None = None, end: str | None = None,
) -> tuple[list[str], list[float], list[float]]:
    """The two series on the dates they share, within [start, end] — a fit's
    calendar. Returns (times, index closes, fund closes)."""
    index_at, fund_at = dict(zip(*index)), dict(zip(*fund))
    times = [t for t in window(fund[0], start, end) if t in index_at]
    return times, [index_at[t] for t in times], [fund_at[t] for t in times]


def _fit(real: list[float], base: list[float], days: list[int]) -> dict:
    """The constant that makes the model end the overlap at the real series'
    level exactly, plus the fit's diagnostics (§2.3).

    `c = -sum(resid) / sum(d) * 365` on log returns, so `cum_end` is 0 by
    construction. `max_cum_dev` is the largest absolute cumulative log
    deviation of the fitted series from the real one — the log measure, which
    is what §2.3's table reports."""
    resid = [math.log(1 + r) - math.log(1 + b) for r, b in zip(real, base)]
    c = -sum(resid) / sum(days) * 365.0
    after = [x + c * d / 365.0 for x, d in zip(resid, days)]
    running, worst = 0.0, 0.0
    for x in after:
        running += x
        worst = max(worst, abs(running))
    return {"c": c, "n": len(real), "residual": statistics.stdev(after),
            "max_cum_dev": worst}


def _beta(index: list[float], fund: list[float]) -> float:
    """Realised leverage: the OLS slope, with intercept, of the fund's log
    return on the index's (§2.3)."""
    x = [math.log(1 + s) for s in index]
    y = [math.log(1 + r) for r in fund]
    mx, my = statistics.fmean(x), statistics.fmean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    var = sum((a - mx) ** 2 for a in x)
    return cov / var


def fit_drag(
    index_closes: list[float], fund_closes: list[float],
    y: list[float], days: list[int], leverage: int,
) -> dict:
    """§2.3, on an overlap whose row 0 is the anchor bar (no return)."""
    s = _returns(index_closes)[1:]
    real = _returns(fund_closes)[1:]
    y, days = y[1:], days[1:]
    base = [
        leverage * si - (leverage - 1) * yi * d / 360.0
        for si, yi, d in zip(s, y, days)
    ]
    return _fit(real, base, days) | {"beta": _beta(s, real)}


def fit_bill(
    bill_closes: list[float], y: list[float], days: list[int], w: float
) -> dict:
    """§2.5. The withholding is proportional: a T-bill fund distributes its
    whole accrual, so `w` scales with the rate and cannot be a constant."""
    real = _returns(bill_closes)[1:]
    y, days = y[1:], days[1:]
    base = [(1.0 - w) * yi * d / 360.0 for yi, d in zip(y, days)]
    return _fit(real, base, days)


def _levels(rates: list[float], days: list[int], per_bar) -> list[float]:
    """The recursion from 1.0 at the first bar; the first row's return is 0."""
    out = [1.0]
    for t in range(1, len(days)):
        out.append(out[-1] * (1.0 + per_bar(t, rates[t], days[t])))
    return out


def leveraged_levels(
    closes: list[float], y: list[float], days: list[int], leverage: int, c: float
) -> list[float]:
    """The modelled L× fund on an index's own bar calendar (§2.3)."""
    s = _returns(closes)
    return _levels(
        y, days,
        lambda t, rate, d: leverage * s[t]
        - (leverage - 1) * rate * d / 360.0 - c * d / 365.0,
    )


def bill_levels(y: list[float], days: list[int], w: float, c_b: float) -> list[float]:
    """The modelled T-bill fund on a traded calendar (§2.5)."""
    return _levels(
        y, days, lambda _t, rate, d: (1.0 - w) * rate * d / 360.0 - c_b * d / 365.0
    )


def splice(
    times: list[str], modelled: list[float],
    real_times: list[str], real_closes: list[float],
) -> tuple[list[tuple[str, float, str]], float]:
    """§3: the modelled series strictly before the real first bar, scaled by
    `real_first / modelled_at_first` so the two meet there multiplicatively;
    the real segment value-for-value. Returns the rows and the scale."""
    first = real_times[0]
    anchor = {t: i for i, t in enumerate(times)}.get(first)
    if anchor is None:
        raise ValueError(f"no modelled bar on the real first date {first}")
    scale = real_closes[0] / modelled[anchor]
    rows = [(times[i], modelled[i] * scale, "synthetic") for i in range(anchor)]
    return rows + [(t, c, "real") for t, c in zip(real_times, real_closes)], scale


def distributions(times: list[str], a: list[float], p: list[float]) -> list[tuple[str, float]]:
    """Implied per-share distributions from a gross pair (TOTAL_RETURN_SPEC §4
    invariant 4): every ex-date and `D_t = P_{t-1} * (1 - R_{t-1}/R_t)`."""
    r = [ai / pi for ai, pi in zip(a, p)]
    return [
        (times[t], p[t - 1] * (1.0 - r[t - 1] / r[t]))
        for t in range(1, len(r))
        if r[t] / r[t - 1] - 1.0 > JUMP_MIN
    ]


def yield_by_year(times: list[str], p: list[float], implied: list[tuple[str, float]]) -> dict[int, float]:
    """§2.2: each year's implied distributions over the prior close."""
    prior = {times[t]: p[t - 1] for t in range(1, len(times))}
    out: dict[int, float] = {}
    for date, d in implied:
        out[int(date[:4])] = out.get(int(date[:4]), 0.0) + d / prior[date]
    return out


def build(parent: Path, gross: Path, w: float, drag, bill_drag, strict: bool = True) -> dict:
    """Read, fit, model and splice. All computation and validation happen here,
    before anything is written — a hard error can never leave a partial dataset
    behind (§3)."""
    rate_times, rate_values = read_close(gross / "macro" / f"{RATE}.csv")
    last_rate = rate_times[-1]
    index_times, index_closes = read_close(gross / f"{INDEX}.csv")
    cal_times, _ = read_close(gross / f"{CALENDAR}.csv")

    real = {s: read_close(parent / f"{s}.csv") for s in (RISK, BILL)}
    for symbol, (times, _) in real.items():
        if strict and times[0] != INCEPTION[symbol]:
            raise ValueError(
                f"{symbol}: first bar {times[0]} is not {INCEPTION[symbol]};"
                " a different inception is a different splice (--force)"
            )

    # --- the fits, each against the parent's own real segment (§3) -----------
    # Both overlaps end at the rate series' last bar: the model has no floating
    # leg past it, and a forward-filled tail would quietly bias the constant.
    overlap, index_on_overlap, risk_on_overlap = aligned(
        (index_times, index_closes), real[RISK], end=last_rate
    )
    risk_fit = fit_drag(
        index_on_overlap, risk_on_overlap,
        carry(rate_times, rate_values, overlap), spans(overlap), LEVERAGE,
    )
    bill_window = window(real[BILL][0], end=last_rate)
    bill_at = dict(zip(*real[BILL]))
    bill_fit = fit_bill(
        [bill_at[t] for t in bill_window],
        carry(rate_times, rate_values, bill_window), spans(bill_window), w,
    )

    c = risk_fit["c"] if drag is None else drag
    c_b = bill_fit["c"] if bill_drag is None else bill_drag
    for name, value, (lo, hi) in (
        ("drag", c, DRAG_BAND), ("bill-drag", c_b, BILL_DRAG_BAND)
    ):
        if not lo <= value <= hi:
            raise ValueError(f"{name} {value:.6f} is outside [{lo}, {hi}]")

    # --- the modelled segments, spliced onto the real ones (§3) --------------
    risk_modelled = leveraged_levels(
        index_closes, carry(rate_times, rate_values, index_times),
        spans(index_times), LEVERAGE, c,
    )
    bill_modelled = bill_levels(
        carry(rate_times, rate_values, cal_times), spans(cal_times), w, c_b
    )

    spliced = {}
    for symbol, times, modelled in (
        (RISK, index_times, risk_modelled), (BILL, cal_times, bill_modelled)
    ):
        rows, scale = splice(times, modelled, *real[symbol])
        spliced[symbol] = {"rows": rows, "scale": scale,
                           "synthetic": sum(1 for r in rows if r[2] == "synthetic")}

    # --- §2.2 / S10, from the gross pair ------------------------------------
    gross_times, gross_adjusted = read_close(gross / f"{INDEX}.csv")
    _, gross_price = read_close(gross / "price" / f"{INDEX}.csv")
    implied = distributions(gross_times, gross_adjusted, gross_price)

    return {
        "symbols": sorted(path.stem for path in parent.glob("*.csv")),
        "pairs": sorted(path.stem for path in (parent / "price").glob("*.csv")),
        "spliced": spliced,
        "fit": {RISK: risk_fit, BILL: bill_fit},
        "drag": {RISK: c, BILL: c_b},
        "overridden": {RISK: drag is not None, BILL: bill_drag is not None},
        "overlap": {RISK: (overlap[0], overlap[-1]), BILL: (bill_window[0], bill_window[-1])},
        "implied": implied,
        "yields": yield_by_year(gross_times, gross_price, implied),
    }


def _table(results: dict) -> list[str]:
    rows = ["| model | overlap | n | c %/yr | used %/yr | beta | daily residual"
            " | max cum. dev. |", "|---|---|---|---|---|---|---|---|"]
    for symbol, label in ((RISK, f"{LEVERAGE}x {INDEX}"), (BILL, f"{RATE} accrual")):
        f = results["fit"][symbol]
        start, end = results["overlap"][symbol]
        beta = f"{f['beta']:.4f}" if "beta" in f else "—"
        rows.append(
            f"| {symbol} — {label} | {start} → {end} | {f['n']} |"
            f" {100 * f['c']:.4f} | {100 * results['drag'][symbol]:.4f} |"
            f" {beta} | {1e4 * f['residual']:.2f} bp |"
            f" {100 * f['max_cum_dev']:.2f}% |"
        )
    return rows


def _splice_table(results: dict) -> list[str]:
    rows = ["| symbol | synthetic rows | first bar | real rows | first real bar | scale |",
            "|---|---|---|---|---|---|"]
    for symbol in (RISK, BILL):
        s = results["spliced"][symbol]
        n = s["synthetic"]
        rows.append(
            f"| {symbol} | {n} | {s['rows'][0][0]} | {len(s['rows']) - n} |"
            f" {s['rows'][n][0]} | {s['scale']!r} |"
        )
    return rows


def _spot_table(results: dict) -> list[str]:
    rows = ["| ex-date | implied | published | delta |", "|---|---|---|---|"]
    by_date = dict(results["implied"])
    for date in sorted(PUBLISHED):
        implied, published = by_date[date], PUBLISHED[date]
        rows.append(
            f"| {date} | {implied:.5f} | {published:.5f} |"
            f" {implied - published:+.5f} |"
        )
    return rows


def render_readme(parent: str, gross: str, w: float, results: dict) -> str:
    """The snapshot README. Names the parent and the gross root by directory
    basename, never from CLI paths, and carries no timestamps — S4 regenerates
    into a temp directory and byte-compares."""
    implied = results["implied"]
    pre = [d for d in implied if d[0] <= "2010-12-31"]
    lines = [
        f"# Synthetic pre-inception snapshot — {default_out(parent)}",
        "",
        f"Derived from the frozen `{parent}` snapshot by `make_synthetic.py`",
        f"(SYNTHETIC_HISTORY_SPEC §2–§4), with the index leg (`{INDEX}`), the accrual",
        f"calendar (`{CALENDAR}`) and the floating rate (`macro/{RATE}`) read from the",
        f"gross root `{gross}` — a swap pays the gross total return in either",
        f"convention. `{RISK}.csv` and `{BILL}.csv` carry columns `time,close,source`:",
        "rows before the real fund's first bar are modelled (`synthetic`), rows from",
        "it on are the parent's own values (`real`), and the two meet",
        "multiplicatively at the splice. Every other `<SYM>.csv` and every",
        f"`price/<SYM>.csv` is byte-copied from the parent; `price/{RISK}.csv` and",
        f"`price/{BILL}.csv` are deliberately absent — a modelled segment has no",
        "unadjusted twin — and `macro/` is not copied.",
        "",
        "**A synthetic root is a falsifier, never a fitting lane**: no parameter is",
        "adopted from a window that contains synthetic bars (§10). Any run whose",
        f"window starts on or after {INCEPTION[RISK]} reads only real bars and",
        "reproduces the parent root's numbers exactly (§4).",
        "",
        "## The models (§2.3, §2.5)",
        "",
        "```",
        f"{LEVERAGE}x fund:     r_t = {LEVERAGE}*s_t"
        f" - {LEVERAGE - 1}*y_(t-1)*d_t/360 - c*d_t/365",
        f"T-bill fund:  r_t = (1 - {w:g})*y_(t-1)*d_t/360 - c_b*d_t/365",
        "```",
        "",
        f"`s` the index total return, `y` {RATE} forward-filled onto the bar calendar",
        "and lagged one row, `d` calendar days since the previous bar. Each constant",
        "is the closed-form mean-residual estimate on log returns, fitted against the",
        f"parent's own real segment, so the model ends the overlap at the real",
        f"series' level exactly. Withholding w = {w:g} enters the bill accrual",
        "proportionally and the leveraged fund not at all — a leveraged fund's own",
        "distributions are tiny and roughly constant, so its constant absorbs them",
        "(§2.5).",
        "",
        "## Fitted constants",
        "",
    ] + _table(results) + [
        "",
        "## The splice",
        "",
    ] + _splice_table(results) + [
        "",
        f"## {INDEX}'s pre-inception distributions (§2.2, S10)",
        "",
        f"{len(pre)} implied ex-dates on {implied[0][0]} → 2010-12-31 from the gross",
        f"pair, the first on {pre[0][0]} — the dot-com stretch is dividend-free by",
        "construction, the one era where a mis-embedded dividend could not matter.",
        "Implied yield by year:",
        "",
        "| year | implied yield |",
        "|---|---|",
    ] + [
        f"| {year} | {100 * results['yields'][year]:.2f}%/yr |"
        for year in sorted(results["yields"]) if year <= 2010
    ] + [
        "",
        "Operator spot check against the issuer's published distribution history:",
        "",
    ] + _spot_table(results)
    return "\n".join(lines) + "\n"


def write_dataset(dst: Path, src: Path, results: dict, readme: str) -> None:
    (dst / "price").mkdir(parents=True, exist_ok=True)
    for symbol in results["symbols"]:
        if symbol in results["spliced"]:
            rows = "\n".join(
                f"{t},{c!r},{source}" for t, c, source in results["spliced"][symbol]["rows"]
            )
            (dst / f"{symbol}.csv").write_text(f"time,close,source\n{rows}\n")
            continue
        shutil.copyfile(src / f"{symbol}.csv", dst / f"{symbol}.csv")
    for symbol in results["pairs"]:
        if symbol in results["spliced"]:
            continue  # a modelled segment has no unadjusted twin (§3)
        shutil.copyfile(src / "price" / f"{symbol}.csv", dst / "price" / f"{symbol}.csv")
    (dst / "README.md").write_text(readme)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "parent", type=Path,
        help="parent dataset root; its TQQQ/BIL are the real segments",
    )
    parser.add_argument(
        "--gross", type=Path, required=True,
        help=f"gross root supplying {INDEX}, {CALENDAR} and macro/{RATE}",
    )
    parser.add_argument(
        "--withholding", type=float, required=True,
        help="the parent's withholding rate; must match its basename",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="output dataset root (default: the parent with -syn inserted)",
    )
    parser.add_argument(
        "--drag", type=float, default=None,
        help="override the fitted leveraged-fund constant (decimal, per year)",
    )
    parser.add_argument(
        "--bill-drag", type=float, default=None,
        help="override the fitted T-bill constant (decimal, per year)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="write into an existing --out, and accept an unexpected inception",
    )
    args = parser.parse_args(argv)

    w = args.withholding
    if not 0.0 <= w < 1.0:
        parser.error(f"--withholding must be in [0, 1): {w}")
    expected = 0.15 if "-net15" in args.parent.name else 0.0
    if w != expected:
        parser.error(
            f"--withholding {w:g} does not match parent {args.parent.name}"
            f" (expected {expected:g})"
        )
    dst = args.out or args.parent.with_name(default_out(args.parent.name))
    if dst.exists() and not args.force:
        parser.error(f"{dst} exists; pass --force to overwrite")

    results = build(args.parent, args.gross, w, args.drag, args.bill_drag,
                    strict=not args.force)
    write_dataset(
        dst, args.parent, results,
        render_readme(args.parent.name, args.gross.name, w, results),
    )

    print("\n".join(_table(results)))
    print("\n".join(_splice_table(results)))
    print(f"Saved {dst}")


if __name__ == "__main__":
    main()
