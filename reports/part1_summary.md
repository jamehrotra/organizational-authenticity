# Part 1 Summary — Stated Values: About Us Page Analysis

## What We Did

We collected archived snapshots of the corporate About Us, Mission, or Values page for
50 S&P 500 companies across 9 years (2016–2024), targeting one snapshot per company-year
(450 total). Data was sourced from the Wayback Machine CDX API.

**URL selection:** For each company, we manually researched and documented 1–4 candidate
URLs (primary about page, backup page, dedicated values page, dedicated mission page).
The pipeline queried the CDX API against these candidates in priority order. If no manual
candidate had a valid archived snapshot for a given year, the pipeline tried 14 common
path heuristics (`/about`, `/about-us`, `/our-values`, etc.). Every fallback and every
missing case is logged with an explanatory `selection_status` field.

**Text extraction:** Raw HTML was cleaned using Trafilatura (with BeautifulSoup as fallback),
stripping navigation, footers, cookie notices, and boilerplate. Extractions yielding fewer
than 30 words were flagged.

**LLM analysis:** Cleaned text was scored against a 10-theme taxonomy by Claude Haiku,
using a 0–3 scale per theme. The model also identified dominant themes and noted notable
linguistic patterns.

## Assumptions

- One snapshot per year is sufficient to capture the company's stated values posture for
  that year. We preferred mid-year snapshots (closest to July) to avoid holiday periods.
- Pages with fewer than 30 words after cleaning are treated as effectively empty and
  excluded from LLM analysis (but retained in the dataset with a flag).
- The 10 themes in `config/theme_taxonomy.yaml` are sufficient to characterize corporate
  values language across all five sectors. This is a simplification; some sector-specific
  language (e.g., "patient safety" in healthcare, "energy transition" in energy) is
  captured by the closest theme rather than a dedicated category.

## Coverage and Gaps

*(Fill in with actual numbers after running the pipeline.)*

| Status | Count | % of 450 |
|--------|-------|----------|
| Manual primary | — | — |
| Manual backup | — | — |
| Heuristic fallback | — | — |
| Missing | — | — |

Notable gaps (expected based on web research):
- **Berkshire Hathaway (BRK.B):** Minimal web presence; homepage is effectively the
  about page. Expect sparse text and possible missing snapshots for early years.
- **Broadcom (AVGO):** B2B company with limited public-facing values language.
- **Intel:** Long, deeply nested URL paths that may not be consistently archived.

## Key Findings

*(Fill in after running the pipeline.)*

## What We Would Do Differently

1. **Human validation pass** on URL selection: have a second researcher verify that
   each selected URL resolves to a genuine values/mission page, not a generic corporate page.
2. **Multiple snapshots per year** as a robustness check: compare January, July, and
   December snapshots to catch mid-year page updates.
3. **Named entity and linguistic shift analysis:** in addition to theme scoring, track
   specific recurring phrases (e.g., "stakeholder capitalism," "net zero," "belonging")
   across years to detect emerging language trends.
