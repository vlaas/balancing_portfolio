"""Fetch dividend records for the six universe symbols from Polygon.io.

Local copy of bt_dataset/fetch_dividends.py with this repo's symbol list.
The records are the source for the T3 implied-distribution spot checks in
tests/test_total_return.py (TOTAL_RETURN_SPEC §7); they are reference data,
never loader input.

Run: POLYGON_API_KEY=... uv run --with requests fetch_dividends.py
"""

import os
from pathlib import Path

import polars as pl
import requests

BASE_URL = "https://api.polygon.io/v3/reference/dividends"
SYMBOLS = ["TQQQ", "BTAL", "QQQ", "SPY", "DBMF", "KMLM"]
OUT_DIR = Path("dividends")


def fetch_ticker_dividends(ticker: str, api_key: str) -> list[dict]:
    """Fetch all dividend records for a ticker, handling pagination."""
    params = {"ticker": ticker, "limit": 1000, "apiKey": api_key}
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


def main():
    api_key = os.environ["POLYGON_API_KEY"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in SYMBOLS:
        print(f"Fetching dividends for {ticker}...")
        records = fetch_ticker_dividends(ticker, api_key)
        print(f"  -> {len(records)} records")
        df = pl.DataFrame(records, infer_schema_length=len(records) or 1)
        out_path = OUT_DIR / f"{ticker}.parquet"
        df.write_parquet(out_path)
        print(f"     Saved to {out_path}")


if __name__ == "__main__":
    main()
