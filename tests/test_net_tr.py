"""NET_TR_SPEC §8 — the net-of-withholding total-return dataset.

N1 layout/self-containment, N2 scaled ratio invariants, N3 per-jump
exactness, N4 yield contraction, N5 byte-reproducibility, N6 generator
guards, N7 net goldens, N8 sweep provenance. Constants come from
make_net_tr; tests/test_total_return.py keeps its own local TAU untouched.
"""

import dataclasses
import datetime as dt
import filecmp
import hashlib
import json
import math
from pathlib import Path

import polars as pl
import pytest

from bundles import BUNDLES
from main import run_bundle
from make_net_tr import FLAT_MAX, JUMP_MIN, TAU, main as net_main
from sweep import main as sweep_main
from test_sweep import T6_SPEC

GOLDEN_DIR = Path(__file__).parent / "data"
TR_DIR = GOLDEN_DIR / "2026-08-20"
NET_DIR = GOLDEN_DIR / "2026-08-20-net15"
SYMBOLS = ["TQQQ", "BTAL", "QQQ", "SPY", "DBMF", "KMLM"]
W = 0.15
MATCHED_END = dt.date(2026, 8, 14)


def read_close(path: Path) -> pl.DataFrame:
    return pl.read_csv(
        path,
        columns=["time", "close"],
        schema_overrides={"close": pl.Float64},
        try_parse_dates=True,
    )


def series(root: Path, symbol: str) -> tuple[pl.DataFrame, pl.Series]:
    """(price frame, adjusted/price ratio) for one symbol of a dataset root."""
    adjusted = read_close(root / f"{symbol}.csv")
    price = read_close(root / "price" / f"{symbol}.csv")
    assert adjusted["time"].equals(price["time"])
    return price, adjusted["close"] / price["close"]


def jump_rows(ratio: pl.Series) -> list[int]:
    steps = ratio.log().diff()
    return [i for i, s in enumerate(steps) if s is not None and s >= JUMP_MIN]


# --- N1 — layout and self-containment ----------------------------------------


def test_net_snapshot_layout_and_self_containment():
    for symbol in SYMBOLS:
        net = pl.read_csv(NET_DIR / f"{symbol}.csv")
        assert net.columns == ["time", "close"]
        assert filecmp.cmp(
            NET_DIR / "price" / f"{symbol}.csv",
            TR_DIR / "price" / f"{symbol}.csv",
            shallow=False,
        )
        parent = pl.read_csv(TR_DIR / f"{symbol}.csv", columns=["time"])
        assert net["time"].equals(parent["time"])
    assert (NET_DIR / "README.md").is_file()


# --- N2 — scaled ratio invariants --------------------------------------------


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_scaled_ratio_invariants(symbol: str) -> None:
    _, r = series(TR_DIR, symbol)
    _, rn = series(NET_DIR, symbol)

    assert (rn - r).min() >= -1e-12
    assert rn.max() <= 1 + 1e-6
    assert rn[-1] == r[-1]

    q = (rn / r).log()
    assert q.min() >= 0.0
    q_steps = q.diff().slice(1)
    assert q_steps.max() <= 1e-12

    jump = r.log().diff().slice(1) >= JUMP_MIN
    assert q_steps.filter(~jump).abs().max() < 1e-12
    assert q.slice(jump_rows(r)[-1]).abs().max() == 0.0

    assert (rn.log().diff().slice(1) >= JUMP_MIN).equals(jump)


# --- N3 — per-jump exactness: the withholding semantics in one line ----------


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_each_jump_reinvests_exactly_the_net_distribution(symbol: str) -> None:
    price, r = series(TR_DIR, symbol)
    _, rn = series(NET_DIR, symbol)
    p = price["close"]

    rows = jump_rows(r)
    assert rows
    for s in rows:
        gross = p[s - 1] * (1 - r[s - 1] / r[s])
        net = p[s - 1] * (1 - rn[s - 1] / rn[s])
        assert net == pytest.approx((1 - W) * gross, abs=1e-9)


# --- N4 — yield contraction --------------------------------------------------


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_cumulative_yield_contracts_by_the_withholding(symbol: str) -> None:
    price, r = series(TR_DIR, symbol)
    _, rn = series(NET_DIR, symbol)
    years = (price["time"][-1] - price["time"][0]).days / 365.25

    y_gross = -math.log(r[0]) / years
    y_net = -math.log(rn[0]) / years
    # Upper bound is Bernoulli ((1-d)^(1-w) <= 1 - (1-w)*d per jump); the
    # lower bound absorbs the second-order term of the largest jumps (KMLM's
    # 2022 distribution, d ~ 13%, is the extreme). Measured at w = 0.15:
    # ratios 0.8441 (KMLM) to 0.8498 (TQQQ/QQQ).
    assert 0.98 * (1 - W) <= y_net / y_gross <= (1 - W) + 1e-12


# --- N5 — byte-reproducibility: the committed snapshot is exactly what the ---
# committed generator produces from the committed parent; nothing in the
# generator may read a clock.


def test_generator_reproduces_the_committed_snapshot_byte_for_byte(tmp_path):
    out = tmp_path / "net"
    net_main([str(TR_DIR), "--out", str(out)])

    produced = sorted(p.relative_to(out) for p in out.rglob("*") if p.is_file())
    committed = sorted(p.relative_to(NET_DIR) for p in NET_DIR.rglob("*") if p.is_file())
    assert produced == committed
    assert len(produced) == 15  # 13 + the two REGIME_SPEC §2.2 index files
    for rel in committed:
        assert filecmp.cmp(out / rel, NET_DIR / rel, shallow=False), rel


# --- N7 — net goldens: the default bundle on the net snapshot over the -------
# matched window (the parent's calendar pin covers the net snapshot by
# byte-copy). Reference values from NET_TR_SPEC §7, reproduced to the cent on
# the first run — a larger deviation is a construction bug, not float noise
# (C is a product of <= 135 doubles). The net-gross gap is small here
# (~-0.19%/yr CAGR on the 50/50) because BTAL's yield is small; the
# correction's weight is in the safe-swap universe.

GOLDEN_NET = {
    "TQQQ/BTAL 50/50": (254_913.36, 0.2467, -0.4478),
    "TQQQ 100%": (688_470.64, 0.4222, -0.8167),
    "TQQQ/BTAL SMA gate": (245_139.65, 0.2400, -0.3773),
    "SPY benchmark": (167_200.29, 0.1521, -0.3374),
}


def matched_window_bundle(**config_changes):
    bundle = BUNDLES["default"]
    config = dataclasses.replace(bundle.config, end=MATCHED_END, **config_changes)
    return dataclasses.replace(bundle, config=config)


def test_default_bundle_reproduces_the_net_golden_numbers() -> None:
    results = run_bundle(matched_window_bundle(), NET_DIR)

    assert [r.label for r in results] == list(GOLDEN_NET)
    for result in results:
        final, cagr, max_dd = GOLDEN_NET[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["cagr"] == pytest.approx(cagr, abs=0.00005)
        assert result.stats["max_drawdown"] == pytest.approx(max_dd, abs=0.00005)

    # Cross-snapshot sandwich, same window: withholding gives back part of the
    # distribution value, never all of it — price < net < gross finals.
    price_finals = {
        r.label: r.stats["final_value"] for r in run_bundle(BUNDLES["default"], GOLDEN_DIR)
    }
    gross_finals = {
        r.label: r.stats["final_value"] for r in run_bundle(matched_window_bundle(), TR_DIR)
    }
    for label in ("TQQQ/BTAL 50/50", "SPY benchmark"):
        assert price_finals[label] < GOLDEN_NET[label][0] < gross_finals[label]


# Net cost golden: the same bundle under the tastytrade base schedule and 3%
# cash yield — the exact configuration of every decision run from here on.
# Values pinned by this implementation once and eyeballed: finals sit just
# below the zero-cost net goldens (SPY just above, cash yield on the
# contribution buffer outweighing its sub-bp fees, as in the gross twin) and
# fees are within a few dollars of the gross T8 fees.

COST_GOLDEN_NET = {
    "TQQQ/BTAL 50/50": (254_199.59, 354.94),
    "TQQQ 100%": (688_316.64, 10.12),
    "TQQQ/BTAL SMA gate": (244_503.56, 277.56),
    "SPY benchmark": (167_218.26, 4.71),
}


def test_default_bundle_reproduces_the_net_cost_golden_numbers() -> None:
    bundle = matched_window_bundle(
        cost_bps={"TQQQ": 1.5, "BTAL": 6, "QQQ": 1, "SPY": 0.7, "*": 6},
        cash_yield=0.03,
    )
    results = run_bundle(bundle, NET_DIR)

    assert [r.label for r in results] == list(COST_GOLDEN_NET)
    for result in results:
        final, fees = COST_GOLDEN_NET[result.label]
        assert result.stats["final_value"] == pytest.approx(final, abs=0.005)
        assert result.stats["total_fees"] == pytest.approx(fees, abs=0.005)


# --- N8 — sweep provenance: with three dataset conventions sharing identical -
# date ranges, the artefacts must name the dataset directory themselves
# (NET_TR_SPEC §6).


def test_sweep_artefacts_record_the_data_directory(tmp_path, monkeypatch):
    spec_path = tmp_path / "grid.json"
    spec_path.write_text(json.dumps(T6_SPEC))
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["sweep.py", str(spec_path), "--data", str(GOLDEN_DIR), "--out", str(out)],
    )

    sweep_main()

    runs = pl.read_csv(out / "runs.csv")
    assert runs["data_dir"].to_list() == [str(GOLDEN_DIR)] * runs.height
    summary = json.loads((out / "summary.json").read_text())
    assert summary["data"]["dir"] == str(GOLDEN_DIR)
    md = (out / "summary.md").read_text()
    assert f"- Data dir: {GOLDEN_DIR}" in md


# --- N6 — generator guards, on synthetic pairs -------------------------------
#
# The reader whitelists time,close, so the fixtures write minimal two-column
# files. Pairs are built from a ratio path R and a flat price of 100: a step
# ln(R_t/R_{t-1}) above JUMP_MIN is a distribution jump, inside
# (FLAT_MAX, JUMP_MIN) the asserted-empty dead zone, below -TAU an error.


def write_pair(root: Path, ratios: list[float], prices: list[float] | None = None,
               symbol: str = "SYN", price_times: list[str] | None = None) -> Path:
    prices = prices or [100.0] * len(ratios)
    times = [
        (dt.date(2024, 1, 1) + dt.timedelta(days=i)).isoformat()
        for i in range(len(ratios))
    ]
    (root / "price").mkdir(parents=True, exist_ok=True)

    def csv(times_, closes):
        return "time,close\n" + "\n".join(
            f"{t},{c!r}" for t, c in zip(times_, closes)
        ) + "\n"

    adjusted = [r * p for r, p in zip(ratios, prices)]
    (root / f"{symbol}.csv").write_text(csv(times, adjusted))
    (root / "price" / f"{symbol}.csv").write_text(csv(price_times or times, prices))
    return root


JUMPY_RATIOS = [0.90, 0.90, 0.95, 0.95, 1.0]


def test_zero_withholding_reproduces_the_parent_exactly(tmp_path):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    net_main([str(src), "--withholding", "0", "--out", str(tmp_path / "net")])

    parent = pl.read_csv(src / "SYN.csv", schema_overrides={"close": pl.Float64})
    net = pl.read_csv(tmp_path / "net" / "SYN.csv", schema_overrides={"close": pl.Float64})
    assert net["close"].equals(parent["close"])
    assert net["time"].equals(parent["time"])


def test_dead_zone_step_is_a_hard_error(tmp_path):
    src = write_pair(tmp_path / "src", [0.95, 0.95 * math.exp(7e-6), 1.0])
    with pytest.raises(ValueError, match=r"SYN 2024-01-02: dead-zone step 6\.9"):
        net_main([str(src), "--out", str(tmp_path / "net")])
    assert not (tmp_path / "net").exists()


def test_negative_step_is_a_hard_error(tmp_path):
    src = write_pair(tmp_path / "src", [0.95, 0.95 * math.exp(-1e-5), 1.0])
    with pytest.raises(ValueError, match=r"SYN 2024-01-02: negative step -"):
        net_main([str(src), "--out", str(tmp_path / "net")])
    assert not (tmp_path / "net").exists()


def test_mismatched_time_columns_are_a_hard_error(tmp_path):
    shifted = ["2024-01-01", "2024-01-02", "2024-01-04"]
    src = write_pair(tmp_path / "src", [0.95, 0.95, 1.0], price_times=shifted)
    with pytest.raises(ValueError, match="SYN: adjusted and price time columns differ"):
        net_main([str(src), "--out", str(tmp_path / "net")])
    assert not (tmp_path / "net").exists()


@pytest.mark.parametrize("rate", ["1.0", "-0.1"])
def test_withholding_out_of_range_is_refused(tmp_path, rate):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    with pytest.raises(SystemExit):
        net_main([str(src), "--withholding", rate, "--out", str(tmp_path / "net")])
    assert not (tmp_path / "net").exists()


# --- CASH_SLEEVE_SPEC §10.5 — the per-symbol rate override -------------------
#
# One symbol may carry its own w when the flat convention demonstrably misprices
# it. The override must touch that symbol and nothing else, name itself in the
# snapshot, and refuse anything it cannot honour — a snapshot whose rate is not
# legible from its own README is worse than no snapshot.


def test_the_override_moves_only_the_symbol_it_names(tmp_path):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    write_pair(src, JUMPY_RATIOS, symbol="OTH")
    flat, over = tmp_path / "flat", tmp_path / "over"
    net_main([str(src), "--out", str(flat)])
    net_main([str(src), "--rate-override", "SYN=0", "--out", str(over)])

    assert filecmp.cmp(over / "OTH.csv", flat / "OTH.csv", shallow=False)
    assert not filecmp.cmp(over / "SYN.csv", flat / "SYN.csv", shallow=False)
    # w = 0 is the parent, bitwise (the k_net/k factor is exactly 1.0).
    assert filecmp.cmp(over / "SYN.csv", src / "SYN.csv", shallow=False)


def test_the_override_names_itself_in_the_snapshot(tmp_path):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    net_main([str(src), "--rate-override", "SYN=0"])

    readme = (tmp_path / "src-net15-syn0" / "README.md").read_text()
    assert "# Net total-return snapshot — src-net15-syn0" in readme
    assert "Per-symbol rate override (CASH_SLEEVE_SPEC §10.5): SYN at w = 0." in readme
    # y gross == y net is the override doing its job; the magnitude is the
    # fixture's five-day span annualised, not a claim about anything.
    assert "| SYN | 2 | 962.07%/yr | 962.07%/yr | w = 0 |" in readme


@pytest.mark.parametrize(
    "override", ["ABSENT=0", "SYN=1.0", "SYN=-0.1", "SYN", "=0", "SYN=x"]
)
def test_an_override_that_cannot_be_honoured_is_refused(tmp_path, override):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    out = tmp_path / "net"
    with pytest.raises((SystemExit, ValueError)):
        net_main([str(src), "--rate-override", override, "--out", str(out)])
    assert not out.exists()


def test_the_committed_bil0_root_differs_from_the_flat_root_in_bil_alone():
    bil0 = GOLDEN_DIR / "2026-08-24-net15-bil0"
    flat = GOLDEN_DIR / "2026-08-24-net15"
    gross = GOLDEN_DIR / "2026-08-24"
    moved = [p.name for p in sorted(bil0.glob("*.csv"))
             if not filecmp.cmp(p, flat / p.name, shallow=False)]
    assert moved == ["BIL.csv"]
    assert sorted(p.name for p in bil0.glob("*.csv")) == \
        sorted(p.name for p in flat.glob("*.csv"))
    # At w = 0 BIL's net series is its gross series to the last bit.
    columns = dict(columns=["time", "close"], schema_overrides={"close": pl.Float64})
    assert pl.read_csv(bil0 / "BIL.csv", **columns)["close"].equals(
        pl.read_csv(gross / "BIL.csv", **columns)["close"]
    )


# --- REGIME_SPEC R9 — the index-file pass-through and the ETF byte pins ------

# SHA-256 of the six net ETF files, measured at 184f02b: the pass-through
# change may not move a byte of them.
ETF_SHA256 = {
    "BTAL.csv": "93d1752638d2f8de4349a953bfbecc2a275758a681427f597d9c13d574669fbf",
    "DBMF.csv": "7af62a046680a9b7072f1d0848ab92010afa4d4e51f2be93949eca4360bd775c",
    "KMLM.csv": "c63907b899fc3e7ead79a10e030c3e3d229d8f475bc9b49d1f5d74eece80c0c8",
    "QQQ.csv": "c9afaffa020c6ea195d2ebdeec4c2b339555c4871f75dc6e2e114668bb8236af",
    "SPY.csv": "c885eedcbcdc3529a14de5e04684af9acb6ca798e58c56881a33f85bdfec4357",
    "TQQQ.csv": "398911f0c9148318d71902cd467aa3a406c30c1be48ea022f39d9a3ededdf47f",
}


def test_net_etf_files_are_byte_identical_to_the_pre_regime_baseline():
    for name, expected in ETF_SHA256.items():
        assert hashlib.sha256((NET_DIR / name).read_bytes()).hexdigest() == expected, name


def test_index_files_pass_through_byte_identical():
    for symbol in ("VIX", "VIX3M"):
        assert filecmp.cmp(NET_DIR / f"{symbol}.csv", TR_DIR / f"{symbol}.csv", shallow=False)
        assert not (NET_DIR / "price" / f"{symbol}.csv").exists()
    readme = (NET_DIR / "README.md").read_text()
    assert "| VIX | index | — | — |" in readme
    assert "| VIX3M | index | — | — |" in readme


def test_synthetic_unpaired_symbol_is_copied_and_listed_as_index(tmp_path):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    (src / "IDX.csv").write_text("time,close\n2024-01-01,20.0\n2024-01-02,21.5\n")

    net_main([str(src), "--out", str(tmp_path / "net")])

    assert filecmp.cmp(src / "IDX.csv", tmp_path / "net" / "IDX.csv", shallow=False)
    assert not (tmp_path / "net" / "price" / "IDX.csv").exists()
    readme = (tmp_path / "net" / "README.md").read_text()
    assert "| IDX | index | — | — |" in readme
    assert "| SYN | 2 |" in readme  # the paired symbol still nets normally


def test_existing_out_dir_refused_without_force(tmp_path):
    src = write_pair(tmp_path / "src", JUMPY_RATIOS)
    out = tmp_path / "net"
    out.mkdir()
    sentinel = out / "sentinel.txt"
    sentinel.write_text("untouched")

    with pytest.raises(SystemExit):
        net_main([str(src), "--out", str(out)])
    assert sorted(out.iterdir()) == [sentinel]
    assert sentinel.read_text() == "untouched"

    net_main([str(src), "--out", str(out), "--force"])
    assert (out / "SYN.csv").exists()
    assert (out / "price" / "SYN.csv").exists()
    assert (out / "README.md").exists()
