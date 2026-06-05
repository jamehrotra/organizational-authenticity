"""
Part 3, Stage 1: Convert theme scores into normalized vectors for each company-year.

Reads part1_dataset.csv and part2_dataset.csv and produces
data/interim/part3/theme_vectors.csv with one row per company-year
containing aligned theme score vectors for both About Us and proxy.

Usage:
    python -m src.part3_index.construct_theme_vectors
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.io import interim_path, processed_path
from src.common.utils import setup_logging, load_theme_taxonomy

log = setup_logging("construct_theme_vectors")

THEME_COLS = [
    "theme_innovation",
    "theme_customers_or_patients",
    "theme_employees",
    "theme_diversity_equity_inclusion",
    "theme_sustainability_environment",
    "theme_community_social_impact",
    "theme_ethics_integrity",
    "theme_governance_accountability",
    "theme_financial_performance",
    "theme_safety_quality",
]


def normalize_vector(scores: np.ndarray) -> np.ndarray:
    """L2-normalize a score vector. Returns zero vector if all zeros."""
    norm = np.linalg.norm(scores)
    if norm == 0:
        return scores
    return scores / norm


def load_theme_vector(row: pd.Series, prefix: str = "") -> np.ndarray:
    """Extract theme scores from a dataframe row as a numpy array."""
    cols = THEME_COLS
    scores = []
    for col in cols:
        val = row.get(col, 0)
        try:
            scores.append(float(val) if pd.notna(val) else 0.0)
        except (ValueError, TypeError):
            scores.append(0.0)
    return np.array(scores, dtype=float)


def run():
    part2 = pd.read_csv(processed_path("part2_dataset.csv"))

    part1_path = processed_path("part1_dataset.csv")
    if part1_path.exists():
        part1 = pd.read_csv(part1_path)
        log.info("Part 1 dataset loaded.")
    else:
        log.warning("part1_dataset.csv not found — running with proxy data only (Part 1 blocked).")
        part1 = pd.DataFrame(columns=["ticker", "company_name", "sector", "year", "selection_status"] + THEME_COLS)

    # Merge on ticker + year — outer so Part 2-only rows are retained when Part 1 is absent
    merged = pd.merge(
        part1[["ticker", "company_name", "sector", "year", "selection_status"] + THEME_COLS],
        part2[["ticker", "company_name", "sector", "year"] + THEME_COLS],
        on=["ticker", "year"],
        suffixes=("_about", "_proxy"),
        how="outer",
    )
    # Fill company metadata from whichever side has it
    merged["company_name"] = merged["company_name_about"].combine_first(merged["company_name_proxy"])
    merged["sector"] = merged["sector_about"].combine_first(merged["sector_proxy"])

    rows = []
    for _, row in merged.iterrows():
        about_cols = [c + "_about" for c in THEME_COLS]
        proxy_cols = [c + "_proxy" for c in THEME_COLS]

        about_vec = np.array([
            float(row.get(c, 0) or 0) for c in about_cols
        ])
        proxy_vec = np.array([
            float(row.get(c, 0) or 0) for c in proxy_cols
        ])

        about_norm = normalize_vector(about_vec)
        proxy_norm = normalize_vector(proxy_vec)

        out = {
            "ticker": row["ticker"],
            "company_name": row.get("company_name") or row.get("company_name_proxy", ""),
            "sector": row.get("sector") or row.get("sector_proxy", ""),
            "year": row["year"],
            "about_has_data": bool(about_vec.sum() > 0),
            "proxy_has_data": bool(proxy_vec.sum() > 0),
        }

        theme_short = [c.replace("theme_", "") for c in THEME_COLS]
        for i, t in enumerate(theme_short):
            out[f"about_{t}"] = about_vec[i]
            out[f"proxy_{t}"] = proxy_vec[i]
            out[f"about_{t}_norm"] = about_norm[i]
            out[f"proxy_{t}_norm"] = proxy_norm[i]

        rows.append(out)

    out_df = pd.DataFrame(rows)
    out_path = interim_path("part3", "theme_vectors.csv")
    out_df.to_csv(out_path, index=False)
    log.info(f"Theme vectors saved: {out_path} ({len(out_df)} rows)")
    return out_df


if __name__ == "__main__":
    run()
