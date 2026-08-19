"""Parameter sweeps: grid expansion over a strategy template, evaluation over
a set of windows, and a summary ranked by a robust objective (docs/SWEEP_SPEC.md).

A sweep spec owns its dates in `windows`; the `template` is one strategy entry
in the ordinary spec grammar in which any leaf — including the whole `gate`
object — may be `{"grid": [v1, v2, ...]}`.
"""

import copy
import datetime as dt
import itertools
import json
from bisect import bisect_left, bisect_right
from calendar import monthrange
from dataclasses import dataclass

from spec import _TYPES, _fail, _fields, _join, gate_str

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
