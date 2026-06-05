"""Shared utility functions: config loading, logging setup, slug generation."""

import logging
import re
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )
    return logging.getLogger(name)


def load_companies() -> pd.DataFrame:
    return pd.read_csv(CONFIG_DIR / "companies.csv")


def load_about_candidates() -> pd.DataFrame:
    df = pd.read_csv(CONFIG_DIR / "about_page_candidates.csv")
    df = df.fillna("")
    return df


def load_theme_taxonomy() -> dict:
    with open(CONFIG_DIR / "theme_taxonomy.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def slug(ticker: str, year: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9]", "_", ticker)
    return f"{safe}_{year}"


def years_range() -> list[int]:
    return list(range(2016, 2025))


def candidate_urls(row: pd.Series) -> list[str]:
    """Return non-empty candidate URLs for a company row, in priority order."""
    cols = ["primary_about_url", "secondary_about_url", "values_url", "mission_url"]
    urls = []
    for col in cols:
        val = str(row.get(col, "")).strip()
        if val and val.lower() not in ("nan", ""):
            urls.append(val)
    return list(dict.fromkeys(urls))  # deduplicate preserving order


FALLBACK_PATHS = [
    "/about",
    "/about-us",
    "/our-company",
    "/company",
    "/who-we-are",
    "/our-story",
    "/our-values",
    "/values",
    "/mission",
    "/purpose",
    "/about/our-story",
    "/about/values",
    "/about/mission",
]


def fallback_urls(domain: str) -> list[str]:
    base = f"https://www.{domain}" if not domain.startswith("http") else domain
    base = base.rstrip("/")
    return [base + path for path in FALLBACK_PATHS]
