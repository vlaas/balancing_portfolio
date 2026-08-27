"""Fetch dividend records for the six universe symbols from Polygon.io.

Local copy of bt_dataset/fetch_dividends.py with this repo's symbol list.
The records are the source for the T3 implied-distribution spot checks in
tests/test_total_return.py (TOTAL_RETURN_SPEC §7); they are reference data,
never loader input.

The request asks explicitly for history from SINCE (1999, before every symbol
here existed) and prints each ticker's earliest record, so the provider's
coverage boundary is a measured fact rather than an assumption. Polygon's
dividend reference data begins 2011-03-18 for QQQ, which is after QQQ's first
distribution (2003-12-24) — `extend_dividends.py` carries the earlier record.

Existing per-ticker parquets are left alone; pass --overwrite to refetch them.

Run: POLYGON_API_KEY=... uv run --with requests fetch_dividends.py
"""

import argparse
import os
from pathlib import Path

import polars as pl
import requests
from bt_secrets import api_key

BASE_URL = "https://api.polygon.io/v3/reference/dividends"
SYMBOLS = ["TQQQ", "BTAL", "QQQ", "SPY", "DBMF", "KMLM", 'BIL']
OUT_DIR = Path("dividends")
SINCE = "1999-01-01"


def fetch_ticker_dividends(ticker: str, api_key: str) -> list[dict]:
    """Fetch all dividend records for a ticker, handling pagination."""
    params = {
        "ticker": ticker, "ex_dividend_date.gte": SINCE,
        "limit": 1000, "apiKey": api_key,
    }
    records = []
    url = BASE_URL
    while url:
        resp = requests.get(url, params=params if url == BASE_URL else None)
        resp.raise_for_status()
        data = resp.json()
        records.extend(data.get("results", []))
        url = data.get("next_url")
        if url:
            url = f"{url}&apiKey={api_key}"
    return records


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite", action="store_true", help="refetch tickers already saved"
    )
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in SYMBOLS:
        out_path = OUT_DIR / f"{ticker}.parquet"
        if out_path.exists() and not args.overwrite:
            print(f"{out_path} exists; skipping (--overwrite to refetch)")
            continue
        print(f"Fetching dividends for {ticker} since {SINCE}...")
        records = fetch_ticker_dividends(ticker, api_key)
        earliest = min((r["ex_dividend_date"] for r in records), default="none")
        print(f"  -> {len(records)} records, earliest ex-date {earliest}")
        df = pl.DataFrame(records, infer_schema_length=len(records) or 1)
        # Column order follows whichever record first carried each key, so it
        # would move with the response order; sort it for a stable schema.
        df = df.select(sorted(df.columns))
        df.write_parquet(out_path)
        print(f"     Saved to {out_path}")


if __name__ == "__main__":
    main()
