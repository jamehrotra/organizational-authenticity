"""Clean raw HTML into plain body text, stripping nav/footer/boilerplate."""

import re
import unicodedata

from bs4 import BeautifulSoup

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

BOILERPLATE_PATTERNS = [
    r"cookie\s+policy",
    r"privacy\s+policy",
    r"terms\s+of\s+(use|service)",
    r"all\s+rights\s+reserved",
    r"copyright\s+©",
    r"skip\s+to\s+(main\s+)?content",
    r"©\s*\d{4}",
]

BOILERPLATE_RE = re.compile(
    "|".join(BOILERPLATE_PATTERNS), re.IGNORECASE
)

# Only check these structural container types for nav/chrome signals.
# Limiting to containers avoids accidentally removing content-bearing elements
# (spans, paragraphs, headings) whose class names happen to contain "nav".
_CONTAINER_TAGS = {"div", "section", "ul", "ol", "aside", "widget"}

# Require token-level matches to avoid false positives like "navigation-content"
# matching a content div. These are unambiguous navigation/chrome identifiers.
_NAV_SIGNAL_RE = re.compile(
    r"\b(sitenav|site-nav|globalnav|global-nav|mainnav|main-nav"
    r"|topnav|top-nav|breadcrumb|sidebar|cookie-banner|cookie-bar"
    r"|popup|modal-overlay|newsletter-signup)\b",
    re.IGNORECASE,
)


def clean_html(html: str, url: str = "") -> str:
    """Extract visible body text from HTML, removing nav/footer/boilerplate."""
    if not html:
        return ""

    if HAS_TRAFILATURA:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
        )
        if extracted and len(extracted.strip()) > 100:
            return _normalize(extracted)

    return _bs4_fallback(html)


def _bs4_fallback(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Remove clearly non-content semantic elements unconditionally.
    for tag in soup(["script", "style", "nav", "header", "footer",
                      "aside", "noscript", "iframe", "form"]):
        tag.decompose()

    # Remove structural containers whose class/id unambiguously marks them as
    # navigation chrome. Only check container-type tags (div, section, ul, ol)
    # to avoid nuking content elements that share a class name fragment.
    for tag in soup.find_all(_CONTAINER_TAGS):
        try:
            attrs = tag.attrs if tag.attrs is not None else {}

            raw_class = attrs.get("class", [])
            if isinstance(raw_class, str):
                raw_class = raw_class.split()
            elif not isinstance(raw_class, (list, tuple)):
                raw_class = []
            classes = " ".join(str(c) for c in raw_class)

            raw_id = attrs.get("id", "")
            elem_id = raw_id if isinstance(raw_id, str) else (str(raw_id) if raw_id else "")

            combined = f"{classes} {elem_id}"
            if _NAV_SIGNAL_RE.search(combined):
                tag.decompose()
        except Exception:
            pass

    # Use newline separator so get_text produces multi-line output.
    # _normalize then filters line by line rather than on one giant blob.
    text = soup.get_text(separator="\n", strip=True)
    return _normalize(text)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    # Collapse spaces/tabs within lines but preserve newline boundaries.
    text = re.sub(r"[^\S\n]+", " ", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [l for l in lines if not BOILERPLATE_RE.search(l)]
    # Drop lines that are only 1-2 tokens (menu labels, lone headings).
    lines = [l for l in lines if len(l.split()) >= 3]
    return "\n".join(lines).strip()


def word_count(text: str) -> int:
    return len(text.split())
