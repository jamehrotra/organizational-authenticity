# Part 3 Summary — Organizational Authenticity Index

## What We Did

We constructed a measure of organizational authenticity — the degree of alignment between
what a company says it values (About Us page themes) and what its formal disclosures
suggest it actually prioritizes (proxy statement themes).

## Operationalization

**Authenticity = cosine_similarity(about_theme_vector, proxy_theme_vector)**

For each company-year:
1. Theme scores (0–3) from the About Us page analysis form a 10-dimensional vector.
2. Theme scores from the proxy statement analysis form a second 10-dimensional vector.
3. Both vectors are L2-normalized (divides by the Euclidean norm), so the score reflects
   the *shape* (relative emphasis pattern) not the *magnitude* (absolute intensity).
4. Cosine similarity between the two normalized vectors yields a score in [0, 1].

**Interpretation:**
- Score = 1.0: both documents emphasize the same themes in the same proportions.
- Score = 0.5: moderate alignment; some shared themes, some divergence.
- Score ≈ 0: the two documents emphasize entirely different themes.
- Score = NaN: one or both documents had no usable theme data.

**Why cosine similarity?**
Cosine similarity is appropriate here because we care about the *pattern* of theme
emphasis, not whether both documents happen to say a lot in general. A company with a
brief, focused values page and a concise proxy statement should be comparable to a company
with longer, more elaborate documents. L2 normalization achieves this.

## Distributional Properties

*(Fill in after running the pipeline.)*

| Statistic | Value |
|-----------|-------|
| Mean score | — |
| Median score | — |
| Std deviation | — |
| Min | — |
| Max | — |
| % with score > 0.7 | — |
| % with score < 0.3 | — |

**By sector:**

| Sector | Mean | Median | N |
|--------|------|--------|---|
| Technology | — | — | — |
| Financials | — | — | — |
| Healthcare | — | — | — |
| Consumer Discretionary | — | — | — |
| Energy | — | — | — |

## Validity Checks

**Face validity:** We examine whether companies intuitively expected to score high or low
actually do. For example, Johnson & Johnson (famous for its Credo, which explicitly
commits to patients, employees, communities, and shareholders in that order) should score
relatively high if its proxy emphasizes similar commitments. Conversely, companies whose
public-facing values language reads as marketing copy with little substantive content
should score lower.

*(Fill in with specific examples after running the pipeline.)*

**Temporal stability:** We examine year-over-year score volatility. If the measure is
meaningful rather than noisy, scores should change gradually for most companies, with sharp
changes corresponding to observable external events (e.g., a rebranding, a major scandal,
or a significant policy shift).

## Limitations

1. **LLM scoring is the largest source of measurement error.** All theme scores are
   model-generated judgments. The pipeline does not include human-coded validation data,
   so we cannot estimate inter-rater reliability. Findings should be interpreted as
   exploratory rather than confirmatory.

2. **Proxy statements systematically inflate governance and financial themes.** Because
   proxy statements are governance documents by design, `governance_accountability` and
   `financial_performance` will score high for almost every company regardless of authentic
   commitment. This means the authenticity score is most informative for the remaining
   eight themes. A weighted variant that down-weights these two themes is a natural extension.

3. **The 10-theme taxonomy may not capture all relevant dimensions.** Some sectors have
   distinctive values language that does not fit neatly into the taxonomy. Energy companies
   may emphasize "energy security" and "transition" in ways that fall between
   `sustainability_environment` and `financial_performance`. Healthcare companies may
   emphasize "access to medicines" which spans `customers_or_patients` and
   `community_social_impact`. A sector-specific taxonomy would yield finer distinctions.

4. **Selection bias in About Us snapshots.** Companies with better-maintained web presences
   and more content-rich About Us pages will have more informative theme vectors, creating
   a confound between web presence quality and measured authenticity.
