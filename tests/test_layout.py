"""DATA_LAYOUT_V2_SPEC §2–§3 — every root keeps each series class in its own folder.

No CSV sits at a root's top level, `adjusted/` and `index/` never share a symbol,
and `index/` holds only the single series with no dividend toggle. The per-folder
counts are the §3 table; a root added under tests/data/ must be pinned here.
"""

from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"
LIVE = Path(__file__).parents[1] / "data"
INDEX = {"SPX", "XNDX", "VIX", "VIX3M", "NDX", "EURUSD", "GBPUSD"}

# (adjusted, index, unadjusted) per root name.
COUNTS = {
    "data": (57, 7, 57),
    "2026-08-14-unadjusted": (0, 0, 6),
    "2026-08-20": (6, 2, 6),
    "2026-08-20-net15": (6, 2, 6),
    "2026-08-24": (48, 4, 48),
    "2026-08-24-net15": (48, 4, 48),
    "2026-08-24-net15-bil0": (48, 4, 48),
    "2026-08-24-syn": (48, 4, 46),
    "2026-08-24-syn-net15": (48, 4, 46),
    "2026-09-02": (57, 7, 57),
    "2026-09-02-net15": (57, 7, 57),
    "2026-09-02-net15-usd": (57, 7, 53),
    "2026-09-02-net15-usd-hc": (57, 7, 52),
}
ROOTS = [LIVE] + sorted(p for p in DATA.iterdir() if p.is_dir())


def stems(root: Path, folder: str) -> set[str]:
    return {p.stem for p in (root / folder).glob("*.csv")}


def test_every_root_is_pinned() -> None:
    assert sorted(root.name for root in ROOTS) == sorted(COUNTS)


@pytest.mark.parametrize("root", ROOTS, ids=lambda root: root.name)
def test_each_series_class_has_its_own_folder(root: Path) -> None:
    assert not list(root.glob("*.csv"))
    adjusted, index, unadjusted = (stems(root, f) for f in ("adjusted", "index", "unadjusted"))
    assert (len(adjusted), len(index), len(unadjusted)) == COUNTS[root.name]
    assert not adjusted & index
    assert index <= INDEX
