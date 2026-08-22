"""Declarative bundles: parse a JSON spec file into a Bundle.

A spec (docs/DECLARATIVE_SPEC.md) is a Config plus an ordered list of
parametrised strategies, benchmark last. Validation errors name the JSON path
of the offending key — a typo must never silently become a default.
"""

import datetime as dt
import json
from pathlib import Path
from typing import NoReturn

from bundles import Bundle
from indicators import ewma_vol, realized_vol
from results_json import slug
from simulate import Config, fee_schedule
from strategies.fixed import Fixed
from strategies.gate import Gate
from strategies.vol_target import VolTarget
from strategy import Cadence

SPEC_SCHEMA_VERSION = 1

# The keys each strategy type requires, shared with sweep._substitute so the
# grid grammar's "a null over a required key means null, not absent" rule
# cannot drift from the validation that enforces it.
REQUIRED_KEYS = {
    "fixed": frozenset({"type", "weights"}),
    "vol_target": frozenset(
        {"type", "risk", "safe", "vol_symbol", "vol", "sigma_target"}
    ),
}


def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _fail(path: str, msg: str) -> NoReturn:
    raise ValueError(f"{path}: {msg}")


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _fields(obj, path: str, required: set, optional: set = frozenset()) -> None:
    if not isinstance(obj, dict):
        _fail(path or "spec", "expected an object")
    for key in obj:
        if key not in required and key not in optional:
            _fail(_join(path, key), "unknown key")
    for key in sorted(required - set(obj)):
        _fail(_join(path, key), "missing key")


def _costs(config: dict, path: str) -> None:
    """Range-check a config block's optional cost_bps / cash_yield fields."""

    def rate(value, rate_path: str) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not 0 <= value <= 1000:
            _fail(rate_path, f"expected a per-side rate in [0, 1000] bps, got {value!r}")

    cost_bps = config.get("cost_bps", 0.0)
    if isinstance(cost_bps, dict):
        for symbol, value in cost_bps.items():
            rate(value, f"{_join(path, 'cost_bps')}.{symbol}")
    else:
        rate(cost_bps, _join(path, "cost_bps"))
    cash_yield = config.get("cash_yield", 0.0)
    if isinstance(cash_yield, bool) or not isinstance(cash_yield, (int, float)) \
            or not 0 <= cash_yield <= 0.20:
        _fail(
            _join(path, "cash_yield"),
            f"expected an annual rate in [0, 0.20], got {cash_yield!r}",
        )


def _pct(x: float) -> str:
    return f"{x * 100:g}"


def _gate(entry: dict, path: str, universe: set) -> tuple[Gate, dict]:
    _fields(
        entry, path,
        {"symbol", "assets"}, {"sma_days", "sma_months", "contribution_exempt"},
    )
    if ("sma_days" in entry) == ("sma_months" in entry):
        _fail(path, "exactly one of sma_days / sma_months")
    for asset in entry["assets"]:
        if asset not in universe:
            _fail(_join(path, "assets"), f"{asset!r} is not among the strategy's assets")
    gate = Gate(
        symbol=entry["symbol"],
        assets=list(entry["assets"]),
        sma_days=entry.get("sma_days"),
        sma_months=entry.get("sma_months"),
        contribution_exempt=entry.get("contribution_exempt", False),
    )
    normalised = {
        "symbol": gate.symbol,
        "assets": list(gate.assets),
        "contribution_exempt": gate.contribution_exempt,
    }
    key = "sma_days" if "sma_days" in entry else "sma_months"
    normalised[key] = entry[key]
    return gate, normalised


def _rebalance(entry: dict, path: str) -> tuple[Cadence, dict]:
    _fields(entry, path, set(), {"weeks", "months", "offset"})
    if ("weeks" in entry) == ("months" in entry):
        _fail(path, "exactly one of weeks / months")
    unit = "weeks" if "weeks" in entry else "months"
    every, offset = entry[unit], entry.get("offset", 0)
    for key, value in ((unit, every), ("offset", offset)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail(_join(path, key), f"expected a non-negative integer, got {value!r}")
    if every < 1:
        _fail(_join(path, unit), f"expected >= 1, got {every!r}")
    if offset >= every:
        _fail(_join(path, "offset"), f"{offset} is not below {unit} = {every}")
    cadence = Cadence(unit, every, offset)
    return cadence, {unit: every, "offset": offset}


def rebalance_str(cadence: Cadence) -> str:
    """`1w`, `2w`, `3m`, `3m+2` — the rendering the auto-labels embed and
    sweep params reuse."""
    offset = f"+{cadence.offset}" if cadence.offset else ""
    return f"{cadence.every}{cadence.unit[0]}{offset}"


def _rebalance_suffix(cadence: Cadence | None) -> str:
    return "" if cadence is None else f" rb {rebalance_str(cadence)}"


def gate_str(gate: Gate) -> str:
    """`QQQ<SMA200`, plus `+contrib` when contributions are exempt — the
    rendering the auto-labels embed and sweep params reuse."""
    exempt = "+contrib" if gate.contribution_exempt else ""
    return f"{gate.symbol}<{gate.column}{exempt}"


def _gate_suffix(gate: Gate | None) -> str:
    return "" if gate is None else f" gate {gate_str(gate)}"


def safe_str(safe: str | dict | None) -> str:
    """`BTAL`, `cash`, or a blended sleeve as `BTAL75+KMLM25` — the rendering
    the auto-label embeds and sweep params reuse.

    Sorted by symbol, so one sleeve cannot spell two labels (and two slugs).
    `+` joins sleeve fractions where `fixed`'s `/` joins portfolio fractions.
    """
    if isinstance(safe, dict):
        return "+".join(f"{s}{_pct(f)}" for s, f in sorted(safe.items()))
    return safe or "cash"


def _sleeve(safe: str | dict | None) -> set[str]:
    """The safe symbols a `safe` value names — empty for cash."""
    if isinstance(safe, dict):
        return set(safe)
    return set() if safe is None else {safe}


def _safe(safe, path: str, risk: str) -> None:
    """A blended sleeve maps safe symbols to fractions *of the sleeve*, fully
    allocated. Blend-with-cash is deliberately inexpressible: `null` is the
    cash arm, and a partial sum would smuggle a second cash definition into
    the arm taxonomy."""
    if not isinstance(safe, dict):
        return
    if len(safe) < 2:
        _fail(path, f"a {len(safe)}-symbol sleeve is the string form; use it")
    for symbol, f in safe.items():
        if not isinstance(symbol, str):
            _fail(path, f"expected a symbol string, got {symbol!r}")
        if symbol == risk:
            _fail(_join(path, symbol), "is the risk asset")
        if isinstance(f, bool) or not isinstance(f, (int, float)) or f <= 0:
            _fail(_join(path, symbol), f"expected a fraction > 0, got {f!r}")
    if abs(sum(safe.values()) - 1) > 1e-9:
        _fail(path, f"sleeve fractions sum to {sum(safe.values()):g}, not 1")


def _fixed(entry: dict, path: str) -> Fixed:
    _fields(entry, path, REQUIRED_KEYS["fixed"], {"label", "gate", "rebalance"})
    weights = entry["weights"]
    if not isinstance(weights, dict) or not weights:
        _fail(_join(path, "weights"), "expected a non-empty object")
    for symbol, w in weights.items():
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w < 0:
            _fail(f"{path}.weights.{symbol}", f"expected a weight >= 0, got {w!r}")
    if sum(weights.values()) > 1 + 1e-9:
        _fail(_join(path, "weights"), f"weights sum to {sum(weights.values()):g}, > 1")

    gate = normalised_gate = None
    if "gate" in entry:
        gate, normalised_gate = _gate(entry["gate"], _join(path, "gate"), set(weights))
    cadence = normalised_cadence = None
    if "rebalance" in entry:
        cadence, normalised_cadence = _rebalance(entry["rebalance"], _join(path, "rebalance"))
    label = entry.get(
        "label",
        "/".join(f"{s}{_pct(w)}" for s, w in weights.items())
        + _gate_suffix(gate) + _rebalance_suffix(cadence),
    )
    st = Fixed(weights=dict(weights), gate=gate, label=label)
    st.rebalance = cadence
    st.spec = {"type": "fixed", "label": label, "weights": dict(weights)} | (
        {"gate": normalised_gate} if normalised_gate else {}
    ) | ({"rebalance": normalised_cadence} if normalised_cadence else {})
    return st


_VOL_KINDS = {"ewma": (ewma_vol, "lam"), "realized": (realized_vol, "n")}


def _vol_target(entry: dict, path: str) -> VolTarget:
    _fields(
        entry, path,
        REQUIRED_KEYS["vol_target"],
        {"leverage", "w_max", "w_min", "fallback", "gate", "label", "rebalance"},
    )
    vol_entry, vol_path = entry["vol"], _join(path, "vol")
    _fields(vol_entry, vol_path, {"kind"}, {"lam", "n"})
    if vol_entry["kind"] not in _VOL_KINDS:
        _fail(_join(vol_path, "kind"), f"unknown kind {vol_entry['kind']!r}")
    factory, param = _VOL_KINDS[vol_entry["kind"]]
    _fields(vol_entry, vol_path, {"kind", param})
    vol = factory(vol_entry[param])

    w_max = entry.get("w_max", 1.0)
    w_min = entry.get("w_min", 0.0)
    if not 0 <= w_min <= w_max <= 1:
        _fail(path, f"need 0 <= w_min <= w_max <= 1, got w_min={w_min}, w_max={w_max}")
    fallback = entry.get("fallback", w_max)
    if not w_min <= fallback <= w_max:
        _fail(_join(path, "fallback"), f"{fallback} is outside [w_min, w_max]")

    risk, safe = entry["risk"], entry["safe"]
    _safe(safe, _join(path, "safe"), risk)
    gate = normalised_gate = None
    if "gate" in entry:
        universe = {risk} | _sleeve(safe)
        gate, normalised_gate = _gate(entry["gate"], _join(path, "gate"), universe)
    cadence = normalised_cadence = None
    if "rebalance" in entry:
        cadence, normalised_cadence = _rebalance(entry["rebalance"], _join(path, "rebalance"))
    label = entry.get(
        "label",
        f"VT {risk}/{safe_str(safe)} t{_pct(entry['sigma_target'])} "
        f"w{_pct(w_min)}-{_pct(w_max)} {entry['vol_symbol']}:{vol.name}"
        + _gate_suffix(gate) + _rebalance_suffix(cadence),
    )
    st = VolTarget(
        risk=risk, safe=safe, vol_symbol=entry["vol_symbol"], vol=vol,
        sigma_target=entry["sigma_target"], leverage=entry.get("leverage", 1.0),
        w_max=w_max, w_min=w_min, fallback=fallback, gate=gate, label=label,
    )
    st.rebalance = cadence
    st.spec = {
        "type": "vol_target", "label": label, "risk": risk,
        "safe": dict(safe) if isinstance(safe, dict) else safe,
        "vol_symbol": entry["vol_symbol"], "vol": dict(vol_entry),
        "sigma_target": entry["sigma_target"], "leverage": st.leverage,
        "w_max": w_max, "w_min": w_min, "fallback": fallback,
    } | ({"gate": normalised_gate} if normalised_gate else {}) | (
        {"rebalance": normalised_cadence} if normalised_cadence else {}
    )
    return st


_TYPES = {"fixed": _fixed, "vol_target": _vol_target}


def build_bundle(spec: dict) -> Bundle:
    if isinstance(spec, dict) and ("windows" in spec or "template" in spec):
        _fail("spec", "this is a sweep spec; run it with "
                      "`uv run sweep.py SPEC`, not `main.py --spec`")
    _fields(spec, "", {"schema_version", "config", "strategies"})
    if spec["schema_version"] != SPEC_SCHEMA_VERSION:
        _fail("schema_version", f"expected {SPEC_SCHEMA_VERSION}, got {spec['schema_version']!r}")

    _fields(
        spec["config"], "config",
        {"start", "initial_capital", "monthly_contribution"},
        {"end", "cost_bps", "cash_yield"},
    )
    _costs(spec["config"], "config")
    end = spec["config"].get("end")  # absent or null both mean "to the end of the data"
    cost_bps = spec["config"].get("cost_bps", 0.0)
    config = Config(
        start=dt.date.fromisoformat(spec["config"]["start"]),
        initial_capital=float(spec["config"]["initial_capital"]),
        monthly_contribution=float(spec["config"]["monthly_contribution"]),
        end=None if end is None else dt.date.fromisoformat(end),
        cost_bps={s: float(v) for s, v in cost_bps.items()}
        if isinstance(cost_bps, dict)
        else float(cost_bps),
        cash_yield=float(spec["config"].get("cash_yield", 0.0)),
    )

    entries = spec["strategies"]
    if not isinstance(entries, list) or len(entries) < 2:
        _fail("strategies", "need at least 2 entries (one strategy plus the benchmark, last)")

    strategies = []
    seen: dict[str, int] = {}  # slug -> index of the first strategy claiming it
    for i, entry in enumerate(entries):
        path = f"strategies[{i}]"
        if not isinstance(entry, dict) or "type" not in entry:
            _fail(_join(path, "type"), "missing key")
        if entry["type"] not in _TYPES:
            _fail(_join(path, "type"), f"unknown type {entry['type']!r}")
        st = _TYPES[entry["type"]](entry, path)
        s = slug(st.label)
        if s in seen:
            what = "duplicate label" if strategies[seen[s]].label == st.label else "slug"
            _fail(_join(path, "label"),
                  f"{what} {st.label!r} collides with strategies[{seen[s]}]")
        seen[s] = i
        strategies.append(st)

    # Every traded symbol must resolve to a fee rate before any simulation runs.
    try:
        fee_schedule(config.cost_bps, sorted({s for st in strategies for s in st.weights}))
    except ValueError as e:
        _fail("config.cost_bps", str(e).removeprefix("cost_bps: "))
    return Bundle(strategies=strategies, config=config)


def normalised_spec(bundle: Bundle) -> dict:
    """The spec with every label and default filled in — what results.json embeds."""
    return {
        "schema_version": SPEC_SCHEMA_VERSION,
        "config": {
            "start": bundle.config.start.isoformat(),
            "initial_capital": bundle.config.initial_capital,
            "monthly_contribution": bundle.config.monthly_contribution,
            "cost_bps": bundle.config.cost_bps
            if isinstance(bundle.config.cost_bps, (int, float))
            else dict(bundle.config.cost_bps),
            "cash_yield": bundle.config.cash_yield,
        } | ({"end": bundle.config.end.isoformat()} if bundle.config.end else {}),
        "strategies": [st.spec for st in bundle.strategies],
    }
