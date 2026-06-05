"""
Stage 4: LLM analysis of cleaned About Us page text.

For each company-year, asks Claude to:
  (a) detect whether the page changed from the prior year
  (b) score each theme from the taxonomy (0-3)
  (c) identify dominant themes and linguistic shifts

Reads from data/interim/part1/ and writes LLM outputs to
data/interim/part1/<ticker>_<year>_llm.json.

Finally assembles data/processed/part1_dataset.csv.

Usage:
    python -m src.part1_wayback.analyze_about_pages [--force] [--model claude-haiku-4-5-20251001]
"""

import argparse
import json
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.common.io import interim_path, processed_path, is_cached, load_text, load_json, save_json
from src.common.io import cache_path
from src.common.llm import call_claude_json
from src.common.utils import (
    setup_logging,
    load_about_candidates,
    load_theme_taxonomy,
    years_range,
    slug,
)

log = setup_logging("analyze_about_pages")

SYSTEM_PROMPT = """You are a research assistant analyzing corporate values and mission statements.
You will be given the visible text from a company's About Us / Mission / Values webpage, archived
from a specific year. Your task is to score each value theme and identify key patterns.

Always return valid JSON with no additional commentary outside the JSON block."""


def build_prompt(ticker: str, company: str, sector: str, year: int, text: str, taxonomy: dict) -> str:
    theme_descriptions = "\n".join(
        f'- "{name}": {info["description"].strip()}'
        for name, info in taxonomy["themes"].items()
    )
    theme_names = list(taxonomy["themes"].keys())

    return f"""Company: {company} ({ticker}), Sector: {sector}, Year: {year}

WEBPAGE TEXT:
{text[:4000]}

TASK:
Score each of these themes based on how prominently they appear in the text above.
Use a 0-3 scale: 0=absent, 1=mentioned, 2=emphasized, 3=central theme.

THEMES:
{theme_descriptions}

Return a JSON object with exactly these keys:
{{
  "themes": {{
    {", ".join(f'"{t}": <0-3>' for t in theme_names)}
  }},
  "dominant_themes": ["<top theme>", "<2nd>", "<3rd>"],
  "word_count": <integer>,
  "analyst_notes": "<1-2 sentences on what this page emphasizes or any notable language>"
}}"""


def text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a[:3000], b[:3000]).ratio()


def run_all(force: bool = False, model: str = "claude-haiku-4-5-20251001"):
    df = load_about_candidates()
    taxonomy = load_theme_taxonomy()
    years = years_range()
    theme_names = list(taxonomy["themes"].keys())

    rows = []

    for _, company_row in tqdm(df.iterrows(), total=len(df), desc="Analyzing companies"):
        ticker = company_row["ticker"]
        company = company_row["company_name"]
        sector = company_row["sector"]

        prev_text = None

        for year in years:
            sl = slug(ticker, year)
            text_path = interim_path("part1", f"{sl}_clean.txt")
            llm_cache = interim_path("part1", f"{sl}_llm.json")
            cdx_cache = cache_path("wayback_cdx", f"{sl}.json")

            text = load_text(text_path) or ""
            cdx = load_json(cdx_cache) or {}

            # Compute text change flag vs prior year
            similarity = text_similarity(prev_text or "", text)
            changed = bool(prev_text is not None and similarity < 0.85 and text)

            # LLM analysis
            llm_result = None
            if text and len(text.split()) >= 30:
                if not force and is_cached(llm_cache):
                    llm_result = load_json(llm_cache)
                else:
                    prompt = build_prompt(ticker, company, sector, year, text, taxonomy)
                    llm_result = call_claude_json(
                        prompt=prompt,
                        system=SYSTEM_PROMPT,
                        model=model,
                        max_tokens=800,
                        cache_path=llm_cache,
                        force=force,
                    )

            # Extract theme scores
            theme_scores = {}
            dominant = []
            analyst_notes = ""

            if llm_result:
                theme_scores = llm_result.get("themes", {})
                dominant = llm_result.get("dominant_themes", [])
                analyst_notes = llm_result.get("analyst_notes", "")

            row = {
                "ticker": ticker,
                "company_name": company,
                "sector": sector,
                "year": year,
                "page_url": cdx.get("selected_url", ""),
                "archive_url": cdx.get("archive_url", ""),
                "selection_status": cdx.get("selection_status", "missing"),
                "page_text_clean": text,
                "word_count": len(text.split()),
                "changed_from_prior": changed,
                "text_similarity_to_prior": round(similarity, 3),
                "theme_categories": json.dumps(theme_scores),
                "dominant_themes": json.dumps(dominant),
                "analyst_notes": analyst_notes,
            }

            # Add individual theme score columns
            for t in theme_names:
                row[f"theme_{t}"] = theme_scores.get(t, None)

            rows.append(row)
            prev_text = text

    out_df = pd.DataFrame(rows)
    out_path = processed_path("part1_dataset.csv")
    out_df.to_csv(out_path, index=False)
    log.info(f"Part 1 dataset saved: {out_path} ({len(out_df)} rows)")

    missing = out_df[out_df["selection_status"] == "missing"]
    log.info(f"Missing snapshots: {len(missing)} / {len(out_df)}")

    return out_df


def main():
    parser = argparse.ArgumentParser(description="Stage 4: LLM analysis of About Us pages")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    args = parser.parse_args()
    run_all(force=args.force, model=args.model)


if __name__ == "__main__":
    main()
