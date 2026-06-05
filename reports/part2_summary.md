# Part 2 Summary — Lived Values: Proxy Statement Analysis

## What We Did

We collected DEF 14A (annual proxy statement) filings for all 50 companies from
SEC EDGAR for the years 2016–2024, using the `sec-edgar-downloader` Python library.
Proxy statements were chosen over ESG/sustainability reports for the following reasons:

1. **Consistent coverage:** All public companies must file a proxy statement annually
   with the SEC. ESG reports are voluntary and coverage before 2019 is sparse.
2. **Single source of truth:** EDGAR provides a standardized programmatic API.
   ESG reports are distributed across company websites in varying formats.
3. **Reproducibility:** Anyone can reproduce this analysis by querying EDGAR with the
   same parameters. ESG report sourcing requires manual effort and judgment.

The tradeoff is that proxy statements are primarily governance documents. Values language
must be inferred from sections like the letter to shareholders, corporate responsibility
narrative, and DEI disclosures rather than being stated explicitly.

**Text extraction:** Raw EDGAR filings (SGML/HTML) were cleaned by stripping markup,
EDGAR headers, and decorative boilerplate. The first 5,000 words were used for LLM
analysis to focus on the substantive early sections of each filing.

**LLM analysis:** Cleaned proxy text was scored against the same 10-theme taxonomy
as Part 1, using Claude Haiku. Additional emphasis scores were computed for DEI language,
ESG/environmental language, employee language, and shareholder language.

## Assumptions

- Filing date proximity: EDGAR filings are searched by calendar year of submission.
  Companies with non-December fiscal year ends may have proxy statements that reflect
  the prior fiscal year. This introduces up to a 12-month offset for some company-years.
- The first 5,000 words of a proxy statement are representative of its thematic emphasis.
  This may underrepresent content in later sections (e.g., detailed compensation tables,
  specific ESG metrics), but captures the narrative framing that is most analytically relevant.
- Theme scoring from a governance document is inherently noisier than scoring an About Us
  page, because proxy statements discuss values instrumentally (e.g., "our sustainability
  commitments support long-term shareholder value") rather than declaratively.

## Coverage and Gaps

*(Fill in with actual numbers after running the pipeline.)*

| Status | Count | % of 450 |
|--------|-------|----------|
| Filing found | — | — |
| No filing found | — | — |
| Extraction error | — | — |

Expected gaps:
- **BRK.B (Berkshire Hathaway):** Uses a non-standard filing structure.
- Companies with unusual fiscal years may have gaps in a specific calendar year.

## Key Findings

*(Fill in after running the pipeline.)*

## What We Would Do Differently

1. **Section-level extraction:** Rather than using the first 5,000 words, parse the
   proxy statement to extract specific sections: letter to shareholders, corporate
   governance narrative, and any standalone DEI or ESG section. This would reduce
   the influence of boilerplate table-of-contents text in early pages.
2. **Add sustainability reports for 2019–2024** as a supplementary source for companies
   with consistent ESG report publication. This would provide richer values-alignment signal.
3. **Fiscal year alignment:** Align proxy statement year to the fiscal year covered
   rather than the calendar year filed, to improve temporal alignment with Part 1 snapshots.
