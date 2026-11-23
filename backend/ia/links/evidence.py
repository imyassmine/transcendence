import asyncio
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .crawler import Candidate
from .fetcher import SafeFetcher
from .parsing import STRONG, fold

EXCERPT_LEN = 300
ENRICH_LIMIT = 10
LOGIN_HINTS = ["login", "signin", "sign-in", "connexion", "auth"]
SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "head"}


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: list[str] = []
        self.text: list[str] = []
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag in SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title.append(data)
        elif not self._skip:
            self.text.append(data)


def page_text(html: str) -> tuple[str, str]:
    parser = _TextParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    title = " ".join(" ".join(parser.title).split())
    text = " ".join(" ".join(parser.text).split())
    return title, text


def excerpt(text: str, length: int = EXCERPT_LEN) -> str:
    folded = fold(text)
    positions = [folded.find(k) for k in STRONG if k in folded]
    if not positions:
        return text[:length]
    start = max(0, min(positions) - length // 3)
    return text[start:start + length]


def is_login_url(url: str) -> bool:
    path = fold(urlsplit(url).path)
    return any(h in path for h in LOGIN_HINTS)


def describe(asked_url: str, final_url: str, status: int, html: str) -> str:
    if status >= 400:
        return f"[erreur HTTP {status}]"
    parts = []
    if is_login_url(final_url) and not is_login_url(asked_url):
        parts.append("[redirige vers la page de connexion : page réservée aux comptes connectés]")
    title, text = page_text(html)
    if title:
        parts.append(f"titre : {title[:100]}")
    if text:
        parts.append(f"extrait : {excerpt(text)}")
    return " | ".join(parts) or "[page vide ou générée en JavaScript]"


async def enrich(fetcher: SafeFetcher, candidates: list[Candidate],
                 limit: int = ENRICH_LIMIT) -> list[Candidate]:
    top = candidates[:limit]
    pages = await asyncio.gather(*(fetcher.get(c.url) for c in top))
    for c, page in zip(top, pages):
        if page is None:
            c.excerpt = "[page inaccessible]"
        else:
            c.excerpt = describe(c.url, page.url, page.status, page.text)
    return candidates
