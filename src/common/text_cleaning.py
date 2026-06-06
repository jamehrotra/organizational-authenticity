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
        if extracted and len(extracted.strip()) > 200:
            return _normalize(extracted)

    return _bs4_fallback(html)


def _bs4_fallback(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "header", "footer",
                      "aside", "noscript", "iframe", "form"]):
        tag.decompose()

    for tag in soup.find_all(True):
        try:
            attrs = tag.attrs if tag.attrs is not None else {}
            raw_class = attrs.get("class", [])
            if isinstance(raw_class, str):
                raw_class = raw_class.split()
            elif not isinstance(raw_class, (list, tuple)):
                raw_class = []
            classes = " ".join(str(c) for c in raw_class)

            raw_id = attrs.get("id", "")
            _id = raw_id if isinstance(raw_id, str) else str(raw_id) if raw_id else ""

            skip_signals = ["nav", "menu", "footer", "sidebar", "cookie",
                            "banner", "popup", "modal", "breadcrumb"]
            if any(s in classes.lower() or s in _id.lower() for s in skip_signals):
                tag.decompose()
        except Exception:
            pass

    text = soup.get_text(separator=" ", strip=True)
    return _normalize(text)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"\s+", " ", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [l for l in lines if not BOILERPLATE_RE.search(l)]
    lines = [l for l in lines if len(l) > 20]
    return "\n".join(lines).strip()


def word_count(text: str) -> int:
    return len(text.split())
