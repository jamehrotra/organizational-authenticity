"""
Part 2, Stage 3: LLM analysis of proxy statement text.

For each company-year, asks Claude to score each theme from the taxonomy
and produce tone/topic emphasis analysis.

Output: data/processed/part2_dataset.csv

Usage:
    python -m src.part2_disclosures.analyze_disclosures [--force] [--model claude-haiku-4-5-20251001]
"""

import argparse
import json
import time
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.common.io import interim_path, processed_path, is_cached, load_text, load_json
from src.common.llm import call_claude_json
from src.common.utils import (
    setup_logging,
    load_companies,
    load_theme_taxonomy,
    years_range,
    slug,
)

log = setup_logging("analyze_disclosures")

SYSTEM_PROMPT = """You are a research assistant analyzing corporate proxy statements (DEF 14A filings).
You will be given excerpts from a proxy statement and must score each value theme based on how
prominently that theme appears in the document.

Proxy statements often emphasize governance and financial performance. Note when other themes
like employees, sustainability, or community appear prominently, as this is analytically significant.

Always return valid JSON with no additional commentary outside the JSON block."""


def build_prompt(ticker: str, company: str, sector: str, year: int, text: str, taxonomy: dict) -> str:
    theme_descriptions = "\n".join(
        f'- "{name}": {info["description"].strip()}'
        for name, info in taxonomy["themes"].items()
    )
    theme_names = list(taxonomy["themes"].keys())

    # Use first 5000 words of proxy — proxy statements are long; focus on substantive sections
    words = text.split()
    excerpt = " ".join(words[:5000])

    return f"""Company: {company} ({ticker}), Sector: {sector}, Year: {year}
Document type: DEF 14A Proxy Statement

DOCUMENT EXCERPT (first ~5000 words):
{excerpt}

TASK:
Score each theme based on how prominently it appears in this proxy statement.
Use 0-3 scale: 0=absent, 1=mentioned briefly, 2=clearly emphasized, 3=central focus.

THEMES:
{theme_descriptions}

Return a JSON object with exactly these keys:
{{
  "themes": {{
    {", ".join(f'"{t}": <0-3>' for t in theme_names)}
  }},
  "dominant_themes": ["<top theme>", "<2nd>", "<3rd>"],
  "dei_emphasis": <0-3 score specifically for DEI language>,
  "esg_emphasis": <0-3 score for environmental/sustainability language>,
  "employee_emphasis": <0-3 score for employee/workforce language>,
  "shareholder_emphasis": <0-3 score for shareholder/investor language>,
  "tone_summary": "<1-2 sentences describing the overall tone and priorities of this proxy>",
  "analyst_notes": "<any notable language, shifts, or patterns worth flagging>"
}}"""


def run_all(force: bool = False, model: str = "claude-haiku-4-5-20251001"):
    companies = load_companies()
    taxonomy = load_theme_taxonomy()
    years = years_range()
    theme_names = list(taxonomy["themes"].keys())

    rows = []

    for _, company_row in tqdm(companies.iterrows(), total=len(companies), desc="Analyzing disclosures"):
        ticker = company_row["ticker"]
        company = company_row["company_name"]
        sector = company_row["sector"]

        for year in years:
            sl = slug(ticker, year)
            text_path = interim_path("part2", f"{sl}_proxy_clean.txt")
            llm_cache = interim_path("part2", f"{sl}_proxy_llm.json")

            text = load_text(text_path) or ""
            has_text = len(text.split()) >= 100

            llm_result = None
            if has_text:
                if not force and is_cached(llm_cache):
                    llm_result = load_json(llm_cache)
                else:
                    prompt = build_prompt(ticker, company, sector, year, text, taxonomy)
                    llm_result = call_claude_json(
                        prompt=prompt,
                        system=SYSTEM_PROMPT,
                        model=model,
                        max_tokens=900,
                        cache_path=llm_cache,
                        force=force,
                    )
                    time.sleep(3)

            theme_scores = {}
            dominant = []
            tone_summary = ""
            analyst_notes = ""

            if llm_result:
                theme_scores = llm_result.get("themes", {})
                dominant = llm_result.get("dominant_themes", [])
                tone_summary = llm_result.get("tone_summary", "")
                analyst_notes = llm_result.get("analyst_notes", "")

            row = {
                "ticker": ticker,
                "company_name": company,
                "sector": sector,
                "year": year,
                "doc_type": "DEF 14A",
                "has_filing": has_text,
                "word_count": len(text.split()),
                "theme_categories": json.dumps(theme_scores),
                "dominant_themes": json.dumps(dominant),
                "dei_emphasis": llm_result.get("dei_emphasis") if llm_result else None,
                "esg_emphasis": llm_result.get("esg_emphasis") if llm_result else None,
                "employee_emphasis": llm_result.get("employee_emphasis") if llm_result else None,
                "shareholder_emphasis": llm_result.get("shareholder_emphasis") if llm_result else None,
                "tone_summary": tone_summary,
                "analyst_notes": analyst_notes,
            }

            for t in theme_names:
                row[f"theme_{t}"] = theme_scores.get(t)

            rows.append(row)

    out_df = pd.DataFrame(rows)
    out_path = processed_path("part2_dataset.csv")
    out_df.to_csv(out_path, index=False)

    coverage = out_df["has_filing"].sum()
    log.info(f"Part 2 dataset saved: {out_path} ({len(out_df)} rows, {coverage} with filings)")
    return out_df


def main():
    parser = argparse.ArgumentParser(description="LLM analysis of proxy statements")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    args = parser.parse_args()
    run_all(force=args.force, model=args.model)


if __name__ == "__main__":
    main()
