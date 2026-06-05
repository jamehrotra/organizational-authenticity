"""
Stage 2: Download raw archived HTML for each selected snapshot.

Reads CDX result files from data/raw/wayback_cdx/ and downloads HTML
to data/raw/wayback_html/<ticker>_<year>.html. Skips already-cached files.

Usage:
    python -m src.part1_wayback.download_snapshots [--force] [--concurrency 5]
"""

import argparse
import asyncio
import re
from pathlib import Path

import aiohttp
from tqdm import tqdm

from src.common.io import cache_path, is_cached, save_text, load_json
from src.common.utils import setup_logging, load_about_candidates, years_range, slug

log = setup_logging("download_snapshots")

CONCURRENCY = 5
TIMEOUT = 45
WAYBACK_BASE = "https://web.archive.org/web"

# Request raw HTML without Wayback toolbar injection
RAW_FLAG = "id_"


def wayback_raw_url(timestamp: str, original_url: str) -> str:
    return f"{WAYBACK_BASE}/{timestamp}{RAW_FLAG}/{original_url}"


async def download_one(
    session: aiohttp.ClientSession,
    ticker: str,
    year: int,
    timestamp: str,
    original_url: str,
    force: bool,
) -> dict:
    out_path = cache_path("wayback_html", f"{slug(ticker, year)}.html")

    if not force and is_cached(out_path):
        return {"ticker": ticker, "year": year, "status": "cached", "path": str(out_path)}

    raw_url = wayback_raw_url(timestamp, original_url)

    try:
        async with session.get(
            raw_url,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            allow_redirects=True,
            ssl=False,
        ) as resp:
            if resp.status != 200:
                log.warning(f"{ticker} {year}: HTTP {resp.status} for {raw_url}")
                return {"ticker": ticker, "year": year, "status": f"http_{resp.status}", "path": None}
            html = await resp.text(encoding="utf-8", errors="replace")
            if len(html) < 500:
                log.warning(f"{ticker} {year}: suspiciously short HTML ({len(html)} chars)")
                return {"ticker": ticker, "year": year, "status": "too_short", "path": None}
            save_text(html, out_path)
            return {"ticker": ticker, "year": year, "status": "ok", "path": str(out_path)}
    except asyncio.TimeoutError:
        log.warning(f"{ticker} {year}: timeout downloading {raw_url}")
        return {"ticker": ticker, "year": year, "status": "timeout", "path": None}
    except Exception as e:
        log.warning(f"{ticker} {year}: error — {e}")
        return {"ticker": ticker, "year": year, "status": f"error: {e}", "path": None}


async def run_all(force: bool = False, concurrency: int = CONCURRENCY):
    df = load_about_candidates()
    years = years_range()

    # Collect all company-years that have a snapshot
    to_download = []
    for _, row in df.iterrows():
        ticker = row["ticker"]
        for year in years:
            cdx_file = cache_path("wayback_cdx", f"{slug(ticker, year)}.json")
            cdx = load_json(cdx_file)
            if cdx and cdx.get("selection_status") not in ("missing", None):
                to_download.append((ticker, year, cdx["timestamp"], cdx["selected_url"]))

    log.info(f"Downloading {len(to_download)} HTML snapshots ({concurrency} concurrent)")

    sem = asyncio.Semaphore(concurrency)
    results = []

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        async def bounded(ticker, year, ts, url):
            async with sem:
                return await download_one(session, ticker, year, ts, url, force)

        coros = [bounded(*args) for args in to_download]
        for coro in tqdm(asyncio.as_completed(coros), total=len(coros), desc="Downloading HTML"):
            r = await coro
            results.append(r)

    ok = sum(1 for r in results if r["status"] in ("ok", "cached"))
    failed = [r for r in results if r["status"] not in ("ok", "cached")]
    log.info(f"Done. Successful: {ok}, Failed: {len(failed)}")
    if failed:
        log.info("Failed cases: " + ", ".join(f"{r['ticker']} {r['year']} ({r['status']})" for r in failed[:10]))

    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 2: Download archived HTML snapshots")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY)
    args = parser.parse_args()

    asyncio.run(run_all(force=args.force, concurrency=args.concurrency))


if __name__ == "__main__":
    main()
