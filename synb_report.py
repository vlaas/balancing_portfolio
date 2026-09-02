"""Phase-2 synthesis arm SYNB — BTAL's slot from two UCITS ETFs (EU_SUBSTITUTE_SPEC §5).

SYNB is the fixed sleeve blend {MVEA: 1 - w_S, XSPS: w_S} — long min-vol, short
S&P via the -1x daily-swap ETF — rebalanced monthly with the rest of the
portfolio. This report solves w_S* for zero portfolio beta against CSPX on the
frozen estimation window (month-ends 2020-05 → 2023-12), quantizes it to the
registered grid {0.40, 0.45, 0.50}, and runs the pre-registered falsifiers
against BTAL on the common window 2020-05 → last bar for every grid point:
F1 the proxy bar (monthly correlation with BTAL), F2 the insurance bar (mean
SYNB return over the worst-decile CNDX months), F3 the E4 bound (peak-to-
trough over 2020-09-01 → 2021-03-31 against BTAL's) and F4 the decay
documentation of the daily-reset short leg. Verdict per arm: PROXY, ARM-ONLY
or FAIL (§5.3). Nothing else is fitted; the windows and the grid are frozen
here.

Run: uv run synb_report.py --data tests/data/2026-09-02-net15-usd [--out results/synb]
"""

import argparse
import datetime as dt
from pathlib import Path

import polars as pl

import results_json
from episode_report import episode_slice
from prices import _read_close
from regime_report import month_ends

LONG, SHORT, BENCH, PROXY, SIGNAL, INDEX = "MVEA", "XSPS", "CSPX", "BTAL", "CNDX", "SPY"
GRID = (0.40, 0.45, 0.50)
ESTIMATION = ("2020-05-01", "2023-12-31")  # month-end rows inside: 44, returns: 43
WINDOW_START = "2020-05-01"                # falsifiers: month-ends from here to the last bar
E4_WINDOW = ("2020-09-01", "2021-03-31")   # §5.3 F3 — not episode_report's E4 recovery window
F1_MIN, F3_MAX = 0.50, 1.5


def _date(text: str) -> dt.date:
    return dt.date.fromisoformat(text)


def frame(data_dir: Path, *symbols: str) -> pl.DataFrame:
    """The symbols' common daily calendar, one close column per symbol."""
    out = None
    for symbol in symbols:
        closes = _read_close(data_dir, symbol).rename({"close": symbol})
        out = closes if out is None else out.join(closes, on="date", how="inner")
    return out.sort("date")


def month_end_rows(daily: pl.DataFrame, start: str, end: str | None = None) -> pl.DataFrame:
    """The month-end closes inside [start, end] — filtered *before*
    differencing, so the first return starts at the window's first month-end."""
    ends = month_ends(daily).filter(pl.col("date") >= _date(start))
    return ends if end is None else ends.filter(pl.col("date") <= _date(end))


def returns(ends: pl.DataFrame) -> pl.DataFrame:
    """Simple month-end-to-month-end returns (portfolio arithmetic, unlike the
    log returns of the overlap regressions), dated by the month-end they end on."""
    symbols = [c for c in ends.columns if c != "date"]
    return ends.select("date", *[pl.col(s).pct_change() for s in symbols]).slice(1)


def monthly_returns(daily: pl.DataFrame, start: str, end: str | None = None) -> pl.DataFrame:
    return returns(month_end_rows(daily, start, end))


def beta(r: pl.DataFrame, symbol: str) -> float:
    return r.select(pl.cov(symbol, BENCH) / pl.var(BENCH)).item()


def solve_w(r: pl.DataFrame) -> float:
    """w with zero beta of (1 - w) MVEA + w XSPS against CSPX:
    w* = cov(rM, rC) / (cov(rM, rC) - cov(rX, rC))."""
    c_long, c_short = r.select(pl.cov(LONG, BENCH), pl.cov(SHORT, BENCH)).row(0)
    return c_long / (c_long - c_short)


def quantize(w: float) -> float:
    """The nearest grid point; an exact tie resolves to the lower point."""
    return min(GRID, key=lambda g: abs(g - w))


def synb(r: pl.DataFrame, w: float) -> pl.Series:
    return ((1 - w) * r[LONG] + w * r[SHORT]).alias("synb")


def f1(r: pl.DataFrame, w: float) -> float:
    return pl.DataFrame({"synb": synb(r, w), "btal": r[PROXY]}).select(pl.corr("synb", "btal")).item()


def f2(r: pl.DataFrame, w: float) -> tuple[float, int]:
    """Mean SYNB return over the k = floor(n / 10) worst CNDX months."""
    k = max(1, len(r) // 10)
    worst = r.with_columns(synb(r, w)).sort(SIGNAL).head(k)
    return worst["synb"].mean(), k


def blend_index(daily: pl.DataFrame, w: float) -> pl.DataFrame:
    """The daily index of the monthly-rebalanced blend: the legs are bought
    at (1 - w, w) on the first bar and at every month-end, and held between.
    On month-ends it equals the product of (1 + (1 - w) rM + w rX)."""
    long, short = daily[LONG].to_list(), daily[SHORT].to_list()
    ends = set(month_ends(daily)["date"].to_list())
    value, long0, short0, index = 1.0, long[0], short[0], []
    for date, m, x in zip(daily["date"].to_list(), long, short):
        level = value * ((1 - w) * m / long0 + w * x / short0)
        index.append(level)
        if date in ends:
            value, long0, short0 = level, m, x
    return pl.DataFrame({"date": daily["date"], "index": index})


def f3(data_dir: Path, w: float) -> tuple[float, float]:
    """In-window peak-to-trough of SYNB and of BTAL over E4_WINDOW (both from
    the window's own running peak, `episode_report.episode_slice`)."""
    synb_dd = episode_slice(blend_index(frame(data_dir, LONG, SHORT), w), *E4_WINDOW)[1]
    btal = _read_close(data_dir, PROXY).rename({"close": "index"})
    return synb_dd, episode_slice(btal, *E4_WINDOW)[1]


def f4(r: pl.DataFrame) -> list[dict]:
    """Per calendar year: the monthly-held XSPS leg against a monthly -1x SPY."""
    rows = []
    for (year,), months in r.group_by(r["date"].dt.year(), maintain_order=True):
        xsps = (1 + months[SHORT]).product() - 1
        short = (1 - months[INDEX]).product() - 1
        rows.append({"year": int(year), "months": len(months), "xsps_pct": xsps * 100,
                     "short_spy_pct": short * 100, "shortfall_pp": (xsps - short) * 100})
    return rows


def arm_verdict(f1_ok: bool, f2_ok: bool, f3_ok: bool) -> str:
    if not (f2_ok and f3_ok):
        return "FAIL"
    return "PROXY" if f1_ok else "ARM-ONLY"


def report(data_dir: Path) -> dict:
    daily = frame(data_dir, LONG, SHORT, BENCH, PROXY, SIGNAL, INDEX)
    est_ends = month_end_rows(daily, *ESTIMATION)
    est = returns(est_ends)
    w_star = solve_w(est)
    chosen = quantize(w_star)
    ends = month_end_rows(daily, WINDOW_START)
    r = returns(ends)
    arms = {}
    for w in GRID:
        corr = f1(r, w)
        mean, k = f2(r, w)
        synb_dd, btal_dd = f3(data_dir, w)
        ratio = synb_dd / btal_dd
        ok = (corr >= F1_MIN, mean > 0, ratio <= F3_MAX)
        arms[f"{w:.2f}"] = {
            "w": w, "primary": w == chosen,
            "f1_corr": corr, "f1": ok[0],
            "f2_mean_pp": mean * 100, "f2_k": k, "f2": ok[1],
            "f3_synb_dd": synb_dd, "f3_btal_dd": btal_dd, "f3_ratio": ratio, "f3": ok[2],
            "verdict": arm_verdict(*ok),
        }
    return {
        "root": data_dir.name,
        "estimation": {
            "first_month_end": est_ends["date"][0].isoformat(),
            "last_month_end": est_ends["date"][-1].isoformat(),
            "n_month_ends": len(est_ends), "n_returns": len(est),
            "beta_long": beta(est, LONG), "beta_short": beta(est, SHORT),
            "w_star": w_star, "chosen": chosen,
        },
        "window": {
            "first_month_end": ends["date"][0].isoformat(),
            "last_month_end": ends["date"][-1].isoformat(),
            "n_month_ends": len(ends), "n_returns": len(r), "e4": list(E4_WINDOW),
        },
        "arms": arms,
        "f4": f4(r),
    }


def render_md(payload: dict) -> str:
    e, w = payload["estimation"], payload["window"]
    lines = [
        f"# SYNB — the synthesis arm on `{payload['root']}` (EU_SUBSTITUTE_SPEC §5)",
        "",
        f"Estimation window (§5.2): month-ends {e['first_month_end']} → {e['last_month_end']}, "
        f"{e['n_month_ends']} month-ends, {e['n_returns']} monthly returns; "
        f"β(MVEA, CSPX) = {e['beta_long']:.4f}, "
        f"β(XSPS, CSPX) = {e['beta_short']:.4f}; **w_S\\* = {e['w_star']:.4f} → {e['chosen']:.2f}** "
        f"(nearest of {', '.join(f'{g:.2f}' for g in GRID)}).",
        "",
        f"Falsifier window (§5.3): month-ends {w['first_month_end']} → {w['last_month_end']}, "
        f"{w['n_returns']} monthly returns; E4 bound over "
        f"{w['e4'][0]} → {w['e4'][1]}.",
        "",
        "| w_S | primary | F1 corr(SYNB, BTAL) ≥ 0.50 | F2 mean over worst-decile CNDX months (k) > 0 "
        "| F3 SYNB / BTAL peak-to-trough, ratio ≤ 1.5 | verdict |",
        "|---|---|---|---|---|---|",
    ]
    for key, a in payload["arms"].items():
        lines.append(
            f"| {key} | {'**yes**' if a['primary'] else 'sens.'} "
            f"| {a['f1_corr']:+.3f} {'✅' if a['f1'] else '❌'} "
            f"| {a['f2_mean_pp']:+.2f} pp (k = {a['f2_k']}) {'✅' if a['f2'] else '❌'} "
            f"| {100 * a['f3_synb_dd']:+.2f} % / {100 * a['f3_btal_dd']:+.2f} %, "
            f"{a['f3_ratio']:.2f} {'✅' if a['f3'] else '❌'} | **{a['verdict']}** |"
        )
    lines += ["", "## F4 — the daily-reset short leg, monthly-held XSPS against −1 × SPY "
              "(documentation, no bar)", "",
              "| year | months | XSPS % | −1 × SPY % | shortfall pp |", "|---|---|---|---|---|"]
    for y in payload["f4"]:
        lines.append(f"| {y['year']} | {y['months']} | {y['xsps_pct']:+.2f} "
                     f"| {y['short_spy_pct']:+.2f} | {y['shortfall_pp']:+.2f} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="the decision root")
    parser.add_argument("--out", type=Path, default=Path("results/synb"),
                        help="artefact directory (default: results/synb)")
    args = parser.parse_args(argv)

    payload = results_json._round(report(args.data))
    md = render_md(payload)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "synb.json").write_text(results_json.dumps(payload))
    (args.out / "synb.md").write_text(md)
    print(md, end="")
    print(f"Saved {args.out}/{{synb.json,synb.md}}")


if __name__ == "__main__":
    main()
