"""Parameter sweeps: grid expansion over a strategy template, evaluation over
a set of windows, and a summary ranked by a robust objective (docs/SWEEP_SPEC.md).

python sweep.py SPEC --data DIR --out DIR [--dry-run]. Never charts, never the
side-by-side report; a sweep result is a table to read, not a parameter to adopt.

A sweep spec owns its dates in `windows`; the `template` is one strategy entry
in the ordinary spec grammar in which any leaf — including the whole `gate`
object — may be `{"grid": [v1, v2, ...]}`.
"""

import argparse
import copy
import datetime as dt
import itertools
import json
import math
import statistics
import time
from bisect import bisect_left, bisect_right
from calendar import monthrange
from dataclasses import dataclass
from pathlib import Path

import polars as pl

import results_json
from main import run_bundle
from prices import load_prices
from spec import _TYPES, _fail, _fields, _join, build_bundle, gate_str, load_spec

SWEEP_SCHEMA_VERSION = 1
OBJECTIVES = ("calmar", "sharpe", "sortino", "cagr", "xirr")

# summary() keys a constraint may bound: everything scalar (the year tuples
# are not orderable thresholds).
CONSTRAINT_KEYS = frozenset({
    "avg_misallocation", "max_misallocation",
    "avg_asset_deviation", "max_asset_deviation",
    "final_value", "total_contributed", "net_profit", "net_profit_pct",
    "cagr", "xirr", "sharpe", "volatility", "sortino", "calmar",
    "max_drawdown", "max_drawdown_days",
})


def validate(spec: dict) -> None:
    """Reject any unknown or malformed key, naming its JSON path — the same
    contract as spec.build_bundle. The template is validated by expand()."""
    _fields(
        spec, "",
        {"schema_version", "config", "windows", "template", "baselines"},
        {"objective", "constraint"},
    )
    if spec["schema_version"] != SWEEP_SCHEMA_VERSION:
        _fail("schema_version",
              f"expected {SWEEP_SCHEMA_VERSION}, got {spec['schema_version']!r}")
    _fields(spec["config"], "config", {"initial_capital", "monthly_contribution"})

    w = spec["windows"]
    _fields(w, "windows", {"start"}, {"end", "holdout", "sensitivity"})
    dt.date.fromisoformat(w["start"])
    for key in ("end", "holdout"):
        if w.get(key) is not None:
            dt.date.fromisoformat(w[key])
    if w.get("sensitivity") is not None:
        sens = w["sensitivity"]
        _fields(sens, "windows.sensitivity", {"every_months"}, {"length_years"})
        every, length = sens["every_months"], sens.get("length_years")
        if isinstance(every, bool) or not isinstance(every, int) or every < 1:
            _fail("windows.sensitivity.every_months",
                  f"expected a positive integer, got {every!r}")
        if length is not None and (
            isinstance(length, bool) or not isinstance(length, int) or length < 1
        ):
            _fail("windows.sensitivity.length_years",
                  f"expected a positive integer or null, got {length!r}")

    objective = spec.get("objective", "calmar")
    if objective not in OBJECTIVES:
        _fail("objective", f"unknown objective {objective!r}")
    constraint = spec.get("constraint") or {}
    if not isinstance(constraint, dict):
        _fail("constraint", "expected an object")
    for key, minimum in constraint.items():
        if key not in CONSTRAINT_KEYS:
            _fail(_join("constraint", key), "unknown summary metric")
        if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
            _fail(_join("constraint", key), f"expected a number, got {minimum!r}")

    baselines = spec["baselines"]
    if not isinstance(baselines, list) or not baselines:
        _fail("baselines", "need at least 1 entry (the last is the benchmark)")
    for i, entry in enumerate(baselines):
        path = f"baselines[{i}]"
        if not isinstance(entry, dict) or "type" not in entry:
            _fail(_join(path, "type"), "missing key")
        if entry["type"] not in _TYPES:
            _fail(_join(path, "type"), f"unknown type {entry['type']!r}")
        _TYPES[entry["type"]](entry, path)


# --- Expansion (§4.2) --------------------------------------------------------


def _grid_dims(template: dict) -> list[tuple[tuple[str, ...], list]]:
    """Every `{"grid": [...]}` leaf as (key path, values), in document order."""
    dims = []

    def walk(node, path: tuple[str, ...], in_list: bool) -> None:
        if isinstance(node, dict):
            if set(node) == {"grid"}:
                where = "template" + "".join(f".{key}" for key in path)
                if in_list:
                    _fail(where, "grid is not supported inside lists")
                values = node["grid"]
                if not isinstance(values, list):
                    _fail(f"{where}.grid", "expected a list")
                distinct = []
                for value in values:
                    if value not in distinct:
                        distinct.append(value)
                if len(distinct) < 2:
                    _fail(f"{where}.grid",
                          f"need at least 2 distinct values, got {values!r}")
                dims.append((path, values))
            else:
                for key, value in node.items():
                    walk(value, path + (key,), in_list)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, path + (str(i),), True)

    walk(template, (), False)
    return dims


def _substitute(entry: dict, path: tuple[str, ...], value) -> None:
    node = entry
    for key in path[:-1]:
        node = node[key]
    if value is None:
        # The builders treat key presence as "has a gate" etc.; a null grid
        # value means the combination goes without the key entirely.
        del node[path[-1]]
    else:
        node[path[-1]] = copy.deepcopy(value)


def _param_value(strategy, path: tuple[str, ...], value):
    if value is None or not isinstance(value, dict):
        return value
    if path == ("gate",):
        return gate_str(strategy.gate)
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def expand(template: dict) -> list[dict]:
    """The template's grid combinations as ordinary strategy entries.

    Depth-first document order defines both the dimension order and, through
    the Cartesian product, the expansion order. Each element carries the
    auto-`label`, `params` (the varied leaves under dotted keys) and `entry`
    (the normalised strategy entry, built through spec._TYPES so validation,
    defaults and labels are shared with ordinary specs). Pure and deterministic.
    """
    dims = _grid_dims(template)
    out = []
    for combo in itertools.product(*(values for _, values in dims)):
        entry = copy.deepcopy(template)
        for (path, _), value in zip(dims, combo):
            _substitute(entry, path, value)
        if not isinstance(entry, dict) or "type" not in entry:
            _fail("template.type", "missing key")
        if entry["type"] not in _TYPES:
            _fail("template.type", f"unknown type {entry['type']!r}")
        st = _TYPES[entry["type"]](entry, "template")
        params = {
            ".".join(path): _param_value(st, path, value)
            for (path, _), value in zip(dims, combo)
        }
        out.append({"label": st.label, "params": params, "entry": st.spec})
    return out


# --- Windows (§4.3) ----------------------------------------------------------


@dataclass(frozen=True)
class Window:
    name: str
    kind: str  # full | fit | test | sens
    start: dt.date  # snapped: a trading day
    end: dt.date  # snapped: a trading day


def _snap_fwd(calendar: list[dt.date], date: dt.date, path: str) -> dt.date:
    i = bisect_left(calendar, date)
    if i == len(calendar):
        _fail(path, f"{date} is past the last trading day {calendar[-1]}")
    return calendar[i]


def _snap_back(calendar: list[dt.date], date: dt.date, path: str) -> dt.date:
    i = bisect_right(calendar, date)
    if i == 0:
        _fail(path, f"{date} is before the first trading day {calendar[0]}")
    return calendar[i - 1]


def _add_months(date: dt.date, months: int) -> dt.date:
    total = date.month - 1 + months
    year, month = date.year + total // 12, total % 12 + 1
    return dt.date(year, month, min(date.day, monthrange(year, month)[1]))


def windows(spec: dict, calendar: list[dt.date]) -> list[Window]:
    """The sweep's evaluation windows over a sorted trading calendar."""
    return _window_plan(spec, calendar)[0]


def _window_plan(
    spec: dict, calendar: list[dt.date]
) -> tuple[list[Window], list[str], list[str]]:
    """(windows, snap notes, warnings); windows[0] is always `full`.

    Starts snap to the first trading day on or after the requested date, ends
    to the last on or before. A note records every user-supplied date that
    moved (§4.6: no silent snapping); derived boundaries snap silently.
    """
    w = spec["windows"]
    notes: list[str] = []
    warnings: list[str] = []

    raw_start = dt.date.fromisoformat(w["start"])
    start = _snap_fwd(calendar, raw_start, "windows.start")
    if start != raw_start:
        notes.append(f"windows.start {raw_start} -> {start}")
    if w.get("end") is None:
        end = calendar[-1]
    else:
        raw_end = dt.date.fromisoformat(w["end"])
        end = _snap_back(calendar, raw_end, "windows.end")
        if end != raw_end:
            notes.append(f"windows.end {raw_end} -> {end}")
    if end < start:
        _fail("windows.end", f"{end} is before start {start}")
    wins = [Window("full", "full", start, end)]

    if w.get("holdout") is not None:
        holdout = dt.date.fromisoformat(w["holdout"])
        if not start < holdout <= end:
            _fail("windows.holdout", f"{holdout} is outside ({start}, {end}]")
        fit_end = _snap_back(calendar, holdout - dt.timedelta(days=1), "windows.holdout")
        test_start = _snap_fwd(calendar, holdout, "windows.holdout")
        if test_start != holdout:
            notes.append(f"windows.holdout {holdout} -> {test_start}")
        wins.append(Window("fit", "fit", start, fit_end))
        wins.append(Window("test", "test", test_start, end))
        if (end - test_start).days < 730:
            warnings.append(
                f"test window {test_start}..{end} is shorter than 2 years; "
                "its metrics are noise"
            )

    if w.get("sensitivity") is not None:
        every = w["sensitivity"]["every_months"]
        length = w["sensitivity"].get("length_years")
        for k in itertools.count():
            s_raw = _add_months(raw_start, k * every)
            if s_raw > end:
                break
            s = _snap_fwd(calendar, s_raw, "windows.sensitivity")
            if length is not None:
                e_raw = _add_months(s_raw, 12 * length)
                if e_raw > end:  # rolling: drop windows overrunning the end
                    break
                e = _snap_back(calendar, e_raw, "windows.sensitivity")
            else:
                if s >= end:  # anchored: the tail window must still have a span
                    break
                e = end
            wins.append(Window(f"sens_{s.isoformat()}", "sens", s, e))
        if length is None and any(win.kind == "sens" for win in wins):
            warnings.append(
                "sensitivity windows are anchored and overlapping "
                "(length_years not set)"
            )

    return wins, notes, warnings


# --- Running (§4.4) ----------------------------------------------------------


def _ordinary(spec: dict, entries: list[dict], start: str, end: str | None) -> dict:
    """An ordinary schema-1 spec for one window: grid entries then baselines,
    benchmark last, so build_bundle/run_bundle are reused unchanged."""
    return {
        "schema_version": 1,
        "config": {
            "start": start,
            "initial_capital": spec["config"]["initial_capital"],
            "monthly_contribution": spec["config"]["monthly_contribution"],
            "end": end,
        },
        "strategies": entries,
    }


def _run_window(task: tuple[dict, str]) -> tuple[float, dict[str, dict]]:
    """One window's simulations. The task and result are plain data so a
    future --jobs can ship them across a process boundary unchanged."""
    ordinary, data_dir = task
    t0 = time.perf_counter()
    results = run_bundle(build_bundle(ordinary), Path(data_dir))
    return time.perf_counter() - t0, {
        r.label: {"stats": r.stats, "exposure": r.exposure} for r in results
    }


def _plan(spec: dict, data_dir: Path):
    """Everything before any simulation: expansion, a data-free probe build
    (slug collisions and entry validation fail here), the traded calendar
    and the window plan."""
    expanded = expand(spec["template"])
    entries = [e["entry"] for e in expanded] + spec["baselines"]
    probe = build_bundle(_ordinary(spec, entries, spec["windows"]["start"], None))
    traded = sorted({s for st in probe.strategies for s in st.weights})
    start = dt.date.fromisoformat(spec["windows"]["start"])
    calendar = load_prices(Path(data_dir), traded, start)["date"].to_list()
    wins, notes, warnings = _window_plan(spec, calendar)
    baseline_labels = [st.label for st in probe.strategies[len(expanded):]]
    return expanded, entries, traded, baseline_labels, wins, notes, warnings


def run_sweep(spec: dict, data_dir: Path) -> tuple[pl.DataFrame, dict]:
    """Simulate every grid strategy and baseline over every window; return the
    long runs table (one row per strategy x window) and the robustness summary.

    Prints one progress line per window. The constraint is evaluated on the
    full window only; violating grid points are still run and reported but
    marked infeasible and excluded from ranking."""
    validate(spec)
    expanded, entries, traded, baseline_labels, wins, notes, warnings = _plan(
        spec, data_dir
    )

    records: dict[str, dict[str, dict]] = {}
    for w in wins:
        task = (_ordinary(spec, entries, w.start.isoformat(), w.end.isoformat()),
                str(data_dir))
        elapsed, per_label = _run_window(task)
        records[w.name] = per_label
        print(f"{w.name} {w.start}..{w.end}  {len(per_label)} strategies  {elapsed:.1f}s")

    constraint = spec.get("constraint") or {}
    feasible = {}
    for e in expanded:
        stats = records["full"][e["label"]]["stats"]
        feasible[e["label"]] = all(
            stats[key] is not None and stats[key] >= minimum
            for key, minimum in constraint.items()
        )

    runs = _runs_frame(wins, expanded, baseline_labels, records, feasible, traded)
    summary = build_summary(
        spec, wins, expanded, baseline_labels, records, feasible,
        notes=notes, warnings=warnings,
    )
    return runs, summary


def _runs_frame(
    wins: list[Window],
    expanded: list[dict],
    baseline_labels: list[str],
    records: dict[str, dict[str, dict]],
    feasible: dict[str, bool],
    traded: list[str],
) -> pl.DataFrame:
    param_keys = list(expanded[0]["params"]) if expanded else []
    params_by_label = {e["label"]: e["params"] for e in expanded}
    rows = []
    for w in wins:
        for label in [e["label"] for e in expanded] + baseline_labels:
            rec = records[w.name][label]
            row = {
                "label": label,
                "kind": w.kind,
                "window": w.name,
                "start": w.start.isoformat(),
                "end": w.end.isoformat(),
                "is_baseline": label not in params_by_label,
                "feasible": feasible.get(label, True),
            }
            params = params_by_label.get(label, {})
            for key in param_keys:
                row[f"params.{key}"] = params.get(key)
            for key, value in rec["stats"].items():
                if key in ("best_year", "worst_year"):
                    # A CSV cell cannot hold the (year, return) tuple.
                    row[key], row[f"{key}_return"] = value
                else:
                    row[key] = value
            for asset in traded:
                block = rec["exposure"].get(asset)
                row[f"exposure.{asset}.avg"] = None if block is None else block["avg"]
                row[f"exposure.{asset}.min"] = None if block is None else block["min"]
            rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None)


# --- Summary (§4.5) ----------------------------------------------------------


def _quantile(xs: list[float], p: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def _dispersion(xs: list[float]) -> dict:
    return {
        "median": statistics.median(xs),
        "min": min(xs),
        "max": max(xs),
        "iqr": _quantile(xs, 0.75) - _quantile(xs, 0.25),
    }


def build_summary(
    spec: dict,
    wins: list[Window],
    expanded: list[dict],
    baseline_labels: list[str],
    records: dict[str, dict[str, dict]],
    feasible: dict[str, bool],
    *,
    notes: list[str],
    warnings: list[str],
) -> dict:
    """The per-strategy robustness blocks of §4.5, ranked by nothing — the
    reader ranks. robust_score is deliberately a minimum over the components
    that exist: full objective, neighbour_min, sensitivity median, holdout test.
    """
    objective = spec.get("objective", "calmar")
    dims = _grid_dims(spec["template"])
    dim_keys = [".".join(path) for path, _ in dims]
    numeric = [
        all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)
        for _, values in dims
    ]
    by_combo = {
        tuple(e["params"][key] for key in dim_keys): e["label"] for e in expanded
    }
    sens = [w for w in wins if w.kind == "sens"]
    has_holdout = any(w.kind == "test" for w in wins)
    grid_labels = [e["label"] for e in expanded]

    def obj(window_name: str, label: str):
        return records[window_name][label]["stats"][objective]

    def neighbours(entry: dict) -> tuple[list[str], bool]:
        """Labels one grid step away in one numeric dimension, and whether the
        point lies on the boundary of any numeric dimension. The categorical
        (gate) dimension has neither neighbours nor a boundary."""
        key = tuple(entry["params"][k] for k in dim_keys)
        labels, edge = [], False
        for d, ((_, values), is_num) in enumerate(zip(dims, numeric)):
            if not is_num:
                continue
            i = values.index(key[d])
            edge = edge or i == 0 or i == len(values) - 1
            for j in (i - 1, i + 1):
                if 0 <= j < len(values):
                    labels.append(by_combo[key[:d] + (values[j],) + key[d + 1:]])
        return labels, edge

    # Per sensitivity window: competition rank by objective among the feasible
    # grid strategies (1 = best). Baselines and infeasible points never rank.
    ranks: dict[str, dict[str, int]] = {}
    for w in sens:
        scores = {l: obj(w.name, l) for l in grid_labels if feasible[l]}
        ranks[w.name] = {
            l: 1 + sum(other > score for other in scores.values())
            for l, score in scores.items()
        }

    def block(label: str, entry: dict | None) -> dict:
        grid = entry is not None
        stats = records["full"][label]["stats"]
        out = {"label": label}
        if grid:
            out["params"] = entry["params"]
        out["full"] = {"objective": stats[objective], **results_json._summary(stats)}
        if grid:
            out["full"]["feasible"] = feasible[label]
        if has_holdout:
            fit, test = obj("fit", label), obj("test", label)
            out["holdout"] = {"fit": fit, "test": test, "test_minus_fit": test - fit}
        else:
            out["holdout"] = None
        if sens:
            objs = [obj(w.name, label) for w in sens]
            dds = [records[w.name][label]["stats"]["max_drawdown"] for w in sens]
            out["sensitivity"] = {
                "objective": _dispersion(objs),
                "max_drawdown": _dispersion(dds),
            }
            if grid:
                rs = [ranks[w.name][label] for w in sens] if feasible[label] else None
                out["sensitivity"]["rank_median"] = rs and statistics.median(rs)
                out["sensitivity"]["rank_worst"] = rs and max(rs)
        else:
            out["sensitivity"] = None
        if grid:
            nbr, edge = neighbours(entry)
            nbr_objs = [records["full"][l]["stats"][objective] for l in nbr]
            out["neighbourhood"] = {
                "neighbour_min": min(nbr_objs) if nbr_objs else None,
                "neighbour_mean": sum(nbr_objs) / len(nbr_objs) if nbr_objs else None,
                "edge": edge,
            }
            components = [out["full"]["objective"]]
            if out["neighbourhood"]["neighbour_min"] is not None:
                components.append(out["neighbourhood"]["neighbour_min"])
            if out["sensitivity"] is not None:
                components.append(out["sensitivity"]["objective"]["median"])
            if out["holdout"] is not None:
                components.append(out["holdout"]["test"])
            out["robust_score"] = min(components)
        return out

    return {
        "objective": objective,
        "constraint": spec.get("constraint"),
        "data": {"start": wins[0].start.isoformat(), "end": wins[0].end.isoformat()},
        "windows": [
            {"name": w.name, "kind": w.kind,
             "start": w.start.isoformat(), "end": w.end.isoformat()}
            for w in wins
        ],
        "snapped": notes,
        "warnings": warnings,
        "strategies": [block(e["label"], e) for e in expanded],
        "baselines": [block(label, None) for label in baseline_labels],
    }


# --- summary.md (§4.5–4.6) ---------------------------------------------------


def _cell(value, pattern: str = "{:.2f}") -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return pattern.format(value)
    return str(value)


def _param_cell(value) -> str:
    if value is None:
        return "-"
    return f"{value:g}" if isinstance(value, (int, float)) else str(value)


def _metric_cells(s: dict, risk_wt: float | None) -> list[str]:
    sens, holdout, nbh = s["sensitivity"], s["holdout"], s.get("neighbourhood")
    o = sens and sens["objective"]
    return [
        _cell(s["full"]["objective"]),
        _cell(nbh and nbh["neighbour_min"]),
        f"{o['median']:.2f} [{o['min']:.2f}–{o['max']:.2f}]" if sens else "-",
        f"{holdout['fit']:.2f} → {holdout['test']:.2f}" if holdout else "-",
        (f"{sens['rank_median']:g}/{sens['rank_worst']}"
         if sens and sens.get("rank_median") is not None else "-"),
        f"{s['full']['max_drawdown']:+.2%}",
        _cell(risk_wt),
        ("yes*" if nbh["edge"] else "") if nbh else "-",
    ]


def _summary_md(summary: dict, runs: pl.DataFrame, risk_of: dict[str, str]) -> str:
    objective = summary["objective"]
    constraint = summary["constraint"]
    full_rows = runs.filter(pl.col("kind") == "full")

    def risk_weight(label: str) -> float | None:
        risk = risk_of.get(label)
        column = f"exposure.{risk}.avg"
        if risk is None or column not in runs.columns:
            return None
        value = full_rows.filter(pl.col("label") == label)[column]
        return value[0] if len(value) else None

    window_parts = [
        f"{w['kind']} {w['start']}..{w['end']}"
        for w in summary["windows"] if w["kind"] in ("full", "fit", "test")
    ]
    n_sens = sum(w["kind"] == "sens" for w in summary["windows"])
    if n_sens:
        window_parts.append(f"{n_sens} sensitivity")
    lines = [
        "# Sweep summary",
        "",
        f"- Data: {summary['data']['start']}..{summary['data']['end']}",
        f"- Objective: {objective}",
        "- Constraint: " + (
            ", ".join(f"{k} >= {v:g}" for k, v in constraint.items())
            if constraint else "none"
        ),
        "- Windows: " + "; ".join(window_parts),
    ]
    lines += [f"- Snapped: {note}" for note in summary["snapped"]]
    lines += [f"- Warning: {warning}" for warning in summary["warnings"]]
    if n_sens:
        lines.append(
            "- Sensitivity windows overlap by construction; the dispersion "
            "reported across them is a description, not a statistical test."
        )

    param_keys = (
        list(summary["strategies"][0]["params"]) if summary["strategies"] else []
    )
    metric_headers = [
        f"full {objective}", "nbr min", "sens median [min–max]",
        "holdout fit → test", "rank med/worst", "maxdd full", "avg risk wt", "edge",
    ]

    ranked = sorted(
        (s for s in summary["strategies"] if s["full"]["feasible"]),
        key=lambda s: s["robust_score"],
        reverse=True,  # stable: ties keep expansion order
    )
    top = ranked[:15]
    lines += [
        "",
        f"## Top {len(top)} of {len(ranked)} feasible grid strategies by robust_score",
        "",
        "| " + " | ".join(param_keys + metric_headers) + " |",
        "|" + "---|" * (len(param_keys) + len(metric_headers)),
    ]
    for s in top:
        cells = [_param_cell(s["params"][k]) for k in param_keys]
        cells += _metric_cells(s, risk_weight(s["label"]))
        lines.append("| " + " | ".join(cells) + " |")
    if any(s["neighbourhood"]["edge"] for s in top):
        lines += [
            "",
            "\\* on the grid boundary — extend the grid in that direction "
            "before believing this point.",
        ]

    lines += [
        "",
        "## Baselines",
        "",
        "| baseline | " + " | ".join(metric_headers) + " |",
        "|" + "---|" * (1 + len(metric_headers)),
    ]
    for s in summary["baselines"]:
        cells = [s["label"]] + _metric_cells(s, risk_weight(s["label"]))
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


# --- CLI (§4, §4.6) ----------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="sweep spec file")
    parser.add_argument(
        "--data", type=Path, default=Path("data"),
        help="price data directory (default: data)",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="output directory (default: results/<spec stem>)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the expanded strategies x windows count and exit",
    )
    args = parser.parse_args()

    spec = load_spec(args.spec)
    validate(spec)

    if args.dry_run:
        expanded, _, _, baseline_labels, wins, _, _ = _plan(spec, args.data)
        total = (len(expanded) + len(baseline_labels)) * len(wins)
        print(
            f"{len(expanded)} grid + {len(baseline_labels)} baselines"
            f" x {len(wins)} windows = {total} runs"
        )
        return

    runs, summary = run_sweep(spec, args.data)
    expanded = expand(spec["template"])
    risk_of = {
        e["label"]: e["entry"]["risk"] for e in expanded if "risk" in e["entry"]
    }
    for block, entry in zip(summary["baselines"], spec["baselines"]):
        if "risk" in entry:
            risk_of[block["label"]] = entry["risk"]
    md = _summary_md(summary, runs, risk_of)

    out = args.out or Path("results") / args.spec.stem
    out.mkdir(parents=True, exist_ok=True)
    (out / "strategies.json").write_text(results_json.dumps(results_json._round(expanded)))
    runs.write_csv(out / "runs.csv", float_precision=results_json.PRECISION)
    runs.write_json(out / "runs.json")
    (out / "summary.json").write_text(results_json.dumps(results_json._round(summary)))
    (out / "summary.md").write_text(md)

    print()
    print(md)
    print(f"Saved {out}/{{strategies.json,runs.csv,runs.json,summary.json,summary.md}}")


if __name__ == "__main__":
    main()
