"""
Stage 1: Query the Wayback Machine CDX API for each company-year-URL combination.

For each company, we try candidate URLs (from about_page_candidates.csv) first.
If none return results, we fall back to common path heuristics.
All CDX responses are cached under data/raw/wayback_cdx/.

Uses synchronous requests (not aiohttp) for reliability on Windows —
aiohttp triggers WinError 121 (semaphore timeout) on this machine.

Usage:
    python -m src.part1_wayback.query_cdx [--force]
"""

import argparse
import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from src.common.io import cache_path, is_cached, save_json, load_json
from src.common.utils import (
    setup_logging,
    load_about_candidates,
    years_range,
    candidate_urls,
    fallback_urls,
    slug,
)

log = setup_logging("query_cdx")

CDX_API = "https://web.archive.org/cdx/search/cdx"
TIMEOUT = 30
CDX_REQUEST_DELAY = 1.0  # seconds between requests to avoid 429s

_session = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = "organizational-authenticity-research/1.0"
    return _session


def query_cdx_for_url(
    url: str,
    year: int,
    match_type: str = "exact",
) -> tuple[list[dict], dict | None]:
    """
    Return (records, failure_info) for a URL in a given year.

    records is a list of CDX record dicts; empty on failure or no results.
    failure_info is None on success, or a dict with diagnostic fields on error.
    """
    params = {
        "url": url,
        "output": "json",
        "from": f"{year}0101",
        "to": f"{year}1231",
        "fl": "timestamp,original,mimetype,statuscode,digest,length",
        "filter": ["statuscode:200", "mimetype:text/html"],
        "collapse": "digest",
        "matchType": match_type,
    }
    phase = "cdx_lookup"
    session = get_session()

    for attempt in range(3):
        try:
            resp = session.get(CDX_API, params=params, timeout=TIMEOUT)
            time.sleep(CDX_REQUEST_DELAY)

            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                log.warning(f"CDX 429 (attempt {attempt+1}) for {url} {year} — retrying in {wait}s")
                time.sleep(wait)
                continue

            if resp.status_code != 200:
                failure = {
                    "phase": phase, "url": url, "year": year,
                    "params": {k: v for k, v in params.items() if k != "filter"},
                    "http_status": resp.status_code, "exception_type": None,
                }
                log.warning(f"CDX HTTP {resp.status_code} | url={url} year={year}")
                return [], failure

            data = resp.json()
            if not data or len(data) < 2:
                return [], None
            headers = data[0]
            records = [dict(zip(headers, row)) for row in data[1:]]
            return records, None

        except requests.exceptions.Timeout:
            failure = {
                "phase": phase, "url": url, "year": year,
                "params": {k: v for k, v in params.items() if k != "filter"},
                "http_status": None, "exception_type": "Timeout",
                "exception_msg": f"Timeout after {TIMEOUT}s",
            }
            log.warning(f"CDX Timeout | url={url} year={year}")
            return [], failure

        except Exception as e:
            failure = {
                "phase": phase, "url": url, "year": year,
                "params": {k: v for k, v in params.items() if k != "filter"},
                "http_status": None, "exception_type": type(e).__name__,
                "exception_msg": str(e),
            }
            log.warning(f"CDX {type(e).__name__} | url={url} year={year} — {e}")
            return [], failure

    return [], {"phase": phase, "url": url, "year": year,
                "http_status": 429, "exception_type": "RateLimited"}


def query_company_year(
    ticker: str,
    row: pd.Series,
    year: int,
    force: bool,
) -> dict:
    """
    Try all candidate URLs for a company-year. Falls back to heuristics if needed.
    Returns a result dict with the best snapshot info and selection_status.
    """
    out_path = cache_path("wayback_cdx", f"{slug(ticker, year)}.json")

    if not force and is_cached(out_path):
        return load_json(out_path)

    candidates = candidate_urls(row)
    fallbacks = fallback_urls(str(row.get("domain", "")))

    result = {
        "ticker": ticker,
        "year": year,
        "selection_status": "missing",
        "selected_url": None,
        "archive_url": None,
        "timestamp": None,
        "cdx_records": [],
        "tried_urls": [],
        "failures": [],
        "notes": "",
    }

    # Try manual candidates first (matchType=exact for configured URLs)
    for url in candidates:
        records, failure = query_cdx_for_url(url, year, match_type="exact")
        if failure:
            result["failures"].append(failure)
        result["tried_urls"].append({"url": url, "source": "manual", "hits": len(records)})
        if records:
            best = _pick_best_record(records)
            archive_url = f"https://web.archive.org/web/{best['timestamp']}id_/{best['original']}"
            result.update({
                "selection_status": "manual_primary" if url == candidates[0] else "manual_backup",
                "selected_url": url,
                "archive_url": archive_url,
                "timestamp": best["timestamp"],
                "cdx_records": records,
            })
            save_json(result, out_path)
            return result

    # Fall back to heuristics
    for url in fallbacks:
        if url in candidates:
            continue
        records, failure = query_cdx_for_url(url, year, match_type="exact")
        if failure:
            result["failures"].append(failure)
        result["tried_urls"].append({"url": url, "source": "heuristic", "hits": len(records)})
        if records:
            best = _pick_best_record(records)
            archive_url = f"https://web.archive.org/web/{best['timestamp']}id_/{best['original']}"
            result.update({
                "selection_status": "heuristic_fallback",
                "selected_url": url,
                "archive_url": archive_url,
                "timestamp": best["timestamp"],
                "cdx_records": records,
                "notes": f"No manual candidate had a snapshot; used heuristic path {url}",
            })
            log.warning(f"{ticker} {year}: heuristic fallback used — {url}")
            save_json(result, out_path)
            return result

    result["notes"] = f"No snapshot found in any of {len(candidates)} manual + {len(fallbacks)} heuristic URLs"
    log.warning(f"{ticker} {year}: MISSING — no snapshot found")
    save_json(result, out_path)
    return result


def _pick_best_record(records: list[dict]) -> dict:
    """Pick the record with timestamp closest to June 30 of its year."""
    def june30_distance(r):
        ts = r["timestamp"]
        try:
            month = int(ts[4:6])
            day = int(ts[6:8])
            return abs((month - 6) * 30 + (day - 30))
        except Exception:
            return 999
    return min(records, key=june30_distance)


def check_wayback_connectivity() -> bool:
    """Quick connectivity check using requests — returns False if unreachable."""
    try:
        resp = get_session().get(
            CDX_API,
            params={"url": "microsoft.com/en-us/about", "output": "json", "limit": "1",
                    "matchType": "exact"},
            timeout=15,
        )
        return resp.status_code < 600
    except Exception as e:
        log.error(f"web.archive.org is unreachable: {e}")
        log.error("Cannot run CDX stage. Check network connectivity to web.archive.org.")
        return False


def run_all(force: bool = False) -> list[dict]:
    df = load_about_candidates()
    years = years_range()
    tasks_spec = [(row, year) for _, row in df.iterrows() for year in years]

    log.info(f"Querying CDX for {len(tasks_spec)} company-year combinations (sequential, {CDX_REQUEST_DELAY}s delay)")

    if not check_wayback_connectivity():
        return []

    results = []
    for row, year in tqdm(tasks_spec, desc="CDX queries"):
        r = query_company_year(row["ticker"], row, year, force)
        results.append(r)

    missing = [r for r in results if r["selection_status"] == "missing"]
    fallbacks = [r for r in results if r["selection_status"] == "heuristic_fallback"]
    found = len(results) - len(missing)
    log.info(f"Done. Found: {found}, Heuristic fallbacks: {len(fallbacks)}, Missing: {len(missing)}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 1: Query Wayback CDX API")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if cached")
    args = parser.parse_args()
    run_all(force=args.force)


if __name__ == "__main__":
    main()
