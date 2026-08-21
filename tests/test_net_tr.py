"""NET_TR_SPEC §8 — the net-of-withholding total-return dataset.

N1 layout/self-containment, N2 scaled ratio invariants, N3 per-jump
exactness, N4 yield contraction, N5 byte-reproducibility, N6 generator
guards, N7 net goldens, N8 sweep provenance. Constants come from
make_net_tr; tests/test_total_return.py keeps its own local TAU untouched.
"""

import datetime as dt
import filecmp
import math
from pathlib import Path

import polars as pl
import pytest

from make_net_tr import FLAT_MAX, JUMP_MIN, TAU, main as net_main

GOLDEN_DIR = Path(__file__).parent / "data"
TR_DIR = GOLDEN_DIR / "2026-08-20"
NET_DIR = GOLDEN_DIR / "2026-08-20-net15"
SYMBOLS = ["TQQQ", "BTAL", "QQQ", "SPY", "DBMF", "KMLM"]
W = 0.15


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
    assert len(produced) == 13
    for rel in committed:
        assert filecmp.cmp(out / rel, NET_DIR / rel, shallow=False), rel


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
    src = write_pair(tmp_path / "src", [0.95, 0.95 * math.exp(1e-5), 1.0])
    with pytest.raises(ValueError, match=r"SYN 2024-01-02: dead-zone step 9\.9"):
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
