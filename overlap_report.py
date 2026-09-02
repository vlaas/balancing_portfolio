"""Phase-1 overlap validation of the EU-substitute lines (EU_SUBSTITUTE_SPEC §4).

For each registered EU/US pair, on the pair's common calendar in a decision
root, OLS of the EU line's period log returns on the US line's — at month-ends
(the decision horizon) and at ISO-week ends (the supplement, which decides P6
alone: seventeen months are underpowered). Emits n, beta, alpha_yr (%/yr),
r2, resid_yr (%/yr), the rolling-12-period tracking difference and the worst
single period, applies the pre-registered bars (§4.2) and pins the haircut
constants h = max(0, -alpha) for the carried component slots (§4.3, §6.3).
Both horizons are computed in one run so that `haircuts.json` and every
verdict come from the same invocation.

Writes overlap.json, overlap.md and haircuts.json under --out and prints the
markdown. The pairs and the bars are frozen here; a bar not listed is not a
bar, and a FAIL is recorded, never engineered around.

Run: uv run overlap_report.py --data tests/data/2026-09-02-net15-usd
     [--out results/overlap_eu]
"""

import argparse
import math
from pathlib import Path

import polars as pl

import results_json
from prices import _read_close
from regime_report import month_ends

# (id, EU line, US original, fidelity class) — §4.2, frozen.
PAIRS = (
    ("P1", "QQQ3", "TQQQ", "MECHANICAL"),
    ("P2", "QQL3", "TQQQ", "MECHANICAL"),
    ("P3", "IB01", "BIL", "MECHANICAL"),
    ("P4", "CSPX", "SPY", "MECHANICAL"),
    ("P5", "CNDX", "QQQ", "MECHANICAL"),
    ("P6", "DBMF_EU", "DBMF", "FUNCTIONAL"),
    ("P7", "LQQ", "QQQ", "PARAMETRIC"),
    ("P8", "DBMF_EU", "KMLM", "—"),
)
# The component slots whose US symbol carries a pair's haircut in the -hc root
# (§6.3). P4/P5 are adoption bars — real CSPX/CNDX bars are used directly.
CARRIED = {"P1": "TQQQ", "P3": "BIL", "P6": "DBMF"}
PERIODS = {"monthly": 12, "weekly": 52}
DECISION = {"P6": "weekly"}  # every other pair decides on the monthly horizon
PASSING = {"PASS", "CONDITIONAL", "PROVISIONAL PASS"}


def joint(data_dir: Path, eu: str, us: str) -> pl.DataFrame:
    """The pair's common calendar: `date | eu | us`, inner join."""
    left = _read_close(data_dir, eu).rename({"close": "eu"})
    right = _read_close(data_dir, us).rename({"close": "us"})
    return left.join(right, on="date", how="inner").sort("date")


def period_ends(frame: pl.DataFrame, horizon: str) -> pl.DataFrame:
    """The joint calendar's last bar of each month or ISO week — the
    `is_rebalance_day` rule on the joined frame, so both lines' holidays are
    respected; the final row never ends a period."""
    if horizon == "monthly":
        return month_ends(frame)
    key = frame["date"].dt.iso_year() * 100 + frame["date"].dt.week()
    return frame.filter((key != key.shift(-1)).fill_null(False))


def regress(ends: pl.DataFrame, periods: int) -> dict:
    """OLS of EU period log returns (y) on US (x), annualised by `periods`."""
    r = ends.select(
        "date", x=pl.col("us").log().diff(), y=pl.col("eu").log().diff()
    ).drop_nulls()
    n = len(r)
    if n < 3:
        raise ValueError(f"{n} periods: too few to regress")
    x, y = r["x"], r["y"]
    beta = r.select(pl.cov("x", "y") / pl.var("x")).item()
    alpha = y.mean() - beta * x.mean()
    corr = r.select(pl.corr("x", "y")).item()
    resid = y - alpha - beta * x
    diff = y - x
    i = diff.abs().arg_max()
    td = diff.rolling_sum(periods).drop_nulls()
    return {
        "n": n,
        "beta": beta,
        "alpha_yr": alpha * periods * 100,
        # Endpoint-only: the summed period differences telescope to the
        # window's total log-return difference, so an asynchronous close
        # enters twice, not every period (documentation, not a bar).
        "drift_yr": diff.mean() * periods * 100,
        "r2": corr * corr,
        "corr": corr,
        "resid_yr": resid.std() * math.sqrt(periods) * 100,
        "td_min": None if td.is_empty() else td.min() * 100,
        "td_median": None if td.is_empty() else td.median() * 100,
        "td_max": None if td.is_empty() else td.max() * 100,
        "worst_date": r["date"][i].isoformat(),
        "worst_pp": diff[i] * 100,
    }


def verdict(pair_id: str, monthly: dict, weekly: dict) -> str:
    """The §4.2 verdict grammar, on the pair's decision horizon."""
    s = weekly if DECISION.get(pair_id) == "weekly" else monthly
    a, b, r2, resid = s["alpha_yr"], s["beta"], s["r2"], s["resid_yr"]
    if pair_id in ("P1", "P2"):
        if not (0.97 <= b <= 1.03 and r2 >= 0.98):
            return "FAIL"
        if -2.0 < a <= 0.5:
            return "PASS"
        if -3.0 < a <= -2.0:
            return "CONDITIONAL"
        return "FAIL"
    if pair_id == "P3":
        return "PASS" if abs(a) <= 0.30 and resid <= 0.75 else "FAIL"
    if pair_id in ("P4", "P5"):
        ok = 0.97 <= b <= 1.03 and r2 >= 0.99 and -0.60 <= a <= 0.10
        return "PASS" if ok else "FAIL"
    if pair_id == "P6":
        ok = s["corr"] >= 0.90 and 0.8 <= b <= 1.2 and abs(a) <= 1.5
        return "PROVISIONAL PASS" if ok else "FAIL"
    if pair_id == "P7":
        return "characterization"
    return "documentation"


def haircuts(rows: list[dict]) -> dict[str, float]:
    """h = max(0, -alpha) %/yr on the decision horizon, for the carried slots
    of passing pairs only — a FAILed slot is absent, not zero (§4.3)."""
    out = {}
    for row in rows:
        if row["id"] in CARRIED and row["verdict"] in PASSING:
            alpha = row[DECISION.get(row["id"], "monthly")]["alpha_yr"]
            out[CARRIED[row["id"]]] = max(0.0, -alpha)
    return out


def report(data_dir: Path) -> dict:
    rows = []
    for pair_id, eu, us, cls in PAIRS:
        frame = joint(data_dir, eu, us)
        stats = {h: regress(period_ends(frame, h), p) for h, p in PERIODS.items()}
        rows.append({
            "id": pair_id, "eu": eu, "us": us, "class": cls,
            "first": frame["date"][0].isoformat(),
            "last": frame["date"][-1].isoformat(),
            "decision_horizon": DECISION.get(pair_id, "monthly"),
            **stats,
            "verdict": verdict(pair_id, stats["monthly"], stats["weekly"]),
        })
    return {"root": data_dir.name, "pairs": rows, "haircuts": haircuts(rows)}


def _cell(value: float | None, digits: int = 2) -> str:
    return "·" if value is None else f"{value:+.{digits}f}"


def render_md(payload: dict) -> str:
    lines = [f"# Overlap validation — `{payload['root']}` (EU_SUBSTITUTE_SPEC §4)", ""]
    for horizon in PERIODS:
        lines += [
            f"## {horizon} horizon"
            + (" — the decision horizon (P6 decides weekly)" if horizon == "monthly"
               else " — the supplement (decides P6)"),
            "",
            "| pair | eu / us | class | first | last | n | β | α %/yr | drift %/yr | R² "
            "| corr | resid %/yr | TD12 min / med / max pp | worst period pp (date) "
            "| verdict |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for row in payload["pairs"]:
            s = row[horizon]
            lines.append(
                f"| {row['id']} | {row['eu']} / {row['us']} | {row['class']} "
                f"| {row['first']} | {row['last']} | {s['n']} | {s['beta']:.4f} "
                f"| {s['alpha_yr']:+.2f} | {s['drift_yr']:+.2f} | {s['r2']:.4f} "
                f"| {s['corr']:.4f} "
                f"| {s['resid_yr']:.2f} | {_cell(s['td_min'])} / {_cell(s['td_median'])} "
                f"/ {_cell(s['td_max'])} | {s['worst_pp']:+.2f} ({s['worst_date']}) "
                f"| {row['verdict'] if horizon == row['decision_horizon'] else '·'} |"
            )
        lines.append("")
    lines += ["## Haircuts pinned (§4.3) — `h = max(0, −α̂)` %/yr, carried slots only", "",
              "| US symbol | h %/yr |", "|---|---|"]
    for symbol, h in sorted(payload["haircuts"].items()):
        lines.append(f"| {symbol} | {h:.4f} |")
    if not payload["haircuts"]:
        lines.append("| — | — |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="the decision root")
    parser.add_argument("--out", type=Path, default=Path("results/overlap_eu"),
                        help="artefact directory (default: results/overlap_eu)")
    args = parser.parse_args(argv)

    payload = results_json._round(report(args.data))
    md = render_md(payload)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "overlap.json").write_text(results_json.dumps(payload))
    (args.out / "overlap.md").write_text(md)
    (args.out / "haircuts.json").write_text(results_json.dumps(payload["haircuts"]))
    print(md, end="")
    print(f"Saved {args.out}/{{overlap.json,overlap.md,haircuts.json}}")


if __name__ == "__main__":
    main()
