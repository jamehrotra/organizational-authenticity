"""
Stage 2: Download raw archived HTML for each selected snapshot.

Reads CDX result files from data/raw/wayback_cdx/ and downloads HTML
to data/raw/wayback_html/<ticker>_<year>.html. Skips already-cached files.

Uses synchronous requests (not aiohttp) for reliability on Windows.

Usage:
    python -m src.part1_wayback.download_snapshots [--force]
"""

import argparse
import time

import requests
from tqdm import tqdm

from src.common.io import cache_path, is_cached, save_text, load_json
from src.common.utils import setup_logging, load_about_candidates, years_range, slug

log = setup_logging("download_snapshots")

TIMEOUT = 45
DOWNLOAD_DELAY = 1.5  # seconds between downloads

_session = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = "organizational-authenticity-research/1.0"
    return _session


def wayback_raw_url(timestamp: str, original_url: str) -> str:
    """Construct archive URL using id_ flag to get raw HTML without Wayback toolbar."""
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"


def download_one(
    ticker: str,
    year: int,
    archive_url: str,
    force: bool,
) -> dict:
    out_path = cache_path("wayback_html", f"{slug(ticker, year)}.html")

    if not force and is_cached(out_path):
        return {"ticker": ticker, "year": year, "status": "cached", "path": str(out_path)}

    phase = "html_download"
    try:
        resp = get_session().get(archive_url, timeout=TIMEOUT, allow_redirects=True)
        time.sleep(DOWNLOAD_DELAY)

        if resp.status_code != 200:
            log.warning(f"{ticker} {year}: HTTP {resp.status_code} | phase={phase} url={archive_url}")
            return {"ticker": ticker, "year": year, "status": f"http_{resp.status_code}", "path": None,
                    "phase": phase, "archive_url": archive_url, "http_status": resp.status_code}

        html = resp.text
        if len(html) < 500:
            log.warning(f"{ticker} {year}: suspiciously short HTML ({len(html)} chars) for {archive_url}")
            return {"ticker": ticker, "year": year, "status": "too_short", "path": None}

        save_text(html, out_path)
        return {"ticker": ticker, "year": year, "status": "ok", "path": str(out_path)}

    except requests.exceptions.Timeout:
        log.warning(f"{ticker} {year}: Timeout | phase={phase} url={archive_url}")
        return {"ticker": ticker, "year": year, "status": "timeout", "path": None,
                "phase": phase, "archive_url": archive_url, "exception_type": "Timeout"}

    except Exception as e:
        log.warning(f"{ticker} {year}: {type(e).__name__} | phase={phase} url={archive_url} — {e}")
        return {"ticker": ticker, "year": year, "status": f"error: {type(e).__name__}", "path": None,
                "phase": phase, "archive_url": archive_url, "exception_type": type(e).__name__}


def run_all(force: bool = False, concurrency: int = 1) -> list[dict]:
    df = load_about_candidates()
    years = years_range()

    to_download = []
    for _, row in df.iterrows():
        ticker = row["ticker"]
        for year in years:
            cdx_file = cache_path("wayback_cdx", f"{slug(ticker, year)}.json")
            cdx = load_json(cdx_file)
            if cdx and cdx.get("selection_status") not in ("missing", None):
                to_download.append((ticker, year, cdx["archive_url"]))

    log.info(f"Downloading {len(to_download)} HTML snapshots")

    results = []
    for ticker, year, archive_url in tqdm(to_download, desc="Downloading HTML"):
        r = download_one(ticker, year, archive_url, force)
        results.append(r)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    failed = [r for r in results if r["status"] not in ("ok", "cached")]
    log.info(f"Done. Successful: {ok}, Failed: {len(failed)}")
    if failed:
        log.info("Failed: " + ", ".join(f"{r['ticker']} {r['year']} ({r['status']})" for r in failed[:10]))

    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 2: Download archived HTML snapshots")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    run_all(force=args.force)


if __name__ == "__main__":
    main()
