import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

STRONG = ["delete", "deletion", "supprim", "suppression", "close-account", "close account",
          "close your account", "close-your-account", "closing your account",
          "closing-your-account", "closeaccount", "fermer mon compte", "fermer le compte",
          "fermer votre compte", "fermer ton compte", "fermeture du compte", "fermeture de compte",
          "fermeture de votre compte", "cloturer", "desactiv", "deactivat", "erase", "effacement",
          "remove account", "account-removal", "data-deletion", "loschen"]
ACCOUNT = ["account", "compte", "profile", "profil", "settings", "parametres", "my-data"]
PRIVACY = ["privacy", "confidentialite", "gdpr", "rgpd", "donnees personnelles",
           "personal data", "personal-data", "data-protection", "dsar"]
NOISE = ["blog", "news", "careers", "jobs", "press", "cookie", "login", "signin", "sign-in",
         "signup", "sign-up", "register", "inscription", ".pdf", ".jpg", ".png"]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_HINTS = ["dpo", "privacy", "rgpd", "gdpr", "dataprotection", "data-protection",
               "confidentialite", "donnees", "datenschutz"]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._label = ""
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            a = dict(attrs)
            self._href = a.get("href") or ""
            self._label = a.get("aria-label") or a.get("title") or ""
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join(" ".join(self._text).split()) or self._label.strip()
            self.links.append((self._href, text))
            self._href = None


def extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    parser = _LinkParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    out = []
    for href, text in parser.links:
        href = href.strip()
        if not href or href.startswith(("#", "javascript:", "tel:")):
            continue
        out.append((href if href.startswith("mailto:") else urljoin(base_url, href), text))
    return out


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def score_link(url: str, text: str) -> float:
    parts = urlsplit(url)
    hay = fold(f"{parts.path} {parts.query} {text}").replace("_", "-")
    strong = any(k in hay for k in STRONG)
    account = any(k in hay for k in ACCOUNT)
    privacy = any(k in hay for k in PRIVACY)
    noise = any(k in hay for k in NOISE)
    score = 5.0 * strong + 2.0 * account + 2.0 * privacy - 3.0 * noise
    if strong and account:
        score += 2.0
    return score


def is_privacy_link(url: str, text: str) -> bool:
    hay = fold(f"{urlsplit(url).path} {text}").replace("_", "-")
    return any(k in hay for k in PRIVACY)


AT_RE = re.compile(r"\s*[\[\(\{]\s*(?:at|arobase|chez)\s*[\]\)\}]\s*", re.IGNORECASE)
DOT_RE = re.compile(r"\s*[\[\(\{]\s*(?:dot|point)\s*[\]\)\}]\s*", re.IGNORECASE)


def deobfuscate(text: str) -> str:
    return DOT_RE.sub(".", AT_RE.sub("@", text))


def find_privacy_emails(html: str, links: list[tuple[str, str]]) -> list[str]:
    found = [h[len("mailto:"):].split("?")[0] for h, _ in links if h.startswith("mailto:")]
    found += EMAIL_RE.findall(deobfuscate(html))
    out: list[str] = []
    for email in found:
        email = email.strip().lower()
        if any(h in email for h in EMAIL_HINTS) and email not in out:
            out.append(email)
    return out
