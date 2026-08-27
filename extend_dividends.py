"""Merge the pre-Polygon distribution records into `dividends/<SYM>.parquet`.

`fetch_dividends.py` can only reach as far back as the provider does — for QQQ
that is 2011-03-18, which misses the trust's first eight years. The CSVs under
`dividends/pre_polygon/` carry the earlier record (see that directory's README
for provenance); this merges each into its parquet, tagging every row with the
`source` it came from so a refetch can be told from a transcription.

Idempotent: rows already present at an ex-date are kept and the CSV's row is
skipped, so re-running after a fetch adds nothing twice.

Run: uv run extend_dividends.py [--dry-run]
"""

import argparse
from pathlib import Path

import polars as pl

OUT_DIR = Path("dividends")
EXTRA_DIR = OUT_DIR / "pre_polygon"


def merge(parquet: Path, extra: Path) -> tuple[pl.DataFrame, int]:
    """The parquet's rows plus the CSV's, deduplicated on ex-date, ascending."""
    existing = pl.read_parquet(parquet)
    if "source" not in existing.columns:
        existing = existing.with_columns(pl.lit("polygon").alias("source"))
    added = pl.read_csv(extra).filter(
        ~pl.col("ex_dividend_date").is_in(existing["ex_dividend_date"].implode())
    )
    if added.is_empty():
        return existing.sort("ex_dividend_date"), 0
    merged = pl.concat([existing, added], how="diagonal_relaxed")
    return merged.sort("ex_dividend_date"), len(added)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="report the merge, write nothing"
    )
    args = parser.parse_args(argv)

    for extra in sorted(EXTRA_DIR.glob("*.csv")):
        parquet = OUT_DIR / f"{extra.stem}.parquet"
        if not parquet.exists():
            raise ValueError(f"{parquet} is missing; run fetch_dividends.py first")
        merged, added = merge(parquet, extra)
        print(
            f"{extra.stem}: +{added} rows -> {len(merged)} total,"
            f" earliest ex-date {merged['ex_dividend_date'].min()}"
        )
        if not args.dry_run:
            merged.write_parquet(parquet)
            print(f"     Saved to {parquet}")


if __name__ == "__main__":
    main()
