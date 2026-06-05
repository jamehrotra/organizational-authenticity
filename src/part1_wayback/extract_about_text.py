"""
Stage 3: Extract clean body text from archived HTML snapshots.

Reads raw HTML from data/raw/wayback_html/ and writes clean text to
data/interim/part1/<ticker>_<year>_clean.txt.

Usage:
    python -m src.part1_wayback.extract_about_text [--force]
"""

import argparse
from pathlib import Path

from tqdm import tqdm

from src.common.io import cache_path, interim_path, is_cached, load_text, save_text
from src.common.text_cleaning import clean_html, word_count
from src.common.utils import setup_logging, load_about_candidates, years_range, slug

log = setup_logging("extract_about_text")


def extract_one(ticker: str, year: int, force: bool = False) -> dict:
    html_path = cache_path("wayback_html", f"{slug(ticker, year)}.html")
    out_path = interim_path("part1", f"{slug(ticker, year)}_clean.txt")

    if not force and is_cached(out_path):
        return {"ticker": ticker, "year": year, "status": "cached", "word_count": None}

    html = load_text(html_path)
    if not html:
        return {"ticker": ticker, "year": year, "status": "no_html", "word_count": 0}

    text = clean_html(html)
    wc = word_count(text)

    if wc < 30:
        log.warning(f"{ticker} {year}: only {wc} words after cleaning — may be empty page")

    save_text(text, out_path)
    return {"ticker": ticker, "year": year, "status": "ok", "word_count": wc}


def run_all(force: bool = False):
    df = load_about_candidates()
    years = years_range()
    tasks = [(row["ticker"], year) for _, row in df.iterrows() for year in years]

    log.info(f"Extracting text from {len(tasks)} company-year snapshots")
    results = []

    for ticker, year in tqdm(tasks, desc="Extracting text"):
        r = extract_one(ticker, year, force=force)
        results.append(r)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    empty = [r for r in results if r["status"] == "no_html"]
    short = [r for r in results if r.get("word_count") is not None and r["word_count"] < 30]

    log.info(f"Done. Extracted: {ok}, No HTML: {len(empty)}, Short (<30 words): {len(short)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 3: Extract clean text from HTML")
    parser.add_argument("--force", action="store_true", help="Re-extract even if cached")
    args = parser.parse_args()
    run_all(force=args.force)


if __name__ == "__main__":
    main()
