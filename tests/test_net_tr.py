"""NET_TR_SPEC §8 — the net-of-withholding total-return dataset.

N1 layout/self-containment, N2 scaled ratio invariants, N3 per-jump
exactness, N4 yield contraction, N5 byte-reproducibility, N6 generator
guards, N7 net goldens, N8 sweep provenance. Constants come from
make_net_tr; tests/test_total_return.py keeps its own local TAU untouched.
"""

import datetime as dt
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
