"""
Part 3, Stage 2: Compute the Organizational Authenticity Index.

Authenticity score = cosine_similarity(about_theme_vector, proxy_theme_vector)

A score of 1.0 means the company's stated values (About Us page) perfectly
align with its formal disclosure priorities (proxy statement). A score near 0
means the two documents emphasize completely different themes.

Output: data/processed/part3_authenticity_index.csv
        data/outputs/part3_summary_statistics.csv

Usage:
    python -m src.part3_index.compute_authenticity_index
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.common.io import interim_path, processed_path, outputs_path
from src.common.utils import setup_logging

log = setup_logging("compute_authenticity_index")

THEME_SHORT = [
    "innovation",
    "customers_or_patients",
    "employees",
    "diversity_equity_inclusion",
    "sustainability_environment",
    "community_social_impact",
    "ethics_integrity",
    "governance_accountability",
    "financial_performance",
    "safety_quality",
]


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a.sum() == 0 or b.sum() == 0:
        return np.nan
    return float(cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0][0])


def top_themes(vec: np.ndarray, n: int = 3) -> list[str]:
    idxs = vec.argsort()[::-1][:n]
    return [THEME_SHORT[i] for i in idxs if vec[i] > 0]


def largest_gap(about: np.ndarray, proxy: np.ndarray) -> str:
    """Theme where about score most exceeds proxy score (stated but not lived)."""
    gaps = about - proxy
    idx = int(gaps.argmax())
    return THEME_SHORT[idx] if gaps[idx] > 0 else "none"


def run():
    vectors = pd.read_csv(interim_path("part3", "theme_vectors.csv"))

    rows = []
    for _, row in vectors.iterrows():
        about_vec = np.nan_to_num(
            np.array([row.get(f"about_{t}", 0) for t in THEME_SHORT], dtype=float), nan=0.0
        )
        proxy_vec = np.nan_to_num(
            np.array([row.get(f"proxy_{t}", 0) for t in THEME_SHORT], dtype=float), nan=0.0
        )

        score = cosine_sim(about_vec, proxy_vec)

        top_stated = top_themes(about_vec)
        top_lived = top_themes(proxy_vec)
        gap = largest_gap(about_vec, proxy_vec)

        both_have_data = bool(row.get("about_has_data") and row.get("proxy_has_data"))

        rows.append({
            "ticker": row["ticker"],
            "company_name": row.get("company_name", ""),
            "sector": row.get("sector", ""),
            "year": int(row["year"]),
            "authenticity_score": round(score, 4) if not np.isnan(score) else None,
            "has_both_sources": both_have_data,
            "top_stated_themes": "|".join(top_stated),
            "top_lived_themes": "|".join(top_lived),
            "largest_theme_gap": gap,
        })

    df = pd.DataFrame(rows)

    # Save full index
    out_path = processed_path("part3_authenticity_index.csv")
    df.to_csv(out_path, index=False)
    log.info(f"Authenticity index saved: {out_path} ({len(df)} rows)")

    # Summary statistics
    valid = df[df["has_both_sources"] & df["authenticity_score"].notna()]

    summary_rows = []

    # Overall
    summary_rows.append({
        "group": "Overall",
        "n": len(valid),
        "mean_score": round(valid["authenticity_score"].mean(), 4),
        "median_score": round(valid["authenticity_score"].median(), 4),
        "std_score": round(valid["authenticity_score"].std(), 4),
        "min_score": round(valid["authenticity_score"].min(), 4),
        "max_score": round(valid["authenticity_score"].max(), 4),
    })

    # By sector
    for sector, grp in valid.groupby("sector"):
        summary_rows.append({
            "group": f"Sector: {sector}",
            "n": len(grp),
            "mean_score": round(grp["authenticity_score"].mean(), 4),
            "median_score": round(grp["authenticity_score"].median(), 4),
            "std_score": round(grp["authenticity_score"].std(), 4),
            "min_score": round(grp["authenticity_score"].min(), 4),
            "max_score": round(grp["authenticity_score"].max(), 4),
        })

    # By year
    for year, grp in valid.groupby("year"):
        summary_rows.append({
            "group": f"Year: {year}",
            "n": len(grp),
            "mean_score": round(grp["authenticity_score"].mean(), 4),
            "median_score": round(grp["authenticity_score"].median(), 4),
            "std_score": round(grp["authenticity_score"].std(), 4),
            "min_score": round(grp["authenticity_score"].min(), 4),
            "max_score": round(grp["authenticity_score"].max(), 4),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_path = outputs_path("part3_summary_statistics.csv")
    summary_df.to_csv(summary_path, index=False)
    log.info(f"Summary statistics saved: {summary_path}")

    # Print top/bottom 5 companies by mean score
    company_means = valid.groupby(["ticker", "company_name"])["authenticity_score"].mean().sort_values()
    log.info("Lowest authenticity (mean over all years):\n" + company_means.head(5).to_string())
    log.info("Highest authenticity (mean over all years):\n" + company_means.tail(5).to_string())

    return df, summary_df


if __name__ == "__main__":
    run()
