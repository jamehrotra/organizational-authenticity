"""
Stage 1: Query the Wayback Machine CDX API for each company-year-URL combination.

For each company, we try candidate URLs (from about_page_candidates.csv) first.
If none return results, we fall back to common path heuristics.
All CDX responses are cached under data/raw/wayback_cdx/.

Usage:
    python -m src.part1_wayback.query_cdx [--force]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import aiohttp
import pandas as pd
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
CONCURRENCY = 5
TIMEOUT = 45


async def query_cdx_for_url(
    session: aiohttp.ClientSession,
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
    try:
        async with session.get(
            CDX_API,
            params=params,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            ssl=False,
        ) as resp:
            if resp.status != 200:
                failure = {
                    "phase": phase,
                    "url": url,
                    "year": year,
                    "params": params,
                    "http_status": resp.status,
                    "exception_type": None,
                }
                log.warning(
                    f"CDX HTTP {resp.status} | url={url} year={year} params={params}"
                )
                return [], failure
            data = await resp.json(content_type=None)
            if not data or len(data) < 2:
                return [], None
            headers = data[0]
            records = [dict(zip(headers, row)) for row in data[1:]]
            return records, None
    except Exception as e:
        failure = {
            "phase": phase,
            "url": url,
            "year": year,
            "params": params,
            "http_status": None,
            "exception_type": type(e).__name__,
            "exception_msg": str(e),
        }
        log.warning(
            f"CDX {type(e).__name__} | url={url} year={year} params={params} — {e}"
        )
        return [], failure


async def query_company_year(
    session: aiohttp.ClientSession,
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

    # Try manual candidates first (matchType=exact as specified for configured URLs)
    for url in candidates:
        records, failure = await query_cdx_for_url(session, url, year, match_type="exact")
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

    # Fall back to heuristics (prefix match makes sense here)
    for url in fallbacks:
        if url in candidates:
            continue
        records, failure = await query_cdx_for_url(session, url, year, match_type="exact")
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
            # Distance in days from June 30 (month 6, day 30)
            return abs((month - 6) * 30 + (day - 30))
        except Exception:
            return 999
    return min(records, key=june30_distance)


async def _check_wayback_connectivity(session: aiohttp.ClientSession) -> bool:
    """Quick connectivity check — returns False if web.archive.org is unreachable."""
    try:
        async with session.get(
            CDX_API,
            params={"url": "example.com", "output": "json", "limit": "1"},
            timeout=aiohttp.ClientTimeout(total=15),
            ssl=False,
        ) as resp:
            return resp.status in (200, 404)
    except Exception as e:
        log.error(f"web.archive.org is unreachable: {e}")
        log.error("Cannot run CDX stage. Check network connectivity to web.archive.org.")
        log.error("Try running again later or from a different network.")
        return False


async def run_all(force: bool = False):
    df = load_about_candidates()
    years = years_range()
    tasks_spec = [(row, year) for _, row in df.iterrows() for year in years]

    log.info(f"Querying CDX for {len(tasks_spec)} company-year combinations ({CONCURRENCY} concurrent)")

    sem = asyncio.Semaphore(CONCURRENCY)
    results = []

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        if not await _check_wayback_connectivity(session):
            return []

        async def bounded(row, year):
            async with sem:
                return await query_company_year(session, row["ticker"], row, year, force)

        coros = [bounded(row, year) for row, year in tasks_spec]
        for coro in tqdm(asyncio.as_completed(coros), total=len(coros), desc="CDX queries"):
            r = await coro
            results.append(r)

    missing = [r for r in results if r["selection_status"] == "missing"]
    fallbacks = [r for r in results if r["selection_status"] == "heuristic_fallback"]
    log.info(f"Done. Missing: {len(missing)}, Heuristic fallbacks: {len(fallbacks)}, Found: {len(results)-len(missing)}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 1: Query Wayback CDX API")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if cached")
    args = parser.parse_args()

    asyncio.run(run_all(force=args.force))


if __name__ == "__main__":
    main()
