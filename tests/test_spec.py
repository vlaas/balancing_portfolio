# Spec parsing, auto-labels, and equivalence to the hand-written strategies —
# DECLARATIVE_SPEC.md T1, T2, T3, T7, T8; REGIME_SPEC R7.

import copy
import datetime as dt
import re
from pathlib import Path

import pytest
from polars.testing import assert_frame_equal

import sweep
from bundles import BUNDLES
from main import collect_indicators, run_bundle
from prices import load_prices
from results_json import results_payload, slug
from simulate import simulate
from spec import build_bundle, load_spec, normalised_spec, safe_str
from stats import correlation
from strategies.fixed import Fixed
from strategies.gate import Gate
from strategies.spy_benchmark import SpyBenchmark
from strategies.tqqq_100 import Tqqq100
from strategies.tqqq_btal_5050 import TqqqBtal5050
from strategies.tqqq_btal_qqq_sma200 import TqqqBtalQqqSma200
from strategy import MarketDay

GOLDEN_DIR = Path(__file__).parent / "data"
SPECS = Path(__file__).parents[1] / "specs"


# --- T1: parsing -------------------------------------------------------------


@pytest.mark.parametrize("name", ["default", "research"])
def test_shipped_specs_build(name):
    bundle = build_bundle(load_spec(SPECS / f"{name}.json"))
    assert len(bundle.strategies) >= 2


def broken(mutate) -> dict:
    spec = copy.deepcopy(load_spec(SPECS / "research.json"))
    mutate(spec)
    return spec


# The §8.1 gate objects the regime cases mutate with.
G_SMA = {"symbol": "QQQ", "assets": ["TQQQ"], "sma_days": 200}
G_R1 = {
    "symbol": "VIX", "denominator": "VIX3M", "assets": ["TQQQ"],
    "ratio_sma": 1, "fire": 1.0,
}


# research.json entries: [0] fixed labelled, [1] fixed TQQQ100, [2] fixed with a
# daily gate, [3] fixed with a monthly exempt gate, [4] vol_target, [5] benchmark.
INVALID = {
    "unknown top-level key": (lambda s: s.update(sweep={}), "sweep"),
    "unknown config key": (lambda s: s["config"].update(ende="2024-01-01"), "config.ende"),
    "unknown strategy key": (lambda s: s["strategies"][0].update(wieghts={}), "strategies[0].wieghts"),
    "unknown gate key": (lambda s: s["strategies"][2]["gate"].update(sma_day=200), "strategies[2].gate.sma_day"),
    "missing required field": (lambda s: s["strategies"][0].pop("weights"), "strategies[0].weights"),
    "both sma lengths": (lambda s: s["strategies"][2]["gate"].update(sma_months=10), "strategies[2].gate"),
    "weights above 1": (lambda s: s["strategies"][0].update(weights={"TQQQ": 0.7, "BTAL": 0.5}), "strategies[0].weights"),
    "w_min above w_max": (lambda s: s["strategies"][4].update(w_min=0.6), "strategies[4]"),
    "duplicate labels": (lambda s: s["strategies"][1].update(label="TQQQ/BTAL 50/50"), "strategies[1].label"),
    "one-strategy list": (lambda s: s.update(strategies=s["strategies"][:1]), "strategies"),
    "cost_bps below range": (lambda s: s["config"].update(cost_bps=-1), "config.cost_bps"),
    "cost_bps entry above range": (lambda s: s["config"].update(cost_bps={"TQQQ": 2000}), "config.cost_bps.TQQQ"),
    "cash_yield above range": (lambda s: s["config"].update(cash_yield=0.5), "config.cash_yield"),
    "unresolved cost symbol": (lambda s: s["config"].update(cost_bps={"TQQQ": 1.5}), "config.cost_bps"),
    "one-symbol sleeve": (lambda s: s["strategies"][4].update(safe={"BTAL": 1.0}), "strategies[4].safe"),
    "sleeve under-allocated": (lambda s: s["strategies"][4].update(safe={"BTAL": 0.5, "KMLM": 0.4}), "strategies[4].safe"),
    "sleeve over-allocated": (lambda s: s["strategies"][4].update(safe={"BTAL": 0.5, "KMLM": 0.6}), "strategies[4].safe"),
    "sleeve fraction zero": (lambda s: s["strategies"][4].update(safe={"BTAL": 1.0, "KMLM": 0.0}), "strategies[4].safe.KMLM"),
    "sleeve fraction negative": (lambda s: s["strategies"][4].update(safe={"BTAL": 1.5, "KMLM": -0.5}), "strategies[4].safe.KMLM"),
    "sleeve holds the risk asset": (lambda s: s["strategies"][4].update(safe={"TQQQ": 0.5, "BTAL": 0.5}), "strategies[4].safe.TQQQ"),
    "sleeve key not a symbol": (lambda s: s["strategies"][4].update(safe={7: 0.5, "BTAL": 0.5}), "strategies[4].safe"),
    # REGIME_SPEC R7 — the regime gate grammar.
    "fire alongside an sma kind": (lambda s: s["strategies"][2]["gate"].update(denominator="VIX3M", ratio_sma=10, fire=1.0), "strategies[2].gate"),
    "denominator without fire": (lambda s: s["strategies"][2]["gate"].update(denominator="VIX3M"), "strategies[2].gate.denominator"),
    "fire without ratio_sma": (lambda s: s["strategies"][2].update(gate={"symbol": "VIX", "assets": ["TQQQ"], "denominator": "VIX3M", "fire": 1.0}), "strategies[2].gate.ratio_sma"),
    "ratio_sma zero": (lambda s: s["strategies"][2].update(gate=G_R1 | {"ratio_sma": 0}), "strategies[2].gate.ratio_sma"),
    "hysteresis not below fire": (lambda s: s["strategies"][2].update(gate=G_R1 | {"hysteresis": 1.0}), "strategies[2].gate.hysteresis"),
    "fire off the cent grid": (lambda s: s["strategies"][2].update(gate=G_R1 | {"fire": 0.955}), "strategies[2].gate.fire"),
    "w_off above one": (lambda s: s["strategies"][2]["gate"].update(w_off=1.5), "strategies[2].gate.w_off"),
    "w_off boolean": (lambda s: s["strategies"][2]["gate"].update(w_off=True), "strategies[2].gate.w_off"),
    "denominator equals the symbol": (lambda s: s["strategies"][2].update(gate=G_R1 | {"denominator": "VIX"}), "strategies[2].gate.denominator"),
    "one-element gate list": (lambda s: s["strategies"][2].update(gate=[dict(G_SMA)]), "strategies[2].gate"),
    "nested gate list": (lambda s: s["strategies"][2].update(gate=[[dict(G_SMA)], dict(G_R1)]), "strategies[2].gate[0]"),
    "unknown key inside a composite member": (lambda s: s["strategies"][2].update(gate=[dict(G_SMA), G_R1 | {"sma_day": 200}]), "strategies[2].gate[1].sma_day"),
}


@pytest.mark.parametrize("mutate,path", INVALID.values(), ids=list(INVALID))
def test_invalid_specs_name_the_json_path(mutate, path):
    with pytest.raises(ValueError, match=re.escape(path)):
        build_bundle(broken(mutate))


def test_a_sleeve_builds_and_normalises_without_aliasing_the_entry():
    sleeve = {"BTAL": 0.75, "KMLM": 0.25}
    bundle = build_bundle(broken(lambda s: s["strategies"][4].update(safe=sleeve)))
    entry = normalised_spec(bundle)["strategies"][4]

    assert entry["safe"] == sleeve
    # Copied, not aliased: the normalised spec is the artefact's own record.
    assert entry["safe"] is not sleeve
    assert set(bundle.strategies[4].weights) == {"TQQQ", "BTAL", "KMLM"}

    # Regression: the string and null forms normalise byte-unchanged.
    for form in ("BTAL", None):
        plain = build_bundle(broken(lambda s: s["strategies"][4].update(safe=form)))
        assert normalised_spec(plain)["strategies"][4]["safe"] == form


def test_a_sleeve_symbol_may_carry_the_gate():
    # The gate universe is {risk} | the sleeve, so a sleeve leg is gateable.
    bundle = build_bundle(broken(lambda s: s["strategies"][4].update(
        safe={"BTAL": 0.5, "KMLM": 0.5},
        gate={"symbol": "QQQ", "assets": ["KMLM"], "sma_days": 200},
    )))
    assert tuple(bundle.strategies[4].gate.assets) == ("KMLM",)

    with pytest.raises(ValueError, match=re.escape("strategies[4].gate.assets")):
        build_bundle(broken(lambda s: s["strategies"][4].update(
            safe={"BTAL": 0.5, "KMLM": 0.5},
            gate={"symbol": "QQQ", "assets": ["DBMF"], "sma_days": 200},
        )))


def test_gate_asset_must_be_traded():
    with pytest.raises(ValueError, match=re.escape("strategies[2].gate.assets")):
        build_bundle(broken(lambda s: s["strategies"][2]["gate"].update(assets=["SPY"])))


def test_a_sweep_spec_names_the_right_entry_point():
    with pytest.raises(ValueError, match=re.escape("run it with `uv run sweep.py")):
        build_bundle(load_spec(SPECS / "sweep_vt.json"))


def test_config_costs_reach_config_and_normalise():
    # COST_MODEL_SPEC.md T6, bundle half: the optional fields land in Config
    # as configured, and normalised_spec always emits them — explicit zeros
    # when the spec never mentioned them.
    bundle = build_bundle(
        broken(lambda s: s["config"].update(cost_bps={"TQQQ": 1.5, "*": 6}, cash_yield=0.03))
    )
    assert bundle.config.cost_bps == {"TQQQ": 1.5, "*": 6.0}
    assert bundle.config.cash_yield == 0.03
    assert normalised_spec(bundle)["config"]["cost_bps"] == {"TQQQ": 1.5, "*": 6.0}
    assert normalised_spec(bundle)["config"]["cash_yield"] == 0.03

    defaults = normalised_spec(build_bundle(broken(lambda s: None)))["config"]
    assert defaults["cost_bps"] == 0.0
    assert defaults["cash_yield"] == 0.0


def test_config_end_is_optional_and_may_be_null():
    assert build_bundle(broken(lambda s: None)).config.end is None
    assert build_bundle(broken(lambda s: s["config"].update(end=None))).config.end is None
    assert build_bundle(
        broken(lambda s: s["config"].update(end="2024-12-31"))
    ).config.end == dt.date(2024, 12, 31)


# --- T2: auto-labels ---------------------------------------------------------


def label_of(entry) -> str:
    spec = {
        "schema_version": 1,
        "config": {"start": "2017-01-03", "initial_capital": 10000, "monthly_contribution": 500},
        "strategies": [entry, {"type": "fixed", "label": "bench", "weights": {"SPY": 1.0}}],
    }
    return build_bundle(spec).strategies[0].label


def test_auto_labels():
    assert label_of({"type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5}}) == "TQQQ50/BTAL50"
    assert label_of({"type": "fixed", "weights": {"SPY": 1.0}}) == "SPY100"
    assert label_of(
        {"type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
         "vol": {"kind": "ewma", "lam": 0.94}, "leverage": 3, "sigma_target": 0.45, "w_max": 0.5}
    ) == "VT TQQQ/BTAL t45 w0-50 QQQ:VOL_EWMA94"
    assert label_of(
        {"type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5},
         "gate": {"symbol": "QQQ", "assets": ["TQQQ"], "sma_months": 10, "contribution_exempt": True}}
    ) == "TQQQ50/BTAL50 gate QQQ<SMA10M+contrib"


def blend(safe, **kwargs) -> dict:
    return {
        "type": "vol_target", "risk": "TQQQ", "safe": safe, "vol_symbol": "QQQ",
        "vol": {"kind": "ewma", "lam": 0.94}, "leverage": 3, "sigma_target": 0.45,
        "w_max": 0.5,
    } | kwargs


def test_a_sleeve_labels_sorted_by_symbol_whatever_the_key_order():
    # Sorted, so one sleeve cannot spell two labels — and two slugs, which
    # would let the same strategy rank twice in one sweep.
    assert label_of(blend({"KMLM": 0.25, "BTAL": 0.75})) == (
        "VT TQQQ/BTAL75+KMLM25 t45 w0-50 QQQ:VOL_EWMA94"
    )
    assert label_of(blend({"BTAL": 0.75, "KMLM": 0.25})) == label_of(
        blend({"KMLM": 0.25, "BTAL": 0.75})
    )
    assert label_of(blend({"BTAL": 0.5, "KMLM": 0.5}, label="mine")) == "mine"


def test_sleeve_and_portfolio_fractions_slugify_apart():
    # `+` joins sleeve fractions where `fixed`'s `/` joins portfolio ones, and
    # slug() collapses both to `-`; the strategy kinds must still not converge.
    sleeve = slug(label_of(blend({"BTAL": 0.5, "KMLM": 0.5})))
    portfolio = slug(label_of({"type": "fixed", "weights": {"BTAL": 0.5, "KMLM": 0.5}}))

    assert sleeve == "vt-tqqq-btal50-kmlm50-t45-w0-50-qqq-vol-ewma94"
    assert portfolio == "btal50-kmlm50"


def test_safe_str_is_shared_by_the_label_and_sweep_params():
    # The gate_str precedent: one renderer, so params and labels cannot drift.
    assert sweep.safe_str is safe_str
    assert safe_str("BTAL") == "BTAL"
    assert safe_str(None) == "cash"
    assert safe_str({"KMLM": 0.25, "BTAL": 0.75}) == "BTAL75+KMLM25"


def test_explicit_label_wins():
    assert label_of({"type": "fixed", "label": "mine", "weights": {"TQQQ": 1.0}}) == "mine"


# --- REGIME_SPEC R7: regime gate renderings and normalisation ----------------


def fixed_with_gate(gate) -> dict:
    return {"type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5}, "gate": gate}


def test_regime_gate_renderings():
    # The five §5.2 renderings, exactly.
    assert label_of(fixed_with_gate(dict(G_SMA))) == "TQQQ50/BTAL50 gate QQQ<SMA200"
    assert label_of(
        fixed_with_gate(G_R1 | {"ratio_sma": 10})
    ) == "TQQQ50/BTAL50 gate VIX/VIX3M@10>=1.00"
    assert label_of(
        fixed_with_gate(G_R1 | {"ratio_sma": 10, "hysteresis": 0.05})
    ) == "TQQQ50/BTAL50 gate VIX/VIX3M@10>=1.00<0.95"
    assert label_of(
        fixed_with_gate(G_SMA | {"w_off": 0})
    ) == "TQQQ50/BTAL50 gate QQQ<SMA200 off0"
    assert label_of(
        fixed_with_gate([dict(G_SMA), G_R1 | {"w_off": 0}])
    ) == "TQQQ50/BTAL50 gate QQQ<SMA200|VIX/VIX3M@1>=1.00 off0"


def test_regime_gate_vt_label():
    assert label_of(
        {"type": "vol_target", "risk": "TQQQ", "safe": "BTAL", "vol_symbol": "QQQ",
         "vol": {"kind": "ewma", "lam": 0.80}, "leverage": 3, "sigma_target": 0.30,
         "w_max": 0.6,
         "gate": G_R1 | {"ratio_sma": 10, "hysteresis": 0.05}}
    ) == "VT TQQQ/BTAL t30 w0-60 QQQ:VOL_EWMA80 gate VIX/VIX3M@10>=1.00<0.95"


def test_regime_gate_normalises_with_hysteresis_filled():
    bundle = build_bundle(broken(lambda s: s["strategies"][2].update(gate=dict(G_R1))))
    entry = normalised_spec(bundle)["strategies"][2]

    # hysteresis is always present on a regime gate; w_off only when given.
    assert entry["gate"] == {
        "symbol": "VIX", "assets": ["TQQQ"], "contribution_exempt": False,
        "denominator": "VIX3M", "ratio_sma": 1, "fire": 1.0, "hysteresis": 0.0,
    }

    with_off = build_bundle(
        broken(lambda s: s["strategies"][2].update(gate=G_R1 | {"w_off": 0.3}))
    )
    assert normalised_spec(with_off)["strategies"][2]["gate"]["w_off"] == 0.3

    # The sma kind keeps its committed shape: no regime keys, no w_off.
    plain = build_bundle(broken(lambda s: None))
    sma_gate = normalised_spec(plain)["strategies"][2]["gate"]
    assert set(sma_gate) == {"symbol", "assets", "contribution_exempt", "sma_days"}


def test_composite_gate_round_trips_through_the_normalised_spec():
    composite = [dict(G_SMA), G_R1 | {"w_off": 0.0}]
    bundle = build_bundle(broken(lambda s: s["strategies"][2].update(gate=composite)))

    first = normalised_spec(bundle)
    assert [g["symbol"] for g in first["strategies"][2]["gate"]] == ["QQQ", "VIX"]

    again = normalised_spec(build_bundle(copy.deepcopy(first)))
    assert again == first

    # The strategy declares both regime symbols, per §3.3.
    st = bundle.strategies[2]
    assert set(st.data) == {"QQQ", "VIX", "VIX3M"}
    collect_indicators([st])  # the input rule holds without spec-author work


def test_identical_entries_collide_loudly():
    entry = {"type": "fixed", "weights": {"TQQQ": 0.5, "BTAL": 0.5}}
    spec = {
        "schema_version": 1,
        "config": {"start": "2017-01-03", "initial_capital": 10000, "monthly_contribution": 500},
        "strategies": [entry, dict(entry)],
    }
    with pytest.raises(ValueError, match="duplicate label"):
        build_bundle(spec)


# --- T3: equivalence to the hand-written strategies --------------------------


EQUIVALENT = {
    "TqqqBtal5050": (lambda: Fixed(weights={"TQQQ": 0.5, "BTAL": 0.5}), TqqqBtal5050),
    "Tqqq100": (lambda: Fixed(weights={"TQQQ": 1.0}), Tqqq100),
    "SpyBenchmark": (lambda: Fixed(weights={"SPY": 1.0}), SpyBenchmark),
    "TqqqBtalQqqSma200": (
        lambda: Fixed(
            weights={"TQQQ": 0.5, "BTAL": 0.5}, gate=Gate("QQQ", ["TQQQ"], sma_days=200)
        ),
        TqqqBtalQqqSma200,
    ),
}


@pytest.mark.parametrize("build,cls", EQUIVALENT.values(), ids=list(EQUIVALENT))
def test_fixed_matches_the_hand_written_class(build, cls):
    config = BUNDLES["default"].config
    handwritten = cls()
    prices = load_prices(
        GOLDEN_DIR, sorted(handwritten.weights), config.start,
        extra=handwritten.data, indicators=collect_indicators([handwritten]),
    )
    for got, want in zip(simulate(prices, build(), config), simulate(prices, handwritten, config)):
        assert_frame_equal(got, want)


# --- T7: the generic strategy contract ---------------------------------------


def every_strategy():
    for name, bundle in BUNDLES.items():
        for st in bundle.strategies:
            yield f"{name}:{st.label}", st, bundle.config
    for path in sorted(SPECS.glob("*.json")):
        if path.stem.startswith("sweep_"):
            continue  # sweep specs have their own grammar; sweep.py reads them
        bundle = build_bundle(load_spec(path))
        symbols = {s for st in bundle.strategies for s in (*st.weights, *st.data)}
        if any(not (GOLDEN_DIR / f"{s}.csv").exists() for s in symbols):
            # REGIME_SPEC §2.2 erratum: the flat snapshot gains no files, so a
            # spec reading VIX/VIX3M cannot run here; R10 and the §9 protocol
            # cover it on the dated snapshots instead.
            continue
        for st in bundle.strategies:
            yield f"{path.stem}:{st.label}", st, bundle.config


CONTRACT = {case[0]: case[1:] for case in every_strategy()}


@pytest.mark.parametrize("strategy,config", CONTRACT.values(), ids=list(CONTRACT))
def test_strategy_contract(strategy, config):
    prices = load_prices(
        GOLDEN_DIR, sorted(strategy.weights), config.start,
        extra=strategy.data, indicators=collect_indicators([strategy]),
    )
    for row in prices.iter_rows(named=True):
        if not row["is_rebalance_day"]:
            continue
        ctx = MarketDay(row, contribution=config.monthly_contribution)
        weights = strategy.balance(ctx)
        assert set(weights) == set(strategy.weights)
        assert all(w >= 0 for w in weights.values())
        assert sum(weights.values()) <= 1 + 1e-9
        for asset in strategy.weights:
            cap = strategy.buy_cap(asset, ctx)
            assert cap is None or cap >= 0

    # The same object run twice yields the same curves: no state leaks.
    for got, want in zip(
        simulate(prices, strategy, config), simulate(prices, strategy, config)
    ):
        assert_frame_equal(got, want)


# --- T8: specs/default.json reproduces the default bundle --------------------


def payload_of(bundle) -> dict:
    results = run_bundle(bundle, GOLDEN_DIR)
    bench = results[-1]
    correlations = [(r.label, correlation(r.twr, bench.twr)) for r in results[:-1]]
    payload = results_payload(
        bundle, "default", results, correlations, "2026-01-01T00:00:00Z", data_dir=GOLDEN_DIR
    )
    payload.pop("run", None)
    payload.pop("spec", None)
    for entry in payload["strategies"]:
        entry.pop("class", None)
        entry.pop("spec", None)
    return payload


def test_spec_default_reproduces_the_default_bundle():
    assert payload_of(build_bundle(load_spec(SPECS / "default.json"))) == payload_of(
        BUNDLES["default"]
    )
