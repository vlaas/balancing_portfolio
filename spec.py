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
from indicators import ewma_vol, mom_monthly, mom_multi, realized_vol, sma_gap
from results_json import slug
from simulate import Config, fee_schedule
from strategies.fixed import Fixed
from strategies.gate import AnyGate, Gate
from strategies.rotation import BestOf, Canary, Rotation
from strategies.vol_target import SafeSwitch, VolTarget
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
    "rotation": frozenset({"type", "assets", "k", "score"}),
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


def _condition(entry: dict, path: str) -> None:
    """The condition kind shared by a gate and a switch's `when`: exactly one
    of sma_days / sma_months / fire / score, with the regime keys validated
    against fire and threshold against score (REGIME_SPEC §4,
    SAFE_SWITCH_SPEC §2.1, COMPOSITION_SPEC §4.1)."""
    kinds = (
        ("sma_days" in entry) + ("sma_months" in entry)
        + ("fire" in entry) + ("score" in entry)
    )
    if kinds != 1:
        _fail(path, "exactly one of sma_days / sma_months / fire / score")
    if "score" in entry:
        _score(entry["score"], _join(path, "score"))
        threshold = entry.get("threshold", 0.0)
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) \
                or abs(threshold * 1000 - round(threshold * 1000)) > 1e-9:
            _fail(_join(path, "threshold"),
                  f"expected a multiple of 0.001, got {threshold!r}")
    elif "threshold" in entry:
        _fail(_join(path, "threshold"), "requires score")
    if "fire" in entry:
        for key in ("denominator", "ratio_sma"):
            if key not in entry:
                _fail(_join(path, key), "required with fire")
        if entry["denominator"] == entry["symbol"]:
            _fail(_join(path, "denominator"), "equals the gate symbol")
        n = entry["ratio_sma"]
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            _fail(_join(path, "ratio_sma"), f"expected an integer >= 1, got {n!r}")
        fire, hysteresis = entry["fire"], entry.get("hysteresis", 0.0)
        for key, value in (("fire", fire), ("hysteresis", hysteresis)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) \
                    or value < 0 or abs(value * 100 - round(value * 100)) > 1e-9:
                _fail(_join(path, key),
                      f"expected a non-negative multiple of 0.01, got {value!r}")
        if hysteresis >= fire:
            _fail(_join(path, "hysteresis"), f"{hysteresis} is not below fire = {fire}")
    else:
        for key in ("denominator", "ratio_sma", "hysteresis"):
            if key in entry:
                _fail(_join(path, key), "requires fire (the regime kind)")


def _condition_normalised(entry: dict) -> dict:
    """The condition keys of a normalised gate or `when` object: the regime
    kind with hysteresis filled, the score kind with threshold filled, or the
    single sma key."""
    if "fire" in entry:
        return {
            "denominator": entry["denominator"], "ratio_sma": entry["ratio_sma"],
            "fire": entry["fire"], "hysteresis": entry.get("hysteresis", 0.0),
        }
    if "score" in entry:
        # `_condition` has already validated it, so the re-parse cannot fail.
        return {
            "score": _score(entry["score"], "score")[1],
            "threshold": entry.get("threshold", 0.0),
        }
    key = "sma_days" if "sma_days" in entry else "sma_months"
    return {key: entry[key]}


def _gate_object(entry: dict, path: str, universe: set) -> tuple[Gate, dict]:
    _fields(
        entry, path,
        {"symbol", "assets"},
        {"sma_days", "sma_months", "denominator", "ratio_sma", "fire",
         "hysteresis", "score", "threshold", "contribution_exempt", "w_off"},
    )
    _condition(entry, path)
    if "w_off" in entry:
        w_off = entry["w_off"]
        if isinstance(w_off, bool) or not isinstance(w_off, (int, float)) \
                or not 0 <= w_off <= 1:
            _fail(_join(path, "w_off"), f"expected a weight in [0, 1], got {w_off!r}")
    for asset in entry["assets"]:
        if asset not in universe:
            _fail(_join(path, "assets"), f"{asset!r} is not among the strategy's assets")
    gate = Gate(
        symbol=entry["symbol"],
        assets=list(entry["assets"]),
        sma_days=entry.get("sma_days"),
        sma_months=entry.get("sma_months"),
        denominator=entry.get("denominator"),
        ratio_sma=entry.get("ratio_sma"),
        fire=entry.get("fire"),
        hysteresis=entry.get("hysteresis", 0.0),
        score=_score(entry["score"], _join(path, "score"))[0]
        if "score" in entry
        else None,
        threshold=entry.get("threshold", 0.0) if "score" in entry else None,
        contribution_exempt=entry.get("contribution_exempt", False),
        w_off=entry.get("w_off"),
    )
    normalised = {
        "symbol": gate.symbol,
        "assets": list(gate.assets),
        "contribution_exempt": gate.contribution_exempt,
    } | _condition_normalised(entry)
    if "w_off" in entry:
        normalised["w_off"] = gate.w_off
    return gate, normalised


def _gate(entry, path: str, universe: set) -> tuple[Gate | AnyGate, dict | list]:
    """A gate object, or a list of >= 2 of them composing to an AnyGate."""
    if not isinstance(entry, list):
        return _gate_object(entry, path, universe)
    if len(entry) < 2:
        _fail(path, "a composite gate needs at least 2 members; use the object form")
    members, normalised = [], []
    for i, member in enumerate(entry):
        member_path = f"{path}[{i}]"
        if isinstance(member, list):
            _fail(member_path, "composite gates do not nest")
        gate, norm = _gate_object(member, member_path, universe)
        members.append(gate)
        normalised.append(norm)
    return AnyGate(tuple(members)), normalised


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


def gate_str(gate: Gate | AnyGate) -> str:
    """`QQQ<SMA200`, `VIX/VIX3M@10>=1.00<0.95` or `QQQ:MOMM1-3-6-12U<=m2`, plus
    `+contrib` when contributions are exempt and ` off{pct}` when `w_off` is
    set; a composite joins its members with `|` — the rendering the auto-labels
    embed and sweep params reuse (REGIME_SPEC §5.2, COMPOSITION_SPEC §4.2)."""
    if isinstance(gate, AnyGate):
        return "|".join(gate_str(member) for member in gate.members)
    exempt = "+contrib" if gate.contribution_exempt else ""
    off = f" off{_pct(gate.w_off)}" if gate.w_off is not None else ""
    if gate.fire is not None:
        band = f"<{gate.fire - gate.hysteresis:.2f}" if gate.hysteresis else ""
        return (
            f"{gate.symbol}/{gate.denominator}@{gate.ratio_sma}"
            f">={gate.fire:.2f}{band}{exempt}{off}"
        )
    if gate.score is not None:
        # `m` for a negative threshold: `slug` strips every non-alphanumeric
        # character, so `<=-0.02` and `<=0.02` would collide at build.
        threshold = _pct(gate.threshold).replace("-", "m")
        return f"{gate.symbol}:{gate.column}<={threshold}{exempt}{off}"
    return f"{gate.symbol}<{gate.column}{exempt}{off}"


def _gate_suffix(gate: Gate | AnyGate | None) -> str:
    return "" if gate is None else f" gate {gate_str(gate)}"


def safe_str(safe: str | dict | SafeSwitch | None) -> str:
    """`BTAL`, `cash`, a blended sleeve as `BTAL75+KMLM25`, or a switch as
    `on~off@condition` — the rendering the auto-label embeds and sweep params
    reuse.

    Sorted by symbol, so one sleeve cannot spell two labels (and two slugs).
    `+` joins sleeve fractions where `fixed`'s `/` joins portfolio fractions;
    `~` joins a switch's sleeves, its condition rendered by `gate_str`
    (SAFE_SWITCH_SPEC §2.3).
    """
    if isinstance(safe, SafeSwitch):
        return f"{safe_str(safe.on)}~{safe_str(safe.off)}@{gate_str(safe.when)}"
    if isinstance(safe, dict):
        return "+".join(f"{s}{_pct(f)}" for s, f in sorted(safe.items()))
    return safe or "cash"


def _sleeve(safe: str | dict | SafeSwitch | None) -> set[str]:
    """The safe symbols a `safe` value names — empty for cash."""
    if isinstance(safe, SafeSwitch):
        return _sleeve(safe.on) | _sleeve(safe.off)
    if isinstance(safe, dict):
        return set(safe)
    return set() if safe is None else {safe}


def _safe(safe, path: str, risk: str) -> tuple:
    """A blended sleeve maps safe symbols to fractions *of the sleeve*, fully
    allocated. Blend-with-cash is deliberately inexpressible: `null` is the
    cash arm, and a partial sum would smuggle a second cash definition into
    the arm taxonomy. A dict carrying `"kind"` is the switch form
    (SAFE_SWITCH_SPEC §2.1). Returns (runtime value, normalised spec value)."""
    if isinstance(safe, dict) and "kind" in safe:
        if safe["kind"] != "switch":
            _fail(_join(path, "kind"), f"unknown kind {safe['kind']!r}")
        _fields(safe, path, {"kind", "on", "off", "when"})
        sides = {}
        for key in ("on", "off"):
            value = safe[key]
            if isinstance(value, dict) and "kind" in value:
                _fail(_join(path, key), "a switch does not nest")
            sides[key] = _safe(value, _join(path, key), risk)
        if sides["on"][1] == sides["off"][1]:
            _fail(path, "on equals off; use the static form")
        when, when_path = safe["when"], _join(path, "when")
        _fields(
            when, when_path, {"symbol"},
            {"sma_days", "sma_months", "denominator", "ratio_sma", "fire",
             "hysteresis", "score", "threshold"},
        )
        _condition(when, when_path)
        condition = Gate(
            symbol=when["symbol"],
            assets=[],
            sma_days=when.get("sma_days"),
            sma_months=when.get("sma_months"),
            denominator=when.get("denominator"),
            ratio_sma=when.get("ratio_sma"),
            fire=when.get("fire"),
            hysteresis=when.get("hysteresis", 0.0),
            score=_score(when["score"], _join(when_path, "score"))[0]
            if "score" in when
            else None,
            threshold=when.get("threshold", 0.0) if "score" in when else None,
        )
        runtime = SafeSwitch(on=sides["on"][0], off=sides["off"][0], when=condition)
        normalised = {
            "kind": "switch", "on": sides["on"][1], "off": sides["off"][1],
            "when": {"symbol": when["symbol"]} | _condition_normalised(when),
        }
        return runtime, normalised
    if not isinstance(safe, dict):
        return safe, safe
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
    return safe, dict(safe)


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

    risk = entry["risk"]
    safe, safe_normalised = _safe(entry["safe"], _join(path, "safe"), risk)
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
        "safe": safe_normalised,
        "vol_symbol": entry["vol_symbol"], "vol": dict(vol_entry),
        "sigma_target": entry["sigma_target"], "leverage": st.leverage,
        "w_max": w_max, "w_min": w_min, "fallback": fallback,
    } | ({"gate": normalised_gate} if normalised_gate else {}) | (
        {"rebalance": normalised_cadence} if normalised_cadence else {}
    )
    return st


def _score(entry, path: str) -> tuple:
    """A ROTATION_SPEC §6.1 score object. Returns (Indicator, normalised)."""
    if not isinstance(entry, dict):
        _fail(path, "expected an object")
    if "kind" not in entry:
        _fields(entry, path, {"months"})
        k = entry["months"]
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            _fail(_join(path, "months"), f"expected an integer >= 1, got {k!r}")
        return mom_monthly(k), {"months": k}
    if entry["kind"] == "sma_gap":
        _fields(entry, path, {"kind", "months"})
        m = entry["months"]
        if isinstance(m, bool) or not isinstance(m, int) or m < 2:
            _fail(_join(path, "months"), f"expected an integer >= 2, got {m!r}")
        return sma_gap(m), {"kind": "sma_gap", "months": m}
    if entry["kind"] not in ("avg", "weighted"):
        _fail(_join(path, "kind"), f"unknown kind {entry['kind']!r}")
    weighted = entry["kind"] == "weighted"
    _fields(entry, path, {"kind", "months"} | ({"weights"} if weighted else set()))
    months = entry["months"]
    if not isinstance(months, list) or len(months) < 2:
        _fail(_join(path, "months"), f"expected a list of >= 2 months, got {months!r}")
    for i, m in enumerate(months):
        if isinstance(m, bool) or not isinstance(m, int) or m < 1:
            _fail(f"{_join(path, 'months')}[{i}]", f"expected an integer >= 1, got {m!r}")
    if any(a >= b for a, b in zip(months, months[1:])):
        _fail(_join(path, "months"), f"expected strictly ascending months, got {months}")
    if not weighted:
        return mom_multi(tuple(months)), {"kind": "avg", "months": list(months)}
    weights = entry["weights"]
    if not isinstance(weights, list) or len(weights) != len(months):
        _fail(_join(path, "weights"),
              f"expected a list of {len(months)} weights, got {weights!r}")
    for i, w in enumerate(weights):
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
            _fail(f"{_join(path, 'weights')}[{i}]", f"expected a weight > 0, got {w!r}")
    return (
        mom_multi(tuple(months), tuple(weights)),
        {"kind": "weighted", "months": list(months), "weights": [float(w) for w in weights]},
    )


def score_str(score: dict) -> str:
    """`12M`, `1-3-6U`, the canonical `13612W`, `1-3-6-12w12-4-2-1`, `gap10M`
    — the rendering the auto-labels embed and sweep params reuse (§7)."""
    if "kind" not in score:
        return f"{score['months']}M"
    if score["kind"] == "sma_gap":
        return f"gap{score['months']}M"
    months = "-".join(str(m) for m in score["months"])
    if score["kind"] == "avg":
        return f"{months}U"
    if list(score["months"]) == [1, 3, 6, 12] and list(score["weights"]) == [12, 4, 2, 1]:
        return "13612W"
    return f"{months}w" + "-".join(f"{w:g}" for w in score["weights"])


def _score_suffix(score: dict, main: dict) -> str:
    """`@1M`-style score marker, empty when the score is the inherited main."""
    return "" if score == main else f"@{score_str(score)}"


def filter_str(entry: dict | None) -> str:
    """`` (default), `all` (unconditional), `>BIL`, `@SPY>0`, `@SPY>BIL`. The
    on-without-hurdle form renders its explicit zero hurdle: `@SPY` and `>SPY`
    would slugify identically and collide at build (§7 errata)."""
    if not entry:
        return ""
    if "kind" in entry:
        return "all"
    on, hurdle = entry.get("on"), entry.get("hurdle")
    if on:
        return f"@{on}>{hurdle}" if hurdle else f"@{on}>0"
    return f">{hurdle}"


def _filter_suffix(entry: dict | None) -> str:
    """The label fragment: the operator forms abut the score (`12M@SPY>BIL`),
    the unconditional one is a word and needs its space (`12M all`)."""
    text = filter_str(entry)
    return f" {text}" if text == "all" else text


def canary_str(entry: dict, main_score: dict) -> str:
    """`TIP/1`, `VWO+BND/2`, score appended `@13612W`-style only when it
    differs from the main score."""
    suffix = _score_suffix(entry["score"], main_score) if "score" in entry else ""
    return "+".join(entry["symbols"]) + f"/{entry['breadth']}" + suffix


def fallback_str(entry, main_score: dict) -> str:
    """`cash`, `AGG`, `IEF60+TLT40`, `best(BIL+IEF)` / `best(TIP+TLT@1M)`, and
    the ranked form `best3(TIP+DBC+BIL+IEF+TLT+LQD+AGG>BIL)` — the floor is a
    hurdle, rendered like a filter's. `n = 1` without a floor keeps the
    original `best(A+B)` rendering byte-for-byte. Sleeves are sorted by symbol
    like `safe_str`, so one sleeve cannot spell two labels."""
    if entry is None:
        return "cash"
    if isinstance(entry, str):
        return entry
    if entry.get("kind") == "best_of":
        n = entry.get("n", 1)
        suffix = _score_suffix(entry["score"], main_score) if "score" in entry else ""
        floor = f">{entry['floor']}" if entry.get("floor") else ""
        return f"best{n if n > 1 else ''}(" + "+".join(entry["symbols"]) + suffix + floor + ")"
    return "+".join(f"{s}{_pct(f)}" for s, f in sorted(entry.items()))


def _filter(entry: dict, path: str) -> None:
    """§6.2: at least one of on / hurdle — an empty object fails because
    absence is the spelling of the default (per-asset > 0). `{"kind": "none"}`
    is the unconditional form and takes no other key."""
    if isinstance(entry, dict) and "kind" in entry:
        _fields(entry, path, {"kind"})
        if entry["kind"] != "none":
            _fail(_join(path, "kind"), f"unknown kind {entry['kind']!r}")
        return
    _fields(entry, path, set(), {"on", "hurdle"})
    if not entry:
        _fail(path, "empty filter; absence is the spelling of the default")
    for key in ("on", "hurdle"):
        if key in entry and not isinstance(entry[key], str):
            _fail(_join(path, key), f"expected a symbol string, got {entry[key]!r}")
    if entry.get("on") is not None and entry.get("on") == entry.get("hurdle"):
        _fail(path, "on equals hurdle")


def _symbol_list(entry, path: str, minimum: int, hint: str) -> None:
    if (
        not isinstance(entry, list)
        or len(entry) < minimum
        or len(set(entry)) != len(entry)
    ):
        _fail(path, f"expected >= {minimum} unique symbols{hint}, got {entry!r}")
    for i, s in enumerate(entry):
        if not isinstance(s, str):
            _fail(f"{path}[{i}]", f"expected a symbol string, got {s!r}")


def _fallback(entry, path: str, main: tuple) -> tuple:
    """§6.3: null (cash) | "SYM" | sleeve dict | best_of. Returns
    (runtime value, normalised) with the inherited best_of score filled."""
    if entry is None or isinstance(entry, str):
        return entry, entry
    if not isinstance(entry, dict):
        _fail(path, f"expected null, a symbol, a sleeve object or best_of, got {entry!r}")
    if "kind" in entry:
        if entry["kind"] != "best_of":
            _fail(_join(path, "kind"), f"unknown kind {entry['kind']!r}")
        _fields(entry, path, {"kind", "symbols"}, {"score", "n", "floor"})
        _symbol_list(entry["symbols"], _join(path, "symbols"), 2,
                     " (one symbol is the string form)")
        n = entry.get("n", 1)
        if isinstance(n, bool) or not isinstance(n, int) \
                or not 1 <= n <= len(entry["symbols"]):
            _fail(_join(path, "n"),
                  f"expected an integer in [1, {len(entry['symbols'])}], got {n!r}")
        floor = entry.get("floor")
        if floor is not None:
            if floor not in entry["symbols"]:
                _fail(_join(path, "floor"), f"{floor!r} is not one of symbols")
            if n < 2:
                # At n = 1 the argmax's score is >= the floor's by
                # construction, so the key can only fire on an exact tie: an
                # inert spelling that looks load-bearing (§2).
                _fail(_join(path, "floor"),
                      "is inert at n = 1; drop floor or set n >= 2")
        if "score" in entry:
            indicator, normalised_score = _score(entry["score"], _join(path, "score"))
        else:
            indicator, normalised_score = main
        return (
            BestOf(tuple(entry["symbols"]), indicator, n, floor),
            {"kind": "best_of", "symbols": list(entry["symbols"]), "n": n}
            | ({"floor": floor} if floor is not None else {})
            | {"score": normalised_score},
        )
    if len(entry) < 2:
        _fail(path, f"a {len(entry)}-symbol sleeve is the string form; use it")
    for symbol, f in entry.items():
        if not isinstance(symbol, str):
            _fail(path, f"expected a symbol string, got {symbol!r}")
        if isinstance(f, bool) or not isinstance(f, (int, float)) or f <= 0:
            _fail(_join(path, symbol), f"expected a fraction > 0, got {f!r}")
    if abs(sum(entry.values()) - 1) > 1e-9:
        _fail(path, f"sleeve fractions sum to {sum(entry.values()):g}, not 1")
    return dict(entry), dict(entry)


def _canary(entry: dict, path: str, main: tuple) -> tuple:
    """§6.4. Returns (Canary, normalised) with the inherited score filled."""
    _fields(entry, path, {"symbols", "breadth"}, {"score"})
    _symbol_list(entry["symbols"], _join(path, "symbols"), 1, "")
    breadth = entry["breadth"]
    if isinstance(breadth, bool) or not isinstance(breadth, int) \
            or not 1 <= breadth <= len(entry["symbols"]):
        _fail(_join(path, "breadth"),
              f"expected an integer in [1, {len(entry['symbols'])}], got {breadth!r}")
    if "score" in entry:
        indicator, normalised_score = _score(entry["score"], _join(path, "score"))
    else:
        indicator, normalised_score = main
    return (
        Canary(tuple(entry["symbols"]), breadth, indicator),
        {"symbols": list(entry["symbols"]), "breadth": breadth,
         "score": normalised_score},
    )


def _rotation(entry: dict, path: str) -> Rotation:
    _fields(
        entry, path,
        REQUIRED_KEYS["rotation"],
        {"filter", "fallback", "canary", "label", "rebalance"},
    )
    _symbol_list(entry["assets"], _join(path, "assets"), 1, "")
    assets = list(entry["assets"])
    k = entry["k"]
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= len(assets):
        _fail(_join(path, "k"),
              f"expected an integer in [1, {len(assets)}], got {k!r}")
    score, normalised_score = _score(entry["score"], _join(path, "score"))
    main = (score, normalised_score)

    filter_on = hurdle = normalised_filter = None
    filter_none = False
    if "filter" in entry:
        _filter(entry["filter"], _join(path, "filter"))
        filter_none = "kind" in entry["filter"]
        filter_on = entry["filter"].get("on")
        hurdle = entry["filter"].get("hurdle")
        normalised_filter = {"kind": "none"} if filter_none else {
            key: value
            for key, value in (("on", filter_on), ("hurdle", hurdle))
            if value is not None
        }
    fallback = normalised_fallback = None
    if "fallback" in entry:
        fallback, normalised_fallback = _fallback(
            entry["fallback"], _join(path, "fallback"), main
        )
    canary = normalised_canary = None
    if "canary" in entry:
        canary, normalised_canary = _canary(entry["canary"], _join(path, "canary"), main)
    cadence = normalised_cadence = None
    if "rebalance" in entry:
        cadence, normalised_cadence = _rebalance(entry["rebalance"], _join(path, "rebalance"))

    label = entry.get(
        "label",
        f"ROT {'+'.join(assets)} top{k} {score_str(normalised_score)}"
        + _filter_suffix(normalised_filter)
        + (f" can {canary_str(normalised_canary, normalised_score)}"
           if normalised_canary else "")
        + f" fb {fallback_str(normalised_fallback, normalised_score)}"
        + _rebalance_suffix(cadence),
    )
    st = Rotation(
        assets=assets, k=k, score=score, filter_on=filter_on, hurdle=hurdle,
        filter_none=filter_none, fallback=fallback, canary=canary, label=label,
    )
    st.rebalance = cadence
    st.spec = {
        "type": "rotation", "label": label, "assets": assets, "k": k,
        "score": normalised_score, "fallback": normalised_fallback,
    } | ({"filter": normalised_filter} if normalised_filter else {}) | (
        {"canary": normalised_canary} if normalised_canary else {}
    ) | ({"rebalance": normalised_cadence} if normalised_cadence else {})
    return st


_TYPES = {"fixed": _fixed, "vol_target": _vol_target, "rotation": _rotation}


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
