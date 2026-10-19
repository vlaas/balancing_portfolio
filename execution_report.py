"""Execution robustness — the bundle when it trades off the month-end and off the close (EXECUTION_ROBUSTNESS_SPEC).

`jitter` moves every month's session — deposit and rebalance together — by up to
±N trading days around the month-end (§3): `--draws` random calendars, each one
shared by every strategy so the comparison with the benchmark is paired, plus
the 2N + 1 fixed-offset calendars of the scan, whose d = 0 is the canonical run.
`fills` executes every trade at an adverse fraction α of the bar's one-sided
range (§4): buys at C·(1 + α(H/C − 1)), sells at C·(1 − α(1 − L/C)), the ratios
taken from the root's `unadjusted/` bars. Deterministic: the same inputs write
byte-identical artefacts.

Run: uv run execution_report.py jitter --spec SPEC --data ROOT [--days 10]
         [--draws 500] [--seed 20261020] [--out DIR]
     uv run execution_report.py fills --spec SPEC --data ROOT
         [--alpha 0 0.25 0.5 1] [--out DIR]
"""

import argparse
import csv
import io
import random
import shlex
import statistics
import sys
from pathlib import Path

import polars as pl

import results_json
from bundles import Bundle
from main import collect_indicators
from prices import load_prices
from simulate import simulate
from spec import build_bundle, load_spec
from stats import summary, twr
from sweep import _quantile

# Higher is better for every metric — a drawdown is negative.
METRICS = ("cagr", "xirr", "max_drawdown", "calmar", "sharpe", "final_value")
QUANTILES = (("p5", 0.05), ("p10", 0.10), ("p25", 0.25), ("p50", 0.50),
             ("p75", 0.75), ("p90", 0.90), ("p95", 0.95))
HEADLINE_ALPHA = 0.5  # §4.2: the "reasonable worst case"
P_CALMAR_MIN = 0.90   # §10.1


# --- Shared --------------------------------------------------------------------


def load(spec: dict, data_dir: Path) -> tuple[Bundle, pl.DataFrame]:
    """The bundle and its one price frame, loaded as `main.run_bundle` loads it."""
    bundle = build_bundle(spec)
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
    return bundle, prices


def run(prices: pl.DataFrame, st, config, fill=None) -> tuple[dict, pl.DataFrame]:
    """One simulation: the §6 metrics and the transaction log."""
    curve, trades, allocations = simulate(prices, st, config, fill)
    stats = summary(curve, twr(curve), allocations, trades)
    return {m: stats[m] for m in METRICS} | {"total_fees": stats["total_fees"]}, trades


def provenance(spec_path: Path, data_dir: Path, prices: pl.DataFrame, bundle: Bundle) -> dict:
    """What a reader needs to rerun the artefact — no timestamp, no HEAD sha."""
    status = results_json.git("status", "--porcelain", "--", str(data_dir))
    return {
        "spec": str(spec_path),
        "root": str(data_dir),
        "root_commit": results_json.git("log", "-1", "--format=%h", "--", str(data_dir)),
        "root_dirty": None if status is None else status != "",
        "start": prices["date"][0].isoformat(),
        "end": prices["date"][-1].isoformat(),
        "trading_days": prices.height,
        "month_ends": int(prices["is_rebalance_day"].sum()),
        "cost_bps": bundle.config.cost_bps,
        "cash_yield": bundle.config.cash_yield,
    }


def _pct(x: float) -> str:
    return f"{100 * x:+.2f} %"


def _header(title: str, payload: dict) -> list[str]:
    d = payload["data"]
    commit = d["root_commit"] or "untracked"
    dirty = " (dirty)" if d["root_dirty"] else ""
    costs = d["cost_bps"]
    cost_text = (
        ", ".join(f"{s} {v:g}" for s, v in costs.items())
        if isinstance(costs, dict) else f"{costs:g} flat"
    )
    return [
        f"# {title}: `{Path(d['spec']).name}`",
        "",
        "Reproduce:",
        "",
        "```",
        payload["command"],
        "```",
        "",
        f"- Data: `{d['root']}` @ `{commit}`{dirty}, {d['start']} → {d['end']}, "
        f"{d['trading_days']} trading days, {d['month_ends']} monthly sessions",
        f"- Costs: `cost_bps` per side {cost_text}; `cash_yield` {d['cash_yield']:g}",
        f"- Benchmark (paired comparisons): {payload['benchmark']}",
    ]


# --- jitter (§3) -------------------------------------------------------------------


def calendar(anchors: list[int], offsets: list[int], n_rows: int) -> tuple[list[int], int, int]:
    """The session rows: each month-end row moved by its offset, clamped into
    [1, n_rows - 2] — day 0 is the initial investment, the last row values
    only — then made strictly increasing (a row at or before its predecessor
    moves to predecessor + 1). Returns (rows, clamps, bumps)."""
    rows: list[int] = []
    clamps = bumps = 0
    for anchor, d in zip(anchors, offsets, strict=True):
        row = min(max(anchor + d, 1), n_rows - 2)
        clamps += row != anchor + d
        if rows and row <= rows[-1]:
            row = rows[-1] + 1
            bumps += 1
        rows.append(row)
    if rows and rows[-1] > n_rows - 2:
        raise ValueError(
            f"calendar: {len(rows)} sessions do not fit before the last row ({n_rows - 1})"
        )
    return rows, clamps, bumps


def draw_offsets(months: int, days: int, draws: int, seed: int) -> list[list[int]]:
    """`draws` offset vectors, uniform on [-days, days], one Random consumed in
    draw order then month order — the first k draws of any run are a k-draw run."""
    rng = random.Random(seed)
    return [[rng.randint(-days, days) for _ in range(months)] for _ in range(draws)]


def with_sessions(prices: pl.DataFrame, rows: list[int]) -> pl.DataFrame:
    mask = [False] * prices.height
    for row in rows:
        mask[row] = True
    return prices.with_columns(is_rebalance_day=pl.Series(mask, dtype=pl.Boolean))


def distribution(xs: list[float], canonical: float) -> dict:
    below = sum(x < canonical for x in xs)
    ties = sum(x == canonical for x in xs)
    return {
        "canonical": canonical,
        "pctile": (below + ties / 2) / len(xs),
        "mean": statistics.fmean(xs),
        "sd": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        "min": min(xs),
        **{name: _quantile(xs, p) for name, p in QUANTILES},
        "max": max(xs),
    }


def jitter_report(
    spec: dict, spec_path: Path, data_dir: Path, days: int, draws: int, seed: int
) -> tuple[dict, list[dict]]:
    """(payload, per-draw rows)."""
    bundle, prices = load(spec, data_dir)
    for st in bundle.strategies:
        if st.rebalance is not None:
            raise SystemExit(
                f"{st.label}: has a rebalance cadence; jitter moves only the month-end"
                " sessions (EXECUTION_ROBUSTNESS_SPEC §3)"
            )
    labels = [st.label for st in bundle.strategies]
    bench = labels[-1]
    anchors = prices.with_row_index().filter("is_rebalance_day")["index"].to_list()

    def run_calendar(offsets: list[int]) -> tuple[dict, int, int]:
        rows, clamps, bumps = calendar(anchors, offsets, prices.height)
        frame = with_sessions(prices, rows)
        return {st.label: run(frame, st, bundle.config)[0] for st in bundle.strategies}, clamps, bumps

    scan = []
    for d in range(-days, days + 1):
        metrics, clamps, bumps = run_calendar([d] * len(anchors))
        scan.append({"d": d, "clamps": clamps, "bumps": bumps, "metrics": metrics})
    canonical = next(s["metrics"] for s in scan if s["d"] == 0)

    rows = []
    for i, offsets in enumerate(draw_offsets(len(anchors), days, draws, seed)):
        metrics, clamps, bumps = run_calendar(offsets)
        rows += [
            {"draw": i, "label": label, **metrics[label], "clamps": clamps, "bumps": bumps}
            for label in labels
        ]

    by = {label: [r for r in rows if r["label"] == label] for label in labels}
    dist = {
        label: {m: distribution([r[m] for r in by[label]], canonical[label][m]) for m in METRICS}
        for label in labels
    }
    paired = {
        label: {
            m: sum(a[m] > b[m] for a, b in zip(by[label], by[bench])) / draws for m in METRICS
        }
        for label in labels[:-1]
    }
    best = {
        label: {
            m: sum(
                max(labels, key=lambda lab: by[lab][i][m]) == label for i in range(draws)
            ) / draws
            for m in ("cagr", "calmar")
        }
        for label in labels
    }
    readout = {
        label: "TIMING-ROBUST"
        if dist[label]["calmar"]["p10"] <= canonical[label]["calmar"] <= dist[label]["calmar"]["p90"]
        and paired[label]["calmar"] >= P_CALMAR_MIN
        else "TIMING-FRAGILE"
        for label in labels[:-1]
    }
    draw_edits = rows[:: len(labels)]
    payload = {
        "data": provenance(spec_path, data_dir, prices, bundle),
        "params": {"days": days, "draws": draws, "seed": seed},
        "benchmark": bench,
        "strategies": labels,
        "calendar": {
            "draws_with_clamps": sum(r["clamps"] > 0 for r in draw_edits),
            "mean_clamps": statistics.fmean(r["clamps"] for r in draw_edits),
            "draws_with_bumps": sum(r["bumps"] > 0 for r in draw_edits),
            "max_bumps": max(r["bumps"] for r in draw_edits),
        },
        "scan": scan,
        "distribution": dist,
        "paired": paired,
        "best": best,
        "readout": readout,
    }
    return payload, rows


def render_jitter(payload: dict) -> str:
    p, c = payload["params"], payload["calendar"]
    labels, bench = payload["strategies"], payload["benchmark"]
    dist, paired = payload["distribution"], payload["paired"]
    lines = _header("Execution robustness — rebalance-date jitter", payload) + [
        f"- Jitter: each month's session (deposit + rebalance) moved by a uniform "
        f"offset in ±{p['days']} trading days; {p['draws']} draws, seed {p['seed']}; "
        "one calendar per draw for every strategy",
        f"- Calendar edits: clamps in {c['draws_with_clamps']} of {p['draws']} draws "
        f"(mean {c['mean_clamps']:.2f} per draw), bumps in {c['draws_with_bumps']} "
        f"(at most {c['max_bumps']} in one draw)",
        "",
        "## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1)",
        "",
        f"| strategy | canonical Calmar | p10 | p90 | P(Calmar > {bench}) | read-out |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label in labels[:-1]:
        d = dist[label]["calmar"]
        lines.append(
            f"| {label} | {d['canonical']:.3f} | {d['p10']:.3f} | {d['p90']:.3f} "
            f"| {paired[label]['calmar']:.3f} | **{payload['readout'][label]}** |"
        )
    for metric, title, fmt in (
        ("cagr", "CAGR (TWR)", _pct),
        ("calmar", "Calmar", lambda x: f"{x:.3f}"),
        ("max_drawdown", "Max drawdown", _pct),
        ("xirr", "XIRR", _pct),
    ):
        lines += [
            "",
            f"## {title} across draws",
            "",
            "| strategy | canonical | pctile | mean | sd | min | p5 | p25 | p50 | p75 | p95 | max |",
            "|---|" + "---:|" * 11,
        ]
        for label in labels:
            d = dist[label][metric]
            sd = fmt(d["sd"]).lstrip("+")
            cells = [fmt(d[k]) for k in ("canonical",)] + [f"{d['pctile']:.2f}", fmt(d["mean"]), sd] + [
                fmt(d[k]) for k in ("min", "p5", "p25", "p50", "p75", "p95", "max")
            ]
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines += [
        "",
        f"## Paired against {bench} — share of draws the strategy is ahead",
        "",
        "Max drawdown: ahead = shallower. Best of all: share of draws the strategy "
        "ranks first among every row, the benchmark included.",
        "",
        "| strategy | CAGR | XIRR | max drawdown | Calmar | Sharpe | best CAGR | best Calmar |",
        "|---|" + "---:|" * 7,
    ]
    for label in labels:
        b = payload["best"][label]
        cells = (
            [f"{paired[label][m]:.3f}" for m in ("cagr", "xirr", "max_drawdown", "calmar", "sharpe")]
            if label in paired else ["·"] * 5
        )
        lines.append(
            f"| {label} | " + " | ".join(cells) + f" | {b['cagr']:.3f} | {b['calmar']:.3f} |"
        )
    for metric, title, fmt in (("calmar", "Calmar", lambda x: f"{x:.3f}"), ("cagr", "CAGR", _pct)):
        lines += [
            "",
            f"## Fixed-offset scan — {title}, every month's session moved by d trading days",
            "",
            "| d | " + " | ".join(labels) + " | clamps | bumps |",
            "|---:|" + "---:|" * (len(labels) + 2),
        ]
        for s in payload["scan"]:
            cells = [fmt(s["metrics"][label][metric]) for label in labels]
            mark = " (canonical)" if s["d"] == 0 else ""
            lines.append(
                f"| {s['d']:+d}{mark} | " + " | ".join(cells) + f" | {s['clamps']} | {s['bumps']} |"
            )
    return "\n".join(lines) + "\n"


def draws_csv(rows: list[dict]) -> str:
    fields = ["draw", "label", *METRICS, "total_fees", "clamps", "bumps"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(results_json._round(rows))
    return out.getvalue()


# --- fills (§4) ----------------------------------------------------------------------


def with_ranges(prices: pl.DataFrame, data_dir: Path, symbols: list[str]) -> tuple[pl.DataFrame, dict]:
    """Join `SYM:HR` = H/C and `SYM:LR` = L/C from the root's unadjusted bars —
    scale-free, so they apply to any adjusted close (§2.2). A day with no bar
    gets 1.0 (a close fill); returns the frame and the per-symbol count of those."""
    missing = {}
    for symbol in symbols:
        path = data_dir / "unadjusted" / f"{symbol}.csv"
        if not path.is_file():
            raise SystemExit(f"{symbol}: no {path} — fills need the root's unadjusted OHLC bars")
        bars = pl.read_csv(
            path,
            columns=["time", "high", "low", "close"],
            schema_overrides={c: pl.Float64 for c in ("high", "low", "close")},
            try_parse_dates=True,
        ).select(
            pl.col("time").alias("date"),
            (pl.col("high") / pl.col("close")).alias(f"{symbol}:HR"),
            (pl.col("low") / pl.col("close")).alias(f"{symbol}:LR"),
        )
        prices = prices.join(bars, on="date", how="left")
        missing[symbol] = prices[f"{symbol}:HR"].null_count()
        prices = prices.with_columns(pl.col(f"{symbol}:HR", f"{symbol}:LR").fill_null(1.0))
    return prices, missing


def adverse(alpha: float):
    """§4.1: buys at C·(1 + α(H/C − 1)), sells at C·(1 − α(1 − L/C))."""

    def fill(row: dict, asset: str, delta: int) -> float:
        close = row[asset]
        if delta > 0:
            return close * (1.0 + alpha * (row[f"{asset}:HR"] - 1.0))
        return close * (1.0 - alpha * (1.0 - row[f"{asset}:LR"]))

    return fill


def slippage(trades: pl.DataFrame, closes: dict) -> list[tuple[str, str, float, float]]:
    """(asset, side, |fill − close| · shares, close · shares) per BUY/SELL."""
    out = []
    for t in trades.filter(pl.col("action").is_in(["BUY", "SELL"])).iter_rows(named=True):
        close = closes[(t["date"], t["asset"])]
        out.append((t["asset"], t["action"], abs(t["price"] - close) * t["shares"], close * t["shares"]))
    return out


def break_even(alphas: list[float], edges: list[float]) -> float | None:
    """The α where the edge first reaches 0, linear between levels; None if it never does."""
    for i, edge in enumerate(edges):
        if edge <= 0:
            if i == 0:
                return alphas[0]
            a0, e0 = alphas[i - 1], edges[i - 1]
            return a0 + e0 * (alphas[i] - a0) / (e0 - edge)
    return None


def fills_report(spec: dict, spec_path: Path, data_dir: Path, alphas: list[float]) -> dict:
    alphas = sorted(set(alphas))
    bundle, prices = load(spec, data_dir)
    labels = [st.label for st in bundle.strategies]
    bench = labels[-1]
    traded = sorted({s for st in bundle.strategies for s in st.weights})
    prices, missing = with_ranges(prices, data_dir, traded)
    closes = {
        (date, symbol): close
        for symbol in traded
        for date, close in zip(prices["date"], prices[symbol])
    }

    rows: dict[str, dict] = {label: {} for label in labels}
    by_symbol = {}
    for alpha in alphas:
        key = f"{alpha:g}"
        legs: dict[tuple[str, str], list[float]] = {}
        for st in bundle.strategies:
            metrics, trades = run(prices, st, bundle.config, adverse(alpha))
            slip = slippage(trades, closes)
            notional = sum(n for *_, n in slip)
            rows[st.label][key] = metrics | {
                "slippage": sum(s for _, _, s, _ in slip),
                "close_notional": notional,
                "slippage_bps": sum(s for _, _, s, _ in slip) / notional * 1e4 if notional else 0.0,
            }
            for asset, side, s, n in slip:
                acc = legs.setdefault((asset, side), [0.0, 0.0])
                acc[0] += s
                acc[1] += n
        by_symbol[key] = {
            symbol: {
                side.lower() + "_bps": legs[(symbol, side)][0] / legs[(symbol, side)][1] * 1e4
                for side in ("BUY", "SELL")
                if (symbol, side) in legs
            }
            for symbol in traded
        }

    keys = [f"{a:g}" for a in alphas]
    edge = {
        label: {k: {m: rows[label][k][m] - rows[bench][k][m] for m in ("cagr", "calmar")} for k in keys}
        for label in labels[:-1]
    }
    payload = {
        "data": provenance(spec_path, data_dir, prices, bundle) | {"missing_bars": missing},
        "params": {"alpha": alphas, "headline_alpha": HEADLINE_ALPHA},
        "benchmark": bench,
        "strategies": labels,
        "rows": rows,
        "edge": edge,
        "break_even": {
            label: {m: break_even(alphas, [edge[label][k][m] for k in keys]) for m in ("cagr", "calmar")}
            for label in labels[:-1]
        },
        "by_symbol": by_symbol,
    }
    headline = f"{HEADLINE_ALPHA:g}"
    if headline in keys:
        payload["readout"] = {
            label: "FILL-ROBUST" if edge[label][headline]["cagr"] > 0 else "FILL-FRAGILE"
            for label in labels[:-1]
        }
    return payload


def render_fills(payload: dict) -> str:
    labels, bench = payload["strategies"], payload["benchmark"]
    keys = [f"{a:g}" for a in payload["params"]["alpha"]]
    base = keys[0]
    missing = {s: n for s, n in payload["data"]["missing_bars"].items() if n}
    lines = _header("Execution robustness — adverse intraday fills", payload) + [
        "- Fill model (§4.1): buy at C·(1 + α(H/C − 1)), sell at C·(1 − α(1 − L/C)), "
        "ratios from the root's `unadjusted/` bars; `cost_bps` charged on top; sizing "
        "and valuation at the close",
        f"- α levels: {', '.join(keys)} — 0.5 the headline reasonable worst case, "
        "1 the literal high/low (a bound, not a scenario)",
        f"- Days with no unadjusted bar (filled at the close): "
        f"{', '.join(f'{s} {n}' for s, n in missing.items()) if missing else 'none'}",
    ]
    if "readout" in payload:
        h = f"{payload['params']['headline_alpha']:g}"
        lines += [
            "",
            f"## Read-out (EXECUTION_ROBUSTNESS_SPEC §10.1, α = {h})",
            "",
            f"| strategy | CAGR edge over {bench} at α = {h} | break-even α, CAGR "
            "| break-even α, Calmar | read-out |",
            "|---|---:|---:|---:|---|",
        ]
        for label in labels[:-1]:
            be = payload["break_even"][label]
            cells = [
                "> max α" if be[m] is None else f"{be[m]:.2f}" for m in ("cagr", "calmar")
            ]
            lines.append(
                f"| {label} | {100 * payload['edge'][label][h]['cagr']:+.2f} pp "
                f"| {cells[0]} | {cells[1]} | **{payload['readout'][label]}** |"
            )
    lines += [
        "",
        "## Strategy × α",
        "",
        f"Δ columns against α = {base}. Slippage = Σ |fill − close| · shares; "
        "bps of the close notional traded.",
        "",
        "| strategy | α | final value | CAGR | Δ CAGR | XIRR | max drawdown | Calmar | Δ Calmar "
        "| Sharpe | fees | slippage | slippage bps |",
        "|---|---:|" + "---:|" * 11,
    ]
    for label in labels:
        r0 = payload["rows"][label][base]
        for k in keys:
            r = payload["rows"][label][k]
            lines.append(
                f"| {label} | {k} | ${r['final_value']:,.2f} | {_pct(r['cagr'])} "
                f"| {100 * (r['cagr'] - r0['cagr']):+.2f} pp | {_pct(r['xirr'])} "
                f"| {_pct(r['max_drawdown'])} | {r['calmar']:.3f} "
                f"| {r['calmar'] - r0['calmar']:+.3f} | {r['sharpe']:.2f} "
                f"| ${r['total_fees']:,.2f} | ${r['slippage']:,.2f} | {r['slippage_bps']:.1f} |"
            )
    lines += [
        "",
        f"## Edge over {bench} at the same α",
        "",
        "| strategy | " + " | ".join(f"CAGR α={k}" for k in keys) + " | "
        + " | ".join(f"Calmar α={k}" for k in keys) + " |",
        "|---|" + "---:|" * (2 * len(keys)),
    ]
    for label in labels[:-1]:
        e = payload["edge"][label]
        lines.append(
            f"| {label} | "
            + " | ".join(f"{100 * e[k]['cagr']:+.2f} pp" for k in keys) + " | "
            + " | ".join(f"{e[k]['calmar']:+.3f}" for k in keys) + " |"
        )
    lines += [
        "",
        "## Realised slippage by symbol and side (bp of close notional, every strategy's trades)",
        "",
        "| symbol | " + " | ".join(f"buy α={k} | sell α={k}" for k in keys) + " |",
        "|---|" + "---:|" * (2 * len(keys)),
    ]
    for symbol in payload["by_symbol"][base]:
        cells = []
        for k in keys:
            s = payload["by_symbol"][k][symbol]
            cells += [f"{s['buy_bps']:.1f}" if "buy_bps" in s else "·",
                      f"{s['sell_bps']:.1f}" if "sell_bps" in s else "·"]
        lines.append(f"| {symbol} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# --- CLI -----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("jitter", "fills"):
        p = sub.add_parser(mode)
        p.add_argument("--spec", type=Path, required=True)
        p.add_argument("--data", type=Path, required=True)
        p.add_argument("--out", type=Path, help="artefact directory (default: results/<spec stem>)")
        if mode == "jitter":
            p.add_argument("--days", type=int, default=10, help="±N trading days (default 10)")
            p.add_argument("--draws", type=int, default=500, help="random calendars (default 500)")
            p.add_argument("--seed", type=int, default=20261020)
        else:
            p.add_argument("--alpha", type=float, nargs="+", default=[0.0, 0.25, 0.5, 1.0],
                           help="adverse fractions of the one-sided range (default 0 0.25 0.5 1)")
    args = parser.parse_args(argv)
    if args.mode == "jitter" and (args.days < 0 or args.draws < 1):
        parser.error("--days must be >= 0 and --draws >= 1")
    if args.mode == "fills" and any(not 0.0 <= a <= 1.0 for a in args.alpha):
        parser.error("--alpha values must lie in [0, 1]")

    out = args.out or Path("results") / args.spec.stem
    spec = load_spec(args.spec)
    command = shlex.join(["uv", "run", "execution_report.py", *argv])
    if args.mode == "jitter":
        payload, rows = jitter_report(spec, args.spec, args.data, args.days, args.draws, args.seed)
        payload = results_json._round({"command": command} | payload)
        md = render_jitter(payload)
        files = {"jitter.json": results_json.dumps(payload), "jitter.md": md,
                 "jitter_draws.csv": draws_csv(rows)}
    else:
        payload = results_json._round({"command": command} | fills_report(spec, args.spec, args.data, args.alpha))
        md = render_fills(payload)
        files = {"fills.json": results_json.dumps(payload), "fills.md": md}

    out.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (out / name).write_text(text)
    print(md, end="")
    print(f"Saved {out}/{{{','.join(files)}}}")


if __name__ == "__main__":
    main()
