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

# Structural container tags we inspect for nav/chrome signals.
_CONTAINER_TAGS = {"div", "section", "ul", "ol", "aside", "widget"}

# Class tokens or id values that unambiguously identify nav/chrome containers.
# Checked against individual class tokens and the full id string so that
# compound class names like "content-hero-no-sidebar" don't false-positive.
_NAV_CLASS_TOKENS = {
    "sitenav", "site-nav", "globalnav", "global-nav",
    "mainnav", "main-nav", "topnav", "top-nav",
    "breadcrumb", "breadcrumbs",
    "sidebar", "side-bar",
    "cookie-banner", "cookie-bar", "cookie-notice",
    "popup", "modal-overlay", "newsletter-signup",
}

# For ids we still use a regex since ids are a single value (no compound issue).
_NAV_ID_RE = re.compile(
    r"^(sitenav|site.nav|globalnav|global.nav|mainnav|main.nav"
    r"|topnav|top.nav|breadcrumb|breadcrumbs|sidebar|side.bar"
    r"|cookie.banner|cookie.bar|cookie.notice"
    r"|popup|modal.overlay|newsletter.signup)$",
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

    # Remove non-content elements unconditionally.
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    # Remove nav unconditionally — it is always site chrome.
    for tag in soup.find_all("nav"):
        tag.decompose()

    # Remove header/footer/form/aside only if they look like site chrome
    # (small word count). Some sites wrap page content in <header> or <form>.
    for tagname in ["header", "footer", "form", "aside"]:
        for tag in soup.find_all(tagname):
            if len(tag.get_text().split()) < 100:
                tag.decompose()

    # Remove structural containers whose class tokens or id exactly match
    # known nav/chrome identifiers. Check class tokens individually so that
    # compound names like "content-hero-no-sidebar" don't false-positive.
    for tag in soup.find_all(_CONTAINER_TAGS):
        try:
            attrs = tag.attrs if tag.attrs is not None else {}

            raw_class = attrs.get("class", [])
            if isinstance(raw_class, str):
                raw_class = raw_class.split()
            elif not isinstance(raw_class, (list, tuple)):
                raw_class = []
            class_tokens = {str(c).lower() for c in raw_class}

            elem_id = attrs.get("id", "") or ""
            if not isinstance(elem_id, str):
                elem_id = str(elem_id)

            if class_tokens & _NAV_CLASS_TOKENS or _NAV_ID_RE.match(elem_id):
                tag.decompose()
        except Exception:
            pass

    # Newline separator so _normalize can filter line by line.
    text = soup.get_text(separator="\n", strip=True)
    return _normalize(text)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [l for l in lines if not BOILERPLATE_RE.search(l)]
    # Drop lines that are only 1-2 tokens (menu labels, lone words).
    lines = [l for l in lines if len(l.split()) >= 3]
    return "\n".join(lines).strip()


def word_count(text: str) -> int:
    return len(text.split())
