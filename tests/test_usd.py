"""EU_SUBSTITUTE_SPEC §8 T2 — `make_usd.py`, the `-usd` root generator.

A converted close is close x FX x scale on every bar, with the FX rate carried
from the latest bar on or before the symbol's date; everything unmapped is
byte-copied; two runs are byte-identical; a missing FX series or a bad map is
loud and leaves no partial dataset.
"""

import filecmp
import json
from pathlib import Path

import polars as pl
import pytest

from make_usd import fx_on, load_map
from make_usd import main as usd_main

GOLDEN_DIR = Path(__file__).parent / "data"
NET = GOLDEN_DIR / "2026-09-02-net15"
USD = GOLDEN_DIR / "2026-09-02-net15-usd"
MAP = Path(__file__).parents[1] / "data" / "fx_lines.json"

SYN = [("2024-01-01", 100.0), ("2024-01-02", 101.0), ("2024-01-03", 102.0),
       ("2024-01-04", 103.0), ("2024-01-05", 104.0)]
OTH = [("2024-01-01", 50.0), ("2024-01-02", 51.0), ("2024-01-03", 52.0)]
IDX = [("2024-01-01", 1.0), ("2024-01-02", 1.5)]
# TradingView labels an FX bar by its 17:00 New York open, so the bar that
# closes on date D is labelled D - 1: SYN's 01-01 takes the 12-31 bar. The
# 01-03 label is missing (an FX holiday), so 01-04 carries the 01-02 bar and
# is the one stale row; 01-06 is a label SYN never reaches.
FX = [("2023-12-31", 1.10), ("2024-01-01", 1.11), ("2024-01-02", 1.12),
      ("2024-01-04", 1.14), ("2024-01-05", 1.15), ("2024-01-06", 1.16)]
RATES = [1.10, 1.11, 1.12, 1.12, 1.14]
SCALE = 0.01


def write_series(root: Path, symbol: str, rows, sub: str | None = None) -> None:
    """A file in the TradingView six-column export layout."""
    folder = root / sub if sub else root
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["time,open,high,low,close,Volume"]
    lines += [f"{t},{c},{c},{c},{c},0.0" for t, c in rows]
    (folder / f"{symbol}.csv").write_text("\n".join(lines) + "\n")


def write_map(path: Path, entries: dict) -> Path:
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
    write_series(root, "FX", FX)
    write_map(tmp_path / "map.json", {"SYN": {"fx": "FX", "scale": SCALE}})
    return root


def run(src: Path, out: Path, map_path: Path | None = None, *extra: str) -> None:
    usd_main([str(src), "--map", str(map_path or src.parent / "map.json"),
              "--out", str(out), *extra])


def test_converted_close_is_close_times_fx_times_scale_on_every_bar(src, tmp_path):
    out = tmp_path / "usd"
    run(src, out)
    got = pl.read_csv(out / "SYN.csv")
    assert got.columns == ["time", "close"]
    assert got["time"].to_list() == [t for t, _ in SYN]
    # Same expression, same order, so the equality is exact.
    assert got["close"].to_list() == [c * r * SCALE for (_, c), r in zip(SYN, RATES)]


def test_unmapped_files_are_byte_copied_and_the_converted_twin_is_dropped(src, tmp_path):
    out = tmp_path / "usd"
    run(src, out)
    for rel in ["OTH.csv", "price/OTH.csv", "IDX.csv", "FX.csv"]:
        assert filecmp.cmp(out / rel, src / rel, shallow=False), rel
    assert not (out / "price" / "SYN.csv").exists()
    assert sorted(p.name for p in out.iterdir()) == [
        "FX.csv", "IDX.csv", "OTH.csv", "README.md", "SYN.csv", "price"
    ]


def test_two_runs_are_byte_identical(src, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    run(src, a)
    run(src, b)
    files = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    assert files == sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    for rel in files:
        assert filecmp.cmp(a / rel, b / rel, shallow=False), rel


def test_readme_names_the_parent_and_the_conversion(src, tmp_path):
    out = tmp_path / "usd"
    run(src, out)
    readme = (out / "README.md").read_text()
    assert readme.startswith("# USD-converted snapshot — src-usd\n")
    assert "| SYN | FX | 0.01 | 5 | 1 | 1.1 | 1.14 |" in readme


def test_fx_is_the_latest_bar_labelled_strictly_before_each_date():
    rate, stale = fx_on("SYN", [t for t, _ in FX], [v for _, v in FX], [t for t, _ in SYN])
    assert rate == RATES
    assert stale == 1


def test_a_same_date_fx_bar_is_never_used():
    # The bar labelled D closes on D + 1 — a day of look-ahead.
    rate, _ = fx_on("SYN", ["2024-01-01", "2024-01-02"], [1.0, 2.0], ["2024-01-02"])
    assert rate == [1.0]


def test_a_bar_with_no_earlier_fx_bar_is_loud(src, tmp_path):
    write_series(src, "FX", FX[1:])  # first FX label 2024-01-01, SYN starts 2024-01-01
    with pytest.raises(ValueError, match="SYN 2024-01-01"):
        run(src, tmp_path / "usd")
    assert not (tmp_path / "usd").exists()


def test_an_unsorted_fx_series_is_loud():
    with pytest.raises(ValueError, match="not strictly ascending"):
        fx_on("SYN", ["2024-01-02", "2024-01-01"], [1.0, 1.0], ["2024-01-02"])


def test_a_missing_fx_series_is_loud_and_leaves_no_partial_output(src, tmp_path):
    write_map(tmp_path / "map.json", {"SYN": {"fx": "NOPE", "scale": 1}})
    with pytest.raises(ValueError, match="FX series NOPE"):
        run(src, tmp_path / "usd")
    assert not (tmp_path / "usd").exists()


@pytest.mark.parametrize("entries", [
    {"ABSENT": {"fx": "FX", "scale": 1}},
    {"SYN": "FX"},
    {"SYN": {"fx": "FX"}},
    {"SYN": {"fx": "FX", "scale": 0}},
    {"SYN": {"fx": "FX", "scale": True}},
    {"SYN": {"fx": "", "scale": 1}},
])
def test_a_bad_map_is_refused_with_no_partial_output(src, tmp_path, entries):
    write_map(tmp_path / "map.json", entries)
    with pytest.raises(ValueError):
        run(src, tmp_path / "usd")
    assert not (tmp_path / "usd").exists()


def test_load_map_returns_fx_and_scale(tmp_path):
    path = write_map(tmp_path / "m.json", {"A": {"fx": "EURUSD", "scale": 1},
                                           "B": {"fx": "GBPUSD", "scale": 0.01}})
    assert load_map(path) == {"A": ("EURUSD", 1.0), "B": ("GBPUSD", 0.01)}


def test_existing_out_dir_refused_without_force(src, tmp_path):
    out = tmp_path / "usd"
    out.mkdir()
    (out / "sentinel").write_text("keep")
    with pytest.raises(SystemExit):
        run(src, out)
    assert (out / "sentinel").read_text() == "keep"
    assert not (out / "SYN.csv").exists()
    run(src, out, None, "--force")
    assert (out / "SYN.csv").exists()


# The committed decision root (EU_SUBSTITUTE_SPEC §3.6).


def test_generator_reproduces_the_committed_usd_root_byte_for_byte(tmp_path):
    out = tmp_path / "usd"
    usd_main([str(NET), "--map", str(MAP), "--out", str(out)])
    produced = sorted(p.relative_to(out) for p in out.rglob("*") if p.is_file())
    committed = sorted(p.relative_to(USD) for p in USD.rglob("*") if p.is_file())
    assert produced == committed
    assert len(produced) == 64 + 53 + 1  # four converted symbols carry no twin
    for rel in committed:
        assert filecmp.cmp(out / rel, USD / rel, shallow=False), rel


def test_the_usd_root_differs_from_its_parent_in_the_mapped_symbols_alone():
    moved = [p.name for p in sorted(USD.glob("*.csv"))
             if not filecmp.cmp(p, NET / p.name, shallow=False)]
    assert moved == ["DBMF_EU.csv", "LQQ.csv", "MVEA.csv", "XSPS.csv"]
    assert sorted(json.loads(MAP.read_text())) == [p.removesuffix(".csv") for p in moved]
    for name in moved:
        assert not (USD / "price" / name).exists()
    assert filecmp.cmp(USD / "price" / "TQQQ.csv", NET / "price" / "TQQQ.csv", shallow=False)


def test_a_converted_row_is_the_parent_close_times_the_previous_labels_fx():
    # XSPS 2026-09-02 (GBX): 411.6 pence x GBPUSD of the bar labelled 2026-09-01.
    xsps = pl.read_csv(USD / "XSPS.csv", try_parse_dates=True).tail(1)
    fx = pl.read_csv(NET / "GBPUSD.csv", columns=["time", "close"], try_parse_dates=True).tail(1)
    assert str(xsps["time"][0]) == "2026-09-02" and str(fx["time"][0]) == "2026-09-01"
    assert xsps["close"][0] == 411.6 * fx["close"][0] * 0.01
    readme = (USD / "README.md").read_text()
    assert readme.startswith("# USD-converted snapshot — 2026-09-02-net15-usd\n")
    assert "| XSPS | GBPUSD | 0.01 | 4623 | 0 | 1.946 | 1.3481 |" in readme
