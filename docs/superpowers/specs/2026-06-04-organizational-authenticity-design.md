# Design Spec: Organizational Authenticity Research Pipeline
**Date:** 2026-06-04

## Overview

A reproducible Python pipeline that measures alignment between what 50 S&P 500 companies
say they value (About Us pages, 2016–2024) and what their formal disclosures suggest they
actually prioritize (SEC proxy statements, same period).

## Architecture

Four sequential parts, each producing a dataset that feeds the next.

```
Part 1 (Wayback)  →  part1_dataset.csv
Part 2 (EDGAR)    →  part2_dataset.csv
                         ↓
Part 3 (Index)   ←  theme_vectors.csv  →  part3_authenticity_index.csv
                                                  ↓
Part 4 (Analysis)          sector_drift.csv + values_volatility.csv
```

## Data Sources

- **Part 1:** Wayback Machine CDX API (free, no key required). One snapshot per company-year.
- **Part 2:** SEC EDGAR DEF 14A filings via `sec-edgar-downloader`. Chosen over ESG reports
  for consistent coverage and single-source reproducibility.

## URL Selection Strategy (Part 1)

Manual-first, heuristic-second:
1. `config/about_page_candidates.csv` contains 1–4 manually researched URLs per company.
2. CDX API is queried against manual candidates in priority order.
3. If no manual candidate yields a snapshot, 14 heuristic paths are tried.
4. Every fallback is logged; missing cases are retained in the dataset.

## Theme Taxonomy

10 sector-neutral themes in `config/theme_taxonomy.yaml`:
innovation, customers_or_patients, employees, diversity_equity_inclusion,
sustainability_environment, community_social_impact, ethics_integrity,
governance_accountability, financial_performance, safety_quality.

Scored 0–3 by Claude Haiku per document.

## Authenticity Index

```
score = cosine_similarity(
    L2_normalize(about_theme_vector),
    L2_normalize(proxy_theme_vector)
)
```

Cosine similarity on L2-normalized vectors captures alignment of emphasis *pattern*,
not absolute volume.

## LLM Strategy

- Model: Claude Haiku (fast, cheap, sufficient for 0–3 scoring tasks)
- Balanced async: 5–10 concurrent HTTP requests for scraping; LLM calls are separate stage
- All LLM outputs cached to disk; pipeline is fully restartable
- `--force` flag bypasses cache for any stage

## Pipeline CLI

```
python run_pipeline.py [stages...] [--from stage] [--force]
```

11 named stages, each independently runnable.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM provider | Anthropic (Haiku) | User has Claude Pro; Haiku is cheapest per token |
| Disclosure type | DEF 14A proxy | Consistent EDGAR coverage > richer but patchy ESG reports |
| URL discovery | Manual config + heuristic fallback | Prevents silent scraping errors; auditable |
| Similarity metric | Cosine similarity | Captures pattern, not magnitude; well-understood |
| Concurrency | 5–10 async HTTP | Balanced; respects Wayback rate limits |
| Text extraction | Trafilatura + BS4 fallback | Trafilatura is best-in-class; BS4 is robust fallback |
