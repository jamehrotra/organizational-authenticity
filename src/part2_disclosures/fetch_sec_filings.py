"""
Part 2, Stage 1: Download DEF 14A (proxy statement) filings from SEC EDGAR.

Uses sec-edgar-downloader to fetch proxy statements for each company-year.
Filing text is saved to data/raw/sec_filings/<ticker>/<year>/.

Usage:
    python -m src.part2_disclosures.fetch_sec_filings [--force] [--tickers MSFT AAPL ...]
"""

import argparse
import os
import shutil
from pathlib import Path

from tqdm import tqdm

from src.common.io import DATA_RAW
from src.common.utils import setup_logging, load_companies, years_range

log = setup_logging("fetch_sec_filings")

SEC_DIR = DATA_RAW / "sec_filings"
FILING_TYPE = "DEF 14A"

# SEC EDGAR requires a user agent with contact info
USER_AGENT = "organizational-authenticity-research jmhrotra@sas.upenn.edu"


def fetch_ticker_year(ticker: str, year: int, force: bool = False) -> dict:
    """Download DEF 14A for a ticker filed in a given calendar year."""
    from sec_edgar_downloader import Downloader

    out_dir = SEC_DIR / ticker / str(year)

    if not force and out_dir.exists() and any(out_dir.rglob("*.txt")):
        return {"ticker": ticker, "year": year, "status": "cached"}

    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        dl = Downloader(
            company_name="organizational-authenticity",
            email_address="jmhrotra@sas.upenn.edu",
            save_path=str(out_dir),
        )
        # after_date / before_date narrows to filings submitted in that year
        dl.get(
            FILING_TYPE,
            ticker,
            after=f"{year}-01-01",
            before=f"{year}-12-31",
            limit=1,
        )
        files = list(out_dir.rglob("*.txt"))
        if files:
            return {"ticker": ticker, "year": year, "status": "ok", "files": [str(f) for f in files]}
        else:
            return {"ticker": ticker, "year": year, "status": "no_filing_found"}
    except Exception as e:
        log.warning(f"{ticker} {year}: {e}")
        return {"ticker": ticker, "year": year, "status": f"error: {e}"}


def run_all(force: bool = False, tickers: list[str] | None = None):
    companies = load_companies()
    if tickers:
        companies = companies[companies["ticker"].isin(tickers)]

    years = years_range()
    tasks = [(row["ticker"], year) for _, row in companies.iterrows() for year in years]

    log.info(f"Fetching DEF 14A filings for {len(tasks)} company-year pairs")
    results = []

    for ticker, year in tqdm(tasks, desc="Fetching SEC filings"):
        r = fetch_ticker_year(ticker, year, force=force)
        results.append(r)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    missing = [r for r in results if r["status"] == "no_filing_found"]
    errors = [r for r in results if r["status"].startswith("error")]

    log.info(f"Done. Found: {ok}, Not found: {len(missing)}, Errors: {len(errors)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch DEF 14A proxy statements from SEC EDGAR")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--tickers", nargs="*", help="Limit to specific tickers")
    args = parser.parse_args()
    run_all(force=args.force, tickers=args.tickers)


if __name__ == "__main__":
    main()
