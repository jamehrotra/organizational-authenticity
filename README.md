# Organizational Authenticity Research Pipeline

A reproducible Python pipeline measuring alignment between what S&P 500 companies
say they value (About Us pages) and what their formal disclosures suggest they
actually prioritize (SEC proxy statements).

## Troubleshooting

**`web.archive.org` unreachable (WinError 121 / connection timeout):**
The Wayback Machine CDX API can be blocked by some corporate/campus networks or temporarily
rate-limited. If the `cdx` stage fails with connection timeouts:
1. Try from a different network (home network, mobile hotspot, VPN)
2. Check if `curl https://web.archive.org` works in your terminal
3. The pipeline will detect this and fail fast with a clear error message
4. All other stages (SEC EDGAR, LLM analysis, index) can run independently

**BRK.B / Berkshire Hathaway on EDGAR:**
EDGAR uses `BRK-B` (not `BRK.B`) as the ticker. The pipeline handles this automatically
via the `EDGAR_TICKER_MAP` in `fetch_sec_filings.py`.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Run the full pipeline
python run_pipeline.py

# Or run individual stages
python run_pipeline.py cdx download extract analyze1
python run_pipeline.py fetch_sec extract2 analyze2
python run_pipeline.py vectors index validity part4

# Resume from a specific stage (all caches respected)
python run_pipeline.py --from index

# Force re-run a stage (ignore cache)
python run_pipeline.py analyze1 --force
```

## Pipeline Stages

| Stage | Command | Description |
|-------|---------|-------------|
| 1 | `cdx` | Query Wayback CDX API for each company-year |
| 2 | `download` | Download archived HTML snapshots |
| 3 | `extract` | Extract clean text from HTML |
| 4 | `analyze1` | LLM theme analysis of About Us pages |
| 5 | `fetch_sec` | Download DEF 14A proxy statements from SEC EDGAR |
| 6 | `extract2` | Extract clean text from proxy statements |
| 7 | `analyze2` | LLM theme analysis of proxy statements |
| 8 | `vectors` | Build normalized theme vectors |
| 9 | `index` | Compute Organizational Authenticity Index |
| 10 | `validity` | Validity checks and plots |
| 11 | `part4` | Sector drift and values volatility analysis |

## Repository Structure

```
organizational-authenticity/
├── run_pipeline.py              # Master CLI runner
├── requirements.txt
├── .env.example
├── config/
│   ├── companies.csv            # 50 S&P 500 companies (fixed sample)
│   ├── about_page_candidates.csv # Manual URL config for Part 1
│   └── theme_taxonomy.yaml      # 10-theme taxonomy with LLM scoring instructions
├── src/
│   ├── common/
│   │   ├── io.py                # Cache paths, JSON/text I/O
│   │   ├── text_cleaning.py     # HTML → clean text (trafilatura + BS4 fallback)
│   │   ├── llm.py               # Anthropic API wrapper with retry + caching
│   │   └── utils.py             # Config loading, slugs, URL helpers
│   ├── part1_wayback/
│   │   ├── query_cdx.py         # Wayback CDX API queries (async)
│   │   ├── download_snapshots.py # Download HTML (async)
│   │   ├── extract_about_text.py # Clean text extraction
│   │   └── analyze_about_pages.py # LLM theme analysis → part1_dataset.csv
│   ├── part2_disclosures/
│   │   ├── fetch_sec_filings.py  # SEC EDGAR DEF 14A download
│   │   ├── extract_disclosure_text.py # Clean text from EDGAR filings
│   │   └── analyze_disclosures.py     # LLM theme analysis → part2_dataset.csv
│   ├── part3_index/
│   │   ├── construct_theme_vectors.py # Normalize theme scores into vectors
│   │   ├── compute_authenticity_index.py # Cosine similarity → authenticity score
│   │   └── validity_checks.py         # Face validity, sector trends, heatmaps
│   └── part4_exploratory/
│       └── sector_drift_analysis.py   # Sector drift + values volatility analysis
├── data/
│   ├── raw/
│   │   ├── wayback_cdx/         # CDX API responses (<ticker>_<year>.json)
│   │   ├── wayback_html/        # Raw archived HTML (<ticker>_<year>.html)
│   │   └── sec_filings/         # DEF 14A filings (<ticker>/<year>/)
│   ├── interim/
│   │   ├── part1/               # Clean text + LLM outputs for About Us pages
│   │   ├── part2/               # Clean text + LLM outputs for proxy statements
│   │   └── part3/               # Theme vectors
│   ├── processed/
│   │   ├── part1_dataset.csv    # Final Part 1 dataset (one row per company-year)
│   │   ├── part2_dataset.csv    # Final Part 2 dataset
│   │   └── part3_authenticity_index.csv  # Authenticity scores
│   └── outputs/
│       ├── part3_summary_statistics.csv
│       ├── part3_validity_checks.json
│       ├── part3_validity_plots/
│       ├── part4_sector_drift.csv
│       ├── part4_values_volatility.csv
│       └── part4_plots/
├── reports/
│   ├── part1_summary.md
│   ├── part2_summary.md
│   ├── part3_summary.md
│   └── part4_summary.md
└── notebooks/
    ├── 01_part1_qc.ipynb
    ├── 02_part2_qc.ipynb
    └── 03_index_analysis.ipynb
```

## Data Sources

### Part 1 — About Us / Mission / Values Pages
**Source:** Wayback Machine CDX API (`http://web.archive.org/cdx/search/cdx`)

**URL selection strategy:** Manual-first with heuristic fallback.
- `config/about_page_candidates.csv` contains 1–4 manually researched candidate URLs
  per company (primary, secondary, values page, mission page).
- For each company-year, the pipeline queries the CDX API against candidate URLs in order.
- If no manual candidate has an archived snapshot for a given year, the pipeline tries
  common path heuristics (`/about`, `/about-us`, `/our-values`, etc.).
- Every fallback case is logged with `selection_status = heuristic_fallback`.
- Missing snapshots are retained as rows with `selection_status = missing`.

**Time window:** One snapshot per year, 2016–2024 (9 time points × 50 companies = 450 target rows).
Snapshot selection prefers mid-year (July) to avoid holiday/maintenance periods.

**Text extraction:** Trafilatura (primary) with BeautifulSoup fallback. Navigation, footer,
boilerplate, and cookie notices are stripped. Any extraction yielding <30 words is flagged.

### Part 2 — Proxy Statements (DEF 14A)
**Source:** SEC EDGAR via `sec-edgar-downloader`

**Rationale for choosing proxy statements over ESG/sustainability reports:**
Proxy statements are filed annually by all public companies and accessible through a
single standardized API (EDGAR). ESG/sustainability reports are voluntary, inconsistently
available before 2019, and distributed across company websites with no standard format.
For a reproducible pipeline requiring consistent 2016–2024 coverage, proxy statements
are the practical choice. The tradeoff is that proxy language is more governance-focused;
values language must be inferred rather than read directly.

**Coverage gaps:** Some filings may not be found via EDGAR for a specific calendar year
if the company filed late or used a non-standard fiscal year. All gaps are documented
in `selection_status` columns.

## Theme Taxonomy

Ten sector-neutral themes used for both About Us and proxy analysis:

| Theme | Description |
|-------|-------------|
| `innovation` | R&D, technology, digital transformation, advancement |
| `customers_or_patients` | Customer/patient focus, outcomes, experience |
| `employees` | Workforce, talent, culture, well-being |
| `diversity_equity_inclusion` | DEI, representation, equal opportunity |
| `sustainability_environment` | Climate, carbon, ESG environmental pillar |
| `community_social_impact` | Philanthropy, community investment, giving back |
| `ethics_integrity` | Ethical conduct, integrity, transparency |
| `governance_accountability` | Board oversight, shareholder rights, risk management |
| `financial_performance` | Revenue, profit, shareholder returns |
| `safety_quality` | Product safety, quality assurance, worker safety |

Themes are scored 0–3 by Claude Haiku per document. The taxonomy is defined in
`config/theme_taxonomy.yaml` and included verbatim in all LLM prompts.

## Authenticity Index

**Operationalization:** Cosine similarity between the normalized theme score vector
from a company's About Us page and the normalized theme score vector from its proxy statement
for the same year.

```
score = cosine_similarity(about_theme_vector, proxy_theme_vector)
```

A score of 1.0 = perfect alignment (both documents emphasize the same themes in the same
proportions). A score near 0 = complete misalignment (documents emphasize different themes).

**Assumptions and limitations:**

1. *LLM scoring introduces measurement error.* Theme scores are judgments made by a
   language model, not human coders. Inter-rater reliability is not formally tested.
   Confidence is higher for clearly emphasized themes (scores 0 or 3) than borderline cases.

2. *Proxy statements are not values documents.* They are governance documents, so
   `governance_accountability` and `financial_performance` will naturally score high
   for almost all companies. This creates a floor effect that compresses variation in
   the authenticity score for those themes. Future work should weight themes by their
   expected variance across document types.

3. *Cosine similarity treats all themes equally.* A mismatch on `sustainability_environment`
   is treated the same as a mismatch on `financial_performance`, even though the former may
   be more societally significant. Theme weighting could be added but introduces subjectivity.

4. *The Wayback Machine is not an exhaustive archive.* Pages that were never crawled,
   behind authentication, or served dynamically may have no snapshot. Coverage is
   systematically worse for less-trafficked pages and earlier years.

## Caching and Restartability

Every intermediate artifact is cached to disk. If a run is interrupted, restart it with
`python run_pipeline.py --from <stage>` and it will skip already-completed work.

To force re-processing of a specific stage: `python run_pipeline.py <stage> --force`

## Reproducibility

- Python 3.11+
- All dependencies pinned in `requirements.txt`
- Random seeds: no stochastic components in the pipeline (LLM outputs are cached after
  first run, so results are deterministic from that point forward)
- The Anthropic API model version is pinned in each analysis script

## Known Limitations and What We Would Do Differently

1. **Human validation of URL selection.** The `about_page_candidates.csv` was populated
   via web research, but we did not manually verify that every URL resolves to a values/mission
   page rather than a generic corporate page. A second human reviewer would improve accuracy.

2. **Proxy statement section targeting.** Full proxy statements are long (50–200 pages).
   Our LLM analysis uses the first 5,000 words. A better approach would extract the
   specific sections most likely to contain values language (letter to shareholders,
   corporate responsibility section, DEI section) before analysis.

3. **No cross-company theme calibration.** LLM theme scores are absolute (0–3) not
   relative, so a company that uses moderate values language throughout might score 1 on
   every theme, which gives the same vector as a company with no values language. Z-scoring
   within-theme across companies would address this.

4. **Meta's Facebook-to-Meta rebrand.** For years 2016–2021, Meta operated as Facebook
   with facebook.com as its primary domain. The pipeline handles this via the secondary_about_url
   column, but snapshot availability may differ.
