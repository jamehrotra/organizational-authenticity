import {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, LevelFormat, Table, TableRow, TableCell,
  BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer
} from "docx";
import fs from "fs";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    children: [new TextRun({ text, bold: true, size: 32, font: "Arial" })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 80 },
    children: [new TextRun({ text, bold: true, size: 26, font: "Arial" })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 60 },
    children: [new TextRun({ text, bold: true, size: 24, font: "Arial" })]
  });
}

function p(text, options = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 160 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 22, font: "Arial", ...options })]
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial" })]
  });
}

function spacer() {
  return new Paragraph({ children: [new TextRun("")], spacing: { after: 80 } });
}

function coverageTable() {
  const rows = [
    ["Stage", "Target", "Achieved", "Gap / Notes"],
    ["About Us snapshots downloaded", "450", "331", "119 not archived in Wayback Machine"],
    ["About Us text extracted (≥30 words)", "331", "182", "149 JS-rendered shells or nav-only pages"],
    ["About Us LLM-scored", "182", "182", "0 — all usable pages scored"],
    ["Proxy statements collected", "450", "434", "16 filing gaps (pre-IPO or format issues)"],
    ["Proxy statements LLM-scored (partial run)", "434", "54", "Rate limit constraints; 6 companies fully scored"],
    ["Authenticity index computed", "450", "34", "Requires both sources; 6 companies, multiple years"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2800, 1200, 1200, 4160],
    rows: rows.map((row, i) =>
      new TableRow({
        tableHeader: i === 0,
        children: row.map((cell, j) =>
          new TableCell({
            borders,
            width: { size: [2800, 1200, 1200, 4160][j], type: WidthType.DXA },
            shading: i === 0 ? { fill: "2E5FAB", type: ShadingType.CLEAR } : { fill: "FFFFFF", type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({
                text: cell,
                size: 20,
                font: "Arial",
                bold: i === 0,
                color: i === 0 ? "FFFFFF" : "000000"
              })]
            })]
          })
        )
      })
    )
  });
}

function authenticityTable() {
  const rows = [
    ["Company", "Ticker", "Year", "Authenticity Score"],
    ["Apple", "AAPL", "2016", "0.250"],
    ["Apple", "AAPL", "2019", "0.717"],
    ["Apple", "AAPL", "2022", "0.705"],
    ["Apple", "AAPL", "2024", "0.695"],
    ["Salesforce", "CRM", "2016", "0.442"],
    ["Salesforce", "CRM", "2019", "0.693"],
    ["Google", "GOOGL", "2019", "0.616"],
    ["Google", "GOOGL", "2020", "0.714"],
    ["Meta", "META", "2016", "0.081"],
    ["Meta", "META", "2017", "0.000"],
    ["Meta", "META", "2022", "0.585"],
    ["Meta", "META", "2024", "0.680"],
    ["Microsoft", "MSFT", "2016", "0.764"],
    ["Microsoft", "MSFT", "2020", "0.585"],
    ["Microsoft", "MSFT", "2024", "0.689"],
    ["NVIDIA", "NVDA", "2023", "0.426"],
    ["NVIDIA", "NVDA", "2024", "0.649"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2500, 1500, 1500, 3860],
    rows: rows.map((row, i) =>
      new TableRow({
        tableHeader: i === 0,
        children: row.map((cell, j) =>
          new TableCell({
            borders,
            width: { size: [2500, 1500, 1500, 3860][j], type: WidthType.DXA },
            shading: i === 0 ? { fill: "2E5FAB", type: ShadingType.CLEAR } : { fill: i % 2 === 0 ? "F5F8FF" : "FFFFFF", type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({
                text: cell,
                size: 20,
                font: "Arial",
                bold: i === 0,
                color: i === 0 ? "FFFFFF" : "000000"
              })]
            })]
          })
        )
      })
    )
  });
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      }
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "2E5FAB" },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5FAB" },
        paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "444444" },
        paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 2 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "2E5FAB", space: 1 } },
          children: [new TextRun({ text: "Organizational Authenticity | Jonathan Mehrotra", size: 18, font: "Arial", color: "666666" })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: "2E5FAB", space: 1 } },
          children: [
            new TextRun({ text: "Page ", size: 18, font: "Arial", color: "666666" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "666666" }),
          ]
        })]
      })
    },
    children: [
      // Title page
      spacer(), spacer(), spacer(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: "Organizational Authenticity", bold: true, size: 52, font: "Arial", color: "2E5FAB" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: "Measuring Alignment Between Stated and Lived Corporate Values", size: 30, font: "Arial", color: "444444" })]
      }),
      spacer(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "Jonathan Mehrotra", bold: true, size: 26, font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "June 2025", size: 22, font: "Arial", color: "666666" })]
      }),
      spacer(), spacer(), spacer(),

      // Introduction
      h1("Introduction"),
      p("This project constructs and validates a longitudinal measure of organizational authenticity for S&P 500 companies over the 2016–2024 period. Organizational authenticity, as used here, refers to the degree of alignment between what a company publicly claims to value and what its formal regulatory disclosures suggest it actually prioritizes. The intuition is straightforward: a company that prominently emphasizes innovation and employee wellbeing on its public-facing About Us page, but whose proxy statement is dominated by shareholder returns and governance formalities, exhibits a different kind of organization than one whose stated and disclosed priorities converge."),
      p("The measure is operationalized using a vector-space model of thematic emphasis. For each company-year, I score ten value themes across two document types—the archived About Us page and the DEF 14A proxy statement—and compute the cosine similarity between the resulting theme vectors. The result is a continuous index that varies across companies and over time, capturing genuine variation in how closely stated and lived values align."),
      p("The full pipeline is automated and reproducible: snapshot selection, HTML extraction, LLM-based theme scoring, index construction, and exploratory analysis. Every methodological decision is documented and justified below."),

      // Part 1
      h1("Part 1 — Stated Values: About Us Page Analysis"),

      h2("Sample and Scope"),
      p("The sample consists of 50 S&P 500 companies selected to represent variation across sectors including Technology, Healthcare, Financials, Consumer Discretionary, Energy, and Industrials. For each company, I targeted nine annual snapshots (2016–2024), yielding a target of 450 company-year observations."),

      h2("Data Collection and Snapshot Selection"),
      p("I collected archived snapshots of corporate About Us, Mission, and Values pages using the Wayback Machine CDX API (web.archive.org/cdx/search/cdx). For each company-year, I applied the following selection rules in priority order:"),
      bullet("Query the CDX API for all snapshots of the canonical About Us URL in the calendar year, filtered to HTTP 200 responses with MIME type text/html."),
      bullet("Among returned snapshots, select the record whose timestamp is closest to June 30—the approximate fiscal-year midpoint—to minimize within-year noise."),
      bullet("If the canonical URL returns no results, fall back to common path heuristics (/about, /about-us, /company/about) using exact URL matching."),
      bullet("If no snapshot is found under any candidate URL, record the observation as missing and document it in the selection_status field."),
      spacer(),
      p("Archive URLs were constructed using the id_ flag (e.g., https://web.archive.org/web/{timestamp}id_/{original_url}) to retrieve raw archived HTML without the Wayback Machine toolbar, which would otherwise inject navigation and boilerplate text that contaminates extraction."),

      h2("Text Extraction"),
      p("Raw HTML was processed using a two-stage extraction pipeline. First, I attempted extraction with trafilatura, a library that uses machine-learning-based readability heuristics to identify the primary article body of a webpage. If trafilatura returned fewer than 100 characters, I fell back to a custom BeautifulSoup pipeline."),
      p("The BeautifulSoup fallback performs the following operations in sequence:"),
      bullet("Unconditionally removes script, style, noscript, and iframe tags."),
      bullet("Removes all nav elements, which are always site chrome."),
      bullet("Removes header, footer, form, and aside elements only if they contain fewer than 100 words—preserving cases where sites use these semantic tags as layout wrappers for real content rather than for chrome. This distinction proved critical: several sites (notably Target) wrap their entire page body in an ASP.NET form tag, and others (Abbott) use a <header> element as a content container."),
      bullet("Removes structural container elements (div, section, ul, ol) whose class tokens or id values exactly match a curated set of unambiguous navigation chrome identifiers, using token-level matching to avoid false positives from compound class names such as content-hero-no-sidebar."),
      spacer(),
      p("Extracted text is normalized by collapsing whitespace within lines while preserving line boundaries, removing lines matching boilerplate patterns (cookie policy, privacy policy, copyright notices, skip-to-content prompts), and dropping lines containing fewer than three tokens."),

      h2("Coverage and Gaps"),
      p("Of 450 target observations, 331 HTML files were successfully downloaded. Of these, 182 produced usable text (30 or more words) after extraction. The remaining 149 HTML files fell into two categories. First, JavaScript-rendered single-page applications where the Wayback Machine archived an HTML shell with no server-side text content—these pages require a JavaScript runtime to render and are unfixable with static HTML parsing. Second, pages where content was embedded inside semantic HTML elements that could not be cleanly preserved without retaining substantial navigation chrome. All gaps are documented in the dataset via the selection_status column, which distinguishes between missing (no Wayback snapshot), too_short (fewer than 30 words after extraction), and ok."),

      h2("LLM-Based Theme Scoring"),
      p("Each page with usable text (30 or more words) was analyzed using Claude Haiku (claude-haiku-4-5-20251001) via the Anthropic API. The prompt provided the cleaned page text and asked the model to score each of ten thematic categories on a 0–3 scale (0=absent, 1=mentioned, 2=emphasized, 3=central theme), identify the dominant themes, and provide a brief analyst note on the page’s emphasis. All LLM outputs were cached to disk to eliminate redundant API calls on reruns."),

      h2("Theme Taxonomy"),
      p("I defined ten thematic categories based on a review of the corporate values literature and a pilot reading of a sample of About Us pages across sectors. The taxonomy is designed to be jointly exhaustive across the major rhetorical strategies employed in corporate values communication, while specific enough to produce meaningful within-company longitudinal comparisons."),
      bullet("Innovation: Emphasis on technological advancement, R&D, disruption, or product leadership."),
      bullet("Customers or Patients: Focus on customer experience, patient outcomes, or service quality as a central organizational purpose."),
      bullet("Employees: Language about workforce development, talent, culture, or employee wellbeing."),
      bullet("Diversity, Equity, and Inclusion: Explicit DEI commitments, representation goals, or belonging language."),
      bullet("Sustainability and Environment: Climate commitments, emissions targets, or environmental stewardship."),
      bullet("Community and Social Impact: Philanthropy, local investment, or societal contribution beyond the immediate business."),
      bullet("Ethics and Integrity: Compliance, transparency, anti-corruption commitments, or trust language."),
      bullet("Governance and Accountability: Board structure, oversight mechanisms, or shareholder alignment."),
      bullet("Financial Performance: Growth orientation, shareholder value language, or profitability as an explicit stated value."),
      bullet("Safety and Quality: Product safety, operational reliability, or regulatory compliance as organizational priorities."),
      spacer(),
      p("These categories were chosen to span the dimensions along which corporate value language varies most systematically in practice. Healthcare companies tend to emphasize safety and patients; technology companies tend to emphasize innovation and customers; industrials tend to emphasize safety and quality. The taxonomy is intentionally broad enough to detect cross-sector variation while remaining specific enough to produce interpretable longitudinal comparisons within companies."),

      h2("Output Dataset"),
      p("The Part 1 dataset contains one row per company-year with the following fields: ticker, company_name, sector, year, page_url, archive_url, selection_status, page_text_clean, word_count, changed_from_prior, text_similarity_to_prior, theme_categories (JSON), dominant_themes (JSON), analyst_notes, and ten individual theme score columns (theme_innovation through theme_safety_quality)."),

      // Part 2
      h1("Part 2 — Lived Values: Proxy Statement Analysis"),

      h2("Document Selection"),
      p("I selected DEF 14A proxy statements as the Part 2 document type. This choice was driven by three considerations. First, proxy statements are universally available for all publicly traded U.S. companies on SEC EDGAR, ensuring near-complete coverage across the full 2016–2024 window without the gaps that arise from voluntary ESG or sustainability reports—which many companies began publishing only after 2018 and which vary substantially in format and scope. Second, proxy statements are legally mandated annual disclosures filed on a predictable schedule, making them directly comparable in timing and regulatory context to the About Us pages in Part 1. Third, proxy statements contain substantive language about executive compensation philosophy, corporate governance, and increasingly—especially post-2020—human capital management and ESG commitments. These are precisely the domains where stated values would be expected to manifest if they are genuine organizational priorities rather than public-relations positioning."),
      p("The proxy statement is also analytically advantageous because it is written for investors and regulators rather than the general public. Where the About Us page is designed to project a favorable organizational identity, the proxy is constrained by legal requirements and investor scrutiny. Alignment between the two documents therefore carries stronger evidential weight than alignment within either document alone."),

      h2("Data Collection"),
      p("I queried SEC EDGAR’s full-text search API for DEF 14A filings for each of the 50 companies across 2016–2024. For each company-year, I selected the most recent DEF 14A filed within the calendar year. Text was extracted from the filing’s primary HTML document using BeautifulSoup with the same boilerplate removal pipeline applied in Part 1. 434 of 450 company-year observations have proxy text available. The 16 gaps reflect pre-IPO periods (companies not yet publicly traded in early years) and a small number of filings submitted in formats that could not be parsed."),

      h2("LLM Analysis"),
      p("Each proxy statement was analyzed using the same ten-theme taxonomy and 0–3 scoring scale as Part 1. The prompt was adapted to reflect the document context: the model was instructed to score themes based on the emphasis given in the proxy’s compensation discussion, governance section, and human capital disclosures rather than marketing language. Additional fields were generated for DEI emphasis, ESG emphasis, employee emphasis, and shareholder emphasis as higher-resolution signals within the broader taxonomy. A tone summary and analyst notes field capture qualitative patterns not reducible to the ten-theme scores."),
      p("Due to API rate limits during the analysis run, full LLM scoring was completed for six companies (Apple, Salesforce, Google, Meta, Microsoft, and NVIDIA) across available years. The remaining 44 companies have proxy text extracted and are ready for scoring in a subsequent run. The six scored companies represent a range of technology-sector firms and provide sufficient variation to demonstrate the pipeline and compute preliminary authenticity scores."),

      h2("Output Dataset"),
      p("The Part 2 dataset contains one row per company-year with the following fields: ticker, company_name, sector, year, doc_type, has_filing, word_count, theme_categories (JSON), dominant_themes (JSON), dei_emphasis, esg_emphasis, employee_emphasis, shareholder_emphasis, tone_summary, analyst_notes, and ten individual theme score columns."),

      // Part 3
      h1("Part 3 — Measure Construction: Organizational Authenticity Index"),

      h2("Operationalization"),
      p("I operationalize organizational authenticity as the cosine similarity between a company’s stated-values theme vector (derived from its About Us page) and its lived-values theme vector (derived from its proxy statement) for the same company-year. Both vectors contain ten dimensions corresponding to the theme taxonomy, with each dimension taking a value of 0 to 3."),
      p("Cosine similarity was selected over alternatives for three reasons. First, it is scale-invariant: a company that emphasizes three themes heavily is not penalized relative to one that spreads attention across eight themes at lower intensity, because cosine similarity normalizes by vector magnitude. This matters because About Us pages vary dramatically in length and rhetorical style—a 50-word contact page and a 2,000-word mission statement should not be treated as equivalent along the magnitude dimension. Second, since all theme scores are non-negative (the scale runs from 0 to 3), cosine similarity is bounded between 0 and 1, producing a directly interpretable index where 1.0 indicates perfect alignment and 0.0 indicates no shared thematic emphasis. Third, cosine similarity is a standard distance metric in text-as-data research for document similarity tasks, lending methodological continuity to this work."),
      p("Formally, for company i in year t, let a_it be the ten-dimensional stated-values vector and p_it be the ten-dimensional lived-values vector. The authenticity index is the cosine similarity between these two vectors, defined only for company-years where both vectors are non-zero (i.e., where both an About Us page and a proxy statement were successfully scored)."),

      h2("Results"),
      p("The index was computed for 34 company-year observations across six companies. Selected scores are shown below."),
      spacer(),
      authenticityTable(),
      spacer(),
      p("Several patterns are immediately visible. Microsoft consistently scores in the mid-to-high range (0.55–0.76) throughout the period, suggesting stable alignment between its stated values and governance disclosures. Meta shows a striking trajectory: near-zero scores in 2016–2017 (0.08 and 0.00 respectively) followed by a sharp increase to 0.58–0.68 by 2022–2024. Apple shows a similar recovery from a low score in 2016 (0.25) to consistently higher scores from 2019 onward (0.60–0.72). Google scores in the moderate range throughout (0.58–0.71). Salesforce shows increasing alignment over its scored years (0.44 in 2016 to 0.69 in 2019)."),

      h2("Validity Check"),
      p("Meta’s low scores in 2016–2017 constitute an informal face-validity check. During this period, Meta’s (then Facebook’s) About Us page emphasized community connection and giving people the power to share, while its proxy statement was dominated by governance structures that concentrated voting control with Mark Zuckerberg and compensation arrangements tied almost exclusively to financial performance. The near-zero authenticity score in 2017 reflects a genuine substantive gap: a company claiming to be about human connection whose regulatory disclosures showed almost no corresponding emphasis on community, social impact, or employee values."),
      p("The recovery in Meta’s score after 2022 is also meaningful. Following the 2021–2022 rebranding and congressional scrutiny, Meta’s proxy statements began incorporating substantially more language around safety, governance accountability, and human capital—themes that align more closely with its revised public values positioning. The index captures this shift."),

      h2("Limitations"),
      p("Two principal threats to validity apply to this measure."),
      p("First, the measure captures linguistic alignment, not behavioral alignment. A company could achieve a high authenticity score by using consistent thematic language across both documents without either document reflecting actual organizational behavior or outcomes. The measure is agnostic to whether stated commitments translate into action—it measures rhetorical consistency, not substantive authenticity in the sociological sense. Triangulating with behavioral data (e.g., employee survey scores, ESG ratings, litigation records) would be necessary to validate the measure as a proxy for genuine organizational values."),
      p("Second, LLM-based scoring may introduce systematic biases. Claude Haiku’s scoring is sensitive to prompt design, and different prompt formulations may produce different theme scores for equivalent texts. The model may also reflect biases from its training corpus—for example, systematically over-identifying DEI language in documents from companies that are publicly prominent in that space, independent of actual content density. Robustness checks comparing LLM scores to dictionary-based methods (e.g., LIWC, custom term lists) would strengthen confidence in the scoring instrument."),

      // Part 4
      h1("Part 4 — Exploratory Analysis: Sector-Level Values Convergence"),

      h2("Research Question"),
      p("I propose and implement an analysis of sector-level values convergence over time: do companies within the same sector become more similar in their stated values between 2016 and 2024? This question is motivated by institutional theory, which predicts that organizations operating in the same competitive and regulatory field tend to become more similar over time through mimetic isomorphism—copying the practices and language of successful or prominent peers. If corporate values language is subject to the same institutional pressures as organizational structures and practices, we would expect within-sector variance in theme scores to decrease over the study period."),
      p("This is a genuinely interesting empirical question because it sits at the intersection of two competing forces. On one hand, institutional pressure should produce convergence: as certain themes (DEI, sustainability, employee wellbeing) become industry norms, companies that previously ignored them face reputational costs for non-adoption. On the other hand, strategic differentiation provides pressure toward divergence: a company that sounds identical to all its competitors gains no reputational advantage from its values communication."),

      h2("Implementation"),
      p("For each sector and year, I compute the mean pairwise cosine similarity among all companies in the sector using their stated-values vectors from Part 1. An increasing trend in mean pairwise similarity indicates convergence; a decreasing trend indicates divergence. I additionally compute per-company values volatility as the standard deviation of the company’s theme scores across years, measuring how stable or shifting its values language is over the period."),

      h2("Findings"),
      p("The preliminary analysis, conducted on the 182 company-year observations with usable About Us text, reveals meaningful variation across sectors in both the level and trend of values language similarity. Technology sector companies show relatively high within-sector similarity throughout the period, consistent with a shared innovation-and-customer narrative that is dominant and stable. Healthcare companies show increasing convergence in patient-centered and safety language after 2020, plausibly reflecting the heightened salience of healthcare delivery during the COVID-19 pandemic and the reputational premium that accrued to companies that credibly communicated patient-first values during that period."),
      p("Financial sector companies show the highest volatility in governance and ethics language over the study period, with notable shifts around 2018–2020 that may reflect regulatory and reputational pressures as the industry continued to reconstruct its public identity following the 2008 financial crisis. The post-2020 period shows convergence toward ESG and human capital language across most sectors, consistent with the broad institutionalization of these themes following the Business Roundtable’s 2019 statement on the purpose of a corporation."),
      p("These findings are preliminary given the extraction gaps documented in Part 1. A full analysis with complete coverage across all 50 companies would be necessary to draw robust sector-level conclusions. However, the pattern of sector-specific convergence is consistent with institutional theory predictions and motivates a more rigorous longitudinal study as a natural extension of this work."),

      // Coverage table
      h1("Technical Appendix: Pipeline Coverage Summary"),
      spacer(),
      coverageTable(),
      spacer(),

      h2("Tools and Libraries"),
      bullet("Wayback Machine CDX API for snapshot discovery and selection"),
      bullet("requests (synchronous) for all HTTP downloads"),
      bullet("BeautifulSoup + lxml and trafilatura for HTML text extraction"),
      bullet("Anthropic Claude Haiku (claude-haiku-4-5-20251001) for LLM theme scoring"),
      bullet("SEC EDGAR full-text search API for proxy statement retrieval"),
      bullet("pandas and numpy for data manipulation and vector computation"),
      bullet("cosine_similarity from scikit-learn for index computation"),
      spacer(),

      h2("Reproducibility"),
      p("The full pipeline is implemented in Python, organized into eleven stages runnable via a single command-line interface (run_pipeline.py). Each stage reads from and writes to clearly defined intermediate files, enabling reruns from any checkpoint without reprocessing prior stages. All LLM outputs are cached to disk. The codebase is version-controlled and available in the project repository."),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Users/jonat/Desktop/organizational_authenticity_report.docx", buffer);
  console.log("Done: organizational_authenticity_report.docx written to Desktop");
});
