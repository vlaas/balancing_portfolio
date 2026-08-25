# The rotation strategy, its grammar, labels and sweep params —
# ROTATION_SPEC §5–§7, T2–T7.

import copy
import datetime as dt
from pathlib import Path

import pytest
from test_simulate import START, frame

import sweep
from indicators import mom_monthly
from main import collect_indicators, run_bundle
from prices import load_prices
from results_json import dumps, results_payload, slug
from simulate import Config, simulate
from spec import build_bundle, load_spec, normalised_spec
from stats import correlation
from strategies.rotation import BestOf, Canary, Rotation
from strategy import MarketDay

GOLDEN_DIR = Path(__file__).parent / "data"
NET_DIR = GOLDEN_DIR / "2026-08-24-net15"
SPECS = Path(__file__).parents[1] / "specs"
DAY = dt.date(2020, 1, 2)
M1 = mom_monthly(1)  # MOM1M


def rot(**kwargs) -> Rotation:
    args = dict(assets=["A", "B", "C"], k=2, score=M1, label="rot")
    args.update(kwargs)
    return Rotation(**args)


def day(**scores) -> MarketDay:
    """A MarketDay carrying MOM1M values per symbol keyword."""
    return MarketDay({"date": DAY} | {f"{s}:MOM1M": v for s, v in scores.items()})


# --- T2 — ranking, hurdle and filter mechanics -------------------------------


def test_top_k_equal_weight():
    assert rot().balance(day(A=0.3, B=0.1, C=0.2)) == {"A": 0.5, "B": 0.0, "C": 0.5}
    assert rot(k=1).balance(day(A=0.1, B=0.3, C=0.2)) == {"A": 0.0, "B": 1.0, "C": 0.0}


def test_default_qualification_is_strict_above_zero():
    # C makes the top two but its score is not > 0 → its slot stays in cash.
    weights = rot().balance(day(A=0.3, B=-0.2, C=0.0))
    assert weights == {"A": 0.5, "B": 0.0, "C": 0.0}
    # With a fallback symbol the failed slot's mass routes there instead.
    st = rot(fallback="F")
    assert st.balance(day(A=0.3, B=-0.2, C=0.0)) == {
        "A": 0.5, "B": 0.0, "C": 0.0, "F": 0.5,
    }


def test_hurdle_qualification_is_strict_and_per_asset():
    st = rot(hurdle="H")
    # B ties the hurdle exactly: strict > fails the slot.
    assert st.balance(day(A=0.3, B=0.2, C=0.1, H=0.2)) == {
        "A": 0.5, "B": 0.0, "C": 0.0,
    }


def test_absolute_filter_gates_all_slots_together():
    absolute = rot(filter_on="S", hurdle="H", fallback="F")
    per_asset = rot(hurdle="H", fallback="F")
    # The constructed month: S clears the hurdle while A's own score does not.
    scores = dict(A=0.1, B=0.05, C=0.01, S=0.4, H=0.2)
    assert absolute.balance(day(**scores)) == {
        "A": 0.5, "B": 0.5, "C": 0.0, "F": 0.0,
    }
    assert per_asset.balance(day(**scores)) == {
        "A": 0.0, "B": 0.0, "C": 0.0, "F": 1.0,
    }
    # S failing routes everything defensive regardless of the asset scores.
    assert absolute.balance(day(A=0.9, B=0.8, C=0.7, S=0.1, H=0.2)) == {
        "A": 0.0, "B": 0.0, "C": 0.0, "F": 1.0,
    }


def test_filter_none_holds_a_negative_momentum_slot_anyway():
    # Every asset is below zero: the default qualification sends the whole
    # portfolio defensive, the unconditional form still holds the top two.
    unconditional = rot(filter_none=True, fallback="F")
    default = rot(fallback="F")
    scores = dict(A=-0.05, B=-0.30, C=-0.10)
    assert unconditional.balance(day(**scores)) == {
        "A": 0.5, "B": 0.0, "C": 0.5, "F": 0.0,
    }
    assert default.balance(day(**scores)) == {
        "A": 0.0, "B": 0.0, "C": 0.0, "F": 1.0,
    }
    # Only the test drops out: the canary still routes its fraction.
    with_canary = rot(filter_none=True, canary=Canary(("X",), 1, M1), fallback="F")
    assert with_canary.balance(day(A=-0.05, B=-0.30, C=-0.10, X=-0.01)) == {
        "A": 0.0, "B": 0.0, "C": 0.0, "F": 1.0,
    }


def test_filter_none_excludes_the_absolute_test():
    with pytest.raises(AssertionError, match="filter_none excludes"):
        rot(filter_none=True, hurdle="H")


# --- T3 — canary fractions, slot replacement, role collisions ----------------


def canary_rot(**kwargs) -> Rotation:
    return rot(canary=Canary(("X", "Y"), 2, M1), fallback="F", **kwargs)


def test_canary_fraction_is_n_bad_over_breadth():
    st = canary_rot()
    # 1 of 2 canaries non-positive (zero counts) → half defensive, the
    # offensive half still top-k at (1 - d) / k each.
    assert st.balance(day(A=0.3, B=0.1, C=0.2, X=0.0, Y=0.1)) == pytest.approx(
        {"A": 0.25, "B": 0.0, "C": 0.25, "F": 0.5}
    )
    # 2 of 2 → fully defensive.
    assert st.balance(day(A=0.3, B=0.1, C=0.2, X=-0.1, Y=0.0)) == pytest.approx(
        {"A": 0.0, "B": 0.0, "C": 0.0, "F": 1.0}
    )


def test_breadth_caps_the_fraction_at_one():
    st = rot(canary=Canary(("X", "Y"), 1, M1), fallback="F")
    assert st.balance(day(A=0.3, B=0.1, C=0.2, X=-0.1, Y=0.2)) == pytest.approx(
        {"A": 0.0, "B": 0.0, "C": 0.0, "F": 1.0}
    )


def test_a_failed_slot_joins_the_canary_pool():
    st = canary_rot()
    # d = 0.5; C makes the top two but fails: pool = 0.5 + 0.25.
    assert st.balance(day(A=0.3, B=-0.3, C=-0.2, X=0.0, Y=0.1)) == pytest.approx(
        {"A": 0.25, "B": 0.0, "C": 0.0, "F": 0.75}
    )


def test_a_role_collision_accumulates_weight():
    # A is both an offensive pick and the fallback: the weights add.
    st = rot(assets=["A", "B"], k=1, canary=Canary(("X",), 2, M1), fallback="A")
    assert st.balance(day(A=0.3, B=0.1, X=-0.1)) == pytest.approx(
        {"A": 1.0, "B": 0.0}
    )


def test_a_sleeve_fallback_splits_the_pool_by_fractions():
    st = rot(fallback={"F": 0.6, "G": 0.4})
    assert st.balance(day(A=0.3, B=-0.2, C=-0.1)) == pytest.approx(
        {"A": 0.5, "B": 0.0, "C": 0.0, "F": 0.3, "G": 0.2}
    )


def test_best_of_routes_the_whole_pool_to_the_argmax():
    st = rot(fallback=BestOf(("F", "G"), M1))
    assert st.balance(day(A=0.3, B=-0.2, C=-0.1, F=0.01, G=0.05)) == pytest.approx(
        {"A": 0.5, "B": 0.0, "C": 0.0, "F": 0.0, "G": 0.5}
    )
    # No sign filter: the least-negative candidate still takes everything.
    assert st.balance(day(A=-0.3, B=-0.2, C=-0.1, F=-0.04, G=-0.02)) == pytest.approx(
        {"A": 0.0, "B": 0.0, "C": 0.0, "F": 0.0, "G": 1.0}
    )
    # An exact tie goes to list order.
    assert st.balance(day(A=0.3, B=-0.2, C=-0.1, F=0.02, G=0.02)) == pytest.approx(
        {"A": 0.5, "B": 0.0, "C": 0.0, "F": 0.5, "G": 0.0}
    )


# --- T4 — warm-up short-circuit ----------------------------------------------


def test_any_missing_score_holds_everything_in_cash():
    zero = {"A": 0.0, "B": 0.0, "C": 0.0}
    assert rot().balance(day(A=None, B=0.1, C=0.2)) == zero
    assert rot(hurdle="H").balance(day(A=0.3, B=0.1, C=0.2, H=None)) == zero
    assert rot(filter_on="S").balance(day(A=0.3, B=0.1, C=0.2, S=None)) == zero
    st = canary_rot()
    assert st.balance(day(A=0.3, B=0.1, C=0.2, X=None, Y=0.1)) == zero | {"F": 0.0}
    best = rot(fallback=BestOf(("F", "G"), M1))
    assert best.balance(day(A=0.3, B=0.1, C=0.2, F=None, G=0.1)) == zero | {
        "F": 0.0, "G": 0.0,
    }


def test_warm_up_and_transitions_row_by_row_through_the_engine():
    prices = frame(
        {
            "A": [10.0] * 5, "B": [10.0] * 5, "C": [10.0] * 5, "F": [10.0] * 5,
            "A:MOM1M": [None, 0.3, 0.3, -0.2, 0.3],
            "B:MOM1M": [None, 0.1, -0.2, -0.3, 0.2],
            "C:MOM1M": [None, 0.2, -0.1, -0.1, 0.1],
            "H:MOM1M": [0.0, 0.0, 0.0, 0.0, 0.05],
        },
        [False, True, True, True, True],
    )
    st = rot(hurdle="H", fallback="F")

    _, _, allocations = simulate(prices, st, Config(START, 10_000.0, 0.0))

    expected = [  # per day: A, B, C, F, CASH targets
        [0.0, 0.0, 0.0, 0.0, 1.0],  # warm-up: all cash, loud in the frame
        [0.5, 0.0, 0.5, 0.0, 0.0],  # A and C on top, both clear the hurdle
        [0.5, 0.0, 0.0, 0.5, 0.0],  # C's slot fails → its mass to F
        [0.0, 0.0, 0.0, 1.0, 0.0],  # every slot fails → all defensive
        [0.5, 0.5, 0.0, 0.0, 0.0],  # B replaces C and clears the 0.05 hurdle
    ]
    assert allocations["asset"].to_list()[:5] == ["A", "B", "C", "F", "CASH"]
    for i, targets in enumerate(expected):
        rows = allocations[5 * i : 5 * (i + 1)]
        assert rows["target"].to_list() == pytest.approx(targets), f"day {i}"


# --- ROTATION_SWEEP_SPEC T4 — the native lanes open warm (§4) ----------------

NATIVE_LANES = ["sweep_rot_gem_native", "sweep_rot_gtaa_native", "sweep_rot_haa_native"]


def opening_rows(spec: dict, days: int = 45):
    """The lane's strategies, their normalised entries, and its opening
    rebalance rows: day 0 — which `simulate` always rebalances — plus the
    first month-end.

    Read straight off the frame rather than simulated. The warm-up
    short-circuit is a property of `balance()`, and truncating the frame
    cannot fake warmth: `prices._read_symbol` computes every indicator on the
    symbol's own full history before the join and the `date >= start` filter.
    (A short `Config.end` is not an option anyway — a window with no drawdown
    yet takes `stats.top_drawdowns` to an empty list.)"""
    entries = [e["entry"] for e in sweep.expand(spec["template"])] + spec["baselines"]
    start = dt.date.fromisoformat(spec["windows"]["start"])
    end = start + dt.timedelta(days=days)
    strategies = build_bundle(
        sweep._ordinary(spec, entries, start.isoformat(), end.isoformat())
    ).strategies
    traded = sorted({s for st in strategies for s in st.weights})
    prices = load_prices(
        NET_DIR, traded, start, end=end,
        extra=sorted({s for st in strategies for s in st.data} - set(traded)),
        indicators=collect_indicators(strategies),
    )
    rows = [
        row for i, row in enumerate(prices.iter_rows(named=True))
        if i == 0 or row["is_rebalance_day"]
    ]
    return strategies, entries, rows


@pytest.mark.parametrize("name", NATIVE_LANES, ids=lambda n: n.split("_")[2])
def test_every_native_grid_point_opens_warm(name):
    # ROTATION_SWEEP_SPEC §4 asserted rather than trusted: on its native
    # window no grid point — and no baseline — spends its opening months in
    # the §5.1 step-1 cash short-circuit. Loading is itself part of the test:
    # a start before a traded fallback's inception dies inside load_prices,
    # which is what moved GTAA's native window to 2007-06 (§12.2).
    spec = load_spec(SPECS / f"{name}.json")
    strategies, entries, rows = opening_rows(spec)

    # The lanes start on trading days, so the window needs no snapping.
    assert rows[0]["date"] == dt.date.fromisoformat(spec["windows"]["start"])
    for st, entry in zip(strategies, entries):
        for symbol, declared in st.indicators.items():
            for indicator in declared:
                column = f"{symbol}:{indicator.name}"
                assert rows[0][column] is not None, f"{st.label}: {column} is warming up"
        # Warm and with somewhere to route a failed slot: every ranked slot's
        # mass lands. A cash fallback may legitimately sit a month out on the
        # signal, so for those points warmth is the whole invariant.
        if entry.get("fallback") is None:
            continue
        for row in rows:
            weights = st.balance(MarketDay(row))
            assert sum(weights.values()) == pytest.approx(1.0), (
                f"{st.label} is all cash on {row['date']}"
            )


# --- T5 — determinism --------------------------------------------------------


def test_an_exact_tie_breaks_by_assets_order():
    scores = dict(A=0.2, B=0.1, C=0.2)
    assert rot(k=1).balance(day(**scores)) == {"A": 1.0, "B": 0.0, "C": 0.0}
    reordered = rot(assets=["C", "B", "A"], k=1)
    assert reordered.balance(day(**scores)) == {"C": 1.0, "B": 0.0, "A": 0.0}


T5_SPEC = {
    "schema_version": 1,
    "config": {
        "start": "2017-01-03",
        "initial_capital": 10_000.0,
        "monthly_contribution": 500.0,
    },
    "strategies": [
        {
            "type": "rotation",
            "assets": ["QQQ", "SPY", "TQQQ"],
            "k": 1,
            "score": {"months": 12},
            "fallback": "BTAL",
        },
        {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}},
    ],
}


def test_repeated_runs_are_byte_identical():
    bundle = build_bundle(T5_SPEC)

    def payload() -> str:
        results = run_bundle(bundle, GOLDEN_DIR)
        bench = results[-1]
        correlations = [
            (r.label, correlation(r.twr, bench.twr)) for r in results[:-1]
        ]
        return dumps(results_payload(
            bundle, "rot", results, correlations, "2026-01-01T00:00:00Z",
            data_dir=GOLDEN_DIR,
        ))

    first = payload()
    assert payload() == first


# --- Universe, data and indicator declarations (§5, the SafeSwitch trick) ----


def test_the_universe_rides_at_zero_and_balance_returns_it_whole():
    st = rot(hurdle="H", fallback=BestOf(("F", "G"), M1))
    assert st.weights == {"A": 0.0, "B": 0.0, "C": 0.0, "F": 0.0, "G": 0.0}
    assert st.data == ("H",)
    balance = st.balance(day(A=0.3, B=0.1, C=0.2, H=0.0, F=0.1, G=0.2))
    assert set(balance) == set(st.weights)


def test_declarations_merge_by_name():
    # A canary sharing the main score declares it once; a best_of with its
    # own score declares only that on its symbols.
    st = rot(
        canary=Canary(("A", "X"), 1, M1),
        fallback=BestOf(("F",), mom_monthly(3)),
        hurdle="H",
    )
    assert st.data == ("H", "X")
    assert [i.name for i in st.indicators["A"]] == ["MOM1M"]
    assert [i.name for i in st.indicators["X"]] == ["MOM1M"]
    assert [i.name for i in st.indicators["F"]] == ["MOM3M"]
    assert [i.name for i in st.indicators["H"]] == ["MOM1M"]


def test_constructor_validation():
    with pytest.raises(AssertionError, match="unique"):
        rot(assets=["A", "A", "B"])
    with pytest.raises(AssertionError, match="1 <= k"):
        rot(k=4)
    with pytest.raises(AssertionError, match="filter_on equals hurdle"):
        rot(filter_on="S", hurdle="S")
    with pytest.raises(AssertionError, match="sum"):
        rot(fallback={"F": 0.5, "G": 0.3})


# --- T6 — grammar ------------------------------------------------------------

BENCH = {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}}
CONFIG = {"start": "2008-07-01", "initial_capital": 10_000.0, "monthly_contribution": 0.0}

# The four §7 examples, labels pinned (T7).
EXAMPLES = {
    "ROT SPY+VEU top1 12M@SPY>BIL fb AGG": {
        "type": "rotation", "assets": ["SPY", "VEU"], "k": 1,
        "score": {"months": 12},
        "filter": {"on": "SPY", "hurdle": "BIL"}, "fallback": "AGG",
    },
    "ROT SPY+EFA+IEF+DBC+VNQ top5 gap10M fb cash": {
        "type": "rotation", "assets": ["SPY", "EFA", "IEF", "DBC", "VNQ"],
        "k": 5, "score": {"kind": "sma_gap", "months": 10},
    },
    "ROT SPY+SCZ top1 1-3-6U fb best(TIP+TLT@1M)": {
        "type": "rotation", "assets": ["SPY", "SCZ"], "k": 1,
        "score": {"kind": "avg", "months": [1, 3, 6]},
        "fallback": {
            "kind": "best_of", "symbols": ["TIP", "TLT"], "score": {"months": 1},
        },
    },
    "ROT SPY+IWM+VEA+VWO+VNQ+DBC+IEF+TLT top4 1-3-6-12U can TIP/1 fb best(BIL+IEF)": {
        "type": "rotation",
        "assets": ["SPY", "IWM", "VEA", "VWO", "VNQ", "DBC", "IEF", "TLT"],
        "k": 4, "score": {"kind": "avg", "months": [1, 3, 6, 12]},
        "canary": {"symbols": ["TIP"], "breadth": 1},
        "fallback": {"kind": "best_of", "symbols": ["BIL", "IEF"]},
    },
}


def build(*entries) -> object:
    return build_bundle({
        "schema_version": 1, "config": dict(CONFIG),
        "strategies": [*entries, dict(BENCH)],
    })


@pytest.mark.parametrize("label", EXAMPLES, ids=lambda l: l.split()[1])
def test_example_specs_build_round_trip_and_pin_their_labels(label):
    bundle = build(EXAMPLES[label])
    assert bundle.strategies[0].label == label

    normalised = normalised_spec(bundle)
    again = normalised_spec(build_bundle(normalised))
    assert again == normalised


def test_the_normalised_spec_fills_inherited_scores():
    haa = list(EXAMPLES)[3]
    spec = build(EXAMPLES[haa]).strategies[0].spec
    main = {"kind": "avg", "months": [1, 3, 6, 12]}
    assert spec["score"] == main
    assert spec["canary"]["score"] == main
    assert spec["fallback"]["score"] == main
    # An explicit best_of score survives as written.
    adm = list(EXAMPLES)[2]
    spec = build(EXAMPLES[adm]).strategies[0].spec
    assert spec["fallback"]["score"] == {"months": 1}
    # The cash default is explicit, so results.json is self-describing.
    gtaa = list(EXAMPLES)[1]
    assert build(EXAMPLES[gtaa]).strategies[0].spec["fallback"] is None


def broken(label: str, mutate) -> dict:
    entry = copy.deepcopy(EXAMPLES[label])
    mutate(entry)
    return entry


GEM, GTAA, ADM, HAA = EXAMPLES


INVALID = {
    "k above the universe": (
        lambda e: e.update(k=3), GEM, r"strategies\[0\].k"),
    "duplicate assets": (
        lambda e: e.update(assets=["SPY", "SPY"]), GEM, r"strategies\[0\].assets"),
    "empty filter object": (
        lambda e: e.update(filter={}), GEM, "absence is the spelling"),
    "on equals hurdle": (
        lambda e: e.update(filter={"on": "SPY", "hurdle": "SPY"}), GEM, "on equals hurdle"),
    "unknown filter kind": (
        lambda e: e.update(filter={"kind": "all"}), GEM, "unknown kind 'all'"),
    "filter kind beside on": (
        lambda e: e.update(filter={"kind": "none", "on": "SPY"}), GEM,
        r"strategies\[0\].filter.on: unknown key"),
    "filter kind beside hurdle": (
        lambda e: e.update(filter={"kind": "none", "hurdle": "BIL"}), GEM,
        r"strategies\[0\].filter.hurdle: unknown key"),
    "single-symbol best_of": (
        lambda e: e["fallback"].update(symbols=["TIP"]), ADM, "string form"),
    "single-symbol sleeve": (
        lambda e: e.update(fallback={"AGG": 1.0}), GEM, "is the string form; use it"),
    "sleeve fractions off one": (
        lambda e: e.update(fallback={"AGG": 0.6, "TLT": 0.3}), GEM, "sum to 0.9"),
    "breadth out of range": (
        lambda e: e["canary"].update(breadth=2), HAA, r"in \[1, 1\]"),
    "unknown score kind": (
        lambda e: e.update(score={"kind": "median", "months": [1, 3]}), GEM,
        "unknown kind 'median'"),
    "weights length mismatch": (
        lambda e: e.update(score={"kind": "weighted", "months": [1, 3], "weights": [1]}),
        GEM, "expected a list of 2 weights"),
    "non-ascending months": (
        lambda e: e.update(score={"kind": "avg", "months": [3, 1]}), GEM,
        "strictly ascending"),
    "months below one": (
        lambda e: e.update(score={"months": 0}), GEM, "expected an integer >= 1"),
    "sma_gap months below two": (
        lambda e: e.update(score={"kind": "sma_gap", "months": 1}), GEM,
        "expected an integer >= 2"),
    "missing weights": (
        lambda e: e.update(score={"kind": "weighted", "months": [1, 3]}), GEM,
        "score.weights: missing key"),
    "unknown entry key": (
        lambda e: e.update(hurdle="BIL"), GEM, r"strategies\[0\].hurdle: unknown key"),
    "fallback of the wrong type": (
        lambda e: e.update(fallback=3), GEM, "expected null, a symbol"),
}


@pytest.mark.parametrize("case", INVALID, ids=str)
def test_invalid_specs_fail_loudly_with_the_json_path(case):
    mutate, label, match = INVALID[case]
    with pytest.raises(ValueError, match=match):
        build(broken(label, mutate))


# --- T7 — labels and slugs ---------------------------------------------------


def test_on_only_and_hurdle_only_filters_slugify_apart():
    # Two rotations differing only in the filter's structure: `@SPY` and
    # `>SPY` would collide (§7 errata: on-only renders `@SPY>0`).
    on_only = broken(GEM, lambda e: e.update(filter={"on": "SPY"}))
    hurdle_only = broken(GEM, lambda e: e.update(filter={"hurdle": "SPY"}))

    bundle = build(on_only, hurdle_only)
    labels = [st.label for st in bundle.strategies[:2]]
    assert labels == [
        "ROT SPY+VEU top1 12M@SPY>0 fb AGG",
        "ROT SPY+VEU top1 12M>SPY fb AGG",
    ]
    assert len({slug(l) for l in labels}) == 2


def test_the_unconditional_filter_labels_and_normalises_as_a_word():
    # ` all` takes the separating space the operator forms do not, and the
    # three filter spellings stay three distinct labels and slugs.
    unconditional = broken(GEM, lambda e: e.update(filter={"kind": "none"}))
    default = broken(GEM, lambda e: e.pop("filter"))

    bundle = build(unconditional, default, dict(EXAMPLES[GEM]))
    labels = [st.label for st in bundle.strategies[:3]]
    assert labels == [
        "ROT SPY+VEU top1 12M all fb AGG",
        "ROT SPY+VEU top1 12M fb AGG",
        "ROT SPY+VEU top1 12M@SPY>BIL fb AGG",
    ]
    assert len({slug(l) for l in labels}) == 3
    # Carried verbatim, and the default's absence stays an absence.
    assert bundle.strategies[0].spec["filter"] == {"kind": "none"}
    assert "filter" not in bundle.strategies[1].spec
    normalised = normalised_spec(bundle)
    assert normalised_spec(build_bundle(normalised)) == normalised


def test_two_identical_rotations_collide_at_build():
    with pytest.raises(ValueError, match="duplicate label"):
        build(dict(EXAMPLES[GEM]), dict(EXAMPLES[GEM]))


def test_rebalance_cadence_lands_in_label_and_spec():
    entry = broken(GEM, lambda e: e.update(rebalance={"months": 3}))
    st = build(entry).strategies[0]
    assert st.label.endswith(" fb AGG rb 3m")
    assert st.rebalance is not None
    assert st.spec["rebalance"] == {"months": 3, "offset": 0}


# --- T8 — real-data golden on the frozen net15 snapshot ----------------------
#
# Produced once by this implementation and eyeballed against direction
# (ROTATION_SPEC §8/§9 pre-registration): GEM's drawdown undercuts SPY's on
# the same window (-0.34 vs -0.47) and its CAGR does not beat SPY's, per the
# out-of-sample literature; GTAA-5 cuts drawdown much further at a lower
# CAGR (no cash yield in this config). Same rule as every golden: a later
# failure means the engine changed; fix the bug or update the dict in the
# same commit with the reason. Never refresh the snapshot.


GOLDEN_SPEC = {
    "schema_version": 1,
    "config": {
        "start": "2008-07-01", "end": "2026-08-24",
        "initial_capital": 10_000.0, "monthly_contribution": 500.0,
    },
    "strategies": [
        {
            "type": "rotation", "assets": ["SPY", "EFA"], "k": 1,
            "score": {"months": 12},
            "filter": {"on": "SPY", "hurdle": "BIL"}, "fallback": "AGG",
        },
        {
            "type": "rotation", "assets": ["SPY", "EFA", "IEF", "DBC", "VNQ"],
            "k": 5, "score": {"kind": "sma_gap", "months": 10},
        },
        {"type": "fixed", "label": "SPY benchmark", "weights": {"SPY": 1.0}},
    ],
}

GOLDEN_ROT = {
    "ROT SPY+EFA top1 12M@SPY>BIL fb AGG": (309_125.31, 0.0842, -0.3377),
    "ROT SPY+EFA+IEF+DBC+VNQ top5 gap10M fb cash": (199_414.05, 0.0425, -0.1396),
    "SPY benchmark": (546_186.86, 0.1203, -0.4716),
}


def test_rotation_bundle_reproduces_the_golden_numbers():
    results = run_bundle(build_bundle(GOLDEN_SPEC), NET_DIR)

    assert [r.label for r in results] == list(GOLDEN_ROT)
    for result in results:
        final, cagr, max_dd = GOLDEN_ROT[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["cagr"] == pytest.approx(cagr, abs=0.00005)
        assert result.stats["max_drawdown"] == pytest.approx(max_dd, abs=0.00005)

    gem, _, spy = results
    assert gem.stats["max_drawdown"] > spy.stats["max_drawdown"]


# --- Sweep params render as label fragments (§7) -----------------------------


def test_sweep_params_render_as_label_fragments():
    template = {
        "type": "rotation",
        "assets": {"grid": [["SPY", "VEU"], ["SPY", "EFA"]]},
        "k": 1,
        "score": {"grid": [{"months": 12}, {"kind": "avg", "months": [1, 3, 6]}]},
        "filter": {"grid": [None, {"on": "SPY"}]},
        "fallback": {"grid": [
            "AGG", {"kind": "best_of", "symbols": ["BIL", "IEF"]},
        ]},
    }

    elements = sweep.expand(template)

    assert len(elements) == 16
    params = [e["params"] for e in elements]
    assert {p["assets"] for p in params} == {"SPY+VEU", "SPY+EFA"}
    assert {p["score"] for p in params} == {"12M", "1-3-6U"}
    assert {p["filter"] for p in params} == {None, "@SPY>0"}
    assert {p["fallback"] for p in params} == {"AGG", "best(BIL+IEF)"}
    labels = [e["label"] for e in elements]
    assert len(set(labels)) == 16  # every grid combination is label-visible


def test_a_filter_grid_spells_three_distinct_behaviours():
    # ROTATION_SWEEP_SPEC §2: `null` deletes the key (per-asset > 0),
    # `{"kind": "none"}` is unconditional, and the object form is the test.
    # All three must survive expansion as separate points.
    template = {
        "type": "rotation", "assets": ["SPY", "VEU"], "k": 1,
        "score": {"months": 12}, "fallback": "AGG",
        "filter": {"grid": [
            {"kind": "none"}, {"on": "SPY", "hurdle": "BIL"}, None,
        ]},
    }

    elements = sweep.expand(template)

    assert [e["params"]["filter"] for e in elements] == [
        "all", "@SPY>BIL", None,
    ]
    assert [e["label"] for e in elements] == [
        "ROT SPY+VEU top1 12M all fb AGG",
        "ROT SPY+VEU top1 12M@SPY>BIL fb AGG",
        "ROT SPY+VEU top1 12M fb AGG",
    ]
    assert [e["entry"].get("filter") for e in elements] == [
        {"kind": "none"}, {"on": "SPY", "hurdle": "BIL"}, None,
    ]
