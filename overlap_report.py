"""Phase-1 overlap validation of the EU-substitute lines (EU_SUBSTITUTE_SPEC §4).

For each registered EU/US pair, on the pair's common calendar in a decision
root, OLS of the EU line's period log returns on the US line's at three
horizons — month-ends (the §4.2 letter), quarter-ends (the §4.4 decision
horizon) and ISO-week ends (the supplement, which decides P6 alone: seventeen
months are underpowered). Emits n, beta, alpha_yr, drift_yr (%/yr), r2,
resid_yr (%/yr), the rolling-12-period tracking difference and the worst
single period, applies the pre-registered bars and pins the haircut constants
h = max(0, -drift) for the carried component slots (§4.3, §6.3).

Erratum 13 (P3's basis): a net-15 root charges BIL's Treasury interest a
withholding an Irish accumulating fund does not pay, so IB01 outperforms
net-15 BIL by that withholding and fails a two-sided drift bar by winning.
P3 is therefore read against **gross** BIL — the parent snapshot, by default
the root's name before its first `-net` suffix — and a pass on that basis
is labelled PASS-BY-ERRATUM; the net-15 reading is recorded beside it.

§4.4 (the async-close amendment, pre-registered before any Phase-3 run): an
LSE or Euronext close precedes New York's by ~4.5 h, so a period return of an
EU line carries the gap's move twice, in and out. The gap is a constant ~3 %
per period whatever the horizon, so it is ~6 % of a monthly move's variance
(R² ≈ 0.95, β attenuated, α biased up by the attenuation) and ~2 % of a
quarterly one. The bars keep their thresholds and are read on the quarter-end
calendar; the intercept is replaced by the endpoint-only drift, which the gap
enters only at the window's two ends. The monthly reading stays recorded as
the letter of §4.2. All horizons are computed in one run so that
`haircuts.json` and every verdict come from the same invocation.

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
PERIODS = {"monthly": 12, "quarterly": 4, "weekly": 52}
DECISION = {"P6": "weekly"}  # every other pair decides on the quarterly horizon (§4.4)
LETTER = {"P6": "weekly"}    # the §4.2 letter: monthly, P6 weekly, the intercept as α
GROSS_BASIS = {"P3"}         # erratum 13: read against the gross parent snapshot
PASSING = {"PASS", "PASS-BY-ERRATUM", "CONDITIONAL", "PROVISIONAL PASS"}


def joint(data_dir: Path, eu: str, us: str) -> pl.DataFrame:
    """The pair's common calendar: `date | eu | us`, inner join."""
    left = _read_close(data_dir, eu).rename({"close": "eu"})
    right = _read_close(data_dir, us).rename({"close": "us"})
    return left.join(right, on="date", how="inner").sort("date")


def period_ends(frame: pl.DataFrame, horizon: str) -> pl.DataFrame:
    """The joint calendar's last bar of each month, quarter or ISO week — the
    `is_rebalance_day` rule on the joined frame, so both lines' holidays are
    respected; the final row never ends a period."""
    if horizon == "monthly":
        return month_ends(frame)
    date = frame["date"]
    if horizon == "quarterly":
        key = date.dt.year() * 10 + (date.dt.month() - 1) // 3
    else:
        key = date.dt.iso_year() * 100 + date.dt.week()
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


def verdict(pair_id: str, s: dict, alpha: str = "drift_yr") -> str:
    """The §4.2 verdict grammar on one horizon's statistics, with `alpha`
    naming the drag estimator: the endpoint drift (§4.4) or the intercept
    (the letter)."""
    a, b, r2, resid = s[alpha], s["beta"], s["r2"], s["resid_yr"]
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
    """h = max(0, -drift) %/yr on the decision horizon, for the carried slots
    of passing pairs only — a FAILed slot is absent, not zero (§4.3)."""
    out = {}
    for row in rows:
        if row["id"] in CARRIED and row["verdict"] in PASSING:
            drift = row[DECISION.get(row["id"], "quarterly")]["drift_yr"]
            out[CARRIED[row["id"]]] = max(0.0, -drift)
    return out


def gross_root(data_dir: Path) -> Path:
    """The parent gross snapshot of a derived root: `2026-09-02-net15-usd` →
    `2026-09-02`; a root with no `-net` suffix is its own gross basis."""
    return data_dir.with_name(data_dir.name.split("-net")[0])


def report(data_dir: Path, gross_dir: Path | None = None) -> dict:
    gross_dir = gross_dir or gross_root(data_dir)
    rows = []
    for pair_id, eu, us, cls in PAIRS:
        basis = gross_dir if pair_id in GROSS_BASIS else data_dir
        frame = joint(basis, eu, us)
        stats = {h: regress(period_ends(frame, h), p) for h, p in PERIODS.items()}
        decision, letter = DECISION.get(pair_id, "quarterly"), LETTER.get(pair_id, "monthly")
        row = {
            "id": pair_id, "eu": eu, "us": us, "class": cls,
            "basis": basis.name,
            "first": frame["date"][0].isoformat(),
            "last": frame["date"][-1].isoformat(),
            "decision_horizon": decision,
            "letter_horizon": letter,
            **stats,
            "verdict": verdict(pair_id, stats[decision]),
            "verdict_letter": verdict(pair_id, stats[letter], "alpha_yr"),
        }
        if pair_id in GROSS_BASIS:
            if row["verdict"] == "PASS":
                row["verdict"] = "PASS-BY-ERRATUM"
            net = joint(data_dir, eu, us)
            row["net_basis"] = {
                "root": data_dir.name,
                decision: regress(period_ends(net, decision), PERIODS[decision]),
            }
        rows.append(row)
    return {"root": data_dir.name, "gross": gross_dir.name, "pairs": rows,
            "haircuts": haircuts(rows)}


def _cell(value: float | None, digits: int = 2) -> str:
    return "·" if value is None else f"{value:+.{digits}f}"


def _verdict_cell(row: dict, horizon: str) -> str:
    if horizon == row["decision_horizon"]:
        return f"**{row['verdict']}**"
    if horizon == row["letter_horizon"]:
        return f"letter: {row['verdict_letter']}"
    return "·"


def render_md(payload: dict) -> str:
    lines = [
        f"# Overlap validation — `{payload['root']}` (EU_SUBSTITUTE_SPEC §4)", "",
        "Verdicts: the **quarterly** table decides (§4.4, drift as α; P6 decides on the",
        "weekly supplement); the **monthly** table records the letter of §4.2 (the",
        "intercept as α), gap-attenuated for every LSE/Euronext line. `·` = not the",
        f"row's verdict horizon. P3 is read against gross BIL in `{payload['gross']}`",
        "(erratum 13); its net-15 reading is listed under the haircuts.", "",
    ]
    titles = {
        "monthly": "monthly horizon — the §4.2 letter (verdict column: intercept as α)",
        "quarterly": "quarterly horizon — the §4.4 decision horizon (verdict column: drift as α)",
        "weekly": "weekly horizon — the supplement (decides P6, drift as α)",
    }
    for horizon in PERIODS:
        lines += [
            f"## {titles[horizon]}",
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
                f"| {_verdict_cell(row, horizon)} |"
            )
        lines.append("")
    lines += ["## Haircuts pinned (§4.3) — `h = max(0, −drift)` %/yr, carried slots only", "",
              "| US symbol | h %/yr |", "|---|---|"]
    for symbol, h in sorted(payload["haircuts"].items()):
        lines.append(f"| {symbol} | {h:.4f} |")
    if not payload["haircuts"]:
        lines.append("| — | — |")
    for row in payload["pairs"]:
        if "net_basis" in row:
            h = row["decision_horizon"]
            s = row["net_basis"][h]
            lines += ["", f"{row['id']} on `{row['net_basis']['root']}` ({h}, the net-15 basis the "
                          f"spec pre-registered): n {s['n']}, β {s['beta']:.4f}, drift "
                          f"{s['drift_yr']:+.2f} %/yr, resid {s['resid_yr']:.2f} — "
                          f"verdict on that basis: {verdict(row['id'], s)}."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="the decision root")
    parser.add_argument("--gross", type=Path, default=None,
                        help="the gross parent snapshot for P3 (default: the root's name "
                             "before its first -net suffix)")
    parser.add_argument("--out", type=Path, default=Path("results/overlap_eu"),
                        help="artefact directory (default: results/overlap_eu)")
    args = parser.parse_args(argv)

    payload = results_json._round(report(args.data, args.gross))
    md = render_md(payload)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "overlap.json").write_text(results_json.dumps(payload))
    (args.out / "overlap.md").write_text(md)
    (args.out / "haircuts.json").write_text(results_json.dumps(payload["haircuts"]))
    print(md, end="")
    print(f"Saved {args.out}/{{overlap.json,overlap.md,haircuts.json}}")


if __name__ == "__main__":
    main()
