"""
Part 4: Sector authenticity drift analysis.

Question: Do some sectors become more or less aligned over time? And do
companies that rebrand their stated values (high About Us page volatility)
show corresponding shifts in their formal disclosures?

Two analyses:
  A. Sector drift — plot and test whether mean authenticity score
     by sector changes significantly from 2016 to 2024.
  B. Values volatility — identify companies that changed their About Us
     language most, and compare to proxy statement drift.

Output: data/outputs/part4_sector_drift.csv
        data/outputs/part4_values_volatility.csv
        data/outputs/part4_plots/

Usage:
    python -m src.part4_exploratory.sector_drift_analysis
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from src.common.io import processed_path, outputs_path, interim_path, load_text
from src.common.utils import setup_logging, years_range, slug

log = setup_logging("sector_drift_analysis")

PLOTS_DIR = outputs_path("part4_plots")


def about_page_volatility(ticker: str) -> float:
    """
    Average year-over-year text dissimilarity for a company's About Us pages.
    Higher = the company changed its stated values language more over time.
    """
    from difflib import SequenceMatcher
    texts = []
    for year in years_range():
        t = load_text(interim_path("part1", f"{slug(ticker, year)}_clean.txt"))
        texts.append(t or "")

    changes = []
    for a, b in zip(texts, texts[1:]):
        if a and b:
            sim = SequenceMatcher(None, a[:3000], b[:3000]).ratio()
            changes.append(1 - sim)
    return float(np.mean(changes)) if changes else np.nan


def proxy_volatility(ticker: str, index_df: pd.DataFrame) -> float:
    """Average year-over-year change in authenticity score for a company."""
    company_scores = index_df[index_df["ticker"] == ticker].sort_values("year")
    if len(company_scores) < 2:
        return np.nan
    diffs = company_scores["authenticity_score"].diff().dropna().abs()
    return float(diffs.mean()) if len(diffs) > 0 else np.nan


def run():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    index_df = pd.read_csv(processed_path("part3_authenticity_index.csv"))
    valid = index_df[index_df["has_both_sources"] & index_df["authenticity_score"].notna()].copy()

    # ─── Analysis A: Sector drift ─────────────────────────────────────────────

    sector_year = (
        valid.groupby(["sector", "year"])["authenticity_score"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    sector_year.columns = ["sector", "year", "mean_score", "std_score", "n"]

    # Test for linear trend within each sector (simple OLS slope)
    trend_results = []
    for sector, grp in sector_year.groupby("sector"):
        grp_sorted = grp.sort_values("year")
        if len(grp_sorted) < 3:
            continue
        slope, intercept, r, p, se = stats.linregress(grp_sorted["year"], grp_sorted["mean_score"])
        trend_results.append({
            "sector": sector,
            "slope": round(slope, 5),
            "r_squared": round(r**2, 4),
            "p_value": round(p, 4),
            "trend": "increasing" if slope > 0 else "decreasing",
            "significant": p < 0.10,
            "score_2016": grp_sorted[grp_sorted["year"] == 2016]["mean_score"].values[0] if 2016 in grp_sorted["year"].values else None,
            "score_2024": grp_sorted[grp_sorted["year"] == 2024]["mean_score"].values[0] if 2024 in grp_sorted["year"].values else None,
        })

    trend_df = pd.DataFrame(trend_results)
    drift_path = outputs_path("part4_sector_drift.csv")
    trend_df.to_csv(drift_path, index=False)
    log.info(f"Sector drift results: {drift_path}")

    # Plot sector drift
    fig, ax = plt.subplots(figsize=(13, 6))
    palette = sns.color_palette("tab10", n_colors=sector_year["sector"].nunique())
    for i, (sector, grp) in enumerate(sector_year.groupby("sector")):
        ax.plot(grp["year"], grp["mean_score"], marker="o", label=sector, color=palette[i], linewidth=2)
        ax.fill_between(
            grp["year"],
            grp["mean_score"] - grp["std_score"] / np.sqrt(grp["n"].clip(1)),
            grp["mean_score"] + grp["std_score"] / np.sqrt(grp["n"].clip(1)),
            alpha=0.15, color=palette[i],
        )

    ax.set_title("Sector Authenticity Drift: Mean Alignment Score by Sector, 2016–2024\n"
                 "(shaded band = ±1 SE)", fontsize=12)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean Authenticity Score (cosine similarity)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    ax.set_xticks(list(years_range()))
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "sector_drift.png", dpi=150)
    plt.close(fig)

    # ─── Analysis B: Values volatility ───────────────────────────────────────

    tickers = valid["ticker"].unique()
    vol_rows = []
    for ticker in tickers:
        about_vol = about_page_volatility(ticker)
        proxy_vol = proxy_volatility(ticker, valid)
        sector = valid[valid["ticker"] == ticker]["sector"].iloc[0]
        company = valid[valid["ticker"] == ticker]["company_name"].iloc[0]
        vol_rows.append({
            "ticker": ticker,
            "company_name": company,
            "sector": sector,
            "about_page_volatility": round(about_vol, 4) if not np.isnan(about_vol) else None,
            "proxy_score_volatility": round(proxy_vol, 4) if not np.isnan(proxy_vol) else None,
        })

    vol_df = pd.DataFrame(vol_rows)
    vol_path = outputs_path("part4_values_volatility.csv")
    vol_df.to_csv(vol_path, index=False)
    log.info(f"Values volatility results: {vol_path}")

    # Scatter: about volatility vs proxy volatility
    plot_data = vol_df.dropna(subset=["about_page_volatility", "proxy_score_volatility"])
    if len(plot_data) > 3:
        fig, ax = plt.subplots(figsize=(9, 7))
        palette = {s: c for s, c in zip(plot_data["sector"].unique(),
                                         sns.color_palette("tab10", n_colors=plot_data["sector"].nunique()))}
        for _, row in plot_data.iterrows():
            color = palette.get(row["sector"], "gray")
            ax.scatter(row["about_page_volatility"], row["proxy_score_volatility"],
                       color=color, s=60, alpha=0.8)
            ax.annotate(row["ticker"], (row["about_page_volatility"], row["proxy_score_volatility"]),
                        fontsize=7, alpha=0.7)

        # Trend line
        x = plot_data["about_page_volatility"].values
        y = plot_data["proxy_score_volatility"].values
        slope, intercept, r, p, _ = stats.linregress(x, y)
        xfit = np.linspace(x.min(), x.max(), 100)
        ax.plot(xfit, slope * xfit + intercept, "k--", alpha=0.5,
                label=f"OLS fit (r={r:.2f}, p={p:.3f})")

        # Legend for sectors
        for sector, color in palette.items():
            ax.scatter([], [], color=color, label=sector, s=60)

        ax.set_title("Values Volatility: About Page Drift vs. Authenticity Score Drift\n"
                     "(does changing your stated values align with changing disclosures?)", fontsize=11)
        ax.set_xlabel("About Page Volatility (avg. year-over-year text dissimilarity)")
        ax.set_ylabel("Proxy Score Volatility (avg. year-over-year |Δ authenticity|)")
        ax.legend(loc="best", fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "values_volatility_scatter.png", dpi=150)
        plt.close(fig)

    log.info(f"All Part 4 outputs saved to: {PLOTS_DIR}")
    return trend_df, vol_df


if __name__ == "__main__":
    run()
