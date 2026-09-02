"""EU_SUBSTITUTE_SPEC §8 T4 — `make_haircut.py`, the `-hc` root generator.

A haircut close is close x (1 - h/100/252)^k with k bars since the symbol's
first bar; h = 0 reproduces the parent bit-for-bit (no-contamination);
everything unmapped is byte-copied; two runs are byte-identical; a bad map or
an absent symbol is loud and leaves no partial dataset.
"""

import filecmp
import json
import math
from pathlib import Path

import polars as pl
import pytest

from make_haircut import haircut, load_haircuts
from make_haircut import main as haircut_main

SYN = [(f"2024-01-0{i}", 100.0) for i in range(1, 7)]
OTH = [("2024-01-01", 50.0), ("2024-01-02", 51.0), ("2024-01-03", 52.0)]
IDX = [("2024-01-01", 1.0), ("2024-01-02", 1.5)]


def write_series(root: Path, symbol: str, rows, sub: str | None = None) -> None:
    """A file in the TradingView six-column export layout."""
    folder = root / sub if sub else root
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["time,open,high,low,close,Volume"]
    lines += [f"{t},{c},{c},{c},{c},0.0" for t, c in rows]
    (folder / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def write_haircuts(path: Path, entries) -> Path:
    path.write_text(json.dumps(entries))
    return path


@pytest.fixture
def src(tmp_path: Path) -> Path:
    root = tmp_path / "src"
    write_series(root, "SYN", SYN)
    write_series(root, "SYN", SYN, "price")
    write_series(root, "OTH", OTH)
    write_series(root, "OTH", OTH, "price")
    write_series(root, "IDX", IDX)
    write_haircuts(tmp_path / "haircuts.json", {"SYN": 1.0})
    return root


def run(src: Path, out: Path, haircuts: Path | None = None, *extra: str) -> None:
    haircut_main([str(src), "--haircuts", str(haircuts or src.parent / "haircuts.json"),
                  "--out", str(out), *extra])


def csv_files(root: Path) -> list[Path]:
    return sorted(p.relative_to(root) for p in root.rglob("*.csv"))


def test_h_zero_reproduces_the_parent_bit_for_bit(src, tmp_path):
    write_haircuts(tmp_path / "haircuts.json", {"SYN": 0, "OTH": 0})
    out = tmp_path / "hc"
    run(src, out)
    assert csv_files(out) == csv_files(src)
    for rel in csv_files(src):
        assert filecmp.cmp(out / rel, src / rel, shallow=False), rel
    assert (out / "README.md").exists()
    files = sorted(p.relative_to(out) for p in out.rglob("*") if p.is_file())
    assert files == sorted(csv_files(src) + [Path("README.md")])


def test_a_pinned_h_1_row(src, tmp_path):
    out = tmp_path / "hc"
    run(src, out)
    got = pl.read_csv(out / "SYN.csv")
    assert got.columns == ["time", "close"]
    assert got["time"].to_list() == [t for t, _ in SYN]
    close = got["close"].to_list()
    assert close[0] == 100.0
    # Same expression, same order, so the equality is exact.
    assert close[5] == 100.0 * (1 - 1 / 25200) ** 5
    for a, b in zip(close, close[1:]):
        assert math.log(b / a) == pytest.approx(math.log(1 - 1 / 25200))
    assert not (out / "price" / "SYN.csv").exists()


def test_unmapped_symbols_are_byte_copied(src, tmp_path):
    out = tmp_path / "hc"
    run(src, out)
    for rel in ["OTH.csv", "price/OTH.csv", "IDX.csv"]:
        assert filecmp.cmp(out / rel, src / rel, shallow=False), rel
    assert sorted(p.name for p in out.iterdir()) == [
        "IDX.csv", "OTH.csv", "README.md", "SYN.csv", "price"
    ]
    assert sorted(p.name for p in (out / "price").iterdir()) == ["OTH.csv"]


@pytest.mark.parametrize("entries", [
    {"ABSENT": 1},
    {"SYN": -1},
    {"SYN": True},
    {"SYN": "1"},
    [1],
])
def test_bad_haircuts_are_refused_with_no_partial_output(src, tmp_path, entries):
    write_haircuts(tmp_path / "haircuts.json", entries)
    with pytest.raises(ValueError):
        run(src, tmp_path / "hc")
    assert not (tmp_path / "hc").exists()


def test_existing_out_dir_refused_without_force(src, tmp_path):
    out = tmp_path / "hc"
    out.mkdir()
    (out / "sentinel").write_text("keep")
    with pytest.raises(SystemExit):
        run(src, out)
    assert (out / "sentinel").read_text() == "keep"
    assert not (out / "SYN.csv").exists()
    run(src, out, None, "--force")
    assert (out / "SYN.csv").exists()


def test_two_runs_are_byte_identical(src, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    run(src, a)
    run(src, b)
    files = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    assert files == sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    for rel in files:
        assert filecmp.cmp(a / rel, b / rel, shallow=False), rel


def test_readme_names_parent_formula_and_rows(src, tmp_path):
    write_haircuts(tmp_path / "haircuts.json", {"SYN": 1.0, "OTH": 0})
    out = tmp_path / "hc"
    run(src, out)
    readme = (out / "README.md").read_text()
    assert readme.startswith("# Haircut snapshot — src-hc\n")
    assert "`close_t × (1 − h/100/252)^k`" in readme
    assert "| symbol | h %/yr | bars | final factor |" in readme
    assert "| OTH | 0 | — | byte-copied |" in readme
    assert "| SYN | 1 | 6 | 0.9998016030480019 |" in readme


def test_haircut_is_a_power_of_bars_since_the_first():
    closes = [100.0, 200.0, 50.0]
    d = 2.0 / 100 / 252
    assert haircut(closes, 2.0) == [100.0, 200.0 * (1 - d), 50.0 * (1 - d) ** 2]


def test_load_haircuts_returns_floats(tmp_path):
    path = write_haircuts(tmp_path / "h.json", {"TQQQ": 0.57, "BIL": 0, "DBMF": 0.12})
    assert load_haircuts(path) == {"TQQQ": 0.57, "BIL": 0.0, "DBMF": 0.12}


# The committed -hc root (EU_SUBSTITUTE_SPEC §6.3): built from the pinned
# haircuts.json on the decision root; TQQQ alone carries a haircut.

USD = Path(__file__).parent / "data" / "2026-09-02-net15-usd"
HC = Path(__file__).parent / "data" / "2026-09-02-net15-usd-hc"
HAIRCUTS = Path(__file__).parents[1] / "results" / "overlap_eu" / "haircuts.json"
ROOT = pytest.mark.skipif(not HC.exists(), reason="the -hc root is committed with the Phase-3 run")


@ROOT
def test_generator_reproduces_the_committed_hc_root_byte_for_byte(tmp_path):
    out = tmp_path / "hc"
    haircut_main([str(USD), "--haircuts", str(HAIRCUTS), "--out", str(out)])
    produced = sorted(p.relative_to(out) for p in out.rglob("*") if p.is_file())
    committed = sorted(p.relative_to(HC) for p in HC.rglob("*") if p.is_file())
    assert produced == committed
    assert len(produced) == 64 + 52 + 1  # TQQQ's twin dropped, README
    for rel in committed:
        assert filecmp.cmp(out / rel, HC / rel, shallow=False), rel


@ROOT
def test_the_hc_root_differs_from_its_parent_in_tqqq_alone():
    moved = [p.name for p in sorted(HC.glob("*.csv")) if not filecmp.cmp(p, USD / p.name, shallow=False)]
    assert moved == ["TQQQ.csv"]
    assert not (HC / "price" / "TQQQ.csv").exists()
    assert json.loads(HAIRCUTS.read_text()) == {"BIL": 0.0, "TQQQ": 0.14206396}
    assert filecmp.cmp(HC / "BIL.csv", USD / "BIL.csv", shallow=False)  # h = 0: byte-copied
    assert "| BIL | 0 | — | byte-copied |" in (HC / "README.md").read_text()
    parent = pl.read_csv(USD / "TQQQ.csv")["close"]
    cut = pl.read_csv(HC / "TQQQ.csv")["close"]
    assert cut[0] == parent[0]
    assert cut[-1] == pytest.approx(parent[-1] * (1 - 0.14206396 / 100 / 252) ** (len(parent) - 1))


@ROOT
def test_an_all_zero_map_reproduces_the_decision_root(tmp_path):
    out = tmp_path / "hc0"
    haircut_main([str(USD), "--haircuts", str(write_haircuts(tmp_path / "zero.json",
                 {"TQQQ": 0, "BIL": 0, "DBMF": 0})), "--out", str(out)])
    for rel in sorted(p.relative_to(USD) for p in USD.rglob("*.csv")):
        assert filecmp.cmp(out / rel, USD / rel, shallow=False), rel
