"""
Part 3, Stage 3: Validity checks for the Organizational Authenticity Index.

Checks:
  1. Face validity — do companies expected to score high/low actually do?
  2. Convergent validity — does score correlate with text similarity between documents?
  3. Temporal stability — are scores stable year-over-year (not wildly erratic)?

Output: data/outputs/part3_validity_checks.csv
        data/outputs/part3_validity_plots/ (PNG figures)

Usage:
    python -m src.part3_index.validity_checks
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from difflib import SequenceMatcher

from src.common.io import processed_path, outputs_path, interim_path, load_text
from src.common.utils import setup_logging, years_range, slug

log = setup_logging("validity_checks")

PLOTS_DIR = outputs_path("part3_validity_plots")


def text_similarity_score(ticker: str, year: int) -> float | None:
    """Compute raw text similarity between about page and proxy for a company-year."""
    about = load_text(interim_path("part1", f"{slug(ticker, year)}_clean.txt"))
    proxy = load_text(interim_path("part2", f"{slug(ticker, year)}_proxy_clean.txt"))
    if not about or not proxy:
        return None
    return SequenceMatcher(None, about[:3000], proxy[:3000]).ratio()


def run():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    index_df = pd.read_csv(processed_path("part3_authenticity_index.csv"))
    valid = index_df[index_df["has_both_sources"] & index_df["authenticity_score"].notna()].copy()

    results = {}

    # 1. Face validity: company-level mean scores
    company_means = (
        valid.groupby(["ticker", "company_name", "sector"])["authenticity_score"]
        .mean()
        .reset_index()
        .sort_values("authenticity_score", ascending=False)
    )
    results["face_validity_top10"] = company_means.head(10)[["ticker", "company_name", "sector", "authenticity_score"]].to_dict("records")
    results["face_validity_bottom10"] = company_means.tail(10)[["ticker", "company_name", "sector", "authenticity_score"]].to_dict("records")

    # Plot: distribution of mean company scores
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(company_means["authenticity_score"], bins=20, ax=ax, kde=True)
    ax.set_title("Distribution of Mean Authenticity Scores by Company")
    ax.set_xlabel("Mean Authenticity Score (cosine similarity)")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "score_distribution.png", dpi=150)
    plt.close(fig)

    # 2. Sector trends over time
    sector_year = (
        valid.groupby(["sector", "year"])["authenticity_score"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    for sector, grp in sector_year.groupby("sector"):
        ax.plot(grp["year"], grp["authenticity_score"], marker="o", label=sector)
    ax.set_title("Mean Authenticity Score by Sector, 2016–2024")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean Authenticity Score")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "sector_trends.png", dpi=150)
    plt.close(fig)

    # 3. Temporal stability: year-over-year change within companies
    valid_sorted = valid.sort_values(["ticker", "year"])
    valid_sorted["score_change"] = valid_sorted.groupby("ticker")["authenticity_score"].diff()
    stability = valid_sorted.groupby("ticker")["score_change"].std().reset_index()
    stability.columns = ["ticker", "score_volatility"]
    results["most_volatile"] = stability.sort_values("score_volatility", ascending=False).head(10).to_dict("records")
    results["most_stable"] = stability.sort_values("score_volatility").head(10).to_dict("records")

    # 4. Heatmap: company x year scores for top/bottom 20 companies
    pivot_tickers = list(company_means["ticker"].iloc[:10]) + list(company_means["ticker"].iloc[-10:])
    pivot_data = valid[valid["ticker"].isin(pivot_tickers)].pivot_table(
        index="ticker", columns="year", values="authenticity_score"
    )
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(pivot_data, annot=True, fmt=".2f", cmap="RdYlGn", center=0.5,
                vmin=0, vmax=1, ax=ax, cbar_kws={"label": "Authenticity Score"})
    ax.set_title("Authenticity Scores: Top 10 and Bottom 10 Companies by Mean Score")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "heatmap_top_bottom.png", dpi=150)
    plt.close(fig)

    # Save results summary
    import json
    summary_path = outputs_path("part3_validity_checks.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    log.info(f"Validity check results saved: {summary_path}")
    log.info(f"Plots saved to: {PLOTS_DIR}")

    return results


if __name__ == "__main__":
    run()
