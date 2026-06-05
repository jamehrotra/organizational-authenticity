"""
Part 2, Stage 2: Extract clean text from SEC DEF 14A filings.

DEF 14A filings from EDGAR are plain text (SGML/HTML). This module strips
SGML markup, HTML tags, and EDGAR boilerplate to yield readable prose text.

Output: data/interim/part2/<ticker>_<year>_proxy_clean.txt

Usage:
    python -m src.part2_disclosures.extract_disclosure_text [--force]
"""

import argparse
import re
from pathlib import Path

from tqdm import tqdm

from src.common.io import DATA_RAW, interim_path, is_cached, save_text
from src.common.text_cleaning import _normalize
from src.common.utils import setup_logging, load_companies, years_range, slug

log = setup_logging("extract_disclosure_text")

SEC_DIR = DATA_RAW / "sec_filings"


def find_filing_file(ticker: str, year: int) -> Path | None:
    """Find the main .txt filing file for a ticker-year."""
    base = SEC_DIR / ticker / str(year)
    if not base.exists():
        return None
    # sec-edgar-downloader nests files; look for the main document
    candidates = sorted(base.rglob("*.txt"), key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0] if candidates else None


def clean_edgar_text(raw: str) -> str:
    """Strip SGML/HTML markup and EDGAR boilerplate from a DEF 14A filing."""
    # Remove SGML document headers
    raw = re.sub(r"<SEC-DOCUMENT>.*?<TEXT>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"</TEXT>.*", "", raw, flags=re.DOTALL | re.IGNORECASE)

    # Strip HTML tags
    raw = re.sub(r"<[^>]+>", " ", raw)

    # Remove EDGAR-specific markers
    raw = re.sub(r"&[A-Za-z]+;", " ", raw)
    raw = re.sub(r"&#\d+;", " ", raw)

    # Remove sequences of dashes/underscores used as decorators
    raw = re.sub(r"[-_=]{4,}", " ", raw)

    # Remove page numbers and typical header/footer patterns
    raw = re.sub(r"\bPage\s+\d+\b", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bTable of Contents\b", "", raw, flags=re.IGNORECASE)

    return _normalize(raw)


def extract_one(ticker: str, year: int, force: bool = False) -> dict:
    out_path = interim_path("part2", f"{slug(ticker, year)}_proxy_clean.txt")

    if not force and is_cached(out_path):
        return {"ticker": ticker, "year": year, "status": "cached"}

    filing = find_filing_file(ticker, year)
    if not filing:
        return {"ticker": ticker, "year": year, "status": "no_filing"}

    try:
        raw = filing.read_text(encoding="utf-8", errors="replace")
        text = clean_edgar_text(raw)
        wc = len(text.split())
        if wc < 100:
            log.warning(f"{ticker} {year}: only {wc} words after cleaning")
        save_text(text, out_path)
        return {"ticker": ticker, "year": year, "status": "ok", "word_count": wc}
    except Exception as e:
        log.warning(f"{ticker} {year}: extraction error — {e}")
        return {"ticker": ticker, "year": year, "status": f"error: {e}"}


def run_all(force: bool = False):
    companies = load_companies()
    years = years_range()
    tasks = [(row["ticker"], year) for _, row in companies.iterrows() for year in years]

    log.info(f"Extracting proxy text for {len(tasks)} company-year pairs")
    results = []

    for ticker, year in tqdm(tasks, desc="Extracting proxy text"):
        r = extract_one(ticker, year, force=force)
        results.append(r)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    missing = [r for r in results if r["status"] == "no_filing"]
    log.info(f"Done. Extracted: {ok}, No filing: {len(missing)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Extract clean text from SEC proxy statements")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    run_all(force=args.force)


if __name__ == "__main__":
    main()
