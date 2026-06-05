# Part 4 Summary — Exploratory Analysis

## Question

Do some sectors become more or less aligned over time? And do companies that
change their stated values language the most also show corresponding shifts in
their formal disclosure priorities — or do they rebrand their public messaging
without changing what they actually emphasize?

## Why This Is Interesting

The period 2016–2024 spans several significant inflection points in corporate values
discourse: the Business Roundtable's 2019 Statement on the Purpose of a Corporation
(which shifted from shareholder primacy to stakeholder capitalism); the COVID-19 pandemic
(which elevated employee well-being and community language); and the ESG backlash of
2022–2024 (which saw some companies quietly reduce DEI and sustainability language). If
authenticity is meaningful, we should see sectors respond differently to these shocks,
and companies that genuinely shifted their priorities should show correlated movement in
both stated and lived values.

## Analysis A: Sector Drift

We plot the mean authenticity score for each of the five sectors from 2016 to 2024,
with 95% confidence intervals. We then fit a simple OLS regression of score on year
within each sector to test for a statistically significant linear trend.

**Hypotheses:**
- Technology and Healthcare companies may show increasing authenticity if their
  About Us pages were refreshed to align more closely with ESG/DEI language that
  also appears in proxy statements.
- Energy companies may show a decline after 2019 if they adopted sustainability
  language on their public-facing pages without a corresponding shift in proxy priorities.
- Financial companies may show low baseline authenticity throughout, because their
  public values language (service, trust, innovation) diverges from proxy language
  (risk management, capital allocation, regulatory compliance).

*(Fill in with actual findings after running the pipeline.)*

## Analysis B: Values Volatility

For each company, we compute:
- **About page volatility:** Average year-over-year text dissimilarity of the About Us page
  (higher = company changed its stated values language more).
- **Proxy score volatility:** Average year-over-year absolute change in authenticity score
  (higher = company's alignment pattern shifted more).

We then test whether these two volatility measures are correlated: do companies that
rebrand their public values also show shifts in formal disclosure priorities?

If the correlation is strong, it suggests values rebrands tend to be genuine (both
stated and lived values shift together). If the correlation is weak or negative, it
suggests companies frequently update their public messaging without changing formal
disclosure priorities — a pattern consistent with "values washing."

*(Fill in with actual findings after running the pipeline.)*

## What We Would Do Differently

1. **Event study design:** Rather than a linear trend test, use a difference-in-differences
   design around specific events (the 2019 Business Roundtable statement; COVID-19 onset
   in Q1 2020; the 2022 ESG backlash) to estimate whether authenticity scores changed
   around those dates more than expected by baseline trend.
2. **Text-level analysis of specific themes:** For the volatility analysis, instead of
   measuring total text dissimilarity, track volatility within specific themes (e.g., only
   DEI language, only sustainability language) to identify which value categories drive rebranding.
3. **External validation:** Cross-reference the authenticity index with third-party ESG ratings
   (MSCI, Sustainalytics) or workforce sentiment data (Glassdoor employer ratings) to test
   whether our measure captures something real about organizational culture.
